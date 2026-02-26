"""
Implémentation du sous-programme : validate_number_range

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def _to_decimal(value) -> Decimal | None:
    """Convertit une valeur en Decimal."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '.').replace(' ', '')
        for symbol in ['€', '$', '£']:
            cleaned = cleaned.replace(symbol, '')
        if cleaned and _is_number(cleaned):
            return Decimal(cleaned)
    return None


def _is_number(s: str) -> bool:
    """Vérifie si une chaîne est un nombre valide."""
    if not s:
        return False
    if s[0] in '+-':
        s = s[1:]
    if not s:
        return False
    return s.replace('.', '', 1).isdigit()


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide qu'un nombre est dans un intervalle.

    Args:
        inputs: {
            "value": number,  # Valeur à valider
            "min": number,  # Valeur minimum
            "max": number,  # Valeur maximum
        }

    Returns:
        {
            "is_valid": boolean,  # True si valeur dans la plage
            "error": string,  # Message d'erreur si invalide
        }
    """
    value_input = inputs.get("value")
    min_input = inputs.get("min")
    max_input = inputs.get("max")

    # Valeur vide
    if value_input is None:
        return {
            "is_valid": False,
            "error": "Valeur requise"
        }

    # Conversion
    value = _to_decimal(value_input)
    if value is None:
        return {
            "is_valid": False,
            "error": "Format de nombre invalide"
        }

    min_val = _to_decimal(min_input)
    max_val = _to_decimal(max_input)

    # Vérification min
    if min_val is not None and value < min_val:
        return {
            "is_valid": False,
            "error": f"La valeur doit être >= {min_val}"
        }

    # Vérification max
    if max_val is not None and value > max_val:
        return {
            "is_valid": False,
            "error": f"La valeur doit être <= {max_val}"
        }

    return {
        "is_valid": True,
        "error": None
    }
