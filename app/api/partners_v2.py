"""
AZALS API - Partners v2 (CORE SaaS)
====================================

Routes pour les partenaires commerciaux (clients, fournisseurs, contacts).
Version CORE SaaS.

MIGRATION CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user()
- SaaSContext fournit tenant_id + user_id directement
- Audit automatique via CoreAuthMiddleware
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.modules.commercial.models import CustomerType
from app.modules.commercial.schemas import (
    ContactCreate,
    ContactList,
    ContactResponse,
    ContactUpdate,
    CustomerCreate,
    CustomerCreateAuto,
    CustomerList,
    CustomerResponse,
    CustomerUpdate,
)
from app.modules.commercial.service import get_commercial_service

router = APIRouter(prefix="/v2/partners", tags=["Partners v2 - CORE SaaS"])


# ============================================================================
# ENDPOINTS CLIENTS
# ============================================================================

@router.get("/clients", response_model=CustomerList)
async def list_clients(
    type: CustomerType | None = None,
    assigned_to: UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les clients avec filtres (exclut les fournisseurs).

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_customers_excluding_suppliers(
        type, assigned_to, is_active, search, page, page_size
    )
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/clients/{client_id}", response_model=CustomerResponse)
async def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Recuperer un client."""
    service = get_commercial_service(db, context.tenant_id)
    customer = service.get_customer(client_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")
    return customer


@router.post("/clients", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: CustomerCreateAuto,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Creer un nouveau client avec code auto-genere.

    CORE SaaS: Utilise context.user_id pour le created_by.
    """
    service = get_commercial_service(db, context.tenant_id)

    # Auto-generer le code si non fourni
    if not data.code:
        auto_code = service.get_next_customer_code()
    else:
        auto_code = data.code
        # Verifier unicite du code fourni
        existing = service.get_customer_by_code(auto_code)
        if existing:
            raise HTTPException(status_code=400, detail="Code client deja utilise")

    # Creer les donnees avec le code
    data_dict = data.model_dump(exclude_unset=False)
    data_dict["code"] = auto_code
    customer_data = CustomerCreate(**data_dict)

    return service.create_customer(customer_data, context.user_id)


@router.put("/clients/{client_id}", response_model=CustomerResponse)
async def update_client(
    client_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre a jour un client."""
    service = get_commercial_service(db, context.tenant_id)
    customer = service.update_customer(client_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")
    return customer


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un client."""
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_customer(client_id):
        raise HTTPException(status_code=404, detail="Client non trouve")


# ============================================================================
# ENDPOINTS FOURNISSEURS (Suppliers)
# ============================================================================

@router.get("/suppliers", response_model=CustomerList)
async def list_suppliers(
    assigned_to: UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=500),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister les fournisseurs avec filtres.

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    service = get_commercial_service(db, context.tenant_id)
    items, total = service.list_customers(
        CustomerType.SUPPLIER, assigned_to, is_active, search, page, page_size
    )
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/suppliers/{supplier_id}", response_model=CustomerResponse)
async def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Recuperer un fournisseur."""
    service = get_commercial_service(db, context.tenant_id)
    supplier = service.get_customer(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouve")
    return supplier


@router.post("/suppliers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Creer un nouveau fournisseur.

    CORE SaaS: Utilise context.user_id pour le created_by.
    """
    service = get_commercial_service(db, context.tenant_id)

    # Forcer le type SUPPLIER
    data_dict = data.model_dump()
    data_dict["customer_type"] = CustomerType.SUPPLIER
    data = CustomerCreate(**data_dict)

    # Verifier unicite du code
    existing = service.get_customer_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code fournisseur deja utilise")

    return service.create_customer(data, context.user_id)


@router.put("/suppliers/{supplier_id}", response_model=CustomerResponse)
async def update_supplier(
    supplier_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Mettre a jour un fournisseur."""
    service = get_commercial_service(db, context.tenant_id)
    supplier = service.update_customer(supplier_id, data)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouve")
    return supplier


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un fournisseur."""
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_customer(supplier_id):
        raise HTTPException(status_code=404, detail="Fournisseur non trouve")


# ============================================================================
# ENDPOINTS CONTACTS
# ============================================================================

@router.get("/contacts", response_model=ContactList)
async def list_all_contacts(
    customer_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Lister tous les contacts.

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    service = get_commercial_service(db, context.tenant_id)
    if customer_id:
        contacts = service.list_contacts(customer_id)
        return ContactList(items=contacts, total=len(contacts), page=page, page_size=page_size)
    items, total = service.list_all_contacts(search=search, page=page, page_size=page_size)
    return ContactList(items=items, total=total, page=page, page_size=page_size)


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Recuperer un contact."""
    service = get_commercial_service(db, context.tenant_id)
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouve")
    return contact


@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Creer un contact pour un client/fournisseur.

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    service = get_commercial_service(db, context.tenant_id)

    # Verifier que le client/fournisseur existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client/fournisseur non trouve")

    return service.create_contact(data)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
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
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """Supprimer un contact."""
    service = get_commercial_service(db, context.tenant_id)
    if not service.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouve")
