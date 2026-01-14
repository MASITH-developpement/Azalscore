"""
AZALS API - Invoicing (Devis, Factures, Avoirs)
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User
from app.modules.commercial.models import DocumentStatus, DocumentType
from app.modules.commercial.schemas import (
    DocumentCreate,
    DocumentLineCreate,
    DocumentLineResponse,
    DocumentUpdate,
)
from app.modules.commercial.service import get_commercial_service

router = APIRouter(prefix="/invoicing", tags=["Invoicing - Devis, Factures, Avoirs"])


# ============================================================================
# SCHEMAS SPECIFIQUES INVOICING
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
    date: date | None = None
    due_date: date | None = None
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
    date: date
    due_date: date | None = None
    total_ht: Decimal
    total_ttc: Decimal
    currency: str = "EUR"
    created_at: datetime

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
# MAPPING TYPE
# ============================================================================

TYPE_MAPPING = {
    "quotes": DocumentType.QUOTE,
    "invoices": DocumentType.INVOICE,
    "credits": DocumentType.CREDIT_NOTE,
}


def get_document_type(type_name: str) -> DocumentType:
    """Convertit le nom URL en DocumentType."""
    if type_name not in TYPE_MAPPING:
        raise HTTPException(status_code=400, detail=f"Type invalide: {type_name}")
    return TYPE_MAPPING[type_name]


# ============================================================================
# ENDPOINTS DEVIS (QUOTES)
# ============================================================================

@router.get("/quotes", response_model=InvoiceListResponse)
async def list_quotes(
    status: str | None = None,
    client_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les devis."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc_status = DocumentStatus(status) if status else None
    items, total = service.list_documents(
        doc_type=DocumentType.QUOTE,
        status=doc_status,
        customer_id=client_id,
        search=search,
        page=page,
        page_size=page_size
    )

    response_items = []
    for item in items:
        response_items.append(InvoiceResponse(
            id=item.id,
            number=item.number,
            type="quote",
            status=item.status.value if hasattr(item.status, 'value') else str(item.status),
            client_id=item.customer_id,
            client_name=item.customer.name if item.customer else "N/A",
            date=item.date,
            due_date=item.due_date,
            total_ht=item.subtotal,  # subtotal = Total HT
            total_ttc=item.total,    # total = Total TTC
            currency=item.currency,
            created_at=item.created_at
        ))

    return InvoiceListResponse(items=response_items, total=total, page=page, page_size=page_size)


@router.get("/quotes/{quote_id}", response_model=InvoiceDetailResponse)
async def get_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un devis."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc = service.get_document(quote_id)
    if not doc or doc.type != DocumentType.QUOTE:
        raise HTTPException(status_code=404, detail="Devis non trouve")

    return InvoiceDetailResponse(
        id=doc.id,
        number=doc.number,
        type="quote",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at,
        lines=doc.lines,
        notes=doc.notes,
        payment_terms=doc.payment_terms
    )


@router.post("/quotes", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un nouveau devis."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Convertir en DocumentCreate
    doc_data = DocumentCreate(
        type=DocumentType.QUOTE,
        customer_id=data.client_id,
        date=data.date or date.today(),
        due_date=data.due_date,
        notes=data.notes,
        payment_terms=data.payment_terms
    )

    doc = service.create_document(doc_data, current_user.id)

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

    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type="quote",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at
    )


@router.put("/quotes/{quote_id}", response_model=InvoiceResponse)
async def update_quote(
    quote_id: UUID,
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modifier un devis."""
    service = get_commercial_service(db, current_user.tenant_id)
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

    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type="quote",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at
    )


