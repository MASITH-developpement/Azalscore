"""
AZALS MODULE 12 - E-Commerce Coupon Service
=============================================

Gestion des codes promo.
"""

import logging
from typing import List, Optional

from sqlalchemy import desc

from app.modules.ecommerce.models import Coupon
from app.modules.ecommerce.schemas import CouponCreate, CouponUpdate

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class CouponService(BaseEcommerceService[Coupon]):
    """Service de gestion des coupons."""

    model = Coupon

    def create(self, data: CouponCreate) -> Coupon:
        """Crée un coupon."""
        coupon_data = data.model_dump()
        coupon_data["code"] = coupon_data["code"].upper()

        coupon = Coupon(
            tenant_id=self.tenant_id,
            **coupon_data,
        )
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def get(self, coupon_id: int) -> Optional[Coupon]:
        """Récupère un coupon par ID."""
        return self._get_by_id(coupon_id)

    def get_by_code(self, code: str) -> Optional[Coupon]:
        """Récupère un coupon par code."""
        return (
            self._base_query()
            .filter(Coupon.code == code.upper())
            .first()
        )

    def list(self, active_only: bool = True) -> List[Coupon]:
        """Liste les coupons."""
        query = self._base_query()

        if active_only:
            query = query.filter(Coupon.is_active == True)

        return query.order_by(desc(Coupon.created_at)).all()

    def update(
        self,
        coupon_id: int,
        data: CouponUpdate,
    ) -> Optional[Coupon]:
        """Met à jour un coupon."""
        coupon = self.get(coupon_id)
        if not coupon:
            return None

        return self._update(coupon, data.model_dump(exclude_unset=True))

    def delete(self, coupon_id: int) -> bool:
        """Désactive un coupon."""
        coupon = self.get(coupon_id)
        if not coupon:
            return False

        coupon.is_active = False
        self.db.commit()
        return True

    def validate(self, code: str, cart_subtotal) -> tuple[bool, str]:
        """
        Valide un code promo.

        Args:
            code: Code promo
            cart_subtotal: Sous-total du panier

        Returns:
            Tuple (is_valid, message)
        """
        from datetime import datetime

        coupon = self.get_by_code(code)

        if not coupon:
            return False, "Code promo invalide"

        if not coupon.is_active:
            return False, "Code promo inactif"

        now = datetime.utcnow()
        if coupon.starts_at and now < coupon.starts_at:
            return False, "Code promo pas encore actif"

        if coupon.expires_at and now > coupon.expires_at:
            return False, "Code promo expiré"

        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            return False, "Code promo épuisé"

        if coupon.min_order_amount and cart_subtotal < coupon.min_order_amount:
            return (
                False,
                f"Montant minimum requis: {coupon.min_order_amount}€",
            )

        return True, "Code promo valide"
