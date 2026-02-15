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
    DonneurOrdre,
    Intervention,
    InterventionPriorite,
    InterventionSequence,
    InterventionStatut,
    RapportFinal,
    RapportIntervention,
)
from .router_crud import router
from .schemas import (
    ArriveeRequest,
    DemarrageRequest,
    FinInterventionRequest,
    InterventionCreate,
    InterventionResponse,
    InterventionUpdate,
    RapportFinalResponse,
    RapportInterventionResponse,
)
from .service import InterventionsService

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
