"""
AZALS MODULE - Contacts Unifiés - Schémas
=========================================

Schémas Pydantic pour la validation et la sérialisation.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    AddressType,
    ContactPersonRole,
    CustomerType,
    EntityType,
    RelationType,
    SupplierStatus,
    SupplierType,
)


# ============================================================================
# SCHEMAS PERSONNE DE CONTACT
# ============================================================================

class ContactPersonBase(BaseModel):
    """Base pour les personnes de contact."""
    model_config = ConfigDict(from_attributes=True)

    role: ContactPersonRole = ContactPersonRole.OTHER
    custom_role: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    is_primary: bool = False
    notes: Optional[str] = None


class ContactPersonCreate(ContactPersonBase):
    """Création d'une personne de contact."""
    pass


class ContactPersonUpdate(BaseModel):
    """Mise à jour d'une personne de contact."""
    model_config = ConfigDict(from_attributes=True)

    role: Optional[ContactPersonRole] = None
    custom_role: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ContactPersonResponse(ContactPersonBase):
    """Réponse personne de contact."""
    id: UUID
    tenant_id: str
    contact_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Computed
    full_name: str
    display_role: str


# ============================================================================
# SCHEMAS ADRESSE
# ============================================================================

class ContactAddressBase(BaseModel):
    """Base pour les adresses."""
    model_config = ConfigDict(from_attributes=True)

    address_type: AddressType = AddressType.BILLING
    label: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    state: Optional[str] = Field(None, max_length=100)
    country_code: str = Field(default="FR", max_length=3)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_default: bool = False
    notes: Optional[str] = None


class ContactAddressCreate(ContactAddressBase):
    """Création d'une adresse."""
    pass


class ContactAddressUpdate(BaseModel):
    """Mise à jour d'une adresse."""
    model_config = ConfigDict(from_attributes=True)

    address_type: Optional[AddressType] = None
    label: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None
    country_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ContactAddressResponse(ContactAddressBase):
    """Réponse adresse."""
    id: UUID
    tenant_id: str
    contact_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Computed
    full_address: str
    display_label: str


# ============================================================================
# SCHEMAS CONTACT PRINCIPAL
# ============================================================================

class ContactBase(BaseModel):
    """Base pour les contacts."""
    model_config = ConfigDict(from_attributes=True)

    # Type d'entité (Particulier / Société)
    entity_type: EntityType = EntityType.COMPANY

    # Types de relation (Client / Fournisseur / Les deux)
    relation_types: List[RelationType] = Field(
        default_factory=list,
        description="Liste des types de relation (CUSTOMER, SUPPLIER)"
    )

    # Identification
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

    # Coordonnées
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)

    # Informations légales
    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    legal_form: Optional[str] = Field(None, max_length=50)

    # Logo
    logo_url: Optional[str] = Field(None, max_length=500)

    # Classification
    tags: List[str] = Field(default_factory=list)

    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

    @field_validator('relation_types', mode='before')
    @classmethod
    def validate_relation_types(cls, v):
        """Convertit les strings en enums si nécessaire."""
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    result.append(RelationType(item))
                elif isinstance(item, RelationType):
                    result.append(item)
                else:
                    result.append(item)
            return result
        return v


class ContactCreate(ContactBase):
    """
    Création d'un contact.
    Le code est optionnel - s'il n'est pas fourni, il sera auto-généré.
    """
    # Code optionnel (auto-généré si non fourni)
    code: Optional[str] = Field(None, max_length=20)

    # Au moins un type de relation est requis
    relation_types: List[RelationType] = Field(
        ...,
        min_length=1,
        description="Au moins un type de relation requis"
    )

    # ========== CONDITIONS CLIENT (optionnel) ==========
    customer_type: Optional[CustomerType] = None
    customer_payment_terms: Optional[str] = None
    customer_payment_method: Optional[str] = None
    customer_credit_limit: Optional[Decimal] = None
    customer_discount_rate: Optional[Decimal] = None
    customer_currency: str = "EUR"

    # CRM
    assigned_to: Optional[UUID] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    segment: Optional[str] = None

    # ========== CONDITIONS FOURNISSEUR (optionnel) ==========
    supplier_status: Optional[SupplierStatus] = None
    supplier_type: Optional[SupplierType] = None
    supplier_payment_terms: Optional[str] = None
    supplier_currency: str = "EUR"
    supplier_credit_limit: Optional[Decimal] = None
    supplier_category: Optional[str] = None

    # ========== PERSONNES ET ADRESSES (création inline) ==========
    persons: List[ContactPersonCreate] = Field(default_factory=list)
    addresses: List[ContactAddressCreate] = Field(default_factory=list)


