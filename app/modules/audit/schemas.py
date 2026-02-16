"""
AZALS MODULE T3 - Schémas Audit & Benchmark
============================================

Schémas Pydantic pour validation et sérialisation.
"""


import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    AuditAction,
    AuditCategory,
    AuditLevel,
    BenchmarkStatus,
    ComplianceFramework,
    MetricType,
    RetentionPolicy,
)

# ============================================================================
# AUDIT LOGS
# ============================================================================

class AuditLogCreateSchema(BaseModel):
    """Création d'un log d'audit."""
    action: AuditAction
    module: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(None, max_length=1000)

    level: AuditLevel = Field(default=AuditLevel.INFO)
    category: AuditCategory = Field(default=AuditCategory.BUSINESS)

    entity_type: str | None = Field(None, max_length=100)
    entity_id: str | None = Field(None, max_length=255)

    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None

    success: bool = Field(default=True)
    error_message: str | None = None
    error_code: str | None = Field(None, max_length=50)

    duration_ms: float | None = None
    retention_policy: RetentionPolicy = Field(default=RetentionPolicy.MEDIUM)


class AuditLogResponseSchema(BaseModel):
    """Reponse pour un log d'audit."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str

    action: AuditAction
    level: AuditLevel
    category: AuditCategory

    module: str
    entity_type: str | None = None
    entity_id: str | None = None

    user_id: UUID | None = None
    user_email: str | None = None
    user_role: str | None = None

    session_id: str | None = None
    request_id: str | None = None
    ip_address: str | None = None

    description: str | None = None
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    diff: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None

    success: bool = True
    error_message: str | None = None
    error_code: str | None = None

    duration_ms: float | None = None

    retention_policy: RetentionPolicy | None = None
    expires_at: datetime | None = None

    created_at: datetime | None = None

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
    logs: list[AuditLogResponseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditSearchSchema(BaseModel):
    """Critères de recherche audit."""
    action: AuditAction | None = None
    level: AuditLevel | None = None
    category: AuditCategory | None = None
    module: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    success: bool | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    search_text: str | None = None


# ============================================================================
# SESSIONS
# ============================================================================

class AuditSessionResponseSchema(BaseModel):
    """Reponse pour une session."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    session_id: str
    user_id: UUID
    user_email: str | None

    login_at: datetime
    logout_at: datetime | None
    last_activity_at: datetime

    ip_address: str | None
    device_type: str | None
    browser: str | None
    os: str | None
    country: str | None
    city: str | None

    actions_count: int
    reads_count: int
    writes_count: int

    is_active: bool
    terminated_reason: str | None


# ============================================================================
# MÉTRIQUES
# ============================================================================

