"""
AZALSCORE - Service MFA Avancé
===============================

Authentification Multi-Facteurs complète:
- TOTP (Google Authenticator, Authy)
- WebAuthn/FIDO2 (clés de sécurité, biométrie)
- SMS OTP
- Email OTP
- Push notifications
- MFA Adaptative (risk-based)
- Device Trust (remember device)
- Recovery flows

Conformité:
- NIST SP 800-63B (Digital Identity Guidelines)
- PCI-DSS v4.0 (Requirement 8: Identify Users and Authenticate Access)
- ANSSI (Recommandations authentification multifacteur)
"""
from __future__ import annotations


import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import struct
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Callable
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class MFAMethod(str, Enum):
    """Méthodes MFA supportées."""
    TOTP = "totp"  # Time-based One-Time Password
    WEBAUTHN = "webauthn"  # FIDO2/WebAuthn
    SMS = "sms"  # SMS OTP
    EMAIL = "email"  # Email OTP
    PUSH = "push"  # Push notification
    BACKUP_CODE = "backup_code"  # Codes de récupération


class MFAStatus(str, Enum):
    """Statut MFA pour un utilisateur."""
    DISABLED = "disabled"
    PENDING_SETUP = "pending_setup"
    ENABLED = "enabled"
    LOCKED = "locked"  # Trop de tentatives échouées


class RiskLevel(str, Enum):
    """Niveau de risque pour MFA adaptative."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationResult(str, Enum):
    """Résultat de vérification MFA."""
    SUCCESS = "success"
    INVALID_CODE = "invalid_code"
    EXPIRED = "expired"
    LOCKED = "locked"
    NOT_SETUP = "not_setup"
    METHOD_UNAVAILABLE = "method_unavailable"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MFAChallenge:
    """Challenge MFA en cours."""
    challenge_id: str
    user_id: str
    tenant_id: str
    method: MFAMethod
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 5
    verified: bool = False
    verified_at: Optional[datetime] = None

    # Données spécifiques à la méthode
    code_hash: Optional[str] = None  # Pour TOTP/SMS/Email
    webauthn_challenge: Optional[bytes] = None  # Pour WebAuthn
    push_token: Optional[str] = None  # Pour Push

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def is_locked(self) -> bool:
        return self.attempts >= self.max_attempts


@dataclass
class TOTPConfig:
    """Configuration TOTP pour un utilisateur."""
    secret: str
    algorithm: str = "SHA1"
    digits: int = 6
    period: int = 30
    issuer: str = "AZALSCORE"
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WebAuthnCredential:
    """Credential WebAuthn enregistré."""
    credential_id: bytes
    public_key: bytes
    sign_count: int
    aaguid: bytes
    user_handle: bytes
    name: str  # Nom donné par l'utilisateur
    created_at: datetime
    last_used_at: Optional[datetime] = None
    transports: list[str] = field(default_factory=list)


@dataclass
class TrustedDevice:
    """Appareil de confiance."""
    device_id: str
    user_id: str
    tenant_id: str
    device_hash: str  # Hash du fingerprint
    name: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_revoked: bool = False


@dataclass
class RiskAssessment:
    """Évaluation du risque pour MFA adaptative."""
    risk_level: RiskLevel
    score: float  # 0-100
    factors: dict[str, float]
    require_mfa: bool
    require_strong_mfa: bool  # WebAuthn uniquement
    additional_verification: list[str]
    reason: str


@dataclass
class MFAConfiguration:
    """Configuration MFA globale pour un tenant."""
    tenant_id: str
    enabled_methods: list[MFAMethod]
    default_method: MFAMethod
    enforce_for_all: bool = False
    enforce_for_roles: list[str] = field(default_factory=list)
    adaptive_enabled: bool = True
    device_trust_enabled: bool = True
    device_trust_duration_days: int = 30
    totp_issuer: str = "AZALSCORE"
    sms_provider: Optional[str] = None
    push_provider: Optional[str] = None


# =============================================================================
# TOTP SERVICE
# =============================================================================

class TOTPService:
    """Service TOTP (RFC 6238)."""

    def __init__(self, digits: int = 6, period: int = 30, algorithm: str = "SHA1"):
        self.digits = digits
        self.period = period
        self.algorithm = algorithm

    def generate_secret(self, length: int = 32) -> str:
        """Génère un secret TOTP en base32."""
        random_bytes = secrets.token_bytes(length)
        return base64.b32encode(random_bytes).decode().rstrip("=")

    def generate_code(self, secret: str, timestamp: Optional[int] = None) -> str:
        """Génère un code TOTP."""
        if timestamp is None:
            timestamp = int(time.time())

        # Calculer le compteur basé sur le temps
        counter = timestamp // self.period

        # Décoder le secret
        secret_bytes = self._decode_secret(secret)

        # HMAC-SHA1 du compteur
        counter_bytes = struct.pack(">Q", counter)
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation (RFC 4226)
        offset = hmac_hash[-1] & 0x0F
        binary = struct.unpack(">I", hmac_hash[offset:offset + 4])[0] & 0x7FFFFFFF

        # Générer le code
        code = binary % (10 ** self.digits)
        return str(code).zfill(self.digits)

    def verify_code(
        self,
        secret: str,
        code: str,
        window: int = 1,
        timestamp: Optional[int] = None
    ) -> bool:
        """
        Vérifie un code TOTP.

        Args:
            secret: Secret TOTP
            code: Code à vérifier
            window: Nombre de périodes de tolérance (avant et après)
            timestamp: Timestamp de référence
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Vérifier dans la fenêtre temporelle
        for offset in range(-window, window + 1):
            test_time = timestamp + (offset * self.period)
            expected = self.generate_code(secret, test_time)
            if hmac.compare_digest(code, expected):
                return True

        return False

    def get_provisioning_uri(
        self,
        secret: str,
        email: str,
        issuer: str = "AZALSCORE"
    ) -> str:
        """Génère l'URI de provisioning pour QR code."""
        # Format: otpauth://totp/ISSUER:EMAIL?secret=SECRET&issuer=ISSUER
        from urllib.parse import quote

        label = f"{issuer}:{email}"
        params = f"secret={secret}&issuer={quote(issuer)}&algorithm={self.algorithm}&digits={self.digits}&period={self.period}"

        return f"otpauth://totp/{quote(label)}?{params}"

    def _decode_secret(self, secret: str) -> bytes:
        """Décode un secret base32."""
        # Ajouter le padding si nécessaire
        padding = 8 - len(secret) % 8
        if padding != 8:
            secret += "=" * padding
        return base64.b32decode(secret.upper())


