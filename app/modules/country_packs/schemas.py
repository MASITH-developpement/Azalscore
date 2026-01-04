"""
AZALS MODULE T5 - Schémas Pydantic Packs Pays
==============================================

Schémas de validation pour les API du module Packs Pays.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


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
    country_name_local: Optional[str] = None
    default_language: str = "fr"
    currency_symbol: Optional[str] = None
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
    company_id_format: Optional[str] = None
    vat_id_label: str = "TVA"
    vat_id_format: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_default: bool = False


class CountryPackCreate(CountryPackBase):
    pass


class CountryPackUpdate(BaseModel):
    country_name: Optional[str] = Field(None, min_length=2, max_length=100)
    country_name_local: Optional[str] = None
    default_language: Optional[str] = None
    currency_symbol: Optional[str] = None
    currency_position: Optional[str] = None
    date_format: Optional[DateFormatStyleEnum] = None
    number_format: Optional[NumberFormatStyleEnum] = None
    timezone: Optional[str] = None
    default_vat_rate: Optional[float] = None
    company_id_label: Optional[str] = None
    vat_id_label: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    status: Optional[PackStatusEnum] = None


class CountryPackResponse(CountryPackBase):
    id: int
    status: PackStatusEnum
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# TAX RATE
# ============================================================================

class TaxRateBase(BaseModel):
    country_pack_id: int
    tax_type: TaxTypeEnum
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    rate: float = Field(..., ge=0, le=100)
    is_percentage: bool = True
    applies_to: Optional[str] = "both"
    region: Optional[str] = None
    account_collected: Optional[str] = None
    account_deductible: Optional[str] = None
    account_payable: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_default: bool = False


class TaxRateCreate(TaxRateBase):
    pass


class TaxRateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    rate: Optional[float] = Field(None, ge=0, le=100)
    applies_to: Optional[str] = None
    region: Optional[str] = None
    account_collected: Optional[str] = None
    account_deductible: Optional[str] = None
    account_payable: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class TaxRateResponse(TaxRateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# DOCUMENT TEMPLATE
# ============================================================================

class DocumentTemplateBase(BaseModel):
    country_pack_id: int
    document_type: DocumentTypeEnum
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    template_format: str = "html"
    template_content: Optional[str] = None
    template_path: Optional[str] = None
    mandatory_fields: Optional[List[str]] = None
    legal_mentions: Optional[str] = None
    numbering_prefix: Optional[str] = None
    numbering_pattern: Optional[str] = None
    numbering_reset: str = "yearly"
    language: str = "fr"
    is_default: bool = False


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    template_content: Optional[str] = None
    template_path: Optional[str] = None
    mandatory_fields: Optional[List[str]] = None
    legal_mentions: Optional[str] = None
    numbering_prefix: Optional[str] = None
    numbering_pattern: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# BANK CONFIG
# ============================================================================

class BankConfigBase(BaseModel):
    country_pack_id: int
    bank_format: BankFormatEnum
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    iban_prefix: Optional[str] = None
    iban_length: Optional[int] = None
    bic_required: bool = True
    export_format: str = "xml"
    export_encoding: str = "utf-8"
    export_template: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_default: bool = False


class BankConfigCreate(BankConfigBase):
    pass


class BankConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    iban_prefix: Optional[str] = None
    iban_length: Optional[int] = None
    bic_required: Optional[bool] = None
    export_format: Optional[str] = None
    export_template: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class BankConfigResponse(BankConfigBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# PUBLIC HOLIDAY
# ============================================================================

class PublicHolidayBase(BaseModel):
    country_pack_id: int
    name: str = Field(..., min_length=2, max_length=200)
    name_local: Optional[str] = None
    holiday_date: Optional[date] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    is_fixed: bool = True
    calculation_rule: Optional[str] = None
    year: Optional[int] = None
    region: Optional[str] = None
    is_national: bool = True
    is_work_day: bool = False
    affects_banks: bool = True
    affects_business: bool = True


class PublicHolidayCreate(PublicHolidayBase):
    pass


class PublicHolidayUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    name_local: Optional[str] = None
    holiday_date: Optional[date] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    is_work_day: Optional[bool] = None
    is_active: Optional[bool] = None


class PublicHolidayResponse(PublicHolidayBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HolidayWithDate(BaseModel):
    id: int
    name: str
    name_local: Optional[str] = None
    date: str
    is_work_day: bool
    affects_banks: bool
    region: Optional[str] = None


# ============================================================================
# LEGAL REQUIREMENT
# ============================================================================

class LegalRequirementBase(BaseModel):
    country_pack_id: int
    category: str = Field(..., min_length=2, max_length=50)
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    requirement_type: Optional[str] = None
    frequency: Optional[str] = None
    deadline_rule: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    legal_reference: Optional[str] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    is_mandatory: bool = True


class LegalRequirementCreate(LegalRequirementBase):
    pass


class LegalRequirementUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    requirement_type: Optional[str] = None
    frequency: Optional[str] = None
    deadline_rule: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_mandatory: Optional[bool] = None
    is_active: Optional[bool] = None


class LegalRequirementResponse(LegalRequirementBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# TENANT COUNTRY SETTINGS
# ============================================================================

class TenantCountryActivate(BaseModel):
    country_pack_id: int
    is_primary: bool = False
    custom_currency: Optional[str] = None
    custom_language: Optional[str] = None
    custom_timezone: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None


class TenantCountrySettingsResponse(BaseModel):
    id: int
    country_pack_id: int
    is_primary: bool
    is_active: bool
    custom_currency: Optional[str] = None
    custom_language: Optional[str] = None
    custom_timezone: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None
    activated_at: datetime
    activated_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# UTILITAIRES
# ============================================================================

class IBANValidationRequest(BaseModel):
    iban: str = Field(..., min_length=10, max_length=34)
    country_code: str = Field(..., min_length=2, max_length=2)


class IBANValidationResponse(BaseModel):
    valid: bool
    formatted_iban: Optional[str] = None
    error: Optional[str] = None


class CurrencyFormatRequest(BaseModel):
    amount: float
    country_code: str = Field(..., min_length=2, max_length=2)


class CurrencyFormatResponse(BaseModel):
    formatted: str
    currency: str
    symbol: Optional[str] = None


class DateFormatRequest(BaseModel):
    date: date
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
    items: List[CountryPackResponse]
    total: int
    skip: int
    limit: int


class PaginatedTaxRatesResponse(BaseModel):
    items: List[TaxRateResponse]
    total: int


class PaginatedTemplatesResponse(BaseModel):
    items: List[DocumentTemplateResponse]
    total: int
