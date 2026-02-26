"""
AZALS MODULE 15 - Stripe Checkout Service
===========================================

Gestion des sessions Checkout Stripe.
"""

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import StripeCheckoutSession
from app.modules.stripe_integration.schemas import CheckoutSessionCreate

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class CheckoutService(BaseStripeService[StripeCheckoutSession]):
    """Service de gestion des sessions Checkout Stripe."""

    model = StripeCheckoutSession

    def create(self, data: CheckoutSessionCreate) -> StripeCheckoutSession:
        """
        Crée une session Checkout.

        Args:
            data: Données de la session

        Returns:
            Session créée
        """
        logger.info(
            "Creating checkout session | tenant=%s mode=%s customer_id=%s",
            self.tenant_id,
            data.mode,
            data.customer_id,
        )

        stripe_customer = None
        if data.customer_id:
            from .customer import CustomerService

            customer_service = CustomerService(self.db, self.tenant_id, self.user_id)
            stripe_customer = customer_service.get_by_crm_id(data.customer_id)

        # Préparer les line_items
        line_items_data = []
        if data.line_items:
            for item in data.line_items:
                line_items_data.append(
                    {
                        "name": item.name,
                        "description": item.description,
                        "amount": int(item.amount * 100),
                        "currency": item.currency.lower(),
                        "quantity": item.quantity,
                    }
                )

        # Simuler appel API Stripe
        session_id = self._generate_stripe_id("cs_", 24)

        amount_total = sum(
            item.amount * item.quantity for item in (data.line_items or [])
        )

        checkout_session = StripeCheckoutSession(
            tenant_id=self.tenant_id,
            stripe_session_id=session_id,
            stripe_customer_id=(
                stripe_customer.stripe_customer_id if stripe_customer else None
            ),
            mode=data.mode,
            payment_status="unpaid",
            status="open",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            url=f"https://checkout.stripe.com/c/pay/{session_id}",
            amount_total=amount_total,
            currency=data.line_items[0].currency if data.line_items else "EUR",
            invoice_id=data.invoice_id,
            order_id=data.order_id,
            subscription_id=data.subscription_id,
            stripe_metadata=data.metadata,
            line_items=line_items_data,
            customer_email=data.customer_email,
            expires_at=self._now() + timedelta(hours=24),
        )
        self.db.add(checkout_session)
        self.db.commit()
        self.db.refresh(checkout_session)

        logger.info(
            "Checkout session created | tenant=%s session_id=%s amount=%s",
            self.tenant_id,
            session_id,
            amount_total,
        )
        return checkout_session

    def get(self, session_id: int) -> Optional[StripeCheckoutSession]:
        """
        Récupère une session Checkout.

        Args:
            session_id: ID interne de la session

        Returns:
            Session ou None
        """
        return self._get_by_id(session_id)

    def get_by_stripe_id(self, stripe_session_id: str) -> Optional[StripeCheckoutSession]:
        """
        Récupère une session par ID Stripe.

        Args:
            stripe_session_id: ID Stripe de la session

        Returns:
            Session ou None
        """
        return (
            self._base_query()
            .filter(StripeCheckoutSession.stripe_session_id == stripe_session_id)
            .first()
        )

    def expire(self, session_id: int) -> bool:
        """
        Expire une session Checkout.

        Args:
            session_id: ID de la session

        Returns:
            True si expirée
        """
        session = self.get(session_id)
        if not session:
            return False

        session.status = "expired"
        session.updated_at = self._now()
        self.db.commit()

        logger.info(
            "Checkout session expired | tenant=%s session_id=%s",
            self.tenant_id,
            session_id,
        )
        return True

    def complete(
        self,
        stripe_session_id: str,
        payment_intent_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> Optional[StripeCheckoutSession]:
        """
        Marque une session comme complétée (via webhook).

        Args:
            stripe_session_id: ID Stripe de la session
            payment_intent_id: ID du PaymentIntent associé
            subscription_id: ID de la subscription associée

        Returns:
            Session mise à jour ou None
        """
        session = self.get_by_stripe_id(stripe_session_id)
        if not session:
            return None

        session.status = "complete"
        session.payment_status = "paid"
        if payment_intent_id:
            session.payment_intent_id = payment_intent_id
        if subscription_id:
            session.subscription_id = subscription_id
        session.updated_at = self._now()

        self.db.commit()
        self.db.refresh(session)

        logger.info(
            "Checkout session completed | tenant=%s session_id=%s",
            self.tenant_id,
            stripe_session_id,
        )
        return session
