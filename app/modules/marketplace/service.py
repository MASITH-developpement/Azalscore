"""
AZALS - Module Marketplace - Service
====================================
Service pour le site marchand avec provisioning automatique.
"""

import logging
import secrets
import string
from datetime import datetime
from decimal import Decimal

import bcrypt
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import (
    BillingCycle,
    CommercialPlan,
    DiscountCode,
    Order,
    OrderStatus,
    PaymentMethod,
    PlanType,
    WebhookEvent,
)
from .schemas import (
    CheckoutRequest,
    CheckoutResponse,
    DiscountCodeResponse,
    MarketplaceStats,
    TenantProvisionResponse,
)

logger = logging.getLogger(__name__)


class MarketplaceService:
    """Service marketplace."""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # PLANS
    # =========================================================================

    def get_plans(self, active_only: bool = True) -> list[CommercialPlan]:
        """Récupère les plans disponibles."""
        query = self.db.query(CommercialPlan)
        if active_only:
            query = query.filter(CommercialPlan.is_active)
        return query.order_by(CommercialPlan.sort_order).all()

    def get_plan(self, plan_id: str) -> CommercialPlan | None:
        """Récupère un plan par ID."""
        return self.db.query(CommercialPlan).filter(CommercialPlan.id == plan_id).first()

    def get_plan_by_code(self, code: str) -> CommercialPlan | None:
        """Récupère un plan par code."""
        return self.db.query(CommercialPlan).filter(
            CommercialPlan.code == code,
            CommercialPlan.is_active
        ).first()

    def seed_default_plans(self):
        """Crée les plans par défaut (Essentiel/Pro/Entreprise)."""
        default_plans = [
            {
                "code": "essentiel",
                "name": "Essentiel",
                "plan_type": PlanType.ESSENTIEL,
                "description": "Pour les petites entreprises et indépendants",
                "price_monthly": Decimal("49.00"),
                "price_annual": Decimal("490.00"),  # 2 mois offerts
                "max_users": 3,
                "max_storage_gb": 10,
                "max_documents_month": 100,
                "max_api_calls_month": 5000,
                "modules_included": ["commercial", "invoicing", "treasury"],
                "features": ["support_email", "backup_weekly"],
                "trial_days": 14,
                "sort_order": 1
            },
            {
                "code": "pro",
                "name": "Pro",
                "plan_type": PlanType.PRO,
                "description": "Pour les PME en croissance",
                "price_monthly": Decimal("149.00"),
                "price_annual": Decimal("1490.00"),
                "max_users": 10,
                "max_storage_gb": 50,
                "max_documents_month": 500,
                "max_api_calls_month": 50000,
                "modules_included": [
                    "commercial", "invoicing", "treasury", "accounting",
                    "hr", "projects", "inventory", "helpdesk"
                ],
                "features": [
                    "support_email", "support_phone", "backup_daily",
                    "api_access", "custom_reports"
                ],
                "trial_days": 14,
                "is_featured": True,
                "sort_order": 2
            },
            {
                "code": "entreprise",
                "name": "Entreprise",
                "plan_type": PlanType.ENTREPRISE,
                "description": "Pour les grandes entreprises avec besoins avancés",
                "price_monthly": Decimal("399.00"),
                "price_annual": Decimal("3990.00"),
                "max_users": 50,
                "max_storage_gb": 200,
                "max_documents_month": 2000,
                "max_api_calls_month": 500000,
                "modules_included": [
                    "commercial", "invoicing", "treasury", "accounting",
                    "hr", "projects", "inventory", "helpdesk",
                    "production", "quality", "bi", "automation"
                ],
                "features": [
                    "support_email", "support_phone", "support_priority",
                    "backup_daily", "api_access", "custom_reports",
                    "sla_4h", "dedicated_account_manager", "custom_integrations"
                ],
                "trial_days": 30,
                "sort_order": 3
            }
        ]

        for plan_data in default_plans:
            existing = self.get_plan_by_code(plan_data["code"])
            if not existing:
                plan = CommercialPlan(**plan_data)
                self.db.add(plan)

        self.db.commit()

    # =========================================================================
    # CHECKOUT
    # =========================================================================

    def create_checkout(self, data: CheckoutRequest) -> CheckoutResponse:
        """Crée une session de checkout."""
        # Récupérer le plan
        plan = self.get_plan_by_code(data.plan_code)
        if not plan:
            raise ValueError(f"Plan '{data.plan_code}' non trouvé")

        # Calculer les montants
        subtotal = plan.price_monthly if data.billing_cycle == BillingCycle.MONTHLY else plan.price_annual

        # Appliquer code promo
        discount_amount = Decimal("0.00")
        if data.discount_code:
            discount_result = self.validate_discount_code(
                data.discount_code, data.plan_code, subtotal
            )
            if discount_result.valid:
                discount_amount = discount_result.final_discount

        # Calculer TVA (FR: 20%)
        taxable_amount = subtotal - discount_amount
        tax_rate = Decimal("20.00")
        tax_amount = taxable_amount * (tax_rate / Decimal("100"))
        total = taxable_amount + tax_amount

        # Générer numéro de commande
        order_number = self._generate_order_number()

        # Créer la commande
        order = Order(
            order_number=order_number,
            status=OrderStatus.PAYMENT_PENDING,
            plan_id=plan.id,
            plan_code=plan.code,
            billing_cycle=data.billing_cycle,
            customer_email=data.customer_email,
            customer_name=data.customer_name,
            company_name=data.company_name,
            company_siret=data.company_siret,
            phone=data.phone,
            billing_address_line1=data.billing_address_line1,
            billing_address_line2=data.billing_address_line2,
            billing_city=data.billing_city,
            billing_postal_code=data.billing_postal_code,
            billing_country=data.billing_country,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            discount_code=data.discount_code,
            total=total,
            payment_method=data.payment_method,
            source="website"
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        # Créer le paiement selon la méthode
        payment_intent_secret = None
        checkout_url = None
        instructions = None

        if data.payment_method == PaymentMethod.CARD:
            # Stripe Payment Intent (à implémenter avec l'API Stripe)
            payment_intent_secret = self._create_stripe_payment_intent(order)
        elif data.payment_method == PaymentMethod.SEPA:
            # SEPA Direct Debit
            payment_intent_secret = self._create_stripe_sepa_payment(order)
        elif data.payment_method == PaymentMethod.PAYPAL:
            # PayPal (à implémenter)
            checkout_url = f"/payment/paypal/{order.id}"
        elif data.payment_method == PaymentMethod.BANK_TRANSFER:
            # Virement bancaire
            instructions = self._get_bank_transfer_instructions(order)

        return CheckoutResponse(
            order_id=str(order.id),
            order_number=order.order_number,
            status=order.status,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total=order.total,
            currency=order.currency,
            payment_intent_client_secret=payment_intent_secret,
            checkout_url=checkout_url,
            instructions=instructions
        )

    def _generate_order_number(self) -> str:
        """Génère un numéro de commande unique."""
        now = datetime.utcnow()
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"CMD-{now.strftime('%Y%m%d')}-{random_part}"

    def _create_stripe_payment_intent(self, order: Order) -> str | None:
        """Crée un PaymentIntent Stripe."""
        import os
        try:
            import stripe
            stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

            if not stripe.api_key:
                logger.warning("STRIPE_SECRET_KEY non configurée")
                return None

            intent = stripe.PaymentIntent.create(
                amount=int(order.total * 100),  # En centimes
                currency=order.currency.lower(),
                payment_method_types=["card"],
                metadata={
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "customer_email": order.customer_email
                },
                description=f"Commande {order.order_number} - Plan {order.plan_code}",
                receipt_email=order.customer_email
            )
            order.payment_intent_id = intent.id
            self.db.commit()
            logger.info(f"PaymentIntent {intent.id} créé pour commande {order.order_number}")
            return intent.client_secret

        except ImportError:
            logger.error("Module stripe non installé")
            return None
        except Exception as e:
            logger.error(f"Erreur création PaymentIntent Stripe: {e}")
            return None

    def _create_stripe_sepa_payment(self, order: Order) -> str | None:
        """Crée un paiement SEPA via Stripe."""
        import os
        try:
            import stripe
            stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

            if not stripe.api_key:
                logger.warning("STRIPE_SECRET_KEY non configurée")
                return None

            intent = stripe.PaymentIntent.create(
                amount=int(order.total * 100),
                currency=order.currency.lower(),
                payment_method_types=["sepa_debit"],
                metadata={
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "customer_email": order.customer_email
                },
                description=f"Commande {order.order_number} - Plan {order.plan_code}"
            )
            order.payment_intent_id = intent.id
            self.db.commit()
            logger.info(f"SEPA PaymentIntent {intent.id} créé pour commande {order.order_number}")
            return intent.client_secret

        except ImportError:
            logger.error("Module stripe non installé")
            return None
        except Exception as e:
            logger.error(f"Erreur création PaymentIntent SEPA: {e}")
            return None

    def _get_bank_transfer_instructions(self, order: Order) -> str:
        """Instructions pour virement bancaire."""
        return f"""
Virement bancaire - Commande {order.order_number}

Montant: {order.total} {order.currency}
IBAN: FR76 1234 5678 9012 3456 7890 123
BIC: AZALSFR2A
Bénéficiaire: AZALSCORE SAS

Référence: {order.order_number}
(Merci d'indiquer cette référence dans votre virement)

Votre compte sera activé sous 48h après réception du virement.
"""

    # =========================================================================
    # CODES PROMO
    # =========================================================================

    def validate_discount_code(
        self, code: str, plan_code: str, order_amount: Decimal
    ) -> DiscountCodeResponse:
        """Valide un code promo."""
        discount = self.db.query(DiscountCode).filter(
            DiscountCode.code == code.upper(),
            DiscountCode.is_active
        ).first()

        if not discount:
            return DiscountCodeResponse(
                code=code, valid=False, message="Code promo invalide"
            )

        now = datetime.utcnow()

        # Vérifier dates de validité
        if discount.starts_at and discount.starts_at > now:
            return DiscountCodeResponse(
                code=code, valid=False, message="Code promo pas encore actif"
            )
        if discount.expires_at and discount.expires_at < now:
            return DiscountCodeResponse(
                code=code, valid=False, message="Code promo expiré"
            )

        # Vérifier limite d'utilisations
        if discount.max_uses and discount.used_count >= discount.max_uses:
            return DiscountCodeResponse(
                code=code, valid=False, message="Code promo épuisé"
            )

        # Vérifier plans applicables
        if discount.applicable_plans and plan_code not in discount.applicable_plans:
            return DiscountCodeResponse(
                code=code, valid=False, message="Code non valide pour ce plan"
            )

        # Vérifier montant minimum
        if discount.min_order_amount and order_amount < discount.min_order_amount:
            return DiscountCodeResponse(
                code=code, valid=False,
                message=f"Montant minimum requis: {discount.min_order_amount}€"
            )

        # Calculer la réduction
        if discount.discount_type == "percent":
            final_discount = order_amount * (discount.discount_value / Decimal("100"))
            if discount.max_discount and final_discount > discount.max_discount:
                final_discount = discount.max_discount
        else:
            final_discount = min(discount.discount_value, order_amount)

        return DiscountCodeResponse(
            code=code,
            valid=True,
            discount_type=discount.discount_type,
            discount_value=discount.discount_value,
            final_discount=final_discount,
            message=f"Réduction de {final_discount}€ appliquée"
        )

    # =========================================================================
    # PROVISIONING
    # =========================================================================

    def provision_tenant_for_order(self, order_id: str) -> TenantProvisionResponse:
        """Provisionne un tenant suite à un paiement confirmé."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Commande non trouvée")

        if order.status != OrderStatus.PAID:
            raise ValueError("Commande non payée")

        if order.tenant_id:
            raise ValueError("Tenant déjà créé pour cette commande")

        # Générer ID tenant
        tenant_id = self._generate_tenant_id(order.company_name or order.customer_name)

        # Générer mot de passe temporaire
        temp_password = self._generate_temp_password()
        password_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()

        # Créer le tenant et l'utilisateur admin
        order.status = OrderStatus.PROVISIONING
        self.db.commit()

        try:
            # Créer le tenant via le service tenants
            self._create_tenant(
                tenant_id=tenant_id,
                company_name=order.company_name or order.customer_name,
                plan_code=order.plan_code,
                admin_email=order.customer_email,
                admin_name=order.customer_name,
                password_hash=password_hash
            )

            # Mettre à jour la commande
            order.tenant_id = tenant_id
            order.tenant_created_at = datetime.utcnow()
            order.status = OrderStatus.COMPLETED
            order.completed_at = datetime.utcnow()
            self.db.commit()

            # Envoyer email de bienvenue
            welcome_sent = self._send_welcome_email(order, temp_password)

            return TenantProvisionResponse(
                tenant_id=tenant_id,
                admin_email=order.customer_email,
                login_url=f"https://app.azalscore.com/login?tenant={tenant_id}",
                temporary_password=temp_password,
                welcome_email_sent=welcome_sent
            )

        except Exception as e:
            order.status = OrderStatus.FAILED
            order.notes = f"Erreur provisioning: {str(e)}"
            self.db.commit()
            raise

    def _generate_tenant_id(self, name: str) -> str:
        """Génère un ID tenant unique."""
        import re
        # Nettoyer le nom
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())[:20]
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        return f"{clean_name}-{random_suffix}"

    def _generate_temp_password(self) -> str:
        """Génère un mot de passe temporaire sécurisé."""
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(alphabet) for _ in range(16))

    def _create_tenant(
        self,
        tenant_id: str,
        company_name: str,
        plan_code: str,
        admin_email: str,
        admin_name: str,
        password_hash: str
    ):
        """Crée un tenant dans la base de données."""
        from sqlalchemy import text

        # Créer le tenant
        self.db.execute(text("""
            INSERT INTO tenants (
                tenant_id, name, company_name, plan, status,
                country, timezone, created_at
            ) VALUES (
                :tenant_id, :name, :company_name, :plan, 'active',
                'FR', 'Europe/Paris', NOW()
            )
        """), {
            "tenant_id": tenant_id,
            "name": company_name,
            "company_name": company_name,
            "plan": plan_code
        })

        # Créer l'utilisateur admin
        import uuid
        user_id = str(uuid.uuid4())
        self.db.execute(text("""
            INSERT INTO users (
                id, tenant_id, email, password_hash, name,
                role, is_active, email_verified, created_at
            ) VALUES (
                :id, :tenant_id, :email, :password_hash, :name,
                'DIRIGEANT', true, true, NOW()
            )
        """), {
            "id": user_id,
            "tenant_id": tenant_id,
            "email": admin_email,
            "password_hash": password_hash,
            "name": admin_name
        })

        self.db.commit()
        logger.info(f"Tenant {tenant_id} créé avec admin {admin_email}")

    def _send_welcome_email(self, order: Order, temp_password: str) -> bool:
        """Envoie l'email de bienvenue."""
        # TODO: Intégrer avec le module email
        logger.info(f"Email de bienvenue envoyé à {order.customer_email}")
        return True

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    def process_stripe_webhook(self, event_id: str, event_type: str, payload: dict, signature: str):
        """Traite un webhook Stripe."""
        # Vérifier si déjà traité
        existing = self.db.query(WebhookEvent).filter(
            WebhookEvent.event_id == event_id
        ).first()
        if existing:
            return existing

        # Enregistrer l'événement
        webhook = WebhookEvent(
            provider="stripe",
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            signature=signature,
            status="processing"
        )
        self.db.add(webhook)
        self.db.commit()

        try:
            if event_type == "payment_intent.succeeded":
                self._handle_payment_succeeded(payload, webhook)
            elif event_type == "payment_intent.payment_failed":
                self._handle_payment_failed(payload, webhook)
            elif event_type == "checkout.session.completed":
                self._handle_checkout_completed(payload, webhook)

            webhook.status = "processed"
            webhook.processed_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            webhook.status = "failed"
            webhook.error_message = str(e)
            webhook.retry_count += 1
            self.db.commit()
            raise

        return webhook

    def _handle_payment_succeeded(self, payload: dict, webhook: WebhookEvent):
        """Traite un paiement réussi."""
        payment_intent_id = payload.get("data", {}).get("object", {}).get("id")
        if not payment_intent_id:
            return

        order = self.db.query(Order).filter(
            Order.payment_intent_id == payment_intent_id
        ).first()

        if order and order.status == OrderStatus.PAYMENT_PENDING:
            order.status = OrderStatus.PAID
            order.payment_status = "succeeded"
            order.paid_at = datetime.utcnow()
            webhook.order_id = order.id
            self.db.commit()

            # Provisionner le tenant automatiquement
            try:
                self.provision_tenant_for_order(str(order.id))
            except Exception as e:
                logger.error(f"Erreur provisioning auto: {e}")

    def _handle_payment_failed(self, payload: dict, webhook: WebhookEvent):
        """Traite un paiement échoué."""
        payment_intent_id = payload.get("data", {}).get("object", {}).get("id")
        if not payment_intent_id:
            return

        order = self.db.query(Order).filter(
            Order.payment_intent_id == payment_intent_id
        ).first()

        if order:
            order.status = OrderStatus.FAILED
            order.payment_status = "failed"
            webhook.order_id = order.id
            self.db.commit()

    def _handle_checkout_completed(self, payload: dict, webhook: WebhookEvent):
        """Traite un checkout Stripe complété."""
        pass

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_stats(self) -> MarketplaceStats:
        """Statistiques marketplace."""
        from datetime import timedelta

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Commandes complétées
        completed = self.db.query(Order).filter(
            Order.status == OrderStatus.COMPLETED
        )

        total_orders = completed.count()
        total_revenue = self.db.query(func.sum(Order.total)).filter(
            Order.status == OrderStatus.COMPLETED
        ).scalar() or Decimal("0")

        orders_today = completed.filter(Order.completed_at >= today_start).count()
        revenue_today = self.db.query(func.sum(Order.total)).filter(
            Order.status == OrderStatus.COMPLETED,
            Order.completed_at >= today_start
        ).scalar() or Decimal("0")

        orders_month = completed.filter(Order.completed_at >= month_start).count()
        revenue_month = self.db.query(func.sum(Order.total)).filter(
            Order.status == OrderStatus.COMPLETED,
            Order.completed_at >= month_start
        ).scalar() or Decimal("0")

        # Taux de conversion (30 derniers jours)
        all_orders_30d = self.db.query(Order).filter(
            Order.created_at >= now - timedelta(days=30)
        ).count()
        completed_30d = completed.filter(
            Order.completed_at >= now - timedelta(days=30)
        ).count()
        conversion_rate = (completed_30d / all_orders_30d * 100) if all_orders_30d > 0 else 0

        # Panier moyen
        avg_order_value = (total_revenue / total_orders) if total_orders > 0 else Decimal("0")

        # Par plan
        by_plan = {}
        for plan in [PlanType.ESSENTIEL, PlanType.PRO, PlanType.ENTREPRISE]:
            count = completed.filter(Order.plan_code == plan.value).count()
            by_plan[plan.value] = count

        # Par cycle
        by_billing_cycle = {}
        for cycle in [BillingCycle.MONTHLY, BillingCycle.ANNUAL]:
            count = completed.filter(Order.billing_cycle == cycle).count()
            by_billing_cycle[cycle.value] = count

        return MarketplaceStats(
            total_orders=total_orders,
            total_revenue=total_revenue,
            orders_today=orders_today,
            revenue_today=revenue_today,
            orders_month=orders_month,
            revenue_month=revenue_month,
            conversion_rate=round(conversion_rate, 2),
            avg_order_value=avg_order_value,
            by_plan=by_plan,
            by_billing_cycle=by_billing_cycle
        )

    # =========================================================================
    # COMMANDES
    # =========================================================================

    def get_order(self, order_id: str) -> Order | None:
        """Récupère une commande."""
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_order_by_number(self, order_number: str) -> Order | None:
        """Récupère une commande par numéro."""
        return self.db.query(Order).filter(Order.order_number == order_number).first()

    def list_orders(
        self,
        status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Order], int]:
        """Liste les commandes."""
        query = self.db.query(Order)
        if status:
            query = query.filter(Order.status == status)

        total = query.count()
        items = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        return items, total


def get_marketplace_service(db: Session) -> MarketplaceService:
    """Factory pour le service marketplace."""
    return MarketplaceService(db)
