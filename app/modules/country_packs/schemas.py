"""
AZALS MODULE T5 - Schémas Pydantic Packs Pays
==============================================

Schémas de validation pour les API du module Packs Pays.
"""


from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# ENUMS
# ============================================================================

class TaxTypeEnum(str, Enum):
    VAT = "VAT"
    SALES_TAX = "SALES_TAX"
    CORPORATE_TAX = "CORPORATE_TAX"
    PAYROLL_TAX = "PAYROLL_TAX"
    WITHHOLDING = "WITHHOLDING"
    CUSTOMS = "CUSTOMS"
    EXCISE = "EXCISE"
    OTHER = "OTHER"


class DocumentTypeEnum(str, Enum):
    INVOICE = "INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    PAYSLIP = "PAYSLIP"
    TAX_RETURN = "TAX_RETURN"
    BALANCE_SHEET = "BALANCE_SHEET"
    INCOME_STATEMENT = "INCOME_STATEMENT"
    CONTRACT = "CONTRACT"
    OTHER = "OTHER"


class BankFormatEnum(str, Enum):
    SEPA = "SEPA"
    SWIFT = "SWIFT"
    ACH = "ACH"
    BACS = "BACS"
    CMI = "CMI"
    RTGS = "RTGS"
    OTHER = "OTHER"


class DateFormatStyleEnum(str, Enum):
    DMY = "DMY"
    MDY = "MDY"
    YMD = "YMD"
    DDMMYYYY = "DDMMYYYY"
    MMDDYYYY = "MMDDYYYY"
    YYYYMMDD = "YYYYMMDD"


class NumberFormatStyleEnum(str, Enum):
    EU = "EU"
    US = "US"
    CH = "CH"


class PackStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


# ============================================================================
# COUNTRY PACK
# ============================================================================

