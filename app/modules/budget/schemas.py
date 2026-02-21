"""
AZALS MODULE - BUDGET: Schemas
===============================

Schemas Pydantic pour la gestion budgetaire.

Auteur: AZALSCORE Team
Version: 2.0.0
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    AlertSeverity,
    AlertStatus,
    AllocationMethod,
    BudgetLineType,
    BudgetPeriodType,
    BudgetStatus,
    BudgetType,
    ControlMode,
    ForecastConfidence,
    RevisionStatus,
    ScenarioType,
    VarianceType,
)


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class PaginatedResponse(BaseModel):
    """Schema de base pour les reponses paginées."""
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# BUDGET CATEGORY SCHEMAS
# ============================================================================

class BudgetCategoryBase(BaseModel):
    """Schema de base pour les categories budgetaires."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    line_type: BudgetLineType = BudgetLineType.EXPENSE
    parent_id: Optional[UUID] = None
    account_codes: List[str] = Field(default_factory=list)
    sort_order: int = 0
    is_active: bool = True


class BudgetCategoryCreate(BudgetCategoryBase):
    """Schema pour creer une categorie."""
    pass


class BudgetCategoryUpdate(BaseModel):
    """Schema pour mettre a jour une categorie."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    line_type: Optional[BudgetLineType] = None
    parent_id: Optional[UUID] = None
    account_codes: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class BudgetCategoryResponse(BudgetCategoryBase):
    """Schema de reponse pour une categorie."""
    id: UUID
    tenant_id: str
    level: int = 0
    path: Optional[str] = None
    is_summary: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBudgetCategories(PaginatedResponse):
    """Reponse paginée de categories."""
    items: List[BudgetCategoryResponse]


# ============================================================================
# BUDGET LINE SCHEMAS
# ============================================================================

class BudgetLineBase(BaseModel):
    """Schema de base pour les lignes budgetaires."""
    category_id: UUID
    code: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    line_type: BudgetLineType = BudgetLineType.EXPENSE
    annual_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("-999999999999"))
    allocation_method: AllocationMethod = AllocationMethod.EQUAL
    seasonal_profile: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = None
    cost_center_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    account_code: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    assumptions: Optional[str] = None


class BudgetLineCreate(BudgetLineBase):
    """Schema pour creer une ligne."""
    monthly_distribution: Optional[Dict[int, Decimal]] = None
    custom_warning_threshold: Optional[Decimal] = None
    custom_critical_threshold: Optional[Decimal] = None


class BudgetLineUpdate(BaseModel):
    """Schema pour mettre a jour une ligne."""
    category_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    annual_amount: Optional[Decimal] = None
    monthly_distribution: Optional[Dict[int, Decimal]] = None
    allocation_method: Optional[AllocationMethod] = None
    seasonal_profile: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    cost_center_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    account_code: Optional[str] = None
    notes: Optional[str] = None


class BudgetLineResponse(BudgetLineBase):
    """Schema de reponse pour une ligne."""
    id: UUID
    tenant_id: str
    budget_id: UUID
    monthly_distribution: Dict[str, Decimal] = Field(default_factory=dict)
    parent_line_id: Optional[UUID] = None
    sort_order: int = 0
    is_summary: bool = False
    ytd_actual: Decimal = Decimal("0")
    ytd_committed: Decimal = Decimal("0")
    remaining_budget: Decimal = Decimal("0")
    consumption_rate: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBudgetLines(PaginatedResponse):
    """Reponse paginée de lignes."""
    items: List[BudgetLineResponse]


# ============================================================================
# BUDGET PERIOD SCHEMAS
# ============================================================================

class BudgetPeriodResponse(BaseModel):
    """Schema de reponse pour une periode."""
    id: UUID
    tenant_id: str
    budget_id: UUID
    period_number: int
    name: str
    start_date: date
    end_date: date
    is_open: bool
    is_locked: bool
    total_budget: Decimal
    total_actual: Decimal
    total_committed: Decimal
    total_available: Decimal
    variance: Decimal

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# BUDGET SCHEMAS
# ============================================================================

class BudgetBase(BaseModel):
    """Schema de base pour les budgets."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    budget_type: BudgetType = BudgetType.OPERATING
    period_type: BudgetPeriodType = BudgetPeriodType.ANNUAL
    fiscal_year: int = Field(..., ge=2000, le=2100)
    start_date: date
    end_date: date
    currency: str = Field(default="EUR", max_length=3)
    entity_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    control_mode: ControlMode = ControlMode.WARNING_ONLY
    warning_threshold: Decimal = Field(default=Decimal("80.00"), ge=0, le=100)
    critical_threshold: Decimal = Field(default=Decimal("95.00"), ge=0, le=100)
    notes: Optional[str] = None
    assumptions: Optional[str] = None
    objectives: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator('end_date')
    @classmethod
    def end_date_after_start(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class BudgetCreate(BudgetBase):
    """Schema pour creer un budget."""
    owner_id: Optional[UUID] = None
    approvers: List[UUID] = Field(default_factory=list)
    template_id: Optional[UUID] = None  # Creer depuis un template
    copy_from_id: Optional[UUID] = None  # Copier depuis un budget existant


class BudgetUpdate(BaseModel):
    """Schema pour mettre a jour un budget."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    control_mode: Optional[ControlMode] = None
    warning_threshold: Optional[Decimal] = None
    critical_threshold: Optional[Decimal] = None
    notes: Optional[str] = None
    assumptions: Optional[str] = None
    objectives: Optional[str] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[UUID] = None
    approvers: Optional[List[UUID]] = None


class BudgetResponse(BudgetBase):
    """Schema de reponse pour un budget."""
    id: UUID
    tenant_id: str
    status: BudgetStatus
    version_number: int
    is_current_version: bool
    parent_budget_id: Optional[UUID] = None
    total_revenue: Decimal
    total_expense: Decimal
    total_investment: Decimal
    net_result: Decimal
    owner_id: Optional[UUID] = None
    approvers: List[UUID] = Field(default_factory=list)
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetDetailResponse(BudgetResponse):
    """Schema de reponse detaillé pour un budget."""
    lines: List[BudgetLineResponse] = Field(default_factory=list)
    periods: List[BudgetPeriodResponse] = Field(default_factory=list)
    approval_history: List[Dict[str, Any]] = Field(default_factory=list)


class PaginatedBudgets(PaginatedResponse):
    """Reponse paginée de budgets."""
    items: List[BudgetResponse]


# ============================================================================
# BUDGET REVISION SCHEMAS
# ============================================================================

class RevisionDetailCreate(BaseModel):
    """Detail d'une revision."""
    budget_line_id: UUID
    new_amount: Decimal
    affected_period: Optional[int] = None
    justification: Optional[str] = None


class BudgetRevisionCreate(BaseModel):
    """Schema pour creer une revision."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    effective_date: date
    reason: str
    impact_analysis: Optional[str] = None
    details: List[RevisionDetailCreate]


class BudgetRevisionUpdate(BaseModel):
    """Schema pour mettre a jour une revision."""
    name: Optional[str] = None
    description: Optional[str] = None
    effective_date: Optional[date] = None
    reason: Optional[str] = None
    impact_analysis: Optional[str] = None


class RevisionDetailResponse(BaseModel):
    """Detail d'une revision."""
    id: UUID
    budget_line_id: Optional[UUID]
    previous_amount: Decimal
    new_amount: Decimal
    change_amount: Decimal
    affected_period: Optional[int] = None
    justification: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetRevisionResponse(BaseModel):
    """Schema de reponse pour une revision."""
    id: UUID
    tenant_id: str
    budget_id: UUID
    revision_number: int
    name: str
    description: Optional[str] = None
    status: RevisionStatus
    effective_date: date
    reason: str
    impact_analysis: Optional[str] = None
    total_change_amount: Decimal
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    applied_at: Optional[datetime] = None
    details: List[RevisionDetailResponse] = Field(default_factory=list)
    created_at: datetime
    created_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedBudgetRevisions(PaginatedResponse):
    """Reponse paginée de revisions."""
    items: List[BudgetRevisionResponse]


# ============================================================================
# BUDGET ACTUAL SCHEMAS
# ============================================================================

class BudgetActualCreate(BaseModel):
    """Schema pour enregistrer un realise."""
    budget_line_id: Optional[UUID] = None
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    amount: Decimal
    line_type: BudgetLineType = BudgetLineType.EXPENSE
    source: str = Field(default="MANUAL", max_length=50)
    source_document_type: Optional[str] = None
    source_document_id: Optional[UUID] = None
    reference: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    account_code: Optional[str] = Field(None, max_length=20)
    cost_center_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class BudgetActualResponse(BaseModel):
    """Schema de reponse pour un realise."""
    id: UUID
    tenant_id: str
    budget_id: UUID
    budget_line_id: Optional[UUID]
    period: str
    period_date: date
    amount: Decimal
    line_type: BudgetLineType
    source: str
    source_document_type: Optional[str] = None
    source_document_id: Optional[UUID] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    account_code: Optional[str] = None
    created_at: datetime
    created_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedBudgetActuals(PaginatedResponse):
    """Reponse paginée de realises."""
    items: List[BudgetActualResponse]


# ============================================================================
# BUDGET ALERT SCHEMAS
# ============================================================================

class BudgetAlertResponse(BaseModel):
    """Schema de reponse pour une alerte."""
    id: UUID
    tenant_id: str
    budget_id: UUID
    budget_line_id: Optional[UUID]
    alert_type: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    threshold_percent: Optional[Decimal] = None
    current_percent: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    period: Optional[str] = None
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledge(BaseModel):
    """Schema pour acquitter une alerte."""
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    """Schema pour resoudre une alerte."""
    resolution_notes: str


class PaginatedBudgetAlerts(PaginatedResponse):
    """Reponse paginée d'alertes."""
    items: List[BudgetAlertResponse]


# ============================================================================
# BUDGET FORECAST SCHEMAS
# ============================================================================

class BudgetForecastCreate(BaseModel):
    """Schema pour creer une prevision."""
    budget_line_id: Optional[UUID] = None
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    revised_forecast: Decimal
    confidence: ForecastConfidence = ForecastConfidence.MEDIUM
    probability: Optional[Decimal] = Field(None, ge=0, le=100)
    assumptions: Optional[str] = None
    methodology: Optional[str] = Field(None, max_length=100)


class BudgetForecastResponse(BaseModel):
    """Schema de reponse pour une prevision."""
    id: UUID
    tenant_id: str
    budget_id: UUID
    budget_line_id: Optional[UUID]
    forecast_date: date
    period: str
    original_budget: Decimal
    revised_forecast: Decimal
    variance: Decimal
    variance_percent: Optional[Decimal]
    confidence: ForecastConfidence
    probability: Optional[Decimal]
    assumptions: Optional[str]
    methodology: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]

    model_config = ConfigDict(from_attributes=True)


