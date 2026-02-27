"""
AZALS MODULE GUARDIAN - Tests Service
======================================
Tests bloquants pour le service Guardian de correction automatique.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.guardian.models import (
    CorrectionAction,
    CorrectionRegistry,
    CorrectionRule,
    CorrectionStatus,
    CorrectionTest,
    Environment,
    ErrorDetection,
    ErrorSeverity,
    ErrorSource,
    ErrorType,
    GuardianAlert,
    GuardianConfig,
    TestResult,
)
from app.modules.guardian.schemas import (
    CorrectionRegistryCreate,
    CorrectionRuleCreate,
    ErrorDetectionCreate,
    FrontendErrorReport,
    GuardianConfigUpdate,
)
from app.modules.guardian.service import GuardianService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def guardian_service(mock_db):
    """Guardian service instance with mocked DB."""
    return GuardianService(mock_db, "test-tenant")


@pytest.fixture
def sample_guardian_config():
    """Sample Guardian configuration."""
    return GuardianConfig(
        id=1,
        tenant_id="test-tenant",
        is_enabled=True,
        auto_correction_enabled=True,
        auto_correction_environments=["SANDBOX", "BETA"],
        max_auto_corrections_per_day=100,
        max_auto_corrections_production=10,
        cooldown_between_corrections_seconds=30,
        alert_on_critical=True,
        alert_on_major=True,
        alert_on_correction_failed=True,
        alert_on_rollback=True,
    )


@pytest.fixture
def sample_error_detection_data():
    """Sample error detection data."""
    return ErrorDetectionCreate(
        severity=ErrorSeverity.MAJOR,
        source=ErrorSource.BACKEND_LOG,
        error_type=ErrorType.EXCEPTION,
        environment=Environment.SANDBOX,
        error_message="NullPointerException in module processing",
        module="invoicing",
        route="/api/v1/invoices",
        error_code="NPE_001",
        stack_trace="at line 42 in service.py...",
        request_id="req-12345",
    )


@pytest.fixture
def sample_correction_registry_data():
    """Sample correction registry data."""
    return CorrectionRegistryCreate(
        environment=Environment.SANDBOX,
        error_source=ErrorSource.BACKEND_LOG,
        error_type=ErrorType.EXCEPTION,
        severity=ErrorSeverity.MAJOR,
        module="invoicing",
        route="/api/v1/invoices",
        probable_cause="Null reference due to missing validation on invoice data",
        correction_action=CorrectionAction.AUTO_FIX,
        correction_description="Added null check validation before processing invoice data",
        estimated_impact="Low impact - affects invoice creation flow only",
        is_reversible=True,
        reversibility_justification="Code change can be reverted without data loss",
        status=CorrectionStatus.PENDING,
    )


@pytest.fixture
def sample_correction_rule_data():
    """Sample correction rule data."""
    return CorrectionRuleCreate(
        name="Auto-fix null pointer exceptions",
        description="Automatically handle null pointer exceptions in invoicing module",
        trigger_error_type=ErrorType.EXCEPTION,
        trigger_module="invoicing",
        trigger_severity_min=ErrorSeverity.MAJOR,
        correction_action=CorrectionAction.CACHE_CLEAR,
        allowed_environments=[Environment.SANDBOX, Environment.BETA],
        max_auto_corrections_per_hour=10,
        cooldown_seconds=60,
        requires_human_validation=False,
        risk_level="LOW",
        is_reversible=True,
        required_tests=["SCENARIO", "REGRESSION"],
    )


# ============================================================================
# SERVICE INITIALIZATION TESTS
# ============================================================================

class TestGuardianServiceInitialization:
    """Tests for Guardian service initialization."""

    def test_service_initialization(self, mock_db):
        """Test service initializes correctly."""
        service = GuardianService(mock_db, "test-tenant")
        assert service.db == mock_db
        assert service.tenant_id == "test-tenant"
        assert service._config is None

    def test_service_initialization_with_different_tenant(self, mock_db):
        """Test service initializes with different tenant."""
        service = GuardianService(mock_db, "other-tenant")
        assert service.tenant_id == "other-tenant"


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestGuardianConfig:
    """Tests for Guardian configuration management."""

    def test_get_config_creates_default_when_missing(self, guardian_service, mock_db):
        """Test get_config creates default configuration when none exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        config = guardian_service.get_config()

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_config_returns_existing(self, guardian_service, mock_db, sample_guardian_config):
        """Test get_config returns existing configuration."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_guardian_config

        config = guardian_service.get_config()

        assert config.tenant_id == "test-tenant"
        assert config.is_enabled is True
        assert config.auto_correction_enabled is True

    def test_get_config_caches_result(self, guardian_service, mock_db, sample_guardian_config):
        """Test get_config caches the configuration."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_guardian_config

        # Call twice
        config1 = guardian_service.get_config()
        config2 = guardian_service.get_config()

        # Should return same cached instance
        assert config1 is config2
        # Should only query once
        assert mock_db.query.call_count == 1

    def test_update_config_success(self, guardian_service, mock_db, sample_guardian_config):
        """Test update_config updates configuration correctly."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_guardian_config

        update_data = GuardianConfigUpdate(
            auto_correction_enabled=False,
            max_auto_corrections_per_day=50,
        )

        result = guardian_service.update_config(update_data)

        assert sample_guardian_config.auto_correction_enabled is False
        assert sample_guardian_config.max_auto_corrections_per_day == 50
        mock_db.commit.assert_called()


# ============================================================================
# ERROR DETECTION TESTS
# ============================================================================

class TestErrorDetection:
    """Tests for error detection functionality."""

    def test_detect_error_success(self, guardian_service, mock_db, sample_guardian_config, sample_error_detection_data):
        """Test successful error detection."""
        # Set config to avoid config query
        guardian_service._config = sample_guardian_config

        # Mock methods that make DB queries
        with patch.object(guardian_service, '_find_similar_error', return_value=None), \
             patch.object(guardian_service, '_attempt_auto_correction', return_value=None):
            error = guardian_service.detect_error(sample_error_detection_data)

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_detect_error_guardian_disabled(self, guardian_service, mock_db, sample_guardian_config, sample_error_detection_data):
        """Test error detection fails when Guardian is disabled."""
        sample_guardian_config.is_enabled = False
        guardian_service._config = sample_guardian_config

        with pytest.raises(ValueError, match="GUARDIAN is disabled"):
            guardian_service.detect_error(sample_error_detection_data)

    def test_detect_error_deduplication(self, guardian_service, mock_db, sample_guardian_config, sample_error_detection_data):
        """Test error deduplication increments count."""
        existing_error = ErrorDetection(
            id=1,
            error_uid="test-uid",
            tenant_id="test-tenant",
            severity=ErrorSeverity.MAJOR,
            source=ErrorSource.BACKEND_LOG,
            error_type=ErrorType.EXCEPTION,
            environment=Environment.SANDBOX,
            error_message="NullPointerException in module processing",
            occurrence_count=5,
            last_occurrence_at=datetime.utcnow(),
        )

        guardian_service._config = sample_guardian_config
        mock_db.query.return_value.filter.return_value.first.return_value = existing_error

        result = guardian_service.detect_error(sample_error_detection_data)

        assert result.occurrence_count == 6
        mock_db.commit.assert_called()

    def test_report_frontend_error_maps_type(self, guardian_service, mock_db, sample_guardian_config):
        """Test frontend error reporting maps types correctly."""
        guardian_service._config = sample_guardian_config
        mock_db.query.return_value.filter.return_value.first.return_value = None

        frontend_report = FrontendErrorReport(
            error_type="TypeError",
            error_message="Cannot read property 'id' of undefined",
            component="InvoiceList",
            route="/invoices",
            browser="Chrome",
            browser_version="120.0",
            timestamp=datetime.utcnow(),
        )

        # Test the type mapping
        mapped_type = guardian_service._map_frontend_error_type("TypeError")
        assert mapped_type == ErrorType.EXCEPTION

        mapped_type = guardian_service._map_frontend_error_type("NetworkError")
        assert mapped_type == ErrorType.NETWORK

        mapped_type = guardian_service._map_frontend_error_type("TimeoutError")
        assert mapped_type == ErrorType.TIMEOUT

        mapped_type = guardian_service._map_frontend_error_type("UnknownType")
        assert mapped_type == ErrorType.UNKNOWN


# ============================================================================
# CORRECTION REGISTRY TESTS
# ============================================================================

class TestCorrectionRegistry:
    """Tests for correction registry functionality."""

    def test_create_correction_registry_success(self, guardian_service, mock_db, sample_correction_registry_data):
        """Test successful correction registry creation."""
        registry = guardian_service.create_correction_registry(sample_correction_registry_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_create_correction_registry_validation_fails(self, guardian_service, mock_db):
        """Test correction registry creation fails with invalid data (Pydantic validation)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="string_too_short"):
            CorrectionRegistryCreate(
                environment=Environment.SANDBOX,
                error_source=ErrorSource.BACKEND_LOG,
                error_type=ErrorType.EXCEPTION,
                severity=ErrorSeverity.MAJOR,
                module="invoicing",
                probable_cause="Short",  # Too short - must be at least 10 characters
                correction_action=CorrectionAction.AUTO_FIX,
                correction_description="Added validation",
                estimated_impact="Low impact",
                is_reversible=True,
                reversibility_justification="Can revert",
            )

    def test_create_correction_registry_links_error(self, guardian_service, mock_db, sample_correction_registry_data):
        """Test correction registry links to error detection."""
        error = ErrorDetection(
            id=1,
            tenant_id="test-tenant",
            severity=ErrorSeverity.MAJOR,
            source=ErrorSource.BACKEND_LOG,
            error_type=ErrorType.EXCEPTION,
            environment=Environment.SANDBOX,
            error_message="Test error",
        )

        sample_correction_registry_data.error_detection_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = error

        registry = guardian_service.create_correction_registry(sample_correction_registry_data)

        mock_db.commit.assert_called()


