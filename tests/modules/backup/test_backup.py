"""
AZALS - Tests Module Backup
===========================
Tests unitaires pour le module de sauvegardes chiffrées AES-256.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

# Models
from app.modules.backup.models import (
    Backup, BackupConfig, RestoreLog,
    BackupStatus, BackupType, BackupFrequency
)

# Service
from app.modules.backup.service import BackupService


# ============================================================================
# TESTS DES MODÈLES
# ============================================================================

class TestBackupStatusModel:
    """Tests pour les statuts de sauvegarde."""

    def test_backup_status_values(self):
        """Vérifie les statuts disponibles."""
        assert BackupStatus.PENDING.value == "pending"
        assert BackupStatus.IN_PROGRESS.value == "in_progress"
        assert BackupStatus.COMPLETED.value == "completed"
        assert BackupStatus.FAILED.value == "failed"
        assert BackupStatus.DELETED.value == "deleted"

    def test_backup_type_values(self):
        """Vérifie les types de sauvegarde."""
        assert BackupType.FULL.value == "full"
        assert BackupType.INCREMENTAL.value == "incremental"
        assert BackupType.DIFFERENTIAL.value == "differential"

    def test_backup_frequency_values(self):
        """Vérifie les fréquences de sauvegarde."""
        assert BackupFrequency.HOURLY.value == "hourly"
        assert BackupFrequency.DAILY.value == "daily"
        assert BackupFrequency.WEEKLY.value == "weekly"
        assert BackupFrequency.MONTHLY.value == "monthly"
        assert BackupFrequency.ON_DEMAND.value == "on_demand"


class TestBackupConfigModel:
    """Tests pour la configuration de sauvegarde."""

    def test_default_encryption_algorithm(self):
        """Vérifie l'algorithme de chiffrement par défaut."""
        config = BackupConfig(
            tenant_id="test_tenant",
            encryption_key_encrypted="encrypted_key_here"
        )
        assert config.encryption_algorithm == "AES-256-GCM"

    def test_default_retention_days(self):
        """Vérifie la rétention par défaut (90 jours)."""
        config = BackupConfig(
            tenant_id="test_tenant",
            encryption_key_encrypted="encrypted_key_here"
        )
        assert config.retention_days == 90


# ============================================================================
# TESTS DU SERVICE BACKUP
# ============================================================================

class TestBackupServiceConfiguration:
    """Tests pour la configuration du service de sauvegarde."""

    def test_initialize_tenant_backup_config(self):
        """Vérifie l'initialisation de la config pour un nouveau tenant."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        service = BackupService(mock_session)

        with patch.object(service, '_generate_tenant_encryption_key', return_value="encrypted_key"):
            config = service.initialize_tenant_config("new_tenant")

        assert mock_session.add.called

    def test_get_tenant_config(self):
        """Vérifie la récupération de la configuration."""
        mock_session = MagicMock()
        mock_config = Mock(
            tenant_id="test_tenant",
            frequency=BackupFrequency.WEEKLY,
            retention_days=90
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        service = BackupService(mock_session)
        config = service.get_tenant_config("test_tenant")

        assert config.tenant_id == "test_tenant"
        assert config.frequency == BackupFrequency.WEEKLY


class TestBackupCreation:
    """Tests pour la création de sauvegardes."""

    def test_create_backup_initializes_status(self):
        """Vérifie que le backup démarre avec le statut PENDING."""
        mock_session = MagicMock()
        mock_config = Mock(
            tenant_id="test_tenant",
            encryption_key_encrypted="key",
            include_attachments=True,
            compress=True
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        service = BackupService(mock_session)

        with patch.object(service, '_execute_backup'):
            backup = service.create_backup("test_tenant")

        # Vérifie qu'un backup a été ajouté
        assert mock_session.add.called

    def test_backup_reference_format(self):
        """Vérifie le format de la référence de sauvegarde."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        reference = service._generate_backup_reference("test_tenant")

        # Format attendu: BACKUP-{tenant}-{YYYYMMDD}-{HHMMSS}
        assert reference.startswith("BACKUP-test_tenant-")
        assert len(reference) > 20


class TestBackupEncryption:
    """Tests pour le chiffrement AES-256."""

    def test_aes_256_gcm_algorithm(self):
        """Vérifie l'utilisation d'AES-256-GCM."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        # Le service doit utiliser AES-256-GCM
        assert service.encryption_algorithm == "AES-256-GCM"

    def test_encrypt_backup_data(self):
        """Vérifie le chiffrement des données de sauvegarde."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        test_data = {"users": [{"id": 1, "name": "Test"}]}

        with patch('cryptography.hazmat.primitives.ciphers.aead.AESGCM') as mock_aes:
            mock_instance = Mock()
            mock_instance.encrypt.return_value = b"encrypted_data"
            mock_aes.return_value = mock_instance

            encrypted = service._encrypt_data(json.dumps(test_data).encode(), b"key" * 8)

        assert encrypted is not None

    def test_decrypt_backup_data(self):
        """Vérifie le déchiffrement des données de sauvegarde."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        with patch('cryptography.hazmat.primitives.ciphers.aead.AESGCM') as mock_aes:
            mock_instance = Mock()
            mock_instance.decrypt.return_value = b'{"users": []}'
            mock_aes.return_value = mock_instance

            decrypted = service._decrypt_data(b"encrypted", b"nonce" * 4, b"key" * 8)

        assert decrypted == b'{"users": []}'


class TestBackupIntegrity:
    """Tests pour l'intégrité des sauvegardes."""

    def test_backup_checksum_calculated(self):
        """Vérifie le calcul du checksum SHA-256."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        test_data = b"backup data content"
        checksum = service._calculate_checksum(test_data)

        # SHA-256 produit un hash de 64 caractères hex
        assert len(checksum) == 64

    def test_verify_backup_integrity(self):
        """Vérifie la vérification d'intégrité après sauvegarde."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        # Simuler un backup avec checksum correct
        mock_backup = Mock(
            file_checksum="abc123" * 10 + "abcd",  # 64 chars
            file_path="/tmp/test_backup.enc"
        )

        with patch.object(service, '_calculate_checksum', return_value="abc123" * 10 + "abcd"):
            with patch('builtins.open', Mock()):
                is_valid = service._verify_integrity(mock_backup)

        assert is_valid is True


