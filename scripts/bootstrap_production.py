#!/usr/bin/env python3
"""
AZALSCORE - Bootstrap PRODUCTION
================================
Creation of the main tenant + initial admin.
This script can only be run ONCE.

SECURITY:
- Password is NEVER stored in plain text
- Bcrypt hash with automatic salt
- Mandatory password change on first login
- Audit logs without password exposure
- Strict tenant isolation

USAGE:
    python scripts/bootstrap_production.py

PREREQUISITES:
    - DATABASE_URL: PostgreSQL connection URL
    - Alembic migrations applied (including system_settings table)
"""

import getpass
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add root path to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.core.models import User, UserRole
from app.models.system_settings import SystemSettings
from app.modules.tenants.models import (
    Tenant,
    TenantStatus,
    TenantEnvironment,
    SubscriptionPlan,
    TenantSettings,
    TenantOnboarding,
)

# Logging configuration (no sensitive data)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('azals.bootstrap.production')


# ============================================================================
# PRODUCTION TENANT CONFIGURATION
# ============================================================================

PROD_TENANT_CONFIG = {
    'tenant_id': 'masith',
    'name': 'MASITH',
    'legal_name': 'MASITH SARL',
    'email': 'contact@masith.fr',
    'environment': TenantEnvironment.PRODUCTION,
    'status': TenantStatus.ACTIVE,
    'plan': SubscriptionPlan.ENTERPRISE,
    'timezone': 'Europe/Paris',
    'language': 'fr',
    'currency': 'EUR',
    'country': 'FR',
    'max_users': 50,
    'max_storage_gb': 100,
}

PROD_ADMIN_CONFIG = {
    'email': 'contact@masith.fr',
    'role': UserRole.DIRIGEANT,  # Highest level for production
    'is_active': 1,
    'must_change_password': 1,  # Mandatory change on first login
}


# ============================================================================
# BOOTSTRAP CHECK
# ============================================================================

def check_bootstrap_lock(session) -> tuple[SystemSettings | None, bool]:
    """
    Check if bootstrap has already been executed.

    Returns:
        tuple: (settings, is_locked) - settings object and lock status
    """
    settings = session.query(SystemSettings).first()

    if settings and settings.bootstrap_locked:
        return settings, True

    return settings, False


def lock_bootstrap(session, settings: SystemSettings | None) -> SystemSettings:
    """
    Lock bootstrap to prevent re-execution.
    """
    if not settings:
        settings = SystemSettings(
            id=uuid.uuid4(),
            bootstrap_locked=True,
            demo_mode_enabled=False,  # Disable demo mode in production
            maintenance_mode=False,
            platform_version="1.0.0",
            registration_enabled=True,
            updated_by="system:bootstrap_production",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(settings)
        logger.info("SystemSettings created with bootstrap_locked=True")
    else:
        settings.bootstrap_locked = True
        settings.demo_mode_enabled = False
        settings.updated_by = "system:bootstrap_production"
        settings.updated_at = datetime.utcnow()
        logger.info("SystemSettings updated: bootstrap_locked=True")

    return settings


# ============================================================================
# CREATION FUNCTIONS
# ============================================================================

def create_production_tenant(session) -> tuple[Tenant | None, bool]:
    """
    Create the production tenant if it doesn't exist.

    Returns:
        tuple: (tenant, created) - created/existing tenant and creation flag
    """
    tenant_id = PROD_TENANT_CONFIG['tenant_id']

    # Idempotent check
    existing_tenant = session.query(Tenant).filter(
        Tenant.tenant_id == tenant_id
    ).first()

    if existing_tenant:
        logger.info(
            f"Tenant '{tenant_id}' already exists (id={existing_tenant.id}, "
            f"environment={existing_tenant.environment}, status={existing_tenant.status})"
        )
        return existing_tenant, False

    # Create new tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        tenant_id=PROD_TENANT_CONFIG['tenant_id'],
        name=PROD_TENANT_CONFIG['name'],
        legal_name=PROD_TENANT_CONFIG['legal_name'],
        email=PROD_TENANT_CONFIG['email'],
        environment=PROD_TENANT_CONFIG['environment'],
        status=PROD_TENANT_CONFIG['status'],
        plan=PROD_TENANT_CONFIG['plan'],
        timezone=PROD_TENANT_CONFIG['timezone'],
        language=PROD_TENANT_CONFIG['language'],
        currency=PROD_TENANT_CONFIG['currency'],
        country=PROD_TENANT_CONFIG['country'],
        max_users=PROD_TENANT_CONFIG['max_users'],
        max_storage_gb=PROD_TENANT_CONFIG['max_storage_gb'],
        storage_used_gb=0,
        features={'production': True, 'full_access': True},
        extra_data={'bootstrapped_by': 'system', 'bootstrap_date': datetime.utcnow().isoformat()},
        activated_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by='system:bootstrap_production',
    )

    session.add(tenant)
    logger.info(
        f"Production tenant created: tenant_id='{tenant_id}', "
        f"environment={tenant.environment.value}, status={tenant.status.value}"
    )

    return tenant, True


