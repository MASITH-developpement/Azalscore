"""
AZALS MODULE - Documents (GED) - Repository
============================================

Repository specialise pour les documents avec isolation tenant.
Utilise BaseRepository avec methodes metier specifiques.
"""
from __future__ import annotations


import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.repository import BaseRepository

from .models import (
    AccessLevel,
    AuditAction,
    Document,
    DocumentAudit,
    DocumentCategory,
    DocumentComment,
    DocumentLink,
    DocumentSequence,
    DocumentShare,
    DocumentStatus,
    DocumentTag,
    DocumentType,
    DocumentVersion,
    FileCategory,
    Folder,
    FolderPermission,
    LinkEntityType,
    RetentionPolicy,
    ShareType,
    StorageConfig,
)

logger = logging.getLogger(__name__)


# =============================================================================
# REPOSITORY DOSSIER
# =============================================================================

class FolderRepository(BaseRepository[Folder]):
    """Repository pour les dossiers."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, Folder, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(Folder).filter(
            Folder.tenant_id == self.tenant_id,
            Folder.deleted_at.is_(None)
        )

    def find_by_path(self, path: str) -> Optional[Folder]:
        """Trouve un dossier par son chemin."""
        return self._base_query().filter(Folder.path == path).first()

    def find_by_name_in_parent(
        self,
        name: str,
        parent_id: Optional[UUID] = None
    ) -> Optional[Folder]:
        """Trouve un dossier par nom dans un parent."""
        query = self._base_query().filter(Folder.name == name)
        if parent_id:
            query = query.filter(Folder.parent_id == parent_id)
        else:
            query = query.filter(Folder.parent_id.is_(None))
        return query.first()

    def get_children(
        self,
        parent_id: Optional[UUID] = None,
        include_deleted: bool = False
    ) -> List[Folder]:
        """Liste les sous-dossiers d'un dossier."""
        query = self.db.query(Folder).filter(
            Folder.tenant_id == self.tenant_id
        )

        if not include_deleted:
            query = query.filter(Folder.deleted_at.is_(None))

        if parent_id:
            query = query.filter(Folder.parent_id == parent_id)
        else:
            query = query.filter(Folder.parent_id.is_(None))

        return query.order_by(Folder.name).all()

    def get_tree(self, root_id: Optional[UUID] = None) -> List[Folder]:
        """Recupere l'arbre complet des dossiers."""
        query = self._base_query()

        if root_id:
            root = self.get_by_id(root_id)
            if root:
                query = query.filter(Folder.path.startswith(root.path))

        return query.order_by(Folder.path).all()

    def get_ancestors(self, folder_id: UUID) -> List[Folder]:
        """Recupere tous les parents d'un dossier."""
        folder = self.get_by_id(folder_id)
        if not folder:
            return []

        # Parser le path pour extraire les IDs parents
        path_parts = folder.path.strip('/').split('/')
        if len(path_parts) <= 1:
            return []

        ancestors = []
        current_path = ""
        for part in path_parts[:-1]:
            current_path = f"{current_path}/{part}" if current_path else f"/{part}"
            ancestor = self.find_by_path(current_path)
            if ancestor:
                ancestors.append(ancestor)

        return ancestors

    def get_descendants_count(self, folder_id: UUID) -> Tuple[int, int]:
        """Compte les documents et sous-dossiers descendants."""
        folder = self.get_by_id(folder_id)
        if not folder:
            return 0, 0

        # Sous-dossiers
        subfolder_count = self._base_query().filter(
            Folder.path.startswith(folder.path + "/")
        ).count()

        # Documents
        document_count = self.db.query(Document).filter(
            Document.tenant_id == self.tenant_id,
            Document.deleted_at.is_(None),
            Document.folder_id.in_(
                self._base_query().filter(
                    or_(
                        Folder.id == folder_id,
                        Folder.path.startswith(folder.path + "/")
                    )
                ).with_entities(Folder.id)
            )
        ).count()

        return document_count, subfolder_count

    def update_path_recursive(
        self,
        folder_id: UUID,
        new_parent_path: str
    ) -> int:
        """Met a jour les chemins de tous les descendants."""
        folder = self.get_by_id(folder_id)
        if not folder:
            return 0

        old_path = folder.path
        new_path = f"{new_parent_path}/{folder.name}"

        # Mettre a jour ce dossier
        folder.path = new_path
        folder.level = new_path.count('/') - 1

        # Mettre a jour tous les descendants
        updated = self.db.query(Folder).filter(
            Folder.tenant_id == self.tenant_id,
            Folder.path.startswith(old_path + "/")
        ).update(
            {
                Folder.path: func.replace(Folder.path, old_path, new_path),
                Folder.level: func.length(func.replace(Folder.path, old_path, new_path))
                              - func.length(func.replace(func.replace(Folder.path, old_path, new_path), '/', ''))
                              - 1
            },
            synchronize_session=False
        )

        self.db.commit()
        return updated + 1

    def update_stats(self, folder_id: UUID) -> None:
        """Met a jour les statistiques d'un dossier."""
        folder = self.get_by_id(folder_id)
        if not folder:
            return

        # Documents directs
        folder.document_count = self.db.query(Document).filter(
            Document.tenant_id == self.tenant_id,
            Document.folder_id == folder_id,
            Document.deleted_at.is_(None)
        ).count()

        # Sous-dossiers directs
        folder.subfolder_count = self._base_query().filter(
            Folder.parent_id == folder_id
        ).count()

        # Taille totale
        size_result = self.db.query(func.sum(Document.file_size)).filter(
            Document.tenant_id == self.tenant_id,
            Document.folder_id == folder_id,
            Document.deleted_at.is_(None)
        ).scalar()
        folder.total_size = size_result or 0

        self.db.commit()


