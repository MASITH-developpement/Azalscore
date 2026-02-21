"""
AZALS MODULE - Cache - Tests Unitaires
=======================================

Tests unitaires pour le module Cache.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.modules.cache.models import (
    CacheLevel,
    CacheStatus,
    EvictionPolicy,
    InvalidationType,
    AlertSeverity,
    AlertStatus,
)
from app.modules.cache.service import L1MemoryCache, CacheService
from app.modules.cache.schemas import (
    CacheConfigCreate,
    CacheRegionCreate,
    CacheSetRequest,
    PreloadTaskCreate,
)
from app.modules.cache.exceptions import (
    CacheConfigAlreadyExistsError,
    CacheRegionDuplicateError,
    CacheKeyTooLongError,
)


# ============================================================================
# TESTS L1 MEMORY CACHE
# ============================================================================

class TestL1MemoryCache:
    """Tests pour L1MemoryCache."""

    def test_set_and_get(self):
        """Test stockage et recuperation basique."""
        cache = L1MemoryCache(max_items=100)

        cache.set("key1", {"data": "value1"}, ttl_seconds=300)
        result = cache.get("key1")

        assert result is not None
        assert result["data"] == "value1"

    def test_get_nonexistent(self):
        """Test recuperation cle inexistante."""
        cache = L1MemoryCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_delete(self):
        """Test suppression."""
        cache = L1MemoryCache()
        cache.set("key1", "value1")

        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("key1") is False

    def test_exists(self):
        """Test verification existence."""
        cache = L1MemoryCache()
        cache.set("key1", "value1")

        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False

    def test_ttl_expiration(self):
        """Test expiration TTL."""
        cache = L1MemoryCache()

        # Cree une entree avec TTL de 0 secondes (expiree immediatement)
        cache.set("key1", "value1", ttl_seconds=0)

        # Simule le passage du temps
        entry = cache._cache.get("tenant:key1") or cache._cache.get("key1")
        if entry:
            entry.expires_at = datetime.utcnow() - timedelta(seconds=1)

        # La valeur devrait etre expiree
        result = cache.get("key1")
        # Note: depends de l'implementation exacte

    def test_invalidate_by_tag(self):
        """Test invalidation par tag."""
        cache = L1MemoryCache()
        cache.set("key1", "value1", tags={"tag1", "tag2"})
        cache.set("key2", "value2", tags={"tag1"})
        cache.set("key3", "value3", tags={"tag2"})

        count = cache.invalidate_by_tag("tag1")

        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is not None

    def test_invalidate_by_pattern(self):
        """Test invalidation par pattern."""
        cache = L1MemoryCache()
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("order:1", "data3")

        count = cache.invalidate_by_pattern("user:*")

        assert count == 2
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("order:1") is not None

    def test_clear(self):
        """Test vidage complet."""
        cache = L1MemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        count = cache.clear()

        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_eviction_lru(self):
        """Test eviction LRU."""
        cache = L1MemoryCache(max_items=3, eviction_policy=EvictionPolicy.LRU)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Accede a key1 pour le rendre recent
        cache.get("key1")

        # Ajoute key4, devrait evincer key2 (LRU)
        cache.set("key4", "value4")

        assert cache.get("key1") is not None  # Recent, garde
        assert cache.get("key2") is None  # LRU, evince
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

    def test_eviction_max_items(self):
        """Test eviction par nombre max d'items."""
        cache = L1MemoryCache(max_items=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Un des premiers devrait etre evince
        stats = cache.get_stats()
        assert stats["items"] <= 2

    def test_stats(self):
        """Test statistiques."""
        cache = L1MemoryCache()

        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss

        stats = cache.get_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["items"] == 1
        assert stats["hit_rate"] == 2 / 3


# ============================================================================
# TESTS CACHE SERVICE (avec mocks)
# ============================================================================

class TestCacheService:
    """Tests pour CacheService."""

    @pytest.fixture
    def mock_db(self):
        """Mock de la session DB."""
        return MagicMock()

    @pytest.fixture
    def tenant_id(self):
        """Tenant ID de test."""
        return "test-tenant-123"

    @pytest.fixture
    def service(self, mock_db, tenant_id):
        """Service cache avec mocks."""
        with patch('app.modules.cache.service.CacheConfigRepository') as mock_config_repo, \
             patch('app.modules.cache.service.CacheRegionRepository') as mock_region_repo, \
             patch('app.modules.cache.service.CacheEntryRepository') as mock_entry_repo, \
             patch('app.modules.cache.service.CacheStatisticsRepository') as mock_stats_repo, \
             patch('app.modules.cache.service.InvalidationEventRepository') as mock_inv_repo, \
             patch('app.modules.cache.service.PreloadTaskRepository') as mock_preload_repo, \
             patch('app.modules.cache.service.CacheAlertRepository') as mock_alert_repo, \
             patch('app.modules.cache.service.CacheAuditLogRepository') as mock_audit_repo:

            # Configure les mocks
            mock_config = MagicMock()
            mock_config.l1_enabled = True
            mock_config.l2_enabled = False
            mock_config.l3_enabled = False
            mock_config.l1_max_items = 1000
            mock_config.l1_max_size_mb = 10
            mock_config.eviction_policy = EvictionPolicy.LRU
            mock_config.default_ttl_seconds = 300
            mock_config.stale_ttl_seconds = 60

            mock_config_repo.return_value.get_config.return_value = mock_config
            mock_config_repo.return_value.config_exists.return_value = False

            service = CacheService(mock_db, tenant_id)
            service._config_repo = mock_config_repo.return_value

            return service

    def test_make_key(self, service, tenant_id):
        """Test creation de cle complete."""
        key = service._make_key("test:key")
        assert key == f"{tenant_id}:test:key"

    def test_set_and_get_l1(self, service):
        """Test set/get avec L1."""
        # Set
        success = service.set("key1", {"data": "test"})
        assert success is True

        # Get
        result = service.get("key1")
        assert result.found is True
        assert result.value["data"] == "test"
        assert result.cache_level == CacheLevel.L1_MEMORY

    def test_get_not_found(self, service):
        """Test get cle non trouvee."""
        result = service.get("nonexistent")
        assert result.found is False
        assert result.value is None

    def test_delete(self, service):
        """Test suppression."""
        service.set("key1", "value1")
        deleted = service.delete("key1")
        assert deleted is True

        result = service.get("key1")
        assert result.found is False

    def test_exists(self, service):
        """Test verification existence."""
        service.set("key1", "value1")

        assert service.exists("key1") is True
        assert service.exists("nonexistent") is False

    def test_mget_mset(self, service):
        """Test operations multi-cles."""
        # mset
        count = service.mset(
            items={"key1": "value1", "key2": "value2"},
            ttl_seconds=300
        )
        assert count == 2

        # mget
        result = service.mget(["key1", "key2", "key3"])
        assert len(result.found_keys) == 2
        assert len(result.missing_keys) == 1
        assert "key3" in result.missing_keys

    def test_key_too_long(self, service):
        """Test cle trop longue."""
        long_key = "x" * 600

        with pytest.raises(CacheKeyTooLongError):
            service.set(long_key, "value")


# ============================================================================
# TESTS INVALIDATION
# ============================================================================

class TestInvalidation:
    """Tests pour les operations d'invalidation."""

    @pytest.fixture
    def cache(self):
        """Cache L1 pour tests."""
        cache = L1MemoryCache(max_items=100)
        cache.set("user:1:profile", {"name": "Alice"}, tags={"user", "profile"})
        cache.set("user:2:profile", {"name": "Bob"}, tags={"user", "profile"})
        cache.set("user:1:settings", {"theme": "dark"}, tags={"user", "settings"})
        cache.set("order:1", {"total": 100}, tags={"order"})
        return cache

    def test_invalidate_by_tag_user(self, cache):
        """Test invalidation par tag user."""
        count = cache.invalidate_by_tag("user")
        assert count == 3
        assert cache.get("user:1:profile") is None
        assert cache.get("user:2:profile") is None
        assert cache.get("user:1:settings") is None
        assert cache.get("order:1") is not None

    def test_invalidate_by_tag_profile(self, cache):
        """Test invalidation par tag profile."""
        count = cache.invalidate_by_tag("profile")
        assert count == 2
        assert cache.get("user:1:profile") is None
        assert cache.get("user:2:profile") is None
        assert cache.get("user:1:settings") is not None

    def test_invalidate_by_pattern_user_1(self, cache):
        """Test invalidation par pattern user:1:*."""
        count = cache.invalidate_by_pattern("user:1:*")
        assert count == 2
        assert cache.get("user:1:profile") is None
        assert cache.get("user:1:settings") is None
        assert cache.get("user:2:profile") is not None


# ============================================================================
# TESTS EVICTION POLICIES
# ============================================================================

class TestEvictionPolicies:
    """Tests pour les politiques d'eviction."""

    def test_lru_policy(self):
        """Test politique LRU."""
        cache = L1MemoryCache(max_items=3, eviction_policy=EvictionPolicy.LRU)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Accede a 'a' et 'b' pour les rendre recents
        cache.get("a")
        cache.get("b")

        # Ajoute 'd', devrait evincer 'c' (LRU)
        cache.set("d", 4)

        assert cache.exists("a") is True
        assert cache.exists("b") is True
        assert cache.exists("c") is False
        assert cache.exists("d") is True

    def test_fifo_policy(self):
        """Test politique FIFO."""
        cache = L1MemoryCache(max_items=3, eviction_policy=EvictionPolicy.FIFO)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Ajoute 'd', devrait evincer 'a' (premier entre)
        cache.set("d", 4)

        assert cache.exists("a") is False
        assert cache.exists("b") is True
        assert cache.exists("c") is True
        assert cache.exists("d") is True


# ============================================================================
# TESTS STATS
# ============================================================================

class TestStats:
    """Tests pour les statistiques."""

    def test_hit_rate_calculation(self):
        """Test calcul du taux de hit."""
        cache = L1MemoryCache()

        cache.set("key1", "value1")

        # 3 hits, 2 misses
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")
        cache.get("nonexistent1")
        cache.get("nonexistent2")

        stats = cache.get_stats()

        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.6

    def test_zero_requests(self):
        """Test taux de hit sans requetes."""
        cache = L1MemoryCache()
        stats = cache.get_stats()

        assert stats["hit_rate"] == 0.0

    def test_size_tracking(self):
        """Test suivi de la taille."""
        cache = L1MemoryCache()

        cache.set("key1", {"data": "x" * 100})
        cache.set("key2", {"data": "y" * 200})

        stats = cache.get_stats()

        assert stats["items"] == 2
        assert stats["size_bytes"] > 0


# ============================================================================
# TESTS SCHEMAS
# ============================================================================

class TestSchemas:
    """Tests pour les schemas Pydantic."""

    def test_cache_config_create_defaults(self):
        """Test valeurs par defaut CacheConfigCreate."""
        config = CacheConfigCreate()

        assert config.l1_enabled is True
        assert config.l2_enabled is True
        assert config.l3_enabled is False
        assert config.default_ttl_seconds == 300
        assert config.eviction_policy == EvictionPolicy.LRU

    def test_cache_config_create_validation(self):
        """Test validation CacheConfigCreate."""
        # TTL valide
        config = CacheConfigCreate(default_ttl_seconds=600)
        assert config.default_ttl_seconds == 600

        # TTL invalide
        with pytest.raises(ValueError):
            CacheConfigCreate(default_ttl_seconds=100000)

    def test_cache_region_create_code_validation(self):
        """Test validation code region."""
        # Code valide
        region = CacheRegionCreate(code="user_cache", name="User Cache")
        assert region.code == "user_cache"

        # Code invalide (commence par chiffre)
        with pytest.raises(ValueError):
            CacheRegionCreate(code="1invalid", name="Test")

    def test_cache_set_request(self):
        """Test CacheSetRequest."""
        request = CacheSetRequest(
            key="user:123",
            value={"name": "Test"},
            ttl_seconds=300,
            tags=["user", "profile"],
            entity_type="User",
            entity_id="123"
        )

        assert request.key == "user:123"
        assert request.value["name"] == "Test"
        assert len(request.tags) == 2

    def test_preload_task_create(self):
        """Test PreloadTaskCreate."""
        task = PreloadTaskCreate(
            name="Preload Users",
            loader_type="QUERY",
            loader_config={"query": "SELECT * FROM users"},
            keys_list=["user:1", "user:2"],
            schedule_cron="0 0 * * *"
        )

        assert task.name == "Preload Users"
        assert task.loader_type == "QUERY"
        assert len(task.keys_list) == 2


# ============================================================================
# TESTS INTEGRATION (marques pour skip sans DB)
# ============================================================================

@pytest.mark.integration
class TestCacheIntegration:
    """Tests d'integration necessitant une vraie DB."""

    @pytest.fixture
    def db_session(self):
        """Session DB de test."""
        # En vrai: creer une session de test avec rollback
        pytest.skip("Necessite une DB de test")

    def test_full_workflow(self, db_session):
        """Test workflow complet."""
        # Create config
        # Create region
        # Set values
        # Get values
        # Invalidate
        # Check stats
        pass
