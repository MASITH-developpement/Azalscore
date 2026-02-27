"""
AZALSCORE - Configuration des Tests
=====================================
Fixtures partagées pour tous les tests.

Usage:
    pytest tests/ -v
    pytest tests/ -v --cov=app --cov-report=html
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# TEST ENGINE - Créé au niveau module pour être partagé
# ============================================================================

# Engine SQLite en mémoire partagé par tous les tests
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Session factory pour les tests
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def engine():
    """Retourner l'engine SQLite en mémoire pour les tests."""
    return TEST_ENGINE


@pytest.fixture(scope="session")
def tables(engine):
    """Créer toutes les tables pour les tests."""
    from app.db import Base
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables) -> Generator[Session, None, None]:
    """Session de base de données pour chaque test."""
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)

    # Nested transaction pour pouvoir rollback après chaque test
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def db(db_session) -> Session:
    """Alias plus court pour db_session."""
    return db_session


# ============================================================================
# APPLICATION FIXTURES
# ============================================================================

@pytest.fixture
def app(tables):
    """Créer une instance de l'application pour les tests."""
    from fastapi import FastAPI
    from app.core.database import get_db

    # Import de l'app après création des tables
    from app.main import app as main_app

    return main_app


@pytest.fixture
def client(app, db_session):
    """Client de test avec injection de la session DB."""
    from fastapi.testclient import TestClient
    from app.core.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# TENANT FIXTURES
# ============================================================================

@pytest.fixture
def sample_tenant_data() -> Dict[str, Any]:
    """Données de tenant valides pour les tests."""
    return {
        "company_name": "Test Company SAS",
        "company_email": "contact@testcompany.fr",
        "country": "FR",
        "siret": "73282932000074",  # Valid SIRET (passes Luhn algorithm)
        "admin_email": "admin@testcompany.fr",
        "admin_password": "SecurePass123!",
        "admin_first_name": "Jean",
        "admin_last_name": "Dupont",
        "admin_phone": "+33612345678",
        "plan": "PROFESSIONAL",
    }


@pytest.fixture
def sample_tenant(db_session) -> "Tenant":
    """Créer un tenant de test dans la base."""
    from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan

    tenant = Tenant(
        tenant_id="test-company",
        name="Test Company",
        legal_name="Test Company SAS",
        email="contact@testcompany.fr",
        country="FR",
        status=TenantStatus.ACTIVE,
        plan=SubscriptionPlan.PROFESSIONAL,
        max_users=25,
        max_storage_gb=50,
        trial_ends_at=datetime.utcnow() + timedelta(days=14),
        activated_at=datetime.utcnow(),
    )
    db_session.add(tenant)
    db_session.flush()
    return tenant


@pytest.fixture
def trial_tenant(db_session) -> "Tenant":
    """Créer un tenant en période d'essai."""
    from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan

    tenant = Tenant(
        tenant_id="trial-company",
        name="Trial Company",
        email="contact@trialcompany.fr",
        country="FR",
        status=TenantStatus.TRIAL,
        plan=SubscriptionPlan.PROFESSIONAL,
        max_users=25,
        trial_ends_at=datetime.utcnow() + timedelta(days=7),
        activated_at=datetime.utcnow(),
    )
    db_session.add(tenant)
    db_session.flush()
    return tenant


@pytest.fixture
def expired_trial_tenant(db_session) -> "Tenant":
    """Créer un tenant avec essai expiré."""
    from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan

    tenant = Tenant(
        tenant_id="expired-trial",
        name="Expired Trial Company",
        email="contact@expiredtrial.fr",
        country="FR",
        status=TenantStatus.TRIAL,
        plan=SubscriptionPlan.STARTER,
        max_users=5,
        trial_ends_at=datetime.utcnow() - timedelta(days=1),  # Expiré hier
        activated_at=datetime.utcnow() - timedelta(days=15),
    )
    db_session.add(tenant)
    db_session.flush()
    return tenant


@pytest.fixture
def suspended_tenant(db_session) -> "Tenant":
    """Créer un tenant suspendu (impayé)."""
    from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan

    tenant = Tenant(
        tenant_id="suspended-company",
        name="Suspended Company",
        email="contact@suspended.fr",
        country="FR",
        status=TenantStatus.SUSPENDED,
        plan=SubscriptionPlan.PROFESSIONAL,
        max_users=25,
        suspended_at=datetime.utcnow() - timedelta(days=3),
    )
    db_session.add(tenant)
    db_session.flush()
    return tenant


