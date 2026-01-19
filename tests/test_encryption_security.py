"""
AZALS - Tests de Securite Chiffrement
Validation du chiffrement des donnees sensibles
"""

import json
import os
import pytest

# Configurer l'environnement de test AVANT tout import
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_encryption.db")
os.environ.setdefault("SECRET_KEY", "test-key-minimum-32-characters-long-for-tests")
os.environ.setdefault("ENCRYPTION_KEY", "8DxR9qZ4tK2vP7mN5wL3jH6gF0cB1aXy2EiU4oS8dYs=")
os.environ.setdefault("BOOTSTRAP_SECRET", "test-bootstrap-minimum-32-characters-here")
os.environ.setdefault("ENVIRONMENT", "test")

from app.core.encryption import (
    FieldEncryption,
    encrypt_value,
    decrypt_value,
    generate_encryption_key,
    EncryptionError
)


class TestFieldEncryption:
    """Tests pour le service de chiffrement."""

    def test_encrypt_decrypt_round_trip(self):
        """
        Test: Chiffrer puis dechiffrer retourne la valeur originale.
        """
        original = "secret_password_123"

        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)

        assert decrypted == original
        assert encrypted != original  # Doit etre different

    def test_encrypt_different_outputs(self):
        """
        Test: Chiffrer la meme valeur produit des resultats differents (IV aleatoire).
        """
        value = "test_value"

        enc1 = encrypt_value(value)
        enc2 = encrypt_value(value)

        # Fernet utilise un IV aleatoire, donc les sorties doivent etre differentes
        assert enc1 != enc2

        # Mais le dechiffrement doit retourner la meme valeur
        assert decrypt_value(enc1) == value
        assert decrypt_value(enc2) == value

    def test_empty_value_returns_empty(self):
        """
        Test: Chiffrer une valeur vide retourne une chaine vide.
        """
        assert encrypt_value("") == ""
        assert decrypt_value("") == ""

    def test_none_value_handled(self):
        """
        Test: Chiffrer None retourne une chaine vide.
        """
        assert encrypt_value(None) == ""
        assert decrypt_value(None) == ""

    def test_encrypted_format_fernet(self):
        """
        Test: Les valeurs chiffrees commencent par le prefixe Fernet.
        """
        encrypted = encrypt_value("test")

        # Fernet tokens commencent toujours par 'gAAAAA'
        assert encrypted.startswith("gAAAAA")

    def test_decrypt_corrupted_data_raises_error(self):
        """
        Test: Dechiffrer des donnees corrompues leve une erreur.
        """
        corrupted = "not_a_valid_fernet_token"

        with pytest.raises(EncryptionError):
            decrypt_value(corrupted)


class TestMFAEncryption:
    """Tests pour le chiffrement MFA."""

    def test_mfa_secret_encryption(self):
        """
        Test: Le secret TOTP est correctement chiffre.
        """
        # Simuler un secret TOTP base32
        totp_secret = "JBSWY3DPEHPK3PXP"

        encrypted = encrypt_value(totp_secret)
        decrypted = decrypt_value(encrypted)

        assert decrypted == totp_secret
        assert encrypted != totp_secret

    def test_backup_codes_encryption(self):
        """
        Test: Les codes de secours sont correctement chiffres.
        """
        backup_codes = ["ABC123", "DEF456", "GHI789"]
        codes_json = json.dumps(backup_codes)

        encrypted = encrypt_value(codes_json)
        decrypted = decrypt_value(encrypted)

        assert json.loads(decrypted) == backup_codes


class TestWebhookAuthConfigEncryption:
    """Tests pour le chiffrement des configurations webhook."""

    def test_auth_config_encryption(self):
        """
        Test: La configuration auth webhook est correctement chiffree.
        """
        auth_config = {
            "api_key": "sk_live_xxxxxxxxxxxxx",
            "username": "admin",
            "password": "super_secret_password"
        }
        config_json = json.dumps(auth_config)

        encrypted = encrypt_value(config_json)
        decrypted = decrypt_value(encrypted)

        assert json.loads(decrypted) == auth_config

        # Verifier que les secrets ne sont pas visibles dans la version chiffree
        assert "sk_live" not in encrypted
        assert "super_secret" not in encrypted


class TestBankTokenEncryption:
    """Tests pour le chiffrement des tokens bancaires."""

    def test_access_token_encryption(self):
        """
        Test: Le token d'acces bancaire est correctement chiffre.
        """
        access_token = "access-xxxxxxxxxxxxxxxxxxxxxxxxxxx"

        encrypted = encrypt_value(access_token)
        decrypted = decrypt_value(encrypted)

        assert decrypted == access_token
        assert "access-" not in encrypted

    def test_refresh_token_encryption(self):
        """
        Test: Le refresh token bancaire est correctement chiffre.
        """
        refresh_token = "refresh-yyyyyyyyyyyyyyyyyyyyyyyyyy"

        encrypted = encrypt_value(refresh_token)
        decrypted = decrypt_value(encrypted)

        assert decrypted == refresh_token


class TestEncryptionKeyGeneration:
    """Tests pour la generation de cles."""

    def test_generate_valid_key(self):
        """
        Test: Les cles generees sont valides pour Fernet.
        """
        key = generate_encryption_key()

        # La cle doit etre une chaine base64 valide
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet key length

    def test_generated_keys_are_unique(self):
        """
        Test: Chaque generation produit une cle unique.
        """
        keys = [generate_encryption_key() for _ in range(10)]

        # Toutes les cles doivent etre differentes
        assert len(set(keys)) == 10


class TestEncryptionPerformance:
    """Tests de performance basiques."""

    def test_encrypt_large_data(self):
        """
        Test: Peut chiffrer des donnees volumineuses.
        """
        large_data = "x" * 100000  # 100KB

        encrypted = encrypt_value(large_data)
        decrypted = decrypt_value(encrypted)

        assert decrypted == large_data

    def test_encrypt_many_values(self):
        """
        Test: Peut chiffrer de nombreuses valeurs rapidement.
        """
        values = [f"value_{i}" for i in range(100)]

        encrypted = [encrypt_value(v) for v in values]
        decrypted = [decrypt_value(e) for e in encrypted]

        assert decrypted == values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
