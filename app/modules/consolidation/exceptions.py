"""
AZALS MODULE - CONSOLIDATION: Exceptions
==========================================

Exceptions metier specifiques au module de consolidation
comptable multi-entites.

Auteur: AZALSCORE Team
Version: 1.0.0
"""


class ConsolidationError(Exception):
    """Exception de base du module Consolidation."""

    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or "CONSOLIDATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# EXCEPTIONS PERIMETRE
# ============================================================================

class PerimeterNotFoundError(ConsolidationError):
    """Perimetre de consolidation non trouve."""

    def __init__(self, perimeter_id: str = None, code: str = None):
        message = f"Perimetre de consolidation non trouve"
        if perimeter_id:
            message += f": {perimeter_id}"
        if code:
            message += f" (code: {code})"
        super().__init__(message, "PERIMETER_NOT_FOUND", {"perimeter_id": perimeter_id, "code": code})


class PerimeterDuplicateError(ConsolidationError):
    """Code de perimetre deja existant."""

    def __init__(self, code: str, fiscal_year: int):
        message = f"Un perimetre avec le code '{code}' existe deja pour l'annee {fiscal_year}"
        super().__init__(message, "PERIMETER_DUPLICATE", {"code": code, "fiscal_year": fiscal_year})


class PerimeterClosedError(ConsolidationError):
    """Operation interdite sur un perimetre cloture."""

    def __init__(self, perimeter_id: str):
        message = f"Le perimetre {perimeter_id} est cloture et ne peut etre modifie"
        super().__init__(message, "PERIMETER_CLOSED", {"perimeter_id": perimeter_id})


# ============================================================================
# EXCEPTIONS ENTITE
# ============================================================================

class EntityNotFoundError(ConsolidationError):
    """Entite de consolidation non trouvee."""

    def __init__(self, entity_id: str = None, code: str = None):
        message = f"Entite non trouvee"
        if entity_id:
            message += f": {entity_id}"
        if code:
            message += f" (code: {code})"
        super().__init__(message, "ENTITY_NOT_FOUND", {"entity_id": entity_id, "code": code})


class EntityDuplicateError(ConsolidationError):
    """Code d'entite deja existant dans le perimetre."""

    def __init__(self, code: str, perimeter_id: str):
        message = f"Une entite avec le code '{code}' existe deja dans ce perimetre"
        super().__init__(message, "ENTITY_DUPLICATE", {"code": code, "perimeter_id": perimeter_id})


class EntityCircularReferenceError(ConsolidationError):
    """Reference circulaire dans la hierarchie des entites."""

    def __init__(self, entity_id: str, parent_id: str):
        message = f"Reference circulaire detectee: {entity_id} ne peut pas etre filiale de {parent_id}"
        super().__init__(message, "ENTITY_CIRCULAR_REFERENCE", {"entity_id": entity_id, "parent_id": parent_id})


class EntityOwnershipError(ConsolidationError):
    """Erreur de pourcentage de detention."""

    def __init__(self, message: str, entity_id: str = None):
        super().__init__(message, "ENTITY_OWNERSHIP_ERROR", {"entity_id": entity_id})


class ParentEntityRequiredError(ConsolidationError):
    """Un perimetre doit avoir une societe mere."""

    def __init__(self, perimeter_id: str):
        message = f"Le perimetre {perimeter_id} doit avoir exactement une societe mere (is_parent=True)"
        super().__init__(message, "PARENT_ENTITY_REQUIRED", {"perimeter_id": perimeter_id})


# ============================================================================
# EXCEPTIONS PARTICIPATION
# ============================================================================

class ParticipationNotFoundError(ConsolidationError):
    """Participation non trouvee."""

    def __init__(self, participation_id: str = None):
        message = f"Participation non trouvee"
        if participation_id:
            message += f": {participation_id}"
        super().__init__(message, "PARTICIPATION_NOT_FOUND", {"participation_id": participation_id})


