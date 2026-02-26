"""
Implémentation du sous-programme : validate_postal_code_fr

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 15+ endroits dans le codebase
"""

from typing import Dict, Any
import re


# Départements français métropolitains et DOM-TOM
DEPARTMENTS = {
    # Métropole
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze",
    "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir",
    "29": "Finistère", "30": "Gard", "31": "Haute-Garonne", "32": "Gers",
    "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre",
    "37": "Indre-et-Loire", "38": "Isère", "39": "Jura", "40": "Landes",
    "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique",
    "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère",
    "49": "Maine-et-Loire", "50": "Manche", "51": "Marne", "52": "Haute-Marne",
    "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan",
    "57": "Moselle", "58": "Nièvre", "59": "Nord", "60": "Oise",
    "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin", "68": "Haut-Rhin",
    "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire", "72": "Sarthe",
    "73": "Savoie", "74": "Haute-Savoie", "75": "Paris", "76": "Seine-Maritime",
    "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres", "80": "Somme",
    "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse",
    "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne", "88": "Vosges",
    "89": "Yonne", "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",

    # Corse
    "2A": "Corse-du-Sud", "2B": "Haute-Corse",
    "20": "Corse",  # Ancien code

    # DOM-TOM
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
    "974": "La Réunion", "975": "Saint-Pierre-et-Miquelon", "976": "Mayotte",
    "977": "Saint-Barthélemy", "978": "Saint-Martin",
    "986": "Wallis-et-Futuna", "987": "Polynésie française", "988": "Nouvelle-Calédonie",
}

# Régions administratives (2016)
REGIONS = {
    "01": "Auvergne-Rhône-Alpes", "03": "Auvergne-Rhône-Alpes", "07": "Auvergne-Rhône-Alpes",
    "15": "Auvergne-Rhône-Alpes", "26": "Auvergne-Rhône-Alpes", "38": "Auvergne-Rhône-Alpes",
    "42": "Auvergne-Rhône-Alpes", "43": "Auvergne-Rhône-Alpes", "63": "Auvergne-Rhône-Alpes",
    "69": "Auvergne-Rhône-Alpes", "73": "Auvergne-Rhône-Alpes", "74": "Auvergne-Rhône-Alpes",

    "21": "Bourgogne-Franche-Comté", "25": "Bourgogne-Franche-Comté", "39": "Bourgogne-Franche-Comté",
    "58": "Bourgogne-Franche-Comté", "70": "Bourgogne-Franche-Comté", "71": "Bourgogne-Franche-Comté",
    "89": "Bourgogne-Franche-Comté", "90": "Bourgogne-Franche-Comté",

    "22": "Bretagne", "29": "Bretagne", "35": "Bretagne", "56": "Bretagne",

    "18": "Centre-Val de Loire", "28": "Centre-Val de Loire", "36": "Centre-Val de Loire",
    "37": "Centre-Val de Loire", "41": "Centre-Val de Loire", "45": "Centre-Val de Loire",

    "2A": "Corse", "2B": "Corse", "20": "Corse",

    "08": "Grand Est", "10": "Grand Est", "51": "Grand Est", "52": "Grand Est",
    "54": "Grand Est", "55": "Grand Est", "57": "Grand Est", "67": "Grand Est", "68": "Grand Est", "88": "Grand Est",

    "02": "Hauts-de-France", "59": "Hauts-de-France", "60": "Hauts-de-France",
    "62": "Hauts-de-France", "80": "Hauts-de-France",

    "75": "Île-de-France", "77": "Île-de-France", "78": "Île-de-France", "91": "Île-de-France",
    "92": "Île-de-France", "93": "Île-de-France", "94": "Île-de-France", "95": "Île-de-France",

    "14": "Normandie", "27": "Normandie", "50": "Normandie", "61": "Normandie", "76": "Normandie",

    "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine", "19": "Nouvelle-Aquitaine",
    "23": "Nouvelle-Aquitaine", "24": "Nouvelle-Aquitaine", "33": "Nouvelle-Aquitaine",
    "40": "Nouvelle-Aquitaine", "47": "Nouvelle-Aquitaine", "64": "Nouvelle-Aquitaine",
    "79": "Nouvelle-Aquitaine", "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",

    "09": "Occitanie", "11": "Occitanie", "12": "Occitanie", "30": "Occitanie",
    "31": "Occitanie", "32": "Occitanie", "34": "Occitanie", "46": "Occitanie",
    "48": "Occitanie", "65": "Occitanie", "66": "Occitanie", "81": "Occitanie", "82": "Occitanie",

    "44": "Pays de la Loire", "49": "Pays de la Loire", "53": "Pays de la Loire",
    "72": "Pays de la Loire", "85": "Pays de la Loire",

    "04": "Provence-Alpes-Côte d'Azur", "05": "Provence-Alpes-Côte d'Azur",
    "06": "Provence-Alpes-Côte d'Azur", "13": "Provence-Alpes-Côte d'Azur",
    "83": "Provence-Alpes-Côte d'Azur", "84": "Provence-Alpes-Côte d'Azur",

    # DOM-TOM
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
    "974": "La Réunion", "976": "Mayotte",
}


