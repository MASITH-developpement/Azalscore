"""
Module Risk Management - GAP-075
================================

Gestion des risques:
- Identification des risques
- Évaluation (probabilité x impact)
- Matrices de risques
- Plans de mitigation
- Suivi des actions
- Indicateurs et alertes
- Rapports de risques
"""

# Models
from .models import (
    RiskCategory,
    RiskStatus,
    Probability,
    Impact,
    RiskLevel,
    MitigationStrategy,
    ActionStatus,
    ControlType,
    ControlEffectiveness,
    IndicatorStatus,
    IncidentStatus,
    RiskMatrix,
    Risk,
    Control,
    MitigationAction,
    RiskIndicator,
    RiskAssessment,
    RiskIncident,
)

# Schemas
from .schemas import (
    RiskMatrixCreate, RiskMatrixUpdate, RiskMatrixResponse, RiskMatrixListResponse,
    RiskCreate, RiskUpdate, RiskResponse, RiskListResponse, RiskFilters,
    ControlCreate, ControlUpdate, ControlResponse, ControlListResponse, ControlExecutionRecord,
    ActionCreate, ActionUpdate, ActionResponse, ActionListResponse, ActionProgressUpdate,
    IndicatorCreate, IndicatorUpdate, IndicatorResponse, IndicatorListResponse, IndicatorValueRecord,
    AssessmentCreate, AssessmentValidation, AssessmentResponse, AssessmentListResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentListResponse, IncidentResolution,
    RiskReportRequest, RiskReportResponse, RiskHeatmapResponse, HeatmapCell,
    AutocompleteResponse, BulkResult,
)

# Exceptions
from .exceptions import (
    RiskError,
    RiskMatrixNotFoundError, RiskMatrixDuplicateError, RiskMatrixValidationError,
    RiskMatrixInUseError, DefaultMatrixRequiredError,
    RiskNotFoundError, RiskDuplicateError, RiskValidationError, RiskStateError,
    RiskClosedError, RiskHasActiveActionsError, RiskAccessDeniedError,
    RiskCircularReferenceError,
    ControlNotFoundError, ControlDuplicateError, ControlValidationError,
    ControlInactiveError,
    ActionNotFoundError, ActionDuplicateError, ActionValidationError,
    ActionStateError, ActionCompletedError, ActionCancelledError, ActionProgressError,
    IndicatorNotFoundError, IndicatorDuplicateError, IndicatorValidationError,
    IndicatorThresholdError, IndicatorInactiveError,
    AssessmentNotFoundError, AssessmentValidationError, AssessmentAlreadyValidatedError,
    IncidentNotFoundError, IncidentDuplicateError, IncidentValidationError,
    IncidentStateError, IncidentClosedError, IncidentNotResolvedError,
)

# Repository
from .repository import (
    RiskMatrixRepository,
    RiskRepository,
    ControlRepository,
    MitigationActionRepository,
    RiskIndicatorRepository,
    RiskAssessmentRepository,
    RiskIncidentRepository,
)

# Service
from .service import RiskService

# Router
from .router import router


__all__ = [
    # Enums
    "RiskCategory", "RiskStatus", "Probability", "Impact", "RiskLevel",
    "MitigationStrategy", "ActionStatus", "ControlType", "ControlEffectiveness",
    "IndicatorStatus", "IncidentStatus",
    # Models
    "RiskMatrix", "Risk", "Control", "MitigationAction",
    "RiskIndicator", "RiskAssessment", "RiskIncident",
    # Schemas
    "RiskMatrixCreate", "RiskMatrixUpdate", "RiskMatrixResponse", "RiskMatrixListResponse",
    "RiskCreate", "RiskUpdate", "RiskResponse", "RiskListResponse", "RiskFilters",
    "ControlCreate", "ControlUpdate", "ControlResponse", "ControlListResponse", "ControlExecutionRecord",
    "ActionCreate", "ActionUpdate", "ActionResponse", "ActionListResponse", "ActionProgressUpdate",
    "IndicatorCreate", "IndicatorUpdate", "IndicatorResponse", "IndicatorListResponse", "IndicatorValueRecord",
    "AssessmentCreate", "AssessmentValidation", "AssessmentResponse", "AssessmentListResponse",
    "IncidentCreate", "IncidentUpdate", "IncidentResponse", "IncidentListResponse", "IncidentResolution",
    "RiskReportRequest", "RiskReportResponse", "RiskHeatmapResponse", "HeatmapCell",
    "AutocompleteResponse", "BulkResult",
    # Exceptions
    "RiskError",
    "RiskMatrixNotFoundError", "RiskMatrixDuplicateError", "RiskMatrixValidationError",
    "RiskMatrixInUseError", "DefaultMatrixRequiredError",
    "RiskNotFoundError", "RiskDuplicateError", "RiskValidationError", "RiskStateError",
    "RiskClosedError", "RiskHasActiveActionsError", "RiskAccessDeniedError",
    "RiskCircularReferenceError",
    "ControlNotFoundError", "ControlDuplicateError", "ControlValidationError",
    "ControlInactiveError",
    "ActionNotFoundError", "ActionDuplicateError", "ActionValidationError",
    "ActionStateError", "ActionCompletedError", "ActionCancelledError", "ActionProgressError",
    "IndicatorNotFoundError", "IndicatorDuplicateError", "IndicatorValidationError",
    "IndicatorThresholdError", "IndicatorInactiveError",
    "AssessmentNotFoundError", "AssessmentValidationError", "AssessmentAlreadyValidatedError",
    "IncidentNotFoundError", "IncidentDuplicateError", "IncidentValidationError",
    "IncidentStateError", "IncidentClosedError", "IncidentNotResolvedError",
    # Repository
    "RiskMatrixRepository", "RiskRepository", "ControlRepository",
    "MitigationActionRepository", "RiskIndicatorRepository",
    "RiskAssessmentRepository", "RiskIncidentRepository",
    # Service
    "RiskService",
    # Router
    "router",
]
