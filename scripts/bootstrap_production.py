#!/usr/bin/env python3
"""
AZALSCORE - Bootstrap PRODUCTION DÉFINITIF
==========================================
Script d'initialisation UNIQUE de la plateforme en production.

EXÉCUTION UNIQUE - Ce script ne peut être lancé QU'UNE SEULE FOIS.

PRÉREQUIS OBLIGATOIRES:
    AZALS_ENV=prod
    DATABASE_URL=postgresql://...
    BOOTSTRAP_SECRET=<secret 32+ chars>
    ENCRYPTION_KEY=<fernet key>
    CORS_ORIGINS=https://...

USAGE:
    AZALS_ENV=prod python scripts/bootstrap_production.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import NoReturn

# Ajout racine au PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


# ============================================================================
# EXCEPTIONS
# ============================================================================

class BootstrapFatalError(Exception):
    """Erreur fatale du bootstrap - arrêt immédiat."""
    pass


class BootstrapAlreadyLocked(BootstrapFatalError):
    """Le bootstrap a déjà été exécuté."""
    pass


class EnvironmentError(BootstrapFatalError):
    """Configuration d'environnement invalide."""
    pass


class DataIntegrityError(BootstrapFatalError):
    """Violation d'intégrité des données."""
    pass


# ============================================================================
# CONFIGURATION PRODUCTION
# ============================================================================

# ============================================================================
# CONFIGURATION - LIRE DEPUIS ENVIRONNEMENT (SECURISE)
# ============================================================================
# AUCUN SECRET EN DUR - Tout est lu depuis les variables d'environnement

def _get_required_env(name: str, description: str) -> str:
    """Recupere une variable d'environnement obligatoire."""
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(f"{name} est OBLIGATOIRE: {description}")
    return value

def _get_optional_env(name: str, default: str) -> str:
    """Recupere une variable d'environnement optionnelle."""
    return os.environ.get(name, default)

# Valeurs par defaut pour tenant (personnalisables)
TENANT_SLUG = _get_optional_env("BOOTSTRAP_TENANT_SLUG", "default-tenant")
TENANT_NAME = _get_optional_env("BOOTSTRAP_TENANT_NAME", "Default Tenant")

# OBLIGATOIRE: Email et mot de passe admin depuis environnement
# ADMIN_EMAIL et ADMIN_PASSWORD doivent etre definis dans l'environnement
ADMIN_EMAIL = None  # Sera lu dynamiquement
ADMIN_PASSWORD = None  # Sera lu dynamiquement - JAMAIS EN DUR


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def fatal(message: str) -> NoReturn:
    """Arrêt fatal avec message d'erreur."""
    print(f"[FATAL] {message}", file=sys.stderr)
    sys.exit(1)


def log(message: str) -> None:
    """Log en console (stdout uniquement)."""
    print(f"[BOOTSTRAP] {message}")


def validate_environment() -> None:
    """
    Valide toutes les variables d'environnement obligatoires.
    Lève EnvironmentError si configuration invalide.
    """
    azals_env = os.environ.get("AZALS_ENV", "").lower()

    if azals_env != "prod":
        raise EnvironmentError(
            f"AZALS_ENV doit être 'prod' (valeur actuelle: '{azals_env or 'non définie'}')"
        )

    required_vars = [
        ("DATABASE_URL", "URL de connexion PostgreSQL"),
        ("BOOTSTRAP_SECRET", "Secret de bootstrap (min 32 caractères)"),
        ("ENCRYPTION_KEY", "Clé de chiffrement Fernet"),
        ("CORS_ORIGINS", "Origins CORS autorisées"),
        ("ADMIN_EMAIL", "Email de l'administrateur initial"),
        ("ADMIN_PASSWORD", "Mot de passe de l'administrateur (min 12 caractères, sera changé à la première connexion)"),
    ]

    missing = []
    for var, desc in required_vars:
        value = os.environ.get(var)
        if not value:
            missing.append(f"  - {var}: {desc}")

    if missing:
        raise EnvironmentError(
            "Variables d'environnement manquantes:\n" + "\n".join(missing)
        )

    # Validation BOOTSTRAP_SECRET
    bootstrap_secret = os.environ.get("BOOTSTRAP_SECRET", "")
    if len(bootstrap_secret) < 32:
        raise EnvironmentError(
            f"BOOTSTRAP_SECRET doit contenir au moins 32 caractères (actuel: {len(bootstrap_secret)})"
        )

    # Validation ADMIN_PASSWORD (securite)
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if len(admin_password) < 12:
        raise EnvironmentError(
            f"ADMIN_PASSWORD doit contenir au moins 12 caractères (actuel: {len(admin_password)})"
        )

    # Rejeter les mots de passe faibles
    weak_patterns = ["password", "123456", "admin", "azals", "changeme", "default"]
    for pattern in weak_patterns:
        if pattern in admin_password.lower():
            raise EnvironmentError(
                f"ADMIN_PASSWORD ne doit pas contenir '{pattern}'. Utilisez un mot de passe fort."
            )

    # Charger les valeurs dans les variables globales
    global ADMIN_EMAIL, ADMIN_PASSWORD
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    log("Variables d'environnement validées")


