"""
AZALS - Contacts Router (CRUDRouter v3)
======================================

Router pour la gestion unifiée des contacts (Clients et Fournisseurs).
"""
from __future__ import annotations


from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from app.modules.contacts import (
    EntityType,
    RelationType,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactList,
    ContactLookupList,
    ContactPersonCreate,
    ContactPersonUpdate,
    ContactPersonResponse,
    ContactAddressCreate,
    ContactAddressUpdate,
    ContactAddressResponse,
    ContactsService,
)

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/contacts", tags=["Contacts"])


def get_service(context: SaaSContext, db: Session) -> ContactsService:
    """Factory pour le service contacts."""
    return ContactsService(db, context.tenant_id)


# =============================================================================
# ENDPOINTS CONTACTS
# =============================================================================

@router.get("/status")
async def get_module_status():
    """Statut du module Contacts."""
    return {
        "module": "contacts",
        "version": "v3",
        "status": "active"
    }


@router.get("/lookup", response_model=ContactLookupList)
async def lookup_contacts(
    relation_type: Optional[RelationType] = Query(None, description="Filtrer par type de relation (CLIENT/SUPPLIER)"),
    search: Optional[str] = Query(None, description="Recherche textuelle"),
    limit: int = Query(50, ge=1, le=200),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """
    Recherche rapide pour les sélecteurs/autocomplete.

    Retourne une liste simplifiée (id, code, name) pour les listes déroulantes.
    """
    service = get_service(context, db)
    items = service.lookup_contacts(
        relation_type=relation_type,
        search=search,
        limit=limit
    )
    return ContactLookupList(items=items, total=len(items))


@router.get("", response_model=ContactList)
async def list_contacts(
    entity_type: Optional[EntityType] = Query(None, description="Filtrer par type d'entité"),
    relation_type: Optional[RelationType] = Query(None, description="Filtrer par type de relation"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    search: Optional[str] = Query(None, description="Recherche textuelle"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """
    Lister les contacts avec filtres et pagination.

    - entity_type: INDIVIDUAL ou COMPANY
    - relation_type: CUSTOMER ou SUPPLIER
    - search: recherche sur nom, email, code, tax_id
    """
    service = get_service(context, db)
    items, total = service.list_contacts(
        entity_type=entity_type,
        relation_type=relation_type,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size
    )

    # Calculer le nombre de pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ContactList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """
    Créer un nouveau contact avec code auto-généré.

    Le code est généré automatiquement au format CONT-YYYY-XXXX.
    Si un code est fourni, il sera utilisé (après vérification d'unicité).
    """
    service = get_service(context, db)

    # Vérifier unicité du code si fourni
    if data.code:
        existing = service.get_contact_by_code(data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le code '{data.code}' est déjà utilisé"
            )

    contact = service.create_contact(data, context.user_id)
    return contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Récupérer un contact par son ID avec ses personnes et adresses."""
    service = get_service(context, db)
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )
    return contact


@router.get("/code/{code}", response_model=ContactResponse)
async def get_contact_by_code(
    code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Récupérer un contact par son code."""
    service = get_service(context, db)
    contact = service.get_contact_by_code(code)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact avec le code '{code}' non trouvé"
        )
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Mettre à jour un contact."""
    service = get_service(context, db)
    contact = service.update_contact(contact_id, data)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    permanent: bool = Query(False, description="Suppression définitive (sinon soft delete)"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """
    Supprimer un contact.

    Par défaut, effectue un soft delete (is_active=False, deleted_at set).
    Avec permanent=True, supprime définitivement.
    """
    service = get_service(context, db)
    if permanent:
        success = service.hard_delete_contact(contact_id)
    else:
        success = service.delete_contact(contact_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )


# =============================================================================
# ENDPOINTS PERSONNES DE CONTACT
# =============================================================================

@router.post("/{contact_id}/persons", response_model=ContactPersonResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_person(
    contact_id: UUID,
    data: ContactPersonCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Ajouter une personne de contact."""
    service = get_service(context, db)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    person = service.create_person(contact_id, data)
    return person


@router.get("/{contact_id}/persons", response_model=List[ContactPersonResponse])
async def list_contact_persons(
    contact_id: UUID,
    is_active: Optional[bool] = Query(None),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Lister les personnes de contact."""
    service = get_service(context, db)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    return service.list_persons(contact_id, is_active=is_active)


@router.put("/{contact_id}/persons/{person_id}", response_model=ContactPersonResponse)
async def update_contact_person(
    contact_id: UUID,
    person_id: UUID,
    data: ContactPersonUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Mettre à jour une personne de contact."""
    service = get_service(context, db)

    # Vérifier que la personne appartient bien à ce contact
    existing = service.get_person(person_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personne de contact non trouvée"
        )

    person = service.update_person(person_id, data)
    return person


@router.delete("/{contact_id}/persons/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact_person(
    contact_id: UUID,
    person_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Supprimer une personne de contact."""
    service = get_service(context, db)

    # Vérifier que la personne appartient bien à ce contact
    existing = service.get_person(person_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personne de contact non trouvée"
        )

    service.delete_person(person_id)


# =============================================================================
# ENDPOINTS ADRESSES
# =============================================================================

@router.post("/{contact_id}/addresses", response_model=ContactAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_address(
    contact_id: UUID,
    data: ContactAddressCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Ajouter une adresse au contact."""
    service = get_service(context, db)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    address = service.create_address(contact_id, data)
    return address


@router.get("/{contact_id}/addresses", response_model=List[ContactAddressResponse])
async def list_contact_addresses(
    contact_id: UUID,
    is_active: Optional[bool] = Query(None),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Lister les adresses d'un contact."""
    service = get_service(context, db)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    return service.list_addresses(contact_id, is_active=is_active)


@router.put("/{contact_id}/addresses/{address_id}", response_model=ContactAddressResponse)
async def update_contact_address(
    contact_id: UUID,
    address_id: UUID,
    data: ContactAddressUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Mettre à jour une adresse de contact."""
    service = get_service(context, db)

    # Vérifier que l'adresse appartient bien à ce contact
    existing = service.get_address(address_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adresse non trouvée"
        )

    address = service.update_address(address_id, data)
    return address


@router.delete("/{contact_id}/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact_address(
    contact_id: UUID,
    address_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Supprimer une adresse de contact."""
    service = get_service(context, db)

    # Vérifier que l'adresse appartient bien à ce contact
    existing = service.get_address(address_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adresse non trouvée"
        )

    service.delete_address(address_id)


# =============================================================================
# ENDPOINTS STATISTIQUES
# =============================================================================

@router.get("/{contact_id}/stats")
async def get_contact_stats(
    contact_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """
    Récupérer les statistiques d'un contact.

    Inclut:
    - Total commandes client
    - Total CA client
    - Total achats fournisseur
    - Dernière activité
    """
    service = get_service(context, db)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    return {
        "contact_id": contact_id,
        "is_customer": contact.is_customer,
        "is_supplier": contact.is_supplier,
        "customer_stats": {
            "total_revenue": float(contact.customer_total_revenue or 0),
            "order_count": contact.customer_order_count or 0,
            "last_order_date": contact.customer_last_order_date,
            "first_order_date": contact.customer_first_order_date,
            "health_score": contact.health_score or 100,
            "lead_score": contact.lead_score or 0,
        } if contact.is_customer else None,
        "supplier_stats": {
            "total_purchases": float(contact.supplier_total_purchases or 0),
            "order_count": contact.supplier_order_count or 0,
            "last_order_date": contact.supplier_last_order_date,
        } if contact.is_supplier else None,
    }
