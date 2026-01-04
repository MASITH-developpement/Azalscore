"""
AZALS MODULE T3 - Schémas Audit & Benchmark
============================================

Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import json

from .models import (
    AuditAction, AuditLevel, AuditCategory, MetricType,
    BenchmarkStatus, RetentionPolicy, ComplianceFramework
)


# ============================================================================
# AUDIT LOGS
# ============================================================================

class AuditLogCreateSchema(BaseModel):
    """Création d'un log d'audit."""
    action: AuditAction
    module: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)

    level: AuditLevel = Field(default=AuditLevel.INFO)
    category: AuditCategory = Field(default=AuditCategory.BUSINESS)

    entity_type: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[str] = Field(None, max_length=255)

    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None

    success: bool = Field(default=True)
    error_message: Optional[str] = None
    error_code: Optional[str] = Field(None, max_length=50)

    duration_ms: Optional[float] = None
    retention_policy: RetentionPolicy = Field(default=RetentionPolicy.MEDIUM)


class AuditLogResponseSchema(BaseModel):
    """Réponse pour un log d'audit."""
    id: int
    tenant_id: str

    action: AuditAction
    level: AuditLevel
    category: AuditCategory

    module: str
    entity_type: Optional[str]
    entity_id: Optional[str]

    user_id: Optional[int]
    user_email: Optional[str]
    user_role: Optional[str]

    session_id: Optional[str]
    request_id: Optional[str]
    ip_address: Optional[str]

    description: Optional[str]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    diff: Optional[Dict[str, Any]]
    extra_data: Optional[Dict[str, Any]]

    success: bool
    error_message: Optional[str]
    error_code: Optional[str]

    duration_ms: Optional[float]

    retention_policy: RetentionPolicy
    expires_at: Optional[datetime]

    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj):
        data = {
            "id": obj.id,
            "tenant_id": obj.tenant_id,
            "action": obj.action,
            "level": obj.level,
            "category": obj.category,
            "module": obj.module,
            "entity_type": obj.entity_type,
            "entity_id": obj.entity_id,
            "user_id": obj.user_id,
            "user_email": obj.user_email,
            "user_role": obj.user_role,
            "session_id": obj.session_id,
            "request_id": obj.request_id,
            "ip_address": obj.ip_address,
            "description": obj.description,
            "old_value": json.loads(obj.old_value) if obj.old_value else None,
            "new_value": json.loads(obj.new_value) if obj.new_value else None,
            "diff": json.loads(obj.diff) if obj.diff else None,
            "extra_data": json.loads(obj.extra_data) if obj.extra_data else None,
            "success": obj.success,
            "error_message": obj.error_message,
            "error_code": obj.error_code,
            "duration_ms": obj.duration_ms,
            "retention_policy": obj.retention_policy,
            "expires_at": obj.expires_at,
            "created_at": obj.created_at
        }
        return cls(**data)


class AuditLogListResponseSchema(BaseModel):
    """Liste de logs d'audit."""
    logs: List[AuditLogResponseSchema]
    total: int
    page: int
    page_size: int


class AuditSearchSchema(BaseModel):
    """Critères de recherche audit."""
    action: Optional[AuditAction] = None
    level: Optional[AuditLevel] = None
    category: Optional[AuditCategory] = None
    module: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    success: Optional[bool] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search_text: Optional[str] = None


# ============================================================================
# SESSIONS
# ============================================================================

class AuditSessionResponseSchema(BaseModel):
    """Réponse pour une session."""
    id: int
    tenant_id: str
    session_id: str
    user_id: int
    user_email: Optional[str]

    login_at: datetime
    logout_at: Optional[datetime]
    last_activity_at: datetime

    ip_address: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    country: Optional[str]
    city: Optional[str]

    actions_count: int
    reads_count: int
    writes_count: int

    is_active: bool
    terminated_reason: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# MÉTRIQUES
# ============================================================================

