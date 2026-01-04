"""
AZALS MODULE M6 - Schémas Production
=====================================

Schémas Pydantic pour la gestion de production.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
import json

from .models import (
    WorkCenterType, WorkCenterStatus, BOMType, BOMStatus,
    OperationType, MOStatus, MOPriority, WorkOrderStatus,
    ConsumptionType, ScrapReason
)


# ============================================================================
# CENTRES DE TRAVAIL
# ============================================================================

class WorkCenterCreate(BaseModel):
    """Création d'un centre de travail."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: WorkCenterType = WorkCenterType.MACHINE
    warehouse_id: Optional[UUID] = None
    location: Optional[str] = None
    capacity: Decimal = Decimal("1")
    efficiency: Decimal = Decimal("100")
    oee_target: Decimal = Decimal("85")
    time_start: Decimal = Decimal("0")
    time_stop: Decimal = Decimal("0")
    time_before: Decimal = Decimal("0")
    time_after: Decimal = Decimal("0")
    cost_per_hour: Decimal = Decimal("0")
    cost_per_cycle: Decimal = Decimal("0")
    currency: str = "EUR"
    working_hours_per_day: Decimal = Decimal("8")
    working_days_per_week: int = 5
    manager_id: Optional[UUID] = None
    operator_ids: Optional[List[UUID]] = None
    requires_approval: bool = False
    allow_parallel: bool = False
    notes: Optional[str] = None


class WorkCenterUpdate(BaseModel):
    """Mise à jour d'un centre de travail."""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[WorkCenterType] = None
    status: Optional[WorkCenterStatus] = None
    warehouse_id: Optional[UUID] = None
    location: Optional[str] = None
    capacity: Optional[Decimal] = None
    efficiency: Optional[Decimal] = None
    oee_target: Optional[Decimal] = None
    cost_per_hour: Optional[Decimal] = None
    cost_per_cycle: Optional[Decimal] = None
    working_hours_per_day: Optional[Decimal] = None
    working_days_per_week: Optional[int] = None
    manager_id: Optional[UUID] = None
    operator_ids: Optional[List[UUID]] = None
    requires_approval: Optional[bool] = None
    allow_parallel: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class WorkCenterResponse(BaseModel):
    """Réponse centre de travail."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    type: WorkCenterType
    status: WorkCenterStatus
    warehouse_id: Optional[UUID]
    location: Optional[str]
    capacity: Decimal
    efficiency: Decimal
    oee_target: Decimal
    cost_per_hour: Decimal
    cost_per_cycle: Decimal
    currency: str
    working_hours_per_day: Decimal
    working_days_per_week: int
    manager_id: Optional[UUID]
    operator_ids: Optional[List[UUID]]
    requires_approval: bool
    allow_parallel: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator('operator_ids', mode='before')
    @classmethod
    def parse_operator_ids(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


class WorkCenterCapacityCreate(BaseModel):
    """Création de capacité centre de travail."""
    work_center_id: UUID
    date: date
    shift: str = "DAY"
    available_hours: Decimal
    notes: Optional[str] = None


class WorkCenterCapacityResponse(BaseModel):
    """Réponse capacité."""
    id: UUID
    work_center_id: UUID
    date: date
    shift: str
    available_hours: Decimal
    planned_hours: Decimal
    actual_hours: Decimal
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NOMENCLATURES (BOM)
# ============================================================================

class BOMLineCreate(BaseModel):
    """Création d'une ligne de nomenclature."""
    product_id: UUID
    quantity: Decimal
    unit: str = "UNIT"
    operation_id: Optional[UUID] = None
    scrap_rate: Decimal = Decimal("0")
    is_critical: bool = True
    alternative_group: Optional[str] = None
    consumption_type: Optional[ConsumptionType] = None
    notes: Optional[str] = None


