"""
MES Router - API REST V3
========================

Endpoints pour le Manufacturing Execution System.
"""
from __future__ import annotations


from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .service import (
    MESService,
    WorkstationStatus,
    OperationStatus,
    DowntimeReason,
    CheckResult,
)


router = APIRouter(prefix="/v3/production/mes", tags=["MES"])


# ========================
# SCHEMAS
# ========================

class WorkstationCreate(BaseModel):
    """Création de poste de travail."""
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    workstation_type: str
    location: Optional[str] = None
    capacity_per_hour: Optional[float] = None
    metadata: Optional[dict] = None


class WorkstationResponse(BaseModel):
    """Réponse poste de travail."""
    id: str
    code: str
    name: str
    workstation_type: str
    status: WorkstationStatus
    location: Optional[str]
    capacity_per_hour: Optional[float]
    current_operator_id: Optional[str]
    current_operation_id: Optional[str]
    is_active: bool


class WorkstationStatusUpdate(BaseModel):
    """Mise à jour statut poste."""
    status: WorkstationStatus
    operator_id: Optional[str] = None


class OperationCreate(BaseModel):
    """Création d'opération."""
    workstation_id: str
    order_id: str
    product_id: str
    operation_code: str
    operation_name: str
    planned_qty: float = Field(..., gt=0)
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None


class OperationResponse(BaseModel):
    """Réponse opération."""
    id: str
    workstation_id: str
    order_id: str
    product_id: str
    operation_code: str
    operation_name: str
    status: OperationStatus
    planned_qty: float
    produced_qty: float
    scrap_qty: float
    good_qty: float
    yield_rate: float
    completion_rate: float
    operator_id: Optional[str]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    setup_time: float
    run_time: float
    total_time: float


class StartOperationRequest(BaseModel):
    """Requête démarrage opération."""
    operator_id: str
    setup_time: float = 0.0


class ReportProductionRequest(BaseModel):
    """Requête déclaration production."""
    quantity: float = Field(..., gt=0)
    scrap_qty: float = 0.0


class CompleteOperationRequest(BaseModel):
    """Requête fin d'opération."""
    produced_qty: float = Field(..., ge=0)
    scrap_qty: float = 0.0


class QualityCheckCreate(BaseModel):
    """Création contrôle qualité."""
    operation_id: str
    workstation_id: str
    check_type: str
    check_name: str
    expected_value: Optional[str] = None


class QualityCheckRecord(BaseModel):
    """Enregistrement contrôle."""
    actual_value: str
    result: CheckResult
    checked_by: str
    notes: Optional[str] = None


class QualityCheckResponse(BaseModel):
    """Réponse contrôle qualité."""
    id: str
    operation_id: str
    workstation_id: str
    check_type: str
    check_name: str
    expected_value: Optional[str]
    actual_value: Optional[str]
    result: CheckResult
    checked_by: Optional[str]
    checked_at: Optional[datetime]


class DowntimeCreate(BaseModel):
    """Création d'arrêt."""
    workstation_id: str
    reason: DowntimeReason
    operation_id: Optional[str] = None
    description: Optional[str] = None
    reported_by: Optional[str] = None


class DowntimeResponse(BaseModel):
    """Réponse arrêt."""
    id: str
    workstation_id: str
    operation_id: Optional[str]
    reason: DowntimeReason
    description: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[float]
    reported_by: Optional[str]
    resolved_by: Optional[str]


class OEERequest(BaseModel):
    """Requête calcul OEE."""
    period_start: datetime
    period_end: datetime


class OEEResponse(BaseModel):
    """Réponse OEE."""
    workstation_id: str
    period_start: datetime
    period_end: datetime
    availability: float
    performance: float
    quality: float
    oee: float
    total_time: float
    run_time: float
    downtime: float
    planned_qty: float
    produced_qty: float
    good_qty: float


# ========================
# DEPENDENCIES
# ========================

async def get_mes_service(
    tenant_id: str = Query(..., alias="tenant_id")
) -> MESService:
    """Dépendance pour obtenir le service MES."""
    return MESService(db=None, tenant_id=tenant_id)


# ========================
# WORKSTATION ENDPOINTS
# ========================

