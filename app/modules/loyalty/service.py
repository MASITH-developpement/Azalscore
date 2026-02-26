"""
Service de Programme de Fidélité - GAP-042

Gestion complète des programmes de fidélité:
- Points sur achats, actions, parrainages
- Niveaux de fidélité (Bronze, Silver, Gold, Platinum)
- Récompenses catalogue
- Coupons et remises
- Expiration des points
- Transferts et dons
- Gamification (badges, challenges)
- Analytics et segmentation
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4


class PointsTransactionType(Enum):
    """Type de transaction de points."""
    EARN_PURCHASE = "earn_purchase"  # Achat
    EARN_REFERRAL = "earn_referral"  # Parrainage
    EARN_REVIEW = "earn_review"  # Avis client
    EARN_BIRTHDAY = "earn_birthday"  # Anniversaire
    EARN_SIGNUP = "earn_signup"  # Inscription
    EARN_SOCIAL = "earn_social"  # Partage social
    EARN_CHALLENGE = "earn_challenge"  # Challenge complété
    EARN_BONUS = "earn_bonus"  # Bonus manuel
    REDEEM_REWARD = "redeem_reward"  # Échange récompense
    REDEEM_DISCOUNT = "redeem_discount"  # Remise
    TRANSFER_OUT = "transfer_out"  # Transfert sortant
    TRANSFER_IN = "transfer_in"  # Transfert entrant
    EXPIRE = "expire"  # Expiration
    ADJUST = "adjust"  # Ajustement manuel
    REVERSAL = "reversal"  # Annulation


class TierLevel(Enum):
    """Niveau de fidélité."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class RewardType(Enum):
    """Type de récompense."""
    PRODUCT = "product"  # Produit physique
    DISCOUNT_PERCENT = "discount_percent"  # % de remise
    DISCOUNT_AMOUNT = "discount_amount"  # Montant de remise
    FREE_SHIPPING = "free_shipping"  # Livraison gratuite
    SERVICE = "service"  # Service
    EXPERIENCE = "experience"  # Expérience
    VOUCHER = "voucher"  # Bon d'achat
    CHARITY = "charity"  # Don caritatif
    UPGRADE = "upgrade"  # Upgrade niveau


class RewardStatus(Enum):
    """Statut d'une récompense."""
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    COMING_SOON = "coming_soon"
    DISCONTINUED = "discontinued"


class CouponStatus(Enum):
    """Statut d'un coupon."""
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ChallengeType(Enum):
    """Type de challenge."""
    PURCHASE_COUNT = "purchase_count"  # Nombre d'achats
    PURCHASE_AMOUNT = "purchase_amount"  # Montant d'achats
    CATEGORY_PURCHASE = "category_purchase"  # Achats catégorie
    STREAK = "streak"  # Jours consécutifs
    REFERRAL = "referral"  # Parrainages
    REVIEW = "review"  # Avis laissés
    SOCIAL_SHARE = "social_share"  # Partages
    COLLECTION = "collection"  # Collection de badges


# Configurations par défaut des niveaux
DEFAULT_TIER_CONFIG = {
    TierLevel.BRONZE: {
        "min_points": 0,
        "points_multiplier": Decimal("1.0"),
        "benefits": ["Newsletter exclusive"],
        "color": "#CD7F32"
    },
    TierLevel.SILVER: {
        "min_points": 1000,
        "points_multiplier": Decimal("1.25"),
        "benefits": ["Newsletter exclusive", "Accès ventes privées"],
        "color": "#C0C0C0"
    },
    TierLevel.GOLD: {
        "min_points": 5000,
        "points_multiplier": Decimal("1.5"),
        "benefits": ["Newsletter exclusive", "Accès ventes privées",
                    "Livraison gratuite", "Support prioritaire"],
        "color": "#FFD700"
    },
    TierLevel.PLATINUM: {
        "min_points": 15000,
        "points_multiplier": Decimal("2.0"),
        "benefits": ["Newsletter exclusive", "Accès ventes privées",
                    "Livraison gratuite", "Support prioritaire",
                    "Cadeaux exclusifs", "Invitations événements"],
        "color": "#E5E4E2"
    },
    TierLevel.DIAMOND: {
        "min_points": 50000,
        "points_multiplier": Decimal("3.0"),
        "benefits": ["Newsletter exclusive", "Accès ventes privées",
                    "Livraison gratuite", "Support VIP dédié",
                    "Cadeaux exclusifs", "Invitations événements",
                    "Personal shopper", "Avant-premières produits"],
        "color": "#B9F2FF"
    }
}


@dataclass
class TierConfig:
    """Configuration d'un niveau de fidélité."""
    tier: TierLevel
    min_points: int
    points_multiplier: Decimal
    benefits: List[str]
    color: str
    annual_points_required: Optional[int] = None
    spending_required: Optional[Decimal] = None
    icon: Optional[str] = None


@dataclass
class EarningRule:
    """Règle de gain de points."""
    rule_id: str
    tenant_id: str
    name: str
    description: str
    transaction_type: PointsTransactionType
    points_per_unit: Decimal  # Points par euro ou par action
    is_active: bool = True

    # Conditions
    min_purchase: Optional[Decimal] = None
    max_purchase: Optional[Decimal] = None
    included_categories: List[str] = field(default_factory=list)
    excluded_categories: List[str] = field(default_factory=list)
    included_products: List[str] = field(default_factory=list)
    excluded_products: List[str] = field(default_factory=list)

    # Limites
    max_points_per_transaction: Optional[int] = None
    max_points_per_day: Optional[int] = None
    max_uses_per_member: Optional[int] = None

    # Bonus temporaire
    bonus_multiplier: Decimal = Decimal("1.0")
    bonus_start: Optional[datetime] = None
    bonus_end: Optional[datetime] = None

    # Validité
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


