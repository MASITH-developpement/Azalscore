"""
Implémentation du sous-programme : validate_full_address

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Champs requis pour une adresse complète
REQUIRED_FIELDS = ["street", "city", "postal_code", "country"]

# Champs optionnels
OPTIONAL_FIELDS = ["street2", "state", "region", "building", "floor", "apartment"]


def _validate_street(street: str) -> tuple[bool, str]:
    """Valide une adresse de rue."""
    if not street or not street.strip():
        return False, "Adresse de rue requise"

    street = street.strip()

    if len(street) < 3:
        return False, "Adresse de rue trop courte"

    if len(street) > 200:
        return False, "Adresse de rue trop longue"

    return True, ""


def _validate_city(city: str) -> tuple[bool, str]:
    """Valide un nom de ville."""
    if not city or not city.strip():
        return False, "Ville requise"

    city = city.strip()

    if len(city) < 2:
        return False, "Nom de ville trop court"

    if len(city) > 100:
        return False, "Nom de ville trop long"

    # Vérifier que c'est principalement alphabétique
    if not re.match(r'^[A-Za-zÀ-ÿ\s\-\'\.]+$', city):
        return False, "Nom de ville contient des caractères invalides"

    return True, ""


def _validate_postal_code(postal_code: str, country: str) -> tuple[bool, str]:
    """Valide un code postal selon le pays."""
    if not postal_code or not postal_code.strip():
        return False, "Code postal requis"

    postal_code = postal_code.strip()
    country_upper = country.upper() if country else ""

    # Patterns par pays
    patterns = {
        "FR": r'^\d{5}$',
        "BE": r'^\d{4}$',
        "CH": r'^\d{4}$',
        "DE": r'^\d{5}$',
        "ES": r'^\d{5}$',
        "IT": r'^\d{5}$',
        "UK": r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$',
        "US": r'^\d{5}(-\d{4})?$',
        "CA": r'^[A-Z]\d[A-Z]\s*\d[A-Z]\d$',
    }

    if country_upper in patterns:
        if not re.match(patterns[country_upper], postal_code, re.IGNORECASE):
            return False, f"Format de code postal invalide pour {country_upper}"

    return True, ""


def _validate_country(country: str) -> tuple[bool, str]:
    """Valide un code pays."""
    if not country or not country.strip():
        return False, "Pays requis"

    country = country.strip().upper()

    # Codes ISO 3166-1 alpha-2 courants
    valid_countries = {
        "FR", "DE", "ES", "IT", "BE", "NL", "PT", "UK", "GB", "CH", "AT",
        "PL", "CZ", "SK", "HU", "RO", "BG", "GR", "IE", "DK", "SE", "NO", "FI",
        "US", "CA", "MX", "BR", "AR", "CL", "CO", "PE",
        "CN", "JP", "KR", "IN", "AU", "NZ", "RU", "ZA",
    }

    if len(country) != 2:
        return False, "Code pays doit être au format ISO (2 lettres)"

    if country not in valid_countries:
        # On accepte quand même si format correct
        if not country.isalpha():
            return False, "Code pays invalide"

    return True, ""


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une adresse postale complète.

    Champs requis: street, city, postal_code, country
    Champs optionnels: street2, state, region, building, floor, apartment

    Args:
        inputs: {
            "address": object,  # Objet adresse avec les champs
        }

    Returns:
        {
            "is_valid": boolean,  # True si adresse valide
            "normalized_address": object,  # Adresse normalisée
            "missing_fields": array,  # Champs manquants
            "invalid_fields": array,  # Champs invalides
            "formatted_address": string,  # Adresse formatée sur plusieurs lignes
            "single_line": string,  # Adresse sur une ligne
            "error": string,  # Message d'erreur principal
        }
    """
    address = inputs.get("address")

    # Objet requis
    if address is None:
        return {
            "is_valid": False,
            "normalized_address": None,
            "missing_fields": REQUIRED_FIELDS,
            "invalid_fields": None,
            "formatted_address": None,
            "single_line": None,
            "error": "Adresse requise"
        }

    if not isinstance(address, dict):
        return {
            "is_valid": False,
            "normalized_address": None,
            "missing_fields": None,
            "invalid_fields": None,
            "formatted_address": None,
            "single_line": None,
            "error": "L'adresse doit être un objet"
        }

    # Vérification des champs requis
    missing_fields = []
    for field in REQUIRED_FIELDS:
        if field not in address or not address[field]:
            missing_fields.append(field)

    if missing_fields:
        return {
            "is_valid": False,
            "normalized_address": None,
            "missing_fields": missing_fields,
            "invalid_fields": None,
            "formatted_address": None,
            "single_line": None,
            "error": f"Champs requis manquants: {', '.join(missing_fields)}"
        }

    # Validation de chaque champ
    invalid_fields = []
    errors = []

    # Street
    is_valid, error = _validate_street(str(address.get("street", "")))
    if not is_valid:
        invalid_fields.append("street")
        errors.append(error)

    # City
    is_valid, error = _validate_city(str(address.get("city", "")))
    if not is_valid:
        invalid_fields.append("city")
        errors.append(error)

    # Country (valider avant postal_code car le format dépend du pays)
    country = str(address.get("country", "")).strip().upper()
    is_valid, error = _validate_country(country)
    if not is_valid:
        invalid_fields.append("country")
        errors.append(error)

    # Postal code
    postal_code = str(address.get("postal_code", "")).strip()
    is_valid, error = _validate_postal_code(postal_code, country)
    if not is_valid:
        invalid_fields.append("postal_code")
        errors.append(error)

    if invalid_fields:
        return {
            "is_valid": False,
            "normalized_address": None,
            "missing_fields": None,
            "invalid_fields": invalid_fields,
            "formatted_address": None,
            "single_line": None,
            "error": errors[0] if errors else "Champs invalides"
        }

    # Normalisation
    normalized = {
        "street": str(address["street"]).strip(),
        "city": str(address["city"]).strip().title(),
        "postal_code": postal_code.upper(),
        "country": country,
    }

    # Champs optionnels
    if address.get("street2"):
        normalized["street2"] = str(address["street2"]).strip()
    if address.get("state"):
        normalized["state"] = str(address["state"]).strip()
    if address.get("region"):
        normalized["region"] = str(address["region"]).strip()

    # Formatage
    lines = [normalized["street"]]
    if normalized.get("street2"):
        lines.append(normalized["street2"])
    lines.append(f"{normalized['postal_code']} {normalized['city']}")
    lines.append(normalized["country"])

    formatted = "\n".join(lines)
    single_line = ", ".join(lines)

    return {
        "is_valid": True,
        "normalized_address": normalized,
        "missing_fields": None,
        "invalid_fields": None,
        "formatted_address": formatted,
        "single_line": single_line,
        "error": None
    }
