"""
Implémentation du sous-programme : slugify

Convertit une chaîne de caractères en slug URL-friendly.
Utilisé pour URLs SEO des articles décisionnels, identifiants, etc.

RÈGLES STRICTES :
- Code métier PUR (pas de try/except externe)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

import re
import unicodedata
from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit une chaîne en slug (URL-friendly).

    Args:
        inputs: {
            "value": string - Texte à convertir en slug
            "max_length": int - Longueur max du slug (défaut: 60, optimal SEO)
            "separator": string - Séparateur à utiliser (défaut: "-")
        }

    Returns:
        {
            "slug": string - Slug URL-friendly
            "original_length": int - Longueur originale
            "was_truncated": bool - Si le slug a été tronqué
        }

    Examples:
        "ERP Décisionnel PME" -> "erp-decisionnel-pme"
        "Cockpit BI: 10 KPIs Essentiels!" -> "cockpit-bi-10-kpis-essentiels"
        "L'année 2026 sera décisive" -> "lannee-2026-sera-decisive"
    """
    value = inputs.get("value", "")
    max_length = inputs.get("max_length", 60)
    separator = inputs.get("separator", "-")

    # Valeur vide
    if not value or not isinstance(value, str):
        return {
            "slug": "",
            "original_length": 0,
            "was_truncated": False
        }

    original_length = len(value)

    # 1. Conversion en minuscules
    slug = value.lower()

    # 2. Normalisation unicode (NFKD)
    # Décompose les caractères accentués (é -> e + accent)
    slug = unicodedata.normalize('NFKD', slug)

    # 3. Suppression des accents (garder uniquement ASCII)
    slug = slug.encode('ascii', 'ignore').decode('ascii')

    # 4. Remplacement des apostrophes et caractères spéciaux courants
    # L'apostrophe devient rien (l'année -> lannee)
    slug = slug.replace("'", "")
    slug = slug.replace("'", "")  # Apostrophe typographique
    slug = slug.replace('"', "")
    slug = slug.replace('"', "")
    slug = slug.replace('"', "")

    # 5. Garder uniquement alphanumérique, espaces et tirets
    slug = re.sub(r'[^\w\s-]', '', slug)

    # 6. Remplacer espaces et underscores par le séparateur
    slug = re.sub(r'[\s_]+', separator, slug)

    # 7. Supprimer les séparateurs multiples consécutifs
    slug = re.sub(f'{re.escape(separator)}+', separator, slug)

    # 8. Trim séparateurs au début et à la fin
    slug = slug.strip(separator)

    # 9. Tronquer à la longueur maximale
    was_truncated = False
    if len(slug) > max_length:
        # Couper au dernier séparateur complet pour éviter les mots coupés
        slug = slug[:max_length]
        last_sep = slug.rfind(separator)
        if last_sep > max_length // 2:  # Si on trouve un séparateur dans la seconde moitié
            slug = slug[:last_sep]
        was_truncated = True

    # 10. Trim final au cas où
    slug = slug.strip(separator)

    return {
        "slug": slug,
        "original_length": original_length,
        "was_truncated": was_truncated
    }


def validate_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide les inputs avant exécution.

    Returns:
        {"valid": bool, "errors": list[str]}
    """
    errors = []

    if "value" not in inputs:
        errors.append("Le champ 'value' est requis")

    if "max_length" in inputs:
        max_length = inputs["max_length"]
        if not isinstance(max_length, int) or max_length < 1:
            errors.append("max_length doit être un entier positif")

    if "separator" in inputs:
        separator = inputs["separator"]
        if not isinstance(separator, str) or len(separator) != 1:
            errors.append("separator doit être un caractère unique")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
