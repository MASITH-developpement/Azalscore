"""
AZALS MODULE 15 - Stripe Customer Service
===========================================

Gestion des clients Stripe.
"""
from __future__ import annotations


import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import StripeCustomer
from app.modules.stripe_integration.schemas import (
    StripeCustomerCreate,
    StripeCustomerUpdate,
)

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class CustomerService(BaseStripeService[StripeCustomer]):
    """Service de gestion des clients Stripe."""

    model = StripeCustomer

    def create(self, data: StripeCustomerCreate) -> StripeCustomer:
        """
        Crée un client Stripe.

        Args:
            data: Données du client

        Returns:
            Client créé

        Raises:
            ValueError: Si client existe déjà
        """
        logger.info(
            "Creating Stripe customer | tenant=%s user=%s email=%s",
            self.tenant_id,
            self.user_id,
            data.email,
        )

        # Vérifier si client existe déjà
        existing = (
            self._base_query()
            .filter(StripeCustomer.customer_id == data.customer_id)
            .first()
        )

        if existing:
            logger.warning(
                "Stripe customer already exists | tenant=%s customer_id=%s",
                self.tenant_id,
                data.customer_id,
            )
            raise ValueError("Client Stripe déjà existant pour ce client")

        # Simuler appel API Stripe
        stripe_customer_id = self._generate_stripe_id("cus_")

        customer = StripeCustomer(
            tenant_id=self.tenant_id,
            stripe_customer_id=stripe_customer_id,
            customer_id=data.customer_id,
            email=data.email,
            name=data.name,
            phone=data.phone,
            description=data.description,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            postal_code=data.postal_code,
            country=data.country,
            tax_exempt=data.tax_exempt,
            stripe_metadata=data.metadata,
            is_synced=True,
            last_synced_at=self._now(),
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        logger.info(
            "Stripe customer created | tenant=%s stripe_customer_id=%s customer_id=%s",
            self.tenant_id,
            stripe_customer_id,
            data.customer_id,
        )
        return customer

    def get(self, customer_id: int) -> Optional[StripeCustomer]:
        """
        Récupère un client Stripe par ID interne.

        Args:
            customer_id: ID interne du client

        Returns:
            Client ou None
        """
        return self._get_by_id(customer_id)

    def get_by_crm_id(self, crm_customer_id: int) -> Optional[StripeCustomer]:
        """
        Récupère un client Stripe par ID CRM.

        Args:
            crm_customer_id: ID du client dans le CRM

        Returns:
            Client Stripe ou None
        """
        return (
            self._base_query()
            .filter(StripeCustomer.customer_id == crm_customer_id)
            .first()
        )

    def get_or_create(
        self,
        crm_customer_id: int,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> StripeCustomer:
        """
        Récupère ou crée un client Stripe.

        Args:
            crm_customer_id: ID CRM du client
            email: Email (optionnel, pour création)
            name: Nom (optionnel, pour création)

        Returns:
            Client Stripe existant ou nouveau
        """
        customer = self.get_by_crm_id(crm_customer_id)
        if customer:
            return customer

        data = StripeCustomerCreate(
            customer_id=crm_customer_id,
            email=email,
            name=name,
        )
        return self.create(data)

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[StripeCustomer], int]:
        """
        Liste les clients Stripe.

        Args:
            skip: Offset pour pagination
            limit: Limite de résultats

        Returns:
            Tuple (liste clients, total)
        """
        query = self._base_query()
        total = query.count()
        items = (
            query.order_by(StripeCustomer.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def update(
        self,
        customer_id: int,
        data: StripeCustomerUpdate,
    ) -> Optional[StripeCustomer]:
        """
        Met à jour un client Stripe.

        Args:
            customer_id: ID interne du client
            data: Données de mise à jour

        Returns:
            Client mis à jour ou None
        """
        customer = self.get(customer_id)
        if not customer:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "metadata":
                customer.stripe_metadata = value
            else:
                setattr(customer, field, value)

        customer.updated_at = self._now()
        customer.last_synced_at = self._now()
        self.db.commit()
        self.db.refresh(customer)

        logger.info(
            "Stripe customer updated | tenant=%s customer_id=%s",
            self.tenant_id,
            customer_id,
        )
        return customer

    def sync(self, customer_id: int) -> StripeCustomer:
        """
        Synchronise un client avec Stripe.

        Args:
            customer_id: ID interne du client

        Returns:
            Client synchronisé

        Raises:
            ValueError: Si client non trouvé
        """
        customer = self.get(customer_id)
        if not customer:
            raise ValueError("Client non trouvé")

        # En production: appeler API Stripe et mettre à jour
        customer.is_synced = True
        customer.last_synced_at = self._now()
        customer.sync_error = None

        self.db.commit()
        self.db.refresh(customer)

        logger.info(
            "Stripe customer synced | tenant=%s customer_id=%s",
            self.tenant_id,
            customer_id,
        )
        return customer
