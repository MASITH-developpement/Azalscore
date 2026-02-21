"""
AZALS MODULE ASSETS - Exceptions
================================

Exceptions personnalisees pour le module de gestion des immobilisations.
"""

from typing import Any


class AssetModuleError(Exception):
    """Exception de base pour le module Assets."""

    def __init__(self, message: str, code: str = "ASSET_ERROR", details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# EXCEPTIONS - CATEGORIES
# ============================================================================

class CategoryNotFoundError(AssetModuleError):
    """Categorie non trouvee."""

    def __init__(self, category_id: str):
        super().__init__(
            message=f"Categorie {category_id} non trouvee",
            code="CATEGORY_NOT_FOUND",
            details={"category_id": category_id}
        )


class CategoryCodeExistsError(AssetModuleError):
    """Code categorie deja utilise."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Le code categorie '{code}' existe deja",
            code="CATEGORY_CODE_EXISTS",
            details={"code": code}
        )


class CategoryHasAssetsError(AssetModuleError):
    """Categorie contient des actifs."""

    def __init__(self, category_id: str, count: int):
        super().__init__(
            message=f"Impossible de supprimer la categorie: {count} actif(s) associe(s)",
            code="CATEGORY_HAS_ASSETS",
            details={"category_id": category_id, "assets_count": count}
        )


class CategoryHasChildrenError(AssetModuleError):
    """Categorie contient des sous-categories."""

    def __init__(self, category_id: str, count: int):
        super().__init__(
            message=f"Impossible de supprimer la categorie: {count} sous-categorie(s)",
            code="CATEGORY_HAS_CHILDREN",
            details={"category_id": category_id, "children_count": count}
        )


# ============================================================================
# EXCEPTIONS - ACTIFS
# ============================================================================

class AssetNotFoundError(AssetModuleError):
    """Actif non trouve."""

    def __init__(self, asset_id: str):
        super().__init__(
            message=f"Immobilisation {asset_id} non trouvee",
            code="ASSET_NOT_FOUND",
            details={"asset_id": asset_id}
        )


class AssetCodeExistsError(AssetModuleError):
    """Code actif deja utilise."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Le code immobilisation '{code}' existe deja",
            code="ASSET_CODE_EXISTS",
            details={"code": code}
        )


class AssetAlreadyInServiceError(AssetModuleError):
    """Actif deja en service."""

    def __init__(self, asset_id: str):
        super().__init__(
            message="Cette immobilisation est deja en service",
            code="ASSET_ALREADY_IN_SERVICE",
            details={"asset_id": asset_id}
        )


class AssetNotInServiceError(AssetModuleError):
    """Actif pas en service."""

    def __init__(self, asset_id: str):
        super().__init__(
            message="Cette immobilisation n'est pas en service",
            code="ASSET_NOT_IN_SERVICE",
            details={"asset_id": asset_id}
        )


class AssetAlreadyDisposedError(AssetModuleError):
    """Actif deja cede."""

    def __init__(self, asset_id: str):
        super().__init__(
            message="Cette immobilisation a deja ete cedee ou mise au rebut",
            code="ASSET_ALREADY_DISPOSED",
            details={"asset_id": asset_id}
        )


class AssetHasComponentsError(AssetModuleError):
    """Actif a des composants."""

    def __init__(self, asset_id: str, count: int):
        super().__init__(
            message=f"Impossible de ceder: {count} composant(s) attache(s)",
            code="ASSET_HAS_COMPONENTS",
            details={"asset_id": asset_id, "components_count": count}
        )


class AssetInvalidStatusTransitionError(AssetModuleError):
    """Transition de statut invalide."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            message=f"Transition de statut invalide: {current_status} -> {target_status}",
            code="INVALID_STATUS_TRANSITION",
            details={"current_status": current_status, "target_status": target_status}
        )


class AssetLockedError(AssetModuleError):
    """Actif verrouille (periode cloturee)."""

    def __init__(self, asset_id: str, reason: str):
        super().__init__(
            message=f"Immobilisation verrouillee: {reason}",
            code="ASSET_LOCKED",
            details={"asset_id": asset_id, "reason": reason}
        )


# ============================================================================
# EXCEPTIONS - AMORTISSEMENT
# ============================================================================

class DepreciationCalculationError(AssetModuleError):
    """Erreur de calcul d'amortissement."""

    def __init__(self, asset_id: str, reason: str):
        super().__init__(
            message=f"Erreur de calcul d'amortissement: {reason}",
            code="DEPRECIATION_CALCULATION_ERROR",
            details={"asset_id": asset_id, "reason": reason}
        )


class DepreciationAlreadyPostedError(AssetModuleError):
    """Amortissement deja comptabilise."""

    def __init__(self, period: str):
        super().__init__(
            message=f"Les amortissements de la periode {period} sont deja comptabilises",
            code="DEPRECIATION_ALREADY_POSTED",
            details={"period": period}
        )


