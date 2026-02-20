"""
Implémentation du sous-programme : validate_payment_terms

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 12+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Conditions de paiement standard
STANDARD_TERMS = {
    "immediate": {
        "days": 0,
        "description": "Paiement immédiat",
        "aliases": ["comptant", "cash", "à réception", "0 jour"],
    },
    "net_10": {
        "days": 10,
        "description": "Paiement à 10 jours net",
        "aliases": ["10 jours", "net 10"],
    },
    "net_15": {
        "days": 15,
        "description": "Paiement à 15 jours net",
        "aliases": ["15 jours", "net 15"],
    },
    "net_30": {
        "days": 30,
        "description": "Paiement à 30 jours net",
        "aliases": ["30 jours", "net 30", "1 mois"],
    },
    "net_45": {
        "days": 45,
        "description": "Paiement à 45 jours net",
        "aliases": ["45 jours", "net 45"],
    },
    "net_60": {
        "days": 60,
        "description": "Paiement à 60 jours net",
        "aliases": ["60 jours", "net 60", "2 mois"],
    },
    "net_90": {
        "days": 90,
        "description": "Paiement à 90 jours net",
        "aliases": ["90 jours", "net 90", "3 mois"],
    },
    "end_of_month": {
        "days": 30,  # Approximatif
        "description": "Paiement fin de mois",
        "aliases": ["fin de mois", "fdm", "eom"],
    },
    "end_of_month_30": {
        "days": 45,  # Approximatif
        "description": "30 jours fin de mois",
        "aliases": ["30 jours fin de mois", "30 fdm", "30 eom"],
    },
    "end_of_month_45": {
        "days": 60,  # Approximatif
        "description": "45 jours fin de mois",
        "aliases": ["45 jours fin de mois", "45 fdm", "45 eom"],
    },
    "end_of_month_60": {
        "days": 75,  # Approximatif
        "description": "60 jours fin de mois",
        "aliases": ["60 jours fin de mois", "60 fdm", "60 eom"],
    },
}


def _normalize_terms(terms: str) -> str:
    """Normalise une chaîne de conditions de paiement."""
    return terms.strip().lower()


def _parse_days(terms: str) -> int | None:
    """Extrait le nombre de jours d'une expression."""
    normalized = _normalize_terms(terms)

    # Pattern pour extraire les jours
    patterns = [
        r'(\d+)\s*jours?',
        r'net\s*(\d+)',
        r'(\d+)\s*days?',
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return int(match.group(1))

    return None


def _find_standard_term(terms: str) -> tuple[str | None, dict | None]:
    """Trouve une condition standard correspondante."""
    normalized = _normalize_terms(terms)

    for term_key, term_info in STANDARD_TERMS.items():
        # Vérifier le nom exact
        if normalized == term_key.replace("_", " "):
            return term_key, term_info

        # Vérifier les alias
        for alias in term_info["aliases"]:
            if normalized == alias.lower():
                return term_key, term_info

    return None, None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide et parse des conditions de paiement.

    Conditions supportées:
    - immediate/comptant: Paiement immédiat
    - net_10 à net_90: Paiement à X jours
    - end_of_month: Fin de mois
    - end_of_month_30/45/60: X jours fin de mois
    - Format libre: "X jours"

    Args:
        inputs: {
            "payment_terms": string,  # Conditions de paiement
            "max_days": number,  # Maximum de jours autorisé (défaut: 90)
        }

    Returns:
        {
            "is_valid": boolean,  # True si conditions valides
            "days": number,  # Nombre de jours de paiement
            "term_code": string,  # Code normalisé (net_30, etc.)
            "description": string,  # Description lisible
            "is_standard": boolean,  # True si condition standard
            "is_end_of_month": boolean,  # True si fin de mois
            "error": string,  # Message d'erreur si invalide
        }
    """
    payment_terms = inputs.get("payment_terms", "")
    max_days = inputs.get("max_days", 90)

    # Valeur vide
    if not payment_terms:
        return {
            "is_valid": False,
            "days": None,
            "term_code": None,
            "description": None,
            "is_standard": None,
            "is_end_of_month": None,
            "error": "Conditions de paiement requises"
        }

    payment_terms = str(payment_terms)
    normalized = _normalize_terms(payment_terms)

    # Chercher une condition standard
    term_code, term_info = _find_standard_term(payment_terms)

    if term_info:
        days = term_info["days"]
        description = term_info["description"]
        is_standard = True
        is_eom = "end_of_month" in term_code
    else:
        # Essayer de parser les jours
        days = _parse_days(payment_terms)

        if days is None:
            return {
                "is_valid": False,
                "days": None,
                "term_code": None,
                "description": None,
                "is_standard": False,
                "is_end_of_month": None,
                "error": "Format de conditions non reconnu"
            }

        term_code = f"net_{days}"
        description = f"Paiement à {days} jours"
        is_standard = False
        is_eom = "fin de mois" in normalized or "fdm" in normalized or "eom" in normalized

    # Vérification du maximum
    if days > max_days:
        return {
            "is_valid": False,
            "days": days,
            "term_code": term_code,
            "description": description,
            "is_standard": is_standard,
            "is_end_of_month": is_eom,
            "error": f"Délai de paiement maximum: {max_days} jours"
        }

    # Vérification valeur négative
    if days < 0:
        return {
            "is_valid": False,
            "days": days,
            "term_code": None,
            "description": None,
            "is_standard": False,
            "is_end_of_month": None,
            "error": "Délai de paiement négatif non autorisé"
        }

    return {
        "is_valid": True,
        "days": days,
        "term_code": term_code,
        "description": description,
        "is_standard": is_standard,
        "is_end_of_month": is_eom,
        "error": None
    }
