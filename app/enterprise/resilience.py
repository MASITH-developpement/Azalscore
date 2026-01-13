"""
AZALSCORE Enterprise - Resilience & Fault Tolerance
=====================================================
Mécanismes de résilience niveau enterprise.

Fonctionnalités:
- Circuit Breaker (pattern disjoncteur)
- Back-pressure multi-niveaux
- Graceful degradation
- Bulkhead isolation

Inspiré de:
- Netflix Hystrix
- Resilience4j
- AWS Circuit Breaker pattern
"""

import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable, Any, TypeVar, Generic
from enum import Enum
from collections import deque
import functools

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """États du circuit breaker."""
    CLOSED = "closed"      # Normal - toutes les requêtes passent
    OPEN = "open"          # Ouvert - requêtes rejetées
    HALF_OPEN = "half_open"  # Test - quelques requêtes autorisées


@dataclass
class CircuitBreakerConfig:
    """Configuration du circuit breaker."""
    # Seuils d'ouverture
    failure_threshold: int = 5        # Nombre d'échecs avant ouverture
    failure_rate_threshold: float = 0.5  # Taux d'échec (50%)
    slow_call_threshold: float = 0.5   # Taux d'appels lents

    # Fenêtre de mesure
    sliding_window_size: int = 10     # Taille fenêtre glissante
    minimum_calls: int = 5            # Appels min avant évaluation

    # Timing
    slow_call_duration_ms: int = 2000  # Seuil appel lent
    wait_duration_seconds: int = 30    # Durée état OPEN
    permitted_calls_half_open: int = 3  # Appels autorisés en HALF_OPEN

    # Recovery
    recovery_rate_threshold: float = 0.8  # Taux succès pour fermer


@dataclass
class CircuitBreakerMetrics:
    """Métriques du circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    slow_calls: int = 0
    rejected_calls: int = 0

    failure_rate: float = 0.0
    slow_call_rate: float = 0.0

    state_changes: int = 0
    last_state_change: Optional[datetime] = None
    time_in_open_state_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "slow_calls": self.slow_calls,
            "rejected_calls": self.rejected_calls,
            "failure_rate": round(self.failure_rate, 3),
            "slow_call_rate": round(self.slow_call_rate, 3),
            "state_changes": self.state_changes,
            "time_in_open_state_seconds": round(self.time_in_open_state_seconds, 2),
        }


class CircuitBreaker:
    """
    Circuit Breaker - Protection contre les défaillances en cascade.

    États:
    - CLOSED: Fonctionnement normal
    - OPEN: Service dégradé, requêtes rejetées
    - HALF_OPEN: Phase de test/récupération

    Usage:
        cb = CircuitBreaker("database")

        @cb.protect
        async def query_database():
            ...
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[str, CircuitState, CircuitState], None]] = None,
        fallback: Optional[Callable[[], Any]] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._on_state_change = on_state_change
        self._fallback = fallback

        self._state = CircuitState.CLOSED
        self._state_changed_at = datetime.utcnow()
        self._metrics = CircuitBreakerMetrics()

        # Fenêtre glissante des résultats (succès/échec/durée)
        self._results: deque = deque(maxlen=self.config.sliding_window_size)

        # Compteur pour HALF_OPEN
        self._half_open_calls = 0
        self._half_open_successes = 0

        # Lock thread-safe
        self._lock = threading.RLock()

        logger.info(f"[CIRCUIT_BREAKER] {name} initialized in CLOSED state")

    @property
    def state(self) -> CircuitState:
        """Retourne l'état actuel du circuit."""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        return self._metrics

    def _check_state_transition(self) -> None:
        """Vérifie si une transition d'état est nécessaire."""
        now = datetime.utcnow()

        if self._state == CircuitState.OPEN:
            # Vérifier si on peut passer en HALF_OPEN
            open_duration = (now - self._state_changed_at).total_seconds()
            if open_duration >= self.config.wait_duration_seconds:
                self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Effectue une transition d'état."""
        old_state = self._state
        if old_state == new_state:
            return

        now = datetime.utcnow()

        # Calculer temps dans l'état précédent
        if old_state == CircuitState.OPEN:
            duration = (now - self._state_changed_at).total_seconds()
            self._metrics.time_in_open_state_seconds += duration

        self._state = new_state
        self._state_changed_at = now
        self._metrics.state_changes += 1
        self._metrics.last_state_change = now

        # Reset pour HALF_OPEN
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._half_open_successes = 0

        # Reset métriques pour CLOSED
        if new_state == CircuitState.CLOSED:
            self._results.clear()

        logger.warning(
            f"[CIRCUIT_BREAKER] {self.name}: {old_state.value} -> {new_state.value}",
            extra={"circuit": self.name, "old_state": old_state.value, "new_state": new_state.value}
        )

        # Callback
        if self._on_state_change:
            try:
                self._on_state_change(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"[CIRCUIT_BREAKER] State change callback error: {e}")

    def _record_success(self, duration_ms: float) -> None:
        """Enregistre un appel réussi."""
        with self._lock:
            is_slow = duration_ms > self.config.slow_call_duration_ms
            self._results.append({"success": True, "slow": is_slow, "duration_ms": duration_ms})

            self._metrics.total_calls += 1
            self._metrics.successful_calls += 1
            if is_slow:
                self._metrics.slow_calls += 1

            self._update_rates()

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                self._half_open_successes += 1
                if self._half_open_successes >= self.config.permitted_calls_half_open:
                    self._transition_to(CircuitState.CLOSED)

    def _record_failure(self, duration_ms: float, error: Optional[Exception] = None) -> None:
        """Enregistre un appel échoué."""
        with self._lock:
            self._results.append({"success": False, "slow": False, "duration_ms": duration_ms})

            self._metrics.total_calls += 1
            self._metrics.failed_calls += 1

            self._update_rates()

            if self._state == CircuitState.HALF_OPEN:
                # Échec en HALF_OPEN -> retour OPEN
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                # Vérifier si on doit ouvrir
                if self._should_open():
                    self._transition_to(CircuitState.OPEN)

    def _update_rates(self) -> None:
        """Met à jour les taux de mesure."""
        if len(self._results) == 0:
            return

        successes = sum(1 for r in self._results if r["success"])
        failures = len(self._results) - successes
        slow = sum(1 for r in self._results if r.get("slow", False))

        self._metrics.failure_rate = failures / len(self._results)
        self._metrics.slow_call_rate = slow / len(self._results)

    def _should_open(self) -> bool:
        """Détermine si le circuit doit s'ouvrir."""
        if len(self._results) < self.config.minimum_calls:
            return False

        return (
            self._metrics.failure_rate >= self.config.failure_rate_threshold or
            self._metrics.slow_call_rate >= self.config.slow_call_threshold
        )

    def can_execute(self) -> bool:
        """Vérifie si une exécution est autorisée."""
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.OPEN:
                self._metrics.rejected_calls += 1
                return False
            elif self._state == CircuitState.HALF_OPEN:
                return self._half_open_calls < self.config.permitted_calls_half_open

        return False

    def protect(self, func: Callable) -> Callable:
        """Décorateur pour protéger une fonction."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not self.can_execute():
                if self._fallback:
                    return self._fallback()
                raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                self._record_success(duration)
                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                self._record_failure(duration, e)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self.can_execute():
                if self._fallback:
                    return self._fallback()
                raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                self._record_success(duration)
                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                self._record_failure(duration, e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def reset(self) -> None:
        """Reset manuel du circuit breaker."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._results.clear()
            logger.info(f"[CIRCUIT_BREAKER] {self.name} manually reset")


