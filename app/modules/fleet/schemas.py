"""
Schemas Pydantic - Module Fleet Management (GAP-062)

Validation et serialisation des donnees.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============== Enums (mirror models) ==============

class VehicleType(str, Enum):
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    UTILITY = "utility"
    BUS = "bus"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    SCOOTER = "scooter"


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    OUT_OF_SERVICE = "out_of_service"
    RESERVED = "reserved"
    SOLD = "sold"
    SCRAPPED = "scrapped"


class FuelType(str, Enum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    LPG = "lpg"
    CNG = "cng"
    HYDROGEN = "hydrogen"
    E85 = "e85"


class ContractType(str, Enum):
    PURCHASE = "purchase"
    LEASING = "leasing"
    LLD = "lld"
    LOA = "loa"
    RENTAL = "rental"
    COMPANY_CAR = "company_car"


class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"


class MaintenanceType(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    INSPECTION = "inspection"
    TECHNICAL_CONTROL = "technical_control"
    TIRE_CHANGE = "tire_change"
    OIL_CHANGE = "oil_change"
    BRAKE_SERVICE = "brake_service"
    BATTERY = "battery"
    BODYWORK = "bodywork"
    OTHER = "other"


class MaintenanceStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class DocumentType(str, Enum):
    REGISTRATION = "registration"
    INSURANCE = "insurance"
    TECHNICAL_INSPECTION = "technical_inspection"
    POLLUTION_CERTIFICATE = "pollution_certificate"
    LEASE_CONTRACT = "lease_contract"
    WARRANTY = "warranty"
    DRIVER_LICENSE = "driver_license"
    MEDICAL_CERTIFICATE = "medical_certificate"
    OTHER = "other"


class AlertType(str, Enum):
    MAINTENANCE_DUE = "maintenance_due"
    DOCUMENT_EXPIRY = "document_expiry"
    INSURANCE_EXPIRY = "insurance_expiry"
    INSPECTION_DUE = "inspection_due"
    CONTRACT_EXPIRY = "contract_expiry"
    LICENSE_EXPIRY = "license_expiry"
    MILEAGE_EXCEEDED = "mileage_exceeded"
    MILEAGE_THRESHOLD = "mileage_threshold"
    FUEL_ANOMALY = "fuel_anomaly"
    COST_THRESHOLD = "cost_threshold"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    ACCIDENT = "accident"
    THEFT = "theft"
    VANDALISM = "vandalism"
    BREAKDOWN = "breakdown"
    FINE = "fine"
    PARKING_FINE = "parking_fine"
    SPEED_FINE = "speed_fine"
    OTHER_FINE = "other_fine"


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    INSURANCE_CLAIM = "insurance_claim"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ============== Vehicle Schemas ==============

class VehicleBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    registration_number: str = Field(..., min_length=2, max_length=20)
    vin: Optional[str] = Field(None, max_length=17)
    internal_number: Optional[str] = Field(None, max_length=50)
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=100)
    year: int = Field(..., ge=1900, le=2100)
    vehicle_type: VehicleType = VehicleType.CAR
    fuel_type: FuelType = FuelType.DIESEL
    status: VehicleStatus = VehicleStatus.AVAILABLE
    color: Optional[str] = Field(None, max_length=50)
    seats: int = Field(default=5, ge=1, le=100)
    doors: int = Field(default=4, ge=1, le=10)
    engine_capacity_cc: Optional[int] = Field(None, ge=0)
    power_hp: Optional[int] = Field(None, ge=0)
    power_kw: Optional[int] = Field(None, ge=0)
    fiscal_power: Optional[int] = Field(None, ge=0)
    co2_emissions: Optional[int] = Field(None, ge=0)
    transmission: str = Field(default="manual", max_length=20)
    initial_mileage: int = Field(default=0, ge=0)
    current_mileage: int = Field(default=0, ge=0)
    annual_mileage_limit: Optional[int] = Field(None, ge=0)
    fuel_capacity_liters: Optional[int] = Field(None, ge=0)
    average_consumption: Optional[Decimal] = Field(None, ge=0)
    battery_capacity_kwh: Optional[Decimal] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    current_value: Optional[Decimal] = Field(None, ge=0)
    residual_value: Optional[Decimal] = Field(None, ge=0)
    monthly_cost: Optional[Decimal] = Field(None, ge=0)
    assigned_driver_id: Optional[UUID] = None
    department: Optional[str] = Field(None, max_length=100)
    cost_center: Optional[str] = Field(None, max_length=50)
    project_id: Optional[UUID] = None
    gps_device_id: Optional[str] = Field(None, max_length=100)
    first_registration_date: Optional[date] = None
    last_technical_inspection: Optional[date] = None
    next_technical_inspection: Optional[date] = None
    last_service_date: Optional[date] = None
    next_service_date: Optional[date] = None
    next_service_mileage: Optional[int] = Field(None, ge=0)
    photo_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v

    @field_validator('registration_number')
    @classmethod
    def format_registration(cls, v: str) -> str:
        return v.upper().strip().replace(" ", "-")


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    registration_number: Optional[str] = Field(None, min_length=2, max_length=20)
    vin: Optional[str] = None
    internal_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    version: Optional[str] = None
    year: Optional[int] = None
    vehicle_type: Optional[VehicleType] = None
    fuel_type: Optional[FuelType] = None
    status: Optional[VehicleStatus] = None
    color: Optional[str] = None
    seats: Optional[int] = None
    doors: Optional[int] = None
    engine_capacity_cc: Optional[int] = None
    power_hp: Optional[int] = None
    power_kw: Optional[int] = None
    fiscal_power: Optional[int] = None
    co2_emissions: Optional[int] = None
    transmission: Optional[str] = None
    current_mileage: Optional[int] = None
    annual_mileage_limit: Optional[int] = None
    fuel_capacity_liters: Optional[int] = None
    average_consumption: Optional[Decimal] = None
    battery_capacity_kwh: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    residual_value: Optional[Decimal] = None
    monthly_cost: Optional[Decimal] = None
    assigned_driver_id: Optional[UUID] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    project_id: Optional[UUID] = None
    gps_device_id: Optional[str] = None
    next_technical_inspection: Optional[date] = None
    next_service_date: Optional[date] = None
    next_service_mileage: Optional[int] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None
    last_location_update: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class VehicleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    registration_number: str
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    fuel_type: FuelType
    status: VehicleStatus
    current_mileage: int
    assigned_driver_id: Optional[UUID] = None
    department: Optional[str] = None
    is_active: bool


class VehicleList(BaseModel):
    items: List[VehicleListItem]
    total: int
    page: int
    page_size: int
    pages: int


class VehicleLocationUpdate(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)


class VehicleMileageUpdate(BaseModel):
    mileage: int = Field(..., ge=0)
    log_date: Optional[date] = None
    source: str = Field(default="manual", max_length=50)
    notes: Optional[str] = None


# ============== Driver Schemas ==============

class DriverBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    employee_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    license_number: Optional[str] = Field(None, max_length=50)
    license_type: Optional[str] = Field(None, max_length=20)
    license_issue_date: Optional[date] = None
    license_expiry_date: Optional[date] = None
    license_country: str = Field(default="France", max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    hire_date: Optional[date] = None
    cost_center: Optional[str] = Field(None, max_length=50)
    medical_certificate_date: Optional[date] = None
    medical_certificate_expiry: Optional[date] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=50)
    emergency_contact_relation: Optional[str] = Field(None, max_length=100)
    photo_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    code: Optional[str] = None
    employee_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    license_number: Optional[str] = None
    license_type: Optional[str] = None
    license_issue_date: Optional[date] = None
    license_expiry_date: Optional[date] = None
    license_country: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    cost_center: Optional[str] = None
    medical_certificate_date: Optional[date] = None
    medical_certificate_expiry: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DriverResponse(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    total_trips: int = 0
    total_distance_km: int = 0
    total_fuel_cost: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    version: int = 1


class DriverListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    department: Optional[str] = None
    license_expiry_date: Optional[date] = None
    is_active: bool


class DriverList(BaseModel):
    items: List[DriverListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Contract Schemas ==============

class ContractBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    vehicle_id: UUID
    contract_type: ContractType
    status: ContractStatus = ContractStatus.ACTIVE
    provider_name: str = Field(..., min_length=1, max_length=200)
    provider_contact: Optional[str] = Field(None, max_length=200)
    provider_phone: Optional[str] = Field(None, max_length=50)
    provider_email: Optional[str] = Field(None, max_length=255)
    contract_number: Optional[str] = Field(None, max_length=100)
    start_date: date
    end_date: Optional[date] = None
    duration_months: Optional[int] = Field(None, ge=0)
    renewal_date: Optional[date] = None
    notice_period_days: int = Field(default=90, ge=0)
    monthly_payment: Optional[Decimal] = Field(None, ge=0)
    deposit: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="EUR", max_length=3)
    mileage_limit_annual: Optional[int] = Field(None, ge=0)
    mileage_limit_total: Optional[int] = Field(None, ge=0)
    excess_mileage_rate: Optional[Decimal] = Field(None, ge=0)
    services_included: List[str] = Field(default_factory=list)
    coverage_details: Optional[str] = None
    insurance_company: Optional[str] = Field(None, max_length=200)
    policy_number: Optional[str] = Field(None, max_length=100)
    coverage_type: Optional[str] = Field(None, max_length=100)
    deductible: Optional[Decimal] = Field(None, ge=0)
    bonus_malus: Optional[Decimal] = None
    document_url: Optional[str] = Field(None, max_length=500)
    reminder_days: int = Field(default=60, ge=0)
    notes: Optional[str] = None

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    code: Optional[str] = None
    contract_type: Optional[ContractType] = None
    status: Optional[ContractStatus] = None
    provider_name: Optional[str] = None
    provider_contact: Optional[str] = None
    provider_phone: Optional[str] = None
    provider_email: Optional[str] = None
    contract_number: Optional[str] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    notice_period_days: Optional[int] = None
    monthly_payment: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    mileage_limit_annual: Optional[int] = None
    excess_mileage_rate: Optional[Decimal] = None
    services_included: Optional[List[str]] = None
    coverage_details: Optional[str] = None
    deductible: Optional[Decimal] = None
    bonus_malus: Optional[Decimal] = None
    document_url: Optional[str] = None
    reminder_days: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ContractResponse(ContractBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    reminder_sent: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    version: int = 1


class ContractListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    vehicle_id: UUID
    contract_type: ContractType
    status: ContractStatus
    provider_name: str
    start_date: date
    end_date: Optional[date] = None
    monthly_payment: Optional[Decimal] = None


class ContractList(BaseModel):
    items: List[ContractListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Fuel Entry Schemas ==============

class FuelEntryBase(BaseModel):
    vehicle_id: UUID
    driver_id: Optional[UUID] = None
    fill_date: date
    fill_time: Optional[datetime] = None
    station_name: Optional[str] = Field(None, max_length=200)
    station_address: Optional[str] = Field(None, max_length=300)
    station_city: Optional[str] = Field(None, max_length=100)
    fuel_type: FuelType
    quantity_liters: Decimal = Field(..., gt=0)
    price_per_liter: Decimal = Field(..., gt=0)
    total_cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="EUR", max_length=3)
    mileage_at_fill: int = Field(..., ge=0)
    full_tank: bool = True
    payment_method: Optional[str] = Field(None, max_length=50)
    fuel_card_number: Optional[str] = Field(None, max_length=50)
    receipt_number: Optional[str] = Field(None, max_length=100)
    receipt_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None

    @model_validator(mode='after')
    def calculate_total(self):
        if self.total_cost is None:
            self.total_cost = self.quantity_liters * self.price_per_liter
        return self


class FuelEntryCreate(FuelEntryBase):
    pass


class FuelEntryUpdate(BaseModel):
    driver_id: Optional[UUID] = None
    fill_date: Optional[date] = None
    station_name: Optional[str] = None
    station_address: Optional[str] = None
    station_city: Optional[str] = None
    fuel_type: Optional[FuelType] = None
    quantity_liters: Optional[Decimal] = None
    price_per_liter: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    mileage_at_fill: Optional[int] = None
    full_tank: Optional[bool] = None
    payment_method: Optional[str] = None
    fuel_card_number: Optional[str] = None
    receipt_number: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class FuelEntryResponse(FuelEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    previous_mileage: Optional[int] = None
    distance_since_last: Optional[int] = None
    consumption_per_100km: Optional[Decimal] = None
    is_validated: bool = False
    anomaly_detected: bool = False
    anomaly_reason: Optional[str] = None
    created_at: datetime


class FuelEntryListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID
    driver_id: Optional[UUID] = None
    fill_date: date
    fuel_type: FuelType
    quantity_liters: Decimal
    total_cost: Decimal
    mileage_at_fill: int
    consumption_per_100km: Optional[Decimal] = None


class FuelEntryList(BaseModel):
    items: List[FuelEntryListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Maintenance Schemas ==============

class MaintenanceBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    vehicle_id: UUID
    maintenance_type: MaintenanceType
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    work_performed: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_mileage: Optional[int] = Field(None, ge=0)
    completed_date: Optional[date] = None
    mileage_at_maintenance: Optional[int] = Field(None, ge=0)
    next_maintenance_date: Optional[date] = None
    next_maintenance_mileage: Optional[int] = Field(None, ge=0)
    provider_name: Optional[str] = Field(None, max_length=200)
    provider_address: Optional[str] = Field(None, max_length=300)
    provider_contact: Optional[str] = Field(None, max_length=200)
    provider_phone: Optional[str] = Field(None, max_length=50)
    cost_parts: Decimal = Field(default=Decimal("0"), ge=0)
    cost_labor: Decimal = Field(default=Decimal("0"), ge=0)
    cost_other: Decimal = Field(default=Decimal("0"), ge=0)
    cost_total: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="EUR", max_length=3)
    vat_rate: Decimal = Field(default=Decimal("20"), ge=0)
    parts_replaced: List[Dict[str, Any]] = Field(default_factory=list)
    warranty_parts: bool = False
    warranty_labor: bool = False
    invoice_number: Optional[str] = Field(None, max_length=100)
    invoice_date: Optional[date] = None
    invoice_url: Optional[str] = Field(None, max_length=500)
    work_order_number: Optional[str] = Field(None, max_length=100)
    technician_name: Optional[str] = Field(None, max_length=200)
    technician_notes: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v

    @model_validator(mode='after')
    def calculate_total(self):
        if self.cost_total is None:
            self.cost_total = self.cost_parts + self.cost_labor + self.cost_other
        return self


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    code: Optional[str] = None
    maintenance_type: Optional[MaintenanceType] = None
    status: Optional[MaintenanceStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    work_performed: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_mileage: Optional[int] = None
    completed_date: Optional[date] = None
    mileage_at_maintenance: Optional[int] = None
    next_maintenance_date: Optional[date] = None
    next_maintenance_mileage: Optional[int] = None
    provider_name: Optional[str] = None
    provider_contact: Optional[str] = None
    provider_phone: Optional[str] = None
    cost_parts: Optional[Decimal] = None
    cost_labor: Optional[Decimal] = None
    cost_other: Optional[Decimal] = None
    cost_total: Optional[Decimal] = None
    parts_replaced: Optional[List[Dict[str, Any]]] = None
    warranty_parts: Optional[bool] = None
    warranty_labor: Optional[bool] = None
    invoice_number: Optional[str] = None
    invoice_url: Optional[str] = None
    technician_name: Optional[str] = None
    technician_notes: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceResponse(MaintenanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vat_amount: Decimal = Decimal("0")
    reminder_sent: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    version: int = 1


class MaintenanceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    vehicle_id: UUID
    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    title: str
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    cost_total: Decimal


class MaintenanceList(BaseModel):
    items: List[MaintenanceListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Incident Schemas ==============

class IncidentBase(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    vehicle_id: UUID
    driver_id: Optional[UUID] = None
    incident_type: IncidentType
    status: IncidentStatus = IncidentStatus.REPORTED
    incident_date: datetime
    incident_location: Optional[str] = Field(None, max_length=300)
    description: str = Field(..., min_length=1)
    circumstances: Optional[str] = None
    third_party_involved: bool = False
    third_party_details: Optional[str] = None
    police_report_number: Optional[str] = Field(None, max_length=100)
    police_report_date: Optional[date] = None
    fine_number: Optional[str] = Field(None, max_length=100)
    fine_amount: Optional[Decimal] = Field(None, ge=0)
    fine_points: Optional[int] = Field(None, ge=0)
    fine_due_date: Optional[date] = None
    fine_paid: bool = False
    fine_contested: bool = False
    insurance_claim_number: Optional[str] = Field(None, max_length=100)
    insurance_claim_date: Optional[date] = None
    repair_cost: Optional[Decimal] = Field(None, ge=0)
    other_costs: Optional[Decimal] = Field(None, ge=0)
    driver_responsible: Optional[bool] = None
    responsibility_percentage: Optional[int] = Field(None, ge=0, le=100)
    photos: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    code: Optional[str] = None
    driver_id: Optional[UUID] = None
    incident_type: Optional[IncidentType] = None
    status: Optional[IncidentStatus] = None
    incident_location: Optional[str] = None
    description: Optional[str] = None
    circumstances: Optional[str] = None
    third_party_involved: Optional[bool] = None
    third_party_details: Optional[str] = None
    police_report_number: Optional[str] = None
    police_report_date: Optional[date] = None
    fine_amount: Optional[Decimal] = None
    fine_due_date: Optional[date] = None
    fine_paid: Optional[bool] = None
    fine_paid_date: Optional[date] = None
    fine_contested: Optional[bool] = None
    insurance_claim_number: Optional[str] = None
    insurance_claim_date: Optional[date] = None
    insurance_status: Optional[str] = None
    insurance_payout: Optional[Decimal] = None
    deductible_amount: Optional[Decimal] = None
    repair_cost: Optional[Decimal] = None
    other_costs: Optional[Decimal] = None
    cost_recovered: Optional[Decimal] = None
    resolution_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    driver_responsible: Optional[bool] = None
    responsibility_percentage: Optional[int] = None
    photos: Optional[List[str]] = None
    documents: Optional[List[str]] = None
    notes: Optional[str] = None


class IncidentResponse(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fine_paid_date: Optional[date] = None
    fine_contest_date: Optional[date] = None
    insurance_status: Optional[str] = None
    insurance_payout: Optional[Decimal] = None
    deductible_amount: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    cost_recovered: Optional[Decimal] = None
    resolution_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    version: int = 1


class IncidentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    vehicle_id: UUID
    driver_id: Optional[UUID] = None
    incident_type: IncidentType
    status: IncidentStatus
    incident_date: datetime
    fine_amount: Optional[Decimal] = None
    repair_cost: Optional[Decimal] = None


class IncidentList(BaseModel):
    items: List[IncidentListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Document Schemas ==============

class DocumentBase(BaseModel):
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    document_type: DocumentType
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    document_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = Field(None, max_length=200)
    file_name: Optional[str] = Field(None, max_length=255)
    file_url: Optional[str] = Field(None, max_length=500)
    reminder_days: int = Field(default=30, ge=0)
    notes: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    document_type: Optional[DocumentType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    file_url: Optional[str] = None
    reminder_days: Optional[int] = None
    notes: Optional[str] = None


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    reminder_sent: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    document_type: DocumentType
    name: str
    expiry_date: Optional[date] = None
    reminder_sent: bool


class DocumentList(BaseModel):
    items: List[DocumentListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Alert Schemas ==============

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    maintenance_id: Optional[UUID] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    due_date: Optional[date] = None
    days_before_due: Optional[int] = None
    is_read: bool = False
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AlertListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: Optional[UUID] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    due_date: Optional[date] = None
    is_read: bool
    is_resolved: bool
    created_at: datetime


class AlertList(BaseModel):
    items: List[AlertListItem]
    total: int


# ============== Dashboard / Stats Schemas ==============

class FleetDashboard(BaseModel):
    """Tableau de bord de la flotte."""
    total_vehicles: int = 0
    vehicles_by_status: Dict[str, int] = Field(default_factory=dict)
    vehicles_by_type: Dict[str, int] = Field(default_factory=dict)

    total_drivers: int = 0
    active_drivers: int = 0

    total_mileage_month: int = 0
    total_fuel_cost_month: Decimal = Decimal("0")
    total_maintenance_cost_month: Decimal = Decimal("0")
    total_incidents_month: int = 0
    total_fines_month: int = 0
    total_fines_amount_month: Decimal = Decimal("0")

    avg_consumption: Decimal = Decimal("0")
    avg_cost_per_km: Decimal = Decimal("0")

    alerts_critical: int = 0
    alerts_warning: int = 0
    alerts_total: int = 0

    contracts_expiring_30d: int = 0
    documents_expiring_30d: int = 0
    inspections_due_30d: int = 0
    maintenances_due_30d: int = 0

    recent_alerts: List[AlertListItem] = Field(default_factory=list)


class TCOReport(BaseModel):
    """Rapport TCO (Total Cost of Ownership)."""
    vehicle_id: UUID
    vehicle_info: str
    period_start: date
    period_end: date

    # Couts
    fuel_cost: Decimal = Decimal("0")
    maintenance_cost: Decimal = Decimal("0")
    insurance_cost: Decimal = Decimal("0")
    tax_cost: Decimal = Decimal("0")
    leasing_cost: Decimal = Decimal("0")
    depreciation: Decimal = Decimal("0")
    fines_cost: Decimal = Decimal("0")
    other_costs: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")

    # Distance
    total_distance_km: int = 0
    cost_per_km: Decimal = Decimal("0")

    # Carburant
    total_fuel_liters: Decimal = Decimal("0")
    avg_consumption_per_100km: Decimal = Decimal("0")

    # Details
    cost_breakdown: Dict[str, Decimal] = Field(default_factory=dict)


class ConsumptionStats(BaseModel):
    """Statistiques de consommation."""
    vehicle_id: UUID
    period_start: date
    period_end: date
    total_liters: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    total_distance_km: int = 0
    avg_consumption_per_100km: Decimal = Decimal("0")
    fill_count: int = 0
    avg_price_per_liter: Decimal = Decimal("0")


# ============== Common Schemas ==============

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

class VehicleFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[VehicleStatus]] = None
    vehicle_type: Optional[List[VehicleType]] = None
    fuel_type: Optional[List[FuelType]] = None
    department: Optional[str] = None
    assigned_driver_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class DriverFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    department: Optional[str] = None
    is_active: Optional[bool] = None
    license_expiring_days: Optional[int] = None


class ContractFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    vehicle_id: Optional[UUID] = None
    contract_type: Optional[List[ContractType]] = None
    status: Optional[List[ContractStatus]] = None
    expiring_days: Optional[int] = None


class MaintenanceFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    vehicle_id: Optional[UUID] = None
    maintenance_type: Optional[List[MaintenanceType]] = None
    status: Optional[List[MaintenanceStatus]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class IncidentFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    incident_type: Optional[List[IncidentType]] = None
    status: Optional[List[IncidentStatus]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class AlertFilters(BaseModel):
    vehicle_id: Optional[UUID] = None
    alert_type: Optional[List[AlertType]] = None
    severity: Optional[List[AlertSeverity]] = None
    is_resolved: Optional[bool] = None
