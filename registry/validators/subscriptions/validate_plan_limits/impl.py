"""
Implémentation du sous-programme : validate_plan_limits

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


# Plans prédéfinis avec leurs limites
DEFAULT_PLANS = {
    "free": {
        "display_name": "Gratuit",
        "users": 1,
        "storage_gb": 1,
        "api_calls_per_month": 1000,
        "projects": 3,
        "invoices_per_month": 10,
        "customers": 50,
        "products": 100,
        "support_level": "community",
    },
    "starter": {
        "display_name": "Starter",
        "users": 3,
        "storage_gb": 10,
        "api_calls_per_month": 10000,
        "projects": 10,
        "invoices_per_month": 100,
        "customers": 500,
        "products": 1000,
        "support_level": "email",
    },
    "professional": {
        "display_name": "Professionnel",
        "users": 10,
        "storage_gb": 50,
        "api_calls_per_month": 100000,
        "projects": 50,
        "invoices_per_month": 1000,
        "customers": 5000,
        "products": 10000,
        "support_level": "priority",
    },
    "business": {
        "display_name": "Business",
        "users": 50,
        "storage_gb": 200,
        "api_calls_per_month": 500000,
        "projects": 200,
        "invoices_per_month": 5000,
        "customers": 25000,
        "products": 50000,
        "support_level": "phone",
    },
    "enterprise": {
        "display_name": "Enterprise",
        "users": -1,  # -1 = illimité
        "storage_gb": -1,
        "api_calls_per_month": -1,
        "projects": -1,
        "invoices_per_month": -1,
        "customers": -1,
        "products": -1,
        "support_level": "dedicated",
    },
}

# Labels français pour les ressources
RESOURCE_LABELS = {
    "users": "utilisateurs",
    "storage_gb": "Go de stockage",
    "api_calls_per_month": "appels API/mois",
    "projects": "projets",
    "invoices_per_month": "factures/mois",
    "customers": "clients",
    "products": "produits",
}


def _to_number(value) -> float | None:
    """Convertit une valeur en nombre."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '.').replace(' ', '')
        if cleaned and cleaned.replace('.', '').replace('-', '').isdigit():
            return float(cleaned)
    return None


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide l'utilisation par rapport aux limites d'un plan d'abonnement.

    Args:
        inputs: {
            "plan_id": string,  # ID du plan (free, starter, professional, business, enterprise)
            "usage": dict,  # Utilisation actuelle {resource: value}
            "requested_increase": dict,  # Augmentation demandée {resource: value} (optionnel)
            "custom_limits": dict,  # Limites personnalisées (remplace les défauts)
        }

    Returns:
        {
            "is_valid": boolean,  # True si dans les limites
            "plan_id": string,  # Plan vérifié
            "plan_name": string,  # Nom affiché du plan
            "limits": dict,  # Limites du plan
            "usage": dict,  # Utilisation actuelle
            "usage_percentage": dict,  # Pourcentage d'utilisation par ressource
            "over_limit_resources": array,  # Ressources dépassant la limite
            "near_limit_resources": array,  # Ressources proches de la limite (>80%)
            "available_capacity": dict,  # Capacité restante par ressource
            "would_exceed_after_increase": dict,  # Ressources qui dépasseraient après augmentation
            "upgrade_recommended": boolean,  # Recommander une mise à niveau
            "error": string,  # Message d'erreur si dépassement
        }
    """
    plan_id = inputs.get("plan_id", "free")
    usage = inputs.get("usage", {})
    requested_increase = inputs.get("requested_increase", {})
    custom_limits = inputs.get("custom_limits", {})

    # Récupérer les limites du plan
    if plan_id not in DEFAULT_PLANS:
        return {
            "is_valid": False,
            "plan_id": plan_id,
            "plan_name": None,
            "limits": {},
            "usage": usage,
            "usage_percentage": {},
            "over_limit_resources": [],
            "near_limit_resources": [],
            "available_capacity": {},
            "would_exceed_after_increase": {},
            "upgrade_recommended": False,
            "error": f"Plan inconnu: {plan_id}"
        }

    plan = DEFAULT_PLANS[plan_id]
    plan_name = plan.get("display_name", plan_id)

    # Fusionner les limites personnalisées
    limits = {}
    for key, value in plan.items():
        if key != "display_name" and key != "support_level":
            limits[key] = custom_limits.get(key, value)

    # Calculer l'utilisation et les pourcentages
    usage_percentage = {}
    over_limit_resources = []
    near_limit_resources = []
    available_capacity = {}
    would_exceed_after_increase = {}

    for resource, limit in limits.items():
        current_usage = _to_number(usage.get(resource, 0)) or 0
        increase = _to_number(requested_increase.get(resource, 0)) or 0

        # -1 = illimité
        if limit == -1:
            usage_percentage[resource] = 0
            available_capacity[resource] = -1  # -1 = illimité
        else:
            # Pourcentage d'utilisation
            if limit > 0:
                pct = (current_usage / limit) * 100
                usage_percentage[resource] = round(pct, 1)

                # Capacité restante
                remaining = limit - current_usage
                available_capacity[resource] = max(0, remaining)

                # Vérifier dépassement
                if current_usage > limit:
                    over_limit_resources.append({
                        "resource": resource,
                        "label": RESOURCE_LABELS.get(resource, resource),
                        "usage": current_usage,
                        "limit": limit,
                        "excess": current_usage - limit,
                        "percentage": round(pct, 1)
                    })
                elif pct >= 80:
                    near_limit_resources.append({
                        "resource": resource,
                        "label": RESOURCE_LABELS.get(resource, resource),
                        "usage": current_usage,
                        "limit": limit,
                        "remaining": remaining,
                        "percentage": round(pct, 1)
                    })

                # Vérifier si l'augmentation demandée dépasserait
                if increase > 0:
                    new_usage = current_usage + increase
                    if new_usage > limit:
                        would_exceed_after_increase[resource] = {
                            "current": current_usage,
                            "requested_increase": increase,
                            "would_be": new_usage,
                            "limit": limit,
                            "excess": new_usage - limit
                        }
            else:
                usage_percentage[resource] = 0
                available_capacity[resource] = 0

    # Déterminer la validité
    is_valid = len(over_limit_resources) == 0 and len(would_exceed_after_increase) == 0

    # Recommander une mise à niveau
    upgrade_recommended = (
        len(over_limit_resources) > 0 or
        len(near_limit_resources) >= 2 or
        any(r.get("percentage", 0) >= 90 for r in near_limit_resources)
    ) and plan_id != "enterprise"

    # Message d'erreur
    error = None
    if over_limit_resources:
        exceeded = over_limit_resources[0]
        error = f"Limite dépassée pour {exceeded['label']}: {exceeded['usage']}/{exceeded['limit']}"
    elif would_exceed_after_increase:
        resource = list(would_exceed_after_increase.keys())[0]
        info = would_exceed_after_increase[resource]
        label = RESOURCE_LABELS.get(resource, resource)
        error = f"L'augmentation demandée dépasserait la limite de {label}: {info['would_be']}/{info['limit']}"

    return {
        "is_valid": is_valid,
        "plan_id": plan_id,
        "plan_name": plan_name,
        "limits": limits,
        "usage": usage,
        "usage_percentage": usage_percentage,
        "over_limit_resources": over_limit_resources,
        "near_limit_resources": near_limit_resources,
        "available_capacity": available_capacity,
        "would_exceed_after_increase": would_exceed_after_increase,
        "upgrade_recommended": upgrade_recommended,
        "error": error
    }
