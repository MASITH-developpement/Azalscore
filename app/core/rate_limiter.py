"""
AZALS - Rate Limiter avec support Redis
========================================

SÉCURITÉ P1-4: Rate limiting distribué pour multi-instance.
Supporte Redis en production, fallback in-memory en dev.

Usage:
    from app.core.rate_limiter import rate_limiter

    # Vérifier le rate limit
    rate_limiter.check_rate("login", ip_address, limit=10, window=60)

    # Enregistrer une tentative
    rate_limiter.record_attempt("login", ip_address)

    # Enregistrer un échec (compteur séparé)
    rate_limiter.record_failure("login", email)
"""
from __future__ import annotations


import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiterBackend(ABC):
    """Interface abstraite pour les backends de rate limiting."""

    @abstractmethod
    def get_count(self, key: str, window_seconds: int) -> int:
        """Retourne le nombre de tentatives dans la fenêtre."""
        pass

    @abstractmethod
    def increment(self, key: str, window_seconds: int) -> int:
        """Incrémente le compteur et retourne la nouvelle valeur."""
        pass

    @abstractmethod
    def get_failure_count(self, key: str) -> int:
        """Retourne le nombre d'échecs consécutifs."""
        pass

    @abstractmethod
    def increment_failure(self, key: str, ttl_seconds: int) -> int:
        """Incrémente les échecs et retourne la nouvelle valeur."""
        pass

    @abstractmethod
    def reset_failures(self, key: str) -> None:
        """Réinitialise le compteur d'échecs."""
        pass


class MemoryRateLimiterBackend(RateLimiterBackend):
    """
    Backend in-memory pour développement.

    ATTENTION: Ne fonctionne pas en mode multi-instance.
    Utiliser Redis en production.
    """

    def __init__(self):
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._failures: dict[str, int] = defaultdict(int)
        self._failure_timestamps: dict[str, float] = {}
        self._lock = Lock()
        logger.warning(
            "[RATE_LIMITER] Using in-memory backend. "
            "NOT suitable for production multi-instance deployment."
        )

    def _cleanup(self, key: str, window_seconds: int) -> None:
        """Nettoie les tentatives expirées."""
        cutoff = time.time() - window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]

    def get_count(self, key: str, window_seconds: int) -> int:
        with self._lock:
            self._cleanup(key, window_seconds)
            return len(self._attempts[key])

    def increment(self, key: str, window_seconds: int) -> int:
        with self._lock:
            self._cleanup(key, window_seconds)
            self._attempts[key].append(time.time())
            return len(self._attempts[key])

    def get_failure_count(self, key: str) -> int:
        with self._lock:
            # Auto-expire failures after 15 minutes
            timestamp = self._failure_timestamps.get(key, 0)
            if time.time() - timestamp > 900:
                self._failures[key] = 0
            return self._failures[key]

    def increment_failure(self, key: str, ttl_seconds: int = 900) -> int:
        with self._lock:
            self._failures[key] += 1
            self._failure_timestamps[key] = time.time()
            return self._failures[key]

    def reset_failures(self, key: str) -> None:
        with self._lock:
            self._failures[key] = 0
            self._failure_timestamps.pop(key, None)


class RedisRateLimiterBackend(RateLimiterBackend):
    """
    Backend Redis pour production multi-instance.

    Utilise des compteurs Redis avec expiration automatique.
    Pattern: Sliding window avec INCR + EXPIRE.
    """

    def __init__(self, redis_client):
        self._redis = redis_client
        self._prefix = "azals:ratelimit:"
        logger.info("[RATE_LIMITER] Using Redis backend for distributed rate limiting")

    def _make_key(self, key: str, suffix: str = "") -> str:
        """Génère une clé Redis avec préfixe."""
        return f"{self._prefix}{key}{suffix}"

    def get_count(self, key: str, window_seconds: int) -> int:
        """
        Retourne le nombre de tentatives dans la fenêtre.
        Utilise une clé avec le timestamp de la fenêtre actuelle.
        """
        window_key = self._make_key(key, f":{int(time.time()) // window_seconds}")
        count = self._redis.get(window_key)
        return int(count) if count else 0

    def increment(self, key: str, window_seconds: int) -> int:
        """
        Incrémente le compteur avec expiration automatique.
        Pattern INCR + EXPIRE atomique via pipeline.
        """
        window_key = self._make_key(key, f":{int(time.time()) // window_seconds}")

        pipe = self._redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window_seconds + 1)
        results = pipe.execute()

        return results[0]

    def get_failure_count(self, key: str) -> int:
        """Retourne le nombre d'échecs consécutifs."""
        failure_key = self._make_key(key, ":failures")
        count = self._redis.get(failure_key)
        return int(count) if count else 0

    def increment_failure(self, key: str, ttl_seconds: int = 900) -> int:
        """Incrémente les échecs avec TTL."""
        failure_key = self._make_key(key, ":failures")

        pipe = self._redis.pipeline()
        pipe.incr(failure_key)
        pipe.expire(failure_key, ttl_seconds)
        results = pipe.execute()

        return results[0]

    def reset_failures(self, key: str) -> None:
        """Réinitialise le compteur d'échecs."""
        failure_key = self._make_key(key, ":failures")
        self._redis.delete(failure_key)


