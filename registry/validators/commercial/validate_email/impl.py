"""
Implémentation du sous-programme : validate_email

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 40+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Pattern RFC 5322 simplifié pour validation email
# Couvre la grande majorité des cas valides
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"  # Local part
    r"@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"  # Domain
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"  # Subdomains
    r"\.[a-zA-Z]{2,}$"  # TLD (min 2 caractères)
)

# Domaines jetables connus (liste partielle pour référence)
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.email", "guerrillamail.com", "mailinator.com",
    "yopmail.com", "trashmail.com", "fakeinbox.com", "10minutemail.com",
    "getnada.com", "temp-mail.org"
}

# TLDs valides principaux (non exhaustif mais couvre les cas courants)
VALID_TLDS = {
    # Generic TLDs
    "com", "org", "net", "edu", "gov", "mil", "int",
    # Country TLDs (Europe)
    "fr", "de", "uk", "es", "it", "pt", "nl", "be", "ch", "at", "pl", "cz", "ie",
    "se", "dk", "no", "fi", "gr", "ro", "bg", "hu", "sk", "hr", "si", "ee", "lv", "lt",
    # Country TLDs (Other)
    "us", "ca", "au", "nz", "jp", "cn", "kr", "in", "br", "mx", "ru",
    # New gTLDs
    "io", "co", "app", "dev", "ai", "tech", "online", "store", "info", "biz", "pro",
    "email", "cloud", "digital", "solutions", "services", "consulting", "agency",
    "design", "studio", "media", "marketing", "finance", "legal", "health", "shop",
    "site", "website", "blog", "news", "tv", "fm", "eu", "asia", "africa"
}


def _normalize_email(email: str) -> str:
    """Normalise une adresse email (lowercase, strip)."""
    return email.strip().lower()


def _extract_parts(email: str) -> tuple[str, str] | None:
    """Extrait le local part et le domaine d'une adresse email."""
    if "@" not in email:
        return None

    parts = email.rsplit("@", 1)
    if len(parts) != 2:
        return None

    local_part, domain = parts
    if not local_part or not domain:
        return None

    return local_part, domain


def _validate_local_part(local_part: str) -> tuple[bool, str]:
    """Valide le local part d'une adresse email."""
    # Longueur max 64 caractères (RFC 5321)
    if len(local_part) > 64:
        return False, "La partie locale dépasse 64 caractères"

    # Ne peut pas commencer ou finir par un point
    if local_part.startswith(".") or local_part.endswith("."):
        return False, "La partie locale ne peut pas commencer ou finir par un point"

    # Pas de points consécutifs
    if ".." in local_part:
        return False, "La partie locale ne peut pas contenir deux points consécutifs"

    return True, ""


def _validate_domain(domain: str) -> tuple[bool, str, str]:
    """
    Valide le domaine d'une adresse email.

    Returns:
        (is_valid, error_message, tld)
    """
    # Longueur max 255 caractères
    if len(domain) > 255:
        return False, "Le domaine dépasse 255 caractères", ""

    # Doit contenir au moins un point (pour le TLD)
    if "." not in domain:
        return False, "Le domaine doit contenir un TLD", ""

    # Extraction du TLD
    tld = domain.rsplit(".", 1)[-1].lower()

    # TLD minimum 2 caractères
    if len(tld) < 2:
        return False, "Le TLD doit contenir au moins 2 caractères", tld

    # TLD uniquement lettres
    if not tld.isalpha():
        return False, "Le TLD doit contenir uniquement des lettres", tld

    # Vérification de chaque partie du domaine
    parts = domain.split(".")
    for part in parts:
        if not part:
            return False, "Le domaine contient des points consécutifs", tld

        if len(part) > 63:
            return False, "Chaque partie du domaine est limitée à 63 caractères", tld

        # Chaque partie doit être alphanumérique avec tirets possibles
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', part):
            if len(part) == 1:
                if not part.isalnum():
                    return False, "Les parties du domaine doivent être alphanumériques", tld
            else:
                return False, "Format de domaine invalide", tld

    return True, "", tld


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une adresse email selon RFC 5322.

    Vérifie:
    - Format général (local@domain)
    - Longueur des parties
    - Caractères autorisés
    - Structure du domaine
    - TLD valide

    Args:
        inputs: {
            "email": string,  # Adresse email à valider
            "check_disposable": boolean,  # Vérifier domaines jetables (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si email valide
            "normalized_email": string,  # Email normalisé (lowercase)
            "local_part": string,  # Partie locale (avant @)
            "domain": string,  # Domaine (après @)
            "tld": string,  # Top-level domain
            "is_disposable": boolean,  # True si domaine jetable détecté
            "error": string,  # Message d'erreur si invalide
        }
    """
    email = inputs.get("email", "")
    check_disposable = inputs.get("check_disposable", False)

    # Valeur vide
    if not email:
        return {
            "is_valid": False,
            "normalized_email": None,
            "local_part": None,
            "domain": None,
            "tld": None,
            "is_disposable": None,
            "error": "Adresse email requise"
        }

    # Conversion en string si nécessaire
    email = str(email)

    # Normalisation
    normalized = _normalize_email(email)

    # Longueur totale max 254 caractères (RFC 5321)
    if len(normalized) > 254:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "local_part": None,
            "domain": None,
            "tld": None,
            "is_disposable": None,
            "error": "L'adresse email dépasse 254 caractères"
        }

    # Extraction des parties
    parts = _extract_parts(normalized)
    if parts is None:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "local_part": None,
            "domain": None,
            "tld": None,
            "is_disposable": None,
            "error": "Format d'adresse email invalide (manque @)"
        }

    local_part, domain = parts

    # Validation du local part
    is_valid_local, local_error = _validate_local_part(local_part)
    if not is_valid_local:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "local_part": local_part,
            "domain": domain,
            "tld": None,
            "is_disposable": None,
            "error": local_error
        }

    # Validation du domaine
    is_valid_domain, domain_error, tld = _validate_domain(domain)
    if not is_valid_domain:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "local_part": local_part,
            "domain": domain,
            "tld": tld if tld else None,
            "is_disposable": None,
            "error": domain_error
        }

    # Vérification avec regex complète
    if not EMAIL_PATTERN.match(normalized):
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "local_part": local_part,
            "domain": domain,
            "tld": tld,
            "is_disposable": None,
            "error": "Format d'adresse email non conforme"
        }

    # Vérification domaine jetable (optionnel)
    is_disposable = domain.lower() in DISPOSABLE_DOMAINS

    if check_disposable and is_disposable:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "local_part": local_part,
            "domain": domain,
            "tld": tld,
            "is_disposable": True,
            "error": "Les adresses email jetables ne sont pas acceptées"
        }

    return {
        "is_valid": True,
        "normalized_email": normalized,
        "local_part": local_part,
        "domain": domain,
        "tld": tld,
        "is_disposable": is_disposable,
        "error": None
    }
