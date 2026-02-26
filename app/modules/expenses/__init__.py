"""
Module de Gestion des Notes de Frais - GAP-084

Fonctionnalités complètes:
- Saisie mobile des dépenses avec OCR
- Workflow de validation multi-niveaux
- Indemnités kilométriques (barème URSSAF 2024)
- Per diem et forfaits
- Export comptable automatique

Conformité: URSSAF, obligations justificatifs, TVA récupérable
"""

from .service import (
    # Énumérations (service)
    ApprovalLevel,

    # Data classes
    Receipt,
    MileageTrip,
    ExpenseLine as ExpenseLineData,
    ExpenseReport as ExpenseReportData,
    ExpensePolicy as ExpensePolicyData,
    ApprovalRequest as ApprovalRequestData,

    # Barèmes
    MILEAGE_RATES_CAR_2024,
    MILEAGE_RATE_BICYCLE,
    MEAL_LIMITS_2024,
    GIFT_LIMITS_2024,

    # Service
    ExpenseService,
    create_expense_service,
)

# Models SQLAlchemy
from .models import (
    ExpenseReport,
    ExpenseLine,
    ExpensePolicy,
    MileageRate,
    EmployeeVehicle,
    ExpenseStatus,
    ExpenseCategory,
    PaymentMethod,
    VehicleType,
)

# Repositories
from .repository import (
    ExpenseReportRepository,
    ExpensePolicyRepository,
    MileageRateRepository,
    EmployeeVehicleRepository,
)

# Exceptions
from .exceptions import (
    ExpenseError,
    ExpenseReportNotFoundError,
    ExpenseReportDuplicateError,
    ExpenseReportValidationError,
    ExpenseReportStateError,
    ExpenseReportAlreadySubmittedError,
    ExpenseReportNotEditableError,
    ExpenseLineNotFoundError,
    ExpenseLineValidationError,
    PolicyNotFoundError,
    PolicyDuplicateError,
    PolicyViolationError,
    ReceiptRequiredError,
    MileageCalculationError,
    ApprovalNotAuthorizedError,
    ExportError,
)

# Router
from .router import router

__all__ = [
    # Enums
    "ExpenseCategory",
    "ExpenseStatus",
    "PaymentMethod",
    "VehicleType",
    "ApprovalLevel",
    # Models SQLAlchemy
    "ExpenseReport",
    "ExpenseLine",
    "ExpensePolicy",
    "MileageRate",
    "EmployeeVehicle",
    # Repositories
    "ExpenseReportRepository",
    "ExpensePolicyRepository",
    "MileageRateRepository",
    "EmployeeVehicleRepository",
    # Data classes (service)
    "Receipt",
    "MileageTrip",
    "ExpenseLineData",
    "ExpenseReportData",
    "ExpensePolicyData",
    "ApprovalRequestData",
    # Barèmes
    "MILEAGE_RATES_CAR_2024",
    "MILEAGE_RATE_BICYCLE",
    "MEAL_LIMITS_2024",
    "GIFT_LIMITS_2024",
    # Service
    "ExpenseService",
    "create_expense_service",
    # Exceptions
    "ExpenseError",
    "ExpenseReportNotFoundError",
    "ExpenseReportDuplicateError",
    "ExpenseReportValidationError",
    "ExpenseReportStateError",
    "ExpenseReportAlreadySubmittedError",
    "ExpenseReportNotEditableError",
    "ExpenseLineNotFoundError",
    "ExpenseLineValidationError",
    "PolicyNotFoundError",
    "PolicyDuplicateError",
    "PolicyViolationError",
    "ReceiptRequiredError",
    "MileageCalculationError",
    "ApprovalNotAuthorizedError",
    "ExportError",
    # Router
    "router",
]
