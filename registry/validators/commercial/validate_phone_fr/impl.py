"""
Implémentation du sous-programme : validate_phone_fr

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 25+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Préfixes téléphoniques français par type
PHONE_PREFIXES = {
    # Fixes géographiques (01-05)
    "01": {"type": "fixe", "region": "Île-de-France"},
    "02": {"type": "fixe", "region": "Nord-Ouest"},
    "03": {"type": "fixe", "region": "Nord-Est"},
    "04": {"type": "fixe", "region": "Sud-Est"},
    "05": {"type": "fixe", "region": "Sud-Ouest"},

    # Mobiles (06, 07)
    "06": {"type": "mobile", "region": None},
    "07": {"type": "mobile", "region": None},

    # Services spéciaux
    "08": {"type": "special", "region": None},  # Numéros spéciaux (gratuits, surtaxés)
    "09": {"type": "voip", "region": None},  # VoIP / Box internet
}

# Préfixes DOM-TOM
DOM_TOM_PREFIXES = {
    "0590": "Guadeloupe",
    "0594": "Guyane",
    "0596": "Martinique",
    "0262": "Réunion",
    "0269": "Mayotte",
    "0508": "Saint-Pierre-et-Miquelon",
}

# Indicatifs internationaux reconnus
COUNTRY_CODES = {
    "+33": "France",
    "0033": "France",
}


def _normalize_phone(phone: str) -> str:
    """
    Normalise un numéro de téléphone français.

    Supprime espaces, points, tirets et parenthèses.
    Convertit +33 ou 0033 en 0.
    """
    # Suppression des caractères de formatage
    cleaned = re.sub(r'[\s\.\-\(\)]', '', phone)

    # Gestion de l'indicatif international français
    if cleaned.startswith("+33"):
        cleaned = "0" + cleaned[3:]
    elif cleaned.startswith("0033"):
        cleaned = "0" + cleaned[4:]

    return cleaned


def _format_phone(phone: str) -> str:
    """
    Formate un numéro français normalisé (10 chiffres) en XX XX XX XX XX.
    """
    if len(phone) != 10:
        return phone

    return f"{phone[0:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]} {phone[8:10]}"


def _get_phone_type(prefix: str) -> tuple[str, str | None]:
    """
    Détermine le type de numéro et la région éventuelle.

    Returns:
        (type, region)
    """
    if prefix in PHONE_PREFIXES:
        info = PHONE_PREFIXES[prefix]
        return info["type"], info["region"]

    return "inconnu", None


def _check_dom_tom(phone: str) -> str | None:
    """Vérifie si le numéro appartient à un DOM-TOM."""
    for prefix, territory in DOM_TOM_PREFIXES.items():
        if phone.startswith(prefix):
            return territory
    return None


def _validate_special_number(phone: str) -> tuple[bool, str, str | None]:
    """
    Valide les numéros spéciaux (08xx).

    Returns:
        (is_valid, subtype, error)
    """
    if not phone.startswith("08"):
        return True, None, None

    # 0800-0805: Numéros gratuits
    if phone[2:4] in ["00", "01", "02", "03", "04", "05"]:
        return True, "gratuit", None

    # 0806-0809: Tarif normal (prix d'un appel local)
    if phone[2:4] in ["06", "07", "08", "09"]:
        return True, "prix_appel_local", None

    # 081x: Tarif majoré
    if phone[2] == "1":
        return True, "majore", None

    # 082x: Tarif surtaxé
    if phone[2] == "2":
        return True, "surtaxe", None

    # 089x: Numéros surtaxés (adultes, jeux, etc.)
    if phone[2] == "9":
        return True, "surtaxe_premium", None

    return True, "special", None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro de téléphone français.

    Formats acceptés:
    - 0X XX XX XX XX (10 chiffres)
    - +33 X XX XX XX XX (indicatif international)
    - 0033 X XX XX XX XX (indicatif international alternatif)

    Args:
        inputs: {
            "phone": string,  # Numéro de téléphone à valider
            "allow_special": boolean,  # Autoriser numéros spéciaux 08 (optionnel, défaut: true)
        }

    Returns:
        {
            "is_valid": boolean,  # True si numéro valide
            "normalized_phone": string,  # Numéro normalisé (10 chiffres)
            "formatted_phone": string,  # Numéro formaté (XX XX XX XX XX)
            "international_format": string,  # Format international (+33 X XX XX XX XX)
            "phone_type": string,  # Type: fixe, mobile, voip, special
            "region": string,  # Région géographique (fixes uniquement)
            "territory": string,  # DOM-TOM le cas échéant
            "is_mobile": boolean,  # True si mobile
            "error": string,  # Message d'erreur si invalide
        }
    """
    phone = inputs.get("phone", "")
    allow_special = inputs.get("allow_special", True)

    # Valeur vide
    if not phone:
        return {
            "is_valid": False,
            "normalized_phone": None,
            "formatted_phone": None,
            "international_format": None,
            "phone_type": None,
            "region": None,
            "territory": None,
            "is_mobile": None,
            "error": "Numéro de téléphone requis"
        }

    # Conversion en string
    phone = str(phone)

    # Normalisation
    normalized = _normalize_phone(phone)

    # Vérification que tous les caractères sont des chiffres
    if not normalized.isdigit():
        return {
            "is_valid": False,
            "normalized_phone": normalized,
            "formatted_phone": None,
            "international_format": None,
            "phone_type": None,
            "region": None,
            "territory": None,
            "is_mobile": None,
            "error": "Le numéro de téléphone doit contenir uniquement des chiffres"
        }

    # Vérification longueur (10 chiffres pour France)
    if len(normalized) != 10:
        return {
            "is_valid": False,
            "normalized_phone": normalized,
            "formatted_phone": None,
            "international_format": None,
            "phone_type": None,
            "region": None,
            "territory": None,
            "is_mobile": None,
            "error": f"Le numéro français doit contenir 10 chiffres (reçu: {len(normalized)})"
        }

    # Vérification du préfixe (doit commencer par 0)
    if not normalized.startswith("0"):
        return {
            "is_valid": False,
            "normalized_phone": normalized,
            "formatted_phone": None,
            "international_format": None,
            "phone_type": None,
            "region": None,
            "territory": None,
            "is_mobile": None,
            "error": "Le numéro français doit commencer par 0"
        }

    # Extraction du préfixe (2 premiers chiffres)
    prefix = normalized[:2]

    # Vérification préfixe valide
    if prefix not in PHONE_PREFIXES:
        return {
            "is_valid": False,
            "normalized_phone": normalized,
            "formatted_phone": _format_phone(normalized),
            "international_format": None,
            "phone_type": None,
            "region": None,
            "territory": None,
            "is_mobile": None,
            "error": f"Préfixe téléphonique '{prefix}' non reconnu"
        }

    # Détermination du type
    phone_type, region = _get_phone_type(prefix)

    # Vérification DOM-TOM
    territory = _check_dom_tom(normalized)
    if territory:
        region = territory

    # Vérification numéros spéciaux
    if phone_type == "special":
        is_valid, subtype, error = _validate_special_number(normalized)
        if error:
            return {
                "is_valid": False,
                "normalized_phone": normalized,
                "formatted_phone": _format_phone(normalized),
                "international_format": None,
                "phone_type": phone_type,
                "region": None,
                "territory": None,
                "is_mobile": False,
                "error": error
            }

        if not allow_special:
            return {
                "is_valid": False,
                "normalized_phone": normalized,
                "formatted_phone": _format_phone(normalized),
                "international_format": None,
                "phone_type": f"special_{subtype}" if subtype else "special",
                "region": None,
                "territory": None,
                "is_mobile": False,
                "error": "Les numéros spéciaux (08xx) ne sont pas acceptés"
            }

        phone_type = f"special_{subtype}" if subtype else "special"

    # Formatage
    formatted = _format_phone(normalized)

    # Format international: +33 suivi du numéro sans le 0
    international = f"+33 {normalized[1:3]} {normalized[3:5]} {normalized[5:7]} {normalized[7:9]} {normalized[9:10]}"
    # Correction format: +33 X XX XX XX XX
    international = f"+33 {normalized[1]} {normalized[2:4]} {normalized[4:6]} {normalized[6:8]} {normalized[8:10]}"

    return {
        "is_valid": True,
        "normalized_phone": normalized,
        "formatted_phone": formatted,
        "international_format": international,
        "phone_type": phone_type,
        "region": region,
        "territory": territory,
        "is_mobile": phone_type == "mobile",
        "error": None
    }
