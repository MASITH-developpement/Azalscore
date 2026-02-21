"""
AZALS MODULE - CONSOLIDATION: Schemas Pydantic
================================================

Schemas de validation et serialisation pour le module
de consolidation comptable multi-entites.

Auteur: AZALSCORE Team
Version: 1.0.0
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


from .models import (
    AccountingStandard,
    ConsolidationMethod,
    ConsolidationStatus,
    ControlType,
    CurrencyConversionMethod,
    EliminationType,
    PackageStatus,
    ReportType,
    RestatementType,
)


# ============================================================================
# SCHEMAS DE BASE
# ============================================================================

class BaseSchema(BaseModel):
    """Schema de base avec configuration commune."""

    class Config:
        from_attributes = True
        populate_by_name = True


class PaginatedResponse(BaseModel):
    """Response paginee generique."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# PERIMETRE DE CONSOLIDATION
# ============================================================================

class ConsolidationPerimeterBase(BaseSchema):
    """Schema de base pour le perimetre de consolidation."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    fiscal_year: int = Field(..., ge=2000, le=2100)
    start_date: date
    end_date: date
    consolidation_currency: str = Field(default="EUR", min_length=3, max_length=3)
    accounting_standard: AccountingStandard = AccountingStandard.FRENCH_GAAP

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class ConsolidationPerimeterCreate(ConsolidationPerimeterBase):
    """Schema pour la creation d'un perimetre."""
    pass


class ConsolidationPerimeterUpdate(BaseSchema):
    """Schema pour la mise a jour d'un perimetre."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    consolidation_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    accounting_standard: Optional[AccountingStandard] = None
    status: Optional[ConsolidationStatus] = None
    is_active: Optional[bool] = None


class ConsolidationPerimeterResponse(ConsolidationPerimeterBase):
    """Schema de reponse pour un perimetre."""
    id: UUID
    tenant_id: str
    status: ConsolidationStatus
    is_active: bool
    version: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    # Statistiques
    entity_count: Optional[int] = 0
    consolidation_count: Optional[int] = 0


class PaginatedPerimeters(PaginatedResponse):
    """Response paginee des perimetres."""
    items: List[ConsolidationPerimeterResponse]


# ============================================================================
# ENTITES DU GROUPE
# ============================================================================

class ConsolidationEntityBase(BaseSchema):
    """Schema de base pour une entite du groupe."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    registration_number: Optional[str] = Field(None, max_length=50)
    country: str = Field(..., min_length=2, max_length=3)
    currency: str = Field(..., min_length=3, max_length=3)

    is_parent: bool = False
    consolidation_method: ConsolidationMethod = ConsolidationMethod.NOT_CONSOLIDATED
    control_type: ControlType = ControlType.NONE

    direct_ownership_pct: Decimal = Field(default=Decimal("0.000"), ge=0, le=100)
    indirect_ownership_pct: Decimal = Field(default=Decimal("0.000"), ge=0, le=100)
    voting_rights_pct: Decimal = Field(default=Decimal("0.000"), ge=0, le=100)
    integration_pct: Decimal = Field(default=Decimal("100.000"), ge=0, le=100)

    acquisition_date: Optional[date] = None
    disposal_date: Optional[date] = None
    fiscal_year_end_month: int = Field(default=12, ge=1, le=12)

    sector: Optional[str] = Field(None, max_length=100)
    segment: Optional[str] = Field(None, max_length=100)


class ConsolidationEntityCreate(ConsolidationEntityBase):
    """Schema pour la creation d'une entite."""
    perimeter_id: UUID
    parent_entity_id: Optional[UUID] = None


