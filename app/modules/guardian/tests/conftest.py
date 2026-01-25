"""
Configuration pytest et fixtures communes pour les tests Guardian
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole
from fastapi import Depends

from app.modules.guardian.models import (
    ErrorDetection,
    CorrectionRegistry,
    CorrectionRule,
    CorrectionTest,
    GuardianAlert,
    GuardianConfig,
    ErrorSeverity,
    ErrorType,
    Environment,
    CorrectionStatus,
    TestResult,
)


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Configuration de test"""
    return {
        "database_url": "sqlite:///:memory:",
        "testing": True
    }


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch):
    """
    Mock get_saas_context pour tous les tests
    Par défaut, utilisateur ADMIN avec permissions guardian.*
    """
    def mock_get_context():
        return SaaSContext(
            tenant_id="tenant-test-001",
            user_id="user-test-001",
            role=UserRole.ADMIN,
            permissions=["guardian.*"],
            scope="full",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    # Remplacer la dépendance FastAPI
    from app.modules.guardian import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    return mock_get_context


@pytest.fixture(scope="function")
def clean_database(db_session):
    """Nettoyer la base après chaque test"""
    yield
    db_session.rollback()


@pytest.fixture
def tenant_id():
    """ID du tenant de test"""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """ID de l'utilisateur de test"""
    return "user-test-001"


# ============================================================================
# FIXTURES AUTH (pour tests RBAC)
# ============================================================================

@pytest.fixture
def admin_auth_headers():
    """Headers d'authentification pour utilisateur ADMIN/DIRIGEANT"""
    # Utilise le mock par défaut qui retourne ADMIN
    return {"Authorization": "Bearer admin-token-test"}


# ============================================================================
# FIXTURES DONNÉES GUARDIAN
# ============================================================================

@pytest.fixture
def sample_guardian_config(db_session, tenant_id):
    """Fixture pour configuration Guardian de test"""
    config = GuardianConfig(
        id=uuid4(),
        tenant_id=tenant_id,
        auto_correction_enabled=True,
        require_validation_for_critical=True,
        max_auto_retries=3,
        alert_threshold_error_rate=0.05,
        updated_at=datetime.utcnow()
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


@pytest.fixture
def sample_error(db_session, tenant_id):
    """Fixture pour une erreur détectée de test"""
    error = ErrorDetection(
        id=12345,
        tenant_id=tenant_id,
        error_type=ErrorType.DATABASE_ERROR,
        severity=ErrorSeverity.HIGH,
        module="finance",
        message="Connection timeout to database",
        environment=Environment.PRODUCTION,
        detected_at=datetime.utcnow(),
        is_processed=False,
        is_acknowledged=False
    )
    db_session.add(error)
    db_session.commit()
    db_session.refresh(error)
    return error


@pytest.fixture
def sample_frontend_error(db_session, tenant_id, user_id):
    """Fixture pour une erreur frontend de test"""
    error = ErrorDetection(
        id=12346,
        tenant_id=tenant_id,
        error_type=ErrorType.FRONTEND_ERROR,
        severity=ErrorSeverity.MEDIUM,
        module="dashboard",
        message="TypeError: Cannot read property 'map' of undefined",
        stack_trace="at Component.render (app.js:123)",
        environment=Environment.PRODUCTION,
        detected_at=datetime.utcnow(),
        user_id_pseudonym=f"pseudo-{user_id[:8]}",  # Pseudonymisé
        is_processed=False
    )
    db_session.add(error)
    db_session.commit()
    db_session.refresh(error)
    return error


@pytest.fixture
def sample_correction(db_session, tenant_id, sample_error):
    """Fixture pour une correction de test"""
    correction = CorrectionRegistry(
        id=uuid4(),
        tenant_id=tenant_id,
        error_id=sample_error.id,
        correction_type="AUTO_FIX",
        description="Automatic database reconnection",
        status=CorrectionStatus.SUCCESS,
        environment=Environment.PRODUCTION,
        executed_by=f"user:{uuid4()}",
        executed_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        requires_validation=False
    )
    db_session.add(correction)
    db_session.commit()
    db_session.refresh(correction)
    return correction


@pytest.fixture
def sample_correction_pending(db_session, tenant_id, sample_error):
    """Fixture pour une correction en attente de validation"""
    correction = CorrectionRegistry(
        id=uuid4(),
        tenant_id=tenant_id,
        error_id=sample_error.id,
        correction_type="MANUAL",
        description="Critical fix requiring validation",
        status=CorrectionStatus.BLOCKED,
        environment=Environment.PRODUCTION,
        executed_by="system",
        executed_at=datetime.utcnow(),
        requires_validation=True
    )
    db_session.add(correction)
    db_session.commit()
    db_session.refresh(correction)
    return correction


@pytest.fixture
def sample_correction_rule(db_session, tenant_id, user_id):
    """Fixture pour une règle de correction de test"""
    rule = CorrectionRule(
        id=12345,
        tenant_id=tenant_id,
        name="Auto-reconnect Database",
        error_type=ErrorType.DATABASE_ERROR,
        module="finance",
        auto_apply=True,
        requires_validation=False,
        max_retry=3,
        retry_delay_seconds=5,
        is_active=True,
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def sample_correction_test(db_session, tenant_id, sample_correction):
    """Fixture pour un test de correction"""
    test = CorrectionTest(
        id=uuid4(),
        tenant_id=tenant_id,
        correction_id=sample_correction.id,
        test_name="database_connection_test",
        test_type="SMOKE",
        status=TestResult.PASSED,
        executed_at=datetime.utcnow(),
        duration_seconds=0.5
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)
    return test


@pytest.fixture
def sample_alert(db_session, tenant_id):
    """Fixture pour une alerte Guardian de test"""
    alert = GuardianAlert(
        id=12345,
        tenant_id=tenant_id,
        severity=ErrorSeverity.HIGH,
        module="finance",
        message="High error rate detected",
        is_acknowledged=False,
        is_resolved=False,
        created_at=datetime.utcnow()
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def create_test_data():
    """Factory pour créer des données de test"""
    def _create(model_class, **kwargs):
        instance = model_class(**kwargs)
        return instance
    return _create


@pytest.fixture
def mock_service():
    """Mock du service Guardian pour tests unitaires"""
    service = Mock()
    service.get_config = Mock(return_value={"auto_correction_enabled": True})
    service.detect_error = Mock(return_value={"id": 1, "error_type": "TEST"})
    service.create_correction_registry = Mock(return_value={"id": str(uuid4())})
    return service


@pytest.fixture
def sample_error_data():
    """Données de test pour création erreur"""
    return {
        "error_type": "DATABASE_ERROR",
        "severity": "HIGH",
        "module": "finance",
        "message": "Connection timeout",
        "environment": "PRODUCTION"
    }


@pytest.fixture
def sample_correction_data(sample_error):
    """Données de test pour création correction"""
    return {
        "error_id": sample_error.id,
        "correction_type": "AUTO_FIX",
        "description": "Automatic fix applied",
        "environment": "PRODUCTION",
        "requires_validation": False
    }


@pytest.fixture
def sample_rule_data():
    """Données de test pour création règle"""
    return {
        "name": "Test Rule",
        "error_type": "DATABASE_ERROR",
        "module": "test",
        "auto_apply": False,
        "requires_validation": True,
        "max_retry": 3,
        "is_active": True
    }


# ============================================================================
# FIXTURES ASSERTIONS
# ============================================================================

@pytest.fixture
def assert_response_success():
    """Helper pour asserter une réponse successful"""
    def _assert(response, expected_status=200):
        assert response.status_code == expected_status
        if response.status_code != 204:  # No content
            data = response.json()
            assert data is not None
            return data
    return _assert


@pytest.fixture
def assert_tenant_isolation():
    """Helper pour vérifier l'isolation tenant (CRITIQUE pour monitoring)"""
    def _assert(response, tenant_id):
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if "tenant_id" in item:
                        assert item["tenant_id"] == tenant_id
            elif isinstance(data, dict):
                if "items" in data:  # Liste paginée
                    for item in data["items"]:
                        if "tenant_id" in item:
                            assert item["tenant_id"] == tenant_id
                elif "tenant_id" in data:
                    assert data["tenant_id"] == tenant_id
    return _assert


@pytest.fixture
def assert_audit_trail():
    """Helper pour vérifier la présence d'audit trail"""
    def _assert(response_data):
        # Guardian doit avoir traces d'exécution
        audit_fields = ["executed_by", "created_by", "validated_by",
                       "acknowledged_by", "resolved_by"]
        has_audit = any(field in response_data for field in audit_fields)
        assert has_audit, "Aucun champ d'audit trail trouvé dans Guardian"
    return _assert


@pytest.fixture
def assert_role_restriction():
    """Helper pour valider les restrictions de rôle"""
    def _assert(response):
        # Vérifier que la réponse est bien 403 Forbidden
        assert response.status_code == 403
        detail = response.json().get("detail", "")
        # Vérifier que le message mentionne les rôles requis
        assert "DIRIGEANT" in detail or "ADMIN" in detail
    return _assert
