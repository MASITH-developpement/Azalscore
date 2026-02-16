"""
AZALS - Email Service (v2 - CRUDRouter Compatible)
=======================================================

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

from app.modules.email.models import (
    EmailTemplate,
    EmailLog,
    EmailConfig,
    EmailQueue,
)
from app.modules.email.schemas import (
    BulkSendResponse,
    EmailConfigCreate,
    EmailConfigResponse,
    EmailConfigUpdate,
    EmailLogResponse,
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    SendEmailResponse,
)

logger = logging.getLogger(__name__)



class EmailTemplateService(BaseService[EmailTemplate, Any, Any]):
    """Service CRUD pour emailtemplate."""

    model = EmailTemplate

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EmailTemplate]
    # - get_or_fail(id) -> Result[EmailTemplate]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EmailTemplate]
    # - update(id, data) -> Result[EmailTemplate]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EmailLogService(BaseService[EmailLog, Any, Any]):
    """Service CRUD pour emaillog."""

    model = EmailLog

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EmailLog]
    # - get_or_fail(id) -> Result[EmailLog]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EmailLog]
    # - update(id, data) -> Result[EmailLog]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EmailConfigService(BaseService[EmailConfig, Any, Any]):
    """Service CRUD pour emailconfig."""

    model = EmailConfig

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EmailConfig]
    # - get_or_fail(id) -> Result[EmailConfig]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EmailConfig]
    # - update(id, data) -> Result[EmailConfig]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class EmailQueueService(BaseService[EmailQueue, Any, Any]):
    """Service CRUD pour emailqueue."""

    model = EmailQueue

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[EmailQueue]
    # - get_or_fail(id) -> Result[EmailQueue]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[EmailQueue]
    # - update(id, data) -> Result[EmailQueue]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

