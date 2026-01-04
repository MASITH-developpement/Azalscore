"""
AZALS MODULE M11 - Conformité (Compliance)
==========================================

Module de gestion de la conformité réglementaire et des politiques.
"""

from .models import (
    Regulation, Requirement, ComplianceAssessment, ComplianceGap,
    ComplianceAction, Policy, PolicyAcknowledgment,
    ComplianceTraining, TrainingCompletion,
    ComplianceDocument, ComplianceAudit, ComplianceAuditFinding,
    ComplianceRisk, ComplianceIncident, ComplianceReport,
    ComplianceStatus, RegulationType, RequirementPriority,
    AssessmentStatus, RiskLevel, ActionStatus, DocumentType,
    AuditStatus, IncidentSeverity, ReportType
)

from .schemas import (
    RegulationCreate, RegulationUpdate, RegulationResponse,
    RequirementCreate, RequirementUpdate, RequirementResponse,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    GapCreate, GapResponse,
    ActionCreate, ActionUpdate, ActionResponse,
    PolicyCreate, PolicyUpdate, PolicyResponse,
    AcknowledgmentCreate, AcknowledgmentResponse,
    TrainingCreate, TrainingUpdate, TrainingResponse,
    CompletionCreate, CompletionResponse,
    DocumentCreate, DocumentUpdate, DocumentResponse,
    AuditCreate, AuditUpdate, AuditResponse,
    FindingCreate, FindingResponse,
    RiskCreate, RiskUpdate, RiskResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse,
    ReportCreate, ReportResponse,
    ComplianceDashboard, ComplianceMetrics
)

from .service import ComplianceService, get_compliance_service
from .router import router

__all__ = [
    # Models
    "Regulation", "Requirement", "ComplianceAssessment", "ComplianceGap",
    "ComplianceAction", "Policy", "PolicyAcknowledgment",
    "ComplianceTraining", "TrainingCompletion",
    "ComplianceDocument", "ComplianceAudit", "ComplianceAuditFinding",
    "ComplianceRisk", "ComplianceIncident", "ComplianceReport",
    # Enums
    "ComplianceStatus", "RegulationType", "RequirementPriority",
    "AssessmentStatus", "RiskLevel", "ActionStatus", "DocumentType",
    "AuditStatus", "IncidentSeverity", "ReportType",
    # Schemas
    "RegulationCreate", "RegulationUpdate", "RegulationResponse",
    "RequirementCreate", "RequirementUpdate", "RequirementResponse",
    "AssessmentCreate", "AssessmentUpdate", "AssessmentResponse",
    "GapCreate", "GapResponse",
    "ActionCreate", "ActionUpdate", "ActionResponse",
    "PolicyCreate", "PolicyUpdate", "PolicyResponse",
    "AcknowledgmentCreate", "AcknowledgmentResponse",
    "TrainingCreate", "TrainingUpdate", "TrainingResponse",
    "CompletionCreate", "CompletionResponse",
    "DocumentCreate", "DocumentUpdate", "DocumentResponse",
    "AuditCreate", "AuditUpdate", "AuditResponse",
    "FindingCreate", "FindingResponse",
    "RiskCreate", "RiskUpdate", "RiskResponse",
    "IncidentCreate", "IncidentUpdate", "IncidentResponse",
    "ReportCreate", "ReportResponse",
    "ComplianceDashboard", "ComplianceMetrics",
    # Service
    "ComplianceService", "get_compliance_service",
    # Router
    "router",
]
