"""
AZALS MODULE M4 - Schémas Achats
================================

Schémas Pydantic pour la gestion des achats.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
import json

from .models import (
    SupplierStatus, SupplierType, RequisitionStatus,
    PurchaseOrderStatus, ReceivingStatus, PurchaseInvoiceStatus, QuotationStatus
)


# ============================================================================
# SCHÉMAS FOURNISSEURS
# ============================================================================

class SupplierBase(BaseModel):
    """Base pour les fournisseurs."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = None
    supplier_type: SupplierType = Field(default=SupplierType.OTHER, alias="type")
    tax_id: Optional[str] = None
    vat_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "France"
    payment_terms: str = "NET30"
    currency: str = "EUR"
    category: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Création d'un fournisseur."""
    credit_limit: Optional[Decimal] = None
    discount_rate: Decimal = Decimal("0")
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SupplierUpdate(BaseModel):
    """Mise à jour d'un fournisseur."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: Optional[str] = None
    legal_name: Optional[str] = None
    supplier_type: Optional[SupplierType] = Field(default=None, alias="type")
    status: Optional[SupplierStatus] = None
    tax_id: Optional[str] = None
    vat_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    payment_terms: Optional[str] = None
    currency: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    discount_rate: Optional[Decimal] = None
    category: Optional[str] = None
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Réponse fournisseur."""
    id: UUID
    status: SupplierStatus = SupplierStatus.PROSPECT
    credit_limit: Optional[Decimal] = None
    discount_rate: Decimal = Decimal("0")
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    rating: Optional[Decimal] = None
    last_evaluation_date: Optional[date] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class SupplierList(BaseModel):
    """Liste de fournisseurs."""
    items: List[SupplierResponse]
    total: int


# ============================================================================
# SCHÉMAS CONTACTS FOURNISSEUR
# ============================================================================

class SupplierContactCreate(BaseModel):
    """Création d'un contact fournisseur."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    job_title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None


class SupplierContactResponse(SupplierContactCreate):
    """Réponse contact fournisseur."""
    id: UUID
    supplier_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS DEMANDES D'ACHAT
# ============================================================================

class RequisitionLineCreate(BaseModel):
    """Création d'une ligne de demande."""
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    estimated_price: Optional[Decimal] = None
    preferred_supplier_id: Optional[UUID] = None
    required_date: Optional[date] = None
    notes: Optional[str] = None


