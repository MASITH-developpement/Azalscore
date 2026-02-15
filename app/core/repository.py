"""
AZALS - Pattern Repository
===========================
Abstraction acces donnees avec isolation tenant automatique.
Utilise QueryOptimizer en interne pour eviter N+1 queries.

Conformite : AZA-NF-002
"""

import logging
from typing import TypeVar, Generic, Optional, List, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.query_optimizer import QueryOptimizer

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Repository de base avec isolation tenant automatique.

    Avantages :
    - Queries centralisees (maintenabilite)
    - tenant_id automatique (securite)
    - QueryOptimizer integre (performance)
    - Testabilite (mock repository facile)

    Usage :
        class ContactRepository(BaseRepository[UnifiedContact]):
            def __init__(self, db, tenant_id):
                super().__init__(db, UnifiedContact, tenant_id)

            def find_by_email(self, email):
                return self.db.query(self.model).filter(
                    self.model.tenant_id == self.tenant_id,
                    self.model.email == email
                ).first()
    """

    def __init__(self, db: Session, model: type[T], tenant_id: str):
        """
        Initialise le repository.

        Args:
            db: Session SQLAlchemy
            model: Classe du modele (ex: UnifiedContact)
            tenant_id: ID du tenant pour filtrage automatique
        """
        self.db = db
        self.model = model
        self.tenant_id = tenant_id
        self._optimizer = QueryOptimizer(db)

    def get_by_id(
        self,
        id: UUID,
        relations: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        Recupere entite par ID (filtre tenant automatiquement).

        Args:
            id: UUID de l'entite
            relations: Relations a eager load (evite N+1)

        Returns:
            Entite ou None si non trouvee

        Example:
            contact = repo.get_by_id(
                contact_id,
                relations=['persons', 'addresses']
            )
        """
        if relations:
            query = self._optimizer.query_with_relations(
                self.model,
                relations,
                use_selectin=True
            )
        else:
            query = self.db.query(self.model)

        return query.filter(
            self.model.tenant_id == self.tenant_id,
            self.model.id == id
        ).first()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        relations: Optional[List[str]] = None,
        order_by: Optional[str] = None
    ) -> tuple[List[T], int]:
        """
        Liste entites du tenant avec pagination.

        Args:
            skip: Offset pagination
            limit: Taille page (max 100 pour securite)
            filters: Filtres {field: value}
            relations: Relations a eager load
            order_by: Champ de tri

        Returns:
            Tuple (items, total)

        Example:
            contacts, total = repo.list_all(
                skip=0,
                limit=20,
                filters={'is_active': True},
                relations=['persons'],
                order_by='name'
            )
        """
        # Securite : limiter la taille max des pages
        limit = min(limit, 100)

        # Query avec ou sans relations
        if relations:
            query = self._optimizer.query_with_relations(
                self.model,
                relations,
                use_selectin=True
            )
        else:
            query = self.db.query(self.model)

        # Filtre tenant obligatoire
        query = query.filter(self.model.tenant_id == self.tenant_id)

        # Filtres optionnels
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        # Tri
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))

        # Pagination avec QueryOptimizer
        page = (skip // limit) + 1 if limit > 0 else 1
        items, total = self._optimizer.paginate(
            query,
            page=page,
            page_size=limit,
            count_total=True
        )

        return items, total

    def create(self, entity: T) -> T:
        """
        Cree entite avec tenant_id automatique.

        Args:
            entity: Instance du modele a creer

        Returns:
            Entite creee avec ID genere
        """
        # Securite : forcer le tenant_id
        entity.tenant_id = self.tenant_id

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        logger.info(
            "entity_created",
            extra={
                "model": self.model.__name__,
                "entity_id": str(entity.id),
                "tenant_id": self.tenant_id
            }
        )

        return entity

    def update(self, entity: T) -> T:
        """
        Met a jour entite.

        Args:
            entity: Instance modifiee

        Returns:
            Entite mise a jour
        """
        self.db.commit()
        self.db.refresh(entity)

        logger.info(
            "entity_updated",
            extra={
                "model": self.model.__name__,
                "entity_id": str(entity.id),
                "tenant_id": self.tenant_id
            }
        )

        return entity

    def delete(self, id: UUID, soft: bool = True) -> bool:
        """
        Supprime entite (soft delete par defaut).

        Args:
            id: UUID de l'entite
            soft: Si True, marque deleted_at au lieu de supprimer

        Returns:
            True si supprimee, False si non trouvee
        """
        entity = self.get_by_id(id)

        if not entity:
            return False

        if soft and hasattr(entity, 'deleted_at'):
            # Soft delete
            from datetime import datetime
            entity.deleted_at = datetime.utcnow()
            if hasattr(entity, 'is_active'):
                entity.is_active = False
            self.db.commit()

            logger.info(
                "entity_soft_deleted",
                extra={
                    "model": self.model.__name__,
                    "entity_id": str(id),
                    "tenant_id": self.tenant_id
                }
            )
        else:
            # Hard delete
            self.db.delete(entity)
            self.db.commit()

            logger.info(
                "entity_hard_deleted",
                extra={
                    "model": self.model.__name__,
                    "entity_id": str(id),
                    "tenant_id": self.tenant_id
                }
            )

        return True

    def exists(self, id: UUID) -> bool:
        """
        Verifie si une entite existe.

        Args:
            id: UUID de l'entite

        Returns:
            True si existe, False sinon
        """
        return self.db.query(
            self.db.query(self.model).filter(
                self.model.tenant_id == self.tenant_id,
                self.model.id == id
            ).exists()
        ).scalar()

    def count(self, filters: Optional[dict] = None) -> int:
        """
        Compte les entites (avec filtres optionnels).

        Args:
            filters: Filtres {field: value}

        Returns:
            Nombre d'entites
        """
        query = self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )

        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.count()

    def bulk_create(self, entities: List[T]) -> List[T]:
        """
        Cree plusieurs entites en batch.

        Args:
            entities: Liste d'instances a creer

        Returns:
            Liste des entites creees
        """
        for entity in entities:
            entity.tenant_id = self.tenant_id
            self.db.add(entity)

        self.db.commit()

        for entity in entities:
            self.db.refresh(entity)

        logger.info(
            "entities_bulk_created",
            extra={
                "model": self.model.__name__,
                "count": len(entities),
                "tenant_id": self.tenant_id
            }
        )

        return entities
