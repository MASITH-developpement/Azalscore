"""
Implémentation du sous-programme : validate_quote_validity

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date, timedelta


# Durées de validité par défaut selon le type de devis
DEFAULT_VALIDITY_DAYS = {
    "standard": 30,       # Devis standard
    "service": 30,        # Devis de service
    "travaux": 90,        # Devis de travaux/BTP
    "projet": 60,         # Devis projet
    "maintenance": 15,    # Devis maintenance urgente
    "urgent": 7,          # Devis urgent
}

# Limites de validité
MIN_VALIDITY_DAYS = 1
MAX_VALIDITY_DAYS = 365  # 1 an maximum


def _parse_date(date_value) -> date | None:
    """
    Parse une date depuis différents formats.

    Formats supportés:
    - date object
    - datetime object
    - string: YYYY-MM-DD, DD/MM/YYYY
    """
    if date_value is None:
        return None

    if isinstance(date_value, date) and not isinstance(date_value, datetime):
        return date_value

    if isinstance(date_value, datetime):
        return date_value.date()

    if isinstance(date_value, str):
        date_str = date_value.strip()

        # Format ISO: YYYY-MM-DD
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            parts = date_str.split('-')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and year >= 1900:
                    return date(year, month, day)

        # Format français: DD/MM/YYYY
        if len(date_str) == 10 and date_str[2] == '/' and date_str[5] == '/':
            parts = date_str.split('/')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and year >= 1900:
                    return date(year, month, day)

    return None


def _format_date(d: date) -> str:
    """Formate une date en ISO (YYYY-MM-DD)."""
    return d.strftime("%Y-%m-%d")


def _calculate_expiry_date(issue_date: date, validity_days: int) -> date:
    """Calcule la date d'expiration."""
    return issue_date + timedelta(days=validity_days)


