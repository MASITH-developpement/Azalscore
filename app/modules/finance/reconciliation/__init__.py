"""
AZALSCORE Finance Reconciliation AI
====================================

Module de rapprochement bancaire intelligent avec IA.

Fonctionnalités:
- Matching automatique transactions ↔ écritures comptables
- Scoring de confiance basé sur règles et ML
- Apprentissage des patterns utilisateur
- Catégorisation automatique des opérations non matchées
- Suggestions intelligentes

Usage:
    from app.modules.finance.reconciliation import ReconciliationService

    service = ReconciliationService(db, tenant_id)
    suggestions = await service.get_match_suggestions(
        bank_account_id=account_id,
        limit=50,
    )
"""

from .service import ReconciliationService, MatchSuggestion, ReconciliationResult
from .router import router as reconciliation_router

__all__ = [
    "ReconciliationService",
    "MatchSuggestion",
    "ReconciliationResult",
    "reconciliation_router",
]