class PaginatedBudgetForecasts(PaginatedResponse):
    """Reponse paginée de previsions."""
    items: List[BudgetForecastResponse]


# ============================================================================
# BUDGET SCENARIO SCHEMAS
# ============================================================================

class ScenarioLineCreate(BaseModel):
    """Ligne de scenario."""
    budget_line_id: UUID
    adjusted_amount: Optional[Decimal] = None
    adjustment_percent: Optional[Decimal] = None
    justification: Optional[str] = None


class BudgetScenarioCreate(BaseModel):
    """Schema pour creer un scenario."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    scenario_type: ScenarioType = ScenarioType.WHAT_IF
    revenue_adjustment_percent: Decimal = Field(default=Decimal("0"))
    expense_adjustment_percent: Decimal = Field(default=Decimal("0"))
    assumptions: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    lines: Optional[List[ScenarioLineCreate]] = None


class BudgetScenarioUpdate(BaseModel):
    """Schema pour mettre a jour un scenario."""
    name: Optional[str] = None
    description: Optional[str] = None
    revenue_adjustment_percent: Optional[Decimal] = None
    expense_adjustment_percent: Optional[Decimal] = None
    assumptions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ScenarioLineResponse(BaseModel):
    """Reponse ligne de scenario."""
    id: UUID
    scenario_id: UUID
    budget_line_id: UUID
    original_amount: Decimal
    adjusted_amount: Decimal
    adjustment_percent: Optional[Decimal]
    variance: Optional[Decimal]
    justification: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BudgetScenarioResponse(BaseModel):
    """Schema de reponse pour un scenario."""
    id: UUID
    tenant_id: str
    budget_id: UUID
    name: str
    description: Optional[str]
    scenario_type: ScenarioType
    is_active: bool
    is_default: bool
    revenue_adjustment_percent: Decimal
    expense_adjustment_percent: Decimal
    assumptions: Optional[Dict[str, Any]]
    total_revenue: Decimal
    total_expense: Decimal
    net_result: Decimal
    variance_vs_baseline: Optional[Decimal]
    lines: List[ScenarioLineResponse] = Field(default_factory=list)
    created_at: datetime
    created_by: Optional[UUID]

    model_config = ConfigDict(from_attributes=True)


class PaginatedBudgetScenarios(PaginatedResponse):
    """Reponse paginée de scenarios."""
    items: List[BudgetScenarioResponse]


# ============================================================================
# VARIANCE & ANALYSIS SCHEMAS
# ============================================================================

class BudgetVariance(BaseModel):
    """Ecart budgetaire."""
    category_id: Optional[UUID] = None
    category_name: str
    budget_line_id: Optional[UUID] = None
    line_name: Optional[str] = None
    period: str
    line_type: BudgetLineType
    budget_amount: Decimal
    actual_amount: Decimal
    committed_amount: Decimal = Decimal("0")
    available_amount: Decimal
    variance_amount: Decimal
    variance_percent: Decimal
    variance_type: VarianceType
    budget_ytd: Decimal
    actual_ytd: Decimal
    variance_ytd: Decimal
    variance_ytd_percent: Decimal


class BudgetExecutionRate(BaseModel):
    """Taux d'execution du budget."""
    budget_id: UUID
    as_of_period: str
    expense: Dict[str, Any]
    revenue: Dict[str, Any]
    investment: Optional[Dict[str, Any]] = None
    net_result: Dict[str, Any]
    consumption_rate: Decimal
    remaining_budget: Decimal


