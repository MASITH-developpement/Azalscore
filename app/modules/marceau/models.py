"""
AZALS MODULE - Marceau Models
==============================

Modeles SQLAlchemy pour l'agent IA Marceau.
TOUS les modeles ont tenant_id avec index et FK vers tenants.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

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
)
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class ActionStatus(str, enum.Enum):
    """Statut d'une action Marceau."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_VALIDATION = "needs_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"


class MemoryType(str, enum.Enum):
    """Type de memoire Marceau."""
    CONVERSATION = "conversation"
    CUSTOMER_PROFILE = "customer_profile"
    DECISION = "decision"
    LEARNING = "learning"
    KNOWLEDGE = "knowledge"


class ConversationOutcome(str, enum.Enum):
    """Resultat d'une conversation telephonique."""
    QUOTE_CREATED = "quote_created"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    TRANSFERRED = "transferred"
    VOICEMAIL = "voicemail"
    ABANDONED = "abandoned"
    INFORMATION_PROVIDED = "information_provided"
    CALLBACK_SCHEDULED = "callback_scheduled"
    COMPLAINT_RECORDED = "complaint_recorded"


class ModuleName(str, enum.Enum):
    """Noms des modules Marceau."""
    TELEPHONIE = "telephonie"
    MARKETING = "marketing"
    SEO = "seo"
    COMMERCIAL = "commercial"
    COMPTABILITE = "comptabilite"
    JURIDIQUE = "juridique"
    RECRUTEMENT = "recrutement"
    SUPPORT = "support"
    ORCHESTRATION = "orchestration"


# ============================================================================
# CONFIGURATION PAR TENANT
# ============================================================================

class MarceauConfig(Base):
    """
    Configuration Marceau par tenant.
    Chaque tenant a une configuration unique et isolee.
    """
    __tablename__ = "marceau_configs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, unique=True, index=True)

    # Modules actives (JSON)
    enabled_modules = Column(JSON, default={
        "telephonie": True,
        "marketing": False,
        "seo": False,
        "commercial": False,
        "comptabilite": False,
        "juridique": False,
        "recrutement": False,
        "support": False,
        "orchestration": False,
    })

    # Niveau d'autonomie par module (0-100%)
    autonomy_levels = Column(JSON, default={
        "telephonie": 100,
        "marketing": 100,
        "seo": 100,
        "commercial": 100,
        "comptabilite": 100,
        "juridique": 100,
        "recrutement": 100,
        "support": 100,
        "orchestration": 100,
    })

    # Configuration IA
    llm_temperature = Column(Float, default=0.2)
    llm_model = Column(String(100), default="llama3-8b-instruct")
    stt_model = Column(String(100), default="whisper-small")
    tts_voice = Column(String(100), default="fr_FR-sise-medium")

    # Configuration telephonie
    telephony_config = Column(JSON, default={
        "asterisk_ami_host": "localhost",
        "asterisk_ami_port": 5038,
        "asterisk_ami_username": "",
        "asterisk_ami_password": "",
        "working_hours": {"start": "09:00", "end": "18:00"},
        "overflow_threshold": 2,
        "overflow_number": "",
        "appointment_duration_minutes": 60,
        "max_wait_days": 14,
        "use_travel_time": True,
        "travel_buffer_minutes": 15,
    })

    # Integrations externes
    integrations = Column(JSON, default={
        "ors_api_key": None,
        "gmail_credentials": None,
        "google_calendar_id": None,
        "linkedin_token": None,
        "facebook_token": None,
        "instagram_token": None,
        "slack_webhook": None,
        "hubspot_api_key": None,
        "wordpress_url": None,
        "wordpress_token": None,
    })

    # Statistiques
    total_actions = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    total_quotes_created = Column(Integer, default=0)
    total_appointments_scheduled = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_marceau_config_tenant', 'tenant_id', unique=True),
    )


# ============================================================================
# JOURNAL DES ACTIONS
# ============================================================================

