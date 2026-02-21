"""
Module Webhooks - GAP-053

Gestion des webhooks sortants:
- Abonnements par événement
- Signature HMAC-SHA256
- Retry avec backoff exponentiel
- Logs de livraison
- Monitoring santé endpoints
- Rotation des secrets
"""

from .service import (
    # Énumérations
    WebhookEvent,
    WebhookStatus,
    DeliveryStatus,
    SignatureVersion,

    # Data classes
    WebhookEndpoint,
    WebhookPayload,
    DeliveryAttempt,
    WebhookLog,
    WebhookSecret,
    HealthCheck,

    # Service
    WebhookService,
    create_webhook_service,
)

__all__ = [
    "WebhookEvent",
    "WebhookStatus",
    "DeliveryStatus",
    "SignatureVersion",
    "WebhookEndpoint",
    "WebhookPayload",
    "DeliveryAttempt",
    "WebhookLog",
    "WebhookSecret",
    "HealthCheck",
    "WebhookService",
    "create_webhook_service",
]
