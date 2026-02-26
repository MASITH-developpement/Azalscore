"""
AZALSCORE Finance Webhooks
==========================

Système unifié de gestion des webhooks pour tous les providers finance.

Usage:
    from app.modules.finance.webhooks import WebhookService, WebhookRouter

    # Service
    service = WebhookService(db, tenant_id)
    result = await service.process_webhook(
        provider="swan",
        payload=request_body,
        signature=request.headers.get("X-Swan-Signature"),
    )

    # Router
    router = WebhookRouter()
    app.include_router(router)
"""

from .service import WebhookService
from .router import router as webhook_router

__all__ = [
    "WebhookService",
    "webhook_router",
]
