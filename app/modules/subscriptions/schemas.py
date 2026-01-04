"""
AZALS MODULE 14 - Subscriptions Schemas
========================================
Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr

from .models import (
    PlanInterval, SubscriptionStatus, InvoiceStatus,
    PaymentStatus, UsageType
)


# ============================================================================
# PLAN SCHEMAS
# ============================================================================

class PlanBase(BaseModel):
    """Base plan."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    base_price: Decimal = Field(..., ge=0)
    currency: str = "EUR"
    interval: PlanInterval = PlanInterval.MONTHLY
    interval_count: int = Field(1, ge=1)
    trial_days: int = Field(0, ge=0)
    trial_once: bool = True
    max_users: Optional[int] = None
    max_storage_gb: Optional[Decimal] = None
    max_api_calls: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    modules_included: Optional[List[str]] = None
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
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    trial_days: Optional[int] = None
    max_users: Optional[int] = None
    max_storage_gb: Optional[Decimal] = None
    max_api_calls: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    modules_included: Optional[List[str]] = None
    per_user_price: Optional[Decimal] = None
    setup_fee: Optional[Decimal] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanResponse(PlanBase):
    """Réponse plan."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanListResponse(BaseModel):
    """Liste des plans."""
    items: List[PlanResponse]
    total: int


# ============================================================================
# ADD-ON SCHEMAS
# ============================================================================

class AddOnBase(BaseModel):
    """Base add-on."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    usage_type: UsageType = UsageType.LICENSED
    unit_name: Optional[str] = None
    min_quantity: int = 0
    max_quantity: Optional[int] = None


class AddOnCreate(AddOnBase):
    """Création add-on."""
    plan_id: int


