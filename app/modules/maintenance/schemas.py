"""
AZALS MODULE M8 - Schémas Pydantic Maintenance
==============================================

Schémas de validation pour les API du module Maintenance (GMAO).
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


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
    description: Optional[str] = None
    category: AssetCategoryEnum
    asset_type: Optional[str] = None


class AssetCreate(AssetBase):
    parent_id: Optional[int] = None
    criticality: AssetCriticalityEnum = AssetCriticalityEnum.MEDIUM
    location_id: Optional[int] = None
    location_description: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    area: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    year_manufactured: Optional[int] = None
    purchase_date: Optional[date] = None
    installation_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    replacement_cost: Optional[Decimal] = None
    specifications: Optional[Dict[str, Any]] = None
    power_rating: Optional[str] = None
    supplier_id: Optional[int] = None
    responsible_id: Optional[int] = None
    department: Optional[str] = None
    maintenance_strategy: Optional[str] = None
    notes: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[AssetCategoryEnum] = None
    asset_type: Optional[str] = None
    status: Optional[AssetStatusEnum] = None
    criticality: Optional[AssetCriticalityEnum] = None
    parent_id: Optional[int] = None
    location_description: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    responsible_id: Optional[int] = None
    department: Optional[str] = None
    maintenance_strategy: Optional[str] = None
    notes: Optional[str] = None


class AssetResponse(AssetBase):
    id: int
    status: AssetStatusEnum
    criticality: AssetCriticalityEnum
    parent_id: Optional[int] = None
    location_id: Optional[int] = None
    location_description: Optional[str] = None
    building: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    year_manufactured: Optional[int] = None
    purchase_date: Optional[date] = None
    installation_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    operating_hours: Optional[Decimal] = None
    specifications: Optional[Dict[str, Any]] = None
    supplier_id: Optional[int] = None
    responsible_id: Optional[int] = None
    department: Optional[str] = None
    maintenance_strategy: Optional[str] = None
    mtbf_hours: Optional[Decimal] = None
    mttr_hours: Optional[Decimal] = None
    availability_rate: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# COMPTEURS
# ============================================================================

class MeterBase(BaseModel):
    meter_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    meter_type: str = Field(..., min_length=2, max_length=50)
    unit: str = Field(..., min_length=1, max_length=50)


class MeterCreate(MeterBase):
    initial_reading: Decimal = Decimal("0")
    alert_threshold: Optional[Decimal] = None
    critical_threshold: Optional[Decimal] = None
    maintenance_trigger_value: Optional[Decimal] = None


class MeterResponse(MeterBase):
    id: int
    asset_id: int
    current_reading: Decimal
    last_reading_date: Optional[datetime] = None
    initial_reading: Decimal
    alert_threshold: Optional[Decimal] = None
    critical_threshold: Optional[Decimal] = None
    maintenance_trigger_value: Optional[Decimal] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeterReadingCreate(BaseModel):
    reading_value: Decimal
    source: str = "MANUAL"
    notes: Optional[str] = None


class MeterReadingResponse(BaseModel):
    id: int
    meter_id: int
    reading_date: datetime
    reading_value: Decimal
    delta: Optional[Decimal] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PLANS DE MAINTENANCE
# ============================================================================

class PlanTaskBase(BaseModel):
    sequence: int
    task_code: Optional[str] = None
    description: str = Field(..., min_length=5)
    detailed_instructions: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    required_skill: Optional[str] = None
    is_mandatory: bool = True


class PlanTaskCreate(PlanTaskBase):
    required_parts: Optional[List[Dict[str, Any]]] = None
    check_points: Optional[List[str]] = None


class PlanTaskResponse(PlanTaskBase):
    id: int
    plan_id: int
    required_parts: Optional[List[Dict[str, Any]]] = None
    check_points: Optional[List[str]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaintenancePlanBase(BaseModel):
    plan_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    maintenance_type: MaintenanceTypeEnum


class MaintenancePlanCreate(MaintenancePlanBase):
    asset_id: Optional[int] = None
    asset_category: Optional[AssetCategoryEnum] = None
    trigger_type: str = "TIME"
    frequency_value: Optional[int] = None
    frequency_unit: Optional[str] = None
    trigger_meter_id: Optional[int] = None
    trigger_meter_interval: Optional[Decimal] = None
    lead_time_days: int = 7
    estimated_duration_hours: Optional[Decimal] = None
    responsible_id: Optional[int] = None
    estimated_labor_cost: Optional[Decimal] = None
    estimated_parts_cost: Optional[Decimal] = None
    instructions: Optional[str] = None
    safety_instructions: Optional[str] = None
    required_tools: Optional[List[str]] = None
    tasks: Optional[List[PlanTaskCreate]] = None


class MaintenancePlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    frequency_value: Optional[int] = None
    frequency_unit: Optional[str] = None
    lead_time_days: Optional[int] = None
    estimated_duration_hours: Optional[Decimal] = None
    responsible_id: Optional[int] = None
    instructions: Optional[str] = None
    safety_instructions: Optional[str] = None
    is_active: Optional[bool] = None


class MaintenancePlanResponse(MaintenancePlanBase):
    id: int
    asset_id: Optional[int] = None
    asset_category: Optional[AssetCategoryEnum] = None
    trigger_type: str
    frequency_value: Optional[int] = None
    frequency_unit: Optional[str] = None
    trigger_meter_id: Optional[int] = None
    trigger_meter_interval: Optional[Decimal] = None
    last_execution_date: Optional[date] = None
    next_due_date: Optional[date] = None
    lead_time_days: int
    estimated_duration_hours: Optional[Decimal] = None
    responsible_id: Optional[int] = None
    is_active: bool
    estimated_labor_cost: Optional[Decimal] = None
    estimated_parts_cost: Optional[Decimal] = None
    instructions: Optional[str] = None
    safety_instructions: Optional[str] = None
    required_tools: Optional[List[str]] = None
    tasks: List[PlanTaskResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ORDRES DE TRAVAIL
# ============================================================================

class WorkOrderTaskCreate(BaseModel):
    sequence: int
    description: str = Field(..., min_length=5)
    instructions: Optional[str] = None
    estimated_minutes: Optional[int] = None


class WorkOrderTaskResponse(BaseModel):
    id: int
    work_order_id: int
    sequence: int
    description: str
    instructions: Optional[str] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    status: str
    completed_date: Optional[datetime] = None
    result: Optional[str] = None
    issues_found: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WorkOrderLaborCreate(BaseModel):
    technician_id: int
    work_date: date
    hours_worked: Decimal
    overtime_hours: Decimal = Decimal("0")
    labor_type: str = "REGULAR"
    hourly_rate: Optional[Decimal] = None
    work_description: Optional[str] = None


class WorkOrderLaborResponse(BaseModel):
    id: int
    work_order_id: int
    technician_id: int
    technician_name: Optional[str] = None
    work_date: date
    hours_worked: Decimal
    overtime_hours: Decimal
    labor_type: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    work_description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkOrderPartCreate(BaseModel):
    spare_part_id: Optional[int] = None
    part_description: str = Field(..., min_length=2, max_length=300)
    quantity_used: Decimal
    unit: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    source: str = "STOCK"
    notes: Optional[str] = None


class WorkOrderPartResponse(BaseModel):
    id: int
    work_order_id: int
    spare_part_id: Optional[int] = None
    part_code: Optional[str] = None
    part_description: str
    quantity_planned: Optional[Decimal] = None
    quantity_used: Decimal
    unit: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    source: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkOrderBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: Optional[str] = None
    maintenance_type: MaintenanceTypeEnum
    asset_id: int


class WorkOrderCreate(WorkOrderBase):
    component_id: Optional[int] = None
    priority: WorkOrderPriorityEnum = WorkOrderPriorityEnum.MEDIUM
    maintenance_plan_id: Optional[int] = None
    failure_id: Optional[int] = None
    requester_id: Optional[int] = None
    request_description: Optional[str] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    external_vendor_id: Optional[int] = None
    work_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    tools_required: Optional[List[str]] = None
    location_description: Optional[str] = None
    estimated_labor_hours: Optional[Decimal] = None
    estimated_parts_cost: Optional[Decimal] = None
    tasks: Optional[List[WorkOrderTaskCreate]] = None


class WorkOrderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    priority: Optional[WorkOrderPriorityEnum] = None
    status: Optional[WorkOrderStatusEnum] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    external_vendor_id: Optional[int] = None
    work_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    location_description: Optional[str] = None
    notes: Optional[str] = None


class WorkOrderComplete(BaseModel):
    completion_notes: str = Field(..., min_length=10)
    meter_reading_end: Optional[Decimal] = None


class WorkOrderResponse(WorkOrderBase):
    id: int
    wo_number: str
    priority: WorkOrderPriorityEnum
    status: WorkOrderStatusEnum
    component_id: Optional[int] = None
    source: Optional[str] = None
    source_reference: Optional[str] = None
    maintenance_plan_id: Optional[int] = None
    failure_id: Optional[int] = None
    requester_id: Optional[int] = None
    request_date: Optional[datetime] = None
    request_description: Optional[str] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    downtime_hours: Optional[Decimal] = None
    assigned_to_id: Optional[int] = None
    external_vendor_id: Optional[int] = None
    work_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    tools_required: Optional[List[str]] = None
    location_description: Optional[str] = None
    completion_notes: Optional[str] = None
    completed_by_id: Optional[int] = None
    verification_required: bool
    verified_by_id: Optional[int] = None
    verified_date: Optional[datetime] = None
    estimated_labor_hours: Optional[Decimal] = None
    estimated_labor_cost: Optional[Decimal] = None
    estimated_parts_cost: Optional[Decimal] = None
    actual_labor_hours: Optional[Decimal] = None
    actual_labor_cost: Optional[Decimal] = None
    actual_parts_cost: Optional[Decimal] = None
    meter_reading_end: Optional[Decimal] = None
    notes: Optional[str] = None
    tasks: List[WorkOrderTaskResponse] = []
    labor_entries: List[WorkOrderLaborResponse] = []
    parts_used: List[WorkOrderPartResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PANNES
# ============================================================================

class FailureBase(BaseModel):
    asset_id: int
    failure_type: FailureTypeEnum
    description: str = Field(..., min_length=10)
    failure_date: datetime


class FailureCreate(FailureBase):
    component_id: Optional[int] = None
    symptoms: Optional[str] = None
    production_stopped: bool = False
    downtime_hours: Optional[Decimal] = None
    meter_reading: Optional[Decimal] = None
    notes: Optional[str] = None


class FailureUpdate(BaseModel):
    description: Optional[str] = None
    symptoms: Optional[str] = None
    production_stopped: Optional[bool] = None
    downtime_hours: Optional[Decimal] = None
    estimated_cost_impact: Optional[Decimal] = None
    resolution: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class FailureResponse(FailureBase):
    id: int
    failure_number: str
    component_id: Optional[int] = None
    symptoms: Optional[str] = None
    detected_date: Optional[datetime] = None
    reported_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    production_stopped: bool
    downtime_hours: Optional[Decimal] = None
    production_loss_units: Optional[Decimal] = None
    estimated_cost_impact: Optional[Decimal] = None
    reported_by_id: Optional[int] = None
    work_order_id: Optional[int] = None
    resolution: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    meter_reading: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PIÈCES DE RECHANGE
# ============================================================================

class SparePartBase(BaseModel):
    part_code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = None
    category: Optional[str] = None


class SparePartCreate(SparePartBase):
    manufacturer: Optional[str] = None
    manufacturer_part_number: Optional[str] = None
    preferred_supplier_id: Optional[int] = None
    unit: str = "PCE"
    unit_cost: Optional[Decimal] = None
    min_stock_level: Decimal = Decimal("0")
    max_stock_level: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    criticality: Optional[AssetCriticalityEnum] = None
    shelf_life_days: Optional[int] = None
    product_id: Optional[int] = None
    notes: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None


class SparePartUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=300)
    description: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    preferred_supplier_id: Optional[int] = None
    unit_cost: Optional[Decimal] = None
    min_stock_level: Optional[Decimal] = None
    max_stock_level: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    criticality: Optional[AssetCriticalityEnum] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SparePartResponse(SparePartBase):
    id: int
    manufacturer: Optional[str] = None
    manufacturer_part_number: Optional[str] = None
    preferred_supplier_id: Optional[int] = None
    unit: str
    unit_cost: Optional[Decimal] = None
    last_purchase_price: Optional[Decimal] = None
    min_stock_level: Decimal
    max_stock_level: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    criticality: Optional[AssetCriticalityEnum] = None
    shelf_life_days: Optional[int] = None
    is_active: bool
    product_id: Optional[int] = None
    notes: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PartRequestBase(BaseModel):
    part_description: str = Field(..., min_length=5, max_length=300)
    quantity_requested: Decimal


class PartRequestCreate(PartRequestBase):
    work_order_id: Optional[int] = None
    spare_part_id: Optional[int] = None
    unit: Optional[str] = None
    priority: WorkOrderPriorityEnum = WorkOrderPriorityEnum.MEDIUM
    required_date: Optional[date] = None
    request_reason: Optional[str] = None


class PartRequestResponse(PartRequestBase):
    id: int
    request_number: str
    work_order_id: Optional[int] = None
    spare_part_id: Optional[int] = None
    unit: Optional[str] = None
    quantity_approved: Optional[Decimal] = None
    quantity_issued: Optional[Decimal] = None
    priority: WorkOrderPriorityEnum
    required_date: Optional[date] = None
    status: PartRequestStatusEnum
    requester_id: Optional[int] = None
    request_date: Optional[datetime] = None
    request_reason: Optional[str] = None
    approved_by_id: Optional[int] = None
    approved_date: Optional[datetime] = None
    issued_by_id: Optional[int] = None
    issued_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONTRATS
# ============================================================================

class ContractBase(BaseModel):
    contract_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    contract_type: ContractTypeEnum


class ContractCreate(ContractBase):
    vendor_id: int
    vendor_contact: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_email: Optional[str] = None
    start_date: date
    end_date: date
    renewal_date: Optional[date] = None
    notice_period_days: Optional[int] = None
    auto_renewal: bool = False
    covered_assets: Optional[List[int]] = None
    coverage_description: Optional[str] = None
    exclusions: Optional[str] = None
    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None
    contract_value: Optional[Decimal] = None
    annual_cost: Optional[Decimal] = None
    payment_frequency: Optional[str] = None
    includes_parts: bool = False
    includes_labor: bool = True
    includes_travel: bool = False
    max_interventions: Optional[int] = None
    manager_id: Optional[int] = None
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    status: Optional[ContractStatusEnum] = None
    vendor_contact: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_email: Optional[str] = None
    renewal_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    covered_assets: Optional[List[int]] = None
    coverage_description: Optional[str] = None
    response_time_hours: Optional[int] = None
    annual_cost: Optional[Decimal] = None
    manager_id: Optional[int] = None
    notes: Optional[str] = None


class ContractResponse(ContractBase):
    id: int
    status: ContractStatusEnum
    vendor_id: int
    vendor_contact: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_email: Optional[str] = None
    start_date: date
    end_date: date
    renewal_date: Optional[date] = None
    notice_period_days: Optional[int] = None
    auto_renewal: bool
    covered_assets: Optional[List[int]] = None
    coverage_description: Optional[str] = None
    exclusions: Optional[str] = None
    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None
    availability_guarantee: Optional[Decimal] = None
    contract_value: Optional[Decimal] = None
    annual_cost: Optional[Decimal] = None
    payment_frequency: Optional[str] = None
    includes_parts: bool
    includes_labor: bool
    includes_travel: bool
    max_interventions: Optional[int] = None
    interventions_used: int
    manager_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# KPIs
# ============================================================================

class MaintenanceKPIResponse(BaseModel):
    id: int
    asset_id: Optional[int] = None
    period_start: date
    period_end: date
    period_type: Optional[str] = None
    availability_rate: Optional[Decimal] = None
    uptime_hours: Optional[Decimal] = None
    downtime_hours: Optional[Decimal] = None
    mtbf_hours: Optional[Decimal] = None
    mttr_hours: Optional[Decimal] = None
    failure_count: int
    wo_total: int
    wo_preventive: int
    wo_corrective: int
    wo_completed: int
    wo_overdue: int
    wo_on_time_rate: Optional[Decimal] = None
    total_maintenance_cost: Optional[Decimal] = None
    labor_cost: Optional[Decimal] = None
    parts_cost: Optional[Decimal] = None
    preventive_ratio: Optional[Decimal] = None
    schedule_compliance: Optional[Decimal] = None
    work_order_backlog: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedAssetResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    skip: int
    limit: int


class PaginatedMaintenancePlanResponse(BaseModel):
    items: List[MaintenancePlanResponse]
    total: int
    skip: int
    limit: int


class PaginatedWorkOrderResponse(BaseModel):
    items: List[WorkOrderResponse]
    total: int
    skip: int
    limit: int


class PaginatedFailureResponse(BaseModel):
    items: List[FailureResponse]
    total: int
    skip: int
    limit: int


class PaginatedSparePartResponse(BaseModel):
    items: List[SparePartResponse]
    total: int
    skip: int
    limit: int


class PaginatedContractResponse(BaseModel):
    items: List[ContractResponse]
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
    assets_by_category: Dict[str, int] = {}

    # Ordres de travail
    wo_total: int = 0
    wo_open: int = 0
    wo_overdue: int = 0
    wo_completed_this_month: int = 0
    wo_by_priority: Dict[str, int] = {}
    wo_by_status: Dict[str, int] = {}

    # Pannes
    failures_this_month: int = 0
    failures_by_type: Dict[str, int] = {}
    mtbf_global: Optional[Decimal] = None
    mttr_global: Optional[Decimal] = None

    # Plans de maintenance
    plans_active: int = 0
    plans_due_soon: int = 0

    # Coûts
    total_cost_this_month: Optional[Decimal] = None
    labor_cost_this_month: Optional[Decimal] = None
    parts_cost_this_month: Optional[Decimal] = None

    # Indicateurs
    availability_rate: Optional[Decimal] = None
    preventive_ratio: Optional[Decimal] = None
    schedule_compliance: Optional[Decimal] = None

    # Contrats
    contracts_active: int = 0
    contracts_expiring_soon: int = 0

    # Pièces de rechange
    parts_below_min_stock: int = 0
    pending_part_requests: int = 0