class CountryPackBase(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    country_name: str = Field(..., min_length=2, max_length=100)
    default_currency: str = Field(..., min_length=3, max_length=3)
    country_name_local: str | None = None
    default_language: str = "fr"
    currency_symbol: str | None = None
    currency_position: str = "after"
    date_format: DateFormatStyleEnum = DateFormatStyleEnum.DMY
    number_format: NumberFormatStyleEnum = NumberFormatStyleEnum.EU
    decimal_separator: str = ","
    thousands_separator: str = " "
    timezone: str = "Europe/Paris"
    week_start: int = Field(1, ge=0, le=6)
    fiscal_year_start_month: int = Field(1, ge=1, le=12)
    fiscal_year_start_day: int = Field(1, ge=1, le=31)
    default_vat_rate: float = 20.0
    has_regional_taxes: bool = False
    company_id_label: str = "SIRET"
    company_id_format: str | None = None
    vat_id_label: str = "TVA"
    vat_id_format: str | None = None
    config: dict[str, Any] | None = None
    is_default: bool = False


class CountryPackCreate(CountryPackBase):
    pass


class CountryPackUpdate(BaseModel):
    country_name: str | None = Field(None, min_length=2, max_length=100)
    country_name_local: str | None = None
    default_language: str | None = None
    currency_symbol: str | None = None
    currency_position: str | None = None
    date_format: DateFormatStyleEnum | None = None
    number_format: NumberFormatStyleEnum | None = None
    timezone: str | None = None
    default_vat_rate: float | None = None
    company_id_label: str | None = None
    vat_id_label: str | None = None
    config: dict[str, Any] | None = None
    is_default: bool | None = None
    status: PackStatusEnum | None = None


class CountryPackResponse(CountryPackBase):
    id: int
    status: PackStatusEnum
    created_at: datetime
    updated_at: datetime | None = None
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TAX RATE
# ============================================================================

class TaxRateBase(BaseModel):
    country_pack_id: int
    tax_type: TaxTypeEnum
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    rate: float = Field(..., ge=0, le=100)
    is_percentage: bool = True
    applies_to: str | None = "both"
    region: str | None = None
    account_collected: str | None = None
    account_deductible: str | None = None
    account_payable: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_default: bool = False


class TaxRateCreate(TaxRateBase):
    pass


class TaxRateUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None
    rate: float | None = Field(None, ge=0, le=100)
    applies_to: str | None = None
    region: str | None = None
    account_collected: str | None = None
    account_deductible: str | None = None
    account_payable: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class TaxRateResponse(TaxRateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DOCUMENT TEMPLATE
# ============================================================================

class DocumentTemplateBase(BaseModel):
    country_pack_id: int
    document_type: DocumentTypeEnum
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    template_format: str = "html"
    template_content: str | None = None
    template_path: str | None = None
    mandatory_fields: list[str] | None = None
    legal_mentions: str | None = None
    numbering_prefix: str | None = None
    numbering_pattern: str | None = None
    numbering_reset: str = "yearly"
    language: str = "fr"
    is_default: bool = False


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    template_content: str | None = None
    template_path: str | None = None
    mandatory_fields: list[str] | None = None
    legal_mentions: str | None = None
    numbering_prefix: str | None = None
    numbering_pattern: str | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# BANK CONFIG
# ============================================================================

class BankConfigBase(BaseModel):
    country_pack_id: int
    bank_format: BankFormatEnum
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    iban_prefix: str | None = None
    iban_length: int | None = None
    bic_required: bool = True
    export_format: str = "xml"
    export_encoding: str = "utf-8"
    export_template: str | None = None
    config: dict[str, Any] | None = None
    is_default: bool = False


class BankConfigCreate(BankConfigBase):
    pass


class BankConfigUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    iban_prefix: str | None = None
    iban_length: int | None = None
    bic_required: bool | None = None
    export_format: str | None = None
    export_template: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class BankConfigResponse(BankConfigBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PUBLIC HOLIDAY
# ============================================================================

class PublicHolidayBase(BaseModel):
    country_pack_id: int
    name: str = Field(..., min_length=2, max_length=200)
    name_local: str | None = None
    holiday_date: date | None = None
    month: int | None = Field(None, ge=1, le=12)
    day: int | None = Field(None, ge=1, le=31)
    is_fixed: bool = True
    calculation_rule: str | None = None
    year: int | None = None
    region: str | None = None
    is_national: bool = True
    is_work_day: bool = False
    affects_banks: bool = True
    affects_business: bool = True


class PublicHolidayCreate(PublicHolidayBase):
    pass


class PublicHolidayUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    name_local: str | None = None
    holiday_date: date | None = None
    month: int | None = Field(None, ge=1, le=12)
    day: int | None = Field(None, ge=1, le=31)
    is_work_day: bool | None = None
    is_active: bool | None = None


class PublicHolidayResponse(PublicHolidayBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class HolidayWithDate(BaseModel):
    id: int
    name: str
    name_local: str | None = None
    date: str
    is_work_day: bool
    affects_banks: bool
    region: str | None = None


# ============================================================================
# LEGAL REQUIREMENT
# ============================================================================

class LegalRequirementBase(BaseModel):
    country_pack_id: int
    category: str = Field(..., min_length=2, max_length=50)
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    requirement_type: str | None = None
    frequency: str | None = None
    deadline_rule: str | None = None
    config: dict[str, Any] | None = None
    legal_reference: str | None = None
    effective_date: date | None = None
    end_date: date | None = None
    is_mandatory: bool = True


class LegalRequirementCreate(LegalRequirementBase):
    pass


class LegalRequirementUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    requirement_type: str | None = None
    frequency: str | None = None
    deadline_rule: str | None = None
    config: dict[str, Any] | None = None
    is_mandatory: bool | None = None
    is_active: bool | None = None


class LegalRequirementResponse(LegalRequirementBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TENANT COUNTRY SETTINGS
# ============================================================================

class TenantCountryActivate(BaseModel):
    country_pack_id: int
    is_primary: bool = False
    custom_currency: str | None = None
    custom_language: str | None = None
    custom_timezone: str | None = None
    custom_config: dict[str, Any] | None = None


class TenantCountrySettingsResponse(BaseModel):
    id: int
    country_pack_id: int
    is_primary: bool
    is_active: bool
    custom_currency: str | None = None
    custom_language: str | None = None
    custom_timezone: str | None = None
    custom_config: dict[str, Any] | None = None
    activated_at: datetime
    activated_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# UTILITAIRES
# ============================================================================

class IBANValidationRequest(BaseModel):
    iban: str = Field(..., min_length=10, max_length=34)
    country_code: str = Field(..., min_length=2, max_length=2)


class IBANValidationResponse(BaseModel):
    valid: bool
    formatted_iban: str | None = None
    error: str | None = None


class CurrencyFormatRequest(BaseModel):
    amount: float
    country_code: str = Field(..., min_length=2, max_length=2)


class CurrencyFormatResponse(BaseModel):
    formatted: str
    currency: str
    symbol: str | None = None


class DateFormatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    format_date: date = Field(..., alias="date")
    country_code: str = Field(..., min_length=2, max_length=2)


class DateFormatResponse(BaseModel):
    formatted: str
    format_style: str


class CountrySummary(BaseModel):
    country_code: str
    country_name: str
    currency: str
    language: str
    timezone: str
    vat_rates_count: int
    templates_count: int
    bank_configs_count: int
    holidays_count: int
    requirements_count: int
    default_vat_rate: float
    fiscal_year_start: str


# ============================================================================
# LISTE PAGINÉE
# ============================================================================

class PaginatedCountryPacksResponse(BaseModel):
    items: list[CountryPackResponse]
    total: int
    skip: int
    limit: int


class PaginatedTaxRatesResponse(BaseModel):
    items: list[TaxRateResponse]
    total: int


class PaginatedTemplatesResponse(BaseModel):
    items: list[DocumentTemplateResponse]
    total: int