def create_tenant_settings(session, tenant: Tenant) -> tuple[TenantSettings | None, bool]:
    """
    Create tenant settings if they don't exist.
    """
    existing = session.query(TenantSettings).filter(
        TenantSettings.tenant_id == tenant.tenant_id
    ).first()

    if existing:
        logger.info(f"TenantSettings for '{tenant.tenant_id}' already exists")
        return existing, False

    settings = TenantSettings(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        two_factor_required=True,  # Required in production
        session_timeout_minutes=30,
        password_expiry_days=90,
        notify_admin_on_signup=True,
        notify_admin_on_error=True,
        daily_digest_enabled=True,
        api_rate_limit=5000,
        auto_backup_enabled=True,
        backup_retention_days=90,  # Longer retention for production
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(settings)
    logger.info(f"TenantSettings created for tenant '{tenant.tenant_id}'")

    return settings, True


def create_tenant_onboarding(session, tenant: Tenant) -> tuple[TenantOnboarding | None, bool]:
    """
    Create tenant onboarding tracking if it doesn't exist.
    """
    existing = session.query(TenantOnboarding).filter(
        TenantOnboarding.tenant_id == tenant.tenant_id
    ).first()

    if existing:
        logger.info(f"TenantOnboarding for '{tenant.tenant_id}' already exists")
        return existing, False

    onboarding = TenantOnboarding(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        company_info_completed=True,  # Already filled
        admin_created=True,  # Created by this script
        users_invited=False,
        modules_configured=False,
        country_pack_selected=True,  # FR by default
        first_data_imported=False,
        training_completed=False,
        progress_percent=42,  # 3/7 steps completed
        current_step='users_invited',
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(onboarding)
    logger.info(f"TenantOnboarding created for tenant '{tenant.tenant_id}'")

    return onboarding, True


def create_production_admin(session, tenant: Tenant, password: str) -> tuple[User | None, bool]:
    """
    Create the production admin user if it doesn't exist.

    SECURITY:
    - Password is hashed with bcrypt (automatic salt)
    - must_change_password=1 forces change on first login
    - No sensitive data in logs

    Returns:
        tuple: (user, created) - created/existing user and creation flag
    """
    email = PROD_ADMIN_CONFIG['email']

    # Idempotent check by email AND tenant_id
    existing_user = session.query(User).filter(
        User.email == email,
        User.tenant_id == tenant.tenant_id
    ).first()

    if existing_user:
        logger.info(
            f"User '{email}' already exists for tenant '{tenant.tenant_id}' "
            f"(id={existing_user.id}, role={existing_user.role.value}, "
            f"is_active={existing_user.is_active})"
        )
        return existing_user, False

    # Secure password hash (bcrypt with automatic salt)
    password_hash = get_password_hash(password)

    # Create admin user
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        email=email,
        password_hash=password_hash,
        role=PROD_ADMIN_CONFIG['role'],
        is_active=PROD_ADMIN_CONFIG['is_active'],
        must_change_password=PROD_ADMIN_CONFIG['must_change_password'],
        password_changed_at=None,  # Never changed
        totp_enabled=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(user)

    # Log WITHOUT password or hash
    logger.info(
        f"Admin user created: email='{email}', tenant_id='{tenant.tenant_id}', "
        f"role={user.role.value}, must_change_password=True"
    )

    return user, True


# ============================================================================
# VERIFICATION
# ============================================================================

def verify_setup(session, tenant: Tenant, user: User) -> bool:
    """
    Verify that the setup was completed correctly.
    """
    from app.core.security import verify_password

    logger.info("=" * 60)
    logger.info("FINAL VERIFICATION")
    logger.info("=" * 60)

    all_passed = True

    # Check tenant exists and is production
    if tenant.environment != TenantEnvironment.PRODUCTION:
        logger.error(f"FAILED: Incorrect environment (expected: production, found: {tenant.environment})")
        all_passed = False
    else:
        logger.info(f"[OK] Tenant environment: {tenant.environment.value}")

    # Check admin exists
    if not user:
        logger.error("FAILED: Admin user not found")
        all_passed = False
    else:
        logger.info(f"[OK] Admin user created: {user.email}")

    # Check password is hashed
    if user and user.password_hash:
        if not user.password_hash.startswith('$2b$'):
            logger.error("FAILED: Password not properly hashed (not bcrypt)")
            all_passed = False
        else:
            logger.info("[OK] Password properly hashed with bcrypt")

    # Check must_change_password flag
    if user and user.must_change_password != 1:
        logger.error("FAILED: must_change_password is not enabled")
        all_passed = False
    else:
        logger.info("[OK] must_change_password is enabled")

    # Check bootstrap lock
    settings = session.query(SystemSettings).first()
    if not settings or not settings.bootstrap_locked:
        logger.error("FAILED: Bootstrap not locked")
        all_passed = False
    else:
        logger.info("[OK] Bootstrap is locked")

    if all_passed:
        logger.info("=" * 60)
        logger.info("[OK] ALL VERIFICATIONS PASSED")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("[FAILED] SOME VERIFICATIONS FAILED")
        logger.error("=" * 60)

    return all_passed


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """
    Main entry point for production bootstrap.
    """
    logger.info("=" * 60)
    logger.info("AZALSCORE - Bootstrap PRODUCTION")
    logger.info("=" * 60)
    logger.info("")
    logger.info("This script will create:")
    logger.info("  1. The main production tenant (MASITH)")
    logger.info("  2. The initial admin user (DIRIGEANT role)")
    logger.info("  3. Lock bootstrap to prevent re-execution")
    logger.info("")
    logger.info("=" * 60)

    # Database connection
    app_settings = get_settings()
    engine = create_engine(app_settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check bootstrap lock
        settings, is_locked = check_bootstrap_lock(session)

        if is_locked:
            logger.error("[FATAL] Bootstrap already locked - cannot re-run")
            logger.error("This script can only be executed ONCE.")
            sys.exit(1)

        # Prompt for admin password
        logger.info("")
        temp_password = getpass.getpass("Temporary admin password: ").strip()

        if not temp_password:
            logger.error("[FATAL] Password cannot be empty")
            sys.exit(1)

        if len(temp_password) < 8:
            logger.error("[FATAL] Password must be at least 8 characters")
            sys.exit(1)

        # Confirm password
        confirm_password = getpass.getpass("Confirm password: ").strip()

        if temp_password != confirm_password:
            logger.error("[FATAL] Passwords do not match")
            sys.exit(1)

        logger.info("")

        # 1. Create production tenant
        tenant, tenant_created = create_production_tenant(session)
        if not tenant:
            raise RuntimeError("Failed to create/retrieve tenant")

        # 2. Create tenant settings
        create_tenant_settings(session, tenant)

        # 3. Create onboarding tracking
        create_tenant_onboarding(session, tenant)

        # 4. Create admin user
        user, user_created = create_production_admin(session, tenant, temp_password)
        if not user:
            raise RuntimeError("Failed to create/retrieve admin user")

        # 5. Lock bootstrap
        lock_bootstrap(session, settings)

        # 6. Commit transaction
        session.commit()
        logger.info("[OK] Transaction committed successfully")

        # 7. Final verification
        if not verify_setup(session, tenant, user):
            logger.warning("Some verifications failed, but data was created")
            return 1

        # Final summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tenant ID     : {tenant.tenant_id}")
        logger.info(f"Tenant Name   : {tenant.name}")
        logger.info(f"Environment   : {tenant.environment.value}")
        logger.info(f"Status        : {tenant.status.value}")
        logger.info(f"Admin Email   : {user.email}")
        logger.info(f"Admin Role    : {user.role.value}")
        logger.info(f"Password Reset: Required on first login")
        logger.info("=" * 60)
        logger.info("")
        logger.info("[LOCK] Bootstrap permanently locked")
        logger.info("[OK] AZALS ready - demo cockpit disabled")
        logger.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        session.rollback()
        logger.warning("\nBootstrap cancelled by user")
        return 130

    except Exception as e:
        session.rollback()
        logger.error(f"ERROR: {e}")
        logger.exception("Error details:")
        return 1

    finally:
        session.close()


if __name__ == '__main__':
    sys.exit(main())
