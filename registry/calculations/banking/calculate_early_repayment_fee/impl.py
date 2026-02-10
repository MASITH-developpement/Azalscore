"""
Implémentation du sous-programme : calculate_early_repayment_fee

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
    Calcule les pénalités de remboursement anticipé

    Args:
        inputs: {
            "remaining_capital": number,  # 
        }

    Returns:
        {
            "fee": number,  # 
        }
    """
    # TODO: Implémenter la logique métier

    remaining_capital = inputs["remaining_capital"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "fee": None,  # TODO: Calculer la valeur
    }
