"""
Implémentation du sous-programme : calculate_annual_savings

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
    Calcule l'économie annuelle

    Args:
        inputs: {
            "monthly_price": number,  # 
        }

    Returns:
        {
            "savings": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    monthly_price = inputs["monthly_price"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "savings": None,  # TODO: Calculer la valeur
    }
