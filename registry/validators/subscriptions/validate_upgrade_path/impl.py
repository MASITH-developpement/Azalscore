"""
Implémentation du sous-programme : validate_upgrade_path

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 12+ endroits dans le codebase
"""

from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


# Hiérarchie des plans (niveau croissant)
PLAN_HIERARCHY = {
    "free": 0,
    "starter": 1,
    "professional": 2,
    "business": 3,
    "enterprise": 4,
}

# Prix mensuels par plan (en EUR)
PLAN_PRICES = {
    "free": Decimal("0.00"),
    "starter": Decimal("19.00"),
    "professional": Decimal("49.00"),
    "business": Decimal("99.00"),
    "enterprise": Decimal("299.00"),
}

# Noms affichés
PLAN_NAMES = {
    "free": "Gratuit",
    "starter": "Starter",
    "professional": "Professionnel",
    "business": "Business",
    "enterprise": "Enterprise",
}

# Transitions interdites
BLOCKED_TRANSITIONS = {
    # ("from_plan", "to_plan"): "raison"
}

# Transitions nécessitant une validation manuelle
MANUAL_APPROVAL_TRANSITIONS = {
    ("enterprise", "business"): "Downgrade depuis Enterprise nécessite une validation",
    ("enterprise", "professional"): "Downgrade depuis Enterprise nécessite une validation",
    ("enterprise", "starter"): "Downgrade depuis Enterprise nécessite une validation",
    ("enterprise", "free"): "Downgrade depuis Enterprise nécessite une validation",
    ("business", "free"): "Downgrade direct vers Gratuit déconseillé",
}


