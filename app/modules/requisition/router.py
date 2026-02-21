"""
Routes API Requisition / Demandes d'achat
=========================================
- Catalogue interne (catégories et articles)
- Gestion des fournisseurs préférés
- Allocations budgétaires
- CRUD demandes d'achat
- Workflow d'approbation
- Templates
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .exceptions import (
    CatalogCategoryNotFoundError, CatalogCategoryDuplicateError,
    CatalogItemNotFoundError, CatalogItemDuplicateError,
    PreferredVendorNotFoundError, PreferredVendorDuplicateError,
    BudgetAllocationNotFoundError, BudgetAllocationDuplicateError,
    BudgetExceededError,
    RequisitionNotFoundError, RequisitionValidationError, RequisitionStateError,
    RequisitionEmptyError, RequisitionLineNotFoundError,
    ApprovalNotAuthorizedError, NoApproverError,
    TemplateNotFoundError, TemplateDuplicateError
)
from .schemas import (
    # Category
    CatalogCategoryCreate, CatalogCategoryUpdate, CatalogCategoryResponse,
    CatalogCategoryListResponse,
    # Item
    CatalogItemCreate, CatalogItemUpdate, CatalogItemResponse,
    CatalogItemListResponse,
    # Vendor
    PreferredVendorCreate, PreferredVendorUpdate, PreferredVendorResponse,
    PreferredVendorListResponse,
    # Budget
    BudgetAllocationCreate, BudgetAllocationUpdate, BudgetAllocationResponse,
    BudgetAllocationListResponse, BudgetCheckResult,
    # Requisition
    RequisitionCreate, RequisitionUpdate, RequisitionResponse,
    RequisitionDetailResponse, RequisitionListResponse, RequisitionFilters,
    # Line
    RequisitionLineCreate, RequisitionLineUpdate, RequisitionLineResponse,
    # Approval
    ApprovalStepCreate, ApprovalStepResponse, ApprovalDecision,
    # Comment
    CommentCreate, CommentResponse,
    # Template
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse,
    # Common
    AutocompleteResponse, BulkResult
)
from .service import RequisitionService


router = APIRouter(prefix="/requisition", tags=["Requisition"])


def get_service(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> RequisitionService:
    """Factory pour le service Requisition."""
    return RequisitionService(db, user.tenant_id, user.id)


# ============================================================================
# Catalog Category Routes
# ============================================================================

@router.get("/categories", response_model=CatalogCategoryListResponse)
async def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    is_active: Optional[bool] = None,
    parent_id: Optional[UUID] = None,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:category:read")
):
    """Liste les catégories du catalogue."""
    items, total, pages = service.list_categories(
        page, page_size, search, is_active, parent_id
    )
    return CatalogCategoryListResponse(
        items=[CatalogCategoryResponse.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/categories/{category_id}", response_model=CatalogCategoryResponse)
async def get_category(
    category_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:category:read")
):
    """Récupère une catégorie."""
    try:
        category = service.get_category(category_id)
        return CatalogCategoryResponse.model_validate(category)
    except CatalogCategoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/categories", response_model=CatalogCategoryResponse, status_code=201)
async def create_category(
    data: CatalogCategoryCreate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:category:create")
):
    """Crée une catégorie."""
    try:
        category = service.create_category(data)
        return CatalogCategoryResponse.model_validate(category)
    except CatalogCategoryDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/categories/{category_id}", response_model=CatalogCategoryResponse)
async def update_category(
    category_id: UUID,
    data: CatalogCategoryUpdate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:category:update")
):
    """Met à jour une catégorie."""
    try:
        category = service.update_category(category_id, data)
        return CatalogCategoryResponse.model_validate(category)
    except CatalogCategoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CatalogCategoryDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:category:delete")
):
    """Supprime une catégorie."""
    try:
        service.delete_category(category_id)
    except CatalogCategoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/categories/{category_id}/restore", response_model=CatalogCategoryResponse)
async def restore_category(
    category_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:category:delete")
):
    """Restaure une catégorie supprimée."""
    try:
        category = service.restore_category(category_id)
        return CatalogCategoryResponse.model_validate(category)
    except CatalogCategoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/categories/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_categories(
    q: str = Query(..., min_length=2),
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:category:read")
):
    """Autocomplete catégories."""
    return AutocompleteResponse(items=service.autocomplete_category(q))


# ============================================================================
# Catalog Item Routes
# ============================================================================

@router.get("/items", response_model=CatalogItemListResponse)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[str] = None,
    category_id: Optional[UUID] = None,
    vendor_id: Optional[UUID] = None,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:item:read")
):
    """Liste les articles du catalogue."""
    items, total, pages = service.list_items(
        page, page_size, search, status, category_id, vendor_id
    )
    return CatalogItemListResponse(
        items=[CatalogItemResponse.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/items/{item_id}", response_model=CatalogItemResponse)
async def get_item(
    item_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:item:read")
):
    """Récupère un article."""
    try:
        item = service.get_item(item_id)
        return CatalogItemResponse.model_validate(item)
    except CatalogItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/items", response_model=CatalogItemResponse, status_code=201)
async def create_item(
    data: CatalogItemCreate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:item:create")
):
    """Crée un article."""
    try:
        item = service.create_item(data)
        return CatalogItemResponse.model_validate(item)
    except CatalogItemDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except CatalogCategoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/items/{item_id}", response_model=CatalogItemResponse)
async def update_item(
    item_id: UUID,
    data: CatalogItemUpdate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:item:update")
):
    """Met à jour un article."""
    try:
        item = service.update_item(item_id, data)
        return CatalogItemResponse.model_validate(item)
    except CatalogItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CatalogItemDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:item:delete")
):
    """Supprime un article."""
    try:
        service.delete_item(item_id)
    except CatalogItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/items/{item_id}/restore", response_model=CatalogItemResponse)
async def restore_item(
    item_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:item:delete")
):
    """Restaure un article supprimé."""
    try:
        item = service.restore_item(item_id)
        return CatalogItemResponse.model_validate(item)
    except CatalogItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/items/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_items(
    q: str = Query(..., min_length=2),
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:item:read")
):
    """Autocomplete articles."""
    return AutocompleteResponse(items=service.autocomplete_item(q))


# ============================================================================
# Preferred Vendor Routes
# ============================================================================

@router.get("/vendors", response_model=PreferredVendorListResponse)
async def list_preferred_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    is_active: Optional[bool] = None,
    category_id: Optional[UUID] = None,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:vendor:read")
):
    """Liste les fournisseurs préférés."""
    items, total, pages = service.list_preferred_vendors(
        page, page_size, search, is_active, category_id
    )
    return PreferredVendorListResponse(
        items=[PreferredVendorResponse.model_validate(v) for v in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/vendors/category/{category_id}", response_model=List[PreferredVendorResponse])
async def get_vendors_for_category(
    category_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:vendor:read")
):
    """Récupère les fournisseurs préférés pour une catégorie."""
    vendors = service.get_vendors_for_category(category_id)
    return [PreferredVendorResponse.model_validate(v) for v in vendors]


@router.get("/vendors/{vendor_pref_id}", response_model=PreferredVendorResponse)
async def get_preferred_vendor(
    vendor_pref_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:vendor:read")
):
    """Récupère un fournisseur préféré."""
    try:
        vendor = service.get_preferred_vendor(vendor_pref_id)
        return PreferredVendorResponse.model_validate(vendor)
    except PreferredVendorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/vendors", response_model=PreferredVendorResponse, status_code=201)
async def create_preferred_vendor(
    data: PreferredVendorCreate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:vendor:create")
):
    """Crée un fournisseur préféré."""
    try:
        vendor = service.create_preferred_vendor(data)
        return PreferredVendorResponse.model_validate(vendor)
    except PreferredVendorDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/vendors/{vendor_pref_id}", response_model=PreferredVendorResponse)
async def update_preferred_vendor(
    vendor_pref_id: UUID,
    data: PreferredVendorUpdate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:vendor:update")
):
    """Met à jour un fournisseur préféré."""
    try:
        vendor = service.update_preferred_vendor(vendor_pref_id, data)
        return PreferredVendorResponse.model_validate(vendor)
    except PreferredVendorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/vendors/{vendor_pref_id}", status_code=204)
async def delete_preferred_vendor(
    vendor_pref_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:vendor:delete")
):
    """Supprime un fournisseur préféré."""
    try:
        service.delete_preferred_vendor(vendor_pref_id)
    except PreferredVendorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Budget Allocation Routes
# ============================================================================

@router.get("/budgets", response_model=BudgetAllocationListResponse)
async def list_budget_allocations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    fiscal_year: Optional[int] = None,
    department_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:budget:read")
):
    """Liste les allocations budgétaires."""
    items, total, pages = service.list_budget_allocations(
        page, page_size, fiscal_year, department_id, is_active
    )
    return BudgetAllocationListResponse(
        items=[BudgetAllocationResponse.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/budgets/{allocation_id}", response_model=BudgetAllocationResponse)
async def get_budget_allocation(
    allocation_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:budget:read")
):
    """Récupère une allocation budgétaire."""
    try:
        allocation = service.get_budget_allocation(allocation_id)
        return BudgetAllocationResponse.model_validate(allocation)
    except BudgetAllocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/budgets", response_model=BudgetAllocationResponse, status_code=201)
async def create_budget_allocation(
    data: BudgetAllocationCreate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:budget:create")
):
    """Crée une allocation budgétaire."""
    try:
        allocation = service.create_budget_allocation(data)
        return BudgetAllocationResponse.model_validate(allocation)
    except BudgetAllocationDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/budgets/{allocation_id}", response_model=BudgetAllocationResponse)
async def update_budget_allocation(
    allocation_id: UUID,
    data: BudgetAllocationUpdate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:budget:update")
):
    """Met à jour une allocation budgétaire."""
    try:
        allocation = service.update_budget_allocation(allocation_id, data)
        return BudgetAllocationResponse.model_validate(allocation)
    except BudgetAllocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/budgets/check", response_model=BudgetCheckResult)
async def check_budget(
    department_id: UUID,
    amount: Decimal,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:budget:read")
):
    """Vérifie la disponibilité budgétaire."""
    return service.check_budget(department_id, amount)


# ============================================================================
# Requisition Routes
# ============================================================================

@router.get("/requisitions", response_model=RequisitionListResponse)
async def list_requisitions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[str] = None,
    requisition_type: Optional[str] = None,
    priority: Optional[str] = None,
    requester_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    approver_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:read")
):
    """Liste les demandes d'achat."""
    items, total, pages = service.list_requisitions(
        page, page_size, search, status, requisition_type, priority,
        requester_id, department_id, approver_id, date_from, date_to,
        min_amount, max_amount
    )
    return RequisitionListResponse(
        items=[RequisitionResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/requisitions/pending-approval", response_model=RequisitionListResponse)
async def list_pending_approval(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: RequisitionService = Depends(get_service),
    user=Depends(get_current_user),
    _: None = require_permission("requisition:approve")
):
    """Liste les demandes en attente d'approbation pour l'utilisateur."""
    items, total, pages = service.list_pending_approval(user.id, page, page_size)
    return RequisitionListResponse(
        items=[RequisitionResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/requisitions/{req_id}", response_model=RequisitionDetailResponse)
async def get_requisition(
    req_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:read")
):
    """Récupère une demande d'achat avec détails."""
    try:
        req = service.get_requisition(req_id)
        lines = service.get_lines(req_id)
        steps = service.get_approval_steps(req_id)
        comments = service.get_comments(req_id, include_internal=True)

        response = RequisitionDetailResponse.model_validate(req)
        response.lines = [RequisitionLineResponse.model_validate(l) for l in lines]
        response.approval_steps = [ApprovalStepResponse.model_validate(s) for s in steps]
        response.comments = [CommentResponse.model_validate(c) for c in comments]
        return response
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/requisitions", response_model=RequisitionResponse, status_code=201)
async def create_requisition(
    data: RequisitionCreate,
    service: RequisitionService = Depends(get_service),
    user=Depends(get_current_user),
    _: None = require_permission("requisition:create")
):
    """Crée une demande d'achat."""
    try:
        req = service.create_requisition(
            data,
            requester_name=getattr(user, 'name', str(user.id)),
            requester_email=getattr(user, 'email', '')
        )
        return RequisitionResponse.model_validate(req)
    except RequisitionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/requisitions/{req_id}", response_model=RequisitionResponse)
async def update_requisition(
    req_id: UUID,
    data: RequisitionUpdate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:update")
):
    """Met à jour une demande d'achat."""
    try:
        req = service.update_requisition(req_id, data)
        return RequisitionResponse.model_validate(req)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/requisitions/{req_id}", status_code=204)
async def delete_requisition(
    req_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:delete")
):
    """Supprime une demande d'achat."""
    try:
        service.delete_requisition(req_id)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requisitions/{req_id}/restore", response_model=RequisitionResponse)
async def restore_requisition(
    req_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:delete")
):
    """Restaure une demande supprimée."""
    try:
        req = service.restore_requisition(req_id)
        return RequisitionResponse.model_validate(req)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/requisitions/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_requisitions(
    q: str = Query(..., min_length=2),
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:read")
):
    """Autocomplete demandes."""
    return AutocompleteResponse(items=service.autocomplete_requisition(q))


# ============================================================================
# Line Routes
# ============================================================================

@router.post("/requisitions/{req_id}/lines", response_model=RequisitionLineResponse, status_code=201)
async def add_line(
    req_id: UUID,
    data: RequisitionLineCreate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:update")
):
    """Ajoute une ligne à la demande."""
    try:
        line = service.add_line(req_id, data)
        return RequisitionLineResponse.model_validate(line)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/requisitions/lines/{line_id}", response_model=RequisitionLineResponse)
async def update_line(
    line_id: UUID,
    data: RequisitionLineUpdate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:update")
):
    """Met à jour une ligne."""
    try:
        line = service.update_line(line_id, data)
        return RequisitionLineResponse.model_validate(line)
    except RequisitionLineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/requisitions/lines/{line_id}", status_code=204)
async def remove_line(
    line_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:update")
):
    """Supprime une ligne."""
    try:
        service.remove_line(line_id)
    except RequisitionLineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Workflow Routes
# ============================================================================

@router.post("/requisitions/{req_id}/submit", response_model=RequisitionResponse)
async def submit_requisition(
    req_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:submit")
):
    """Soumet une demande."""
    try:
        req = service.submit_requisition(req_id)
        return RequisitionResponse.model_validate(req)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RequisitionStateError, RequisitionEmptyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requisitions/{req_id}/request-approval", response_model=RequisitionResponse)
async def request_approval(
    req_id: UUID,
    approvers: List[ApprovalStepCreate],
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:submit")
):
    """Demande l'approbation."""
    try:
        req = service.submit_for_approval(req_id, approvers)
        return RequisitionResponse.model_validate(req)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RequisitionStateError, NoApproverError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requisitions/{req_id}/approve", response_model=RequisitionResponse)
async def process_approval(
    req_id: UUID,
    decision: ApprovalDecision,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:approve")
):
    """Traite une décision d'approbation."""
    try:
        req = service.process_approval(req_id, decision)
        return RequisitionResponse.model_validate(req)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ApprovalNotAuthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requisitions/{req_id}/cancel", response_model=RequisitionResponse)
async def cancel_requisition(
    req_id: UUID,
    reason: str = "",
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:cancel")
):
    """Annule une demande."""
    try:
        req = service.cancel_requisition(req_id, reason)
        return RequisitionResponse.model_validate(req)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requisitions/{req_id}/close", response_model=RequisitionResponse)
async def close_requisition(
    req_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:close")
):
    """Clôture une demande."""
    try:
        req = service.close_requisition(req_id)
        return RequisitionResponse.model_validate(req)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RequisitionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Comment Routes
# ============================================================================

@router.post("/requisitions/{req_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    req_id: UUID,
    data: CommentCreate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:comment")
):
    """Ajoute un commentaire."""
    try:
        comment = service.add_comment(req_id, data)
        return CommentResponse.model_validate(comment)
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/requisitions/{req_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    req_id: UUID,
    include_internal: bool = False,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:read")
):
    """Récupère les commentaires."""
    try:
        comments = service.get_comments(req_id, include_internal)
        return [CommentResponse.model_validate(c) for c in comments]
    except RequisitionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Template Routes
# ============================================================================

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    is_active: Optional[bool] = None,
    requisition_type: Optional[str] = None,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:template:read")
):
    """Liste les modèles de demande."""
    items, total, pages = service.list_templates(
        page, page_size, search, is_active, requisition_type
    )
    return TemplateListResponse(
        items=[TemplateResponse.model_validate(t) for t in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:template:read")
):
    """Récupère un modèle."""
    try:
        template = service.get_template(template_id)
        return TemplateResponse.model_validate(template)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:template:create")
):
    """Crée un modèle."""
    try:
        template = service.create_template(data)
        return TemplateResponse.model_validate(template)
    except TemplateDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:template:update")
):
    """Met à jour un modèle."""
    try:
        template = service.update_template(template_id, data)
        return TemplateResponse.model_validate(template)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:template:delete")
):
    """Supprime un modèle."""
    try:
        service.delete_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/templates/{template_id}/create-requisition", response_model=RequisitionResponse, status_code=201)
async def create_from_template(
    template_id: UUID,
    data: RequisitionCreate,
    service: RequisitionService = Depends(get_service),
    user=Depends(get_current_user),
    _: None = require_permission("requisition:create")
):
    """Crée une demande à partir d'un modèle."""
    try:
        req = service.create_from_template(
            template_id,
            data,
            requester_name=getattr(user, 'name', str(user.id)),
            requester_email=getattr(user, 'email', '')
        )
        return RequisitionResponse.model_validate(req)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/templates/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_templates(
    q: str = Query(..., min_length=2),
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:template:read")
):
    """Autocomplete modèles."""
    return AutocompleteResponse(items=service.autocomplete_template(q))


# ============================================================================
# Stats Routes
# ============================================================================

@router.get("/stats")
async def get_stats(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    service: RequisitionService = Depends(get_service),
    _: None = require_permission("requisition:stats")
):
    """Récupère les statistiques."""
    return service.get_stats(date_from, date_to)
