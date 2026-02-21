"""
AZALS MODULE - CURRENCY: Schemas Pydantic
=========================================

Schemas de validation pour la gestion multi-devises.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# ENUMERATIONS
# ============================================================================

class RateSource(str, Enum):
    """Sources des taux de change."""
    ECB = "ecb"
    FOREX = "forex"
    OPENEXCHANGE = "openexchange"
    FIXER = "fixer"
    CURRENCYLAYER = "currencylayer"
    XE = "xe"
    MANUAL = "manual"


class RateType(str, Enum):
    """Types de taux de change."""
    SPOT = "spot"
    AVERAGE = "average"
    CLOSING = "closing"
    OPENING = "opening"
    HIGH = "high"
    LOW = "low"
    CUSTOM = "custom"


class ConversionMethod(str, Enum):
    """Methodes de conversion."""
    DIRECT = "direct"
    TRIANGULATION = "triangulation"
    CROSS_RATE = "cross_rate"
    AVERAGE = "average"


class GainLossType(str, Enum):
    """Types de gains/pertes de change."""
    REALIZED = "realized"
    UNREALIZED = "unrealized"


class CurrencyStatus(str, Enum):
    """Statut d'une devise."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class RevaluationStatus(str, Enum):
    """Statut d'une reevaluation."""
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


# ============================================================================
# CURRENCY SCHEMAS
# ============================================================================

class CurrencyBase(BaseModel):
    """Base pour les devises."""
    code: str = Field(..., min_length=3, max_length=3, description="Code ISO 4217")
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=10)
    decimals: int = Field(default=2, ge=0, le=8)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()


class CurrencyCreate(CurrencyBase):
    """Creation d'une devise."""
    numeric_code: Optional[str] = Field(None, max_length=3)
    name_en: Optional[str] = Field(None, max_length=100)
    symbol_native: Optional[str] = Field(None, max_length=10)
    rounding: Optional[Decimal] = Field(default=Decimal("0.01"), ge=0)
    format_pattern: Optional[str] = Field(None, max_length=50)
    decimal_separator: str = Field(default=",", max_length=1)
    thousands_separator: str = Field(default=" ", max_length=1)
    symbol_position: str = Field(default="after", pattern="^(before|after)$")
    country_codes: List[str] = Field(default_factory=list)
    is_major: bool = False
    is_crypto: bool = False
    is_enabled: bool = True
    exchange_gain_account: Optional[str] = Field(None, max_length=20)
    exchange_loss_account: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class CurrencyUpdate(BaseModel):
    """Mise a jour d'une devise."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    decimals: Optional[int] = Field(None, ge=0, le=8)
    format_pattern: Optional[str] = None
    decimal_separator: Optional[str] = None
    thousands_separator: Optional[str] = None
    symbol_position: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    is_reporting: Optional[bool] = None
    exchange_gain_account: Optional[str] = None
    exchange_loss_account: Optional[str] = None
    status: Optional[CurrencyStatus] = None
    notes: Optional[str] = None


class CurrencyResponse(CurrencyBase):
    """Reponse devise."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    numeric_code: Optional[str] = None
    name_en: Optional[str] = None
    symbol_native: Optional[str] = None
    rounding: Optional[Decimal] = None
    format_pattern: Optional[str] = None
    decimal_separator: str = ","
    thousands_separator: str = " "
    symbol_position: str = "after"
    country_codes: List[str] = Field(default_factory=list)
    is_major: bool = False
    is_crypto: bool = False
    is_enabled: bool = True
    is_default: bool = False
    is_reporting: bool = False
    is_functional: bool = False
    status: CurrencyStatus = CurrencyStatus.ACTIVE
    exchange_gain_account: Optional[str] = None
    exchange_loss_account: Optional[str] = None
    notes: Optional[str] = None
    version: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None


class CurrencyListItem(BaseModel):
    """Item liste devises."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    symbol: str
    decimals: int
    is_enabled: bool
    is_default: bool
    is_reporting: bool
    is_major: bool
    status: CurrencyStatus


class CurrencyList(BaseModel):
    """Liste de devises."""
    items: List[CurrencyListItem]
    total: int


# ============================================================================
# EXCHANGE RATE SCHEMAS
# ============================================================================

class ExchangeRateBase(BaseModel):
    """Base pour les taux de change."""
    base_currency_code: str = Field(..., min_length=3, max_length=3)
    quote_currency_code: str = Field(..., min_length=3, max_length=3)
    rate: Decimal = Field(..., gt=0, decimal_places=12)
    rate_date: date

    @field_validator('base_currency_code', 'quote_currency_code')
    @classmethod
    def uppercase_codes(cls, v: str) -> str:
        return v.upper().strip()


class ExchangeRateCreate(ExchangeRateBase):
    """Creation d'un taux de change."""
    inverse_rate: Optional[Decimal] = Field(None, gt=0)
    bid_rate: Optional[Decimal] = Field(None, gt=0)
    ask_rate: Optional[Decimal] = Field(None, gt=0)
    rate_type: RateType = RateType.SPOT
    source: RateSource = RateSource.MANUAL
    source_reference: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    is_official: bool = False