class DepreciationRunNotFoundError(AssetModuleError):
    """Execution amortissement non trouvee."""

    def __init__(self, run_id: str):
        super().__init__(
            message=f"Execution d'amortissement {run_id} non trouvee",
            code="DEPRECIATION_RUN_NOT_FOUND",
            details={"run_id": run_id}
        )


class InvalidDepreciationMethodError(AssetModuleError):
    """Methode d'amortissement invalide."""

    def __init__(self, method: str, reason: str):
        super().__init__(
            message=f"Methode d'amortissement invalide ({method}): {reason}",
            code="INVALID_DEPRECIATION_METHOD",
            details={"method": method, "reason": reason}
        )


class UsefulLifeNotSetError(AssetModuleError):
    """Duree d'utilisation non definie."""

    def __init__(self, asset_id: str):
        super().__init__(
            message="La duree d'utilisation doit etre definie pour calculer l'amortissement",
            code="USEFUL_LIFE_NOT_SET",
            details={"asset_id": asset_id}
        )


# ============================================================================
# EXCEPTIONS - MOUVEMENTS
# ============================================================================

class MovementNotFoundError(AssetModuleError):
    """Mouvement non trouve."""

    def __init__(self, movement_id: str):
        super().__init__(
            message=f"Mouvement {movement_id} non trouve",
            code="MOVEMENT_NOT_FOUND",
            details={"movement_id": movement_id}
        )


class MovementAlreadyPostedError(AssetModuleError):
    """Mouvement deja comptabilise."""

    def __init__(self, movement_id: str):
        super().__init__(
            message="Ce mouvement est deja comptabilise et ne peut etre modifie",
            code="MOVEMENT_ALREADY_POSTED",
            details={"movement_id": movement_id}
        )


class InvalidMovementAmountError(AssetModuleError):
    """Montant de mouvement invalide."""

    def __init__(self, amount: str, reason: str):
        super().__init__(
            message=f"Montant de mouvement invalide ({amount}): {reason}",
            code="INVALID_MOVEMENT_AMOUNT",
            details={"amount": amount, "reason": reason}
        )


# ============================================================================
# EXCEPTIONS - MAINTENANCE
# ============================================================================

class MaintenanceNotFoundError(AssetModuleError):
    """Maintenance non trouvee."""

    def __init__(self, maintenance_id: str):
        super().__init__(
            message=f"Maintenance {maintenance_id} non trouvee",
            code="MAINTENANCE_NOT_FOUND",
            details={"maintenance_id": maintenance_id}
        )


class MaintenanceAlreadyCompletedError(AssetModuleError):
    """Maintenance deja terminee."""

    def __init__(self, maintenance_id: str):
        super().__init__(
            message="Cette maintenance est deja terminee",
            code="MAINTENANCE_ALREADY_COMPLETED",
            details={"maintenance_id": maintenance_id}
        )


class MaintenanceInvalidStatusError(AssetModuleError):
    """Statut de maintenance invalide."""

    def __init__(self, current_status: str, action: str):
        super().__init__(
            message=f"Action '{action}' impossible avec le statut '{current_status}'",
            code="MAINTENANCE_INVALID_STATUS",
            details={"current_status": current_status, "action": action}
        )


# ============================================================================
# EXCEPTIONS - INVENTAIRE
# ============================================================================

class InventoryNotFoundError(AssetModuleError):
    """Inventaire non trouve."""

    def __init__(self, inventory_id: str):
        super().__init__(
            message=f"Inventaire {inventory_id} non trouve",
            code="INVENTORY_NOT_FOUND",
            details={"inventory_id": inventory_id}
        )


class InventoryAlreadyCompletedError(AssetModuleError):
    """Inventaire deja termine."""

    def __init__(self, inventory_id: str):
        super().__init__(
            message="Cet inventaire est deja termine",
            code="INVENTORY_ALREADY_COMPLETED",
            details={"inventory_id": inventory_id}
        )


class InventoryItemNotFoundError(AssetModuleError):
    """Element d'inventaire non trouve."""

    def __init__(self, item_id: str):
        super().__init__(
            message=f"Element d'inventaire {item_id} non trouve",
            code="INVENTORY_ITEM_NOT_FOUND",
            details={"item_id": item_id}
        )


class InventoryInProgressError(AssetModuleError):
    """Un inventaire est deja en cours."""

    def __init__(self, location: str | None = None):
        super().__init__(
            message="Un inventaire est deja en cours" + (f" pour {location}" if location else ""),
            code="INVENTORY_IN_PROGRESS",
            details={"location": location}
        )


# ============================================================================
# EXCEPTIONS - ASSURANCE
# ============================================================================

class InsurancePolicyNotFoundError(AssetModuleError):
    """Police d'assurance non trouvee."""

    def __init__(self, policy_id: str):
        super().__init__(
            message=f"Police d'assurance {policy_id} non trouvee",
            code="INSURANCE_POLICY_NOT_FOUND",
            details={"policy_id": policy_id}
        )


class InsurancePolicyExpiredError(AssetModuleError):
    """Police d'assurance expiree."""

    def __init__(self, policy_id: str, end_date: str):
        super().__init__(
            message=f"La police d'assurance a expire le {end_date}",
            code="INSURANCE_POLICY_EXPIRED",
            details={"policy_id": policy_id, "end_date": end_date}
        )


class AssetAlreadyInsuredError(AssetModuleError):
    """Actif deja assure sur cette police."""

    def __init__(self, asset_id: str, policy_id: str):
        super().__init__(
            message="Cet actif est deja couvert par cette police",
            code="ASSET_ALREADY_INSURED",
            details={"asset_id": asset_id, "policy_id": policy_id}
        )


# ============================================================================
# EXCEPTIONS - TRANSFERT
# ============================================================================

class TransferNotFoundError(AssetModuleError):
    """Transfert non trouve."""

    def __init__(self, transfer_id: str):
        super().__init__(
            message=f"Transfert {transfer_id} non trouve",
            code="TRANSFER_NOT_FOUND",
            details={"transfer_id": transfer_id}
        )


class TransferAlreadyCompletedError(AssetModuleError):
    """Transfert deja effectue."""

    def __init__(self, transfer_id: str):
        super().__init__(
            message="Ce transfert est deja complete",
            code="TRANSFER_ALREADY_COMPLETED",
            details={"transfer_id": transfer_id}
        )


class TransferInvalidDestinationError(AssetModuleError):
    """Destination de transfert invalide."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Destination de transfert invalide: {reason}",
            code="TRANSFER_INVALID_DESTINATION",
            details={"reason": reason}
        )


# ============================================================================
# EXCEPTIONS - VALIDATION
# ============================================================================

class ValidationError(AssetModuleError):
    """Erreur de validation."""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Erreur de validation sur '{field}': {message}",
            code="VALIDATION_ERROR",
            details={"field": field, "error": message}
        )


class DateValidationError(AssetModuleError):
    """Erreur de validation de date."""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Date invalide pour '{field}': {message}",
            code="DATE_VALIDATION_ERROR",
            details={"field": field, "error": message}
        )


class InServiceDateBeforeAcquisitionError(AssetModuleError):
    """Date de mise en service avant acquisition."""

    def __init__(self, acquisition_date: str, in_service_date: str):
        super().__init__(
            message="La date de mise en service ne peut pas etre anterieure a la date d'acquisition",
            code="IN_SERVICE_DATE_BEFORE_ACQUISITION",
            details={"acquisition_date": acquisition_date, "in_service_date": in_service_date}
        )


class DisposalDateBeforeAcquisitionError(AssetModuleError):
    """Date de cession avant acquisition."""

    def __init__(self, acquisition_date: str, disposal_date: str):
        super().__init__(
            message="La date de cession ne peut pas etre anterieure a la date d'acquisition",
            code="DISPOSAL_DATE_BEFORE_ACQUISITION",
            details={"acquisition_date": acquisition_date, "disposal_date": disposal_date}
        )


# ============================================================================
# EXCEPTIONS - CONCURRENCE
# ============================================================================

class OptimisticLockError(AssetModuleError):
    """Erreur de verrouillage optimiste."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            message=f"L'enregistrement a ete modifie par un autre utilisateur. Veuillez rafraichir.",
            code="OPTIMISTIC_LOCK_ERROR",
            details={"entity_type": entity_type, "entity_id": entity_id}
        )


# ============================================================================
# EXCEPTIONS - COMPTABILITE
# ============================================================================

class AccountingIntegrationError(AssetModuleError):
    """Erreur d'integration comptable."""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Erreur d'integration comptable ({operation}): {reason}",
            code="ACCOUNTING_INTEGRATION_ERROR",
            details={"operation": operation, "reason": reason}
        )


class MissingAccountError(AssetModuleError):
    """Compte comptable manquant."""

    def __init__(self, account_type: str, asset_id: str):
        super().__init__(
            message=f"Compte comptable manquant: {account_type}",
            code="MISSING_ACCOUNT",
            details={"account_type": account_type, "asset_id": asset_id}
        )


class PeriodClosedError(AssetModuleError):
    """Periode comptable cloturee."""

    def __init__(self, period: str):
        super().__init__(
            message=f"La periode comptable {period} est cloturee",
            code="PERIOD_CLOSED",
            details={"period": period}
        )
