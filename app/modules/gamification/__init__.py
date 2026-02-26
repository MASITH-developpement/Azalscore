"""
AZALS MODULE GAMIFICATION
=========================

Module de gamification complet pour AZALSCORE ERP.

Fonctionnalites:
- Points et niveaux utilisateurs (XP, Coins, Karma, Credits)
- Badges et achievements avec progression
- Defis quotidiens/hebdomadaires/mensuels
- Classements (leaderboards) multi-periodes
- Recompenses et boutique
- Regles d'attribution automatique
- Notifications achievements
- Historique progression
- Equipes et competitions
- Dashboard gamification

Inspire de:
- Salesforce Trailhead
- Microsoft Dynamics 365 Gamification
- SAP SuccessFactors

Architecture:
- Multi-tenant avec isolation stricte (tenant_id obligatoire)
- Soft delete pour toutes les entites
- Audit complet avec versioning
- Pattern _base_query() filtre sur toutes les requetes
"""

from .models import (
    # Enums
    PointType,
    TransactionType,
    BadgeRarity,
    BadgeStatus,
    ChallengeType,
    ChallengeStatus,
    RewardType,
    RewardStatus,
    LeaderboardPeriod,
    LeaderboardScope,
    RuleEventType,
    CompetitionStatus,
    NotificationType,
    # Models
    GamificationLevel,
    UserGamificationProfile,
    PointTransaction,
    BadgeCategory,
    GamificationBadge,
    UserBadge,
    GamificationChallenge,
    UserChallenge,
    GamificationReward,
    RewardClaim,
    GamificationRule,
    RuleTriggerLog,
    GamificationTeam,
    TeamMembership,
    GamificationCompetition,
    CompetitionParticipant,
    Leaderboard,
    LeaderboardEntry,
    GamificationNotification,
    GamificationActivity,
    GamificationStreak,
    GamificationConfig,
)

from .schemas import (
    # Base
    PaginatedResponse,
    AutocompleteItem,
    AutocompleteResponse,
    # Niveaux
    LevelCreate,
    LevelUpdate,
    LevelResponse,
    # Profils
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserProfileSummary,
    # Points
    PointBalanceResponse,
    AwardPointsRequest,
    SpendPointsRequest,
    TransferPointsRequest,
    PointTransactionResponse,
    PointTransactionFilters,
    # Badges
    BadgeCategoryCreate,
    BadgeCategoryResponse,
    BadgeCreate,
    BadgeUpdate,
    BadgeResponse,
    BadgeFilters,
    UserBadgeResponse,
    # Defis
    ChallengeCreate,
    ChallengeUpdate,
    ChallengeResponse,
    ChallengeFilters,
    UserChallengeResponse,
    JoinChallengeRequest,
    UpdateProgressRequest,
    # Recompenses
    RewardCreate,
    RewardUpdate,
    RewardResponse,
    RewardFilters,
    ClaimRewardRequest,
    RewardClaimResponse,
    UpdateClaimStatusRequest,
    # Regles
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    TriggerRuleRequest,
    # Equipes
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamMemberResponse,
    JoinTeamRequest,
    InviteToTeamRequest,
    # Competitions
    CompetitionCreate,
    CompetitionUpdate,
    CompetitionResponse,
    CompetitionParticipantResponse,
    # Leaderboards
    LeaderboardCreate,
    LeaderboardUpdate,
    LeaderboardResponse,
    LeaderboardWithEntries,
    LeaderboardEntryResponse,
    # Notifications
    NotificationResponse,
    MarkNotificationsReadRequest,
    # Streaks
    StreakResponse,
    # Activite
    ActivityResponse,
    ActivityFilters,
    # Configuration
    GamificationConfigUpdate,
    GamificationConfigResponse,
    # Dashboard
    GamificationDashboard,
    GamificationStats,
    UserGamificationStats,
)

from .service import GamificationService, create_gamification_service

from .router import router

from .exceptions import (
    GamificationError,
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    InsufficientPointsError,
    InvalidPointAmountError,
    PointsExpiredError,
    DailyPointLimitExceededError,
    BadgeNotFoundError,
    BadgeAlreadyUnlockedError,
    BadgeNotAvailableError,
    BadgeLimitReachedError,
    BadgeCategoryNotFoundError,
    ChallengeNotFoundError,
    ChallengeNotActiveError,
    ChallengeFullError,
    AlreadyJoinedChallengeError,
    ChallengeNotJoinedError,
    RewardsAlreadyClaimedError,
    ChallengeNotCompletedError,
    RegistrationClosedError,
    RewardNotFoundError,
    RewardNotAvailableError,
    RewardOutOfStockError,
    RewardLimitReachedError,
    LevelRequirementNotMetError,
    ClaimNotFoundError,
    ClaimStatusError,
    RuleNotFoundError,
    RuleTriggerError,
    RuleCooldownError,
    RuleConditionError,
    TeamNotFoundError,
    TeamFullError,
    AlreadyInTeamError,
    NotTeamMemberError,
    NotTeamCaptainError,
    CannotLeaveAsLastMemberError,
    CompetitionNotFoundError,
    CompetitionNotOpenError,
    AlreadyRegisteredError,
    CompetitionFullError,
    LeaderboardNotFoundError,
    LevelNotFoundError,
    InvalidLevelConfigError,
    ConfigNotFoundError,
    FeatureDisabledError,
    DuplicateCodeError,
    InvalidStateError,
    PermissionDeniedError,
    RateLimitError,
)

__all__ = [
    # Router
    "router",
    # Service
    "GamificationService",
    "create_gamification_service",
    # Enums
    "PointType",
    "TransactionType",
    "BadgeRarity",
    "BadgeStatus",
    "ChallengeType",
    "ChallengeStatus",
    "RewardType",
    "RewardStatus",
    "LeaderboardPeriod",
    "LeaderboardScope",
    "RuleEventType",
    "CompetitionStatus",
    "NotificationType",
    # Models
    "GamificationLevel",
    "UserGamificationProfile",
    "PointTransaction",
    "BadgeCategory",
    "GamificationBadge",
    "UserBadge",
    "GamificationChallenge",
    "UserChallenge",
    "GamificationReward",
    "RewardClaim",
    "GamificationRule",
    "RuleTriggerLog",
    "GamificationTeam",
    "TeamMembership",
    "GamificationCompetition",
    "CompetitionParticipant",
    "Leaderboard",
    "LeaderboardEntry",
    "GamificationNotification",
    "GamificationActivity",
    "GamificationStreak",
    "GamificationConfig",
    # Schemas
    "PaginatedResponse",
    "LevelCreate",
    "LevelUpdate",
    "LevelResponse",
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileResponse",
    "UserProfileSummary",
    "PointBalanceResponse",
    "AwardPointsRequest",
    "SpendPointsRequest",
    "TransferPointsRequest",
    "PointTransactionResponse",
    "PointTransactionFilters",
    "BadgeCategoryCreate",
    "BadgeCategoryResponse",
    "BadgeCreate",
    "BadgeUpdate",
    "BadgeResponse",
    "BadgeFilters",
    "UserBadgeResponse",
    "ChallengeCreate",
    "ChallengeUpdate",
    "ChallengeResponse",
    "ChallengeFilters",
    "UserChallengeResponse",
    "RewardCreate",
    "RewardUpdate",
    "RewardResponse",
    "RewardFilters",
    "ClaimRewardRequest",
    "RewardClaimResponse",
    "RuleCreate",
    "RuleUpdate",
    "RuleResponse",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamMemberResponse",
    "CompetitionCreate",
    "CompetitionUpdate",
    "CompetitionResponse",
    "CompetitionParticipantResponse",
    "LeaderboardCreate",
    "LeaderboardUpdate",
    "LeaderboardResponse",
    "LeaderboardWithEntries",
    "LeaderboardEntryResponse",
    "NotificationResponse",
    "MarkNotificationsReadRequest",
    "StreakResponse",
    "ActivityResponse",
    "ActivityFilters",
    "GamificationConfigUpdate",
    "GamificationConfigResponse",
    "GamificationDashboard",
    "GamificationStats",
    "UserGamificationStats",
    # Exceptions
    "GamificationError",
    "ProfileNotFoundError",
    "InsufficientPointsError",
    "BadgeNotFoundError",
    "BadgeAlreadyUnlockedError",
    "ChallengeNotFoundError",
    "RewardNotFoundError",
    "TeamNotFoundError",
    "CompetitionNotFoundError",
    "FeatureDisabledError",
]
