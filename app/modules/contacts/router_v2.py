"""
AZALS API v2 - Contacts Unifiés
===============================

Routes pour la gestion unifiée des contacts (Clients et Fournisseurs).
Module de sous-programmes réutilisables par tous les autres modules.

Frontend: /v2/contacts/*
Backend: Module Contacts Unifié
"""
from __future__ import annotations


from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

from app.modules.contacts import (
    EntityType,
    RelationType,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactList,
    ContactSummary,
    ContactLookup,
    ContactLookupList,
    ContactPersonCreate,
    ContactPersonUpdate,
    ContactPersonResponse,
    ContactAddressCreate,
    ContactAddressUpdate,
    ContactAddressResponse,
)
from app.modules.contacts.service import ContactsService


router = APIRouter(prefix="/v2/contacts", tags=["Contacts Unifiés v2"])


# ============================================================================
# HELPERS
# ============================================================================

def get_contacts_service(db: Session, tenant_id: str) -> ContactsService:
    """Factory pour le service contacts."""
    return ContactsService(db, tenant_id)


# ============================================================================
# ENDPOINTS CONTACTS (CRUD PRINCIPAL)
# ============================================================================

@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer un nouveau contact avec code auto-généré.

    Le code est généré automatiquement au format CONT-YYYY-XXXX.
    Si un code est fourni, il sera utilisé (après vérification d'unicité).

    Un contact peut être Client, Fournisseur, ou les deux simultanément.
    """
    service = get_contacts_service(db, current_user.tenant_id)

    # Vérifier unicité du code si fourni
    if data.code:
        existing = service.get_contact_by_code(data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le code '{data.code}' est déjà utilisé"
            )

    contact = service.create_contact(data, current_user.id)
    return contact


@router.get("", response_model=ContactList)
async def list_contacts(
    entity_type: Optional[EntityType] = Query(None, description="Filtrer par type d'entité"),
    relation_type: Optional[RelationType] = Query(None, description="Filtrer par type de relation"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    search: Optional[str] = Query(None, description="Recherche textuelle"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lister les contacts avec filtres et pagination.

    - entity_type: INDIVIDUAL ou COMPANY
    - relation_type: CUSTOMER ou SUPPLIER
    - search: recherche sur nom, email, code, tax_id
    """
    service = get_contacts_service(db, current_user.tenant_id)
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


@router.get("/lookup", response_model=ContactLookupList)
async def lookup_contacts(
    relation_type: Optional[RelationType] = Query(None, description="Filtrer par type de relation"),
    search: Optional[str] = Query(None, description="Recherche textuelle"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche rapide pour les sélecteurs/autocomplete.

    Retourne une liste simplifiée (id, code, name) pour les listes déroulantes.
    """
    service = get_contacts_service(db, current_user.tenant_id)
    items = service.lookup_contacts(
        relation_type=relation_type,
        search=search,
        limit=limit
    )
    return ContactLookupList(items=items, total=len(items))


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un contact par son ID avec ses personnes et adresses."""
    service = get_contacts_service(db, current_user.tenant_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un contact par son code."""
    service = get_contacts_service(db, current_user.tenant_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un contact."""
    service = get_contacts_service(db, current_user.tenant_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprimer un contact.

    Par défaut, effectue un soft delete (is_active=False, deleted_at set).
    Avec permanent=True, supprime définitivement (cascade sur personnes et adresses).
    """
    service = get_contacts_service(db, current_user.tenant_id)
    if permanent:
        success = service.hard_delete_contact(contact_id)
    else:
        success = service.delete_contact(contact_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )


# ============================================================================
# ENDPOINTS PERSONNES DE CONTACT
# ============================================================================

@router.post("/{contact_id}/persons", response_model=ContactPersonResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_person(
    contact_id: UUID,
    data: ContactPersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une personne de contact."""
    service = get_contacts_service(db, current_user.tenant_id)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les personnes de contact."""
    service = get_contacts_service(db, current_user.tenant_id)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    return service.list_persons(contact_id, is_active=is_active)


@router.get("/{contact_id}/persons/{person_id}", response_model=ContactPersonResponse)
async def get_contact_person(
    contact_id: UUID,
    person_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une personne de contact."""
    service = get_contacts_service(db, current_user.tenant_id)
    person = service.get_person(person_id)
    if not person or person.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personne de contact non trouvée"
        )
    return person


@router.put("/{contact_id}/persons/{person_id}", response_model=ContactPersonResponse)
async def update_contact_person(
    contact_id: UUID,
    person_id: UUID,
    data: ContactPersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une personne de contact."""
    service = get_contacts_service(db, current_user.tenant_id)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une personne de contact."""
    service = get_contacts_service(db, current_user.tenant_id)

    # Vérifier que la personne appartient bien à ce contact
    existing = service.get_person(person_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personne de contact non trouvée"
        )

    service.delete_person(person_id)


# ============================================================================
# ENDPOINTS ADRESSES
# ============================================================================

@router.post("/{contact_id}/addresses", response_model=ContactAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_address(
    contact_id: UUID,
    data: ContactAddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une adresse au contact."""
    service = get_contacts_service(db, current_user.tenant_id)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les adresses d'un contact."""
    service = get_contacts_service(db, current_user.tenant_id)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    return service.list_addresses(contact_id, is_active=is_active)


@router.get("/{contact_id}/addresses/{address_id}", response_model=ContactAddressResponse)
async def get_contact_address(
    contact_id: UUID,
    address_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une adresse de contact."""
    service = get_contacts_service(db, current_user.tenant_id)
    address = service.get_address(address_id)
    if not address or address.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adresse non trouvée"
        )
    return address


@router.put("/{contact_id}/addresses/{address_id}", response_model=ContactAddressResponse)
async def update_contact_address(
    contact_id: UUID,
    address_id: UUID,
    data: ContactAddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une adresse de contact."""
    service = get_contacts_service(db, current_user.tenant_id)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une adresse de contact."""
    service = get_contacts_service(db, current_user.tenant_id)

    # Vérifier que l'adresse appartient bien à ce contact
    existing = service.get_address(address_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adresse non trouvée"
        )

    service.delete_address(address_id)


# ============================================================================
# ENDPOINTS LOGO / PHOTO
# ============================================================================

@router.post("/{contact_id}/logo", response_model=ContactResponse)
async def upload_contact_logo(
    contact_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploader le logo/photo du contact.

    Formats acceptés: JPG, PNG, GIF, WebP
    Taille max: 2 MB
    """
    service = get_contacts_service(db, current_user.tenant_id)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    # Valider le type de fichier
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non autorisé. Formats acceptés: {', '.join(allowed_types)}"
        )

    # Valider la taille (2 MB max)
    max_size = 2 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop volumineux (max 2 MB)"
        )

    # Upload et mise à jour du contact
    logo_url = await service.upload_logo(contact_id, contents, file.filename, file.content_type)

    return service.get_contact(contact_id)


@router.delete("/{contact_id}/logo", response_model=ContactResponse)
async def delete_contact_logo(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer le logo/photo du contact."""
    service = get_contacts_service(db, current_user.tenant_id)

    # Vérifier que le contact existe
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact non trouvé"
        )

    await service.delete_logo(contact_id)

    return service.get_contact(contact_id)


# ============================================================================
# ENDPOINTS STATISTIQUES
# ============================================================================

@router.get("/{contact_id}/stats")
async def get_contact_stats(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les statistiques d'un contact.

    Inclut:
    - Total commandes client
    - Total CA client
    - Total achats fournisseur
    - Dernière activité
    """
    service = get_contacts_service(db, current_user.tenant_id)

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
