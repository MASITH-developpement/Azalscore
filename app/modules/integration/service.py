"""
Service Integration Hub / Centre d'intégration - GAP-086

Gestion des intégrations:
- Connecteurs API
- Webhooks et événements
- Mappings de données
- Synchronisation
- Logs et monitoring
- Gestion des erreurs
- Files d'attente
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import uuid4
import json
import hashlib


# ============== Énumérations ==============

class ConnectorType(str, Enum):
    """Types de connecteur"""
    REST_API = "rest_api"
    SOAP = "soap"
    GRAPHQL = "graphql"
    WEBHOOK = "webhook"
    DATABASE = "database"
    FILE = "file"
    SFTP = "sftp"
    EMAIL = "email"
    QUEUE = "queue"


class ConnectorStatus(str, Enum):
    """Statuts de connecteur"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    TESTING = "testing"


class AuthType(str, Enum):
    """Types d'authentification"""
    NONE = "none"
    API_KEY = "api_key"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    CERTIFICATE = "certificate"
    CUSTOM = "custom"


class SyncDirection(str, Enum):
    """Direction de synchronisation"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Statuts de synchronisation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class WebhookStatus(str, Enum):
    """Statuts webhook"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class MessageStatus(str, Enum):
    """Statuts message queue"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class LogLevel(str, Enum):
    """Niveaux de log"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============== Data Classes ==============

@dataclass
class AuthConfig:
    """Configuration d'authentification"""
    auth_type: AuthType = AuthType.NONE
    api_key: str = ""
    api_key_header: str = "X-API-Key"
    username: str = ""
    password: str = ""
    token: str = ""
    token_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    scope: str = ""
    certificate_path: str = ""
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class RateLimitConfig:
    """Configuration de rate limiting"""
    requests_per_second: int = 10
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_size: int = 20
    retry_after_seconds: int = 60


@dataclass
class RetryConfig:
    """Configuration de retry"""
    max_retries: int = 3
    initial_delay_seconds: int = 1
    max_delay_seconds: int = 60
    exponential_backoff: bool = True
    retry_on_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])


@dataclass
class Connector:
    """Connecteur d'intégration"""
    id: str
    tenant_id: str
    name: str
    code: str
    connector_type: ConnectorType
    status: ConnectorStatus = ConnectorStatus.INACTIVE
    description: str = ""

    # Endpoint
    base_url: str = ""
    timeout_seconds: int = 30

    # Authentification
    auth_config: AuthConfig = field(default_factory=AuthConfig)

    # Rate limiting
    rate_limit_config: RateLimitConfig = field(default_factory=RateLimitConfig)

    # Retry
    retry_config: RetryConfig = field(default_factory=RetryConfig)

    # Configuration spécifique
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

    # Statistiques
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_request_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: str = ""

    # Métadonnées
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FieldMapping:
    """Mapping de champ"""
    id: str
    source_field: str
    target_field: str
    transform_type: str = "direct"  # direct, constant, expression, lookup
    transform_value: str = ""
    default_value: Any = None
    required: bool = False
    data_type: str = "string"


@dataclass
class DataMapping:
    """Mapping de données"""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str = ""
    source_entity: str = ""
    target_entity: str = ""
    direction: SyncDirection = SyncDirection.OUTBOUND
    field_mappings: List[FieldMapping] = field(default_factory=list)
    filter_expression: str = ""
    transform_script: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SyncJob:
    """Job de synchronisation"""
    id: str
    tenant_id: str
    connector_id: str
    connector_name: str
    mapping_id: Optional[str] = None
    mapping_name: str = ""
    name: str = ""
    description: str = ""
    direction: SyncDirection = SyncDirection.OUTBOUND
    status: SyncStatus = SyncStatus.PENDING

    # Planification
    schedule_cron: str = ""  # Expression cron
    is_scheduled: bool = False
    next_run_at: Optional[datetime] = None

    # Exécution
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0

    # Résultats
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    records_skipped: int = 0
    error_message: str = ""
    error_details: List[Dict] = field(default_factory=list)

    # Configuration
    batch_size: int = 100
    full_sync: bool = False
    last_sync_timestamp: Optional[datetime] = None

    # Métadonnées
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WebhookEndpoint:
    """Endpoint webhook"""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str = ""
    status: WebhookStatus = WebhookStatus.ACTIVE

    # URL
    url: str = ""
    secret_key: str = ""
    signature_header: str = "X-Signature"

    # Événements
    event_types: List[str] = field(default_factory=list)

    # Configuration
    http_method: str = "POST"
    content_type: str = "application/json"
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30

    # Retry
    retry_config: RetryConfig = field(default_factory=RetryConfig)

    # Statistiques
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_delivery_at: Optional[datetime] = None
    last_status_code: Optional[int] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WebhookDelivery:
    """Livraison webhook"""
    id: str
    tenant_id: str
    endpoint_id: str
    endpoint_name: str
    event_type: str
    event_id: str
    status: str = "pending"  # pending, sent, delivered, failed

    # Requête
    request_url: str = ""
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: str = ""

    # Réponse
    response_status_code: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: str = ""

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    duration_ms: int = 0

    # Retry
    attempt_number: int = 1
    next_retry_at: Optional[datetime] = None
    error_message: str = ""


