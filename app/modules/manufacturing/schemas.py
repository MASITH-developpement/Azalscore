"""
Schémas Pydantic Manufacturing / Fabrication
=============================================
- Validation stricte
- Types correspondant exactement au frontend
- Schémas de création, mise à jour et réponse
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============== Énumérations ==============

class BOMType(str, Enum):
    MANUFACTURING = "manufacturing"
    ASSEMBLY = "assembly"
    SUBCONTRACTING = "subcontracting"
    PHANTOM = "phantom"
    KIT = "kit"


class BOMStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    OBSOLETE = "obsolete"


class WorkcenterType(str, Enum):
    MACHINE = "machine"
    MANUAL = "manual"
    ASSEMBLY = "assembly"
    QUALITY = "quality"
    PACKAGING = "packaging"


class WorkcenterState(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class WorkOrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OperationStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class QualityCheckType(str, Enum):
    INCOMING = "incoming"
    IN_PROCESS = "in_process"
    FINAL = "final"


class QualityResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"


# ============== BOM Line Schemas ==============

class BOMLineBase(BaseModel):
    """Base BOM Line."""
    component_id: UUID
    component_code: str = Field(..., min_length=1, max_length=50)
    component_name: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit: str = Field(default="", max_length=20)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    is_optional: bool = False
    scrap_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    operation_id: Optional[UUID] = None
    notes: Optional[str] = None


class BOMLineCreate(BOMLineBase):
    """Création de ligne BOM."""
    sequence: Optional[int] = None


class BOMLineUpdate(BaseModel):
    """Mise à jour de ligne BOM."""
    component_id: Optional[UUID] = None
    component_code: Optional[str] = Field(None, min_length=1, max_length=50)
    component_name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=20)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    is_optional: Optional[bool] = None
    scrap_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    sequence: Optional[int] = None
    operation_id: Optional[UUID] = None
    notes: Optional[str] = None


class BOMLineResponse(BOMLineBase):
    """Réponse ligne BOM."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    bom_id: UUID
    sequence: int
    total_cost: Decimal
    substitute_ids: List[UUID] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== BOM Schemas ==============

class BOMBase(BaseModel):
    """Base BOM."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    bom_type: BOMType = BOMType.MANUFACTURING
    product_id: UUID
    product_code: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit: str = Field(default="", max_length=20)
    yield_rate: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    routing_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()

    @model_validator(mode='after')
    def validate_dates(self):
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError('valid_until must be after valid_from')
        return self


class BOMCreate(BOMBase):
    """Création BOM."""
    lines: List[BOMLineCreate] = Field(default_factory=list)


class BOMUpdate(BaseModel):
    """Mise à jour BOM."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    bom_type: Optional[BOMType] = None
    status: Optional[BOMStatus] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = None
    yield_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    routing_id: Optional[UUID] = None
    labor_cost: Optional[Decimal] = Field(None, ge=0)
    overhead_cost: Optional[Decimal] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class BOMResponse(BOMBase):
    """Réponse BOM."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: BOMStatus
    material_cost: Decimal
    labor_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    bom_version: int
    is_current: bool
    lines: List[BOMLineResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class BOMListItem(BaseModel):
    """Item léger pour listes BOM."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    status: BOMStatus
    bom_type: BOMType
    product_code: str
    product_name: str
    total_cost: Decimal
    line_count: int = 0
    created_at: datetime


# ============== Workcenter Schemas ==============

class WorkcenterBase(BaseModel):
    """Base Workcenter."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    workcenter_type: WorkcenterType = WorkcenterType.MACHINE
    capacity: Decimal = Field(default=Decimal("1"), gt=0)
    capacity_unit: str = Field(default="units/hour", max_length=50)
    hourly_cost: Decimal = Field(default=Decimal("0"), ge=0)
    setup_cost: Decimal = Field(default=Decimal("0"), ge=0)
    default_setup_time: int = Field(default=0, ge=0)
    default_cleanup_time: int = Field(default=0, ge=0)
    working_hours_per_day: Decimal = Field(default=Decimal("8"), gt=0, le=24)
    efficiency: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    location: str = Field(default="", max_length=255)
    department: str = Field(default="", max_length=100)
    max_operators: int = Field(default=1, ge=1)
    tags: List[str] = Field(default_factory=list)
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class WorkcenterCreate(WorkcenterBase):
    """Création Workcenter."""
    pass


class WorkcenterUpdate(BaseModel):
    """Mise à jour Workcenter."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    workcenter_type: Optional[WorkcenterType] = None
    state: Optional[WorkcenterState] = None
    capacity: Optional[Decimal] = Field(None, gt=0)
    capacity_unit: Optional[str] = None
    hourly_cost: Optional[Decimal] = Field(None, ge=0)
    setup_cost: Optional[Decimal] = Field(None, ge=0)
    default_setup_time: Optional[int] = Field(None, ge=0)
    default_cleanup_time: Optional[int] = Field(None, ge=0)
    working_hours_per_day: Optional[Decimal] = Field(None, gt=0, le=24)
    efficiency: Optional[Decimal] = Field(None, ge=0, le=100)
    location: Optional[str] = None
    department: Optional[str] = None
    max_operators: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    next_maintenance: Optional[datetime] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class WorkcenterResponse(WorkcenterBase):
    """Réponse Workcenter."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    state: WorkcenterState
    operator_ids: List[UUID] = []
    equipment_ids: List[UUID] = []
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class WorkcenterListItem(BaseModel):
    """Item léger pour listes Workcenter."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    workcenter_type: WorkcenterType
    state: WorkcenterState
    hourly_cost: Decimal
    efficiency: Decimal
    is_active: bool
    created_at: datetime


# ============== Operation Schemas ==============

class OperationBase(BaseModel):
    """Base Operation."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    workcenter_id: UUID
    workcenter_name: str = Field(default="", max_length=255)
    setup_time: int = Field(default=0, ge=0)
    run_time: int = Field(default=0, ge=0)
    cleanup_time: int = Field(default=0, ge=0)
    wait_time: int = Field(default=0, ge=0)
    quality_check_required: bool = False
    quality_check_type: Optional[QualityCheckType] = None
    instructions: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    tools_required: List[str] = Field(default_factory=list)


class OperationCreate(OperationBase):
    """Création Operation."""
    sequence: Optional[int] = None


class OperationUpdate(BaseModel):
    """Mise à jour Operation."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    workcenter_id: Optional[UUID] = None
    workcenter_name: Optional[str] = None
    sequence: Optional[int] = None
    setup_time: Optional[int] = Field(None, ge=0)
    run_time: Optional[int] = Field(None, ge=0)
    cleanup_time: Optional[int] = Field(None, ge=0)
    wait_time: Optional[int] = Field(None, ge=0)
    quality_check_required: Optional[bool] = None
    quality_check_type: Optional[QualityCheckType] = None
    instructions: Optional[str] = None
    attachments: Optional[List[str]] = None
    tools_required: Optional[List[str]] = None


class OperationResponse(OperationBase):
    """Réponse Operation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    routing_id: UUID
    sequence: int
    labor_cost_per_unit: Decimal
    machine_cost_per_unit: Decimal
    total_cost_per_unit: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== Routing Schemas ==============

class RoutingBase(BaseModel):
    """Base Routing."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    product_id: UUID
    bom_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class RoutingCreate(RoutingBase):
    """Création Routing."""
    operations: List[OperationCreate] = Field(default_factory=list)


