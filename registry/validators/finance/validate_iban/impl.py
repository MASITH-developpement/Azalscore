"""
Implémentation du sous-programme : validate_iban

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Longueurs IBAN par pays (ISO 13616)
IBAN_LENGTHS = {
    "AL": 28, "AD": 24, "AT": 20, "AZ": 28, "BH": 22, "BY": 28, "BE": 16,
    "BA": 20, "BR": 29, "BG": 22, "CR": 22, "HR": 21, "CY": 28, "CZ": 24,
    "DK": 18, "DO": 28, "EG": 29, "SV": 28, "EE": 20, "FO": 18, "FI": 18,
    "FR": 27, "GE": 22, "DE": 22, "GI": 23, "GR": 27, "GL": 18, "GT": 28,
    "HU": 28, "IS": 26, "IQ": 23, "IE": 22, "IL": 23, "IT": 27, "JO": 30,
    "KZ": 20, "XK": 20, "KW": 30, "LV": 21, "LB": 28, "LI": 21, "LT": 20,
    "LU": 20, "MK": 19, "MT": 31, "MR": 27, "MU": 30, "MC": 27, "MD": 24,
    "ME": 22, "NL": 18, "NO": 15, "PK": 24, "PS": 29, "PL": 28, "PT": 25,
    "QA": 29, "RO": 24, "LC": 32, "SM": 27, "ST": 25, "SA": 24, "RS": 22,
    "SC": 31, "SK": 24, "SI": 19, "ES": 24, "SE": 24, "CH": 21, "TL": 23,
    "TN": 24, "TR": 26, "UA": 29, "AE": 23, "GB": 22, "VA": 22, "VG": 24,
}


def _normalize_iban(iban: str) -> str:
    """Normalise un IBAN (supprime espaces et tirets, met en majuscules)."""
    return re.sub(r'[\s\-]', '', iban.upper())


def _validate_iban_checksum(iban: str) -> bool:
    """
    Vérifie le checksum IBAN selon ISO 7064 (MOD 97-10).

    1. Déplacer les 4 premiers caractères à la fin
    2. Convertir les lettres en chiffres (A=10, B=11, ..., Z=35)
    3. Calculer modulo 97, doit être égal à 1
    """
    # Réorganiser: déplacer les 4 premiers caractères à la fin
    rearranged = iban[4:] + iban[:4]

    # Convertir les lettres en chiffres
    numeric_string = ""
    for char in rearranged:
        if char.isalpha():
            numeric_string += str(ord(char) - ord('A') + 10)
        else:
            numeric_string += char

    # Calculer modulo 97
    return int(numeric_string) % 97 == 1


def _extract_bank_code(iban: str, country_code: str) -> str:
    """Extrait le code banque selon le pays."""
    if country_code == "FR":
        # France: positions 5-9 (code banque 5 chiffres)
        return iban[4:9]
    elif country_code == "DE":
        # Allemagne: positions 5-12 (BLZ 8 chiffres)
        return iban[4:12]
    elif country_code == "GB":
        # UK: positions 5-8 (sort code dans le BBAN)
        return iban[4:8]
    elif country_code == "ES":
        # Espagne: positions 5-8 (code banque 4 chiffres)
        return iban[4:8]
    elif country_code == "IT":
        # Italie: positions 6-10 (code ABI 5 chiffres)
        return iban[5:10]
    elif country_code == "BE":
        # Belgique: positions 5-7 (code banque 3 chiffres)
        return iban[4:7]
    elif country_code == "NL":
        # Pays-Bas: positions 5-8 (code banque 4 caractères)
        return iban[4:8]
    elif country_code == "CH":
        # Suisse: positions 5-9 (clearing number 5 chiffres)
        return iban[4:9]
    else:
        # Par défaut: premiers caractères après le code pays et check digits
        return iban[4:8]


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro IBAN selon la norme ISO 13616.

    Args:
        inputs: {
            "iban": string,  # Numéro IBAN à valider
        }

    Returns:
        {
            "is_valid": boolean,  # True si IBAN valide
            "normalized_iban": string,  # IBAN normalisé (sans espaces, majuscules)
            "country_code": string,  # Code pays ISO 2 lettres
            "bank_code": string,  # Code banque extrait
            "error": string,  # Message d'erreur si invalide, None sinon
        }
    """
    iban = inputs.get("iban", "")

    # Valeur vide
    if not iban or not isinstance(iban, str):
        return {
            "is_valid": False,
            "normalized_iban": None,
            "country_code": None,
            "bank_code": None,
            "error": "IBAN requis"
        }

    # Normalisation
    normalized = _normalize_iban(iban)

    # Longueur minimale
    if len(normalized) < 15:
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": None,
            "bank_code": None,
            "error": "IBAN trop court"
        }

    # Extraction code pays
    country_code = normalized[:2]

    # Vérification que les 2 premiers caractères sont des lettres
    if not country_code.isalpha():
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": None,
            "bank_code": None,
            "error": "Code pays invalide (doit être 2 lettres)"
        }

    # Vérification que les caractères 3-4 sont des chiffres (check digits)
    check_digits = normalized[2:4]
    if not check_digits.isdigit():
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": country_code,
            "bank_code": None,
            "error": "Check digits invalides (positions 3-4 doivent être des chiffres)"
        }

    # Vérification longueur selon pays
    expected_length = IBAN_LENGTHS.get(country_code)
    if expected_length is None:
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": country_code,
            "bank_code": None,
            "error": f"Code pays '{country_code}' non reconnu"
        }

    if len(normalized) != expected_length:
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": country_code,
            "bank_code": None,
            "error": f"Longueur incorrecte pour {country_code}: attendu {expected_length}, reçu {len(normalized)}"
        }

    # Vérification caractères alphanumériques uniquement
    if not normalized.isalnum():
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": country_code,
            "bank_code": None,
            "error": "IBAN contient des caractères non alphanumériques"
        }

    # Vérification checksum MOD 97
    if not _validate_iban_checksum(normalized):
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": country_code,
            "bank_code": None,
            "error": "Checksum IBAN invalide"
        }

    # Extraction code banque
    bank_code = _extract_bank_code(normalized, country_code)

    return {
        "is_valid": True,
        "normalized_iban": normalized,
        "country_code": country_code,
        "bank_code": bank_code,
        "error": None
    }
