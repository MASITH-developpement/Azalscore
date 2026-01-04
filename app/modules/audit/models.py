"""
AZALS MODULE T3 - Modèles Audit & Benchmark
============================================

Modèles SQLAlchemy pour l'audit et les benchmarks.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean, ForeignKey,
    Index, Enum, UniqueConstraint, Float, BigInteger, func
)
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class AuditAction(str, enum.Enum):
    """Types d'actions auditées."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    VALIDATE = "VALIDATE"
    REJECT = "REJECT"
    APPROVE = "APPROVE"
    SUBMIT = "SUBMIT"
    CANCEL = "CANCEL"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    CONFIGURE = "CONFIGURE"
    EXECUTE = "EXECUTE"


class AuditLevel(str, enum.Enum):
    """Niveau d'importance de l'audit."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditCategory(str, enum.Enum):
    """Catégories d'audit."""
    SECURITY = "SECURITY"
    BUSINESS = "BUSINESS"
    SYSTEM = "SYSTEM"
    DATA = "DATA"
    COMPLIANCE = "COMPLIANCE"
    PERFORMANCE = "PERFORMANCE"


class MetricType(str, enum.Enum):
    """Types de métriques."""
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    TIMER = "TIMER"


class BenchmarkStatus(str, enum.Enum):
    """Statut d'un benchmark."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RetentionPolicy(str, enum.Enum):
    """Politiques de rétention."""
    IMMEDIATE = "IMMEDIATE"      # Suppression immédiate
    SHORT = "SHORT"              # 30 jours
    MEDIUM = "MEDIUM"            # 1 an
    LONG = "LONG"                # 5 ans
    PERMANENT = "PERMANENT"      # Jamais supprimé
    LEGAL = "LEGAL"              # Conforme réglementation (10 ans)


class ComplianceFramework(str, enum.Enum):
    """Frameworks de conformité."""
    GDPR = "GDPR"
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"
    CUSTOM = "CUSTOM"


# ============================================================================
# MODÈLES PRINCIPAUX
# ============================================================================

class AuditLog(Base):
    """
    Journal d'audit centralisé.
    Enregistre toutes les actions du système.
    """
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Action
    action = Column(Enum(AuditAction), nullable=False)
    level = Column(Enum(AuditLevel), default=AuditLevel.INFO, nullable=False)
    category = Column(Enum(AuditCategory), default=AuditCategory.BUSINESS, nullable=False)

    # Source
    module = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(255), nullable=True)

    # Utilisateur
    user_id = Column(Integer, nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)

    # Session/Request
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Contenu
    description = Column(String(1000), nullable=True)
    old_value = Column(Text, nullable=True)  # JSON avant modification
    new_value = Column(Text, nullable=True)  # JSON après modification
    diff = Column(Text, nullable=True)       # Diff des changements
    extra_data = Column(Text, nullable=True)   # JSON métadonnées additionnelles

    # Résultat
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Performance
    duration_ms = Column(Float, nullable=True)

    # Retention
    retention_policy = Column(Enum(RetentionPolicy), default=RetentionPolicy.MEDIUM, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_audit_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_audit_module_action', 'module', 'action'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_user', 'user_id', 'created_at'),
        Index('idx_audit_level', 'level'),
        Index('idx_audit_category', 'category'),
        Index('idx_audit_retention', 'retention_policy', 'expires_at'),
    )


class AuditSession(Base):
    """
    Session utilisateur auditée.
    Trace les connexions et activités.
    """
    __tablename__ = "audit_sessions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Session
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String(255), nullable=True)

    # Connexion
    login_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    logout_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Localisation
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    # Statistiques session
    actions_count = Column(Integer, default=0, nullable=False)
    reads_count = Column(Integer, default=0, nullable=False)
    writes_count = Column(Integer, default=0, nullable=False)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    terminated_reason = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_sessions_tenant', 'tenant_id'),
        Index('idx_sessions_user', 'user_id'),
        Index('idx_sessions_active', 'is_active'),
    )


class MetricDefinition(Base):
    """
    Définition d'une métrique à collecter.
    """
    __tablename__ = "audit_metric_definitions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    metric_type = Column(Enum(MetricType), nullable=False)
    unit = Column(String(50), nullable=True)  # ms, %, count, bytes...
    module = Column(String(50), nullable=True)

    # Agrégation
    aggregation_period = Column(String(20), default='HOUR', nullable=False)  # MINUTE, HOUR, DAY
    retention_days = Column(Integer, default=90, nullable=False)

    # Seuils
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)

    # Statut
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_metric_code'),
        Index('idx_metrics_tenant', 'tenant_id'),
    )


class MetricValue(Base):
    """
    Valeur d'une métrique à un instant donné.
    """
    __tablename__ = "audit_metric_values"

    id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Métrique
    metric_id = Column(Integer, ForeignKey('audit_metric_definitions.id', ondelete='CASCADE'), nullable=False)
    metric_code = Column(String(100), nullable=False, index=True)

    # Valeur
    value = Column(Float, nullable=False)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    avg_value = Column(Float, nullable=True)
    count = Column(Integer, default=1, nullable=False)

    # Période
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Dimensions (optionnel)
    dimensions = Column(Text, nullable=True)  # JSON: {"module": "treasury", "action": "read"}

    __table_args__ = (
        Index('idx_metric_values_tenant', 'tenant_id'),
        Index('idx_metric_values_metric', 'metric_id'),
        Index('idx_metric_values_code', 'metric_code'),
        Index('idx_metric_values_period', 'period_start', 'period_end'),
    )


class Benchmark(Base):
    """
    Benchmark de performance ou fonctionnel.
    """
    __tablename__ = "audit_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default='1.0', nullable=False)

    # Type
    benchmark_type = Column(String(50), nullable=False)  # PERFORMANCE, SECURITY, COMPLIANCE, FEATURE
    module = Column(String(50), nullable=True)

    # Configuration
    config = Column(Text, nullable=True)  # JSON: paramètres du benchmark
    baseline = Column(Text, nullable=True)  # JSON: valeurs de référence

    # Planification
    is_scheduled = Column(Boolean, default=False, nullable=False)
    schedule_cron = Column(String(100), nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)

    # Statut
    status = Column(Enum(BenchmarkStatus), default=BenchmarkStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', 'version', name='uq_benchmark_code_version'),
        Index('idx_benchmarks_tenant', 'tenant_id'),
        Index('idx_benchmarks_type', 'benchmark_type'),
    )


class BenchmarkResult(Base):
    """
    Résultat d'exécution d'un benchmark.
    """
    __tablename__ = "audit_benchmark_results"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Benchmark
    benchmark_id = Column(Integer, ForeignKey('audit_benchmarks.id', ondelete='CASCADE'), nullable=False)

    # Exécution
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)

    # Résultats
    status = Column(Enum(BenchmarkStatus), nullable=False)
    score = Column(Float, nullable=True)  # Score global (0-100)
    passed = Column(Boolean, nullable=True)
    results = Column(Text, nullable=True)  # JSON: détails des résultats
    summary = Column(Text, nullable=True)  # Résumé texte

    # Comparaison
    previous_score = Column(Float, nullable=True)
    score_delta = Column(Float, nullable=True)
    trend = Column(String(20), nullable=True)  # UP, DOWN, STABLE

    # Erreurs
    error_message = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)  # JSON: liste des warnings

    executed_by = Column(Integer, nullable=True)

    __table_args__ = (
        Index('idx_results_tenant', 'tenant_id'),
        Index('idx_results_benchmark', 'benchmark_id'),
        Index('idx_results_started', 'started_at'),
    )


class ComplianceCheck(Base):
    """
    Vérification de conformité.
    """
    __tablename__ = "audit_compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Framework
    framework = Column(Enum(ComplianceFramework), nullable=False)
    control_id = Column(String(50), nullable=False)
    control_name = Column(String(200), nullable=False)
    control_description = Column(Text, nullable=True)

    # Catégorie
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)

    # Vérification
    check_type = Column(String(50), nullable=False)  # AUTOMATED, MANUAL, HYBRID
    check_query = Column(Text, nullable=True)  # Requête ou script de vérification
    expected_result = Column(Text, nullable=True)

    # Statut
    status = Column(String(20), default='PENDING', nullable=False)  # PENDING, COMPLIANT, NON_COMPLIANT, N/A
    last_checked_at = Column(DateTime, nullable=True)
    checked_by = Column(Integer, nullable=True)

    # Résultat
    actual_result = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)  # JSON: preuves de conformité
    remediation = Column(Text, nullable=True)

    # Priorité
    severity = Column(String(20), default='MEDIUM', nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    due_date = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'framework', 'control_id', name='uq_compliance_control'),
        Index('idx_compliance_tenant', 'tenant_id'),
        Index('idx_compliance_framework', 'framework'),
        Index('idx_compliance_status', 'status'),
    )


class DataRetentionRule(Base):
    """
    Règle de rétention des données.
    """
    __tablename__ = "audit_retention_rules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Cible
    target_table = Column(String(100), nullable=False)
    target_module = Column(String(50), nullable=True)

    # Politique
    policy = Column(Enum(RetentionPolicy), nullable=False)
    retention_days = Column(Integer, nullable=False)

    # Condition
    condition = Column(Text, nullable=True)  # Condition SQL additionnelle

    # Action
    action = Column(String(20), default='DELETE', nullable=False)  # DELETE, ARCHIVE, ANONYMIZE

    # Planification
    schedule_cron = Column(String(100), nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_affected_count = Column(Integer, default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_retention_tenant', 'tenant_id'),
        Index('idx_retention_table', 'target_table'),
    )


class AuditExport(Base):
    """
    Export de données d'audit.
    """
    __tablename__ = "audit_exports"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Configuration
    export_type = Column(String(50), nullable=False)  # AUDIT_LOGS, METRICS, COMPLIANCE
    format = Column(String(20), default='CSV', nullable=False)  # CSV, JSON, PDF, EXCEL

    # Filtres
    date_from = Column(DateTime, nullable=True)
    date_to = Column(DateTime, nullable=True)
    filters = Column(Text, nullable=True)  # JSON: filtres appliqués

    # Statut
    status = Column(String(20), default='PENDING', nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    progress = Column(Integer, default=0, nullable=False)

    # Résultat
    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    records_count = Column(Integer, nullable=True)

    # Erreur
    error_message = Column(Text, nullable=True)

    # Audit
    requested_by = Column(Integer, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_exports_tenant', 'tenant_id'),
        Index('idx_exports_status', 'status'),
        Index('idx_exports_requested', 'requested_at'),
    )


class AuditDashboard(Base):
    """
    Configuration de tableau de bord d'audit.
    """
    __tablename__ = "audit_dashboards"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    widgets = Column(Text, nullable=False)  # JSON: configuration des widgets
    layout = Column(Text, nullable=True)  # JSON: disposition des widgets
    refresh_interval = Column(Integer, default=60, nullable=False)  # En secondes

    # Accès
    is_public = Column(Boolean, default=False, nullable=False)
    owner_id = Column(Integer, nullable=False)
    shared_with = Column(Text, nullable=True)  # JSON: utilisateurs/rôles

    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_dashboard_code'),
        Index('idx_dashboards_tenant', 'tenant_id'),
        Index('idx_dashboards_owner', 'owner_id'),
    )
