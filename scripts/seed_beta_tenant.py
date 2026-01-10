#!/usr/bin/env python3
"""
AZALS - Seed Beta Tenant Masith
================================
Script idempotent pour créer le premier tenant de bêta fermée.

SÉCURITÉ:
- Mot de passe JAMAIS stocké en clair
- Hash bcrypt avec salt automatique
- Changement de mot de passe obligatoire au premier login
- Logs d'audit sans exposition du mot de passe
- Isolation stricte par tenant

USAGE:
    python scripts/seed_beta_tenant.py

ENVIRONNEMENT REQUIS:
    - DATABASE_URL : URL de connexion PostgreSQL
    - Migrations 033_beta_tenant_fields.sql appliquées
"""

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ajout du chemin racine au PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.core.models import User, UserRole
from app.modules.tenants.models import (
    Tenant,
    TenantStatus,
    TenantEnvironment,
    SubscriptionPlan,
    TenantSettings,
    TenantOnboarding,
)

# Configuration du logging (sans données sensibles)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('azals.seed.beta')


# ============================================================================
# CONFIGURATION DU TENANT BETA
# ============================================================================

BETA_TENANT_CONFIG = {
    'tenant_id': 'masith',
    'name': 'MASITH',
    'legal_name': 'MASITH SARL',
    'email': 'contact@stephane-moreau.fr',
    'environment': TenantEnvironment.BETA,
    'status': TenantStatus.ACTIVE,
    'plan': SubscriptionPlan.PROFESSIONAL,
    'timezone': 'Europe/Paris',
    'language': 'fr',
    'currency': 'EUR',
    'country': 'FR',
    'max_users': 10,
    'max_storage_gb': 50,
}

BETA_ADMIN_CONFIG = {
    'email': 'contact@stephane-moreau.fr',
    'role': UserRole.ADMIN,  # tenant_admin = ADMIN dans l'enum existant
    'is_active': 1,
    'must_change_password': 1,  # Changement obligatoire au premier login
}

# Mot de passe initial temporaire (sera hashé, JAMAIS stocké en clair)
INITIAL_PASSWORD = 'gobelet'


# ============================================================================
# FONCTIONS DE CRÉATION
# ============================================================================

def create_beta_tenant(session) -> tuple[Tenant | None, bool]:
    """
    Crée le tenant beta si inexistant.

    Returns:
        tuple: (tenant, created) - tenant créé/existant et flag de création
    """
    tenant_id = BETA_TENANT_CONFIG['tenant_id']

    # Vérification idempotente
    existing_tenant = session.query(Tenant).filter(
        Tenant.tenant_id == tenant_id
    ).first()

    if existing_tenant:
        logger.info(
            f"Tenant '{tenant_id}' existe déjà (id={existing_tenant.id}, "
            f"environment={existing_tenant.environment}, status={existing_tenant.status})"
        )
        return existing_tenant, False

    # Création du nouveau tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        tenant_id=BETA_TENANT_CONFIG['tenant_id'],
        name=BETA_TENANT_CONFIG['name'],
        legal_name=BETA_TENANT_CONFIG['legal_name'],
        email=BETA_TENANT_CONFIG['email'],
        environment=BETA_TENANT_CONFIG['environment'],
        status=BETA_TENANT_CONFIG['status'],
        plan=BETA_TENANT_CONFIG['plan'],
        timezone=BETA_TENANT_CONFIG['timezone'],
        language=BETA_TENANT_CONFIG['language'],
        currency=BETA_TENANT_CONFIG['currency'],
        country=BETA_TENANT_CONFIG['country'],
        max_users=BETA_TENANT_CONFIG['max_users'],
        max_storage_gb=BETA_TENANT_CONFIG['max_storage_gb'],
        storage_used_gb=0,
        features={'beta_access': True, 'early_adopter': True},
        extra_data={'onboarded_by': 'system', 'beta_wave': 1},
        activated_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by='system:seed_beta_tenant',
    )

    session.add(tenant)
    logger.info(
        f"Tenant beta créé: tenant_id='{tenant_id}', "
        f"environment={tenant.environment.value}, status={tenant.status.value}"
    )

    return tenant, True