class MarceauAction(Base):
    """
    Journal des actions executees par Marceau.
    Tracabilite complete de toutes les decisions et actions.
    """
    __tablename__ = "marceau_actions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Module et type d'action
    module = Column(Enum(ModuleName, values_callable=lambda x: [e.value for e in x]), nullable=False)
    action_type = Column(String(100), nullable=False)  # call_received, quote_created, etc.
    status = Column(Enum(ActionStatus, values_callable=lambda x: [e.value for e in x]), default=ActionStatus.PENDING, nullable=False)

    # Donnees d'entree/sortie
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})

    # Scoring et validation
    confidence_score = Column(Float, default=1.0)  # 0-1
    required_human_validation = Column(Boolean, default=False)
    validated_by = Column(UniversalUUID(), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validation_notes = Column(Text, nullable=True)

    # Entite liee
    related_entity_type = Column(String(100), nullable=True)  # Intervention, CommercialDocument, etc.
    related_entity_id = Column(UniversalUUID(), nullable=True)

    # Conversation associee
    conversation_id = Column(UniversalUUID(), ForeignKey("marceau_conversations.id"), nullable=True)

    # Metriques
    duration_seconds = Column(Float, default=0)
    tokens_used = Column(Integer, default=0)

    # Erreur eventuelle
    error_message = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    conversation = relationship("MarceauConversation", back_populates="actions")

    __table_args__ = (
        Index('idx_marceau_action_tenant', 'tenant_id'),
        Index('idx_marceau_action_module', 'tenant_id', 'module'),
        Index('idx_marceau_action_status', 'tenant_id', 'status'),
        Index('idx_marceau_action_date', 'tenant_id', 'created_at'),
        Index('idx_marceau_action_validation', 'tenant_id', 'required_human_validation', 'status'),
    )


# ============================================================================
# MEMOIRE CONTEXTUELLE
# ============================================================================

class MarceauMemory(Base):
    """
    Memoire contextuelle de Marceau.
    Stockee en DB avec reference vers ChromaDB pour embeddings.
    """
    __tablename__ = "marceau_memory"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Type de memoire
    memory_type = Column(Enum(MemoryType, values_callable=lambda x: [e.value for e in x]), nullable=False)

    # Contenu
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  # Resume pour affichage

    # Reference ChromaDB
    embedding_id = Column(String(255), nullable=True, index=True)
    collection_name = Column(String(100), nullable=True)

    # Relations
    related_action_id = Column(UniversalUUID(), nullable=True)
    related_customer_id = Column(UniversalUUID(), nullable=True)
    related_conversation_id = Column(UniversalUUID(), nullable=True)

    # Classification
    tags = Column(JSON, default=[])
    importance_score = Column(Float, default=0.5)  # 0-1, plus c'est haut plus c'est important

    # Expiration
    expires_at = Column(DateTime, nullable=True)
    is_permanent = Column(Boolean, default=False)

    # Source
    source = Column(String(100), nullable=True)  # upload, conversation, learning, etc.
    source_file_name = Column(String(255), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_marceau_memory_tenant', 'tenant_id'),
        Index('idx_marceau_memory_type', 'tenant_id', 'memory_type'),
        Index('idx_marceau_memory_embedding', 'embedding_id'),
        Index('idx_marceau_memory_tags', 'tenant_id'),  # Pour recherche par tags
        Index('idx_marceau_memory_importance', 'tenant_id', 'importance_score'),
    )


# ============================================================================
# CONVERSATIONS TELEPHONIQUES
# ============================================================================

class MarceauConversation(Base):
    """
    Conversation telephonique geree par Marceau.
    Stocke transcript, resume, intent et resultat.
    """
    __tablename__ = "marceau_conversations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Appelant
    caller_phone = Column(String(50), nullable=False)
    caller_name = Column(String(255), nullable=True)
    customer_id = Column(UniversalUUID(), nullable=True, index=True)

    # Contenu
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    intent = Column(String(100), nullable=True)  # quote_request, appointment_request, support, other

    # Metriques
    duration_seconds = Column(Integer, default=0)
    satisfaction_score = Column(Float, nullable=True)  # Note client 1-5

    # Resultat
    outcome = Column(Enum(ConversationOutcome, values_callable=lambda x: [e.value for e in x]), nullable=True)

    # Fichiers
    recording_url = Column(String(500), nullable=True)

    # Lien avec l'appel Asterisk
    asterisk_call_id = Column(String(100), nullable=True, index=True)
    asterisk_channel = Column(String(255), nullable=True)

    # Transfert eventuel
    transferred_to = Column(String(100), nullable=True)
    transfer_reason = Column(String(255), nullable=True)

    # Dates
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    actions = relationship("MarceauAction", back_populates="conversation")

    __table_args__ = (
        Index('idx_marceau_conv_tenant', 'tenant_id'),
        Index('idx_marceau_conv_customer', 'tenant_id', 'customer_id'),
        Index('idx_marceau_conv_phone', 'tenant_id', 'caller_phone'),
        Index('idx_marceau_conv_outcome', 'tenant_id', 'outcome'),
        Index('idx_marceau_conv_date', 'tenant_id', 'started_at'),
        Index('idx_marceau_conv_asterisk', 'asterisk_call_id'),
    )


# ============================================================================
# DOCUMENTS DE CONNAISSANCE
# ============================================================================

class MarceauKnowledgeDocument(Base):
    """
    Document uploade pour enrichir la base de connaissances.
    """
    __tablename__ = "marceau_knowledge_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Fichier
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, csv
    file_size = Column(Integer, default=0)
    file_url = Column(String(500), nullable=True)

    # Traitement
    is_processed = Column(Boolean, default=False)
    chunks_count = Column(Integer, default=0)
    processing_error = Column(Text, nullable=True)

    # Classification
    category = Column(String(100), nullable=True)  # catalog, procedure, faq, etc.
    tags = Column(JSON, default=[])

    # Audit
    uploaded_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_marceau_doc_tenant', 'tenant_id'),
        Index('idx_marceau_doc_processed', 'tenant_id', 'is_processed'),
        Index('idx_marceau_doc_category', 'tenant_id', 'category'),
    )