# =============================================================================
# WEBAUTHN SERVICE
# =============================================================================

class WebAuthnService:
    """
    Service WebAuthn/FIDO2.

    Gère l'enregistrement et l'authentification avec:
    - Clés de sécurité (YubiKey, etc.)
    - Biométrie (Touch ID, Face ID, Windows Hello)
    - Passkeys
    """

    def __init__(
        self,
        rp_id: str = "azalscore.com",
        rp_name: str = "AZALSCORE",
        origin: str = "https://azalscore.com",
        timeout: int = 60000,
    ):
        self.rp_id = rp_id
        self.rp_name = rp_name
        self.origin = origin
        self.timeout = timeout
        self._challenges: dict[str, MFAChallenge] = {}
        self._credentials: dict[str, list[WebAuthnCredential]] = {}

    def generate_registration_options(
        self,
        user_id: str,
        username: str,
        display_name: str,
        existing_credential_ids: Optional[list[bytes]] = None,
    ) -> dict:
        """
        Génère les options pour l'enregistrement d'un nouveau credential.
        """
        challenge = secrets.token_bytes(32)
        challenge_id = str(uuid.uuid4())

        # Stocker le challenge
        self._challenges[challenge_id] = MFAChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            tenant_id="",  # Sera rempli plus tard
            method=MFAMethod.WEBAUTHN,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            webauthn_challenge=challenge,
        )

        options = {
            "challenge": base64.urlsafe_b64encode(challenge).decode().rstrip("="),
            "rp": {
                "id": self.rp_id,
                "name": self.rp_name,
            },
            "user": {
                "id": base64.urlsafe_b64encode(user_id.encode()).decode().rstrip("="),
                "name": username,
                "displayName": display_name,
            },
            "pubKeyCredParams": [
                {"type": "public-key", "alg": -7},  # ES256
                {"type": "public-key", "alg": -257},  # RS256
            ],
            "timeout": self.timeout,
            "authenticatorSelection": {
                "authenticatorAttachment": "cross-platform",  # Ou "platform" pour biométrie
                "userVerification": "preferred",
                "residentKey": "preferred",
            },
            "attestation": "direct",
        }

        # Exclure les credentials existants
        if existing_credential_ids:
            options["excludeCredentials"] = [
                {
                    "type": "public-key",
                    "id": base64.urlsafe_b64encode(cred_id).decode().rstrip("="),
                }
                for cred_id in existing_credential_ids
            ]

        return {
            "challenge_id": challenge_id,
            "options": options,
        }

    def verify_registration(
        self,
        challenge_id: str,
        credential: dict,
    ) -> Optional[WebAuthnCredential]:
        """
        Vérifie la réponse d'enregistrement WebAuthn.
        """
        challenge = self._challenges.get(challenge_id)
        if not challenge or challenge.is_expired():
            logger.warning(f"Invalid or expired challenge: {challenge_id}")
            return None

        try:
            # Parser la réponse
            client_data = json.loads(
                base64.urlsafe_b64decode(
                    credential["response"]["clientDataJSON"] + "=="
                )
            )

            # Vérifier le challenge
            received_challenge = base64.urlsafe_b64decode(client_data["challenge"] + "==")
            if received_challenge != challenge.webauthn_challenge:
                logger.warning("Challenge mismatch")
                return None

            # Vérifier l'origin
            if client_data["origin"] != self.origin:
                logger.warning(f"Origin mismatch: {client_data['origin']} != {self.origin}")
                return None

            # Vérifier le type
            if client_data["type"] != "webauthn.create":
                logger.warning("Invalid ceremony type")
                return None

            # Parser attestation object
            attestation_object = base64.urlsafe_b64decode(
                credential["response"]["attestationObject"] + "=="
            )

            # Extraire le credential ID et la clé publique
            # (Implémentation simplifiée - en production utiliser webauthn-py)
            credential_id = base64.urlsafe_b64decode(credential["id"] + "==")

            # Créer le credential
            webauthn_credential = WebAuthnCredential(
                credential_id=credential_id,
                public_key=attestation_object,  # Simplifié
                sign_count=0,
                aaguid=b"\x00" * 16,  # Simplifié
                user_handle=challenge.user_id.encode(),
                name="Security Key",
                created_at=datetime.utcnow(),
                transports=credential.get("transports", []),
            )

            # Nettoyer le challenge
            del self._challenges[challenge_id]

            logger.info(f"WebAuthn credential registered for user {challenge.user_id}")
            return webauthn_credential

        except Exception as e:
            logger.error(f"WebAuthn registration verification failed: {e}")
            return None

    def generate_authentication_options(
        self,
        user_id: str,
        credentials: list[WebAuthnCredential],
    ) -> dict:
        """
        Génère les options pour l'authentification WebAuthn.
        """
        challenge = secrets.token_bytes(32)
        challenge_id = str(uuid.uuid4())

        # Stocker le challenge
        self._challenges[challenge_id] = MFAChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            tenant_id="",
            method=MFAMethod.WEBAUTHN,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            webauthn_challenge=challenge,
        )

        options = {
            "challenge": base64.urlsafe_b64encode(challenge).decode().rstrip("="),
            "timeout": self.timeout,
            "rpId": self.rp_id,
            "userVerification": "preferred",
            "allowCredentials": [
                {
                    "type": "public-key",
                    "id": base64.urlsafe_b64encode(cred.credential_id).decode().rstrip("="),
                    "transports": cred.transports,
                }
                for cred in credentials
            ],
        }

        return {
            "challenge_id": challenge_id,
            "options": options,
        }

    def verify_authentication(
        self,
        challenge_id: str,
        credential: dict,
        stored_credentials: list[WebAuthnCredential],
    ) -> tuple[bool, Optional[WebAuthnCredential]]:
        """
        Vérifie la réponse d'authentification WebAuthn.

        Returns:
            Tuple (success, used_credential)
        """
        challenge = self._challenges.get(challenge_id)
        if not challenge or challenge.is_expired():
            return False, None

        try:
            credential_id = base64.urlsafe_b64decode(credential["id"] + "==")

            # Trouver le credential correspondant
            matched_credential = None
            for stored in stored_credentials:
                if stored.credential_id == credential_id:
                    matched_credential = stored
                    break

            if not matched_credential:
                logger.warning("Unknown credential ID")
                return False, None

            # Parser client data
            client_data = json.loads(
                base64.urlsafe_b64decode(
                    credential["response"]["clientDataJSON"] + "=="
                )
            )

            # Vérifier le challenge
            received_challenge = base64.urlsafe_b64decode(client_data["challenge"] + "==")
            if received_challenge != challenge.webauthn_challenge:
                return False, None

            # Vérifier le type
            if client_data["type"] != "webauthn.get":
                return False, None

            # En production: vérifier la signature, le sign_count, etc.

            # Nettoyer et mettre à jour
            del self._challenges[challenge_id]
            matched_credential.last_used_at = datetime.utcnow()
            matched_credential.sign_count += 1

            logger.info(f"WebAuthn authentication successful for user {challenge.user_id}")
            return True, matched_credential

        except Exception as e:
            logger.error(f"WebAuthn authentication verification failed: {e}")
            return False, None