class BudgetSummary(BaseModel):
    """Resume du budget."""
    id: UUID
    code: str
    name: str
    budget_type: BudgetType
    status: BudgetStatus
    fiscal_year: int
    version_number: int
    total_revenue: Decimal
    total_expense: Decimal
    total_investment: Decimal
    net_result: Decimal
    ytd_actual_expense: Decimal = Decimal("0")
    ytd_actual_revenue: Decimal = Decimal("0")
    consumption_rate: Decimal = Decimal("0")
    alerts_count: int = 0
    lines_count: int = 0
    execution_rate: Optional[BudgetExecutionRate] = None


class BudgetDashboard(BaseModel):
    """Dashboard budgetaire."""
    tenant_id: str
    fiscal_year: int
    as_of_date: date

    # Totaux globaux
    total_budgeted_expense: Decimal
    total_budgeted_revenue: Decimal
    total_actual_expense: Decimal
    total_actual_revenue: Decimal
    total_variance: Decimal
    overall_consumption_rate: Decimal

    # Budgets actifs
    active_budgets_count: int
    budgets_summary: List[BudgetSummary]

    # Alertes
    active_alerts_count: int
    critical_alerts_count: int
    recent_alerts: List[BudgetAlertResponse]

    # Top depassements
    top_overruns: List[BudgetVariance]

    # Top economies
    top_savings: List[BudgetVariance]

    # Tendance
    monthly_trend: List[Dict[str, Any]]


