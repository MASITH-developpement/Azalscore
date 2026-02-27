"""
AZALS MODULE INVENTORY - Exceptions
====================================

Exceptions metier specifiques au module de gestion des stocks.
"""

from typing import Optional, List
from uuid import UUID
from decimal import Decimal


class InventoryError(Exception):
    """Exception de base du module Inventory."""

    def __init__(self, message: str, tenant_id: Optional[UUID] = None):
        self.message = message
        self.tenant_id = tenant_id
        super().__init__(self.message)


# ============================================================================
# PRODUCT ERRORS
# ============================================================================

class ProductNotFoundError(InventoryError):
    """Produit non trouve."""

    def __init__(self, product_id: Optional[str] = None, sku: Optional[str] = None):
        self.product_id = product_id
        self.sku = sku
        identifier = sku or product_id
        super().__init__(f"Produit {identifier} non trouve")


class ProductDuplicateError(InventoryError):
    """SKU ou code produit deja existant."""

    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Un produit avec {field}={value} existe deja")


class ProductInactiveError(InventoryError):
    """Operation sur un produit inactif."""

    def __init__(self, product_id: str, status: str):
        self.product_id = product_id
        self.status = status
        super().__init__(f"Le produit {product_id} est inactif (statut: {status})")


# ============================================================================
# STOCK ERRORS
# ============================================================================

class InsufficientStockError(InventoryError):
    """Stock insuffisant pour l'operation."""

    def __init__(
        self,
        product_id: str,
        location_id: str,
        requested: Decimal,
        available: Decimal
    ):
        self.product_id = product_id
        self.location_id = location_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Stock insuffisant pour le produit {product_id}: "
            f"demande={requested}, disponible={available}"
        )


class NegativeStockError(InventoryError):
    """Le stock ne peut pas etre negatif."""

    def __init__(self, product_id: str, location_id: str, resulting_qty: Decimal):
        self.product_id = product_id
        self.location_id = location_id
        self.resulting_qty = resulting_qty
        super().__init__(
            f"Operation impossible: stock resultant negatif ({resulting_qty}) "
            f"pour le produit {product_id}"
        )


class StockLevelNotFoundError(InventoryError):
    """Niveau de stock non trouve."""

    def __init__(self, product_id: str, location_id: str):
        self.product_id = product_id
        self.location_id = location_id
        super().__init__(
            f"Niveau de stock non trouve pour le produit {product_id} "
            f"a l'emplacement {location_id}"
        )


# ============================================================================
# WAREHOUSE/LOCATION ERRORS
# ============================================================================

class WarehouseNotFoundError(InventoryError):
    """Entrepot non trouve."""

    def __init__(self, warehouse_id: Optional[str] = None, code: Optional[str] = None):
        self.warehouse_id = warehouse_id
        self.code = code
        identifier = code or warehouse_id
        super().__init__(f"Entrepot {identifier} non trouve")


class LocationNotFoundError(InventoryError):
    """Emplacement non trouve."""

    def __init__(self, location_id: Optional[str] = None, code: Optional[str] = None):
        self.location_id = location_id
        self.code = code
        identifier = code or location_id
        super().__init__(f"Emplacement {identifier} non trouve")


class LocationInactiveError(InventoryError):
    """Emplacement inactif."""

    def __init__(self, location_id: str):
        self.location_id = location_id
        super().__init__(f"L'emplacement {location_id} est inactif")


class LocationCapacityExceededError(InventoryError):
    """Capacite de l'emplacement depassee."""

    def __init__(self, location_id: str, current: Decimal, max_capacity: Decimal):
        self.location_id = location_id
        self.current = current
        self.max_capacity = max_capacity
        super().__init__(
            f"Capacite depassee pour l'emplacement {location_id}: "
            f"{current}/{max_capacity}"
        )


# ============================================================================
# MOVEMENT ERRORS
# ============================================================================

