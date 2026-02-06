"""
AZALS MODULE 14 - Subscriptions Schemas
========================================
Schémas Pydantic pour validation et sérialisation.
"""

import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from .models import InvoiceStatus, PaymentStatus, PlanInterval, SubscriptionStatus, UsageType

# ============================================================================
# PLAN SCHEMAS
# ============================================================================

class PlanBase(BaseModel):
    """Base plan."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    base_price: Decimal = Field(..., ge=0)
    currency: str = "EUR"
    interval: PlanInterval = PlanInterval.MONTHLY
    interval_count: int = Field(1, ge=1)
    trial_days: int = Field(0, ge=0)
    trial_once: bool = True
    max_users: int | None = None
    max_storage_gb: Decimal | None = None
    max_api_calls: int | None = None
    features: dict[str, Any] | None = None
    modules_included: list[str] | None = None
    per_user_price: Decimal = Decimal("0")
    included_users: int = 1
    setup_fee: Decimal = Decimal("0")
    is_public: bool = True
    sort_order: int = 0


class PlanCreate(PlanBase):
    """Création plan."""
    pass


class PlanUpdate(BaseModel):
    """Mise à jour plan."""
    name: str | None = None
    description: str | None = None
    base_price: Decimal | None = None
    trial_days: int | None = None
    max_users: int | None = None
    max_storage_gb: Decimal | None = None
    max_api_calls: int | None = None
    features: dict[str, Any] | None = None
    modules_included: list[str] | None = None
    per_user_price: Decimal | None = None
    setup_fee: Decimal | None = None
    is_public: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class PlanResponse(PlanBase):
    """Réponse plan."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class PlanListResponse(BaseModel):
    """Liste des plans."""
    items: list[PlanResponse]
    total: int


# ============================================================================
# ADD-ON SCHEMAS
# ============================================================================

