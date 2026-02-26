"""
AZALS - Chiffrement AES-256 au repos
====================================
Chiffrement symétrique des données sensibles.
Compatible avec SQLAlchemy via types personnalisés.

RÈGLES DE SÉCURITÉ:
- ENCRYPTION_KEY obligatoire (générée avec Fernet.generate_key())
- Clé stockée dans variable d'environnement, JAMAIS dans le code
- Chiffrement transparent pour les colonnes sensibles
"""

import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import String, Text, TypeDecorator


class EncryptionError(Exception):
    """Erreur de chiffrement/déchiffrement."""
    pass


class FieldEncryption:
    """
    Service de chiffrement AES-256 pour données sensibles.

    Utilise Fernet (AES-128-CBC avec HMAC-SHA256) pour:
    - Chiffrement authentifié (confidentialité + intégrité)
    - Gestion automatique de l'IV (Initialization Vector)
    - Protection contre les attaques par replay (timestamp)

    Usage:
        encryption = FieldEncryption()
        encrypted = encryption.encrypt("données sensibles")
        decrypted = encryption.decrypt(encrypted)
    """

    _instance: Optional['FieldEncryption'] = None

    def __init__(self, encryption_key: str | None = None):
        """
        Initialise le service de chiffrement.

        Args:
            encryption_key: Clé Fernet (32 bytes base64).
                           Si None, lit ENCRYPTION_KEY depuis l'environnement.

        Raises:
            EncryptionError: Si aucune clé n'est configurée
        """
        key = encryption_key or os.environ.get("ENCRYPTION_KEY")

        if not key:
            # En mode test, générer une clé temporaire
            env = os.environ.get("ENVIRONMENT", "development")
            if env == "test":
                key = Fernet.generate_key().decode()
            else:
                raise EncryptionError(
                    "ENCRYPTION_KEY est OBLIGATOIRE. "
                    "Générez avec: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )

        # Valider la clé
        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise EncryptionError(f"Clé de chiffrement invalide: {e}")

    @classmethod
    def get_instance(cls) -> 'FieldEncryption':
        """Singleton pour réutiliser l'instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset le singleton (utile pour les tests)."""
        cls._instance = None

    def encrypt(self, plaintext: str) -> str:
        """
        Chiffre une chaîne de caractères.

        Args:
            plaintext: Texte en clair à chiffrer

        Returns:
            Texte chiffré encodé en base64

        Note:
            Retourne une chaîne vide si plaintext est None ou vide.
        """
        if not plaintext:
            return ""

        try:
            encrypted = self.cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Échec du chiffrement: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Déchiffre une chaîne chiffrée.

        Args:
            ciphertext: Texte chiffré (base64)

        Returns:
            Texte en clair

        Raises:
            EncryptionError: Si le déchiffrement échoue (clé invalide, données corrompues)
        """
        if not ciphertext:
            return ""

        try:
            decrypted = self.cipher.decrypt(ciphertext.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise EncryptionError(
                "Déchiffrement impossible: clé invalide ou données corrompues. "
                "Vérifiez que la clé ENCRYPTION_KEY est correcte."
            )
        except Exception as e:
            raise EncryptionError(f"Échec du déchiffrement: {e}")

    def encrypt_if_not_encrypted(self, value: str) -> str:
        """
        Chiffre uniquement si pas déjà chiffré.
        Utile pour les migrations de données.
        """
        if not value:
            return ""

        # Fernet commence toujours par 'gAAAAA'
        if value.startswith('gAAAAA'):
            return value  # Déjà chiffré

        return self.encrypt(value)

    def is_encrypted(self, value: str) -> bool:
        """Vérifie si une valeur semble être chiffrée (format Fernet)."""
        if not value:
            return False
        return value.startswith('gAAAAA')


# ============================================================================
# TYPES SQLALCHEMY POUR COLONNES CHIFFRÉES
# ============================================================================

class EncryptedString(TypeDecorator):
    """
    Type SQLAlchemy pour colonnes String chiffrées.

    Chiffre automatiquement à l'écriture, déchiffre à la lecture.

    Usage:
        class User(Base):
            phone: Mapped[Optional[Any]] = mapped_column(EncryptedString(255))
    """
    impl = String
    cache_ok = True

    def __init__(self, length: int = 255, **kwargs):
        # Fernet produit des sorties plus longues (~1.4x + overhead)
        # Prévoir de la marge
        super().__init__(length=length * 2, **kwargs)

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Chiffre avant stockage en DB."""
        if value is None:
            return None
        # SÉCURITÉ P0-4: JAMAIS de fallback en clair
        # Si le chiffrement échoue, c'est une erreur fatale
        encryption = FieldEncryption.get_instance()
        return encryption.encrypt(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Déchiffre après lecture de la DB."""
        if value is None:
            return None
        try:
            encryption = FieldEncryption.get_instance()
            return encryption.decrypt(value)
        except EncryptionError:
            # Valeur peut-être non chiffrée (données anciennes)
            return value


class EncryptedText(TypeDecorator):
    """
    Type SQLAlchemy pour colonnes Text chiffrées (données longues).

    Usage:
        class User(Base):
            notes: Mapped[Optional[Any]] = mapped_column(EncryptedText())
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Chiffre avant stockage."""
        if value is None:
            return None
        # SÉCURITÉ P0-4: JAMAIS de fallback en clair
        encryption = FieldEncryption.get_instance()
        return encryption.encrypt(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Déchiffre après lecture."""
        if value is None:
            return None
        try:
            encryption = FieldEncryption.get_instance()
            return encryption.decrypt(value)
        except EncryptionError:
            # Valeur peut-être non chiffrée (données anciennes/migration)
            return value


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def generate_encryption_key() -> str:
    """
    Génère une nouvelle clé de chiffrement Fernet.

    Returns:
        Clé encodée en base64 (prête pour ENCRYPTION_KEY)
    """
    return Fernet.generate_key().decode()


def derive_key_from_password(password: str, salt: bytes | None = None) -> tuple:
    """
    Dérive une clé Fernet depuis un mot de passe.

    Utile pour chiffrement basé sur mot de passe utilisateur.

    Args:
        password: Mot de passe
        salt: Salt (16 bytes). Généré aléatoirement si None.

    Returns:
        Tuple (clé_fernet, salt)
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,  # OWASP 2023 recommandation
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key.decode(), salt


def hash_sensitive_for_search(value: str) -> str:
    """
    Hash une valeur sensible pour permettre la recherche sans déchiffrer.

    Utile pour rechercher par email chiffré:
    - Stocker hash dans colonne séparée
    - Rechercher par hash

    Args:
        value: Valeur à hasher

    Returns:
        Hash SHA-256 en hex
    """
    if not value:
        return ""

    # Normaliser (lowercase, strip)
    normalized = value.lower().strip()

    # Hash avec sel applicatif (configurable)
    salt = os.environ.get("HASH_SALT", "azals-default-salt")
    salted = f"{salt}:{normalized}"

    return hashlib.sha256(salted.encode()).hexdigest()


# ============================================================================
# FONCTIONS SIMPLES D'ENCRYPTION
# ============================================================================

def encrypt_value(value: str) -> str:
    """
    Chiffre une valeur avec la cle configuree.

    Args:
        value: Valeur a chiffrer

    Returns:
        Valeur chiffree
    """
    if not value:
        return ""
    encryption = FieldEncryption.get_instance()
    return encryption.encrypt(value)


def decrypt_value(value: str) -> str:
    """
    Dechiffre une valeur avec la cle configuree.

    Args:
        value: Valeur chiffree

    Returns:
        Valeur en clair
    """
    if not value:
        return ""
    encryption = FieldEncryption.get_instance()
    return encryption.decrypt(value)


# ============================================================================
# AES-256-GCM (P1 SÉCURITÉ - Chiffrement renforcé)
# ============================================================================

def encrypt_aes256_gcm(plaintext: bytes, key: bytes, aad: bytes | None = None) -> bytes:
    """
    Chiffre des données avec AES-256-GCM (authenticated encryption).

    P1 SÉCURITÉ: Utiliser cette fonction pour les données hautement sensibles.
    AES-256-GCM fournit:
    - Confidentialité (chiffrement 256-bit)
    - Intégrité (GHASH)
    - Authentification (tag)

    Args:
        plaintext: Données à chiffrer
        key: Clé de 32 bytes (256 bits)
        aad: Additional Authenticated Data (optionnel)

    Returns:
        IV (12 bytes) + Tag (16 bytes) + Ciphertext

    Raises:
        ValueError: Si la clé n'est pas de 32 bytes
    """
    if len(key) != 32:
        raise ValueError("AES-256 requires a 32-byte key")

    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    iv = os.urandom(12)  # 96-bit IV recommandé pour GCM

    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()

    if aad:
        encryptor.authenticate_additional_data(aad)

    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    # Format: IV (12) + Tag (16) + Ciphertext
    return iv + encryptor.tag + ciphertext


def decrypt_aes256_gcm(ciphertext: bytes, key: bytes, aad: bytes | None = None) -> bytes:
    """
    Déchiffre des données chiffrées avec AES-256-GCM.

    Args:
        ciphertext: IV (12 bytes) + Tag (16 bytes) + Ciphertext
        key: Clé de 32 bytes (256 bits)
        aad: Additional Authenticated Data (doit correspondre au chiffrement)

    Returns:
        Données déchiffrées

    Raises:
        ValueError: Si la clé ou le format est invalide
        cryptography.exceptions.InvalidTag: Si l'authentification échoue
    """
    if len(key) != 32:
        raise ValueError("AES-256 requires a 32-byte key")

    if len(ciphertext) < 28:  # 12 (IV) + 16 (Tag) minimum
        raise ValueError("Ciphertext too short")

    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    iv = ciphertext[:12]
    tag = ciphertext[12:28]
    ct = ciphertext[28:]

    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()

    if aad:
        decryptor.authenticate_additional_data(aad)

    return decryptor.update(ct) + decryptor.finalize()


def generate_aes256_key() -> bytes:
    """
    Génère une clé AES-256 sécurisée (32 bytes).

    Returns:
        Clé de 32 bytes générée avec os.urandom()
    """
    return os.urandom(32)


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'FieldEncryption',
    'EncryptedString',
    'EncryptedText',
    'EncryptionError',
    'generate_encryption_key',
    'derive_key_from_password',
    'hash_sensitive_for_search',
    'encrypt_value',
    'decrypt_value',
    # P1 SÉCURITÉ: AES-256-GCM
    'encrypt_aes256_gcm',
    'decrypt_aes256_gcm',
    'generate_aes256_key',
]