class ConsolidationEntityUpdate(BaseSchema):
    """Schema pour la mise a jour d'une entite."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    country: Optional[str] = Field(None, min_length=2, max_length=3)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

    parent_entity_id: Optional[UUID] = None
    consolidation_method: Optional[ConsolidationMethod] = None
    control_type: Optional[ControlType] = None

    direct_ownership_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    indirect_ownership_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    voting_rights_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    integration_pct: Optional[Decimal] = Field(None, ge=0, le=100)

    acquisition_date: Optional[date] = None
    disposal_date: Optional[date] = None
    sector: Optional[str] = None
    segment: Optional[str] = None
    is_active: Optional[bool] = None


class ConsolidationEntityResponse(ConsolidationEntityBase):
    """Schema de reponse pour une entite."""
    id: UUID
    tenant_id: str
    perimeter_id: UUID
    parent_entity_id: Optional[UUID] = None
    total_ownership_pct: Decimal
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    # Relations
    parent_name: Optional[str] = None
    subsidiaries_count: Optional[int] = 0


class PaginatedEntities(PaginatedResponse):
    """Response paginee des entites."""
    items: List[ConsolidationEntityResponse]


# ============================================================================
# PARTICIPATIONS
# ============================================================================

class ParticipationBase(BaseSchema):
    """Schema de base pour une participation."""
    parent_id: UUID
    subsidiary_id: UUID
    direct_ownership: Decimal = Field(..., ge=0, le=100)
    indirect_ownership: Decimal = Field(default=Decimal("0.000"), ge=0, le=100)
    voting_rights: Decimal = Field(default=Decimal("0.000"), ge=0, le=100)
    acquisition_date: date
    acquisition_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    fair_value_at_acquisition: Decimal = Field(default=Decimal("0.00"), ge=0)
    goodwill_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    goodwill_currency: str = Field(default="EUR", min_length=3, max_length=3)
    notes: Optional[str] = None


class ParticipationCreate(ParticipationBase):
    """Schema pour la creation d'une participation."""
    pass


class ParticipationUpdate(BaseSchema):
    """Schema pour la mise a jour d'une participation."""
    direct_ownership: Optional[Decimal] = Field(None, ge=0, le=100)
    indirect_ownership: Optional[Decimal] = Field(None, ge=0, le=100)
    voting_rights: Optional[Decimal] = Field(None, ge=0, le=100)
    acquisition_cost: Optional[Decimal] = Field(None, ge=0)
    fair_value_at_acquisition: Optional[Decimal] = Field(None, ge=0)
    goodwill_amount: Optional[Decimal] = Field(None, ge=0)
    goodwill_impairment: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class ParticipationResponse(ParticipationBase):
    """Schema de reponse pour une participation."""
    id: UUID
    tenant_id: str
    total_ownership: Decimal
    goodwill_impairment: Decimal
    version: int
    created_at: datetime
    updated_at: datetime

    # Relations
    parent_name: Optional[str] = None
    subsidiary_name: Optional[str] = None


# ============================================================================
# COURS DE CHANGE
# ============================================================================

class ExchangeRateBase(BaseSchema):
    """Schema de base pour un cours de change."""
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    rate_date: date
    closing_rate: Decimal = Field(..., gt=0)
    average_rate: Decimal = Field(..., gt=0)
    historical_rate: Optional[Decimal] = Field(None, gt=0)
    source: Optional[str] = Field(None, max_length=100)


class ExchangeRateCreate(ExchangeRateBase):
    """Schema pour la creation d'un cours de change."""
    pass


class ExchangeRateBulkCreate(BaseSchema):
    """Schema pour la creation en masse de cours de change."""
    rates: List[ExchangeRateCreate]


class ExchangeRateResponse(ExchangeRateBase):
    """Schema de reponse pour un cours de change."""
    id: UUID
    tenant_id: str
    created_at: datetime


class PaginatedExchangeRates(PaginatedResponse):
    """Response paginee des cours de change."""
    items: List[ExchangeRateResponse]


# ============================================================================
# CONSOLIDATION
# ============================================================================