@dataclass
class QueueMessage:
    """Message de file d'attente"""
    id: str
    tenant_id: str
    queue_name: str
    message_type: str
    status: MessageStatus = MessageStatus.PENDING
    priority: int = 5  # 1-10, 1 = highest

    # Contenu
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Retry
    attempt_count: int = 0
    max_attempts: int = 3
    next_retry_at: Optional[datetime] = None
    error_message: str = ""

    # Traçabilité
    correlation_id: str = ""
    source: str = ""


@dataclass
class IntegrationLog:
    """Log d'intégration"""
    id: str
    tenant_id: str
    connector_id: Optional[str] = None
    connector_name: str = ""
    job_id: Optional[str] = None
    webhook_id: Optional[str] = None
    message_id: Optional[str] = None
    level: LogLevel = LogLevel.INFO
    category: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    error_trace: str = ""
    duration_ms: int = 0
    correlation_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class IntegrationStats:
    """Statistiques d'intégration"""
    tenant_id: str
    period_start: date
    period_end: date
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: Decimal = Decimal("0")
    average_duration_ms: int = 0
    total_records_synced: int = 0
    webhook_deliveries: int = 0
    queue_messages_processed: int = 0
    by_connector: Dict[str, Dict] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    hourly_distribution: Dict[int, int] = field(default_factory=dict)


# ============== Service ==============

