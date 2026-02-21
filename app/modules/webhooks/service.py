"""
Service Webhooks - GAP-053

Gestion des webhooks sortants:
- Abonnements par événement
- Signature HMAC-SHA256
- Retry avec backoff exponentiel
- Logs de livraison
- Monitoring santé endpoints
- Rotation des secrets
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import hashlib
import hmac
import json


# ============================================================
# ÉNUMÉRATIONS
# ============================================================

class WebhookEvent(Enum):
    """Événements déclencheurs de webhooks."""
    # Documents commerciaux
    INVOICE_CREATED = "invoice.created"
    INVOICE_SENT = "invoice.sent"
    INVOICE_PAID = "invoice.paid"
    INVOICE_OVERDUE = "invoice.overdue"
    QUOTE_CREATED = "quote.created"
    QUOTE_ACCEPTED = "quote.accepted"
    QUOTE_REJECTED = "quote.rejected"
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"

    # Clients et contacts
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    CONTACT_CREATED = "contact.created"

    # Paiements
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    REFUND_ISSUED = "refund.issued"

    # Produits et stock
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    STOCK_LOW = "stock.low"
    STOCK_OUT = "stock.out"

    # Utilisateurs
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # Interventions
    INTERVENTION_CREATED = "intervention.created"
    INTERVENTION_COMPLETED = "intervention.completed"
    INTERVENTION_CANCELLED = "intervention.cancelled"

    # Workflows
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    APPROVAL_PENDING = "approval.pending"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"

    # Système
    BACKUP_COMPLETED = "backup.completed"
    IMPORT_COMPLETED = "import.completed"
    EXPORT_COMPLETED = "export.completed"


class WebhookStatus(Enum):
    """Statut d'un webhook."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    FAILING = "failing"


class DeliveryStatus(Enum):
    """Statut de livraison."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class SignatureVersion(Enum):
    """Versions de signature."""
    V1_HMAC_SHA256 = "v1"
    V2_HMAC_SHA512 = "v2"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class WebhookEndpoint:
    """Configuration d'un endpoint webhook."""
    id: str
    tenant_id: str
    name: str
    url: str

    # Événements abonnés
    events: Set[WebhookEvent] = field(default_factory=set)

    # Sécurité
    secret: str = ""
    signature_version: SignatureVersion = SignatureVersion.V1_HMAC_SHA256
    verify_ssl: bool = True

    # Headers personnalisés
    custom_headers: Dict[str, str] = field(default_factory=dict)

    # État
    status: WebhookStatus = WebhookStatus.ACTIVE

    # Configuration retry
    max_retries: int = 5
    retry_delay_seconds: int = 60
    timeout_seconds: int = 30

    # Statistiques
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_delivery_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0

    # Métadonnées
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Taux de succès."""
        if self.total_deliveries == 0:
            return 100.0
        return (self.successful_deliveries / self.total_deliveries) * 100


@dataclass
class WebhookPayload:
    """Payload d'un webhook."""
    id: str
    tenant_id: str
    event: WebhookEvent
    timestamp: datetime = field(default_factory=datetime.now)

    # Données
    data: Dict[str, Any] = field(default_factory=dict)

    # Contexte
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None

    # Métadonnées API
    api_version: str = "2026-02"

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour envoi."""
        return {
            "id": self.id,
            "event": self.event.value,
            "timestamp": self.timestamp.isoformat(),
            "api_version": self.api_version,
            "data": self.data,
            "context": {
                "source_id": self.source_id,
                "source_type": self.source_type,
                "actor_id": self.actor_id,
                "actor_email": self.actor_email,
            }
        }


@dataclass
class DeliveryAttempt:
    """Tentative de livraison."""
    id: str
    tenant_id: str
    endpoint_id: str
    payload_id: str

    # État
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempt_number: int = 1

    # Requête
    request_url: str = ""
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: str = ""

    # Réponse
    response_status_code: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[str] = None
    response_time_ms: int = 0

    # Erreur
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Timestamps
    scheduled_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Retry
    next_retry_at: Optional[datetime] = None


@dataclass
class WebhookLog:
    """Log d'événement webhook."""
    id: str
    tenant_id: str
    endpoint_id: str
    event: WebhookEvent

    # Résultat
    success: bool = False
    attempts: int = 0
    final_status_code: Optional[int] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    total_duration_ms: int = 0


