"""
Exceptions métier - Module Approval Workflow (GAP-083)
"""


class ApprovalError(Exception):
    """Exception de base du module Approval."""
    pass


class WorkflowNotFoundError(ApprovalError):
    """Workflow non trouvé."""
    pass


class WorkflowDuplicateError(ApprovalError):
    """Code workflow déjà existant."""
    pass


class WorkflowValidationError(ApprovalError):
    """Erreur de validation workflow."""
    pass


class WorkflowStateError(ApprovalError):
    """Transition d'état workflow invalide."""
    pass


class WorkflowInactiveError(ApprovalError):
    """Workflow inactif."""
    pass


class RequestNotFoundError(ApprovalError):
    """Demande d'approbation non trouvée."""
    pass


class RequestDuplicateError(ApprovalError):
    """Numéro de demande déjà existant."""
    pass


class RequestValidationError(ApprovalError):
    """Erreur de validation demande."""
    pass


class RequestStateError(ApprovalError):
    """Transition d'état demande invalide."""
    pass


class RequestAlreadyProcessedError(ApprovalError):
    """Demande déjà traitée."""
    pass


class ApproverNotAuthorizedError(ApprovalError):
    """Approbateur non autorisé."""
    pass


class ApproverAlreadyActedError(ApprovalError):
    """Approbateur a déjà agi."""
    pass


class CommentsRequiredError(ApprovalError):
    """Commentaires requis pour cette action."""
    pass


class DelegationNotFoundError(ApprovalError):
    """Délégation non trouvée."""
    pass


class DelegationValidationError(ApprovalError):
    """Erreur de validation délégation."""
    pass


class DelegationExpiredError(ApprovalError):
    """Délégation expirée."""
    pass


class EscalationError(ApprovalError):
    """Erreur d'escalade."""
    pass
