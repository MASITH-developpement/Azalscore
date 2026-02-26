"""
AZALS - API Ressources Humaines
Gestion effectif, paie, absences (indicateurs dirigeant uniquement)
Respect strict de la confidentialité - Aucune donnée nominative
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

router = APIRouter(prefix="/hr", tags=["hr"])


@router.get("/status")
async def get_hr_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Retourne le statut RH global (anonymisé)

    SÉCURITÉ: Authentification requise.

    États:
    - 🟢 : Situation sociale normale (paie à jour, pas d'alerte)
    - 🟠 : Tension RH (paie à valider, absence clé imminente)
    - 🔴 : Risque social (paie non versée, non-conformité DSN)

    Retour:
    {
        "status": "🟢"|"🟠"|"🔴",
        "headcount": 12,
        "payroll_status": "Validée"|"À valider"|"En retard",
        "payroll_due_date": "2026-01-31",
        "days_until_payroll": 29,
        "critical_absences": 0,
        "dsn_status": "À jour"|"En retard",
        "last_payroll_date": "2025-12-31"
    }
    """

    # Simulation réaliste basée sur date actuelle
    today = datetime.now().date()

    # Effectif (simulation statique)
    headcount = 12

    # Paie mensuelle : échéance fin du mois
    # Si on est avant le 25, paie du mois en cours "À valider"
    # Si entre 25 et fin du mois, paie "Validée"
    # Si après le 5 du mois suivant, "En retard"

    current_month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    next_month_start = current_month_end + timedelta(days=1)
    next_month_start + timedelta(days=5)  # 5 du mois suivant

    days_until_payroll = (current_month_end - today).days

    # Déterminer statut paie
    if today.day >= 25:
        payroll_status = "Validée"
        last_payroll_date = current_month_end
    elif today.day <= 5 and today.month > 1:
        # Début du mois, paie du mois dernier
        last_month_end = today.replace(day=1) - timedelta(days=1)
        payroll_status = "En retard" if today.day > 5 else "À valider"
        last_payroll_date = last_month_end
    else:
        payroll_status = "À valider"
        last_payroll_date = (today.replace(day=1) - timedelta(days=1))

    # DSN (Déclaration Sociale Nominative) : 5 ou 15 du mois selon effectif
    # Simplifié : 15 du mois pour < 50 salariés
    dsn_deadline_day = 15
    if today.day > dsn_deadline_day:
        # DSN du mois en cours devrait être faite
        dsn_status = "À jour"  # Simulation optimiste
    else:
        dsn_status = "À jour"

    # Absences critiques (simulation : 0 sauf si effectif < 5)
    critical_absences = 0
    if headcount < 5:
        # Petite structure : toute absence est critique
        critical_absences = 1

    # Déterminer le statut global
    if payroll_status == "En retard" or dsn_status == "En retard":
        status = "🔴"  # Risque social critique
    elif payroll_status == "À valider" or critical_absences > 0:
        status = "🟠"  # Tension RH
    else:
        status = "🟢"  # Normal

    return {
        "status": status,
        "headcount": headcount,
        "payroll_status": payroll_status,
        "payroll_due_date": current_month_end.isoformat(),
        "days_until_payroll": days_until_payroll,
        "critical_absences": critical_absences,
        "dsn_status": dsn_status,
        "last_payroll_date": last_payroll_date.isoformat()
    }
