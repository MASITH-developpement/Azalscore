"""
Implémentation du sous-programme : validate_file_size

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide la taille d'un fichier

    Args:
        inputs: {
            "file_size_bytes": number,  # 
            "max_size_mb": number,  # 
        }

    Returns:
        {
            "is_valid": boolean,  # 
            "size_mb": number,  # 
            "error": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    file_size_bytes = inputs["file_size_bytes"]
    max_size_mb = inputs["max_size_mb"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "is_valid": None,  # TODO: Calculer la valeur
        "size_mb": None,  # TODO: Calculer la valeur
        "error": None,  # TODO: Calculer la valeur
    }
