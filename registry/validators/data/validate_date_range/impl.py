"""
Implémentation du sous-programme : validate_date_range

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

        # Format ISO: YYYY-MM-DD
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            parts = date_str.split('-')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                    # Validation jour du mois
                    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
                    if is_leap:
                        days_in_month[2] = 29
                    if day <= days_in_month[month]:
                        return date(year, month, day)

        # Format français: DD/MM/YYYY
        if len(date_str) == 10 and date_str[2] == '/' and date_str[5] == '/':
            parts = date_str.split('/')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
                    if is_leap:
                        days_in_month[2] = 29
                    if day <= days_in_month[month]:
                        return date(year, month, day)

    return None


def _format_date(d: date) -> str:
    """Formate une date en ISO."""
    return d.strftime("%Y-%m-%d")


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide qu'une date est dans un intervalle donné.

    Args:
        inputs: {
            "date": string/date,  # Date à valider
            "min_date": string/date,  # Date minimum (optionnel)
            "max_date": string/date,  # Date maximum (optionnel)
            "inclusive": boolean,  # Bornes inclusives (défaut: true)
        }

    Returns:
        {
            "is_valid": boolean,  # True si dans l'intervalle
            "date": string,  # Date validée (ISO)
            "min_date": string,  # Date minimum (ISO)
            "max_date": string,  # Date maximum (ISO)
            "days_from_min": number,  # Jours depuis min_date
            "days_to_max": number,  # Jours jusqu'à max_date
            "is_in_past": boolean,  # Date dans le passé
            "is_in_future": boolean,  # Date dans le futur
            "error": string,  # Message d'erreur si invalide
        }
    """
    date_input = inputs.get("date")
    min_date_input = inputs.get("min_date")
    max_date_input = inputs.get("max_date")
    inclusive = inputs.get("inclusive", True)

    # Date à valider
    validated_date = _parse_date(date_input)
    if validated_date is None:
        return {
            "is_valid": False,
            "date": None,
            "min_date": None,
            "max_date": None,
            "days_from_min": None,
            "days_to_max": None,
            "is_in_past": None,
            "is_in_future": None,
            "error": "Date invalide ou manquante"
        }

    # Parse des bornes
    min_date = _parse_date(min_date_input) if min_date_input else None
    max_date = _parse_date(max_date_input) if max_date_input else None

    # Vérification cohérence des bornes
    if min_date and max_date and min_date > max_date:
        return {
            "is_valid": False,
            "date": _format_date(validated_date),
            "min_date": _format_date(min_date),
            "max_date": _format_date(max_date),
            "days_from_min": None,
            "days_to_max": None,
            "is_in_past": validated_date < date.today(),
            "is_in_future": validated_date > date.today(),
            "error": "La date minimum doit être antérieure à la date maximum"
        }

    # Vérification borne inférieure
    if min_date:
        if inclusive:
            if validated_date < min_date:
                return {
                    "is_valid": False,
                    "date": _format_date(validated_date),
                    "min_date": _format_date(min_date),
                    "max_date": _format_date(max_date) if max_date else None,
                    "days_from_min": (validated_date - min_date).days,
                    "days_to_max": (max_date - validated_date).days if max_date else None,
                    "is_in_past": validated_date < date.today(),
                    "is_in_future": validated_date > date.today(),
                    "error": f"La date doit être au plus tôt le {_format_date(min_date)}"
                }
        else:
            if validated_date <= min_date:
                return {
                    "is_valid": False,
                    "date": _format_date(validated_date),
                    "min_date": _format_date(min_date),
                    "max_date": _format_date(max_date) if max_date else None,
                    "days_from_min": (validated_date - min_date).days,
                    "days_to_max": (max_date - validated_date).days if max_date else None,
                    "is_in_past": validated_date < date.today(),
                    "is_in_future": validated_date > date.today(),
                    "error": f"La date doit être strictement postérieure au {_format_date(min_date)}"
                }

    # Vérification borne supérieure
    if max_date:
        if inclusive:
            if validated_date > max_date:
                return {
                    "is_valid": False,
                    "date": _format_date(validated_date),
                    "min_date": _format_date(min_date) if min_date else None,
                    "max_date": _format_date(max_date),
                    "days_from_min": (validated_date - min_date).days if min_date else None,
                    "days_to_max": (max_date - validated_date).days,
                    "is_in_past": validated_date < date.today(),
                    "is_in_future": validated_date > date.today(),
                    "error": f"La date doit être au plus tard le {_format_date(max_date)}"
                }
        else:
            if validated_date >= max_date:
                return {
                    "is_valid": False,
                    "date": _format_date(validated_date),
                    "min_date": _format_date(min_date) if min_date else None,
                    "max_date": _format_date(max_date),
                    "days_from_min": (validated_date - min_date).days if min_date else None,
                    "days_to_max": (max_date - validated_date).days,
                    "is_in_past": validated_date < date.today(),
                    "is_in_future": validated_date > date.today(),
                    "error": f"La date doit être strictement antérieure au {_format_date(max_date)}"
                }

    # Calculs
    days_from_min = (validated_date - min_date).days if min_date else None
    days_to_max = (max_date - validated_date).days if max_date else None
    today = date.today()

    return {
        "is_valid": True,
        "date": _format_date(validated_date),
        "min_date": _format_date(min_date) if min_date else None,
        "max_date": _format_date(max_date) if max_date else None,
        "days_from_min": days_from_min,
        "days_to_max": days_to_max,
        "is_in_past": validated_date < today,
        "is_in_future": validated_date > today,
        "error": None
    }
