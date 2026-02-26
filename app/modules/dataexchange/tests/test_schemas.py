"""
AZALS - Module DataExchange - Tests Schemas
============================================
Tests unitaires pour les schemas Pydantic du module DataExchange.
"""
import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

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
)
from app.modules.dataexchange.schemas import (
    # Profile schemas
    ExchangeProfileCreate,
    ExchangeProfileUpdate,
    ExchangeProfileResponse,

    # Field Mapping schemas
    FieldMappingCreate,
    FieldMappingUpdate,
    FieldMappingResponse,

    # Validation Rule schemas
    ValidationRuleCreate,
    ValidationRuleResponse,

    # Transformation schemas
    TransformationCreate,
    TransformationResponse,

    # Connector schemas
    FileConnectorCreate,
    FileConnectorUpdate,
    FileConnectorResponse,

    # Scheduled Exchange schemas
    ScheduledExchangeCreate,
    ScheduledExchangeUpdate,
    ScheduledExchangeResponse,

    # Job schemas
    ExchangeJobCreate,
    ExchangeJobResponse,

    # Lookup Table schemas
    LookupTableCreate,
    LookupTableResponse,

    # Filter schemas
    ProfileFilters as ExchangeProfileFilter,
    JobFilters as ExchangeJobFilter,

    # Request schemas
    ImportRequest,
    ExportRequest,
)


# ============== Test Profile Schemas ==============

class TestExchangeProfileCreate:
    """Tests pour ExchangeProfileCreate schema."""

    def test_valid_import_profile(self):
        data = {
            "code": "IMP_CLIENTS",
            "name": "Import Clients",
            "exchange_type": ExchangeType.IMPORT,
            "file_format": FileFormat.CSV,
            "entity_type": "client",
        }
        profile = ExchangeProfileCreate(**data)
        assert profile.code == "IMP_CLIENTS"
        assert profile.name == "Import Clients"
        assert profile.exchange_type == ExchangeType.IMPORT
        assert profile.file_format == FileFormat.CSV

    def test_valid_export_profile(self):
        data = {
            "code": "EXP_FACTURES",
            "name": "Export Factures",
            "exchange_type": ExchangeType.EXPORT,
            "file_format": FileFormat.EXCEL,
            "entity_type": "invoice",
        }
        profile = ExchangeProfileCreate(**data)
        assert profile.exchange_type == ExchangeType.EXPORT
        assert profile.file_format == FileFormat.EXCEL

    def test_missing_required_field(self):
        data = {
            "name": "Import Clients",
            "exchange_type": ExchangeType.IMPORT,
        }
        with pytest.raises(ValidationError):
            ExchangeProfileCreate(**data)

    def test_profile_with_options(self):
        data = {
            "code": "IMP_CSV",
            "name": "Import CSV",
            "exchange_type": ExchangeType.IMPORT,
            "file_format": FileFormat.CSV,
            "entity_type": "product",
            "file_encoding": "utf-8",
            "csv_delimiter": ";",
            "csv_quote_char": '"',
            "has_header": True,
            "skip_rows": 1,
        }
        profile = ExchangeProfileCreate(**data)
        assert profile.csv_delimiter == ";"
        assert profile.has_header is True


class TestExchangeProfileUpdate:
    """Tests pour ExchangeProfileUpdate schema."""

    def test_partial_update(self):
        data = {
            "name": "Nouveau Nom",
        }
        update = ExchangeProfileUpdate(**data)
        assert update.name == "Nouveau Nom"
        assert update.code is None

    def test_update_description(self):
        data = {
            "description": "Description mise a jour",
            "is_active": False,
        }
        update = ExchangeProfileUpdate(**data)
        assert update.description == "Description mise a jour"
        assert update.is_active is False


# ============== Test Field Mapping Schemas ==============

class TestFieldMappingCreate:
    """Tests pour FieldMappingCreate schema."""

    def test_valid_mapping(self):
        data = {
            "source_field": "nom_client",
            "target_field": "name",
            "data_type": FieldDataType.STRING,
            "is_required": True,
        }
        mapping = FieldMappingCreate(**data)
        assert mapping.source_field == "nom_client"
        assert mapping.target_field == "name"
        assert mapping.is_required is True

    def test_mapping_with_default_value(self):
        data = {
            "source_field": "pays",
            "target_field": "country",
            "data_type": FieldDataType.STRING,
            "default_value": "France",
        }
        mapping = FieldMappingCreate(**data)
        assert mapping.default_value == "France"

    def test_key_field_mapping(self):
        data = {
            "source_field": "code_client",
            "target_field": "client_code",
            "data_type": FieldDataType.STRING,
            "is_key": True,
        }
        mapping = FieldMappingCreate(**data)
        assert mapping.is_key is True


# ============== Test Validation Rule Schemas ==============

class TestValidationRuleCreate:
    """Tests pour ValidationRuleCreate schema."""

    def test_required_rule(self):
        data = {
            "rule_type": ValidationRuleType.REQUIRED,
            "field_name": "email",
            "error_message": "Email requis",
        }
        rule = ValidationRuleCreate(**data)
        assert rule.rule_type == ValidationRuleType.REQUIRED
        assert rule.field_name == "email"

    def test_regex_rule(self):
        data = {
            "rule_type": ValidationRuleType.REGEX,
            "field_name": "phone",
            "configuration": {"pattern": r"^\+?[0-9]{10,15}$"},
            "error_message": "Numero de telephone invalide",
        }
        rule = ValidationRuleCreate(**data)
        assert rule.configuration["pattern"] is not None


