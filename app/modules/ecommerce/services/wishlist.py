"""
AZALS MODULE 12 - E-Commerce Wishlist Service
===============================================

Gestion des listes de souhaits.
"""

import logging
from typing import List, Optional

from app.modules.ecommerce.models import EcommerceProduct, Wishlist, WishlistItem
from app.modules.ecommerce.schemas import WishlistItemAdd

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class WishlistService(BaseEcommerceService[Wishlist]):
    """Service de gestion des wishlists."""

    model = Wishlist

    def get_or_create(self, customer_id: int) -> Wishlist:
        """Récupère ou crée une wishlist pour un client."""
        wishlist = (
            self._base_query()
            .filter(Wishlist.customer_id == customer_id)
            .first()
        )

        if not wishlist:
            wishlist = Wishlist(
                tenant_id=self.tenant_id,
                customer_id=customer_id,
            )
            self.db.add(wishlist)
            self.db.commit()
            self.db.refresh(wishlist)

        return wishlist

    def get_items(self, customer_id: int) -> List[WishlistItem]:
        """Liste les articles de la wishlist d'un client."""
        wishlist = self.get_or_create(customer_id)

        return (
            self.db.query(WishlistItem)
            .filter(
                WishlistItem.tenant_id == self.tenant_id,
                WishlistItem.wishlist_id == wishlist.id,
            )
            .all()
        )

    def add_item(
        self,
        customer_id: int,
        data: WishlistItemAdd,
    ) -> WishlistItem:
        """Ajoute un article à la wishlist."""
        wishlist = self.get_or_create(customer_id)

        # Vérifier si déjà présent
        existing = (
            self.db.query(WishlistItem)
            .filter(
                WishlistItem.tenant_id == self.tenant_id,
                WishlistItem.wishlist_id == wishlist.id,
                WishlistItem.product_id == data.product_id,
            )
            .first()
        )

        if existing:
            return existing

        # Récupérer le prix actuel du produit
        product = (
            self.db.query(EcommerceProduct)
            .filter(
                EcommerceProduct.tenant_id == self.tenant_id,
                EcommerceProduct.id == data.product_id,
            )
            .first()
        )

        item = WishlistItem(
            tenant_id=self.tenant_id,
            wishlist_id=wishlist.id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            added_price=product.price if product else None,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        logger.info(
            "Wishlist item added | customer_id=%s product_id=%s",
            customer_id,
            data.product_id,
        )
        return item

    def remove_item(self, customer_id: int, product_id: int) -> bool:
        """Retire un article de la wishlist."""
        wishlist = self.get_or_create(customer_id)

        item = (
            self.db.query(WishlistItem)
            .filter(
                WishlistItem.tenant_id == self.tenant_id,
                WishlistItem.wishlist_id == wishlist.id,
                WishlistItem.product_id == product_id,
            )
            .first()
        )

        if not item:
            return False

        self.db.delete(item)
        self.db.commit()

        logger.info(
            "Wishlist item removed | customer_id=%s product_id=%s",
            customer_id,
            product_id,
        )
        return True

    def clear(self, customer_id: int) -> bool:
        """Vide la wishlist d'un client."""
        wishlist = self.get_or_create(customer_id)

        self.db.query(WishlistItem).filter(
            WishlistItem.tenant_id == self.tenant_id,
            WishlistItem.wishlist_id == wishlist.id,
        ).delete()

        self.db.commit()
        return True

    def is_in_wishlist(
        self,
        customer_id: int,
        product_id: int,
    ) -> bool:
        """Vérifie si un produit est dans la wishlist."""
        wishlist = (
            self._base_query()
            .filter(Wishlist.customer_id == customer_id)
            .first()
        )

        if not wishlist:
            return False

        return (
            self.db.query(WishlistItem)
            .filter(
                WishlistItem.tenant_id == self.tenant_id,
                WishlistItem.wishlist_id == wishlist.id,
                WishlistItem.product_id == product_id,
            )
            .first()
            is not None
        )

    def get_count(self, customer_id: int) -> int:
        """Retourne le nombre d'articles dans la wishlist."""
        wishlist = (
            self._base_query()
            .filter(Wishlist.customer_id == customer_id)
            .first()
        )

        if not wishlist:
            return 0

        return (
            self.db.query(WishlistItem)
            .filter(
                WishlistItem.tenant_id == self.tenant_id,
                WishlistItem.wishlist_id == wishlist.id,
            )
            .count()
        )
