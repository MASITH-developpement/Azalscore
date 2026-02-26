"""
AZALS - Enrichment Service (v2 - CRUDRouter Compatible)
============================================================

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

from app.modules.enrichment.models import (
    EnrichmentHistory,
    EnrichmentRateLimit,
    EnrichmentProviderConfig,
)
from app.modules.enrichment.schemas import (
    EnrichmentAcceptResponse,
    EnrichmentHistoryResponse,
    EnrichmentLookupResponse,
    EnrichmentStatsResponse,
    ProviderConfigResponse,
    ProviderInfoResponse,
    ProvidersListResponse,
)

logger = logging.getLogger(__name__)



class EnrichmentHistoryService(BaseService[EnrichmentHistory, Any, Any]):
    """Service CRUD pour enrichmenthistory."""

    model = EnrichmentHistory

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EnrichmentHistory]
    # - get_or_fail(id) -> Result[EnrichmentHistory]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EnrichmentHistory]
    # - update(id, data) -> Result[EnrichmentHistory]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EnrichmentRateLimitService(BaseService[EnrichmentRateLimit, Any, Any]):
    """Service CRUD pour enrichmentratelimit."""

    model = EnrichmentRateLimit

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EnrichmentRateLimit]
    # - get_or_fail(id) -> Result[EnrichmentRateLimit]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EnrichmentRateLimit]
    # - update(id, data) -> Result[EnrichmentRateLimit]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EnrichmentProviderConfigService(BaseService[EnrichmentProviderConfig, Any, Any]):
    """Service CRUD pour enrichmentproviderconfig."""

    model = EnrichmentProviderConfig

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EnrichmentProviderConfig]
    # - get_or_fail(id) -> Result[EnrichmentProviderConfig]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EnrichmentProviderConfig]
    # - update(id, data) -> Result[EnrichmentProviderConfig]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

