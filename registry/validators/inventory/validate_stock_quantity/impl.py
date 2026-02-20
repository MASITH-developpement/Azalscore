"""
Implémentation du sous-programme : validate_stock_quantity

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


def _to_decimal(value) -> Decimal | None:
    """Convertit une valeur en Decimal."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '.').replace(' ', '')
        if cleaned and cleaned.replace('.', '').replace('-', '').isdigit():
            return Decimal(cleaned)
    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une quantité en stock.

    Vérifie:
    - Quantité valide (non négative)
    - Respect du stock minimum (seuil d'alerte)
    - Respect du stock maximum (capacité)

    Args:
        inputs: {
            "quantity": number,  # Quantité à valider
            "min_stock": number,  # Stock minimum (seuil d'alerte)
            "max_stock": number,  # Stock maximum (capacité)
            "allow_negative": boolean,  # Autoriser négatif (défaut: false)
            "unit": string,  # Unité de mesure (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si quantité valide
            "quantity": number,  # Quantité normalisée
            "is_below_min": boolean,  # Sous le seuil minimum
            "is_above_max": boolean,  # Au-dessus du maximum
            "stock_status": string,  # Status: out_of_stock, low, normal, high, overstocked
            "reorder_needed": boolean,  # Réapprovisionnement nécessaire
            "available_capacity": number,  # Capacité restante (si max défini)
            "error": string,  # Message d'erreur si invalide
        }
    """
    quantity_input = inputs.get("quantity")
    min_stock_input = inputs.get("min_stock")
    max_stock_input = inputs.get("max_stock")
    allow_negative = inputs.get("allow_negative", False)
    unit = inputs.get("unit", "unité(s)")

    # Quantité requise
    if quantity_input is None:
        return {
            "is_valid": False,
            "quantity": None,
            "is_below_min": None,
            "is_above_max": None,
            "stock_status": None,
            "reorder_needed": None,
            "available_capacity": None,
            "error": "Quantité requise"
        }

    # Conversion
    quantity = _to_decimal(quantity_input)
    if quantity is None:
        return {
            "is_valid": False,
            "quantity": None,
            "is_below_min": None,
            "is_above_max": None,
            "stock_status": None,
            "reorder_needed": None,
            "available_capacity": None,
            "error": "Format de quantité invalide"
        }

    min_stock = _to_decimal(min_stock_input) if min_stock_input is not None else None
    max_stock = _to_decimal(max_stock_input) if max_stock_input is not None else None

    # Vérification quantité négative
    if quantity < 0 and not allow_negative:
        return {
            "is_valid": False,
            "quantity": float(quantity),
            "is_below_min": True,
            "is_above_max": False,
            "stock_status": "negative",
            "reorder_needed": True,
            "available_capacity": None,
            "error": "Quantité négative non autorisée"
        }

    # Vérification cohérence min/max
    if min_stock is not None and max_stock is not None and min_stock > max_stock:
        return {
            "is_valid": False,
            "quantity": float(quantity),
            "is_below_min": None,
            "is_above_max": None,
            "stock_status": None,
            "reorder_needed": None,
            "available_capacity": None,
            "error": "Le stock minimum doit être inférieur au stock maximum"
        }

    # Calculs
    is_below_min = min_stock is not None and quantity < min_stock
    is_above_max = max_stock is not None and quantity > max_stock
    available_capacity = float(max_stock - quantity) if max_stock is not None else None

    # Détermination du statut
    if quantity <= 0:
        stock_status = "out_of_stock"
    elif is_below_min:
        if min_stock and quantity < min_stock / 2:
            stock_status = "critical"
        else:
            stock_status = "low"
    elif is_above_max:
        stock_status = "overstocked"
    elif max_stock and quantity > max_stock * Decimal("0.9"):
        stock_status = "high"
    else:
        stock_status = "normal"

    # Réapprovisionnement nécessaire
    reorder_needed = quantity <= 0 or is_below_min

    # Vérification dépassement max (avertissement, pas erreur)
    error = None
    if is_above_max:
        error = f"Quantité dépasse la capacité maximale ({max_stock} {unit})"

    return {
        "is_valid": not is_above_max,  # Dépassement max = invalide
        "quantity": float(quantity),
        "is_below_min": is_below_min,
        "is_above_max": is_above_max,
        "stock_status": stock_status,
        "reorder_needed": reorder_needed,
        "available_capacity": available_capacity,
        "error": error
    }
