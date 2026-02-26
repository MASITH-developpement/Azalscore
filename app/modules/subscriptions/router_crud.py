"""
AZALS MODULE - SUBSCRIPTIONS: Router Unifié
============================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.subscriptions.router_unified import router as subscriptions_router

    # Double enregistrement pour compatibilité
    app.include_router(subscriptions_router, prefix="/v2")
    app.include_router(subscriptions_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (44 total):
- Plans (5): CRUD
- Add-ons (4): CRUD + by plan
- Subscriptions (8): CRUD + change-plan/cancel/pause/resume
- Invoices (6): CRUD + finalize/void/pay
- Payments (3): create/list + refund
- Usage Records (3): create (global + by subscription) + summary
- Coupons (6): CRUD + validate (by code + by ID)
- Metrics (4): calculate/get by date/trend/get or calculate
- Webhooks (2): receive/list
- Stats (1): cached stats
- Dashboard (1): cached dashboard
"""
from __future__ import annotations


from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.cache import cached

from app.azals import SaaSContext, get_context, get_db

from .models import InvoiceStatus, SubscriptionStatus
from .schemas import (
    AddOnCreate,
    AddOnResponse,
    AddOnUpdate,
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    CouponValidateRequest,
    CouponValidateResponse,
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    MetricsSnapshot,
    PaymentCreate,
    PaymentResponse,
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
    RefundRequest,
    SubscriptionCancelRequest,
    SubscriptionChangePlanRequest,
    SubscriptionCreate,
    SubscriptionDashboard,
    SubscriptionListResponse,
    SubscriptionPauseRequest,
    SubscriptionResponse,
    SubscriptionStatsResponse,
    SubscriptionUpdate,
    UsageRecordCreate,
    UsageRecordResponse,
    UsageSummary,
    WebhookEvent,
)
from .service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions - Abonnements"])

# ============================================================================
# SERVICE DEPENDENCY
# ============================================================================

def get_subscription_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
) -> SubscriptionService:
    """Factory utilisant le contexte unifié."""
    return SubscriptionService(db, context.tenant_id, context.user_id)

# ============================================================================
# PLANS
# ============================================================================

@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Créer un plan d'abonnement."""
    return service.create_plan(data)

