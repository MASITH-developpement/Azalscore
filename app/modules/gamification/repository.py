"""
AZALS MODULE GAMIFICATION - Repository
======================================

Repositories avec isolation tenant et soft delete.
Pattern _base_query() filtre obligatoire.
"""
from __future__ import annotations


from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from .models import (
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
    PointType,
    TransactionType,
    BadgeStatus,
    ChallengeStatus,
    RewardStatus,
    CompetitionStatus,
    LeaderboardPeriod,
    NotificationType,
)
from .schemas import (
    BadgeFilters,
    ChallengeFilters,
    RewardFilters,
    PointTransactionFilters,
    ActivityFilters,
)


class BaseRepository:
    """Repository de base avec tenant isolation."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted


# =============================================================================
# REPOSITORY NIVEAUX
# =============================================================================

class LevelRepository(BaseRepository):
    """Repository pour les niveaux."""

    def _base_query(self):
        return self.db.query(GamificationLevel).filter(
            GamificationLevel.tenant_id == self.tenant_id
        )

    def get_by_id(self, level_id: UUID) -> GamificationLevel | None:
        return self._base_query().filter(GamificationLevel.id == level_id).first()

    def get_by_number(self, level_number: int) -> GamificationLevel | None:
        return self._base_query().filter(
            GamificationLevel.level_number == level_number,
            GamificationLevel.is_active == True
        ).first()

    def get_all(self) -> List[GamificationLevel]:
        return self._base_query().filter(
            GamificationLevel.is_active == True
        ).order_by(GamificationLevel.level_number).all()

    def get_level_for_xp(self, xp: int) -> GamificationLevel | None:
        """Trouve le niveau correspondant a un montant d'XP."""
        return self._base_query().filter(
            GamificationLevel.is_active == True,
            GamificationLevel.min_xp <= xp,
            or_(GamificationLevel.max_xp == None, GamificationLevel.max_xp > xp)
        ).order_by(desc(GamificationLevel.level_number)).first()

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> GamificationLevel:
        entity = GamificationLevel(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: GamificationLevel, data: dict[str, Any]) -> GamificationLevel:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY PROFILS UTILISATEUR
# =============================================================================

class UserProfileRepository(BaseRepository):
    """Repository pour les profils utilisateur."""

    def _base_query(self):
        query = self.db.query(UserGamificationProfile).filter(
            UserGamificationProfile.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(UserGamificationProfile.is_deleted == False)
        return query

    def get_by_id(self, profile_id: UUID) -> UserGamificationProfile | None:
        return self._base_query().filter(UserGamificationProfile.id == profile_id).first()

    def get_by_user_id(self, user_id: UUID) -> UserGamificationProfile | None:
        return self._base_query().filter(UserGamificationProfile.user_id == user_id).first()

    def get_or_create(self, user_id: UUID) -> Tuple[UserGamificationProfile, bool]:
        """Recupere ou cree un profil utilisateur."""
        profile = self.get_by_user_id(user_id)
        if profile:
            return profile, False

        profile = UserGamificationProfile(
            tenant_id=self.tenant_id,
            user_id=user_id
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile, True

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "current_level",
        sort_dir: str = "desc"
    ) -> Tuple[List[UserGamificationProfile], int]:
        query = self._base_query()
        total = query.count()

        sort_col = getattr(UserGamificationProfile, sort_by, UserGamificationProfile.current_level)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def get_top_by_xp(self, limit: int = 100) -> List[UserGamificationProfile]:
        return self._base_query().filter(
            UserGamificationProfile.show_on_leaderboard == True
        ).order_by(desc(UserGamificationProfile.lifetime_xp)).limit(limit).all()

    def get_by_team(self, team_id: UUID) -> List[UserGamificationProfile]:
        return self._base_query().filter(
            UserGamificationProfile.team_id == team_id
        ).all()

    def create(self, data: dict[str, Any]) -> UserGamificationProfile:
        entity = UserGamificationProfile(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: UserGamificationProfile, data: dict[str, Any]) -> UserGamificationProfile:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'user_id']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: UserGamificationProfile, deleted_by: UUID | None = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: UserGamificationProfile) -> UserGamificationProfile:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY TRANSACTIONS
# =============================================================================

