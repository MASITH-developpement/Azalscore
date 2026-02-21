"""
AZALS MODULE - Documents (GED)
==============================

Modeles SQLAlchemy pour la Gestion Electronique de Documents.
Inspire de: Sage, Axonaut, Pennylane, Odoo, Microsoft Dynamics 365, SharePoint

Fonctionnalites:
- Upload/download fichiers
- Dossiers hierarchiques
- Metadonnees personnalisables
- Versioning documents
- Recherche full-text
- Partage et permissions
- Liens avec entites (factures, contrats, etc.)
- Previsualisation
- Compression/archivage
- Retention et purge
- Audit trail acces
- Tags et categories
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.types import JSONB, UniversalUUID
from app.db import Base


# =============================================================================
# ENUMS
# =============================================================================

class DocumentStatus(str, enum.Enum):
    """Statut d'un document."""
    DRAFT = "DRAFT"                  # Brouillon
    PENDING = "PENDING"              # En attente de validation
    ACTIVE = "ACTIVE"                # Actif
    ARCHIVED = "ARCHIVED"            # Archive
    EXPIRED = "EXPIRED"              # Expire
    DELETED = "DELETED"              # Marque pour suppression


class DocumentType(str, enum.Enum):
    """Type de document."""
    FILE = "FILE"                    # Fichier standard
    FOLDER = "FOLDER"                # Dossier
    SHORTCUT = "SHORTCUT"            # Raccourci/lien
    TEMPLATE = "TEMPLATE"            # Modele de document
    ARCHIVE = "ARCHIVE"              # Archive compressee


class FileCategory(str, enum.Enum):
    """Categorie de fichier."""
    DOCUMENT = "DOCUMENT"            # Documents (PDF, DOC, etc.)
    IMAGE = "IMAGE"                  # Images
    VIDEO = "VIDEO"                  # Videos
    AUDIO = "AUDIO"                  # Audio
    SPREADSHEET = "SPREADSHEET"      # Tableurs
    PRESENTATION = "PRESENTATION"    # Presentations
    ARCHIVE = "ARCHIVE"              # Archives (ZIP, etc.)
    CODE = "CODE"                    # Code source
    DATA = "DATA"                    # Donnees (CSV, JSON, etc.)
    OTHER = "OTHER"                  # Autre


class AccessLevel(str, enum.Enum):
    """Niveau d'acces."""
    NONE = "NONE"                    # Aucun acces
    VIEW = "VIEW"                    # Lecture seule
    COMMENT = "COMMENT"              # Lecture + commentaires
    EDIT = "EDIT"                    # Modification
    FULL = "FULL"                    # Controle total


class ShareType(str, enum.Enum):
    """Type de partage."""
    USER = "USER"                    # Partage avec utilisateur
    ROLE = "ROLE"                    # Partage avec role
    DEPARTMENT = "DEPARTMENT"        # Partage avec departement
    TEAM = "TEAM"                    # Partage avec equipe
    PUBLIC = "PUBLIC"                # Acces public (avec lien)
    EXTERNAL = "EXTERNAL"            # Partage externe


class LinkEntityType(str, enum.Enum):
    """Type d'entite liee."""
    INVOICE = "INVOICE"              # Facture
    QUOTE = "QUOTE"                  # Devis
    ORDER = "ORDER"                  # Commande
    CONTRACT = "CONTRACT"            # Contrat
    PROJECT = "PROJECT"              # Projet
    TASK = "TASK"                    # Tache
    CONTACT = "CONTACT"              # Contact
    PRODUCT = "PRODUCT"              # Produit
    EMPLOYEE = "EMPLOYEE"            # Employe
    EXPENSE = "EXPENSE"              # Note de frais
    TICKET = "TICKET"                # Ticket support
    ASSET = "ASSET"                  # Immobilisation
    COMPLIANCE = "COMPLIANCE"        # Conformite
    OTHER = "OTHER"                  # Autre


class RetentionPolicy(str, enum.Enum):
    """Politique de retention."""
    NONE = "NONE"                    # Pas de retention
    SHORT = "SHORT"                  # 1 an
    MEDIUM = "MEDIUM"                # 3 ans
    LONG = "LONG"                    # 5 ans
    LEGAL = "LEGAL"                  # 10 ans (legal)
    PERMANENT = "PERMANENT"          # Permanent


class AuditAction(str, enum.Enum):
    """Action d'audit."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    DOWNLOAD = "DOWNLOAD"
    SHARE = "SHARE"
    UNSHARE = "UNSHARE"
    MOVE = "MOVE"
    COPY = "COPY"
    RENAME = "RENAME"
    RESTORE = "RESTORE"
    ARCHIVE = "ARCHIVE"
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"
    VERSION = "VERSION"
    PREVIEW = "PREVIEW"
    PRINT = "PRINT"
    EXPORT = "EXPORT"


class CompressionStatus(str, enum.Enum):
    """Statut de compression."""
    NONE = "NONE"                    # Non compresse
    PENDING = "PENDING"              # En attente
    COMPRESSED = "COMPRESSED"        # Compresse
    FAILED = "FAILED"                # Echec


class WorkflowStatus(str, enum.Enum):
    """Statut du workflow de validation."""
    NONE = "NONE"                    # Pas de workflow
    PENDING = "PENDING"              # En attente
    APPROVED = "APPROVED"            # Approuve
    REJECTED = "REJECTED"            # Rejete
    CANCELLED = "CANCELLED"          # Annule


# =============================================================================
# MODELE - DOSSIER
# =============================================================================

class Folder(Base):
    """
    Dossier pour organiser les documents.
    Structure hierarchique avec chemin materialise.
    """
    __tablename__ = "doc_folders"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Hierarchie
    parent_id = Column(UniversalUUID(), ForeignKey("doc_folders.id", ondelete="CASCADE"), nullable=True)
    path = Column(String(1000), nullable=False, index=True)  # /root/parent/folder
    level = Column(Integer, default=0, nullable=False)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Code couleur hex
    icon = Column(String(50), nullable=True)  # Icone personnalisee

    # Parametres
    is_system = Column(Boolean, default=False)  # Dossier systeme (non supprimable)
    is_template = Column(Boolean, default=False)  # Dossier modele
    default_access_level = Column(Enum(AccessLevel), default=AccessLevel.VIEW)
    inherit_permissions = Column(Boolean, default=True)

    # Retention
    retention_policy = Column(Enum(RetentionPolicy), default=RetentionPolicy.NONE)
    retention_days = Column(Integer, nullable=True)

    # Statistiques
    document_count = Column(Integer, default=0)
    subfolder_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)  # Taille totale en bytes

    # Metadonnees
    metadata = Column(JSONB, default=dict)  # Metadonnees personnalisees
    tags = Column(JSONB, default=list)

    # Soft delete
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Version pour optimistic locking
    version = Column(Integer, default=1, nullable=False)

    # Relations
    parent = relationship("Folder", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="folder", lazy="dynamic")
    permissions = relationship("FolderPermission", back_populates="folder", lazy="dynamic", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'parent_id', 'name', name='uq_folder_name_in_parent'),
        Index('ix_folder_tenant_path', 'tenant_id', 'path'),
        Index('ix_folder_tenant_parent', 'tenant_id', 'parent_id'),
        Index('ix_folder_deleted', 'deleted_at'),
    )


# =============================================================================
# MODELE - DOCUMENT
# =============================================================================

class Document(Base):
    """
    Document ou fichier.
    Support du versioning et des metadonnees.
    """
    __tablename__ = "doc_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Reference
    code = Column(String(50), nullable=False, index=True)  # DOC-2024-0001
    folder_id = Column(UniversalUUID(), ForeignKey("doc_folders.id", ondelete="SET NULL"), nullable=True)

    # Type et statut
    document_type = Column(Enum(DocumentType), default=DocumentType.FILE, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.ACTIVE, nullable=False)
    category = Column(Enum(FileCategory), default=FileCategory.DOCUMENT, nullable=False)

    # Informations fichier
    name = Column(String(255), nullable=False)
    title = Column(String(500), nullable=True)  # Titre affiche (peut etre different du nom)
    description = Column(Text, nullable=True)
    file_extension = Column(String(20), nullable=True)
    mime_type = Column(String(255), nullable=True)
    file_size = Column(BigInteger, default=0)  # Taille en bytes

    # Stockage
    storage_path = Column(String(1000), nullable=True)  # Chemin sur le stockage
    storage_provider = Column(String(50), default="local")  # local, s3, azure, gcs
    storage_bucket = Column(String(255), nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA-256 du fichier
    checksum_algorithm = Column(String(20), default="sha256")

    # Versioning
    current_version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True)
    original_document_id = Column(UniversalUUID(), nullable=True)  # ID du document original si version

    # Contenu searchable
    content_text = Column(Text, nullable=True)  # Texte extrait pour recherche full-text
    content_indexed = Column(Boolean, default=False)
    indexed_at = Column(DateTime, nullable=True)

    # Workflow
    workflow_status = Column(Enum(WorkflowStatus), default=WorkflowStatus.NONE)
    workflow_id = Column(UniversalUUID(), nullable=True)
    approved_by = Column(UniversalUUID(), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Verrouillage
    is_locked = Column(Boolean, default=False)
    locked_by = Column(UniversalUUID(), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    lock_reason = Column(String(255), nullable=True)

    # Compression
    compression_status = Column(Enum(CompressionStatus), default=CompressionStatus.NONE)
    compressed_size = Column(BigInteger, nullable=True)
    compression_ratio = Column(Float, nullable=True)

    # Retention
    retention_policy = Column(Enum(RetentionPolicy), default=RetentionPolicy.NONE)
    retention_until = Column(DateTime, nullable=True)
    purge_scheduled_at = Column(DateTime, nullable=True)

    # Previsualisation
    preview_available = Column(Boolean, default=False)
    preview_path = Column(String(1000), nullable=True)
    thumbnail_path = Column(String(1000), nullable=True)

    # Metadonnees
    metadata = Column(JSONB, default=dict)  # Metadonnees personnalisees
    tags = Column(JSONB, default=list)  # Tags
    custom_fields = Column(JSONB, default=dict)  # Champs personnalises

    # Statistiques
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    last_accessed_by = Column(UniversalUUID(), nullable=True)

    # Soft delete
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Version pour optimistic locking
    version = Column(Integer, default=1, nullable=False)

    # Relations
    folder = relationship("Folder", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")
    shares = relationship("DocumentShare", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")
    links = relationship("DocumentLink", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")
    comments = relationship("DocumentComment", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")
    audit_logs = relationship("DocumentAudit", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_document_code'),
        Index('ix_document_tenant_folder', 'tenant_id', 'folder_id'),
        Index('ix_document_tenant_status', 'tenant_id', 'status'),
        Index('ix_document_tenant_type', 'tenant_id', 'document_type'),
        Index('ix_document_tenant_category', 'tenant_id', 'category'),
        Index('ix_document_checksum', 'checksum'),
        Index('ix_document_deleted', 'deleted_at'),
        Index('ix_document_retention', 'retention_until'),
        # Index full-text sur content_text (PostgreSQL)
        # Index('ix_document_content_fts', func.to_tsvector('french', content_text), postgresql_using='gin'),
    )


# =============================================================================
# MODELE - VERSION DE DOCUMENT
# =============================================================================

class DocumentVersion(Base):
    """
    Version d'un document.
    Historique des modifications.
    """
    __tablename__ = "doc_versions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Document parent
    document_id = Column(UniversalUUID(), ForeignKey("doc_documents.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)

    # Informations fichier
    file_size = Column(BigInteger, default=0)
    storage_path = Column(String(1000), nullable=True)
    checksum = Column(String(64), nullable=True)

    # Modifications
    change_summary = Column(String(500), nullable=True)  # Resume des modifications
    change_type = Column(String(50), nullable=True)  # MINOR, MAJOR, REVISION

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    document = relationship("Document", back_populates="versions")

    __table_args__ = (
        UniqueConstraint('document_id', 'version_number', name='uq_document_version'),
        Index('ix_version_document', 'document_id'),
    )


# =============================================================================
# MODELE - PARTAGE DE DOCUMENT
# =============================================================================

class DocumentShare(Base):
    """
    Partage d'un document ou dossier.
    Gestion des permissions.
    """
    __tablename__ = "doc_shares"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Document ou dossier partage
    document_id = Column(UniversalUUID(), ForeignKey("doc_documents.id", ondelete="CASCADE"), nullable=True)
    folder_id = Column(UniversalUUID(), ForeignKey("doc_folders.id", ondelete="CASCADE"), nullable=True)

    # Type de partage
    share_type = Column(Enum(ShareType), nullable=False)
    access_level = Column(Enum(AccessLevel), default=AccessLevel.VIEW, nullable=False)

    # Destinataire
    shared_with_user_id = Column(UniversalUUID(), nullable=True)
    shared_with_role = Column(String(100), nullable=True)
    shared_with_department = Column(String(100), nullable=True)
    shared_with_email = Column(String(255), nullable=True)  # Pour partage externe

    # Lien de partage
    share_link = Column(String(255), nullable=True, unique=True)
    share_link_expires_at = Column(DateTime, nullable=True)
    share_link_password = Column(String(255), nullable=True)  # Hash du mot de passe
    share_link_max_downloads = Column(Integer, nullable=True)
    share_link_download_count = Column(Integer, default=0)

    # Options
    can_download = Column(Boolean, default=True)
    can_print = Column(Boolean, default=True)
    can_share = Column(Boolean, default=False)
    notify_on_access = Column(Boolean, default=False)

    # Validite
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UniversalUUID(), nullable=True)

    # Relations
    document = relationship("Document", back_populates="shares")

    __table_args__ = (
        Index('ix_share_document', 'document_id'),
        Index('ix_share_folder', 'folder_id'),
        Index('ix_share_user', 'shared_with_user_id'),
        Index('ix_share_link', 'share_link'),
    )


# =============================================================================
# MODELE - PERMISSION DOSSIER
# =============================================================================

class FolderPermission(Base):
    """
    Permission sur un dossier.
    """
    __tablename__ = "doc_folder_permissions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    folder_id = Column(UniversalUUID(), ForeignKey("doc_folders.id", ondelete="CASCADE"), nullable=False)
    access_level = Column(Enum(AccessLevel), nullable=False)

    # Destinataire
    user_id = Column(UniversalUUID(), nullable=True)
    role = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)

    # Options
    inherit = Column(Boolean, default=True)  # Herite aux sous-dossiers
    include_documents = Column(Boolean, default=True)  # Applique aux documents

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    folder = relationship("Folder", back_populates="permissions")

    __table_args__ = (
        Index('ix_folder_perm_folder', 'folder_id'),
        Index('ix_folder_perm_user', 'user_id'),
    )


# =============================================================================
# MODELE - LIEN DOCUMENT-ENTITE
# =============================================================================

class DocumentLink(Base):
    """
    Lien entre un document et une entite metier.
    Permet d'attacher des documents aux factures, contrats, etc.
    """
    __tablename__ = "doc_links"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    document_id = Column(UniversalUUID(), ForeignKey("doc_documents.id", ondelete="CASCADE"), nullable=False)

    # Entite liee
    entity_type = Column(Enum(LinkEntityType), nullable=False)
    entity_id = Column(UniversalUUID(), nullable=False)
    entity_code = Column(String(100), nullable=True)  # Code lisible (ex: INV-2024-0001)

    # Type de lien
    link_type = Column(String(50), default="attachment")  # attachment, reference, source
    is_primary = Column(Boolean, default=False)  # Document principal de l'entite

    # Metadonnees
    description = Column(String(500), nullable=True)
    metadata = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    document = relationship("Document", back_populates="links")

    __table_args__ = (
        UniqueConstraint('document_id', 'entity_type', 'entity_id', name='uq_document_entity_link'),
        Index('ix_link_document', 'document_id'),
        Index('ix_link_entity', 'entity_type', 'entity_id'),
    )


# =============================================================================
# MODELE - COMMENTAIRE DOCUMENT
# =============================================================================

class DocumentComment(Base):
    """
    Commentaire sur un document.
    """
    __tablename__ = "doc_comments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    document_id = Column(UniversalUUID(), ForeignKey("doc_documents.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UniversalUUID(), ForeignKey("doc_comments.id", ondelete="CASCADE"), nullable=True)

    # Contenu
    content = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)

    # Position (pour annotations)
    page_number = Column(Integer, nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)

    # Mentions
    mentions = Column(JSONB, default=list)  # Liste des user_id mentionnes

    # Soft delete
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    document = relationship("Document", back_populates="comments")
    parent = relationship("DocumentComment", remote_side=[id], backref="replies")

    __table_args__ = (
        Index('ix_comment_document', 'document_id'),
        Index('ix_comment_parent', 'parent_id'),
    )


# =============================================================================
# MODELE - TAG DOCUMENT
# =============================================================================

class DocumentTag(Base):
    """
    Tag pour categoriser les documents.
    """
    __tablename__ = "doc_tags"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    color = Column(String(7), nullable=True)  # Code couleur hex
    description = Column(String(500), nullable=True)

    # Hierarchie
    parent_id = Column(UniversalUUID(), ForeignKey("doc_tags.id", ondelete="SET NULL"), nullable=True)

    # Statistiques
    document_count = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'slug', name='uq_tag_slug'),
        Index('ix_tag_tenant', 'tenant_id'),
    )


# =============================================================================
# MODELE - CATEGORIE DOCUMENT
# =============================================================================

class DocumentCategory(Base):
    """
    Categorie pour classifier les documents.
    """
    __tablename__ = "doc_categories"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)

    # Hierarchie
    parent_id = Column(UniversalUUID(), ForeignKey("doc_categories.id", ondelete="SET NULL"), nullable=True)
    level = Column(Integer, default=0)

    # Configuration
    default_retention = Column(Enum(RetentionPolicy), default=RetentionPolicy.NONE)
    required_metadata = Column(JSONB, default=list)  # Champs obligatoires
    allowed_extensions = Column(JSONB, default=list)  # Extensions autorisees
    max_file_size = Column(BigInteger, nullable=True)  # Taille max en bytes

    # Statistiques
    document_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_category_code'),
        Index('ix_category_tenant', 'tenant_id'),
        Index('ix_category_parent', 'parent_id'),
    )


# =============================================================================
# MODELE - AUDIT DOCUMENT
# =============================================================================

class DocumentAudit(Base):
    """
    Journal d'audit des acces et actions sur les documents.
    """
    __tablename__ = "doc_audit"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Document
    document_id = Column(UniversalUUID(), ForeignKey("doc_documents.id", ondelete="CASCADE"), nullable=True)
    folder_id = Column(UniversalUUID(), nullable=True)
    document_code = Column(String(50), nullable=True)
    document_name = Column(String(255), nullable=True)

    # Action
    action = Column(Enum(AuditAction), nullable=False)
    description = Column(String(500), nullable=True)

    # Utilisateur
    user_id = Column(UniversalUUID(), nullable=True)
    user_email = Column(String(255), nullable=True)
    user_name = Column(String(255), nullable=True)

    # Contexte
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(255), nullable=True)

    # Details
    old_value = Column(JSONB, nullable=True)  # Valeur avant modification
    new_value = Column(JSONB, nullable=True)  # Valeur apres modification
    metadata = Column(JSONB, default=dict)

    # Resultat
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relations
    document = relationship("Document", back_populates="audit_logs")

    __table_args__ = (
        Index('ix_audit_tenant_date', 'tenant_id', 'created_at'),
        Index('ix_audit_document', 'document_id'),
        Index('ix_audit_user', 'user_id'),
        Index('ix_audit_action', 'action'),
    )


# =============================================================================
# MODELE - SEQUENCE DOCUMENT
# =============================================================================

class DocumentSequence(Base):
    """
    Sequence pour la generation des codes documents.
    """
    __tablename__ = "doc_sequences"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    year = Column(Integer, nullable=False)
    prefix = Column(String(10), default="DOC", nullable=False)
    last_number = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'year', 'prefix', name='uq_doc_sequence'),
    )


# =============================================================================
# MODELE - CONFIGURATION STOCKAGE
# =============================================================================

class StorageConfig(Base):
    """
    Configuration du stockage pour le tenant.
    """
    __tablename__ = "doc_storage_config"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String(50), nullable=False, unique=True)

    # Provider
    provider = Column(String(50), default="local", nullable=False)  # local, s3, azure, gcs
    bucket = Column(String(255), nullable=True)
    region = Column(String(50), nullable=True)
    endpoint = Column(String(500), nullable=True)

    # Credentials (chiffrees)
    access_key = Column(String(500), nullable=True)
    secret_key = Column(String(500), nullable=True)

    # Quotas
    max_storage_bytes = Column(BigInteger, nullable=True)  # Quota total
    max_file_size_bytes = Column(BigInteger, nullable=True)  # Taille max fichier
    used_storage_bytes = Column(BigInteger, default=0)

    # Options
    enable_versioning = Column(Boolean, default=True)
    enable_compression = Column(Boolean, default=True)
    compression_threshold = Column(BigInteger, default=1048576)  # 1MB
    enable_thumbnails = Column(Boolean, default=True)
    enable_preview = Column(Boolean, default=True)
    enable_ocr = Column(Boolean, default=False)

    # Retention
    default_retention = Column(Enum(RetentionPolicy), default=RetentionPolicy.NONE)
    trash_retention_days = Column(Integer, default=30)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_storage_config_tenant', 'tenant_id'),
    )
