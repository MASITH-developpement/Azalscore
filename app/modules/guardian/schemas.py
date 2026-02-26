"""
AZALS MODULE GUARDIAN - Schémas Pydantic
=========================================

Schémas de validation et sérialisation pour l'API GUARDIAN.
"""
from __future__ import annotations


from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    CorrectionAction,
    CorrectionStatus,
    Environment,
    ErrorSeverity,
    ErrorSource,
    ErrorType,
)

# ============================================================================
# SCHEMAS DE BASE
# ============================================================================

class GuardianBaseSchema(BaseModel):
    """Schéma de base avec configuration commune."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ============================================================================
# ERROR DETECTION SCHEMAS
# ============================================================================

class ErrorDetectionCreate(BaseModel):
    """Schéma pour créer une détection d'erreur."""
    severity: ErrorSeverity
    source: ErrorSource
    error_type: ErrorType
    environment: Environment
    error_message: str = Field(..., min_length=1, max_length=10000)

    # Localisation (optionnel)
    module: str | None = Field(None, max_length=100)
    route: str | None = Field(None, max_length=500)
    component: str | None = Field(None, max_length=200)
    function_name: str | None = Field(None, max_length=200)
    line_number: int | None = None
    file_path: str | None = Field(None, max_length=500)

    # Contexte utilisateur (pseudonymisé)
    user_role: str | None = Field(None, max_length=50)
    user_id_hash: str | None = Field(None, max_length=64)
    session_id_hash: str | None = Field(None, max_length=64)

    # Détails
    error_code: str | None = Field(None, max_length=50)
    stack_trace: str | None = None
    request_id: str | None = Field(None, max_length=255)
    correlation_id: str | None = Field(None, max_length=255)

    # Contexte technique (pas de données personnelles)
    context_data: dict[str, Any] | None = None
    http_status: int | None = None
    http_method: str | None = Field(None, max_length=10)


class ErrorDetectionResponse(GuardianBaseSchema):
    """Réponse pour une détection d'erreur."""
    id: int
    error_uid: str
    tenant_id: str
    severity: str
    source: str
    error_type: str
    environment: str
    error_message: str

    module: str | None = None
    route: str | None = None
    component: str | None = None
    function_name: str | None = None
    error_code: str | None = None

    occurrence_count: int
    is_processed: bool
    is_acknowledged: bool
    correction_id: int | None = None

    detected_at: datetime
    first_occurrence_at: datetime
    last_occurrence_at: datetime


