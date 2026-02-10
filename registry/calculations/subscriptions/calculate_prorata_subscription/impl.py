"""
Implémentation du sous-programme : calculate_prorata_subscription

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
    Calcule le prorata d'abonnement

    Args:
        inputs: {
            "monthly_fee": number,  # 
        }

    Returns:
        {
            "prorata": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    monthly_fee = inputs["monthly_fee"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "prorata": None,  # TODO: Calculer la valeur
    }
