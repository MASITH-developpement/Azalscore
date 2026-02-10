"""
Implémentation du sous-programme : parse_number

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
    Parse une chaîne en nombre

    Args:
        inputs: {
            "value": string,  # 
            "locale": string,  # 
        }

    Returns:
        {
            "number": number,  # 
            "is_valid": boolean,  # 
        }
    """
    # TODO: Implémenter la logique métier

    value = inputs["value"]
    locale = inputs.get("locale", 'fr_FR')

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "number": None,  # TODO: Calculer la valeur
        "is_valid": None,  # TODO: Calculer la valeur
    }
