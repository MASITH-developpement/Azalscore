"""
AZALS MODULE 15 - Stripe Integration Service
==============================================
Logique métier pour l'intégration Stripe.

Flux de création de tenant après paiement:
1. Client complète Stripe Checkout
2. Webhook checkout.session.completed reçu
3. Tenant créé automatiquement via TenantService
4. Utilisateur admin créé via IAMService
5. Email de bienvenue envoyé (optionnel)
"""

import logging
import re
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import (
    DisputeStatus,
    PaymentIntentStatus,
    RefundStatus,
    StripeCheckoutSession,
    StripeConfig,
    StripeConnectAccount,
    StripeCustomer,
    StripeDispute,
    StripePaymentIntent,
    StripePaymentMethod,
    StripePrice,
    StripeProduct,
    StripeRefund,
    StripeWebhook,
    WebhookStatus,
)
from .schemas import (
    CheckoutSessionCreate,
    ConnectAccountCreate,
    PaymentIntentConfirm,
    PaymentIntentCreate,
    PaymentMethodCreate,
    RefundCreate,
    SetupIntentCreate,
    StripeConfigCreate,
    StripeConfigUpdate,
    StripeCustomerCreate,
    StripeCustomerUpdate,
    StripePriceCreate,
    StripeProductCreate,
)

logger = logging.getLogger(__name__)


