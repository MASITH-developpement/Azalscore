"""
AZALS - PACK PAYS FRANCE - API Router
=======================================
Endpoints pour la localisation française.
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db

from .schemas import (
    DSNDeclarationResponse,
    DSNEmployeeData,
    # DSN
    DSNGenerateRequest,
    FECExportResponse,
    # FEC
    FECGenerateRequest,
    FECValidationResult,
    # Stats
    FrancePackStats,
    # Contrats
    FRContractCreate,
    FRContractResponse,
    # TVA
    FRVATRateResponse,
    # PCG
    PCGAccountCreate,
    PCGAccountResponse,
    RGPDBreachCreate,
    RGPDBreachResponse,
    # RGPD
    RGPDConsentCreate,
    RGPDConsentResponse,
    RGPDProcessingCreate,
    RGPDProcessingResponse,
    RGPDRequestCreate,
    RGPDRequestResponse,
    VATDeclarationCreate,
    VATDeclarationResponse,
)
from .service import FrancePackService

router = APIRouter(prefix="/france", tags=["Pack France"])


# ============================================================================
# PCG - PLAN COMPTABLE GÉNÉRAL
# ============================================================================

@router.post("/pcg/initialize")
def initialize_pcg(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Initialiser le PCG 2024 standard."""
    service = FrancePackService(db, tenant_id)
    count = service.initialize_pcg()
    return {"message": f"{count} comptes PCG créés", "count": count}


