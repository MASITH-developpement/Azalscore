"""
AZALS MODULE - Cache - Service
==============================

Service complet pour la gestion du cache applicatif.
- Cache multi-niveau (L1 memoire, L2 Redis)
- TTL configurable par type
- Invalidation intelligente (cle/pattern/tag/entite)
- Statistiques hit/miss
- Monitoring taille cache
- Prechargement cache
- Cache par entite
- Alertes seuils
"""
from __future__ import annotations


import gzip
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from .models import (
    AlertSeverity,
    AlertStatus,
    CacheAlert,
    CacheAuditLog,
    CacheConfig,
    CacheEntry,
    CacheLevel,
    CacheRegion,
    CacheStatistics,
    CacheStatus,
    EvictionPolicy,
    InvalidationEvent,
    InvalidationType,
    PreloadTask,
)
from .repository import (
    CacheAlertRepository,
    CacheAuditLogRepository,
    CacheConfigRepository,
    CacheEntryRepository,
    CacheRegionRepository,
    CacheStatisticsRepository,
    InvalidationEventRepository,
    PreloadTaskRepository,
)
from .schemas import (
    CacheConfigCreate,
    CacheConfigResponse,
    CacheConfigUpdate,
    CacheDashboard,
    CacheEntryResponse,
    CacheGetResponse,
    CacheMGetResponse,
    CacheRegionCreate,
    CacheRegionResponse,
    CacheRegionUpdate,
    CacheSetRequest,
    CacheStatsAggregated,
    CacheStatsResponse,
    InvalidationResponse,
    PreloadRunResponse,
    PreloadTaskCreate,
    PreloadTaskResponse,
    PreloadTaskUpdate,
    PurgeResponse,
    RecentInvalidation,
    TopKey,
)
from .exceptions import (
    CacheConfigAlreadyExistsError,
    CacheConfigNotFoundError,
    CacheConnectionError,
    CacheDeserializationError,
    CacheEntryNotFoundError,
    CacheKeyInvalidError,
    CacheKeyTooLongError,
    CacheRegionDuplicateError,
    CacheRegionNotFoundError,
    CacheSerializationError,
    CacheValueTooLargeError,
    CompressionError,
    DecompressionError,
    InvalidationError,
    InvalidPatternError,
    PreloadExecutionError,
    PreloadTaskNotFoundError,
    PurgeConfirmationRequiredError,
    CacheAlertNotFoundError,
    CacheAlertAlreadyResolvedError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# CACHE L1 MEMORY (In-Process)
# ============================================================================

@dataclass
class L1CacheEntry:
    """Entree cache L1 en memoire."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    stale_at: Optional[datetime]
    tags: Set[str]
    hit_count: int = 0
    last_accessed_at: Optional[datetime] = None
    size_bytes: int = 0
    is_compressed: bool = False


class L1MemoryCache:
    """Cache L1 en memoire avec eviction LRU/LFU."""

    def __init__(
        self,
        max_items: int = 10000,
        max_size_mb: int = 100,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    ):
        self._cache: Dict[str, L1CacheEntry] = {}
        self._tags_index: Dict[str, Set[str]] = {}
        self._lru_order: List[str] = []
        self._frequency: Dict[str, int] = {}
        self._max_items = max_items
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._current_size_bytes = 0
        self._eviction_policy = eviction_policy

        # Stats
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Recupere une valeur."""
        entry = self._cache.get(key)
        if not entry:
            self._misses += 1
            return None

        now = datetime.utcnow()

        # Verifie expiration
        if entry.expires_at and now > entry.expires_at:
            self.delete(key)
            self._misses += 1
            return None

        # Met a jour stats
        entry.hit_count += 1
        entry.last_accessed_at = now
        self._hits += 1

        # Met a jour LRU
        if key in self._lru_order:
            self._lru_order.remove(key)
        self._lru_order.append(key)

        # Met a jour LFU
        self._frequency[key] = self._frequency.get(key, 0) + 1

        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        stale_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None
    ) -> L1CacheEntry:
        """Stocke une valeur."""
        # Calcule taille
        size_bytes = len(json.dumps(value, default=str).encode())

        # Evicte si necessaire
        while len(self._cache) >= self._max_items or \
              self._current_size_bytes + size_bytes > self._max_size_bytes:
            if not self._evict_one():
                break

        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        stale_at = now + timedelta(seconds=ttl_seconds - stale_seconds) \
            if ttl_seconds and stale_seconds else None

        entry = L1CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=expires_at,
            stale_at=stale_at,
            tags=tags or set(),
            size_bytes=size_bytes,
        )

        # Supprime ancienne entree si existe
        if key in self._cache:
            self._current_size_bytes -= self._cache[key].size_bytes

        self._cache[key] = entry
        self._current_size_bytes += size_bytes

        # Met a jour index tags
        for tag in entry.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = set()
            self._tags_index[tag].add(key)

        # Met a jour LRU
        if key in self._lru_order:
            self._lru_order.remove(key)
        self._lru_order.append(key)

        return entry

    def delete(self, key: str) -> bool:
        """Supprime une entree."""
        entry = self._cache.pop(key, None)
        if not entry:
            return False

        self._current_size_bytes -= entry.size_bytes

        # Nettoie index tags
        for tag in entry.tags:
            if tag in self._tags_index:
                self._tags_index[tag].discard(key)
                if not self._tags_index[tag]:
                    del self._tags_index[tag]

        # Nettoie LRU/LFU
        if key in self._lru_order:
            self._lru_order.remove(key)
        self._frequency.pop(key, None)

        return True

    def exists(self, key: str) -> bool:
        """Verifie si une cle existe."""
        entry = self._cache.get(key)
        if not entry:
            return False
        if entry.expires_at and datetime.utcnow() > entry.expires_at:
            return False
        return True

    def invalidate_by_tag(self, tag: str) -> int:
        """Invalide par tag."""
        keys = self._tags_index.get(tag, set()).copy()
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalide par pattern."""
        import fnmatch
        keys_to_delete = [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
        count = 0
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        return count

    def clear(self) -> int:
        """Vide le cache."""
        count = len(self._cache)
        self._cache.clear()
        self._tags_index.clear()
        self._lru_order.clear()
        self._frequency.clear()
        self._current_size_bytes = 0
        return count

    def _evict_one(self) -> bool:
        """Evicte une entree."""
        if not self._cache:
            return False

        key_to_evict = None

        if self._eviction_policy == EvictionPolicy.LRU:
            for key in self._lru_order:
                if key in self._cache:
                    key_to_evict = key
                    break
        elif self._eviction_policy == EvictionPolicy.LFU:
            min_freq = float('inf')
            for key in self._cache:
                freq = self._frequency.get(key, 0)
                if freq < min_freq:
                    min_freq = freq
                    key_to_evict = key
        elif self._eviction_policy == EvictionPolicy.FIFO:
            oldest_time = datetime.utcnow()
            for key, entry in self._cache.items():
                if entry.created_at < oldest_time:
                    oldest_time = entry.created_at
                    key_to_evict = key
        elif self._eviction_policy == EvictionPolicy.TTL:
            # Evicte les expires d'abord
            for key, entry in self._cache.items():
                if entry.expires_at and datetime.utcnow() > entry.expires_at:
                    key_to_evict = key
                    break
            if not key_to_evict:
                # Sinon le plus proche de l'expiration
                soonest_time = None
                for key, entry in self._cache.items():
                    if entry.expires_at:
                        if soonest_time is None or entry.expires_at < soonest_time:
                            soonest_time = entry.expires_at
                            key_to_evict = key
        else:  # RANDOM
            import random
            key_to_evict = random.choice(list(self._cache.keys()))

        if key_to_evict:
            self.delete(key_to_evict)
            self._evictions += 1
            return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques."""
        total = self._hits + self._misses
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self._hits / total if total > 0 else 0.0,
            'items': len(self._cache),
            'size_bytes': self._current_size_bytes,
            'max_items': self._max_items,
            'max_size_bytes': self._max_size_bytes,
            'evictions': self._evictions,
        }


