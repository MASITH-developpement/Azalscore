"""
Routes API Manufacturing / Fabrication
=======================================
- CRUD complet pour BOM, Workcenter, Routing, WorkOrder
- Autocomplete pour tous les types
- Gestion des états et transitions
- Contrôles qualité
- Statistiques de production
- Permissions vérifiées sur chaque endpoint
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
    BOMNotFoundError, BOMDuplicateError, BOMValidationError, BOMStateError,
    BOMLineNotFoundError,
    WorkcenterNotFoundError, WorkcenterDuplicateError, WorkcenterValidationError,
    RoutingNotFoundError, RoutingDuplicateError,
    WorkOrderNotFoundError, WorkOrderValidationError, WorkOrderStateError,
    WorkOrderOperationNotFoundError, WorkOrderOperationStateError,
    QualityCheckNotFoundError, QualityCheckValidationError
)
from .models import BOMStatus, BOMType, WorkcenterState, WorkcenterType, WorkOrderStatus
from .schemas import (
    # BOM
    BOMCreate, BOMUpdate, BOMResponse, BOMListResponse, BOMFilters,
    BOMLineCreate, BOMLineUpdate, BOMLineResponse,
    BOMExplodeResponse, BOMExplodeItem,
    # Workcenter
    WorkcenterCreate, WorkcenterUpdate, WorkcenterResponse, WorkcenterListResponse,
    WorkcenterFilters,
    # Routing
    RoutingCreate, RoutingUpdate, RoutingResponse, RoutingListResponse,
    OperationCreate, OperationUpdate, OperationResponse,
    # Work Order
    WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse, WorkOrderListResponse,
    WorkOrderFilters, WorkOrderOperationResponse,
    # Quality
    QualityCheckCreate, QualityCheckUpdate, QualityCheckResponse,
    # Logs
    ProductionLogResponse,
    # Common
    AutocompleteResponse, BulkResult, ProductionStats,
    RecordProductionRequest, StartOperationRequest, CompleteOperationRequest
)
from .service import ManufacturingService


router = APIRouter(prefix="/manufacturing", tags=["Manufacturing"])


def get_service(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ManufacturingService:
    """Factory pour le service Manufacturing."""
    return ManufacturingService(db, user.tenant_id, user.id)


# ============================================================================
# BOM Routes
# ============================================================================

@router.get("/boms", response_model=BOMListResponse)
async def list_boms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[BOMStatus]] = Query(None),
    bom_type: Optional[List[BOMType]] = Query(None),
    product_id: Optional[UUID] = Query(None),
    is_current: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.view")
):
    """Liste paginée des nomenclatures (BOMs)."""
    filters = BOMFilters(
        search=search,
        status=status,
        bom_type=bom_type,
        product_id=product_id,
        is_current=is_current
    )
    items, total, pages = service.list_boms(filters, page, page_size, sort_by, sort_dir)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get("/boms/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_boms(
    prefix: str = Query(..., min_length=2),
    field: str = Query("name", pattern="^(name|code)$"),
    limit: int = Query(10, ge=1, le=50),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.view")
):
    """Autocomplete pour les nomenclatures."""
    items = service.autocomplete_bom(prefix, field, limit)
    return {"items": items}


@router.get("/boms/{id}", response_model=BOMResponse)
async def get_bom(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.view")
):
    """Récupère une nomenclature par ID."""
    try:
        return service.get_bom(id)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/boms", response_model=BOMResponse, status_code=201)
async def create_bom(
    data: BOMCreate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.create")
):
    """Crée une nouvelle nomenclature."""
    try:
        return service.create_bom(data)
    except BOMDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/boms/{id}", response_model=BOMResponse)
async def update_bom(
    id: UUID,
    data: BOMUpdate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.edit")
):
    """Met à jour une nomenclature."""
    try:
        return service.update_bom(id, data)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (BOMStateError, BOMValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/boms/{id}", status_code=204)
async def delete_bom(
    id: UUID,
    hard: bool = Query(False),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.delete")
):
    """Supprime une nomenclature."""
    try:
        service.delete_bom(id, hard)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BOMValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/boms/{id}/restore", response_model=BOMResponse)
async def restore_bom(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.delete")
):
    """Restaure une nomenclature supprimée."""
    try:
        return service.restore_bom(id)
    except (BOMNotFoundError, BOMValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/boms/{id}/activate", response_model=BOMResponse)
async def activate_bom(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.edit")
):
    """Active une nomenclature (désactive les autres pour ce produit)."""
    try:
        return service.activate_bom(id)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BOMStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/boms/{id}/explode", response_model=BOMExplodeResponse)
async def explode_bom(
    id: UUID,
    quantity: Decimal = Query(Decimal("1"), gt=0),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.view")
):
    """Explose une nomenclature (liste tous les composants requis)."""
    try:
        components = service.explode_bom(id, quantity)
        return {"components": components}
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# BOM Lines
@router.post("/boms/{bom_id}/lines", response_model=BOMLineResponse, status_code=201)
async def add_bom_line(
    bom_id: UUID,
    data: BOMLineCreate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.edit")
):
    """Ajoute une ligne à une nomenclature."""
    try:
        return service.add_bom_line(bom_id, data)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BOMValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/boms/{bom_id}/lines/{line_id}", response_model=BOMLineResponse)
async def update_bom_line(
    bom_id: UUID,
    line_id: UUID,
    data: BOMLineUpdate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.edit")
):
    """Met à jour une ligne de nomenclature."""
    try:
        return service.update_bom_line(bom_id, line_id, data)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BOMLineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BOMValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/boms/{bom_id}/lines/{line_id}", status_code=204)
async def delete_bom_line(
    bom_id: UUID,
    line_id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.edit")
):
    """Supprime une ligne de nomenclature."""
    try:
        service.delete_bom_line(bom_id, line_id)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BOMLineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BOMValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Workcenter Routes
# ============================================================================

@router.get("/workcenters", response_model=WorkcenterListResponse)
async def list_workcenters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    workcenter_type: Optional[List[WorkcenterType]] = Query(None),
    state: Optional[List[WorkcenterState]] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("code"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.view")
):
    """Liste paginée des postes de travail."""
    filters = WorkcenterFilters(
        search=search,
        workcenter_type=workcenter_type,
        state=state,
        is_active=is_active
    )
    items, total, pages = service.list_workcenters(filters, page, page_size, sort_by, sort_dir)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get("/workcenters/available", response_model=List[WorkcenterResponse])
async def list_available_workcenters(
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.view")
):
    """Liste les postes de travail disponibles."""
    return service.get_available_workcenters()


@router.get("/workcenters/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_workcenters(
    prefix: str = Query(..., min_length=2),
    field: str = Query("name", pattern="^(name|code)$"),
    limit: int = Query(10, ge=1, le=50),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.view")
):
    """Autocomplete pour les postes de travail."""
    items = service.autocomplete_workcenter(prefix, field, limit)
    return {"items": items}


@router.get("/workcenters/{id}", response_model=WorkcenterResponse)
async def get_workcenter(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.view")
):
    """Récupère un poste de travail par ID."""
    try:
        return service.get_workcenter(id)
    except WorkcenterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/workcenters", response_model=WorkcenterResponse, status_code=201)
async def create_workcenter(
    data: WorkcenterCreate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.create")
):
    """Crée un nouveau poste de travail."""
    try:
        return service.create_workcenter(data)
    except WorkcenterDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/workcenters/{id}", response_model=WorkcenterResponse)
async def update_workcenter(
    id: UUID,
    data: WorkcenterUpdate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.edit")
):
    """Met à jour un poste de travail."""
    try:
        return service.update_workcenter(id, data)
    except WorkcenterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/workcenters/{id}", status_code=204)
async def delete_workcenter(
    id: UUID,
    hard: bool = Query(False),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.delete")
):
    """Supprime un poste de travail."""
    try:
        service.delete_workcenter(id, hard)
    except WorkcenterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkcenterValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workcenters/{id}/state", response_model=WorkcenterResponse)
async def set_workcenter_state(
    id: UUID,
    state: WorkcenterState = Query(...),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workcenter.edit")
):
    """Change l'état d'un poste de travail."""
    try:
        return service.set_workcenter_state(id, state)
    except WorkcenterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Routing Routes
# ============================================================================

@router.get("/routings", response_model=RoutingListResponse)
async def list_routings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("code"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.routing.view")
):
    """Liste paginée des gammes opératoires."""
    items, total, pages = service.list_routings(
        page, page_size, sort_by, sort_dir, product_id, is_active
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get("/routings/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_routings(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.routing.view")
):
    """Autocomplete pour les gammes opératoires."""
    items = service.autocomplete_routing(prefix, limit)
    return {"items": items}


@router.get("/routings/{id}", response_model=RoutingResponse)
async def get_routing(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.routing.view")
):
    """Récupère une gamme opératoire par ID."""
    try:
        return service.get_routing(id)
    except RoutingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/routings", response_model=RoutingResponse, status_code=201)
async def create_routing(
    data: RoutingCreate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.routing.create")
):
    """Crée une nouvelle gamme opératoire."""
    try:
        return service.create_routing(data)
    except RoutingDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/routings/{id}", response_model=RoutingResponse)
async def update_routing(
    id: UUID,
    data: RoutingUpdate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.routing.edit")
):
    """Met à jour une gamme opératoire."""
    try:
        return service.update_routing(id, data)
    except RoutingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/routings/{id}", status_code=204)
async def delete_routing(
    id: UUID,
    hard: bool = Query(False),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.routing.delete")
):
    """Supprime une gamme opératoire."""
    try:
        service.delete_routing(id, hard)
    except RoutingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Routing Operations
@router.post("/routings/{routing_id}/operations", response_model=OperationResponse, status_code=201)
async def add_routing_operation(
    routing_id: UUID,
    data: OperationCreate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.routing.edit")
):
    """Ajoute une opération à une gamme."""
    try:
        return service.add_operation(routing_id, data)
    except RoutingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkcenterNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Work Order Routes
# ============================================================================

@router.get("/work-orders", response_model=WorkOrderListResponse)
async def list_work_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[WorkOrderStatus]] = Query(None),
    product_id: Optional[UUID] = Query(None),
    planned_start_from: Optional[date] = Query(None),
    planned_start_to: Optional[date] = Query(None),
    priority_min: Optional[int] = Query(None, ge=0, le=10),
    priority_max: Optional[int] = Query(None, ge=0, le=10),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.view")
):
    """Liste paginée des ordres de fabrication."""
    filters = WorkOrderFilters(
        search=search,
        status=status,
        product_id=product_id,
        planned_start_from=planned_start_from,
        planned_start_to=planned_start_to,
        priority_min=priority_min,
        priority_max=priority_max
    )
    items, total, pages = service.list_work_orders(filters, page, page_size, sort_by, sort_dir)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get("/work-orders/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_work_orders(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.view")
):
    """Autocomplete pour les ordres de fabrication."""
    items = service.autocomplete_work_order(prefix, limit)
    return {"items": items}


@router.get("/work-orders/{id}", response_model=WorkOrderResponse)
async def get_work_order(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.view")
):
    """Récupère un ordre de fabrication par ID."""
    try:
        return service.get_work_order(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/work-orders", response_model=WorkOrderResponse, status_code=201)
async def create_work_order(
    data: WorkOrderCreate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.create")
):
    """Crée un nouvel ordre de fabrication."""
    try:
        return service.create_work_order(data)
    except BOMNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RoutingNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/work-orders/{id}", response_model=WorkOrderResponse)
async def update_work_order(
    id: UUID,
    data: WorkOrderUpdate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Met à jour un ordre de fabrication."""
    try:
        return service.update_work_order(id, data)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/work-orders/{id}", status_code=204)
