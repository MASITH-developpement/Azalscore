"""
Module Programme de Fidélité - GAP-042

Gestion complète des programmes de fidélité:
- Points sur achats et actions
- Niveaux (Bronze, Silver, Gold, Platinum, Diamond)
- Catalogue de récompenses
- Coupons et remises
- Expiration FIFO des points
- Parrainages
- Gamification (badges, challenges)
- Analytics
"""

from .service import (
    # Énumérations
    PointsTransactionType,
    TierLevel,
    RewardType,
    RewardStatus,
    CouponStatus,
    ChallengeType,

    # Configuration
    DEFAULT_TIER_CONFIG,

    # Data classes
    TierConfig,
    EarningRule,
    Reward,
    Member,
    PointsTransaction,
    PointsBatch,
    RewardRedemption,
    Coupon,
    Badge,
    Challenge,
    Referral,

    # Service
    LoyaltyService,
    create_loyalty_service,
)

__all__ = [
    "PointsTransactionType",
    "TierLevel",
    "RewardType",
    "RewardStatus",
    "CouponStatus",
    "ChallengeType",
    "DEFAULT_TIER_CONFIG",
    "TierConfig",
    "EarningRule",
    "Reward",
    "Member",
    "PointsTransaction",
    "PointsBatch",
    "RewardRedemption",
    "Coupon",
    "Badge",
    "Challenge",
    "Referral",
    "LoyaltyService",
    "create_loyalty_service",
]