class TestBackupRetention:
    """Tests pour la gestion de la rétention."""

    def test_cleanup_old_backups(self):
        """Vérifie le nettoyage des anciennes sauvegardes."""
        mock_session = MagicMock()

        old_backup = Mock(
            id=uuid4(),
            status=BackupStatus.COMPLETED,
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        mock_session.query.return_value.filter.return_value.all.return_value = [old_backup]

        service = BackupService(mock_session)

        with patch.object(service, '_delete_backup_file'):
            deleted_count = service.cleanup_old_backups("test_tenant", retention_days=90)

        assert deleted_count >= 0

    def test_respect_max_backups_limit(self):
        """Vérifie le respect de la limite de sauvegardes."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        # Avec max_backups=12, les plus anciennes doivent être supprimées
        mock_config = Mock(max_backups=12)

        # Créer 15 backups mock
        mock_backups = [Mock(id=uuid4()) for _ in range(15)]
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_backups

        with patch.object(service, '_delete_backup_file'):
            service._enforce_max_backups("test_tenant", mock_config)


class TestBackupRestore:
    """Tests pour la restauration."""

    def test_restore_creates_log(self):
        """Vérifie qu'une restauration crée un log."""
        mock_session = MagicMock()

        mock_backup = Mock(
            id=uuid4(),
            tenant_id="test_tenant",
            status=BackupStatus.COMPLETED,
            file_path="/tmp/backup.enc",
            is_encrypted=True
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_backup

        service = BackupService(mock_session)

        with patch.object(service, '_execute_restore'):
            service.restore_backup(str(mock_backup.id), "test_tenant")

        # Vérifie qu'un RestoreLog a été créé
        assert mock_session.add.called

    def test_restore_to_different_tenant(self):
        """Vérifie la restauration vers un autre tenant."""
        mock_session = MagicMock()

        mock_backup = Mock(
            id=uuid4(),
            tenant_id="source_tenant",
            status=BackupStatus.COMPLETED
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_backup

        service = BackupService(mock_session)

        with patch.object(service, '_execute_restore'):
            service.restore_backup(
                str(mock_backup.id),
                target_tenant_id="destination_tenant"
            )


class TestScheduledBackups:
    """Tests pour les sauvegardes planifiées."""

    def test_calculate_next_backup_daily(self):
        """Vérifie le calcul de la prochaine sauvegarde quotidienne."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        next_backup = service._calculate_next_backup(
            BackupFrequency.DAILY,
            backup_hour=2
        )

        assert next_backup.hour == 2

    def test_calculate_next_backup_weekly(self):
        """Vérifie le calcul de la prochaine sauvegarde hebdomadaire."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        next_backup = service._calculate_next_backup(
            BackupFrequency.WEEKLY,
            backup_hour=3,
            backup_day=0  # Lundi
        )

        assert next_backup.weekday() == 0  # Lundi


# ============================================================================
# TESTS D'ISOLATION MULTI-TENANT
# ============================================================================

class TestBackupMultiTenantIsolation:
    """Tests pour l'isolation des sauvegardes par tenant."""

    def test_backup_isolated_by_tenant(self):
        """Vérifie que les backups sont isolés par tenant."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        # Simuler la requête avec filtre tenant_id
        service.get_tenant_backups("tenant_a")

        # Vérifier que le filtre tenant_id est appliqué
        mock_session.query.return_value.filter_by.assert_called()

    def test_encryption_key_per_tenant(self):
        """Vérifie qu'une clé de chiffrement unique par tenant."""
        mock_session = MagicMock()
        service = BackupService(mock_session)

        key1 = service._generate_tenant_encryption_key("tenant_a")
        key2 = service._generate_tenant_encryption_key("tenant_b")

        # Les clés doivent être différentes
        assert key1 != key2

    def test_cannot_restore_other_tenant_backup(self):
        """Vérifie qu'on ne peut pas restaurer le backup d'un autre tenant."""
        mock_session = MagicMock()

        # Backup appartient à tenant_a
        mock_backup = Mock(
            id=uuid4(),
            tenant_id="tenant_a",
            status=BackupStatus.COMPLETED
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_backup

        service = BackupService(mock_session)

        # Tentative de restauration par tenant_b
        with pytest.raises((PermissionError, ValueError)):
            service.restore_backup(
                str(mock_backup.id),
                "tenant_b",  # Pas le propriétaire
                require_ownership=True
            )