class RateLimiter:
    """
    Rate limiter unifié avec backend configurable.

    SÉCURITÉ P1-4: Supporte Redis pour déploiements distribués.
    """

    def __init__(self, backend: Optional[RateLimiterBackend] = None):
        self._backend = backend or self._create_default_backend()

    def _create_default_backend(self) -> RateLimiterBackend:
        """Crée le backend par défaut (Redis si disponible, sinon Memory)."""
        try:
            from app.core.config import get_settings
            settings = get_settings()

            # Essayer Redis si configuré
            redis_url = getattr(settings, 'redis_url', None)
            if redis_url:
                try:
                    import redis
                    client = redis.from_url(redis_url, decode_responses=True)
                    client.ping()  # Test connection
                    return RedisRateLimiterBackend(client)
                except ImportError:
                    logger.warning(
                        "[RATE_LIMITER] redis package not installed. "
                        "pip install redis for production."
                    )
                except Exception as e:
                    logger.warning("[RATE_LIMITER] Redis connection failed: %s", e)
        except Exception as e:
            logger.warning("[RATE_LIMITER] Settings load failed: %s", e)

        # Fallback to memory
        return MemoryRateLimiterBackend()

    def check_rate(
        self,
        action: str,
        identifier: str,
        limit: int,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Vérifie si le rate limit est atteint.

        Args:
            action: Type d'action (login, register, api)
            identifier: Identifiant unique (IP, email, user_id)
            limit: Nombre max de tentatives
            window_seconds: Fenêtre de temps en secondes

        Returns:
            (is_allowed, current_count)
        """
        key = f"{action}:{identifier}"
        count = self._backend.get_count(key, window_seconds)
        return count < limit, count

    def record_attempt(
        self,
        action: str,
        identifier: str,
        window_seconds: int = 60
    ) -> int:
        """
        Enregistre une tentative.

        Returns:
            Nombre actuel de tentatives dans la fenêtre
        """
        key = f"{action}:{identifier}"
        return self._backend.increment(key, window_seconds)

    def check_failures(
        self,
        action: str,
        identifier: str,
        max_failures: int = 5
    ) -> tuple[bool, int]:
        """
        Vérifie si le nombre d'échecs dépasse le maximum.

        Returns:
            (is_allowed, failure_count)
        """
        key = f"{action}:{identifier}"
        count = self._backend.get_failure_count(key)
        return count < max_failures, count

    def record_failure(
        self,
        action: str,
        identifier: str,
        ttl_seconds: int = 900
    ) -> int:
        """
        Enregistre un échec.

        Returns:
            Nombre actuel d'échecs
        """
        key = f"{action}:{identifier}"
        return self._backend.increment_failure(key, ttl_seconds)

    def reset_failures(self, action: str, identifier: str) -> None:
        """Réinitialise les échecs pour un identifiant."""
        key = f"{action}:{identifier}"
        self._backend.reset_failures(key)

    @property
    def is_distributed(self) -> bool:
        """Retourne True si utilise un backend distribué."""
        return isinstance(self._backend, RedisRateLimiterBackend)


# Instance globale
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Retourne l'instance globale du rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# Alias pour import simple
rate_limiter = get_rate_limiter()


# =============================================================================
# AUTH RATE LIMITER - Wrapper spécialisé pour authentification
# =============================================================================

class AuthRateLimiter:
    """
    Rate limiter spécialisé pour l'authentification.

    SÉCURITÉ P1-4: Utilise le backend Redis quand disponible.
    Compatible avec l'ancienne API in-memory.
    """

    def __init__(self):
        self._limiter = get_rate_limiter()

    def check_login_rate(self, ip: str, email: str) -> None:
        """
        Vérifie le rate limit pour login.

        Raises:
            HTTPException 429 si limit atteinte
        """
        from fastapi import HTTPException, status
        from app.core.config import get_settings

        settings = get_settings()
        limit = settings.auth_rate_limit_per_minute

        # Vérification par IP
        allowed, count = self._limiter.check_rate("login:ip", ip, limit, 60)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts from this IP. Wait 60 seconds.",
                headers={"Retry-After": "60"}
            )

        # Vérification par email (3x plus permissif)
        allowed, count = self._limiter.check_rate("login:email", email, limit * 3, 60)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts for this account. Wait 60 seconds.",
                headers={"Retry-After": "60"}
            )

        # Blocage si trop d'échecs consécutifs
        allowed, failures = self._limiter.check_failures("login", email, 5)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to failed attempts. Wait 15 minutes.",
                headers={"Retry-After": "900"}
            )

    def record_login_attempt(self, ip: str, email: str, success: bool) -> None:
        """Enregistre une tentative de login."""
        self._limiter.record_attempt("login:ip", ip, 60)
        self._limiter.record_attempt("login:email", email, 60)

        if success:
            self._limiter.reset_failures("login", email)
        else:
            self._limiter.record_failure("login", email, 900)

    def check_register_rate(self, ip: str) -> None:
        """
        Vérifie le rate limit pour registration.

        Raises:
            HTTPException 429 si limit atteinte
        """
        from fastapi import HTTPException, status

        # Max 3 registrations par 5 minutes par IP
        allowed, count = self._limiter.check_rate("register", ip, 3, 300)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts. Wait 5 minutes.",
                headers={"Retry-After": "300"}
            )

    def record_register_attempt(self, ip: str) -> None:
        """Enregistre une tentative d'inscription."""
        self._limiter.record_attempt("register", ip, 300)


# Instance pour rétrocompatibilité avec auth.py
auth_rate_limiter = AuthRateLimiter()


# =============================================================================
# PLATFORM-WIDE RATE LIMITING MIDDLEWARE
# =============================================================================

class PlatformRateLimitMiddleware:
    """
    Middleware de rate limiting global pour toute la plateforme.

    SÉCURITÉ: Protège contre les attaques DDoS et abuse API.

    Limites par défaut:
    - Par IP: 1000 requêtes/minute
    - Par Tenant: 5000 requêtes/minute
    - Global plateforme: 50000 requêtes/minute

    Usage:
        from app.core.rate_limiter import PlatformRateLimitMiddleware
        app.add_middleware(PlatformRateLimitMiddleware)
    """

    def __init__(
        self,
        app,
        ip_limit: int = 1000,
        tenant_limit: int = 5000,
        global_limit: int = 50000,
        window_seconds: int = 60
    ):
        self.app = app
        self.ip_limit = ip_limit
        self.tenant_limit = tenant_limit
        self.global_limit = global_limit
        self.window = window_seconds
        self._limiter = get_rate_limiter()

    async def __call__(self, scope, receive, send):
        """ASGI middleware interface."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request
        from starlette.responses import JSONResponse

        request = Request(scope, receive)

        # Extraire IP
        client_ip = self._get_client_ip(request)

        # Vérifier limite par IP
        allowed, count = self._limiter.check_rate("platform:ip", client_ip, self.ip_limit, self.window)
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"IP rate limit: {self.ip_limit}/min exceeded",
                    "retry_after": self.window
                },
                headers={"Retry-After": str(self.window)}
            )
            await response(scope, receive, send)
            return

        # Extraire tenant_id si présent
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            allowed, count = self._limiter.check_rate("platform:tenant", tenant_id, self.tenant_limit, self.window)
            if not allowed:
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Tenant rate limit: {self.tenant_limit}/min exceeded",
                        "retry_after": self.window
                    },
                    headers={"Retry-After": str(self.window)}
                )
                await response(scope, receive, send)
                return

        # Vérifier limite globale plateforme
        allowed, count = self._limiter.check_rate("platform:global", "all", self.global_limit, self.window)
        if not allowed:
            logger.critical(
                "[RATE_LIMIT] Platform global limit reached: %s/%s", count, self.global_limit
            )
            response = JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily unavailable",
                    "detail": "Platform capacity exceeded. Please retry later.",
                    "retry_after": self.window
                },
                headers={"Retry-After": str(self.window)}
            )
            await response(scope, receive, send)
            return

        # Enregistrer les requêtes
        self._limiter.record_attempt("platform:ip", client_ip, self.window)
        if tenant_id:
            self._limiter.record_attempt("platform:tenant", tenant_id, self.window)
        self._limiter.record_attempt("platform:global", "all", self.window)

        await self.app(scope, receive, send)

    def _get_client_ip(self, request: "Request") -> str:
        """Extrait l'IP client de manière sécurisée."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        if request.client:
            return request.client.host
        return "unknown"


def setup_platform_rate_limiting(
    app,
    ip_limit: int = 1000,
    tenant_limit: int = 5000,
    global_limit: int = 50000
):
    """
    Configure le rate limiting global sur l'application.

    Args:
        app: Application FastAPI/Starlette
        ip_limit: Requêtes max par IP par minute
        tenant_limit: Requêtes max par tenant par minute
        global_limit: Requêtes max globales par minute
    """
    app.add_middleware(
        PlatformRateLimitMiddleware,
        ip_limit=ip_limit,
        tenant_limit=tenant_limit,
        global_limit=global_limit
    )
    logger.info(
        "[RATE_LIMIT] Platform limits configured: "
        f"IP={ip_limit}/min, Tenant={tenant_limit}/min, Global={global_limit}/min"
    )


__all__ = [
    "RateLimiter",
    "RateLimiterBackend",
    "MemoryRateLimiterBackend",
    "RedisRateLimiterBackend",
    "get_rate_limiter",
    "rate_limiter",
    "AuthRateLimiter",
    "auth_rate_limiter",
    "PlatformRateLimitMiddleware",
    "setup_platform_rate_limiting",
]
