"""
Implémentation du sous-programme : calculate_customer_acquisition_cost

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 8+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule le coût d'acquisition client (CAC)

    Args:
        inputs: {
            "marketing_cost": number,  # 
            "sales_cost": number,  # 
            "new_customers": number,  # 
        }

    Returns:
        {
            "cac": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    marketing_cost = inputs["marketing_cost"]
    sales_cost = inputs["sales_cost"]
    new_customers = inputs["new_customers"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "cac": None,  # TODO: Calculer la valeur
    }
