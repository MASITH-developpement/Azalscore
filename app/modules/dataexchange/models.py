"""
AZALS - Module DataExchange - Modeles SQLAlchemy
=================================================
Import/Export de donnees multi-format avec mapping configurable.

Inspire de: Sage Data Exchange, Axonaut Import, Pennylane Connect,
Odoo Import/Export, Microsoft Dynamics 365 Data Management.

CRITIQUE: Tous les modeles ont tenant_id pour isolation multi-tenant.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, BigInteger,
    ForeignKey, Index, Numeric
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.core.types import JSON, UniversalUUID


# ============== Enumerations ==============

class FileFormat(str, Enum):
    """Formats de fichiers supportes."""
    CSV = "csv"
    EXCEL = "excel"
    XLSX = "xlsx"
    XLS = "xls"
    JSON = "json"
    XML = "xml"
    OFX = "ofx"           # Format bancaire
    QIF = "qif"           # Quicken Interchange Format
    CFONB = "cfonb"       # Format bancaire francais
    FEC = "fec"           # Fichier Ecritures Comptables
    EBICS = "ebics"       # Format bancaire europeen


class ExchangeType(str, Enum):
    """Type d'echange."""
    IMPORT = "import"
    EXPORT = "export"


class ExchangeStatus(str, Enum):
    """Statut d'un echange."""
    DRAFT = "draft"               # Brouillon
    PENDING = "pending"           # En attente d'execution
    VALIDATING = "validating"     # Validation en cours
    PROCESSING = "processing"     # Traitement en cours
    COMPLETED = "completed"       # Termine avec succes
    PARTIAL = "partial"           # Termine partiellement
    FAILED = "failed"             # Echec
    CANCELLED = "cancelled"       # Annule
    ROLLED_BACK = "rolled_back"   # Rollback effectue


class ConnectorType(str, Enum):
    """Types de connecteurs de fichiers."""
    LOCAL = "local"               # Systeme de fichiers local
    FTP = "ftp"                   # FTP
    SFTP = "sftp"                 # SFTP
    S3 = "s3"                     # Amazon S3
    GCS = "gcs"                   # Google Cloud Storage
    AZURE_BLOB = "azure_blob"     # Azure Blob Storage
    WEBDAV = "webdav"             # WebDAV
    API = "api"                   # API externe


class ScheduleFrequency(str, Enum):
    """Frequence de planification."""
    ONCE = "once"                 # Une seule fois
    HOURLY = "hourly"             # Toutes les heures
    DAILY = "daily"               # Quotidien
    WEEKLY = "weekly"             # Hebdomadaire
    MONTHLY = "monthly"           # Mensuel
    CRON = "cron"                 # Expression cron personnalisee


class TransformationType(str, Enum):
    """Types de transformation."""
    NONE = "none"                 # Aucune
    UPPERCASE = "uppercase"       # Majuscules
    LOWERCASE = "lowercase"       # Minuscules
    TRIM = "trim"                 # Supprimer espaces
    REPLACE = "replace"           # Remplacement
    FORMAT_DATE = "format_date"   # Formater date
    FORMAT_NUMBER = "format_number"  # Formater nombre
    LOOKUP = "lookup"             # Recherche dans table
    FORMULA = "formula"           # Formule calculee
    CONCAT = "concat"             # Concatenation
    SPLIT = "split"               # Decoupage
    DEFAULT = "default"           # Valeur par defaut
    MAP = "map"                   # Mapping de valeurs
    CUSTOM = "custom"             # Script personnalise


class ValidationSeverity(str, Enum):
    """Severite des erreurs de validation."""
    ERROR = "error"               # Erreur bloquante
    WARNING = "warning"           # Avertissement
    INFO = "info"                 # Information


class EntityTargetType(str, Enum):
    """Types d'entites cibles pour import/export."""
    CONTACT = "contact"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PRODUCT = "product"
    INVOICE = "invoice"
    ORDER = "order"
    PAYMENT = "payment"
    JOURNAL_ENTRY = "journal_entry"
    ACCOUNT = "account"
    EMPLOYEE = "employee"
    PROJECT = "project"
    TASK = "task"
    EXPENSE = "expense"
    INVENTORY = "inventory"
    CUSTOM = "custom"


class NotificationType(str, Enum):
    """Types de notification."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationEvent(str, Enum):
    """Evenements declenchant une notification."""
    ON_START = "on_start"           # Debut d'execution
    ON_COMPLETE = "on_complete"     # Fin avec succes
    ON_ERROR = "on_error"           # Erreur
    ON_WARNING = "on_warning"       # Avertissements
    ON_PARTIAL = "on_partial"       # Succes partiel


class FieldDataType(str, Enum):
    """Types de donnees pour les champs."""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    UUID = "uuid"
    JSON = "json"
    ARRAY = "array"


class ValidationRuleType(str, Enum):
    """Types de regles de validation."""
    REQUIRED = "required"           # Champ requis
    UNIQUE = "unique"               # Valeur unique
    REGEX = "regex"                 # Expression reguliere
    MIN_LENGTH = "min_length"       # Longueur minimale
    MAX_LENGTH = "max_length"       # Longueur maximale
    MIN_VALUE = "min_value"         # Valeur minimale
    MAX_VALUE = "max_value"         # Valeur maximale
    ENUM = "enum"                   # Valeur dans une liste
    REFERENCE = "reference"         # Reference externe
    FORMAT = "format"               # Format specifique
    CUSTOM = "custom"               # Validation personnalisee


# ============== Modeles ==============

class ExchangeProfile(Base):
    """
    Profil d'import/export reutilisable.
    Definit le format, le mapping et les options.
    """
    __tablename__ = "dataexchange_profiles"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Type et format
    exchange_type = Column(String(20), nullable=False)  # import/export
    file_format = Column(String(20), nullable=False)
    entity_type = Column(String(50), nullable=False)    # Type d'entite cible

    # Options de fichier
    file_encoding = Column(String(20), default="utf-8")
    csv_delimiter = Column(String(5), default=",")
    csv_quote_char = Column(String(5), default='"')
    csv_has_header = Column(Boolean, default=True)
    excel_sheet_name = Column(String(100), nullable=True)
    excel_start_row = Column(Integer, default=1)
    xml_root_element = Column(String(100), nullable=True)
    xml_row_element = Column(String(100), nullable=True)
    json_root_path = Column(String(255), nullable=True)

    # Options avancees
    skip_empty_rows = Column(Boolean, default=True)
    trim_values = Column(Boolean, default=True)
    date_format = Column(String(50), default="%Y-%m-%d")
    decimal_separator = Column(String(5), default=".")
    thousand_separator = Column(String(5), default="")
    null_value = Column(String(20), default="")

    # Export options
    include_header = Column(Boolean, default=True)
    export_template = Column(Text, nullable=True)  # Template Jinja2 pour exports

    # Comportement
    on_duplicate = Column(String(20), default="update")  # skip, update, error, create_new
    on_error = Column(String(20), default="continue")    # continue, stop, rollback
    batch_size = Column(Integer, default=100)
    enable_rollback = Column(Boolean, default=True)

    # Validation
    validate_before_import = Column(Boolean, default=True)
    strict_validation = Column(Boolean, default=False)

    # Metadata
    is_system = Column(Boolean, default=False)  # Profil systeme non modifiable
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    field_mappings = relationship("FieldMapping", back_populates="profile", cascade="all, delete-orphan")
    validations = relationship("ValidationRule", back_populates="profile", cascade="all, delete-orphan")
    transformations = relationship("Transformation", back_populates="profile", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_dataexchange_profiles_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_dataexchange_profiles_tenant_type", "tenant_id", "exchange_type"),
        Index("ix_dataexchange_profiles_tenant_entity", "tenant_id", "entity_type"),
        Index("ix_dataexchange_profiles_active", "tenant_id", "is_active", "is_deleted"),
    )


class FieldMapping(Base):
    """
    Mapping entre champ source et champ cible.
    """
    __tablename__ = "dataexchange_field_mappings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    profile_id = Column(UniversalUUID(), ForeignKey("dataexchange_profiles.id"), nullable=False)

    # Champs
    source_field = Column(String(255), nullable=False)   # Nom dans le fichier source
    target_field = Column(String(255), nullable=False)   # Nom dans l'entite cible
    source_column_index = Column(Integer, nullable=True) # Index de colonne (CSV/Excel)

    # Type de donnees
    source_type = Column(String(50), default="string")
    target_type = Column(String(50), default="string")

    # Options
    is_required = Column(Boolean, default=False)
    is_key = Column(Boolean, default=False)              # Champ de deduplication
    default_value = Column(Text, nullable=True)
    format_pattern = Column(String(255), nullable=True)  # Pattern de format (dates, etc.)

    # Transformation
    transformation_type = Column(String(50), default="none")
    transformation_config = Column(JSON, default=dict)   # Config de transformation

    # Ordre
    sort_order = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    profile = relationship("ExchangeProfile", back_populates="field_mappings")

    __table_args__ = (
        Index("ix_field_mappings_profile", "profile_id"),
        Index("ix_field_mappings_tenant", "tenant_id"),
    )


class ValidationRule(Base):
    """
    Regle de validation pour un profil.
    """
    __tablename__ = "dataexchange_validation_rules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    profile_id = Column(UniversalUUID(), ForeignKey("dataexchange_profiles.id"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Cible
    target_field = Column(String(255), nullable=True)    # Champ concerne (null = tout)

    # Regle
    rule_type = Column(String(50), nullable=False)       # required, regex, range, unique, lookup, custom
    rule_config = Column(JSON, default=dict)             # Configuration de la regle

    # Severite et action
    severity = Column(String(20), default="error")       # error, warning, info
    stop_on_fail = Column(Boolean, default=False)

    # Message d'erreur
    error_message = Column(String(500), nullable=True)
    error_message_template = Column(String(500), nullable=True)  # Avec placeholders

    # Activation
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    profile = relationship("ExchangeProfile", back_populates="validations")

    __table_args__ = (
        Index("ix_validation_rules_profile", "profile_id"),
        Index("ix_validation_rules_tenant", "tenant_id"),
    )


class Transformation(Base):
    """
    Transformation de donnees appliquee lors de l'import/export.
    """
    __tablename__ = "dataexchange_transformations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    profile_id = Column(UniversalUUID(), ForeignKey("dataexchange_profiles.id"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Type et configuration
    transformation_type = Column(String(50), nullable=False)
    source_fields = Column(JSON, default=list)           # Champs source
    target_field = Column(String(255), nullable=True)    # Champ cible
    config = Column(JSON, default=dict)                  # Configuration

    # Script personnalise (pour type=custom)
    script = Column(Text, nullable=True)                 # Expression Python securisee

    # Options
    apply_on = Column(String(20), default="row")         # row, cell, file
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    profile = relationship("ExchangeProfile", back_populates="transformations")

    __table_args__ = (
        Index("ix_transformations_profile", "profile_id"),
        Index("ix_transformations_tenant", "tenant_id"),
    )


class FileConnector(Base):
    """
    Connecteur de fichiers (FTP, S3, etc.).
    """
    __tablename__ = "dataexchange_file_connectors"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Type et configuration
    connector_type = Column(String(20), nullable=False)

    # Configuration connexion (chiffree)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    username = Column(String(255), nullable=True)
    password_encrypted = Column(Text, nullable=True)      # Chiffre
    private_key_encrypted = Column(Text, nullable=True)   # Chiffre (SFTP)

    # S3/Cloud
    bucket_name = Column(String(255), nullable=True)
    region = Column(String(50), nullable=True)
    access_key_encrypted = Column(Text, nullable=True)
    secret_key_encrypted = Column(Text, nullable=True)
    endpoint_url = Column(String(500), nullable=True)     # Pour S3 compatible

    # Paths
    base_path = Column(String(500), default="/")
    input_path = Column(String(500), nullable=True)       # Chemin pour imports
    output_path = Column(String(500), nullable=True)      # Chemin pour exports
    archive_path = Column(String(500), nullable=True)     # Chemin d'archivage
    error_path = Column(String(500), nullable=True)       # Chemin pour fichiers en erreur

    # Options
    passive_mode = Column(Boolean, default=True)          # FTP
    verify_ssl = Column(Boolean, default=True)
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=5)

    # Pattern de fichiers
    file_pattern = Column(String(255), nullable=True)     # Glob pattern
    archive_after_process = Column(Boolean, default=True)
    delete_after_process = Column(Boolean, default=False)

    # Etat
    is_active = Column(Boolean, default=True)
    last_connected_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    consecutive_errors = Column(Integer, default=0)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_file_connectors_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_file_connectors_tenant_type", "tenant_id", "connector_type"),
        Index("ix_file_connectors_active", "tenant_id", "is_active", "is_deleted"),
    )


class ScheduledExchange(Base):
    """
    Planification d'import/export automatique.
    """
    __tablename__ = "dataexchange_scheduled"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Liens
    profile_id = Column(UniversalUUID(), ForeignKey("dataexchange_profiles.id"), nullable=False)
    connector_id = Column(UniversalUUID(), ForeignKey("dataexchange_file_connectors.id"), nullable=True)

    # Planification
    frequency = Column(String(20), nullable=False)
    cron_expression = Column(String(100), nullable=True)  # Pour CRON
    scheduled_time = Column(String(10), nullable=True)    # HH:MM
    scheduled_day = Column(Integer, nullable=True)        # 0-6 (lundi-dimanche)
    scheduled_day_of_month = Column(Integer, nullable=True)
    timezone = Column(String(50), default="Europe/Paris")

    # Fichier
    source_path = Column(String(500), nullable=True)      # Import: chemin source
    destination_path = Column(String(500), nullable=True) # Export: chemin destination
    file_naming_pattern = Column(String(255), nullable=True)  # Pattern avec {date}, etc.

    # Notifications
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notification_config = Column(JSON, default=dict)

    # Etat
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)

    # Options
    max_retries = Column(Integer, default=3)
    retry_delay_minutes = Column(Integer, default=15)
    pause_on_consecutive_failures = Column(Integer, default=5)  # Pause apres X echecs

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    profile = relationship("ExchangeProfile")
    connector = relationship("FileConnector")

    __table_args__ = (
        Index("ix_scheduled_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_scheduled_tenant_active", "tenant_id", "is_active", "is_deleted"),
        Index("ix_scheduled_next_run", "next_run_at", "is_active"),
    )


class ExchangeJob(Base):
    """
    Job d'import/export (execution).
    """
    __tablename__ = "dataexchange_jobs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Reference
    reference = Column(String(100), nullable=False, index=True)

    # Liens
    profile_id = Column(UniversalUUID(), ForeignKey("dataexchange_profiles.id"), nullable=False)
    scheduled_id = Column(UniversalUUID(), ForeignKey("dataexchange_scheduled.id"), nullable=True)
    connector_id = Column(UniversalUUID(), ForeignKey("dataexchange_file_connectors.id"), nullable=True)

    # Type
    exchange_type = Column(String(20), nullable=False)   # import/export
    entity_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")

    # Fichier source/destination
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_format = Column(String(20), nullable=True)

    # Resultats fichier de sortie (export)
    output_file_name = Column(String(255), nullable=True)
    output_file_path = Column(String(1000), nullable=True)
    output_file_size = Column(BigInteger, nullable=True)

    # Statistiques
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    created_count = Column(Integer, default=0)
    updated_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)

    # Progression
    progress_percent = Column(Numeric(5, 2), default=0)
    current_phase = Column(String(50), nullable=True)   # reading, validating, processing, finalizing

    # Timestamps
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Erreur globale
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default=dict)

    # Rollback
    rollback_data = Column(JSON, nullable=True)          # Donnees pour rollback
    rolled_back_at = Column(DateTime, nullable=True)
    rolled_back_by = Column(UniversalUUID(), nullable=True)

    # Options execution
    options = Column(JSON, default=dict)                 # Options specifiques
    triggered_by = Column(String(50), default="manual")  # manual, scheduled, api

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    profile = relationship("ExchangeProfile")
    scheduled = relationship("ScheduledExchange")
    connector = relationship("FileConnector")
    logs = relationship("ExchangeLog", back_populates="job", cascade="all, delete-orphan")
    errors = relationship("ExchangeError", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_tenant_reference", "tenant_id", "reference"),
        Index("ix_jobs_tenant_status", "tenant_id", "status"),
        Index("ix_jobs_tenant_type", "tenant_id", "exchange_type"),
        Index("ix_jobs_created", "tenant_id", "created_at"),
        Index("ix_jobs_profile", "profile_id"),
    )


class ExchangeLog(Base):
    """
    Log detaille d'un echange (par ligne).
    """
    __tablename__ = "dataexchange_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    job_id = Column(UniversalUUID(), ForeignKey("dataexchange_jobs.id"), nullable=False)

    # Position dans le fichier
    row_number = Column(Integer, nullable=False)

    # Action et resultat
    action = Column(String(20), nullable=False)          # create, update, skip, error
    entity_id = Column(UniversalUUID(), nullable=True)   # ID de l'entite creee/modifiee
    entity_reference = Column(String(255), nullable=True)

    # Donnees
    source_data = Column(JSON, default=dict)             # Donnees source (ligne)
    target_data = Column(JSON, default=dict)             # Donnees transformees
    changes = Column(JSON, default=dict)                 # Changements effectues

    # Resultat
    success = Column(Boolean, default=True)
    message = Column(Text, nullable=True)

    # Timing
    processing_time_ms = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relations
    job = relationship("ExchangeJob", back_populates="logs")

    __table_args__ = (
        Index("ix_logs_job", "job_id"),
        Index("ix_logs_tenant", "tenant_id"),
        Index("ix_logs_job_row", "job_id", "row_number"),
        Index("ix_logs_job_action", "job_id", "action"),
    )


class ExchangeError(Base):
    """
    Erreur de validation ou traitement.
    """
    __tablename__ = "dataexchange_errors"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    job_id = Column(UniversalUUID(), ForeignKey("dataexchange_jobs.id"), nullable=False)

    # Position
    row_number = Column(Integer, nullable=True)
    column_name = Column(String(255), nullable=True)
    field_name = Column(String(255), nullable=True)

    # Erreur
    error_code = Column(String(50), nullable=False)
    error_type = Column(String(50), nullable=False)      # validation, transformation, database, system
    severity = Column(String(20), default="error")
    message = Column(Text, nullable=False)

    # Contexte
    source_value = Column(Text, nullable=True)
    expected_value = Column(Text, nullable=True)
    rule_code = Column(String(50), nullable=True)        # Code de la regle de validation

    # Donnees completes de la ligne
    row_data = Column(JSON, default=dict)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relations
    job = relationship("ExchangeJob", back_populates="errors")

    __table_args__ = (
        Index("ix_errors_job", "job_id"),
        Index("ix_errors_tenant", "tenant_id"),
        Index("ix_errors_job_severity", "job_id", "severity"),
        Index("ix_errors_job_row", "job_id", "row_number"),
    )


class ExchangeHistory(Base):
    """
    Historique des echanges pour statistiques et audit.
    """
    __tablename__ = "dataexchange_history"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    job_id = Column(UniversalUUID(), nullable=False, index=True)

    # Resume
    exchange_type = Column(String(20), nullable=False)
    entity_type = Column(String(50), nullable=False)
    profile_code = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False)

    # Fichier
    file_name = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_format = Column(String(20), nullable=True)

    # Statistiques
    total_rows = Column(Integer, default=0)
    created_count = Column(Integer, default=0)
    updated_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Declencheur
    triggered_by = Column(String(50), nullable=True)
    executed_by = Column(UniversalUUID(), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_history_tenant_date", "tenant_id", "created_at"),
        Index("ix_history_tenant_type", "tenant_id", "exchange_type"),
        Index("ix_history_tenant_entity", "tenant_id", "entity_type"),
        Index("ix_history_job", "job_id"),
    )


class NotificationConfig(Base):
    """
    Configuration des notifications pour les echanges.
    """
    __tablename__ = "dataexchange_notification_configs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Type et configuration
    notification_type = Column(String(20), nullable=False)

    # Email
    email_to = Column(JSON, default=list)                # Liste d'emails
    email_cc = Column(JSON, default=list)
    email_template = Column(Text, nullable=True)

    # Webhook
    webhook_url = Column(String(500), nullable=True)
    webhook_headers = Column(JSON, default=dict)
    webhook_method = Column(String(10), default="POST")

    # Slack/Teams
    channel_id = Column(String(255), nullable=True)
    bot_token_encrypted = Column(Text, nullable=True)

    # Declencheurs
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notify_on_warning = Column(Boolean, default=False)
    min_error_count = Column(Integer, default=0)         # Notifier si >= X erreurs

    # Etat
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_notif_config_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_notif_config_tenant_active", "tenant_id", "is_active", "is_deleted"),
    )


class LookupTable(Base):
    """
    Table de correspondance pour les transformations lookup.
    """
    __tablename__ = "dataexchange_lookup_tables"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Donnees
    entries = Column(JSON, default=dict)                 # {source_value: target_value}
    case_sensitive = Column(Boolean, default=False)
    default_value = Column(String(255), nullable=True)

    # Etat
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index("ix_lookup_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_lookup_tenant_active", "tenant_id", "is_active", "is_deleted"),
    )
