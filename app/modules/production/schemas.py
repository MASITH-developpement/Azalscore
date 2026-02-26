"""
AZALS MODULE M6 - Schémas Production
=====================================

Schémas Pydantic pour la gestion de production.
"""
from __future__ import annotations



import json
import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    BOMStatus,
    BOMType,
    ConsumptionType,
    MOPriority,
    MOStatus,
    OperationType,
    ScrapReason,
    WorkCenterStatus,
    WorkCenterType,
    WorkOrderStatus,
)

# ============================================================================
# CENTRES DE TRAVAIL
# ============================================================================

class WorkCenterCreate(BaseModel):
    """Création d'un centre de travail."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    work_center_type: WorkCenterType = Field(default=WorkCenterType.MACHINE, alias="type")
    warehouse_id: UUID | None = None
    location: str | None = None
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
    manager_id: UUID | None = None
    operator_ids: list[UUID] | None = None
    requires_approval: bool = False
    allow_parallel: bool = False
    notes: str | None = None


class WorkCenterUpdate(BaseModel):
    """Mise à jour d'un centre de travail."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    name: str | None = None
    description: str | None = None
    work_center_type: WorkCenterType | None = Field(default=None, alias="type")
    status: WorkCenterStatus | None = None
    warehouse_id: UUID | None = None
    location: str | None = None
    capacity: Decimal | None = None
    efficiency: Decimal | None = None
    oee_target: Decimal | None = None
    cost_per_hour: Decimal | None = None
    cost_per_cycle: Decimal | None = None
    working_hours_per_day: Decimal | None = None
    working_days_per_week: int | None = None
    manager_id: UUID | None = None
    operator_ids: list[UUID] | None = None
    requires_approval: bool | None = None
    allow_parallel: bool | None = None
    notes: str | None = None
    is_active: bool | None = None


class WorkCenterResponse(BaseModel):
    """Réponse centre de travail."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    code: str
    name: str
    description: str | None
    work_center_type: WorkCenterType = Field(..., alias="type")
    status: WorkCenterStatus
    warehouse_id: UUID | None
    location: str | None
    capacity: Decimal
    efficiency: Decimal
    oee_target: Decimal
    cost_per_hour: Decimal
    cost_per_cycle: Decimal
    currency: str
    working_hours_per_day: Decimal
    working_days_per_week: int
    manager_id: UUID | None
    operator_ids: list[UUID] | None
    requires_approval: bool
    allow_parallel: bool
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


    @field_validator('operator_ids', mode='before')
    @classmethod
    def parse_operator_ids(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


class WorkCenterCapacityCreate(BaseModel):
    """Création de capacité centre de travail."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    work_center_id: UUID
    capacity_date: datetime.date = Field(..., alias="date")
    shift: str = "DAY"
    available_hours: Decimal
    notes: str | None = None


class WorkCenterCapacityResponse(BaseModel):
    """Réponse capacité."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    id: UUID
    work_center_id: UUID
    capacity_date: datetime.date = Field(..., alias="date")
    shift: str
    available_hours: Decimal
    planned_hours: Decimal
    actual_hours: Decimal
    notes: str | None
    created_at: datetime.datetime



# ============================================================================
# NOMENCLATURES (BOM)
# ============================================================================

class BOMLineCreate(BaseModel):
    """Création d'une ligne de nomenclature."""
    product_id: UUID
    quantity: Decimal
    unit: str = "UNIT"
    operation_id: UUID | None = None
    scrap_rate: Decimal = Decimal("0")
    is_critical: bool = True
    alternative_group: str | None = None
    consumption_type: ConsumptionType | None = None
    notes: str | None = None


class BOMLineResponse(BaseModel):
    """Réponse ligne de nomenclature."""
    id: UUID
    bom_id: UUID
    line_number: int
    product_id: UUID
    quantity: Decimal
    unit: str
    operation_id: UUID | None
    scrap_rate: Decimal
    is_critical: bool
    alternative_group: str | None
    consumption_type: ConsumptionType | None
    notes: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class BOMCreate(BaseModel):
    """Création d'une nomenclature."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    version: str = "1.0"
    product_id: UUID
    quantity: Decimal = Decimal("1")
    unit: str = "UNIT"
    bom_type: BOMType = Field(default=BOMType.MANUFACTURING, alias="type")
    routing_id: UUID | None = None
    valid_from: datetime.date | None = None
    valid_to: datetime.date | None = None
    is_default: bool = False
    allow_alternatives: bool = True
    consumption_type: ConsumptionType = ConsumptionType.AUTO_ON_COMPLETE
    notes: str | None = None
    lines: list[BOMLineCreate] = Field(default_factory=list)


class BOMUpdate(BaseModel):
    """Mise à jour d'une nomenclature."""
    name: str | None = None
    description: str | None = None
    status: BOMStatus | None = None
    routing_id: UUID | None = None
    valid_from: datetime.date | None = None
    valid_to: datetime.date | None = None
    is_default: bool | None = None
    allow_alternatives: bool | None = None
    consumption_type: ConsumptionType | None = None
    notes: str | None = None
    is_active: bool | None = None


