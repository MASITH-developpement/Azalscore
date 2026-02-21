"""
AZALS MODULE - Cache - Schemas
==============================

Schemas Pydantic pour la gestion du cache applicatif.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .models import (
    AlertSeverity,
    AlertStatus,
    CacheLevel,
    CacheStatus,
    EvictionPolicy,
    InvalidationType,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

class CacheConfigCreate(BaseModel):
    """Creation configuration cache."""
    l1_enabled: bool = True
    l2_enabled: bool = True
    l3_enabled: bool = False
    default_ttl_seconds: int = Field(default=300, ge=1, le=86400)
    stale_ttl_seconds: int = Field(default=60, ge=0, le=3600)
    l1_max_items: int = Field(default=10000, ge=100, le=1000000)
    l1_max_size_mb: int = Field(default=100, ge=1, le=10000)
    l2_max_size_mb: int = Field(default=500, ge=1, le=100000)
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    compression_enabled: bool = True
    compression_threshold_bytes: int = Field(default=1024, ge=0)
    preload_enabled: bool = False
    alert_hit_rate_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    alert_memory_threshold_percent: float = Field(default=90.0, ge=0.0, le=100.0)
    alert_eviction_rate_threshold: int = Field(default=100, ge=0)


class CacheConfigUpdate(BaseModel):
    """Mise a jour configuration cache."""
    l1_enabled: Optional[bool] = None
    l2_enabled: Optional[bool] = None
    l3_enabled: Optional[bool] = None
    default_ttl_seconds: Optional[int] = Field(default=None, ge=1, le=86400)
    stale_ttl_seconds: Optional[int] = Field(default=None, ge=0, le=3600)
    l1_max_items: Optional[int] = Field(default=None, ge=100, le=1000000)
    l1_max_size_mb: Optional[int] = Field(default=None, ge=1, le=10000)
    l2_max_size_mb: Optional[int] = Field(default=None, ge=1, le=100000)
    eviction_policy: Optional[EvictionPolicy] = None
    compression_enabled: Optional[bool] = None
    compression_threshold_bytes: Optional[int] = Field(default=None, ge=0)
    preload_enabled: Optional[bool] = None
    alert_hit_rate_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    alert_memory_threshold_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    alert_eviction_rate_threshold: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class CacheConfigResponse(BaseModel):
    """Reponse configuration cache."""
    id: UUID
    tenant_id: str
    l1_enabled: bool
    l2_enabled: bool
    l3_enabled: bool
    default_ttl_seconds: int
    stale_ttl_seconds: int
    l1_max_items: int
    l1_max_size_mb: int
    l2_max_size_mb: int
    eviction_policy: EvictionPolicy
    compression_enabled: bool
    compression_threshold_bytes: int
    preload_enabled: bool
    alert_hit_rate_threshold: float
    alert_memory_threshold_percent: float
    alert_eviction_rate_threshold: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# REGIONS
# ============================================================================

class CacheRegionCreate(BaseModel):
    """Creation d'une region cache."""
    code: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z][a-z0-9_]*$')
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    ttl_seconds: int = Field(default=300, ge=1, le=86400)
    stale_ttl_seconds: int = Field(default=60, ge=0, le=3600)
    max_items: int = Field(default=1000, ge=1, le=100000)
    default_tags: List[str] = Field(default_factory=list)
    entity_types: List[str] = Field(default_factory=list)
    preload_enabled: bool = False
    preload_keys: List[str] = Field(default_factory=list)
    preload_cron: Optional[str] = None


