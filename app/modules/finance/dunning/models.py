"""
AZALS MODULE - Dunning (Relances Impayés)
==========================================

Modèles SQLAlchemy pour la gestion des relances impayés.

Fonctionnalités:
- Niveaux de relance avec escalade automatique
- Règles de relance configurables par tenant
- Templates email/SMS personnalisables
- Historique complet des actions
- Intégration avec les factures et clients
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.types import UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================


class DunningLevelType(str, PyEnum):
    """Type de niveau de relance."""
    REMINDER = "REMINDER"          # Rappel simple
    FIRST_NOTICE = "FIRST_NOTICE"  # 1ère relance
    SECOND_NOTICE = "SECOND_NOTICE"  # 2ème relance
    FORMAL_NOTICE = "FORMAL_NOTICE"  # Mise en demeure
    FINAL_NOTICE = "FINAL_NOTICE"   # Dernière relance avant contentieux
    COLLECTION = "COLLECTION"       # Transmission au recouvrement


class DunningChannel(str, PyEnum):
    """Canal de communication pour les relances."""
    EMAIL = "EMAIL"
    SMS = "SMS"
    LETTER = "LETTER"       # Courrier postal
    PHONE = "PHONE"         # Appel téléphonique
    REGISTERED = "REGISTERED"  # Recommandé AR


class DunningStatus(str, PyEnum):
    """Statut d'une relance."""
    PENDING = "PENDING"     # En attente d'envoi
    SENT = "SENT"           # Envoyée
    DELIVERED = "DELIVERED"  # Délivrée
    READ = "READ"           # Lue (email/SMS)
    FAILED = "FAILED"       # Échec d'envoi
    CANCELLED = "CANCELLED"  # Annulée


class DunningCampaignStatus(str, PyEnum):
    """Statut d'une campagne de relance."""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class PaymentPromiseStatus(str, PyEnum):
    """Statut d'une promesse de paiement."""
    PENDING = "PENDING"     # En attente de la date promise
    KEPT = "KEPT"           # Promesse tenue
    BROKEN = "BROKEN"       # Promesse non tenue
    PARTIAL = "PARTIAL"     # Paiement partiel reçu
    CANCELLED = "CANCELLED"  # Annulée


# ============================================================================
# MODÈLES
# ============================================================================


class DunningLevel(Base):
    """
    Niveau de relance configuré par tenant.

    Définit l'escalade des relances avec délais et canaux.
    """
    __tablename__ = "dunning_levels"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # Ex: LEVEL_1
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level_type: Mapped[str] = mapped_column(Enum(DunningLevelType), nullable=False)

    # Ordre dans l'escalade
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Délais
    days_after_due: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    days_before_next: Mapped[int | None] = mapped_column(Integer)  # Délai avant niveau suivant

    # Canaux autorisés pour ce niveau
    channels: Mapped[list] = mapped_column(JSON, default=lambda: ["EMAIL"])
    primary_channel: Mapped[str] = mapped_column(Enum(DunningChannel), default=DunningChannel.EMAIL)

    # Actions automatiques
    block_orders: Mapped[bool] = mapped_column(Boolean, default=False)  # Bloquer les commandes
    add_fees: Mapped[bool] = mapped_column(Boolean, default=False)      # Ajouter des frais
    fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    fee_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # % du montant dû

    # Intérêts de retard (40€ min selon art. L441-10 Code de commerce)
    apply_late_interest: Mapped[bool] = mapped_column(Boolean, default=False)
    late_interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # Taux annuel
    fixed_recovery_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=Decimal("40.00"))

    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relations
    templates = relationship("DunningTemplate", back_populates="level")

    __table_args__ = (
        Index("ix_dunning_level_tenant_seq", "tenant_id", "sequence"),
        Index("ix_dunning_level_tenant_code", "tenant_id", "code", unique=True),
    )


class DunningTemplate(Base):
    """
    Template de relance (email, SMS, courrier).
    """
    __tablename__ = "dunning_templates"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Niveau de relance associé
    level_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("dunning_levels.id"), nullable=False)

    # Type de canal
    channel: Mapped[str] = mapped_column(Enum(DunningChannel), nullable=False)

    # Langue
    language: Mapped[str] = mapped_column(String(5), default="fr")

    # Contenu
    subject: Mapped[str | None] = mapped_column(String(500))  # Pour email
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Variables disponibles: {customer_name}, {invoice_number}, {amount_due},
    # {due_date}, {days_overdue}, {total_fees}, {company_name}, {payment_link}

    # Configuration
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relations
    level = relationship("DunningLevel", back_populates="templates")

    __table_args__ = (
        Index("ix_dunning_template_tenant_level", "tenant_id", "level_id"),
    )


class DunningRule(Base):
    """
    Règles de déclenchement des relances.

    Permet de personnaliser les critères de relance par:
    - Segment client (VIP, standard, à risque)
    - Montant minimum
    - Type de facture
    - Etc.
    """
    __tablename__ = "dunning_rules"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Priorité (plus bas = plus prioritaire)
    priority: Mapped[int] = mapped_column(Integer, default=100)

    # Conditions (JSON avec critères)
    # Ex: {"min_amount": 100, "customer_segment": "VIP", "invoice_type": "SERVICE"}
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)

    # Niveau de départ (si conditions matchent)
    start_level_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID(), ForeignKey("dunning_levels.id"))

    # Montant minimum pour relancer
    min_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Jours de grâce supplémentaires
    grace_days: Mapped[int] = mapped_column(Integer, default=0)

    # Exclure certains jours (weekends, jours fériés)
    exclude_weekends: Mapped[bool] = mapped_column(Boolean, default=True)
    exclude_holidays: Mapped[bool] = mapped_column(Boolean, default=True)

    # Actions
    auto_send: Mapped[bool] = mapped_column(Boolean, default=True)  # Envoi automatique
    require_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_dunning_rule_tenant_priority", "tenant_id", "priority"),
    )


