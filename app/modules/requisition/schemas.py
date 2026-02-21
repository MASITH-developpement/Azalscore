"""
Schémas Pydantic Requisition / Demandes d'achat
===============================================
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============== CatalogCategory Schemas ==============

class CatalogCategoryCreate(BaseModel):
    """Création catégorie catalogue"""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    parent_id: Optional[UUID] = None
    gl_account: str = ""
    requires_approval: bool = False
    approval_threshold: Optional[Decimal] = None
    is_active: bool = True


class CatalogCategoryUpdate(BaseModel):
    """Mise à jour catégorie catalogue"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    gl_account: Optional[str] = None
    requires_approval: Optional[bool] = None
    approval_threshold: Optional[Decimal] = None
    is_active: Optional[bool] = None


class CatalogCategoryResponse(BaseModel):
    """Réponse catégorie catalogue"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str
    parent_id: Optional[UUID]
    gl_account: str
    requires_approval: bool
    approval_threshold: Optional[Decimal]
    is_active: bool
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: Optional[datetime]
    version: int


class CatalogCategoryListResponse(BaseModel):
    """Liste paginée catégories"""
    items: List[CatalogCategoryResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== CatalogItem Schemas ==============

class CatalogItemCreate(BaseModel):
    """Création article catalogue"""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    category_id: Optional[UUID] = None
    unit_price: Decimal = Decimal("0")
    currency: str = "EUR"
    unit_of_measure: str = "EA"
    preferred_vendor_id: Optional[UUID] = None
    preferred_vendor_name: str = ""
    vendor_item_code: str = ""
    lead_time_days: int = 0
    min_order_qty: int = 1
    max_order_qty: Optional[int] = None
    order_multiple: int = 1
    image_url: str = ""
    specifications: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class CatalogItemUpdate(BaseModel):
    """Mise à jour article catalogue"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    unit_price: Optional[Decimal] = None
    currency: Optional[str] = None
    unit_of_measure: Optional[str] = None
    preferred_vendor_id: Optional[UUID] = None
    preferred_vendor_name: Optional[str] = None
    vendor_item_code: Optional[str] = None
    lead_time_days: Optional[int] = None
    min_order_qty: Optional[int] = None
    max_order_qty: Optional[int] = None
    order_multiple: Optional[int] = None
    status: Optional[str] = None
    image_url: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class CatalogItemResponse(BaseModel):
    """Réponse article catalogue"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str
    category_id: Optional[UUID]
    category_name: str
    unit_price: Decimal
    currency: str
    unit_of_measure: str
    preferred_vendor_id: Optional[UUID]
    preferred_vendor_name: str
    vendor_item_code: str
    lead_time_days: int
    min_order_qty: int
    max_order_qty: Optional[int]
    order_multiple: int
    status: str
    image_url: str
    specifications: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: Optional[datetime]
    version: int


class CatalogItemListResponse(BaseModel):
    """Liste paginée articles"""
    items: List[CatalogItemResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== PreferredVendor Schemas ==============

class PreferredVendorCreate(BaseModel):
    """Création fournisseur préféré"""
    vendor_id: UUID
    vendor_code: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=200)
    category_ids: List[UUID] = Field(default_factory=list)
    contract_id: Optional[UUID] = None
    contract_end_date: Optional[date] = None
    discount_percentage: Decimal = Decimal("0")
    payment_terms: str = ""
    lead_time_days: int = 0
    minimum_order: Decimal = Decimal("0")
    rating: int = Field(0, ge=0, le=5)
    is_primary: bool = False
    is_active: bool = True


class PreferredVendorUpdate(BaseModel):
    """Mise à jour fournisseur préféré"""
    vendor_code: Optional[str] = Field(None, min_length=1, max_length=50)
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category_ids: Optional[List[UUID]] = None
    contract_id: Optional[UUID] = None
    contract_end_date: Optional[date] = None
    discount_percentage: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    minimum_order: Optional[Decimal] = None
    rating: Optional[int] = Field(None, ge=0, le=5)
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None


class PreferredVendorResponse(BaseModel):
    """Réponse fournisseur préféré"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    vendor_code: str
    vendor_name: str
    category_ids: List[UUID]
    contract_id: Optional[UUID]
    contract_end_date: Optional[date]
    discount_percentage: Decimal
    payment_terms: str
    lead_time_days: int
    minimum_order: Decimal
    rating: int
    is_primary: bool
    is_active: bool
    created_at: datetime
    version: int