class ContactUpdate(BaseModel):
    """Mise à jour d'un contact."""
    model_config = ConfigDict(from_attributes=True)

    entity_type: Optional[EntityType] = None
    relation_types: Optional[List[RelationType]] = None

    name: Optional[str] = None
    legal_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None

    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    legal_form: Optional[str] = None

    logo_url: Optional[str] = None

    # Client
    customer_type: Optional[CustomerType] = None
    customer_payment_terms: Optional[str] = None
    customer_payment_method: Optional[str] = None
    customer_credit_limit: Optional[Decimal] = None
    customer_discount_rate: Optional[Decimal] = None
    customer_currency: Optional[str] = None
    assigned_to: Optional[UUID] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    segment: Optional[str] = None

    # Fournisseur
    supplier_status: Optional[SupplierStatus] = None
    supplier_type: Optional[SupplierType] = None
    supplier_payment_terms: Optional[str] = None
    supplier_currency: Optional[str] = None
    supplier_credit_limit: Optional[Decimal] = None
    supplier_category: Optional[str] = None

    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

    is_active: Optional[bool] = None


class ContactResponse(ContactBase):
    """Réponse contact complète."""
    id: UUID
    tenant_id: str
    code: str

    # Client
    customer_type: Optional[CustomerType] = None
    customer_payment_terms: Optional[str] = None
    customer_payment_method: Optional[str] = None
    customer_credit_limit: Optional[Decimal] = None
    customer_discount_rate: Optional[Decimal] = None
    customer_currency: str = "EUR"
    assigned_to: Optional[UUID] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    segment: Optional[str] = None
    lead_score: int = 0
    health_score: int = 100
    customer_total_revenue: Decimal = Decimal("0.00")
    customer_order_count: int = 0
    customer_last_order_date: Optional[datetime] = None
    customer_first_order_date: Optional[datetime] = None

    # Fournisseur
    supplier_status: Optional[SupplierStatus] = None
    supplier_type: Optional[SupplierType] = None
    supplier_payment_terms: Optional[str] = None
    supplier_currency: str = "EUR"
    supplier_credit_limit: Optional[Decimal] = None
    supplier_category: Optional[str] = None
    supplier_total_purchases: Decimal = Decimal("0.00")
    supplier_order_count: int = 0
    supplier_last_order_date: Optional[datetime] = None

    # Métadonnées
    is_active: bool
    deleted_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    # Computed
    is_customer: bool
    is_supplier: bool
    display_name: str

    # Relations incluses
    persons: List[ContactPersonResponse] = Field(default_factory=list)
    addresses: List[ContactAddressResponse] = Field(default_factory=list)


class ContactSummary(BaseModel):
    """Résumé contact (pour les listes)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    entity_type: EntityType
    relation_types: List[RelationType]
    email: Optional[str] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None
    is_customer: bool
    is_supplier: bool
    is_active: bool


class ContactList(BaseModel):
    """Liste paginée de contacts."""
    items: List[ContactSummary]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1


# ============================================================================
# SCHEMAS LOOKUP (pour les sélecteurs)
# ============================================================================

class ContactLookup(BaseModel):
    """Contact pour les listes déroulantes / sélecteurs."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    entity_type: EntityType
    is_customer: bool
    is_supplier: bool
    logo_url: Optional[str] = None


class ContactLookupList(BaseModel):
    """Liste de contacts pour lookup."""
    items: List[ContactLookup]
    total: int
