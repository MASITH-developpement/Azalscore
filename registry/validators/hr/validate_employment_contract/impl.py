"""
Implémentation du sous-programme : validate_employment_contract

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 8+ endroits dans le codebase
"""

from typing import Dict, Any
from datetime import datetime, date, timedelta


# Types de contrats français
CONTRACT_TYPES = {
    "CDI": {
        "name": "Contrat à Durée Indéterminée",
        "requires_end_date": False,
        "max_duration_months": None,
        "renewable": False,
        "trial_period_months": 4,  # Maximum légal pour cadres
    },
    "CDD": {
        "name": "Contrat à Durée Déterminée",
        "requires_end_date": True,
        "max_duration_months": 18,  # Renouvellements inclus
        "renewable": True,
        "max_renewals": 2,
        "trial_period_months": 1,
    },
    "CTT": {
        "name": "Contrat de Travail Temporaire (Intérim)",
        "requires_end_date": True,
        "max_duration_months": 18,
        "renewable": True,
        "max_renewals": 2,
        "trial_period_months": 0.5,
    },
    "APPRENTISSAGE": {
        "name": "Contrat d'Apprentissage",
        "requires_end_date": True,
        "min_duration_months": 6,
        "max_duration_months": 36,
        "renewable": False,
        "trial_period_months": 1.5,
    },
    "PROFESSIONNALISATION": {
        "name": "Contrat de Professionnalisation",
        "requires_end_date": True,
        "min_duration_months": 6,
        "max_duration_months": 24,
        "renewable": False,
        "trial_period_months": 1,
    },
    "STAGE": {
        "name": "Convention de Stage",
        "requires_end_date": True,
        "max_duration_months": 6,
        "renewable": False,
        "trial_period_months": 0,
    },
    "CUI": {
        "name": "Contrat Unique d'Insertion",
        "requires_end_date": True,
        "max_duration_months": 24,
        "renewable": True,
        "trial_period_months": 1,
    },
    "SEASONAL": {
        "name": "Contrat Saisonnier",
        "requires_end_date": True,
        "max_duration_months": 8,
        "renewable": True,
        "trial_period_months": 0.5,
    },
}


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

        # Format ISO: YYYY-MM-DD
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            parts = date_str.split('-')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and year >= 1900:
                    return date(year, month, day)

        # Format français: DD/MM/YYYY
        if len(date_str) == 10 and date_str[2] == '/' and date_str[5] == '/':
            parts = date_str.split('/')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and year >= 1900:
                    return date(year, month, day)

    return None