class PointTransactionRepository(BaseRepository):
    """Repository pour les transactions de points."""

    def _base_query(self):
        return self.db.query(PointTransaction).filter(
            PointTransaction.tenant_id == self.tenant_id
        )

    def get_by_id(self, transaction_id: UUID) -> PointTransaction | None:
        return self._base_query().filter(PointTransaction.id == transaction_id).first()

    def get_by_user(
        self,
        user_id: UUID,
        filters: PointTransactionFilters | None = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[PointTransaction], int]:
        query = self._base_query().filter(PointTransaction.user_id == user_id)

        if filters:
            if filters.point_type:
                query = query.filter(PointTransaction.point_type == filters.point_type)
            if filters.transaction_type:
                query = query.filter(PointTransaction.transaction_type == filters.transaction_type)
            if filters.source:
                query = query.filter(PointTransaction.source == filters.source)
            if filters.date_from:
                query = query.filter(PointTransaction.created_at >= filters.date_from)
            if filters.date_to:
                query = query.filter(PointTransaction.created_at <= filters.date_to)

        total = query.count()
        query = query.order_by(desc(PointTransaction.created_at))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def get_sum_for_period(
        self,
        user_id: UUID,
        point_type: PointType,
        transaction_type: TransactionType,
        start_date: datetime,
        end_date: datetime | None = None
    ) -> int:
        query = self._base_query().filter(
            PointTransaction.user_id == user_id,
            PointTransaction.point_type == point_type,
            PointTransaction.transaction_type == transaction_type,
            PointTransaction.created_at >= start_date
        )
        if end_date:
            query = query.filter(PointTransaction.created_at <= end_date)

        result = query.with_entities(func.sum(PointTransaction.amount)).scalar()
        return result or 0

    def get_daily_total(self, user_id: UUID, point_type: PointType) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_sum_for_period(
            user_id,
            point_type,
            TransactionType.EARN,
            today_start
        )

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> PointTransaction:
        entity = PointTransaction(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def expire_points(self) -> int:
        """Expire les points qui ont depasse leur date d'expiration."""
        now = datetime.utcnow()
        count = self._base_query().filter(
            PointTransaction.expires_at != None,
            PointTransaction.expires_at <= now,
            PointTransaction.is_expired == False
        ).update({"is_expired": True})
        self.db.commit()
        return count


# =============================================================================
# REPOSITORY BADGES
# =============================================================================

class BadgeCategoryRepository(BaseRepository):
    """Repository pour les categories de badges."""

    def _base_query(self):
        return self.db.query(BadgeCategory).filter(
            BadgeCategory.tenant_id == self.tenant_id
        )

    def get_by_id(self, category_id: UUID) -> BadgeCategory | None:
        return self._base_query().filter(BadgeCategory.id == category_id).first()

    def get_by_code(self, code: str) -> BadgeCategory | None:
        return self._base_query().filter(BadgeCategory.code == code.upper()).first()

    def get_all_active(self) -> List[BadgeCategory]:
        return self._base_query().filter(
            BadgeCategory.is_active == True
        ).order_by(BadgeCategory.sort_order).all()

    def create(self, data: dict[str, Any]) -> BadgeCategory:
        data["code"] = data.get("code", "").upper()
        entity = BadgeCategory(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity


class BadgeRepository(BaseRepository):
    """Repository pour les badges."""

    def _base_query(self):
        query = self.db.query(GamificationBadge).filter(
            GamificationBadge.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(GamificationBadge.is_deleted == False)
        return query

    def get_by_id(self, badge_id: UUID) -> GamificationBadge | None:
        return self._base_query().filter(GamificationBadge.id == badge_id).first()

    def get_by_code(self, code: str) -> GamificationBadge | None:
        return self._base_query().filter(GamificationBadge.code == code.upper()).first()

    def list(
        self,
        filters: BadgeFilters | None = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[GamificationBadge], int]:
        query = self._base_query()
        now = datetime.utcnow()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    GamificationBadge.name.ilike(term),
                    GamificationBadge.code.ilike(term),
                    GamificationBadge.description.ilike(term)
                ))
            if filters.category_id:
                query = query.filter(GamificationBadge.category_id == filters.category_id)
            if filters.rarity:
                query = query.filter(GamificationBadge.rarity == filters.rarity)
            if not filters.include_secret:
                query = query.filter(GamificationBadge.is_secret == False)
            if filters.only_available:
                query = query.filter(
                    GamificationBadge.is_active == True,
                    or_(GamificationBadge.available_from == None, GamificationBadge.available_from <= now),
                    or_(GamificationBadge.available_until == None, GamificationBadge.available_until >= now)
                )

        total = query.count()
        query = query.order_by(GamificationBadge.rarity, GamificationBadge.name)
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        query = self._base_query().filter(GamificationBadge.code == code.upper())
        if exclude_id:
            query = query.filter(GamificationBadge.id != exclude_id)
        return query.count() > 0

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> GamificationBadge:
        data["code"] = data.get("code", "").upper()
        entity = GamificationBadge(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: GamificationBadge, data: dict[str, Any]) -> GamificationBadge:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'code']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def increment_holders(self, badge_id: UUID) -> None:
        self._base_query().filter(
            GamificationBadge.id == badge_id
        ).update({"current_holders": GamificationBadge.current_holders + 1})
        self.db.commit()

    def soft_delete(self, entity: GamificationBadge) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class UserBadgeRepository(BaseRepository):
    """Repository pour les badges utilisateur."""

    def _base_query(self):
        return self.db.query(UserBadge).filter(
            UserBadge.tenant_id == self.tenant_id
        )

    def get_by_id(self, user_badge_id: UUID) -> UserBadge | None:
        return self._base_query().filter(UserBadge.id == user_badge_id).first()

    def get_by_user_and_badge(self, user_id: UUID, badge_id: UUID) -> UserBadge | None:
        return self._base_query().filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id
        ).first()

    def get_by_user(
        self,
        user_id: UUID,
        status: BadgeStatus | None = None,
        include_badge: bool = True
    ) -> List[UserBadge]:
        query = self._base_query().filter(UserBadge.user_id == user_id)
        if status:
            query = query.filter(UserBadge.status == status)
        if include_badge:
            query = query.options(joinedload(UserBadge.badge))
        return query.order_by(desc(UserBadge.unlocked_at)).all()

    def get_recent_unlocks(self, user_id: UUID, limit: int = 5) -> List[UserBadge]:
        return self._base_query().filter(
            UserBadge.user_id == user_id,
            UserBadge.status == BadgeStatus.UNLOCKED
        ).options(
            joinedload(UserBadge.badge)
        ).order_by(desc(UserBadge.unlocked_at)).limit(limit).all()

    def count_by_user(self, user_id: UUID, status: BadgeStatus | None = None) -> int:
        query = self._base_query().filter(UserBadge.user_id == user_id)
        if status:
            query = query.filter(UserBadge.status == status)
        return query.count()

    def create(self, data: dict[str, Any]) -> UserBadge:
        entity = UserBadge(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: UserBadge, data: dict[str, Any]) -> UserBadge:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'user_id', 'badge_id']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY DEFIS
