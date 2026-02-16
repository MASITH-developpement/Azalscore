"""
AZALS MODULE 15 - Stripe Webhook Service
==========================================

Traitement des webhooks Stripe.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import (
    DisputeStatus,
    PaymentIntentStatus,
    StripeDispute,
    StripePaymentIntent,
    StripeWebhook,
    WebhookStatus,
)

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class WebhookService(BaseStripeService[StripeWebhook]):
    """Service de traitement des webhooks Stripe."""

    model = StripeWebhook

    def process(
        self,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
    ) -> StripeWebhook:
        """
        Traite un webhook Stripe.

        Args:
            event_id: ID de l'événement Stripe
            event_type: Type d'événement
            payload: Données du webhook
            signature: Signature pour vérification

        Returns:
            Webhook enregistré
        """
        logger.info(
            "Processing webhook | tenant=%s event_id=%s event_type=%s",
            self.tenant_id,
            event_id,
            event_type,
        )

        # Enregistrer le webhook
        webhook = StripeWebhook(
            tenant_id=self.tenant_id,
            stripe_event_id=event_id,
            event_type=event_type,
            payload=payload,
            api_version=payload.get("api_version"),
            object_type=payload.get("data", {}).get("object", {}).get("object"),
            object_id=payload.get("data", {}).get("object", {}).get("id"),
            status=WebhookStatus.PENDING,
            signature=signature,
            is_verified=True,  # Après vérification signature en production
        )
        self.db.add(webhook)
        self.db.flush()

        # Traiter selon le type
        try:
            self._handle(webhook)
            webhook.status = WebhookStatus.PROCESSED
            webhook.processed_at = self._now()

            logger.info(
                "Webhook processed | tenant=%s event_id=%s event_type=%s",
                self.tenant_id,
                event_id,
                event_type,
            )
        except Exception as e:
            webhook.status = WebhookStatus.FAILED
            webhook.error_message = str(e)

            logger.warning(
                "Webhook processing failed | tenant=%s event_id=%s event_type=%s error=%s",
                self.tenant_id,
                event_id,
                event_type,
                str(e),
            )
            raise

        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    def _handle(self, webhook: StripeWebhook):
        """
        Handler interne pour dispatcher les webhooks.

        Args:
            webhook: Webhook à traiter
        """
        event_type = webhook.event_type
        data = webhook.payload.get("data", {}).get("object", {})

        handlers = {
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "charge.dispute.created": self._handle_dispute_created,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(data)
        else:
            logger.debug(
                "No handler for event type | tenant=%s event_type=%s",
                self.tenant_id,
                event_type,
            )

    def _handle_payment_succeeded(self, data: Dict[str, Any]):
        """Gère paiement réussi."""
        pi_id = data.get("id")

        pi = (
            self.db.query(StripePaymentIntent)
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.stripe_payment_intent_id == pi_id,
            )
            .first()
        )

        if pi:
            pi.status = PaymentIntentStatus.SUCCEEDED
            pi.amount_received = Decimal(str(data.get("amount_received", 0))) / 100
            pi.updated_at = self._now()

            logger.info(
                "Payment succeeded via webhook | tenant=%s pi_id=%s",
                self.tenant_id,
                pi_id,
            )

    def _handle_payment_failed(self, data: Dict[str, Any]):
        """Gère paiement échoué."""
        pi_id = data.get("id")
        error_code = data.get("last_payment_error", {}).get("code", "unknown")

        logger.warning(
            "Payment failed | tenant=%s pi_id=%s error=%s",
            self.tenant_id,
            pi_id,
            error_code,
        )

        pi = (
            self.db.query(StripePaymentIntent)
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.stripe_payment_intent_id == pi_id,
            )
            .first()
        )

        if pi:
            pi.status = PaymentIntentStatus.REQUIRES_PAYMENT_METHOD
            pi.updated_at = self._now()

    def _handle_checkout_completed(self, data: Dict[str, Any]):
        """Gère checkout complété - délègue au TenantProvisioningService."""
        from .provisioning import TenantProvisioningService

        provisioning = TenantProvisioningService(
            self.db, self.tenant_id, self.user_id
        )
        provisioning.handle_checkout_completed(data)

    def _handle_subscription_created(self, data: Dict[str, Any]):
        """Gère création abonnement."""
        from .provisioning import TenantProvisioningService

        provisioning = TenantProvisioningService(
            self.db, self.tenant_id, self.user_id
        )
        provisioning.handle_subscription_created(data)

    def _handle_subscription_updated(self, data: Dict[str, Any]):
        """Gère mise à jour abonnement."""
        from .provisioning import TenantProvisioningService

        provisioning = TenantProvisioningService(
            self.db, self.tenant_id, self.user_id
        )
        provisioning.handle_subscription_updated(data)

    def _handle_subscription_deleted(self, data: Dict[str, Any]):
        """Gère suppression abonnement."""
        from .provisioning import TenantProvisioningService

        provisioning = TenantProvisioningService(
            self.db, self.tenant_id, self.user_id
        )
        provisioning.handle_subscription_deleted(data)

    def _handle_invoice_paid(self, data: Dict[str, Any]):
        """Gère facture payée."""
        from .provisioning import TenantProvisioningService

        provisioning = TenantProvisioningService(
            self.db, self.tenant_id, self.user_id
        )
        provisioning.handle_invoice_paid(data)

    def _handle_invoice_payment_failed(self, data: Dict[str, Any]):
        """Gère échec paiement facture."""
        from .provisioning import TenantProvisioningService

        provisioning = TenantProvisioningService(
            self.db, self.tenant_id, self.user_id
        )
        provisioning.handle_invoice_payment_failed(data)

    def _handle_dispute_created(self, data: Dict[str, Any]):
        """Gère création litige."""
        dispute = StripeDispute(
            tenant_id=self.tenant_id,
            stripe_dispute_id=data.get("id"),
            stripe_charge_id=data.get("charge"),
            stripe_payment_intent_id=data.get("payment_intent"),
            amount=Decimal(str(data.get("amount", 0))) / 100,
            currency=data.get("currency", "EUR").upper(),
            status=DisputeStatus(data.get("status", "needs_response")),
            reason=data.get("reason"),
        )
        self.db.add(dispute)

        logger.warning(
            "Dispute created | tenant=%s dispute_id=%s amount=%s",
            self.tenant_id,
            data.get("id"),
            data.get("amount"),
        )

    def retry_failed(self, webhook_id: int) -> bool:
        """
        Réessaie un webhook échoué.

        Args:
            webhook_id: ID du webhook

        Returns:
            True si réussi
        """
        webhook = self._get_by_id(webhook_id)
        if not webhook or webhook.status != WebhookStatus.FAILED:
            return False

        webhook.retry_count = (webhook.retry_count or 0) + 1

        try:
            self._handle(webhook)
            webhook.status = WebhookStatus.PROCESSED
            webhook.processed_at = self._now()
            webhook.error_message = None
            self.db.commit()
            return True
        except Exception as e:
            webhook.error_message = str(e)
            self.db.commit()
            return False
