"""
Implémentation du sous-programme : generate_short_id

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent (NON)

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un identifiant court (8 caractères)

    Args:
        inputs: {
            "length": number,  # 
        }

    Returns:
        {
            "short_id": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    length = inputs.get("length", 8)

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "short_id": None,  # TODO: Calculer la valeur
    }