class BOMResponse(BaseModel):
    """Réponse nomenclature."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    code: str
    name: str
    description: str | None
    version: str
    product_id: UUID
    quantity: Decimal
    unit: str
    bom_type: BOMType = Field(..., alias="type")
    status: BOMStatus
    routing_id: UUID | None
    valid_from: datetime.date | None
    valid_to: datetime.date | None
    material_cost: Decimal
    labor_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    currency: str
    is_default: bool
    allow_alternatives: bool
    consumption_type: ConsumptionType
    is_active: bool
    lines: list[BOMLineResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime



class BOMList(BaseModel):
    """Liste de nomenclatures."""
    items: list[BOMResponse]
    total: int


# ============================================================================
# GAMMES DE FABRICATION
# ============================================================================

class RoutingOperationCreate(BaseModel):
    """Création d'une opération de gamme."""
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    sequence: int
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    operation_type: OperationType = Field(default=OperationType.PRODUCTION, alias="type")
    work_center_id: UUID | None = None
    setup_time: Decimal = Decimal("0")
    operation_time: Decimal = Decimal("0")
    cleanup_time: Decimal = Decimal("0")
    wait_time: Decimal = Decimal("0")
    batch_size: Decimal = Decimal("1")
    labor_cost_per_hour: Decimal = Decimal("0")
    machine_cost_per_hour: Decimal = Decimal("0")
    is_subcontracted: bool = False
    subcontractor_id: UUID | None = None
    requires_quality_check: bool = False
    skill_required: str | None = None
    notes: str | None = None


class RoutingOperationResponse(BaseModel):
    """Réponse opération de gamme."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    id: UUID
    routing_id: UUID
    sequence: int
    code: str
    name: str
    description: str | None
    operation_type: OperationType = Field(..., alias="type")
    work_center_id: UUID | None
    setup_time: Decimal
    operation_time: Decimal
    cleanup_time: Decimal
    wait_time: Decimal
    batch_size: Decimal
    labor_cost_per_hour: Decimal
    machine_cost_per_hour: Decimal
    is_subcontracted: bool
    subcontractor_id: UUID | None
    requires_quality_check: bool
    skill_required: str | None
    created_at: datetime.datetime



class RoutingCreate(BaseModel):
    """Création d'une gamme de fabrication."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    version: str = "1.0"
    product_id: UUID | None = None
    notes: str | None = None
    operations: list[RoutingOperationCreate] = Field(default_factory=list)


class RoutingUpdate(BaseModel):
    """Mise à jour d'une gamme."""
    name: str | None = None
    description: str | None = None
    status: BOMStatus | None = None
    product_id: UUID | None = None
    notes: str | None = None
    is_active: bool | None = None


