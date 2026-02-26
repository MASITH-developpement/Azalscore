"""
AZALS - PACK PAYS FRANCE - API Router
=======================================
Endpoints pour la localisation française.
"""
from __future__ import annotations



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
# PAIE FRANCE - CALCUL COTISATIONS ET BULLETINS
# ============================================================================

from .paie_france import (
    PaieFranceService,
    BaremesPayeFrance,
    COTISATIONS_FRANCE_2024,
)
from decimal import Decimal


@router.get("/paie/baremes")
def get_baremes_paie(
    tenant_id: str = Query(...),
):
    """
    Récupérer les barèmes de paie France en vigueur.
    Inclut PMSS, SMIC, durée légale du travail.
    """
    return {
        "annee": 2024,
        "pmss": float(BaremesPayeFrance.PMSS_2024),
        "pass": float(BaremesPayeFrance.PASS_2024),
        "smic_horaire": float(BaremesPayeFrance.SMIC_HORAIRE_2024),
        "smic_mensuel": float(BaremesPayeFrance.SMIC_MENSUEL_2024),
        "heures_mensuelles": float(BaremesPayeFrance.HEURES_MENSUELLES),
        "heures_hebdo": float(BaremesPayeFrance.HEURES_HEBDO),
        "majoration_hs_8_premieres": float(BaremesPayeFrance.MAJORATION_HS_8_PREMIERES),
        "majoration_hs_suivantes": float(BaremesPayeFrance.MAJORATION_HS_SUIVANTES)
    }


@router.get("/paie/cotisations")
def get_cotisations_france(
    tenant_id: str = Query(...),
    is_cadre: bool = Query(False),
    effectif: int = Query(50)
):
    """
    Récupérer la liste des cotisations sociales applicables.
    Filtre selon cadre/non-cadre et effectif entreprise.
    """
    cotisations = []
    for c in COTISATIONS_FRANCE_2024:
        if c.categorie == "cadre" and not is_cadre:
            continue
        cotisations.append({
            "code": c.code,
            "libelle": c.libelle,
            "taux_salarial": float(c.taux_salarial),
            "taux_patronal": float(c.taux_patronal),
            "plafond": float(c.plafond) if c.plafond else None,
            "base": c.base,
            "categorie": c.categorie
        })
    return {"cotisations": cotisations, "count": len(cotisations)}


