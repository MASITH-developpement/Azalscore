"""
Implémentation du sous-programme : validate_journal_entry_balance

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 30+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


# Tolérance pour l'équilibrage (pour gérer les erreurs d'arrondi)
BALANCE_TOLERANCE = Decimal("0.01")


def _to_decimal(value) -> Decimal:
    """Convertit une valeur en Decimal de manière sécurisée."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        # Nettoyer la chaîne (espaces, symboles monétaires)
        cleaned = value.strip().replace(" ", "").replace("€", "").replace("$", "")
        cleaned = cleaned.replace(",", ".")  # Format français
        if cleaned and (cleaned.replace(".", "").replace("-", "").isdigit()):
            return Decimal(cleaned)
    return Decimal("0")


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide qu'une écriture comptable est équilibrée (Débit = Crédit).

    Principe de la partie double:
    - La somme des débits doit être égale à la somme des crédits
    - Une tolérance de 0.01 est acceptée pour les arrondis

    Args:
        inputs: {
            "lines": array,  # Liste des lignes d'écriture
                             # Chaque ligne: {"account": str, "debit": number, "credit": number}
        }

    Returns:
        {
            "is_balanced": boolean,  # True si équilibré (débit = crédit)
            "debit_total": number,  # Total des débits
            "credit_total": number,  # Total des crédits
            "difference": number,  # Différence (débit - crédit)
            "line_count": number,  # Nombre de lignes
            "has_debit_lines": boolean,  # Au moins une ligne au débit
            "has_credit_lines": boolean,  # Au moins une ligne au crédit
            "warnings": array,  # Avertissements éventuels
            "error": string,  # Message d'erreur si invalide
        }
    """
    lines = inputs.get("lines", [])
    warnings = []

    # Validation de l'entrée
    if not lines:
        return {
            "is_balanced": False,
            "debit_total": Decimal("0"),
            "credit_total": Decimal("0"),
            "difference": Decimal("0"),
            "line_count": 0,
            "has_debit_lines": False,
            "has_credit_lines": False,
            "warnings": [],
            "error": "L'écriture ne contient aucune ligne"
        }

    if not isinstance(lines, list):
        return {
            "is_balanced": False,
            "debit_total": Decimal("0"),
            "credit_total": Decimal("0"),
            "difference": Decimal("0"),
            "line_count": 0,
            "has_debit_lines": False,
            "has_credit_lines": False,
            "warnings": [],
            "error": "Les lignes doivent être fournies sous forme de liste"
        }

    # Calcul des totaux
    debit_total = Decimal("0")
    credit_total = Decimal("0")
    debit_count = 0
    credit_count = 0
    empty_lines = 0

    for i, line in enumerate(lines):
        if not isinstance(line, dict):
            return {
                "is_balanced": False,
                "debit_total": debit_total,
                "credit_total": credit_total,
                "difference": Decimal("0"),
                "line_count": len(lines),
                "has_debit_lines": debit_count > 0,
                "has_credit_lines": credit_count > 0,
                "warnings": warnings,
                "error": f"Ligne {i + 1}: format invalide (doit être un objet)"
            }

        debit = _to_decimal(line.get("debit", 0))
        credit = _to_decimal(line.get("credit", 0))

        # Vérification des montants négatifs
        if debit < 0:
            return {
                "is_balanced": False,
                "debit_total": debit_total,
                "credit_total": credit_total,
                "difference": Decimal("0"),
                "line_count": len(lines),
                "has_debit_lines": debit_count > 0,
                "has_credit_lines": credit_count > 0,
                "warnings": warnings,
                "error": f"Ligne {i + 1}: le débit ne peut pas être négatif"
            }

        if credit < 0:
            return {
                "is_balanced": False,
                "debit_total": debit_total,
                "credit_total": credit_total,
                "difference": Decimal("0"),
                "line_count": len(lines),
                "has_debit_lines": debit_count > 0,
                "has_credit_lines": credit_count > 0,
                "warnings": warnings,
                "error": f"Ligne {i + 1}: le crédit ne peut pas être négatif"
            }

        # Vérification qu'une ligne n'est pas à la fois au débit et au crédit
        if debit > 0 and credit > 0:
            warnings.append(
                f"Ligne {i + 1}: présente à la fois au débit ({debit}) et au crédit ({credit})"
            )

        # Vérification ligne vide
        if debit == 0 and credit == 0:
            empty_lines += 1

        # Accumulation des totaux
        debit_total += debit
        credit_total += credit

        if debit > 0:
            debit_count += 1
        if credit > 0:
            credit_count += 1

    # Avertissement pour lignes vides
    if empty_lines > 0:
        warnings.append(f"{empty_lines} ligne(s) sans mouvement (débit et crédit à 0)")

    # Calcul de la différence
    difference = debit_total - credit_total

    # Vérification de l'équilibre avec tolérance
    is_balanced = abs(difference) <= BALANCE_TOLERANCE

    # Vérification qu'il y a bien des lignes au débit ET au crédit
    if debit_count == 0:
        return {
            "is_balanced": False,
            "debit_total": debit_total.quantize(Decimal("0.01")),
            "credit_total": credit_total.quantize(Decimal("0.01")),
            "difference": difference.quantize(Decimal("0.01")),
            "line_count": len(lines),
            "has_debit_lines": False,
            "has_credit_lines": credit_count > 0,
            "warnings": warnings,
            "error": "L'écriture ne contient aucune ligne au débit"
        }

    if credit_count == 0:
        return {
            "is_balanced": False,
            "debit_total": debit_total.quantize(Decimal("0.01")),
            "credit_total": credit_total.quantize(Decimal("0.01")),
            "difference": difference.quantize(Decimal("0.01")),
            "line_count": len(lines),
            "has_debit_lines": debit_count > 0,
            "has_credit_lines": False,
            "warnings": warnings,
            "error": "L'écriture ne contient aucune ligne au crédit"
        }

    # Si non équilibré, retourner l'erreur
    if not is_balanced:
        return {
            "is_balanced": False,
            "debit_total": debit_total.quantize(Decimal("0.01")),
            "credit_total": credit_total.quantize(Decimal("0.01")),
            "difference": difference.quantize(Decimal("0.01")),
            "line_count": len(lines),
            "has_debit_lines": True,
            "has_credit_lines": True,
            "warnings": warnings,
            "error": f"L'écriture n'est pas équilibrée: différence de {difference.quantize(Decimal('0.01'))} EUR"
        }

    return {
        "is_balanced": True,
        "debit_total": debit_total.quantize(Decimal("0.01")),
        "credit_total": credit_total.quantize(Decimal("0.01")),
        "difference": difference.quantize(Decimal("0.01")),
        "line_count": len(lines),
        "has_debit_lines": True,
        "has_credit_lines": True,
        "warnings": warnings,
        "error": None
    }
