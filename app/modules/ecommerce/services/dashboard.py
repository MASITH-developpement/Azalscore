"""
AZALS MODULE 12 - E-Commerce Dashboard Service
================================================

Statistiques et analytics e-commerce.
"""
from __future__ import annotations


import logging
from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import desc, func

from app.modules.ecommerce.models import (
    CartStatus,
    EcommerceCart,
    EcommerceCustomer,
    EcommerceOrder,
    EcommerceProduct,
    PaymentStatus,
    ProductStatus,
)

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class DashboardService(BaseEcommerceService[EcommerceOrder]):
    """Service de statistiques e-commerce."""

    model = EcommerceOrder

    def get_stats(self) -> dict:
        """Obtient les statistiques globales du dashboard."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Commandes
        total_orders = self._base_query().count()

        orders_today = (
            self._base_query()
            .filter(EcommerceOrder.created_at >= today_start)
            .count()
        )

        orders_this_month = (
            self._base_query()
            .filter(EcommerceOrder.created_at >= month_start)
            .count()
        )

        # Revenus
        total_revenue = self._get_revenue()
        revenue_today = self._get_revenue(since=today_start)
        revenue_this_month = self._get_revenue(since=month_start)

        # Produits
        product_stats = self._get_product_stats()

        # Clients
        customer_stats = self._get_customer_stats(month_start)

        # Paniers
        cart_stats = self._get_cart_stats()

        # Valeur moyenne commande
        avg_order_value = (
            (total_revenue / total_orders) if total_orders > 0 else Decimal("0")
        )

        return {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "average_order_value": float(avg_order_value),
            "revenue_today": float(revenue_today),
            "orders_today": orders_today,
            "revenue_this_month": float(revenue_this_month),
            "orders_this_month": orders_this_month,
            **product_stats,
            **customer_stats,
            **cart_stats,
        }

    def _get_revenue(self, since: datetime = None) -> Decimal:
        """Calcule le revenu total."""
        query = (
            self.db.query(func.coalesce(func.sum(EcommerceOrder.total), 0))
            .filter(
                EcommerceOrder.tenant_id == self.tenant_id,
                EcommerceOrder.payment_status == PaymentStatus.CAPTURED,
            )
        )

        if since:
            query = query.filter(EcommerceOrder.created_at >= since)

        return query.scalar() or Decimal("0")

    def _get_product_stats(self) -> dict:
        """Statistiques des produits."""
        base_query = self.db.query(EcommerceProduct).filter(
            EcommerceProduct.tenant_id == self.tenant_id
        )

        total_products = base_query.count()

        active_products = base_query.filter(
            EcommerceProduct.status == ProductStatus.ACTIVE
        ).count()

        out_of_stock = base_query.filter(
            EcommerceProduct.stock_quantity <= 0,
            EcommerceProduct.track_inventory == True,
        ).count()

        low_stock = base_query.filter(
            EcommerceProduct.stock_quantity > 0,
            EcommerceProduct.stock_quantity <= EcommerceProduct.low_stock_threshold,
            EcommerceProduct.track_inventory == True,
        ).count()

        return {
            "total_products": total_products,
            "active_products": active_products,
            "out_of_stock_products": out_of_stock,
            "low_stock_products": low_stock,
        }

    def _get_customer_stats(self, month_start: datetime) -> dict:
        """Statistiques des clients."""
        base_query = self.db.query(EcommerceCustomer).filter(
            EcommerceCustomer.tenant_id == self.tenant_id
        )

        total_customers = base_query.count()

        new_customers = base_query.filter(
            EcommerceCustomer.created_at >= month_start
        ).count()

        return {
            "total_customers": total_customers,
            "new_customers_this_month": new_customers,
        }

    def _get_cart_stats(self) -> dict:
        """Statistiques des paniers."""
        base_query = self.db.query(EcommerceCart).filter(
            EcommerceCart.tenant_id == self.tenant_id
        )

        active_carts = base_query.filter(
            EcommerceCart.status == CartStatus.ACTIVE
        ).count()

        abandoned_carts = base_query.filter(
            EcommerceCart.status == CartStatus.ABANDONED
        ).count()

        total_carts = active_carts + abandoned_carts
        abandonment_rate = (
            (abandoned_carts / total_carts * 100) if total_carts > 0 else 0
        )

        return {
            "active_carts": active_carts,
            "abandoned_carts": abandoned_carts,
            "cart_abandonment_rate": round(abandonment_rate, 2),
        }

    def get_top_selling_products(self, limit: int = 10) -> List[dict]:
        """Obtient les produits les plus vendus."""
        products = (
            self.db.query(EcommerceProduct)
            .filter(
                EcommerceProduct.tenant_id == self.tenant_id,
                EcommerceProduct.sale_count > 0,
            )
            .order_by(desc(EcommerceProduct.sale_count))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "sale_count": p.sale_count,
                "revenue": float(p.price * p.sale_count),
            }
            for p in products
        ]

    def get_recent_orders(self, limit: int = 10) -> List[dict]:
        """Obtient les commandes récentes."""
        orders = (
            self._base_query()
            .order_by(desc(EcommerceOrder.created_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": o.id,
                "order_number": o.order_number,
                "customer_email": o.customer_email,
                "total": float(o.total),
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ]

    def get_sales_by_period(
        self,
        period: str = "day",
        limit: int = 30,
    ) -> List[dict]:
        """
        Obtient les ventes par période.

        Args:
            period: "day", "week", "month"
            limit: Nombre de périodes à retourner

        Returns:
            Liste des ventes par période
        """
        if period == "day":
            date_trunc = func.date_trunc("day", EcommerceOrder.created_at)
        elif period == "week":
            date_trunc = func.date_trunc("week", EcommerceOrder.created_at)
        else:
            date_trunc = func.date_trunc("month", EcommerceOrder.created_at)

        results = (
            self.db.query(
                date_trunc.label("period"),
                func.count(EcommerceOrder.id).label("order_count"),
                func.sum(EcommerceOrder.total).label("revenue"),
            )
            .filter(
                EcommerceOrder.tenant_id == self.tenant_id,
                EcommerceOrder.payment_status == PaymentStatus.CAPTURED,
            )
            .group_by(date_trunc)
            .order_by(desc(date_trunc))
            .limit(limit)
            .all()
        )

        return [
            {
                "period": r.period.isoformat() if r.period else None,
                "order_count": r.order_count,
                "revenue": float(r.revenue or 0),
            }
            for r in results
        ]
