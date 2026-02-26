"""
Implémentation du sous-programme : validate_invoice_number

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
import re
from datetime import datetime, date


# Patterns de numérotation courants
DEFAULT_PATTERNS = {
    "yearly_sequential": r"^(?P<prefix>[A-Z]{0,5})-?(?P<year>\d{4})-?(?P<seq>\d{1,8})$",
    "monthly_sequential": r"^(?P<prefix>[A-Z]{0,5})-?(?P<year>\d{4})(?P<month>\d{2})-?(?P<seq>\d{1,6})$",
    "simple_sequential": r"^(?P<prefix>[A-Z]{0,5})-?(?P<seq>\d{1,10})$",
    "dated": r"^(?P<prefix>[A-Z]{0,5})-?(?P<date>\d{8})-?(?P<seq>\d{1,6})$",
}

# Préfixes de document courants
DOCUMENT_PREFIXES = {
    "FA": "facture",
    "FAC": "facture",
    "FACT": "facture",
    "FC": "facture_client",
    "FF": "facture_fournisseur",
    "AV": "avoir",
    "NC": "note_credit",
    "DE": "devis",
    "DEV": "devis",
    "BC": "bon_commande",
    "BL": "bon_livraison",
    "BR": "bon_retour",
}


def _extract_components(number: str, pattern: str) -> dict | None:
    """
    Extrait les composants d'un numéro selon un pattern.

    Returns:
        Dict avec les composants trouvés ou None si pas de match.
    """
    match = re.match(pattern, number.upper(), re.IGNORECASE)
    if not match:
        return None

    return match.groupdict()


def _validate_year(year_str: str) -> tuple[bool, int | None, str]:
    """
    Valide une année extraite d'un numéro de facture.

    Returns:
        (is_valid, year_int, error)
    """
    if not year_str or not year_str.isdigit():
        return False, None, "Année invalide"

    year = int(year_str)
    current_year = datetime.now().year

    # Année raisonnable: de 2000 à année courante + 1
    if year < 2000:
        return False, year, "Année antérieure à 2000"

    if year > current_year + 1:
        return False, year, f"Année future non autorisée (max: {current_year + 1})"

    return True, year, ""


def _validate_month(month_str: str) -> tuple[bool, int | None, str]:
    """
    Valide un mois extrait d'un numéro de facture.

    Returns:
        (is_valid, month_int, error)
    """
    if not month_str or not month_str.isdigit():
        return False, None, "Mois invalide"

    month = int(month_str)

    if month < 1 or month > 12:
        return False, month, f"Mois invalide (reçu: {month})"

    return True, month, ""


def _validate_sequence(seq_str: str) -> tuple[bool, int | None, str]:
    """
    Valide un numéro séquentiel.

    Returns:
        (is_valid, sequence_int, error)
    """
    if not seq_str or not seq_str.isdigit():
        return False, None, "Séquence invalide"

    seq = int(seq_str)

    if seq <= 0:
        return False, seq, "Le numéro séquentiel doit être positif"

    return True, seq, ""


def _detect_pattern(number: str) -> tuple[str | None, dict | None]:
    """
    Détecte automatiquement le pattern d'un numéro de facture.

    Returns:
        (pattern_name, components)
    """
    normalized = number.strip().upper()

    for pattern_name, pattern in DEFAULT_PATTERNS.items():
        components = _extract_components(normalized, pattern)
        if components:
            return pattern_name, components

    return None, None


def _validate_with_custom_pattern(number: str, pattern: str) -> tuple[bool, str]:
    """
    Valide un numéro avec un pattern personnalisé.

    Returns:
        (is_valid, error)
    """
    if not pattern:
        return True, ""

    # Vérifier si le pattern est valide
    # On utilise une approche simple sans try/except
    # Le pattern doit matcher le numéro
    if re.match(pattern, number, re.IGNORECASE):
        return True, ""

    return False, f"Le numéro ne correspond pas au format attendu: {pattern}"


def _detect_document_type(prefix: str) -> str | None:
    """Détecte le type de document selon le préfixe."""
    if not prefix:
        return None

    prefix_upper = prefix.upper()
    return DOCUMENT_PREFIXES.get(prefix_upper, None)


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un numéro de facture selon un format défini ou auto-détecté.

    Formats supportés:
    - yearly_sequential: [PREFIX]-YYYY-NNNNN (ex: FA-2024-00001)
    - monthly_sequential: [PREFIX]-YYYYMM-NNNN (ex: FAC-202401-0001)
    - simple_sequential: [PREFIX]-NNNNNNN (ex: 0000123)
    - dated: [PREFIX]-YYYYMMDD-NNN (ex: FA-20240115-001)
    - custom: Pattern regex personnalisé

    Args:
        inputs: {
            "invoice_number": string,  # Numéro de facture à valider
            "format_pattern": string,  # Pattern regex personnalisé (optionnel)
            "expected_prefix": string,  # Préfixe attendu (optionnel)
            "expected_year": number,  # Année attendue (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si numéro valide
            "normalized_number": string,  # Numéro normalisé
            "detected_pattern": string,  # Pattern détecté (yearly_sequential, etc.)
            "prefix": string,  # Préfixe extrait
            "document_type": string,  # Type de document détecté
            "year": number,  # Année extraite
            "month": number,  # Mois extrait (si applicable)
            "sequence": number,  # Numéro séquentiel
            "error": string,  # Message d'erreur si invalide
        }
    """
    invoice_number = inputs.get("invoice_number", "")
    format_pattern = inputs.get("format_pattern", "")
    expected_prefix = inputs.get("expected_prefix", "")
    expected_year = inputs.get("expected_year", None)

    # Valeur vide
    if not invoice_number:
        return {
            "is_valid": False,
            "normalized_number": None,
            "detected_pattern": None,
            "prefix": None,
            "document_type": None,
            "year": None,
            "month": None,
            "sequence": None,
            "error": "Numéro de facture requis"
        }

    # Normalisation (majuscules, suppression espaces excessifs)
    normalized = " ".join(str(invoice_number).strip().upper().split())

    # Longueur minimale
    if len(normalized) < 3:
        return {
            "is_valid": False,
            "normalized_number": normalized,
            "detected_pattern": None,
            "prefix": None,
            "document_type": None,
            "year": None,
            "month": None,
            "sequence": None,
            "error": "Numéro de facture trop court (minimum 3 caractères)"
        }

    # Validation avec pattern personnalisé si fourni
    if format_pattern:
        is_valid, error = _validate_with_custom_pattern(normalized, format_pattern)
        if not is_valid:
            return {
                "is_valid": False,
                "normalized_number": normalized,
                "detected_pattern": "custom",
                "prefix": None,
                "document_type": None,
                "year": None,
                "month": None,
                "sequence": None,
                "error": error
            }

    # Détection automatique du pattern
    pattern_name, components = _detect_pattern(normalized)

    if not components:
        # Si aucun pattern ne correspond mais un pattern personnalisé a validé
        if format_pattern:
            return {
                "is_valid": True,
                "normalized_number": normalized,
                "detected_pattern": "custom",
                "prefix": None,
                "document_type": None,
                "year": None,
                "month": None,
                "sequence": None,
                "error": None
            }

        return {
            "is_valid": False,
            "normalized_number": normalized,
            "detected_pattern": None,
            "prefix": None,
            "document_type": None,
            "year": None,
            "month": None,
            "sequence": None,
            "error": "Format de numéro de facture non reconnu"
        }

    # Extraction des composants
    prefix = components.get("prefix", "")
    year_str = components.get("year", "")
    month_str = components.get("month", "")
    seq_str = components.get("seq", "")
    date_str = components.get("date", "")

    # Validation du préfixe si attendu
    if expected_prefix and prefix and prefix.upper() != expected_prefix.upper():
        return {
            "is_valid": False,
            "normalized_number": normalized,
            "detected_pattern": pattern_name,
            "prefix": prefix,
            "document_type": _detect_document_type(prefix),
            "year": None,
            "month": None,
            "sequence": None,
            "error": f"Préfixe incorrect (attendu: {expected_prefix}, reçu: {prefix})"
        }

    # Extraction de l'année depuis la date si format dated
    if date_str and len(date_str) == 8:
        year_str = date_str[:4]
        month_str = date_str[4:6]

    # Validation de l'année
    year = None
    if year_str:
        is_valid_year, year, year_error = _validate_year(year_str)
        if not is_valid_year:
            return {
                "is_valid": False,
                "normalized_number": normalized,
                "detected_pattern": pattern_name,
                "prefix": prefix,
                "document_type": _detect_document_type(prefix),
                "year": year,
                "month": None,
                "sequence": None,
                "error": year_error
            }

        # Vérification année attendue
        if expected_year and year != expected_year:
            return {
                "is_valid": False,
                "normalized_number": normalized,
                "detected_pattern": pattern_name,
                "prefix": prefix,
                "document_type": _detect_document_type(prefix),
                "year": year,
                "month": None,
                "sequence": None,
                "error": f"Année incorrecte (attendu: {expected_year}, reçu: {year})"
            }

    # Validation du mois
    month = None
    if month_str:
        is_valid_month, month, month_error = _validate_month(month_str)
        if not is_valid_month:
            return {
                "is_valid": False,
                "normalized_number": normalized,
                "detected_pattern": pattern_name,
                "prefix": prefix,
                "document_type": _detect_document_type(prefix),
                "year": year,
                "month": month,
                "sequence": None,
                "error": month_error
            }

    # Validation de la séquence
    sequence = None
    if seq_str:
        is_valid_seq, sequence, seq_error = _validate_sequence(seq_str)
        if not is_valid_seq:
            return {
                "is_valid": False,
                "normalized_number": normalized,
                "detected_pattern": pattern_name,
                "prefix": prefix,
                "document_type": _detect_document_type(prefix),
                "year": year,
                "month": month,
                "sequence": sequence,
                "error": seq_error
            }

    return {
        "is_valid": True,
        "normalized_number": normalized,
        "detected_pattern": pattern_name,
        "prefix": prefix if prefix else None,
        "document_type": _detect_document_type(prefix) if prefix else None,
        "year": year,
        "month": month,
        "sequence": sequence,
        "error": None
    }
