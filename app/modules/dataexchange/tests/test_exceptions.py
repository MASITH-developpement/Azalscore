"""
AZALS - Module DataExchange - Tests Exceptions
===============================================
Tests unitaires pour les exceptions du module DataExchange.
"""
import uuid

import pytest

from app.modules.dataexchange.exceptions import (
    # Base exception
    DataExchangeError,

    # Profile errors
    ProfileNotFoundError,
    ProfileDuplicateCodeError,
    ProfileInUseError,
    SystemProfileError,

    # Connector errors
    ConnectorNotFoundError,
    ConnectorDuplicateCodeError,
    ConnectorConnectionError,
    ConnectorAuthenticationError,
    ConnectorInUseError,

    # Schedule errors
    ScheduledExchangeNotFoundError,
    ScheduledExchangeDuplicateCodeError,
    InvalidCronExpressionError,

    # Job errors
    JobNotFoundError,
    JobAlreadyRunningError,
    JobCannotBeCancelledError,
    JobCannotBeRolledBackError,
    JobAlreadyRolledBackError,

    # File errors
    FileNotFoundError as DataExchangeFileNotFoundError,
    FileFormatError,
    FileReadError,
    FileWriteError,
    FileTooLargeError,
    FileEncodingError,

    # Validation errors
    ValidationError,
    RequiredFieldMissingError,
    InvalidFieldValueError,
    DuplicateKeyError,
    ReferenceNotFoundError,

    # Mapping errors
    MappingNotFoundError,
    MappingConfigurationError,
    NoKeyFieldDefinedError,

    # Transformation errors
    TransformationError,
    TransformationScriptError,
    LookupTableNotFoundError,
    LookupValueNotFoundError,

    # Notification errors
    NotificationConfigNotFoundError,
    NotificationSendError,

    # Processing errors
    ProcessingError,
    EntityCreationError,
    EntityUpdateError,
    RollbackError,
)


# ============== Test Base Exception ==============

class TestDataExchangeError:
    """Tests pour DataExchangeError."""

    def test_base_exception_with_message(self):
        error = DataExchangeError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.code == "DATAEXCHANGE_ERROR"

    def test_base_exception_with_code(self):
        error = DataExchangeError("Test error", code="CUSTOM_CODE")
        assert error.code == "CUSTOM_CODE"

    def test_base_exception_with_details(self):
        details = {"key": "value", "count": 5}
        error = DataExchangeError("Test error", details=details)
        assert error.details == details
        assert error.details["key"] == "value"


# ============== Test Profile Errors ==============

class TestProfileErrors:
    """Tests pour les erreurs de profils."""

    def test_profile_not_found(self):
        profile_id = str(uuid.uuid4())
        error = ProfileNotFoundError(profile_id)
        assert error.code == "PROFILE_NOT_FOUND"
        assert profile_id in str(error)
        assert error.details["profile_id"] == profile_id

    def test_profile_duplicate_code(self):
        error = ProfileDuplicateCodeError("IMP_CLIENTS")
        assert error.code == "PROFILE_DUPLICATE_CODE"
        assert "IMP_CLIENTS" in str(error)
        assert error.details["code"] == "IMP_CLIENTS"

    def test_profile_in_use(self):
        profile_id = str(uuid.uuid4())
        error = ProfileInUseError(profile_id, usage_count=5)
        assert error.code == "PROFILE_IN_USE"
        assert "5" in str(error)
        assert error.details["usage_count"] == 5

    def test_system_profile_error(self):
        profile_id = str(uuid.uuid4())
        error = SystemProfileError(profile_id, "delete")
        assert error.code == "SYSTEM_PROFILE_ERROR"
        assert "delete" in str(error)
        assert error.details["operation"] == "delete"


# ============== Test Connector Errors ==============

class TestConnectorErrors:
    """Tests pour les erreurs de connecteurs."""

    def test_connector_not_found(self):
        connector_id = str(uuid.uuid4())
        error = ConnectorNotFoundError(connector_id)
        assert error.code == "CONNECTOR_NOT_FOUND"
        assert connector_id in str(error)

    def test_connector_duplicate_code(self):
        error = ConnectorDuplicateCodeError("FTP_MAIN")
        assert error.code == "CONNECTOR_DUPLICATE_CODE"
        assert "FTP_MAIN" in str(error)

    def test_connector_connection_error(self):
        connector_id = str(uuid.uuid4())
        error = ConnectorConnectionError(connector_id, "Connection refused")
        assert error.code == "CONNECTOR_CONNECTION_ERROR"
        assert "Connection refused" in str(error)

    def test_connector_authentication_error(self):
        connector_id = str(uuid.uuid4())
        error = ConnectorAuthenticationError(connector_id)
        assert error.code == "CONNECTOR_AUTH_ERROR"
        assert "authentification" in str(error).lower()

    def test_connector_in_use(self):
        connector_id = str(uuid.uuid4())
        error = ConnectorInUseError(connector_id, usage_count=3)
        assert error.code == "CONNECTOR_IN_USE"
        assert error.details["usage_count"] == 3


# ============== Test Schedule Errors ==============