class ConsolidationBase(BaseSchema):
    """Schema de base pour une consolidation."""
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    period_start: date
    period_end: date
    fiscal_year: int = Field(..., ge=2000, le=2100)
    period_type: str = Field(default="annual", pattern="^(annual|quarterly|monthly)$")
    consolidation_currency: str = Field(default="EUR", min_length=3, max_length=3)
    accounting_standard: AccountingStandard = AccountingStandard.FRENCH_GAAP

    @model_validator(mode='after')
    def validate_dates(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be >= period_start")
        return self


class ConsolidationCreate(ConsolidationBase):
    """Schema pour la creation d'une consolidation."""
    perimeter_id: UUID


class ConsolidationUpdate(BaseSchema):
    """Schema pour la mise a jour d'une consolidation."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ConsolidationStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class ConsolidationResponse(ConsolidationBase):
    """Schema de reponse pour une consolidation."""
    id: UUID
    tenant_id: str
    perimeter_id: UUID
    status: ConsolidationStatus

    # Resultats
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    group_equity: Decimal
    minority_interests: Decimal
    consolidated_revenue: Decimal
    consolidated_net_income: Decimal
    group_net_income: Decimal
    minority_net_income: Decimal
    translation_difference: Decimal
    total_goodwill: Decimal

    # Workflow
    submitted_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    # Audit
    version: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    # Statistiques
    packages_count: Optional[int] = 0
    packages_validated: Optional[int] = 0
    eliminations_count: Optional[int] = 0


class PaginatedConsolidations(PaginatedResponse):
    """Response paginee des consolidations."""
    items: List[ConsolidationResponse]


# ============================================================================
# PAQUET DE CONSOLIDATION
# ============================================================================

class TrialBalanceEntry(BaseSchema):
    """Ligne de balance pour le paquet."""
    account_code: str
    account_name: str
    debit: Decimal = Field(default=Decimal("0.00"))
    credit: Decimal = Field(default=Decimal("0.00"))
    balance: Decimal = Field(default=Decimal("0.00"))
    currency: str = Field(default="EUR")


class IntercompanyDetail(BaseSchema):
    """Detail d'une operation intercompany."""
    counterparty_entity_id: UUID
    counterparty_code: str
    transaction_type: str  # receivable, payable, sale, purchase
    account_code: str
    amount: Decimal
    currency: str = Field(default="EUR")
    description: Optional[str] = None


class ConsolidationPackageBase(BaseSchema):
    """Schema de base pour un paquet de consolidation."""
    period_start: date
    period_end: date
    local_currency: str = Field(..., min_length=3, max_length=3)

    # Totaux en devise locale
    total_assets_local: Decimal = Field(default=Decimal("0.00"))
    total_liabilities_local: Decimal = Field(default=Decimal("0.00"))
    total_equity_local: Decimal = Field(default=Decimal("0.00"))
    net_income_local: Decimal = Field(default=Decimal("0.00"))

    # Intercompany
    intercompany_receivables: Decimal = Field(default=Decimal("0.00"))
    intercompany_payables: Decimal = Field(default=Decimal("0.00"))
    intercompany_sales: Decimal = Field(default=Decimal("0.00"))
    intercompany_purchases: Decimal = Field(default=Decimal("0.00"))
    dividends_to_parent: Decimal = Field(default=Decimal("0.00"))

    # Balance detaillee
    trial_balance: List[TrialBalanceEntry] = Field(default_factory=list)
    intercompany_details: List[IntercompanyDetail] = Field(default_factory=list)

    is_audited: bool = False
    auditor_notes: Optional[str] = None


class ConsolidationPackageCreate(ConsolidationPackageBase):
    """Schema pour la creation d'un paquet."""
    consolidation_id: UUID
    entity_id: UUID


class ConsolidationPackageUpdate(BaseSchema):
    """Schema pour la mise a jour d'un paquet."""
    total_assets_local: Optional[Decimal] = None
    total_liabilities_local: Optional[Decimal] = None
    total_equity_local: Optional[Decimal] = None
    net_income_local: Optional[Decimal] = None

    intercompany_receivables: Optional[Decimal] = None
    intercompany_payables: Optional[Decimal] = None
    intercompany_sales: Optional[Decimal] = None
    intercompany_purchases: Optional[Decimal] = None
    dividends_to_parent: Optional[Decimal] = None

    trial_balance: Optional[List[TrialBalanceEntry]] = None
    intercompany_details: Optional[List[IntercompanyDetail]] = None

    is_audited: Optional[bool] = None
    auditor_notes: Optional[str] = None


class ConsolidationPackageSubmit(BaseSchema):
    """Schema pour la soumission d'un paquet."""
    comments: Optional[str] = None


class ConsolidationPackageValidate(BaseSchema):
    """Schema pour la validation d'un paquet."""
    comments: Optional[str] = None


class ConsolidationPackageReject(BaseSchema):
    """Schema pour le rejet d'un paquet."""
    reason: str = Field(..., min_length=1)


class ConsolidationPackageResponse(ConsolidationPackageBase):
    """Schema de reponse pour un paquet."""
    id: UUID
    tenant_id: str
    consolidation_id: UUID
    entity_id: UUID
    reporting_currency: str
    status: PackageStatus

    # Cours utilises
    closing_rate: Optional[Decimal] = None
    average_rate: Optional[Decimal] = None

    # Totaux convertis
    total_assets_converted: Decimal
    total_liabilities_converted: Decimal
    total_equity_converted: Decimal
    net_income_converted: Decimal
    translation_difference: Decimal

    # Workflow
    submitted_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Audit
    version: int
    created_at: datetime
    updated_at: datetime

    # Relations
    entity_name: Optional[str] = None
    entity_code: Optional[str] = None


class PaginatedPackages(PaginatedResponse):
    """Response paginee des paquets."""
    items: List[ConsolidationPackageResponse]


# ============================================================================
# ELIMINATIONS
# ============================================================================

class JournalEntryLine(BaseSchema):
    """Ligne d'ecriture comptable."""
    account: str
    debit: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0)
    label: str
    entity_id: Optional[str] = None