class ExchangeRateUpdate(BaseModel):
    """Mise a jour d'un taux de change."""
    rate: Optional[Decimal] = Field(None, gt=0)
    bid_rate: Optional[Decimal] = Field(None, gt=0)
    ask_rate: Optional[Decimal] = Field(None, gt=0)
    rate_type: Optional[RateType] = None
    source: Optional[RateSource] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    is_locked: Optional[bool] = None


class ExchangeRateResponse(ExchangeRateBase):
    """Reponse taux de change."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    base_currency_id: UUID
    quote_currency_id: UUID
    inverse_rate: Optional[Decimal] = None
    bid_rate: Optional[Decimal] = None
    ask_rate: Optional[Decimal] = None
    spread: Optional[Decimal] = None
    rate_type: RateType
    source: RateSource
    source_reference: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    fetched_at: Optional[datetime] = None
    is_manual: bool = False
    is_official: bool = False
    is_interpolated: bool = False
    is_locked: bool = False
    version: int = 1
    created_at: datetime


class ExchangeRateListItem(BaseModel):
    """Item liste taux."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    base_currency_code: str
    quote_currency_code: str
    rate: Decimal
    rate_date: date
    rate_type: RateType
    source: RateSource
    is_manual: bool


class ExchangeRateList(BaseModel):
    """Liste de taux."""
    items: List[ExchangeRateListItem]
    total: int
    page: int
    page_size: int
    pages: int


class RateHistoryItem(BaseModel):
    """Item historique des taux."""
    rate_date: date
    rate: Decimal
    rate_type: RateType
    source: RateSource
    variation_percent: Optional[Decimal] = None


class RateHistoryResponse(BaseModel):
    """Historique des taux."""
    base_currency: str
    quote_currency: str
    start_date: date
    end_date: date
    history: List[RateHistoryItem]
    average_rate: Optional[Decimal] = None
    min_rate: Optional[Decimal] = None
    max_rate: Optional[Decimal] = None
    volatility: Optional[Decimal] = None


# ============================================================================
# CONVERSION SCHEMAS
# ============================================================================

class ConversionRequest(BaseModel):
    """Demande de conversion."""
    amount: Decimal = Field(..., description="Montant a convertir")
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    rate_date: Optional[date] = None
    rate_type: RateType = RateType.SPOT

    @field_validator('from_currency', 'to_currency')
    @classmethod
    def uppercase_codes(cls, v: str) -> str:
        return v.upper().strip()


class ConversionResult(BaseModel):
    """Resultat de conversion."""
    original_amount: Decimal
    original_currency: str
    converted_amount: Decimal
    target_currency: str
    exchange_rate: Decimal
    inverse_rate: Decimal
    rate_date: date
    rate_source: RateSource
    rate_type: RateType
    conversion_method: ConversionMethod
    pivot_currency: Optional[str] = None
    intermediate_rates: Optional[List[Dict[str, Any]]] = None
    rounding_difference: Decimal = Decimal("0")


class MultiConversionRequest(BaseModel):
    """Demande de conversion multiple."""
    amounts: List[Dict[str, Any]] = Field(..., min_length=1)
    target_currency: str = Field(..., min_length=3, max_length=3)
    rate_date: Optional[date] = None


class MultiConversionResult(BaseModel):
    """Resultat de conversion multiple."""
    conversions: List[ConversionResult]
    total_in_target: Decimal
    target_currency: str


# ============================================================================
# CONFIG SCHEMAS
# ============================================================================

class CurrencyConfigCreate(BaseModel):
    """Creation config devises."""
    default_currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    reporting_currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    primary_rate_source: RateSource = RateSource.ECB
    fallback_rate_source: Optional[RateSource] = RateSource.OPENEXCHANGE
    auto_update_rates: bool = True
    update_frequency_hours: int = Field(default=24, ge=1, le=168)
    conversion_method: ConversionMethod = ConversionMethod.DIRECT
    pivot_currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    track_exchange_gains: bool = True
    exchange_gain_account: Optional[str] = None
    exchange_loss_account: Optional[str] = None


