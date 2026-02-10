"""
Implémentation du sous-programme : average_array

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 25+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule la moyenne d'un tableau

    Args:
        inputs: {
            "values": array,  # 
        }

    Returns:
        {
            "average": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    values = inputs["values"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "average": None,  # TODO: Calculer la valeur
    }
