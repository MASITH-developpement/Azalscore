"""
AZALS MODULE 14 - Subscriptions Service
=========================================
Logique métier pour la gestion des abonnements.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import (
    InvoiceLine,
    InvoiceStatus,
    PaymentStatus,
    PlanAddOn,
    PlanInterval,
    Subscription,
    SubscriptionChange,
    SubscriptionCoupon,
    SubscriptionInvoice,
    SubscriptionItem,
    SubscriptionMetrics,
    SubscriptionPayment,
    SubscriptionPlan,
    SubscriptionStatus,
    SubscriptionWebhook,
    UsageRecord,
    UsageType,
)
from .schemas import (
    AddOnCreate,
    AddOnUpdate,
    CouponCreate,
    CouponUpdate,
    CouponValidateRequest,
    InvoiceCreate,
    PaymentCreate,
    PlanCreate,
    PlanUpdate,
    SubscriptionCancelRequest,
    SubscriptionChangePlanRequest,
    SubscriptionCreate,
    SubscriptionPauseRequest,
    SubscriptionUpdate,
    UsageRecordCreate,
)


class SubscriptionService:
    """Service abonnements complet."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # PLANS
    # ========================================================================

    def create_plan(self, data: PlanCreate) -> SubscriptionPlan:
        """Créer un plan."""
        # Vérifier code unique
        existing = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.tenant_id == self.tenant_id,
            SubscriptionPlan.code == data.code
        ).first()
        if existing:
            raise ValueError(f"Code plan '{data.code}' déjà utilisé")

        plan = SubscriptionPlan(
            tenant_id=self.tenant_id,
            is_active=True,
            **data.model_dump()
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_plan(self, plan_id: int) -> SubscriptionPlan | None:
        """Récupérer un plan."""
        return self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.tenant_id == self.tenant_id,
            SubscriptionPlan.id == plan_id
        ).first()

    def get_plan_by_code(self, code: str) -> SubscriptionPlan | None:
        """Récupérer plan par code."""
        return self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.tenant_id == self.tenant_id,
            SubscriptionPlan.code == code
        ).first()

    def list_plans(
        self,
        is_active: bool | None = None,
        is_public: bool | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[SubscriptionPlan], int]:
        """Lister les plans."""
        query = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.tenant_id == self.tenant_id
        )
        if is_active is not None:
            query = query.filter(SubscriptionPlan.is_active == is_active)
        if is_public is not None:
            query = query.filter(SubscriptionPlan.is_public == is_public)

        total = query.count()
        items = query.order_by(
            SubscriptionPlan.sort_order, SubscriptionPlan.name
        ).offset(skip).limit(limit).all()
        return items, total

    def update_plan(self, plan_id: int, data: PlanUpdate) -> SubscriptionPlan | None:
        """Mettre à jour un plan."""
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        plan.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def delete_plan(self, plan_id: int) -> bool:
        """Désactiver un plan."""
        plan = self.get_plan(plan_id)
        if not plan:
            return False

        # SÉCURITÉ: Vérifier pas d'abonnements actifs (filtrer par tenant_id)
        active_subs = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.plan_id == plan_id,
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).count()

        if active_subs > 0:
            raise ValueError(f"{active_subs} abonnements actifs sur ce plan")

        plan.is_active = False
        plan.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    # ========================================================================
    # ADD-ONS
    # ========================================================================

    def create_addon(self, data: AddOnCreate) -> PlanAddOn:
        """Créer un add-on."""
        plan = self.get_plan(data.plan_id)
        if not plan:
            raise ValueError("Plan introuvable")

        addon = PlanAddOn(
            tenant_id=self.tenant_id,
            is_active=True,
            **data.model_dump()
        )
        self.db.add(addon)
        self.db.commit()
        self.db.refresh(addon)
        return addon

    def list_addons(self, plan_id: int) -> list[PlanAddOn]:
        """Lister les add-ons d'un plan."""
        return self.db.query(PlanAddOn).filter(
            PlanAddOn.tenant_id == self.tenant_id,
            PlanAddOn.plan_id == plan_id,
            PlanAddOn.is_active
        ).all()

    def update_addon(
        self, addon_id: int, data: AddOnUpdate
    ) -> PlanAddOn | None:
        """Mettre à jour un add-on."""
        addon = self.db.query(PlanAddOn).filter(
            PlanAddOn.tenant_id == self.tenant_id,
            PlanAddOn.id == addon_id
        ).first()
        if not addon:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(addon, field, value)

        self.db.commit()
        self.db.refresh(addon)
        return addon

    # ========================================================================
    # SUBSCRIPTIONS
    # ========================================================================

    def _generate_subscription_number(self) -> str:
        """Générer numéro d'abonnement."""
        today = date.today()
        prefix = f"SUB{today.strftime('%Y%m')}"

        last = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.subscription_number.like(f"{prefix}%")
        ).order_by(Subscription.id.desc()).first()

        if last:
            last_num = int(last.subscription_number[-5:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:05d}"

    def _calculate_period_end(
        self, start: date, interval: PlanInterval, interval_count: int
    ) -> date:
        """Calculer fin de période."""
        if interval == PlanInterval.DAILY:
            return start + timedelta(days=interval_count)
        elif interval == PlanInterval.WEEKLY:
            return start + timedelta(weeks=interval_count)
        elif interval == PlanInterval.MONTHLY:
            return start + relativedelta(months=interval_count)
        elif interval == PlanInterval.QUARTERLY:
            return start + relativedelta(months=3 * interval_count)
        elif interval == PlanInterval.SEMI_ANNUAL:
            return start + relativedelta(months=6 * interval_count)
        elif interval == PlanInterval.ANNUAL:
            return start + relativedelta(years=interval_count)
        elif interval == PlanInterval.LIFETIME:
            return date(2099, 12, 31)
        return start + relativedelta(months=interval_count)

    def _calculate_mrr(self, subscription: Subscription) -> Decimal:
        """Calculer MRR d'un abonnement."""
        plan = subscription.plan
        base = plan.base_price * subscription.quantity

        # Ajouter items/add-ons
        for item in subscription.items:
            if item.is_active:
                base += item.unit_price * item.quantity

        # Appliquer remise
        if subscription.discount_percent > 0:
            if not subscription.discount_end_date or subscription.discount_end_date >= date.today():
                base = base * (1 - subscription.discount_percent / 100)

        # Normaliser en mensuel
        if plan.interval == PlanInterval.ANNUAL:
            return base / 12
        elif plan.interval == PlanInterval.QUARTERLY:
            return base / 3
        elif plan.interval == PlanInterval.SEMI_ANNUAL:
            return base / 6
        elif plan.interval == PlanInterval.WEEKLY:
            return base * Decimal("4.33")
        elif plan.interval == PlanInterval.DAILY:
            return base * 30

        return base

    def create_subscription(self, data: SubscriptionCreate) -> Subscription:
        """Créer un abonnement."""
        plan = self.get_plan(data.plan_id)
        if not plan:
            raise ValueError("Plan introuvable")

        if not plan.is_active:
            raise ValueError("Plan inactif")

        # Date de début
        start_date = data.start_date or date.today()

        # Période d'essai
        trial_start = None
        trial_end = data.trial_end
        status = SubscriptionStatus.ACTIVE

        if plan.trial_days > 0 and not data.trial_end:
            # Vérifier si client a déjà eu un essai
            if plan.trial_once:
                existing_trial = self.db.query(Subscription).filter(
                    Subscription.tenant_id == self.tenant_id,
                    Subscription.customer_id == data.customer_id,
                    Subscription.plan_id == data.plan_id,
                    Subscription.trial_start is not None
                ).first()

                if not existing_trial:
                    trial_start = start_date
                    trial_end = start_date + timedelta(days=plan.trial_days)
                    status = SubscriptionStatus.TRIALING
            else:
                trial_start = start_date
                trial_end = start_date + timedelta(days=plan.trial_days)
                status = SubscriptionStatus.TRIALING

        # Période actuelle
        period_start = trial_end or start_date
        period_end = self._calculate_period_end(
            period_start, plan.interval, plan.interval_count
        )

        # Coupon
        coupon_id = None
        discount_percent = data.discount_percent or Decimal("0")

        if data.coupon_code:
            coupon = self.validate_coupon(CouponValidateRequest(
                code=data.coupon_code,
                plan_id=data.plan_id,
                customer_id=data.customer_id
            ))
            if coupon.get("valid"):
                coupon_obj = coupon.get("coupon")
                coupon_id = coupon_obj.id
                if coupon_obj.discount_type == "percent":
                    discount_percent = coupon_obj.discount_value

        subscription = Subscription(
            tenant_id=self.tenant_id,
            subscription_number=self._generate_subscription_number(),
            plan_id=data.plan_id,
            customer_id=data.customer_id,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            status=status,
            quantity=data.quantity,
            current_users=0,
            trial_start=trial_start,
            trial_end=trial_end,
            current_period_start=period_start,
            current_period_end=period_end,
            started_at=start_date,
            billing_cycle_anchor=data.billing_cycle_anchor or period_start.day,
            collection_method=data.collection_method,
            default_payment_method_id=data.default_payment_method_id,
            discount_percent=discount_percent,
            discount_end_date=data.discount_end_date,
            coupon_id=coupon_id,
            extra_data=data.extra_data,
            notes=data.notes
        )
        self.db.add(subscription)
        self.db.flush()

        # Ajouter items
        if data.items:
            for item_data in data.items:
                item = SubscriptionItem(
                    tenant_id=self.tenant_id,
                    subscription_id=subscription.id,
                    add_on_code=item_data.add_on_code,
                    name=item_data.name,
                    description=item_data.description,
                    unit_price=item_data.unit_price,
                    quantity=item_data.quantity,
                    usage_type=item_data.usage_type,
                    is_active=True
                )
                self.db.add(item)

        # Calculer MRR
        self.db.flush()
        subscription.mrr = self._calculate_mrr(subscription)
        subscription.arr = subscription.mrr * 12

        # SÉCURITÉ: Incrémenter compteur coupon (filtrer par tenant_id)
        if coupon_id:
            self.db.query(SubscriptionCoupon).filter(
                SubscriptionCoupon.tenant_id == self.tenant_id,
                SubscriptionCoupon.id == coupon_id
            ).update({"times_redeemed": SubscriptionCoupon.times_redeemed + 1})

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def get_subscription(self, subscription_id: int) -> Subscription | None:
        """Récupérer un abonnement."""
        return self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.id == subscription_id
        ).first()

    def get_subscription_by_number(
        self, subscription_number: str
    ) -> Subscription | None:
        """Récupérer abonnement par numéro."""
        return self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.subscription_number == subscription_number
        ).first()

    def list_subscriptions(
        self,
        customer_id: int | None = None,
        plan_id: int | None = None,
        status: SubscriptionStatus | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Subscription], int]:
        """Lister les abonnements."""
        query = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id
        )
        if customer_id:
            query = query.filter(Subscription.customer_id == customer_id)
        if plan_id:
            query = query.filter(Subscription.plan_id == plan_id)
        if status:
            query = query.filter(Subscription.status == status)

        total = query.count()
        items = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_subscription(
        self, subscription_id: int, data: SubscriptionUpdate
    ) -> Subscription | None:
        """Mettre à jour un abonnement."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Gérer changement de quantité
        if "quantity" in update_data and update_data["quantity"] != subscription.quantity:
            old_qty = subscription.quantity
            new_qty = update_data["quantity"]

            # Enregistrer changement
            change = SubscriptionChange(
                tenant_id=self.tenant_id,
                subscription_id=subscription_id,
                change_type="quantity_change",
                previous_quantity=old_qty,
                new_quantity=new_qty,
                previous_mrr=subscription.mrr,
                effective_date=date.today()
            )
            self.db.add(change)

        for field, value in update_data.items():
            setattr(subscription, field, value)

        # Recalculer MRR
        subscription.mrr = self._calculate_mrr(subscription)
        subscription.arr = subscription.mrr * 12
        subscription.updated_at = datetime.utcnow()

        if hasattr(self.db, 'query'):  # Update change new_mrr
            pass

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def change_plan(
        self, subscription_id: int, data: SubscriptionChangePlanRequest
    ) -> Subscription:
        """Changer de plan."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            raise ValueError("Abonnement introuvable")

        if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]:
            raise ValueError("Abonnement non actif")

        new_plan = self.get_plan(data.new_plan_id)
        if not new_plan:
            raise ValueError("Nouveau plan introuvable")

        old_plan = subscription.plan
        old_mrr = subscription.mrr

        # Déterminer type de changement
        new_price = new_plan.base_price
        old_price = old_plan.base_price
        change_type = "upgrade" if new_price > old_price else "downgrade"

        # Calculer proratisation
        proration_amount = Decimal("0")
        if data.prorate and subscription.status == SubscriptionStatus.ACTIVE:
            days_remaining = (subscription.current_period_end - date.today()).days
            total_days = (subscription.current_period_end - subscription.current_period_start).days

            if total_days > 0:
                # Crédit du plan actuel
                credit = old_price * Decimal(str(days_remaining)) / Decimal(str(total_days))
                # Coût du nouveau plan
                charge = new_price * Decimal(str(days_remaining)) / Decimal(str(total_days))
                proration_amount = charge - credit

        # Enregistrer changement
        change = SubscriptionChange(
            tenant_id=self.tenant_id,
            subscription_id=subscription_id,
            change_type=change_type,
            change_reason=data.reason,
            previous_plan_id=old_plan.id,
            new_plan_id=new_plan.id,
            previous_quantity=subscription.quantity,
            new_quantity=data.new_quantity or subscription.quantity,
            previous_mrr=old_mrr,
            proration_amount=proration_amount,
            effective_date=data.effective_date or date.today()
        )

        # Mettre à jour abonnement
        subscription.plan_id = new_plan.id
        if data.new_quantity:
            subscription.quantity = data.new_quantity

        subscription.mrr = self._calculate_mrr(subscription)
        subscription.arr = subscription.mrr * 12
        change.new_mrr = subscription.mrr

        self.db.add(change)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def cancel_subscription(
        self, subscription_id: int, data: SubscriptionCancelRequest
    ) -> Subscription:
        """Annuler un abonnement."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            raise ValueError("Abonnement introuvable")

        if subscription.status == SubscriptionStatus.CANCELED:
            raise ValueError("Abonnement déjà annulé")

        # Enregistrer changement
        change = SubscriptionChange(
            tenant_id=self.tenant_id,
            subscription_id=subscription_id,
            change_type="cancel",
            change_reason=data.reason,
            previous_mrr=subscription.mrr,
            new_mrr=Decimal("0"),
            effective_date=subscription.current_period_end if data.cancel_at_period_end else date.today()
        )
        self.db.add(change)

        subscription.cancel_at_period_end = data.cancel_at_period_end
        subscription.canceled_at = datetime.utcnow()
        subscription.cancellation_reason = data.reason

        if not data.cancel_at_period_end:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.ended_at = date.today()
            subscription.mrr = Decimal("0")
            subscription.arr = Decimal("0")

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def pause_subscription(
        self, subscription_id: int, data: SubscriptionPauseRequest
    ) -> Subscription:
        """Mettre en pause un abonnement."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            raise ValueError("Abonnement introuvable")

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValueError("Seuls les abonnements actifs peuvent être mis en pause")

        # Enregistrer changement
        change = SubscriptionChange(
            tenant_id=self.tenant_id,
            subscription_id=subscription_id,
            change_type="pause",
            change_reason=data.reason,
            previous_mrr=subscription.mrr,
            new_mrr=Decimal("0"),
            effective_date=date.today()
        )
        self.db.add(change)

        subscription.status = SubscriptionStatus.PAUSED
        subscription.paused_at = datetime.utcnow()
        subscription.resume_at = data.resume_at

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def resume_subscription(self, subscription_id: int) -> Subscription:
        """Reprendre un abonnement en pause."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            raise ValueError("Abonnement introuvable")

        if subscription.status != SubscriptionStatus.PAUSED:
            raise ValueError("Abonnement non en pause")

        # Enregistrer changement
        change = SubscriptionChange(
            tenant_id=self.tenant_id,
            subscription_id=subscription_id,
            change_type="resume",
            previous_mrr=Decimal("0"),
            effective_date=date.today()
        )

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.paused_at = None
        subscription.resume_at = None
        subscription.mrr = self._calculate_mrr(subscription)
        subscription.arr = subscription.mrr * 12
        change.new_mrr = subscription.mrr

        self.db.add(change)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    # ========================================================================
    # INVOICES
    # ========================================================================

    def _generate_invoice_number(self) -> str:
        """Générer numéro de facture."""
        today = date.today()
        prefix = f"INV{today.strftime('%Y%m')}"

        last = self.db.query(SubscriptionInvoice).filter(
            SubscriptionInvoice.tenant_id == self.tenant_id,
            SubscriptionInvoice.invoice_number.like(f"{prefix}%")
        ).order_by(SubscriptionInvoice.id.desc()).first()

        if last:
            last_num = int(last.invoice_number[-5:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:05d}"

    def create_invoice(self, data: InvoiceCreate) -> SubscriptionInvoice:
        """Créer une facture manuelle."""
        subscription = self.get_subscription(data.subscription_id)
        if not subscription:
            raise ValueError("Abonnement introuvable")

        # Calculer totaux
        subtotal = sum(
            line.quantity * line.unit_price - line.discount_amount
            for line in data.lines
        )
        tax_amount = sum(
            (line.quantity * line.unit_price - line.discount_amount) * line.tax_rate / 100
            for line in data.lines
        )
        discount_amount = sum(line.discount_amount for line in data.lines)
        total = subtotal + tax_amount

        invoice = SubscriptionInvoice(
            tenant_id=self.tenant_id,
            subscription_id=data.subscription_id,
            invoice_number=self._generate_invoice_number(),
            customer_id=data.customer_id,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            billing_address=data.billing_address,
            status=InvoiceStatus.DRAFT,
            period_start=data.period_start,
            period_end=data.period_end,
            due_date=data.due_date or (date.today() + timedelta(days=30)),
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total=total,
            amount_remaining=total,
            collection_method=data.collection_method,
            notes=data.notes,
            footer=data.footer
        )
        self.db.add(invoice)
        self.db.flush()

        # Ajouter lignes
        for line_data in data.lines:
            line_amount = line_data.quantity * line_data.unit_price - line_data.discount_amount
            line_tax = line_amount * line_data.tax_rate / 100

            line = InvoiceLine(
                tenant_id=self.tenant_id,
                invoice_id=invoice.id,
                description=line_data.description,
                item_type=line_data.item_type,
                period_start=line_data.period_start,
                period_end=line_data.period_end,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_amount=line_data.discount_amount,
                amount=line_amount,
                tax_rate=line_data.tax_rate,
                tax_amount=line_tax
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoice(self, invoice_id: int) -> SubscriptionInvoice | None:
        """Récupérer une facture."""
        return self.db.query(SubscriptionInvoice).filter(
            SubscriptionInvoice.tenant_id == self.tenant_id,
            SubscriptionInvoice.id == invoice_id
        ).first()

    def list_invoices(
        self,
        subscription_id: int | None = None,
        customer_id: int | None = None,
        status: InvoiceStatus | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[SubscriptionInvoice], int]:
        """Lister les factures."""
        query = self.db.query(SubscriptionInvoice).filter(
            SubscriptionInvoice.tenant_id == self.tenant_id
        )
        if subscription_id:
            query = query.filter(SubscriptionInvoice.subscription_id == subscription_id)
        if customer_id:
            query = query.filter(SubscriptionInvoice.customer_id == customer_id)
        if status:
            query = query.filter(SubscriptionInvoice.status == status)

        total = query.count()
        items = query.order_by(SubscriptionInvoice.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def finalize_invoice(self, invoice_id: int) -> SubscriptionInvoice:
        """Finaliser une facture."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise ValueError("Facture introuvable")

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError("Seules les factures brouillon peuvent être finalisées")

        invoice.status = InvoiceStatus.OPEN
        invoice.finalized_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def void_invoice(self, invoice_id: int) -> SubscriptionInvoice:
        """Annuler une facture."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise ValueError("Facture introuvable")

        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Impossible d'annuler une facture payée")

        invoice.status = InvoiceStatus.VOID
        invoice.voided_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def mark_invoice_paid(
        self, invoice_id: int, payment_amount: Decimal | None = None
    ) -> SubscriptionInvoice:
        """Marquer facture comme payée."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise ValueError("Facture introuvable")

        amount = payment_amount or invoice.amount_remaining
        invoice.amount_paid += amount
        invoice.amount_remaining = max(Decimal("0"), invoice.total - invoice.amount_paid)

        if invoice.amount_remaining <= 0:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    # ========================================================================
    # PAYMENTS
    # ========================================================================

    def _generate_payment_number(self) -> str:
        """Générer numéro de paiement."""
        today = date.today()
        prefix = f"PAY{today.strftime('%Y%m')}"

        last = self.db.query(SubscriptionPayment).filter(
            SubscriptionPayment.tenant_id == self.tenant_id,
            SubscriptionPayment.payment_number.like(f"{prefix}%")
        ).order_by(SubscriptionPayment.id.desc()).first()

        if last:
            last_num = int(last.payment_number[-5:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:05d}"

    def create_payment(self, data: PaymentCreate) -> SubscriptionPayment:
        """Créer un paiement."""
        invoice = self.get_invoice(data.invoice_id)
        if not invoice:
            raise ValueError("Facture introuvable")

        payment = SubscriptionPayment(
            tenant_id=self.tenant_id,
            invoice_id=data.invoice_id,
            payment_number=self._generate_payment_number(),
            customer_id=invoice.customer_id,
            amount=data.amount,
            currency=data.currency,
            status=PaymentStatus.PENDING,
            payment_method_type=data.payment_method_type,
            payment_method_id=data.payment_method_id
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def process_payment(self, payment_id: int, success: bool = True, error: str = None):
        """Traiter résultat paiement."""
        payment = self.db.query(SubscriptionPayment).filter(
            SubscriptionPayment.tenant_id == self.tenant_id,
            SubscriptionPayment.id == payment_id
        ).first()

        if not payment:
            raise ValueError("Paiement introuvable")

        payment.processed_at = datetime.utcnow()

        if success:
            payment.status = PaymentStatus.SUCCEEDED
            # Marquer facture payée
            if payment.invoice_id:
                self.mark_invoice_paid(payment.invoice_id, payment.amount)
        else:
            payment.status = PaymentStatus.FAILED
            payment.failure_message = error

        self.db.commit()

    def refund_payment(
        self, payment_id: int, amount: Decimal | None = None, reason: str = None
    ) -> SubscriptionPayment:
        """Rembourser un paiement."""
        payment = self.db.query(SubscriptionPayment).filter(
            SubscriptionPayment.tenant_id == self.tenant_id,
            SubscriptionPayment.id == payment_id
        ).first()

        if not payment:
            raise ValueError("Paiement introuvable")

        if payment.status != PaymentStatus.SUCCEEDED:
            raise ValueError("Seuls les paiements réussis peuvent être remboursés")

        refund_amount = amount or payment.amount
        if refund_amount > (payment.amount - payment.refunded_amount):
            raise ValueError("Montant de remboursement supérieur au disponible")

        payment.refunded_amount += refund_amount
        payment.refund_reason = reason

        if payment.refunded_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        self.db.commit()
        self.db.refresh(payment)
        return payment

    # ========================================================================
    # USAGE RECORDS
    # ========================================================================

    def create_usage_record(self, data: UsageRecordCreate) -> UsageRecord:
        """Créer un enregistrement d'usage."""
        # SÉCURITÉ: Vérifier idempotence (filtrer par tenant_id)
        if data.idempotency_key:
            existing = self.db.query(UsageRecord).filter(
                UsageRecord.tenant_id == self.tenant_id,
                UsageRecord.idempotency_key == data.idempotency_key
            ).first()
            if existing:
                return existing

        # SÉCURITÉ: Récupérer item (filtrer par tenant_id)
        item = self.db.query(SubscriptionItem).filter(
            SubscriptionItem.tenant_id == self.tenant_id,
            SubscriptionItem.id == data.subscription_item_id
        ).first()

        if not item:
            raise ValueError("Item d'abonnement introuvable")

        if item.usage_type != UsageType.METERED:
            raise ValueError("Cet item n'est pas de type metered")

        subscription = self.get_subscription(item.subscription_id)

        record = UsageRecord(
            tenant_id=self.tenant_id,
            subscription_id=subscription.id,
            subscription_item_id=data.subscription_item_id,
            quantity=data.quantity,
            unit=data.unit,
            action=data.action,
            timestamp=data.timestamp or datetime.utcnow(),
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            idempotency_key=data.idempotency_key,
            extra_data=data.extra_data
        )
        self.db.add(record)

        # Mettre à jour usage cumulé
        if data.action == "set":
            item.metered_usage = data.quantity
        else:  # increment
            item.metered_usage += data.quantity

        self.db.commit()
        self.db.refresh(record)
        return record

    def get_usage_summary(
        self, subscription_id: int,
        period_start: date | None = None,
        period_end: date | None = None
    ) -> list[dict[str, Any]]:
        """Résumé d'usage par item."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            raise ValueError("Abonnement introuvable")

        start = period_start or subscription.current_period_start
        end = period_end or subscription.current_period_end

        summary = []
        for item in subscription.items:
            if item.usage_type == UsageType.METERED:
                total_usage = self.db.query(
                    func.sum(UsageRecord.quantity)
                ).filter(
                    UsageRecord.subscription_item_id == item.id,
                    UsageRecord.period_start >= start,
                    UsageRecord.period_end <= end
                ).scalar() or Decimal("0")

                summary.append({
                    "subscription_id": subscription_id,
                    "item_id": item.id,
                    "item_name": item.name,
                    "period_start": start,
                    "period_end": end,
                    "total_usage": total_usage,
                    "unit": None,
                    "estimated_amount": total_usage * item.unit_price
                })

        return summary

    # ========================================================================
    # COUPONS
    # ========================================================================

    def create_coupon(self, data: CouponCreate) -> SubscriptionCoupon:
        """Créer un coupon."""
        # Vérifier code unique
        existing = self.db.query(SubscriptionCoupon).filter(
            SubscriptionCoupon.tenant_id == self.tenant_id,
            SubscriptionCoupon.code == data.code
        ).first()
        if existing:
            raise ValueError(f"Code coupon '{data.code}' déjà utilisé")

        coupon = SubscriptionCoupon(
            tenant_id=self.tenant_id,
            is_active=True,
            **data.model_dump()
        )
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    def get_coupon(self, coupon_id: int) -> SubscriptionCoupon | None:
        """Récupérer un coupon."""
        return self.db.query(SubscriptionCoupon).filter(
            SubscriptionCoupon.tenant_id == self.tenant_id,
            SubscriptionCoupon.id == coupon_id
        ).first()

    def get_coupon_by_code(self, code: str) -> SubscriptionCoupon | None:
        """Récupérer coupon par code."""
        return self.db.query(SubscriptionCoupon).filter(
            SubscriptionCoupon.tenant_id == self.tenant_id,
            SubscriptionCoupon.code == code
        ).first()

    def list_coupons(
        self,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> list[SubscriptionCoupon]:
        """Lister les coupons."""
        query = self.db.query(SubscriptionCoupon).filter(
            SubscriptionCoupon.tenant_id == self.tenant_id
        )
        if is_active is not None:
            query = query.filter(SubscriptionCoupon.is_active == is_active)

        return query.order_by(SubscriptionCoupon.created_at.desc()).offset(skip).limit(limit).all()

    def validate_coupon(self, data: CouponValidateRequest) -> dict[str, Any]:
        """Valider un coupon."""
        coupon = self.get_coupon_by_code(data.code)

        if not coupon:
            return {"valid": False, "error_message": "Coupon introuvable"}

        if not coupon.is_active:
            return {"valid": False, "error_message": "Coupon inactif"}

        now = datetime.utcnow()
        if coupon.valid_from and now < coupon.valid_from:
            return {"valid": False, "error_message": "Coupon pas encore valide"}

        if coupon.valid_until and now > coupon.valid_until:
            return {"valid": False, "error_message": "Coupon expiré"}

        if coupon.max_redemptions and coupon.times_redeemed >= coupon.max_redemptions:
            return {"valid": False, "error_message": "Limite d'utilisation atteinte"}

        # Vérifier plans concernés
        if coupon.applies_to_plans and data.plan_id and data.plan_id not in coupon.applies_to_plans:
            return {"valid": False, "error_message": "Coupon non valide pour ce plan"}

        # Vérifier montant minimum
        if coupon.min_amount and data.amount and data.amount < coupon.min_amount:
            return {"valid": False, "error_message": f"Montant minimum: {coupon.min_amount}"}

        # Vérifier première commande
        if coupon.first_time_only and data.customer_id:
            existing = self.db.query(Subscription).filter(
                Subscription.tenant_id == self.tenant_id,
                Subscription.customer_id == data.customer_id
            ).first()
            if existing:
                return {"valid": False, "error_message": "Coupon réservé aux nouveaux clients"}

        # Calculer réduction
        discount_amount = None
        if data.amount:
            if coupon.discount_type == "percent":
                discount_amount = data.amount * coupon.discount_value / 100
            else:
                discount_amount = min(coupon.discount_value, data.amount)

        return {
            "valid": True,
            "coupon": coupon,
            "discount_amount": discount_amount
        }

    def update_coupon(
        self, coupon_id: int, data: CouponUpdate
    ) -> SubscriptionCoupon | None:
        """Mettre à jour un coupon."""
        coupon = self.get_coupon(coupon_id)
        if not coupon:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(coupon, field, value)

        self.db.commit()
        self.db.refresh(coupon)
        return coupon

    # ========================================================================
    # METRICS
    # ========================================================================

    def calculate_metrics(self, metric_date: date = None) -> SubscriptionMetrics:
        """Calculer et sauvegarder métriques."""
        target_date = metric_date or date.today()

        # Vérifier si existe déjà
        existing = self.db.query(SubscriptionMetrics).filter(
            SubscriptionMetrics.tenant_id == self.tenant_id,
            SubscriptionMetrics.metric_date == target_date
        ).first()

        metrics = existing or SubscriptionMetrics(tenant_id=self.tenant_id, metric_date=target_date)

        # Compteurs abonnements
        active_subs = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).all()

        trialing = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.TRIALING
        ).count()

        canceled = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.CANCELED
        ).count()

        # MRR
        mrr = sum(s.mrr for s in active_subs)

        # Mouvements du jour
        month_start = target_date.replace(day=1)

        new_subs = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.started_at >= month_start,
            Subscription.started_at <= target_date
        ).all()

        churned = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.canceled_at >= month_start,
            Subscription.canceled_at <= datetime.combine(target_date, datetime.max.time())
        ).count()

        # Changements MRR
        changes = self.db.query(SubscriptionChange).filter(
            SubscriptionChange.tenant_id == self.tenant_id,
            SubscriptionChange.effective_date >= month_start,
            SubscriptionChange.effective_date <= target_date
        ).all()

        new_mrr = sum(s.mrr for s in new_subs)
        expansion_mrr = sum(
            c.new_mrr - c.previous_mrr for c in changes
            if c.change_type == "upgrade" and c.new_mrr and c.previous_mrr
        )
        contraction_mrr = sum(
            c.previous_mrr - c.new_mrr for c in changes
            if c.change_type == "downgrade" and c.new_mrr and c.previous_mrr
        )
        churned_mrr = sum(
            c.previous_mrr for c in changes
            if c.change_type == "cancel" and c.previous_mrr
        )

        # Clients uniques
        total_customers = self.db.query(
            func.count(func.distinct(Subscription.customer_id))
        ).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
        ).scalar() or 0

        # ARPU
        arpu = mrr / len(active_subs) if active_subs else Decimal("0")

        # Churn rate
        start_count = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.started_at < month_start,
            or_(
                Subscription.ended_at is None,
                Subscription.ended_at >= month_start
            )
        ).count()

        churn_rate = (Decimal(str(churned)) / Decimal(str(start_count)) * 100) if start_count > 0 else Decimal("0")

        # Mettre à jour métriques
        metrics.mrr = mrr
        metrics.arr = mrr * 12
        metrics.new_mrr = new_mrr
        metrics.expansion_mrr = expansion_mrr
        metrics.contraction_mrr = contraction_mrr
        metrics.churned_mrr = churned_mrr
        metrics.total_subscriptions = len(active_subs) + trialing + canceled
        metrics.active_subscriptions = len(active_subs)
        metrics.trialing_subscriptions = trialing
        metrics.canceled_subscriptions = canceled
        metrics.new_subscriptions = len(new_subs)
        metrics.churned_subscriptions = churned
        metrics.total_customers = total_customers
        metrics.churn_rate = churn_rate
        metrics.arpu = arpu

        if not existing:
            self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        return metrics

    def get_metrics(self, metric_date: date) -> SubscriptionMetrics | None:
        """Récupérer métriques d'une date."""
        return self.db.query(SubscriptionMetrics).filter(
            SubscriptionMetrics.tenant_id == self.tenant_id,
            SubscriptionMetrics.metric_date == metric_date
        ).first()

    def get_metrics_trend(
        self, start_date: date, end_date: date
    ) -> list[SubscriptionMetrics]:
        """Récupérer tendance métriques."""
        return self.db.query(SubscriptionMetrics).filter(
            SubscriptionMetrics.tenant_id == self.tenant_id,
            SubscriptionMetrics.metric_date >= start_date,
            SubscriptionMetrics.metric_date <= end_date
        ).order_by(SubscriptionMetrics.metric_date).all()

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> dict[str, Any]:
        """Dashboard abonnements."""
        today = date.today()
        month_start = today.replace(day=1)
        last_month = month_start - timedelta(days=1)
        last_month.replace(day=1)

        # Abonnements actifs
        active = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).all()

        trialing = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.TRIALING
        ).count()

        past_due = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.PAST_DUE
        ).count()

        # MRR actuel
        mrr = sum(s.mrr for s in active)

        # MRR mois précédent
        prev_metrics = self.get_metrics(last_month)
        prev_mrr = prev_metrics.mrr if prev_metrics else Decimal("0")
        mrr_growth = ((mrr - prev_mrr) / prev_mrr * 100) if prev_mrr > 0 else Decimal("0")

        # Annulations ce mois
        canceled_this_month = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.canceled_at >= month_start
        ).count()

        # Top plans
        plan_counts = self.db.query(
            SubscriptionPlan.name,
            func.count(Subscription.id).label("count"),
            func.sum(Subscription.mrr).label("mrr")
        ).join(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).group_by(SubscriptionPlan.name).order_by(
            func.sum(Subscription.mrr).desc()
        ).limit(5).all()

        top_plans = [
            {"name": p.name, "count": p.count, "mrr": float(p.mrr or 0)}
            for p in plan_counts
        ]

        # Prochains renouvellements
        upcoming = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.current_period_end <= today + timedelta(days=7)
        ).order_by(Subscription.current_period_end).limit(5).all()

        upcoming_renewals = [
            {
                "id": s.id,
                "customer_name": s.customer_name,
                "plan": s.plan.name if s.plan else None,
                "renewal_date": s.current_period_end.isoformat(),
                "mrr": float(s.mrr)
            }
            for s in upcoming
        ]

        # Factures en attente
        pending_invoices = self.db.query(
            func.count(SubscriptionInvoice.id),
            func.coalesce(func.sum(SubscriptionInvoice.amount_remaining), 0)
        ).filter(
            SubscriptionInvoice.tenant_id == self.tenant_id,
            SubscriptionInvoice.status == InvoiceStatus.OPEN
        ).first()

        # Calculer métriques additionnelles
        arpu = mrr / len(active) if active else Decimal("0")

        # Churn rate ce mois
        start_count = self.db.query(Subscription).filter(
            Subscription.tenant_id == self.tenant_id,
            Subscription.started_at < month_start,
            or_(
                Subscription.ended_at is None,
                Subscription.ended_at >= month_start
            )
        ).count()
        churn_rate = (canceled_this_month / start_count * 100) if start_count > 0 else 0

        return {
            "mrr": float(mrr),
            "mrr_growth": float(mrr_growth),
            "arr": float(mrr * 12),
            "total_active": len(active),
            "trialing": trialing,
            "past_due": past_due,
            "canceled_this_month": canceled_this_month,
            "new_mrr": 0,  # À calculer
            "expansion_mrr": 0,
            "contraction_mrr": 0,
            "churned_mrr": 0,
            "net_mrr_change": float(mrr - prev_mrr),
            "churn_rate": churn_rate,
            "trial_conversion_rate": 0,  # À calculer
            "arpu": float(arpu),
            "average_ltv": float(arpu * 24),  # Estimation simple
            "top_plans": top_plans,
            "upcoming_renewals": upcoming_renewals,
            "pending_invoices_count": pending_invoices[0] or 0,
            "pending_invoices_amount": float(pending_invoices[1] or 0)
        }

    # ========================================================================
    # WEBHOOKS
    # ========================================================================

    def process_webhook(self, event_type: str, source: str, payload: dict[str, Any]) -> SubscriptionWebhook:
        """Enregistrer et traiter webhook."""
        webhook = SubscriptionWebhook(
            tenant_id=self.tenant_id,
            event_id=payload.get("id"),
            event_type=event_type,
            source=source,
            payload=payload,
            related_object_type=payload.get("object"),
            related_object_id=payload.get("object_id"),
            is_processed=False
        )
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)

        # Traiter selon le type
        try:
            self._handle_webhook(webhook)
            webhook.is_processed = True
            webhook.processed_at = datetime.utcnow()
        except Exception as e:
            webhook.processing_error = str(e)
            webhook.retry_count += 1

        self.db.commit()
        return webhook

    def _handle_webhook(self, webhook: SubscriptionWebhook):
        """Handler interne webhook."""
        # Implémentation selon source et type
        pass
