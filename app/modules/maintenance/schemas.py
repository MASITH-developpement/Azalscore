"""
AZALS MODULE M8 - Schémas Pydantic Maintenance
==============================================

Schémas de validation pour les API du module Maintenance (GMAO).
"""
from __future__ import annotations



import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# ENUMS
# ============================================================================

class AssetCategoryEnum(str, Enum):
    MACHINE = "MACHINE"
    EQUIPMENT = "EQUIPMENT"
    VEHICLE = "VEHICLE"
    BUILDING = "BUILDING"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    TOOL = "TOOL"
    UTILITY = "UTILITY"
    FURNITURE = "FURNITURE"
    OTHER = "OTHER"


class AssetStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_MAINTENANCE = "IN_MAINTENANCE"
    RESERVED = "RESERVED"
    DISPOSED = "DISPOSED"
    UNDER_REPAIR = "UNDER_REPAIR"
    STANDBY = "STANDBY"


class AssetCriticalityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MaintenanceTypeEnum(str, Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    PREDICTIVE = "PREDICTIVE"
    CONDITION_BASED = "CONDITION_BASED"
    BREAKDOWN = "BREAKDOWN"
    IMPROVEMENT = "IMPROVEMENT"
    INSPECTION = "INSPECTION"
    CALIBRATION = "CALIBRATION"


class WorkOrderStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    PLANNED = "PLANNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class WorkOrderPriorityEnum(str, Enum):
    EMERGENCY = "EMERGENCY"
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SCHEDULED = "SCHEDULED"


class FailureTypeEnum(str, Enum):
    MECHANICAL = "MECHANICAL"
    ELECTRICAL = "ELECTRICAL"
    ELECTRONIC = "ELECTRONIC"
    HYDRAULIC = "HYDRAULIC"
    PNEUMATIC = "PNEUMATIC"
    SOFTWARE = "SOFTWARE"
    OPERATOR_ERROR = "OPERATOR_ERROR"
    WEAR = "WEAR"
    CONTAMINATION = "CONTAMINATION"
    UNKNOWN = "UNKNOWN"


class PartRequestStatusEnum(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    ISSUED = "ISSUED"
    CANCELLED = "CANCELLED"


class ContractTypeEnum(str, Enum):
    FULL_SERVICE = "FULL_SERVICE"
    PREVENTIVE = "PREVENTIVE"
    ON_CALL = "ON_CALL"
    PARTS_ONLY = "PARTS_ONLY"
    LABOR_ONLY = "LABOR_ONLY"
    WARRANTY = "WARRANTY"


class ContractStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"


# ============================================================================
# ACTIFS
# ============================================================================

class AssetBase(BaseModel):
    asset_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    category: AssetCategoryEnum
    asset_type: str | None = None


class AssetCreate(AssetBase):
    parent_id: int | None = None
    criticality: AssetCriticalityEnum = AssetCriticalityEnum.MEDIUM
    location_id: int | None = None
    location_description: str | None = None
    building: str | None = None
    floor: str | None = None
    area: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    year_manufactured: int | None = None
    purchase_date: datetime.date | None = None
    installation_date: datetime.date | None = None
    warranty_end_date: datetime.date | None = None
    purchase_cost: Decimal | None = None
    replacement_cost: Decimal | None = None
    specifications: dict[str, Any] | None = None
    power_rating: str | None = None
    supplier_id: int | None = None
    responsible_id: int | None = None
    department: str | None = None
    maintenance_strategy: str | None = None
    notes: str | None = None


class AssetUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    category: AssetCategoryEnum | None = None
    asset_type: str | None = None
    status: AssetStatusEnum | None = None
    criticality: AssetCriticalityEnum | None = None
    parent_id: int | None = None
    location_description: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    specifications: dict[str, Any] | None = None
    responsible_id: int | None = None
    department: str | None = None
    maintenance_strategy: str | None = None
    notes: str | None = None


class AssetResponse(AssetBase):
    id: int
    status: AssetStatusEnum
    criticality: AssetCriticalityEnum
    parent_id: int | None = None
    location_id: int | None = None
    location_description: str | None = None
    building: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    year_manufactured: int | None = None
    purchase_date: datetime.date | None = None
    installation_date: datetime.date | None = None
    warranty_end_date: datetime.date | None = None
    last_maintenance_date: datetime.date | None = None
    next_maintenance_date: datetime.date | None = None
    purchase_cost: Decimal | None = None
    current_value: Decimal | None = None
    operating_hours: Decimal | None = None
    specifications: dict[str, Any] | None = None
    supplier_id: int | None = None
    responsible_id: int | None = None
    department: str | None = None
    maintenance_strategy: str | None = None
    mtbf_hours: Decimal | None = None
    mttr_hours: Decimal | None = None
    availability_rate: Decimal | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# COMPTEURS
# ============================================================================

class MeterBase(BaseModel):
    meter_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    meter_type: str = Field(..., min_length=2, max_length=50)
    unit: str = Field(..., min_length=1, max_length=50)


class MeterCreate(MeterBase):
    initial_reading: Decimal = Decimal("0")
    alert_threshold: Decimal | None = None
    critical_threshold: Decimal | None = None
    maintenance_trigger_value: Decimal | None = None


class MeterResponse(MeterBase):
    id: int
    asset_id: int
    current_reading: Decimal
    last_reading_date: datetime.datetime | None = None
    initial_reading: Decimal
    alert_threshold: Decimal | None = None
    critical_threshold: Decimal | None = None
    maintenance_trigger_value: Decimal | None = None
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MeterReadingCreate(BaseModel):
    reading_value: Decimal
    source: str = "MANUAL"
    notes: str | None = None


class MeterReadingResponse(BaseModel):
    id: int
    meter_id: int
    reading_date: datetime.datetime
    reading_value: Decimal
    delta: Decimal | None = None
    source: str | None = None
    notes: str | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PLANS DE MAINTENANCE
# ============================================================================

class PlanTaskBase(BaseModel):
    sequence: int
    task_code: str | None = None
    description: str = Field(..., min_length=5)
    detailed_instructions: str | None = None
    estimated_duration_minutes: int | None = None
    required_skill: str | None = None
    is_mandatory: bool = True


class PlanTaskCreate(PlanTaskBase):
    required_parts: list[dict[str, Any]] | None = None
    check_points: list[str] | None = None


class PlanTaskResponse(PlanTaskBase):
    id: int
    plan_id: int
    required_parts: list[dict[str, Any]] | None = None
    check_points: list[str] | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MaintenancePlanBase(BaseModel):
    plan_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    maintenance_type: MaintenanceTypeEnum


class MaintenancePlanCreate(MaintenancePlanBase):
    asset_id: int | None = None
    asset_category: AssetCategoryEnum | None = None
    trigger_type: str = "TIME"
    frequency_value: int | None = None
    frequency_unit: str | None = None
    trigger_meter_id: int | None = None
    trigger_meter_interval: Decimal | None = None
    lead_time_days: int = 7
    estimated_duration_hours: Decimal | None = None
    responsible_id: int | None = None
    estimated_labor_cost: Decimal | None = None
    estimated_parts_cost: Decimal | None = None
    instructions: str | None = None
    safety_instructions: str | None = None
    required_tools: list[str] | None = None
    tasks: list[PlanTaskCreate] | None = None


class MaintenancePlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    frequency_value: int | None = None
    frequency_unit: str | None = None
    lead_time_days: int | None = None
    estimated_duration_hours: Decimal | None = None
    responsible_id: int | None = None
    instructions: str | None = None
    safety_instructions: str | None = None
    is_active: bool | None = None


class MaintenancePlanResponse(MaintenancePlanBase):
    id: int
    asset_id: int | None = None
    asset_category: AssetCategoryEnum | None = None
    trigger_type: str
    frequency_value: int | None = None
    frequency_unit: str | None = None
    trigger_meter_id: int | None = None
    trigger_meter_interval: Decimal | None = None
    last_execution_date: datetime.date | None = None
    next_due_date: datetime.date | None = None
    lead_time_days: int
    estimated_duration_hours: Decimal | None = None
    responsible_id: int | None = None
    is_active: bool
    estimated_labor_cost: Decimal | None = None
    estimated_parts_cost: Decimal | None = None
    instructions: str | None = None
    safety_instructions: str | None = None
    required_tools: list[str] | None = None
    tasks: list[PlanTaskResponse] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ORDRES DE TRAVAIL
# ============================================================================

class WorkOrderTaskCreate(BaseModel):
    sequence: int
    description: str = Field(..., min_length=5)
    instructions: str | None = None
    estimated_minutes: int | None = None


class WorkOrderTaskResponse(BaseModel):
    id: int
    work_order_id: int
    sequence: int
    description: str
    instructions: str | None = None
    estimated_minutes: int | None = None
    actual_minutes: int | None = None
    status: str
    completed_date: datetime.datetime | None = None
    result: str | None = None
    issues_found: str | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkOrderLaborCreate(BaseModel):
    technician_id: int
    work_date: datetime.date
    hours_worked: Decimal
    overtime_hours: Decimal = Decimal("0")
    labor_type: str = "REGULAR"
    hourly_rate: Decimal | None = None
    work_description: str | None = None


class WorkOrderLaborResponse(BaseModel):
    id: int
    work_order_id: int
    technician_id: int
    technician_name: str | None = None
    work_date: datetime.date
    hours_worked: Decimal
    overtime_hours: Decimal
    labor_type: str | None = None
    hourly_rate: Decimal | None = None
    total_cost: Decimal | None = None
    work_description: str | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class WorkOrderPartCreate(BaseModel):
    spare_part_id: int | None = None
    part_description: str = Field(..., min_length=2, max_length=300)
    quantity_used: Decimal
    unit: str | None = None
    unit_cost: Decimal | None = None
    source: str = "STOCK"
    notes: str | None = None


class WorkOrderPartResponse(BaseModel):
    id: int
    work_order_id: int
    spare_part_id: int | None = None
    part_code: str | None = None
    part_description: str
    quantity_planned: Decimal | None = None
    quantity_used: Decimal
    unit: str | None = None
    unit_cost: Decimal | None = None
    total_cost: Decimal | None = None
    source: str | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class WorkOrderBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str | None = None
    maintenance_type: MaintenanceTypeEnum
    asset_id: int


class WorkOrderCreate(WorkOrderBase):
    component_id: int | None = None
    priority: WorkOrderPriorityEnum = WorkOrderPriorityEnum.MEDIUM
    maintenance_plan_id: int | None = None
    failure_id: int | None = None
    requester_id: int | None = None
    request_description: str | None = None
    scheduled_start_date: datetime.datetime | None = None
    scheduled_end_date: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    assigned_to_id: int | None = None
    external_vendor_id: int | None = None
    work_instructions: str | None = None
    safety_precautions: str | None = None
    tools_required: list[str] | None = None
    location_description: str | None = None
    estimated_labor_hours: Decimal | None = None
    estimated_parts_cost: Decimal | None = None
    tasks: list[WorkOrderTaskCreate] | None = None


class WorkOrderUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=300)
    description: str | None = None
    priority: WorkOrderPriorityEnum | None = None
    status: WorkOrderStatusEnum | None = None
    scheduled_start_date: datetime.datetime | None = None
    scheduled_end_date: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    assigned_to_id: int | None = None
    external_vendor_id: int | None = None
    work_instructions: str | None = None
    safety_precautions: str | None = None
    location_description: str | None = None
    notes: str | None = None


class WorkOrderComplete(BaseModel):
    completion_notes: str = Field(..., min_length=10)
    meter_reading_end: Decimal | None = None


class WorkOrderResponse(WorkOrderBase):
    id: int
    wo_number: str
    priority: WorkOrderPriorityEnum
    status: WorkOrderStatusEnum
    component_id: int | None = None
    source: str | None = None
    source_reference: str | None = None
    maintenance_plan_id: int | None = None
    failure_id: int | None = None
    requester_id: int | None = None
    request_date: datetime.datetime | None = None
    request_description: str | None = None
    scheduled_start_date: datetime.datetime | None = None
    scheduled_end_date: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    actual_start_date: datetime.datetime | None = None
    actual_end_date: datetime.datetime | None = None
    downtime_hours: Decimal | None = None
    assigned_to_id: int | None = None
    external_vendor_id: int | None = None
    work_instructions: str | None = None
    safety_precautions: str | None = None
    tools_required: list[str] | None = None
    location_description: str | None = None
    completion_notes: str | None = None
    completed_by_id: int | None = None
    verification_required: bool
    verified_by_id: int | None = None
    verified_date: datetime.datetime | None = None
    estimated_labor_hours: Decimal | None = None
    estimated_labor_cost: Decimal | None = None
    estimated_parts_cost: Decimal | None = None
    actual_labor_hours: Decimal | None = None
    actual_labor_cost: Decimal | None = None
    actual_parts_cost: Decimal | None = None
    meter_reading_end: Decimal | None = None
    notes: str | None = None
    tasks: list[WorkOrderTaskResponse] = []
    labor_entries: list[WorkOrderLaborResponse] = []
    parts_used: list[WorkOrderPartResponse] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PANNES
# ============================================================================

class FailureBase(BaseModel):
    asset_id: int
    failure_type: FailureTypeEnum
    description: str = Field(..., min_length=10)
    failure_date: datetime.datetime


class FailureCreate(FailureBase):
    component_id: int | None = None
    symptoms: str | None = None
    production_stopped: bool = False
    downtime_hours: Decimal | None = None
    meter_reading: Decimal | None = None
    notes: str | None = None


class FailureUpdate(BaseModel):
    description: str | None = None
    symptoms: str | None = None
    production_stopped: bool | None = None
    downtime_hours: Decimal | None = None
    estimated_cost_impact: Decimal | None = None
    resolution: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    status: str | None = None
    notes: str | None = None


class FailureResponse(FailureBase):
    id: int
    failure_number: str
    component_id: int | None = None
    symptoms: str | None = None
    detected_date: datetime.datetime | None = None
    reported_date: datetime.datetime | None = None
    resolved_date: datetime.datetime | None = None
    production_stopped: bool
    downtime_hours: Decimal | None = None
    production_loss_units: Decimal | None = None
    estimated_cost_impact: Decimal | None = None
    reported_by_id: int | None = None
    work_order_id: int | None = None
    resolution: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    meter_reading: Decimal | None = None
    status: str
    notes: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PIÈCES DE RECHANGE
# ============================================================================

class SparePartBase(BaseModel):
    part_code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=300)
    description: str | None = None
    category: str | None = None


