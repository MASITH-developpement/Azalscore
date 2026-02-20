"""
Implémentation du sous-programme : validate_tva_intra

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 8+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Patterns de TVA par pays (Union Européenne)
TVA_PATTERNS = {
    "AT": (r"^ATU\d{8}$", "ATU + 8 chiffres"),  # Autriche
    "BE": (r"^BE[01]\d{9}$", "BE + 0/1 + 9 chiffres"),  # Belgique
    "BG": (r"^BG\d{9,10}$", "BG + 9-10 chiffres"),  # Bulgarie
    "CY": (r"^CY\d{8}[A-Z]$", "CY + 8 chiffres + lettre"),  # Chypre
    "CZ": (r"^CZ\d{8,10}$", "CZ + 8-10 chiffres"),  # Tchéquie
    "DE": (r"^DE\d{9}$", "DE + 9 chiffres"),  # Allemagne
    "DK": (r"^DK\d{8}$", "DK + 8 chiffres"),  # Danemark
    "EE": (r"^EE\d{9}$", "EE + 9 chiffres"),  # Estonie
    "EL": (r"^EL\d{9}$", "EL + 9 chiffres"),  # Grèce
    "ES": (r"^ES[A-Z0-9]\d{7}[A-Z0-9]$", "ES + lettre/chiffre + 7 chiffres + lettre/chiffre"),  # Espagne
    "FI": (r"^FI\d{8}$", "FI + 8 chiffres"),  # Finlande
    "FR": (r"^FR[A-Z0-9]{2}\d{9}$", "FR + 2 caractères + 9 chiffres (SIREN)"),  # France
    "HR": (r"^HR\d{11}$", "HR + 11 chiffres"),  # Croatie
    "HU": (r"^HU\d{8}$", "HU + 8 chiffres"),  # Hongrie
    "IE": (r"^IE\d{7}[A-Z]{1,2}$", "IE + 7 chiffres + 1-2 lettres"),  # Irlande
    "IT": (r"^IT\d{11}$", "IT + 11 chiffres"),  # Italie
    "LT": (r"^LT(\d{9}|\d{12})$", "LT + 9 ou 12 chiffres"),  # Lituanie
    "LU": (r"^LU\d{8}$", "LU + 8 chiffres"),  # Luxembourg
    "LV": (r"^LV\d{11}$", "LV + 11 chiffres"),  # Lettonie
    "MT": (r"^MT\d{8}$", "MT + 8 chiffres"),  # Malte
    "NL": (r"^NL\d{9}B\d{2}$", "NL + 9 chiffres + B + 2 chiffres"),  # Pays-Bas
    "PL": (r"^PL\d{10}$", "PL + 10 chiffres"),  # Pologne
    "PT": (r"^PT\d{9}$", "PT + 9 chiffres"),  # Portugal
    "RO": (r"^RO\d{2,10}$", "RO + 2-10 chiffres"),  # Roumanie
    "SE": (r"^SE\d{12}$", "SE + 12 chiffres"),  # Suède
    "SI": (r"^SI\d{8}$", "SI + 8 chiffres"),  # Slovénie
    "SK": (r"^SK\d{10}$", "SK + 10 chiffres"),  # Slovaquie
    "GB": (r"^GB(\d{9}|\d{12}|GD\d{3}|HA\d{3})$", "GB + 9/12 chiffres ou GD/HA + 3 chiffres"),  # UK (historique)
    "XI": (r"^XI\d{9,12}$", "XI + 9-12 chiffres"),  # Irlande du Nord (post-Brexit)
}


def _normalize_tva(tva: str) -> str:
    """Normalise un numéro de TVA (supprime espaces, tirets, met en majuscules)."""
    return re.sub(r'[\s\-\.]', '', tva.upper())


def _validate_french_tva(tva: str) -> tuple[bool, str]:
    """
    Validation spécifique pour TVA française.

    Format: FR + clé (2 caractères) + SIREN (9 chiffres)
    La clé est calculée à partir du SIREN.
    """
    if len(tva) != 13:
        return False, f"TVA française doit avoir 13 caractères (reçu: {len(tva)})"

    key = tva[2:4]
    siren = tva[4:13]

    # Le SIREN doit être numérique
    if not siren.isdigit():
        return False, "Le SIREN (9 derniers chiffres) doit être numérique"

    # Calcul de la clé de validation
    # Formule: clé = (12 + 3 * (SIREN modulo 97)) modulo 97
    siren_int = int(siren)
    expected_key = (12 + 3 * (siren_int % 97)) % 97

    # La clé peut être numérique ou alphanumérique
    if key.isdigit():
        if int(key) != expected_key:
            return False, f"Clé de contrôle invalide (attendu: {expected_key:02d})"
    else:
        # Pour les clés alphanumériques (cas particuliers)
        # On valide juste le format
        if not key.isalnum():
            return False, "Clé de contrôle doit être alphanumérique"

    return True, ""


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro de TVA intracommunautaire.

    Supporte tous les pays de l'Union Européenne.

    Args:
        inputs: {
            "tva": string,  # Numéro de TVA à valider
            "country": string,  # Code pays ISO (optionnel, auto-détecté)
        }

    Returns:
        {
            "is_valid": boolean,  # True si TVA valide
            "normalized_tva": string,  # TVA normalisée
            "country_code": string,  # Code pays ISO
            "country_name": string,  # Nom du pays
            "local_number": string,  # Numéro sans préfixe pays
            "error": string,  # Message d'erreur si invalide
        }
    """
    tva = inputs.get("tva", "")
    country_hint = inputs.get("country", "")

    # Valeur vide
    if not tva:
        return {
            "is_valid": False,
            "normalized_tva": None,
            "country_code": None,
            "country_name": None,
            "local_number": None,
            "error": "Numéro de TVA requis"
        }

    # Normalisation
    normalized = _normalize_tva(str(tva))

    # Longueur minimale
    if len(normalized) < 4:
        return {
            "is_valid": False,
            "normalized_tva": normalized,
            "country_code": None,
            "country_name": None,
            "local_number": None,
            "error": "Numéro de TVA trop court"
        }

    # Extraction du code pays
    country_code = normalized[:2]

    # Vérification que les 2 premiers caractères sont des lettres
    if not country_code.isalpha():
        return {
            "is_valid": False,
            "normalized_tva": normalized,
            "country_code": None,
            "country_name": None,
            "local_number": None,
            "error": "Le numéro de TVA doit commencer par un code pays (2 lettres)"
        }

    # Vérification du pays dans la liste UE
    if country_code not in TVA_PATTERNS:
        return {
            "is_valid": False,
            "normalized_tva": normalized,
            "country_code": country_code,
            "country_name": None,
            "local_number": normalized[2:],
            "error": f"Code pays '{country_code}' non reconnu dans l'UE"
        }

    pattern, format_desc = TVA_PATTERNS[country_code]
    local_number = normalized[2:]

    # Vérification du format
    if not re.match(pattern, normalized):
        return {
            "is_valid": False,
            "normalized_tva": normalized,
            "country_code": country_code,
            "country_name": _get_country_name(country_code),
            "local_number": local_number,
            "error": f"Format invalide pour {country_code}. Attendu: {format_desc}"
        }

    # Validation spécifique pour la France
    if country_code == "FR":
        is_valid, error_msg = _validate_french_tva(normalized)
        if not is_valid:
            return {
                "is_valid": False,
                "normalized_tva": normalized,
                "country_code": country_code,
                "country_name": "France",
                "local_number": local_number,
                "error": error_msg
            }

    return {
        "is_valid": True,
        "normalized_tva": normalized,
        "country_code": country_code,
        "country_name": _get_country_name(country_code),
        "local_number": local_number,
        "error": None
    }


def _get_country_name(code: str) -> str:
    """Retourne le nom du pays pour un code ISO."""
    country_names = {
        "AT": "Autriche", "BE": "Belgique", "BG": "Bulgarie", "CY": "Chypre",
        "CZ": "Tchéquie", "DE": "Allemagne", "DK": "Danemark", "EE": "Estonie",
        "EL": "Grèce", "ES": "Espagne", "FI": "Finlande", "FR": "France",
        "HR": "Croatie", "HU": "Hongrie", "IE": "Irlande", "IT": "Italie",
        "LT": "Lituanie", "LU": "Luxembourg", "LV": "Lettonie", "MT": "Malte",
        "NL": "Pays-Bas", "PL": "Pologne", "PT": "Portugal", "RO": "Roumanie",
        "SE": "Suède", "SI": "Slovénie", "SK": "Slovaquie", "GB": "Royaume-Uni",
        "XI": "Irlande du Nord",
    }
    return country_names.get(code, "Inconnu")
