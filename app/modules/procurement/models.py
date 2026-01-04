"""
AZALS MODULE M4 - Modèles Achats
================================

Modèles SQLAlchemy pour la gestion des achats.
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, DateTime, Text, Boolean, ForeignKey,
    Integer, Numeric, Date, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class SupplierStatus(str, enum.Enum):
    """Statuts fournisseur."""
    PROSPECT = "PROSPECT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    INACTIVE = "INACTIVE"


class SupplierType(str, enum.Enum):
    """Types de fournisseur."""
    MANUFACTURER = "MANUFACTURER"
    DISTRIBUTOR = "DISTRIBUTOR"
    SERVICE = "SERVICE"
    FREELANCE = "FREELANCE"
    OTHER = "OTHER"


class RequisitionStatus(str, enum.Enum):
    """Statuts demande d'achat."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ORDERED = "ORDERED"
    CANCELLED = "CANCELLED"


class PurchaseOrderStatus(str, enum.Enum):
    """Statuts commande d'achat."""
    DRAFT = "DRAFT"
    SENT = "SENT"
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"
    RECEIVED = "RECEIVED"
    INVOICED = "INVOICED"
    CANCELLED = "CANCELLED"


class ReceivingStatus(str, enum.Enum):
    """Statuts réception."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    CANCELLED = "CANCELLED"


class PurchaseInvoiceStatus(str, enum.Enum):
    """Statuts facture d'achat."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"


class QuotationStatus(str, enum.Enum):
    """Statuts devis fournisseur."""
    REQUESTED = "REQUESTED"
    RECEIVED = "RECEIVED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


# ============================================================================
# FOURNISSEURS
# ============================================================================

class Supplier(Base):
    """Fournisseur."""
    __tablename__ = "procurement_suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    type = Column(SQLEnum(SupplierType), default=SupplierType.OTHER)
    status = Column(SQLEnum(SupplierStatus), default=SupplierStatus.PROSPECT)

    # Identification légale
    tax_id = Column(String(50), nullable=True)  # SIRET/SIREN
    vat_number = Column(String(50), nullable=True)
    registration_number = Column(String(100), nullable=True)

    # Contact principal
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    fax = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)

    # Adresse
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="France")

    # Conditions commerciales
    payment_terms = Column(String(50), default="NET30")
    currency = Column(String(3), default="EUR")
    credit_limit = Column(Numeric(15, 2), nullable=True)
    discount_rate = Column(Numeric(5, 2), default=0)

    # Banque
    bank_name = Column(String(255), nullable=True)
    iban = Column(String(50), nullable=True)
    bic = Column(String(20), nullable=True)

    # Catégorie
    category = Column(String(100), nullable=True)
    tags = Column(JSONB, default=list)

    # Évaluation
    rating = Column(Numeric(3, 2), nullable=True)  # 0-5
    last_evaluation_date = Column(Date, nullable=True)

    # Comptabilité
    account_id = Column(UUID(as_uuid=True), nullable=True)  # Lien compte fournisseur

    # Métadonnées
    notes = Column(Text, nullable=True)
    custom_fields = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_supplier_code'),
        Index('idx_suppliers_tenant', 'tenant_id'),
        Index('idx_suppliers_status', 'tenant_id', 'status'),
        Index('idx_suppliers_category', 'tenant_id', 'category'),
    )


class SupplierContact(Base):
    """Contact fournisseur."""
    __tablename__ = "procurement_supplier_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    __table_args__ = (
        Index('idx_supplier_contacts_tenant', 'tenant_id'),
        Index('idx_supplier_contacts_supplier', 'tenant_id', 'supplier_id'),
    )


# ============================================================================
# DEMANDES D'ACHAT
# ============================================================================

