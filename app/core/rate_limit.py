"""
AZALS - Rate Limiting Service
=============================
Service de rate limiting distribué avec Redis.

Architecture:
- Redis comme backend principal (distribuée entre workers)
- Fallback en mémoire si Redis indisponible
- Algorithme: Sliding window counter avec TTL

SÉCURITÉ:
- Isolation par IP et par tenant
- Protection contre DoS et abus
- Logging des violations pour audit

Usage:
    rate_limiter = RateLimiter.get_instance()
    is_allowed, info = rate_limiter.check_rate_limit(
        key="ip:192.168.1.1",
        limit=100,
        window_seconds=60
    )
"""

import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Résultat d'une vérification de rate limit."""
    allowed: bool
    current_count: int
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp
    retry_after: int  # Seconds


class RateLimiter:
    """
    Service de rate limiting distribué.

    Utilise Redis en production pour synchroniser les compteurs
    entre les workers. Fallback automatique en mémoire si Redis
    n'est pas disponible.

    Algorithme: Sliding window avec compteur atomique et TTL.
    """

    _instance: Optional['RateLimiter'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialise le rate limiter."""
        self._redis_client = None
        self._memory_store: dict[str, list[float]] = defaultdict(list)
        self._memory_lock = threading.Lock()
        self._redis_available = False

        # Tentative de connexion Redis
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialise la connexion Redis si disponible."""
        redis_url = os.environ.get("REDIS_URL")

        if redis_url:
            try:
                import redis
                self._redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                # Test de connexion
                self._redis_client.ping()
                self._redis_available = True
                logger.info("[RATE_LIMIT] Redis connecté pour rate limiting distribué")
            except ImportError:
                logger.warning("[RATE_LIMIT] Package redis non installé, fallback mémoire")
            except Exception as e:
                logger.warning(
                    "[RATE_LIMIT] Redis indisponible, fallback mémoire",
                    extra={"error": str(e)[:200], "consequence": "memory_fallback"}
                )
        else:
            env = os.environ.get("ENVIRONMENT", "development")
            if env == "production":
                logger.warning(
                    "[RATE_LIMIT] REDIS_URL non configuré en production! "
                    "Rate limiting non distribué entre workers."
                )

    @classmethod
    def get_instance(cls) -> 'RateLimiter':
        """Singleton thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset le singleton (pour les tests)."""
        with cls._lock:
            cls._instance = None

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> RateLimitResult:
        """
        Vérifie si une requête est autorisée selon le rate limit.

        Args:
            key: Clé unique (ex: "ip:192.168.1.1" ou "tenant:abc123")
            limit: Nombre maximum de requêtes dans la fenêtre
            window_seconds: Durée de la fenêtre en secondes

        Returns:
            RateLimitResult avec le statut et les métriques
        """
        current_time = int(time.time())
        reset_at = current_time + window_seconds

        # Utiliser Redis si disponible
        if self._redis_available and self._redis_client:
            try:
                return self._check_redis(key, limit, window_seconds, current_time, reset_at)
            except Exception as e:
                logger.warning(
                    "[RATE_LIMIT] Erreur Redis, fallback mémoire",
                    extra={"error": str(e)[:200], "key": key[:50]}
                )

        # Fallback mémoire
        return self._check_memory(key, limit, window_seconds, current_time, reset_at)

    def _check_redis(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        current_time: int,
        reset_at: int
    ) -> RateLimitResult:
        """Vérification rate limit via Redis."""
        redis_key = f"azals:ratelimit:{key}"

        # Pipeline atomique: INCR + EXPIRE si nouvelle clé
        pipe = self._redis_client.pipeline()
        pipe.incr(redis_key)
        pipe.ttl(redis_key)
        results = pipe.execute()

        current_count = results[0]
        ttl = results[1]

        # Définir TTL si c'est une nouvelle clé (TTL = -1)
        if ttl == -1:
            self._redis_client.expire(redis_key, window_seconds)
            ttl = window_seconds

        # Calculer reset_at basé sur le TTL actuel
        actual_reset_at = current_time + max(ttl, 0)

        allowed = current_count <= limit
        remaining = max(0, limit - current_count)

        if not allowed:
            logger.debug(
                "[RATE_LIMIT] Limite atteinte (Redis)",
                extra={
                    "key": key[:50],
                    "current": current_count,
                    "limit": limit,
                    "reset_in": ttl
                }
            )

        return RateLimitResult(
            allowed=allowed,
            current_count=current_count,
            limit=limit,
            remaining=remaining,
            reset_at=actual_reset_at,
            retry_after=max(0, ttl) if not allowed else 0
        )

    def _check_memory(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        current_time: int,
        reset_at: int
    ) -> RateLimitResult:
        """Vérification rate limit via mémoire (fallback)."""
        with self._memory_lock:
            # Nettoyer les entrées expirées
            cutoff = current_time - window_seconds
            self._memory_store[key] = [
                t for t in self._memory_store[key] if t > cutoff
            ]

            current_count = len(self._memory_store[key])
            allowed = current_count < limit

            if allowed:
                self._memory_store[key].append(current_time)
                current_count += 1

            remaining = max(0, limit - current_count)

            # Calculer le reset basé sur la plus ancienne entrée
            if self._memory_store[key]:
                oldest = min(self._memory_store[key])
                reset_at = int(oldest) + window_seconds
            else:
                reset_at = current_time + window_seconds

            if not allowed:
                logger.debug(
                    "[RATE_LIMIT] Limite atteinte (mémoire)",
                    extra={
                        "key": key[:50],
                        "current": current_count,
                        "limit": limit
                    }
                )

            return RateLimitResult(
                allowed=allowed,
                current_count=current_count,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=max(0, reset_at - current_time) if not allowed else 0
            )

    def is_redis_available(self) -> bool:
        """Retourne True si Redis est disponible."""
        return self._redis_available

    def get_stats(self) -> dict:
        """Retourne les statistiques du rate limiter."""
        stats = {
            "backend": "redis" if self._redis_available else "memory",
            "redis_available": self._redis_available,
        }

        if not self._redis_available:
            with self._memory_lock:
                stats["memory_keys"] = len(self._memory_store)
                stats["memory_entries"] = sum(
                    len(v) for v in self._memory_store.values()
                )

        return stats

    def clear_key(self, key: str) -> bool:
        """
        Supprime une clé de rate limit (pour admin/tests).

        Args:
            key: Clé à supprimer

        Returns:
            True si supprimé
        """
        if self._redis_available and self._redis_client:
            try:
                redis_key = f"azals:ratelimit:{key}"
                return bool(self._redis_client.delete(redis_key))
            except Exception as e:
                logger.warning(
                    "[RATE_LIMIT] Erreur Redis clear_key",
                    extra={"error": str(e)[:200]}
                )

        with self._memory_lock:
            if key in self._memory_store:
                del self._memory_store[key]
                return True
        return False


# Fonctions utilitaires pour usage simplifié
def check_ip_rate_limit(
    ip: str,
    limit: int = 100,
    window: int = 60
) -> RateLimitResult:
    """
    Vérifie le rate limit pour une IP.

    Args:
        ip: Adresse IP client
        limit: Requêtes max par fenêtre (default: 100)
        window: Fenêtre en secondes (default: 60)

    Returns:
        RateLimitResult
    """
    return RateLimiter.get_instance().check_rate_limit(
        key=f"ip:{ip}",
        limit=limit,
        window_seconds=window
    )


def check_tenant_rate_limit(
    tenant_id: str,
    limit: int = 500,
    window: int = 60
) -> RateLimitResult:
    """
    Vérifie le rate limit pour un tenant.

    Args:
        tenant_id: ID du tenant
        limit: Requêtes max par fenêtre (default: 500)
        window: Fenêtre en secondes (default: 60)

    Returns:
        RateLimitResult
    """
    return RateLimiter.get_instance().check_rate_limit(
        key=f"tenant:{tenant_id}",
        limit=limit,
        window_seconds=window
    )


def check_endpoint_rate_limit(
    ip: str,
    endpoint: str,
    limit: int = 20,
    window: int = 60
) -> RateLimitResult:
    """
    Vérifie le rate limit pour un endpoint spécifique (ex: /auth/login).

    Args:
        ip: Adresse IP client
        endpoint: Path de l'endpoint
        limit: Requêtes max par fenêtre (default: 20)
        window: Fenêtre en secondes (default: 60)

    Returns:
        RateLimitResult
    """
    # Normaliser l'endpoint
    clean_endpoint = endpoint.replace("/", "_").strip("_")
    return RateLimiter.get_instance().check_rate_limit(
        key=f"endpoint:{ip}:{clean_endpoint}",
        limit=limit,
        window_seconds=window
    )


__all__ = [
    'RateLimiter',
    'RateLimitResult',
    'check_ip_rate_limit',
    'check_tenant_rate_limit',
    'check_endpoint_rate_limit',
]
