"""
AZALS - Two-Factor Authentication (2FA) ÉLITE
==============================================
Authentification à deux facteurs avec TOTP.
Compatible Google Authenticator, Authy, etc.
"""
from __future__ import annotations


import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

import pyotp
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.models import User


@dataclass
class TOTPSetupResult:
    """Résultat de l'initialisation 2FA."""
    secret: str
    provisioning_uri: str
    qr_code_data: str  # URI pour générer QR code
    backup_codes: list[str]


@dataclass
class TOTPVerifyResult:
    """Résultat de la vérification 2FA."""
    success: bool
    message: str
    backup_code_used: bool = False


class TwoFactorService:
    """
    Service de gestion 2FA TOTP.

    Fonctionnalités:
    - Génération de secret TOTP
    - Vérification de code TOTP
    - Codes de secours
    - QR code URI pour apps authentificator
    """

    ISSUER_NAME = "AZALS"
    BACKUP_CODES_COUNT = 10
    BACKUP_CODE_LENGTH = 8

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def setup_2fa(self, user: User) -> TOTPSetupResult:
        """
        Initialise le 2FA pour un utilisateur.

        Args:
            user: Utilisateur pour lequel activer 2FA

        Returns:
            TOTPSetupResult avec secret, URI et codes de secours
        """
        # Générer un nouveau secret TOTP
        secret = pyotp.random_base32()

        # Générer l'URI de provisionnement (pour QR code)
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=self.ISSUER_NAME
        )

        # Générer les codes de secours
        backup_codes = self._generate_backup_codes()

        # Stocker le secret (non activé jusqu'à vérification)
        user.totp_secret = secret
        user.backup_codes = json.dumps(self._hash_backup_codes(backup_codes))
        self.db.commit()

        return TOTPSetupResult(
            secret=secret,
            provisioning_uri=provisioning_uri,
            qr_code_data=provisioning_uri,
            backup_codes=backup_codes
        )

    def verify_and_enable_2fa(self, user: User, code: str) -> TOTPVerifyResult:
        """
        Vérifie le code TOTP et active le 2FA si correct.
        Utilisé lors de la première configuration.

        Args:
            user: Utilisateur
            code: Code TOTP à 6 chiffres

        Returns:
            TOTPVerifyResult
        """
        if not user.totp_secret:
            return TOTPVerifyResult(
                success=False,
                message="2FA not initialized. Call setup_2fa first."
            )

        if user.totp_enabled:
            return TOTPVerifyResult(
                success=False,
                message="2FA already enabled."
            )

        # Vérifier le code TOTP
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return TOTPVerifyResult(
                success=False,
                message="Invalid TOTP code."
            )

        # Activer le 2FA
        user.totp_enabled = 1
        user.totp_verified_at = datetime.now(timezone.utc)
        self.db.commit()

        return TOTPVerifyResult(
            success=True,
            message="2FA enabled successfully."
        )

    def verify_2fa(self, user: User, code: str) -> TOTPVerifyResult:
        """
        Vérifie un code 2FA (TOTP ou backup code).
        Utilisé lors de la connexion.

        Args:
            user: Utilisateur
            code: Code TOTP ou code de secours

        Returns:
            TOTPVerifyResult
        """
        if not user.totp_enabled:
            return TOTPVerifyResult(
                success=True,
                message="2FA not enabled for this user."
            )

        if not user.totp_secret:
            return TOTPVerifyResult(
                success=False,
                message="2FA configuration error."
            )

        # Essayer le code TOTP standard
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            return TOTPVerifyResult(
                success=True,
                message="TOTP verified."
            )

        # Essayer comme code de secours
        if self._verify_backup_code(user, code):
            return TOTPVerifyResult(
                success=True,
                message="Backup code verified and consumed.",
                backup_code_used=True
            )

        return TOTPVerifyResult(
            success=False,
            message="Invalid 2FA code."
        )

    def disable_2fa(self, user: User, code: str) -> TOTPVerifyResult:
        """
        Désactive le 2FA après vérification.

        Args:
            user: Utilisateur
            code: Code TOTP pour confirmer

        Returns:
            TOTPVerifyResult
        """
        # Vérifier le code avant désactivation
        verify_result = self.verify_2fa(user, code)
        if not verify_result.success:
            return TOTPVerifyResult(
                success=False,
                message="Invalid code. Cannot disable 2FA."
            )

        # Désactiver
        user.totp_enabled = 0
        user.totp_secret = None
        user.totp_verified_at = None
        user.backup_codes = None
        self.db.commit()

        return TOTPVerifyResult(
            success=True,
            message="2FA disabled successfully."
        )

    def regenerate_backup_codes(self, user: User, code: str) -> tuple[bool, list[str]]:
        """
        Régénère les codes de secours après vérification.

        Args:
            user: Utilisateur
            code: Code TOTP pour confirmer

        Returns:
            Tuple (success, new_backup_codes)
        """
        # Vérifier le code TOTP (pas backup code pour cette opération)
        if not user.totp_secret:
            return False, []

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return False, []

        # Générer nouveaux codes
        new_codes = self._generate_backup_codes()
        user.backup_codes = json.dumps(self._hash_backup_codes(new_codes))
        self.db.commit()

        return True, new_codes

    def is_2fa_required(self, user: User) -> bool:
        """
        Vérifie si 2FA est requis pour cet utilisateur.
        En production, 2FA est obligatoire pour les dirigeants.
        """
        if self.settings.is_production:
            # En production, 2FA obligatoire pour tous
            return True
        return user.totp_enabled == 1

    def get_2fa_status(self, user: User) -> dict:
        """Retourne le statut 2FA d'un utilisateur."""
        return {
            "enabled": user.totp_enabled == 1,
            "verified_at": user.totp_verified_at.isoformat() if user.totp_verified_at else None,
            "has_backup_codes": user.backup_codes is not None,
            "required": self.is_2fa_required(user)
        }

    def _generate_backup_codes(self) -> list[str]:
        """Génère des codes de secours."""
        return [
            secrets.token_hex(self.BACKUP_CODE_LENGTH // 2).upper()
            for _ in range(self.BACKUP_CODES_COUNT)
        ]

    def _hash_backup_codes(self, codes: list[str]) -> list[str]:
        """Hash les codes de secours pour stockage."""
        return [
            hashlib.sha256(code.encode()).hexdigest()
            for code in codes
        ]

    def _verify_backup_code(self, user: User, code: str) -> bool:
        """Vérifie et consomme un code de secours."""
        if not user.backup_codes:
            return False

        try:
            stored_hashes = json.loads(user.backup_codes)
        except json.JSONDecodeError:
            return False

        code_hash = hashlib.sha256(code.upper().encode()).hexdigest()

        if code_hash in stored_hashes:
            # Consommer le code (le retirer)
            stored_hashes.remove(code_hash)
            user.backup_codes = json.dumps(stored_hashes)
            self.db.commit()
            return True

        return False


def get_current_totp_code(secret: str) -> str:
    """
    Utilitaire pour obtenir le code TOTP actuel (pour tests).

    Args:
        secret: Secret TOTP base32

    Returns:
        Code TOTP à 6 chiffres
    """
    totp = pyotp.TOTP(secret)
    return totp.now()
