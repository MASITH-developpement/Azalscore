"""
Implémentation du sous-programme : validate_credit_card

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 25+ endroits dans le codebase

SÉCURITÉ:
- Ne stocke JAMAIS le numéro de carte complet
- Utilise uniquement pour la validation du format
- En production, utiliser un service de tokenisation (Stripe, etc.)
"""

from typing import Dict, Any
import re


def _luhn_checksum(card_number: str) -> bool:
    """
    Vérifie la validité d'un numéro de carte via l'algorithme de Luhn.

    L'algorithme de Luhn est utilisé pour valider les numéros de cartes bancaires,
    SIREN, SIRET, numéros de sécurité sociale, etc.
    """
    def digits_of(n: str) -> list:
        return [int(d) for d in n]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(str(d * 2)))

    return checksum % 10 == 0


def _detect_card_type(card_number: str) -> str:
    """
    Détecte le type de carte bancaire basé sur le préfixe (BIN/IIN).

    Retourne le type de carte ou "unknown".
    """
    # Patterns pour les principaux réseaux de cartes
    patterns = {
        "visa": r"^4[0-9]{12}(?:[0-9]{3})?$",
        "mastercard": r"^5[1-5][0-9]{14}$|^2(?:2(?:2[1-9]|[3-9][0-9])|[3-6][0-9][0-9]|7(?:[01][0-9]|20))[0-9]{12}$",
        "amex": r"^3[47][0-9]{13}$",
        "discover": r"^6(?:011|5[0-9]{2})[0-9]{12}$",
        "diners": r"^3(?:0[0-5]|[68][0-9])[0-9]{11}$",
        "jcb": r"^(?:2131|1800|35\d{3})\d{11}$",
        "unionpay": r"^(62|88)\d{14,17}$",
        "maestro": r"^(5018|5020|5038|6304|6759|6761|6763)[0-9]{8,15}$",
        "cb": r"^(4|5[1-5])[0-9]{14}$",  # Carte Bleue (FR)
    }

    for card_type, pattern in patterns.items():
        if re.match(pattern, card_number):
            return card_type

    return "unknown"


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro de carte bancaire.

    Utilise l'algorithme de Luhn pour vérifier la validité du numéro.
    Détecte également le type de carte (Visa, Mastercard, etc.).

    Args:
        inputs: {
            "card_number": string,  # Numéro de carte (avec ou sans espaces/tirets)
        }

    Returns:
        {
            "is_valid": boolean,  # True si le numéro est valide
            "card_type": string,  # Type de carte (visa, mastercard, etc.)
            "masked_number": string,  # Numéro masqué (ex: ****1234)
        }

    SÉCURITÉ:
    - Ne jamais logger le numéro de carte complet
    - Ne jamais stocker le numéro de carte (utiliser tokenisation)
    - Retourne un numéro masqué pour l'affichage
    """
    card_number = inputs.get("card_number", "")

    # Nettoyer le numéro (enlever espaces, tirets)
    cleaned = re.sub(r'[\s\-]', '', str(card_number))

    # Vérifications de base
    if not cleaned:
        return {
            "is_valid": False,
            "card_type": "unknown",
            "masked_number": "",
            "error": "Numéro de carte requis"
        }

    # Vérifier que ce sont uniquement des chiffres
    if not cleaned.isdigit():
        return {
            "is_valid": False,
            "card_type": "unknown",
            "masked_number": "",
            "error": "Le numéro de carte ne doit contenir que des chiffres"
        }

    # Vérifier la longueur (13 à 19 chiffres selon le type de carte)
    if len(cleaned) < 13 or len(cleaned) > 19:
        return {
            "is_valid": False,
            "card_type": "unknown",
            "masked_number": "",
            "error": "Longueur du numéro de carte invalide"
        }

    # Vérifier avec l'algorithme de Luhn
    is_valid = _luhn_checksum(cleaned)

    # Détecter le type de carte
    card_type = _detect_card_type(cleaned) if is_valid else "unknown"

    # Créer le numéro masqué (SÉCURITÉ: ne jamais exposer le numéro complet)
    masked = "*" * (len(cleaned) - 4) + cleaned[-4:]

    return {
        "is_valid": is_valid,
        "card_type": card_type,
        "masked_number": masked,
    }