@router.post("/workstations", status_code=201, response_model=WorkstationResponse)
async def create_workstation(
    data: WorkstationCreate,
    service: MESService = Depends(get_mes_service)
):
    """Crée un poste de travail."""
    ws = await service.create_workstation(
        code=data.code,
        name=data.name,
        workstation_type=data.workstation_type,
        location=data.location,
        capacity_per_hour=data.capacity_per_hour,
        metadata=data.metadata
    )
    return WorkstationResponse(
        id=ws.id,
        code=ws.code,
        name=ws.name,
        workstation_type=ws.workstation_type,
        status=ws.status,
        location=ws.location,
        capacity_per_hour=ws.capacity_per_hour,
        current_operator_id=ws.current_operator_id,
        current_operation_id=ws.current_operation_id,
        is_active=ws.is_active
    )


@router.get("/workstations", response_model=list[WorkstationResponse])
async def list_workstations(
    workstation_type: Optional[str] = None,
    status: Optional[WorkstationStatus] = None,
    is_active: Optional[bool] = None,
    service: MESService = Depends(get_mes_service)
):
    """Liste les postes de travail."""
    workstations = await service.list_workstations(
        workstation_type=workstation_type,
        status=status,
        is_active=is_active
    )
    return [
        WorkstationResponse(
            id=ws.id,
            code=ws.code,
            name=ws.name,
            workstation_type=ws.workstation_type,
            status=ws.status,
            location=ws.location,
            capacity_per_hour=ws.capacity_per_hour,
            current_operator_id=ws.current_operator_id,
            current_operation_id=ws.current_operation_id,
            is_active=ws.is_active
        )
        for ws in workstations
    ]


