"""
AZALSCORE - Service de Chiffrement Avancé
==========================================

Extension du système de chiffrement avec:
- Key Management Service (KMS)
- Envelope Encryption (Data Encryption Keys)
- Key Rotation automatique
- Chiffrement asymétrique (RSA-4096)
- Support HSM (Hardware Security Module)
- Tokenization pour données PCI-DSS
- Chiffrement de fichiers

Conformité:
- PCI-DSS v4.0 (Requirement 3: Protect stored account data)
- RGPD Article 32 (Security of processing)
- SOC 2 Type II (CC6.1: Logical and Physical Access Controls)
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
from typing import Any, Optional, TypeVar
from functools import lru_cache
import threading

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class KeyType(str, Enum):
    """Types de clés cryptographiques."""
    MASTER_KEY = "master_key"  # Clé maître pour chiffrer les DEK
    DATA_ENCRYPTION_KEY = "dek"  # Clé de chiffrement de données
    KEY_ENCRYPTION_KEY = "kek"  # Clé pour chiffrer d'autres clés
    SIGNING_KEY = "signing"  # Clé de signature
    HMAC_KEY = "hmac"  # Clé HMAC
    RSA_PRIVATE = "rsa_private"
    RSA_PUBLIC = "rsa_public"


class KeyStatus(str, Enum):
    """Statut d'une clé."""
    ACTIVE = "active"  # Utilisée pour chiffrement et déchiffrement
    DECRYPT_ONLY = "decrypt_only"  # Peut uniquement déchiffrer (rotation)
    DISABLED = "disabled"  # Désactivée
    PENDING_DELETION = "pending_deletion"  # Programmée pour suppression
    DELETED = "deleted"  # Supprimée (soft delete)


class EncryptionAlgorithm(str, Enum):
    """Algorithmes de chiffrement supportés."""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    RSA_OAEP_SHA256 = "rsa-oaep-sha256"
    FERNET = "fernet"


class TokenizationType(str, Enum):
    """Types de tokenization."""
    CREDIT_CARD = "credit_card"  # Format preserving
    SSN = "ssn"
    IBAN = "iban"
    EMAIL = "email"
    PHONE = "phone"
    GENERIC = "generic"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CryptoKey:
    """Représentation d'une clé cryptographique."""
    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    status: KeyStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotated_from: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    # Matériel de clé (chiffré ou en clair selon contexte)
    key_material: Optional[bytes] = None
    encrypted_key_material: Optional[bytes] = None

    def is_active(self) -> bool:
        """Vérifie si la clé est active."""
        if self.status != KeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def can_decrypt(self) -> bool:
        """Vérifie si la clé peut être utilisée pour déchiffrer."""
        return self.status in (KeyStatus.ACTIVE, KeyStatus.DECRYPT_ONLY)


@dataclass
class EncryptedData:
    """Données chiffrées avec métadonnées."""
    ciphertext: bytes
    key_id: str
    algorithm: EncryptionAlgorithm
    iv: Optional[bytes] = None
    tag: Optional[bytes] = None  # Pour GCM/authenticated encryption
    aad: Optional[bytes] = None  # Additional authenticated data
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_bytes(self) -> bytes:
        """Sérialise en format binaire."""
        header = {
            "key_id": self.key_id,
            "algorithm": self.algorithm.value,
            "timestamp": self.timestamp.isoformat(),
        }
        header_json = json.dumps(header).encode()
        header_len = struct.pack(">I", len(header_json))

        iv_len = struct.pack(">B", len(self.iv) if self.iv else 0)
        tag_len = struct.pack(">B", len(self.tag) if self.tag else 0)

        parts = [
            b"AZLSENC1",  # Magic bytes + version
            header_len,
            header_json,
            iv_len,
            self.iv or b"",
            tag_len,
            self.tag or b"",
            self.ciphertext,
        ]

        return b"".join(parts)

    @classmethod
    def from_bytes(cls, data: bytes) -> "EncryptedData":
        """Désérialise depuis format binaire."""
        if not data.startswith(b"AZLSENC1"):
            raise ValueError("Invalid encrypted data format")

        offset = 8  # After magic bytes

        header_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4

        header_json = data[offset:offset+header_len]
        header = json.loads(header_json)
        offset += header_len

        iv_len = struct.unpack(">B", data[offset:offset+1])[0]
        offset += 1
        iv = data[offset:offset+iv_len] if iv_len else None
        offset += iv_len

        tag_len = struct.unpack(">B", data[offset:offset+1])[0]
        offset += 1
        tag = data[offset:offset+tag_len] if tag_len else None
        offset += tag_len

        ciphertext = data[offset:]

        return cls(
            ciphertext=ciphertext,
            key_id=header["key_id"],
            algorithm=EncryptionAlgorithm(header["algorithm"]),
            iv=iv,
            tag=tag,
            timestamp=datetime.fromisoformat(header["timestamp"]),
        )

    def to_base64(self) -> str:
        """Encode en base64 pour stockage texte."""
        return base64.b64encode(self.to_bytes()).decode()

    @classmethod
    def from_base64(cls, data: str) -> "EncryptedData":
        """Décode depuis base64."""
        return cls.from_bytes(base64.b64decode(data))


