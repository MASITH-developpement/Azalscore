"""
AZALS - Service Webhooks E-Invoicing France 2026
=================================================

Gestion des webhooks pour la facturation électronique:
- Notifications sortantes vers systèmes tiers
- Validation des webhooks entrants
- File d'attente et retry logic
"""
from __future__ import annotations


import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceDirection,
    EInvoiceLifecycleEvent,
    EInvoiceRecord,
    EInvoiceStatusDB,
    TenantPDPConfig,
)

logger = logging.getLogger(__name__)


class WebhookEventType:
    """Types d'événements webhook."""
    INVOICE_CREATED = "invoice.created"
    INVOICE_VALIDATED = "invoice.validated"
    INVOICE_SENT = "invoice.sent"
    INVOICE_DELIVERED = "invoice.delivered"
    INVOICE_RECEIVED = "invoice.received"
    INVOICE_ACCEPTED = "invoice.accepted"
    INVOICE_REFUSED = "invoice.refused"
    INVOICE_PAID = "invoice.paid"
    INVOICE_ERROR = "invoice.error"
    INVOICE_CANCELLED = "invoice.cancelled"
    EREPORTING_SUBMITTED = "ereporting.submitted"
    EREPORTING_ACCEPTED = "ereporting.accepted"
    EREPORTING_REJECTED = "ereporting.rejected"