class PreferredVendorListResponse(BaseModel):
    """Liste paginée fournisseurs"""
    items: List[PreferredVendorResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== BudgetAllocation Schemas ==============

class BudgetAllocationCreate(BaseModel):
    """Création allocation budgétaire"""
    budget_id: UUID
    budget_name: str = Field(..., min_length=1, max_length=200)
    department_id: UUID
    department_name: str = Field(..., min_length=1, max_length=200)
    cost_center_id: Optional[UUID] = None
    fiscal_year: int
    total_amount: Decimal = Decimal("0")
    category_allocations: Dict[str, Decimal] = Field(default_factory=dict)
    is_active: bool = True


class BudgetAllocationUpdate(BaseModel):
    """Mise à jour allocation budgétaire"""
    budget_name: Optional[str] = Field(None, min_length=1, max_length=200)
    department_name: Optional[str] = Field(None, min_length=1, max_length=200)
    total_amount: Optional[Decimal] = None
    category_allocations: Optional[Dict[str, Decimal]] = None
    is_active: Optional[bool] = None


class BudgetAllocationResponse(BaseModel):
    """Réponse allocation budgétaire"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    budget_id: UUID
    budget_name: str
    department_id: UUID
    department_name: str
    cost_center_id: Optional[UUID]
    fiscal_year: int
    total_amount: Decimal
    committed_amount: Decimal
    spent_amount: Decimal
    available_amount: Decimal
    category_allocations: Dict[str, Decimal]
    is_active: bool
    created_at: datetime
    version: int


class BudgetAllocationListResponse(BaseModel):
    """Liste paginée allocations"""
    items: List[BudgetAllocationResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== RequisitionLine Schemas ==============

class RequisitionLineCreate(BaseModel):
    """Création ligne demande"""
    item_id: Optional[UUID] = None
    item_code: str = ""
    description: str = Field(..., min_length=1)
    category_id: Optional[UUID] = None
    category_name: str = ""
    quantity: Decimal = Decimal("1")
    unit_of_measure: str = "EA"
    unit_price: Decimal = Decimal("0")
    currency: str = "EUR"
    suggested_vendor_id: Optional[UUID] = None
    suggested_vendor_name: str = ""
    budget_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    gl_account: str = ""
    specifications: str = ""
    notes: str = ""


class RequisitionLineUpdate(BaseModel):
    """Mise à jour ligne demande"""
    item_id: Optional[UUID] = None
    item_code: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    currency: Optional[str] = None
    suggested_vendor_id: Optional[UUID] = None
    suggested_vendor_name: Optional[str] = None
    budget_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    gl_account: Optional[str] = None
    specifications: Optional[str] = None
    notes: Optional[str] = None


class RequisitionLineResponse(BaseModel):
    """Réponse ligne demande"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    requisition_id: UUID
    line_number: int
    item_id: Optional[UUID]
    item_code: str
    description: str
    category_id: Optional[UUID]
    category_name: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    total_price: Decimal
    currency: str
    suggested_vendor_id: Optional[UUID]
    suggested_vendor_name: str
    status: str
    po_id: Optional[UUID]
    po_number: str
    po_line_id: Optional[UUID]
    ordered_quantity: Decimal
    received_quantity: Decimal
    budget_id: Optional[UUID]
    cost_center_id: Optional[UUID]
    gl_account: str
    specifications: str
    notes: str


# ============== ApprovalStep Schemas ==============

class ApprovalStepCreate(BaseModel):
    """Création étape approbation"""
    approver_id: UUID
    approver_name: str = Field(..., min_length=1, max_length=200)


class ApprovalStepResponse(BaseModel):
    """Réponse étape approbation"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    requisition_id: UUID
    step_number: int
    approver_id: UUID
    approver_name: str
    status: str
    comments: str
    decided_at: Optional[datetime]


class ApprovalDecision(BaseModel):
    """Décision d'approbation"""
    decision: str = Field(..., pattern="^(approved|rejected)$")
    comments: str = ""


# ============== Comment Schemas ==============

class CommentCreate(BaseModel):
    """Création commentaire"""
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class CommentResponse(BaseModel):
    """Réponse commentaire"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requisition_id: UUID
    author_id: UUID
    author_name: str
    content: str
    is_internal: bool
    created_at: datetime


# ============== Requisition Schemas ==============

class RequisitionCreate(BaseModel):
    """Création demande d'achat"""
    requisition_type: str = "goods"
    priority: str = "medium"
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    justification: str = ""
    department_id: Optional[UUID] = None
    department_name: str = ""
    required_date: Optional[date] = None
    budget_id: Optional[UUID] = None
    budget_name: str = ""
    currency: str = "EUR"
    lines: List[RequisitionLineCreate] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class RequisitionUpdate(BaseModel):
    """Mise à jour demande d'achat"""
    requisition_type: Optional[str] = None
    priority: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    justification: Optional[str] = None
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    required_date: Optional[date] = None
    budget_id: Optional[UUID] = None
    budget_name: Optional[str] = None
    currency: Optional[str] = None
    tags: Optional[List[str]] = None


class RequisitionResponse(BaseModel):
    """Réponse demande d'achat"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    requisition_number: str
    requisition_type: str
    status: str
    priority: str
    requester_id: UUID
    requester_name: str
    requester_email: str
    department_id: Optional[UUID]
    department_name: str
    title: str
    description: str
    justification: str
    total_amount: Decimal
    currency: str
    required_date: Optional[date]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    closed_at: Optional[datetime]
    current_approver_id: Optional[UUID]
    current_approver_name: str
    budget_id: Optional[UUID]
    budget_name: str
    budget_check_passed: bool
    budget_check_message: str
    po_ids: List[UUID]
    tags: List[str]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: Optional[datetime]
    version: int


class RequisitionDetailResponse(RequisitionResponse):
    """Réponse détaillée demande"""
    lines: List[RequisitionLineResponse] = Field(default_factory=list)
    approval_steps: List[ApprovalStepResponse] = Field(default_factory=list)
    comments: List[CommentResponse] = Field(default_factory=list)


class RequisitionListResponse(BaseModel):
    """Liste paginée demandes"""
    items: List[RequisitionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RequisitionFilters(BaseModel):
    """Filtres pour liste demandes"""
    status: Optional[str] = None
    requisition_type: Optional[str] = None
    priority: Optional[str] = None
    requester_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    approver_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


# ============== Template Schemas ==============

class TemplateCreate(BaseModel):
    """Création modèle demande"""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    requisition_type: str = "goods"
    default_lines: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class TemplateUpdate(BaseModel):
    """Mise à jour modèle demande"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    requisition_type: Optional[str] = None
    default_lines: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Réponse modèle demande"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str
    requisition_type: str
    default_lines: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    created_by: Optional[UUID]
    version: int


class TemplateListResponse(BaseModel):
    """Liste paginée modèles"""
    items: List[TemplateResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Stats Schemas ==============

class RequisitionStats(BaseModel):
    """Statistiques demandes"""
    tenant_id: UUID
    period_start: date
    period_end: date
    total_requisitions: int = 0
    draft_count: int = 0
    pending_approval_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    ordered_count: int = 0
    total_amount: Decimal = Decimal("0")
    approved_amount: Decimal = Decimal("0")
    average_approval_time_days: Decimal = Decimal("0")
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_department: Dict[str, Dict] = Field(default_factory=dict)
    by_category: Dict[str, Decimal] = Field(default_factory=dict)
    top_items: List[Dict] = Field(default_factory=list)


class BudgetCheckResult(BaseModel):
    """Résultat vérification budget"""
    passed: bool
    message: str
    available_amount: Decimal = Decimal("0")
    required_amount: Decimal = Decimal("0")
    over_budget_amount: Decimal = Decimal("0")


# ============== Common Schemas ==============

class AutocompleteResponse(BaseModel):
    """Réponse autocomplete"""
    items: List[Dict[str, Any]]


class BulkResult(BaseModel):
    """Résultat opération en masse"""
    success_count: int
    failure_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
