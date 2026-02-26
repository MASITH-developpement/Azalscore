"""
AZALS MODULE ASSETS - Schemas Pydantic
======================================

Schemas de validation pour le module de gestion des immobilisations.
"""
from __future__ import annotations


from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================

class AssetTypeEnum(str, Enum):
    # Incorporelles
    INTANGIBLE_GOODWILL = "INTANGIBLE_GOODWILL"
    INTANGIBLE_PATENT = "INTANGIBLE_PATENT"
    INTANGIBLE_LICENSE = "INTANGIBLE_LICENSE"
    INTANGIBLE_SOFTWARE = "INTANGIBLE_SOFTWARE"
    INTANGIBLE_TRADEMARK = "INTANGIBLE_TRADEMARK"
    INTANGIBLE_RD = "INTANGIBLE_RD"
    INTANGIBLE_OTHER = "INTANGIBLE_OTHER"
    # Corporelles
    TANGIBLE_LAND = "TANGIBLE_LAND"
    TANGIBLE_BUILDING = "TANGIBLE_BUILDING"
    TANGIBLE_TECHNICAL = "TANGIBLE_TECHNICAL"
    TANGIBLE_INDUSTRIAL = "TANGIBLE_INDUSTRIAL"
    TANGIBLE_TRANSPORT = "TANGIBLE_TRANSPORT"
    TANGIBLE_OFFICE = "TANGIBLE_OFFICE"
    TANGIBLE_IT = "TANGIBLE_IT"
    TANGIBLE_FURNITURE = "TANGIBLE_FURNITURE"
    TANGIBLE_FIXTURE = "TANGIBLE_FIXTURE"
    TANGIBLE_TOOLS = "TANGIBLE_TOOLS"
    TANGIBLE_OTHER = "TANGIBLE_OTHER"
    # Financieres
    FINANCIAL_PARTICIPATION = "FINANCIAL_PARTICIPATION"
    FINANCIAL_LOAN = "FINANCIAL_LOAN"
    FINANCIAL_DEPOSIT = "FINANCIAL_DEPOSIT"
    FINANCIAL_OTHER = "FINANCIAL_OTHER"
    # En cours
    IN_PROGRESS = "IN_PROGRESS"


class DepreciationMethodEnum(str, Enum):
    LINEAR = "LINEAR"
    DECLINING_BALANCE = "DECLINING_BALANCE"
    UNITS_OF_PRODUCTION = "UNITS_OF_PRODUCTION"
    SUM_OF_YEARS_DIGITS = "SUM_OF_YEARS_DIGITS"
    EXCEPTIONAL = "EXCEPTIONAL"
    NONE = "NONE"


class AssetStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    IN_SERVICE = "IN_SERVICE"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    FULLY_DEPRECIATED = "FULLY_DEPRECIATED"
    DISPOSED = "DISPOSED"
    SCRAPPED = "SCRAPPED"
    TRANSFERRED = "TRANSFERRED"
    STOLEN = "STOLEN"
    DESTROYED = "DESTROYED"


class DisposalTypeEnum(str, Enum):
    SALE = "SALE"
    SCRAP = "SCRAP"
    DONATION = "DONATION"
    THEFT = "THEFT"
    DESTRUCTION = "DESTRUCTION"
    TRANSFER_INTRAGROUP = "TRANSFER_INTRAGROUP"
    EXCHANGE = "EXCHANGE"
    LOSS = "LOSS"


class MovementTypeEnum(str, Enum):
    ACQUISITION = "ACQUISITION"
    IMPROVEMENT = "IMPROVEMENT"
    REVALUATION_UP = "REVALUATION_UP"
    REVALUATION_DOWN = "REVALUATION_DOWN"
    IMPAIRMENT = "IMPAIRMENT"
    IMPAIRMENT_REVERSAL = "IMPAIRMENT_REVERSAL"
    DEPRECIATION = "DEPRECIATION"
    DISPOSAL = "DISPOSAL"
    TRANSFER = "TRANSFER"
    SPLIT = "SPLIT"
    MERGE = "MERGE"


