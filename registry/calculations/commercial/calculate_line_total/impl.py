"""
Implémentation du sous-programme : calculate_line_total

Code métier PUR - Calculs commerciaux
Utilisation : 50+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule le total d'une ligne commerciale.

    Formula:
    - Subtotal HT = quantity × unit_price
    - Discount = subtotal_ht × discount_rate
    - Total HT = subtotal_ht - discount
    - VAT = total_ht × vat_rate
    - Total TTC = total_ht + vat

    Args:
        inputs: {
            "quantity": float,
            "unit_price": float,
            "discount_rate": float (optionnel, défaut 0),
            "vat_rate": float (optionnel, défaut 0.20)
        }

    Returns:
        {
            "subtotal_ht": float,
            "discount_amount": float,
            "total_ht_after_discount": float,
            "vat_amount": float,
            "total_ttc": float
        }
    """
    quantity = Decimal(str(inputs["quantity"]))
    unit_price = Decimal(str(inputs["unit_price"]))
    discount_rate = Decimal(str(inputs.get("discount_rate", 0)))
    vat_rate = Decimal(str(inputs.get("vat_rate", 0.20)))

    # Calcul sous-total HT
    subtotal_ht = quantity * unit_price

    # Calcul remise
    discount_amount = subtotal_ht * discount_rate

    # Total HT après remise
    total_ht_after_discount = subtotal_ht - discount_amount

    # Calcul TVA
    vat_amount = total_ht_after_discount * vat_rate

    # Total TTC
    total_ttc = total_ht_after_discount + vat_amount

    return {
        "subtotal_ht": round(float(subtotal_ht), 2),
        "discount_amount": round(float(discount_amount), 2),
        "total_ht_after_discount": round(float(total_ht_after_discount), 2),
        "vat_amount": round(float(vat_amount), 2),
        "total_ttc": round(float(total_ttc), 2)
    }
