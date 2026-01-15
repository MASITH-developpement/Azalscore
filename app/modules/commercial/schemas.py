"""
AZALS MODULE M1 - Schémas Commercial
=====================================

Schémas Pydantic pour le CRM et la gestion commerciale.
"""

import datetime
import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    ActivityType,
    CustomerType,
    DocumentStatus,
    DocumentType,
    OpportunityStatus,
    PaymentMethod,
    PaymentTerms,
)

# ============================================================================
# SCHÉMAS CLIENTS
# ============================================================================

class CustomerBase(BaseModel):
    """Base pour les clients."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: str | None = None
    customer_type: CustomerType = Field(default=CustomerType.PROSPECT, alias="type")

    # Contact
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    website: str | None = None

    # Adresse
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
    country_code: str = "FR"

    # Légal
    tax_id: str | None = None
    registration_number: str | None = None
    legal_form: str | None = None

    # Commercial
    assigned_to: UUID | None = None
    industry: str | None = None
    size: str | None = None
    annual_revenue: Decimal | None = None
    employee_count: int | None = None

    # Conditions
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    payment_method: PaymentMethod | None = None
    credit_limit: Decimal | None = None
    currency: str = "EUR"
    discount_rate: float = 0.0

    # Classification
    tags: list[str] = Field(default_factory=list)
    segment: str | None = None
    source: str | None = None

    # Notes
    notes: str | None = None
    internal_notes: str | None = None

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class CustomerCreate(CustomerBase):
    """Création d'un client."""
    pass


class CustomerCreateAuto(BaseModel):
    """Création d'un client avec code auto-généré."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    # Code est optionnel - sera auto-généré si non fourni
    code: str | None = Field(default=None, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: str | None = None
    customer_type: CustomerType = Field(default=CustomerType.CUSTOMER, alias="type")

    # Contact
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    website: str | None = None

    # Adresse
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
    country_code: str = "FR"

    # Légal
    tax_id: str | None = None
    registration_number: str | None = None
    legal_form: str | None = None

    # Commercial
    assigned_to: UUID | None = None
    industry: str | None = None
    size: str | None = None
    annual_revenue: Decimal | None = None
    employee_count: int | None = None

    # Conditions
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    payment_method: PaymentMethod | None = None
    credit_limit: Decimal | None = None
    currency: str = "EUR"
    discount_rate: float = 0.0

    # Classification
    tags: list[str] = Field(default_factory=list)
    segment: str | None = None
    source: str | None = None

    # Notes
    notes: str | None = None
    internal_notes: str | None = None

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class CustomerUpdate(BaseModel):
    """Mise à jour d'un client."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: str | None = None
    legal_name: str | None = None
    customer_type: CustomerType | None = Field(default=None, alias="type")
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    website: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
    country_code: str | None = None
    tax_id: str | None = None
    registration_number: str | None = None
    legal_form: str | None = None
    assigned_to: UUID | None = None
    industry: str | None = None
    size: str | None = None
    annual_revenue: Decimal | None = None
    employee_count: int | None = None
    payment_terms: PaymentTerms | None = None
    payment_method: PaymentMethod | None = None
    credit_limit: Decimal | None = None
    currency: str | None = None
    discount_rate: float | None = None
    tags: list[str] | None = None
    segment: str | None = None
    source: str | None = None
    lead_score: int | None = None
    health_score: int | None = None
    notes: str | None = None
    internal_notes: str | None = None
    is_active: bool | None = None


class CustomerResponse(CustomerBase):
    """Réponse client."""
    id: UUID
    lead_score: int = 0
    health_score: int = 100
    total_revenue: Decimal = Decimal("0")
    order_count: int = 0
    last_order_date: datetime.date | None = None
    first_order_date: datetime.date | None = None
    is_active: bool = True
    created_by: UUID | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerList(BaseModel):
    """Liste de clients."""
    items: list[CustomerResponse]
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
    title: str | None = None
    job_title: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    linkedin: str | None = None
    is_primary: bool = False
    is_billing: bool = False
    is_shipping: bool = False
    is_decision_maker: bool = False
    preferred_language: str = "fr"
    preferred_contact_method: str | None = None
    do_not_call: bool = False
    do_not_email: bool = False
    notes: str | None = None


