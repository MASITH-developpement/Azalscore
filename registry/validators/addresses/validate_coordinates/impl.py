"""
Implémentation du sous-programme : validate_coordinates

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
    Valide des coordonnées GPS

    Args:
        inputs: {
            "lat": number,  # 
        }

    Returns:
        {
            "is_valid": boolean,  # 
        }
    """
    # TODO: Implémenter la logique métier

    lat = inputs["lat"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "is_valid": None,  # TODO: Calculer la valeur
    }
