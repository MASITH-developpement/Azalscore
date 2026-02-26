"""
AZALS MODULE GAMIFICATION - Schemas Pydantic
=============================================

Schemas de validation pour le module de gamification.
"""
from __future__ import annotations


from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    BadgeRarity,
    BadgeStatus,
    ChallengeStatus,
    ChallengeType,
    CompetitionStatus,
    LeaderboardPeriod,
    LeaderboardScope,
    NotificationType,
    PointType,
    RewardStatus,
    RewardType,
    RuleEventType,
    TransactionType,
)


# =============================================================================
# SCHEMAS DE BASE
# =============================================================================

class PaginatedResponse(BaseModel):
    """Schema de reponse paginee."""
    items: list
    total: int
    page: int
    page_size: int
    pages: int


class AutocompleteItem(BaseModel):
    """Item d'autocompletion."""
    id: str
    code: str
    name: str
    label: str


class AutocompleteResponse(BaseModel):
    """Reponse d'autocompletion."""
    items: list[AutocompleteItem]


# =============================================================================
# SCHEMAS NIVEAUX
# =============================================================================

class LevelBase(BaseModel):
    """Schema de base pour les niveaux."""
    level_number: int = Field(..., ge=1)
    name: str = Field(..., max_length=100)
    description: str | None = None
    min_xp: int = Field(..., ge=0)
    max_xp: int | None = None
    icon: str | None = None
    color: str | None = Field(None, max_length=20)
    perks: list[str] = Field(default_factory=list)
    multiplier: Decimal = Field(default=Decimal("1.0"), ge=Decimal("0.1"), le=Decimal("10.0"))


class LevelCreate(LevelBase):
    """Schema de creation de niveau."""
    badge_id: UUID | None = None


class LevelUpdate(BaseModel):
    """Schema de mise a jour de niveau."""
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    min_xp: int | None = Field(None, ge=0)
    max_xp: int | None = None
    icon: str | None = None
    color: str | None = Field(None, max_length=20)
    perks: list[str] | None = None
    multiplier: Decimal | None = Field(None, ge=Decimal("0.1"), le=Decimal("10.0"))
    badge_id: UUID | None = None
    is_active: bool | None = None


class LevelResponse(LevelBase):
    """Schema de reponse pour les niveaux."""
    id: UUID
    tenant_id: str
    badge_id: UUID | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS PROFIL UTILISATEUR
# =============================================================================

class UserProfileBase(BaseModel):
    """Schema de base pour le profil utilisateur."""
    avatar_url: str | None = None
    title: str | None = Field(None, max_length=100)
    notifications_enabled: bool = True
    public_profile: bool = True
    show_on_leaderboard: bool = True


class UserProfileCreate(UserProfileBase):
    """Schema de creation de profil."""
    user_id: UUID


class UserProfileUpdate(BaseModel):
    """Schema de mise a jour de profil."""
    avatar_url: str | None = None
    title: str | None = Field(None, max_length=100)
    selected_badge_id: UUID | None = None
    notifications_enabled: bool | None = None
    public_profile: bool | None = None
    show_on_leaderboard: bool | None = None


class UserProfileResponse(UserProfileBase):
    """Schema de reponse pour le profil."""
    id: UUID
    tenant_id: str
    user_id: UUID
    current_level: int
    current_xp: int
    lifetime_xp: int
    coins_balance: int
    karma_balance: int
    credits_balance: int
    current_login_streak: int
    longest_login_streak: int
    current_activity_streak: int
    badges_unlocked: int
    challenges_completed: int
    rewards_claimed: int
    team_id: UUID | None = None
    selected_badge_id: UUID | None = None
    level_up_date: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileSummary(BaseModel):
    """Resume du profil utilisateur."""
    user_id: UUID
    display_name: str | None = None
    avatar_url: str | None = None
    level: int
    xp: int
    xp_to_next_level: int
    level_progress_percent: Decimal
    badges_count: int
    rank: int | None = None
    title: str | None = None


# =============================================================================
# SCHEMAS POINTS
# =============================================================================

class PointBalanceResponse(BaseModel):
    """Schema de reponse pour les balances de points."""
    point_type: PointType
    balance: int
    lifetime_earned: int
    lifetime_spent: int