class ErrorDetectionListResponse(BaseModel):
    """Liste paginée de détections d'erreurs."""
    items: list[ErrorDetectionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# CORRECTION REGISTRY SCHEMAS
# ============================================================================

class CorrectionRegistryCreate(BaseModel):
    """
    Schéma pour créer une entrée dans le registre des corrections.
    TOUS les champs obligatoires selon les exigences sont requis.
    """
    # Champs obligatoires
    environment: Environment
    error_source: ErrorSource
    error_type: ErrorType
    severity: ErrorSeverity
    module: str = Field(..., min_length=1, max_length=100)

    # Localisation
    route: str | None = Field(None, max_length=500)
    component: str | None = Field(None, max_length=200)
    function_impacted: str | None = Field(None, max_length=200)

    # Rôle utilisateur
    affected_user_role: str | None = Field(None, max_length=50)

    # Cause et correction (OBLIGATOIRES)
    probable_cause: str = Field(..., min_length=10, max_length=5000,
                                description="Cause probable identifiée de l'erreur")
    correction_action: CorrectionAction
    correction_description: str = Field(..., min_length=10, max_length=5000,
                                        description="Description de l'action corrective")
    correction_details: dict[str, Any] | None = None

    # Impact (OBLIGATOIRE)
    estimated_impact: str = Field(..., min_length=10, max_length=5000,
                                  description="Impact estimé sur le système et les utilisateurs")
    impact_scope: str | None = Field(None, max_length=100)
    affected_entities_count: int | None = None

    # Réversibilité (OBLIGATOIRE)
    is_reversible: bool = Field(..., description="La correction est-elle réversible?")
    reversibility_justification: str = Field(..., min_length=10, max_length=2000,
                                             description="Justification du caractère réversible ou non")
    rollback_procedure: str | None = None

    # Statut initial
    status: CorrectionStatus = CorrectionStatus.PENDING

    # Lien avec erreur détectée
    error_detection_id: int | None = None

    # Erreur originale
    original_error_message: str | None = None
    original_error_code: str | None = Field(None, max_length=50)
    original_stack_trace: str | None = None

    # Validation humaine
    requires_human_validation: bool = False


class CorrectionRegistryResponse(GuardianBaseSchema):
    """Réponse pour une entrée du registre des corrections."""
    id: int
    correction_uid: str
    tenant_id: str
    created_at: datetime

    # Classification
    environment: str
    error_source: str
    error_type: str
    severity: str
    module: str

    # Localisation
    route: str | None = None
    component: str | None = None
    function_impacted: str | None = None
    affected_user_role: str | None = None

    # Cause et correction
    probable_cause: str
    correction_action: str
    correction_description: str
    correction_details: dict[str, Any] | None = None

    # Impact
    estimated_impact: str
    impact_scope: str | None = None
    affected_entities_count: int | None = None

    # Réversibilité
    is_reversible: bool
    reversibility_justification: str
    rollback_procedure: str | None = None

    # Tests et résultats
    tests_executed: list[dict[str, Any]] | None = None
    correction_result: str | None = None
    correction_successful: bool | None = None

    # Statut
    status: str

    # Validation
    requires_human_validation: bool
    validated_by: int | None = None
    validated_at: datetime | None = None
    validation_comment: str | None = None

    # Exécution
    executed_by: str | None = None
    executed_at: datetime | None = None
    execution_duration_ms: float | None = None

    # Rollback
    rolled_back: bool
    rollback_at: datetime | None = None
    rollback_reason: str | None = None


class CorrectionRegistryListResponse(BaseModel):
    """Liste paginée du registre des corrections."""
    items: list[CorrectionRegistryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CorrectionValidationRequest(BaseModel):
    """Requête de validation d'une correction par un humain."""
    approved: bool = Field(..., description="Approuver ou rejeter la correction")
    comment: str | None = Field(None, max_length=2000,
                                   description="Commentaire de validation")


class CorrectionRollbackRequest(BaseModel):
    """Requête de rollback d'une correction."""
    reason: str = Field(..., min_length=10, max_length=2000,
                        description="Raison du rollback")


# ============================================================================
# CORRECTION RULE SCHEMAS
# ============================================================================

class CorrectionRuleCreate(BaseModel):
    """Schéma pour créer une règle de correction."""
    name: str = Field(..., min_length=3, max_length=200)
    description: str | None = None

    # Conditions de déclenchement
    trigger_error_type: ErrorType | None = None
    trigger_error_code: str | None = Field(None, max_length=50)
    trigger_module: str | None = Field(None, max_length=100)
    trigger_severity_min: ErrorSeverity | None = None
    trigger_conditions: dict[str, Any] | None = None

    # Action
    correction_action: CorrectionAction
    action_config: dict[str, Any] | None = None
    action_script: str | None = None

    # Environnements
    allowed_environments: list[Environment] = [Environment.SANDBOX]

    # Limites
    max_auto_corrections_per_hour: int = Field(10, ge=1, le=1000)
    cooldown_seconds: int = Field(60, ge=0, le=86400)
    requires_human_validation: bool = False

    # Risque
    risk_level: str = Field("LOW", pattern="^(LOW|MEDIUM|HIGH)$")
    is_reversible: bool = True

    # Tests requis
    required_tests: list[str] | None = None


class CorrectionRuleUpdate(BaseModel):
    """Schéma pour mettre à jour une règle de correction."""
    name: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    trigger_error_type: ErrorType | None = None
    trigger_error_code: str | None = Field(None, max_length=50)
    trigger_module: str | None = Field(None, max_length=100)
    trigger_severity_min: ErrorSeverity | None = None
    trigger_conditions: dict[str, Any] | None = None
    correction_action: CorrectionAction | None = None
    action_config: dict[str, Any] | None = None
    action_script: str | None = None
    allowed_environments: list[Environment] | None = None
    max_auto_corrections_per_hour: int | None = Field(None, ge=1, le=1000)
    cooldown_seconds: int | None = Field(None, ge=0, le=86400)
    requires_human_validation: bool | None = None
    risk_level: str | None = Field(None, pattern="^(LOW|MEDIUM|HIGH)$")
    is_reversible: bool | None = None
    required_tests: list[str] | None = None
    is_active: bool | None = None


class CorrectionRuleResponse(GuardianBaseSchema):
    """Réponse pour une règle de correction."""
    id: int
    rule_uid: str
    tenant_id: str

    name: str
    description: str | None = None
    version: str

    trigger_error_type: str | None = None
    trigger_error_code: str | None = None
    trigger_module: str | None = None
    trigger_severity_min: str | None = None
    trigger_conditions: dict[str, Any] | None = None

    correction_action: str
    action_config: dict[str, Any] | None = None
    allowed_environments: list[str]

    max_auto_corrections_per_hour: int
    cooldown_seconds: int
    requires_human_validation: bool

    risk_level: str
    is_reversible: bool
    required_tests: list[str] | None = None

    total_executions: int
    successful_executions: int
    failed_executions: int
    last_execution_at: datetime | None = None

    is_active: bool
    is_system_rule: bool
    created_at: datetime
    updated_at: datetime


class CorrectionRuleListResponse(BaseModel):
    """Liste paginée des règles de correction."""
    items: list[CorrectionRuleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# CORRECTION TEST SCHEMAS
# ============================================================================

class CorrectionTestCreate(BaseModel):
    """Schéma pour créer un test de correction."""
    correction_id: int
    test_name: str = Field(..., max_length=200)
    test_type: str = Field(..., pattern="^(SCENARIO|REGRESSION|PERSISTENCE|PERMISSION|ACCESS)$")
    test_config: dict[str, Any] | None = None
    test_input: dict[str, Any] | None = None
    blocking: bool = True
    triggers_rollback: bool = False


class CorrectionTestResponse(GuardianBaseSchema):
    """Réponse pour un test de correction."""
    id: int
    tenant_id: str
    correction_id: int

    test_name: str
    test_type: str
    test_config: dict[str, Any] | None = None

    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = None

    result: str
    result_details: dict[str, Any] | None = None
    expected_output: dict[str, Any] | None = None
    actual_output: dict[str, Any] | None = None

    error_message: str | None = None
    triggers_rollback: bool
    blocking: bool


class CorrectionTestListResponse(BaseModel):
    """Liste des tests pour une correction."""
    items: list[CorrectionTestResponse]
    total: int


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class GuardianAlertCreate(BaseModel):
    """Schéma pour créer une alerte."""
    alert_type: str = Field(..., max_length=50)
    severity: ErrorSeverity
    title: str = Field(..., max_length=500)
    message: str
    details: dict[str, Any] | None = None

    error_detection_id: int | None = None
    correction_id: int | None = None

    target_roles: list[str] | None = None
    target_users: list[int] | None = None

    expires_at: datetime | None = None


class GuardianAlertResponse(GuardianBaseSchema):
    """Réponse pour une alerte."""
    id: int
    alert_uid: str
    tenant_id: str

    alert_type: str
    severity: str
    title: str
    message: str
    details: dict[str, Any] | None = None

    error_detection_id: int | None = None
    correction_id: int | None = None

    target_roles: list[str] | None = None

    is_read: bool
    read_at: datetime | None = None
    is_acknowledged: bool
    acknowledged_at: datetime | None = None
    is_resolved: bool
    resolved_at: datetime | None = None
    resolution_comment: str | None = None

    created_at: datetime
    expires_at: datetime | None = None


class GuardianAlertListResponse(BaseModel):
    """Liste paginée des alertes."""
    items: list[GuardianAlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    unread_count: int


class AlertAcknowledgeRequest(BaseModel):
    """Requête d'acquittement d'une alerte."""
    pass  # Pas de champs requis


class AlertResolveRequest(BaseModel):
    """Requête de résolution d'une alerte."""
    comment: str | None = Field(None, max_length=2000)


# ============================================================================
# CONFIG SCHEMAS
# ============================================================================

class GuardianConfigUpdate(BaseModel):
    """Schéma pour mettre à jour la configuration GUARDIAN."""
    is_enabled: bool | None = None
    auto_correction_enabled: bool | None = None
    auto_correction_environments: list[Environment] | None = None
    max_auto_corrections_per_day: int | None = Field(None, ge=0, le=10000)
    max_auto_corrections_production: int | None = Field(None, ge=0, le=100)
    cooldown_between_corrections_seconds: int | None = Field(None, ge=0, le=3600)
    alert_on_critical: bool | None = None
    alert_on_major: bool | None = None
    alert_on_correction_failed: bool | None = None
    alert_on_rollback: bool | None = None
    error_retention_days: int | None = Field(None, ge=1, le=365)
    correction_retention_days: int | None = Field(None, ge=365, le=3650)  # Min 1 an
    alert_retention_days: int | None = Field(None, ge=1, le=365)


class GuardianConfigResponse(GuardianBaseSchema):
    """Réponse pour la configuration GUARDIAN."""
    id: int
    tenant_id: str
    is_enabled: bool
    auto_correction_enabled: bool
    auto_correction_environments: list[str]
    max_auto_corrections_per_day: int
    max_auto_corrections_production: int
    cooldown_between_corrections_seconds: int
    alert_on_critical: bool
    alert_on_major: bool
    alert_on_correction_failed: bool
    alert_on_rollback: bool
    error_retention_days: int
    correction_retention_days: int
    alert_retention_days: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# STATISTICS & DASHBOARD SCHEMAS
# ============================================================================

class GuardianStatistics(BaseModel):
    """Statistiques GUARDIAN."""
    period_start: datetime
    period_end: datetime

    # Erreurs
    total_errors_detected: int
    errors_by_severity: dict[str, int]
    errors_by_type: dict[str, int]
    errors_by_module: dict[str, int]
    errors_by_source: dict[str, int]

    # Corrections
    total_corrections: int
    corrections_by_status: dict[str, int]
    corrections_by_action: dict[str, int]
    auto_corrections_count: int
    manual_corrections_count: int
    successful_corrections: int
    failed_corrections: int
    rollback_count: int

    # Tests
    total_tests_executed: int
    tests_passed: int
    tests_failed: int

    # Alertes
    total_alerts: int
    unresolved_alerts: int
    alerts_by_severity: dict[str, int]

    # Performance
    avg_correction_time_ms: float | None = None
    avg_detection_to_correction_time_ms: float | None = None


class GuardianDashboard(BaseModel):
    """Tableau de bord GUARDIAN."""
    statistics: GuardianStatistics
    recent_errors: list[ErrorDetectionResponse]
    pending_validations: list[CorrectionRegistryResponse]
    recent_corrections: list[CorrectionRegistryResponse]
    active_alerts: list[GuardianAlertResponse]
    system_health: dict[str, Any]


# ============================================================================
# FRONTEND ERROR REPORTING
# ============================================================================

class FrontendErrorReport(BaseModel):
    """
    Rapport d'erreur frontend.
    Utilisé par le frontend pour signaler des erreurs au backend.
    """
    error_type: str = Field(..., max_length=50)
    error_message: str = Field(..., max_length=5000)
    stack_trace: str | None = None
    component: str | None = Field(None, max_length=200)
    route: str | None = Field(None, max_length=500)

    # Contexte browser (pas de données personnelles)
    browser: str | None = Field(None, max_length=100)
    browser_version: str | None = Field(None, max_length=50)
    os: str | None = Field(None, max_length=100)
    viewport_width: int | None = None
    viewport_height: int | None = None

    # Contexte applicatif
    user_role: str | None = Field(None, max_length=50)
    module: str | None = Field(None, max_length=100)
    action: str | None = Field(None, max_length=100)

    # Métadonnées techniques
    timestamp: datetime
    correlation_id: str | None = Field(None, max_length=255)
    extra_context: dict[str, Any] | None = None


# ============================================================================
# INCIDENT SCHEMAS (Frontend)
# ============================================================================

class IncidentCreate(BaseModel):
    """Schéma pour créer un incident depuis le frontend."""
    type: str = Field(..., max_length=20)  # auth, api, business, js, network, validation
    severity: str = Field(..., max_length=20)  # info, warning, error, critical

    # Localisation
    page: str = Field(..., max_length=500)
    route: str = Field(..., max_length=500)

    # HTTP (optionnel)
    endpoint: str | None = Field(None, max_length=500)
    method: str | None = Field(None, max_length=10)
    http_status: int | None = None

    # Détails
    message: str = Field(..., min_length=1)
    details: str | None = None
    stack_trace: str | None = None

    # Screenshot (base64)
    screenshot_data: str | None = None

    # Timestamp frontend
    frontend_timestamp: datetime


class IncidentResponse(GuardianBaseSchema):
    """Réponse pour un incident."""
    id: str  # UUID as string
    incident_uid: str
    tenant_id: str

    type: str
    severity: str

    user_id: str | None = None
    user_role: str | None = None

    page: str
    route: str

    endpoint: str | None = None
    method: str | None = None
    http_status: int | None = None

    message: str
    details: str | None = None
    stack_trace: str | None = None

    screenshot_path: str | None = None
    has_screenshot: bool

    frontend_timestamp: datetime
    guardian_actions: list[dict] | None = None

    is_processed: bool
    is_resolved: bool
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None

    created_at: datetime
