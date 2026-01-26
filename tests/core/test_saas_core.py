"""
Tests unitaires pour le CORE SaaS
==================================

Teste:
- SaaSContext creation et propriétés
- SaaSCore.authenticate()
- SaaSCore.authorize()
- SaaSCore.is_module_active()
- SaaSCore.execute()
- Result pattern
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()
from app.core.models import Base, User, UserRole
from app.core.saas_context import Result, SaaSContext, TenantScope
from app.core.saas_core import ALGORITHM, SaaSCore
from app.modules.tenants.models import (
    ModuleStatus,
    SubscriptionPlan,
    Tenant,
    TenantModule,
    TenantStatus,
)


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
def tenant(db_session):
    """Create test tenant."""
    tenant = Tenant(
        tenant_id="TEST_TENANT",
        name="Test Company",
        email="test@example.com",
        status=TenantStatus.ACTIVE,
        plan=SubscriptionPlan.PROFESSIONAL,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def user_dirigeant(db_session, tenant):
    """Create test user with DIRIGEANT role."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        email="dirigeant@test.com",
        password_hash="hashed_password",
        role=UserRole.DIRIGEANT,
        is_active=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_employe(db_session, tenant):
    """Create test user with EMPLOYE role."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.tenant_id,
        email="employe@test.com",
        password_hash="hashed_password",
        role=UserRole.EMPLOYE,
        is_active=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_superadmin(db_session):
    """Create test user with SUPERADMIN role."""
    user = User(
        id=uuid.uuid4(),
        tenant_id="SYSTEM",
        email="superadmin@azals.com",
        password_hash="hashed_password",
        role=UserRole.SUPERADMIN,
        is_active=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def active_module(db_session, tenant):
    """Create active module for tenant."""
    module = TenantModule(
        tenant_id=tenant.tenant_id,
        module_code="commercial",
        module_name="Module Commercial",
        module_version="1.0.0",
        status=ModuleStatus.ACTIVE,
    )
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)
    return module


@pytest.fixture
def saas_core(db_session):
    """Create SaaSCore instance."""
    return SaaSCore(db_session)


def create_token(user_id: uuid.UUID, expires_delta: int = 30) -> str:
    """Helper to create JWT token."""
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


# ============================================================================
# TESTS: SaaSContext
# ============================================================================

def test_saas_context_creation():
    """Test SaaSContext creation."""
    context = SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"commercial.*", "invoicing.invoice.read"},
        scope=TenantScope.TENANT,
    )

    assert context.tenant_id == "TEST_TENANT"
    assert context.role == UserRole.DIRIGEANT
    assert len(context.permissions) == 2


def test_saas_context_immutable():
    """Test SaaSContext is immutable (frozen dataclass)."""
    context = SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
    )

    with pytest.raises(AttributeError):
        context.tenant_id = "MODIFIED"


def test_saas_context_is_creator():
    """Test is_creator property."""
    context_superadmin = SaaSContext(
        tenant_id="SYSTEM",
        user_id=uuid.uuid4(),
        role=UserRole.SUPERADMIN,
    )

    context_dirigeant = SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
    )

    assert context_superadmin.is_creator is True
    assert context_dirigeant.is_creator is False


def test_saas_context_has_permission():
    """Test has_permission method."""
    context = SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"commercial.*", "invoicing.invoice.read"},
    )

    # Permission exacte
    assert context.has_permission("invoicing.invoice.read") is True

    # Wildcard module.resource.*
    assert context.has_permission("commercial.customer.create") is True
    assert context.has_permission("commercial.quote.approve") is True

    # Permission refusée
    assert context.has_permission("iam.user.delete") is False


def test_saas_context_superadmin_has_all_permissions():
    """Test SUPERADMIN has all permissions via wildcard."""
    context = SaaSContext(
        tenant_id="SYSTEM",
        user_id=uuid.uuid4(),
        role=UserRole.SUPERADMIN,
        permissions={"*"},
    )

    # Toute permission doit être accordée
    assert context.has_permission("commercial.customer.delete") is True
    assert context.has_permission("iam.user.delete") is True
    assert context.has_permission("anything.any.any") is True


# ============================================================================
# TESTS: Result Pattern
# ============================================================================

def test_result_ok():
    """Test Result.ok()."""
    result = Result.ok(data={"key": "value"})

    assert result.success is True
    assert result.data == {"key": "value"}
    assert result.error is None


def test_result_fail():
    """Test Result.fail()."""
    result = Result.fail(error="Something went wrong", error_code="ERR_TEST")

    assert result.success is False
    assert result.error == "Something went wrong"
    assert result.error_code == "ERR_TEST"
    assert result.data is None


def test_result_unwrap_success():
    """Test Result.unwrap() on success."""
    result = Result.ok(data=42)
    assert result.unwrap() == 42


def test_result_unwrap_failure():
    """Test Result.unwrap() on failure raises exception."""
    result = Result.fail(error="Failed")

    with pytest.raises(ValueError, match="Result failed: Failed"):
        result.unwrap()


def test_result_unwrap_or():
    """Test Result.unwrap_or()."""
    success = Result.ok(data=42)
    failure = Result.fail(error="Failed")

    assert success.unwrap_or(default=0) == 42
    assert failure.unwrap_or(default=0) == 0


# ============================================================================
# TESTS: SaaSCore.authenticate()
# ============================================================================

def test_authenticate_success(saas_core, tenant, user_dirigeant):
    """Test successful authentication."""
    token = create_token(user_dirigeant.id)

    result = saas_core.authenticate(
        token=token,
        tenant_id=tenant.tenant_id,
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        correlation_id="test-123",
    )

    assert result.success is True
    assert isinstance(result.data, SaaSContext)

    context = result.data
    assert context.tenant_id == tenant.tenant_id
    assert context.user_id == user_dirigeant.id
    assert context.role == UserRole.DIRIGEANT
    assert context.ip_address == "127.0.0.1"
    assert context.user_agent == "TestAgent/1.0"
    assert context.correlation_id == "test-123"


def test_authenticate_invalid_token(saas_core, tenant):
    """Test authentication with invalid token."""
    result = saas_core.authenticate(
        token="invalid_token",
        tenant_id=tenant.tenant_id,
    )

    assert result.success is False
    assert result.error_code == "AUTH_INVALID_TOKEN"


def test_authenticate_user_not_found(saas_core, tenant):
    """Test authentication with non-existent user."""
    fake_user_id = uuid.uuid4()
    token = create_token(fake_user_id)

    result = saas_core.authenticate(
        token=token,
        tenant_id=tenant.tenant_id,
    )

    assert result.success is False
    assert result.error_code == "AUTH_USER_NOT_FOUND"


def test_authenticate_user_inactive(saas_core, tenant, user_dirigeant):
    """Test authentication with inactive user."""
    user_dirigeant.is_active = 0
    saas_core.db.commit()

    token = create_token(user_dirigeant.id)

    result = saas_core.authenticate(
        token=token,
        tenant_id=tenant.tenant_id,
    )

    assert result.success is False
    assert result.error_code == "AUTH_USER_NOT_FOUND"


def test_authenticate_tenant_not_active(saas_core, tenant, user_dirigeant):
    """Test authentication with suspended tenant."""
    tenant.status = TenantStatus.SUSPENDED
    saas_core.db.commit()

    token = create_token(user_dirigeant.id)

    result = saas_core.authenticate(
        token=token,
        tenant_id=tenant.tenant_id,
    )

    assert result.success is False
    assert result.error_code == "AUTH_TENANT_NOT_ACTIVE"


def test_authenticate_expired_token(saas_core, tenant, user_dirigeant):
    """Test authentication with expired token."""
    # Create token expired 1 minute ago
    token = create_token(user_dirigeant.id, expires_delta=-1)

    result = saas_core.authenticate(
        token=token,
        tenant_id=tenant.tenant_id,
    )

    assert result.success is False
    assert result.error_code == "AUTH_INVALID_TOKEN"


# ============================================================================
# TESTS: SaaSCore.authorize()
# ============================================================================

def test_authorize_superadmin_has_all_permissions(saas_core):
    """Test SUPERADMIN has all permissions."""
    context = SaaSContext(
        tenant_id="SYSTEM",
        user_id=uuid.uuid4(),
        role=UserRole.SUPERADMIN,
        permissions={"*"},
        scope=TenantScope.GLOBAL,
    )

    assert saas_core.authorize(context, "commercial.customer.delete") is True
    assert saas_core.authorize(context, "iam.user.delete") is True
    assert saas_core.authorize(context, "anything.resource.action") is True


def test_authorize_dirigeant(saas_core):
    """Test DIRIGEANT permissions."""
    context = SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"commercial.*", "invoicing.*"},
    )

    assert saas_core.authorize(context, "commercial.customer.create") is True
    assert saas_core.authorize(context, "invoicing.invoice.approve") is True
    assert saas_core.authorize(context, "iam.user.delete") is False


def test_authorize_employe(saas_core):
    """Test EMPLOYE limited permissions."""
    context = SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.EMPLOYE,
        permissions={"commercial.customer.read", "inventory.product.read"},
    )

    assert saas_core.authorize(context, "commercial.customer.read") is True
    assert saas_core.authorize(context, "commercial.customer.create") is False
    assert saas_core.authorize(context, "commercial.customer.delete") is False


# ============================================================================
# TESTS: SaaSCore.is_module_active()
# ============================================================================

def test_is_module_active_true(saas_core, tenant, active_module):
    """Test module is active."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
    )

    assert saas_core.is_module_active(context, "commercial") is True


