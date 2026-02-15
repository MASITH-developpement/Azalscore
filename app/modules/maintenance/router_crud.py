"""
AZALS MODULE - MAINTENANCE: Router Unifié
==========================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.maintenance.router_unified import router as maintenance_router

    # Double enregistrement pour compatibilité
    app.include_router(maintenance_router, prefix="/v2")
    app.include_router(maintenance_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (35 total):
- Assets (5): CRUD + delete
- Meters (2): create + record reading
- Plans (4): CRUD
- Work Orders (9): CRUD + start/complete + labor + parts
- Failures (4): CRUD
- Spare Parts (4): CRUD
- Part Requests (2): create + list
- Contracts (4): CRUD
- Dashboard (1)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .models import (
    AssetCategory,
    AssetCriticality,
    AssetStatus,
    ContractStatus,
    PartRequestStatus,
    WorkOrderPriority,
    WorkOrderStatus,
)
from .schemas import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    ContractCreate,
    ContractResponse,
    ContractUpdate,
    FailureCreate,
    FailureResponse,
    FailureUpdate,
    MaintenanceDashboard,
    MaintenancePlanCreate,
    MaintenancePlanResponse,
    MaintenancePlanUpdate,
    MeterCreate,
    MeterReadingCreate,
    MeterReadingResponse,
    MeterResponse,
    PaginatedAssetResponse,
    PaginatedContractResponse,
    PaginatedFailureResponse,
    PaginatedMaintenancePlanResponse,
    PaginatedSparePartResponse,
    PaginatedWorkOrderResponse,
    PartRequestCreate,
    PartRequestResponse,
    SparePartCreate,
    SparePartResponse,
    SparePartUpdate,
    WorkOrderComplete,
    WorkOrderCreate,
    WorkOrderLaborCreate,
    WorkOrderLaborResponse,
    WorkOrderPartCreate,
    WorkOrderPartResponse,
    WorkOrderResponse,
    WorkOrderUpdate,
)
from .service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["Maintenance - GMAO"])

# ============================================================================
# SERVICE DEPENDENCY
# ============================================================================

def get_maintenance_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
) -> MaintenanceService:
    """Factory utilisant le contexte unifié."""
    return MaintenanceService(db, int(context.tenant_id), int(context.user_id))

# ============================================================================
# ACTIFS
# ============================================================================

@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: AssetCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Créer un nouvel actif."""
    return service.create_asset(data)

@router.get("/assets", response_model=PaginatedAssetResponse)
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: AssetCategory | None = None,
    asset_status: AssetStatus | None = Query(None, alias="status"),
    criticality: AssetCriticality | None = None,
    search: str | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Lister les actifs avec filtres."""
    assets, total = service.list_assets(skip, limit, category, asset_status, criticality, search)
    return PaginatedAssetResponse(items=assets, total=total, skip=skip, limit=limit)

@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Récupérer un actif par ID."""
    asset = service.get_asset(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actif non trouvé"
        )
    return asset

@router.put("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    data: AssetUpdate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Mettre à jour un actif."""
    asset = service.update_asset(asset_id, data)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actif non trouvé"
        )
    return asset

@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Supprimer un actif (soft delete)."""
    if not service.delete_asset(asset_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actif non trouvé"
        )

# ============================================================================
# COMPTEURS
# ============================================================================

@router.post("/assets/{asset_id}/meters", response_model=MeterResponse, status_code=status.HTTP_201_CREATED)
async def create_meter(
    asset_id: int,
    data: MeterCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Créer un compteur pour un actif."""
    meter = service.create_meter(asset_id, data)
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actif non trouvé"
        )
    return meter

@router.post("/meters/{meter_id}/readings", response_model=MeterReadingResponse, status_code=status.HTTP_201_CREATED)
async def record_meter_reading(
    meter_id: int,
    data: MeterReadingCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Enregistrer un relevé de compteur."""
    reading = service.record_meter_reading(meter_id, data)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compteur non trouvé"
        )
    return reading

# ============================================================================
# PLANS DE MAINTENANCE
# ============================================================================

@router.post("/plans", response_model=MaintenancePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_plan(
    data: MaintenancePlanCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Créer un plan de maintenance."""
    return service.create_maintenance_plan(data)

@router.get("/plans", response_model=PaginatedMaintenancePlanResponse)
async def list_maintenance_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: int | None = None,
    is_active: bool | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Lister les plans de maintenance."""
    plans, total = service.list_maintenance_plans(skip, limit, asset_id, is_active)
    return PaginatedMaintenancePlanResponse(items=plans, total=total, skip=skip, limit=limit)

@router.get("/plans/{plan_id}", response_model=MaintenancePlanResponse)
async def get_maintenance_plan(
    plan_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Récupérer un plan de maintenance."""
    plan = service.get_maintenance_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan non trouvé"
        )
    return plan

@router.put("/plans/{plan_id}", response_model=MaintenancePlanResponse)
async def update_maintenance_plan(
    plan_id: int,
    data: MaintenancePlanUpdate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Mettre à jour un plan de maintenance."""
    plan = service.update_maintenance_plan(plan_id, data)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan non trouvé"
        )
    return plan

# ============================================================================
# ORDRES DE TRAVAIL
# ============================================================================

@router.post("/work-orders", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    data: WorkOrderCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Créer un ordre de travail."""
    return service.create_work_order(data)

@router.get("/work-orders", response_model=PaginatedWorkOrderResponse)
async def list_work_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: int | None = None,
    wo_status: WorkOrderStatus | None = Query(None, alias="status"),
    priority: WorkOrderPriority | None = None,
    assigned_to_id: int | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Lister les ordres de travail."""
    work_orders, total = service.list_work_orders(skip, limit, asset_id, wo_status, priority, assigned_to_id)
    return PaginatedWorkOrderResponse(items=work_orders, total=total, skip=skip, limit=limit)

@router.get("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def get_work_order(
    wo_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Récupérer un ordre de travail."""
    wo = service.get_work_order(wo_id)
    if not wo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordre de travail non trouvé"
        )
    return wo