class ParticipationDuplicateError(ConsolidationError):
    """Lien de participation deja existant."""

    def __init__(self, parent_id: str, subsidiary_id: str):
        message = f"Un lien de participation existe deja entre {parent_id} et {subsidiary_id}"
        super().__init__(message, "PARTICIPATION_DUPLICATE", {"parent_id": parent_id, "subsidiary_id": subsidiary_id})


class InvalidParticipationError(ConsolidationError):
    """Participation invalide."""

    def __init__(self, message: str, parent_id: str = None, subsidiary_id: str = None):
        super().__init__(message, "INVALID_PARTICIPATION", {"parent_id": parent_id, "subsidiary_id": subsidiary_id})


# ============================================================================
# EXCEPTIONS CONSOLIDATION
# ============================================================================

class ConsolidationNotFoundError(ConsolidationError):
    """Consolidation non trouvee."""

    def __init__(self, consolidation_id: str = None, code: str = None):
        message = f"Consolidation non trouvee"
        if consolidation_id:
            message += f": {consolidation_id}"
        if code:
            message += f" (code: {code})"
        super().__init__(message, "CONSOLIDATION_NOT_FOUND", {"consolidation_id": consolidation_id, "code": code})


class ConsolidationDuplicateError(ConsolidationError):
    """Code de consolidation deja existant."""

    def __init__(self, code: str):
        message = f"Une consolidation avec le code '{code}' existe deja"
        super().__init__(message, "CONSOLIDATION_DUPLICATE", {"code": code})


class ConsolidationStatusError(ConsolidationError):
    """Operation interdite pour le statut actuel de la consolidation."""

    def __init__(self, current_status: str, required_status: str = None, action: str = None):
        message = f"Operation impossible: la consolidation est en statut '{current_status}'"
        if required_status:
            message += f", statut requis: '{required_status}'"
        if action:
            message += f" pour l'action '{action}'"
        super().__init__(message, "CONSOLIDATION_STATUS_ERROR", {
            "current_status": current_status,
            "required_status": required_status,
            "action": action
        })


class ConsolidationValidationError(ConsolidationError):
    """Erreur de validation de la consolidation."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message, "CONSOLIDATION_VALIDATION_ERROR", {"errors": errors or []})


class ConsolidationIncompleteError(ConsolidationError):
    """La consolidation n'est pas complete."""

    def __init__(self, message: str, missing_items: list = None):
        super().__init__(message, "CONSOLIDATION_INCOMPLETE", {"missing_items": missing_items or []})


# ============================================================================
# EXCEPTIONS PAQUET
# ============================================================================

class PackageNotFoundError(ConsolidationError):
    """Paquet de consolidation non trouve."""

    def __init__(self, package_id: str = None, entity_id: str = None):
        message = f"Paquet de consolidation non trouve"
        if package_id:
            message += f": {package_id}"
        if entity_id:
            message += f" (entite: {entity_id})"
        super().__init__(message, "PACKAGE_NOT_FOUND", {"package_id": package_id, "entity_id": entity_id})


class PackageDuplicateError(ConsolidationError):
    """Paquet deja existant pour cette entite et cette consolidation."""

    def __init__(self, consolidation_id: str, entity_id: str):
        message = f"Un paquet existe deja pour l'entite {entity_id} dans la consolidation {consolidation_id}"
        super().__init__(message, "PACKAGE_DUPLICATE", {"consolidation_id": consolidation_id, "entity_id": entity_id})


class PackageStatusError(ConsolidationError):
    """Operation interdite pour le statut actuel du paquet."""

    def __init__(self, current_status: str, action: str = None):
        message = f"Operation impossible: le paquet est en statut '{current_status}'"
        if action:
            message += f" pour l'action '{action}'"
        super().__init__(message, "PACKAGE_STATUS_ERROR", {"current_status": current_status, "action": action})