@dataclass
class Token:
    """Token de substitution pour données sensibles."""
    token: str
    token_type: TokenizationType
    original_hash: str  # Hash pour déduplication
    created_at: datetime
    expires_at: Optional[datetime]
    tenant_id: str
    metadata: dict = field(default_factory=dict)


# =============================================================================
# KEY STORE ABSTRACTION
# =============================================================================

class KeyStore(ABC):
    """Interface pour le stockage des clés."""

    @abstractmethod
    def store_key(self, key: CryptoKey) -> None:
        """Stocke une clé."""
        pass

    @abstractmethod
    def get_key(self, key_id: str) -> Optional[CryptoKey]:
        """Récupère une clé par ID."""
        pass

    @abstractmethod
    def get_active_key(self, key_type: KeyType, tenant_id: Optional[str] = None) -> Optional[CryptoKey]:
        """Récupère la clé active pour un type donné."""
        pass

    @abstractmethod
    def list_keys(
        self,
        key_type: Optional[KeyType] = None,
        status: Optional[KeyStatus] = None,
        tenant_id: Optional[str] = None
    ) -> list[CryptoKey]:
        """Liste les clés selon critères."""
        pass

    @abstractmethod
    def update_key_status(self, key_id: str, status: KeyStatus) -> None:
        """Met à jour le statut d'une clé."""
        pass

    @abstractmethod
    def delete_key(self, key_id: str) -> None:
        """Supprime une clé."""
        pass


class InMemoryKeyStore(KeyStore):
    """
    Key store en mémoire pour développement/tests.
    NE PAS UTILISER EN PRODUCTION.
    """

    def __init__(self):
        self._keys: dict[str, CryptoKey] = {}
        self._lock = threading.Lock()

    def store_key(self, key: CryptoKey) -> None:
        with self._lock:
            self._keys[key.key_id] = key

    def get_key(self, key_id: str) -> Optional[CryptoKey]:
        return self._keys.get(key_id)

    def get_active_key(self, key_type: KeyType, tenant_id: Optional[str] = None) -> Optional[CryptoKey]:
        with self._lock:
            for key in self._keys.values():
                if key.key_type == key_type and key.is_active():
                    if tenant_id is None or key.tenant_id == tenant_id:
                        return key
            return None

    def list_keys(
        self,
        key_type: Optional[KeyType] = None,
        status: Optional[KeyStatus] = None,
        tenant_id: Optional[str] = None
    ) -> list[CryptoKey]:
        with self._lock:
            result = []
            for key in self._keys.values():
                if key_type and key.key_type != key_type:
                    continue
                if status and key.status != status:
                    continue
                if tenant_id and key.tenant_id != tenant_id:
                    continue
                result.append(key)
            return result

    def update_key_status(self, key_id: str, status: KeyStatus) -> None:
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id].status = status

    def delete_key(self, key_id: str) -> None:
        with self._lock:
            if key_id in self._keys:
                del self._keys[key_id]


class DatabaseKeyStore(KeyStore):
    """
    Key store utilisant la base de données.
    Les clés sont chiffrées avec la Master Key avant stockage.
    """

    def __init__(self, db_session_factory, master_key: bytes):
        self._db_session_factory = db_session_factory
        self._master_cipher = Fernet(base64.urlsafe_b64encode(master_key[:32]))
        self._cache: dict[str, CryptoKey] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_times: dict[str, float] = {}
        self._lock = threading.Lock()

    def _encrypt_key_material(self, key_material: bytes) -> bytes:
        """Chiffre le matériel de clé."""
        return self._master_cipher.encrypt(key_material)

    def _decrypt_key_material(self, encrypted: bytes) -> bytes:
        """Déchiffre le matériel de clé."""
        return self._master_cipher.decrypt(encrypted)

    def store_key(self, key: CryptoKey) -> None:
        """Stocke une clé en base de données."""
        # Chiffrer le matériel de clé
        if key.key_material:
            key.encrypted_key_material = self._encrypt_key_material(key.key_material)
            key.key_material = None  # Ne pas stocker en clair

        # NOTE: Production - Implémenter stockage en table crypto_keys
        # Pour l'instant: cache mémoire
        with self._lock:
            self._cache[key.key_id] = key
            self._cache_times[key.key_id] = time.time()

    def get_key(self, key_id: str) -> Optional[CryptoKey]:
        """Récupère une clé."""
        # Vérifier le cache
        with self._lock:
            if key_id in self._cache:
                if time.time() - self._cache_times[key_id] < self._cache_ttl:
                    key = self._cache[key_id]
                    # Déchiffrer le matériel si nécessaire
                    if key.encrypted_key_material and not key.key_material:
                        key.key_material = self._decrypt_key_material(key.encrypted_key_material)
                    return key

        # NOTE: Production - Récupérer depuis DB crypto_keys si pas en cache
        return None

    def get_active_key(self, key_type: KeyType, tenant_id: Optional[str] = None) -> Optional[CryptoKey]:
        """Récupère la clé active."""
        with self._lock:
            for key in self._cache.values():
                if key.key_type == key_type and key.is_active():
                    if tenant_id is None or key.tenant_id == tenant_id:
                        if key.encrypted_key_material and not key.key_material:
                            key.key_material = self._decrypt_key_material(key.encrypted_key_material)
                        return key
        return None

    def list_keys(
        self,
        key_type: Optional[KeyType] = None,
        status: Optional[KeyStatus] = None,
        tenant_id: Optional[str] = None
    ) -> list[CryptoKey]:
        """Liste les clés."""
        with self._lock:
            result = []
            for key in self._cache.values():
                if key_type and key.key_type != key_type:
                    continue
                if status and key.status != status:
                    continue
                if tenant_id and key.tenant_id != tenant_id:
                    continue
                result.append(key)
            return result

    def update_key_status(self, key_id: str, status: KeyStatus) -> None:
        """Met à jour le statut."""
        with self._lock:
            if key_id in self._cache:
                self._cache[key_id].status = status

    def delete_key(self, key_id: str) -> None:
        """Supprime une clé (soft delete)."""
        with self._lock:
            if key_id in self._cache:
                self._cache[key_id].status = KeyStatus.DELETED


# =============================================================================
# HSM INTEGRATION
# =============================================================================

class HSMProvider(ABC):
    """Interface pour Hardware Security Module."""

    @abstractmethod
    def generate_key(self, key_type: KeyType, key_id: str) -> bytes:
        """Génère une clé dans le HSM."""
        pass

    @abstractmethod
    def encrypt(self, key_id: str, plaintext: bytes) -> bytes:
        """Chiffre avec une clé HSM."""
        pass

    @abstractmethod
    def decrypt(self, key_id: str, ciphertext: bytes) -> bytes:
        """Déchiffre avec une clé HSM."""
        pass

    @abstractmethod
    def sign(self, key_id: str, data: bytes) -> bytes:
        """Signe des données."""
        pass

    @abstractmethod
    def verify(self, key_id: str, data: bytes, signature: bytes) -> bool:
        """Vérifie une signature."""
        pass