@router.put("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def update_work_order(
    wo_id: int,
    data: WorkOrderUpdate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Mettre à jour un ordre de travail."""
    wo = service.update_work_order(wo_id, data)
    if not wo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordre de travail non trouvé"
        )
    return wo

@router.post("/work-orders/{wo_id}/start", response_model=WorkOrderResponse)
async def start_work_order(
    wo_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Démarrer un ordre de travail."""
    wo = service.start_work_order(wo_id)
    if not wo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de démarrer cet ordre de travail"
        )
    return wo

@router.post("/work-orders/{wo_id}/complete", response_model=WorkOrderResponse)
async def complete_work_order(
    wo_id: int,
    data: WorkOrderComplete,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Terminer un ordre de travail."""
    wo = service.complete_work_order(wo_id, data)
    if not wo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de terminer cet ordre de travail"
        )
    return wo

@router.post("/work-orders/{wo_id}/labor", response_model=WorkOrderLaborResponse, status_code=status.HTTP_201_CREATED)
async def add_labor_entry(
    wo_id: int,
    data: WorkOrderLaborCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Ajouter une entrée de main d'oeuvre."""
    labor = service.add_labor_entry(wo_id, data)
    if not labor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordre de travail non trouvé"
        )
    return labor

@router.post("/work-orders/{wo_id}/parts", response_model=WorkOrderPartResponse, status_code=status.HTTP_201_CREATED)
async def add_part_used(
    wo_id: int,
    data: WorkOrderPartCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Ajouter une pièce utilisée."""
    part = service.add_part_used(wo_id, data)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ordre de travail non trouvé"
        )
    return part

# ============================================================================
# PANNES
# ============================================================================

@router.post("/failures", response_model=FailureResponse, status_code=status.HTTP_201_CREATED)
async def create_failure(
    data: FailureCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Enregistrer une panne."""
    return service.create_failure(data)

@router.get("/failures", response_model=PaginatedFailureResponse)
async def list_failures(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: int | None = None,
    failure_status: str | None = Query(None, alias="status"),
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Lister les pannes."""
    failures, total = service.list_failures(skip, limit, asset_id, failure_status)
    return PaginatedFailureResponse(items=failures, total=total, skip=skip, limit=limit)

@router.get("/failures/{failure_id}", response_model=FailureResponse)
async def get_failure(
    failure_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Récupérer une panne."""
    failure = service.get_failure(failure_id)
    if not failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panne non trouvée"
        )
    return failure

@router.put("/failures/{failure_id}", response_model=FailureResponse)
async def update_failure(
    failure_id: int,
    data: FailureUpdate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Mettre à jour une panne."""
    failure = service.update_failure(failure_id, data)
    if not failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panne non trouvée"
        )
    return failure

# ============================================================================
# PIÈCES DE RECHANGE
# ============================================================================

@router.post("/spare-parts", response_model=SparePartResponse, status_code=status.HTTP_201_CREATED)
async def create_spare_part(
    data: SparePartCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Créer une pièce de rechange."""
    return service.create_spare_part(data)

@router.get("/spare-parts", response_model=PaginatedSparePartResponse)
async def list_spare_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = None,
    search: str | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Lister les pièces de rechange."""
    parts, total = service.list_spare_parts(skip, limit, category, search)
    return PaginatedSparePartResponse(items=parts, total=total, skip=skip, limit=limit)

@router.get("/spare-parts/{part_id}", response_model=SparePartResponse)
async def get_spare_part(
    part_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Récupérer une pièce de rechange."""
    part = service.get_spare_part(part_id)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pièce non trouvée"
        )
    return part

@router.put("/spare-parts/{part_id}", response_model=SparePartResponse)
async def update_spare_part(
    part_id: int,
    data: SparePartUpdate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Mettre à jour une pièce de rechange."""
    part = service.update_spare_part(part_id, data)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pièce non trouvée"
        )
    return part

# ============================================================================
# DEMANDES DE PIÈCES
# ============================================================================

@router.post("/part-requests", response_model=PartRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_part_request(
    data: PartRequestCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Créer une demande de pièce."""
    return service.create_part_request(data)

@router.get("/part-requests")
async def list_part_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    request_status: PartRequestStatus | None = Query(None, alias="status"),
    work_order_id: int | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Lister les demandes de pièces."""
    requests, total = service.list_part_requests(skip, limit, request_status, work_order_id)
    return {"items": requests, "total": total, "skip": skip, "limit": limit}

# ============================================================================
# CONTRATS
# ============================================================================

@router.post("/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: ContractCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Créer un contrat de maintenance."""
    return service.create_contract(data)

@router.get("/contracts", response_model=PaginatedContractResponse)
async def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    contract_status: ContractStatus | None = Query(None, alias="status"),
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Lister les contrats de maintenance."""
    contracts, total = service.list_contracts(skip, limit, contract_status)
    return PaginatedContractResponse(items=contracts, total=total, skip=skip, limit=limit)

@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Récupérer un contrat."""
    contract = service.get_contract(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrat non trouvé"
        )
    return contract

@router.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Mettre à jour un contrat."""
    contract = service.update_contract(contract_id, data)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrat non trouvé"
        )
    return contract

# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=MaintenanceDashboard)
async def get_dashboard(
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """Obtenir le tableau de bord maintenance."""
    return service.get_dashboard()
