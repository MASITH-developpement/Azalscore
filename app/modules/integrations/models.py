"""
Models SQLAlchemy - Module Integrations (GAP-086)

CRITIQUE: Tous les modèles ont tenant_id pour isolation multi-tenant.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Numeric,
    ForeignKey, Index, JSON
)
from app.core.types import UniversalUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# ============== Enums ==============

class ConnectorType(str, Enum):
    """Types de connecteurs."""
    SAGE = "sage"
    CEGID = "cegid"
    PENNYLANE = "pennylane"
    ODOO = "odoo"
    SAP = "sap"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    STRIPE = "stripe"
    GOCARDLESS = "gocardless"
    QONTO = "qonto"
    MAILCHIMP = "mailchimp"
    SLACK = "slack"
    GOOGLE_DRIVE = "google_drive"
    CUSTOM = "custom"


class AuthType(str, Enum):
    """Types d'authentification."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    BEARER = "bearer"
    HMAC = "hmac"
    CERTIFICATE = "certificate"


class SyncDirection(str, Enum):
    """Direction de synchronisation."""
    IMPORT = "import"
    EXPORT = "export"
    BIDIRECTIONAL = "bidirectional"


class SyncFrequency(str, Enum):
    """Fréquence de synchronisation."""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class ConnectionStatus(str, Enum):
    """Statut de connexion."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"
    PENDING = "pending"


class SyncStatus(str, Enum):
    """Statut de synchronisation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConflictResolution(str, Enum):
    """Stratégies de résolution de conflits."""
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"
    MERGE = "merge"


class EntityType(str, Enum):
    """Types d'entités synchronisables."""
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PRODUCT = "product"
    ORDER = "order"
    INVOICE = "invoice"
    PAYMENT = "payment"
    CONTACT = "contact"
    LEAD = "lead"


# ============== Models ==============

class Connection(Base):
    """Connexion à un service externe."""
    __tablename__ = "integ_legacy_connections"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    connector_type = Column(String(50), nullable=False)
    auth_type = Column(String(30), nullable=False)

    # Configuration
    base_url = Column(String(500))
    credentials = Column(JSON, default=dict)  # Chiffré en production
    custom_headers = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)

    # OAuth2
    access_token = Column(Text)  # Chiffré
    refresh_token = Column(Text)  # Chiffré
    token_expires_at = Column(DateTime)

    # État
    status = Column(String(20), default=ConnectionStatus.PENDING.value)
    last_connected_at = Column(DateTime)
    last_error = Column(Text)

    # Santé
    last_health_check = Column(DateTime)
    consecutive_errors = Column(Integer, default=0)

    # Audit
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    entity_mappings = relationship("EntityMapping", back_populates="connection", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="connection")

    __table_args__ = (
        Index("ix_integ_leg_conn_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_integ_leg_conn_tenant_type", "tenant_id", "connector_type"),
        Index("ix_integ_leg_conn_tenant_status", "tenant_id", "status"),
    )


class EntityMapping(Base):
    """Mapping d'une entité entre systèmes."""
    __tablename__ = "integ_legacy_entity_mappings"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    connection_id = Column(UUID(), ForeignKey("integ_legacy_connections.id"), nullable=False)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)

    # Source et cible
    source_entity = Column(String(100), nullable=False)
    target_entity = Column(String(100), nullable=False)
    direction = Column(String(20), default=SyncDirection.BIDIRECTIONAL.value)

    # Mappings de champs (JSON)
    field_mappings = Column(JSON, default=list)

    # Filtres (JSON)
    source_filter = Column(JSON)
    target_filter = Column(JSON)

    # Clé de déduplication
    dedup_key_source = Column(String(100))
    dedup_key_target = Column(String(100))

    # État
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    connection = relationship("Connection", back_populates="entity_mappings")
    sync_jobs = relationship("SyncJob", back_populates="entity_mapping")

    __table_args__ = (
        Index("ix_entity_mappings_connection", "connection_id", "entity_type"),
        Index("ix_entity_mappings_tenant_code", "tenant_id", "code", unique=True),
    )


class SyncJob(Base):
    """Job de synchronisation."""
    __tablename__ = "integ_legacy_sync_jobs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    connection_id = Column(UUID(), ForeignKey("integ_legacy_connections.id"), nullable=False)
    entity_mapping_id = Column(UUID(), ForeignKey("integ_legacy_entity_mappings.id"), nullable=False)

    # Configuration
    direction = Column(String(20), nullable=False)
    conflict_resolution = Column(String(20), default=ConflictResolution.NEWEST_WINS.value)

    # Planification
    frequency = Column(String(20), default=SyncFrequency.MANUAL.value)
    next_run_at = Column(DateTime)
    cron_expression = Column(String(100))

    # État
    status = Column(String(20), default=SyncStatus.PENDING.value)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Statistiques
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    created_records = Column(Integer, default=0)
    updated_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)

    # Erreurs (JSON)
    errors = Column(JSON, default=list)

    # Delta sync
    last_sync_at = Column(DateTime)
    sync_cursor = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())

    # Relations
    connection = relationship("Connection", back_populates="sync_jobs")
    entity_mapping = relationship("EntityMapping", back_populates="sync_jobs")
    logs = relationship("SyncLog", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sync_jobs_tenant_status", "tenant_id", "status"),
        Index("ix_sync_jobs_connection", "connection_id", "status"),
    )


class SyncLog(Base):
    """Log de synchronisation."""
    __tablename__ = "integ_legacy_sync_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    job_id = Column(UUID(), ForeignKey("integ_legacy_sync_jobs.id"), nullable=False)

    # Enregistrement
    source_id = Column(String(255), nullable=False)
    target_id = Column(String(255))
    entity_type = Column(String(50), nullable=False)

    # Action
    action = Column(String(20), nullable=False)  # create, update, skip, error

    # Données (JSON)
    source_data = Column(JSON)
    target_data = Column(JSON)
    changes = Column(JSON)

    # Résultat
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relation
    job = relationship("SyncJob", back_populates="logs")

    __table_args__ = (
        Index("ix_sync_logs_job", "job_id", "timestamp"),
        Index("ix_sync_logs_source", "tenant_id", "source_id"),
    )


class Conflict(Base):
    """Conflit de synchronisation."""
    __tablename__ = "integ_legacy_conflicts"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    job_id = Column(UUID(), ForeignKey("integ_legacy_sync_jobs.id"), nullable=False)

    # Enregistrements en conflit
    source_id = Column(String(255), nullable=False)
    target_id = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)

    # Données (JSON)
    source_data = Column(JSON, default=dict)
    target_data = Column(JSON, default=dict)
    conflicting_fields = Column(JSON, default=list)

    # Résolution
    resolution = Column(String(20))
    resolved_data = Column(JSON)
    resolved_at = Column(DateTime)
    resolved_by = Column(UUID())

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_conflicts_tenant_pending", "tenant_id", "resolved_at"),
        Index("ix_conflicts_job", "job_id"),
    )


class Webhook(Base):
    """Webhook entrant."""
    __tablename__ = "integ_legacy_webhooks"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    connection_id = Column(UUID(), ForeignKey("integ_legacy_connections.id"), nullable=False)

    # Configuration
    endpoint_path = Column(String(255), nullable=False)
    secret_key = Column(String(255))  # Pour validation HMAC
    is_active = Column(Boolean, default=True)

    # Événements (JSON)
    subscribed_events = Column(JSON, default=list)

    # Stats
    last_received_at = Column(DateTime)
    total_received = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())

    __table_args__ = (
        Index("ix_webhooks_tenant_path", "tenant_id", "endpoint_path", unique=True),
    )
