"""
Service de Planification de Tâches - GAP-049

Gestion des tâches planifiées:
- Jobs récurrents (cron)
- Tâches différées
- Files d'attente prioritaires
- Retry avec backoff
- Monitoring et alertes
- Distributed locking
- Historique d'exécution
- Dépendances entre jobs
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4
import json
import hashlib
import time


class JobStatus(Enum):
    """Statut d'un job."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"


class JobPriority(Enum):
    """Priorité d'un job."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class JobType(Enum):
    """Type de job."""
    IMMEDIATE = "immediate"  # Exécution immédiate
    SCHEDULED = "scheduled"  # Date/heure précise
    RECURRING = "recurring"  # Cron
    DELAYED = "delayed"  # Après un délai


class RetryStrategy(Enum):
    """Stratégie de retry."""
    NONE = "none"
    FIXED = "fixed"  # Délai fixe
    EXPONENTIAL = "exponential"  # Backoff exponentiel
    LINEAR = "linear"  # Augmentation linéaire


class QueueType(Enum):
    """Type de file d'attente."""
    DEFAULT = "default"
    HIGH_PRIORITY = "high_priority"
    BACKGROUND = "background"
    REALTIME = "realtime"
    BATCH = "batch"


@dataclass
class RetryConfig:
    """Configuration des retries."""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 3
    initial_delay_seconds: int = 60
    max_delay_seconds: int = 3600
    multiplier: float = 2.0
    jitter: bool = True  # Ajouter du jitter aléatoire


@dataclass
class JobDefinition:
    """Définition d'un job."""
    job_def_id: str
    tenant_id: str
    name: str
    description: str
    job_type: JobType
    handler: str  # Nom du handler à exécuter

    # Planification
    cron_expression: Optional[str] = None  # Pour RECURRING
    scheduled_at: Optional[datetime] = None  # Pour SCHEDULED
    delay_seconds: Optional[int] = None  # Pour DELAYED

    # Configuration
    queue: QueueType = QueueType.DEFAULT
    priority: JobPriority = JobPriority.NORMAL
    timeout_seconds: int = 300
    retry_config: RetryConfig = field(default_factory=RetryConfig)

    # Paramètres par défaut
    default_params: Dict[str, Any] = field(default_factory=dict)

    # Contraintes
    max_concurrent: int = 1  # Max instances simultanées
    singleton: bool = False  # Une seule instance à la fois
    unique_key: Optional[str] = None  # Clé de déduplication

    # Dépendances
    depends_on: List[str] = field(default_factory=list)  # Job IDs
    blocks: List[str] = field(default_factory=list)  # Jobs bloqués par celui-ci

    # Fenêtre d'exécution
    run_window_start: Optional[str] = None  # "08:00"
    run_window_end: Optional[str] = None  # "22:00"
    run_on_days: List[int] = field(default_factory=list)  # 0=lundi, 6=dimanche

    # État
    is_active: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class JobInstance:
    """Instance d'exécution d'un job."""
    instance_id: str
    tenant_id: str
    job_def_id: str
    job_name: str
    handler: str
    status: JobStatus

    # Paramètres
    params: Dict[str, Any] = field(default_factory=dict)

    # File d'attente
    queue: QueueType = QueueType.DEFAULT
    priority: JobPriority = JobPriority.NORMAL

    # Planification
    scheduled_at: Optional[datetime] = None
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Retry
    attempt: int = 1
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    retry_history: List[Dict[str, Any]] = field(default_factory=list)

    # Résultat
    result: Optional[Any] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # Métriques
    duration_ms: Optional[int] = None
    memory_used_mb: Optional[float] = None
    cpu_percent: Optional[float] = None

    # Worker
    worker_id: Optional[str] = None
    locked_at: Optional[datetime] = None
    lock_token: Optional[str] = None

    # Timeout
    timeout_seconds: int = 300
    timeout_at: Optional[datetime] = None

    # Progression
    progress_percent: int = 0
    progress_message: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    unique_key: Optional[str] = None
    parent_instance_id: Optional[str] = None  # Pour les sous-jobs


@dataclass
class Queue:
    """File d'attente de jobs."""
    queue_id: str
    tenant_id: str
    name: str
    queue_type: QueueType

    # Configuration
    max_concurrent: int = 10
    rate_limit_per_minute: Optional[int] = None

    # État
    is_paused: bool = False
    pending_count: int = 0
    running_count: int = 0

    # Statistiques
    processed_count: int = 0
    failed_count: int = 0
    avg_duration_ms: float = 0


@dataclass
class Worker:
    """Worker d'exécution."""
    worker_id: str
    tenant_id: str
    name: str
    queues: List[QueueType]

    # État
    is_active: bool = True
    is_busy: bool = False
    current_job_id: Optional[str] = None

    # Heartbeat
    last_heartbeat: datetime = field(default_factory=datetime.now)
    started_at: datetime = field(default_factory=datetime.now)

    # Stats
    jobs_processed: int = 0
    jobs_failed: int = 0

    # Ressources
    hostname: Optional[str] = None
    pid: Optional[int] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None


@dataclass
class SchedulerLock:
    """Verrou distribué."""
    lock_id: str
    resource_id: str
    owner_id: str
    acquired_at: datetime
    expires_at: datetime
    token: str


@dataclass
class JobEvent:
    """Événement de job."""
    event_id: str
    instance_id: str
    event_type: str  # queued, started, completed, failed, retrying, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


