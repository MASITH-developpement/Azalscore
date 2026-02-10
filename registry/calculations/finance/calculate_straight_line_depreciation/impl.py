"""
Implémentation du sous-programme : calculate_straight_line_depreciation

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
    Calcule l'amortissement linéaire

    Args:
        inputs: {
            "asset_cost": number,  # 
            "salvage_value": number,  # 
            "useful_life_years": number,  # 
        }

    Returns:
        {
            "annual_depreciation": number,  # 
            "monthly_depreciation": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    asset_cost = inputs["asset_cost"]
    salvage_value = inputs["salvage_value"]
    useful_life_years = inputs["useful_life_years"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "annual_depreciation": None,  # TODO: Calculer la valeur
        "monthly_depreciation": None,  # TODO: Calculer la valeur
    }
