"""
Implémentation du sous-programme : validate_bic

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
    Valide un code BIC/SWIFT

    Args:
        inputs: {
            "bic": string,  # 
        }

    Returns:
        {
            "is_valid": boolean,  # 
            "normalized_bic": string,  # 
            "error": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    bic = inputs["bic"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "is_valid": None,  # TODO: Calculer la valeur
        "normalized_bic": None,  # TODO: Calculer la valeur
        "error": None,  # TODO: Calculer la valeur
    }
