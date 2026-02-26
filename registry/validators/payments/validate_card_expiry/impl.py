"""
Implémentation du sous-programme : validate_card_expiry

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import date
import re


def _parse_expiry(expiry: str) -> tuple[int | None, int | None, str]:
    """
    Parse une date d'expiration de carte.

    Formats supportés: MM/YY, MM/YYYY, MMYY, MMYYYY

    Returns:
        (month, year, error)
    """
    if not expiry:
        return None, None, "Date d'expiration requise"

    # Normalisation
    cleaned = expiry.strip().replace(" ", "").replace("-", "/")

    # Pattern MM/YY ou MM/YYYY
    match = re.match(r'^(\d{2})/(\d{2,4})$', cleaned)
    if match:
        month = int(match.group(1))
        year_str = match.group(2)
        if len(year_str) == 2:
            year = 2000 + int(year_str)
        else:
            year = int(year_str)
        return month, year, ""

    # Pattern MMYY ou MMYYYY
    if cleaned.isdigit():
        if len(cleaned) == 4:
            month = int(cleaned[:2])
            year = 2000 + int(cleaned[2:])
            return month, year, ""
        elif len(cleaned) == 6:
            month = int(cleaned[:2])
            year = int(cleaned[2:])
            return month, year, ""

    return None, None, "Format de date invalide (attendu: MM/YY ou MM/YYYY)"


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une date d'expiration de carte bancaire.

    Formats acceptés:
    - MM/YY (ex: 12/25)
    - MM/YYYY (ex: 12/2025)
    - MMYY (ex: 1225)
    - MMYYYY (ex: 122025)

    Args:
        inputs: {
            "expiry": string,  # Date d'expiration
            "reference_date": string/date,  # Date de référence (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si carte non expirée
            "month": number,  # Mois d'expiration
            "year": number,  # Année d'expiration
            "formatted_expiry": string,  # Format MM/YY
            "is_expired": boolean,  # True si expirée
            "months_until_expiry": number,  # Mois avant expiration
            "is_expiring_soon": boolean,  # Expire dans les 3 mois
            "error": string,  # Message d'erreur si invalide
        }
    """
    expiry = inputs.get("expiry", "")
    reference_date = inputs.get("reference_date")

    # Parse de l'expiration
    month, year, parse_error = _parse_expiry(str(expiry) if expiry else "")

    if parse_error:
        return {
            "is_valid": False,
            "month": None,
            "year": None,
            "formatted_expiry": None,
            "is_expired": None,
            "months_until_expiry": None,
            "is_expiring_soon": None,
            "error": parse_error
        }

    # Validation du mois
    if month < 1 or month > 12:
        return {
            "is_valid": False,
            "month": month,
            "year": year,
            "formatted_expiry": None,
            "is_expired": None,
            "months_until_expiry": None,
            "is_expiring_soon": None,
            "error": f"Mois invalide: {month}"
        }

    # Validation de l'année (pas trop dans le passé ou futur)
    current_year = date.today().year
    if year < current_year - 10:
        return {
            "is_valid": False,
            "month": month,
            "year": year,
            "formatted_expiry": f"{month:02d}/{year % 100:02d}",
            "is_expired": True,
            "months_until_expiry": None,
            "is_expiring_soon": False,
            "error": "Carte expirée depuis plus de 10 ans"
        }

    if year > current_year + 20:
        return {
            "is_valid": False,
            "month": month,
            "year": year,
            "formatted_expiry": f"{month:02d}/{year % 100:02d}",
            "is_expired": False,
            "months_until_expiry": None,
            "is_expiring_soon": False,
            "error": "Année d'expiration trop éloignée"
        }

    # Date de référence
    if reference_date:
        if isinstance(reference_date, date):
            ref_date = reference_date
        elif isinstance(reference_date, str):
            # Parse simple YYYY-MM-DD
            parts = reference_date.split("-")
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                ref_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                ref_date = date.today()
        else:
            ref_date = date.today()
    else:
        ref_date = date.today()

    # Calcul de l'expiration (fin du mois d'expiration)
    # Une carte expire à la fin du mois indiqué
    ref_year = ref_date.year
    ref_month = ref_date.month

    # Nombre de mois jusqu'à expiration
    months_until_expiry = (year - ref_year) * 12 + (month - ref_month)

    # La carte est valide jusqu'à la fin du mois d'expiration
    is_expired = months_until_expiry < 0

    # Expire bientôt (dans les 3 mois)
    is_expiring_soon = 0 <= months_until_expiry <= 3

    # Format
    formatted = f"{month:02d}/{year % 100:02d}"

    if is_expired:
        return {
            "is_valid": False,
            "month": month,
            "year": year,
            "formatted_expiry": formatted,
            "is_expired": True,
            "months_until_expiry": months_until_expiry,
            "is_expiring_soon": False,
            "error": "Carte expirée"
        }

    return {
        "is_valid": True,
        "month": month,
        "year": year,
        "formatted_expiry": formatted,
        "is_expired": False,
        "months_until_expiry": months_until_expiry,
        "is_expiring_soon": is_expiring_soon,
        "error": None
    }