class AwardPointsRequest(BaseModel):
    """Schema pour attribuer des points."""
    user_id: UUID
    amount: int = Field(..., gt=0)
    point_type: PointType = PointType.XP
    description: str | None = Field(None, max_length=500)
    source: str | None = Field(None, max_length=100)
    source_id: UUID | None = None
    expires_at: datetime | None = None


class SpendPointsRequest(BaseModel):
    """Schema pour depenser des points."""
    user_id: UUID
    amount: int = Field(..., gt=0)
    point_type: PointType = PointType.COINS
    description: str | None = Field(None, max_length=500)
    reference_type: str | None = Field(None, max_length=50)
    reference_id: UUID | None = None


class TransferPointsRequest(BaseModel):
    """Schema pour transferer des points."""
    from_user_id: UUID
    to_user_id: UUID
    amount: int = Field(..., gt=0)
    point_type: PointType = PointType.COINS
    message: str | None = Field(None, max_length=500)


class PointTransactionResponse(BaseModel):
    """Schema de reponse pour les transactions."""
    id: UUID
    user_id: UUID
    point_type: PointType
    transaction_type: TransactionType
    amount: int
    balance_after: int
    description: str | None = None
    source: str | None = None
    source_id: UUID | None = None
    multiplier: Decimal
    expires_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PointTransactionFilters(BaseModel):
    """Filtres pour les transactions."""
    point_type: PointType | None = None
    transaction_type: TransactionType | None = None
    source: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


# =============================================================================
# SCHEMAS BADGES
# =============================================================================

class BadgeCategoryBase(BaseModel):
    """Schema de base pour les categories de badges."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str | None = None
    icon: str | None = None
    color: str | None = Field(None, max_length=20)
    sort_order: int = 0


class BadgeCategoryCreate(BadgeCategoryBase):
    """Schema de creation de categorie."""
    pass


class BadgeCategoryResponse(BadgeCategoryBase):
    """Schema de reponse pour les categories."""
    id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BadgeBase(BaseModel):
    """Schema de base pour les badges."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str | None = None
    icon: str = Field(..., max_length=255)
    icon_locked: str | None = None
    color: str | None = Field(None, max_length=20)
    rarity: BadgeRarity = BadgeRarity.COMMON
    criteria_type: str | None = Field(None, max_length=50)
    criteria: dict[str, Any] = Field(default_factory=dict)
    progress_max: int = 100
    points_reward: int = 0
    points_type: PointType = PointType.XP
    is_secret: bool = False
    is_featured: bool = False
    is_stackable: bool = False


class BadgeCreate(BadgeBase):
    """Schema de creation de badge."""
    category_id: UUID | None = None
    max_holders: int | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    bonus_rewards: list[dict] = Field(default_factory=list)


class BadgeUpdate(BaseModel):
    """Schema de mise a jour de badge."""
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    icon: str | None = Field(None, max_length=255)
    icon_locked: str | None = None
    color: str | None = Field(None, max_length=20)
    rarity: BadgeRarity | None = None
    criteria_type: str | None = Field(None, max_length=50)
    criteria: dict[str, Any] | None = None
    progress_max: int | None = None
    points_reward: int | None = None
    category_id: UUID | None = None
    max_holders: int | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    is_secret: bool | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class BadgeResponse(BadgeBase):
    """Schema de reponse pour les badges."""
    id: UUID
    tenant_id: str
    category_id: UUID | None = None
    max_holders: int | None = None
    current_holders: int
    available_from: datetime | None = None
    available_until: datetime | None = None
    is_active: bool
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class UserBadgeResponse(BaseModel):
    """Schema de reponse pour les badges utilisateur."""
    id: UUID
    user_id: UUID
    badge_id: UUID
    badge: BadgeResponse | None = None
    status: BadgeStatus
    progress: int
    progress_max: int
    progress_percent: Decimal = Decimal("0")
    started_at: datetime | None = None
    unlocked_at: datetime | None = None
    claimed_at: datetime | None = None
    times_earned: int = 1
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BadgeFilters(BaseModel):
    """Filtres pour les badges."""
    search: str | None = None
    category_id: UUID | None = None
    rarity: BadgeRarity | None = None
    include_secret: bool = False
    only_available: bool = True


# =============================================================================
# SCHEMAS DEFIS
# =============================================================================

