"""
AZALS - Garde-fous de Securite Runtime
=======================================
Module de verification ABSOLUE de la coherence environnement/version.

REGLES NON NEGOCIABLES:
-----------------------
1. PROD + version "-dev" = CRASH IMMEDIAT
2. DEV + version "-prod" = WARNING (autorise pour pre-prod)
3. PROD + DEBUG = CRASH IMMEDIAT
4. PROD + DB_AUTO_RESET_ON_VIOLATION = CRASH IMMEDIAT
5. PROD + secrets manquants = CRASH IMMEDIAT

Ce module DOIT etre appele:
- Au demarrage de l'application
- Avant toute connexion DB
- Avant toute migration/reset
"""

import os
import sys
import subprocess
from typing import Optional, Tuple
from dataclasses import dataclass


# =============================================================================
# EXCEPTIONS DE SECURITE
# =============================================================================

class SecurityGuardError(Exception):
    """Exception levee lors d'une violation de securite fatale."""
    pass


class EnvironmentVersionMismatchError(SecurityGuardError):
    """Erreur: incoherence entre environnement et version."""
    pass


class ProductionSecurityError(SecurityGuardError):
    """Erreur: configuration de securite invalide en production."""
    pass


class BranchEnvironmentError(SecurityGuardError):
    """Erreur: execution sur une branche interdite."""
    pass


# =============================================================================
# DETECTION DE LA BRANCHE GIT
# =============================================================================

def get_current_git_branch() -> Optional[str]:
    """
    Detecte la branche git courante.
    Retourne None si la detection echoue (pas un repo git, etc).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None


def is_main_branch() -> bool:
    """Retourne True si on est sur la branche main."""
    branch = get_current_git_branch()
    return branch == "main"


def is_develop_branch() -> bool:
    """Retourne True si on est sur la branche develop."""
    branch = get_current_git_branch()
    return branch == "develop"


# =============================================================================
# VERIFICATION ENVIRONNEMENT / VERSION
# =============================================================================

@dataclass
class SecurityStatus:
    """Etat de securite de l'application."""
    environment: str
    version: str
    branch: Optional[str]
    is_locked: bool
    warnings: list
    errors: list

    def __str__(self) -> str:
        status = "LOCKED" if self.is_locked else "UNLOCKED"
        return (
            f"[SECURITY] ENV={self.environment} | "
            f"VERSION={self.version} | "
            f"BRANCH={self.branch or 'unknown'} | "
            f"STATUS={status}"
        )


def enforce_env_version_consistency(settings, version: str) -> SecurityStatus:
    """
    Verifie la coherence entre l'environnement et la version.

    REGLES:
    - PROD + "-dev" = CRASH IMMEDIAT
    - DEV + "-prod" = WARNING (autorise)

    Args:
        settings: Instance de Settings (pydantic)
        version: Version de l'application (ex: "0.0.0-dev")

    Returns:
        SecurityStatus avec l'etat de la verification

    Raises:
        EnvironmentVersionMismatchError: Si PROD + "-dev"
    """
    warnings = []
    errors = []

    env = settings.environment
    is_prod = env == "production"
    is_dev_version = version.endswith("-dev")
    is_prod_version = version.endswith("-prod")

    branch = get_current_git_branch()

    # REGLE 1: PROD + "-dev" = FATAL
    if is_prod and is_dev_version:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "[FATAL] VIOLATION DE SECURITE CRITIQUE\n"
            "=" * 70 + "\n"
            f"ENVIRONNEMENT : {env}\n"
            f"VERSION       : {version}\n"
            f"BRANCHE       : {branch or 'unknown'}\n"
            "=" * 70 + "\n"
            "ERREUR: Version '-dev' INTERDITE en production.\n"
            "\n"
            "SOLUTION:\n"
            "1. Modifiez app/core/version.py\n"
            "2. Changez AZALS_VERSION en 'X.Y.Z-prod'\n"
            "3. Redemarrez l'application\n"
            "=" * 70
        )
        errors.append(error_msg)
        raise EnvironmentVersionMismatchError(error_msg)

    # REGLE 2: DEV + "-prod" = WARNING (autorise pour pre-prod/release)
    if not is_prod and is_prod_version:
        warning_msg = (
            f"[WARN] Version '{version}' en environnement '{env}'. "
            "Pre-production/release mode detecte."
        )
        warnings.append(warning_msg)
        print(warning_msg)

    is_locked = is_prod or (branch == "main")

    return SecurityStatus(
        environment=env,
        version=version,
        branch=branch,
        is_locked=is_locked,
        warnings=warnings,
        errors=errors
    )


# =============================================================================
# VERIFICATION DES SECRETS PRODUCTION
# =============================================================================

def enforce_production_secrets(settings) -> None:
    """
    Verifie que tous les secrets obligatoires sont presents en production.

    OBLIGATOIRES EN PROD:
    - BOOTSTRAP_SECRET (min 32 chars)
    - ENCRYPTION_KEY (Fernet key)
    - SECRET_KEY (deja valide par pydantic)

    Raises:
        ProductionSecurityError: Si un secret manque
    """
    if settings.environment != "production":
        return

    errors = []

    # BOOTSTRAP_SECRET
    if not settings.bootstrap_secret:
        errors.append("BOOTSTRAP_SECRET manquant")
    elif len(settings.bootstrap_secret) < 32:
        errors.append("BOOTSTRAP_SECRET < 32 caracteres")

    # ENCRYPTION_KEY
    if not settings.encryption_key:
        errors.append("ENCRYPTION_KEY manquant")

    # CORS_ORIGINS (obligatoire et strict)
    if not settings.cors_origins:
        errors.append("CORS_ORIGINS manquant")
    elif "localhost" in settings.cors_origins.lower():
        errors.append("localhost interdit dans CORS_ORIGINS en production")
    elif "*" in settings.cors_origins:
        errors.append("CORS_ORIGINS='*' interdit en production")

    if errors:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "[FATAL] SECRETS DE PRODUCTION MANQUANTS\n"
            "=" * 70 + "\n"
            + "\n".join(f"  - {e}" for e in errors) + "\n"
            "=" * 70 + "\n"
            "L'application ne peut pas demarrer en production\n"
            "sans une configuration de securite complete.\n"
            "=" * 70
        )
        raise ProductionSecurityError(error_msg)


