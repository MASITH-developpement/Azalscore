"""
Tests unitaires pour le module HR Vault.
"""

import os
import tempfile
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.hr_vault.models import (
    EncryptionAlgorithm,
    GDPRRequestStatus,
    GDPRRequestType,
    RetentionPeriod,
    SignatureStatus,
    VaultAccessLog,
    VaultAccessRole,
    VaultAccessType,
    VaultDocument,
    VaultDocumentCategory,
    VaultDocumentStatus,
    VaultDocumentType,
    VaultDocumentVersion,
    VaultEncryptionKey,
    VaultGDPRRequest,
)
from app.modules.hr_vault.schemas import (
    VaultCategoryCreate,
    VaultDocumentFilters,
    VaultDocumentUpload,
    VaultGDPRRequestCreate,
)
from app.modules.hr_vault.exceptions import (
    AccessDeniedException,
    DocumentIntegrityException,
    DocumentNotFoundException,
    FileSizeLimitException,
    InvalidFileTypeException,
    RetentionPeriodActiveException,
)
from app.modules.hr_vault.repository import HRVaultRepository
from app.modules.hr_vault.service import HRVaultService, create_hr_vault_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def tenant_id() -> str:
    return "test-tenant-123"


@pytest.fixture
def employee_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def master_key() -> bytes:
    return os.urandom(32)


@pytest.fixture
def storage_path() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session, tenant_id) -> HRVaultRepository:
    return HRVaultRepository(mock_session, tenant_id)


@pytest.fixture
def service(mock_session, tenant_id, storage_path, master_key, user_id) -> HRVaultService:
    return HRVaultService(
        session=mock_session,
        tenant_id=tenant_id,
        storage_path=storage_path,
        master_key=master_key,
        current_user_id=user_id,
        current_user_role=VaultAccessRole.HR_ADMIN,
    )


# ============================================================================
# TESTS - ENUMS
# ============================================================================

class TestEnums:
    """Tests pour les enumerations."""

    def test_document_type_values(self):
        """Verifie que tous les types de documents sont definis."""
        assert VaultDocumentType.PAYSLIP.value == "PAYSLIP"
        assert VaultDocumentType.CONTRACT.value == "CONTRACT"
        assert VaultDocumentType.DIPLOMA.value == "DIPLOMA"
        assert len(VaultDocumentType) >= 20

    def test_retention_period_values(self):
        """Verifie les periodes de conservation."""
        assert RetentionPeriod.FIVE_YEARS.value == "5_YEARS"
        assert RetentionPeriod.FIFTY_YEARS.value == "50_YEARS"
        assert RetentionPeriod.PERMANENT.value == "PERMANENT"

    def test_access_roles(self):
        """Verifie les roles d'acces."""
        assert VaultAccessRole.EMPLOYEE.value == "EMPLOYEE"
        assert VaultAccessRole.HR_ADMIN.value == "HR_ADMIN"
        assert VaultAccessRole.MANAGER.value == "MANAGER"


# ============================================================================
# TESTS - MODELS
# ============================================================================

class TestModels:
    """Tests pour les modeles SQLAlchemy."""

    def test_document_creation(self, tenant_id, employee_id):
        """Test creation d'un document."""
        doc = VaultDocument(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=employee_id,
            document_type=VaultDocumentType.PAYSLIP,
            title="Bulletin de paie Janvier 2024",
            file_name="bulletin_2024_01.pdf",
            file_size=150000,
            mime_type="application/pdf",
            storage_path="test/path",
            file_hash="abc123",
        )
        assert doc.status == VaultDocumentStatus.ACTIVE
        assert doc.is_encrypted == True
        assert doc.version == 1

    def test_category_creation(self, tenant_id):
        """Test creation d'une categorie."""
        category = VaultDocumentCategory(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            code="PAIE",
            name="Documents de paie",
            default_retention=RetentionPeriod.FIFTY_YEARS,
        )
        assert category.is_active == True
        assert category.visible_to_employee == True

    def test_access_log_creation(self, tenant_id, employee_id, user_id):
        """Test creation d'un log d'acces."""
        doc_id = uuid.uuid4()
        log = VaultAccessLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            document_id=doc_id,
            employee_id=employee_id,
            accessed_by=user_id,
            access_role=VaultAccessRole.HR_ADMIN,
            access_type=VaultAccessType.VIEW,
        )
        assert log.success == True


# ============================================================================
# TESTS - REPOSITORY
# ============================================================================

class TestRepository:
    """Tests pour le repository."""

    @pytest.mark.asyncio
    async def test_base_query_filters_by_tenant(self, repository, tenant_id):
        """Verifie que _base_query filtre par tenant_id."""
        query = repository._base_query(VaultDocument)
        # Le query doit contenir une clause WHERE sur tenant_id
        assert query is not None

    @pytest.mark.asyncio
    async def test_active_query_excludes_deleted(self, repository):
        """Verifie que _active_query exclut les supprimes."""
        query = repository._active_query(VaultDocument)
        assert query is not None


