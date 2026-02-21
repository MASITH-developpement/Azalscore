"""
AZALS MODULE CONTRACTS - Exceptions
====================================

Exceptions metier specifiques au module de gestion des contrats.
"""


class ContractError(Exception):
    """Exception de base du module Contracts."""
    pass


# ============================================================================
# CONTRACT ERRORS
# ============================================================================

class ContractNotFoundError(ContractError):
    """Contrat non trouve."""
    def __init__(self, contract_id: str = None, message: str = None):
        self.contract_id = contract_id
        self.message = message or f"Contrat {contract_id} non trouve"
        super().__init__(self.message)


class ContractDuplicateError(ContractError):
    """Numero de contrat deja existant."""
    def __init__(self, contract_number: str = None, message: str = None):
        self.contract_number = contract_number
        self.message = message or f"Le numero de contrat {contract_number} existe deja"
        super().__init__(self.message)


class ContractValidationError(ContractError):
    """Erreur de validation du contrat."""
    def __init__(self, message: str, field: str = None, errors: list = None):
        self.field = field
        self.errors = errors or []
        super().__init__(message)


class ContractStateError(ContractError):
    """Transition d'etat invalide."""
    def __init__(self, current_status: str, target_status: str, message: str = None):
        self.current_status = current_status
        self.target_status = target_status
        self.message = message or f"Transition impossible de {current_status} vers {target_status}"
        super().__init__(self.message)


class ContractNotEditableError(ContractError):
    """Contrat non modifiable dans son etat actuel."""
    def __init__(self, status: str = None, message: str = None):
        self.status = status
        self.message = message or f"Le contrat n'est pas modifiable (statut: {status})"
        super().__init__(self.message)


class ContractAlreadySignedError(ContractError):
    """Contrat deja signe."""
    pass


class ContractNotReadyForSignatureError(ContractError):
    """Contrat pas pret pour signature."""
    def __init__(self, reason: str = None):
        self.reason = reason
        self.message = f"Le contrat n'est pas pret pour signature: {reason}"
        super().__init__(self.message)


class ContractExpiredError(ContractError):
    """Contrat expire."""
    def __init__(self, contract_id: str = None, expired_at: str = None):
        self.contract_id = contract_id
        self.expired_at = expired_at
        self.message = f"Le contrat {contract_id} a expire le {expired_at}"
        super().__init__(self.message)


class ContractTerminatedError(ContractError):
    """Contrat resilie."""
    pass


# ============================================================================
# PARTY ERRORS
# ============================================================================

class PartyNotFoundError(ContractError):
    """Partie non trouvee."""
    def __init__(self, party_id: str = None):
        self.party_id = party_id
        self.message = f"Partie {party_id} non trouvee"
        super().__init__(self.message)


class PartyAlreadySignedError(ContractError):
    """La partie a deja signe."""
    def __init__(self, party_id: str = None):
        self.party_id = party_id
        self.message = f"La partie {party_id} a deja signe"
        super().__init__(self.message)


class PartySignatureRequiredError(ContractError):
    """Signature d'une partie requise."""
    pass


class MissingPartyError(ContractError):
    """Partie manquante dans le contrat."""
    def __init__(self, role: str = None):
        self.role = role
        self.message = f"Une partie avec le role {role} est requise"
        super().__init__(self.message)


# ============================================================================
# LINE ERRORS
# ============================================================================

class ContractLineNotFoundError(ContractError):
    """Ligne de contrat non trouvee."""
    def __init__(self, line_id: str = None):
        self.line_id = line_id
        self.message = f"Ligne {line_id} non trouvee"
        super().__init__(self.message)


class ContractLineValidationError(ContractError):
    """Erreur de validation de ligne."""
    pass


# ============================================================================
# CLAUSE ERRORS
# ============================================================================

class ClauseNotFoundError(ContractError):
    """Clause non trouvee."""
    def __init__(self, clause_id: str = None):
        self.clause_id = clause_id
        self.message = f"Clause {clause_id} non trouvee"
        super().__init__(self.message)


class MandatoryClauseMissingError(ContractError):
    """Clause obligatoire manquante."""
    def __init__(self, clause_title: str = None):
        self.clause_title = clause_title
        self.message = f"La clause obligatoire '{clause_title}' est manquante"
        super().__init__(self.message)


class ClauseNegotiationError(ContractError):
    """Erreur lors de la negociation d'une clause."""
    pass


