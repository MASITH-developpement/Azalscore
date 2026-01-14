"""
AZALS - Module Marketplace - Router
===================================
Endpoints API pour le site marchand.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

from .models import OrderStatus
from .schemas import (
    CheckoutRequest,
    CheckoutResponse,
    CommercialPlanResponse,
    DiscountCodeResponse,
    DiscountCodeValidate,
    MarketplaceDashboard,
    OrderDetail,
    OrderResponse,
    TenantProvisionRequest,
    TenantProvisionResponse,
)
from .service import get_marketplace_service

router = APIRouter(prefix="/marketplace", tags=["Site Marchand"])


def get_service(db: Session = Depends(get_db)):
    return get_marketplace_service(db)


# ============================================================================
# PLANS (PUBLIC)
# ============================================================================

@router.get("/plans", response_model=list[CommercialPlanResponse])
def list_plans(service = Depends(get_service)):
    """Liste les plans commerciaux disponibles."""
    return service.get_plans()


@router.get("/plans/{plan_code}", response_model=CommercialPlanResponse)
def get_plan(plan_code: str, service = Depends(get_service)):
    """Récupère un plan par code."""
    plan = service.get_plan_by_code(plan_code)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouvé")
    return plan


@router.post("/plans/seed")
def seed_plans(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Initialise les plans par défaut (admin only)."""
    service.seed_default_plans()
    return {"status": "Plans créés"}


# ============================================================================
# CHECKOUT (PUBLIC)
# ============================================================================

@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    data: CheckoutRequest,
    request: Request,
    service = Depends(get_service)
):
    """Crée une session de checkout."""
    if not data.accept_terms or not data.accept_privacy:
        raise HTTPException(
            status_code=400,
            detail="Vous devez accepter les CGV et la politique de confidentialité"
        )

    try:
        return service.create_checkout(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discount/validate", response_model=DiscountCodeResponse)
def validate_discount(data: DiscountCodeValidate, service = Depends(get_service)):
    """Valide un code promo."""
    return service.validate_discount_code(data.code, data.plan_code, data.order_amount)


# ============================================================================
# COMMANDES
# ============================================================================

@router.get("/orders", response_model=list[OrderResponse])
def list_orders(
    status: OrderStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Liste les commandes (admin)."""
    items, _ = service.list_orders(status, skip, limit)
    return items


@router.get("/orders/{order_id}", response_model=OrderDetail)
def get_order(
    order_id: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Récupère une commande."""
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


@router.get("/orders/number/{order_number}", response_model=OrderResponse)
def get_order_by_number(order_number: str, service = Depends(get_service)):
    """Récupère une commande par numéro (public pour suivi)."""
    order = service.get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


# ============================================================================
# PROVISIONING
# ============================================================================

@router.post("/provision", response_model=TenantProvisionResponse)
def provision_tenant(
    data: TenantProvisionRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Provisionne un tenant pour une commande payée (admin)."""
    try:
        return service.provision_tenant_for_order(data.order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, service = Depends(get_service)):
    """Webhook Stripe pour les événements de paiement."""
    payload = await request.json()
    signature = request.headers.get("stripe-signature")

    event_id = payload.get("id")
    event_type = payload.get("type")

    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Payload invalide")

    try:
        service.process_stripe_webhook(event_id, event_type, payload, signature)
        return {"received": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DASHBOARD (ADMIN)
# ============================================================================

@router.get("/dashboard", response_model=MarketplaceDashboard)
def get_dashboard(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Dashboard marketplace (admin)."""
    stats = service.get_stats()
    orders, _ = service.list_orders(limit=10)
    plans = service.get_plans()

    return MarketplaceDashboard(
        stats=stats,
        recent_orders=[OrderResponse.model_validate(o) for o in orders],
        popular_plans=[CommercialPlanResponse.model_validate(p) for p in plans[:3]]
    )
