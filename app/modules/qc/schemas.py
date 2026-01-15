"""
AZALS MODULE T4 - Schémas Pydantic Contrôle Qualité
====================================================

Schémas de validation pour les API du module QC.
"""


import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# ENUMS
# ============================================================================

class QCRuleCategoryEnum(str, Enum):
    ARCHITECTURE = "ARCHITECTURE"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    CODE_QUALITY = "CODE_QUALITY"
    TESTING = "TESTING"
    DOCUMENTATION = "DOCUMENTATION"
    API = "API"
    DATABASE = "DATABASE"
    INTEGRATION = "INTEGRATION"
    COMPLIANCE = "COMPLIANCE"


class QCRuleSeverityEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    BLOCKER = "BLOCKER"


class QCCheckStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class ModuleStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    IN_DEVELOPMENT = "IN_DEVELOPMENT"
    READY_FOR_QC = "READY_FOR_QC"
    QC_IN_PROGRESS = "QC_IN_PROGRESS"
    QC_PASSED = "QC_PASSED"
    QC_FAILED = "QC_FAILED"
    PRODUCTION = "PRODUCTION"
    DEPRECATED = "DEPRECATED"


class QCTestTypeEnum(str, Enum):
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    E2E = "E2E"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    REGRESSION = "REGRESSION"


# Alias pour compatibilité
TestTypeEnum = QCTestTypeEnum


class ValidationPhaseEnum(str, Enum):
    PRE_QC = "PRE_QC"
    AUTOMATED = "AUTOMATED"
    MANUAL = "MANUAL"
    FINAL = "FINAL"
    POST_DEPLOY = "POST_DEPLOY"


# ============================================================================
# RÈGLES QC
# ============================================================================

class QCRuleBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    category: QCRuleCategoryEnum
    severity: QCRuleSeverityEnum = QCRuleSeverityEnum.WARNING
    check_type: str = Field(..., min_length=2, max_length=50)
    applies_to_modules: list[str] | None = None
    applies_to_phases: list[str] | None = None
    check_config: dict[str, Any] | None = None
    threshold_value: float | None = None
    threshold_operator: str | None = None


class QCRuleCreate(QCRuleBase):
    pass


class QCRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    severity: QCRuleSeverityEnum | None = None
    applies_to_modules: list[str] | None = None
    applies_to_phases: list[str] | None = None
    check_config: dict[str, Any] | None = None
    threshold_value: float | None = None
    threshold_operator: str | None = None
    is_active: bool | None = None


