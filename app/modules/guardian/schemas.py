"""
AZALS MODULE GUARDIAN - Schémas Pydantic
=========================================

Schémas de validation et sérialisation pour l'API GUARDIAN.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from .models import (
    ErrorSeverity,
    ErrorSource,
    ErrorType,
    CorrectionStatus,
    CorrectionAction,
    TestResult,
    Environment,
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
    module: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(None, max_length=500)
    component: Optional[str] = Field(None, max_length=200)
    function_name: Optional[str] = Field(None, max_length=200)
    line_number: Optional[int] = None
    file_path: Optional[str] = Field(None, max_length=500)

    # Contexte utilisateur (pseudonymisé)
    user_role: Optional[str] = Field(None, max_length=50)
    user_id_hash: Optional[str] = Field(None, max_length=64)
    session_id_hash: Optional[str] = Field(None, max_length=64)

    # Détails
    error_code: Optional[str] = Field(None, max_length=50)
    stack_trace: Optional[str] = None
    request_id: Optional[str] = Field(None, max_length=255)
    correlation_id: Optional[str] = Field(None, max_length=255)

    # Contexte technique (pas de données personnelles)
    context_data: Optional[Dict[str, Any]] = None
    http_status: Optional[int] = None
    http_method: Optional[str] = Field(None, max_length=10)


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

    module: Optional[str] = None
    route: Optional[str] = None
    component: Optional[str] = None
    function_name: Optional[str] = None
    error_code: Optional[str] = None

    occurrence_count: int
    is_processed: bool
    is_acknowledged: bool
    correction_id: Optional[int] = None

    detected_at: datetime
    first_occurrence_at: datetime
    last_occurrence_at: datetime


class ErrorDetectionListResponse(BaseModel):
    """Liste paginée de détections d'erreurs."""
    items: List[ErrorDetectionResponse]
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
    route: Optional[str] = Field(None, max_length=500)
    component: Optional[str] = Field(None, max_length=200)
    function_impacted: Optional[str] = Field(None, max_length=200)

    # Rôle utilisateur
    affected_user_role: Optional[str] = Field(None, max_length=50)

    # Cause et correction (OBLIGATOIRES)
    probable_cause: str = Field(..., min_length=10, max_length=5000,
                                description="Cause probable identifiée de l'erreur")
    correction_action: CorrectionAction
    correction_description: str = Field(..., min_length=10, max_length=5000,
                                        description="Description de l'action corrective")
    correction_details: Optional[Dict[str, Any]] = None

    # Impact (OBLIGATOIRE)
    estimated_impact: str = Field(..., min_length=10, max_length=5000,
                                  description="Impact estimé sur le système et les utilisateurs")
    impact_scope: Optional[str] = Field(None, max_length=100)
    affected_entities_count: Optional[int] = None

    # Réversibilité (OBLIGATOIRE)
    is_reversible: bool = Field(..., description="La correction est-elle réversible?")
    reversibility_justification: str = Field(..., min_length=10, max_length=2000,
                                             description="Justification du caractère réversible ou non")
    rollback_procedure: Optional[str] = None

    # Statut initial
    status: CorrectionStatus = CorrectionStatus.PENDING

    # Lien avec erreur détectée
    error_detection_id: Optional[int] = None

    # Erreur originale
    original_error_message: Optional[str] = None
    original_error_code: Optional[str] = Field(None, max_length=50)
    original_stack_trace: Optional[str] = None

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
    route: Optional[str] = None
    component: Optional[str] = None
    function_impacted: Optional[str] = None
    affected_user_role: Optional[str] = None

    # Cause et correction
    probable_cause: str
    correction_action: str
    correction_description: str
    correction_details: Optional[Dict[str, Any]] = None

    # Impact
    estimated_impact: str
    impact_scope: Optional[str] = None
    affected_entities_count: Optional[int] = None

    # Réversibilité
    is_reversible: bool
    reversibility_justification: str
    rollback_procedure: Optional[str] = None

    # Tests et résultats
    tests_executed: Optional[List[Dict[str, Any]]] = None
    correction_result: Optional[str] = None
    correction_successful: Optional[bool] = None

    # Statut
    status: str

    # Validation
    requires_human_validation: bool
    validated_by: Optional[int] = None
    validated_at: Optional[datetime] = None
    validation_comment: Optional[str] = None

    # Exécution
    executed_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    execution_duration_ms: Optional[float] = None

    # Rollback
    rolled_back: bool
    rollback_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None