def create_tenant_settings(session, tenant: Tenant) -> tuple[TenantSettings | None, bool]:
    """
    Crée les paramètres du tenant si inexistants.
    """
    existing = session.query(TenantSettings).filter(
        TenantSettings.tenant_id == tenant.tenant_id
    ).first()

    if existing:
        logger.info(f"TenantSettings pour '{tenant.tenant_id}' existe déjà")
        return existing, False

    settings = TenantSettings(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        two_factor_required=False,  # Pas obligatoire en beta, mais recommandé
        session_timeout_minutes=60,
        password_expiry_days=90,
        notify_admin_on_signup=True,
        notify_admin_on_error=True,
        daily_digest_enabled=True,
        api_rate_limit=1000,
        auto_backup_enabled=True,
        backup_retention_days=30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(settings)
    logger.info(f"TenantSettings créé pour tenant '{tenant.tenant_id}'")

    return settings, True


def create_tenant_onboarding(session, tenant: Tenant) -> tuple[TenantOnboarding | None, bool]:
    """
    Crée le suivi d'onboarding du tenant si inexistant.
    """
    existing = session.query(TenantOnboarding).filter(
        TenantOnboarding.tenant_id == tenant.tenant_id
    ).first()

    if existing:
        logger.info(f"TenantOnboarding pour '{tenant.tenant_id}' existe déjà")
        return existing, False

    onboarding = TenantOnboarding(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        company_info_completed=True,  # Déjà renseigné
        admin_created=True,  # Sera créé par ce script
        users_invited=False,
        modules_configured=False,
        country_pack_selected=False,
        first_data_imported=False,
        training_completed=False,
        progress_percent=28,  # 2/7 étapes complétées
        current_step='users_invited',
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(onboarding)
    logger.info(f"TenantOnboarding créé pour tenant '{tenant.tenant_id}'")

    return onboarding, True


def create_beta_admin_user(session, tenant: Tenant) -> tuple[User | None, bool]:
    """
    Crée l'utilisateur admin du tenant beta si inexistant.

    SÉCURITÉ:
    - Le mot de passe est hashé avec bcrypt (salt automatique)
    - must_change_password=1 impose le changement au premier login
    - Aucune donnée sensible dans les logs

    Returns:
        tuple: (user, created) - user créé/existant et flag de création
    """
    email = BETA_ADMIN_CONFIG['email']

    # Vérification idempotente par email ET tenant_id
    existing_user = session.query(User).filter(
        User.email == email,
        User.tenant_id == tenant.tenant_id
    ).first()

    if existing_user:
        logger.info(
            f"Utilisateur '{email}' existe déjà pour tenant '{tenant.tenant_id}' "
            f"(id={existing_user.id}, role={existing_user.role.value}, "
            f"is_active={existing_user.is_active})"
        )
        return existing_user, False

    # Hash sécurisé du mot de passe (bcrypt avec salt automatique)
    password_hash = get_password_hash(INITIAL_PASSWORD)

    # Création de l'utilisateur admin
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        email=email,
        password_hash=password_hash,
        role=BETA_ADMIN_CONFIG['role'],
        is_active=BETA_ADMIN_CONFIG['is_active'],
        must_change_password=BETA_ADMIN_CONFIG['must_change_password'],
        password_changed_at=None,  # Jamais changé
        totp_enabled=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(user)

    # Log SANS le mot de passe ni le hash
    logger.info(
        f"Utilisateur admin créé: email='{email}', tenant_id='{tenant.tenant_id}', "
        f"role={user.role.value}, must_change_password=True"
    )

    return user, True


def log_audit_event(session, tenant_id: str, user_id: uuid.UUID, action: str, details: str):
    """
    Enregistre un événement d'audit dans le journal.
    """
    try:
        session.execute(
            text("""
                INSERT INTO core_audit_journal (id, tenant_id, user_id, action, details, created_at)
                VALUES (:id, :tenant_id, :user_id, :action, :details, :created_at)
            """),
            {
                'id': str(uuid.uuid4()),
                'tenant_id': tenant_id,
                'user_id': str(user_id),
                'action': action,
                'details': details,
                'created_at': datetime.utcnow(),
            }
        )
        logger.debug(f"Audit log: {action}")
    except Exception as e:
        logger.warning(f"Échec de l'audit log (non bloquant): {e}")


# ============================================================================
# VÉRIFICATIONS FINALES
# ============================================================================

def verify_tenant_isolation(session, tenant_id: str) -> bool:
    """
    Vérifie que les données du tenant sont correctement isolées.
    """
    # Vérification: tenant existe
    tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        logger.error(f"ÉCHEC: Tenant '{tenant_id}' introuvable")
        return False

    # Vérification: utilisateur lié au bon tenant
    user = session.query(User).filter(
        User.tenant_id == tenant_id,
        User.email == BETA_ADMIN_CONFIG['email']
    ).first()

    if not user:
        logger.error(f"ÉCHEC: Utilisateur admin introuvable pour tenant '{tenant_id}'")
        return False

    # Vérification: pas d'accès cross-tenant possible
    other_tenant_users = session.query(User).filter(
        User.tenant_id != tenant_id,
        User.email == BETA_ADMIN_CONFIG['email']
    ).count()

    if other_tenant_users > 0:
        logger.warning(
            f"ATTENTION: Email '{BETA_ADMIN_CONFIG['email']}' existe aussi dans d'autres tenants"
        )

    return True


def verify_password_security(session, user: User) -> bool:
    """
    Vérifie que le mot de passe est correctement sécurisé.
    """
    from app.core.security import verify_password

    # Vérification: le hash n'est PAS le mot de passe en clair
    if user.password_hash == INITIAL_PASSWORD:
        logger.error("ÉCHEC CRITIQUE: Mot de passe stocké en clair!")
        return False

    # Vérification: le hash commence par $2b$ (bcrypt)
    if not user.password_hash.startswith('$2b$'):
        logger.error("ÉCHEC: Hash de mot de passe invalide (pas bcrypt)")
        return False

    # Vérification: le mot de passe peut être vérifié
    if not verify_password(INITIAL_PASSWORD, user.password_hash):
        logger.error("ÉCHEC: Vérification du mot de passe échouée")
        return False

    # Vérification: must_change_password est actif
    if user.must_change_password != 1:
        logger.error("ÉCHEC: must_change_password n'est pas activé")
        return False

    logger.info("✓ Sécurité du mot de passe vérifiée (bcrypt, must_change_password=true)")
    return True


def verify_beta_environment(session, tenant: Tenant) -> bool:
    """
    Vérifie que le tenant est bien marqué comme beta.
    """
    if tenant.environment != TenantEnvironment.BETA:
        logger.error(
            f"ÉCHEC: Environnement incorrect "
            f"(attendu: beta, trouvé: {tenant.environment})"
        )
        return False

    if tenant.status != TenantStatus.ACTIVE:
        logger.error(
            f"ÉCHEC: Statut incorrect "
            f"(attendu: ACTIVE, trouvé: {tenant.status})"
        )
        return False

    logger.info(
        f"✓ Environnement beta vérifié (environment={tenant.environment.value}, "
        f"status={tenant.status.value})"
    )
    return True


def run_all_verifications(session, tenant: Tenant, user: User) -> bool:
    """
    Exécute toutes les vérifications de sécurité et conformité.
    """
    logger.info("=" * 60)
    logger.info("VÉRIFICATIONS FINALES")
    logger.info("=" * 60)

    all_passed = True

    if not verify_tenant_isolation(session, tenant.tenant_id):
        all_passed = False

    if not verify_password_security(session, user):
        all_passed = False

    if not verify_beta_environment(session, tenant):
        all_passed = False

    if all_passed:
        logger.info("=" * 60)
        logger.info("✓ TOUTES LES VÉRIFICATIONS PASSÉES")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("✗ CERTAINES VÉRIFICATIONS ONT ÉCHOUÉ")
        logger.error("=" * 60)

    return all_passed


# ============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================================

def main():
    """
    Point d'entrée principal du script de seed.
    """
    logger.info("=" * 60)
    logger.info("AZALS - Seed Beta Tenant Masith")
    logger.info("=" * 60)

    # Connexion à la base de données
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Création du tenant beta
        tenant, tenant_created = create_beta_tenant(session)
        if not tenant:
            raise RuntimeError("Échec de création/récupération du tenant")

        # 2. Création des paramètres du tenant
        create_tenant_settings(session, tenant)

        # 3. Création du suivi d'onboarding
        create_tenant_onboarding(session, tenant)

        # 4. Création de l'utilisateur admin
        user, user_created = create_beta_admin_user(session, tenant)
        if not user:
            raise RuntimeError("Échec de création/récupération de l'utilisateur")

        # 5. Commit de la transaction
        session.commit()
        logger.info("Transaction committée avec succès")

        # 6. Log d'audit (après commit pour avoir les IDs)
        if tenant_created:
            log_audit_event(
                session,
                tenant.tenant_id,
                user.id,
                'TENANT_CREATED',
                f'Tenant beta créé: {tenant.tenant_id}'
            )

        if user_created:
            log_audit_event(
                session,
                tenant.tenant_id,
                user.id,
                'USER_CREATED',
                f'Admin créé pour tenant beta (email masqué), must_change_password=true'
            )
            session.commit()

        # 7. Vérifications finales
        if not run_all_verifications(session, tenant, user):
            logger.warning("Des vérifications ont échoué, mais les données ont été créées")
            return 1

        # Résumé final
        logger.info("")
        logger.info("=" * 60)
        logger.info("RÉSUMÉ")
        logger.info("=" * 60)
        logger.info(f"Tenant ID     : {tenant.tenant_id}")
        logger.info(f"Environnement : {tenant.environment.value}")
        logger.info(f"Statut        : {tenant.status.value}")
        logger.info(f"Admin email   : {user.email}")
        logger.info(f"Admin rôle    : {user.role.value}")
        logger.info(f"Changement MDP: Obligatoire au premier login")
        logger.info("=" * 60)
        logger.info("✓ SEED TERMINÉ AVEC SUCCÈS")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        session.rollback()
        logger.error(f"ERREUR: {e}")
        logger.exception("Détails de l'erreur:")
        return 1

    finally:
        session.close()


if __name__ == '__main__':
    sys.exit(main())
