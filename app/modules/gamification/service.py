"""
AZALS MODULE GAMIFICATION - Service
====================================

Service metier pour le systeme de gamification complet.

Fonctionnalites:
- Gestion des points (XP, coins, karma)
- Systeme de niveaux avec progression
- Badges et achievements
- Defis quotidiens/hebdomadaires/mensuels
- Classements (leaderboards)
- Recompenses et boutique
- Streaks et habitudes
- Regles d'attribution automatique
- Equipes et competitions
- Notifications

Inspire de: Salesforce Trailhead, Microsoft Dynamics 365 Gamification, SAP SuccessFactors
"""
from __future__ import annotations


import random
import string
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
import uuid

from sqlalchemy.orm import Session

from .models import (
    PointType,
    TransactionType,
    BadgeStatus,
    BadgeRarity,
    ChallengeStatus,
    ChallengeType,
    RewardStatus,
    CompetitionStatus,
    LeaderboardPeriod,
    NotificationType,
    RuleEventType,
)
from .repository import (
    LevelRepository,
    UserProfileRepository,
    PointTransactionRepository,
    BadgeCategoryRepository,
    BadgeRepository,
    UserBadgeRepository,
    ChallengeRepository,
    UserChallengeRepository,
    RewardRepository,
    RewardClaimRepository,
    RuleRepository,
    RuleTriggerLogRepository,
    TeamRepository,
    TeamMembershipRepository,
    CompetitionRepository,
    CompetitionParticipantRepository,
    LeaderboardRepository,
    LeaderboardEntryRepository,
    NotificationRepository,
    ActivityRepository,
    StreakRepository,
    ConfigRepository,
)
from .schemas import (
    UserProfileResponse,
    UserProfileSummary,
    PointTransactionResponse,
    PointTransactionFilters,
    BadgeFilters,
    UserBadgeResponse,
    ChallengeFilters,
    UserChallengeResponse,
    RewardFilters,
    RewardClaimResponse,
    LeaderboardEntryResponse,
    LeaderboardWithEntries,
    GamificationDashboard,
    GamificationStats,
    UserGamificationStats,
    ActivityFilters,
)
from .exceptions import (
    ProfileNotFoundError,
    InsufficientPointsError,
    BadgeNotFoundError,
    BadgeAlreadyUnlockedError,
    BadgeNotAvailableError,
    BadgeLimitReachedError,
    ChallengeNotFoundError,
    ChallengeNotActiveError,
    ChallengeFullError,
    AlreadyJoinedChallengeError,
    ChallengeNotJoinedError,
    RewardsAlreadyClaimedError,
    ChallengeNotCompletedError,
    RewardNotFoundError,
    RewardNotAvailableError,
    RewardOutOfStockError,
    RewardLimitReachedError,
    LevelRequirementNotMetError,
    RuleNotFoundError,
    RuleCooldownError,
    TeamNotFoundError,
    TeamFullError,
    AlreadyInTeamError,
    NotTeamMemberError,
    CompetitionNotFoundError,
    AlreadyRegisteredError,
    DailyPointLimitExceededError,
    FeatureDisabledError,
    DuplicateCodeError,
)


class GamificationService:
    """
    Service principal de gamification.

    Gere toute la logique metier du systeme de gamification.
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

        # Initialiser les repositories
        self.levels = LevelRepository(db, tenant_id)
        self.profiles = UserProfileRepository(db, tenant_id)
        self.transactions = PointTransactionRepository(db, tenant_id)
        self.badge_categories = BadgeCategoryRepository(db, tenant_id)
        self.badges = BadgeRepository(db, tenant_id)
        self.user_badges = UserBadgeRepository(db, tenant_id)
        self.challenges = ChallengeRepository(db, tenant_id)
        self.user_challenges = UserChallengeRepository(db, tenant_id)
        self.rewards = RewardRepository(db, tenant_id)
        self.reward_claims = RewardClaimRepository(db, tenant_id)
        self.rules = RuleRepository(db, tenant_id)
        self.rule_logs = RuleTriggerLogRepository(db, tenant_id)
        self.teams = TeamRepository(db, tenant_id)
        self.team_memberships = TeamMembershipRepository(db, tenant_id)
        self.competitions = CompetitionRepository(db, tenant_id)
        self.competition_participants = CompetitionParticipantRepository(db, tenant_id)
        self.leaderboards = LeaderboardRepository(db, tenant_id)
        self.leaderboard_entries = LeaderboardEntryRepository(db, tenant_id)
        self.notifications = NotificationRepository(db, tenant_id)
        self.activities = ActivityRepository(db, tenant_id)
        self.streaks = StreakRepository(db, tenant_id)
        self.config_repo = ConfigRepository(db, tenant_id)

        # Charger la configuration
        self._config = None

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def get_config(self):
        """Recupere ou cree la configuration du tenant."""
        if self._config is None:
            self._config, _ = self.config_repo.get_or_create()
        return self._config

    def update_config(self, data: dict[str, Any]):
        """Met a jour la configuration."""
        config = self.get_config()
        self._config = self.config_repo.update(config, data)
        return self._config

    def _check_feature_enabled(self, feature: str) -> None:
        """Verifie qu'une fonctionnalite est activee."""
        config = self.get_config()
        feature_map = {
            "points": config.points_enabled,
            "badges": config.badges_enabled,
            "challenges": config.challenges_enabled,
            "leaderboards": config.leaderboards_enabled,
            "rewards": config.rewards_enabled,
            "teams": config.teams_enabled,
            "competitions": config.competitions_enabled,
        }
        if not feature_map.get(feature, True):
            raise FeatureDisabledError(feature)

    # =========================================================================
    # PROFILS UTILISATEUR
    # =========================================================================

    def get_or_create_profile(self, user_id: UUID):
        """Recupere ou cree le profil de gamification d'un utilisateur."""
        profile, created = self.profiles.get_or_create(user_id)
        if created:
            # Initialiser les niveaux par defaut si necessaire
            self._ensure_default_levels()
            # Logger l'activite
            self._log_activity(
                user_id=user_id,
                activity_type="profile_created",
                description="Profil de gamification cree"
            )
        return profile

    def get_profile(self, user_id: UUID):
        """Recupere le profil d'un utilisateur."""
        profile = self.profiles.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(str(user_id))
        return profile

    def get_profile_summary(self, user_id: UUID) -> UserProfileSummary:
        """Recupere un resume du profil utilisateur."""
        profile = self.get_profile(user_id)
        level = self.levels.get_by_number(profile.current_level)
        next_level = self.levels.get_by_number(profile.current_level + 1)

        xp_to_next = 0
        progress = Decimal("100.0")
        if level and next_level:
            level_xp = profile.current_xp - level.min_xp
            xp_needed = next_level.min_xp - level.min_xp
            xp_to_next = xp_needed - level_xp
            progress = (Decimal(level_xp) / Decimal(xp_needed) * 100).quantize(Decimal("0.01"))

        return UserProfileSummary(
            user_id=user_id,
            level=profile.current_level,
            xp=profile.current_xp,
            xp_to_next_level=xp_to_next,
            level_progress_percent=progress,
            badges_count=profile.badges_unlocked,
            title=profile.title,
            avatar_url=profile.avatar_url
        )

    def update_profile(self, user_id: UUID, data: dict[str, Any]):
        """Met a jour le profil d'un utilisateur."""
        profile = self.get_profile(user_id)
        return self.profiles.update(profile, data)

    # =========================================================================
    # POINTS
    # =========================================================================

    def award_points(
        self,
        user_id: UUID,
        amount: int,
        point_type: PointType = PointType.XP,
        description: str = "",
        source: str | None = None,
        source_id: UUID | None = None,
        apply_multiplier: bool = True,
        expires_at: datetime | None = None,
        created_by: UUID | None = None
    ):
        """Attribue des points a un utilisateur."""
        self._check_feature_enabled("points")

        if amount <= 0:
            raise ValueError("Le montant doit etre positif")

        profile = self.get_or_create_profile(user_id)
        config = self.get_config()

        # Verifier limite journaliere
        if config.max_points_per_day:
            daily_total = self.transactions.get_daily_total(user_id, point_type)
            if daily_total + amount > config.max_points_per_day:
                raise DailyPointLimitExceededError(config.max_points_per_day, daily_total)

        # Appliquer multiplicateur
        base_amount = amount
        multiplier = Decimal("1.0")
        if apply_multiplier:
            level = self.levels.get_by_number(profile.current_level)
            if level and level.multiplier:
                multiplier = level.multiplier
            multiplier *= config.default_xp_multiplier

        final_amount = int(Decimal(amount) * multiplier)

        # Mettre a jour le solde
        balance_after = 0
        if point_type == PointType.XP:
            profile.current_xp += final_amount
            profile.lifetime_xp += final_amount
            balance_after = profile.current_xp
        elif point_type == PointType.COINS:
            profile.coins_balance += final_amount
            profile.lifetime_coins_earned += final_amount
            balance_after = profile.coins_balance
        elif point_type == PointType.KARMA:
            profile.karma_balance += final_amount
            balance_after = profile.karma_balance
        elif point_type == PointType.CREDITS:
            profile.credits_balance += final_amount
            balance_after = profile.credits_balance

        # Creer la transaction
        transaction = self.transactions.create({
            "user_id": user_id,
            "point_type": point_type,
            "transaction_type": TransactionType.EARN,
            "amount": final_amount,
            "balance_after": balance_after,
            "description": description,
            "source": source,
            "source_id": source_id,
            "multiplier": multiplier,
            "base_amount": base_amount,
            "expires_at": expires_at
        }, created_by)

        # Mettre a jour le profil
        self.profiles.update(profile, {})

        # Verifier niveau
        if point_type == PointType.XP:
            self._check_level_up(user_id, profile)

        # Logger l'activite
        self._log_activity(
            user_id=user_id,
            activity_type="points_earned",
            description=f"+{final_amount} {point_type.value}",
            details={"amount": final_amount, "point_type": point_type.value, "source": source},
            points_delta=final_amount if point_type != PointType.XP else 0,
            xp_delta=final_amount if point_type == PointType.XP else 0
        )

        # Verifier badges lies aux points
        self._check_point_badges(user_id, point_type, profile)

        return transaction

    def spend_points(
        self,
        user_id: UUID,
        amount: int,
        point_type: PointType = PointType.COINS,
        description: str = "",
        reference_type: str | None = None,
        reference_id: UUID | None = None
    ):
        """Depense des points."""
        self._check_feature_enabled("points")

        if amount <= 0:
            raise ValueError("Le montant doit etre positif")

        profile = self.get_profile(user_id)

        # Verifier le solde
        balance = 0
        if point_type == PointType.COINS:
            balance = profile.coins_balance
        elif point_type == PointType.KARMA:
            balance = profile.karma_balance
        elif point_type == PointType.CREDITS:
            balance = profile.credits_balance
        elif point_type == PointType.XP:
            raise ValueError("XP ne peut pas etre depense")

        if balance < amount:
            raise InsufficientPointsError(amount, balance, point_type.value)

        # Mettre a jour le solde
        balance_after = balance - amount
        if point_type == PointType.COINS:
            profile.coins_balance = balance_after
            profile.lifetime_coins_spent += amount
        elif point_type == PointType.KARMA:
            profile.karma_balance = balance_after
        elif point_type == PointType.CREDITS:
            profile.credits_balance = balance_after

        # Creer la transaction
        transaction = self.transactions.create({
            "user_id": user_id,
            "point_type": point_type,
            "transaction_type": TransactionType.SPEND,
            "amount": -amount,
            "balance_after": balance_after,
            "description": description,
            "reference_type": reference_type,
            "reference_id": reference_id
        })

        self.profiles.update(profile, {})

        return transaction

    def transfer_points(
        self,
        from_user_id: UUID,
        to_user_id: UUID,
        amount: int,
        point_type: PointType = PointType.COINS,
        message: str | None = None
    ):
        """Transfere des points entre utilisateurs."""
        self._check_feature_enabled("points")

        if from_user_id == to_user_id:
            raise ValueError("Impossible de transferer des points a soi-meme")

        # Depenser de l'expediteur
        self.spend_points(
            from_user_id,
            amount,
            point_type,
            f"Transfert vers utilisateur {to_user_id}",
            "transfer",
            to_user_id
        )

        # Crediter le destinataire
        return self.award_points(
            to_user_id,
            amount,
            point_type,
            f"Transfert de utilisateur {from_user_id}" + (f": {message}" if message else ""),
            "transfer",
            from_user_id,
            apply_multiplier=False
        )

    def get_point_balance(self, user_id: UUID, point_type: PointType) -> int:
        """Recupere le solde de points d'un type."""
        profile = self.get_profile(user_id)
        if point_type == PointType.XP:
            return profile.current_xp
        elif point_type == PointType.COINS:
            return profile.coins_balance
        elif point_type == PointType.KARMA:
            return profile.karma_balance
        elif point_type == PointType.CREDITS:
            return profile.credits_balance
        return 0

    def get_transactions(
        self,
        user_id: UUID,
        filters: PointTransactionFilters | None = None,
        page: int = 1,
        page_size: int = 50
    ):
        """Recupere l'historique des transactions."""
        return self.transactions.get_by_user(user_id, filters, page, page_size)

    # =========================================================================
    # NIVEAUX
    # =========================================================================

    def _ensure_default_levels(self):
        """Cree les niveaux par defaut si necessaire."""
        existing = self.levels.get_all()
        if existing:
            return

        default_levels = [
            {"level_number": 1, "name": "Debutant", "min_xp": 0, "max_xp": 100, "color": "#64748b"},
            {"level_number": 2, "name": "Apprenti", "min_xp": 100, "max_xp": 300, "color": "#22c55e"},
            {"level_number": 3, "name": "Confirme", "min_xp": 300, "max_xp": 600, "color": "#3b82f6"},
            {"level_number": 4, "name": "Expert", "min_xp": 600, "max_xp": 1000, "color": "#a855f7"},
            {"level_number": 5, "name": "Maitre", "min_xp": 1000, "max_xp": 1500, "color": "#f59e0b"},
            {"level_number": 6, "name": "Grand Maitre", "min_xp": 1500, "max_xp": 2500, "color": "#ef4444"},
            {"level_number": 7, "name": "Legende", "min_xp": 2500, "max_xp": 4000, "color": "#ec4899"},
            {"level_number": 8, "name": "Mythique", "min_xp": 4000, "max_xp": 6000, "color": "#8b5cf6"},
            {"level_number": 9, "name": "Divin", "min_xp": 6000, "max_xp": 10000, "color": "#06b6d4"},
            {"level_number": 10, "name": "Transcendant", "min_xp": 10000, "max_xp": None, "color": "#ffd700", "multiplier": Decimal("1.5")},
        ]

        for level_data in default_levels:
            self.levels.create(level_data)

    def _check_level_up(self, user_id: UUID, profile):
        """Verifie et applique un level up si necessaire."""
        new_level = self.levels.get_level_for_xp(profile.current_xp)
        if not new_level:
            return

        if new_level.level_number > profile.current_level:
            old_level = profile.current_level
            profile.current_level = new_level.level_number
            profile.level_up_date = datetime.utcnow()
            self.profiles.update(profile, {})

            # Notification
            self._create_notification(
                user_id=user_id,
                notification_type=NotificationType.LEVEL_UP,
                title=f"Niveau {new_level.level_number} atteint!",
                message=f"Felicitations! Vous etes maintenant {new_level.name}",
                data={"level": new_level.level_number, "level_name": new_level.name}
            )

            # Logger
            self._log_activity(
                user_id=user_id,
                activity_type="level_up",
                description=f"Niveau {new_level.level_number} atteint: {new_level.name}",
                details={"old_level": old_level, "new_level": new_level.level_number}
            )

            # Debloquer badge du niveau si defini
            if new_level.badge_id:
                try:
                    self.unlock_badge(user_id, new_level.badge_id, auto=True)
                except BadgeAlreadyUnlockedError:
                    pass

    def get_level_info(self, level_number: int):
        """Recupere les informations d'un niveau."""
        return self.levels.get_by_number(level_number)

    def get_all_levels(self):
        """Recupere tous les niveaux."""
        return self.levels.get_all()

    # =========================================================================
    # BADGES
    # =========================================================================

    def create_badge(self, data: dict[str, Any], created_by: UUID | None = None):
        """Cree un nouveau badge."""
        self._check_feature_enabled("badges")

        if self.badges.code_exists(data.get("code", "")):
            raise DuplicateCodeError("badge", data.get("code", ""))

        return self.badges.create(data, created_by)

    def get_badge(self, badge_id: UUID):
        """Recupere un badge."""
        badge = self.badges.get_by_id(badge_id)
        if not badge:
            raise BadgeNotFoundError(str(badge_id))
        return badge

    def list_badges(
        self,
        filters: BadgeFilters | None = None,
        page: int = 1,
        page_size: int = 50
    ):
        """Liste les badges."""
        self._check_feature_enabled("badges")
        return self.badges.list(filters, page, page_size)

    def get_user_badges(self, user_id: UUID, status: BadgeStatus | None = None):
        """Recupere les badges d'un utilisateur."""
        return self.user_badges.get_by_user(user_id, status)

    def unlock_badge(
        self,
        user_id: UUID,
        badge_id: UUID,
        auto: bool = False,
        context: dict[str, Any] | None = None
    ):
        """Debloque un badge pour un utilisateur."""
        self._check_feature_enabled("badges")

        badge = self.get_badge(badge_id)
        now = datetime.utcnow()

        # Verifier disponibilite
        if not badge.is_active:
            raise BadgeNotAvailableError(str(badge_id), "Badge inactif")
        if badge.available_from and badge.available_from > now:
            raise BadgeNotAvailableError(str(badge_id), "Badge pas encore disponible")
        if badge.available_until and badge.available_until < now:
            raise BadgeNotAvailableError(str(badge_id), "Badge expire")

        # Verifier limite de detenteurs
        if badge.max_holders and badge.current_holders >= badge.max_holders:
            raise BadgeLimitReachedError(str(badge_id), badge.max_holders)

        # Verifier si deja debloque
        existing = self.user_badges.get_by_user_and_badge(user_id, badge_id)
        if existing:
            if existing.status == BadgeStatus.UNLOCKED:
                if badge.is_stackable:
                    existing.times_earned += 1
                    self.user_badges.update(existing, {"times_earned": existing.times_earned})
                else:
                    raise BadgeAlreadyUnlockedError(str(badge_id), str(user_id))
            else:
                # Mettre a jour vers unlocked
                self.user_badges.update(existing, {
                    "status": BadgeStatus.UNLOCKED,
                    "progress": badge.progress_max,
                    "unlocked_at": now,
                    "unlock_context": context or {}
                })
                existing = self.user_badges.get_by_id(existing.id)
        else:
            # Creer nouveau user_badge
            existing = self.user_badges.create({
                "user_id": user_id,
                "badge_id": badge_id,
                "status": BadgeStatus.UNLOCKED,
                "progress": badge.progress_max,
                "progress_max": badge.progress_max,
                "unlocked_at": now,
                "unlock_context": context or {}
            })

        # Incrementer le compteur du badge
        self.badges.increment_holders(badge_id)

        # Mettre a jour le profil
        profile = self.get_profile(user_id)
        profile.badges_unlocked = self.user_badges.count_by_user(user_id, BadgeStatus.UNLOCKED)
        self.profiles.update(profile, {})

        # Attribuer points de recompense
        if badge.points_reward > 0:
            self.award_points(
                user_id,
                badge.points_reward,
                badge.points_type,
                f"Badge debloque: {badge.name}",
                "badge",
                badge_id,
                apply_multiplier=False
            )

        # Notification
        config = self.get_config()
        if config.notify_badge_unlock:
            self._create_notification(
                user_id=user_id,
                notification_type=NotificationType.BADGE_UNLOCKED,
                title=f"Badge debloque: {badge.name}",
                message=badge.description,
                icon=badge.icon,
                reference_type="badge",
                reference_id=badge_id,
                data={"badge_id": str(badge_id), "rarity": badge.rarity.value}
            )

        # Logger
        self._log_activity(
            user_id=user_id,
            activity_type="badge_unlocked",
            description=f"Badge debloque: {badge.name}",
            details={"badge_id": str(badge_id), "badge_name": badge.name, "rarity": badge.rarity.value}
        )

        # Mettre a jour equipe si applicable
        if profile.team_id:
            self.teams.update_stats(profile.team_id, badges_delta=1)

        return existing

    def update_badge_progress(
        self,
        user_id: UUID,
        badge_id: UUID,
        progress: int,
        increment: bool = False
    ):
        """Met a jour la progression d'un badge."""
        badge = self.get_badge(badge_id)
        existing = self.user_badges.get_by_user_and_badge(user_id, badge_id)

        if existing and existing.status == BadgeStatus.UNLOCKED:
            return existing  # Deja debloque

        current_progress = existing.progress if existing else 0
        new_progress = current_progress + progress if increment else progress
        new_progress = min(new_progress, badge.progress_max)

        if not existing:
            existing = self.user_badges.create({
                "user_id": user_id,
                "badge_id": badge_id,
                "status": BadgeStatus.IN_PROGRESS,
                "progress": new_progress,
                "progress_max": badge.progress_max,
                "started_at": datetime.utcnow()
            })
        else:
            self.user_badges.update(existing, {
                "progress": new_progress,
                "status": BadgeStatus.IN_PROGRESS if new_progress < badge.progress_max else BadgeStatus.UNLOCKED
            })

        # Auto-unlock si progression complete
        if new_progress >= badge.progress_max:
            return self.unlock_badge(user_id, badge_id, auto=True)

        return self.user_badges.get_by_id(existing.id)

    def _check_point_badges(self, user_id: UUID, point_type: PointType, profile):
        """Verifie les badges lies a l'accumulation de points."""
        # Recuperer badges avec critere de points
        badges, _ = self.badges.list(BadgeFilters(only_available=True), page_size=1000)

        for badge in badges:
            if not badge.criteria:
                continue

            criteria = badge.criteria
            if criteria.get("type") != "points_threshold":
                continue
            if criteria.get("point_type") != point_type.value:
                continue

            threshold = criteria.get("threshold", 0)
            current = profile.lifetime_xp if point_type == PointType.XP else profile.lifetime_coins_earned

            if current >= threshold:
                try:
                    self.unlock_badge(user_id, badge.id, auto=True)
                except (BadgeAlreadyUnlockedError, BadgeNotAvailableError):
                    pass

    # =========================================================================
    # DEFIS
    # =========================================================================

    def create_challenge(self, data: dict[str, Any], created_by: UUID | None = None):
        """Cree un nouveau defi."""
        self._check_feature_enabled("challenges")

        if self.challenges.code_exists(data.get("code", "")):
            raise DuplicateCodeError("defi", data.get("code", ""))

        return self.challenges.create(data, created_by)

    def get_challenge(self, challenge_id: UUID):
        """Recupere un defi."""
        challenge = self.challenges.get_by_id(challenge_id)
        if not challenge:
            raise ChallengeNotFoundError(str(challenge_id))
        return challenge

    def list_challenges(
        self,
        filters: ChallengeFilters | None = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Liste les defis."""
        self._check_feature_enabled("challenges")
        return self.challenges.list(filters, page, page_size)

    def join_challenge(self, user_id: UUID, challenge_id: UUID, team_id: UUID | None = None):
        """Rejoint un defi."""
        self._check_feature_enabled("challenges")

        challenge = self.get_challenge(challenge_id)
        now = datetime.utcnow()

        # Verifications
        if challenge.status not in [ChallengeStatus.ACTIVE, ChallengeStatus.SCHEDULED]:
            raise ChallengeNotActiveError(str(challenge_id), challenge.status.value)

        if challenge.registration_deadline and challenge.registration_deadline < now:
            raise ChallengeNotActiveError(str(challenge_id), "Inscriptions fermees")

        if challenge.max_participants and challenge.current_participants >= challenge.max_participants:
            raise ChallengeFullError(str(challenge_id), challenge.max_participants)

        # Verifier si deja inscrit
        existing = self.user_challenges.get_by_user_and_challenge(user_id, challenge_id)
        if existing:
            raise AlreadyJoinedChallengeError(str(challenge_id), str(user_id))

        # Creer la participation
        user_challenge = self.user_challenges.create({
            "user_id": user_id,
            "challenge_id": challenge_id,
            "status": ChallengeStatus.ACTIVE,
            "target": challenge.target_value,
            "team_id": team_id
        })

        # Mettre a jour le compteur
        self.challenges.increment_participants(challenge_id)

        # Logger
        self._log_activity(
            user_id=user_id,
            activity_type="challenge_joined",
            description=f"Defi rejoint: {challenge.name}",
            details={"challenge_id": str(challenge_id)}
        )

        return user_challenge

    def update_challenge_progress(
        self,
        user_id: UUID,
        challenge_id: UUID,
        progress: int,
        increment: bool = True,
        context: dict[str, Any] | None = None
    ):
        """Met a jour la progression d'un defi."""
        user_challenge = self.user_challenges.get_by_user_and_challenge(user_id, challenge_id)
        if not user_challenge:
            raise ChallengeNotJoinedError(str(challenge_id), str(user_id))

        if user_challenge.status != ChallengeStatus.ACTIVE:
            return user_challenge

        challenge = self.get_challenge(challenge_id)

        new_progress = user_challenge.progress + progress if increment else progress
        new_progress = min(new_progress, user_challenge.target)
        progress_percent = Decimal(new_progress) / Decimal(user_challenge.target) * 100

        # Ajouter a l'historique
        history = list(user_challenge.progress_history or [])
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "progress": new_progress,
            "delta": progress if increment else new_progress - user_challenge.progress,
            "context": context
        })

        update_data = {
            "progress": new_progress,
            "progress_percent": progress_percent.quantize(Decimal("0.01")),
            "progress_history": history
        }

        # Completion automatique
        if new_progress >= user_challenge.target:
            update_data["status"] = ChallengeStatus.COMPLETED
            update_data["completed_at"] = datetime.utcnow()

            # Notification
            config = self.get_config()
            if config.notify_challenge_complete:
                self._create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.CHALLENGE_COMPLETED,
                    title=f"Defi termine: {challenge.name}",
                    message="Reclamez vos recompenses!",
                    reference_type="challenge",
                    reference_id=challenge_id
                )

            # Logger
            self._log_activity(
                user_id=user_id,
                activity_type="challenge_completed",
                description=f"Defi termine: {challenge.name}",
                details={"challenge_id": str(challenge_id)}
            )

        return self.user_challenges.update(user_challenge, update_data)

    def claim_challenge_rewards(self, user_id: UUID, challenge_id: UUID):
        """Reclame les recompenses d'un defi termine."""
        user_challenge = self.user_challenges.get_by_user_and_challenge(user_id, challenge_id)
        if not user_challenge:
            raise ChallengeNotJoinedError(str(challenge_id), str(user_id))

        if user_challenge.status != ChallengeStatus.COMPLETED:
            raise ChallengeNotCompletedError(
                str(challenge_id),
                user_challenge.progress,
                user_challenge.target
            )

        if user_challenge.rewards_claimed:
            raise RewardsAlreadyClaimedError(str(challenge_id))

        challenge = self.get_challenge(challenge_id)
        rewards_data = []

        # Attribuer les recompenses
        for reward in (challenge.rewards or []):
            reward_type = reward.get("type")
            value = reward.get("value", 0)

            if reward_type == "xp":
                self.award_points(user_id, value, PointType.XP, f"Defi: {challenge.name}", "challenge", challenge_id)
                rewards_data.append({"type": "xp", "amount": value})
            elif reward_type == "coins":
                self.award_points(user_id, value, PointType.COINS, f"Defi: {challenge.name}", "challenge", challenge_id)
                rewards_data.append({"type": "coins", "amount": value})
            elif reward_type == "badge":
                try:
                    self.unlock_badge(user_id, UUID(value), auto=True)
                    rewards_data.append({"type": "badge", "badge_id": value})
                except (BadgeAlreadyUnlockedError, BadgeNotFoundError):
                    pass

        # Mettre a jour
        self.user_challenges.update(user_challenge, {
            "rewards_claimed": True,
            "claimed_at": datetime.utcnow(),
            "rewards_data": rewards_data
        })

        # Mettre a jour profil
        profile = self.get_profile(user_id)
        profile.challenges_completed += 1
        self.profiles.update(profile, {})

        return rewards_data

    def get_user_challenges(
        self,
        user_id: UUID,
        status: ChallengeStatus | None = None
    ):
        """Recupere les defis d'un utilisateur."""
        return self.user_challenges.get_by_user(user_id, status)

    # =========================================================================
    # RECOMPENSES
    # =========================================================================

    def create_reward(self, data: dict[str, Any], created_by: UUID | None = None):
        """Cree une nouvelle recompense."""
        self._check_feature_enabled("rewards")

        if self.rewards.code_exists(data.get("code", "")):
            raise DuplicateCodeError("recompense", data.get("code", ""))

        return self.rewards.create(data, created_by)

    def get_reward(self, reward_id: UUID):
        """Recupere une recompense."""
        reward = self.rewards.get_by_id(reward_id)
        if not reward:
            raise RewardNotFoundError(str(reward_id))
        return reward

    def list_rewards(
        self,
        filters: RewardFilters | None = None,
        user_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Liste les recompenses."""
        self._check_feature_enabled("rewards")

        user_coins = None
        if user_id and filters and filters.affordable:
            profile = self.get_profile(user_id)
            user_coins = profile.coins_balance

        return self.rewards.list(filters, user_coins, page, page_size)

    def claim_reward(
        self,
        user_id: UUID,
        reward_id: UUID,
        shipping_address: dict[str, Any] | None = None,
        user_notes: str | None = None
    ):
        """Reclame une recompense."""
        self._check_feature_enabled("rewards")

        reward = self.get_reward(reward_id)
        profile = self.get_profile(user_id)
        now = datetime.utcnow()

        # Verifications
        if not reward.is_active:
            raise RewardNotAvailableError(str(reward_id), "Recompense inactive")
        if reward.available_from and reward.available_from > now:
            raise RewardNotAvailableError(str(reward_id), "Pas encore disponible")
        if reward.available_until and reward.available_until < now:
            raise RewardNotAvailableError(str(reward_id), "Expiree")
        if reward.stock is not None and reward.claimed_count >= reward.stock:
            raise RewardOutOfStockError(str(reward_id))
        if reward.min_level_required and profile.current_level < reward.min_level_required:
            raise LevelRequirementNotMetError(reward.min_level_required, profile.current_level)

        # Verifier limite par utilisateur
        if reward.limit_per_user:
            user_claims = self.reward_claims.count_user_claims_for_reward(user_id, reward_id)
            if user_claims >= reward.limit_per_user:
                raise RewardLimitReachedError(str(reward_id), "par utilisateur", reward.limit_per_user)

        # Verifier limite journaliere
        if reward.limit_per_day:
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_claims = self.reward_claims.count_user_claims_for_reward(user_id, reward_id, today_start)
            if today_claims >= reward.limit_per_day:
                raise RewardLimitReachedError(str(reward_id), "journaliere", reward.limit_per_day)

        # Depenser les points
        transaction = None
        if reward.cost_points > 0:
            transaction = self.spend_points(
                user_id,
                reward.cost_points,
                reward.cost_type,
                f"Recompense: {reward.name}",
                "reward",
                reward_id
            )

        # Creer la reclamation
        claim_code = self._generate_claim_code()
        claim = self.reward_claims.create({
            "user_id": user_id,
            "reward_id": reward_id,
            "transaction_id": transaction.id if transaction else None,
            "points_spent": reward.cost_points,
            "status": RewardStatus.PENDING,
            "claim_code": claim_code,
            "shipping_address": shipping_address,
            "user_notes": user_notes
        })

        # Incrementer le compteur
        self.rewards.increment_claimed(reward_id)

        # Mettre a jour profil
        profile.rewards_claimed += 1
        self.profiles.update(profile, {})

        # Traitement immediat pour certains types
        if reward.reward_type.value == "badge":
            badge_id = reward.value.get("badge_id") if reward.value else None
            if badge_id:
                try:
                    self.unlock_badge(user_id, UUID(badge_id), auto=True)
                    self.reward_claims.update(claim, {
                        "status": RewardStatus.FULFILLED,
                        "fulfilled_at": datetime.utcnow()
                    })
                except BadgeAlreadyUnlockedError:
                    pass
        elif reward.reward_type.value == "points":
            point_type = PointType(reward.value.get("point_type", "xp"))
            amount = reward.value.get("amount", 0)
            self.award_points(user_id, amount, point_type, f"Recompense: {reward.name}", "reward_claim", claim.id)
            self.reward_claims.update(claim, {
                "status": RewardStatus.FULFILLED,
                "fulfilled_at": datetime.utcnow()
            })

        # Logger
        self._log_activity(
            user_id=user_id,
            activity_type="reward_claimed",
            description=f"Recompense reclamee: {reward.name}",
            details={"reward_id": str(reward_id), "cost": reward.cost_points}
        )

        return self.reward_claims.get_by_id(claim.id)

    def get_user_claims(self, user_id: UUID, status: RewardStatus | None = None):
        """Recupere les reclamations d'un utilisateur."""
        return self.reward_claims.get_by_user(user_id, status)

    def update_claim_status(
        self,
        claim_id: UUID,
        status: RewardStatus,
        tracking_number: str | None = None,
        admin_notes: str | None = None,
        processed_by: UUID | None = None
    ):
        """Met a jour le statut d'une reclamation."""
        claim = self.reward_claims.get_by_id(claim_id)
        if not claim:
            raise RewardNotFoundError(str(claim_id))

        update_data = {"status": status}
        if tracking_number:
            update_data["tracking_number"] = tracking_number
        if admin_notes:
            update_data["admin_notes"] = admin_notes
        if status == RewardStatus.PROCESSING:
            update_data["processed_at"] = datetime.utcnow()
            update_data["processed_by"] = processed_by
        elif status == RewardStatus.FULFILLED:
            update_data["fulfilled_at"] = datetime.utcnow()

        return self.reward_claims.update(claim, update_data)

    # =========================================================================
    # REGLES D'ATTRIBUTION
    # =========================================================================

    def create_rule(self, data: dict[str, Any], created_by: UUID | None = None):
        """Cree une nouvelle regle."""
        if self.rules.code_exists(data.get("code", "")):
            raise DuplicateCodeError("regle", data.get("code", ""))

        return self.rules.create(data, created_by)

    def trigger_event(
        self,
        event_type: RuleEventType,
        user_id: UUID,
        event_data: dict[str, Any] | None = None,
        source: str | None = None
    ):
        """Declenche un evenement et execute les regles correspondantes."""
        rules = self.rules.get_active_for_event(event_type.value, source)
        results = []

        for rule in rules:
            try:
                result = self._execute_rule(rule, user_id, event_data or {})
                if result:
                    results.append(result)
            except Exception as e:
                # Logger l'erreur mais continuer
                self.rule_logs.create({
                    "rule_id": rule.id,
                    "user_id": user_id,
                    "event_data": event_data,
                    "success": False,
                    "error_message": str(e)
                })

        return results

    def _execute_rule(
        self,
        rule,
        user_id: UUID,
        event_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Execute une regle pour un utilisateur."""
        now = datetime.utcnow()

        # Verifier cooldown
        if rule.cooldown_minutes:
            last_trigger = self.rule_logs.get_last_trigger(user_id, rule.id)
            if last_trigger:
                cooldown_end = last_trigger.triggered_at + timedelta(minutes=rule.cooldown_minutes)
                if now < cooldown_end:
                    remaining = int((cooldown_end - now).total_seconds() / 60)
                    raise RuleCooldownError(str(rule.id), remaining)

        # Verifier limite journaliere
        if rule.max_triggers_per_day:
            today_count = self.rule_logs.count_triggers_today(user_id, rule.id)
            if today_count >= rule.max_triggers_per_day:
                return None

        # Verifier conditions
        if not self._check_rule_conditions(rule, event_data):
            return None

        # Executer les actions
        actions_executed = []
        points_awarded = 0
        badges_unlocked = []

        for action in (rule.actions or []):
            action_type = action.get("type")

            if action_type == "award_points":
                point_type = PointType(action.get("point_type", "xp"))
                amount = action.get("amount", 0)
                self.award_points(
                    user_id,
                    amount,
                    point_type,
                    f"Regle: {rule.name}",
                    "rule",
                    rule.id,
                    apply_multiplier=rule.level_multiplier
                )
                points_awarded += amount
                actions_executed.append({"type": "award_points", "amount": amount, "point_type": point_type.value})

            elif action_type == "unlock_badge":
                badge_id = action.get("badge_id")
                if badge_id:
                    try:
                        self.unlock_badge(user_id, UUID(badge_id), auto=True)
                        badges_unlocked.append(badge_id)
                        actions_executed.append({"type": "unlock_badge", "badge_id": badge_id})
                    except (BadgeAlreadyUnlockedError, BadgeNotFoundError):
                        pass

            elif action_type == "update_badge_progress":
                badge_id = action.get("badge_id")
                progress = action.get("progress", 1)
                if badge_id:
                    self.update_badge_progress(user_id, UUID(badge_id), progress, increment=True)
                    actions_executed.append({"type": "update_badge_progress", "badge_id": badge_id, "progress": progress})

            elif action_type == "update_challenge_progress":
                challenge_id = action.get("challenge_id")
                progress = action.get("progress", 1)
                if challenge_id:
                    try:
                        self.update_challenge_progress(user_id, UUID(challenge_id), progress, increment=True)
                        actions_executed.append({"type": "update_challenge_progress", "challenge_id": challenge_id})
                    except ChallengeNotJoinedError:
                        pass

        # Logger le declenchement
        self.rule_logs.create({
            "rule_id": rule.id,
            "user_id": user_id,
            "event_data": event_data,
            "success": True,
            "actions_executed": actions_executed,
            "points_awarded": points_awarded,
            "badges_unlocked": badges_unlocked
        })

        # Mettre a jour les stats de la regle
        self.rules.increment_trigger_count(rule.id)

        return {
            "rule_id": str(rule.id),
            "rule_name": rule.name,
            "actions_executed": actions_executed,
            "points_awarded": points_awarded,
            "badges_unlocked": badges_unlocked
        }

    def _check_rule_conditions(self, rule, event_data: dict[str, Any]) -> bool:
        """Verifie les conditions d'une regle."""
        conditions = rule.conditions or {}
        if not conditions:
            return True

        results = []
        for condition in conditions.get("items", [conditions]):
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")

            if not field or not operator:
                continue

            event_value = event_data.get(field)

            if operator == "==":
                results.append(event_value == value)
            elif operator == "!=":
                results.append(event_value != value)
            elif operator == ">":
                results.append(event_value > value if event_value else False)
            elif operator == ">=":
                results.append(event_value >= value if event_value else False)
            elif operator == "<":
                results.append(event_value < value if event_value else False)
            elif operator == "<=":
                results.append(event_value <= value if event_value else False)
            elif operator == "in":
                results.append(event_value in value if value else False)
            elif operator == "contains":
                results.append(value in event_value if event_value else False)

        if not results:
            return True

        if rule.condition_logic == "OR":
            return any(results)
        return all(results)

    # =========================================================================
    # EQUIPES
    # =========================================================================

    def create_team(self, data: dict[str, Any], created_by: UUID):
        """Cree une nouvelle equipe."""
        self._check_feature_enabled("teams")

        if self.teams.code_exists(data.get("code", "")):
            raise DuplicateCodeError("equipe", data.get("code", ""))

        # Creer l'equipe
        data["captain_id"] = created_by
        team = self.teams.create(data, created_by)

        # Ajouter le createur comme capitaine
        self.team_memberships.create({
            "user_id": created_by,
            "team_id": team.id,
            "role": "captain"
        })

        # Mettre a jour le profil
        profile = self.get_profile(created_by)
        self.profiles.update(profile, {"team_id": team.id})

        # Mettre a jour le compteur
        self.teams.update(team, {"current_members": 1})

        return team

    def join_team(self, user_id: UUID, team_id: UUID):
        """Rejoint une equipe."""
        self._check_feature_enabled("teams")

        team = self.teams.get_by_id(team_id)
        if not team:
            raise TeamNotFoundError(str(team_id))

        # Verifier si deja dans une equipe
        existing = self.team_memberships.get_active_by_user(user_id)
        if existing:
            raise AlreadyInTeamError(str(user_id), str(existing.team_id))

        # Verifier limite
        if team.max_members and team.current_members >= team.max_members:
            raise TeamFullError(str(team_id), team.max_members)

        # Creer l'appartenance
        membership = self.team_memberships.create({
            "user_id": user_id,
            "team_id": team_id,
            "role": "member"
        })

        # Mettre a jour
        self.teams.update(team, {"current_members": team.current_members + 1})
        profile = self.get_profile(user_id)
        self.profiles.update(profile, {"team_id": team_id})

        return membership

    def leave_team(self, user_id: UUID):
        """Quitte l'equipe actuelle."""
        membership = self.team_memberships.get_active_by_user(user_id)
        if not membership:
            raise NotTeamMemberError(str(user_id), "")

        team = self.teams.get_by_id(membership.team_id)

        # Desactiver l'appartenance
        self.team_memberships.deactivate(membership)

        # Mettre a jour l'equipe
        self.teams.update(team, {"current_members": max(0, team.current_members - 1)})

        # Mettre a jour le profil
        profile = self.get_profile(user_id)
        self.profiles.update(profile, {"team_id": None})

        return True

    def get_team(self, team_id: UUID):
        """Recupere une equipe."""
        team = self.teams.get_by_id(team_id)
        if not team:
            raise TeamNotFoundError(str(team_id))
        return team

    def list_teams(
        self,
        search: str | None = None,
        public_only: bool = False,
        page: int = 1,
        page_size: int = 20
    ):
        """Liste les equipes."""
        self._check_feature_enabled("teams")
        return self.teams.list(search, public_only, page, page_size)

    def get_team_members(self, team_id: UUID):
        """Recupere les membres d'une equipe."""
        return self.team_memberships.get_by_team(team_id)

    # =========================================================================
    # COMPETITIONS
    # =========================================================================

    def create_competition(self, data: dict[str, Any], created_by: UUID | None = None):
        """Cree une nouvelle competition."""
        self._check_feature_enabled("competitions")

        if self.competitions.code_exists(data.get("code", "")):
            raise DuplicateCodeError("competition", data.get("code", ""))

        return self.competitions.create(data, created_by)

    def register_for_competition(
        self,
        competition_id: UUID,
        user_id: UUID | None = None,
        team_id: UUID | None = None
    ):
        """S'inscrit a une competition."""
        self._check_feature_enabled("competitions")

        competition = self.competitions.get_by_id(competition_id)
        if not competition:
            raise CompetitionNotFoundError(str(competition_id))

        if competition.status != CompetitionStatus.REGISTRATION:
            raise CompetitionNotFoundError(str(competition_id))

        if competition.max_participants and competition.current_participants >= competition.max_participants:
            raise CompetitionNotFoundError(str(competition_id))

        # Verifier inscription existante
        if user_id:
            existing = self.competition_participants.get_by_user(user_id, competition_id)
            if existing:
                raise AlreadyRegisteredError(str(competition_id), str(user_id))

        # Creer la participation
        participant = self.competition_participants.create({
            "competition_id": competition_id,
            "user_id": user_id,
            "team_id": team_id
        })

        # Mettre a jour
        self.competitions.update(competition, {
            "current_participants": competition.current_participants + 1
        })

        return participant

    def get_competition(self, competition_id: UUID):
        """Recupere une competition."""
        competition = self.competitions.get_by_id(competition_id)
        if not competition:
            raise CompetitionNotFoundError(str(competition_id))
        return competition

    def list_competitions(
        self,
        status: list[CompetitionStatus] | None = None,
        page: int = 1,
        page_size: int = 20
    ):
        """Liste les competitions."""
        self._check_feature_enabled("competitions")
        return self.competitions.list(status, page, page_size)

    # =========================================================================
    # LEADERBOARDS
    # =========================================================================

    def get_leaderboard(
        self,
        leaderboard_id: UUID | None = None,
        code: str | None = None,
        period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME
    ) -> LeaderboardWithEntries:
        """Recupere un classement avec ses entrees."""
        self._check_feature_enabled("leaderboards")

        if leaderboard_id:
            leaderboard = self.leaderboards.get_by_id(leaderboard_id)
        elif code:
            leaderboard = self.leaderboards.get_by_code(code)
        else:
            leaderboard = self.leaderboards.get_default(period)

        if not leaderboard:
            # Creer un classement par defaut
            leaderboard = self._create_default_leaderboard(period)

        entries = self.leaderboard_entries.get_entries(leaderboard.id, leaderboard.show_top_n)

        return LeaderboardWithEntries(
            **{k: v for k, v in leaderboard.__dict__.items() if not k.startswith('_')},
            entries=[LeaderboardEntryResponse(**{k: v for k, v in e.__dict__.items() if not k.startswith('_')}) for e in entries]
        )

    def get_user_rank(
        self,
        user_id: UUID,
        leaderboard_id: UUID | None = None,
        period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME
    ) -> LeaderboardEntryResponse | None:
        """Recupere le rang d'un utilisateur."""
        if leaderboard_id:
            leaderboard = self.leaderboards.get_by_id(leaderboard_id)
        else:
            leaderboard = self.leaderboards.get_default(period)

        if not leaderboard:
            return None

        entry = self.leaderboard_entries.get_user_entry(leaderboard.id, user_id)
        if entry:
            return LeaderboardEntryResponse(**{k: v for k, v in entry.__dict__.items() if not k.startswith('_')})
        return None

    def refresh_leaderboard(self, leaderboard_id: UUID):
        """Rafraichit un classement."""
        leaderboard = self.leaderboards.get_by_id(leaderboard_id)
        if not leaderboard:
            return

        # Supprimer les anciennes entrees
        self.leaderboard_entries.clear_entries(leaderboard_id)

        # Recuperer les profils tries
        profiles = self.profiles.get_top_by_xp(leaderboard.show_top_n)

        # Creer les nouvelles entrees
        entries = []
        for rank, profile in enumerate(profiles, 1):
            entries.append({
                "leaderboard_id": leaderboard_id,
                "user_id": profile.user_id,
                "rank": rank,
                "score": profile.lifetime_xp if leaderboard.point_type == PointType.XP else profile.coins_balance,
                "display_name": profile.title or f"User {str(profile.user_id)[:8]}",
                "avatar_url": profile.avatar_url,
                "level": profile.current_level,
                "badge_count": profile.badges_unlocked
            })

        self.leaderboard_entries.create_many(entries)

        # Mettre a jour timestamp
        self.leaderboards.update(leaderboard, {"last_computed_at": datetime.utcnow()})

    def _create_default_leaderboard(self, period: LeaderboardPeriod):
        """Cree un classement par defaut."""
        code = f"DEFAULT_{period.value.upper()}"
        existing = self.leaderboards.get_by_code(code)
        if existing:
            return existing

        return self.leaderboards.create({
            "code": code,
            "name": f"Classement {period.value}",
            "period": period,
            "point_type": PointType.XP,
            "is_featured": period == LeaderboardPeriod.ALL_TIME,
            "is_public": True
        })

    # =========================================================================
    # STREAKS
    # =========================================================================

    def update_streak(self, user_id: UUID, streak_type: str = "login"):
        """Met a jour une serie."""
        today = date.today()
        streak, created = self.streaks.get_or_create(user_id, streak_type)

        if streak.last_activity_date == today:
            return streak  # Deja mis a jour aujourd'hui

        yesterday = today - timedelta(days=1)

        if streak.last_activity_date == yesterday:
            # Continue la serie
            new_count = streak.current_count + 1

            # Verifier record
            if new_count > streak.longest_count:
                streak.longest_count = new_count
                best_streaks = list(streak.best_streaks or [])
                best_streaks.append({
                    "count": new_count,
                    "date": today.isoformat()
                })
                best_streaks = sorted(best_streaks, key=lambda x: x["count"], reverse=True)[:5]
                streak.best_streaks = best_streaks

            streak.current_count = new_count
        else:
            # Serie cassee
            if streak.current_count > 0:
                streak.streak_broken_at = datetime.utcnow()
                streak.total_streaks += 1

                # Notification de serie cassee
                self._create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.STREAK_BROKEN,
                    title="Serie interrompue",
                    message=f"Votre serie de {streak.current_count} jours a ete interrompue"
                )

            streak.current_count = 1
            streak.streak_started_at = datetime.utcnow()

        streak.last_activity_date = today

        # Calculer multiplicateur
        config = self.get_config()
        if streak.current_count > 1:
            multiplier = min(
                Decimal("1.0") + Decimal("0.1") * (streak.current_count - 1),
                config.max_streak_multiplier
            )
            streak.current_multiplier = multiplier

        self.streaks.update(streak, {
            "current_count": streak.current_count,
            "longest_count": streak.longest_count,
            "last_activity_date": streak.last_activity_date,
            "streak_started_at": streak.streak_started_at,
            "streak_broken_at": streak.streak_broken_at,
            "total_streaks": streak.total_streaks,
            "current_multiplier": streak.current_multiplier,
            "best_streaks": streak.best_streaks
        })

        # Bonus de streak
        if streak.current_count in [7, 30, 100, 365]:
            bonus = config.login_streak_bonus * streak.current_count
            self.award_points(
                user_id,
                bonus,
                PointType.BONUS,
                f"Bonus serie de {streak.current_count} jours!",
                "streak",
                streak.id
            )

        return streak

    def get_user_streaks(self, user_id: UUID):
        """Recupere les series d'un utilisateur."""
        return self.streaks.get_by_user(user_id)

    # =========================================================================
    # NOTIFICATIONS
    # =========================================================================

    def _create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str | None = None,
        icon: str | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
        data: dict[str, Any] | None = None,
        action_url: str | None = None
    ):
        """Cree une notification."""
        return self.notifications.create({
            "user_id": user_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "icon": icon,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "data": data or {},
            "action_url": action_url
        })

    def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        notification_type: NotificationType | None = None,
        limit: int = 50
    ):
        """Recupere les notifications d'un utilisateur."""
        return self.notifications.get_by_user(user_id, unread_only, notification_type, limit)

    def count_unread_notifications(self, user_id: UUID) -> int:
        """Compte les notifications non lues."""
        return self.notifications.count_unread(user_id)

    def mark_notifications_read(
        self,
        user_id: UUID,
        notification_ids: list[UUID] | None = None,
        mark_all: bool = False
    ) -> int:
        """Marque des notifications comme lues."""
        if mark_all:
            return self.notifications.mark_all_as_read(user_id)
        elif notification_ids:
            return self.notifications.mark_as_read(notification_ids, user_id)
        return 0

    # =========================================================================
    # ACTIVITE
    # =========================================================================

    def _log_activity(
        self,
        user_id: UUID,
        activity_type: str,
        description: str = "",
        details: dict[str, Any] | None = None,
        points_delta: int = 0,
        xp_delta: int = 0,
        source_module: str | None = None,
        source_action: str | None = None,
        source_id: UUID | None = None,
        is_public: bool = True
    ):
        """Enregistre une activite."""
        return self.activities.create({
            "user_id": user_id,
            "activity_type": activity_type,
            "description": description,
            "details": details or {},
            "points_delta": points_delta,
            "xp_delta": xp_delta,
            "source_module": source_module,
            "source_action": source_action,
            "source_id": source_id,
            "is_public": is_public
        })

    def get_user_activity(
        self,
        user_id: UUID,
        filters: ActivityFilters | None = None,
        page: int = 1,
        page_size: int = 50
    ):
        """Recupere l'historique d'activite d'un utilisateur."""
        return self.activities.get_by_user(user_id, filters, page, page_size)

    # =========================================================================
    # DASHBOARD & STATS
    # =========================================================================

    def get_user_dashboard(self, user_id: UUID) -> GamificationDashboard:
        """Recupere le tableau de bord d'un utilisateur."""
        profile = self.get_or_create_profile(user_id)
        summary = self.get_profile_summary(user_id)

        transactions, _ = self.transactions.get_by_user(user_id, page_size=5)
        badges = self.user_badges.get_recent_unlocks(user_id, 5)
        challenges = self.user_challenges.get_by_user(user_id, ChallengeStatus.ACTIVE)
        streaks = self.streaks.get_by_user(user_id)
        unread_count = self.notifications.count_unread(user_id)

        # Rangs
        rank_global = self.get_user_rank(user_id, period=LeaderboardPeriod.ALL_TIME)
        rank_monthly = self.get_user_rank(user_id, period=LeaderboardPeriod.MONTHLY)

        return GamificationDashboard(
            user_profile=summary,
            recent_points=[PointTransactionResponse(**{k: v for k, v in t.__dict__.items() if not k.startswith('_')}) for t in transactions],
            recent_badges=[UserBadgeResponse(**{k: v for k, v in b.__dict__.items() if not k.startswith('_')}) for b in badges],
            active_challenges=[UserChallengeResponse(**{k: v for k, v in c.__dict__.items() if not k.startswith('_')}) for c in challenges],
            current_streaks=streaks,
            notifications_count=unread_count,
            rank_global=rank_global.rank if rank_global else None,
            rank_monthly=rank_monthly.rank if rank_monthly else None
        )

    def get_global_stats(self) -> GamificationStats:
        """Recupere les statistiques globales."""
        profiles, total = self.profiles.list(page_size=1)
        today = date.today()

        # Stats basiques
        stats = GamificationStats(
            tenant_id=str(self.tenant_id),
            total_users=total,
            active_users_today=0,
            active_users_week=0,
            active_users_month=0,
            total_points_earned=0,
            total_points_spent=0,
            total_badges_unlocked=0,
            total_challenges_completed=0,
            total_rewards_claimed=0,
            avg_user_level=Decimal("1.0"),
            top_earners=[],
            popular_badges=[],
            active_challenges_count=len(self.challenges.get_active()),
            active_competitions_count=0
        )

        return stats

    def get_user_stats(self, user_id: UUID) -> UserGamificationStats:
        """Recupere les statistiques d'un utilisateur."""
        profile = self.get_profile(user_id)

        return UserGamificationStats(
            user_id=user_id,
            total_xp=profile.lifetime_xp,
            total_coins_earned=profile.lifetime_coins_earned,
            total_coins_spent=profile.lifetime_coins_spent,
            badges_unlocked=profile.badges_unlocked,
            badges_total=self.badges.list(page_size=1)[1],
            challenges_completed=profile.challenges_completed,
            challenges_total_joined=self.user_challenges.count_by_user(user_id),
            rewards_claimed=profile.rewards_claimed,
            current_login_streak=profile.current_login_streak,
            longest_login_streak=profile.longest_login_streak,
            member_since=profile.created_at,
            last_activity=profile.updated_at
        )

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _generate_claim_code(self) -> str:
        """Genere un code de reclamation unique."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=12))


# =============================================================================
# FACTORY
# =============================================================================

def create_gamification_service(db: Session, tenant_id: UUID) -> GamificationService:
    """Factory pour creer un service de gamification."""
    return GamificationService(db, tenant_id)
