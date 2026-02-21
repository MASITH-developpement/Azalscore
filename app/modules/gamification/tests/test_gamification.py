"""
AZALS MODULE GAMIFICATION - Tests
=================================

Tests unitaires et d'integration pour le module de gamification.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.modules.gamification.models import (
    PointType,
    TransactionType,
    BadgeRarity,
    BadgeStatus,
    ChallengeType,
    ChallengeStatus,
    RewardType,
    RewardStatus,
    LeaderboardPeriod,
    NotificationType,
    RuleEventType,
)
from app.modules.gamification.service import GamificationService
from app.modules.gamification.exceptions import (
    ProfileNotFoundError,
    InsufficientPointsError,
    BadgeNotFoundError,
    BadgeAlreadyUnlockedError,
    ChallengeNotFoundError,
    AlreadyJoinedChallengeError,
    RewardNotFoundError,
    RewardOutOfStockError,
    TeamNotFoundError,
    AlreadyInTeamError,
    FeatureDisabledError,
    DuplicateCodeError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def engine():
    """Cree un moteur SQLite en memoire pour les tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Cree une session de test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def tenant_id():
    """ID tenant de test."""
    return uuid4()


@pytest.fixture
def user_id():
    """ID utilisateur de test."""
    return uuid4()


@pytest.fixture
def service(session, tenant_id):
    """Service de gamification pour les tests."""
    return GamificationService(session, tenant_id)


# =============================================================================
# TESTS PROFILS
# =============================================================================

class TestUserProfile:
    """Tests pour les profils utilisateur."""

    def test_create_profile(self, service, user_id):
        """Test creation de profil."""
        profile = service.get_or_create_profile(user_id)

        assert profile is not None
        assert profile.user_id == user_id
        assert profile.current_level == 1
        assert profile.current_xp == 0
        assert profile.coins_balance == 0

    def test_get_existing_profile(self, service, user_id):
        """Test recuperation de profil existant."""
        profile1 = service.get_or_create_profile(user_id)
        profile2 = service.get_or_create_profile(user_id)

        assert profile1.id == profile2.id

    def test_update_profile(self, service, user_id):
        """Test mise a jour de profil."""
        service.get_or_create_profile(user_id)
        updated = service.update_profile(user_id, {
            "avatar_url": "https://example.com/avatar.png",
            "title": "Champion"
        })

        assert updated.avatar_url == "https://example.com/avatar.png"
        assert updated.title == "Champion"

    def test_get_profile_summary(self, service, user_id):
        """Test resume de profil."""
        service.get_or_create_profile(user_id)
        summary = service.get_profile_summary(user_id)

        assert summary.user_id == user_id
        assert summary.level == 1
        assert summary.badges_count == 0


# =============================================================================
# TESTS POINTS
# =============================================================================

class TestPoints:
    """Tests pour le systeme de points."""

    def test_award_xp(self, service, user_id):
        """Test attribution de XP."""
        profile = service.get_or_create_profile(user_id)
        initial_xp = profile.current_xp

        transaction = service.award_points(
            user_id,
            amount=100,
            point_type=PointType.XP,
            description="Test XP"
        )

        assert transaction.amount >= 100  # Peut avoir multiplicateur
        assert transaction.point_type == PointType.XP
        assert transaction.transaction_type == TransactionType.EARN

        profile = service.get_profile(user_id)
        assert profile.current_xp > initial_xp

    def test_award_coins(self, service, user_id):
        """Test attribution de coins."""
        service.get_or_create_profile(user_id)

        transaction = service.award_points(
            user_id,
            amount=50,
            point_type=PointType.COINS,
            description="Test coins"
        )

        profile = service.get_profile(user_id)
        assert profile.coins_balance >= 50

    def test_spend_coins(self, service, user_id):
        """Test depense de coins."""
        service.get_or_create_profile(user_id)

        # D'abord gagner des coins
        service.award_points(user_id, 100, PointType.COINS, "Gain")

        # Ensuite depenser
        transaction = service.spend_points(
            user_id,
            amount=30,
            point_type=PointType.COINS,
            description="Depense"
        )

        assert transaction.amount == -30
        profile = service.get_profile(user_id)
        assert profile.coins_balance >= 70

    def test_insufficient_points(self, service, user_id):
        """Test points insuffisants."""
        service.get_or_create_profile(user_id)

        with pytest.raises(InsufficientPointsError):
            service.spend_points(
                user_id,
                amount=1000,
                point_type=PointType.COINS,
                description="Trop cher"
            )

    def test_transfer_points(self, service, user_id):
        """Test transfert de points."""
        user2_id = uuid4()

        service.get_or_create_profile(user_id)
        service.get_or_create_profile(user2_id)

        # Donner des coins au premier utilisateur
        service.award_points(user_id, 100, PointType.COINS, "Initial")

        # Transferer
        service.transfer_points(user_id, user2_id, 50, PointType.COINS)

        profile1 = service.get_profile(user_id)
        profile2 = service.get_profile(user2_id)

        assert profile1.coins_balance >= 50
        assert profile2.coins_balance >= 50