async def delete_work_order(
    id: UUID,
    hard: bool = Query(False),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.delete")
):
    """Supprime un ordre de fabrication."""
    try:
        service.delete_work_order(id, hard)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Work Order State Transitions
@router.post("/work-orders/{id}/confirm", response_model=WorkOrderResponse)
async def confirm_work_order(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Confirme un ordre de fabrication."""
    try:
        return service.confirm_work_order(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/work-orders/{id}/start", response_model=WorkOrderResponse)
async def start_work_order(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Démarre un ordre de fabrication."""
    try:
        return service.start_work_order(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/work-orders/{id}/pause", response_model=WorkOrderResponse)
async def pause_work_order(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Met en pause un ordre de fabrication."""
    try:
        return service.pause_work_order(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/work-orders/{id}/resume", response_model=WorkOrderResponse)
async def resume_work_order(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Reprend un ordre de fabrication en pause."""
    try:
        return service.resume_work_order(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/work-orders/{id}/complete", response_model=WorkOrderResponse)
async def complete_work_order(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Termine un ordre de fabrication."""
    try:
        return service.complete_work_order(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/work-orders/{id}/cancel", response_model=WorkOrderResponse)
async def cancel_work_order(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Annule un ordre de fabrication."""
    try:
        return service.cancel_work_order(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Production Recording
@router.post("/work-orders/{id}/record-production", response_model=WorkOrderResponse)
async def record_production(
    id: UUID,
    data: RecordProductionRequest,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Enregistre une production sur un OF."""
    try:
        return service.record_production(
            id,
            data.quantity_produced,
            data.quantity_scrapped,
            data.operator_id
        )
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Work Order Operations
@router.post("/work-orders/{wo_id}/operations/{op_id}/start", response_model=WorkOrderOperationResponse)
async def start_work_order_operation(
    wo_id: UUID,
    op_id: UUID,
    data: StartOperationRequest,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Démarre une opération d'OF."""
    try:
        return service.start_operation(
            wo_id, op_id, data.operator_id, data.operator_name
        )
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderOperationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderOperationStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/work-orders/{wo_id}/operations/{op_id}/complete", response_model=WorkOrderOperationResponse)
async def complete_work_order_operation(
    wo_id: UUID,
    op_id: UUID,
    data: CompleteOperationRequest,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.edit")
):
    """Termine une opération d'OF."""
    try:
        return service.complete_operation(
            wo_id, op_id, data.quantity_produced, data.quantity_scrapped
        )
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderOperationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkOrderOperationStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Production Logs
@router.get("/work-orders/{id}/logs", response_model=List[ProductionLogResponse])
async def list_production_logs(
    id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.view")
):
    """Liste les logs de production d'un OF."""
    try:
        return service.list_production_logs(id)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Quality Check Routes
# ============================================================================

@router.post("/quality-checks", response_model=QualityCheckResponse, status_code=201)
async def create_quality_check(
    data: QualityCheckCreate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.quality.create")
):
    """Crée un contrôle qualité."""
    try:
        return service.create_quality_check(data)
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/quality-checks/{id}", response_model=QualityCheckResponse)
async def record_quality_result(
    id: UUID,
    data: QualityCheckUpdate,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.quality.edit")
):
    """Enregistre le résultat d'un contrôle qualité."""
    try:
        return service.record_quality_result(id, data)
    except QualityCheckNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except QualityCheckValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/work-orders/{wo_id}/quality-checks", response_model=List[QualityCheckResponse])
async def list_quality_checks(
    wo_id: UUID,
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.quality.view")
):
    """Liste les contrôles qualité d'un OF."""
    return service.list_quality_checks_for_work_order(wo_id)


# ============================================================================
# Statistics Routes
# ============================================================================

@router.get("/stats/boms", response_model=dict)
async def get_bom_stats(
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.bom.view")
):
    """Statistiques des nomenclatures."""
    return service.get_bom_stats()


@router.get("/stats/work-orders", response_model=dict)
async def get_work_order_stats(
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.view")
):
    """Statistiques des ordres de fabrication."""
    return service.get_work_order_stats()


@router.get("/stats/production", response_model=ProductionStats)
async def get_production_stats(
    period_start: date = Query(...),
    period_end: date = Query(...),
    service: ManufacturingService = Depends(get_service),
    _: None = require_permission("manufacturing.workorder.view")
):
    """Statistiques de production sur une période."""
    if period_end < period_start:
        raise HTTPException(status_code=400, detail="period_end must be after period_start")
    return service.get_production_stats(period_start, period_end)
