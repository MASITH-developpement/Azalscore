"""
AZALS MODULE - Contacts Unifiés
===============================

Module de gestion unifiée des contacts (Clients et Fournisseurs).
Fournit des sous-programmes réutilisables par tous les autres modules.

Fonctionnalités:
- Fiche contact unifiée (Client / Fournisseur / Les deux)
- Code auto-généré (CONT-YYYY-XXXX)
- Type d'entité (Particulier / Société)
- Contacts multiples (personnes)
- Adresses multiples (facturation, livraison, chantier)
- Logo / Photo
"""

from .models import (
    UnifiedContact,
    ContactAddress,
    ContactPerson,
    ContactSequence,
    AddressType,
    EntityType,
    RelationType,
    ContactPersonRole,
)
from .schemas import (
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
from .service import ContactsService

__all__ = [
    # Models
    "UnifiedContact",
    "ContactAddress",
    "ContactPerson",
    "ContactSequence",
    # Enums
    "AddressType",
    "EntityType",
    "RelationType",
    "ContactPersonRole",
    # Schemas
    "ContactCreate",
    "ContactUpdate",
    "ContactResponse",
    "ContactList",
    "ContactSummary",
    "ContactLookup",
    "ContactLookupList",
    "ContactPersonCreate",
    "ContactPersonUpdate",
    "ContactPersonResponse",
    "ContactAddressCreate",
    "ContactAddressUpdate",
    "ContactAddressResponse",
    # Service
    "ContactsService",
]
