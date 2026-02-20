"""
Implémentation du sous-programme : validate_social_security_number

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 10+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Départements métropolitains valides (01-95, sauf 20 qui est Corse)
# 2A et 2B pour la Corse
# 97x et 98x pour DOM-TOM
VALID_DEPARTMENTS = (
    [f"{i:02d}" for i in range(1, 96) if i != 20] +
    ["2A", "2B"] +
    ["971", "972", "973", "974", "975", "976", "977", "978", "984", "986", "987", "988"]
)

# Codes pays étrangers (99xxx)
FOREIGN_COUNTRY_PREFIX = "99"


def _normalize_ssn(ssn: str) -> str:
    """Normalise un NIR (supprime espaces, points, tirets)."""
    return re.sub(r'[\s\.\-]', '', ssn.upper())


def _validate_key(ssn_without_key: str, provided_key: str) -> tuple[bool, int]:
    """
    Valide la clé de contrôle du NIR.

    La clé est calculée comme: 97 - (NIR modulo 97)

    Returns:
        (is_valid, expected_key)
    """
    # Conversion des lettres corses
    ssn_numeric = ssn_without_key.replace('A', '0').replace('B', '0')

    # Pour les NIR avec lettres corses, ajustement du calcul
    if 'A' in ssn_without_key:
        ssn_int = int(ssn_numeric) - 1000000
    elif 'B' in ssn_without_key:
        ssn_int = int(ssn_numeric) - 2000000
    else:
        ssn_int = int(ssn_numeric)

    expected_key = 97 - (ssn_int % 97)

    if provided_key.isdigit():
        return int(provided_key) == expected_key, expected_key

    return False, expected_key


def _extract_gender(code: str) -> str:
    """Extrait le genre depuis le code sexe."""
    if code == "1":
        return "homme"
    elif code == "2":
        return "femme"
    elif code == "3":
        return "homme_étranger"  # Né à l'étranger (temporaire)
    elif code == "4":
        return "femme_étranger"  # Né à l'étranger (temporaire)
    return "inconnu"


def _extract_birth_info(ssn: str) -> dict:
    """
    Extrait les informations de naissance du NIR.

    Format: SAAMMDDPPPCCC
    - S: Sexe (1=H, 2=F)
    - AA: Année de naissance
    - MM: Mois de naissance
    - DD: Département (ou 99 pour étranger)
    - PPP: Code commune/pays
    - CCC: Numéro d'ordre
    """
    return {
        "gender_code": ssn[0],
        "birth_year_short": ssn[1:3],
        "birth_month": ssn[3:5],
        "department": ssn[5:7] if ssn[5:7].isdigit() else ssn[5:7],
        "commune": ssn[7:10],
        "order": ssn[10:13],
    }


def _validate_month(month_str: str) -> tuple[bool, str]:
    """Valide le mois de naissance."""
    if not month_str.isdigit():
        return False, "Mois de naissance invalide"

    month = int(month_str)

    # Mois spéciaux: 20-30/50 pour estimation administrative, 31-42 pour adoption
    if month == 0:
        return False, "Mois de naissance invalide (00)"

    if 1 <= month <= 12:
        return True, ""

    if 20 <= month <= 30 or 50 <= month <= 99:
        return True, ""  # Mois d'estimation

    if 31 <= month <= 42:
        return True, ""  # Adoption

    return False, f"Mois de naissance invalide ({month})"


def _get_birth_year_full(year_short: str) -> int:
    """
    Détermine l'année complète de naissance.

    Utilise une heuristique: années 00-30 -> 2000s, sinon 1900s
    """
    if not year_short.isdigit():
        return 0

    year = int(year_short)

    # Heuristique basée sur la date actuelle
    if year <= 30:
        return 2000 + year
    else:
        return 1900 + year


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro de sécurité sociale français (NIR).

    Format: S AA MM DD PPP CCC KK (15 chiffres)
    - S: Sexe (1=Homme, 2=Femme)
    - AA: Année de naissance
    - MM: Mois de naissance
    - DD: Département de naissance (ou 99 pour étranger)
    - PPP: Code commune ou pays
    - CCC: Numéro d'ordre
    - KK: Clé de contrôle (97 - NIR mod 97)

    Args:
        inputs: {
            "ssn": string,  # Numéro de sécurité sociale à valider
        }

    Returns:
        {
            "is_valid": boolean,  # True si NIR valide
            "normalized_ssn": string,  # NIR normalisé (15 caractères)
            "formatted_ssn": string,  # NIR formaté (S AA MM DD PPP CCC KK)
            "gender": string,  # Genre: homme, femme
            "gender_code": string,  # Code genre: 1, 2
            "birth_year": number,  # Année de naissance complète
            "birth_month": number,  # Mois de naissance
            "department": string,  # Département de naissance
            "is_foreign_born": boolean,  # Né à l'étranger
            "key": string,  # Clé de contrôle
            "error": string,  # Message d'erreur si invalide
        }
    """
    ssn = inputs.get("ssn", "")

    # Valeur vide
    if not ssn:
        return {
            "is_valid": False,
            "normalized_ssn": None,
            "formatted_ssn": None,
            "gender": None,
            "gender_code": None,
            "birth_year": None,
            "birth_month": None,
            "department": None,
            "is_foreign_born": None,
            "key": None,
            "error": "Numéro de sécurité sociale requis"
        }

    # Normalisation
    normalized = _normalize_ssn(str(ssn))

    # Longueur (15 caractères: 13 + 2 pour la clé)
    if len(normalized) != 15:
        return {
            "is_valid": False,
            "normalized_ssn": normalized,
            "formatted_ssn": None,
            "gender": None,
            "gender_code": None,
            "birth_year": None,
            "birth_month": None,
            "department": None,
            "is_foreign_born": None,
            "key": None,
            "error": f"Le NIR doit contenir 15 caractères (reçu: {len(normalized)})"
        }

    # Extraction des parties
    ssn_body = normalized[:13]
    ssn_key = normalized[13:15]

    # Vérification format général (chiffres + éventuellement A ou B pour Corse)
    if not re.match(r'^[12][0-9]{2}(0[1-9]|1[0-2]|[2-9][0-9])([0-9]{2}|2[AB])[0-9]{6}$', ssn_body):
        # Format plus permissif pour cas spéciaux
        if not re.match(r'^[1-8][0-9]{2}[0-9]{2}([0-9]{2}|2[AB])[0-9]{6}$', ssn_body):
            return {
                "is_valid": False,
                "normalized_ssn": normalized,
                "formatted_ssn": None,
                "gender": None,
                "gender_code": None,
                "birth_year": None,
                "birth_month": None,
                "department": None,
                "is_foreign_born": None,
                "key": ssn_key,
                "error": "Format du NIR invalide"
            }

    # Vérification de la clé
    if not ssn_key.isdigit():
        return {
            "is_valid": False,
            "normalized_ssn": normalized,
            "formatted_ssn": None,
            "gender": None,
            "gender_code": None,
            "birth_year": None,
            "birth_month": None,
            "department": None,
            "is_foreign_born": None,
            "key": ssn_key,
            "error": "La clé de contrôle doit être numérique"
        }

    # Extraction des informations
    info = _extract_birth_info(ssn_body)

    # Validation du mois
    is_valid_month, month_error = _validate_month(info["birth_month"])
    if not is_valid_month:
        return {
            "is_valid": False,
            "normalized_ssn": normalized,
            "formatted_ssn": None,
            "gender": _extract_gender(info["gender_code"]),
            "gender_code": info["gender_code"],
            "birth_year": None,
            "birth_month": None,
            "department": info["department"],
            "is_foreign_born": info["department"] == "99",
            "key": ssn_key,
            "error": month_error
        }

    # Validation de la clé
    is_valid_key, expected_key = _validate_key(ssn_body, ssn_key)
    if not is_valid_key:
        return {
            "is_valid": False,
            "normalized_ssn": normalized,
            "formatted_ssn": None,
            "gender": _extract_gender(info["gender_code"]),
            "gender_code": info["gender_code"],
            "birth_year": _get_birth_year_full(info["birth_year_short"]),
            "birth_month": int(info["birth_month"]) if info["birth_month"].isdigit() and 1 <= int(info["birth_month"]) <= 12 else None,
            "department": info["department"],
            "is_foreign_born": info["department"] == "99",
            "key": ssn_key,
            "error": f"Clé de contrôle invalide (attendu: {expected_key:02d})"
        }

    # Formatage: S AA MM DD PPP CCC KK
    formatted = f"{ssn_body[0]} {ssn_body[1:3]} {ssn_body[3:5]} {ssn_body[5:7]} {ssn_body[7:10]} {ssn_body[10:13]} {ssn_key}"

    # Mois de naissance (uniquement si standard 1-12)
    birth_month = None
    if info["birth_month"].isdigit():
        month_int = int(info["birth_month"])
        if 1 <= month_int <= 12:
            birth_month = month_int

    return {
        "is_valid": True,
        "normalized_ssn": normalized,
        "formatted_ssn": formatted,
        "gender": _extract_gender(info["gender_code"]),
        "gender_code": info["gender_code"],
        "birth_year": _get_birth_year_full(info["birth_year_short"]),
        "birth_month": birth_month,
        "department": info["department"],
        "is_foreign_born": info["department"] == "99",
        "key": ssn_key,
        "error": None
    }