class PurchaseRequisition(Base):
    """Demande d'achat."""
    __tablename__ = "procurement_requisitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    status = Column(SQLEnum(RequisitionStatus), default=RequisitionStatus.DRAFT)
    priority = Column(String(20), default="NORMAL")  # LOW, NORMAL, HIGH, URGENT

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    justification = Column(Text, nullable=True)

    requester_id = Column(UUID(as_uuid=True), nullable=False)
    department_id = Column(UUID(as_uuid=True), nullable=True)

    requested_date = Column(Date, nullable=False)
    required_date = Column(Date, nullable=True)

    estimated_total = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="EUR")
    budget_code = Column(String(50), nullable=True)

    # Approbation
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)
    attachments = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_requisition_number'),
        Index('idx_requisitions_tenant', 'tenant_id'),
        Index('idx_requisitions_status', 'tenant_id', 'status'),
        Index('idx_requisitions_requester', 'tenant_id', 'requester_id'),
    )


class PurchaseRequisitionLine(Base):
    """Ligne de demande d'achat."""
    __tablename__ = "procurement_requisition_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requisitions.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    product_code = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20), default="UNIT")
    estimated_price = Column(Numeric(15, 2), nullable=True)
    total = Column(Numeric(15, 2), nullable=True)

    preferred_supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=True)
    required_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # Lien vers commande
    ordered_quantity = Column(Numeric(15, 4), default=0)
    purchase_order_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    requisition = relationship("PurchaseRequisition", foreign_keys=[requisition_id])

    __table_args__ = (
        Index('idx_requisition_lines_requisition', 'requisition_id'),
        Index('idx_requisition_lines_tenant', 'tenant_id'),
    )


# ============================================================================
# DEVIS FOURNISSEURS
# ============================================================================

class SupplierQuotation(Base):
    """Devis fournisseur."""
    __tablename__ = "procurement_quotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=False)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requisitions.id"), nullable=True)

    status = Column(SQLEnum(QuotationStatus), default=QuotationStatus.REQUESTED)

    request_date = Column(Date, nullable=False)
    response_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    currency = Column(String(3), default="EUR")
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    payment_terms = Column(String(50), nullable=True)
    delivery_terms = Column(String(255), nullable=True)
    delivery_date = Column(Date, nullable=True)

    reference = Column(String(100), nullable=True)  # Référence fournisseur
    notes = Column(Text, nullable=True)
    attachments = Column(JSONB, default=list)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_quotation_number'),
        Index('idx_quotations_tenant', 'tenant_id'),
        Index('idx_quotations_supplier', 'tenant_id', 'supplier_id'),
        Index('idx_quotations_status', 'tenant_id', 'status'),
    )


class SupplierQuotationLine(Base):
    """Ligne de devis fournisseur."""
    __tablename__ = "procurement_quotation_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("procurement_quotations.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    product_code = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20), default="UNIT")
    unit_price = Column(Numeric(15, 4), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=20)
    total = Column(Numeric(15, 2), nullable=False)

    lead_time = Column(Integer, nullable=True)  # Délai en jours
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    quotation = relationship("SupplierQuotation", foreign_keys=[quotation_id])

    __table_args__ = (
        Index('idx_quotation_lines_quotation', 'quotation_id'),
        Index('idx_quotation_lines_tenant', 'tenant_id'),
    )


# ============================================================================
# COMMANDES D'ACHAT
# ============================================================================

class PurchaseOrder(Base):
    """Commande d'achat."""
    __tablename__ = "procurement_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=False)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requisitions.id"), nullable=True)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("procurement_quotations.id"), nullable=True)

    status = Column(SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)

    order_date = Column(Date, nullable=False)
    expected_date = Column(Date, nullable=True)
    confirmed_date = Column(Date, nullable=True)

    # Adresse de livraison
    delivery_address = Column(Text, nullable=True)
    delivery_contact = Column(String(255), nullable=True)

    # Montants
    currency = Column(String(3), default="EUR")
    subtotal = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    shipping_cost = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    # Conditions
    payment_terms = Column(String(50), nullable=True)
    incoterms = Column(String(20), nullable=True)

    # Réception
    received_amount = Column(Numeric(15, 2), default=0)
    invoiced_amount = Column(Numeric(15, 2), default=0)

    # Références
    supplier_reference = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    attachments = Column(JSONB, default=list)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_order_number'),
        Index('idx_orders_tenant', 'tenant_id'),
        Index('idx_orders_supplier', 'tenant_id', 'supplier_id'),
        Index('idx_orders_status', 'tenant_id', 'status'),
        Index('idx_orders_date', 'tenant_id', 'order_date'),
    )


