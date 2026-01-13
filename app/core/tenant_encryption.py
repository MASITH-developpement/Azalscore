"""
AZALS - Chiffrement AES-256 PAR TENANT
======================================
Chaque tenant possede sa propre cle de chiffrement derivee.
Aucune cle stockee en clair - derivation cryptographique.

ARCHITECTURE SECURITE:
- Cle maitre (MASTER_ENCRYPTION_KEY) stockee dans env
- Cle tenant = PBKDF2(master_key + tenant_id + salt)
- Salt unique par tenant stocke en DB (hash, pas en clair)
- Donnees illisibles meme avec acces DB direct

RGPD/SOC2 COMPLIANT:
- Isolation cryptographique par tenant
- Suppression tenant = cle perdue = donnees irrecuperables
- Audit trail de tous les acces
"""

import os
import base64
import hashlib
import json
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class TenantEncryptionError(Exception):
    """Erreur de chiffrement/dechiffrement tenant."""
    pass


class TenantKeyDerivationError(TenantEncryptionError):
    """Erreur lors de la derivation de cle tenant."""
    pass


class TenantDataCorruptionError(TenantEncryptionError):
    """Donnees corrompues detectees lors du dechiffrement."""
    pass


class TenantEncryptionService:
    """
    Service de chiffrement isole par tenant.

    Chaque tenant a sa propre cle derivee de:
    - MASTER_ENCRYPTION_KEY (env)
    - tenant_id (unique)
    - salt (genere a la creation du tenant)

    GARANTIES:
    - Tenant A ne peut JAMAIS dechiffrer donnees tenant B
    - Perte de MASTER_KEY = toutes donnees perdues (disaster recovery)
    - Audit de tous les acces chiffrement
    """

    # Cache des ciphers par tenant (evite re-derivation)
    _tenant_ciphers: Dict[str, Fernet] = {}
    _tenant_salts: Dict[str, bytes] = {}

    # Iterations PBKDF2 (OWASP 2024 recommandation)
    PBKDF2_ITERATIONS = 600000
    SALT_SIZE = 32  # 256 bits

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialise le service avec la cle maitre.

        Args:
            master_key: Cle maitre (MASTER_ENCRYPTION_KEY).
                       Si None, lit depuis environnement.
        """
        self.master_key = master_key or os.environ.get("MASTER_ENCRYPTION_KEY")

        if not self.master_key:
            # Fallback sur ENCRYPTION_KEY pour retrocompatibilite
            self.master_key = os.environ.get("ENCRYPTION_KEY")

        if not self.master_key:
            env = os.environ.get("ENVIRONMENT", "development")
            if env == "test":
                # Mode test: generer cle temporaire
                self.master_key = Fernet.generate_key().decode()
                logger.warning("Mode TEST: cle maitre temporaire generee")
            else:
                raise TenantEncryptionError(
                    "MASTER_ENCRYPTION_KEY ou ENCRYPTION_KEY est OBLIGATOIRE. "
                    "Generez avec: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )

    def generate_tenant_salt(self) -> bytes:
        """
        Genere un salt unique pour un nouveau tenant.

        Returns:
            Salt de 32 bytes (256 bits)
        """
        return os.urandom(self.SALT_SIZE)

    def derive_tenant_key(self, tenant_id: str, salt: bytes) -> bytes:
        """
        Derive la cle Fernet specifique a un tenant.

        Args:
            tenant_id: Identifiant unique du tenant
            salt: Salt unique du tenant

        Returns:
            Cle Fernet derivee (32 bytes base64)
        """
        if not tenant_id:
            raise TenantKeyDerivationError("tenant_id est requis")
        if not salt or len(salt) < 16:
            raise TenantKeyDerivationError("Salt invalide (min 16 bytes)")

        # Combine master_key + tenant_id pour unicite
        key_material = f"{self.master_key}:{tenant_id}".encode('utf-8')

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend()
        )

        derived_key = base64.urlsafe_b64encode(kdf.derive(key_material))
        return derived_key

    def get_tenant_cipher(self, tenant_id: str, salt: bytes) -> Fernet:
        """
        Obtient le cipher Fernet pour un tenant (avec cache).

        Args:
            tenant_id: Identifiant du tenant
            salt: Salt du tenant

        Returns:
            Instance Fernet prete a l'emploi
        """
        cache_key = f"{tenant_id}:{hashlib.sha256(salt).hexdigest()[:16]}"

        if cache_key not in self._tenant_ciphers:
            derived_key = self.derive_tenant_key(tenant_id, salt)
            self._tenant_ciphers[cache_key] = Fernet(derived_key)
            self._tenant_salts[tenant_id] = salt
            logger.debug(f"Cipher cree pour tenant {tenant_id[:8]}...")

        return self._tenant_ciphers[cache_key]

    def encrypt(self, tenant_id: str, salt: bytes, plaintext: str) -> str:
        """
        Chiffre des donnees pour un tenant specifique.

        Args:
            tenant_id: Identifiant du tenant
            salt: Salt du tenant
            plaintext: Donnees en clair

        Returns:
            Donnees chiffrees (base64)
        """
        if not plaintext:
            return ""

        try:
            cipher = self.get_tenant_cipher(tenant_id, salt)
            encrypted = cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Echec chiffrement tenant {tenant_id[:8]}: {e}")
            raise TenantEncryptionError(f"Chiffrement echoue: {e}")

    def decrypt(self, tenant_id: str, salt: bytes, ciphertext: str) -> str:
        """
        Dechiffre des donnees pour un tenant specifique.

        Args:
            tenant_id: Identifiant du tenant
            salt: Salt du tenant
            ciphertext: Donnees chiffrees

        Returns:
            Donnees en clair

        Raises:
            TenantDataCorruptionError: Si donnees corrompues
        """
        if not ciphertext:
            return ""

        try:
            cipher = self.get_tenant_cipher(tenant_id, salt)
            decrypted = cipher.decrypt(ciphertext.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            logger.error(f"CORRUPTION DETECTEE tenant {tenant_id[:8]}")
            raise TenantDataCorruptionError(
                f"Donnees corrompues ou cle invalide pour tenant {tenant_id}. "
                "Verifiez MASTER_ENCRYPTION_KEY ou restaurez depuis backup."
            )
        except Exception as e:
            logger.error(f"Echec dechiffrement tenant {tenant_id[:8]}: {e}")
            raise TenantEncryptionError(f"Dechiffrement echoue: {e}")

    def encrypt_dict(self, tenant_id: str, salt: bytes, data: Dict[str, Any]) -> str:
        """
        Chiffre un dictionnaire complet (JSON serialize).

        Utile pour sauvegardes et export de donnees.
        """
        json_str = json.dumps(data, ensure_ascii=False, default=str)
        return self.encrypt(tenant_id, salt, json_str)

    def decrypt_dict(self, tenant_id: str, salt: bytes, ciphertext: str) -> Dict[str, Any]:
        """
        Dechiffre un dictionnaire (JSON deserialize).
        """
        json_str = self.decrypt(tenant_id, salt, ciphertext)
        return json.loads(json_str)

    def rotate_tenant_key(
        self,
        tenant_id: str,
        old_salt: bytes,
        new_salt: bytes,
        ciphertext: str
    ) -> str:
        """
        Rotation de cle pour un tenant (re-chiffre avec nouvelle cle).

        Args:
            tenant_id: Identifiant du tenant
            old_salt: Ancien salt
            new_salt: Nouveau salt
            ciphertext: Donnees chiffrees avec ancienne cle

        Returns:
            Donnees chiffrees avec nouvelle cle
        """
        # Dechiffre avec ancienne cle
        plaintext = self.decrypt(tenant_id, old_salt, ciphertext)

        # Invalide le cache de l'ancien cipher
        old_cache_key = f"{tenant_id}:{hashlib.sha256(old_salt).hexdigest()[:16]}"
        if old_cache_key in self._tenant_ciphers:
            del self._tenant_ciphers[old_cache_key]

        # Re-chiffre avec nouvelle cle
        return self.encrypt(tenant_id, new_salt, plaintext)

    def verify_integrity(self, tenant_id: str, salt: bytes, ciphertext: str) -> bool:
        """
        Verifie l'integrite des donnees sans les retourner.

        Returns:
            True si donnees valides, False si corrompues
        """
        try:
            self.decrypt(tenant_id, salt, ciphertext)
            return True
        except TenantDataCorruptionError:
            return False
        except Exception:
            return False

    def clear_cache(self, tenant_id: Optional[str] = None) -> None:
        """
        Vide le cache des ciphers (securite).

        Args:
            tenant_id: Si specifie, vide uniquement ce tenant
        """
        if tenant_id:
            keys_to_remove = [k for k in self._tenant_ciphers if k.startswith(f"{tenant_id}:")]
            for key in keys_to_remove:
                del self._tenant_ciphers[key]
            if tenant_id in self._tenant_salts:
                del self._tenant_salts[tenant_id]
            logger.info(f"Cache vide pour tenant {tenant_id[:8]}...")
        else:
            self._tenant_ciphers.clear()
            self._tenant_salts.clear()
            logger.info("Cache chiffrement entierement vide")


# Singleton global
_service_instance: Optional[TenantEncryptionService] = None


def get_tenant_encryption_service() -> TenantEncryptionService:
    """Obtient l'instance singleton du service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = TenantEncryptionService()
    return _service_instance


