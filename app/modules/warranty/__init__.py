"""
Module de Gestion des Garanties Produits - GAP-039

Gestion complète:
- Garantie légale de conformité (2 ans)
- Garanties commerciales
- Extensions de garantie
- Demandes SAV et réparations
- Remplacements et remboursements
- Provisions comptables

Conformité: Code de la consommation L217-3 à L217-14, Directive 2019/771
"""

from .service import (
    # Énumérations
    WarrantyType,
    WarrantyStatus,
    ClaimStatus,
    ClaimResolution,
    DefectType,

    # Data classes
    Product,
    Customer,
    WarrantyTerms,
    Warranty,
    ClaimDocument,
    RepairDetail,
    WarrantyClaim,
    WarrantyExtension,
    WarrantyProvision,

    # Constantes
    LEGAL_WARRANTY_DURATION_MONTHS,
    HIDDEN_DEFECTS_DURATION_YEARS,
    REPAIR_MAX_DAYS,
    WARRANTY_EXCLUSIONS,

    # Service
    WarrantyService,
    create_warranty_service,
)

__all__ = [
    "WarrantyType",
    "WarrantyStatus",
    "ClaimStatus",
    "ClaimResolution",
    "DefectType",
    "Product",
    "Customer",
    "WarrantyTerms",
    "Warranty",
    "ClaimDocument",
    "RepairDetail",
    "WarrantyClaim",
    "WarrantyExtension",
    "WarrantyProvision",
    "LEGAL_WARRANTY_DURATION_MONTHS",
    "HIDDEN_DEFECTS_DURATION_YEARS",
    "REPAIR_MAX_DAYS",
    "WARRANTY_EXCLUSIONS",
    "WarrantyService",
    "create_warranty_service",
]
