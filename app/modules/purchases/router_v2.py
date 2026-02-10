"""
AZALS MODULE M4 - Router Purchases v2
======================================

API REST pour la gestion des achats - CORE SaaS v2.
Migration vers SaaSContext pour l'authentification et l'isolation tenant.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.database import get_db

from .models import InvoiceStatus, OrderStatus, SupplierStatus
from .schemas import (
    PaginatedInvoices,
    PaginatedOrders,
    PaginatedSuppliers,
    PurchaseInvoiceCreate,
    PurchaseInvoiceResponse,
    PurchaseInvoiceUpdate,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchasesSummary,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)
from .service import PurchasesService


router = APIRouter(
    prefix="/v2/purchases",
    tags=["Purchases v2 - CORE SaaS"]
)


def get_purchases_service(
    db: Session,
    tenant_id: str,
    user_id: str
) -> PurchasesService:
    """Factory pour créer le service Purchases avec CORE SaaS v2."""
    return PurchasesService(db, tenant_id, user_id)


# ============================================================================
# ENDPOINTS FOURNISSEURS
# ============================================================================

@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer un nouveau fournisseur."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    return service.create_supplier(data, context.user_id)


@router.get("/suppliers", response_model=PaginatedSuppliers)
async def list_suppliers(
    status_filter: Optional[SupplierStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les fournisseurs avec filtres."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    items, total = service.list_suppliers(status_filter, search, is_active, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedSuppliers(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer un fournisseur."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    supplier = service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour un fournisseur."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    supplier = service.update_supplier(supplier_id, data)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return supplier


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un fournisseur (soft delete)."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    success = service.delete_supplier(supplier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")


# ============================================================================
# ENDPOINTS COMMANDES D'ACHAT
# ============================================================================

@router.post("/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une nouvelle commande d'achat."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    return service.create_order(data, context.user_id)


@router.get("/orders", response_model=PaginatedOrders)
async def list_orders(
    supplier_id: Optional[UUID] = None,
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les commandes d'achat avec filtres."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    items, total = service.list_orders(supplier_id, status_filter, search, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedOrders(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une commande d'achat."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


@router.put("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def update_order(
    order_id: UUID,
    data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour une commande d'achat."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    order = service.update_order(order_id, data)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


@router.post("/orders/{order_id}/validate", response_model=PurchaseOrderResponse)
async def validate_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Valider une commande d'achat (DRAFT → SENT)."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    order = service.validate_order(order_id, context.user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


@router.post("/orders/{order_id}/cancel", response_model=PurchaseOrderResponse)
async def cancel_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Annuler une commande d'achat."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    order = service.cancel_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer une commande d'achat (seulement si DRAFT)."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    if order.status != OrderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Seules les commandes en brouillon peuvent être supprimées")

    service.db.delete(order)
    service.db.commit()


# ============================================================================
# ENDPOINTS FACTURES FOURNISSEURS
# ============================================================================

@router.post("/invoices", response_model=PurchaseInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Créer une nouvelle facture fournisseur."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    return service.create_invoice(data, context.user_id)


@router.get("/invoices", response_model=PaginatedInvoices)
async def list_invoices(
    supplier_id: Optional[UUID] = None,
    order_id: Optional[UUID] = None,
    status_filter: Optional[InvoiceStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les factures fournisseurs avec filtres."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    items, total = service.list_invoices(supplier_id, order_id, status_filter, search, page, per_page)

    pages = (total + per_page - 1) // per_page

    return PaginatedInvoices(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Récupérer une facture fournisseur."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return invoice


@router.put("/invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    data: PurchaseInvoiceUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre à jour une facture fournisseur."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    invoice = service.update_invoice(invoice_id, data)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return invoice


@router.post("/invoices/{invoice_id}/validate", response_model=PurchaseInvoiceResponse)
async def validate_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Valider une facture fournisseur (DRAFT → VALIDATED)."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    invoice = service.validate_invoice(invoice_id, context.user_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer une facture fournisseur (seulement si DRAFT)."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Seules les factures en brouillon peuvent être supprimées")

    service.db.delete(invoice)
    service.db.commit()


# ============================================================================
# ENDPOINTS SUMMARY / DASHBOARD
# ============================================================================

@router.get("/summary", response_model=PurchasesSummary)
async def get_summary(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Obtenir le résumé du module achats."""
    service = get_purchases_service(db, context.tenant_id, context.user_id)
    return service.get_summary()
