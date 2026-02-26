"""
AZALS MODULE - Documents (GED) - Tests Service
===============================================

Tests unitaires pour le service GED.
"""

import io
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.modules.documents.models import (
    AccessLevel,
    Document,
    DocumentStatus,
    DocumentType,
    FileCategory,
    Folder,
    LinkEntityType,
    RetentionPolicy,
    ShareType,
)
from app.modules.documents.ged_service import GEDService, get_ged_service
from app.modules.documents.schemas import (
    CommentCreate,
    DocumentLinkCreate,
    DocumentUpdate,
    FolderCreate,
    FolderUpdate,
    SearchQuery,
    ShareCreate,
    TagCreate,
    CategoryCreate,
)
from app.modules.documents.exceptions import (
    DocumentNotFoundError,
    DocumentLockedError,
    FolderNotFoundError,
    FolderAlreadyExistsError,
    FolderNotEmptyError,
    FolderSystemError,
    StorageQuotaExceededError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def db_engine():
    """Cree un moteur SQLite en memoire pour les tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Cree une session de base de donnees."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def temp_storage():
    """Cree un repertoire temporaire pour le stockage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def ged_service(db_session, temp_storage):
    """Cree un service GED pour les tests."""
    tenant_id = "test_tenant"
    user_id = uuid4()
    return get_ged_service(
        db=db_session,
        tenant_id=tenant_id,
        user_id=user_id,
        user_email="test@example.com",
        storage_path=temp_storage
    )


@pytest.fixture
def sample_pdf_content():
    """Contenu PDF factice."""
    return b"%PDF-1.4 Sample PDF content for testing"


@pytest.fixture
def sample_text_content():
    """Contenu texte factice."""
    return b"This is a sample text file for testing the GED service."


# =============================================================================
# TESTS DOSSIERS
# =============================================================================

class TestFolders:
    """Tests pour la gestion des dossiers."""

    def test_create_folder_root(self, ged_service):
        """Test creation d'un dossier racine."""
        data = FolderCreate(
            name="Documents",
            description="Dossier principal"
        )

        folder = ged_service.create_folder(data)

        assert folder is not None
        assert folder.name == "Documents"
        assert folder.path == "/Documents"
        assert folder.level == 0
        assert folder.parent_id is None

    def test_create_subfolder(self, ged_service):
        """Test creation d'un sous-dossier."""
        # Creer dossier parent
        parent_data = FolderCreate(name="Root")
        parent = ged_service.create_folder(parent_data)

        # Creer sous-dossier
        child_data = FolderCreate(
            name="Subfolder",
            parent_id=parent.id
        )
        child = ged_service.create_folder(child_data)

        assert child is not None
        assert child.parent_id == parent.id
        assert child.path == "/Root/Subfolder"
        assert child.level == 1

    def test_create_folder_duplicate_name(self, ged_service):
        """Test erreur si nom de dossier duplique."""
        data = FolderCreate(name="Test")
        ged_service.create_folder(data)

        with pytest.raises(FolderAlreadyExistsError):
            ged_service.create_folder(data)

    def test_update_folder(self, ged_service):
        """Test mise a jour d'un dossier."""
        data = FolderCreate(name="Original")
        folder = ged_service.create_folder(data)

        update_data = FolderUpdate(
            name="Updated",
            description="New description"
        )
        updated = ged_service.update_folder(folder.id, update_data)

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.description == "New description"

    def test_delete_folder_empty(self, ged_service):
        """Test suppression d'un dossier vide."""
        data = FolderCreate(name="ToDelete")
        folder = ged_service.create_folder(data)

        result = ged_service.delete_folder(folder.id)

        assert result is True
        assert ged_service.get_folder(folder.id) is None

    def test_delete_folder_not_empty(self, ged_service, sample_text_content):
        """Test erreur suppression dossier non vide."""
        folder_data = FolderCreate(name="Parent")
        folder = ged_service.create_folder(folder_data)

        # Ajouter un document
        ged_service.upload_document(
            file_content=sample_text_content,
            filename="test.txt",
            folder_id=folder.id
        )

        with pytest.raises(FolderNotEmptyError):
            ged_service.delete_folder(folder.id)

    def test_delete_folder_force(self, ged_service, sample_text_content):
        """Test suppression forcee d'un dossier non vide."""
        folder_data = FolderCreate(name="Parent")
        folder = ged_service.create_folder(folder_data)

        # Ajouter un document
        ged_service.upload_document(
            file_content=sample_text_content,
            filename="test.txt",
            folder_id=folder.id
        )

        # Supprimer avec force
        result = ged_service.delete_folder(folder.id, force=True)
        assert result is True

    def test_list_folders(self, ged_service):
        """Test listage des dossiers."""
        ged_service.create_folder(FolderCreate(name="Folder1"))
        ged_service.create_folder(FolderCreate(name="Folder2"))
        ged_service.create_folder(FolderCreate(name="Folder3"))

        folders = ged_service.list_folders()

        assert len(folders) == 3


# =============================================================================
# TESTS DOCUMENTS
# =============================================================================

class TestDocuments:
    """Tests pour la gestion des documents."""

    def test_upload_document(self, ged_service, sample_pdf_content):
        """Test upload d'un document."""
        result = ged_service.upload_document(
            file_content=sample_pdf_content,
            filename="document.pdf",
            title="Mon Document",
            description="Description test"
        )

        assert result is not None
        assert result.name == "document.pdf"
        assert result.code.startswith("DOC-")
        assert result.file_size == len(sample_pdf_content)

    def test_upload_document_to_folder(self, ged_service, sample_text_content):
        """Test upload dans un dossier."""
        folder = ged_service.create_folder(FolderCreate(name="Uploads"))

        result = ged_service.upload_document(
            file_content=sample_text_content,
            filename="file.txt",
            folder_id=folder.id
        )

        assert result is not None
        # Verifier que le document est dans le dossier
        docs, _ = ged_service.list_documents(folder_id=folder.id)
        assert len(docs) == 1

    def test_upload_with_tags(self, ged_service, sample_text_content):
        """Test upload avec tags."""
        result = ged_service.upload_document(
            file_content=sample_text_content,
            filename="tagged.txt",
            tags=["important", "urgent"]
        )

        doc = ged_service.get_document(result.document_id)
        assert "important" in doc.tags
        assert "urgent" in doc.tags

    def test_get_document(self, ged_service, sample_text_content):
        """Test recuperation d'un document."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="test.txt"
        )

        doc = ged_service.get_document(upload.document_id)

        assert doc is not None
        assert doc.id == upload.document_id
        assert doc.name == "test.txt"

    def test_get_document_not_found(self, ged_service):
        """Test document non trouve."""
        doc = ged_service.get_document(uuid4())
        assert doc is None

    def test_update_document(self, ged_service, sample_text_content):
        """Test mise a jour d'un document."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="original.txt"
        )

        update_data = DocumentUpdate(
            title="New Title",
            description="New Description"
        )
        updated = ged_service.update_document(upload.document_id, update_data)

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.description == "New Description"

    def test_delete_document_soft(self, ged_service, sample_text_content):
        """Test soft delete d'un document."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="to_delete.txt"
        )

        result = ged_service.delete_document(upload.document_id)

        assert result is True
        # Document non visible dans liste normale
        doc = ged_service.get_document(upload.document_id)
        assert doc is None

    def test_restore_document(self, ged_service, sample_text_content):
        """Test restauration d'un document supprime."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="to_restore.txt"
        )

        ged_service.delete_document(upload.document_id)
        restored = ged_service.restore_document(upload.document_id)

        assert restored is not None
        assert restored.status == DocumentStatus.ACTIVE


