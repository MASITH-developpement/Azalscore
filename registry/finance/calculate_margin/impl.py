"""
Implémentation du sous-programme : calculate_margin

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas d'appel à d'autres sous-programmes
- Pas de side effects
- Idempotent garanti
- La gestion d'erreur est déléguée au moteur d'orchestration
"""

from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule la marge brute et le taux de marge.

    Args:
        inputs: {
            "price": float - Prix de vente HT
            "cost": float - Coût d'achat HT
        }

    Returns:
        {
            "margin": float - Marge brute (price - cost)
            "margin_rate": float - Taux de marge (margin / price)
            "margin_percentage": float - Taux de marge en %
        }

    Notes:
        - Si price == 0, margin_rate = 0
        - Valeurs arrondies à 2 décimales
    """
    price = float(inputs["price"])
    cost = float(inputs["cost"])

    # Calcul de la marge brute
    margin = price - cost

    # Calcul du taux de marge
    margin_rate = (margin / price) if price > 0 else 0.0

    # Conversion en pourcentage
    margin_percentage = margin_rate * 100

    return {
        "margin": round(margin, 2),
        "margin_rate": round(margin_rate, 4),
        "margin_percentage": round(margin_percentage, 2)
    }
