"""
AZALS - MODULE IA TRANSVERSE OPÉRATIONNELLE
=============================================
Modèles SQLAlchemy pour l'assistant IA central.

Principes:
- IA assistante, jamais décisionnaire finale
- Double confirmation pour points rouges
- Traçabilité complète
- Apprentissage transversal anonymisé

MIGRATED: All PKs and FKs use UUID for PostgreSQL compatibility.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base
from app.core.types import UniversalUUID

# ============================================================================
# ENUMS
# ============================================================================

class AIRequestType(str, PyEnum):
    """Types de requêtes IA."""
    QUESTION = "question"           # Question simple
    ANALYSIS = "analysis"           # Analyse de données
    PREDICTION = "prediction"       # Prévision
    RECOMMENDATION = "recommendation"  # Recommandation
    RISK_DETECTION = "risk_detection"  # Détection de risques
    SYNTHESIS = "synthesis"         # Synthèse
    REMINDER = "reminder"           # Rappel
    DECISION_SUPPORT = "decision_support"  # Aide à la décision


class AIResponseStatus(str, PyEnum):
    """Statuts de réponse IA."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class RiskLevel(str, PyEnum):
    """Niveaux de risque."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, PyEnum):
    """Catégories de risques."""
    FINANCIAL = "financial"
    LEGAL = "legal"
    OPERATIONAL = "operational"
    REGULATORY = "regulatory"
    SECURITY = "security"
    REPUTATIONAL = "reputational"
    STRATEGIC = "strategic"


class DecisionStatus(str, PyEnum):
    """Statuts de décision."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ============================================================================
# CONVERSATIONS & INTERACTIONS
# ============================================================================

class AIConversation(Base):
    """Conversation avec l'IA."""
    __tablename__ = "ai_conversations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    # Métadonnées
    title = Column(String(255))
    context = Column(JSON)  # Contexte métier
    module_source = Column(String(100))  # Module d'origine

    # État
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relations
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ai_conv_tenant', 'tenant_id'),
        Index('idx_ai_conv_user', 'tenant_id', 'user_id'),
    )


class AIMessage(Base):
    """Message dans une conversation IA."""
    __tablename__ = "ai_messages"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    conversation_id = Column(UniversalUUID(), ForeignKey("ai_conversations.id"), nullable=False)

    # Type et contenu
    role = Column(String(20), nullable=False)  # user, assistant, system
    request_type = Column(String(50))
    content = Column(Text, nullable=False)

    # Métadonnées
    message_metadata = Column(JSON)
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)

    # État
    status = Column(String(30), default="completed")

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    conversation = relationship("AIConversation", back_populates="messages")

    __table_args__ = (
        Index('idx_ai_msg_conv', 'conversation_id'),
    )


# ============================================================================
# ANALYSES & DÉCISIONS
# ============================================================================

class AIAnalysis(Base):
    """Analyse IA pour aide à la décision."""
    __tablename__ = "ai_analyses"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    # Identification
    analysis_code = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Type et contexte
    analysis_type = Column(String(50), nullable=False)  # 360, financial, operational, etc.
    module_source = Column(String(100))
    entity_type = Column(String(100))  # customer, order, project, etc.
    entity_id = Column(String(100))

    # Données analysées
    input_data = Column(JSON)
    data_period_start = Column(DateTime)
    data_period_end = Column(DateTime)

    # Résultats
    summary = Column(Text)
    findings = Column(JSON)  # Liste des constats
    metrics = Column(JSON)  # Métriques calculées
    confidence_score = Column(Float)  # Score de confiance 0-1

    # Risques identifiés
    risks_identified = Column(JSON)
    overall_risk_level = Column(String(20))

    # Recommandations
    recommendations = Column(JSON)

    # État
    status = Column(String(30), default="completed")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    __table_args__ = (
        Index('idx_ai_analysis_tenant', 'tenant_id'),
        Index('idx_ai_analysis_user', 'tenant_id', 'user_id'),
        Index('idx_ai_analysis_type', 'tenant_id', 'analysis_type'),
    )


