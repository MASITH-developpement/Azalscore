"""
Module Referral / Parrainage - GAP-070
======================================

Programme de parrainage:
- Programmes configurables
- Codes de parrainage uniques
- Récompenses multi-niveaux
- Tracking des conversions
- Commissions et paiements
- Analytics et ROI
- Détection de fraude
"""

# Models
from .models import (
    ProgramStatus,
    RewardType,
    RewardTrigger,
    ReferralStatus,
    PayoutStatus,
    FraudReason,
    ReferralProgram,
    RewardTier,
    ReferralCode,
    Referral,
    Reward,
    Payout,
    FraudCheck,
)

# Schemas
from .schemas import (
    # Program
    ReferralProgramCreate,
    ReferralProgramUpdate,
    ReferralProgramResponse,
    ReferralProgramListResponse,
    ProgramFilters,
    # Tier
    RewardTierCreate,
    RewardTierUpdate,
    RewardTierResponse,
    # Code
    ReferralCodeCreate,
    ReferralCodeUpdate,
    ReferralCodeResponse,
    ReferralCodeListResponse,
    # Referral
    ReferralCreate,
    ReferralResponse,
    ReferralListResponse,
    ReferralFilters,
    # Reward
    RewardResponse,
    # Payout
    PayoutCreate,
    PayoutUpdate,
    PayoutResponse,
    PayoutListResponse,
    PayoutFilters,
    # Tracking
    TrackClickRequest,
    TrackSignupRequest,
    TrackConversionRequest,
    # Stats
    ReferralStats,
    ReferrerProfile,
    # Common
    AutocompleteResponse,
    BulkResult,
)

# Exceptions
from .exceptions import (
    ReferralError,
    ProgramNotFoundError,
    ProgramDuplicateError,
    ProgramValidationError,
    ProgramStateError,
    ProgramBudgetExceededError,
    ProgramLimitReachedError,
    RewardTierNotFoundError,
    RewardTierValidationError,
    ReferralCodeNotFoundError,
    ReferralCodeDuplicateError,
    ReferralCodeExpiredError,
    ReferralCodeLimitReachedError,
    ReferralCodeInactiveError,
    ReferralNotFoundError,
    ReferralValidationError,
    ReferralStateError,
    ReferralExpiredError,
    SelfReferralError,
    DuplicateRefereeError,
    RewardNotFoundError,
    RewardValidationError,
    RewardAlreadyClaimedError,
    RewardExpiredError,
    PayoutNotFoundError,
    PayoutValidationError,
    PayoutStateError,
    PayoutMinimumNotReachedError,
    FraudDetectedError,
    FraudCheckFailedError,
)

# Repository
from .repository import (
    ProgramRepository,
    RewardTierRepository,
    ReferralCodeRepository,
    ReferralRepository,
    RewardRepository,
    PayoutRepository,
    FraudCheckRepository,
)

# Service
from .service import ReferralService

# Router
from .router import router


__all__ = [
    # Enums
    "ProgramStatus",
    "RewardType",
    "RewardTrigger",
    "ReferralStatus",
    "PayoutStatus",
    "FraudReason",
    # Models
    "ReferralProgram",
    "RewardTier",
    "ReferralCode",
    "Referral",
    "Reward",
    "Payout",
    "FraudCheck",
    # Program Schemas
    "ReferralProgramCreate",
    "ReferralProgramUpdate",
    "ReferralProgramResponse",
    "ReferralProgramListResponse",
    "ProgramFilters",
    # Tier Schemas
    "RewardTierCreate",
    "RewardTierUpdate",
    "RewardTierResponse",
    # Code Schemas
    "ReferralCodeCreate",
    "ReferralCodeUpdate",
    "ReferralCodeResponse",
    "ReferralCodeListResponse",
    # Referral Schemas
    "ReferralCreate",
    "ReferralResponse",
    "ReferralListResponse",
    "ReferralFilters",
    # Reward Schemas
    "RewardResponse",
    # Payout Schemas
    "PayoutCreate",
    "PayoutUpdate",
    "PayoutResponse",
    "PayoutListResponse",
    "PayoutFilters",
    # Tracking Schemas
    "TrackClickRequest",
    "TrackSignupRequest",
    "TrackConversionRequest",
    # Stats Schemas
    "ReferralStats",
    "ReferrerProfile",
    # Common Schemas
    "AutocompleteResponse",
    "BulkResult",
    # Exceptions
    "ReferralError",
    "ProgramNotFoundError",
    "ProgramDuplicateError",
    "ProgramValidationError",
    "ProgramStateError",
    "ProgramBudgetExceededError",
    "ProgramLimitReachedError",
    "RewardTierNotFoundError",
    "RewardTierValidationError",
    "ReferralCodeNotFoundError",
    "ReferralCodeDuplicateError",
    "ReferralCodeExpiredError",
    "ReferralCodeLimitReachedError",
    "ReferralCodeInactiveError",
    "ReferralNotFoundError",
    "ReferralValidationError",
    "ReferralStateError",
    "ReferralExpiredError",
    "SelfReferralError",
    "DuplicateRefereeError",
    "RewardNotFoundError",
    "RewardValidationError",
    "RewardAlreadyClaimedError",
    "RewardExpiredError",
    "PayoutNotFoundError",
    "PayoutValidationError",
    "PayoutStateError",
    "PayoutMinimumNotReachedError",
    "FraudDetectedError",
    "FraudCheckFailedError",
    # Repository
    "ProgramRepository",
    "RewardTierRepository",
    "ReferralCodeRepository",
    "ReferralRepository",
    "RewardRepository",
    "PayoutRepository",
    "FraudCheckRepository",
    # Service
    "ReferralService",
    # Router
    "router",
]
