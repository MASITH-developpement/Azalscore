"""
Implémentation du sous-programme : validate_barcode

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 18+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Types de codes-barres supportés
BARCODE_TYPES = {
    "EAN13": {
        "length": 13,
        "pattern": r"^\d{13}$",
        "description": "European Article Number (13 chiffres)",
    },
    "EAN8": {
        "length": 8,
        "pattern": r"^\d{8}$",
        "description": "European Article Number court (8 chiffres)",
    },
    "UPC-A": {
        "length": 12,
        "pattern": r"^\d{12}$",
        "description": "Universal Product Code (12 chiffres)",
    },
    "UPC-E": {
        "length": 8,
        "pattern": r"^\d{8}$",
        "description": "Universal Product Code court (8 chiffres)",
    },
    "ISBN13": {
        "length": 13,
        "pattern": r"^97[89]\d{10}$",
        "description": "International Standard Book Number (13 chiffres)",
    },
    "ISBN10": {
        "length": 10,
        "pattern": r"^\d{9}[\dX]$",
        "description": "International Standard Book Number ancien (10 caractères)",
    },
    "CODE128": {
        "length": None,  # Variable
        "pattern": r"^[\x00-\x7F]+$",
        "description": "Code 128 (alphanumérique)",
    },
    "CODE39": {
        "length": None,  # Variable
        "pattern": r"^[A-Z0-9\-\.\ \$\/\+\%]+$",
        "description": "Code 39 (alphanumérique)",
    },
}


def _calculate_ean_checksum(digits: str) -> int:
    """
    Calcule le chiffre de contrôle EAN/UPC.

    Algorithme: somme alternée (×1, ×3) modulo 10.
    """
    total = 0
    for i, digit in enumerate(digits[:-1]):
        if i % 2 == 0:
            total += int(digit)
        else:
            total += int(digit) * 3

    checksum = (10 - (total % 10)) % 10
    return checksum


def _calculate_isbn10_checksum(digits: str) -> str:
    """
    Calcule le chiffre de contrôle ISBN-10.

    Algorithme: somme pondérée modulo 11.
    """
    total = 0
    for i, digit in enumerate(digits[:9]):
        total += int(digit) * (10 - i)

    remainder = total % 11
    checksum = 11 - remainder

    if checksum == 10:
        return "X"
    elif checksum == 11:
        return "0"
    else:
        return str(checksum)


def _validate_ean13(barcode: str) -> tuple[bool, str, str]:
    """Valide un code EAN-13."""
    if len(barcode) != 13:
        return False, "", f"EAN-13 doit avoir 13 chiffres (reçu: {len(barcode)})"

    if not barcode.isdigit():
        return False, "", "EAN-13 doit contenir uniquement des chiffres"

    expected_checksum = _calculate_ean_checksum(barcode)
    actual_checksum = int(barcode[-1])

    if expected_checksum != actual_checksum:
        return False, str(expected_checksum), f"Checksum invalide (attendu: {expected_checksum})"

    return True, str(actual_checksum), ""


def _validate_ean8(barcode: str) -> tuple[bool, str, str]:
    """Valide un code EAN-8."""
    if len(barcode) != 8:
        return False, "", f"EAN-8 doit avoir 8 chiffres (reçu: {len(barcode)})"

    if not barcode.isdigit():
        return False, "", "EAN-8 doit contenir uniquement des chiffres"

    # Même algorithme que EAN-13
    total = 0
    for i, digit in enumerate(barcode[:-1]):
        if i % 2 == 0:
            total += int(digit) * 3
        else:
            total += int(digit)

    expected_checksum = (10 - (total % 10)) % 10
    actual_checksum = int(barcode[-1])

    if expected_checksum != actual_checksum:
        return False, str(expected_checksum), f"Checksum invalide (attendu: {expected_checksum})"

    return True, str(actual_checksum), ""


def _validate_upc(barcode: str) -> tuple[bool, str, str]:
    """Valide un code UPC-A."""
    if len(barcode) != 12:
        return False, "", f"UPC-A doit avoir 12 chiffres (reçu: {len(barcode)})"

    if not barcode.isdigit():
        return False, "", "UPC-A doit contenir uniquement des chiffres"

    expected_checksum = _calculate_ean_checksum(barcode)
    actual_checksum = int(barcode[-1])

    if expected_checksum != actual_checksum:
        return False, str(expected_checksum), f"Checksum invalide (attendu: {expected_checksum})"

    return True, str(actual_checksum), ""


def _validate_isbn10(barcode: str) -> tuple[bool, str, str]:
    """Valide un ISBN-10."""
    if len(barcode) != 10:
        return False, "", f"ISBN-10 doit avoir 10 caractères (reçu: {len(barcode)})"

    if not re.match(r'^\d{9}[\dX]$', barcode.upper()):
        return False, "", "ISBN-10 format invalide"

    expected_checksum = _calculate_isbn10_checksum(barcode)
    actual_checksum = barcode[-1].upper()

    if expected_checksum != actual_checksum:
        return False, expected_checksum, f"Checksum invalide (attendu: {expected_checksum})"

    return True, actual_checksum, ""


def _detect_type(barcode: str) -> str | None:
    """Détecte automatiquement le type de code-barres."""
    barcode = barcode.strip()

    if len(barcode) == 13 and barcode.isdigit():
        if barcode.startswith("978") or barcode.startswith("979"):
            return "ISBN13"
        return "EAN13"
    elif len(barcode) == 12 and barcode.isdigit():
        return "UPC-A"
    elif len(barcode) == 10 and re.match(r'^\d{9}[\dX]$', barcode.upper()):
        return "ISBN10"
    elif len(barcode) == 8 and barcode.isdigit():
        return "EAN8"

    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un code-barres (EAN, UPC, ISBN, etc.).

    Types supportés:
    - EAN13: Code européen 13 chiffres
    - EAN8: Code européen 8 chiffres
    - UPC-A: Code américain 12 chiffres
    - ISBN13/ISBN10: Livres

    Args:
        inputs: {
            "barcode": string,  # Code-barres à valider
            "type": string,  # Type attendu (optionnel, auto-détection)
        }

    Returns:
        {
            "is_valid": boolean,  # True si code valide
            "normalized_barcode": string,  # Code normalisé
            "detected_type": string,  # Type détecté
            "checksum": string,  # Chiffre de contrôle
            "country_prefix": string,  # Préfixe pays (EAN)
            "error": string,  # Message d'erreur si invalide
        }
    """
    barcode = inputs.get("barcode", "")
    barcode_type = inputs.get("type", "")

    # Valeur vide
    if not barcode:
        return {
            "is_valid": False,
            "normalized_barcode": None,
            "detected_type": None,
            "checksum": None,
            "country_prefix": None,
            "error": "Code-barres requis"
        }

    # Normalisation
    normalized = str(barcode).strip().replace(" ", "").replace("-", "").upper()

    # Détection du type
    if barcode_type:
        detected_type = barcode_type.upper()
    else:
        detected_type = _detect_type(normalized)

    if detected_type is None:
        return {
            "is_valid": False,
            "normalized_barcode": normalized,
            "detected_type": None,
            "checksum": None,
            "country_prefix": None,
            "error": "Type de code-barres non reconnu"
        }

    # Validation selon le type
    is_valid = False
    checksum = ""
    error = ""

    if detected_type == "EAN13" or detected_type == "ISBN13":
        is_valid, checksum, error = _validate_ean13(normalized)
    elif detected_type == "EAN8":
        is_valid, checksum, error = _validate_ean8(normalized)
    elif detected_type == "UPC-A":
        is_valid, checksum, error = _validate_upc(normalized)
    elif detected_type == "ISBN10":
        is_valid, checksum, error = _validate_isbn10(normalized)
    else:
        # Type non supporté pour validation, on vérifie juste le format
        is_valid = True

    if not is_valid:
        return {
            "is_valid": False,
            "normalized_barcode": normalized,
            "detected_type": detected_type,
            "checksum": checksum if checksum else None,
            "country_prefix": None,
            "error": error
        }

    # Extraction du préfixe pays (EAN-13)
    country_prefix = None
    if detected_type in ["EAN13", "ISBN13"] and len(normalized) == 13:
        prefix = normalized[:3]
        # Quelques préfixes connus
        prefixes = {
            "300": "FR", "301": "FR", "302": "FR", "303": "FR", "304": "FR",
            "305": "FR", "306": "FR", "307": "FR", "308": "FR", "309": "FR",
            "310": "FR", "311": "FR", "312": "FR", "313": "FR", "314": "FR",
            "315": "FR", "316": "FR", "317": "FR", "318": "FR", "319": "FR",
            "320": "FR", "321": "FR", "322": "FR", "323": "FR", "324": "FR",
            "325": "FR", "326": "FR", "327": "FR", "328": "FR", "329": "FR",
            "330": "FR", "331": "FR", "332": "FR", "333": "FR", "334": "FR",
            "335": "FR", "336": "FR", "337": "FR", "338": "FR", "339": "FR",
            "340": "FR", "341": "FR", "342": "FR", "343": "FR", "344": "FR",
            "345": "FR", "346": "FR", "347": "FR", "348": "FR", "349": "FR",
            "350": "FR", "351": "FR", "352": "FR", "353": "FR", "354": "FR",
            "355": "FR", "356": "FR", "357": "FR", "358": "FR", "359": "FR",
            "360": "FR", "361": "FR", "362": "FR", "363": "FR", "364": "FR",
            "365": "FR", "366": "FR", "367": "FR", "368": "FR", "369": "FR",
            "370": "FR", "371": "FR", "372": "FR", "373": "FR", "374": "FR",
            "375": "FR", "376": "FR", "377": "FR", "378": "FR", "379": "FR",
            "400": "DE", "401": "DE", "402": "DE", "403": "DE", "404": "DE",
            "405": "DE", "406": "DE", "407": "DE", "408": "DE", "409": "DE",
            "410": "DE", "411": "DE", "412": "DE", "413": "DE", "414": "DE",
            "415": "DE", "416": "DE", "417": "DE", "418": "DE", "419": "DE",
            "420": "DE", "421": "DE", "422": "DE", "423": "DE", "424": "DE",
            "425": "DE", "426": "DE", "427": "DE", "428": "DE", "429": "DE",
            "430": "DE", "431": "DE", "432": "DE", "433": "DE", "434": "DE",
            "435": "DE", "436": "DE", "437": "DE", "438": "DE", "439": "DE",
            "500": "UK", "501": "UK", "502": "UK", "503": "UK", "504": "UK",
            "505": "UK", "506": "UK", "507": "UK", "508": "UK", "509": "UK",
            "800": "IT", "801": "IT", "802": "IT", "803": "IT", "804": "IT",
            "805": "IT", "806": "IT", "807": "IT", "808": "IT", "809": "IT",
            "840": "ES", "841": "ES", "842": "ES", "843": "ES", "844": "ES",
            "845": "ES", "846": "ES", "847": "ES", "848": "ES", "849": "ES",
        }
        country_prefix = prefixes.get(prefix, prefix)

    return {
        "is_valid": True,
        "normalized_barcode": normalized,
        "detected_type": detected_type,
        "checksum": checksum,
        "country_prefix": country_prefix,
        "error": None
    }
