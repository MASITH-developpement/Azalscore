"""
Implémentation du sous-programme : convert_weight

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 12+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit des poids

    Args:
        inputs: {
            "value": number,  # 
        }

    Returns:
        {
            "converted": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    value = inputs["value"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "converted": None,  # TODO: Calculer la valeur
    }