# =============================================================================
# TESTS NIVEAUX
# =============================================================================

class TestLevels:
    """Tests pour le systeme de niveaux."""

    def test_level_up(self, service, user_id):
        """Test passage de niveau."""
        service.get_or_create_profile(user_id)

        # Attribuer assez d'XP pour passer niveau 2 (100 XP requis)
        service.award_points(
            user_id,
            amount=150,
            point_type=PointType.XP,
            description="Level up",
            apply_multiplier=False
        )

        profile = service.get_profile(user_id)
        assert profile.current_level >= 2

    def test_get_level_info(self, service):
        """Test recuperation info niveau."""
        # Assurer que les niveaux par defaut existent
        service._ensure_default_levels()

        level = service.get_level_info(1)
        assert level is not None
        assert level.level_number == 1
        assert level.name == "Debutant"


# =============================================================================
# TESTS BADGES
# =============================================================================

class TestBadges:
    """Tests pour le systeme de badges."""

    def test_create_badge(self, service, user_id):
        """Test creation de badge."""
        badge = service.create_badge({
            "code": "FIRST_LOGIN",
            "name": "Premiere connexion",
            "description": "Badge pour la premiere connexion",
            "icon": "star",
            "rarity": BadgeRarity.COMMON,
            "points_reward": 10
        }, user_id)

        assert badge.code == "FIRST_LOGIN"
        assert badge.rarity == BadgeRarity.COMMON

    def test_duplicate_badge_code(self, service, user_id):
        """Test code badge duplique."""
        service.create_badge({
            "code": "UNIQUE_BADGE",
            "name": "Badge unique",
            "icon": "star"
        }, user_id)

        with pytest.raises(DuplicateCodeError):
            service.create_badge({
                "code": "UNIQUE_BADGE",
                "name": "Autre badge",
                "icon": "star"
            }, user_id)

    def test_unlock_badge(self, service, user_id):
        """Test deblocage de badge."""
        # Creer le badge
        badge = service.create_badge({
            "code": "TEST_BADGE",
            "name": "Badge test",
            "icon": "medal",
            "points_reward": 25
        }, user_id)

        # Creer le profil
        service.get_or_create_profile(user_id)

        # Debloquer
        user_badge = service.unlock_badge(user_id, badge.id)

        assert user_badge.status == BadgeStatus.UNLOCKED
        assert user_badge.unlocked_at is not None

        # Verifier le profil
        profile = service.get_profile(user_id)
        assert profile.badges_unlocked == 1

    def test_already_unlocked_badge(self, service, user_id):
        """Test badge deja debloque."""
        badge = service.create_badge({
            "code": "SINGLE_BADGE",
            "name": "Badge unique",
            "icon": "crown"
        }, user_id)

        service.get_or_create_profile(user_id)
        service.unlock_badge(user_id, badge.id)

        with pytest.raises(BadgeAlreadyUnlockedError):
            service.unlock_badge(user_id, badge.id)

    def test_stackable_badge(self, service, user_id):
        """Test badge stackable."""
        badge = service.create_badge({
            "code": "STACK_BADGE",
            "name": "Badge stackable",
            "icon": "layers",
            "is_stackable": True
        }, user_id)

        service.get_or_create_profile(user_id)
        service.unlock_badge(user_id, badge.id)
        user_badge = service.unlock_badge(user_id, badge.id)

        assert user_badge.times_earned == 2

    def test_badge_progress(self, service, user_id):
        """Test progression de badge."""
        badge = service.create_badge({
            "code": "PROGRESS_BADGE",
            "name": "Badge a progression",
            "icon": "chart",
            "progress_max": 100
        }, user_id)

        service.get_or_create_profile(user_id)

        # Mettre a jour la progression
        user_badge = service.update_badge_progress(user_id, badge.id, 50)
        assert user_badge.progress == 50
        assert user_badge.status == BadgeStatus.IN_PROGRESS

        # Completer
        user_badge = service.update_badge_progress(user_id, badge.id, 50, increment=True)
        assert user_badge.status == BadgeStatus.UNLOCKED


