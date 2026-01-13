"""
AZALS MODULE 14 - Subscriptions Models
=======================================
Modèles SQLAlchemy pour la gestion des abonnements.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class PlanInterval(str, PyEnum):
    """Intervalle de facturation."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    LIFETIME = "lifetime"


class SubscriptionStatus(str, PyEnum):
    """Statut abonnement."""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELED = "canceled"
    EXPIRED = "expired"
    UNPAID = "unpaid"


class InvoiceStatus(str, PyEnum):
    """Statut facture."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class PaymentStatus(str, PyEnum):
    """Statut paiement."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class UsageType(str, PyEnum):
    """Type d'usage."""
    LICENSED = "licensed"  # Nombre fixe d'utilisateurs/seats
    METERED = "metered"    # Basé sur l'usage réel
    RATED = "rated"        # Tarif par unité


# ============================================================================
# PLAN MODELS
# ============================================================================

class SubscriptionPlan(Base):
    """Plan d'abonnement."""
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Tarification
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=False, default="EUR")
    interval: Mapped[str | None] = mapped_column(Enum(PlanInterval), nullable=False, default=PlanInterval.MONTHLY)
    interval_count: Mapped[int] = mapped_column(Integer, default=1)

    # Période d'essai
    trial_days: Mapped[int | None] = mapped_column(Integer, default=0)
    trial_once: Mapped[bool | None] = mapped_column(Boolean, default=True)  # Une seule période d'essai par client

    # Limites
    max_users: Mapped[int | None] = mapped_column(Integer)  # None = illimité
    max_storage_gb: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_api_calls: Mapped[int | None] = mapped_column(Integer)

    # Fonctionnalités incluses
    features: Mapped[dict | None] = mapped_column(JSON)  # {"feature_code": true/false ou limite}
    modules_included: Mapped[dict | None] = mapped_column(JSON)  # ["module1", "module2"]

    # Prix par utilisateur additionnel
    per_user_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    included_users: Mapped[int | None] = mapped_column(Integer, default=1)

    # Configuration facturation
    billing_scheme: Mapped[str | None] = mapped_column(String(20), default="per_unit")  # per_unit, tiered, volume
    tiers: Mapped[dict | None] = mapped_column(JSON)  # Pour pricing par paliers

    # Setup fees
    setup_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    setup_fee_behavior: Mapped[str | None] = mapped_column(String(20), default="once")  # once, recurring

    # Metadata
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool | None] = mapped_column(Boolean, default=True)  # Visible dans le catalogue
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    subscriptions = relationship("Subscription", back_populates="plan")
    add_ons = relationship("PlanAddOn", back_populates="plan")

    __table_args__ = (
        Index('idx_sub_plans_tenant', 'tenant_id'),
        Index('idx_sub_plans_code', 'tenant_id', 'code', unique=True),
        Index('idx_sub_plans_active', 'tenant_id', 'is_active'),
    )


class PlanAddOn(Base):
    """Add-on de plan."""
    __tablename__ = "subscription_plan_addons"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscription_plans.id"), nullable=False)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Tarification
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    usage_type: Mapped[str | None] = mapped_column(Enum(UsageType), default=UsageType.LICENSED)
    unit_name: Mapped[str | None] = mapped_column(String(50))  # "utilisateur", "Go", "appel API"

    # Quantités
    min_quantity: Mapped[int | None] = mapped_column(Integer, default=0)
    max_quantity: Mapped[int | None] = mapped_column(Integer)

    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    plan = relationship("SubscriptionPlan", back_populates="add_ons")

    __table_args__ = (
        Index('idx_plan_addons_tenant', 'tenant_id'),
        Index('idx_plan_addons_plan', 'plan_id'),
    )


# ============================================================================
# SUBSCRIPTION MODELS
# ============================================================================

