"""
AZALS - Module Backup - Schémas
===============================
Schémas Pydantic pour les sauvegardes.
"""
from __future__ import annotations


from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, Field

from .models import BackupFrequency, BackupStatus, BackupType

# ============================================================================
# CONFIGURATION
# ============================================================================

class BackupConfigCreate(BaseModel):
    """Création configuration backup."""
    frequency: BackupFrequency = BackupFrequency.WEEKLY
    backup_hour: int = Field(default=2, ge=0, le=23)
    backup_day: int = Field(default=0, ge=0, le=6)
    backup_day_of_month: int = Field(default=1, ge=1, le=28)
    retention_days: int = Field(default=90, ge=7, le=365)
    max_backups: int = Field(default=12, ge=1, le=100)
    storage_path: str | None = None
    storage_type: str = "local"
    include_attachments: bool = True
    compress: bool = True
    verify_after_backup: bool = True


class BackupConfigUpdate(BaseModel):
    """Mise à jour configuration backup."""
    frequency: BackupFrequency | None = None
    backup_hour: int | None = Field(default=None, ge=0, le=23)
    backup_day: int | None = Field(default=None, ge=0, le=6)
    backup_day_of_month: int | None = Field(default=None, ge=1, le=28)
    retention_days: int | None = Field(default=None, ge=7, le=365)
    max_backups: int | None = Field(default=None, ge=1, le=100)
    storage_path: str | None = None
    storage_type: str | None = None
    include_attachments: bool | None = None
    compress: bool | None = None
    verify_after_backup: bool | None = None
    is_active: bool | None = None


class BackupConfigResponse(BaseModel):
    """Réponse configuration backup."""
    id: UUID
    tenant_id: str
    encryption_algorithm: str
    frequency: BackupFrequency
    backup_hour: int
    backup_day: int
    backup_day_of_month: int
    retention_days: int
    max_backups: int
    storage_path: str | None
    storage_type: str
    include_attachments: bool
    compress: bool
    verify_after_backup: bool
    is_active: bool
    last_backup_at: datetime | None
    next_backup_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BACKUP
# ============================================================================

class BackupCreate(BaseModel):
    """Création manuelle de backup."""
    backup_type: BackupType = BackupType.FULL
    include_attachments: bool = True
    notes: str | None = None


class BackupResponse(BaseModel):
    """Réponse backup."""
    id: UUID
    tenant_id: str
    reference: str
    backup_type: BackupType
    status: BackupStatus
    file_name: str | None
    file_size: int | None
    file_checksum: str | None
    is_encrypted: bool
    encryption_algorithm: str
    records_count: int
    include_attachments: bool
    is_compressed: bool
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    last_restored_at: datetime | None
    restore_count: int
    notes: str | None
    error_message: str | None
    triggered_by: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class BackupDetail(BackupResponse):
    """Détail complet d'une sauvegarde."""
    file_path: str | None
    encryption_iv: str | None
    tables_included: list[str]


# ============================================================================
# RESTAURATION
# ============================================================================

class RestoreRequest(BaseModel):
    """Requête de restauration."""
    backup_id: str
    target_type: str = "same_tenant"  # same_tenant, new_tenant, test
    target_tenant_id: str | None = None
    tables_to_restore: list[str] | None = None  # None = toutes


class RestoreResponse(BaseModel):
    """Réponse restauration."""
    id: UUID
    backup_id: str
    tenant_id: str
    status: BackupStatus
    target_type: str
    target_tenant_id: str | None
    tables_restored: list[str]
    records_restored: int
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD
# ============================================================================

class BackupStats(BaseModel):
    """Statistiques backup."""
    total_backups: int
    total_size_bytes: int
    last_backup_at: datetime | None
    last_backup_status: BackupStatus | None
    next_backup_at: datetime | None
    success_rate: float
    average_duration_seconds: float


class BackupDashboard(BaseModel):
    """Dashboard backup."""
    config: BackupConfigResponse | None
    stats: BackupStats
    recent_backups: list[BackupResponse]
    recent_restores: list[RestoreResponse]
