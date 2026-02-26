"""
AZALS MODULE T5 - Router Packs Pays Unifié
==========================================

API unifiée pour la gestion des configurations pays.
Compatible v1 et v2 via double enregistrement.
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .service import CountryPackService
from .models import (
    PackStatus, TaxType, DocumentType, BankFormat,
    DateFormatStyle, NumberFormatStyle
)

router = APIRouter(prefix="/country-packs", tags=["Country Packs"])

def get_country_pack_service(db: Session, tenant_id: str, user_id: str) -> CountryPackService:
    """Factory pour créer le service Country Packs avec contexte SaaS."""
    return CountryPackService(db, tenant_id, user_id)

# ============================================================================
# COUNTRY PACKS (PACKS PAYS)
# ============================================================================

@router.get("/packs")
async def list_country_packs(
    status: PackStatus | None = Query(None, description="Filtrer par statut"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister tous les packs pays."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    packs, total = service.list_country_packs(status, skip, limit)
    return {"packs": packs, "total": total}

@router.get("/packs/{pack_id}")
async def get_country_pack(
    pack_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un pack pays par ID."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    pack = service.get_country_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Country pack not found")
    return pack

@router.get("/packs/code/{country_code}")
async def get_country_pack_by_code(
    country_code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un pack pays par code (ex: FR, US)."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    pack = service.get_country_pack_by_code(country_code)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Country pack '{country_code}' not found")
    return pack

@router.get("/packs/default")
async def get_default_pack(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer le pack pays par défaut."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    pack = service.get_default_pack()
    if not pack:
        raise HTTPException(status_code=404, detail="No default country pack configured")
    return pack

@router.get("/summary/{country_code}")
async def get_country_summary(
    country_code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un résumé complet du pack pays."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_country_summary(country_code)

# ============================================================================
# TAX RATES (TAUX DE TAXE)
# ============================================================================

@router.get("/tax-rates")
async def get_tax_rates(
    country_pack_id: int | None = Query(None, description="Filtrer par pack pays"),
    tax_type: TaxType | None = Query(None, description="Filtrer par type de taxe"),
    is_active: bool = Query(True, description="Filtrer actifs uniquement"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les taux de taxe."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_tax_rates(country_pack_id, tax_type, is_active)

@router.get("/vat-rates/{country_code}")
async def get_vat_rates(
    country_code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer les taux de TVA pour un pays."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_vat_rates(country_code)

@router.get("/vat-rates/{country_code}/default")
async def get_default_vat_rate(
    country_code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer le taux de TVA par défaut pour un pays."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    rate = service.get_default_vat_rate(country_code)
    if not rate:
        raise HTTPException(status_code=404, detail="No default VAT rate found")
    return rate

# ============================================================================
# DOCUMENT TEMPLATES
# ============================================================================

@router.get("/templates")
async def get_document_templates(
    country_pack_id: int | None = Query(None, description="Filtrer par pack pays"),
    document_type: DocumentType | None = Query(None, description="Filtrer par type de document"),
    is_active: bool = Query(True, description="Filtrer actifs uniquement"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les templates de documents."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_document_templates(country_pack_id, document_type, is_active)

@router.get("/templates/{country_code}/{document_type}/default")
async def get_default_template(
    country_code: str,
    document_type: DocumentType,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer le template par défaut pour un type de document."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    template = service.get_default_template(country_code, document_type)
    if not template:
        raise HTTPException(status_code=404, detail="No default template found")
    return template

# ============================================================================
# BANK CONFIGURATIONS
# ============================================================================

@router.get("/bank-configs")
async def get_bank_configs(
    country_pack_id: int | None = Query(None, description="Filtrer par pack pays"),
    bank_format: BankFormat | None = Query(None, description="Filtrer par format"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les configurations bancaires."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_bank_configs(country_pack_id, bank_format)

@router.post("/bank-configs/validate-iban")
async def validate_iban(
    iban: str = Query(..., description="IBAN à valider"),
    country_code: str = Query(..., description="Code pays"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Valider un IBAN pour un pays."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.validate_iban(iban, country_code)

# ============================================================================
# PUBLIC HOLIDAYS (JOURS FÉRIÉS)
# ============================================================================

@router.get("/holidays")
async def get_holidays(
    country_pack_id: int | None = Query(None, description="Filtrer par pack pays"),
    year: int | None = Query(None, description="Filtrer par année"),
    region: str | None = Query(None, description="Filtrer par région"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les jours fériés."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_holidays(country_pack_id, year, region)

@router.get("/holidays/{country_code}/year/{year}")
async def get_holidays_for_year(
    country_code: str,
    year: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer les jours fériés pour une année avec dates calculées."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_holidays_for_year(country_code, year)

@router.post("/holidays/check")
async def is_holiday(
    check_date: date = Query(..., description="Date à vérifier"),
    country_code: str = Query(..., description="Code pays"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Vérifier si une date est un jour férié."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    is_hol = service.is_holiday(check_date, country_code)
    return {"date": check_date, "country_code": country_code, "is_holiday": is_hol}

# ============================================================================
# LEGAL REQUIREMENTS (EXIGENCES LÉGALES)
# ============================================================================

@router.get("/legal-requirements")
async def get_legal_requirements(
    country_pack_id: int | None = Query(None, description="Filtrer par pack pays"),
    category: str | None = Query(None, description="Filtrer par catégorie"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les exigences légales."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_legal_requirements(country_pack_id, category)

# ============================================================================
# TENANT COUNTRY SETTINGS
# ============================================================================

@router.get("/tenant/countries")
async def get_tenant_countries(
    active_only: bool = Query(True, description="Filtrer actifs uniquement"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer les pays activés pour le tenant."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    return service.get_tenant_countries(active_only)

@router.get("/tenant/primary-country")
async def get_primary_country(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer le pack pays principal du tenant."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    pack = service.get_primary_country()
    if not pack:
        raise HTTPException(status_code=404, detail="No primary country configured")
    return pack

@router.post("/tenant/activate-country", status_code=201)
async def activate_country_for_tenant(
    country_pack_id: int = Query(..., description="ID du pack pays à activer"),
    is_primary: bool = Query(False, description="Définir comme pays principal"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Activer un pack pays pour le tenant."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    activated_by = int(context.user_id) if context.user_id else None
    return service.activate_country_for_tenant(country_pack_id, is_primary, None, activated_by)

# ============================================================================
# UTILITIES (FORMATAGE)
# ============================================================================

@router.post("/format-currency")
async def format_currency(
    amount: float = Query(..., description="Montant à formater"),
    country_code: str = Query(..., description="Code pays"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Formater un montant selon les conventions du pays."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    formatted = service.format_currency(amount, country_code)
    return {"amount": amount, "country_code": country_code, "formatted": formatted}

@router.post("/format-date")
async def format_date(
    date_value: date = Query(..., description="Date à formater"),
    country_code: str = Query(..., description="Code pays"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Formater une date selon les conventions du pays."""
    service = get_country_pack_service(db, context.tenant_id, context.user_id)
    formatted = service.format_date(date_value, country_code)
    return {"date": date_value, "country_code": country_code, "formatted": formatted}
