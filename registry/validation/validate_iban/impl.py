"""
Implémentation du sous-programme : validate_iban

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent garanti
"""

import re
from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un IBAN selon la norme internationale.

    Args:
        inputs: {"iban": str}

    Returns:
        {
            "is_valid": bool,
            "normalized_iban": str,
            "country_code": str,
            "error": str | None
        }
    """
    iban = inputs["iban"]

    # Normalisation : suppression espaces et mise en majuscules
    normalized = re.sub(r'\s+', '', iban).upper()

    # Vérification longueur minimale (15) et maximale (34)
    if len(normalized) < 15 or len(normalized) > 34:
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": normalized[:2] if len(normalized) >= 2 else "",
            "error": "Longueur IBAN invalide (doit être entre 15 et 34 caractères)"
        }

    # Vérification format de base (2 lettres + 2 chiffres + alphanumériques)
    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', normalized):
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": normalized[:2] if len(normalized) >= 2 else "",
            "error": "Format IBAN invalide (doit commencer par 2 lettres + 2 chiffres)"
        }

    # Extraction du code pays
    country_code = normalized[:2]

    # Vérification du checksum (modulo 97)
    # Déplacer les 4 premiers caractères à la fin
    rearranged = normalized[4:] + normalized[:4]

    # Convertir les lettres en chiffres (A=10, B=11, ..., Z=35)
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        else:
            # A=10, B=11, ..., Z=35
            numeric += str(ord(char) - ord('A') + 10)

    # Calcul du modulo 97
    checksum = int(numeric) % 97

    if checksum != 1:
        return {
            "is_valid": False,
            "normalized_iban": normalized,
            "country_code": country_code,
            "error": "Checksum IBAN invalide"
        }

    # IBAN valide
    return {
        "is_valid": True,
        "normalized_iban": normalized,
        "country_code": country_code,
        "error": None
    }