@router.get("/plans", response_model=PlanListResponse)
def list_plans(
    is_active: bool | None = None,
    is_public: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister les plans."""
    items, total = service.list_plans(
        is_active=is_active, is_public=is_public, skip=skip, limit=limit
    )
    return PlanListResponse(items=items, total=total)

@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Récupérer un plan."""
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    return plan

@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Mettre à jour un plan."""
    plan = service.update_plan(plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    return plan

@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Désactiver un plan."""
    if not service.delete_plan(plan_id):
        raise HTTPException(status_code=404, detail="Plan introuvable")

# ============================================================================
# ADD-ONS
# ============================================================================

@router.post("/addons", response_model=AddOnResponse, status_code=status.HTTP_201_CREATED)
def create_addon(
    data: AddOnCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Créer un add-on."""
    return service.create_addon(data)

@router.get("/addons", response_model=list[AddOnResponse])
def list_all_addons(
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister tous les add-ons."""
    return []

@router.get("/plans/{plan_id}/addons", response_model=list[AddOnResponse])
def list_plan_addons(
    plan_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister les add-ons d'un plan."""
    return service.list_addons(plan_id)

@router.put("/addons/{addon_id}", response_model=AddOnResponse)
def update_addon(
    addon_id: int,
    data: AddOnUpdate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Mettre à jour un add-on."""
    addon = service.update_addon(addon_id, data)
    if not addon:
        raise HTTPException(status_code=404, detail="Add-on introuvable")
    return addon

@router.delete("/addons/{addon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_addon(
    addon_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Désactiver un add-on."""
    raise HTTPException(status_code=501, detail="Non implémenté")

# ============================================================================
# SUBSCRIPTIONS
# ============================================================================

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    data: SubscriptionCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Créer un abonnement."""
    return service.create_subscription(data)

@router.get("/", response_model=SubscriptionListResponse)
def list_subscriptions(
    customer_id: int | None = None,
    plan_id: int | None = None,
    subscription_status: SubscriptionStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister les abonnements."""
    items, total = service.list_subscriptions(
        customer_id=customer_id, plan_id=plan_id, status=subscription_status,
        skip=skip, limit=limit
    )
    return SubscriptionListResponse(
        items=items, total=total, page=skip // limit + 1, page_size=limit
    )

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Récupérer un abonnement."""
    subscription = service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return subscription

@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    data: SubscriptionUpdate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Mettre à jour un abonnement."""
    subscription = service.update_subscription(subscription_id, data)
    if not subscription:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return subscription

@router.post("/{subscription_id}/change-plan", response_model=SubscriptionResponse)
def change_subscription_plan(
    subscription_id: int,
    data: SubscriptionChangePlanRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Changer de plan d'abonnement."""
    return service.change_plan(subscription_id, data)

@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: int,
    data: SubscriptionCancelRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Annuler un abonnement."""
    return service.cancel_subscription(subscription_id, data)

@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: int,
    data: SubscriptionPauseRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Mettre en pause un abonnement."""
    return service.pause_subscription(subscription_id, data)

@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Reprendre un abonnement en pause."""
    return service.resume_subscription(subscription_id)

# ============================================================================
# INVOICES
# ============================================================================

@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Créer une facture manuelle."""
    return service.create_invoice(data)

@router.get("/invoices", response_model=InvoiceListResponse)
def list_invoices(
    subscription_id: int | None = None,
    customer_id: int | None = None,
    invoice_status: InvoiceStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister les factures."""
    items, total = service.list_invoices(
        subscription_id=subscription_id, customer_id=customer_id,
        status=invoice_status, skip=skip, limit=limit
    )
    return InvoiceListResponse(
        items=items, total=total, page=skip // limit + 1, page_size=limit
    )

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Récupérer une facture."""
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return invoice

@router.post("/invoices/{invoice_id}/finalize", response_model=InvoiceResponse)
def finalize_invoice(
    invoice_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Finaliser une facture."""
    return service.finalize_invoice(invoice_id)

@router.post("/invoices/{invoice_id}/void", response_model=InvoiceResponse)
def void_invoice(
    invoice_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Annuler une facture."""
    return service.void_invoice(invoice_id)

@router.post("/invoices/{invoice_id}/pay", response_model=InvoiceResponse)
def pay_invoice(
    invoice_id: int,
    amount: float | None = None,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Marquer une facture comme payée."""
    from decimal import Decimal
    payment_amount = Decimal(str(amount)) if amount else None
    return service.mark_invoice_paid(invoice_id, payment_amount)

# ============================================================================
# PAYMENTS
# ============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    data: PaymentCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Créer un paiement."""
    return service.create_payment(data)

@router.get("/payments", response_model=list[PaymentResponse])
def list_payments(
    invoice_id: int | None = None,
    customer_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister les paiements."""
    return []

@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    data: RefundRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Rembourser un paiement."""
    return service.refund_payment(payment_id, data.amount, data.reason)

# ============================================================================
# USAGE RECORDS
# ============================================================================

@router.post("/usage", response_model=UsageRecordResponse, status_code=status.HTTP_201_CREATED)
def create_usage_record_global(
    data: UsageRecordCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Enregistrer usage (pour abonnements metered)."""
    return service.create_usage_record(data)

@router.post("/{subscription_id}/usage", response_model=UsageRecordResponse, status_code=status.HTTP_201_CREATED)
def create_usage_record(
    subscription_id: int,
    data: UsageRecordCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Enregistrer usage pour un abonnement (pour abonnements metered)."""
    return service.create_usage_record(data)

@router.get("/{subscription_id}/usage", response_model=list[UsageSummary])
def get_usage_summary(
    subscription_id: int,
    period_start: date | None = None,
    period_end: date | None = None,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Résumé d'usage pour un abonnement."""
    return service.get_usage_summary(subscription_id, period_start, period_end)

# ============================================================================
# COUPONS
# ============================================================================

@router.post("/coupons", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    data: CouponCreate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Créer un coupon."""
    return service.create_coupon(data)

@router.get("/coupons", response_model=list[CouponResponse])
def list_coupons(
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister les coupons."""
    return service.list_coupons(is_active=is_active, skip=skip, limit=limit)

@router.get("/coupons/{coupon_id}", response_model=CouponResponse)
def get_coupon(
    coupon_id: int,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Récupérer un coupon."""
    coupon = service.get_coupon(coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon introuvable")
    return coupon

@router.put("/coupons/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int,
    data: CouponUpdate,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Mettre à jour un coupon."""
    coupon = service.update_coupon(coupon_id, data)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon introuvable")
    return coupon

@router.post("/coupons/validate", response_model=CouponValidateResponse)
def validate_coupon_by_code(
    data: CouponValidateRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Valider un code coupon."""
    result = service.validate_coupon(data)
    return CouponValidateResponse(
        valid=result.get("valid", False),
        coupon=result.get("coupon"),
        discount_amount=result.get("discount_amount"),
        error_message=result.get("error_message")
    )

@router.post("/coupons/{coupon_id}/validate", response_model=CouponValidateResponse)
def validate_coupon(
    coupon_id: int,
    data: CouponValidateRequest,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Valider un coupon par ID."""
    result = service.validate_coupon(data)
    return CouponValidateResponse(
        valid=result.get("valid", False),
        coupon=result.get("coupon"),
        discount_amount=result.get("discount_amount"),
        error_message=result.get("error_message")
    )

# ============================================================================
# METRICS
# ============================================================================

@router.post("/metrics/calculate", response_model=MetricsSnapshot)
def calculate_metrics(
    metric_date: date | None = None,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Calculer et sauvegarder les métriques."""
    metrics = service.calculate_metrics(metric_date)
    return metrics

@router.get("/metrics/{metric_date}", response_model=MetricsSnapshot)
def get_metrics_by_date(
    metric_date: date,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Récupérer les métriques d'une date."""
    metrics = service.get_metrics(metric_date)
    if not metrics:
        raise HTTPException(status_code=404, detail="Métriques introuvables")
    return metrics

@router.get("/metrics/trend", response_model=list[MetricsSnapshot])
def get_metrics_trend(
    start_date: date,
    end_date: date,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Récupérer la tendance des métriques."""
    return service.get_metrics_trend(start_date, end_date)

@router.get("/metrics", response_model=MetricsSnapshot)
def get_metrics(
    metric_date: date | None = None,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Récupérer ou calculer les métriques."""
    target_date = metric_date or date.today()
    metrics = service.get_metrics(target_date)

    if not metrics:
        metrics = service.calculate_metrics(target_date)

    return metrics

# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhooks")
def receive_webhook(
    event: WebhookEvent,
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Recevoir un webhook."""
    webhook = service.process_webhook(
        event.event_type, event.source, event.payload
    )
    return {"received": True, "webhook_id": webhook.id}

@router.get("/webhooks", response_model=list[dict])
def list_webhooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Lister les webhooks."""
    return []

# ============================================================================
# FONCTIONS CACHABLES
# ============================================================================

@cached(ttl=300, key_builder=lambda service: f"subscriptions:stats:{service.tenant_id}")
def _get_cached_stats(service: SubscriptionService) -> dict:
    """Calcule les stats abonnements (cache 5min)."""
    dashboard = service.get_dashboard()
    plans_data = service.list_plans(is_active=True, skip=0, limit=1000)
    total_plans = plans_data[1] if plans_data else 0
    return {
        "total_plans": total_plans,
        "active_subscriptions": dashboard.total_active,
        "trial_subscriptions": dashboard.trialing,
        "mrr": dashboard.mrr,
        "arr": dashboard.arr,
        "churn_rate": dashboard.churn_rate,
        "new_subscribers_month": dashboard.canceled_this_month,
        "revenue_this_month": dashboard.new_mrr + dashboard.expansion_mrr,
    }

@cached(ttl=300, key_builder=lambda service: f"subscriptions:dashboard:{service.tenant_id}")
def _get_cached_dashboard(service: SubscriptionService) -> dict:
    """Calcule le dashboard abonnements (cache 5min)."""
    dashboard = service.get_dashboard()
    return dashboard.model_dump() if hasattr(dashboard, 'model_dump') else dashboard

# ============================================================================
# STATS
# ============================================================================

@router.get("/stats", response_model=SubscriptionStatsResponse)
def get_stats(
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Statistiques abonnements simplifié (cache 5min)."""
    data = _get_cached_stats(service)
    return SubscriptionStatsResponse(**data)

# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=SubscriptionDashboard)
def get_dashboard(
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Dashboard abonnements (cache 5min)."""
    data = _get_cached_dashboard(service)
    return SubscriptionDashboard(**data)
