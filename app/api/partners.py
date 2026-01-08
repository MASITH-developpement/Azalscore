"""
AZALS API - Partners (Alias vers Module Commercial)
====================================================

Routes pour les partenaires commerciaux (clients, fournisseurs, contacts).
Ces routes sont des alias vers le module commercial M1.

Frontend: /v1/partners/*
Backend: Module Commercial (M1)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user

# Réutiliser les schémas et services du module commercial
from app.modules.commercial.models import CustomerType
from app.modules.commercial.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerList,
    ContactCreate, ContactUpdate, ContactResponse,
)
from app.modules.commercial.service import get_commercial_service

router = APIRouter(prefix="/partners", tags=["Partners - Clients & Fournisseurs"])


# ============================================================================
# ENDPOINTS CLIENTS
# ============================================================================

@router.get("/clients", response_model=CustomerList)
async def list_clients(
    type: Optional[CustomerType] = None,
    assigned_to: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les clients avec filtres."""
    service = get_commercial_service(db, current_user["tenant_id"])
    items, total = service.list_customers(type, assigned_to, is_active, search, page, page_size)
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/clients/{client_id}", response_model=CustomerResponse)
async def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un client."""
    service = get_commercial_service(db, current_user["tenant_id"])
    customer = service.get_customer(client_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.post("/clients", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau client."""
    service = get_commercial_service(db, current_user["tenant_id"])

    # Vérifier unicité du code
    existing = service.get_customer_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code client déjà utilisé")

    return service.create_customer(data, current_user["user_id"])


@router.put("/clients/{client_id}", response_model=CustomerResponse)
async def update_client(
    client_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un client."""
    service = get_commercial_service(db, current_user["tenant_id"])
    customer = service.update_customer(client_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un client."""
    service = get_commercial_service(db, current_user["tenant_id"])
    if not service.delete_customer(client_id):
        raise HTTPException(status_code=404, detail="Client non trouvé")


# ============================================================================
# ENDPOINTS FOURNISSEURS (Suppliers)
# ============================================================================

@router.get("/suppliers", response_model=CustomerList)
async def list_suppliers(
    assigned_to: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister les fournisseurs avec filtres."""
    service = get_commercial_service(db, current_user["tenant_id"])
    # Filtrer par type SUPPLIER
    items, total = service.list_customers(
        CustomerType.SUPPLIER, assigned_to, is_active, search, page, page_size
    )
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.get("/suppliers/{supplier_id}", response_model=CustomerResponse)
async def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un fournisseur."""
    service = get_commercial_service(db, current_user["tenant_id"])
    supplier = service.get_customer(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return supplier


@router.post("/suppliers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau fournisseur."""
    service = get_commercial_service(db, current_user["tenant_id"])

    # Forcer le type SUPPLIER
    data_dict = data.model_dump()
    data_dict["customer_type"] = CustomerType.SUPPLIER
    data = CustomerCreate(**data_dict)

    # Vérifier unicité du code
    existing = service.get_customer_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Code fournisseur déjà utilisé")

    return service.create_customer(data, current_user["user_id"])


@router.put("/suppliers/{supplier_id}", response_model=CustomerResponse)
async def update_supplier(
    supplier_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un fournisseur."""
    service = get_commercial_service(db, current_user["tenant_id"])
    supplier = service.update_customer(supplier_id, data)
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return supplier


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un fournisseur."""
    service = get_commercial_service(db, current_user["tenant_id"])
    if not service.delete_customer(supplier_id):
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")


# ============================================================================
# ENDPOINTS CONTACTS
# ============================================================================

@router.get("/contacts", response_model=List[ContactResponse])
async def list_all_contacts(
    customer_id: Optional[UUID] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lister tous les contacts."""
    service = get_commercial_service(db, current_user["tenant_id"])
    if customer_id:
        return service.list_contacts(customer_id)
    # TODO: Implémenter une méthode list_all_contacts dans le service
    return []


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un contact."""
    service = get_commercial_service(db, current_user["tenant_id"])
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return contact


@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Créer un contact pour un client/fournisseur."""
    service = get_commercial_service(db, current_user["tenant_id"])

    # Vérifier que le client/fournisseur existe
    customer = service.get_customer(data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client/fournisseur non trouvé")

    return service.create_contact(data)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un contact."""
    service = get_commercial_service(db, current_user["tenant_id"])
    contact = service.update_contact(contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un contact."""
    service = get_commercial_service(db, current_user["tenant_id"])
    if not service.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouvé")
