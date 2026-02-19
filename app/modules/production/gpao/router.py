"""
AZALSCORE GPAO/MRP Router V3
=============================

Endpoints REST pour la gestion de production.

Endpoints BOM:
- GET  /v3/production/gpao/boms - Liste nomenclatures
- POST /v3/production/gpao/boms - Créer nomenclature
- GET  /v3/production/gpao/boms/{id} - Détails BOM
- POST /v3/production/gpao/boms/{id}/components - Ajouter composant

Endpoints Gammes:
- GET  /v3/production/gpao/routings - Liste gammes
- POST /v3/production/gpao/routings - Créer gamme
- GET  /v3/production/gpao/routings/{id} - Détails gamme

Endpoints OF:
- GET  /v3/production/gpao/orders - Liste OF
- POST /v3/production/gpao/orders - Créer OF
- GET  /v3/production/gpao/orders/{id} - Détails OF
- POST /v3/production/gpao/orders/{id}/release - Lancer OF
- POST /v3/production/gpao/orders/{id}/start - Démarrer OF
- POST /v3/production/gpao/orders/{id}/report - Déclarer production
- POST /v3/production/gpao/orders/{id}/complete - Terminer OF
- POST /v3/production/gpao/orders/{id}/cancel - Annuler OF

Endpoints MRP:
- POST /v3/production/gpao/mrp/calculate - Calcul besoins
- POST /v3/production/gpao/mrp/run - Exécuter MRP

Endpoints Capacité:
- POST /v3/production/gpao/capacity - Plan de capacité
- GET  /v3/production/gpao/stats - Statistiques
- GET  /v3/production/gpao/health - Health check
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    GPAOService,
    ManufacturingOrder,
    BillOfMaterials,
    BOMComponent,
    Routing,
    RoutingOperation,
    MRPRequirement,
    CapacityPlan,
    ProductionStatus,
    OperationType,
    UnitOfMeasure,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/production/gpao", tags=["Production GPAO"])


# =============================================================================
# SCHEMAS
# =============================================================================


class ComponentInput(BaseModel):
    """Composant en entrée."""
    product_id: str
    product_name: str = ""
    quantity: Decimal = Field(..., gt=0)
    unit: str = "piece"
    is_phantom: bool = False
    scrap_rate: Decimal = Field(Decimal("0"), ge=0)
    lead_time_days: int = Field(0, ge=0)


class CreateBOMRequest(BaseModel):
    """Requête création BOM."""
    product_id: str
    product_name: str
    components: list[ComponentInput]
    version: str = "1.0"
    effective_date: Optional[date] = None
    notes: Optional[str] = None


class ComponentResponse(BaseModel):
    """Composant en réponse."""
    id: str
    product_id: str
    product_name: str
    quantity: Decimal
    unit: str
    position: int
    is_phantom: bool
    scrap_rate: Decimal


class BOMResponse(BaseModel):
    """Réponse BOM."""
    id: str
    product_id: str
    product_name: str
    version: str
    components: list[ComponentResponse]
    is_active: bool
    total_components: int
    effective_date: str
    created_at: str


class OperationInput(BaseModel):
    """Opération en entrée."""
    name: str
    type: str = "other"
    workstation_id: Optional[str] = None
    workstation_name: Optional[str] = None
    setup_time: int = Field(0, ge=0)
    run_time: int = Field(0, ge=0)
    queue_time: int = Field(0, ge=0)
    instructions: Optional[str] = None


class CreateRoutingRequest(BaseModel):
    """Requête création gamme."""
    product_id: str
    product_name: str
    operations: list[OperationInput]
    version: str = "1.0"


class OperationResponse(BaseModel):
    """Opération en réponse."""
    id: str
    sequence: int
    name: str
    operation_type: str
    workstation_id: Optional[str]
    workstation_name: Optional[str]
    setup_time_minutes: int
    run_time_minutes: int
    total_time_minutes: int


class RoutingResponse(BaseModel):
    """Réponse gamme."""
    id: str
    product_id: str
    product_name: str
    version: str
    operations: list[OperationResponse]
    total_time_minutes: int
    is_active: bool
    created_at: str


class CreateOrderRequest(BaseModel):
    """Requête création OF."""
    product_id: str
    product_name: str
    quantity: Decimal = Field(..., gt=0)
    unit: str = "piece"
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    priority: int = Field(5, ge=1, le=10)
    bom_id: Optional[str] = None
    routing_id: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Réponse OF."""
    id: str
    order_number: str
    product_id: str
    product_name: str
    quantity_planned: Decimal
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    quantity_remaining: Decimal
    unit: str
    status: str
    priority: int
    completion_rate: Decimal
    scrap_rate: Decimal
    bom_id: Optional[str]
    routing_id: Optional[str]
    planned_start: Optional[str]
    planned_end: Optional[str]
    actual_start: Optional[str]
    actual_end: Optional[str]
    created_at: str


class ReportProductionRequest(BaseModel):
    """Requête déclaration production."""
    quantity_produced: Decimal = Field(..., ge=0)
    quantity_scrapped: Decimal = Field(Decimal("0"), ge=0)
    operator_id: Optional[str] = None


class CancelOrderRequest(BaseModel):
    """Requête annulation OF."""
    reason: Optional[str] = None


class CalculateMRPRequest(BaseModel):
    """Requête calcul MRP."""
    product_id: str
    product_name: str
    quantity: Decimal = Field(..., gt=0)
    due_date: date
    on_hand: Decimal = Field(Decimal("0"), ge=0)
    scheduled_receipts: Decimal = Field(Decimal("0"), ge=0)


class MRPRequirementResponse(BaseModel):
    """Réponse besoin MRP."""
    id: str
    product_id: str
    product_name: str
    requirement_date: str
    gross_requirement: Decimal
    scheduled_receipts: Decimal
    projected_on_hand: Decimal
    net_requirement: Decimal
    planned_order_release: Optional[str]
    planned_order_quantity: Decimal
    action_type: Optional[str]
    action_message: Optional[str]
    level: int


class CapacityRequest(BaseModel):
    """Requête plan capacité."""
    workstation_id: str
    workstation_name: str
    start_date: date
    end_date: date
    available_hours_per_day: Decimal = Field(Decimal("8"), gt=0)


class CapacityPlanResponse(BaseModel):
    """Réponse plan capacité."""
    workstation_id: str
    workstation_name: str
    date: str
    available_hours: Decimal
    planned_hours: Decimal
    utilization_rate: Decimal
    is_overloaded: bool
    orders: list[str]


class AddComponentRequest(BaseModel):
    """Requête ajout composant."""
    product_id: str
    product_name: str
    quantity: Decimal = Field(..., gt=0)
    unit: str = "piece"


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_gpao_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> GPAOService:
    """Dépendance pour obtenir le service GPAO."""
    return GPAOService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def bom_to_response(bom: BillOfMaterials) -> BOMResponse:
    """Convertit une BOM en réponse."""
    return BOMResponse(
        id=bom.id,
        product_id=bom.product_id,
        product_name=bom.product_name,
        version=bom.version,
        components=[
            ComponentResponse(
                id=c.id,
                product_id=c.product_id,
                product_name=c.product_name,
                quantity=c.quantity,
                unit=c.unit.value,
                position=c.position,
                is_phantom=c.is_phantom,
                scrap_rate=c.scrap_rate,
            )
            for c in bom.components
        ],
        is_active=bom.is_active,
        total_components=bom.total_components,
        effective_date=bom.effective_date.isoformat(),
        created_at=bom.created_at.isoformat(),
    )


def routing_to_response(routing: Routing) -> RoutingResponse:
    """Convertit une gamme en réponse."""
    return RoutingResponse(
        id=routing.id,
        product_id=routing.product_id,
        product_name=routing.product_name,
        version=routing.version,
        operations=[
            OperationResponse(
                id=op.id,
                sequence=op.sequence,
                name=op.name,
                operation_type=op.operation_type.value,
                workstation_id=op.workstation_id,
                workstation_name=op.workstation_name,
                setup_time_minutes=op.setup_time_minutes,
                run_time_minutes=op.run_time_minutes,
                total_time_minutes=op.total_time_minutes,
            )
            for op in routing.operations
        ],
        total_time_minutes=routing.total_time_minutes,
        is_active=routing.is_active,
        created_at=routing.created_at.isoformat(),
    )


