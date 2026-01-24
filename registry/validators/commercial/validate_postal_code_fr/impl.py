"""
Implémentation du sous-programme : validate_postal_code_fr

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un code postal français

    Args:
        inputs: {
            "postal_code": string,  # 
        }

    Returns:
        {
            "is_valid": boolean,  # 
            "normalized_code": string,  # 
            "department": string,  # 
            "error": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    postal_code = inputs["postal_code"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "is_valid": None,  # TODO: Calculer la valeur
        "normalized_code": None,  # TODO: Calculer la valeur
        "department": None,  # TODO: Calculer la valeur
        "error": None,  # TODO: Calculer la valeur
    }