# =============================================================================
# TESTS TELECHARGEMENT
# =============================================================================

class TestDownload:
    """Tests pour le telechargement."""

    def test_download_document(self, ged_service, sample_text_content):
        """Test telechargement d'un document."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="download.txt"
        )

        content, filename, mime_type = ged_service.download_document(upload.document_id)

        assert content == sample_text_content
        assert filename == "download.txt"
        assert mime_type == "text/plain"

    def test_download_not_found(self, ged_service):
        """Test telechargement document inexistant."""
        with pytest.raises(DocumentNotFoundError):
            ged_service.download_document(uuid4())


# =============================================================================
# TESTS VERSIONING
# =============================================================================

class TestVersioning:
    """Tests pour le versioning."""

    def test_upload_new_version(self, ged_service, sample_text_content):
        """Test upload d'une nouvelle version."""
        # Version initiale
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="versioned.txt"
        )

        # Nouvelle version
        new_content = b"Updated content for version 2"
        version = ged_service.upload_new_version(
            document_id=upload.document_id,
            file_content=new_content,
            change_summary="Version 2 update",
            change_type="MINOR"
        )

        assert version is not None
        assert version.version_number == 2

        # Verifier que le document a la nouvelle version
        doc = ged_service.get_document(upload.document_id)
        assert doc.current_version == 2

    def test_get_versions(self, ged_service, sample_text_content):
        """Test liste des versions."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="multi-version.txt"
        )

        # Ajouter 2 versions
        ged_service.upload_new_version(upload.document_id, b"V2")
        ged_service.upload_new_version(upload.document_id, b"V3")

        versions, total = ged_service.get_versions(upload.document_id)

        assert total == 3
        assert len(versions) == 3

    def test_download_specific_version(self, ged_service, sample_text_content):
        """Test telechargement d'une version specifique."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="v1.txt"
        )

        new_content = b"Version 2 content"
        ged_service.upload_new_version(upload.document_id, new_content)

        # Telecharger version 1
        content, _, _ = ged_service.download_document(upload.document_id, version=1)
        assert content == sample_text_content

        # Telecharger version 2
        content, _, _ = ged_service.download_document(upload.document_id, version=2)
        assert content == new_content