# =============================================================================

class ChallengeRepository(BaseRepository):
    """Repository pour les defis."""

    def _base_query(self):
        query = self.db.query(GamificationChallenge).filter(
            GamificationChallenge.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(GamificationChallenge.is_deleted == False)
        return query

    def get_by_id(self, challenge_id: UUID) -> GamificationChallenge | None:
        return self._base_query().filter(GamificationChallenge.id == challenge_id).first()

    def get_by_code(self, code: str) -> GamificationChallenge | None:
        return self._base_query().filter(GamificationChallenge.code == code.upper()).first()

    def list(
        self,
        filters: ChallengeFilters | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GamificationChallenge], int]:
        query = self._base_query()
        now = datetime.utcnow()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    GamificationChallenge.name.ilike(term),
                    GamificationChallenge.code.ilike(term),
                    GamificationChallenge.description.ilike(term)
                ))
            if filters.challenge_type:
                query = query.filter(GamificationChallenge.challenge_type == filters.challenge_type)
            if filters.status:
                query = query.filter(GamificationChallenge.status.in_(filters.status))
            if filters.is_team is not None:
                query = query.filter(GamificationChallenge.is_team_challenge == filters.is_team)
            if filters.only_available:
                query = query.filter(
                    GamificationChallenge.is_active == True,
                    GamificationChallenge.status.in_([ChallengeStatus.ACTIVE, ChallengeStatus.SCHEDULED]),
                    or_(GamificationChallenge.start_date == None, GamificationChallenge.start_date <= now),
                    or_(GamificationChallenge.end_date == None, GamificationChallenge.end_date >= now)
                )

        total = query.count()
        query = query.order_by(desc(GamificationChallenge.is_featured), GamificationChallenge.start_date)
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def get_active(self) -> List[GamificationChallenge]:
        now = datetime.utcnow()
        return self._base_query().filter(
            GamificationChallenge.status == ChallengeStatus.ACTIVE,
            GamificationChallenge.is_active == True,
            or_(GamificationChallenge.start_date == None, GamificationChallenge.start_date <= now),
            or_(GamificationChallenge.end_date == None, GamificationChallenge.end_date >= now)
        ).all()

    def code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        query = self._base_query().filter(GamificationChallenge.code == code.upper())
        if exclude_id:
            query = query.filter(GamificationChallenge.id != exclude_id)
        return query.count() > 0

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> GamificationChallenge:
        data["code"] = data.get("code", "").upper()
        entity = GamificationChallenge(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: GamificationChallenge, data: dict[str, Any]) -> GamificationChallenge:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'code']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def increment_participants(self, challenge_id: UUID) -> None:
        self._base_query().filter(
            GamificationChallenge.id == challenge_id
        ).update({"current_participants": GamificationChallenge.current_participants + 1})
        self.db.commit()

    def soft_delete(self, entity: GamificationChallenge) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class UserChallengeRepository(BaseRepository):
    """Repository pour les participations aux defis."""

    def _base_query(self):
        return self.db.query(UserChallenge).filter(
            UserChallenge.tenant_id == self.tenant_id
        )

    def get_by_id(self, user_challenge_id: UUID) -> UserChallenge | None:
        return self._base_query().filter(UserChallenge.id == user_challenge_id).first()

    def get_by_user_and_challenge(self, user_id: UUID, challenge_id: UUID) -> UserChallenge | None:
        return self._base_query().filter(
            UserChallenge.user_id == user_id,
            UserChallenge.challenge_id == challenge_id
        ).first()

    def get_by_user(
        self,
        user_id: UUID,
        status: ChallengeStatus | None = None,
        include_challenge: bool = True
    ) -> List[UserChallenge]:
        query = self._base_query().filter(UserChallenge.user_id == user_id)
        if status:
            query = query.filter(UserChallenge.status == status)
        if include_challenge:
            query = query.options(joinedload(UserChallenge.challenge))
        return query.order_by(desc(UserChallenge.joined_at)).all()

    def get_active_by_user(self, user_id: UUID) -> List[UserChallenge]:
        return self.get_by_user(user_id, ChallengeStatus.ACTIVE)

    def get_by_challenge(self, challenge_id: UUID) -> List[UserChallenge]:
        return self._base_query().filter(
            UserChallenge.challenge_id == challenge_id
        ).order_by(desc(UserChallenge.progress)).all()

    def count_by_user(self, user_id: UUID, status: ChallengeStatus | None = None) -> int:
        query = self._base_query().filter(UserChallenge.user_id == user_id)
        if status:
            query = query.filter(UserChallenge.status == status)
        return query.count()

    def create(self, data: dict[str, Any]) -> UserChallenge:
        entity = UserChallenge(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: UserChallenge, data: dict[str, Any]) -> UserChallenge:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'user_id', 'challenge_id']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY RECOMPENSES