class RequisitionLineResponse(RequisitionLineCreate):
    """Réponse ligne de demande."""
    id: UUID
    requisition_id: UUID
    line_number: int
    total: Optional[Decimal] = None
    ordered_quantity: Decimal = Decimal("0")
    purchase_order_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RequisitionCreate(BaseModel):
    """Création d'une demande d'achat."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    justification: Optional[str] = None
    priority: str = "NORMAL"
    requested_date: date
    required_date: Optional[date] = None
    budget_code: Optional[str] = None
    department_id: Optional[UUID] = None
    notes: Optional[str] = None
    lines: List[RequisitionLineCreate] = Field(default_factory=list)


class RequisitionResponse(BaseModel):
    """Réponse demande d'achat."""
    id: UUID
    number: str
    status: RequisitionStatus
    priority: str
    title: str
    description: Optional[str] = None
    justification: Optional[str] = None
    requester_id: UUID
    department_id: Optional[UUID] = None
    requested_date: date
    required_date: Optional[date] = None
    estimated_total: Decimal = Decimal("0")
    currency: str
    budget_code: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    lines: List[RequisitionLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS DEVIS FOURNISSEURS
# ============================================================================

class QuotationLineCreate(BaseModel):
    """Création d'une ligne de devis."""
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("20")
    lead_time: Optional[int] = None
    notes: Optional[str] = None


class QuotationLineResponse(QuotationLineCreate):
    """Réponse ligne de devis."""
    id: UUID
    quotation_id: UUID
    line_number: int
    total: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class QuotationCreate(BaseModel):
    """Création d'un devis fournisseur."""
    supplier_id: UUID
    requisition_id: Optional[UUID] = None
    request_date: date
    expiry_date: Optional[date] = None
    currency: str = "EUR"
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    delivery_date: Optional[date] = None
    notes: Optional[str] = None
    lines: List[QuotationLineCreate] = Field(default_factory=list)


class QuotationResponse(BaseModel):
    """Réponse devis fournisseur."""
    id: UUID
    number: str
    supplier_id: UUID
    requisition_id: Optional[UUID] = None
    status: QuotationStatus
    request_date: date
    response_date: Optional[date] = None
    expiry_date: Optional[date] = None
    currency: str
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    delivery_date: Optional[date] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    lines: List[QuotationLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS COMMANDES D'ACHAT
# ============================================================================

class OrderLineCreate(BaseModel):
    """Création d'une ligne de commande."""
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("20")
    expected_date: Optional[date] = None
    requisition_line_id: Optional[UUID] = None
    notes: Optional[str] = None


class OrderLineResponse(OrderLineCreate):
    """Réponse ligne de commande."""
    id: UUID
    order_id: UUID
    line_number: int
    total: Decimal
    received_quantity: Decimal = Decimal("0")
    invoiced_quantity: Decimal = Decimal("0")
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderCreate(BaseModel):
    """Création d'une commande d'achat."""
    supplier_id: UUID
    requisition_id: Optional[UUID] = None
    quotation_id: Optional[UUID] = None
    order_date: date
    expected_date: Optional[date] = None
    delivery_address: Optional[str] = None
    delivery_contact: Optional[str] = None
    currency: str = "EUR"
    payment_terms: Optional[str] = None
    incoterms: Optional[str] = None
    shipping_cost: Decimal = Decimal("0")
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    lines: List[OrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(BaseModel):
    """Réponse commande d'achat."""
    id: UUID
    number: str
    supplier_id: UUID
    requisition_id: Optional[UUID] = None
    quotation_id: Optional[UUID] = None
    status: PurchaseOrderStatus
    order_date: date
    expected_date: Optional[date] = None
    confirmed_date: Optional[date] = None
    delivery_address: Optional[str] = None
    delivery_contact: Optional[str] = None
    currency: str
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    shipping_cost: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    payment_terms: Optional[str] = None
    incoterms: Optional[str] = None
    received_amount: Decimal = Decimal("0")
    invoiced_amount: Decimal = Decimal("0")
    supplier_reference: Optional[str] = None
    notes: Optional[str] = None
    lines: List[OrderLineResponse] = Field(default_factory=list)
    sent_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderList(BaseModel):
    """Liste de commandes."""
    items: List[PurchaseOrderResponse]
    total: int


# ============================================================================
# SCHÉMAS RÉCEPTIONS
# ============================================================================

class ReceiptLineCreate(BaseModel):
    """Création d'une ligne de réception."""
    order_line_id: UUID
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    description: str
    ordered_quantity: Decimal
    received_quantity: Decimal
    rejected_quantity: Decimal = Decimal("0")
    unit: str = "UNIT"
    rejection_reason: Optional[str] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None


class ReceiptLineResponse(ReceiptLineCreate):
    """Réponse ligne de réception."""
    id: UUID
    receipt_id: UUID
    line_number: int
    serial_numbers: List[str] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class GoodsReceiptCreate(BaseModel):
    """Création d'une réception."""
    order_id: UUID
    receipt_date: date
    delivery_note: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    warehouse_id: Optional[UUID] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    lines: List[ReceiptLineCreate] = Field(default_factory=list)


class GoodsReceiptResponse(BaseModel):
    """Réponse réception."""
    id: UUID
    number: str
    order_id: UUID
    supplier_id: UUID
    status: ReceivingStatus
    receipt_date: date
    delivery_note: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    warehouse_id: Optional[UUID] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    lines: List[ReceiptLineResponse] = Field(default_factory=list)
    received_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS FACTURES D'ACHAT
# ============================================================================

class InvoiceLineCreate(BaseModel):
    """Création d'une ligne de facture."""
    order_line_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal
    unit: str = "UNIT"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("20")
    account_id: Optional[UUID] = None
    analytic_code: Optional[str] = None
    notes: Optional[str] = None


class InvoiceLineResponse(InvoiceLineCreate):
    """Réponse ligne de facture."""
    id: UUID
    invoice_id: UUID
    line_number: int
    tax_amount: Decimal = Decimal("0")
    total: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseInvoiceCreate(BaseModel):
    """Création d'une facture d'achat."""
    supplier_id: UUID
    order_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    supplier_invoice_number: Optional[str] = None
    supplier_invoice_date: Optional[date] = None
    currency: str = "EUR"
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class PurchaseInvoiceResponse(BaseModel):
    """Réponse facture d'achat."""
    id: UUID
    number: str
    supplier_id: UUID
    order_id: Optional[UUID] = None
    status: PurchaseInvoiceStatus
    invoice_date: date
    due_date: Optional[date] = None
    supplier_invoice_number: Optional[str] = None
    supplier_invoice_date: Optional[date] = None
    currency: str
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    paid_amount: Decimal = Decimal("0")
    remaining_amount: Decimal = Decimal("0")
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    lines: List[InvoiceLineResponse] = Field(default_factory=list)
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseInvoiceList(BaseModel):
    """Liste de factures."""
    items: List[PurchaseInvoiceResponse]
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
    reference: Optional[str] = None
    bank_account_id: Optional[UUID] = None
    notes: Optional[str] = None
    allocations: List[PaymentAllocationCreate] = Field(default_factory=list)


class SupplierPaymentResponse(BaseModel):
    """Réponse paiement fournisseur."""
    id: UUID
    number: str
    supplier_id: UUID
    payment_date: date
    amount: Decimal
    currency: str
    payment_method: str
    reference: Optional[str] = None
    bank_account_id: Optional[UUID] = None
    journal_entry_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS ÉVALUATION FOURNISSEUR
# ============================================================================

class SupplierEvaluationCreate(BaseModel):
    """Création d'une évaluation fournisseur."""
    supplier_id: UUID
    evaluation_date: date
    period_start: date
    period_end: date
    quality_score: Optional[Decimal] = None
    price_score: Optional[Decimal] = None
    delivery_score: Optional[Decimal] = None
    service_score: Optional[Decimal] = None
    reliability_score: Optional[Decimal] = None
    comments: Optional[str] = None
    recommendations: Optional[str] = None


class SupplierEvaluationResponse(SupplierEvaluationCreate):
    """Réponse évaluation fournisseur."""
    id: UUID
    overall_score: Optional[Decimal] = None
    total_orders: int = 0
    total_amount: Decimal = Decimal("0")
    on_time_delivery_rate: Optional[Decimal] = None
    quality_rejection_rate: Optional[Decimal] = None
    evaluated_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


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
    top_suppliers_by_amount: List[Dict[str, Any]] = Field(default_factory=list)
    top_suppliers_by_orders: List[Dict[str, Any]] = Field(default_factory=list)

    # Répartition par catégorie
    by_category: Dict[str, Decimal] = Field(default_factory=dict)