def _get_status(days_remaining: int) -> str:
    """
    Détermine le statut de validité du devis.

    Returns:
        - "valid": Valide avec marge confortable
        - "expiring_soon": Expire dans moins de 7 jours
        - "expired": Expiré
        - "expired_recently": Expiré depuis moins de 7 jours
        - "expired_long_ago": Expiré depuis plus de 7 jours
    """
    if days_remaining > 7:
        return "valid"
    elif days_remaining > 0:
        return "expiring_soon"
    elif days_remaining == 0:
        return "expiring_today"
    elif days_remaining >= -7:
        return "expired_recently"
    else:
        return "expired_long_ago"


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide la période de validité d'un devis.

    Calcule si le devis est toujours valide à la date courante
    et fournit des informations sur sa validité.

    Args:
        inputs: {
            "issue_date": string/date,  # Date d'émission du devis
            "validity_days": number,  # Durée de validité en jours (optionnel)
            "current_date": string/date,  # Date de référence (optionnel, défaut: aujourd'hui)
            "quote_type": string,  # Type de devis pour validité par défaut (optionnel)
            "expiry_date": string/date,  # Date d'expiration explicite (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si le devis est encore valide
            "issue_date": string,  # Date d'émission (ISO format)
            "expiry_date": string,  # Date d'expiration (ISO format)
            "current_date": string,  # Date de référence (ISO format)
            "validity_days": number,  # Durée de validité
            "days_remaining": number,  # Jours restants (négatif si expiré)
            "days_elapsed": number,  # Jours écoulés depuis l'émission
            "status": string,  # Statut: valid, expiring_soon, expired, etc.
            "percentage_elapsed": number,  # Pourcentage de validité écoulé
            "error": string,  # Message d'erreur si problème
        }
    """
    issue_date_input = inputs.get("issue_date")
    validity_days = inputs.get("validity_days")
    current_date_input = inputs.get("current_date")
    quote_type = inputs.get("quote_type", "standard")
    expiry_date_input = inputs.get("expiry_date")

    # Parsing de la date d'émission
    issue_date = _parse_date(issue_date_input)
    if issue_date is None:
        return {
            "is_valid": False,
            "issue_date": None,
            "expiry_date": None,
            "current_date": None,
            "validity_days": None,
            "days_remaining": None,
            "days_elapsed": None,
            "status": None,
            "percentage_elapsed": None,
            "error": "Date d'émission invalide ou manquante"
        }

    # Parsing de la date courante (défaut: aujourd'hui)
    if current_date_input:
        current_date = _parse_date(current_date_input)
        if current_date is None:
            return {
                "is_valid": False,
                "issue_date": _format_date(issue_date),
                "expiry_date": None,
                "current_date": None,
                "validity_days": None,
                "days_remaining": None,
                "days_elapsed": None,
                "status": None,
                "percentage_elapsed": None,
                "error": "Date de référence invalide"
            }
    else:
        current_date = date.today()

    # Vérification cohérence dates
    if current_date < issue_date:
        return {
            "is_valid": False,
            "issue_date": _format_date(issue_date),
            "expiry_date": None,
            "current_date": _format_date(current_date),
            "validity_days": None,
            "days_remaining": None,
            "days_elapsed": None,
            "status": None,
            "percentage_elapsed": None,
            "error": "La date de référence ne peut pas être antérieure à la date d'émission"
        }

    # Détermination de la durée de validité
    if expiry_date_input:
        # Si date d'expiration explicite fournie
        expiry_date = _parse_date(expiry_date_input)
        if expiry_date is None:
            return {
                "is_valid": False,
                "issue_date": _format_date(issue_date),
                "expiry_date": None,
                "current_date": _format_date(current_date),
                "validity_days": None,
                "days_remaining": None,
                "days_elapsed": None,
                "status": None,
                "percentage_elapsed": None,
                "error": "Date d'expiration invalide"
            }

        if expiry_date <= issue_date:
            return {
                "is_valid": False,
                "issue_date": _format_date(issue_date),
                "expiry_date": _format_date(expiry_date),
                "current_date": _format_date(current_date),
                "validity_days": None,
                "days_remaining": None,
                "days_elapsed": None,
                "status": None,
                "percentage_elapsed": None,
                "error": "La date d'expiration doit être postérieure à la date d'émission"
            }

        validity_days = (expiry_date - issue_date).days
    else:
        # Utiliser validity_days fourni ou valeur par défaut selon type
        if validity_days is None:
            validity_days = DEFAULT_VALIDITY_DAYS.get(quote_type, DEFAULT_VALIDITY_DAYS["standard"])

        # Validation de la durée
        if not isinstance(validity_days, (int, float)):
            return {
                "is_valid": False,
                "issue_date": _format_date(issue_date),
                "expiry_date": None,
                "current_date": _format_date(current_date),
                "validity_days": None,
                "days_remaining": None,
                "days_elapsed": None,
                "status": None,
                "percentage_elapsed": None,
                "error": "La durée de validité doit être un nombre"
            }

        validity_days = int(validity_days)

        if validity_days < MIN_VALIDITY_DAYS:
            return {
                "is_valid": False,
                "issue_date": _format_date(issue_date),
                "expiry_date": None,
                "current_date": _format_date(current_date),
                "validity_days": validity_days,
                "days_remaining": None,
                "days_elapsed": None,
                "status": None,
                "percentage_elapsed": None,
                "error": f"La durée de validité minimum est de {MIN_VALIDITY_DAYS} jour(s)"
            }

        if validity_days > MAX_VALIDITY_DAYS:
            return {
                "is_valid": False,
                "issue_date": _format_date(issue_date),
                "expiry_date": None,
                "current_date": _format_date(current_date),
                "validity_days": validity_days,
                "days_remaining": None,
                "days_elapsed": None,
                "status": None,
                "percentage_elapsed": None,
                "error": f"La durée de validité maximum est de {MAX_VALIDITY_DAYS} jours"
            }

        # Calcul de la date d'expiration
        expiry_date = _calculate_expiry_date(issue_date, validity_days)

    # Calculs
    days_elapsed = (current_date - issue_date).days
    days_remaining = (expiry_date - current_date).days

    # Pourcentage écoulé (0-100+)
    if validity_days > 0:
        percentage_elapsed = round((days_elapsed / validity_days) * 100, 1)
    else:
        percentage_elapsed = 100.0

    # Statut
    status = _get_status(days_remaining)

    # Le devis est valide si la date d'expiration n'est pas passée
    is_valid = days_remaining >= 0

    return {
        "is_valid": is_valid,
        "issue_date": _format_date(issue_date),
        "expiry_date": _format_date(expiry_date),
        "current_date": _format_date(current_date),
        "validity_days": validity_days,
        "days_remaining": days_remaining,
        "days_elapsed": days_elapsed,
        "status": status,
        "percentage_elapsed": percentage_elapsed,
        "error": None
    }