@router.get("/pcg/accounts", response_model=list[PCGAccountResponse])
def list_pcg_accounts(
    tenant_id: str = Query(...),
    pcg_class: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lister les comptes du PCG."""
    service = FrancePackService(db, tenant_id)
    return service.list_pcg_accounts(pcg_class, active_only, skip, limit)


@router.get("/pcg/accounts/{account_number}", response_model=PCGAccountResponse)
def get_pcg_account(
    account_number: str,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer un compte PCG."""
    service = FrancePackService(db, tenant_id)
    account = service.get_pcg_account(account_number)
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
    return account


@router.post("/pcg/accounts", response_model=PCGAccountResponse)
def create_pcg_account(
    data: PCGAccountCreate,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Créer un compte PCG personnalisé."""
    service = FrancePackService(db, tenant_id)
    return service.create_pcg_account(data)


# ============================================================================
# TVA FRANÇAISE
# ============================================================================

@router.post("/tva/initialize")
def initialize_vat_rates(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Initialiser les taux de TVA français."""
    service = FrancePackService(db, tenant_id)
    count = service.initialize_vat_rates()
    return {"message": f"{count} taux de TVA créés", "count": count}


@router.get("/tva/rates", response_model=list[FRVATRateResponse])
def list_vat_rates(
    tenant_id: str = Query(...),
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Lister les taux de TVA."""
    service = FrancePackService(db, tenant_id)
    return service.list_vat_rates(active_only)


@router.get("/tva/rates/{code}", response_model=FRVATRateResponse)
def get_vat_rate(
    code: str,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupérer un taux de TVA."""
    service = FrancePackService(db, tenant_id)
    rate = service.get_vat_rate(code)
    if not rate:
        raise HTTPException(status_code=404, detail="Taux non trouvé")
    return rate


@router.post("/tva/declarations", response_model=VATDeclarationResponse)
def create_vat_declaration(
    data: VATDeclarationCreate,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Créer une déclaration de TVA."""
    service = FrancePackService(db, tenant_id)
    return service.create_vat_declaration(data)


@router.post("/tva/declarations/{declaration_id}/calculate", response_model=VATDeclarationResponse)
def calculate_vat_declaration(
    declaration_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Calculer les montants d'une déclaration TVA."""
    service = FrancePackService(db, tenant_id)
    try:
        return service.calculate_vat_declaration(declaration_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# FEC - FICHIER DES ÉCRITURES COMPTABLES
# ============================================================================

@router.post("/fec/generate", response_model=FECExportResponse)
def generate_fec(
    data: FECGenerateRequest,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Générer un FEC."""
    service = FrancePackService(db, tenant_id)
    return service.generate_fec(data)


@router.post("/fec/{fec_id}/validate", response_model=FECValidationResult)
def validate_fec(
    fec_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Valider un FEC."""
    service = FrancePackService(db, tenant_id)
    try:
        return service.validate_fec(fec_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/fec/{fec_id}/export")
def export_fec_file(
    fec_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Exporter le FEC au format texte."""
    service = FrancePackService(db, tenant_id)
    try:
        content = service.export_fec_file(fec_id)
        return {"content": content, "format": "txt"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DSN - DÉCLARATION SOCIALE NOMINATIVE
# ============================================================================

@router.post("/dsn", response_model=DSNDeclarationResponse)
def create_dsn(
    data: DSNGenerateRequest,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Créer une DSN."""
    service = FrancePackService(db, tenant_id)
    return service.create_dsn(data)


@router.post("/dsn/{dsn_id}/employees")
def add_dsn_employee(
    dsn_id: int,
    data: DSNEmployeeData,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Ajouter un salarié à la DSN."""
    service = FrancePackService(db, tenant_id)
    try:
        employee = service.add_dsn_employee(dsn_id, data)
        return {"message": "Salarié ajouté", "employee_id": employee.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/dsn/{dsn_id}/submit", response_model=DSNDeclarationResponse)
def submit_dsn(
    dsn_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Soumettre la DSN."""
    service = FrancePackService(db, tenant_id)
    try:
        return service.submit_dsn(dsn_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# CONTRATS FRANÇAIS
# ============================================================================

@router.post("/contracts", response_model=FRContractResponse)
def create_contract(
    data: FRContractCreate,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Créer un contrat de travail français."""
    service = FrancePackService(db, tenant_id)
    return service.create_contract(data)


# ============================================================================
# RGPD
# ============================================================================

@router.post("/rgpd/consents", response_model=RGPDConsentResponse)
def create_consent(
    data: RGPDConsentCreate,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Créer un consentement RGPD."""
    service = FrancePackService(db, tenant_id)
    return service.create_consent(data)


@router.post("/rgpd/consents/{consent_id}/withdraw", response_model=RGPDConsentResponse)
def withdraw_consent(
    consent_id: int,
    reason: str | None = None,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Retirer un consentement RGPD."""
    service = FrancePackService(db, tenant_id)
    try:
        return service.withdraw_consent(consent_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rgpd/requests", response_model=RGPDRequestResponse)
def create_rgpd_request(
    data: RGPDRequestCreate,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Créer une demande RGPD (droit d'accès, effacement, etc.)."""
    service = FrancePackService(db, tenant_id)
    return service.create_rgpd_request(data)


@router.post("/rgpd/requests/{request_id}/process", response_model=RGPDRequestResponse)
def process_rgpd_request(
    request_id: int,
    response: str,
    data_exported: bool = False,
    data_deleted: bool = False,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Traiter une demande RGPD."""
    service = FrancePackService(db, tenant_id)
    try:
        return service.process_rgpd_request(request_id, response, data_exported, data_deleted)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rgpd/processing", response_model=RGPDProcessingResponse)
def create_data_processing(
    data: RGPDProcessingCreate,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Créer une entrée au registre des traitements (Article 30)."""
    service = FrancePackService(db, tenant_id)
    return service.create_data_processing(data)


@router.post("/rgpd/breaches", response_model=RGPDBreachResponse)
def report_data_breach(
    data: RGPDBreachCreate,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Signaler une violation de données."""
    service = FrancePackService(db, tenant_id)
    return service.report_data_breach(data)


# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", response_model=FrancePackStats)
def get_france_stats(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Statistiques du Pack France."""
    service = FrancePackService(db, tenant_id)
    return service.get_stats()