@router.delete("/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un devis (brouillon uniquement)."""
    service = get_commercial_service(db, current_user.tenant_id)
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
    current_user: User = Depends(get_current_user)
):
    """Envoyer un devis au client."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc = service.send_document(quote_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Devis non trouve")

    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type="quote",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at
    )


# ============================================================================
# ENDPOINTS FACTURES (INVOICES)
# ============================================================================

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    status: str | None = None,
    client_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les factures."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc_status = DocumentStatus(status) if status else None
    items, total = service.list_documents(
        doc_type=DocumentType.INVOICE,
        status=doc_status,
        customer_id=client_id,
        search=search,
        page=page,
        page_size=page_size
    )

    response_items = []
    for item in items:
        response_items.append(InvoiceResponse(
            id=item.id,
            number=item.number,
            type="invoice",
            status=item.status.value if hasattr(item.status, 'value') else str(item.status),
            client_id=item.customer_id,
            client_name=item.customer.name if item.customer else "N/A",
            date=item.date,
            due_date=item.due_date,
            total_ht=item.subtotal,  # subtotal = Total HT
            total_ttc=item.total,    # total = Total TTC
            currency=item.currency,
            created_at=item.created_at
        ))

    return InvoiceListResponse(items=response_items, total=total, page=page, page_size=page_size)


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une facture."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc = service.get_document(invoice_id)
    if not doc or doc.type != DocumentType.INVOICE:
        raise HTTPException(status_code=404, detail="Facture non trouvee")

    return InvoiceDetailResponse(
        id=doc.id,
        number=doc.number,
        type="invoice",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at,
        lines=doc.lines,
        notes=doc.notes,
        payment_terms=doc.payment_terms
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une nouvelle facture."""
    service = get_commercial_service(db, current_user.tenant_id)

    doc_data = DocumentCreate(
        type=DocumentType.INVOICE,
        customer_id=data.client_id,
        date=data.date or date.today(),
        due_date=data.due_date,
        notes=data.notes,
        payment_terms=data.payment_terms
    )

    doc = service.create_document(doc_data, current_user.id)

    for line in data.lines:
        line_data = DocumentLineCreate(
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            vat_rate=line.vat_rate,
            discount_percent=line.discount_percent
        )
        service.add_document_line(doc.id, line_data)

    doc = service.get_document(doc.id)

    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type="invoice",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at
    )


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envoyer une facture au client."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc = service.send_document(invoice_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Facture non trouvee")

    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type="invoice",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at
    )


# ============================================================================
# ENDPOINTS AVOIRS (CREDITS)
# ============================================================================

@router.get("/credits", response_model=InvoiceListResponse)
async def list_credits(
    status: str | None = None,
    client_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les avoirs."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc_status = DocumentStatus(status) if status else None
    items, total = service.list_documents(
        doc_type=DocumentType.CREDIT_NOTE,
        status=doc_status,
        customer_id=client_id,
        search=search,
        page=page,
        page_size=page_size
    )

    response_items = []
    for item in items:
        response_items.append(InvoiceResponse(
            id=item.id,
            number=item.number,
            type="credit",
            status=item.status.value if hasattr(item.status, 'value') else str(item.status),
            client_id=item.customer_id,
            client_name=item.customer.name if item.customer else "N/A",
            date=item.date,
            due_date=item.due_date,
            total_ht=item.subtotal,  # subtotal = Total HT
            total_ttc=item.total,    # total = Total TTC
            currency=item.currency,
            created_at=item.created_at
        ))

    return InvoiceListResponse(items=response_items, total=total, page=page, page_size=page_size)


@router.post("/credits", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_credit(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un nouvel avoir."""
    service = get_commercial_service(db, current_user.tenant_id)

    doc_data = DocumentCreate(
        type=DocumentType.CREDIT_NOTE,
        customer_id=data.client_id,
        date=data.date or date.today(),
        due_date=data.due_date,
        notes=data.notes,
        payment_terms=data.payment_terms
    )

    doc = service.create_document(doc_data, current_user.id)

    for line in data.lines:
        line_data = DocumentLineCreate(
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            vat_rate=line.vat_rate,
            discount_percent=line.discount_percent
        )
        service.add_document_line(doc.id, line_data)

    doc = service.get_document(doc.id)

    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type="credit",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at
    )


@router.post("/credits/{credit_id}/send", response_model=InvoiceResponse)
async def send_credit(
    credit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envoyer un avoir au client."""
    service = get_commercial_service(db, current_user.tenant_id)
    doc = service.send_document(credit_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Avoir non trouve")

    return InvoiceResponse(
        id=doc.id,
        number=doc.number,
        type="credit",
        status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
        client_id=doc.customer_id,
        client_name=doc.customer.name if doc.customer else "N/A",
        date=doc.date,
        due_date=doc.due_date,
        total_ht=doc.subtotal,  # subtotal = Total HT dans le modèle
        total_ttc=doc.total,    # total = Total TTC dans le modèle
        currency=doc.currency,
        created_at=doc.created_at
    )