# ============================================================================
# CONSOLIDATION SCHEMAS
# ============================================================================

class BudgetConsolidationCreate(BaseModel):
    """Schema pour creer une consolidation."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    consolidation_type: str = "BY_ENTITY"
    fiscal_year: int
    currency: str = "EUR"
    budget_ids: List[UUID]
    exclude_intercompany: bool = True


class BudgetConsolidationResponse(BaseModel):
    """Schema de reponse pour une consolidation."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    consolidation_type: str
    fiscal_year: int
    currency: str
    budget_ids: List[UUID]
    total_revenue: Decimal
    total_expense: Decimal
    total_investment: Decimal
    net_result: Decimal
    last_consolidated_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TEMPLATE SCHEMAS
# ============================================================================

class BudgetTemplateCreate(BaseModel):
    """Schema pour creer un template."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    budget_type: BudgetType
    period_type: BudgetPeriodType = BudgetPeriodType.ANNUAL
    category_ids: List[UUID] = Field(default_factory=list)
    default_allocation_method: AllocationMethod = AllocationMethod.EQUAL
    default_settings: Optional[Dict[str, Any]] = None
    default_thresholds: Optional[Dict[str, Any]] = None


class BudgetTemplateResponse(BaseModel):
    """Schema de reponse pour un template."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    budget_type: BudgetType
    period_type: BudgetPeriodType
    category_ids: List[UUID]
    default_allocation_method: AllocationMethod
    default_settings: Optional[Dict[str, Any]]
    is_active: bool
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBudgetTemplates(PaginatedResponse):
    """Reponse paginée de templates."""
    items: List[BudgetTemplateResponse]