class PurchaseOrderLine(Base):
    """Ligne de commande d'achat."""
    __tablename__ = "procurement_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("procurement_orders.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    product_code = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)

    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20), default="UNIT")
    unit_price = Column(Numeric(15, 4), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=20)
    total = Column(Numeric(15, 2), nullable=False)

    expected_date = Column(Date, nullable=True)
    received_quantity = Column(Numeric(15, 4), default=0)
    invoiced_quantity = Column(Numeric(15, 4), default=0)

    # Lien requisition
    requisition_line_id = Column(UUID(as_uuid=True), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("PurchaseOrder", foreign_keys=[order_id])

    __table_args__ = (
        Index('idx_order_lines_order', 'order_id'),
        Index('idx_order_lines_tenant', 'tenant_id'),
        Index('idx_order_lines_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# RÉCEPTIONS
# ============================================================================

class GoodsReceipt(Base):
    """Réception de marchandises."""
    __tablename__ = "procurement_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("procurement_orders.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=False)

    status = Column(SQLEnum(ReceivingStatus), default=ReceivingStatus.DRAFT)

    receipt_date = Column(Date, nullable=False)
    delivery_note = Column(String(100), nullable=True)
    carrier = Column(String(255), nullable=True)
    tracking_number = Column(String(100), nullable=True)

    warehouse_id = Column(UUID(as_uuid=True), nullable=True)
    location = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)
    attachments = Column(JSONB, default=list)

    received_by = Column(UUID(as_uuid=True), nullable=True)
    validated_by = Column(UUID(as_uuid=True), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("PurchaseOrder", foreign_keys=[order_id])
    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_receipt_number'),
        Index('idx_receipts_tenant', 'tenant_id'),
        Index('idx_receipts_order', 'tenant_id', 'order_id'),
        Index('idx_receipts_supplier', 'tenant_id', 'supplier_id'),
    )


class GoodsReceiptLine(Base):
    """Ligne de réception."""
    __tablename__ = "procurement_receipt_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("procurement_receipts.id"), nullable=False)
    order_line_id = Column(UUID(as_uuid=True), ForeignKey("procurement_order_lines.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    product_code = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)

    ordered_quantity = Column(Numeric(15, 4), nullable=False)
    received_quantity = Column(Numeric(15, 4), nullable=False)
    rejected_quantity = Column(Numeric(15, 4), default=0)
    unit = Column(String(20), default="UNIT")

    rejection_reason = Column(Text, nullable=True)
    lot_number = Column(String(100), nullable=True)
    serial_numbers = Column(JSONB, default=list)
    expiry_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    receipt = relationship("GoodsReceipt", foreign_keys=[receipt_id])

    __table_args__ = (
        Index('idx_receipt_lines_receipt', 'receipt_id'),
        Index('idx_receipt_lines_tenant', 'tenant_id'),
    )


# ============================================================================
# FACTURES D'ACHAT
# ============================================================================

class PurchaseInvoice(Base):
    """Facture d'achat."""
    __tablename__ = "procurement_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("procurement_orders.id"), nullable=True)

    status = Column(SQLEnum(PurchaseInvoiceStatus), default=PurchaseInvoiceStatus.DRAFT)

    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    supplier_invoice_number = Column(String(100), nullable=True)
    supplier_invoice_date = Column(Date, nullable=True)

    currency = Column(String(3), default="EUR")
    subtotal = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    paid_amount = Column(Numeric(15, 2), default=0)
    remaining_amount = Column(Numeric(15, 2), default=0)

    payment_terms = Column(String(50), nullable=True)
    payment_method = Column(String(50), nullable=True)

    # Comptabilité
    journal_entry_id = Column(UUID(as_uuid=True), nullable=True)
    posted_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)
    attachments = Column(JSONB, default=list)

    validated_by = Column(UUID(as_uuid=True), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_purchase_invoice_number'),
        Index('idx_purchase_invoices_tenant', 'tenant_id'),
        Index('idx_purchase_invoices_supplier', 'tenant_id', 'supplier_id'),
        Index('idx_purchase_invoices_status', 'tenant_id', 'status'),
        Index('idx_purchase_invoices_due', 'tenant_id', 'due_date'),
    )


class PurchaseInvoiceLine(Base):
    """Ligne de facture d'achat."""
    __tablename__ = "procurement_invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("procurement_invoices.id"), nullable=False)
    order_line_id = Column(UUID(as_uuid=True), ForeignKey("procurement_order_lines.id"), nullable=True)

    line_number = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    product_code = Column(String(50), nullable=True)
    description = Column(String(500), nullable=False)

    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20), default="UNIT")
    unit_price = Column(Numeric(15, 4), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=20)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), nullable=False)

    account_id = Column(UUID(as_uuid=True), nullable=True)  # Compte de charge
    analytic_code = Column(String(50), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("PurchaseInvoice", foreign_keys=[invoice_id])

    __table_args__ = (
        Index('idx_invoice_lines_invoice', 'invoice_id'),
        Index('idx_invoice_lines_tenant', 'tenant_id'),
    )


# ============================================================================
# PAIEMENTS FOURNISSEURS
# ============================================================================

class SupplierPayment(Base):
    """Paiement fournisseur."""
    __tablename__ = "procurement_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=False)

    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    payment_method = Column(String(50), nullable=False)
    reference = Column(String(100), nullable=True)

    bank_account_id = Column(UUID(as_uuid=True), nullable=True)

    # Comptabilité
    journal_entry_id = Column(UUID(as_uuid=True), nullable=True)

    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_payment_number'),
        Index('idx_payments_tenant', 'tenant_id'),
        Index('idx_payments_supplier', 'tenant_id', 'supplier_id'),
        Index('idx_payments_date', 'tenant_id', 'payment_date'),
    )


class PaymentAllocation(Base):
    """Affectation de paiement sur facture."""
    __tablename__ = "procurement_payment_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("procurement_payments.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("procurement_invoices.id"), nullable=False)

    amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    payment = relationship("SupplierPayment", foreign_keys=[payment_id])
    invoice = relationship("PurchaseInvoice", foreign_keys=[invoice_id])

    __table_args__ = (
        Index('idx_allocations_payment', 'payment_id'),
        Index('idx_allocations_invoice', 'invoice_id'),
        Index('idx_allocations_tenant', 'tenant_id'),
    )


# ============================================================================
# ÉVALUATION FOURNISSEURS
# ============================================================================

class SupplierEvaluation(Base):
    """Évaluation fournisseur."""
    __tablename__ = "procurement_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("procurement_suppliers.id"), nullable=False)

    evaluation_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Scores par critère (0-5)
    quality_score = Column(Numeric(3, 2), nullable=True)
    price_score = Column(Numeric(3, 2), nullable=True)
    delivery_score = Column(Numeric(3, 2), nullable=True)
    service_score = Column(Numeric(3, 2), nullable=True)
    reliability_score = Column(Numeric(3, 2), nullable=True)

    overall_score = Column(Numeric(3, 2), nullable=True)

    # Statistiques
    total_orders = Column(Integer, default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    on_time_delivery_rate = Column(Numeric(5, 2), nullable=True)
    quality_rejection_rate = Column(Numeric(5, 2), nullable=True)

    comments = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    evaluated_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    __table_args__ = (
        Index('idx_supplier_eval_tenant', 'tenant_id'),
        Index('idx_supplier_eval_supplier', 'tenant_id', 'supplier_id'),
        Index('idx_supplier_eval_date', 'tenant_id', 'evaluation_date'),
    )