class CircuitBreakerOpenError(Exception):
    """Exception levée quand le circuit est ouvert."""
    pass


class BackPressureLevel(str, Enum):
    """Niveaux de back-pressure."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BackPressureConfig:
    """Configuration du back-pressure."""
    # Seuils de pression (% capacité)
    low_threshold: float = 0.5
    medium_threshold: float = 0.7
    high_threshold: float = 0.85
    critical_threshold: float = 0.95

    # Actions par niveau
    low_action: str = "log"
    medium_action: str = "throttle_low_priority"
    high_action: str = "reject_low_priority"
    critical_action: str = "reject_all_new"

    # Capacités
    max_queue_size: int = 1000
    max_concurrent_requests: int = 100
    max_memory_percent: float = 0.8


@dataclass
class BackPressureMetrics:
    """Métriques de back-pressure."""
    current_level: BackPressureLevel = BackPressureLevel.NONE
    current_pressure: float = 0.0
    queue_size: int = 0
    concurrent_requests: int = 0
    rejected_count: int = 0
    throttled_count: int = 0

    level_changes: int = 0
    time_in_high_pressure_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "current_level": self.current_level.value,
            "current_pressure": round(self.current_pressure, 3),
            "queue_size": self.queue_size,
            "concurrent_requests": self.concurrent_requests,
            "rejected_count": self.rejected_count,
            "throttled_count": self.throttled_count,
            "level_changes": self.level_changes,
        }


class BackPressure:
    """
    Back-Pressure Controller - Gestion de la charge système.

    Protège le système contre la surcharge en:
    - Monitorant la pression (queue, concurrent requests, memory)
    - Appliquant des actions graduées selon le niveau
    - Priorisant les tenants premium

    Usage:
        bp = BackPressure("api")

        if bp.should_accept(priority=5):
            # Process request
        else:
            # Return 503
    """

    def __init__(
        self,
        name: str,
        config: Optional[BackPressureConfig] = None,
        on_level_change: Optional[Callable[[BackPressureLevel, BackPressureLevel], None]] = None,
    ):
        self.name = name
        self.config = config or BackPressureConfig()
        self._on_level_change = on_level_change

        self._metrics = BackPressureMetrics()
        self._level = BackPressureLevel.NONE
        self._level_changed_at = datetime.utcnow()

        # Compteurs en temps réel
        self._concurrent = 0
        self._queue_size = 0

        self._lock = threading.RLock()

        logger.info(f"[BACK_PRESSURE] {name} initialized")

    @property
    def level(self) -> BackPressureLevel:
        return self._level

    @property
    def metrics(self) -> BackPressureMetrics:
        return self._metrics

    def update_pressure(
        self,
        queue_size: Optional[int] = None,
        concurrent_requests: Optional[int] = None,
        memory_percent: Optional[float] = None,
    ) -> BackPressureLevel:
        """Met à jour les indicateurs de pression."""
        with self._lock:
            if queue_size is not None:
                self._queue_size = queue_size
                self._metrics.queue_size = queue_size

            if concurrent_requests is not None:
                self._concurrent = concurrent_requests
                self._metrics.concurrent_requests = concurrent_requests

            # Calculer pression globale
            pressures = []

            if self.config.max_queue_size > 0:
                pressures.append(self._queue_size / self.config.max_queue_size)

            if self.config.max_concurrent_requests > 0:
                pressures.append(self._concurrent / self.config.max_concurrent_requests)

            if memory_percent is not None:
                pressures.append(memory_percent / self.config.max_memory_percent)

            if pressures:
                self._metrics.current_pressure = max(pressures)
            else:
                self._metrics.current_pressure = 0.0

            # Déterminer niveau
            new_level = self._determine_level(self._metrics.current_pressure)
            if new_level != self._level:
                self._transition_level(new_level)

            return self._level

    def _determine_level(self, pressure: float) -> BackPressureLevel:
        """Détermine le niveau de back-pressure."""
        if pressure >= self.config.critical_threshold:
            return BackPressureLevel.CRITICAL
        elif pressure >= self.config.high_threshold:
            return BackPressureLevel.HIGH
        elif pressure >= self.config.medium_threshold:
            return BackPressureLevel.MEDIUM
        elif pressure >= self.config.low_threshold:
            return BackPressureLevel.LOW
        return BackPressureLevel.NONE

    def _transition_level(self, new_level: BackPressureLevel) -> None:
        """Transition de niveau."""
        old_level = self._level
        now = datetime.utcnow()

        # Calculer temps dans l'état précédent si haute pression
        if old_level in [BackPressureLevel.HIGH, BackPressureLevel.CRITICAL]:
            duration = (now - self._level_changed_at).total_seconds()
            self._metrics.time_in_high_pressure_seconds += duration

        self._level = new_level
        self._level_changed_at = now
        self._metrics.current_level = new_level
        self._metrics.level_changes += 1

        logger.warning(
            f"[BACK_PRESSURE] {self.name}: {old_level.value} -> {new_level.value}",
            extra={
                "controller": self.name,
                "old_level": old_level.value,
                "new_level": new_level.value,
                "pressure": self._metrics.current_pressure,
            }
        )

        if self._on_level_change:
            try:
                self._on_level_change(old_level, new_level)
            except Exception as e:
                logger.error(f"[BACK_PRESSURE] Level change callback error: {e}")

    def should_accept(self, priority: int = 5) -> bool:
        """
        Détermine si une requête doit être acceptée.

        Args:
            priority: Priorité de la requête (1=haute, 10=basse)

        Returns:
            True si la requête peut être traitée
        """
        with self._lock:
            if self._level == BackPressureLevel.NONE:
                return True

            elif self._level == BackPressureLevel.LOW:
                # Log seulement
                return True

            elif self._level == BackPressureLevel.MEDIUM:
                # Throttle basse priorité
                if priority > 7:
                    self._metrics.throttled_count += 1
                    return False
                return True

            elif self._level == BackPressureLevel.HIGH:
                # Rejeter basse priorité
                if priority > 5:
                    self._metrics.rejected_count += 1
                    return False
                return True

            elif self._level == BackPressureLevel.CRITICAL:
                # Accepter uniquement haute priorité
                if priority > 2:
                    self._metrics.rejected_count += 1
                    return False
                return True

            return True

    def increment_concurrent(self) -> int:
        """Incrémente le compteur de requêtes concurrentes."""
        with self._lock:
            self._concurrent += 1
            self._metrics.concurrent_requests = self._concurrent
            self.update_pressure()
            return self._concurrent

    def decrement_concurrent(self) -> int:
        """Décrémente le compteur de requêtes concurrentes."""
        with self._lock:
            self._concurrent = max(0, self._concurrent - 1)
            self._metrics.concurrent_requests = self._concurrent
            self.update_pressure()
            return self._concurrent

    def set_queue_size(self, size: int) -> None:
        """Met à jour la taille de la file."""
        with self._lock:
            self._queue_size = size
            self._metrics.queue_size = size
            self.update_pressure()

    def get_recommended_delay_ms(self) -> int:
        """Retourne un délai recommandé selon le niveau de pression."""
        delays = {
            BackPressureLevel.NONE: 0,
            BackPressureLevel.LOW: 10,
            BackPressureLevel.MEDIUM: 50,
            BackPressureLevel.HIGH: 200,
            BackPressureLevel.CRITICAL: 1000,
        }
        return delays.get(self._level, 0)


class Bulkhead:
    """
    Bulkhead Pattern - Isolation des ressources.

    Limite le nombre de requêtes concurrentes pour un pool de ressources,
    empêchant une défaillance de se propager.
    """

    def __init__(
        self,
        name: str,
        max_concurrent: int = 10,
        max_wait_ms: int = 5000,
    ):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_wait_ms = max_wait_ms

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._sync_semaphore = threading.Semaphore(max_concurrent)
        self._active = 0
        self._rejected = 0
        self._lock = threading.RLock()

        logger.info(f"[BULKHEAD] {name} initialized with max_concurrent={max_concurrent}")

    @property
    def active_count(self) -> int:
        return self._active

    @property
    def available(self) -> int:
        return self.max_concurrent - self._active

    @property
    def rejected_count(self) -> int:
        return self._rejected

    async def acquire(self) -> bool:
        """Acquiert un slot (async)."""
        try:
            acquired = await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.max_wait_ms / 1000,
            )
            if acquired:
                with self._lock:
                    self._active += 1
                return True
        except asyncio.TimeoutError:
            with self._lock:
                self._rejected += 1
            logger.warning(f"[BULKHEAD] {self.name} acquisition timeout")
            return False
        return False

    def release(self) -> None:
        """Libère un slot."""
        self._semaphore.release()
        with self._lock:
            self._active = max(0, self._active - 1)

    def acquire_sync(self) -> bool:
        """Acquiert un slot (sync)."""
        acquired = self._sync_semaphore.acquire(timeout=self.max_wait_ms / 1000)
        if acquired:
            with self._lock:
                self._active += 1
            return True
        else:
            with self._lock:
                self._rejected += 1
            return False

    def release_sync(self) -> None:
        """Libère un slot (sync)."""
        self._sync_semaphore.release()
        with self._lock:
            self._active = max(0, self._active - 1)

    def protect(self, func: Callable) -> Callable:
        """Décorateur pour protéger une fonction."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not await self.acquire():
                raise BulkheadFullError(f"Bulkhead {self.name} is full")
            try:
                return await func(*args, **kwargs)
            finally:
                self.release()

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self.acquire_sync():
                raise BulkheadFullError(f"Bulkhead {self.name} is full")
            try:
                return func(*args, **kwargs)
            finally:
                self.release_sync()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper


