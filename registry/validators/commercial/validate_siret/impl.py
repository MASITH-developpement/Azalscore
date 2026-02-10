"""
Implémentation du sous-programme : validate_siret

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Algorithme de Luhn pour validation
- Pas de side effects

Utilisation : 8+ endroits dans le codebase
"""

import re
from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro SIRET français.

    Le SIRET est composé de :
    - 9 chiffres (SIREN - identifiant entreprise)
    - 5 chiffres (NIC - identifiant établissement)

    Validation par algorithme de Luhn.

    Args:
        inputs: {"siret": str}

    Returns:
        {
            "is_valid": bool,
            "normalized_siret": str,
            "siren": str,
            "nic": str,
            "error": str | None
        }
    """
    siret = inputs["siret"]

    # Normalisation : suppression espaces et caractères non numériques
    normalized = re.sub(r'\D', '', siret)

    # Vérification longueur exacte (14 chiffres)
    if len(normalized) != 14:
        return {
            "is_valid": False,
            "normalized_siret": normalized,
            "siren": normalized[:9] if len(normalized) >= 9 else "",
            "nic": normalized[9:14] if len(normalized) >= 14 else "",
            "error": "Le SIRET doit contenir exactement 14 chiffres"
        }

    # Vérification que tous les caractères sont des chiffres
    if not normalized.isdigit():
        return {
            "is_valid": False,
            "normalized_siret": normalized,
            "siren": normalized[:9],
            "nic": normalized[9:14],
            "error": "Le SIRET doit contenir uniquement des chiffres"
        }

    # Extraction SIREN et NIC
    siren = normalized[:9]
    nic = normalized[9:14]

    # Validation avec algorithme de Luhn
    total = 0
    for i, digit in enumerate(normalized):
        d = int(digit)

        # Pour les positions paires (index 1, 3, 5...), on multiplie par 2
        if i % 2 == 1:
            d *= 2
            # Si le résultat est > 9, on soustrait 9
            if d > 9:
                d -= 9

        total += d

    # Le SIRET est valide si la somme est un multiple de 10
    is_valid = (total % 10) == 0

    if not is_valid:
        return {
            "is_valid": False,
            "normalized_siret": normalized,
            "siren": siren,
            "nic": nic,
            "error": "Le SIRET n'est pas valide (échec algorithme de Luhn)"
        }

    # SIRET valide
    return {
        "is_valid": True,
        "normalized_siret": normalized,
        "siren": siren,
        "nic": nic,
        "error": None
    }
