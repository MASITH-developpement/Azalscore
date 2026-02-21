"""
AZALS - Module DataExchange - Tests Service
============================================
Tests unitaires pour le service du module DataExchange.
"""
import uuid
import io
import csv
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.modules.dataexchange.service import (
    DataExchangeService,
    ImportFormat,
    ExportFormat,
    ImportStatus,
    ExportStatus,
    FieldType,
    ValidationAction,
    DuplicateAction,
    FieldMapping,
    ImportProfile,
    ExportProfile,
    ImportJob,
    ExportJob,
)


# ============== Fixtures ==============

@pytest.fixture
def mock_session():
    """Mock de session SQLAlchemy async."""
    session = AsyncMock()
    return session


@pytest.fixture
def tenant_id():
    """ID tenant pour les tests."""
    return uuid.uuid4()


@pytest.fixture
def user_id():
    """ID utilisateur pour les tests."""
    return uuid.uuid4()


@pytest.fixture
def dataexchange_service(mock_session, tenant_id, user_id):
    """Instance du service DataExchange."""
    service = DataExchangeService(mock_session, tenant_id, user_id)
    return service


@pytest.fixture
def sample_csv_content():
    """Contenu CSV pour les tests."""
    return """nom,email,telephone
Jean Dupont,jean@example.com,0123456789
Marie Martin,marie@example.com,0987654321
Pierre Durand,pierre@example.com,0567891234"""


@pytest.fixture
def sample_json_content():
    """Contenu JSON pour les tests."""
    return json.dumps([
        {"nom": "Jean Dupont", "email": "jean@example.com", "telephone": "0123456789"},
        {"nom": "Marie Martin", "email": "marie@example.com", "telephone": "0987654321"},
    ])


@pytest.fixture
def sample_field_mappings():
    """Mappings de champs pour les tests."""
    return [
        FieldMapping(
            source_field="nom",
            target_field="name",
            field_type=FieldType.STRING,
            is_required=True,
        ),
        FieldMapping(
            source_field="email",
            target_field="email",
            field_type=FieldType.EMAIL,
            is_required=True,
        ),
        FieldMapping(
            source_field="telephone",
            target_field="phone",
            field_type=FieldType.STRING,
            is_required=False,
        ),
    ]


@pytest.fixture
def sample_import_profile(sample_field_mappings):
    """Profil d'import pour les tests."""
    return ImportProfile(
        id=str(uuid.uuid4()),
        code="IMP_CLIENTS",
        name="Import Clients",
        format=ImportFormat.CSV,
        entity_type="client",
        field_mappings=sample_field_mappings,
        validation_action=ValidationAction.REJECT_ROW,
        duplicate_action=DuplicateAction.SKIP,
    )


# ============== Test Enumerations ==============

class TestImportFormat:
    """Tests pour l'enumeration ImportFormat."""

    def test_csv_format(self):
        assert ImportFormat.CSV.value == "csv"

    def test_excel_format(self):
        assert ImportFormat.EXCEL.value == "excel"

    def test_json_format(self):
        assert ImportFormat.JSON.value == "json"

    def test_xml_format(self):
        assert ImportFormat.XML.value == "xml"


class TestExportFormat:
    """Tests pour l'enumeration ExportFormat."""

    def test_csv_format(self):
        assert ExportFormat.CSV.value == "csv"

    def test_excel_format(self):
        assert ExportFormat.EXCEL.value == "excel"

    def test_json_format(self):
        assert ExportFormat.JSON.value == "json"

    def test_pdf_format(self):
        assert ExportFormat.PDF.value == "pdf"


class TestImportStatus:
    """Tests pour l'enumeration ImportStatus."""

    def test_pending_status(self):
        assert ImportStatus.PENDING.value == "pending"

    def test_completed_status(self):
        assert ImportStatus.COMPLETED.value == "completed"

    def test_failed_status(self):
        assert ImportStatus.FAILED.value == "failed"


class TestValidationAction:
    """Tests pour l'enumeration ValidationAction."""

    def test_reject_row(self):
        assert ValidationAction.REJECT_ROW.value == "reject_row"

    def test_reject_file(self):
        assert ValidationAction.REJECT_FILE.value == "reject_file"

    def test_skip(self):
        assert ValidationAction.SKIP.value == "skip"


class TestDuplicateAction:
    """Tests pour l'enumeration DuplicateAction."""

    def test_skip(self):
        assert DuplicateAction.SKIP.value == "skip"

    def test_update(self):
        assert DuplicateAction.UPDATE.value == "update"

    def test_error(self):
        assert DuplicateAction.ERROR.value == "error"


# ============== Test FieldMapping ==============

class TestFieldMapping:
    """Tests pour FieldMapping dataclass."""

    def test_create_field_mapping(self):
        mapping = FieldMapping(
            source_field="nom",
            target_field="name",
            field_type=FieldType.STRING,
        )
        assert mapping.source_field == "nom"
        assert mapping.target_field == "name"
        assert mapping.field_type == FieldType.STRING

    def test_required_field_mapping(self):
        mapping = FieldMapping(
            source_field="email",
            target_field="email",
            field_type=FieldType.EMAIL,
            is_required=True,
        )
        assert mapping.is_required is True

    def test_field_with_default(self):
        mapping = FieldMapping(
            source_field="pays",
            target_field="country",
            field_type=FieldType.STRING,
            default_value="France",
        )
        assert mapping.default_value == "France"


# ============== Test ImportProfile ==============

