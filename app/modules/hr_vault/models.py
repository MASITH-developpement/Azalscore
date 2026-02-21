"""
AZALS MODULE HR_VAULT - Modeles Coffre-fort RH
================================================

Modeles SQLAlchemy pour le stockage securise des documents employes.
Inspire de: Sage HR, Lucca, Payfit, Personio, BambooHR

Conformite:
- RGPD (droit a l'oubli, portabilite)
- Code du travail articles L3243-2, D3243-8
- Decret 2016-1762 (bulletins de paie electroniques)
- NF Z42-020 (archivage electronique)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.types import JSONB, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class VaultDocumentType(str, enum.Enum):
    """Types de documents du coffre-fort RH."""
    # Paie
    PAYSLIP = "PAYSLIP"
    PAYSLIP_SUMMARY = "PAYSLIP_SUMMARY"
    TAX_STATEMENT = "TAX_STATEMENT"

    # Contrats
    CONTRACT = "CONTRACT"
    AMENDMENT = "AMENDMENT"
    TEMPORARY_CONTRACT = "TEMPORARY_CONTRACT"
    APPRENTICESHIP = "APPRENTICESHIP"
    INTERNSHIP = "INTERNSHIP"

    # Attestations
    EMPLOYMENT_CERTIFICATE = "EMPLOYMENT_CERTIFICATE"
    SALARY_CERTIFICATE = "SALARY_CERTIFICATE"
    TRAINING_CERTIFICATE = "TRAINING_CERTIFICATE"
    FRANCE_TRAVAIL = "FRANCE_TRAVAIL"

    # Fin de contrat
    TERMINATION_LETTER = "TERMINATION_LETTER"
    STC = "STC"
    WORK_CERTIFICATE = "WORK_CERTIFICATE"
    PORTABILITY_NOTICE = "PORTABILITY_NOTICE"

    # Sante et securite
    MEDICAL_APTITUDE = "MEDICAL_APTITUDE"
    ACCIDENT_DECLARATION = "ACCIDENT_DECLARATION"

    # Documents personnels
    ID_DOCUMENT = "ID_DOCUMENT"
    DIPLOMA = "DIPLOMA"
    DEGREE = "DEGREE"
    CERTIFICATION = "CERTIFICATION"
    RIB = "RIB"
    VITALE_CARD = "VITALE_CARD"
    DRIVING_LICENSE = "DRIVING_LICENSE"

    # Administratif
    EVALUATION = "EVALUATION"
    WARNING = "WARNING"
    PROMOTION_LETTER = "PROMOTION_LETTER"
    BONUS_LETTER = "BONUS_LETTER"

    # Autre
    OTHER = "OTHER"


class VaultDocumentStatus(str, enum.Enum):
    """Statut d'un document."""
    DRAFT = "DRAFT"
    PENDING_SIGNATURE = "PENDING_SIGNATURE"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class VaultAccessType(str, enum.Enum):
    """Type d'acces au document."""
    VIEW = "VIEW"
    DOWNLOAD = "DOWNLOAD"
    PRINT = "PRINT"
    SHARE = "SHARE"
    EDIT = "EDIT"
    DELETE = "DELETE"
    SIGN = "SIGN"


class VaultAccessRole(str, enum.Enum):
    """Role d'acces au coffre-fort."""
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    HR_ADMIN = "HR_ADMIN"
    HR_DIRECTOR = "HR_DIRECTOR"
    LEGAL = "LEGAL"
    ACCOUNTANT = "ACCOUNTANT"
    SYSTEM = "SYSTEM"


class RetentionPeriod(str, enum.Enum):
    """Duree de conservation legale."""
    FIVE_YEARS = "5_YEARS"
    TEN_YEARS = "10_YEARS"
    THIRTY_YEARS = "30_YEARS"
    FIFTY_YEARS = "50_YEARS"
    LIFETIME_PLUS_5 = "LIFETIME_PLUS_5"
    PERMANENT = "PERMANENT"


class SignatureStatus(str, enum.Enum):
    """Statut de signature electronique."""
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    SIGNED_EMPLOYEE = "SIGNED_EMPLOYEE"
    SIGNED_EMPLOYER = "SIGNED_EMPLOYER"
    FULLY_SIGNED = "FULLY_SIGNED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class EncryptionAlgorithm(str, enum.Enum):
    """Algorithme de chiffrement."""
    AES_256_GCM = "AES_256_GCM"
    AES_256_CBC = "AES_256_CBC"


class GDPRRequestType(str, enum.Enum):
    """Type de demande RGPD."""
    ACCESS = "ACCESS"
    RECTIFICATION = "RECTIFICATION"
    ERASURE = "ERASURE"
    PORTABILITY = "PORTABILITY"
    RESTRICTION = "RESTRICTION"
    OBJECTION = "OBJECTION"


class GDPRRequestStatus(str, enum.Enum):
    """Statut de demande RGPD."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AlertType(str, enum.Enum):
    """Type d'alerte."""
    EXPIRATION = "EXPIRATION"
    MISSING_DOCUMENT = "MISSING_DOCUMENT"
    SIGNATURE_PENDING = "SIGNATURE_PENDING"
    RETENTION_END = "RETENTION_END"
    GDPR_REQUEST = "GDPR_REQUEST"
    ACCESS_ANOMALY = "ACCESS_ANOMALY"


# ============================================================================
# MODELES - CATEGORIES DE DOCUMENTS
# ============================================================================

class VaultDocumentCategory(Base):
    """Categorie de documents personnalisable."""
    __tablename__ = "hr_vault_categories"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)

    # Configuration
    default_retention = Column(SQLEnum(RetentionPeriod), default=RetentionPeriod.FIVE_YEARS)
    requires_signature = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=True)
    visible_to_employee = Column(Boolean, default=True)

    # Ordre d'affichage
    sort_order = Column(Integer, default=0)

    # Soft delete
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)
    version = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_vault_category_code'),
        Index('idx_vault_categories_tenant', 'tenant_id'),
        Index('idx_vault_categories_active', 'tenant_id', 'is_active'),
    )


# ============================================================================
# MODELES - DOCUMENTS
# ============================================================================

class VaultDocument(Base):
    """Document dans le coffre-fort RH."""
    __tablename__ = "hr_vault_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UniversalUUID(), ForeignKey("hr_employees.id"), nullable=False)

    # Classification
    document_type = Column(SQLEnum(VaultDocumentType), nullable=False)
    category_id = Column(UniversalUUID(), ForeignKey("hr_vault_categories.id"), nullable=True)

    # Informations du document
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)

    # Fichier
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    storage_provider = Column(String(50), default="local")

    # Chiffrement
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(UniversalUUID(), ForeignKey("hr_vault_encryption_keys.id"), nullable=True)
    encryption_algorithm = Column(SQLEnum(EncryptionAlgorithm), default=EncryptionAlgorithm.AES_256_GCM)

    # Integrite
    file_hash = Column(String(64), nullable=False)  # SHA-256
    hash_algorithm = Column(String(20), default="SHA256")

    # Horodatage certifie
    timestamp_token = Column(Text, nullable=True)
    timestamp_authority = Column(String(255), nullable=True)
    timestamped_at = Column(DateTime, nullable=True)

    # Statut
    status = Column(SQLEnum(VaultDocumentStatus), default=VaultDocumentStatus.ACTIVE)

    # Dates du document
    document_date = Column(Date, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    # Paie specifique
    pay_period = Column(String(20), nullable=True)  # "2024-01"
    gross_salary = Column(Numeric(12, 2), nullable=True)
    net_salary = Column(Numeric(12, 2), nullable=True)

    # Signature electronique
    signature_status = Column(SQLEnum(SignatureStatus), default=SignatureStatus.NOT_REQUIRED)
    signature_request_id = Column(String(255), nullable=True)
    signed_at = Column(DateTime, nullable=True)
    signature_proof = Column(Text, nullable=True)

    # Conservation
    retention_period = Column(SQLEnum(RetentionPeriod), default=RetentionPeriod.FIFTY_YEARS)
    retention_end_date = Column(Date, nullable=True)

    # Confidentialite
    is_confidential = Column(Boolean, default=True)
    confidentiality_level = Column(Integer, default=1)  # 1-5
    visible_to_employee = Column(Boolean, default=True)

    # Notification
    employee_notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    employee_viewed = Column(Boolean, default=False)
    first_viewed_at = Column(DateTime, nullable=True)

    # Metadonnees
    tags = Column(JSONB, default=list)
    custom_fields = Column(JSONB, default=dict)
    source_system = Column(String(100), nullable=True)
    source_reference = Column(String(255), nullable=True)

    # Soft delete
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)
    deletion_reason = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)
    version = Column(Integer, default=1)

    # Relations
    employee = relationship("Employee", foreign_keys=[employee_id])
    category = relationship("VaultDocumentCategory", foreign_keys=[category_id])
    versions = relationship("VaultDocumentVersion", back_populates="document", cascade="all, delete-orphan")
    access_logs = relationship("VaultAccessLog", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_vault_docs_tenant', 'tenant_id'),
        Index('idx_vault_docs_employee', 'tenant_id', 'employee_id'),
        Index('idx_vault_docs_type', 'tenant_id', 'document_type'),
        Index('idx_vault_docs_status', 'tenant_id', 'status'),
        Index('idx_vault_docs_category', 'tenant_id', 'category_id'),
        Index('idx_vault_docs_expiry', 'tenant_id', 'expiry_date'),
        Index('idx_vault_docs_pay_period', 'tenant_id', 'pay_period'),
        Index('idx_vault_docs_active', 'tenant_id', 'is_active'),
        Index('idx_vault_docs_signature', 'tenant_id', 'signature_status'),
    )


class VaultDocumentVersion(Base):
    """Version d'un document (historique des modifications)."""
    __tablename__ = "hr_vault_document_versions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("hr_vault_documents.id"), nullable=False)

    version_number = Column(Integer, nullable=False)

    # Fichier
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)

    # Chiffrement
    encryption_key_id = Column(UniversalUUID(), nullable=True)

    # Horodatage
    timestamp_token = Column(Text, nullable=True)

    # Changement
    change_reason = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    document = relationship("VaultDocument", back_populates="versions")

    __table_args__ = (
        UniqueConstraint('document_id', 'version_number', name='uq_vault_version'),
        Index('idx_vault_versions_tenant', 'tenant_id'),
        Index('idx_vault_versions_document', 'document_id'),
    )


# ============================================================================
# MODELES - CHIFFREMENT
# ============================================================================

class VaultEncryptionKey(Base):
    """Cle de chiffrement pour les documents."""
    __tablename__ = "hr_vault_encryption_keys"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Cle (chiffree avec master key)
    algorithm = Column(SQLEnum(EncryptionAlgorithm), default=EncryptionAlgorithm.AES_256_GCM)
    encrypted_key = Column(LargeBinary, nullable=False)
    key_version = Column(Integer, default=1)

    # Gestion du cycle de vie
    is_active = Column(Boolean, default=True)
    rotated_to_id = Column(UniversalUUID(), ForeignKey("hr_vault_encryption_keys.id"), nullable=True)
    rotated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_vault_keys_tenant', 'tenant_id'),
        Index('idx_vault_keys_active', 'tenant_id', 'is_active'),
    )


# ============================================================================
# MODELES - ACCES
# ============================================================================

class VaultAccessLog(Base):
    """Journal d'acces aux documents (audit trail)."""
    __tablename__ = "hr_vault_access_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("hr_vault_documents.id"), nullable=False)
    employee_id = Column(UniversalUUID(), nullable=False)  # Proprietaire du document

    # Qui a accede
    accessed_by = Column(UniversalUUID(), nullable=False)
    access_role = Column(SQLEnum(VaultAccessRole), nullable=False)

    # Action
    access_type = Column(SQLEnum(VaultAccessType), nullable=False)
    access_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Contexte
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_type = Column(String(50), nullable=True)
    geolocation = Column(String(255), nullable=True)

    # Resultat
    success = Column(Boolean, default=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Details
    details = Column(JSONB, default=dict)

    # Relations
    document = relationship("VaultDocument", back_populates="access_logs")

    __table_args__ = (
        Index('idx_vault_access_tenant', 'tenant_id'),
        Index('idx_vault_access_document', 'document_id'),
        Index('idx_vault_access_employee', 'tenant_id', 'employee_id'),
        Index('idx_vault_access_user', 'tenant_id', 'accessed_by'),
        Index('idx_vault_access_date', 'tenant_id', 'access_date'),
        Index('idx_vault_access_type', 'tenant_id', 'access_type'),
    )


class VaultAccessPermission(Base):
    """Permissions d'acces au coffre-fort."""
    __tablename__ = "hr_vault_access_permissions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Qui
    user_id = Column(UniversalUUID(), nullable=True)  # Permission utilisateur specifique
    role = Column(SQLEnum(VaultAccessRole), nullable=True)  # Permission par role

    # Quoi
    employee_id = Column(UniversalUUID(), nullable=True)  # Acces a un employe specifique
    document_type = Column(SQLEnum(VaultDocumentType), nullable=True)  # Acces a un type de doc
    category_id = Column(UniversalUUID(), nullable=True)  # Acces a une categorie

    # Actions autorisees
    can_view = Column(Boolean, default=False)
    can_download = Column(Boolean, default=False)
    can_print = Column(Boolean, default=False)
    can_upload = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    can_sign = Column(Boolean, default=False)

    # Validite
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    # Audit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_vault_perms_tenant', 'tenant_id'),
        Index('idx_vault_perms_user', 'tenant_id', 'user_id'),
        Index('idx_vault_perms_role', 'tenant_id', 'role'),
        Index('idx_vault_perms_employee', 'tenant_id', 'employee_id'),
    )


# ============================================================================
# MODELES - CONSENTEMENT ET RGPD
# ============================================================================

class VaultConsent(Base):
    """Consentement pour l'utilisation du coffre-fort."""
    __tablename__ = "hr_vault_consents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UniversalUUID(), ForeignKey("hr_employees.id"), nullable=False)

    # Type de consentement
    consent_type = Column(String(50), nullable=False)  # vault_activation, electronic_payslip, etc.
    consent_version = Column(String(20), nullable=False)

    # Consentement
    given = Column(Boolean, default=False)
    given_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    # Contexte
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Preuve
    consent_text_hash = Column(String(64), nullable=True)
    signature_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index('idx_vault_consents_tenant', 'tenant_id'),
        Index('idx_vault_consents_employee', 'tenant_id', 'employee_id'),
        Index('idx_vault_consents_type', 'tenant_id', 'consent_type'),
    )


class VaultGDPRRequest(Base):
    """Demande RGPD (droit d'acces, suppression, portabilite)."""
    __tablename__ = "hr_vault_gdpr_requests"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UniversalUUID(), ForeignKey("hr_employees.id"), nullable=False)

    # Demande
    request_code = Column(String(50), nullable=False)
    request_type = Column(SQLEnum(GDPRRequestType), nullable=False)
    status = Column(SQLEnum(GDPRRequestStatus), default=GDPRRequestStatus.PENDING)

    # Details
    request_description = Column(Text, nullable=True)
    document_types = Column(JSONB, default=list)  # Types de documents concernes
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    # Dates
    requested_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(Date, nullable=False)  # 30 jours max RGPD
    processed_at = Column(DateTime, nullable=True)

    # Traitement
    processed_by = Column(UniversalUUID(), nullable=True)
    response_details = Column(Text, nullable=True)

    # Export (pour portabilite)
    export_file_path = Column(String(500), nullable=True)
    export_file_hash = Column(String(64), nullable=True)
    export_expires_at = Column(DateTime, nullable=True)
    download_count = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'request_code', name='uq_vault_gdpr_code'),
        Index('idx_vault_gdpr_tenant', 'tenant_id'),
        Index('idx_vault_gdpr_employee', 'tenant_id', 'employee_id'),
        Index('idx_vault_gdpr_status', 'tenant_id', 'status'),
        Index('idx_vault_gdpr_type', 'tenant_id', 'request_type'),
    )


# ============================================================================
# MODELES - ALERTES ET NOTIFICATIONS
# ============================================================================

class VaultAlert(Base):
    """Alerte du coffre-fort RH."""
    __tablename__ = "hr_vault_alerts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UniversalUUID(), nullable=True)
    document_id = Column(UniversalUUID(), ForeignKey("hr_vault_documents.id"), nullable=True)

    # Alerte
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="INFO")  # INFO, WARNING, CRITICAL

    # Cible
    target_user_id = Column(UniversalUUID(), nullable=True)
    target_role = Column(SQLEnum(VaultAccessRole), nullable=True)

    # Statut
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)

    # Action
    action_url = Column(String(500), nullable=True)
    action_taken = Column(Boolean, default=False)
    action_taken_at = Column(DateTime, nullable=True)

    # Dates
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_vault_alerts_tenant', 'tenant_id'),
        Index('idx_vault_alerts_employee', 'tenant_id', 'employee_id'),
        Index('idx_vault_alerts_type', 'tenant_id', 'alert_type'),
        Index('idx_vault_alerts_target', 'tenant_id', 'target_user_id'),
        Index('idx_vault_alerts_unread', 'tenant_id', 'is_read'),
    )


# ============================================================================
# MODELES - STATISTIQUES
# ============================================================================

class VaultStatistics(Base):
    """Statistiques du coffre-fort (snapshot quotidien)."""
    __tablename__ = "hr_vault_statistics"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False)

    # Compteurs
    total_employees = Column(Integer, default=0)
    active_vaults = Column(Integer, default=0)
    total_documents = Column(Integer, default=0)
    documents_by_type = Column(JSONB, default=dict)

    # Stockage
    total_storage_bytes = Column(Numeric(20, 0), default=0)
    storage_by_type = Column(JSONB, default=dict)

    # Activite
    documents_uploaded = Column(Integer, default=0)
    documents_viewed = Column(Integer, default=0)
    documents_downloaded = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)

    # Conformite
    pending_signatures = Column(Integer, default=0)
    expiring_documents = Column(Integer, default=0)
    gdpr_requests_pending = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'date', name='uq_vault_stats_date'),
        Index('idx_vault_stats_tenant', 'tenant_id'),
        Index('idx_vault_stats_date', 'tenant_id', 'date'),
    )
