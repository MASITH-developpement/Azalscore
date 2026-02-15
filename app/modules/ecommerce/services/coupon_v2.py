"""
AZALS MODULE 12 - E-Commerce Coupon Service (v2 - CRUDRouter compatible)
=========================================================================

Version compatible avec BaseService et CRUDRouter.

DIFFÉRENCES avec coupon.py:
- Hérite de BaseService au lieu de BaseEcommerceService
- Accepte SaaSContext au lieu de tenant_id
- Retourne Result[T] au lieu de T directement
- Prêt pour CRUDRouter (auto-génération CRUD)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.ecommerce.models import Coupon
from app.modules.ecommerce.schemas import CouponCreate, CouponUpdate

logger = logging.getLogger(__name__)


class CouponServiceV2(BaseService[Coupon, CouponCreate, CouponUpdate]):
    """
    Service de gestion des coupons - compatible CRUDRouter.

    Les méthodes CRUD héritées de BaseService:
    - get(id) -> Optional[Coupon]
    - get_or_fail(id) -> Result[Coupon]
    - list(page, page_size, filters) -> PaginatedResponse[Coupon]
    - create(data) -> Result[Coupon]
    - update(id, data) -> Result[Coupon]
    - delete(id, soft) -> Result[bool]

    Méthodes métier spécifiques ci-dessous.
    """

    model = Coupon

    # Surcharge de create pour la logique métier spécifique
    def create(self, data: CouponCreate) -> Result[Coupon]:
        """
        Crée un coupon avec validation métier.

        Args:
            data: Données du coupon

        Returns:
            Result avec le coupon créé ou erreur
        """
        # Validation: code unique
        existing = self.get_by_code(data.code)
        if existing:
            return Result.fail(
                f"Code promo '{data.code}' existe déjà",
                error_code="DUPLICATE"
            )

        # Validation: dates cohérentes
        if data.starts_at and data.expires_at:
            if data.expires_at <= data.starts_at:
                return Result.fail(
                    "La date d'expiration doit être postérieure au début",
                    error_code="VALIDATION"
                )

        # Créer avec code en majuscules
        coupon_data = data.model_dump()
        coupon_data["code"] = coupon_data["code"].upper()

        coupon = Coupon(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            **coupon_data,
        )

        created = self.repo.create(coupon)

        self._logger.info(
            "Coupon created",
            extra={"coupon_id": str(created.id), "code": created.code}
        )

        return Result.ok(created)

    # =========================================================================
    # MÉTHODES MÉTIER SPÉCIFIQUES
    # =========================================================================

    def get_by_code(self, code: str) -> Optional[Coupon]:
        """
        Récupère un coupon par code.

        Args:
            code: Code promo

        Returns:
            Coupon ou None
        """
        return (
            self.db.query(Coupon)
            .filter(
                Coupon.tenant_id == self.tenant_id,
                Coupon.code == code.upper(),
            )
            .first()
        )

    def validate(self, code: str, cart_subtotal) -> Result[Coupon]:
        """
        Valide un code promo pour un montant de panier.

        Args:
            code: Code promo
            cart_subtotal: Sous-total du panier

        Returns:
            Result avec le coupon si valide
        """
        coupon = self.get_by_code(code)

        if not coupon:
            return Result.fail("Code promo invalide", error_code="NOT_FOUND")

        if not coupon.is_active:
            return Result.fail("Code promo inactif", error_code="INVALID")

        now = datetime.utcnow()
        if coupon.starts_at and now < coupon.starts_at:
            return Result.fail("Code promo pas encore actif", error_code="INVALID")

        if coupon.expires_at and now > coupon.expires_at:
            return Result.fail("Code promo expiré", error_code="INVALID")

        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            return Result.fail("Code promo épuisé", error_code="INVALID")

        if coupon.min_order_amount and cart_subtotal < coupon.min_order_amount:
            return Result.fail(
                f"Montant minimum requis: {coupon.min_order_amount}€",
                error_code="VALIDATION"
            )

        return Result.ok(coupon)

    def increment_usage(self, coupon_id) -> Result[Coupon]:
        """
        Incrémente le compteur d'utilisation.

        Args:
            coupon_id: ID du coupon

        Returns:
            Result avec le coupon mis à jour
        """
        result = self.get_or_fail(coupon_id)
        if not result.success:
            return result

        coupon = result.data
        coupon.usage_count = (coupon.usage_count or 0) + 1

        self.db.commit()
        self.db.refresh(coupon)

        return Result.ok(coupon)

    def list_active(self) -> List[Coupon]:
        """
        Liste les coupons actifs.

        Returns:
            Liste des coupons actifs
        """
        return (
            self.db.query(Coupon)
            .filter(
                Coupon.tenant_id == self.tenant_id,
                Coupon.is_active == True,
            )
            .order_by(Coupon.created_at.desc())
            .all()
        )


# =============================================================================
# EXEMPLE D'UTILISATION AVEC CRUDROUTER
# =============================================================================
"""
Dans router_unified.py, on peut maintenant faire:

from app.core.base_router import CRUDRouter
from app.modules.ecommerce.services.coupon_v2 import CouponServiceV2
from app.modules.ecommerce.schemas import CouponCreate, CouponUpdate, CouponResponse

# Auto-génère POST, GET, PUT, DELETE, LIST pour /coupons
coupons_router = CRUDRouter.create_crud_router(
    service_class=CouponServiceV2,
    resource_name="coupon",
    plural_name="coupons",
    create_schema=CouponCreate,
    update_schema=CouponUpdate,
    response_schema=CouponResponse,
    tags=["E-Commerce - Coupons"],
)

# Ajouter les endpoints métier personnalisés
@coupons_router.post("/validate")
async def validate_coupon(
    code: str,
    cart_subtotal: Decimal,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = CouponServiceV2(db, context)
    result = service.validate(code, cart_subtotal)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return {"valid": True, "coupon": result.data}

# Le router final:
router.include_router(coupons_router)

RÉSULTAT: ~80 lignes de CRUD → ~15 lignes!
"""
