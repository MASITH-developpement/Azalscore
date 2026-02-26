"""
AZALS - API Fiscalité
Gestion des déclarations fiscales et échéances (TVA, IS, taxes diverses)
Pays-agnostique : principes généraux applicables multi-juridictions
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.dependencies import get_db, get_tenant_id
from app.core.models import User

router = APIRouter(prefix="/tax", tags=["tax"])


@router.get("/status")
async def get_tax_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Retourne le statut fiscal global

    SÉCURITÉ: Authentification requise.

    États:
    - 🟢 : Toutes déclarations à jour, prochaine échéance > 15j
    - 🟠 : Échéance proche (< 15j) ou information manquante
    - 🔴 : Retard de déclaration ou non-conformité

    Retour:
    {
        "status": "🟢"|"🟠"|"🔴",
        "next_deadline": "2026-02-15",
        "next_deadline_type": "TVA",
        "days_until_deadline": 14,
        "vat_status": "À jour",
        "corporate_tax_status": "À jour",
        "last_vat_declaration": "2025-12-20",
        "last_corporate_tax_declaration": "2025-03-15"
    }
    """

    # Simulation réaliste basée sur date actuelle
    today = datetime.now().date()

    # Échéance TVA mensuelle (15 du mois suivant)
    next_month = today.replace(day=1) + timedelta(days=32)
    vat_deadline = next_month.replace(day=15)
    days_until = (vat_deadline - today).days

    # Dernière déclaration TVA (mois dernier)
    last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=20)

    # IS : déclaration annuelle (15 mars + 4 mois après clôture)
    # Simplifié : 15 avril N pour exercice N-1
    current_year = today.year
    corporate_tax_deadline = datetime(current_year, 4, 15).date()
    if today > corporate_tax_deadline:
        corporate_tax_deadline = datetime(current_year + 1, 4, 15).date()

    last_corporate_tax = datetime(current_year - 1, 3, 15).date()

    # Déterminer le statut
    if days_until < 0:
        status = "🔴"  # Retard
        vat_status = "En retard"
    elif days_until <= 15:
        status = "🟠"  # Échéance proche
        vat_status = "Échéance proche"
    else:
        status = "🟢"  # À jour
        vat_status = "À jour"

    # Vérifier IS
    days_until_corporate = (corporate_tax_deadline - today).days
    if days_until_corporate < 0:
        status = "🔴"
        corporate_tax_status = "En retard"
    elif days_until_corporate <= 30:
        if status != "🔴":
            status = "🟠"
        corporate_tax_status = "Échéance proche"
    else:
        corporate_tax_status = "À jour"

    # Déterminer prochaine échéance prioritaire
    if days_until < days_until_corporate:
        next_deadline = vat_deadline
        next_deadline_type = "TVA"
        days_until_next = days_until
    else:
        next_deadline = corporate_tax_deadline
        next_deadline_type = "IS"
        days_until_next = days_until_corporate

    return {
        "status": status,
        "next_deadline": next_deadline.isoformat(),
        "next_deadline_type": next_deadline_type,
        "days_until_deadline": days_until_next,
        "vat_status": vat_status,
        "corporate_tax_status": corporate_tax_status,
        "last_vat_declaration": last_month.isoformat(),
        "last_corporate_tax_declaration": last_corporate_tax.isoformat()
    }