class PackageValidationError(ConsolidationError):
    """Erreur de validation du paquet."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message, "PACKAGE_VALIDATION_ERROR", {"errors": errors or []})


class PackageBalanceError(ConsolidationError):
    """La balance du paquet n'est pas equilibree."""

    def __init__(self, entity_id: str, difference: str):
        message = f"La balance de l'entite {entity_id} n'est pas equilibree (ecart: {difference})"
        super().__init__(message, "PACKAGE_BALANCE_ERROR", {"entity_id": entity_id, "difference": difference})


# ============================================================================
# EXCEPTIONS ELIMINATIONS
# ============================================================================

class EliminationNotFoundError(ConsolidationError):
    """Elimination non trouvee."""

    def __init__(self, elimination_id: str = None):
        message = f"Elimination non trouvee"
        if elimination_id:
            message += f": {elimination_id}"
        super().__init__(message, "ELIMINATION_NOT_FOUND", {"elimination_id": elimination_id})


class EliminationValidationError(ConsolidationError):
    """Erreur de validation de l'elimination."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message, "ELIMINATION_VALIDATION_ERROR", {"errors": errors or []})


class EliminationImbalanceError(ConsolidationError):
    """L'ecriture d'elimination n'est pas equilibree."""

    def __init__(self, debit_total: str, credit_total: str):
        message = f"L'ecriture d'elimination n'est pas equilibree (debit: {debit_total}, credit: {credit_total})"
        super().__init__(message, "ELIMINATION_IMBALANCE", {"debit_total": debit_total, "credit_total": credit_total})


# ============================================================================
# EXCEPTIONS RETRAITEMENTS
# ============================================================================

class RestatementNotFoundError(ConsolidationError):
    """Retraitement non trouve."""

    def __init__(self, restatement_id: str = None):
        message = f"Retraitement non trouve"
        if restatement_id:
            message += f": {restatement_id}"
        super().__init__(message, "RESTATEMENT_NOT_FOUND", {"restatement_id": restatement_id})