# =============================================================================

class RewardRepository(BaseRepository):
    """Repository pour les recompenses."""

    def _base_query(self):
        query = self.db.query(GamificationReward).filter(
            GamificationReward.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(GamificationReward.is_deleted == False)
        return query

    def get_by_id(self, reward_id: UUID) -> GamificationReward | None:
        return self._base_query().filter(GamificationReward.id == reward_id).first()

    def get_by_code(self, code: str) -> GamificationReward | None:
        return self._base_query().filter(GamificationReward.code == code.upper()).first()

    def list(
        self,
        filters: RewardFilters | None = None,
        user_coins: int | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GamificationReward], int]:
        query = self._base_query()
        now = datetime.utcnow()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    GamificationReward.name.ilike(term),
                    GamificationReward.code.ilike(term),
                    GamificationReward.description.ilike(term)
                ))
            if filters.reward_type:
                query = query.filter(GamificationReward.reward_type == filters.reward_type)
            if filters.category:
                query = query.filter(GamificationReward.category == filters.category)
            if filters.min_cost is not None:
                query = query.filter(GamificationReward.cost_points >= filters.min_cost)
            if filters.max_cost is not None:
                query = query.filter(GamificationReward.cost_points <= filters.max_cost)
            if filters.affordable and user_coins is not None:
                query = query.filter(GamificationReward.cost_points <= user_coins)
            if filters.only_available:
                query = query.filter(
                    GamificationReward.is_active == True,
                    or_(GamificationReward.available_from == None, GamificationReward.available_from <= now),
                    or_(GamificationReward.available_until == None, GamificationReward.available_until >= now),
                    or_(
                        GamificationReward.stock == None,
                        GamificationReward.stock > GamificationReward.claimed_count
                    )
                )

        total = query.count()
        query = query.order_by(desc(GamificationReward.is_featured), GamificationReward.cost_points)
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        query = self._base_query().filter(GamificationReward.code == code.upper())
        if exclude_id:
            query = query.filter(GamificationReward.id != exclude_id)
        return query.count() > 0

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> GamificationReward:
        data["code"] = data.get("code", "").upper()
        entity = GamificationReward(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: GamificationReward, data: dict[str, Any]) -> GamificationReward:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'code']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def increment_claimed(self, reward_id: UUID) -> None:
        self._base_query().filter(
            GamificationReward.id == reward_id
        ).update({"claimed_count": GamificationReward.claimed_count + 1})
        self.db.commit()

    def soft_delete(self, entity: GamificationReward) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class RewardClaimRepository(BaseRepository):
    """Repository pour les reclamations de recompenses."""

    def _base_query(self):
        return self.db.query(RewardClaim).filter(
            RewardClaim.tenant_id == self.tenant_id
        )

    def get_by_id(self, claim_id: UUID) -> RewardClaim | None:
        return self._base_query().filter(RewardClaim.id == claim_id).first()

    def get_by_code(self, claim_code: str) -> RewardClaim | None:
        return self._base_query().filter(RewardClaim.claim_code == claim_code).first()

    def get_by_user(
        self,
        user_id: UUID,
        status: RewardStatus | None = None,
        include_reward: bool = True
    ) -> List[RewardClaim]:
        query = self._base_query().filter(RewardClaim.user_id == user_id)
        if status:
            query = query.filter(RewardClaim.status == status)
        if include_reward:
            query = query.options(joinedload(RewardClaim.reward))
        return query.order_by(desc(RewardClaim.claimed_at)).all()

    def count_user_claims_for_reward(
        self,
        user_id: UUID,
        reward_id: UUID,
        since: datetime | None = None
    ) -> int:
        query = self._base_query().filter(
            RewardClaim.user_id == user_id,
            RewardClaim.reward_id == reward_id
        )
        if since:
            query = query.filter(RewardClaim.claimed_at >= since)
        return query.count()

    def create(self, data: dict[str, Any]) -> RewardClaim:
        entity = RewardClaim(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: RewardClaim, data: dict[str, Any]) -> RewardClaim:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'user_id', 'reward_id']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY REGLES