class SchedulerService:
    """Service de planification de tâches."""

    def __init__(
        self,
        tenant_id: str,
        job_repository: Optional[Any] = None,
        queue_backend: Optional[Any] = None,
        lock_backend: Optional[Any] = None,
        notification_service: Optional[Any] = None
    ):
        self.tenant_id = tenant_id
        self.job_repo = job_repository or {}
        self.queue_backend = queue_backend
        self.lock_backend = lock_backend
        self.notification = notification_service

        # Caches
        self._definitions: Dict[str, JobDefinition] = {}
        self._instances: Dict[str, JobInstance] = {}
        self._queues: Dict[str, Queue] = {}
        self._workers: Dict[str, Worker] = {}
        self._locks: Dict[str, SchedulerLock] = {}
        self._events: List[JobEvent] = []

        # Handlers enregistrés
        self._handlers: Dict[str, Callable] = {}

        # Initialiser les queues par défaut
        self._init_default_queues()

    def _init_default_queues(self):
        """Initialise les queues par défaut."""
        for qt in QueueType:
            queue_id = f"queue_{self.tenant_id}_{qt.value}"
            self._queues[queue_id] = Queue(
                queue_id=queue_id,
                tenant_id=self.tenant_id,
                name=qt.value,
                queue_type=qt,
                max_concurrent=self._get_queue_concurrency(qt)
            )

    def _get_queue_concurrency(self, queue_type: QueueType) -> int:
        """Retourne la concurrence par défaut d'une queue."""
        concurrency = {
            QueueType.REALTIME: 20,
            QueueType.HIGH_PRIORITY: 15,
            QueueType.DEFAULT: 10,
            QueueType.BACKGROUND: 5,
            QueueType.BATCH: 3
        }
        return concurrency.get(queue_type, 10)

    # =========================================================================
    # Définition des Jobs
    # =========================================================================

    def create_job_definition(
        self,
        name: str,
        handler: str,
        job_type: JobType,
        **kwargs
    ) -> JobDefinition:
        """Crée une définition de job."""
        job_def_id = f"jobdef_{uuid4().hex[:12]}"

        # Construire la config de retry
        retry_data = kwargs.get("retry_config", {})
        retry_config = RetryConfig(
            strategy=RetryStrategy(retry_data.get("strategy", "exponential")),
            max_retries=retry_data.get("max_retries", 3),
            initial_delay_seconds=retry_data.get("initial_delay", 60),
            max_delay_seconds=retry_data.get("max_delay", 3600),
            multiplier=retry_data.get("multiplier", 2.0)
        )

        definition = JobDefinition(
            job_def_id=job_def_id,
            tenant_id=self.tenant_id,
            name=name,
            description=kwargs.get("description", ""),
            job_type=job_type,
            handler=handler,
            cron_expression=kwargs.get("cron_expression"),
            scheduled_at=kwargs.get("scheduled_at"),
            delay_seconds=kwargs.get("delay_seconds"),
            queue=QueueType(kwargs.get("queue", "default")),
            priority=JobPriority(kwargs.get("priority", 5)),
            timeout_seconds=kwargs.get("timeout_seconds", 300),
            retry_config=retry_config,
            default_params=kwargs.get("default_params", {}),
            max_concurrent=kwargs.get("max_concurrent", 1),
            singleton=kwargs.get("singleton", False),
            unique_key=kwargs.get("unique_key"),
            depends_on=kwargs.get("depends_on", []),
            run_window_start=kwargs.get("run_window_start"),
            run_window_end=kwargs.get("run_window_end"),
            run_on_days=kwargs.get("run_on_days", []),
            created_by=kwargs.get("created_by", "system"),
            tags=kwargs.get("tags", [])
        )

        # Calculer la prochaine exécution pour les jobs récurrents
        if job_type == JobType.RECURRING and definition.cron_expression:
            definition.next_run_at = self._calculate_next_run(definition.cron_expression)

        self._definitions[job_def_id] = definition
        return definition

    def register_handler(self, name: str, handler: Callable):
        """Enregistre un handler de job."""
        self._handlers[name] = handler

    def _calculate_next_run(self, cron: str) -> datetime:
        """Calcule la prochaine exécution d'un cron."""
        # Implémentation simplifiée - utiliser croniter en production
        # Format: minute hour day_of_month month day_of_week
        parts = cron.split()
        if len(parts) != 5:
            return datetime.now() + timedelta(hours=1)

        now = datetime.now()

        # Parser l'heure et minute
        minute = int(parts[0]) if parts[0] != "*" else now.minute
        hour = int(parts[1]) if parts[1] != "*" else now.hour

        next_run = now.replace(minute=minute, second=0, microsecond=0)
        if parts[1] != "*":
            next_run = next_run.replace(hour=hour)

        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    # =========================================================================
    # Création et Soumission de Jobs
    # =========================================================================

    def submit_job(
        self,
        job_def_id: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> JobInstance:
        """Soumet un job pour exécution."""
        definition = self._definitions.get(job_def_id)
        if not definition:
            raise ValueError(f"Définition {job_def_id} non trouvée")

        if not definition.is_active:
            raise ValueError(f"Job {definition.name} est désactivé")

        # Vérifier les contraintes
        if definition.singleton:
            running = self._get_running_instances(job_def_id)
            if running:
                raise ValueError(f"Job singleton déjà en cours: {running[0].instance_id}")

        # Vérifier la déduplication
        unique_key = kwargs.get("unique_key") or definition.unique_key
        if unique_key:
            key_hash = self._compute_unique_key(unique_key, params)
            existing = self._find_by_unique_key(key_hash)
            if existing:
                return existing

        instance_id = f"job_{uuid4().hex[:12]}"

        instance = JobInstance(
            instance_id=instance_id,
            tenant_id=self.tenant_id,
            job_def_id=job_def_id,
            job_name=definition.name,
            handler=definition.handler,
            status=JobStatus.PENDING,
            params={**definition.default_params, **(params or {})},
            queue=definition.queue,
            priority=kwargs.get("priority", definition.priority),
            max_retries=definition.retry_config.max_retries,
            timeout_seconds=definition.timeout_seconds,
            created_by=kwargs.get("created_by", "system"),
            unique_key=self._compute_unique_key(unique_key, params) if unique_key else None,
            parent_instance_id=kwargs.get("parent_instance_id")
        )

        # Planification selon le type
        if definition.job_type == JobType.IMMEDIATE:
            instance.scheduled_at = datetime.now()
        elif definition.job_type == JobType.SCHEDULED:
            instance.scheduled_at = kwargs.get("scheduled_at") or definition.scheduled_at
        elif definition.job_type == JobType.DELAYED:
            delay = kwargs.get("delay_seconds") or definition.delay_seconds or 0
            instance.scheduled_at = datetime.now() + timedelta(seconds=delay)

        self._instances[instance_id] = instance

        # Événement
        self._add_event(instance_id, "created", {"params": params})

        # Vérifier les dépendances
        if definition.depends_on:
            pending_deps = self._check_dependencies(definition.depends_on)
            if pending_deps:
                instance.status = JobStatus.PENDING
                self._add_event(instance_id, "waiting_dependencies", {"deps": pending_deps})
                return instance

        # Enfiler
        self._enqueue(instance)

        return instance

    def _compute_unique_key(
        self,
        key_template: str,
        params: Optional[Dict[str, Any]]
    ) -> str:
        """Calcule une clé unique."""
        if not params:
            return hashlib.md5(key_template.encode()).hexdigest()

        key_data = key_template
        for k, v in sorted(params.items()):
            key_data += f":{k}={v}"

        return hashlib.md5(key_data.encode()).hexdigest()

    def _find_by_unique_key(self, key: str) -> Optional[JobInstance]:
        """Trouve un job par clé unique."""
        for instance in self._instances.values():
            if instance.unique_key == key and instance.status in (
                JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING
            ):
                return instance
        return None

    def _get_running_instances(self, job_def_id: str) -> List[JobInstance]:
        """Récupère les instances en cours d'un job."""
        return [
            i for i in self._instances.values()
            if i.job_def_id == job_def_id and i.status in (
                JobStatus.QUEUED, JobStatus.RUNNING
            )
        ]

    def _check_dependencies(self, dep_ids: List[str]) -> List[str]:
        """Vérifie les dépendances d'un job."""
        pending = []
        for dep_id in dep_ids:
            dep = self._definitions.get(dep_id)
            if dep and dep.last_run_at is None:
                pending.append(dep_id)
        return pending

    def _enqueue(self, instance: JobInstance):
        """Ajoute un job à la file d'attente."""
        # Vérifier la fenêtre d'exécution
        if not self._is_in_run_window(instance):
            instance.status = JobStatus.SCHEDULED
            return

        instance.status = JobStatus.QUEUED
        instance.queued_at = datetime.now()

        # Mettre à jour les stats de la queue
        queue = self._get_queue(instance.queue)
        if queue:
            queue.pending_count += 1

        self._add_event(instance.instance_id, "queued", {})

    def _is_in_run_window(self, instance: JobInstance) -> bool:
        """Vérifie si on est dans la fenêtre d'exécution."""
        definition = self._definitions.get(instance.job_def_id)
        if not definition:
            return True

        now = datetime.now()

        # Vérifier les jours
        if definition.run_on_days:
            if now.weekday() not in definition.run_on_days:
                return False

        # Vérifier l'heure
        if definition.run_window_start and definition.run_window_end:
            current_time = now.strftime("%H:%M")
            if not (definition.run_window_start <= current_time <= definition.run_window_end):
                return False

        return True

    def _get_queue(self, queue_type: QueueType) -> Optional[Queue]:
        """Récupère une queue."""
        queue_id = f"queue_{self.tenant_id}_{queue_type.value}"
        return self._queues.get(queue_id)

    # =========================================================================
    # Exécution des Jobs
    # =========================================================================

    def acquire_job(
        self,
        worker_id: str,
        queues: Optional[List[QueueType]] = None
    ) -> Optional[JobInstance]:
        """Acquiert un job pour exécution par un worker."""
        queues = queues or [QueueType.DEFAULT]

        # Trier par priorité
        candidates = []
        for instance in self._instances.values():
            if instance.tenant_id != self.tenant_id:
                continue
            if instance.status != JobStatus.QUEUED:
                continue
            if instance.queue not in queues:
                continue
            if instance.scheduled_at and instance.scheduled_at > datetime.now():
                continue

            candidates.append(instance)

        if not candidates:
            return None

        # Trier par priorité puis par date de queue
        candidates.sort(key=lambda x: (-x.priority.value, x.queued_at or datetime.now()))

        for instance in candidates:
            # Tenter d'acquérir un lock
            lock = self._acquire_lock(instance.instance_id, worker_id)
            if lock:
                instance.status = JobStatus.RUNNING
                instance.started_at = datetime.now()
                instance.worker_id = worker_id
                instance.lock_token = lock.token
                instance.timeout_at = datetime.now() + timedelta(seconds=instance.timeout_seconds)

                # Mettre à jour les stats
                queue = self._get_queue(instance.queue)
                if queue:
                    queue.pending_count -= 1
                    queue.running_count += 1

                self._add_event(instance.instance_id, "started", {"worker_id": worker_id})

                return instance

        return None

    def _acquire_lock(self, resource_id: str, owner_id: str) -> Optional[SchedulerLock]:
        """Acquiert un verrou distribué."""
        lock_id = f"lock_{resource_id}"

        # Vérifier si un lock existe et est expiré
        existing = self._locks.get(lock_id)
        if existing:
            if existing.expires_at > datetime.now():
                return None
            # Lock expiré, on peut le reprendre

        token = uuid4().hex
        lock = SchedulerLock(
            lock_id=lock_id,
            resource_id=resource_id,
            owner_id=owner_id,
            acquired_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=5),
            token=token
        )

        self._locks[lock_id] = lock
        return lock

    def _release_lock(self, resource_id: str, token: str) -> bool:
        """Libère un verrou."""
        lock_id = f"lock_{resource_id}"
        lock = self._locks.get(lock_id)

        if lock and lock.token == token:
            del self._locks[lock_id]
            return True

        return False

    def execute_job(self, instance_id: str) -> JobInstance:
        """Exécute un job (appelé par le worker)."""
        instance = self._instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} non trouvée")

        handler = self._handlers.get(instance.handler)
        if not handler:
            instance.status = JobStatus.FAILED
            instance.error_message = f"Handler '{instance.handler}' non trouvé"
            return instance

        start_time = time.time()

        try:
            # Exécuter le handler
            result = handler(instance.params, self._create_job_context(instance))

            # Succès
            instance.status = JobStatus.COMPLETED
            instance.result = result
            instance.completed_at = datetime.now()
            instance.duration_ms = int((time.time() - start_time) * 1000)
            instance.progress_percent = 100

            self._add_event(instance.instance_id, "completed", {
                "duration_ms": instance.duration_ms,
                "result": str(result)[:500]
            })

            # Mettre à jour la définition
            definition = self._definitions.get(instance.job_def_id)
            if definition:
                definition.last_run_at = datetime.now()
                if definition.job_type == JobType.RECURRING:
                    definition.next_run_at = self._calculate_next_run(definition.cron_expression)

        except Exception as e:
            instance.error_message = str(e)
            instance.duration_ms = int((time.time() - start_time) * 1000)

            # Retry ?
            if instance.attempt < instance.max_retries:
                self._schedule_retry(instance)
            else:
                instance.status = JobStatus.FAILED
                instance.completed_at = datetime.now()

                self._add_event(instance.instance_id, "failed", {
                    "error": str(e),
                    "attempts": instance.attempt
                })

                # Notification d'échec
                if self.notification:
                    self.notification.send(
                        "job_failed",
                        variables={
                            "job_name": instance.job_name,
                            "error": str(e),
                            "attempts": instance.attempt
                        }
                    )

        finally:
            # Libérer le lock
            if instance.lock_token:
                self._release_lock(instance.instance_id, instance.lock_token)

            # Mettre à jour les stats de queue
            queue = self._get_queue(instance.queue)
            if queue:
                queue.running_count -= 1
                queue.processed_count += 1
                if instance.status == JobStatus.FAILED:
                    queue.failed_count += 1

        return instance

    def _create_job_context(self, instance: JobInstance) -> Dict[str, Any]:
        """Crée le contexte d'exécution d'un job."""
        return {
            "instance_id": instance.instance_id,
            "job_name": instance.job_name,
            "tenant_id": instance.tenant_id,
            "attempt": instance.attempt,
            "update_progress": lambda pct, msg=None: self._update_progress(instance, pct, msg)
        }

    def _update_progress(self, instance: JobInstance, percent: int, message: Optional[str]):
        """Met à jour la progression d'un job."""
        instance.progress_percent = min(percent, 100)
        instance.progress_message = message

    def _schedule_retry(self, instance: JobInstance):
        """Planifie un retry."""
        instance.status = JobStatus.RETRYING
        instance.attempt += 1

        definition = self._definitions.get(instance.job_def_id)
        config = definition.retry_config if definition else RetryConfig()

        # Calculer le délai
        if config.strategy == RetryStrategy.FIXED:
            delay = config.initial_delay_seconds
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.initial_delay_seconds * (config.multiplier ** (instance.attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.initial_delay_seconds * instance.attempt
        else:
            delay = config.initial_delay_seconds

        delay = min(delay, config.max_delay_seconds)

        # Ajouter du jitter (±10%)
        if config.jitter:
            import random
            jitter = delay * 0.1 * (random.random() * 2 - 1)
            delay += jitter

        instance.next_retry_at = datetime.now() + timedelta(seconds=delay)
        instance.retry_history.append({
            "attempt": instance.attempt - 1,
            "error": instance.error_message,
            "timestamp": datetime.now().isoformat()
        })

        self._add_event(instance.instance_id, "retrying", {
            "attempt": instance.attempt,
            "next_retry_at": instance.next_retry_at.isoformat(),
            "delay_seconds": delay
        })

    # =========================================================================
    # Gestion des Jobs Récurrents
    # =========================================================================

    def process_scheduled_jobs(self) -> List[JobInstance]:
        """Traite les jobs planifiés (appelé par le scheduler)."""
        created = []
        now = datetime.now()

        for definition in self._definitions.values():
            if not definition.is_active:
                continue
            if definition.tenant_id != self.tenant_id:
                continue
            if definition.job_type != JobType.RECURRING:
                continue
            if not definition.next_run_at:
                continue
            if definition.next_run_at > now:
                continue

            # Vérifier si pas déjà en cours
            if definition.singleton:
                running = self._get_running_instances(definition.job_def_id)
                if running:
                    continue

            # Créer une instance
            try:
                instance = self.submit_job(definition.job_def_id)
                created.append(instance)
            except Exception:
                pass

        return created

    def process_retries(self) -> List[JobInstance]:
        """Traite les jobs en attente de retry."""
        now = datetime.now()
        retried = []

        for instance in self._instances.values():
            if instance.status != JobStatus.RETRYING:
                continue
            if not instance.next_retry_at:
                continue
            if instance.next_retry_at > now:
                continue

            # Remettre en queue
            instance.status = JobStatus.QUEUED
            instance.queued_at = datetime.now()
            instance.next_retry_at = None

            retried.append(instance)

        return retried

    # =========================================================================
    # Gestion des Workers
    # =========================================================================

    def register_worker(
        self,
        name: str,
        queues: List[QueueType],
        **kwargs
    ) -> Worker:
        """Enregistre un worker."""
        worker_id = f"worker_{uuid4().hex[:8]}"

        worker = Worker(
            worker_id=worker_id,
            tenant_id=self.tenant_id,
            name=name,
            queues=queues,
            hostname=kwargs.get("hostname"),
            pid=kwargs.get("pid")
        )

        self._workers[worker_id] = worker
        return worker

    def worker_heartbeat(self, worker_id: str, **kwargs) -> Worker:
        """Met à jour le heartbeat d'un worker."""
        worker = self._workers.get(worker_id)
        if not worker:
            raise ValueError(f"Worker {worker_id} non trouvé")

        worker.last_heartbeat = datetime.now()
        worker.is_busy = kwargs.get("is_busy", worker.is_busy)
        worker.current_job_id = kwargs.get("current_job_id")
        worker.memory_mb = kwargs.get("memory_mb")
        worker.cpu_percent = kwargs.get("cpu_percent")

        return worker

    def deactivate_stale_workers(self, timeout_minutes: int = 5) -> List[Worker]:
        """Désactive les workers sans heartbeat récent."""
        cutoff = datetime.now() - timedelta(minutes=timeout_minutes)
        deactivated = []

        for worker in self._workers.values():
            if worker.is_active and worker.last_heartbeat < cutoff:
                worker.is_active = False
                deactivated.append(worker)

                # Libérer les jobs en cours
                if worker.current_job_id:
                    instance = self._instances.get(worker.current_job_id)
                    if instance and instance.status == JobStatus.RUNNING:
                        instance.status = JobStatus.QUEUED
                        instance.worker_id = None
                        instance.started_at = None

        return deactivated

    # =========================================================================
    # Contrôle des Jobs
    # =========================================================================

    def cancel_job(self, instance_id: str) -> JobInstance:
        """Annule un job."""
        instance = self._instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} non trouvée")

        if instance.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
            raise ValueError(f"Job ne peut pas être annulé: {instance.status}")

        instance.status = JobStatus.CANCELLED
        instance.completed_at = datetime.now()

        self._add_event(instance_id, "cancelled", {})

        return instance

    def pause_job_definition(self, job_def_id: str) -> JobDefinition:
        """Met en pause une définition de job."""
        definition = self._definitions.get(job_def_id)
        if not definition:
            raise ValueError(f"Définition {job_def_id} non trouvée")

        definition.is_active = False
        return definition

    def resume_job_definition(self, job_def_id: str) -> JobDefinition:
        """Reprend une définition de job."""
        definition = self._definitions.get(job_def_id)
        if not definition:
            raise ValueError(f"Définition {job_def_id} non trouvée")

        definition.is_active = True

        # Recalculer la prochaine exécution pour les jobs récurrents
        if definition.job_type == JobType.RECURRING and definition.cron_expression:
            definition.next_run_at = self._calculate_next_run(definition.cron_expression)

        return definition

    def pause_queue(self, queue_type: QueueType) -> Queue:
        """Met en pause une queue."""
        queue = self._get_queue(queue_type)
        if not queue:
            raise ValueError(f"Queue {queue_type} non trouvée")

        queue.is_paused = True
        return queue

    def resume_queue(self, queue_type: QueueType) -> Queue:
        """Reprend une queue."""
        queue = self._get_queue(queue_type)
        if not queue:
            raise ValueError(f"Queue {queue_type} non trouvée")

        queue.is_paused = False
        return queue

    # =========================================================================
    # Historique et Événements
    # =========================================================================

    def _add_event(
        self,
        instance_id: str,
        event_type: str,
        details: Dict[str, Any]
    ):
        """Ajoute un événement."""
        event = JobEvent(
            event_id=f"evt_{uuid4().hex[:8]}",
            instance_id=instance_id,
            event_type=event_type,
            details=details
        )
        self._events.append(event)

    def get_job_events(self, instance_id: str) -> List[JobEvent]:
        """Récupère les événements d'un job."""
        return [e for e in self._events if e.instance_id == instance_id]

    # =========================================================================
    # Statistiques
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques globales."""
        instances = [i for i in self._instances.values()
                    if i.tenant_id == self.tenant_id]

        by_status = {}
        for status in JobStatus:
            by_status[status.value] = len([
                i for i in instances if i.status == status
            ])

        by_queue = {}
        for queue_type in QueueType:
            queue = self._get_queue(queue_type)
            if queue:
                by_queue[queue_type.value] = {
                    "pending": queue.pending_count,
                    "running": queue.running_count,
                    "processed": queue.processed_count,
                    "failed": queue.failed_count
                }

        workers = [w for w in self._workers.values()
                  if w.tenant_id == self.tenant_id]

        return {
            "total_jobs": len(instances),
            "by_status": by_status,
            "by_queue": by_queue,
            "active_workers": len([w for w in workers if w.is_active]),
            "busy_workers": len([w for w in workers if w.is_busy]),
            "jobs_last_hour": len([
                i for i in instances
                if i.created_at >= datetime.now() - timedelta(hours=1)
            ])
        }

    # =========================================================================
    # Récupération
    # =========================================================================

    def get_instance(self, instance_id: str) -> Optional[JobInstance]:
        """Récupère une instance."""
        return self._instances.get(instance_id)

    def list_instances(
        self,
        status: Optional[JobStatus] = None,
        job_def_id: Optional[str] = None,
        limit: int = 50
    ) -> List[JobInstance]:
        """Liste les instances."""
        instances = [
            i for i in self._instances.values()
            if i.tenant_id == self.tenant_id
        ]

        if status:
            instances = [i for i in instances if i.status == status]
        if job_def_id:
            instances = [i for i in instances if i.job_def_id == job_def_id]

        instances.sort(key=lambda x: x.created_at, reverse=True)
        return instances[:limit]

    def list_definitions(
        self,
        active_only: bool = True
    ) -> List[JobDefinition]:
        """Liste les définitions de jobs."""
        definitions = [
            d for d in self._definitions.values()
            if d.tenant_id == self.tenant_id
        ]

        if active_only:
            definitions = [d for d in definitions if d.is_active]

        return sorted(definitions, key=lambda d: d.name)


def create_scheduler_service(
    tenant_id: str,
    **kwargs
) -> SchedulerService:
    """Factory pour créer un service de planification."""
    return SchedulerService(tenant_id=tenant_id, **kwargs)