class MetricCreateSchema(BaseModel):
    """Création d'une métrique."""
    code: str = Field(..., min_length=2, max_length=100, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None

    metric_type: MetricType
    unit: str | None = Field(None, max_length=50)
    module: str | None = Field(None, max_length=50)

    aggregation_period: str = Field(default="HOUR", pattern=r'^(MINUTE|HOUR|DAY)$')
    retention_days: int = Field(default=90, ge=1, le=3650)

    warning_threshold: float | None = None
    critical_threshold: float | None = None


class MetricResponseSchema(BaseModel):
    """Reponse pour une metrique."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    code: str
    name: str
    description: str | None

    metric_type: MetricType
    unit: str | None
    module: str | None

    aggregation_period: str
    retention_days: int

    warning_threshold: float | None
    critical_threshold: float | None

    is_active: bool
    is_system: bool

    created_at: datetime


class MetricValueSchema(BaseModel):
    """Valeur de métrique à enregistrer."""
    metric_code: str
    value: float
    dimensions: dict[str, Any] | None = None


class MetricValueResponseSchema(BaseModel):
    """Réponse pour une valeur de métrique."""
    id: UUID
    metric_code: str
    value: float
    min_value: float | None
    max_value: float | None
    avg_value: float | None
    count: int
    period_start: datetime
    period_end: datetime
    dimensions: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)

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
    description: str | None = None
    version: str = Field(default="1.0", max_length=20)

    benchmark_type: str = Field(..., pattern=r'^(PERFORMANCE|SECURITY|COMPLIANCE|FEATURE)$')
    module: str | None = Field(None, max_length=50)

    config: dict[str, Any] | None = None
    baseline: dict[str, Any] | None = None

    is_scheduled: bool = Field(default=False)
    schedule_cron: str | None = Field(None, max_length=100)


class BenchmarkResponseSchema(BaseModel):
    """Réponse pour un benchmark."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: str | None
    version: str

    benchmark_type: str
    module: str | None

    config: dict[str, Any] | None
    baseline: dict[str, Any] | None

    is_scheduled: bool
    schedule_cron: str | None
    last_run_at: datetime | None
    next_run_at: datetime | None

    status: BenchmarkStatus
    is_active: bool

    created_at: datetime
    updated_at: datetime
    created_by: str | None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('config', 'baseline', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dicts."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    @field_validator('created_by', mode='before')
    @classmethod
    def stringify_uuid(cls, v):
        """Convert UUID to string."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

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
    id: UUID
    tenant_id: str
    benchmark_id: UUID

    started_at: datetime
    completed_at: datetime | None
    duration_ms: float | None

    status: BenchmarkStatus
    score: float | None
    passed: bool | None
    results: dict[str, Any] | None
    summary: str | None

    previous_score: float | None
    score_delta: float | None
    trend: str | None

    error_message: str | None
    warnings: list[str] | None

    executed_by: str | None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('results', 'warnings', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string to dict/list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    @field_validator('executed_by', mode='before')
    @classmethod
    def stringify_uuid(cls, v):
        """Convert UUID to string."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

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
    control_description: str | None = None

    category: str | None = Field(None, max_length=100)
    subcategory: str | None = Field(None, max_length=100)

    check_type: str = Field(..., pattern=r'^(AUTOMATED|MANUAL|HYBRID)$')
    check_query: str | None = None
    expected_result: str | None = None

    severity: str = Field(default="MEDIUM", pattern=r'^(LOW|MEDIUM|HIGH|CRITICAL)$')
    due_date: datetime | None = None


class ComplianceCheckResponseSchema(BaseModel):
    """Réponse pour un contrôle de conformité."""
    id: UUID
    tenant_id: str

    framework: ComplianceFramework
    control_id: str
    control_name: str
    control_description: str | None

    category: str | None
    subcategory: str | None

    check_type: str
    status: str
    last_checked_at: datetime | None
    checked_by: str | None

    actual_result: str | None
    evidence: dict[str, Any] | None
    remediation: str | None

    severity: str
    due_date: datetime | None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('checked_by', mode='before')
    @classmethod
    def stringify_uuid(cls, v):
        """Convert UUID to string."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

    @field_validator('evidence', mode='before')
    @classmethod
    def parse_json_evidence(cls, v):
        """Parse JSON string to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

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
    actual_result: str | None = None
    evidence: dict[str, Any] | None = None
    remediation: str | None = None


class ComplianceSummarySchema(BaseModel):
    """Résumé de conformité."""
    total: int
    compliant: int
    non_compliant: int
    pending: int
    not_applicable: int
    compliance_rate: float
    by_severity: dict[str, dict[str, int]]
    by_category: dict[str, dict[str, int]]


# ============================================================================
# RÉTENTION
# ============================================================================

class RetentionRuleCreateSchema(BaseModel):
    """Création d'une règle de rétention."""
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None

    target_table: str = Field(..., min_length=2, max_length=100)
    target_module: str | None = Field(None, max_length=50)

    policy: RetentionPolicy
    retention_days: int = Field(..., ge=1, le=3650)

    condition: str | None = None
    action: str = Field(default="DELETE", pattern=r'^(DELETE|ARCHIVE|ANONYMIZE)$')

    schedule_cron: str | None = Field(None, max_length=100)


class RetentionRuleResponseSchema(BaseModel):
    """Réponse pour une règle de rétention."""
    id: UUID
    tenant_id: str
    name: str
    description: str | None

    target_table: str
    target_module: str | None

    policy: RetentionPolicy
    retention_days: int

    condition: str | None
    action: str

    schedule_cron: str | None
    last_run_at: datetime | None
    next_run_at: datetime | None
    last_affected_count: int

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EXPORTS
# ============================================================================

class ExportCreateSchema(BaseModel):
    """Création d'un export."""
    export_type: str = Field(..., pattern=r'^(AUDIT_LOGS|METRICS|COMPLIANCE)$')
    format: str = Field(default="CSV", pattern=r'^(CSV|JSON|PDF|EXCEL)$')

    date_from: datetime | None = None
    date_to: datetime | None = None
    filters: dict[str, Any] | None = None


class ExportResponseSchema(BaseModel):
    """Réponse pour un export."""
    id: UUID
    tenant_id: str

    export_type: str
    format: str

    date_from: datetime | None
    date_to: datetime | None
    filters: dict[str, Any] | None

    status: str
    progress: int

    file_path: str | None
    file_size: int | None
    records_count: int | None

    error_message: str | None

    requested_by: UUID
    requested_at: datetime
    completed_at: datetime | None

    expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('filters', mode='before')
    @classmethod
    def parse_json_filters(cls, v):
        """Parse JSON string to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

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
    model_config = ConfigDict(protected_namespaces=())

    id: str
    type: str  # audit_stats, recent_activity, compliance_summary, metric_chart
    title: str
    config: dict[str, Any] | None = None
    size: str = Field(default="medium", pattern=r'^(small|medium|large)$')


class DashboardCreateSchema(BaseModel):
    """Création d'un tableau de bord."""
    code: str = Field(..., min_length=2, max_length=50, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None

    widgets: list[DashboardWidgetSchema]
    layout: dict[str, Any] | None = None
    refresh_interval: int = Field(default=60, ge=10, le=3600)

    is_public: bool = Field(default=False)
    is_default: bool = Field(default=False)


class DashboardResponseSchema(BaseModel):
    """Réponse pour un tableau de bord."""
    id: UUID
    tenant_id: str
    code: str
    name: str
    description: str | None

    widgets: list[DashboardWidgetSchema]
    layout: dict[str, Any] | None
    refresh_interval: int

    is_public: bool
    owner_id: UUID
    shared_with: list[str] | None

    is_default: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('widgets', mode='before')
    @classmethod
    def parse_widgets(cls, v):
        """Parse JSON string to list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    @field_validator('layout', 'shared_with', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        """Parse JSON string to dict/list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

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
    dashboard: dict[str, Any]
    data: dict[str, Any]


# ============================================================================
# STATISTIQUES
# ============================================================================

class AuditStatsSchema(BaseModel):
    """Statistiques d'audit."""
    total_logs_24h: int
    failed_24h: int
    active_sessions: int
    unique_users_24h: int

    logs_by_action: dict[str, int] | None = None
    logs_by_module: dict[str, int] | None = None
    logs_by_level: dict[str, int] | None = None


class AuditDashboardResponseSchema(BaseModel):
    """Dashboard d'audit complet."""
    stats: AuditStatsSchema
    recent_logs: list[AuditLogResponseSchema]
    active_sessions: list[AuditSessionResponseSchema]
    compliance_summary: ComplianceSummarySchema | None
    latest_benchmarks: list[BenchmarkResultResponseSchema] | None