class CurrencyConfigUpdate(BaseModel):
    """Mise a jour config devises."""
    default_currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    reporting_currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    primary_rate_source: Optional[RateSource] = None
    fallback_rate_source: Optional[RateSource] = None
    auto_update_rates: Optional[bool] = None
    update_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    update_time: Optional[str] = Field(None, pattern="^[0-2][0-9]:[0-5][0-9]$")
    conversion_method: Optional[ConversionMethod] = None
    pivot_currency_code: Optional[str] = None
    allow_triangulation: Optional[bool] = None
    rounding_method: Optional[str] = None
    rounding_precision: Optional[int] = Field(None, ge=0, le=8)
    track_exchange_gains: Optional[bool] = None
    exchange_gain_account: Optional[str] = None
    exchange_loss_account: Optional[str] = None
    allow_manual_rates: Optional[bool] = None
    require_rate_approval: Optional[bool] = None
    rate_tolerance_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    notify_rate_changes: Optional[bool] = None
    notification_threshold_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    notification_emails: Optional[List[str]] = None


class CurrencyConfigResponse(BaseModel):
    """Reponse config devises."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    default_currency_code: str
    reporting_currency_code: str
    functional_currency_code: Optional[str] = None
    primary_rate_source: RateSource
    fallback_rate_source: Optional[RateSource] = None
    auto_update_rates: bool
    update_frequency_hours: int
    update_time: Optional[str] = None
    last_rate_update: Optional[datetime] = None
    next_rate_update: Optional[datetime] = None
    conversion_method: ConversionMethod
    pivot_currency_code: str
    allow_triangulation: bool
    rounding_method: str
    rounding_precision: int
    track_exchange_gains: bool
    exchange_gain_account: Optional[str] = None
    exchange_loss_account: Optional[str] = None
    unrealized_gain_account: Optional[str] = None
    unrealized_loss_account: Optional[str] = None
    allow_manual_rates: bool
    require_rate_approval: bool
    rate_tolerance_percent: Decimal
    notify_rate_changes: bool
    notification_threshold_percent: Decimal
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================================
# GAIN/LOSS SCHEMAS
# ============================================================================

class ExchangeGainLossCreate(BaseModel):
    """Creation gain/perte de change."""
    document_type: str = Field(..., min_length=1, max_length=50)
    document_id: UUID
    document_reference: Optional[str] = None
    gain_loss_type: GainLossType
    original_amount: Decimal
    original_currency_code: str = Field(..., min_length=3, max_length=3)
    booking_rate: Decimal = Field(..., gt=0)
    settlement_rate: Optional[Decimal] = Field(None, gt=0)
    booking_date: date
    settlement_date: Optional[date] = None
    notes: Optional[str] = None


class ExchangeGainLossResponse(BaseModel):
    """Reponse gain/perte de change."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    document_type: str
    document_id: UUID
    document_reference: Optional[str] = None
    gain_loss_type: GainLossType
    original_amount: Decimal
    original_currency_code: str
    booking_rate: Decimal
    settlement_rate: Optional[Decimal] = None
    revaluation_rate: Optional[Decimal] = None
    booking_amount: Decimal
    settlement_amount: Optional[Decimal] = None
    reporting_currency_code: str
    gain_loss_amount: Decimal
    is_gain: bool
    booking_date: date
    settlement_date: Optional[date] = None
    revaluation_date: Optional[date] = None
    is_posted: bool
    journal_entry_id: Optional[UUID] = None
    posting_date: Optional[date] = None
    notes: Optional[str] = None
    version: int
    created_at: datetime


class ExchangeGainLossList(BaseModel):
    """Liste gains/pertes."""
    items: List[ExchangeGainLossResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ExchangeGainLossSummary(BaseModel):
    """Resume gains/pertes."""
    period_start: date
    period_end: date
    currency: str
    realized_gains: Decimal = Decimal("0")
    realized_losses: Decimal = Decimal("0")
    realized_net: Decimal = Decimal("0")
    unrealized_gains: Decimal = Decimal("0")
    unrealized_losses: Decimal = Decimal("0")
    unrealized_net: Decimal = Decimal("0")
    total_net: Decimal = Decimal("0")
    entry_count: int = 0


# ============================================================================
# REVALUATION SCHEMAS
# ============================================================================

class RevaluationCreate(BaseModel):
    """Creation reevaluation."""
    name: str = Field(..., min_length=1, max_length=255)
    revaluation_date: date
    period: str = Field(..., pattern="^[0-9]{4}-[0-9]{2}$")  # YYYY-MM
    currencies_to_revalue: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RevaluationResponse(BaseModel):
    """Reponse reevaluation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    code: str
    name: str
    fiscal_year_id: Optional[UUID] = None
    period: str
    revaluation_date: date
    currencies_revalued: List[str]
    base_currency_code: str
    status: RevaluationStatus
    total_gain: Decimal
    total_loss: Decimal
    net_amount: Decimal
    document_count: int
    journal_entry_id: Optional[UUID] = None
    posted_at: Optional[datetime] = None
    notes: Optional[str] = None
    version: int
    created_at: datetime


class RevaluationPreview(BaseModel):
    """Apercu reevaluation."""
    revaluation_date: date
    currencies: List[str]
    documents: List[Dict[str, Any]]
    total_gain: Decimal
    total_loss: Decimal
    net_amount: Decimal
    document_count: int


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class RateAlertResponse(BaseModel):
    """Reponse alerte taux."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    base_currency_code: str
    quote_currency_code: str
    alert_type: str
    severity: str
    old_rate: Optional[Decimal] = None
    new_rate: Optional[Decimal] = None
    variation_percent: Optional[Decimal] = None
    title: str
    message: str
    is_read: bool
    is_acknowledged: bool
    acknowledged_by: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# FILTER SCHEMAS
# ============================================================================

class CurrencyFilters(BaseModel):
    """Filtres devises."""
    search: Optional[str] = Field(None, min_length=1)
    is_enabled: Optional[bool] = None
    is_major: Optional[bool] = None
    status: Optional[CurrencyStatus] = None


class ExchangeRateFilters(BaseModel):
    """Filtres taux de change."""
    base_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    quote_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    rate_type: Optional[RateType] = None
    source: Optional[RateSource] = None
    is_manual: Optional[bool] = None


class GainLossFilters(BaseModel):
    """Filtres gains/pertes."""
    gain_loss_type: Optional[GainLossType] = None
    document_type: Optional[str] = None
    currency: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_posted: Optional[bool] = None


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class CurrencyExposureReport(BaseModel):
    """Rapport exposition devises."""
    as_of_date: date
    reporting_currency: str
    exposures: List[Dict[str, Any]]
    total_assets: Dict[str, Decimal]
    total_liabilities: Dict[str, Decimal]
    net_exposure: Dict[str, Decimal]


class RateVariationReport(BaseModel):
    """Rapport variation taux."""
    currency_pair: str
    period_start: date
    period_end: date
    start_rate: Decimal
    end_rate: Decimal
    variation_percent: Decimal
    average_rate: Decimal
    min_rate: Decimal
    max_rate: Decimal
    volatility: Decimal


class ExchangeGainLossReport(BaseModel):
    """Rapport gains/pertes de change."""
    period_start: date
    period_end: date
    reporting_currency: str
    by_currency: Dict[str, ExchangeGainLossSummary]
    by_document_type: Dict[str, ExchangeGainLossSummary]
    totals: ExchangeGainLossSummary


# ============================================================================
# COMMON SCHEMAS
# ============================================================================

class AutocompleteItem(BaseModel):
    """Item autocomplete."""
    id: str
    code: str
    name: str
    label: str
    symbol: Optional[str] = None


class AutocompleteResponse(BaseModel):
    """Reponse autocomplete."""
    items: List[AutocompleteItem]


class BulkRateUpdateRequest(BaseModel):
    """Mise a jour en masse des taux."""
    rates: List[ExchangeRateCreate]
    source: RateSource = RateSource.MANUAL
    overwrite_existing: bool = True


class BulkRateUpdateResponse(BaseModel):
    """Resultat MAJ en masse."""
    created: int
    updated: int
    errors: List[Dict[str, Any]]


class RateFetchRequest(BaseModel):
    """Demande recuperation taux."""
    currencies: List[str] = Field(default_factory=list)
    base_currency: str = Field(default="EUR", min_length=3, max_length=3)
    source: RateSource = RateSource.ECB
    rate_date: Optional[date] = None


class RateFetchResult(BaseModel):
    """Resultat recuperation taux."""
    source: RateSource
    fetch_date: datetime
    rate_date: date
    rates_fetched: int
    rates_saved: int
    errors: List[str]
