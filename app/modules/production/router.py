"""
AZALS MODULE M6 - Routes Production
====================================

API REST pour la gestion de production.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.models import User

from .models import BOMStatus, MOPriority, MOStatus, WorkCenterStatus
from .schemas import (
    BOMCreate,
    BOMLineCreate,
    BOMLineResponse,
    BOMList,
    BOMResponse,
    BOMUpdate,
    CompleteWorkOrderRequest,
    ConsumeRequest,
    ConsumptionResponse,
    # Maintenance
    MaintenanceScheduleCreate,
    MaintenanceScheduleResponse,
    # Manufacturing Orders
    MOCreate,
    MOList,
    MOResponse,
    MOUpdate,
    OutputResponse,
    # Planning
    PlanCreate,
    PlanResponse,
    # Production
    ProduceRequest,
    # Dashboard
    ProductionDashboard,
    ReturnRequest,
    # Routing
    RoutingCreate,
    RoutingResponse,
    # Scrap
    ScrapCreate,
    ScrapResponse,
    StartWorkOrderRequest,
    # Work Centers
    WorkCenterCreate,
    WorkCenterResponse,
    WorkCenterUpdate,
    # Work Orders
    WorkOrderResponse,
)
from .service import get_production_service

router = APIRouter(prefix="/production", tags=["Production (M6)"])


# ============================================================================
# CENTRES DE TRAVAIL
# ============================================================================

@router.post("/work-centers", response_model=WorkCenterResponse, status_code=status.HTTP_201_CREATED)
async def create_work_center(
    data: WorkCenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un centre de travail."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    return service.create_work_center(data)


@router.get("/work-centers", response_model=list[WorkCenterResponse])
async def list_work_centers(
    status: WorkCenterStatus | None = None,
    type: str | None = Query(None, alias="type"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les centres de travail."""
    service = get_production_service(db, current_user.tenant_id)
    items, _ = service.list_work_centers(status=status, type_filter=type, skip=skip, limit=limit)
    return items


