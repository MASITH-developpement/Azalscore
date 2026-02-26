"""
AZALS - Odoo Import Service (v2 - CRUDRouter Compatible)
=============================================================

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

from app.modules.odoo_import.models import (
    OdooConnectionConfig,
    OdooImportHistory,
    OdooFieldMapping,
)
from app.modules.odoo_import.schemas import (
    OdooConnectionConfigCreate,
    OdooConnectionConfigResponse,
    OdooConnectionConfigUpdate,
    OdooDataPreviewResponse,
    OdooFieldMappingCreate,
    OdooFieldMappingResponse,
    OdooHistoryDetailResponse,
    OdooHistorySearchResponse,
    OdooImportHistoryResponse,
    OdooNextRunsResponse,
    OdooScheduleConfigResponse,
    OdooTestConnectionResponse,
)

logger = logging.getLogger(__name__)



class OdooConnectionConfigService(BaseService[OdooConnectionConfig, Any, Any]):
    """Service CRUD pour odooconnectionconfig."""

    model = OdooConnectionConfig

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[OdooConnectionConfig]
    # - get_or_fail(id) -> Result[OdooConnectionConfig]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[OdooConnectionConfig]
    # - update(id, data) -> Result[OdooConnectionConfig]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class OdooImportHistoryService(BaseService[OdooImportHistory, Any, Any]):
    """Service CRUD pour odooimporthistory."""

    model = OdooImportHistory

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[OdooImportHistory]
    # - get_or_fail(id) -> Result[OdooImportHistory]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[OdooImportHistory]
    # - update(id, data) -> Result[OdooImportHistory]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class OdooFieldMappingService(BaseService[OdooFieldMapping, Any, Any]):
    """Service CRUD pour odoofieldmapping."""

    model = OdooFieldMapping

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[OdooFieldMapping]
    # - get_or_fail(id) -> Result[OdooFieldMapping]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[OdooFieldMapping]
    # - update(id, data) -> Result[OdooFieldMapping]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