class RoutingUpdate(BaseModel):
    """Mise à jour Routing."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    product_id: Optional[UUID] = None
    bom_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class RoutingResponse(RoutingBase):
    """Réponse Routing."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    total_setup_time: int
    total_run_time: int
    total_time: int
    total_cost_per_unit: Decimal
    routing_version: int
    is_current: bool
    is_active: bool
    operations: List[OperationResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class RoutingListItem(BaseModel):
    """Item léger pour listes Routing."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    total_time: int
    total_cost_per_unit: Decimal
    is_active: bool
    created_at: datetime


# ============== Work Order Schemas ==============

class WorkOrderBase(BaseModel):
    """Base Work Order."""
    name: str = Field(..., min_length=1, max_length=255)
    product_id: UUID
    product_code: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity_to_produce: Decimal = Field(..., gt=0)
    unit: str = Field(default="", max_length=20)
    bom_id: Optional[UUID] = None
    routing_id: Optional[UUID] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    priority: int = Field(default=0, ge=0)
    source_type: str = Field(default="manual", max_length=50)
    source_id: Optional[UUID] = None
    production_location: str = Field(default="", max_length=255)
    responsible_id: Optional[UUID] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class WorkOrderCreate(WorkOrderBase):
    """Création Work Order."""
    pass


class WorkOrderUpdate(BaseModel):
    """Mise à jour Work Order."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[WorkOrderStatus] = None
    quantity_to_produce: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=0)
    production_location: Optional[str] = None
    responsible_id: Optional[UUID] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class WorkOrderOperationResponse(BaseModel):
    """Réponse opération d'OF."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence: int
    name: str
    workcenter_id: Optional[UUID]
    status: OperationStatus
    planned_setup_time: int
    planned_run_time: int
    actual_setup_time: int
    actual_run_time: int
    planned_start: Optional[datetime]
    planned_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    quantity_to_produce: Decimal
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    operator_id: Optional[UUID]
    operator_name: str
    quality_check_passed: Optional[bool]


class WorkOrderResponse(WorkOrderBase):
    """Réponse Work Order."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    number: str
    status: WorkOrderStatus
    quantity_produced: Decimal
    quantity_scrapped: Decimal
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    planned_material_cost: Decimal
    planned_labor_cost: Decimal
    planned_overhead_cost: Decimal
    planned_total_cost: Decimal
    actual_material_cost: Decimal
    actual_labor_cost: Decimal
    actual_overhead_cost: Decimal
    actual_total_cost: Decimal
    operations: List[WorkOrderOperationResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class WorkOrderListItem(BaseModel):
    """Item léger pour listes Work Order."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    number: str
    name: str
    status: WorkOrderStatus
    product_code: str
    product_name: str
    quantity_to_produce: Decimal
    quantity_produced: Decimal
    planned_start: Optional[datetime]
    planned_end: Optional[datetime]
    priority: int
    created_at: datetime


# ============== Quality Check Schemas ==============

class QualitySpecification(BaseModel):
    """Spécification de contrôle qualité."""
    name: str
    target: Optional[Decimal] = None
    tolerance: Optional[Decimal] = None
    actual: Optional[Decimal] = None
    passed: Optional[bool] = None
    unit: str = ""
    notes: str = ""


class QualityCheckCreate(BaseModel):
    """Création Quality Check."""
    work_order_id: UUID
    operation_id: Optional[UUID] = None
    check_type: QualityCheckType = QualityCheckType.IN_PROCESS
    inspector_id: Optional[UUID] = None
    inspector_name: str = Field(default="", max_length=255)
    sample_size: int = Field(default=1, ge=1)
    specifications: List[QualitySpecification] = Field(default_factory=list)


class QualityCheckUpdate(BaseModel):
    """Mise à jour Quality Check."""
    result: Optional[QualityResult] = None
    specifications: Optional[List[QualitySpecification]] = None
    passed_count: Optional[int] = Field(None, ge=0)
    failed_count: Optional[int] = Field(None, ge=0)
    disposition: Optional[str] = None
    corrective_actions: Optional[str] = None
    notes: Optional[str] = None


class QualityCheckResponse(BaseModel):
    """Réponse Quality Check."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    work_order_id: UUID
    operation_id: Optional[UUID]
    check_type: QualityCheckType
    result: Optional[QualityResult]
    specifications: List[Dict[str, Any]]
    sample_size: int
    passed_count: int
    failed_count: int
    inspector_id: Optional[UUID]
    inspector_name: str
    checked_at: Optional[datetime]
    corrective_actions: Optional[str]
    disposition: str
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


# ============== Production Log Schemas ==============

class ProductionLogCreate(BaseModel):
    """Création Production Log."""
    work_order_id: UUID
    operation_id: Optional[UUID] = None
    event_type: str = Field(..., min_length=1, max_length=50)
    quantity: Decimal = Field(default=Decimal("0"), ge=0)
    unit: str = Field(default="", max_length=20)
    duration_minutes: int = Field(default=0, ge=0)
    operator_id: Optional[UUID] = None
    workcenter_id: Optional[UUID] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ProductionLogResponse(BaseModel):
    """Réponse Production Log."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    work_order_id: UUID
    operation_id: Optional[UUID]
    event_type: str
    quantity: Decimal
    unit: str
    duration_minutes: int
    operator_id: Optional[UUID]
    workcenter_id: Optional[UUID]
    details: Dict[str, Any]
    timestamp: datetime


# ============== Pagination et Listes ==============

class PaginatedBOMList(BaseModel):
    """Liste paginée BOM."""
    items: List[BOMListItem]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedWorkcenterList(BaseModel):
    """Liste paginée Workcenter."""
    items: List[WorkcenterListItem]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedRoutingList(BaseModel):
    """Liste paginée Routing."""
    items: List[RoutingListItem]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedWorkOrderList(BaseModel):
    """Liste paginée Work Order."""
    items: List[WorkOrderListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Autocomplete ==============

class AutocompleteItem(BaseModel):
    """Item autocomplete."""
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    """Réponse autocomplete."""
    items: List[AutocompleteItem]


# ============== Bulk Operations ==============

class BulkCreateRequest(BaseModel):
    """Requête création en masse."""
    items: List[Dict[str, Any]] = Field(..., min_length=1, max_length=1000)


class BulkUpdateRequest(BaseModel):
    """Requête mise à jour en masse."""
    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    data: Dict[str, Any]


class BulkDeleteRequest(BaseModel):
    """Requête suppression en masse."""
    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    hard: bool = False


class BulkResult(BaseModel):
    """Résultat opération en masse."""
    success: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ============== Filtres ==============

class BOMFilters(BaseModel):
    """Filtres BOM."""
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[BOMStatus]] = None
    bom_type: Optional[List[BOMType]] = None
    product_id: Optional[UUID] = None
    is_current: Optional[bool] = None
    tags: Optional[List[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class WorkcenterFilters(BaseModel):
    """Filtres Workcenter."""
    search: Optional[str] = Field(None, min_length=2)
    workcenter_type: Optional[List[WorkcenterType]] = None
    state: Optional[List[WorkcenterState]] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    tags: Optional[List[str]] = None


class WorkOrderFilters(BaseModel):
    """Filtres Work Order."""
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[WorkOrderStatus]] = None
    product_id: Optional[UUID] = None
    priority_min: Optional[int] = None
    priority_max: Optional[int] = None
    planned_start_from: Optional[datetime] = None
    planned_start_to: Optional[datetime] = None
    tags: Optional[List[str]] = None


# ============== BOM Explosion ==============

class BOMExplodeItem(BaseModel):
    """Item d'explosion de BOM."""
    component_id: str
    component_code: str
    component_name: str
    quantity: Decimal
    unit: str
    unit_cost: Decimal
    total_cost: Decimal
    level: int
    is_optional: bool


class BOMExplodeResponse(BaseModel):
    """Réponse explosion BOM."""
    components: List[BOMExplodeItem]


# ============== Operation Requests ==============

class RecordProductionRequest(BaseModel):
    """Requête enregistrement production."""
    quantity_produced: Decimal = Field(..., gt=0)
    quantity_scrapped: Decimal = Field(default=Decimal("0"), ge=0)
    operator_id: Optional[UUID] = None


class StartOperationRequest(BaseModel):
    """Requête démarrage opération."""
    operator_id: Optional[UUID] = None
    operator_name: str = Field(default="", max_length=255)


class CompleteOperationRequest(BaseModel):
    """Requête fin opération."""
    quantity_produced: Decimal = Field(..., gt=0)
    quantity_scrapped: Decimal = Field(default=Decimal("0"), ge=0)


# ============== List Response Aliases ==============

# Aliases pour uniformité avec le router
BOMListResponse = PaginatedBOMList
WorkcenterListResponse = PaginatedWorkcenterList
RoutingListResponse = PaginatedRoutingList
WorkOrderListResponse = PaginatedWorkOrderList


# ============== Stats ==============

class ProductionStats(BaseModel):
    """Statistiques de production."""
    total_work_orders: int = 0
    completed_orders: int = 0
    on_time_orders: int = 0
    late_orders: int = 0
    total_produced: Decimal = Decimal("0")
    total_scrapped: Decimal = Decimal("0")
    scrap_rate: Decimal = Decimal("0")
    quality_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    first_pass_yield: Decimal = Decimal("0")
    oee: Decimal = Decimal("0")
    availability: Decimal = Decimal("0")
    performance: Decimal = Decimal("0")
    quality_rate: Decimal = Decimal("0")
    total_setup_time: int = 0
    total_run_time: int = 0
    total_downtime: int = 0
    total_material_cost: Decimal = Decimal("0")
    total_labor_cost: Decimal = Decimal("0")
    actual_vs_planned_cost: Decimal = Decimal("0")
    workcenter_utilization: Dict[str, Decimal] = Field(default_factory=dict)