class RoutingResponse(BaseModel):
    """Réponse gamme de fabrication."""
    id: UUID
    code: str
    name: str
    description: str | None
    version: str
    product_id: UUID | None
    status: BOMStatus
    total_setup_time: Decimal
    total_operation_time: Decimal
    total_time: Decimal
    total_labor_cost: Decimal
    total_machine_cost: Decimal
    currency: str
    is_active: bool
    operations: list[RoutingOperationResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ORDRES DE FABRICATION
# ============================================================================

class MOCreate(BaseModel):
    """Création d'un ordre de fabrication."""
    name: str | None = None
    product_id: UUID
    bom_id: UUID | None = None
    routing_id: UUID | None = None
    quantity_planned: Decimal
    unit: str = "UNIT"
    priority: MOPriority = MOPriority.NORMAL
    scheduled_start: datetime.datetime | None = None
    scheduled_end: datetime.datetime | None = None
    deadline: datetime.datetime | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    origin_type: str | None = None
    origin_id: UUID | None = None
    origin_number: str | None = None
    responsible_id: UUID | None = None
    notes: str | None = None


class MOUpdate(BaseModel):
    """Mise à jour d'un ordre de fabrication."""
    name: str | None = None
    priority: MOPriority | None = None
    scheduled_start: datetime.datetime | None = None
    scheduled_end: datetime.datetime | None = None
    deadline: datetime.datetime | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    responsible_id: UUID | None = None
    notes: str | None = None


class WorkOrderResponse(BaseModel):
    """Réponse ordre de travail."""
    id: UUID
    mo_id: UUID
    sequence: int
    name: str
    description: str | None
    operation_id: UUID | None
    work_center_id: UUID | None
    status: WorkOrderStatus
    quantity_planned: Decimal
    quantity_done: Decimal
    quantity_scrapped: Decimal
    setup_time_planned: Decimal
    operation_time_planned: Decimal
    setup_time_actual: Decimal
    operation_time_actual: Decimal
    scheduled_start: datetime.datetime | None
    scheduled_end: datetime.datetime | None
    actual_start: datetime.datetime | None
    actual_end: datetime.datetime | None
    operator_id: UUID | None
    labor_cost: Decimal
    machine_cost: Decimal
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConsumptionResponse(BaseModel):
    """Réponse consommation matière."""
    id: UUID
    mo_id: UUID
    product_id: UUID
    bom_line_id: UUID | None
    work_order_id: UUID | None
    quantity_planned: Decimal
    quantity_consumed: Decimal
    quantity_returned: Decimal
    unit: str
    lot_id: UUID | None
    serial_id: UUID | None
    warehouse_id: UUID | None
    location_id: UUID | None
    unit_cost: Decimal
    total_cost: Decimal
    consumed_at: datetime.datetime | None
    consumed_by: UUID | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MOResponse(BaseModel):
    """Réponse ordre de fabrication."""
    id: UUID
    number: str
    name: str | None
    product_id: UUID
    bom_id: UUID | None
    routing_id: UUID | None
    quantity_planned: Decimal
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    unit: str
    status: MOStatus
    priority: MOPriority
    scheduled_start: datetime.datetime | None
    scheduled_end: datetime.datetime | None
    actual_start: datetime.datetime | None
    actual_end: datetime.datetime | None
    deadline: datetime.datetime | None
    warehouse_id: UUID | None
    location_id: UUID | None
    origin_type: str | None
    origin_id: UUID | None
    origin_number: str | None
    planned_cost: Decimal
    actual_cost: Decimal
    material_cost: Decimal
    labor_cost: Decimal
    overhead_cost: Decimal
    currency: str
    responsible_id: UUID | None
    progress_percent: Decimal
    work_orders: list[WorkOrderResponse] = Field(default_factory=list)
    consumptions: list[ConsumptionResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MOList(BaseModel):
    """Liste d'ordres de fabrication."""
    items: list[MOResponse]
    total: int


# ============================================================================
# ORDRES DE TRAVAIL
# ============================================================================

class WorkOrderUpdate(BaseModel):
    """Mise à jour d'un ordre de travail."""
    work_center_id: UUID | None = None
    scheduled_start: datetime.datetime | None = None
    scheduled_end: datetime.datetime | None = None
    operator_id: UUID | None = None
    notes: str | None = None


class StartWorkOrderRequest(BaseModel):
    """Démarrage d'un ordre de travail."""
    operator_id: UUID | None = None


class CompleteWorkOrderRequest(BaseModel):
    """Complétion d'un ordre de travail."""
    quantity_done: Decimal
    quantity_scrapped: Decimal = Decimal("0")
    scrap_reason: ScrapReason | None = None
    notes: str | None = None


class TimeEntryCreate(BaseModel):
    """Création d'une saisie de temps."""
    work_order_id: UUID
    entry_type: str = "PRODUCTION"
    operator_id: UUID
    start_time: datetime.datetime
    end_time: datetime.datetime | None = None
    quantity_produced: Decimal = Decimal("0")
    quantity_scrapped: Decimal = Decimal("0")
    scrap_reason: ScrapReason | None = None
    notes: str | None = None


class TimeEntryResponse(BaseModel):
    """Réponse saisie de temps."""
    id: UUID
    work_order_id: UUID
    entry_type: str
    operator_id: UUID
    start_time: datetime.datetime
    end_time: datetime.datetime | None
    duration_minutes: Decimal | None
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    scrap_reason: ScrapReason | None
    notes: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONSOMMATION
# ============================================================================

class ConsumeRequest(BaseModel):
    """Demande de consommation de matière."""
    product_id: UUID
    quantity: Decimal
    lot_id: UUID | None = None
    serial_id: UUID | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    work_order_id: UUID | None = None
    notes: str | None = None


class ReturnRequest(BaseModel):
    """Demande de retour de matière."""
    consumption_id: UUID
    quantity: Decimal
    notes: str | None = None


# ============================================================================
# PRODUCTION OUTPUT
# ============================================================================

class ProduceRequest(BaseModel):
    """Demande de déclaration de production."""
    quantity: Decimal
    lot_id: UUID | None = None
    serial_ids: list[UUID] | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    work_order_id: UUID | None = None
    is_quality_passed: bool = True
    quality_notes: str | None = None
    notes: str | None = None


class OutputResponse(BaseModel):
    """Réponse sortie de production."""
    id: UUID
    mo_id: UUID
    work_order_id: UUID | None
    product_id: UUID
    quantity: Decimal
    unit: str
    lot_id: UUID | None
    serial_ids: list[UUID] | None
    warehouse_id: UUID | None
    location_id: UUID | None
    is_quality_passed: bool
    quality_notes: str | None
    unit_cost: Decimal
    total_cost: Decimal
    produced_at: datetime.datetime
    produced_by: UUID | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

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
    mo_id: UUID | None = None
    work_order_id: UUID | None = None
    product_id: UUID
    quantity: Decimal
    unit: str = "UNIT"
    lot_id: UUID | None = None
    serial_id: UUID | None = None
    reason: ScrapReason = ScrapReason.DEFECT
    reason_detail: str | None = None
    work_center_id: UUID | None = None
    notes: str | None = None


class ScrapResponse(BaseModel):
    """Réponse rebut."""
    id: UUID
    mo_id: UUID | None
    work_order_id: UUID | None
    product_id: UUID
    quantity: Decimal
    unit: str
    lot_id: UUID | None
    serial_id: UUID | None
    reason: ScrapReason
    reason_detail: str | None
    work_center_id: UUID | None
    unit_cost: Decimal
    total_cost: Decimal
    scrapped_at: datetime.datetime
    scrapped_by: UUID | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PLANIFICATION
# ============================================================================

class PlanLineCreate(BaseModel):
    """Création d'une ligne de plan."""
    product_id: UUID
    bom_id: UUID | None = None
    quantity_demanded: Decimal
    required_date: datetime.date | None = None
    priority: MOPriority = MOPriority.NORMAL
    notes: str | None = None


class PlanLineResponse(BaseModel):
    """Réponse ligne de plan."""
    id: UUID
    plan_id: UUID
    product_id: UUID
    bom_id: UUID | None
    quantity_demanded: Decimal
    quantity_available: Decimal
    quantity_to_produce: Decimal
    required_date: datetime.date | None
    planned_start: datetime.date | None
    planned_end: datetime.date | None
    mo_id: UUID | None
    priority: MOPriority
    notes: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PlanCreate(BaseModel):
    """Création d'un plan de production."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_date: datetime.date
    end_date: datetime.date
    planning_horizon_days: int = 30
    planning_method: str = "MRP"
    notes: str | None = None
    lines: list[PlanLineCreate] = Field(default_factory=list)


class PlanResponse(BaseModel):
    """Réponse plan de production."""
    id: UUID
    code: str
    name: str
    description: str | None
    start_date: datetime.date
    end_date: datetime.date
    planning_horizon_days: int
    status: str
    planning_method: str
    total_orders: int
    total_quantity: Decimal
    total_hours: Decimal
    generated_at: datetime.datetime | None
    approved_at: datetime.datetime | None
    approved_by: UUID | None
    lines: list[PlanLineResponse] = Field(default_factory=list)
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MAINTENANCE
# ============================================================================

class MaintenanceScheduleCreate(BaseModel):
    """Création d'un calendrier de maintenance."""
    work_center_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    frequency_type: str  # DAILY, WEEKLY, MONTHLY, HOURS, CYCLES
    frequency_value: int = 1
    duration_hours: Decimal = Decimal("1")
    notes: str | None = None


class MaintenanceScheduleResponse(BaseModel):
    """Réponse calendrier maintenance."""
    id: UUID
    work_center_id: UUID
    name: str
    description: str | None
    frequency_type: str
    frequency_value: int
    duration_hours: Decimal
    last_maintenance: datetime.datetime | None
    next_maintenance: datetime.datetime | None
    cycles_since_last: int
    hours_since_last: Decimal
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


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
    top_products_produced: list[dict[str, Any]] = Field(default_factory=list)

    # Ordres urgents
    urgent_orders: list[dict[str, Any]] = Field(default_factory=list)
