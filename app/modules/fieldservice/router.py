"""
Routes API - Module Field Service (GAP-081)

CRUD complet, Autocomplete, Permissions vérifiées.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import WorkOrderStatus, TechnicianStatus, WorkOrderType, Priority
from .repository import (
    WorkOrderRepository, TechnicianRepository,
    CustomerSiteRepository, ServiceZoneRepository
)
from .schemas import (
    WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse, WorkOrderList, WorkOrderFilters,
    TechnicianCreate, TechnicianUpdate, TechnicianResponse, TechnicianList, TechnicianFilters,
    TechnicianLocationUpdate,
    CustomerSiteCreate, CustomerSiteUpdate, CustomerSiteResponse,
    ServiceZoneCreate, ServiceZoneUpdate, ServiceZoneResponse,
    AutocompleteResponse, BulkResult
)

router = APIRouter(prefix="/fieldservice", tags=["Field Service"])


# ============== Helpers ==============

def get_wo_repo(db: Session = Depends(get_db), user=Depends(get_current_user)) -> WorkOrderRepository:
    return WorkOrderRepository(db, user.tenant_id)


def get_tech_repo(db: Session = Depends(get_db), user=Depends(get_current_user)) -> TechnicianRepository:
    return TechnicianRepository(db, user.tenant_id)


def get_site_repo(db: Session = Depends(get_db), user=Depends(get_current_user)) -> CustomerSiteRepository:
    return CustomerSiteRepository(db, user.tenant_id)


def get_zone_repo(db: Session = Depends(get_db), user=Depends(get_current_user)) -> ServiceZoneRepository:
    return ServiceZoneRepository(db, user.tenant_id)


# ============== WORK ORDER ROUTES ==============

@router.get("/work-orders", response_model=WorkOrderList)
async def list_work_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    work_order_type: Optional[List[WorkOrderType]] = Query(None),
    status: Optional[List[WorkOrderStatus]] = Query(None),
    priority: Optional[List[Priority]] = Query(None),
    technician_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    repo: WorkOrderRepository = Depends(get_wo_repo),
    _: None = require_permission("fieldservice.view")
):
    """Liste paginée des ordres de travail."""
    filters = WorkOrderFilters(
        search=search, work_order_type=work_order_type, status=status,
        priority=priority, technician_id=technician_id,
        date_from=date_from, date_to=date_to
    )
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/work-orders/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_work_orders(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    repo: WorkOrderRepository = Depends(get_wo_repo),
    _: None = require_permission("fieldservice.view")
):
    """Autocomplete pour les ordres de travail."""
    items = repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/work-orders/overdue")
async def list_overdue_work_orders(
    repo: WorkOrderRepository = Depends(get_wo_repo),
    _: None = require_permission("fieldservice.view")
):
    """Liste les ordres de travail en retard."""
    return repo.get_overdue()


@router.get("/work-orders/{id}", response_model=WorkOrderResponse)
async def get_work_order(
    id: UUID,
    repo: WorkOrderRepository = Depends(get_wo_repo),
    _: None = require_permission("fieldservice.view")
):
    """Récupère un ordre de travail."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Work order not found")
    return entity