# ============================================================================
# FONCTIONS DE VÉRIFICATION
# ============================================================================

def check_bootstrap_lock(session) -> None:
    """
    Vérifie que le bootstrap n'est pas déjà verrouillé.
    Lève BootstrapAlreadyLocked si déjà exécuté.
    """
    from app.models.system_settings import SystemSettings

    settings = session.query(SystemSettings).first()

    if settings and settings.bootstrap_locked:
        raise BootstrapAlreadyLocked(
            "Le bootstrap a DÉJÀ été exécuté. "
            "Cette opération est IRRÉVERSIBLE et ne peut être lancée qu'une seule fois."
        )

    log("Verrou bootstrap: NON VERROUILLÉ (OK)")


def check_tenant_not_exists(session) -> None:
    """
    Vérifie que le tenant n'existe pas déjà.
    Lève DataIntegrityError si le tenant existe.
    """
    from app.modules.tenants.models import Tenant

    existing = session.query(Tenant).filter(
        Tenant.tenant_id == TENANT_SLUG
    ).first()

    if existing:
        raise DataIntegrityError(
            f"Le tenant '{TENANT_SLUG}' existe déjà (id={existing.id}). "
            "Le bootstrap ne peut pas être exécuté sur une base non vierge."
        )

    log(f"Tenant '{TENANT_SLUG}': INEXISTANT (OK)")


def check_admin_not_exists(session) -> None:
    """
    Vérifie que l'admin n'existe pas déjà.
    Lève DataIntegrityError si l'admin existe.
    """
    from app.core.models import User

    existing = session.query(User).filter(
        User.email == ADMIN_EMAIL
    ).first()

    if existing:
        raise DataIntegrityError(
            f"L'utilisateur '{ADMIN_EMAIL}' existe déjà (id={existing.id}). "
            "Le bootstrap ne peut pas être exécuté sur une base non vierge."
        )

    log(f"Admin '{ADMIN_EMAIL}': INEXISTANT (OK)")


# ============================================================================
# FONCTIONS DE CRÉATION
# ============================================================================

def create_tenant(session) -> uuid.UUID:
    """
    Crée le tenant principal MASITH en mode production.
    Retourne l'UUID du tenant créé.
    """
    from app.modules.tenants.models import (
        Tenant,
        TenantStatus,
        TenantEnvironment,
        SubscriptionPlan,
    )

    tenant_uuid = uuid.uuid4()
    now = datetime.utcnow()

    tenant = Tenant(
        id=tenant_uuid,
        tenant_id=TENANT_SLUG,
        name=TENANT_NAME,
        legal_name=f"{TENANT_NAME} SARL",
        email=ADMIN_EMAIL,
        environment=TenantEnvironment.PRODUCTION,
        status=TenantStatus.ACTIVE,
        plan=SubscriptionPlan.ENTERPRISE,
        timezone="Europe/Paris",
        language="fr",
        currency="EUR",
        country="FR",
        max_users=100,
        max_storage_gb=500,
        storage_used_gb=0,
        features={"production": True, "demo_disabled": True},
        extra_data={"bootstrap_date": now.isoformat(), "bootstrap_version": "1.0.0"},
        activated_at=now,
        created_at=now,
        updated_at=now,
        created_by="system:bootstrap_production",
    )

    session.add(tenant)
    log(f"Tenant créé: {TENANT_NAME} (id={tenant_uuid})")

    return tenant_uuid


def create_admin(session, tenant_id: str) -> uuid.UUID:
    """
    Crée l'administrateur initial avec changement de mot de passe obligatoire.
    Retourne l'UUID de l'utilisateur créé.
    """
    from app.core.models import User, UserRole
    from app.core.security import get_password_hash

    user_uuid = uuid.uuid4()
    now = datetime.utcnow()

    # Hash sécurisé du mot de passe (bcrypt)
    password_hash = get_password_hash(ADMIN_PASSWORD)

    user = User(
        id=user_uuid,
        tenant_id=tenant_id,
        email=ADMIN_EMAIL,
        password_hash=password_hash,
        role=UserRole.SUPERADMIN,
        is_active=1,
        must_change_password=1,  # OBLIGATOIRE
        password_changed_at=None,
        totp_enabled=0,
        created_at=now,
        updated_at=now,
    )

    session.add(user)
    log(f"Admin créé: {ADMIN_EMAIL} (role=SUPERADMIN, must_change_password=TRUE)")

    return user_uuid


