"""
AZALS MODULE M7 - Base Quality Service
=======================================

Classe de base pour tous les sous-services qualité.
"""
from __future__ import annotations


import logging
from typing import TypeVar, Generic, Type, Optional, Tuple, List, Any
from datetime import date

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseQualityService(Generic[T]):
    """
    Classe de base pour les services qualité.

    Fournit des méthodes communes pour:
    - CRUD basique
    - Pagination
    - Filtrage
    - Recherche
    """

    model: Type[T] = None

    def __init__(self, db: Session, tenant_id: int, user_id: int = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def _base_query(self):
        """Query de base avec filtre tenant."""
        return self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )

    def _get_by_id(self, entity_id: int, options: list = None) -> Optional[T]:
        """Récupère une entité par ID avec options de chargement."""
        query = self._base_query().filter(self.model.id == entity_id)
        if options:
            for opt in options:
                query = query.options(opt)
        return query.first()

    def _list_with_filters(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: dict = None,
        search_fields: list = None,
        search: str = None,
        order_by=None,
        options: list = None,
    ) -> Tuple[List[T], int]:
        """
        Liste les entités avec filtres, recherche et pagination.

        Args:
            skip: Offset
            limit: Nombre max de résultats
            filters: Dict de {field: value} pour filtrage exact
            search_fields: Liste de champs pour recherche texte
            search: Terme de recherche
            order_by: Colonne de tri (par défaut: id desc)
            options: Options SQLAlchemy (joinedload, etc.)

        Returns:
            Tuple (items, total)
        """
        query = self._base_query()

        # Appliquer les filtres exacts
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        # Appliquer la recherche texte
        if search and search_fields:
            search_filter = f"%{search}%"
            conditions = [
                getattr(self.model, field).ilike(search_filter)
                for field in search_fields
                if hasattr(self.model, field)
            ]
            if conditions:
                query = query.filter(or_(*conditions))

        # Compter le total
        total = query.count()

        # Appliquer le tri
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            query = query.order_by(desc(self.model.id))

        # Appliquer les options de chargement
        if options:
            for opt in options:
                query = query.options(opt)

        # Pagination
        items = query.offset(skip).limit(limit).all()

        return items, total

    def _create(self, entity: T) -> T:
        """Crée une entité."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _update(self, entity: T, data: dict) -> T:
        """Met à jour une entité avec un dict de données."""
        for field, value in data.items():
            if hasattr(entity, field) and value is not None:
                setattr(entity, field, value)
        if hasattr(entity, 'updated_by'):
            entity.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _delete(self, entity: T, soft: bool = True) -> bool:
        """Supprime une entité (soft ou hard delete)."""
        if soft and hasattr(entity, 'is_active'):
            entity.is_active = False
            self.db.commit()
        else:
            self.db.delete(entity)
            self.db.commit()
        return True

    def _generate_sequence(self, sequence_type: str) -> str:
        """Génère un numéro de séquence."""
        from app.core.sequences import SequenceGenerator
        seq = SequenceGenerator(self.db, str(self.tenant_id))
        return seq.next_reference(sequence_type)