class AddOnBase(BaseModel):
    """Base add-on."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., ge=0)
    usage_type: UsageType = UsageType.LICENSED
    unit_name: str | None = None
    min_quantity: int = 0
    max_quantity: int | None = None


class AddOnCreate(AddOnBase):
    """Création add-on."""
    plan_id: int


class AddOnUpdate(BaseModel):
    """Mise à jour add-on."""
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    unit_name: str | None = None
    min_quantity: int | None = None
    max_quantity: int | None = None
    is_active: bool | None = None


class AddOnResponse(AddOnBase):
    """Réponse add-on."""
    id: int
    tenant_id: str
    plan_id: int
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ============================================================================
# SUBSCRIPTION SCHEMAS
# ============================================================================

class SubscriptionItemCreate(BaseModel):
    """Création item abonnement."""
    add_on_code: str | None = None
    name: str
    description: str | None = None
    unit_price: Decimal
    quantity: int = 1
    usage_type: UsageType = UsageType.LICENSED


class SubscriptionItemResponse(BaseModel):
    """Réponse item abonnement."""
    id: int
    add_on_code: str | None = None
    name: str
    description: str | None = None
    unit_price: Decimal
    quantity: int
    usage_type: UsageType
    metered_usage: Decimal
    is_active: bool

    model_config = {"from_attributes": True}


class SubscriptionCreate(BaseModel):
    """Création abonnement."""
    plan_id: int
    customer_id: int
    customer_name: str | None = None
    customer_email: EmailStr | None = None
    quantity: int = Field(1, ge=1)
    start_date: datetime.date | None = None
    trial_end: datetime.date | None = None
    billing_cycle_anchor: int | None = Field(None, ge=1, le=28)
    discount_percent: Decimal | None = Field(None, ge=0, le=100)
    discount_end_date: datetime.date | None = None
    coupon_code: str | None = None
    collection_method: str = "charge_automatically"
    default_payment_method_id: str | None = None
    items: list[SubscriptionItemCreate] | None = None
    extra_data: dict[str, Any] | None = None
    notes: str | None = None


class SubscriptionUpdate(BaseModel):
    """Mise à jour abonnement."""
    quantity: int | None = None
    discount_percent: Decimal | None = None
    discount_end_date: datetime.date | None = None
    default_payment_method_id: str | None = None
    extra_data: dict[str, Any] | None = None
    notes: str | None = None


class SubscriptionResponse(BaseModel):
    """Réponse abonnement."""
    id: int
    tenant_id: str
    subscription_number: str
    external_id: str | None = None
    plan_id: int
    customer_id: int
    customer_name: str | None = None
    customer_email: str | None = None
    status: SubscriptionStatus
    quantity: int
    current_users: int
    trial_start: datetime.date | None = None
    trial_end: datetime.date | None = None
    current_period_start: datetime.date
    current_period_end: datetime.date
    started_at: datetime.date
    ended_at: datetime.date | None = None
    cancel_at_period_end: bool
    canceled_at: datetime.datetime | None = None
    paused_at: datetime.datetime | None = None
    resume_at: datetime.date | None = None
    billing_cycle_anchor: int
    discount_percent: Decimal
    discount_end_date: datetime.date | None = None
    mrr: Decimal
    arr: Decimal
    items: list[SubscriptionItemResponse] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class SubscriptionListResponse(BaseModel):
    """Liste des abonnements."""
    items: list[SubscriptionResponse]
    total: int
    page: int
    page_size: int


class SubscriptionChangePlanRequest(BaseModel):
    """Changement de plan."""
    new_plan_id: int
    new_quantity: int | None = None
    prorate: bool = True
    effective_date: datetime.date | None = None
    reason: str | None = None


class SubscriptionCancelRequest(BaseModel):
    """Annulation abonnement."""
    cancel_at_period_end: bool = True
    reason: str | None = None
    feedback: str | None = None


class SubscriptionPauseRequest(BaseModel):
    """Mise en pause abonnement."""
    resume_at: datetime.date | None = None
    reason: str | None = None


# ============================================================================
# INVOICE SCHEMAS
# ============================================================================

class InvoiceLineCreate(BaseModel):
    """Création ligne facture."""
    description: str = Field(..., min_length=1, max_length=500)
    item_type: str | None = None
    period_start: datetime.date | None = None
    period_end: datetime.date | None = None
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")


class InvoiceLineResponse(BaseModel):
    """Réponse ligne facture."""
    id: int
    description: str
    item_type: str | None = None
    period_start: datetime.date | None = None
    period_end: datetime.date | None = None
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    proration: bool

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    """Création facture manuelle."""
    subscription_id: int
    customer_id: int
    customer_name: str | None = None
    customer_email: EmailStr | None = None
    billing_address: dict[str, Any] | None = None
    period_start: datetime.date
    period_end: datetime.date
    due_date: datetime.date | None = None
    collection_method: str = "send_invoice"
    lines: list[InvoiceLineCreate]
    notes: str | None = None
    footer: str | None = None


class InvoiceResponse(BaseModel):
    """Réponse facture."""
    id: int
    tenant_id: str
    subscription_id: int
    invoice_number: str
    external_id: str | None = None
    customer_id: int
    customer_name: str | None = None
    customer_email: str | None = None
    status: InvoiceStatus
    period_start: datetime.date
    period_end: datetime.date
    due_date: datetime.date | None = None
    finalized_at: datetime.datetime | None = None
    paid_at: datetime.datetime | None = None
    subtotal: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_remaining: Decimal
    currency: str
    collection_method: str
    attempt_count: int
    hosted_invoice_url: str | None = None
    pdf_url: str | None = None
    lines: list[InvoiceLineResponse] = []
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Liste des factures."""
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentCreate(BaseModel):
    """Création paiement."""
    invoice_id: int
    amount: Decimal = Field(..., gt=0)
    currency: str = "EUR"
    payment_method_type: str | None = None
    payment_method_id: str | None = None


class PaymentResponse(BaseModel):
    """Réponse paiement."""
    id: int
    tenant_id: str
    invoice_id: int | None = None
    payment_number: str
    external_id: str | None = None
    customer_id: int
    amount: Decimal
    currency: str
    fee_amount: Decimal
    status: PaymentStatus
    payment_method_type: str | None = None
    payment_method_details: dict[str, Any] | None = None
    created_at: datetime.datetime
    processed_at: datetime.datetime | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    refunded_amount: Decimal

    model_config = {"from_attributes": True}


class RefundRequest(BaseModel):
    """Demande de remboursement."""
    amount: Decimal | None = None  # None = remboursement total
    reason: str | None = None


# ============================================================================
# USAGE SCHEMAS
# ============================================================================

class UsageRecordCreate(BaseModel):
    """Création enregistrement usage."""
    subscription_item_id: int
    quantity: Decimal = Field(..., gt=0)
    unit: str | None = None
    action: str = "increment"  # set ou increment
    timestamp: datetime.datetime | None = None
    idempotency_key: str | None = None
    extra_data: dict[str, Any] | None = None


class UsageRecordResponse(BaseModel):
    """Réponse enregistrement usage."""
    id: int
    subscription_id: int
    subscription_item_id: int | None = None
    quantity: Decimal
    unit: str | None = None
    action: str
    timestamp: datetime.datetime
    idempotency_key: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UsageSummary(BaseModel):
    """Résumé usage."""
    subscription_id: int
    item_id: int
    item_name: str
    period_start: datetime.date
    period_end: datetime.date
    total_usage: Decimal
    unit: str | None = None
    estimated_amount: Decimal