class MovementNotFoundError(InventoryError):
    """Mouvement de stock non trouve."""

    def __init__(self, movement_id: Optional[str] = None):
        self.movement_id = movement_id
        super().__init__(f"Mouvement {movement_id} non trouve")


class MovementValidationError(InventoryError):
    """Erreur de validation du mouvement."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


class MovementAlreadyValidatedError(InventoryError):
    """Mouvement deja valide."""

    def __init__(self, movement_id: str):
        self.movement_id = movement_id
        super().__init__(f"Le mouvement {movement_id} est deja valide")


class MovementCancelledError(InventoryError):
    """Mouvement annule, operation impossible."""

    def __init__(self, movement_id: str):
        self.movement_id = movement_id
        super().__init__(f"Le mouvement {movement_id} est annule")


# ============================================================================
# LOT/SERIAL ERRORS
# ============================================================================

class LotNotFoundError(InventoryError):
    """Lot non trouve."""

    def __init__(self, lot_id: Optional[str] = None, lot_number: Optional[str] = None):
        self.lot_id = lot_id
        self.lot_number = lot_number
        identifier = lot_number or lot_id
        super().__init__(f"Lot {identifier} non trouve")


class LotExpiredError(InventoryError):
    """Lot expire."""

    def __init__(self, lot_number: str, expiry_date: str):
        self.lot_number = lot_number
        self.expiry_date = expiry_date
        super().__init__(f"Le lot {lot_number} a expire le {expiry_date}")


class SerialNumberNotFoundError(InventoryError):
    """Numero de serie non trouve."""

    def __init__(self, serial_number: str):
        self.serial_number = serial_number
        super().__init__(f"Numero de serie {serial_number} non trouve")


class SerialNumberDuplicateError(InventoryError):
    """Numero de serie deja utilise."""

    def __init__(self, serial_number: str, product_id: str):
        self.serial_number = serial_number
        self.product_id = product_id
        super().__init__(
            f"Le numero de serie {serial_number} existe deja "
            f"pour le produit {product_id}"
        )


class SerialNumberUsedError(InventoryError):
    """Numero de serie deja sorti du stock."""

    def __init__(self, serial_number: str):
        self.serial_number = serial_number
        super().__init__(f"Le numero de serie {serial_number} est deja sorti du stock")


# ============================================================================
# PICKING ERRORS
# ============================================================================

class PickingNotFoundError(InventoryError):
    """Picking non trouve."""

    def __init__(self, picking_id: Optional[str] = None):
        self.picking_id = picking_id
        super().__init__(f"Picking {picking_id} non trouve")


class PickingStateError(InventoryError):
    """Transition d'etat invalide pour le picking."""

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition impossible de {current_status} vers {target_status}"
        )


class PickingIncompleteError(InventoryError):
    """Picking incomplet."""

    def __init__(self, picking_id: str, missing_lines: int):
        self.picking_id = picking_id
        self.missing_lines = missing_lines
        super().__init__(
            f"Le picking {picking_id} est incomplet: {missing_lines} lignes manquantes"
        )


# ============================================================================
# INVENTORY COUNT ERRORS
# ============================================================================

class InventoryCountNotFoundError(InventoryError):
    """Inventaire non trouve."""

    def __init__(self, count_id: Optional[str] = None):
        self.count_id = count_id
        super().__init__(f"Inventaire {count_id} non trouve")


class InventoryCountInProgressError(InventoryError):
    """Un inventaire est deja en cours pour cet emplacement."""

    def __init__(self, location_id: str):
        self.location_id = location_id
        super().__init__(
            f"Un inventaire est deja en cours pour l'emplacement {location_id}"
        )


class InventoryCountValidationError(InventoryError):
    """Erreur de validation de l'inventaire."""

    def __init__(self, message: str, discrepancies: Optional[List[dict]] = None):
        self.discrepancies = discrepancies or []
        super().__init__(message)


# ============================================================================
# CACHE ERRORS
# ============================================================================

class InventoryCacheError(InventoryError):
    """Erreur de cache non critique."""
    pass