class SparePartCreate(SparePartBase):
    manufacturer: str | None = None
    manufacturer_part_number: str | None = None
    preferred_supplier_id: int | None = None
    unit: str = "PCE"
    unit_cost: Decimal | None = None
    min_stock_level: Decimal = Decimal("0")
    max_stock_level: Decimal | None = None
    reorder_point: Decimal | None = None
    reorder_quantity: Decimal | None = None
    lead_time_days: int | None = None
    criticality: AssetCriticalityEnum | None = None
    shelf_life_days: int | None = None
    product_id: int | None = None
    notes: str | None = None
    specifications: dict[str, Any] | None = None


class SparePartUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=300)
    description: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    preferred_supplier_id: int | None = None
    unit_cost: Decimal | None = None
    min_stock_level: Decimal | None = None
    max_stock_level: Decimal | None = None
    reorder_point: Decimal | None = None
    lead_time_days: int | None = None
    criticality: AssetCriticalityEnum | None = None
    is_active: bool | None = None
    notes: str | None = None


class SparePartResponse(SparePartBase):
    id: int
    manufacturer: str | None = None
    manufacturer_part_number: str | None = None
    preferred_supplier_id: int | None = None
    unit: str
    unit_cost: Decimal | None = None
    last_purchase_price: Decimal | None = None
    min_stock_level: Decimal
    max_stock_level: Decimal | None = None
    reorder_point: Decimal | None = None
    reorder_quantity: Decimal | None = None
    lead_time_days: int | None = None
    criticality: AssetCriticalityEnum | None = None
    shelf_life_days: int | None = None
    is_active: bool
    product_id: int | None = None
    notes: str | None = None
    specifications: dict[str, Any] | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class PartRequestBase(BaseModel):
    part_description: str = Field(..., min_length=5, max_length=300)
    quantity_requested: Decimal