# =============================================================================
# REPOSITORY DOCUMENT
# =============================================================================

class DocumentRepository(BaseRepository[Document]):
    """Repository pour les documents."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, Document, tenant_id)

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        return self.db.query(Document).filter(
            Document.tenant_id == self.tenant_id,
            Document.deleted_at.is_(None)
        )

    def find_by_code(self, code: str) -> Optional[Document]:
        """Trouve un document par son code."""
        return self._base_query().filter(Document.code == code).first()

    def find_by_checksum(self, checksum: str) -> Optional[Document]:
        """Trouve un document par son checksum (detection doublons)."""
        return self._base_query().filter(Document.checksum == checksum).first()

    def find_by_name_in_folder(
        self,
        name: str,
        folder_id: Optional[UUID] = None
    ) -> Optional[Document]:
        """Trouve un document par nom dans un dossier."""
        query = self._base_query().filter(Document.name == name)
        if folder_id:
            query = query.filter(Document.folder_id == folder_id)
        else:
            query = query.filter(Document.folder_id.is_(None))
        return query.first()

    def list_by_folder(
        self,
        folder_id: Optional[UUID] = None,
        include_subfolders: bool = False,
        skip: int = 0,
        limit: int = 50,
        status: Optional[DocumentStatus] = None,
        category: Optional[FileCategory] = None,
        order_by: str = "name"
    ) -> Tuple[List[Document], int]:
        """Liste les documents d'un dossier."""
        query = self._base_query()

        if include_subfolders and folder_id:
            # Recuperer tous les sous-dossiers
            folder_ids = [folder_id]
            subfolders = self.db.query(Folder.id).filter(
                Folder.tenant_id == self.tenant_id,
                Folder.deleted_at.is_(None),
                Folder.path.startswith(
                    self.db.query(Folder.path).filter(
                        Folder.id == folder_id
                    ).scalar() + "/"
                )
            ).all()
            folder_ids.extend([f.id for f in subfolders])
            query = query.filter(Document.folder_id.in_(folder_ids))
        elif folder_id:
            query = query.filter(Document.folder_id == folder_id)
        else:
            query = query.filter(Document.folder_id.is_(None))

        if status:
            query = query.filter(Document.status == status)

        if category:
            query = query.filter(Document.category == category)

        total = query.count()

        # Tri
        if hasattr(Document, order_by):
            query = query.order_by(getattr(Document, order_by))

        items = query.offset(skip).limit(limit).all()
        return items, total

    def list_by_entity(
        self,
        entity_type: LinkEntityType,
        entity_id: UUID
    ) -> List[Document]:
        """Liste les documents lies a une entite."""
        return self._base_query().filter(
            Document.id.in_(
                self.db.query(DocumentLink.document_id).filter(
                    DocumentLink.tenant_id == self.tenant_id,
                    DocumentLink.entity_type == entity_type,
                    DocumentLink.entity_id == entity_id
                )
            )
        ).all()

    def list_by_tags(
        self,
        tags: List[str],
        match_all: bool = False
    ) -> List[Document]:
        """Liste les documents par tags."""
        query = self._base_query()

        if match_all:
            for tag in tags:
                query = query.filter(Document.tags.contains([tag]))
        else:
            query = query.filter(Document.tags.overlap(tags))

        return query.all()

    def search(
        self,
        query_text: str,
        folder_id: Optional[UUID] = None,
        include_content: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Document], int]:
        """Recherche full-text dans les documents."""
        query = self._base_query()

        # Recherche dans nom, titre, description
        search_term = f"%{query_text}%"
        search_conditions = [
            Document.name.ilike(search_term),
            Document.title.ilike(search_term),
            Document.description.ilike(search_term),
            Document.code.ilike(search_term)
        ]

        if include_content:
            search_conditions.append(Document.content_text.ilike(search_term))

        query = query.filter(or_(*search_conditions))

        # Filtres additionnels
        if folder_id:
            query = query.filter(Document.folder_id == folder_id)

        if filters:
            if filters.get("status"):
                query = query.filter(Document.status == filters["status"])
            if filters.get("category"):
                query = query.filter(Document.category == filters["category"])
            if filters.get("document_type"):
                query = query.filter(Document.document_type == filters["document_type"])
            if filters.get("created_from"):
                query = query.filter(Document.created_at >= filters["created_from"])
            if filters.get("created_to"):
                query = query.filter(Document.created_at <= filters["created_to"])
            if filters.get("created_by"):
                query = query.filter(Document.created_by == filters["created_by"])
            if filters.get("tags"):
                query = query.filter(Document.tags.overlap(filters["tags"]))
            if filters.get("extensions"):
                query = query.filter(Document.file_extension.in_(filters["extensions"]))
            if filters.get("min_size"):
                query = query.filter(Document.file_size >= filters["min_size"])
            if filters.get("max_size"):
                query = query.filter(Document.file_size <= filters["max_size"])

        total = query.count()
        items = query.order_by(Document.name).offset(skip).limit(limit).all()

        return items, total

    def get_pending_retention(
        self,
        before_date: datetime
    ) -> List[Document]:
        """Liste les documents a purger (retention expiree)."""
        return self._base_query().filter(
            Document.retention_until.isnot(None),
            Document.retention_until <= before_date
        ).all()

    def get_deleted_for_purge(
        self,
        deleted_before: datetime
    ) -> List[Document]:
        """Liste les documents supprimes a purger definitivement."""
        return self.db.query(Document).filter(
            Document.tenant_id == self.tenant_id,
            Document.deleted_at.isnot(None),
            Document.deleted_at <= deleted_before
        ).all()

    def increment_view_count(self, document_id: UUID, user_id: UUID) -> None:
        """Incremente le compteur de vues."""
        self.db.query(Document).filter(
            Document.id == document_id
        ).update({
            Document.view_count: Document.view_count + 1,
            Document.last_accessed_at: datetime.utcnow(),
            Document.last_accessed_by: user_id
        })
        self.db.commit()

    def increment_download_count(self, document_id: UUID) -> None:
        """Incremente le compteur de telechargements."""
        self.db.query(Document).filter(
            Document.id == document_id
        ).update({
            Document.download_count: Document.download_count + 1
        })
        self.db.commit()

    def get_statistics(self) -> Dict[str, Any]:
        """Statistiques globales des documents."""
        base = self._base_query()

        total_count = base.count()
        total_size = self.db.query(func.sum(Document.file_size)).filter(
            Document.tenant_id == self.tenant_id,
            Document.deleted_at.is_(None)
        ).scalar() or 0

        # Par categorie
        by_category = dict(
            self.db.query(Document.category, func.count(Document.id)).filter(
                Document.tenant_id == self.tenant_id,
                Document.deleted_at.is_(None)
            ).group_by(Document.category).all()
        )

        # Par statut
        by_status = dict(
            self.db.query(Document.status, func.count(Document.id)).filter(
                Document.tenant_id == self.tenant_id,
                Document.deleted_at.is_(None)
            ).group_by(Document.status).all()
        )

        # Par extension
        by_extension = dict(
            self.db.query(Document.file_extension, func.count(Document.id)).filter(
                Document.tenant_id == self.tenant_id,
                Document.deleted_at.is_(None),
                Document.file_extension.isnot(None)
            ).group_by(Document.file_extension).limit(20).all()
        )

        return {
            "total_count": total_count,
            "total_size": total_size,
            "by_category": by_category,
            "by_status": by_status,
            "by_extension": by_extension
        }


