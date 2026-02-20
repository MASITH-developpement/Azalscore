"""
Implémentation du sous-programme : validate_rib

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 12+ endroits dans le codebase
"""

from typing import Dict, Any


def _letter_to_number(letter: str) -> int:
    """
    Convertit une lettre en nombre selon la table de correspondance RIB.

    Table de conversion:
    A,J = 1, B,K,S = 2, C,L,T = 3, D,M,U = 4, E,N,V = 5,
    F,O,W = 6, G,P,X = 7, H,Q,Y = 8, I,R,Z = 9
    """
    letter = letter.upper()
    conversion_table = {
        'A': 1, 'J': 1,
        'B': 2, 'K': 2, 'S': 2,
        'C': 3, 'L': 3, 'T': 3,
        'D': 4, 'M': 4, 'U': 4,
        'E': 5, 'N': 5, 'V': 5,
        'F': 6, 'O': 6, 'W': 6,
        'G': 7, 'P': 7, 'X': 7,
        'H': 8, 'Q': 8, 'Y': 8,
        'I': 9, 'R': 9, 'Z': 9,
    }
    return conversion_table.get(letter, 0)


def _convert_to_numeric(value: str) -> str:
    """Convertit une chaîne alphanumériques en chiffres uniquement."""
    result = ""
    for char in value.upper():
        if char.isdigit():
            result += char
        elif char.isalpha():
            result += str(_letter_to_number(char))
    return result


def _calculate_rib_key(bank_code: str, branch_code: str, account_number: str) -> int:
    """
    Calcule la clé RIB selon l'algorithme officiel.

    Formule: Clé = 97 - ((89 × B + 15 × G + 3 × C) mod 97)
    où B = code banque, G = code guichet, C = compte

    Les lettres sont converties en chiffres avant calcul.
    """
    # Convertir en numérique
    b = _convert_to_numeric(bank_code)
    g = _convert_to_numeric(branch_code)
    c = _convert_to_numeric(account_number)

    # Concaténer et convertir en entier
    # Pour gérer les grands nombres, on utilise le calcul modulaire progressif
    concatenated = b + g + c

    # Calcul du reste par modulo 97
    # Pour les grands nombres, on calcule progressivement
    remainder = 0
    for digit in concatenated:
        remainder = (remainder * 10 + int(digit)) % 97

    # La formule complète est: 97 - ((89*B + 15*G + 3*C) mod 97)
    # Simplifiée avec la concaténation: 97 - (concat mod 97) n'est pas exacte
    # La vraie formule utilise les pondérations

    # Utilisation de la méthode avec concaténation et décalage
    # Clé = 97 - reste de (code_banque || code_guichet || numéro_compte || 00) / 97
    concat_with_zeros = b + g + c + "00"

    # Calcul progressif du modulo pour éviter les overflow
    mod_result = 0
    for digit in concat_with_zeros:
        mod_result = (mod_result * 10 + int(digit)) % 97

    key = 97 - mod_result
    return key


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un RIB français (Relevé d'Identité Bancaire).

    Format RIB: Code Banque (5) + Code Guichet (5) + N° Compte (11) + Clé (2)

    Args:
        inputs: {
            "bank_code": string,  # Code banque (5 chiffres)
            "branch_code": string,  # Code guichet (5 chiffres)
            "account_number": string,  # Numéro de compte (11 caractères)
            "key": string,  # Clé RIB (2 chiffres)
        }

    Returns:
        {
            "is_valid": boolean,  # True si RIB valide
            "normalized_bank_code": string,  # Code banque normalisé
            "normalized_branch_code": string,  # Code guichet normalisé
            "normalized_account": string,  # Numéro compte normalisé
            "normalized_key": string,  # Clé normalisée
            "calculated_key": int,  # Clé calculée (pour vérification)
            "iban_bban": string,  # BBAN (partie française de l'IBAN)
            "error": string,  # Message d'erreur si invalide
        }
    """
    bank_code = inputs.get("bank_code", "")
    branch_code = inputs.get("branch_code", "")
    account_number = inputs.get("account_number", "")
    key = inputs.get("key", "")

    # Normalisation (supprime espaces)
    bank_code = str(bank_code).strip().replace(" ", "")
    branch_code = str(branch_code).strip().replace(" ", "")
    account_number = str(account_number).strip().replace(" ", "").upper()
    key = str(key).strip().replace(" ", "")

    # Validation code banque
    if not bank_code:
        return {
            "is_valid": False,
            "normalized_bank_code": None,
            "normalized_branch_code": None,
            "normalized_account": None,
            "normalized_key": None,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Code banque requis"
        }

    if len(bank_code) != 5:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": f"Code banque invalide: attendu 5 chiffres, reçu {len(bank_code)}"
        }

    if not bank_code.isdigit():
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Code banque doit contenir uniquement des chiffres"
        }

    # Validation code guichet
    if not branch_code:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": None,
            "normalized_account": None,
            "normalized_key": None,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Code guichet requis"
        }

    if len(branch_code) != 5:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": f"Code guichet invalide: attendu 5 chiffres, reçu {len(branch_code)}"
        }

    if not branch_code.isdigit():
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Code guichet doit contenir uniquement des chiffres"
        }

    # Validation numéro de compte
    if not account_number:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": None,
            "normalized_key": None,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Numéro de compte requis"
        }

    if len(account_number) != 11:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": f"Numéro de compte invalide: attendu 11 caractères, reçu {len(account_number)}"
        }

    if not account_number.isalnum():
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Numéro de compte doit être alphanumérique"
        }

    # Validation clé
    if not key:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": None,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Clé RIB requise"
        }

    if len(key) != 2:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": f"Clé RIB invalide: attendu 2 chiffres, reçu {len(key)}"
        }

    if not key.isdigit():
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": None,
            "iban_bban": None,
            "error": "Clé RIB doit contenir uniquement des chiffres"
        }

    # Calcul et vérification de la clé
    calculated_key = _calculate_rib_key(bank_code, branch_code, account_number)
    provided_key = int(key)

    if calculated_key != provided_key:
        return {
            "is_valid": False,
            "normalized_bank_code": bank_code,
            "normalized_branch_code": branch_code,
            "normalized_account": account_number,
            "normalized_key": key,
            "calculated_key": calculated_key,
            "iban_bban": None,
            "error": f"Clé RIB incorrecte: attendu {calculated_key:02d}, reçu {key}"
        }

    # Construction du BBAN (pour l'IBAN français)
    bban = bank_code + branch_code + account_number + key

    return {
        "is_valid": True,
        "normalized_bank_code": bank_code,
        "normalized_branch_code": branch_code,
        "normalized_account": account_number,
        "normalized_key": key,
        "calculated_key": calculated_key,
        "iban_bban": bban,
        "error": None
    }
