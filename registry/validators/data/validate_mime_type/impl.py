"""
Implémentation du sous-programme : validate_mime_type

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any


# Types MIME communs par catégorie
MIME_CATEGORIES = {
    "image": {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "image/svg+xml", "image/bmp", "image/tiff", "image/x-icon"
    },
    "document": {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "text/plain", "text/rtf"
    },
    "archive": {
        "application/zip", "application/x-rar-compressed",
        "application/x-7z-compressed", "application/x-tar",
        "application/gzip", "application/x-bzip2"
    },
    "audio": {
        "audio/mpeg", "audio/wav", "audio/ogg", "audio/flac",
        "audio/aac", "audio/webm", "audio/x-m4a"
    },
    "video": {
        "video/mp4", "video/x-msvideo", "video/x-matroska",
        "video/quicktime", "video/webm", "video/x-flv"
    },
    "data": {
        "application/json", "application/xml", "text/xml",
        "text/csv", "application/x-yaml", "text/yaml"
    },
}

# Types MIME dangereux
DANGEROUS_MIME_TYPES = {
    "application/x-msdownload",  # .exe
    "application/x-msdos-program",
    "application/x-sh",  # Shell scripts
    "application/x-php",
    "text/x-php",
    "application/x-httpd-php",
    "application/javascript",
    "text/javascript",
    "application/x-javascript",
}


def _get_category(mime_type: str) -> str | None:
    """Détermine la catégorie d'un type MIME."""
    mime_lower = mime_type.lower()
    for category, types in MIME_CATEGORIES.items():
        if mime_lower in types:
            return category

    # Catégorie générique basée sur le préfixe
    if mime_lower.startswith("image/"):
        return "image"
    elif mime_lower.startswith("video/"):
        return "video"
    elif mime_lower.startswith("audio/"):
        return "audio"
    elif mime_lower.startswith("text/"):
        return "text"

    return None


def _is_valid_mime_format(mime_type: str) -> bool:
    """Vérifie si le format MIME est valide (type/subtype)."""
    if not mime_type or "/" not in mime_type:
        return False

    parts = mime_type.split("/")
    if len(parts) != 2:
        return False

    type_part, subtype = parts
    if not type_part or not subtype:
        return False

    return True


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide le type MIME d'un fichier.

    Args:
        inputs: {
            "mime_type": string,  # Type MIME à valider
            "allowed_types": array,  # Types MIME autorisés (optionnel)
            "allowed_categories": array,  # Catégories autorisées (optionnel)
            "allow_dangerous": boolean,  # Autoriser types dangereux (défaut: false)
        }

    Returns:
        {
            "is_valid": boolean,  # True si type valide
            "normalized_type": string,  # Type MIME normalisé
            "category": string,  # Catégorie (image, document, etc.)
            "is_dangerous": boolean,  # True si type dangereux
            "error": string,  # Message d'erreur si invalide
        }
    """
    mime_type = inputs.get("mime_type", "")
    allowed_types = inputs.get("allowed_types")
    allowed_categories = inputs.get("allowed_categories")
    allow_dangerous = inputs.get("allow_dangerous", False)

    # Valeur vide
    if not mime_type:
        return {
            "is_valid": False,
            "normalized_type": None,
            "category": None,
            "is_dangerous": None,
            "error": "Type MIME requis"
        }

    # Normalisation
    normalized = str(mime_type).strip().lower()

    # Vérification format
    if not _is_valid_mime_format(normalized):
        return {
            "is_valid": False,
            "normalized_type": normalized,
            "category": None,
            "is_dangerous": None,
            "error": "Format MIME invalide (attendu: type/subtype)"
        }

    # Catégorie
    category = _get_category(normalized)

    # Vérification type dangereux
    is_dangerous = normalized in DANGEROUS_MIME_TYPES

    if is_dangerous and not allow_dangerous:
        return {
            "is_valid": False,
            "normalized_type": normalized,
            "category": category,
            "is_dangerous": True,
            "error": f"Type MIME dangereux non autorisé: {normalized}"
        }

    # Vérification types autorisés
    if allowed_types:
        allowed_lower = [t.lower() for t in allowed_types]
        if normalized not in allowed_lower:
            return {
                "is_valid": False,
                "normalized_type": normalized,
                "category": category,
                "is_dangerous": is_dangerous,
                "error": f"Type MIME non autorisé. Autorisés: {', '.join(allowed_lower)}"
            }

    # Vérification catégories autorisées
    if allowed_categories and category:
        allowed_cat_lower = [c.lower() for c in allowed_categories]
        if category not in allowed_cat_lower:
            return {
                "is_valid": False,
                "normalized_type": normalized,
                "category": category,
                "is_dangerous": is_dangerous,
                "error": f"Catégorie non autorisée. Autorisées: {', '.join(allowed_cat_lower)}"
            }

    return {
        "is_valid": True,
        "normalized_type": normalized,
        "category": category,
        "is_dangerous": is_dangerous,
        "error": None
    }
