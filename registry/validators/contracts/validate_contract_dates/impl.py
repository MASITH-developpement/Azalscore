"""
Implémentation du sous-programme : validate_contract_dates

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date, timedelta


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
    Valide les dates d'un contrat.

    Vérifie:
    - Cohérence des dates (début < fin)
    - Date de signature
    - Durée du contrat

    Args:
        inputs: {
            "start": string/date,  # Date de début
            "end": string/date,  # Date de fin (optionnel)
            "signed_at": string/date,  # Date de signature (optionnel)
            "min_duration_days": number,  # Durée minimale (optionnel)
            "max_duration_days": number,  # Durée maximale (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si dates valides
            "start_date": string,  # Date de début (ISO)
            "end_date": string,  # Date de fin (ISO)
            "duration_days": number,  # Durée en jours
            "duration_months": number,  # Durée en mois
            "is_active": boolean,  # Contrat actif aujourd'hui
            "is_expired": boolean,  # Contrat expiré
            "days_until_start": number,  # Jours avant début
            "days_until_end": number,  # Jours avant fin
            "error": string,  # Message d'erreur si invalide
        }
    """
    start_input = inputs.get("start")
    end_input = inputs.get("end")
    signed_at_input = inputs.get("signed_at")
    min_duration = inputs.get("min_duration_days")
    max_duration = inputs.get("max_duration_days")

    # Date de début requise
    if start_input is None:
        return {
            "is_valid": False,
            "start_date": None,
            "end_date": None,
            "duration_days": None,
            "duration_months": None,
            "is_active": None,
            "is_expired": None,
            "days_until_start": None,
            "days_until_end": None,
            "error": "Date de début requise"
        }

    # Parse des dates
    start_date = _parse_date(start_input)
    if start_date is None:
        return {
            "is_valid": False,
            "start_date": None,
            "end_date": None,
            "duration_days": None,
            "duration_months": None,
            "is_active": None,
            "is_expired": None,
            "days_until_start": None,
            "days_until_end": None,
            "error": "Format de date de début invalide"
        }

    end_date = _parse_date(end_input) if end_input else None
    signed_at = _parse_date(signed_at_input) if signed_at_input else None

    # Vérification signature avant début
    if signed_at and signed_at > start_date:
        return {
            "is_valid": False,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
            "duration_days": None,
            "duration_months": None,
            "is_active": None,
            "is_expired": None,
            "days_until_start": None,
            "days_until_end": None,
            "error": "La signature doit être antérieure ou égale à la date de début"
        }

    # Vérification cohérence dates
    if end_date and end_date <= start_date:
        return {
            "is_valid": False,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "duration_days": None,
            "duration_months": None,
            "is_active": None,
            "is_expired": None,
            "days_until_start": None,
            "days_until_end": None,
            "error": "La date de fin doit être postérieure à la date de début"
        }

    # Calcul de la durée
    duration_days = None
    duration_months = None
    if end_date:
        duration_days = (end_date - start_date).days
        duration_months = round(duration_days / 30, 1)

        # Vérification durée minimale
        if min_duration and duration_days < min_duration:
            return {
                "is_valid": False,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "duration_days": duration_days,
                "duration_months": duration_months,
                "is_active": None,
                "is_expired": None,
                "days_until_start": None,
                "days_until_end": None,
                "error": f"Durée minimale: {min_duration} jours"
            }

        # Vérification durée maximale
        if max_duration and duration_days > max_duration:
            return {
                "is_valid": False,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "duration_days": duration_days,
                "duration_months": duration_months,
                "is_active": None,
                "is_expired": None,
                "days_until_start": None,
                "days_until_end": None,
                "error": f"Durée maximale: {max_duration} jours"
            }

    # Calculs relatifs à aujourd'hui
    today = date.today()
    days_until_start = (start_date - today).days
    days_until_end = (end_date - today).days if end_date else None

    is_active = start_date <= today and (end_date is None or today <= end_date)
    is_expired = end_date is not None and today > end_date

    return {
        "is_valid": True,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
        "duration_days": duration_days,
        "duration_months": duration_months,
        "is_active": is_active,
        "is_expired": is_expired,
        "days_until_start": days_until_start,
        "days_until_end": days_until_end,
        "error": None
    }