# ============================================================================
# OBLIGATION ERRORS
# ============================================================================

class ObligationNotFoundError(ContractError):
    """Obligation non trouvee."""
    def __init__(self, obligation_id: str = None):
        self.obligation_id = obligation_id
        self.message = f"Obligation {obligation_id} non trouvee"
        super().__init__(self.message)


class ObligationAlreadyCompletedError(ContractError):
    """Obligation deja completee."""
    pass


class ObligationOverdueError(ContractError):
    """Obligation en retard."""
    def __init__(self, obligation_id: str = None, due_date: str = None):
        self.obligation_id = obligation_id
        self.due_date = due_date
        self.message = f"L'obligation {obligation_id} est en retard (echeance: {due_date})"
        super().__init__(self.message)


# ============================================================================
# MILESTONE ERRORS
# ============================================================================

class MilestoneNotFoundError(ContractError):
    """Jalon non trouve."""
    def __init__(self, milestone_id: str = None):
        self.milestone_id = milestone_id
        self.message = f"Jalon {milestone_id} non trouve"
        super().__init__(self.message)


class MilestoneAlreadyCompletedError(ContractError):
    """Jalon deja complete."""
    pass


class MilestoneDependencyError(ContractError):
    """Dependance de jalon non satisfaite."""
    def __init__(self, milestone_id: str = None, depends_on: str = None):
        self.milestone_id = milestone_id
        self.depends_on = depends_on
        self.message = f"Le jalon {milestone_id} depend du jalon {depends_on} qui n'est pas complete"
        super().__init__(self.message)


# ============================================================================
# AMENDMENT ERRORS
# ============================================================================

class AmendmentNotFoundError(ContractError):
    """Avenant non trouve."""
    def __init__(self, amendment_id: str = None):
        self.amendment_id = amendment_id
        self.message = f"Avenant {amendment_id} non trouve"
        super().__init__(self.message)


class AmendmentNotAllowedError(ContractError):
    """Avenant non autorise dans l'etat actuel du contrat."""
    def __init__(self, status: str = None):
        self.status = status
        self.message = f"Un avenant ne peut pas etre cree sur un contrat avec le statut {status}"
        super().__init__(self.message)


class AmendmentAlreadyAppliedError(ContractError):
    """Avenant deja applique."""
    pass


# ============================================================================
# RENEWAL ERRORS
# ============================================================================

class RenewalNotAllowedError(ContractError):
    """Renouvellement non autorise."""
    def __init__(self, reason: str = None):
        self.reason = reason
        self.message = f"Renouvellement non autorise: {reason}"
        super().__init__(self.message)


class MaxRenewalsReachedError(ContractError):
    """Nombre maximum de renouvellements atteint."""
    def __init__(self, max_renewals: int = None):
        self.max_renewals = max_renewals
        self.message = f"Le nombre maximum de renouvellements ({max_renewals}) a ete atteint"
        super().__init__(self.message)


class RenewalNoticePeriodError(ContractError):
    """Periode de preavis non respectee."""
    def __init__(self, notice_days: int = None, days_remaining: int = None):
        self.notice_days = notice_days
        self.days_remaining = days_remaining
        self.message = f"Le preavis de {notice_days} jours n'est pas respecte ({days_remaining} jours restants)"
        super().__init__(self.message)


# ============================================================================
# APPROVAL ERRORS
# ============================================================================

class ApprovalNotFoundError(ContractError):
    """Approbation non trouvee."""
    def __init__(self, approval_id: str = None):
        self.approval_id = approval_id
        self.message = f"Approbation {approval_id} non trouvee"
        super().__init__(self.message)


class ApprovalNotAuthorizedError(ContractError):
    """Non autorise a approuver."""
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.message = f"L'utilisateur {user_id} n'est pas autorise a approuver ce contrat"
        super().__init__(self.message)


class ApprovalAlreadyProcessedError(ContractError):
    """Approbation deja traitee."""
    def __init__(self, status: str = None):
        self.status = status
        self.message = f"Cette approbation a deja ete traitee (statut: {status})"
        super().__init__(self.message)


class ApprovalRequiredError(ContractError):
    """Approbation requise avant de continuer."""
    def __init__(self, level: int = None):
        self.level = level
        self.message = f"Approbation de niveau {level} requise avant de continuer"
        super().__init__(self.message)


class ApprovalLevelError(ContractError):
    """Erreur de niveau d'approbation."""
    pass


