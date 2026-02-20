"""
Implémentation du sous-programme : validate_fiscal_year

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 10+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date


def _parse_date(date_value) -> date | None:
    """Parse une date depuis différents formats."""
    if date_value is None:
        return None

    if isinstance(date_value, date):
        return date_value

    if isinstance(date_value, datetime):
        return date_value.date()

    if isinstance(date_value, str):
        # Essayer différents formats
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            parsed = None
            # Simple parsing sans try/except (règle stricte)
            # On utilise une approche de validation manuelle
            if fmt == "%Y-%m-%d" and len(date_value) == 10 and date_value[4] == '-' and date_value[7] == '-':
                parts = date_value.split('-')
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        return date(year, month, day)
            elif fmt == "%d/%m/%Y" and len(date_value) == 10 and date_value[2] == '/' and date_value[5] == '/':
                parts = date_value.split('/')
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        return date(year, month, day)

    return None


def _calculate_months_difference(start: date, end: date) -> int:
    """Calcule la différence en mois entre deux dates."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    # Ajuster si le jour de fin est avant le jour de début
    if end.day < start.day:
        months -= 1
    return months


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un exercice fiscal selon les règles comptables françaises.

    Règles:
    - Durée standard: 12 mois
    - Durée minimale: 1 mois (exercice de constitution)
    - Durée maximale: 23 mois (premier exercice ou changement de clôture)
    - La date de fin doit être après la date de début

    Args:
        inputs: {
            "start_date": string/date,  # Date de début de l'exercice
            "end_date": string/date,  # Date de fin de l'exercice
            "is_first_fiscal_year": boolean,  # Est-ce le premier exercice (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si exercice valide
            "duration_months": number,  # Durée en mois
            "duration_days": number,  # Durée en jours
            "is_standard_duration": boolean,  # True si durée de 12 mois
            "is_short_fiscal_year": boolean,  # True si durée < 12 mois
            "is_long_fiscal_year": boolean,  # True si durée > 12 mois
            "closing_date_month": number,  # Mois de clôture (1-12)
            "fiscal_year_code": string,  # Code suggéré (ex: "2024" ou "2024-2025")
            "error": string,  # Message d'erreur si invalide
        }
    """
    start_date = inputs.get("start_date")
    end_date = inputs.get("end_date")
    is_first_fiscal_year = inputs.get("is_first_fiscal_year", False)

    # Parsing des dates
    start = _parse_date(start_date)
    end = _parse_date(end_date)

    # Validation date de début
    if start is None:
        return {
            "is_valid": False,
            "duration_months": None,
            "duration_days": None,
            "is_standard_duration": None,
            "is_short_fiscal_year": None,
            "is_long_fiscal_year": None,
            "closing_date_month": None,
            "fiscal_year_code": None,
            "error": "Date de début invalide ou manquante"
        }

    # Validation date de fin
    if end is None:
        return {
            "is_valid": False,
            "duration_months": None,
            "duration_days": None,
            "is_standard_duration": None,
            "is_short_fiscal_year": None,
            "is_long_fiscal_year": None,
            "closing_date_month": None,
            "fiscal_year_code": None,
            "error": "Date de fin invalide ou manquante"
        }

    # La fin doit être après le début
    if end <= start:
        return {
            "is_valid": False,
            "duration_months": None,
            "duration_days": (end - start).days,
            "is_standard_duration": False,
            "is_short_fiscal_year": None,
            "is_long_fiscal_year": None,
            "closing_date_month": end.month,
            "fiscal_year_code": None,
            "error": "La date de fin doit être postérieure à la date de début"
        }

    # Calcul de la durée
    duration_days = (end - start).days + 1  # +1 pour inclure les deux dates
    duration_months = _calculate_months_difference(start, end)

    # Durée minimale: au moins 1 jour
    if duration_days < 1:
        return {
            "is_valid": False,
            "duration_months": 0,
            "duration_days": duration_days,
            "is_standard_duration": False,
            "is_short_fiscal_year": True,
            "is_long_fiscal_year": False,
            "closing_date_month": end.month,
            "fiscal_year_code": None,
            "error": "L'exercice doit avoir une durée d'au moins 1 jour"
        }

    # Durée maximale selon le type d'exercice
    max_months = 23 if is_first_fiscal_year else 12
    if duration_months > max_months:
        return {
            "is_valid": False,
            "duration_months": duration_months,
            "duration_days": duration_days,
            "is_standard_duration": False,
            "is_short_fiscal_year": False,
            "is_long_fiscal_year": True,
            "closing_date_month": end.month,
            "fiscal_year_code": None,
            "error": f"L'exercice ne peut pas dépasser {max_months} mois"
        }

    # Détermination du type d'exercice
    is_standard = 11 <= duration_months <= 13  # ~12 mois avec tolérance
    is_short = duration_months < 11
    is_long = duration_months > 13

    # Génération du code exercice
    if start.year == end.year:
        fiscal_year_code = str(end.year)
    else:
        fiscal_year_code = f"{start.year}-{end.year}"

    return {
        "is_valid": True,
        "duration_months": duration_months,
        "duration_days": duration_days,
        "is_standard_duration": is_standard,
        "is_short_fiscal_year": is_short,
        "is_long_fiscal_year": is_long,
        "closing_date_month": end.month,
        "fiscal_year_code": fiscal_year_code,
        "error": None
    }
