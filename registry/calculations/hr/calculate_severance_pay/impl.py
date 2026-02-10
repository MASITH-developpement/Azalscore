"""
Implémentation du sous-programme : calculate_severance_pay

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 5+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule l'indemnité de licenciement

    Args:
        inputs: {
            "years_of_service": number,  # 
            "average_salary": number,  # 
        }

    Returns:
        {
            "severance_amount": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    years_of_service = inputs["years_of_service"]
    average_salary = inputs["average_salary"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "severance_amount": None,  # TODO: Calculer la valeur
    }