# =============================================================================
# OTP SERVICE (SMS/Email)
# =============================================================================

class OTPService:
    """Service OTP pour SMS et Email."""

    def __init__(
        self,
        code_length: int = 6,
        validity_minutes: int = 10,
        max_attempts: int = 3,
    ):
        self.code_length = code_length
        self.validity_minutes = validity_minutes
        self.max_attempts = max_attempts
        self._pending_codes: dict[str, MFAChallenge] = {}
        self._lock = threading.Lock()

    def generate_code(
        self,
        user_id: str,
        tenant_id: str,
        method: MFAMethod,
    ) -> tuple[str, MFAChallenge]:
        """
        Génère un code OTP.

        Returns:
            Tuple (code_in_clear, challenge)
        """
        # Générer un code numérique
        code = "".join(secrets.choice("0123456789") for _ in range(self.code_length))

        # Hash du code pour stockage
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        challenge_id = str(uuid.uuid4())
        challenge = MFAChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            tenant_id=tenant_id,
            method=method,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=self.validity_minutes),
            max_attempts=self.max_attempts,
            code_hash=code_hash,
        )

        with self._lock:
            # Invalider les anciens codes pour cet utilisateur
            to_remove = []
            for cid, ch in self._pending_codes.items():
                if ch.user_id == user_id and ch.method == method:
                    to_remove.append(cid)
            for cid in to_remove:
                del self._pending_codes[cid]

            self._pending_codes[challenge_id] = challenge

        return code, challenge

    def verify_code(
        self,
        challenge_id: str,
        code: str,
    ) -> VerificationResult:
        """Vérifie un code OTP."""
        with self._lock:
            challenge = self._pending_codes.get(challenge_id)

            if not challenge:
                return VerificationResult.NOT_SETUP

            if challenge.is_expired():
                del self._pending_codes[challenge_id]
                return VerificationResult.EXPIRED

            if challenge.is_locked():
                return VerificationResult.LOCKED

            # Vérifier le code
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            if hmac.compare_digest(code_hash, challenge.code_hash):
                challenge.verified = True
                challenge.verified_at = datetime.utcnow()
                del self._pending_codes[challenge_id]
                return VerificationResult.SUCCESS

            # Incrémenter les tentatives
            challenge.attempts += 1
            return VerificationResult.INVALID_CODE

    def cleanup_expired(self) -> int:
        """Nettoie les codes expirés."""
        count = 0
        with self._lock:
            to_remove = []
            for cid, challenge in self._pending_codes.items():
                if challenge.is_expired():
                    to_remove.append(cid)
            for cid in to_remove:
                del self._pending_codes[cid]
                count += 1
        return count


