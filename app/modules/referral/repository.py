"""
Repository Referral / Parrainage
=================================
- CRITIQUE: Toutes les requêtes filtrées par tenant_id
- Optimisations et cache
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from .models import (
    ReferralProgram, ProgramStatus,
    RewardTier,
    ReferralCode,
    Referral, ReferralStatus,
    Reward, RewardType,
    Payout, PayoutStatus,
    FraudCheck
)
from .schemas import ProgramFilters, ReferralFilters, PayoutFilters


class BaseTenantRepository:
    """Repository de base avec isolation tenant."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted


class ProgramRepository(BaseTenantRepository):
    """Repository pour ReferralProgram."""

    def _base_query(self):
        query = self.db.query(ReferralProgram).filter(
            ReferralProgram.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ReferralProgram.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ReferralProgram]:
        return self._base_query().filter(ReferralProgram.id == id).first()

    def get_by_code(self, code: str) -> Optional[ReferralProgram]:
        return self._base_query().filter(
            ReferralProgram.code == code.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(ReferralProgram.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ReferralProgram.code == code.upper())
        if exclude_id:
            query = query.filter(ReferralProgram.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: ProgramFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ReferralProgram], int]:
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        sort_col = getattr(ReferralProgram, sort_by, ReferralProgram.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: ProgramFilters):
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(or_(
                ReferralProgram.name.ilike(term),
                ReferralProgram.code.ilike(term),
                ReferralProgram.description.ilike(term)
            ))

        if filters.status:
            query = query.filter(ReferralProgram.status.in_(filters.status))

        if filters.tags:
            query = query.filter(ReferralProgram.tags.overlap(filters.tags))

        if filters.date_from:
            query = query.filter(ReferralProgram.created_at >= filters.date_from)

        if filters.date_to:
            query = query.filter(ReferralProgram.created_at <= filters.date_to)

        return query

    def get_active_programs(self) -> List[ReferralProgram]:
        """Retourne les programmes actifs."""
        return self._base_query().filter(
            ReferralProgram.status == ProgramStatus.ACTIVE
        ).all()

    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []

        query = self._base_query().filter(
            ReferralProgram.status == ProgramStatus.ACTIVE
        )

        if field == "code":
            query = query.filter(ReferralProgram.code.ilike(f"{prefix}%"))
        else:
            query = query.filter(or_(
                ReferralProgram.name.ilike(f"{prefix}%"),
                ReferralProgram.code.ilike(f"{prefix}%")
            ))

        results = query.order_by(ReferralProgram.name).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": f"[{item.code}] {item.name}"
            }
            for item in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ReferralProgram:
        program = ReferralProgram(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(program)
        self.db.commit()
        self.db.refresh(program)
        return program

    def update(
        self,
        program: ReferralProgram,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ReferralProgram:
        for key, value in data.items():
            if hasattr(program, key):
                setattr(program, key, value)
        program.updated_by = updated_by
        self.db.commit()
        self.db.refresh(program)
        return program

    def soft_delete(self, program: ReferralProgram, deleted_by: UUID = None) -> bool:
        program.is_deleted = True
        program.deleted_at = datetime.utcnow()
        program.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, program: ReferralProgram) -> ReferralProgram:
        program.is_deleted = False
        program.deleted_at = None
        program.deleted_by = None
        self.db.commit()
        self.db.refresh(program)
        return program

    def get_stats(self) -> Dict[str, Any]:
        base = self._base_query()
        total = base.count()
        by_status = {}
        for status in ProgramStatus:
            by_status[status.value] = base.filter(
                ReferralProgram.status == status
            ).count()
        return {"total": total, "by_status": by_status}


class RewardTierRepository(BaseTenantRepository):
    """Repository pour RewardTier."""

    def _base_query(self):
        query = self.db.query(RewardTier).filter(
            RewardTier.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(RewardTier.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[RewardTier]:
        return self._base_query().filter(RewardTier.id == id).first()

    def list_for_program(self, program_id: UUID) -> List[RewardTier]:
        return self._base_query().filter(
            RewardTier.program_id == program_id
        ).order_by(RewardTier.priority, RewardTier.min_referrals).all()

    def get_applicable_tier(
        self,
        program_id: UUID,
        referral_count: int,
        conversion_amount: Decimal = Decimal("0")
    ) -> Optional[RewardTier]:
        """Retourne le palier applicable pour un nombre de parrainages."""
        tiers = self.list_for_program(program_id)
        applicable = None
        for tier in tiers:
            if not tier.is_active:
                continue
            if tier.max_uses and tier.current_uses >= tier.max_uses:
                continue
            if referral_count >= tier.min_referrals:
                if tier.max_referrals is None or referral_count <= tier.max_referrals:
                    if conversion_amount >= tier.min_conversion_amount:
                        applicable = tier
        return applicable

    def create(self, program_id: UUID, data: Dict[str, Any]) -> RewardTier:
        tier = RewardTier(
            tenant_id=self.tenant_id,
            program_id=program_id,
            **data
        )
        self.db.add(tier)
        self.db.commit()
        self.db.refresh(tier)
        return tier

    def update(self, tier: RewardTier, data: Dict[str, Any]) -> RewardTier:
        for key, value in data.items():
            if hasattr(tier, key):
                setattr(tier, key, value)
        tier.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(tier)
        return tier

    def delete(self, tier: RewardTier) -> bool:
        tier.is_deleted = True
        tier.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class ReferralCodeRepository(BaseTenantRepository):
    """Repository pour ReferralCode."""

    def _base_query(self):
        query = self.db.query(ReferralCode).filter(
            ReferralCode.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(ReferralCode.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ReferralCode]:
        return self._base_query().filter(ReferralCode.id == id).first()

    def get_by_code(self, code: str) -> Optional[ReferralCode]:
        return self._base_query().filter(
            ReferralCode.code == code.upper()
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ReferralCode.code == code.upper())
        if exclude_id:
            query = query.filter(ReferralCode.id != exclude_id)
        return query.count() > 0

    def list_for_referrer(self, referrer_id: UUID) -> List[ReferralCode]:
        return self._base_query().filter(
            ReferralCode.referrer_id == referrer_id
        ).order_by(ReferralCode.created_at.desc()).all()

    def list_for_program(
        self,
        program_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ReferralCode], int]:
        query = self._base_query().filter(ReferralCode.program_id == program_id)
        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(ReferralCode.created_at.desc()).offset(offset).limit(page_size).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> ReferralCode:
        code = ReferralCode(tenant_id=self.tenant_id, **data)
        self.db.add(code)
        self.db.commit()
        self.db.refresh(code)
        return code

    def update(self, code: ReferralCode, data: Dict[str, Any]) -> ReferralCode:
        for key, value in data.items():
            if hasattr(code, key):
                setattr(code, key, value)
        self.db.commit()
        self.db.refresh(code)
        return code

    def increment_stats(
        self,
        code: ReferralCode,
        clicks: int = 0,
        signups: int = 0,
        conversions: int = 0,
        earnings: Decimal = Decimal("0")
    ) -> ReferralCode:
        code.total_clicks += clicks
        code.total_signups += signups
        code.total_conversions += conversions
        code.total_earnings += earnings
        code.current_uses += 1
        code.last_used_at = datetime.utcnow()
        self.db.commit()
        return code

    def delete(self, code: ReferralCode) -> bool:
        code.is_deleted = True
        code.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class ReferralRepository(BaseTenantRepository):
    """Repository pour Referral."""

    def _base_query(self):
        query = self.db.query(Referral).filter(
            Referral.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Referral.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Referral]:
        return self._base_query().filter(Referral.id == id).first()

    def list(
        self,
        filters: ReferralFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Referral], int]:
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        sort_col = getattr(Referral, sort_by, Referral.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: ReferralFilters):
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(or_(
                Referral.referee_email.ilike(term),
                Referral.referee_name.ilike(term)
            ))

        if filters.program_id:
            query = query.filter(Referral.program_id == filters.program_id)

        if filters.referrer_id:
            query = query.filter(Referral.referrer_id == filters.referrer_id)

        if filters.referee_id:
            query = query.filter(Referral.referee_id == filters.referee_id)

        if filters.status:
            query = query.filter(Referral.status.in_(filters.status))

        if filters.is_suspicious is not None:
            query = query.filter(Referral.is_suspicious == filters.is_suspicious)

        if filters.date_from:
            query = query.filter(Referral.created_at >= filters.date_from)

        if filters.date_to:
            query = query.filter(Referral.created_at <= filters.date_to)

        return query

    def list_for_referrer(
        self,
        referrer_id: UUID,
        status: List[ReferralStatus] = None
    ) -> List[Referral]:
        query = self._base_query().filter(Referral.referrer_id == referrer_id)
        if status:
            query = query.filter(Referral.status.in_(status))
        return query.order_by(Referral.created_at.desc()).all()

    def count_for_referrer(
        self,
        referrer_id: UUID,
        program_id: UUID = None,
        status: List[ReferralStatus] = None
    ) -> int:
        query = self._base_query().filter(Referral.referrer_id == referrer_id)
        if program_id:
            query = query.filter(Referral.program_id == program_id)
        if status:
            query = query.filter(Referral.status.in_(status))
        return query.count()

    def referee_exists(
        self,
        program_id: UUID,
        referee_email: str,
        exclude_id: UUID = None
    ) -> bool:
        """Vérifie si un email est déjà parrainé dans ce programme."""
        query = self._base_query().filter(
            Referral.program_id == program_id,
            Referral.referee_email == referee_email.lower()
        )
        if exclude_id:
            query = query.filter(Referral.id != exclude_id)
        return query.count() > 0

    def create(self, data: Dict[str, Any]) -> Referral:
        referral = Referral(tenant_id=self.tenant_id, **data)
        self.db.add(referral)
        self.db.commit()
        self.db.refresh(referral)
        return referral

    def update(self, referral: Referral, data: Dict[str, Any]) -> Referral:
        for key, value in data.items():
            if hasattr(referral, key):
                setattr(referral, key, value)
        referral.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(referral)
        return referral

    def get_stats(self, program_id: UUID = None) -> Dict[str, Any]:
        query = self._base_query()
        if program_id:
            query = query.filter(Referral.program_id == program_id)

        total = query.count()
        by_status = {}
        for status in ReferralStatus:
            by_status[status.value] = query.filter(
                Referral.status == status
            ).count()

        total_value = query.filter(
            Referral.status == ReferralStatus.CONVERTED
        ).with_entities(func.sum(Referral.conversion_amount)).scalar() or Decimal("0")

        return {
            "total": total,
            "by_status": by_status,
            "total_conversion_value": float(total_value)
        }


class RewardRepository(BaseTenantRepository):
    """Repository pour Reward."""

    def _base_query(self):
        query = self.db.query(Reward).filter(
            Reward.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Reward.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Reward]:
        return self._base_query().filter(Reward.id == id).first()

    def list_for_user(
        self,
        user_id: UUID,
        is_claimed: bool = None
    ) -> List[Reward]:
        query = self._base_query().filter(Reward.user_id == user_id)
        if is_claimed is not None:
            query = query.filter(Reward.is_claimed == is_claimed)
        return query.order_by(Reward.created_at.desc()).all()

    def list_for_referral(self, referral_id: UUID) -> List[Reward]:
        return self._base_query().filter(
            Reward.referral_id == referral_id
        ).all()

    def list_unclaimed_for_user(self, user_id: UUID) -> List[Reward]:
        return self._base_query().filter(
            Reward.user_id == user_id,
            Reward.is_claimed == False,
            or_(
                Reward.expires_at.is_(None),
                Reward.expires_at > datetime.utcnow()
            )
        ).all()

    def get_total_earnings(self, user_id: UUID) -> Dict[str, Decimal]:
        total = self._base_query().filter(
            Reward.user_id == user_id,
            Reward.is_referrer_reward == True
        ).with_entities(func.sum(Reward.reward_value)).scalar() or Decimal("0")

        claimed = self._base_query().filter(
            Reward.user_id == user_id,
            Reward.is_referrer_reward == True,
            Reward.is_claimed == True
        ).with_entities(func.sum(Reward.reward_value)).scalar() or Decimal("0")

        pending = total - claimed

        return {
            "total": total,
            "claimed": claimed,
            "pending": pending
        }

    def create(self, data: Dict[str, Any]) -> Reward:
        reward = Reward(tenant_id=self.tenant_id, **data)
        self.db.add(reward)
        self.db.commit()
        self.db.refresh(reward)
        return reward

    def update(self, reward: Reward, data: Dict[str, Any]) -> Reward:
        for key, value in data.items():
            if hasattr(reward, key):
                setattr(reward, key, value)
        self.db.commit()
        self.db.refresh(reward)
        return reward

    def claim(self, reward: Reward) -> Reward:
        reward.is_claimed = True
        reward.claimed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(reward)
        return reward


class PayoutRepository(BaseTenantRepository):
    """Repository pour Payout."""

    def _base_query(self):
        query = self.db.query(Payout).filter(
            Payout.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Payout.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Payout]:
        return self._base_query().filter(Payout.id == id).first()

    def list(
        self,
        filters: PayoutFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Payout], int]:
        query = self._base_query()

        if filters:
            if filters.user_id:
                query = query.filter(Payout.user_id == filters.user_id)
            if filters.status:
                query = query.filter(Payout.status.in_(filters.status))
            if filters.date_from:
                query = query.filter(Payout.created_at >= filters.date_from)
            if filters.date_to:
                query = query.filter(Payout.created_at <= filters.date_to)

        total = query.count()

        sort_col = getattr(Payout, sort_by, Payout.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def list_for_user(self, user_id: UUID) -> List[Payout]:
        return self._base_query().filter(
            Payout.user_id == user_id
        ).order_by(Payout.created_at.desc()).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Payout:
        payout = Payout(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(payout)
        self.db.commit()
        self.db.refresh(payout)
        return payout

    def update(self, payout: Payout, data: Dict[str, Any]) -> Payout:
        for key, value in data.items():
            if hasattr(payout, key):
                setattr(payout, key, value)
        payout.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payout)
        return payout

    def process(self, payout: Payout, transaction_reference: str) -> Payout:
        payout.status = PayoutStatus.PAID
        payout.processed_at = datetime.utcnow()
        payout.transaction_reference = transaction_reference
        self.db.commit()
        self.db.refresh(payout)
        return payout


class FraudCheckRepository(BaseTenantRepository):
    """Repository pour FraudCheck."""

    def _base_query(self):
        return self.db.query(FraudCheck).filter(
            FraudCheck.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[FraudCheck]:
        return self._base_query().filter(FraudCheck.id == id).first()

    def list_for_referral(self, referral_id: UUID) -> List[FraudCheck]:
        return self._base_query().filter(
            FraudCheck.referral_id == referral_id
        ).order_by(FraudCheck.created_at.desc()).all()

    def create(self, data: Dict[str, Any]) -> FraudCheck:
        check = FraudCheck(tenant_id=self.tenant_id, **data)
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check

    def get_similar_ip_count(
        self,
        ip_address: str,
        hours: int = 24,
        exclude_id: UUID = None
    ) -> int:
        """Compte les referrals avec la même IP récemment."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(Referral).filter(
            Referral.tenant_id == self.tenant_id,
            Referral.ip_address == ip_address,
            Referral.created_at >= cutoff
        )
        if exclude_id:
            query = query.filter(Referral.id != exclude_id)
        return query.count()

    def get_similar_device_count(
        self,
        device_fingerprint: str,
        hours: int = 24,
        exclude_id: UUID = None
    ) -> int:
        """Compte les referrals avec le même device récemment."""
        if not device_fingerprint:
            return 0
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(Referral).filter(
            Referral.tenant_id == self.tenant_id,
            Referral.device_fingerprint == device_fingerprint,
            Referral.created_at >= cutoff
        )
        if exclude_id:
            query = query.filter(Referral.id != exclude_id)
        return query.count()


# Import timedelta at module level
from datetime import timedelta