def disable_demo_configuration(session) -> None:
    """
    Désactive toute configuration de démonstration.
    """
    from app.models.system_settings import SystemSettings

    settings = session.query(SystemSettings).first()

    if settings:
        settings.demo_mode_enabled = False
        settings.updated_at = datetime.utcnow()
        settings.updated_by = "system:bootstrap_production"
        log("Configuration démo désactivée (existante)")
    else:
        log("Aucune configuration démo à désactiver")


def lock_bootstrap(session) -> None:
    """
    Verrouille définitivement le bootstrap.
    Cette opération est IRRÉVERSIBLE.
    """
    from app.models.system_settings import SystemSettings

    now = datetime.utcnow()
    settings = session.query(SystemSettings).first()

    if not settings:
        settings = SystemSettings(
            id=uuid.uuid4(),
            bootstrap_locked=True,
            maintenance_mode=False,
            demo_mode_enabled=False,
            registration_enabled=True,
            platform_version="1.0.0",
            global_api_rate_limit=10000,
            extra_settings={"bootstrap_completed_at": now.isoformat()},
            created_at=now,
            updated_at=now,
            updated_by="system:bootstrap_production",
        )
        session.add(settings)
    else:
        settings.bootstrap_locked = True
        settings.demo_mode_enabled = False
        settings.updated_at = now
        settings.updated_by = "system:bootstrap_production"
        if settings.extra_settings:
            settings.extra_settings["bootstrap_completed_at"] = now.isoformat()
        else:
            settings.extra_settings = {"bootstrap_completed_at": now.isoformat()}

    log("BOOTSTRAP VERROUILLÉ DÉFINITIVEMENT")


# ============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================================

def main() -> int:
    """
    Point d'entrée principal du bootstrap production.
    Retourne 0 si succès, 1 si erreur.
    """
    print("=" * 70)
    print("AZALSCORE - BOOTSTRAP PRODUCTION DÉFINITIF")
    print("=" * 70)
    print()

    try:
        # 1. Validation environnement
        log("Étape 1/7: Validation environnement...")
        validate_environment()

        # 2. Connexion base de données
        log("Étape 2/7: Connexion base de données...")
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.config import get_settings

        settings = get_settings()
        engine = create_engine(settings.database_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        log("Connexion établie")

        # 3. Vérification verrou bootstrap
        log("Étape 3/7: Vérification verrou bootstrap...")
        check_bootstrap_lock(session)

        # 4. Vérification données existantes
        log("Étape 4/7: Vérification données existantes...")
        check_tenant_not_exists(session)
        check_admin_not_exists(session)

        # 5. Création des données
        log("Étape 5/7: Création tenant et admin...")
        tenant_uuid = create_tenant(session)
        create_admin(session, TENANT_SLUG)

        # 6. Désactivation démo
        log("Étape 6/7: Désactivation mode démo...")
        disable_demo_configuration(session)

        # 7. Verrouillage définitif
        log("Étape 7/7: Verrouillage bootstrap...")
        lock_bootstrap(session)

        # Commit atomique
        session.commit()
        session.close()

        print()
        print("=" * 70)
        print("BOOTSTRAP TERMINÉ AVEC SUCCÈS")
        print("=" * 70)
        print()
        print(f"  Tenant      : {TENANT_NAME} ({TENANT_SLUG})")
        print(f"  Admin       : {ADMIN_EMAIL}")
        print(f"  Role        : SUPERADMIN")
        print(f"  Password    : (temporaire - changement obligatoire)")
        print(f"  Mode        : PRODUCTION")
        print(f"  Démo        : DÉSACTIVÉE")
        print(f"  Bootstrap   : VERROUILLÉ")
        print()
        print("=" * 70)

        return 0

    except BootstrapAlreadyLocked as e:
        print()
        fatal(str(e))

    except EnvironmentError as e:
        print()
        fatal(str(e))

    except DataIntegrityError as e:
        print()
        fatal(str(e))

    except Exception as e:
        print()
        print(f"[ERROR] Erreur inattendue: {type(e).__name__}: {e}", file=sys.stderr)

        # Rollback si session existe
        try:
            session.rollback()
            session.close()
        except Exception:
            pass

        fatal("Le bootstrap a échoué. Aucune modification n'a été appliquée.")


if __name__ == "__main__":
    sys.exit(main())
