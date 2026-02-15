"""
AZALS MODULE - PRODUCTION: Router Unifié
=========================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.production.router_unified import router as production_router

    # Double enregistrement pour compatibilité
    app.include_router(production_router, prefix="/v2")
    app.include_router(production_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (43 total):
- Work Centers (6): CRUD + status + orders
- BOM (7): CRUD + by product + activate + add line
- Routings (3): create + list + get
- Manufacturing Orders (9): CRUD + confirm/start/complete/cancel
- Work Orders (5): get + start/complete/pause/resume
- Consumptions (3): consume + return + produce
- Scraps (2): create + list
- Plans (2): create + get
- Maintenance (3): schedule + list + due
- Dashboard (1)
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

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
    MaintenanceScheduleCreate,
    MaintenanceScheduleResponse,
    MOCreate,
    MOList,
    MOResponse,
    MOUpdate,
    OutputResponse,
    PlanCreate,
    PlanResponse,
    ProduceRequest,
    ProductionDashboard,
    ReturnRequest,
    RoutingCreate,
    RoutingResponse,
    ScrapCreate,
    ScrapResponse,
    StartWorkOrderRequest,
    WorkCenterCreate,
    WorkCenterResponse,
    WorkCenterUpdate,
    WorkOrderResponse,
)
from .service import get_production_service

router = APIRouter(prefix="/production", tags=["Production - Manufacturing"])

# ============================================================================
# CENTRES DE TRAVAIL
# ============================================================================

@router.post("/work-centers", response_model=WorkCenterResponse, status_code=status.HTTP_201_CREATED)
async def create_work_center(
    data: WorkCenterCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un centre de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.create_work_center(data, created_by=context.user_id)

@router.get("/work-centers", response_model=list[WorkCenterResponse])
async def list_work_centers(
    wc_status: WorkCenterStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les centres de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.list_work_centers(status=wc_status)

@router.get("/work-centers/{wc_id}", response_model=WorkCenterResponse)
async def get_work_center(
    wc_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un centre de travail."""
    service = get_production_service(db, context.tenant_id)
    wc = service.get_work_center(wc_id)
    if not wc:
        raise HTTPException(status_code=404, detail="Centre de travail non trouvé")
    return wc

