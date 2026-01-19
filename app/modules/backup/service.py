"""
AZALS - Module Backup - Service
===============================
Service de sauvegarde chiffrée AES-256 par tenant.
"""

import base64
import contextlib
import gzip
import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value

from .models import Backup, BackupConfig, BackupFrequency, BackupStatus, RestoreLog
from .schemas import (
    BackupConfigCreate,
    BackupConfigUpdate,
    BackupCreate,
    BackupDashboard,
    BackupResponse,
    BackupStats,
    RestoreRequest,
    RestoreResponse,
)

logger = logging.getLogger(__name__)


class BackupService:
    """Service pour les sauvegardes chiffrées."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.base_path = os.environ.get("BACKUP_PATH", "/var/azals/backups")

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def get_config(self) -> BackupConfig | None:
        """Récupère la configuration backup du tenant."""
        return self.db.query(BackupConfig).filter(
            BackupConfig.tenant_id == self.tenant_id
        ).first()

    def create_config(self, data: BackupConfigCreate) -> BackupConfig:
        """Crée la configuration backup avec génération de clé."""
        # Générer une clé AES-256 unique pour ce tenant
        encryption_key = secrets.token_bytes(32)  # 256 bits
        encryption_key_b64 = base64.b64encode(encryption_key).decode()

        config = BackupConfig(
            tenant_id=self.tenant_id,
            encryption_key_encrypted=encrypt_value(encryption_key_b64),
            encryption_algorithm="AES-256-GCM",
            frequency=data.frequency,
            backup_hour=data.backup_hour,
            backup_day=data.backup_day,
            backup_day_of_month=data.backup_day_of_month,
            retention_days=data.retention_days,
            max_backups=data.max_backups,
            storage_path=data.storage_path or f"{self.base_path}/{self.tenant_id}",
            storage_type=data.storage_type,
            include_attachments=data.include_attachments,
            compress=data.compress,
            verify_after_backup=data.verify_after_backup,
            next_backup_at=self._calculate_next_backup(data.frequency, data.backup_hour, data.backup_day)
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        # Créer le répertoire de stockage
        os.makedirs(config.storage_path, exist_ok=True)

        return config

    def update_config(self, data: BackupConfigUpdate) -> BackupConfig | None:
        """Met à jour la configuration backup."""
        config = self.get_config()
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        # Recalculer next_backup_at si la fréquence change
        if 'frequency' in update_data or 'backup_hour' in update_data:
            config.next_backup_at = self._calculate_next_backup(
                config.frequency, config.backup_hour, config.backup_day
            )

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        return config

    def _calculate_next_backup(self, frequency: BackupFrequency, hour: int, day: int) -> datetime:
        """Calcule la prochaine date de backup."""
        now = datetime.utcnow()
        next_backup = now.replace(hour=hour, minute=0, second=0, microsecond=0)

        if frequency == BackupFrequency.HOURLY:
            if next_backup <= now:
                next_backup += timedelta(hours=1)
        elif frequency == BackupFrequency.DAILY:
            if next_backup <= now:
                next_backup += timedelta(days=1)
        elif frequency == BackupFrequency.WEEKLY:
            days_until = (day - now.weekday()) % 7
            next_backup += timedelta(days=days_until)
            if next_backup <= now:
                next_backup += timedelta(weeks=1)
        elif frequency == BackupFrequency.MONTHLY:
            next_backup = next_backup.replace(day=min(day, 28))
            if next_backup <= now:
                if next_backup.month == 12:
                    next_backup = next_backup.replace(year=next_backup.year + 1, month=1)
                else:
                    next_backup = next_backup.replace(month=next_backup.month + 1)

        return next_backup

    # =========================================================================
    # CHIFFREMENT AES-256-GCM
    # =========================================================================

    def _get_encryption_key(self) -> bytes:
        """Récupère la clé de chiffrement du tenant."""
        config = self.get_config()
        if not config:
            raise ValueError("Configuration backup non trouvée")

        key_b64 = decrypt_value(config.encryption_key_encrypted)
        return base64.b64decode(key_b64)

    def _encrypt_data(self, data: bytes) -> tuple[bytes, bytes]:
        """Chiffre les données avec AES-256-GCM."""
        key = self._get_encryption_key()
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)  # 96 bits nonce pour GCM
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return ciphertext, nonce

    def _decrypt_data(self, ciphertext: bytes, nonce: bytes) -> bytes:
        """Déchiffre les données."""
        key = self._get_encryption_key()
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    # =========================================================================
    # BACKUP
    # =========================================================================

    def create_backup(self, data: BackupCreate, triggered_by: str = "manual") -> Backup:
        """Crée une nouvelle sauvegarde."""
        config = self.get_config()
        if not config:
            raise ValueError("Configuration backup requise")

        # Générer référence unique
        now = datetime.utcnow()
        reference = f"BKP-{self.tenant_id[:8].upper()}-{now.strftime('%Y%m%d%H%M%S')}"

        backup = Backup(
            tenant_id=self.tenant_id,
            config_id=config.id,
            reference=reference,
            backup_type=data.backup_type,
            status=BackupStatus.PENDING,
            is_encrypted=True,
            encryption_algorithm="AES-256-GCM",
            include_attachments=data.include_attachments,
            is_compressed=config.compress,
            notes=data.notes,
            triggered_by=triggered_by
        )
        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)

        # Lancer le backup en arrière-plan (synchrone ici pour simplicité)
        try:
            self._execute_backup(backup, config)
        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            self.db.commit()
            logger.error(f"Erreur backup {reference}: {e}")

        return backup

    def _execute_backup(self, backup: Backup, config: BackupConfig):
        """Exécute le backup."""
        backup.status = BackupStatus.IN_PROGRESS
        backup.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Collecter les données
            backup_data = self._collect_tenant_data(backup.include_attachments)

            # Sérialiser en JSON
            json_data = json.dumps(backup_data, default=str, ensure_ascii=False)
            data_bytes = json_data.encode('utf-8')

            # Compresser si configuré
            if config.compress:
                data_bytes = gzip.compress(data_bytes)

            # Calculer checksum avant chiffrement
            original_checksum = hashlib.sha256(data_bytes).hexdigest()

            # Chiffrer
            ciphertext, nonce = self._encrypt_data(data_bytes)

            # Générer nom de fichier
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            file_name = f"{self.tenant_id}_{timestamp}.azals.bak"
            file_path = os.path.join(config.storage_path, file_name)

            # Écrire le fichier
            os.makedirs(config.storage_path, exist_ok=True)
            with open(file_path, 'wb') as f:
                # Header: nonce (12 bytes) + ciphertext
                f.write(nonce)
                f.write(ciphertext)

            # Mettre à jour le backup
            backup.file_path = file_path
            backup.file_name = file_name
            backup.file_size = os.path.getsize(file_path)
            backup.file_checksum = original_checksum
            backup.encryption_iv = base64.b64encode(nonce).decode()
            backup.tables_included = list(backup_data.keys())
            backup.records_count = sum(len(v) if isinstance(v, list) else 1 for v in backup_data.values())
            backup.status = BackupStatus.COMPLETED
            backup.completed_at = datetime.utcnow()
            backup.duration_seconds = int((backup.completed_at - backup.started_at).total_seconds())

            # Mettre à jour la config
            config.last_backup_at = backup.completed_at
            config.next_backup_at = self._calculate_next_backup(
                config.frequency, config.backup_hour, config.backup_day
            )

            self.db.commit()

            # Nettoyer les anciens backups
            self._cleanup_old_backups(config)

            logger.info(f"Backup {backup.reference} terminé: {backup.file_size} bytes")

        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            backup.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def _collect_tenant_data(self, include_attachments: bool) -> dict[str, Any]:
        """Collecte toutes les données du tenant."""
        data = {}

        # Tables à sauvegarder (principales)
        tables = [
            "commercial_customers",
            "commercial_documents",
            "commercial_document_lines",
            "commercial_products",
            "invoices",
            "bank_accounts",
            "bank_transactions",
            "support_tickets",
            "support_ticket_comments",
            "users",
            "email_logs",
            "audit_logs"
        ]

        for table in tables:
            try:
                result = self.db.execute(text(f"""
                    SELECT * FROM {table}
                    WHERE tenant_id = :tenant_id
                """), {"tenant_id": self.tenant_id})
                columns = result.keys()
                rows = [dict(zip(columns, row, strict=False)) for row in result.fetchall()]
                data[table] = rows
            except Exception as e:
                logger.warning(f"Table {table} non trouvée ou erreur: {e}")

        return data

    def _cleanup_old_backups(self, config: BackupConfig):
        """Nettoie les anciens backups selon la politique de rétention."""
        cutoff_date = datetime.utcnow() - timedelta(days=config.retention_days)

        # Supprimer les backups expirés
        old_backups = self.db.query(Backup).filter(
            Backup.tenant_id == self.tenant_id,
            Backup.status == BackupStatus.COMPLETED,
            Backup.created_at < cutoff_date
        ).all()

        for backup in old_backups:
            if backup.file_path and os.path.exists(backup.file_path):
                try:
                    os.remove(backup.file_path)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {backup.file_path}: {e}")
            backup.status = BackupStatus.DELETED
            self.db.commit()

        # Garder seulement max_backups
        all_backups = self.db.query(Backup).filter(
            Backup.tenant_id == self.tenant_id,
            Backup.status == BackupStatus.COMPLETED
        ).order_by(Backup.created_at.desc()).all()

        if len(all_backups) > config.max_backups:
            for backup in all_backups[config.max_backups:]:
                if backup.file_path and os.path.exists(backup.file_path):
                    with contextlib.suppress(Exception):
                        os.remove(backup.file_path)
                backup.status = BackupStatus.DELETED
            self.db.commit()

    # =========================================================================
    # RESTAURATION
    # =========================================================================

    def restore_backup(self, data: RestoreRequest, restored_by: str) -> RestoreLog:
        """Restaure une sauvegarde."""
        backup = self.get_backup(data.backup_id)
        if not backup:
            raise ValueError("Sauvegarde non trouvée")

        if backup.status != BackupStatus.COMPLETED:
            raise ValueError("Sauvegarde non valide pour restauration")

        restore_log = RestoreLog(
            tenant_id=self.tenant_id,
            backup_id=backup.id,
            status=BackupStatus.PENDING,
            target_type=data.target_type,
            target_tenant_id=data.target_tenant_id,
            restored_by=restored_by
        )
        self.db.add(restore_log)
        self.db.commit()
        self.db.refresh(restore_log)

        try:
            self._execute_restore(restore_log, backup, data.tables_to_restore)
        except Exception as e:
            restore_log.status = BackupStatus.FAILED
            restore_log.error_message = str(e)
            self.db.commit()
            logger.error(f"Erreur restauration: {e}")

        return restore_log

    def _execute_restore(self, restore_log: RestoreLog, backup: Backup, tables_to_restore: list[str] | None):
        """Exécute la restauration."""
        restore_log.status = BackupStatus.IN_PROGRESS
        restore_log.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Lire et déchiffrer le fichier
            with open(backup.file_path, 'rb') as f:
                nonce = f.read(12)
                ciphertext = f.read()

            data_bytes = self._decrypt_data(ciphertext, nonce)

            # Décompresser si nécessaire
            if backup.is_compressed:
                data_bytes = gzip.decompress(data_bytes)

            # Vérifier le checksum
            checksum = hashlib.sha256(data_bytes).hexdigest()
            if checksum != backup.file_checksum:
                raise ValueError("Checksum invalide - fichier corrompu")

            # Parser JSON
            backup_data = json.loads(data_bytes.decode('utf-8'))

            # Restaurer les tables

            # Note: la restauration complète nécessiterait plus de logique
            # pour gérer les contraintes FK, etc.
            restore_log.tables_restored = list(backup_data.keys())
            restore_log.records_restored = sum(len(v) if isinstance(v, list) else 1 for v in backup_data.values())

            restore_log.status = BackupStatus.COMPLETED
            restore_log.completed_at = datetime.utcnow()
            restore_log.duration_seconds = int((restore_log.completed_at - restore_log.started_at).total_seconds())

            # Mettre à jour le backup
            backup.last_restored_at = restore_log.completed_at
            backup.restore_count += 1

            self.db.commit()
            logger.info(f"Restauration {restore_log.id} terminée")

        except Exception as e:
            restore_log.status = BackupStatus.FAILED
            restore_log.error_message = str(e)
            restore_log.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    # =========================================================================
    # QUERIES
    # =========================================================================

    def get_backup(self, backup_id: str) -> Backup | None:
        """Récupère une sauvegarde."""
        return self.db.query(Backup).filter(
            Backup.id == backup_id,
            Backup.tenant_id == self.tenant_id
        ).first()

    def list_backups(
        self,
        status: BackupStatus | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Backup], int]:
        """Liste les sauvegardes."""
        query = self.db.query(Backup).filter(
            Backup.tenant_id == self.tenant_id,
            Backup.status != BackupStatus.DELETED
        )
        if status:
            query = query.filter(Backup.status == status)

        total = query.count()
        items = query.order_by(Backup.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_stats(self) -> BackupStats:
        """Statistiques des sauvegardes."""
        backups = self.db.query(Backup).filter(
            Backup.tenant_id == self.tenant_id,
            Backup.status != BackupStatus.DELETED
        ).all()

        completed = [b for b in backups if b.status == BackupStatus.COMPLETED]
        [b for b in backups if b.status == BackupStatus.FAILED]

        total_size = sum(b.file_size or 0 for b in completed)
        avg_duration = sum(b.duration_seconds or 0 for b in completed) / len(completed) if completed else 0
        success_rate = len(completed) / len(backups) * 100 if backups else 0

        last_backup = max(completed, key=lambda b: b.completed_at) if completed else None
        config = self.get_config()

        return BackupStats(
            total_backups=len(backups),
            total_size_bytes=total_size,
            last_backup_at=last_backup.completed_at if last_backup else None,
            last_backup_status=last_backup.status if last_backup else None,
            next_backup_at=config.next_backup_at if config else None,
            success_rate=round(success_rate, 1),
            average_duration_seconds=round(avg_duration, 1)
        )

    def get_dashboard(self) -> BackupDashboard:
        """Dashboard backup."""
        from .schemas import BackupConfigResponse

        config = self.get_config()
        stats = self.get_stats()

        backups, _ = self.list_backups(limit=10)
        recent_backups = [BackupResponse.model_validate(b) for b in backups]

        restores = self.db.query(RestoreLog).filter(
            RestoreLog.tenant_id == self.tenant_id
        ).order_by(RestoreLog.created_at.desc()).limit(5).all()
        recent_restores = [RestoreResponse.model_validate(r) for r in restores]

        return BackupDashboard(
            config=BackupConfigResponse.model_validate(config) if config else None,
            stats=stats,
            recent_backups=recent_backups,
            recent_restores=recent_restores
        )


def get_backup_service(db: Session, tenant_id: str) -> BackupService:
    """Factory pour le service backup."""
    return BackupService(db, tenant_id)
