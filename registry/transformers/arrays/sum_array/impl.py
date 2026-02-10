"""
Implémentation du sous-programme : sum_array

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 35+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule la somme d'un tableau

    Args:
        inputs: {
            "values": array,  # 
        }

    Returns:
        {
            "sum": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    values = inputs["values"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "sum": None,  # TODO: Calculer la valeur
    }
