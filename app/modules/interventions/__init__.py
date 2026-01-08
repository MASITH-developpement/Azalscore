"""
AZALS MODULE INTERVENTIONS v1
==============================

Module de gestion des interventions terrain.

Fonctionnalités:
- Numérotation officielle INT-YYYY-XXXX
- Gestion du donneur d'ordre
- Temps automatique par actions terrain
- Planification (consommation du module Planning)
- Rapports d'intervention
- Rapport final consolidé
- RBAC + multi-tenant
"""

from .models import (
    Intervention,
    InterventionStatut,
    InterventionPriorite,
    RapportIntervention,
    RapportFinal,
    DonneurOrdre,
    InterventionSequence,
)
from .schemas import (
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
    ArriveeRequest,
    DemarrageRequest,
    FinInterventionRequest,
    RapportInterventionResponse,
    RapportFinalResponse,
)
from .service import InterventionsService
from .router import router

__all__ = [
    # Models
    "Intervention",
    "InterventionStatut",
    "InterventionPriorite",
    "RapportIntervention",
    "RapportFinal",
    "DonneurOrdre",
    "InterventionSequence",
    # Schemas
    "InterventionCreate",
    "InterventionUpdate",
    "InterventionResponse",
    "ArriveeRequest",
    "DemarrageRequest",
    "FinInterventionRequest",
    "RapportInterventionResponse",
    "RapportFinalResponse",
    # Service
    "InterventionsService",
    # Router
    "router",
]