def test_is_module_active_false(saas_core, tenant):
    """Test module is not active."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
    )

    assert saas_core.is_module_active(context, "invoicing") is False


def test_is_module_active_superadmin_global_scope(saas_core, user_superadmin):
    """Test SUPERADMIN with global scope can access all modules."""
    context = SaaSContext(
        tenant_id="SYSTEM",
        user_id=user_superadmin.id,
        role=UserRole.SUPERADMIN,
        scope=TenantScope.GLOBAL,
    )

    # SUPERADMIN en scope global peut accéder à n'importe quel module
    assert saas_core.is_module_active(context, "commercial") is True
    assert saas_core.is_module_active(context, "nonexistent") is True


# ============================================================================
# TESTS: SaaSCore.activate_module()
# ============================================================================

def test_activate_module_success(saas_core, tenant):
    """Test module activation."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"iam.module.activate"},
    )

    result = saas_core.activate_module(
        context=context,
        module_code="invoicing",
        module_name="Module Facturation",
        module_version="1.0.0",
    )

    assert result.success is True
    assert isinstance(result.data, TenantModule)
    assert result.data.module_code == "invoicing"
    assert result.data.status == ModuleStatus.ACTIVE


def test_activate_module_permission_denied(saas_core, tenant):
    """Test module activation without permission."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.EMPLOYE,
        permissions=set(),  # No permissions
    )

    result = saas_core.activate_module(
        context=context,
        module_code="invoicing",
    )

    assert result.success is False
    assert result.error_code == "AUTH_PERMISSION_DENIED"


def test_activate_module_already_active(saas_core, tenant, active_module):
    """Test activating already active module."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"iam.module.activate"},
    )

    result = saas_core.activate_module(
        context=context,
        module_code="commercial",  # Already active
    )

    assert result.success is False
    assert result.error_code == "MODULE_ALREADY_ACTIVE"