class PartRequestCreate(PartRequestBase):
    work_order_id: int | None = None
    spare_part_id: int | None = None
    unit: str | None = None
    priority: WorkOrderPriorityEnum = WorkOrderPriorityEnum.MEDIUM
    required_date: datetime.date | None = None
    request_reason: str | None = None


class PartRequestResponse(PartRequestBase):
    id: int
    request_number: str
    work_order_id: int | None = None
    spare_part_id: int | None = None
    unit: str | None = None
    quantity_approved: Decimal | None = None
    quantity_issued: Decimal | None = None
    priority: WorkOrderPriorityEnum
    required_date: datetime.date | None = None
    status: PartRequestStatusEnum
    requester_id: int | None = None
    request_date: datetime.datetime | None = None
    request_reason: str | None = None
    approved_by_id: int | None = None
    approved_date: datetime.datetime | None = None
    issued_by_id: int | None = None
    issued_date: datetime.datetime | None = None
    notes: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONTRATS
# ============================================================================

class ContractBase(BaseModel):
    contract_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    contract_type: ContractTypeEnum


class ContractCreate(ContractBase):
    vendor_id: int
    vendor_contact: str | None = None
    vendor_phone: str | None = None
    vendor_email: str | None = None
    start_date: datetime.date
    end_date: datetime.date
    renewal_date: datetime.date | None = None
    notice_period_days: int | None = None
    auto_renewal: bool = False
    covered_assets: list[int] | None = None
    coverage_description: str | None = None
    exclusions: str | None = None
    response_time_hours: int | None = None
    resolution_time_hours: int | None = None
    contract_value: Decimal | None = None
    annual_cost: Decimal | None = None
    payment_frequency: str | None = None
    includes_parts: bool = False
    includes_labor: bool = True
    includes_travel: bool = False
    max_interventions: int | None = None
    manager_id: int | None = None
    notes: str | None = None


class ContractUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    status: ContractStatusEnum | None = None
    vendor_contact: str | None = None
    vendor_phone: str | None = None
    vendor_email: str | None = None
    renewal_date: datetime.date | None = None
    auto_renewal: bool | None = None
    covered_assets: list[int] | None = None
    coverage_description: str | None = None
    response_time_hours: int | None = None
    annual_cost: Decimal | None = None
    manager_id: int | None = None
    notes: str | None = None


class ContractResponse(ContractBase):
    id: int
    status: ContractStatusEnum
    vendor_id: int
    vendor_contact: str | None = None
    vendor_phone: str | None = None
    vendor_email: str | None = None
    start_date: datetime.date
    end_date: datetime.date
    renewal_date: datetime.date | None = None
    notice_period_days: int | None = None
    auto_renewal: bool
    covered_assets: list[int] | None = None
    coverage_description: str | None = None
    exclusions: str | None = None
    response_time_hours: int | None = None
    resolution_time_hours: int | None = None
    availability_guarantee: Decimal | None = None
    contract_value: Decimal | None = None
    annual_cost: Decimal | None = None
    payment_frequency: str | None = None
    includes_parts: bool
    includes_labor: bool
    includes_travel: bool
    max_interventions: int | None = None
    interventions_used: int
    manager_id: int | None = None
    notes: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# KPIs