@pytest.fixture
def cancelled_tenant(db_session) -> "Tenant":
    """Créer un tenant annulé."""
    from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan

    tenant = Tenant(
        tenant_id="cancelled-company",
        name="Cancelled Company",
        email="contact@cancelled.fr",
        country="FR",
        status=TenantStatus.CANCELLED,
        plan=SubscriptionPlan.STARTER,
        cancelled_at=datetime.utcnow() - timedelta(days=10),
    )
    db_session.add(tenant)
    db_session.flush()
    return tenant


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def sample_user(db_session, sample_tenant) -> "User":
    """Créer un utilisateur de test."""
    from app.core.models import User
    from app.core.security import get_password_hash as hash_password

    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.tenant_id,
        email="user@testcompany.fr",
        password_hash=hash_password("TestPass123!"),
        role="EMPLOYE",
        is_active=1,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin_user(db_session, sample_tenant) -> "User":
    """Créer un utilisateur admin de test."""
    from app.core.models import User
    from app.core.security import get_password_hash as hash_password

    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.tenant_id,
        email="admin@testcompany.fr",
        password_hash=hash_password("AdminPass123!"),
        role="ADMIN",
        is_active=1,
    )
    db_session.add(user)
    db_session.flush()
    return user


# ============================================================================
# AUTH FIXTURES
# ============================================================================

@pytest.fixture
def auth_headers(sample_user, sample_tenant) -> Dict[str, str]:
    """Headers d'authentification valides."""
    from app.core.security import create_access_token

    token = create_access_token(
        data={
            "sub": str(sample_user.id),
            "tenant_id": sample_tenant.tenant_id,
            "role": sample_user.role,
        }
    )

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": sample_tenant.tenant_id,
    }


@pytest.fixture
def admin_auth_headers(admin_user, sample_tenant) -> Dict[str, str]:
    """Headers d'authentification admin."""
    from app.core.security import create_access_token

    token = create_access_token(
        data={
            "sub": str(admin_user.id),
            "tenant_id": sample_tenant.tenant_id,
            "role": "ADMIN",
        }
    )

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": sample_tenant.tenant_id,
    }


# ============================================================================
# STRIPE FIXTURES
# ============================================================================

@pytest.fixture
def stripe_checkout_event() -> Dict[str, Any]:
    """Événement Stripe checkout.session.completed."""
    return {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "customer": "cus_test_123",
                "subscription": "sub_test_123",
                "metadata": {
                    "tenant_id": "test-company",
                    "plan": "PROFESSIONAL",
                },
                "amount_total": 14900,
                "currency": "eur",
            }
        }
    }


@pytest.fixture
def stripe_payment_failed_event() -> Dict[str, Any]:
    """Événement Stripe invoice.payment_failed."""
    return {
        "id": "evt_test_456",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_test_456",
                "customer": "cus_test_123",
                "subscription": "sub_test_123",
                "attempt_count": 3,
                "amount_due": 14900,
            }
        }
    }


@pytest.fixture
def stripe_subscription_deleted_event() -> Dict[str, Any]:
    """Événement Stripe customer.subscription.deleted."""
    return {
        "id": "evt_test_789",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test_123",
                "customer": "cus_test_123",
                "metadata": {
                    "tenant_id": "test-company",
                },
            }
        }
    }


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def mock_rate_limiter():
    """Mock du rate limiter pour permettre les tests sans limitation."""
    mock_limiter = MagicMock()
    mock_limiter.check_rate.return_value = (True, 0)  # Always allow
    mock_limiter.record_attempt.return_value = None

    with patch("app.core.rate_limiter.rate_limiter", mock_limiter):
        yield mock_limiter


@pytest.fixture
def mock_stripe():
    """Mock du module Stripe."""
    with patch("stripe.Webhook.construct_event") as mock_construct:
        with patch("stripe.checkout.Session.create") as mock_session:
            with patch("stripe.Customer.create") as mock_customer:
                mock_construct.return_value = MagicMock()
                mock_session.return_value = MagicMock(url="https://checkout.stripe.com/test")
                mock_customer.return_value = MagicMock(id="cus_test_123")

                yield {
                    "construct_event": mock_construct,
                    "create_session": mock_session,
                    "create_customer": mock_customer,
                }


@pytest.fixture
def mock_email_service():
    """Mock du service d'email."""
    with patch("app.services.email_service.get_email_service") as mock:
        service = MagicMock()
        service.send_welcome.return_value = True
        service.send_trial_reminder.return_value = True
        service.send_payment_success.return_value = True
        service.send_payment_failed.return_value = True
        mock.return_value = service
        yield service


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_test_tenant(db: Session, tenant_id: str, status: str = "ACTIVE", **kwargs):
    """Helper pour créer un tenant de test."""
    from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan

    defaults = {
        "name": f"Test {tenant_id}",
        "email": f"contact@{tenant_id}.fr",
        "country": "FR",
        "plan": SubscriptionPlan.PROFESSIONAL,
        "max_users": 25,
        "max_storage_gb": 50,
    }
    defaults.update(kwargs)

    tenant = Tenant(
        tenant_id=tenant_id,
        status=TenantStatus[status],
        **defaults
    )
    db.add(tenant)
    db.flush()
    return tenant


def create_test_user(db: Session, tenant_id: str, email: str, role: str = "EMPLOYE"):
    """Helper pour créer un utilisateur de test."""
    from app.core.models import User
    from app.core.security import get_password_hash as hash_password

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=email,
        password_hash=hash_password("TestPass123!"),
        role=role,
        is_active=1,
    )
    db.add(user)
    db.flush()
    return user