class TestScheduleErrors:
    """Tests pour les erreurs de planification."""

    def test_scheduled_exchange_not_found(self):
        schedule_id = str(uuid.uuid4())
        error = ScheduledExchangeNotFoundError(schedule_id)
        assert error.code == "SCHEDULED_NOT_FOUND"
        assert schedule_id in str(error)

    def test_scheduled_exchange_duplicate_code(self):
        error = ScheduledExchangeDuplicateCodeError("DAILY_EXPORT")
        assert error.code == "SCHEDULED_DUPLICATE_CODE"
        assert "DAILY_EXPORT" in str(error)

    def test_invalid_cron_expression(self):
        error = InvalidCronExpressionError("invalid cron")
        assert error.code == "INVALID_CRON_EXPRESSION"
        assert "invalid cron" in str(error)


# ============== Test Job Errors ==============

class TestJobErrors:
    """Tests pour les erreurs de jobs."""

    def test_job_not_found(self):
        job_id = str(uuid.uuid4())
        error = JobNotFoundError(job_id)
        assert error.code == "JOB_NOT_FOUND"
        assert job_id in str(error)

    def test_job_already_running(self):
        job_id = str(uuid.uuid4())
        error = JobAlreadyRunningError(job_id)
        assert error.code == "JOB_ALREADY_RUNNING"

    def test_job_cannot_be_cancelled(self):
        job_id = str(uuid.uuid4())
        error = JobCannotBeCancelledError(job_id, "completed")
        assert error.code == "JOB_CANNOT_CANCEL"
        assert "completed" in str(error)

    def test_job_cannot_be_rolled_back(self):
        job_id = str(uuid.uuid4())
        error = JobCannotBeRolledBackError(job_id, "Job has no rollback data")
        assert error.code == "JOB_CANNOT_ROLLBACK"
        assert "rollback data" in str(error)

    def test_job_already_rolled_back(self):
        job_id = str(uuid.uuid4())
        error = JobAlreadyRolledBackError(job_id)
        assert error.code == "JOB_ALREADY_ROLLED_BACK"


# ============== Test File Errors ==============

class TestFileErrors:
    """Tests pour les erreurs de fichiers."""

    def test_file_not_found(self):
        error = DataExchangeFileNotFoundError("/path/to/file.csv")
        assert error.code == "FILE_NOT_FOUND"
        assert "/path/to/file.csv" in str(error)

    def test_file_format_error(self):
        error = FileFormatError("xyz", reason="Unknown format")
        assert error.code == "FILE_FORMAT_ERROR"
        assert "xyz" in str(error)
        assert "Unknown format" in str(error)

    def test_file_format_error_without_reason(self):
        error = FileFormatError("abc")
        assert error.code == "FILE_FORMAT_ERROR"
        assert "abc" in str(error)

    def test_file_read_error(self):
        error = FileReadError("/path/to/file.csv", "Permission denied")
        assert error.code == "FILE_READ_ERROR"
        assert "Permission denied" in str(error)

    def test_file_write_error(self):
        error = FileWriteError("/path/to/output.csv", "Disk full")
        assert error.code == "FILE_WRITE_ERROR"
        assert "Disk full" in str(error)

    def test_file_too_large(self):
        error = FileTooLargeError(file_size=100000000, max_size=50000000)
        assert error.code == "FILE_TOO_LARGE"
        assert error.details["file_size"] == 100000000
        assert error.details["max_size"] == 50000000

    def test_file_encoding_error(self):
        error = FileEncodingError("utf-8", "Invalid byte sequence")
        assert error.code == "FILE_ENCODING_ERROR"
        assert "utf-8" in str(error)


# ============== Test Validation Errors ==============

class TestValidationErrors:
    """Tests pour les erreurs de validation."""

    def test_validation_error(self):
        errors = [
            {"field": "email", "type": "invalid"},
            {"field": "phone", "type": "required"},
        ]
        error = ValidationError("Erreurs de validation", errors=errors)
        assert error.code == "VALIDATION_ERROR"
        assert len(error.errors) == 2

    def test_required_field_missing(self):
        error = RequiredFieldMissingError("email", row=5)
        assert error.code == "VALIDATION_ERROR"
        assert "email" in str(error)
        assert "5" in str(error)

    def test_required_field_missing_without_row(self):
        error = RequiredFieldMissingError("name")
        assert "name" in str(error)

    def test_invalid_field_value(self):
        error = InvalidFieldValueError(
            field="age",
            value="not-a-number",
            expected="integer",
            row=10
        )
        assert error.code == "VALIDATION_ERROR"
        assert "age" in str(error)
        assert "not-a-number" in str(error)

    def test_duplicate_key(self):
        error = DuplicateKeyError(
            key_field="email",
            value="test@example.com",
            rows=[5, 15, 25]
        )
        assert error.code == "VALIDATION_ERROR"
        assert "test@example.com" in str(error)
        assert error.errors[0]["rows"] == [5, 15, 25]

    def test_reference_not_found(self):
        error = ReferenceNotFoundError(
            field="client_id",
            value="CLI001",
            entity_type="client",
            row=7
        )
        assert error.code == "VALIDATION_ERROR"
        assert "CLI001" in str(error)
        assert "client" in str(error)


# ============== Test Mapping Errors ==============

class TestMappingErrors:
    """Tests pour les erreurs de mapping."""

    def test_mapping_not_found(self):
        mapping_id = str(uuid.uuid4())
        error = MappingNotFoundError(mapping_id)
        assert error.code == "MAPPING_NOT_FOUND"
        assert mapping_id in str(error)

    def test_mapping_configuration_error(self):
        error = MappingConfigurationError("Invalid transformation", field="name")
        assert error.code == "MAPPING_CONFIG_ERROR"
        assert "Invalid transformation" in str(error)
        assert error.details.get("field") == "name"

    def test_no_key_field_defined(self):
        error = NoKeyFieldDefinedError()
        assert error.code == "MAPPING_CONFIG_ERROR"
        assert "deduplication" in str(error).lower()


# ============== Test Transformation Errors ==============

class TestTransformationErrors:
    """Tests pour les erreurs de transformation."""

    def test_transformation_error(self):
        error = TransformationError(
            "Division by zero",
            transformation_code="FORMULA_001",
            row=15
        )
        assert error.code == "TRANSFORMATION_ERROR"
        assert "Division by zero" in str(error)
        assert error.details["transformation_code"] == "FORMULA_001"
        assert error.details["row"] == 15

    def test_transformation_script_error(self):
        error = TransformationScriptError(
            "SyntaxError: unexpected token",
            transformation_code="CUSTOM_001"
        )
        assert error.code == "TRANSFORMATION_ERROR"
        assert "SyntaxError" in str(error)

    def test_lookup_table_not_found(self):
        error = LookupTableNotFoundError("COUNTRY_CODES")
        assert error.code == "LOOKUP_TABLE_NOT_FOUND"
        assert "COUNTRY_CODES" in str(error)

    def test_lookup_value_not_found(self):
        error = LookupValueNotFoundError("COUNTRY_CODES", "XX")
        assert error.code == "LOOKUP_VALUE_NOT_FOUND"
        assert "XX" in str(error)
        assert "COUNTRY_CODES" in str(error)


# ============== Test Notification Errors ==============

class TestNotificationErrors:
    """Tests pour les erreurs de notification."""

    def test_notification_config_not_found(self):
        config_id = str(uuid.uuid4())
        error = NotificationConfigNotFoundError(config_id)
        assert error.code == "NOTIFICATION_CONFIG_NOT_FOUND"
        assert config_id in str(error)

    def test_notification_send_error(self):
        error = NotificationSendError("email", "SMTP connection failed")
        assert error.code == "NOTIFICATION_SEND_ERROR"
        assert "email" in str(error)
        assert "SMTP" in str(error)


# ============== Test Processing Errors ==============

class TestProcessingErrors:
    """Tests pour les erreurs de traitement."""

    def test_processing_error(self):
        error = ProcessingError(
            "Database constraint violation",
            row=50,
            entity_type="invoice"
        )
        assert error.code == "PROCESSING_ERROR"
        assert "Database constraint" in str(error)
        assert error.details["row"] == 50
        assert error.details["entity_type"] == "invoice"

    def test_entity_creation_error(self):
        error = EntityCreationError(
            entity_type="client",
            error="Duplicate email",
            row=10
        )
        assert error.code == "PROCESSING_ERROR"
        assert "client" in str(error)
        assert "Duplicate email" in str(error)

    def test_entity_update_error(self):
        entity_id = str(uuid.uuid4())
        error = EntityUpdateError(
            entity_type="product",
            entity_id=entity_id,
            error="Stock cannot be negative",
            row=20
        )
        assert error.code == "PROCESSING_ERROR"
        assert "product" in str(error)
        assert entity_id in str(error)

    def test_rollback_error(self):
        job_id = str(uuid.uuid4())
        error = RollbackError(job_id, "Rollback data corrupted")
        assert error.code == "ROLLBACK_ERROR"
        assert "corrupted" in str(error)
        assert error.details["job_id"] == job_id


# ============== Test Exception Inheritance ==============

class TestExceptionInheritance:
    """Tests pour l'heritage des exceptions."""

    def test_all_exceptions_inherit_from_base(self):
        """Verifie que toutes les exceptions heritent de DataExchangeError."""
        exceptions = [
            ProfileNotFoundError("id"),
            ConnectorNotFoundError("id"),
            JobNotFoundError("id"),
            DataExchangeFileNotFoundError("/path"),
            ValidationError("message"),
            MappingNotFoundError("id"),
            TransformationError("message"),
            ProcessingError("message"),
        ]
        for exc in exceptions:
            assert isinstance(exc, DataExchangeError)

    def test_validation_errors_inherit_from_validation(self):
        """Verifie que les erreurs de validation heritent de ValidationError."""
        exceptions = [
            RequiredFieldMissingError("field"),
            InvalidFieldValueError("field", "value", "expected"),
            DuplicateKeyError("field", "value", [1, 2]),
            ReferenceNotFoundError("field", "value", "entity"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ValidationError)
