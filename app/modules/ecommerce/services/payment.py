"""
AZALS MODULE 12 - E-Commerce Payment Service
==============================================

Gestion des paiements.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.modules.ecommerce.models import (
    EcommerceOrder,
    EcommercePayment,
    OrderStatus,
    PaymentStatus,
)

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class PaymentService(BaseEcommerceService[EcommercePayment]):
    """Service de gestion des paiements."""

    model = EcommercePayment

    def create(
        self,
        order_id: int,
        amount: Decimal,
        provider: str = "stripe",
        payment_method: str = "card",
    ) -> EcommercePayment:
        """Crée un paiement."""
        payment = EcommercePayment(
            tenant_id=self.tenant_id,
            order_id=order_id,
            amount=amount,
            currency="EUR",
            provider=provider,
            payment_method=payment_method,
            status=PaymentStatus.PENDING,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get(self, payment_id: int) -> Optional[EcommercePayment]:
        """Récupère un paiement."""
        return self._get_by_id(payment_id)

    def confirm(
        self,
        payment_id: int,
        external_id: str,
        card_brand: Optional[str] = None,
        card_last4: Optional[str] = None,
    ) -> Optional[EcommercePayment]:
        """Confirme un paiement."""
        payment = self.get(payment_id)
        if not payment:
            return None

        payment.status = PaymentStatus.CAPTURED
        payment.external_id = external_id
        payment.card_brand = card_brand
        payment.card_last4 = card_last4
        payment.captured_at = datetime.utcnow()

        # Mettre à jour la commande
        order = (
            self.db.query(EcommerceOrder)
            .filter(
                EcommerceOrder.tenant_id == self.tenant_id,
                EcommerceOrder.id == payment.order_id,
            )
            .first()
        )
        if order:
            order.payment_status = PaymentStatus.CAPTURED
            order.paid_at = datetime.utcnow()
            order.status = OrderStatus.CONFIRMED

        self.db.commit()
        self.db.refresh(payment)

        logger.info(
            "Payment confirmed | payment_id=%s order_id=%s amount=%s",
            payment_id,
            payment.order_id,
            payment.amount,
        )
        return payment

    def fail(
        self,
        payment_id: int,
        error_code: str,
        error_message: str,
    ) -> Optional[EcommercePayment]:
        """Marque un paiement comme échoué."""
        payment = self.get(payment_id)
        if not payment:
            return None

        payment.status = PaymentStatus.FAILED
        payment.error_code = error_code
        payment.error_message = error_message
        payment.failed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payment)

        logger.warning(
            "Payment failed | payment_id=%s error=%s",
            payment_id,
            error_code,
        )
        return payment

    def refund(
        self,
        payment_id: int,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> Optional[EcommercePayment]:
        """Rembourse un paiement."""
        payment = self.get(payment_id)
        if not payment:
            return None

        if payment.status != PaymentStatus.CAPTURED:
            logger.warning(
                "Refund failed | payment_id=%s status=%s",
                payment_id,
                payment.status,
            )
            return None

        refund_amount = amount or payment.amount
        payment.refund_amount = refund_amount
        payment.refund_reason = reason
        payment.refunded_at = datetime.utcnow()

        if refund_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        # Mettre à jour la commande
        order = (
            self.db.query(EcommerceOrder)
            .filter(
                EcommerceOrder.tenant_id == self.tenant_id,
                EcommerceOrder.id == payment.order_id,
            )
            .first()
        )
        if order:
            order.payment_status = payment.status
            if payment.status == PaymentStatus.REFUNDED:
                order.status = OrderStatus.REFUNDED
                order.refunded_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payment)

        logger.info(
            "Payment refunded | payment_id=%s amount=%s",
            payment_id,
            refund_amount,
        )
        return payment
