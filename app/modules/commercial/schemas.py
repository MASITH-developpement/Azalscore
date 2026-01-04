"""
AZALS MODULE M1 - Schémas Commercial
=====================================

Schémas Pydantic pour le CRM et la gestion commerciale.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
import json

from .models import (
    CustomerType, OpportunityStatus, DocumentType, DocumentStatus,
    PaymentMethod, PaymentTerms, ActivityType
)


# ============================================================================
# SCHÉMAS CLIENTS
# ============================================================================

class CustomerBase(BaseModel):
    """Base pour les clients."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = None
    customer_type: CustomerType = Field(default=CustomerType.PROSPECT, alias="type")

    # Contact
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None

    # Adresse
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    country_code: str = "FR"

    # Légal
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    legal_form: Optional[str] = None

    # Commercial
    assigned_to: Optional[UUID] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[Decimal] = None
    employee_count: Optional[int] = None

    # Conditions
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    payment_method: Optional[PaymentMethod] = None
    credit_limit: Optional[Decimal] = None
    currency: str = "EUR"
    discount_rate: float = 0.0

    # Classification
    tags: List[str] = Field(default_factory=list)
    segment: Optional[str] = None
    source: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class CustomerCreate(CustomerBase):
    """Création d'un client."""
    pass


class CustomerUpdate(BaseModel):
    """Mise à jour d'un client."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: Optional[str] = None
    legal_name: Optional[str] = None
    customer_type: Optional[CustomerType] = Field(default=None, alias="type")
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    country_code: Optional[str] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    legal_form: Optional[str] = None
    assigned_to: Optional[UUID] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[Decimal] = None
    employee_count: Optional[int] = None
    payment_terms: Optional[PaymentTerms] = None
    payment_method: Optional[PaymentMethod] = None
    credit_limit: Optional[Decimal] = None
    currency: Optional[str] = None
    discount_rate: Optional[float] = None
    tags: Optional[List[str]] = None
    segment: Optional[str] = None
    source: Optional[str] = None
    lead_score: Optional[int] = None
    health_score: Optional[int] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Réponse client."""
    id: UUID
    lead_score: int = 0
    health_score: int = 100
    total_revenue: Decimal = Decimal("0")
    order_count: int = 0
    last_order_date: Optional[date] = None
    first_order_date: Optional[date] = None
    is_active: bool = True
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerList(BaseModel):
    """Liste de clients."""
    items: List[CustomerResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS CONTACTS
# ============================================================================

class ContactBase(BaseModel):
    """Base pour les contacts."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    linkedin: Optional[str] = None
    is_primary: bool = False
    is_billing: bool = False
    is_shipping: bool = False
    is_decision_maker: bool = False
    preferred_language: str = "fr"
    preferred_contact_method: Optional[str] = None
    do_not_call: bool = False
    do_not_email: bool = False
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    """Création d'un contact."""
    customer_id: UUID


class ContactUpdate(BaseModel):
    """Mise à jour d'un contact."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    linkedin: Optional[str] = None
    is_primary: Optional[bool] = None
    is_billing: Optional[bool] = None
    is_shipping: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    preferred_language: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    do_not_call: Optional[bool] = None
    do_not_email: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ContactResponse(ContactBase):
    """Réponse contact."""
    id: UUID
    customer_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS OPPORTUNITÉS
# ============================================================================

class OpportunityBase(BaseModel):
    """Base pour les opportunités."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: OpportunityStatus = OpportunityStatus.NEW
    stage: Optional[str] = None
    probability: int = Field(default=10, ge=0, le=100)
    amount: Decimal = Decimal("0")
    currency: str = "EUR"
    expected_close_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    team: Optional[str] = None
    source: Optional[str] = None
    campaign: Optional[str] = None
    competitors: List[str] = Field(default_factory=list)
    products: List[Any] = Field(default_factory=list)
    notes: Optional[str] = None
    next_steps: Optional[str] = None

    @field_validator('competitors', 'products', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class OpportunityCreate(OpportunityBase):
    """Création d'une opportunité."""
    customer_id: UUID


class OpportunityUpdate(BaseModel):
    """Mise à jour d'une opportunité."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[OpportunityStatus] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    team: Optional[str] = None
    source: Optional[str] = None
    campaign: Optional[str] = None
    competitors: Optional[List[str]] = None
    products: Optional[List[Any]] = None
    win_reason: Optional[str] = None
    loss_reason: Optional[str] = None
    notes: Optional[str] = None
    next_steps: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    """Réponse opportunité."""
    id: UUID
    customer_id: UUID
    weighted_amount: Optional[Decimal] = None
    actual_close_date: Optional[date] = None
    win_reason: Optional[str] = None
    loss_reason: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityList(BaseModel):
    """Liste d'opportunités."""
    items: List[OpportunityResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS DOCUMENTS COMMERCIAUX
# ============================================================================

class DocumentLineBase(BaseModel):
    """Base pour les lignes de document."""
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    description: str
    quantity: Decimal = Decimal("1")
    unit: Optional[str] = None
    unit_price: Decimal = Decimal("0")
    discount_percent: float = 0.0
    tax_rate: float = 20.0
    notes: Optional[str] = None


class DocumentLineCreate(DocumentLineBase):
    """Création d'une ligne."""
    pass


class DocumentLineResponse(DocumentLineBase):
    """Réponse ligne."""
    id: UUID
    document_id: UUID
    line_number: int
    discount_amount: Decimal = Decimal("0")
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    """Base pour les documents commerciaux."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    document_type: DocumentType = Field(..., alias="type")
    reference: Optional[str] = None
    doc_date: date = Field(default_factory=date.today, alias="date")
    due_date: Optional[date] = None
    validity_date: Optional[date] = None
    delivery_date: Optional[date] = None
    billing_address: Optional[dict] = None
    shipping_address: Optional[dict] = None
    payment_terms: Optional[PaymentTerms] = None
    payment_method: Optional[PaymentMethod] = None
    shipping_method: Optional[str] = None
    shipping_cost: Decimal = Decimal("0")
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Création d'un document."""
    customer_id: UUID
    opportunity_id: Optional[UUID] = None
    lines: List[DocumentLineCreate] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    """Mise à jour d'un document."""
    reference: Optional[str] = None
    status: Optional[DocumentStatus] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    validity_date: Optional[date] = None
    delivery_date: Optional[date] = None
    billing_address: Optional[dict] = None
    shipping_address: Optional[dict] = None
    payment_terms: Optional[PaymentTerms] = None
    payment_method: Optional[PaymentMethod] = None
    shipping_method: Optional[str] = None
    shipping_cost: Optional[Decimal] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Réponse document."""
    id: UUID
    customer_id: UUID
    opportunity_id: Optional[UUID] = None
    number: str
    status: DocumentStatus
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    discount_percent: float = 0.0
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    currency: str = "EUR"
    paid_amount: Decimal = Decimal("0")
    remaining_amount: Optional[Decimal] = None
    tracking_number: Optional[str] = None
    parent_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    pdf_url: Optional[str] = None
    assigned_to: Optional[UUID] = None
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    lines: List[DocumentLineResponse] = Field(default_factory=list)
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """Liste de documents."""
    items: List[DocumentResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS PAIEMENTS
# ============================================================================

class PaymentBase(BaseModel):
    """Base pour les paiements."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    method: PaymentMethod
    amount: Decimal
    currency: str = "EUR"
    payment_date: date = Field(default_factory=date.today, alias="date")
    reference: Optional[str] = None
    bank_account: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Création d'un paiement."""
    document_id: UUID


class PaymentResponse(PaymentBase):
    """Réponse paiement."""
    id: UUID
    document_id: UUID
    received_date: Optional[date] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS ACTIVITÉS
# ============================================================================

class ActivityBase(BaseModel):
    """Base pour les activités."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    activity_type: ActivityType = Field(..., alias="type")
    subject: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    activity_date: datetime = Field(default_factory=datetime.utcnow, alias="date")
    due_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    assigned_to: Optional[UUID] = None


class ActivityCreate(ActivityBase):
    """Création d'une activité."""
    customer_id: UUID
    opportunity_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None


class ActivityUpdate(BaseModel):
    """Mise à jour d'une activité."""
    subject: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_completed: Optional[bool] = None
    assigned_to: Optional[UUID] = None


class ActivityResponse(ActivityBase):
    """Réponse activité."""
    id: UUID
    customer_id: UUID
    opportunity_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS PIPELINE
# ============================================================================

class PipelineStageBase(BaseModel):
    """Base pour les étapes du pipeline."""
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = None
    description: Optional[str] = None
    order: int = Field(..., ge=1)
    probability: int = Field(default=50, ge=0, le=100)
    color: str = "#3B82F6"
    is_won: bool = False
    is_lost: bool = False


class PipelineStageCreate(PipelineStageBase):
    """Création d'une étape."""
    pass


class PipelineStageResponse(PipelineStageBase):
    """Réponse étape."""
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHÉMAS PRODUITS
# ============================================================================

class ProductBase(BaseModel):
    """Base pour les produits."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    is_service: bool = False
    unit_price: Decimal = Decimal("0")
    currency: str = "EUR"
    unit: str = "pce"
    tax_rate: float = 20.0
    track_stock: bool = False
    stock_quantity: Decimal = Decimal("0")
    min_stock: Decimal = Decimal("0")
    image_url: Optional[str] = None
    gallery: List[str] = Field(default_factory=list)

    @field_validator('gallery', mode='before')
    @classmethod
    def parse_gallery(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class ProductCreate(ProductBase):
    """Création d'un produit."""
    pass


class ProductUpdate(BaseModel):
    """Mise à jour d'un produit."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_service: Optional[bool] = None
    unit_price: Optional[Decimal] = None
    currency: Optional[str] = None
    unit: Optional[str] = None
    tax_rate: Optional[float] = None
    track_stock: Optional[bool] = None
    stock_quantity: Optional[Decimal] = None
    min_stock: Optional[Decimal] = None
    image_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Réponse produit."""
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Liste de produits."""
    items: List[ProductResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS STATISTIQUES
# ============================================================================

class SalesDashboard(BaseModel):
    """Dashboard commercial."""
    # Chiffres clés
    total_revenue: Decimal = Decimal("0")
    total_orders: int = 0
    total_quotes: int = 0
    total_invoices: int = 0

    # Pipeline
    pipeline_value: Decimal = Decimal("0")
    weighted_pipeline: Decimal = Decimal("0")
    opportunities_count: int = 0
    won_this_month: int = 0
    lost_this_month: int = 0

    # Clients
    total_customers: int = 0
    new_customers_this_month: int = 0
    active_customers: int = 0

    # Conversion
    quote_to_order_rate: float = 0.0
    average_deal_size: Decimal = Decimal("0")

    # Par statut
    documents_by_status: dict = Field(default_factory=dict)
    opportunities_by_stage: dict = Field(default_factory=dict)


class PipelineStats(BaseModel):
    """Statistiques pipeline."""
    stages: List[dict]
    total_value: Decimal = Decimal("0")
    weighted_value: Decimal = Decimal("0")
    opportunities_count: int = 0
    average_probability: float = 0.0
