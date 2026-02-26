"""
AZALS MODULE 15 - Stripe PaymentIntent Service
================================================

Gestion des PaymentIntents Stripe.
"""
from __future__ import annotations


import logging
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import (
    PaymentIntentStatus,
    StripePaymentIntent,
)
from app.modules.stripe_integration.schemas import (
    PaymentIntentConfirm,
    PaymentIntentCreate,
)

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class PaymentIntentService(BaseStripeService[StripePaymentIntent]):
    """Service de gestion des PaymentIntents Stripe."""

    model = StripePaymentIntent

    def create(self, data: PaymentIntentCreate) -> StripePaymentIntent:
        """
        Crée un PaymentIntent.

        Args:
            data: Données du PaymentIntent

        Returns:
            PaymentIntent créé
        """
        logger.info(
            "Creating payment intent | tenant=%s amount=%s currency=%s customer_id=%s",
            self.tenant_id,
            data.amount,
            data.currency,
            data.customer_id,
        )

        stripe_customer = None
        if data.customer_id:
            from .customer import CustomerService

            customer_service = CustomerService(self.db, self.tenant_id, self.user_id)
            stripe_customer = customer_service.get_by_crm_id(data.customer_id)

        # Simuler appel API Stripe
        stripe_pi_id = self._generate_stripe_id("pi_")
        client_secret = f"{stripe_pi_id}_secret_{self._generate_stripe_id('')}"

        payment_intent = StripePaymentIntent(
            tenant_id=self.tenant_id,
            stripe_payment_intent_id=stripe_pi_id,
            stripe_customer_id=stripe_customer.id if stripe_customer else None,
            amount=data.amount,
            amount_received=Decimal("0"),
            currency=data.currency.upper(),
            status=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
            payment_method_id=data.payment_method_id,
            payment_method_types=data.payment_method_types,
            capture_method=data.capture_method,
            client_secret=client_secret,
            invoice_id=data.invoice_id,
            order_id=data.order_id,
            subscription_id=data.subscription_id,
            description=data.description,
            stripe_metadata=data.metadata,
            receipt_email=data.receipt_email,
        )
        self.db.add(payment_intent)
        self.db.commit()
        self.db.refresh(payment_intent)

        logger.info(
            "Payment intent created | tenant=%s pi_id=%s amount=%s status=%s",
            self.tenant_id,
            stripe_pi_id,
            data.amount,
            PaymentIntentStatus.REQUIRES_PAYMENT_METHOD.value,
        )
        return payment_intent

    def get(self, payment_intent_id: int) -> Optional[StripePaymentIntent]:
        """
        Récupère un PaymentIntent.

        Args:
            payment_intent_id: ID du PaymentIntent

        Returns:
            PaymentIntent ou None
        """
        return self._get_by_id(payment_intent_id)

    def list(
        self,
        customer_id: Optional[int] = None,
        status: Optional[PaymentIntentStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[StripePaymentIntent], int]:
        """
        Liste les PaymentIntents.

        Args:
            customer_id: Filtrer par client CRM
            status: Filtrer par statut
            skip: Offset
            limit: Limite

        Returns:
            Tuple (liste, total)
        """
        query = self._base_query()

        if customer_id:
            from .customer import CustomerService

            customer_service = CustomerService(self.db, self.tenant_id, self.user_id)
            stripe_customer = customer_service.get_by_crm_id(customer_id)
            if stripe_customer:
                query = query.filter(
                    StripePaymentIntent.stripe_customer_id == stripe_customer.id
                )

        if status:
            query = query.filter(StripePaymentIntent.status == status)

        total = query.count()
        items = (
            query.order_by(StripePaymentIntent.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def confirm(
        self,
        payment_intent_id: int,
        data: PaymentIntentConfirm,
    ) -> StripePaymentIntent:
        """
        Confirme un PaymentIntent.

        Args:
            payment_intent_id: ID du PaymentIntent
            data: Données de confirmation

        Returns:
            PaymentIntent confirmé

        Raises:
            ValueError: Si PaymentIntent non trouvé
        """
        logger.info(
            "Confirming payment intent | tenant=%s pi_id=%s",
            self.tenant_id,
            payment_intent_id,
        )

        pi = self.get(payment_intent_id)
        if not pi:
            logger.warning(
                "Payment intent not found | tenant=%s pi_id=%s",
                self.tenant_id,
                payment_intent_id,
            )
            raise ValueError("PaymentIntent non trouvé")

        if data.payment_method_id:
            pi.payment_method_id = data.payment_method_id

        # Simuler confirmation réussie
        pi.status = PaymentIntentStatus.SUCCEEDED
        pi.amount_received = pi.amount
        pi.updated_at = self._now()

        # Calculer frais Stripe simulés (1.5% + 0.25€)
        stripe_fee = pi.amount * Decimal("0.015") + Decimal("0.25")
        pi.stripe_fee = stripe_fee
        pi.net_amount = pi.amount - stripe_fee

        self.db.commit()
        self.db.refresh(pi)

        logger.info(
            "Payment intent confirmed | tenant=%s pi_id=%s stripe_id=%s amount=%s",
            self.tenant_id,
            payment_intent_id,
            pi.stripe_payment_intent_id,
            pi.amount,
        )
        return pi

    def capture(
        self,
        payment_intent_id: int,
        amount: Optional[Decimal] = None,
    ) -> StripePaymentIntent:
        """
        Capture un PaymentIntent (pour capture manuelle).

        Args:
            payment_intent_id: ID du PaymentIntent
            amount: Montant à capturer (optionnel, défaut: total)

        Returns:
            PaymentIntent capturé

        Raises:
            ValueError: Si PaymentIntent non trouvé ou non capturable
        """
        pi = self.get(payment_intent_id)
        if not pi:
            raise ValueError("PaymentIntent non trouvé")

        if pi.status != PaymentIntentStatus.REQUIRES_CAPTURE:
            raise ValueError("PaymentIntent ne peut pas être capturé")

        capture_amount = amount or pi.amount

        pi.status = PaymentIntentStatus.SUCCEEDED
        pi.amount_received = capture_amount
        pi.captured_at = self._now()
        pi.updated_at = self._now()

        self.db.commit()
        self.db.refresh(pi)

        logger.info(
            "Payment intent captured | tenant=%s pi_id=%s amount=%s",
            self.tenant_id,
            payment_intent_id,
            capture_amount,
        )
        return pi

    def cancel(
        self,
        payment_intent_id: int,
        reason: Optional[str] = None,
    ) -> StripePaymentIntent:
        """
        Annule un PaymentIntent.

        Args:
            payment_intent_id: ID du PaymentIntent
            reason: Raison de l'annulation

        Returns:
            PaymentIntent annulé

        Raises:
            ValueError: Si PaymentIntent non trouvé ou déjà réussi
        """
        logger.info(
            "Cancelling payment intent | tenant=%s pi_id=%s reason=%s",
            self.tenant_id,
            payment_intent_id,
            reason,
        )

        pi = self.get(payment_intent_id)
        if not pi:
            logger.warning(
                "Payment intent not found for cancellation | tenant=%s pi_id=%s",
                self.tenant_id,
                payment_intent_id,
            )
            raise ValueError("PaymentIntent non trouvé")

        if pi.status == PaymentIntentStatus.SUCCEEDED:
            logger.warning(
                "Cannot cancel succeeded payment | tenant=%s pi_id=%s",
                self.tenant_id,
                payment_intent_id,
            )
            raise ValueError("Impossible d'annuler un paiement réussi")

        pi.status = PaymentIntentStatus.CANCELED
        pi.cancellation_reason = reason
        pi.updated_at = self._now()

        self.db.commit()
        self.db.refresh(pi)

        logger.info(
            "Payment intent cancelled | tenant=%s pi_id=%s stripe_id=%s",
            self.tenant_id,
            payment_intent_id,
            pi.stripe_payment_intent_id,
        )
        return pi

    def update_from_webhook(
        self,
        stripe_pi_id: str,
        status: PaymentIntentStatus,
        amount_received: Optional[Decimal] = None,
    ) -> Optional[StripePaymentIntent]:
        """
        Met à jour un PaymentIntent depuis un webhook.

        Args:
            stripe_pi_id: ID Stripe du PaymentIntent
            status: Nouveau statut
            amount_received: Montant reçu

        Returns:
            PaymentIntent mis à jour ou None
        """
        pi = (
            self._base_query()
            .filter(StripePaymentIntent.stripe_payment_intent_id == stripe_pi_id)
            .first()
        )

        if not pi:
            return None

        pi.status = status
        if amount_received is not None:
            pi.amount_received = amount_received
        pi.updated_at = self._now()

        self.db.commit()
        self.db.refresh(pi)
        return pi
