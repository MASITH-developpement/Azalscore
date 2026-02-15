"""
AZALS MODULE 15 - Stripe Integration Schemas
==============================================
Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from .models import DisputeStatus, PaymentIntentStatus, RefundStatus, StripeAccountStatus, WebhookStatus

# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class StripeCustomerCreate(BaseModel):
    """Création client Stripe."""
    customer_id: int
    email: EmailStr | None = None
    name: str | None = None
    phone: str | None = None
    description: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    tax_exempt: str = "none"
    metadata: dict[str, str] | None = None


class StripeCustomerUpdate(BaseModel):
    """Mise à jour client Stripe."""
    email: EmailStr | None = None
    name: str | None = None
    phone: str | None = None
    description: str | None = None
    address_line1: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    default_payment_method_id: str | None = None
    metadata: dict[str, str] | None = None


class StripeCustomerResponse(BaseModel):
    """Réponse client Stripe."""
    id: int
    tenant_id: str
    stripe_customer_id: str
    customer_id: int
    email: str | None = None
    name: str | None = None
    phone: str | None = None
    default_payment_method_id: str | None = None
    balance: Decimal
    currency: str | None = None
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
    token: str | None = None  # Token Stripe.js
    set_as_default: bool = False


class PaymentMethodResponse(BaseModel):
    """Réponse méthode de paiement."""
    id: int
    stripe_payment_method_id: str
    method_type: str
    card_brand: str | None = None
    card_last4: str | None = None
    card_exp_month: int | None = None
    card_exp_year: int | None = None
    is_default: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SetupIntentCreate(BaseModel):
    """Création SetupIntent pour ajouter méthode."""
    customer_id: int
    payment_method_types: list[str] = ["card"]
    usage: str = "off_session"  # on_session, off_session


class SetupIntentResponse(BaseModel):
    """Réponse SetupIntent."""
    setup_intent_id: str
    client_secret: str
    status: str
    payment_method_types: list[str]


# ============================================================================
# PAYMENT INTENT SCHEMAS
# ============================================================================

class PaymentIntentCreate(BaseModel):
    """Création PaymentIntent."""
    customer_id: int | None = None
    amount: Decimal = Field(..., gt=0)
    currency: str = "EUR"
    payment_method_types: list[str] = ["card"]
    capture_method: str = "automatic"  # automatic, manual
    confirm: bool = False
    payment_method_id: str | None = None
    receipt_email: EmailStr | None = None
    description: str | None = None
    metadata: dict[str, str] | None = None
    # Références
    invoice_id: int | None = None
    order_id: int | None = None
    subscription_id: int | None = None


class PaymentIntentUpdate(BaseModel):
    """Mise à jour PaymentIntent."""
    amount: Decimal | None = None
    description: str | None = None
    metadata: dict[str, str] | None = None
    receipt_email: EmailStr | None = None


class PaymentIntentResponse(BaseModel):
    """Réponse PaymentIntent."""
    id: int
    stripe_payment_intent_id: str
    amount: Decimal
    amount_received: Decimal
    currency: str
    status: PaymentIntentStatus
    client_secret: str | None = None
    payment_method_id: str | None = None
    capture_method: str
    invoice_id: int | None = None
    order_id: int | None = None
    description: str | None = None
    stripe_fee: Decimal | None = None
    net_amount: Decimal | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentIntentConfirm(BaseModel):
    """Confirmation PaymentIntent."""
    payment_method_id: str | None = None
    return_url: str | None = None

    @field_validator("return_url")
    @classmethod
    def validate_return_url(cls, v):
        """SÉCURITÉ: Valider l'URL de retour."""
        if v is None:
            return v
        return _validate_redirect_url(v)


class PaymentIntentCapture(BaseModel):
    """Capture PaymentIntent."""
    amount_to_capture: Decimal | None = None


# ============================================================================
# CHECKOUT SESSION SCHEMAS
# ============================================================================

class CheckoutLineItem(BaseModel):
    """Ligne de checkout."""
    name: str
    description: str | None = None
    amount: Decimal  # Prix unitaire
    currency: str = "EUR"
    quantity: int = 1
    images: list[str] | None = None