# =============================================================================
# TESTS DEFIS
# =============================================================================

class TestChallenges:
    """Tests pour les defis."""

    def test_create_challenge(self, service, user_id):
        """Test creation de defi."""
        challenge = service.create_challenge({
            "code": "DAILY_SALES",
            "name": "Vendre 10 produits",
            "challenge_type": ChallengeType.DAILY,
            "target_value": 10,
            "rewards": [{"type": "xp", "value": 100}]
        }, user_id)

        assert challenge.code == "DAILY_SALES"
        assert challenge.target_value == 10

    def test_join_challenge(self, service, user_id):
        """Test rejoindre un defi."""
        challenge = service.create_challenge({
            "code": "JOIN_TEST",
            "name": "Defi test",
            "challenge_type": ChallengeType.WEEKLY,
            "status": ChallengeStatus.ACTIVE,
            "target_value": 5
        }, user_id)

        service.get_or_create_profile(user_id)
        user_challenge = service.join_challenge(user_id, challenge.id)

        assert user_challenge.status == ChallengeStatus.ACTIVE
        assert user_challenge.progress == 0
        assert user_challenge.target == 5

    def test_already_joined_challenge(self, service, user_id):
        """Test deja inscrit au defi."""
        challenge = service.create_challenge({
            "code": "SINGLE_JOIN",
            "name": "Un seul join",
            "challenge_type": ChallengeType.DAILY,
            "status": ChallengeStatus.ACTIVE,
            "target_value": 1
        }, user_id)

        service.get_or_create_profile(user_id)
        service.join_challenge(user_id, challenge.id)

        with pytest.raises(AlreadyJoinedChallengeError):
            service.join_challenge(user_id, challenge.id)

    def test_update_challenge_progress(self, service, user_id):
        """Test mise a jour progression."""
        challenge = service.create_challenge({
            "code": "PROGRESS_TEST",
            "name": "Progression test",
            "challenge_type": ChallengeType.WEEKLY,
            "status": ChallengeStatus.ACTIVE,
            "target_value": 10,
            "rewards": [{"type": "xp", "value": 50}]
        }, user_id)

        service.get_or_create_profile(user_id)
        service.join_challenge(user_id, challenge.id)

        # Progression partielle
        uc = service.update_challenge_progress(user_id, challenge.id, 5)
        assert uc.progress == 5
        assert uc.status == ChallengeStatus.ACTIVE

        # Completion
        uc = service.update_challenge_progress(user_id, challenge.id, 5)
        assert uc.progress == 10
        assert uc.status == ChallengeStatus.COMPLETED

    def test_claim_challenge_rewards(self, service, user_id):
        """Test reclamation recompenses."""
        challenge = service.create_challenge({
            "code": "REWARD_TEST",
            "name": "Recompense test",
            "challenge_type": ChallengeType.DAILY,
            "status": ChallengeStatus.ACTIVE,
            "target_value": 1,
            "rewards": [
                {"type": "xp", "value": 100},
                {"type": "coins", "value": 50}
            ]
        }, user_id)

        service.get_or_create_profile(user_id)
        service.join_challenge(user_id, challenge.id)
        service.update_challenge_progress(user_id, challenge.id, 1)

        rewards = service.claim_challenge_rewards(user_id, challenge.id)

        assert len(rewards) == 2
        assert any(r["type"] == "xp" for r in rewards)
        assert any(r["type"] == "coins" for r in rewards)


# =============================================================================
# TESTS RECOMPENSES
# =============================================================================

class TestRewards:
    """Tests pour les recompenses."""

    def test_create_reward(self, service, user_id):
        """Test creation de recompense."""
        reward = service.create_reward({
            "code": "GIFT_CARD",
            "name": "Carte cadeau 50E",
            "reward_type": RewardType.VOUCHER,
            "cost_points": 500,
            "cost_type": PointType.COINS,
            "stock": 10
        }, user_id)

        assert reward.code == "GIFT_CARD"
        assert reward.cost_points == 500

    def test_claim_reward(self, service, user_id):
        """Test reclamation de recompense."""
        reward = service.create_reward({
            "code": "CLAIM_TEST",
            "name": "Test reclamation",
            "reward_type": RewardType.POINTS,
            "cost_points": 50,
            "cost_type": PointType.COINS,
            "value": {"point_type": "xp", "amount": 100}
        }, user_id)

        service.get_or_create_profile(user_id)
        service.award_points(user_id, 100, PointType.COINS, "Initial")

        claim = service.claim_reward(user_id, reward.id)

        assert claim.status == RewardStatus.FULFILLED
        assert claim.points_spent == 50

    def test_reward_out_of_stock(self, service, user_id):
        """Test rupture de stock."""
        reward = service.create_reward({
            "code": "LIMITED",
            "name": "Edition limitee",
            "reward_type": RewardType.PHYSICAL,
            "cost_points": 10,
            "stock": 0
        }, user_id)

        service.get_or_create_profile(user_id)
        service.award_points(user_id, 100, PointType.COINS, "Initial")

        with pytest.raises(RewardOutOfStockError):
            service.claim_reward(user_id, reward.id)


