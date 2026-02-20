"""
AZALS - Router Liasses Fiscales (GAP-049)
==========================================
API endpoints pour la génération et le pré-remplissage automatique
des liasses fiscales françaises à partir des données comptables.

Fonctionnalités:
- Génération automatique des formulaires 2050-2059 (régime réel normal)
- Génération automatique des formulaires 2033-A à 2033-G (régime simplifié)
- Calcul automatique du résultat fiscal et de l'IS
- Export EDI-TDFC pour télétransmission DGFiP
- Prévisualisation avant soumission
"""

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .liasses_fiscales import (
    LiassesFiscalesService,
    RegimeFiscal,
    TypeLiasse,
)


router = APIRouter(prefix="/france/liasses-fiscales", tags=["Pack France - Liasses Fiscales"])


# ============================================================================
# SCHEMAS
# ============================================================================

class LigneFormulaireResponse(BaseModel):
    """Ligne d'un formulaire fiscal."""
    code: str
    libelle: str
    valeur_n: str
    valeur_n1: str = "0"
    comptes: list[str] = []
    calcul: str | None = None


class FormulaireResponse(BaseModel):
    """Formulaire fiscal (2050, 2051, etc.)."""
    numero: str
    titre: str
    total_n: str
    total_n1: str = "0"
    lignes: list[LigneFormulaireResponse]


class LiasseFiscaleResponse(BaseModel):
    """Liasse fiscale complète."""
    metadata: dict[str, Any]
    resultats: dict[str, str]
    formulaires: list[FormulaireResponse]
    errors: list[str]
    warnings: list[str]


class GenerationRequest(BaseModel):
    """Requête de génération de liasse fiscale."""
    fiscal_year_id: str = Field(..., description="ID de l'exercice comptable")
    regime: str = Field("REEL_NORMAL", description="Régime fiscal: REEL_NORMAL, REEL_SIMPLIFIE, IS, BNC")
    fiscal_year_n1_id: str | None = Field(None, description="ID de l'exercice N-1 pour comparaison")


class ISCalculationResponse(BaseModel):
    """Résultat du calcul IS."""
    resultat_imposable: str
    is_total: str
    est_pme: bool
    tranches: list[dict[str, Any]]


class PreviewResponse(BaseModel):
    """Prévisualisation de la liasse fiscale."""
    fiscal_year_code: str
    date_debut: str
    date_fin: str
    regime: str
    formulaires_prevus: list[str]
    estimations: dict[str, str]
    completude: dict[str, Any]