def _validate_redirect_url(url: str) -> str:
    """
    SÉCURITÉ: Valide qu'une URL de redirection est sûre.

    Empêche les attaques d'open redirect en:
    1. Vérifiant que l'URL est bien formée
    2. Vérifiant que le domaine est autorisé (APP_URL)
    3. Rejetant les URLs malveillantes (javascript:, data:, etc.)
    """
    import os
    from urllib.parse import urlparse

    if not url:
        raise ValueError("URL required")

    # Vérifier le format
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError("Invalid URL format")

    # SÉCURITÉ: Rejeter les protocoles dangereux
    if parsed.scheme.lower() not in ("https", "http"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    # SÉCURITÉ: Exiger HTTPS en production
    env = os.getenv("AZALS_ENV", "development")
    if env == "production" and parsed.scheme.lower() != "https":
        raise ValueError("HTTPS required for redirect URLs in production")

    # SÉCURITÉ: Valider le domaine
    app_url = os.getenv("APP_URL", "https://app.azalscore.com")
    app_parsed = urlparse(app_url)
    allowed_domains = [
        app_parsed.netloc,
        # Domaines Stripe autorisés pour les retours checkout
        "checkout.stripe.com",
    ]

    # Ajouter les domaines supplémentaires configurés
    extra_domains = os.getenv("ALLOWED_REDIRECT_DOMAINS", "")
    if extra_domains:
        allowed_domains.extend([d.strip() for d in extra_domains.split(",") if d.strip()])

    if parsed.netloc not in allowed_domains:
        raise ValueError(
            f"Redirect domain not allowed: {parsed.netloc}. "
            f"Allowed: {', '.join(allowed_domains)}"
        )

    return url


class CheckoutSessionCreate(BaseModel):
    """Création session checkout."""
    customer_id: int | None = None
    customer_email: EmailStr | None = None
    mode: str = "payment"  # payment, subscription, setup
    success_url: str
    cancel_url: str
    line_items: list[CheckoutLineItem] | None = None
    # Pour abonnements
    price_id: str | None = None  # Stripe Price ID
    quantity: int = 1
    trial_period_days: int | None = None
    # Options
    allow_promotion_codes: bool = False
    collect_shipping_address: bool = False
    payment_method_types: list[str] = ["card"]
    # Références
    invoice_id: int | None = None
    order_id: int | None = None
    subscription_id: int | None = None
    metadata: dict[str, str] | None = None

    @field_validator("success_url", "cancel_url")
    @classmethod
    def validate_urls(cls, v):
        """SÉCURITÉ: Valider les URLs de redirection."""
        return _validate_redirect_url(v)


class CheckoutSessionResponse(BaseModel):
    """Réponse session checkout."""
    id: int
    stripe_session_id: str
    url: str
    mode: str
    payment_status: str | None = None
    status: str
    amount_total: Decimal | None = None
    currency: str
    customer_email: str | None = None
    expires_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# REFUND SCHEMAS
# ============================================================================

class RefundCreate(BaseModel):
    """Création remboursement."""
    payment_intent_id: int  # ID interne
    amount: Decimal | None = None  # None = remboursement total
    reason: str | None = None  # duplicate, fraudulent, requested_by_customer
    description: str | None = None
    metadata: dict[str, str] | None = None


class RefundResponse(BaseModel):
    """Réponse remboursement."""
    id: int
    stripe_refund_id: str
    payment_intent_id: int
    amount: Decimal
    currency: str
    status: RefundStatus
    reason: str | None = None
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# DISPUTE SCHEMAS
# ============================================================================

class DisputeResponse(BaseModel):
    """Réponse litige."""
    id: int
    stripe_dispute_id: str
    stripe_charge_id: str | None = None
    amount: Decimal
    currency: str
    status: DisputeStatus
    reason: str | None = None
    evidence_due_by: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DisputeEvidenceSubmit(BaseModel):
    """Soumission preuves litige."""
    customer_name: str | None = None
    customer_email: str | None = None
    product_description: str | None = None
    shipping_documentation: str | None = None  # File ID
    receipt: str | None = None  # File ID
    uncategorized_text: str | None = None


# ============================================================================
# PRODUCT & PRICE SCHEMAS
# ============================================================================

class StripeProductCreate(BaseModel):
    """Création produit Stripe."""
    name: str
    description: str | None = None
    product_id: int | None = None  # Lien produit AZALS
    plan_id: int | None = None  # Lien plan abonnement AZALS
    images: list[str] | None = None
    metadata: dict[str, str] | None = None


class StripeProductResponse(BaseModel):
    """Réponse produit Stripe."""
    id: int
    stripe_product_id: str
    name: str
    description: str | None = None
    product_id: int | None = None
    plan_id: int | None = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StripePriceCreate(BaseModel):
    """Création prix Stripe."""
    product_id: int  # ID interne produit
    unit_amount: Decimal  # En centimes
    currency: str = "EUR"
    recurring_interval: str | None = None  # month, year
    recurring_interval_count: int = 1
    nickname: str | None = None
    metadata: dict[str, str] | None = None


class StripePriceResponse(BaseModel):
    """Réponse prix Stripe."""
    id: int
    stripe_price_id: str
    unit_amount: Decimal
    currency: str
    recurring_interval: str | None = None
    recurring_interval_count: int
    active: bool
    nickname: str | None = None
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

    @field_validator("return_url", "refresh_url")
    @classmethod
    def validate_urls(cls, v):
        """SÉCURITÉ: Valider les URLs de redirection."""
        return _validate_redirect_url(v)


class ConnectAccountResponse(BaseModel):
    """Réponse compte Connect."""
    id: int
    stripe_account_id: str
    vendor_id: int | None = None
    email: str | None = None
    account_type: str
    status: StripeAccountStatus
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    onboarding_url: str | None = None
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
    arrival_date: datetime | None = None
    description: str | None = None
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
    object_type: str | None = None
    object_id: str | None = None
    status: WebhookStatus
    processed_at: datetime | None = None
    processing_error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# CONFIG SCHEMAS
# ============================================================================

class StripeConfigCreate(BaseModel):
    """Configuration Stripe."""
    api_key_live: str | None = None
    api_key_test: str | None = None
    webhook_secret_live: str | None = None
    webhook_secret_test: str | None = None
    is_live_mode: bool = False
    default_currency: str = "EUR"
    default_payment_methods: list[str] = ["card"]
    statement_descriptor: str | None = None
    auto_capture: bool = True
    send_receipts: bool = True


class StripeConfigUpdate(BaseModel):
    """Mise à jour configuration."""
    api_key_live: str | None = None
    api_key_test: str | None = None
    webhook_secret_live: str | None = None
    webhook_secret_test: str | None = None
    is_live_mode: bool | None = None
    default_currency: str | None = None
    statement_descriptor: str | None = None
    auto_capture: bool | None = None
    send_receipts: bool | None = None
    connect_enabled: bool | None = None
    platform_fee_percent: Decimal | None = None


class StripeConfigResponse(BaseModel):
    """Réponse configuration."""
    id: int
    tenant_id: str
    is_live_mode: bool
    default_currency: str
    default_payment_methods: list[str]
    statement_descriptor: str | None = None
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
    recent_payments: list[dict[str, Any]]
    recent_refunds: list[dict[str, Any]]


class PaymentAnalytics(BaseModel):
    """Analytics paiements."""
    period: str  # daily, weekly, monthly
    start_date: datetime
    end_date: datetime
    total_volume: Decimal
    total_count: int
    average_amount: Decimal
    by_method: dict[str, Decimal]
    by_status: dict[str, int]
    by_currency: dict[str, Decimal]
    chart_data: list[dict[str, Any]]


# ============================================================================
# TRANSFER SCHEMAS (pour Connect)
# ============================================================================

class TransferCreate(BaseModel):
    """Création transfert vers compte Connect."""
    destination_account_id: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "EUR"
    description: str | None = None
    source_transaction: str | None = None  # Charge ID
    metadata: dict[str, str] | None = None


class TransferResponse(BaseModel):
    """Réponse transfert."""
    stripe_transfer_id: str
    destination_account_id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
