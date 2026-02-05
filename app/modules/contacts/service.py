"""
AZALS MODULE - Contacts Unifiés - Service
=========================================

Service métier pour la gestion des contacts.
Applique l'isolation totale par tenant.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from .models import (
    AddressType,
    UnifiedContact,
    ContactAddress,
    ContactPerson,
    ContactSequence,
    EntityType,
    RelationType,
)
from .schemas import (
    ContactAddressCreate,
    ContactAddressUpdate,
    ContactCreate,
    ContactPersonCreate,
    ContactPersonUpdate,
    ContactUpdate,
)


class ContactsService:
    """
    Service de gestion des contacts.

    PRINCIPE D'ISOLATION:
    - Tous les contacts sont isolés par tenant_id
    - Une même entité (ACME Corp) peut être Client ET Fournisseur = 1 seule fiche
    - Deux tenants peuvent avoir un contact "ACME Corp" = 2 fiches indépendantes
    - Aucun partage entre tenants
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # GÉNÉRATION DE CODE
    # ========================================================================

    def _generate_code(self) -> str:
        """
        Génère un code CONT-YYYY-XXXX de manière transactionnelle.

        Utilise un verrouillage pessimiste (with_for_update) pour éviter
        les conflits en cas d'accès concurrent.
        """
        current_year = datetime.utcnow().year

        # Verrouillage pessimiste pour éviter les doublons
        sequence = self.db.query(ContactSequence).filter(
            ContactSequence.tenant_id == self.tenant_id,
            ContactSequence.year == current_year
        ).with_for_update().first()

        if not sequence:
            sequence = ContactSequence(
                tenant_id=self.tenant_id,
                year=current_year,
                last_number=0
            )
            self.db.add(sequence)
            self.db.flush()

        sequence.last_number += 1
        return f"CONT-{current_year}-{sequence.last_number:04d}"

    # ========================================================================
    # CRUD CONTACT
    # ========================================================================

    def create_contact(self, data: ContactCreate, user_id: Optional[UUID] = None) -> UnifiedContact:
        """
        Créer un nouveau contact.

        - Code auto-généré si non fourni
        - Personnes et adresses créées en cascade
        """
        # Générer le code si non fourni
        code = data.code if data.code else self._generate_code()

        # Vérifier unicité du code
        existing = self.get_contact_by_code(code)
        if existing:
            raise ValueError(f"Un contact avec le code {code} existe déjà")

        # Convertir relation_types en liste de strings pour JSONB
        relation_types = [rt.value if isinstance(rt, RelationType) else rt for rt in data.relation_types]

        # Créer le contact
        contact = UnifiedContact(
            tenant_id=self.tenant_id,
            code=code,
            entity_type=data.entity_type,
            relation_types=relation_types,
            name=data.name,
            legal_name=data.legal_name,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            mobile=data.mobile,
            website=data.website,
            tax_id=data.tax_id,
            registration_number=data.registration_number,
            legal_form=data.legal_form,
            logo_url=data.logo_url,
            # Client
            customer_type=data.customer_type,
            customer_payment_terms=data.customer_payment_terms,
            customer_payment_method=data.customer_payment_method,
            customer_credit_limit=data.customer_credit_limit,
            customer_discount_rate=data.customer_discount_rate,
            customer_currency=data.customer_currency,
            assigned_to=data.assigned_to,
            industry=data.industry,
            source=data.source,
            segment=data.segment,
            # Fournisseur
            supplier_status=data.supplier_status,
            supplier_type=data.supplier_type,
            supplier_payment_terms=data.supplier_payment_terms,
            supplier_currency=data.supplier_currency,
            supplier_credit_limit=data.supplier_credit_limit,
            supplier_category=data.supplier_category,
            # Métadonnées
            tags=data.tags,
            notes=data.notes,
            internal_notes=data.internal_notes,
            created_by=user_id,
        )

        self.db.add(contact)
        self.db.flush()  # Pour obtenir l'ID

        # Créer les personnes de contact
        for person_data in data.persons:
            self._create_person(contact.id, person_data)

        # Créer les adresses
        for address_data in data.addresses:
            self._create_address(contact.id, address_data)

        self.db.commit()
        self.db.refresh(contact)

        return contact

    def get_contact(self, contact_id: UUID) -> Optional[UnifiedContact]:
        """Récupérer un contact par ID (isolé par tenant)."""
        return self.db.query(Contact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.id == contact_id,
            UnifiedContact.deleted_at.is_(None)
        ).first()

    def get_contact_by_code(self, code: str) -> Optional[UnifiedContact]:
        """Récupérer un contact par code (isolé par tenant)."""
        return self.db.query(Contact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.code == code,
            UnifiedContact.deleted_at.is_(None)
        ).first()

    def list_contacts(
        self,
        entity_type: Optional[EntityType] = None,
        relation_type: Optional[RelationType] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[UnifiedContact], int]:
        """
        Lister les contacts avec filtres (isolés par tenant).

        Args:
            entity_type: Filtrer par type d'entité (INDIVIDUAL/COMPANY)
            relation_type: Filtrer par type de relation (CUSTOMER/SUPPLIER)
            is_active: Filtrer par statut actif
            search: Recherche textuelle (nom, email, code)
            assigned_to: Filtrer par commercial assigné
            page: Numéro de page
            page_size: Taille de page

        Returns:
            Tuple (liste contacts, total)
        """
        query = self.db.query(Contact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.deleted_at.is_(None)
        )

        # Filtres
        if entity_type:
            query = query.filter(UnifiedContact.entity_type == entity_type)

        if relation_type:
            # Filtrer sur le JSONB relation_types
            query = query.filter(
                UnifiedContact.relation_types.contains([relation_type.value])
            )

        if is_active is not None:
            query = query.filter(UnifiedContact.is_active == is_active)

        if assigned_to:
            query = query.filter(UnifiedContact.assigned_to == assigned_to)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    UnifiedContact.name.ilike(search_term),
                    UnifiedContact.code.ilike(search_term),
                    UnifiedContact.email.ilike(search_term),
                    UnifiedContact.legal_name.ilike(search_term),
                    UnifiedContact.tax_id.ilike(search_term),
                    UnifiedContact.registration_number.ilike(search_term),
                )
            )

        # Compter le total
        total = query.count()

        # Pagination
        query = query.order_by(desc(UnifiedContact.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        return query.all(), total

    def update_contact(self, contact_id: UUID, data: ContactUpdate) -> Optional[UnifiedContact]:
        """Mettre à jour un contact."""
        contact = self.get_contact(contact_id)
        if not contact:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Convertir relation_types si présent
        if 'relation_types' in update_data and update_data['relation_types']:
            update_data['relation_types'] = [
                rt.value if isinstance(rt, RelationType) else rt
                for rt in update_data['relation_types']
            ]

        for field, value in update_data.items():
            setattr(contact, field, value)

        self.db.commit()
        self.db.refresh(contact)

        return contact

    def delete_contact(self, contact_id: UUID) -> bool:
        """
        Soft delete d'un contact (deleted_at + is_active=False).
        """
        contact = self.get_contact(contact_id)
        if not contact:
            return False

        contact.deleted_at = datetime.utcnow()
        contact.is_active = False

        self.db.commit()
        return True

    def hard_delete_contact(self, contact_id: UUID) -> bool:
        """
        Suppression définitive d'un contact et ses relations.
        """
        contact = self.get_contact(contact_id)
        if not contact:
            return False

        self.db.delete(contact)
        self.db.commit()
        return True

    # ========================================================================
    # CRUD PERSONNES DE CONTACT
    # ========================================================================

    def _create_person(self, contact_id: UUID, data: ContactPersonCreate) -> ContactPerson:
        """Créer une personne de contact (interne)."""
        person = ContactPerson(
            tenant_id=self.tenant_id,
            contact_id=contact_id,
            **data.model_dump()
        )
        self.db.add(person)
        self.db.flush()
        return person

    def create_person(self, contact_id: UUID, data: ContactPersonCreate) -> Optional[ContactPerson]:
        """Créer une personne de contact."""
        contact = self.get_contact(contact_id)
        if not contact:
            return None

        # Si marqué comme principal, retirer le flag des autres
        if data.is_primary:
            self._unset_primary_person(contact_id)

        person = self._create_person(contact_id, data)
        self.db.commit()
        self.db.refresh(person)

        return person

    def get_person(self, person_id: UUID) -> Optional[ContactPerson]:
        """Récupérer une personne de contact."""
        return self.db.query(ContactPerson).filter(
            ContactPerson.tenant_id == self.tenant_id,
            ContactPerson.id == person_id
        ).first()

    def list_persons(self, contact_id: UUID, is_active: Optional[bool] = None) -> List[ContactPerson]:
        """Lister les personnes d'un contact."""
        query = self.db.query(ContactPerson).filter(
            ContactPerson.tenant_id == self.tenant_id,
            ContactPerson.contact_id == contact_id,
        )

        if is_active is not None:
            query = query.filter(ContactPerson.is_active == is_active)
        else:
            # Par défaut, ne montrer que les actifs
            query = query.filter(ContactPerson.is_active == True)

        return query.order_by(
            desc(ContactPerson.is_primary),
            ContactPerson.last_name
        ).all()

    def update_person(self, person_id: UUID, data: ContactPersonUpdate) -> Optional[ContactPerson]:
        """Mettre à jour une personne de contact."""
        person = self.get_person(person_id)
        if not person:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Si marqué comme principal, retirer le flag des autres
        if update_data.get('is_primary'):
            self._unset_primary_person(person.contact_id)

        for field, value in update_data.items():
            setattr(person, field, value)

        self.db.commit()
        self.db.refresh(person)

        return person

    def delete_person(self, person_id: UUID) -> bool:
        """Supprimer une personne de contact (soft delete)."""
        person = self.get_person(person_id)
        if not person:
            return False

        person.is_active = False
        self.db.commit()
        return True

    def _unset_primary_person(self, contact_id: UUID):
        """Retirer le flag 'principal' de toutes les personnes d'un contact."""
        self.db.query(ContactPerson).filter(
            ContactPerson.tenant_id == self.tenant_id,
            ContactPerson.contact_id == contact_id,
            ContactPerson.is_primary == True
        ).update({'is_primary': False})

    # ========================================================================
    # CRUD ADRESSES
    # ========================================================================

    def _create_address(self, contact_id: UUID, data: ContactAddressCreate) -> ContactAddress:
        """Créer une adresse (interne)."""
        address = ContactAddress(
            tenant_id=self.tenant_id,
            contact_id=contact_id,
            **data.model_dump()
        )
        self.db.add(address)
        self.db.flush()
        return address

    def create_address(self, contact_id: UUID, data: ContactAddressCreate) -> Optional[ContactAddress]:
        """Créer une adresse."""
        contact = self.get_contact(contact_id)
        if not contact:
            return None

        # Si marquée par défaut, retirer le flag des autres du même type
        if data.is_default:
            self._unset_default_address(contact_id, data.address_type)

        address = self._create_address(contact_id, data)
        self.db.commit()
        self.db.refresh(address)

        return address

    def get_address(self, address_id: UUID) -> Optional[ContactAddress]:
        """Récupérer une adresse."""
        return self.db.query(ContactAddress).filter(
            ContactAddress.tenant_id == self.tenant_id,
            ContactAddress.id == address_id
        ).first()

    def list_addresses(
        self,
        contact_id: UUID,
        address_type: Optional[AddressType] = None,
        is_active: Optional[bool] = None
    ) -> List[ContactAddress]:
        """Lister les adresses d'un contact."""
        query = self.db.query(ContactAddress).filter(
            ContactAddress.tenant_id == self.tenant_id,
            ContactAddress.contact_id == contact_id,
        )

        if is_active is not None:
            query = query.filter(ContactAddress.is_active == is_active)
        else:
            # Par défaut, ne montrer que les actives
            query = query.filter(ContactAddress.is_active == True)

        if address_type:
            query = query.filter(ContactAddress.address_type == address_type)

        return query.order_by(
            desc(ContactAddress.is_default),
            ContactAddress.address_type
        ).all()

    def update_address(self, address_id: UUID, data: ContactAddressUpdate) -> Optional[ContactAddress]:
        """Mettre à jour une adresse."""
        address = self.get_address(address_id)
        if not address:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Si marquée par défaut, retirer le flag des autres du même type
        if update_data.get('is_default'):
            address_type = update_data.get('address_type', address.address_type)
            self._unset_default_address(address.contact_id, address_type)

        for field, value in update_data.items():
            setattr(address, field, value)

        self.db.commit()
        self.db.refresh(address)

        return address

    def delete_address(self, address_id: UUID) -> bool:
        """Supprimer une adresse (soft delete)."""
        address = self.get_address(address_id)
        if not address:
            return False

        address.is_active = False
        self.db.commit()
        return True

    def _unset_default_address(self, contact_id: UUID, address_type: AddressType):
        """Retirer le flag 'par défaut' des adresses du même type."""
        self.db.query(ContactAddress).filter(
            ContactAddress.tenant_id == self.tenant_id,
            ContactAddress.contact_id == contact_id,
            ContactAddress.address_type == address_type,
            ContactAddress.is_default == True
        ).update({'is_default': False})

    # ========================================================================
    # LOGO / PHOTO
    # ========================================================================

    def _get_logo_dir(self) -> "Path":
        """Retourne le répertoire des logos pour ce tenant."""
        from pathlib import Path
        logo_dir = Path(__file__).parent.parent.parent.parent / "uploads" / "contacts" / self.tenant_id
        logo_dir.mkdir(parents=True, exist_ok=True)
        return logo_dir

    async def upload_logo(
        self,
        contact_id: UUID,
        content: bytes,
        filename: str,
        content_type: str
    ) -> str:
        """
        Upload et sauvegarder le logo d'un contact.

        Returns:
            URL du logo uploadé
        """
        import aiofiles
        from pathlib import Path

        contact = self.get_contact(contact_id)
        if not contact:
            raise ValueError("Contact non trouvé")

        # Supprimer l'ancien logo si existant
        if contact.logo_url:
            await self.delete_logo(contact_id)

        # Déterminer l'extension
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        ext = ext_map.get(content_type, ".png")

        # Nom unique pour le fichier
        logo_filename = f"contact_{contact_id}{ext}"
        logo_dir = self._get_logo_dir()
        logo_path = logo_dir / logo_filename

        # Sauvegarder le fichier
        async with aiofiles.open(logo_path, "wb") as f:
            await f.write(content)

        # URL relative pour le frontend
        logo_url = f"/uploads/contacts/{self.tenant_id}/{logo_filename}"

        # Mettre à jour le contact
        contact.logo_url = logo_url
        self.db.commit()

        return logo_url

    async def delete_logo(self, contact_id: UUID) -> bool:
        """Supprimer le logo d'un contact."""
        import aiofiles.os
        from pathlib import Path

        contact = self.get_contact(contact_id)
        if not contact:
            return False

        if contact.logo_url:
            # Extraire le nom du fichier depuis l'URL
            filename = contact.logo_url.split("/")[-1]
            logo_path = self._get_logo_dir() / filename

            # Supprimer le fichier s'il existe
            try:
                if logo_path.exists():
                    await aiofiles.os.remove(logo_path)
            except Exception:
                pass  # Ignorer les erreurs de suppression

        contact.logo_url = None
        self.db.commit()
        return True

    def update_logo(self, contact_id: UUID, logo_url: str) -> Optional[UnifiedContact]:
        """Mettre à jour directement l'URL du logo (sans upload)."""
        contact = self.get_contact(contact_id)
        if not contact:
            return None

        contact.logo_url = logo_url
        self.db.commit()
        self.db.refresh(contact)

        return contact

    # ========================================================================
    # LOOKUPS (pour les sélecteurs)
    # ========================================================================

    def lookup_contacts(
        self,
        relation_type: Optional[RelationType] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[UnifiedContact]:
        """
        Recherche rapide pour les sélecteurs (ContactSelector).

        Retourne une liste simplifiée pour les dropdowns/autocomplete.
        """
        query = self.db.query(Contact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.is_active == True,
            UnifiedContact.deleted_at.is_(None)
        )

        if relation_type:
            query = query.filter(
                UnifiedContact.relation_types.contains([relation_type.value])
            )

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    UnifiedContact.name.ilike(search_term),
                    UnifiedContact.code.ilike(search_term),
                )
            )

        return query.order_by(UnifiedContact.name).limit(limit).all()

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def check_duplicate(
        self,
        tax_id: Optional[str] = None,
        registration_number: Optional[str] = None,
        email: Optional[str] = None,
        exclude_id: Optional[UUID] = None
    ) -> Optional[UnifiedContact]:
        """
        Vérifier s'il existe un contact avec les mêmes identifiants.

        Utile pour éviter les doublons lors de la création.
        """
        query = self.db.query(Contact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.deleted_at.is_(None)
        )

        if exclude_id:
            query = query.filter(UnifiedContact.id != exclude_id)

        conditions = []
        if tax_id:
            conditions.append(UnifiedContact.tax_id == tax_id)
        if registration_number:
            conditions.append(UnifiedContact.registration_number == registration_number)
        if email:
            conditions.append(UnifiedContact.email == email)

        if not conditions:
            return None

        query = query.filter(or_(*conditions))
        return query.first()


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_contacts_service(db: Session, tenant_id: str) -> ContactsService:
    """Factory pour créer un service Contacts."""
    return ContactsService(db, tenant_id)