@dataclass
class Reward:
    """Récompense du catalogue."""
    reward_id: str
    tenant_id: str
    name: str
    description: str
    reward_type: RewardType
    points_cost: int
    status: RewardStatus = RewardStatus.AVAILABLE

    # Valeur
    value: Optional[Decimal] = None  # Valeur en euros
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None

    # Stock
    stock_quantity: Optional[int] = None  # None = illimité
    reserved_quantity: int = 0

    # Restrictions
    min_tier: Optional[TierLevel] = None
    max_per_member: Optional[int] = None
    valid_for_days: int = 365  # Validité après échange

    # Catégories applicables (pour remises)
    applicable_categories: List[str] = field(default_factory=list)
    applicable_products: List[str] = field(default_factory=list)

    # Images et présentation
    image_url: Optional[str] = None
    category: str = "general"
    sort_order: int = 0

    # Dates
    available_from: Optional[date] = None
    available_to: Optional[date] = None


@dataclass
class Member:
    """Membre du programme de fidélité."""
    member_id: str
    tenant_id: str
    customer_id: str
    email: str
    enrolled_at: datetime
    tier: TierLevel = TierLevel.BRONZE

    # Solde
    points_balance: int = 0
    points_earned_total: int = 0
    points_redeemed_total: int = 0
    points_expired_total: int = 0

    # Historique année en cours
    points_earned_ytd: int = 0
    spending_ytd: Decimal = Decimal("0")

    # Anniversaire et préférences
    birth_date: Optional[date] = None
    preferences: Dict[str, Any] = field(default_factory=dict)

    # Parrainage
    referral_code: str = ""
    referred_by: Optional[str] = None
    referral_count: int = 0

    # Gamification
    badges: List[str] = field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    last_activity: Optional[datetime] = None

    # Statut
    is_active: bool = True
    opted_out_marketing: bool = False


@dataclass
class PointsTransaction:
    """Transaction de points."""
    transaction_id: str
    tenant_id: str
    member_id: str
    transaction_type: PointsTransactionType
    points: int  # Positif = gain, négatif = dépense
    balance_after: int
    description: str
    created_at: datetime = field(default_factory=datetime.now)

    # Référence
    reference_type: Optional[str] = None  # "order", "reward", "transfer"
    reference_id: Optional[str] = None
    earning_rule_id: Optional[str] = None

    # Expiration
    expires_at: Optional[datetime] = None
    expired: bool = False

    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PointsBatch:
    """Lot de points avec expiration commune."""
    batch_id: str
    tenant_id: str
    member_id: str
    original_points: int
    remaining_points: int
    earned_at: datetime
    expires_at: datetime
    source_transaction_id: str
    is_expired: bool = False


@dataclass
class RewardRedemption:
    """Échange de récompense."""
    redemption_id: str
    tenant_id: str
    member_id: str
    reward_id: str
    points_spent: int
    redeemed_at: datetime = field(default_factory=datetime.now)

    # Détails de la récompense
    reward_name: str = ""
    reward_type: RewardType = RewardType.VOUCHER
    reward_value: Optional[Decimal] = None

    # Coupon généré
    coupon_code: Optional[str] = None
    coupon_valid_until: Optional[datetime] = None
    coupon_used: bool = False

    # Livraison (si produit physique)
    shipping_address: Optional[Dict[str, str]] = None
    shipped_at: Optional[datetime] = None
    tracking_number: Optional[str] = None

    # Statut
    status: str = "completed"  # completed, pending, shipped, cancelled


@dataclass
class Coupon:
    """Coupon de réduction."""
    coupon_id: str
    tenant_id: str
    code: str
    member_id: Optional[str]  # None = coupon générique
    status: CouponStatus = CouponStatus.ACTIVE

    # Type et valeur
    discount_type: str = "percent"  # percent, amount
    discount_value: Decimal = Decimal("0")
    min_purchase: Optional[Decimal] = None
    max_discount: Optional[Decimal] = None

    # Restrictions
    applicable_categories: List[str] = field(default_factory=list)
    applicable_products: List[str] = field(default_factory=list)

    # Utilisation
    max_uses: int = 1
    current_uses: int = 0
    max_uses_per_member: int = 1

    # Dates
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    # Source
    source_type: Optional[str] = None  # "reward", "campaign", "manual"
    source_id: Optional[str] = None


@dataclass
class Badge:
    """Badge de gamification."""
    badge_id: str
    tenant_id: str
    name: str
    description: str
    icon: str
    category: str  # "purchase", "engagement", "loyalty", "social"

    # Critères
    criteria_type: str  # "count", "amount", "streak", "collection"
    criteria_value: int
    criteria_details: Dict[str, Any] = field(default_factory=dict)

    # Bonus
    bonus_points: int = 0

    # Rareté
    rarity: str = "common"  # common, rare, epic, legendary

    # Statut
    is_active: bool = True
    is_secret: bool = False  # Badge caché jusqu'à débloqué


