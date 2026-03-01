"""
Service de Programme de Fidelite - GAP-042

Gestion complete des programmes de fidelite avec persistence SQLAlchemy:
- Points sur achats, actions, parrainages
- Niveaux de fidelite (Bronze, Silver, Gold, Platinum, Diamond)
- Recompenses catalogue
- Coupons et remises
- Expiration des points
- Gamification (badges, challenges)
- Analytics et segmentation

CRITIQUE: Utilise les repositories pour l'isolation multi-tenant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .models import (
    TierLevel,
    PointsTransactionType,
    RewardType,
    RewardStatus,
    CouponStatus,
    ChallengeType,
    LoyaltyMember,
    LoyaltyReward,
    LoyaltyEarningRule,
    LoyaltyCoupon,
    LoyaltyChallenge,
    LoyaltyBadge,
    LoyaltyPointsTransaction,
    LoyaltyRedemption,
    LoyaltyReferral,
)
from .repository import (
    MemberRepository,
    TransactionRepository,
    RewardRepository,
    RedemptionRepository,
    CouponRepository,
    EarningRuleRepository,
    BadgeRepository,
    ChallengeRepository,
    ReferralRepository,
    LoyaltyStatsRepository,
)


# ============================================================================
# CONFIGURATION NIVEAUX
# ============================================================================

DEFAULT_TIER_CONFIG = {
    TierLevel.BRONZE: {
        "min_points": 0,
        "points_multiplier": Decimal("1.0"),
        "benefits": ["Newsletter exclusive"],
        "color": "#CD7F32"
    },
    TierLevel.SILVER: {
        "min_points": 2500,
        "points_multiplier": Decimal("1.25"),
        "benefits": ["Newsletter exclusive", "Acces ventes privees"],
        "color": "#C0C0C0"
    },
    TierLevel.GOLD: {
        "min_points": 10000,
        "points_multiplier": Decimal("1.5"),
        "benefits": ["Newsletter exclusive", "Acces ventes privees",
                    "Livraison gratuite", "Support prioritaire"],
        "color": "#FFD700"
    },
    TierLevel.PLATINUM: {
        "min_points": 25000,
        "points_multiplier": Decimal("2.0"),
        "benefits": ["Newsletter exclusive", "Acces ventes privees",
                    "Livraison gratuite", "Support prioritaire",
                    "Cadeaux exclusifs", "Invitations evenements"],
        "color": "#E5E4E2"
    },
    TierLevel.DIAMOND: {
        "min_points": 50000,
        "points_multiplier": Decimal("3.0"),
        "benefits": ["Newsletter exclusive", "Acces ventes privees",
                    "Livraison gratuite", "Support VIP dedie",
                    "Cadeaux exclusifs", "Invitations evenements",
                    "Personal shopper", "Avant-premieres produits"],
        "color": "#B9F2FF"
    }
}


@dataclass
class TierConfig:
    """Configuration d'un niveau de fidelite."""
    tier: TierLevel
    min_points: int
    points_multiplier: Decimal
    benefits: List[str]
    color: str
    annual_points_required: Optional[int] = None
    spending_required: Optional[Decimal] = None


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class LoyaltyService:
    """Service de gestion du programme de fidelite avec persistence SQLAlchemy."""

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        points_expiry_months: int = 24,
        referral_points_referrer: int = 500,
        referral_points_referred: int = 200
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.points_expiry_months = points_expiry_months
        self.referral_points_referrer = referral_points_referrer
        self.referral_points_referred = referral_points_referred

        # Repositories avec isolation tenant
        self.member_repo = MemberRepository(db, tenant_id)
        self.transaction_repo = TransactionRepository(db, tenant_id)
        self.reward_repo = RewardRepository(db, tenant_id)
        self.redemption_repo = RedemptionRepository(db, tenant_id)
        self.coupon_repo = CouponRepository(db, tenant_id)
        self.earning_rule_repo = EarningRuleRepository(db, tenant_id)
        self.badge_repo = BadgeRepository(db, tenant_id)
        self.challenge_repo = ChallengeRepository(db, tenant_id)
        self.referral_repo = ReferralRepository(db, tenant_id)
        self.stats_repo = LoyaltyStatsRepository(db, tenant_id)

        # Configuration des niveaux
        self.tier_configs: Dict[TierLevel, TierConfig] = {}
        self._init_default_tiers()

    def _init_default_tiers(self):
        """Initialise les niveaux par defaut."""
        for tier, config in DEFAULT_TIER_CONFIG.items():
            self.tier_configs[tier] = TierConfig(
                tier=tier,
                min_points=config["min_points"],
                points_multiplier=config["points_multiplier"],
                benefits=config["benefits"],
                color=config["color"]
            )

    # ========================================================================
    # MEMBRES
    # ========================================================================

    def enroll_member(
        self,
        customer_id: str,
        email: str,
        birth_date: Optional[datetime] = None,
        preferences: Optional[Dict] = None,
        referral_code: Optional[str] = None,
        welcome_points: int = 100
    ) -> LoyaltyMember:
        """Inscrit un nouveau membre au programme."""
        # Verifier si deja inscrit
        existing = self.member_repo.get_by_customer_id(customer_id)
        if existing:
            raise ValueError(f"Client {customer_id} deja inscrit")

        # Traiter parrainage
        referred_by = None
        if referral_code:
            referrer = self.member_repo.get_by_referral_code(referral_code)
            if referrer:
                referred_by = str(referrer.id)

        member = self.member_repo.create(
            customer_id=customer_id,
            email=email,
            birth_date=birth_date,
            preferences=preferences,
            referred_by=referred_by,
            welcome_points=welcome_points
        )

        # Creer le parrainage si applicable
        if referred_by:
            self.referral_repo.create(
                referrer_member_id=referred_by,
                referred_member_id=str(member.id),
                referral_code=referral_code,
                referrer_points=self.referral_points_referrer,
                referred_points=self.referral_points_referred
            )

        return member

    def get_member(self, member_id: str) -> Optional[LoyaltyMember]:
        """Recupere un membre par ID."""
        return self.member_repo.get_by_id(member_id)

    def get_member_by_customer(self, customer_id: str) -> Optional[LoyaltyMember]:
        """Recupere un membre par customer_id."""
        return self.member_repo.get_by_customer_id(customer_id)

    def list_members(
        self,
        tier: Optional[TierLevel] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LoyaltyMember], int]:
        """Liste les membres avec filtres."""
        return self.member_repo.list_all(
            tier=tier,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size
        )

    def get_member_balance(self, member_id: str) -> Dict[str, Any]:
        """Recupere le solde et info d'un membre."""
        member = self.member_repo.get_by_id(member_id)
        if not member:
            raise ValueError(f"Membre {member_id} non trouve")

        tier_config = self.tier_configs.get(member.tier, self.tier_configs[TierLevel.BRONZE])

        # Points vers le prochain niveau
        next_tier = self._get_next_tier(member.tier)
        points_to_next = 0
        if next_tier:
            next_config = self.tier_configs[next_tier]
            points_to_next = max(0, next_config.min_points - member.points_earned_total)

        return {
            "member_id": str(member.id),
            "points_balance": member.points_balance,
            "points_earned_total": member.points_earned_total,
            "points_redeemed_total": member.points_redeemed_total,
            "points_expired_total": member.points_expired_total,
            "tier": member.tier.value if hasattr(member.tier, 'value') else member.tier,
            "tier_multiplier": float(tier_config.points_multiplier),
            "tier_benefits": tier_config.benefits,
            "next_tier": next_tier.value if next_tier and hasattr(next_tier, 'value') else (next_tier or None),
            "points_to_next_tier": points_to_next,
            "referral_code": member.referral_code,
            "referral_count": member.referral_count,
        }

    def _get_next_tier(self, current_tier: TierLevel) -> Optional[TierLevel]:
        """Retourne le niveau suivant."""
        order = [TierLevel.BRONZE, TierLevel.SILVER, TierLevel.GOLD,
                 TierLevel.PLATINUM, TierLevel.DIAMOND]
        try:
            idx = order.index(current_tier)
            if idx < len(order) - 1:
                return order[idx + 1]
        except ValueError:
            pass
        return None

    # ========================================================================
    # POINTS
    # ========================================================================

    def add_points(
        self,
        member_id: str,
        points: int,
        transaction_type: PointsTransactionType,
        description: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        earning_rule_id: Optional[str] = None
    ) -> Optional[LoyaltyPointsTransaction]:
        """Ajoute des points a un membre."""
        # Calculer expiration
        expires_at = datetime.utcnow() + timedelta(days=self.points_expiry_months * 30)

        transaction = self.member_repo.add_points(
            member_id=member_id,
            points=points,
            transaction_type=transaction_type,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            earning_rule_id=earning_rule_id,
            expires_at=expires_at
        )

        # Mettre a jour le tier
        if transaction:
            self.member_repo.update_tier(member_id)

        return transaction

    def deduct_points(
        self,
        member_id: str,
        points: int,
        transaction_type: PointsTransactionType,
        description: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> Optional[LoyaltyPointsTransaction]:
        """Deduit des points d'un membre."""
        return self.member_repo.deduct_points(
            member_id=member_id,
            points=points,
            transaction_type=transaction_type,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id
        )

    def calculate_purchase_points(
        self,
        member_id: str,
        purchase_amount: Decimal,
        product_ids: Optional[List[str]] = None,
        category_ids: Optional[List[str]] = None
    ) -> int:
        """Calcule les points pour un achat."""
        member = self.member_repo.get_by_id(member_id)
        if not member:
            return 0

        tier_config = self.tier_configs.get(member.tier, self.tier_configs[TierLevel.BRONZE])

        # Obtenir les regles applicables
        rules = self.earning_rule_repo.get_active_for_purchase()

        total_points = 0
        for rule in rules:
            # Verifier conditions
            if rule.min_purchase and purchase_amount < rule.min_purchase:
                continue
            if rule.max_purchase and purchase_amount > rule.max_purchase:
                continue

            # Calculer points
            points = int(purchase_amount * rule.points_per_unit)

            # Appliquer bonus temporaire
            now = datetime.utcnow()
            if rule.bonus_start and rule.bonus_end:
                if rule.bonus_start <= now <= rule.bonus_end:
                    points = int(points * rule.bonus_multiplier)

            # Appliquer multiplicateur de niveau
            points = int(points * tier_config.points_multiplier)

            # Limites
            if rule.max_points_per_transaction:
                points = min(points, rule.max_points_per_transaction)

            total_points += points

        return total_points

    def award_purchase_points(
        self,
        member_id: str,
        purchase_amount: Decimal,
        order_id: str,
        product_ids: Optional[List[str]] = None,
        category_ids: Optional[List[str]] = None
    ) -> Optional[LoyaltyPointsTransaction]:
        """Attribue les points pour un achat."""
        points = self.calculate_purchase_points(
            member_id=member_id,
            purchase_amount=purchase_amount,
            product_ids=product_ids,
            category_ids=category_ids
        )

        if points <= 0:
            return None

        return self.add_points(
            member_id=member_id,
            points=points,
            transaction_type=PointsTransactionType.EARN_PURCHASE,
            description=f"Points pour commande {order_id}",
            reference_type="order",
            reference_id=order_id
        )

    def get_member_transactions(
        self,
        member_id: str,
        transaction_type: Optional[PointsTransactionType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LoyaltyPointsTransaction], int]:
        """Recupere l'historique des transactions d'un membre."""
        return self.transaction_repo.list_by_member(
            member_id=member_id,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )

    def process_expiring_points(self) -> int:
        """Traite l'expiration des points."""
        return self.transaction_repo.process_expiration()

    # ========================================================================
    # RECOMPENSES
    # ========================================================================

    def create_reward(
        self,
        name: str,
        reward_type: RewardType,
        points_cost: int,
        description: Optional[str] = None,
        **kwargs
    ) -> LoyaltyReward:
        """Cree une recompense."""
        return self.reward_repo.create(
            name=name,
            reward_type=reward_type,
            points_cost=points_cost,
            description=description,
            **kwargs
        )

    def get_reward(self, reward_id: str) -> Optional[LoyaltyReward]:
        """Recupere une recompense."""
        return self.reward_repo.get_by_id(reward_id)

    def list_rewards(
        self,
        category: Optional[str] = None,
        status: Optional[RewardStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LoyaltyReward], int]:
        """Liste les recompenses."""
        return self.reward_repo.list_all(
            category=category,
            status=status,
            page=page,
            page_size=page_size
        )

    def list_available_rewards(
        self,
        member_id: str,
        category: Optional[str] = None
    ) -> List[LoyaltyReward]:
        """Liste les recompenses disponibles pour un membre."""
        return self.reward_repo.list_available_for_member(member_id, category)

    def redeem_reward(
        self,
        member_id: str,
        reward_id: str,
        shipping_address: Optional[Dict] = None
    ) -> LoyaltyRedemption:
        """Echange une recompense contre des points."""
        member = self.member_repo.get_by_id(member_id)
        if not member:
            raise ValueError(f"Membre {member_id} non trouve")

        reward = self.reward_repo.get_by_id(reward_id)
        if not reward:
            raise ValueError(f"Recompense {reward_id} non trouvee")

        if reward.status != RewardStatus.AVAILABLE:
            raise ValueError(f"Recompense non disponible")

        if member.points_balance < reward.points_cost:
            raise ValueError(
                f"Solde insuffisant ({member.points_balance} < {reward.points_cost})"
            )

        # Verifier le niveau minimum
        if reward.min_tier:
            tier_order = [TierLevel.BRONZE, TierLevel.SILVER, TierLevel.GOLD,
                         TierLevel.PLATINUM, TierLevel.DIAMOND]
            member_idx = tier_order.index(member.tier)
            required_idx = tier_order.index(reward.min_tier)
            if member_idx < required_idx:
                raise ValueError(f"Niveau {reward.min_tier.value} requis")

        # Verifier limite par membre
        if reward.max_per_member:
            count = self.redemption_repo.count_by_member_reward(member_id, reward_id)
            if count >= reward.max_per_member:
                raise ValueError("Limite d'echanges atteinte")

        # Verifier le stock
        if reward.stock_quantity is not None:
            available = reward.stock_quantity - reward.reserved_quantity
            if available <= 0:
                raise ValueError("Rupture de stock")
            reward.reserved_quantity += 1
            self.db.commit()

        # Deduire les points
        self.deduct_points(
            member_id=member_id,
            points=reward.points_cost,
            transaction_type=PointsTransactionType.REDEEM_REWARD,
            description=f"Echange: {reward.name}",
            reference_type="reward",
            reference_id=reward_id
        )

        # Creer l'echange
        return self.redemption_repo.create(
            member_id=member_id,
            reward=reward,
            shipping_address=shipping_address
        )

    # ========================================================================
    # COUPONS
    # ========================================================================

    def validate_coupon(
        self,
        code: str,
        member_id: Optional[str] = None,
        cart_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Valide un coupon."""
        return self.coupon_repo.validate(code, member_id, cart_amount)

    def use_coupon(self, code: str, order_id: str) -> Optional[LoyaltyCoupon]:
        """Utilise un coupon."""
        return self.coupon_repo.use(code, order_id)

    # ========================================================================
    # REGLES DE GAIN
    # ========================================================================

    def create_earning_rule(
        self,
        name: str,
        transaction_type: PointsTransactionType,
        points_per_unit: Decimal,
        description: Optional[str] = None,
        **kwargs
    ) -> LoyaltyEarningRule:
        """Cree une regle de gain."""
        return self.earning_rule_repo.create(
            name=name,
            transaction_type=transaction_type,
            points_per_unit=points_per_unit,
            description=description,
            **kwargs
        )

    def list_earning_rules(
        self,
        is_active: Optional[bool] = None
    ) -> List[LoyaltyEarningRule]:
        """Liste les regles de gain."""
        return self.earning_rule_repo.list_all(is_active)

    # ========================================================================
    # BADGES ET GAMIFICATION
    # ========================================================================

    def create_badge(
        self,
        name: str,
        icon: str,
        category: str,
        criteria_type: str,
        criteria_value: int,
        description: Optional[str] = None,
        bonus_points: int = 0,
        rarity: str = "common",
        is_secret: bool = False
    ) -> LoyaltyBadge:
        """Cree un badge."""
        return self.badge_repo.create(
            name=name,
            icon=icon,
            category=category,
            criteria_type=criteria_type,
            criteria_value=criteria_value,
            description=description,
            bonus_points=bonus_points,
            rarity=rarity,
            is_secret=is_secret
        )

    def list_badges(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[LoyaltyBadge]:
        """Liste les badges."""
        return self.badge_repo.list_all(category, is_active)

    def award_badge(self, member_id: str, badge_id: str) -> bool:
        """Attribue un badge a un membre."""
        badge = self.badge_repo.get_by_id(badge_id)
        if not badge:
            return False

        success = self.member_repo.add_badge(member_id, badge_id)

        # Attribuer les points bonus
        if success and badge.bonus_points > 0:
            self.add_points(
                member_id=member_id,
                points=badge.bonus_points,
                transaction_type=PointsTransactionType.EARN_BONUS,
                description=f"Badge debloque: {badge.name}",
                reference_type="badge",
                reference_id=badge_id
            )

        return success

    # ========================================================================
    # CHALLENGES
    # ========================================================================

    def create_challenge(
        self,
        name: str,
        challenge_type: ChallengeType,
        target_value: int,
        bonus_points: int,
        start_date: datetime,
        end_date: datetime,
        description: Optional[str] = None,
        min_tier: Optional[TierLevel] = None,
        max_participants: Optional[int] = None
    ) -> LoyaltyChallenge:
        """Cree un challenge."""
        return self.challenge_repo.create(
            name=name,
            challenge_type=challenge_type,
            target_value=target_value,
            bonus_points=bonus_points,
            start_date=start_date,
            end_date=end_date,
            description=description,
            min_tier=min_tier,
            max_participants=max_participants
        )

    def list_active_challenges(self) -> List[LoyaltyChallenge]:
        """Liste les challenges actifs."""
        return self.challenge_repo.list_active()

    def update_challenge_progress(
        self,
        challenge_id: str,
        member_id: str,
        progress_increment: int
    ) -> Dict[str, Any]:
        """Met a jour la progression sur un challenge."""
        result = self.challenge_repo.update_progress(
            challenge_id=challenge_id,
            member_id=member_id,
            progress_increment=progress_increment
        )

        # Attribuer les points si complete
        if result.get("completed") and result.get("points_earned", 0) > 0:
            self.add_points(
                member_id=member_id,
                points=result["points_earned"],
                transaction_type=PointsTransactionType.EARN_CHALLENGE,
                description=f"Challenge complete: {challenge_id}",
                reference_type="challenge",
                reference_id=challenge_id
            )

        return result

    # ========================================================================
    # PARRAINAGES
    # ========================================================================

    def get_referral_link(self, member_id: str) -> Optional[str]:
        """Recupere le lien de parrainage d'un membre."""
        member = self.member_repo.get_by_id(member_id)
        if member:
            return f"?ref={member.referral_code}"
        return None

    def list_member_referrals(self, member_id: str) -> List[LoyaltyReferral]:
        """Liste les parrainages d'un membre."""
        return self.referral_repo.list_by_referrer(member_id)

    def qualify_referral(self, referred_member_id: str) -> Optional[LoyaltyReferral]:
        """Qualifie un parrainage (filleul a fait son premier achat)."""
        referral = self.referral_repo.get_by_referred_member(referred_member_id)
        if not referral or referral.qualified:
            return None

        referral = self.referral_repo.qualify(str(referral.id))
        if not referral:
            return None

        # Attribuer les points au parrain
        self.add_points(
            member_id=referral.referrer_member_id,
            points=referral.referrer_points,
            transaction_type=PointsTransactionType.EARN_REFERRAL,
            description=f"Parrainage qualifie",
            reference_type="referral",
            reference_id=str(referral.id)
        )

        # Attribuer les points au filleul
        self.add_points(
            member_id=referral.referred_member_id,
            points=referral.referred_points,
            transaction_type=PointsTransactionType.EARN_REFERRAL,
            description=f"Bonus de bienvenue parrainage",
            reference_type="referral",
            reference_id=str(referral.id)
        )

        self.referral_repo.award_points(str(referral.id))

        return referral

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_program_statistics(self) -> Dict[str, Any]:
        """Recupere les statistiques du programme."""
        return self.stats_repo.get_program_stats()


# ============================================================================
# FACTORY
# ============================================================================

def create_loyalty_service(
    db: Session,
    tenant_id: str,
    points_expiry_months: int = 24,
    referral_points_referrer: int = 500,
    referral_points_referred: int = 200
) -> LoyaltyService:
    """Cree un service de programme de fidelite."""
    return LoyaltyService(
        db=db,
        tenant_id=tenant_id,
        points_expiry_months=points_expiry_months,
        referral_points_referrer=referral_points_referrer,
        referral_points_referred=referral_points_referred
    )