class MetricCreateSchema(BaseModel):
    """Création d'une métrique."""
    code: str = Field(..., min_length=2, max_length=100, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None

    metric_type: MetricType
    unit: Optional[str] = Field(None, max_length=50)
    module: Optional[str] = Field(None, max_length=50)

    aggregation_period: str = Field(default="HOUR", pattern=r'^(MINUTE|HOUR|DAY)$')
    retention_days: int = Field(default=90, ge=1, le=3650)

    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None


class MetricResponseSchema(BaseModel):
    """Réponse pour une métrique."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    metric_type: MetricType
    unit: Optional[str]
    module: Optional[str]

    aggregation_period: str
    retention_days: int

    warning_threshold: Optional[float]
    critical_threshold: Optional[float]

    is_active: bool
    is_system: bool

    created_at: datetime

    class Config:
        from_attributes = True


class MetricValueSchema(BaseModel):
    """Valeur de métrique à enregistrer."""
    metric_code: str
    value: float
    dimensions: Optional[Dict[str, Any]] = None


class MetricValueResponseSchema(BaseModel):
    """Réponse pour une valeur de métrique."""
    id: int
    metric_code: str
    value: float
    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]
    count: int
    period_start: datetime
    period_end: datetime
    dimensions: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj):
        return cls(
            id=obj.id,
            metric_code=obj.metric_code,
            value=obj.value,
            min_value=obj.min_value,
            max_value=obj.max_value,
            avg_value=obj.avg_value,
            count=obj.count,
            period_start=obj.period_start,
            period_end=obj.period_end,
            dimensions=json.loads(obj.dimensions) if obj.dimensions else None
        )


# ============================================================================
# BENCHMARKS
# ============================================================================

class BenchmarkCreateSchema(BaseModel):
    """Création d'un benchmark."""
    code: str = Field(..., min_length=2, max_length=100, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    version: str = Field(default="1.0", max_length=20)

    benchmark_type: str = Field(..., pattern=r'^(PERFORMANCE|SECURITY|COMPLIANCE|FEATURE)$')
    module: Optional[str] = Field(None, max_length=50)

    config: Optional[Dict[str, Any]] = None
    baseline: Optional[Dict[str, Any]] = None

    is_scheduled: bool = Field(default=False)
    schedule_cron: Optional[str] = Field(None, max_length=100)


class BenchmarkResponseSchema(BaseModel):
    """Réponse pour un benchmark."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    version: str

    benchmark_type: str
    module: Optional[str]

    config: Optional[Dict[str, Any]]
    baseline: Optional[Dict[str, Any]]

    is_scheduled: bool
    schedule_cron: Optional[str]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]

    status: BenchmarkStatus
    is_active: bool

    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj):
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            code=obj.code,
            name=obj.name,
            description=obj.description,
            version=obj.version,
            benchmark_type=obj.benchmark_type,
            module=obj.module,
            config=json.loads(obj.config) if obj.config else None,
            baseline=json.loads(obj.baseline) if obj.baseline else None,
            is_scheduled=obj.is_scheduled,
            schedule_cron=obj.schedule_cron,
            last_run_at=obj.last_run_at,
            next_run_at=obj.next_run_at,
            status=obj.status,
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            created_by=obj.created_by
        )


class BenchmarkResultResponseSchema(BaseModel):
    """Réponse pour un résultat de benchmark."""
    id: int
    tenant_id: str
    benchmark_id: int

    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[float]

    status: BenchmarkStatus
    score: Optional[float]
    passed: Optional[bool]
    results: Optional[Dict[str, Any]]
    summary: Optional[str]

    previous_score: Optional[float]
    score_delta: Optional[float]
    trend: Optional[str]

    error_message: Optional[str]
    warnings: Optional[List[str]]

    executed_by: Optional[int]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj):
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            benchmark_id=obj.benchmark_id,
            started_at=obj.started_at,
            completed_at=obj.completed_at,
            duration_ms=obj.duration_ms,
            status=obj.status,
            score=obj.score,
            passed=obj.passed,
            results=json.loads(obj.results) if obj.results else None,
            summary=obj.summary,
            previous_score=obj.previous_score,
            score_delta=obj.score_delta,
            trend=obj.trend,
            error_message=obj.error_message,
            warnings=json.loads(obj.warnings) if obj.warnings else None,
            executed_by=obj.executed_by
        )


# ============================================================================
# CONFORMITÉ
# ============================================================================

class ComplianceCheckCreateSchema(BaseModel):
    """Création d'un contrôle de conformité."""
    framework: ComplianceFramework
    control_id: str = Field(..., min_length=1, max_length=50)
    control_name: str = Field(..., min_length=2, max_length=200)
    control_description: Optional[str] = None

    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)

    check_type: str = Field(..., pattern=r'^(AUTOMATED|MANUAL|HYBRID)$')
    check_query: Optional[str] = None
    expected_result: Optional[str] = None

    severity: str = Field(default="MEDIUM", pattern=r'^(LOW|MEDIUM|HIGH|CRITICAL)$')
    due_date: Optional[datetime] = None


class ComplianceCheckResponseSchema(BaseModel):
    """Réponse pour un contrôle de conformité."""
    id: int
    tenant_id: str

    framework: ComplianceFramework
    control_id: str
    control_name: str
    control_description: Optional[str]

    category: Optional[str]
    subcategory: Optional[str]

    check_type: str
    status: str
    last_checked_at: Optional[datetime]
    checked_by: Optional[int]

    actual_result: Optional[str]
    evidence: Optional[Dict[str, Any]]
    remediation: Optional[str]

    severity: str
    due_date: Optional[datetime]

    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj):
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            framework=obj.framework,
            control_id=obj.control_id,
            control_name=obj.control_name,
            control_description=obj.control_description,
            category=obj.category,
            subcategory=obj.subcategory,
            check_type=obj.check_type,
            status=obj.status,
            last_checked_at=obj.last_checked_at,
            checked_by=obj.checked_by,
            actual_result=obj.actual_result,
            evidence=json.loads(obj.evidence) if obj.evidence else None,
            remediation=obj.remediation,
            severity=obj.severity,
            due_date=obj.due_date,
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )


class ComplianceUpdateSchema(BaseModel):
    """Mise à jour d'un contrôle de conformité."""
    status: str = Field(..., pattern=r'^(PENDING|COMPLIANT|NON_COMPLIANT|N/A)$')
    actual_result: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None


class ComplianceSummarySchema(BaseModel):
    """Résumé de conformité."""
    total: int
    compliant: int
    non_compliant: int
    pending: int
    not_applicable: int
    compliance_rate: float
    by_severity: Dict[str, Dict[str, int]]
    by_category: Dict[str, Dict[str, int]]


# ============================================================================
# RÉTENTION
# ============================================================================

class RetentionRuleCreateSchema(BaseModel):
    """Création d'une règle de rétention."""
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None

    target_table: str = Field(..., min_length=2, max_length=100)
    target_module: Optional[str] = Field(None, max_length=50)

    policy: RetentionPolicy
    retention_days: int = Field(..., ge=1, le=3650)

    condition: Optional[str] = None
    action: str = Field(default="DELETE", pattern=r'^(DELETE|ARCHIVE|ANONYMIZE)$')

    schedule_cron: Optional[str] = Field(None, max_length=100)


class RetentionRuleResponseSchema(BaseModel):
    """Réponse pour une règle de rétention."""
    id: int
    tenant_id: str
    name: str
    description: Optional[str]

    target_table: str
    target_module: Optional[str]

    policy: RetentionPolicy
    retention_days: int

    condition: Optional[str]
    action: str

    schedule_cron: Optional[str]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_affected_count: int

    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EXPORTS
# ============================================================================

