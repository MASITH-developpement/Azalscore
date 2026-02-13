"""
Configuration pytest globale pour tous les modules CORE SaaS v2.
Fournit les fixtures de base pour les tests.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.core.saas_context import SaaSContext, UserRole


@pytest.fixture
def tenant_id():
    """ID de tenant pour les tests."""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """ID d'utilisateur pour les tests (UUID)."""
    return "12345678-1234-1234-1234-123456789001"


@pytest.fixture(scope="function", autouse=True)
def mock_saas_context_global(tenant_id, user_id):
    """
    Mock global de SaaSContext pour tous les tests.
    Utilise dependency_overrides de FastAPI.
    """
    from uuid import UUID
    from app.core.saas_context import TenantScope

    def mock_get_context():
        return SaaSContext(
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

    from app.core.dependencies_v2 import get_saas_context
    from app.main import app

    # Override dependency
    app.dependency_overrides[get_saas_context] = mock_get_context

    yield mock_get_context

    # Cleanup
    app.dependency_overrides.pop(get_saas_context, None)


@pytest.fixture(scope="function", autouse=True)
def mock_db_global():
    """
    Mock global de la session database SQLAlchemy.

    Simule toutes les méthodes courantes de Session pour permettre
    aux tests de s'exécuter sans connexion réelle à la base de données.
    """
    class MockQuery:
        """Mock pour les résultats de query()."""

        def __init__(self):
            self._result = None

        def filter(self, *args, **kwargs):
            return self

        def filter_by(self, **kwargs):
            return self

        def options(self, *args):
            return self

        def join(self, *args, **kwargs):
            return self

        def outerjoin(self, *args, **kwargs):
            return self

        def order_by(self, *args):
            return self

        def group_by(self, *args):
            return self

        def having(self, *args):
            return self

        def distinct(self, *args):
            return self

        def subquery(self):
            return self

        def with_entities(self, *args):
            return self

        def first(self):
            return self._result

        def one(self):
            if self._result is None:
                raise Exception("No row found")
            return self._result

        def one_or_none(self):
            return self._result

        def all(self):
            return [] if self._result is None else [self._result]

        def count(self):
            return 0 if self._result is None else 1

        def scalar(self):
            return None

        def exists(self):
            return self

        def offset(self, n):
            return self

        def limit(self, n):
            return self

        def slice(self, start, stop):
            return self

        def __iter__(self):
            return iter([])

    class MockDB:
        """
        Mock complet de SQLAlchemy Session.

        Implémente toutes les méthodes nécessaires pour les tests unitaires.
        """

        def __init__(self):
            self._query = MockQuery()
            self._added = []
            self._deleted = []

        def query(self, *args, **kwargs):
            return self._query

        def execute(self, *args, **kwargs):
            class MockResult:
                def fetchall(self):
                    return []
                def fetchone(self):
                    return None
                def scalar(self):
                    return None
                def scalars(self):
                    return self
                def all(self):
                    return []
                def first(self):
                    return None
            return MockResult()

        def add(self, obj):
            self._added.append(obj)

        def add_all(self, objs):
            self._added.extend(objs)

        def delete(self, obj):
            self._deleted.append(obj)

        def merge(self, obj):
            return obj

        def flush(self):
            """Flush pending changes (no-op in mock)."""
            pass

        def commit(self):
            """Commit transaction (no-op in mock)."""
            pass

        def rollback(self):
            """Rollback transaction (no-op in mock)."""
            pass

        def refresh(self, obj, *args, **kwargs):
            """Refresh object from database (no-op in mock)."""
            pass

        def expire(self, obj, *args):
            """Expire object attributes (no-op in mock)."""
            pass

        def expire_all(self):
            """Expire all objects (no-op in mock)."""
            pass

        def expunge(self, obj):
            """Remove object from session (no-op in mock)."""
            pass

        def expunge_all(self):
            """Remove all objects from session (no-op in mock)."""
            pass

        def close(self):
            """Close session (no-op in mock)."""
            pass

        def begin(self):
            """Begin transaction (no-op in mock)."""
            return self

        def begin_nested(self):
            """Begin nested transaction (no-op in mock)."""
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get_bind(self, *args, **kwargs):
            return None

        def is_active(self):
            return True

        @property
        def info(self):
            return {}

        @property
        def dirty(self):
            return set()

        @property
        def new(self):
            return set(self._added)

        @property
        def deleted(self):
            return set(self._deleted)

    mock_session = MockDB()

    from app.core.database import get_db
    from app.main import app

    def mock_get_db():
        try:
            yield mock_session
        finally:
            pass

    app.dependency_overrides[get_db] = mock_get_db

    yield mock_session

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def test_client(mock_db_global, mock_saas_context_global, tenant_id, user_id):
    """
    Client de test FastAPI avec toutes les dépendances mockées et headers configurés.
    À utiliser dans les tests au lieu de créer un TestClient au niveau module.
    """
    from app.main import app

    class TestClientWithHeaders(TestClient):
        """TestClient qui ajoute automatiquement les headers requis."""

        def request(self, method: str, url: str, **kwargs):
            # Ajouter les headers requis si pas déjà présents
            headers = kwargs.get("headers") or {}

            if "X-Tenant-ID" not in headers:
                headers["X-Tenant-ID"] = tenant_id
            if "Authorization" not in headers:
                headers["Authorization"] = f"Bearer mock-jwt-{user_id}"

            kwargs["headers"] = headers
            return super().request(method, url, **kwargs)

    return TestClientWithHeaders(app)
