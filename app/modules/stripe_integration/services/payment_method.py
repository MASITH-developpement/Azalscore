"""
AZALS MODULE 15 - Stripe Payment Method Service
=================================================

Gestion des méthodes de paiement Stripe.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import StripeCustomer, StripePaymentMethod
from app.modules.stripe_integration.schemas import PaymentMethodCreate, SetupIntentCreate

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class PaymentMethodService(BaseStripeService[StripePaymentMethod]):
    """Service de gestion des méthodes de paiement Stripe."""

    model = StripePaymentMethod

    def add(self, data: PaymentMethodCreate) -> StripePaymentMethod:
        """
        Ajoute une méthode de paiement à un client.

        Args:
            data: Données de la méthode de paiement

        Returns:
            Méthode de paiement créée

        Raises:
            ValueError: Si client non trouvé
        """
        # Récupérer le client Stripe
        customer = (
            self.db.query(StripeCustomer)
            .filter(
                StripeCustomer.tenant_id == self.tenant_id,
                StripeCustomer.stripe_customer_id == data.stripe_customer_id,
            )
            .first()
        )

        if not customer:
            raise ValueError("Client Stripe non trouvé")

        # Simuler appel API Stripe
        stripe_pm_id = self._generate_stripe_id("pm_")

        payment_method = StripePaymentMethod(
            tenant_id=self.tenant_id,
            stripe_payment_method_id=stripe_pm_id,
            stripe_customer_id=customer.id,
            method_type=data.method_type,
            is_default=data.set_as_default,
            is_active=True,
        )
        self.db.add(payment_method)

        if data.set_as_default:
            # Retirer default des autres méthodes
            self.db.query(StripePaymentMethod).filter(
                StripePaymentMethod.tenant_id == self.tenant_id,
                StripePaymentMethod.stripe_customer_id == customer.id,
                StripePaymentMethod.id != payment_method.id,
            ).update({"is_default": False})

            customer.default_payment_method_id = stripe_pm_id

        self.db.commit()
        self.db.refresh(payment_method)

        logger.info(
            "Payment method added | tenant=%s customer_id=%s pm_id=%s",
            self.tenant_id,
            customer.id,
            stripe_pm_id,
        )
        return payment_method

    def list_for_customer(self, customer_id: int) -> List[StripePaymentMethod]:
        """
        Liste les méthodes de paiement d'un client.

        Args:
            customer_id: ID interne du client Stripe

        Returns:
            Liste des méthodes de paiement actives
        """
        customer = (
            self.db.query(StripeCustomer)
            .filter(
                StripeCustomer.tenant_id == self.tenant_id,
                StripeCustomer.id == customer_id,
            )
            .first()
        )

        if not customer:
            return []

        return (
            self.db.query(StripePaymentMethod)
            .filter(
                StripePaymentMethod.tenant_id == self.tenant_id,
                StripePaymentMethod.stripe_customer_id == customer.id,
                StripePaymentMethod.is_active == True,
            )
            .all()
        )

    def delete(self, payment_method_id: int) -> bool:
        """
        Supprime (désactive) une méthode de paiement.

        Args:
            payment_method_id: ID de la méthode de paiement

        Returns:
            True si supprimée
        """
        pm = (
            self._base_query()
            .filter(StripePaymentMethod.id == payment_method_id)
            .first()
        )

        if not pm:
            return False

        # En production: détacher via API Stripe
        pm.is_active = False
        self.db.commit()

        logger.info(
            "Payment method deleted | tenant=%s pm_id=%s",
            self.tenant_id,
            payment_method_id,
        )
        return True

    def create_setup_intent(self, data: SetupIntentCreate) -> Dict[str, Any]:
        """
        Crée un SetupIntent pour ajouter une méthode de paiement.

        Args:
            data: Données du SetupIntent

        Returns:
            Informations du SetupIntent (id, client_secret, etc.)

        Raises:
            ValueError: Si client non trouvé
        """
        from .customer import CustomerService

        customer_service = CustomerService(self.db, self.tenant_id, self.user_id)
        customer = customer_service.get_by_crm_id(data.customer_id)

        if not customer:
            raise ValueError("Client non trouvé")

        # Simuler appel API Stripe
        seti_id = self._generate_stripe_id("seti_")
        secret = self._generate_stripe_id("secret_")

        logger.info(
            "SetupIntent created | tenant=%s customer_id=%s seti_id=%s",
            self.tenant_id,
            data.customer_id,
            seti_id,
        )

        return {
            "setup_intent_id": seti_id,
            "client_secret": f"{seti_id}_{secret}",
            "status": "requires_payment_method",
            "payment_method_types": data.payment_method_types,
        }

    def set_default(self, customer_id: int, payment_method_id: int) -> bool:
        """
        Définit une méthode de paiement comme défaut.

        Args:
            customer_id: ID du client Stripe
            payment_method_id: ID de la méthode de paiement

        Returns:
            True si modifié
        """
        customer = (
            self.db.query(StripeCustomer)
            .filter(
                StripeCustomer.tenant_id == self.tenant_id,
                StripeCustomer.id == customer_id,
            )
            .first()
        )

        if not customer:
            return False

        pm = (
            self._base_query()
            .filter(
                StripePaymentMethod.id == payment_method_id,
                StripePaymentMethod.stripe_customer_id == customer.id,
            )
            .first()
        )

        if not pm:
            return False

        # Retirer default des autres
        self.db.query(StripePaymentMethod).filter(
            StripePaymentMethod.tenant_id == self.tenant_id,
            StripePaymentMethod.stripe_customer_id == customer.id,
        ).update({"is_default": False})

        pm.is_default = True
        customer.default_payment_method_id = pm.stripe_payment_method_id
        self.db.commit()

        logger.info(
            "Default payment method set | tenant=%s customer_id=%s pm_id=%s",
            self.tenant_id,
            customer_id,
            payment_method_id,
        )
        return True
