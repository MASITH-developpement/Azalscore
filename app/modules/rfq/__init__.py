"""
Module de Gestion des Appels d'Offres (RFQ/RFP) - GAP-037

Gestion complète:
- AO entrants (réponse aux marchés)
- AO sortants (consultation fournisseurs)
- Workflow de validation interne
- Scoring et comparaison des offres
- Conformité marchés publics

Conformité: Code de la commande publique, DUME
"""

from .service import (
    # Énumérations
    TenderType,
    TenderStatus,
    BidStatus,
    CriterionType,
    DocumentCategory,

    # Data classes
    TenderDocument,
    EvaluationCriterion,
    Lot,
    Tender,
    BidDocument,
    BidLineItem,
    BidScore,
    Bid,
    Question,
    TenderAlert,

    # Service
    TenderService,
    create_tender_service,
)

__all__ = [
    "TenderType",
    "TenderStatus",
    "BidStatus",
    "CriterionType",
    "DocumentCategory",
    "TenderDocument",
    "EvaluationCriterion",
    "Lot",
    "Tender",
    "BidDocument",
    "BidLineItem",
    "BidScore",
    "Bid",
    "Question",
    "TenderAlert",
    "TenderService",
    "create_tender_service",
]
