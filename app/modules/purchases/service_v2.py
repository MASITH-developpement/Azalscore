"""
AZALS - Purchases Service (v2 - CRUDRouter Compatible)
===========================================================

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

from app.modules.purchases.models import (
    PurchaseSupplier,
    LegacyPurchaseOrder,
    LegacyPurchaseOrderLine,
    LegacyPurchaseInvoice,
    LegacyPurchaseInvoiceLine,
)
from app.modules.purchases.schemas import (
    PurchaseInvoiceBase,
    PurchaseInvoiceCreate,
    PurchaseInvoiceLineBase,
    PurchaseInvoiceLineCreate,
    PurchaseInvoiceLineResponse,
    PurchaseInvoiceLineUpdate,
    PurchaseInvoiceResponse,
    PurchaseInvoiceUpdate,
    PurchaseOrderBase,
    PurchaseOrderCreate,
    PurchaseOrderLineBase,
    PurchaseOrderLineCreate,
    PurchaseOrderLineResponse,
    PurchaseOrderLineUpdate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    SupplierBase,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)

logger = logging.getLogger(__name__)



class PurchaseSupplierService(BaseService[PurchaseSupplier, Any, Any]):
    """Service CRUD pour purchasesupplier."""

    model = PurchaseSupplier

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[PurchaseSupplier]
    # - get_or_fail(id) -> Result[PurchaseSupplier]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[PurchaseSupplier]
    # - update(id, data) -> Result[PurchaseSupplier]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class LegacyPurchaseOrderService(BaseService[LegacyPurchaseOrder, Any, Any]):
    """Service CRUD pour legacypurchaseorder."""

    model = LegacyPurchaseOrder

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[LegacyPurchaseOrder]
    # - get_or_fail(id) -> Result[LegacyPurchaseOrder]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[LegacyPurchaseOrder]
    # - update(id, data) -> Result[LegacyPurchaseOrder]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class LegacyPurchaseOrderLineService(BaseService[LegacyPurchaseOrderLine, Any, Any]):
    """Service CRUD pour legacypurchaseorderline."""

    model = LegacyPurchaseOrderLine

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[LegacyPurchaseOrderLine]
    # - get_or_fail(id) -> Result[LegacyPurchaseOrderLine]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[LegacyPurchaseOrderLine]
    # - update(id, data) -> Result[LegacyPurchaseOrderLine]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class LegacyPurchaseInvoiceService(BaseService[LegacyPurchaseInvoice, Any, Any]):
    """Service CRUD pour legacypurchaseinvoice."""

    model = LegacyPurchaseInvoice

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[LegacyPurchaseInvoice]
    # - get_or_fail(id) -> Result[LegacyPurchaseInvoice]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[LegacyPurchaseInvoice]
    # - update(id, data) -> Result[LegacyPurchaseInvoice]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques


class LegacyPurchaseInvoiceLineService(BaseService[LegacyPurchaseInvoiceLine, Any, Any]):
    """Service CRUD pour legacypurchaseinvoiceline."""

    model = LegacyPurchaseInvoiceLine

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[LegacyPurchaseInvoiceLine]
    # - get_or_fail(id) -> Result[LegacyPurchaseInvoiceLine]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[LegacyPurchaseInvoiceLine]
    # - update(id, data) -> Result[LegacyPurchaseInvoiceLine]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques

