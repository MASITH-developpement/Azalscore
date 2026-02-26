"""
AZALS MODULE - Complaints Exceptions
=====================================

Exceptions personnalisees pour le module de gestion des reclamations.
"""
from __future__ import annotations


from typing import Any


class ComplaintException(Exception):
    """Exception de base pour le module Complaints."""

    def __init__(
        self,
        message: str,
        code: str = "COMPLAINT_ERROR",
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# NOT FOUND EXCEPTIONS
# ============================================================================

class ComplaintNotFoundError(ComplaintException):
    """Reclamation non trouvee."""

    def __init__(self, complaint_id: str | None = None, reference: str | None = None):
        identifier = reference or complaint_id or "unknown"
        super().__init__(
            message=f"Reclamation '{identifier}' non trouvee",
            code="COMPLAINT_NOT_FOUND",
            details={"complaint_id": complaint_id, "reference": reference}
        )


class TeamNotFoundError(ComplaintException):
    """Equipe non trouvee."""

    def __init__(self, team_id: str):
        super().__init__(
            message=f"Equipe '{team_id}' non trouvee",
            code="TEAM_NOT_FOUND",
            details={"team_id": team_id}
        )


class AgentNotFoundError(ComplaintException):
    """Agent non trouve."""

    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent '{agent_id}' non trouve",
            code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id}
        )


class CategoryNotFoundError(ComplaintException):
    """Categorie non trouvee."""

    def __init__(self, category_id: str | None = None, code: str | None = None):
        identifier = code or category_id or "unknown"
        super().__init__(
            message=f"Categorie '{identifier}' non trouvee",
            code="CATEGORY_NOT_FOUND",
            details={"category_id": category_id, "code": code}
        )


class SLAPolicyNotFoundError(ComplaintException):
    """Politique SLA non trouvee."""

    def __init__(self, sla_id: str):
        super().__init__(
            message=f"Politique SLA '{sla_id}' non trouvee",
            code="SLA_POLICY_NOT_FOUND",
            details={"sla_id": sla_id}
        )


class TemplateNotFoundError(ComplaintException):
    """Modele de reponse non trouve."""

    def __init__(self, template_id: str | None = None, code: str | None = None):
        identifier = code or template_id or "unknown"
        super().__init__(
            message=f"Modele '{identifier}' non trouve",
            code="TEMPLATE_NOT_FOUND",
            details={"template_id": template_id, "code": code}
        )


class ActionNotFoundError(ComplaintException):
    """Action non trouvee."""

    def __init__(self, action_id: str):
        super().__init__(
            message=f"Action '{action_id}' non trouvee",
            code="ACTION_NOT_FOUND",
            details={"action_id": action_id}
        )


class ExchangeNotFoundError(ComplaintException):
    """Echange non trouve."""

    def __init__(self, exchange_id: str):
        super().__init__(
            message=f"Echange '{exchange_id}' non trouve",
            code="EXCHANGE_NOT_FOUND",
            details={"exchange_id": exchange_id}
        )


class AttachmentNotFoundError(ComplaintException):
    """Piece jointe non trouvee."""

    def __init__(self, attachment_id: str):
        super().__init__(
            message=f"Piece jointe '{attachment_id}' non trouvee",
            code="ATTACHMENT_NOT_FOUND",
            details={"attachment_id": attachment_id}
        )


class AutomationRuleNotFoundError(ComplaintException):
    """Regle d'automatisation non trouvee."""

    def __init__(self, rule_id: str):
        super().__init__(
            message=f"Regle d'automatisation '{rule_id}' non trouvee",
            code="AUTOMATION_RULE_NOT_FOUND",
            details={"rule_id": rule_id}
        )


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================

class InvalidStatusTransitionError(ComplaintException):
    """Transition de statut invalide."""

    def __init__(self, current_status: str, target_status: str, complaint_id: str | None = None):
        super().__init__(
            message=f"Transition de statut invalide: {current_status} -> {target_status}",
            code="INVALID_STATUS_TRANSITION",
            details={
                "current_status": current_status,
                "target_status": target_status,
                "complaint_id": complaint_id
            }
        )


