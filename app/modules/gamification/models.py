"""
AZALS MODULE GAMIFICATION - Modeles SQLAlchemy
===============================================

Modeles pour le systeme de gamification complet:
- Points et niveaux utilisateurs
- Badges et achievements
- Defis et objectifs
- Classements (leaderboards)
- Recompenses
- Regles d'attribution automatique
- Equipes et competitions
- Historique progression

Inspire de: Salesforce (Trailhead), Microsoft Dynamics 365 Gamification, SAP SuccessFactors

Architecture multi-tenant avec isolation stricte.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.types import JSONB, UniversalUUID
from app.db import Base


# =============================================================================
# ENUMS
# =============================================================================

class PointType(str, enum.Enum):
    """Types de points."""
    XP = "xp"  # Experience points
    COINS = "coins"  # Monnaie virtuelle
    KARMA = "karma"  # Points de reputation
    BONUS = "bonus"  # Points bonus temporaires
    CREDITS = "credits"  # Credits echangeables


class TransactionType(str, enum.Enum):
    """Types de transaction de points."""
    EARN = "earn"
    SPEND = "spend"
    TRANSFER = "transfer"
    EXPIRE = "expire"
    ADJUST = "adjust"
    REFUND = "refund"


class BadgeRarity(str, enum.Enum):
    """Rarete des badges."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


class BadgeStatus(str, enum.Enum):
    """Statut d'un badge pour un utilisateur."""
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    UNLOCKED = "unlocked"
    CLAIMED = "claimed"


class ChallengeType(str, enum.Enum):
    """Types de defi."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    SPECIAL = "special"
    PERMANENT = "permanent"
    TEAM = "team"


class ChallengeStatus(str, enum.Enum):
    """Statut d'un defi."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RewardType(str, enum.Enum):
    """Types de recompense."""
    POINTS = "points"
    BADGE = "badge"
    DISCOUNT = "discount"
    PHYSICAL = "physical"
    FEATURE = "feature"
    ACCESS = "access"
    CUSTOM = "custom"
    VOUCHER = "voucher"


class RewardStatus(str, enum.Enum):
    """Statut d'une recompense reclamee."""
    PENDING = "pending"
    PROCESSING = "processing"
    FULFILLED = "fulfilled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class LeaderboardPeriod(str, enum.Enum):
    """Periodes de classement."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


class LeaderboardScope(str, enum.Enum):
    """Portee du classement."""
    GLOBAL = "global"
    TEAM = "team"
    DEPARTMENT = "department"
    REGION = "region"
    CUSTOM = "custom"


class RuleEventType(str, enum.Enum):
    """Types d'evenements declencheurs."""
    ACTION_COMPLETED = "action_completed"
    TARGET_REACHED = "target_reached"
    STREAK_MILESTONE = "streak_milestone"
    LEVEL_UP = "level_up"
    BADGE_UNLOCKED = "badge_unlocked"
    CHALLENGE_COMPLETED = "challenge_completed"
    REFERRAL = "referral"
    CUSTOM = "custom"


class CompetitionStatus(str, enum.Enum):
    """Statut d'une competition."""
    DRAFT = "draft"
    REGISTRATION = "registration"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationType(str, enum.Enum):
    """Types de notifications gamification."""
    POINTS_EARNED = "points_earned"
    LEVEL_UP = "level_up"
    BADGE_UNLOCKED = "badge_unlocked"
    CHALLENGE_COMPLETED = "challenge_completed"
    REWARD_AVAILABLE = "reward_available"
    STREAK_WARNING = "streak_warning"
    STREAK_BROKEN = "streak_broken"
    LEADERBOARD_CHANGE = "leaderboard_change"
    COMPETITION_START = "competition_start"
    TEAM_INVITE = "team_invite"


# =============================================================================
# MODELES POINTS & NIVEAUX
# =============================================================================

