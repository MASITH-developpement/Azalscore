"""
AZALS GUARDIAN - Modèles IA Monitoring
======================================
Tables pour le système de monitoring IA automatisé.

MODE A: ai_incidents - Incidents détectés et traités
MODE B: ai_audit_reports - Rapports d'audit mensuels
MODE C: ai_sla_metrics - Métriques SLA/Enterprise
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID
from app.db import Base


# =============================================================================
# ENUMS
# =============================================================================

class IncidentType(str, Enum):
    """Type d'incident détecté."""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATA = "data"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INFRASTRUCTURE = "infrastructure"


class IncidentStatus(str, Enum):
    """Statut de l'incident."""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    FIXED = "fixed"
    ROLLBACK = "rollback"
    FAILED = "failed"
    IGNORED = "ignored"


class IncidentSeverity(str, Enum):
    """Sévérité de l'incident."""
    CRITICAL = "critical"  # P1 - Action immédiate
    HIGH = "high"          # P2 - Action rapide
    MEDIUM = "medium"      # P3 - Action planifiée
    LOW = "low"            # P4 - Information


class AuditStatus(str, Enum):
    """Statut du rapport d'audit."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# MODE A - INCIDENTS
# =============================================================================

class AIIncident(Base):
    """
    Table des incidents détectés par l'IA.

    Stocke chaque incident avec:
    - Signature d'erreur unique
    - Contexte (tenant, module, endpoint)
    - Actions prises
    - Résultat de l'intervention
    """
    __tablename__ = "ai_incidents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Identification
    incident_uid = Column(String(64), unique=True, nullable=False, index=True)
    tenant_id = Column(String(64), nullable=True, index=True)  # Null si système global

    # Contexte de l'erreur
    module = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)  # GET, POST, etc.

    # Détails de l'erreur
    error_signature = Column(String(255), nullable=False, index=True)
    error_type = Column(String(100), nullable=False)  # TypeError, ValueError, etc.
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)

    # Classification
    incident_type = Column(String(20), nullable=False, default=IncidentType.BACKEND.value)
    severity = Column(String(20), nullable=False, default=IncidentSeverity.MEDIUM.value)
    status = Column(String(20), nullable=False, default=IncidentStatus.DETECTED.value)

    # Intervention IA
    analysis_started_at = Column(DateTime, nullable=True)
    analysis_completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Durée intervention en ms

    # Actions prises
    action_taken = Column(Text, nullable=True)  # Description de l'action
    git_branch = Column(String(100), nullable=True)
    git_commit = Column(String(64), nullable=True)
    git_tag = Column(String(50), nullable=True)
    rollback_performed = Column(Boolean, default=False)

    # Résultat
    resolution_notes = Column(Text, nullable=True)
    auto_resolved = Column(Boolean, default=False)
    requires_human = Column(Boolean, default=False)

    # Métadonnées
    context_data = Column(JSON, nullable=True)  # Données contextuelles
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Index composites pour recherche rapide
    __table_args__ = (
        Index('ix_ai_incidents_tenant_module', 'tenant_id', 'module'),
        Index('ix_ai_incidents_status_severity', 'status', 'severity'),
        Index('ix_ai_incidents_created', 'created_at'),
    )


# =============================================================================
# MODE A - SCORES MODULES
# =============================================================================

class AIModuleScore(Base):
    """
    Score de fiabilité par module.

    Calcul sur 100 points:
    - 30 pts: Aucune erreur critique récente
    - 20 pts: Temps de réponse acceptable
    - 20 pts: Données cohérentes
    - 20 pts: Sécurité intacte
    - 10 pts: Stabilité post-correction
    """
    __tablename__ = "ai_module_scores"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Identification
    tenant_id = Column(String(64), nullable=True, index=True)
    module = Column(String(100), nullable=False, index=True)

    # Score global (0-100)
    score_total = Column(Integer, nullable=False, default=100)

    # Composantes du score
    score_errors = Column(Integer, nullable=False, default=30)       # /30
    score_performance = Column(Integer, nullable=False, default=20)  # /20
    score_data = Column(Integer, nullable=False, default=20)         # /20
    score_security = Column(Integer, nullable=False, default=20)     # /20
    score_stability = Column(Integer, nullable=False, default=10)    # /10

    # Statistiques
    incidents_total = Column(Integer, default=0)
    incidents_critical = Column(Integer, default=0)
    incidents_resolved = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, nullable=True)
    last_incident_at = Column(DateTime, nullable=True)

    # Période d'évaluation
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Métadonnées
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    details = Column(JSON, nullable=True)

    __table_args__ = (
        Index('ix_ai_module_scores_tenant_module', 'tenant_id', 'module'),
        Index('ix_ai_module_scores_period', 'period_start', 'period_end'),
    )


# =============================================================================
# MODE B - RAPPORTS D'AUDIT
# =============================================================================

class AIAuditReport(Base):
    """
    Rapports d'audit mensuels (Mode B).

    Lecture seule - Aucune modification système.
    """
    __tablename__ = "ai_audit_reports"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Identification
    report_uid = Column(String(64), unique=True, nullable=False, index=True)
    tenant_id = Column(String(64), nullable=True, index=True)  # Null = audit global

    # Période
    audit_month = Column(Integer, nullable=False)  # 1-12
    audit_year = Column(Integer, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Statut
    status = Column(String(20), nullable=False, default=AuditStatus.PENDING.value)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Résumé global
    modules_audited = Column(Integer, default=0)
    total_incidents = Column(Integer, default=0)
    critical_incidents = Column(Integer, default=0)
    avg_score = Column(Float, nullable=True)

    # Rapport détaillé (JSON)
    module_reports = Column(JSON, nullable=True)  # Score par module
    risks_identified = Column(JSON, nullable=True)  # Risques P1/P2/P3
    technical_debt = Column(JSON, nullable=True)  # Dette technique estimée
    recommendations = Column(JSON, nullable=True)  # Recommandations (sans action)

    # Fichier rapport
    report_json = Column(JSON, nullable=True)  # Rapport complet JSON
    report_file_path = Column(String(255), nullable=True)  # Chemin PDF si généré

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_ai_audit_reports_period', 'audit_year', 'audit_month'),
    )


# =============================================================================
# MODE C - MÉTRIQUES SLA
# =============================================================================

class AISLAMetric(Base):
    """
    Métriques SLA/Enterprise (Mode C).

    Indicateurs objectifs, horodatés et auditables.
    """
    __tablename__ = "ai_sla_metrics"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Identification
    metric_uid = Column(String(64), unique=True, nullable=False, index=True)
    tenant_id = Column(String(64), nullable=True, index=True)

    # Période de mesure
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Disponibilité
    uptime_percent = Column(Float, nullable=True)  # % disponibilité
    downtime_minutes = Column(Integer, default=0)

    # Temps de réponse
    avg_detection_time_ms = Column(Integer, nullable=True)  # Temps détection incident
    avg_resolution_time_ms = Column(Integer, nullable=True)  # Temps correction
    p95_response_time_ms = Column(Integer, nullable=True)  # Percentile 95
    p99_response_time_ms = Column(Integer, nullable=True)  # Percentile 99

    # Incidents
    total_incidents = Column(Integer, default=0)
    incidents_by_module = Column(JSON, nullable=True)
    rollback_count = Column(Integer, default=0)
    rollback_rate = Column(Float, nullable=True)  # %

    # Sécurité & Isolation
    tenant_isolation_verified = Column(Boolean, default=True)
    security_incidents = Column(Integer, default=0)
    data_integrity_score = Column(Float, nullable=True)  # 0-100

    # Métadonnées
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    raw_data = Column(JSON, nullable=True)  # Données brutes pour audit

    __table_args__ = (
        Index('ix_ai_sla_metrics_tenant_period', 'tenant_id', 'period_type'),
        Index('ix_ai_sla_metrics_period', 'period_start', 'period_end'),
    )


# =============================================================================
# CONFIGURATION IA
# =============================================================================

class AIConfig(Base):
    """
    Configuration du système IA Guardian.
    """
    __tablename__ = "ai_config"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, index=True)

    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, int, float, bool, json
    description = Column(Text, nullable=True)

    # Métadonnées
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "IncidentType",
    "IncidentStatus",
    "IncidentSeverity",
    "AuditStatus",
    "AIIncident",
    "AIModuleScore",
    "AIAuditReport",
    "AISLAMetric",
    "AIConfig",
]
