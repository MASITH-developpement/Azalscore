"""
AZALS MODULE 12 - E-Commerce Category Service
===============================================

Gestion des catégories de produits.
"""

import logging
from typing import List, Optional

from app.modules.ecommerce.models import EcommerceCategory
from app.modules.ecommerce.schemas import CategoryCreate, CategoryUpdate

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class CategoryService(BaseEcommerceService[EcommerceCategory]):
    """Service de gestion des catégories."""

    model = EcommerceCategory

    def create(self, data: CategoryCreate) -> EcommerceCategory:
        """Crée une nouvelle catégorie."""
        return self._create(data.model_dump())

    def get(self, category_id: int) -> Optional[EcommerceCategory]:
        """Récupère une catégorie par ID."""
        return self._get_by_id(category_id)

    def list(
        self,
        parent_id: Optional[int] = None,
        visible_only: bool = True,
    ) -> List[EcommerceCategory]:
        """
        Liste les catégories.

        Args:
            parent_id: Filtrer par catégorie parente
            visible_only: Si True, uniquement les catégories visibles

        Returns:
            Liste des catégories triées par ordre
        """
        query = self._base_query()

        if parent_id is not None:
            query = query.filter(EcommerceCategory.parent_id == parent_id)

        if visible_only:
            query = query.filter(EcommerceCategory.is_visible == True)

        return query.order_by(EcommerceCategory.sort_order).all()

    def update(
        self,
        category_id: int,
        data: CategoryUpdate,
    ) -> Optional[EcommerceCategory]:
        """Met à jour une catégorie."""
        category = self.get(category_id)
        if not category:
            return None

        return self._update(category, data.model_dump(exclude_unset=True))

    def delete(self, category_id: int) -> bool:
        """Supprime une catégorie."""
        category = self.get(category_id)
        if not category:
            return False

        return self._delete(category)

    def get_tree(self) -> List[dict]:
        """
        Récupère l'arborescence complète des catégories.

        Returns:
            Liste des catégories racines avec leurs enfants
        """
        all_categories = self.list(visible_only=False)

        # Construire l'arborescence
        category_map = {c.id: c for c in all_categories}
        root_categories = []

        for cat in all_categories:
            if cat.parent_id is None:
                root_categories.append(self._build_tree_node(cat, category_map))

        return root_categories

    def _build_tree_node(
        self,
        category: EcommerceCategory,
        category_map: dict,
    ) -> dict:
        """Construit un noeud de l'arborescence."""
        children = [
            self._build_tree_node(c, category_map)
            for c in category_map.values()
            if c.parent_id == category.id
        ]

        return {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "is_visible": category.is_visible,
            "sort_order": category.sort_order,
            "children": children,
        }