class ExportCreateSchema(BaseModel):
    """Création d'un export."""
    export_type: str = Field(..., pattern=r'^(AUDIT_LOGS|METRICS|COMPLIANCE)$')
    format: str = Field(default="CSV", pattern=r'^(CSV|JSON|PDF|EXCEL)$')

    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None


class ExportResponseSchema(BaseModel):
    """Réponse pour un export."""
    id: int
    tenant_id: str

    export_type: str
    format: str

    date_from: Optional[datetime]
    date_to: Optional[datetime]
    filters: Optional[Dict[str, Any]]

    status: str
    progress: int

    file_path: Optional[str]
    file_size: Optional[int]
    records_count: Optional[int]

    error_message: Optional[str]

    requested_by: int
    requested_at: datetime
    completed_at: Optional[datetime]

    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj):
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            export_type=obj.export_type,
            format=obj.format,
            date_from=obj.date_from,
            date_to=obj.date_to,
            filters=json.loads(obj.filters) if obj.filters else None,
            status=obj.status,
            progress=obj.progress,
            file_path=obj.file_path,
            file_size=obj.file_size,
            records_count=obj.records_count,
            error_message=obj.error_message,
            requested_by=obj.requested_by,
            requested_at=obj.requested_at,
            completed_at=obj.completed_at,
            expires_at=obj.expires_at
        )


# ============================================================================
# DASHBOARDS
# ============================================================================

class DashboardWidgetSchema(BaseModel):
    """Configuration d'un widget de dashboard."""
    id: str
    type: str  # audit_stats, recent_activity, compliance_summary, metric_chart
    title: str
    config: Optional[Dict[str, Any]] = None
    size: str = Field(default="medium", pattern=r'^(small|medium|large)$')


class DashboardCreateSchema(BaseModel):
    """Création d'un tableau de bord."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None

    widgets: List[DashboardWidgetSchema]
    layout: Optional[Dict[str, Any]] = None
    refresh_interval: int = Field(default=60, ge=10, le=3600)

    is_public: bool = Field(default=False)
    is_default: bool = Field(default=False)


class DashboardResponseSchema(BaseModel):
    """Réponse pour un tableau de bord."""
    id: int
    tenant_id: str
    code: str
    name: str
    description: Optional[str]

    widgets: List[DashboardWidgetSchema]
    layout: Optional[Dict[str, Any]]
    refresh_interval: int

    is_public: bool
    owner_id: int
    shared_with: Optional[List[str]]

    is_default: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj):
        return cls(
            id=obj.id,
            tenant_id=obj.tenant_id,
            code=obj.code,
            name=obj.name,
            description=obj.description,
            widgets=json.loads(obj.widgets) if isinstance(obj.widgets, str) else obj.widgets,
            layout=json.loads(obj.layout) if obj.layout else None,
            refresh_interval=obj.refresh_interval,
            is_public=obj.is_public,
            owner_id=obj.owner_id,
            shared_with=json.loads(obj.shared_with) if obj.shared_with else None,
            is_default=obj.is_default,
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )


class DashboardDataResponseSchema(BaseModel):
    """Données d'un tableau de bord."""
    dashboard: Dict[str, Any]
    data: Dict[str, Any]


# ============================================================================
# STATISTIQUES
# ============================================================================

class AuditStatsSchema(BaseModel):
    """Statistiques d'audit."""
    total_logs_24h: int
    failed_24h: int
    active_sessions: int
    unique_users_24h: int

    logs_by_action: Optional[Dict[str, int]] = None
    logs_by_module: Optional[Dict[str, int]] = None
    logs_by_level: Optional[Dict[str, int]] = None


class AuditDashboardResponseSchema(BaseModel):
    """Dashboard d'audit complet."""
    stats: AuditStatsSchema
    recent_logs: List[AuditLogResponseSchema]
    active_sessions: List[AuditSessionResponseSchema]
    compliance_summary: Optional[ComplianceSummarySchema]
    latest_benchmarks: Optional[List[BenchmarkResultResponseSchema]]