class Subscription(Base):
    """Abonnement client."""
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    subscription_number: Mapped[str | None] = mapped_column(String(50), nullable=False, unique=True)
    external_id: Mapped[str | None] = mapped_column(String(100))  # ID Stripe/autre

    # Relation plan et client
    plan_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscription_plans.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)  # Référence CRM
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_email: Mapped[str | None] = mapped_column(String(255))

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIALING)

    # Quantités
    quantity: Mapped[int | None] = mapped_column(Integer, default=1)  # Nombre d'utilisateurs/seats
    current_users: Mapped[int | None] = mapped_column(Integer, default=0)

    # Période d'essai
    trial_start: Mapped[date | None] = mapped_column(Date)
    trial_end: Mapped[date | None] = mapped_column(Date)

    # Période d'abonnement
    current_period_start: Mapped[date] = mapped_column(Date)
    current_period_end: Mapped[date] = mapped_column(Date)
    started_at: Mapped[date] = mapped_column(Date)
    ended_at: Mapped[date | None] = mapped_column(Date)

    # Annulation
    cancel_at_period_end: Mapped[bool | None] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    # Pause
    paused_at: Mapped[datetime | None] = mapped_column(DateTime)
    resume_at: Mapped[date | None] = mapped_column(Date)

    # Facturation
    billing_cycle_anchor: Mapped[int | None] = mapped_column(Integer, default=1)  # Jour du mois
    collection_method: Mapped[str | None] = mapped_column(String(20), default="charge_automatically")
    default_payment_method_id: Mapped[str | None] = mapped_column(String(100))

    # Remises
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)
    discount_end_date: Mapped[date | None] = mapped_column(Date)
    coupon_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscription_coupons.id"))

    # Métriques
    mrr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)  # Monthly Recurring Revenue
    arr: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), default=0)  # Annual Recurring Revenue

    # Metadata
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    items = relationship("SubscriptionItem", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("SubscriptionInvoice", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")
    coupon = relationship("SubscriptionCoupon")

    __table_args__ = (
        Index('idx_subscriptions_tenant', 'tenant_id'),
        Index('idx_subscriptions_customer', 'tenant_id', 'customer_id'),
        Index('idx_subscriptions_status', 'tenant_id', 'status'),
        Index('idx_subscriptions_period', 'tenant_id', 'current_period_end'),
    )


class SubscriptionItem(Base):
    """Élément d'abonnement (add-ons, quantités)."""
    __tablename__ = "subscription_items"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscriptions.id"), nullable=False)

    # Identification
    add_on_code: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Tarification
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer, default=1)
    usage_type: Mapped[str | None] = mapped_column(Enum(UsageType), default=UsageType.LICENSED)

    # Pour usage metered
    metered_usage: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), default=0)
    billing_threshold: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    subscription = relationship("Subscription", back_populates="items")

    __table_args__ = (
        Index('idx_sub_items_subscription', 'subscription_id'),
    )


class SubscriptionChange(Base):
    """Historique des changements d'abonnement."""
    __tablename__ = "subscription_changes"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscriptions.id"), nullable=False)

    # Type de changement
    change_type: Mapped[str | None] = mapped_column(String(50), nullable=False)  # upgrade, downgrade, quantity_change, cancel, pause, resume
    change_reason: Mapped[str | None] = mapped_column(Text)

    # Avant/Après
    previous_plan_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    new_plan_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    previous_quantity: Mapped[int | None] = mapped_column(Integer)
    new_quantity: Mapped[int | None] = mapped_column(Integer)
    previous_mrr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    new_mrr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    # Proratisation
    proration_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    effective_date: Mapped[date] = mapped_column(Date)

    # Metadata
    changed_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # User ID
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sub_changes_subscription', 'subscription_id'),
        Index('idx_sub_changes_date', 'tenant_id', 'created_at'),
    )


# ============================================================================
# INVOICE MODELS
# ============================================================================

