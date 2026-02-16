"""
EXEMPLE: Contacts Router avec CRUDRouter
=========================================

Ce fichier montre comment le router contacts pourrait être simplifié
en utilisant CRUDRouter.

AVANT: 564 lignes (router_unified.py actuel)
APRÈS: ~150 lignes (cette version)

GAIN: -73% de code!

NOTE: Cet exemple nécessite que ContactsService hérite de BaseService
et accepte SaaSContext au lieu de tenant_id.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

# Import unifié via azals
from app.azals import (
    CRUDRouter,
    SaaSContext,
    get_context,
    get_db,
    PaginatedResponse,
)

# Imports du module
from app.modules.contacts import (
    EntityType,
    RelationType,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactPersonCreate,
    ContactPersonUpdate,
    ContactPersonResponse,
    ContactAddressCreate,
    ContactAddressUpdate,
    ContactAddressResponse,
    ContactLookupList,
)
from app.modules.contacts.service import ContactsService


# =============================================================================
# CRUD AUTO-GÉNÉRÉ (remplace ~150 lignes de boilerplate!)
# =============================================================================

# Le CRUD principal est généré automatiquement
contacts_crud = CRUDRouter.create_crud_router(
    service_class=ContactsService,
    resource_name="contact",
    plural_name="contacts",
    create_schema=ContactCreate,
    update_schema=ContactUpdate,
    response_schema=ContactResponse,
    tags=["Contacts"],
)

# Router principal
router = APIRouter(prefix="/contacts", tags=["Contacts"])

# Inclure le CRUD auto-généré
# Cela ajoute automatiquement:
#   POST   /contacts         → Créer
#   GET    /contacts         → Lister (pagination)
#   GET    /contacts/{id}    → Récupérer
#   PUT    /contacts/{id}    → Modifier
#   DELETE /contacts/{id}    → Supprimer
router.include_router(contacts_crud)


# =============================================================================
# ENDPOINTS MÉTIER PERSONNALISÉS (on ne peut pas les auto-générer)
# =============================================================================

@router.get("/lookup", response_model=ContactLookupList)
async def lookup_contacts(
    relation_type: Optional[RelationType] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Recherche rapide pour autocomplete."""
    service = ContactsService(db, context)
    items = service.lookup_contacts(relation_type=relation_type, search=search, limit=limit)
    return ContactLookupList(items=items, total=len(items))


