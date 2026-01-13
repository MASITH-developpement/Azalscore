"""
AZALS - Module Backup - Modèles
===============================
Modèles de données pour les sauvegardes chiffrées.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, BigInteger, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class BackupStatus(str, Enum):
    """Statut d'une sauvegarde."""
    PENDING = "pending"          # En attente
    IN_PROGRESS = "in_progress"  # En cours
    COMPLETED = "completed"      # Terminée avec succès
    FAILED = "failed"            # Échec
    DELETED = "deleted"          # Supprimée


class BackupType(str, Enum):
    """Type de sauvegarde."""
    FULL = "full"               # Sauvegarde complète
    INCREMENTAL = "incremental" # Incrémentale
    DIFFERENTIAL = "differential" # Différentielle


class BackupFrequency(str, Enum):
    """Fréquence de sauvegarde."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


class BackupConfig(Base):
    """Configuration de sauvegarde par tenant."""
    __tablename__ = "backup_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, unique=True, index=True)

    # Clé de chiffrement (chiffrée avec la clé maître)
    encryption_key_encrypted = Column(Text, nullable=False)
    encryption_algorithm = Column(String(50), default="AES-256-GCM")

    # Planification
    frequency = Column(SQLEnum(BackupFrequency), default=BackupFrequency.WEEKLY)
    backup_hour = Column(Integer, default=2)  # Heure de backup (0-23)
    backup_day = Column(Integer, default=0)   # Jour de la semaine (0=lundi) pour weekly
    backup_day_of_month = Column(Integer, default=1)  # Jour du mois pour monthly

    # Rétention
    retention_days = Column(Integer, default=90)
    max_backups = Column(Integer, default=12)

    # Stockage
    storage_path = Column(String(500), nullable=True)
    storage_type = Column(String(50), default="local")  # local, s3, gcs, azure

    # Options
    include_attachments = Column(Boolean, default=True)
    compress = Column(Boolean, default=True)
    verify_after_backup = Column(Boolean, default=True)

    # État
    is_active = Column(Boolean, default=True)
    last_backup_at = Column(DateTime, nullable=True)
    next_backup_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        {'extend_existing': True}
    )


class Backup(Base):
    """Sauvegarde effectuée."""
    __tablename__ = "backups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    config_id = Column(UUID(as_uuid=True), nullable=True)

    # Identification
    reference = Column(String(100), nullable=False, index=True)
    backup_type = Column(SQLEnum(BackupType), default=BackupType.FULL)
    status = Column(SQLEnum(BackupStatus), default=BackupStatus.PENDING, index=True)

    # Fichier
    file_path = Column(String(1000), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)  # Taille en octets
    file_checksum = Column(String(128), nullable=True)  # SHA-256

    # Chiffrement
    is_encrypted = Column(Boolean, default=True)
    encryption_algorithm = Column(String(50), default="AES-256-GCM")
    encryption_iv = Column(String(100), nullable=True)  # IV/Nonce

    # Contenu
    tables_included = Column(JSON, default=list)
    records_count = Column(Integer, default=0)
    include_attachments = Column(Boolean, default=True)
    is_compressed = Column(Boolean, default=True)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Restauration
    last_restored_at = Column(DateTime, nullable=True)
    restore_count = Column(Integer, default=0)

    # Métadonnées
    notes = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    triggered_by = Column(String(100), nullable=True)  # scheduler, manual, api

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        {'extend_existing': True}
    )


class RestoreLog(Base):
    """Log de restauration."""
    __tablename__ = "restore_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    backup_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    status = Column(SQLEnum(BackupStatus), default=BackupStatus.PENDING)
    target_type = Column(String(50), default="same_tenant")  # same_tenant, new_tenant, test
    target_tenant_id = Column(String(50), nullable=True)

    tables_restored = Column(JSON, default=list)
    records_restored = Column(Integer, default=0)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    error_message = Column(Text, nullable=True)
    restored_by = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        {'extend_existing': True}
    )
