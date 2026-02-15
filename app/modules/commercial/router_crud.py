"""
AZALS - Commercial Router (CRUDRouter v3)
==========================================

Router complet pour le module Commercial (CRM).
Compatible v1, v2, et v3 via app.azals.

Conformite : AZA-NF-006
"""

from datetime import date
from datetime import datetime as dt
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .models import CustomerType, DocumentStatus, DocumentType, OpportunityStatus
from .schemas import (
    ActivityCreate,
    ActivityResponse,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    CustomerCreate,
    CustomerList,
    CustomerResponse,
    CustomerUpdate,
    DocumentCreate,
    DocumentLineCreate,
    DocumentLineResponse,
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
    OpportunityCreate,
    OpportunityList,
    OpportunityResponse,
    OpportunityUpdate,
    PaymentCreate,
    PaymentResponse,
    PipelineStageCreate,
    PipelineStageResponse,
    PipelineStats,
    ProductCreate,
    ProductList,
    ProductResponse,
    ProductUpdate,
    SalesDashboard,
)
from .service import CommercialService


# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/commercial", tags=["Commercial - CRM"])


# =============================================================================
# HELPER: Factory Service
# =============================================================================

def get_commercial_service(db: Session, tenant_id: str) -> CommercialService:
    """Factory pour creer le service Commercial."""
    return CommercialService(db, tenant_id)


# =============================================================================
# ENDPOINTS STATUS
# =============================================================================

@router.get("/status")
async def get_module_status():
    """Statut du module Commercial."""
    return {
        "module": "commercial",
        "version": "v3",
        "status": "active"
    }


# =============================================================================
# ENDPOINTS CLIENTS
# =============================================================================