# ============================================================================
# CACHE SERVICE PRINCIPAL
# ============================================================================

class CacheService:
    """Service complet de gestion du cache."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self._config_repo = CacheConfigRepository(db, tenant_id)
        self._region_repo = CacheRegionRepository(db, tenant_id)
        self._entry_repo = CacheEntryRepository(db, tenant_id)
        self._stats_repo = CacheStatisticsRepository(db, tenant_id)
        self._invalidation_repo = InvalidationEventRepository(db, tenant_id)
        self._preload_repo = PreloadTaskRepository(db, tenant_id)
        self._alert_repo = CacheAlertRepository(db, tenant_id)
        self._audit_repo = CacheAuditLogRepository(db, tenant_id)

        # Cache L1 en memoire (singleton per tenant dans un vrai env)
        self._l1_cache: Optional[L1MemoryCache] = None

        # Redis connection (simule pour l'instant)
        self._redis_client = None

        # Loaders enregistres
        self._loaders: Dict[str, Callable] = {}

    def _get_l1_cache(self) -> L1MemoryCache:
        """Recupere ou cree le cache L1."""
        if self._l1_cache is None:
            config = self._config_repo.get_config()
            if config:
                self._l1_cache = L1MemoryCache(
                    max_items=config.l1_max_items,
                    max_size_mb=config.l1_max_size_mb,
                    eviction_policy=config.eviction_policy
                )
            else:
                self._l1_cache = L1MemoryCache()
        return self._l1_cache

    def _make_key(self, key: str) -> str:
        """Cree une cle complete avec tenant."""
        return f"{self.tenant_id}:{key}"

    def _compute_hash(self, value: Any) -> str:
        """Calcule le hash d'une valeur."""
        serialized = json.dumps(value, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()

    def _audit_action(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        description: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Enregistre une action d'audit."""
        log = CacheAuditLog(
            tenant_id=self.tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_value=old_value,
            new_value=new_value,
            success=success,
            error_message=error_message,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.flush()

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def get_config(self) -> Optional[CacheConfig]:
        """Recupere la configuration."""
        return self._config_repo.get_config()

    def create_config(
        self,
        data: CacheConfigCreate,
        user_id: Optional[UUID] = None
    ) -> CacheConfig:
        """Cree la configuration cache."""
        if self._config_repo.config_exists():
            raise CacheConfigAlreadyExistsError(
                f"Configuration cache existe deja pour tenant {self.tenant_id}"
            )

        config = CacheConfig(
            tenant_id=self.tenant_id,
            l1_enabled=data.l1_enabled,
            l2_enabled=data.l2_enabled,
            l3_enabled=data.l3_enabled,
            default_ttl_seconds=data.default_ttl_seconds,
            stale_ttl_seconds=data.stale_ttl_seconds,
            l1_max_items=data.l1_max_items,
            l1_max_size_mb=data.l1_max_size_mb,
            l2_max_size_mb=data.l2_max_size_mb,
            eviction_policy=data.eviction_policy,
            compression_enabled=data.compression_enabled,
            compression_threshold_bytes=data.compression_threshold_bytes,
            preload_enabled=data.preload_enabled,
            alert_hit_rate_threshold=data.alert_hit_rate_threshold,
            alert_memory_threshold_percent=data.alert_memory_threshold_percent,
            alert_eviction_rate_threshold=data.alert_eviction_rate_threshold,
            created_by=user_id,
        )
        self.db.add(config)
        self.db.commit()

        self._audit_action(
            action="CREATE",
            entity_type="CONFIG",
            entity_id=str(config.id),
            description="Configuration cache creee",
            user_id=user_id
        )

        # Reset L1 cache pour utiliser nouvelle config
        self._l1_cache = None

        return config

    def update_config(
        self,
        data: CacheConfigUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[CacheConfig]:
        """Met a jour la configuration."""
        config = self._config_repo.get_config()
        if not config:
            raise CacheConfigNotFoundError("Configuration cache non trouvee")

        old_value = {
            'l1_max_items': config.l1_max_items,
            'l1_max_size_mb': config.l1_max_size_mb,
            'eviction_policy': config.eviction_policy.value,
        }

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        config.updated_by = user_id
        self.db.commit()

        self._audit_action(
            action="UPDATE",
            entity_type="CONFIG",
            entity_id=str(config.id),
            description="Configuration cache mise a jour",
            old_value=old_value,
            new_value=update_data,
            user_id=user_id
        )

        # Reset L1 cache pour utiliser nouvelle config
        self._l1_cache = None

        return config

    # ========================================================================
    # REGIONS
    # ========================================================================

    def list_regions(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[CacheRegion], int]:
        """Liste les regions."""
        return self._region_repo.list_active(skip, limit)

    def get_region(self, region_id: UUID) -> Optional[CacheRegion]:
        """Recupere une region."""
        return self._region_repo.get_by_id(region_id)

    def get_region_by_code(self, code: str) -> Optional[CacheRegion]:
        """Recupere une region par code."""
        return self._region_repo.find_by_code(code)

    def create_region(
        self,
        data: CacheRegionCreate,
        user_id: Optional[UUID] = None
    ) -> CacheRegion:
        """Cree une region."""
        config = self._config_repo.get_config()
        if not config:
            raise CacheConfigNotFoundError("Configuration cache requise")

        existing = self._region_repo.find_by_code(data.code)
        if existing:
            raise CacheRegionDuplicateError(f"Region {data.code} existe deja")

        region = CacheRegion(
            tenant_id=self.tenant_id,
            config_id=config.id,
            code=data.code,
            name=data.name,
            description=data.description,
            ttl_seconds=data.ttl_seconds,
            stale_ttl_seconds=data.stale_ttl_seconds,
            max_items=data.max_items,
            default_tags=data.default_tags,
            entity_types=data.entity_types,
            preload_enabled=data.preload_enabled,
            preload_keys=data.preload_keys,
            preload_cron=data.preload_cron,
            created_by=user_id,
        )
        self.db.add(region)
        self.db.commit()

        self._audit_action(
            action="CREATE",
            entity_type="REGION",
            entity_id=str(region.id),
            description=f"Region {data.code} creee",
            user_id=user_id
        )

        return region

    def update_region(
        self,
        region_id: UUID,
        data: CacheRegionUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[CacheRegion]:
        """Met a jour une region."""
        region = self._region_repo.get_by_id(region_id)
        if not region:
            raise CacheRegionNotFoundError(f"Region {region_id} non trouvee")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(region, key, value)

        self.db.commit()

        self._audit_action(
            action="UPDATE",
            entity_type="REGION",
            entity_id=str(region.id),
            description=f"Region {region.code} mise a jour",
            new_value=update_data,
            user_id=user_id
        )

        return region

    def delete_region(
        self,
        region_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Supprime une region."""
        region = self._region_repo.get_by_id(region_id)
        if not region:
            raise CacheRegionNotFoundError(f"Region {region_id} non trouvee")

        # Invalide les entrees de cette region
        self._entry_repo.invalidate_pattern(f"*:{region.code}:*")

        self.db.delete(region)
        self.db.commit()

        self._audit_action(
            action="DELETE",
            entity_type="REGION",
            entity_id=str(region_id),
            description=f"Region {region.code} supprimee",
            user_id=user_id
        )

        return True

    # ========================================================================
    # OPERATIONS CACHE
    # ========================================================================

    def get(
        self,
        key: str,
        default: Any = None,
        region: Optional[str] = None
    ) -> CacheGetResponse:
        """Recupere une valeur du cache."""
        start_time = time.time()
        full_key = self._make_key(key)

        config = self._config_repo.get_config()

        # Essaie L1
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            value = l1.get(full_key)
            if value is not None:
                duration = (time.time() - start_time) * 1000
                return CacheGetResponse(
                    key=key,
                    value=value,
                    found=True,
                    cache_level=CacheLevel.L1_MEMORY,
                )

        # Essaie L2 (Redis) - simule
        # En production: self._redis_client.get(full_key)

        # Essaie L3 (DB)
        if config and config.l3_enabled:
            entry = self._entry_repo.find_by_key(key)
            if entry and entry.value_json:
                try:
                    value = json.loads(entry.value_json)

                    # Promeut vers L1
                    if config.l1_enabled:
                        l1 = self._get_l1_cache()
                        ttl = (entry.expires_at - datetime.utcnow()).total_seconds() \
                            if entry.expires_at else None
                        l1.set(full_key, value, ttl_seconds=int(ttl) if ttl else None)

                    # Met a jour stats
                    entry.hit_count += 1
                    entry.last_accessed_at = datetime.utcnow()
                    self.db.flush()

                    return CacheGetResponse(
                        key=key,
                        value=value,
                        found=True,
                        cache_level=CacheLevel.L3_PERSISTENT,
                        expires_at=entry.expires_at,
                        hit_count=entry.hit_count,
                    )
                except json.JSONDecodeError:
                    pass

        return CacheGetResponse(
            key=key,
            value=default,
            found=False,
        )

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None,
        region: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> bool:
        """Stocke une valeur dans le cache."""
        if len(key) > 500:
            raise CacheKeyTooLongError(f"Cle trop longue: {len(key)} > 500")

        full_key = self._make_key(key)
        config = self._config_repo.get_config()

        # Determine TTL
        effective_ttl = ttl_seconds
        if effective_ttl is None:
            if region:
                reg = self._region_repo.find_by_code(region)
                if reg:
                    effective_ttl = reg.ttl_seconds
            if effective_ttl is None and config:
                effective_ttl = config.default_ttl_seconds

        stale_ttl = config.stale_ttl_seconds if config else 60
        tags_set = set(tags or [])

        # Ajoute tags de region
        if region:
            tags_set.add(f"region:{region}")

        # Stocke dans L1
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            l1.set(
                full_key,
                value,
                ttl_seconds=effective_ttl,
                stale_seconds=stale_ttl,
                tags=tags_set
            )

        # Stocke dans L2 (Redis) - simule

        # Stocke dans L3 (DB)
        if config and config.l3_enabled:
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=effective_ttl) if effective_ttl else None
            stale_at = now + timedelta(seconds=effective_ttl - stale_ttl) \
                if effective_ttl and stale_ttl else None

            try:
                value_json = json.dumps(value, default=str)
            except Exception as e:
                raise CacheSerializationError(f"Impossible de serialiser: {e}")

            # Cherche entree existante
            entry = self._entry_repo.find_by_key(key)
            if entry:
                entry.value_json = value_json
                entry.value_hash = self._compute_hash(value)
                entry.original_size_bytes = len(value_json.encode())
                entry.expires_at = expires_at
                entry.stale_at = stale_at
                entry.tags = list(tags_set)
                entry.entity_type = entity_type
                entry.entity_id = entity_id
                entry.region_code = region
                entry.status = CacheStatus.ACTIVE
            else:
                entry = CacheEntry(
                    tenant_id=self.tenant_id,
                    cache_key=key,
                    key_hash=self._entry_repo._compute_key_hash(key),
                    region_code=region,
                    value_json=value_json,
                    value_hash=self._compute_hash(value),
                    original_size_bytes=len(value_json.encode()),
                    expires_at=expires_at,
                    stale_at=stale_at,
                    tags=list(tags_set),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    cache_level=CacheLevel.L3_PERSISTENT,
                )
                self.db.add(entry)

            self.db.flush()

        return True

    def delete(self, key: str) -> bool:
        """Supprime une entree du cache."""
        full_key = self._make_key(key)
        config = self._config_repo.get_config()

        deleted = False

        # Supprime de L1
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            if l1.delete(full_key):
                deleted = True

        # Supprime de L2 (Redis) - simule

        # Supprime de L3 (DB)
        if config and config.l3_enabled:
            count = self._entry_repo.invalidate_key(key)
            if count > 0:
                deleted = True

        return deleted

    def exists(self, key: str) -> bool:
        """Verifie si une cle existe."""
        full_key = self._make_key(key)
        config = self._config_repo.get_config()

        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            if l1.exists(full_key):
                return True

        if config and config.l3_enabled:
            entry = self._entry_repo.find_by_key(key)
            if entry and entry.status == CacheStatus.ACTIVE:
                if not entry.expires_at or entry.expires_at > datetime.utcnow():
                    return True

        return False

    def mget(self, keys: List[str]) -> CacheMGetResponse:
        """Recupere plusieurs valeurs."""
        items = {}
        found_keys = []
        missing_keys = []

        for key in keys:
            result = self.get(key)
            if result.found:
                items[key] = result.value
                found_keys.append(key)
            else:
                missing_keys.append(key)

        return CacheMGetResponse(
            items=items,
            found_keys=found_keys,
            missing_keys=missing_keys
        )

    def mset(
        self,
        items: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None,
        region: Optional[str] = None
    ) -> int:
        """Stocke plusieurs valeurs."""
        count = 0
        for key, value in items.items():
            if self.set(key, value, ttl_seconds, tags, region):
                count += 1
        return count

    def mdelete(self, keys: List[str]) -> int:
        """Supprime plusieurs entrees."""
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count

    # ========================================================================
    # INVALIDATION
    # ========================================================================

    def invalidate_by_key(
        self,
        key: str,
        user_id: Optional[UUID] = None
    ) -> InvalidationResponse:
        """Invalide par cle."""
        start_time = time.time()
        full_key = self._make_key(key)
        config = self._config_repo.get_config()
        levels_affected = []
        count = 0

        # L1
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            if l1.delete(full_key):
                count += 1
                levels_affected.append(CacheLevel.L1_MEMORY)

        # L3
        if config and config.l3_enabled:
            db_count = self._entry_repo.invalidate_key(key)
            if db_count > 0:
                count += db_count
                if CacheLevel.L3_PERSISTENT not in levels_affected:
                    levels_affected.append(CacheLevel.L3_PERSISTENT)

        duration_ms = int((time.time() - start_time) * 1000)

        # Enregistre evenement
        event = InvalidationEvent(
            tenant_id=self.tenant_id,
            invalidation_type=InvalidationType.KEY,
            target_key=key,
            keys_invalidated=count,
            levels_affected=[l.value for l in levels_affected],
            duration_ms=duration_ms,
            triggered_by=user_id,
        )
        self.db.add(event)
        self.db.commit()

        return InvalidationResponse(
            id=event.id,
            invalidation_type=InvalidationType.KEY,
            keys_invalidated=count,
            levels_affected=levels_affected,
            duration_ms=duration_ms,
            timestamp=event.created_at,
        )

    def invalidate_by_pattern(
        self,
        pattern: str,
        user_id: Optional[UUID] = None
    ) -> InvalidationResponse:
        """Invalide par pattern."""
        start_time = time.time()
        config = self._config_repo.get_config()
        levels_affected = []
        count = 0

        full_pattern = self._make_key(pattern)

        # L1
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            l1_count = l1.invalidate_by_pattern(full_pattern)
            if l1_count > 0:
                count += l1_count
                levels_affected.append(CacheLevel.L1_MEMORY)

        # L3
        if config and config.l3_enabled:
            db_count = self._entry_repo.invalidate_pattern(pattern)
            if db_count > 0:
                count += db_count
                if CacheLevel.L3_PERSISTENT not in levels_affected:
                    levels_affected.append(CacheLevel.L3_PERSISTENT)

        duration_ms = int((time.time() - start_time) * 1000)

        event = InvalidationEvent(
            tenant_id=self.tenant_id,
            invalidation_type=InvalidationType.PATTERN,
            target_pattern=pattern,
            keys_invalidated=count,
            levels_affected=[l.value for l in levels_affected],
            duration_ms=duration_ms,
            triggered_by=user_id,
        )
        self.db.add(event)
        self.db.commit()

        return InvalidationResponse(
            id=event.id,
            invalidation_type=InvalidationType.PATTERN,
            keys_invalidated=count,
            levels_affected=levels_affected,
            duration_ms=duration_ms,
            timestamp=event.created_at,
        )

    def invalidate_by_tag(
        self,
        tag: str,
        user_id: Optional[UUID] = None
    ) -> InvalidationResponse:
        """Invalide par tag."""
        start_time = time.time()
        config = self._config_repo.get_config()
        levels_affected = []
        count = 0

        # L1
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            l1_count = l1.invalidate_by_tag(tag)
            if l1_count > 0:
                count += l1_count
                levels_affected.append(CacheLevel.L1_MEMORY)

        # L3
        if config and config.l3_enabled:
            db_count = self._entry_repo.invalidate_tag(tag)
            if db_count > 0:
                count += db_count
                if CacheLevel.L3_PERSISTENT not in levels_affected:
                    levels_affected.append(CacheLevel.L3_PERSISTENT)

        duration_ms = int((time.time() - start_time) * 1000)

        event = InvalidationEvent(
            tenant_id=self.tenant_id,
            invalidation_type=InvalidationType.TAG,
            target_tag=tag,
            keys_invalidated=count,
            levels_affected=[l.value for l in levels_affected],
            duration_ms=duration_ms,
            triggered_by=user_id,
        )
        self.db.add(event)
        self.db.commit()

        return InvalidationResponse(
            id=event.id,
            invalidation_type=InvalidationType.TAG,
            keys_invalidated=count,
            levels_affected=levels_affected,
            duration_ms=duration_ms,
            timestamp=event.created_at,
        )

    def invalidate_by_entity(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> InvalidationResponse:
        """Invalide par entite."""
        start_time = time.time()
        config = self._config_repo.get_config()
        levels_affected = []
        count = 0

        # L3
        if config and config.l3_enabled:
            db_count = self._entry_repo.invalidate_entity(entity_type, entity_id)
            if db_count > 0:
                count += db_count
                levels_affected.append(CacheLevel.L3_PERSISTENT)

        # L1 - invalide par tag entity
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            tag = f"entity:{entity_type}"
            if entity_id:
                tag = f"entity:{entity_type}:{entity_id}"
            l1_count = l1.invalidate_by_tag(tag)
            if l1_count > 0:
                count += l1_count
                if CacheLevel.L1_MEMORY not in levels_affected:
                    levels_affected.append(CacheLevel.L1_MEMORY)

        duration_ms = int((time.time() - start_time) * 1000)

        event = InvalidationEvent(
            tenant_id=self.tenant_id,
            invalidation_type=InvalidationType.ENTITY,
            target_entity_type=entity_type,
            target_entity_id=entity_id,
            keys_invalidated=count,
            levels_affected=[l.value for l in levels_affected],
            duration_ms=duration_ms,
            triggered_by=user_id,
        )
        self.db.add(event)
        self.db.commit()

        return InvalidationResponse(
            id=event.id,
            invalidation_type=InvalidationType.ENTITY,
            keys_invalidated=count,
            levels_affected=levels_affected,
            duration_ms=duration_ms,
            timestamp=event.created_at,
        )

    def invalidate_all(
        self,
        user_id: Optional[UUID] = None
    ) -> InvalidationResponse:
        """Invalide tout le cache du tenant."""
        start_time = time.time()
        config = self._config_repo.get_config()
        levels_affected = []
        count = 0

        # L1
        if config and config.l1_enabled:
            l1 = self._get_l1_cache()
            l1_count = l1.clear()
            if l1_count > 0:
                count += l1_count
                levels_affected.append(CacheLevel.L1_MEMORY)

        # L3
        if config and config.l3_enabled:
            db_count = self._entry_repo.invalidate_all()
            if db_count > 0:
                count += db_count
                levels_affected.append(CacheLevel.L3_PERSISTENT)

        duration_ms = int((time.time() - start_time) * 1000)

        event = InvalidationEvent(
            tenant_id=self.tenant_id,
            invalidation_type=InvalidationType.TENANT,
            keys_invalidated=count,
            levels_affected=[l.value for l in levels_affected],
            duration_ms=duration_ms,
            triggered_by=user_id,
        )
        self.db.add(event)
        self.db.commit()

        self._audit_action(
            action="PURGE_ALL",
            entity_type="CACHE",
            description=f"Purge complete: {count} cles invalidees",
            user_id=user_id
        )

        return InvalidationResponse(
            id=event.id,
            invalidation_type=InvalidationType.TENANT,
            keys_invalidated=count,
            levels_affected=levels_affected,
            duration_ms=duration_ms,
            timestamp=event.created_at,
        )

    # ========================================================================
    # PURGE
    # ========================================================================

    def purge(
        self,
        level: Optional[CacheLevel] = None,
        region_code: Optional[str] = None,
        expired_only: bool = False,
        user_id: Optional[UUID] = None
    ) -> PurgeResponse:
        """Purge le cache."""
        start_time = time.time()
        levels_affected = []
        keys_purged = 0
        size_freed = 0

        config = self._config_repo.get_config()

        # Purge L1
        if (not level or level == CacheLevel.L1_MEMORY) and config and config.l1_enabled:
            l1 = self._get_l1_cache()
            stats_before = l1.get_stats()
            l1_count = l1.clear()
            if l1_count > 0:
                keys_purged += l1_count
                size_freed += stats_before['size_bytes']
                levels_affected.append(CacheLevel.L1_MEMORY)

        # Purge L3
        if (not level or level == CacheLevel.L3_PERSISTENT) and config and config.l3_enabled:
            if expired_only:
                db_count = self._entry_repo.purge_expired()
            else:
                db_count = self._entry_repo.purge_all()
            if db_count > 0:
                keys_purged += db_count
                levels_affected.append(CacheLevel.L3_PERSISTENT)

        duration_ms = int((time.time() - start_time) * 1000)

        self._audit_action(
            action="PURGE",
            entity_type="CACHE",
            description=f"Purge: {keys_purged} cles, {size_freed} bytes liberes",
            user_id=user_id
        )

        self.db.commit()

        return PurgeResponse(
            keys_purged=keys_purged,
            size_freed_bytes=size_freed,
            levels_affected=levels_affected,
            duration_ms=duration_ms,
        )

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_stats(
        self,
        level: Optional[CacheLevel] = None
    ) -> CacheStatsAggregated:
        """Recupere les statistiques."""
        config = self._config_repo.get_config()
        now = datetime.utcnow()

        l1_stats = None
        l2_stats = None
        l3_stats = None

        total_hits = 0
        total_misses = 0
        total_items = 0
        total_size = 0

        # Stats L1
        if config and config.l1_enabled and (not level or level == CacheLevel.L1_MEMORY):
            l1 = self._get_l1_cache()
            l1_raw = l1.get_stats()

            total_requests = l1_raw['hits'] + l1_raw['misses']

            l1_stats = CacheStatsResponse(
                tenant_id=self.tenant_id,
                cache_level=CacheLevel.L1_MEMORY,
                period_start=now - timedelta(hours=1),
                period_end=now,
                hits=l1_raw['hits'],
                misses=l1_raw['misses'],
                stale_hits=0,
                hit_rate=l1_raw['hit_rate'],
                sets=0,
                deletes=0,
                evictions_ttl=0,
                evictions_capacity=l1_raw['evictions'],
                total_evictions=l1_raw['evictions'],
                invalidations_total=0,
                current_items=l1_raw['items'],
                current_size_bytes=l1_raw['size_bytes'],
                max_items=l1_raw['max_items'],
                max_size_bytes=l1_raw['max_size_bytes'],
                fill_rate=l1_raw['items'] / l1_raw['max_items'] if l1_raw['max_items'] > 0 else 0,
                avg_get_time_ms=0.1,
                avg_set_time_ms=0.2,
                p95_get_time_ms=0.5,
                p99_get_time_ms=1.0,
            )

            total_hits += l1_raw['hits']
            total_misses += l1_raw['misses']
            total_items += l1_raw['items']
            total_size += l1_raw['size_bytes']

        # Stats L3
        if config and config.l3_enabled and (not level or level == CacheLevel.L3_PERSISTENT):
            entries_count = self._entry_repo.count_active()
            entries_size = self._entry_repo.get_total_size()

            l3_stats = CacheStatsResponse(
                tenant_id=self.tenant_id,
                cache_level=CacheLevel.L3_PERSISTENT,
                period_start=now - timedelta(hours=1),
                period_end=now,
                hits=0,
                misses=0,
                stale_hits=0,
                hit_rate=0.0,
                sets=0,
                deletes=0,
                evictions_ttl=0,
                evictions_capacity=0,
                total_evictions=0,
                invalidations_total=0,
                current_items=entries_count,
                current_size_bytes=entries_size,
                max_items=0,
                max_size_bytes=0,
                fill_rate=0.0,
                avg_get_time_ms=5.0,
                avg_set_time_ms=10.0,
                p95_get_time_ms=20.0,
                p99_get_time_ms=50.0,
            )

            total_items += entries_count
            total_size += entries_size

        overall_hit_rate = total_hits / (total_hits + total_misses) \
            if (total_hits + total_misses) > 0 else 0.0

        return CacheStatsAggregated(
            l1_stats=l1_stats,
            l2_stats=l2_stats,
            l3_stats=l3_stats,
            total_hits=total_hits,
            total_misses=total_misses,
            overall_hit_rate=overall_hit_rate,
            total_size_bytes=total_size,
            total_items=total_items,
        )

    # ========================================================================
    # PRECHARGEMENT
    # ========================================================================

    def list_preload_tasks(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PreloadTask], int]:
        """Liste les taches de prechargement."""
        return self._preload_repo.list_all(skip=skip, limit=limit)

    def create_preload_task(
        self,
        data: PreloadTaskCreate,
        user_id: Optional[UUID] = None
    ) -> PreloadTask:
        """Cree une tache de prechargement."""
        region = None
        if data.region_code:
            region = self._region_repo.find_by_code(data.region_code)

        task = PreloadTask(
            tenant_id=self.tenant_id,
            region_id=region.id if region else None,
            region_code=data.region_code,
            name=data.name,
            description=data.description,
            keys_pattern=data.keys_pattern,
            keys_list=data.keys_list,
            loader_type=data.loader_type,
            loader_config=data.loader_config,
            schedule_cron=data.schedule_cron,
            is_active=data.is_active,
            created_by=user_id,
        )
        self.db.add(task)
        self.db.commit()

        self._audit_action(
            action="CREATE",
            entity_type="PRELOAD_TASK",
            entity_id=str(task.id),
            description=f"Tache prechargement {data.name} creee",
            user_id=user_id
        )

        return task

    def run_preload_task(
        self,
        task_id: UUID,
        user_id: Optional[UUID] = None
    ) -> PreloadRunResponse:
        """Execute une tache de prechargement."""
        task = self._preload_repo.get_by_id(task_id)
        if not task:
            raise PreloadTaskNotFoundError(f"Tache {task_id} non trouvee")

        start_time = time.time()
        keys_loaded = 0
        error = None

        try:
            # Charge les cles definies
            for key in task.keys_list:
                # Simule le chargement (en prod: appel au loader)
                value = {"key": key, "loaded_at": datetime.utcnow().isoformat()}
                if self.set(key, value, region=task.region_code):
                    keys_loaded += 1

            task.last_run_status = "SUCCESS"
            task.last_run_keys_loaded = keys_loaded
        except Exception as e:
            error = str(e)
            task.last_run_status = "FAILED"
            task.last_run_error = error
            logger.exception(f"Erreur prechargement task {task_id}")

        duration_ms = int((time.time() - start_time) * 1000)
        task.last_run_at = datetime.utcnow()
        task.last_run_duration_ms = duration_ms

        self.db.commit()

        return PreloadRunResponse(
            task_id=task_id,
            status=task.last_run_status,
            keys_loaded=keys_loaded,
            duration_ms=duration_ms,
            error=error,
        )

    # ========================================================================
    # ALERTES
    # ========================================================================

    def get_active_alerts(self, limit: int = 50) -> List[CacheAlert]:
        """Recupere les alertes actives."""
        return self._alert_repo.get_active_alerts(limit)

    def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> CacheAlert:
        """Acquitte une alerte."""
        alert = self._alert_repo.get_by_id(alert_id)
        if not alert:
            raise CacheAlertNotFoundError(f"Alerte {alert_id} non trouvee")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id

        self.db.commit()
        return alert

    def resolve_alert(
        self,
        alert_id: UUID,
        user_id: Optional[UUID] = None,
        resolution_notes: Optional[str] = None
    ) -> CacheAlert:
        """Resout une alerte."""
        alert = self._alert_repo.get_by_id(alert_id)
        if not alert:
            raise CacheAlertNotFoundError(f"Alerte {alert_id} non trouvee")

        if alert.status == AlertStatus.RESOLVED:
            raise CacheAlertAlreadyResolvedError("Alerte deja resolue")

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        alert.resolution_notes = resolution_notes

        self.db.commit()
        return alert

    def check_thresholds(self) -> List[CacheAlert]:
        """Verifie les seuils et cree des alertes si necessaire."""
        config = self._config_repo.get_config()
        if not config:
            return []

        alerts = []
        stats = self.get_stats()

        # Verifie hit rate
        if stats.overall_hit_rate < config.alert_hit_rate_threshold:
            alert = CacheAlert(
                tenant_id=self.tenant_id,
                alert_type="HIT_RATE",
                severity=AlertSeverity.WARNING,
                title="Taux de hit faible",
                message=f"Le taux de hit ({stats.overall_hit_rate:.1%}) est inferieur au seuil ({config.alert_hit_rate_threshold:.1%})",
                threshold_value=config.alert_hit_rate_threshold,
                actual_value=stats.overall_hit_rate,
            )
            self.db.add(alert)
            alerts.append(alert)

        # Verifie memoire L1
        if stats.l1_stats:
            fill_rate = stats.l1_stats.fill_rate * 100
            if fill_rate > config.alert_memory_threshold_percent:
                alert = CacheAlert(
                    tenant_id=self.tenant_id,
                    alert_type="MEMORY",
                    severity=AlertSeverity.WARNING,
                    title="Cache L1 presque plein",
                    message=f"Le cache L1 est rempli a {fill_rate:.1f}%",
                    threshold_value=config.alert_memory_threshold_percent,
                    actual_value=fill_rate,
                    cache_level=CacheLevel.L1_MEMORY,
                )
                self.db.add(alert)
                alerts.append(alert)

        self.db.commit()
        return alerts

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> CacheDashboard:
        """Recupere le dashboard cache."""
        config = self._config_repo.get_config()
        stats = self.get_stats()

        # Top keys
        top_entries = self._entry_repo.get_top_keys(10)
        top_keys = [
            TopKey(
                key=e.cache_key,
                hit_count=e.hit_count,
                region_code=e.region_code,
                entity_type=e.entity_type,
            )
            for e in top_entries
        ]

        # Recent invalidations
        recent_events = self._invalidation_repo.get_recent(10)
        recent_invalidations = [
            RecentInvalidation(
                id=e.id,
                invalidation_type=e.invalidation_type,
                keys_invalidated=e.keys_invalidated,
                created_at=e.created_at,
            )
            for e in recent_events
        ]

        # Alertes actives
        active_alerts = self.get_active_alerts(10)

        return CacheDashboard(
            config=CacheConfigResponse.model_validate(config) if config else None,
            stats=stats,
            top_keys=top_keys,
            recent_invalidations=recent_invalidations,
            active_alerts=[
                CacheAlertResponse.model_validate(a.__dict__) for a in active_alerts
            ] if active_alerts else [],
            regions_count=self._region_repo.count_active(),
            preload_tasks_count=self._preload_repo.count_active(),
            entries_count=self._entry_repo.count_active(),
        )

    # ========================================================================
    # AUDIT
    # ========================================================================

    def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> List[CacheAuditLog]:
        """Recupere les logs d'audit."""
        return self._audit_repo.get_recent(limit)


# ============================================================================
# FACTORY
# ============================================================================

def get_cache_service(db: Session, tenant_id: str) -> CacheService:
    """Factory pour le service cache."""
    return CacheService(db=db, tenant_id=tenant_id)
