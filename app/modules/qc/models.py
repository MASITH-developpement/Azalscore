"""
AZALS MODULE T4 - Modèles Contrôle Qualité Central
===================================================

Modèles SQLAlchemy pour le système de contrôle qualité.
REFACTORED: Migration vers UUID pour production SaaS industrielle.
NOTE: ForeignKey retirées des modèles pour bootstrap Alembic sécurisé.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    Float, Enum, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import UniversalUUID, JSONB


# ============================================================================
# ENUMS
# ============================================================================

class QCRuleCategory(str, PyEnum):
    """Catégories de règles QC."""
    ARCHITECTURE = "ARCHITECTURE"      # Règles d'architecture
    SECURITY = "SECURITY"              # Règles de sécurité
    PERFORMANCE = "PERFORMANCE"        # Règles de performance
    CODE_QUALITY = "CODE_QUALITY"      # Qualité du code
    TESTING = "TESTING"                # Couverture tests
    DOCUMENTATION = "DOCUMENTATION"    # Documentation
    API = "API"                        # Standards API
    DATABASE = "DATABASE"              # Standards BDD
    INTEGRATION = "INTEGRATION"        # Intégration
    COMPLIANCE = "COMPLIANCE"          # Conformité


class QCRuleSeverity(str, PyEnum):
    """Sévérité des règles QC."""
    INFO = "INFO"              # Information
    WARNING = "WARNING"        # Avertissement
    CRITICAL = "CRITICAL"      # Critique (bloquant)
    BLOCKER = "BLOCKER"        # Bloqueur (empêche validation)


class QCCheckStatus(str, PyEnum):
    """Statut d'un check QC."""
    PENDING = "PENDING"        # En attente
    RUNNING = "RUNNING"        # En cours
    PASSED = "PASSED"          # Réussi
    FAILED = "FAILED"          # Échoué
    SKIPPED = "SKIPPED"        # Ignoré
    ERROR = "ERROR"            # Erreur technique


class ModuleStatus(str, PyEnum):
    """Statut de validation d'un module."""
    DRAFT = "DRAFT"                # Brouillon
    IN_DEVELOPMENT = "IN_DEVELOPMENT"  # En développement
    READY_FOR_QC = "READY_FOR_QC"      # Prêt pour QC
    QC_IN_PROGRESS = "QC_IN_PROGRESS"  # QC en cours
    QC_PASSED = "QC_PASSED"            # QC validé
    QC_FAILED = "QC_FAILED"            # QC échoué
    PRODUCTION = "PRODUCTION"          # En production
    DEPRECATED = "DEPRECATED"          # Déprécié


class QCTestType(str, PyEnum):
    """Types de tests."""
    UNIT = "UNIT"                  # Tests unitaires
    INTEGRATION = "INTEGRATION"    # Tests d'intégration
    E2E = "E2E"                    # Tests end-to-end
    PERFORMANCE = "PERFORMANCE"    # Tests de performance
    SECURITY = "SECURITY"          # Tests de sécurité
    REGRESSION = "REGRESSION"      # Tests de régression


# Alias pour compatibilité
TestType = QCTestType


class ValidationPhase(str, PyEnum):
    """Phases de validation."""
    PRE_QC = "PRE_QC"              # Pré-validation
    AUTOMATED = "AUTOMATED"         # Validation automatique
    MANUAL = "MANUAL"              # Validation manuelle
    FINAL = "FINAL"                # Validation finale
    POST_DEPLOY = "POST_DEPLOY"    # Post-déploiement


# ============================================================================
# MODÈLES - REFACTORED TO UUID FOR SAAS PRODUCTION
# ============================================================================

