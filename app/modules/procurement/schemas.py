"""
AZALS MODULE M4 - Schémas Achats
================================

Schémas Pydantic pour la gestion des achats.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    PurchaseInvoiceStatus,
    PurchaseOrderStatus,
    QuotationStatus,
    ReceivingStatus,
    RequisitionStatus,
    SupplierStatus,
    SupplierType,
)

# ============================================================================
# SCHÉMAS FOURNISSEURS
# ============================================================================

class SupplierBase(BaseModel):
    """Base pour les fournisseurs."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: str | None = None
    supplier_type: SupplierType = Field(default=SupplierType.OTHER, alias="type")
    tax_id: str | None = None
    vat_number: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "France"
    payment_terms: str = "NET30"
    currency: str = "EUR"
    category: str | None = None


class SupplierCreate(SupplierBase):
    """Création d'un fournisseur."""
    credit_limit: Decimal | None = None
    discount_rate: Decimal = Decimal("0")
    bank_name: str | None = None
    iban: str | None = None
    bic: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class SupplierUpdate(BaseModel):
    """Mise à jour d'un fournisseur."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: str | None = None
    legal_name: str | None = None
    supplier_type: SupplierType | None = Field(default=None, alias="type")
    status: SupplierStatus | None = None
    tax_id: str | None = None
    vat_number: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    payment_terms: str | None = None
    currency: str | None = None
    credit_limit: Decimal | None = None
    discount_rate: Decimal | None = None
    category: str | None = None
    bank_name: str | None = None
    iban: str | None = None
    bic: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class SupplierResponse(SupplierBase):
    """Réponse fournisseur."""
    id: UUID
    status: SupplierStatus = SupplierStatus.PROSPECT
    credit_limit: Decimal | None = None
    discount_rate: Decimal = Decimal("0")
    bank_name: str | None = None
    iban: str | None = None
    bic: str | None = None
    rating: Decimal | None = None
    last_evaluation_date: date | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class SupplierList(BaseModel):
    """Liste de fournisseurs."""
    items: list[SupplierResponse]
    total: int


# ============================================================================
# SCHÉMAS CONTACTS FOURNISSEUR
# ============================================================================

class SupplierContactCreate(BaseModel):
    """Création d'un contact fournisseur."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    job_title: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    is_primary: bool = False
    notes: str | None = None


class SupplierContactResponse(SupplierContactCreate):
    """Réponse contact fournisseur."""
    id: UUID
    supplier_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DEMANDES D'ACHAT
# ============================================================================

class RequisitionLineCreate(BaseModel):
    """Création d'une ligne de demande."""
    product_id: UUID | None = None
    product_code: str | None = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    estimated_price: Decimal | None = None
    preferred_supplier_id: UUID | None = None
    required_date: date | None = None
    notes: str | None = None