# =============================================================================
# TESTS VERROUILLAGE
# =============================================================================

class TestLocking:
    """Tests pour le verrouillage."""

    def test_lock_document(self, ged_service, sample_text_content):
        """Test verrouillage d'un document."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="lockable.txt"
        )

        locked = ged_service.lock_document(
            upload.document_id,
            reason="En cours d'edition"
        )

        assert locked.is_locked is True
        assert locked.lock_reason == "En cours d'edition"

    def test_unlock_document(self, ged_service, sample_text_content):
        """Test deverrouillage d'un document."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="lockable.txt"
        )

        ged_service.lock_document(upload.document_id)
        unlocked = ged_service.unlock_document(upload.document_id)

        assert unlocked.is_locked is False

    def test_update_locked_document_by_other(self, ged_service, sample_text_content):
        """Test erreur modification document verrouille par autre utilisateur."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="locked.txt"
        )

        ged_service.lock_document(upload.document_id)

        # Tenter de modifier avec un autre user_id
        with pytest.raises(DocumentLockedError):
            ged_service.update_document(
                upload.document_id,
                DocumentUpdate(title="New Title"),
                user_id=uuid4()  # Autre utilisateur
            )


# =============================================================================
# TESTS PARTAGE
# =============================================================================

class TestSharing:
    """Tests pour le partage."""

    def test_create_share_user(self, ged_service, sample_text_content):
        """Test partage avec un utilisateur."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="shared.txt"
        )

        share_data = ShareCreate(
            share_type=ShareType.USER,
            user_id=uuid4(),
            access_level=AccessLevel.VIEW
        )

        share = ged_service.create_share(upload.document_id, share_data)

        assert share is not None
        assert share.share_type == ShareType.USER
        assert share.access_level == AccessLevel.VIEW

    def test_create_share_public_link(self, ged_service, sample_text_content):
        """Test creation d'un lien de partage public."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="public.txt"
        )

        share_data = ShareCreate(
            share_type=ShareType.PUBLIC,
            generate_link=True,
            access_level=AccessLevel.VIEW
        )

        share = ged_service.create_share(upload.document_id, share_data)

        assert share is not None
        assert share.share_link is not None

    def test_revoke_share(self, ged_service, sample_text_content):
        """Test revocation d'un partage."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="revoke.txt"
        )

        share_data = ShareCreate(
            share_type=ShareType.USER,
            user_id=uuid4()
        )
        share = ged_service.create_share(upload.document_id, share_data)

        result = ged_service.revoke_share(share.id)
        assert result is True


