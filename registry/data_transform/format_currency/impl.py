"""
Implémentation du sous-programme : format_currency

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent garanti

Utilisation : 100+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formate un montant en chaîne de caractères selon la locale et la devise.

    Args:
        inputs: {
            "amount": float/Decimal,
            "currency": str (défaut: "EUR"),
            "locale": str (défaut: "fr_FR"),
            "show_symbol": bool (défaut: true)
        }

    Returns:
        {
            "formatted": str (ex: "1 234,56 €"),
            "amount": float,
            "currency": str
        }

    Examples:
        >>> execute({"amount": 1234.56})
        {"formatted": "1 234,56 €", "amount": 1234.56, "currency": "EUR"}

        >>> execute({"amount": 1234.56, "currency": "USD", "locale": "en_US"})
        {"formatted": "$1,234.56", "amount": 1234.56, "currency": "USD"}
    """
    amount = inputs["amount"]
    currency = inputs.get("currency", "EUR")
    locale = inputs.get("locale", "fr_FR")
    show_symbol = inputs.get("show_symbol", True)

    # Conversion en Decimal pour précision
    if not isinstance(amount, Decimal):
        amount_decimal = Decimal(str(amount))
    else:
        amount_decimal = amount

    # Arrondi à 2 décimales
    amount_rounded = round(amount_decimal, 2)

    # Symboles de devises
    CURRENCY_SYMBOLS = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
        "CHF": "CHF",
        "JPY": "¥",
        "CNY": "¥"
    }

    # Formatage selon la locale
    if locale.startswith("fr"):
        # Format français : 1 234,56 €
        amount_str = f"{amount_rounded:,.2f}".replace(",", " ").replace(".", ",")
        if show_symbol:
            symbol = CURRENCY_SYMBOLS.get(currency, currency)
            formatted = f"{amount_str} {symbol}"
        else:
            formatted = amount_str

    elif locale.startswith("en"):
        # Format anglais : $1,234.56 ou 1,234.56
        amount_str = f"{amount_rounded:,.2f}"
        if show_symbol:
            symbol = CURRENCY_SYMBOLS.get(currency, currency)
            if currency in ["USD", "GBP"]:
                formatted = f"{symbol}{amount_str}"
            else:
                formatted = f"{amount_str} {symbol}"
        else:
            formatted = amount_str

    else:
        # Format par défaut : 1234.56 EUR
        if show_symbol:
            formatted = f"{amount_rounded} {currency}"
        else:
            formatted = str(amount_rounded)

    return {
        "formatted": formatted,
        "amount": float(amount_rounded),
        "currency": currency
    }
