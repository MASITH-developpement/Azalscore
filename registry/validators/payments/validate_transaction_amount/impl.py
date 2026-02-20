"""
Implémentation du sous-programme : validate_transaction_amount

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 30+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


# Limites par défaut (en EUR)
DEFAULT_MIN_AMOUNT = Decimal("0.01")
DEFAULT_MAX_AMOUNT = Decimal("100000.00")


def _to_decimal(value) -> Decimal | None:
    """Convertit une valeur en Decimal."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.strip().replace(' ', '').replace(',', '.')
        # Supprimer symboles monétaires
        for symbol in ['€', '$', '£', '¥', 'EUR', 'USD', 'GBP']:
            cleaned = cleaned.replace(symbol, '')
        if cleaned and _is_valid_amount(cleaned):
            return Decimal(cleaned)
    return None


def _is_valid_amount(s: str) -> bool:
    """Vérifie si une chaîne représente un montant valide."""
    if not s:
        return False
    if s[0] in '+-':
        s = s[1:]
    if not s:
        return False
    dot_count = s.count('.')
    if dot_count > 1:
        return False
    return s.replace('.', '').isdigit()


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un montant de transaction.

    Vérifie:
    - Format valide
    - Montant positif (sauf refund)
    - Respect des limites min/max
    - Précision (2 décimales max)

    Args:
        inputs: {
            "amount": number/string,  # Montant à valider
            "min_amount": number,  # Montant minimum (défaut: 0.01)
            "max_amount": number,  # Montant maximum (défaut: 100000)
            "currency": string,  # Devise (optionnel)
            "allow_negative": boolean,  # Autoriser négatif/refund (défaut: false)
        }

    Returns:
        {
            "is_valid": boolean,  # True si montant valide
            "amount": number,  # Montant normalisé
            "amount_cents": number,  # Montant en centimes
            "formatted_amount": string,  # Montant formaté
            "currency": string,  # Devise
            "is_refund": boolean,  # True si montant négatif
            "exceeds_limit": boolean,  # Dépasse une limite
            "error": string,  # Message d'erreur si invalide
        }
    """
    amount_input = inputs.get("amount")
    min_amount_input = inputs.get("min_amount", DEFAULT_MIN_AMOUNT)
    max_amount_input = inputs.get("max_amount", DEFAULT_MAX_AMOUNT)
    currency = inputs.get("currency", "EUR")
    allow_negative = inputs.get("allow_negative", False)

    # Montant requis
    if amount_input is None:
        return {
            "is_valid": False,
            "amount": None,
            "amount_cents": None,
            "formatted_amount": None,
            "currency": currency,
            "is_refund": None,
            "exceeds_limit": None,
            "error": "Montant requis"
        }

    # Conversion
    amount = _to_decimal(amount_input)
    if amount is None:
        return {
            "is_valid": False,
            "amount": None,
            "amount_cents": None,
            "formatted_amount": None,
            "currency": currency,
            "is_refund": None,
            "exceeds_limit": None,
            "error": "Format de montant invalide"
        }

    min_amount = _to_decimal(min_amount_input) or DEFAULT_MIN_AMOUNT
    max_amount = _to_decimal(max_amount_input) or DEFAULT_MAX_AMOUNT

    # Arrondir à 2 décimales
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Détection refund
    is_refund = amount < 0

    # Vérification montant négatif
    if is_refund and not allow_negative:
        return {
            "is_valid": False,
            "amount": float(amount),
            "amount_cents": int(amount * 100),
            "formatted_amount": f"{amount:.2f} {currency}",
            "currency": currency,
            "is_refund": True,
            "exceeds_limit": False,
            "error": "Montant négatif non autorisé (utilisez allow_negative pour les remboursements)"
        }

    # Valeur absolue pour les vérifications de limite
    abs_amount = abs(amount)

    # Vérification montant minimum
    if abs_amount < min_amount and abs_amount != 0:
        return {
            "is_valid": False,
            "amount": float(amount),
            "amount_cents": int(amount * 100),
            "formatted_amount": f"{amount:.2f} {currency}",
            "currency": currency,
            "is_refund": is_refund,
            "exceeds_limit": False,
            "error": f"Montant minimum: {min_amount:.2f} {currency}"
        }

    # Vérification montant maximum
    if abs_amount > max_amount:
        return {
            "is_valid": False,
            "amount": float(amount),
            "amount_cents": int(amount * 100),
            "formatted_amount": f"{amount:.2f} {currency}",
            "currency": currency,
            "is_refund": is_refund,
            "exceeds_limit": True,
            "error": f"Montant maximum: {max_amount:.2f} {currency}"
        }

    # Vérification montant zéro
    if amount == 0:
        return {
            "is_valid": False,
            "amount": 0,
            "amount_cents": 0,
            "formatted_amount": f"0.00 {currency}",
            "currency": currency,
            "is_refund": False,
            "exceeds_limit": False,
            "error": "Montant ne peut pas être zéro"
        }

    # Formatage
    formatted = f"{amount:.2f} {currency}"

    return {
        "is_valid": True,
        "amount": float(amount),
        "amount_cents": int(amount * 100),
        "formatted_amount": formatted,
        "currency": currency,
        "is_refund": is_refund,
        "exceeds_limit": False,
        "error": None
    }
