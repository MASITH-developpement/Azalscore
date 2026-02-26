"""
Schémas Pydantic - Module Forecasting (GAP-076)

Validation stricte, types correspondant au frontend.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============== Énumérations ==============

class ForecastType(str, Enum):
    SALES = "sales"
    REVENUE = "revenue"
    CASH_FLOW = "cash_flow"
    INVENTORY = "inventory"
    DEMAND = "demand"
    EXPENSE = "expense"
    HEADCOUNT = "headcount"
    CUSTOM = "custom"


class ForecastMethod(str, Enum):
    MOVING_AVERAGE = "moving_average"
    WEIGHTED_AVERAGE = "weighted_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL = "seasonal"
    ARIMA = "arima"
    MANUAL = "manual"
    HYBRID = "hybrid"


class Granularity(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ForecastStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ScenarioType(str, Enum):
    BASELINE = "baseline"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    BEST_CASE = "best_case"
    WORST_CASE = "worst_case"
    CUSTOM = "custom"


class BudgetStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCKED = "locked"


class KPIStatus(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


# ============== Forecast Schemas ==============

class ForecastPeriod(BaseModel):
    """Période de prévision."""
    period: str
    value: Decimal = Decimal("0")
    confidence_low: Optional[Decimal] = None
    confidence_high: Optional[Decimal] = None
    manual_adjustment: Optional[Decimal] = None
    adjusted_value: Optional[Decimal] = None


class ForecastBase(BaseModel):
    """Base pour Forecast."""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    forecast_type: ForecastType = ForecastType.SALES
    method: ForecastMethod = ForecastMethod.MOVING_AVERAGE
    status: ForecastStatus = ForecastStatus.DRAFT
    start_date: date
    end_date: date
    granularity: Granularity = Granularity.MONTHLY
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    model_id: Optional[UUID] = None
    assumptions: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError('end_date must be after start_date')
        return self


class ForecastCreate(ForecastBase):
    """Création de prévision."""
    periods: List[ForecastPeriod] = Field(default_factory=list)


class ForecastUpdate(BaseModel):
    """Mise à jour de prévision."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    status: Optional[ForecastStatus] = None
    method: Optional[ForecastMethod] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    model_id: Optional[UUID] = None
    assumptions: Optional[List[str]] = None
    notes: Optional[str] = None
    periods: Optional[List[ForecastPeriod]] = None


class ForecastResponse(ForecastBase):
    """Réponse Forecast."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    periods: List[Dict[str, Any]] = Field(default_factory=list)
    total_forecasted: Decimal = Decimal("0")
    average_per_period: Decimal = Decimal("0")
    actual_to_date: Decimal = Decimal("0")
    variance: Decimal = Decimal("0")
    variance_percent: Decimal = Decimal("0")
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class ForecastListItem(BaseModel):
    """Item léger pour les listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    forecast_type: ForecastType
    status: ForecastStatus
    start_date: date
    end_date: date
    total_forecasted: Decimal
    created_at: datetime


