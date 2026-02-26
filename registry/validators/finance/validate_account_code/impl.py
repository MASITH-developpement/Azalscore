"""
Implémentation du sous-programme : validate_account_code

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 25+ endroits dans le codebase
"""

from typing import Dict, Any


# Classification des comptes PCG (Plan Comptable Général France)
PCG_CLASSES = {
    "1": {
        "name": "Capitaux",
        "type": "BILAN",
        "nature": "PASSIF",
        "description": "Capitaux propres, emprunts, provisions"
    },
    "2": {
        "name": "Immobilisations",
        "type": "BILAN",
        "nature": "ACTIF",
        "description": "Immobilisations incorporelles, corporelles, financières"
    },
    "3": {
        "name": "Stocks",
        "type": "BILAN",
        "nature": "ACTIF",
        "description": "Stocks et en-cours"
    },
    "4": {
        "name": "Tiers",
        "type": "BILAN",
        "nature": "MIXTE",
        "description": "Créances et dettes d'exploitation"
    },
    "5": {
        "name": "Financier",
        "type": "BILAN",
        "nature": "ACTIF",
        "description": "Comptes financiers (banque, caisse)"
    },
    "6": {
        "name": "Charges",
        "type": "RESULTAT",
        "nature": "CHARGE",
        "description": "Comptes de charges"
    },
    "7": {
        "name": "Produits",
        "type": "RESULTAT",
        "nature": "PRODUIT",
        "description": "Comptes de produits"
    },
    "8": {
        "name": "Spéciaux",
        "type": "SPECIAL",
        "nature": "SPECIAL",
        "description": "Comptes spéciaux (engagements)"
    },
}

# Comptes interdits (ne peuvent pas être utilisés directement)
FORBIDDEN_ACCOUNTS = {
    "0": "Classe 0 non utilisée en PCG",
    "9": "Classe 9 réservée à la comptabilité analytique",
}

# Sous-classes PCG avec descriptions
PCG_SUBCLASSES = {
    # Classe 1
    "10": "Capital et réserves",
    "11": "Report à nouveau",
    "12": "Résultat de l'exercice",
    "13": "Subventions d'investissement",
    "14": "Provisions réglementées",
    "15": "Provisions pour risques et charges",
    "16": "Emprunts et dettes assimilées",
    "17": "Dettes rattachées à des participations",
    "18": "Comptes de liaison",
    # Classe 2
    "20": "Immobilisations incorporelles",
    "21": "Immobilisations corporelles",
    "22": "Immobilisations mises en concession",
    "23": "Immobilisations en cours",
    "25": "Parts dans entreprises liées",
    "26": "Participations",
    "27": "Autres immobilisations financières",
    "28": "Amortissements des immobilisations",
    "29": "Dépréciations des immobilisations",
    # Classe 3
    "31": "Matières premières",
    "32": "Autres approvisionnements",
    "33": "En-cours de production de biens",
    "34": "En-cours de production de services",
    "35": "Stocks de produits",
    "37": "Stocks de marchandises",
    "39": "Dépréciations des stocks",
    # Classe 4
    "40": "Fournisseurs",
    "41": "Clients",
    "42": "Personnel",
    "43": "Organismes sociaux",
    "44": "État et collectivités",
    "45": "Groupe et associés",
    "46": "Débiteurs et créditeurs divers",
    "47": "Comptes transitoires",
    "48": "Comptes de régularisation",
    "49": "Dépréciations des comptes de tiers",
    # Classe 5
    "50": "Valeurs mobilières de placement",
    "51": "Banques",
    "52": "Instruments de trésorerie",
    "53": "Caisse",
    "54": "Régies d'avances",
    "58": "Virements internes",
    "59": "Dépréciations VMP",
    # Classe 6
    "60": "Achats",
    "61": "Services extérieurs",
    "62": "Autres services extérieurs",
    "63": "Impôts et taxes",
    "64": "Charges de personnel",
    "65": "Autres charges de gestion",
    "66": "Charges financières",
    "67": "Charges exceptionnelles",
    "68": "Dotations aux amortissements",
    "69": "Participation et impôts",
    # Classe 7
    "70": "Ventes",
    "71": "Production stockée",
    "72": "Production immobilisée",
    "74": "Subventions d'exploitation",
    "75": "Autres produits de gestion",
    "76": "Produits financiers",
    "77": "Produits exceptionnels",
    "78": "Reprises sur amortissements",
    "79": "Transferts de charges",
}


def _get_account_class(account_code: str) -> str:
    """Retourne la classe du compte (premier chiffre)."""
    if account_code and len(account_code) >= 1:
        return account_code[0]
    return ""