class GamificationLevel(Base):
    """Definition des niveaux de progression."""
    __tablename__ = "gamification_levels"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    level_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    min_xp = Column(Integer, nullable=False, default=0)
    max_xp = Column(Integer, nullable=True)  # NULL pour le dernier niveau

    # Visuels
    icon = Column(String(255), nullable=True)
    color = Column(String(20), nullable=True)
    badge_id = Column(UniversalUUID(), ForeignKey("gamification_badges.id"), nullable=True)

    # Avantages du niveau
    perks = Column(JSONB, default=list)  # ["perk1", "perk2"]
    multiplier = Column(Numeric(4, 2), default=Decimal("1.0"))  # Multiplicateur de points

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'level_number', name='uq_level_number'),
        Index('idx_gam_levels_tenant', 'tenant_id'),
    )


class UserGamificationProfile(Base):
    """Profil de gamification d'un utilisateur."""
    __tablename__ = "gamification_user_profiles"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    # Niveau actuel
    current_level = Column(Integer, default=1)
    current_xp = Column(Integer, default=0)
    lifetime_xp = Column(Integer, default=0)

    # Balances de points
    coins_balance = Column(Integer, default=0)
    karma_balance = Column(Integer, default=0)
    credits_balance = Column(Integer, default=0)

    # Totaux vie
    lifetime_coins_earned = Column(Integer, default=0)
    lifetime_coins_spent = Column(Integer, default=0)

    # Streaks
    current_login_streak = Column(Integer, default=0)
    longest_login_streak = Column(Integer, default=0)
    last_login_date = Column(Date, nullable=True)
    current_activity_streak = Column(Integer, default=0)
    longest_activity_streak = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)

    # Stats
    badges_unlocked = Column(Integer, default=0)
    challenges_completed = Column(Integer, default=0)
    rewards_claimed = Column(Integer, default=0)
    competitions_won = Column(Integer, default=0)

    # Equipe actuelle
    team_id = Column(UniversalUUID(), ForeignKey("gamification_teams.id"), nullable=True)

    # Avatar et personnalisation
    avatar_url = Column(String(500), nullable=True)
    title = Column(String(100), nullable=True)  # Titre affiche
    selected_badge_id = Column(UniversalUUID(), nullable=True)  # Badge principal affiche

    # Preferences
    notifications_enabled = Column(Boolean, default=True)
    public_profile = Column(Boolean, default=True)
    show_on_leaderboard = Column(Boolean, default=True)

    # Dates
    level_up_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Version pour optimistic locking
    version = Column(Integer, default=1)

    # Relations
    team = relationship("GamificationTeam", back_populates="members")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', name='uq_user_gamification_profile'),
        Index('idx_gam_profiles_tenant', 'tenant_id'),
        Index('idx_gam_profiles_user', 'tenant_id', 'user_id'),
        Index('idx_gam_profiles_level', 'tenant_id', 'current_level'),
        Index('idx_gam_profiles_team', 'tenant_id', 'team_id'),
    )


class PointTransaction(Base):
    """Transaction de points."""
    __tablename__ = "gamification_point_transactions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    point_type = Column(SQLEnum(PointType), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    # Details
    description = Column(String(500), nullable=True)
    source = Column(String(100), nullable=True)  # action, challenge, reward, etc.
    source_id = Column(UniversalUUID(), nullable=True)
    reference_type = Column(String(50), nullable=True)  # Type de l'entite source
    reference_id = Column(UniversalUUID(), nullable=True)  # ID de l'entite

    # Multiplicateurs appliques
    multiplier = Column(Numeric(4, 2), default=Decimal("1.0"))
    base_amount = Column(Integer, nullable=True)  # Montant avant multiplicateur

    # Expiration
    expires_at = Column(DateTime, nullable=True)
    is_expired = Column(Boolean, default=False)

    # Metadata (extra_data car 'metadata' reserve SQLAlchemy)
    extra_data = Column(JSONB, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_gam_transactions_tenant', 'tenant_id'),
        Index('idx_gam_transactions_user', 'tenant_id', 'user_id'),
        Index('idx_gam_transactions_type', 'tenant_id', 'point_type', 'transaction_type'),
        Index('idx_gam_transactions_source', 'tenant_id', 'source', 'source_id'),
        Index('idx_gam_transactions_date', 'tenant_id', 'created_at'),
    )