class RequisitionLineResponse(RequisitionLineCreate):
    """Réponse ligne de demande."""
    id: UUID
    requisition_id: UUID
    line_number: int
    total: Decimal | None = None
    ordered_quantity: Decimal = Decimal("0")
    purchase_order_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequisitionCreate(BaseModel):
    """Création d'une demande d'achat."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    justification: str | None = None
    priority: str = "NORMAL"
    requested_date: date
    required_date: date | None = None
    budget_code: str | None = None
    department_id: UUID | None = None
    notes: str | None = None
    lines: list[RequisitionLineCreate] = Field(default_factory=list)


class RequisitionResponse(BaseModel):
    """Réponse demande d'achat."""
    id: UUID
    number: str
    status: RequisitionStatus
    priority: str
    title: str
    description: str | None = None
    justification: str | None = None
    requester_id: UUID
    department_id: UUID | None = None
    requested_date: date
    required_date: date | None = None
    estimated_total: Decimal = Decimal("0")
    currency: str
    budget_code: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    notes: str | None = None
    lines: list[RequisitionLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DEVIS FOURNISSEURS
# ============================================================================

class QuotationLineCreate(BaseModel):
    """Création d'une ligne de devis."""
    product_id: UUID | None = None
    product_code: str | None = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("20")
    lead_time: int | None = None
    notes: str | None = None


class QuotationLineResponse(QuotationLineCreate):
    """Réponse ligne de devis."""
    id: UUID
    quotation_id: UUID
    line_number: int
    total: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotationCreate(BaseModel):
    """Création d'un devis fournisseur."""
    supplier_id: UUID
    requisition_id: UUID | None = None
    request_date: date
    expiry_date: date | None = None
    currency: str = "EUR"
    payment_terms: str | None = None
    delivery_terms: str | None = None
    delivery_date: date | None = None
    notes: str | None = None
    lines: list[QuotationLineCreate] = Field(default_factory=list)


class QuotationResponse(BaseModel):
    """Réponse devis fournisseur."""
    id: UUID
    number: str
    supplier_id: UUID
    requisition_id: UUID | None = None
    status: QuotationStatus
    request_date: date
    response_date: date | None = None
    expiry_date: date | None = None
    currency: str
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    payment_terms: str | None = None
    delivery_terms: str | None = None
    delivery_date: date | None = None
    reference: str | None = None
    notes: str | None = None
    lines: list[QuotationLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS COMMANDES D'ACHAT
# ============================================================================

class OrderLineCreate(BaseModel):
    """Création d'une ligne de commande."""
    product_id: UUID | None = None
    product_code: str | None = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("20")
    expected_date: date | None = None
    requisition_line_id: UUID | None = None
    notes: str | None = None


class OrderLineResponse(OrderLineCreate):
    """Réponse ligne de commande."""
    id: UUID
    order_id: UUID
    line_number: int
    total: Decimal
    received_quantity: Decimal = Decimal("0")
    invoiced_quantity: Decimal = Decimal("0")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderCreate(BaseModel):
    """Création d'une commande d'achat."""
    supplier_id: UUID
    requisition_id: UUID | None = None
    quotation_id: UUID | None = None
    order_date: date
    expected_date: date | None = None
    delivery_address: str | None = None
    delivery_contact: str | None = None
    currency: str = "EUR"
    payment_terms: str | None = None
    incoterms: str | None = None
    shipping_cost: Decimal = Decimal("0")
    notes: str | None = None
    internal_notes: str | None = None
    lines: list[OrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(BaseModel):
    """Réponse commande d'achat."""
    id: UUID
    number: str
    supplier_id: UUID
    requisition_id: UUID | None = None
    quotation_id: UUID | None = None
    status: PurchaseOrderStatus
    order_date: date
    expected_date: date | None = None
    confirmed_date: date | None = None
    delivery_address: str | None = None
    delivery_contact: str | None = None
    currency: str
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    shipping_cost: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    payment_terms: str | None = None
    incoterms: str | None = None
    received_amount: Decimal = Decimal("0")
    invoiced_amount: Decimal = Decimal("0")
    supplier_reference: str | None = None
    notes: str | None = None
    lines: list[OrderLineResponse] = Field(default_factory=list)
    sent_at: datetime | None = None
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderList(BaseModel):
    """Liste de commandes."""
    items: list[PurchaseOrderResponse]
    total: int


# ============================================================================
# SCHÉMAS RÉCEPTIONS
# ============================================================================

class ReceiptLineCreate(BaseModel):
    """Création d'une ligne de réception."""
    order_line_id: UUID
    product_id: UUID | None = None
    product_code: str | None = None
    description: str
    ordered_quantity: Decimal
    received_quantity: Decimal
    rejected_quantity: Decimal = Decimal("0")
    unit: str = "UNIT"
    rejection_reason: str | None = None
    lot_number: str | None = None
    expiry_date: date | None = None
    notes: str | None = None


class ReceiptLineResponse(ReceiptLineCreate):
    """Réponse ligne de réception."""
    id: UUID
    receipt_id: UUID
    line_number: int
    serial_numbers: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoodsReceiptCreate(BaseModel):
    """Création d'une réception."""
    order_id: UUID
    receipt_date: date
    delivery_note: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    warehouse_id: UUID | None = None
    location: str | None = None
    notes: str | None = None
    lines: list[ReceiptLineCreate] = Field(default_factory=list)


class GoodsReceiptResponse(BaseModel):
    """Réponse réception."""
    id: UUID
    number: str
    order_id: UUID
    supplier_id: UUID
    status: ReceivingStatus
    receipt_date: date
    delivery_note: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    warehouse_id: UUID | None = None
    location: str | None = None
    notes: str | None = None
    lines: list[ReceiptLineResponse] = Field(default_factory=list)
    received_by: UUID | None = None
    validated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS FACTURES D'ACHAT
# ============================================================================

class InvoiceLineCreate(BaseModel):
    """Création d'une ligne de facture."""
    order_line_id: UUID | None = None
    product_id: UUID | None = None
    product_code: str | None = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("20")
    account_id: UUID | None = None
    analytic_code: str | None = None
    notes: str | None = None


class InvoiceLineResponse(InvoiceLineCreate):
    """Réponse ligne de facture."""
    id: UUID
    invoice_id: UUID
    line_number: int
    tax_amount: Decimal = Decimal("0")
    total: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseInvoiceCreate(BaseModel):
    """Création d'une facture d'achat."""
    supplier_id: UUID
    order_id: UUID | None = None
    invoice_date: date
    due_date: date | None = None
    supplier_invoice_number: str | None = None
    supplier_invoice_date: date | None = None
    currency: str = "EUR"
    payment_terms: str | None = None
    payment_method: str | None = None
    notes: str | None = None
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class PurchaseInvoiceResponse(BaseModel):
    """Réponse facture d'achat."""
    id: UUID
    number: str
    supplier_id: UUID
    order_id: UUID | None = None
    status: PurchaseInvoiceStatus
    invoice_date: date
    due_date: date | None = None
    supplier_invoice_number: str | None = None
    supplier_invoice_date: date | None = None
    currency: str
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    paid_amount: Decimal = Decimal("0")
    remaining_amount: Decimal = Decimal("0")
    payment_terms: str | None = None
    payment_method: str | None = None
    notes: str | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    validated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseInvoiceList(BaseModel):
    """Liste de factures."""
    items: list[PurchaseInvoiceResponse]
    total: int


# ============================================================================
# SCHÉMAS PAIEMENTS
# ============================================================================

class PaymentAllocationCreate(BaseModel):
    """Affectation de paiement."""
    invoice_id: UUID
    amount: Decimal


class SupplierPaymentCreate(BaseModel):
    """Création d'un paiement fournisseur."""
    supplier_id: UUID
    payment_date: date
    amount: Decimal
    currency: str = "EUR"
    payment_method: str
    reference: str | None = None
    bank_account_id: UUID | None = None
    notes: str | None = None
    allocations: list[PaymentAllocationCreate] = Field(default_factory=list)


class SupplierPaymentResponse(BaseModel):
    """Réponse paiement fournisseur."""
    id: UUID
    number: str
    supplier_id: UUID
    payment_date: date
    amount: Decimal
    currency: str
    payment_method: str
    reference: str | None = None
    bank_account_id: UUID | None = None
    journal_entry_id: UUID | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS ÉVALUATION FOURNISSEUR
# ============================================================================

class SupplierEvaluationCreate(BaseModel):
    """Création d'une évaluation fournisseur."""
    supplier_id: UUID
    evaluation_date: date
    period_start: date
    period_end: date
    quality_score: Decimal | None = None
    price_score: Decimal | None = None
    delivery_score: Decimal | None = None
    service_score: Decimal | None = None
    reliability_score: Decimal | None = None
    comments: str | None = None
    recommendations: str | None = None


class SupplierEvaluationResponse(SupplierEvaluationCreate):
    """Réponse évaluation fournisseur."""
    id: UUID
    overall_score: Decimal | None = None
    total_orders: int = 0
    total_amount: Decimal = Decimal("0")
    on_time_delivery_rate: Decimal | None = None
    quality_rejection_rate: Decimal | None = None
    evaluated_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS DASHBOARD
# ============================================================================

class ProcurementDashboard(BaseModel):
    """Dashboard Achats."""
    # Fournisseurs
    total_suppliers: int = 0
    active_suppliers: int = 0
    pending_approvals: int = 0

    # Demandes
    pending_requisitions: int = 0
    requisitions_this_month: int = 0

    # Commandes
    draft_orders: int = 0
    pending_orders: int = 0
    orders_this_month: int = 0
    orders_amount_this_month: Decimal = Decimal("0")

    # Réceptions
    pending_receipts: int = 0

    # Factures
    pending_invoices: int = 0
    overdue_invoices: int = 0
    invoices_this_month: int = 0
    invoices_amount_this_month: Decimal = Decimal("0")

    # Paiements
    unpaid_amount: Decimal = Decimal("0")
    payments_due_this_week: Decimal = Decimal("0")

    # Top fournisseurs
    top_suppliers_by_amount: list[dict[str, Any]] = Field(default_factory=list)
    top_suppliers_by_orders: list[dict[str, Any]] = Field(default_factory=list)

    # Répartition par catégorie
    by_category: dict[str, Decimal] = Field(default_factory=dict)
