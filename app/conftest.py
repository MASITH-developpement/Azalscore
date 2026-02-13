"""
Configuration pytest globale pour tous les modules CORE SaaS v2.
================================================================

Fournit les fixtures de base pour les tests avec:
- Base SQLite in-memory pour tests d'integration
- Mocking du middleware d'authentification
- SaaSContext mock pour les endpoints

ARCHITECTURE DE TEST:
=====================

Pour les tests d'integration (endpoints):
- Utilise SQLite in-memory comme vraie DB
- Mock SaaSCore.authenticate pour bypasser JWT
- Injecte SaaSContext valide

Pour les tests unitaires (services):
- MockDB simple peut etre utilise
"""

import os
import pytest
from datetime import datetime
from typing import Any, Generator
from unittest.mock import patch
from uuid import UUID

# Configure test environment BEFORE any imports that use encryption
# Use a valid Fernet key (base64-encoded 32 bytes)
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ENCRYPTION_KEY", "J37-b0UuiaXxpvZmlu95ZmK0cNKYQK57SqplMtAmdn4=")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.saas_context import Result, SaaSContext, TenantScope, UserRole


# ============================================================================
# SQLITE TYPE COMPATIBILITY
# ============================================================================
# SQLite ne supporte pas nativement certains types PostgreSQL.
# On enregistre des type compilers pour les convertir.

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM


@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(element, compiler, **kw):
    """Compile PostgreSQL UUID as CHAR(36) for SQLite."""
    return "CHAR(36)"


