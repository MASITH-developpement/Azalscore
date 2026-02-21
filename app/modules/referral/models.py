"""
Modèles SQLAlchemy Referral / Parrainage
=========================================
- Multi-tenant obligatoire (tenant_id sur TOUTES les entités)
- Soft delete (is_deleted, deleted_at, deleted_by)
- Audit complet (created_at/by, updated_at/by)
- Versioning (optimistic locking)

Entités:
- ReferralProgram (Programme de parrainage)
- RewardTier (Palier de récompense)
- ReferralCode (Code de parrainage)
- Referral (Parrainage individuel)
- Reward (Récompense attribuée)
- Payout (Paiement de commission)
- FraudCheck (Vérification anti-fraude)
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum, event
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.db import Base


# ============== Énumérations ==============

class ProgramStatus(str, Enum):
    """Statut du programme de parrainage."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ARCHIVED = "archived"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.DRAFT: [cls.ACTIVE, cls.ARCHIVED],
            cls.ACTIVE: [cls.PAUSED, cls.ENDED],
            cls.PAUSED: [cls.ACTIVE, cls.ENDED],
            cls.ENDED: [cls.ARCHIVED],
            cls.ARCHIVED: []
        }


class RewardType(str, Enum):
    """Type de récompense."""
    CASH = "cash"
    CREDIT = "credit"
    DISCOUNT_PERCENT = "discount_percent"
    DISCOUNT_AMOUNT = "discount_amount"
    FREE_PRODUCT = "free_product"
    FREE_SERVICE = "free_service"
    POINTS = "points"
    GIFT_CARD = "gift_card"
    CUSTOM = "custom"


class RewardTrigger(str, Enum):
    """Déclencheur de récompense."""
    SIGNUP = "signup"
    FIRST_PURCHASE = "first_purchase"
    PURCHASE_AMOUNT = "purchase_amount"
    SUBSCRIPTION = "subscription"
    MILESTONE = "milestone"
    MANUAL = "manual"


class ReferralStatus(str, Enum):
    """Statut du parrainage."""
    PENDING = "pending"
    CLICKED = "clicked"
    SIGNED_UP = "signed_up"
    CONVERTED = "converted"
    QUALIFIED = "qualified"
    REWARDED = "rewarded"
    EXPIRED = "expired"
    REJECTED = "rejected"
    FRAUDULENT = "fraudulent"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.PENDING: [cls.CLICKED, cls.EXPIRED],
            cls.CLICKED: [cls.SIGNED_UP, cls.EXPIRED],
            cls.SIGNED_UP: [cls.CONVERTED, cls.EXPIRED, cls.REJECTED],
            cls.CONVERTED: [cls.QUALIFIED, cls.REJECTED, cls.FRAUDULENT],
            cls.QUALIFIED: [cls.REWARDED, cls.REJECTED, cls.FRAUDULENT],
            cls.REWARDED: [cls.FRAUDULENT],
            cls.EXPIRED: [],
            cls.REJECTED: [],
            cls.FRAUDULENT: []
        }


class PayoutStatus(str, Enum):
    """Statut du paiement."""
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class FraudReason(str, Enum):
    """Raison de fraude détectée."""
    SELF_REFERRAL = "self_referral"
    SAME_IP = "same_ip"
    SAME_DEVICE = "same_device"
    SAME_PAYMENT = "same_payment"
    VELOCITY = "velocity"
    PATTERN = "pattern"
    MANUAL_FLAG = "manual_flag"


# ============== Modèles ==============