class MaintenanceTypeEnum(str, Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    PREDICTIVE = "PREDICTIVE"
    REGULATORY = "REGULATORY"
    CALIBRATION = "CALIBRATION"
    INSPECTION = "INSPECTION"
    UPGRADE = "UPGRADE"


class MaintenanceStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class InventoryStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VALIDATED = "VALIDATED"
    CANCELLED = "CANCELLED"


class InsuranceStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


# ============================================================================
# CATEGORIES
# ============================================================================

class AssetCategoryBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None


class AssetCategoryCreate(AssetCategoryBase):
    parent_id: UUID | None = None
    default_asset_type: AssetTypeEnum | None = None
    default_depreciation_method: DepreciationMethodEnum = DepreciationMethodEnum.LINEAR
    default_useful_life_years: int | None = None
    default_useful_life_months: int = 0
    default_asset_account: str | None = None
    default_depreciation_account: str | None = None
    default_expense_account: str | None = None
    is_active: bool = True


class AssetCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    parent_id: UUID | None = None
    default_asset_type: AssetTypeEnum | None = None
    default_depreciation_method: DepreciationMethodEnum | None = None
    default_useful_life_years: int | None = None
    default_useful_life_months: int | None = None
    default_asset_account: str | None = None
    default_depreciation_account: str | None = None
    default_expense_account: str | None = None
    is_active: bool | None = None


class AssetCategoryResponse(AssetCategoryBase):
    id: UUID
    parent_id: UUID | None = None
    default_asset_type: AssetTypeEnum | None = None
    default_depreciation_method: DepreciationMethodEnum | None = None
    default_useful_life_years: int | None = None
    default_useful_life_months: int | None = None
    default_asset_account: str | None = None
    default_depreciation_account: str | None = None
    default_expense_account: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# IMMOBILISATIONS
# ============================================================================

class FixedAssetBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    description: str | None = None
    asset_type: AssetTypeEnum


class FixedAssetCreate(FixedAssetBase):
    asset_code: str | None = None  # Auto-generated if not provided
    category_id: UUID | None = None
    parent_asset_id: UUID | None = None
    is_component: bool = False

    # Identification physique
    serial_number: str | None = None
    barcode: str | None = None
    inventory_number: str | None = None
    manufacturer: str | None = None
    brand: str | None = None
    model: str | None = None
    year_manufactured: int | None = None

    # Acquisition
    acquisition_date: date
    in_service_date: date | None = None
    purchase_order_reference: str | None = None
    invoice_reference: str | None = None
    invoice_date: date | None = None
    supplier_id: UUID | None = None
    supplier_name: str | None = None

    # Couts
    purchase_price: Decimal = Decimal("0")
    vat_amount: Decimal = Decimal("0")
    transport_cost: Decimal = Decimal("0")
    installation_cost: Decimal = Decimal("0")
    customs_cost: Decimal = Decimal("0")
    other_costs: Decimal = Decimal("0")

    # Valeur residuelle
    residual_value: Decimal = Decimal("0")
    residual_value_percent: Decimal | None = None

    # Amortissement
    depreciation_method: DepreciationMethodEnum = DepreciationMethodEnum.LINEAR
    useful_life_years: int
    useful_life_months: int = 0
    depreciation_start_date: date | None = None
    declining_balance_rate: Decimal | None = None
    total_units: Decimal | None = None

    # Localisation
    location_id: UUID | None = None
    site_name: str | None = None
    building: str | None = None
    floor: str | None = None
    room: str | None = None
    position: str | None = None
    gps_latitude: Decimal | None = None
    gps_longitude: Decimal | None = None

    # Responsable
    responsible_id: UUID | None = None
    responsible_name: str | None = None
    department_id: UUID | None = None
    department_name: str | None = None
    cost_center: str | None = None

    # Comptes
    asset_account: str | None = None
    depreciation_account: str | None = None
    expense_account: str | None = None

    # Garantie
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    warranty_provider: str | None = None

    # Specifications
    specifications: dict[str, Any] | None = None
    dimensions: str | None = None
    weight: Decimal | None = None
    weight_unit: str = "kg"
    power_rating: str | None = None

    # Compteur
    counter_type: str | None = None
    counter_at_acquisition: Decimal | None = None

    # Notes
    notes: str | None = None
    tags: list[str] | None = None
    currency: str = "EUR"


class FixedAssetUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=300)
    description: str | None = None
    category_id: UUID | None = None
    status: AssetStatusEnum | None = None

    # Identification
    serial_number: str | None = None
    barcode: str | None = None
    inventory_number: str | None = None
    manufacturer: str | None = None
    brand: str | None = None
    model: str | None = None

    # Dates
    in_service_date: date | None = None
    depreciation_start_date: date | None = None

    # Valeur residuelle
    residual_value: Decimal | None = None

    # Localisation
    location_id: UUID | None = None
    site_name: str | None = None
    building: str | None = None
    floor: str | None = None
    room: str | None = None
    position: str | None = None

    # Responsable
    responsible_id: UUID | None = None
    responsible_name: str | None = None
    department_id: UUID | None = None
    department_name: str | None = None
    cost_center: str | None = None

    # Garantie
    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    warranty_provider: str | None = None

    # Maintenance
    next_maintenance_date: date | None = None
    maintenance_frequency_days: int | None = None

    # Compteur
    counter_current: Decimal | None = None

    # Notes
    notes: str | None = None
    internal_notes: str | None = None
    tags: list[str] | None = None
    condition_rating: int | None = Field(None, ge=1, le=5)