class EliminationEntryBase(BaseSchema):
    """Schema de base pour une elimination."""
    elimination_type: EliminationType
    description: str = Field(..., min_length=1)
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    journal_entries: List[JournalEntryLine] = Field(default_factory=list)
    is_automatic: bool = True


class EliminationEntryCreate(EliminationEntryBase):
    """Schema pour la creation d'une elimination."""
    consolidation_id: UUID
    entity1_id: Optional[UUID] = None
    entity2_id: Optional[UUID] = None
    source_document_type: Optional[str] = None
    source_document_id: Optional[UUID] = None


class EliminationEntryUpdate(BaseSchema):
    """Schema pour la mise a jour d'une elimination."""
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    journal_entries: Optional[List[JournalEntryLine]] = None
    is_validated: Optional[bool] = None


class EliminationEntryResponse(EliminationEntryBase):
    """Schema de reponse pour une elimination."""
    id: UUID
    tenant_id: str
    consolidation_id: UUID
    code: Optional[str] = None
    entity1_id: Optional[UUID] = None
    entity2_id: Optional[UUID] = None
    source_document_type: Optional[str] = None
    source_document_id: Optional[UUID] = None
    is_validated: bool
    validated_at: Optional[datetime] = None
    version: int
    created_at: datetime
    updated_at: datetime

    # Relations
    entity1_name: Optional[str] = None
    entity2_name: Optional[str] = None


class PaginatedEliminations(PaginatedResponse):
    """Response paginee des eliminations."""
    items: List[EliminationEntryResponse]


class GenerateEliminationsRequest(BaseSchema):
    """Request pour generer les eliminations automatiques."""
    consolidation_id: UUID
    elimination_types: Optional[List[EliminationType]] = None  # Si None, tous les types


class GenerateEliminationsResponse(BaseSchema):
    """Response de la generation d'eliminations."""
    generated_count: int
    eliminations: List[EliminationEntryResponse]
    warnings: List[str] = Field(default_factory=list)


# ============================================================================
# RETRAITEMENTS
# ============================================================================

class RestatementBase(BaseSchema):
    """Schema de base pour un retraitement."""
    restatement_type: RestatementType
    description: str = Field(..., min_length=1)
    standard_reference: Optional[str] = Field(None, max_length=50)

    impact_assets: Decimal = Field(default=Decimal("0.00"))
    impact_liabilities: Decimal = Field(default=Decimal("0.00"))
    impact_equity: Decimal = Field(default=Decimal("0.00"))
    impact_income: Decimal = Field(default=Decimal("0.00"))
    impact_expense: Decimal = Field(default=Decimal("0.00"))
    tax_impact: Decimal = Field(default=Decimal("0.00"))

    journal_entries: List[JournalEntryLine] = Field(default_factory=list)
    calculation_details: Dict[str, Any] = Field(default_factory=dict)

    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None


class RestatementCreate(RestatementBase):
    """Schema pour la creation d'un retraitement."""
    consolidation_id: UUID
    entity_id: UUID


class RestatementUpdate(BaseSchema):
    """Schema pour la mise a jour d'un retraitement."""
    description: Optional[str] = None
    impact_assets: Optional[Decimal] = None
    impact_liabilities: Optional[Decimal] = None
    impact_equity: Optional[Decimal] = None
    impact_income: Optional[Decimal] = None
    impact_expense: Optional[Decimal] = None
    tax_impact: Optional[Decimal] = None
    journal_entries: Optional[List[JournalEntryLine]] = None
    calculation_details: Optional[Dict[str, Any]] = None
    is_validated: Optional[bool] = None


class RestatementResponse(RestatementBase):
    """Schema de reponse pour un retraitement."""
    id: UUID
    tenant_id: str
    consolidation_id: UUID
    entity_id: UUID
    code: Optional[str] = None
    is_validated: bool
    validated_at: Optional[datetime] = None
    version: int
    created_at: datetime
    updated_at: datetime

    entity_name: Optional[str] = None


