"""
Implémentation du sous-programme : calculate_vat

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent garanti
"""

from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule le montant TTC à partir du montant HT et du taux de TVA.

    Args:
        inputs: {
            "amount_ht": float,
            "vat_rate": float (ex: 0.20 pour 20%)
        }

    Returns:
        {
            "amount_ht": float,
            "vat_amount": float,
            "amount_ttc": float,
            "vat_rate_percentage": float
        }
    """
    amount_ht = float(inputs["amount_ht"])
    vat_rate = float(inputs["vat_rate"])

    # Calcul du montant de TVA
    vat_amount = amount_ht * vat_rate

    # Calcul du montant TTC
    amount_ttc = amount_ht + vat_amount

    # Conversion du taux en pourcentage
    vat_rate_percentage = vat_rate * 100

    return {
        "amount_ht": round(amount_ht, 2),
        "vat_amount": round(vat_amount, 2),
        "amount_ttc": round(amount_ttc, 2),
        "vat_rate_percentage": round(vat_rate_percentage, 2)
    }
