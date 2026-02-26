"""
AZALS MODULE - Contacts - Repository
=====================================

Repository specialise pour les contacts unifies.
Demontre l'utilisation de BaseRepository avec methodes metier.

Proof of Concept pour le Pattern Repository AZALSCORE.
"""
from __future__ import annotations


import logging
from typing import Optional, List
from uuid import UUID

from app.core.repository import BaseRepository
from app.modules.contacts.models import UnifiedContact, RelationType

logger = logging.getLogger(__name__)


class ContactRepository(BaseRepository[UnifiedContact]):
    """
    Repository specialise pour les contacts unifies.

    Herite de BaseRepository :
    - tenant_id automatique
    - QueryOptimizer integre
    - Methodes CRUD standard

    Ajoute methodes metier specifiques aux contacts.

    Usage :
        from app.modules.contacts.repository import ContactRepository

        repo = ContactRepository(db, ctx.tenant_id)
        contacts, total = repo.list_active(skip=0, limit=20)
        contact = repo.find_by_email("john@example.com")
    """

    def __init__(self, db, tenant_id: str):
        """
        Initialise le repository contacts.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant
        """
        super().__init__(db, UnifiedContact, tenant_id)

    # =========================================================================
    # RECHERCHE
    # =========================================================================

    def find_by_email(self, email: str) -> Optional[UnifiedContact]:
        """
        Recherche contact par email (unique par tenant).

        Args:
            email: Adresse email

        Returns:
            Contact ou None
        """
        return self.db.query(UnifiedContact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.email == email,
            UnifiedContact.deleted_at.is_(None)
        ).first()

    def find_by_code(self, code: str) -> Optional[UnifiedContact]:
        """
        Recherche contact par code (CONT-YYYY-XXXX).

        Args:
            code: Code du contact

        Returns:
            Contact ou None
        """
        return self.db.query(UnifiedContact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.code == code,
            UnifiedContact.deleted_at.is_(None)
        ).first()

    def search_by_name(
        self,
        name: str,
        limit: int = 50
    ) -> List[UnifiedContact]:
        """
        Recherche floue par nom.

        Args:
            name: Terme de recherche
            limit: Nombre max de resultats

        Returns:
            Liste de contacts
        """
        return self.db.query(UnifiedContact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.name.ilike(f"%{name}%"),
            UnifiedContact.deleted_at.is_(None)
        ).limit(limit).all()

    # =========================================================================
    # FILTRES METIER
    # =========================================================================

    def list_active(
        self,
        skip: int = 0,
        limit: int = 100,
        relations: Optional[List[str]] = None
    ) -> tuple[List[UnifiedContact], int]:
        """
        Liste contacts actifs uniquement.

        Args:
            skip: Offset pagination
            limit: Taille page
            relations: Relations a eager load

        Returns:
            Tuple (contacts, total)
        """
        return self.list_all(
            skip=skip,
            limit=limit,
            filters={"is_active": True},
            relations=relations,
            order_by="name"
        )

    def list_customers(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[UnifiedContact], int]:
        """
        Liste contacts de type client.

        Args:
            skip: Offset pagination
            limit: Taille page

        Returns:
            Tuple (customers, total)
        """
        query = self.db.query(UnifiedContact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.relation_types.contains([RelationType.CUSTOMER.value]),
            UnifiedContact.deleted_at.is_(None),
            UnifiedContact.is_active.is_(True)
        ).order_by(UnifiedContact.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total

    def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[UnifiedContact], int]:
        """
        Liste contacts de type fournisseur.

        Args:
            skip: Offset pagination
            limit: Taille page

        Returns:
            Tuple (suppliers, total)
        """
        query = self.db.query(UnifiedContact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.relation_types.contains([RelationType.SUPPLIER.value]),
            UnifiedContact.deleted_at.is_(None),
            UnifiedContact.is_active.is_(True)
        ).order_by(UnifiedContact.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()

        return items, total

    # =========================================================================
    # AVEC RELATIONS (eager loading)
    # =========================================================================

    def get_with_details(self, id: UUID) -> Optional[UnifiedContact]:
        """
        Recupere contact avec toutes ses relations.

        Utilise QueryOptimizer pour eviter N+1.

        Args:
            id: UUID du contact

        Returns:
            Contact avec persons et addresses charges
        """
        return self.get_by_id(
            id,
            relations=['persons', 'addresses']
        )

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def count_active(self) -> int:
        """
        Compte les contacts actifs.

        Returns:
            Nombre de contacts actifs
        """
        return self.count(filters={"is_active": True})

    def count_customers(self) -> int:
        """
        Compte les clients.

        Returns:
            Nombre de clients
        """
        return self.db.query(UnifiedContact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.relation_types.contains([RelationType.CUSTOMER.value]),
            UnifiedContact.deleted_at.is_(None)
        ).count()

    def count_suppliers(self) -> int:
        """
        Compte les fournisseurs.

        Returns:
            Nombre de fournisseurs
        """
        return self.db.query(UnifiedContact).filter(
            UnifiedContact.tenant_id == self.tenant_id,
            UnifiedContact.relation_types.contains([RelationType.SUPPLIER.value]),
            UnifiedContact.deleted_at.is_(None)
        ).count()