class CacheRegionUpdate(BaseModel):
    """Mise a jour d'une region cache."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    ttl_seconds: Optional[int] = Field(default=None, ge=1, le=86400)
    stale_ttl_seconds: Optional[int] = Field(default=None, ge=0, le=3600)
    max_items: Optional[int] = Field(default=None, ge=1, le=100000)
    default_tags: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    preload_enabled: Optional[bool] = None
    preload_keys: Optional[List[str]] = None
    preload_cron: Optional[str] = None
    is_active: Optional[bool] = None


class CacheRegionResponse(BaseModel):
    """Reponse region cache."""
    id: UUID
    tenant_id: str
    config_id: UUID
    code: str
    name: str
    description: Optional[str]
    ttl_seconds: int
    stale_ttl_seconds: int
    max_items: int
    default_tags: List[str]
    entity_types: List[str]
    preload_enabled: bool
    preload_keys: List[str]
    preload_cron: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# OPERATIONS CACHE
# ============================================================================

class CacheSetRequest(BaseModel):
    """Requete pour stocker une valeur en cache."""
    key: str = Field(..., min_length=1, max_length=500)
    value: Any
    ttl_seconds: Optional[int] = Field(default=None, ge=1, le=86400)
    tags: List[str] = Field(default_factory=list)
    region: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


class CacheGetResponse(BaseModel):
    """Reponse pour une valeur en cache."""
    key: str
    value: Any
    found: bool
    is_stale: bool = False
    cache_level: Optional[CacheLevel] = None
    expires_at: Optional[datetime] = None
    hit_count: int = 0


class CacheMSetRequest(BaseModel):
    """Requete pour stocker plusieurs valeurs."""
    items: Dict[str, Any]
    ttl_seconds: Optional[int] = Field(default=None, ge=1, le=86400)
    tags: List[str] = Field(default_factory=list)
    region: Optional[str] = None


class CacheMGetResponse(BaseModel):
    """Reponse pour plusieurs valeurs."""
    items: Dict[str, Any]
    found_keys: List[str]
    missing_keys: List[str]


# ============================================================================
# INVALIDATION
# ============================================================================

class InvalidateByKeyRequest(BaseModel):
    """Invalidation par cle."""
    key: str = Field(..., min_length=1, max_length=500)


class InvalidateByPatternRequest(BaseModel):
    """Invalidation par pattern."""
    pattern: str = Field(..., min_length=1, max_length=500)


class InvalidateByTagRequest(BaseModel):
    """Invalidation par tag."""
    tag: str = Field(..., min_length=1, max_length=100)


class InvalidateByEntityRequest(BaseModel):
    """Invalidation par entite."""
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: Optional[str] = None


class InvalidationResponse(BaseModel):
    """Reponse d'invalidation."""
    id: UUID
    invalidation_type: InvalidationType
    keys_invalidated: int
    levels_affected: List[CacheLevel]
    duration_ms: int
    timestamp: datetime


# ============================================================================
# STATISTIQUES
# ============================================================================

class CacheStatsResponse(BaseModel):
    """Statistiques du cache."""
    tenant_id: str
    cache_level: CacheLevel
    period_start: datetime
    period_end: datetime

    # Compteurs
    hits: int
    misses: int
    stale_hits: int
    hit_rate: float

    # Operations
    sets: int
    deletes: int

    # Evictions
    evictions_ttl: int
    evictions_capacity: int
    total_evictions: int

    # Invalidations
    invalidations_total: int

    # Taille
    current_items: int
    current_size_bytes: int
    max_items: int
    max_size_bytes: int
    fill_rate: float

    # Performance
    avg_get_time_ms: float
    avg_set_time_ms: float
    p95_get_time_ms: float
    p99_get_time_ms: float


class CacheStatsAggregated(BaseModel):
    """Statistiques agregees par niveau."""
    l1_stats: Optional[CacheStatsResponse] = None
    l2_stats: Optional[CacheStatsResponse] = None
    l3_stats: Optional[CacheStatsResponse] = None
    total_hits: int = 0
    total_misses: int = 0
    overall_hit_rate: float = 0.0
    total_size_bytes: int = 0
    total_items: int = 0


# ============================================================================
# ENTREES CACHE
# ============================================================================