class SubscriptionInvoice(Base):
    """Facture d'abonnement."""
    __tablename__ = "subscription_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscriptions.id"), nullable=False)

    # Identification
    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=False, unique=True)
    external_id: Mapped[str | None] = mapped_column(String(100))  # ID Stripe/autre

    # Client
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_email: Mapped[str | None] = mapped_column(String(255))
    billing_address: Mapped[dict | None] = mapped_column(JSON)

    # Statut et dates
    status: Mapped[str | None] = mapped_column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Montants
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)
    amount_remaining: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)

    # Devise
    currency: Mapped[str | None] = mapped_column(String(3), nullable=False, default="EUR")

    # Paiement
    payment_intent_id: Mapped[str | None] = mapped_column(String(100))
    default_payment_method: Mapped[str | None] = mapped_column(String(100))
    collection_method: Mapped[str | None] = mapped_column(String(20), default="charge_automatically")

    # Tentatives de recouvrement
    attempt_count: Mapped[int | None] = mapped_column(Integer, default=0)
    next_payment_attempt: Mapped[datetime | None] = mapped_column(DateTime)

    # Métadonnées
    hosted_invoice_url: Mapped[str | None] = mapped_column(String(500))
    pdf_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    footer: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    subscription = relationship("Subscription", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("SubscriptionPayment", back_populates="invoice")

    __table_args__ = (
        Index('idx_sub_invoices_tenant', 'tenant_id'),
        Index('idx_sub_invoices_subscription', 'subscription_id'),
        Index('idx_sub_invoices_status', 'tenant_id', 'status'),
        Index('idx_sub_invoices_customer', 'tenant_id', 'customer_id'),
        Index('idx_sub_invoices_due', 'tenant_id', 'due_date'),
    )


class InvoiceLine(Base):
    """Ligne de facture."""
    __tablename__ = "subscription_invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscription_invoices.id"), nullable=False)

    # Description
    description: Mapped[str | None] = mapped_column(String(500), nullable=False)
    item_type: Mapped[str | None] = mapped_column(String(50))  # subscription, add_on, usage, proration, setup_fee

    # Période
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)

    # Quantités et prix
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), default=1)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=False)

    # Taxes
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)

    # Référence
    subscription_item_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    proration: Mapped[bool | None] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    invoice = relationship("SubscriptionInvoice", back_populates="lines")

    __table_args__ = (
        Index('idx_inv_lines_invoice', 'invoice_id'),
    )


# ============================================================================
# PAYMENT MODELS
# ============================================================================

class SubscriptionPayment(Base):
    """Paiement d'abonnement."""
    __tablename__ = "subscription_payments"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscription_invoices.id"))

    # Identification
    payment_number: Mapped[str | None] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100))  # ID Stripe/autre

    # Client
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)

    # Montant
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=False, default="EUR")
    fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)  # Frais de transaction

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    # Mode de paiement
    payment_method_type: Mapped[str | None] = mapped_column(String(30))  # card, bank_transfer, sepa
    payment_method_id: Mapped[str | None] = mapped_column(String(100))
    payment_method_details: Mapped[dict | None] = mapped_column(JSON)  # Derniers chiffres carte, etc.

    # Dates
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # En cas d'échec
    failure_code: Mapped[str | None] = mapped_column(String(50))
    failure_message: Mapped[str | None] = mapped_column(Text)

    # Remboursement
    refunded_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)
    refund_reason: Mapped[str | None] = mapped_column(Text)

    # Relations
    invoice = relationship("SubscriptionInvoice", back_populates="payments")

    __table_args__ = (
        Index('idx_sub_payments_tenant', 'tenant_id'),
        Index('idx_sub_payments_invoice', 'invoice_id'),
        Index('idx_sub_payments_customer', 'tenant_id', 'customer_id'),
        Index('idx_sub_payments_status', 'tenant_id', 'status'),
    )


# ============================================================================
# USAGE MODELS
# ============================================================================

class UsageRecord(Base):
    """Enregistrement d'usage pour abonnements metered."""
    __tablename__ = "subscription_usage_records"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscriptions.id"), nullable=False)
    subscription_item_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("subscription_items.id"))

    # Usage
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50))  # API calls, GB, users, etc.
    action: Mapped[str | None] = mapped_column(String(20), nullable=False, default="increment")  # set, increment

    # Période
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)

    # Identification
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True)

    # Metadata
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    subscription = relationship("Subscription", back_populates="usage_records")

    __table_args__ = (
        Index('idx_usage_records_subscription', 'subscription_id'),
        Index('idx_usage_records_period', 'tenant_id', 'period_start', 'period_end'),
        Index('idx_usage_records_timestamp', 'subscription_id', 'timestamp'),
    )


