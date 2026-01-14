"""
AZALS MODULE M8 - Router Maintenance (GMAO)
============================================

Endpoints API REST pour la gestion de la maintenance.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from .service import get_maintenance_service
from .models import (
    AssetCategory, AssetStatus, AssetCriticality,
    WorkOrderStatus, WorkOrderPriority, PartRequestStatus, ContractStatus
)
from .schemas import (
    # Assets
    AssetCreate, AssetUpdate, AssetResponse, PaginatedAssetResponse,
    # Meters
    MeterCreate, MeterResponse, MeterReadingCreate, MeterReadingResponse,
    # Plans
    MaintenancePlanCreate, MaintenancePlanUpdate, MaintenancePlanResponse,
    PaginatedMaintenancePlanResponse,
    # Work Orders
    WorkOrderCreate, WorkOrderUpdate, WorkOrderComplete, WorkOrderResponse,
    PaginatedWorkOrderResponse, WorkOrderLaborCreate, WorkOrderLaborResponse,
    WorkOrderPartCreate, WorkOrderPartResponse,
    # Failures
    FailureCreate, FailureUpdate, FailureResponse, PaginatedFailureResponse,
    # Spare Parts
    SparePartCreate, SparePartUpdate, SparePartResponse, PaginatedSparePartResponse,
    PartRequestCreate, PartRequestResponse,
    # Contracts
    ContractCreate, ContractUpdate, ContractResponse, PaginatedContractResponse,
    # Dashboard
    MaintenanceDashboard
)


router = APIRouter(prefix="/maintenance", tags=["Maintenance (GMAO)"])


# ============================================================================
# ACTIFS
# ============================================================================

@router.post("/assets", response_model=AssetResponse, status_code=201)
async def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouvel actif."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.create_asset(data)


@router.get("/assets", response_model=PaginatedAssetResponse)
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: Optional[AssetCategory] = None,
    status: Optional[AssetStatus] = None,
    criticality: Optional[AssetCriticality] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les actifs avec filtres."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    assets, total = service.list_assets(skip, limit, category, status, criticality, search)
    return PaginatedAssetResponse(items=assets, total=total, skip=skip, limit=limit)


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un actif par ID."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    asset = service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Actif non trouvé")
    return asset


@router.put("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un actif."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    asset = service.update_asset(asset_id, data)
    if not asset:
        raise HTTPException(status_code=404, detail="Actif non trouvé")
    return asset


@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un actif (soft delete)."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    if not service.delete_asset(asset_id):
        raise HTTPException(status_code=404, detail="Actif non trouvé")


# ============================================================================
# COMPTEURS
# ============================================================================

@router.post("/assets/{asset_id}/meters", response_model=MeterResponse, status_code=201)
async def create_meter(
    asset_id: int,
    data: MeterCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un compteur pour un actif."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    meter = service.create_meter(asset_id, data)
    if not meter:
        raise HTTPException(status_code=404, detail="Actif non trouvé")
    return meter


@router.post("/meters/{meter_id}/readings", response_model=MeterReadingResponse, status_code=201)
async def record_meter_reading(
    meter_id: int,
    data: MeterReadingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Enregistrer un relevé de compteur."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    reading = service.record_meter_reading(meter_id, data)
    if not reading:
        raise HTTPException(status_code=404, detail="Compteur non trouvé")
    return reading


# ============================================================================
# PLANS DE MAINTENANCE
# ============================================================================

@router.post("/plans", response_model=MaintenancePlanResponse, status_code=201)
async def create_maintenance_plan(
    data: MaintenancePlanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un plan de maintenance."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.create_maintenance_plan(data)


@router.get("/plans", response_model=PaginatedMaintenancePlanResponse)
async def list_maintenance_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les plans de maintenance."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    plans, total = service.list_maintenance_plans(skip, limit, asset_id, is_active)
    return PaginatedMaintenancePlanResponse(items=plans, total=total, skip=skip, limit=limit)


@router.get("/plans/{plan_id}", response_model=MaintenancePlanResponse)
async def get_maintenance_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un plan de maintenance."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    plan = service.get_maintenance_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouvé")
    return plan


@router.put("/plans/{plan_id}", response_model=MaintenancePlanResponse)
async def update_maintenance_plan(
    plan_id: int,
    data: MaintenancePlanUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un plan de maintenance."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    plan = service.update_maintenance_plan(plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouvé")
    return plan


# ============================================================================
# ORDRES DE TRAVAIL
# ============================================================================

@router.post("/work-orders", response_model=WorkOrderResponse, status_code=201)
async def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un ordre de travail."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.create_work_order(data)


@router.get("/work-orders", response_model=PaginatedWorkOrderResponse)
async def list_work_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: Optional[int] = None,
    status: Optional[WorkOrderStatus] = None,
    priority: Optional[WorkOrderPriority] = None,
    assigned_to_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les ordres de travail."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    work_orders, total = service.list_work_orders(skip, limit, asset_id, status, priority, assigned_to_id)
    return PaginatedWorkOrderResponse(items=work_orders, total=total, skip=skip, limit=limit)


@router.get("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def get_work_order(
    wo_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un ordre de travail."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    wo = service.get_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
    return wo


@router.put("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def update_work_order(
    wo_id: int,
    data: WorkOrderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un ordre de travail."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    wo = service.update_work_order(wo_id, data)
    if not wo:
        raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
    return wo


@router.post("/work-orders/{wo_id}/start", response_model=WorkOrderResponse)
async def start_work_order(
    wo_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Démarrer un ordre de travail."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    wo = service.start_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=400, detail="Impossible de démarrer cet ordre de travail")
    return wo


@router.post("/work-orders/{wo_id}/complete", response_model=WorkOrderResponse)
async def complete_work_order(
    wo_id: int,
    data: WorkOrderComplete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Terminer un ordre de travail."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    wo = service.complete_work_order(wo_id, data)
    if not wo:
        raise HTTPException(status_code=400, detail="Impossible de terminer cet ordre de travail")
    return wo


@router.post("/work-orders/{wo_id}/labor", response_model=WorkOrderLaborResponse, status_code=201)
async def add_labor_entry(
    wo_id: int,
    data: WorkOrderLaborCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Ajouter une entrée de main d'œuvre."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    labor = service.add_labor_entry(wo_id, data)
    if not labor:
        raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
    return labor


@router.post("/work-orders/{wo_id}/parts", response_model=WorkOrderPartResponse, status_code=201)
async def add_part_used(
    wo_id: int,
    data: WorkOrderPartCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Ajouter une pièce utilisée."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    part = service.add_part_used(wo_id, data)
    if not part:
        raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
    return part


# ============================================================================
# PANNES
# ============================================================================

@router.post("/failures", response_model=FailureResponse, status_code=201)
async def create_failure(
    data: FailureCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Enregistrer une panne."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.create_failure(data)


@router.get("/failures", response_model=PaginatedFailureResponse)
async def list_failures(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les pannes."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    failures, total = service.list_failures(skip, limit, asset_id, status)
    return PaginatedFailureResponse(items=failures, total=total, skip=skip, limit=limit)


@router.get("/failures/{failure_id}", response_model=FailureResponse)
async def get_failure(
    failure_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer une panne."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    failure = service.get_failure(failure_id)
    if not failure:
        raise HTTPException(status_code=404, detail="Panne non trouvée")
    return failure


@router.put("/failures/{failure_id}", response_model=FailureResponse)
async def update_failure(
    failure_id: int,
    data: FailureUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une panne."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    failure = service.update_failure(failure_id, data)
    if not failure:
        raise HTTPException(status_code=404, detail="Panne non trouvée")
    return failure


# ============================================================================
# PIÈCES DE RECHANGE
# ============================================================================

@router.post("/spare-parts", response_model=SparePartResponse, status_code=201)
async def create_spare_part(
    data: SparePartCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer une pièce de rechange."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.create_spare_part(data)


@router.get("/spare-parts", response_model=PaginatedSparePartResponse)
async def list_spare_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les pièces de rechange."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    parts, total = service.list_spare_parts(skip, limit, category, search)
    return PaginatedSparePartResponse(items=parts, total=total, skip=skip, limit=limit)


@router.get("/spare-parts/{part_id}", response_model=SparePartResponse)
async def get_spare_part(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer une pièce de rechange."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    part = service.get_spare_part(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Pièce non trouvée")
    return part


@router.put("/spare-parts/{part_id}", response_model=SparePartResponse)
async def update_spare_part(
    part_id: int,
    data: SparePartUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une pièce de rechange."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    part = service.update_spare_part(part_id, data)
    if not part:
        raise HTTPException(status_code=404, detail="Pièce non trouvée")
    return part


# ============================================================================
# DEMANDES DE PIÈCES
# ============================================================================

@router.post("/part-requests", response_model=PartRequestResponse, status_code=201)
async def create_part_request(
    data: PartRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer une demande de pièce."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.create_part_request(data)


@router.get("/part-requests")
async def list_part_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[PartRequestStatus] = None,
    work_order_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les demandes de pièces."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    requests, total = service.list_part_requests(skip, limit, status, work_order_id)
    return {"items": requests, "total": total, "skip": skip, "limit": limit}


# ============================================================================
# CONTRATS
# ============================================================================

@router.post("/contracts", response_model=ContractResponse, status_code=201)
async def create_contract(
    data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un contrat de maintenance."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.create_contract(data)


@router.get("/contracts", response_model=PaginatedContractResponse)
async def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[ContractStatus] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les contrats de maintenance."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    contracts, total = service.list_contracts(skip, limit, status)
    return PaginatedContractResponse(items=contracts, total=total, skip=skip, limit=limit)


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un contrat."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    contract = service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un contrat."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    contract = service.update_contract(contract_id, data)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=MaintenanceDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtenir le tableau de bord maintenance."""
    service = get_maintenance_service(db, current_user["tenant_id"], current_user["id"])
    return service.get_dashboard()