# =============================================================================
# TESTS LIENS ENTITES
# =============================================================================

class TestEntityLinks:
    """Tests pour les liens avec entites."""

    def test_link_to_invoice(self, ged_service, sample_text_content):
        """Test lien avec une facture."""
        upload = ged_service.upload_document(
            file_content=sample_text_content,
            filename="invoice_attachment.pdf"
        )

        link_data = DocumentLinkCreate(
            entity_type=LinkEntityType.INVOICE,
            entity_id=uuid4(),
            entity_code="INV-2024-0001",
            is_primary=True
        )

        link = ged_service.link_to_entity(upload.document_id, link_data)

        assert link is not None
        assert link.entity_type == LinkEntityType.INVOICE
        assert link.is_primary is True

    def test_get_entity_documents(self, ged_service, sample_text_content):
        """Test recuperation des documents d'une entite."""
        entity_id = uuid4()

        # Creer plusieurs documents lies
        for i in range(3):
            upload = ged_service.upload_document(
                file_content=sample_text_content,
                filename=f"attachment_{i}.txt"
            )
            ged_service.link_to_entity(
                upload.document_id,
                DocumentLinkCreate(
                    entity_type=LinkEntityType.CONTRACT,
                    entity_id=entity_id
                )
            )

        docs = ged_service.get_entity_documents(LinkEntityType.CONTRACT, entity_id)
        assert len(docs) == 3


# =============================================================================
# TESTS RECHERCHE
# =============================================================================

class TestSearch:
    """Tests pour la recherche."""

    def test_search_by_name(self, ged_service, sample_text_content):
        """Test recherche par nom."""
        ged_service.upload_document(sample_text_content, "report_2024.pdf")
        ged_service.upload_document(sample_text_content, "invoice_2024.pdf")
        ged_service.upload_document(sample_text_content, "contract.pdf")

        query = SearchQuery(query="report")
        results = ged_service.search(query)

        assert results.total >= 1
        assert any("report" in r.document.name.lower() for r in results.items)

    def test_search_with_filters(self, ged_service, sample_text_content):
        """Test recherche avec filtres."""
        ged_service.upload_document(
            sample_text_content,
            "important.txt",
            tags=["urgent"]
        )
        ged_service.upload_document(sample_text_content, "normal.txt")

        query = SearchQuery(query="important", tags=["urgent"])
        results = ged_service.search(query)

        assert results.total >= 1


# =============================================================================
# TESTS COMMENTAIRES
# =============================================================================

class TestComments:
    """Tests pour les commentaires."""

    def test_add_comment(self, ged_service, sample_text_content):
        """Test ajout d'un commentaire."""
        upload = ged_service.upload_document(sample_text_content, "commented.txt")

        comment_data = CommentCreate(content="Ceci est un commentaire")
        comment = ged_service.add_comment(upload.document_id, comment_data)

        assert comment is not None
        assert comment.content == "Ceci est un commentaire"

    def test_get_comments(self, ged_service, sample_text_content):
        """Test liste des commentaires."""
        upload = ged_service.upload_document(sample_text_content, "multi_comment.txt")

        ged_service.add_comment(upload.document_id, CommentCreate(content="Comment 1"))
        ged_service.add_comment(upload.document_id, CommentCreate(content="Comment 2"))

        comments = ged_service.get_comments(upload.document_id)
        assert len(comments) == 2


# =============================================================================
# TESTS TAGS ET CATEGORIES
# =============================================================================

class TestTagsAndCategories:
    """Tests pour les tags et categories."""

    def test_create_tag(self, ged_service):
        """Test creation d'un tag."""
        tag_data = TagCreate(
            name="Important",
            color="#FF0000"
        )
        tag = ged_service.create_tag(tag_data)

        assert tag is not None
        assert tag.name == "Important"
        assert tag.slug == "important"

    def test_create_category(self, ged_service):
        """Test creation d'une categorie."""
        cat_data = CategoryCreate(
            code="LEGAL",
            name="Documents Legaux",
            default_retention=RetentionPolicy.LEGAL
        )
        category = ged_service.create_category(cat_data)

        assert category is not None
        assert category.code == "LEGAL"
        assert category.default_retention == RetentionPolicy.LEGAL


# =============================================================================
# TESTS OPERATIONS EN LOT
# =============================================================================

class TestBatchOperations:
    """Tests pour les operations en lot."""

    def test_batch_move(self, ged_service, sample_text_content):
        """Test deplacement en lot."""
        folder = ged_service.create_folder(FolderCreate(name="Target"))

        doc_ids = []
        for i in range(3):
            upload = ged_service.upload_document(
                sample_text_content,
                f"batch_{i}.txt"
            )
            doc_ids.append(upload.document_id)

        result = ged_service.batch_move(doc_ids, folder.id)

        assert result.success_count == 3
        assert result.failed_count == 0

    def test_batch_delete(self, ged_service, sample_text_content):
        """Test suppression en lot."""
        doc_ids = []
        for i in range(3):
            upload = ged_service.upload_document(
                sample_text_content,
                f"delete_{i}.txt"
            )
            doc_ids.append(upload.document_id)

        result = ged_service.batch_delete(doc_ids)

        assert result.success_count == 3

    def test_batch_tag(self, ged_service, sample_text_content):
        """Test ajout de tags en lot."""
        doc_ids = []
        for i in range(3):
            upload = ged_service.upload_document(
                sample_text_content,
                f"tag_{i}.txt"
            )
            doc_ids.append(upload.document_id)

        result = ged_service.batch_tag(doc_ids, ["batch", "tagged"])

        assert result.success_count == 3

        # Verifier les tags
        for doc_id in doc_ids:
            doc = ged_service.get_document(doc_id)
            assert "batch" in doc.tags


# =============================================================================
# TESTS STATISTIQUES
# =============================================================================

class TestStatistics:
    """Tests pour les statistiques."""

    def test_get_storage_stats(self, ged_service, sample_text_content):
        """Test statistiques de stockage."""
        # Creer quelques documents
        ged_service.upload_document(sample_text_content, "stat1.txt")
        ged_service.upload_document(sample_text_content, "stat2.txt")

        stats = ged_service.get_storage_stats()

        assert stats.total_documents >= 2
        assert stats.total_size > 0


# =============================================================================
# TESTS AUDIT
# =============================================================================

class TestAudit:
    """Tests pour l'audit."""

    def test_audit_trail(self, ged_service, sample_text_content):
        """Test historique d'audit."""
        upload = ged_service.upload_document(sample_text_content, "audited.txt")

        # Effectuer quelques actions
        ged_service.get_document(upload.document_id)
        ged_service.update_document(
            upload.document_id,
            DocumentUpdate(title="Updated")
        )

        history, total = ged_service.get_audit_history(upload.document_id)

        assert total >= 2  # Au moins CREATE et UPDATE
