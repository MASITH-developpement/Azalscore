"""
AZALS - Module DataExchange - Tests Models
==========================================
Tests unitaires pour les modeles SQLAlchemy du module DataExchange.
"""
import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.modules.dataexchange.models import (
    FileFormat,
    ExchangeType,
    ExchangeStatus,
    ConnectorType,
    ScheduleFrequency,
    TransformationType,
    FieldDataType,
    ValidationRuleType,
    NotificationType,
    NotificationEvent,
    ExchangeProfile,
    FieldMapping,
    ValidationRule,
    Transformation,
    FileConnector,
    ScheduledExchange,
    ExchangeJob,
    ExchangeLog,
    ExchangeError,
    ExchangeHistory,
    NotificationConfig,
    LookupTable,
)


# ============== Test Enumerations ==============

class TestFileFormat:
    """Tests pour l'enumeration FileFormat."""

    def test_csv_format(self):
        assert FileFormat.CSV.value == "csv"

    def test_excel_format(self):
        assert FileFormat.EXCEL.value == "excel"

    def test_json_format(self):
        assert FileFormat.JSON.value == "json"

    def test_xml_format(self):
        assert FileFormat.XML.value == "xml"

    def test_ofx_format(self):
        assert FileFormat.OFX.value == "ofx"

    def test_fec_format(self):
        assert FileFormat.FEC.value == "fec"


class TestExchangeType:
    """Tests pour l'enumeration ExchangeType."""

    def test_import_type(self):
        assert ExchangeType.IMPORT.value == "import"

    def test_export_type(self):
        assert ExchangeType.EXPORT.value == "export"


class TestExchangeStatus:
    """Tests pour l'enumeration ExchangeStatus."""

    def test_all_statuses(self):
        expected_statuses = [
            "draft", "pending", "validating", "processing",
            "completed", "partial", "failed", "cancelled", "rolled_back"
        ]
        actual_statuses = [s.value for s in ExchangeStatus]
        assert sorted(actual_statuses) == sorted(expected_statuses)


class TestConnectorType:
    """Tests pour l'enumeration ConnectorType."""

    def test_local_connector(self):
        assert ConnectorType.LOCAL.value == "local"

    def test_ftp_connector(self):
        assert ConnectorType.FTP.value == "ftp"

    def test_s3_connector(self):
        assert ConnectorType.S3.value == "s3"


class TestTransformationType:
    """Tests pour l'enumeration TransformationType."""

    def test_transformation_types(self):
        assert TransformationType.UPPERCASE.value == "uppercase"
        assert TransformationType.LOWERCASE.value == "lowercase"
        assert TransformationType.TRIM.value == "trim"
        assert TransformationType.LOOKUP.value == "lookup"


# ============== Test Models ==============

class TestExchangeProfile:
    """Tests pour le modele ExchangeProfile."""

    def test_profile_table_name(self):
        assert ExchangeProfile.__tablename__ == "dataexchange_profiles"

    def test_profile_has_tenant_id(self):
        assert hasattr(ExchangeProfile, "tenant_id")

    def test_profile_has_soft_delete(self):
        assert hasattr(ExchangeProfile, "is_deleted")
        assert hasattr(ExchangeProfile, "deleted_at")
        assert hasattr(ExchangeProfile, "deleted_by")

    def test_profile_has_version(self):
        assert hasattr(ExchangeProfile, "version")

    def test_profile_has_audit_fields(self):
        assert hasattr(ExchangeProfile, "created_at")
        assert hasattr(ExchangeProfile, "created_by")
        assert hasattr(ExchangeProfile, "updated_at")
        assert hasattr(ExchangeProfile, "updated_by")


class TestFieldMapping:
    """Tests pour le modele FieldMapping."""

    def test_mapping_table_name(self):
        assert FieldMapping.__tablename__ == "dataexchange_field_mappings"

    def test_mapping_has_profile_relationship(self):
        assert hasattr(FieldMapping, "profile_id")

    def test_mapping_has_source_and_target(self):
        assert hasattr(FieldMapping, "source_field")
        assert hasattr(FieldMapping, "target_field")