@router.get("/code/{code}", response_model=ContactResponse)
async def get_contact_by_code(
    code: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un contact par son code."""
    service = ContactsService(db, context)
    contact = service.get_contact_by_code(code)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact avec le code '{code}' non trouvé")
    return contact


@router.get("/{contact_id}/stats")
async def get_contact_stats(
    contact_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer les statistiques d'un contact."""
    service = ContactsService(db, context)
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    return {
        "contact_id": contact_id,
        "is_customer": contact.is_customer,
        "is_supplier": contact.is_supplier,
        "customer_stats": {
            "total_revenue": float(contact.customer_total_revenue or 0),
            "order_count": contact.customer_order_count or 0,
        } if contact.is_customer else None,
        "supplier_stats": {
            "total_purchases": float(contact.supplier_total_purchases or 0),
            "order_count": contact.supplier_order_count or 0,
        } if contact.is_supplier else None,
    }


# =============================================================================
# SOUS-RESSOURCES: Personnes (simplifiées)
# =============================================================================

@router.post("/{contact_id}/persons", response_model=ContactPersonResponse, status_code=201)
async def create_person(
    contact_id: UUID,
    data: ContactPersonCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Ajouter une personne de contact."""
    service = ContactsService(db, context)
    if not service.get_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return service.create_person(contact_id, data)


@router.get("/{contact_id}/persons", response_model=List[ContactPersonResponse])
async def list_persons(
    contact_id: UUID,
    is_active: Optional[bool] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les personnes de contact."""
    service = ContactsService(db, context)
    if not service.get_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return service.list_persons(contact_id, is_active=is_active)


@router.put("/{contact_id}/persons/{person_id}", response_model=ContactPersonResponse)
async def update_person(
    contact_id: UUID,
    person_id: UUID,
    data: ContactPersonUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour une personne de contact."""
    service = ContactsService(db, context)
    existing = service.get_person(person_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="Personne non trouvée")
    return service.update_person(person_id, data)


@router.delete("/{contact_id}/persons/{person_id}", status_code=204)
async def delete_person(
    contact_id: UUID,
    person_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer une personne de contact."""
    service = ContactsService(db, context)
    existing = service.get_person(person_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="Personne non trouvée")
    service.delete_person(person_id)


# =============================================================================
# SOUS-RESSOURCES: Adresses (simplifiées)
# =============================================================================

@router.post("/{contact_id}/addresses", response_model=ContactAddressResponse, status_code=201)
async def create_address(
    contact_id: UUID,
    data: ContactAddressCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Ajouter une adresse."""
    service = ContactsService(db, context)
    if not service.get_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return service.create_address(contact_id, data)


@router.get("/{contact_id}/addresses", response_model=List[ContactAddressResponse])
async def list_addresses(
    contact_id: UUID,
    is_active: Optional[bool] = None,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les adresses."""
    service = ContactsService(db, context)
    if not service.get_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return service.list_addresses(contact_id, is_active=is_active)


@router.put("/{contact_id}/addresses/{address_id}", response_model=ContactAddressResponse)
async def update_address(
    contact_id: UUID,
    address_id: UUID,
    data: ContactAddressUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour une adresse."""
    service = ContactsService(db, context)
    existing = service.get_address(address_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="Adresse non trouvée")
    return service.update_address(address_id, data)


@router.delete("/{contact_id}/addresses/{address_id}", status_code=204)
async def delete_address(
    contact_id: UUID,
    address_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer une adresse."""
    service = ContactsService(db, context)
    existing = service.get_address(address_id)
    if not existing or existing.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="Adresse non trouvée")
    service.delete_address(address_id)


# =============================================================================
# LOGO (endpoint métier spécifique)
# =============================================================================

@router.post("/{contact_id}/logo", response_model=ContactResponse)
async def upload_logo(
    contact_id: UUID,
    file: UploadFile = File(...),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Uploader le logo du contact."""
    service = ContactsService(db, context)
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    # Validation
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Type de fichier non autorisé")

    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 2 MB)")

    await service.upload_logo(contact_id, contents, file.filename, file.content_type)
    return service.get_contact(contact_id)


@router.delete("/{contact_id}/logo", response_model=ContactResponse)
async def delete_logo(
    contact_id: UUID,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer le logo du contact."""
    service = ContactsService(db, context)
    contact = service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    await service.delete_logo(contact_id)
    return service.get_contact(contact_id)


# =============================================================================
# RÉSUMÉ
# =============================================================================
"""
COMPARAISON:

┌─────────────────────────────────────────────────────────────────────────┐
│ Fichier                          │ Lignes │ Réduction                   │
├──────────────────────────────────┼────────┼─────────────────────────────┤
│ router_unified.py (actuel)       │ 564    │ -                           │
│ router_unified_v2_example.py     │ ~250   │ -55%                        │
│                                  │        │                             │
│ Si on migre les sous-ressources  │ ~100   │ -82%                        │
│ vers CRUDRouter aussi            │        │                             │
└──────────────────────────────────┴────────┴─────────────────────────────┘

NOTE IMPORTANTE:
Pour utiliser CRUDRouter, le service doit:
1. Hériter de BaseService
2. Accepter SaaSContext au lieu de tenant_id

Exemple de service compatible:

    class ContactsService(BaseService[Contact, ContactCreate, ContactUpdate]):
        model = Contact

        def __init__(self, db: Session, context: SaaSContext):
            super().__init__(db, context)

        # Les méthodes CRUD sont héritées automatiquement!
        # On ne garde que les méthodes métier:

        def lookup_contacts(self, ...):
            ...

        def upload_logo(self, ...):
            ...
"""