class FixedAssetResponse(FixedAssetBase):
    id: UUID
    asset_code: str
    category_id: UUID | None = None
    parent_asset_id: UUID | None = None
    is_component: bool
    status: AssetStatusEnum

    # Identification
    serial_number: str | None = None
    barcode: str | None = None
    qr_code: str | None = None
    inventory_number: str | None = None
    manufacturer: str | None = None
    brand: str | None = None
    model: str | None = None
    year_manufactured: int | None = None

    # Acquisition
    acquisition_date: date
    in_service_date: date | None = None
    invoice_reference: str | None = None
    supplier_name: str | None = None

    # Couts
    purchase_price: Decimal
    acquisition_cost: Decimal
    residual_value: Decimal

    # Amortissement
    depreciation_method: DepreciationMethodEnum
    useful_life_years: int
    useful_life_months: int
    depreciation_start_date: date | None = None

    # Valeurs calculees
    accumulated_depreciation: Decimal
    net_book_value: Decimal | None = None
    impairment_amount: Decimal

    # Localisation
    site_name: str | None = None
    building: str | None = None
    room: str | None = None

    # Responsable
    responsible_name: str | None = None
    department_name: str | None = None
    cost_center: str | None = None

    # Comptes
    asset_account: str | None = None
    depreciation_account: str | None = None

    # Garantie
    warranty_end_date: date | None = None

    # Maintenance
    last_maintenance_date: date | None = None
    next_maintenance_date: date | None = None

    # Cession
    disposal_date: date | None = None
    disposal_type: DisposalTypeEnum | None = None
    disposal_gain_loss: Decimal | None = None

    # Compteur
    counter_type: str | None = None
    counter_current: Decimal | None = None

    # Notes
    notes: str | None = None
    tags: list[str] | None = None
    condition_rating: int | None = None

    currency: str

    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class FixedAssetSummary(BaseModel):
    """Version allégée pour les listes."""
    id: UUID
    asset_code: str
    name: str
    asset_type: AssetTypeEnum
    status: AssetStatusEnum
    acquisition_date: date
    acquisition_cost: Decimal
    net_book_value: Decimal | None = None
    site_name: str | None = None
    responsible_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MISE EN SERVICE
# ============================================================================

class PutInServiceRequest(BaseModel):
    in_service_date: date
    depreciation_start_date: date | None = None
    location_id: UUID | None = None
    site_name: str | None = None
    responsible_id: UUID | None = None
    responsible_name: str | None = None
    notes: str | None = None


# ============================================================================
# CESSION
# ============================================================================

class DisposeAssetRequest(BaseModel):
    disposal_date: date
    disposal_type: DisposalTypeEnum
    disposal_proceeds: Decimal = Decimal("0")
    disposal_costs: Decimal = Decimal("0")
    buyer_name: str | None = None
    buyer_id: UUID | None = None
    notes: str | None = None


