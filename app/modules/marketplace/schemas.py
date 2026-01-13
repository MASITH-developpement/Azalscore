"""
AZALS - Module Marketplace - Schémas
====================================
Schémas Pydantic pour le site marchand.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

from .models import PlanType, BillingCycle, PaymentMethod, OrderStatus


# ============================================================================
# PLANS
# ============================================================================

class PlanFeature(BaseModel):
    """Fonctionnalité d'un plan."""
    name: str
    included: bool
    description: Optional[str] = None


class CommercialPlanResponse(BaseModel):
    """Réponse plan commercial."""
    id: str
    code: str
    name: str
    plan_type: PlanType
    description: Optional[str]
    price_monthly: Decimal
    price_annual: Decimal
    currency: str
    max_users: int
    max_storage_gb: int
    max_documents_month: int
    modules_included: List[str]
    features: List[str]
    trial_days: int
    setup_fee: Decimal
    is_featured: bool

    class Config:
        from_attributes = True


class PlanComparison(BaseModel):
    """Comparatif des plans."""
    plans: List[CommercialPlanResponse]
    features: List[Dict[str, Any]]  # Matrice features x plans


# ============================================================================
# COMMANDES
# ============================================================================

class CheckoutRequest(BaseModel):
    """Requête de checkout."""
    plan_code: str
    billing_cycle: BillingCycle
    customer_email: EmailStr
    customer_name: str
    company_name: Optional[str] = None
    company_siret: Optional[str] = None
    phone: Optional[str] = None
    billing_address_line1: str
    billing_address_line2: Optional[str] = None
    billing_city: str
    billing_postal_code: str
    billing_country: str = "FR"
    payment_method: PaymentMethod
    discount_code: Optional[str] = None
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
    payment_intent_client_secret: Optional[str]  # Pour Stripe
    checkout_url: Optional[str]  # Pour PayPal
    instructions: Optional[str]  # Pour virement


class OrderResponse(BaseModel):
    """Réponse commande."""
    id: str
    order_number: str
    status: OrderStatus
    plan_code: str
    billing_cycle: BillingCycle
    customer_email: str
    customer_name: Optional[str]
    company_name: Optional[str]
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str
    payment_method: Optional[PaymentMethod]
    paid_at: Optional[datetime]
    tenant_id: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderDetail(OrderResponse):
    """Détail complet d'une commande."""
    company_siret: Optional[str]
    phone: Optional[str]
    billing_address_line1: Optional[str]
    billing_address_line2: Optional[str]
    billing_city: Optional[str]
    billing_postal_code: Optional[str]
    billing_country: Optional[str]
    payment_intent_id: Optional[str]
    payment_status: Optional[str]
    tenant_created_at: Optional[datetime]
    notes: Optional[str]


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
    discount_type: Optional[str]
    discount_value: Optional[Decimal]
    final_discount: Optional[Decimal]
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
    temporary_password: Optional[str]  # Affiché une seule fois
    welcome_email_sent: bool


# ============================================================================
# WEBHOOK
# ============================================================================

class StripeWebhookPayload(BaseModel):
    """Payload webhook Stripe."""
    id: str
    type: str
    data: Dict[str, Any]


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
    by_plan: Dict[str, int]
    by_billing_cycle: Dict[str, int]


class MarketplaceDashboard(BaseModel):
    """Dashboard marketplace."""
    stats: MarketplaceStats
    recent_orders: List[OrderResponse]
    popular_plans: List[CommercialPlanResponse]