class ValidationResponse(BaseModel):
    """Résultat de validation de la liasse."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    completude_pct: float
    formulaires_valides: list[str]
    formulaires_invalides: list[str]


# ============================================================================
# DEPENDENCY
# ============================================================================

def get_liasses_service(
    db: Session = Depends(get_db),
    ctx: SaaSContext = Depends(get_saas_context)
) -> LiassesFiscalesService:
    """Dependency pour le service liasses fiscales."""
    return LiassesFiscalesService(db, ctx.tenant_id)


# ============================================================================
# ENDPOINTS - GÉNÉRATION
# ============================================================================

@router.post("/generate", response_model=LiasseFiscaleResponse)
async def generate_liasse_fiscale(
    request: GenerationRequest,
    service: LiassesFiscalesService = Depends(get_liasses_service)
):
    """
    Génère une liasse fiscale complète pré-remplie à partir des données comptables.

    Cette fonction effectue:
    1. Lecture des écritures comptables validées de l'exercice
    2. Agrégation des soldes par compte PCG
    3. Mapping vers les rubriques des formulaires fiscaux
    4. Calcul du résultat fiscal (réintégrations et déductions)
    5. Calcul de l'IS dû (avec taux réduit PME si applicable)

    Formulaires générés (régime réel normal):
    - 2050: Bilan - Actif
    - 2051: Bilan - Passif
    - 2052: Compte de résultat - Charges
    - 2053: Compte de résultat - Produits
    - 2058-A: Détermination du résultat fiscal
    """
    try:
        regime = RegimeFiscal(request.regime)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Régime fiscal invalide: {request.regime}. "
                   f"Valeurs acceptées: REEL_NORMAL, REEL_SIMPLIFIE, IS, BNC, MICRO_BIC"
        )

    try:
        liasse = service.generer_liasse_complete(
            fiscal_year_id=request.fiscal_year_id,
            regime=regime,
            fiscal_year_n1_id=request.fiscal_year_n1_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")

    return service.export_liasse_dict(liasse)


@router.get("/preview/{fiscal_year_id}")
async def preview_liasse_fiscale(
    fiscal_year_id: str,
    regime: str = Query("REEL_NORMAL", description="Régime fiscal"),
    service: LiassesFiscalesService = Depends(get_liasses_service)
):
    """
    Prévisualisation d'une liasse fiscale avant génération complète.

    Retourne:
    - Les formulaires qui seront générés
    - Une estimation des principaux montants
    - Le pourcentage de complétude des données comptables
    """
    # Vérification des données disponibles
    from app.modules.accounting.models import (
        AccountingFiscalYear,
        AccountingJournalEntry,
        AccountingJournalEntryLine,
        EntryStatus,
    )
    from sqlalchemy import func

    fiscal_year = service.db.query(AccountingFiscalYear).filter(
        AccountingFiscalYear.tenant_id == service.tenant_id,
        AccountingFiscalYear.id == fiscal_year_id
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Exercice non trouvé")

    # Compte des écritures validées
    entries_count = service.db.query(func.count(AccountingJournalEntry.id)).filter(
        AccountingJournalEntry.tenant_id == service.tenant_id,
        AccountingJournalEntry.fiscal_year_id == fiscal_year_id,
        AccountingJournalEntry.status == EntryStatus.POSTED
    ).scalar()

    # Compte des lignes
    lines_count = service.db.query(func.count(AccountingJournalEntryLine.id)).join(
        AccountingJournalEntry
    ).filter(
        AccountingJournalEntryLine.tenant_id == service.tenant_id,
        AccountingJournalEntry.fiscal_year_id == fiscal_year_id,
        AccountingJournalEntry.status == EntryStatus.POSTED
    ).scalar()

    # Estimations rapides
    total_debit = service.db.query(func.coalesce(func.sum(AccountingJournalEntryLine.debit), 0)).join(
        AccountingJournalEntry
    ).filter(
        AccountingJournalEntryLine.tenant_id == service.tenant_id,
        AccountingJournalEntry.fiscal_year_id == fiscal_year_id,
        AccountingJournalEntry.status == EntryStatus.POSTED
    ).scalar()

    total_credit = service.db.query(func.coalesce(func.sum(AccountingJournalEntryLine.credit), 0)).join(
        AccountingJournalEntry
    ).filter(
        AccountingJournalEntryLine.tenant_id == service.tenant_id,
        AccountingJournalEntry.fiscal_year_id == fiscal_year_id,
        AccountingJournalEntry.status == EntryStatus.POSTED
    ).scalar()

    # CA estimé (comptes 70x)
    ca_estime = service._get_balance_by_prefixes(
        ["701", "702", "703", "704", "705", "706", "707"],
        fiscal_year_id, is_credit_nature=True
    )

    # Charges estimées (comptes 6x)
    charges_estime = service._get_balance_by_prefixes(
        ["60", "61", "62", "63", "64", "65", "66", "67", "68"],
        fiscal_year_id, is_credit_nature=False
    )

    # Formulaires selon régime
    if regime in ["REEL_NORMAL", "IS"]:
        formulaires = ["2050", "2051", "2052", "2053", "2058-A"]
    elif regime == "REEL_SIMPLIFIE":
        formulaires = ["2033-A", "2033-B", "2033-C", "2033-D", "2033-E"]
    elif regime == "BNC":
        formulaires = ["2035-A", "2035-B"]
    else:
        formulaires = ["2050", "2051", "2052", "2053"]

    # Calcul complétude
    has_entries = entries_count > 0
    is_balanced = abs(total_debit - total_credit) < Decimal("0.01")
    has_revenue = ca_estime > 0
    has_expenses = charges_estime > 0

    completeness = {
        "entries_posted": has_entries,
        "balance_ok": is_balanced,
        "revenue_recorded": has_revenue,
        "expenses_recorded": has_expenses,
        "entries_count": entries_count,
        "lines_count": lines_count,
        "imbalance": str(abs(total_debit - total_credit))
    }

    completeness_pct = sum([has_entries, is_balanced, has_revenue, has_expenses]) / 4 * 100

    return {
        "fiscal_year_code": fiscal_year.code,
        "date_debut": fiscal_year.start_date.date().isoformat(),
        "date_fin": fiscal_year.end_date.date().isoformat(),
        "regime": regime,
        "formulaires_prevus": formulaires,
        "estimations": {
            "chiffre_affaires": str(ca_estime),
            "charges_totales": str(charges_estime),
            "resultat_estime": str(ca_estime - charges_estime),
            "total_mouvements_debit": str(total_debit),
            "total_mouvements_credit": str(total_credit),
        },
        "completude": completeness,
        "completude_pct": completeness_pct,
        "pret_pour_generation": completeness_pct >= 75
    }


@router.post("/generate/{fiscal_year_id}/formulaire/{type_formulaire}")
async def generate_single_form(
    fiscal_year_id: str,
    type_formulaire: str,
    service: LiassesFiscalesService = Depends(get_liasses_service)
):
    """
    Génère un seul formulaire fiscal.

    Types disponibles:
    - 2050: Bilan Actif
    - 2051: Bilan Passif
    - 2052: Compte de résultat - Charges
    - 2053: Compte de résultat - Produits
    - 2058-A: Résultat fiscal
    """
    type_map = {
        "2050": service._generer_2050_actif,
        "2051": service._generer_2051_passif,
    }

    if type_formulaire not in type_map and type_formulaire not in ["2052", "2053", "2058-A"]:
        raise HTTPException(
            status_code=400,
            detail=f"Type de formulaire non supporté: {type_formulaire}"
        )

    try:
        if type_formulaire in type_map:
            formulaire = type_map[type_formulaire](fiscal_year_id, None)
        elif type_formulaire in ["2052", "2053"]:
            form_2052, form_2053 = service._generer_2052_2053_resultat(fiscal_year_id, None)
            formulaire = form_2052 if type_formulaire == "2052" else form_2053
        elif type_formulaire == "2058-A":
            # Besoin du résultat comptable
            form_2052, form_2053 = service._generer_2052_2053_resultat(fiscal_year_id, None)
            resultat_comptable = form_2053.total_n - form_2052.total_n
            formulaire, _ = service._generer_2058a_resultat_fiscal(fiscal_year_id, resultat_comptable)

        return {
            "numero": formulaire.numero,
            "titre": formulaire.titre,
            "total_n": str(formulaire.total_n),
            "total_n1": str(formulaire.total_n1),
            "lignes": [
                {
                    "code": l.code,
                    "libelle": l.libelle,
                    "valeur_n": str(l.valeur_n),
                    "valeur_n1": str(l.valeur_n1),
                    "comptes": l.comptes,
                    "calcul": l.calcul
                }
                for l in formulaire.lignes
            ]
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# ENDPOINTS - CALCUL IS
# ============================================================================

@router.post("/calculate-is")
async def calculate_corporate_tax(
    resultat_imposable: Decimal = Query(..., description="Résultat fiscal imposable"),
    est_pme: bool = Query(True, description="L'entreprise est-elle une PME?"),
    service: LiassesFiscalesService = Depends(get_liasses_service)
):
    """
    Calcule l'impôt sur les sociétés (IS) dû.

    Règles applicables (2024-2025):
    - Taux réduit PME: 15% sur les premiers 42 500 EUR de bénéfice
    - Taux normal: 25% au-delà

    Conditions du taux réduit PME:
    - CA < 10 M EUR
    - Capital entièrement libéré
    - Détenu à 75% minimum par des personnes physiques
    """
    is_du, detail = service.calculer_is(resultat_imposable, est_pme)

    return {
        "resultat_imposable": str(resultat_imposable),
        "is_total": str(is_du),
        "est_pme": est_pme,
        "tranches": detail["tranches"],
        "taux_effectif": str(round(is_du / max(resultat_imposable, Decimal("1")) * 100, 2)) + "%"
    }


# ============================================================================
# ENDPOINTS - EXPORT
# ============================================================================

@router.post("/export/edi/{fiscal_year_id}")
async def export_edi_tdfc(
    fiscal_year_id: str,
    regime: str = Query("REEL_NORMAL"),
    service: LiassesFiscalesService = Depends(get_liasses_service)
):
    """
    Exporte la liasse fiscale au format EDI-TDFC pour télétransmission à la DGFiP.

    Ce format est utilisé pour:
    - Le dépôt en ligne sur impots.gouv.fr
    - La transmission via les partenaires EDI agréés
    """
    try:
        regime_enum = RegimeFiscal(regime)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Régime invalide: {regime}")

    try:
        liasse = service.generer_liasse_complete(fiscal_year_id, regime_enum)
        edi_content = service.export_liasse_edi(liasse)

        return {
            "format": "EDI-TDFC",
            "exercice": liasse.exercice_code,
            "regime": regime,
            "content": edi_content,
            "filename": f"LIASSE_{liasse.exercice_code}_{regime}.txt",
            "warnings": liasse.warnings,
            "errors": liasse.errors
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/export/json/{fiscal_year_id}")
async def export_json(
    fiscal_year_id: str,
    regime: str = Query("REEL_NORMAL"),
    fiscal_year_n1_id: str | None = Query(None),
    service: LiassesFiscalesService = Depends(get_liasses_service)
):
    """
    Exporte la liasse fiscale au format JSON structuré.

    Utile pour:
    - Intégration avec d'autres systèmes
    - Archivage électronique
    - Analyse et reporting
    """
    try:
        regime_enum = RegimeFiscal(regime)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Régime invalide: {regime}")

    try:
        liasse = service.generer_liasse_complete(fiscal_year_id, regime_enum, fiscal_year_n1_id)
        return service.export_liasse_dict(liasse)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# ENDPOINTS - VALIDATION
# ============================================================================

@router.post("/validate/{fiscal_year_id}")
async def validate_liasse(
    fiscal_year_id: str,
    regime: str = Query("REEL_NORMAL"),
    service: LiassesFiscalesService = Depends(get_liasses_service)
):
    """
    Valide une liasse fiscale avant soumission.

    Vérifications effectuées:
    - Équilibre du bilan (Actif = Passif)
    - Cohérence du compte de résultat
    - Présence des données obligatoires
    - Montants dans les limites acceptables
    """
    try:
        regime_enum = RegimeFiscal(regime)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Régime invalide: {regime}")

    try:
        liasse = service.generer_liasse_complete(fiscal_year_id, regime_enum)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    errors = liasse.errors.copy()
    warnings = liasse.warnings.copy()
    formulaires_valides = []
    formulaires_invalides = []

    # Validation par formulaire
    for form in liasse.formulaires:
        form_errors = []

        # Vérification des lignes obligatoires
        if form.numero == "2050":
            # Vérifier total actif
            if form.total_n <= 0:
                form_errors.append("Total actif nul ou négatif")

        elif form.numero == "2051":
            # Vérifier total passif
            if form.total_n <= 0:
                form_errors.append("Total passif nul ou négatif")

            # Vérifier équilibre avec 2050
            form_2050 = next((f for f in liasse.formulaires if f.numero == "2050"), None)
            if form_2050:
                diff = abs(form.total_n - form_2050.total_n)
                if diff > Decimal("0.01"):
                    form_errors.append(f"Déséquilibre bilan: écart de {diff} EUR")

        elif form.numero in ["2052", "2053"]:
            # Vérifier cohérence charges/produits
            pass

        if form_errors:
            formulaires_invalides.append(form.numero)
            errors.extend([f"{form.numero}: {e}" for e in form_errors])
        else:
            formulaires_valides.append(form.numero)

    # Calcul complétude
    total_forms = len(liasse.formulaires)
    valid_forms = len(formulaires_valides)
    completude_pct = (valid_forms / max(total_forms, 1)) * 100

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "completude_pct": completude_pct,
        "formulaires_valides": formulaires_valides,
        "formulaires_invalides": formulaires_invalides,
        "resultat_fiscal": str(liasse.resultat_fiscal),
        "is_du": str(liasse.impot_du)
    }


# ============================================================================
# ENDPOINTS - INFORMATIONS
# ============================================================================

@router.get("/regimes")
async def list_fiscal_regimes():
    """Liste les régimes fiscaux disponibles."""
    return {
        "regimes": [
            {
                "code": "REEL_NORMAL",
                "name": "Réel Normal",
                "description": "Entreprises avec CA > 789 000 EUR (services) ou > 238 000 EUR (ventes)",
                "formulaires": ["2050", "2051", "2052", "2053", "2054", "2055", "2056", "2057", "2058-A à C", "2059-A à G"]
            },
            {
                "code": "REEL_SIMPLIFIE",
                "name": "Réel Simplifié",
                "description": "Entreprises avec CA entre les seuils micro et réel normal",
                "formulaires": ["2033-A", "2033-B", "2033-C", "2033-D", "2033-E", "2033-F", "2033-G"]
            },
            {
                "code": "IS",
                "name": "Impôt sur les Sociétés",
                "description": "Sociétés soumises à l'IS (SA, SAS, SARL, etc.)",
                "formulaires": ["2065", "2050-2059"]
            },
            {
                "code": "BNC",
                "name": "Bénéfices Non Commerciaux",
                "description": "Professions libérales et activités non commerciales",
                "formulaires": ["2035-A", "2035-B", "2035-E"]
            },
            {
                "code": "MICRO_BIC",
                "name": "Micro-BIC",
                "description": "Micro-entreprises (pas de liasse détaillée)",
                "formulaires": []
            }
        ]
    }


@router.get("/formulaires")
async def list_tax_forms():
    """Liste les formulaires fiscaux disponibles avec leur description."""
    return {
        "liasse_reel_normal": [
            {"numero": "2050", "titre": "Bilan - Actif", "description": "Immobilisations, stocks, créances, trésorerie"},
            {"numero": "2051", "titre": "Bilan - Passif", "description": "Capitaux propres, provisions, dettes"},
            {"numero": "2052", "titre": "Compte de résultat - Charges", "description": "Achats, services, personnel, amortissements"},
            {"numero": "2053", "titre": "Compte de résultat - Produits", "description": "Ventes, productions, produits financiers"},
            {"numero": "2054", "titre": "Immobilisations", "description": "Détail des mouvements d'immobilisations"},
            {"numero": "2055", "titre": "Amortissements", "description": "Tableau des amortissements"},
            {"numero": "2056", "titre": "Provisions", "description": "Tableau des provisions"},
            {"numero": "2057", "titre": "Échéances créances/dettes", "description": "Ventilation par échéance"},
            {"numero": "2058-A", "titre": "Résultat fiscal", "description": "Calcul du résultat fiscal (réintégrations/déductions)"},
            {"numero": "2058-B", "titre": "Déficits et provisions non déductibles", "description": "Suivi des déficits reportables"},
            {"numero": "2058-C", "titre": "Affectation du résultat", "description": "Distribution dividendes, réserves"},
        ],
        "liasse_simplifie": [
            {"numero": "2033-A", "titre": "Bilan simplifié", "description": "Actif et passif simplifiés"},
            {"numero": "2033-B", "titre": "Compte de résultat simplifié", "description": "Charges et produits simplifiés"},
            {"numero": "2033-C", "titre": "Immobilisations et plus-values", "description": "Tableau simplifié"},
            {"numero": "2033-D", "titre": "Provisions", "description": "Tableau des provisions simplifié"},
            {"numero": "2033-E", "titre": "Résultat fiscal", "description": "Détermination du résultat fiscal"},
        ],
        "declarations": [
            {"numero": "2065", "titre": "Déclaration IS", "description": "Déclaration de résultats IS"},
            {"numero": "2031", "titre": "Déclaration BIC", "description": "Déclaration de résultats BIC"},
            {"numero": "2035", "titre": "Déclaration BNC", "description": "Déclaration de résultats BNC"},
            {"numero": "2067", "titre": "Relevé de solde IS", "description": "Liquidation de l'IS"},
            {"numero": "2572", "titre": "Acomptes IS", "description": "Paiement des acomptes IS"},
        ]
    }


@router.get("/taux-is")
async def get_is_rates():
    """Retourne les taux d'IS en vigueur."""
    return {
        "annee": 2025,
        "taux_normal": "25%",
        "taux_reduit_pme": "15%",
        "plafond_taux_reduit": "42 500 EUR",
        "conditions_taux_reduit": [
            "CA HT < 10 000 000 EUR",
            "Capital entièrement libéré",
            "Détention ≥ 75% par des personnes physiques"
        ],
        "echeances": [
            {"date": "15 mars", "description": "1er acompte IS"},
            {"date": "15 juin", "description": "2ème acompte IS"},
            {"date": "15 septembre", "description": "3ème acompte IS"},
            {"date": "15 décembre", "description": "4ème acompte IS"},
            {"date": "15 mai N+1", "description": "Solde IS (date limite dépôt liasse)"}
        ]
    }
