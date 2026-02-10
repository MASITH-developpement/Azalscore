"""
Implémentation du sous-programme : get_company_info

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects (DÉCLARÉ)
- Idempotent

Utilisation : 8+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Récupère les infos d'une entreprise via INSEE

    Args:
        inputs: {
            "siret": string,  # 
        }

    Returns:
        {
            "company_data": object,  # 
            "error": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    siret = inputs["siret"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "company_data": None,  # TODO: Calculer la valeur
        "error": None,  # TODO: Calculer la valeur
    }