def _calculate_duration_months(start: date, end: date) -> float:
    """Calcule la durée en mois entre deux dates."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    # Ajustement pour les jours
    if end.day < start.day:
        months -= 1
    return months


def _format_date(d: date) -> str:
    """Formate une date en ISO."""
    return d.strftime("%Y-%m-%d")


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un contrat de travail selon le droit français.

    Vérifie:
    - Type de contrat reconnu
    - Cohérence des dates
    - Durée maximale selon le type
    - Règles spécifiques par type de contrat

    Args:
        inputs: {
            "contract_type": string,  # Type: CDI, CDD, CTT, APPRENTISSAGE, etc.
            "start_date": string/date,  # Date de début
            "end_date": string/date,  # Date de fin (optionnel pour CDI)
            "renewal_count": number,  # Nombre de renouvellements (optionnel)
            "weekly_hours": number,  # Heures hebdomadaires (optionnel)
            "employee_age": number,  # Âge du salarié (optionnel, pour apprentissage)
        }

    Returns:
        {
            "is_valid": boolean,  # True si contrat valide
            "contract_type": string,  # Type de contrat normalisé
            "contract_name": string,  # Nom complet du type
            "start_date": string,  # Date de début (ISO)
            "end_date": string,  # Date de fin (ISO)
            "duration_months": number,  # Durée en mois
            "max_trial_period_months": number,  # Période d'essai max
            "is_fixed_term": boolean,  # True si durée déterminée
            "warnings": array,  # Avertissements
            "error": string,  # Message d'erreur si invalide
        }
    """
    contract_type = inputs.get("contract_type", "")
    start_date_input = inputs.get("start_date")
    end_date_input = inputs.get("end_date")
    renewal_count = inputs.get("renewal_count", 0)
    weekly_hours = inputs.get("weekly_hours")
    employee_age = inputs.get("employee_age")

    warnings = []

    # Type de contrat requis
    if not contract_type:
        return {
            "is_valid": False,
            "contract_type": None,
            "contract_name": None,
            "start_date": None,
            "end_date": None,
            "duration_months": None,
            "max_trial_period_months": None,
            "is_fixed_term": None,
            "warnings": [],
            "error": "Type de contrat requis"
        }

    # Normalisation du type
    contract_type_upper = contract_type.strip().upper()

    # Vérification type reconnu
    if contract_type_upper not in CONTRACT_TYPES:
        return {
            "is_valid": False,
            "contract_type": contract_type_upper,
            "contract_name": None,
            "start_date": None,
            "end_date": None,
            "duration_months": None,
            "max_trial_period_months": None,
            "is_fixed_term": None,
            "warnings": [],
            "error": f"Type de contrat non reconnu: {contract_type_upper}. Types valides: {', '.join(CONTRACT_TYPES.keys())}"
        }

    contract_info = CONTRACT_TYPES[contract_type_upper]

    # Parsing de la date de début
    start_date = _parse_date(start_date_input)
    if start_date is None:
        return {
            "is_valid": False,
            "contract_type": contract_type_upper,
            "contract_name": contract_info["name"],
            "start_date": None,
            "end_date": None,
            "duration_months": None,
            "max_trial_period_months": contract_info["trial_period_months"],
            "is_fixed_term": contract_info["requires_end_date"],
            "warnings": [],
            "error": "Date de début invalide ou manquante"
        }

    # Parsing de la date de fin
    end_date = _parse_date(end_date_input) if end_date_input else None

    # Vérification date de fin requise
    if contract_info["requires_end_date"] and end_date is None:
        return {
            "is_valid": False,
            "contract_type": contract_type_upper,
            "contract_name": contract_info["name"],
            "start_date": _format_date(start_date),
            "end_date": None,
            "duration_months": None,
            "max_trial_period_months": contract_info["trial_period_months"],
            "is_fixed_term": True,
            "warnings": [],
            "error": f"Date de fin requise pour un {contract_type_upper}"
        }

    # Cohérence des dates
    if end_date and end_date <= start_date:
        return {
            "is_valid": False,
            "contract_type": contract_type_upper,
            "contract_name": contract_info["name"],
            "start_date": _format_date(start_date),
            "end_date": _format_date(end_date),
            "duration_months": None,
            "max_trial_period_months": contract_info["trial_period_months"],
            "is_fixed_term": contract_info["requires_end_date"],
            "warnings": [],
            "error": "La date de fin doit être postérieure à la date de début"
        }

    # Calcul de la durée
    duration_months = None
    if end_date:
        duration_months = _calculate_duration_months(start_date, end_date)

        # Vérification durée minimale
        min_duration = contract_info.get("min_duration_months")
        if min_duration and duration_months < min_duration:
            return {
                "is_valid": False,
                "contract_type": contract_type_upper,
                "contract_name": contract_info["name"],
                "start_date": _format_date(start_date),
                "end_date": _format_date(end_date),
                "duration_months": duration_months,
                "max_trial_period_months": contract_info["trial_period_months"],
                "is_fixed_term": True,
                "warnings": [],
                "error": f"Durée minimale pour un {contract_type_upper}: {min_duration} mois"
            }

        # Vérification durée maximale
        max_duration = contract_info.get("max_duration_months")
        if max_duration and duration_months > max_duration:
            return {
                "is_valid": False,
                "contract_type": contract_type_upper,
                "contract_name": contract_info["name"],
                "start_date": _format_date(start_date),
                "end_date": _format_date(end_date),
                "duration_months": duration_months,
                "max_trial_period_months": contract_info["trial_period_months"],
                "is_fixed_term": True,
                "warnings": [],
                "error": f"Durée maximale pour un {contract_type_upper}: {max_duration} mois"
            }

    # Vérification des renouvellements
    if renewal_count:
        max_renewals = contract_info.get("max_renewals", 0)
        if not contract_info.get("renewable"):
            warnings.append(f"Le {contract_type_upper} n'est pas renouvelable")
        elif renewal_count > max_renewals:
            return {
                "is_valid": False,
                "contract_type": contract_type_upper,
                "contract_name": contract_info["name"],
                "start_date": _format_date(start_date),
                "end_date": _format_date(end_date) if end_date else None,
                "duration_months": duration_months,
                "max_trial_period_months": contract_info["trial_period_months"],
                "is_fixed_term": contract_info["requires_end_date"],
                "warnings": [],
                "error": f"Nombre maximum de renouvellements pour un {contract_type_upper}: {max_renewals}"
            }

    # Vérifications spécifiques par type

    # Apprentissage: vérification de l'âge
    if contract_type_upper == "APPRENTISSAGE" and employee_age:
        if employee_age < 16:
            return {
                "is_valid": False,
                "contract_type": contract_type_upper,
                "contract_name": contract_info["name"],
                "start_date": _format_date(start_date),
                "end_date": _format_date(end_date) if end_date else None,
                "duration_months": duration_months,
                "max_trial_period_months": contract_info["trial_period_months"],
                "is_fixed_term": True,
                "warnings": [],
                "error": "L'apprenti doit avoir au moins 16 ans"
            }
        if employee_age > 29:
            warnings.append("L'âge maximum pour l'apprentissage est généralement 29 ans (dérogations possibles)")

    # Stage: vérification durée 6 mois max
    if contract_type_upper == "STAGE" and duration_months and duration_months > 6:
        return {
            "is_valid": False,
            "contract_type": contract_type_upper,
            "contract_name": contract_info["name"],
            "start_date": _format_date(start_date),
            "end_date": _format_date(end_date) if end_date else None,
            "duration_months": duration_months,
            "max_trial_period_months": 0,
            "is_fixed_term": True,
            "warnings": [],
            "error": "Un stage ne peut pas dépasser 6 mois par année d'enseignement"
        }

    # Heures hebdomadaires
    if weekly_hours:
        if weekly_hours > 48:
            return {
                "is_valid": False,
                "contract_type": contract_type_upper,
                "contract_name": contract_info["name"],
                "start_date": _format_date(start_date),
                "end_date": _format_date(end_date) if end_date else None,
                "duration_months": duration_months,
                "max_trial_period_months": contract_info["trial_period_months"],
                "is_fixed_term": contract_info["requires_end_date"],
                "warnings": [],
                "error": "La durée maximale hebdomadaire est de 48 heures"
            }
        if weekly_hours > 44:
            warnings.append("Attention: dépassement de la durée moyenne de 44h/semaine sur 12 semaines")
        if weekly_hours < 24 and contract_type_upper not in ["STAGE", "APPRENTISSAGE"]:
            warnings.append("Contrat à temps très partiel (moins de 24h/semaine)")

    # CDI avec date de fin (avertissement)
    if contract_type_upper == "CDI" and end_date:
        warnings.append("Un CDI ne devrait pas avoir de date de fin prédéfinie")

    return {
        "is_valid": True,
        "contract_type": contract_type_upper,
        "contract_name": contract_info["name"],
        "start_date": _format_date(start_date),
        "end_date": _format_date(end_date) if end_date else None,
        "duration_months": duration_months,
        "max_trial_period_months": contract_info["trial_period_months"],
        "is_fixed_term": contract_info["requires_end_date"],
        "warnings": warnings,
        "error": None
    }