class ChallengeBase(BaseModel):
    """Schema de base pour les defis."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    challenge_type: ChallengeType
    icon: str | None = None
    banner_url: str | None = None
    color: str | None = Field(None, max_length=20)
    criteria_type: str | None = Field(None, max_length=50)
    criteria: dict[str, Any] = Field(default_factory=dict)
    target_value: int = 1
    unit: str | None = Field(None, max_length=50)
    rewards: list[dict] = Field(default_factory=list)
    is_team_challenge: bool = False


class ChallengeCreate(ChallengeBase):
    """Schema de creation de defi."""
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_deadline: datetime | None = None
    max_participants: int | None = None
    min_participants: int | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    is_public: bool = True
    eligible_departments: list[str] = Field(default_factory=list)
    eligible_roles: list[str] = Field(default_factory=list)
    is_featured: bool = False


class ChallengeUpdate(BaseModel):
    """Schema de mise a jour de defi."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    status: ChallengeStatus | None = None
    icon: str | None = None
    banner_url: str | None = None
    criteria: dict[str, Any] | None = None
    target_value: int | None = None
    rewards: list[dict] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_participants: int | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class ChallengeResponse(ChallengeBase):
    """Schema de reponse pour les defis."""
    id: UUID
    tenant_id: str
    status: ChallengeStatus
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_deadline: datetime | None = None
    max_participants: int | None = None
    current_participants: int
    min_participants: int | None = None
    team_size_min: int | None = None
    team_size_max: int | None = None
    is_public: bool
    is_featured: bool
    is_active: bool
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class UserChallengeResponse(BaseModel):
    """Schema de reponse pour les defis utilisateur."""
    id: UUID
    user_id: UUID
    challenge_id: UUID
    challenge: ChallengeResponse | None = None
    status: ChallengeStatus
    progress: int
    target: int
    progress_percent: Decimal
    team_id: UUID | None = None
    joined_at: datetime
    completed_at: datetime | None = None
    rewards_claimed: bool
    final_rank: int | None = None

    model_config = ConfigDict(from_attributes=True)


class JoinChallengeRequest(BaseModel):
    """Schema pour rejoindre un defi."""
    challenge_id: UUID
    team_id: UUID | None = None


class UpdateProgressRequest(BaseModel):
    """Schema pour mettre a jour la progression."""
    progress: int = Field(..., ge=0)
    context: dict[str, Any] = Field(default_factory=dict)


class ChallengeFilters(BaseModel):
    """Filtres pour les defis."""
    search: str | None = None
    challenge_type: ChallengeType | None = None
    status: list[ChallengeStatus] | None = None
    is_team: bool | None = None
    only_available: bool = True


# =============================================================================
# SCHEMAS RECOMPENSES
# =============================================================================

class RewardBase(BaseModel):
    """Schema de base pour les recompenses."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    reward_type: RewardType
    category: str | None = Field(None, max_length=100)
    image_url: str | None = None
    thumbnail_url: str | None = None
    cost_points: int = 0
    cost_type: PointType = PointType.COINS
    value: dict[str, Any] = Field(default_factory=dict)
    redemption_instructions: str | None = None


class RewardCreate(RewardBase):
    """Schema de creation de recompense."""
    stock: int | None = None
    limit_per_user: int | None = None
    limit_per_day: int | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    min_level_required: int | None = None
    eligible_badge_ids: list[UUID] = Field(default_factory=list)
    is_featured: bool = False


class RewardUpdate(BaseModel):
    """Schema de mise a jour de recompense."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    image_url: str | None = None
    cost_points: int | None = None
    value: dict[str, Any] | None = None
    redemption_instructions: str | None = None
    stock: int | None = None
    limit_per_user: int | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    min_level_required: int | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class RewardResponse(RewardBase):
    """Schema de reponse pour les recompenses."""
    id: UUID
    tenant_id: str
    stock: int | None = None
    claimed_count: int
    available_stock: int | None = None
    limit_per_user: int | None = None
    limit_per_day: int | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    min_level_required: int | None = None
    is_featured: bool
    is_active: bool
    is_available: bool = True
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class ClaimRewardRequest(BaseModel):
    """Schema pour reclamer une recompense."""
    reward_id: UUID
    shipping_address: dict[str, Any] | None = None
    user_notes: str | None = Field(None, max_length=500)