@router.put("/work-centers/{wc_id}", response_model=WorkCenterResponse)
async def update_work_center(
    wc_id: UUID,
    data: WorkCenterUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un centre de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.update_work_center(wc_id, data, updated_by=context.user_id)

@router.post("/work-centers/{wc_id}/status/{wc_status}", response_model=WorkCenterResponse)
async def set_work_center_status(
    wc_id: UUID,
    wc_status: WorkCenterStatus,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Modifier le statut d'un centre de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.set_work_center_status(wc_id, wc_status, context.user_id)

@router.get("/work-centers/{wc_id}/work-orders", response_model=list[WorkOrderResponse])
async def get_work_center_orders(
    wc_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les ordres de travail d'un centre."""
    service = get_production_service(db, context.tenant_id)
    return service.get_work_center_orders(wc_id)

# ============================================================================
# NOMENCLATURES (BOM)
# ============================================================================

@router.post("/bom", response_model=BOMResponse, status_code=status.HTTP_201_CREATED)
async def create_bom(
    data: BOMCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une nomenclature."""
    service = get_production_service(db, context.tenant_id)
    return service.create_bom(data, created_by=context.user_id)

@router.get("/bom", response_model=BOMList)
async def list_boms(
    product_id: UUID | None = None,
    bom_status: BOMStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les nomenclatures."""
    service = get_production_service(db, context.tenant_id)
    boms, total = service.list_boms(
        product_id=product_id,
        status=bom_status,
        page=page,
        page_size=page_size
    )
    return BOMList(boms=boms, total=total, page=page, page_size=page_size)

@router.get("/bom/{bom_id}", response_model=BOMResponse)
async def get_bom(
    bom_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une nomenclature."""
    service = get_production_service(db, context.tenant_id)
    bom = service.get_bom(bom_id)
    if not bom:
        raise HTTPException(status_code=404, detail="Nomenclature non trouvée")
    return bom

@router.get("/bom/product/{product_id}", response_model=BOMResponse)
async def get_bom_by_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer la nomenclature active d'un produit."""
    service = get_production_service(db, context.tenant_id)
    bom = service.get_bom_by_product(product_id)
    if not bom:
        raise HTTPException(status_code=404, detail="Nomenclature active non trouvée")
    return bom

@router.put("/bom/{bom_id}", response_model=BOMResponse)
async def update_bom(
    bom_id: UUID,
    data: BOMUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une nomenclature."""
    service = get_production_service(db, context.tenant_id)
    return service.update_bom(bom_id, data, updated_by=context.user_id)

@router.post("/bom/{bom_id}/activate", response_model=BOMResponse)
async def activate_bom(
    bom_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Activer une nomenclature."""
    service = get_production_service(db, context.tenant_id)
    return service.activate_bom(bom_id, context.user_id)

@router.post("/bom/{bom_id}/lines", response_model=BOMLineResponse, status_code=status.HTTP_201_CREATED)
async def add_bom_line(
    bom_id: UUID,
    data: BOMLineCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Ajouter une ligne à une nomenclature."""
    service = get_production_service(db, context.tenant_id)
    return service.add_bom_line(bom_id, data)

# ============================================================================
# GAMMES (ROUTINGS)
# ============================================================================

@router.post("/routings", response_model=RoutingResponse, status_code=status.HTTP_201_CREATED)
async def create_routing(
    data: RoutingCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une gamme de fabrication."""
    service = get_production_service(db, context.tenant_id)
    return service.create_routing(data, created_by=context.user_id)

@router.get("/routings", response_model=list[RoutingResponse])
async def list_routings(
    product_id: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les gammes."""
    service = get_production_service(db, context.tenant_id)
    return service.list_routings(product_id=product_id)

@router.get("/routings/{routing_id}", response_model=RoutingResponse)
async def get_routing(
    routing_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une gamme."""
    service = get_production_service(db, context.tenant_id)
    routing = service.get_routing(routing_id)
    if not routing:
        raise HTTPException(status_code=404, detail="Gamme non trouvée")
    return routing

# ============================================================================
# ORDRES DE FABRICATION (MO)
# ============================================================================

@router.post("/orders", response_model=MOResponse, status_code=status.HTTP_201_CREATED)
async def create_manufacturing_order(
    data: MOCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un ordre de fabrication."""
    service = get_production_service(db, context.tenant_id)
    return service.create_manufacturing_order(data, created_by=context.user_id)

@router.get("/orders", response_model=MOList)
async def list_manufacturing_orders(
    product_id: UUID | None = None,
    mo_status: MOStatus | None = Query(None, alias="status"),
    priority: MOPriority | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les ordres de fabrication."""
    service = get_production_service(db, context.tenant_id)
    orders, total = service.list_manufacturing_orders(
        product_id=product_id,
        status=mo_status,
        priority=priority,
        page=page,
        page_size=page_size
    )
    return MOList(orders=orders, total=total, page=page, page_size=page_size)

@router.get("/orders/{mo_id}", response_model=MOResponse)
async def get_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un ordre de fabrication."""
    service = get_production_service(db, context.tenant_id)
    mo = service.get_manufacturing_order(mo_id)
    if not mo:
        raise HTTPException(status_code=404, detail="Ordre de fabrication non trouvé")
    return mo

@router.put("/orders/{mo_id}", response_model=MOResponse)
async def update_manufacturing_order(
    mo_id: UUID,
    data: MOUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un ordre de fabrication."""
    service = get_production_service(db, context.tenant_id)
    return service.update_manufacturing_order(mo_id, data, updated_by=context.user_id)

@router.post("/orders/{mo_id}/confirm", response_model=MOResponse)
async def confirm_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Confirmer un ordre de fabrication."""
    service = get_production_service(db, context.tenant_id)
    return service.confirm_manufacturing_order(mo_id, context.user_id)

@router.post("/orders/{mo_id}/start", response_model=MOResponse)
async def start_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer un ordre de fabrication."""
    service = get_production_service(db, context.tenant_id)
    return service.start_manufacturing_order(mo_id, context.user_id)

@router.post("/orders/{mo_id}/complete", response_model=MOResponse)
async def complete_manufacturing_order(
    mo_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Terminer un ordre de fabrication."""
    service = get_production_service(db, context.tenant_id)
    return service.complete_manufacturing_order(mo_id, context.user_id)

@router.post("/orders/{mo_id}/cancel", response_model=MOResponse)
async def cancel_manufacturing_order(
    mo_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Annuler un ordre de fabrication."""
    service = get_production_service(db, context.tenant_id)
    return service.cancel_manufacturing_order(mo_id, reason, context.user_id)

# ============================================================================
# ORDRES DE TRAVAIL (WO)
# ============================================================================

@router.get("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def get_work_order(
    wo_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un ordre de travail."""
    service = get_production_service(db, context.tenant_id)
    wo = service.get_work_order(wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
    return wo

@router.post("/work-orders/{wo_id}/start", response_model=WorkOrderResponse)
async def start_work_order(
    wo_id: UUID,
    data: StartWorkOrderRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer un ordre de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.start_work_order(wo_id, data, context.user_id)

@router.post("/work-orders/{wo_id}/complete", response_model=WorkOrderResponse)
async def complete_work_order(
    wo_id: UUID,
    data: CompleteWorkOrderRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Terminer un ordre de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.complete_work_order(wo_id, data, context.user_id)

@router.post("/work-orders/{wo_id}/pause", response_model=WorkOrderResponse)
async def pause_work_order(
    wo_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre en pause un ordre de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.pause_work_order(wo_id, reason, context.user_id)

@router.post("/work-orders/{wo_id}/resume", response_model=WorkOrderResponse)
async def resume_work_order(
    wo_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Reprendre un ordre de travail."""
    service = get_production_service(db, context.tenant_id)
    return service.resume_work_order(wo_id, context.user_id)

# ============================================================================
# CONSOMMATIONS & PRODUCTION
# ============================================================================

@router.post("/orders/{mo_id}/consume", response_model=ConsumptionResponse, status_code=status.HTTP_201_CREATED)
async def consume_material(
    mo_id: UUID,
    data: ConsumeRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Consommer des matières premières."""
    service = get_production_service(db, context.tenant_id)
    return service.consume_material(mo_id, data, context.user_id)

@router.post("/consumptions/return", response_model=ConsumptionResponse)
async def return_material(
    data: ReturnRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Retourner des matières au stock."""
    service = get_production_service(db, context.tenant_id)
    return service.return_material(data, context.user_id)

@router.post("/orders/{mo_id}/produce", response_model=OutputResponse, status_code=status.HTTP_201_CREATED)
async def record_production(
    mo_id: UUID,
    data: ProduceRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Enregistrer une production."""
    service = get_production_service(db, context.tenant_id)
    return service.record_production(mo_id, data, context.user_id)

# ============================================================================
# REBUTS
# ============================================================================

@router.post("/scraps", response_model=ScrapResponse, status_code=status.HTTP_201_CREATED)
async def record_scrap(
    data: ScrapCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Enregistrer un rebut."""
    service = get_production_service(db, context.tenant_id)
    return service.record_scrap(data, context.user_id)

@router.get("/scraps", response_model=list[ScrapResponse])
async def list_scraps(
    mo_id: UUID | None = None,
    product_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les rebuts."""
    service = get_production_service(db, context.tenant_id)
    return service.list_scraps(
        mo_id=mo_id,
        product_id=product_id,
        from_date=from_date,
        to_date=to_date
    )

# ============================================================================
# PLANIFICATION
# ============================================================================

@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_production_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un plan de production."""
    service = get_production_service(db, context.tenant_id)
    return service.create_production_plan(data, created_by=context.user_id)

@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_production_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un plan de production."""
    service = get_production_service(db, context.tenant_id)
    plan = service.get_production_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de production non trouvé")
    return plan

# ============================================================================
# MAINTENANCE
# ============================================================================

@router.post("/maintenance", response_model=MaintenanceScheduleResponse, status_code=status.HTTP_201_CREATED)
async def schedule_maintenance(
    data: MaintenanceScheduleCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Planifier une maintenance."""
    service = get_production_service(db, context.tenant_id)
    return service.schedule_maintenance(data, created_by=context.user_id)

@router.get("/maintenance", response_model=list[MaintenanceScheduleResponse])
async def list_maintenance_schedules(
    work_center_id: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les maintenances planifiées."""
    service = get_production_service(db, context.tenant_id)
    return service.list_maintenance_schedules(work_center_id=work_center_id)

@router.get("/maintenance/due", response_model=list[MaintenanceScheduleResponse])
async def list_due_maintenance(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les maintenances dues."""
    service = get_production_service(db, context.tenant_id)
    return service.list_due_maintenance()

# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=ProductionDashboard)
async def get_production_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer le dashboard de production."""
    service = get_production_service(db, context.tenant_id)
    return service.get_production_dashboard()
