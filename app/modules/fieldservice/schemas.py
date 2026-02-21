"""
Schémas Pydantic - Module Field Service (GAP-081)
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============== Enums ==============

class WorkOrderType(str, Enum):
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    INSPECTION = "inspection"
    EMERGENCY = "emergency"
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    UPGRADE = "upgrade"


class WorkOrderStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TechnicianStatus(str, Enum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"
    UNAVAILABLE = "unavailable"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SkillLevel(str, Enum):
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    EXPERT = "expert"


# ============== Work Order Schemas ==============

class WorkOrderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    work_order_type: WorkOrderType = WorkOrderType.MAINTENANCE
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    priority: Priority = Priority.MEDIUM
    customer_id: UUID
    customer_name: Optional[str] = None
    site_id: Optional[UUID] = None
    technician_id: Optional[UUID] = None
    scheduled_date: Optional[date] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    estimated_duration_minutes: int = Field(default=60, ge=0)
    billable: bool = True
    tags: List[str] = Field(default_factory=list)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class WorkOrderCreate(WorkOrderBase):
    lines: List[Dict[str, Any]] = Field(default_factory=list)


class WorkOrderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    work_order_type: Optional[WorkOrderType] = None
    status: Optional[WorkOrderStatus] = None
    priority: Optional[Priority] = None
    site_id: Optional[UUID] = None
    technician_id: Optional[UUID] = None
    scheduled_date: Optional[date] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None
    resolution_notes: Optional[str] = None
    billable: Optional[bool] = None
    tags: Optional[List[str]] = None
    lines: Optional[List[Dict[str, Any]]] = None
    parts_used: Optional[List[Dict[str, Any]]] = None


class WorkOrderResponse(WorkOrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    lines: List[Dict[str, Any]] = Field(default_factory=list)
    parts_used: List[Dict[str, Any]] = Field(default_factory=list)
    labor_entries: List[Dict[str, Any]] = Field(default_factory=list)
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    resolution_notes: Optional[str] = None
    customer_signature: Optional[str] = None
    technician_signature: Optional[str] = None
    photos: List[Dict[str, Any]] = Field(default_factory=list)
    labor_total: Decimal = Decimal("0")
    parts_total: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    invoice_id: Optional[UUID] = None
    sla_due_date: Optional[datetime] = None
    sla_met: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class WorkOrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    work_order_type: WorkOrderType
    status: WorkOrderStatus
    priority: Priority
    customer_name: Optional[str] = None
    scheduled_date: Optional[date] = None
    technician_id: Optional[UUID] = None
    created_at: datetime


class WorkOrderList(BaseModel):
    items: List[WorkOrderListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== FSTechnician Schemas ==============

class TechnicianSkillSchema(BaseModel):
    skill_id: UUID
    skill_name: str
    level: SkillLevel = SkillLevel.INTERMEDIATE
    certified: bool = False
    certification_date: Optional[date] = None
    certification_expiry: Optional[date] = None


class TechnicianBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[UUID] = None
    status: TechnicianStatus = TechnicianStatus.AVAILABLE
    home_zone_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    max_daily_work_orders: int = Field(default=8, ge=1, le=20)
    hourly_rate: Decimal = Decimal("0")
    overtime_rate: Decimal = Decimal("0")

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class TechnicianCreate(TechnicianBase):
    skills: List[TechnicianSkillSchema] = Field(default_factory=list)


class TechnicianUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[TechnicianStatus] = None
    home_zone_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    max_daily_work_orders: Optional[int] = None
    hourly_rate: Optional[Decimal] = None
    overtime_rate: Optional[Decimal] = None
    skills: Optional[List[TechnicianSkillSchema]] = None
    is_active: Optional[bool] = None


class TechnicianLocationUpdate(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)


class TechnicianResponse(TechnicianBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    current_location_lat: Optional[Decimal] = None
    current_location_lng: Optional[Decimal] = None
    last_location_update: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    version: int = 1


class TechnicianListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    first_name: str
    last_name: str
    email: str
    status: TechnicianStatus
    is_active: bool


class TechnicianList(BaseModel):
    items: List[TechnicianListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Customer Site Schemas ==============

class CustomerSiteBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    customer_id: UUID
    customer_name: Optional[str] = None
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(default="France", max_length=100)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    access_instructions: Optional[str] = None
    special_requirements: Optional[str] = None
    zone_id: Optional[UUID] = None

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class CustomerSiteCreate(CustomerSiteBase):
    equipment_list: List[Dict[str, Any]] = Field(default_factory=list)


class CustomerSiteUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    access_instructions: Optional[str] = None
    special_requirements: Optional[str] = None
    zone_id: Optional[UUID] = None
    equipment_list: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class CustomerSiteResponse(CustomerSiteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    equipment_list: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    version: int = 1


# ============== Service Zone Schemas ==============

class ServiceZoneBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    center_lat: Optional[Decimal] = None
    center_lng: Optional[Decimal] = None
    radius_km: Optional[Decimal] = None
    travel_time_minutes: int = Field(default=30, ge=0)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class ServiceZoneCreate(ServiceZoneBase):
    polygon_coordinates: List[Dict[str, Any]] = Field(default_factory=list)
    assigned_technicians: List[UUID] = Field(default_factory=list)


class ServiceZoneUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    center_lat: Optional[Decimal] = None
    center_lng: Optional[Decimal] = None
    radius_km: Optional[Decimal] = None
    travel_time_minutes: Optional[int] = None
    polygon_coordinates: Optional[List[Dict[str, Any]]] = None
    assigned_technicians: Optional[List[UUID]] = None
    is_active: Optional[bool] = None


class ServiceZoneResponse(ServiceZoneBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    polygon_coordinates: List[Dict[str, Any]] = Field(default_factory=list)
    assigned_technicians: List[UUID] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    version: int = 1


# ============== Common ==============

class AutocompleteItem(BaseModel):
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]


class BulkResult(BaseModel):
    success: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ============== Filters ==============

class WorkOrderFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    work_order_type: Optional[List[WorkOrderType]] = None
    status: Optional[List[WorkOrderStatus]] = None
    priority: Optional[List[Priority]] = None
    customer_id: Optional[UUID] = None
    technician_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class TechnicianFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[TechnicianStatus]] = None
    zone_id: Optional[UUID] = None
    is_active: Optional[bool] = None