class WebhookPayload:
    """Constructeur de payload webhook."""

    @staticmethod
    def from_einvoice(
        einvoice: EInvoiceRecord,
        event_type: str,
        message: str | None = None,
        details: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Construit le payload depuis une facture."""
        return {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "einvoice_id": str(einvoice.id),
                "tenant_id": einvoice.tenant_id,
                "invoice_number": einvoice.invoice_number,
                "direction": einvoice.direction.value,
                "status": einvoice.status.value,
                "lifecycle_status": einvoice.lifecycle_status,
                "ppf_id": einvoice.ppf_id,
                "pdp_id": einvoice.pdp_id,
                "transaction_id": einvoice.transaction_id,
                "seller_siret": einvoice.seller_siret,
                "seller_name": einvoice.seller_name,
                "buyer_siret": einvoice.buyer_siret,
                "buyer_name": einvoice.buyer_name,
                "total_ttc": str(einvoice.total_ttc) if einvoice.total_ttc else None,
                "currency": einvoice.currency,
                "issue_date": einvoice.issue_date.isoformat() if einvoice.issue_date else None,
            },
            "message": message,
            "details": details or {}
        }


class WebhookNotificationService:
    """
    Service de notification webhook.

    Gère l'envoi des webhooks aux systèmes tiers configurés
    lors des changements de statut des factures.
    """

    def __init__(self, db: Session):
        self.db = db
        self.http_client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.aclose()

    def _get_http_client(self) -> httpx.AsyncClient:
        if self.http_client is None:
            raise RuntimeError("Utilisez 'async with' pour le service webhook")
        return self.http_client

    async def notify_status_change(
        self,
        einvoice: EInvoiceRecord,
        old_status: EInvoiceStatusDB | None,
        new_status: EInvoiceStatusDB,
        message: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Notifie les systèmes configurés d'un changement de statut.

        Retourne la liste des résultats d'envoi.
        """
        # Mapper le statut vers le type d'événement
        event_mapping = {
            EInvoiceStatusDB.DRAFT: WebhookEventType.INVOICE_CREATED,
            EInvoiceStatusDB.VALIDATED: WebhookEventType.INVOICE_VALIDATED,
            EInvoiceStatusDB.SENT: WebhookEventType.INVOICE_SENT,
            EInvoiceStatusDB.DELIVERED: WebhookEventType.INVOICE_DELIVERED,
            EInvoiceStatusDB.RECEIVED: WebhookEventType.INVOICE_RECEIVED,
            EInvoiceStatusDB.ACCEPTED: WebhookEventType.INVOICE_ACCEPTED,
            EInvoiceStatusDB.REFUSED: WebhookEventType.INVOICE_REFUSED,
            EInvoiceStatusDB.PAID: WebhookEventType.INVOICE_PAID,
            EInvoiceStatusDB.ERROR: WebhookEventType.INVOICE_ERROR,
            EInvoiceStatusDB.CANCELLED: WebhookEventType.INVOICE_CANCELLED,
        }

        event_type = event_mapping.get(new_status, f"invoice.{new_status.value.lower()}")

        # Construire le payload
        payload = WebhookPayload.from_einvoice(
            einvoice,
            event_type,
            message=message,
            details={"previous_status": old_status.value if old_status else None}
        )

        # Trouver les webhooks configurés
        webhooks = self._get_configured_webhooks(einvoice.tenant_id)

        results = []
        for webhook in webhooks:
            result = await self._send_webhook(
                url=webhook["url"],
                payload=payload,
                secret=webhook.get("secret"),
                config_id=webhook.get("config_id")
            )
            results.append(result)

        return results

    async def notify_ereporting_change(
        self,
        tenant_id: str,
        ereporting_id: UUID,
        event_type: str,
        data: dict[str, Any],
        message: str | None = None
    ) -> list[dict[str, Any]]:
        """Notifie les systèmes d'un changement e-reporting."""
        payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "ereporting_id": str(ereporting_id),
                "tenant_id": tenant_id,
                **data
            },
            "message": message
        }

        webhooks = self._get_configured_webhooks(tenant_id)

        results = []
        for webhook in webhooks:
            result = await self._send_webhook(
                url=webhook["url"],
                payload=payload,
                secret=webhook.get("secret"),
                config_id=webhook.get("config_id")
            )
            results.append(result)

        return results

    async def _send_webhook(
        self,
        url: str,
        payload: dict[str, Any],
        secret: str | None = None,
        config_id: UUID | None = None,
        retry_count: int = 3
    ) -> dict[str, Any]:
        """
        Envoie un webhook avec retry logic.

        Retourne le résultat de l'envoi.
        """
        client = self._get_http_client()

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AZALS-EInvoicing/1.0",
            "X-Webhook-Event": payload.get("event_type", "unknown"),
            "X-Webhook-Timestamp": payload.get("timestamp", datetime.utcnow().isoformat()),
        }

        # Ajouter la signature si secret configuré
        body = json.dumps(payload)
        if secret:
            signature = self._compute_signature(body, secret)
            headers["X-Webhook-Signature"] = signature
            headers["X-Webhook-Signature-256"] = f"sha256={signature}"

        last_error = None
        for attempt in range(retry_count):
            try:
                response = await client.post(
                    url,
                    content=body,
                    headers=headers
                )

                if response.status_code < 300:
                    return {
                        "success": True,
                        "url": url,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                        "config_id": str(config_id) if config_id else None
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"

            except httpx.TimeoutException:
                last_error = "Timeout"
            except httpx.RequestError as e:
                last_error = str(e)
            except Exception as e:
                last_error = str(e)
                logger.error(f"Erreur webhook {url}: {e}")

            # Attendre avant retry (exponential backoff)
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)

        return {
            "success": False,
            "url": url,
            "error": last_error,
            "attempts": retry_count,
            "config_id": str(config_id) if config_id else None
        }

    def _get_configured_webhooks(self, tenant_id: str) -> list[dict[str, Any]]:
        """Récupère les webhooks configurés pour le tenant."""
        configs = self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.tenant_id == tenant_id,
            TenantPDPConfig.is_active == True,
            TenantPDPConfig.webhook_url.isnot(None)
        ).all()

        webhooks = []
        for config in configs:
            if config.webhook_url:
                webhooks.append({
                    "url": config.webhook_url,
                    "secret": config.webhook_secret,
                    "config_id": config.id,
                    "provider": config.provider.value if config.provider else None
                })

        return webhooks

    @staticmethod
    def _compute_signature(payload: str, secret: str) -> str:
        """Calcule la signature HMAC-SHA256 du payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


class WebhookVerificationService:
    """Service de vérification des webhooks entrants."""

    @staticmethod
    def verify_signature(
        payload: bytes | str,
        signature: str,
        secret: str
    ) -> bool:
        """
        Vérifie la signature d'un webhook entrant.

        Supporte les formats:
        - SHA256 simple
        - sha256=<signature>
        """
        if isinstance(payload, str):
            payload = payload.encode()

        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Nettoyer la signature
        if signature.startswith("sha256="):
            signature = signature[7:]

        return hmac.compare_digest(expected, signature)

    @staticmethod
    def verify_timestamp(
        timestamp: str | datetime,
        tolerance_seconds: int = 300
    ) -> bool:
        """
        Vérifie que le timestamp du webhook est récent.

        Protection contre les replay attacks.
        """
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                return False

        now = datetime.utcnow()
        if timestamp.tzinfo:
            timestamp = timestamp.replace(tzinfo=None)

        diff = abs((now - timestamp).total_seconds())
        return diff <= tolerance_seconds


def get_webhook_service(db: Session) -> WebhookNotificationService:
    """Factory pour le service webhook."""
    return WebhookNotificationService(db)