class ContactCreate(ContactBase):
    """Création d'un contact."""
    customer_id: UUID


class ContactUpdate(BaseModel):
    """Mise à jour d'un contact."""
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    job_title: str | None = None
    department: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    linkedin: str | None = None
    is_primary: bool | None = None
    is_billing: bool | None = None
    is_shipping: bool | None = None
    is_decision_maker: bool | None = None
    preferred_language: str | None = None
    preferred_contact_method: str | None = None
    do_not_call: bool | None = None
    do_not_email: bool | None = None
    notes: str | None = None
    is_active: bool | None = None


class ContactResponse(ContactBase):
    """Réponse contact."""
    id: UUID
    customer_id: UUID
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ContactList(BaseModel):
    """Liste de contacts."""
    items: list[ContactResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS OPPORTUNITÉS
# ============================================================================

class OpportunityBase(BaseModel):
    """Base pour les opportunités."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: OpportunityStatus = OpportunityStatus.NEW
    stage: str | None = None
    probability: int = Field(default=10, ge=0, le=100)
    amount: Decimal = Decimal("0")
    currency: str = "EUR"
    expected_close_date: datetime.date | None = None
    assigned_to: UUID | None = None
    team: str | None = None
    source: str | None = None
    campaign: str | None = None
    competitors: list[str] = Field(default_factory=list)
    products: list[Any] = Field(default_factory=list)
    notes: str | None = None
    next_steps: str | None = None

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
    name: str | None = None
    description: str | None = None
    status: OpportunityStatus | None = None
    stage: str | None = None
    probability: int | None = None
    amount: Decimal | None = None
    currency: str | None = None
    expected_close_date: datetime.date | None = None
    actual_close_date: datetime.date | None = None
    assigned_to: UUID | None = None
    team: str | None = None
    source: str | None = None
    campaign: str | None = None
    competitors: list[str] | None = None
    products: list[Any] | None = None
    win_reason: str | None = None
    loss_reason: str | None = None
    notes: str | None = None
    next_steps: str | None = None


class OpportunityResponse(OpportunityBase):
    """Réponse opportunité."""
    id: UUID
    customer_id: UUID
    weighted_amount: Decimal | None = None
    actual_close_date: datetime.date | None = None
    win_reason: str | None = None
    loss_reason: str | None = None
    created_by: UUID | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class OpportunityList(BaseModel):
    """Liste d'opportunités."""
    items: list[OpportunityResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# SCHÉMAS DOCUMENTS COMMERCIAUX
# ============================================================================

class DocumentLineBase(BaseModel):
    """Base pour les lignes de document."""
    product_id: UUID | None = None
    product_code: str | None = None
    description: str
    quantity: Decimal = Decimal("1")
    unit: str | None = None
    unit_price: Decimal = Decimal("0")
    discount_percent: float = 0.0
    tax_rate: float = 20.0
    notes: str | None = None


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
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    """Base pour les documents commerciaux."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    document_type: DocumentType = Field(..., alias="type")
    reference: str | None = None
    doc_date: datetime.date = Field(default_factory=datetime.date.today, alias="date")
    due_date: datetime.date | None = None
    validity_date: datetime.date | None = None
    delivery_date: datetime.date | None = None
    billing_address: dict | None = None
    shipping_address: dict | None = None
    payment_terms: PaymentTerms | None = None
    payment_method: PaymentMethod | None = None
    shipping_method: str | None = None
    shipping_cost: Decimal = Decimal("0")
    notes: str | None = None
    internal_notes: str | None = None
    terms: str | None = None


class DocumentCreate(DocumentBase):
    """Création d'un document."""
    customer_id: UUID
    opportunity_id: UUID | None = None
    lines: list[DocumentLineCreate] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    """Mise à jour d'un document."""
    reference: str | None = None
    status: DocumentStatus | None = None
    date: datetime.date | None = None
    due_date: datetime.date | None = None
    validity_date: datetime.date | None = None
    delivery_date: datetime.date | None = None
    billing_address: dict | None = None
    shipping_address: dict | None = None
    payment_terms: PaymentTerms | None = None
    payment_method: PaymentMethod | None = None
    shipping_method: str | None = None
    shipping_cost: Decimal | None = None
    tracking_number: str | None = None
    notes: str | None = None
    internal_notes: str | None = None
    terms: str | None = None


class DocumentResponse(DocumentBase):
    """Réponse document."""
    id: UUID
    customer_id: UUID
    opportunity_id: UUID | None = None
    number: str
    status: DocumentStatus
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    discount_percent: float = 0.0
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    currency: str = "EUR"
    paid_amount: Decimal = Decimal("0")
    remaining_amount: Decimal | None = None
    tracking_number: str | None = None
    parent_id: UUID | None = None
    invoice_id: UUID | None = None
    pdf_url: str | None = None
    assigned_to: UUID | None = None
    validated_by: UUID | None = None
    validated_at: datetime.datetime | None = None
    lines: list[DocumentLineResponse] = Field(default_factory=list)
    created_by: UUID | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentList(BaseModel):
    """Liste de documents."""
    items: list[DocumentResponse]
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
    payment_date: datetime.date = Field(default_factory=datetime.date.today, alias="date")
    reference: str | None = None
    bank_account: str | None = None
    transaction_id: str | None = None
    notes: str | None = None


class PaymentCreate(PaymentBase):
    """Création d'un paiement."""
    document_id: UUID


class PaymentResponse(PaymentBase):
    """Réponse paiement."""
    id: UUID
    document_id: UUID
    received_date: datetime.date | None = None
    created_by: UUID | None = None
    created_at: datetime.datetime



# ============================================================================
# SCHÉMAS ACTIVITÉS
# ============================================================================

class ActivityBase(BaseModel):
    """Base pour les activités."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    activity_type: ActivityType = Field(..., alias="type")
    subject: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    activity_date: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, alias="date")
    due_date: datetime.datetime | None = None
    duration_minutes: int | None = None
    assigned_to: UUID | None = None


class ActivityCreate(ActivityBase):
    """Création d'une activité."""
    customer_id: UUID
    opportunity_id: UUID | None = None
    contact_id: UUID | None = None


class ActivityUpdate(BaseModel):
    """Mise à jour d'une activité."""
    subject: str | None = None
    description: str | None = None
    date: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    duration_minutes: int | None = None
    is_completed: bool | None = None
    assigned_to: UUID | None = None


class ActivityResponse(ActivityBase):
    """Réponse activité."""
    id: UUID
    customer_id: UUID
    opportunity_id: UUID | None = None
    contact_id: UUID | None = None
    is_completed: bool = False
    completed_at: datetime.datetime | None = None
    created_by: UUID | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS PIPELINE
# ============================================================================

class PipelineStageBase(BaseModel):
    """Base pour les étapes du pipeline."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str | None = None
    description: str | None = None
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
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SCHÉMAS PRODUITS
# ============================================================================

class ProductBase(BaseModel):
    """Base pour les produits."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    is_service: bool = False
    unit_price: Decimal = Decimal("0")
    currency: str = "EUR"
    unit: str = "pce"
    tax_rate: float = 20.0
    track_stock: bool = False
    stock_quantity: Decimal = Decimal("0")
    min_stock: Decimal = Decimal("0")
    image_url: str | None = None
    gallery: list[str] = Field(default_factory=list)

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
    name: str | None = None
    description: str | None = None
    category: str | None = None
    is_service: bool | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    tax_rate: float | None = None
    track_stock: bool | None = None
    stock_quantity: Decimal | None = None
    min_stock: Decimal | None = None
    image_url: str | None = None
    gallery: list[str] | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    """Réponse produit."""
    id: UUID
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    """Liste de produits."""
    items: list[ProductResponse]
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
    stages: list[dict]
    total_value: Decimal = Decimal("0")
    weighted_value: Decimal = Decimal("0")
    opportunities_count: int = 0
    average_probability: float = 0.0
