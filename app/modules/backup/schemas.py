"""
AZALS - Module Backup - Schémas
===============================
Schémas Pydantic pour les sauvegardes.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .models import BackupStatus, BackupType, BackupFrequency


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
    storage_path: Optional[str] = None
    storage_type: str = "local"
    include_attachments: bool = True
    compress: bool = True
    verify_after_backup: bool = True


class BackupConfigUpdate(BaseModel):
    """Mise à jour configuration backup."""
    frequency: Optional[BackupFrequency] = None
    backup_hour: Optional[int] = Field(default=None, ge=0, le=23)
    backup_day: Optional[int] = Field(default=None, ge=0, le=6)
    backup_day_of_month: Optional[int] = Field(default=None, ge=1, le=28)
    retention_days: Optional[int] = Field(default=None, ge=7, le=365)
    max_backups: Optional[int] = Field(default=None, ge=1, le=100)
    storage_path: Optional[str] = None
    storage_type: Optional[str] = None
    include_attachments: Optional[bool] = None
    compress: Optional[bool] = None
    verify_after_backup: Optional[bool] = None
    is_active: Optional[bool] = None


class BackupConfigResponse(BaseModel):
    """Réponse configuration backup."""
    id: str
    tenant_id: str
    encryption_algorithm: str
    frequency: BackupFrequency
    backup_hour: int
    backup_day: int
    backup_day_of_month: int
    retention_days: int
    max_backups: int
    storage_path: Optional[str]
    storage_type: str
    include_attachments: bool
    compress: bool
    verify_after_backup: bool
    is_active: bool
    last_backup_at: Optional[datetime]
    next_backup_at: Optional[datetime]
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
    notes: Optional[str] = None


class BackupResponse(BaseModel):
    """Réponse backup."""
    id: str
    tenant_id: str
    reference: str
    backup_type: BackupType
    status: BackupStatus
    file_name: Optional[str]
    file_size: Optional[int]
    file_checksum: Optional[str]
    is_encrypted: bool
    encryption_algorithm: str
    records_count: int
    include_attachments: bool
    is_compressed: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    last_restored_at: Optional[datetime]
    restore_count: int
    notes: Optional[str]
    error_message: Optional[str]
    triggered_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BackupDetail(BackupResponse):
    """Détail complet d'une sauvegarde."""
    file_path: Optional[str]
    encryption_iv: Optional[str]
    tables_included: List[str]


# ============================================================================
# RESTAURATION
# ============================================================================

class RestoreRequest(BaseModel):
    """Requête de restauration."""
    backup_id: str
    target_type: str = "same_tenant"  # same_tenant, new_tenant, test
    target_tenant_id: Optional[str] = None
    tables_to_restore: Optional[List[str]] = None  # None = toutes


class RestoreResponse(BaseModel):
    """Réponse restauration."""
    id: str
    backup_id: str
    tenant_id: str
    status: BackupStatus
    target_type: str
    target_tenant_id: Optional[str]
    tables_restored: List[str]
    records_restored: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    error_message: Optional[str]
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
    last_backup_at: Optional[datetime]
    last_backup_status: Optional[BackupStatus]
    next_backup_at: Optional[datetime]
    success_rate: float
    average_duration_seconds: float


class BackupDashboard(BaseModel):
    """Dashboard backup."""
    config: Optional[BackupConfigResponse]
    stats: BackupStats
    recent_backups: List[BackupResponse]
    recent_restores: List[RestoreResponse]
