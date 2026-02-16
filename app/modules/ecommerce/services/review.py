"""
AZALS MODULE 12 - E-Commerce Review Service
=============================================

Gestion des avis produits.
"""

import logging
from typing import List, Optional

from sqlalchemy import desc

from app.modules.ecommerce.models import ProductReview
from app.modules.ecommerce.schemas import ReviewCreate

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class ReviewService(BaseEcommerceService[ProductReview]):
    """Service de gestion des avis produits."""

    model = ProductReview

    def create(
        self,
        data: ReviewCreate,
        customer_id: Optional[int] = None,
    ) -> ProductReview:
        """Crée un avis produit."""
        review = ProductReview(
            tenant_id=self.tenant_id,
            product_id=data.product_id,
            customer_id=customer_id,
            rating=data.rating,
            title=data.title,
            content=data.content,
            author_name=data.author_name,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        logger.info(
            "Review created | tenant=%s product_id=%s rating=%d",
            self.tenant_id,
            data.product_id,
            data.rating,
        )
        return review

    def get(self, review_id: int) -> Optional[ProductReview]:
        """Récupère un avis."""
        return self._get_by_id(review_id)

    def get_product_reviews(
        self,
        product_id: int,
        approved_only: bool = True,
    ) -> List[ProductReview]:
        """Liste les avis d'un produit."""
        query = self._base_query().filter(
            ProductReview.product_id == product_id
        )

        if approved_only:
            query = query.filter(ProductReview.is_approved == True)

        return query.order_by(desc(ProductReview.created_at)).all()

    def get_customer_reviews(
        self,
        customer_id: int,
    ) -> List[ProductReview]:
        """Liste les avis d'un client."""
        return (
            self._base_query()
            .filter(ProductReview.customer_id == customer_id)
            .order_by(desc(ProductReview.created_at))
            .all()
        )

    def approve(self, review_id: int) -> bool:
        """Approuve un avis."""
        review = self.get(review_id)
        if not review:
            return False

        review.is_approved = True
        self.db.commit()

        logger.info("Review approved | review_id=%s", review_id)
        return True

    def reject(self, review_id: int) -> bool:
        """Rejette un avis."""
        review = self.get(review_id)
        if not review:
            return False

        review.is_approved = False
        self.db.commit()

        logger.info("Review rejected | review_id=%s", review_id)
        return True

    def delete(self, review_id: int) -> bool:
        """Supprime un avis."""
        review = self.get(review_id)
        if not review:
            return False

        self.db.delete(review)
        self.db.commit()
        return True

    def get_pending_reviews(self) -> List[ProductReview]:
        """Liste les avis en attente de modération."""
        return (
            self._base_query()
            .filter(ProductReview.is_approved == False)
            .order_by(desc(ProductReview.created_at))
            .all()
        )

    def get_product_rating(self, product_id: int) -> dict:
        """
        Calcule les statistiques de notation d'un produit.

        Returns:
            Dictionnaire avec average, count, distribution
        """
        reviews = self.get_product_reviews(product_id, approved_only=True)

        if not reviews:
            return {
                "average": 0,
                "count": 0,
                "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            }

        total = sum(r.rating for r in reviews)
        count = len(reviews)
        average = round(total / count, 1)

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            distribution[review.rating] += 1

        return {
            "average": average,
            "count": count,
            "distribution": distribution,
        }
