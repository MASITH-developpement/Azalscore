"""
Implémentation du sous-programme : log_to_sentry

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects (DÉCLARÉ)
- Idempotent (NON)

Utilisation : 30+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enregistre dans Sentry

    Args:
        inputs: {
            "error": object,  # 
        }

    Returns:
        {
            "event_id": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    error = inputs["error"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "event_id": None,  # TODO: Calculer la valeur
    }
