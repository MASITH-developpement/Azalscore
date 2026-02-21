"""
AZALS MODULE - Cache Applicatif
===============================

Module complet de gestion du cache pour AZALSCORE ERP.

Fonctionnalites:
- Cache multi-niveau (L1 memoire, L2 Redis, L3 persistent)
- TTL configurable par type/region
- Invalidation intelligente (cle/pattern/tag/entite/tenant)
- Statistiques hit/miss
- Monitoring taille cache
- Prechargement cache
- Cache par entite
- Admin: visualisation et purge
- Alertes seuils
- Dashboard performance
- Audit complet

Usage:
    from app.modules.cache import CacheService, get_cache_service

    # Dans un endpoint FastAPI
    service = get_cache_service(db, tenant_id)

    # Stocker une valeur
    service.set("user:123", user_data, ttl_seconds=300, tags=["user"])

    # Recuperer une valeur
    result = service.get("user:123")
    if result.found:
        user = result.value

    # Invalider par tag
    service.invalidate_by_tag("user")

    # Invalider par entite
    service.invalidate_by_entity("User", "123")
"""

from .models import (
    # Enums
    CacheLevel,
    EvictionPolicy,
    CacheStatus,
    InvalidationType,
    AlertSeverity,
    AlertStatus,
    # Models
    CacheConfig,
    CacheRegion,
    CacheEntry,
    CacheStatistics,
    InvalidationEvent,
    PreloadTask,
    CacheAlert,
    CacheAuditLog,
)

from .schemas import (
    # Config
    CacheConfigCreate,
    CacheConfigUpdate,
    CacheConfigResponse,
    # Regions
    CacheRegionCreate,
    CacheRegionUpdate,
    CacheRegionResponse,
    # Operations
    CacheSetRequest,
    CacheGetResponse,
    CacheMSetRequest,
    CacheMGetResponse,
    # Invalidation
    InvalidateByKeyRequest,
    InvalidateByPatternRequest,
    InvalidateByTagRequest,
    InvalidateByEntityRequest,
    InvalidationResponse,
    # Stats
    CacheStatsResponse,
    CacheStatsAggregated,
    # Entries
    CacheEntryResponse,
    CacheEntryList,
    # Preload
    PreloadTaskCreate,
    PreloadTaskUpdate,
    PreloadTaskResponse,
    PreloadRunResponse,
    # Alerts
    CacheAlertResponse,
    AlertAcknowledgeRequest,
    AlertResolveRequest,
    # Dashboard
    CacheDashboard,
    TopKey,
    RecentInvalidation,
    # Purge
    PurgeRequest,
    PurgeResponse,
    # Audit
    CacheAuditLogResponse,
)

from .service import (
    CacheService,
    get_cache_service,
    L1MemoryCache,
)

from .router import router

from .exceptions import (
    CacheError,
    CacheConfigNotFoundError,
    CacheConfigAlreadyExistsError,
    CacheRegionNotFoundError,
    CacheRegionDuplicateError,
    CacheEntryNotFoundError,
    CacheKeyInvalidError,
    CacheKeyTooLongError,
    CacheValueTooLargeError,
    CacheSerializationError,
    CacheDeserializationError,
    CacheConnectionError,
    CacheTimeoutError,
    InvalidationError,
    InvalidPatternError,
    PreloadTaskNotFoundError,
    PreloadExecutionError,
    CacheAlertNotFoundError,
    PurgeConfirmationRequiredError,
)

__all__ = [
    # Enums
    "CacheLevel",
    "EvictionPolicy",
    "CacheStatus",
    "InvalidationType",
    "AlertSeverity",
    "AlertStatus",
    # Models
    "CacheConfig",
    "CacheRegion",
    "CacheEntry",
    "CacheStatistics",
    "InvalidationEvent",
    "PreloadTask",
    "CacheAlert",
    "CacheAuditLog",
    # Schemas
    "CacheConfigCreate",
    "CacheConfigUpdate",
    "CacheConfigResponse",
    "CacheRegionCreate",
    "CacheRegionUpdate",
    "CacheRegionResponse",
    "CacheSetRequest",
    "CacheGetResponse",
    "CacheMSetRequest",
    "CacheMGetResponse",
    "InvalidateByKeyRequest",
    "InvalidateByPatternRequest",
    "InvalidateByTagRequest",
    "InvalidateByEntityRequest",
    "InvalidationResponse",
    "CacheStatsResponse",
    "CacheStatsAggregated",
    "CacheEntryResponse",
    "CacheEntryList",
    "PreloadTaskCreate",
    "PreloadTaskUpdate",
    "PreloadTaskResponse",
    "PreloadRunResponse",
    "CacheAlertResponse",
    "AlertAcknowledgeRequest",
    "AlertResolveRequest",
    "CacheDashboard",
    "TopKey",
    "RecentInvalidation",
    "PurgeRequest",
    "PurgeResponse",
    "CacheAuditLogResponse",
    # Service
    "CacheService",
    "get_cache_service",
    "L1MemoryCache",
    # Router
    "router",
    # Exceptions
    "CacheError",
    "CacheConfigNotFoundError",
    "CacheConfigAlreadyExistsError",
    "CacheRegionNotFoundError",
    "CacheRegionDuplicateError",
    "CacheEntryNotFoundError",
    "CacheKeyInvalidError",
    "CacheKeyTooLongError",
    "CacheValueTooLargeError",
    "CacheSerializationError",
    "CacheDeserializationError",
    "CacheConnectionError",
    "CacheTimeoutError",
    "InvalidationError",
    "InvalidPatternError",
    "PreloadTaskNotFoundError",
    "PreloadExecutionError",
    "CacheAlertNotFoundError",
    "PurgeConfirmationRequiredError",
]
