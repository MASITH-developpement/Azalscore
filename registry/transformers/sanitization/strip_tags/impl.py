"""
Implémentation du sous-programme : strip_tags

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
    Supprime les tags HTML

    Args:
        inputs: {
            "html": string,  # 
        }

    Returns:
        {
            "text": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    html = inputs["html"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "text": None,  # TODO: Calculer la valeur
    }
