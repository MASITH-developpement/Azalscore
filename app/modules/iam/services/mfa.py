"""
AZALS MODULE T0 - MFA Service
==============================

Gestion de l'authentification multi-facteurs.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

import pyotp

from app.core.encryption import encrypt_value, decrypt_value
from app.modules.iam.models import IAMUser, MFAType
from .base import BaseIAMService

logger = logging.getLogger(__name__)


class MFAService(BaseIAMService[IAMUser]):
    """Service MFA."""

    model = IAMUser

    def setup_totp(self, user_id: UUID) -> Tuple[str, str]:
        """Configure TOTP pour un utilisateur. Retourne (secret, provisioning_uri)."""
        user = self._base_query().filter(IAMUser.id == user_id).first()
        if not user:
            raise ValueError("Utilisateur non trouvé")

        # Générer un secret TOTP
        secret = pyotp.random_base32()

        # Stocker le secret chiffré (non activé encore)
        user.mfa_secret = encrypt_value(secret)
        user.mfa_type = MFAType.TOTP
        user.mfa_enabled = False  # Sera activé après vérification
        self.db.commit()

        # Générer l'URI de provisioning pour QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="AZALSCORE"
        )

        return secret, provisioning_uri

    def verify_totp(self, user_id: UUID, code: str) -> bool:
        """Vérifie un code TOTP."""
        user = self._base_query().filter(IAMUser.id == user_id).first()
        if not user or not user.mfa_secret:
            return False

        secret = decrypt_value(user.mfa_secret)
        totp = pyotp.TOTP(secret)

        return totp.verify(code, valid_window=1)

    def activate_mfa(self, user_id: UUID, code: str) -> bool:
        """Active MFA après vérification du premier code."""
        if not self.verify_totp(user_id, code):
            return False

        user = self._base_query().filter(IAMUser.id == user_id).first()
        if not user:
            return False

        user.mfa_enabled = True
        user.mfa_activated_at = datetime.utcnow()

        # Générer les codes de backup
        backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]
        user.mfa_backup_codes = ",".join([
            encrypt_value(code) for code in backup_codes
        ])

        self._audit_log("MFA_ACTIVATED", "USER", user_id, None,
                       new_values={"mfa_type": str(user.mfa_type)})
        self.db.commit()

        return True

    def deactivate_mfa(self, user_id: UUID, deactivated_by: int | None = None) -> bool:
        """Désactive MFA pour un utilisateur."""
        user = self._base_query().filter(IAMUser.id == user_id).first()
        if not user:
            return False

        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_type = None
        user.mfa_backup_codes = None

        self._audit_log("MFA_DEACTIVATED", "USER", user_id, deactivated_by)
        self.db.commit()
        return True

    def verify_backup_code(self, user_id: UUID, code: str) -> bool:
        """Vérifie un code de backup."""
        user = self._base_query().filter(IAMUser.id == user_id).first()
        if not user or not user.mfa_backup_codes:
            return False

        backup_codes = user.mfa_backup_codes.split(",")

        for i, encrypted_code in enumerate(backup_codes):
            if decrypt_value(encrypted_code) == code:
                # Supprimer le code utilisé
                backup_codes.pop(i)
                user.mfa_backup_codes = ",".join(backup_codes) if backup_codes else None

                self._audit_log("BACKUP_CODE_USED", "USER", user_id, None)
                self.db.commit()
                return True

        return False

    def regenerate_backup_codes(self, user_id: UUID) -> list[str]:
        """Régénère les codes de backup."""
        user = self._base_query().filter(IAMUser.id == user_id).first()
        if not user or not user.mfa_enabled:
            raise ValueError("MFA non activé")

        backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]
        user.mfa_backup_codes = ",".join([
            encrypt_value(code) for code in backup_codes
        ])

        self._audit_log("BACKUP_CODES_REGENERATED", "USER", user_id, None)
        self.db.commit()

        return backup_codes

    def is_mfa_required(self, user_id: UUID) -> bool:
        """Vérifie si MFA est requis pour un utilisateur."""
        user = self._base_query().filter(IAMUser.id == user_id).first()
        if not user:
            return False

        return user.mfa_enabled