@compiles(PG_JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    """Compile PostgreSQL JSONB as TEXT for SQLite."""
    return "TEXT"


@compiles(PG_ENUM, "sqlite")
def compile_enum_sqlite(element, compiler, **kw):
    """Compile PostgreSQL ENUM as VARCHAR for SQLite."""
    return "VARCHAR(50)"


# ============================================================================
# TEST DATA - Constantes utilisees dans tous les tests
# ============================================================================

TEST_TENANT_ID = "tenant-test-001"
TEST_USER_ID = "12345678-1234-1234-1234-123456789001"
TEST_USER_UUID = UUID(TEST_USER_ID)


# ============================================================================
# MOCK USER CLASS
# ============================================================================

class MockUser:
    """
    Mock de l'objet User pour les tests ou la DB n'est pas utilisee.
    """

    def __init__(
        self,
        id: UUID = TEST_USER_UUID,
        tenant_id: str = TEST_TENANT_ID,
        email: str = "test@azalscore.com",
        role: str = "ADMIN",
        is_active: bool = True,
        **kwargs
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.email = email
        self.is_active = is_active
        self._role = role

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def role(self):
        class RoleValue:
            def __init__(self, value):
                self.value = value
            def __str__(self):
                return self.value
            def __eq__(self, other):
                if hasattr(other, 'value'):
                    return self.value == other.value
                return self.value == str(other)
        return RoleValue(self._role)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


# ============================================================================
# FIXTURES DE BASE
# ============================================================================

@pytest.fixture
def tenant_id():
    """ID de tenant pour les tests."""
    return TEST_TENANT_ID


@pytest.fixture
def user_id():
    """ID d'utilisateur pour les tests (string UUID)."""
    return TEST_USER_ID


@pytest.fixture
def user_uuid():
    """ID d'utilisateur pour les tests (UUID object)."""
    return TEST_USER_UUID


@pytest.fixture
def mock_user():
    """Utilisateur mock pour les tests."""
    return MockUser()


# ============================================================================
# DATABASE TEST ENGINE - SQLite In-Memory
# ============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """
    Cree un engine SQLite in-memory pour les tests.

    Note: scope="session" pour reutiliser entre les tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Activer les foreign keys pour SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Creer les tables
    from app.db import Base
    from app.db.model_loader import load_all_models

    try:
        load_all_models()
    except Exception:
        pass  # Deja charge

    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine) -> Generator[Session, None, None]:
    """
    Session DB pour un test individuel.

    Utilise une transaction qui est rollback a la fin du test
    pour isolation entre tests.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# FIXTURE PRINCIPALE - Mock global de l'authentification
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def mock_auth_global(tenant_id, user_id):
    """
    Mock global de l'authentification CORE SaaS.

    Cette fixture est appliquee AUTOMATIQUEMENT a tous les tests.
    Elle mock:
    1. SaaSCore.authenticate() - retourne un SaaSContext valide
    2. get_saas_context dependency - retourne un SaaSContext
    3. get_db dependency - retourne session de test ou mock
    """
    # Creer le SaaSContext mock
    mock_context = SaaSContext(
        tenant_id=tenant_id,
        user_id=UUID(user_id),
        role=UserRole.ADMIN,
        permissions={"*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-correlation-id",
        timestamp=datetime.utcnow()
    )

    # Creer le mock user pour le middleware
    mock_user_obj = MockUser(
        id=UUID(user_id),
        tenant_id=tenant_id,
        role="ADMIN"
    )

    # Mock SaaSCore.authenticate pour retourner succes
    def mock_authenticate(self, token, tenant_id, ip_address="", user_agent="", correlation_id=""):
        return Result.ok(mock_context)

    # Mock get_saas_context dependency
    def mock_get_context():
        return mock_context

    # Creer un mock DB simple pour le middleware
    class MockDBForMiddleware:
        """Mock DB simple juste pour le middleware auth."""
        def query(self, model):
            class Q:
                def filter(self, *args, **kwargs):
                    return self
                def first(self):
                    return mock_user_obj
            return Q()
        def close(self):
            pass

    def mock_session_local():
        return MockDBForMiddleware()

    # Appliquer les patches
    patches = [
        patch('app.core.saas_core.SaaSCore.authenticate', mock_authenticate),
        patch('app.core.core_auth_middleware.SessionLocal', mock_session_local),
    ]

    for p in patches:
        p.start()

    # Override FastAPI dependencies
    from app.core.dependencies_v2 import get_saas_context
    from app.main import app

    app.dependency_overrides[get_saas_context] = mock_get_context

    yield {
        'context': mock_context,
        'user': mock_user_obj,
        'tenant_id': tenant_id,
        'user_id': user_id,
    }

    # Cleanup
    for p in patches:
        p.stop()

    app.dependency_overrides.pop(get_saas_context, None)


# ============================================================================
# FIXTURE DB SESSION (pour compatibilite)
# ============================================================================

@pytest.fixture
def db_session(test_db_session):
    """
    Alias pour test_db_session.

    Utilise la vraie DB SQLite pour les tests d'integration.
    """
    return test_db_session


# ============================================================================
# FIXTURE TEST CLIENT
# ============================================================================

@pytest.fixture
def test_client(mock_auth_global, test_db_session):
    """
    Client de test FastAPI avec DB reelle et auth mockee.
    """
    from app.core.database import get_db
    from app.main import app

    # Override get_db pour utiliser la session de test
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    tenant_id = mock_auth_global['tenant_id']
    user_id = mock_auth_global['user_id']

    class TestClientWithHeaders(TestClient):
        """TestClient qui ajoute automatiquement les headers requis."""

        def request(self, method: str, url: str, **kwargs):
            headers = kwargs.get("headers") or {}

            if "X-Tenant-ID" not in headers:
                headers["X-Tenant-ID"] = tenant_id
            if "Authorization" not in headers:
                headers["Authorization"] = f"Bearer mock-jwt-{user_id}"

            kwargs["headers"] = headers
            return super().request(method, url, **kwargs)

    client = TestClientWithHeaders(app)

    yield client

    # Cleanup
    app.dependency_overrides.pop(get_db, None)


# ============================================================================
# FIXTURES UTILITAIRES
# ============================================================================

@pytest.fixture
def sample_user(mock_auth_global):
    """Utilisateur exemple pour les tests."""
    return mock_auth_global['user']


@pytest.fixture
def saas_context(mock_auth_global):
    """SaaSContext mock pour les tests."""
    return mock_auth_global['context']