class QCRuleResponse(QCRuleBase):
    id: int
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("applies_to_modules", "applies_to_phases", "check_config", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return v
        return v


# ============================================================================
# MODULES
# ============================================================================

class ModuleRegistryBase(BaseModel):
    module_code: str = Field(..., min_length=2, max_length=10)
    module_name: str = Field(..., min_length=2, max_length=200)
    module_type: str = Field(..., description="TRANSVERSE ou METIER")
    module_version: str = "1.0.0"
    description: str | None = None
    dependencies: list[str] | None = None


class ModuleRegisterCreate(ModuleRegistryBase):
    pass


class ModuleRegistryResponse(ModuleRegistryBase):
    id: int
    status: ModuleStatusEnum
    overall_score: float
    architecture_score: float
    security_score: float
    performance_score: float
    code_quality_score: float
    testing_score: float
    documentation_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    blocked_checks: int
    last_qc_run: datetime | None = None
    validated_at: datetime | None = None
    validated_by: int | None = None
    production_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("dependencies", mode="before")
    @classmethod
    def parse_dependencies(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v


class ModuleStatusUpdate(BaseModel):
    status: ModuleStatusEnum


# ============================================================================
# VALIDATIONS
# ============================================================================

class ValidationStartRequest(BaseModel):
    module_id: int
    phase: ValidationPhaseEnum = ValidationPhaseEnum.AUTOMATED


class ValidationRunRequest(BaseModel):
    module_id: int
    phase: ValidationPhaseEnum = ValidationPhaseEnum.AUTOMATED


class ValidationResponse(BaseModel):
    id: int
    module_id: int
    validation_phase: ValidationPhaseEnum
    started_at: datetime
    completed_at: datetime | None = None
    started_by: int | None = None
    status: QCCheckStatusEnum
    overall_score: float | None = None
    total_rules: int
    passed_rules: int
    failed_rules: int
    skipped_rules: int
    blocked_rules: int
    category_scores: dict[str, Any] | None = None
    report_summary: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("category_scores", mode="before")
    @classmethod
    def parse_category_scores(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v


class CheckResultResponse(BaseModel):
    id: int
    validation_id: int
    rule_id: int | None = None
    rule_code: str
    rule_name: str | None = None
    category: QCRuleCategoryEnum
    severity: QCRuleSeverityEnum
    status: QCCheckStatusEnum
    executed_at: datetime | None = None
    duration_ms: int | None = None
    expected_value: str | None = None
    actual_value: str | None = None
    score: float | None = None
    message: str | None = None
    error_details: str | None = None
    recommendation: str | None = None
    evidence: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("evidence", mode="before")
    @classmethod
    def parse_evidence(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v


# ============================================================================
# TESTS
# ============================================================================

class QCTestRunCreate(BaseModel):
    module_id: int
    test_type: QCTestTypeEnum
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int = 0
    error_tests: int = 0
    coverage_percent: float | None = None
    test_suite: str | None = None
    duration_seconds: float | None = None
    failed_test_details: dict[str, Any] | None = None
    output_log: str | None = None
    triggered_by: str = "manual"
    validation_id: int | None = None


# Alias pour compatibilité
TestRunCreate = QCTestRunCreate


class QCTestRunResponse(BaseModel):
    id: int
    module_id: int
    validation_id: int | None = None
    test_type: TestTypeEnum
    test_suite: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    status: QCCheckStatusEnum
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    coverage_percent: float | None = None
    triggered_by: str | None = None
    triggered_user: int | None = None

    model_config = ConfigDict(from_attributes=True)


# Alias pour compatibilité
TestRunResponse = QCTestRunResponse


# ============================================================================
# MÉTRIQUES
# ============================================================================

class QCMetricResponse(BaseModel):
    id: int
    module_id: int | None = None
    metric_date: datetime
    modules_total: int
    modules_validated: int
    modules_production: int
    modules_failed: int
    avg_overall_score: float | None = None
    avg_architecture_score: float | None = None
    avg_security_score: float | None = None
    avg_performance_score: float | None = None
    avg_code_quality_score: float | None = None
    avg_testing_score: float | None = None
    avg_documentation_score: float | None = None
    total_tests_run: int
    total_tests_passed: int
    avg_coverage: float | None = None
    total_checks_run: int
    total_checks_passed: int
    critical_issues: int
    blocker_issues: int
    score_trend: str | None = None
    score_delta: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ALERTES
# ============================================================================

class QCAlertCreate(BaseModel):
    alert_type: str
    title: str = Field(..., min_length=2, max_length=200)
    message: str
    severity: QCRuleSeverityEnum = QCRuleSeverityEnum.WARNING
    module_id: int | None = None
    validation_id: int | None = None
    check_result_id: int | None = None
    details: dict[str, Any] | None = None


class QCAlertResponse(BaseModel):
    id: int
    module_id: int | None = None
    validation_id: int | None = None
    check_result_id: int | None = None
    alert_type: str
    severity: QCRuleSeverityEnum
    title: str
    message: str
    details: dict[str, Any] | None = None
    is_read: bool
    is_resolved: bool
    resolved_at: datetime | None = None
    resolved_by: int | None = None
    resolution_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("details", mode="before")
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v


class AlertResolveRequest(BaseModel):
    resolution_notes: str | None = None


# ============================================================================
# DASHBOARDS
# ============================================================================

class QCDashboardCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    layout: dict[str, Any] | None = None
    widgets: list[dict[str, Any]] | None = None
    filters: dict[str, Any] | None = None
    is_default: bool = False
    is_public: bool = False


class QCDashboardUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = None
    layout: dict[str, Any] | None = None
    widgets: list[dict[str, Any]] | None = None
    filters: dict[str, Any] | None = None
    is_default: bool | None = None
    is_public: bool | None = None
    auto_refresh: bool | None = None
    refresh_interval: int | None = None


class QCDashboardResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    layout: dict[str, Any] | None = None
    widgets: list[dict[str, Any]] | None = None
    filters: dict[str, Any] | None = None
    is_default: bool
    is_public: bool
    owner_id: int | None = None
    auto_refresh: bool
    refresh_interval: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("layout", "filters", mode="before")
    @classmethod
    def parse_dict_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v

    @field_validator("widgets", mode="before")
    @classmethod
    def parse_widgets(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v


class DashboardDataResponse(BaseModel):
    summary: dict[str, Any]
    status_distribution: dict[str, int]
    recent_validations: list[dict[str, Any]]
    recent_tests: list[dict[str, Any]]
    critical_alerts: list[dict[str, Any]]


# ============================================================================
# TEMPLATES
# ============================================================================

class QCTemplateCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    rules: list[dict[str, Any]]
    category: str | None = None


class QCTemplateResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    rules: list[dict[str, Any]]
    category: str | None = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("rules", mode="before")
    @classmethod
    def parse_rules(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v


# ============================================================================
# LISTE PAGINÉE
# ============================================================================

class PaginatedRulesResponse(BaseModel):
    items: list[QCRuleResponse]
    total: int
    skip: int
    limit: int


class PaginatedModulesResponse(BaseModel):
    items: list[ModuleRegistryResponse]
    total: int
    skip: int
    limit: int


class PaginatedValidationsResponse(BaseModel):
    items: list[ValidationResponse]
    total: int
    skip: int
    limit: int


class PaginatedCheckResultsResponse(BaseModel):
    items: list[CheckResultResponse]
    total: int
    skip: int
    limit: int


class PaginatedTestRunsResponse(BaseModel):
    items: list[TestRunResponse]
    total: int
    skip: int
    limit: int


class PaginatedAlertsResponse(BaseModel):
    items: list[QCAlertResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# STATISTIQUES
# ============================================================================

class QCStatsResponse(BaseModel):
    total_modules: int
    validated_modules: int
    production_modules: int
    failed_modules: int
    average_score: float
    total_rules: int
    active_rules: int
    unresolved_alerts: int
    tests_run_today: int
    tests_passed_today: int


class ModuleScoreBreakdown(BaseModel):
    module_code: str
    module_name: str
    overall_score: float
    architecture_score: float
    security_score: float
    performance_score: float
    code_quality_score: float
    testing_score: float
    documentation_score: float
    status: ModuleStatusEnum
