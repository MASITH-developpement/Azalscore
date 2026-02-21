"""
Service Referral / Parrainage
==============================
- Logique métier
- Orchestration des repositories
- Validation des règles
- Détection de fraude
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    ReferralProgram, ProgramStatus,
    RewardTier, RewardType,
    ReferralCode,
    Referral, ReferralStatus,
    Reward,
    Payout, PayoutStatus,
    FraudCheck, FraudReason
)
from .repository import (
    ProgramRepository, RewardTierRepository, ReferralCodeRepository,
    ReferralRepository, RewardRepository, PayoutRepository, FraudCheckRepository
)
from .schemas import (
    ReferralProgramCreate, ReferralProgramUpdate, ProgramFilters,
    RewardTierCreate, RewardTierUpdate,
    ReferralCodeCreate, ReferralCodeUpdate,
    ReferralCreate, ReferralUpdate, ReferralFilters,
    RewardCreate,
    PayoutCreate, PayoutUpdate, PayoutFilters,
    FraudCheckCreate,
    TrackClickRequest, TrackSignupRequest, TrackConversionRequest,
    ReferralStats, ReferrerProfile
)
from .exceptions import (
    ProgramNotFoundError, ProgramDuplicateError, ProgramValidationError,
    ProgramStateError, ProgramBudgetExceededError, ProgramLimitReachedError,
    RewardTierNotFoundError, RewardTierValidationError,
    ReferralCodeNotFoundError, ReferralCodeDuplicateError,
    ReferralCodeExpiredError, ReferralCodeLimitReachedError, ReferralCodeInactiveError,
    ReferralNotFoundError, ReferralValidationError, ReferralStateError,
    ReferralExpiredError, SelfReferralError, DuplicateRefereeError,
    RewardNotFoundError, RewardAlreadyClaimedError, RewardExpiredError,
    PayoutNotFoundError, PayoutValidationError, PayoutStateError,
    FraudDetectedError
)


class ReferralService:
    """
    Service métier Referral.
    Encapsule toute la logique métier.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Repositories
        self.program_repo = ProgramRepository(db, tenant_id)
        self.tier_repo = RewardTierRepository(db, tenant_id)
        self.code_repo = ReferralCodeRepository(db, tenant_id)
        self.referral_repo = ReferralRepository(db, tenant_id)
        self.reward_repo = RewardRepository(db, tenant_id)
        self.payout_repo = PayoutRepository(db, tenant_id)
        self.fraud_repo = FraudCheckRepository(db, tenant_id)

    # ================== Programs ==================

    def get_program(self, id: UUID) -> ReferralProgram:
        """Récupère un programme par ID."""
        program = self.program_repo.get_by_id(id)
        if not program:
            raise ProgramNotFoundError(f"Program {id} not found")
        return program

    def get_program_by_code(self, code: str) -> ReferralProgram:
        """Récupère un programme par code."""
        program = self.program_repo.get_by_code(code)
        if not program:
            raise ProgramNotFoundError(f"Program code={code} not found")
        return program

    def list_programs(
        self,
        filters: ProgramFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ReferralProgram], int, int]:
        """Liste paginée des programmes."""
        items, total = self.program_repo.list(filters, page, page_size, sort_by, sort_dir)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def create_program(self, data: ReferralProgramCreate) -> ReferralProgram:
        """Crée un nouveau programme."""
        if self.program_repo.code_exists(data.code):
            raise ProgramDuplicateError(f"Code {data.code} already exists")

        program_data = data.model_dump(exclude={'tiers'})
        program = self.program_repo.create(program_data, self.user_id)

        # Créer les paliers
        for tier_data in data.tiers:
            self.tier_repo.create(program.id, tier_data.model_dump())

        self.db.refresh(program)
        return program

    def update_program(self, id: UUID, data: ReferralProgramUpdate) -> ReferralProgram:
        """Met à jour un programme."""
        program = self.get_program(id)

        # Vérifier transition de statut
        if data.status and data.status != program.status:
            allowed = ProgramStatus.allowed_transitions().get(program.status, [])
            if data.status not in allowed:
                raise ProgramStateError(
                    f"Transition {program.status} -> {data.status} not allowed"
                )

        return self.program_repo.update(
            program,
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def delete_program(self, id: UUID, hard: bool = False) -> bool:
        """Supprime un programme."""
        program = self.get_program(id)

        can_delete, reason = program.can_delete()
        if not can_delete:
            raise ProgramValidationError(reason)

        if hard:
            self.db.delete(program)
            self.db.commit()
            return True
        return self.program_repo.soft_delete(program, self.user_id)

    def activate_program(self, id: UUID) -> ReferralProgram:
        """Active un programme."""
        program = self.get_program(id)

        if program.status not in [ProgramStatus.DRAFT, ProgramStatus.PAUSED]:
            raise ProgramStateError(f"Cannot activate program in status {program.status}")

        program.status = ProgramStatus.ACTIVE
        self.db.commit()
        self.db.refresh(program)
        return program

    def pause_program(self, id: UUID) -> ReferralProgram:
        """Met en pause un programme."""
        program = self.get_program(id)

        if program.status != ProgramStatus.ACTIVE:
            raise ProgramStateError("Can only pause active programs")

        program.status = ProgramStatus.PAUSED
        self.db.commit()
        self.db.refresh(program)
        return program

    def end_program(self, id: UUID) -> ReferralProgram:
        """Termine un programme."""
        program = self.get_program(id)

        if program.status not in [ProgramStatus.ACTIVE, ProgramStatus.PAUSED]:
            raise ProgramStateError(f"Cannot end program in status {program.status}")

        program.status = ProgramStatus.ENDED
        self.db.commit()
        self.db.refresh(program)
        return program

    def autocomplete_program(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete programmes."""
        return self.program_repo.autocomplete(prefix, field, limit)

    # ================== Reward Tiers ==================

    def add_tier(self, program_id: UUID, data: RewardTierCreate) -> RewardTier:
        """Ajoute un palier à un programme."""
        program = self.get_program(program_id)

        if program.status == ProgramStatus.ACTIVE:
            raise ProgramValidationError("Cannot modify active program")

        return self.tier_repo.create(program_id, data.model_dump())

    def update_tier(self, program_id: UUID, tier_id: UUID, data: RewardTierUpdate) -> RewardTier:
        """Met à jour un palier."""
        program = self.get_program(program_id)
        tier = self.tier_repo.get_by_id(tier_id)

        if not tier or tier.program_id != program_id:
            raise RewardTierNotFoundError(f"Tier {tier_id} not found")

        return self.tier_repo.update(tier, data.model_dump(exclude_unset=True))

    def delete_tier(self, program_id: UUID, tier_id: UUID) -> bool:
        """Supprime un palier."""
        program = self.get_program(program_id)
        tier = self.tier_repo.get_by_id(tier_id)

        if not tier or tier.program_id != program_id:
            raise RewardTierNotFoundError(f"Tier {tier_id} not found")

        if program.status == ProgramStatus.ACTIVE:
            raise ProgramValidationError("Cannot modify active program")

        return self.tier_repo.delete(tier)

    # ================== Referral Codes ==================

    def generate_referral_code(
        self,
        program_id: UUID,
        referrer_id: UUID,
        custom_code: str = None
    ) -> ReferralCode:
        """Génère un code de parrainage pour un utilisateur."""
        program = self.get_program(program_id)

        if program.status != ProgramStatus.ACTIVE:
            raise ProgramValidationError("Program is not active")

        # Générer ou valider le code
        code = custom_code.upper().strip() if custom_code else self._generate_unique_code()

        if self.code_repo.code_exists(code):
            raise ReferralCodeDuplicateError(f"Code {code} already exists")

        # Créer le code
        code_data = {
            "program_id": program_id,
            "referrer_id": referrer_id,
            "code": code,
            "expires_at": datetime.combine(program.end_date, datetime.max.time()) if program.end_date else None
        }

        return self.code_repo.create(code_data)

    def _generate_unique_code(self, length: int = 8) -> str:
        """Génère un code unique."""
        while True:
            code = secrets.token_urlsafe(length)[:length].upper()
            if not self.code_repo.code_exists(code):
                return code

    def get_referral_code(self, code: str) -> ReferralCode:
        """Récupère un code de parrainage."""
        ref_code = self.code_repo.get_by_code(code)
        if not ref_code:
            raise ReferralCodeNotFoundError(f"Code {code} not found")
        return ref_code

    def validate_code(self, code: str) -> ReferralCode:
        """Valide un code de parrainage."""
        ref_code = self.get_referral_code(code)

        if not ref_code.is_active:
            raise ReferralCodeInactiveError("Code is inactive")

        if ref_code.expires_at and datetime.utcnow() > ref_code.expires_at:
            raise ReferralCodeExpiredError("Code has expired")

        if ref_code.max_uses and ref_code.current_uses >= ref_code.max_uses:
            raise ReferralCodeLimitReachedError("Code usage limit reached")

        # Vérifier le programme
        program = self.program_repo.get_by_id(ref_code.program_id)
        if not program or program.status != ProgramStatus.ACTIVE:
            raise ProgramValidationError("Associated program is not active")

        return ref_code

    def list_codes_for_referrer(self, referrer_id: UUID) -> List[ReferralCode]:
        """Liste les codes d'un parrain."""
        return self.code_repo.list_for_referrer(referrer_id)

    # ================== Referrals ==================

    def track_click(self, data: TrackClickRequest) -> Referral:
        """Enregistre un clic sur un lien de parrainage."""
        ref_code = self.validate_code(data.code)

        # Créer le referral
        referral_data = {
            "program_id": ref_code.program_id,
            "referral_code_id": ref_code.id,
            "referrer_id": ref_code.referrer_id,
            "status": ReferralStatus.CLICKED,
            "click_timestamp": datetime.utcnow(),
            "ip_address": data.ip_address,
            "user_agent": data.user_agent,
            "device_fingerprint": data.device_fingerprint,
            "utm_source": data.utm_source,
            "utm_medium": data.utm_medium,
            "utm_campaign": data.utm_campaign,
            "landing_page": data.landing_page
        }

        # Définir l'expiration
        program = self.program_repo.get_by_id(ref_code.program_id)
        if program:
            referral_data["expires_at"] = datetime.utcnow() + timedelta(
                days=program.conversion_window_days
            )

        referral = self.referral_repo.create(referral_data)

        # Mettre à jour les stats du code
        self.code_repo.increment_stats(ref_code, clicks=1)

        # Exécuter les vérifications anti-fraude
        self._run_fraud_checks(referral)

        return referral

    def track_signup(self, data: TrackSignupRequest) -> Referral:
        """Enregistre une inscription via parrainage."""
        referral = self.referral_repo.get_by_id(data.referral_id)
        if not referral:
            raise ReferralNotFoundError(f"Referral {data.referral_id} not found")

        if referral.status not in [ReferralStatus.CLICKED, ReferralStatus.PENDING]:
            raise ReferralStateError(f"Cannot signup on referral in status {referral.status}")

        # Vérifier expiration
        if referral.expires_at and datetime.utcnow() > referral.expires_at:
            referral.status = ReferralStatus.EXPIRED
            self.db.commit()
            raise ReferralExpiredError("Referral has expired")

        # Vérifier auto-parrainage
        program = self.program_repo.get_by_id(referral.program_id)
        if program and not program.allow_self_referral:
            if data.referee_id == referral.referrer_id:
                referral.status = ReferralStatus.FRAUDULENT
                referral.fraud_flags = [FraudReason.SELF_REFERRAL.value]
                self.db.commit()
                raise SelfReferralError("Self-referral is not allowed")

        # Vérifier unicité email
        if program and program.require_unique_email:
            if self.referral_repo.referee_exists(program.id, data.referee_email, referral.id):
                raise DuplicateRefereeError("Email already referred in this program")

        # Mettre à jour le referral
        referral.referee_id = data.referee_id
        referral.referee_email = data.referee_email.lower()
        referral.referee_name = data.referee_name
        referral.signup_timestamp = datetime.utcnow()
        referral.status = ReferralStatus.SIGNED_UP

        # Mettre à jour les stats
        ref_code = self.code_repo.get_by_id(referral.referral_code_id)
        if ref_code:
            self.code_repo.increment_stats(ref_code, signups=1)

        if program:
            program.total_signups += 1

        self.db.commit()
        self.db.refresh(referral)

        return referral

    def track_conversion(self, data: TrackConversionRequest) -> Referral:
        """Enregistre une conversion."""
        referral = self.referral_repo.get_by_id(data.referral_id)
        if not referral:
            raise ReferralNotFoundError(f"Referral {data.referral_id} not found")

        if referral.status != ReferralStatus.SIGNED_UP:
            raise ReferralStateError(f"Cannot convert referral in status {referral.status}")

        # Vérifier expiration
        if referral.expires_at and datetime.utcnow() > referral.expires_at:
            referral.status = ReferralStatus.EXPIRED
            self.db.commit()
            raise ReferralExpiredError("Referral has expired")

        # Vérifier montant minimum
        program = self.program_repo.get_by_id(referral.program_id)
        if program and data.amount < program.min_conversion_amount:
            raise ReferralValidationError(
                f"Conversion amount must be at least {program.min_conversion_amount}"
            )

        # Mettre à jour le referral
        referral.conversion_order_id = data.order_id
        referral.conversion_amount = data.amount
        referral.conversion_timestamp = datetime.utcnow()
        referral.status = ReferralStatus.CONVERTED

        # Mettre à jour les stats
        ref_code = self.code_repo.get_by_id(referral.referral_code_id)
        if ref_code:
            self.code_repo.increment_stats(ref_code, conversions=1)

        if program:
            program.total_conversions += 1
            program.current_total_referrals += 1

        self.db.commit()
        self.db.refresh(referral)

        # Auto-qualifier si pas de vérification requise
        if not referral.is_suspicious:
            self.qualify_referral(referral.id)

        return referral

    def qualify_referral(self, id: UUID) -> Referral:
        """Qualifie un parrainage pour récompense."""
        referral = self.referral_repo.get_by_id(id)
        if not referral:
            raise ReferralNotFoundError(f"Referral {id} not found")

        if referral.status != ReferralStatus.CONVERTED:
            raise ReferralStateError("Can only qualify converted referrals")

        if referral.is_suspicious:
            raise FraudDetectedError("Referral flagged as suspicious")

        referral.status = ReferralStatus.QUALIFIED
        referral.qualification_timestamp = datetime.utcnow()
        self.db.commit()

        # Créer les récompenses
        self._create_rewards(referral)

        self.db.refresh(referral)
        return referral

    def _create_rewards(self, referral: Referral) -> None:
        """Crée les récompenses pour un parrainage qualifié."""
        program = self.program_repo.get_by_id(referral.program_id)
        if not program:
            return

        # Trouver le palier applicable
        referrer_count = self.referral_repo.count_for_referrer(
            referral.referrer_id,
            program.id,
            [ReferralStatus.QUALIFIED, ReferralStatus.REWARDED]
        )
        tier = self.tier_repo.get_applicable_tier(
            program.id,
            referrer_count,
            referral.conversion_amount
        )

        if not tier:
            return

        # Vérifier budget
        total_reward = tier.referrer_reward_value + tier.referee_reward_value
        if program.total_budget and program.spent_budget + total_reward > program.total_budget:
            raise ProgramBudgetExceededError("Program budget exceeded")

        # Créer récompense parrain
        referrer_reward = self.reward_repo.create({
            "program_id": program.id,
            "referral_id": referral.id,
            "user_id": referral.referrer_id,
            "is_referrer_reward": True,
            "reward_type": tier.referrer_reward_type,
            "reward_value": tier.referrer_reward_value,
            "currency": program.currency,
            "description": tier.referrer_reward_description
        })
        referral.referrer_reward_id = referrer_reward.id

        # Créer récompense filleul
        if referral.referee_id:
            referee_reward = self.reward_repo.create({
                "program_id": program.id,
                "referral_id": referral.id,
                "user_id": referral.referee_id,
                "is_referrer_reward": False,
                "reward_type": tier.referee_reward_type,
                "reward_value": tier.referee_reward_value,
                "currency": program.currency,
                "description": tier.referee_reward_description
            })
            referral.referee_reward_id = referee_reward.id

        # Mettre à jour les compteurs
        tier.current_uses += 1
        program.spent_budget += total_reward
        program.total_rewards_paid += total_reward
        referral.status = ReferralStatus.REWARDED

        self.db.commit()

    def list_referrals(
        self,
        filters: ReferralFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Referral], int, int]:
        """Liste paginée des parrainages."""
        items, total = self.referral_repo.list(filters, page, page_size, sort_by, sort_dir)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def reject_referral(self, id: UUID, reason: str = "") -> Referral:
        """Rejette un parrainage."""
        referral = self.referral_repo.get_by_id(id)
        if not referral:
            raise ReferralNotFoundError(f"Referral {id} not found")

        if referral.status in [ReferralStatus.EXPIRED, ReferralStatus.REJECTED, ReferralStatus.FRAUDULENT]:
            raise ReferralStateError(f"Cannot reject referral in status {referral.status}")

        referral.status = ReferralStatus.REJECTED
        referral.notes = reason
        self.db.commit()
        self.db.refresh(referral)
        return referral

    def flag_fraudulent(self, id: UUID, reason: FraudReason) -> Referral:
        """Marque un parrainage comme frauduleux."""
        referral = self.referral_repo.get_by_id(id)
        if not referral:
            raise ReferralNotFoundError(f"Referral {id} not found")

        referral.status = ReferralStatus.FRAUDULENT
        referral.is_suspicious = True
        if reason.value not in referral.fraud_flags:
            referral.fraud_flags = referral.fraud_flags + [reason.value]
        self.db.commit()
        self.db.refresh(referral)
        return referral

    # ================== Fraud Detection ==================

    def _run_fraud_checks(self, referral: Referral) -> None:
        """Exécute les vérifications anti-fraude."""
        fraud_score = Decimal("0")
        flags = []

        # Check IP
        ip_count = self.fraud_repo.get_similar_ip_count(referral.ip_address, exclude_id=referral.id)
        if ip_count > 3:
            fraud_score += Decimal("30")
            flags.append(FraudReason.SAME_IP.value)
            self.fraud_repo.create({
                "referral_id": referral.id,
                "check_type": "ip",
                "result": "fail" if ip_count > 5 else "warning",
                "score": Decimal(str(min(ip_count * 10, 50))),
                "details": {"ip": referral.ip_address, "count": ip_count}
            })

        # Check device
        if referral.device_fingerprint:
            device_count = self.fraud_repo.get_similar_device_count(
                referral.device_fingerprint,
                exclude_id=referral.id
            )
            if device_count > 2:
                fraud_score += Decimal("40")
                flags.append(FraudReason.SAME_DEVICE.value)
                self.fraud_repo.create({
                    "referral_id": referral.id,
                    "check_type": "device",
                    "result": "fail" if device_count > 3 else "warning",
                    "score": Decimal(str(min(device_count * 15, 60))),
                    "details": {"fingerprint": referral.device_fingerprint, "count": device_count}
                })

        # Mettre à jour le referral
        referral.fraud_score = fraud_score
        referral.fraud_flags = flags
        referral.is_suspicious = fraud_score >= Decimal("50")
        self.db.commit()

    # ================== Rewards ==================

    def claim_reward(self, reward_id: UUID) -> Reward:
        """Réclame une récompense."""
        reward = self.reward_repo.get_by_id(reward_id)
        if not reward:
            raise RewardNotFoundError(f"Reward {reward_id} not found")

        if reward.is_claimed:
            raise RewardAlreadyClaimedError("Reward already claimed")

        if reward.expires_at and datetime.utcnow() > reward.expires_at:
            raise RewardExpiredError("Reward has expired")

        return self.reward_repo.claim(reward)

    def list_rewards_for_user(self, user_id: UUID, is_claimed: bool = None) -> List[Reward]:
        """Liste les récompenses d'un utilisateur."""
        return self.reward_repo.list_for_user(user_id, is_claimed)

    # ================== Payouts ==================

    def create_payout(self, data: PayoutCreate) -> Payout:
        """Crée une demande de paiement."""
        # Vérifier les récompenses
        total = Decimal("0")
        for reward_id in data.reward_ids:
            reward = self.reward_repo.get_by_id(reward_id)
            if not reward:
                raise RewardNotFoundError(f"Reward {reward_id} not found")
            if reward.payout_id:
                raise PayoutValidationError(f"Reward {reward_id} already in a payout")
            if reward.reward_type != RewardType.CASH:
                raise PayoutValidationError(f"Only cash rewards can be paid out")
            total += reward.reward_value

        if total != data.amount:
            raise PayoutValidationError("Amount doesn't match rewards total")

        payout = self.payout_repo.create(data.model_dump(), self.user_id)

        # Lier les récompenses
        for reward_id in data.reward_ids:
            reward = self.reward_repo.get_by_id(reward_id)
            reward.payout_id = payout.id
            reward.is_claimed = True
            reward.claimed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payout)
        return payout

    def process_payout(self, id: UUID, transaction_reference: str) -> Payout:
        """Traite un paiement."""
        payout = self.payout_repo.get_by_id(id)
        if not payout:
            raise PayoutNotFoundError(f"Payout {id} not found")

        if payout.status != PayoutStatus.PENDING:
            raise PayoutStateError(f"Cannot process payout in status {payout.status}")

        return self.payout_repo.process(payout, transaction_reference)

    def list_payouts(
        self,
        filters: PayoutFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Payout], int, int]:
        """Liste paginée des paiements."""
        items, total = self.payout_repo.list(filters, page, page_size)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    # ================== Stats ==================

    def get_program_stats(self) -> Dict[str, Any]:
        """Statistiques des programmes."""
        return self.program_repo.get_stats()

    def get_referral_stats(self, program_id: UUID = None) -> ReferralStats:
        """Statistiques des parrainages."""
        stats_data = self.referral_repo.get_stats(program_id)

        total_clicks = stats_data["by_status"].get("clicked", 0) + \
                       stats_data["by_status"].get("signed_up", 0) + \
                       stats_data["by_status"].get("converted", 0)
        total_signups = stats_data["by_status"].get("signed_up", 0) + \
                        stats_data["by_status"].get("converted", 0)
        total_conversions = stats_data["by_status"].get("converted", 0) + \
                            stats_data["by_status"].get("qualified", 0) + \
                            stats_data["by_status"].get("rewarded", 0)

        click_to_signup = Decimal(str(total_signups / total_clicks * 100)) if total_clicks > 0 else Decimal("0")
        signup_to_conversion = Decimal(str(total_conversions / total_signups * 100)) if total_signups > 0 else Decimal("0")
        overall = Decimal(str(total_conversions / total_clicks * 100)) if total_clicks > 0 else Decimal("0")

        return ReferralStats(
            tenant_id=self.tenant_id,
            program_id=program_id,
            total_clicks=total_clicks,
            total_signups=total_signups,
            total_conversions=total_conversions,
            total_qualified=stats_data["by_status"].get("qualified", 0),
            click_to_signup_rate=click_to_signup,
            signup_to_conversion_rate=signup_to_conversion,
            overall_conversion_rate=overall,
            total_conversion_value=Decimal(str(stats_data["total_conversion_value"])),
            fraud_detected=stats_data["by_status"].get("fraudulent", 0)
        )

    def get_referrer_profile(self, user_id: UUID) -> ReferrerProfile:
        """Récupère le profil d'un parrain."""
        codes = self.code_repo.list_for_referrer(user_id)
        active_codes = [c.code for c in codes if c.is_active and not c.is_deleted]

        referrals = self.referral_repo.list_for_referrer(user_id)
        total = len(referrals)
        successful = len([r for r in referrals if r.status == ReferralStatus.REWARDED])
        pending = len([r for r in referrals if r.status in [
            ReferralStatus.CLICKED, ReferralStatus.SIGNED_UP, ReferralStatus.CONVERTED
        ]])

        earnings = self.reward_repo.get_total_earnings(user_id)

        first_date = None
        last_date = None
        if referrals:
            first_date = min(r.created_at.date() for r in referrals)
            last_date = max(r.created_at.date() for r in referrals)

        conversion_rate = Decimal(str(successful / total * 100)) if total > 0 else Decimal("0")

        return ReferrerProfile(
            user_id=user_id,
            tenant_id=self.tenant_id,
            active_codes=active_codes,
            total_referrals=total,
            successful_referrals=successful,
            pending_referrals=pending,
            total_earnings=earnings["total"],
            pending_earnings=earnings["pending"],
            paid_earnings=earnings["claimed"],
            first_referral_date=first_date,
            last_referral_date=last_date,
            conversion_rate=conversion_rate
        )


def create_referral_service(
    db: Session,
    tenant_id: UUID,
    user_id: UUID = None
) -> ReferralService:
    """Factory pour créer une instance du service."""
    return ReferralService(db, tenant_id, user_id)