# =============================================================================
# MODELES BADGES
# =============================================================================

class BadgeCategory(Base):
    """Categorie de badges."""
    __tablename__ = "gamification_badge_categories"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)
    color = Column(String(20), nullable=True)
    sort_order = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    badges = relationship("GamificationBadge", back_populates="category")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_badge_category_code'),
        Index('idx_gam_badge_cat_tenant', 'tenant_id'),
    )


class GamificationBadge(Base):
    """Definition d'un badge."""
    __tablename__ = "gamification_badges"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(UniversalUUID(), ForeignKey("gamification_badge_categories.id"), nullable=True)

    # Visuels
    icon = Column(String(255), nullable=False)
    icon_locked = Column(String(255), nullable=True)
    color = Column(String(20), nullable=True)
    rarity = Column(SQLEnum(BadgeRarity), default=BadgeRarity.COMMON)

    # Criteres d'obtention
    criteria_type = Column(String(50), nullable=True)  # points_threshold, action_count, etc.
    criteria = Column(JSONB, default=dict)  # {"action": "login", "count": 30}
    progress_max = Column(Integer, default=100)

    # Recompenses
    points_reward = Column(Integer, default=0)
    points_type = Column(SQLEnum(PointType), default=PointType.XP)
    bonus_rewards = Column(JSONB, default=list)  # Autres recompenses

    # Limites
    max_holders = Column(Integer, nullable=True)  # Limite de detenteurs
    current_holders = Column(Integer, default=0)
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)

    # Options
    is_secret = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_stackable = Column(Boolean, default=False)  # Peut etre obtenu plusieurs fois

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, default=1)

    # Relations
    category = relationship("BadgeCategory", back_populates="badges")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_badge_code'),
        Index('idx_gam_badges_tenant', 'tenant_id'),
        Index('idx_gam_badges_category', 'tenant_id', 'category_id'),
        Index('idx_gam_badges_rarity', 'tenant_id', 'rarity'),
    )


class UserBadge(Base):
    """Badge obtenu par un utilisateur."""
    __tablename__ = "gamification_user_badges"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)
    badge_id = Column(UniversalUUID(), ForeignKey("gamification_badges.id"), nullable=False)

    # Statut
    status = Column(SQLEnum(BadgeStatus), default=BadgeStatus.LOCKED)
    progress = Column(Integer, default=0)
    progress_max = Column(Integer, default=100)

    # Dates
    started_at = Column(DateTime, nullable=True)
    unlocked_at = Column(DateTime, nullable=True)
    claimed_at = Column(DateTime, nullable=True)

    # Notifications
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)

    # Pour badges stackables
    times_earned = Column(Integer, default=1)

    # Metadata
    unlock_context = Column(JSONB, default=dict)  # Contexte du deblocage

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    badge = relationship("GamificationBadge")

    __table_args__ = (
        Index('idx_gam_user_badges_tenant', 'tenant_id'),
        Index('idx_gam_user_badges_user', 'tenant_id', 'user_id'),
        Index('idx_gam_user_badges_badge', 'tenant_id', 'badge_id'),
        Index('idx_gam_user_badges_status', 'tenant_id', 'user_id', 'status'),
    )


# =============================================================================
# MODELES DEFIS
# =============================================================================

class GamificationChallenge(Base):
    """Definition d'un defi."""
    __tablename__ = "gamification_challenges"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    challenge_type = Column(SQLEnum(ChallengeType), nullable=False)
    status = Column(SQLEnum(ChallengeStatus), default=ChallengeStatus.DRAFT)

    # Visuels
    icon = Column(String(255), nullable=True)
    banner_url = Column(String(500), nullable=True)
    color = Column(String(20), nullable=True)

    # Periode
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    registration_deadline = Column(DateTime, nullable=True)

    # Criteres
    criteria_type = Column(String(50), nullable=True)
    criteria = Column(JSONB, default=dict)  # {"action": "sales", "target": 1000}
    target_value = Column(Integer, default=1)
    unit = Column(String(50), nullable=True)  # "ventes", "points", "km", etc.

    # Recompenses
    rewards = Column(JSONB, default=list)  # [{"type": "xp", "value": 100}, {"type": "badge", "value": "badge_id"}]

    # Participants
    max_participants = Column(Integer, nullable=True)
    current_participants = Column(Integer, default=0)
    min_participants = Column(Integer, nullable=True)

    # Pour defis d'equipe
    is_team_challenge = Column(Boolean, default=False)
    team_size_min = Column(Integer, nullable=True)
    team_size_max = Column(Integer, nullable=True)

    # Visibilite
    is_public = Column(Boolean, default=True)
    eligible_departments = Column(JSONB, default=list)
    eligible_roles = Column(JSONB, default=list)

    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_challenge_code'),
        Index('idx_gam_challenges_tenant', 'tenant_id'),
        Index('idx_gam_challenges_type', 'tenant_id', 'challenge_type'),
        Index('idx_gam_challenges_status', 'tenant_id', 'status'),
        Index('idx_gam_challenges_dates', 'tenant_id', 'start_date', 'end_date'),
    )


class UserChallenge(Base):
    """Participation d'un utilisateur a un defi."""
    __tablename__ = "gamification_user_challenges"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)
    challenge_id = Column(UniversalUUID(), ForeignKey("gamification_challenges.id"), nullable=False)

    # Statut
    status = Column(SQLEnum(ChallengeStatus), default=ChallengeStatus.ACTIVE)
    progress = Column(Integer, default=0)
    target = Column(Integer, default=1)
    progress_percent = Column(Numeric(5, 2), default=Decimal("0.00"))

    # Pour defis d'equipe
    team_id = Column(UniversalUUID(), ForeignKey("gamification_teams.id"), nullable=True)

    # Dates
    joined_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Recompenses
    rewards_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime, nullable=True)
    rewards_data = Column(JSONB, default=dict)  # Details des recompenses recues

    # Rang final (si classement)
    final_rank = Column(Integer, nullable=True)

    # Historique de progression
    progress_history = Column(JSONB, default=list)  # [{"date": "...", "value": 10, "total": 50}]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    challenge = relationship("GamificationChallenge")
    team = relationship("GamificationTeam")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', 'challenge_id', name='uq_user_challenge'),
        Index('idx_gam_user_challenges_tenant', 'tenant_id'),
        Index('idx_gam_user_challenges_user', 'tenant_id', 'user_id'),
        Index('idx_gam_user_challenges_challenge', 'tenant_id', 'challenge_id'),
        Index('idx_gam_user_challenges_status', 'tenant_id', 'status'),
    )


# =============================================================================
# MODELES RECOMPENSES
# =============================================================================

class GamificationReward(Base):
    """Definition d'une recompense."""
    __tablename__ = "gamification_rewards"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    category = Column(String(100), nullable=True)

    # Visuels
    image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # Cout
    cost_points = Column(Integer, default=0)
    cost_type = Column(SQLEnum(PointType), default=PointType.COINS)

    # Valeur
    value = Column(JSONB, default=dict)  # {"discount_percent": 20} ou {"badge_id": "..."}
    redemption_instructions = Column(Text, nullable=True)

    # Stock
    stock = Column(Integer, nullable=True)  # NULL = illimite
    claimed_count = Column(Integer, default=0)
    reserved_count = Column(Integer, default=0)

    # Limites
    limit_per_user = Column(Integer, nullable=True)
    limit_per_day = Column(Integer, nullable=True)

    # Disponibilite
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)
    min_level_required = Column(Integer, nullable=True)
    eligible_badge_ids = Column(JSONB, default=list)

    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_reward_code'),
        Index('idx_gam_rewards_tenant', 'tenant_id'),
        Index('idx_gam_rewards_type', 'tenant_id', 'reward_type'),
        Index('idx_gam_rewards_active', 'tenant_id', 'is_active'),
    )


