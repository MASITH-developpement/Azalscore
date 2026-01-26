"""
AZALS MODULE M1 - Router Commercial (MIGRÉ CORE SaaS)
======================================================

API REST pour le CRM et la gestion commerciale.

✅ MIGRATION 100% COMPLÈTE vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user()
- 45/45 endpoints protégés migrés vers pattern CORE ✅
- Service adapté pour utiliser context.tenant_id

ENDPOINTS MIGRÉS (45):
- Customers (6): CRUD + convert
- Contacts (4): CRUD
- Opportunities (6): CRUD + win/lose
- Documents (10): CRUD + validate/send/convert/invoice/affaire + export
- Lines (2): add + delete
- Payments (2): create + list
- Activities (3): create + list + complete
- Pipeline (3): create stage + list stages + stats
- Products (4): CRUD
- Dashboard (1): get dashboard
- Exports (3): customers + contacts + opportunities
"""

from datetime import date, datetime as dt
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

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
from .service import get_commercial_service

router = APIRouter(prefix="/v2/commercial", tags=["M1 - Commercial"])


# ============================================================================
# DÉPENDANCES
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> object:
    """
    Dépendance pour obtenir le service Commercial (endpoints PROTÉGÉS).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation tenant
    """
    return get_commercial_service(db, context.tenant_id)


