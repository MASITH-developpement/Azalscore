"""
Implémentation du sous-programme : generate_document_number

Code métier PUR - Génération de numéros
Utilisation : 40+ endroits dans le codebase
"""

from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un numéro de document formaté.

    Args:
        inputs: {
            "prefix": str,
            "year": int,
            "counter": int,
            "format": str (optionnel)
        }

    Returns:
        {
            "document_number": str,
            "prefix": str,
            "year": int,
            "counter": int
        }

    Examples:
        >>> execute({"prefix": "FAC", "year": 2026, "counter": 1})
        {"document_number": "FAC-2026-00001", ...}

        >>> execute({"prefix": "DEV", "year": 2026, "counter": 42, "format": "{prefix}{year}-{num:04d}"})
        {"document_number": "DEV2026-0042", ...}
    """
    prefix = inputs["prefix"]
    year = int(inputs["year"])
    counter = int(inputs["counter"])
    format_template = inputs.get("format", "{prefix}-{year}-{num:05d}")

    # Génération du numéro
    document_number = format_template.format(
        prefix=prefix,
        year=year,
        num=counter
    )

    return {
        "document_number": document_number,
        "prefix": prefix,
        "year": year,
        "counter": counter
    }