# =============================================================================

class RuleRepository(BaseRepository):
    """Repository pour les regles."""

    def _base_query(self):
        query = self.db.query(GamificationRule).filter(
            GamificationRule.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(GamificationRule.is_deleted == False)
        return query

    def get_by_id(self, rule_id: UUID) -> GamificationRule | None:
        return self._base_query().filter(GamificationRule.id == rule_id).first()

    def get_by_code(self, code: str) -> GamificationRule | None:
        return self._base_query().filter(GamificationRule.code == code.upper()).first()

    def get_active_for_event(
        self,
        event_type: str,
        event_source: str | None = None
    ) -> List[GamificationRule]:
        now = datetime.utcnow()
        query = self._base_query().filter(
            GamificationRule.is_active == True,
            GamificationRule.event_type == event_type,
            or_(GamificationRule.valid_from == None, GamificationRule.valid_from <= now),
            or_(GamificationRule.valid_until == None, GamificationRule.valid_until >= now)
        )
        if event_source:
            query = query.filter(
                or_(GamificationRule.event_source == None, GamificationRule.event_source == event_source)
            )
        return query.order_by(desc(GamificationRule.priority)).all()

    def code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        query = self._base_query().filter(GamificationRule.code == code.upper())
        if exclude_id:
            query = query.filter(GamificationRule.id != exclude_id)
        return query.count() > 0

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> GamificationRule:
        data["code"] = data.get("code", "").upper()
        entity = GamificationRule(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: GamificationRule, data: dict[str, Any]) -> GamificationRule:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'code']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def increment_trigger_count(self, rule_id: UUID) -> None:
        now = datetime.utcnow()
        self._base_query().filter(
            GamificationRule.id == rule_id
        ).update({
            "trigger_count": GamificationRule.trigger_count + 1,
            "last_triggered_at": now
        })
        self.db.commit()

    def soft_delete(self, entity: GamificationRule) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class RuleTriggerLogRepository(BaseRepository):
    """Repository pour les logs de declenchement."""

    def _base_query(self):
        return self.db.query(RuleTriggerLog).filter(
            RuleTriggerLog.tenant_id == self.tenant_id
        )

    def get_by_user_and_rule(
        self,
        user_id: UUID,
        rule_id: UUID,
        since: datetime | None = None
    ) -> List[RuleTriggerLog]:
        query = self._base_query().filter(
            RuleTriggerLog.user_id == user_id,
            RuleTriggerLog.rule_id == rule_id
        )
        if since:
            query = query.filter(RuleTriggerLog.triggered_at >= since)
        return query.all()

    def count_triggers_today(self, user_id: UUID, rule_id: UUID) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return self._base_query().filter(
            RuleTriggerLog.user_id == user_id,
            RuleTriggerLog.rule_id == rule_id,
            RuleTriggerLog.triggered_at >= today_start
        ).count()

    def get_last_trigger(self, user_id: UUID, rule_id: UUID) -> RuleTriggerLog | None:
        return self._base_query().filter(
            RuleTriggerLog.user_id == user_id,
            RuleTriggerLog.rule_id == rule_id
        ).order_by(desc(RuleTriggerLog.triggered_at)).first()

    def create(self, data: dict[str, Any]) -> RuleTriggerLog:
        entity = RuleTriggerLog(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY EQUIPES
# =============================================================================

class TeamRepository(BaseRepository):
    """Repository pour les equipes."""

    def _base_query(self):
        query = self.db.query(GamificationTeam).filter(
            GamificationTeam.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(GamificationTeam.is_deleted == False)
        return query

    def get_by_id(self, team_id: UUID) -> GamificationTeam | None:
        return self._base_query().filter(GamificationTeam.id == team_id).first()

    def get_by_code(self, code: str) -> GamificationTeam | None:
        return self._base_query().filter(GamificationTeam.code == code.upper()).first()

    def list(
        self,
        search: str | None = None,
        public_only: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GamificationTeam], int]:
        query = self._base_query().filter(GamificationTeam.is_active == True)

        if search:
            term = f"%{search}%"
            query = query.filter(or_(
                GamificationTeam.name.ilike(term),
                GamificationTeam.code.ilike(term)
            ))
        if public_only:
            query = query.filter(GamificationTeam.is_public == True)

        total = query.count()
        query = query.order_by(desc(GamificationTeam.total_points))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        query = self._base_query().filter(GamificationTeam.code == code.upper())
        if exclude_id:
            query = query.filter(GamificationTeam.id != exclude_id)
        return query.count() > 0

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> GamificationTeam:
        data["code"] = data.get("code", "").upper()
        entity = GamificationTeam(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: GamificationTeam, data: dict[str, Any]) -> GamificationTeam:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'code']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_stats(self, team_id: UUID, points_delta: int = 0, badges_delta: int = 0) -> None:
        updates = {}
        if points_delta:
            updates["total_points"] = GamificationTeam.total_points + points_delta
        if badges_delta:
            updates["total_badges"] = GamificationTeam.total_badges + badges_delta
        if updates:
            self._base_query().filter(GamificationTeam.id == team_id).update(updates)
            self.db.commit()

    def soft_delete(self, entity: GamificationTeam) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class TeamMembershipRepository(BaseRepository):
    """Repository pour les appartenances aux equipes."""

    def _base_query(self):
        return self.db.query(TeamMembership).filter(
            TeamMembership.tenant_id == self.tenant_id
        )

    def get_by_user(self, user_id: UUID, active_only: bool = True) -> List[TeamMembership]:
        query = self._base_query().filter(TeamMembership.user_id == user_id)
        if active_only:
            query = query.filter(TeamMembership.is_active == True)
        return query.all()

    def get_active_by_user(self, user_id: UUID) -> TeamMembership | None:
        return self._base_query().filter(
            TeamMembership.user_id == user_id,
            TeamMembership.is_active == True
        ).first()

    def get_by_team(self, team_id: UUID, active_only: bool = True) -> List[TeamMembership]:
        query = self._base_query().filter(TeamMembership.team_id == team_id)
        if active_only:
            query = query.filter(TeamMembership.is_active == True)
        return query.order_by(TeamMembership.role, TeamMembership.joined_at).all()

    def count_active_members(self, team_id: UUID) -> int:
        return self._base_query().filter(
            TeamMembership.team_id == team_id,
            TeamMembership.is_active == True
        ).count()

    def create(self, data: dict[str, Any]) -> TeamMembership:
        entity = TeamMembership(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: TeamMembership, data: dict[str, Any]) -> TeamMembership:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'user_id', 'team_id']:
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def deactivate(self, entity: TeamMembership) -> TeamMembership:
        entity.is_active = False
        entity.left_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY COMPETITIONS