def order_to_response(order: ManufacturingOrder) -> OrderResponse:
    """Convertit un OF en réponse."""
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        product_id=order.product_id,
        product_name=order.product_name,
        quantity_planned=order.quantity_planned,
        quantity_produced=order.quantity_produced,
        quantity_scrapped=order.quantity_scrapped,
        quantity_remaining=order.quantity_remaining,
        unit=order.unit.value,
        status=order.status.value,
        priority=order.priority,
        completion_rate=order.completion_rate,
        scrap_rate=order.scrap_rate,
        bom_id=order.bom_id,
        routing_id=order.routing_id,
        planned_start=order.planned_start.isoformat() if order.planned_start else None,
        planned_end=order.planned_end.isoformat() if order.planned_end else None,
        actual_start=order.actual_start.isoformat() if order.actual_start else None,
        actual_end=order.actual_end.isoformat() if order.actual_end else None,
        created_at=order.created_at.isoformat(),
    )


# =============================================================================
# ENDPOINTS - BOM
# =============================================================================


@router.get(
    "/boms",
    response_model=list[BOMResponse],
    summary="Liste des nomenclatures",
    description="Retourne toutes les nomenclatures (BOM).",
)
async def list_boms(
    product_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
    service: GPAOService = Depends(get_gpao_service),
):
    """Liste les nomenclatures."""
    boms = await service.list_boms(product_id=product_id, active_only=active_only)
    return [bom_to_response(b) for b in boms]


@router.post(
    "/boms",
    response_model=BOMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nomenclature",
    description="Crée une nouvelle nomenclature (BOM).",
)
async def create_bom(
    request: CreateBOMRequest,
    service: GPAOService = Depends(get_gpao_service),
):
    """Crée une nomenclature."""
    bom = await service.create_bom(
        product_id=request.product_id,
        product_name=request.product_name,
        components=[c.model_dump() for c in request.components],
        version=request.version,
        effective_date=request.effective_date,
        notes=request.notes,
    )
    return bom_to_response(bom)


@router.get(
    "/boms/{bom_id}",
    response_model=BOMResponse,
    summary="Détails d'une nomenclature",
)
async def get_bom(
    bom_id: str,
    service: GPAOService = Depends(get_gpao_service),
):
    """Détails d'une BOM."""
    bom = await service.get_bom(bom_id)
    if not bom:
        raise HTTPException(status_code=404, detail="BOM non trouvée")
    return bom_to_response(bom)


@router.post(
    "/boms/{bom_id}/components",
    response_model=BOMResponse,
    summary="Ajouter un composant",
)
async def add_component(
    bom_id: str,
    request: AddComponentRequest,
    service: GPAOService = Depends(get_gpao_service),
):
    """Ajoute un composant à une BOM."""
    bom = await service.add_bom_component(
        bom_id=bom_id,
        product_id=request.product_id,
        product_name=request.product_name,
        quantity=request.quantity,
        unit=UnitOfMeasure(request.unit),
    )
    if not bom:
        raise HTTPException(status_code=404, detail="BOM non trouvée")
    return bom_to_response(bom)


# =============================================================================
# ENDPOINTS - ROUTING
# =============================================================================


@router.get(
    "/routings",
    response_model=list[RoutingResponse],
    summary="Liste des gammes",
    description="Retourne toutes les gammes de fabrication.",
)
async def list_routings(
    product_id: Optional[str] = Query(None),
    service: GPAOService = Depends(get_gpao_service),
):
    """Liste les gammes."""
    routings = await service.list_routings(product_id=product_id)
    return [routing_to_response(r) for r in routings]


@router.post(
    "/routings",
    response_model=RoutingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une gamme",
    description="Crée une nouvelle gamme de fabrication.",
)
async def create_routing(
    request: CreateRoutingRequest,
    service: GPAOService = Depends(get_gpao_service),
):
    """Crée une gamme."""
    routing = await service.create_routing(
        product_id=request.product_id,
        product_name=request.product_name,
        operations=[op.model_dump() for op in request.operations],
        version=request.version,
    )
    return routing_to_response(routing)