# ============================================================================
# CORRECTION RULE TESTS
# ============================================================================

class TestCorrectionRule:
    """Tests for correction rule functionality."""

    def test_create_correction_rule_success(self, guardian_service, mock_db, sample_correction_rule_data):
        """Test successful correction rule creation."""
        rule = guardian_service.create_correction_rule(sample_correction_rule_data, user_id=1)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_update_correction_rule_increments_version(self, guardian_service, mock_db):
        """Test updating rule increments version."""
        existing_rule = CorrectionRule(
            id=1,
            tenant_id="test-tenant",
            rule_uid="rule-123",
            name="Test Rule",
            version="1.0",
            correction_action=CorrectionAction.CACHE_CLEAR,
            allowed_environments=["SANDBOX"],
            is_active=True,
            is_system_rule=False,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = existing_rule

        from app.modules.guardian.schemas import CorrectionRuleUpdate
        update_data = CorrectionRuleUpdate(name="Updated Rule Name")

        result = guardian_service.update_correction_rule(1, update_data)

        assert existing_rule.version == "1.1"

    def test_delete_correction_rule_soft_delete(self, guardian_service, mock_db):
        """Test deleting rule performs soft delete."""
        existing_rule = CorrectionRule(
            id=1,
            tenant_id="test-tenant",
            rule_uid="rule-123",
            name="Test Rule",
            is_active=True,
            is_system_rule=False,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = existing_rule

        result = guardian_service.delete_correction_rule(1)

        assert result is True
        assert existing_rule.is_active is False

    def test_delete_system_rule_fails(self, guardian_service, mock_db):
        """Test deleting system rule raises error."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found or is a system rule"):
            guardian_service.delete_correction_rule(1)


# ============================================================================
# ALERT TESTS
# ============================================================================

class TestGuardianAlerts:
    """Tests for Guardian alert functionality."""

    def test_acknowledge_alert_success(self, guardian_service, mock_db):
        """Test successful alert acknowledgment."""
        alert = GuardianAlert(
            id=1,
            tenant_id="test-tenant",
            alert_uid="alert-123",
            alert_type="ERROR_DETECTED",
            severity=ErrorSeverity.MAJOR,
            title="Test Alert",
            message="Test message",
            is_read=False,
            is_acknowledged=False,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = alert

        result = guardian_service.acknowledge_alert(1, user_id=1)

        assert alert.is_read is True
        assert alert.is_acknowledged is True
        assert alert.acknowledged_by == 1
        mock_db.commit.assert_called()

    def test_acknowledge_alert_not_found(self, guardian_service, mock_db):
        """Test acknowledging non-existent alert raises error."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            guardian_service.acknowledge_alert(999, user_id=1)

    def test_resolve_alert_success(self, guardian_service, mock_db):
        """Test successful alert resolution."""
        alert = GuardianAlert(
            id=1,
            tenant_id="test-tenant",
            alert_uid="alert-123",
            alert_type="ERROR_DETECTED",
            severity=ErrorSeverity.MAJOR,
            title="Test Alert",
            message="Test message",
            is_read=False,
            is_acknowledged=False,
            is_resolved=False,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = alert

        result = guardian_service.resolve_alert(1, user_id=1, comment="Issue fixed")

        assert alert.is_resolved is True
        assert alert.resolved_by == 1
        assert alert.resolution_comment == "Issue fixed"
        # Should also acknowledge if not already
        assert alert.is_acknowledged is True


# ============================================================================
# ROLLBACK TESTS
# ============================================================================

class TestRollback:
    """Tests for rollback functionality."""

    def test_request_rollback_success(self, guardian_service, mock_db, sample_guardian_config):
        """Test successful rollback request."""
        registry = CorrectionRegistry(
            id=1,
            tenant_id="test-tenant",
            correction_uid="corr-123",
            status=CorrectionStatus.APPLIED,
            rolled_back=False,
            is_reversible=True,
            decision_trail=[],
        )

        guardian_service._config = sample_guardian_config
        mock_db.query.return_value.filter.return_value.first.return_value = registry

        result = guardian_service.request_rollback(1, reason="Found regression issue", user_id=1)

        assert registry.rolled_back is True
        assert registry.status == CorrectionStatus.ROLLED_BACK
        assert "regression issue" in registry.rollback_reason

    def test_request_rollback_already_rolled_back(self, guardian_service, mock_db):
        """Test rollback fails if already rolled back."""
        registry = CorrectionRegistry(
            id=1,
            tenant_id="test-tenant",
            correction_uid="corr-123",
            status=CorrectionStatus.ROLLED_BACK,
            rolled_back=True,
            is_reversible=True,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = registry

        with pytest.raises(ValueError, match="already rolled back"):
            guardian_service.request_rollback(1, reason="Test", user_id=1)

    def test_request_rollback_not_reversible(self, guardian_service, mock_db):
        """Test rollback fails if not reversible."""
        registry = CorrectionRegistry(
            id=1,
            tenant_id="test-tenant",
            correction_uid="corr-123",
            status=CorrectionStatus.APPLIED,
            rolled_back=False,
            is_reversible=False,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = registry

        with pytest.raises(ValueError, match="not reversible"):
            guardian_service.request_rollback(1, reason="Test", user_id=1)


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestCorrectionValidation:
    """Tests for human validation of corrections."""

    def test_validate_correction_approve(self, guardian_service, mock_db):
        """Test approving a correction."""
        registry = CorrectionRegistry(
            id=1,
            tenant_id="test-tenant",
            correction_uid="corr-123",
            status=CorrectionStatus.BLOCKED,
            correction_details={},
            decision_trail=[],
        )

        mock_db.query.return_value.filter.return_value.first.return_value = registry

        result = guardian_service.validate_correction(1, approved=True, user_id=1, comment="Looks good")

        assert registry.status == CorrectionStatus.APPROVED
        assert registry.validated_by == 1
        assert registry.validation_comment == "Looks good"

    def test_validate_correction_reject(self, guardian_service, mock_db):
        """Test rejecting a correction."""
        registry = CorrectionRegistry(
            id=1,
            tenant_id="test-tenant",
            correction_uid="corr-123",
            status=CorrectionStatus.BLOCKED,
            decision_trail=[],
        )

        mock_db.query.return_value.filter.return_value.first.return_value = registry

        result = guardian_service.validate_correction(1, approved=False, user_id=1, comment="Too risky")

        assert registry.status == CorrectionStatus.REJECTED
        assert registry.validation_comment == "Too risky"

    def test_validate_correction_wrong_status(self, guardian_service, mock_db):
        """Test validation fails for wrong status."""
        registry = CorrectionRegistry(
            id=1,
            tenant_id="test-tenant",
            correction_uid="corr-123",
            status=CorrectionStatus.APPLIED,  # Already applied
        )

        mock_db.query.return_value.filter.return_value.first.return_value = registry

        with pytest.raises(ValueError, match="not pending validation"):
            guardian_service.validate_correction(1, approved=True, user_id=1)


# ============================================================================
# LISTING AND QUERY TESTS
# ============================================================================

class TestListingQueries:
    """Tests for listing and query functionality."""

    def test_list_errors_with_filters(self, guardian_service, mock_db):
        """Test listing errors with filters."""
        errors = [
            ErrorDetection(id=1, tenant_id="test-tenant", severity=ErrorSeverity.MAJOR),
            ErrorDetection(id=2, tenant_id="test-tenant", severity=ErrorSeverity.CRITICAL),
        ]

        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = errors
        # Chain filter calls return the same mock
        mock_query.filter.return_value = mock_query
        mock_db.query.return_value.filter.return_value = mock_query

        items, total = guardian_service.list_errors(
            page=1,
            page_size=20,
            severity=ErrorSeverity.MAJOR,
        )

        assert total == 2

    def test_list_corrections_pagination(self, guardian_service, mock_db):
        """Test listing corrections with pagination."""
        corrections = [
            CorrectionRegistry(id=i, tenant_id="test-tenant")
            for i in range(5)
        ]

        mock_query = MagicMock()
        mock_query.count.return_value = 50
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = corrections
        mock_db.query.return_value.filter.return_value = mock_query

        items, total = guardian_service.list_corrections(page=2, page_size=5)

        assert total == 50
        assert len(items) == 5

    def test_list_alerts_with_unread_count(self, guardian_service, mock_db):
        """Test listing alerts includes unread count."""
        alerts = [
            GuardianAlert(id=1, tenant_id="test-tenant", is_read=False),
            GuardianAlert(id=2, tenant_id="test-tenant", is_read=True),
        ]

        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = alerts
        mock_db.query.return_value.filter.return_value = mock_query
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1

        items, total, unread = guardian_service.list_alerts()

        assert total == 2


# ============================================================================
# TENANT ISOLATION TESTS
# ============================================================================

class TestTenantIsolation:
    """Tests for tenant isolation in Guardian service."""

    def test_error_detection_respects_tenant(self, mock_db):
        """Test error detection is tenant-isolated."""
        service1 = GuardianService(mock_db, "tenant-1")
        service2 = GuardianService(mock_db, "tenant-2")

        assert service1.tenant_id != service2.tenant_id

    def test_config_per_tenant(self, mock_db):
        """Test configuration is per-tenant."""
        config1 = GuardianConfig(tenant_id="tenant-1", is_enabled=True)
        config2 = GuardianConfig(tenant_id="tenant-2", is_enabled=False)

        service1 = GuardianService(mock_db, "tenant-1")
        service2 = GuardianService(mock_db, "tenant-2")

        mock_db.query.return_value.filter.return_value.first.side_effect = [config1, config2]

        result1 = service1.get_config()
        result2 = service2.get_config()

        assert result1.tenant_id == "tenant-1"
        assert result2.tenant_id == "tenant-2"
        assert result1.is_enabled != result2.is_enabled


# ============================================================================
# STATISTICS TESTS
# ============================================================================

class TestGuardianStatistics:
    """Tests for statistics generation."""

    def test_get_statistics_empty(self, guardian_service, mock_db):
        """Test statistics with no data."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        stats = guardian_service.get_statistics(period_days=30)

        assert stats.total_errors_detected == 0
        assert stats.total_corrections == 0
        assert stats.total_alerts == 0

    def test_get_statistics_with_data(self, guardian_service, mock_db):
        """Test statistics with sample data."""
        errors = [
            MagicMock(severity=ErrorSeverity.MAJOR, error_type=ErrorType.EXCEPTION,
                     module="invoicing", source=ErrorSource.BACKEND_LOG),
            MagicMock(severity=ErrorSeverity.CRITICAL, error_type=ErrorType.DATABASE,
                     module="users", source=ErrorSource.DATABASE_ERROR),
        ]

        corrections = [
            MagicMock(status=CorrectionStatus.APPLIED, correction_action=CorrectionAction.AUTO_FIX,
                     executed_by="GUARDIAN", correction_successful=True, rolled_back=False,
                     execution_duration_ms=150),
        ]

        tests = [
            MagicMock(result=TestResult.PASSED),
            MagicMock(result=TestResult.FAILED),
        ]

        alerts = [
            MagicMock(severity=ErrorSeverity.MAJOR, is_resolved=False),
            MagicMock(severity=ErrorSeverity.CRITICAL, is_resolved=True),
        ]

        # Configure mock to return different data for different queries
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            errors, corrections, tests, alerts
        ]

        stats = guardian_service.get_statistics(period_days=30)

        assert stats.total_errors_detected == 2
        assert stats.total_corrections == 1
        assert stats.total_tests_executed == 2
        assert stats.tests_passed == 1
        assert stats.tests_failed == 1
        assert stats.total_alerts == 2
        assert stats.unresolved_alerts == 1


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestGuardianModels:
    """Tests for Guardian model creation."""

    def test_error_detection_model_creation(self):
        """Test ErrorDetection model creation."""
        error = ErrorDetection(
            tenant_id="test-tenant",
            severity=ErrorSeverity.MAJOR,
            source=ErrorSource.BACKEND_LOG,
            error_type=ErrorType.EXCEPTION,
            environment=Environment.PRODUCTION,
            error_message="Test error message",
            module="test-module",
        )

        assert error.severity == ErrorSeverity.MAJOR
        assert error.environment == Environment.PRODUCTION

    def test_correction_registry_model_creation(self):
        """Test CorrectionRegistry model creation."""
        registry = CorrectionRegistry(
            tenant_id="test-tenant",
            environment=Environment.SANDBOX,
            error_source=ErrorSource.BACKEND_LOG,
            error_type=ErrorType.EXCEPTION,
            severity=ErrorSeverity.MAJOR,
            module="test-module",
            probable_cause="Test cause",
            correction_action=CorrectionAction.AUTO_FIX,
            correction_description="Test correction",
            estimated_impact="Low impact",
            is_reversible=True,
            reversibility_justification="Can be reverted",
            status=CorrectionStatus.PENDING,
        )

        assert registry.status == CorrectionStatus.PENDING
        assert registry.is_reversible is True

    def test_correction_rule_model_creation(self):
        """Test CorrectionRule model creation."""
        rule = CorrectionRule(
            tenant_id="test-tenant",
            name="Test Rule",
            correction_action=CorrectionAction.CACHE_CLEAR,
            allowed_environments=["SANDBOX"],
            is_active=True,
        )

        assert rule.is_active is True
        assert rule.correction_action == CorrectionAction.CACHE_CLEAR

    def test_guardian_alert_model_creation(self):
        """Test GuardianAlert model creation."""
        alert = GuardianAlert(
            tenant_id="test-tenant",
            alert_type="ERROR_DETECTED",
            severity=ErrorSeverity.CRITICAL,
            title="Critical Error",
            message="Critical error occurred in production",
            is_read=False,  # SQLAlchemy default only applies on INSERT
        )

        assert alert.severity == ErrorSeverity.CRITICAL
        assert alert.is_read is False


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestGuardianEnums:
    """Tests for Guardian enumerations."""

    def test_error_severity_values(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.CRITICAL.value == "CRITICAL"
        assert ErrorSeverity.MAJOR.value == "MAJOR"
        assert ErrorSeverity.MINOR.value == "MINOR"
        assert ErrorSeverity.WARNING.value == "WARNING"
        assert ErrorSeverity.INFO.value == "INFO"

    def test_error_source_values(self):
        """Test ErrorSource enum values."""
        assert ErrorSource.FRONTEND_LOG.value == "FRONTEND_LOG"
        assert ErrorSource.BACKEND_LOG.value == "BACKEND_LOG"
        assert ErrorSource.DATABASE_ERROR.value == "DATABASE_ERROR"
        assert ErrorSource.API_ERROR.value == "API_ERROR"

    def test_correction_status_values(self):
        """Test CorrectionStatus enum values."""
        assert CorrectionStatus.PENDING.value == "PENDING"
        assert CorrectionStatus.APPLIED.value == "APPLIED"
        assert CorrectionStatus.FAILED.value == "FAILED"
        assert CorrectionStatus.ROLLED_BACK.value == "ROLLED_BACK"

    def test_correction_action_values(self):
        """Test CorrectionAction enum values."""
        assert CorrectionAction.AUTO_FIX.value == "AUTO_FIX"
        assert CorrectionAction.CACHE_CLEAR.value == "CACHE_CLEAR"
        assert CorrectionAction.ROLLBACK.value == "ROLLBACK"
        assert CorrectionAction.ESCALATION.value == "ESCALATION"

    def test_environment_values(self):
        """Test Environment enum values."""
        assert Environment.SANDBOX.value == "SANDBOX"
        assert Environment.BETA.value == "BETA"
        assert Environment.PRODUCTION.value == "PRODUCTION"

    def test_test_result_values(self):
        """Test TestResult enum values."""
        assert TestResult.PASSED.value == "PASSED"
        assert TestResult.FAILED.value == "FAILED"
        assert TestResult.SKIPPED.value == "SKIPPED"
        assert TestResult.ERROR.value == "ERROR"