class InvalidEscalationLevelError(ComplaintException):
    """Niveau d'escalade invalide."""

    def __init__(self, current_level: str, target_level: str):
        super().__init__(
            message=f"Escalade invalide: {current_level} -> {target_level}",
            code="INVALID_ESCALATION_LEVEL",
            details={
                "current_level": current_level,
                "target_level": target_level
            }
        )


class ComplaintAlreadyClosedError(ComplaintException):
    """Reclamation deja cloturee."""

    def __init__(self, complaint_id: str, reference: str | None = None):
        super().__init__(
            message=f"Reclamation '{reference or complaint_id}' deja cloturee",
            code="COMPLAINT_ALREADY_CLOSED",
            details={"complaint_id": complaint_id, "reference": reference}
        )


class ComplaintNotResolvedError(ComplaintException):
    """Reclamation non resolue."""

    def __init__(self, complaint_id: str):
        super().__init__(
            message=f"Reclamation '{complaint_id}' doit etre resolue avant cloture",
            code="COMPLAINT_NOT_RESOLVED",
            details={"complaint_id": complaint_id}
        )


class DuplicateReferenceError(ComplaintException):
    """Reference dupliquee."""

    def __init__(self, reference: str):
        super().__init__(
            message=f"Reference '{reference}' deja existante",
            code="DUPLICATE_REFERENCE",
            details={"reference": reference}
        )


class DuplicateCodeError(ComplaintException):
    """Code duplique."""

    def __init__(self, code: str, entity_type: str):
        super().__init__(
            message=f"Code '{code}' deja existant pour {entity_type}",
            code="DUPLICATE_CODE",
            details={"code": code, "entity_type": entity_type}
        )


class CustomerInfoRequiredError(ComplaintException):
    """Informations client requises."""

    def __init__(self):
        super().__init__(
            message="Au moins un email ou nom de client est requis",
            code="CUSTOMER_INFO_REQUIRED"
        )


class ResolutionRequiredError(ComplaintException):
    """Resolution requise."""

    def __init__(self, complaint_id: str):
        super().__init__(
            message=f"Une resolution est requise pour la reclamation '{complaint_id}'",
            code="RESOLUTION_REQUIRED",
            details={"complaint_id": complaint_id}
        )


# ============================================================================
# PERMISSION EXCEPTIONS
# ============================================================================

class AgentNotAvailableError(ComplaintException):
    """Agent non disponible."""

    def __init__(self, agent_id: str, reason: str = "non disponible"):
        super().__init__(
            message=f"Agent '{agent_id}' {reason}",
            code="AGENT_NOT_AVAILABLE",
            details={"agent_id": agent_id, "reason": reason}
        )


class AgentOverloadedError(ComplaintException):
    """Agent surcharge."""

    def __init__(self, agent_id: str, current_load: int, max_load: int):
        super().__init__(
            message=f"Agent '{agent_id}' surcharge ({current_load}/{max_load})",
            code="AGENT_OVERLOADED",
            details={
                "agent_id": agent_id,
                "current_load": current_load,
                "max_load": max_load
            }
        )


class InsufficientPermissionError(ComplaintException):
    """Permissions insuffisantes."""

    def __init__(self, action: str, agent_id: str | None = None):
        super().__init__(
            message=f"Permissions insuffisantes pour '{action}'",
            code="INSUFFICIENT_PERMISSION",
            details={"action": action, "agent_id": agent_id}
        )


class CompensationLimitExceededError(ComplaintException):
    """Limite de compensation depassee."""

    def __init__(self, requested: float, max_allowed: float, agent_id: str):
        super().__init__(
            message=f"Limite de compensation depassee: {requested} > {max_allowed}",
            code="COMPENSATION_LIMIT_EXCEEDED",
            details={
                "requested": requested,
                "max_allowed": max_allowed,
                "agent_id": agent_id
            }
        )


class ApprovalRequiredError(ComplaintException):
    """Approbation requise."""

    def __init__(self, complaint_id: str, reason: str):
        super().__init__(
            message=f"Approbation requise: {reason}",
            code="APPROVAL_REQUIRED",
            details={"complaint_id": complaint_id, "reason": reason}
        )


# ============================================================================
# SLA EXCEPTIONS
# ============================================================================

