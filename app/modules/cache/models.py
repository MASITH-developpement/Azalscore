"""
AZALS MODULE - Cache - Modeles
==============================

Modeles SQLAlchemy pour la gestion du cache applicatif.
Inclut audit complet et tenant_id obligatoire.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class CacheLevel(str, enum.Enum):
    """Niveaux de cache."""
    L1_MEMORY = "L1_MEMORY"
    L2_REDIS = "L2_REDIS"
    L3_PERSISTENT = "L3_PERSISTENT"


class EvictionPolicy(str, enum.Enum):
    """Politiques d'eviction."""
    LRU = "LRU"    # Least Recently Used
    LFU = "LFU"    # Least Frequently Used
    FIFO = "FIFO"  # First In First Out
    TTL = "TTL"    # Time To Live only
    RANDOM = "RANDOM"


class CacheStatus(str, enum.Enum):
    """Statut d'une entree cache."""
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class InvalidationType(str, enum.Enum):
    """Types d'invalidation."""
    KEY = "KEY"
    PATTERN = "PATTERN"
    TAG = "TAG"
    ENTITY = "ENTITY"
    TENANT = "TENANT"
    ALL = "ALL"


class AlertSeverity(str, enum.Enum):
    """Severite des alertes."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    """Statut des alertes."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


# ============================================================================
# MODELES PRINCIPAUX
# ============================================================================

class CacheConfig(Base):
    """
    Configuration du cache par tenant.
    Definit les parametres globaux du cache.
    """
    __tablename__ = "cache_configs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, unique=True, index=True)

    # Niveaux actifs
    l1_enabled = Column(Boolean, default=True, nullable=False)
    l2_enabled = Column(Boolean, default=True, nullable=False)
    l3_enabled = Column(Boolean, default=False, nullable=False)

    # TTL par defaut (secondes)
    default_ttl_seconds = Column(Integer, default=300, nullable=False)
    stale_ttl_seconds = Column(Integer, default=60, nullable=False)

    # Capacite L1 (memoire)
    l1_max_items = Column(Integer, default=10000, nullable=False)
    l1_max_size_mb = Column(Integer, default=100, nullable=False)

    # Capacite L2 (Redis)
    l2_max_size_mb = Column(Integer, default=500, nullable=False)

    # Politique d'eviction
    eviction_policy = Column(Enum(EvictionPolicy), default=EvictionPolicy.LRU, nullable=False)

    # Compression
    compression_enabled = Column(Boolean, default=True, nullable=False)
    compression_threshold_bytes = Column(Integer, default=1024, nullable=False)

    # Prechargement
    preload_enabled = Column(Boolean, default=False, nullable=False)

    # Alertes
    alert_hit_rate_threshold = Column(Float, default=0.7, nullable=False)
    alert_memory_threshold_percent = Column(Float, default=90.0, nullable=False)
    alert_eviction_rate_threshold = Column(Integer, default=100, nullable=False)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    regions = relationship("CacheRegion", back_populates="config", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_cache_config_tenant', 'tenant_id'),
    )


class CacheRegion(Base):
    """
    Region de cache avec configuration specifique.
    Permet de definir des comportements differents par type de donnees.
    """
    __tablename__ = "cache_regions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    config_id = Column(UniversalUUID(), ForeignKey('cache_configs.id', ondelete='CASCADE'), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    ttl_seconds = Column(Integer, default=300, nullable=False)
    stale_ttl_seconds = Column(Integer, default=60, nullable=False)
    max_items = Column(Integer, default=1000, nullable=False)

    # Tags par defaut
    default_tags = Column(JSON, default=list, nullable=False)

    # Entites associees
    entity_types = Column(JSON, default=list, nullable=False)

    # Prechargement
    preload_enabled = Column(Boolean, default=False, nullable=False)
    preload_keys = Column(JSON, default=list, nullable=False)
    preload_cron = Column(String(100), nullable=True)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    config = relationship("CacheConfig", back_populates="regions")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_cache_region_code'),
        Index('idx_cache_region_tenant', 'tenant_id'),
        Index('idx_cache_region_code', 'code'),
    )


