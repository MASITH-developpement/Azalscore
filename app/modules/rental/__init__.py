"""
Module Rental / Location - GAP-063

Gestion de la location:
- Catalogue articles locatifs
- Disponibilités et planning
- Contrats de location
- Tarification dynamique
- Dépôts de garantie
- États des lieux
- Facturation récurrente
"""

from .service import (
    # Énumérations
    RentalItemType,
    RentalItemStatus,
    ContractStatus,
    PricingType,
    InspectionType,
    InspectionCondition,
    DepositStatus,

    # Data classes
    PricingRule,
    RentalItem,
    RentalContract,
    ContractLine,
    Inspection,
    Reservation,
    Extension,
    AvailabilitySlot,
    RentalStats,

    # Service
    RentalService,
    create_rental_service,
)

__all__ = [
    "RentalItemType",
    "RentalItemStatus",
    "ContractStatus",
    "PricingType",
    "InspectionType",
    "InspectionCondition",
    "DepositStatus",
    "PricingRule",
    "RentalItem",
    "RentalContract",
    "ContractLine",
    "Inspection",
    "Reservation",
    "Extension",
    "AvailabilitySlot",
    "RentalStats",
    "RentalService",
    "create_rental_service",
]