def _calculate_proration(
    from_plan: str,
    to_plan: str,
    days_remaining: int,
    billing_cycle_days: int
) -> dict:
    """Calcule le prorata pour un changement de plan."""
    from_price = PLAN_PRICES.get(from_plan, Decimal("0"))
    to_price = PLAN_PRICES.get(to_plan, Decimal("0"))

    if billing_cycle_days <= 0:
        billing_cycle_days = 30

    # Prix journalier
    from_daily = from_price / billing_cycle_days
    to_daily = to_price / billing_cycle_days

    # Crédit pour les jours restants sur l'ancien plan
    credit = (from_daily * days_remaining).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Coût pour les jours restants sur le nouveau plan
    charge = (to_daily * days_remaining).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Montant net (négatif = remboursement, positif = paiement)
    net_amount = (charge - credit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "credit_amount": float(credit),
        "charge_amount": float(charge),
        "net_amount": float(net_amount),
        "is_refund": net_amount < 0,
        "days_remaining": days_remaining,
        "billing_cycle_days": billing_cycle_days,
    }


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un changement de plan d'abonnement.

    Args:
        inputs: {
            "from_plan": string,  # Plan actuel
            "to_plan": string,  # Plan cible
            "days_remaining": number,  # Jours restants dans le cycle (optionnel)
            "billing_cycle_days": number,  # Durée du cycle de facturation (défaut: 30)
            "current_usage": dict,  # Utilisation actuelle (optionnel)
            "allow_downgrade": boolean,  # Autoriser les downgrades (défaut: true)
            "allow_immediate": boolean,  # Changement immédiat vs fin de cycle (défaut: true)
        }

    Returns:
        {
            "is_valid": boolean,  # True si transition autorisée
            "from_plan": string,  # Plan source
            "to_plan": string,  # Plan cible
            "from_plan_name": string,  # Nom affiché source
            "to_plan_name": string,  # Nom affiché cible
            "transition_type": string,  # upgrade, downgrade, same, lateral
            "price_difference": number,  # Différence de prix mensuel
            "price_difference_formatted": string,  # Différence formatée
            "proration": dict,  # Calcul du prorata
            "requires_manual_approval": boolean,  # Nécessite validation manuelle
            "data_loss_warning": boolean,  # Risque de perte de données (downgrade)
            "features_lost": array,  # Fonctionnalités perdues (downgrade)
            "features_gained": array,  # Fonctionnalités gagnées (upgrade)
            "effective_date": string,  # immediate ou end_of_cycle
            "error": string,  # Message d'erreur si invalide
        }
    """
    from_plan = inputs.get("from_plan", "").lower().strip()
    to_plan = inputs.get("to_plan", "").lower().strip()
    days_remaining = inputs.get("days_remaining", 0)
    billing_cycle_days = inputs.get("billing_cycle_days", 30)
    current_usage = inputs.get("current_usage", {})
    allow_downgrade = inputs.get("allow_downgrade", True)
    allow_immediate = inputs.get("allow_immediate", True)

    # Validation des plans
    if not from_plan:
        return {
            "is_valid": False,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "from_plan_name": None,
            "to_plan_name": None,
            "transition_type": None,
            "price_difference": None,
            "price_difference_formatted": None,
            "proration": None,
            "requires_manual_approval": False,
            "data_loss_warning": False,
            "features_lost": [],
            "features_gained": [],
            "effective_date": None,
            "error": "Plan actuel requis"
        }

    if not to_plan:
        return {
            "is_valid": False,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "from_plan_name": PLAN_NAMES.get(from_plan),
            "to_plan_name": None,
            "transition_type": None,
            "price_difference": None,
            "price_difference_formatted": None,
            "proration": None,
            "requires_manual_approval": False,
            "data_loss_warning": False,
            "features_lost": [],
            "features_gained": [],
            "effective_date": None,
            "error": "Plan cible requis"
        }

    if from_plan not in PLAN_HIERARCHY:
        return {
            "is_valid": False,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "from_plan_name": None,
            "to_plan_name": PLAN_NAMES.get(to_plan),
            "transition_type": None,
            "price_difference": None,
            "price_difference_formatted": None,
            "proration": None,
            "requires_manual_approval": False,
            "data_loss_warning": False,
            "features_lost": [],
            "features_gained": [],
            "effective_date": None,
            "error": f"Plan source inconnu: {from_plan}"
        }

    if to_plan not in PLAN_HIERARCHY:
        return {
            "is_valid": False,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "from_plan_name": PLAN_NAMES.get(from_plan),
            "to_plan_name": None,
            "transition_type": None,
            "price_difference": None,
            "price_difference_formatted": None,
            "proration": None,
            "requires_manual_approval": False,
            "data_loss_warning": False,
            "features_lost": [],
            "features_gained": [],
            "effective_date": None,
            "error": f"Plan cible inconnu: {to_plan}"
        }

    from_level = PLAN_HIERARCHY[from_plan]
    to_level = PLAN_HIERARCHY[to_plan]
    from_price = PLAN_PRICES[from_plan]
    to_price = PLAN_PRICES[to_plan]

    # Déterminer le type de transition
    if from_level < to_level:
        transition_type = "upgrade"
    elif from_level > to_level:
        transition_type = "downgrade"
    else:
        transition_type = "same"

    # Noms affichés
    from_plan_name = PLAN_NAMES.get(from_plan, from_plan)
    to_plan_name = PLAN_NAMES.get(to_plan, to_plan)

    # Différence de prix
    price_diff = float(to_price - from_price)
    if price_diff >= 0:
        price_diff_formatted = f"+{price_diff:.2f} €/mois"
    else:
        price_diff_formatted = f"{price_diff:.2f} €/mois"

    # Même plan
    if transition_type == "same":
        return {
            "is_valid": True,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "from_plan_name": from_plan_name,
            "to_plan_name": to_plan_name,
            "transition_type": "same",
            "price_difference": 0,
            "price_difference_formatted": "0.00 €/mois",
            "proration": None,
            "requires_manual_approval": False,
            "data_loss_warning": False,
            "features_lost": [],
            "features_gained": [],
            "effective_date": "immediate",
            "error": None
        }

    # Vérifier les transitions bloquées
    transition_key = (from_plan, to_plan)
    if transition_key in BLOCKED_TRANSITIONS:
        return {
            "is_valid": False,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "from_plan_name": from_plan_name,
            "to_plan_name": to_plan_name,
            "transition_type": transition_type,
            "price_difference": price_diff,
            "price_difference_formatted": price_diff_formatted,
            "proration": None,
            "requires_manual_approval": False,
            "data_loss_warning": False,
            "features_lost": [],
            "features_gained": [],
            "effective_date": None,
            "error": BLOCKED_TRANSITIONS[transition_key]
        }

    # Vérifier si downgrade autorisé
    if transition_type == "downgrade" and not allow_downgrade:
        return {
            "is_valid": False,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "from_plan_name": from_plan_name,
            "to_plan_name": to_plan_name,
            "transition_type": transition_type,
            "price_difference": price_diff,
            "price_difference_formatted": price_diff_formatted,
            "proration": None,
            "requires_manual_approval": False,
            "data_loss_warning": True,
            "features_lost": [],
            "features_gained": [],
            "effective_date": None,
            "error": "Les downgrades ne sont pas autorisés"
        }

    # Vérifier si approbation manuelle nécessaire
    requires_manual_approval = transition_key in MANUAL_APPROVAL_TRANSITIONS

    # Fonctionnalités gagnées/perdues (simplifiées)
    features_lost = []
    features_gained = []
    data_loss_warning = False

    if transition_type == "downgrade":
        data_loss_warning = True
        # Calculer les différences de limites
        level_diff = from_level - to_level
        if level_diff >= 1:
            features_lost.append("Réduction du nombre d'utilisateurs")
        if level_diff >= 2:
            features_lost.append("Réduction de l'espace de stockage")
            features_lost.append("Réduction des appels API")
        if from_plan == "enterprise":
            features_lost.append("Support dédié")
            features_lost.append("Ressources illimitées")
        if from_plan in ["enterprise", "business"]:
            features_lost.append("Support téléphonique")

    elif transition_type == "upgrade":
        level_diff = to_level - from_level
        if level_diff >= 1:
            features_gained.append("Plus d'utilisateurs")
        if level_diff >= 2:
            features_gained.append("Plus d'espace de stockage")
            features_gained.append("Plus d'appels API")
        if to_plan == "enterprise":
            features_gained.append("Support dédié")
            features_gained.append("Ressources illimitées")
        if to_plan in ["enterprise", "business"]:
            features_gained.append("Support téléphonique")

    # Calcul du prorata si jours restants spécifiés
    proration = None
    if days_remaining > 0 and allow_immediate:
        proration = _calculate_proration(
            from_plan, to_plan, days_remaining, billing_cycle_days
        )

    # Date effective
    if allow_immediate:
        effective_date = "immediate"
    else:
        effective_date = "end_of_cycle"

    return {
        "is_valid": True,
        "from_plan": from_plan,
        "to_plan": to_plan,
        "from_plan_name": from_plan_name,
        "to_plan_name": to_plan_name,
        "transition_type": transition_type,
        "price_difference": price_diff,
        "price_difference_formatted": price_diff_formatted,
        "proration": proration,
        "requires_manual_approval": requires_manual_approval,
        "data_loss_warning": data_loss_warning,
        "features_lost": features_lost,
        "features_gained": features_gained,
        "effective_date": effective_date,
        "error": None
    }
