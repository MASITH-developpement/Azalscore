"""
AZALS MODULE GAP-086 - Modeles Integration
============================================

Modeles SQLAlchemy pour les integrations tierces.
Inspire de Zapier, Make, Microsoft Dynamics 365, Odoo.

REGLES:
- tenant_id obligatoire sur tous les modeles
- Soft delete avec is_deleted, deleted_at, deleted_by
- Audit complet avec created_at, updated_at, created_by, updated_by
- Versioning pour les configurations
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
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
    func,
)
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID, JSONB
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class ConnectorType(str, enum.Enum):
    """Types de connecteurs disponibles."""
    # Productivite Google
    GOOGLE_DRIVE = "google_drive"
    GOOGLE_SHEETS = "google_sheets"
    GOOGLE_CALENDAR = "google_calendar"
    GMAIL = "gmail"

    # Microsoft
    MICROSOFT_365 = "microsoft_365"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    OUTLOOK = "outlook"
    TEAMS = "teams"
    ONEDRIVE = "onedrive"
    SHAREPOINT = "sharepoint"

    # Communication
    SLACK = "slack"
    DISCORD = "discord"
    TWILIO = "twilio"
    SENDGRID = "sendgrid"

    # CRM
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO_CRM = "zoho_crm"

    # Comptabilite
    SAGE = "sage"
    CEGID = "cegid"
    PENNYLANE = "pennylane"
    QUICKBOOKS = "quickbooks"
    XERO = "xero"

    # ERP
    ODOO = "odoo"
    SAP = "sap"
    NETSUITE = "netsuite"

    # E-commerce
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    PRESTASHOP = "prestashop"
    MAGENTO = "magento"

    # Paiement
    STRIPE = "stripe"
    PAYPAL = "paypal"
    GOCARDLESS = "gocardless"
    MOLLIE = "mollie"

    # Banque / Fintech
    QONTO = "qonto"
    SWAN = "swan"
    BRIDGE = "bridge"
    PLAID = "plaid"

    # Marketing
    MAILCHIMP = "mailchimp"
    BREVO = "brevo"
    KLAVIYO = "klaviyo"
    ACTIVECAMPAIGN = "activecampaign"

    # Stockage
    DROPBOX = "dropbox"
    AWS_S3 = "aws_s3"

    # Automatisation
    ZAPIER = "zapier"
    MAKE = "make"
    N8N = "n8n"

    # Custom / API generique
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class AuthType(str, enum.Enum):
    """Types d'authentification."""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    OAUTH1 = "oauth1"
    BASIC = "basic"
    BEARER = "bearer"
    HMAC = "hmac"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    CUSTOM = "custom"


class ConnectionStatus(str, enum.Enum):
    """Statut de connexion."""
    PENDING = "pending"
    CONFIGURING = "configuring"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"


class SyncDirection(str, enum.Enum):
    """Direction de synchronisation."""
    INBOUND = "inbound"      # Externe -> AZALSCORE
    OUTBOUND = "outbound"    # AZALSCORE -> Externe
    BIDIRECTIONAL = "bidirectional"


class SyncMode(str, enum.Enum):
    """Mode de synchronisation."""
    REALTIME = "realtime"    # Webhook / temps reel
    SCHEDULED = "scheduled"  # Planifie (cron)
    MANUAL = "manual"        # Manuel
    ON_DEMAND = "on_demand"  # A la demande via API


class SyncFrequency(str, enum.Enum):
    """Frequence de synchronisation planifiee."""
    EVERY_MINUTE = "every_minute"
    EVERY_5_MINUTES = "every_5_minutes"
    EVERY_15_MINUTES = "every_15_minutes"
    EVERY_30_MINUTES = "every_30_minutes"
    HOURLY = "hourly"
    EVERY_2_HOURS = "every_2_hours"
    EVERY_6_HOURS = "every_6_hours"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class SyncStatus(str, enum.Enum):
    """Statut d'une execution de synchronisation."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class ConflictResolution(str, enum.Enum):
    """Strategies de resolution de conflits."""
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    NEWEST_WINS = "newest_wins"
    OLDEST_WINS = "oldest_wins"
    MANUAL = "manual"
    MERGE = "merge"
    SKIP = "skip"


class EntityType(str, enum.Enum):
    """Types d'entites synchronisables."""
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    CONTACT = "contact"
    PRODUCT = "product"
    ORDER = "order"
    INVOICE = "invoice"
    PAYMENT = "payment"
    TRANSACTION = "transaction"
    LEAD = "lead"
    OPPORTUNITY = "opportunity"
    PROJECT = "project"
    TASK = "task"
    TICKET = "ticket"
    FILE = "file"
    EVENT = "event"
    MESSAGE = "message"
    CUSTOM = "custom"


