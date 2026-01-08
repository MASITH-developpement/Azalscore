"""
AZALS API - Invoicing (Alias vers Module Commercial)
====================================================

Routes pour la facturation (devis, factures, commandes).
Ces routes sont des alias vers le module commercial M1.

Frontend: /v1/invoicing/*
Backend: Module Commercial (M1) - Documents
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.models import User

# Réutiliser les schémas et services du module commercial
from app.modules.commercial.models import DocumentType, DocumentStatus
from app.modules.commercial.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentList,
    DocumentLineCreate, DocumentLineResponse,
)
from app.modules.commercial.service import get_commercial_service

router = APIRouter(prefix="/invoicing", tags=["Invoicing - Facturation"])


# ============================================================================
# ENDPOINTS DEVIS (Quotes)
# ============================================================================

@router.get("/quotes", response_model=DocumentList)
async def list_quotes(
    status: Optional[DocumentStatus] = None,
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les devis avec filtres."""
    service = get_commercial_service(db, current_user.tenant_id)
    items, total = service.list_documents(
        type=DocumentType.QUOTE,
        status=status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@router.get("/quotes/{quote_id}", response_model=DocumentResponse)
async def get_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un devis."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.get_document(quote_id)
    if not document or document.type != DocumentType.QUOTE:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    return document


@router.post("/quotes", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau devis."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Forcer le type QUOTE
    data_dict = data.model_dump()
    data_dict["type"] = DocumentType.QUOTE
    data = DocumentCreate(**data_dict)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_document(data, current_user.id)


@router.put("/quotes/{quote_id}", response_model=DocumentResponse)
async def update_quote(
    quote_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un devis."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.get_document(quote_id)
    if not document or document.type != DocumentType.QUOTE:
        raise HTTPException(status_code=404, detail="Devis non trouvé")

    updated = service.update_document(quote_id, data)
    if not updated:
        raise HTTPException(status_code=400, detail="Devis non modifiable")
    return updated


@router.delete("/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un devis (brouillon uniquement)."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.get_document(quote_id)
    if not document or document.type != DocumentType.QUOTE:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    if document.status != DocumentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Seuls les brouillons peuvent être supprimés")

    # TODO: Implémenter delete_document dans le service
    raise HTTPException(status_code=501, detail="Suppression non implémentée")


@router.post("/quotes/{quote_id}/convert", response_model=DocumentResponse)
async def convert_quote_to_order(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convertir un devis en commande."""
    service = get_commercial_service(db, current_user.tenant_id)
    order = service.convert_quote_to_order(quote_id, current_user.id)
    if not order:
        raise HTTPException(status_code=400, detail="Devis non trouvé ou non convertible")
    return order


# ============================================================================
# ENDPOINTS FACTURES (Invoices)
# ============================================================================

@router.get("/invoices", response_model=DocumentList)
async def list_invoices(
    status: Optional[DocumentStatus] = None,
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les factures avec filtres."""
    service = get_commercial_service(db, current_user.tenant_id)
    items, total = service.list_documents(
        type=DocumentType.INVOICE,
        status=status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@router.get("/invoices/{invoice_id}", response_model=DocumentResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une facture."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.get_document(invoice_id)
    if not document or document.type != DocumentType.INVOICE:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return document


@router.post("/invoices", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle facture."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Forcer le type INVOICE
    data_dict = data.model_dump()
    data_dict["type"] = DocumentType.INVOICE
    data = DocumentCreate(**data_dict)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_document(data, current_user.id)


# ============================================================================
# ENDPOINTS COMMANDES (Orders)
# ============================================================================

@router.get("/orders", response_model=DocumentList)
async def list_orders(
    status: Optional[DocumentStatus] = None,
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les commandes avec filtres."""
    service = get_commercial_service(db, current_user.tenant_id)
    items, total = service.list_documents(
        type=DocumentType.ORDER,
        status=status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size
    )
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@router.get("/orders/{order_id}", response_model=DocumentResponse)
async def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une commande."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.get_document(order_id)
    if not document or document.type != DocumentType.ORDER:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return document


@router.post("/orders/{order_id}/invoice", response_model=DocumentResponse)
async def create_invoice_from_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une facture à partir d'une commande."""
    service = get_commercial_service(db, current_user.tenant_id)
    invoice = service.create_invoice_from_order(order_id, current_user.id)
    if not invoice:
        raise HTTPException(status_code=400, detail="Commande non trouvée ou non facturable")
    return invoice
