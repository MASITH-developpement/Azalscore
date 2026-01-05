"""
AZALS - Cache Redis ÉLITE
=========================
Cache distribué pour performance et scalabilité.
Support Redis, fallback mémoire en développement.
"""

import json
import logging
import hashlib
from typing import Optional, Callable, TypeVar
from functools import wraps
import redis
from redis.exceptions import RedisError
from app.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheBackend:
    """Interface abstraite pour le cache."""

    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError

    def set(self, key: str, value: str, ttl: int) -> bool:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def clear_pattern(self, pattern: str) -> int:
        raise NotImplementedError

    def incr(self, key: str, ttl: Optional[int] = None) -> int:
        raise NotImplementedError


class RedisCache(CacheBackend):
    """Cache Redis pour production."""

    def __init__(self, redis_url: str, prefix: str = "azals"):
        self._client: Optional[redis.Redis] = None
        self._redis_url = redis_url
        self._prefix = prefix
        self._connected = False

    def _get_client(self) -> Optional[redis.Redis]:
        """Connexion lazy au Redis."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self._client.ping()
                self._connected = True
                logger.info("Redis connecté avec succès")
            except RedisError as e:
                logger.warning(f"Redis non disponible: {e}")
                self._connected = False
                return None
        return self._client if self._connected else None

    def _key(self, key: str) -> str:
        """Préfixe la clé."""
        return f"{self._prefix}:{key}"

    def get(self, key: str) -> Optional[str]:
        client = self._get_client()
        if client:
            try:
                return client.get(self._key(key))
            except RedisError as e:
                logger.error(f"Redis GET error: {e}")
        return None

    def set(self, key: str, value: str, ttl: int = 300) -> bool:
        client = self._get_client()
        if client:
            try:
                return client.setex(self._key(key), ttl, value)
            except RedisError as e:
                logger.error(f"Redis SET error: {e}")
        return False

    def delete(self, key: str) -> bool:
        client = self._get_client()
        if client:
            try:
                return client.delete(self._key(key)) > 0
            except RedisError as e:
                logger.error(f"Redis DELETE error: {e}")
        return False

    def exists(self, key: str) -> bool:
        client = self._get_client()
        if client:
            try:
                return client.exists(self._key(key)) > 0
            except RedisError as e:
                logger.error(f"Redis EXISTS error: {e}")
        return False

    def clear_pattern(self, pattern: str) -> int:
        """Supprime toutes les clés matchant le pattern."""
        client = self._get_client()
        if client:
            try:
                full_pattern = self._key(pattern)
                keys = client.keys(full_pattern)
                if keys:
                    return client.delete(*keys)
            except RedisError as e:
                logger.error(f"Redis CLEAR_PATTERN error: {e}")
        return 0

    def incr(self, key: str, ttl: Optional[int] = None) -> int:
        """Incrémente un compteur (pour rate limiting)."""
        client = self._get_client()
        if client:
            try:
                full_key = self._key(key)
                value = client.incr(full_key)
                if ttl and value == 1:  # Premier incr, on set le TTL
                    client.expire(full_key, ttl)
                return value
            except RedisError as e:
                logger.error(f"Redis INCR error: {e}")
        return 0

    @property
    def is_connected(self) -> bool:
        return self._connected


class MemoryCache(CacheBackend):
    """Cache mémoire pour développement/test."""

    def __init__(self):
        self._store: dict = {}
        self._expires: dict = {}
        import time
        self._time = time

    def _is_expired(self, key: str) -> bool:
        if key in self._expires:
            return self._time.time() > self._expires[key]
        return False

    def _cleanup(self, key: str):
        if self._is_expired(key):
            self._store.pop(key, None)
            self._expires.pop(key, None)
            return True
        return False

    def get(self, key: str) -> Optional[str]:
        self._cleanup(key)
        return self._store.get(key)

    def set(self, key: str, value: str, ttl: int = 300) -> bool:
        self._store[key] = value
        self._expires[key] = self._time.time() + ttl
        return True

    def delete(self, key: str) -> bool:
        existed = key in self._store
        self._store.pop(key, None)
        self._expires.pop(key, None)
        return existed

    def exists(self, key: str) -> bool:
        self._cleanup(key)
        return key in self._store

    def clear_pattern(self, pattern: str) -> int:
        import fnmatch
        keys_to_delete = [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
        for k in keys_to_delete:
            self.delete(k)
        return len(keys_to_delete)

    def incr(self, key: str, ttl: Optional[int] = None) -> int:
        self._cleanup(key)
        value = int(self._store.get(key, 0)) + 1
        self._store[key] = str(value)
        if ttl:
            self._expires[key] = self._time.time() + ttl
        return value


# Instance globale du cache
_cache: Optional[CacheBackend] = None


def get_cache() -> CacheBackend:
    """Retourne l'instance de cache (singleton)."""
    global _cache
    if _cache is None:
        settings = get_settings()
        if settings.redis_url:
            _cache = RedisCache(settings.redis_url)
            if not _cache.is_connected:
                logger.warning("Redis indisponible, fallback sur cache mémoire")
                _cache = MemoryCache()
        else:
            logger.info("Redis URL non configurée, utilisation cache mémoire")
            _cache = MemoryCache()
    return _cache


# Décorateur de mise en cache
def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Décorateur pour mettre en cache le résultat d'une fonction.

    Args:
        ttl: Time-to-live en secondes
        key_prefix: Préfixe pour la clé de cache
        key_builder: Fonction pour construire la clé (args, kwargs) -> str

    Utilisation:
        @cached(ttl=60, key_prefix="user")
        def get_user(user_id: int) -> User:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache()

            # Construction de la clé
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Clé par défaut: hash des arguments
                key_data = f"{args}:{kwargs}"
                key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
                key = f"{key_prefix}:{func.__name__}:{key_hash}"

            # Vérification du cache
            cached_value = cache.get(key)
            if cached_value is not None:
                try:
                    return json.loads(cached_value)
                except json.JSONDecodeError:
                    return cached_value

            # Exécution de la fonction
            result = func(*args, **kwargs)

            # Mise en cache
            try:
                cache.set(key, json.dumps(result), ttl)
            except (TypeError, ValueError):
                # Non sérialisable en JSON, on stocke tel quel si c'est une string
                if isinstance(result, str):
                    cache.set(key, result, ttl)

            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalide toutes les clés matchant le pattern.

    Args:
        pattern: Pattern glob (ex: "user:*", "tenant:masith:*")

    Returns:
        Nombre de clés supprimées
    """
    cache = get_cache()
    return cache.clear_pattern(pattern)


def cache_key_tenant(tenant_id: str, *parts: str) -> str:
    """
    Construit une clé de cache scopée par tenant.

    Args:
        tenant_id: ID du tenant
        parts: Parties de la clé

    Returns:
        Clé de cache formatée
    """
    return f"tenant:{tenant_id}:{':'.join(parts)}"


# TTL prédéfinis
class CacheTTL:
    """Time-to-live standards pour différents types de données."""
    SHORT = 60          # 1 minute (données très volatiles)
    MEDIUM = 300        # 5 minutes (par défaut)
    LONG = 900          # 15 minutes (données peu volatiles)
    HOUR = 3600         # 1 heure (référentiels)
    DAY = 86400         # 1 jour (configurations)
    RATE_LIMIT = 60     # 1 minute (rate limiting)