class ForecastList(BaseModel):
    """Réponse paginée."""
    items: List[ForecastListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== ForecastModel Schemas ==============

class ForecastModelBase(BaseModel):
    """Base pour ForecastModel."""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    forecast_type: ForecastType = ForecastType.SALES
    method: ForecastMethod = ForecastMethod.MOVING_AVERAGE
    parameters: Dict[str, Any] = Field(default_factory=dict)
    training_period_months: int = Field(default=12, ge=1, le=120)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class ForecastModelCreate(ForecastModelBase):
    """Création de modèle."""
    pass


class ForecastModelUpdate(BaseModel):
    """Mise à jour de modèle."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    method: Optional[ForecastMethod] = None
    parameters: Optional[Dict[str, Any]] = None
    training_period_months: Optional[int] = Field(None, ge=1, le=120)
    is_active: Optional[bool] = None


class ForecastModelResponse(ForecastModelBase):
    """Réponse ForecastModel."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    accuracy_metrics: Dict[str, Any] = Field(default_factory=dict)
    last_trained_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


# ============== Scenario Schemas ==============

class ScenarioBase(BaseModel):
    """Base pour Scenario."""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    scenario_type: ScenarioType = ScenarioType.BASELINE
    base_forecast_id: UUID
    adjustment_type: str = Field(default="percent", pattern="^(percent|absolute)$")
    adjustment_value: Decimal = Decimal("0")
    assumptions: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class ScenarioCreate(ScenarioBase):
    """Création de scénario."""
    pass


class ScenarioUpdate(BaseModel):
    """Mise à jour de scénario."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    scenario_type: Optional[ScenarioType] = None
    adjustment_type: Optional[str] = Field(None, pattern="^(percent|absolute)$")
    adjustment_value: Optional[Decimal] = None
    assumptions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ScenarioResponse(ScenarioBase):
    """Réponse Scenario."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    periods: List[Dict[str, Any]] = Field(default_factory=list)
    total_forecasted: Decimal = Decimal("0")
    variance_from_baseline: Decimal = Decimal("0")
    variance_percent: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


# ============== Budget Schemas ==============

class BudgetLineSchema(BaseModel):
    """Ligne de budget."""
    account_code: str
    account_name: str
    period_amounts: Dict[str, Decimal] = Field(default_factory=dict)
    notes: Optional[str] = None


class BudgetBase(BaseModel):
    """Base pour Budget."""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    fiscal_year: int = Field(..., ge=2000, le=2100)
    start_date: date
    end_date: date
    granularity: Granularity = Granularity.MONTHLY
    department_id: Optional[UUID] = None
    department_name: Optional[str] = Field(None, max_length=100)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError('end_date must be after start_date')
        return self


class BudgetCreate(BudgetBase):
    """Création de budget."""
    lines: List[BudgetLineSchema] = Field(default_factory=list)


class BudgetUpdate(BaseModel):
    """Mise à jour de budget."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    status: Optional[BudgetStatus] = None
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    lines: Optional[List[BudgetLineSchema]] = None


class BudgetResponse(BudgetBase):
    """Réponse Budget."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: BudgetStatus = BudgetStatus.DRAFT
    lines: List[Dict[str, Any]] = Field(default_factory=list)
    total_budget: Decimal = Decimal("0")
    total_actual: Decimal = Decimal("0")
    total_variance: Decimal = Decimal("0")
    variance_percent: Decimal = Decimal("0")
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    parent_budget_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class BudgetListItem(BaseModel):
    """Item léger pour les listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    fiscal_year: int
    status: BudgetStatus
    total_budget: Decimal
    total_actual: Decimal
    variance_percent: Decimal
    created_at: datetime


class BudgetList(BaseModel):
    """Réponse paginée."""
    items: List[BudgetListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== KPI Schemas ==============

class KPIBase(BaseModel):
    """Base pour KPI."""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    formula: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    target_value: Decimal = Decimal("0")
    green_threshold: Decimal = Decimal("0")
    amber_threshold: Decimal = Decimal("0")
    red_threshold: Decimal = Decimal("0")
    update_frequency: str = Field(default="monthly", max_length=20)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


class KPICreate(KPIBase):
    """Création de KPI."""
    pass


class KPIUpdate(BaseModel):
    """Mise à jour de KPI."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    category: Optional[str] = None
    formula: Optional[str] = None
    unit: Optional[str] = None
    target_value: Optional[Decimal] = None
    green_threshold: Optional[Decimal] = None
    amber_threshold: Optional[Decimal] = None
    red_threshold: Optional[Decimal] = None
    update_frequency: Optional[str] = None
    is_active: Optional[bool] = None


class KPIValueUpdate(BaseModel):
    """Mise à jour de la valeur d'un KPI."""
    value: Decimal
    measurement_date: Optional[datetime] = None


class KPIResponse(KPIBase):
    """Réponse KPI."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    current_value: Decimal = Decimal("0")
    previous_value: Decimal = Decimal("0")
    achievement_percent: Decimal = Decimal("0")
    trend: str = "stable"
    status: KPIStatus = KPIStatus.GREEN
    last_measured_at: Optional[datetime] = None
    historical_values: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    is_deleted: bool = False
    version: int = 1


class KPIListItem(BaseModel):
    """Item léger pour les listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: Optional[str] = None
    current_value: Decimal
    target_value: Decimal
    achievement_percent: Decimal
    status: KPIStatus
    trend: str


class KPIList(BaseModel):
    """Réponse paginée."""
    items: List[KPIListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Autocomplete ==============

class AutocompleteItem(BaseModel):
    """Item d'autocomplete."""
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
    items: List[ForecastCreate] = Field(..., min_length=1, max_length=1000)


class BulkUpdateRequest(BaseModel):
    """Requête mise à jour en masse."""
    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    data: ForecastUpdate


class BulkDeleteRequest(BaseModel):
    """Requête suppression en masse."""
    ids: List[UUID] = Field(..., min_length=1, max_length=1000)
    hard: bool = False


class BulkResult(BaseModel):
    """Résultat opération bulk."""
    success: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ============== Filters ==============

class ForecastFilters(BaseModel):
    """Filtres pour les prévisions."""
    search: Optional[str] = Field(None, min_length=2)
    forecast_type: Optional[List[ForecastType]] = None
    status: Optional[List[ForecastStatus]] = None
    method: Optional[List[ForecastMethod]] = None
    category: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class BudgetFilters(BaseModel):
    """Filtres pour les budgets."""
    search: Optional[str] = Field(None, min_length=2)
    fiscal_year: Optional[int] = None
    status: Optional[List[BudgetStatus]] = None
    department_id: Optional[UUID] = None


class KPIFilters(BaseModel):
    """Filtres pour les KPIs."""
    search: Optional[str] = Field(None, min_length=2)
    category: Optional[str] = None
    status: Optional[List[KPIStatus]] = None
    is_active: Optional[bool] = None


# ============== Reports ==============

class VarianceReport(BaseModel):
    """Rapport de variance budgétaire."""
    budget_id: UUID
    name: str
    fiscal_year: int
    total_budget: Decimal
    total_actual: Decimal
    total_variance: Decimal
    variance_percent: Decimal
    lines: List[Dict[str, Any]]


class ScenarioComparison(BaseModel):
    """Comparaison de scénarios."""
    scenarios: List[Dict[str, Any]]
    periods: List[Dict[str, Any]]


class KPIDashboard(BaseModel):
    """Tableau de bord KPI."""
    total_kpis: int
    by_status: Dict[str, int]
    by_category: Dict[str, List[Dict[str, Any]]]
    alerts: List[Dict[str, Any]]
