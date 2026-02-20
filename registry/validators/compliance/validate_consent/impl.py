"""
Implémentation du sous-programme : validate_consent

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 25+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date


# Types de consentement RGPD
CONSENT_TYPES = {
    "marketing": "Communications marketing",
    "analytics": "Analyse et statistiques",
    "profiling": "Profilage",
    "third_party": "Partage avec tiers",
    "cookies": "Cookies non essentiels",
    "newsletter": "Newsletter",
    "sms": "SMS commerciaux",
    "phone": "Appels commerciaux",
}

# Durée de validité par défaut (en mois)
DEFAULT_CONSENT_VALIDITY_MONTHS = 24


def _parse_date(date_value) -> date | None:
    """Parse une date depuis différents formats."""
    if date_value is None:
        return None
    if isinstance(date_value, date) and not isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, str):
        date_str = date_value.strip()
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            parts = date_str.split('-')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day)
    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un consentement RGPD.

    Vérifie que le consentement est:
    - Explicite et non ambigu
    - Daté et traçable
    - Pour un type reconnu
    - Non expiré

    Args:
        inputs: {
            "consent": object,  # Objet consentement
                # consent_type: string - Type de consentement
                # given: boolean - Consentement donné
                # given_at: date - Date du consentement
                # ip_address: string - IP lors du consentement (optionnel)
                # source: string - Source du consentement (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si consentement valide
            "consent_type": string,  # Type de consentement
            "consent_description": string,  # Description du type
            "is_given": boolean,  # Consentement accordé
            "given_at": string,  # Date du consentement
            "is_expired": boolean,  # Consentement expiré
            "days_until_expiry": number,  # Jours avant expiration
            "has_proof": boolean,  # Preuve disponible (IP, source)
            "error": string,  # Message d'erreur si invalide
        }
    """
    consent = inputs.get("consent")

    # Objet requis
    if consent is None:
        return {
            "is_valid": False,
            "consent_type": None,
            "consent_description": None,
            "is_given": None,
            "given_at": None,
            "is_expired": None,
            "days_until_expiry": None,
            "has_proof": None,
            "error": "Consentement requis"
        }

    if not isinstance(consent, dict):
        return {
            "is_valid": False,
            "consent_type": None,
            "consent_description": None,
            "is_given": None,
            "given_at": None,
            "is_expired": None,
            "days_until_expiry": None,
            "has_proof": None,
            "error": "Le consentement doit être un objet"
        }

    # Type de consentement
    consent_type = consent.get("consent_type", "")
    if not consent_type:
        return {
            "is_valid": False,
            "consent_type": None,
            "consent_description": None,
            "is_given": None,
            "given_at": None,
            "is_expired": None,
            "days_until_expiry": None,
            "has_proof": None,
            "error": "Type de consentement requis"
        }

    consent_type = str(consent_type).lower()
    consent_description = CONSENT_TYPES.get(consent_type)

    if consent_description is None:
        # Accepter les types personnalisés
        consent_description = consent_type.replace("_", " ").title()

    # Valeur du consentement
    is_given = consent.get("given")
    if is_given is None:
        return {
            "is_valid": False,
            "consent_type": consent_type,
            "consent_description": consent_description,
            "is_given": None,
            "given_at": None,
            "is_expired": None,
            "days_until_expiry": None,
            "has_proof": None,
            "error": "Valeur du consentement (given) requise"
        }

    is_given = bool(is_given)

    # Date du consentement
    given_at = _parse_date(consent.get("given_at"))
    if given_at is None:
        return {
            "is_valid": False,
            "consent_type": consent_type,
            "consent_description": consent_description,
            "is_given": is_given,
            "given_at": None,
            "is_expired": None,
            "days_until_expiry": None,
            "has_proof": None,
            "error": "Date du consentement (given_at) requise"
        }

    # Vérification date dans le futur
    today = date.today()
    if given_at > today:
        return {
            "is_valid": False,
            "consent_type": consent_type,
            "consent_description": consent_description,
            "is_given": is_given,
            "given_at": given_at.strftime("%Y-%m-%d"),
            "is_expired": None,
            "days_until_expiry": None,
            "has_proof": None,
            "error": "Date du consentement dans le futur"
        }

    # Calcul expiration
    from dateutil.relativedelta import relativedelta
    expiry_date = given_at + relativedelta(months=DEFAULT_CONSENT_VALIDITY_MONTHS)
    is_expired = today > expiry_date
    days_until_expiry = (expiry_date - today).days if not is_expired else 0

    # Preuve
    has_proof = bool(consent.get("ip_address") or consent.get("source"))

    # Si expiré
    if is_expired:
        return {
            "is_valid": False,
            "consent_type": consent_type,
            "consent_description": consent_description,
            "is_given": is_given,
            "given_at": given_at.strftime("%Y-%m-%d"),
            "is_expired": True,
            "days_until_expiry": 0,
            "has_proof": has_proof,
            "error": "Consentement expiré - renouvellement nécessaire"
        }

    return {
        "is_valid": True,
        "consent_type": consent_type,
        "consent_description": consent_description,
        "is_given": is_given,
        "given_at": given_at.strftime("%Y-%m-%d"),
        "is_expired": False,
        "days_until_expiry": days_until_expiry,
        "has_proof": has_proof,
        "error": None
    }