@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer un nouveau client/prospect."""
    service = get_commercial_service(db, context.tenant_id)

    if data.code:
        existing = service.get_customer_by_code(data.code)
        if existing:
            raise HTTPException(status_code=400, detail="Code client deja utilise")

    return service.create_customer(data, context.user_id)


@router.get("/customers", response_model=CustomerList)
async def list_customers(
    type: Optional[CustomerType] = None,
    assigned_to: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les clients avec filtres."""
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_customers(type, assigned_to, is_active, search, page, page_size)
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer un client."""
    service = get_commercial_service(db, context.tenant_id)
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre a jour un client."""
    service = get_commercial_service(db, context.tenant_id)
    customer = service.update_customer(customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")
    return customer


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer un client."""
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_customer(customer_id):
        raise HTTPException(status_code=404, detail="Client non trouve")


@router.post("/customers/{customer_id}/convert", response_model=CustomerResponse)
async def convert_prospect(
    customer_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Convertir un prospect en client."""
    service = get_commercial_service(db, context.tenant_id)
    customer = service.convert_prospect(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")
    return customer


# =============================================================================
# ENDPOINTS CONTACTS
# =============================================================================

@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer un contact pour un client."""
    service = get_commercial_service(db, context.tenant_id)

    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")

    return service.create_contact(data)


@router.get("/customers/{customer_id}/contacts", response_model=List[ContactResponse])
async def list_contacts(
    customer_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les contacts d'un client."""
    service = get_commercial_service(db, context.tenant_id)
    return service.list_contacts(customer_id)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre a jour un contact."""
    service = get_commercial_service(db, context.tenant_id)
    contact = service.update_contact(contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouve")
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer un contact."""
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouve")


# =============================================================================
# ENDPOINTS OPPORTUNITES
# =============================================================================

@router.post("/opportunities", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: OpportunityCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer une opportunite."""
    service = get_commercial_service(db, context.tenant_id)

    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")

    return service.create_opportunity(data, context.user_id)


@router.get("/opportunities", response_model=OpportunityList)
async def list_opportunities(
    status: Optional[OpportunityStatus] = None,
    customer_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les opportunites."""
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_opportunities(status, customer_id, assigned_to, page, page_size)
    return OpportunityList(items=items, total=total, page=page, page_size=page_size)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer une opportunite."""
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunite non trouvee")
    return opportunity


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: UUID,
    data: OpportunityUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre a jour une opportunite."""
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.update_opportunity(opportunity_id, data)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunite non trouvee")
    return opportunity


@router.post("/opportunities/{opportunity_id}/win", response_model=OpportunityResponse)
async def win_opportunity(
    opportunity_id: UUID,
    win_reason: Optional[str] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Marquer une opportunite comme gagnee."""
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.win_opportunity(opportunity_id, win_reason)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunite non trouvee")
    return opportunity


@router.post("/opportunities/{opportunity_id}/lose", response_model=OpportunityResponse)
async def lose_opportunity(
    opportunity_id: UUID,
    loss_reason: Optional[str] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Marquer une opportunite comme perdue."""
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.lose_opportunity(opportunity_id, loss_reason)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunite non trouvee")
    return opportunity


# =============================================================================
# ENDPOINTS DOCUMENTS COMMERCIAUX
# =============================================================================

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer un document commercial (devis, commande, facture)."""
    service = get_commercial_service(db, context.tenant_id)

    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")

    return service.create_document(data, context.user_id)


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les documents commerciaux."""
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_documents(
        doc_type=type,
        status=status,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        search=None,
        page=page,
        page_size=page_size
    )
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@router.get("/documents/export")
async def export_documents(
    type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Exporter les documents au format CSV."""
    service = get_commercial_service(db, context.tenant_id)
    csv_content = service.export_documents_csv(type, status, date_from, date_to)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=documents_{date.today().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer un document."""
    service = get_commercial_service(db, context.tenant_id)
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouve")
    return document


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre a jour un document."""
    service = get_commercial_service(db, context.tenant_id)
    document = service.update_document(document_id, data)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouve ou non modifiable")
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer un document (uniquement si DRAFT)."""
    service = get_commercial_service(db, context.tenant_id)
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Document non trouve ou non supprimable (seuls les brouillons peuvent etre supprimes)"
        )


@router.post("/documents/{document_id}/validate", response_model=DocumentResponse)
async def validate_document(
    document_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Valider un document."""
    service = get_commercial_service(db, context.tenant_id)
    document = service.validate_document(document_id, context.user_id)
    if not document:
        raise HTTPException(status_code=400, detail="Document non trouve ou deja valide")
    return document


@router.post("/documents/{document_id}/send", response_model=DocumentResponse)
async def send_document(
    document_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Marquer un document comme envoye."""
    service = get_commercial_service(db, context.tenant_id)
    document = service.send_document(document_id)
    if not document:
        raise HTTPException(status_code=400, detail="Document non trouve ou non envoyable")
    return document


@router.post("/quotes/{quote_id}/convert", response_model=DocumentResponse)
async def convert_quote_to_order(
    quote_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Convertir un devis en commande."""
    service = get_commercial_service(db, context.tenant_id)
    order = service.convert_quote_to_order(quote_id, context.user_id)
    if not order:
        raise HTTPException(status_code=400, detail="Devis non trouve ou non convertible")
    return order


@router.post("/orders/{order_id}/invoice", response_model=DocumentResponse)
async def create_invoice_from_order(
    order_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer une facture a partir d'une commande."""
    service = get_commercial_service(db, context.tenant_id)
    invoice = service.create_invoice_from_order(order_id, context.user_id)
    if not invoice:
        raise HTTPException(status_code=400, detail="Commande non trouvee ou non facturable")
    return invoice


@router.post("/orders/{order_id}/affaire")
async def create_affaire_from_order(
    order_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer une affaire (projet) a partir d'une commande."""
    service = get_commercial_service(db, context.tenant_id)
    document = service.get_document(order_id)
    if not document or document.document_type != DocumentType.ORDER:
        raise HTTPException(status_code=404, detail="Commande non trouvee")

    from app.modules.projects.service import ProjectsService
    from app.modules.projects.schemas import ProjectCreate

    projects_service = ProjectsService(db, context.tenant_id)
    project_data = ProjectCreate(
        code=f"AFF-{document.number}",
        name=f"Affaire - {document.customer_name or 'Client'}",
        description=f"Affaire creee depuis la commande {document.number}",
        client_id=document.customer_id,
        budget=float(document.total_ttc) if document.total_ttc else None,
        status="ACTIVE"
    )
    project = projects_service.create_project(project_data, context.user_id)

    return {"id": str(project.id), "reference": project.code}


@router.post("/documents/{document_id}/lines", response_model=DocumentLineResponse, status_code=status.HTTP_201_CREATED)
async def add_document_line(
    document_id: UUID,
    data: DocumentLineCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Ajouter une ligne a un document."""
    service = get_commercial_service(db, context.tenant_id)
    line = service.add_document_line(document_id, data)
    if not line:
        raise HTTPException(status_code=400, detail="Document non trouve ou non modifiable")
    return line


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_line(
    line_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer une ligne de document."""
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_document_line(line_id):
        raise HTTPException(status_code=400, detail="Ligne non trouvee ou non supprimable")


# =============================================================================
# ENDPOINTS PAIEMENTS
# =============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Enregistrer un paiement sur une facture."""
    service = get_commercial_service(db, context.tenant_id)
    payment = service.create_payment(data, context.user_id)
    if not payment:
        raise HTTPException(status_code=400, detail="Facture non trouvee")
    return payment


@router.get("/documents/{document_id}/payments", response_model=List[PaymentResponse])
async def list_payments(
    document_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les paiements d'un document."""
    service = get_commercial_service(db, context.tenant_id)
    return service.list_payments(document_id)


# =============================================================================
# ENDPOINTS ACTIVITES
# =============================================================================

@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    data: ActivityCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer une activite (appel, email, reunion, etc.)."""
    service = get_commercial_service(db, context.tenant_id)

    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")

    return service.create_activity(data, context.user_id)


@router.get("/activities", response_model=List[ActivityResponse])
async def list_activities(
    customer_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    is_completed: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les activites."""
    service = get_commercial_service(db, context.tenant_id)
    return service.list_activities(customer_id, opportunity_id, assigned_to, is_completed, limit)


@router.post("/activities/{activity_id}/complete", response_model=ActivityResponse)
async def complete_activity(
    activity_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Marquer une activite comme terminee."""
    service = get_commercial_service(db, context.tenant_id)
    activity = service.complete_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activite non trouvee")
    return activity


# =============================================================================
# ENDPOINTS PIPELINE
# =============================================================================

@router.post("/pipeline/stages", response_model=PipelineStageResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline_stage(
    data: PipelineStageCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer une etape du pipeline."""
    service = get_commercial_service(db, context.tenant_id)
    return service.create_pipeline_stage(data)


@router.get("/pipeline/stages", response_model=List[PipelineStageResponse])
async def list_pipeline_stages(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les etapes du pipeline."""
    service = get_commercial_service(db, context.tenant_id)
    return service.list_pipeline_stages()


@router.get("/pipeline/stats", response_model=PipelineStats)
async def get_pipeline_stats(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques du pipeline."""
    service = get_commercial_service(db, context.tenant_id)
    return service.get_pipeline_stats()


# =============================================================================
# ENDPOINTS PRODUITS
# =============================================================================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Creer un produit ou service."""
    service = get_commercial_service(db, context.tenant_id)

    existing = service.get_product(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code produit deja utilise")

    return service.create_product(data)


@router.get("/products", response_model=ProductList)
async def list_products(
    category: Optional[str] = None,
    is_service: Optional[bool] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les produits."""
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_products(category, is_service, is_active, search, page, page_size)
    return ProductList(items=items, total=total, page=page, page_size=page_size)


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recuperer un produit."""
    service = get_commercial_service(db, context.tenant_id)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouve")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre a jour un produit."""
    service = get_commercial_service(db, context.tenant_id)
    product = service.update_product(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouve")
    return product


# =============================================================================
# ENDPOINTS DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=SalesDashboard)
async def get_dashboard(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Obtenir le dashboard commercial."""
    service = get_commercial_service(db, context.tenant_id)
    return service.get_dashboard()


# =============================================================================
# ENDPOINTS EXPORT CSV
# =============================================================================

@router.get("/export/customers")
async def export_customers_csv(
    type: Optional[CustomerType] = None,
    is_active: Optional[bool] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Exporter les clients au format CSV."""
    service = get_commercial_service(db, context.tenant_id)
    csv_content = service.export_customers_csv(type, is_active)

    filename = f"clients_export_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Tenant-ID": context.tenant_id
        }
    )


@router.get("/export/contacts")
async def export_contacts_csv(
    customer_id: Optional[UUID] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Exporter les contacts au format CSV."""
    service = get_commercial_service(db, context.tenant_id)
    csv_content = service.export_contacts_csv(customer_id)

    filename = f"contacts_export_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Tenant-ID": context.tenant_id
        }
    )


@router.get("/export/opportunities")
async def export_opportunities_csv(
    status: Optional[OpportunityStatus] = None,
    customer_id: Optional[UUID] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Exporter les opportunites au format CSV."""
    service = get_commercial_service(db, context.tenant_id)
    csv_content = service.export_opportunities_csv(status, customer_id)

    filename = f"opportunites_export_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Tenant-ID": context.tenant_id
        }
    )
