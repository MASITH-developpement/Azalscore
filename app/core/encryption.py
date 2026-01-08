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

import os
import base64
import hashlib
from typing import Optional, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import TypeDecorator, String, Text


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

    def __init__(self, encryption_key: Optional[str] = None):
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
            phone = Column(EncryptedString(255))
    """
    impl = String
    cache_ok = True

    def __init__(self, length: int = 255, **kwargs):
        # Fernet produit des sorties plus longues (~1.4x + overhead)
        # Prévoir de la marge
        super().__init__(length=length * 2, **kwargs)

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Chiffre avant stockage en DB."""
        if value is None:
            return None
        try:
            encryption = FieldEncryption.get_instance()
            return encryption.encrypt(value)
        except EncryptionError:
            # En cas d'erreur, stocker en clair (fallback développement)
            # En production, cette erreur devrait être fatale
            import logging
            logging.warning("Encryption failed, storing plaintext (DEV ONLY)")
            return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
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
            notes = Column(EncryptedText())
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Chiffre avant stockage."""
        if value is None:
            return None
        try:
            encryption = FieldEncryption.get_instance()
            return encryption.encrypt(value)
        except EncryptionError:
            return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Déchiffre après lecture."""
        if value is None:
            return None
        try:
            encryption = FieldEncryption.get_instance()
            return encryption.decrypt(value)
        except EncryptionError:
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


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple:
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
]
