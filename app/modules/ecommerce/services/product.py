"""
AZALS MODULE 12 - E-Commerce Product Service
==============================================

Gestion des produits et variantes.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import or_

from app.modules.ecommerce.models import (
    EcommerceProduct,
    ProductStatus,
    ProductVariant,
)
from app.modules.ecommerce.schemas import (
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class ProductService(BaseEcommerceService[EcommerceProduct]):
    """Service de gestion des produits."""

    model = EcommerceProduct

    def create(self, data: ProductCreate) -> EcommerceProduct:
        """Crée un nouveau produit."""
        logger.info(
            "Creating product | tenant=%s user=%s sku=%s name=%s",
            self.tenant_id,
            self.user_id,
            data.sku,
            data.name,
        )

        product_data = data.model_dump()

        # Convertir les images en JSON
        if product_data.get("images"):
            product_data["images"] = [
                img.model_dump() if hasattr(img, "model_dump") else img
                for img in product_data["images"]
            ]

        product = EcommerceProduct(
            tenant_id=self.tenant_id,
            status=ProductStatus.DRAFT,
            **product_data,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        logger.info("Product created | product_id=%s sku=%s", product.id, product.sku)
        return product

    def get(self, product_id: int) -> Optional[EcommerceProduct]:
        """Récupère un produit par ID."""
        return self._get_by_id(product_id)

    def get_by_slug(self, slug: str) -> Optional[EcommerceProduct]:
        """Récupère un produit par slug."""
        return self._base_query().filter(EcommerceProduct.slug == slug).first()

    def get_by_sku(self, sku: str) -> Optional[EcommerceProduct]:
        """Récupère un produit par SKU."""
        return self._base_query().filter(EcommerceProduct.sku == sku).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None,
        status: Optional[ProductStatus] = None,
        search: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock_only: bool = False,
        featured_only: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[EcommerceProduct], int]:
        """Liste les produits avec filtres et pagination."""
        query = self._base_query()

        if category_id:
            query = query.filter(
                EcommerceProduct.category_ids.contains([category_id])
            )

        if status:
            query = query.filter(EcommerceProduct.status == status)

        if search:
            search_filter = or_(
                EcommerceProduct.name.ilike(f"%{search}%"),
                EcommerceProduct.sku.ilike(f"%{search}%"),
                EcommerceProduct.description.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)

        if min_price is not None:
            query = query.filter(EcommerceProduct.price >= min_price)

        if max_price is not None:
            query = query.filter(EcommerceProduct.price <= max_price)

        if in_stock_only:
            query = query.filter(EcommerceProduct.stock_quantity > 0)

        if featured_only:
            query = query.filter(EcommerceProduct.is_featured == True)

        sort_column = getattr(
            EcommerceProduct,
            sort_by,
            EcommerceProduct.created_at,
        )

        return self._list_paginated(
            query,
            page,
            page_size,
            sort_column,
            sort_order == "desc",
        )

    def update(
        self,
        product_id: int,
        data: ProductUpdate,
    ) -> Optional[EcommerceProduct]:
        """Met à jour un produit."""
        product = self.get(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "images" in update_data and update_data["images"]:
            update_data["images"] = [
                img.model_dump() if hasattr(img, "model_dump") else img
                for img in update_data["images"]
            ]

        return self._update(product, update_data)

    def delete(self, product_id: int) -> bool:
        """Archive un produit (soft delete)."""
        product = self.get(product_id)
        if not product:
            return False

        return self._soft_delete(product, "status", ProductStatus.ARCHIVED)

    def publish(self, product_id: int) -> Optional[EcommerceProduct]:
        """Publie un produit."""
        product = self.get(product_id)
        if not product:
            return None

        product.status = ProductStatus.ACTIVE
        product.published_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_stock(
        self,
        product_id: int,
        quantity_change: int,
        variant_id: Optional[int] = None,
    ) -> bool:
        """
        Met à jour le stock d'un produit ou variante.

        Args:
            product_id: ID du produit
            quantity_change: Changement de quantité (+/-)
            variant_id: ID de la variante (optionnel)

        Returns:
            True si mise à jour réussie
        """
        logger.info(
            "Updating stock | tenant=%s product_id=%s variant_id=%s change=%d",
            self.tenant_id,
            product_id,
            variant_id,
            quantity_change,
        )

        if variant_id:
            variant = (
                self.db.query(ProductVariant)
                .filter(
                    ProductVariant.tenant_id == self.tenant_id,
                    ProductVariant.id == variant_id,
                )
                .first()
            )
            if variant:
                old_qty = variant.stock_quantity
                variant.stock_quantity += quantity_change
                self.db.commit()
                logger.info(
                    "Stock updated | variant_id=%s old=%d new=%d",
                    variant_id,
                    old_qty,
                    variant.stock_quantity,
                )
                return True
        else:
            product = self.get(product_id)
            if product:
                old_qty = product.stock_quantity
                product.stock_quantity += quantity_change

                if product.stock_quantity <= 0:
                    product.status = ProductStatus.OUT_OF_STOCK
                    logger.warning(
                        "Product out of stock | product_id=%s sku=%s",
                        product_id,
                        product.sku,
                    )

                self.db.commit()
                logger.info(
                    "Stock updated | product_id=%s old=%d new=%d",
                    product_id,
                    old_qty,
                    product.stock_quantity,
                )
                return True

        return False

    # =========================================================================
    # VARIANTS
    # =========================================================================

    def create_variant(self, data: VariantCreate) -> ProductVariant:
        """Crée une variante de produit."""
        variant = ProductVariant(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(variant)
        self.db.commit()
        self.db.refresh(variant)
        return variant

    def get_variants(self, product_id: int) -> List[ProductVariant]:
        """Liste les variantes d'un produit."""
        return (
            self.db.query(ProductVariant)
            .filter(
                ProductVariant.tenant_id == self.tenant_id,
                ProductVariant.product_id == product_id,
            )
            .order_by(ProductVariant.position)
            .all()
        )

    def update_variant(
        self,
        variant_id: int,
        data: VariantUpdate,
    ) -> Optional[ProductVariant]:
        """Met à jour une variante."""
        variant = (
            self.db.query(ProductVariant)
            .filter(
                ProductVariant.tenant_id == self.tenant_id,
                ProductVariant.id == variant_id,
            )
            .first()
        )

        if not variant:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(variant, field, value)

        self.db.commit()
        self.db.refresh(variant)
        return variant

    def delete_variant(self, variant_id: int) -> bool:
        """Supprime une variante."""
        variant = (
            self.db.query(ProductVariant)
            .filter(
                ProductVariant.tenant_id == self.tenant_id,
                ProductVariant.id == variant_id,
            )
            .first()
        )

        if not variant:
            return False

        self.db.delete(variant)
        self.db.commit()
        return True
