"""
AZALS MODULE M4 - Modèles Purchases
====================================

Modèles SQLAlchemy pour la gestion des achats.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class SupplierStatus(str, enum.Enum):
    """Statuts fournisseur."""
    PROSPECT = "PROSPECT"      # Prospect (pas encore fournisseur)
    PENDING = "PENDING"        # En attente validation
    APPROVED = "APPROVED"      # Approuvé et actif
    BLOCKED = "BLOCKED"        # Bloqué (litiges, paiements)
    INACTIVE = "INACTIVE"      # Inactif (archivé)


class OrderStatus(str, enum.Enum):
    """Statuts commande achat."""
    DRAFT = "DRAFT"          # Brouillon (éditable)
    SENT = "SENT"            # Envoyée au fournisseur
    CONFIRMED = "CONFIRMED"  # Confirmée par fournisseur
    PARTIAL = "PARTIAL"      # Partiellement reçue
    RECEIVED = "RECEIVED"    # Entièrement reçue
    INVOICED = "INVOICED"    # Facturée (liée à facture)
    CANCELLED = "CANCELLED"  # Annulée


class InvoiceStatus(str, enum.Enum):
    """Statuts facture fournisseur."""
    DRAFT = "DRAFT"        # Brouillon (saisie en cours)
    VALIDATED = "VALIDATED"  # Validée (comptabilisée)
    PAID = "PAID"          # Payée
    CANCELLED = "CANCELLED"  # Annulée


class SupplierType(str, enum.Enum):
    """Type de fournisseur."""
    GOODS = "GOODS"
    SERVICES = "SERVICES"
    BOTH = "BOTH"
    RAW_MATERIALS = "RAW_MATERIALS"
    EQUIPMENT = "EQUIPMENT"


# ============================================================================
# MODÈLES
# ============================================================================

class PurchaseSupplier(Base):
    """Fournisseur."""
    __tablename__ = "purchases_suppliers"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False, index=True)  # Code fournisseur unique
    name = Column(String(255), nullable=False, index=True)  # Raison sociale
    supplier_type = Column(Enum(SupplierType, name='purchases_suppliertype'), default=SupplierType.BOTH)

    # Contact principal
    contact_name = Column(String(255))  # Nom contact principal
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))
    website = Column(String(255))

    # Adresse
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    state = Column(String(100))
    country = Column(String(100), default="France")

    # Informations légales
    tax_id = Column(String(50))  # SIRET/VAT
    registration_number = Column(String(50))
    legal_form = Column(String(50))

    # Conditions commerciales
    payment_terms = Column(String(100))  # Ex: "30 jours fin de mois"
    currency = Column(String(3), default="EUR")
    credit_limit = Column(Numeric(15, 2))

    # Statut
    status = Column(Enum(SupplierStatus, name='purchases_supplierstatus'), default=SupplierStatus.PENDING, nullable=False, index=True)

    # Classification
    tags = Column(Text)  # Tags JSON string
    category = Column(String(100))  # Catégorie métier

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    orders = relationship("LegacyPurchaseOrder", back_populates="supplier", lazy="dynamic")
    invoices = relationship("LegacyPurchaseInvoice", back_populates="supplier", lazy="dynamic")

    # Index
    __table_args__ = (
        Index('idx_purchases_suppliers_tenant_id', 'tenant_id'),
        Index('idx_purchases_suppliers_code', 'tenant_id', 'code', unique=True),
        Index('idx_purchases_suppliers_status', 'status'),
    )


class LegacyPurchaseOrder(Base):
    """Commande d'achat fournisseur."""
    __tablename__ = "purchases_orders"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    number = Column(String(50), nullable=False, index=True)  # CA-2024-001
    supplier_id = Column(UniversalUUID(), ForeignKey("purchases_suppliers.id"), nullable=False, index=True)

    # Dates
    date = Column(DateTime, nullable=False)  # Date commande
    expected_date = Column(DateTime)  # Date livraison prévue
    received_date = Column(DateTime)  # Date réception effective

    # Statut
    status = Column(Enum(OrderStatus, name='purchases_orderstatus'), default=OrderStatus.DRAFT, nullable=False, index=True)

    # Référence externe
    reference = Column(String(100))  # Référence fournisseur (si fournie)

    # Livraison
    delivery_address = Column(Text)
    delivery_contact = Column(String(255))
    delivery_phone = Column(String(50))

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Totaux (calculés depuis lignes)
    total_ht = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_tax = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_ttc = Column(Numeric(15, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="EUR")

    # Validation
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID(), ForeignKey("users.id"))

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    supplier = relationship("PurchaseSupplier", back_populates="orders")
    lines = relationship("LegacyPurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")
    invoices = relationship("LegacyPurchaseInvoice", back_populates="order")

    # Index
    __table_args__ = (
        Index('idx_purchases_orders_tenant_id', 'tenant_id'),
        Index('idx_purchases_orders_number', 'tenant_id', 'number', unique=True),
        Index('idx_purchases_orders_supplier', 'supplier_id'),
        Index('idx_purchases_orders_status', 'status'),
        Index('idx_purchases_orders_date', 'date'),
    )