def _normalize_postal_code(code: str) -> str:
    """Normalise un code postal (supprime espaces)."""
    return re.sub(r'\s', '', str(code).strip())


def _extract_department(code: str) -> str:
    """
    Extrait le code département d'un code postal.

    Gère les cas spéciaux:
    - Corse: 20xxx -> 2A ou 2B selon le code
    - DOM-TOM: 97xxx, 98xxx
    """
    if len(code) < 2:
        return ""

    # DOM-TOM (3 chiffres)
    if code.startswith("97") or code.startswith("98"):
        return code[:3]

    # Corse
    if code.startswith("20"):
        # 20000-20190 et 20600-20620: Corse-du-Sud (2A)
        # 20200-20290: Haute-Corse (2B)
        postal_num = int(code) if code.isdigit() else 0
        if 20000 <= postal_num <= 20190 or 20600 <= postal_num <= 20699:
            return "2A"
        elif 20200 <= postal_num <= 20299:
            return "2B"
        return "20"  # Corse générique si non déterminable

    # Métropole standard (2 chiffres)
    return code[:2]


def _is_valid_postal_code_range(code: str) -> bool:
    """Vérifie que le code postal est dans une plage valide."""
    if not code.isdigit():
        return False

    num = int(code)

    # Métropole: 01000-95999 (sauf 00xxx et 20xxx spécial)
    if 1000 <= num <= 95999:
        return True

    # DOM-TOM: 97100-97699, 98xxx
    if 97100 <= num <= 97699:
        return True
    if 98000 <= num <= 98999:
        return True

    return False


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide un code postal français.

    Format: 5 chiffres
    - 01000-95999: Métropole
    - 97xxx: DOM (Guadeloupe, Martinique, Guyane, Réunion, Mayotte)
    - 98xxx: COM (Polynésie, Nouvelle-Calédonie, Wallis-et-Futuna)

    Args:
        inputs: {
            "postal_code": string,  # Code postal à valider
        }

    Returns:
        {
            "is_valid": boolean,  # True si code postal valide
            "normalized_code": string,  # Code postal normalisé (5 chiffres)
            "department_code": string,  # Code département (2-3 caractères)
            "department_name": string,  # Nom du département
            "region": string,  # Nom de la région
            "is_dom_tom": boolean,  # True si DOM-TOM
            "error": string,  # Message d'erreur si invalide
        }
    """
    postal_code = inputs.get("postal_code", "")

    # Valeur vide
    if not postal_code:
        return {
            "is_valid": False,
            "normalized_code": None,
            "department_code": None,
            "department_name": None,
            "region": None,
            "is_dom_tom": None,
            "error": "Code postal requis"
        }

    # Normalisation
    normalized = _normalize_postal_code(postal_code)

    # Vérification que tous les caractères sont des chiffres
    if not normalized.isdigit():
        return {
            "is_valid": False,
            "normalized_code": normalized,
            "department_code": None,
            "department_name": None,
            "region": None,
            "is_dom_tom": None,
            "error": "Le code postal doit contenir uniquement des chiffres"
        }

    # Vérification longueur (5 chiffres)
    if len(normalized) != 5:
        return {
            "is_valid": False,
            "normalized_code": normalized,
            "department_code": None,
            "department_name": None,
            "region": None,
            "is_dom_tom": None,
            "error": f"Le code postal doit contenir 5 chiffres (reçu: {len(normalized)})"
        }

    # Vérification plage valide
    if not _is_valid_postal_code_range(normalized):
        return {
            "is_valid": False,
            "normalized_code": normalized,
            "department_code": None,
            "department_name": None,
            "region": None,
            "is_dom_tom": None,
            "error": "Code postal hors des plages valides"
        }

    # Extraction du département
    dept_code = _extract_department(normalized)

    # Vérification département reconnu
    if dept_code not in DEPARTMENTS:
        # Cas spécial: les codes postaux commençant par 00 n'existent pas
        if normalized.startswith("00"):
            return {
                "is_valid": False,
                "normalized_code": normalized,
                "department_code": None,
                "department_name": None,
                "region": None,
                "is_dom_tom": None,
                "error": "Code postal invalide (les codes 00xxx n'existent pas)"
            }

        return {
            "is_valid": False,
            "normalized_code": normalized,
            "department_code": dept_code,
            "department_name": None,
            "region": None,
            "is_dom_tom": None,
            "error": f"Département '{dept_code}' non reconnu"
        }

    # Récupération des informations
    dept_name = DEPARTMENTS[dept_code]
    region = REGIONS.get(dept_code, None)
    is_dom_tom = normalized.startswith("97") or normalized.startswith("98")

    return {
        "is_valid": True,
        "normalized_code": normalized,
        "department_code": dept_code,
        "department_name": dept_name,
        "region": region,
        "is_dom_tom": is_dom_tom,
        "error": None
    }
