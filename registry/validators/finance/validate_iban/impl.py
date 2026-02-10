"""
Implémentation du sous-programme : validate_iban

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro IBAN

    Args:
        inputs: {
            "iban": string,  # 
        }

    Returns:
        {
            "is_valid": boolean,  # 
            "normalized_iban": string,  # 
            "country_code": string,  # 
            "bank_code": string,  # 
            "error": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    iban = inputs["iban"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "is_valid": None,  # TODO: Calculer la valeur
        "normalized_iban": None,  # TODO: Calculer la valeur
        "country_code": None,  # TODO: Calculer la valeur
        "bank_code": None,  # TODO: Calculer la valeur
        "error": None,  # TODO: Calculer la valeur
    }