# =============================================================================

class CompetitionRepository(BaseRepository):
    """Repository pour les competitions."""

    def _base_query(self):
        query = self.db.query(GamificationCompetition).filter(
            GamificationCompetition.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(GamificationCompetition.is_deleted == False)
        return query

    def get_by_id(self, competition_id: UUID) -> GamificationCompetition | None:
        return self._base_query().filter(GamificationCompetition.id == competition_id).first()

    def get_by_code(self, code: str) -> GamificationCompetition | None:
        return self._base_query().filter(GamificationCompetition.code == code.upper()).first()

    def list(
        self,
        status: List[CompetitionStatus] | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GamificationCompetition], int]:
        query = self._base_query().filter(GamificationCompetition.is_active == True)

        if status:
            query = query.filter(GamificationCompetition.status.in_(status))

        total = query.count()
        query = query.order_by(desc(GamificationCompetition.is_featured), GamificationCompetition.start_date)
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        query = self._base_query().filter(GamificationCompetition.code == code.upper())
        if exclude_id:
            query = query.filter(GamificationCompetition.id != exclude_id)
        return query.count() > 0

    def create(self, data: dict[str, Any], created_by: UUID | None = None) -> GamificationCompetition:
        data["code"] = data.get("code", "").upper()
        entity = GamificationCompetition(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: GamificationCompetition, data: dict[str, Any]) -> GamificationCompetition:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'code']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: GamificationCompetition) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class CompetitionParticipantRepository(BaseRepository):
    """Repository pour les participants aux competitions."""

    def _base_query(self):
        return self.db.query(CompetitionParticipant).filter(
            CompetitionParticipant.tenant_id == self.tenant_id
        )

    def get_by_competition(
        self,
        competition_id: UUID,
        active_only: bool = True
    ) -> List[CompetitionParticipant]:
        query = self._base_query().filter(CompetitionParticipant.competition_id == competition_id)
        if active_only:
            query = query.filter(CompetitionParticipant.is_active == True)
        return query.order_by(CompetitionParticipant.current_rank).all()

    def get_by_user(self, user_id: UUID, competition_id: UUID) -> CompetitionParticipant | None:
        return self._base_query().filter(
            CompetitionParticipant.user_id == user_id,
            CompetitionParticipant.competition_id == competition_id
        ).first()

    def create(self, data: dict[str, Any]) -> CompetitionParticipant:
        entity = CompetitionParticipant(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: CompetitionParticipant, data: dict[str, Any]) -> CompetitionParticipant:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY LEADERBOARDS