class WebhookDirection(str, enum.Enum):
    """Direction du webhook."""
    INBOUND = "inbound"    # Reception (entrant)
    OUTBOUND = "outbound"  # Envoi (sortant)


class WebhookStatus(str, enum.Enum):
    """Statut webhook."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class TransformationType(str, enum.Enum):
    """Types de transformation de donnees."""
    DIRECT_MAP = "direct_map"
    EXPRESSION = "expression"
    LOOKUP = "lookup"
    TEMPLATE = "template"
    SCRIPT = "script"
    CONDITIONAL = "conditional"


class LogLevel(str, enum.Enum):
    """Niveau de log."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(str, enum.Enum):
    """Statut de sante."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ============================================================================
# MODELES
# ============================================================================

class ConnectorDefinition(Base):
    """
    Definition d'un connecteur preconfigure.
    Contient les metadonnees et configuration par defaut.
    """
    __tablename__ = "integration_connector_definitions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)

    # Identification
    connector_type = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # crm, accounting, ecommerce...

    # Visuel
    icon_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    color = Column(String(20), nullable=True)  # Couleur de marque

    # Configuration
    auth_type = Column(Enum(AuthType), nullable=False)
    base_url = Column(String(500), nullable=True)
    api_version = Column(String(20), nullable=True)

    # OAuth2
    oauth_authorize_url = Column(String(500), nullable=True)
    oauth_token_url = Column(String(500), nullable=True)
    oauth_scopes = Column(JSONB, default=list)  # Liste des scopes disponibles
    oauth_pkce_required = Column(Boolean, default=False)

    # Champs requis/optionnels pour config
    required_fields = Column(JSONB, default=list)  # ["api_key", "shop_domain"]
    optional_fields = Column(JSONB, default=list)

    # Entites supportees
    supported_entities = Column(JSONB, default=list)  # ["customer", "order"]
    supported_directions = Column(JSONB, default=list)  # ["inbound", "outbound"]

    # Rate limits
    rate_limit_requests = Column(Integer, default=60)  # Par minute
    rate_limit_daily = Column(Integer, nullable=True)

    # Webhooks
    supports_webhooks = Column(Boolean, default=False)
    webhook_events = Column(JSONB, default=list)

    # Documentation
    documentation_url = Column(String(500), nullable=True)
    setup_guide_url = Column(String(500), nullable=True)

    # Statut
    is_active = Column(Boolean, default=True)
    is_beta = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)

    # Metadata
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_connector_def_type', 'connector_type'),
        Index('idx_connector_def_category', 'category'),
        Index('idx_connector_def_active', 'is_active'),
    )


class Connection(Base):
    """
    Connexion configuree a un service externe.
    Une connexion = une instance de connecteur pour un tenant.
    """
    __tablename__ = "integration_connections"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    connector_type = Column(String(50), nullable=False)

    # Configuration
    auth_type = Column(Enum(AuthType), nullable=False)
    base_url = Column(String(500), nullable=True)
    api_version = Column(String(20), nullable=True)

    # Credentials (chiffrees en production)
    credentials = Column(JSONB, default=dict)  # api_key, username, password...
    custom_headers = Column(JSONB, default=dict)
    settings = Column(JSONB, default=dict)  # Parametres specifiques

    # OAuth2 Tokens (chiffres en production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    token_scope = Column(Text, nullable=True)

    # Etat
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING, nullable=False)
    last_connected_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Sante / Monitoring
    health_status = Column(Enum(HealthStatus), default=HealthStatus.UNKNOWN)
    last_health_check = Column(DateTime, nullable=True)
    consecutive_errors = Column(Integer, default=0)
    success_rate_24h = Column(Float, nullable=True)
    avg_response_time_ms = Column(Integer, nullable=True)

    # Rate limiting
    rate_limit_remaining = Column(Integer, nullable=True)
    rate_limit_reset_at = Column(DateTime, nullable=True)

    # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    mappings = relationship("DataMapping", back_populates="connection", cascade="all, delete-orphan")
    sync_configs = relationship("SyncConfiguration", back_populates="connection", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="connection", cascade="all, delete-orphan")
    executions = relationship("SyncExecution", back_populates="connection")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_connection_tenant_code'),
        Index('idx_connection_tenant', 'tenant_id'),
        Index('idx_connection_type', 'connector_type'),
        Index('idx_connection_status', 'status'),
        Index('idx_connection_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_connection_not_deleted', 'tenant_id', 'is_deleted'),
    )


class DataMapping(Base):
    """
    Mapping des donnees entre AZALSCORE et le systeme externe.
    Definit comment transformer les champs.
    """
    __tablename__ = "integration_data_mappings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    connection_id = Column(UniversalUUID(), ForeignKey('integration_connections.id', ondelete='CASCADE'), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Entites
    entity_type = Column(Enum(EntityType), nullable=False)
    source_entity = Column(String(100), nullable=False)  # Nom dans systeme source
    target_entity = Column(String(100), nullable=False)  # Nom dans AZALSCORE
    direction = Column(Enum(SyncDirection), default=SyncDirection.BIDIRECTIONAL)

    # Mappings de champs
    # Format: [{"source": "field1", "target": "field2", "transform": "...", "required": true}]
    field_mappings = Column(JSONB, default=list)

    # Cles de deduplication
    source_key_field = Column(String(100), nullable=True)  # Champ cle dans source
    target_key_field = Column(String(100), nullable=True)  # Champ cle dans cible

    # Filtres
    source_filter = Column(JSONB, nullable=True)  # Filtre sur donnees source
    target_filter = Column(JSONB, nullable=True)  # Filtre sur donnees cible

    # Transformation avancee
    pre_transform_script = Column(Text, nullable=True)   # Script avant mapping
    post_transform_script = Column(Text, nullable=True)  # Script apres mapping

    # Configuration
    conflict_resolution = Column(Enum(ConflictResolution), default=ConflictResolution.NEWEST_WINS)
    batch_size = Column(Integer, default=100)

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    connection = relationship("Connection", back_populates="mappings")
    sync_configs = relationship("SyncConfiguration", back_populates="mapping")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'connection_id', 'code', name='uq_mapping_code'),
        Index('idx_mapping_tenant', 'tenant_id'),
        Index('idx_mapping_connection', 'connection_id'),
        Index('idx_mapping_entity', 'entity_type'),
    )


class SyncConfiguration(Base):
    """
    Configuration d'une synchronisation.
    Definit quand et comment synchroniser.
    """
    __tablename__ = "integration_sync_configurations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    connection_id = Column(UniversalUUID(), ForeignKey('integration_connections.id', ondelete='CASCADE'), nullable=False)
    mapping_id = Column(UniversalUUID(), ForeignKey('integration_data_mappings.id', ondelete='CASCADE'), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Direction et mode
    direction = Column(Enum(SyncDirection), nullable=False)
    sync_mode = Column(Enum(SyncMode), default=SyncMode.SCHEDULED)

    # Planification (pour mode SCHEDULED)
    frequency = Column(Enum(SyncFrequency), nullable=True)
    cron_expression = Column(String(100), nullable=True)  # Cron custom
    timezone = Column(String(50), default='Europe/Paris')

    # Execution
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(Enum(SyncStatus), nullable=True)

    # Retry
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    # Delta sync
    use_delta_sync = Column(Boolean, default=True)
    delta_field = Column(String(100), nullable=True)  # Champ pour delta (updated_at)
    last_delta_value = Column(Text, nullable=True)    # Derniere valeur du delta

    # Notifications
    notify_on_error = Column(Boolean, default=True)
    notify_on_success = Column(Boolean, default=False)
    notification_emails = Column(JSONB, default=list)
    notification_webhook_url = Column(String(500), nullable=True)

    # Statut
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    pause_reason = Column(Text, nullable=True)

    # Statistiques
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    total_records_synced = Column(Integer, default=0)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    connection = relationship("Connection", back_populates="sync_configs")
    mapping = relationship("DataMapping", back_populates="sync_configs")
    executions = relationship("SyncExecution", back_populates="config", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_sync_config_code'),
        Index('idx_sync_config_tenant', 'tenant_id'),
        Index('idx_sync_config_connection', 'connection_id'),
        Index('idx_sync_config_next_run', 'next_run_at'),
        Index('idx_sync_config_active', 'is_active', 'is_paused'),
    )


class SyncExecution(Base):
    """
    Execution d'une synchronisation.
    Historique des jobs de synchronisation.
    """
    __tablename__ = "integration_sync_executions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    connection_id = Column(UniversalUUID(), ForeignKey('integration_connections.id', ondelete='SET NULL'), nullable=True)
    config_id = Column(UniversalUUID(), ForeignKey('integration_sync_configurations.id', ondelete='SET NULL'), nullable=True)

    # Identification
    execution_number = Column(String(50), nullable=False)  # Format: EXE-YYYYMMDD-XXXXX

    # Configuration au moment de l'execution
    direction = Column(Enum(SyncDirection), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)

    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Statut
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING, nullable=False)

    # Statistiques
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    created_records = Column(Integer, default=0)
    updated_records = Column(Integer, default=0)
    deleted_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)

    # Progression
    progress_percent = Column(Float, default=0)
    current_step = Column(String(100), nullable=True)

    # Erreurs
    error_count = Column(Integer, default=0)
    errors = Column(JSONB, default=list)  # Liste des erreurs
    last_error = Column(Text, nullable=True)

    # Retry
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False)
    original_execution_id = Column(UniversalUUID(), nullable=True)

    # Delta sync
    delta_start_value = Column(Text, nullable=True)
    delta_end_value = Column(Text, nullable=True)

    # Metadata
    triggered_by = Column(String(50), nullable=True)  # manual, scheduled, webhook
    triggered_by_user = Column(UniversalUUID(), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    connection = relationship("Connection", back_populates="executions")
    config = relationship("SyncConfiguration", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    conflicts = relationship("SyncConflict", back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_execution_tenant', 'tenant_id'),
        Index('idx_execution_connection', 'connection_id'),
        Index('idx_execution_config', 'config_id'),
        Index('idx_execution_status', 'status'),
        Index('idx_execution_started', 'started_at'),
        Index('idx_execution_tenant_status', 'tenant_id', 'status'),
    )


class ExecutionLog(Base):
    """
    Log detaille d'une execution.
    Trace chaque enregistrement traite.
    """
    __tablename__ = "integration_execution_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    execution_id = Column(UniversalUUID(), ForeignKey('integration_sync_executions.id', ondelete='CASCADE'), nullable=False)

    # Niveau et message
    level = Column(Enum(LogLevel), default=LogLevel.INFO, nullable=False)
    message = Column(Text, nullable=False)

    # Enregistrement concerne
    source_id = Column(String(255), nullable=True)
    target_id = Column(String(255), nullable=True)
    entity_type = Column(String(50), nullable=True)

    # Action
    action = Column(String(50), nullable=True)  # create, update, delete, skip, error

    # Donnees
    source_data = Column(JSONB, nullable=True)
    target_data = Column(JSONB, nullable=True)
    changes = Column(JSONB, nullable=True)  # Diff des modifications

    # Erreur
    error_code = Column(String(50), nullable=True)
    error_details = Column(JSONB, nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Performance
    processing_time_ms = Column(Integer, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    # Relations
    execution = relationship("SyncExecution", back_populates="logs")

    __table_args__ = (
        Index('idx_exec_log_tenant', 'tenant_id'),
        Index('idx_exec_log_execution', 'execution_id'),
        Index('idx_exec_log_level', 'level'),
        Index('idx_exec_log_source', 'source_id'),
        Index('idx_exec_log_timestamp', 'timestamp'),
    )


class SyncConflict(Base):
    """
    Conflit detecte lors d'une synchronisation.
    Necessite resolution manuelle ou automatique.
    """
    __tablename__ = "integration_sync_conflicts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    execution_id = Column(UniversalUUID(), ForeignKey('integration_sync_executions.id', ondelete='CASCADE'), nullable=False)

    # Enregistrements en conflit
    source_id = Column(String(255), nullable=False)
    target_id = Column(String(255), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)

    # Donnees en conflit
    source_data = Column(JSONB, default=dict)
    target_data = Column(JSONB, default=dict)
    conflicting_fields = Column(JSONB, default=list)  # Champs en conflit

    # Resolution
    resolution_strategy = Column(Enum(ConflictResolution), nullable=True)
    resolved_data = Column(JSONB, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UniversalUUID(), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Statut
    is_resolved = Column(Boolean, default=False)
    is_ignored = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    execution = relationship("SyncExecution", back_populates="conflicts")

    __table_args__ = (
        Index('idx_conflict_tenant', 'tenant_id'),
        Index('idx_conflict_execution', 'execution_id'),
        Index('idx_conflict_resolved', 'is_resolved'),
        Index('idx_conflict_tenant_pending', 'tenant_id', 'is_resolved'),
    )


class Webhook(Base):
    """
    Configuration de webhook entrant ou sortant.
    """
    __tablename__ = "integration_webhooks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    connection_id = Column(UniversalUUID(), ForeignKey('integration_connections.id', ondelete='CASCADE'), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Direction
    direction = Column(Enum(WebhookDirection), nullable=False)

    # Configuration entrant
    endpoint_path = Column(String(255), nullable=True)  # Path unique pour recevoir
    secret_key = Column(String(255), nullable=True)     # Pour validation HMAC
    signature_header = Column(String(100), nullable=True)  # Header contenant signature
    signature_algorithm = Column(String(20), nullable=True)  # sha256, sha512...

    # Configuration sortant
    target_url = Column(String(500), nullable=True)
    http_method = Column(String(10), default='POST')
    headers = Column(JSONB, default=dict)
    auth_type = Column(Enum(AuthType), nullable=True)
    auth_credentials = Column(JSONB, default=dict)

    # Evenements
    subscribed_events = Column(JSONB, default=list)  # ["order.created", "customer.updated"]

    # Payload
    payload_template = Column(Text, nullable=True)  # Template du payload
    include_metadata = Column(Boolean, default=True)

    # Retry (sortant)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=30)
    timeout_seconds = Column(Integer, default=30)

    # Statut
    status = Column(Enum(WebhookStatus), default=WebhookStatus.ACTIVE)
    is_active = Column(Boolean, default=True)

    # Statistiques
    last_triggered_at = Column(DateTime, nullable=True)
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    connection = relationship("Connection", back_populates="webhooks")
    logs = relationship("WebhookLog", back_populates="webhook", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_webhook_code'),
        UniqueConstraint('tenant_id', 'endpoint_path', name='uq_webhook_path'),
        Index('idx_webhook_tenant', 'tenant_id'),
        Index('idx_webhook_connection', 'connection_id'),
        Index('idx_webhook_direction', 'direction'),
        Index('idx_webhook_path', 'endpoint_path'),
    )


class WebhookLog(Base):
    """
    Log des appels webhook.
    """
    __tablename__ = "integration_webhook_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    webhook_id = Column(UniversalUUID(), ForeignKey('integration_webhooks.id', ondelete='CASCADE'), nullable=False)

    # Direction
    direction = Column(Enum(WebhookDirection), nullable=False)

    # Request
    request_url = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_headers = Column(JSONB, default=dict)
    request_body = Column(Text, nullable=True)

    # Response
    response_status_code = Column(Integer, nullable=True)
    response_headers = Column(JSONB, default=dict)
    response_body = Column(Text, nullable=True)

    # Evenement
    event_type = Column(String(100), nullable=True)
    event_id = Column(String(255), nullable=True)

    # Performance
    duration_ms = Column(Integer, nullable=True)

    # Resultat
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Retry
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False)

    # IP source (pour entrant)
    source_ip = Column(String(50), nullable=True)

    # Timestamp
    timestamp = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    # Relations
    webhook = relationship("Webhook", back_populates="logs")

    __table_args__ = (
        Index('idx_webhook_log_tenant', 'tenant_id'),
        Index('idx_webhook_log_webhook', 'webhook_id'),
        Index('idx_webhook_log_timestamp', 'timestamp'),
        Index('idx_webhook_log_success', 'success'),
    )


class TransformationRule(Base):
    """
    Regle de transformation de donnees reutilisable.
    """
    __tablename__ = "integration_transformation_rules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Type
    transformation_type = Column(Enum(TransformationType), nullable=False)

    # Configuration
    # Format depend du type:
    # - DIRECT_MAP: null
    # - EXPRESSION: {"expression": "value.upper()"}
    # - LOOKUP: {"table": "...", "key": "...", "value": "..."}
    # - TEMPLATE: {"template": "Hello {{name}}"}
    # - SCRIPT: {"language": "python", "code": "..."}
    # - CONDITIONAL: {"conditions": [...], "default": "..."}
    config = Column(JSONB, default=dict)

    # Types source et cible
    source_type = Column(String(50), nullable=True)  # string, number, date...
    target_type = Column(String(50), nullable=True)

    # Validation
    validation_regex = Column(String(500), nullable=True)

    # Statut
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # Regles systeme non modifiables

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_transform_rule_code'),
        Index('idx_transform_rule_tenant', 'tenant_id'),
        Index('idx_transform_rule_type', 'transformation_type'),
    )


class IntegrationDashboard(Base):
    """
    Configuration du dashboard d'integrations.
    Widgets et metriques personnalisees.
    """
    __tablename__ = "integration_dashboards"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration des widgets
    widgets = Column(JSONB, nullable=False)  # Liste des widgets
    layout = Column(JSONB, nullable=True)    # Disposition

    # Rafraichissement
    refresh_interval_seconds = Column(Integer, default=60)

    # Acces
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    owner_id = Column(UniversalUUID(), nullable=False)
    shared_with = Column(JSONB, default=list)  # user_ids ou role_codes

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_int_dashboard_code'),
        Index('idx_int_dashboard_tenant', 'tenant_id'),
        Index('idx_int_dashboard_owner', 'owner_id'),
    )