class CacheEntry(Base):
    """
    Entree de cache persistante (L3).
    Stocke les metadonnees des entrees cache.
    """
    __tablename__ = "cache_entries"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Cle
    cache_key = Column(String(500), nullable=False, index=True)
    key_hash = Column(String(64), nullable=False, index=True)

    # Region
    region_id = Column(UniversalUUID(), ForeignKey('cache_regions.id', ondelete='SET NULL'), nullable=True)
    region_code = Column(String(50), nullable=True)

    # Valeur (pour L3)
    value_json = Column(Text, nullable=True)
    value_hash = Column(String(64), nullable=True)

    # Taille
    original_size_bytes = Column(Integer, default=0, nullable=False)
    compressed_size_bytes = Column(Integer, default=0, nullable=False)
    is_compressed = Column(Boolean, default=False, nullable=False)

    # TTL
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    stale_at = Column(DateTime, nullable=True)

    # Tags
    tags = Column(JSON, default=list, nullable=False)

    # Entite associee
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(String(255), nullable=True, index=True)

    # Statistiques
    hit_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)

    # Niveau actuel
    cache_level = Column(Enum(CacheLevel), default=CacheLevel.L1_MEMORY, nullable=False)
    status = Column(Enum(CacheStatus), default=CacheStatus.ACTIVE, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'key_hash', name='uq_cache_entry_key'),
        Index('idx_cache_entry_tenant', 'tenant_id'),
        Index('idx_cache_entry_key', 'cache_key'),
        Index('idx_cache_entry_expires', 'expires_at'),
        Index('idx_cache_entry_entity', 'entity_type', 'entity_id'),
        Index('idx_cache_entry_region', 'region_code'),
        Index('idx_cache_entry_status', 'status'),
    )


class CacheStatistics(Base):
    """
    Statistiques du cache agregees par periode.
    """
    __tablename__ = "cache_statistics"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Periode
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), default='HOUR', nullable=False)  # MINUTE, HOUR, DAY

    # Niveau
    cache_level = Column(Enum(CacheLevel), nullable=False)

    # Compteurs
    hits = Column(BigInteger, default=0, nullable=False)
    misses = Column(BigInteger, default=0, nullable=False)
    stale_hits = Column(BigInteger, default=0, nullable=False)

    # Operations
    sets = Column(BigInteger, default=0, nullable=False)
    deletes = Column(BigInteger, default=0, nullable=False)

    # Evictions
    evictions_ttl = Column(BigInteger, default=0, nullable=False)
    evictions_capacity = Column(BigInteger, default=0, nullable=False)

    # Invalidations
    invalidations_key = Column(BigInteger, default=0, nullable=False)
    invalidations_tag = Column(BigInteger, default=0, nullable=False)
    invalidations_pattern = Column(BigInteger, default=0, nullable=False)
    invalidations_entity = Column(BigInteger, default=0, nullable=False)
    invalidations_tenant = Column(BigInteger, default=0, nullable=False)

    # Taille
    current_items = Column(BigInteger, default=0, nullable=False)
    current_size_bytes = Column(BigInteger, default=0, nullable=False)
    max_items = Column(BigInteger, default=0, nullable=False)
    max_size_bytes = Column(BigInteger, default=0, nullable=False)

    # Performance
    avg_get_time_ms = Column(Float, default=0.0, nullable=False)
    avg_set_time_ms = Column(Float, default=0.0, nullable=False)
    p95_get_time_ms = Column(Float, default=0.0, nullable=False)
    p99_get_time_ms = Column(Float, default=0.0, nullable=False)

    # Calcules
    hit_rate = Column(Float, default=0.0, nullable=False)
    fill_rate = Column(Float, default=0.0, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'period_start', 'cache_level', 'period_type', name='uq_cache_stats_period'),
        Index('idx_cache_stats_tenant', 'tenant_id'),
        Index('idx_cache_stats_period', 'period_start', 'period_end'),
        Index('idx_cache_stats_level', 'cache_level'),
    )


