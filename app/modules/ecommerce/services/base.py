"""
AZALS MODULE 12 - E-Commerce Base Service
===========================================

Service de base avec fonctionnalités communes.
"""

import logging
from typing import Generic, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.query_optimizer import QueryOptimizer

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseEcommerceService(Generic[T]):
    """
    Service de base pour les sous-services e-commerce.

    Fournit:
    - Gestion de session et tenant
    - Query optimizer
    - Méthodes CRUD génériques
    - Pagination
    """

    model: Type[T] = None

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        user_id: Optional[str] = None,
    ):
        """
        Initialise le service de base.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour isolation multi-tenant
            user_id: ID de l'utilisateur pour audit
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._optimizer = QueryOptimizer(db)

    def _base_query(self):
        """Retourne une query de base filtrée par tenant."""
        return self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )

    def _get_by_id(self, entity_id: int) -> Optional[T]:
        """Récupère une entité par ID avec isolation tenant."""
        return self._base_query().filter(self.model.id == entity_id).first()

    def _list_paginated(
        self,
        query,
        page: int = 1,
        page_size: int = 20,
        order_by=None,
        order_desc: bool = True,
    ) -> Tuple[List[T], int]:
        """
        Pagine une query et retourne les résultats avec le total.

        Args:
            query: Query SQLAlchemy
            page: Numéro de page (1-indexed)
            page_size: Nombre d'éléments par page
            order_by: Colonne de tri
            order_desc: Tri descendant si True

        Returns:
            Tuple (items, total_count)
        """
        total = query.count()

        if order_by is not None:
            query = (
                query.order_by(desc(order_by))
                if order_desc
                else query.order_by(order_by)
            )

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def _create(self, data: dict) -> T:
        """
        Crée une nouvelle entité.

        Args:
            data: Dictionnaire des données

        Returns:
            Entité créée
        """
        entity = self.model(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _update(self, entity: T, data: dict) -> T:
        """
        Met à jour une entité.

        Args:
            entity: Entité à mettre à jour
            data: Dictionnaire des données (exclude_unset=True recommandé)

        Returns:
            Entité mise à jour
        """
        for field, value in data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _delete(self, entity: T) -> bool:
        """
        Supprime une entité.

        Args:
            entity: Entité à supprimer

        Returns:
            True si supprimée
        """
        self.db.delete(entity)
        self.db.commit()
        return True

    def _soft_delete(self, entity: T, status_field: str, archived_status) -> bool:
        """
        Archive une entité (soft delete).

        Args:
            entity: Entité à archiver
            status_field: Nom du champ de statut
            archived_status: Valeur du statut archivé

        Returns:
            True si archivée
        """
        setattr(entity, status_field, archived_status)
        self.db.commit()
        return True