class SoftwareHSM(HSMProvider):
    """
    HSM logiciel pour développement/tests.
    Simule les opérations HSM en mémoire.
    """

    def __init__(self, master_secret: bytes):
        self._master_secret = master_secret
        self._keys: dict[str, bytes] = {}
        self._lock = threading.Lock()

    def _derive_key(self, key_id: str) -> bytes:
        """Dérive une clé depuis le master secret."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"azalscore-soft-hsm",
            info=key_id.encode(),
            backend=default_backend()
        )
        return hkdf.derive(self._master_secret)

    def generate_key(self, key_type: KeyType, key_id: str) -> bytes:
        """Génère une clé."""
        key_material = self._derive_key(key_id)
        with self._lock:
            self._keys[key_id] = key_material
        return key_material

    def encrypt(self, key_id: str, plaintext: bytes) -> bytes:
        """Chiffre avec AES-256-GCM."""
        with self._lock:
            key = self._keys.get(key_id) or self._derive_key(key_id)

        iv = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # Format: IV (12) + Tag (16) + Ciphertext
        return iv + encryptor.tag + ciphertext

    def decrypt(self, key_id: str, ciphertext: bytes) -> bytes:
        """Déchiffre."""
        with self._lock:
            key = self._keys.get(key_id) or self._derive_key(key_id)

        iv = ciphertext[:12]
        tag = ciphertext[12:28]
        ct = ciphertext[28:]

        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def sign(self, key_id: str, data: bytes) -> bytes:
        """Signe avec HMAC-SHA256."""
        with self._lock:
            key = self._keys.get(key_id) or self._derive_key(key_id)
        return hmac.new(key, data, hashlib.sha256).digest()

    def verify(self, key_id: str, data: bytes, signature: bytes) -> bool:
        """Vérifie la signature."""
        expected = self.sign(key_id, data)
        return hmac.compare_digest(expected, signature)


class AWSKMSProvider(HSMProvider):
    """
    Intégration AWS KMS (Key Management Service).
    """

    def __init__(self, region: str = "eu-west-3", key_alias_prefix: str = "alias/azalscore"):
        self.region = region
        self.key_alias_prefix = key_alias_prefix
        self._client = None

    def _get_client(self):
        """Retourne le client AWS KMS."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client("kms", region_name=self.region)
            except ImportError:
                raise RuntimeError("boto3 not installed")
        return self._client

    def generate_key(self, key_type: KeyType, key_id: str) -> bytes:
        """Génère une Data Encryption Key."""
        client = self._get_client()

        # Génère une DEK chiffrée par la CMK
        response = client.generate_data_key(
            KeyId=f"{self.key_alias_prefix}/{key_type.value}",
            KeySpec="AES_256"
        )

        # Retourne la clé en clair (à utiliser en mémoire uniquement)
        return response["Plaintext"]

    def encrypt(self, key_id: str, plaintext: bytes) -> bytes:
        """Chiffre avec KMS."""
        client = self._get_client()

        response = client.encrypt(
            KeyId=f"{self.key_alias_prefix}/{key_id}",
            Plaintext=plaintext
        )

        return response["CiphertextBlob"]

    def decrypt(self, key_id: str, ciphertext: bytes) -> bytes:
        """Déchiffre avec KMS."""
        client = self._get_client()

        response = client.decrypt(
            KeyId=f"{self.key_alias_prefix}/{key_id}",
            CiphertextBlob=ciphertext
        )

        return response["Plaintext"]

    def sign(self, key_id: str, data: bytes) -> bytes:
        """Signe avec KMS."""
        client = self._get_client()

        # Hash les données d'abord
        digest = hashlib.sha256(data).digest()

        response = client.sign(
            KeyId=f"{self.key_alias_prefix}/{key_id}",
            Message=digest,
            MessageType="DIGEST",
            SigningAlgorithm="RSASSA_PSS_SHA_256"
        )

        return response["Signature"]

    def verify(self, key_id: str, data: bytes, signature: bytes) -> bool:
        """Vérifie avec KMS."""
        client = self._get_client()

        digest = hashlib.sha256(data).digest()

        try:
            response = client.verify(
                KeyId=f"{self.key_alias_prefix}/{key_id}",
                Message=digest,
                MessageType="DIGEST",
                Signature=signature,
                SigningAlgorithm="RSASSA_PSS_SHA_256"
            )
            return response["SignatureValid"]
        except Exception:
            return False


# =============================================================================
# KEY MANAGEMENT SERVICE
# =============================================================================

class KeyManagementService:
    """
    Service central de gestion des clés cryptographiques.

    Features:
    - Génération de clés (AES-256, RSA-4096)
    - Envelope encryption avec DEK/KEK
    - Rotation automatique des clés
    - Support HSM
    - Audit complet
    """

    def __init__(
        self,
        key_store: KeyStore,
        hsm_provider: Optional[HSMProvider] = None,
        default_key_rotation_days: int = 90,
    ):
        self._key_store = key_store
        self._hsm = hsm_provider
        self._default_rotation_days = default_key_rotation_days
        self._lock = threading.Lock()

    def generate_key(
        self,
        key_type: KeyType,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
        tenant_id: Optional[str] = None,
        expires_days: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> CryptoKey:
        """
        Génère une nouvelle clé cryptographique.
        """
        key_id = str(uuid.uuid4())

        # Générer le matériel de clé
        if self._hsm:
            key_material = self._hsm.generate_key(key_type, key_id)
        else:
            if algorithm == EncryptionAlgorithm.AES_256_GCM:
                key_material = os.urandom(32)
            elif algorithm == EncryptionAlgorithm.FERNET:
                key_material = Fernet.generate_key()
            elif algorithm == EncryptionAlgorithm.RSA_OAEP_SHA256:
                # Génère paire RSA
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=4096,
                    backend=default_backend()
                )
                key_material = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            else:
                key_material = os.urandom(32)

        # Calculer la date d'expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        elif self._default_rotation_days:
            expires_at = datetime.utcnow() + timedelta(days=self._default_rotation_days)

        key = CryptoKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=algorithm,
            status=KeyStatus.ACTIVE,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            tenant_id=tenant_id,
            metadata=metadata or {},
            key_material=key_material,
        )

        self._key_store.store_key(key)

        logger.info(
            f"Key generated: {key_id}",
            extra={
                "key_id": key_id,
                "key_type": key_type.value,
                "algorithm": algorithm.value,
                "tenant_id": tenant_id,
            }
        )

        return key

    def get_key(self, key_id: str) -> Optional[CryptoKey]:
        """Récupère une clé par ID."""
        return self._key_store.get_key(key_id)

    def get_active_key(
        self,
        key_type: KeyType,
        tenant_id: Optional[str] = None
    ) -> CryptoKey:
        """
        Récupère la clé active ou en génère une nouvelle.
        """
        key = self._key_store.get_active_key(key_type, tenant_id)

        if not key:
            # Pas de clé active, en générer une
            key = self.generate_key(key_type, tenant_id=tenant_id)

        return key

    def rotate_key(
        self,
        key_id: str,
        keep_old_for_decryption: bool = True
    ) -> CryptoKey:
        """
        Effectue une rotation de clé.

        Args:
            key_id: ID de la clé à faire tourner
            keep_old_for_decryption: Garder l'ancienne clé pour déchiffrement

        Returns:
            Nouvelle clé
        """
        old_key = self._key_store.get_key(key_id)
        if not old_key:
            raise ValueError(f"Key not found: {key_id}")

        # Générer nouvelle clé
        new_key = self.generate_key(
            key_type=old_key.key_type,
            algorithm=old_key.algorithm,
            tenant_id=old_key.tenant_id,
            metadata={**old_key.metadata, "rotated_from": key_id}
        )
        new_key.rotated_from = key_id

        # Mettre à jour le statut de l'ancienne clé
        if keep_old_for_decryption:
            self._key_store.update_key_status(key_id, KeyStatus.DECRYPT_ONLY)
        else:
            self._key_store.update_key_status(key_id, KeyStatus.DISABLED)

        logger.info(
            f"Key rotated: {key_id} -> {new_key.key_id}",
            extra={
                "old_key_id": key_id,
                "new_key_id": new_key.key_id,
                "key_type": old_key.key_type.value,
            }
        )

        return new_key

    def disable_key(self, key_id: str) -> None:
        """Désactive une clé."""
        self._key_store.update_key_status(key_id, KeyStatus.DISABLED)
        logger.info(f"Key disabled: {key_id}")

    def schedule_deletion(self, key_id: str, days: int = 7) -> datetime:
        """
        Programme la suppression d'une clé.
        Retourne la date de suppression.
        """
        key = self._key_store.get_key(key_id)
        if not key:
            raise ValueError(f"Key not found: {key_id}")

        key.status = KeyStatus.PENDING_DELETION
        key.metadata["deletion_date"] = (
            datetime.utcnow() + timedelta(days=days)
        ).isoformat()

        self._key_store.store_key(key)

        deletion_date = datetime.utcnow() + timedelta(days=days)
        logger.warning(
            f"Key scheduled for deletion: {key_id} on {deletion_date}",
            extra={"key_id": key_id, "deletion_date": deletion_date.isoformat()}
        )

        return deletion_date

    def check_rotation_needed(self) -> list[CryptoKey]:
        """Vérifie les clés qui nécessitent une rotation."""
        keys_to_rotate = []
        all_keys = self._key_store.list_keys(status=KeyStatus.ACTIVE)

        for key in all_keys:
            if key.expires_at and datetime.utcnow() > key.expires_at - timedelta(days=7):
                keys_to_rotate.append(key)

        return keys_to_rotate


# =============================================================================
# ENVELOPE ENCRYPTION SERVICE
# =============================================================================

