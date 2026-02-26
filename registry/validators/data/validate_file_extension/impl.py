"""
Implémentation du sous-programme : validate_file_extension

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 18+ endroits dans le codebase
"""

from typing import Dict, Any


# Extensions dangereuses (exécutables, scripts)
DANGEROUS_EXTENSIONS = {
    "exe", "bat", "cmd", "com", "msi", "scr", "pif",  # Windows
    "sh", "bash", "zsh", "csh",  # Unix shells
    "ps1", "psm1", "psd1",  # PowerShell
    "vbs", "vbe", "js", "jse", "wsf", "wsh",  # Scripts
    "jar", "class",  # Java
    "py", "pyc", "pyo",  # Python (contexte upload)
    "php", "phtml", "php3", "php4", "php5",  # PHP
    "asp", "aspx", "cer",  # ASP
    "dll", "so", "dylib",  # Libraries
    "reg",  # Registry
}

# Catégories d'extensions
EXTENSION_CATEGORIES = {
    "image": {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tiff", "tif"},
    "document": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "txt", "rtf"},
    "archive": {"zip", "rar", "7z", "tar", "gz", "bz2", "xz"},
    "audio": {"mp3", "wav", "ogg", "flac", "aac", "wma", "m4a"},
    "video": {"mp4", "avi", "mkv", "mov", "wmv", "flv", "webm"},
    "data": {"json", "xml", "csv", "yaml", "yml"},
}


def _extract_extension(filename: str) -> str | None:
    """Extrait l'extension d'un nom de fichier."""
    if not filename:
        return None

    # Trouver le dernier point
    last_dot = filename.rfind('.')
    if last_dot == -1 or last_dot == len(filename) - 1:
        return None

    return filename[last_dot + 1:].lower()


def _get_category(extension: str) -> str | None:
    """Détermine la catégorie d'une extension."""
    for category, extensions in EXTENSION_CATEGORIES.items():
        if extension in extensions:
            return category
    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide l'extension d'un fichier.

    Args:
        inputs: {
            "filename": string,  # Nom du fichier à valider
            "allowed_extensions": array,  # Extensions autorisées (optionnel)
            "blocked_extensions": array,  # Extensions bloquées (optionnel)
            "allow_dangerous": boolean,  # Autoriser extensions dangereuses (défaut: false)
        }

    Returns:
        {
            "is_valid": boolean,  # True si extension valide
            "extension": string,  # Extension extraite
            "category": string,  # Catégorie (image, document, etc.)
            "is_dangerous": boolean,  # True si extension dangereuse
            "error": string,  # Message d'erreur si invalide
        }
    """
    filename = inputs.get("filename", "")
    allowed_extensions = inputs.get("allowed_extensions")
    blocked_extensions = inputs.get("blocked_extensions", [])
    allow_dangerous = inputs.get("allow_dangerous", False)

    # Valeur vide
    if not filename:
        return {
            "is_valid": False,
            "extension": None,
            "category": None,
            "is_dangerous": None,
            "error": "Nom de fichier requis"
        }

    # Extraction de l'extension
    extension = _extract_extension(str(filename))

    if extension is None:
        return {
            "is_valid": False,
            "extension": None,
            "category": None,
            "is_dangerous": None,
            "error": "Pas d'extension trouvée"
        }

    # Catégorie
    category = _get_category(extension)

    # Vérification extension dangereuse
    is_dangerous = extension in DANGEROUS_EXTENSIONS

    if is_dangerous and not allow_dangerous:
        return {
            "is_valid": False,
            "extension": extension,
            "category": category,
            "is_dangerous": True,
            "error": f"Extension dangereuse non autorisée: .{extension}"
        }

    # Vérification extensions bloquées
    if blocked_extensions:
        blocked_lower = [ext.lower().lstrip('.') for ext in blocked_extensions]
        if extension in blocked_lower:
            return {
                "is_valid": False,
                "extension": extension,
                "category": category,
                "is_dangerous": is_dangerous,
                "error": f"Extension bloquée: .{extension}"
            }

    # Vérification extensions autorisées
    if allowed_extensions:
        allowed_lower = [ext.lower().lstrip('.') for ext in allowed_extensions]
        if extension not in allowed_lower:
            return {
                "is_valid": False,
                "extension": extension,
                "category": category,
                "is_dangerous": is_dangerous,
                "error": f"Extension non autorisée. Autorisées: {', '.join('.' + e for e in allowed_lower)}"
            }

    return {
        "is_valid": True,
        "extension": extension,
        "category": category,
        "is_dangerous": is_dangerous,
        "error": None
    }
