"""
AZALS MODULE 14 - Subscriptions Models
=======================================
Modèles SQLAlchemy pour la gestion des abonnements.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date,
    ForeignKey, Numeric, Enum, Index, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Tarification
    base_price = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EUR")
    interval = Column(Enum(PlanInterval), nullable=False, default=PlanInterval.MONTHLY)
    interval_count = Column(Integer, nullable=False, default=1)

    # Période d'essai
    trial_days = Column(Integer, default=0)
    trial_once = Column(Boolean, default=True)  # Une seule période d'essai par client

    # Limites
    max_users = Column(Integer)  # None = illimité
    max_storage_gb = Column(Numeric(10, 2))
    max_api_calls = Column(Integer)

    # Fonctionnalités incluses
    features = Column(JSON)  # {"feature_code": true/false ou limite}
    modules_included = Column(JSON)  # ["module1", "module2"]

    # Prix par utilisateur additionnel
    per_user_price = Column(Numeric(10, 2), default=0)
    included_users = Column(Integer, default=1)

    # Configuration facturation
    billing_scheme = Column(String(20), default="per_unit")  # per_unit, tiered, volume
    tiers = Column(JSON)  # Pour pricing par paliers

    # Setup fees
    setup_fee = Column(Numeric(10, 2), default=0)
    setup_fee_behavior = Column(String(20), default="once")  # once, recurring

    # Metadata
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Visible dans le catalogue
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Tarification
    price = Column(Numeric(10, 2), nullable=False, default=0)
    usage_type = Column(Enum(UsageType), default=UsageType.LICENSED)
    unit_name = Column(String(50))  # "utilisateur", "Go", "appel API"

    # Quantités
    min_quantity = Column(Integer, default=0)
    max_quantity = Column(Integer)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    subscription_number = Column(String(50), nullable=False, unique=True)
    external_id = Column(String(100))  # ID Stripe/autre

    # Relation plan et client
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    customer_id = Column(Integer, nullable=False, index=True)  # Référence CRM
    customer_name = Column(String(255))
    customer_email = Column(String(255))

    # Statut
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIALING)

    # Quantités
    quantity = Column(Integer, default=1)  # Nombre d'utilisateurs/seats
    current_users = Column(Integer, default=0)

    # Période d'essai
    trial_start = Column(Date)
    trial_end = Column(Date)

    # Période d'abonnement
    current_period_start = Column(Date, nullable=False)
    current_period_end = Column(Date, nullable=False)
    started_at = Column(Date, nullable=False)
    ended_at = Column(Date)

    # Annulation
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime)
    cancellation_reason = Column(Text)

    # Pause
    paused_at = Column(DateTime)
    resume_at = Column(Date)

    # Facturation
    billing_cycle_anchor = Column(Integer, default=1)  # Jour du mois
    collection_method = Column(String(20), default="charge_automatically")
    default_payment_method_id = Column(String(100))

    # Remises
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_end_date = Column(Date)
    coupon_id = Column(Integer, ForeignKey("subscription_coupons.id"))

    # Métriques
    mrr = Column(Numeric(12, 2), default=0)  # Monthly Recurring Revenue
    arr = Column(Numeric(14, 2), default=0)  # Annual Recurring Revenue

    # Metadata
    extra_data = Column(JSON)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    # Identification
    add_on_code = Column(String(50))
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Tarification
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=1)
    usage_type = Column(Enum(UsageType), default=UsageType.LICENSED)

    # Pour usage metered
    metered_usage = Column(Numeric(14, 4), default=0)
    billing_threshold = Column(Numeric(10, 2))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    subscription = relationship("Subscription", back_populates="items")

    __table_args__ = (
        Index('idx_sub_items_subscription', 'subscription_id'),
    )


class SubscriptionChange(Base):
    """Historique des changements d'abonnement."""
    __tablename__ = "subscription_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    # Type de changement
    change_type = Column(String(50), nullable=False)  # upgrade, downgrade, quantity_change, cancel, pause, resume
    change_reason = Column(Text)

    # Avant/Après
    previous_plan_id = Column(Integer)
    new_plan_id = Column(Integer)
    previous_quantity = Column(Integer)
    new_quantity = Column(Integer)
    previous_mrr = Column(Numeric(12, 2))
    new_mrr = Column(Numeric(12, 2))

    # Proratisation
    proration_amount = Column(Numeric(10, 2), default=0)
    effective_date = Column(Date, nullable=False)

    # Metadata
    changed_by = Column(Integer)  # User ID
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    # Identification
    invoice_number = Column(String(50), nullable=False, unique=True)
    external_id = Column(String(100))  # ID Stripe/autre

    # Client
    customer_id = Column(Integer, nullable=False)
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    billing_address = Column(JSON)

    # Statut et dates
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date)
    finalized_at = Column(DateTime)
    paid_at = Column(DateTime)
    voided_at = Column(DateTime)

    # Montants
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    amount_paid = Column(Numeric(12, 2), default=0)
    amount_remaining = Column(Numeric(12, 2), default=0)

    # Devise
    currency = Column(String(3), nullable=False, default="EUR")

    # Paiement
    payment_intent_id = Column(String(100))
    default_payment_method = Column(String(100))
    collection_method = Column(String(20), default="charge_automatically")

    # Tentatives de recouvrement
    attempt_count = Column(Integer, default=0)
    next_payment_attempt = Column(DateTime)

    # Métadonnées
    hosted_invoice_url = Column(String(500))
    pdf_url = Column(String(500))
    notes = Column(Text)
    footer = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("subscription_invoices.id"), nullable=False)

    # Description
    description = Column(String(500), nullable=False)
    item_type = Column(String(50))  # subscription, add_on, usage, proration, setup_fee

    # Période
    period_start = Column(Date)
    period_end = Column(Date)

    # Quantités et prix
    quantity = Column(Numeric(14, 4), default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    amount = Column(Numeric(12, 2), nullable=False)

    # Taxes
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)

    # Référence
    subscription_item_id = Column(Integer)
    proration = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("subscription_invoices.id"))

    # Identification
    payment_number = Column(String(50), nullable=False)
    external_id = Column(String(100))  # ID Stripe/autre

    # Client
    customer_id = Column(Integer, nullable=False)

    # Montant
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    fee_amount = Column(Numeric(10, 2), default=0)  # Frais de transaction

    # Statut
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    # Mode de paiement
    payment_method_type = Column(String(30))  # card, bank_transfer, sepa
    payment_method_id = Column(String(100))
    payment_method_details = Column(JSON)  # Derniers chiffres carte, etc.

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # En cas d'échec
    failure_code = Column(String(50))
    failure_message = Column(Text)

    # Remboursement
    refunded_amount = Column(Numeric(12, 2), default=0)
    refund_reason = Column(Text)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    subscription_item_id = Column(Integer, ForeignKey("subscription_items.id"))

    # Usage
    quantity = Column(Numeric(14, 4), nullable=False)
    unit = Column(String(50))  # API calls, GB, users, etc.
    action = Column(String(20), nullable=False, default="increment")  # set, increment

    # Période
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_start = Column(Date)
    period_end = Column(Date)

    # Identification
    idempotency_key = Column(String(100), unique=True)

    # Metadata
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Réduction
    discount_type = Column(String(20), nullable=False)  # percent, fixed_amount
    discount_value = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3))  # Pour fixed_amount

    # Durée
    duration = Column(String(20), nullable=False, default="once")  # once, repeating, forever
    duration_months = Column(Integer)  # Pour repeating

    # Limites
    max_redemptions = Column(Integer)
    times_redeemed = Column(Integer, default=0)

    # Restrictions
    applies_to_plans = Column(JSON)  # Liste des plan_ids concernés
    min_amount = Column(Numeric(10, 2))
    first_time_only = Column(Boolean, default=False)

    # Validité
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Date du snapshot
    metric_date = Column(Date, nullable=False)

    # Revenus
    mrr = Column(Numeric(14, 2), default=0)  # Monthly Recurring Revenue
    arr = Column(Numeric(16, 2), default=0)  # Annual Recurring Revenue
    new_mrr = Column(Numeric(12, 2), default=0)  # Nouveaux abonnements
    expansion_mrr = Column(Numeric(12, 2), default=0)  # Upgrades
    contraction_mrr = Column(Numeric(12, 2), default=0)  # Downgrades
    churned_mrr = Column(Numeric(12, 2), default=0)  # Annulations

    # Compteurs
    total_subscriptions = Column(Integer, default=0)
    active_subscriptions = Column(Integer, default=0)
    trialing_subscriptions = Column(Integer, default=0)
    canceled_subscriptions = Column(Integer, default=0)
    new_subscriptions = Column(Integer, default=0)
    churned_subscriptions = Column(Integer, default=0)

    # Clients
    total_customers = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)
    churned_customers = Column(Integer, default=0)

    # Taux
    churn_rate = Column(Numeric(5, 2), default=0)  # % mensuel
    trial_conversion_rate = Column(Numeric(5, 2), default=0)

    # ARPU (Average Revenue Per User)
    arpu = Column(Numeric(10, 2), default=0)

    # LTV (Lifetime Value)
    average_ltv = Column(Numeric(12, 2), default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sub_metrics_tenant_date', 'tenant_id', 'metric_date', unique=True),
    )


# ============================================================================
# WEBHOOK EVENTS
# ============================================================================

class SubscriptionWebhook(Base):
    """Événements webhook abonnement."""
    __tablename__ = "subscription_webhooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    event_id = Column(String(100), unique=True)
    event_type = Column(String(100), nullable=False)

    # Source
    source = Column(String(50), nullable=False)  # stripe, paypal, internal

    # Données
    payload = Column(JSON, nullable=False)
    related_object_type = Column(String(50))  # subscription, invoice, payment
    related_object_id = Column(String(100))

    # Traitement
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_error = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sub_webhooks_tenant', 'tenant_id'),
        Index('idx_sub_webhooks_type', 'tenant_id', 'event_type'),
        Index('idx_sub_webhooks_processed', 'is_processed'),
    )