# ============================================================================

class MaintenanceKPIResponse(BaseModel):
    id: int
    asset_id: int | None = None
    period_start: datetime.date
    period_end: datetime.date
    period_type: str | None = None
    availability_rate: Decimal | None = None
    uptime_hours: Decimal | None = None
    downtime_hours: Decimal | None = None
    mtbf_hours: Decimal | None = None
    mttr_hours: Decimal | None = None
    failure_count: int
    wo_total: int
    wo_preventive: int
    wo_corrective: int
    wo_completed: int
    wo_overdue: int
    wo_on_time_rate: Decimal | None = None
    total_maintenance_cost: Decimal | None = None
    labor_cost: Decimal | None = None
    parts_cost: Decimal | None = None
    preventive_ratio: Decimal | None = None
    schedule_compliance: Decimal | None = None
    work_order_backlog: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedAssetResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    skip: int
    limit: int


class PaginatedMaintenancePlanResponse(BaseModel):
    items: list[MaintenancePlanResponse]
    total: int
    skip: int
    limit: int


class PaginatedWorkOrderResponse(BaseModel):
    items: list[WorkOrderResponse]
    total: int
    skip: int
    limit: int


class PaginatedFailureResponse(BaseModel):
    items: list[FailureResponse]
    total: int
    skip: int
    limit: int


class PaginatedSparePartResponse(BaseModel):
    items: list[SparePartResponse]
    total: int
    skip: int
    limit: int


class PaginatedContractResponse(BaseModel):
    items: list[ContractResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# DASHBOARD MAINTENANCE
# ============================================================================

class MaintenanceDashboard(BaseModel):
    # Actifs
    assets_total: int = 0
    assets_active: int = 0
    assets_in_maintenance: int = 0
    assets_by_category: dict[str, int] = {}

    # Ordres de travail
    wo_total: int = 0
    wo_open: int = 0
    wo_overdue: int = 0
    wo_completed_this_month: int = 0
    wo_by_priority: dict[str, int] = {}
    wo_by_status: dict[str, int] = {}

    # Pannes
    failures_this_month: int = 0
    failures_by_type: dict[str, int] = {}
    mtbf_global: Decimal | None = None
    mttr_global: Decimal | None = None

    # Plans de maintenance
    plans_active: int = 0
    plans_due_soon: int = 0

    # Coûts
    total_cost_this_month: Decimal | None = None
    labor_cost_this_month: Decimal | None = None
    parts_cost_this_month: Decimal | None = None

    # Indicateurs
    availability_rate: Decimal | None = None
    preventive_ratio: Decimal | None = None
    schedule_compliance: Decimal | None = None

    # Contrats
    contracts_active: int = 0
    contracts_expiring_soon: int = 0

    # Pièces de rechange
    parts_below_min_stock: int = 0
    pending_part_requests: int = 0
