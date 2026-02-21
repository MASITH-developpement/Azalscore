"""
Schémas Pydantic - Module Expenses (GAP-084)
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============== Enums ==============

class ExpenseCategory(str, Enum):
    MILEAGE = "mileage"
    PUBLIC_TRANSPORT = "public_transport"
    TAXI_RIDE = "taxi"
    PARKING = "parking"
    TOLL = "toll"
    RENTAL_CAR = "rental_car"
    FUEL = "fuel"
    HOTEL = "hotel"
    AIRBNB = "airbnb"
    RESTAURANT = "restaurant"
    MEAL_SOLO = "meal_solo"
    MEAL_BUSINESS = "meal_business"
    MEAL_TEAM = "meal_team"
    FLIGHT = "flight"
    TRAIN = "train"
    VISA = "visa"
    TRAVEL_INSURANCE = "travel_insurance"
    PHONE = "phone"
    INTERNET = "internet"
    OFFICE_SUPPLIES = "office_supplies"
    IT_EQUIPMENT = "it_equipment"
    BOOKS = "books"
    REPRESENTATION = "representation"
    SUBSCRIPTION = "subscription"
    OTHER = "other"


class ExpenseStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    PERSONAL_CARD = "personal_card"
    COMPANY_CARD = "company_card"
    CASH = "cash"
    COMPANY_ACCOUNT = "company_account"
    MILEAGE = "mileage"


class VehicleType(str, Enum):
    CAR_3CV = "car_3cv"
    CAR_4CV = "car_4cv"
    CAR_5CV = "car_5cv"
    CAR_6CV = "car_6cv"
    CAR_7CV_PLUS = "car_7cv_plus"
    MOTORCYCLE_50CC = "moto_50cc"
    MOTORCYCLE_125CC = "moto_125cc"
    MOTORCYCLE_3_5CV = "moto_3_5cv"
    MOTORCYCLE_5CV_PLUS = "moto_5cv_plus"
    BICYCLE = "bicycle"
    ELECTRIC_BICYCLE = "electric_bicycle"


# ============== Expense Line Schemas ==============

class ExpenseLineBase(BaseModel):
    category: ExpenseCategory
    description: str = Field(..., min_length=1, max_length=500)
    expense_date: date
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="EUR", max_length=3)
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    payment_method: PaymentMethod = PaymentMethod.PERSONAL_CARD
    receipt_required: bool = True
    project_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    billable: bool = False
    accounting_code: Optional[str] = Field(None, max_length=20)
    cost_center: Optional[str] = Field(None, max_length=50)


class ExpenseLineCreate(ExpenseLineBase):
    # Kilométrique
    mileage_departure: Optional[str] = Field(None, max_length=255)
    mileage_arrival: Optional[str] = Field(None, max_length=255)
    mileage_distance_km: Optional[Decimal] = Field(None, gt=0)
    mileage_is_round_trip: bool = False
    vehicle_type: Optional[VehicleType] = None
    mileage_purpose: Optional[str] = None

    # Repas d'affaires
    guests: List[str] = Field(default_factory=list)


class ExpenseLineUpdate(BaseModel):
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    expense_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    payment_method: Optional[PaymentMethod] = None
    project_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    billable: Optional[bool] = None
    guests: Optional[List[str]] = None


class ExpenseLineResponse(ExpenseLineBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    report_id: UUID
    vat_amount: Optional[Decimal] = None
    amount_excl_vat: Optional[Decimal] = None
    vat_recoverable: bool = True
    receipt_id: Optional[UUID] = None
    receipt_file_path: Optional[str] = None
    mileage_departure: Optional[str] = None
    mileage_arrival: Optional[str] = None
    mileage_distance_km: Optional[Decimal] = None
    mileage_is_round_trip: bool = False
    vehicle_type: Optional[str] = None
    mileage_rate: Optional[Decimal] = None
    mileage_purpose: Optional[str] = None
    guests: List[str] = Field(default_factory=list)
    guest_count: int = 0
    is_policy_compliant: bool = True
    policy_violation_reason: Optional[str] = None
    ocr_processed: bool = False
    created_at: datetime


# ============== Expense Report Schemas ==============

class ExpenseReportBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    mission_reference: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="EUR", max_length=3)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class ExpenseReportCreate(ExpenseReportBase):
    lines: List[ExpenseLineCreate] = Field(default_factory=list)


class ExpenseReportUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    mission_reference: Optional[str] = None


class ExpenseReportResponse(ExpenseReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: Optional[str] = None
    department_id: Optional[UUID] = None
    status: ExpenseStatus
    total_amount: Decimal = Decimal("0")
    total_vat: Decimal = Decimal("0")
    total_reimbursable: Decimal = Decimal("0")
    current_approver_id: Optional[UUID] = None
    approval_history: List[Dict[str, Any]] = Field(default_factory=list)
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    exported_to_accounting: bool = False
    lines: List[ExpenseLineResponse] = Field(default_factory=list)
    version: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False


class ExpenseReportListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    employee_name: Optional[str] = None
    status: ExpenseStatus
    total_amount: Decimal
    total_reimbursable: Decimal
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    submitted_at: Optional[datetime] = None
    line_count: int = 0


class ExpenseReportList(BaseModel):
    items: List[ExpenseReportListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Policy Schemas ==============

class ExpensePolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    is_default: bool = False
    category_limits: Dict[str, Decimal] = Field(default_factory=dict)
    single_expense_limit: Decimal = Decimal("500")
    daily_limit: Decimal = Decimal("200")
    monthly_limit: Decimal = Decimal("2000")
    receipt_required_above: Decimal = Decimal("10")
    receipt_required_categories: List[str] = Field(default_factory=list)
    meal_solo_limit: Decimal = Decimal("20.20")
    meal_business_limit: Decimal = Decimal("50")
    meal_require_guests: bool = True
    mileage_max_daily_km: Decimal = Decimal("500")
    require_train_over_km: Decimal = Decimal("300")
    approval_thresholds: Dict[str, Decimal] = Field(default_factory=dict)
    blocked_categories: List[str] = Field(default_factory=list)


class ExpensePolicyCreate(ExpensePolicyBase):
    pass


class ExpensePolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    category_limits: Optional[Dict[str, Decimal]] = None
    single_expense_limit: Optional[Decimal] = None
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    receipt_required_above: Optional[Decimal] = None
    meal_solo_limit: Optional[Decimal] = None
    meal_business_limit: Optional[Decimal] = None
    approval_thresholds: Optional[Dict[str, Decimal]] = None
    blocked_categories: Optional[List[str]] = None


class ExpensePolicyResponse(ExpensePolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    is_active: bool = True
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============== Mileage Schemas ==============

class MileageCalculationRequest(BaseModel):
    departure: str = Field(..., min_length=1)
    arrival: str = Field(..., min_length=1)
    distance_km: Decimal = Field(..., gt=0)
    is_round_trip: bool = False
    vehicle_type: VehicleType = VehicleType.CAR_5CV
    expense_date: date


class MileageCalculationResponse(BaseModel):
    distance_km: Decimal
    rate_applied: Decimal
    amount: Decimal
    vehicle_type: VehicleType
    annual_mileage_before: Decimal
    annual_mileage_after: Decimal


# ============== Statistics ==============

class ExpenseStatsResponse(BaseModel):
    tenant_id: UUID
    period_start: date
    period_end: date
    total_reports: int = 0
    total_amount: Decimal = Decimal("0")
    total_approved: Decimal = Decimal("0")
    total_pending: Decimal = Decimal("0")
    total_rejected: Decimal = Decimal("0")
    average_per_report: Decimal = Decimal("0")
    by_category: Dict[str, Decimal] = Field(default_factory=dict)
    by_employee: Dict[str, Decimal] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)


class EmployeeExpenseStats(BaseModel):
    employee_id: UUID
    year: int
    report_count: int = 0
    total_submitted: Decimal = Decimal("0")
    total_approved: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    total_pending: Decimal = Decimal("0")
    by_category: Dict[str, Decimal] = Field(default_factory=dict)
    average_per_report: Decimal = Decimal("0")


# ============== Validation ==============

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    total_amount: Decimal
    line_count: int


# ============== Filters ==============

class ExpenseReportFilters(BaseModel):
    search: Optional[str] = Field(None, min_length=2)
    status: Optional[List[ExpenseStatus]] = None
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


# ============== Common ==============

class AutocompleteItem(BaseModel):
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]
