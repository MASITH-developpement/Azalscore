"""
Implémentation du sous-programme : validate_file_extension

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 18+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide l'extension d'un fichier

    Args:
        inputs: {
            "filename": string,  # 
            "allowed_extensions": array,  # 
        }

    Returns:
        {
            "is_valid": boolean,  # 
            "extension": string,  # 
            "error": string,  # 
        }
    """
    # TODO: Implémenter la logique métier

    filename = inputs["filename"]
    allowed_extensions = inputs["allowed_extensions"]

    # Logique métier à implémenter
    # TODO: Remplacer ce template par la vraie logique

    return {
        "is_valid": None,  # TODO: Calculer la valeur
        "extension": None,  # TODO: Calculer la valeur
        "error": None,  # TODO: Calculer la valeur
    }
