"""
AZALSCORE - E-Invoicing Webhooks
Traitement des webhooks PDP et notifications
"""
from __future__ import annotations

import concurrent.futures
import logging
import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceRecord,
    EInvoiceStatusDB,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_webhooks import (
    get_webhook_service,
)

if TYPE_CHECKING:
    from .lifecycle import LifecycleManager

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Gestionnaire des webhooks e-invoicing.

    Gère:
    - Réception et traitement des webhooks PDP
    - Envoi de notifications webhook
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        lifecycle_manager: "LifecycleManager"
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.lifecycle_manager = lifecycle_manager

    def process_webhook(
        self,
        pdp_config: TenantPDPConfig,
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Traite un webhook PDP.

        Args:
            pdp_config: Configuration PDP
            payload: Données du webhook

        Returns:
            Résultat du traitement
        """
        # Trouver la facture
        einvoice = self._find_einvoice(payload)

        if not einvoice:
            return {"error": "Facture non trouvée", "payload": payload}

        # Mettre à jour le statut
        event_type = payload.get("event_type", "").upper()
        new_status = self._map_event_to_status(event_type)

        if new_status:
            old_status = einvoice.status
            einvoice.status = new_status
            einvoice.lifecycle_status = payload.get("lifecycle_status")
            einvoice.updated_at = datetime.utcnow()

            self.db.commit()

            self.lifecycle_manager.add_event(
                einvoice,
                status=event_type,
                actor=payload.get("actor"),
                source="WEBHOOK",
                message=payload.get("message"),
                details=payload.get("details", {})
            )

            self.lifecycle_manager.update_stats_on_status_change(
                einvoice, old_status, new_status
            )

        return {
            "processed": True,
            "einvoice_id": str(einvoice.id),
            "new_status": new_status.value if new_status else None
        }

    def _find_einvoice(self, payload: dict[str, Any]) -> EInvoiceRecord | None:
        """Trouve la facture correspondant au payload."""
        if payload.get("ppf_id"):
            return self.db.query(EInvoiceRecord).filter(
                EInvoiceRecord.tenant_id == self.tenant_id,
                EInvoiceRecord.ppf_id == payload["ppf_id"]
            ).first()
        elif payload.get("pdp_id"):
            return self.db.query(EInvoiceRecord).filter(
                EInvoiceRecord.tenant_id == self.tenant_id,
                EInvoiceRecord.pdp_id == payload["pdp_id"]
            ).first()
        elif payload.get("invoice_id"):
            return self.db.query(EInvoiceRecord).filter(
                EInvoiceRecord.tenant_id == self.tenant_id,
                EInvoiceRecord.transaction_id == payload["invoice_id"]
            ).first()
        return None

    def _map_event_to_status(self, event_type: str) -> EInvoiceStatusDB | None:
        """Mappe un type d'événement vers un statut."""
        status_mapping = {
            "DEPOSITED": EInvoiceStatusDB.SENT,
            "TRANSMITTED": EInvoiceStatusDB.DELIVERED,
            "RECEIVED": EInvoiceStatusDB.RECEIVED,
            "ACCEPTED": EInvoiceStatusDB.ACCEPTED,
            "REFUSED": EInvoiceStatusDB.REFUSED,
            "PAID": EInvoiceStatusDB.PAID,
            "CANCELLED": EInvoiceStatusDB.CANCELLED,
            "ERROR": EInvoiceStatusDB.ERROR,
        }
        return status_mapping.get(event_type)

    def trigger_notification(
        self,
        einvoice: EInvoiceRecord,
        old_status: EInvoiceStatusDB | None,
        new_status: EInvoiceStatusDB,
        message: str | None = None
    ) -> None:
        """
        Déclenche une notification webhook de manière asynchrone.

        Args:
            einvoice: Facture électronique
            old_status: Ancien statut
            new_status: Nouveau statut
            message: Message optionnel
        """
        def run_async_notification():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._send_webhook_notification(einvoice, old_status, new_status, message)
                )
            except Exception as e:
                logger.warning(f"Erreur notification webhook: {e}")
            finally:
                loop.close()

        # Exécuter en background pour ne pas bloquer
        try:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            executor.submit(run_async_notification)
        except Exception as e:
            logger.warning(f"Impossible de lancer notification webhook: {e}")

    async def _send_webhook_notification(
        self,
        einvoice: EInvoiceRecord,
        old_status: EInvoiceStatusDB | None,
        new_status: EInvoiceStatusDB,
        message: str | None = None
    ) -> list[dict[str, Any]]:
        """Envoie les notifications webhook."""
        webhook_service = get_webhook_service(self.db)
        async with webhook_service:
            results = await webhook_service.notify_status_change(
                einvoice=einvoice,
                old_status=old_status,
                new_status=new_status,
                message=message
            )
            for result in results:
                if result.get("success"):
                    logger.info(f"Webhook envoyé: {result.get('url')}")
                else:
                    logger.warning(f"Échec webhook: {result.get('url')} - {result.get('error')}")
            return results