class DunningAction(Base):
    """
    Action de relance effectuée sur une facture.

    Historique complet de toutes les relances envoyées.
    """
    __tablename__ = "dunning_actions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Référence facture (UUID string pour flexibilité cross-module)
    invoice_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)

    # Référence client
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255))
    customer_phone: Mapped[str | None] = mapped_column(String(50))

    # Niveau et canal
    level_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("dunning_levels.id"), nullable=False)
    channel: Mapped[str] = mapped_column(Enum(DunningChannel), nullable=False)

    # Campagne (si envoi groupé)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID(), ForeignKey("dunning_campaigns.id"))

    # Montants
    amount_due: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fees_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    interest_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    total_due: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Dates
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_overdue: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Statut
    status: Mapped[str] = mapped_column(Enum(DunningStatus), default=DunningStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Contenu envoyé (archivé)
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)

    # Tracking
    message_id: Mapped[str | None] = mapped_column(String(255))  # ID externe (Mailgun, Twilio, etc.)

    # Résultat
    payment_received: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    payment_date: Mapped[date | None] = mapped_column(Date)

    # Utilisateur
    created_by: Mapped[str | None] = mapped_column(String(50))  # ID utilisateur
    approved_by: Mapped[str | None] = mapped_column(String(50))

    # Notes
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_dunning_action_tenant_invoice", "tenant_id", "invoice_id"),
        Index("ix_dunning_action_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_dunning_action_tenant_status", "tenant_id", "status"),
        Index("ix_dunning_action_tenant_date", "tenant_id", "created_at"),
    )


class DunningCampaign(Base):
    """
    Campagne de relance groupée.

    Permet de traiter plusieurs factures en lot.
    """
    __tablename__ = "dunning_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Niveau cible
    level_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("dunning_levels.id"), nullable=False)

    # Planning
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Statut
    status: Mapped[str] = mapped_column(Enum(DunningCampaignStatus), default=DunningCampaignStatus.DRAFT)

    # Statistiques
    total_invoices: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    paid_count: Mapped[int] = mapped_column(Integer, default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # Utilisateur
    created_by: Mapped[str | None] = mapped_column(String(50))

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relations
    actions = relationship("DunningAction", backref="campaign")

    __table_args__ = (
        Index("ix_dunning_campaign_tenant_status", "tenant_id", "status"),
    )


class PaymentPromise(Base):
    """
    Promesse de paiement reçue d'un client.

    Permet de suivre les engagements de paiement.
    """
    __tablename__ = "payment_promises"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Référence
    invoice_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dunning_action_id: Mapped[uuid.UUID | None] = mapped_column(UniversalUUID(), ForeignKey("dunning_actions.id"))

    # Promesse
    promised_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    promised_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Résultat
    status: Mapped[str] = mapped_column(Enum(PaymentPromiseStatus), default=PaymentPromiseStatus.PENDING)
    actual_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    actual_date: Mapped[date | None] = mapped_column(Date)

    # Contact
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_method: Mapped[str | None] = mapped_column(String(50))  # phone, email, meeting

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Utilisateur
    recorded_by: Mapped[str | None] = mapped_column(String(50))

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_payment_promise_tenant_invoice", "tenant_id", "invoice_id"),
        Index("ix_payment_promise_tenant_date", "tenant_id", "promised_date"),
    )


class CustomerDunningProfile(Base):
    """
    Profil de relance par client.

    Permet de personnaliser les règles de relance par client:
    - Clients VIP avec traitement spécial
    - Clients à risque avec relances plus agressives
    - Clients bloqués (pas de relance)
    """
    __tablename__ = "customer_dunning_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Client
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Segment
    segment: Mapped[str | None] = mapped_column(String(50))  # VIP, STANDARD, AT_RISK, BLOCKED

    # Configuration spécifique
    dunning_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    block_reason: Mapped[str | None] = mapped_column(Text)
    custom_grace_days: Mapped[int | None] = mapped_column(Integer)
    custom_min_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Préférences de contact
    preferred_channel: Mapped[str | None] = mapped_column(Enum(DunningChannel))
    preferred_language: Mapped[str] = mapped_column(String(5), default="fr")
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))

    # Statistiques
    total_overdue_count: Mapped[int] = mapped_column(Integer, default=0)
    total_overdue_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    avg_days_to_pay: Mapped[int | None] = mapped_column(Integer)
    last_dunning_date: Mapped[date | None] = mapped_column(Date)
    last_payment_date: Mapped[date | None] = mapped_column(Date)

    # Risque
    risk_score: Mapped[int | None] = mapped_column(Integer)  # 0-100

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_customer_dunning_tenant_customer", "tenant_id", "customer_id", unique=True),
        Index("ix_customer_dunning_tenant_segment", "tenant_id", "segment"),
    )
