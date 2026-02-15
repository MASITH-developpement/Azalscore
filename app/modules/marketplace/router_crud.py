"""
AZALS - Module Marketplace - Router Unifié
===========================================

API unifiée pour le site marchand avec provisioning automatique.
Compatible v1 et v2 via double enregistrement.

Note: Ce module a une isolation tenant minimale car il gère
principalement des endpoints publics (plans, checkout).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.azals import get_db

from .service import MarketplaceService
from .models import OrderStatus
from .schemas import CheckoutRequest

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

def get_marketplace_service(db: Session, user_id: str = None) -> MarketplaceService:
    """Factory pour créer le service Marketplace."""
    return MarketplaceService(db, user_id)

# ============================================================================
# PLANS (PUBLIC)
# ============================================================================

@router.get("/plans")
async def get_plans(
    active_only: bool = Query(True, description="Filtrer plans actifs uniquement"),
    db: Session = Depends(get_db)
):
    """Lister les plans commerciaux disponibles."""
    service = get_marketplace_service(db)
    return service.get_plans(active_only)

@router.get("/plans/{plan_id}")
async def get_plan(
    plan_id: str,
    db: Session = Depends(get_db)
):
    """Récupérer un plan par ID."""
    service = get_marketplace_service(db)
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.get("/plans/code/{code}")
async def get_plan_by_code(
    code: str,
    db: Session = Depends(get_db)
):
    """Récupérer un plan par code."""
    service = get_marketplace_service(db)
    plan = service.get_plan_by_code(code)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{code}' not found")
    return plan

# ============================================================================
# CHECKOUT (PUBLIC)
# ============================================================================

@router.post("/checkout", status_code=201)
async def create_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """Créer une session de checkout."""
    service = get_marketplace_service(db)
    try:
        return service.create_checkout(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# DISCOUNT CODES (PUBLIC)
# ============================================================================

@router.post("/discount/validate")
async def validate_discount_code(
    code: str = Query(..., description="Code promo à valider"),
    plan_code: str = Query(..., description="Code du plan"),
    order_amount: float = Query(..., description="Montant de la commande"),
    db: Session = Depends(get_db)
):
    """Valider un code promo."""
    from decimal import Decimal
    service = get_marketplace_service(db)
    return service.validate_discount_code(code, plan_code, Decimal(str(order_amount)))

# ============================================================================
# ORDERS (ADMIN)
# ============================================================================

@router.get("/orders")
async def list_orders(
    status: OrderStatus | None = Query(None, description="Filtrer par statut"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lister les commandes (ADMIN)."""
    service = get_marketplace_service(db)
    orders, total = service.list_orders(status, skip, limit)
    return {"orders": orders, "total": total}

@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Récupérer une commande par ID."""
    service = get_marketplace_service(db)
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/orders/number/{order_number}")
async def get_order_by_number(
    order_number: str,
    db: Session = Depends(get_db)
):
    """Récupérer une commande par numéro."""
    service = get_marketplace_service(db)
    order = service.get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# ============================================================================
# PROVISIONING (ADMIN)
# ============================================================================

@router.post("/orders/{order_id}/provision")
async def provision_tenant_for_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Provisionner un tenant pour une commande payée."""
    service = get_marketplace_service(db)
    try:
        return service.provision_tenant_for_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# WEBHOOKS (STRIPE)
# ============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Endpoint webhook Stripe."""
    import json

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        event = json.loads(payload)
        event_id = event.get("id")
        event_type = event.get("type")

        service = get_marketplace_service(db)
        webhook = service.process_stripe_webhook(
            event_id, event_type, event, signature
        )

        return {"received": True, "webhook_id": webhook.id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

# ============================================================================
# STATISTICS (ADMIN)
# ============================================================================

@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db)
):
    """Statistiques marketplace (ADMIN)."""
    service = get_marketplace_service(db)
    return service.get_stats()

# ============================================================================
# SEED DATA (ADMIN)
# ============================================================================

@router.post("/seed/plans")
async def seed_default_plans(
    db: Session = Depends(get_db)
):
    """Créer les plans par défaut (ADMIN)."""
    service = get_marketplace_service(db)
    service.seed_default_plans()
    return {"message": "Default plans seeded successfully"}