class SLABreachWarning(ComplaintException):
    """Avertissement de depassement SLA."""

    def __init__(
        self,
        complaint_id: str,
        sla_type: str,
        due_at: str,
        time_remaining_hours: float
    ):
        super().__init__(
            message=f"Avertissement SLA {sla_type}: {time_remaining_hours:.1f}h restantes",
            code="SLA_BREACH_WARNING",
            details={
                "complaint_id": complaint_id,
                "sla_type": sla_type,
                "due_at": due_at,
                "time_remaining_hours": time_remaining_hours
            }
        )


class SLABreachedError(ComplaintException):
    """SLA depasse."""

    def __init__(self, complaint_id: str, sla_type: str, breached_at: str):
        super().__init__(
            message=f"SLA {sla_type} depasse pour reclamation '{complaint_id}'",
            code="SLA_BREACHED",
            details={
                "complaint_id": complaint_id,
                "sla_type": sla_type,
                "breached_at": breached_at
            }
        )


# ============================================================================
# TEMPLATE EXCEPTIONS
# ============================================================================

class TemplateVariableError(ComplaintException):
    """Erreur de variable dans le modele."""

    def __init__(self, template_id: str, missing_variables: list[str]):
        super().__init__(
            message=f"Variables manquantes dans le modele: {', '.join(missing_variables)}",
            code="TEMPLATE_VARIABLE_ERROR",
            details={
                "template_id": template_id,
                "missing_variables": missing_variables
            }
        )


class TemplateRenderError(ComplaintException):
    """Erreur de rendu du modele."""

    def __init__(self, template_id: str, error: str):
        super().__init__(
            message=f"Erreur de rendu du modele '{template_id}': {error}",
            code="TEMPLATE_RENDER_ERROR",
            details={"template_id": template_id, "error": error}
        )


# ============================================================================
# AUTOMATION EXCEPTIONS
# ============================================================================

class AutomationExecutionError(ComplaintException):
    """Erreur d'execution d'automatisation."""

    def __init__(self, rule_id: str, error: str):
        super().__init__(
            message=f"Erreur d'execution de la regle '{rule_id}': {error}",
            code="AUTOMATION_EXECUTION_ERROR",
            details={"rule_id": rule_id, "error": error}
        )


class InvalidAutomationConditionError(ComplaintException):
    """Condition d'automatisation invalide."""

    def __init__(self, rule_id: str, condition: str):
        super().__init__(
            message=f"Condition invalide dans la regle '{rule_id}': {condition}",
            code="INVALID_AUTOMATION_CONDITION",
            details={"rule_id": rule_id, "condition": condition}
        )


class InvalidAutomationActionError(ComplaintException):
    """Action d'automatisation invalide."""

    def __init__(self, rule_id: str, action: str):
        super().__init__(
            message=f"Action invalide dans la regle '{rule_id}': {action}",
            code="INVALID_AUTOMATION_ACTION",
            details={"rule_id": rule_id, "action": action}
        )


# ============================================================================
# ATTACHMENT EXCEPTIONS
# ============================================================================

class FileTooLargeError(ComplaintException):
    """Fichier trop volumineux."""

    def __init__(self, filename: str, size: int, max_size: int):
        super().__init__(
            message=f"Fichier '{filename}' trop volumineux ({size} > {max_size} bytes)",
            code="FILE_TOO_LARGE",
            details={
                "filename": filename,
                "size": size,
                "max_size": max_size
            }
        )


class InvalidFileTypeError(ComplaintException):
    """Type de fichier invalide."""

    def __init__(self, filename: str, mime_type: str, allowed_types: list[str]):
        super().__init__(
            message=f"Type de fichier '{mime_type}' non autorise pour '{filename}'",
            code="INVALID_FILE_TYPE",
            details={
                "filename": filename,
                "mime_type": mime_type,
                "allowed_types": allowed_types
            }
        )


class FileUploadError(ComplaintException):
    """Erreur d'upload de fichier."""

    def __init__(self, filename: str, error: str):
        super().__init__(
            message=f"Erreur d'upload pour '{filename}': {error}",
            code="FILE_UPLOAD_ERROR",
            details={"filename": filename, "error": error}
        )
