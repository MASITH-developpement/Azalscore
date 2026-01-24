"""
AZALS - Token Blacklist Service
================================
Gestion de la révocation des tokens JWT côté serveur.
Permet l'invalidation immédiate des tokens lors du logout.

SÉCURITÉ:
- Stockage en mémoire avec fallback Redis en production
- TTL automatique basé sur l'expiration du token
- Thread-safe pour environnements multi-workers
"""

import os
import threading
import time
from datetime import datetime
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TokenBlacklist:
    """
    Service de blacklist de tokens JWT.

    En production, utilise Redis pour la synchronisation entre workers.
    En développement, utilise un stockage en mémoire thread-safe.

    Usage:
        blacklist = TokenBlacklist.get_instance()
        blacklist.add(jti, exp_timestamp)
        if blacklist.is_blacklisted(jti):
            raise AuthenticationError("Token révoqué")
    """

    _instance: Optional['TokenBlacklist'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialise le service de blacklist."""
        self._memory_store: dict[str, float] = {}  # jti -> expiration timestamp
        self._memory_lock = threading.Lock()
        self._redis_client = None
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

        # Tenter connexion Redis en production
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialise la connexion Redis si disponible."""
        redis_url = os.environ.get("REDIS_URL")
        env = os.environ.get("ENVIRONMENT", "development")

        if redis_url and env == "production":
            try:
                import redis
                self._redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test de connexion
                self._redis_client.ping()
                logger.info("[TOKEN_BLACKLIST] Redis connecté pour blacklist distribuée")
            except ImportError:
                logger.warning("[TOKEN_BLACKLIST] Package redis non installé, fallback mémoire")
                self._redis_client = None
            except Exception as e:
                logger.warning(f"[TOKEN_BLACKLIST] Redis indisponible ({e}), fallback mémoire")
                self._redis_client = None
        else:
            if env == "production":
                logger.warning(
                    "[TOKEN_BLACKLIST] REDIS_URL non configuré en production! "
                    "Blacklist non distribuée entre workers."
                )

    @classmethod
    def get_instance(cls) -> 'TokenBlacklist':
        """Singleton thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset le singleton (utile pour les tests)."""
        with cls._lock:
            cls._instance = None

    def add(self, jti: str, exp_timestamp: float) -> bool:
        """
        Ajoute un token à la blacklist.

        Args:
            jti: JWT ID unique du token
            exp_timestamp: Timestamp d'expiration du token

        Returns:
            True si ajouté avec succès
        """
        if not jti:
            return False

        # Calculer TTL (garder jusqu'à expiration + marge de 60s)
        ttl = max(1, int(exp_timestamp - time.time()) + 60)

        # Redis si disponible
        if self._redis_client:
            try:
                key = f"token_blacklist:{jti}"
                self._redis_client.setex(key, ttl, "1")
                logger.debug(f"[TOKEN_BLACKLIST] Token {jti[:16]}... blacklisté (Redis, TTL={ttl}s)")
                return True
            except Exception as e:
                logger.warning(f"[TOKEN_BLACKLIST] Erreur Redis, fallback mémoire: {e}")

        # Fallback mémoire
        with self._memory_lock:
            self._memory_store[jti] = exp_timestamp
            self._maybe_cleanup()

        logger.debug(f"[TOKEN_BLACKLIST] Token {jti[:16]}... blacklisté (mémoire, TTL={ttl}s)")
        return True

    def is_blacklisted(self, jti: str) -> bool:
        """
        Vérifie si un token est dans la blacklist.

        Args:
            jti: JWT ID unique du token

        Returns:
            True si le token est blacklisté
        """
        if not jti:
            return False

        # Redis si disponible
        if self._redis_client:
            try:
                key = f"token_blacklist:{jti}"
                result = self._redis_client.exists(key)
                return bool(result)
            except Exception as e:
                logger.warning(f"[TOKEN_BLACKLIST] Erreur Redis, fallback mémoire: {e}")

        # Vérification mémoire
        with self._memory_lock:
            if jti in self._memory_store:
                exp = self._memory_store[jti]
                # Vérifier si pas encore expiré
                if exp > time.time():
                    return True
                # Nettoyer l'entrée expirée
                del self._memory_store[jti]

        return False

    def remove(self, jti: str) -> bool:
        """
        Retire un token de la blacklist (rarement utilisé).

        Args:
            jti: JWT ID unique du token

        Returns:
            True si retiré avec succès
        """
        if not jti:
            return False

        # Redis si disponible
        if self._redis_client:
            try:
                key = f"token_blacklist:{jti}"
                self._redis_client.delete(key)
            except Exception as e:
                logger.warning(f"[TOKEN_BLACKLIST] Erreur Redis lors de suppression: {e}")

        # Mémoire
        with self._memory_lock:
            if jti in self._memory_store:
                del self._memory_store[jti]
                return True

        return False

    def _maybe_cleanup(self) -> None:
        """Nettoie les entrées expirées si nécessaire."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        self._last_cleanup = now
        expired = [jti for jti, exp in self._memory_store.items() if exp <= now]

        for jti in expired:
            del self._memory_store[jti]

        if expired:
            logger.debug(f"[TOKEN_BLACKLIST] Nettoyage: {len(expired)} tokens expirés supprimés")

    def count(self) -> int:
        """Retourne le nombre de tokens blacklistés."""
        if self._redis_client:
            try:
                keys = self._redis_client.keys("token_blacklist:*")
                return len(keys)
            except Exception:
                pass

        with self._memory_lock:
            return len(self._memory_store)

    def clear(self) -> None:
        """Vide la blacklist (ATTENTION: usage tests uniquement)."""
        if self._redis_client:
            try:
                keys = self._redis_client.keys("token_blacklist:*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"[TOKEN_BLACKLIST] Erreur Redis lors de clear: {e}")

        with self._memory_lock:
            self._memory_store.clear()

        logger.info("[TOKEN_BLACKLIST] Blacklist vidée")


def blacklist_token(jti: str, exp_timestamp: float) -> bool:
    """
    Fonction utilitaire pour blacklister un token.

    Args:
        jti: JWT ID unique
        exp_timestamp: Timestamp d'expiration

    Returns:
        True si succès
    """
    return TokenBlacklist.get_instance().add(jti, exp_timestamp)


def is_token_blacklisted(jti: str) -> bool:
    """
    Fonction utilitaire pour vérifier si un token est blacklisté.

    Args:
        jti: JWT ID unique

    Returns:
        True si blacklisté
    """
    return TokenBlacklist.get_instance().is_blacklisted(jti)


__all__ = [
    'TokenBlacklist',
    'blacklist_token',
    'is_token_blacklisted',
]
