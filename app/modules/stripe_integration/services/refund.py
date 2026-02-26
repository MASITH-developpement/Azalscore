"""
AZALS MODULE 15 - Stripe Refund Service
=========================================

Gestion des remboursements Stripe.
"""
from __future__ import annotations


import logging
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import (
    PaymentIntentStatus,
    RefundStatus,
    StripePaymentIntent,
    StripeRefund,
)
from app.modules.stripe_integration.schemas import RefundCreate

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class RefundService(BaseStripeService[StripeRefund]):
    """Service de gestion des remboursements Stripe."""

    model = StripeRefund

    def create(self, data: RefundCreate) -> StripeRefund:
        """
        Crée un remboursement.

        Args:
            data: Données du remboursement

        Returns:
            Remboursement créé

        Raises:
            ValueError: Si PaymentIntent invalide ou montant insuffisant
        """
        pi = (
            self.db.query(StripePaymentIntent)
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.id == data.payment_intent_id,
            )
            .first()
        )

        if not pi:
            raise ValueError("PaymentIntent non trouvé")

        if pi.status != PaymentIntentStatus.SUCCEEDED:
            raise ValueError("Seuls les paiements réussis peuvent être remboursés")

        refund_amount = data.amount or pi.amount_received

        # Vérifier montant disponible
        existing_refunds = sum(
            r.amount for r in pi.refunds if r.status == RefundStatus.SUCCEEDED
        )

        if refund_amount > (pi.amount_received - existing_refunds):
            raise ValueError("Montant de remboursement supérieur au disponible")

        # Simuler appel API Stripe
        stripe_refund_id = self._generate_stripe_id("re_")

        refund = StripeRefund(
            tenant_id=self.tenant_id,
            stripe_refund_id=stripe_refund_id,
            payment_intent_id=pi.id,
            amount=refund_amount,
            currency=pi.currency,
            status=RefundStatus.SUCCEEDED,
            reason=data.reason,
            description=data.description,
            stripe_metadata=data.metadata,
        )
        self.db.add(refund)
        self.db.commit()
        self.db.refresh(refund)

        logger.info(
            "Refund created | tenant=%s refund_id=%s pi_id=%s amount=%s",
            self.tenant_id,
            stripe_refund_id,
            data.payment_intent_id,
            refund_amount,
        )
        return refund

    def get(self, refund_id: int) -> Optional[StripeRefund]:
        """
        Récupère un remboursement.

        Args:
            refund_id: ID du remboursement

        Returns:
            Remboursement ou None
        """
        return self._get_by_id(refund_id)

    def list(
        self,
        payment_intent_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[StripeRefund]:
        """
        Liste les remboursements.

        Args:
            payment_intent_id: Filtrer par PaymentIntent
            skip: Offset
            limit: Limite

        Returns:
            Liste des remboursements
        """
        query = self._base_query()

        if payment_intent_id:
            query = query.filter(StripeRefund.payment_intent_id == payment_intent_id)

        return (
            query.order_by(StripeRefund.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def cancel(self, refund_id: int) -> bool:
        """
        Annule un remboursement en attente.

        Args:
            refund_id: ID du remboursement

        Returns:
            True si annulé
        """
        refund = self.get(refund_id)
        if not refund:
            return False

        if refund.status != RefundStatus.PENDING:
            return False

        refund.status = RefundStatus.CANCELED
        refund.updated_at = self._now()
        self.db.commit()

        logger.info(
            "Refund cancelled | tenant=%s refund_id=%s",
            self.tenant_id,
            refund_id,
        )
        return True
