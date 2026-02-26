"""
AZALSCORE Finance Auto Categorization
======================================

Service de catégorisation automatique des opérations bancaires.

Fonctionnalités:
- Catégorisation par règles et patterns
- Apprentissage des préférences utilisateur
- Suggestions de comptes comptables
- Matching fournisseurs/clients

Usage:
    from app.modules.finance.auto_categorization import CategorizationService

    service = CategorizationService(db, tenant_id)
    result = await service.categorize_transaction(transaction)
"""

from .service import (
    CategorizationService,
    CategorizationResult,
    CategorySuggestion,
    CategorizationRule,
    RuleType,
    MatchConfidence,
)
from .router import router as auto_categorization_router

__all__ = [
    "CategorizationService",
    "CategorizationResult",
    "CategorySuggestion",
    "CategorizationRule",
    "RuleType",
    "MatchConfidence",
    "auto_categorization_router",
]
