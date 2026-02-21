"""
Exceptions métier Requisition / Demandes d'achat
================================================
"""


class RequisitionError(Exception):
    """Exception de base du module Requisition."""
    pass


# ============== CatalogCategory Exceptions ==============

class CatalogCategoryNotFoundError(RequisitionError):
    """Catégorie non trouvée."""
    pass


class CatalogCategoryDuplicateError(RequisitionError):
    """Code catégorie déjà existant."""
    pass


class CatalogCategoryValidationError(RequisitionError):
    """Erreur de validation catégorie."""
    pass


# ============== CatalogItem Exceptions ==============

class CatalogItemNotFoundError(RequisitionError):
    """Article catalogue non trouvé."""
    pass


class CatalogItemDuplicateError(RequisitionError):
    """Code article déjà existant."""
    pass


class CatalogItemValidationError(RequisitionError):
    """Erreur de validation article."""
    pass


class CatalogItemInactiveError(RequisitionError):
    """Article catalogue inactif."""
    pass


# ============== PreferredVendor Exceptions ==============

class PreferredVendorNotFoundError(RequisitionError):
    """Fournisseur préféré non trouvé."""
    pass


class PreferredVendorDuplicateError(RequisitionError):
    """Fournisseur préféré déjà existant."""
    pass


class PreferredVendorValidationError(RequisitionError):
    """Erreur de validation fournisseur."""
    pass


# ============== BudgetAllocation Exceptions ==============

class BudgetAllocationNotFoundError(RequisitionError):
    """Allocation budgétaire non trouvée."""
    pass


class BudgetAllocationDuplicateError(RequisitionError):
    """Allocation budgétaire déjà existante."""
    pass


class BudgetAllocationValidationError(RequisitionError):
    """Erreur de validation allocation."""
    pass


class BudgetExceededError(RequisitionError):
    """Budget dépassé."""
    pass


class InsufficientBudgetError(RequisitionError):
    """Budget insuffisant."""
    pass


# ============== Requisition Exceptions ==============

class RequisitionNotFoundError(RequisitionError):
    """Demande d'achat non trouvée."""
    pass


class RequisitionDuplicateError(RequisitionError):
    """Numéro de demande déjà existant."""
    pass


class RequisitionValidationError(RequisitionError):
    """Erreur de validation demande."""
    pass


class RequisitionStateError(RequisitionError):
    """Transition d'état demande invalide."""
    pass


class RequisitionClosedError(RequisitionError):
    """Demande fermée, modification impossible."""
    pass


class RequisitionEmptyError(RequisitionError):
    """Demande sans lignes."""
    pass


# ============== RequisitionLine Exceptions ==============

class RequisitionLineNotFoundError(RequisitionError):
    """Ligne de demande non trouvée."""
    pass


class RequisitionLineValidationError(RequisitionError):
    """Erreur de validation ligne."""
    pass


# ============== Approval Exceptions ==============

class ApprovalStepNotFoundError(RequisitionError):
    """Étape d'approbation non trouvée."""
    pass


class ApprovalNotAuthorizedError(RequisitionError):
    """Utilisateur non autorisé à approuver."""
    pass


class ApprovalAlreadyProcessedError(RequisitionError):
    """Étape déjà traitée."""
    pass


class ApprovalPendingError(RequisitionError):
    """Approbation en attente."""
    pass


class NoApproverError(RequisitionError):
    """Aucun approbateur défini."""
    pass


# ============== Template Exceptions ==============

class TemplateNotFoundError(RequisitionError):
    """Modèle non trouvé."""
    pass


class TemplateDuplicateError(RequisitionError):
    """Code modèle déjà existant."""
    pass


class TemplateValidationError(RequisitionError):
    """Erreur de validation modèle."""
    pass


# ============== Order Exceptions ==============

class OrderGenerationError(RequisitionError):
    """Erreur lors de la génération de commande."""
    pass


class OrderAlreadyGeneratedError(RequisitionError):
    """Commande déjà générée."""
    pass