@dataclass
class Challenge:
    """Challenge temporaire."""
    challenge_id: str
    tenant_id: str
    name: str
    description: str
    challenge_type: ChallengeType
    target_value: int
    bonus_points: int

    # Dates
    start_date: datetime
    end_date: datetime

    # Restrictions
    min_tier: Optional[TierLevel] = None
    max_participants: Optional[int] = None

    # Progression
    participants: Dict[str, int] = field(default_factory=dict)
    completions: int = 0

    # Statut
    is_active: bool = True


@dataclass
class Referral:
    """Parrainage."""
    referral_id: str
    tenant_id: str
    referrer_member_id: str
    referred_member_id: str
    referral_code: str
    referred_at: datetime = field(default_factory=datetime.now)

    # Récompenses
    referrer_points: int = 0
    referred_points: int = 0
    points_awarded: bool = False
    awarded_at: Optional[datetime] = None

    # Condition de qualification
    qualification_criteria: str = "first_purchase"  # signup, first_purchase
    qualified: bool = False
    qualified_at: Optional[datetime] = None


class LoyaltyService:
    """Service de gestion du programme de fidélité."""

    def __init__(
        self,
        tenant_id: str,
        member_repository: Optional[Any] = None,
        points_repository: Optional[Any] = None,
        reward_repository: Optional[Any] = None,
        tier_config: Optional[Dict[TierLevel, TierConfig]] = None,
        points_expiry_months: int = 24,
        referral_points_referrer: int = 500,
        referral_points_referred: int = 200
    ):
        self.tenant_id = tenant_id
        self.member_repo = member_repository or {}
        self.points_repo = points_repository or {}
        self.reward_repo = reward_repository or {}

        # Configuration
        self.points_expiry_months = points_expiry_months
        self.referral_points_referrer = referral_points_referrer
        self.referral_points_referred = referral_points_referred

        # Niveaux
        self.tier_configs: Dict[TierLevel, TierConfig] = {}
        if tier_config:
            self.tier_configs = tier_config
        else:
            self._init_default_tiers()

        # Caches
        self._members: Dict[str, Member] = {}
        self._earning_rules: Dict[str, EarningRule] = {}
        self._rewards: Dict[str, Reward] = {}
        self._transactions: Dict[str, PointsTransaction] = {}
        self._batches: Dict[str, PointsBatch] = {}
        self._redemptions: Dict[str, RewardRedemption] = {}
        self._coupons: Dict[str, Coupon] = {}
        self._badges: Dict[str, Badge] = {}
        self._challenges: Dict[str, Challenge] = {}
        self._referrals: Dict[str, Referral] = {}

    def _init_default_tiers(self):
        """Initialise les niveaux par défaut."""
        for tier, config in DEFAULT_TIER_CONFIG.items():
            self.tier_configs[tier] = TierConfig(
                tier=tier,
                min_points=config["min_points"],
                points_multiplier=config["points_multiplier"],
                benefits=config["benefits"],
                color=config["color"]
            )

    # =========================================================================
    # Gestion des Membres
    # =========================================================================

    def enroll_member(
        self,
        customer_id: str,
        email: str,
        referral_code: Optional[str] = None,
        birth_date: Optional[date] = None,
        **kwargs
    ) -> Member:
        """Inscrit un nouveau membre."""
        # Vérifier si déjà membre
        existing = self.get_member_by_customer(customer_id)
        if existing:
            raise ValueError(f"Client {customer_id} déjà inscrit")

        member_id = f"mbr_{uuid4().hex[:12]}"
        member_referral_code = f"REF{uuid4().hex[:8].upper()}"

        member = Member(
            member_id=member_id,
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            email=email,
            enrolled_at=datetime.now(),
            birth_date=birth_date,
            referral_code=member_referral_code,
            preferences=kwargs.get("preferences", {})
        )

        # Traiter le parrainage
        if referral_code:
            referrer = self._find_member_by_referral_code(referral_code)
            if referrer:
                member.referred_by = referrer.member_id
                self._create_referral(referrer, member, referral_code)

        # Points de bienvenue
        welcome_points = kwargs.get("welcome_points", 100)
        if welcome_points > 0:
            self._add_points(
                member,
                welcome_points,
                PointsTransactionType.EARN_SIGNUP,
                "Points de bienvenue"
            )

        self._members[member_id] = member
        return member

    def get_member(self, member_id: str) -> Optional[Member]:
        """Récupère un membre par ID."""
        return self._members.get(member_id)

    def get_member_by_customer(self, customer_id: str) -> Optional[Member]:
        """Récupère un membre par ID client."""
        for member in self._members.values():
            if member.tenant_id == self.tenant_id and member.customer_id == customer_id:
                return member
        return None

    def _find_member_by_referral_code(self, code: str) -> Optional[Member]:
        """Trouve un membre par son code de parrainage."""
        for member in self._members.values():
            if member.referral_code == code and member.is_active:
                return member
        return None

    def update_member_tier(self, member_id: str) -> TierLevel:
        """Met à jour le niveau d'un membre selon ses points."""
        member = self._members.get(member_id)
        if not member:
            raise ValueError(f"Membre {member_id} non trouvé")

        # Trouver le niveau applicable
        new_tier = TierLevel.BRONZE
        for tier, config in sorted(
            self.tier_configs.items(),
            key=lambda x: x[1].min_points,
            reverse=True
        ):
            if member.points_earned_ytd >= config.min_points:
                new_tier = tier
                break

        if new_tier != member.tier:
            old_tier = member.tier
            member.tier = new_tier
            # Pourrait déclencher notification ici

        return member.tier

    # =========================================================================
    # Règles de Gain
    # =========================================================================

    def create_earning_rule(
        self,
        name: str,
        description: str,
        transaction_type: PointsTransactionType,
        points_per_unit: Decimal,
        **kwargs
    ) -> EarningRule:
        """Crée une règle de gain de points."""
        rule_id = f"rule_{uuid4().hex[:12]}"

        rule = EarningRule(
            rule_id=rule_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            transaction_type=transaction_type,
            points_per_unit=points_per_unit,
            is_active=kwargs.get("is_active", True),
            min_purchase=kwargs.get("min_purchase"),
            max_purchase=kwargs.get("max_purchase"),
            included_categories=kwargs.get("included_categories", []),
            excluded_categories=kwargs.get("excluded_categories", []),
            included_products=kwargs.get("included_products", []),
            excluded_products=kwargs.get("excluded_products", []),
            max_points_per_transaction=kwargs.get("max_points_per_transaction"),
            max_points_per_day=kwargs.get("max_points_per_day"),
            max_uses_per_member=kwargs.get("max_uses_per_member"),
            bonus_multiplier=Decimal(str(kwargs.get("bonus_multiplier", "1.0"))),
            bonus_start=kwargs.get("bonus_start"),
            bonus_end=kwargs.get("bonus_end"),
            valid_from=kwargs.get("valid_from"),
            valid_to=kwargs.get("valid_to")
        )

        self._earning_rules[rule_id] = rule
        return rule

    def get_applicable_rules(
        self,
        transaction_type: PointsTransactionType,
        amount: Optional[Decimal] = None,
        product_id: Optional[str] = None,
        category_id: Optional[str] = None,
        as_of: Optional[datetime] = None
    ) -> List[EarningRule]:
        """Récupère les règles applicables."""
        as_of = as_of or datetime.now()
        applicable = []

        for rule in self._earning_rules.values():
            if rule.tenant_id != self.tenant_id:
                continue
            if not rule.is_active:
                continue
            if rule.transaction_type != transaction_type:
                continue

            # Vérifier les dates
            if rule.valid_from and as_of.date() < rule.valid_from:
                continue
            if rule.valid_to and as_of.date() > rule.valid_to:
                continue

            # Vérifier le montant
            if amount is not None:
                if rule.min_purchase and amount < rule.min_purchase:
                    continue
                if rule.max_purchase and amount > rule.max_purchase:
                    continue

            # Vérifier les produits/catégories
            if rule.included_products and product_id not in rule.included_products:
                continue
            if rule.excluded_products and product_id in rule.excluded_products:
                continue
            if rule.included_categories and category_id not in rule.included_categories:
                continue
            if rule.excluded_categories and category_id in rule.excluded_categories:
                continue

            applicable.append(rule)

        return applicable

    # =========================================================================
    # Transactions de Points
    # =========================================================================

    def _add_points(
        self,
        member: Member,
        points: int,
        transaction_type: PointsTransactionType,
        description: str,
        **kwargs
    ) -> PointsTransaction:
        """Ajoute des points à un membre (interne)."""
        # Appliquer le multiplicateur de niveau
        tier_config = self.tier_configs.get(member.tier)
        if tier_config and transaction_type == PointsTransactionType.EARN_PURCHASE:
            points = int(Decimal(str(points)) * tier_config.points_multiplier)

        # Calculer l'expiration
        expires_at = datetime.now() + timedelta(days=self.points_expiry_months * 30)

        # Mettre à jour le solde
        member.points_balance += points
        member.points_earned_total += points
        member.points_earned_ytd += points

        transaction = PointsTransaction(
            transaction_id=f"pts_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            member_id=member.member_id,
            transaction_type=transaction_type,
            points=points,
            balance_after=member.points_balance,
            description=description,
            expires_at=expires_at,
            reference_type=kwargs.get("reference_type"),
            reference_id=kwargs.get("reference_id"),
            earning_rule_id=kwargs.get("earning_rule_id"),
            metadata=kwargs.get("metadata", {})
        )

        self._transactions[transaction.transaction_id] = transaction

        # Créer le batch pour expiration
        batch = PointsBatch(
            batch_id=f"batch_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            member_id=member.member_id,
            original_points=points,
            remaining_points=points,
            earned_at=datetime.now(),
            expires_at=expires_at,
            source_transaction_id=transaction.transaction_id
        )
        self._batches[batch.batch_id] = batch

        # Mettre à jour le niveau
        self.update_member_tier(member.member_id)

        return transaction

    def _deduct_points(
        self,
        member: Member,
        points: int,
        transaction_type: PointsTransactionType,
        description: str,
        **kwargs
    ) -> PointsTransaction:
        """Déduit des points d'un membre (FIFO)."""
        if member.points_balance < points:
            raise ValueError(
                f"Solde insuffisant: {member.points_balance} < {points}"
            )

        # Déduire en FIFO (plus anciens d'abord)
        remaining_to_deduct = points
        batches = sorted(
            [b for b in self._batches.values()
             if b.member_id == member.member_id
             and b.remaining_points > 0
             and not b.is_expired],
            key=lambda x: x.earned_at
        )

        for batch in batches:
            if remaining_to_deduct <= 0:
                break

            deduct_from_batch = min(batch.remaining_points, remaining_to_deduct)
            batch.remaining_points -= deduct_from_batch
            remaining_to_deduct -= deduct_from_batch

        # Mettre à jour le solde
        member.points_balance -= points
        member.points_redeemed_total += points

        transaction = PointsTransaction(
            transaction_id=f"pts_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            member_id=member.member_id,
            transaction_type=transaction_type,
            points=-points,
            balance_after=member.points_balance,
            description=description,
            reference_type=kwargs.get("reference_type"),
            reference_id=kwargs.get("reference_id"),
            metadata=kwargs.get("metadata", {})
        )

        self._transactions[transaction.transaction_id] = transaction
        return transaction

    def earn_points_on_purchase(
        self,
        member_id: str,
        order_id: str,
        amount: Decimal,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> PointsTransaction:
        """Crédite des points sur un achat."""
        member = self._members.get(member_id)
        if not member:
            raise ValueError(f"Membre {member_id} non trouvé")

        # Trouver les règles applicables
        rules = self.get_applicable_rules(
            PointsTransactionType.EARN_PURCHASE,
            amount=amount
        )

        if not rules:
            # Règle par défaut: 1 point par euro
            points = int(amount)
        else:
            # Appliquer la meilleure règle
            best_rule = max(rules, key=lambda r: r.points_per_unit)
            points = int(amount * best_rule.points_per_unit)

            # Appliquer le bonus si actif
            now = datetime.now()
            if (best_rule.bonus_start and best_rule.bonus_end and
                best_rule.bonus_start <= now <= best_rule.bonus_end):
                points = int(Decimal(str(points)) * best_rule.bonus_multiplier)

            # Appliquer le plafond
            if best_rule.max_points_per_transaction:
                points = min(points, best_rule.max_points_per_transaction)

        # Mettre à jour le spending YTD
        member.spending_ytd += amount
        member.last_activity = datetime.now()

        return self._add_points(
            member,
            points,
            PointsTransactionType.EARN_PURCHASE,
            f"Points sur commande {order_id}",
            reference_type="order",
            reference_id=order_id
        )

    def process_expiration(self, as_of: Optional[datetime] = None) -> int:
        """Traite l'expiration des points."""
        as_of = as_of or datetime.now()
        total_expired = 0

        for batch in self._batches.values():
            if batch.is_expired or batch.remaining_points <= 0:
                continue
            if batch.expires_at <= as_of:
                member = self._members.get(batch.member_id)
                if not member:
                    continue

                expired_points = batch.remaining_points
                batch.remaining_points = 0
                batch.is_expired = True

                member.points_balance -= expired_points
                member.points_expired_total += expired_points

                # Transaction d'expiration
                transaction = PointsTransaction(
                    transaction_id=f"pts_{uuid4().hex[:12]}",
                    tenant_id=self.tenant_id,
                    member_id=member.member_id,
                    transaction_type=PointsTransactionType.EXPIRE,
                    points=-expired_points,
                    balance_after=member.points_balance,
                    description="Expiration des points",
                    expired=True
                )
                self._transactions[transaction.transaction_id] = transaction

                total_expired += expired_points

        return total_expired

    # =========================================================================
    # Récompenses
    # =========================================================================

    def create_reward(
        self,
        name: str,
        description: str,
        reward_type: RewardType,
        points_cost: int,
        **kwargs
    ) -> Reward:
        """Crée une récompense."""
        reward_id = f"rwd_{uuid4().hex[:12]}"

        reward = Reward(
            reward_id=reward_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            reward_type=reward_type,
            points_cost=points_cost,
            status=kwargs.get("status", RewardStatus.AVAILABLE),
            value=kwargs.get("value"),
            discount_percent=kwargs.get("discount_percent"),
            discount_amount=kwargs.get("discount_amount"),
            stock_quantity=kwargs.get("stock_quantity"),
            min_tier=kwargs.get("min_tier"),
            max_per_member=kwargs.get("max_per_member"),
            valid_for_days=kwargs.get("valid_for_days", 365),
            applicable_categories=kwargs.get("applicable_categories", []),
            applicable_products=kwargs.get("applicable_products", []),
            image_url=kwargs.get("image_url"),
            category=kwargs.get("category", "general"),
            sort_order=kwargs.get("sort_order", 0),
            available_from=kwargs.get("available_from"),
            available_to=kwargs.get("available_to")
        )

        self._rewards[reward_id] = reward
        return reward

    def get_available_rewards(
        self,
        member_id: str,
        category: Optional[str] = None
    ) -> List[Reward]:
        """Liste les récompenses disponibles pour un membre."""
        member = self._members.get(member_id)
        if not member:
            return []

        available = []
        now = date.today()

        for reward in self._rewards.values():
            if reward.tenant_id != self.tenant_id:
                continue
            if reward.status != RewardStatus.AVAILABLE:
                continue
            if category and reward.category != category:
                continue

            # Vérifier le niveau minimum
            if reward.min_tier:
                tier_order = list(TierLevel)
                if tier_order.index(member.tier) < tier_order.index(reward.min_tier):
                    continue

            # Vérifier les dates
            if reward.available_from and now < reward.available_from:
                continue
            if reward.available_to and now > reward.available_to:
                continue

            # Vérifier le stock
            if reward.stock_quantity is not None:
                available_stock = reward.stock_quantity - reward.reserved_quantity
                if available_stock <= 0:
                    continue

            # Marquer si le membre peut échanger
            reward_dict = {
                "reward": reward,
                "can_redeem": member.points_balance >= reward.points_cost,
                "points_needed": max(0, reward.points_cost - member.points_balance)
            }
            available.append(reward)

        return sorted(available, key=lambda r: r.sort_order)

    def redeem_reward(
        self,
        member_id: str,
        reward_id: str,
        shipping_address: Optional[Dict[str, str]] = None
    ) -> RewardRedemption:
        """Échange une récompense."""
        member = self._members.get(member_id)
        if not member:
            raise ValueError(f"Membre {member_id} non trouvé")

        reward = self._rewards.get(reward_id)
        if not reward:
            raise ValueError(f"Récompense {reward_id} non trouvée")

        # Vérifications
        if member.points_balance < reward.points_cost:
            raise ValueError(
                f"Points insuffisants: {member.points_balance} < {reward.points_cost}"
            )

        if reward.status != RewardStatus.AVAILABLE:
            raise ValueError(f"Récompense non disponible: {reward.status}")

        if reward.stock_quantity is not None:
            available = reward.stock_quantity - reward.reserved_quantity
            if available <= 0:
                raise ValueError("Récompense en rupture de stock")

        # Déduire les points
        self._deduct_points(
            member,
            reward.points_cost,
            PointsTransactionType.REDEEM_REWARD,
            f"Échange: {reward.name}",
            reference_type="reward",
            reference_id=reward_id
        )

        # Mettre à jour le stock
        if reward.stock_quantity is not None:
            reward.reserved_quantity += 1

        # Générer un coupon si applicable
        coupon_code = None
        coupon_valid_until = None

        if reward.reward_type in (RewardType.DISCOUNT_PERCENT,
                                   RewardType.DISCOUNT_AMOUNT,
                                   RewardType.VOUCHER,
                                   RewardType.FREE_SHIPPING):
            coupon = self._generate_coupon_for_reward(member, reward)
            coupon_code = coupon.code
            coupon_valid_until = coupon.valid_until

        redemption = RewardRedemption(
            redemption_id=f"rdm_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            member_id=member_id,
            reward_id=reward_id,
            points_spent=reward.points_cost,
            reward_name=reward.name,
            reward_type=reward.reward_type,
            reward_value=reward.value,
            coupon_code=coupon_code,
            coupon_valid_until=coupon_valid_until,
            shipping_address=shipping_address
        )

        self._redemptions[redemption.redemption_id] = redemption
        return redemption

    def _generate_coupon_for_reward(
        self,
        member: Member,
        reward: Reward
    ) -> Coupon:
        """Génère un coupon pour une récompense."""
        code = f"LYL{uuid4().hex[:8].upper()}"

        discount_type = "percent"
        discount_value = Decimal("0")

        if reward.reward_type == RewardType.DISCOUNT_PERCENT:
            discount_type = "percent"
            discount_value = reward.discount_percent or Decimal("0")
        elif reward.reward_type == RewardType.DISCOUNT_AMOUNT:
            discount_type = "amount"
            discount_value = reward.discount_amount or Decimal("0")
        elif reward.reward_type == RewardType.VOUCHER:
            discount_type = "amount"
            discount_value = reward.value or Decimal("0")
        elif reward.reward_type == RewardType.FREE_SHIPPING:
            discount_type = "free_shipping"
            discount_value = Decimal("0")

        valid_until = datetime.now() + timedelta(days=reward.valid_for_days)

        coupon = Coupon(
            coupon_id=f"cpn_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            code=code,
            member_id=member.member_id,
            discount_type=discount_type,
            discount_value=discount_value,
            applicable_categories=reward.applicable_categories,
            applicable_products=reward.applicable_products,
            valid_until=valid_until,
            source_type="reward",
            source_id=reward.reward_id
        )

        self._coupons[coupon.coupon_id] = coupon
        return coupon

    def validate_coupon(
        self,
        code: str,
        member_id: Optional[str] = None,
        cart_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Valide un coupon."""
        coupon = None
        for c in self._coupons.values():
            if c.code == code and c.tenant_id == self.tenant_id:
                coupon = c
                break

        if not coupon:
            return {"valid": False, "error": "Coupon non trouvé"}

        if coupon.status != CouponStatus.ACTIVE:
            return {"valid": False, "error": f"Coupon {coupon.status.value}"}

        if coupon.valid_until and datetime.now() > coupon.valid_until:
            coupon.status = CouponStatus.EXPIRED
            return {"valid": False, "error": "Coupon expiré"}

        if coupon.member_id and coupon.member_id != member_id:
            return {"valid": False, "error": "Coupon réservé à un autre membre"}

        if coupon.current_uses >= coupon.max_uses:
            return {"valid": False, "error": "Coupon déjà utilisé"}

        if cart_amount and coupon.min_purchase:
            if cart_amount < coupon.min_purchase:
                return {
                    "valid": False,
                    "error": f"Minimum d'achat requis: {coupon.min_purchase}"
                }

        return {
            "valid": True,
            "coupon": coupon,
            "discount_type": coupon.discount_type,
            "discount_value": str(coupon.discount_value)
        }

    def use_coupon(self, code: str, order_id: str) -> Coupon:
        """Marque un coupon comme utilisé."""
        coupon = None
        for c in self._coupons.values():
            if c.code == code:
                coupon = c
                break

        if not coupon:
            raise ValueError(f"Coupon {code} non trouvé")

        coupon.current_uses += 1
        if coupon.current_uses >= coupon.max_uses:
            coupon.status = CouponStatus.USED

        return coupon

    # =========================================================================
    # Parrainages
    # =========================================================================

    def _create_referral(
        self,
        referrer: Member,
        referred: Member,
        code: str
    ) -> Referral:
        """Crée un parrainage."""
        referral = Referral(
            referral_id=f"ref_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            referrer_member_id=referrer.member_id,
            referred_member_id=referred.member_id,
            referral_code=code,
            referrer_points=self.referral_points_referrer,
            referred_points=self.referral_points_referred
        )

        self._referrals[referral.referral_id] = referral
        return referral

    def qualify_referral(
        self,
        referred_member_id: str,
        order_id: str
    ) -> Optional[Referral]:
        """Qualifie un parrainage (premier achat)."""
        # Trouver le parrainage
        referral = None
        for r in self._referrals.values():
            if r.referred_member_id == referred_member_id and not r.qualified:
                referral = r
                break

        if not referral:
            return None

        # Qualifier
        referral.qualified = True
        referral.qualified_at = datetime.now()

        # Attribuer les points
        referrer = self._members.get(referral.referrer_member_id)
        referred = self._members.get(referral.referred_member_id)

        if referrer:
            self._add_points(
                referrer,
                referral.referrer_points,
                PointsTransactionType.EARN_REFERRAL,
                f"Parrainage de {referred.email if referred else 'membre'}",
                reference_type="referral",
                reference_id=referral.referral_id
            )
            referrer.referral_count += 1

        if referred:
            self._add_points(
                referred,
                referral.referred_points,
                PointsTransactionType.EARN_REFERRAL,
                "Bonus filleul",
                reference_type="referral",
                reference_id=referral.referral_id
            )

        referral.points_awarded = True
        referral.awarded_at = datetime.now()

        return referral

    # =========================================================================
    # Gamification
    # =========================================================================

    def create_badge(
        self,
        name: str,
        description: str,
        icon: str,
        category: str,
        criteria_type: str,
        criteria_value: int,
        **kwargs
    ) -> Badge:
        """Crée un badge."""
        badge_id = f"bdg_{uuid4().hex[:12]}"

        badge = Badge(
            badge_id=badge_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            icon=icon,
            category=category,
            criteria_type=criteria_type,
            criteria_value=criteria_value,
            criteria_details=kwargs.get("criteria_details", {}),
            bonus_points=kwargs.get("bonus_points", 0),
            rarity=kwargs.get("rarity", "common"),
            is_secret=kwargs.get("is_secret", False)
        )

        self._badges[badge_id] = badge
        return badge

    def check_and_award_badges(self, member_id: str) -> List[Badge]:
        """Vérifie et attribue les badges gagnés."""
        member = self._members.get(member_id)
        if not member:
            return []

        awarded = []

        for badge in self._badges.values():
            if badge.tenant_id != self.tenant_id:
                continue
            if not badge.is_active:
                continue
            if badge.badge_id in member.badges:
                continue

            # Vérifier les critères
            earned = False

            if badge.criteria_type == "count":
                # Nombre d'actions (achats, avis, etc.)
                category = badge.criteria_details.get("category", "purchase")
                if category == "purchase":
                    txn_count = len([
                        t for t in self._transactions.values()
                        if t.member_id == member_id
                        and t.transaction_type == PointsTransactionType.EARN_PURCHASE
                    ])
                    earned = txn_count >= badge.criteria_value

            elif badge.criteria_type == "amount":
                # Montant total dépensé
                earned = member.spending_ytd >= Decimal(str(badge.criteria_value))

            elif badge.criteria_type == "streak":
                # Jours consécutifs
                earned = member.current_streak >= badge.criteria_value

            elif badge.criteria_type == "referral":
                # Nombre de parrainages
                earned = member.referral_count >= badge.criteria_value

            if earned:
                member.badges.append(badge.badge_id)
                awarded.append(badge)

                # Points bonus
                if badge.bonus_points > 0:
                    self._add_points(
                        member,
                        badge.bonus_points,
                        PointsTransactionType.EARN_BONUS,
                        f"Badge débloqué: {badge.name}"
                    )

        return awarded

    def create_challenge(
        self,
        name: str,
        description: str,
        challenge_type: ChallengeType,
        target_value: int,
        bonus_points: int,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Challenge:
        """Crée un challenge temporaire."""
        challenge_id = f"chl_{uuid4().hex[:12]}"

        challenge = Challenge(
            challenge_id=challenge_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            challenge_type=challenge_type,
            target_value=target_value,
            bonus_points=bonus_points,
            start_date=start_date,
            end_date=end_date,
            min_tier=kwargs.get("min_tier"),
            max_participants=kwargs.get("max_participants")
        )

        self._challenges[challenge_id] = challenge
        return challenge

    def update_challenge_progress(
        self,
        member_id: str,
        challenge_id: str,
        progress_increment: int
    ) -> Dict[str, Any]:
        """Met à jour la progression d'un membre sur un challenge."""
        member = self._members.get(member_id)
        challenge = self._challenges.get(challenge_id)

        if not member or not challenge:
            return {"error": "Membre ou challenge non trouvé"}

        if not challenge.is_active:
            return {"error": "Challenge inactif"}

        now = datetime.now()
        if now < challenge.start_date or now > challenge.end_date:
            return {"error": "Challenge non actif actuellement"}

        # Vérifier le niveau minimum
        if challenge.min_tier:
            tier_order = list(TierLevel)
            if tier_order.index(member.tier) < tier_order.index(challenge.min_tier):
                return {"error": "Niveau insuffisant"}

        # Mettre à jour la progression
        current = challenge.participants.get(member_id, 0)
        new_progress = current + progress_increment
        challenge.participants[member_id] = new_progress

        # Vérifier si complété
        completed = False
        if new_progress >= challenge.target_value and current < challenge.target_value:
            completed = True
            challenge.completions += 1

            # Attribuer les points bonus
            self._add_points(
                member,
                challenge.bonus_points,
                PointsTransactionType.EARN_CHALLENGE,
                f"Challenge complété: {challenge.name}",
                reference_type="challenge",
                reference_id=challenge_id
            )

        return {
            "progress": new_progress,
            "target": challenge.target_value,
            "completed": completed,
            "points_earned": challenge.bonus_points if completed else 0
        }

    # =========================================================================
    # Transferts
    # =========================================================================

    def transfer_points(
        self,
        from_member_id: str,
        to_member_id: str,
        points: int,
        reason: str = "Transfert de points"
    ) -> Tuple[PointsTransaction, PointsTransaction]:
        """Transfère des points entre membres."""
        from_member = self._members.get(from_member_id)
        to_member = self._members.get(to_member_id)

        if not from_member or not to_member:
            raise ValueError("Membre source ou destination non trouvé")

        if from_member.points_balance < points:
            raise ValueError("Solde insuffisant pour le transfert")

        # Transaction sortante
        out_txn = self._deduct_points(
            from_member,
            points,
            PointsTransactionType.TRANSFER_OUT,
            f"Transfert vers {to_member.email}: {reason}",
            reference_type="transfer",
            reference_id=to_member_id
        )

        # Transaction entrante
        in_txn = self._add_points(
            to_member,
            points,
            PointsTransactionType.TRANSFER_IN,
            f"Transfert de {from_member.email}: {reason}",
            reference_type="transfer",
            reference_id=from_member_id
        )

        return out_txn, in_txn

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_member_analytics(self, member_id: str) -> Dict[str, Any]:
        """Récupère les analytics d'un membre."""
        member = self._members.get(member_id)
        if not member:
            return {}

        transactions = [
            t for t in self._transactions.values()
            if t.member_id == member_id
        ]

        redemptions = [
            r for r in self._redemptions.values()
            if r.member_id == member_id
        ]

        tier_config = self.tier_configs.get(member.tier)
        next_tier = self._get_next_tier(member.tier)
        next_tier_config = self.tier_configs.get(next_tier) if next_tier else None

        return {
            "member_id": member_id,
            "tier": member.tier.value,
            "tier_benefits": tier_config.benefits if tier_config else [],
            "points_balance": member.points_balance,
            "points_earned_total": member.points_earned_total,
            "points_redeemed_total": member.points_redeemed_total,
            "points_expired_total": member.points_expired_total,
            "spending_ytd": str(member.spending_ytd),
            "next_tier": next_tier.value if next_tier else None,
            "points_to_next_tier": (
                next_tier_config.min_points - member.points_earned_ytd
                if next_tier_config else 0
            ),
            "badges_count": len(member.badges),
            "referral_count": member.referral_count,
            "redemptions_count": len(redemptions),
            "member_since": member.enrolled_at.isoformat(),
            "days_as_member": (datetime.now() - member.enrolled_at).days
        }

    def _get_next_tier(self, current: TierLevel) -> Optional[TierLevel]:
        """Récupère le niveau suivant."""
        tier_order = list(TierLevel)
        current_idx = tier_order.index(current)
        if current_idx < len(tier_order) - 1:
            return tier_order[current_idx + 1]
        return None

    def get_program_stats(self) -> Dict[str, Any]:
        """Statistiques globales du programme."""
        members = [m for m in self._members.values()
                  if m.tenant_id == self.tenant_id]

        transactions = [t for t in self._transactions.values()
                       if t.tenant_id == self.tenant_id]

        redemptions = [r for r in self._redemptions.values()
                      if r.tenant_id == self.tenant_id]

        # Distribution par niveau
        tier_distribution = {}
        for tier in TierLevel:
            tier_distribution[tier.value] = len([
                m for m in members if m.tier == tier
            ])

        return {
            "total_members": len(members),
            "active_members": len([m for m in members if m.is_active]),
            "total_points_issued": sum(m.points_earned_total for m in members),
            "total_points_redeemed": sum(m.points_redeemed_total for m in members),
            "total_points_outstanding": sum(m.points_balance for m in members),
            "total_redemptions": len(redemptions),
            "tier_distribution": tier_distribution,
            "avg_points_per_member": (
                sum(m.points_balance for m in members) / len(members)
                if members else 0
            ),
            "redemption_rate": (
                len(redemptions) / len(members) * 100 if members else 0
            )
        }


def create_loyalty_service(
    tenant_id: str,
    **kwargs
) -> LoyaltyService:
    """Factory pour créer un service de fidélité."""
    return LoyaltyService(tenant_id=tenant_id, **kwargs)