class RewardClaimResponse(BaseModel):
    """Schema de reponse pour les reclamations."""
    id: UUID
    user_id: UUID
    reward_id: UUID
    reward: RewardResponse | None = None
    status: RewardStatus
    claim_code: str | None = None
    points_spent: int
    shipping_address: dict[str, Any] | None = None
    tracking_number: str | None = None
    claimed_at: datetime
    fulfilled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UpdateClaimStatusRequest(BaseModel):
    """Schema pour mettre a jour le statut d'une reclamation."""
    status: RewardStatus
    tracking_number: str | None = None
    admin_notes: str | None = None


class RewardFilters(BaseModel):
    """Filtres pour les recompenses."""
    search: str | None = None
    reward_type: RewardType | None = None
    category: str | None = None
    min_cost: int | None = None
    max_cost: int | None = None
    affordable: bool = False
    only_available: bool = True


# =============================================================================
# SCHEMAS REGLES
# =============================================================================

class RuleBase(BaseModel):
    """Schema de base pour les regles."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    event_type: RuleEventType
    event_source: str | None = Field(None, max_length=100)
    event_action: str | None = Field(None, max_length=100)
    conditions: dict[str, Any] = Field(default_factory=dict)
    condition_logic: str = Field(default="AND", pattern="^(AND|OR)$")
    actions: list[dict[str, Any]] = Field(default_factory=list)


class RuleCreate(RuleBase):
    """Schema de creation de regle."""
    max_triggers_per_user: int | None = None
    max_triggers_per_day: int | None = None
    cooldown_minutes: int | None = None
    level_multiplier: bool = False
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    priority: int = 0


class RuleUpdate(BaseModel):
    """Schema de mise a jour de regle."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    conditions: dict[str, Any] | None = None
    condition_logic: str | None = Field(None, pattern="^(AND|OR)$")
    actions: list[dict[str, Any]] | None = None
    max_triggers_per_user: int | None = None
    max_triggers_per_day: int | None = None
    cooldown_minutes: int | None = None
    level_multiplier: bool | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    priority: int | None = None
    is_active: bool | None = None


class RuleResponse(RuleBase):
    """Schema de reponse pour les regles."""
    id: UUID
    tenant_id: str
    max_triggers_per_user: int | None = None
    max_triggers_per_day: int | None = None
    cooldown_minutes: int | None = None
    level_multiplier: bool
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    priority: int
    trigger_count: int
    last_triggered_at: datetime | None = None
    is_active: bool
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class TriggerRuleRequest(BaseModel):
    """Schema pour declencher une regle manuellement."""
    user_id: UUID
    event_data: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# SCHEMAS EQUIPES
# =============================================================================

class TeamBase(BaseModel):
    """Schema de base pour les equipes."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    logo_url: str | None = None
    color: str | None = Field(None, max_length=20)
    banner_url: str | None = None


class TeamCreate(TeamBase):
    """Schema de creation d'equipe."""
    max_members: int | None = None
    is_public: bool = True
    allow_join_requests: bool = True


class TeamUpdate(BaseModel):
    """Schema de mise a jour d'equipe."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    logo_url: str | None = None
    color: str | None = Field(None, max_length=20)
    banner_url: str | None = None
    captain_id: UUID | None = None
    max_members: int | None = None
    is_public: bool | None = None
    allow_join_requests: bool | None = None
    is_active: bool | None = None


class TeamResponse(TeamBase):
    """Schema de reponse pour les equipes."""
    id: UUID
    tenant_id: str
    captain_id: UUID | None = None
    max_members: int | None = None
    current_members: int
    total_points: int
    total_badges: int
    challenges_completed: int
    competitions_won: int
    is_public: bool
    allow_join_requests: bool
    is_active: bool
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
    """Schema de reponse pour les membres d'equipe."""
    id: UUID
    user_id: UUID
    team_id: UUID
    role: str
    joined_at: datetime
    points_contributed: int
    badges_contributed: int
    is_active: bool
    user_profile: UserProfileSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class JoinTeamRequest(BaseModel):
    """Schema pour rejoindre une equipe."""
    team_id: UUID
    message: str | None = Field(None, max_length=500)


class InviteToTeamRequest(BaseModel):
    """Schema pour inviter a une equipe."""
    user_id: UUID
    message: str | None = Field(None, max_length=500)


