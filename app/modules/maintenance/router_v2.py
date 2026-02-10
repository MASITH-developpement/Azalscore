"""
AZALS MODULE M8 - Router Maintenance API v2 (CORE SaaS)
========================================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id

Endpoints API REST pour la gestion de la maintenance (GMAO) v2.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

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
    # Assets
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    # Contracts
    ContractCreate,
    ContractResponse,
    ContractUpdate,
    # Failures
    FailureCreate,
    FailureResponse,
    FailureUpdate,
    # Dashboard
    MaintenanceDashboard,
    # Plans
    MaintenancePlanCreate,
    MaintenancePlanResponse,
    MaintenancePlanUpdate,
    # Meters
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
    # Spare Parts
    SparePartCreate,
    SparePartResponse,
    SparePartUpdate,
    WorkOrderComplete,
    # Work Orders
    WorkOrderCreate,
    WorkOrderLaborCreate,
    WorkOrderLaborResponse,
    WorkOrderPartCreate,
    WorkOrderPartResponse,
    WorkOrderResponse,
    WorkOrderUpdate,
)
from .service import MaintenanceService

router = APIRouter(prefix="/v2/maintenance", tags=["Maintenance v2 - CORE SaaS"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_maintenance_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> MaintenanceService:
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id et context.user_id avec conversion int."""
    return MaintenanceService(db, int(context.tenant_id), int(context.user_id))


# ============================================================================
# ACTIFS
# ============================================================================

@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: AssetCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Créer un nouvel actif."""
    return service.create_asset(data)


@router.get("/assets", response_model=PaginatedAssetResponse)
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: AssetCategory | None = None,
    status: AssetStatus | None = None,
    criticality: AssetCriticality | None = None,
    search: str | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Lister les actifs avec filtres."""
    assets, total = service.list_assets(skip, limit, category, status, criticality, search)
    return PaginatedAssetResponse(items=assets, total=total, skip=skip, limit=limit)


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Récupérer un actif par ID."""
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
    """✅ MIGRÉ CORE SaaS: Mettre à jour un actif."""
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
    """✅ MIGRÉ CORE SaaS: Supprimer un actif (soft delete)."""
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
    """✅ MIGRÉ CORE SaaS: Créer un compteur pour un actif."""
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
    """✅ MIGRÉ CORE SaaS: Enregistrer un relevé de compteur."""
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
    """✅ MIGRÉ CORE SaaS: Créer un plan de maintenance."""
    return service.create_maintenance_plan(data)


@router.get("/plans", response_model=PaginatedMaintenancePlanResponse)
async def list_maintenance_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: int | None = None,
    is_active: bool | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Lister les plans de maintenance."""
    plans, total = service.list_maintenance_plans(skip, limit, asset_id, is_active)
    return PaginatedMaintenancePlanResponse(items=plans, total=total, skip=skip, limit=limit)


@router.get("/plans/{plan_id}", response_model=MaintenancePlanResponse)
async def get_maintenance_plan(
    plan_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Récupérer un plan de maintenance."""
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
    """✅ MIGRÉ CORE SaaS: Mettre à jour un plan de maintenance."""
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
    """✅ MIGRÉ CORE SaaS: Créer un ordre de travail."""
    return service.create_work_order(data)


@router.get("/work-orders", response_model=PaginatedWorkOrderResponse)
async def list_work_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: int | None = None,
    status: WorkOrderStatus | None = None,
    priority: WorkOrderPriority | None = None,
    assigned_to_id: int | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Lister les ordres de travail."""
    work_orders, total = service.list_work_orders(skip, limit, asset_id, status, priority, assigned_to_id)
    return PaginatedWorkOrderResponse(items=work_orders, total=total, skip=skip, limit=limit)


@router.get("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def get_work_order(
    wo_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Récupérer un ordre de travail."""
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
    """✅ MIGRÉ CORE SaaS: Mettre à jour un ordre de travail."""
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
    """✅ MIGRÉ CORE SaaS: Démarrer un ordre de travail."""
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
    """✅ MIGRÉ CORE SaaS: Terminer un ordre de travail."""
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
    """✅ MIGRÉ CORE SaaS: Ajouter une entrée de main d'œuvre."""
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
    """✅ MIGRÉ CORE SaaS: Ajouter une pièce utilisée."""
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
    """✅ MIGRÉ CORE SaaS: Enregistrer une panne."""
    return service.create_failure(data)


@router.get("/failures", response_model=PaginatedFailureResponse)
async def list_failures(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    asset_id: int | None = None,
    status: str | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Lister les pannes."""
    failures, total = service.list_failures(skip, limit, asset_id, status)
    return PaginatedFailureResponse(items=failures, total=total, skip=skip, limit=limit)


@router.get("/failures/{failure_id}", response_model=FailureResponse)
async def get_failure(
    failure_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Récupérer une panne."""
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
    """✅ MIGRÉ CORE SaaS: Mettre à jour une panne."""
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
    """✅ MIGRÉ CORE SaaS: Créer une pièce de rechange."""
    return service.create_spare_part(data)


@router.get("/spare-parts", response_model=PaginatedSparePartResponse)
async def list_spare_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = None,
    search: str | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Lister les pièces de rechange."""
    parts, total = service.list_spare_parts(skip, limit, category, search)
    return PaginatedSparePartResponse(items=parts, total=total, skip=skip, limit=limit)


@router.get("/spare-parts/{part_id}", response_model=SparePartResponse)
async def get_spare_part(
    part_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Récupérer une pièce de rechange."""
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
    """✅ MIGRÉ CORE SaaS: Mettre à jour une pièce de rechange."""
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
    """✅ MIGRÉ CORE SaaS: Créer une demande de pièce."""
    return service.create_part_request(data)


@router.get("/part-requests")
async def list_part_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: PartRequestStatus | None = None,
    work_order_id: int | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Lister les demandes de pièces."""
    requests, total = service.list_part_requests(skip, limit, status, work_order_id)
    return {"items": requests, "total": total, "skip": skip, "limit": limit}


# ============================================================================
# CONTRATS
# ============================================================================

@router.post("/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: ContractCreate,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Créer un contrat de maintenance."""
    return service.create_contract(data)


@router.get("/contracts", response_model=PaginatedContractResponse)
async def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: ContractStatus | None = None,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Lister les contrats de maintenance."""
    contracts, total = service.list_contracts(skip, limit, status)
    return PaginatedContractResponse(items=contracts, total=total, skip=skip, limit=limit)


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    service: MaintenanceService = Depends(get_maintenance_service)
):
    """✅ MIGRÉ CORE SaaS: Récupérer un contrat."""
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
    """✅ MIGRÉ CORE SaaS: Mettre à jour un contrat."""
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
    """✅ MIGRÉ CORE SaaS: Obtenir le tableau de bord maintenance."""
    return service.get_dashboard()
