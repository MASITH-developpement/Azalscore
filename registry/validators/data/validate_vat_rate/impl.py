"""
Implémentation du sous-programme : validate_vat_rate

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 18+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


# Taux de TVA par pays
VAT_RATES = {
    "FR": {
        "normal": Decimal("20.00"),
        "intermediaire": Decimal("10.00"),
        "reduit": Decimal("5.50"),
        "super_reduit": Decimal("2.10"),
        "exonere": Decimal("0.00"),
    },
    "DE": {
        "normal": Decimal("19.00"),
        "reduit": Decimal("7.00"),
        "exonere": Decimal("0.00"),
    },
    "ES": {
        "normal": Decimal("21.00"),
        "reduit": Decimal("10.00"),
        "super_reduit": Decimal("4.00"),
        "exonere": Decimal("0.00"),
    },
    "IT": {
        "normal": Decimal("22.00"),
        "reduit": Decimal("10.00"),
        "super_reduit": Decimal("4.00"),
        "exonere": Decimal("0.00"),
    },
    "BE": {
        "normal": Decimal("21.00"),
        "reduit": Decimal("12.00"),
        "super_reduit": Decimal("6.00"),
        "exonere": Decimal("0.00"),
    },
}


def _to_decimal(value) -> Decimal | None:
    """Convertit une valeur en Decimal."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '.').replace('%', '')
        if cleaned and cleaned.replace('.', '').replace('-', '').isdigit():
            return Decimal(cleaned)
    return None


def _find_vat_type(rate: Decimal, country: str) -> str | None:
    """Trouve le type de TVA correspondant à un taux."""
    if country not in VAT_RATES:
        return None

    for vat_type, vat_rate in VAT_RATES[country].items():
        if rate == vat_rate:
            return vat_type

    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un taux de TVA selon les taux légaux par pays.

    Args:
        inputs: {
            "vat_rate": number,  # Taux de TVA à valider
            "country": string,  # Code pays ISO (défaut: FR)
        }

    Returns:
        {
            "is_valid": boolean,  # True si taux valide
            "vat_type": string,  # Type: normal, reduit, etc.
            "error": string,  # Message d'erreur si invalide
        }
    """
    vat_rate_input = inputs.get("vat_rate")
    country = inputs.get("country", "FR").upper()

    # Valeur vide
    if vat_rate_input is None:
        return {
            "is_valid": False,
            "vat_type": None,
            "error": "Taux de TVA requis"
        }

    # Conversion
    rate = _to_decimal(vat_rate_input)
    if rate is None:
        return {
            "is_valid": False,
            "vat_type": None,
            "error": "Format de taux invalide"
        }

    # Arrondir à 2 décimales
    rate = rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Vérification pays
    if country not in VAT_RATES:
        # Accepter quand même si le taux est raisonnable
        if Decimal("0") <= rate <= Decimal("30"):
            return {
                "is_valid": True,
                "vat_type": "custom",
                "error": None
            }
        return {
            "is_valid": False,
            "vat_type": None,
            "error": f"Pays non supporté: {country}"
        }

    # Recherche du type
    vat_type = _find_vat_type(rate, country)

    if vat_type is None:
        valid_rates = [f"{r}% ({t})" for t, r in VAT_RATES[country].items()]
        return {
            "is_valid": False,
            "vat_type": None,
            "error": f"Taux non standard pour {country}. Taux valides: {', '.join(valid_rates)}"
        }

    return {
        "is_valid": True,
        "vat_type": vat_type,
        "error": None
    }