@router.get(
    "/routings/{routing_id}",
    response_model=RoutingResponse,
    summary="Détails d'une gamme",
)
async def get_routing(
    routing_id: str,
    service: GPAOService = Depends(get_gpao_service),
):
    """Détails d'une gamme."""
    routing = await service.get_routing(routing_id)
    if not routing:
        raise HTTPException(status_code=404, detail="Gamme non trouvée")
    return routing_to_response(routing)


# =============================================================================
# ENDPOINTS - MANUFACTURING ORDERS
# =============================================================================


@router.get(
    "/orders",
    response_model=list[OrderResponse],
    summary="Liste des ordres de fabrication",
)
async def list_orders(
    order_status: Optional[ProductionStatus] = Query(None, alias="status"),
    product_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: GPAOService = Depends(get_gpao_service),
):
    """Liste les ordres de fabrication."""
    orders = await service.list_orders(
        status=order_status,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return [order_to_response(o) for o in orders]


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un ordre de fabrication",
)
async def create_order(
    request: CreateOrderRequest,
    service: GPAOService = Depends(get_gpao_service),
):
    """Crée un ordre de fabrication."""
    order = await service.create_manufacturing_order(
        product_id=request.product_id,
        product_name=request.product_name,
        quantity=request.quantity,
        unit=UnitOfMeasure(request.unit),
        planned_start=request.planned_start,
        planned_end=request.planned_end,
        priority=request.priority,
        bom_id=request.bom_id,
        routing_id=request.routing_id,
        notes=request.notes,
    )
    return order_to_response(order)


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Détails d'un ordre de fabrication",
)
async def get_order(
    order_id: str,
    service: GPAOService = Depends(get_gpao_service),
):
    """Détails d'un OF."""
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="OF non trouvé")
    return order_to_response(order)


@router.post(
    "/orders/{order_id}/release",
    response_model=OrderResponse,
    summary="Lancer un ordre de fabrication",
)
async def release_order(
    order_id: str,
    service: GPAOService = Depends(get_gpao_service),
):
    """Lance un OF."""
    order = await service.release_order(order_id)
    if not order:
        raise HTTPException(status_code=400, detail="Impossible de lancer cet OF")
    return order_to_response(order)


@router.post(
    "/orders/{order_id}/start",
    response_model=OrderResponse,
    summary="Démarrer un ordre de fabrication",
)
async def start_order(
    order_id: str,
    service: GPAOService = Depends(get_gpao_service),
):
    """Démarre un OF."""
    order = await service.start_order(order_id)
    if not order:
        raise HTTPException(status_code=400, detail="Impossible de démarrer cet OF")
    return order_to_response(order)


@router.post(
    "/orders/{order_id}/report",
    response_model=OrderResponse,
    summary="Déclarer de la production",
)
async def report_production(
    order_id: str,
    request: ReportProductionRequest,
    service: GPAOService = Depends(get_gpao_service),
):
    """Déclare de la production."""
    order = await service.report_production(
        order_id=order_id,
        quantity_produced=request.quantity_produced,
        quantity_scrapped=request.quantity_scrapped,
        operator_id=request.operator_id,
    )
    if not order:
        raise HTTPException(status_code=400, detail="Impossible de déclarer sur cet OF")
    return order_to_response(order)


@router.post(
    "/orders/{order_id}/complete",
    response_model=OrderResponse,
    summary="Terminer un ordre de fabrication",
)
async def complete_order(
    order_id: str,
    service: GPAOService = Depends(get_gpao_service),
):
    """Termine un OF."""
    order = await service.complete_order(order_id)
    if not order:
        raise HTTPException(status_code=400, detail="Impossible de terminer cet OF")
    return order_to_response(order)


@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Annuler un ordre de fabrication",
)
async def cancel_order(
    order_id: str,
    request: CancelOrderRequest = CancelOrderRequest(),
    service: GPAOService = Depends(get_gpao_service),
):
    """Annule un OF."""
    order = await service.cancel_order(order_id, reason=request.reason)
    if not order:
        raise HTTPException(status_code=400, detail="Impossible d'annuler cet OF")
    return order_to_response(order)


# =============================================================================
# ENDPOINTS - MRP
# =============================================================================


