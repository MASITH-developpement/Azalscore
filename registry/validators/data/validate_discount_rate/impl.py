"""
Implémentation du sous-programme : validate_discount_rate

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


def _to_decimal(value) -> Decimal | None:
    """Convertit une valeur en Decimal."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '.').replace('%', '')
        if cleaned and cleaned.replace('.', '').replace('-', '').isdigit():
            return Decimal(cleaned)
    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un taux de remise.

    Args:
        inputs: {
            "discount_rate": number,  # Taux de remise (0-100)
        }

    Returns:
        {
            "is_valid": boolean,  # True si remise valide
            "error": string,  # Message d'erreur si invalide
        }
    """
    discount_rate_input = inputs.get("discount_rate")

    # Valeur vide
    if discount_rate_input is None:
        return {
            "is_valid": False,
            "error": "Taux de remise requis"
        }

    # Conversion
    rate = _to_decimal(discount_rate_input)
    if rate is None:
        return {
            "is_valid": False,
            "error": "Format de taux invalide"
        }

    # Si c'est une fraction (0.10), convertir en pourcentage
    if rate > 0 and rate < 1:
        rate = rate * 100

    # Vérification plage
    if rate < 0:
        return {
            "is_valid": False,
            "error": "Taux de remise négatif non autorisé"
        }

    if rate > 100:
        return {
            "is_valid": False,
            "error": "Taux de remise supérieur à 100% non autorisé"
        }

    return {
        "is_valid": True,
        "error": None
    }
