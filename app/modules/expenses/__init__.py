"""
Module de Gestion des Notes de Frais - GAP-033

Fonctionnalités complètes:
- Saisie mobile des dépenses avec OCR
- Workflow de validation multi-niveaux
- Indemnités kilométriques (barème URSSAF 2024)
- Per diem et forfaits
- Export comptable automatique

Conformité: URSSAF, obligations justificatifs, TVA récupérable
"""

from .service import (
    # Énumérations
    ExpenseCategory,
    ExpenseStatus,
    PaymentMethod,
    VehicleType,
    ApprovalLevel,

    # Data classes
    Receipt,
    MileageTrip,
    ExpenseLine,
    ExpenseReport,
    ExpensePolicy,
    ApprovalRequest,

    # Barèmes
    MILEAGE_RATES_CAR_2024,
    MILEAGE_RATE_BICYCLE,
    MEAL_LIMITS_2024,
    GIFT_LIMITS_2024,

    # Service
    ExpenseService,
    create_expense_service,
)

__all__ = [
    "ExpenseCategory",
    "ExpenseStatus",
    "PaymentMethod",
    "VehicleType",
    "ApprovalLevel",
    "Receipt",
    "MileageTrip",
    "ExpenseLine",
    "ExpenseReport",
    "ExpensePolicy",
    "ApprovalRequest",
    "MILEAGE_RATES_CAR_2024",
    "MILEAGE_RATE_BICYCLE",
    "MEAL_LIMITS_2024",
    "GIFT_LIMITS_2024",
    "ExpenseService",
    "create_expense_service",
]
