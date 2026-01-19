"""
AZALS MODULE 14 - Subscriptions Router
========================================
Endpoints API pour la gestion des abonnements.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_tenant_id

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
    SubscriptionUpdate,
    UsageRecordCreate,
    UsageRecordResponse,
    UsageSummary,
    WebhookEvent,
)
from .service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions - Abonnements"])


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> SubscriptionService:
    return SubscriptionService(db, tenant_id)


# ============================================================================
# PLANS
# ============================================================================

@router.post("/plans", response_model=PlanResponse, status_code=201)
def create_plan(
    data: PlanCreate,
    service: SubscriptionService = Depends(get_service)
):
    """Créer un plan d'abonnement."""
    try:
        return service.create_plan(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans", response_model=PlanListResponse)
def list_plans(
    is_active: bool | None = None,
    is_public: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: SubscriptionService = Depends(get_service)
):
    """Lister les plans."""
    items, total = service.list_plans(
        is_active=is_active, is_public=is_public, skip=skip, limit=limit
    )
    return PlanListResponse(items=items, total=total)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Récupérer un plan."""
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    return plan


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    service: SubscriptionService = Depends(get_service)
):
    """Mettre à jour un plan."""
    plan = service.update_plan(plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    return plan


@router.delete("/plans/{plan_id}", status_code=204)
def delete_plan(
    plan_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Désactiver un plan."""
    try:
        if not service.delete_plan(plan_id):
            raise HTTPException(status_code=404, detail="Plan introuvable")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ADD-ONS
# ============================================================================

@router.post("/addons", response_model=AddOnResponse, status_code=201)
def create_addon(
    data: AddOnCreate,
    service: SubscriptionService = Depends(get_service)
):
    """Créer un add-on."""
    try:
        return service.create_addon(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans/{plan_id}/addons", response_model=list[AddOnResponse])
def list_addons(
    plan_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Lister les add-ons d'un plan."""
    return service.list_addons(plan_id)


@router.patch("/addons/{addon_id}", response_model=AddOnResponse)
def update_addon(
    addon_id: int,
    data: AddOnUpdate,
    service: SubscriptionService = Depends(get_service)
):
    """Mettre à jour un add-on."""
    addon = service.update_addon(addon_id, data)
    if not addon:
        raise HTTPException(status_code=404, detail="Add-on introuvable")
    return addon


# ============================================================================
# SUBSCRIPTIONS
# ============================================================================

@router.post("", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    data: SubscriptionCreate,
    service: SubscriptionService = Depends(get_service)
):
    """Créer un abonnement."""
    try:
        return service.create_subscription(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=SubscriptionListResponse)
def list_subscriptions(
    customer_id: int | None = None,
    plan_id: int | None = None,
    status: SubscriptionStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_service)
):
    """Lister les abonnements."""
    items, total = service.list_subscriptions(
        customer_id=customer_id, plan_id=plan_id, status=status,
        skip=skip, limit=limit
    )
    return SubscriptionListResponse(
        items=items, total=total, page=skip // limit + 1, page_size=limit
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Récupérer un abonnement."""
    subscription = service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return subscription


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    data: SubscriptionUpdate,
    service: SubscriptionService = Depends(get_service)
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
    service: SubscriptionService = Depends(get_service)
):
    """Changer de plan d'abonnement."""
    try:
        return service.change_plan(subscription_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: int,
    data: SubscriptionCancelRequest,
    service: SubscriptionService = Depends(get_service)
):
    """Annuler un abonnement."""
    try:
        return service.cancel_subscription(subscription_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: int,
    data: SubscriptionPauseRequest,
    service: SubscriptionService = Depends(get_service)
):
    """Mettre en pause un abonnement."""
    try:
        return service.pause_subscription(subscription_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Reprendre un abonnement en pause."""
    try:
        return service.resume_subscription(subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# INVOICES
# ============================================================================

@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    data: InvoiceCreate,
    service: SubscriptionService = Depends(get_service)
):
    """Créer une facture manuelle."""
    try:
        return service.create_invoice(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices", response_model=InvoiceListResponse)
def list_invoices(
    subscription_id: int | None = None,
    customer_id: int | None = None,
    status: InvoiceStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_service)
):
    """Lister les factures."""
    items, total = service.list_invoices(
        subscription_id=subscription_id, customer_id=customer_id,
        status=status, skip=skip, limit=limit
    )
    return InvoiceListResponse(
        items=items, total=total, page=skip // limit + 1, page_size=limit
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Récupérer une facture."""
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return invoice


@router.post("/invoices/{invoice_id}/finalize", response_model=InvoiceResponse)
def finalize_invoice(
    invoice_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Finaliser une facture."""
    try:
        return service.finalize_invoice(invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceResponse)
def void_invoice(
    invoice_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Annuler une facture."""
    try:
        return service.void_invoice(invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/pay", response_model=InvoiceResponse)
def pay_invoice(
    invoice_id: int,
    amount: float | None = None,
    service: SubscriptionService = Depends(get_service)
):
    """Marquer une facture comme payée."""
    try:
        from decimal import Decimal
        payment_amount = Decimal(str(amount)) if amount else None
        return service.mark_invoice_paid(invoice_id, payment_amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PAYMENTS
# ============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(
    data: PaymentCreate,
    service: SubscriptionService = Depends(get_service)
):
    """Créer un paiement."""
    try:
        return service.create_payment(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    data: RefundRequest,
    service: SubscriptionService = Depends(get_service)
):
    """Rembourser un paiement."""
    try:
        return service.refund_payment(payment_id, data.amount, data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# USAGE RECORDS
# ============================================================================

@router.post("/usage", response_model=UsageRecordResponse, status_code=201)
def create_usage_record(
    data: UsageRecordCreate,
    service: SubscriptionService = Depends(get_service)
):
    """Enregistrer usage (pour abonnements metered)."""
    try:
        return service.create_usage_record(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{subscription_id}/usage", response_model=list[UsageSummary])
def get_usage_summary(
    subscription_id: int,
    period_start: date | None = None,
    period_end: date | None = None,
    service: SubscriptionService = Depends(get_service)
):
    """Résumé d'usage pour un abonnement."""
    try:
        return service.get_usage_summary(subscription_id, period_start, period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# COUPONS
# ============================================================================

@router.post("/coupons", response_model=CouponResponse, status_code=201)
def create_coupon(
    data: CouponCreate,
    service: SubscriptionService = Depends(get_service)
):
    """Créer un coupon."""
    try:
        return service.create_coupon(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/coupons", response_model=list[CouponResponse])
def list_coupons(
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubscriptionService = Depends(get_service)
):
    """Lister les coupons."""
    return service.list_coupons(is_active=is_active, skip=skip, limit=limit)


@router.get("/coupons/{coupon_id}", response_model=CouponResponse)
def get_coupon(
    coupon_id: int,
    service: SubscriptionService = Depends(get_service)
):
    """Récupérer un coupon."""
    coupon = service.get_coupon(coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon introuvable")
    return coupon


@router.patch("/coupons/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int,
    data: CouponUpdate,
    service: SubscriptionService = Depends(get_service)
):
    """Mettre à jour un coupon."""
    coupon = service.update_coupon(coupon_id, data)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon introuvable")
    return coupon


@router.post("/coupons/validate", response_model=CouponValidateResponse)
def validate_coupon(
    data: CouponValidateRequest,
    service: SubscriptionService = Depends(get_service)
):
    """Valider un code coupon."""
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
    service: SubscriptionService = Depends(get_service)
):
    """Calculer et sauvegarder les métriques."""
    metrics = service.calculate_metrics(metric_date)
    return metrics


@router.get("/metrics/{metric_date}", response_model=MetricsSnapshot)
def get_metrics(
    metric_date: date,
    service: SubscriptionService = Depends(get_service)
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
    service: SubscriptionService = Depends(get_service)
):
    """Récupérer la tendance des métriques."""
    return service.get_metrics_trend(start_date, end_date)


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=SubscriptionDashboard)
def get_dashboard(
    service: SubscriptionService = Depends(get_service)
):
    """Dashboard abonnements."""
    return service.get_dashboard()


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhooks")
def receive_webhook(
    event: WebhookEvent,
    service: SubscriptionService = Depends(get_service)
):
    """Recevoir un webhook."""
    webhook = service.process_webhook(
        event.event_type, event.source, event.payload
    )
    return {"received": True, "webhook_id": webhook.id}