# ============================================================================
# SEASONAL PROFILE SCHEMAS
# ============================================================================

class SeasonalProfileCreate(BaseModel):
    """Schema pour creer un profil saisonnier."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    monthly_weights: List[Decimal] = Field(..., min_length=12, max_length=12)

    @field_validator('monthly_weights')
    @classmethod
    def validate_weights(cls, v):
        if len(v) != 12:
            raise ValueError('monthly_weights must contain exactly 12 values')
        if any(w < 0 for w in v):
            raise ValueError('All weights must be non-negative')
        return v


class SeasonalProfileResponse(BaseModel):
    """Schema de reponse pour un profil saisonnier."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    monthly_weights: List[Decimal]
    is_active: bool
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedSeasonalProfiles(PaginatedResponse):
    """Reponse paginée de profils saisonniers."""
    items: List[SeasonalProfileResponse]


# ============================================================================
# WORKFLOW SCHEMAS
# ============================================================================

class BudgetSubmit(BaseModel):
    """Schema pour soumettre un budget."""
    comments: Optional[str] = None


class BudgetApprove(BaseModel):
    """Schema pour approuver un budget."""
    comments: Optional[str] = None


class BudgetReject(BaseModel):
    """Schema pour rejeter un budget."""
    reason: str


class BudgetActivate(BaseModel):
    """Schema pour activer un budget."""
    effective_date: Optional[date] = None


class RevisionApprove(BaseModel):
    """Schema pour approuver une revision."""
    comments: Optional[str] = None


class RevisionReject(BaseModel):
    """Schema pour rejeter une revision."""
    reason: str


# ============================================================================
# IMPORT/EXPORT SCHEMAS
# ============================================================================

class BudgetImportData(BaseModel):
    """Donnees d'import de budget."""
    category_code: str
    annual_amount: Decimal
    monthly_amounts: Optional[Dict[int, Decimal]] = None
    notes: Optional[str] = None


class BudgetImportRequest(BaseModel):
    """Requete d'import de budget."""
    budget_id: Optional[UUID] = None  # Si null, creer un nouveau budget
    budget_code: Optional[str] = None
    budget_name: Optional[str] = None
    fiscal_year: Optional[int] = None
    lines: List[BudgetImportData]
    overwrite: bool = False


class BudgetImportResult(BaseModel):
    """Resultat d'import."""
    success: bool
    budget_id: Optional[UUID] = None
    lines_imported: int = 0
    lines_updated: int = 0
    lines_skipped: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class BudgetExportRequest(BaseModel):
    """Requete d'export de budget."""
    budget_id: UUID
    format: str = "excel"  # excel, csv, pdf
    include_actuals: bool = True
    include_variances: bool = True
    group_by: Optional[str] = None  # category, period, cost_center


class BudgetExportResult(BaseModel):
    """Resultat d'export."""
    file_url: str
    file_name: str
    file_size: int
    expires_at: datetime


# ============================================================================
# ACCOUNTING INTEGRATION SCHEMAS
# ============================================================================

class AccountingActualsImport(BaseModel):
    """Import des realises depuis la comptabilite."""
    budget_id: UUID
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    account_codes: Optional[List[str]] = None
    cost_center_ids: Optional[List[UUID]] = None


class AccountingActualsResult(BaseModel):
    """Resultat d'import des realises."""
    success: bool
    period: str
    records_imported: int
    total_amount: Decimal
    by_category: Dict[str, Decimal]
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# CONTROL CHECK SCHEMAS
# ============================================================================

class BudgetControlCheck(BaseModel):
    """Verification de controle budgetaire."""
    budget_id: UUID
    budget_line_id: Optional[UUID] = None
    amount: Decimal
    description: Optional[str] = None
    cost_center_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class BudgetControlResult(BaseModel):
    """Resultat de controle budgetaire."""
    allowed: bool
    control_mode: ControlMode
    budget_amount: Decimal
    consumed_amount: Decimal
    requested_amount: Decimal
    available_amount: Decimal
    consumption_after: Decimal
    consumption_percent: Decimal
    threshold_exceeded: Optional[str] = None  # warning, critical, exceeded
    message: str
    requires_override: bool = False
