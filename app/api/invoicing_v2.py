"""
AZALS API - Invoicing v2 (MIGRE CORE SaaS)
==========================================

API pour Devis, Factures, Avoirs - Version CORE SaaS.

MIGRATION CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user()
- SaaSContext fournit tenant_id + user_id directement
- Audit automatique via CoreAuthMiddleware
"""

import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.modules.commercial.models import DocumentStatus, DocumentType
from app.modules.commercial.schemas import (
    DocumentCreate,
    DocumentLineCreate,
    DocumentLineResponse,
    DocumentUpdate,
)
from app.modules.commercial.service import get_commercial_service

router = APIRouter(prefix="/v2/invoicing", tags=["Invoicing v2 - CORE SaaS"])


# ============================================================================
# SCHEMAS
# ============================================================================

class InvoiceLineInput(BaseModel):
    """Ligne de document pour creation."""
    description: str
    quantity: Decimal = Field(default=Decimal("1"))
    unit_price: Decimal
    vat_rate: Decimal = Field(default=Decimal("20"))
    discount_percent: Decimal | None = None


class InvoiceCreate(BaseModel):
    """Schema de creation de document facturation."""
    client_id: UUID
    date: datetime.date | None = None
    due_date: datetime.date | None = None
    notes: str | None = None
    payment_terms: str | None = None
    lines: list[InvoiceLineInput] = []


class InvoiceResponse(BaseModel):
    """Response schema pour un document."""
    id: UUID
    number: str
    type: str
    status: str
    client_id: UUID
    client_name: str
    date: datetime.date
    due_date: datetime.date | None = None
    total_ht: Decimal
    total_ttc: Decimal
    currency: str = "EUR"
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class InvoiceDetailResponse(InvoiceResponse):
    """Response avec lignes."""
    lines: list[DocumentLineResponse] = []
    notes: str | None = None
    payment_terms: str | None = None


class InvoiceListResponse(BaseModel):
    """Liste paginee."""
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# HELPERS
# ============================================================================

TYPE_MAPPING = {
    "quotes": DocumentType.QUOTE,
    "invoices": DocumentType.INVOICE,
    "credits": DocumentType.CREDIT_NOTE,
}


def _doc_to_response(doc, doc_type: str) -> InvoiceResponse:
    """Convertit un document en response."""
    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type=doc_type,
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,
        total_ttc=doc.total,
        currency=doc.currency,
        created_at=doc.created_at
    )


def _doc_to_detail_response(doc, doc_type: str) -> InvoiceDetailResponse:
    """Convertit un document en response detaillee."""
    return InvoiceDetailResponse(
        id=doc.id,
        number=doc.number,
        type=doc_type,
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,
        total_ttc=doc.total,
        currency=doc.currency,
        created_at=doc.created_at,
        lines=doc.lines,
        notes=doc.notes,
        payment_terms=doc.payment_terms
    )


# ============================================================================
# ENDPOINTS DEVIS (QUOTES)
# ============================================================================