class ReferralProgram(Base):
    """
    Programme de parrainage.

    Définit les règles et récompenses du programme.
    """
    __tablename__ = "referral_programs"

    # === Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Statut ===
    status = Column(
        SQLEnum(ProgramStatus, name="program_status_enum", create_type=False),
        default=ProgramStatus.DRAFT,
        nullable=False
    )

    # === Période ===
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # === Configuration conversion ===
    require_conversion = Column(Boolean, default=True, nullable=False)
    conversion_window_days = Column(Integer, default=30, nullable=False)
    min_conversion_amount = Column(Numeric(15, 2), default=Decimal("0"))

    # === Limites ===
    max_referrals_per_referrer = Column(Integer, nullable=True)
    max_total_referrals = Column(Integer, nullable=True)
    current_total_referrals = Column(Integer, default=0)

    # === Multi-niveau ===
    multi_level_enabled = Column(Boolean, default=False, nullable=False)
    max_levels = Column(Integer, default=1, nullable=False)
    level_commission_rates = Column(ARRAY(Numeric(5, 2)), default=list)

    # === Budget ===
    total_budget = Column(Numeric(15, 2), nullable=True)
    spent_budget = Column(Numeric(15, 2), default=Decimal("0"))
    currency = Column(String(3), default="EUR", nullable=False)

    # === Options ===
    allow_self_referral = Column(Boolean, default=False, nullable=False)
    require_unique_email = Column(Boolean, default=True, nullable=False)
    require_unique_device = Column(Boolean, default=True, nullable=False)

    # === Éligibilité ===
    eligible_user_segments = Column(ARRAY(String), default=list)
    excluded_user_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)

    # === Tracking ===
    total_clicks = Column(Integer, default=0)
    total_signups = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_rewards_paid = Column(Numeric(15, 2), default=Decimal("0"))

    # === Conditions ===
    terms_conditions = Column(Text, default="")

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # === Optimistic Locking ===
    version = Column(Integer, default=1, nullable=False)

    # === Métadonnées ===
    tags = Column(ARRAY(String), default=list)
    extra_data = Column(JSONB, default=dict)

    # === Relations ===
    tiers = relationship("RewardTier", back_populates="program", lazy="dynamic")
    codes = relationship("ReferralCode", back_populates="program", lazy="dynamic")
    referrals = relationship("Referral", back_populates="program", lazy="dynamic")

    # === Contraintes ===
    __table_args__ = (
        Index('ix_refprog_tenant', 'tenant_id'),
        Index('ix_refprog_tenant_code', 'tenant_id', 'code'),
        Index('ix_refprog_tenant_status', 'tenant_id', 'status'),
        Index('ix_refprog_tenant_deleted', 'tenant_id', 'is_deleted'),
        UniqueConstraint('tenant_id', 'code', name='uq_refprog_tenant_code'),
        CheckConstraint('conversion_window_days > 0', name='ck_refprog_window_positive'),
        CheckConstraint('max_levels >= 1', name='ck_refprog_levels_min'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def is_active(self) -> bool:
        return self.status == ProgramStatus.ACTIVE and not self.is_deleted

    @hybrid_property
    def budget_remaining(self) -> Optional[Decimal]:
        if self.total_budget is None:
            return None
        return self.total_budget - self.spent_budget

    @hybrid_property
    def conversion_rate(self) -> Decimal:
        if self.total_clicks == 0:
            return Decimal("0")
        return Decimal(str(self.total_conversions / self.total_clicks * 100))

    def can_delete(self) -> tuple:
        if self.status == ProgramStatus.ACTIVE:
            return False, "Cannot delete active program"
        if self.current_total_referrals > 0:
            return False, "Cannot delete program with referrals"
        return True, ""

    def __repr__(self) -> str:
        return f"<ReferralProgram {self.code}: {self.name}>"


class RewardTier(Base):
    """
    Palier de récompense.

    Définit les récompenses selon le nombre de parrainages.
    """
    __tablename__ = "referral_reward_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey('referral_programs.id'), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Conditions ===
    min_referrals = Column(Integer, default=0, nullable=False)
    max_referrals = Column(Integer, nullable=True)
    min_conversion_amount = Column(Numeric(15, 2), default=Decimal("0"))

    # === Récompense parrain ===
    referrer_reward_type = Column(
        SQLEnum(RewardType, name="reward_type_enum", create_type=False),
        default=RewardType.CREDIT,
        nullable=False
    )
    referrer_reward_value = Column(Numeric(15, 2), default=Decimal("0"))
    referrer_reward_description = Column(String(500), default="")

    # === Récompense filleul ===
    referee_reward_type = Column(
        SQLEnum(RewardType, name="reward_type_enum", create_type=False),
        default=RewardType.DISCOUNT_PERCENT,
        nullable=False
    )
    referee_reward_value = Column(Numeric(15, 2), default=Decimal("0"))
    referee_reward_description = Column(String(500), default="")

    # === Limites ===
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)

    # === Ordre et activation ===
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # === Relations ===
    program = relationship("ReferralProgram", back_populates="tiers")

    __table_args__ = (
        Index('ix_reftier_tenant', 'tenant_id'),
        Index('ix_reftier_program', 'program_id'),
        CheckConstraint('min_referrals >= 0', name='ck_reftier_min_refs'),
        CheckConstraint('referrer_reward_value >= 0', name='ck_reftier_referrer_value'),
        CheckConstraint('referee_reward_value >= 0', name='ck_reftier_referee_value'),
    )


class ReferralCode(Base):
    """
    Code de parrainage individuel.

    Chaque parrain peut avoir un ou plusieurs codes.
    """
    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey('referral_programs.id'), nullable=False)
    referrer_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # === Code ===
    code = Column(String(50), nullable=False)
    short_url = Column(String(255), nullable=True)

    # === Statistiques ===
    total_clicks = Column(Integer, default=0)
    total_signups = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_earnings = Column(Numeric(15, 2), default=Decimal("0"))

    # === Limites ===
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)

    # === Validité ===
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # === Personnalisation ===
    custom_message = Column(Text, default="")

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # === Métadonnées ===
    extra_data = Column(JSONB, default=dict)

    # === Relations ===
    program = relationship("ReferralProgram", back_populates="codes")
    referrals = relationship("Referral", back_populates="referral_code", lazy="dynamic")

    __table_args__ = (
        Index('ix_refcode_tenant', 'tenant_id'),
        Index('ix_refcode_program', 'program_id'),
        Index('ix_refcode_referrer', 'referrer_id'),
        Index('ix_refcode_code', 'tenant_id', 'code'),
        UniqueConstraint('tenant_id', 'code', name='uq_refcode_tenant_code'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def conversion_rate(self) -> Decimal:
        if self.total_clicks == 0:
            return Decimal("0")
        return Decimal(str(self.total_conversions / self.total_clicks * 100))

    @hybrid_property
    def is_valid(self) -> bool:
        if not self.is_active or self.is_deleted:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True


class Referral(Base):
    """
    Parrainage individuel.

    Représente un parrainage du clic jusqu'à la récompense.
    """
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey('referral_programs.id'), nullable=False)
    referral_code_id = Column(UUID(as_uuid=True), ForeignKey('referral_codes.id'), nullable=False)

    # === Acteurs ===
    referrer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    referee_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    referee_email = Column(String(255), default="")
    referee_name = Column(String(255), default="")

    # === Statut ===
    status = Column(
        SQLEnum(ReferralStatus, name="referral_status_enum", create_type=False),
        default=ReferralStatus.PENDING,
        nullable=False
    )

    # === Timestamps ===
    click_timestamp = Column(DateTime, nullable=True)
    signup_timestamp = Column(DateTime, nullable=True)
    conversion_timestamp = Column(DateTime, nullable=True)
    qualification_timestamp = Column(DateTime, nullable=True)

    # === Conversion ===
    conversion_order_id = Column(UUID(as_uuid=True), nullable=True)
    conversion_amount = Column(Numeric(15, 2), default=Decimal("0"))

    # === Multi-niveau ===
    level = Column(Integer, default=1, nullable=False)
    parent_referral_id = Column(UUID(as_uuid=True), ForeignKey('referrals.id'), nullable=True)

    # === Attribution / Tracking ===
    ip_address = Column(String(45), default="")
    user_agent = Column(Text, default="")
    device_fingerprint = Column(String(255), default="")
    utm_source = Column(String(100), default="")
    utm_medium = Column(String(100), default="")
    utm_campaign = Column(String(100), default="")
    landing_page = Column(Text, default="")

    # === Fraude ===
    fraud_score = Column(Numeric(5, 2), default=Decimal("0"))
    fraud_flags = Column(ARRAY(String), default=list)
    is_suspicious = Column(Boolean, default=False, nullable=False)

    # === Récompenses ===
    referrer_reward_id = Column(UUID(as_uuid=True), nullable=True)
    referee_reward_id = Column(UUID(as_uuid=True), nullable=True)

    # === Notes ===
    notes = Column(Text, default="")

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # === Métadonnées ===
    extra_data = Column(JSONB, default=dict)

    # === Relations ===
    program = relationship("ReferralProgram", back_populates="referrals")
    referral_code = relationship("ReferralCode", back_populates="referrals")
    parent = relationship("Referral", remote_side="Referral.id", backref="children")
    rewards = relationship("Reward", back_populates="referral", lazy="dynamic")
    fraud_checks = relationship("FraudCheck", back_populates="referral", lazy="dynamic")

    __table_args__ = (
        Index('ix_referral_tenant', 'tenant_id'),
        Index('ix_referral_program', 'program_id'),
        Index('ix_referral_code', 'referral_code_id'),
        Index('ix_referral_referrer', 'referrer_id'),
        Index('ix_referral_referee', 'referee_id'),
        Index('ix_referral_status', 'tenant_id', 'status'),
        CheckConstraint('level >= 1', name='ck_referral_level_min'),
        CheckConstraint('conversion_amount >= 0', name='ck_referral_amount_positive'),
    )


class Reward(Base):
    """
    Récompense attribuée.

    Représente une récompense pour parrain ou filleul.
    """
    __tablename__ = "referral_rewards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey('referral_programs.id'), nullable=False)
    referral_id = Column(UUID(as_uuid=True), ForeignKey('referrals.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # === Type de bénéficiaire ===
    is_referrer_reward = Column(Boolean, default=True, nullable=False)

    # === Récompense ===
    reward_type = Column(
        SQLEnum(RewardType, name="reward_type_enum", create_type=False),
        default=RewardType.CREDIT,
        nullable=False
    )
    reward_value = Column(Numeric(15, 2), default=Decimal("0"))
    currency = Column(String(3), default="EUR", nullable=False)
    description = Column(String(500), default="")

    # === Statut ===
    is_claimed = Column(Boolean, default=False, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # === Détails selon le type ===
    discount_code = Column(String(50), nullable=True)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    credit_transaction_id = Column(UUID(as_uuid=True), nullable=True)

    # === Payout ===
    payout_id = Column(UUID(as_uuid=True), ForeignKey('referral_payouts.id'), nullable=True)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # === Relations ===
    referral = relationship("Referral", back_populates="rewards")
    payout = relationship("Payout", back_populates="rewards")

    __table_args__ = (
        Index('ix_reward_tenant', 'tenant_id'),
        Index('ix_reward_user', 'user_id'),
        Index('ix_reward_referral', 'referral_id'),
        CheckConstraint('reward_value >= 0', name='ck_reward_value_positive'),
    )

    @hybrid_property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class Payout(Base):
    """
    Paiement de commission.

    Regroupe plusieurs récompenses en un paiement.
    """
    __tablename__ = "referral_payouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # === Montant ===
    amount = Column(Numeric(15, 2), default=Decimal("0"))
    currency = Column(String(3), default="EUR", nullable=False)

    # === Statut ===
    status = Column(
        SQLEnum(PayoutStatus, name="payout_status_enum", create_type=False),
        default=PayoutStatus.PENDING,
        nullable=False
    )

    # === Paiement ===
    payment_method = Column(String(50), default="")
    payment_details = Column(JSONB, default=dict)

    # === Tracking ===
    processed_at = Column(DateTime, nullable=True)
    transaction_reference = Column(String(255), default="")
    failure_reason = Column(Text, default="")

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # === Relations ===
    rewards = relationship("Reward", back_populates="payout", lazy="dynamic")

    __table_args__ = (
        Index('ix_payout_tenant', 'tenant_id'),
        Index('ix_payout_user', 'user_id'),
        Index('ix_payout_status', 'tenant_id', 'status'),
        CheckConstraint('amount >= 0', name='ck_payout_amount_positive'),
    )


class FraudCheck(Base):
    """
    Vérification anti-fraude.

    Enregistre les résultats des vérifications.
    """
    __tablename__ = "referral_fraud_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    referral_id = Column(UUID(as_uuid=True), ForeignKey('referrals.id'), nullable=False)

    # === Type de vérification ===
    check_type = Column(String(50), nullable=False)  # ip, device, email, velocity

    # === Résultat ===
    result = Column(String(20), nullable=False)  # pass, fail, warning
    score = Column(Numeric(5, 2), default=Decimal("0"))

    # === Détails ===
    details = Column(JSONB, default=dict)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # === Relations ===
    referral = relationship("Referral", back_populates="fraud_checks")

    __table_args__ = (
        Index('ix_fraudcheck_tenant', 'tenant_id'),
        Index('ix_fraudcheck_referral', 'referral_id'),
    )


# ============== Event Listeners ==============

@event.listens_for(ReferralProgram, 'before_update')
def increment_program_version(mapper, connection, target):
    """Incrémenter la version avant mise à jour."""
    target.version += 1


@event.listens_for(ReferralCode, 'before_insert')
def set_code_expiry(mapper, connection, target):
    """Définir l'expiration basée sur le programme si non spécifiée."""
    if target.expires_at is None and target.program:
        if target.program.end_date:
            target.expires_at = datetime.combine(
                target.program.end_date, datetime.max.time()
            )
