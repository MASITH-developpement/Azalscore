"""
Implémentation du sous-programme : validate_renewal_notice

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 10+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date, timedelta


# Délais de préavis standards (en jours)
STANDARD_NOTICE_PERIODS = {
    "monthly": 30,
    "quarterly": 30,
    "annual": 60,
    "biannual": 90,
}


def _parse_date(date_value) -> date | None:
    """Parse une date depuis différents formats."""
    if date_value is None:
        return None
    if isinstance(date_value, date) and not isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, str):
        date_str = date_value.strip()
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            parts = date_str.split('-')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day)
    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide le préavis de renouvellement/résiliation d'un contrat.

    Vérifie si le préavis peut encore être donné avant la date limite.

    Args:
        inputs: {
            "end_date": string/date,  # Date de fin du contrat
            "notice_days": number,  # Délai de préavis requis (optionnel)
            "contract_type": string,  # Type de contrat (optionnel)
            "current_date": string/date,  # Date de référence (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si préavis peut être envoyé
            "end_date": string,  # Date de fin (ISO)
            "notice_deadline": string,  # Date limite de préavis
            "days_until_deadline": number,  # Jours avant deadline
            "can_give_notice": boolean,  # Préavis encore possible
            "notice_days_required": number,  # Délai requis
            "recommended_action": string,  # Action recommandée
            "error": string,  # Message d'erreur si invalide
        }
    """
    end_date_input = inputs.get("end_date")
    notice_days = inputs.get("notice_days")
    contract_type = inputs.get("contract_type", "annual")
    current_date_input = inputs.get("current_date")

    # Date de fin requise
    if end_date_input is None:
        return {
            "is_valid": False,
            "end_date": None,
            "notice_deadline": None,
            "days_until_deadline": None,
            "can_give_notice": None,
            "notice_days_required": None,
            "recommended_action": None,
            "error": "Date de fin requise"
        }

    # Parse date de fin
    end_date = _parse_date(end_date_input)
    if end_date is None:
        return {
            "is_valid": False,
            "end_date": None,
            "notice_deadline": None,
            "days_until_deadline": None,
            "can_give_notice": None,
            "notice_days_required": None,
            "recommended_action": None,
            "error": "Format de date de fin invalide"
        }

    # Date de référence
    if current_date_input:
        current_date = _parse_date(current_date_input)
        if current_date is None:
            current_date = date.today()
    else:
        current_date = date.today()

    # Déterminer le délai de préavis
    if notice_days is None:
        notice_days = STANDARD_NOTICE_PERIODS.get(contract_type.lower(), 30)

    # Calculer la date limite de préavis
    notice_deadline = end_date - timedelta(days=notice_days)
    days_until_deadline = (notice_deadline - current_date).days
    days_until_end = (end_date - current_date).days

    # Vérifier si préavis possible
    can_give_notice = current_date <= notice_deadline

    # Déterminer l'action recommandée
    if can_give_notice:
        if days_until_deadline <= 7:
            recommended_action = "URGENT: Envoyer le préavis immédiatement"
        elif days_until_deadline <= 30:
            recommended_action = "Planifier l'envoi du préavis prochainement"
        else:
            recommended_action = "Préavis peut être envoyé dans les temps"
    else:
        if days_until_end > 0:
            recommended_action = "Préavis tardif: contacter le prestataire"
        else:
            recommended_action = "Contrat déjà expiré"

    return {
        "is_valid": True,
        "end_date": end_date.strftime("%Y-%m-%d"),
        "notice_deadline": notice_deadline.strftime("%Y-%m-%d"),
        "days_until_deadline": days_until_deadline,
        "can_give_notice": can_give_notice,
        "notice_days_required": notice_days,
        "recommended_action": recommended_action,
        "error": None
    }
