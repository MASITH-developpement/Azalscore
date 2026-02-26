"""
AZALS MODULE - Dunning (Relances Impayés)
==========================================

Module de gestion des relances automatiques pour les factures impayées.

Fonctionnalités:
- 6 niveaux de relance configurables (rappel → recouvrement)
- Templates personnalisables (email, SMS, courrier)
- Règles de déclenchement par segment client
- Calcul automatique des pénalités (art. L441-10 Code de commerce)
- Suivi des promesses de paiement
- Campagnes de relance en masse
- Statistiques et aging report

Conformité:
- Indemnité forfaitaire de recouvrement: 40€ (art. L441-10)
- Intérêts de retard: 3x taux directeur BCE
- Respect des jours ouvrés (hors weekends et jours fériés)
"""

from .service import DunningService
from .router import router as dunning_router
from .models import (
    DunningLevel,
    DunningTemplate,
    DunningRule,
    DunningAction,
    DunningCampaign,
    PaymentPromise,
    CustomerDunningProfile,
    DunningLevelType,
    DunningChannel,
    DunningStatus,
    DunningCampaignStatus,
    PaymentPromiseStatus,
)
from .schemas import (
    DunningLevelCreate,
    DunningLevelResponse,
    DunningTemplateCreate,
    DunningTemplateResponse,
    DunningActionCreate,
    DunningActionResponse,
    DunningCampaignCreate,
    DunningCampaignResponse,
    PaymentPromiseCreate,
    PaymentPromiseResponse,
    DunningStatistics,
    OverdueAnalysis,
)

__all__ = [
    # Service & Router
    "DunningService",
    "dunning_router",
    # Models
    "DunningLevel",
    "DunningTemplate",
    "DunningRule",
    "DunningAction",
    "DunningCampaign",
    "PaymentPromise",
    "CustomerDunningProfile",
    # Enums
    "DunningLevelType",
    "DunningChannel",
    "DunningStatus",
    "DunningCampaignStatus",
    "PaymentPromiseStatus",
    # Schemas
    "DunningLevelCreate",
    "DunningLevelResponse",
    "DunningTemplateCreate",
    "DunningTemplateResponse",
    "DunningActionCreate",
    "DunningActionResponse",
    "DunningCampaignCreate",
    "DunningCampaignResponse",
    "PaymentPromiseCreate",
    "PaymentPromiseResponse",
    "DunningStatistics",
    "OverdueAnalysis",
]