class BOMLineResponse(BaseModel):
    """Réponse ligne de nomenclature."""
    id: UUID
    bom_id: UUID
    line_number: int
    product_id: UUID
    quantity: Decimal
    unit: str
    operation_id: Optional[UUID]
    scrap_rate: Decimal
    is_critical: bool
    alternative_group: Optional[str]
    consumption_type: Optional[ConsumptionType]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BOMCreate(BaseModel):
    """Création d'une nomenclature."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    version: str = "1.0"
    product_id: UUID
    quantity: Decimal = Decimal("1")
    unit: str = "UNIT"
    type: BOMType = BOMType.MANUFACTURING
    routing_id: Optional[UUID] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_default: bool = False
    allow_alternatives: bool = True
    consumption_type: ConsumptionType = ConsumptionType.AUTO_ON_COMPLETE
    notes: Optional[str] = None
    lines: List[BOMLineCreate] = Field(default_factory=list)


class BOMUpdate(BaseModel):
    """Mise à jour d'une nomenclature."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BOMStatus] = None
    routing_id: Optional[UUID] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_default: Optional[bool] = None
    allow_alternatives: Optional[bool] = None
    consumption_type: Optional[ConsumptionType] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class BOMResponse(BaseModel):
    """Réponse nomenclature."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    version: str
    product_id: UUID
    quantity: Decimal
    unit: str
    type: BOMType
    status: BOMStatus
    routing_id: Optional[UUID]
    valid_from: Optional[date]
    valid_to: Optional[date]
    material_cost: Decimal
    labor_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    currency: str
    is_default: bool
    allow_alternatives: bool
    consumption_type: ConsumptionType
    is_active: bool
    lines: List[BOMLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BOMList(BaseModel):
    """Liste de nomenclatures."""
    items: List[BOMResponse]
    total: int


# ============================================================================
# GAMMES DE FABRICATION
# ============================================================================

class RoutingOperationCreate(BaseModel):
    """Création d'une opération de gamme."""
    sequence: int
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: OperationType = OperationType.PRODUCTION
    work_center_id: Optional[UUID] = None
    setup_time: Decimal = Decimal("0")
    operation_time: Decimal = Decimal("0")
    cleanup_time: Decimal = Decimal("0")
    wait_time: Decimal = Decimal("0")
    batch_size: Decimal = Decimal("1")
    labor_cost_per_hour: Decimal = Decimal("0")
    machine_cost_per_hour: Decimal = Decimal("0")
    is_subcontracted: bool = False
    subcontractor_id: Optional[UUID] = None
    requires_quality_check: bool = False
    skill_required: Optional[str] = None
    notes: Optional[str] = None


class RoutingOperationResponse(BaseModel):
    """Réponse opération de gamme."""
    id: UUID
    routing_id: UUID
    sequence: int
    code: str
    name: str
    description: Optional[str]
    type: OperationType
    work_center_id: Optional[UUID]
    setup_time: Decimal
    operation_time: Decimal
    cleanup_time: Decimal
    wait_time: Decimal
    batch_size: Decimal
    labor_cost_per_hour: Decimal
    machine_cost_per_hour: Decimal
    is_subcontracted: bool
    subcontractor_id: Optional[UUID]
    requires_quality_check: bool
    skill_required: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RoutingCreate(BaseModel):
    """Création d'une gamme de fabrication."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    version: str = "1.0"
    product_id: Optional[UUID] = None
    notes: Optional[str] = None
    operations: List[RoutingOperationCreate] = Field(default_factory=list)


class RoutingUpdate(BaseModel):
    """Mise à jour d'une gamme."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BOMStatus] = None
    product_id: Optional[UUID] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class RoutingResponse(BaseModel):
    """Réponse gamme de fabrication."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    version: str
    product_id: Optional[UUID]
    status: BOMStatus
    total_setup_time: Decimal
    total_operation_time: Decimal
    total_time: Decimal
    total_labor_cost: Decimal
    total_machine_cost: Decimal
    currency: str
    is_active: bool
    operations: List[RoutingOperationResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ORDRES DE FABRICATION
# ============================================================================

class MOCreate(BaseModel):
    """Création d'un ordre de fabrication."""
    name: Optional[str] = None
    product_id: UUID
    bom_id: Optional[UUID] = None
    routing_id: Optional[UUID] = None
    quantity_planned: Decimal
    unit: str = "UNIT"
    priority: MOPriority = MOPriority.NORMAL
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    deadline: Optional[datetime] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    origin_type: Optional[str] = None
    origin_id: Optional[UUID] = None
    origin_number: Optional[str] = None
    responsible_id: Optional[UUID] = None
    notes: Optional[str] = None


class MOUpdate(BaseModel):
    """Mise à jour d'un ordre de fabrication."""
    name: Optional[str] = None
    priority: Optional[MOPriority] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    deadline: Optional[datetime] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    responsible_id: Optional[UUID] = None
    notes: Optional[str] = None