@router.get("/work-centers/{wc_id}", response_model=WorkCenterResponse)
async def get_work_center(
    wc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un centre de travail."""
    service = get_production_service(db, current_user.tenant_id)
    wc = service.get_work_center(wc_id)
    if not wc:
        raise HTTPException(status_code=404, detail="Centre de travail non trouvé")
    return wc


@router.put("/work-centers/{wc_id}", response_model=WorkCenterResponse)
async def update_work_center(
    wc_id: UUID,
    data: WorkCenterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un centre de travail."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    wc = service.update_work_center(wc_id, data)
    if not wc:
        raise HTTPException(status_code=404, detail="Centre de travail non trouvé")
    return wc


@router.post("/work-centers/{wc_id}/status/{status}", response_model=WorkCenterResponse)
async def set_work_center_status(
    wc_id: UUID,
    status: WorkCenterStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Changer le statut d'un centre de travail."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    wc = service.set_work_center_status(wc_id, status)
    if not wc:
        raise HTTPException(status_code=404, detail="Centre de travail non trouvé")
    return wc


@router.get("/work-centers/{wc_id}/work-orders", response_model=list[WorkOrderResponse])
async def list_work_orders_for_work_center(
    wc_id: UUID,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les ordres de travail d'un centre."""
    service = get_production_service(db, current_user.tenant_id)
    from .models import WorkOrderStatus as WOStatus
    wo_status = WOStatus(status) if status else None
    return service.list_work_orders_for_work_center(wc_id, status=wo_status)


# ============================================================================
# NOMENCLATURES (BOM)
# ============================================================================

@router.post("/bom", response_model=BOMResponse, status_code=status.HTTP_201_CREATED)
async def create_bom(
    data: BOMCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nomenclature."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    return service.create_bom(data)


@router.get("/bom", response_model=BOMList)
async def list_boms(
    product_id: UUID | None = None,
    status: BOMStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les nomenclatures."""
    service = get_production_service(db, current_user.tenant_id)
    items, total = service.list_boms(product_id=product_id, status=status, skip=skip, limit=limit)
    return BOMList(items=items, total=total)


@router.get("/bom/{bom_id}", response_model=BOMResponse)
async def get_bom(
    bom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une nomenclature."""
    service = get_production_service(db, current_user.tenant_id)
    bom = service.get_bom(bom_id)
    if not bom:
        raise HTTPException(status_code=404, detail="Nomenclature non trouvée")
    return bom


@router.get("/bom/product/{product_id}", response_model=BOMResponse)
async def get_bom_for_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer la nomenclature par défaut d'un produit."""
    service = get_production_service(db, current_user.tenant_id)
    bom = service.get_bom_for_product(product_id)
    if not bom:
        raise HTTPException(status_code=404, detail="Aucune nomenclature par défaut pour ce produit")
    return bom


@router.put("/bom/{bom_id}", response_model=BOMResponse)
async def update_bom(
    bom_id: UUID,
    data: BOMUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une nomenclature."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    bom = service.update_bom(bom_id, data)
    if not bom:
        raise HTTPException(status_code=404, detail="Nomenclature non trouvée")
    return bom


@router.post("/bom/{bom_id}/activate", response_model=BOMResponse)
async def activate_bom(
    bom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activer une nomenclature."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    bom = service.activate_bom(bom_id)
    if not bom:
        raise HTTPException(status_code=404, detail="Nomenclature non trouvée")
    return bom


@router.post("/bom/{bom_id}/lines", response_model=BOMLineResponse, status_code=status.HTTP_201_CREATED)
async def add_bom_line(
    bom_id: UUID,
    data: BOMLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une ligne à une nomenclature."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    line = service.add_bom_line(bom_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Nomenclature non trouvée")
    return line


# ============================================================================
# GAMMES DE FABRICATION
# ============================================================================

@router.post("/routings", response_model=RoutingResponse, status_code=status.HTTP_201_CREATED)
async def create_routing(
    data: RoutingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une gamme de fabrication."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    return service.create_routing(data)


@router.get("/routings", response_model=list[RoutingResponse])
async def list_routings(
    product_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les gammes de fabrication."""
    service = get_production_service(db, current_user.tenant_id)
    items, _ = service.list_routings(product_id=product_id, skip=skip, limit=limit)
    return items


@router.get("/routings/{routing_id}", response_model=RoutingResponse)
async def get_routing(
    routing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une gamme de fabrication."""
    service = get_production_service(db, current_user.tenant_id)
    routing = service.get_routing(routing_id)
    if not routing:
        raise HTTPException(status_code=404, detail="Gamme non trouvée")
    return routing


# ============================================================================
# ORDRES DE FABRICATION
# ============================================================================

@router.post("/orders", response_model=MOResponse, status_code=status.HTTP_201_CREATED)
async def create_manufacturing_order(
    data: MOCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un ordre de fabrication."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    return service.create_manufacturing_order(data)


@router.get("/orders", response_model=MOList)
async def list_manufacturing_orders(
    status: MOStatus | None = None,
    priority: MOPriority | None = None,
    product_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les ordres de fabrication."""
    service = get_production_service(db, current_user.tenant_id)
    items, total = service.list_manufacturing_orders(
        status=status, priority=priority, product_id=product_id,
        date_from=date_from, date_to=date_to, skip=skip, limit=limit
    )
    return MOList(items=items, total=total)


@router.get("/orders/{mo_id}", response_model=MOResponse)
async def get_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un ordre de fabrication."""
    service = get_production_service(db, current_user.tenant_id)
    mo = service.get_manufacturing_order(mo_id)
    if not mo:
        raise HTTPException(status_code=404, detail="Ordre de fabrication non trouvé")
    return mo


@router.put("/orders/{mo_id}", response_model=MOResponse)
async def update_manufacturing_order(
    mo_id: UUID,
    data: MOUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un ordre de fabrication."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    mo = service.update_manufacturing_order(mo_id, data)
    if not mo:
        raise HTTPException(status_code=404, detail="Ordre de fabrication non trouvé ou non modifiable")
    return mo


@router.post("/orders/{mo_id}/confirm", response_model=MOResponse)
async def confirm_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirmer un ordre de fabrication."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    mo = service.confirm_manufacturing_order(mo_id)
    if not mo:
        raise HTTPException(status_code=400, detail="Impossible de confirmer l'OF")
    return mo


@router.post("/orders/{mo_id}/start", response_model=MOResponse)
async def start_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Démarrer un ordre de fabrication."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    mo = service.start_manufacturing_order(mo_id)
    if not mo:
        raise HTTPException(status_code=400, detail="Impossible de démarrer l'OF")
    return mo


@router.post("/orders/{mo_id}/complete", response_model=MOResponse)
async def complete_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminer un ordre de fabrication."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    mo = service.complete_manufacturing_order(mo_id)
    if not mo:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'OF")
    return mo


@router.post("/orders/{mo_id}/cancel", response_model=MOResponse)
async def cancel_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler un ordre de fabrication."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    mo = service.cancel_manufacturing_order(mo_id)
    if not mo:
        raise HTTPException(status_code=400, detail="Impossible d'annuler l'OF")
    return mo


# ============================================================================
# ORDRES DE TRAVAIL
# ============================================================================

@router.get("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def get_work_order(
    wo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un ordre de travail."""
    service = get_production_service(db, current_user.tenant_id)
    wo = service.get_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
    return wo


@router.post("/work-orders/{wo_id}/start", response_model=WorkOrderResponse)
async def start_work_order(
    wo_id: UUID,
    data: StartWorkOrderRequest = StartWorkOrderRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Démarrer un ordre de travail."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    wo = service.start_work_order(wo_id, data)
    if not wo:
        raise HTTPException(status_code=400, detail="Impossible de démarrer l'ordre de travail")
    return wo


@router.post("/work-orders/{wo_id}/complete", response_model=WorkOrderResponse)
async def complete_work_order(
    wo_id: UUID,
    data: CompleteWorkOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminer un ordre de travail."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    wo = service.complete_work_order(wo_id, data)
    if not wo:
        raise HTTPException(status_code=400, detail="Impossible de terminer l'ordre de travail")
    return wo


@router.post("/work-orders/{wo_id}/pause", response_model=WorkOrderResponse)
async def pause_work_order(
    wo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre en pause un ordre de travail."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    wo = service.pause_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=400, detail="Impossible de mettre en pause l'ordre de travail")
    return wo


@router.post("/work-orders/{wo_id}/resume", response_model=WorkOrderResponse)
async def resume_work_order(
    wo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reprendre un ordre de travail."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    wo = service.resume_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=400, detail="Impossible de reprendre l'ordre de travail")
    return wo


# ============================================================================
# CONSOMMATION
# ============================================================================

@router.post("/orders/{mo_id}/consume", response_model=ConsumptionResponse, status_code=status.HTTP_201_CREATED)
async def consume_material(
    mo_id: UUID,
    data: ConsumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consommer des matières."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    consumption = service.consume_material(mo_id, data)
    if not consumption:
        raise HTTPException(status_code=400, detail="Impossible de consommer les matières")
    return consumption


@router.post("/consumptions/return", response_model=ConsumptionResponse)
async def return_material(
    data: ReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retourner des matières non utilisées."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    consumption = service.return_material(data)
    if not consumption:
        raise HTTPException(status_code=404, detail="Consommation non trouvée")
    return consumption


# ============================================================================
# PRODUCTION
# ============================================================================

@router.post("/orders/{mo_id}/produce", response_model=OutputResponse, status_code=status.HTTP_201_CREATED)
async def produce(
    mo_id: UUID,
    data: ProduceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Déclarer une production."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    output = service.produce(mo_id, data)
    if not output:
        raise HTTPException(status_code=400, detail="Impossible de déclarer la production")
    return output


# ============================================================================
# REBUTS
# ============================================================================

@router.post("/scraps", response_model=ScrapResponse, status_code=status.HTTP_201_CREATED)
async def create_scrap(
    data: ScrapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Déclarer un rebut."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    return service.create_scrap(data)


@router.get("/scraps", response_model=list[ScrapResponse])
async def list_scraps(
    mo_id: UUID | None = None,
    product_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les rebuts."""
    service = get_production_service(db, current_user.tenant_id)
    items, _ = service.list_scraps(
        mo_id=mo_id, product_id=product_id,
        date_from=date_from, date_to=date_to,
        skip=skip, limit=limit
    )
    return items


# ============================================================================
# PLANIFICATION
# ============================================================================

@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_production_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un plan de production."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    return service.create_production_plan(data)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_production_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un plan de production."""
    service = get_production_service(db, current_user.tenant_id)
    plan = service.get_production_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouvé")
    return plan


# ============================================================================
# MAINTENANCE
# ============================================================================

@router.post("/maintenance", response_model=MaintenanceScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_schedule(
    data: MaintenanceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un calendrier de maintenance."""
    service = get_production_service(db, current_user.tenant_id, current_user.id)
    return service.create_maintenance_schedule(data)


@router.get("/maintenance", response_model=list[MaintenanceScheduleResponse])
async def list_maintenance_schedules(
    work_center_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les calendriers de maintenance."""
    service = get_production_service(db, current_user.tenant_id)
    return service.list_maintenance_schedules(work_center_id=work_center_id)


@router.get("/maintenance/due", response_model=list[MaintenanceScheduleResponse])
async def get_due_maintenance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les maintenances dues."""
    service = get_production_service(db, current_user.tenant_id)
    return service.get_due_maintenance()


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=ProductionDashboard)
async def get_production_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer le dashboard production."""
    service = get_production_service(db, current_user.tenant_id)
    return service.get_dashboard()