@router.post("/work-orders", response_model=WorkOrderResponse, status_code=201)
async def create_work_order(
    data: WorkOrderCreate,
    repo: WorkOrderRepository = Depends(get_wo_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.create")
):
    """Crée un ordre de travail."""
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")
    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/work-orders/{id}", response_model=WorkOrderResponse)
async def update_work_order(
    id: UUID,
    data: WorkOrderUpdate,
    repo: WorkOrderRepository = Depends(get_wo_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.edit")
):
    """Met à jour un ordre de travail."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Work order not found")

    if data.code and data.code != entity.code:
        if repo.code_exists(data.code, exclude_id=id):
            raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")

    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.delete("/work-orders/{id}", status_code=204)
async def delete_work_order(
    id: UUID,
    repo: WorkOrderRepository = Depends(get_wo_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.delete")
):
    """Supprime un ordre de travail."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Work order not found")

    can_delete, reason = entity.can_delete()
    if not can_delete:
        raise HTTPException(status_code=400, detail=reason)

    repo.soft_delete(entity, user.id)


@router.post("/work-orders/{id}/dispatch", response_model=WorkOrderResponse)
async def dispatch_work_order(
    id: UUID,
    technician_id: UUID,
    repo: WorkOrderRepository = Depends(get_wo_repo),
    tech_repo: TechnicianRepository = Depends(get_tech_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.dispatch")
):
    """Assigne un technicien et dispatche l'ordre de travail."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Work order not found")

    technician = tech_repo.get_by_id(technician_id)
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")

    if technician.status != TechnicianStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="FSTechnician not available")

    return repo.update(entity, {
        "technician_id": technician_id,
        "status": WorkOrderStatus.DISPATCHED
    }, user.id)


@router.post("/work-orders/{id}/start", response_model=WorkOrderResponse)
async def start_work_order(
    id: UUID,
    repo: WorkOrderRepository = Depends(get_wo_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.edit")
):
    """Démarre un ordre de travail."""
    from datetime import datetime
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Work order not found")

    return repo.update(entity, {
        "status": WorkOrderStatus.IN_PROGRESS,
        "actual_start_time": datetime.utcnow()
    }, user.id)


@router.post("/work-orders/{id}/complete", response_model=WorkOrderResponse)
async def complete_work_order(
    id: UUID,
    resolution_notes: Optional[str] = None,
    repo: WorkOrderRepository = Depends(get_wo_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.edit")
):
    """Termine un ordre de travail."""
    from datetime import datetime
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Work order not found")

    now = datetime.utcnow()
    duration = None
    if entity.actual_start_time:
        duration = int((now - entity.actual_start_time).total_seconds() / 60)

    # Vérifier SLA
    sla_met = None
    if entity.sla_due_date:
        sla_met = now <= entity.sla_due_date

    return repo.update(entity, {
        "status": WorkOrderStatus.COMPLETED,
        "actual_end_time": now,
        "actual_duration_minutes": duration,
        "resolution_notes": resolution_notes,
        "sla_met": sla_met
    }, user.id)


# ============== TECHNICIAN ROUTES ==============

@router.get("/technicians", response_model=TechnicianList)
async def list_technicians(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[TechnicianStatus]] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    repo: TechnicianRepository = Depends(get_tech_repo),
    _: None = require_permission("fieldservice.view")
):
    """Liste paginée des techniciens."""
    filters = TechnicianFilters(search=search, status=status, is_active=is_active)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/technicians/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_technicians(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    repo: TechnicianRepository = Depends(get_tech_repo),
    _: None = require_permission("fieldservice.view")
):
    """Autocomplete pour les techniciens."""
    items = repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/technicians/available")
async def list_available_technicians(
    date_filter: Optional[date] = Query(None),
    repo: TechnicianRepository = Depends(get_tech_repo),
    _: None = require_permission("fieldservice.view")
):
    """Liste les techniciens disponibles."""
    return repo.get_available(date_filter)


@router.get("/technicians/{id}", response_model=TechnicianResponse)
async def get_technician(
    id: UUID,
    repo: TechnicianRepository = Depends(get_tech_repo),
    _: None = require_permission("fieldservice.view")
):
    """Récupère un technicien."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Technician not found")
    return entity


@router.post("/technicians", response_model=TechnicianResponse, status_code=201)
async def create_technician(
    data: TechnicianCreate,
    repo: TechnicianRepository = Depends(get_tech_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.create")
):
    """Crée un technicien."""
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")
    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/technicians/{id}", response_model=TechnicianResponse)
async def update_technician(
    id: UUID,
    data: TechnicianUpdate,
    repo: TechnicianRepository = Depends(get_tech_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.edit")
):
    """Met à jour un technicien."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Technician not found")

    if data.code and data.code != entity.code:
        if repo.code_exists(data.code, exclude_id=id):
            raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")

    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.post("/technicians/{id}/location", response_model=TechnicianResponse)
async def update_technician_location(
    id: UUID,
    data: TechnicianLocationUpdate,
    repo: TechnicianRepository = Depends(get_tech_repo),
    _: None = require_permission("fieldservice.edit")
):
    """Met à jour la position GPS d'un technicien."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Technician not found")
    return repo.update_location(entity, data.latitude, data.longitude)


@router.delete("/technicians/{id}", status_code=204)
async def delete_technician(
    id: UUID,
    repo: TechnicianRepository = Depends(get_tech_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.delete")
):
    """Supprime un technicien."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Technician not found")
    repo.soft_delete(entity, user.id)


# ============== CUSTOMER SITE ROUTES ==============

@router.get("/sites/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_sites(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    repo: CustomerSiteRepository = Depends(get_site_repo),
    _: None = require_permission("fieldservice.view")
):
    """Autocomplete pour les sites clients."""
    items = repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/sites/customer/{customer_id}")
async def list_sites_by_customer(
    customer_id: UUID,
    repo: CustomerSiteRepository = Depends(get_site_repo),
    _: None = require_permission("fieldservice.view")
):
    """Liste les sites d'un client."""
    return repo.get_by_customer(customer_id)


@router.get("/sites/{id}", response_model=CustomerSiteResponse)
async def get_site(
    id: UUID,
    repo: CustomerSiteRepository = Depends(get_site_repo),
    _: None = require_permission("fieldservice.view")
):
    """Récupère un site client."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Site not found")
    return entity


@router.post("/sites", response_model=CustomerSiteResponse, status_code=201)
async def create_site(
    data: CustomerSiteCreate,
    repo: CustomerSiteRepository = Depends(get_site_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.create")
):
    """Crée un site client."""
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")
    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/sites/{id}", response_model=CustomerSiteResponse)
async def update_site(
    id: UUID,
    data: CustomerSiteUpdate,
    repo: CustomerSiteRepository = Depends(get_site_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.edit")
):
    """Met à jour un site client."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Site not found")
    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.delete("/sites/{id}", status_code=204)
async def delete_site(
    id: UUID,
    repo: CustomerSiteRepository = Depends(get_site_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.delete")
):
    """Supprime un site client."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Site not found")
    repo.soft_delete(entity, user.id)


# ============== SERVICE ZONE ROUTES ==============

@router.get("/zones", response_model=List[ServiceZoneResponse])
async def list_zones(
    repo: ServiceZoneRepository = Depends(get_zone_repo),
    _: None = require_permission("fieldservice.view")
):
    """Liste les zones de service actives."""
    return repo.list_active()


@router.get("/zones/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_zones(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    repo: ServiceZoneRepository = Depends(get_zone_repo),
    _: None = require_permission("fieldservice.view")
):
    """Autocomplete pour les zones."""
    items = repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/zones/{id}", response_model=ServiceZoneResponse)
async def get_zone(
    id: UUID,
    repo: ServiceZoneRepository = Depends(get_zone_repo),
    _: None = require_permission("fieldservice.view")
):
    """Récupère une zone de service."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Zone not found")
    return entity


@router.post("/zones", response_model=ServiceZoneResponse, status_code=201)
async def create_zone(
    data: ServiceZoneCreate,
    repo: ServiceZoneRepository = Depends(get_zone_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.create")
):
    """Crée une zone de service."""
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")
    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/zones/{id}", response_model=ServiceZoneResponse)
async def update_zone(
    id: UUID,
    data: ServiceZoneUpdate,
    repo: ServiceZoneRepository = Depends(get_zone_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.edit")
):
    """Met à jour une zone de service."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Zone not found")
    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.delete("/zones/{id}", status_code=204)
async def delete_zone(
    id: UUID,
    repo: ServiceZoneRepository = Depends(get_zone_repo),
    user=Depends(get_current_user),
    _: None = require_permission("fieldservice.delete")
):
    """Supprime une zone de service."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Zone not found")
    repo.soft_delete(entity, user.id)