@router.get("/workstations/{workstation_id}", response_model=WorkstationResponse)
async def get_workstation(
    workstation_id: str,
    service: MESService = Depends(get_mes_service)
):
    """Récupère un poste de travail."""
    ws = await service.get_workstation(workstation_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workstation not found")
    return WorkstationResponse(
        id=ws.id,
        code=ws.code,
        name=ws.name,
        workstation_type=ws.workstation_type,
        status=ws.status,
        location=ws.location,
        capacity_per_hour=ws.capacity_per_hour,
        current_operator_id=ws.current_operator_id,
        current_operation_id=ws.current_operation_id,
        is_active=ws.is_active
    )


@router.patch(
    "/workstations/{workstation_id}/status",
    response_model=WorkstationResponse
)
async def update_workstation_status(
    workstation_id: str,
    data: WorkstationStatusUpdate,
    service: MESService = Depends(get_mes_service)
):
    """Met à jour le statut d'un poste."""
    ws = await service.update_workstation_status(
        workstation_id,
        status=data.status,
        operator_id=data.operator_id
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workstation not found")
    return WorkstationResponse(
        id=ws.id,
        code=ws.code,
        name=ws.name,
        workstation_type=ws.workstation_type,
        status=ws.status,
        location=ws.location,
        capacity_per_hour=ws.capacity_per_hour,
        current_operator_id=ws.current_operator_id,
        current_operation_id=ws.current_operation_id,
        is_active=ws.is_active
    )


@router.get("/workstations/{workstation_id}/stats")
async def get_workstation_stats(
    workstation_id: str,
    service: MESService = Depends(get_mes_service)
):
    """Récupère les statistiques d'un poste."""
    return await service.get_workstation_stats(workstation_id)


@router.post("/workstations/{workstation_id}/oee", response_model=OEEResponse)
async def calculate_workstation_oee(
    workstation_id: str,
    data: OEERequest,
    service: MESService = Depends(get_mes_service)
):
    """Calcule l'OEE d'un poste."""
    oee = await service.calculate_oee(
        workstation_id,
        period_start=data.period_start,
        period_end=data.period_end
    )
    return OEEResponse(
        workstation_id=oee.workstation_id,
        period_start=oee.period_start,
        period_end=oee.period_end,
        availability=oee.availability,
        performance=oee.performance,
        quality=oee.quality,
        oee=oee.oee,
        total_time=oee.total_time,
        run_time=oee.run_time,
        downtime=oee.downtime,
        planned_qty=oee.planned_qty,
        produced_qty=oee.produced_qty,
        good_qty=oee.good_qty
    )


# ========================
# OPERATION ENDPOINTS
# ========================

@router.post("/operations", status_code=201, response_model=OperationResponse)
async def create_operation(
    data: OperationCreate,
    service: MESService = Depends(get_mes_service)
):
    """Crée une opération."""
    op = await service.create_operation(
        workstation_id=data.workstation_id,
        order_id=data.order_id,
        product_id=data.product_id,
        operation_code=data.operation_code,
        operation_name=data.operation_name,
        planned_qty=data.planned_qty,
        planned_start=data.planned_start,
        planned_end=data.planned_end
    )
    return OperationResponse(
        id=op.id,
        workstation_id=op.workstation_id,
        order_id=op.order_id,
        product_id=op.product_id,
        operation_code=op.operation_code,
        operation_name=op.operation_name,
        status=op.status,
        planned_qty=op.planned_qty,
        produced_qty=op.produced_qty,
        scrap_qty=op.scrap_qty,
        good_qty=op.good_qty,
        yield_rate=op.yield_rate,
        completion_rate=op.completion_rate,
        operator_id=op.operator_id,
        actual_start=op.actual_start,
        actual_end=op.actual_end,
        setup_time=op.setup_time,
        run_time=op.run_time,
        total_time=op.total_time
    )


@router.get("/operations", response_model=list[OperationResponse])
async def list_operations(
    workstation_id: Optional[str] = None,
    order_id: Optional[str] = None,
    status: Optional[OperationStatus] = None,
    service: MESService = Depends(get_mes_service)
):
    """Liste les opérations."""
    operations = await service.list_operations(
        workstation_id=workstation_id,
        order_id=order_id,
        status=status
    )
    return [
        OperationResponse(
            id=op.id,
            workstation_id=op.workstation_id,
            order_id=op.order_id,
            product_id=op.product_id,
            operation_code=op.operation_code,
            operation_name=op.operation_name,
            status=op.status,
            planned_qty=op.planned_qty,
            produced_qty=op.produced_qty,
            scrap_qty=op.scrap_qty,
            good_qty=op.good_qty,
            yield_rate=op.yield_rate,
            completion_rate=op.completion_rate,
            operator_id=op.operator_id,
            actual_start=op.actual_start,
            actual_end=op.actual_end,
            setup_time=op.setup_time,
            run_time=op.run_time,
            total_time=op.total_time
        )
        for op in operations
    ]


@router.get("/operations/{operation_id}", response_model=OperationResponse)
async def get_operation(
    operation_id: str,
    service: MESService = Depends(get_mes_service)
):
    """Récupère une opération."""
    op = await service.get_operation(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return OperationResponse(
        id=op.id,
        workstation_id=op.workstation_id,
        order_id=op.order_id,
        product_id=op.product_id,
        operation_code=op.operation_code,
        operation_name=op.operation_name,
        status=op.status,
        planned_qty=op.planned_qty,
        produced_qty=op.produced_qty,
        scrap_qty=op.scrap_qty,
        good_qty=op.good_qty,
        yield_rate=op.yield_rate,
        completion_rate=op.completion_rate,
        operator_id=op.operator_id,
        actual_start=op.actual_start,
        actual_end=op.actual_end,
        setup_time=op.setup_time,
        run_time=op.run_time,
        total_time=op.total_time
    )


@router.post("/operations/{operation_id}/start", response_model=OperationResponse)
async def start_operation(
    operation_id: str,
    data: StartOperationRequest,
    service: MESService = Depends(get_mes_service)
):
    """Démarre une opération."""
    op = await service.start_operation(
        operation_id,
        operator_id=data.operator_id,
        setup_time=data.setup_time
    )
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return OperationResponse(
        id=op.id,
        workstation_id=op.workstation_id,
        order_id=op.order_id,
        product_id=op.product_id,
        operation_code=op.operation_code,
        operation_name=op.operation_name,
        status=op.status,
        planned_qty=op.planned_qty,
        produced_qty=op.produced_qty,
        scrap_qty=op.scrap_qty,
        good_qty=op.good_qty,
        yield_rate=op.yield_rate,
        completion_rate=op.completion_rate,
        operator_id=op.operator_id,
        actual_start=op.actual_start,
        actual_end=op.actual_end,
        setup_time=op.setup_time,
        run_time=op.run_time,
        total_time=op.total_time
    )


@router.post("/operations/{operation_id}/pause", response_model=OperationResponse)
async def pause_operation(
    operation_id: str,
    notes: Optional[str] = None,
    service: MESService = Depends(get_mes_service)
):
    """Met en pause une opération."""
    op = await service.pause_operation(operation_id, notes=notes)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return OperationResponse(
        id=op.id,
        workstation_id=op.workstation_id,
        order_id=op.order_id,
        product_id=op.product_id,
        operation_code=op.operation_code,
        operation_name=op.operation_name,
        status=op.status,
        planned_qty=op.planned_qty,
        produced_qty=op.produced_qty,
        scrap_qty=op.scrap_qty,
        good_qty=op.good_qty,
        yield_rate=op.yield_rate,
        completion_rate=op.completion_rate,
        operator_id=op.operator_id,
        actual_start=op.actual_start,
        actual_end=op.actual_end,
        setup_time=op.setup_time,
        run_time=op.run_time,
        total_time=op.total_time
    )


@router.post("/operations/{operation_id}/resume", response_model=OperationResponse)
async def resume_operation(
    operation_id: str,
    service: MESService = Depends(get_mes_service)
):
    """Reprend une opération."""
    op = await service.resume_operation(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return OperationResponse(
        id=op.id,
        workstation_id=op.workstation_id,
        order_id=op.order_id,
        product_id=op.product_id,
        operation_code=op.operation_code,
        operation_name=op.operation_name,
        status=op.status,
        planned_qty=op.planned_qty,
        produced_qty=op.produced_qty,
        scrap_qty=op.scrap_qty,
        good_qty=op.good_qty,
        yield_rate=op.yield_rate,
        completion_rate=op.completion_rate,
        operator_id=op.operator_id,
        actual_start=op.actual_start,
        actual_end=op.actual_end,
        setup_time=op.setup_time,
        run_time=op.run_time,
        total_time=op.total_time
    )


@router.post("/operations/{operation_id}/report", response_model=OperationResponse)
async def report_production(
    operation_id: str,
    data: ReportProductionRequest,
    service: MESService = Depends(get_mes_service)
):
    """Déclare une production partielle."""
    op = await service.report_production(
        operation_id,
        quantity=data.quantity,
        scrap_qty=data.scrap_qty
    )
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return OperationResponse(
        id=op.id,
        workstation_id=op.workstation_id,
        order_id=op.order_id,
        product_id=op.product_id,
        operation_code=op.operation_code,
        operation_name=op.operation_name,
        status=op.status,
        planned_qty=op.planned_qty,
        produced_qty=op.produced_qty,
        scrap_qty=op.scrap_qty,
        good_qty=op.good_qty,
        yield_rate=op.yield_rate,
        completion_rate=op.completion_rate,
        operator_id=op.operator_id,
        actual_start=op.actual_start,
        actual_end=op.actual_end,
        setup_time=op.setup_time,
        run_time=op.run_time,
        total_time=op.total_time
    )


@router.post("/operations/{operation_id}/complete", response_model=OperationResponse)
async def complete_operation(
    operation_id: str,
    data: CompleteOperationRequest,
    service: MESService = Depends(get_mes_service)
):
    """Termine une opération."""
    op = await service.complete_operation(
        operation_id,
        produced_qty=data.produced_qty,
        scrap_qty=data.scrap_qty
    )
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return OperationResponse(
        id=op.id,
        workstation_id=op.workstation_id,
        order_id=op.order_id,
        product_id=op.product_id,
        operation_code=op.operation_code,
        operation_name=op.operation_name,
        status=op.status,
        planned_qty=op.planned_qty,
        produced_qty=op.produced_qty,
        scrap_qty=op.scrap_qty,
        good_qty=op.good_qty,
        yield_rate=op.yield_rate,
        completion_rate=op.completion_rate,
        operator_id=op.operator_id,
        actual_start=op.actual_start,
        actual_end=op.actual_end,
        setup_time=op.setup_time,
        run_time=op.run_time,
        total_time=op.total_time
    )


# ========================
# QUALITY CHECK ENDPOINTS
# ========================

@router.post("/quality-checks", status_code=201, response_model=QualityCheckResponse)
async def create_quality_check(
    data: QualityCheckCreate,
    service: MESService = Depends(get_mes_service)
):
    """Crée un contrôle qualité."""
    check = await service.create_quality_check(
        operation_id=data.operation_id,
        workstation_id=data.workstation_id,
        check_type=data.check_type,
        check_name=data.check_name,
        expected_value=data.expected_value
    )
    return QualityCheckResponse(
        id=check.id,
        operation_id=check.operation_id,
        workstation_id=check.workstation_id,
        check_type=check.check_type,
        check_name=check.check_name,
        expected_value=check.expected_value,
        actual_value=check.actual_value,
        result=check.result,
        checked_by=check.checked_by,
        checked_at=check.checked_at
    )


@router.get("/quality-checks", response_model=list[QualityCheckResponse])
async def list_quality_checks(
    operation_id: Optional[str] = None,
    workstation_id: Optional[str] = None,
    result: Optional[CheckResult] = None,
    service: MESService = Depends(get_mes_service)
):
    """Liste les contrôles qualité."""
    checks = await service.list_quality_checks(
        operation_id=operation_id,
        workstation_id=workstation_id,
        result=result
    )
    return [
        QualityCheckResponse(
            id=c.id,
            operation_id=c.operation_id,
            workstation_id=c.workstation_id,
            check_type=c.check_type,
            check_name=c.check_name,
            expected_value=c.expected_value,
            actual_value=c.actual_value,
            result=c.result,
            checked_by=c.checked_by,
            checked_at=c.checked_at
        )
        for c in checks
    ]


@router.post(
    "/quality-checks/{check_id}/record",
    response_model=QualityCheckResponse
)
async def record_quality_check(
    check_id: str,
    data: QualityCheckRecord,
    service: MESService = Depends(get_mes_service)
):
    """Enregistre un résultat de contrôle."""
    check = await service.record_quality_check(
        check_id,
        actual_value=data.actual_value,
        result=data.result,
        checked_by=data.checked_by,
        notes=data.notes
    )
    if not check:
        raise HTTPException(status_code=404, detail="Quality check not found")
    return QualityCheckResponse(
        id=check.id,
        operation_id=check.operation_id,
        workstation_id=check.workstation_id,
        check_type=check.check_type,
        check_name=check.check_name,
        expected_value=check.expected_value,
        actual_value=check.actual_value,
        result=check.result,
        checked_by=check.checked_by,
        checked_at=check.checked_at
    )


# ========================
# DOWNTIME ENDPOINTS
# ========================

@router.post("/downtimes", status_code=201, response_model=DowntimeResponse)
async def report_downtime(
    data: DowntimeCreate,
    service: MESService = Depends(get_mes_service)
):
    """Déclare un arrêt."""
    dt = await service.report_downtime(
        workstation_id=data.workstation_id,
        reason=data.reason,
        operation_id=data.operation_id,
        description=data.description,
        reported_by=data.reported_by
    )
    return DowntimeResponse(
        id=dt.id,
        workstation_id=dt.workstation_id,
        operation_id=dt.operation_id,
        reason=dt.reason,
        description=dt.description,
        start_time=dt.start_time,
        end_time=dt.end_time,
        duration_minutes=dt.duration_minutes,
        reported_by=dt.reported_by,
        resolved_by=dt.resolved_by
    )


@router.get("/downtimes", response_model=list[DowntimeResponse])
async def list_downtimes(
    workstation_id: Optional[str] = None,
    reason: Optional[DowntimeReason] = None,
    active_only: bool = False,
    service: MESService = Depends(get_mes_service)
):
    """Liste les arrêts."""
    downtimes = await service.list_downtimes(
        workstation_id=workstation_id,
        reason=reason,
        active_only=active_only
    )
    return [
        DowntimeResponse(
            id=dt.id,
            workstation_id=dt.workstation_id,
            operation_id=dt.operation_id,
            reason=dt.reason,
            description=dt.description,
            start_time=dt.start_time,
            end_time=dt.end_time,
            duration_minutes=dt.duration_minutes,
            reported_by=dt.reported_by,
            resolved_by=dt.resolved_by
        )
        for dt in downtimes
    ]


@router.post("/downtimes/{downtime_id}/resolve", response_model=DowntimeResponse)
async def resolve_downtime(
    downtime_id: str,
    resolved_by: Optional[str] = None,
    service: MESService = Depends(get_mes_service)
):
    """Résout un arrêt."""
    dt = await service.resolve_downtime(downtime_id, resolved_by=resolved_by)
    if not dt:
        raise HTTPException(status_code=404, detail="Downtime not found")
    return DowntimeResponse(
        id=dt.id,
        workstation_id=dt.workstation_id,
        operation_id=dt.operation_id,
        reason=dt.reason,
        description=dt.description,
        start_time=dt.start_time,
        end_time=dt.end_time,
        duration_minutes=dt.duration_minutes,
        reported_by=dt.reported_by,
        resolved_by=dt.resolved_by
    )


# ========================
# DASHBOARD & STATS
# ========================

@router.get("/dashboard")
async def get_dashboard(
    service: MESService = Depends(get_mes_service)
):
    """Récupère les données du tableau de bord MES."""
    return await service.get_dashboard_data()


@router.get("/operators/{operator_id}/stats")
async def get_operator_stats(
    operator_id: str,
    service: MESService = Depends(get_mes_service)
):
    """Récupère les statistiques d'un opérateur."""
    return await service.get_operator_stats(operator_id)
