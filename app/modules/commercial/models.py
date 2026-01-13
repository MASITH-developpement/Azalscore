"""
AZALS MODULE M1 - Modèles Commercial
=====================================

Modèles SQLAlchemy pour le CRM et la gestion commerciale.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class CustomerType(str, enum.Enum):
    """Type de client/fournisseur."""
    PROSPECT = "PROSPECT"
    LEAD = "LEAD"
    CUSTOMER = "CUSTOMER"
    VIP = "VIP"
    PARTNER = "PARTNER"
    CHURNED = "CHURNED"
    SUPPLIER = "SUPPLIER"  # Fournisseur


class OpportunityStatus(str, enum.Enum):
    """Statut d'une opportunité."""
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"


class DocumentType(str, enum.Enum):
    """Type de document commercial."""
    QUOTE = "QUOTE"
    ORDER = "ORDER"
    INVOICE = "INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    PROFORMA = "PROFORMA"
    DELIVERY = "DELIVERY"


class DocumentStatus(str, enum.Enum):
    """Statut d'un document commercial."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DELIVERED = "DELIVERED"
    INVOICED = "INVOICED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    """Méthode de paiement."""
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"
    CREDIT_CARD = "CREDIT_CARD"
    CASH = "CASH"
    DIRECT_DEBIT = "DIRECT_DEBIT"
    PAYPAL = "PAYPAL"
    OTHER = "OTHER"


class PaymentTerms(str, enum.Enum):
    """Conditions de paiement."""
    IMMEDIATE = "IMMEDIATE"
    NET_15 = "NET_15"
    NET_30 = "NET_30"
    NET_45 = "NET_45"
    NET_60 = "NET_60"
    NET_90 = "NET_90"
    END_OF_MONTH = "END_OF_MONTH"
    CUSTOM = "CUSTOM"


class ActivityType(str, enum.Enum):
    """Type d'activité CRM."""
    CALL = "CALL"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    TASK = "TASK"
    NOTE = "NOTE"
    FOLLOW_UP = "FOLLOW_UP"


# ============================================================================
# MODÈLES CRM
# ============================================================================

class Customer(Base):
    """Client/Prospect."""
    __tablename__ = "customers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)  # Code client unique
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))  # Raison sociale
    type = Column(Enum(CustomerType), default=CustomerType.PROSPECT)

    # Contact principal
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))
    website = Column(String(255))

    # Adresse
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    state = Column(String(100))
    country_code = Column(String(3), default="FR")

    # Informations légales
    tax_id = Column(String(50))  # Numéro TVA
    registration_number = Column(String(50))  # SIRET/SIREN
    legal_form = Column(String(50))  # Forme juridique

    # Commercial
    assigned_to = Column(UniversalUUID())  # Commercial assigné
    industry = Column(String(100))  # Secteur d'activité
    size = Column(String(50))  # Taille (TPE, PME, ETI, GE)
    annual_revenue = Column(Numeric(15, 2))
    employee_count = Column(Integer)

    # Conditions commerciales
    payment_terms = Column(Enum(PaymentTerms), default=PaymentTerms.NET_30)
    payment_method = Column(Enum(PaymentMethod))
    credit_limit = Column(Numeric(15, 2))
    currency = Column(String(3), default="EUR")
    discount_rate = Column(Float, default=0.0)  # Remise globale %

    # Classification
    tags = Column(JSON, default=list)  # Tags libres
    segment = Column(String(50))  # Segment marketing
    source = Column(String(100))  # Source acquisition

    # Scoring
    lead_score = Column(Integer, default=0)  # Score prospect
    health_score = Column(Integer, default=100)  # Score santé client

    # Statistiques
    total_revenue = Column(Numeric(15, 2), default=0)
    order_count = Column(Integer, default=0)
    last_order_date = Column(Date)
    first_order_date = Column(Date)

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="customer")
    documents = relationship("CommercialDocument", back_populates="customer")
    activities = relationship("CustomerActivity", back_populates="customer")

    __table_args__ = (
        Index("ix_customers_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_customers_tenant_type", "tenant_id", "type"),
        Index("ix_customers_tenant_assigned", "tenant_id", "assigned_to"),
        Index("ix_customers_tenant_active", "tenant_id", "is_active"),
    )


class Contact(Base):
    """Contact d'un client."""
    __tablename__ = "customer_contacts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    customer_id = Column(UniversalUUID(), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)

    # Identité
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(50))  # M., Mme, Dr, etc.
    job_title = Column(String(100))  # Fonction
    department = Column(String(100))  # Service

    # Coordonnées
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))
    linkedin = Column(String(255))

    # Rôle
    is_primary = Column(Boolean, default=False)  # Contact principal
    is_billing = Column(Boolean, default=False)  # Contact facturation
    is_shipping = Column(Boolean, default=False)  # Contact livraison
    is_decision_maker = Column(Boolean, default=False)  # Décideur

    # Préférences
    preferred_language = Column(String(5), default="fr")
    preferred_contact_method = Column(String(20))  # email, phone, etc.
    do_not_call = Column(Boolean, default=False)
    do_not_email = Column(Boolean, default=False)

    # Notes
    notes = Column(Text)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    customer = relationship("Customer", back_populates="contacts")

    __table_args__ = (
        Index("ix_contacts_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_contacts_tenant_email", "tenant_id", "email"),
    )