# ============================================================================
# TESTS: SaaSCore.deactivate_module()
# ============================================================================

def test_deactivate_module_success(saas_core, tenant, active_module):
    """Test module deactivation."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"iam.module.deactivate"},
    )

    result = saas_core.deactivate_module(
        context=context,
        module_code="commercial",
    )

    assert result.success is True
    assert result.data["status"] == "DISABLED"

    # Verify module is now disabled
    assert saas_core.is_module_active(context, "commercial") is False


def test_deactivate_module_not_found(saas_core, tenant):
    """Test deactivating non-existent module."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"iam.module.deactivate"},
    )

    result = saas_core.deactivate_module(
        context=context,
        module_code="nonexistent",
    )

    assert result.success is False
    assert result.error_code == "MODULE_NOT_FOUND"


# ============================================================================
# TESTS: SaaSCore.execute() (mocked)
# ============================================================================

@pytest.mark.asyncio
async def test_execute_success(saas_core, tenant, active_module):
    """Test execute() with mocked executor."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"commercial.customer.create"},
    )

    # Mock executor with async execute method
    mock_executor = MagicMock()

    # Create an async mock for the execute method
    async def async_execute(*args, **kwargs):
        return Result.ok(data={"customer_id": "123"})

    mock_executor.execute = async_execute

    with patch.object(saas_core, '_load_module_executor', return_value=mock_executor):
        result = await saas_core.execute(
            action="commercial.customer.create",
            context=context,
            data={"name": "Test Customer"},
        )

    assert result.success is True
    assert result.data == {"customer_id": "123"}


@pytest.mark.asyncio
async def test_execute_invalid_action_format(saas_core):
    """Test execute() with invalid action format."""
    context = SaaSContext(
        tenant_id="TEST_TENANT",
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
    )

    result = await saas_core.execute(
        action="invalid_action",  # Missing dots
        context=context,
    )

    assert result.success is False
    assert result.error_code == "CORE_INVALID_ACTION_FORMAT"


@pytest.mark.asyncio
async def test_execute_module_not_active(saas_core, tenant):
    """Test execute() with inactive module."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"invoicing.invoice.create"},
    )

    result = await saas_core.execute(
        action="invoicing.invoice.create",  # Module not active
        context=context,
    )

    assert result.success is False
    assert result.error_code == "CORE_MODULE_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_execute_permission_denied(saas_core, tenant, active_module):
    """Test execute() without permission."""
    context = SaaSContext(
        tenant_id=tenant.tenant_id,
        user_id=uuid.uuid4(),
        role=UserRole.EMPLOYE,
        permissions={"commercial.customer.read"},  # Only read, not create
    )

    result = await saas_core.execute(
        action="commercial.customer.create",
        context=context,
    )

    assert result.success is False
    assert result.error_code == "AUTH_PERMISSION_DENIED"


# ============================================================================
# TESTS: Password Helpers
# ============================================================================

def test_hash_and_verify_password():
    """Test password hashing and verification."""
    password = "SecurePassword123!"

    hashed = SaaSCore.hash_password(password)

    assert hashed != password
    assert SaaSCore.verify_password(password, hashed) is True
    assert SaaSCore.verify_password("WrongPassword", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    user_id = uuid.uuid4()

    token = SaaSCore.create_access_token(user_id, expires_delta=30)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    assert payload["sub"] == str(user_id)