# ============================================================================
# COUPON MODELS
# ============================================================================

class SubscriptionCoupon(Base):
    """Code promo/coupon pour abonnements."""
    __tablename__ = "subscription_coupons"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Réduction
    discount_type: Mapped[str | None] = mapped_column(String(20), nullable=False)  # percent, fixed_amount
    discount_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))  # Pour fixed_amount

    # Durée
    duration: Mapped[str | None] = mapped_column(String(20), nullable=False, default="once")  # once, repeating, forever
    duration_months: Mapped[int | None] = mapped_column(Integer)  # Pour repeating

    # Limites
    max_redemptions: Mapped[int | None] = mapped_column(Integer)
    times_redeemed: Mapped[int | None] = mapped_column(Integer, default=0)

    # Restrictions
    applies_to_plans: Mapped[dict | None] = mapped_column(JSON)  # Liste des plan_ids concernés
    min_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    first_time_only: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Validité
    valid_from: Mapped[datetime | None] = mapped_column(DateTime)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sub_coupons_tenant', 'tenant_id'),
        Index('idx_sub_coupons_code', 'tenant_id', 'code', unique=True),
        Index('idx_sub_coupons_active', 'tenant_id', 'is_active'),
    )


# ============================================================================
# METRICS MODELS
# ============================================================================

class SubscriptionMetrics(Base):
    """Métriques d'abonnement (snapshot quotidien)."""
    __tablename__ = "subscription_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Date du snapshot
    metric_date: Mapped[date] = mapped_column(Date)

    # Revenus
    mrr: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), default=0)  # Monthly Recurring Revenue
    arr: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), default=0)  # Annual Recurring Revenue
    new_mrr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)  # Nouveaux abonnements
    expansion_mrr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)  # Upgrades
    contraction_mrr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)  # Downgrades
    churned_mrr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)  # Annulations

    # Compteurs
    total_subscriptions: Mapped[int | None] = mapped_column(Integer, default=0)
    active_subscriptions: Mapped[int | None] = mapped_column(Integer, default=0)
    trialing_subscriptions: Mapped[int | None] = mapped_column(Integer, default=0)
    canceled_subscriptions: Mapped[int | None] = mapped_column(Integer, default=0)
    new_subscriptions: Mapped[int | None] = mapped_column(Integer, default=0)
    churned_subscriptions: Mapped[int | None] = mapped_column(Integer, default=0)

    # Clients
    total_customers: Mapped[int | None] = mapped_column(Integer, default=0)
    new_customers: Mapped[int | None] = mapped_column(Integer, default=0)
    churned_customers: Mapped[int | None] = mapped_column(Integer, default=0)

    # Taux
    churn_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)  # % mensuel
    trial_conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=0)

    # ARPU (Average Revenue Per User)
    arpu: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=0)

    # LTV (Lifetime Value)
    average_ltv: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=0)

    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sub_metrics_tenant_date', 'tenant_id', 'metric_date', unique=True),
    )


# ============================================================================
# WEBHOOK EVENTS
# ============================================================================

class SubscriptionWebhook(Base):
    """Événements webhook abonnement."""
    __tablename__ = "subscription_webhooks"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    event_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=False)

    # Source
    source: Mapped[str | None] = mapped_column(String(50), nullable=False)  # stripe, paypal, internal

    # Données
    payload: Mapped[dict] = mapped_column(JSON)
    related_object_type: Mapped[str | None] = mapped_column(String(50))  # subscription, invoice, payment
    related_object_id: Mapped[str | None] = mapped_column(String(100))

    # Traitement
    is_processed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)
    processing_error: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int | None] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sub_webhooks_tenant', 'tenant_id'),
        Index('idx_sub_webhooks_type', 'tenant_id', 'event_type'),
        Index('idx_sub_webhooks_processed', 'is_processed'),
    )