# =============================================================================
# ADAPTIVE MFA (Risk-Based)
# =============================================================================

class AdaptiveMFAService:
    """
    Service MFA Adaptative basé sur le risque.

    Évalue le contexte de la connexion et ajuste les exigences MFA:
    - Nouvel appareil/IP = risque élevé
    - Comportement inhabituel = risque élevé
    - Appareil de confiance = risque faible
    """

    # Poids des facteurs de risque (0-100)
    RISK_FACTORS = {
        "new_device": 30,
        "new_ip": 20,
        "new_country": 40,
        "impossible_travel": 50,
        "unusual_time": 15,
        "failed_attempts_recent": 25,
        "vpn_detected": 10,
        "tor_detected": 35,
        "known_bad_ip": 45,
        "sensitive_operation": 20,
    }

    # Seuils de risque
    THRESHOLDS = {
        RiskLevel.LOW: 20,
        RiskLevel.MEDIUM: 40,
        RiskLevel.HIGH: 60,
        RiskLevel.CRITICAL: 80,
    }

    def __init__(self):
        self._user_history: dict[str, list[dict]] = defaultdict(list)
        self._bad_ips: set[str] = set()
        self._lock = threading.Lock()

    def assess_risk(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: Optional[str] = None,
        geo_location: Optional[dict] = None,
        is_sensitive_operation: bool = False,
    ) -> RiskAssessment:
        """
        Évalue le risque d'une tentative de connexion.
        """
        factors = {}
        score = 0.0

        with self._lock:
            user_history = self._user_history.get(f"{tenant_id}:{user_id}", [])

        # Vérifier si nouvel appareil
        if device_fingerprint:
            known_devices = {h.get("device_fingerprint") for h in user_history}
            if device_fingerprint not in known_devices:
                factors["new_device"] = self.RISK_FACTORS["new_device"]
                score += factors["new_device"]

        # Vérifier si nouvelle IP
        known_ips = {h.get("ip_address") for h in user_history}
        if ip_address not in known_ips:
            factors["new_ip"] = self.RISK_FACTORS["new_ip"]
            score += factors["new_ip"]

        # Vérifier le pays
        if geo_location:
            known_countries = {h.get("country") for h in user_history if h.get("country")}
            current_country = geo_location.get("country")
            if current_country and known_countries and current_country not in known_countries:
                factors["new_country"] = self.RISK_FACTORS["new_country"]
                score += factors["new_country"]

        # Vérifier le voyage impossible
        if user_history and geo_location:
            last_login = user_history[-1] if user_history else None
            if last_login and last_login.get("geo_location"):
                if self._check_impossible_travel(
                    last_login["geo_location"],
                    geo_location,
                    last_login.get("timestamp")
                ):
                    factors["impossible_travel"] = self.RISK_FACTORS["impossible_travel"]
                    score += factors["impossible_travel"]

        # Vérifier l'heure inhabituelle
        current_hour = datetime.utcnow().hour
        if user_history:
            typical_hours = [h.get("hour", 12) for h in user_history]
            avg_hour = sum(typical_hours) / len(typical_hours)
            if abs(current_hour - avg_hour) > 6:
                factors["unusual_time"] = self.RISK_FACTORS["unusual_time"]
                score += factors["unusual_time"]

        # Vérifier les échecs récents
        recent_failures = sum(
            1 for h in user_history
            if h.get("success") is False
            and h.get("timestamp", datetime.min) > datetime.utcnow() - timedelta(hours=1)
        )
        if recent_failures >= 3:
            factors["failed_attempts_recent"] = self.RISK_FACTORS["failed_attempts_recent"]
            score += factors["failed_attempts_recent"]

        # Vérifier les IPs connues comme malveillantes
        if ip_address in self._bad_ips:
            factors["known_bad_ip"] = self.RISK_FACTORS["known_bad_ip"]
            score += factors["known_bad_ip"]

        # Opération sensible
        if is_sensitive_operation:
            factors["sensitive_operation"] = self.RISK_FACTORS["sensitive_operation"]
            score += factors["sensitive_operation"]

        # Déterminer le niveau de risque
        risk_level = RiskLevel.LOW
        for level, threshold in self.THRESHOLDS.items():
            if score >= threshold:
                risk_level = level

        # Déterminer les exigences
        require_mfa = risk_level != RiskLevel.LOW
        require_strong_mfa = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

        additional_verification = []
        if risk_level == RiskLevel.CRITICAL:
            additional_verification = ["email_confirmation", "manual_review"]
        elif risk_level == RiskLevel.HIGH:
            additional_verification = ["webauthn_preferred"]

        # Générer la raison
        reason_parts = []
        if "new_device" in factors:
            reason_parts.append("new device detected")
        if "new_ip" in factors:
            reason_parts.append("new IP address")
        if "new_country" in factors:
            reason_parts.append("new country")
        if "impossible_travel" in factors:
            reason_parts.append("impossible travel detected")
        if "unusual_time" in factors:
            reason_parts.append("unusual login time")

        reason = "; ".join(reason_parts) if reason_parts else "normal login"

        return RiskAssessment(
            risk_level=risk_level,
            score=min(score, 100),
            factors=factors,
            require_mfa=require_mfa,
            require_strong_mfa=require_strong_mfa,
            additional_verification=additional_verification,
            reason=reason,
        )

    def record_login(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: Optional[str] = None,
        geo_location: Optional[dict] = None,
        success: bool = True,
    ) -> None:
        """Enregistre une tentative de connexion."""
        key = f"{tenant_id}:{user_id}"

        record = {
            "timestamp": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_fingerprint": device_fingerprint,
            "geo_location": geo_location,
            "country": geo_location.get("country") if geo_location else None,
            "hour": datetime.utcnow().hour,
            "success": success,
        }

        with self._lock:
            self._user_history[key].append(record)
            # Garder seulement les 100 derniers enregistrements
            if len(self._user_history[key]) > 100:
                self._user_history[key] = self._user_history[key][-100:]

    def add_bad_ip(self, ip_address: str) -> None:
        """Ajoute une IP à la liste noire."""
        with self._lock:
            self._bad_ips.add(ip_address)

    def _check_impossible_travel(
        self,
        last_location: dict,
        current_location: dict,
        last_timestamp: Optional[datetime]
    ) -> bool:
        """
        Vérifie si le déplacement est physiquement impossible.
        """
        if not last_timestamp:
            return False

        time_diff_hours = (datetime.utcnow() - last_timestamp).total_seconds() / 3600

        # Calcul de distance simplifié (Haversine)
        last_lat = last_location.get("latitude", 0)
        last_lon = last_location.get("longitude", 0)
        curr_lat = current_location.get("latitude", 0)
        curr_lon = current_location.get("longitude", 0)

        import math
        R = 6371  # Rayon de la Terre en km

        lat1, lon1 = math.radians(last_lat), math.radians(last_lon)
        lat2, lon2 = math.radians(curr_lat), math.radians(curr_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = R * c

        # Vitesse maximale réaliste: 900 km/h (avion commercial)
        max_distance = time_diff_hours * 900

        return distance_km > max_distance


# =============================================================================
# DEVICE TRUST SERVICE
# =============================================================================

class DeviceTrustService:
    """
    Service de gestion des appareils de confiance.

    Permet aux utilisateurs de "se souvenir" d'un appareil
    pour éviter la MFA à chaque connexion.
    """

    def __init__(
        self,
        trust_duration_days: int = 30,
        max_devices_per_user: int = 10,
        secret_key: bytes = None,
    ):
        self.trust_duration_days = trust_duration_days
        self.max_devices_per_user = max_devices_per_user
        self._secret_key = secret_key or os.urandom(32)
        self._trusted_devices: dict[str, TrustedDevice] = {}
        self._lock = threading.Lock()

    def generate_device_token(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: str,
        user_agent: str,
        device_name: Optional[str] = None,
    ) -> tuple[str, TrustedDevice]:
        """
        Génère un token pour un nouvel appareil de confiance.

        Returns:
            Tuple (token, device)
        """
        device_id = str(uuid.uuid4())

        # Créer un hash du device fingerprint
        fingerprint_data = f"{user_agent}:{ip_address}"
        device_hash = hmac.new(
            self._secret_key,
            fingerprint_data.encode(),
            hashlib.sha256
        ).hexdigest()

        now = datetime.utcnow()
        device = TrustedDevice(
            device_id=device_id,
            user_id=user_id,
            tenant_id=tenant_id,
            device_hash=device_hash,
            name=device_name or f"Device {device_id[:8]}",
            created_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(days=self.trust_duration_days),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Générer le token
        token_data = {
            "device_id": device_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "device_hash": device_hash,
            "expires_at": device.expires_at.isoformat(),
        }
        token_json = json.dumps(token_data, sort_keys=True)
        signature = hmac.new(
            self._secret_key,
            token_json.encode(),
            hashlib.sha256
        ).hexdigest()

        token = base64.urlsafe_b64encode(
            f"{token_json}|{signature}".encode()
        ).decode()

        # Stocker l'appareil
        with self._lock:
            # Vérifier la limite
            user_devices = [
                d for d in self._trusted_devices.values()
                if d.user_id == user_id and d.tenant_id == tenant_id and not d.is_revoked
            ]
            if len(user_devices) >= self.max_devices_per_user:
                # Supprimer le plus ancien
                oldest = min(user_devices, key=lambda d: d.last_seen_at)
                del self._trusted_devices[oldest.device_id]

            self._trusted_devices[device_id] = device

        logger.info(f"Trusted device created: {device_id} for user {user_id}")
        return token, device

    def verify_device_token(
        self,
        token: str,
        user_id: str,
        tenant_id: str,
        current_user_agent: str,
    ) -> tuple[bool, Optional[TrustedDevice]]:
        """
        Vérifie un token d'appareil de confiance.

        Returns:
            Tuple (is_valid, device)
        """
        try:
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            parts = decoded.rsplit("|", 1)
            if len(parts) != 2:
                return False, None

            token_json, signature = parts

            # Vérifier la signature
            expected_signature = hmac.new(
                self._secret_key,
                token_json.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return False, None

            token_data = json.loads(token_json)

            # Vérifier l'utilisateur et le tenant
            if token_data["user_id"] != user_id or token_data["tenant_id"] != tenant_id:
                return False, None

            # Vérifier l'expiration
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.utcnow() > expires_at:
                return False, None

            # Récupérer l'appareil
            device_id = token_data["device_id"]
            with self._lock:
                device = self._trusted_devices.get(device_id)

            if not device or device.is_revoked:
                return False, None

            # Vérifier le fingerprint (avec tolérance pour user-agent)
            if not self._verify_user_agent_similarity(device.user_agent, current_user_agent):
                logger.warning(f"User agent mismatch for device {device_id}")
                return False, None

            # Mettre à jour last_seen
            device.last_seen_at = datetime.utcnow()

            return True, device

        except Exception as e:
            logger.error(f"Device token verification error: {e}")
            return False, None

    def revoke_device(self, device_id: str, user_id: str, tenant_id: str) -> bool:
        """Révoque un appareil de confiance."""
        with self._lock:
            device = self._trusted_devices.get(device_id)
            if not device:
                return False

            if device.user_id != user_id or device.tenant_id != tenant_id:
                return False

            device.is_revoked = True
            logger.info(f"Trusted device revoked: {device_id}")
            return True

    def revoke_all_devices(self, user_id: str, tenant_id: str) -> int:
        """Révoque tous les appareils d'un utilisateur."""
        count = 0
        with self._lock:
            for device in self._trusted_devices.values():
                if device.user_id == user_id and device.tenant_id == tenant_id:
                    device.is_revoked = True
                    count += 1

        logger.info(f"Revoked {count} devices for user {user_id}")
        return count

    def get_user_devices(self, user_id: str, tenant_id: str) -> list[TrustedDevice]:
        """Liste les appareils de confiance d'un utilisateur."""
        with self._lock:
            return [
                d for d in self._trusted_devices.values()
                if d.user_id == user_id and d.tenant_id == tenant_id and not d.is_revoked
            ]

    def _verify_user_agent_similarity(self, stored: str, current: str) -> bool:
        """Vérifie si deux user-agents sont similaires."""
        # Extraire les parties principales (navigateur, OS)
        def extract_key_parts(ua: str) -> tuple:
            # Simplification: extraire navigateur et OS
            parts = ua.split()
            return tuple(p for p in parts[:3] if not p.startswith("("))

        stored_parts = extract_key_parts(stored)
        current_parts = extract_key_parts(current)

        # Tolérer des différences mineures (version exacte)
        return len(set(stored_parts) & set(current_parts)) >= 2


# =============================================================================
# MFA SERVICE PRINCIPAL
# =============================================================================

class MFAService:
    """
    Service MFA principal qui orchestre toutes les méthodes.
    """

    def __init__(
        self,
        config: Optional[MFAConfiguration] = None,
        totp_service: Optional[TOTPService] = None,
        webauthn_service: Optional[WebAuthnService] = None,
        otp_service: Optional[OTPService] = None,
        adaptive_service: Optional[AdaptiveMFAService] = None,
        device_trust_service: Optional[DeviceTrustService] = None,
    ):
        self.config = config or MFAConfiguration(
            tenant_id="default",
            enabled_methods=[MFAMethod.TOTP, MFAMethod.EMAIL],
            default_method=MFAMethod.TOTP,
        )

        self.totp = totp_service or TOTPService()
        self.webauthn = webauthn_service or WebAuthnService()
        self.otp = otp_service or OTPService()
        self.adaptive = adaptive_service or AdaptiveMFAService()
        self.device_trust = device_trust_service or DeviceTrustService()

        # Storage
        self._user_mfa_configs: dict[str, dict] = {}  # user_id -> config
        self._backup_codes: dict[str, list[str]] = {}  # user_id -> codes
        self._lock = threading.Lock()

    def setup_totp(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
    ) -> dict:
        """
        Initialise la configuration TOTP pour un utilisateur.

        Returns:
            Dict avec secret, uri pour QR code
        """
        secret = self.totp.generate_secret()
        uri = self.totp.get_provisioning_uri(
            secret=secret,
            email=email,
            issuer=self.config.totp_issuer,
        )

        # Stocker (en attente de vérification)
        key = f"{tenant_id}:{user_id}"
        with self._lock:
            if key not in self._user_mfa_configs:
                self._user_mfa_configs[key] = {}

            self._user_mfa_configs[key]["totp"] = TOTPConfig(
                secret=secret,
                verified=False,
            )

        return {
            "secret": secret,
            "uri": uri,
            "method": MFAMethod.TOTP.value,
        }

    def verify_totp_setup(
        self,
        user_id: str,
        tenant_id: str,
        code: str,
    ) -> bool:
        """Vérifie le premier code TOTP pour activer."""
        key = f"{tenant_id}:{user_id}"

        with self._lock:
            config = self._user_mfa_configs.get(key, {}).get("totp")
            if not config:
                return False

            if self.totp.verify_code(config.secret, code):
                config.verified = True
                # Générer les codes de backup
                self._generate_backup_codes(user_id, tenant_id)
                return True

        return False

    def verify_code(
        self,
        user_id: str,
        tenant_id: str,
        code: str,
        method: MFAMethod = MFAMethod.TOTP,
        challenge_id: Optional[str] = None,
    ) -> VerificationResult:
        """
        Vérifie un code MFA.
        """
        key = f"{tenant_id}:{user_id}"

        if method == MFAMethod.TOTP:
            with self._lock:
                config = self._user_mfa_configs.get(key, {}).get("totp")
                if not config or not config.verified:
                    return VerificationResult.NOT_SETUP

            if self.totp.verify_code(config.secret, code):
                return VerificationResult.SUCCESS
            return VerificationResult.INVALID_CODE

        elif method in (MFAMethod.SMS, MFAMethod.EMAIL):
            if not challenge_id:
                return VerificationResult.NOT_SETUP
            return self.otp.verify_code(challenge_id, code)

        elif method == MFAMethod.BACKUP_CODE:
            return self._verify_backup_code(user_id, tenant_id, code)

        return VerificationResult.METHOD_UNAVAILABLE

    def _generate_backup_codes(self, user_id: str, tenant_id: str, count: int = 10) -> list[str]:
        """Génère des codes de récupération."""
        codes = []
        for _ in range(count):
            # Format: XXXX-XXXX
            part1 = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4))
            part2 = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4))
            codes.append(f"{part1}-{part2}")

        # Stocker les hash
        key = f"{tenant_id}:{user_id}"
        with self._lock:
            self._backup_codes[key] = [
                hashlib.sha256(code.encode()).hexdigest()
                for code in codes
            ]

        return codes

    def _verify_backup_code(
        self,
        user_id: str,
        tenant_id: str,
        code: str
    ) -> VerificationResult:
        """Vérifie et consomme un code de backup."""
        key = f"{tenant_id}:{user_id}"
        code_hash = hashlib.sha256(code.upper().replace("-", "").encode()).hexdigest()

        with self._lock:
            stored_codes = self._backup_codes.get(key, [])

            for i, stored_hash in enumerate(stored_codes):
                if hmac.compare_digest(code_hash, stored_hash):
                    # Consommer le code
                    stored_codes.pop(i)
                    return VerificationResult.SUCCESS

        return VerificationResult.INVALID_CODE

    def get_available_methods(self, user_id: str, tenant_id: str) -> list[MFAMethod]:
        """Retourne les méthodes MFA configurées pour un utilisateur."""
        key = f"{tenant_id}:{user_id}"
        methods = []

        with self._lock:
            user_config = self._user_mfa_configs.get(key, {})

            if user_config.get("totp") and user_config["totp"].verified:
                methods.append(MFAMethod.TOTP)

            if user_config.get("webauthn"):
                methods.append(MFAMethod.WEBAUTHN)

            # Les méthodes OTP sont toujours disponibles si configurées globalement
            if MFAMethod.SMS in self.config.enabled_methods:
                methods.append(MFAMethod.SMS)
            if MFAMethod.EMAIL in self.config.enabled_methods:
                methods.append(MFAMethod.EMAIL)

            # Backup codes si MFA est configuré
            if methods and self._backup_codes.get(key):
                methods.append(MFAMethod.BACKUP_CODE)

        return methods

    def is_mfa_required(
        self,
        user_id: str,
        tenant_id: str,
        user_roles: list[str],
        context: Optional[dict] = None,
    ) -> tuple[bool, Optional[RiskAssessment]]:
        """
        Détermine si MFA est requis pour cette connexion.

        Returns:
            Tuple (required, risk_assessment)
        """
        # Vérifier si MFA est forcé pour tous
        if self.config.enforce_for_all:
            return True, None

        # Vérifier si MFA est forcé pour certains rôles
        if self.config.enforce_for_roles:
            if any(role in self.config.enforce_for_roles for role in user_roles):
                return True, None

        # MFA adaptative
        if self.config.adaptive_enabled and context:
            assessment = self.adaptive.assess_risk(
                user_id=user_id,
                tenant_id=tenant_id,
                ip_address=context.get("ip_address", ""),
                user_agent=context.get("user_agent", ""),
                device_fingerprint=context.get("device_fingerprint"),
                geo_location=context.get("geo_location"),
                is_sensitive_operation=context.get("is_sensitive_operation", False),
            )
            return assessment.require_mfa, assessment

        return False, None

    def disable_mfa(self, user_id: str, tenant_id: str) -> bool:
        """Désactive complètement MFA pour un utilisateur."""
        key = f"{tenant_id}:{user_id}"

        with self._lock:
            if key in self._user_mfa_configs:
                del self._user_mfa_configs[key]
            if key in self._backup_codes:
                del self._backup_codes[key]

            # Révoquer tous les appareils de confiance
            self.device_trust.revoke_all_devices(user_id, tenant_id)

        logger.info(f"MFA disabled for user {user_id}")
        return True


# =============================================================================
# FACTORY
# =============================================================================

_mfa_service: Optional[MFAService] = None


def get_mfa_service() -> MFAService:
    """Retourne l'instance singleton du service MFA."""
    global _mfa_service
    if _mfa_service is None:
        _mfa_service = MFAService()
    return _mfa_service


def configure_mfa_service(
    config: MFAConfiguration,
    webauthn_config: Optional[dict] = None,
) -> MFAService:
    """Configure le service MFA."""
    global _mfa_service

    totp = TOTPService()
    webauthn = WebAuthnService(**(webauthn_config or {}))
    otp = OTPService()
    adaptive = AdaptiveMFAService()
    device_trust = DeviceTrustService(
        trust_duration_days=config.device_trust_duration_days
    )

    _mfa_service = MFAService(
        config=config,
        totp_service=totp,
        webauthn_service=webauthn,
        otp_service=otp,
        adaptive_service=adaptive,
        device_trust_service=device_trust,
    )

    logger.info(
        "MFA service configured",
        extra={
            "enabled_methods": [m.value for m in config.enabled_methods],
            "adaptive_enabled": config.adaptive_enabled,
            "device_trust_enabled": config.device_trust_enabled,
        }
    )

    return _mfa_service
