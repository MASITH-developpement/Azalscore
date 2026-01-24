"""
Implémentation du sous-programme : calculate_project_duration

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 10+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule la durée d'un projet

    Args:
        inputs: {
            "tasks": array,  # 
        }

    Returns:
        {
            "total_duration": number,  # 
            "critical_path": array,  # 
            "earliest_start": string,  # 
            "latest_finish": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    tasks = inputs["tasks"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "total_duration": None,  # TODO: Calculer la valeur
        "critical_path": None,  # TODO: Calculer la valeur
        "earliest_start": None,  # TODO: Calculer la valeur
        "latest_finish": None,  # TODO: Calculer la valeur
    }
