"""
AZALS - Module Marketplace - Schémas
====================================
Schémas Pydantic pour le site marchand.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import Any

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from .models import BillingCycle, OrderStatus, PaymentMethod, PlanType

# ============================================================================
# PLANS
# ============================================================================

class PlanFeature(BaseModel):
    """Fonctionnalité d'un plan."""
    name: str
    included: bool
    description: str | None = None


class CommercialPlanResponse(BaseModel):
    """Réponse plan commercial."""
    id: UUID
    code: str
    name: str
    plan_type: PlanType
    description: str | None
    price_monthly: Decimal
    price_annual: Decimal
    currency: str
    max_users: int
    max_storage_gb: int
    max_documents_month: int
    modules_included: list[str]
    features: list[str]
    trial_days: int
    setup_fee: Decimal
    is_featured: bool

    class Config:
        from_attributes = True


class PlanComparison(BaseModel):
    """Comparatif des plans."""
    plans: list[CommercialPlanResponse]
    features: list[dict[str, Any]]  # Matrice features x plans


# ============================================================================
# COMMANDES
# ============================================================================

class CheckoutRequest(BaseModel):
    """Requête de checkout."""
    plan_code: str
    billing_cycle: BillingCycle
    customer_email: EmailStr
    customer_name: str
    company_name: str | None = None
    company_siret: str | None = None
    phone: str | None = None
    billing_address_line1: str
    billing_address_line2: str | None = None
    billing_city: str
    billing_postal_code: str
    billing_country: str = "FR"
    payment_method: PaymentMethod
    discount_code: str | None = None
    accept_terms: bool = Field(..., description="Acceptation CGV obligatoire")
    accept_privacy: bool = Field(..., description="Acceptation politique confidentialité obligatoire")


class CheckoutResponse(BaseModel):
    """Réponse checkout."""
    order_id: str
    order_number: str
    status: OrderStatus
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str
    payment_intent_client_secret: str | None  # Pour Stripe
    checkout_url: str | None  # Pour PayPal
    instructions: str | None  # Pour virement


class OrderResponse(BaseModel):
    """Réponse commande."""
    id: UUID
    order_number: str
    status: OrderStatus
    plan_code: str
    billing_cycle: BillingCycle
    customer_email: str
    customer_name: str | None
    company_name: str | None
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str
    payment_method: PaymentMethod | None
    paid_at: datetime | None
    tenant_id: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class OrderDetail(OrderResponse):
    """Détail complet d'une commande."""
    company_siret: str | None
    phone: str | None
    billing_address_line1: str | None
    billing_address_line2: str | None
    billing_city: str | None
    billing_postal_code: str | None
    billing_country: str | None
    payment_intent_id: str | None
    payment_status: str | None
    tenant_created_at: datetime | None
    notes: str | None


# ============================================================================
# CODES PROMO
# ============================================================================

class DiscountCodeValidate(BaseModel):
    """Validation code promo."""
    code: str
    plan_code: str
    order_amount: Decimal


class DiscountCodeResponse(BaseModel):
    """Réponse code promo."""
    code: str
    valid: bool
    discount_type: str | None
    discount_value: Decimal | None
    final_discount: Decimal | None
    message: str


# ============================================================================
# PROVISIONING
# ============================================================================

class TenantProvisionRequest(BaseModel):
    """Requête de provisioning tenant."""
    order_id: str


class TenantProvisionResponse(BaseModel):
    """Réponse provisioning tenant."""
    tenant_id: str
    admin_email: str
    login_url: str
    temporary_password: str | None  # Affiché une seule fois
    welcome_email_sent: bool


# ============================================================================
# WEBHOOK
# ============================================================================

class StripeWebhookPayload(BaseModel):
    """Payload webhook Stripe."""
    id: str
    type: str
    data: dict[str, Any]


# ============================================================================
# STATISTIQUES
# ============================================================================

class MarketplaceStats(BaseModel):
    """Statistiques marketplace."""
    total_orders: int
    total_revenue: Decimal
    orders_today: int
    revenue_today: Decimal
    orders_month: int
    revenue_month: Decimal
    conversion_rate: float
    avg_order_value: Decimal
    by_plan: dict[str, int]
    by_billing_cycle: dict[str, int]


class MarketplaceDashboard(BaseModel):
    """Dashboard marketplace."""
    stats: MarketplaceStats
    recent_orders: list[OrderResponse]
    popular_plans: list[CommercialPlanResponse]