class BulkheadFullError(Exception):
    """Exception levée quand le bulkhead est plein."""
    pass


# Registry global des circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_back_pressure_controllers: Dict[str, BackPressure] = {}
_bulkheads: Dict[str, Bulkhead] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Récupère ou crée un circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def get_back_pressure(
    name: str,
    config: Optional[BackPressureConfig] = None,
) -> BackPressure:
    """Récupère ou crée un contrôleur de back-pressure."""
    if name not in _back_pressure_controllers:
        _back_pressure_controllers[name] = BackPressure(name, config)
    return _back_pressure_controllers[name]


def get_bulkhead(
    name: str,
    max_concurrent: int = 10,
    max_wait_ms: int = 5000,
) -> Bulkhead:
    """Récupère ou crée un bulkhead."""
    if name not in _bulkheads:
        _bulkheads[name] = Bulkhead(name, max_concurrent, max_wait_ms)
    return _bulkheads[name]


def get_resilience_status() -> Dict[str, Any]:
    """Retourne le statut de tous les composants de résilience."""
    return {
        "circuit_breakers": {
            name: {
                "state": cb.state.value,
                "metrics": cb.metrics.to_dict(),
            }
            for name, cb in _circuit_breakers.items()
        },
        "back_pressure": {
            name: bp.metrics.to_dict()
            for name, bp in _back_pressure_controllers.items()
        },
        "bulkheads": {
            name: {
                "active": bh.active_count,
                "available": bh.available,
                "rejected": bh.rejected_count,
            }
            for name, bh in _bulkheads.items()
        },
    }
