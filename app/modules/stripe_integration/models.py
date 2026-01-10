"""
AZALS MODULE 15 - Stripe Integration Models
============================================
Modèles SQLAlchemy pour l'intégration Stripe.
MIGRATED: All PKs and FKs use UUID for PostgreSQL compatibility.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base
from app.core.types import UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)

    # Lien avec CRM (UUID reference)
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)
    customer_type: Mapped[Optional[str]] = mapped_column(String(50), default="company")  # company, individual

    # Données client
    email: Mapped[Optional[str]] = mapped_column(String(255))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Adresse
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(2))

    # Paramètres facturation
    default_payment_method_id: Mapped[Optional[str]] = mapped_column(String(100))
    invoice_prefix: Mapped[Optional[str]] = mapped_column(String(20))
    tax_exempt: Mapped[Optional[str]] = mapped_column(String(20), default="none")  # none, exempt, reverse
    tax_ids: Mapped[Optional[dict]] = mapped_column(JSON)  # [{type, value}]

    # Métadonnées Stripe
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    delinquent: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Synchronisation
    is_synced: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sync_error: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_payment_method_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    stripe_customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("stripe_customers.id"))

    # Type
    method_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=False)  # card, sepa_debit, bank_transfer

    # Détails carte
    card_brand: Mapped[Optional[str]] = mapped_column(String(20))  # visa, mastercard, amex
    card_last4: Mapped[Optional[str]] = mapped_column(String(4))
    card_exp_month: Mapped[Optional[int]] = mapped_column(Integer)
    card_exp_year: Mapped[Optional[int]] = mapped_column(Integer)
    card_funding: Mapped[Optional[str]] = mapped_column(String(20))  # credit, debit, prepaid
    card_country: Mapped[Optional[str]] = mapped_column(String(2))

    # Détails SEPA
    sepa_bank_code: Mapped[Optional[str]] = mapped_column(String(20))
    sepa_last4: Mapped[Optional[str]] = mapped_column(String(4))
    sepa_country: Mapped[Optional[str]] = mapped_column(String(2))

    # Adresse facturation
    billing_name: Mapped[Optional[str]] = mapped_column(String(255))
    billing_email: Mapped[Optional[str]] = mapped_column(String(255))
    billing_address: Mapped[Optional[dict]] = mapped_column(JSON)

    # Statut
    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    stripe_customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("stripe_customers.id"))

    # Montants
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=False)
    amount_received: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=False, default="EUR")

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(PaymentIntentStatus), nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(100))

    # Méthode de paiement
    payment_method_id: Mapped[Optional[str]] = mapped_column(String(100))
    payment_method_types: Mapped[Optional[dict]] = mapped_column(JSON)  # ["card", "sepa_debit"]

    # Capture
    capture_method: Mapped[Optional[str]] = mapped_column(String(20), default="automatic")  # automatic, manual
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Client secret (pour frontend)
    client_secret: Mapped[Optional[str]] = mapped_column(String(255))

    # Références (UUID pour liens AZALS)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Lien facture AZALS
    order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Lien commande AZALS
    subscription_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Lien abonnement AZALS
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Métadonnées
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    receipt_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Frais
    application_fee_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    stripe_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Configuration
    mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=False)  # payment, subscription, setup
    payment_status: Mapped[Optional[str]] = mapped_column(String(20))  # paid, unpaid, no_payment_required
    status: Mapped[Optional[str]] = mapped_column(String(20))  # open, complete, expired

    # URLs
    success_url: Mapped[Optional[str]] = mapped_column(String(500))
    cancel_url: Mapped[Optional[str]] = mapped_column(String(500))
    url: Mapped[Optional[str]] = mapped_column(String(500))

    # Montants
    amount_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    amount_subtotal: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="EUR")

    # Références (UUID)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    subscription_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Résultat
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100))
    subscription_stripe_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Métadonnées
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    line_items: Mapped[Optional[dict]] = mapped_column(JSON)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255))

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_refund_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("stripe_payment_intents.id"))
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Montant
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=False, default="EUR")

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(RefundStatus), nullable=False, default=RefundStatus.PENDING)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(100))

    # Raison
    reason: Mapped[Optional[str]] = mapped_column(String(100))  # duplicate, fraudulent, requested_by_customer
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Métadonnées
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(50))

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_dispute_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Montant
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=False, default="EUR")

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(DisputeStatus), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(100))  # fraudulent, duplicate, product_not_received, etc.

    # Preuves
    evidence: Mapped[Optional[dict]] = mapped_column(JSON)
    evidence_due_by: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_charge_refundable: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Résultat
    network_reason_code: Mapped[Optional[str]] = mapped_column(String(50))

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_event_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)

    # Données
    payload: Mapped[dict] = mapped_column(JSON)
    api_version: Mapped[Optional[str]] = mapped_column(String(20))

    # Objet concerné
    object_type: Mapped[Optional[str]] = mapped_column(String(50))  # payment_intent, customer, invoice
    object_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Traitement
    status: Mapped[Optional[str]] = mapped_column(Enum(WebhookStatus), nullable=False, default=WebhookStatus.PENDING)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    processing_error: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Signature
    signature: Mapped[Optional[str]] = mapped_column(String(255))
    is_verified: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_product_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)

    # Lien AZALS (UUID)
    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Produit AZALS
    plan_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Plan abonnement AZALS

    # Données produit
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    images: Mapped[Optional[dict]] = mapped_column(JSON)
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # Type
    product_type: Mapped[Optional[str]] = mapped_column(String(20), default="service")  # service, good

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    prices = relationship("StripePrice", back_populates="product")

    __table_args__ = (
        Index('idx_stripe_products_tenant', 'tenant_id'),
        Index('idx_stripe_products_product', 'tenant_id', 'product_id'),
    )


class StripePrice(Base):
    """Prix Stripe synchronisé."""
    __tablename__ = "stripe_prices"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    stripe_product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("stripe_products.id"))

    # Tarification
    unit_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))  # En centimes
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=False, default="EUR")
    billing_scheme: Mapped[Optional[str]] = mapped_column(String(20), default="per_unit")  # per_unit, tiered

    # Récurrence
    recurring_interval: Mapped[Optional[str]] = mapped_column(String(20))  # day, week, month, year
    recurring_interval_count: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    recurring_usage_type: Mapped[Optional[str]] = mapped_column(String(20), default="licensed")  # licensed, metered

    # Tiers (pour tarification par paliers)
    tiers: Mapped[Optional[dict]] = mapped_column(JSON)
    tiers_mode: Mapped[Optional[str]] = mapped_column(String(20))  # graduated, volume

    # Statut
    active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)

    # Lien AZALS (UUID)
    vendor_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Vendeur/Partenaire AZALS

    # Type de compte
    account_type: Mapped[Optional[str]] = mapped_column(String(20), default="standard")  # standard, express, custom
    country: Mapped[Optional[str]] = mapped_column(String(2))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    business_type: Mapped[Optional[str]] = mapped_column(String(20))  # individual, company

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(StripeAccountStatus), default=StripeAccountStatus.PENDING)
    charges_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    payouts_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    details_submitted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Capacités
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON)  # {card_payments: active, transfers: active}

    # Onboarding
    onboarding_url: Mapped[Optional[str]] = mapped_column(String(500))
    onboarding_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Paramètres
    default_currency: Mapped[Optional[str]] = mapped_column(String(3))
    payout_schedule: Mapped[Optional[dict]] = mapped_column(JSON)

    # Métadonnées
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    requirements: Mapped[Optional[dict]] = mapped_column(JSON)  # Requirements pour activation complète

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    stripe_payout_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=False, unique=True)
    stripe_account_id: Mapped[Optional[str]] = mapped_column(String(100))  # Pour Connect

    # Montant
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=False, default="EUR")

    # Statut
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=False)  # pending, in_transit, paid, failed, canceled
    failure_code: Mapped[Optional[str]] = mapped_column(String(50))
    failure_message: Mapped[Optional[str]] = mapped_column(Text)

    # Destination
    destination_type: Mapped[Optional[str]] = mapped_column(String(20))  # bank_account, card
    destination_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Dates
    arrival_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Métadonnées
    description: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    statement_descriptor: Mapped[Optional[str]] = mapped_column(String(22))

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, unique=True)

    # Clés API (chiffrées en production)
    api_key_live: Mapped[Optional[str]] = mapped_column(String(255))  # sk_live_...
    api_key_test: Mapped[Optional[str]] = mapped_column(String(255))  # sk_test_...
    webhook_secret_live: Mapped[Optional[str]] = mapped_column(String(255))
    webhook_secret_test: Mapped[Optional[str]] = mapped_column(String(255))

    # Mode
    is_live_mode: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Configuration par défaut
    default_currency: Mapped[Optional[str]] = mapped_column(String(3), default="EUR")
    default_payment_methods: Mapped[Optional[dict]] = mapped_column(JSON, default=["card"])
    statement_descriptor: Mapped[Optional[str]] = mapped_column(String(22))
    statement_descriptor_suffix: Mapped[Optional[str]] = mapped_column(String(10))

    # Stripe Connect
    connect_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    platform_fee_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), default=0)

    # Paramètres
    auto_capture: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    send_receipts: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    allow_promotion_codes: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Taxes
    automatic_tax: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    tax_behavior: Mapped[Optional[str]] = mapped_column(String(20), default="exclusive")  # exclusive, inclusive

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_stripe_config_tenant', 'tenant_id', unique=True),
    )
