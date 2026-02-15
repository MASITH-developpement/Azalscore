"""
AZALS - Validation des mots de passe
=====================================

Module centralisé pour la validation des mots de passe.
Utilisé par signup, auth, et tout autre module nécessitant
une validation de mot de passe.

SÉCURITÉ:
- Longueur: 8-128 caractères
- Complexité: majuscule, minuscule, chiffre, caractère spécial
- Anti-patterns: détection des mots de passe faibles courants
- Anti-DoS: limite maximale pour éviter les attaques bcrypt
"""

import re
from dataclasses import dataclass
from typing import List, Optional


# Configuration des règles de validation
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128  # Prévient DoS bcrypt (bcrypt tronque à 72 bytes)
MIN_UNIQUE_CHARS = 5  # Nombre minimum de caractères uniques

# Caractères spéciaux autorisés
SPECIAL_CHARS = set('!@#$%^&*()_+-=[]{}|;:,.<>?/~`\'"\\')

# Patterns faibles courants (en minuscules pour comparaison)
WEAK_PATTERNS = frozenset([
    # Mots courants
    'password', 'motdepasse', 'secret', 'admin', 'user', 'login',
    'welcome', 'letmein', 'changeme', 'default', 'root', 'test',
    # Séquences numériques
    '12345678', '123456789', '1234567890', '87654321',
    # Séquences clavier
    'qwerty', 'azerty', 'qwertz', 'asdfgh', 'zxcvbn', 'qweasd',
    # Mots populaires (top passwords)
    'monkey', 'master', 'dragon', 'shadow', 'sunshine', 'princess',
    'football', 'baseball', 'iloveyou', 'trustno1', 'superman',
    'batman', 'access', 'passw0rd', 'p@ssword', 'p@ssw0rd',
    # Français courants
    'bonjour', 'soleil', 'france', 'azerty123',
])

# Séquences clavier à éviter
KEYBOARD_SEQUENCES = frozenset([
    'qwerty', 'azerty', 'qwertz', 'asdfgh', 'zxcvbn',
    'qweasd', 'asdqwe', 'zaqwsx', '!@#$%^',
    '123456', '654321', '234567', '345678', '456789',
    'abcdef', 'fedcba', 'abcdefgh',
])


@dataclass
class PasswordValidationResult:
    """Résultat de la validation d'un mot de passe."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    strength_score: int  # 0-100


def validate_password(
    password: str,
    check_weak_patterns: bool = True,
    min_length: int = MIN_PASSWORD_LENGTH,
    max_length: int = MAX_PASSWORD_LENGTH,
) -> PasswordValidationResult:
    """
    Valide un mot de passe selon les règles de sécurité AZALS.

    Args:
        password: Le mot de passe à valider
        check_weak_patterns: Vérifier les patterns faibles (recommandé)
        min_length: Longueur minimale (défaut: 8)
        max_length: Longueur maximale (défaut: 128)

    Returns:
        PasswordValidationResult avec is_valid, errors, warnings, et strength_score
    """
    errors: List[str] = []
    warnings: List[str] = []
    strength_score = 0

    # Vérification de base: type
    if not isinstance(password, str):
        return PasswordValidationResult(
            is_valid=False,
            errors=["Le mot de passe doit être une chaîne de caractères"],
            warnings=[],
            strength_score=0
        )

    # Longueur maximale (anti-DoS)
    if len(password) > max_length:
        errors.append(f"Le mot de passe ne doit pas dépasser {max_length} caractères")
        return PasswordValidationResult(
            is_valid=False, errors=errors, warnings=warnings, strength_score=0
        )

    # Longueur minimale
    if len(password) < min_length:
        errors.append(f"Le mot de passe doit contenir au moins {min_length} caractères")
    else:
        strength_score += 20

    # Présence de majuscules
    if not any(c.isupper() for c in password):
        errors.append("Le mot de passe doit contenir au moins une majuscule")
    else:
        strength_score += 15

    # Présence de minuscules
    if not any(c.islower() for c in password):
        errors.append("Le mot de passe doit contenir au moins une minuscule")
    else:
        strength_score += 15

    # Présence de chiffres
    if not any(c.isdigit() for c in password):
        errors.append("Le mot de passe doit contenir au moins un chiffre")
    else:
        strength_score += 15

    # Présence de caractères spéciaux
    if not any(c in SPECIAL_CHARS for c in password):
        errors.append("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*...)")
    else:
        strength_score += 15

    # Diversité des caractères
    unique_chars = len(set(password))
    if unique_chars < MIN_UNIQUE_CHARS:
        errors.append(f"Le mot de passe doit contenir au moins {MIN_UNIQUE_CHARS} caractères différents")
    else:
        strength_score += min(10, unique_chars - MIN_UNIQUE_CHARS)

    # Vérifications des patterns faibles
    if check_weak_patterns:
        password_lower = password.lower()

        # Patterns faibles courants
        for pattern in WEAK_PATTERNS:
            if pattern in password_lower:
                errors.append(
                    f'Le mot de passe contient un pattern trop courant ("{pattern}")'
                )
                strength_score = max(0, strength_score - 20)
                break

        # Caractères répétitifs (ex: "aaaa", "1111")
        for i in range(len(password) - 3):
            if password[i] == password[i+1] == password[i+2] == password[i+3]:
                errors.append(
                    "Le mot de passe ne doit pas contenir 4 caractères identiques consécutifs"
                )
                strength_score = max(0, strength_score - 10)
                break

        # Séquences clavier
        for seq in KEYBOARD_SEQUENCES:
            if seq in password_lower:
                errors.append(
                    "Le mot de passe ne doit pas contenir de séquences clavier communes"
                )
                strength_score = max(0, strength_score - 10)
                break

    # Bonus de longueur
    if len(password) >= 12:
        strength_score += 5
    if len(password) >= 16:
        strength_score += 5

    # Warnings (non bloquants)
    if len(password) < 12:
        warnings.append("Un mot de passe de 12 caractères ou plus est recommandé")

    if unique_chars < 8:
        warnings.append("Utilisez plus de caractères différents pour un mot de passe plus fort")

    # Calcul final
    strength_score = min(100, max(0, strength_score))

    return PasswordValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        strength_score=strength_score
    )


def validate_password_or_raise(
    password: str,
    error_prefix: str = "",
    check_weak_patterns: bool = True,
) -> str:
    """
    Valide un mot de passe et lève une ValueError si invalide.

    Utile pour les validateurs Pydantic.

    Args:
        password: Le mot de passe à valider
        error_prefix: Préfixe pour les messages d'erreur
        check_weak_patterns: Vérifier les patterns faibles

    Returns:
        Le mot de passe validé

    Raises:
        ValueError: Si le mot de passe est invalide
    """
    result = validate_password(password, check_weak_patterns=check_weak_patterns)

    if not result.is_valid:
        # Retourner la première erreur (plus clair pour l'utilisateur)
        error_msg = result.errors[0] if result.errors else "Mot de passe invalide"
        if error_prefix:
            error_msg = f"{error_prefix}: {error_msg}"
        raise ValueError(error_msg)

    return password


def get_password_strength_label(score: int) -> str:
    """Retourne un label lisible pour le score de force du mot de passe."""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Fort"
    elif score >= 40:
        return "Moyen"
    elif score >= 20:
        return "Faible"
    else:
        return "Très faible"