# =============================================================================
# VERIFICATION DEBUG / RESET UUID
# =============================================================================

def enforce_production_safety(settings) -> None:
    """
    Verifie les regles de securite absolues en production.

    INTERDIT EN PROD:
    - DEBUG = true
    - DB_AUTO_RESET_ON_VIOLATION = true
    - DB_RESET_UUID = true

    Raises:
        ProductionSecurityError: Si une regle est violee
    """
    if settings.environment != "production":
        return

    errors = []

    # DEBUG interdit
    if settings.debug:
        errors.append("DEBUG=true INTERDIT en production")

    # Auto-reset interdit
    if settings.db_auto_reset_on_violation:
        errors.append("DB_AUTO_RESET_ON_VIOLATION=true INTERDIT en production")

    # Reset UUID interdit
    if settings.db_reset_uuid:
        errors.append("DB_RESET_UUID=true INTERDIT en production")

    # Verification variable d'environnement directe (bypass pydantic)
    if os.environ.get("DEBUG", "").lower() in ("true", "1", "yes"):
        errors.append("Variable DEBUG detectee dans l'environnement")

    if os.environ.get("DB_AUTO_RESET_ON_VIOLATION", "").lower() in ("true", "1", "yes"):
        errors.append("Variable DB_AUTO_RESET_ON_VIOLATION detectee dans l'environnement")

    if errors:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "[FATAL] CONFIGURATION DANGEREUSE EN PRODUCTION\n"
            "=" * 70 + "\n"
            + "\n".join(f"  - {e}" for e in errors) + "\n"
            "=" * 70 + "\n"
            "Ces configurations sont INTERDITES en production.\n"
            "Corrigez votre configuration et redemarrez.\n"
            "=" * 70
        )
        raise ProductionSecurityError(error_msg)


# =============================================================================
# VERIFICATION BRANCHE GIT
# =============================================================================

def enforce_branch_restrictions(settings) -> None:
    """
    Verifie les restrictions de branche.

    REGLES:
    - Branche 'main' ne peut PAS executer en mode DEV
    - Scripts DEV refuses sur 'main'

    Note: Cette fonction ne bloque pas en dev sur main,
    mais emet un warning severe. Le blocage est fait par les scripts bash.

    Returns:
        None (emet des warnings si necessaire)
    """
    branch = get_current_git_branch()

    if branch == "main" and settings.environment in ("development", "test"):
        # Warning severe mais pas de crash (le script bash doit bloquer)
        print(
            "\n" + "=" * 70 + "\n"
            "[SECURITY WARNING] MODE DEVELOPPEMENT SUR BRANCHE MAIN\n"
            "=" * 70 + "\n"
            f"BRANCHE      : {branch}\n"
            f"ENVIRONNEMENT: {settings.environment}\n"
            "=" * 70 + "\n"
            "ATTENTION: Le mode developpement ne devrait pas\n"
            "s'executer sur la branche main.\n"
            "Utilisez la branche 'develop' pour le developpement.\n"
            "=" * 70 + "\n"
        )


# =============================================================================
# VERIFICATION COMPLETE AU DEMARRAGE
# =============================================================================

def run_all_security_checks(settings, version: str) -> SecurityStatus:
    """
    Execute TOUTES les verifications de securite.

    A appeler au tout debut du demarrage de l'application.

    Args:
        settings: Instance de Settings
        version: AZALS_VERSION

    Returns:
        SecurityStatus

    Raises:
        SecurityGuardError: Si une verification critique echoue
    """
    # 1. Coherence environnement/version (FATAL si echec)
    status = enforce_env_version_consistency(settings, version)

    # 2. Restrictions de branche (warning)
    enforce_branch_restrictions(settings)

    # 3. Securite production (FATAL si echec)
    enforce_production_safety(settings)

    # 4. Secrets production (FATAL si echec)
    enforce_production_secrets(settings)

    return status


def log_security_status(status: SecurityStatus) -> None:
    """
    Affiche le statut de securite dans les logs de demarrage.

    Format:
    [SECURITY] ENV=prod | VERSION=0.0.0-prod | BRANCH=main | STATUS=LOCKED
    """
    print(str(status))


# =============================================================================
# FONCTION PRINCIPALE POUR MAIN.PY
# =============================================================================

def enforce_startup_security(settings) -> SecurityStatus:
    """
    Point d'entree principal pour les verifications de securite.

    A appeler dans lifespan() de main.py AVANT toute autre operation.

    Usage:
        from app.core.guards import enforce_startup_security
        from app.core.version import AZALS_VERSION

        security_status = enforce_startup_security(settings)
        log_security_status(security_status)

    Args:
        settings: Instance de Settings

    Returns:
        SecurityStatus

    Raises:
        SecurityGuardError: Si une verification critique echoue
    """
    from app.core.version import AZALS_VERSION

    status = run_all_security_checks(settings, AZALS_VERSION)
    log_security_status(status)

    return status