@router.get("/quotes", response_model=InvoiceListResponse)
async def list_quotes(
    status_filter: str | None = Query(None, alias="status"),
    client_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les devis du tenant.

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    service = get_commercial_service(db, context.tenant_id)
    doc_status = DocumentStatus(status_filter) if status_filter else None

    items, total = service.list_documents(
        doc_type=DocumentType.QUOTE,
        status=doc_status,
        customer_id=client_id,
        search=search,
        page=page,
        page_size=page_size
    )

    return InvoiceListResponse(
        items=[_doc_to_response(item, "quote") for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/quotes/{quote_id}", response_model=InvoiceDetailResponse)
async def get_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Recuperer un devis."""
    service = get_commercial_service(db, context.tenant_id)
    doc = service.get_document(quote_id)

    if not doc or doc.type != DocumentType.QUOTE:
        raise HTTPException(status_code=404, detail="Devis non trouve")

    return _doc_to_detail_response(doc, "quote")


@router.post("/quotes", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Creer un nouveau devis.

    CORE SaaS: Utilise context.user_id pour le created_by.
    """
    service = get_commercial_service(db, context.tenant_id)

    doc_data = DocumentCreate(
        type=DocumentType.QUOTE,
        customer_id=data.client_id,
        date=data.date or datetime.date.today(),
        due_date=data.due_date,
        notes=data.notes,
        payment_terms=data.payment_terms
    )

    doc = service.create_document(doc_data, context.user_id)

    # Ajouter les lignes
    for line in data.lines:
        line_data = DocumentLineCreate(
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            tax_rate=float(line.vat_rate) if line.vat_rate else 20.0,
            discount_percent=float(line.discount_percent) if line.discount_percent else 0.0
        )
        service.add_document_line(doc.id, line_data)

    # Recharger pour avoir les totaux
    doc = service.get_document(doc.id)
    return _doc_to_response(doc, "quote")


@router.put("/quotes/{quote_id}", response_model=InvoiceResponse)
async def update_quote(
    quote_id: UUID,
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Modifier un devis."""
    service = get_commercial_service(db, context.tenant_id)
    doc = service.get_document(quote_id)

    if not doc or doc.type != DocumentType.QUOTE:
        raise HTTPException(status_code=404, detail="Devis non trouve")

    update_data = DocumentUpdate(
        customer_id=data.client_id,
        date=data.date,
        due_date=data.due_date,
        notes=data.notes,
        payment_terms=data.payment_terms
    )
    doc = service.update_document(quote_id, update_data)

    return _doc_to_response(doc, "quote")


@router.delete("/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un devis (brouillon uniquement)."""
    service = get_commercial_service(db, context.tenant_id)
    doc = service.get_document(quote_id)

    if not doc or doc.type != DocumentType.QUOTE:
        raise HTTPException(status_code=404, detail="Devis non trouve")
    if doc.status != DocumentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Seuls les brouillons peuvent etre supprimes")

    service.delete_document(quote_id)


@router.post("/quotes/{quote_id}/send", response_model=InvoiceResponse)
async def send_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Envoyer un devis au client."""
    service = get_commercial_service(db, context.tenant_id)
    doc = service.send_document(quote_id, context.user_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Devis non trouve")

    return _doc_to_response(doc, "quote")


# ============================================================================
# ENDPOINTS FACTURES (INVOICES)
# ============================================================================

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    status_filter: str | None = Query(None, alias="status"),
    client_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les factures du tenant."""
    service = get_commercial_service(db, context.tenant_id)
    doc_status = DocumentStatus(status_filter) if status_filter else None

    items, total = service.list_documents(
        doc_type=DocumentType.INVOICE,
        status=doc_status,
        customer_id=client_id,
        search=search,
        page=page,
        page_size=page_size
    )

    return InvoiceListResponse(
        items=[_doc_to_response(item, "invoice") for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Recuperer une facture."""
    service = get_commercial_service(db, context.tenant_id)
    doc = service.get_document(invoice_id)

    if not doc or doc.type != DocumentType.INVOICE:
        raise HTTPException(status_code=404, detail="Facture non trouvee")

    return _doc_to_detail_response(doc, "invoice")


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Creer une nouvelle facture."""
    service = get_commercial_service(db, context.tenant_id)

    doc_data = DocumentCreate(
        type=DocumentType.INVOICE,
        customer_id=data.client_id,
        date=data.date or datetime.date.today(),
        due_date=data.due_date or (datetime.date.today() + datetime.timedelta(days=30)),
        notes=data.notes,
        payment_terms=data.payment_terms
    )

    doc = service.create_document(doc_data, context.user_id)

    for line in data.lines:
        line_data = DocumentLineCreate(
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            tax_rate=float(line.vat_rate) if line.vat_rate else 20.0,
            discount_percent=float(line.discount_percent) if line.discount_percent else 0.0
        )
        service.add_document_line(doc.id, line_data)

    doc = service.get_document(doc.id)
    return _doc_to_response(doc, "invoice")


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer une facture (brouillon uniquement)."""
    service = get_commercial_service(db, context.tenant_id)
    doc = service.get_document(invoice_id)

    if not doc or doc.type != DocumentType.INVOICE:
        raise HTTPException(status_code=404, detail="Facture non trouvee")
    if doc.status != DocumentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Seuls les brouillons peuvent etre supprimes")

    service.delete_document(invoice_id)


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Envoyer une facture au client."""
    service = get_commercial_service(db, context.tenant_id)
    doc = service.send_document(invoice_id, context.user_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Facture non trouvee")

    return _doc_to_response(doc, "invoice")


# ============================================================================
# ENDPOINTS AVOIRS (CREDITS)
# ============================================================================

@router.get("/credits", response_model=InvoiceListResponse)
async def list_credits(
    status_filter: str | None = Query(None, alias="status"),
    client_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Lister les avoirs du tenant."""
    service = get_commercial_service(db, context.tenant_id)
    doc_status = DocumentStatus(status_filter) if status_filter else None

    items, total = service.list_documents(
        doc_type=DocumentType.CREDIT_NOTE,
        status=doc_status,
        customer_id=client_id,
        search=search,
        page=page,
        page_size=page_size
    )

    return InvoiceListResponse(
        items=[_doc_to_response(item, "credit") for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/credits", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_credit(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Creer un nouvel avoir."""
    service = get_commercial_service(db, context.tenant_id)

    doc_data = DocumentCreate(
        type=DocumentType.CREDIT_NOTE,
        customer_id=data.client_id,
        date=data.date or datetime.date.today(),
        notes=data.notes
    )

    doc = service.create_document(doc_data, context.user_id)

    for line in data.lines:
        line_data = DocumentLineCreate(
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            tax_rate=float(line.vat_rate) if line.vat_rate else 20.0,
            discount_percent=float(line.discount_percent) if line.discount_percent else 0.0
        )
        service.add_document_line(doc.id, line_data)

    doc = service.get_document(doc.id)
    return _doc_to_response(doc, "credit")