class CacheEntryResponse(BaseModel):
    """Reponse entree cache."""
    id: UUID
    tenant_id: str
    cache_key: str
    region_code: Optional[str]
    original_size_bytes: int
    compressed_size_bytes: int
    is_compressed: bool
    created_at: datetime
    expires_at: Optional[datetime]
    tags: List[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    hit_count: int
    last_accessed_at: Optional[datetime]
    cache_level: CacheLevel
    status: CacheStatus

    class Config:
        from_attributes = True


class CacheEntryList(BaseModel):
    """Liste d'entrees cache."""
    items: List[CacheEntryResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# PRECHARGEMENT
# ============================================================================

class PreloadTaskCreate(BaseModel):
    """Creation tache de prechargement."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    region_code: Optional[str] = None
    keys_pattern: Optional[str] = None
    keys_list: List[str] = Field(default_factory=list)
    loader_type: str = Field(..., pattern=r'^(QUERY|API|FUNCTION)$')
    loader_config: Dict[str, Any] = Field(default_factory=dict)
    schedule_cron: Optional[str] = None
    is_active: bool = True


class PreloadTaskUpdate(BaseModel):
    """Mise a jour tache de prechargement."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    keys_pattern: Optional[str] = None
    keys_list: Optional[List[str]] = None
    loader_config: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    is_active: Optional[bool] = None


class PreloadTaskResponse(BaseModel):
    """Reponse tache de prechargement."""
    id: UUID
    tenant_id: str
    region_id: Optional[UUID]
    region_code: Optional[str]
    name: str
    description: Optional[str]
    keys_pattern: Optional[str]
    keys_list: List[str]
    loader_type: str
    loader_config: Dict[str, Any]
    schedule_cron: Optional[str]
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    last_run_status: Optional[str]
    last_run_keys_loaded: int
    last_run_duration_ms: int
    last_run_error: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PreloadRunResponse(BaseModel):
    """Reponse execution prechargement."""
    task_id: UUID
    status: str
    keys_loaded: int
    duration_ms: int
    error: Optional[str] = None


# ============================================================================
# ALERTES
# ============================================================================

class CacheAlertResponse(BaseModel):
    """Reponse alerte cache."""
    id: UUID
    tenant_id: str
    alert_type: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    threshold_value: Optional[float]
    actual_value: Optional[float]
    cache_level: Optional[CacheLevel]
    region_code: Optional[str]
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    """Requete d'acquittement d'alerte."""
    notes: Optional[str] = None


class AlertResolveRequest(BaseModel):
    """Requete de resolution d'alerte."""
    resolution_notes: str = Field(..., min_length=1, max_length=1000)


# ============================================================================
# DASHBOARD
# ============================================================================

class TopKey(BaseModel):
    """Cle la plus utilisee."""
    key: str
    hit_count: int
    region_code: Optional[str]
    entity_type: Optional[str]


class RecentInvalidation(BaseModel):
    """Invalidation recente."""
    id: UUID
    invalidation_type: InvalidationType
    keys_invalidated: int
    created_at: datetime


class CacheDashboard(BaseModel):
    """Dashboard cache."""
    config: Optional[CacheConfigResponse]
    stats: CacheStatsAggregated
    top_keys: List[TopKey]
    recent_invalidations: List[RecentInvalidation]
    active_alerts: List[CacheAlertResponse]
    regions_count: int
    preload_tasks_count: int
    entries_count: int


# ============================================================================
# PURGE
# ============================================================================

class PurgeRequest(BaseModel):
    """Requete de purge cache."""
    level: Optional[CacheLevel] = None
    region_code: Optional[str] = None
    expired_only: bool = False
    confirm: bool = False

    @field_validator('confirm')
    @classmethod
    def must_confirm(cls, v: bool) -> bool:
        if not v:
            raise ValueError('confirm must be True to proceed with purge')
        return v


class PurgeResponse(BaseModel):
    """Reponse de purge cache."""
    keys_purged: int
    size_freed_bytes: int
    levels_affected: List[CacheLevel]
    duration_ms: int


# ============================================================================
# AUDIT
# ============================================================================

class CacheAuditLogResponse(BaseModel):
    """Reponse audit log cache."""
    id: UUID
    tenant_id: str
    action: str
    entity_type: str
    entity_id: Optional[str]
    description: Optional[str]
    success: bool
    error_message: Optional[str]
    user_id: Optional[UUID]
    user_email: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
