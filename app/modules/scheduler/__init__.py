"""
Module Planification de Tâches - GAP-049

Gestion des tâches planifiées:
- Jobs récurrents (cron)
- Tâches différées et immédiates
- Files d'attente prioritaires
- Retry avec backoff exponentiel
- Distributed locking
- Monitoring des workers
- Historique d'exécution
"""

from .service import (
    # Énumérations
    JobStatus,
    JobPriority,
    JobType,
    RetryStrategy,
    QueueType,

    # Data classes
    RetryConfig,
    JobDefinition,
    JobInstance,
    Queue,
    Worker,
    SchedulerLock,
    JobEvent,

    # Service
    SchedulerService,
    create_scheduler_service,
)

__all__ = [
    "JobStatus",
    "JobPriority",
    "JobType",
    "RetryStrategy",
    "QueueType",
    "RetryConfig",
    "JobDefinition",
    "JobInstance",
    "Queue",
    "Worker",
    "SchedulerLock",
    "JobEvent",
    "SchedulerService",
    "create_scheduler_service",
]
