"""
Implémentation du sous-programme : validate_file_size

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


# Constantes de conversion
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024


def _format_size(bytes_size: int) -> str:
    """Formate une taille en unité lisible."""
    if bytes_size >= BYTES_PER_GB:
        return f"{bytes_size / BYTES_PER_GB:.2f} Go"
    elif bytes_size >= BYTES_PER_MB:
        return f"{bytes_size / BYTES_PER_MB:.2f} Mo"
    elif bytes_size >= BYTES_PER_KB:
        return f"{bytes_size / BYTES_PER_KB:.2f} Ko"
    else:
        return f"{bytes_size} octets"


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide la taille d'un fichier.

    Args:
        inputs: {
            "file_size_bytes": number,  # Taille du fichier en octets
            "max_size_mb": number,  # Taille maximum en Mo
            "min_size_bytes": number,  # Taille minimum en octets (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si taille valide
            "size_mb": number,  # Taille en Mo
            "size_formatted": string,  # Taille formatée
            "percentage_of_max": number,  # Pourcentage du max
            "error": string,  # Message d'erreur si invalide
        }
    """
    file_size_bytes = inputs.get("file_size_bytes")
    max_size_mb = inputs.get("max_size_mb")
    min_size_bytes = inputs.get("min_size_bytes", 0)

    # Valeur vide
    if file_size_bytes is None:
        return {
            "is_valid": False,
            "size_mb": None,
            "size_formatted": None,
            "percentage_of_max": None,
            "error": "Taille de fichier requise"
        }

    # Conversion en entier
    if not isinstance(file_size_bytes, (int, float)):
        return {
            "is_valid": False,
            "size_mb": None,
            "size_formatted": None,
            "percentage_of_max": None,
            "error": "Format de taille invalide"
        }

    file_size_bytes = int(file_size_bytes)

    # Taille négative
    if file_size_bytes < 0:
        return {
            "is_valid": False,
            "size_mb": None,
            "size_formatted": None,
            "percentage_of_max": None,
            "error": "Taille négative non autorisée"
        }

    # Calculs
    size_mb = round(file_size_bytes / BYTES_PER_MB, 2)
    size_formatted = _format_size(file_size_bytes)

    # Vérification taille minimum
    if file_size_bytes < min_size_bytes:
        return {
            "is_valid": False,
            "size_mb": size_mb,
            "size_formatted": size_formatted,
            "percentage_of_max": None,
            "error": f"Taille minimum: {_format_size(min_size_bytes)}"
        }

    # Vérification taille maximum
    percentage_of_max = None
    if max_size_mb is not None:
        max_bytes = max_size_mb * BYTES_PER_MB
        percentage_of_max = round((file_size_bytes / max_bytes) * 100, 1) if max_bytes > 0 else 100

        if file_size_bytes > max_bytes:
            return {
                "is_valid": False,
                "size_mb": size_mb,
                "size_formatted": size_formatted,
                "percentage_of_max": percentage_of_max,
                "error": f"Taille maximum: {max_size_mb} Mo"
            }

    return {
        "is_valid": True,
        "size_mb": size_mb,
        "size_formatted": size_formatted,
        "percentage_of_max": percentage_of_max,
        "error": None
    }