# =============================================================================

class LeaderboardRepository(BaseRepository):
    """Repository pour les classements."""

    def _base_query(self):
        return self.db.query(Leaderboard).filter(
            Leaderboard.tenant_id == self.tenant_id
        )

    def get_by_id(self, leaderboard_id: UUID) -> Leaderboard | None:
        return self._base_query().filter(Leaderboard.id == leaderboard_id).first()

    def get_by_code(self, code: str) -> Leaderboard | None:
        return self._base_query().filter(Leaderboard.code == code.upper()).first()

    def get_default(self, period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME) -> Leaderboard | None:
        return self._base_query().filter(
            Leaderboard.period == period,
            Leaderboard.is_active == True,
            Leaderboard.is_featured == True
        ).first()

    def list_active(self) -> List[Leaderboard]:
        return self._base_query().filter(
            Leaderboard.is_active == True
        ).order_by(desc(Leaderboard.is_featured), Leaderboard.name).all()

    def create(self, data: dict[str, Any]) -> Leaderboard:
        data["code"] = data.get("code", "").upper()
        entity = Leaderboard(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Leaderboard, data: dict[str, Any]) -> Leaderboard:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'code']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity


class LeaderboardEntryRepository(BaseRepository):
    """Repository pour les entrees de classement."""

    def _base_query(self):
        return self.db.query(LeaderboardEntry).filter(
            LeaderboardEntry.tenant_id == self.tenant_id
        )

    def get_entries(
        self,
        leaderboard_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[LeaderboardEntry]:
        return self._base_query().filter(
            LeaderboardEntry.leaderboard_id == leaderboard_id
        ).order_by(LeaderboardEntry.rank).offset(offset).limit(limit).all()

    def get_user_entry(self, leaderboard_id: UUID, user_id: UUID) -> LeaderboardEntry | None:
        return self._base_query().filter(
            LeaderboardEntry.leaderboard_id == leaderboard_id,
            LeaderboardEntry.user_id == user_id
        ).first()

    def clear_entries(self, leaderboard_id: UUID) -> int:
        count = self._base_query().filter(
            LeaderboardEntry.leaderboard_id == leaderboard_id
        ).delete()
        self.db.commit()
        return count

    def create_many(self, entries: List[dict[str, Any]]) -> int:
        for entry_data in entries:
            entry = LeaderboardEntry(tenant_id=self.tenant_id, **entry_data)
            self.db.add(entry)
        self.db.commit()
        return len(entries)


# =============================================================================
# REPOSITORY NOTIFICATIONS
# =============================================================================

class NotificationRepository(BaseRepository):
    """Repository pour les notifications."""

    def _base_query(self):
        return self.db.query(GamificationNotification).filter(
            GamificationNotification.tenant_id == self.tenant_id
        )

    def get_by_id(self, notification_id: UUID) -> GamificationNotification | None:
        return self._base_query().filter(GamificationNotification.id == notification_id).first()

    def get_by_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        notification_type: NotificationType | None = None,
        limit: int = 50
    ) -> List[GamificationNotification]:
        query = self._base_query().filter(
            GamificationNotification.user_id == user_id,
            GamificationNotification.is_dismissed == False
        )
        if unread_only:
            query = query.filter(GamificationNotification.is_read == False)
        if notification_type:
            query = query.filter(GamificationNotification.notification_type == notification_type)

        return query.order_by(desc(GamificationNotification.created_at)).limit(limit).all()

    def count_unread(self, user_id: UUID) -> int:
        return self._base_query().filter(
            GamificationNotification.user_id == user_id,
            GamificationNotification.is_read == False,
            GamificationNotification.is_dismissed == False
        ).count()

    def create(self, data: dict[str, Any]) -> GamificationNotification:
        entity = GamificationNotification(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def mark_as_read(self, notification_ids: List[UUID], user_id: UUID) -> int:
        now = datetime.utcnow()
        count = self._base_query().filter(
            GamificationNotification.id.in_(notification_ids),
            GamificationNotification.user_id == user_id
        ).update({"is_read": True, "read_at": now}, synchronize_session=False)
        self.db.commit()
        return count

    def mark_all_as_read(self, user_id: UUID) -> int:
        now = datetime.utcnow()
        count = self._base_query().filter(
            GamificationNotification.user_id == user_id,
            GamificationNotification.is_read == False
        ).update({"is_read": True, "read_at": now}, synchronize_session=False)
        self.db.commit()
        return count


# =============================================================================
# REPOSITORY ACTIVITES
# =============================================================================

class ActivityRepository(BaseRepository):
    """Repository pour l'historique d'activite."""

    def _base_query(self):
        return self.db.query(GamificationActivity).filter(
            GamificationActivity.tenant_id == self.tenant_id
        )

    def get_by_user(
        self,
        user_id: UUID,
        filters: ActivityFilters | None = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[GamificationActivity], int]:
        query = self._base_query().filter(GamificationActivity.user_id == user_id)

        if filters:
            if filters.activity_type:
                query = query.filter(GamificationActivity.activity_type == filters.activity_type)
            if filters.source_module:
                query = query.filter(GamificationActivity.source_module == filters.source_module)
            if filters.date_from:
                query = query.filter(GamificationActivity.created_at >= filters.date_from)
            if filters.date_to:
                query = query.filter(GamificationActivity.created_at <= filters.date_to)
            if filters.public_only:
                query = query.filter(GamificationActivity.is_public == True)

        total = query.count()
        query = query.order_by(desc(GamificationActivity.created_at))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def get_recent(self, user_id: UUID, limit: int = 10) -> List[GamificationActivity]:
        return self._base_query().filter(
            GamificationActivity.user_id == user_id
        ).order_by(desc(GamificationActivity.created_at)).limit(limit).all()

    def create(self, data: dict[str, Any]) -> GamificationActivity:
        entity = GamificationActivity(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY STREAKS
# =============================================================================

class StreakRepository(BaseRepository):
    """Repository pour les streaks."""

    def _base_query(self):
        return self.db.query(GamificationStreak).filter(
            GamificationStreak.tenant_id == self.tenant_id
        )

    def get_by_user(self, user_id: UUID) -> List[GamificationStreak]:
        return self._base_query().filter(GamificationStreak.user_id == user_id).all()

    def get_by_user_and_type(self, user_id: UUID, streak_type: str) -> GamificationStreak | None:
        return self._base_query().filter(
            GamificationStreak.user_id == user_id,
            GamificationStreak.streak_type == streak_type
        ).first()

    def get_or_create(self, user_id: UUID, streak_type: str) -> Tuple[GamificationStreak, bool]:
        streak = self.get_by_user_and_type(user_id, streak_type)
        if streak:
            return streak, False

        streak = GamificationStreak(
            tenant_id=self.tenant_id,
            user_id=user_id,
            streak_type=streak_type
        )
        self.db.add(streak)
        self.db.commit()
        self.db.refresh(streak)
        return streak, True

    def update(self, entity: GamificationStreak, data: dict[str, Any]) -> GamificationStreak:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id', 'user_id', 'streak_type']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity


# =============================================================================
# REPOSITORY CONFIGURATION
# =============================================================================

class ConfigRepository(BaseRepository):
    """Repository pour la configuration."""

    def _base_query(self):
        return self.db.query(GamificationConfig).filter(
            GamificationConfig.tenant_id == self.tenant_id
        )

    def get(self) -> GamificationConfig | None:
        return self._base_query().first()

    def get_or_create(self) -> Tuple[GamificationConfig, bool]:
        config = self.get()
        if config:
            return config, False

        config = GamificationConfig(tenant_id=self.tenant_id)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config, True

    def update(self, entity: GamificationConfig, data: dict[str, Any]) -> GamificationConfig:
        for key, value in data.items():
            if hasattr(entity, key) and key not in ['id', 'tenant_id']:
                setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity
