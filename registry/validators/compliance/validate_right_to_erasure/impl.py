"""
Implémentation du sous-programme : validate_right_to_erasure

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 12+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date


# Motifs de refus légitimes selon RGPD art. 17.3
LEGITIMATE_REFUSAL_REASONS = {
    "legal_obligation": "Obligation légale de conservation",
    "public_interest": "Mission d'intérêt public",
    "public_health": "Intérêt public en matière de santé",
    "archiving": "Fins archivistiques dans l'intérêt public",
    "research": "Fins de recherche scientifique ou historique",
    "legal_claims": "Constatation, exercice ou défense de droits en justice",
}

# Délai de réponse RGPD (en jours)
RESPONSE_DEADLINE_DAYS = 30
EXTENSION_DEADLINE_DAYS = 60  # Avec justification


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
    Valide une demande de droit à l'effacement (RGPD art. 17).

    Vérifie:
    - Identité du demandeur
    - Périmètre de la demande
    - Absence de motifs de refus légitimes
    - Respect des délais de réponse

    Args:
        inputs: {
            "request": object,  # Objet demande d'effacement
                # requester_id: string - ID du demandeur
                # request_date: date - Date de la demande
                # data_scope: array - Périmètre des données
                # identity_verified: boolean - Identité vérifiée
                # has_active_contract: boolean - Contrat actif
                # has_pending_invoices: boolean - Factures en attente
                # has_legal_hold: boolean - Conservation légale
        }

    Returns:
        {
            "is_valid": boolean,  # True si demande recevable
            "request_date": string,  # Date de la demande
            "response_deadline": string,  # Date limite de réponse
            "days_remaining": number,  # Jours restants pour répondre
            "can_be_fulfilled": boolean,  # Peut être satisfaite
            "refusal_reasons": array,  # Motifs de refus si applicable
            "partial_erasure_possible": boolean,  # Effacement partiel possible
            "data_to_retain": array,  # Données à conserver
            "data_to_erase": array,  # Données à effacer
            "error": string,  # Message d'erreur si invalide
        }
    """
    request = inputs.get("request")

    # Objet requis
    if request is None:
        return {
            "is_valid": False,
            "request_date": None,
            "response_deadline": None,
            "days_remaining": None,
            "can_be_fulfilled": None,
            "refusal_reasons": None,
            "partial_erasure_possible": None,
            "data_to_retain": None,
            "data_to_erase": None,
            "error": "Demande requise"
        }

    if not isinstance(request, dict):
        return {
            "is_valid": False,
            "request_date": None,
            "response_deadline": None,
            "days_remaining": None,
            "can_be_fulfilled": None,
            "refusal_reasons": None,
            "partial_erasure_possible": None,
            "data_to_retain": None,
            "data_to_erase": None,
            "error": "La demande doit être un objet"
        }

    # Vérification identité
    identity_verified = request.get("identity_verified", False)
    if not identity_verified:
        return {
            "is_valid": False,
            "request_date": None,
            "response_deadline": None,
            "days_remaining": None,
            "can_be_fulfilled": False,
            "refusal_reasons": ["identity_not_verified"],
            "partial_erasure_possible": False,
            "data_to_retain": None,
            "data_to_erase": None,
            "error": "Identité du demandeur non vérifiée"
        }

    # Date de demande
    request_date = _parse_date(request.get("request_date"))
    if request_date is None:
        return {
            "is_valid": False,
            "request_date": None,
            "response_deadline": None,
            "days_remaining": None,
            "can_be_fulfilled": None,
            "refusal_reasons": None,
            "partial_erasure_possible": None,
            "data_to_retain": None,
            "data_to_erase": None,
            "error": "Date de demande requise"
        }

    # Calcul des délais
    today = date.today()
    from datetime import timedelta
    response_deadline = request_date + timedelta(days=RESPONSE_DEADLINE_DAYS)
    days_remaining = (response_deadline - today).days

    # Vérification des motifs de refus
    refusal_reasons = []
    data_to_retain = []
    data_to_erase = request.get("data_scope", ["all"])

    # Contrat actif
    if request.get("has_active_contract"):
        refusal_reasons.append("legal_obligation")
        data_to_retain.append("contract_data")

    # Factures en attente
    if request.get("has_pending_invoices"):
        refusal_reasons.append("legal_obligation")
        data_to_retain.append("billing_data")

    # Conservation légale
    if request.get("has_legal_hold"):
        refusal_reasons.append("legal_claims")
        data_to_retain.append("legal_hold_data")

    # Données comptables (obligation 10 ans)
    if "invoices" in data_to_erase or "all" in data_to_erase:
        refusal_reasons.append("legal_obligation")
        data_to_retain.append("accounting_records")

    # Déterminer si effacement possible
    can_be_fulfilled = len(refusal_reasons) == 0
    partial_erasure_possible = len(refusal_reasons) > 0 and len(data_to_retain) < len(data_to_erase)

    # Calculer données à effacer effectivement
    if not can_be_fulfilled:
        effective_erase = [d for d in data_to_erase if d not in data_to_retain]
        if "all" in data_to_erase:
            effective_erase = ["profile", "preferences", "activity_history"]
    else:
        effective_erase = data_to_erase

    # Déduplication des motifs
    refusal_reasons = list(set(refusal_reasons)) if refusal_reasons else None

    # Vérification délai dépassé
    if days_remaining < 0:
        return {
            "is_valid": False,
            "request_date": request_date.strftime("%Y-%m-%d"),
            "response_deadline": response_deadline.strftime("%Y-%m-%d"),
            "days_remaining": days_remaining,
            "can_be_fulfilled": can_be_fulfilled,
            "refusal_reasons": refusal_reasons,
            "partial_erasure_possible": partial_erasure_possible,
            "data_to_retain": data_to_retain if data_to_retain else None,
            "data_to_erase": effective_erase if effective_erase else None,
            "error": f"Délai de réponse dépassé de {abs(days_remaining)} jours"
        }

    return {
        "is_valid": True,
        "request_date": request_date.strftime("%Y-%m-%d"),
        "response_deadline": response_deadline.strftime("%Y-%m-%d"),
        "days_remaining": days_remaining,
        "can_be_fulfilled": can_be_fulfilled,
        "refusal_reasons": refusal_reasons,
        "partial_erasure_possible": partial_erasure_possible,
        "data_to_retain": data_to_retain if data_to_retain else None,
        "data_to_erase": effective_erase if effective_erase else None,
        "error": None
    }
