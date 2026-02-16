"""
AZALS - Contacts Service (v2 - CRUDRouter Compatible)
==========================================================

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

from app.modules.contacts.models import (
    ContactSequence,
    UnifiedContact,
    ContactPerson,
    ContactAddress,
)
from app.modules.contacts.schemas import (
    ContactAddressBase,
    ContactAddressCreate,
    ContactAddressResponse,
    ContactAddressUpdate,
    ContactBase,
    ContactCreate,
    ContactPersonBase,
    ContactPersonCreate,
    ContactPersonResponse,
    ContactPersonUpdate,
    ContactResponse,
    ContactUpdate,
)

logger = logging.getLogger(__name__)



class ContactSequenceService(BaseService[ContactSequence, Any, Any]):
    """Service CRUD pour contactsequence."""

    model = ContactSequence

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ContactSequence]
    # - get_or_fail(id) -> Result[ContactSequence]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ContactSequence]
    # - update(id, data) -> Result[ContactSequence]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class UnifiedContactService(BaseService[UnifiedContact, Any, Any]):
    """Service CRUD pour unifiedcontact."""

    model = UnifiedContact

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[UnifiedContact]
    # - get_or_fail(id) -> Result[UnifiedContact]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[UnifiedContact]
    # - update(id, data) -> Result[UnifiedContact]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ContactPersonService(BaseService[ContactPerson, Any, Any]):
    """Service CRUD pour contactperson."""

    model = ContactPerson

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ContactPerson]
    # - get_or_fail(id) -> Result[ContactPerson]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ContactPerson]
    # - update(id, data) -> Result[ContactPerson]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ContactAddressService(BaseService[ContactAddress, Any, Any]):
    """Service CRUD pour contactaddress."""

    model = ContactAddress

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[ContactAddress]
    # - get_or_fail(id) -> Result[ContactAddress]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[ContactAddress]
    # - update(id, data) -> Result[ContactAddress]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

