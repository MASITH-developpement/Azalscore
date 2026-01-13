"""
AZALS - Module Marketplace - Modèles
====================================
Modèles pour les offres commerciales et abonnements.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Numeric, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class PlanType(str, Enum):
    """Type de plan."""
    ESSENTIEL = "essentiel"
    PRO = "pro"
    ENTREPRISE = "entreprise"


class BillingCycle(str, Enum):
    """Cycle de facturation."""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PaymentMethod(str, Enum):
    """Méthode de paiement."""
    CARD = "card"
    SEPA = "sepa"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"


class OrderStatus(str, Enum):
    """Statut de commande."""
    PENDING = "pending"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    PROVISIONING = "provisioning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class CommercialPlan(Base):
    """Plan commercial (Essentiel/Pro/Entreprise)."""
    __tablename__ = "commercial_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False)
    description = Column(Text)

    # Tarification mensuelle
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_annual = Column(Numeric(10, 2), nullable=False)  # Prix annuel total (avec remise)
    currency = Column(String(3), default="EUR")

    # Limites
    max_users = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=10)
    max_documents_month = Column(Integer, default=100)
    max_api_calls_month = Column(Integer, default=10000)

    # Modules inclus
    modules_included = Column(JSON, default=list)  # ["commercial", "finance", "hr", ...]
    features = Column(JSON, default=list)  # ["support_email", "support_phone", ...]

    # Options
    trial_days = Column(Integer, default=14)
    setup_fee = Column(Numeric(10, 2), default=0)

    # Stripe
    stripe_price_id_monthly = Column(String(100))
    stripe_price_id_annual = Column(String(100))
    stripe_product_id = Column(String(100))

    # État
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        {'extend_existing': True}
    )


class Order(Base):
    """Commande client (site marchand)."""
    __tablename__ = "marketplace_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), nullable=False, unique=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)

    # Plan commandé
    plan_id = Column(UUID(as_uuid=True), nullable=False)
    plan_code = Column(String(50), nullable=False)
    billing_cycle = Column(SQLEnum(BillingCycle), nullable=False)

    # Client
    customer_email = Column(String(255), nullable=False, index=True)
    customer_name = Column(String(255))
    company_name = Column(String(255))
    company_siret = Column(String(20))
    phone = Column(String(50))

    # Adresse facturation
    billing_address_line1 = Column(String(255))
    billing_address_line2 = Column(String(255))
    billing_city = Column(String(100))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(2), default="FR")

    # Montants
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=20.00)  # TVA 20%
    tax_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    discount_code = Column(String(50))
    total = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Paiement
    payment_method = Column(SQLEnum(PaymentMethod))
    payment_intent_id = Column(String(100))  # Stripe PaymentIntent
    payment_status = Column(String(50))
    paid_at = Column(DateTime)

    # Tenant créé
    tenant_id = Column(String(50), index=True)
    tenant_created_at = Column(DateTime)

    # Métadonnées
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    source = Column(String(50), default="website")  # website, api, admin
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    __table_args__ = (
        {'extend_existing': True}
    )


class DiscountCode(Base):
    """Code promo / réduction."""
    __tablename__ = "discount_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))

    # Type de réduction
    discount_type = Column(String(20), default="percent")  # percent, fixed
    discount_value = Column(Numeric(10, 2), nullable=False)
    max_discount = Column(Numeric(10, 2))  # Plafond si percent

    # Restrictions
    applicable_plans = Column(JSON)  # null = tous les plans
    min_order_amount = Column(Numeric(10, 2))
    first_order_only = Column(Boolean, default=False)

    # Validité
    starts_at = Column(DateTime)
    expires_at = Column(DateTime)
    max_uses = Column(Integer)
    used_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        {'extend_existing': True}
    )


class WebhookEvent(Base):
    """Événements webhook Stripe."""
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), default="stripe")
    event_id = Column(String(100), nullable=False, unique=True)
    event_type = Column(String(100), nullable=False, index=True)

    # Payload
    payload = Column(JSON, nullable=False)
    signature = Column(String(500))

    # Traitement
    status = Column(String(50), default="received")  # received, processing, processed, failed
    processed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Liens
    order_id = Column(UUID(as_uuid=True))
    tenant_id = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        {'extend_existing': True}
    )