# ============================================================================
# COUPON SCHEMAS
# ============================================================================

class CouponCreate(BaseModel):
    """Création coupon."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    discount_type: str = "percent"  # percent ou fixed_amount
    discount_value: Decimal = Field(..., gt=0)
    currency: str | None = None
    duration: str = "once"  # once, repeating, forever
    duration_months: int | None = None
    max_redemptions: int | None = None
    applies_to_plans: list[int] | None = None
    min_amount: Decimal | None = None
    first_time_only: bool = False
    valid_from: datetime.datetime | None = None
    valid_until: datetime.datetime | None = None


class CouponUpdate(BaseModel):
    """Mise à jour coupon."""
    name: str | None = None
    description: str | None = None
    max_redemptions: int | None = None
    valid_until: datetime.datetime | None = None
    is_active: bool | None = None


class CouponResponse(BaseModel):
    """Réponse coupon."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: str | None = None
    discount_type: str
    discount_value: Decimal
    currency: str | None = None
    duration: str
    duration_months: int | None = None
    max_redemptions: int | None = None
    times_redeemed: int
    applies_to_plans: list[int] | None = None
    first_time_only: bool
    valid_from: datetime.datetime | None = None
    valid_until: datetime.datetime | None = None
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CouponValidateRequest(BaseModel):
    """Validation coupon."""
    code: str
    plan_id: int | None = None
    customer_id: int | None = None
    amount: Decimal | None = None


class CouponValidateResponse(BaseModel):
    """Résultat validation coupon."""
    valid: bool
    coupon: CouponResponse | None = None
    discount_amount: Decimal | None = None
    error_message: str | None = None


# ============================================================================
# METRICS SCHEMAS
# ============================================================================

class MetricsSnapshot(BaseModel):
    """Snapshot métriques."""
    metric_date: datetime.date
    mrr: Decimal
    arr: Decimal
    new_mrr: Decimal
    expansion_mrr: Decimal
    contraction_mrr: Decimal
    churned_mrr: Decimal
    total_subscriptions: int
    active_subscriptions: int
    trialing_subscriptions: int
    canceled_subscriptions: int
    new_subscriptions: int
    churned_subscriptions: int
    total_customers: int
    new_customers: int
    churned_customers: int
    churn_rate: Decimal
    trial_conversion_rate: Decimal
    arpu: Decimal
    average_ltv: Decimal


class MetricsTrend(BaseModel):
    """Tendance métriques."""
    period: str  # daily, weekly, monthly
    start_date: datetime.date
    end_date: datetime.date
    data_points: list[MetricsSnapshot]


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class SubscriptionStatsResponse(BaseModel):
    """Stats abonnements simplifié pour le frontend."""
    total_plans: int = 0
    active_subscriptions: int = 0
    trial_subscriptions: int = 0
    mrr: Decimal = Decimal("0")
    arr: Decimal = Decimal("0")
    churn_rate: Decimal = Decimal("0")
    new_subscribers_month: int = 0
    revenue_this_month: Decimal = Decimal("0")


class SubscriptionDashboard(BaseModel):
    """Dashboard abonnements."""
    # Revenus
    mrr: Decimal
    mrr_growth: Decimal  # % vs mois précédent
    arr: Decimal

    # Compteurs
    total_active: int
    trialing: int
    past_due: int
    canceled_this_month: int

    # Mouvements MRR
    new_mrr: Decimal
    expansion_mrr: Decimal
    contraction_mrr: Decimal
    churned_mrr: Decimal
    net_mrr_change: Decimal

    # Taux
    churn_rate: Decimal
    trial_conversion_rate: Decimal

    # ARPU & LTV
    arpu: Decimal
    average_ltv: Decimal

    # Top plans
    top_plans: list[dict[str, Any]]

    # Prochains renouvellements
    upcoming_renewals: list[dict[str, Any]]

    # Factures en attente
    pending_invoices_count: int
    pending_invoices_amount: Decimal


class RevenueBreakdown(BaseModel):
    """Répartition revenus."""
    by_plan: list[dict[str, Any]]
    by_interval: dict[str, Decimal]
    by_currency: dict[str, Decimal]


# ============================================================================
# WEBHOOK SCHEMAS
# ============================================================================

class WebhookEvent(BaseModel):
    """Événement webhook."""
    event_type: str
    source: str
    payload: dict[str, Any]
    related_object_type: str | None = None
    related_object_id: str | None = None


class WebhookResponse(BaseModel):
    """Réponse événement webhook."""
    id: int
    event_id: str | None = None
    event_type: str
    source: str
    related_object_type: str | None = None
    related_object_id: str | None = None
    is_processed: bool
    processed_at: datetime.datetime | None = None
    processing_error: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
