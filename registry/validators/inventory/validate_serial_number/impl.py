"""
Implémentation du sous-programme : validate_serial_number

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 12+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Patterns de numéros de série courants
COMMON_PATTERNS = {
    "alphanumeric": r"^[A-Z0-9]+$",
    "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    "numeric": r"^\d+$",
    "prefixed": r"^[A-Z]{2,4}-\d+$",
    "dated": r"^[A-Z]{2,4}-\d{4}\d{2}-\d+$",
}


def _normalize_serial(serial: str) -> str:
    """Normalise un numéro de série."""
    return serial.strip().upper()


def _detect_pattern(serial: str) -> str | None:
    """Détecte le pattern d'un numéro de série."""
    serial_lower = serial.lower()

    for pattern_name, pattern in COMMON_PATTERNS.items():
        if re.match(pattern, serial_lower if pattern_name == "uuid" else serial):
            return pattern_name

    return None


def _extract_info(serial: str) -> dict:
    """Extrait des informations du numéro de série."""
    info = {
        "prefix": None,
        "year": None,
        "month": None,
        "sequence": None,
    }

    # Pattern préfixé: XX-123456
    match = re.match(r'^([A-Z]{2,4})-(\d+)$', serial)
    if match:
        info["prefix"] = match.group(1)
        info["sequence"] = match.group(2)
        return info

    # Pattern daté: XX-YYYYMM-123456
    match = re.match(r'^([A-Z]{2,4})-(\d{4})(\d{2})-(\d+)$', serial)
    if match:
        info["prefix"] = match.group(1)
        info["year"] = int(match.group(2))
        info["month"] = int(match.group(3))
        info["sequence"] = match.group(4)
        return info

    return info


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro de série.

    Args:
        inputs: {
            "serial_number": string,  # Numéro de série à valider
            "format_pattern": string,  # Pattern regex personnalisé (optionnel)
            "min_length": number,  # Longueur minimale (défaut: 4)
            "max_length": number,  # Longueur maximale (défaut: 50)
        }

    Returns:
        {
            "is_valid": boolean,  # True si numéro valide
            "normalized_serial": string,  # Numéro normalisé
            "detected_pattern": string,  # Pattern détecté
            "prefix": string,  # Préfixe extrait
            "year": number,  # Année extraite
            "month": number,  # Mois extrait
            "sequence": string,  # Séquence extraite
            "error": string,  # Message d'erreur si invalide
        }
    """
    serial_number = inputs.get("serial_number", "")
    format_pattern = inputs.get("format_pattern", "")
    min_length = inputs.get("min_length", 4)
    max_length = inputs.get("max_length", 50)

    # Valeur vide
    if not serial_number:
        return {
            "is_valid": False,
            "normalized_serial": None,
            "detected_pattern": None,
            "prefix": None,
            "year": None,
            "month": None,
            "sequence": None,
            "error": "Numéro de série requis"
        }

    # Normalisation
    normalized = _normalize_serial(str(serial_number))

    # Vérification longueur
    if len(normalized) < min_length:
        return {
            "is_valid": False,
            "normalized_serial": normalized,
            "detected_pattern": None,
            "prefix": None,
            "year": None,
            "month": None,
            "sequence": None,
            "error": f"Numéro de série trop court (minimum {min_length} caractères)"
        }

    if len(normalized) > max_length:
        return {
            "is_valid": False,
            "normalized_serial": normalized,
            "detected_pattern": None,
            "prefix": None,
            "year": None,
            "month": None,
            "sequence": None,
            "error": f"Numéro de série trop long (maximum {max_length} caractères)"
        }

    # Validation avec pattern personnalisé
    if format_pattern:
        if not re.match(format_pattern, normalized, re.IGNORECASE):
            return {
                "is_valid": False,
                "normalized_serial": normalized,
                "detected_pattern": "custom",
                "prefix": None,
                "year": None,
                "month": None,
                "sequence": None,
                "error": "Format de numéro de série non conforme"
            }

    # Vérification caractères valides
    if not re.match(r'^[A-Z0-9\-_]+$', normalized):
        return {
            "is_valid": False,
            "normalized_serial": normalized,
            "detected_pattern": None,
            "prefix": None,
            "year": None,
            "month": None,
            "sequence": None,
            "error": "Caractères non autorisés (alphanumérique et tirets uniquement)"
        }

    # Détection du pattern
    detected_pattern = _detect_pattern(normalized)

    # Extraction d'informations
    info = _extract_info(normalized)

    # Validation année/mois si extraits
    if info["year"]:
        current_year = 2026  # Hardcodé pour éviter import datetime
        if info["year"] < 1990 or info["year"] > current_year + 1:
            return {
                "is_valid": False,
                "normalized_serial": normalized,
                "detected_pattern": detected_pattern,
                "prefix": info["prefix"],
                "year": info["year"],
                "month": info["month"],
                "sequence": info["sequence"],
                "error": f"Année invalide dans le numéro de série: {info['year']}"
            }

    if info["month"]:
        if info["month"] < 1 or info["month"] > 12:
            return {
                "is_valid": False,
                "normalized_serial": normalized,
                "detected_pattern": detected_pattern,
                "prefix": info["prefix"],
                "year": info["year"],
                "month": info["month"],
                "sequence": info["sequence"],
                "error": f"Mois invalide dans le numéro de série: {info['month']}"
            }

    return {
        "is_valid": True,
        "normalized_serial": normalized,
        "detected_pattern": detected_pattern,
        "prefix": info["prefix"],
        "year": info["year"],
        "month": info["month"],
        "sequence": info["sequence"],
        "error": None
    }