@dataclass
class WebhookSecret:
    """Secret de signature webhook."""
    id: str
    tenant_id: str
    endpoint_id: str
    secret: str
    version: int = 1

    # Rotation
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None


@dataclass
class HealthCheck:
    """Résultat de health check d'un endpoint."""
    id: str
    endpoint_id: str

    # Résultat
    is_healthy: bool = False
    status_code: Optional[int] = None
    response_time_ms: int = 0
    error_message: Optional[str] = None

    # Timestamp
    checked_at: datetime = field(default_factory=datetime.now)


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class WebhookService:
    """Service de gestion des webhooks."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (à remplacer par DB)
        self._endpoints: Dict[str, WebhookEndpoint] = {}
        self._payloads: Dict[str, WebhookPayload] = {}
        self._delivery_attempts: Dict[str, DeliveryAttempt] = {}
        self._logs: List[WebhookLog] = []
        self._secrets: Dict[str, List[WebhookSecret]] = {}
        self._health_checks: Dict[str, List[HealthCheck]] = {}

        # Queue de livraison (en production: Redis/RabbitMQ)
        self._delivery_queue: List[str] = []

    # ========================================
    # GESTION DES ENDPOINTS
    # ========================================

    def create_endpoint(
        self,
        name: str,
        url: str,
        events: List[WebhookEvent],
        **kwargs
    ) -> WebhookEndpoint:
        """Crée un endpoint webhook."""
        import secrets as py_secrets

        # Générer le secret
        secret = py_secrets.token_urlsafe(32)

        endpoint = WebhookEndpoint(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            url=url,
            events=set(events),
            secret=secret,
            signature_version=kwargs.get("signature_version", SignatureVersion.V1_HMAC_SHA256),
            verify_ssl=kwargs.get("verify_ssl", True),
            custom_headers=kwargs.get("custom_headers", {}),
            max_retries=kwargs.get("max_retries", 5),
            retry_delay_seconds=kwargs.get("retry_delay_seconds", 60),
            timeout_seconds=kwargs.get("timeout_seconds", 30),
            description=kwargs.get("description"),
        )

        self._endpoints[endpoint.id] = endpoint

        # Initialiser le secret dans l'historique
        self._secrets[endpoint.id] = [WebhookSecret(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            endpoint_id=endpoint.id,
            secret=secret,
            version=1,
        )]

        return endpoint

    def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        """Récupère un endpoint."""
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint and endpoint.tenant_id == self.tenant_id:
            return endpoint
        return None

    def list_endpoints(
        self,
        status: Optional[WebhookStatus] = None,
        event: Optional[WebhookEvent] = None
    ) -> List[WebhookEndpoint]:
        """Liste les endpoints."""
        endpoints = [
            e for e in self._endpoints.values()
            if e.tenant_id == self.tenant_id
        ]

        if status:
            endpoints = [e for e in endpoints if e.status == status]
        if event:
            endpoints = [e for e in endpoints if event in e.events]

        return sorted(endpoints, key=lambda x: x.created_at, reverse=True)

    def update_endpoint(
        self,
        endpoint_id: str,
        **kwargs
    ) -> Optional[WebhookEndpoint]:
        """Met à jour un endpoint."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None

        if "name" in kwargs:
            endpoint.name = kwargs["name"]
        if "url" in kwargs:
            endpoint.url = kwargs["url"]
        if "events" in kwargs:
            endpoint.events = set(kwargs["events"])
        if "status" in kwargs:
            endpoint.status = kwargs["status"]
        if "custom_headers" in kwargs:
            endpoint.custom_headers = kwargs["custom_headers"]
        if "max_retries" in kwargs:
            endpoint.max_retries = kwargs["max_retries"]
        if "verify_ssl" in kwargs:
            endpoint.verify_ssl = kwargs["verify_ssl"]

        endpoint.updated_at = datetime.now()
        return endpoint

    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Supprime un endpoint."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        del self._endpoints[endpoint_id]

        # Nettoyer les secrets
        if endpoint_id in self._secrets:
            del self._secrets[endpoint_id]

        return True

    def pause_endpoint(self, endpoint_id: str) -> bool:
        """Met en pause un endpoint."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        endpoint.status = WebhookStatus.PAUSED
        endpoint.updated_at = datetime.now()
        return True

    def resume_endpoint(self, endpoint_id: str) -> bool:
        """Reprend un endpoint."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        endpoint.status = WebhookStatus.ACTIVE
        endpoint.consecutive_failures = 0
        endpoint.updated_at = datetime.now()
        return True

    # ========================================
    # SIGNATURE ET SÉCURITÉ
    # ========================================

    def _sign_payload(
        self,
        payload: str,
        secret: str,
        version: SignatureVersion
    ) -> str:
        """Signe un payload."""
        if version == SignatureVersion.V1_HMAC_SHA256:
            signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            return f"v1={signature}"
        elif version == SignatureVersion.V2_HMAC_SHA512:
            signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha512
            ).hexdigest()
            return f"v2={signature}"
        return ""

    def verify_signature(
        self,
        endpoint_id: str,
        payload: str,
        signature: str
    ) -> bool:
        """Vérifie une signature (pour webhooks entrants)."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        expected = self._sign_payload(
            payload, endpoint.secret, endpoint.signature_version
        )
        return hmac.compare_digest(expected, signature)

    def rotate_secret(self, endpoint_id: str) -> Optional[str]:
        """Rotation du secret d'un endpoint."""
        import secrets as py_secrets

        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None

        # Générer nouveau secret
        new_secret = py_secrets.token_urlsafe(32)

        # Marquer l'ancien comme expirant
        if endpoint_id in self._secrets:
            for old_secret in self._secrets[endpoint_id]:
                if old_secret.is_active:
                    old_secret.expires_at = datetime.now() + timedelta(hours=24)
                    old_secret.rotated_at = datetime.now()

        # Ajouter le nouveau
        version = len(self._secrets.get(endpoint_id, [])) + 1
        new_secret_obj = WebhookSecret(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            endpoint_id=endpoint_id,
            secret=new_secret,
            version=version,
        )

        if endpoint_id not in self._secrets:
            self._secrets[endpoint_id] = []
        self._secrets[endpoint_id].append(new_secret_obj)

        # Mettre à jour l'endpoint
        endpoint.secret = new_secret
        endpoint.updated_at = datetime.now()

        return new_secret

    # ========================================
    # ENVOI DE WEBHOOKS
    # ========================================

    def trigger(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        **kwargs
    ) -> List[str]:
        """
        Déclenche un événement webhook.
        Retourne les IDs des livraisons créées.
        """
        # Créer le payload
        payload = WebhookPayload(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            event=event,
            data=data,
            source_id=kwargs.get("source_id"),
            source_type=kwargs.get("source_type"),
            actor_id=kwargs.get("actor_id"),
            actor_email=kwargs.get("actor_email"),
        )

        self._payloads[payload.id] = payload

        # Trouver les endpoints abonnés
        endpoints = self.list_endpoints(status=WebhookStatus.ACTIVE, event=event)

        delivery_ids = []
        for endpoint in endpoints:
            # Créer une tentative de livraison
            attempt = self._create_delivery_attempt(endpoint, payload)
            delivery_ids.append(attempt.id)

            # Ajouter à la queue
            self._delivery_queue.append(attempt.id)

        return delivery_ids

    def _create_delivery_attempt(
        self,
        endpoint: WebhookEndpoint,
        payload: WebhookPayload
    ) -> DeliveryAttempt:
        """Crée une tentative de livraison."""
        payload_json = json.dumps(payload.to_dict())
        signature = self._sign_payload(
            payload_json, endpoint.secret, endpoint.signature_version
        )

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": payload.id,
            "X-Webhook-Event": payload.event.value,
            "X-Webhook-Timestamp": payload.timestamp.isoformat(),
            "X-Webhook-Signature": signature,
            **endpoint.custom_headers,
        }

        attempt = DeliveryAttempt(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            endpoint_id=endpoint.id,
            payload_id=payload.id,
            request_url=endpoint.url,
            request_headers=headers,
            request_body=payload_json,
        )

        self._delivery_attempts[attempt.id] = attempt
        return attempt

    def deliver(self, attempt_id: str) -> DeliveryAttempt:
        """
        Effectue la livraison d'un webhook.
        En production: utiliser httpx/aiohttp avec async.
        """
        attempt = self._delivery_attempts.get(attempt_id)
        if not attempt or attempt.tenant_id != self.tenant_id:
            raise ValueError(f"Tentative {attempt_id} non trouvée")

        endpoint = self.get_endpoint(attempt.endpoint_id)
        if not endpoint:
            attempt.status = DeliveryStatus.FAILED
            attempt.error_message = "Endpoint non trouvé"
            return attempt

        attempt.started_at = datetime.now()
        attempt.status = DeliveryStatus.PENDING

        # Simuler l'envoi (en production: vraie requête HTTP)
        try:
            # Simulation succès/échec
            import random
            start_time = datetime.now()

            # 95% de succès en simulation
            if random.random() < 0.95:
                attempt.response_status_code = 200
                attempt.response_body = '{"status": "ok"}'
                attempt.status = DeliveryStatus.DELIVERED

                # Mettre à jour stats endpoint
                endpoint.successful_deliveries += 1
                endpoint.last_success_at = datetime.now()
                endpoint.consecutive_failures = 0
            else:
                attempt.response_status_code = 500
                attempt.error_message = "Internal Server Error"
                attempt.status = DeliveryStatus.FAILED

                endpoint.failed_deliveries += 1
                endpoint.last_failure_at = datetime.now()
                endpoint.consecutive_failures += 1

                # Planifier retry si pas dépassé
                if attempt.attempt_number < endpoint.max_retries:
                    delay = endpoint.retry_delay_seconds * (2 ** (attempt.attempt_number - 1))
                    attempt.next_retry_at = datetime.now() + timedelta(seconds=delay)
                    attempt.status = DeliveryStatus.RETRYING

            attempt.response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        except Exception as e:
            attempt.status = DeliveryStatus.FAILED
            attempt.error_message = str(e)
            endpoint.failed_deliveries += 1
            endpoint.consecutive_failures += 1

        attempt.completed_at = datetime.now()
        endpoint.total_deliveries += 1
        endpoint.last_delivery_at = datetime.now()

        # Marquer comme failing si trop d'échecs
        if endpoint.consecutive_failures >= 5:
            endpoint.status = WebhookStatus.FAILING

        # Logger
        self._log_delivery(attempt, endpoint)

        return attempt

    def retry(self, attempt_id: str) -> DeliveryAttempt:
        """Réessaie une livraison."""
        original = self._delivery_attempts.get(attempt_id)
        if not original or original.tenant_id != self.tenant_id:
            raise ValueError(f"Tentative {attempt_id} non trouvée")

        endpoint = self.get_endpoint(original.endpoint_id)
        if not endpoint:
            raise ValueError("Endpoint non trouvé")

        # Créer nouvelle tentative
        new_attempt = DeliveryAttempt(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            endpoint_id=original.endpoint_id,
            payload_id=original.payload_id,
            attempt_number=original.attempt_number + 1,
            request_url=original.request_url,
            request_headers=original.request_headers,
            request_body=original.request_body,
        )

        self._delivery_attempts[new_attempt.id] = new_attempt
        return self.deliver(new_attempt.id)

    def _log_delivery(
        self,
        attempt: DeliveryAttempt,
        endpoint: WebhookEndpoint
    ) -> None:
        """Enregistre un log de livraison."""
        payload = self._payloads.get(attempt.payload_id)
        if not payload:
            return

        log = WebhookLog(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            endpoint_id=endpoint.id,
            event=payload.event,
            success=(attempt.status == DeliveryStatus.DELIVERED),
            attempts=attempt.attempt_number,
            final_status_code=attempt.response_status_code,
            delivered_at=attempt.completed_at if attempt.status == DeliveryStatus.DELIVERED else None,
            total_duration_ms=attempt.response_time_ms,
        )

        self._logs.append(log)

    # ========================================
    # HEALTH CHECK
    # ========================================

    def check_health(self, endpoint_id: str) -> HealthCheck:
        """Vérifie la santé d'un endpoint."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} non trouvé")

        # Simuler un health check
        import random
        start_time = datetime.now()

        health = HealthCheck(
            id=str(uuid4()),
            endpoint_id=endpoint_id,
        )

        # 90% de succès en simulation
        if random.random() < 0.90:
            health.is_healthy = True
            health.status_code = 200
        else:
            health.is_healthy = False
            health.status_code = 503
            health.error_message = "Service Unavailable"

        health.response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000) + random.randint(10, 200)
        health.checked_at = datetime.now()

        # Stocker
        if endpoint_id not in self._health_checks:
            self._health_checks[endpoint_id] = []
        self._health_checks[endpoint_id].append(health)

        # Garder seulement les 100 derniers
        self._health_checks[endpoint_id] = self._health_checks[endpoint_id][-100:]

        return health

    def get_health_history(
        self,
        endpoint_id: str,
        limit: int = 50
    ) -> List[HealthCheck]:
        """Récupère l'historique de santé."""
        checks = self._health_checks.get(endpoint_id, [])
        return sorted(checks, key=lambda x: x.checked_at, reverse=True)[:limit]

    # ========================================
    # LOGS ET MONITORING
    # ========================================

    def get_logs(
        self,
        endpoint_id: Optional[str] = None,
        event: Optional[WebhookEvent] = None,
        success: Optional[bool] = None,
        limit: int = 100
    ) -> List[WebhookLog]:
        """Récupère les logs."""
        logs = [l for l in self._logs if l.tenant_id == self.tenant_id]

        if endpoint_id:
            logs = [l for l in logs if l.endpoint_id == endpoint_id]
        if event:
            logs = [l for l in logs if l.event == event]
        if success is not None:
            logs = [l for l in logs if l.success == success]

        return sorted(logs, key=lambda x: x.created_at, reverse=True)[:limit]

    def get_delivery_attempts(
        self,
        payload_id: str
    ) -> List[DeliveryAttempt]:
        """Récupère les tentatives de livraison pour un payload."""
        attempts = [
            a for a in self._delivery_attempts.values()
            if a.tenant_id == self.tenant_id and a.payload_id == payload_id
        ]
        return sorted(attempts, key=lambda x: x.attempt_number)

    def get_pending_retries(self) -> List[DeliveryAttempt]:
        """Récupère les livraisons en attente de retry."""
        now = datetime.now()
        return [
            a for a in self._delivery_attempts.values()
            if (a.tenant_id == self.tenant_id and
                a.status == DeliveryStatus.RETRYING and
                a.next_retry_at and
                a.next_retry_at <= now)
        ]

    def get_statistics(
        self,
        endpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calcule les statistiques."""
        if endpoint_id:
            endpoints = [self.get_endpoint(endpoint_id)]
            endpoints = [e for e in endpoints if e]
        else:
            endpoints = self.list_endpoints()

        total_deliveries = sum(e.total_deliveries for e in endpoints)
        successful = sum(e.successful_deliveries for e in endpoints)
        failed = sum(e.failed_deliveries for e in endpoints)

        return {
            "total_endpoints": len(endpoints),
            "active_endpoints": len([e for e in endpoints if e.status == WebhookStatus.ACTIVE]),
            "failing_endpoints": len([e for e in endpoints if e.status == WebhookStatus.FAILING]),
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "success_rate": (successful / total_deliveries * 100) if total_deliveries > 0 else 100.0,
            "pending_retries": len(self.get_pending_retries()),
        }


# ============================================================
# FACTORY
# ============================================================

def create_webhook_service(tenant_id: str) -> WebhookService:
    """Crée une instance du service Webhook."""
    return WebhookService(tenant_id=tenant_id)