class DisposalResponse(BaseModel):
    asset_id: UUID
    asset_code: str
    disposal_date: date
    disposal_type: DisposalTypeEnum
    gross_value: Decimal
    accumulated_depreciation: Decimal
    net_book_value: Decimal
    disposal_proceeds: Decimal
    disposal_costs: Decimal
    gain_loss: Decimal
    accounting_entries: list[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TABLEAU D'AMORTISSEMENT
# ============================================================================

class DepreciationScheduleEntryResponse(BaseModel):
    id: UUID
    period_number: int
    period_start: date
    period_end: date
    fiscal_year: int | None = None

    opening_gross_value: Decimal
    opening_accumulated_depreciation: Decimal
    opening_net_book_value: Decimal

    depreciation_rate: Decimal | None = None
    depreciation_amount: Decimal
    prorata_days: int | None = None

    fiscal_depreciation_amount: Decimal | None = None
    deferred_depreciation: Decimal | None = None

    closing_accumulated_depreciation: Decimal
    closing_net_book_value: Decimal

    is_posted: bool

    model_config = ConfigDict(from_attributes=True)


class DepreciationScheduleResponse(BaseModel):
    asset_id: UUID
    asset_code: str
    asset_name: str
    depreciation_method: DepreciationMethodEnum
    useful_life_years: int
    useful_life_months: int
    acquisition_cost: Decimal
    residual_value: Decimal
    entries: list[DepreciationScheduleEntryResponse]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EXECUTION AMORTISSEMENTS
# ============================================================================

class DepreciationRunCreate(BaseModel):
    period_start: date
    period_end: date
    fiscal_year: int | None = None
    period_number: int | None = None
    description: str | None = None


class DepreciationRunResponse(BaseModel):
    id: UUID
    run_number: str
    run_date: date
    period_start: date
    period_end: date
    fiscal_year: int | None = None

    assets_processed: int
    total_depreciation: Decimal
    errors_count: int

    status: str
    validated_at: datetime | None = None
    posted_at: datetime | None = None

    entries: list[dict[str, Any]] | None = None
    errors: list[dict[str, Any]] | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MOUVEMENTS
# ============================================================================

class AssetMovementCreate(BaseModel):
    movement_type: MovementTypeEnum
    movement_date: date
    amount: Decimal
    reference: str | None = None
    description: str | None = None
    effective_date: date | None = None
    document_reference: str | None = None
    notes: str | None = None

    # Pour transferts
    to_location_id: UUID | None = None
    to_responsible_id: UUID | None = None


class AssetMovementResponse(BaseModel):
    id: UUID
    asset_id: UUID
    movement_type: MovementTypeEnum
    movement_date: date
    movement_number: str | None = None
    reference: str | None = None
    description: str | None = None

    amount: Decimal
    previous_value: Decimal | None = None
    new_value: Decimal | None = None

    is_posted: bool
    journal_entry_id: UUID | None = None

    created_at: datetime
    created_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MAINTENANCE
# ============================================================================

class AssetMaintenanceCreate(BaseModel):
    maintenance_type: MaintenanceTypeEnum
    title: str = Field(..., min_length=5, max_length=300)
    description: str | None = None

    scheduled_date: date
    scheduled_end_date: date | None = None

    technician_id: UUID | None = None
    technician_name: str | None = None
    external_provider_id: UUID | None = None
    external_provider_name: str | None = None

    labor_cost: Decimal = Decimal("0")
    parts_cost: Decimal = Decimal("0")
    external_cost: Decimal = Decimal("0")
    other_cost: Decimal = Decimal("0")

    parts_used: list[dict[str, Any]] | None = None
    notes: str | None = None


class AssetMaintenanceUpdate(BaseModel):
    maintenance_type: MaintenanceTypeEnum | None = None
    title: str | None = Field(None, min_length=5, max_length=300)
    description: str | None = None
    status: MaintenanceStatusEnum | None = None

    scheduled_date: date | None = None
    scheduled_end_date: date | None = None
    actual_start_date: datetime | None = None
    actual_end_date: datetime | None = None
    duration_hours: Decimal | None = None

    technician_id: UUID | None = None
    technician_name: str | None = None

    labor_cost: Decimal | None = None
    parts_cost: Decimal | None = None
    external_cost: Decimal | None = None
    other_cost: Decimal | None = None

    work_performed: str | None = None
    parts_used: list[dict[str, Any]] | None = None
    counter_reading: Decimal | None = None

    affects_depreciation: bool | None = None
    capitalized_amount: Decimal | None = None
    extends_useful_life: bool | None = None
    additional_life_months: int | None = None

    notes: str | None = None


class AssetMaintenanceComplete(BaseModel):
    actual_end_date: datetime | None = None
    work_performed: str
    duration_hours: Decimal | None = None

    labor_cost: Decimal | None = None
    parts_cost: Decimal | None = None
    external_cost: Decimal | None = None
    other_cost: Decimal | None = None

    parts_used: list[dict[str, Any]] | None = None
    counter_reading: Decimal | None = None

    next_maintenance_date: date | None = None
    notes: str | None = None


class AssetMaintenanceResponse(BaseModel):
    id: UUID
    asset_id: UUID
    maintenance_number: str | None = None
    maintenance_type: MaintenanceTypeEnum
    status: MaintenanceStatusEnum

    title: str
    description: str | None = None
    work_performed: str | None = None

    scheduled_date: date
    scheduled_end_date: date | None = None
    actual_start_date: datetime | None = None
    actual_end_date: datetime | None = None
    duration_hours: Decimal | None = None

    technician_name: str | None = None
    external_provider_name: str | None = None

    labor_cost: Decimal
    parts_cost: Decimal
    external_cost: Decimal
    other_cost: Decimal
    total_cost: Decimal

    counter_reading: Decimal | None = None
    next_maintenance_date: date | None = None

    affects_depreciation: bool
    capitalized_amount: Decimal | None = None

    created_at: datetime
    created_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INVENTAIRE
# ============================================================================

class AssetInventoryCreate(BaseModel):
    inventory_date: date
    description: str | None = None
    location_id: UUID | None = None
    location_name: str | None = None
    category_id: UUID | None = None
    department_id: UUID | None = None
    responsible_id: UUID | None = None
    responsible_name: str | None = None


class AssetInventoryItemUpdate(BaseModel):
    found: bool
    actual_location: str | None = None
    scanned_barcode: str | None = None
    condition_rating: int | None = Field(None, ge=1, le=5)
    condition_notes: str | None = None
    photo_url: str | None = None
    notes: str | None = None


class AssetInventoryItemResponse(BaseModel):
    id: UUID
    asset_id: UUID | None = None
    asset_code: str | None = None
    asset_name: str | None = None
    expected_location: str | None = None
    expected_barcode: str | None = None

    found: bool | None = None
    actual_location: str | None = None
    scanned_barcode: str | None = None
    scanned_at: datetime | None = None

    condition_rating: int | None = None
    condition_notes: str | None = None
    is_unexpected: bool
    location_mismatch: bool

    model_config = ConfigDict(from_attributes=True)


class AssetInventoryResponse(BaseModel):
    id: UUID
    inventory_number: str
    inventory_date: date
    description: str | None = None

    location_name: str | None = None
    status: InventoryStatusEnum

    assets_expected: int
    assets_found: int
    assets_missing: int
    assets_unexpected: int
    assets_condition_issues: int

    responsible_name: str | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None
    validated_at: datetime | None = None

    items: list[AssetInventoryItemResponse] | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ASSURANCE
# ============================================================================

class AssetInsurancePolicyCreate(BaseModel):
    policy_number: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=2, max_length=300)
    description: str | None = None

    insurer_name: str = Field(..., min_length=2, max_length=200)
    insurer_contact: str | None = None
    insurer_phone: str | None = None
    insurer_email: str | None = None

    coverage_type: str | None = None
    coverage_description: str | None = None
    exclusions: str | None = None

    total_insured_value: Decimal | None = None
    deductible_amount: Decimal | None = None
    premium_amount: Decimal | None = None
    premium_frequency: str | None = None

    start_date: date
    end_date: date
    auto_renewal: bool = False

    notes: str | None = None


