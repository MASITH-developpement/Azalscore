"""
AZALS - API Juridique & Structurel
Gestion conformité statutaire, contrats, risques juridiques
Responsabilité dirigeant - Indicateurs gouvernance
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.dependencies import get_db, get_tenant_id
from app.core.models import User

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/status")
async def get_legal_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Retourne le statut juridique/structurel global

    SÉCURITÉ: Authentification requise.

    États:
    - 🟢 : Conformité à jour, pas de risque identifié
    - 🟠 : Élément à surveiller (statuts à revoir, contrat à renouveler)
    - 🔴 : Non-conformité avérée ou risque juridique critique

    Retour:
    {
        "status": "🟢"|"🟠"|"🔴",
        "statutory_compliance": "À jour"|"À revoir"|"Non conforme",
        "last_statutory_review": "2025-06-15",
        "sensitive_contracts_count": 3,
        "expiring_contracts_soon": 1,
        "identified_risks": 0,
        "legal_form": "SAS"|"SARL"|etc,
        "registration_status": "Valide"
    }
    """

    # Simulation réaliste basée sur date actuelle
    today = datetime.now().date()

    # Dernière révision statutaire (obligatoire annuellement en bonne pratique)
    last_review = datetime(2025, 6, 15).date()
    days_since_review = (today - last_review).days
    months_since_review = days_since_review // 30  # Approximation mois

    # Statuts : À revoir si > 18 mois, non conforme si > 36 mois
    if days_since_review > 1095:  # 36 mois
        statutory_compliance = "Non conforme"
    elif days_since_review > 547:  # 18 mois
        statutory_compliance = "À revoir"
    else:
        statutory_compliance = "À jour"

    # Contrats sensibles (baux, fournisseurs critiques, financements)
    sensitive_contracts_count = 3

    # Contrats expirant dans les 90 jours
    expiring_soon = 1

    # Risques identifiés (litiges, contentieux, non-conformité réglementaire)
    identified_risks = 0

    # Forme juridique
    legal_form = "SAS"  # Simulation

    # Immatriculation RCS
    registration_status = "Valide"

    # Déterminer le statut global
    if statutory_compliance == "Non conforme" or identified_risks > 0:
        status = "🔴"  # Critique : responsabilité dirigeant engagée
    elif statutory_compliance == "À revoir" or expiring_soon > 0:
        status = "🟠"  # Attention : éléments à traiter
    else:
        status = "🟢"  # Normal

    return {
        "status": status,
        "statutory_compliance": statutory_compliance,
        "last_statutory_review": last_review.isoformat(),
        "last_statutory_review_months_ago": months_since_review,
        "sensitive_contracts_count": sensitive_contracts_count,
        "expiring_contracts_soon": expiring_soon,
        "identified_risks": identified_risks,
        "legal_form": legal_form,
        "registration_status": registration_status
    }