class RewardClaim(Base):
    """Reclamation de recompense par un utilisateur."""
    __tablename__ = "gamification_reward_claims"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)
    reward_id = Column(UniversalUUID(), ForeignKey("gamification_rewards.id"), nullable=False)

    # Transaction
    transaction_id = Column(UniversalUUID(), ForeignKey("gamification_point_transactions.id"), nullable=True)
    points_spent = Column(Integer, default=0)

    # Statut
    status = Column(SQLEnum(RewardStatus), default=RewardStatus.PENDING)
    claim_code = Column(String(50), nullable=True)

    # Livraison (si physique)
    shipping_address = Column(JSONB, default=dict)
    tracking_number = Column(String(100), nullable=True)

    # Notes
    user_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)

    # Dates
    claimed_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    fulfilled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    processed_by = Column(UniversalUUID(), nullable=True)
    cancelled_by = Column(UniversalUUID(), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    reward = relationship("GamificationReward")

    __table_args__ = (
        Index('idx_gam_claims_tenant', 'tenant_id'),
        Index('idx_gam_claims_user', 'tenant_id', 'user_id'),
        Index('idx_gam_claims_reward', 'tenant_id', 'reward_id'),
        Index('idx_gam_claims_status', 'tenant_id', 'status'),
        Index('idx_gam_claims_code', 'claim_code'),
    )


# =============================================================================
# MODELES REGLES D'ATTRIBUTION
# =============================================================================

class GamificationRule(Base):
    """Regle d'attribution automatique de points/badges."""
    __tablename__ = "gamification_rules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Declencheur
    event_type = Column(SQLEnum(RuleEventType), nullable=False)
    event_source = Column(String(100), nullable=True)  # Module source (sales, support, etc.)
    event_action = Column(String(100), nullable=True)  # Action specifique

    # Conditions
    conditions = Column(JSONB, default=dict)  # {"field": "amount", "operator": ">=", "value": 1000}
    condition_logic = Column(String(10), default="AND")  # AND, OR

    # Actions
    actions = Column(JSONB, default=list)
    # [{"type": "award_points", "point_type": "xp", "amount": 10}, {"type": "unlock_badge", "badge_id": "..."}]

    # Limites
    max_triggers_per_user = Column(Integer, nullable=True)
    max_triggers_per_day = Column(Integer, nullable=True)
    cooldown_minutes = Column(Integer, nullable=True)  # Delai entre deux declenchements

    # Multiplicateurs
    level_multiplier = Column(Boolean, default=False)  # Appliquer multiplicateur du niveau

    # Periode de validite
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    # Priorite (pour regles conflictuelles)
    priority = Column(Integer, default=0)

    # Statistiques
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_rule_code'),
        Index('idx_gam_rules_tenant', 'tenant_id'),
        Index('idx_gam_rules_event', 'tenant_id', 'event_type', 'event_source'),
        Index('idx_gam_rules_active', 'tenant_id', 'is_active'),
    )


class RuleTriggerLog(Base):
    """Log des declenchements de regles."""
    __tablename__ = "gamification_rule_trigger_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    rule_id = Column(UniversalUUID(), ForeignKey("gamification_rules.id"), nullable=False)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    # Evenement
    event_data = Column(JSONB, default=dict)

    # Resultat
    success = Column(Boolean, default=True)
    actions_executed = Column(JSONB, default=list)
    error_message = Column(Text, nullable=True)

    # Resultats
    points_awarded = Column(Integer, default=0)
    badges_unlocked = Column(JSONB, default=list)

    triggered_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_gam_trigger_logs_tenant', 'tenant_id'),
        Index('idx_gam_trigger_logs_rule', 'tenant_id', 'rule_id'),
        Index('idx_gam_trigger_logs_user', 'tenant_id', 'user_id'),
        Index('idx_gam_trigger_logs_date', 'tenant_id', 'triggered_at'),
    )


# =============================================================================
# MODELES EQUIPES & COMPETITIONS
# =============================================================================

class GamificationTeam(Base):
    """Equipe de gamification."""
    __tablename__ = "gamification_teams"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Visuels
    logo_url = Column(String(500), nullable=True)
    color = Column(String(20), nullable=True)
    banner_url = Column(String(500), nullable=True)

    # Capitaine/Admin
    captain_id = Column(UniversalUUID(), nullable=True)

    # Limites
    max_members = Column(Integer, nullable=True)
    current_members = Column(Integer, default=0)

    # Stats
    total_points = Column(Integer, default=0)
    total_badges = Column(Integer, default=0)
    challenges_completed = Column(Integer, default=0)
    competitions_won = Column(Integer, default=0)

    # Visibilite
    is_public = Column(Boolean, default=True)
    allow_join_requests = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, default=1)

    # Relations
    members = relationship("UserGamificationProfile", back_populates="team")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_team_code'),
        Index('idx_gam_teams_tenant', 'tenant_id'),
        Index('idx_gam_teams_captain', 'tenant_id', 'captain_id'),
    )


class TeamMembership(Base):
    """Appartenance a une equipe avec historique."""
    __tablename__ = "gamification_team_memberships"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)
    team_id = Column(UniversalUUID(), ForeignKey("gamification_teams.id"), nullable=False)

    role = Column(String(50), default="member")  # member, admin, captain
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Contribution
    points_contributed = Column(Integer, default=0)
    badges_contributed = Column(Integer, default=0)

    invited_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_gam_memberships_tenant', 'tenant_id'),
        Index('idx_gam_memberships_user', 'tenant_id', 'user_id'),
        Index('idx_gam_memberships_team', 'tenant_id', 'team_id'),
    )


class GamificationCompetition(Base):
    """Competition entre equipes ou individus."""
    __tablename__ = "gamification_competitions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(CompetitionStatus), default=CompetitionStatus.DRAFT)

    # Type
    is_team_competition = Column(Boolean, default=False)
    scoring_type = Column(String(50), default="points")  # points, challenges, badges

    # Visuels
    banner_url = Column(String(500), nullable=True)
    icon = Column(String(255), nullable=True)

    # Periode
    registration_start = Column(DateTime, nullable=True)
    registration_end = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Participants
    max_participants = Column(Integer, nullable=True)
    current_participants = Column(Integer, default=0)
    min_participants = Column(Integer, nullable=True)

    # Criteres de scoring
    scoring_criteria = Column(JSONB, default=dict)

    # Prix
    prizes = Column(JSONB, default=list)
    # [{"rank": 1, "reward_id": "...", "title": "Champion"}, ...]

    # Resultats
    results = Column(JSONB, default=dict)
    winner_id = Column(UniversalUUID(), nullable=True)
    final_rankings = Column(JSONB, default=list)

    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Version
    version = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_competition_code'),
        Index('idx_gam_competitions_tenant', 'tenant_id'),
        Index('idx_gam_competitions_status', 'tenant_id', 'status'),
        Index('idx_gam_competitions_dates', 'tenant_id', 'start_date', 'end_date'),
    )