# ============== Test Connector Schemas ==============

class TestFileConnectorCreate:
    """Tests pour FileConnectorCreate schema."""

    def test_ftp_connector(self):
        data = {
            "code": "FTP_MAIN",
            "name": "FTP Principal",
            "connector_type": ConnectorType.FTP,
            "connection_params": {
                "host": "ftp.example.com",
                "port": 21,
                "username": "user",
            },
        }
        connector = FileConnectorCreate(**data)
        assert connector.connector_type == ConnectorType.FTP
        assert connector.connection_params["host"] == "ftp.example.com"

    def test_s3_connector(self):
        data = {
            "code": "S3_BACKUP",
            "name": "S3 Backup",
            "connector_type": ConnectorType.S3,
            "connection_params": {
                "bucket": "my-bucket",
                "region": "eu-west-1",
            },
        }
        connector = FileConnectorCreate(**data)
        assert connector.connector_type == ConnectorType.S3


class TestFileConnectorUpdate:
    """Tests pour FileConnectorUpdate schema."""

    def test_update_connection(self):
        data = {
            "connection_params": {
                "host": "new-ftp.example.com",
                "port": 22,
            },
        }
        update = FileConnectorUpdate(**data)
        assert update.connection_params["host"] == "new-ftp.example.com"


# ============== Test Scheduled Exchange Schemas ==============

class TestScheduledExchangeCreate:
    """Tests pour ScheduledExchangeCreate schema."""

    def test_daily_schedule(self):
        profile_id = uuid.uuid4()
        data = {
            "code": "DAILY_EXPORT",
            "name": "Export Quotidien",
            "profile_id": profile_id,
            "frequency": ScheduleFrequency.DAILY,
            "schedule_time": "23:00",
        }
        schedule = ScheduledExchangeCreate(**data)
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.schedule_time == "23:00"

    def test_cron_schedule(self):
        profile_id = uuid.uuid4()
        data = {
            "code": "CRON_IMPORT",
            "name": "Import Cron",
            "profile_id": profile_id,
            "frequency": ScheduleFrequency.CRON,
            "cron_expression": "0 */2 * * *",
        }
        schedule = ScheduledExchangeCreate(**data)
        assert schedule.cron_expression == "0 */2 * * *"


# ============== Test Job Schemas ==============

class TestExchangeJobCreate:
    """Tests pour ExchangeJobCreate schema."""

    def test_create_job(self):
        profile_id = uuid.uuid4()
        data = {
            "profile_id": profile_id,
            "file_name": "clients.csv",
            "file_size": 1024,
        }
        job = ExchangeJobCreate(**data)
        assert job.profile_id == profile_id
        assert job.file_name == "clients.csv"


# ============== Test Lookup Table Schemas ==============

class TestLookupTableCreate:
    """Tests pour LookupTableCreate schema."""

    def test_create_lookup(self):
        data = {
            "code": "COUNTRY_CODES",
            "name": "Codes Pays",
            "entries": {
                "FR": "France",
                "DE": "Allemagne",
                "ES": "Espagne",
            },
        }
        lookup = LookupTableCreate(**data)
        assert lookup.code == "COUNTRY_CODES"
        assert lookup.entries["FR"] == "France"


# ============== Test Filter Schemas ==============

class TestExchangeProfileFilter:
    """Tests pour ExchangeProfileFilter schema."""

    def test_filter_by_type(self):
        data = {
            "exchange_type": ExchangeType.IMPORT,
        }
        filter_obj = ExchangeProfileFilter(**data)
        assert filter_obj.exchange_type == ExchangeType.IMPORT

    def test_filter_by_format(self):
        data = {
            "file_format": FileFormat.CSV,
            "is_active": True,
        }
        filter_obj = ExchangeProfileFilter(**data)
        assert filter_obj.file_format == FileFormat.CSV


class TestExchangeJobFilter:
    """Tests pour ExchangeJobFilter schema."""

    def test_filter_by_status(self):
        data = {
            "status": ExchangeStatus.COMPLETED,
        }
        filter_obj = ExchangeJobFilter(**data)
        assert filter_obj.status == ExchangeStatus.COMPLETED


# ============== Test Request Schemas ==============

class TestImportRequest:
    """Tests pour ImportRequest schema."""

    def test_import_request(self):
        profile_id = uuid.uuid4()
        data = {
            "profile_id": profile_id,
        }
        request = ImportRequest(**data)
        assert request.profile_id == profile_id


class TestExportRequest:
    """Tests pour ExportRequest schema."""

    def test_export_request(self):
        profile_id = uuid.uuid4()
        data = {
            "profile_id": profile_id,
        }
        request = ExportRequest(**data)
        assert request.profile_id == profile_id

    def test_export_with_filters(self):
        profile_id = uuid.uuid4()
        data = {
            "profile_id": profile_id,
            "filters": {"status": "active"},
        }
        request = ExportRequest(**data)
        assert request.filters["status"] == "active"
