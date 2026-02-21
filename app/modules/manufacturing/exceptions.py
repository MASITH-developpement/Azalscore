"""
Exceptions métier Manufacturing / Fabrication
==============================================
"""


class ManufacturingError(Exception):
    """Exception de base du module Manufacturing."""
    pass


# ============== BOM Exceptions ==============

class BOMNotFoundError(ManufacturingError):
    """Nomenclature non trouvée."""
    pass


class BOMDuplicateError(ManufacturingError):
    """Code nomenclature déjà existant."""
    pass


class BOMValidationError(ManufacturingError):
    """Erreur de validation nomenclature."""
    pass


class BOMStateError(ManufacturingError):
    """Transition d'état nomenclature invalide."""
    pass


class BOMLineNotFoundError(ManufacturingError):
    """Ligne de nomenclature non trouvée."""
    pass


# ============== Workcenter Exceptions ==============

class WorkcenterNotFoundError(ManufacturingError):
    """Poste de travail non trouvé."""
    pass


class WorkcenterDuplicateError(ManufacturingError):
    """Code poste de travail déjà existant."""
    pass


class WorkcenterValidationError(ManufacturingError):
    """Erreur de validation poste de travail."""
    pass


class WorkcenterBusyError(ManufacturingError):
    """Poste de travail occupé."""
    pass


# ============== Routing Exceptions ==============

class RoutingNotFoundError(ManufacturingError):
    """Gamme non trouvée."""
    pass


class RoutingDuplicateError(ManufacturingError):
    """Code gamme déjà existant."""
    pass


class RoutingValidationError(ManufacturingError):
    """Erreur de validation gamme."""
    pass


class OperationNotFoundError(ManufacturingError):
    """Opération non trouvée."""
    pass


# ============== Work Order Exceptions ==============

class WorkOrderNotFoundError(ManufacturingError):
    """Ordre de fabrication non trouvé."""
    pass


class WorkOrderDuplicateError(ManufacturingError):
    """Numéro d'OF déjà existant."""
    pass


class WorkOrderValidationError(ManufacturingError):
    """Erreur de validation OF."""
    pass


class WorkOrderStateError(ManufacturingError):
    """Transition d'état OF invalide."""
    pass


class WorkOrderOperationNotFoundError(ManufacturingError):
    """Opération d'OF non trouvée."""
    pass


class WorkOrderOperationStateError(ManufacturingError):
    """Transition d'état d'opération d'OF invalide."""
    pass


# ============== Quality Check Exceptions ==============

class QualityCheckNotFoundError(ManufacturingError):
    """Contrôle qualité non trouvé."""
    pass


class QualityCheckValidationError(ManufacturingError):
    """Erreur de validation contrôle qualité."""
    pass


# ============== Production Log Exceptions ==============

class ProductionLogValidationError(ManufacturingError):
    """Erreur de validation journal de production."""
    pass