class Opportunity(Base):
    """Opportunité commerciale (Pipeline)."""
    __tablename__ = "opportunities"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    customer_id = Column(UniversalUUID(), ForeignKey("customers.id"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)  # Numéro opportunité
    name = Column(String(255), nullable=False)  # Nom/Titre
    description = Column(Text)

    # Pipeline
    status = Column(Enum(OpportunityStatus), default=OpportunityStatus.NEW)
    stage = Column(String(50))  # Étape personnalisée
    probability = Column(Integer, default=10)  # Probabilité de succès %

    # Montants
    amount = Column(Numeric(15, 2), default=0)  # Montant estimé
    currency = Column(String(3), default="EUR")
    weighted_amount = Column(Numeric(15, 2))  # Montant pondéré

    # Dates
    expected_close_date = Column(Date)  # Date de conclusion prévue
    actual_close_date = Column(Date)  # Date de conclusion réelle

    # Attribution
    assigned_to = Column(UniversalUUID())  # Commercial responsable
    team = Column(String(100))  # Équipe commerciale

    # Source
    source = Column(String(100))  # Source (web, appel, salon, etc.)
    campaign = Column(String(100))  # Campagne marketing

    # Concurrence
    competitors = Column(JSON, default=list)  # Concurrents identifiés
    win_reason = Column(String(255))  # Raison du gain
    loss_reason = Column(String(255))  # Raison de la perte

    # Produits
    products = Column(JSON, default=list)  # Produits/services concernés

    # Notes
    notes = Column(Text)
    next_steps = Column(Text)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    customer = relationship("Customer", back_populates="opportunities")
    documents = relationship("CommercialDocument", back_populates="opportunity")
    activities = relationship("CustomerActivity", back_populates="opportunity")

    __table_args__ = (
        Index("ix_opportunities_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_opportunities_tenant_status", "tenant_id", "status"),
        Index("ix_opportunities_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_opportunities_tenant_assigned", "tenant_id", "assigned_to"),
        Index("ix_opportunities_tenant_close", "tenant_id", "expected_close_date"),
    )


# ============================================================================
# MODÈLES DOCUMENTS COMMERCIAUX
# ============================================================================

class CommercialDocument(Base):
    """Document commercial (Devis, Commande, Facture, etc.)."""
    __tablename__ = "commercial_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    customer_id = Column(UniversalUUID(), ForeignKey("customers.id"), nullable=False)
    opportunity_id = Column(UniversalUUID(), ForeignKey("opportunities.id"))

    # Identification
    type = Column(Enum(DocumentType), nullable=False)
    number = Column(String(50), nullable=False)  # Numéro du document
    reference = Column(String(100))  # Référence client
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)

    # Dates
    date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date)  # Date d'échéance
    validity_date = Column(Date)  # Date de validité (devis)
    delivery_date = Column(Date)  # Date de livraison prévue

    # Adresses
    billing_address = Column(JSON)  # Adresse de facturation
    shipping_address = Column(JSON)  # Adresse de livraison

    # Montants
    subtotal = Column(Numeric(15, 2), default=0)  # Total HT
    discount_amount = Column(Numeric(15, 2), default=0)  # Remise
    discount_percent = Column(Float, default=0)
    tax_amount = Column(Numeric(15, 2), default=0)  # TVA
    total = Column(Numeric(15, 2), default=0)  # Total TTC
    currency = Column(String(3), default="EUR")

    # Paiement
    payment_terms = Column(Enum(PaymentTerms))
    payment_method = Column(Enum(PaymentMethod))
    paid_amount = Column(Numeric(15, 2), default=0)  # Montant payé
    remaining_amount = Column(Numeric(15, 2))  # Reste à payer

    # Livraison
    shipping_method = Column(String(100))
    shipping_cost = Column(Numeric(10, 2), default=0)
    tracking_number = Column(String(100))

    # Notes
    notes = Column(Text)  # Notes visibles client
    internal_notes = Column(Text)  # Notes internes
    terms = Column(Text)  # Conditions générales

    # Lien avec autres documents
    parent_id = Column(UniversalUUID())  # Document parent (devis → commande)
    invoice_id = Column(UniversalUUID())  # Facture liée

    # PDF
    pdf_url = Column(String(500))

    # Attribution
    assigned_to = Column(UniversalUUID())
    validated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    customer = relationship("Customer", back_populates="documents")
    opportunity = relationship("Opportunity", back_populates="documents")
    lines = relationship("DocumentLine", back_populates="document", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="document")

    __table_args__ = (
        Index("ix_documents_tenant_number", "tenant_id", "type", "number", unique=True),
        Index("ix_documents_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_documents_tenant_type", "tenant_id", "type"),
        Index("ix_documents_tenant_status", "tenant_id", "status"),
        Index("ix_documents_tenant_date", "tenant_id", "date"),
    )


