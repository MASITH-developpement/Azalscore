"""
AZALS - Backup Service (v2 - CRUDRouter Compatible)
========================================================

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

from app.modules.backup.models import (
    BackupConfig,
    Backup,
    RestoreLog,
)
from app.modules.backup.schemas import (
    BackupConfigCreate,
    BackupConfigResponse,
    BackupConfigUpdate,
    BackupCreate,
    BackupResponse,
    RestoreResponse,
)

logger = logging.getLogger(__name__)



class BackupConfigService(BaseService[BackupConfig, Any, Any]):
    """Service CRUD pour backupconfig."""

    model = BackupConfig

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[BackupConfig]
    # - get_or_fail(id) -> Result[BackupConfig]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[BackupConfig]
    # - update(id, data) -> Result[BackupConfig]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class BackupService(BaseService[Backup, Any, Any]):
    """Service CRUD pour backup."""

    model = Backup

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Backup]
    # - get_or_fail(id) -> Result[Backup]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Backup]
    # - update(id, data) -> Result[Backup]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class RestoreLogService(BaseService[RestoreLog, Any, Any]):
    """Service CRUD pour restorelog."""

    model = RestoreLog

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[RestoreLog]
    # - get_or_fail(id) -> Result[RestoreLog]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[RestoreLog]
    # - update(id, data) -> Result[RestoreLog]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

