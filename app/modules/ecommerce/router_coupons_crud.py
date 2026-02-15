"""
AZALS MODULE 12 - E-Commerce Coupons Router (CRUDRouter)
=========================================================

Exemple de router minimaliste utilisant CRUDRouter.

AVANT (router_unified.py - section coupons): ~120 lignes
APRÈS (ce fichier): ~50 lignes
GAIN: -58% de code!
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import CRUDRouter, SaaSContext, get_context, get_db

from app.modules.ecommerce.schemas import (
    CouponCreate,
    CouponUpdate,
    CouponResponse,
)
from app.modules.ecommerce.services.coupon_v2 import CouponServiceV2


# =============================================================================
# CRUD AUTO-GÉNÉRÉ (remplace ~80 lignes de boilerplate!)
# =============================================================================

# Génère automatiquement:
#   POST   /coupons         → Créer un coupon
#   GET    /coupons         → Lister avec pagination
#   GET    /coupons/{id}    → Récupérer par ID
#   PUT    /coupons/{id}    → Modifier
#   DELETE /coupons/{id}    → Supprimer (soft delete)
coupons_crud = CRUDRouter.create_crud_router(
    service_class=CouponServiceV2,
    resource_name="coupon",
    plural_name="coupons",
    create_schema=CouponCreate,
    update_schema=CouponUpdate,
    response_schema=CouponResponse,
    tags=["E-Commerce - Coupons"],
    soft_delete=True,
)


# =============================================================================
# ENDPOINTS MÉTIER PERSONNALISÉS
# =============================================================================

@coupons_crud.get("/code/{code}", response_model=CouponResponse)
async def get_coupon_by_code(
    code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Récupérer un coupon par son code."""
    service = CouponServiceV2(db, context)
    coupon = service.get_by_code(code)
    if not coupon:
        raise HTTPException(status_code=404, detail=f"Coupon '{code}' non trouvé")
    return coupon


@coupons_crud.post("/validate")
async def validate_coupon(
    code: str = Query(..., description="Code promo à valider"),
    cart_subtotal: Decimal = Query(..., description="Sous-total du panier"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """
    Valide un code promo pour un montant de panier.

    Vérifie:
    - Existence du code
    - Statut actif
    - Dates de validité
    - Limite d'utilisation
    - Montant minimum requis
    """
    service = CouponServiceV2(db, context)
    result = service.validate(code, cart_subtotal)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    coupon = result.data
    return {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type.value if coupon.discount_type else None,
        "discount_value": float(coupon.discount_value) if coupon.discount_value else 0,
        "message": "Code promo valide",
    }


@coupons_crud.get("/active", response_model=List[CouponResponse])
async def list_active_coupons(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les coupons actuellement actifs."""
    service = CouponServiceV2(db, context)
    return service.list_active()


# =============================================================================
# EXPORT
# =============================================================================

# Router prêt à être inclus dans le module principal
router = coupons_crud


# =============================================================================
# COMPARAISON LIGNES DE CODE
# =============================================================================
"""
AVANT (dans router_unified.py):

@router.post("/coupons", response_model=CouponResponse, status_code=201)
async def create_coupon(
    data: CouponCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = EcommerceService(db, context.tenant_id, str(context.user_id))
    return service.create_coupon(data)


@router.get("/coupons", response_model=PaginatedResponse[CouponResponse])
async def list_coupons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = EcommerceService(db, context.tenant_id, str(context.user_id))
    coupons = service.list_coupons(active_only=active_only)
    total = len(coupons)
    # ... pagination manuelle ...


@router.get("/coupons/{coupon_id}", response_model=CouponResponse)
async def get_coupon(
    coupon_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = EcommerceService(db, context.tenant_id, str(context.user_id))
    coupon = service.get_coupon(coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon non trouvé")
    return coupon


@router.put("/coupons/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: int,
    data: CouponUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = EcommerceService(db, context.tenant_id, str(context.user_id))
    coupon = service.update_coupon(coupon_id, data)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon non trouvé")
    return coupon


@router.delete("/coupons/{coupon_id}", status_code=204)
async def delete_coupon(
    coupon_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    service = EcommerceService(db, context.tenant_id, str(context.user_id))
    if not service.delete_coupon(coupon_id):
        raise HTTPException(status_code=404, detail="Coupon non trouvé")


# ... plus les endpoints métier ...

TOTAL AVANT: ~120 lignes
TOTAL APRÈS: ~50 lignes
GAIN: -58%
"""