# =============================================================================
# TESTS EQUIPES
# =============================================================================

class TestTeams:
    """Tests pour les equipes."""

    def test_create_team(self, service, user_id):
        """Test creation d'equipe."""
        service.get_or_create_profile(user_id)

        team = service.create_team({
            "code": "ALPHA",
            "name": "Team Alpha",
            "description": "La meilleure equipe"
        }, user_id)

        assert team.code == "ALPHA"
        assert team.captain_id == user_id
        assert team.current_members == 1

    def test_join_team(self, service, user_id):
        """Test rejoindre une equipe."""
        user2_id = uuid4()

        service.get_or_create_profile(user_id)
        service.get_or_create_profile(user2_id)

        team = service.create_team({
            "code": "JOIN_TEAM",
            "name": "Team Join"
        }, user_id)

        membership = service.join_team(user2_id, team.id)

        assert membership.team_id == team.id
        assert membership.role == "member"

        team = service.get_team(team.id)
        assert team.current_members == 2

    def test_already_in_team(self, service, user_id):
        """Test deja membre d'une equipe."""
        service.get_or_create_profile(user_id)

        team1 = service.create_team({"code": "TEAM1", "name": "Team 1"}, user_id)

        with pytest.raises(AlreadyInTeamError):
            service.create_team({"code": "TEAM2", "name": "Team 2"}, user_id)

    def test_leave_team(self, service, user_id):
        """Test quitter une equipe."""
        user2_id = uuid4()

        service.get_or_create_profile(user_id)
        service.get_or_create_profile(user2_id)

        team = service.create_team({
            "code": "LEAVE_TEAM",
            "name": "Team Leave"
        }, user_id)

        service.join_team(user2_id, team.id)
        service.leave_team(user2_id)

        profile = service.get_profile(user2_id)
        assert profile.team_id is None


# =============================================================================
# TESTS STREAKS
# =============================================================================

class TestStreaks:
    """Tests pour les series."""

    def test_start_streak(self, service, user_id):
        """Test demarrage de serie."""
        service.get_or_create_profile(user_id)

        streak = service.update_streak(user_id, "login")

        assert streak.current_count == 1
        assert streak.last_activity_date == date.today()

    def test_continue_streak(self, service, user_id):
        """Test continuation de serie."""
        service.get_or_create_profile(user_id)

        streak = service.update_streak(user_id, "login")

        # Simuler le lendemain
        streak.last_activity_date = date.today() - timedelta(days=1)
        service.streaks.update(streak, {"last_activity_date": streak.last_activity_date})

        streak = service.update_streak(user_id, "login")

        assert streak.current_count == 2


# =============================================================================
# TESTS NOTIFICATIONS
# =============================================================================

class TestNotifications:
    """Tests pour les notifications."""

    def test_level_up_notification(self, service, user_id):
        """Test notification de level up."""
        service.get_or_create_profile(user_id)

        # Passer niveau 2
        service.award_points(user_id, 150, PointType.XP, "Level up", apply_multiplier=False)

        notifications = service.get_notifications(user_id)
        level_up_notifs = [n for n in notifications if n.notification_type == NotificationType.LEVEL_UP]

        assert len(level_up_notifs) > 0

    def test_badge_notification(self, service, user_id):
        """Test notification de badge."""
        badge = service.create_badge({
            "code": "NOTIF_BADGE",
            "name": "Badge notification",
            "icon": "bell"
        }, user_id)

        service.get_or_create_profile(user_id)
        service.unlock_badge(user_id, badge.id)

        notifications = service.get_notifications(user_id)
        badge_notifs = [n for n in notifications if n.notification_type == NotificationType.BADGE_UNLOCKED]

        assert len(badge_notifs) > 0

    def test_mark_notifications_read(self, service, user_id):
        """Test marquer notifications comme lues."""
        service.get_or_create_profile(user_id)

        # Creer des notifications
        service.award_points(user_id, 200, PointType.XP, "Test", apply_multiplier=False)

        unread = service.count_unread_notifications(user_id)
        assert unread > 0

        service.mark_notifications_read(user_id, mark_all=True)

        unread = service.count_unread_notifications(user_id)
        assert unread == 0