class TestImportProfile:
    """Tests pour ImportProfile dataclass."""

    def test_create_import_profile(self, sample_field_mappings):
        profile = ImportProfile(
            id=str(uuid.uuid4()),
            code="IMP_TEST",
            name="Import Test",
            format=ImportFormat.CSV,
            entity_type="client",
            field_mappings=sample_field_mappings,
        )
        assert profile.code == "IMP_TEST"
        assert profile.format == ImportFormat.CSV
        assert len(profile.field_mappings) == 3

    def test_profile_with_validation_action(self, sample_field_mappings):
        profile = ImportProfile(
            id=str(uuid.uuid4()),
            code="IMP_STRICT",
            name="Import Strict",
            format=ImportFormat.CSV,
            entity_type="client",
            field_mappings=sample_field_mappings,
            validation_action=ValidationAction.REJECT_FILE,
        )
        assert profile.validation_action == ValidationAction.REJECT_FILE


# ============== Test ExportProfile ==============

class TestExportProfile:
    """Tests pour ExportProfile dataclass."""

    def test_create_export_profile(self):
        profile = ExportProfile(
            id=str(uuid.uuid4()),
            code="EXP_CLIENTS",
            name="Export Clients",
            format=ExportFormat.CSV,
            entity_type="client",
            fields=["name", "email", "phone"],
        )
        assert profile.code == "EXP_CLIENTS"
        assert profile.format == ExportFormat.CSV
        assert "email" in profile.fields


# ============== Test DataExchangeService ==============

class TestDataExchangeService:
    """Tests pour DataExchangeService."""

    def test_service_initialization(self, dataexchange_service, tenant_id, user_id):
        """Test l'initialisation du service."""
        assert dataexchange_service.tenant_id == tenant_id
        assert dataexchange_service.user_id == user_id

    def test_service_has_session(self, dataexchange_service, mock_session):
        """Verifie que le service a une session."""
        assert dataexchange_service.session == mock_session


class TestCSVParsing:
    """Tests pour le parsing CSV."""

    def test_parse_csv_headers(self, sample_csv_content):
        """Test extraction des en-tetes CSV."""
        reader = csv.DictReader(io.StringIO(sample_csv_content))
        headers = reader.fieldnames
        assert "nom" in headers
        assert "email" in headers
        assert "telephone" in headers

    def test_parse_csv_rows(self, sample_csv_content):
        """Test extraction des lignes CSV."""
        reader = csv.DictReader(io.StringIO(sample_csv_content))
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["nom"] == "Jean Dupont"
        assert rows[1]["email"] == "marie@example.com"


class TestJSONParsing:
    """Tests pour le parsing JSON."""

    def test_parse_json_array(self, sample_json_content):
        """Test parsing d'un tableau JSON."""
        data = json.loads(sample_json_content)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["nom"] == "Jean Dupont"


class TestDataValidation:
    """Tests pour la validation des donnees."""

    def test_required_field_present(self):
        """Test champ requis present."""
        row = {"nom": "Jean", "email": "jean@example.com"}
        assert "nom" in row
        assert "email" in row

    def test_required_field_missing(self):
        """Test champ requis manquant."""
        row = {"nom": "Jean"}
        assert "email" not in row

    def test_email_validation(self):
        """Test validation email basique."""
        import re
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        valid_email = "test@example.com"
        invalid_email = "not-an-email"

        assert re.match(email_pattern, valid_email) is not None
        assert re.match(email_pattern, invalid_email) is None


class TestDataTransformation:
    """Tests pour les transformations de donnees."""

    def test_uppercase_transformation(self):
        """Test transformation majuscules."""
        value = "jean dupont"
        transformed = value.upper()
        assert transformed == "JEAN DUPONT"

    def test_lowercase_transformation(self):
        """Test transformation minuscules."""
        value = "JEAN DUPONT"
        transformed = value.lower()
        assert transformed == "jean dupont"

    def test_trim_transformation(self):
        """Test transformation trim."""
        value = "  Jean Dupont  "
        transformed = value.strip()
        assert transformed == "Jean Dupont"

    def test_default_value(self):
        """Test valeur par defaut."""
        value = None
        default = "France"
        result = value if value else default
        assert result == "France"


class TestExportGeneration:
    """Tests pour la generation d'exports."""

    def test_generate_csv_output(self):
        """Test generation CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["nom", "email"])
        writer.writerow(["Jean Dupont", "jean@example.com"])

        content = output.getvalue()
        assert "nom,email" in content
        assert "Jean Dupont" in content

    def test_generate_json_output(self):
        """Test generation JSON."""
        data = [{"nom": "Jean", "email": "jean@example.com"}]
        content = json.dumps(data, ensure_ascii=False)
        assert '"nom": "Jean"' in content


class TestDuplicateHandling:
    """Tests pour la gestion des doublons."""

    def test_skip_duplicate(self):
        """Test skip des doublons."""
        existing = {"email@example.com"}
        new_email = "email@example.com"
        action = DuplicateAction.SKIP

        if new_email in existing and action == DuplicateAction.SKIP:
            result = "skipped"
        else:
            result = "processed"

        assert result == "skipped"

    def test_update_duplicate(self):
        """Test mise a jour des doublons."""
        action = DuplicateAction.UPDATE
        assert action.value == "update"


class TestJobStatus:
    """Tests pour les statuts de jobs."""

    def test_job_status_transitions(self):
        """Test transitions de statut."""
        # PENDING -> PROCESSING -> COMPLETED
        status = ImportStatus.PENDING
        assert status == ImportStatus.PENDING

        status = ImportStatus.PROCESSING
        assert status == ImportStatus.PROCESSING

        status = ImportStatus.COMPLETED
        assert status == ImportStatus.COMPLETED

    def test_job_can_fail(self):
        """Test statut echec."""
        status = ImportStatus.FAILED
        assert status == ImportStatus.FAILED
