"""
AZALS MODULE 15 - Stripe Product & Price Service
==================================================

Gestion des produits et prix Stripe.
"""
from __future__ import annotations


import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import StripePrice, StripeProduct
from app.modules.stripe_integration.schemas import StripePriceCreate, StripeProductCreate

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class ProductPriceService(BaseStripeService[StripeProduct]):
    """Service de gestion des produits et prix Stripe."""

    model = StripeProduct

    def create_product(self, data: StripeProductCreate) -> StripeProduct:
        """
        Crée un produit Stripe.

        Args:
            data: Données du produit

        Returns:
            Produit créé
        """
        # Simuler appel API Stripe
        stripe_product_id = self._generate_stripe_id("prod_")

        product = StripeProduct(
            tenant_id=self.tenant_id,
            stripe_product_id=stripe_product_id,
            product_id=data.product_id,
            plan_id=data.plan_id,
            name=data.name,
            description=data.description,
            active=True,
            images=data.images,
            stripe_metadata=data.metadata,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        logger.info(
            "Stripe product created | tenant=%s product_id=%s name=%s",
            self.tenant_id,
            stripe_product_id,
            data.name,
        )
        return product

    def get_product(self, product_id: int) -> Optional[StripeProduct]:
        """
        Récupère un produit.

        Args:
            product_id: ID du produit

        Returns:
            Produit ou None
        """
        return self._get_by_id(product_id)

    def list_products(self, active_only: bool = True) -> List[StripeProduct]:
        """
        Liste les produits.

        Args:
            active_only: Filtrer les produits actifs

        Returns:
            Liste des produits
        """
        query = self._base_query()
        if active_only:
            query = query.filter(StripeProduct.active == True)
        return query.order_by(StripeProduct.created_at.desc()).all()

    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> Optional[StripeProduct]:
        """
        Met à jour un produit.

        Args:
            product_id: ID du produit
            name: Nouveau nom
            description: Nouvelle description
            active: Nouveau statut

        Returns:
            Produit mis à jour ou None
        """
        product = self.get_product(product_id)
        if not product:
            return None

        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if active is not None:
            product.active = active

        product.updated_at = self._now()
        self.db.commit()
        self.db.refresh(product)
        return product

    def create_price(self, data: StripePriceCreate) -> StripePrice:
        """
        Crée un prix Stripe.

        Args:
            data: Données du prix

        Returns:
            Prix créé

        Raises:
            ValueError: Si produit non trouvé
        """
        product = self.get_product(data.product_id)
        if not product:
            raise ValueError("Produit non trouvé")

        # Simuler appel API Stripe
        stripe_price_id = self._generate_stripe_id("price_")

        price = StripePrice(
            tenant_id=self.tenant_id,
            stripe_price_id=stripe_price_id,
            stripe_product_id=product.id,
            unit_amount=data.unit_amount,
            currency=data.currency.upper(),
            recurring_interval=data.recurring_interval,
            recurring_interval_count=data.recurring_interval_count,
            active=True,
            nickname=data.nickname,
            stripe_metadata=data.metadata,
        )
        self.db.add(price)
        self.db.commit()
        self.db.refresh(price)

        logger.info(
            "Stripe price created | tenant=%s price_id=%s amount=%s currency=%s",
            self.tenant_id,
            stripe_price_id,
            data.unit_amount,
            data.currency,
        )
        return price

    def get_price(self, price_id: int) -> Optional[StripePrice]:
        """
        Récupère un prix.

        Args:
            price_id: ID du prix

        Returns:
            Prix ou None
        """
        return (
            self.db.query(StripePrice)
            .filter(
                StripePrice.tenant_id == self.tenant_id,
                StripePrice.id == price_id,
            )
            .first()
        )

    def list_prices(
        self,
        product_id: Optional[int] = None,
        active_only: bool = True,
    ) -> List[StripePrice]:
        """
        Liste les prix.

        Args:
            product_id: Filtrer par produit
            active_only: Filtrer les prix actifs

        Returns:
            Liste des prix
        """
        query = self.db.query(StripePrice).filter(
            StripePrice.tenant_id == self.tenant_id
        )

        if product_id:
            query = query.filter(StripePrice.stripe_product_id == product_id)
        if active_only:
            query = query.filter(StripePrice.active == True)

        return query.order_by(StripePrice.created_at.desc()).all()

    def deactivate_price(self, price_id: int) -> bool:
        """
        Désactive un prix.

        Args:
            price_id: ID du prix

        Returns:
            True si désactivé
        """
        price = self.get_price(price_id)
        if not price:
            return False

        price.active = False
        price.updated_at = self._now()
        self.db.commit()
        return True