class PaginatedRestatements(PaginatedResponse):
    """Response paginee des retraitements."""
    items: List[RestatementResponse]


# ============================================================================
# RECONCILIATION INTER-SOCIETES
# ============================================================================

class IntercompanyReconciliationBase(BaseSchema):
    """Schema de base pour une reconciliation interco."""
    entity1_id: UUID
    entity2_id: UUID
    transaction_type: str = Field(..., min_length=1, max_length=50)
    amount_entity1: Decimal
    amount_entity2: Decimal
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    difference_reason: Optional[str] = None
    tolerance_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tolerance_pct: Decimal = Field(default=Decimal("0.0000"), ge=0, le=100)


class IntercompanyReconciliationCreate(IntercompanyReconciliationBase):
    """Schema pour la creation d'une reconciliation."""
    consolidation_id: UUID


class IntercompanyReconciliationUpdate(BaseSchema):
    """Schema pour la mise a jour d'une reconciliation."""
    amount_entity1: Optional[Decimal] = None
    amount_entity2: Optional[Decimal] = None
    difference_reason: Optional[str] = None
    action_required: Optional[str] = None
    action_taken: Optional[str] = None
    is_reconciled: Optional[bool] = None


class IntercompanyReconciliationResponse(IntercompanyReconciliationBase):
    """Schema de reponse pour une reconciliation."""
    id: UUID
    tenant_id: str
    consolidation_id: UUID
    difference: Decimal
    difference_pct: Decimal
    is_reconciled: bool
    reconciled_at: Optional[datetime] = None
    is_within_tolerance: bool
    action_required: Optional[str] = None
    action_taken: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

    entity1_name: Optional[str] = None
    entity2_name: Optional[str] = None


class PaginatedReconciliations(PaginatedResponse):
    """Response paginee des reconciliations."""
    items: List[IntercompanyReconciliationResponse]


class ReconciliationSummary(BaseSchema):
    """Resume des reconciliations interco."""
    total_pairs: int
    reconciled_count: int
    unreconciled_count: int
    within_tolerance_count: int
    total_difference: Decimal
    by_type: Dict[str, int]


# ============================================================================
# GOODWILL
# ============================================================================

class GoodwillCalculationBase(BaseSchema):
    """Schema de base pour un calcul de goodwill."""
    calculation_date: date
    acquisition_cost: Decimal = Field(..., ge=0)
    acquisition_currency: str = Field(default="EUR", min_length=3, max_length=3)
    assets_fair_value: Decimal = Field(default=Decimal("0.00"))
    liabilities_fair_value: Decimal = Field(default=Decimal("0.00"))
    ownership_percentage: Decimal = Field(..., ge=0, le=100)
    revaluation_adjustments: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None


class GoodwillCalculationCreate(GoodwillCalculationBase):
    """Schema pour la creation d'un calcul de goodwill."""
    consolidation_id: UUID
    participation_id: UUID


class GoodwillCalculationUpdate(BaseSchema):
    """Schema pour la mise a jour d'un calcul de goodwill."""
    current_period_impairment: Optional[Decimal] = Field(None, ge=0)
    impairment_test_date: Optional[date] = None
    impairment_test_result: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class GoodwillCalculationResponse(GoodwillCalculationBase):
    """Schema de reponse pour un calcul de goodwill."""
    id: UUID
    tenant_id: str
    consolidation_id: UUID
    participation_id: UUID

    net_assets_fair_value: Decimal
    group_share_net_assets: Decimal
    goodwill_amount: Decimal
    badwill_amount: Decimal
    cumulative_impairment: Decimal
    current_period_impairment: Decimal
    carrying_value: Decimal

    impairment_test_date: Optional[date] = None
    impairment_test_result: Optional[Dict[str, Any]] = None

    version: int
    created_at: datetime
    updated_at: datetime

    subsidiary_name: Optional[str] = None


# ============================================================================
# RAPPORTS CONSOLIDES
# ============================================================================

class ConsolidatedReportBase(BaseSchema):
    """Schema de base pour un rapport consolide."""
    report_type: ReportType
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    period_start: date
    period_end: date
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ConsolidatedReportCreate(ConsolidatedReportBase):
    """Schema pour la creation d'un rapport."""
    consolidation_id: UUID