# =============================================================================
# TESTS REGLES
# =============================================================================

class TestRules:
    """Tests pour les regles d'attribution."""

    def test_create_rule(self, service, user_id):
        """Test creation de regle."""
        rule = service.create_rule({
            "code": "SALE_BONUS",
            "name": "Bonus vente",
            "event_type": RuleEventType.ACTION_COMPLETED,
            "event_source": "sales",
            "event_action": "create",
            "actions": [{"type": "award_points", "point_type": "xp", "amount": 10}]
        }, user_id)

        assert rule.code == "SALE_BONUS"
        assert rule.event_type == RuleEventType.ACTION_COMPLETED

    def test_trigger_rule(self, service, user_id):
        """Test declenchement de regle."""
        rule = service.create_rule({
            "code": "TRIGGER_TEST",
            "name": "Test trigger",
            "event_type": RuleEventType.ACTION_COMPLETED,
            "event_source": "test",
            "actions": [{"type": "award_points", "point_type": "xp", "amount": 25}]
        }, user_id)

        service.get_or_create_profile(user_id)
        initial_xp = service.get_profile(user_id).current_xp

        results = service.trigger_event(
            RuleEventType.ACTION_COMPLETED,
            user_id,
            {"action": "test"},
            "test"
        )

        final_xp = service.get_profile(user_id).current_xp
        assert final_xp > initial_xp


# =============================================================================
# TESTS DASHBOARD
# =============================================================================

class TestDashboard:
    """Tests pour le dashboard."""

    def test_get_dashboard(self, service, user_id):
        """Test recuperation dashboard."""
        service.get_or_create_profile(user_id)

        dashboard = service.get_user_dashboard(user_id)

        assert dashboard.user_profile is not None
        assert isinstance(dashboard.recent_points, list)
        assert isinstance(dashboard.recent_badges, list)
        assert isinstance(dashboard.active_challenges, list)

    def test_get_user_stats(self, service, user_id):
        """Test statistiques utilisateur."""
        service.get_or_create_profile(user_id)

        # Ajouter quelques activites
        service.award_points(user_id, 100, PointType.XP, "Test")
        service.award_points(user_id, 50, PointType.COINS, "Test")

        stats = service.get_user_stats(user_id)

        assert stats.user_id == user_id
        assert stats.total_xp >= 100
        assert stats.total_coins_earned >= 50


# =============================================================================
# TESTS CONFIGURATION
# =============================================================================

class TestConfiguration:
    """Tests pour la configuration."""

    def test_get_config(self, service):
        """Test recuperation configuration."""
        config = service.get_config()

        assert config is not None
        assert config.points_enabled is True
        assert config.badges_enabled is True

    def test_update_config(self, service):
        """Test mise a jour configuration."""
        config = service.update_config({
            "login_streak_bonus": 20,
            "notify_level_up": False
        })

        assert config.login_streak_bonus == 20
        assert config.notify_level_up is False

    def test_feature_disabled(self, service, user_id):
        """Test fonctionnalite desactivee."""
        service.update_config({"badges_enabled": False})

        with pytest.raises(FeatureDisabledError):
            service.create_badge({
                "code": "DISABLED",
                "name": "Badge desactive",
                "icon": "x"
            }, user_id)


# =============================================================================
# TESTS LEADERBOARDS
# =============================================================================

class TestLeaderboards:
    """Tests pour les classements."""

    def test_get_leaderboard(self, service, user_id):
        """Test recuperation classement."""
        service.get_or_create_profile(user_id)

        leaderboard = service.get_leaderboard(period=LeaderboardPeriod.ALL_TIME)

        assert leaderboard is not None
        assert leaderboard.period == LeaderboardPeriod.ALL_TIME

    def test_refresh_leaderboard(self, service, user_id):
        """Test rafraichissement classement."""
        service.get_or_create_profile(user_id)
        service.award_points(user_id, 100, PointType.XP, "Test")

        leaderboard = service.get_leaderboard(period=LeaderboardPeriod.ALL_TIME)
        service.refresh_leaderboard(leaderboard.id)

        # Verifier que le leaderboard a ete mis a jour
        updated = service.leaderboards.get_by_id(leaderboard.id)
        assert updated.last_computed_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
