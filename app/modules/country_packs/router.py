"""
AZALS MODULE T5 - Router API Packs Pays
========================================

Endpoints REST pour le module Packs Pays.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.modules.country_packs.models import BankFormat, DocumentType, PackStatus, TaxType
from app.modules.country_packs.schemas import (
    BankConfigCreate,
    BankConfigResponse,
    # Country Pack
    CountryPackCreate,
    CountryPackResponse,
    CountryPackUpdate,
    CountrySummary,
    CurrencyFormatRequest,
    CurrencyFormatResponse,
    DateFormatRequest,
    DateFormatResponse,
    DocumentTemplateCreate,
    DocumentTemplateResponse,
    HolidayWithDate,
    # Utils
    IBANValidationRequest,
    IBANValidationResponse,
    # Legal Requirement
    LegalRequirementCreate,
    LegalRequirementResponse,
    PaginatedCountryPacksResponse,
    # Holiday
    PublicHolidayCreate,
    PublicHolidayResponse,
    # Tax Rate
    TaxRateCreate,
    TaxRateResponse,
    TaxRateUpdate,
    # Tenant Settings
    TenantCountryActivate,
    TenantCountrySettingsResponse,
)
from app.modules.country_packs.service import CountryPackService, get_country_pack_service

router = APIRouter(prefix="/country-packs", tags=["Country Packs"])


def get_service(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> CountryPackService:
    """Obtient le service pour le tenant courant."""
    return get_country_pack_service(db, current_user.tenant_id)


# ============================================================================
# COUNTRY PACKS
# ============================================================================

@router.post("/", response_model=CountryPackResponse, status_code=status.HTTP_201_CREATED)
def create_country_pack(
    data: CountryPackCreate,
    service: CountryPackService = Depends(get_service),
    current_user = Depends(get_current_user)
):
    """Crée un nouveau pack pays."""
    pack = service.create_country_pack(
        country_code=data.country_code,
        country_name=data.country_name,
        default_currency=data.default_currency,
        country_name_local=data.country_name_local,
        default_language=data.default_language,
        currency_symbol=data.currency_symbol,
        date_format=data.date_format,
        number_format=data.number_format,
        timezone=data.timezone,
        fiscal_year_start_month=data.fiscal_year_start_month,
        default_vat_rate=data.default_vat_rate,
        company_id_label=data.company_id_label,
        vat_id_label=data.vat_id_label,
        config=data.config,
        is_default=data.is_default,
        created_by=current_user.id
    )
    return pack


@router.get("/", response_model=PaginatedCountryPacksResponse)
def list_country_packs(
    status: PackStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: CountryPackService = Depends(get_service)
):
    """Liste les packs pays."""
    packs, total = service.list_country_packs(
        status=status,
        skip=skip,
        limit=limit
    )
    return PaginatedCountryPacksResponse(items=packs, total=total, skip=skip, limit=limit)


@router.get("/default", response_model=Optional[CountryPackResponse])
def get_default_pack(service: CountryPackService = Depends(get_service)):
    """Récupère le pack pays par défaut."""
    return service.get_default_pack()


@router.get("/primary", response_model=Optional[CountryPackResponse])
def get_primary_pack(service: CountryPackService = Depends(get_service)):
    """Récupère le pack pays principal du tenant."""
    return service.get_primary_country()


@router.get("/{pack_id}", response_model=CountryPackResponse)
def get_country_pack(pack_id: int, service: CountryPackService = Depends(get_service)):
    """Récupère un pack pays par ID."""
    pack = service.get_country_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Country pack not found")
    return pack


@router.get("/code/{country_code}", response_model=CountryPackResponse)
def get_country_pack_by_code(country_code: str, service: CountryPackService = Depends(get_service)):
    """Récupère un pack pays par code."""
    pack = service.get_country_pack_by_code(country_code)
    if not pack:
        raise HTTPException(status_code=404, detail="Country pack not found")
    return pack


@router.get("/code/{country_code}/summary", response_model=CountrySummary)
def get_country_summary(country_code: str, service: CountryPackService = Depends(get_service)):
    """Récupère un résumé du pack pays."""
    summary = service.get_country_summary(country_code)
    if not summary:
        raise HTTPException(status_code=404, detail="Country pack not found")
    return CountrySummary(**summary)


@router.put("/{pack_id}", response_model=CountryPackResponse)
def update_country_pack(
    pack_id: int,
    data: CountryPackUpdate,
    service: CountryPackService = Depends(get_service)
):
    """Met à jour un pack pays."""
    pack = service.update_country_pack(pack_id, **data.model_dump(exclude_unset=True))
    if not pack:
        raise HTTPException(status_code=404, detail="Country pack not found")
    return pack


@router.delete("/{pack_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_country_pack(pack_id: int, service: CountryPackService = Depends(get_service)):
    """Supprime un pack pays."""
    if not service.delete_country_pack(pack_id):
        raise HTTPException(status_code=404, detail="Country pack not found")


# ============================================================================
# TAX RATES
# ============================================================================

@router.post("/tax-rates", response_model=TaxRateResponse, status_code=status.HTTP_201_CREATED)
def create_tax_rate(
    data: TaxRateCreate,
    service: CountryPackService = Depends(get_service)
):
    """Crée un taux de taxe."""
    tax = service.create_tax_rate(
        country_pack_id=data.country_pack_id,
        tax_type=data.tax_type,
        code=data.code,
        name=data.name,
        rate=data.rate,
        description=data.description,
        applies_to=data.applies_to,
        region=data.region,
        account_collected=data.account_collected,
        account_deductible=data.account_deductible,
        account_payable=data.account_payable,
        valid_from=data.valid_from,
        valid_to=data.valid_to,
        is_default=data.is_default
    )
    return tax


@router.get("/tax-rates", response_model=list[TaxRateResponse])
def list_tax_rates(
    country_pack_id: int | None = None,
    tax_type: TaxType | None = None,
    is_active: bool = True,
    service: CountryPackService = Depends(get_service)
):
    """Liste les taux de taxe."""
    return service.get_tax_rates(
        country_pack_id=country_pack_id,
        tax_type=tax_type,
        is_active=is_active
    )


@router.get("/tax-rates/vat/{country_code}", response_model=list[TaxRateResponse])
def get_vat_rates(country_code: str, service: CountryPackService = Depends(get_service)):
    """Récupère les taux de TVA pour un pays."""
    return service.get_vat_rates(country_code)


@router.get("/tax-rates/vat/{country_code}/default", response_model=Optional[TaxRateResponse])
def get_default_vat_rate(country_code: str, service: CountryPackService = Depends(get_service)):
    """Récupère le taux de TVA par défaut pour un pays."""
    return service.get_default_vat_rate(country_code)


@router.put("/tax-rates/{tax_id}", response_model=TaxRateResponse)
def update_tax_rate(
    tax_id: int,
    data: TaxRateUpdate,
    service: CountryPackService = Depends(get_service)
):
    """Met à jour un taux de taxe."""
    tax = service.update_tax_rate(tax_id, **data.model_dump(exclude_unset=True))
    if not tax:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    return tax


@router.delete("/tax-rates/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tax_rate(tax_id: int, service: CountryPackService = Depends(get_service)):
    """Supprime un taux de taxe."""
    if not service.delete_tax_rate(tax_id):
        raise HTTPException(status_code=404, detail="Tax rate not found")


# ============================================================================
# DOCUMENT TEMPLATES
# ============================================================================

@router.post("/templates", response_model=DocumentTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_document_template(
    data: DocumentTemplateCreate,
    service: CountryPackService = Depends(get_service),
    current_user = Depends(get_current_user)
):
    """Crée un template de document."""
    template = service.create_document_template(
        country_pack_id=data.country_pack_id,
        document_type=data.document_type,
        code=data.code,
        name=data.name,
        description=data.description,
        template_format=data.template_format,
        template_content=data.template_content,
        template_path=data.template_path,
        mandatory_fields=data.mandatory_fields,
        legal_mentions=data.legal_mentions,
        numbering_prefix=data.numbering_prefix,
        numbering_pattern=data.numbering_pattern,
        language=data.language,
        is_default=data.is_default,
        created_by=current_user.id
    )
    return template


@router.get("/templates", response_model=list[DocumentTemplateResponse])
def list_document_templates(
    country_pack_id: int | None = None,
    document_type: DocumentType | None = None,
    is_active: bool = True,
    service: CountryPackService = Depends(get_service)
):
    """Liste les templates de documents."""
    return service.get_document_templates(
        country_pack_id=country_pack_id,
        document_type=document_type,
        is_active=is_active
    )


@router.get("/templates/default/{country_code}/{document_type}", response_model=Optional[DocumentTemplateResponse])
def get_default_template(
    country_code: str,
    document_type: DocumentType,
    service: CountryPackService = Depends(get_service)
):
    """Récupère le template par défaut pour un type de document."""
    return service.get_default_template(country_code, document_type)


# ============================================================================
# BANK CONFIGS
# ============================================================================

@router.post("/bank-configs", response_model=BankConfigResponse, status_code=status.HTTP_201_CREATED)
def create_bank_config(
    data: BankConfigCreate,
    service: CountryPackService = Depends(get_service)
):
    """Crée une configuration bancaire."""
    config = service.create_bank_config(
        country_pack_id=data.country_pack_id,
        bank_format=data.bank_format,
        code=data.code,
        name=data.name,
        description=data.description,
        iban_prefix=data.iban_prefix,
        iban_length=data.iban_length,
        bic_required=data.bic_required,
        export_format=data.export_format,
        export_encoding=data.export_encoding,
        export_template=data.export_template,
        config=data.config,
        is_default=data.is_default
    )
    return config


@router.get("/bank-configs", response_model=list[BankConfigResponse])
def list_bank_configs(
    country_pack_id: int | None = None,
    bank_format: BankFormat | None = None,
    service: CountryPackService = Depends(get_service)
):
    """Liste les configurations bancaires."""
    return service.get_bank_configs(
        country_pack_id=country_pack_id,
        bank_format=bank_format
    )


@router.post("/bank-configs/validate-iban", response_model=IBANValidationResponse)
def validate_iban(
    data: IBANValidationRequest,
    service: CountryPackService = Depends(get_service)
):
    """Valide un IBAN pour un pays."""
    result = service.validate_iban(data.iban, data.country_code)
    return IBANValidationResponse(**result)


# ============================================================================
# HOLIDAYS
# ============================================================================

@router.post("/holidays", response_model=PublicHolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(
    data: PublicHolidayCreate,
    service: CountryPackService = Depends(get_service)
):
    """Crée un jour férié."""
    holiday = service.create_holiday(
        country_pack_id=data.country_pack_id,
        name=data.name,
        name_local=data.name_local,
        holiday_date=data.holiday_date,
        month=data.month,
        day=data.day,
        is_fixed=data.is_fixed,
        calculation_rule=data.calculation_rule,
        year=data.year,
        region=data.region,
        is_national=data.is_national,
        is_work_day=data.is_work_day,
        affects_banks=data.affects_banks,
        affects_business=data.affects_business
    )
    return holiday


@router.get("/holidays", response_model=list[PublicHolidayResponse])
def list_holidays(
    country_pack_id: int | None = None,
    year: int | None = None,
    region: str | None = None,
    service: CountryPackService = Depends(get_service)
):
    """Liste les jours fériés."""
    return service.get_holidays(
        country_pack_id=country_pack_id,
        year=year,
        region=region
    )


@router.get("/holidays/{country_code}/year/{year}", response_model=list[HolidayWithDate])
def get_holidays_for_year(
    country_code: str,
    year: int,
    service: CountryPackService = Depends(get_service)
):
    """Récupère les jours fériés pour une année avec dates calculées."""
    holidays = service.get_holidays_for_year(country_code, year)
    return [HolidayWithDate(**h) for h in holidays]


@router.get("/holidays/{country_code}/check/{check_date}", response_model=bool)
def is_holiday(
    country_code: str,
    check_date: date,
    service: CountryPackService = Depends(get_service)
):
    """Vérifie si une date est un jour férié."""
    return service.is_holiday(check_date, country_code)


# ============================================================================
# LEGAL REQUIREMENTS
# ============================================================================

@router.post("/legal-requirements", response_model=LegalRequirementResponse, status_code=status.HTTP_201_CREATED)
def create_legal_requirement(
    data: LegalRequirementCreate,
    service: CountryPackService = Depends(get_service)
):
    """Crée une exigence légale."""
    req = service.create_legal_requirement(
        country_pack_id=data.country_pack_id,
        category=data.category,
        code=data.code,
        name=data.name,
        description=data.description,
        requirement_type=data.requirement_type,
        frequency=data.frequency,
        deadline_rule=data.deadline_rule,
        config=data.config,
        legal_reference=data.legal_reference,
        effective_date=data.effective_date,
        is_mandatory=data.is_mandatory
    )
    return req


@router.get("/legal-requirements", response_model=list[LegalRequirementResponse])
def list_legal_requirements(
    country_pack_id: int | None = None,
    category: str | None = None,
    service: CountryPackService = Depends(get_service)
):
    """Liste les exigences légales."""
    return service.get_legal_requirements(
        country_pack_id=country_pack_id,
        category=category
    )


# ============================================================================
# TENANT SETTINGS
# ============================================================================

@router.post("/tenant/activate", response_model=TenantCountrySettingsResponse)
def activate_country_for_tenant(
    data: TenantCountryActivate,
    service: CountryPackService = Depends(get_service),
    current_user = Depends(get_current_user)
):
    """Active un pack pays pour le tenant."""
    settings = service.activate_country_for_tenant(
        country_pack_id=data.country_pack_id,
        is_primary=data.is_primary,
        custom_config=data.custom_config,
        activated_by=current_user.id
    )
    return settings


@router.get("/tenant/countries", response_model=list[TenantCountrySettingsResponse])
def get_tenant_countries(
    active_only: bool = True,
    service: CountryPackService = Depends(get_service)
):
    """Récupère les pays activés pour le tenant."""
    return service.get_tenant_countries(active_only=active_only)


# ============================================================================
# UTILS
# ============================================================================

@router.post("/utils/format-currency", response_model=CurrencyFormatResponse)
def format_currency(
    data: CurrencyFormatRequest,
    service: CountryPackService = Depends(get_service)
):
    """Formate un montant selon les conventions du pays."""
    pack = service.get_country_pack_by_code(data.country_code)
    if not pack:
        raise HTTPException(status_code=404, detail="Country pack not found")

    formatted = service.format_currency(data.amount, data.country_code)
    return CurrencyFormatResponse(
        formatted=formatted,
        currency=pack.default_currency,
        symbol=pack.currency_symbol
    )


@router.post("/utils/format-date", response_model=DateFormatResponse)
def format_date(
    data: DateFormatRequest,
    service: CountryPackService = Depends(get_service)
):
    """Formate une date selon les conventions du pays."""
    pack = service.get_country_pack_by_code(data.country_code)
    if not pack:
        raise HTTPException(status_code=404, detail="Country pack not found")

    formatted = service.format_date(data.date, data.country_code)
    return DateFormatResponse(
        formatted=formatted,
        format_style=pack.date_format.value
    )