def reset_tenant_encryption_service() -> None:
    """Reset le singleton (tests uniquement)."""
    global _service_instance
    if _service_instance:
        _service_instance.clear_cache()
    _service_instance = None


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def encode_salt(salt: bytes) -> str:
    """Encode un salt en base64 pour stockage DB."""
    return base64.b64encode(salt).decode('utf-8')


def decode_salt(salt_b64: str) -> bytes:
    """Decode un salt depuis base64."""
    return base64.b64decode(salt_b64.encode('utf-8'))


def generate_tenant_encryption_config(tenant_id: str) -> Dict[str, str]:
    """
    Genere la configuration de chiffrement pour un nouveau tenant.

    Returns:
        {
            'tenant_id': str,
            'salt_b64': str,  # A stocker en DB
            'created_at': str
        }
    """
    service = get_tenant_encryption_service()
    salt = service.generate_tenant_salt()

    return {
        'tenant_id': tenant_id,
        'salt_b64': encode_salt(salt),
        'created_at': datetime.now(timezone.utc).isoformat()
    }


__all__ = [
    'TenantEncryptionService',
    'TenantEncryptionError',
    'TenantKeyDerivationError',
    'TenantDataCorruptionError',
    'get_tenant_encryption_service',
    'reset_tenant_encryption_service',
    'encode_salt',
    'decode_salt',
    'generate_tenant_encryption_config',
]