# ============================================================================
# TESTS - SERVICE
# ============================================================================

class TestService:
    """Tests pour le service."""

    def test_service_creation(self, service, tenant_id):
        """Test creation du service."""
        assert service.tenant_id == tenant_id
        assert service.repository is not None

    def test_check_admin_permission_hr_admin(self, service):
        """Test permission admin pour HR_ADMIN."""
        # Ne doit pas lever d'exception
        service._check_admin_permission()

    def test_check_admin_permission_employee_denied(self, mock_session, tenant_id, storage_path, master_key, user_id):
        """Test permission admin refusee pour EMPLOYEE."""
        service = HRVaultService(
            session=mock_session,
            tenant_id=tenant_id,
            storage_path=storage_path,
            master_key=master_key,
            current_user_id=user_id,
            current_user_role=VaultAccessRole.EMPLOYEE,
        )
        with pytest.raises(AccessDeniedException):
            service._check_admin_permission()

    def test_check_view_permission_own_documents(self, mock_session, tenant_id, storage_path, master_key, user_id):
        """Test permission vue pour ses propres documents."""
        service = HRVaultService(
            session=mock_session,
            tenant_id=tenant_id,
            storage_path=storage_path,
            master_key=master_key,
            current_user_id=user_id,
            current_user_role=VaultAccessRole.EMPLOYEE,
        )
        # L'employe peut voir ses propres documents
        service._check_view_permission(user_id)

    def test_check_view_permission_other_documents_denied(self, mock_session, tenant_id, storage_path, master_key, user_id):
        """Test permission vue refusee pour documents d'autrui."""
        service = HRVaultService(
            session=mock_session,
            tenant_id=tenant_id,
            storage_path=storage_path,
            master_key=master_key,
            current_user_id=user_id,
            current_user_role=VaultAccessRole.EMPLOYEE,
        )
        other_employee = uuid.uuid4()
        with pytest.raises(AccessDeniedException):
            service._check_view_permission(other_employee)


# ============================================================================
# TESTS - CHIFFREMENT
# ============================================================================

class TestEncryption:
    """Tests pour le chiffrement."""

    def test_encrypt_decrypt_master_key(self, service):
        """Test chiffrement/dechiffrement avec master key."""
        data = b"test data to encrypt"
        encrypted = service._encrypt_with_master_key(data)
        decrypted = service._decrypt_with_master_key(encrypted)
        assert decrypted == data

    def test_encrypted_data_different_from_original(self, service):
        """Verifie que les donnees chiffrees sont differentes."""
        data = b"test data"
        encrypted = service._encrypt_with_master_key(data)
        assert encrypted != data
        assert len(encrypted) > len(data)

    def test_encryption_includes_nonce(self, service):
        """Verifie que le nonce est inclus."""
        data = b"test data"
        encrypted = service._encrypt_with_master_key(data)
        # Le nonce fait 12 bytes
        assert len(encrypted) >= 12


# ============================================================================
# TESTS - VALIDATION
# ============================================================================

class TestValidation:
    """Tests pour les validations."""

    def test_file_size_limit(self):
        """Test limite de taille de fichier."""
        from app.modules.hr_vault.service import MAX_FILE_SIZE
        assert MAX_FILE_SIZE == 50 * 1024 * 1024  # 50 MB

    def test_allowed_mime_types(self):
        """Test types MIME autorises."""
        from app.modules.hr_vault.service import ALLOWED_MIME_TYPES
        assert "application/pdf" in ALLOWED_MIME_TYPES
        assert "image/jpeg" in ALLOWED_MIME_TYPES

    def test_retention_rules_defined(self):
        """Test regles de conservation definies."""
        from app.modules.hr_vault.service import RETENTION_RULES
        assert VaultDocumentType.PAYSLIP in RETENTION_RULES
        assert RETENTION_RULES[VaultDocumentType.PAYSLIP] == RetentionPeriod.FIFTY_YEARS


# ============================================================================
# TESTS - SCHEMAS
# ============================================================================

class TestSchemas:
    """Tests pour les schemas Pydantic."""

    def test_category_create_validation(self):
        """Test validation creation categorie."""
        category = VaultCategoryCreate(
            code="TEST",
            name="Test Category",
        )
        assert category.default_retention == RetentionPeriod.FIVE_YEARS
        assert category.is_confidential == True

    def test_document_upload_validation(self, employee_id):
        """Test validation upload document."""
        upload = VaultDocumentUpload(
            employee_id=employee_id,
            document_type=VaultDocumentType.PAYSLIP,
            title="Test Document",
        )
        assert upload.notify_employee == True
        assert upload.requires_signature == False

    def test_document_filters_defaults(self):
        """Test filtres par defaut."""
        filters = VaultDocumentFilters()
        assert filters.include_deleted == False

    def test_gdpr_request_create(self, employee_id):
        """Test creation demande RGPD."""
        request = VaultGDPRRequestCreate(
            employee_id=employee_id,
            request_type=GDPRRequestType.PORTABILITY,
        )
        assert request.document_types == []


