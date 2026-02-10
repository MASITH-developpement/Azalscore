"""
AZALS MODULE M4 - Schémas Purchases
====================================

Schémas Pydantic pour la gestion des achats.
"""

import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    InvoiceStatus,
    OrderStatus,
    SupplierStatus,
    SupplierType,
)


# ============================================================================
# SCHÉMAS FOURNISSEURS
# ============================================================================

class SupplierBase(BaseModel):
    """Base pour les fournisseurs."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    code: Optional[str] = Field(default=None, max_length=50)  # Auto-généré si non fourni
    name: str = Field(..., min_length=1, max_length=255)
    supplier_type: SupplierType = SupplierType.BOTH

    # Contact
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None

    # Adresse
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    country: str = "France"

    # Légal
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    legal_form: Optional[str] = None

    # Commercial
    payment_terms: Optional[str] = None
    currency: str = "EUR"
    credit_limit: Optional[Decimal] = None

    # Classification
    tags: Optional[str] = None
    category: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Création d'un fournisseur."""
    pass


class SupplierUpdate(BaseModel):
    """Mise à jour d'un fournisseur."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    supplier_type: Optional[SupplierType] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    legal_form: Optional[str] = None
    payment_terms: Optional[str] = None
    currency: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    status: Optional[SupplierStatus] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Réponse fournisseur."""
    id: UUID
    tenant_id: str
    status: SupplierStatus
    is_active: bool
    created_by: Optional[UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ============================================================================
# SCHÉMAS LIGNES COMMANDE
# ============================================================================

class PurchaseOrderLineBase(BaseModel):
    """Base pour les lignes de commande."""
    model_config = ConfigDict(from_attributes=True)

    line_number: int
    product_code: Optional[str] = None
    description: str
    quantity: Decimal = Decimal("1.000")
    unit: str = "unité"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("20.00")
    notes: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Création d'une ligne de commande."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Mise à jour d'une ligne de commande."""
    model_config = ConfigDict(from_attributes=True)

    product_code: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    received_quantity: Optional[Decimal] = None
    notes: Optional[str] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Réponse ligne de commande."""
    id: UUID
    tenant_id: str
    order_id: UUID
    discount_amount: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    received_quantity: Decimal
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ============================================================================
# SCHÉMAS COMMANDES
# ============================================================================

class PurchaseOrderBase(BaseModel):
    """Base pour les commandes."""
    model_config = ConfigDict(from_attributes=True)

    number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    date: datetime.datetime
    expected_date: Optional[datetime.datetime] = None
    reference: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_contact: Optional[str] = None
    delivery_phone: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    currency: str = "EUR"


class PurchaseOrderCreate(BaseModel):
    """Création d'une commande."""
    model_config = ConfigDict(from_attributes=True)

    supplier_id: UUID
    date: datetime.datetime
    expected_date: Optional[datetime.datetime] = None
    reference: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_contact: Optional[str] = None
    delivery_phone: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    currency: str = "EUR"
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Mise à jour d'une commande."""
    model_config = ConfigDict(from_attributes=True)

    supplier_id: Optional[UUID] = None
    date: Optional[datetime.datetime] = None
    expected_date: Optional[datetime.datetime] = None
    received_date: Optional[datetime.datetime] = None
    reference: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_contact: Optional[str] = None
    delivery_phone: Optional[str] = None
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    currency: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Réponse commande."""
    id: UUID
    tenant_id: str
    status: OrderStatus
    received_date: Optional[datetime.datetime] = None
    total_ht: Decimal
    total_tax: Decimal
    total_ttc: Decimal
    validated_at: Optional[datetime.datetime] = None
    validated_by: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)


# ============================================================================
# SCHÉMAS LIGNES FACTURE
# ============================================================================

class PurchaseInvoiceLineBase(BaseModel):
    """Base pour les lignes de facture."""
    model_config = ConfigDict(from_attributes=True)

    line_number: int
    product_code: Optional[str] = None
    description: str
    quantity: Decimal = Decimal("1.000")
    unit: str = "unité"
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("20.00")
    notes: Optional[str] = None


class PurchaseInvoiceLineCreate(PurchaseInvoiceLineBase):
    """Création d'une ligne de facture."""
    pass


class PurchaseInvoiceLineUpdate(BaseModel):
    """Mise à jour d'une ligne de facture."""
    model_config = ConfigDict(from_attributes=True)

    product_code: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    notes: Optional[str] = None


class PurchaseInvoiceLineResponse(PurchaseInvoiceLineBase):
    """Réponse ligne de facture."""
    id: UUID
    tenant_id: str
    invoice_id: UUID
    discount_amount: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ============================================================================
# SCHÉMAS FACTURES
# ============================================================================

class PurchaseInvoiceBase(BaseModel):
    """Base pour les factures."""
    model_config = ConfigDict(from_attributes=True)

    number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    order_id: Optional[UUID] = None
    invoice_date: datetime.datetime
    due_date: Optional[datetime.datetime] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    currency: str = "EUR"


class PurchaseInvoiceCreate(BaseModel):
    """Création d'une facture."""
    model_config = ConfigDict(from_attributes=True)

    number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    order_id: Optional[UUID] = None
    invoice_date: datetime.datetime
    due_date: Optional[datetime.datetime] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    currency: str = "EUR"
    lines: List[PurchaseInvoiceLineCreate] = Field(default_factory=list)


class PurchaseInvoiceUpdate(BaseModel):
    """Mise à jour d'une facture."""
    model_config = ConfigDict(from_attributes=True)

    supplier_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    invoice_date: Optional[datetime.datetime] = None
    due_date: Optional[datetime.datetime] = None
    payment_date: Optional[datetime.datetime] = None
    reference: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None


class PurchaseInvoiceResponse(PurchaseInvoiceBase):
    """Réponse facture."""
    id: UUID
    tenant_id: str
    status: InvoiceStatus
    payment_date: Optional[datetime.datetime] = None
    total_ht: Decimal
    total_tax: Decimal
    total_ttc: Decimal
    validated_at: Optional[datetime.datetime] = None
    validated_by: Optional[UUID] = None
    paid_at: Optional[datetime.datetime] = None
    paid_amount: Decimal
    payment_method: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    lines: List[PurchaseInvoiceLineResponse] = Field(default_factory=list)


# ============================================================================
# SCHÉMAS SUMMARY / DASHBOARD
# ============================================================================

class PurchasesSummary(BaseModel):
    """Résumé du module achats."""
    model_config = ConfigDict(from_attributes=True)

    # Fournisseurs
    total_suppliers: int
    active_suppliers: int
    pending_suppliers: int

    # Commandes
    total_orders: int
    draft_orders: int
    sent_orders: int
    confirmed_orders: int
    received_orders: int

    # Factures
    total_invoices: int
    pending_invoices: int
    validated_invoices: int
    paid_invoices: int

    # Montants (période en cours)
    period_orders_amount: Decimal
    period_invoices_amount: Decimal
    period_paid_amount: Decimal
    pending_payments_amount: Decimal

    # Statistiques
    average_order_amount: Decimal
    average_invoice_amount: Decimal
    top_suppliers: List[dict] = Field(default_factory=list)


# ============================================================================
# SCHÉMAS PAGINATION
# ============================================================================

class PaginatedSuppliers(BaseModel):
    """Liste paginée de fournisseurs."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SupplierResponse]


class PaginatedOrders(BaseModel):
    """Liste paginée de commandes."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[PurchaseOrderResponse]


class PaginatedInvoices(BaseModel):
    """Liste paginée de factures."""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[PurchaseInvoiceResponse]
