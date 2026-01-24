"""
Implémentation du sous-programme : refund_payment

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects (DÉCLARÉ)
- Idempotent (NON)

Utilisation : 8+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rembourse un paiement Stripe

    Args:
        inputs: {
            "payment_intent_id": string,  # 
            "amount": number,  # 
        }

    Returns:
        {
            "refund_id": string,  # 
            "status": string,  # 
            "amount_refunded": number,  # 
            "error": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    payment_intent_id = inputs["payment_intent_id"]
    amount = inputs["amount"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "refund_id": None,  # TODO: Calculer la valeur
        "status": None,  # TODO: Calculer la valeur
        "amount_refunded": None,  # TODO: Calculer la valeur
        "error": None,  # TODO: Calculer la valeur
    }
