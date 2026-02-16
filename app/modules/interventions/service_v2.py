"""
AZALS - Interventions Service (v2 - CRUDRouter Compatible)
===============================================================

Service compatible avec BaseService et CRUDRouter.
Migration automatique depuis service.py.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

from app.modules.interventions.models import (
    InterventionSequence,
    DonneurOrdre,
    Intervention,
    RapportIntervention,
    RapportFinal,
)
from app.modules.interventions.schemas import (
    DonneurOrdreBase,
    DonneurOrdreCreate,
    DonneurOrdreResponse,
    DonneurOrdreUpdate,
    InterventionBase,
    InterventionCreate,
    InterventionListResponse,
    InterventionResponse,
    InterventionUpdate,
    RapportFinalResponse,
    RapportInterventionBase,
    RapportInterventionResponse,
    RapportInterventionUpdate,
)

logger = logging.getLogger(__name__)



class InterventionSequenceService(BaseService[InterventionSequence, Any, Any]):
    """Service CRUD pour interventionsequence."""

    model = InterventionSequence

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[InterventionSequence]
    # - get_or_fail(id) -> Result[InterventionSequence]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[InterventionSequence]
    # - update(id, data) -> Result[InterventionSequence]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class DonneurOrdreService(BaseService[DonneurOrdre, Any, Any]):
    """Service CRUD pour donneurordre."""

    model = DonneurOrdre

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[DonneurOrdre]
    # - get_or_fail(id) -> Result[DonneurOrdre]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[DonneurOrdre]
    # - update(id, data) -> Result[DonneurOrdre]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class InterventionService(BaseService[Intervention, Any, Any]):
    """Service CRUD pour intervention."""

    model = Intervention

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Intervention]
    # - get_or_fail(id) -> Result[Intervention]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Intervention]
    # - update(id, data) -> Result[Intervention]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class RapportInterventionService(BaseService[RapportIntervention, Any, Any]):
    """Service CRUD pour rapportintervention."""

    model = RapportIntervention

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[RapportIntervention]
    # - get_or_fail(id) -> Result[RapportIntervention]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[RapportIntervention]
    # - update(id, data) -> Result[RapportIntervention]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class RapportFinalService(BaseService[RapportFinal, Any, Any]):
    """Service CRUD pour rapportfinal."""

    model = RapportFinal

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[RapportFinal]
    # - get_or_fail(id) -> Result[RapportFinal]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[RapportFinal]
    # - update(id, data) -> Result[RapportFinal]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

