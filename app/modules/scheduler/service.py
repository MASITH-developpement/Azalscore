"""
Service de Planification de Taches - GAP-049

Gestion des taches planifiees avec persistence SQLAlchemy:
- Jobs recurrents (cron)
- Taches differees
- Files d'attente prioritaires
- Retry avec backoff
- Monitoring et alertes
- Distributed locking
- Historique d'execution
- Dependances entre jobs

CRITIQUE: Utilise les repositories pour l'isolation multi-tenant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .models import (
    JobStatus,
    JobPriority,
    JobType,
    RetryStrategy,
    QueueType,
    JobDefinition,
    JobInstance,
    JobQueue,
    Worker,
    SchedulerLock,
    JobEvent,
)
from .repository import (
    JobDefinitionRepository,
    JobInstanceRepository,
    JobQueueRepository,
    WorkerRepository,
    LockRepository,
    EventRepository,
    SchedulerStatsRepository,
)


# ============================================================================
# DATA CLASSES (pour compatibilite API)
# ============================================================================

@dataclass
class RetryConfig:
    """Configuration des retries."""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 3
    initial_delay_seconds: int = 60
    max_delay_seconds: int = 3600
    multiplier: float = 2.0
    jitter: bool = True


@dataclass
class QueueStats:
    """Statistiques d'une file d'attente."""
    queue_name: str
    pending_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    avg_wait_time_seconds: float = 0
    avg_execution_time_seconds: float = 0


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class SchedulerService:
    """Service de planification de taches avec persistence SQLAlchemy."""

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        notification_service: Optional[Any] = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.notification = notification_service

        # Repositories avec isolation tenant
        self.definition_repo = JobDefinitionRepository(db, tenant_id)
        self.instance_repo = JobInstanceRepository(db, tenant_id)
        self.queue_repo = JobQueueRepository(db, tenant_id)
        self.worker_repo = WorkerRepository(db, tenant_id)
        self.lock_repo = LockRepository(db, tenant_id)
        self.event_repo = EventRepository(db, tenant_id)
        self.stats_repo = SchedulerStatsRepository(db, tenant_id)

        # Handlers enregistres
        self._handlers: Dict[str, Callable] = {}

        # Initialiser les queues par defaut
        self._init_default_queues()

    def _init_default_queues(self):
        """Initialise les queues par defaut."""
        for qt in QueueType:
            name = qt.value
            existing = self.queue_repo.get_by_name(name)
            if not existing:
                self.queue_repo.create(
                    name=name,
                    queue_type=qt,
                    max_concurrent=self._get_queue_concurrency(qt)
                )

    def _get_queue_concurrency(self, queue_type: QueueType) -> int:
        """Retourne la concurrence par defaut d'une queue."""
        concurrency = {
            QueueType.REALTIME: 20,
            QueueType.HIGH_PRIORITY: 15,
            QueueType.DEFAULT: 10,
            QueueType.BACKGROUND: 5,
            QueueType.BATCH: 3
        }
        return concurrency.get(queue_type, 10)

    # ========================================================================
    # HANDLERS
    # ========================================================================

    def register_handler(self, handler_name: str, handler_func: Callable) -> None:
        """Enregistre un handler de job."""
        self._handlers[handler_name] = handler_func

    def get_handler(self, handler_name: str) -> Optional[Callable]:
        """Recupere un handler."""
        return self._handlers.get(handler_name)

    # ========================================================================
    # DEFINITIONS DE JOBS
    # ========================================================================

    def create_job_definition(
        self,
        name: str,
        handler: str,
        job_type: JobType = JobType.IMMEDIATE,
        description: Optional[str] = None,
        cron_expression: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        delay_seconds: Optional[int] = None,
        queue: QueueType = QueueType.DEFAULT,
        priority: JobPriority = JobPriority.NORMAL,
        timeout_seconds: int = 300,
        retry_config: Optional[RetryConfig] = None,
        default_params: Optional[Dict[str, Any]] = None,
        max_concurrent: int = 1,
        singleton: bool = False,
        unique_key: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        run_window_start: Optional[str] = None,
        run_window_end: Optional[str] = None,
        run_on_days: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> JobDefinition:
        """Cree une definition de job."""
        retry = retry_config or RetryConfig()

        return self.definition_repo.create(
            name=name,
            handler=handler,
            job_type=job_type,
            description=description,
            cron_expression=cron_expression,
            scheduled_at=scheduled_at,
            delay_seconds=delay_seconds,
            queue=queue,
            priority=priority,
            timeout_seconds=timeout_seconds,
            retry_strategy=retry.strategy,
            max_retries=retry.max_retries,
            initial_delay_seconds=retry.initial_delay_seconds,
            max_delay_seconds=retry.max_delay_seconds,
            retry_multiplier=retry.multiplier,
            default_params=default_params,
            max_concurrent=max_concurrent,
            singleton=singleton,
            unique_key=unique_key,
            depends_on=depends_on,
            run_window_start=run_window_start,
            run_window_end=run_window_end,
            run_on_days=run_on_days,
            tags=tags,
            created_by=created_by
        )

    def get_job_definition(self, job_def_id: str) -> Optional[JobDefinition]:
        """Recupere une definition de job."""
        return self.definition_repo.get_by_id(job_def_id)

    def get_job_definition_by_name(self, name: str) -> Optional[JobDefinition]:
        """Recupere une definition par nom."""
        return self.definition_repo.get_by_name(name)

    def list_job_definitions(self, active_only: bool = True) -> List[JobDefinition]:
        """Liste les definitions de job."""
        return self.definition_repo.list_all(active_only)

    def update_job_definition(self, job_def_id: str, **updates) -> Optional[JobDefinition]:
        """Met a jour une definition."""
        return self.definition_repo.update(job_def_id, **updates)

    def pause_job_definition(self, job_def_id: str) -> Optional[JobDefinition]:
        """Met en pause une definition."""
        return self.definition_repo.pause(job_def_id)

    def resume_job_definition(self, job_def_id: str) -> Optional[JobDefinition]:
        """Reprend une definition."""
        return self.definition_repo.resume(job_def_id)

    def delete_job_definition(self, job_def_id: str) -> bool:
        """Supprime une definition."""
        return self.definition_repo.delete(job_def_id)

    # ========================================================================
    # INSTANCES DE JOBS
    # ========================================================================

    def enqueue_job(
        self,
        job_def_id: str,
        params: Optional[Dict[str, Any]] = None,
        priority: Optional[JobPriority] = None,
        scheduled_at: Optional[datetime] = None,
        unique_key: Optional[str] = None
    ) -> JobInstance:
        """Ajoute un job a la file d'attente."""
        job_def = self.definition_repo.get_by_id(job_def_id)
        if not job_def:
            raise ValueError(f"Definition {job_def_id} non trouvee")

        if not job_def.is_active:
            raise ValueError(f"Definition {job_def_id} inactive")

        # Verifier singleton
        if job_def.singleton:
            running = self.instance_repo.count_running_for_definition(job_def_id)
            if running > 0:
                raise ValueError(f"Job singleton {job_def.name} deja en cours")

        # Verifier concurrence max
        if job_def.max_concurrent > 0:
            running = self.instance_repo.count_running_for_definition(job_def_id)
            if running >= job_def.max_concurrent:
                raise ValueError(f"Max concurrent ({job_def.max_concurrent}) atteint")

        # Verifier deduplication
        if unique_key or job_def.unique_key:
            key = unique_key or job_def.unique_key
            existing = self.instance_repo.get_by_unique_key(key)
            if existing and existing.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                raise ValueError(f"Job avec cle {key} deja en cours")

        # Fusionner les params
        merged_params = {**(job_def.default_params or {}), **(params or {})}

        return self.instance_repo.create(
            job_def_id=job_def_id,
            job_name=job_def.name,
            handler=job_def.handler,
            params=merged_params,
            queue=job_def.queue,
            priority=priority or job_def.priority,
            scheduled_at=scheduled_at,
            timeout_seconds=job_def.timeout_seconds,
            unique_key=unique_key or job_def.unique_key
        )

    def get_job_instance(self, instance_id: str) -> Optional[JobInstance]:
        """Recupere une instance de job."""
        return self.instance_repo.get_by_id(instance_id)

    def list_job_instances(
        self,
        job_def_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        queue: Optional[QueueType] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[JobInstance], int]:
        """Liste les instances de job."""
        return self.instance_repo.list(
            job_def_id=job_def_id,
            status=status,
            queue=queue,
            page=page,
            page_size=page_size
        )

    def cancel_job(self, instance_id: str, reason: Optional[str] = None) -> Optional[JobInstance]:
        """Annule un job."""
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance:
            return None

        if instance.status not in [JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.QUEUED]:
            raise ValueError(f"Impossible d'annuler un job en statut {instance.status}")

        return self.instance_repo.cancel(instance_id, reason)

    def retry_job(self, instance_id: str) -> Optional[JobInstance]:
        """Relance un job echoue."""
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance:
            return None

        if instance.status != JobStatus.FAILED:
            raise ValueError("Seuls les jobs echoues peuvent etre relances")

        return self.instance_repo.retry(instance_id)

    # ========================================================================
    # EXECUTION
    # ========================================================================

    def poll_next_job(
        self,
        worker_id: str,
        queues: Optional[List[QueueType]] = None
    ) -> Optional[JobInstance]:
        """Recupere le prochain job a executer pour un worker."""
        # Verifier le worker
        worker = self.worker_repo.get_by_id(worker_id)
        if not worker or not worker.is_active:
            return None

        # Obtenir le prochain job
        return self.instance_repo.poll_next(worker_id, queues)

    def start_job(self, instance_id: str, worker_id: str) -> Optional[JobInstance]:
        """Demarre l'execution d'un job."""
        # Acquerir un lock
        lock_key = f"job_{instance_id}"
        if not self.lock_repo.acquire(lock_key, worker_id, ttl_seconds=300):
            return None

        instance = self.instance_repo.start(instance_id, worker_id)
        if instance:
            self.event_repo.create(
                instance_id=instance_id,
                event_type="started",
                details={"worker_id": worker_id}
            )

        return instance

    def complete_job(
        self,
        instance_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[JobInstance]:
        """Marque un job comme termine."""
        instance = self.instance_repo.complete(instance_id, result)
        if instance:
            self.event_repo.create(
                instance_id=instance_id,
                event_type="completed",
                details={"result": result}
            )

            # Mettre a jour last_run sur la definition
            self.definition_repo.update_last_run(str(instance.job_def_id))

            # Liberer le lock
            self.lock_repo.release(f"job_{instance_id}")

        return instance

    def fail_job(
        self,
        instance_id: str,
        error: str,
        should_retry: bool = True
    ) -> Optional[JobInstance]:
        """Marque un job comme echoue."""
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance:
            return None

        job_def = self.definition_repo.get_by_id(str(instance.job_def_id))

        # Determiner si retry
        can_retry = (
            should_retry and
            job_def and
            instance.attempt < job_def.max_retries
        )

        if can_retry:
            instance = self.instance_repo.schedule_retry(instance_id, error)
            self.event_repo.create(
                instance_id=instance_id,
                event_type="retry_scheduled",
                details={"error": error, "attempt": instance.attempt if instance else 0}
            )
        else:
            instance = self.instance_repo.fail(instance_id, error)
            self.event_repo.create(
                instance_id=instance_id,
                event_type="failed",
                details={"error": error}
            )

            # Notification si configure
            if self.notification:
                self.notification.send_job_failure_alert(instance)

        # Liberer le lock
        self.lock_repo.release(f"job_{instance_id}")

        return instance

    def execute_job(self, instance_id: str, worker_id: str) -> Dict[str, Any]:
        """Execute un job (pour utilisation directe)."""
        instance = self.start_job(instance_id, worker_id)
        if not instance:
            return {"success": False, "error": "Job non disponible"}

        handler = self.get_handler(instance.handler)
        if not handler:
            self.fail_job(instance_id, f"Handler {instance.handler} non trouve", should_retry=False)
            return {"success": False, "error": f"Handler {instance.handler} non trouve"}

        try:
            result = handler(instance.params)
            self.complete_job(instance_id, result)
            return {"success": True, "result": result}
        except Exception as e:
            self.fail_job(instance_id, str(e))
            return {"success": False, "error": str(e)}

    # ========================================================================
    # WORKERS
    # ========================================================================

    def register_worker(
        self,
        hostname: str,
        queues: Optional[List[QueueType]] = None,
        max_concurrent: int = 5
    ) -> Worker:
        """Enregistre un worker."""
        return self.worker_repo.create(
            hostname=hostname,
            queues=queues,
            max_concurrent=max_concurrent
        )

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """Recupere un worker."""
        return self.worker_repo.get_by_id(worker_id)

    def list_workers(self, active_only: bool = True) -> List[Worker]:
        """Liste les workers."""
        return self.worker_repo.list_all(active_only)

    def heartbeat_worker(self, worker_id: str) -> Optional[Worker]:
        """Met a jour le heartbeat d'un worker."""
        return self.worker_repo.heartbeat(worker_id)

    def deactivate_worker(self, worker_id: str) -> Optional[Worker]:
        """Desactive un worker."""
        return self.worker_repo.deactivate(worker_id)

    # ========================================================================
    # LOCKS
    # ========================================================================

    def acquire_lock(
        self,
        lock_key: str,
        owner_id: str,
        ttl_seconds: int = 300
    ) -> bool:
        """Acquiert un lock distribue."""
        return self.lock_repo.acquire(lock_key, owner_id, ttl_seconds)

    def release_lock(self, lock_key: str, owner_id: Optional[str] = None) -> bool:
        """Libere un lock."""
        return self.lock_repo.release(lock_key, owner_id)

    def refresh_lock(self, lock_key: str, owner_id: str, ttl_seconds: int = 300) -> bool:
        """Rafraichit le TTL d'un lock."""
        return self.lock_repo.refresh(lock_key, owner_id, ttl_seconds)

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_queue_stats(self, queue_name: Optional[str] = None) -> List[QueueStats]:
        """Recupere les statistiques des queues."""
        stats_list = self.stats_repo.get_queue_stats(queue_name)
        return [
            QueueStats(
                queue_name=s["queue_name"],
                pending_jobs=s.get("pending_jobs", 0),
                running_jobs=s.get("running_jobs", 0),
                completed_jobs=s.get("completed_jobs", 0),
                failed_jobs=s.get("failed_jobs", 0),
                avg_wait_time_seconds=s.get("avg_wait_time_seconds", 0),
                avg_execution_time_seconds=s.get("avg_execution_time_seconds", 0)
            )
            for s in stats_list
        ]

    def get_job_statistics(
        self,
        job_def_id: Optional[str] = None,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """Recupere les statistiques des jobs."""
        return self.stats_repo.get_job_stats(job_def_id, period_days)

    # ========================================================================
    # MAINTENANCE
    # ========================================================================

    def process_scheduled_jobs(self) -> List[JobInstance]:
        """Traite les jobs planifies a executer."""
        definitions = self.definition_repo.list_scheduled()
        instances = []

        for job_def in definitions:
            try:
                instance = self.enqueue_job(str(job_def.id))
                instances.append(instance)
                self.definition_repo.update_last_run(str(job_def.id))
            except ValueError:
                # Job deja en cours ou limite atteinte
                continue

        return instances

    def cleanup_stale_jobs(self, timeout_hours: int = 24) -> int:
        """Nettoie les jobs bloques."""
        return self.instance_repo.cleanup_stale(timeout_hours)

    def cleanup_old_events(self, retention_days: int = 30) -> int:
        """Nettoie les anciens evenements."""
        return self.event_repo.cleanup_old(retention_days)


# ============================================================================
# FACTORY
# ============================================================================

def create_scheduler_service(
    db: Session,
    tenant_id: str,
    notification_service: Optional[Any] = None
) -> SchedulerService:
    """Cree un service de planification."""
    return SchedulerService(
        db=db,
        tenant_id=tenant_id,
        notification_service=notification_service
    )