# =============================================================================
# SCHEMAS COMPETITIONS
# =============================================================================

class CompetitionBase(BaseModel):
    """Schema de base pour les competitions."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    is_team_competition: bool = False
    scoring_type: str = Field(default="points", max_length=50)
    banner_url: str | None = None
    icon: str | None = None


class CompetitionCreate(CompetitionBase):
    """Schema de creation de competition."""
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_participants: int | None = None
    min_participants: int | None = None
    scoring_criteria: dict[str, Any] = Field(default_factory=dict)
    prizes: list[dict] = Field(default_factory=list)
    is_featured: bool = False


class CompetitionUpdate(BaseModel):
    """Schema de mise a jour de competition."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    status: CompetitionStatus | None = None
    banner_url: str | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_participants: int | None = None
    scoring_criteria: dict[str, Any] | None = None
    prizes: list[dict] | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class CompetitionResponse(CompetitionBase):
    """Schema de reponse pour les competitions."""
    id: UUID
    tenant_id: str
    status: CompetitionStatus
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    max_participants: int | None = None
    current_participants: int
    min_participants: int | None = None
    scoring_criteria: dict[str, Any]
    prizes: list[dict]
    winner_id: UUID | None = None
    is_featured: bool
    is_active: bool
    created_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)


class CompetitionParticipantResponse(BaseModel):
    """Schema de reponse pour les participants."""
    id: UUID
    competition_id: UUID
    user_id: UUID | None = None
    team_id: UUID | None = None
    current_score: int
    current_rank: int | None = None
    previous_rank: int | None = None
    rank_change: int = 0
    registered_at: datetime
    is_active: bool
    user_profile: UserProfileSummary | None = None
    team: TeamResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS LEADERBOARDS
# =============================================================================

class LeaderboardBase(BaseModel):
    """Schema de base pour les classements."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: str | None = None
    period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME
    scope: LeaderboardScope = LeaderboardScope.GLOBAL
    scope_value: str | None = Field(None, max_length=100)
    point_type: PointType = PointType.XP


class LeaderboardCreate(LeaderboardBase):
    """Schema de creation de classement."""
    scoring_formula: str | None = None
    show_top_n: int = 100
    min_score_to_display: int = 0
    include_inactive_users: bool = False
    period_start: datetime | None = None
    period_end: datetime | None = None
    is_public: bool = True
    is_featured: bool = False


class LeaderboardUpdate(BaseModel):
    """Schema de mise a jour de classement."""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    show_top_n: int | None = None
    min_score_to_display: int | None = None
    is_public: bool | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class LeaderboardResponse(LeaderboardBase):
    """Schema de reponse pour les classements."""
    id: UUID
    tenant_id: str
    scoring_formula: str | None = None
    show_top_n: int
    min_score_to_display: int
    include_inactive_users: bool
    period_start: datetime | None = None
    period_end: datetime | None = None
    last_computed_at: datetime | None = None
    is_public: bool
    is_featured: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntryResponse(BaseModel):
    """Schema de reponse pour les entrees de classement."""
    rank: int
    previous_rank: int | None = None
    rank_change: int = 0
    user_id: UUID | None = None
    team_id: UUID | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    level: int | None = None
    badge_count: int | None = None
    score: int
    score_breakdown: dict[str, Any] = Field(default_factory=dict)


class LeaderboardWithEntries(LeaderboardResponse):
    """Classement avec ses entrees."""
    entries: list[LeaderboardEntryResponse] = Field(default_factory=list)
    user_entry: LeaderboardEntryResponse | None = None


# =============================================================================
# SCHEMAS NOTIFICATIONS
# =============================================================================

class NotificationResponse(BaseModel):
    """Schema de reponse pour les notifications."""
    id: UUID
    notification_type: NotificationType
    title: str
    message: str | None = None
    icon: str | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    action_url: str | None = None
    action_label: str | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarkNotificationsReadRequest(BaseModel):
    """Schema pour marquer des notifications comme lues."""
    notification_ids: list[UUID] | None = None
    mark_all: bool = False


# =============================================================================
# SCHEMAS STREAKS
# =============================================================================

class StreakResponse(BaseModel):
    """Schema de reponse pour les streaks."""
    id: UUID
    user_id: UUID
    streak_type: str
    current_count: int
    longest_count: int
    total_streaks: int
    last_activity_date: date | None = None
    streak_started_at: datetime | None = None
    streak_broken_at: datetime | None = None
    current_multiplier: Decimal
    best_streaks: list[dict] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS ACTIVITE
# =============================================================================

class ActivityResponse(BaseModel):
    """Schema de reponse pour l'activite."""
    id: UUID
    user_id: UUID
    activity_type: str
    activity_subtype: str | None = None
    description: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    points_delta: int
    xp_delta: int
    source_module: str | None = None
    source_action: str | None = None
    is_public: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityFilters(BaseModel):
    """Filtres pour l'activite."""
    activity_type: str | None = None
    source_module: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    public_only: bool = False


