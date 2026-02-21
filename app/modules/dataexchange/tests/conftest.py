"""
AZALS - Module DataExchange - Test Configuration
=================================================
Fixtures et configuration communes pour les tests du module DataExchange.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dataexchange.models import (
    FileFormat,
    ExchangeType,
    ExchangeStatus,
    ConnectorType,
    ScheduleFrequency,
    TransformationType,
    FieldDataType,
    ValidationRuleType,
    ExchangeProfile,
    FieldMapping,
    ValidationRule,
    Transformation,
    FileConnector,
    ScheduledExchange,
    ExchangeJob,
    ExchangeLog,
    ExchangeError,
    LookupTable,
)


# ============== Session Fixtures ==============

@pytest.fixture
def mock_session():
    """Mock de session SQLAlchemy async."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


# ============== ID Fixtures ==============

@pytest.fixture
def tenant_id():
    """ID tenant pour les tests."""
    return uuid.uuid4()


@pytest.fixture
def user_id():
    """ID utilisateur pour les tests."""
    return uuid.uuid4()


@pytest.fixture
def profile_id():
    """ID profil pour les tests."""
    return uuid.uuid4()


@pytest.fixture
def connector_id():
    """ID connecteur pour les tests."""
    return uuid.uuid4()


@pytest.fixture
def job_id():
    """ID job pour les tests."""
    return uuid.uuid4()


@pytest.fixture
def schedule_id():
    """ID planification pour les tests."""
    return uuid.uuid4()


# ============== Model Fixtures ==============

@pytest.fixture
def sample_import_profile(tenant_id, user_id) -> ExchangeProfile:
    """Profil d'import exemple."""
    return ExchangeProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="IMP_CLIENTS",
        name="Import Clients",
        description="Import des clients depuis fichier CSV",
        exchange_type=ExchangeType.IMPORT,
        file_format=FileFormat.CSV,
        entity_type="client",
        file_encoding="utf-8",
        csv_delimiter=";",
        csv_quote_char='"',
        has_header=True,
        skip_rows=0,
        is_active=True,
        is_system=False,
        is_deleted=False,
        version=1,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )


@pytest.fixture
def sample_export_profile(tenant_id, user_id) -> ExchangeProfile:
    """Profil d'export exemple."""
    return ExchangeProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="EXP_FACTURES",
        name="Export Factures",
        description="Export des factures vers Excel",
        exchange_type=ExchangeType.EXPORT,
        file_format=FileFormat.EXCEL,
        entity_type="invoice",
        file_encoding="utf-8",
        is_active=True,
        is_system=False,
        is_deleted=False,
        version=1,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )


@pytest.fixture
def sample_field_mappings(tenant_id, profile_id) -> List[FieldMapping]:
    """Liste de mappings de champs."""
    return [
        FieldMapping(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            profile_id=profile_id,
            source_field="nom",
            target_field="name",
            data_type=FieldDataType.STRING,
            is_required=True,
            is_key=False,
            position=1,
        ),
        FieldMapping(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            profile_id=profile_id,
            source_field="email",
            target_field="email",
            data_type=FieldDataType.EMAIL,
            is_required=True,
            is_key=True,
            position=2,
        ),
        FieldMapping(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            profile_id=profile_id,
            source_field="telephone",
            target_field="phone",
            data_type=FieldDataType.STRING,
            is_required=False,
            is_key=False,
            position=3,
        ),
    ]


@pytest.fixture
def sample_validation_rules(tenant_id, profile_id) -> List[ValidationRule]:
    """Liste de regles de validation."""
    return [
        ValidationRule(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            profile_id=profile_id,
            field_name="email",
            rule_type=ValidationRuleType.REQUIRED,
            error_message="Email requis",
            stop_on_error=False,
            position=1,
        ),
        ValidationRule(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            profile_id=profile_id,
            field_name="email",
            rule_type=ValidationRuleType.REGEX,
            configuration={"pattern": r"^[^@]+@[^@]+\.[^@]+$"},
            error_message="Email invalide",
            stop_on_error=False,
            position=2,
        ),
    ]


@pytest.fixture
def sample_ftp_connector(tenant_id, user_id) -> FileConnector:
    """Connecteur FTP exemple."""
    return FileConnector(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="FTP_MAIN",
        name="FTP Principal",
        description="Serveur FTP principal",
        connector_type=ConnectorType.FTP,
        connection_params={
            "host": "ftp.example.com",
            "port": 21,
            "username": "user",
            "passive_mode": True,
        },
        base_path="/imports",
        is_active=True,
        is_deleted=False,
        version=1,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )


@pytest.fixture
def sample_s3_connector(tenant_id, user_id) -> FileConnector:
    """Connecteur S3 exemple."""
    return FileConnector(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="S3_BACKUP",
        name="S3 Backup",
        description="Bucket S3 pour sauvegardes",
        connector_type=ConnectorType.S3,
        connection_params={
            "bucket": "my-backup-bucket",
            "region": "eu-west-1",
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
        },
        base_path="/exports",
        is_active=True,
        is_deleted=False,
        version=1,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )


@pytest.fixture
def sample_daily_schedule(tenant_id, profile_id, connector_id, user_id) -> ScheduledExchange:
    """Planification quotidienne exemple."""
    return ScheduledExchange(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="DAILY_EXPORT",
        name="Export Quotidien",
        description="Export automatique chaque jour a 23h",
        profile_id=profile_id,
        connector_id=connector_id,
        frequency=ScheduleFrequency.DAILY,
        schedule_time="23:00",
        is_active=True,
        last_run_at=None,
        next_run_at=datetime.utcnow() + timedelta(days=1),
        is_deleted=False,
        version=1,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )


@pytest.fixture
def sample_pending_job(tenant_id, profile_id, user_id) -> ExchangeJob:
    """Job en attente exemple."""
    return ExchangeJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        profile_id=profile_id,
        status=ExchangeStatus.PENDING,
        file_name="clients.csv",
        file_size=10240,
        total_rows=0,
        processed_rows=0,
        success_count=0,
        error_count=0,
        warning_count=0,
        is_rolled_back=False,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )


@pytest.fixture
def sample_completed_job(tenant_id, profile_id, user_id) -> ExchangeJob:
    """Job termine exemple."""
    now = datetime.utcnow()
    return ExchangeJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        profile_id=profile_id,
        status=ExchangeStatus.COMPLETED,
        file_name="clients.csv",
        file_size=10240,
        total_rows=100,
        processed_rows=100,
        success_count=98,
        error_count=2,
        warning_count=5,
        started_at=now - timedelta(minutes=5),
        completed_at=now,
        is_rolled_back=False,
        rollback_data={"created_ids": [str(uuid.uuid4()) for _ in range(98)]},
        created_at=now - timedelta(minutes=6),
        created_by=user_id,
    )


@pytest.fixture
def sample_lookup_table(tenant_id, user_id) -> LookupTable:
    """Table de correspondance exemple."""
    return LookupTable(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="COUNTRY_CODES",
        name="Codes Pays",
        description="Table de correspondance des codes pays",
        entries={
            "FR": "France",
            "DE": "Allemagne",
            "ES": "Espagne",
            "IT": "Italie",
            "GB": "Royaume-Uni",
            "US": "Etats-Unis",
        },
        is_deleted=False,
        version=1,
        created_at=datetime.utcnow(),
        created_by=user_id,
    )


# ============== Data Fixtures ==============

@pytest.fixture
def sample_csv_content() -> str:
    """Contenu CSV pour les tests."""
    return """nom;email;telephone
Jean Dupont;jean@example.com;0123456789
Marie Martin;marie@example.com;0987654321
Pierre Durand;pierre@example.com;0567891234
Sophie Bernard;sophie@example.com;0678901234
"""


@pytest.fixture
def sample_json_data() -> List[Dict[str, Any]]:
    """Donnees JSON pour les tests."""
    return [
        {"nom": "Jean Dupont", "email": "jean@example.com", "telephone": "0123456789"},
        {"nom": "Marie Martin", "email": "marie@example.com", "telephone": "0987654321"},
        {"nom": "Pierre Durand", "email": "pierre@example.com", "telephone": "0567891234"},
    ]


@pytest.fixture
def sample_invalid_csv_content() -> str:
    """Contenu CSV invalide pour les tests."""
    return """nom;email;telephone
Jean Dupont;;0123456789
Marie Martin;invalid-email;0987654321
;pierre@example.com;
"""


# ============== Request Data Fixtures ==============

@pytest.fixture
def profile_create_data() -> Dict[str, Any]:
    """Donnees de creation de profil."""
    return {
        "code": "IMP_PRODUCTS",
        "name": "Import Produits",
        "description": "Import des produits",
        "exchange_type": "import",
        "file_format": "csv",
        "entity_type": "product",
        "file_encoding": "utf-8",
        "csv_delimiter": ";",
        "has_header": True,
    }


@pytest.fixture
def connector_create_data() -> Dict[str, Any]:
    """Donnees de creation de connecteur."""
    return {
        "code": "SFTP_BACKUP",
        "name": "SFTP Backup",
        "description": "Serveur SFTP de sauvegarde",
        "connector_type": "sftp",
        "connection_params": {
            "host": "sftp.example.com",
            "port": 22,
            "username": "backup_user",
        },
        "base_path": "/backups",
    }


@pytest.fixture
def schedule_create_data(profile_id, connector_id) -> Dict[str, Any]:
    """Donnees de creation de planification."""
    return {
        "code": "WEEKLY_REPORT",
        "name": "Rapport Hebdomadaire",
        "description": "Export hebdomadaire des rapports",
        "profile_id": str(profile_id),
        "connector_id": str(connector_id),
        "frequency": "weekly",
        "schedule_day": 1,  # Lundi
        "schedule_time": "06:00",
    }
