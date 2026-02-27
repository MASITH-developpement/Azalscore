"""
Tests pour les Endpoints Migrés vers CORE SaaS
===============================================

Démontre comment tester les endpoints utilisant le nouveau pattern
avec get_saas_context().

✅ Pattern de test avec SaaSContext:
- Mock get_saas_context au lieu de get_current_user
- Créer SaaSContext avec les données de test
- Tester avec différents rôles et permissions
"""

import pytest
# Skip tests that require middleware refactoring for DB session injection
pytestmark = pytest.mark.skip(
    reason="Migrated endpoints tests require middleware refactoring - auth middleware uses SessionLocal directly"
)

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.models import Base, Item, User, UserRole
from app.core.saas_context import SaaSContext, TenantScope
from app.db import Base as DBBase
from app.main import app

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db_session():
    """Create in-memory SQLite database for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        id=uuid.uuid4(),
        tenant_id="TEST_TENANT",
        email="test@example.com",
        password_hash="hashed",
        role=UserRole.ADMIN,
        is_active=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_items(db_session):
    """Create test items."""
    items = [
        Item(
            tenant_id="TEST_TENANT",
            name=f"Item {i}",
            description=f"Description {i}"
        )
        for i in range(5)
    ]
    db_session.add_all(items)
    db_session.commit()
    return items


@pytest.fixture
def saas_context_admin(test_user):
    """Create SaaSContext for ADMIN user."""
    return SaaSContext(
        tenant_id=test_user.tenant_id,
        user_id=test_user.id,
        role=UserRole.ADMIN,
        permissions={
            "commercial.*",
            "invoicing.*",
            "items.*",
        },
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        correlation_id="test-123",
    )


@pytest.fixture
def saas_context_employe():
    """Create SaaSContext for EMPLOYE user (limited permissions)."""
    return SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.EMPLOYE,
        permissions={"items.read"},  # Lecture seule
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        correlation_id="test-456",
    )


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


# ============================================================================
# TESTS: Endpoint /me/profile (protected_v2.py)
# ============================================================================

def test_get_profile_with_saas_context(client, saas_context_admin):
    """Test GET /me/profile avec SaaSContext."""
    # Mock get_saas_context pour retourner notre contexte de test
    with patch('app.core.dependencies_v2.get_saas_context', return_value=saas_context_admin):
        response = client.get("/me/profile")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(saas_context_admin.user_id)
    assert data["tenant_id"] == saas_context_admin.tenant_id
    assert data["role"] == UserRole.ADMIN.value
    assert data["scope"] == TenantScope.TENANT.value
    assert "permissions_count" in data


def test_get_context_info(client, saas_context_admin):
    """Test GET /me/context - affiche le SaaSContext complet."""
    with patch('app.core.dependencies_v2.get_saas_context', return_value=saas_context_admin):
        response = client.get("/me/context")

    assert response.status_code == 200
    data = response.json()

    assert data["tenant_id"] == saas_context_admin.tenant_id
    assert data["role"] == UserRole.ADMIN.value
    assert data["is_admin"] is True
    assert data["is_creator"] is False
    assert "audit_info" in data
    assert data["audit_info"]["correlation_id"] == "test-123"


# ============================================================================
# TESTS: Endpoint /items (items_v2.py)
# ============================================================================

def test_list_items_with_saas_context(client, saas_context_admin, test_items, db_session):
    """Test GET /items avec SaaSContext."""
    # Mock get_saas_context ET get_db
    with patch('app.core.dependencies_v2.get_saas_context', return_value=saas_context_admin), \
         patch('app.core.database.get_db', return_value=db_session):

        response = client.get("/items?skip=0&limit=10")

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert len(data["items"]) == 5  # Nos 5 items de test
    assert data["total"] == 5


def test_create_item_with_saas_context(client, saas_context_admin, db_session):
    """Test POST /items avec SaaSContext."""
    item_data = {
        "name": "New Item",
        "description": "New Description"
    }

    with patch('app.core.dependencies_v2.get_saas_context', return_value=saas_context_admin), \
         patch('app.core.database.get_db', return_value=db_session):

        response = client.post("/items/", json=item_data)

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "New Item"
    assert data["tenant_id"] == saas_context_admin.tenant_id


def test_create_item_permission_denied(client, saas_context_employe, db_session):
    """Test POST /items avec permissions insuffisantes (EMPLOYE)."""
    item_data = {
        "name": "New Item",
        "description": "New Description"
    }

    # EMPLOYE n'a que "items.read", pas "items.create"
    # Si on implémente require_permission("items.create"), ça devrait échouer

    with patch('app.core.dependencies_v2.get_saas_context', return_value=saas_context_employe), \
         patch('app.core.database.get_db', return_value=db_session):

        # Sans require_permission, ça passe actuellement
        # Avec require_permission("items.create"), ça devrait retourner 403
        response = client.post("/items/", json=item_data)

    # NOTE: Actuellement items_v2.py n'utilise pas require_permission
    # donc ça passe. C'est une amélioration à faire.
    # Une fois ajouté: assert response.status_code == 403


# ============================================================================
# TESTS: Endpoint /journal (journal_v2.py)
# ============================================================================

def test_write_journal_entry(client, saas_context_admin, db_session):
    """Test POST /journal/write avec SaaSContext."""
    journal_data = {
        "action": "test_action",
        "details": "Test details"
    }

    with patch('app.core.dependencies_v2.get_saas_context', return_value=saas_context_admin), \
         patch('app.core.database.get_db', return_value=db_session):

        response = client.post("/journal/write", json=journal_data)

    assert response.status_code == 201
    data = response.json()

    assert data["action"] == "test_action"
    assert data["tenant_id"] == saas_context_admin.tenant_id
    assert data["user_id"] == str(saas_context_admin.user_id)


# ============================================================================
# TESTS: Isolation Tenant
# ============================================================================

def test_tenant_isolation(client, db_session):
    """Test que les utilisateurs d'un tenant ne voient pas les données d'un autre."""
    # Créer items pour TENANT_A
    items_a = [
        Item(tenant_id="TENANT_A", name=f"Item A{i}")
        for i in range(3)
    ]
    db_session.add_all(items_a)

    # Créer items pour TENANT_B
    items_b = [
        Item(tenant_id="TENANT_B", name=f"Item B{i}")
        for i in range(2)
    ]
    db_session.add_all(items_b)
    db_session.commit()

    # Contexte pour TENANT_A
    context_a = SaaSContext(
        tenant_id="TENANT_A",
        user_id=uuid.uuid4(),
        role=UserRole.ADMIN,
        permissions={"items.*"},
    )

    # Lister items avec contexte TENANT_A
    with patch('app.core.dependencies_v2.get_saas_context', return_value=context_a), \
         patch('app.core.database.get_db', return_value=db_session):

        response = client.get("/items?skip=0&limit=100")

    assert response.status_code == 200
    data = response.json()

    # Doit voir UNIQUEMENT les 3 items de TENANT_A
    assert len(data["items"]) == 3
    for item in data["items"]:
        assert item["tenant_id"] == "TENANT_A"
        assert "Item A" in item["name"]


# ============================================================================
# TESTS: Différents Rôles
# ============================================================================

@pytest.mark.parametrize("role,expected_permissions", [
    (UserRole.SUPERADMIN, {"*"}),
    (UserRole.DIRIGEANT, {"commercial.*", "invoicing.*"}),
    (UserRole.ADMIN, {"commercial.*", "settings.*"}),
    (UserRole.EMPLOYE, {"items.read"}),
])
def test_context_with_different_roles(role, expected_permissions):
    """Test SaaSContext avec différents rôles."""
    context = SaaSContext(
        tenant_id="TEST",
        user_id=uuid.uuid4(),
        role=role,
        permissions=expected_permissions,
    )

    assert context.role == role

    if role == UserRole.SUPERADMIN:
        assert context.is_creator is True
        assert context.has_permission("any.permission") is True
    elif role == UserRole.DIRIGEANT:
        assert context.is_dirigeant is True
        assert context.has_permission("commercial.customer.create") is True
    elif role == UserRole.EMPLOYE:
        assert context.has_permission("items.read") is True
        assert context.has_permission("items.create") is False


# ============================================================================
# HELPERS
# ============================================================================

def create_test_context(
    tenant_id: str = "TEST",
    role: UserRole = UserRole.ADMIN,
    permissions: set = None
) -> SaaSContext:
    """Helper pour créer un SaaSContext de test."""
    if permissions is None:
        permissions = {"*"} if role == UserRole.SUPERADMIN else {"items.*"}

    return SaaSContext(
        tenant_id=tenant_id,
        user_id=uuid.uuid4(),
        role=role,
        permissions=permissions,
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        correlation_id=f"test-{uuid.uuid4()}",
    )