class InvalidationEvent(Base):
    """
    Historique des evenements d'invalidation.
    """
    __tablename__ = "cache_invalidation_events"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Type d'invalidation
    invalidation_type = Column(Enum(InvalidationType), nullable=False)

    # Cible
    target_key = Column(String(500), nullable=True)
    target_pattern = Column(String(500), nullable=True)
    target_tag = Column(String(100), nullable=True)
    target_entity_type = Column(String(100), nullable=True)
    target_entity_id = Column(String(255), nullable=True)

    # Resultat
    keys_invalidated = Column(Integer, default=0, nullable=False)
    levels_affected = Column(JSON, default=list, nullable=False)

    # Performance
    duration_ms = Column(Integer, default=0, nullable=False)

    # Source
    source_module = Column(String(50), nullable=True)
    source_action = Column(String(100), nullable=True)
    triggered_by = Column(UniversalUUID(), nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_invalidation_tenant', 'tenant_id'),
        Index('idx_invalidation_type', 'invalidation_type'),
        Index('idx_invalidation_created', 'created_at'),
    )


class PreloadTask(Base):
    """
    Tache de prechargement du cache.
    """
    __tablename__ = "cache_preload_tasks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Region
    region_id = Column(UniversalUUID(), ForeignKey('cache_regions.id', ondelete='CASCADE'), nullable=True)
    region_code = Column(String(50), nullable=True)

    # Configuration
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Cles a precharger
    keys_pattern = Column(String(500), nullable=True)
    keys_list = Column(JSON, default=list, nullable=False)

    # Loader
    loader_type = Column(String(50), nullable=False)  # QUERY, API, FUNCTION
    loader_config = Column(JSON, default=dict, nullable=False)

    # Planification
    schedule_cron = Column(String(100), nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)

    # Resultat derniere execution
    last_run_status = Column(String(20), nullable=True)  # SUCCESS, FAILED, PARTIAL
    last_run_keys_loaded = Column(Integer, default=0, nullable=False)
    last_run_duration_ms = Column(Integer, default=0, nullable=False)
    last_run_error = Column(Text, nullable=True)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_preload_tenant', 'tenant_id'),
        Index('idx_preload_region', 'region_code'),
        Index('idx_preload_next_run', 'next_run_at'),
    )


class CacheAlert(Base):
    """
    Alertes liees au cache (seuils, performance).
    """
    __tablename__ = "cache_alerts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Type d'alerte
    alert_type = Column(String(50), nullable=False)  # HIT_RATE, MEMORY, EVICTION, LATENCY
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False)

    # Contenu
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Valeurs
    threshold_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)

    # Niveau de cache
    cache_level = Column(Enum(CacheLevel), nullable=True)
    region_code = Column(String(50), nullable=True)

    # Resolution
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(UniversalUUID(), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UniversalUUID(), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_alert_tenant', 'tenant_id'),
        Index('idx_alert_status', 'status'),
        Index('idx_alert_severity', 'severity'),
        Index('idx_alert_triggered', 'triggered_at'),
    )


class CacheAuditLog(Base):
    """
    Journal d'audit pour les operations de cache.
    """
    __tablename__ = "cache_audit_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Action
    action = Column(String(50), nullable=False)  # CONFIG_UPDATE, PURGE, INVALIDATE, PRELOAD, etc.
    entity_type = Column(String(50), nullable=False)  # CONFIG, REGION, ENTRY, TASK
    entity_id = Column(String(255), nullable=True)

    # Details
    description = Column(String(500), nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)

    # Resultat
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Utilisateur
    user_id = Column(UniversalUUID(), nullable=True)
    user_email = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_audit_log_tenant', 'tenant_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_created', 'created_at'),
    )