class DocumentLine(Base):
    """Ligne de document commercial."""
    __tablename__ = "document_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("commercial_documents.id", ondelete="CASCADE"), nullable=False)

    # Position
    line_number = Column(Integer, nullable=False)

    # Produit/Service
    product_id = Column(UniversalUUID())  # Référence produit
    product_code = Column(String(50))
    description = Column(Text, nullable=False)

    # Quantités
    quantity = Column(Numeric(10, 3), default=1)
    unit = Column(String(20))  # Unité (pce, kg, h, etc.)

    # Prix
    unit_price = Column(Numeric(15, 4), default=0)  # Prix unitaire HT
    discount_percent = Column(Float, default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    subtotal = Column(Numeric(15, 2), default=0)  # Total ligne HT

    # TVA
    tax_rate = Column(Float, default=20.0)  # Taux TVA %
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)  # Total ligne TTC

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    document = relationship("CommercialDocument", back_populates="lines")

    __table_args__ = (
        Index("ix_doc_lines_tenant_document", "tenant_id", "document_id"),
    )


# ============================================================================
# MODÈLES PAIEMENTS
# ============================================================================

class Payment(Base):
    """Paiement reçu."""
    __tablename__ = "payments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("commercial_documents.id"), nullable=False)

    # Identification
    reference = Column(String(100))  # Référence paiement
    method = Column(Enum(PaymentMethod), nullable=False)

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Dates
    date = Column(Date, nullable=False, default=date.today)
    received_date = Column(Date)

    # Banque
    bank_account = Column(String(100))
    transaction_id = Column(String(100))

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    document = relationship("CommercialDocument", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_tenant_document", "tenant_id", "document_id"),
        Index("ix_payments_tenant_date", "tenant_id", "date"),
    )


# ============================================================================
# MODÈLES ACTIVITÉS CRM
# ============================================================================

class CustomerActivity(Base):
    """Activité CRM (appels, emails, réunions, etc.)."""
    __tablename__ = "customer_activities"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    customer_id = Column(UniversalUUID(), ForeignKey("customers.id"), nullable=False)
    opportunity_id = Column(UniversalUUID(), ForeignKey("opportunities.id"))
    contact_id = Column(UniversalUUID(), ForeignKey("customer_contacts.id"))

    # Type et sujet
    type = Column(Enum(ActivityType), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text)

    # Dates
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime)  # Pour les tâches
    completed_at = Column(DateTime)

    # Durée
    duration_minutes = Column(Integer)

    # Statut
    is_completed = Column(Boolean, default=False)

    # Attribution
    assigned_to = Column(UniversalUUID())

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    customer = relationship("Customer", back_populates="activities")
    opportunity = relationship("Opportunity", back_populates="activities")

    __table_args__ = (
        Index("ix_activities_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_activities_tenant_opportunity", "tenant_id", "opportunity_id"),
        Index("ix_activities_tenant_date", "tenant_id", "date"),
        Index("ix_activities_tenant_assigned", "tenant_id", "assigned_to"),
    )


# ============================================================================
# MODÈLE PIPELINE (Configuration)
# ============================================================================

class PipelineStage(Base):
    """Étape du pipeline de vente."""
    __tablename__ = "pipeline_stages"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(100), nullable=False)
    code = Column(String(50))
    description = Column(Text)

    # Position et probabilité
    order = Column(Integer, nullable=False)
    probability = Column(Integer, default=50)  # Probabilité de succès %

    # Couleur pour UI
    color = Column(String(20), default="#3B82F6")

    # Type
    is_won = Column(Boolean, default=False)  # Étape "gagné"
    is_lost = Column(Boolean, default=False)  # Étape "perdu"

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_pipeline_tenant_order", "tenant_id", "order"),
    )


# ============================================================================
# MODÈLE PRODUITS/SERVICES (Catalogue)
# ============================================================================

class CatalogProduct(Base):
    """Produit ou service au catalogue commercial (distinct de inventory.Product)."""
    __tablename__ = "catalog_products"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Type
    is_service = Column(Boolean, default=False)  # Service ou produit

    # Prix
    unit_price = Column(Numeric(15, 4), default=0)  # Prix unitaire HT
    currency = Column(String(3), default="EUR")
    unit = Column(String(20), default="pce")  # Unité

    # TVA
    tax_rate = Column(Float, default=20.0)

    # Stock (pour produits)
    track_stock = Column(Boolean, default=False)
    stock_quantity = Column(Numeric(10, 3), default=0)
    min_stock = Column(Numeric(10, 3), default=0)

    # Images
    image_url = Column(String(500))
    gallery = Column(JSON, default=list)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_products_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_products_tenant_category", "tenant_id", "category"),
        Index("ix_products_tenant_active", "tenant_id", "is_active"),
    )