# =============================================================================
# SCHEMAS CONFIGURATION
# =============================================================================

class GamificationConfigUpdate(BaseModel):
    """Schema de mise a jour de la configuration."""
    points_enabled: bool | None = None
    badges_enabled: bool | None = None
    challenges_enabled: bool | None = None
    leaderboards_enabled: bool | None = None
    rewards_enabled: bool | None = None
    teams_enabled: bool | None = None
    competitions_enabled: bool | None = None
    default_xp_multiplier: Decimal | None = None
    xp_to_coins_ratio: Decimal | None = None
    login_streak_bonus: int | None = None
    max_streak_multiplier: Decimal | None = None
    notify_points_threshold: int | None = None
    notify_level_up: bool | None = None
    notify_badge_unlock: bool | None = None
    notify_challenge_complete: bool | None = None
    notify_leaderboard_change: bool | None = None
    show_exact_points: bool | None = None
    show_user_level: bool | None = None
    show_global_leaderboard: bool | None = None
    max_points_per_day: int | None = None
    max_actions_per_hour: int | None = None
    primary_color: str | None = Field(None, max_length=20)
    badge_style: str | None = Field(None, max_length=50)


class GamificationConfigResponse(BaseModel):
    """Schema de reponse pour la configuration."""
    id: UUID
    tenant_id: str
    points_enabled: bool
    badges_enabled: bool
    challenges_enabled: bool
    leaderboards_enabled: bool
    rewards_enabled: bool
    teams_enabled: bool
    competitions_enabled: bool
    default_xp_multiplier: Decimal
    xp_to_coins_ratio: Decimal
    login_streak_bonus: int
    max_streak_multiplier: Decimal
    notify_points_threshold: int
    notify_level_up: bool
    notify_badge_unlock: bool
    notify_challenge_complete: bool
    notify_leaderboard_change: bool
    show_exact_points: bool
    show_user_level: bool
    show_global_leaderboard: bool
    max_points_per_day: int | None = None
    max_actions_per_hour: int | None = None
    primary_color: str
    badge_style: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SCHEMAS DASHBOARD & STATS
# =============================================================================

class GamificationDashboard(BaseModel):
    """Tableau de bord gamification."""
    user_profile: UserProfileSummary
    recent_points: list[PointTransactionResponse]
    recent_badges: list[UserBadgeResponse]
    active_challenges: list[UserChallengeResponse]
    current_streaks: list[StreakResponse]
    notifications_count: int
    rank_global: int | None = None
    rank_monthly: int | None = None


class GamificationStats(BaseModel):
    """Statistiques globales de gamification."""
    tenant_id: str
    total_users: int
    active_users_today: int
    active_users_week: int
    active_users_month: int
    total_points_earned: int
    total_points_spent: int
    total_badges_unlocked: int
    total_challenges_completed: int
    total_rewards_claimed: int
    avg_user_level: Decimal
    top_earners: list[dict[str, Any]]
    popular_badges: list[dict[str, Any]]
    active_challenges_count: int
    active_competitions_count: int


class UserGamificationStats(BaseModel):
    """Statistiques de gamification d'un utilisateur."""
    user_id: UUID
    total_xp: int
    total_coins_earned: int
    total_coins_spent: int
    badges_unlocked: int
    badges_total: int
    challenges_completed: int
    challenges_total_joined: int
    rewards_claimed: int
    current_login_streak: int
    longest_login_streak: int
    rank_global: int | None = None
    rank_monthly: int | None = None
    percentile: Decimal | None = None
    member_since: datetime
    last_activity: datetime | None = None
