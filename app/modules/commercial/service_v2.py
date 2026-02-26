"""
AZALS - Commercial Service (v2 - CRUDRouter Compatible)
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

from app.modules.commercial.models import (
    Customer,
    Contact,
    Opportunity,
    CommercialDocument,
    DocumentLine,
    Payment,
    CustomerActivity,
    PipelineStage,
    CatalogProduct,
)
from app.modules.commercial.schemas import (
    ActivityBase,
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    ContactBase,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    CustomerBase,
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
    DocumentBase,
    DocumentCreate,
    DocumentLineBase,
    DocumentLineCreate,
    DocumentLineResponse,
    DocumentResponse,
    DocumentUpdate,
    OpportunityBase,
    OpportunityCreate,
    OpportunityResponse,
    OpportunityUpdate,
    PaymentBase,
    PaymentCreate,
    PaymentResponse,
    PipelineStageBase,
    PipelineStageCreate,
    PipelineStageResponse,
    ProductBase,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

logger = logging.getLogger(__name__)



class CustomerService(BaseService[Customer, Any, Any]):
    """Service CRUD pour customer."""

    model = Customer

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Customer]
    # - get_or_fail(id) -> Result[Customer]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Customer]
    # - update(id, data) -> Result[Customer]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class ContactService(BaseService[Contact, Any, Any]):
    """Service CRUD pour contact."""

    model = Contact

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Contact]
    # - get_or_fail(id) -> Result[Contact]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Contact]
    # - update(id, data) -> Result[Contact]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class OpportunityService(BaseService[Opportunity, Any, Any]):
    """Service CRUD pour opportunity."""

    model = Opportunity

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Opportunity]
    # - get_or_fail(id) -> Result[Opportunity]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Opportunity]
    # - update(id, data) -> Result[Opportunity]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class CommercialDocumentService(BaseService[CommercialDocument, Any, Any]):
    """Service CRUD pour commercialdocument."""

    model = CommercialDocument

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[CommercialDocument]
    # - get_or_fail(id) -> Result[CommercialDocument]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[CommercialDocument]
    # - update(id, data) -> Result[CommercialDocument]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class DocumentLineService(BaseService[DocumentLine, Any, Any]):
    """Service CRUD pour documentline."""

    model = DocumentLine

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[DocumentLine]
    # - get_or_fail(id) -> Result[DocumentLine]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[DocumentLine]
    # - update(id, data) -> Result[DocumentLine]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class PaymentService(BaseService[Payment, Any, Any]):
    """Service CRUD pour payment."""

    model = Payment

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[Payment]
    # - get_or_fail(id) -> Result[Payment]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[Payment]
    # - update(id, data) -> Result[Payment]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class CustomerActivityService(BaseService[CustomerActivity, Any, Any]):
    """Service CRUD pour customeractivity."""

    model = CustomerActivity

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[CustomerActivity]
    # - get_or_fail(id) -> Result[CustomerActivity]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[CustomerActivity]
    # - update(id, data) -> Result[CustomerActivity]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class PipelineStageService(BaseService[PipelineStage, Any, Any]):
    """Service CRUD pour pipelinestage."""

    model = PipelineStage

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[PipelineStage]
    # - get_or_fail(id) -> Result[PipelineStage]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[PipelineStage]
    # - update(id, data) -> Result[PipelineStage]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class CatalogProductService(BaseService[CatalogProduct, Any, Any]):
    """Service CRUD pour catalogproduct."""

    model = CatalogProduct

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[CatalogProduct]
    # - get_or_fail(id) -> Result[CatalogProduct]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[CatalogProduct]
    # - update(id, data) -> Result[CatalogProduct]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