@router.post(
    "/mrp/calculate",
    response_model=list[MRPRequirementResponse],
    summary="Calculer les besoins MRP",
    description="Calcule les besoins nets pour un produit.",
)
async def calculate_mrp(
    request: CalculateMRPRequest,
    service: GPAOService = Depends(get_gpao_service),
):
    """Calcule les besoins MRP."""
    requirements = await service.calculate_requirements(
        product_id=request.product_id,
        product_name=request.product_name,
        quantity=request.quantity,
        due_date=request.due_date,
        on_hand=request.on_hand,
        scheduled_receipts=request.scheduled_receipts,
    )

    return [
        MRPRequirementResponse(
            id=r.id,
            product_id=r.product_id,
            product_name=r.product_name,
            requirement_date=r.requirement_date.isoformat(),
            gross_requirement=r.gross_requirement,
            scheduled_receipts=r.scheduled_receipts,
            projected_on_hand=r.projected_on_hand,
            net_requirement=r.net_requirement,
            planned_order_release=r.planned_order_release.isoformat() if r.planned_order_release else None,
            planned_order_quantity=r.planned_order_quantity,
            action_type=r.action_type.value if r.action_type else None,
            action_message=r.action_message,
            level=r.level,
        )
        for r in requirements
    ]


@router.post(
    "/mrp/run",
    response_model=list[MRPRequirementResponse],
    summary="Exécuter le MRP complet",
    description="Exécute le calcul MRP pour tous les OF planifiés.",
)
async def run_mrp(
    horizon_days: int = Query(30, ge=1, le=365),
    service: GPAOService = Depends(get_gpao_service),
):
    """Exécute le MRP complet."""
    requirements = await service.run_mrp(horizon_days=horizon_days)

    return [
        MRPRequirementResponse(
            id=r.id,
            product_id=r.product_id,
            product_name=r.product_name,
            requirement_date=r.requirement_date.isoformat(),
            gross_requirement=r.gross_requirement,
            scheduled_receipts=r.scheduled_receipts,
            projected_on_hand=r.projected_on_hand,
            net_requirement=r.net_requirement,
            planned_order_release=r.planned_order_release.isoformat() if r.planned_order_release else None,
            planned_order_quantity=r.planned_order_quantity,
            action_type=r.action_type.value if r.action_type else None,
            action_message=r.action_message,
            level=r.level,
        )
        for r in requirements
    ]


# =============================================================================
# ENDPOINTS - CAPACITY
# =============================================================================


@router.post(
    "/capacity",
    response_model=list[CapacityPlanResponse],
    summary="Calculer le plan de capacité",
)
async def calculate_capacity(
    request: CapacityRequest,
    service: GPAOService = Depends(get_gpao_service),
):
    """Calcule le plan de capacité."""
    plans = await service.calculate_capacity(
        workstation_id=request.workstation_id,
        workstation_name=request.workstation_name,
        start_date=request.start_date,
        end_date=request.end_date,
        available_hours_per_day=request.available_hours_per_day,
    )

    return [
        CapacityPlanResponse(
            workstation_id=p.workstation_id,
            workstation_name=p.workstation_name,
            date=p.date.isoformat(),
            available_hours=p.available_hours,
            planned_hours=p.planned_hours,
            utilization_rate=p.utilization_rate,
            is_overloaded=p.is_overloaded,
            orders=p.orders,
        )
        for p in plans
    ]


# =============================================================================
# ENDPOINTS - STATS & HEALTH
# =============================================================================


@router.get(
    "/stats",
    summary="Statistiques de production",
)
async def get_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: GPAOService = Depends(get_gpao_service),
):
    """Statistiques de production."""
    return await service.get_production_stats(start_date, end_date)


@router.get(
    "/health",
    summary="Health check GPAO",
)
async def health_check():
    """Health check du service GPAO."""
    return {
        "status": "healthy",
        "service": "production-gpao",
        "features": [
            "bill_of_materials",
            "routings",
            "manufacturing_orders",
            "mrp_calculation",
            "capacity_planning",
            "production_tracking",
        ],
        "statuses": [s.value for s in ProductionStatus],
        "operation_types": [o.value for o in OperationType],
    }