class ConsolidatedReportResponse(ConsolidatedReportBase):
    """Schema de reponse pour un rapport."""
    id: UUID
    tenant_id: str
    consolidation_id: UUID
    report_data: Dict[str, Any]
    comparative_data: Optional[Dict[str, Any]] = None
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None
    generated_at: Optional[datetime] = None
    is_final: bool
    finalized_at: Optional[datetime] = None
    version: int
    created_at: datetime
    updated_at: datetime


class PaginatedReports(PaginatedResponse):
    """Response paginee des rapports."""
    items: List[ConsolidatedReportResponse]


class GenerateReportRequest(BaseSchema):
    """Request pour generer un rapport."""
    consolidation_id: UUID
    report_type: ReportType
    include_comparative: bool = True
    comparative_consolidation_id: Optional[UUID] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MAPPING COMPTES
# ============================================================================

class AccountMappingBase(BaseSchema):
    """Schema de base pour un mapping de compte."""
    local_account_code: str = Field(..., min_length=1, max_length=20)
    local_account_label: Optional[str] = Field(None, max_length=255)
    group_account_code: str = Field(..., min_length=1, max_length=20)
    group_account_label: Optional[str] = Field(None, max_length=255)
    reporting_category: Optional[str] = Field(None, max_length=100)
    reporting_subcategory: Optional[str] = Field(None, max_length=100)
    currency_method: CurrencyConversionMethod = CurrencyConversionMethod.CLOSING_RATE


class AccountMappingCreate(AccountMappingBase):
    """Schema pour la creation d'un mapping."""
    perimeter_id: UUID
    entity_id: Optional[UUID] = None


class AccountMappingBulkCreate(BaseSchema):
    """Schema pour la creation en masse de mappings."""
    perimeter_id: UUID
    entity_id: Optional[UUID] = None
    mappings: List[AccountMappingBase]


class AccountMappingResponse(AccountMappingBase):
    """Schema de reponse pour un mapping."""
    id: UUID
    tenant_id: str
    perimeter_id: UUID
    entity_id: Optional[UUID] = None
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class PaginatedAccountMappings(PaginatedResponse):
    """Response paginee des mappings."""
    items: List[AccountMappingResponse]


# ============================================================================
# DASHBOARD & STATISTIQUES
# ============================================================================

class ConsolidationDashboard(BaseSchema):
    """Dashboard de consolidation."""
    # Perimetres
    active_perimeters: int
    total_entities: int
    entities_by_method: Dict[str, int]

    # Consolidations en cours
    consolidations_in_progress: int
    consolidations_validated: int

    # Packages
    packages_pending: int
    packages_validated: int
    packages_rejected: int

    # Intercompany
    total_intercompany_balance: Decimal
    unreconciled_items: int
    reconciliation_rate: Decimal

    # Eliminations
    total_eliminations: int
    elimination_amount: Decimal

    # Goodwill
    total_goodwill: Decimal
    total_impairment: Decimal


class ConsolidationProgress(BaseSchema):
    """Progression d'une consolidation."""
    consolidation_id: UUID
    total_entities: int
    packages_submitted: int
    packages_validated: int
    packages_rejected: int
    completion_pct: Decimal
    eliminations_generated: bool
    restatements_validated: bool
    reports_generated: List[str]


# ============================================================================
# FILTRES
# ============================================================================

class ConsolidationFilters(BaseSchema):
    """Filtres pour la recherche de consolidations."""
    search: Optional[str] = None
    fiscal_year: Optional[int] = None
    status: Optional[List[ConsolidationStatus]] = None
    perimeter_id: Optional[UUID] = None
    accounting_standard: Optional[AccountingStandard] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class EntityFilters(BaseSchema):
    """Filtres pour la recherche d'entites."""
    search: Optional[str] = None
    perimeter_id: Optional[UUID] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    consolidation_method: Optional[List[ConsolidationMethod]] = None
    is_parent: Optional[bool] = None
    is_active: Optional[bool] = None


class PackageFilters(BaseSchema):
    """Filtres pour la recherche de paquets."""
    consolidation_id: Optional[UUID] = None
    entity_id: Optional[UUID] = None
    status: Optional[List[PackageStatus]] = None
    is_audited: Optional[bool] = None


class ReconciliationFilters(BaseSchema):
    """Filtres pour la recherche de reconciliations."""
    consolidation_id: Optional[UUID] = None
    entity_id: Optional[UUID] = None
    transaction_type: Optional[str] = None
    is_reconciled: Optional[bool] = None
    is_within_tolerance: Optional[bool] = None
