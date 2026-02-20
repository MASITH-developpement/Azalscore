"""
Implémentation du sous-programme : validate_password_strength

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 8+ endroits dans le codebase
"""

from typing import Dict, Any
import re
import math


# Mots de passe communs à rejeter
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123", "azerty",
    "motdepasse", "admin", "admin123", "root", "toor", "welcome", "login",
}

# Séquences clavier à détecter
KEYBOARD_SEQUENCES = [
    "qwerty", "azerty", "qwertz", "asdfgh", "zxcvbn", "123456", "abcdef",
    "987654", "fedcba", "qazwsx", "1qaz2wsx"
]


def _check_character_types(password: str) -> dict:
    """Analyse les types de caractères présents."""
    return {
        "has_lowercase": bool(re.search(r'[a-z]', password)),
        "has_uppercase": bool(re.search(r'[A-Z]', password)),
        "has_digit": bool(re.search(r'\d', password)),
        "has_special": bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password)),
    }


def _check_sequences(password: str) -> bool:
    """Détecte les séquences prévisibles."""
    password_lower = password.lower()

    for seq in KEYBOARD_SEQUENCES:
        if seq in password_lower:
            return True

    # Séquences répétitives
    if re.search(r'(.)\1{2,}', password):
        return True

    return False


def _calculate_entropy(password: str) -> float:
    """Calcule l'entropie approximative."""
    charset_size = 0
    if re.search(r'[a-z]', password):
        charset_size += 26
    if re.search(r'[A-Z]', password):
        charset_size += 26
    if re.search(r'\d', password):
        charset_size += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
        charset_size += 32

    if charset_size == 0:
        return 0

    return len(password) * math.log2(charset_size)


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide la force d'un mot de passe selon des critères de sécurité.

    Args:
        inputs: {
            "password": string,  # Mot de passe à valider
            "min_length": number,  # Longueur minimale (défaut: 8)
        }

    Returns:
        {
            "is_valid": boolean,  # True si mot de passe valide
            "strength": string,  # Niveau: weak, fair, strong, very_strong
            "score": number,  # Score de force (0-100)
            "errors": array,  # Liste des erreurs/faiblesses
        }
    """
    password = inputs.get("password", "")
    min_length = inputs.get("min_length", 8)

    errors = []

    # Valeur vide
    if not password:
        return {
            "is_valid": False,
            "strength": "none",
            "score": 0,
            "errors": ["Mot de passe requis"]
        }

    # Vérification longueur
    if len(password) < min_length:
        errors.append(f"Minimum {min_length} caractères requis")

    # Analyse des caractères
    char_types = _check_character_types(password)

    if not char_types["has_lowercase"]:
        errors.append("Ajoutez des lettres minuscules")
    if not char_types["has_uppercase"]:
        errors.append("Ajoutez des lettres majuscules")
    if not char_types["has_digit"]:
        errors.append("Ajoutez des chiffres")

    # Vérification mot de passe commun
    if password.lower() in COMMON_PASSWORDS:
        errors.append("Mot de passe trop commun")

    # Vérification des séquences
    if _check_sequences(password):
        errors.append("Évitez les séquences prévisibles")

    # Calcul du score
    score = 0

    # Points pour la longueur
    score += min(len(password) * 3, 30)

    # Points pour les types de caractères
    type_count = sum(char_types.values())
    score += type_count * 15

    # Points pour la complexité
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10

    # Pénalités
    if password.lower() in COMMON_PASSWORDS:
        score -= 40
    if _check_sequences(password):
        score -= 20

    score = max(0, min(100, score))

    # Détermination du niveau
    if score < 30:
        strength = "weak"
    elif score < 50:
        strength = "fair"
    elif score < 75:
        strength = "strong"
    else:
        strength = "very_strong"

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "strength": strength,
        "score": score,
        "errors": errors if errors else None
    }
