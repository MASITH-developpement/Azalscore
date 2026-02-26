"""
AZALS MODULE 15 - Stripe Dashboard Service
============================================

Analytics et statistiques Stripe.
"""
from __future__ import annotations


import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import (
    DisputeStatus,
    PaymentIntentStatus,
    RefundStatus,
    StripeDispute,
    StripePaymentIntent,
    StripeRefund,
)

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class DashboardService(BaseStripeService[StripePaymentIntent]):
    """Service d'analytics et dashboard Stripe."""

    model = StripePaymentIntent

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtient les statistiques du dashboard Stripe.

        Returns:
            Dictionnaire avec toutes les métriques
        """
        thirty_days_ago = self._now() - timedelta(days=30)

        # Volume 30 jours
        volume = (
            self.db.query(func.sum(StripePaymentIntent.amount_received))
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
                StripePaymentIntent.created_at >= thirty_days_ago,
            )
            .scalar()
            or Decimal("0")
        )

        # Paiements réussis
        successful = (
            self.db.query(StripePaymentIntent)
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
                StripePaymentIntent.created_at >= thirty_days_ago,
            )
            .count()
        )

        # Paiements échoués
        failed = (
            self.db.query(StripePaymentIntent)
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.status == PaymentIntentStatus.CANCELED,
                StripePaymentIntent.created_at >= thirty_days_ago,
            )
            .count()
        )

        # Remboursements
        refunds = (
            self.db.query(func.sum(StripeRefund.amount))
            .filter(
                StripeRefund.tenant_id == self.tenant_id,
                StripeRefund.status == RefundStatus.SUCCEEDED,
                StripeRefund.created_at >= thirty_days_ago,
            )
            .scalar()
            or Decimal("0")
        )

        # Litiges ouverts
        open_disputes = (
            self.db.query(StripeDispute)
            .filter(
                StripeDispute.tenant_id == self.tenant_id,
                StripeDispute.status.in_(
                    [DisputeStatus.NEEDS_RESPONSE, DisputeStatus.UNDER_REVIEW]
                ),
            )
            .count()
        )

        disputed_amount = (
            self.db.query(func.sum(StripeDispute.amount))
            .filter(
                StripeDispute.tenant_id == self.tenant_id,
                StripeDispute.status.in_(
                    [DisputeStatus.NEEDS_RESPONSE, DisputeStatus.UNDER_REVIEW]
                ),
            )
            .scalar()
            or Decimal("0")
        )

        # Taux de succès
        total_attempts = successful + failed
        success_rate = (
            (Decimal(str(successful)) / Decimal(str(total_attempts)) * 100)
            if total_attempts > 0
            else Decimal("0")
        )

        # Transaction moyenne
        avg_transaction = (
            volume / Decimal(str(successful)) if successful > 0 else Decimal("0")
        )

        # Récents paiements
        recent_payments = self._get_recent_payments(limit=5)

        # Récents remboursements
        recent_refunds = self._get_recent_refunds(limit=5)

        return {
            "total_volume_30d": float(volume),
            "successful_payments_30d": successful,
            "failed_payments_30d": failed,
            "refunds_30d": float(refunds),
            "success_rate": float(success_rate),
            "average_transaction": float(avg_transaction),
            "open_disputes": open_disputes,
            "disputed_amount": float(disputed_amount),
            "available_balance": 0,  # À récupérer via API Stripe
            "pending_balance": 0,
            "recent_payments": recent_payments,
            "recent_refunds": recent_refunds,
        }

    def _get_recent_payments(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Récupère les paiements récents."""
        payments = (
            self.db.query(StripePaymentIntent)
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
            )
            .order_by(StripePaymentIntent.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": p.id,
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ]

    def _get_recent_refunds(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Récupère les remboursements récents."""
        refunds = (
            self.db.query(StripeRefund)
            .filter(StripeRefund.tenant_id == self.tenant_id)
            .order_by(StripeRefund.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": r.id,
                "amount": float(r.amount),
                "currency": r.currency,
                "status": r.status.value,
                "created_at": r.created_at.isoformat(),
            }
            for r in refunds
        ]

    def get_volume_by_day(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtient le volume de paiements par jour.

        Args:
            days: Nombre de jours

        Returns:
            Liste de volumes par jour
        """
        start_date = self._now() - timedelta(days=days)

        results = (
            self.db.query(
                func.date_trunc("day", StripePaymentIntent.created_at).label("day"),
                func.sum(StripePaymentIntent.amount_received).label("volume"),
                func.count(StripePaymentIntent.id).label("count"),
            )
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
                StripePaymentIntent.created_at >= start_date,
            )
            .group_by(func.date_trunc("day", StripePaymentIntent.created_at))
            .order_by(func.date_trunc("day", StripePaymentIntent.created_at))
            .all()
        )

        return [
            {
                "date": r.day.isoformat() if r.day else None,
                "volume": float(r.volume or 0),
                "count": r.count,
            }
            for r in results
        ]

    def get_payment_methods_breakdown(self) -> List[Dict[str, Any]]:
        """
        Obtient la répartition par méthode de paiement.

        Returns:
            Liste avec volume par méthode
        """
        thirty_days_ago = self._now() - timedelta(days=30)

        results = (
            self.db.query(
                StripePaymentIntent.payment_method_types,
                func.sum(StripePaymentIntent.amount_received).label("volume"),
                func.count(StripePaymentIntent.id).label("count"),
            )
            .filter(
                StripePaymentIntent.tenant_id == self.tenant_id,
                StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
                StripePaymentIntent.created_at >= thirty_days_ago,
            )
            .group_by(StripePaymentIntent.payment_method_types)
            .all()
        )

        return [
            {
                "methods": r.payment_method_types or ["card"],
                "volume": float(r.volume or 0),
                "count": r.count,
            }
            for r in results
        ]