def _get_account_subclass(account_code: str) -> str:
    """Retourne la sous-classe du compte (deux premiers chiffres)."""
    if account_code and len(account_code) >= 2:
        return account_code[:2]
    return ""


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un code de compte comptable selon le PCG (Plan Comptable Général).

    Args:
        inputs: {
            "account_code": string,  # Code compte à valider
            "chart_of_accounts": string,  # Référentiel (défaut: PCG)
        }

    Returns:
        {
            "is_valid": boolean,  # True si compte valide
            "account_type": string,  # Type: BILAN, RESULTAT, SPECIAL
            "account_nature": string,  # Nature: ACTIF, PASSIF, CHARGE, PRODUIT, MIXTE, SPECIAL
            "account_class": string,  # Classe (1-8)
            "account_class_name": string,  # Nom de la classe
            "account_subclass": string,  # Sous-classe (2 premiers chiffres)
            "account_subclass_name": string,  # Nom de la sous-classe
            "is_detail_account": boolean,  # True si compte de détail (6+ chiffres)
            "normalized_code": string,  # Code normalisé
            "error": string,  # Message d'erreur si invalide
        }
    """
    account_code = inputs.get("account_code", "")
    chart_of_accounts = inputs.get("chart_of_accounts", "PCG")

    # Valeur vide
    if not account_code or not isinstance(account_code, str):
        return {
            "is_valid": False,
            "account_type": None,
            "account_nature": None,
            "account_class": None,
            "account_class_name": None,
            "account_subclass": None,
            "account_subclass_name": None,
            "is_detail_account": None,
            "normalized_code": None,
            "error": "Code compte requis"
        }

    # Normalisation: supprime espaces, points
    normalized = account_code.strip().replace(" ", "").replace(".", "")

    # Vérification format numérique
    if not normalized.isdigit():
        return {
            "is_valid": False,
            "account_type": None,
            "account_nature": None,
            "account_class": None,
            "account_class_name": None,
            "account_subclass": None,
            "account_subclass_name": None,
            "is_detail_account": None,
            "normalized_code": normalized,
            "error": "Le code compte doit être numérique"
        }

    # Longueur minimale
    if len(normalized) < 2:
        return {
            "is_valid": False,
            "account_type": None,
            "account_nature": None,
            "account_class": None,
            "account_class_name": None,
            "account_subclass": None,
            "account_subclass_name": None,
            "is_detail_account": None,
            "normalized_code": normalized,
            "error": "Code compte trop court (minimum 2 chiffres)"
        }

    # Longueur maximale (selon PCG: généralement 6-8 chiffres max)
    if len(normalized) > 12:
        return {
            "is_valid": False,
            "account_type": None,
            "account_nature": None,
            "account_class": None,
            "account_class_name": None,
            "account_subclass": None,
            "account_subclass_name": None,
            "is_detail_account": None,
            "normalized_code": normalized,
            "error": "Code compte trop long (maximum 12 chiffres)"
        }

    # Extraction classe
    account_class = _get_account_class(normalized)

    # Vérification classe interdite
    if account_class in FORBIDDEN_ACCOUNTS:
        return {
            "is_valid": False,
            "account_type": None,
            "account_nature": None,
            "account_class": account_class,
            "account_class_name": None,
            "account_subclass": None,
            "account_subclass_name": None,
            "is_detail_account": None,
            "normalized_code": normalized,
            "error": FORBIDDEN_ACCOUNTS[account_class]
        }

    # Vérification classe valide
    if account_class not in PCG_CLASSES:
        return {
            "is_valid": False,
            "account_type": None,
            "account_nature": None,
            "account_class": account_class,
            "account_class_name": None,
            "account_subclass": None,
            "account_subclass_name": None,
            "is_detail_account": None,
            "normalized_code": normalized,
            "error": f"Classe de compte '{account_class}' non reconnue"
        }

    class_info = PCG_CLASSES[account_class]
    account_subclass = _get_account_subclass(normalized)
    subclass_name = PCG_SUBCLASSES.get(account_subclass, "")

    # Un compte de détail a généralement 6 chiffres ou plus
    is_detail_account = len(normalized) >= 6

    return {
        "is_valid": True,
        "account_type": class_info["type"],
        "account_nature": class_info["nature"],
        "account_class": account_class,
        "account_class_name": class_info["name"],
        "account_subclass": account_subclass,
        "account_subclass_name": subclass_name,
        "is_detail_account": is_detail_account,
        "normalized_code": normalized,
        "error": None
    }
