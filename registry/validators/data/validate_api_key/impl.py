"""
Implémentation du sous-programme : validate_api_key

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Formats de clés API connus
API_KEY_FORMATS = {
    "uuid": {
        "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        "description": "UUID v4",
        "example": "550e8400-e29b-41d4-a716-446655440000",
    },
    "hex32": {
        "pattern": r"^[0-9a-fA-F]{32}$",
        "description": "32 caractères hexadécimaux",
        "example": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
    },
    "hex64": {
        "pattern": r"^[0-9a-fA-F]{64}$",
        "description": "64 caractères hexadécimaux",
        "example": "a1b2c3d4e5f6..." + "a" * 64,
    },
    "base64": {
        "pattern": r"^[A-Za-z0-9+/]+=*$",
        "description": "Encodage Base64",
        "example": "YXBpX2tleV9leGFtcGxl",
    },
    "alphanumeric": {
        "pattern": r"^[A-Za-z0-9]+$",
        "description": "Alphanumérique",
        "example": "abc123XYZ",
    },
    "prefixed": {
        "pattern": r"^[a-z]+_[A-Za-z0-9]+$",
        "description": "Préfixe + underscore (ex: sk_live_xxx)",
        "example": "sk_live_abc123",
    },
}


def _detect_format(api_key: str) -> str | None:
    """Détecte automatiquement le format d'une clé API."""
    for format_name, format_info in API_KEY_FORMATS.items():
        if re.match(format_info["pattern"], api_key, re.IGNORECASE):
            return format_name
    return None


def _validate_with_format(api_key: str, format_name: str) -> tuple[bool, str]:
    """Valide une clé API selon un format spécifique."""
    if format_name not in API_KEY_FORMATS:
        return False, f"Format inconnu: {format_name}"

    format_info = API_KEY_FORMATS[format_name]
    if not re.match(format_info["pattern"], api_key, re.IGNORECASE):
        return False, f"Format invalide. Attendu: {format_info['description']}"

    return True, ""


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une clé API selon son format.

    Formats supportés:
    - uuid: UUID v4
    - hex32: 32 caractères hexadécimaux
    - hex64: 64 caractères hexadécimaux
    - base64: Encodage Base64
    - alphanumeric: Alphanumérique simple
    - prefixed: Préfixe avec underscore (sk_live_xxx)

    Args:
        inputs: {
            "api_key": string,  # Clé API à valider
            "format": string,  # Format attendu (optionnel, auto-détection)
            "min_length": number,  # Longueur minimale (défaut: 16)
            "max_length": number,  # Longueur maximale (défaut: 256)
        }

    Returns:
        {
            "is_valid": boolean,  # True si clé valide
            "detected_format": string,  # Format détecté
            "length": number,  # Longueur de la clé
            "prefix": string,  # Préfixe si applicable
            "error": string,  # Message d'erreur si invalide
        }
    """
    api_key = inputs.get("api_key", "")
    format_hint = inputs.get("format", "")
    min_length = inputs.get("min_length", 16)
    max_length = inputs.get("max_length", 256)

    # Valeur vide
    if not api_key:
        return {
            "is_valid": False,
            "detected_format": None,
            "length": 0,
            "prefix": None,
            "error": "Clé API requise"
        }

    api_key = str(api_key).strip()
    length = len(api_key)

    # Vérification longueur
    if length < min_length:
        return {
            "is_valid": False,
            "detected_format": None,
            "length": length,
            "prefix": None,
            "error": f"Clé trop courte (minimum {min_length} caractères)"
        }

    if length > max_length:
        return {
            "is_valid": False,
            "detected_format": None,
            "length": length,
            "prefix": None,
            "error": f"Clé trop longue (maximum {max_length} caractères)"
        }

    # Extraction du préfixe si applicable
    prefix = None
    if "_" in api_key:
        prefix = api_key.split("_")[0]

    # Validation selon format
    if format_hint:
        is_valid, error = _validate_with_format(api_key, format_hint.lower())
        if not is_valid:
            return {
                "is_valid": False,
                "detected_format": format_hint.lower(),
                "length": length,
                "prefix": prefix,
                "error": error
            }
        detected_format = format_hint.lower()
    else:
        detected_format = _detect_format(api_key)

    # Vérification de caractères valides (si pas de format détecté)
    if not detected_format:
        # Accepter au moins alphanumérique avec quelques caractères spéciaux
        if not re.match(r'^[A-Za-z0-9_\-+/=]+$', api_key):
            return {
                "is_valid": False,
                "detected_format": None,
                "length": length,
                "prefix": prefix,
                "error": "Caractères non autorisés dans la clé"
            }

    return {
        "is_valid": True,
        "detected_format": detected_format,
        "length": length,
        "prefix": prefix,
        "error": None
    }