# ============================================================================
# FEEDBACK ET APPRENTISSAGE
# ============================================================================

class MarceauFeedback(Base):
    """
    Feedback utilisateur sur les actions Marceau.
    Utilise pour l'apprentissage continu.
    """
    __tablename__ = "marceau_feedback"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Action concernee
    action_id = Column(UniversalUUID(), ForeignKey("marceau_actions.id"), nullable=False)

    # Feedback
    rating = Column(Integer, nullable=False)  # 1-5 ou -1/0/1
    feedback_type = Column(String(50), nullable=False)  # positive, negative, correction
    comment = Column(Text, nullable=True)

    # Correction eventuelle
    correction_data = Column(JSON, nullable=True)  # Donnees corrigees

    # Auteur
    given_by = Column(UniversalUUID(), nullable=True)

    # Traitement
    is_processed = Column(Boolean, default=False)
    applied_to_learning = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_marceau_feedback_tenant', 'tenant_id'),
        Index('idx_marceau_feedback_action', 'action_id'),
        Index('idx_marceau_feedback_processed', 'tenant_id', 'is_processed'),
    )


# ============================================================================
# TACHES PLANIFIEES
# ============================================================================

class MarceauScheduledTask(Base):
    """
    Taches planifiees par Marceau (cron jobs).
    """
    __tablename__ = "marceau_scheduled_tasks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Module et action
    module = Column(Enum(ModuleName, values_callable=lambda x: [e.value for e in x]), nullable=False)
    action_type = Column(String(100), nullable=False)
    action_params = Column(JSON, default={})

    # Planification (cron format)
    cron_expression = Column(String(100), nullable=False)  # "0 9 * * 1-5" = 9h lun-ven
    timezone = Column(String(50), default="Europe/Paris")

    # Statut
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(50), nullable=True)
    last_run_error = Column(Text, nullable=True)

    # Statistiques
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Audit
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_marceau_task_tenant', 'tenant_id'),
        Index('idx_marceau_task_active', 'tenant_id', 'is_active'),
        Index('idx_marceau_task_next_run', 'next_run_at'),
    )