class AIDecisionSupport(Base):
    """Support de décision avec validation obligatoire."""
    __tablename__ = "ai_decision_supports"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    decision_code = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Contexte
    decision_type = Column(String(100), nullable=False)
    module_source = Column(String(100))
    priority = Column(String(20), default="normal")
    deadline = Column(DateTime)

    # Analyse liée
    analysis_id = Column(UniversalUUID(), ForeignKey("ai_analyses.id"))

    # Options proposées
    options = Column(JSON)  # Liste d'options avec pros/cons
    recommended_option = Column(Integer)  # Index de l'option recommandée
    recommendation_rationale = Column(Text)

    # Risques
    risk_level = Column(String(20))
    risks = Column(JSON)
    mitigation_measures = Column(JSON)

    # Impact estimé
    estimated_impact = Column(JSON)  # financial, operational, etc.

    # GOUVERNANCE - Point rouge
    is_red_point = Column(Boolean, default=False)
    requires_double_confirmation = Column(Boolean, default=False)

    # Décision
    status = Column(String(30), default="pending_review")
    decided_by_id = Column(UniversalUUID())
    decided_at = Column(DateTime)
    decision_made = Column(Integer)  # Index option choisie
    decision_notes = Column(Text)

    # Double confirmation (si point rouge)
    first_confirmation_by = Column(UniversalUUID())
    first_confirmation_at = Column(DateTime)
    second_confirmation_by = Column(UniversalUUID())
    second_confirmation_at = Column(DateTime)

    # Audit
    created_by_id = Column(UniversalUUID(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ai_decision_tenant', 'tenant_id'),
        Index('idx_ai_decision_status', 'tenant_id', 'status'),
        Index('idx_ai_decision_red', 'tenant_id', 'is_red_point'),
    )


# ============================================================================
# DÉTECTION DE RISQUES
# ============================================================================

class AIRiskAlert(Base):
    """Alerte de risque détectée par l'IA."""
    __tablename__ = "ai_risk_alerts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    alert_code = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Classification
    category = Column(String(50), nullable=False)
    subcategory = Column(String(100))
    risk_level = Column(String(20), nullable=False)
    probability = Column(Float)  # 0-1
    impact_score = Column(Float)  # 0-10

    # Source
    detection_source = Column(String(100))  # Module qui a déclenché
    trigger_rule = Column(String(255))
    trigger_data = Column(JSON)

    # Entités concernées
    affected_entities = Column(JSON)  # [{type, id, name}]

    # Impact potentiel
    potential_impact = Column(JSON)
    estimated_financial_impact = Column(Numeric(15, 2))

    # Recommandations
    recommended_actions = Column(JSON)
    preventive_measures = Column(JSON)

    # État
    status = Column(String(30), default="active")  # active, acknowledged, mitigated, resolved, expired
    acknowledged_by = Column(UniversalUUID())
    acknowledged_at = Column(DateTime)
    resolved_by = Column(UniversalUUID())
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    __table_args__ = (
        Index('idx_ai_risk_tenant', 'tenant_id'),
        Index('idx_ai_risk_level', 'tenant_id', 'risk_level'),
        Index('idx_ai_risk_category', 'tenant_id', 'category'),
        Index('idx_ai_risk_status', 'tenant_id', 'status'),
    )


# ============================================================================
# PRÉDICTIONS
# ============================================================================

class AIPrediction(Base):
    """Prédiction IA."""
    __tablename__ = "ai_predictions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    prediction_code = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)

    # Type
    prediction_type = Column(String(100), nullable=False)  # sales, cashflow, demand, etc.
    target_metric = Column(String(100))
    module_source = Column(String(100))

    # Période
    prediction_start = Column(DateTime, nullable=False)
    prediction_end = Column(DateTime, nullable=False)
    granularity = Column(String(20))  # daily, weekly, monthly

    # Données d'entrée
    input_data_summary = Column(JSON)
    model_used = Column(String(100))
    model_parameters = Column(JSON)

    # Résultats
    predicted_values = Column(JSON)  # [{date, value, confidence}]
    confidence_interval = Column(JSON)  # {lower, upper}
    confidence_score = Column(Float)

    # Comparaison (si données réelles disponibles)
    actual_values = Column(JSON)
    accuracy_score = Column(Float)
    mape = Column(Float)  # Mean Absolute Percentage Error

    # État
    status = Column(String(30), default="active")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ai_pred_tenant', 'tenant_id'),
        Index('idx_ai_pred_type', 'tenant_id', 'prediction_type'),
    )


