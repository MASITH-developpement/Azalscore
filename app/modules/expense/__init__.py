"""
Module Expense Management / Notes de frais - GAP-084

Gestion des notes de frais:
- Saisie des dépenses
- Justificatifs et OCR
- Politiques de dépenses
- Workflow d'approbation
- Remboursements
- Cartes corporate
- Rapports et analytics
"""

from .service import (
    # Énumérations
    ExpenseCategory,
    ExpenseStatus,
    ReportStatus,
    PaymentMethod,
    MileageType,
    CardStatus,

    # Data classes
    ExpensePolicy,
    Receipt,
    Expense,
    ExpenseReport,
    CorporateCard,
    CardTransaction,
    ExpenseStats,

    # Service
    ExpenseService,
    create_expense_service,
)

__all__ = [
    "ExpenseCategory",
    "ExpenseStatus",
    "ReportStatus",
    "PaymentMethod",
    "MileageType",
    "CardStatus",
    "ExpensePolicy",
    "Receipt",
    "Expense",
    "ExpenseReport",
    "CorporateCard",
    "CardTransaction",
    "ExpenseStats",
    "ExpenseService",
    "create_expense_service",
]
