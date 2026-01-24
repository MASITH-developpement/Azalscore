"""
Implémentation du sous-programme : validate_email

Code métier PUR - Validation email RFC 5322
Utilisation : 30+ endroits dans le codebase
"""

import re
from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une adresse email.

    Pattern RFC 5322 simplifié mais robuste.
    """
    email = inputs["email"]

    # Normalisation
    normalized = email.strip().lower()

    # Pattern de validation (RFC 5322 simplifié)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Vérifications de base
    if not normalized:
        return {
            "is_valid": False,
            "normalized_email": "",
            "domain": "",
            "local_part": "",
            "error": "L'email ne peut pas être vide"
        }

    if '@' not in normalized:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "domain": "",
            "local_part": normalized,
            "error": "L'email doit contenir un symbole @"
        }

    # Split local_part et domain
    parts = normalized.split('@')
    if len(parts) != 2:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "domain": "",
            "local_part": "",
            "error": "L'email contient plusieurs symboles @"
        }

    local_part, domain = parts

    # Validation avec regex
    if not re.match(pattern, normalized):
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "domain": domain,
            "local_part": local_part,
            "error": "Format d'email invalide"
        }

    # Vérifications supplémentaires
    if len(local_part) > 64:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "domain": domain,
            "local_part": local_part,
            "error": "La partie locale ne peut pas dépasser 64 caractères"
        }

    if len(domain) > 255:
        return {
            "is_valid": False,
            "normalized_email": normalized,
            "domain": domain,
            "local_part": local_part,
            "error": "Le domaine ne peut pas dépasser 255 caractères"
        }

    # Email valide
    return {
        "is_valid": True,
        "normalized_email": normalized,
        "domain": domain,
        "local_part": local_part,
        "error": None
    }
