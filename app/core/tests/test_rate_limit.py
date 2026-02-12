"""
Tests pour le service de rate limiting.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.rate_limit import (
    RateLimiter,
    RateLimitResult,
    check_ip_rate_limit,
    check_tenant_rate_limit,
    check_endpoint_rate_limit,
)


class TestRateLimiter:
    """Tests du service RateLimiter."""

    def setup_method(self):
        """Reset le singleton avant chaque test."""
        RateLimiter.reset_instance()

    def test_singleton_pattern(self):
        """Vérifie que RateLimiter est un singleton."""
        instance1 = RateLimiter.get_instance()
        instance2 = RateLimiter.get_instance()
        assert instance1 is instance2

    def test_check_rate_limit_allows_first_request(self):
        """La première requête doit être autorisée."""
        limiter = RateLimiter.get_instance()
        result = limiter.check_rate_limit(
            key="test:first",
            limit=10,
            window_seconds=60
        )

        assert result.allowed is True
        assert result.current_count == 1
        assert result.remaining == 9

    def test_check_rate_limit_blocks_after_limit(self):
        """Les requêtes sont bloquées après la limite."""
        limiter = RateLimiter.get_instance()

        # Consommer toute la limite
        for i in range(10):
            result = limiter.check_rate_limit(
                key="test:exhaust",
                limit=10,
                window_seconds=60
            )
            if i < 10:
                assert result.allowed is True

        # La 11ème requête doit être bloquée
        result = limiter.check_rate_limit(
            key="test:exhaust",
            limit=10,
            window_seconds=60
        )
        assert result.allowed is False
        assert result.remaining == 0

    def test_check_ip_rate_limit(self):
        """Test de la fonction utilitaire check_ip_rate_limit."""
        result = check_ip_rate_limit("192.168.1.1", limit=5)

        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
        assert result.limit == 5

    def test_check_tenant_rate_limit(self):
        """Test de la fonction utilitaire check_tenant_rate_limit."""
        result = check_tenant_rate_limit("tenant-123", limit=100)

        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
        assert result.limit == 100

    def test_check_endpoint_rate_limit(self):
        """Test de la fonction utilitaire check_endpoint_rate_limit."""
        result = check_endpoint_rate_limit(
            ip="192.168.1.1",
            endpoint="/auth/login",
            limit=10
        )

        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
        assert result.limit == 10

    def test_different_keys_have_separate_limits(self):
        """Différentes clés ont des limites séparées."""
        limiter = RateLimiter.get_instance()

        # Consommer la limite pour une clé
        for _ in range(5):
            limiter.check_rate_limit("key:a", limit=5, window_seconds=60)

        # L'autre clé doit toujours être accessible
        result = limiter.check_rate_limit("key:b", limit=5, window_seconds=60)
        assert result.allowed is True

    def test_get_stats_returns_info(self):
        """get_stats retourne des informations sur le backend."""
        limiter = RateLimiter.get_instance()
        stats = limiter.get_stats()

        assert "backend" in stats
        assert stats["backend"] in ["redis", "memory"]
        assert "redis_available" in stats

    def test_clear_key_removes_rate_limit(self):
        """clear_key supprime les compteurs pour une clé."""
        limiter = RateLimiter.get_instance()

        # Créer des entrées
        limiter.check_rate_limit("test:clear", limit=10, window_seconds=60)

        # Supprimer
        success = limiter.clear_key("test:clear")
        assert success is True

        # Vérifier que le compteur est remis à zéro
        result = limiter.check_rate_limit("test:clear", limit=10, window_seconds=60)
        assert result.current_count == 1  # Première requête après clear


class TestRateLimiterWithRedisMock:
    """Tests avec Redis mocké."""

    def setup_method(self):
        """Reset le singleton avant chaque test."""
        RateLimiter.reset_instance()

    def test_fallback_to_memory_when_no_redis_url(self):
        """Sans REDIS_URL, utilise le stockage mémoire."""
        with patch.dict('os.environ', {}, clear=False):
            # S'assurer que REDIS_URL n'est pas défini
            import os
            os.environ.pop('REDIS_URL', None)

            RateLimiter.reset_instance()
            limiter = RateLimiter.get_instance()

            assert limiter._redis_available is False
            stats = limiter.get_stats()
            assert stats["backend"] == "memory"
