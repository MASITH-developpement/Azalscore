"""
Implémentation du sous-programme : validate_date_format

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 30+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date
import re


# Formats de date supportés avec leurs patterns
DATE_FORMATS = {
    "YYYY-MM-DD": {
        "pattern": r"^(\d{4})-(\d{2})-(\d{2})$",
        "order": ["year", "month", "day"],
        "separator": "-",
        "example": "2024-01-15",
    },
    "DD/MM/YYYY": {
        "pattern": r"^(\d{2})/(\d{2})/(\d{4})$",
        "order": ["day", "month", "year"],
        "separator": "/",
        "example": "15/01/2024",
    },
    "DD-MM-YYYY": {
        "pattern": r"^(\d{2})-(\d{2})-(\d{4})$",
        "order": ["day", "month", "year"],
        "separator": "-",
        "example": "15-01-2024",
    },
    "MM/DD/YYYY": {
        "pattern": r"^(\d{2})/(\d{2})/(\d{4})$",
        "order": ["month", "day", "year"],
        "separator": "/",
        "example": "01/15/2024",
    },
    "YYYY/MM/DD": {
        "pattern": r"^(\d{4})/(\d{2})/(\d{2})$",
        "order": ["year", "month", "day"],
        "separator": "/",
        "example": "2024/01/15",
    },
    "DD.MM.YYYY": {
        "pattern": r"^(\d{2})\.(\d{2})\.(\d{4})$",
        "order": ["day", "month", "year"],
        "separator": ".",
        "example": "15.01.2024",
    },
    "YYYYMMDD": {
        "pattern": r"^(\d{4})(\d{2})(\d{2})$",
        "order": ["year", "month", "day"],
        "separator": "",
        "example": "20240115",
    },
}


def _validate_date_components(year: int, month: int, day: int) -> tuple[bool, str]:
    """
    Valide les composants d'une date.

    Returns:
        (is_valid, error_message)
    """
    # Année raisonnable
    if year < 1900 or year > 2100:
        return False, f"Année hors plage valide (1900-2100): {year}"

    # Mois valide
    if month < 1 or month > 12:
        return False, f"Mois invalide: {month}"

    # Jours par mois
    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Année bissextile
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    if is_leap:
        days_in_month[2] = 29

    if day < 1 or day > days_in_month[month]:
        return False, f"Jour invalide pour {month:02d}/{year}: {day}"

    return True, ""


def _parse_with_format(date_string: str, format_name: str) -> tuple[bool, date | None, str]:
    """
    Parse une date selon un format spécifique.

    Returns:
        (is_valid, parsed_date, error)
    """
    if format_name not in DATE_FORMATS:
        return False, None, f"Format non supporté: {format_name}"

    format_info = DATE_FORMATS[format_name]
    pattern = format_info["pattern"]
    order = format_info["order"]

    match = re.match(pattern, date_string.strip())
    if not match:
        return False, None, f"La date ne correspond pas au format {format_name} (exemple: {format_info['example']})"

    groups = match.groups()

    # Extraction des composants selon l'ordre
    components = {}
    for i, component_name in enumerate(order):
        components[component_name] = int(groups[i])

    year = components["year"]
    month = components["month"]
    day = components["day"]

    # Validation des composants
    is_valid, error = _validate_date_components(year, month, day)
    if not is_valid:
        return False, None, error

    return True, date(year, month, day), ""


def _detect_format(date_string: str) -> str | None:
    """Détecte automatiquement le format d'une date."""
    date_string = date_string.strip()

    for format_name, format_info in DATE_FORMATS.items():
        if re.match(format_info["pattern"], date_string):
            return format_name

    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide et parse une date selon un format spécifié.

    Formats supportés:
    - YYYY-MM-DD (ISO 8601)
    - DD/MM/YYYY (français)
    - DD-MM-YYYY
    - MM/DD/YYYY (américain)
    - YYYY/MM/DD
    - DD.MM.YYYY (allemand)
    - YYYYMMDD (compact)

    Args:
        inputs: {
            "date_string": string,  # Chaîne de date à valider
            "format": string,  # Format attendu (optionnel, auto-détection)
        }

    Returns:
        {
            "is_valid": boolean,  # True si date valide
            "parsed_date": string,  # Date parsée en ISO (YYYY-MM-DD)
            "detected_format": string,  # Format détecté/utilisé
            "year": number,  # Année extraite
            "month": number,  # Mois extrait
            "day": number,  # Jour extrait
            "day_of_week": string,  # Jour de la semaine
            "is_leap_year": boolean,  # Année bissextile
            "error": string,  # Message d'erreur si invalide
        }
    """
    date_string = inputs.get("date_string", "")
    format_hint = inputs.get("format", "")

    # Valeur vide
    if not date_string:
        return {
            "is_valid": False,
            "parsed_date": None,
            "detected_format": None,
            "year": None,
            "month": None,
            "day": None,
            "day_of_week": None,
            "is_leap_year": None,
            "error": "Date requise"
        }

    date_string = str(date_string).strip()

    # Déterminer le format à utiliser
    if format_hint:
        format_to_use = format_hint.upper()
        if format_to_use not in DATE_FORMATS:
            return {
                "is_valid": False,
                "parsed_date": None,
                "detected_format": None,
                "year": None,
                "month": None,
                "day": None,
                "day_of_week": None,
                "is_leap_year": None,
                "error": f"Format non supporté: {format_hint}. Formats valides: {', '.join(DATE_FORMATS.keys())}"
            }
    else:
        format_to_use = _detect_format(date_string)
        if not format_to_use:
            return {
                "is_valid": False,
                "parsed_date": None,
                "detected_format": None,
                "year": None,
                "month": None,
                "day": None,
                "day_of_week": None,
                "is_leap_year": None,
                "error": "Format de date non reconnu"
            }

    # Parser la date
    is_valid, parsed_date, error = _parse_with_format(date_string, format_to_use)

    if not is_valid:
        return {
            "is_valid": False,
            "parsed_date": None,
            "detected_format": format_to_use,
            "year": None,
            "month": None,
            "day": None,
            "day_of_week": None,
            "is_leap_year": None,
            "error": error
        }

    # Jour de la semaine
    days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    day_of_week = days[parsed_date.weekday()]

    # Année bissextile
    year = parsed_date.year
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    return {
        "is_valid": True,
        "parsed_date": parsed_date.strftime("%Y-%m-%d"),
        "detected_format": format_to_use,
        "year": parsed_date.year,
        "month": parsed_date.month,
        "day": parsed_date.day,
        "day_of_week": day_of_week,
        "is_leap_year": is_leap,
        "error": None
    }
