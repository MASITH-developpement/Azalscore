"""
Implémentation du sous-programme : validate_siren

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Algorithme de Luhn pour validation
- Pas de side effects
- Idempotent

Utilisation : 8+ endroits dans le codebase
"""

from typing import Dict, Any
import re


def _luhn_checksum(number: str) -> bool:
    """
    Valide un numéro avec l'algorithme de Luhn.

    Utilisé pour SIREN/SIRET en France.
    """
    total = 0
    for i, digit in enumerate(number):
        d = int(digit)

        # Pour les positions impaires (de droite, 1-indexé), on multiplie par 2
        # Note: pour SIREN/SIRET français, on commence de la gauche
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9

        total += d

    return total % 10 == 0


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro SIREN français (9 chiffres).

    Le SIREN (Système d'Identification du Répertoire des Entreprises)
    est un identifiant unique à 9 chiffres attribué par l'INSEE.

    Validation:
    - Exactement 9 chiffres
    - Algorithme de Luhn valide

    Args:
        inputs: {
            "siren": string,  # Numéro SIREN à valider
        }

    Returns:
        {
            "is_valid": boolean,  # True si SIREN valide
            "normalized_siren": string,  # SIREN normalisé (9 chiffres)
            "formatted_siren": string,  # SIREN formaté (XXX XXX XXX)
            "error": string,  # Message d'erreur si invalide
        }
    """
    siren = inputs.get("siren", "")

    # Valeur vide
    if not siren:
        return {
            "is_valid": False,
            "normalized_siren": None,
            "formatted_siren": None,
            "error": "SIREN requis"
        }

    # Normalisation: suppression espaces, tirets, points
    normalized = re.sub(r'[\s\-\.]', '', str(siren))

    # Vérification que tous les caractères sont des chiffres
    if not normalized.isdigit():
        return {
            "is_valid": False,
            "normalized_siren": normalized,
            "formatted_siren": None,
            "error": "Le SIREN doit contenir uniquement des chiffres"
        }

    # Vérification longueur exacte (9 chiffres)
    if len(normalized) != 9:
        return {
            "is_valid": False,
            "normalized_siren": normalized,
            "formatted_siren": None,
            "error": f"Le SIREN doit contenir exactement 9 chiffres (reçu: {len(normalized)})"
        }

    # Validation avec algorithme de Luhn
    if not _luhn_checksum(normalized):
        return {
            "is_valid": False,
            "normalized_siren": normalized,
            "formatted_siren": f"{normalized[:3]} {normalized[3:6]} {normalized[6:9]}",
            "error": "Le SIREN n'est pas valide (échec algorithme de Luhn)"
        }

    # Formatage: XXX XXX XXX
    formatted = f"{normalized[:3]} {normalized[3:6]} {normalized[6:9]}"

    return {
        "is_valid": True,
        "normalized_siren": normalized,
        "formatted_siren": formatted,
        "error": None
    }
