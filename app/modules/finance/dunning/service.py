"""
AZALS MODULE - Dunning (Relances Impayés): Service
===================================================

Service de gestion des relances impayés.

Fonctionnalités:
- Détection automatique des factures en retard
- Envoi automatique des relances par email/SMS
- Escalade progressive des niveaux de relance
- Calcul des pénalités de retard (art. L441-10 Code de commerce)
- Suivi des promesses de paiement
- Statistiques et reporting
"""
from __future__ import annotations


import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from .models import (
    DunningLevel,
    DunningTemplate,
    DunningRule,
    DunningAction,
    DunningCampaign,
    PaymentPromise,
    CustomerDunningProfile,
    DunningLevelType,
    DunningChannel,
    DunningStatus,
    DunningCampaignStatus,
    PaymentPromiseStatus,
)
from .schemas import (
    DunningLevelCreate,
    DunningLevelUpdate,
    DunningTemplateCreate,
    DunningRuleCreate,
    DunningActionCreate,
    DunningCampaignCreate,
    PaymentPromiseCreate,
    PaymentPromiseUpdate,
    CustomerDunningProfileCreate,
    CustomerDunningProfileUpdate,
    OverdueInvoice,
    OverdueAnalysis,
    DunningStatistics,
    BulkDunningRequest,
    DEFAULT_TEMPLATES,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Taux d'intérêt de retard par défaut (3x taux directeur BCE)
DEFAULT_LATE_INTEREST_RATE = Decimal("10.0")  # %

# Indemnité forfaitaire de recouvrement (art. L441-10)
FIXED_RECOVERY_FEE = Decimal("40.00")

# Jours fériés français 2025-2026
FRENCH_HOLIDAYS_2025 = [
    date(2025, 1, 1),   # Jour de l'an
    date(2025, 4, 21),  # Lundi de Pâques
    date(2025, 5, 1),   # Fête du travail
    date(2025, 5, 8),   # Victoire 1945
    date(2025, 5, 29),  # Ascension
    date(2025, 6, 9),   # Lundi de Pentecôte
    date(2025, 7, 14),  # Fête nationale
    date(2025, 8, 15),  # Assomption
    date(2025, 11, 1),  # Toussaint
    date(2025, 11, 11), # Armistice
    date(2025, 12, 25), # Noël
]


# ============================================================================
# SERVICE
# ============================================================================


class DunningService:
    """Service de gestion des relances impayés."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # DUNNING LEVELS
    # ========================================================================

    def create_level(self, data: DunningLevelCreate) -> DunningLevel:
        """Créer un niveau de relance."""
        level = DunningLevel(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            level_type=DunningLevelType(data.level_type),
            sequence=data.sequence,
            days_after_due=data.days_after_due,
            days_before_next=data.days_before_next,
            channels=data.channels,
            primary_channel=DunningChannel(data.primary_channel),
            block_orders=data.block_orders,
            add_fees=data.add_fees,
            fee_amount=data.fee_amount,
            fee_percentage=data.fee_percentage,
            apply_late_interest=data.apply_late_interest,
            late_interest_rate=data.late_interest_rate,
            fixed_recovery_fee=data.fixed_recovery_fee,
            require_approval=data.require_approval,
        )
        self.db.add(level)
        self.db.commit()
        self.db.refresh(level)
        return level

    def get_level(self, level_id: UUID) -> Optional[DunningLevel]:
        """Récupérer un niveau de relance."""
        return self.db.query(DunningLevel).filter(
            DunningLevel.tenant_id == self.tenant_id,
            DunningLevel.id == level_id
        ).first()

    def list_levels(self, active_only: bool = True) -> list[DunningLevel]:
        """Lister les niveaux de relance."""
        query = self.db.query(DunningLevel).filter(
            DunningLevel.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(DunningLevel.is_active == True)  # noqa: E712
        return query.order_by(DunningLevel.sequence).all()

    def get_next_level(self, current_level_id: UUID) -> Optional[DunningLevel]:
        """Récupérer le niveau de relance suivant."""
        current = self.get_level(current_level_id)
        if not current:
            return None
        return self.db.query(DunningLevel).filter(
            DunningLevel.tenant_id == self.tenant_id,
            DunningLevel.sequence > current.sequence,
            DunningLevel.is_active == True  # noqa: E712
        ).order_by(DunningLevel.sequence).first()

    def initialize_default_levels(self) -> int:
        """Initialiser les niveaux de relance par défaut."""
        existing = self.db.query(DunningLevel).filter(
            DunningLevel.tenant_id == self.tenant_id
        ).first()
        if existing:
            return 0

        default_levels = [
            DunningLevel(
                tenant_id=self.tenant_id,
                code="REMINDER",
                name="Rappel de paiement",
                level_type=DunningLevelType.REMINDER,
                sequence=1,
                days_after_due=3,
                days_before_next=7,
                channels=["EMAIL"],
                primary_channel=DunningChannel.EMAIL,
            ),
            DunningLevel(
                tenant_id=self.tenant_id,
                code="LEVEL_1",
                name="1ère relance",
                level_type=DunningLevelType.FIRST_NOTICE,
                sequence=2,
                days_after_due=10,
                days_before_next=10,
                channels=["EMAIL", "SMS"],
                primary_channel=DunningChannel.EMAIL,
            ),
            DunningLevel(
                tenant_id=self.tenant_id,
                code="LEVEL_2",
                name="2ème relance",
                level_type=DunningLevelType.SECOND_NOTICE,
                sequence=3,
                days_after_due=20,
                days_before_next=10,
                channels=["EMAIL", "SMS", "PHONE"],
                primary_channel=DunningChannel.EMAIL,
                add_fees=True,
                fixed_recovery_fee=FIXED_RECOVERY_FEE,
            ),
            DunningLevel(
                tenant_id=self.tenant_id,
                code="FORMAL",
                name="Mise en demeure",
                level_type=DunningLevelType.FORMAL_NOTICE,
                sequence=4,
                days_after_due=30,
                days_before_next=15,
                channels=["EMAIL", "REGISTERED"],
                primary_channel=DunningChannel.REGISTERED,
                block_orders=True,
                add_fees=True,
                apply_late_interest=True,
                late_interest_rate=DEFAULT_LATE_INTEREST_RATE,
                fixed_recovery_fee=FIXED_RECOVERY_FEE,
                require_approval=True,
            ),
            DunningLevel(
                tenant_id=self.tenant_id,
                code="FINAL",
                name="Dernière relance",
                level_type=DunningLevelType.FINAL_NOTICE,
                sequence=5,
                days_after_due=45,
                days_before_next=15,
                channels=["REGISTERED"],
                primary_channel=DunningChannel.REGISTERED,
                block_orders=True,
                add_fees=True,
                apply_late_interest=True,
                late_interest_rate=DEFAULT_LATE_INTEREST_RATE,
                fixed_recovery_fee=FIXED_RECOVERY_FEE,
                require_approval=True,
            ),
            DunningLevel(
                tenant_id=self.tenant_id,
                code="COLLECTION",
                name="Transmission au recouvrement",
                level_type=DunningLevelType.COLLECTION,
                sequence=6,
                days_after_due=60,
                channels=["LETTER"],
                primary_channel=DunningChannel.LETTER,
                block_orders=True,
                require_approval=True,
            ),
        ]

        for level in default_levels:
            self.db.add(level)

        self.db.commit()
        return len(default_levels)

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(self, data: DunningTemplateCreate) -> DunningTemplate:
        """Créer un template de relance."""
        template = DunningTemplate(
            tenant_id=self.tenant_id,
            level_id=data.level_id,
            channel=DunningChannel(data.channel),
            language=data.language,
            subject=data.subject,
            body=data.body,
            is_default=data.is_default,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template(
        self,
        level_id: UUID,
        channel: str,
        language: str = "fr"
    ) -> Optional[DunningTemplate]:
        """Récupérer un template pour un niveau et canal."""
        return self.db.query(DunningTemplate).filter(
            DunningTemplate.tenant_id == self.tenant_id,
            DunningTemplate.level_id == level_id,
            DunningTemplate.channel == DunningChannel(channel),
            DunningTemplate.language == language,
            DunningTemplate.is_active == True  # noqa: E712
        ).first()

    def render_template(
        self,
        template: DunningTemplate,
        context: dict
    ) -> tuple[str | None, str]:
        """Rendre un template avec le contexte."""
        subject = template.subject
        body = template.body

        # Remplacer les variables
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if subject:
                subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))

        return subject, body

    # ========================================================================
    # RULES
    # ========================================================================

    def create_rule(self, data: DunningRuleCreate) -> DunningRule:
        """Créer une règle de relance."""
        rule = DunningRule(
            tenant_id=self.tenant_id,
            name=data.name,
            description=data.description,
            priority=data.priority,
            conditions=data.conditions,
            start_level_id=data.start_level_id,
            min_amount=data.min_amount,
            grace_days=data.grace_days,
            exclude_weekends=data.exclude_weekends,
            exclude_holidays=data.exclude_holidays,
            auto_send=data.auto_send,
            require_approval=data.require_approval,
            is_default=data.is_default,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_applicable_rule(
        self,
        invoice_amount: Decimal,
        customer_segment: Optional[str] = None
    ) -> Optional[DunningRule]:
        """Trouver la règle applicable pour une facture."""
        rules = self.db.query(DunningRule).filter(
            DunningRule.tenant_id == self.tenant_id,
            DunningRule.is_active == True  # noqa: E712
        ).order_by(DunningRule.priority).all()

        for rule in rules:
            # Vérifier le montant minimum
            if rule.min_amount and invoice_amount < rule.min_amount:
                continue

            # Vérifier les conditions JSON
            conditions = rule.conditions or {}
            if customer_segment:
                required_segments = conditions.get("customer_segments", [])
                if required_segments and customer_segment not in required_segments:
                    continue

            return rule

        # Règle par défaut
        return self.db.query(DunningRule).filter(
            DunningRule.tenant_id == self.tenant_id,
            DunningRule.is_default == True  # noqa: E712
        ).first()

    # ========================================================================
    # OVERDUE DETECTION
    # ========================================================================

    def get_overdue_invoices(
        self,
        min_days_overdue: int = 1,
        max_days_overdue: Optional[int] = None,
        min_amount: Optional[Decimal] = None,
        customer_id: Optional[str] = None,
        exclude_blocked: bool = True,
    ) -> list[OverdueInvoice]:
        """
        Récupérer les factures en retard.

        Cette méthode doit être adaptée pour se connecter
        au module de facturation réel.
        """
        # NOTE: Cette implémentation simule la récupération des factures
        # En production, connecter au module sales/invoices
        today = date.today()

        # Simuler une requête au module de facturation
        # Dans une vraie implémentation:
        # from app.modules.sales.models import Invoice
        # invoices = self.db.query(Invoice).filter(
        #     Invoice.tenant_id == self.tenant_id,
        #     Invoice.status == "SENT",
        #     Invoice.payment_status != "PAID",
        #     Invoice.due_date < today
        # ).all()

        overdue_list: list[OverdueInvoice] = []

        # TODO: Intégrer avec le module de facturation réel
        logger.warning("[Dunning] get_overdue_invoices() requires integration with invoice module")

        return overdue_list

    def calculate_days_overdue(
        self,
        due_date: date,
        exclude_weekends: bool = True,
        exclude_holidays: bool = True
    ) -> int:
        """Calculer le nombre de jours de retard (jours ouvrés optionnels)."""
        today = date.today()
        if due_date >= today:
            return 0

        if not exclude_weekends and not exclude_holidays:
            return (today - due_date).days

        # Calcul en jours ouvrés
        days = 0
        current = due_date + timedelta(days=1)
        while current <= today:
            is_weekend = current.weekday() >= 5
            is_holiday = current in FRENCH_HOLIDAYS_2025

            if exclude_weekends and is_weekend:
                current += timedelta(days=1)
                continue
            if exclude_holidays and is_holiday:
                current += timedelta(days=1)
                continue

            days += 1
            current += timedelta(days=1)

        return days

    # ========================================================================
    # FEES CALCULATION
    # ========================================================================

    def calculate_late_interest(
        self,
        amount: Decimal,
        days_overdue: int,
        annual_rate: Decimal = DEFAULT_LATE_INTEREST_RATE
    ) -> Decimal:
        """
        Calculer les intérêts de retard.

        Formule: Principal × (Taux annuel / 365) × Nombre de jours
        """
        if days_overdue <= 0:
            return Decimal("0")

        daily_rate = annual_rate / Decimal("365") / Decimal("100")
        interest = amount * daily_rate * Decimal(str(days_overdue))
        return interest.quantize(Decimal("0.01"))

    def calculate_total_fees(
        self,
        amount: Decimal,
        days_overdue: int,
        level: DunningLevel
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Calculer les frais totaux pour un niveau de relance.

        Returns:
            (intérêts, frais fixes, total_fees)
        """
        interest = Decimal("0")
        fixed_fees = Decimal("0")

        if level.apply_late_interest and level.late_interest_rate:
            interest = self.calculate_late_interest(
                amount, days_overdue, level.late_interest_rate
            )

        if level.add_fees:
            if level.fixed_recovery_fee:
                fixed_fees += level.fixed_recovery_fee
            if level.fee_amount:
                fixed_fees += level.fee_amount
            if level.fee_percentage:
                fixed_fees += amount * level.fee_percentage / Decimal("100")

        total_fees = interest + fixed_fees
        return interest, fixed_fees, total_fees

    # ========================================================================
    # DUNNING ACTIONS
    # ========================================================================

    def create_action(
        self,
        invoice: OverdueInvoice,
        level: DunningLevel,
        channel: Optional[str] = None,
        campaign_id: Optional[UUID] = None,
        created_by: Optional[str] = None,
    ) -> DunningAction:
        """Créer une action de relance."""
        channel = channel or level.primary_channel.value
        days_overdue = self.calculate_days_overdue(invoice.due_date)

        interest, fixed_fees, total_fees = self.calculate_total_fees(
            invoice.amount_due, days_overdue, level
        )

        action = DunningAction(
            tenant_id=self.tenant_id,
            invoice_id=invoice.invoice_id,
            invoice_number=invoice.invoice_number,
            customer_id=invoice.customer_id,
            customer_name=invoice.customer_name,
            customer_email=invoice.customer_email,
            level_id=level.id,
            channel=DunningChannel(channel),
            campaign_id=campaign_id,
            amount_due=invoice.amount_due,
            fees_applied=fixed_fees,
            interest_applied=interest,
            total_due=invoice.amount_due + total_fees,
            due_date=invoice.due_date,
            days_overdue=days_overdue,
            status=DunningStatus.PENDING,
            created_by=created_by,
        )

        # Générer le contenu
        template = self.get_template(level.id, channel)
        if template:
            context = {
                "customer_name": invoice.customer_name,
                "invoice_number": invoice.invoice_number,
                "amount_due": f"{invoice.amount_due:.2f}",
                "due_date": invoice.due_date.strftime("%d/%m/%Y"),
                "days_overdue": days_overdue,
                "interest_amount": f"{interest:.2f}",
                "total_due": f"{(invoice.amount_due + total_fees):.2f}",
                "company_name": "AZALS",  # TODO: Récupérer du tenant
            }
            subject, body = self.render_template(template, context)
            action.subject = subject
            action.body = body

        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)

        logger.info(
            f"[Dunning] Action créée: {action.id} - "
            f"Facture {invoice.invoice_number} - Niveau {level.code}"
        )

        return action

    def send_action(self, action_id: UUID) -> DunningAction:
        """Envoyer une action de relance."""
        action = self.db.query(DunningAction).filter(
            DunningAction.tenant_id == self.tenant_id,
            DunningAction.id == action_id
        ).first()

        if not action:
            raise ValueError(f"Action {action_id} introuvable")

        if action.status != DunningStatus.PENDING:
            raise ValueError(f"Action {action_id} déjà traitée (status: {action.status})")

        # TODO: Intégrer avec les services d'envoi réels (Mailgun, Twilio, etc.)
        # Pour l'instant, simuler l'envoi

        try:
            if action.channel == DunningChannel.EMAIL:
                # TODO: Envoyer email via service email
                logger.info(f"[Dunning] Envoi email à {action.customer_email}")
                action.status = DunningStatus.SENT
                action.sent_at = datetime.utcnow()
                # Simuler ID externe
                action.message_id = f"email_{uuid4().hex[:12]}"

            elif action.channel == DunningChannel.SMS:
                # TODO: Envoyer SMS via Twilio/autre
                logger.info(f"[Dunning] Envoi SMS à {action.customer_phone}")
                action.status = DunningStatus.SENT
                action.sent_at = datetime.utcnow()
                action.message_id = f"sms_{uuid4().hex[:12]}"

            else:
                # Pour LETTER, REGISTERED, PHONE: marquer comme en attente
                action.status = DunningStatus.PENDING
                logger.info(f"[Dunning] Action {action.channel.value} nécessite traitement manuel")

        except Exception as e:
            action.status = DunningStatus.FAILED
            action.error_message = str(e)
            logger.error(f"[Dunning] Échec envoi action {action_id}: {e}")

        self.db.commit()
        return action

    def get_actions(
        self,
        invoice_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        level_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[DunningAction], int]:
        """Lister les actions de relance avec filtres."""
        query = self.db.query(DunningAction).filter(
            DunningAction.tenant_id == self.tenant_id
        )

        if invoice_id:
            query = query.filter(DunningAction.invoice_id == invoice_id)
        if customer_id:
            query = query.filter(DunningAction.customer_id == customer_id)
        if status:
            query = query.filter(DunningAction.status == DunningStatus(status))
        if level_id:
            query = query.filter(DunningAction.level_id == level_id)
        if from_date:
            query = query.filter(DunningAction.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.filter(DunningAction.created_at <= datetime.combine(to_date, datetime.max.time()))

        total = query.count()
        actions = query.order_by(DunningAction.created_at.desc()).offset(skip).limit(limit).all()

        return actions, total

    def mark_payment_received(
        self,
        action_id: UUID,
        payment_amount: Decimal,
        payment_date: date
    ) -> DunningAction:
        """Marquer une action comme payée."""
        action = self.db.query(DunningAction).filter(
            DunningAction.tenant_id == self.tenant_id,
            DunningAction.id == action_id
        ).first()

        if not action:
            raise ValueError(f"Action {action_id} introuvable")

        action.payment_received = True
        action.payment_amount = payment_amount
        action.payment_date = payment_date
        action.updated_at = datetime.utcnow()

        self.db.commit()
        return action

    # ========================================================================
    # CAMPAIGNS
    # ========================================================================

    def create_campaign(
        self,
        data: DunningCampaignCreate,
        created_by: Optional[str] = None
    ) -> DunningCampaign:
        """Créer une campagne de relance."""
        campaign = DunningCampaign(
            tenant_id=self.tenant_id,
            name=data.name,
            description=data.description,
            level_id=data.level_id,
            scheduled_at=data.scheduled_at,
            status=DunningCampaignStatus.DRAFT,
            created_by=created_by,
        )
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def run_campaign(self, campaign_id: UUID) -> DunningCampaign:
        """Exécuter une campagne de relance."""
        campaign = self.db.query(DunningCampaign).filter(
            DunningCampaign.tenant_id == self.tenant_id,
            DunningCampaign.id == campaign_id
        ).first()

        if not campaign:
            raise ValueError(f"Campagne {campaign_id} introuvable")

        if campaign.status not in [DunningCampaignStatus.DRAFT, DunningCampaignStatus.SCHEDULED]:
            raise ValueError(f"Campagne {campaign_id} ne peut pas être démarrée (status: {campaign.status})")

        campaign.status = DunningCampaignStatus.RUNNING
        campaign.started_at = datetime.utcnow()

        level = self.get_level(campaign.level_id)
        if not level:
            raise ValueError(f"Niveau {campaign.level_id} introuvable")

        # Récupérer les factures éligibles
        overdue = self.get_overdue_invoices(min_days_overdue=level.days_after_due)

        campaign.total_invoices = len(overdue)
        campaign.total_amount = sum(inv.amount_due for inv in overdue)

        # Créer les actions
        for invoice in overdue:
            try:
                action = self.create_action(
                    invoice=invoice,
                    level=level,
                    campaign_id=campaign.id,
                )
                # Envoyer si envoi automatique
                self.send_action(action.id)
                campaign.sent_count += 1
            except Exception as e:
                campaign.failed_count += 1
                logger.error(f"[Dunning] Échec pour {invoice.invoice_number}: {e}")

        campaign.status = DunningCampaignStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()

        self.db.commit()
        return campaign

    # ========================================================================
    # PAYMENT PROMISES
    # ========================================================================

    def create_promise(
        self,
        data: PaymentPromiseCreate,
        recorded_by: Optional[str] = None
    ) -> PaymentPromise:
        """Enregistrer une promesse de paiement."""
        promise = PaymentPromise(
            tenant_id=self.tenant_id,
            invoice_id=data.invoice_id,
            customer_id=data.customer_id,
            dunning_action_id=data.dunning_action_id,
            promised_amount=data.promised_amount,
            promised_date=data.promised_date,
            contact_name=data.contact_name,
            contact_method=data.contact_method,
            notes=data.notes,
            recorded_by=recorded_by,
        )
        self.db.add(promise)
        self.db.commit()
        self.db.refresh(promise)
        return promise

    def update_promise(
        self,
        promise_id: UUID,
        data: PaymentPromiseUpdate
    ) -> PaymentPromise:
        """Mettre à jour une promesse de paiement."""
        promise = self.db.query(PaymentPromise).filter(
            PaymentPromise.tenant_id == self.tenant_id,
            PaymentPromise.id == promise_id
        ).first()

        if not promise:
            raise ValueError(f"Promesse {promise_id} introuvable")

        if data.status:
            promise.status = PaymentPromiseStatus(data.status)
        if data.actual_amount is not None:
            promise.actual_amount = data.actual_amount
        if data.actual_date:
            promise.actual_date = data.actual_date
        if data.notes:
            promise.notes = data.notes

        promise.updated_at = datetime.utcnow()
        self.db.commit()
        return promise

    def check_broken_promises(self) -> list[PaymentPromise]:
        """Vérifier les promesses non tenues."""
        today = date.today()
        broken = self.db.query(PaymentPromise).filter(
            PaymentPromise.tenant_id == self.tenant_id,
            PaymentPromise.status == PaymentPromiseStatus.PENDING,
            PaymentPromise.promised_date < today
        ).all()

        for promise in broken:
            promise.status = PaymentPromiseStatus.BROKEN
            promise.updated_at = datetime.utcnow()

        if broken:
            self.db.commit()
            logger.info(f"[Dunning] {len(broken)} promesses marquées comme non tenues")

        return broken

    # ========================================================================
    # CUSTOMER PROFILES
    # ========================================================================

    def get_or_create_profile(
        self,
        customer_id: str,
        customer_name: str
    ) -> CustomerDunningProfile:
        """Récupérer ou créer un profil de relance client."""
        profile = self.db.query(CustomerDunningProfile).filter(
            CustomerDunningProfile.tenant_id == self.tenant_id,
            CustomerDunningProfile.customer_id == customer_id
        ).first()

        if not profile:
            profile = CustomerDunningProfile(
                tenant_id=self.tenant_id,
                customer_id=customer_id,
                customer_name=customer_name,
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

        return profile

    def update_profile(
        self,
        customer_id: str,
        data: CustomerDunningProfileUpdate
    ) -> CustomerDunningProfile:
        """Mettre à jour un profil client."""
        profile = self.db.query(CustomerDunningProfile).filter(
            CustomerDunningProfile.tenant_id == self.tenant_id,
            CustomerDunningProfile.customer_id == customer_id
        ).first()

        if not profile:
            raise ValueError(f"Profil client {customer_id} introuvable")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)

        profile.updated_at = datetime.utcnow()
        self.db.commit()
        return profile

    def block_customer_dunning(
        self,
        customer_id: str,
        reason: str
    ) -> CustomerDunningProfile:
        """Bloquer les relances pour un client."""
        profile = self.db.query(CustomerDunningProfile).filter(
            CustomerDunningProfile.tenant_id == self.tenant_id,
            CustomerDunningProfile.customer_id == customer_id
        ).first()

        if not profile:
            raise ValueError(f"Profil client {customer_id} introuvable")

        profile.dunning_blocked = True
        profile.block_reason = reason
        profile.updated_at = datetime.utcnow()

        self.db.commit()
        logger.info(f"[Dunning] Client {customer_id} bloqué: {reason}")
        return profile

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_statistics(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> DunningStatistics:
        """Récupérer les statistiques des relances."""
        query = self.db.query(DunningAction).filter(
            DunningAction.tenant_id == self.tenant_id
        )

        if from_date:
            query = query.filter(DunningAction.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.filter(DunningAction.created_at <= datetime.combine(to_date, datetime.max.time()))

        actions = query.all()

        total = len(actions)
        sent = len([a for a in actions if a.status in [DunningStatus.SENT, DunningStatus.DELIVERED, DunningStatus.READ]])
        delivered = len([a for a in actions if a.status in [DunningStatus.DELIVERED, DunningStatus.READ]])
        failed = len([a for a in actions if a.status == DunningStatus.FAILED])

        total_relanced = sum(a.amount_due for a in actions)
        total_recovered = sum(a.payment_amount or Decimal("0") for a in actions if a.payment_received)

        delivery_rate = (delivered / sent * 100) if sent > 0 else 0.0
        recovery_rate = (float(total_recovered / total_relanced) * 100) if total_relanced > 0 else 0.0

        # Par niveau
        by_level = {}
        for action in actions:
            level_id = str(action.level_id)
            if level_id not in by_level:
                by_level[level_id] = {"count": 0, "amount": Decimal("0"), "recovered": Decimal("0")}
            by_level[level_id]["count"] += 1
            by_level[level_id]["amount"] += action.amount_due
            if action.payment_received:
                by_level[level_id]["recovered"] += action.payment_amount or Decimal("0")

        # Par canal
        by_channel = {}
        for action in actions:
            channel = action.channel.value
            if channel not in by_channel:
                by_channel[channel] = {"count": 0, "sent": 0, "delivered": 0}
            by_channel[channel]["count"] += 1
            if action.status in [DunningStatus.SENT, DunningStatus.DELIVERED, DunningStatus.READ]:
                by_channel[channel]["sent"] += 1
            if action.status in [DunningStatus.DELIVERED, DunningStatus.READ]:
                by_channel[channel]["delivered"] += 1

        return DunningStatistics(
            total_actions=total,
            sent_count=sent,
            delivered_count=delivered,
            failed_count=failed,
            delivery_rate=delivery_rate,
            total_amount_relanced=total_relanced,
            total_amount_recovered=total_recovered,
            recovery_rate=recovery_rate,
            by_level=by_level,
            by_channel=by_channel,
        )

    def get_aging_analysis(self) -> OverdueAnalysis:
        """Analyse du vieillissement des créances."""
        overdue = self.get_overdue_invoices()

        by_aging = {
            "0-30": {"count": 0, "amount": Decimal("0")},
            "31-60": {"count": 0, "amount": Decimal("0")},
            "61-90": {"count": 0, "amount": Decimal("0")},
            "90+": {"count": 0, "amount": Decimal("0")},
        }

        by_customer: dict[str, dict] = {}
        by_level: dict[str, dict] = {}

        for inv in overdue:
            # Catégoriser par âge
            if inv.days_overdue <= 30:
                bucket = "0-30"
            elif inv.days_overdue <= 60:
                bucket = "31-60"
            elif inv.days_overdue <= 90:
                bucket = "61-90"
            else:
                bucket = "90+"

            by_aging[bucket]["count"] += 1
            by_aging[bucket]["amount"] += inv.amount_due

            # Par client
            if inv.customer_id not in by_customer:
                by_customer[inv.customer_id] = {
                    "customer_id": inv.customer_id,
                    "customer_name": inv.customer_name,
                    "count": 0,
                    "amount": Decimal("0"),
                }
            by_customer[inv.customer_id]["count"] += 1
            by_customer[inv.customer_id]["amount"] += inv.amount_due

            # Par niveau actuel
            level = inv.current_level or "NONE"
            if level not in by_level:
                by_level[level] = {"count": 0, "amount": Decimal("0")}
            by_level[level]["count"] += 1
            by_level[level]["amount"] += inv.amount_due

        return OverdueAnalysis(
            total_invoices=len(overdue),
            total_amount=sum(inv.amount_due for inv in overdue),
            by_aging=by_aging,
            by_customer=sorted(by_customer.values(), key=lambda x: x["amount"], reverse=True)[:20],
            by_level=by_level,
        )
