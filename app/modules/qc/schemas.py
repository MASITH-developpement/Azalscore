"""
AZALS MODULE T4 - Schémas Pydantic Contrôle Qualité
====================================================

Schémas de validation pour les API du module QC.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator
import json


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


class TestTypeEnum(str, Enum):
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    E2E = "E2E"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    REGRESSION = "REGRESSION"


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
    description: Optional[str] = None
    category: QCRuleCategoryEnum
    severity: QCRuleSeverityEnum = QCRuleSeverityEnum.WARNING
    check_type: str = Field(..., min_length=2, max_length=50)
    applies_to_modules: Optional[List[str]] = None
    applies_to_phases: Optional[List[str]] = None
    check_config: Optional[Dict[str, Any]] = None
    threshold_value: Optional[float] = None
    threshold_operator: Optional[str] = None


class QCRuleCreate(QCRuleBase):
    pass


class QCRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    severity: Optional[QCRuleSeverityEnum] = None
    applies_to_modules: Optional[List[str]] = None
    applies_to_phases: Optional[List[str]] = None
    check_config: Optional[Dict[str, Any]] = None
    threshold_value: Optional[float] = None
    threshold_operator: Optional[str] = None
    is_active: Optional[bool] = None


class QCRuleResponse(QCRuleBase):
    id: int
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

    @field_validator("applies_to_modules", "applies_to_phases", "check_config", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
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
    description: Optional[str] = None
    dependencies: Optional[List[str]] = None


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
    last_qc_run: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    validated_by: Optional[int] = None
    production_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator("dependencies", mode="before")
    @classmethod
    def parse_dependencies(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
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
    completed_at: Optional[datetime] = None
    started_by: Optional[int] = None
    status: QCCheckStatusEnum
    overall_score: Optional[float] = None
    total_rules: int
    passed_rules: int
    failed_rules: int
    skipped_rules: int
    blocked_rules: int
    category_scores: Optional[Dict[str, Any]] = None
    report_summary: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("category_scores", mode="before")
    @classmethod
    def parse_category_scores(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v


class CheckResultResponse(BaseModel):
    id: int
    validation_id: int
    rule_id: Optional[int] = None
    rule_code: str
    rule_name: Optional[str] = None
    category: QCRuleCategoryEnum
    severity: QCRuleSeverityEnum
    status: QCCheckStatusEnum
    executed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    score: Optional[float] = None
    message: Optional[str] = None
    error_details: Optional[str] = None
    recommendation: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    @field_validator("evidence", mode="before")
    @classmethod
    def parse_evidence(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v


# ============================================================================
# TESTS
# ============================================================================

class TestRunCreate(BaseModel):
    module_id: int
    test_type: TestTypeEnum
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int = 0
    error_tests: int = 0
    coverage_percent: Optional[float] = None
    test_suite: Optional[str] = None
    duration_seconds: Optional[float] = None
    failed_test_details: Optional[Dict[str, Any]] = None
    output_log: Optional[str] = None
    triggered_by: str = "manual"
    validation_id: Optional[int] = None


class TestRunResponse(BaseModel):
    id: int
    module_id: int
    validation_id: Optional[int] = None
    test_type: TestTypeEnum
    test_suite: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: QCCheckStatusEnum
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    coverage_percent: Optional[float] = None
    triggered_by: Optional[str] = None
    triggered_user: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# MÉTRIQUES
# ============================================================================

class QCMetricResponse(BaseModel):
    id: int
    module_id: Optional[int] = None
    metric_date: datetime
    modules_total: int
    modules_validated: int
    modules_production: int
    modules_failed: int
    avg_overall_score: Optional[float] = None
    avg_architecture_score: Optional[float] = None
    avg_security_score: Optional[float] = None
    avg_performance_score: Optional[float] = None
    avg_code_quality_score: Optional[float] = None
    avg_testing_score: Optional[float] = None
    avg_documentation_score: Optional[float] = None
    total_tests_run: int
    total_tests_passed: int
    avg_coverage: Optional[float] = None
    total_checks_run: int
    total_checks_passed: int
    critical_issues: int
    blocker_issues: int
    score_trend: Optional[str] = None
    score_delta: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ALERTES
# ============================================================================

class QCAlertCreate(BaseModel):
    alert_type: str
    title: str = Field(..., min_length=2, max_length=200)
    message: str
    severity: QCRuleSeverityEnum = QCRuleSeverityEnum.WARNING
    module_id: Optional[int] = None
    validation_id: Optional[int] = None
    check_result_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class QCAlertResponse(BaseModel):
    id: int
    module_id: Optional[int] = None
    validation_id: Optional[int] = None
    check_result_id: Optional[int] = None
    alert_type: str
    severity: QCRuleSeverityEnum
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    is_read: bool
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("details", mode="before")
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v


class AlertResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None


# ============================================================================
# DASHBOARDS
# ============================================================================

class QCDashboardCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: bool = False
    is_public: bool = False


class QCDashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None
    auto_refresh: Optional[bool] = None
    refresh_interval: Optional[int] = None


class QCDashboardResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: bool
    is_public: bool
    owner_id: Optional[int] = None
    auto_refresh: bool
    refresh_interval: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator("layout", "filters", mode="before")
    @classmethod
    def parse_dict_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v

    @field_validator("widgets", mode="before")
    @classmethod
    def parse_widgets(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        return v


class DashboardDataResponse(BaseModel):
    summary: Dict[str, Any]
    status_distribution: Dict[str, int]
    recent_validations: List[Dict[str, Any]]
    recent_tests: List[Dict[str, Any]]
    critical_alerts: List[Dict[str, Any]]


# ============================================================================
# TEMPLATES
# ============================================================================

class QCTemplateCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    rules: List[Dict[str, Any]]
    category: Optional[str] = None


class QCTemplateResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    rules: List[Dict[str, Any]]
    category: Optional[str] = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

    @field_validator("rules", mode="before")
    @classmethod
    def parse_rules(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        return v


# ============================================================================
# LISTE PAGINÉE
# ============================================================================

class PaginatedRulesResponse(BaseModel):
    items: List[QCRuleResponse]
    total: int
    skip: int
    limit: int


class PaginatedModulesResponse(BaseModel):
    items: List[ModuleRegistryResponse]
    total: int
    skip: int
    limit: int


class PaginatedValidationsResponse(BaseModel):
    items: List[ValidationResponse]
    total: int
    skip: int
    limit: int


class PaginatedCheckResultsResponse(BaseModel):
    items: List[CheckResultResponse]
    total: int
    skip: int
    limit: int


class PaginatedTestRunsResponse(BaseModel):
    items: List[TestRunResponse]
    total: int
    skip: int
    limit: int


class PaginatedAlertsResponse(BaseModel):
    items: List[QCAlertResponse]
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