class CompetitionParticipant(Base):
    """Participant a une competition."""
    __tablename__ = "gamification_competition_participants"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    competition_id = Column(UniversalUUID(), ForeignKey("gamification_competitions.id"), nullable=False)

    # Participant (user ou team)
    user_id = Column(UniversalUUID(), nullable=True)
    team_id = Column(UniversalUUID(), ForeignKey("gamification_teams.id"), nullable=True)

    # Score
    current_score = Column(Integer, default=0)
    current_rank = Column(Integer, nullable=True)
    previous_rank = Column(Integer, nullable=True)

    # Historique
    score_history = Column(JSONB, default=list)

    # Dates
    registered_at = Column(DateTime, default=datetime.utcnow)
    withdrawn_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Prix remporte
    prize_awarded = Column(JSONB, default=dict)
    prize_claimed = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_gam_comp_participants_tenant', 'tenant_id'),
        Index('idx_gam_comp_participants_comp', 'tenant_id', 'competition_id'),
        Index('idx_gam_comp_participants_user', 'tenant_id', 'user_id'),
        Index('idx_gam_comp_participants_team', 'tenant_id', 'team_id'),
        Index('idx_gam_comp_participants_rank', 'tenant_id', 'competition_id', 'current_rank'),
    )


# =============================================================================
# MODELES LEADERBOARDS
# =============================================================================

class Leaderboard(Base):
    """Definition d'un classement."""
    __tablename__ = "gamification_leaderboards"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type
    period = Column(SQLEnum(LeaderboardPeriod), default=LeaderboardPeriod.ALL_TIME)
    scope = Column(SQLEnum(LeaderboardScope), default=LeaderboardScope.GLOBAL)
    scope_value = Column(String(100), nullable=True)  # ID departement, region, etc.

    # Scoring
    point_type = Column(SQLEnum(PointType), default=PointType.XP)
    scoring_formula = Column(String(500), nullable=True)  # Formule custom

    # Options
    show_top_n = Column(Integer, default=100)
    min_score_to_display = Column(Integer, default=0)
    include_inactive_users = Column(Boolean, default=False)

    # Periode custom
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Cache
    last_computed_at = Column(DateTime, nullable=True)
    cached_rankings = Column(JSONB, default=list)

    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_leaderboard_code'),
        Index('idx_gam_leaderboards_tenant', 'tenant_id'),
        Index('idx_gam_leaderboards_period', 'tenant_id', 'period'),
    )


class LeaderboardEntry(Base):
    """Entree dans un classement (cache)."""
    __tablename__ = "gamification_leaderboard_entries"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    leaderboard_id = Column(UniversalUUID(), ForeignKey("gamification_leaderboards.id"), nullable=False)

    # Participant
    user_id = Column(UniversalUUID(), nullable=True)
    team_id = Column(UniversalUUID(), nullable=True)

    # Position
    rank = Column(Integer, nullable=False)
    previous_rank = Column(Integer, nullable=True)
    rank_change = Column(Integer, default=0)

    # Score
    score = Column(Integer, default=0)
    score_breakdown = Column(JSONB, default=dict)

    # Infos affichees (cache)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    level = Column(Integer, nullable=True)
    badge_count = Column(Integer, nullable=True)

    # Periode
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    computed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_gam_lb_entries_tenant', 'tenant_id'),
        Index('idx_gam_lb_entries_lb', 'tenant_id', 'leaderboard_id'),
        Index('idx_gam_lb_entries_rank', 'tenant_id', 'leaderboard_id', 'rank'),
        Index('idx_gam_lb_entries_user', 'tenant_id', 'user_id'),
    )


# =============================================================================
# MODELES NOTIFICATIONS & HISTORIQUE
# =============================================================================

class GamificationNotification(Base):
    """Notification de gamification."""
    __tablename__ = "gamification_notifications"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)

    # Reference
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(UniversalUUID(), nullable=True)

    # Donnees additionnelles
    data = Column(JSONB, default=dict)

    # Statut
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_dismissed = Column(Boolean, default=False)

    # Actions
    action_url = Column(String(500), nullable=True)
    action_label = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_gam_notifications_tenant', 'tenant_id'),
        Index('idx_gam_notifications_user', 'tenant_id', 'user_id'),
        Index('idx_gam_notifications_unread', 'tenant_id', 'user_id', 'is_read'),
        Index('idx_gam_notifications_type', 'tenant_id', 'notification_type'),
    )