class CorrectionRegistryListResponse(BaseModel):
    """Liste paginée du registre des corrections."""
    items: List[CorrectionRegistryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CorrectionValidationRequest(BaseModel):
    """Requête de validation d'une correction par un humain."""
    approved: bool = Field(..., description="Approuver ou rejeter la correction")
    comment: Optional[str] = Field(None, max_length=2000,
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
    description: Optional[str] = None

    # Conditions de déclenchement
    trigger_error_type: Optional[ErrorType] = None
    trigger_error_code: Optional[str] = Field(None, max_length=50)
    trigger_module: Optional[str] = Field(None, max_length=100)
    trigger_severity_min: Optional[ErrorSeverity] = None
    trigger_conditions: Optional[Dict[str, Any]] = None

    # Action
    correction_action: CorrectionAction
    action_config: Optional[Dict[str, Any]] = None
    action_script: Optional[str] = None

    # Environnements
    allowed_environments: List[Environment] = [Environment.SANDBOX]

    # Limites
    max_auto_corrections_per_hour: int = Field(10, ge=1, le=1000)
    cooldown_seconds: int = Field(60, ge=0, le=86400)
    requires_human_validation: bool = False

    # Risque
    risk_level: str = Field("LOW", pattern="^(LOW|MEDIUM|HIGH)$")
    is_reversible: bool = True

    # Tests requis
    required_tests: Optional[List[str]] = None


class CorrectionRuleUpdate(BaseModel):
    """Schéma pour mettre à jour une règle de correction."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    trigger_error_type: Optional[ErrorType] = None
    trigger_error_code: Optional[str] = Field(None, max_length=50)
    trigger_module: Optional[str] = Field(None, max_length=100)
    trigger_severity_min: Optional[ErrorSeverity] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    correction_action: Optional[CorrectionAction] = None
    action_config: Optional[Dict[str, Any]] = None
    action_script: Optional[str] = None
    allowed_environments: Optional[List[Environment]] = None
    max_auto_corrections_per_hour: Optional[int] = Field(None, ge=1, le=1000)
    cooldown_seconds: Optional[int] = Field(None, ge=0, le=86400)
    requires_human_validation: Optional[bool] = None
    risk_level: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH)$")
    is_reversible: Optional[bool] = None
    required_tests: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CorrectionRuleResponse(GuardianBaseSchema):
    """Réponse pour une règle de correction."""
    id: int
    rule_uid: str
    tenant_id: str

    name: str
    description: Optional[str] = None
    version: str

    trigger_error_type: Optional[str] = None
    trigger_error_code: Optional[str] = None
    trigger_module: Optional[str] = None
    trigger_severity_min: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None

    correction_action: str
    action_config: Optional[Dict[str, Any]] = None
    allowed_environments: List[str]

    max_auto_corrections_per_hour: int
    cooldown_seconds: int
    requires_human_validation: bool

    risk_level: str
    is_reversible: bool
    required_tests: Optional[List[str]] = None

    total_executions: int
    successful_executions: int
    failed_executions: int
    last_execution_at: Optional[datetime] = None

    is_active: bool
    is_system_rule: bool
    created_at: datetime
    updated_at: datetime


class CorrectionRuleListResponse(BaseModel):
    """Liste paginée des règles de correction."""
    items: List[CorrectionRuleResponse]
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
    test_config: Optional[Dict[str, Any]] = None
    test_input: Optional[Dict[str, Any]] = None
    blocking: bool = True
    triggers_rollback: bool = False


class CorrectionTestResponse(GuardianBaseSchema):
    """Réponse pour un test de correction."""
    id: int
    tenant_id: str
    correction_id: int

    test_name: str
    test_type: str
    test_config: Optional[Dict[str, Any]] = None

    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None

    result: str
    result_details: Optional[Dict[str, Any]] = None
    expected_output: Optional[Dict[str, Any]] = None
    actual_output: Optional[Dict[str, Any]] = None

    error_message: Optional[str] = None
    triggers_rollback: bool
    blocking: bool


class CorrectionTestListResponse(BaseModel):
    """Liste des tests pour une correction."""
    items: List[CorrectionTestResponse]
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
    details: Optional[Dict[str, Any]] = None

    error_detection_id: Optional[int] = None
    correction_id: Optional[int] = None

    target_roles: Optional[List[str]] = None
    target_users: Optional[List[int]] = None

    expires_at: Optional[datetime] = None


class GuardianAlertResponse(GuardianBaseSchema):
    """Réponse pour une alerte."""
    id: int
    alert_uid: str
    tenant_id: str

    alert_type: str
    severity: str
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None

    error_detection_id: Optional[int] = None
    correction_id: Optional[int] = None

    target_roles: Optional[List[str]] = None

    is_read: bool
    read_at: Optional[datetime] = None
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None

    created_at: datetime
    expires_at: Optional[datetime] = None


class GuardianAlertListResponse(BaseModel):
    """Liste paginée des alertes."""
    items: List[GuardianAlertResponse]
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
    comment: Optional[str] = Field(None, max_length=2000)


# ============================================================================
# CONFIG SCHEMAS
# ============================================================================

class GuardianConfigUpdate(BaseModel):
    """Schéma pour mettre à jour la configuration GUARDIAN."""
    is_enabled: Optional[bool] = None
    auto_correction_enabled: Optional[bool] = None
    auto_correction_environments: Optional[List[Environment]] = None
    max_auto_corrections_per_day: Optional[int] = Field(None, ge=0, le=10000)
    max_auto_corrections_production: Optional[int] = Field(None, ge=0, le=100)
    cooldown_between_corrections_seconds: Optional[int] = Field(None, ge=0, le=3600)
    alert_on_critical: Optional[bool] = None
    alert_on_major: Optional[bool] = None
    alert_on_correction_failed: Optional[bool] = None
    alert_on_rollback: Optional[bool] = None
    error_retention_days: Optional[int] = Field(None, ge=1, le=365)
    correction_retention_days: Optional[int] = Field(None, ge=365, le=3650)  # Min 1 an
    alert_retention_days: Optional[int] = Field(None, ge=1, le=365)


class GuardianConfigResponse(GuardianBaseSchema):
    """Réponse pour la configuration GUARDIAN."""
    id: int
    tenant_id: str
    is_enabled: bool
    auto_correction_enabled: bool
    auto_correction_environments: List[str]
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
    errors_by_severity: Dict[str, int]
    errors_by_type: Dict[str, int]
    errors_by_module: Dict[str, int]
    errors_by_source: Dict[str, int]

    # Corrections
    total_corrections: int
    corrections_by_status: Dict[str, int]
    corrections_by_action: Dict[str, int]
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
    alerts_by_severity: Dict[str, int]

    # Performance
    avg_correction_time_ms: Optional[float] = None
    avg_detection_to_correction_time_ms: Optional[float] = None


class GuardianDashboard(BaseModel):
    """Tableau de bord GUARDIAN."""
    statistics: GuardianStatistics
    recent_errors: List[ErrorDetectionResponse]
    pending_validations: List[CorrectionRegistryResponse]
    recent_corrections: List[CorrectionRegistryResponse]
    active_alerts: List[GuardianAlertResponse]
    system_health: Dict[str, Any]


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
    stack_trace: Optional[str] = None
    component: Optional[str] = Field(None, max_length=200)
    route: Optional[str] = Field(None, max_length=500)

    # Contexte browser (pas de données personnelles)
    browser: Optional[str] = Field(None, max_length=100)
    browser_version: Optional[str] = Field(None, max_length=50)
    os: Optional[str] = Field(None, max_length=100)
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None

    # Contexte applicatif
    user_role: Optional[str] = Field(None, max_length=50)
    module: Optional[str] = Field(None, max_length=100)
    action: Optional[str] = Field(None, max_length=100)

    # Métadonnées techniques
    timestamp: datetime
    correlation_id: Optional[str] = Field(None, max_length=255)
    extra_context: Optional[Dict[str, Any]] = None


# ============================================================================
# INCIDENT SCHEMAS (Simplifié pour frontend)
# ============================================================================

class IncidentCreate(BaseModel):
    """
    Schéma pour créer un incident depuis le frontend.
    Format simplifié pour capture rapide des erreurs.
    """
    type: str = Field(..., pattern="^(auth|api|business|js|network|validation)$")
    severity: str = Field(..., pattern="^(info|warning|error|critical)$")
    page: str = Field(..., max_length=500)
    route: str = Field(..., max_length=500)
    endpoint: Optional[str] = Field(None, max_length=500)
    method: Optional[str] = Field(None, max_length=10)
    http_status: Optional[int] = None
    message: str = Field(..., max_length=2000)
    details: Optional[str] = Field(None, max_length=5000)
    stack_trace: Optional[str] = None
    screenshot_data: Optional[str] = None  # Base64 encoded image
    timestamp: datetime


class IncidentResponse(GuardianBaseSchema):
    """Réponse pour un incident créé."""
    id: str
    tenant_id: str
    type: str
    severity: str
    page: str
    route: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    http_status: Optional[int] = None
    message: str
    details: Optional[str] = None
    timestamp: datetime
    created_at: datetime
    has_screenshot: bool