class AssetInsurancePolicyResponse(BaseModel):
    id: UUID
    policy_number: str
    name: str
    description: str | None = None

    insurer_name: str
    insurer_contact: str | None = None

    coverage_type: str | None = None
    total_insured_value: Decimal | None = None
    deductible_amount: Decimal | None = None
    premium_amount: Decimal | None = None
    premium_frequency: str | None = None

    start_date: date
    end_date: date
    status: InsuranceStatusEnum
    auto_renewal: bool

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetInsuranceItemCreate(BaseModel):
    asset_id: UUID
    insured_value: Decimal
    coverage_start_date: date | None = None
    coverage_end_date: date | None = None
    notes: str | None = None


# ============================================================================
# TRANSFERTS
# ============================================================================

class AssetTransferCreate(BaseModel):
    transfer_date: date
    reason: str | None = None

    to_location_id: UUID | None = None
    to_location_name: str | None = None
    to_responsible_id: UUID | None = None
    to_responsible_name: str | None = None
    to_department_id: UUID | None = None
    to_cost_center: str | None = None

    notes: str | None = None


class AssetTransferResponse(BaseModel):
    id: UUID
    asset_id: UUID
    transfer_number: str
    transfer_date: date

    from_location_name: str | None = None
    from_responsible_name: str | None = None
    from_cost_center: str | None = None

    to_location_name: str | None = None
    to_responsible_name: str | None = None
    to_cost_center: str | None = None

    reason: str | None = None
    status: str

    approved_at: datetime | None = None
    completed_at: datetime | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# VALORISATION
# ============================================================================

