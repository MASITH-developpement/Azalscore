"""
AZALS MODULE 15 - Stripe Integration Models
============================================
Modèles SQLAlchemy pour l'intégration Stripe.
MIGRATED: All PKs and FKs use UUID for PostgreSQL compatibility.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import UniversalUUID

# ============================================================================
# ENUMS
# ============================================================================

class StripeAccountStatus(str, PyEnum):
    """Statut compte Stripe Connect."""
    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    DISABLED = "disabled"


class PaymentIntentStatus(str, PyEnum):
    """Statut PaymentIntent."""
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    REQUIRES_CAPTURE = "requires_capture"


class RefundStatus(str, PyEnum):
    """Statut remboursement."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class DisputeStatus(str, PyEnum):
    """Statut litige."""
    WARNING_NEEDS_RESPONSE = "warning_needs_response"
    WARNING_UNDER_REVIEW = "warning_under_review"
    WARNING_CLOSED = "warning_closed"
    NEEDS_RESPONSE = "needs_response"
    UNDER_REVIEW = "under_review"
    CHARGE_REFUNDED = "charge_refunded"
    WON = "won"
    LOST = "lost"


class WebhookStatus(str, PyEnum):
    """Statut traitement webhook."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


# ============================================================================
# STRIPE CUSTOMER
# ============================================================================

class StripeCustomer(Base):
    """Client Stripe synchronisé."""
    __tablename__ = "stripe_customers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_customer_id = Column(String(100), nullable=False, unique=True)

    # Lien avec CRM (UUID reference)
    customer_id = Column(UniversalUUID(), nullable=False, index=True)
    customer_type = Column(String(50), default="company")  # company, individual

    # Données client
    email = Column(String(255))
    name = Column(String(255))
    phone = Column(String(50))
    description = Column(Text)

    # Adresse
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2))

    # Paramètres facturation
    default_payment_method_id = Column(String(100))
    invoice_prefix = Column(String(20))
    tax_exempt = Column(String(20), default="none")  # none, exempt, reverse
    tax_ids = Column(JSON)  # [{type, value}]

    # Métadonnées Stripe
    stripe_metadata = Column(JSON)
    balance = Column(Numeric(12, 2), default=0)
    currency = Column(String(3))
    delinquent = Column(Boolean, default=False)

    # Synchronisation
    is_synced = Column(Boolean, default=True)
    last_synced_at = Column(DateTime)
    sync_error = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    payment_methods = relationship("StripePaymentMethod", back_populates="customer")
    payment_intents = relationship("StripePaymentIntent", back_populates="customer")

    __table_args__ = (
        Index('idx_stripe_customers_tenant', 'tenant_id'),
        Index('idx_stripe_customers_customer', 'tenant_id', 'customer_id'),
        Index('idx_stripe_customers_email', 'tenant_id', 'email'),
    )


# ============================================================================
# PAYMENT METHODS
# ============================================================================

class StripePaymentMethod(Base):
    """Méthode de paiement Stripe."""
    __tablename__ = "stripe_payment_methods"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_payment_method_id = Column(String(100), nullable=False, unique=True)
    stripe_customer_id = Column(UniversalUUID(), ForeignKey("stripe_customers.id"))

    # Type
    method_type = Column(String(30), nullable=False)  # card, sepa_debit, bank_transfer

    # Détails carte
    card_brand = Column(String(20))  # visa, mastercard, amex
    card_last4 = Column(String(4))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)
    card_funding = Column(String(20))  # credit, debit, prepaid
    card_country = Column(String(2))

    # Détails SEPA
    sepa_bank_code = Column(String(20))
    sepa_last4 = Column(String(4))
    sepa_country = Column(String(2))

    # Adresse facturation
    billing_name = Column(String(255))
    billing_email = Column(String(255))
    billing_address = Column(JSON)

    # Statut
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    customer = relationship("StripeCustomer", back_populates="payment_methods")

    __table_args__ = (
        Index('idx_stripe_pm_tenant', 'tenant_id'),
        Index('idx_stripe_pm_customer', 'stripe_customer_id'),
    )


# ============================================================================
# PAYMENT INTENTS
# ============================================================================

class StripePaymentIntent(Base):
    """PaymentIntent Stripe."""
    __tablename__ = "stripe_payment_intents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_payment_intent_id = Column(String(100), nullable=False, unique=True)
    stripe_customer_id = Column(UniversalUUID(), ForeignKey("stripe_customers.id"))

    # Montants
    amount = Column(Numeric(12, 2), nullable=False)
    amount_received = Column(Numeric(12, 2), default=0)
    currency = Column(String(3), nullable=False, default="EUR")

    # Statut
    status = Column(Enum(PaymentIntentStatus), nullable=False)
    cancellation_reason = Column(String(100))

    # Méthode de paiement
    payment_method_id = Column(String(100))
    payment_method_types = Column(JSON)  # ["card", "sepa_debit"]

    # Capture
    capture_method = Column(String(20), default="automatic")  # automatic, manual
    captured_at = Column(DateTime)

    # Client secret (pour frontend)
    client_secret = Column(String(255))

    # Références (UUID pour liens AZALS)
    invoice_id = Column(UniversalUUID())  # Lien facture AZALS
    order_id = Column(UniversalUUID())  # Lien commande AZALS
    subscription_id = Column(UniversalUUID())  # Lien abonnement AZALS
    description = Column(Text)

    # Métadonnées
    stripe_metadata = Column(JSON)
    receipt_email = Column(String(255))

    # Frais
    application_fee_amount = Column(Numeric(10, 2))
    stripe_fee = Column(Numeric(10, 2))
    net_amount = Column(Numeric(12, 2))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    customer = relationship("StripeCustomer", back_populates="payment_intents")
    refunds = relationship("StripeRefund", back_populates="payment_intent")

    __table_args__ = (
        Index('idx_stripe_pi_tenant', 'tenant_id'),
        Index('idx_stripe_pi_customer', 'stripe_customer_id'),
        Index('idx_stripe_pi_status', 'tenant_id', 'status'),
        Index('idx_stripe_pi_invoice', 'tenant_id', 'invoice_id'),
    )


# ============================================================================
# CHECKOUT SESSIONS
# ============================================================================

class StripeCheckoutSession(Base):
    """Session de checkout Stripe."""
    __tablename__ = "stripe_checkout_sessions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_session_id = Column(String(100), nullable=False, unique=True)
    stripe_customer_id = Column(String(100))

    # Configuration
    mode = Column(String(20), nullable=False)  # payment, subscription, setup
    payment_status = Column(String(20))  # paid, unpaid, no_payment_required
    status = Column(String(20))  # open, complete, expired

    # URLs
    success_url = Column(String(500))
    cancel_url = Column(String(500))
    url = Column(String(500))

    # Montants
    amount_total = Column(Numeric(12, 2))
    amount_subtotal = Column(Numeric(12, 2))
    currency = Column(String(3), default="EUR")

    # Références (UUID)
    invoice_id = Column(UniversalUUID())
    order_id = Column(UniversalUUID())
    subscription_id = Column(UniversalUUID())

    # Résultat
    payment_intent_id = Column(String(100))
    subscription_stripe_id = Column(String(100))

    # Métadonnées
    stripe_metadata = Column(JSON)
    line_items = Column(JSON)
    customer_email = Column(String(255))

    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_stripe_checkout_tenant', 'tenant_id'),
        Index('idx_stripe_checkout_status', 'tenant_id', 'status'),
    )


# ============================================================================
# REFUNDS
# ============================================================================

class StripeRefund(Base):
    """Remboursement Stripe."""
    __tablename__ = "stripe_refunds"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_refund_id = Column(String(100), nullable=False, unique=True)
    payment_intent_id = Column(UniversalUUID(), ForeignKey("stripe_payment_intents.id"))
    stripe_charge_id = Column(String(100))

    # Montant
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")

    # Statut
    status = Column(Enum(RefundStatus), nullable=False, default=RefundStatus.PENDING)
    failure_reason = Column(String(100))

    # Raison
    reason = Column(String(100))  # duplicate, fraudulent, requested_by_customer
    description = Column(Text)

    # Métadonnées
    stripe_metadata = Column(JSON)
    receipt_number = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    payment_intent = relationship("StripePaymentIntent", back_populates="refunds")

    __table_args__ = (
        Index('idx_stripe_refunds_tenant', 'tenant_id'),
        Index('idx_stripe_refunds_pi', 'payment_intent_id'),
    )


# ============================================================================
# DISPUTES
# ============================================================================

class StripeDispute(Base):
    """Litige Stripe."""
    __tablename__ = "stripe_disputes"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_dispute_id = Column(String(100), nullable=False, unique=True)
    stripe_charge_id = Column(String(100))
    stripe_payment_intent_id = Column(String(100))

    # Montant
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")

    # Statut
    status = Column(Enum(DisputeStatus), nullable=False)
    reason = Column(String(100))  # fraudulent, duplicate, product_not_received, etc.

    # Preuves
    evidence = Column(JSON)
    evidence_due_by = Column(DateTime)
    is_charge_refundable = Column(Boolean, default=False)

    # Résultat
    network_reason_code = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_stripe_disputes_tenant', 'tenant_id'),
        Index('idx_stripe_disputes_status', 'tenant_id', 'status'),
    )


# ============================================================================
# WEBHOOKS
# ============================================================================

class StripeWebhook(Base):
    """Événement webhook Stripe."""
    __tablename__ = "stripe_webhooks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_event_id = Column(String(100), nullable=False, unique=True)
    event_type = Column(String(100), nullable=False)

    # Données
    payload = Column(JSON, nullable=False)
    api_version = Column(String(20))

    # Objet concerné
    object_type = Column(String(50))  # payment_intent, customer, invoice
    object_id = Column(String(100))

    # Traitement
    status = Column(Enum(WebhookStatus), nullable=False, default=WebhookStatus.PENDING)
    processed_at = Column(DateTime)
    processing_error = Column(Text)
    retry_count = Column(Integer, default=0)

    # Signature
    signature = Column(String(255))
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_stripe_webhooks_tenant', 'tenant_id'),
        Index('idx_stripe_webhooks_type', 'tenant_id', 'event_type'),
        Index('idx_stripe_webhooks_status', 'status'),
        Index('idx_stripe_webhooks_object', 'object_type', 'object_id'),
    )


# ============================================================================
# STRIPE PRODUCTS (Prix et produits synchronisés)
# ============================================================================

class StripeProduct(Base):
    """Produit Stripe synchronisé."""
    __tablename__ = "stripe_products"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_product_id = Column(String(100), nullable=False, unique=True)

    # Lien AZALS (UUID)
    product_id = Column(UniversalUUID())  # Produit AZALS
    plan_id = Column(UniversalUUID())  # Plan abonnement AZALS

    # Données produit
    name = Column(String(255), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)
    images = Column(JSON)
    stripe_metadata = Column(JSON)

    # Type
    product_type = Column(String(20), default="service")  # service, good

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    prices = relationship("StripePrice", back_populates="product")

    __table_args__ = (
        Index('idx_stripe_products_tenant', 'tenant_id'),
        Index('idx_stripe_products_product', 'tenant_id', 'product_id'),
    )


class StripePrice(Base):
    """Prix Stripe synchronisé."""
    __tablename__ = "stripe_prices"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_price_id = Column(String(100), nullable=False, unique=True)
    stripe_product_id = Column(UniversalUUID(), ForeignKey("stripe_products.id"))

    # Tarification
    unit_amount = Column(Numeric(12, 2))  # En centimes
    currency = Column(String(3), nullable=False, default="EUR")
    billing_scheme = Column(String(20), default="per_unit")  # per_unit, tiered

    # Récurrence
    recurring_interval = Column(String(20))  # day, week, month, year
    recurring_interval_count = Column(Integer, default=1)
    recurring_usage_type = Column(String(20), default="licensed")  # licensed, metered

    # Tiers (pour tarification par paliers)
    tiers = Column(JSON)
    tiers_mode = Column(String(20))  # graduated, volume

    # Statut
    active = Column(Boolean, default=True)
    nickname = Column(String(100))
    stripe_metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    product = relationship("StripeProduct", back_populates="prices")

    __table_args__ = (
        Index('idx_stripe_prices_tenant', 'tenant_id'),
        Index('idx_stripe_prices_product', 'stripe_product_id'),
    )


# ============================================================================
# STRIPE CONNECT (pour marketplaces)
# ============================================================================

class StripeConnectAccount(Base):
    """Compte Stripe Connect."""
    __tablename__ = "stripe_connect_accounts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_account_id = Column(String(100), nullable=False, unique=True)

    # Lien AZALS (UUID)
    vendor_id = Column(UniversalUUID())  # Vendeur/Partenaire AZALS

    # Type de compte
    account_type = Column(String(20), default="standard")  # standard, express, custom
    country = Column(String(2))
    email = Column(String(255))
    business_type = Column(String(20))  # individual, company

    # Statut
    status = Column(Enum(StripeAccountStatus), default=StripeAccountStatus.PENDING)
    charges_enabled = Column(Boolean, default=False)
    payouts_enabled = Column(Boolean, default=False)
    details_submitted = Column(Boolean, default=False)

    # Capacités
    capabilities = Column(JSON)  # {card_payments: active, transfers: active}

    # Onboarding
    onboarding_url = Column(String(500))
    onboarding_expires_at = Column(DateTime)

    # Paramètres
    default_currency = Column(String(3))
    payout_schedule = Column(JSON)

    # Métadonnées
    stripe_metadata = Column(JSON)
    requirements = Column(JSON)  # Requirements pour activation complète

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_stripe_connect_tenant', 'tenant_id'),
        Index('idx_stripe_connect_vendor', 'tenant_id', 'vendor_id'),
        Index('idx_stripe_connect_status', 'tenant_id', 'status'),
    )


# ============================================================================
# PAYOUT (Virements Stripe)
# ============================================================================

class StripePayout(Base):
    """Virement Stripe."""
    __tablename__ = "stripe_payouts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    stripe_payout_id = Column(String(100), nullable=False, unique=True)
    stripe_account_id = Column(String(100))  # Pour Connect

    # Montant
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")

    # Statut
    status = Column(String(20), nullable=False)  # pending, in_transit, paid, failed, canceled
    failure_code = Column(String(50))
    failure_message = Column(Text)

    # Destination
    destination_type = Column(String(20))  # bank_account, card
    destination_id = Column(String(100))

    # Dates
    arrival_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Métadonnées
    description = Column(String(255))
    stripe_metadata = Column(JSON)
    statement_descriptor = Column(String(22))

    __table_args__ = (
        Index('idx_stripe_payouts_tenant', 'tenant_id'),
        Index('idx_stripe_payouts_status', 'tenant_id', 'status'),
        Index('idx_stripe_payouts_account', 'stripe_account_id'),
    )


# ============================================================================
# CONFIGURATION
# ============================================================================

class StripeConfig(Base):
    """Configuration Stripe par tenant."""
    __tablename__ = "stripe_config"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, unique=True)

    # Clés API (chiffrées en production)
    api_key_live = Column(String(255))  # sk_live_...
    api_key_test = Column(String(255))  # sk_test_...
    webhook_secret_live = Column(String(255))
    webhook_secret_test = Column(String(255))

    # Mode
    is_live_mode = Column(Boolean, default=False)

    # Configuration par défaut
    default_currency = Column(String(3), default="EUR")
    default_payment_methods = Column(JSON, default=["card"])
    statement_descriptor = Column(String(22))
    statement_descriptor_suffix = Column(String(10))

    # Stripe Connect
    connect_enabled = Column(Boolean, default=False)
    platform_fee_percent = Column(Numeric(5, 2), default=0)

    # Paramètres
    auto_capture = Column(Boolean, default=True)
    send_receipts = Column(Boolean, default=True)
    allow_promotion_codes = Column(Boolean, default=False)

    # Taxes
    automatic_tax = Column(Boolean, default=False)
    tax_behavior = Column(String(20), default="exclusive")  # exclusive, inclusive

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_stripe_config_tenant', 'tenant_id', unique=True),
    )