class IntegrationService:
    """
    Service de gestion des intégrations.

    Fonctionnalités:
    - Connecteurs API
    - Webhooks
    - Mappings de données
    - Synchronisation
    - Files d'attente
    - Logs et monitoring
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._connectors: Dict[str, Connector] = {}
        self._mappings: Dict[str, DataMapping] = {}
        self._sync_jobs: Dict[str, SyncJob] = {}
        self._webhooks: Dict[str, WebhookEndpoint] = {}
        self._deliveries: Dict[str, WebhookDelivery] = {}
        self._messages: Dict[str, QueueMessage] = {}
        self._logs: Dict[str, IntegrationLog] = {}

    # ========== Connecteurs ==========

    def create_connector(
        self,
        name: str,
        code: str,
        connector_type: ConnectorType,
        base_url: str = "",
        description: str = "",
        auth_type: AuthType = AuthType.NONE,
        timeout_seconds: int = 30
    ) -> Connector:
        """Créer un connecteur"""
        connector = Connector(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            code=code.upper(),
            connector_type=connector_type,
            base_url=base_url,
            description=description,
            timeout_seconds=timeout_seconds
        )
        connector.auth_config.auth_type = auth_type
        self._connectors[connector.id] = connector
        return connector

    def configure_auth(
        self,
        connector_id: str,
        auth_type: AuthType,
        api_key: str = "",
        username: str = "",
        password: str = "",
        token: str = "",
        client_id: str = "",
        client_secret: str = "",
        token_url: str = ""
    ) -> Optional[Connector]:
        """Configurer authentification"""
        connector = self._connectors.get(connector_id)
        if not connector:
            return None

        connector.auth_config = AuthConfig(
            auth_type=auth_type,
            api_key=api_key,
            username=username,
            password=password,
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url
        )
        connector.updated_at = datetime.now()
        return connector

    def configure_rate_limit(
        self,
        connector_id: str,
        requests_per_second: int = 10,
        requests_per_minute: int = 100,
        burst_size: int = 20
    ) -> Optional[Connector]:
        """Configurer rate limiting"""
        connector = self._connectors.get(connector_id)
        if not connector:
            return None

        connector.rate_limit_config = RateLimitConfig(
            requests_per_second=requests_per_second,
            requests_per_minute=requests_per_minute,
            burst_size=burst_size
        )
        connector.updated_at = datetime.now()
        return connector

    def activate_connector(self, connector_id: str) -> Optional[Connector]:
        """Activer connecteur"""
        connector = self._connectors.get(connector_id)
        if not connector:
            return None

        connector.status = ConnectorStatus.ACTIVE
        connector.updated_at = datetime.now()
        return connector

    def deactivate_connector(self, connector_id: str) -> Optional[Connector]:
        """Désactiver connecteur"""
        connector = self._connectors.get(connector_id)
        if not connector:
            return None

        connector.status = ConnectorStatus.INACTIVE
        connector.updated_at = datetime.now()
        return connector

    def test_connector(self, connector_id: str) -> Dict[str, Any]:
        """Tester connecteur (simulation)"""
        connector = self._connectors.get(connector_id)
        if not connector:
            return {"success": False, "error": "Connecteur non trouvé"}

        # Simulation de test
        connector.total_requests += 1
        connector.last_request_at = datetime.now()

        # Test simulé réussi
        connector.successful_requests += 1
        connector.last_success_at = datetime.now()

        self._log(
            connector_id=connector_id,
            connector_name=connector.name,
            level=LogLevel.INFO,
            category="test",
            message="Test de connexion réussi"
        )

        return {
            "success": True,
            "message": "Connexion établie avec succès",
            "response_time_ms": 150,
            "timestamp": datetime.now().isoformat()
        }

    def execute_request(
        self,
        connector_id: str,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Exécuter requête (simulation)"""
        connector = self._connectors.get(connector_id)
        if not connector:
            return {"success": False, "error": "Connecteur non trouvé"}

        if connector.status != ConnectorStatus.ACTIVE:
            return {"success": False, "error": "Connecteur inactif"}

        connector.total_requests += 1
        connector.last_request_at = datetime.now()

        # Simulation d'exécution
        success = True  # Simulé
        response_data = {"status": "ok", "data": data}

        if success:
            connector.successful_requests += 1
            connector.last_success_at = datetime.now()

            self._log(
                connector_id=connector_id,
                connector_name=connector.name,
                level=LogLevel.INFO,
                category="request",
                message=f"{method} {endpoint} - Succès",
                details={"method": method, "endpoint": endpoint}
            )

            return {
                "success": True,
                "status_code": 200,
                "data": response_data,
                "duration_ms": 200
            }
        else:
            connector.failed_requests += 1
            connector.last_error_at = datetime.now()
            connector.last_error_message = "Erreur de connexion"

            self._log(
                connector_id=connector_id,
                connector_name=connector.name,
                level=LogLevel.ERROR,
                category="request",
                message=f"{method} {endpoint} - Erreur"
            )

            return {
                "success": False,
                "error": "Erreur de connexion"
            }

    def get_connector(self, connector_id: str) -> Optional[Connector]:
        """Obtenir connecteur"""
        return self._connectors.get(connector_id)

    def list_connectors(
        self,
        status: Optional[ConnectorStatus] = None,
        connector_type: Optional[ConnectorType] = None
    ) -> List[Connector]:
        """Lister connecteurs"""
        connectors = list(self._connectors.values())

        if status:
            connectors = [c for c in connectors if c.status == status]
        if connector_type:
            connectors = [c for c in connectors if c.connector_type == connector_type]

        return sorted(connectors, key=lambda x: x.name)

    # ========== Mappings ==========

    def create_mapping(
        self,
        name: str,
        code: str,
        source_entity: str,
        target_entity: str,
        direction: SyncDirection = SyncDirection.OUTBOUND,
        description: str = ""
    ) -> DataMapping:
        """Créer mapping de données"""
        mapping = DataMapping(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            code=code.upper(),
            description=description,
            source_entity=source_entity,
            target_entity=target_entity,
            direction=direction
        )
        self._mappings[mapping.id] = mapping
        return mapping

    def add_field_mapping(
        self,
        mapping_id: str,
        source_field: str,
        target_field: str,
        transform_type: str = "direct",
        transform_value: str = "",
        default_value: Any = None,
        required: bool = False,
        data_type: str = "string"
    ) -> Optional[DataMapping]:
        """Ajouter mapping de champ"""
        mapping = self._mappings.get(mapping_id)
        if not mapping:
            return None

        field_mapping = FieldMapping(
            id=str(uuid4()),
            source_field=source_field,
            target_field=target_field,
            transform_type=transform_type,
            transform_value=transform_value,
            default_value=default_value,
            required=required,
            data_type=data_type
        )
        mapping.field_mappings.append(field_mapping)
        mapping.updated_at = datetime.now()
        return mapping

    def transform_data(
        self,
        mapping_id: str,
        source_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transformer données selon mapping"""
        mapping = self._mappings.get(mapping_id)
        if not mapping or not mapping.is_active:
            return None

        result = {}
        for field_map in mapping.field_mappings:
            source_value = source_data.get(field_map.source_field)

            if source_value is None:
                if field_map.required:
                    return None  # Champ requis manquant
                source_value = field_map.default_value

            # Appliquer transformation
            if field_map.transform_type == "direct":
                result[field_map.target_field] = source_value
            elif field_map.transform_type == "constant":
                result[field_map.target_field] = field_map.transform_value
            elif field_map.transform_type == "expression":
                # Simulation: évaluer expression
                result[field_map.target_field] = source_value
            elif field_map.transform_type == "lookup":
                # Simulation: lookup dans table de correspondance
                result[field_map.target_field] = source_value

        return result

    def get_mapping(self, mapping_id: str) -> Optional[DataMapping]:
        """Obtenir mapping"""
        return self._mappings.get(mapping_id)

    def list_mappings(
        self,
        direction: Optional[SyncDirection] = None,
        active_only: bool = True
    ) -> List[DataMapping]:
        """Lister mappings"""
        mappings = list(self._mappings.values())

        if active_only:
            mappings = [m for m in mappings if m.is_active]
        if direction:
            mappings = [m for m in mappings if m.direction == direction]

        return sorted(mappings, key=lambda x: x.name)

    # ========== Synchronisation ==========

    def create_sync_job(
        self,
        connector_id: str,
        name: str,
        direction: SyncDirection = SyncDirection.OUTBOUND,
        mapping_id: Optional[str] = None,
        schedule_cron: str = "",
        batch_size: int = 100
    ) -> Optional[SyncJob]:
        """Créer job de synchronisation"""
        connector = self._connectors.get(connector_id)
        if not connector:
            return None

        mapping_name = ""
        if mapping_id:
            mapping = self._mappings.get(mapping_id)
            if mapping:
                mapping_name = mapping.name

        job = SyncJob(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            connector_id=connector_id,
            connector_name=connector.name,
            mapping_id=mapping_id,
            mapping_name=mapping_name,
            name=name,
            direction=direction,
            schedule_cron=schedule_cron,
            is_scheduled=bool(schedule_cron),
            batch_size=batch_size
        )
        self._sync_jobs[job.id] = job
        return job

    def start_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Démarrer synchronisation"""
        job = self._sync_jobs.get(job_id)
        if not job or job.status == SyncStatus.RUNNING:
            return None

        job.status = SyncStatus.RUNNING
        job.started_at = datetime.now()
        job.records_processed = 0
        job.records_created = 0
        job.records_updated = 0
        job.records_failed = 0
        job.error_details = []

        self._log(
            connector_id=job.connector_id,
            connector_name=job.connector_name,
            job_id=job_id,
            level=LogLevel.INFO,
            category="sync",
            message=f"Démarrage synchronisation: {job.name}"
        )

        return job

    def complete_sync_job(
        self,
        job_id: str,
        records_created: int = 0,
        records_updated: int = 0,
        records_failed: int = 0,
        error_message: str = ""
    ) -> Optional[SyncJob]:
        """Terminer synchronisation"""
        job = self._sync_jobs.get(job_id)
        if not job or job.status != SyncStatus.RUNNING:
            return None

        job.completed_at = datetime.now()
        job.duration_seconds = int(
            (job.completed_at - job.started_at).total_seconds()
        )
        job.records_created = records_created
        job.records_updated = records_updated
        job.records_failed = records_failed
        job.records_processed = records_created + records_updated + records_failed
        job.error_message = error_message
        job.last_sync_timestamp = job.completed_at

        if records_failed > 0 and records_created + records_updated == 0:
            job.status = SyncStatus.FAILED
        elif records_failed > 0:
            job.status = SyncStatus.PARTIAL
        else:
            job.status = SyncStatus.COMPLETED

        self._log(
            connector_id=job.connector_id,
            connector_name=job.connector_name,
            job_id=job_id,
            level=LogLevel.INFO if job.status == SyncStatus.COMPLETED else LogLevel.WARNING,
            category="sync",
            message=f"Synchronisation terminée: {job.records_processed} enregistrements",
            details={
                "created": records_created,
                "updated": records_updated,
                "failed": records_failed
            }
        )

        return job

    def cancel_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Annuler synchronisation"""
        job = self._sync_jobs.get(job_id)
        if not job or job.status != SyncStatus.RUNNING:
            return None

        job.status = SyncStatus.CANCELLED
        job.completed_at = datetime.now()

        return job

    def get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Obtenir job"""
        return self._sync_jobs.get(job_id)

    def list_sync_jobs(
        self,
        connector_id: Optional[str] = None,
        status: Optional[SyncStatus] = None
    ) -> List[SyncJob]:
        """Lister jobs"""
        jobs = list(self._sync_jobs.values())

        if connector_id:
            jobs = [j for j in jobs if j.connector_id == connector_id]
        if status:
            jobs = [j for j in jobs if j.status == status]

        return sorted(jobs, key=lambda x: x.created_at, reverse=True)

    # ========== Webhooks ==========

    def create_webhook(
        self,
        name: str,
        code: str,
        url: str,
        event_types: List[str],
        description: str = "",
        secret_key: str = ""
    ) -> WebhookEndpoint:
        """Créer webhook"""
        if not secret_key:
            secret_key = hashlib.sha256(str(uuid4()).encode()).hexdigest()[:32]

        webhook = WebhookEndpoint(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            code=code.upper(),
            description=description,
            url=url,
            secret_key=secret_key,
            event_types=event_types
        )
        self._webhooks[webhook.id] = webhook
        return webhook

    def trigger_webhook(
        self,
        event_type: str,
        event_id: str,
        payload: Dict[str, Any]
    ) -> List[WebhookDelivery]:
        """Déclencher webhooks pour un événement"""
        deliveries = []

        for webhook in self._webhooks.values():
            if webhook.status != WebhookStatus.ACTIVE:
                continue
            if event_type not in webhook.event_types:
                continue

            delivery = WebhookDelivery(
                id=str(uuid4()),
                tenant_id=self.tenant_id,
                endpoint_id=webhook.id,
                endpoint_name=webhook.name,
                event_type=event_type,
                event_id=event_id,
                request_url=webhook.url,
                request_body=json.dumps(payload)
            )
            self._deliveries[delivery.id] = delivery
            deliveries.append(delivery)

            # Simulation envoi
            self._send_webhook(delivery, webhook)

        return deliveries

    def _send_webhook(
        self,
        delivery: WebhookDelivery,
        webhook: WebhookEndpoint
    ) -> None:
        """Envoyer webhook (simulation)"""
        delivery.sent_at = datetime.now()

        # Simulation succès
        success = True

        if success:
            delivery.status = "delivered"
            delivery.response_status_code = 200
            delivery.duration_ms = 150

            webhook.total_deliveries += 1
            webhook.successful_deliveries += 1
            webhook.last_delivery_at = datetime.now()
            webhook.last_status_code = 200

        else:
            delivery.status = "failed"
            delivery.error_message = "Connection timeout"
            delivery.next_retry_at = datetime.now() + timedelta(
                seconds=webhook.retry_config.initial_delay_seconds
            )

            webhook.total_deliveries += 1
            webhook.failed_deliveries += 1

    def retry_webhook_delivery(
        self,
        delivery_id: str
    ) -> Optional[WebhookDelivery]:
        """Réessayer livraison webhook"""
        delivery = self._deliveries.get(delivery_id)
        if not delivery or delivery.status == "delivered":
            return None

        webhook = self._webhooks.get(delivery.endpoint_id)
        if not webhook:
            return None

        if delivery.attempt_number >= webhook.retry_config.max_retries:
            delivery.status = "failed"
            return delivery

        delivery.attempt_number += 1
        self._send_webhook(delivery, webhook)

        return delivery

    def get_webhook(self, webhook_id: str) -> Optional[WebhookEndpoint]:
        """Obtenir webhook"""
        return self._webhooks.get(webhook_id)

    def list_webhooks(
        self,
        status: Optional[WebhookStatus] = None,
        event_type: Optional[str] = None
    ) -> List[WebhookEndpoint]:
        """Lister webhooks"""
        webhooks = list(self._webhooks.values())

        if status:
            webhooks = [w for w in webhooks if w.status == status]
        if event_type:
            webhooks = [w for w in webhooks if event_type in w.event_types]

        return sorted(webhooks, key=lambda x: x.name)

    def get_webhook_deliveries(
        self,
        webhook_id: str,
        status: Optional[str] = None
    ) -> List[WebhookDelivery]:
        """Obtenir livraisons webhook"""
        deliveries = [
            d for d in self._deliveries.values()
            if d.endpoint_id == webhook_id
        ]

        if status:
            deliveries = [d for d in deliveries if d.status == status]

        return sorted(deliveries, key=lambda x: x.created_at, reverse=True)

    # ========== Files d'attente ==========

    def enqueue_message(
        self,
        queue_name: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: int = 5,
        scheduled_at: Optional[datetime] = None,
        correlation_id: str = "",
        source: str = ""
    ) -> QueueMessage:
        """Ajouter message à la file"""
        message = QueueMessage(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            queue_name=queue_name,
            message_type=message_type,
            payload=payload,
            priority=priority,
            scheduled_at=scheduled_at,
            correlation_id=correlation_id or str(uuid4()),
            source=source
        )
        self._messages[message.id] = message

        self._log(
            level=LogLevel.DEBUG,
            category="queue",
            message=f"Message ajouté: {queue_name}/{message_type}",
            details={"message_id": message.id}
        )

        return message

    def dequeue_message(
        self,
        queue_name: str
    ) -> Optional[QueueMessage]:
        """Récupérer prochain message"""
        now = datetime.now()
        candidates = [
            m for m in self._messages.values()
            if m.queue_name == queue_name
            and m.status == MessageStatus.PENDING
            and (m.scheduled_at is None or m.scheduled_at <= now)
        ]

        if not candidates:
            return None

        # Trier par priorité puis par création
        candidates.sort(key=lambda x: (x.priority, x.created_at))
        message = candidates[0]

        message.status = MessageStatus.PROCESSING
        message.started_at = datetime.now()
        message.attempt_count += 1

        return message

    def complete_message(
        self,
        message_id: str
    ) -> Optional[QueueMessage]:
        """Marquer message comme traité"""
        message = self._messages.get(message_id)
        if not message:
            return None

        message.status = MessageStatus.COMPLETED
        message.completed_at = datetime.now()

        return message

    def fail_message(
        self,
        message_id: str,
        error_message: str
    ) -> Optional[QueueMessage]:
        """Marquer message comme échoué"""
        message = self._messages.get(message_id)
        if not message:
            return None

        message.error_message = error_message

        if message.attempt_count >= message.max_attempts:
            message.status = MessageStatus.DEAD_LETTER
        else:
            message.status = MessageStatus.PENDING
            # Backoff exponentiel
            delay = 2 ** message.attempt_count
            message.next_retry_at = datetime.now() + timedelta(seconds=delay)

        return message

    def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """Obtenir statistiques file"""
        messages = [m for m in self._messages.values() if m.queue_name == queue_name]

        return {
            "queue_name": queue_name,
            "total": len(messages),
            "pending": len([m for m in messages if m.status == MessageStatus.PENDING]),
            "processing": len([m for m in messages if m.status == MessageStatus.PROCESSING]),
            "completed": len([m for m in messages if m.status == MessageStatus.COMPLETED]),
            "failed": len([m for m in messages if m.status == MessageStatus.FAILED]),
            "dead_letter": len([m for m in messages if m.status == MessageStatus.DEAD_LETTER])
        }

    # ========== Logs ==========

    def _log(
        self,
        level: LogLevel,
        category: str,
        message: str,
        connector_id: Optional[str] = None,
        connector_name: str = "",
        job_id: Optional[str] = None,
        webhook_id: Optional[str] = None,
        message_id: Optional[str] = None,
        details: Dict[str, Any] = None,
        correlation_id: str = ""
    ) -> IntegrationLog:
        """Créer log"""
        log = IntegrationLog(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            connector_id=connector_id,
            connector_name=connector_name,
            job_id=job_id,
            webhook_id=webhook_id,
            message_id=message_id,
            level=level,
            category=category,
            message=message,
            details=details or {},
            correlation_id=correlation_id or str(uuid4())
        )
        self._logs[log.id] = log
        return log

    def get_logs(
        self,
        connector_id: Optional[str] = None,
        job_id: Optional[str] = None,
        level: Optional[LogLevel] = None,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[IntegrationLog]:
        """Obtenir logs"""
        logs = list(self._logs.values())

        if connector_id:
            logs = [l for l in logs if l.connector_id == connector_id]
        if job_id:
            logs = [l for l in logs if l.job_id == job_id]
        if level:
            logs = [l for l in logs if l.level == level]
        if category:
            logs = [l for l in logs if l.category == category]
        if date_from:
            logs = [l for l in logs if l.created_at >= date_from]
        if date_to:
            logs = [l for l in logs if l.created_at <= date_to]

        logs = sorted(logs, key=lambda x: x.created_at, reverse=True)
        return logs[:limit]

    def get_error_logs(self, hours: int = 24) -> List[IntegrationLog]:
        """Obtenir logs d'erreur récents"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            l for l in self._logs.values()
            if l.level in [LogLevel.ERROR, LogLevel.CRITICAL]
            and l.created_at >= cutoff
        ]

    # ========== Statistiques ==========

    def get_integration_stats(
        self,
        period_start: date,
        period_end: date
    ) -> IntegrationStats:
        """Calculer statistiques"""
        stats = IntegrationStats(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end
        )

        # Par connecteur
        for connector in self._connectors.values():
            stats.total_requests += connector.total_requests
            stats.successful_requests += connector.successful_requests
            stats.failed_requests += connector.failed_requests

            stats.by_connector[connector.id] = {
                "name": connector.name,
                "requests": connector.total_requests,
                "success": connector.successful_requests,
                "failed": connector.failed_requests
            }

        if stats.total_requests > 0:
            stats.success_rate = Decimal(stats.successful_requests) / stats.total_requests * 100

        # Jobs de sync
        jobs = [
            j for j in self._sync_jobs.values()
            if j.started_at and period_start <= j.started_at.date() <= period_end
        ]
        stats.total_records_synced = sum(j.records_processed for j in jobs)

        # Webhooks
        deliveries = [
            d for d in self._deliveries.values()
            if d.sent_at and period_start <= d.sent_at.date() <= period_end
        ]
        stats.webhook_deliveries = len(deliveries)

        # Messages queue
        messages = [
            m for m in self._messages.values()
            if m.completed_at and period_start <= m.completed_at.date() <= period_end
        ]
        stats.queue_messages_processed = len(messages)

        # Distribution horaire
        for log in self._logs.values():
            if period_start <= log.created_at.date() <= period_end:
                hour = log.created_at.hour
                stats.hourly_distribution[hour] = stats.hourly_distribution.get(hour, 0) + 1

        return stats


def create_integration_service(tenant_id: str) -> IntegrationService:
    """Factory function pour créer le service integration"""
    return IntegrationService(tenant_id)


# ============================================================================
# CONNECTOR DEFINITIONS - Configuration statique des connecteurs
# ============================================================================

# Import des types du models pour eviter duplication
from .models import (
    ConnectorType as ModelConnectorType,
    EntityType,
    SyncDirection as ModelSyncDirection,
    AuthType as ModelAuthType,
)


@dataclass
class ConnectorDefinition:
    """Definition statique d'un type de connecteur."""
    connector_type: ModelConnectorType
    name: str
    display_name: str
    description: str
    category: str
    icon_url: str = ""
    logo_url: str = ""
    color: str = "#000000"
    auth_type: str = "oauth2"
    base_url: str = ""
    api_version: str = ""
    oauth_authorize_url: str = ""
    oauth_token_url: str = ""
    oauth_scopes: List[str] = field(default_factory=list)
    oauth_pkce_required: bool = False
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    supported_entities: List[EntityType] = field(default_factory=list)
    supported_directions: List[ModelSyncDirection] = field(default_factory=list)
    rate_limit_requests: int = 100
    rate_limit_daily: int = 10000
    supports_webhooks: bool = False
    webhook_events: List[str] = field(default_factory=list)
    documentation_url: str = ""
    setup_guide_url: str = ""
    is_beta: bool = False
    is_premium: bool = False


# Definitions des connecteurs preconfigures
CONNECTOR_DEFINITIONS: Dict[ModelConnectorType, ConnectorDefinition] = {
    # Google
    ModelConnectorType.GOOGLE_DRIVE: ConnectorDefinition(
        connector_type=ModelConnectorType.GOOGLE_DRIVE,
        name="google_drive",
        display_name="Google Drive",
        description="Stockage et partage de fichiers Google",
        category="storage",
        color="#4285F4",
        auth_type="oauth2",
        base_url="https://www.googleapis.com/drive/v3",
        oauth_authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        oauth_token_url="https://oauth2.googleapis.com/token",
        oauth_scopes=["https://www.googleapis.com/auth/drive"],
        supported_entities=[EntityType.FILE],
        supported_directions=[ModelSyncDirection.INBOUND, ModelSyncDirection.OUTBOUND],
        supports_webhooks=True,
        webhook_events=["file.created", "file.updated", "file.deleted"],
        documentation_url="https://developers.google.com/drive",
    ),
    ModelConnectorType.GOOGLE_SHEETS: ConnectorDefinition(
        connector_type=ModelConnectorType.GOOGLE_SHEETS,
        name="google_sheets",
        display_name="Google Sheets",
        description="Tableurs Google pour import/export de donnees",
        category="productivity",
        color="#0F9D58",
        auth_type="oauth2",
        base_url="https://sheets.googleapis.com/v4",
        oauth_authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        oauth_token_url="https://oauth2.googleapis.com/token",
        oauth_scopes=["https://www.googleapis.com/auth/spreadsheets"],
        supported_entities=[EntityType.CUSTOM],
        supported_directions=[ModelSyncDirection.INBOUND, ModelSyncDirection.OUTBOUND],
        documentation_url="https://developers.google.com/sheets",
    ),

    # Microsoft
    ModelConnectorType.MICROSOFT_365: ConnectorDefinition(
        connector_type=ModelConnectorType.MICROSOFT_365,
        name="microsoft_365",
        display_name="Microsoft 365",
        description="Suite Microsoft 365 (OneDrive, Outlook, etc.)",
        category="productivity",
        color="#0078D4",
        auth_type="oauth2",
        base_url="https://graph.microsoft.com/v1.0",
        oauth_authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        oauth_token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        oauth_scopes=["openid", "profile", "email", "Files.ReadWrite"],
        supported_entities=[EntityType.FILE, EntityType.EVENT, EntityType.CONTACT],
        supported_directions=[ModelSyncDirection.BIDIRECTIONAL],
        supports_webhooks=True,
        documentation_url="https://learn.microsoft.com/en-us/graph/",
    ),

    # Slack
    ModelConnectorType.SLACK: ConnectorDefinition(
        connector_type=ModelConnectorType.SLACK,
        name="slack",
        display_name="Slack",
        description="Messagerie d'equipe et notifications",
        category="communication",
        color="#4A154B",
        auth_type="oauth2",
        base_url="https://slack.com/api",
        oauth_authorize_url="https://slack.com/oauth/v2/authorize",
        oauth_token_url="https://slack.com/api/oauth.v2.access",
        oauth_scopes=["chat:write", "channels:read"],
        supported_entities=[EntityType.MESSAGE],
        supported_directions=[ModelSyncDirection.OUTBOUND],
        supports_webhooks=True,
        webhook_events=["message", "reaction_added"],
        documentation_url="https://api.slack.com/",
    ),

    # Salesforce
    ModelConnectorType.SALESFORCE: ConnectorDefinition(
        connector_type=ModelConnectorType.SALESFORCE,
        name="salesforce",
        display_name="Salesforce",
        description="CRM Salesforce",
        category="crm",
        color="#00A1E0",
        auth_type="oauth2",
        base_url="https://login.salesforce.com",
        oauth_authorize_url="https://login.salesforce.com/services/oauth2/authorize",
        oauth_token_url="https://login.salesforce.com/services/oauth2/token",
        supported_entities=[EntityType.CUSTOMER, EntityType.CONTACT, EntityType.LEAD, EntityType.OPPORTUNITY],
        supported_directions=[ModelSyncDirection.BIDIRECTIONAL],
        supports_webhooks=True,
        is_premium=True,
        documentation_url="https://developer.salesforce.com/docs",
    ),

    # HubSpot
    ModelConnectorType.HUBSPOT: ConnectorDefinition(
        connector_type=ModelConnectorType.HUBSPOT,
        name="hubspot",
        display_name="HubSpot",
        description="CRM et marketing HubSpot",
        category="crm",
        color="#FF7A59",
        auth_type="oauth2",
        base_url="https://api.hubapi.com",
        oauth_authorize_url="https://app.hubspot.com/oauth/authorize",
        oauth_token_url="https://api.hubapi.com/oauth/v1/token",
        supported_entities=[EntityType.CONTACT, EntityType.CUSTOMER, EntityType.LEAD],
        supported_directions=[ModelSyncDirection.BIDIRECTIONAL],
        supports_webhooks=True,
        documentation_url="https://developers.hubspot.com/docs",
    ),

    # Stripe
    ModelConnectorType.STRIPE: ConnectorDefinition(
        connector_type=ModelConnectorType.STRIPE,
        name="stripe",
        display_name="Stripe",
        description="Paiements en ligne Stripe",
        category="payment",
        color="#635BFF",
        auth_type="api_key",
        base_url="https://api.stripe.com/v1",
        required_fields=["api_key"],
        supported_entities=[EntityType.CUSTOMER, EntityType.PAYMENT, EntityType.INVOICE],
        supported_directions=[ModelSyncDirection.BIDIRECTIONAL],
        supports_webhooks=True,
        webhook_events=["payment_intent.succeeded", "invoice.paid", "customer.created"],
        documentation_url="https://stripe.com/docs/api",
    ),

    # Shopify
    ModelConnectorType.SHOPIFY: ConnectorDefinition(
        connector_type=ModelConnectorType.SHOPIFY,
        name="shopify",
        display_name="Shopify",
        description="Plateforme e-commerce Shopify",
        category="ecommerce",
        color="#96BF48",
        auth_type="oauth2",
        base_url="https://admin.shopify.com/admin/api/2024-01",
        oauth_authorize_url="https://{shop}.myshopify.com/admin/oauth/authorize",
        oauth_token_url="https://{shop}.myshopify.com/admin/oauth/access_token",
        required_fields=["shop"],
        supported_entities=[EntityType.CUSTOMER, EntityType.PRODUCT, EntityType.ORDER],
        supported_directions=[ModelSyncDirection.BIDIRECTIONAL],
        supports_webhooks=True,
        webhook_events=["orders/create", "products/update", "customers/create"],
        documentation_url="https://shopify.dev/docs/api",
    ),

    # API Generique
    ModelConnectorType.REST_API: ConnectorDefinition(
        connector_type=ModelConnectorType.REST_API,
        name="rest_api",
        display_name="REST API",
        description="Connecteur API REST generique",
        category="custom",
        color="#6B7280",
        auth_type="custom",
        required_fields=["base_url"],
        optional_fields=["headers", "auth_type", "api_key"],
        supported_entities=[EntityType.CUSTOM],
        supported_directions=[ModelSyncDirection.BIDIRECTIONAL],
        documentation_url="",
    ),

    # Webhook
    ModelConnectorType.WEBHOOK: ConnectorDefinition(
        connector_type=ModelConnectorType.WEBHOOK,
        name="webhook",
        display_name="Webhook",
        description="Webhook personnalise entrant/sortant",
        category="custom",
        color="#6B7280",
        auth_type="custom",
        required_fields=["webhook_url"],
        supported_entities=[EntityType.CUSTOM],
        supported_directions=[ModelSyncDirection.BIDIRECTIONAL],
        supports_webhooks=True,
    ),
}