class LegacyPurchaseOrderLine(Base):
    """Ligne de commande achat."""
    __tablename__ = "purchases_order_lines"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Relation commande
    order_id = Column(UniversalUUID(), ForeignKey("purchases_orders.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)  # Numéro de ligne (1, 2, 3...)

    # Produit/Service
    product_code = Column(String(50))  # Code article (optionnel)
    description = Column(Text, nullable=False)  # Description article
    quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("1.000"))
    unit = Column(String(20), default="unité")  # unité, kg, m, etc.

    # Prix
    unit_price = Column(Numeric(15, 2), nullable=False)  # Prix unitaire HT
    discount_percent = Column(Numeric(5, 2), default=Decimal("0.00"))  # Remise %
    tax_rate = Column(Numeric(5, 2), default=Decimal("20.00"))  # TVA %

    # Totaux calculés
    discount_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"))  # HT après remise
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    total = Column(Numeric(15, 2), default=Decimal("0.00"))  # TTC

    # Réception
    received_quantity = Column(Numeric(15, 3), default=Decimal("0.000"))

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relation
    order = relationship("LegacyPurchaseOrder", back_populates="lines")

    # Index
    __table_args__ = (
        Index('idx_purchases_order_lines_tenant_id', 'tenant_id'),
        Index('idx_purchases_order_lines_order', 'order_id'),
    )


class LegacyPurchaseInvoice(Base):
    """Facture fournisseur."""
    __tablename__ = "purchases_invoices"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    number = Column(String(50), nullable=False, index=True)  # Numéro facture fournisseur
    supplier_id = Column(UniversalUUID(), ForeignKey("purchases_suppliers.id"), nullable=False, index=True)
    order_id = Column(UniversalUUID(), ForeignKey("purchases_orders.id"), index=True)  # Optionnel

    # Dates
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    payment_date = Column(DateTime)  # Date paiement effectif

    # Statut
    status = Column(Enum(InvoiceStatus, name='purchases_invoicestatus'), default=InvoiceStatus.DRAFT, nullable=False, index=True)

    # Référence
    reference = Column(String(100))  # Référence interne

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Totaux (calculés depuis lignes)
    total_ht = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_tax = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_ttc = Column(Numeric(15, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="EUR")

    # Validation
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID(), ForeignKey("users.id"))

    # Paiement
    paid_at = Column(DateTime)
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    payment_method = Column(String(50))  # Virement, chèque, etc.

    # Métadonnées
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    supplier = relationship("PurchaseSupplier", back_populates="invoices")
    order = relationship("LegacyPurchaseOrder", back_populates="invoices")
    lines = relationship("LegacyPurchaseInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

    # Index
    __table_args__ = (
        Index('idx_purchases_invoices_tenant_id', 'tenant_id'),
        Index('idx_purchases_invoices_number', 'tenant_id', 'number', unique=True),
        Index('idx_purchases_invoices_supplier', 'supplier_id'),
        Index('idx_purchases_invoices_order', 'order_id'),
        Index('idx_purchases_invoices_status', 'status'),
        Index('idx_purchases_invoices_date', 'invoice_date'),
    )


class LegacyPurchaseInvoiceLine(Base):
    """Ligne de facture fournisseur."""
    __tablename__ = "purchases_invoice_lines"

    # Clé primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Relation facture
    invoice_id = Column(UniversalUUID(), ForeignKey("purchases_invoices.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)

    # Produit/Service
    product_code = Column(String(50))
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False, default=Decimal("1.000"))
    unit = Column(String(20), default="unité")

    # Prix
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=Decimal("0.00"))
    tax_rate = Column(Numeric(5, 2), default=Decimal("20.00"))

    # Totaux calculés
    discount_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    total = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relation
    invoice = relationship("LegacyPurchaseInvoice", back_populates="lines")

    # Index
    __table_args__ = (
        Index('idx_purchases_invoice_lines_tenant_id', 'tenant_id'),
        Index('idx_purchases_invoice_lines_invoice', 'invoice_id'),
    )