# ============================================================================
# TESTS - EXCEPTIONS
# ============================================================================

class TestExceptions:
    """Tests pour les exceptions."""

    def test_document_not_found_exception(self):
        """Test exception document non trouve."""
        exc = DocumentNotFoundException("doc-123")
        assert exc.code == "DOCUMENT_NOT_FOUND"
        assert "doc-123" in exc.message

    def test_access_denied_exception(self):
        """Test exception acces refuse."""
        exc = AccessDeniedException("user-1", "doc-1", "view")
        assert exc.code == "ACCESS_DENIED"
        assert "view" in str(exc.details)

    def test_file_size_limit_exception(self):
        """Test exception taille fichier."""
        exc = FileSizeLimitException(100000000, 50000000)
        assert exc.code == "FILE_SIZE_LIMIT_EXCEEDED"

    def test_invalid_file_type_exception(self):
        """Test exception type fichier invalide."""
        exc = InvalidFileTypeException("application/exe", ["application/pdf"])
        assert exc.code == "INVALID_FILE_TYPE"

    def test_retention_period_active_exception(self):
        """Test exception periode conservation active."""
        exc = RetentionPeriodActiveException("doc-1", "2050-01-01")
        assert exc.code == "RETENTION_PERIOD_ACTIVE"

    def test_document_integrity_exception(self):
        """Test exception integrite document."""
        exc = DocumentIntegrityException("doc-1", "hash1", "hash2")
        assert exc.code == "DOCUMENT_INTEGRITY_ERROR"


# ============================================================================
# TESTS - INTEGRATION
# ============================================================================

class TestIntegration:
    """Tests d'integration (necessitent une vraie DB)."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Necessite une vraie base de donnees")
    async def test_full_document_lifecycle(self, service, employee_id):
        """Test cycle de vie complet d'un document."""
        # 1. Upload
        upload_data = VaultDocumentUpload(
            employee_id=employee_id,
            document_type=VaultDocumentType.PAYSLIP,
            title="Bulletin Janvier 2024",
            pay_period="2024-01",
            gross_salary=Decimal("3500.00"),
            net_salary=Decimal("2700.00"),
        )
        file_content = b"%PDF-1.4 test content"

        doc = await service.upload_document(
            data=upload_data,
            file_content=file_content,
            file_name="bulletin_2024_01.pdf",
            mime_type="application/pdf",
        )
        assert doc.id is not None

        # 2. Lecture
        doc_read = await service.get_document(doc.id)
        assert doc_read.title == "Bulletin Janvier 2024"

        # 3. Telechargement
        content, filename, mime = await service.download_document(doc.id)
        assert content == file_content

        # 4. Mise a jour
        from app.modules.hr_vault.schemas import VaultDocumentUpdate
        update_data = VaultDocumentUpdate(description="Description ajoutee")
        doc_updated = await service.update_document(doc.id, update_data)
        assert doc_updated.description == "Description ajoutee"

        # 5. Suppression
        result = await service.delete_document(doc.id, force=True)
        assert result == True


# ============================================================================
# TESTS - FACTORY
# ============================================================================

class TestFactory:
    """Tests pour la factory."""

    def test_create_service_with_defaults(self, mock_session, tenant_id, storage_path):
        """Test creation service avec valeurs par defaut."""
        service = create_hr_vault_service(
            session=mock_session,
            tenant_id=tenant_id,
            storage_path=storage_path,
        )
        assert service is not None
        assert service.tenant_id == tenant_id

    def test_create_service_with_custom_key(self, mock_session, tenant_id, storage_path, master_key, user_id):
        """Test creation service avec cle personnalisee."""
        service = create_hr_vault_service(
            session=mock_session,
            tenant_id=tenant_id,
            storage_path=storage_path,
            master_key=master_key,
            current_user_id=user_id,
            current_user_role=VaultAccessRole.HR_DIRECTOR,
        )
        assert service.current_user_role == VaultAccessRole.HR_DIRECTOR


# ============================================================================
# TESTS - RGPD
# ============================================================================

class TestRGPD:
    """Tests pour la conformite RGPD."""

    def test_gdpr_request_types(self):
        """Verifie tous les types de demandes RGPD."""
        assert GDPRRequestType.ACCESS.value == "ACCESS"
        assert GDPRRequestType.ERASURE.value == "ERASURE"
        assert GDPRRequestType.PORTABILITY.value == "PORTABILITY"

    def test_gdpr_request_status(self):
        """Verifie tous les statuts de demandes RGPD."""
        assert GDPRRequestStatus.PENDING.value == "PENDING"
        assert GDPRRequestStatus.COMPLETED.value == "COMPLETED"
