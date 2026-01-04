"""
AZALS MODULE 15 - Stripe Integration Schemas
==============================================
Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr

from .models import (
    StripeAccountStatus, PaymentIntentStatus, RefundStatus,
    DisputeStatus, WebhookStatus
)


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class StripeCustomerCreate(BaseModel):
    """Création client Stripe."""
    customer_id: int
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_exempt: str = "none"
    metadata: Optional[Dict[str, str]] = None


class StripeCustomerUpdate(BaseModel):
    """Mise à jour client Stripe."""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    default_payment_method_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class StripeCustomerResponse(BaseModel):
    """Réponse client Stripe."""
    id: int
    tenant_id: str
    stripe_customer_id: str
    customer_id: int
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    default_payment_method_id: Optional[str] = None
    balance: Decimal
    currency: Optional[str] = None
    delinquent: bool
    is_synced: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# PAYMENT METHOD SCHEMAS
# ============================================================================

class PaymentMethodCreate(BaseModel):
    """Création méthode de paiement."""
    stripe_customer_id: str
    method_type: str = "card"
    token: Optional[str] = None  # Token Stripe.js
    set_as_default: bool = False


class PaymentMethodResponse(BaseModel):
    """Réponse méthode de paiement."""
    id: int
    stripe_payment_method_id: str
    method_type: str
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    is_default: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SetupIntentCreate(BaseModel):
    """Création SetupIntent pour ajouter méthode."""
    customer_id: int
    payment_method_types: List[str] = ["card"]
    usage: str = "off_session"  # on_session, off_session


class SetupIntentResponse(BaseModel):
    """Réponse SetupIntent."""
    setup_intent_id: str
    client_secret: str
    status: str
    payment_method_types: List[str]


# ============================================================================
# PAYMENT INTENT SCHEMAS
# ============================================================================

class PaymentIntentCreate(BaseModel):
    """Création PaymentIntent."""
    customer_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    currency: str = "EUR"
    payment_method_types: List[str] = ["card"]
    capture_method: str = "automatic"  # automatic, manual
    confirm: bool = False
    payment_method_id: Optional[str] = None
    receipt_email: Optional[EmailStr] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    # Références
    invoice_id: Optional[int] = None
    order_id: Optional[int] = None
    subscription_id: Optional[int] = None


class PaymentIntentUpdate(BaseModel):
    """Mise à jour PaymentIntent."""
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    receipt_email: Optional[EmailStr] = None


class PaymentIntentResponse(BaseModel):
    """Réponse PaymentIntent."""
    id: int
    stripe_payment_intent_id: str
    amount: Decimal
    amount_received: Decimal
    currency: str
    status: PaymentIntentStatus
    client_secret: Optional[str] = None
    payment_method_id: Optional[str] = None
    capture_method: str
    invoice_id: Optional[int] = None
    order_id: Optional[int] = None
    description: Optional[str] = None
    stripe_fee: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentIntentConfirm(BaseModel):
    """Confirmation PaymentIntent."""
    payment_method_id: Optional[str] = None
    return_url: Optional[str] = None


class PaymentIntentCapture(BaseModel):
    """Capture PaymentIntent."""
    amount_to_capture: Optional[Decimal] = None


# ============================================================================
# CHECKOUT SESSION SCHEMAS
# ============================================================================

class CheckoutLineItem(BaseModel):
    """Ligne de checkout."""
    name: str
    description: Optional[str] = None
    amount: Decimal  # Prix unitaire
    currency: str = "EUR"
    quantity: int = 1
    images: Optional[List[str]] = None


class CheckoutSessionCreate(BaseModel):
    """Création session checkout."""
    customer_id: Optional[int] = None
    customer_email: Optional[EmailStr] = None
    mode: str = "payment"  # payment, subscription, setup
    success_url: str
    cancel_url: str
    line_items: Optional[List[CheckoutLineItem]] = None
    # Pour abonnements
    price_id: Optional[str] = None  # Stripe Price ID
    quantity: int = 1
    trial_period_days: Optional[int] = None
    # Options
    allow_promotion_codes: bool = False
    collect_shipping_address: bool = False
    payment_method_types: List[str] = ["card"]
    # Références
    invoice_id: Optional[int] = None
    order_id: Optional[int] = None
    subscription_id: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None


class CheckoutSessionResponse(BaseModel):
    """Réponse session checkout."""
    id: int
    stripe_session_id: str
    url: str
    mode: str
    payment_status: Optional[str] = None
    status: str
    amount_total: Optional[Decimal] = None
    currency: str
    customer_email: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# REFUND SCHEMAS
# ============================================================================

class RefundCreate(BaseModel):
    """Création remboursement."""
    payment_intent_id: int  # ID interne
    amount: Optional[Decimal] = None  # None = remboursement total
    reason: Optional[str] = None  # duplicate, fraudulent, requested_by_customer
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class RefundResponse(BaseModel):
    """Réponse remboursement."""
    id: int
    stripe_refund_id: str
    payment_intent_id: int
    amount: Decimal
    currency: str
    status: RefundStatus
    reason: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# DISPUTE SCHEMAS
# ============================================================================

class DisputeResponse(BaseModel):
    """Réponse litige."""
    id: int
    stripe_dispute_id: str
    stripe_charge_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: DisputeStatus
    reason: Optional[str] = None
    evidence_due_by: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DisputeEvidenceSubmit(BaseModel):
    """Soumission preuves litige."""
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    product_description: Optional[str] = None
    shipping_documentation: Optional[str] = None  # File ID
    receipt: Optional[str] = None  # File ID
    uncategorized_text: Optional[str] = None


# ============================================================================
# PRODUCT & PRICE SCHEMAS
# ============================================================================

class StripeProductCreate(BaseModel):
    """Création produit Stripe."""
    name: str
    description: Optional[str] = None
    product_id: Optional[int] = None  # Lien produit AZALS
    plan_id: Optional[int] = None  # Lien plan abonnement AZALS
    images: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None


class StripeProductResponse(BaseModel):
    """Réponse produit Stripe."""
    id: int
    stripe_product_id: str
    name: str
    description: Optional[str] = None
    product_id: Optional[int] = None
    plan_id: Optional[int] = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StripePriceCreate(BaseModel):
    """Création prix Stripe."""
    product_id: int  # ID interne produit
    unit_amount: Decimal  # En centimes
    currency: str = "EUR"
    recurring_interval: Optional[str] = None  # month, year
    recurring_interval_count: int = 1
    nickname: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class StripePriceResponse(BaseModel):
    """Réponse prix Stripe."""
    id: int
    stripe_price_id: str
    unit_amount: Decimal
    currency: str
    recurring_interval: Optional[str] = None
    recurring_interval_count: int
    active: bool
    nickname: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# CONNECT SCHEMAS
# ============================================================================

class ConnectAccountCreate(BaseModel):
    """Création compte Connect."""
    vendor_id: int
    email: EmailStr
    country: str = "FR"
    account_type: str = "express"  # standard, express, custom
    business_type: str = "company"  # individual, company
    return_url: str
    refresh_url: str


class ConnectAccountResponse(BaseModel):
    """Réponse compte Connect."""
    id: int
    stripe_account_id: str
    vendor_id: Optional[int] = None
    email: Optional[str] = None
    account_type: str
    status: StripeAccountStatus
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    onboarding_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConnectOnboardingLink(BaseModel):
    """Lien onboarding Connect."""
    url: str
    expires_at: datetime


# ============================================================================
# PAYOUT SCHEMAS
# ============================================================================

class PayoutResponse(BaseModel):
    """Réponse virement."""
    id: int
    stripe_payout_id: str
    amount: Decimal
    currency: str
    status: str
    arrival_date: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# WEBHOOK SCHEMAS
# ============================================================================

class WebhookEventResponse(BaseModel):
    """Réponse événement webhook."""
    id: int
    stripe_event_id: str
    event_type: str
    object_type: Optional[str] = None
    object_id: Optional[str] = None
    status: WebhookStatus
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# CONFIG SCHEMAS
# ============================================================================

class StripeConfigCreate(BaseModel):
    """Configuration Stripe."""
    api_key_live: Optional[str] = None
    api_key_test: Optional[str] = None
    webhook_secret_live: Optional[str] = None
    webhook_secret_test: Optional[str] = None
    is_live_mode: bool = False
    default_currency: str = "EUR"
    default_payment_methods: List[str] = ["card"]
    statement_descriptor: Optional[str] = None
    auto_capture: bool = True
    send_receipts: bool = True


class StripeConfigUpdate(BaseModel):
    """Mise à jour configuration."""
    api_key_live: Optional[str] = None
    api_key_test: Optional[str] = None
    webhook_secret_live: Optional[str] = None
    webhook_secret_test: Optional[str] = None
    is_live_mode: Optional[bool] = None
    default_currency: Optional[str] = None
    statement_descriptor: Optional[str] = None
    auto_capture: Optional[bool] = None
    send_receipts: Optional[bool] = None
    connect_enabled: Optional[bool] = None
    platform_fee_percent: Optional[Decimal] = None


class StripeConfigResponse(BaseModel):
    """Réponse configuration."""
    id: int
    tenant_id: str
    is_live_mode: bool
    default_currency: str
    default_payment_methods: List[str]
    statement_descriptor: Optional[str] = None
    auto_capture: bool
    send_receipts: bool
    connect_enabled: bool
    platform_fee_percent: Decimal
    # Masquer les clés
    has_live_key: bool = False
    has_test_key: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class StripeDashboard(BaseModel):
    """Dashboard Stripe."""
    # Volume
    total_volume_30d: Decimal
    successful_payments_30d: int
    failed_payments_30d: int
    refunds_30d: Decimal

    # Taux
    success_rate: Decimal
    average_transaction: Decimal

    # Litiges
    open_disputes: int
    disputed_amount: Decimal

    # Balance
    available_balance: Decimal
    pending_balance: Decimal

    # Récent
    recent_payments: List[Dict[str, Any]]
    recent_refunds: List[Dict[str, Any]]


class PaymentAnalytics(BaseModel):
    """Analytics paiements."""
    period: str  # daily, weekly, monthly
    start_date: datetime
    end_date: datetime
    total_volume: Decimal
    total_count: int
    average_amount: Decimal
    by_method: Dict[str, Decimal]
    by_status: Dict[str, int]
    by_currency: Dict[str, Decimal]
    chart_data: List[Dict[str, Any]]


# ============================================================================
# TRANSFER SCHEMAS (pour Connect)
# ============================================================================

class TransferCreate(BaseModel):
    """Création transfert vers compte Connect."""
    destination_account_id: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "EUR"
    description: Optional[str] = None
    source_transaction: Optional[str] = None  # Charge ID
    metadata: Optional[Dict[str, str]] = None


class TransferResponse(BaseModel):
    """Réponse transfert."""
    stripe_transfer_id: str
    destination_account_id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