class AssetValuationResponse(BaseModel):
    valuation_date: date
    fiscal_year: int | None = None

    total_assets_count: int
    total_gross_value: Decimal
    total_accumulated_depreciation: Decimal
    total_net_book_value: Decimal
    total_impairment: Decimal
    total_revaluation_surplus: Decimal

    by_asset_type: dict[str, Any] | None = None
    by_category: dict[str, Any] | None = None
    by_location: dict[str, Any] | None = None
    by_department: dict[str, Any] | None = None

    currency: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# FILTRES
# ============================================================================

class AssetFilters(BaseModel):
    search: str | None = None
    status: list[AssetStatusEnum] | None = None
    asset_type: list[AssetTypeEnum] | None = None
    category_id: UUID | None = None
    location_id: UUID | None = None
    responsible_id: UUID | None = None
    department_id: UUID | None = None

    acquisition_date_from: date | None = None
    acquisition_date_to: date | None = None

    min_value: Decimal | None = None
    max_value: Decimal | None = None

    warranty_expiring_before: date | None = None
    maintenance_due_before: date | None = None

    tags: list[str] | None = None


# ============================================================================
# LISTES PAGINÉES
# ============================================================================

class PaginatedAssetResponse(BaseModel):
    items: list[FixedAssetSummary]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedMaintenanceResponse(BaseModel):
    items: list[AssetMaintenanceResponse]
    total: int
    page: int
    page_size: int


class PaginatedMovementResponse(BaseModel):
    items: list[AssetMovementResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# AUTOCOMPLETE
# ============================================================================

class AssetAutocompleteItem(BaseModel):
    id: UUID
    asset_code: str
    name: str
    asset_type: AssetTypeEnum
    status: AssetStatusEnum
    site_name: str | None = None
    label: str  # [CODE] Name - Site

    model_config = ConfigDict(from_attributes=True)


class AssetAutocompleteResponse(BaseModel):
    suggestions: list[AssetAutocompleteItem]
    total: int


# ============================================================================
# STATISTIQUES
# ============================================================================

class AssetStatistics(BaseModel):
    # Comptages
    total_assets: int = 0
    assets_in_service: int = 0
    assets_fully_depreciated: int = 0
    assets_disposed: int = 0
    assets_under_maintenance: int = 0

    # Valeurs
    total_gross_value: Decimal = Decimal("0")
    total_accumulated_depreciation: Decimal = Decimal("0")
    total_net_book_value: Decimal = Decimal("0")

    # Par type
    by_asset_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    value_by_asset_type: dict[str, Decimal] = {}

    # Alertes
    warranty_expiring_soon: int = 0
    maintenance_overdue: int = 0
    maintenance_due_soon: int = 0

    # Acquisitions/Cessions (mois en cours)
    acquisitions_this_month: int = 0
    acquisitions_value_this_month: Decimal = Decimal("0")
    disposals_this_month: int = 0
    disposals_value_this_month: Decimal = Decimal("0")

    # Amortissements
    depreciation_this_year: Decimal = Decimal("0")
    depreciation_this_month: Decimal = Decimal("0")


class AssetDashboard(BaseModel):
    statistics: AssetStatistics
    recent_acquisitions: list[FixedAssetSummary] = []
    recent_disposals: list[FixedAssetSummary] = []
    upcoming_maintenances: list[AssetMaintenanceResponse] = []
    warranty_expiring: list[FixedAssetSummary] = []
    depreciation_summary: dict[str, Any] = {}


# ============================================================================
# GENERATION CODES-BARRES/QR
# ============================================================================

class BarcodeGenerateRequest(BaseModel):
    asset_ids: list[UUID]
    barcode_type: str = "CODE128"  # CODE128, QR, DATAMATRIX
    include_info: bool = True  # Inclure infos dans QR


class BarcodeResponse(BaseModel):
    asset_id: UUID
    asset_code: str
    barcode_data: str
    barcode_image: str | None = None  # Base64
    qr_content: str | None = None


# ============================================================================
# RAPPORTS
# ============================================================================

class AssetRegisterRequest(BaseModel):
    as_of_date: date | None = None
    category_id: UUID | None = None
    asset_type: AssetTypeEnum | None = None
    status: AssetStatusEnum | None = None
    location_id: UUID | None = None
    include_disposed: bool = False


class DepreciationReportRequest(BaseModel):
    fiscal_year: int
    period: int | None = None  # Mois 1-12, None = annuel
    category_id: UUID | None = None
    asset_type: AssetTypeEnum | None = None


class TaxDeclarationRequest(BaseModel):
    fiscal_year: int
    declaration_type: str = "2054"  # 2054, 2055, 2059