class QCRule(Base):
    """Définition d'une règle de contrôle qualité."""
    __tablename__ = "qc_rules"
    __table_args__ = (
        Index("idx_qc_rules_tenant_code", "tenant_id", "code", unique=True),
        Index("idx_qc_rules_category", "tenant_id", "category"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    category = Column(Enum(QCRuleCategory), nullable=False)
    severity = Column(Enum(QCRuleSeverity), default=QCRuleSeverity.WARNING, nullable=False)

    # Critères d'application
    applies_to_modules = Column(Text)  # JSON list ou "*" pour tous
    applies_to_phases = Column(Text)   # JSON list de ValidationPhase

    # Règle
    check_type = Column(String(50), nullable=False)  # file_exists, pattern_match, test_coverage, etc.
    check_config = Column(Text)  # JSON config pour le check

    # Seuils
    threshold_value = Column(Float)
    threshold_operator = Column(String(10))  # >=, <=, ==, >, <

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # Règle système non modifiable

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())


class ModuleRegistry(Base):
    """Registre des modules avec leur statut de validation."""
    __tablename__ = "qc_module_registry"
    __table_args__ = (
        Index("idx_module_registry_tenant_code", "tenant_id", "module_code", unique=True),
        Index("idx_module_registry_status", "tenant_id", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    module_code = Column(String(10), nullable=False)  # T0, T1, M1, etc.
    module_name = Column(String(200), nullable=False)
    module_version = Column(String(20), default="1.0.0", nullable=False)
    module_type = Column(String(20), nullable=False)  # TRANSVERSE ou METIER

    description = Column(Text)
    dependencies = Column(Text)  # JSON list des codes modules dépendants

    status = Column(Enum(ModuleStatus), default=ModuleStatus.DRAFT, nullable=False)

    # Scores
    overall_score = Column(Float, default=0.0)
    architecture_score = Column(Float, default=0.0)
    security_score = Column(Float, default=0.0)
    performance_score = Column(Float, default=0.0)
    code_quality_score = Column(Float, default=0.0)
    testing_score = Column(Float, default=0.0)
    documentation_score = Column(Float, default=0.0)

    # Statistiques
    total_checks = Column(Integer, default=0)
    passed_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    blocked_checks = Column(Integer, default=0)

    # Dates importantes
    last_qc_run = Column(DateTime)
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())
    production_at = Column(DateTime)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class QCValidation(Base):
    """Session de validation QC pour un module."""
    __tablename__ = "qc_validations"
    __table_args__ = (
        Index("idx_validations_tenant_module", "tenant_id", "module_id"),
        Index("idx_validations_status", "tenant_id", "status"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # FK gérée via migration Alembic séparée
    module_id = Column(UniversalUUID(), nullable=False)
    validation_phase = Column(Enum(ValidationPhase), nullable=False)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    started_by = Column(UniversalUUID())

    # Résultats
    status = Column(Enum(QCCheckStatus), default=QCCheckStatus.PENDING, nullable=False)
    overall_score = Column(Float)

    total_rules = Column(Integer, default=0)
    passed_rules = Column(Integer, default=0)
    failed_rules = Column(Integer, default=0)
    skipped_rules = Column(Integer, default=0)
    blocked_rules = Column(Integer, default=0)

    # Scores par catégorie (JSON)
    category_scores = Column(Text)

    # Rapport
    report_summary = Column(Text)
    report_details = Column(Text)  # JSON avec tous les détails


class QCCheckResult(Base):
    """Résultat d'un check QC individuel."""
    __tablename__ = "qc_check_results"
    __table_args__ = (
        Index("idx_check_results_validation", "validation_id"),
        Index("idx_check_results_status", "tenant_id", "status"),
        Index("idx_check_results_category", "tenant_id", "category"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # FK gérées via migration Alembic séparée
    validation_id = Column(UniversalUUID(), nullable=False)
    rule_id = Column(UniversalUUID())

    rule_code = Column(String(50), nullable=False)
    rule_name = Column(String(200))
    category = Column(Enum(QCRuleCategory), nullable=False)
    severity = Column(Enum(QCRuleSeverity), nullable=False)

    status = Column(Enum(QCCheckStatus), default=QCCheckStatus.PENDING, nullable=False)

    # Résultats
    executed_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer)

    expected_value = Column(String(255))
    actual_value = Column(String(255))
    score = Column(Float)  # 0-100

    # Messages
    message = Column(Text)
    error_details = Column(Text)
    recommendation = Column(Text)

    # Preuves
    evidence = Column(Text)  # JSON avec fichiers, lignes, etc.


class QCTestRun(Base):
    """Exécution de tests pour un module."""
    __tablename__ = "qc_test_runs"
    __table_args__ = (
        Index("idx_test_runs_tenant_module", "tenant_id", "module_id"),
        Index("idx_test_runs_type", "tenant_id", "test_type"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # FK gérées via migration Alembic séparée
    module_id = Column(UniversalUUID(), nullable=False)
    validation_id = Column(UniversalUUID())

    test_type = Column(Enum(TestType), nullable=False)
    test_suite = Column(String(200))

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # Résultats
    status = Column(Enum(QCCheckStatus), default=QCCheckStatus.PENDING, nullable=False)

    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)

    coverage_percent = Column(Float)

    # Détails
    failed_test_details = Column(Text)  # JSON
    output_log = Column(Text)

    # Métadonnées
    triggered_by = Column(String(50))  # manual, ci, scheduled
    triggered_user = Column(UniversalUUID())


# Alias pour compatibilité
TestRun = QCTestRun


class QCMetric(Base):
    """Métriques QC agrégées."""
    __tablename__ = "qc_metrics"
    __table_args__ = (
        Index("idx_qc_metrics_tenant_date", "tenant_id", "metric_date"),
        Index("idx_qc_metrics_module", "tenant_id", "module_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # FK gérée via migration Alembic séparée
    module_id = Column(UniversalUUID())
    metric_date = Column(DateTime, nullable=False)

    # Métriques globales
    modules_total = Column(Integer, default=0)
    modules_validated = Column(Integer, default=0)
    modules_production = Column(Integer, default=0)
    modules_failed = Column(Integer, default=0)

    # Scores moyens
    avg_overall_score = Column(Float)
    avg_architecture_score = Column(Float)
    avg_security_score = Column(Float)
    avg_performance_score = Column(Float)
    avg_code_quality_score = Column(Float)
    avg_testing_score = Column(Float)
    avg_documentation_score = Column(Float)

    # Tests
    total_tests_run = Column(Integer, default=0)
    total_tests_passed = Column(Integer, default=0)
    avg_coverage = Column(Float)

    # Règles
    total_checks_run = Column(Integer, default=0)
    total_checks_passed = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    blocker_issues = Column(Integer, default=0)

    # Tendances
    score_trend = Column(String(10))  # UP, DOWN, STABLE
    score_delta = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class QCAlert(Base):
    """Alertes QC."""
    __tablename__ = "qc_alerts"
    __table_args__ = (
        Index("idx_qc_alerts_tenant_unresolved", "tenant_id", "is_resolved"),
        Index("idx_qc_alerts_severity", "tenant_id", "severity"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # FK gérées via migration Alembic séparée
    module_id = Column(UniversalUUID())
    validation_id = Column(UniversalUUID())
    check_result_id = Column(UniversalUUID())

    alert_type = Column(String(50), nullable=False)  # validation_failed, score_dropped, blocker_found
    severity = Column(Enum(QCRuleSeverity), default=QCRuleSeverity.WARNING, nullable=False)

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text)  # JSON

    # Statut
    is_read = Column(Boolean, default=False, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(UniversalUUID())
    resolution_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class QCDashboard(Base):
    """Configuration de dashboard QC personnalisé."""
    __tablename__ = "qc_dashboards"
    __table_args__ = (
        Index("idx_qc_dashboards_tenant_owner", "tenant_id", "owner_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Configuration
    layout = Column(Text)  # JSON layout
    widgets = Column(Text)  # JSON widgets config
    filters = Column(Text)  # JSON filtres par défaut

    # Partage
    is_default = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    owner_id = Column(UniversalUUID())
    shared_with = Column(Text)  # JSON user/role ids

    # Rafraîchissement
    auto_refresh = Column(Boolean, default=True, nullable=False)
    refresh_interval = Column(Integer, default=60)  # secondes

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class QCTemplate(Base):
    """Templates de règles QC prédéfinies."""
    __tablename__ = "qc_templates"
    __table_args__ = (
        Index("idx_qc_templates_tenant_code", "tenant_id", "code", unique=True),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Contenu
    rules = Column(Text, nullable=False)  # JSON list de règles
    category = Column(String(50))  # Module type: TRANSVERSE, METIER, ALL

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