# =============================================================================
# REPOSITORY VERSION
# =============================================================================

class VersionRepository(BaseRepository[DocumentVersion]):
    """Repository pour les versions de documents."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, DocumentVersion, tenant_id)

    def get_versions(
        self,
        document_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[DocumentVersion], int]:
        """Liste les versions d'un document."""
        query = self.db.query(DocumentVersion).filter(
            DocumentVersion.tenant_id == self.tenant_id,
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc())

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total

    def get_version(
        self,
        document_id: UUID,
        version_number: int
    ) -> Optional[DocumentVersion]:
        """Recupere une version specifique."""
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.tenant_id == self.tenant_id,
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number
        ).first()

    def get_latest_version_number(self, document_id: UUID) -> int:
        """Recupere le numero de la derniere version."""
        result = self.db.query(func.max(DocumentVersion.version_number)).filter(
            DocumentVersion.document_id == document_id
        ).scalar()
        return result or 0


# =============================================================================
# REPOSITORY PARTAGE
# =============================================================================

class ShareRepository(BaseRepository[DocumentShare]):
    """Repository pour les partages."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, DocumentShare, tenant_id)

    def get_by_link(self, share_link: str) -> Optional[DocumentShare]:
        """Trouve un partage par son lien."""
        return self.db.query(DocumentShare).filter(
            DocumentShare.share_link == share_link,
            DocumentShare.is_active == True
        ).first()

    def get_document_shares(
        self,
        document_id: UUID
    ) -> List[DocumentShare]:
        """Liste les partages d'un document."""
        return self.db.query(DocumentShare).filter(
            DocumentShare.tenant_id == self.tenant_id,
            DocumentShare.document_id == document_id,
            DocumentShare.is_active == True
        ).all()

    def get_folder_shares(
        self,
        folder_id: UUID
    ) -> List[DocumentShare]:
        """Liste les partages d'un dossier."""
        return self.db.query(DocumentShare).filter(
            DocumentShare.tenant_id == self.tenant_id,
            DocumentShare.folder_id == folder_id,
            DocumentShare.is_active == True
        ).all()

    def get_user_shares(
        self,
        user_id: UUID
    ) -> List[DocumentShare]:
        """Liste les documents partages avec un utilisateur."""
        return self.db.query(DocumentShare).filter(
            DocumentShare.tenant_id == self.tenant_id,
            DocumentShare.shared_with_user_id == user_id,
            DocumentShare.is_active == True
        ).all()

    def check_access(
        self,
        document_id: UUID,
        user_id: UUID,
        required_level: AccessLevel
    ) -> bool:
        """Verifie si un utilisateur a l'acces requis."""
        share = self.db.query(DocumentShare).filter(
            DocumentShare.tenant_id == self.tenant_id,
            DocumentShare.document_id == document_id,
            DocumentShare.shared_with_user_id == user_id,
            DocumentShare.is_active == True,
            or_(
                DocumentShare.valid_until.is_(None),
                DocumentShare.valid_until >= datetime.utcnow()
            )
        ).first()

        if not share:
            return False

        access_levels = {
            AccessLevel.NONE: 0,
            AccessLevel.VIEW: 1,
            AccessLevel.COMMENT: 2,
            AccessLevel.EDIT: 3,
            AccessLevel.FULL: 4
        }

        return access_levels.get(share.access_level, 0) >= access_levels.get(required_level, 0)


# =============================================================================
# REPOSITORY LIEN
# =============================================================================

class LinkRepository(BaseRepository[DocumentLink]):
    """Repository pour les liens document-entite."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, DocumentLink, tenant_id)

    def find_link(
        self,
        document_id: UUID,
        entity_type: LinkEntityType,
        entity_id: UUID
    ) -> Optional[DocumentLink]:
        """Trouve un lien specifique."""
        return self.db.query(DocumentLink).filter(
            DocumentLink.tenant_id == self.tenant_id,
            DocumentLink.document_id == document_id,
            DocumentLink.entity_type == entity_type,
            DocumentLink.entity_id == entity_id
        ).first()

    def get_document_links(self, document_id: UUID) -> List[DocumentLink]:
        """Liste les liens d'un document."""
        return self.db.query(DocumentLink).filter(
            DocumentLink.tenant_id == self.tenant_id,
            DocumentLink.document_id == document_id
        ).all()

    def get_entity_links(
        self,
        entity_type: LinkEntityType,
        entity_id: UUID
    ) -> List[DocumentLink]:
        """Liste les liens d'une entite."""
        return self.db.query(DocumentLink).filter(
            DocumentLink.tenant_id == self.tenant_id,
            DocumentLink.entity_type == entity_type,
            DocumentLink.entity_id == entity_id
        ).all()


# =============================================================================
# REPOSITORY COMMENTAIRE
# =============================================================================

class CommentRepository(BaseRepository[DocumentComment]):
    """Repository pour les commentaires."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, DocumentComment, tenant_id)

    def get_document_comments(
        self,
        document_id: UUID,
        include_deleted: bool = False
    ) -> List[DocumentComment]:
        """Liste les commentaires d'un document."""
        query = self.db.query(DocumentComment).filter(
            DocumentComment.tenant_id == self.tenant_id,
            DocumentComment.document_id == document_id,
            DocumentComment.parent_id.is_(None)  # Seulement les racines
        )

        if not include_deleted:
            query = query.filter(DocumentComment.is_active == True)

        return query.options(
            joinedload(DocumentComment.replies)
        ).order_by(DocumentComment.created_at).all()


# =============================================================================
# REPOSITORY AUDIT
# =============================================================================

class AuditRepository(BaseRepository[DocumentAudit]):
    """Repository pour l'audit."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, DocumentAudit, tenant_id)

    def log_action(
        self,
        action: AuditAction,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        document_id: Optional[UUID] = None,
        folder_id: Optional[UUID] = None,
        document_code: Optional[str] = None,
        document_name: Optional[str] = None,
        description: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> DocumentAudit:
        """Enregistre une action d'audit."""
        audit = DocumentAudit(
            tenant_id=self.tenant_id,
            action=action,
            user_id=user_id,
            user_email=user_email,
            document_id=document_id,
            folder_id=folder_id,
            document_code=document_code,
            document_name=document_name,
            description=description,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        self.db.add(audit)
        self.db.commit()
        return audit

    def get_document_history(
        self,
        document_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[DocumentAudit], int]:
        """Historique d'audit d'un document."""
        query = self.db.query(DocumentAudit).filter(
            DocumentAudit.tenant_id == self.tenant_id,
            DocumentAudit.document_id == document_id
        ).order_by(DocumentAudit.created_at.desc())

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total

    def get_user_activity(
        self,
        user_id: UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[DocumentAudit], int]:
        """Activite d'un utilisateur."""
        query = self.db.query(DocumentAudit).filter(
            DocumentAudit.tenant_id == self.tenant_id,
            DocumentAudit.user_id == user_id
        )

        if from_date:
            query = query.filter(DocumentAudit.created_at >= from_date)
        if to_date:
            query = query.filter(DocumentAudit.created_at <= to_date)

        query = query.order_by(DocumentAudit.created_at.desc())

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total


# =============================================================================
# REPOSITORY SEQUENCE
# =============================================================================

class SequenceRepository:
    """Repository pour les sequences de documents."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get_next_code(self, prefix: str = "DOC") -> str:
        """Genere le prochain code document."""
        current_year = datetime.utcnow().year

        # Verrouillage pessimiste
        sequence = self.db.query(DocumentSequence).filter(
            DocumentSequence.tenant_id == self.tenant_id,
            DocumentSequence.year == current_year,
            DocumentSequence.prefix == prefix
        ).with_for_update().first()

        if not sequence:
            sequence = DocumentSequence(
                tenant_id=self.tenant_id,
                year=current_year,
                prefix=prefix,
                last_number=0
            )
            self.db.add(sequence)
            self.db.flush()

        sequence.last_number += 1
        code = f"{prefix}-{current_year}-{sequence.last_number:05d}"

        self.db.commit()
        return code


# =============================================================================
# REPOSITORY TAG
# =============================================================================

class TagRepository(BaseRepository[DocumentTag]):
    """Repository pour les tags."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, DocumentTag, tenant_id)

    def find_by_slug(self, slug: str) -> Optional[DocumentTag]:
        """Trouve un tag par son slug."""
        return self.db.query(DocumentTag).filter(
            DocumentTag.tenant_id == self.tenant_id,
            DocumentTag.slug == slug
        ).first()

    def get_or_create(self, name: str, color: Optional[str] = None) -> DocumentTag:
        """Recupere ou cree un tag."""
        slug = name.lower().replace(" ", "-")
        tag = self.find_by_slug(slug)

        if not tag:
            tag = DocumentTag(
                tenant_id=self.tenant_id,
                name=name,
                slug=slug,
                color=color
            )
            self.db.add(tag)
            self.db.commit()

        return tag


# =============================================================================
# REPOSITORY CATEGORIE
# =============================================================================

class CategoryRepository(BaseRepository[DocumentCategory]):
    """Repository pour les categories."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db, DocumentCategory, tenant_id)

    def find_by_code(self, code: str) -> Optional[DocumentCategory]:
        """Trouve une categorie par son code."""
        return self.db.query(DocumentCategory).filter(
            DocumentCategory.tenant_id == self.tenant_id,
            DocumentCategory.code == code
        ).first()

    def get_active(self) -> List[DocumentCategory]:
        """Liste les categories actives."""
        return self.db.query(DocumentCategory).filter(
            DocumentCategory.tenant_id == self.tenant_id,
            DocumentCategory.is_active == True
        ).order_by(DocumentCategory.name).all()


# =============================================================================
# REPOSITORY CONFIGURATION STOCKAGE
# =============================================================================

class StorageConfigRepository:
    """Repository pour la configuration de stockage."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get_config(self) -> Optional[StorageConfig]:
        """Recupere la configuration."""
        return self.db.query(StorageConfig).filter(
            StorageConfig.tenant_id == self.tenant_id
        ).first()

    def get_or_create(self) -> StorageConfig:
        """Recupere ou cree la configuration."""
        config = self.get_config()
        if not config:
            config = StorageConfig(tenant_id=self.tenant_id)
            self.db.add(config)
            self.db.commit()
        return config

    def update_used_storage(self, delta: int) -> None:
        """Met a jour l'espace utilise."""
        config = self.get_or_create()
        config.used_storage_bytes += delta
        if config.used_storage_bytes < 0:
            config.used_storage_bytes = 0
        self.db.commit()
