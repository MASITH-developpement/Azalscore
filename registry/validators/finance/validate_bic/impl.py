"""
Implémentation du sous-programme : validate_bic

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Codes pays ISO 3166-1 alpha-2 valides (liste partielle des principaux)
VALID_COUNTRY_CODES = {
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT",
    "AU", "AW", "AX", "AZ", "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI",
    "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS", "BT", "BV", "BW", "BY",
    "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN",
    "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM",
    "DO", "DZ", "EC", "EE", "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK",
    "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL",
    "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM",
    "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR",
    "IS", "IT", "JE", "JM", "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN",
    "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC", "LI", "LK", "LR", "LS",
    "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK",
    "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW",
    "MX", "MY", "MZ", "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP",
    "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM",
    "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM",
    "SN", "SO", "SR", "SS", "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF",
    "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TR", "TT", "TV", "TW",
    "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI",
    "VN", "VU", "WF", "WS", "XK", "YE", "YT", "ZA", "ZM", "ZW",
}


def _normalize_bic(bic: str) -> str:
    """Normalise un BIC (supprime espaces, met en majuscules)."""
    return re.sub(r'\s', '', bic.upper())


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un code BIC/SWIFT selon la norme ISO 9362.

    Format BIC: AAAABBCCXXX
    - AAAA: Code banque (4 lettres)
    - BB: Code pays (2 lettres ISO 3166-1)
    - CC: Code localisation (2 caractères alphanumériques)
    - XXX: Code agence (3 caractères alphanumériques, optionnel)

    Args:
        inputs: {
            "bic": string,  # Code BIC/SWIFT à valider
        }

    Returns:
        {
            "is_valid": boolean,  # True si BIC valide
            "normalized_bic": string,  # BIC normalisé
            "bank_code": string,  # Code banque (4 premiers caractères)
            "country_code": string,  # Code pays ISO
            "location_code": string,  # Code localisation
            "branch_code": string,  # Code agence (ou "XXX" si absent)
            "is_primary_office": boolean,  # True si agence principale (XXX ou absent)
            "error": string,  # Message d'erreur si invalide
        }
    """
    bic = inputs.get("bic", "")

    # Valeur vide
    if not bic or not isinstance(bic, str):
        return {
            "is_valid": False,
            "normalized_bic": None,
            "bank_code": None,
            "country_code": None,
            "location_code": None,
            "branch_code": None,
            "is_primary_office": None,
            "error": "BIC requis"
        }

    # Normalisation
    normalized = _normalize_bic(bic)

    # Longueur: 8 ou 11 caractères
    if len(normalized) not in (8, 11):
        return {
            "is_valid": False,
            "normalized_bic": normalized,
            "bank_code": None,
            "country_code": None,
            "location_code": None,
            "branch_code": None,
            "is_primary_office": None,
            "error": f"Longueur BIC invalide: attendu 8 ou 11 caractères, reçu {len(normalized)}"
        }

    # Extraction des composants
    bank_code = normalized[:4]
    country_code = normalized[4:6]
    location_code = normalized[6:8]
    branch_code = normalized[8:11] if len(normalized) == 11 else "XXX"

    # Vérification code banque (4 lettres uniquement)
    if not bank_code.isalpha():
        return {
            "is_valid": False,
            "normalized_bic": normalized,
            "bank_code": bank_code,
            "country_code": country_code,
            "location_code": location_code,
            "branch_code": branch_code,
            "is_primary_office": None,
            "error": "Code banque invalide (4 premières positions doivent être des lettres)"
        }

    # Vérification code pays
    if not country_code.isalpha():
        return {
            "is_valid": False,
            "normalized_bic": normalized,
            "bank_code": bank_code,
            "country_code": country_code,
            "location_code": location_code,
            "branch_code": branch_code,
            "is_primary_office": None,
            "error": "Code pays invalide (positions 5-6 doivent être des lettres)"
        }

    if country_code not in VALID_COUNTRY_CODES:
        return {
            "is_valid": False,
            "normalized_bic": normalized,
            "bank_code": bank_code,
            "country_code": country_code,
            "location_code": location_code,
            "branch_code": branch_code,
            "is_primary_office": None,
            "error": f"Code pays '{country_code}' non reconnu (ISO 3166-1)"
        }

    # Vérification code localisation (alphanumériques)
    if not location_code.isalnum():
        return {
            "is_valid": False,
            "normalized_bic": normalized,
            "bank_code": bank_code,
            "country_code": country_code,
            "location_code": location_code,
            "branch_code": branch_code,
            "is_primary_office": None,
            "error": "Code localisation invalide (positions 7-8 doivent être alphanumériques)"
        }

    # Vérification code agence si présent
    if len(normalized) == 11 and not branch_code.isalnum():
        return {
            "is_valid": False,
            "normalized_bic": normalized,
            "bank_code": bank_code,
            "country_code": country_code,
            "location_code": location_code,
            "branch_code": branch_code,
            "is_primary_office": None,
            "error": "Code agence invalide (positions 9-11 doivent être alphanumériques)"
        }

    # Déterminer si c'est le siège principal
    is_primary = branch_code == "XXX" or len(normalized) == 8

    # BIC 8 caractères: normaliser en ajoutant XXX
    if len(normalized) == 8:
        normalized = normalized + "XXX"

    return {
        "is_valid": True,
        "normalized_bic": normalized,
        "bank_code": bank_code,
        "country_code": country_code,
        "location_code": location_code,
        "branch_code": branch_code,
        "is_primary_office": is_primary,
        "error": None
    }