class TestValidationRule:
    """Tests pour le modele ValidationRule."""

    def test_validation_table_name(self):
        assert ValidationRule.__tablename__ == "dataexchange_validation_rules"

    def test_validation_has_rule_type(self):
        assert hasattr(ValidationRule, "rule_type")

    def test_validation_has_configuration(self):
        assert hasattr(ValidationRule, "configuration")


class TestTransformation:
    """Tests pour le modele Transformation."""

    def test_transformation_table_name(self):
        assert Transformation.__tablename__ == "dataexchange_transformations"

    def test_transformation_has_type(self):
        assert hasattr(Transformation, "transformation_type")


class TestFileConnector:
    """Tests pour le modele FileConnector."""

    def test_connector_table_name(self):
        assert FileConnector.__tablename__ == "dataexchange_file_connectors"

    def test_connector_has_tenant_id(self):
        assert hasattr(FileConnector, "tenant_id")

    def test_connector_has_connection_params(self):
        assert hasattr(FileConnector, "connection_params")


class TestScheduledExchange:
    """Tests pour le modele ScheduledExchange."""

    def test_schedule_table_name(self):
        assert ScheduledExchange.__tablename__ == "dataexchange_scheduled_exchanges"

    def test_schedule_has_frequency(self):
        assert hasattr(ScheduledExchange, "frequency")

    def test_schedule_has_cron_expression(self):
        assert hasattr(ScheduledExchange, "cron_expression")

    def test_schedule_has_active_flag(self):
        assert hasattr(ScheduledExchange, "is_active")


class TestExchangeJob:
    """Tests pour le modele ExchangeJob."""

    def test_job_table_name(self):
        assert ExchangeJob.__tablename__ == "dataexchange_jobs"

    def test_job_has_status(self):
        assert hasattr(ExchangeJob, "status")

    def test_job_has_counters(self):
        assert hasattr(ExchangeJob, "total_rows")
        assert hasattr(ExchangeJob, "processed_rows")
        assert hasattr(ExchangeJob, "success_count")
        assert hasattr(ExchangeJob, "error_count")

    def test_job_has_rollback_data(self):
        assert hasattr(ExchangeJob, "rollback_data")
        assert hasattr(ExchangeJob, "is_rolled_back")


class TestExchangeLog:
    """Tests pour le modele ExchangeLog."""

    def test_log_table_name(self):
        assert ExchangeLog.__tablename__ == "dataexchange_logs"

    def test_log_has_job_id(self):
        assert hasattr(ExchangeLog, "job_id")

    def test_log_has_level(self):
        assert hasattr(ExchangeLog, "level")


class TestExchangeError:
    """Tests pour le modele ExchangeError."""

    def test_error_table_name(self):
        assert ExchangeError.__tablename__ == "dataexchange_errors"

    def test_error_has_row_number(self):
        assert hasattr(ExchangeError, "row_number")

    def test_error_has_error_details(self):
        assert hasattr(ExchangeError, "error_code")
        assert hasattr(ExchangeError, "error_message")


class TestExchangeHistory:
    """Tests pour le modele ExchangeHistory."""

    def test_history_table_name(self):
        assert ExchangeHistory.__tablename__ == "dataexchange_history"

    def test_history_has_action(self):
        assert hasattr(ExchangeHistory, "action")


class TestNotificationConfig:
    """Tests pour le modele NotificationConfig."""

    def test_notification_table_name(self):
        assert NotificationConfig.__tablename__ == "dataexchange_notification_configs"

    def test_notification_has_type(self):
        assert hasattr(NotificationConfig, "notification_type")

    def test_notification_has_events(self):
        assert hasattr(NotificationConfig, "events")


class TestLookupTable:
    """Tests pour le modele LookupTable."""

    def test_lookup_table_name(self):
        assert LookupTable.__tablename__ == "dataexchange_lookup_tables"

    def test_lookup_has_entries(self):
        assert hasattr(LookupTable, "entries")