# ============================================================================
# ENDPOINTS CLIENTS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un nouveau client/prospect.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (created_by)
    """
    service = get_commercial_service(db, context.tenant_id)

    # Vérifier unicité du code
    existing = service.get_customer_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code client déjà utilisé")

    return service.create_customer(data, context.user_id)


@router.get("/customers", response_model=CustomerList)
async def list_customers(
    type: CustomerType | None = None,
    assigned_to: UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les clients avec filtres.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique via context.tenant_id
    """
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_customers(type, assigned_to, is_active, search, page, page_size)
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un client.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un client.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    customer = service.update_customer(customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Supprimer un client.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_customer(customer_id):
        raise HTTPException(status_code=404, detail="Client non trouvé")


@router.post("/customers/{customer_id}/convert", response_model=CustomerResponse)
async def convert_prospect(
    customer_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Convertir un prospect en client.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    customer = service.convert_prospect(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


# ============================================================================
# ENDPOINTS CONTACTS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un contact pour un client.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    contact = service.create_contact(data)
    return contact


@router.get("/customers/{customer_id}/contacts", response_model=list[ContactResponse])
async def list_contacts(
    customer_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les contacts d'un client.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    return service.list_contacts(customer_id)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un contact.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    contact = service.update_contact(contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Supprimer un contact.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouvé")


# ============================================================================
# ENDPOINTS OPPORTUNITÉS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/opportunities", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: OpportunityCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une opportunité.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (created_by)
    """
    service = get_commercial_service(db, context.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_opportunity(data, context.user_id)


@router.get("/opportunities", response_model=OpportunityList)
async def list_opportunities(
    status: OpportunityStatus | None = None,
    customer_id: UUID | None = None,
    assigned_to: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les opportunités.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_opportunities(status, customer_id, assigned_to, page, page_size)
    return OpportunityList(items=items, total=total, page=page, page_size=page_size)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer une opportunité.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: UUID,
    data: OpportunityUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour une opportunité.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.update_opportunity(opportunity_id, data)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


@router.post("/opportunities/{opportunity_id}/win", response_model=OpportunityResponse)
async def win_opportunity(
    opportunity_id: UUID,
    win_reason: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Marquer une opportunité comme gagnée.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.win_opportunity(opportunity_id, win_reason)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


@router.post("/opportunities/{opportunity_id}/lose", response_model=OpportunityResponse)
async def lose_opportunity(
    opportunity_id: UUID,
    loss_reason: str | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Marquer une opportunité comme perdue.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    opportunity = service.lose_opportunity(opportunity_id, loss_reason)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunité non trouvée")
    return opportunity


# ============================================================================
# ENDPOINTS DOCUMENTS COMMERCIAUX (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un document commercial (devis, commande, facture).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (created_by)
    """
    service = get_commercial_service(db, context.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_document(data, context.user_id)


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    type: DocumentType | None = None,
    status: DocumentStatus | None = None,
    customer_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les documents commerciaux.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_documents(type, status, customer_id, date_from, date_to, page, page_size)
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@router.get("/documents/export")
async def export_documents(
    type: DocumentType | None = None,
    status: DocumentStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Exporter les documents au format CSV.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
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
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un document.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return document


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un document.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    document = service.update_document(document_id, data)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé ou non modifiable")
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Supprimer un document (uniquement si DRAFT).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=400, detail="Document non trouvé ou non supprimable (seuls les brouillons peuvent être supprimés)")


@router.post("/documents/{document_id}/validate", response_model=DocumentResponse)
async def validate_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Valider un document.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (validated_by)
    """
    service = get_commercial_service(db, context.tenant_id)
    document = service.validate_document(document_id, context.user_id)
    if not document:
        raise HTTPException(status_code=400, detail="Document non trouvé ou déjà validé")
    return document


@router.post("/documents/{document_id}/send", response_model=DocumentResponse)
async def send_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Marquer un document comme envoyé.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    document = service.send_document(document_id)
    if not document:
        raise HTTPException(status_code=400, detail="Document non trouvé ou non envoyable")
    return document


@router.post("/quotes/{quote_id}/convert", response_model=DocumentResponse)
async def convert_quote_to_order(
    quote_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Convertir un devis en commande.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (converted_by)
    """
    service = get_commercial_service(db, context.tenant_id)
    order = service.convert_quote_to_order(quote_id, context.user_id)
    if not order:
        raise HTTPException(status_code=400, detail="Devis non trouvé ou non convertible")
    return order


@router.post("/orders/{order_id}/invoice", response_model=DocumentResponse)
async def create_invoice_from_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une facture à partir d'une commande.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (created_by)
    """
    service = get_commercial_service(db, context.tenant_id)
    invoice = service.create_invoice_from_order(order_id, context.user_id)
    if not invoice:
        raise HTTPException(status_code=400, detail="Commande non trouvée ou non facturable")
    return invoice


@router.post("/orders/{order_id}/affaire")
async def create_affaire_from_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une affaire (projet) à partir d'une commande.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (created_by)
    """
    service = get_commercial_service(db, context.tenant_id)
    document = service.get_document(order_id)
    if not document or document.document_type != DocumentType.ORDER:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    # Créer le projet via le module projects
    from app.modules.projects.service import ProjectsService
    from app.modules.projects.schemas import ProjectCreate

    projects_service = ProjectsService(db, context.tenant_id)
    project_data = ProjectCreate(
        code=f"AFF-{document.number}",
        name=f"Affaire - {document.customer_name or 'Client'}",
        description=f"Affaire créée depuis la commande {document.number}",
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
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Ajouter une ligne à un document.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    line = service.add_document_line(document_id, data)
    if not line:
        raise HTTPException(status_code=400, detail="Document non trouvé ou non modifiable")
    return line


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_line(
    line_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Supprimer une ligne de document.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_document_line(line_id):
        raise HTTPException(status_code=400, detail="Ligne non trouvée ou non supprimable")


# ============================================================================
# ENDPOINTS PAIEMENTS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Enregistrer un paiement sur une facture.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (recorded_by)
    """
    service = get_commercial_service(db, context.tenant_id)
    payment = service.create_payment(data, context.user_id)
    if not payment:
        raise HTTPException(status_code=400, detail="Facture non trouvée")
    return payment


@router.get("/documents/{document_id}/payments", response_model=list[PaymentResponse])
async def list_payments(
    document_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les paiements d'un document.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    return service.list_payments(document_id)


# ============================================================================
# ENDPOINTS ACTIVITÉS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    data: ActivityCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une activité (appel, email, réunion, etc.).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    - Utilise context.user_id pour audit (created_by)
    """
    service = get_commercial_service(db, context.tenant_id)

    # Vérifier que le client existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    return service.create_activity(data, context.user_id)


@router.get("/activities", response_model=list[ActivityResponse])
async def list_activities(
    customer_id: UUID | None = None,
    opportunity_id: UUID | None = None,
    assigned_to: UUID | None = None,
    is_completed: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les activités.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    return service.list_activities(customer_id, opportunity_id, assigned_to, is_completed, limit)


@router.post("/activities/{activity_id}/complete", response_model=ActivityResponse)
async def complete_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Marquer une activité comme terminée.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    activity = service.complete_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    return activity


# ============================================================================
# ENDPOINTS PIPELINE (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/pipeline/stages", response_model=PipelineStageResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline_stage(
    data: PipelineStageCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer une étape du pipeline.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    return service.create_pipeline_stage(data)


@router.get("/pipeline/stages", response_model=list[PipelineStageResponse])
async def list_pipeline_stages(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les étapes du pipeline.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    return service.list_pipeline_stages()


@router.get("/pipeline/stats", response_model=PipelineStats)
async def get_pipeline_stats(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Obtenir les statistiques du pipeline.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    return service.get_pipeline_stats()


# ============================================================================
# ENDPOINTS PRODUITS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Créer un produit ou service.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)

    # Vérifier unicité du code
    existing = service.get_product(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code produit déjà utilisé")

    return service.create_product(data)


@router.get("/products", response_model=ProductList)
async def list_products(
    category: str | None = None,
    is_service: bool | None = None,
    is_active: bool | None = True,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les produits.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_products(category, is_service, is_active, search, page, page_size)
    return ProductList(items=items, total=total, page=page, page_size=page_size)


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Récupérer un produit.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Mettre à jour un produit.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation
    """
    service = get_commercial_service(db, context.tenant_id)
    product = service.update_product(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


# ============================================================================
# ENDPOINTS DASHBOARD (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.get("/dashboard", response_model=SalesDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Obtenir le dashboard commercial.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique
    """
    service = get_commercial_service(db, context.tenant_id)
    return service.get_dashboard()


# ============================================================================
# ENDPOINTS EXPORT CSV (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.get("/export/customers")
async def export_customers_csv(
    type: CustomerType | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Exporter les clients au format CSV.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation stricte
    """
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
    customer_id: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Exporter les contacts au format CSV.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation stricte
    """
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
    status: OpportunityStatus | None = None,
    customer_id: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Exporter les opportunités au format CSV.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour isolation stricte
    """
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


# ============================================================================
# MIGRATION COMMERCIAL COMPLÈTE - CORE SaaS
# ============================================================================
#
# TOTAL ENDPOINTS: 45
# - Tous endpoints protégés (MIGRÉS): 45
#
# - Customers (6): create, list, get, update, delete, convert
# - Contacts (4): create, list, update, delete
# - Opportunities (6): create, list, get, update, win, lose
# - Documents (10): create, list, export, get, update, delete, validate, send, convert, invoice, affaire
# - Lines (2): add, delete
# - Payments (2): create, list
# - Activities (3): create, list, complete
# - Pipeline (3): create stage, list stages, stats
# - Products (4): create, list, get, update
# - Dashboard (1): get dashboard
# - Exports (3): customers, contacts, opportunities
#
# ✅ MIGRATION 100% COMPLÈTE (45/45 endpoints protégés migrés)
# ============================================================================