# ============================================================================
# TEMPLATE ERRORS
# ============================================================================

class TemplateNotFoundError(ContractError):
    """Template non trouve."""
    def __init__(self, template_id: str = None):
        self.template_id = template_id
        self.message = f"Template {template_id} non trouve"
        super().__init__(self.message)


class TemplateDuplicateError(ContractError):
    """Code de template deja existant."""
    def __init__(self, code: str = None):
        self.code = code
        self.message = f"Le code de template {code} existe deja"
        super().__init__(self.message)


class TemplateValidationError(ContractError):
    """Erreur de validation du template."""
    pass


class ClauseTemplateNotFoundError(ContractError):
    """Template de clause non trouve."""
    def __init__(self, template_id: str = None):
        self.template_id = template_id
        self.message = f"Template de clause {template_id} non trouve"
        super().__init__(self.message)


# ============================================================================
# CATEGORY ERRORS
# ============================================================================

class CategoryNotFoundError(ContractError):
    """Categorie non trouvee."""
    def __init__(self, category_id: str = None):
        self.category_id = category_id
        self.message = f"Categorie {category_id} non trouvee"
        super().__init__(self.message)


class CategoryDuplicateError(ContractError):
    """Code de categorie deja existant."""
    def __init__(self, code: str = None):
        self.code = code
        self.message = f"Le code de categorie {code} existe deja"
        super().__init__(self.message)


class CategoryHasChildrenError(ContractError):
    """La categorie a des sous-categories."""
    pass


class CategoryHasContractsError(ContractError):
    """La categorie a des contrats associes."""
    pass


# ============================================================================
# DOCUMENT ERRORS
# ============================================================================

class DocumentNotFoundError(ContractError):
    """Document non trouve."""
    def __init__(self, document_id: str = None):
        self.document_id = document_id
        self.message = f"Document {document_id} non trouve"
        super().__init__(self.message)


class DocumentUploadError(ContractError):
    """Erreur lors de l'upload du document."""
    pass


class DocumentSignatureError(ContractError):
    """Erreur lors de la signature du document."""
    pass


# ============================================================================
# ALERT ERRORS
# ============================================================================

class AlertNotFoundError(ContractError):
    """Alerte non trouvee."""
    def __init__(self, alert_id: str = None):
        self.alert_id = alert_id
        self.message = f"Alerte {alert_id} non trouvee"
        super().__init__(self.message)


class AlertAlreadyAcknowledgedError(ContractError):
    """Alerte deja acquittee."""
    pass


# ============================================================================
# SIGNATURE ERRORS
# ============================================================================

class SignatureServiceError(ContractError):
    """Erreur du service de signature."""
    pass


class SignatureRequestError(ContractError):
    """Erreur lors de la demande de signature."""
    pass


class SignatureVerificationError(ContractError):
    """Erreur de verification de signature."""
    pass


# ============================================================================
# BILLING ERRORS
# ============================================================================

class BillingCalculationError(ContractError):
    """Erreur de calcul de facturation."""
    pass


class RecurringBillingError(ContractError):
    """Erreur de facturation recurrente."""
    pass


class PriceRevisionError(ContractError):
    """Erreur de revision tarifaire."""
    pass


# ============================================================================
# WORKFLOW ERRORS
# ============================================================================

class WorkflowError(ContractError):
    """Erreur de workflow."""
    pass


class WorkflowStepError(ContractError):
    """Erreur d'etape de workflow."""
    pass


# ============================================================================
# ACCESS ERRORS
# ============================================================================

class ContractAccessDeniedError(ContractError):
    """Acces au contrat refuse."""
    def __init__(self, contract_id: str = None, user_id: str = None):
        self.contract_id = contract_id
        self.user_id = user_id
        self.message = f"Acces refuse au contrat {contract_id} pour l'utilisateur {user_id}"
        super().__init__(self.message)


class ConfidentialContractError(ContractError):
    """Acces a un contrat confidentiel refuse."""
    pass


# ============================================================================
# OPTIMISTIC LOCKING
# ============================================================================

class ContractVersionConflictError(ContractError):
    """Conflit de version - modification concurrente detectee."""
    def __init__(self, expected_version: int = None, current_version: int = None):
        self.expected_version = expected_version
        self.current_version = current_version
        self.message = (
            f"Conflit de version: version attendue {expected_version}, "
            f"version actuelle {current_version}. Le contrat a ete modifie par un autre utilisateur."
        )
        super().__init__(self.message)