class AddOnUpdate(BaseModel):
    """Mise à jour add-on."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    unit_name: Optional[str] = None
    min_quantity: Optional[int] = None
    max_quantity: Optional[int] = None
    is_active: Optional[bool] = None


class AddOnResponse(AddOnBase):
    """Réponse add-on."""
    id: int
    tenant_id: str
    plan_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# SUBSCRIPTION SCHEMAS
# ============================================================================

class SubscriptionItemCreate(BaseModel):
    """Création item abonnement."""
    add_on_code: Optional[str] = None
    name: str
    description: Optional[str] = None
    unit_price: Decimal
    quantity: int = 1
    usage_type: UsageType = UsageType.LICENSED


class SubscriptionItemResponse(BaseModel):
    """Réponse item abonnement."""
    id: int
    add_on_code: Optional[str] = None
    name: str
    description: Optional[str] = None
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
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    quantity: int = Field(1, ge=1)
    start_date: Optional[date] = None
    trial_end: Optional[date] = None
    billing_cycle_anchor: Optional[int] = Field(None, ge=1, le=28)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_end_date: Optional[date] = None
    coupon_code: Optional[str] = None
    collection_method: str = "charge_automatically"
    default_payment_method_id: Optional[str] = None
    items: Optional[List[SubscriptionItemCreate]] = None
    extra_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    """Mise à jour abonnement."""
    quantity: Optional[int] = None
    discount_percent: Optional[Decimal] = None
    discount_end_date: Optional[date] = None
    default_payment_method_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Réponse abonnement."""
    id: int
    tenant_id: str
    subscription_number: str
    external_id: Optional[str] = None
    plan_id: int
    customer_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    status: SubscriptionStatus
    quantity: int
    current_users: int
    trial_start: Optional[date] = None
    trial_end: Optional[date] = None
    current_period_start: date
    current_period_end: date
    started_at: date
    ended_at: Optional[date] = None
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    resume_at: Optional[date] = None
    billing_cycle_anchor: int
    discount_percent: Decimal
    discount_end_date: Optional[date] = None
    mrr: Decimal
    arr: Decimal
    items: List[SubscriptionItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionListResponse(BaseModel):
    """Liste des abonnements."""
    items: List[SubscriptionResponse]
    total: int
    page: int
    page_size: int


class SubscriptionChangePlanRequest(BaseModel):
    """Changement de plan."""
    new_plan_id: int
    new_quantity: Optional[int] = None
    prorate: bool = True
    effective_date: Optional[date] = None
    reason: Optional[str] = None


class SubscriptionCancelRequest(BaseModel):
    """Annulation abonnement."""
    cancel_at_period_end: bool = True
    reason: Optional[str] = None
    feedback: Optional[str] = None


class SubscriptionPauseRequest(BaseModel):
    """Mise en pause abonnement."""
    resume_at: Optional[date] = None
    reason: Optional[str] = None


# ============================================================================
# INVOICE SCHEMAS
# ============================================================================

class InvoiceLineCreate(BaseModel):
    """Création ligne facture."""
    description: str = Field(..., min_length=1, max_length=500)
    item_type: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")


class InvoiceLineResponse(BaseModel):
    """Réponse ligne facture."""
    id: int
    description: str
    item_type: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
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
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    billing_address: Optional[Dict[str, Any]] = None
    period_start: date
    period_end: date
    due_date: Optional[date] = None
    collection_method: str = "send_invoice"
    lines: List[InvoiceLineCreate]
    notes: Optional[str] = None
    footer: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Réponse facture."""
    id: int
    tenant_id: str
    subscription_id: int
    invoice_number: str
    external_id: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    status: InvoiceStatus
    period_start: date
    period_end: date
    due_date: Optional[date] = None
    finalized_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
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
    hosted_invoice_url: Optional[str] = None
    pdf_url: Optional[str] = None
    lines: List[InvoiceLineResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Liste des factures."""
    items: List[InvoiceResponse]
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
    payment_method_type: Optional[str] = None
    payment_method_id: Optional[str] = None


class PaymentResponse(BaseModel):
    """Réponse paiement."""
    id: int
    tenant_id: str
    invoice_id: Optional[int] = None
    payment_number: str
    external_id: Optional[str] = None
    customer_id: int
    amount: Decimal
    currency: str
    fee_amount: Decimal
    status: PaymentStatus
    payment_method_type: Optional[str] = None
    payment_method_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    refunded_amount: Decimal

    model_config = {"from_attributes": True}


class RefundRequest(BaseModel):
    """Demande de remboursement."""
    amount: Optional[Decimal] = None  # None = remboursement total
    reason: Optional[str] = None


# ============================================================================
# USAGE SCHEMAS
# ============================================================================

class UsageRecordCreate(BaseModel):
    """Création enregistrement usage."""
    subscription_item_id: int
    quantity: Decimal = Field(..., gt=0)
    unit: Optional[str] = None
    action: str = "increment"  # set ou increment
    timestamp: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class UsageRecordResponse(BaseModel):
    """Réponse enregistrement usage."""
    id: int
    subscription_id: int
    subscription_item_id: Optional[int] = None
    quantity: Decimal
    unit: Optional[str] = None
    action: str
    timestamp: datetime
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageSummary(BaseModel):
    """Résumé usage."""
    subscription_id: int
    item_id: int
    item_name: str
    period_start: date
    period_end: date
    total_usage: Decimal
    unit: Optional[str] = None
    estimated_amount: Decimal


# ============================================================================
# COUPON SCHEMAS
# ============================================================================

class CouponCreate(BaseModel):
    """Création coupon."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    discount_type: str = "percent"  # percent ou fixed_amount
    discount_value: Decimal = Field(..., gt=0)
    currency: Optional[str] = None
    duration: str = "once"  # once, repeating, forever
    duration_months: Optional[int] = None
    max_redemptions: Optional[int] = None
    applies_to_plans: Optional[List[int]] = None
    min_amount: Optional[Decimal] = None
    first_time_only: bool = False
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class CouponUpdate(BaseModel):
    """Mise à jour coupon."""
    name: Optional[str] = None
    description: Optional[str] = None
    max_redemptions: Optional[int] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class CouponResponse(BaseModel):
    """Réponse coupon."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    currency: Optional[str] = None
    duration: str
    duration_months: Optional[int] = None
    max_redemptions: Optional[int] = None
    times_redeemed: int
    applies_to_plans: Optional[List[int]] = None
    first_time_only: bool
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CouponValidateRequest(BaseModel):
    """Validation coupon."""
    code: str
    plan_id: Optional[int] = None
    customer_id: Optional[int] = None
    amount: Optional[Decimal] = None


class CouponValidateResponse(BaseModel):
    """Résultat validation coupon."""
    valid: bool
    coupon: Optional[CouponResponse] = None
    discount_amount: Optional[Decimal] = None
    error_message: Optional[str] = None


# ============================================================================
# METRICS SCHEMAS
# ============================================================================

class MetricsSnapshot(BaseModel):
    """Snapshot métriques."""
    metric_date: date
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
    start_date: date
    end_date: date
    data_points: List[MetricsSnapshot]


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

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
    top_plans: List[Dict[str, Any]]

    # Prochains renouvellements
    upcoming_renewals: List[Dict[str, Any]]

    # Factures en attente
    pending_invoices_count: int
    pending_invoices_amount: Decimal


class RevenueBreakdown(BaseModel):
    """Répartition revenus."""
    by_plan: List[Dict[str, Any]]
    by_interval: Dict[str, Decimal]
    by_currency: Dict[str, Decimal]


# ============================================================================
# WEBHOOK SCHEMAS
# ============================================================================

class WebhookEvent(BaseModel):
    """Événement webhook."""
    event_type: str
    source: str
    payload: Dict[str, Any]
    related_object_type: Optional[str] = None
    related_object_id: Optional[str] = None


class WebhookResponse(BaseModel):
    """Réponse événement webhook."""
    id: int
    event_id: Optional[str] = None
    event_type: str
    source: str
    related_object_type: Optional[str] = None
    related_object_id: Optional[str] = None
    is_processed: bool
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