# ============================================================================
# APPRENTISSAGE & FEEDBACK
# ============================================================================

class AIFeedback(Base):
    """Feedback utilisateur sur les réponses IA."""
    __tablename__ = "ai_feedbacks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)

    # Référence
    reference_type = Column(String(50), nullable=False)  # message, analysis, prediction, decision
    reference_id = Column(UniversalUUID(), nullable=False)

    # Évaluation
    rating = Column(Integer)  # 1-5
    is_helpful = Column(Boolean)
    is_accurate = Column(Boolean)

    # Feedback textuel
    feedback_text = Column(Text)
    improvement_suggestion = Column(Text)

    # Catégorie
    feedback_category = Column(String(50))  # quality, accuracy, relevance, speed

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ai_feedback_ref', 'reference_type', 'reference_id'),
    )


class AILearningData(Base):
    """Données d'apprentissage anonymisées."""
    __tablename__ = "ai_learning_data"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)

    # Anonymisé - pas de tenant_id ni user_id direct
    data_hash = Column(String(64), unique=True)

    # Type
    data_type = Column(String(50), nullable=False)
    category = Column(String(100))

    # Données anonymisées
    pattern_data = Column(JSON)
    outcome_data = Column(JSON)

    # Métriques
    usage_count = Column(Integer, default=1)
    success_rate = Column(Float)
    avg_rating = Column(Float)

    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ai_learning_type', 'data_type'),
    )


# ============================================================================
# CONFIGURATION IA
# ============================================================================

class AIConfiguration(Base):
    """Configuration IA par tenant."""
    __tablename__ = "ai_configurations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, unique=True)

    # Activation
    is_enabled = Column(Boolean, default=True)
    enabled_features = Column(JSON)  # Liste des fonctionnalités activées

    # Limites
    daily_request_limit = Column(Integer, default=1000)
    max_tokens_per_request = Column(Integer, default=4000)

    # Comportement
    response_language = Column(String(10), default="fr")
    formality_level = Column(String(20), default="professional")
    detail_level = Column(String(20), default="balanced")

    # Sécurité
    require_confirmation_threshold = Column(String(20), default="high")  # Niveau risque nécessitant confirmation
    auto_escalation_enabled = Column(Boolean, default=True)
    escalation_delay_hours = Column(Integer, default=24)

    # Modules autorisés
    allowed_modules = Column(JSON)
    restricted_data_types = Column(JSON)

    # Notifications
    notify_on_risk = Column(Boolean, default=True)
    notify_on_anomaly = Column(Boolean, default=True)
    notification_channels = Column(JSON)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())

    __table_args__ = (
        Index('idx_ai_config_tenant', 'tenant_id'),
    )


# ============================================================================
# AUDIT IA
# ============================================================================

class AIAuditLog(Base):
    """Journal d'audit des actions IA."""
    __tablename__ = "ai_audit_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID())

    # Action
    action = Column(String(100), nullable=False)
    action_category = Column(String(50))

    # Référence
    reference_type = Column(String(50))
    reference_id = Column(UniversalUUID())

    # Détails
    request_summary = Column(Text)
    response_summary = Column(Text)
    parameters = Column(JSON)

    # Résultat
    status = Column(String(30))
    error_message = Column(Text)

    # Contexte
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    session_id = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ai_audit_tenant', 'tenant_id'),
        Index('idx_ai_audit_action', 'tenant_id', 'action'),
        Index('idx_ai_audit_date', 'tenant_id', 'created_at'),
    )