class WorkOrderResponse(BaseModel):
    """Réponse ordre de travail."""
    id: UUID
    mo_id: UUID
    sequence: int
    name: str
    description: Optional[str]
    operation_id: Optional[UUID]
    work_center_id: Optional[UUID]
    status: WorkOrderStatus
    quantity_planned: Decimal
    quantity_done: Decimal
    quantity_scrapped: Decimal
    setup_time_planned: Decimal
    operation_time_planned: Decimal
    setup_time_actual: Decimal
    operation_time_actual: Decimal
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    operator_id: Optional[UUID]
    labor_cost: Decimal
    machine_cost: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsumptionResponse(BaseModel):
    """Réponse consommation matière."""
    id: UUID
    mo_id: UUID
    product_id: UUID
    bom_line_id: Optional[UUID]
    work_order_id: Optional[UUID]
    quantity_planned: Decimal
    quantity_consumed: Decimal
    quantity_returned: Decimal
    unit: str
    lot_id: Optional[UUID]
    serial_id: Optional[UUID]
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    unit_cost: Decimal
    total_cost: Decimal
    consumed_at: Optional[datetime]
    consumed_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class MOResponse(BaseModel):
    """Réponse ordre de fabrication."""
    id: UUID
    number: str
    name: Optional[str]
    product_id: UUID
    bom_id: Optional[UUID]
    routing_id: Optional[UUID]
    quantity_planned: Decimal
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    unit: str
    status: MOStatus
    priority: MOPriority
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    deadline: Optional[datetime]
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    origin_type: Optional[str]
    origin_id: Optional[UUID]
    origin_number: Optional[str]
    planned_cost: Decimal
    actual_cost: Decimal
    material_cost: Decimal
    labor_cost: Decimal
    overhead_cost: Decimal
    currency: str
    responsible_id: Optional[UUID]
    progress_percent: Decimal
    work_orders: List[WorkOrderResponse] = Field(default_factory=list)
    consumptions: List[ConsumptionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MOList(BaseModel):
    """Liste d'ordres de fabrication."""
    items: List[MOResponse]
    total: int


# ============================================================================
# ORDRES DE TRAVAIL
# ============================================================================

class WorkOrderUpdate(BaseModel):
    """Mise à jour d'un ordre de travail."""
    work_center_id: Optional[UUID] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    operator_id: Optional[UUID] = None
    notes: Optional[str] = None


class StartWorkOrderRequest(BaseModel):
    """Démarrage d'un ordre de travail."""
    operator_id: Optional[UUID] = None


class CompleteWorkOrderRequest(BaseModel):
    """Complétion d'un ordre de travail."""
    quantity_done: Decimal
    quantity_scrapped: Decimal = Decimal("0")
    scrap_reason: Optional[ScrapReason] = None
    notes: Optional[str] = None


class TimeEntryCreate(BaseModel):
    """Création d'une saisie de temps."""
    work_order_id: UUID
    entry_type: str = "PRODUCTION"
    operator_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    quantity_produced: Decimal = Decimal("0")
    quantity_scrapped: Decimal = Decimal("0")
    scrap_reason: Optional[ScrapReason] = None
    notes: Optional[str] = None


class TimeEntryResponse(BaseModel):
    """Réponse saisie de temps."""
    id: UUID
    work_order_id: UUID
    entry_type: str
    operator_id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[Decimal]
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    scrap_reason: Optional[ScrapReason]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CONSOMMATION
# ============================================================================

class ConsumeRequest(BaseModel):
    """Demande de consommation de matière."""
    product_id: UUID
    quantity: Decimal
    lot_id: Optional[UUID] = None
    serial_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    work_order_id: Optional[UUID] = None
    notes: Optional[str] = None


class ReturnRequest(BaseModel):
    """Demande de retour de matière."""
    consumption_id: UUID
    quantity: Decimal
    notes: Optional[str] = None


# ============================================================================
# PRODUCTION OUTPUT
# ============================================================================

class ProduceRequest(BaseModel):
    """Demande de déclaration de production."""
    quantity: Decimal
    lot_id: Optional[UUID] = None
    serial_ids: Optional[List[UUID]] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    work_order_id: Optional[UUID] = None
    is_quality_passed: bool = True
    quality_notes: Optional[str] = None
    notes: Optional[str] = None


class OutputResponse(BaseModel):
    """Réponse sortie de production."""
    id: UUID
    mo_id: UUID
    work_order_id: Optional[UUID]
    product_id: UUID
    quantity: Decimal
    unit: str
    lot_id: Optional[UUID]
    serial_ids: Optional[List[UUID]]
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    is_quality_passed: bool
    quality_notes: Optional[str]
    unit_cost: Decimal
    total_cost: Decimal
    produced_at: datetime
    produced_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator('serial_ids', mode='before')
    @classmethod
    def parse_serial_ids(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


# ============================================================================
# REBUTS
# ============================================================================

class ScrapCreate(BaseModel):
    """Déclaration de rebut."""
    mo_id: Optional[UUID] = None
    work_order_id: Optional[UUID] = None
    product_id: UUID
    quantity: Decimal
    unit: str = "UNIT"
    lot_id: Optional[UUID] = None
    serial_id: Optional[UUID] = None
    reason: ScrapReason = ScrapReason.DEFECT
    reason_detail: Optional[str] = None
    work_center_id: Optional[UUID] = None
    notes: Optional[str] = None


class ScrapResponse(BaseModel):
    """Réponse rebut."""
    id: UUID
    mo_id: Optional[UUID]
    work_order_id: Optional[UUID]
    product_id: UUID
    quantity: Decimal
    unit: str
    lot_id: Optional[UUID]
    serial_id: Optional[UUID]
    reason: ScrapReason
    reason_detail: Optional[str]
    work_center_id: Optional[UUID]
    unit_cost: Decimal
    total_cost: Decimal
    scrapped_at: datetime
    scrapped_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PLANIFICATION
# ============================================================================

class PlanLineCreate(BaseModel):
    """Création d'une ligne de plan."""
    product_id: UUID
    bom_id: Optional[UUID] = None
    quantity_demanded: Decimal
    required_date: Optional[date] = None
    priority: MOPriority = MOPriority.NORMAL
    notes: Optional[str] = None


class PlanLineResponse(BaseModel):
    """Réponse ligne de plan."""
    id: UUID
    plan_id: UUID
    product_id: UUID
    bom_id: Optional[UUID]
    quantity_demanded: Decimal
    quantity_available: Decimal
    quantity_to_produce: Decimal
    required_date: Optional[date]
    planned_start: Optional[date]
    planned_end: Optional[date]
    mo_id: Optional[UUID]
    priority: MOPriority
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PlanCreate(BaseModel):
    """Création d'un plan de production."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    planning_horizon_days: int = 30
    planning_method: str = "MRP"
    notes: Optional[str] = None
    lines: List[PlanLineCreate] = Field(default_factory=list)


class PlanResponse(BaseModel):
    """Réponse plan de production."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    start_date: date
    end_date: date
    planning_horizon_days: int
    status: str
    planning_method: str
    total_orders: int
    total_quantity: Decimal
    total_hours: Decimal
    generated_at: Optional[datetime]
    approved_at: Optional[datetime]
    approved_by: Optional[UUID]
    lines: List[PlanLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# MAINTENANCE
# ============================================================================

class MaintenanceScheduleCreate(BaseModel):
    """Création d'un calendrier de maintenance."""
    work_center_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    frequency_type: str  # DAILY, WEEKLY, MONTHLY, HOURS, CYCLES
    frequency_value: int = 1
    duration_hours: Decimal = Decimal("1")
    notes: Optional[str] = None


class MaintenanceScheduleResponse(BaseModel):
    """Réponse calendrier maintenance."""
    id: UUID
    work_center_id: UUID
    name: str
    description: Optional[str]
    frequency_type: str
    frequency_value: int
    duration_hours: Decimal
    last_maintenance: Optional[datetime]
    next_maintenance: Optional[datetime]
    cycles_since_last: int
    hours_since_last: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD
# ============================================================================

class ProductionDashboard(BaseModel):
    """Dashboard Production."""
    # Ordres de fabrication
    total_orders: int = 0
    orders_draft: int = 0
    orders_confirmed: int = 0
    orders_in_progress: int = 0
    orders_done_today: int = 0
    orders_done_this_week: int = 0
    orders_late: int = 0

    # Production
    quantity_produced_today: Decimal = Decimal("0")
    quantity_produced_this_week: Decimal = Decimal("0")
    quantity_scrapped_today: Decimal = Decimal("0")
    scrap_rate: Decimal = Decimal("0")

    # Centres de travail
    total_work_centers: int = 0
    work_centers_available: int = 0
    work_centers_busy: int = 0
    work_centers_maintenance: int = 0
    average_oee: Decimal = Decimal("0")

    # Coûts
    total_cost_this_month: Decimal = Decimal("0")
    material_cost_this_month: Decimal = Decimal("0")
    labor_cost_this_month: Decimal = Decimal("0")

    # Alertes
    low_material_alerts: int = 0
    maintenance_due: int = 0
    quality_issues: int = 0

    # Top produits
    top_products_produced: List[Dict[str, Any]] = Field(default_factory=list)

    # Ordres urgents
    urgent_orders: List[Dict[str, Any]] = Field(default_factory=list)
