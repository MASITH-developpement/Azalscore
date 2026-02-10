"""
Implémentation du sous-programme : calculate_churn_rate

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 10+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule le taux d'attrition

    Args:
        inputs: {
            "customers_start": number,  # 
            "customers_lost": number,  # 
            "period_days": number,  # 
        }

    Returns:
        {
            "churn_rate": number,  # 
            "retention_rate": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    customers_start = inputs["customers_start"]
    customers_lost = inputs["customers_lost"]
    period_days = inputs["period_days"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "churn_rate": None,  # TODO: Calculer la valeur
        "retention_rate": None,  # TODO: Calculer la valeur
    }