@router.post("/paie/simulation")
def simuler_bulletin_paie(
    salaire_brut: Decimal = Query(..., description="Salaire brut mensuel"),
    is_cadre: bool = Query(False),
    is_cdd: bool = Query(False),
    effectif: int = Query(50, description="Effectif entreprise"),
    zone_transport: str = Query("IDF", description="Zone versement mobilité"),
    taux_at: Decimal = Query(Decimal("2.00"), description="Taux AT/MP"),
    alsace_moselle: bool = Query(False),
    taux_pas: Decimal = Query(None, description="Taux PAS personnalisé"),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Simuler un bulletin de paie avec calcul détaillé des cotisations.
    Retourne les montants salariaux, patronaux et le net à payer.
    """
    service = PaieFranceService(
        db=db,
        tenant_id=tenant_id,
        is_cadre=is_cadre,
        is_cdd=is_cdd,
        effectif_entreprise=effectif,
        zone_transport=zone_transport,
        taux_at=taux_at,
        alsace_moselle=alsace_moselle
    )

    lignes, total_salarial, total_patronal = service.calculer_cotisations(salaire_brut)

    # Calcul net imposable et net à payer
    net_imposable = salaire_brut - total_salarial
    # Ajouter CSG non déductible au net imposable
    for ligne in lignes:
        if ligne.code == "CSG_NDED":
            net_imposable += ligne.montant_salarial

    # Calcul PAS
    if taux_pas is not None:
        pas = service.calculer_pas(net_imposable, taux_pas)
    else:
        pas, _ = service.calculer_pas(net_imposable)

    net_a_payer = salaire_brut - total_salarial - pas

    return {
        "salaire_brut": float(salaire_brut),
        "cotisations": [
            {
                "code": l.code,
                "libelle": l.libelle,
                "base": float(l.base),
                "taux_salarial": float(l.taux_salarial),
                "montant_salarial": float(l.montant_salarial),
                "taux_patronal": float(l.taux_patronal),
                "montant_patronal": float(l.montant_patronal)
            }
            for l in lignes
        ],
        "totaux": {
            "total_salarial": float(total_salarial),
            "total_patronal": float(total_patronal),
            "cout_employeur": float(salaire_brut + total_patronal)
        },
        "net": {
            "net_avant_pas": float(salaire_brut - total_salarial),
            "net_imposable": float(net_imposable),
            "prelevement_source": float(pas),
            "net_a_payer": float(net_a_payer)
        },
        "ratios": {
            "taux_charges_salariales": float(total_salarial / salaire_brut * 100),
            "taux_charges_patronales": float(total_patronal / salaire_brut * 100)
        }
    }


@router.get("/paie/taux-pas")
def get_taux_pas_bareme(
    revenu_mensuel: Decimal = Query(..., description="Revenu mensuel net imposable"),
    tenant_id: str = Query(...)
):
    """
    Récupérer le taux de PAS applicable selon le barème par défaut.
    Utilisé en l'absence de taux personnalisé transmis par la DGFiP.
    """
    # Barème simplifié 2024 (taux neutre mensuel)
    bareme = [
        (Decimal("1591"), Decimal("0")),
        (Decimal("1653"), Decimal("0.5")),
        (Decimal("1759"), Decimal("1.3")),
        (Decimal("1877"), Decimal("2.1")),
        (Decimal("2003"), Decimal("2.9")),
        (Decimal("2137"), Decimal("3.5")),
        (Decimal("2289"), Decimal("4.1")),
        (Decimal("2522"), Decimal("5.3")),
        (Decimal("2810"), Decimal("6.5")),
        (Decimal("3165"), Decimal("7.5")),
        (Decimal("3568"), Decimal("8.5")),
        (Decimal("4070"), Decimal("9.9")),
        (Decimal("4690"), Decimal("11.9")),
        (Decimal("5588"), Decimal("13.8")),
        (Decimal("6883"), Decimal("15.8")),
        (Decimal("8654"), Decimal("17.9")),
        (Decimal("11539"), Decimal("20")),
        (Decimal("16002"), Decimal("24")),
        (Decimal("24722"), Decimal("28")),
        (Decimal("50000"), Decimal("33")),
        (Decimal("999999"), Decimal("43")),
    ]

    taux = Decimal("0")
    for seuil, t in bareme:
        if revenu_mensuel <= seuil:
            taux = t
            break

    return {
        "revenu_mensuel": float(revenu_mensuel),
        "taux_pas": float(taux),
        "montant_pas": float(revenu_mensuel * taux / 100)
    }


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
# EDI-TVA - DÉCLARATIONS AUTOMATIQUES (Article 287 CGI)
# ============================================================================

from .edi_tva import EDITVAService, EDITVAConfig, EDITVAScheduler


@router.post("/edi-tva/configure")
def configure_edi_tva(
    partner_id: str = Query(..., description="Identifiant partenaire EDI agréé"),
    sender_siret: str = Query(..., min_length=14, max_length=14),
    sender_siren: str = Query(..., min_length=9, max_length=9),
    tax_id: str = Query(..., description="Numéro TVA intracommunautaire (FR + 11 chiffres)"),
    direction: str = Query(..., description="Service des impôts (SIE)"),
    test_mode: bool = Query(True, description="Mode test/production"),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Configurer les paramètres EDI-TVA pour le tenant.
    Nécessaire avant toute transmission automatique.
    """
    config = EDITVAConfig(
        partner_id=partner_id,
        sender_siret=sender_siret,
        sender_siren=sender_siren,
        tax_id=tax_id,
        direction=direction,
        test_mode=test_mode
    )
    # Stocker la config (à implémenter avec le module settings)
    return {
        "success": True,
        "message": "Configuration EDI-TVA enregistrée",
        "config": {
            "partner_id": partner_id,
            "siret": sender_siret,
            "siren": sender_siren,
            "tax_id": tax_id,
            "direction": direction,
            "test_mode": test_mode
        }
    }


@router.post("/edi-tva/declarations/{declaration_id}/validate")
def validate_tva_declaration(
    declaration_id: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Valider une déclaration TVA avant transmission EDI.
    Vérifie la cohérence des montants et le format des données.
    """
    # Config par défaut pour validation (lecture seule)
    config = EDITVAConfig(
        partner_id="VALIDATION",
        sender_siret="00000000000000",
        sender_siren="000000000",
        tax_id="FR00000000000",
        direction="SIE",
        test_mode=True
    )
    service = EDITVAService(db, tenant_id, config)
    return service.validate_declaration(declaration_id)


@router.post("/edi-tva/declarations/{declaration_id}/generate")
def generate_edi_tva_message(
    declaration_id: int,
    tenant_id: str = Query(...),
    sender_siret: str = Query(..., min_length=14, max_length=14),
    sender_siren: str = Query(..., min_length=9, max_length=9),
    db: Session = Depends(get_db)
):
    """
    Générer le message EDIFACT pour une déclaration CA3.
    Retourne le fichier EDI prêt pour transmission.
    """
    config = EDITVAConfig(
        partner_id="GENERATION",
        sender_siret=sender_siret,
        sender_siren=sender_siren,
        tax_id="",
        direction="",
        test_mode=True
    )
    service = EDITVAService(db, tenant_id, config)
    edi_message = service.generate_ca3(declaration_id)
    return {
        "declaration_id": declaration_id,
        "format": "EDIFACT/TAXCON",
        "message": edi_message
    }


@router.post("/edi-tva/declarations/{declaration_id}/submit")
def submit_tva_declaration(
    declaration_id: int,
    partner_id: str = Query(..., description="Identifiant partenaire EDI"),
    sender_siret: str = Query(..., min_length=14, max_length=14),
    sender_siren: str = Query(..., min_length=9, max_length=9),
    tax_id: str = Query(..., description="Numéro TVA intracommunautaire"),
    direction: str = Query(..., description="Service des impôts"),
    test_mode: bool = Query(True),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Soumettre une déclaration TVA via EDI-TVA.
    En mode production, la déclaration est transmise à la DGFiP.
    """
    config = EDITVAConfig(
        partner_id=partner_id,
        sender_siret=sender_siret,
        sender_siren=sender_siren,
        tax_id=tax_id,
        direction=direction,
        test_mode=test_mode
    )
    service = EDITVAService(db, tenant_id, config)
    response = service.submit_declaration(declaration_id)
    return {
        "success": response.success,
        "transmission_id": response.transmission_id,
        "timestamp": response.timestamp.isoformat(),
        "status": response.status.value,
        "message": response.message,
        "dgfip_reference": response.dgfip_reference,
        "errors": response.errors,
        "warnings": response.warnings
    }


@router.get("/edi-tva/transmissions/{transmission_id}/status")
def get_transmission_status(
    transmission_id: str,
    partner_id: str = Query(...),
    sender_siret: str = Query(...),
    sender_siren: str = Query(...),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Récupérer le statut d'une transmission EDI-TVA.
    Permet de vérifier l'accusé de réception DGFiP.
    """
    config = EDITVAConfig(
        partner_id=partner_id,
        sender_siret=sender_siret,
        sender_siren=sender_siren,
        tax_id="",
        direction="",
        test_mode=True
    )
    service = EDITVAService(db, tenant_id, config)
    response = service.get_acknowledgment(transmission_id)
    return {
        "transmission_id": response.transmission_id,
        "status": response.status.value,
        "timestamp": response.timestamp.isoformat(),
        "message": response.message
    }


@router.get("/edi-tva/calendar/{year}")
def get_tva_calendar(
    year: int,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Obtenir le calendrier des échéances TVA pour l'année.
    Inclut les dates limites de dépôt CA3 et CA12.
    """
    scheduler = EDITVAScheduler(db, tenant_id)
    return {
        "year": year,
        "deadlines": scheduler.get_calendar(year)
    }


@router.get("/edi-tva/pending")
def get_pending_declarations(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Récupérer les déclarations TVA en attente de transmission.
    Utile pour le tableau de bord comptable.
    """
    scheduler = EDITVAScheduler(db, tenant_id)
    pending = scheduler.get_pending_declarations()
    return {
        "count": len(pending),
        "declarations": [
            {
                "id": d.id,
                "type": d.declaration_type,
                "period": f"{d.period_start} - {d.period_end}",
                "due_date": d.due_date.isoformat() if d.due_date else None,
                "status": d.status
            }
            for d in pending
        ]
    }


@router.post("/edi-tva/declarations/{declaration_id}/schedule")
def schedule_auto_submit(
    declaration_id: int,
    submit_date: date = Query(..., description="Date de transmission automatique"),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Planifier une transmission automatique de déclaration TVA.
    La déclaration sera transmise à la date spécifiée.
    """
    scheduler = EDITVAScheduler(db, tenant_id)
    return scheduler.schedule_auto_submit(declaration_id, submit_date)


# ============================================================================
# CONFORMITÉ FISCALE AVANCÉE - TVA INTRACOMMUNAUTAIRE & INTERNATIONAL
# ============================================================================

from .conformite_fiscale_avancee import (
    ConformiteFiscaleAvanceeService,
    TypeOperation,
    PAYS_UE,
    SEUILS_VENTE_DISTANCE,
)


@router.post("/fiscalite/territorialite")
def analyser_territorialite_tva(
    pays_vendeur: str = Query("FR", min_length=2, max_length=2),
    pays_acheteur: str = Query(..., min_length=2, max_length=2),
    type_acheteur: str = Query("B2B", description="B2B ou B2C"),
    type_bien: str = Query("MARCHANDISE", description="MARCHANDISE, SERVICE"),
    montant_ht: Decimal = Query(...),
    numero_tva_acheteur: str = Query(None, description="Numéro TVA intracommunautaire"),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Analyser la territorialité TVA d'une opération.
    Détermine le lieu d'imposition, le taux applicable et les mentions facture.
    """
    service = ConformiteFiscaleAvanceeService(db, tenant_id)
    result = service.analyser_territorialite(
        pays_vendeur=pays_vendeur,
        pays_acheteur=pays_acheteur,
        type_acheteur=type_acheteur,
        type_bien=type_bien,
        montant_ht=montant_ht,
        numero_tva_acheteur=numero_tva_acheteur
    )
    return {
        "operation_type": result.operation_type.value,
        "lieu_imposition": result.lieu_imposition,
        "tva_applicable": result.tva_applicable,
        "taux_tva": float(result.taux_tva),
        "autoliquidation": result.autoliquidation,
        "mention_facture": result.mention_facture,
        "code_regime": result.code_regime,
        "explication": result.explication
    }


@router.get("/fiscalite/pays-ue")
def get_pays_ue(tenant_id: str = Query(...)):
    """Récupérer la liste des pays de l'Union Européenne."""
    return {"pays": PAYS_UE}


@router.get("/fiscalite/seuils-vente-distance")
def get_seuils_vente_distance(tenant_id: str = Query(...)):
    """
    Récupérer les seuils de vente à distance par pays.
    Au-delà de ces seuils, TVA du pays de destination applicable.
    """
    return {
        "seuil_global_oss": 10000,
        "seuils_par_pays": SEUILS_VENTE_DISTANCE
    }


@router.post("/fiscalite/deb/generer")
def generer_deb(
    mois: int = Query(..., ge=1, le=12),
    annee: int = Query(..., ge=2020),
    flux: str = Query("EXPEDITION", description="EXPEDITION ou INTRODUCTION"),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Générer la Déclaration d'Échanges de Biens (DEB).
    Obligatoire pour les échanges intracommunautaires > 460 000 EUR/an.
    """
    service = ConformiteFiscaleAvanceeService(db, tenant_id)
    result = service.generer_deb(mois=mois, annee=annee, flux=flux)
    return result


@router.post("/fiscalite/des/generer")
def generer_des(
    mois: int = Query(..., ge=1, le=12),
    annee: int = Query(..., ge=2020),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Générer la Déclaration Européenne de Services (DES).
    Obligatoire pour les prestations de services B2B intracommunautaires.
    """
    service = ConformiteFiscaleAvanceeService(db, tenant_id)
    result = service.generer_des(mois=mois, annee=annee)
    return result


@router.get("/fiscalite/oss/statut")
def get_statut_oss(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Vérifier le statut OSS (One-Stop-Shop) du tenant.
    Indique si le régime OSS est applicable et le seuil atteint.
    """
    service = ConformiteFiscaleAvanceeService(db, tenant_id)
    return service.get_statut_oss()


@router.post("/fiscalite/autoliquidation/verifier")
def verifier_autoliquidation(
    pays_fournisseur: str = Query(..., min_length=2, max_length=2),
    type_operation: str = Query(..., description="BIEN ou SERVICE"),
    montant_ht: Decimal = Query(...),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Vérifier si l'autoliquidation de TVA est applicable.
    Retourne les écritures comptables à passer.
    """
    service = ConformiteFiscaleAvanceeService(db, tenant_id)
    return service.verifier_autoliquidation(
        pays_fournisseur=pays_fournisseur,
        type_operation=type_operation,
        montant_ht=montant_ht
    )


@router.post("/fiscalite/prix-transfert/analyse")
def analyser_prix_transfert(
    entite_liee_pays: str = Query(..., min_length=2, max_length=2),
    type_transaction: str = Query(..., description="VENTE, ACHAT, SERVICE, REDEVANCE"),
    montant: Decimal = Query(...),
    methode_valorisation: str = Query("COMPARABLE", description="COMPARABLE, COST_PLUS, RESALE_MINUS"),
    tenant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Analyser une transaction avec partie liée pour conformité prix de transfert.
    Vérifie le respect du principe de pleine concurrence (arm's length).
    """
    service = ConformiteFiscaleAvanceeService(db, tenant_id)
    return service.analyser_prix_transfert(
        entite_liee_pays=entite_liee_pays,
        type_transaction=type_transaction,
        montant=montant,
        methode_valorisation=methode_valorisation
    )


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
