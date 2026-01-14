"""
AZALS MODULE M1 - Router Commercial
====================================

API REST pour le CRM et la gestion commerciale.
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.models import User

from .models import CustomerType, OpportunityStatus, DocumentType, DocumentStatus
from .schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerList,
    ContactCreate, ContactUpdate, ContactResponse,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse, OpportunityList,
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentList, DocumentLineCreate, DocumentLineResponse,
    PaymentCreate, PaymentResponse,
    ActivityCreate, ActivityResponse,
    PipelineStageCreate, PipelineStageResponse,
    ProductCreate, ProductUpdate, ProductResponse, ProductList,
    SalesDashboard, PipelineStats
)
from .service import get_commercial_service

router = APIRouter(prefix="/api/v1/commercial", tags=["M1 - Commercial"])


# ============================================================================
# ENDPOINTS CLIENTS
# ============================================================================

@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau client/prospect."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Vérifier unicité du code
    existing = service.get_customer_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code client déjà utilisé")

    return service.create_customer(data, current_user.id)


@router.get("/customers", response_model=CustomerList)
async def list_customers(
    type: Optional[CustomerType] = None,
    assigned_to: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les clients avec filtres."""
    service = get_commercial_service(db, current_user.tenant_id)
    items, total = service.list_customers(type, assigned_to, is_active, search, page, page_size)
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un client."""
    service = get_commercial_service(db, current_user.tenant_id)
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un client."""
    service = get_commercial_service(db, current_user.tenant_id)
    customer = service.update_customer(customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un client."""
    service = get_commercial_service(db, current_user.tenant_id)
    if not service.delete_customer(customer_id):
        raise HTTPException(status_code=404, detail="Client non trouvé")


@router.post("/customers/{customer_id}/convert", response_model=CustomerResponse)
async def convert_prospect(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convertir un prospect en client."""
    service = get_commercial_service(db, current_user.tenant_id)
    customer = service.convert_prospect(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


# ============================================================================
# ENDPOINTS CONTACTS
# ============================================================================

@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un contact pour un client."""
    print(f"[DEBUG] commercial/router create_contact appelé avec data={data}")
    service = get_commercial_service(db, current_user.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    contact = service.create_contact(data)
    print(f"[DEBUG] Contact créé avec succès: {contact.id}")
    return contact


@router.get("/customers/{customer_id}/contacts", response_model=List[ContactResponse])
async def list_contacts(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les contacts d'un client."""
    service = get_commercial_service(db, current_user.tenant_id)
    return service.list_contacts(customer_id)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un contact."""
    service = get_commercial_service(db, current_user.tenant_id)
    contact = service.update_contact(contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un contact."""
    service = get_commercial_service(db, current_user.tenant_id)
    if not service.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouvé")


# ============================================================================
# ENDPOINTS OPPORTUNITÉS
# ============================================================================

@router.post("/opportunities", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une opportunité."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_opportunity(data, current_user.id)


@router.get("/opportunities", response_model=OpportunityList)
async def list_opportunities(
    status: Optional[OpportunityStatus] = None,
    customer_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les opportunités."""
    service = get_commercial_service(db, current_user.tenant_id)
    items, total = service.list_opportunities(status, customer_id, assigned_to, page, page_size)
    return OpportunityList(items=items, total=total, page=page, page_size=page_size)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une opportunité."""
    service = get_commercial_service(db, current_user.tenant_id)
    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: UUID,
    data: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une opportunité."""
    service = get_commercial_service(db, current_user.tenant_id)
    opportunity = service.update_opportunity(opportunity_id, data)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


@router.post("/opportunities/{opportunity_id}/win", response_model=OpportunityResponse)
async def win_opportunity(
    opportunity_id: UUID,
    win_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marquer une opportunité comme gagnée."""
    service = get_commercial_service(db, current_user.tenant_id)
    opportunity = service.win_opportunity(opportunity_id, win_reason)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


@router.post("/opportunities/{opportunity_id}/lose", response_model=OpportunityResponse)
async def lose_opportunity(
    opportunity_id: UUID,
    loss_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marquer une opportunité comme perdue."""
    service = get_commercial_service(db, current_user.tenant_id)
    opportunity = service.lose_opportunity(opportunity_id, loss_reason)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


# ============================================================================
# ENDPOINTS DOCUMENTS COMMERCIAUX
# ============================================================================

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un document commercial (devis, commande, facture)."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_document(data, current_user.id)


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les documents commerciaux."""
    service = get_commercial_service(db, current_user.tenant_id)
    items, total = service.list_documents(type, status, customer_id, date_from, date_to, page, page_size)
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un document."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return document


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un document."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.update_document(document_id, data)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé ou non modifiable")
    return document


@router.post("/documents/{document_id}/validate", response_model=DocumentResponse)
async def validate_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Valider un document."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.validate_document(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=400, detail="Document non trouvé ou déjà validé")
    return document


@router.post("/documents/{document_id}/send", response_model=DocumentResponse)
async def send_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marquer un document comme envoyé."""
    service = get_commercial_service(db, current_user.tenant_id)
    document = service.send_document(document_id)
    if not document:
        raise HTTPException(status_code=400, detail="Document non trouvé ou non envoyable")
    return document


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


@router.post("/documents/{document_id}/lines", response_model=DocumentLineResponse, status_code=status.HTTP_201_CREATED)
async def add_document_line(
    document_id: UUID,
    data: DocumentLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une ligne à un document."""
    service = get_commercial_service(db, current_user.tenant_id)
    line = service.add_document_line(document_id, data)
    if not line:
        raise HTTPException(status_code=400, detail="Document non trouvé ou non modifiable")
    return line


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_line(
    line_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une ligne de document."""
    service = get_commercial_service(db, current_user.tenant_id)
    if not service.delete_document_line(line_id):
        raise HTTPException(status_code=400, detail="Ligne non trouvée ou non supprimable")


# ============================================================================
# ENDPOINTS PAIEMENTS
# ============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enregistrer un paiement sur une facture."""
    service = get_commercial_service(db, current_user.tenant_id)
    payment = service.create_payment(data, current_user.id)
    if not payment:
        raise HTTPException(status_code=400, detail="Facture non trouvée")
    return payment


@router.get("/documents/{document_id}/payments", response_model=List[PaymentResponse])
async def list_payments(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les paiements d'un document."""
    service = get_commercial_service(db, current_user.tenant_id)
    return service.list_payments(document_id)


# ============================================================================
# ENDPOINTS ACTIVITÉS
# ============================================================================

@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une activité (appel, email, réunion, etc.)."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_activity(data, current_user.id)


@router.get("/activities", response_model=List[ActivityResponse])
async def list_activities(
    customer_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    is_completed: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les activités."""
    service = get_commercial_service(db, current_user.tenant_id)
    return service.list_activities(customer_id, opportunity_id, assigned_to, is_completed, limit)


@router.post("/activities/{activity_id}/complete", response_model=ActivityResponse)
async def complete_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marquer une activité comme terminée."""
    service = get_commercial_service(db, current_user.tenant_id)
    activity = service.complete_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    return activity


# ============================================================================
# ENDPOINTS PIPELINE
# ============================================================================

@router.post("/pipeline/stages", response_model=PipelineStageResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline_stage(
    data: PipelineStageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une étape du pipeline."""
    service = get_commercial_service(db, current_user.tenant_id)
    return service.create_pipeline_stage(data)


@router.get("/pipeline/stages", response_model=List[PipelineStageResponse])
async def list_pipeline_stages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les étapes du pipeline."""
    service = get_commercial_service(db, current_user.tenant_id)
    return service.list_pipeline_stages()


@router.get("/pipeline/stats", response_model=PipelineStats)
async def get_pipeline_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir les statistiques du pipeline."""
    service = get_commercial_service(db, current_user.tenant_id)
    return service.get_pipeline_stats()


# ============================================================================
# ENDPOINTS PRODUITS
# ============================================================================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un produit ou service."""
    service = get_commercial_service(db, current_user.tenant_id)

    # Vérifier unicité du code
    existing = service.get_product(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code produit déjà utilisé")

    return service.create_product(data)


@router.get("/products", response_model=ProductList)
async def list_products(
    category: Optional[str] = None,
    is_service: Optional[bool] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les produits."""
    service = get_commercial_service(db, current_user.tenant_id)
    items, total = service.list_products(category, is_service, is_active, search, page, page_size)
    return ProductList(items=items, total=total, page=page, page_size=page_size)


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un produit."""
    service = get_commercial_service(db, current_user.tenant_id)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un produit."""
    service = get_commercial_service(db, current_user.tenant_id)
    product = service.update_product(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


# ============================================================================
# ENDPOINTS DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=SalesDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir le dashboard commercial."""
    service = get_commercial_service(db, current_user.tenant_id)
    return service.get_dashboard()


# ============================================================================
# ENDPOINTS EXPORT CSV (CRM T0)
# ============================================================================

from fastapi.responses import StreamingResponse
from datetime import datetime as dt

@router.get("/export/customers")
async def export_customers_csv(
    type: Optional[CustomerType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exporter les clients au format CSV.
    SÉCURITÉ: Les données sont strictement filtrées par tenant_id.
    """
    service = get_commercial_service(db, current_user.tenant_id)
    csv_content = service.export_customers_csv(type, is_active)

    filename = f"clients_export_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Tenant-ID": current_user.tenant_id
        }
    )


@router.get("/export/contacts")
async def export_contacts_csv(
    customer_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exporter les contacts au format CSV.
    SÉCURITÉ: Les données sont strictement filtrées par tenant_id.
    """
    service = get_commercial_service(db, current_user.tenant_id)
    csv_content = service.export_contacts_csv(customer_id)

    filename = f"contacts_export_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Tenant-ID": current_user.tenant_id
        }
    )


@router.get("/export/opportunities")
async def export_opportunities_csv(
    status: Optional[OpportunityStatus] = None,
    customer_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exporter les opportunités au format CSV.
    SÉCURITÉ: Les données sont strictement filtrées par tenant_id.
    """
    service = get_commercial_service(db, current_user.tenant_id)
    csv_content = service.export_opportunities_csv(status, customer_id)

    filename = f"opportunites_export_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Tenant-ID": current_user.tenant_id
        }
    )