class RestatementValidationError(ConsolidationError):
    """Erreur de validation du retraitement."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message, "RESTATEMENT_VALIDATION_ERROR", {"errors": errors or []})


# ============================================================================
# EXCEPTIONS RECONCILIATION
# ============================================================================

class ReconciliationNotFoundError(ConsolidationError):
    """Reconciliation non trouvee."""

    def __init__(self, reconciliation_id: str = None):
        message = f"Reconciliation non trouvee"
        if reconciliation_id:
            message += f": {reconciliation_id}"
        super().__init__(message, "RECONCILIATION_NOT_FOUND", {"reconciliation_id": reconciliation_id})


class ReconciliationMismatchError(ConsolidationError):
    """Ecart de reconciliation hors tolerance."""

    def __init__(self, entity1_id: str, entity2_id: str, difference: str, tolerance: str):
        message = (
            f"Ecart de reconciliation entre {entity1_id} et {entity2_id}: "
            f"{difference} (tolerance: {tolerance})"
        )
        super().__init__(message, "RECONCILIATION_MISMATCH", {
            "entity1_id": entity1_id,
            "entity2_id": entity2_id,
            "difference": difference,
            "tolerance": tolerance
        })


# ============================================================================
# EXCEPTIONS COURS DE CHANGE
# ============================================================================

class ExchangeRateNotFoundError(ConsolidationError):
    """Cours de change non trouve."""

    def __init__(self, from_currency: str, to_currency: str, date: str):
        message = f"Cours de change non trouve: {from_currency}/{to_currency} au {date}"
        super().__init__(message, "EXCHANGE_RATE_NOT_FOUND", {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "date": date
        })


class ExchangeRateDuplicateError(ConsolidationError):
    """Cours de change deja existant."""

    def __init__(self, from_currency: str, to_currency: str, date: str):
        message = f"Un cours de change existe deja pour {from_currency}/{to_currency} au {date}"
        super().__init__(message, "EXCHANGE_RATE_DUPLICATE", {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "date": date
        })


# ============================================================================
# EXCEPTIONS GOODWILL
# ============================================================================

class GoodwillCalculationError(ConsolidationError):
    """Erreur de calcul du goodwill."""

    def __init__(self, message: str, participation_id: str = None):
        super().__init__(message, "GOODWILL_CALCULATION_ERROR", {"participation_id": participation_id})


class GoodwillNotFoundError(ConsolidationError):
    """Calcul de goodwill non trouve."""

    def __init__(self, goodwill_id: str = None):
        message = f"Calcul de goodwill non trouve"
        if goodwill_id:
            message += f": {goodwill_id}"
        super().__init__(message, "GOODWILL_NOT_FOUND", {"goodwill_id": goodwill_id})


# ============================================================================
# EXCEPTIONS RAPPORTS
# ============================================================================

class ReportNotFoundError(ConsolidationError):
    """Rapport non trouve."""

    def __init__(self, report_id: str = None):
        message = f"Rapport non trouve"
        if report_id:
            message += f": {report_id}"
        super().__init__(message, "REPORT_NOT_FOUND", {"report_id": report_id})


class ReportGenerationError(ConsolidationError):
    """Erreur lors de la generation du rapport."""

    def __init__(self, message: str, report_type: str = None):
        super().__init__(message, "REPORT_GENERATION_ERROR", {"report_type": report_type})


# ============================================================================
# EXCEPTIONS MAPPING
# ============================================================================

class AccountMappingNotFoundError(ConsolidationError):
    """Mapping de compte non trouve."""

    def __init__(self, local_account: str = None, entity_id: str = None):
        message = f"Mapping de compte non trouve"
        if local_account:
            message += f" pour le compte {local_account}"
        if entity_id:
            message += f" (entite: {entity_id})"
        super().__init__(message, "ACCOUNT_MAPPING_NOT_FOUND", {
            "local_account": local_account,
            "entity_id": entity_id
        })


class AccountMappingDuplicateError(ConsolidationError):
    """Mapping de compte deja existant."""

    def __init__(self, local_account: str, perimeter_id: str, entity_id: str = None):
        message = f"Un mapping existe deja pour le compte {local_account}"
        super().__init__(message, "ACCOUNT_MAPPING_DUPLICATE", {
            "local_account": local_account,
            "perimeter_id": perimeter_id,
            "entity_id": entity_id
        })


# ============================================================================
# EXCEPTIONS CONVERSION DEVISE
# ============================================================================

class CurrencyConversionError(ConsolidationError):
    """Erreur lors de la conversion de devise."""

    def __init__(self, message: str, from_currency: str = None, to_currency: str = None):
        super().__init__(message, "CURRENCY_CONVERSION_ERROR", {
            "from_currency": from_currency,
            "to_currency": to_currency
        })


class MissingExchangeRatesError(ConsolidationError):
    """Cours de change manquants pour la consolidation."""

    def __init__(self, missing_rates: list):
        message = f"Cours de change manquants: {', '.join(missing_rates)}"
        super().__init__(message, "MISSING_EXCHANGE_RATES", {"missing_rates": missing_rates})


# ============================================================================
# EXCEPTIONS SECURITE
# ============================================================================

class ConsolidationAccessDeniedError(ConsolidationError):
    """Acces refuse a la ressource de consolidation."""

    def __init__(self, resource_type: str, resource_id: str = None, action: str = None):
        message = f"Acces refuse a la ressource {resource_type}"
        if resource_id:
            message += f" ({resource_id})"
        if action:
            message += f" pour l'action '{action}'"
        super().__init__(message, "ACCESS_DENIED", {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action
        })


class TenantIsolationError(ConsolidationError):
    """Violation de l'isolation multi-tenant."""

    def __init__(self, message: str = None):
        default_message = "Tentative d'acces a des donnees d'un autre tenant"
        super().__init__(message or default_message, "TENANT_ISOLATION_VIOLATION")