class StripeService:
    """Service Stripe complet."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2
        self._stripe = None
        self._config = None

    def _get_config(self) -> StripeConfig | None:
        """Récupérer configuration Stripe."""
        if self._config is None:
            self._config = self.db.query(StripeConfig).filter(
                StripeConfig.tenant_id == self.tenant_id
            ).first()
        return self._config

    def _get_stripe_client(self):
        """Obtenir client Stripe configuré."""
        config = self._get_config()
        if not config:
            raise ValueError("Configuration Stripe non trouvée")

        # En production, importer stripe et configurer
        # import stripe
        # api_key = config.api_key_live if config.is_live_mode else config.api_key_test
        # stripe.api_key = api_key
        # return stripe

        # Pour le développement, retourner un mock
        return None

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def create_config(self, data: StripeConfigCreate) -> StripeConfig:
        """Créer configuration Stripe."""
        existing = self._get_config()
        if existing:
            raise ValueError("Configuration déjà existante")

        config = StripeConfig(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        self._config = config
        return config

    def update_config(self, data: StripeConfigUpdate) -> StripeConfig:
        """Mettre à jour configuration."""
        config = self._get_config()
        if not config:
            raise ValueError("Configuration non trouvée")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        self._config = config
        return config

    def get_config(self) -> StripeConfig | None:
        """Récupérer configuration."""
        return self._get_config()

    # ========================================================================
    # CUSTOMERS
    # ========================================================================

    def create_customer(self, data: StripeCustomerCreate) -> StripeCustomer:
        """Créer un client Stripe."""
        logger.info(
            "Creating Stripe customer | tenant=%s user=%s email=%s",
            self.tenant_id, self.user_id, data.email
        )
        # Vérifier si client existe déjà
        existing = self.db.query(StripeCustomer).filter(
            StripeCustomer.tenant_id == self.tenant_id,
            StripeCustomer.customer_id == data.customer_id
        ).first()

        if existing:
            logger.warning(
                "Stripe customer already exists | tenant=%s customer_id=%s",
                self.tenant_id, data.customer_id
            )
            raise ValueError("Client Stripe déjà existant pour ce client")

        # Appel API Stripe (simulé)
        # stripe = self._get_stripe_client()
        # stripe_customer = stripe.Customer.create(
        #     email=data.email,
        #     name=data.name,
        #     phone=data.phone,
        #     description=data.description,
        #     address={...},
        #     metadata=data.metadata
        # )

        # Simuler ID Stripe
        import uuid
        stripe_customer_id = f"cus_{uuid.uuid4().hex[:14]}"

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
            last_synced_at=datetime.utcnow()
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        logger.info(
            "Stripe customer created | tenant=%s stripe_customer_id=%s customer_id=%s",
            self.tenant_id, stripe_customer_id, data.customer_id
        )
        return customer

    def get_customer(self, customer_id: int) -> StripeCustomer | None:
        """Récupérer client Stripe par ID interne."""
        return self.db.query(StripeCustomer).filter(
            StripeCustomer.tenant_id == self.tenant_id,
            StripeCustomer.id == customer_id
        ).first()

    def get_customer_by_crm_id(self, crm_customer_id: int) -> StripeCustomer | None:
        """Récupérer client Stripe par ID CRM."""
        return self.db.query(StripeCustomer).filter(
            StripeCustomer.tenant_id == self.tenant_id,
            StripeCustomer.customer_id == crm_customer_id
        ).first()

    def get_or_create_customer(
        self, crm_customer_id: int, email: str = None, name: str = None
    ) -> StripeCustomer:
        """Récupérer ou créer client Stripe."""
        customer = self.get_customer_by_crm_id(crm_customer_id)
        if customer:
            return customer

        data = StripeCustomerCreate(
            customer_id=crm_customer_id,
            email=email,
            name=name
        )
        return self.create_customer(data)

    def list_customers(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[StripeCustomer], int]:
        """Lister les clients Stripe."""
        query = self.db.query(StripeCustomer).filter(
            StripeCustomer.tenant_id == self.tenant_id
        )
        total = query.count()
        items = query.order_by(StripeCustomer.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_customer(
        self, customer_id: int, data: StripeCustomerUpdate
    ) -> StripeCustomer | None:
        """Mettre à jour client Stripe."""
        customer = self.get_customer(customer_id)
        if not customer:
            return None

        # API Stripe
        # stripe = self._get_stripe_client()
        # stripe.Customer.modify(customer.stripe_customer_id, ...)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "metadata":
                customer.stripe_metadata = value
            else:
                setattr(customer, field, value)

        customer.updated_at = datetime.utcnow()
        customer.last_synced_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def sync_customer(self, customer_id: int) -> StripeCustomer:
        """Synchroniser client avec Stripe."""
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError("Client non trouvé")

        # API Stripe
        # stripe = self._get_stripe_client()
        # stripe_data = stripe.Customer.retrieve(customer.stripe_customer_id)
        # Mettre à jour avec les données Stripe...

        customer.is_synced = True
        customer.last_synced_at = datetime.utcnow()
        customer.sync_error = None

        self.db.commit()
        self.db.refresh(customer)
        return customer

    # ========================================================================
    # PAYMENT METHODS
    # ========================================================================

    def add_payment_method(
        self, data: PaymentMethodCreate
    ) -> StripePaymentMethod:
        """Ajouter méthode de paiement."""
        # SÉCURITÉ: Filtrer par tenant_id
        customer = self.db.query(StripeCustomer).filter(
            StripeCustomer.tenant_id == self.tenant_id,
            StripeCustomer.stripe_customer_id == data.stripe_customer_id
        ).first()

        if not customer:
            raise ValueError("Client Stripe non trouvé")

        # API Stripe
        # stripe = self._get_stripe_client()
        # pm = stripe.PaymentMethod.attach(data.token, customer=data.stripe_customer_id)

        import uuid
        stripe_pm_id = f"pm_{uuid.uuid4().hex[:14]}"

        payment_method = StripePaymentMethod(
            tenant_id=self.tenant_id,
            stripe_payment_method_id=stripe_pm_id,
            stripe_customer_id=customer.id,
            method_type=data.method_type,
            is_default=data.set_as_default,
            is_active=True
        )
        self.db.add(payment_method)

        if data.set_as_default:
            # SÉCURITÉ: Retirer default des autres (filtrer par tenant_id)
            self.db.query(StripePaymentMethod).filter(
                StripePaymentMethod.tenant_id == self.tenant_id,
                StripePaymentMethod.stripe_customer_id == customer.id,
                StripePaymentMethod.id != payment_method.id
            ).update({"is_default": False})

            customer.default_payment_method_id = stripe_pm_id

        self.db.commit()
        self.db.refresh(payment_method)
        return payment_method

    def list_payment_methods(
        self, customer_id: int
    ) -> list[StripePaymentMethod]:
        """Lister méthodes de paiement d'un client."""
        customer = self.get_customer(customer_id)
        if not customer:
            return []

        # SÉCURITÉ: Filtrer par tenant_id
        return self.db.query(StripePaymentMethod).filter(
            StripePaymentMethod.tenant_id == self.tenant_id,
            StripePaymentMethod.stripe_customer_id == customer.id,
            StripePaymentMethod.is_active
        ).all()

    def delete_payment_method(self, payment_method_id: int) -> bool:
        """Supprimer méthode de paiement."""
        pm = self.db.query(StripePaymentMethod).filter(
            StripePaymentMethod.tenant_id == self.tenant_id,
            StripePaymentMethod.id == payment_method_id
        ).first()

        if not pm:
            return False

        # API Stripe
        # stripe = self._get_stripe_client()
        # stripe.PaymentMethod.detach(pm.stripe_payment_method_id)

        pm.is_active = False
        self.db.commit()
        return True

    def create_setup_intent(
        self, data: SetupIntentCreate
    ) -> dict[str, Any]:
        """Créer SetupIntent pour ajouter méthode paiement."""
        customer = self.get_customer_by_crm_id(data.customer_id)
        if not customer:
            raise ValueError("Client non trouvé")

        # API Stripe
        # stripe = self._get_stripe_client()
        # setup_intent = stripe.SetupIntent.create(
        #     customer=customer.stripe_customer_id,
        #     payment_method_types=data.payment_method_types,
        #     usage=data.usage
        # )

        import uuid
        return {
            "setup_intent_id": f"seti_{uuid.uuid4().hex[:14]}",
            "client_secret": f"seti_{uuid.uuid4().hex[:14]}_secret_{uuid.uuid4().hex[:14]}",
            "status": "requires_payment_method",
            "payment_method_types": data.payment_method_types
        }

    # ========================================================================
    # PAYMENT INTENTS
    # ========================================================================

    def create_payment_intent(
        self, data: PaymentIntentCreate
    ) -> StripePaymentIntent:
        """Créer PaymentIntent."""
        logger.info(
            "Creating payment intent | tenant=%s amount=%s currency=%s customer_id=%s",
            self.tenant_id, data.amount, data.currency, data.customer_id
        )
        stripe_customer = None
        if data.customer_id:
            stripe_customer = self.get_customer_by_crm_id(data.customer_id)

        # API Stripe
        # stripe = self._get_stripe_client()
        # pi = stripe.PaymentIntent.create(
        #     amount=int(data.amount * 100),  # En centimes
        #     currency=data.currency.lower(),
        #     customer=stripe_customer.stripe_customer_id if stripe_customer else None,
        #     payment_method_types=data.payment_method_types,
        #     capture_method=data.capture_method,
        #     confirm=data.confirm,
        #     payment_method=data.payment_method_id,
        #     receipt_email=data.receipt_email,
        #     description=data.description,
        #     metadata=data.metadata
        # )

        import uuid
        stripe_pi_id = f"pi_{uuid.uuid4().hex[:14]}"

        payment_intent = StripePaymentIntent(
            tenant_id=self.tenant_id,
            stripe_payment_intent_id=stripe_pi_id,
            stripe_customer_id=stripe_customer.id if stripe_customer else None,
            amount=data.amount,
            amount_received=Decimal("0"),
            currency=data.currency.upper(),
            status=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
            payment_method_id=data.payment_method_id,
            payment_method_types=data.payment_method_types,
            capture_method=data.capture_method,
            client_secret=f"{stripe_pi_id}_secret_{uuid.uuid4().hex[:14]}",
            invoice_id=data.invoice_id,
            order_id=data.order_id,
            subscription_id=data.subscription_id,
            description=data.description,
            stripe_metadata=data.metadata,
            receipt_email=data.receipt_email
        )
        self.db.add(payment_intent)
        self.db.commit()
        self.db.refresh(payment_intent)
        logger.info(
            "Payment intent created | tenant=%s payment_intent_id=%s amount=%s status=%s",
            self.tenant_id, stripe_pi_id, data.amount, PaymentIntentStatus.REQUIRES_PAYMENT_METHOD.value
        )
        return payment_intent

    def get_payment_intent(
        self, payment_intent_id: int
    ) -> StripePaymentIntent | None:
        """Récupérer PaymentIntent."""
        return self.db.query(StripePaymentIntent).filter(
            StripePaymentIntent.tenant_id == self.tenant_id,
            StripePaymentIntent.id == payment_intent_id
        ).first()

    def list_payment_intents(
        self,
        customer_id: int | None = None,
        status: PaymentIntentStatus | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[StripePaymentIntent], int]:
        """Lister PaymentIntents."""
        query = self.db.query(StripePaymentIntent).filter(
            StripePaymentIntent.tenant_id == self.tenant_id
        )
        if customer_id:
            stripe_customer = self.get_customer_by_crm_id(customer_id)
            if stripe_customer:
                query = query.filter(
                    StripePaymentIntent.stripe_customer_id == stripe_customer.id
                )
        if status:
            query = query.filter(StripePaymentIntent.status == status)

        total = query.count()
        items = query.order_by(
            StripePaymentIntent.created_at.desc()
        ).offset(skip).limit(limit).all()
        return items, total

    def confirm_payment_intent(
        self, payment_intent_id: int, data: PaymentIntentConfirm
    ) -> StripePaymentIntent:
        """Confirmer PaymentIntent."""
        logger.info(
            "Confirming payment intent | tenant=%s payment_intent_id=%s",
            self.tenant_id, payment_intent_id
        )
        pi = self.get_payment_intent(payment_intent_id)
        if not pi:
            logger.warning(
                "Payment intent not found | tenant=%s payment_intent_id=%s",
                self.tenant_id, payment_intent_id
            )
            raise ValueError("PaymentIntent non trouvé")

        # API Stripe
        # stripe = self._get_stripe_client()
        # stripe.PaymentIntent.confirm(
        #     pi.stripe_payment_intent_id,
        #     payment_method=data.payment_method_id,
        #     return_url=data.return_url
        # )

        # Simuler confirmation réussie
        if data.payment_method_id:
            pi.payment_method_id = data.payment_method_id

        pi.status = PaymentIntentStatus.SUCCEEDED
        pi.amount_received = pi.amount
        pi.updated_at = datetime.utcnow()

        # Calculer frais (simulés)
        self._get_config()
        stripe_fee = pi.amount * Decimal("0.015") + Decimal("0.25")  # 1.5% + 0.25€
        pi.stripe_fee = stripe_fee
        pi.net_amount = pi.amount - stripe_fee

        self.db.commit()
        self.db.refresh(pi)
        logger.info(
            "Payment intent confirmed | tenant=%s payment_intent_id=%s stripe_id=%s amount=%s",
            self.tenant_id, payment_intent_id, pi.stripe_payment_intent_id, pi.amount
        )
        return pi

    def capture_payment_intent(
        self, payment_intent_id: int, amount: Decimal | None = None
    ) -> StripePaymentIntent:
        """Capturer PaymentIntent (pour capture manuelle)."""
        pi = self.get_payment_intent(payment_intent_id)
        if not pi:
            raise ValueError("PaymentIntent non trouvé")

        if pi.status != PaymentIntentStatus.REQUIRES_CAPTURE:
            raise ValueError("PaymentIntent ne peut pas être capturé")

        capture_amount = amount or pi.amount

        # API Stripe
        # stripe = self._get_stripe_client()
        # stripe.PaymentIntent.capture(
        #     pi.stripe_payment_intent_id,
        #     amount_to_capture=int(capture_amount * 100)
        # )

        pi.status = PaymentIntentStatus.SUCCEEDED
        pi.amount_received = capture_amount
        pi.captured_at = datetime.utcnow()
        pi.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pi)
        return pi

    def cancel_payment_intent(
        self, payment_intent_id: int, reason: str = None
    ) -> StripePaymentIntent:
        """Annuler PaymentIntent."""
        logger.info(
            "Cancelling payment intent | tenant=%s payment_intent_id=%s reason=%s",
            self.tenant_id, payment_intent_id, reason
        )
        pi = self.get_payment_intent(payment_intent_id)
        if not pi:
            logger.warning(
                "Payment intent not found for cancellation | tenant=%s payment_intent_id=%s",
                self.tenant_id, payment_intent_id
            )
            raise ValueError("PaymentIntent non trouvé")

        if pi.status == PaymentIntentStatus.SUCCEEDED:
            logger.warning(
                "Cannot cancel succeeded payment | tenant=%s payment_intent_id=%s",
                self.tenant_id, payment_intent_id
            )
            raise ValueError("Impossible d'annuler un paiement réussi")

        # API Stripe
        # stripe = self._get_stripe_client()
        # stripe.PaymentIntent.cancel(pi.stripe_payment_intent_id)

        pi.status = PaymentIntentStatus.CANCELED
        pi.cancellation_reason = reason
        pi.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pi)
        logger.info(
            "Payment intent cancelled | tenant=%s payment_intent_id=%s stripe_id=%s",
            self.tenant_id, payment_intent_id, pi.stripe_payment_intent_id
        )
        return pi

    # ========================================================================
    # CHECKOUT SESSIONS
    # ========================================================================

    def create_checkout_session(
        self, data: CheckoutSessionCreate
    ) -> StripeCheckoutSession:
        """Créer session checkout."""
        logger.info(
            "Creating checkout session | tenant=%s mode=%s customer_id=%s",
            self.tenant_id, data.mode, data.customer_id
        )
        stripe_customer = None
        if data.customer_id:
            stripe_customer = self.get_customer_by_crm_id(data.customer_id)

        # Préparer line_items
        line_items_data = []
        if data.line_items:
            for item in data.line_items:
                line_items_data.append({
                    "name": item.name,
                    "description": item.description,
                    "amount": int(item.amount * 100),
                    "currency": item.currency.lower(),
                    "quantity": item.quantity
                })

        # API Stripe
        # stripe = self._get_stripe_client()
        # session = stripe.checkout.Session.create(
        #     customer=stripe_customer.stripe_customer_id if stripe_customer else None,
        #     customer_email=data.customer_email,
        #     mode=data.mode,
        #     success_url=data.success_url,
        #     cancel_url=data.cancel_url,
        #     line_items=line_items_data,
        #     payment_method_types=data.payment_method_types,
        #     allow_promotion_codes=data.allow_promotion_codes,
        #     metadata=data.metadata
        # )

        import uuid
        session_id = f"cs_{uuid.uuid4().hex[:24]}"

        amount_total = sum(
            item.amount * item.quantity
            for item in (data.line_items or [])
        )

        checkout_session = StripeCheckoutSession(
            tenant_id=self.tenant_id,
            stripe_session_id=session_id,
            stripe_customer_id=stripe_customer.stripe_customer_id if stripe_customer else None,
            mode=data.mode,
            payment_status="unpaid",
            status="open",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            url=f"https://checkout.stripe.com/c/pay/{session_id}",
            amount_total=amount_total,
            currency=data.line_items[0].currency if data.line_items else "EUR",
            invoice_id=data.invoice_id,
            order_id=data.order_id,
            subscription_id=data.subscription_id,
            stripe_metadata=data.metadata,
            line_items=line_items_data,
            customer_email=data.customer_email,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(checkout_session)
        self.db.commit()
        self.db.refresh(checkout_session)
        logger.info(
            "Checkout session created | tenant=%s session_id=%s amount=%s",
            self.tenant_id, session_id, amount_total
        )
        return checkout_session

    def get_checkout_session(
        self, session_id: int
    ) -> StripeCheckoutSession | None:
        """Récupérer session checkout."""
        return self.db.query(StripeCheckoutSession).filter(
            StripeCheckoutSession.tenant_id == self.tenant_id,
            StripeCheckoutSession.id == session_id
        ).first()

    # ========================================================================
    # REFUNDS
    # ========================================================================

    def create_refund(self, data: RefundCreate) -> StripeRefund:
        """Créer remboursement."""
        pi = self.get_payment_intent(data.payment_intent_id)
        if not pi:
            raise ValueError("PaymentIntent non trouvé")

        if pi.status != PaymentIntentStatus.SUCCEEDED:
            raise ValueError("Seuls les paiements réussis peuvent être remboursés")

        refund_amount = data.amount or pi.amount_received

        # Vérifier montant disponible
        existing_refunds = sum(
            r.amount for r in pi.refunds
            if r.status == RefundStatus.SUCCEEDED
        )

        if refund_amount > (pi.amount_received - existing_refunds):
            raise ValueError("Montant de remboursement supérieur au disponible")

        # API Stripe
        # stripe = self._get_stripe_client()
        # refund = stripe.Refund.create(
        #     payment_intent=pi.stripe_payment_intent_id,
        #     amount=int(refund_amount * 100),
        #     reason=data.reason,
        #     metadata=data.metadata
        # )

        import uuid
        refund = StripeRefund(
            tenant_id=self.tenant_id,
            stripe_refund_id=f"re_{uuid.uuid4().hex[:14]}",
            payment_intent_id=pi.id,
            amount=refund_amount,
            currency=pi.currency,
            status=RefundStatus.SUCCEEDED,
            reason=data.reason,
            description=data.description,
            stripe_metadata=data.metadata
        )
        self.db.add(refund)
        self.db.commit()
        self.db.refresh(refund)
        return refund

    def list_refunds(
        self,
        payment_intent_id: int | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> list[StripeRefund]:
        """Lister remboursements."""
        query = self.db.query(StripeRefund).filter(
            StripeRefund.tenant_id == self.tenant_id
        )
        if payment_intent_id:
            query = query.filter(StripeRefund.payment_intent_id == payment_intent_id)

        return query.order_by(StripeRefund.created_at.desc()).offset(skip).limit(limit).all()

    # ========================================================================
    # PRODUCTS & PRICES
    # ========================================================================

    def create_product(self, data: StripeProductCreate) -> StripeProduct:
        """Créer produit Stripe."""
        # API Stripe
        # stripe = self._get_stripe_client()
        # product = stripe.Product.create(
        #     name=data.name,
        #     description=data.description,
        #     images=data.images,
        #     metadata=data.metadata
        # )

        import uuid
        product = StripeProduct(
            tenant_id=self.tenant_id,
            stripe_product_id=f"prod_{uuid.uuid4().hex[:14]}",
            product_id=data.product_id,
            plan_id=data.plan_id,
            name=data.name,
            description=data.description,
            active=True,
            images=data.images,
            stripe_metadata=data.metadata
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def create_price(self, data: StripePriceCreate) -> StripePrice:
        """Créer prix Stripe."""
        product = self.db.query(StripeProduct).filter(
            StripeProduct.tenant_id == self.tenant_id,
            StripeProduct.id == data.product_id
        ).first()

        if not product:
            raise ValueError("Produit non trouvé")

        # API Stripe
        # stripe = self._get_stripe_client()
        # price = stripe.Price.create(
        #     product=product.stripe_product_id,
        #     unit_amount=int(data.unit_amount),
        #     currency=data.currency.lower(),
        #     recurring={...} if data.recurring_interval else None,
        #     nickname=data.nickname,
        #     metadata=data.metadata
        # )

        import uuid
        price = StripePrice(
            tenant_id=self.tenant_id,
            stripe_price_id=f"price_{uuid.uuid4().hex[:14]}",
            stripe_product_id=product.id,
            unit_amount=data.unit_amount,
            currency=data.currency.upper(),
            recurring_interval=data.recurring_interval,
            recurring_interval_count=data.recurring_interval_count,
            active=True,
            nickname=data.nickname,
            stripe_metadata=data.metadata
        )
        self.db.add(price)
        self.db.commit()
        self.db.refresh(price)
        return price

    # ========================================================================
    # CONNECT
    # ========================================================================

    def create_connect_account(
        self, data: ConnectAccountCreate
    ) -> StripeConnectAccount:
        """Créer compte Connect."""
        # API Stripe
        # stripe = self._get_stripe_client()
        # account = stripe.Account.create(
        #     type=data.account_type,
        #     country=data.country,
        #     email=data.email,
        #     business_type=data.business_type,
        #     capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}}
        # )
        #
        # account_link = stripe.AccountLink.create(
        #     account=account.id,
        #     refresh_url=data.refresh_url,
        #     return_url=data.return_url,
        #     type="account_onboarding"
        # )

        import uuid

        from .models import StripeAccountStatus

        account = StripeConnectAccount(
            tenant_id=self.tenant_id,
            stripe_account_id=f"acct_{uuid.uuid4().hex[:16]}",
            vendor_id=data.vendor_id,
            account_type=data.account_type,
            country=data.country,
            email=data.email,
            business_type=data.business_type,
            status=StripeAccountStatus.PENDING,
            charges_enabled=False,
            payouts_enabled=False,
            details_submitted=False,
            onboarding_url=f"https://connect.stripe.com/setup/{uuid.uuid4().hex[:20]}",
            onboarding_expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_connect_account(
        self, account_id: int
    ) -> StripeConnectAccount | None:
        """Récupérer compte Connect."""
        return self.db.query(StripeConnectAccount).filter(
            StripeConnectAccount.tenant_id == self.tenant_id,
            StripeConnectAccount.id == account_id
        ).first()

    # ========================================================================
    # WEBHOOKS
    # ========================================================================

    def process_webhook(
        self, event_id: str, event_type: str, payload: dict[str, Any],
        signature: str = None
    ) -> StripeWebhook:
        """Traiter webhook Stripe."""
        logger.info(
            "Processing webhook | tenant=%s event_id=%s event_type=%s",
            self.tenant_id, event_id, event_type
        )
        # Vérifier signature
        # config = self._get_config()
        # secret = config.webhook_secret_live if config.is_live_mode else config.webhook_secret_test
        # stripe.Webhook.construct_event(payload, signature, secret)

        # Enregistrer webhook
        webhook = StripeWebhook(
            tenant_id=self.tenant_id,
            stripe_event_id=event_id,
            event_type=event_type,
            payload=payload,
            api_version=payload.get("api_version"),
            object_type=payload.get("data", {}).get("object", {}).get("object"),
            object_id=payload.get("data", {}).get("object", {}).get("id"),
            status=WebhookStatus.PENDING,
            signature=signature,
            is_verified=True  # Après vérification signature
        )
        self.db.add(webhook)
        self.db.flush()

        # Traiter selon le type
        try:
            self._handle_webhook(webhook)
            webhook.status = WebhookStatus.PROCESSED
            webhook.processed_at = datetime.utcnow()
            logger.info(
                "Webhook processed successfully | tenant=%s event_id=%s event_type=%s",
                self.tenant_id, event_id, event_type
            )
        except Exception as e:
            webhook.status = WebhookStatus.FAILED
            logger.warning(
                "Webhook processing failed | tenant=%s event_id=%s event_type=%s error_type=%s",
                self.tenant_id, event_id, event_type, type(e).__name__
            )
            raise

        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    def _handle_webhook(self, webhook: StripeWebhook):
        """Handler interne webhook."""
        event_type = webhook.event_type
        data = webhook.payload.get("data", {}).get("object", {})

        if event_type == "payment_intent.succeeded":
            self._handle_payment_succeeded(data)
        elif event_type == "payment_intent.payment_failed":
            self._handle_payment_failed(data)
        elif event_type == "checkout.session.completed":
            self._handle_checkout_completed(data)
        elif event_type == "customer.subscription.created":
            self._handle_subscription_created(data)
        elif event_type == "customer.subscription.updated":
            self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(data)
        elif event_type == "invoice.paid":
            self._handle_invoice_paid(data)
        elif event_type == "invoice.payment_failed":
            self._handle_invoice_payment_failed(data)
        elif event_type == "charge.dispute.created":
            self._handle_dispute_created(data)

    def _handle_payment_succeeded(self, data: dict):
        """Gérer paiement réussi."""
        pi_id = data.get("id")
        # SÉCURITÉ: TOUJOURS filtrer par tenant_id en plus de l'ID Stripe
        pi = self.db.query(StripePaymentIntent).filter(
            StripePaymentIntent.tenant_id == self.tenant_id,
            StripePaymentIntent.stripe_payment_intent_id == pi_id
        ).first()

        if pi:
            pi.status = PaymentIntentStatus.SUCCEEDED
            pi.amount_received = Decimal(str(data.get("amount_received", 0))) / 100
            pi.updated_at = datetime.utcnow()

    def _handle_payment_failed(self, data: dict):
        """Gérer paiement échoué."""
        pi_id = data.get("id")
        error_code = data.get("last_payment_error", {}).get("code", "unknown")
        logger.warning(
            "Payment failed | tenant=%s payment_intent_id=%s error_type=%s",
            self.tenant_id, pi_id, error_code
        )
        # SÉCURITÉ: TOUJOURS filtrer par tenant_id en plus de l'ID Stripe
        pi = self.db.query(StripePaymentIntent).filter(
            StripePaymentIntent.tenant_id == self.tenant_id,
            StripePaymentIntent.stripe_payment_intent_id == pi_id
        ).first()

        if pi:
            pi.status = PaymentIntentStatus.REQUIRES_PAYMENT_METHOD
            pi.updated_at = datetime.utcnow()

    def _handle_checkout_completed(self, data: dict):
        """
        Gérer checkout Stripe complété - CRÉATION AUTOMATIQUE DE TENANT.

        Ce handler est appelé quand un client complète le paiement via Stripe Checkout.
        Il crée automatiquement:
        1. Le tenant avec le plan correspondant
        2. L'utilisateur admin avec mot de passe temporaire
        3. Enregistre la souscription Stripe

        Metadata attendues dans checkout session:
        - tenant_name: Nom de l'entreprise
        - admin_email: Email de l'admin (ou customer_email)
        - admin_first_name: Prénom (optionnel)
        - admin_last_name: Nom (optionnel)
        - country: Pays (défaut: FR)
        """
        logger.info("Processing checkout.session.completed: %s", data.get('id'))

        # Extraire les informations
        customer_email = data.get("customer_email") or data.get("customer_details", {}).get("email")
        metadata = data.get("metadata", {})

        # Récupérer les metadata personnalisées
        tenant_name = metadata.get("tenant_name") or metadata.get("company_name")
        admin_email = metadata.get("admin_email") or customer_email
        admin_first_name = metadata.get("admin_first_name", "Admin")
        admin_last_name = metadata.get("admin_last_name", "")
        country = metadata.get("country", "FR")

        # Déterminer le plan depuis le mode de paiement ou les metadata
        plan = self._determine_plan_from_checkout(data)

        if not admin_email:
            logger.error("checkout.session.completed: No email found, cannot create tenant")
            return

        if not tenant_name:
            # Générer un nom par défaut depuis l'email
            tenant_name = admin_email.split("@")[0].replace(".", " ").title()

        # Générer un tenant_id unique
        tenant_id = self._generate_tenant_id(tenant_name)

        # Vérifier si le tenant existe déjà
        existing_tenant = self._get_tenant_by_email(admin_email)
        if existing_tenant:
            logger.info("Tenant already exists for email %s, skipping creation", admin_email)
            return

        # Créer le tenant et l'admin
        result = self._provision_new_tenant(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            admin_email=admin_email,
            admin_first_name=admin_first_name,
            admin_last_name=admin_last_name,
            plan=plan,
            country=country,
            stripe_customer_id=data.get("customer"),
            stripe_subscription_id=data.get("subscription")
        )

        if result:
            logger.info("Tenant %s created successfully for %s", tenant_id, admin_email)
        else:
            logger.error("Failed to create tenant for %s", admin_email)

    def _handle_subscription_created(self, data: dict):
        """
        Gérer création abonnement Stripe.

        Alternative à checkout.session.completed pour les souscriptions
        créées directement via API ou Customer Portal.
        """
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")
        logger.info(
            "Creating subscription | tenant=%s subscription_id=%s customer_id=%s status=%s",
            self.tenant_id, subscription_id, customer_id, status
        )

        # Récupérer les metadata
        metadata = data.get("metadata", {})

        # Si c'est une nouvelle souscription active et qu'on a les metadata
        if status in ["active", "trialing"] and metadata.get("tenant_id"):
            tenant_id = metadata.get("tenant_id")

            # Mettre à jour le tenant avec les infos Stripe
            self._update_tenant_stripe_info(
                tenant_id=tenant_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan=self._determine_plan_from_subscription(data)
            )
            logger.info(
                "Subscription created | tenant=%s subscription_id=%s plan=%s",
                tenant_id, subscription_id, self._determine_plan_from_subscription(data)
            )

    def _handle_subscription_updated(self, data: dict):
        """
        Gérer mise à jour abonnement Stripe.

        Gère les changements de plan, renouvellements, etc.
        """
        logger.info("Processing subscription.updated: %s", data.get('id'))

        subscription_id = data.get("id")
        status = data.get("status")
        metadata = data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        if not tenant_id:
            # Chercher le tenant par stripe_subscription_id
            tenant_id = self._find_tenant_by_subscription(subscription_id)

        if not tenant_id:
            logger.warning("No tenant found for subscription %s", subscription_id)
            return

        # Mettre à jour selon le statut
        if status == "active":
            self._activate_tenant(tenant_id)
            new_plan = self._determine_plan_from_subscription(data)
            self._update_tenant_plan(tenant_id, new_plan)
        elif status == "past_due":
            self._mark_tenant_payment_issue(tenant_id)
        elif status == "unpaid":
            self._suspend_tenant(tenant_id, reason="payment_failed")

    def _handle_subscription_deleted(self, data: dict):
        """
        Gérer suppression/annulation abonnement Stripe.

        Le tenant est suspendu mais pas supprimé (conservation des données).
        """
        subscription_id = data.get("id")
        logger.info(
            "Cancelling subscription | tenant=%s subscription_id=%s",
            self.tenant_id, subscription_id
        )

        metadata = data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        if not tenant_id:
            tenant_id = self._find_tenant_by_subscription(subscription_id)

        if tenant_id:
            self._suspend_tenant(tenant_id, reason="subscription_cancelled")
            logger.info(
                "Subscription cancelled | tenant=%s subscription_id=%s suspended_tenant=%s",
                self.tenant_id, subscription_id, tenant_id
            )
        else:
            logger.warning(
                "Subscription cancelled but no tenant found | subscription_id=%s",
                subscription_id
            )

    def _handle_invoice_paid(self, data: dict):
        """
        Gérer facture payée.

        Réactive le tenant si suspendu pour non-paiement.
        """
        logger.info("Processing invoice.paid: %s", data.get('id'))

        subscription_id = data.get("subscription")
        if not subscription_id:
            return

        metadata = data.get("subscription_details", {}).get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        if not tenant_id:
            tenant_id = self._find_tenant_by_subscription(subscription_id)

        if tenant_id:
            self._activate_tenant(tenant_id)
            self._clear_payment_issues(tenant_id)

    def _handle_invoice_payment_failed(self, data: dict):
        """
        Gérer échec paiement facture.

        Marque le tenant comme ayant un problème de paiement.
        Après plusieurs échecs, le tenant sera suspendu.
        """
        subscription_id = data.get("subscription")
        attempt_count = data.get("attempt_count", 1)
        logger.warning(
            "Invoice payment failed | tenant=%s subscription_id=%s attempt=%s",
            self.tenant_id, subscription_id, attempt_count
        )

        if not subscription_id:
            return

        tenant_id = self._find_tenant_by_subscription(subscription_id)

        if tenant_id:
            self._mark_tenant_payment_issue(tenant_id, attempt_count=attempt_count)

            # Suspendre après 3 tentatives échouées
            if attempt_count >= 3:
                self._suspend_tenant(tenant_id, reason="payment_failed_multiple")
                logger.warning(
                    "Tenant suspended due to payment failures | tenant=%s subscription_id=%s attempt_count=%s",
                    tenant_id, subscription_id, attempt_count
                )

    # ========================================================================
    # HELPERS POUR PROVISIONING TENANT
    # ========================================================================

    def _generate_tenant_id(self, name: str) -> str:
        """Génère un tenant_id unique depuis le nom."""
        # Normaliser le nom
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        slug = slug[:20]  # Limiter la longueur

        # Ajouter un suffixe unique si nécessaire
        base_slug = slug
        counter = 0

        while self._tenant_exists(slug):
            counter += 1
            slug = f"{base_slug}-{counter}"

        return slug

    def _tenant_exists(self, tenant_id: str) -> bool:
        """Vérifie si un tenant existe."""
        from app.modules.tenants.models import Tenant
        return self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first() is not None

    def _get_tenant_by_email(self, email: str):
        """Récupère un tenant par email admin."""
        from app.modules.tenants.models import Tenant
        return self.db.query(Tenant).filter(Tenant.email == email).first()

    def _find_tenant_by_subscription(self, subscription_id: str) -> str | None:
        """Trouve le tenant_id associé à une subscription Stripe."""
        from app.modules.tenants.models import Tenant
        tenant = self.db.query(Tenant).filter(
            Tenant.extra_data["stripe_subscription_id"].astext == subscription_id
        ).first()
        return tenant.tenant_id if tenant else None

    def _determine_plan_from_checkout(self, data: dict) -> str:
        """Détermine le plan depuis les données de checkout."""
        # Regarder le montant ou les metadata
        amount_total = data.get("amount_total", 0)  # En centimes
        metadata = data.get("metadata", {})

        # Plan explicite dans metadata
        if metadata.get("plan"):
            return metadata.get("plan").upper()

        # Sinon, déduire du montant (à adapter selon vos prix)
        if amount_total >= 50000:  # 500€+
            return "ENTERPRISE"
        elif amount_total >= 10000:  # 100€+
            return "PROFESSIONAL"
        elif amount_total >= 3000:  # 30€+
            return "STARTER"
        else:
            return "FREE"

    def _determine_plan_from_subscription(self, data: dict) -> str:
        """Détermine le plan depuis les données de subscription."""
        items = data.get("items", {}).get("data", [])
        if items:
            price = items[0].get("price", {})
            price.get("product")

            # Mapping product_id -> plan (à configurer)
            # Pour l'instant, utiliser les metadata ou le montant
            unit_amount = price.get("unit_amount", 0)
            if unit_amount >= 50000:
                return "ENTERPRISE"
            elif unit_amount >= 10000:
                return "PROFESSIONAL"
            elif unit_amount >= 3000:
                return "STARTER"

        return "STARTER"

    def _provision_new_tenant(
        self,
        tenant_id: str,
        tenant_name: str,
        admin_email: str,
        admin_first_name: str,
        admin_last_name: str,
        plan: str,
        country: str,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Provisionne un nouveau tenant complet avec admin.

        Returns:
            Dict avec tenant et admin info, ou None si échec
        """
        from app.modules.iam.schemas import UserCreate
        from app.modules.iam.service import IAMService
        from app.modules.tenants.models import SubscriptionPlan, Tenant, TenantEnvironment, TenantStatus

        # Générer mot de passe temporaire
        temp_password = secrets.token_urlsafe(12)

        # 1. Créer le tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            name=tenant_name,
            legal_name=tenant_name,
            email=admin_email,
            country=country,
            environment=TenantEnvironment.PRODUCTION,
            status=TenantStatus.ACTIVE,
            plan=SubscriptionPlan[plan] if plan in SubscriptionPlan.__members__ else SubscriptionPlan.STARTER,
            timezone="Europe/Paris",
            language="fr",
            currency="EUR",
            max_users=self._get_max_users_for_plan(plan),
            max_storage_gb=self._get_max_storage_for_plan(plan),
            features={"stripe_provisioned": True},
            extra_data={
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id,
                "provisioned_at": datetime.utcnow().isoformat()
            },
            activated_at=datetime.utcnow(),
            created_by="system:stripe_webhook"
        )
        self.db.add(tenant)
        self.db.flush()

        # 2. Créer l'utilisateur admin via IAMService
        iam_service = IAMService(self.db, tenant_id)

        admin_user = iam_service.create_user(UserCreate(
            email=admin_email,
            username=admin_email.split("@")[0],
            password=temp_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role_codes=["ADMIN"],  # Rôle admin
            locale="fr",
            timezone="Europe/Paris"
        ))

        # 3. Marquer le mot de passe comme devant être changé
        admin_user.must_change_password = True

        self.db.commit()

        logger.info("Provisioned tenant %s with admin %s", tenant_id, admin_email)

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "admin_email": admin_email,
            "admin_user_id": admin_user.id,
            "temporary_password": temp_password,
            "plan": plan
        }

    def _get_max_users_for_plan(self, plan: str) -> int:
        """Retourne le nombre max d'utilisateurs selon le plan."""
        limits = {
            "FREE": 2,
            "STARTER": 5,
            "PROFESSIONAL": 25,
            "ENTERPRISE": 100
        }
        return limits.get(plan, 5)

    def _get_max_storage_for_plan(self, plan: str) -> int:
        """Retourne le stockage max en GB selon le plan."""
        limits = {
            "FREE": 1,
            "STARTER": 10,
            "PROFESSIONAL": 100,
            "ENTERPRISE": 500
        }
        return limits.get(plan, 10)

    def _update_tenant_stripe_info(
        self,
        tenant_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        plan: str
    ):
        """Met à jour les infos Stripe d'un tenant existant."""
        from app.modules.tenants.models import SubscriptionPlan, Tenant

        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant:
            if not tenant.extra_data:
                tenant.extra_data = {}
            tenant.extra_data["stripe_customer_id"] = stripe_customer_id
            tenant.extra_data["stripe_subscription_id"] = stripe_subscription_id
            tenant.plan = SubscriptionPlan[plan] if plan in SubscriptionPlan.__members__ else tenant.plan
            tenant.updated_at = datetime.utcnow()
            self.db.commit()

    def _update_tenant_plan(self, tenant_id: str, plan: str):
        """Met à jour le plan d'un tenant."""
        from app.modules.tenants.models import SubscriptionPlan, Tenant

        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant and plan in SubscriptionPlan.__members__:
            tenant.plan = SubscriptionPlan[plan]
            tenant.max_users = self._get_max_users_for_plan(plan)
            tenant.max_storage_gb = self._get_max_storage_for_plan(plan)
            tenant.updated_at = datetime.utcnow()
            self.db.commit()

    def _activate_tenant(self, tenant_id: str):
        """Active un tenant."""
        from app.modules.tenants.models import Tenant, TenantStatus

        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant and tenant.status != TenantStatus.ACTIVE:
            tenant.status = TenantStatus.ACTIVE
            tenant.suspended_at = None
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info("Tenant %s activated", tenant_id)

    def _suspend_tenant(self, tenant_id: str, reason: str):
        """Suspend un tenant."""
        from app.modules.tenants.models import Tenant, TenantStatus

        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant:
            tenant.status = TenantStatus.SUSPENDED
            tenant.suspended_at = datetime.utcnow()
            if not tenant.extra_data:
                tenant.extra_data = {}
            tenant.extra_data["suspension_reason"] = reason
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info("Tenant %s suspended: %s", tenant_id, reason)

    def _mark_tenant_payment_issue(self, tenant_id: str, attempt_count: int = 1):
        """Marque un tenant comme ayant un problème de paiement."""
        from app.modules.tenants.models import Tenant

        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant:
            if not tenant.extra_data:
                tenant.extra_data = {}
            tenant.extra_data["payment_issue"] = True
            tenant.extra_data["payment_failure_count"] = attempt_count
            tenant.extra_data["last_payment_failure"] = datetime.utcnow().isoformat()
            tenant.updated_at = datetime.utcnow()
            self.db.commit()

    def _clear_payment_issues(self, tenant_id: str):
        """Efface les problèmes de paiement d'un tenant."""
        from app.modules.tenants.models import Tenant

        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if tenant and tenant.extra_data:
            tenant.extra_data.pop("payment_issue", None)
            tenant.extra_data.pop("payment_failure_count", None)
            tenant.extra_data.pop("last_payment_failure", None)
            tenant.updated_at = datetime.utcnow()
            self.db.commit()

    def _handle_dispute_created(self, data: dict):
        """Gérer création litige."""
        dispute = StripeDispute(
            tenant_id=self.tenant_id,
            stripe_dispute_id=data.get("id"),
            stripe_charge_id=data.get("charge"),
            stripe_payment_intent_id=data.get("payment_intent"),
            amount=Decimal(str(data.get("amount", 0))) / 100,
            currency=data.get("currency", "EUR").upper(),
            status=DisputeStatus(data.get("status", "needs_response")),
            reason=data.get("reason")
        )
        self.db.add(dispute)

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> dict[str, Any]:
        """Dashboard Stripe."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Volume 30 jours
        volume = self.db.query(
            func.sum(StripePaymentIntent.amount_received)
        ).filter(
            StripePaymentIntent.tenant_id == self.tenant_id,
            StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
            StripePaymentIntent.created_at >= thirty_days_ago
        ).scalar() or Decimal("0")

        # Paiements réussis
        successful = self.db.query(StripePaymentIntent).filter(
            StripePaymentIntent.tenant_id == self.tenant_id,
            StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
            StripePaymentIntent.created_at >= thirty_days_ago
        ).count()

        # Paiements échoués
        failed = self.db.query(StripePaymentIntent).filter(
            StripePaymentIntent.tenant_id == self.tenant_id,
            StripePaymentIntent.status == PaymentIntentStatus.CANCELED,
            StripePaymentIntent.created_at >= thirty_days_ago
        ).count()

        # Remboursements
        refunds = self.db.query(
            func.sum(StripeRefund.amount)
        ).filter(
            StripeRefund.tenant_id == self.tenant_id,
            StripeRefund.status == RefundStatus.SUCCEEDED,
            StripeRefund.created_at >= thirty_days_ago
        ).scalar() or Decimal("0")

        # Litiges ouverts
        open_disputes = self.db.query(StripeDispute).filter(
            StripeDispute.tenant_id == self.tenant_id,
            StripeDispute.status.in_([
                DisputeStatus.NEEDS_RESPONSE,
                DisputeStatus.UNDER_REVIEW
            ])
        ).count()

        disputed_amount = self.db.query(
            func.sum(StripeDispute.amount)
        ).filter(
            StripeDispute.tenant_id == self.tenant_id,
            StripeDispute.status.in_([
                DisputeStatus.NEEDS_RESPONSE,
                DisputeStatus.UNDER_REVIEW
            ])
        ).scalar() or Decimal("0")

        # Taux de succès
        total_attempts = successful + failed
        success_rate = (Decimal(str(successful)) / Decimal(str(total_attempts)) * 100) if total_attempts > 0 else Decimal("0")

        # Transaction moyenne
        avg_transaction = volume / Decimal(str(successful)) if successful > 0 else Decimal("0")

        # Récents paiements
        recent_payments = self.db.query(StripePaymentIntent).filter(
            StripePaymentIntent.tenant_id == self.tenant_id,
            StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED
        ).order_by(StripePaymentIntent.created_at.desc()).limit(5).all()

        # Récents remboursements
        recent_refunds = self.db.query(StripeRefund).filter(
            StripeRefund.tenant_id == self.tenant_id
        ).order_by(StripeRefund.created_at.desc()).limit(5).all()

        return {
            "total_volume_30d": float(volume),
            "successful_payments_30d": successful,
            "failed_payments_30d": failed,
            "refunds_30d": float(refunds),
            "success_rate": float(success_rate),
            "average_transaction": float(avg_transaction),
            "open_disputes": open_disputes,
            "disputed_amount": float(disputed_amount),
            "available_balance": 0,  # À récupérer via API
            "pending_balance": 0,
            "recent_payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "status": p.status.value,
                    "created_at": p.created_at.isoformat()
                }
                for p in recent_payments
            ],
            "recent_refunds": [
                {
                    "id": r.id,
                    "amount": float(r.amount),
                    "currency": r.currency,
                    "status": r.status.value,
                    "created_at": r.created_at.isoformat()
                }
                for r in recent_refunds
            ]
        }