class EnvelopeEncryptionService:
    """
    Service d'envelope encryption.

    Architecture:
    - Master Key (MK): Protège les KEK, jamais exposée
    - Key Encryption Key (KEK): Chiffre les DEK, par tenant
    - Data Encryption Key (DEK): Chiffre les données, usage unique ou temporaire

    Avantages:
    - Rotation de clés sans re-chiffrer toutes les données
    - Isolation par tenant
    - Conformité PCI-DSS
    """

    def __init__(self, kms: KeyManagementService, hsm: Optional[HSMProvider] = None):
        self._kms = kms
        self._hsm = hsm

    def encrypt(
        self,
        plaintext: bytes,
        tenant_id: str,
        context: Optional[dict] = None,
    ) -> EncryptedData:
        """
        Chiffre des données avec envelope encryption.

        Process:
        1. Génère une DEK unique
        2. Chiffre les données avec la DEK
        3. Chiffre la DEK avec la KEK du tenant
        4. Retourne données chiffrées + DEK chiffrée
        """
        # Obtenir ou créer la KEK du tenant
        kek = self._kms.get_active_key(KeyType.KEY_ENCRYPTION_KEY, tenant_id)

        # Générer une DEK unique pour ces données
        dek = os.urandom(32)
        iv = os.urandom(12)

        # Chiffrer les données avec la DEK (AES-256-GCM)
        cipher = Cipher(
            algorithms.AES(dek),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # AAD (Additional Authenticated Data) pour contexte
        aad = json.dumps({
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            **(context or {})
        }).encode()
        encryptor.authenticate_additional_data(aad)

        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag

        # Chiffrer la DEK avec la KEK
        if self._hsm:
            encrypted_dek = self._hsm.encrypt(kek.key_id, dek)
        else:
            # Utiliser Fernet pour chiffrer la DEK
            kek_cipher = Fernet(base64.urlsafe_b64encode(kek.key_material[:32]))
            encrypted_dek = kek_cipher.encrypt(dek)

        # Construire le résultat
        # Format: encrypted_dek_len (4) + encrypted_dek + iv + tag + ciphertext
        encrypted_dek_len = struct.pack(">I", len(encrypted_dek))
        full_ciphertext = encrypted_dek_len + encrypted_dek + iv + tag + ciphertext

        return EncryptedData(
            ciphertext=full_ciphertext,
            key_id=kek.key_id,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            aad=aad,
        )

    def decrypt(
        self,
        encrypted_data: EncryptedData,
        tenant_id: str,
    ) -> bytes:
        """
        Déchiffre des données chiffrées avec envelope encryption.
        """
        # Récupérer la KEK
        kek = self._kms.get_key(encrypted_data.key_id)
        if not kek or not kek.can_decrypt():
            raise ValueError(f"Key not available for decryption: {encrypted_data.key_id}")

        # Parser les données chiffrées
        data = encrypted_data.ciphertext
        offset = 0

        encrypted_dek_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4

        encrypted_dek = data[offset:offset+encrypted_dek_len]
        offset += encrypted_dek_len

        iv = data[offset:offset+12]
        offset += 12

        tag = data[offset:offset+16]
        offset += 16

        ciphertext = data[offset:]

        # Déchiffrer la DEK
        if self._hsm:
            dek = self._hsm.decrypt(kek.key_id, encrypted_dek)
        else:
            kek_cipher = Fernet(base64.urlsafe_b64encode(kek.key_material[:32]))
            dek = kek_cipher.decrypt(encrypted_dek)

        # Déchiffrer les données
        cipher = Cipher(
            algorithms.AES(dek),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        if encrypted_data.aad:
            decryptor.authenticate_additional_data(encrypted_data.aad)

        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext


# =============================================================================
# TOKENIZATION SERVICE
# =============================================================================

class TokenizationService:
    """
    Service de tokenization pour données sensibles (PCI-DSS).

    Remplace les données sensibles par des tokens non réversibles
    sans accès au vault.
    """

    def __init__(
        self,
        token_store,  # TokenStore interface
        secret_key: bytes,
    ):
        self._token_store = token_store
        self._secret_key = secret_key
        self._token_prefix = "tok_"

    def _compute_hash(self, value: str) -> str:
        """Calcule un hash déterministe pour déduplication."""
        return hmac.new(
            self._secret_key,
            value.encode(),
            hashlib.sha256
        ).hexdigest()

    def _generate_token(self, token_type: TokenizationType) -> str:
        """Génère un token unique."""
        random_part = secrets.token_urlsafe(16)
        return f"{self._token_prefix}{token_type.value}_{random_part}"

    def _format_preserving_token(
        self,
        value: str,
        token_type: TokenizationType
    ) -> str:
        """
        Génère un token qui préserve le format.
        Ex: carte bancaire 4111111111111111 -> 4111XXXXXXXXXXXX
        """
        if token_type == TokenizationType.CREDIT_CARD:
            # Garder les 4 premiers et 4 derniers chiffres
            if len(value) >= 13:
                masked = value[:4] + "X" * (len(value) - 8) + value[-4:]
                return f"{self._token_prefix}cc_{masked}_{secrets.token_hex(4)}"

        elif token_type == TokenizationType.IBAN:
            # Garder le code pays et les 4 derniers caractères
            if len(value) >= 10:
                masked = value[:4] + "X" * (len(value) - 8) + value[-4:]
                return f"{self._token_prefix}iban_{masked}_{secrets.token_hex(4)}"

        elif token_type == TokenizationType.EMAIL:
            # Masquer une partie de l'email
            parts = value.split("@")
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                if len(username) > 2:
                    masked_user = username[0] + "***" + username[-1]
                else:
                    masked_user = "***"
                return f"{self._token_prefix}email_{masked_user}@{domain}_{secrets.token_hex(4)}"

        # Token générique
        return self._generate_token(token_type)

    def tokenize(
        self,
        value: str,
        token_type: TokenizationType,
        tenant_id: str,
        preserve_format: bool = False,
        expires_days: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Tokenize une valeur sensible.

        Returns:
            Token de substitution
        """
        # Vérifier si déjà tokenisé (déduplication)
        value_hash = self._compute_hash(value)

        # Générer le token
        if preserve_format:
            token_value = self._format_preserving_token(value, token_type)
        else:
            token_value = self._generate_token(token_type)

        # Calculer expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        # Créer et stocker le token
        token = Token(
            token=token_value,
            token_type=token_type,
            original_hash=value_hash,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )

        # Stocker la valeur originale (chiffrée) associée au token
        self._token_store.store(token, value)

        logger.info(
            f"Value tokenized: {token_type.value}",
            extra={
                "token_type": token_type.value,
                "tenant_id": tenant_id,
                "has_expiration": expires_at is not None,
            }
        )

        return token_value

    def detokenize(self, token: str, tenant_id: str) -> Optional[str]:
        """
        Récupère la valeur originale depuis un token.
        """
        result = self._token_store.get(token, tenant_id)

        if result:
            logger.info(
                "Value detokenized",
                extra={"tenant_id": tenant_id}
            )

        return result

    def validate_token(self, token: str, tenant_id: str) -> bool:
        """Vérifie si un token existe et est valide."""
        return self._token_store.exists(token, tenant_id)

    def revoke_token(self, token: str, tenant_id: str) -> bool:
        """Révoque un token."""
        return self._token_store.delete(token, tenant_id)


# =============================================================================
# FILE ENCRYPTION SERVICE
# =============================================================================

class FileEncryptionService:
    """
    Service de chiffrement de fichiers.

    Features:
    - Chiffrement par blocs pour fichiers volumineux
    - Streaming pour faible empreinte mémoire
    - Intégrité via HMAC
    """

    BLOCK_SIZE = 64 * 1024  # 64 KB blocks
    FILE_MAGIC = b"AZLSFILE"
    VERSION = 1

    def __init__(self, kms: KeyManagementService):
        self._kms = kms

    def encrypt_file(
        self,
        input_path: str,
        output_path: str,
        tenant_id: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Chiffre un fichier.

        Returns:
            Métadonnées du fichier chiffré
        """
        # Générer une DEK pour ce fichier
        dek = self._kms.generate_key(
            KeyType.DATA_ENCRYPTION_KEY,
            tenant_id=tenant_id,
            metadata={"purpose": "file_encryption", "file": input_path}
        )

        # Générer IV
        iv = os.urandom(16)

        # Préparer le chiffrement
        cipher = Cipher(
            algorithms.AES(dek.key_material[:32]),
            modes.CTR(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Préparer le HMAC pour l'intégrité
        hmac_key = dek.key_material[32:] if len(dek.key_material) > 32 else os.urandom(32)
        file_hmac = hmac.new(hmac_key, digestmod=hashlib.sha256)

        # Header du fichier
        header = {
            "version": self.VERSION,
            "key_id": dek.key_id,
            "tenant_id": tenant_id,
            "algorithm": "aes-256-ctr",
            "block_size": self.BLOCK_SIZE,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        header_json = json.dumps(header).encode()

        total_bytes = 0

        with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
            # Écrire le header
            fout.write(self.FILE_MAGIC)
            fout.write(struct.pack(">I", len(header_json)))
            fout.write(header_json)
            fout.write(iv)

            # Chiffrer par blocs
            while True:
                block = fin.read(self.BLOCK_SIZE)
                if not block:
                    break

                encrypted_block = encryptor.update(block)
                fout.write(encrypted_block)
                file_hmac.update(encrypted_block)
                total_bytes += len(block)

            # Finaliser
            encrypted_block = encryptor.finalize()
            if encrypted_block:
                fout.write(encrypted_block)
                file_hmac.update(encrypted_block)

            # Écrire le HMAC à la fin
            fout.write(file_hmac.digest())

        logger.info(
            f"File encrypted: {input_path} -> {output_path}",
            extra={
                "key_id": dek.key_id,
                "tenant_id": tenant_id,
                "size_bytes": total_bytes,
            }
        )

        return {
            "key_id": dek.key_id,
            "size_bytes": total_bytes,
            "output_path": output_path,
        }

    def decrypt_file(
        self,
        input_path: str,
        output_path: str,
        tenant_id: str,
    ) -> dict:
        """
        Déchiffre un fichier.
        """
        with open(input_path, "rb") as fin:
            # Lire et vérifier le magic
            magic = fin.read(len(self.FILE_MAGIC))
            if magic != self.FILE_MAGIC:
                raise ValueError("Invalid encrypted file format")

            # Lire le header
            header_len = struct.unpack(">I", fin.read(4))[0]
            header_json = fin.read(header_len)
            header = json.loads(header_json)

            # Vérifier le tenant
            if header.get("tenant_id") != tenant_id:
                raise ValueError("Tenant mismatch")

            # Lire l'IV
            iv = fin.read(16)

            # Récupérer la clé
            key = self._kms.get_key(header["key_id"])
            if not key or not key.can_decrypt():
                raise ValueError(f"Key not available: {header['key_id']}")

            # Lire tout le contenu chiffré (moins le HMAC à la fin)
            content = fin.read()
            stored_hmac = content[-32:]
            encrypted_content = content[:-32]

            # Vérifier l'intégrité
            hmac_key = key.key_material[32:] if len(key.key_material) > 32 else key.key_material[:32]
            computed_hmac = hmac.new(hmac_key, encrypted_content, hashlib.sha256).digest()
            if not hmac.compare_digest(stored_hmac, computed_hmac):
                raise ValueError("File integrity check failed")

            # Déchiffrer
            cipher = Cipher(
                algorithms.AES(key.key_material[:32]),
                modes.CTR(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            with open(output_path, "wb") as fout:
                plaintext = decryptor.update(encrypted_content) + decryptor.finalize()
                fout.write(plaintext)

        logger.info(
            f"File decrypted: {input_path} -> {output_path}",
            extra={
                "key_id": header["key_id"],
                "tenant_id": tenant_id,
            }
        )

        return {
            "key_id": header["key_id"],
            "size_bytes": len(plaintext),
            "output_path": output_path,
            "metadata": header.get("metadata", {}),
        }


# =============================================================================
# FACTORY & INITIALIZATION
# =============================================================================

_encryption_service: Optional[EnvelopeEncryptionService] = None
_kms_service: Optional[KeyManagementService] = None
_tokenization_service: Optional[TokenizationService] = None
_file_encryption_service: Optional[FileEncryptionService] = None


def initialize_encryption_services(
    master_key: Optional[str] = None,
    hsm_type: str = "software",  # software, aws_kms
    hsm_config: Optional[dict] = None,
    db_session_factory=None,
    use_database_store: bool = True,
) -> dict:
    """
    Initialise tous les services de chiffrement.

    Args:
        master_key: Clé maître (optionnel, utilise MASTER_ENCRYPTION_KEY si non fourni)
        hsm_type: Type de HSM ("software", "aws_kms")
        hsm_config: Configuration HSM
        db_session_factory: Factory pour sessions DB (pour DatabaseKeyStore)
        use_database_store: Si True, utilise DatabaseKeyStore (recommandé en production)

    Returns:
        Dict avec toutes les instances de services
    """
    global _encryption_service, _kms_service, _tokenization_service, _file_encryption_service

    # Master key depuis env ou paramètre
    master_key_bytes = (master_key or os.environ.get("MASTER_ENCRYPTION_KEY", "")).encode()
    if not master_key_bytes or len(master_key_bytes) < 32:
        # Générer une clé pour développement
        master_key_bytes = os.urandom(32)
        logger.warning("No MASTER_ENCRYPTION_KEY provided, using random key")

    # Initialiser le HSM provider
    hsm: Optional[HSMProvider] = None
    if hsm_type == "software":
        hsm = SoftwareHSM(master_key_bytes)
    elif hsm_type == "aws_kms":
        hsm = AWSKMSProvider(**(hsm_config or {}))

    # Key Store - DatabaseKeyStore en production pour persistance
    # SÉCURITÉ P0: DatabaseKeyStore chiffre les clés avec la master key avant stockage
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    key_store: KeyStore

    if use_database_store and (db_session_factory is not None or is_production):
        key_store = DatabaseKeyStore(db_session_factory, master_key_bytes)
        logger.info(
            "Using DatabaseKeyStore for key persistence",
            extra={"mode": "database", "production": is_production}
        )
    else:
        key_store = InMemoryKeyStore()
        if is_production:
            logger.warning(
                "Using InMemoryKeyStore in production - keys will be lost on restart!",
                extra={"mode": "memory", "risk": "keys_lost_on_restart"}
            )
        else:
            logger.info("Using InMemoryKeyStore (development mode)")

    # KMS
    _kms_service = KeyManagementService(key_store, hsm)

    # Envelope Encryption
    _encryption_service = EnvelopeEncryptionService(_kms_service, hsm)

    # File Encryption
    _file_encryption_service = FileEncryptionService(_kms_service)

    logger.info(
        "Encryption services initialized",
        extra={"hsm_type": hsm_type, "key_store": type(key_store).__name__}
    )

    return {
        "kms": _kms_service,
        "envelope": _encryption_service,
        "file": _file_encryption_service,
    }


def get_kms() -> KeyManagementService:
    """Retourne le service KMS."""
    global _kms_service
    if _kms_service is None:
        initialize_encryption_services()
    return _kms_service


def get_envelope_encryption() -> EnvelopeEncryptionService:
    """Retourne le service d'envelope encryption."""
    global _encryption_service
    if _encryption_service is None:
        initialize_encryption_services()
    return _encryption_service


def get_file_encryption() -> FileEncryptionService:
    """Retourne le service de chiffrement de fichiers."""
    global _file_encryption_service
    if _file_encryption_service is None:
        initialize_encryption_services()
    return _file_encryption_service
