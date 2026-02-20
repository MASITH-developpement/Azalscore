"""
Implémentation du sous-programme : validate_data_retention

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any


# Durées de rétention légales françaises (en jours)
LEGAL_RETENTION_PERIODS = {
    "invoices": {
        "min_days": 3650,  # 10 ans minimum
        "max_days": 3650,
        "description": "Factures et pièces comptables",
        "legal_basis": "Code de commerce L.123-22",
    },
    "contracts": {
        "min_days": 1825,  # 5 ans après fin du contrat
        "max_days": 3650,
        "description": "Contrats commerciaux",
        "legal_basis": "Code civil art. 2224",
    },
    "payroll": {
        "min_days": 1825,  # 5 ans
        "max_days": 1825,
        "description": "Bulletins de paie",
        "legal_basis": "Code du travail L.3243-4",
    },
    "tax_records": {
        "min_days": 2190,  # 6 ans
        "max_days": 2190,
        "description": "Documents fiscaux",
        "legal_basis": "Livre des procédures fiscales L.102 B",
    },
    "customer_data": {
        "min_days": 0,
        "max_days": 1095,  # 3 ans max après dernière interaction
        "description": "Données clients (RGPD)",
        "legal_basis": "RGPD art. 5.1.e",
    },
    "logs": {
        "min_days": 365,  # 1 an minimum
        "max_days": 365,
        "description": "Logs de connexion",
        "legal_basis": "LCEN",
    },
    "consent": {
        "min_days": 1095,  # 3 ans
        "max_days": 1825,  # 5 ans max
        "description": "Preuves de consentement",
        "legal_basis": "RGPD art. 7.1",
    },
    "medical": {
        "min_days": 7300,  # 20 ans
        "max_days": 7300,
        "description": "Dossiers médicaux",
        "legal_basis": "Code de la santé publique R.1112-7",
    },
}


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide une durée de rétention de données selon la réglementation.

    Vérifie que la durée de rétention est conforme aux obligations légales
    françaises et au RGPD.

    Args:
        inputs: {
            "retention_days": number,  # Durée de rétention en jours
            "data_type": string,  # Type de données (optionnel)
        }

    Returns:
        {
            "is_valid": boolean,  # True si durée valide
            "retention_days": number,  # Durée normalisée
            "retention_years": number,  # Durée en années
            "data_type": string,  # Type de données
            "min_required_days": number,  # Minimum légal
            "max_allowed_days": number,  # Maximum autorisé
            "legal_basis": string,  # Base légale
            "is_compliant": boolean,  # Conforme aux obligations
            "warning": string,  # Avertissement si proche des limites
            "error": string,  # Message d'erreur si invalide
        }
    """
    retention_days = inputs.get("retention_days")
    data_type = inputs.get("data_type", "customer_data")

    # Valeur requise
    if retention_days is None:
        return {
            "is_valid": False,
            "retention_days": None,
            "retention_years": None,
            "data_type": data_type,
            "min_required_days": None,
            "max_allowed_days": None,
            "legal_basis": None,
            "is_compliant": None,
            "warning": None,
            "error": "Durée de rétention requise"
        }

    # Conversion
    if not isinstance(retention_days, (int, float)):
        return {
            "is_valid": False,
            "retention_days": None,
            "retention_years": None,
            "data_type": data_type,
            "min_required_days": None,
            "max_allowed_days": None,
            "legal_basis": None,
            "is_compliant": None,
            "warning": None,
            "error": "Format de durée invalide"
        }

    retention_days = int(retention_days)

    # Valeur négative
    if retention_days < 0:
        return {
            "is_valid": False,
            "retention_days": retention_days,
            "retention_years": None,
            "data_type": data_type,
            "min_required_days": None,
            "max_allowed_days": None,
            "legal_basis": None,
            "is_compliant": None,
            "warning": None,
            "error": "Durée de rétention négative non autorisée"
        }

    # Récupération des règles pour le type de données
    data_type_lower = data_type.lower() if data_type else "customer_data"
    rules = LEGAL_RETENTION_PERIODS.get(data_type_lower)

    if rules is None:
        # Type non reconnu - règles génériques RGPD
        rules = LEGAL_RETENTION_PERIODS["customer_data"]
        data_type_lower = "customer_data"

    min_days = rules["min_days"]
    max_days = rules["max_days"]
    legal_basis = rules["legal_basis"]
    description = rules["description"]

    # Calcul en années
    retention_years = round(retention_days / 365, 1)

    # Vérification conformité
    warning = None
    is_compliant = True

    if retention_days < min_days:
        is_compliant = False
        return {
            "is_valid": False,
            "retention_days": retention_days,
            "retention_years": retention_years,
            "data_type": data_type_lower,
            "min_required_days": min_days,
            "max_allowed_days": max_days,
            "legal_basis": legal_basis,
            "is_compliant": False,
            "warning": None,
            "error": f"Durée insuffisante pour {description}. Minimum légal: {min_days} jours ({round(min_days/365, 1)} ans)"
        }

    if max_days > 0 and retention_days > max_days:
        is_compliant = False
        return {
            "is_valid": False,
            "retention_days": retention_days,
            "retention_years": retention_years,
            "data_type": data_type_lower,
            "min_required_days": min_days,
            "max_allowed_days": max_days,
            "legal_basis": legal_basis,
            "is_compliant": False,
            "warning": None,
            "error": f"Durée excessive (RGPD minimisation). Maximum: {max_days} jours ({round(max_days/365, 1)} ans)"
        }

    # Avertissements
    if min_days > 0 and retention_days < min_days * 1.1:
        warning = f"Proche du minimum légal ({min_days} jours)"
    elif max_days > 0 and retention_days > max_days * 0.9:
        warning = f"Proche du maximum autorisé ({max_days} jours)"

    return {
        "is_valid": True,
        "retention_days": retention_days,
        "retention_years": retention_years,
        "data_type": data_type_lower,
        "min_required_days": min_days,
        "max_allowed_days": max_days if max_days > 0 else None,
        "legal_basis": legal_basis,
        "is_compliant": is_compliant,
        "warning": warning,
        "error": None
    }