class GamificationActivity(Base):
    """Historique d'activite gamification (audit)."""
    __tablename__ = "gamification_activities"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    activity_type = Column(String(100), nullable=False)  # points_earned, badge_unlocked, etc.
    activity_subtype = Column(String(100), nullable=True)

    # Details
    description = Column(Text, nullable=True)
    details = Column(JSONB, default=dict)

    # Valeurs
    points_delta = Column(Integer, default=0)
    xp_delta = Column(Integer, default=0)

    # Contexte
    source_module = Column(String(100), nullable=True)
    source_action = Column(String(100), nullable=True)
    source_id = Column(UniversalUUID(), nullable=True)

    # Visibilite
    is_public = Column(Boolean, default=True)  # Visible sur le profil public

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_gam_activities_tenant', 'tenant_id'),
        Index('idx_gam_activities_user', 'tenant_id', 'user_id'),
        Index('idx_gam_activities_type', 'tenant_id', 'activity_type'),
        Index('idx_gam_activities_date', 'tenant_id', 'created_at'),
    )


# =============================================================================
# MODELES STREAKS
# =============================================================================

class GamificationStreak(Base):
    """Serie (streak) d'un utilisateur."""
    __tablename__ = "gamification_streaks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    streak_type = Column(String(50), nullable=False)  # login, activity, purchase, etc.

    current_count = Column(Integer, default=0)
    longest_count = Column(Integer, default=0)
    total_streaks = Column(Integer, default=1)

    # Dates
    last_activity_date = Column(Date, nullable=True)
    streak_started_at = Column(DateTime, nullable=True)
    streak_broken_at = Column(DateTime, nullable=True)

    # Bonus
    current_multiplier = Column(Numeric(4, 2), default=Decimal("1.0"))

    # Historique des meilleures series
    best_streaks = Column(JSONB, default=list)
    # [{"count": 30, "started": "...", "ended": "..."}]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', 'streak_type', name='uq_user_streak_type'),
        Index('idx_gam_streaks_tenant', 'tenant_id'),
        Index('idx_gam_streaks_user', 'tenant_id', 'user_id'),
        Index('idx_gam_streaks_type', 'tenant_id', 'streak_type'),
    )


# =============================================================================
# MODELES CONFIGURATION
# =============================================================================

class GamificationConfig(Base):
    """Configuration de gamification par tenant."""
    __tablename__ = "gamification_config"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, unique=True, index=True)

    # Activation des fonctionnalites
    points_enabled = Column(Boolean, default=True)
    badges_enabled = Column(Boolean, default=True)
    challenges_enabled = Column(Boolean, default=True)
    leaderboards_enabled = Column(Boolean, default=True)
    rewards_enabled = Column(Boolean, default=True)
    teams_enabled = Column(Boolean, default=True)
    competitions_enabled = Column(Boolean, default=True)

    # Points
    default_xp_multiplier = Column(Numeric(4, 2), default=Decimal("1.0"))
    xp_to_coins_ratio = Column(Numeric(6, 2), default=Decimal("10.0"))  # 10 XP = 1 coin

    # Streaks
    login_streak_bonus = Column(Integer, default=10)  # Points bonus par jour de streak
    max_streak_multiplier = Column(Numeric(4, 2), default=Decimal("2.0"))

    # Notifications
    notify_points_threshold = Column(Integer, default=100)  # Notifier a partir de X points
    notify_level_up = Column(Boolean, default=True)
    notify_badge_unlock = Column(Boolean, default=True)
    notify_challenge_complete = Column(Boolean, default=True)
    notify_leaderboard_change = Column(Boolean, default=True)

    # Affichage
    show_exact_points = Column(Boolean, default=True)
    show_user_level = Column(Boolean, default=True)
    show_global_leaderboard = Column(Boolean, default=True)

    # Anti-abus
    max_points_per_day = Column(Integer, nullable=True)
    max_actions_per_hour = Column(Integer, nullable=True)

    # Branding
    primary_color = Column(String(20), default="#6366f1")
    badge_style = Column(String(50), default="default")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_gam_config_tenant', 'tenant_id'),
    )
