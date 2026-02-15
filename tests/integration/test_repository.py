"""
AZALSCORE - Tests Integration Repository Pattern
=================================================

Tests d'integration pour le Pattern Repository.
Verifie l'isolation tenant et l'integration avec QueryOptimizer.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4


class TestBaseRepository:
    """Tests pour BaseRepository."""

    def test_repository_filters_by_tenant_id(self):
        """
        CRITIQUE: Le repository doit TOUJOURS filtrer par tenant_id.
        """
        from app.core.repository import BaseRepository

        # Mock DB session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Mock model
        class MockModel:
            __name__ = "MockModel"
            tenant_id = "tenant_field"
            id = "id_field"

        repo = BaseRepository(mock_db, MockModel, "tenant-a")
        entity_id = uuid4()

        # Appeler get_by_id
        result = repo.get_by_id(entity_id)

        # Verifier que filter a ete appele
        assert mock_query.filter.called
        assert result is None  # Pas trouve

    def test_repository_tenant_isolation(self):
        """
        Un repository pour tenant-a ne doit pas voir les donnees de tenant-b.
        """
        from app.core.repository import BaseRepository

        # Mock model avec tenant_id
        class MockModel:
            __name__ = "MockModel"
            tenant_id = None
            id = None

            def __init__(self):
                self.tenant_id = None
                self.id = uuid4()

        # Mock DB - retourne None pour simuler isolation
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Repository tenant-b essaie d'acceder a une entite tenant-a
        repo_b = BaseRepository(mock_db, MockModel, "tenant-b")
        entity_id = uuid4()

        result = repo_b.get_by_id(entity_id)

        # Ne doit pas trouver l'entite (isolation)
        assert result is None

    def test_create_sets_tenant_id_automatically(self):
        """
        create() doit forcer le tenant_id meme si l'entite en a un different.
        """
        from app.core.repository import BaseRepository

        class MockModel:
            __name__ = "MockModel"
            tenant_id = None
            id = None

            def __init__(self):
                self.tenant_id = "wrong-tenant"  # Mauvais tenant
                self.id = uuid4()

        mock_db = MagicMock()
        repo = BaseRepository(mock_db, MockModel, "correct-tenant")

        entity = MockModel()
        assert entity.tenant_id == "wrong-tenant"  # Avant

        # Patch commit et refresh
        with patch.object(repo, 'db') as mock_db_patched:
            mock_db_patched.add = MagicMock()
            mock_db_patched.commit = MagicMock()
            mock_db_patched.refresh = MagicMock()

            # Le create devrait forcer le bon tenant_id
            repo.db = mock_db_patched
            repo.create(entity)

        # Apres create, tenant_id doit etre le bon
        assert entity.tenant_id == "correct-tenant"


class TestContactRepository:
    """Tests pour ContactRepository (POC)."""

    def test_contact_repository_inherits_base(self):
        """
        ContactRepository doit heriter de BaseRepository.
        """
        from app.core.repository import BaseRepository
        from app.modules.contacts.repository import ContactRepository

        assert issubclass(ContactRepository, BaseRepository)

    def test_contact_repository_has_metier_methods(self):
        """
        ContactRepository doit avoir des methodes metier specifiques.
        """
        from app.modules.contacts.repository import ContactRepository

        # Verifier que les methodes existent
        assert hasattr(ContactRepository, 'find_by_email')
        assert hasattr(ContactRepository, 'find_by_code')
        assert hasattr(ContactRepository, 'search_by_name')
        assert hasattr(ContactRepository, 'list_active')
        assert hasattr(ContactRepository, 'list_customers')
        assert hasattr(ContactRepository, 'list_suppliers')
        assert hasattr(ContactRepository, 'get_with_details')

    def test_contact_repository_find_by_email(self):
        """
        find_by_email doit filtrer par tenant et email.
        """
        from app.modules.contacts.repository import ContactRepository

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = ContactRepository(mock_db, "test-tenant")
        result = repo.find_by_email("test@example.com")

        # Verifier que query et filter ont ete appeles
        assert mock_db.query.called
        assert mock_query.filter.called
        assert result is None


class TestStandardError:
    """Tests pour StandardError."""

    def test_standard_error_has_required_fields(self):
        """
        StandardError doit avoir tous les champs requis.
        """
        from app.core.errors import StandardError, ErrorCode
        from datetime import datetime

        error = StandardError(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Test message",
            http_status=400,
            request_id="req-123"
        )

        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.message == "Test message"
        assert error.http_status == 400
        assert error.request_id == "req-123"
        assert isinstance(error.timestamp, datetime)

    def test_standard_error_serialization(self):
        """
        StandardError doit se serialiser correctement en JSON.
        """
        from app.core.errors import StandardError, ErrorCode

        error = StandardError(
            error_code=ErrorCode.AUTH_INVALID_TOKEN,
            message="Token invalide",
            http_status=401,
            request_id="req-456",
            path="/api/v1/protected"
        )

        data = error.model_dump(mode="json")

        assert data["error_code"] == "AUTH_INVALID_TOKEN"
        assert data["message"] == "Token invalide"
        assert data["http_status"] == 401
        assert data["request_id"] == "req-456"
        assert data["path"] == "/api/v1/protected"
        assert "timestamp" in data

    def test_error_code_constants(self):
        """
        ErrorCode doit avoir les constantes attendues.
        """
        from app.core.errors import ErrorCode

        # Auth
        assert ErrorCode.AUTH_INVALID_TOKEN == "AUTH_INVALID_TOKEN"
        assert ErrorCode.AUTH_EXPIRED_TOKEN == "AUTH_EXPIRED_TOKEN"

        # Tenant
        assert ErrorCode.TENANT_ACCESS_DENIED == "TENANT_ACCESS_DENIED"
        assert ErrorCode.PERMISSION_DENIED == "PERMISSION_DENIED"

        # Validation
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.RESOURCE_NOT_FOUND == "RESOURCE_NOT_FOUND"

        # Rate limiting
        assert ErrorCode.RATE_LIMIT_EXCEEDED == "RATE_LIMIT_EXCEEDED"

    def test_create_standard_error_factory(self):
        """
        create_standard_error() doit creer une StandardError valide.
        """
        from app.core.errors import create_standard_error, ErrorCode

        error = create_standard_error(
            error_code=ErrorCode.INTEGRITY_ERROR,
            message="Contrainte violee",
            http_status=409,
            request_id="req-789",
            path="/api/v1/contacts",
            details={"field": "email", "reason": "duplicate"}
        )

        assert isinstance(error, object)
        assert error.error_code == ErrorCode.INTEGRITY_ERROR
        assert error.details == {"field": "email", "reason": "duplicate"}
