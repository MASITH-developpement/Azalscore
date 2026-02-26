"""
AZALS MODULE GAMIFICATION - Router API
======================================

Endpoints REST pour le module de gamification.
"""
from __future__ import annotations


import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import (
    PointType,
    BadgeStatus,
    BadgeRarity,
    ChallengeStatus,
    ChallengeType,
    RewardStatus,
    RewardType,
    CompetitionStatus,
    LeaderboardPeriod,
    NotificationType,
    RuleEventType,
)
from .schemas import (
    # Pagination
    PaginatedResponse,
    AutocompleteResponse,
    AutocompleteItem,
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
    AwardPointsRequest,
    SpendPointsRequest,
    TransferPointsRequest,
    PointTransactionResponse,
    PointTransactionFilters,
    PointBalanceResponse,
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
from .service import GamificationService
from .exceptions import (
    GamificationError,
    ProfileNotFoundError,
    InsufficientPointsError,
    BadgeNotFoundError,
    BadgeAlreadyUnlockedError,
    ChallengeNotFoundError,
    ChallengeNotActiveError,
    AlreadyJoinedChallengeError,
    RewardNotFoundError,
    RewardNotAvailableError,
    RewardOutOfStockError,
    TeamNotFoundError,
    TeamFullError,
    AlreadyInTeamError,
    CompetitionNotFoundError,
    FeatureDisabledError,
    DuplicateCodeError,
)


router = APIRouter(prefix="/gamification", tags=["Gamification"])


def get_service(db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> GamificationService:
    """Dependency pour obtenir le service de gamification."""
    return GamificationService(db, current_user.tenant_id)


def handle_gamification_error(e: GamificationError):
    """Gestion centralisee des erreurs de gamification."""
    status_map = {
        "PROFILE_NOT_FOUND": 404,
        "BADGE_NOT_FOUND": 404,
        "CHALLENGE_NOT_FOUND": 404,
        "REWARD_NOT_FOUND": 404,
        "TEAM_NOT_FOUND": 404,
        "COMPETITION_NOT_FOUND": 404,
        "LEVEL_NOT_FOUND": 404,
        "LEADERBOARD_NOT_FOUND": 404,
        "INSUFFICIENT_POINTS": 400,
        "BADGE_ALREADY_UNLOCKED": 409,
        "ALREADY_JOINED_CHALLENGE": 409,
        "ALREADY_IN_TEAM": 409,
        "ALREADY_REGISTERED": 409,
        "DUPLICATE_CODE": 409,
        "FEATURE_DISABLED": 403,
        "REWARD_OUT_OF_STOCK": 400,
        "REWARD_NOT_AVAILABLE": 400,
        "CHALLENGE_NOT_ACTIVE": 400,
        "TEAM_FULL": 400,
    }
    status_code = status_map.get(e.code, 400)
    raise HTTPException(status_code=status_code, detail={"code": e.code, "message": e.message, "details": e.details})


# =============================================================================
# PROFILS
# =============================================================================

@router.get("/profile/me", response_model=UserProfileResponse)
async def get_my_profile(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mon profil de gamification."""
    try:
        profile = service.get_or_create_profile(current_user.id)
        return profile
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/profile/me/summary", response_model=UserProfileSummary)
async def get_my_profile_summary(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere le resume de mon profil."""
    try:
        return service.get_profile_summary(current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.put("/profile/me", response_model=UserProfileResponse)
async def update_my_profile(
    data: UserProfileUpdate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Met a jour mon profil."""
    try:
        return service.update_profile(current_user.id, data.model_dump(exclude_unset=True))
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    service: GamificationService = Depends(get_service),
    _: None = require_permission("gamification.profile.read")
):
    """Recupere le profil d'un utilisateur."""
    try:
        return service.get_profile(user_id)
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=GamificationDashboard)
async def get_dashboard(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere le tableau de bord de gamification."""
    try:
        return service.get_user_dashboard(current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/stats", response_model=GamificationStats)
async def get_global_stats(
    service: GamificationService = Depends(get_service),
    _: None = require_permission("gamification.stats.read")
):
    """Recupere les statistiques globales."""
    try:
        return service.get_global_stats()
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/stats/me", response_model=UserGamificationStats)
async def get_my_stats(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mes statistiques."""
    try:
        return service.get_user_stats(current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# POINTS
# =============================================================================

@router.get("/points/balance")
async def get_point_balances(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere les soldes de points."""
    profile = service.get_or_create_profile(current_user.id)
    return {
        "xp": profile.current_xp,
        "coins": profile.coins_balance,
        "karma": profile.karma_balance,
        "credits": profile.credits_balance,
        "lifetime_xp": profile.lifetime_xp,
        "lifetime_coins_earned": profile.lifetime_coins_earned
    }


@router.get("/points/transactions", response_model=PaginatedResponse)
async def get_transactions(
    point_type: Optional[PointType] = Query(None),
    source: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste mes transactions de points."""
    filters = PointTransactionFilters(
        point_type=point_type,
        source=source,
        date_from=date_from,
        date_to=date_to
    )
    items, total = service.get_transactions(current_user.id, filters, page, page_size)
    return PaginatedResponse(
        items=[PointTransactionResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.post("/points/award", response_model=PointTransactionResponse)
async def award_points(
    data: AwardPointsRequest,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.points.award")
):
    """Attribue des points a un utilisateur."""
    try:
        transaction = service.award_points(
            user_id=data.user_id,
            amount=data.amount,
            point_type=data.point_type,
            description=data.description,
            source=data.source,
            source_id=data.source_id,
            expires_at=data.expires_at,
            created_by=current_user.id
        )
        return transaction
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/points/spend", response_model=PointTransactionResponse)
async def spend_points(
    data: SpendPointsRequest,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Depense des points."""
    try:
        if data.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non autorise")

        transaction = service.spend_points(
            user_id=data.user_id,
            amount=data.amount,
            point_type=data.point_type,
            description=data.description,
            reference_type=data.reference_type,
            reference_id=data.reference_id
        )
        return transaction
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/points/transfer", response_model=PointTransactionResponse)
async def transfer_points(
    data: TransferPointsRequest,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Transfere des points a un autre utilisateur."""
    try:
        if data.from_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Non autorise")

        transaction = service.transfer_points(
            from_user_id=data.from_user_id,
            to_user_id=data.to_user_id,
            amount=data.amount,
            point_type=data.point_type,
            message=data.message
        )
        return transaction
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# NIVEAUX
# =============================================================================

@router.get("/levels", response_model=list[LevelResponse])
async def list_levels(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste tous les niveaux."""
    return service.get_all_levels()


@router.get("/levels/{level_number}", response_model=LevelResponse)
async def get_level(
    level_number: int,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere un niveau."""
    level = service.get_level_info(level_number)
    if not level:
        raise HTTPException(status_code=404, detail="Niveau non trouve")
    return level


@router.post("/levels", response_model=LevelResponse, status_code=status.HTTP_201_CREATED)
async def create_level(
    data: LevelCreate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.admin")
):
    """Cree un nouveau niveau."""
    try:
        return service.levels.create(data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# BADGES
# =============================================================================

@router.get("/badges", response_model=PaginatedResponse)
async def list_badges(
    search: Optional[str] = Query(None),
    category_id: Optional[UUID] = Query(None),
    rarity: Optional[BadgeRarity] = Query(None),
    include_secret: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste les badges."""
    try:
        filters = BadgeFilters(
            search=search,
            category_id=category_id,
            rarity=rarity,
            include_secret=include_secret
        )
        items, total = service.list_badges(filters, page, page_size)
        return PaginatedResponse(
            items=[BadgeResponse.model_validate(b) for b in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0
        )
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/badges/{badge_id}", response_model=BadgeResponse)
async def get_badge(
    badge_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere un badge."""
    try:
        return service.get_badge(badge_id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/badges", response_model=BadgeResponse, status_code=status.HTTP_201_CREATED)
async def create_badge(
    data: BadgeCreate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.badges.create")
):
    """Cree un nouveau badge."""
    try:
        return service.create_badge(data.model_dump(), current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.put("/badges/{badge_id}", response_model=BadgeResponse)
async def update_badge(
    badge_id: UUID,
    data: BadgeUpdate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.badges.update")
):
    """Met a jour un badge."""
    try:
        badge = service.get_badge(badge_id)
        return service.badges.update(badge, data.model_dump(exclude_unset=True))
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/badges/my", response_model=list[UserBadgeResponse])
async def get_my_badges(
    status: Optional[BadgeStatus] = Query(None),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mes badges."""
    badges = service.get_user_badges(current_user.id, status)
    return [UserBadgeResponse.model_validate(b) for b in badges]


@router.post("/badges/{badge_id}/unlock", response_model=UserBadgeResponse)
async def unlock_badge(
    badge_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.badges.unlock")
):
    """Debloque un badge pour l'utilisateur courant."""
    try:
        return service.unlock_badge(current_user.id, badge_id)
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# DEFIS
# =============================================================================

@router.get("/challenges", response_model=PaginatedResponse)
async def list_challenges(
    search: Optional[str] = Query(None),
    challenge_type: Optional[ChallengeType] = Query(None),
    status: Optional[list[ChallengeStatus]] = Query(None),
    is_team: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste les defis."""
    try:
        filters = ChallengeFilters(
            search=search,
            challenge_type=challenge_type,
            status=status,
            is_team=is_team
        )
        items, total = service.list_challenges(filters, page, page_size)
        return PaginatedResponse(
            items=[ChallengeResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0
        )
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere un defi."""
    try:
        return service.get_challenge(challenge_id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/challenges", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    data: ChallengeCreate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.challenges.create")
):
    """Cree un nouveau defi."""
    try:
        return service.create_challenge(data.model_dump(), current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.put("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def update_challenge(
    challenge_id: UUID,
    data: ChallengeUpdate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.challenges.update")
):
    """Met a jour un defi."""
    try:
        challenge = service.get_challenge(challenge_id)
        return service.challenges.update(challenge, data.model_dump(exclude_unset=True))
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/challenges/my", response_model=list[UserChallengeResponse])
async def get_my_challenges(
    status: Optional[ChallengeStatus] = Query(None),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mes defis."""
    challenges = service.get_user_challenges(current_user.id, status)
    return [UserChallengeResponse.model_validate(c) for c in challenges]


@router.post("/challenges/{challenge_id}/join", response_model=UserChallengeResponse)
async def join_challenge(
    challenge_id: UUID,
    team_id: Optional[UUID] = Query(None),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Rejoint un defi."""
    try:
        return service.join_challenge(current_user.id, challenge_id, team_id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/challenges/{challenge_id}/progress", response_model=UserChallengeResponse)
async def update_challenge_progress(
    challenge_id: UUID,
    data: UpdateProgressRequest,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Met a jour la progression d'un defi."""
    try:
        return service.update_challenge_progress(
            current_user.id,
            challenge_id,
            data.progress,
            increment=True,
            context=data.context
        )
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/challenges/{challenge_id}/claim")
async def claim_challenge_rewards(
    challenge_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Reclame les recompenses d'un defi termine."""
    try:
        rewards = service.claim_challenge_rewards(current_user.id, challenge_id)
        return {"rewards": rewards}
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# RECOMPENSES
# =============================================================================

@router.get("/rewards", response_model=PaginatedResponse)
async def list_rewards(
    search: Optional[str] = Query(None),
    reward_type: Optional[RewardType] = Query(None),
    category: Optional[str] = Query(None),
    affordable: bool = Query(False),
    min_cost: Optional[int] = Query(None),
    max_cost: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste les recompenses."""
    try:
        filters = RewardFilters(
            search=search,
            reward_type=reward_type,
            category=category,
            affordable=affordable,
            min_cost=min_cost,
            max_cost=max_cost
        )
        items, total = service.list_rewards(filters, current_user.id, page, page_size)
        return PaginatedResponse(
            items=[RewardResponse.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0
        )
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/rewards/{reward_id}", response_model=RewardResponse)
async def get_reward(
    reward_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere une recompense."""
    try:
        return service.get_reward(reward_id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/rewards", response_model=RewardResponse, status_code=status.HTTP_201_CREATED)
async def create_reward(
    data: RewardCreate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.rewards.create")
):
    """Cree une nouvelle recompense."""
    try:
        return service.create_reward(data.model_dump(), current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.put("/rewards/{reward_id}", response_model=RewardResponse)
async def update_reward(
    reward_id: UUID,
    data: RewardUpdate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.rewards.update")
):
    """Met a jour une recompense."""
    try:
        reward = service.get_reward(reward_id)
        return service.rewards.update(reward, data.model_dump(exclude_unset=True))
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/rewards/{reward_id}/claim", response_model=RewardClaimResponse)
async def claim_reward(
    reward_id: UUID,
    data: ClaimRewardRequest,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Reclame une recompense."""
    try:
        return service.claim_reward(
            current_user.id,
            reward_id,
            data.shipping_address,
            data.user_notes
        )
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/rewards/claims/my", response_model=list[RewardClaimResponse])
async def get_my_claims(
    status: Optional[RewardStatus] = Query(None),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mes reclamations."""
    claims = service.get_user_claims(current_user.id, status)
    return [RewardClaimResponse.model_validate(c) for c in claims]


@router.put("/rewards/claims/{claim_id}/status", response_model=RewardClaimResponse)
async def update_claim_status(
    claim_id: UUID,
    data: UpdateClaimStatusRequest,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.rewards.manage")
):
    """Met a jour le statut d'une reclamation."""
    try:
        return service.update_claim_status(
            claim_id,
            data.status,
            data.tracking_number,
            data.admin_notes,
            current_user.id
        )
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# REGLES
# =============================================================================

@router.get("/rules", response_model=list[RuleResponse])
async def list_rules(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.rules.read")
):
    """Liste les regles."""
    rules, _ = service.rules._base_query().filter().all(), 0
    return [RuleResponse.model_validate(r) for r in rules]


@router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: RuleCreate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.rules.create")
):
    """Cree une nouvelle regle."""
    try:
        return service.create_rule(data.model_dump(), current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/rules/trigger")
async def trigger_event(
    data: TriggerRuleRequest,
    event_type: RuleEventType = Query(...),
    source: Optional[str] = Query(None),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.rules.trigger")
):
    """Declenche un evenement manuellement."""
    try:
        results = service.trigger_event(
            event_type,
            data.user_id,
            data.event_data,
            source
        )
        return {"results": results}
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# EQUIPES
# =============================================================================

@router.get("/teams", response_model=PaginatedResponse)
async def list_teams(
    search: Optional[str] = Query(None),
    public_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste les equipes."""
    try:
        items, total = service.list_teams(search, public_only, page, page_size)
        return PaginatedResponse(
            items=[TeamResponse.model_validate(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0
        )
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere une equipe."""
    try:
        return service.get_team(team_id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/teams/{team_id}/members", response_model=list[TeamMemberResponse])
async def get_team_members(
    team_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere les membres d'une equipe."""
    try:
        members = service.get_team_members(team_id)
        return [TeamMemberResponse.model_validate(m) for m in members]
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Cree une nouvelle equipe."""
    try:
        return service.create_team(data.model_dump(), current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    data: TeamUpdate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Met a jour une equipe."""
    try:
        team = service.get_team(team_id)
        # Verifier que l'utilisateur est capitaine
        if team.captain_id != current_user.id:
            raise HTTPException(status_code=403, detail="Seul le capitaine peut modifier l'equipe")
        return service.teams.update(team, data.model_dump(exclude_unset=True))
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/teams/{team_id}/join")
async def join_team(
    team_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Rejoint une equipe."""
    try:
        membership = service.join_team(current_user.id, team_id)
        return TeamMemberResponse.model_validate(membership)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/teams/leave")
async def leave_team(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Quitte l'equipe actuelle."""
    try:
        service.leave_team(current_user.id)
        return {"message": "Vous avez quitte l'equipe"}
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# COMPETITIONS
# =============================================================================

@router.get("/competitions", response_model=PaginatedResponse)
async def list_competitions(
    status: Optional[list[CompetitionStatus]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste les competitions."""
    try:
        items, total = service.list_competitions(status, page, page_size)
        return PaginatedResponse(
            items=[CompetitionResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0
        )
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/competitions/{competition_id}", response_model=CompetitionResponse)
async def get_competition(
    competition_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere une competition."""
    try:
        return service.get_competition(competition_id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/competitions", response_model=CompetitionResponse, status_code=status.HTTP_201_CREATED)
async def create_competition(
    data: CompetitionCreate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.competitions.create")
):
    """Cree une nouvelle competition."""
    try:
        return service.create_competition(data.model_dump(), current_user.id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/competitions/{competition_id}/register", response_model=CompetitionParticipantResponse)
async def register_for_competition(
    competition_id: UUID,
    team_id: Optional[UUID] = Query(None),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """S'inscrit a une competition."""
    try:
        participant = service.register_for_competition(
            competition_id,
            current_user.id if not team_id else None,
            team_id
        )
        return CompetitionParticipantResponse.model_validate(participant)
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# LEADERBOARDS
# =============================================================================

@router.get("/leaderboards", response_model=list[LeaderboardResponse])
async def list_leaderboards(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Liste les classements."""
    try:
        return service.leaderboards.list_active()
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/leaderboards/{leaderboard_id}", response_model=LeaderboardWithEntries)
async def get_leaderboard(
    leaderboard_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere un classement avec ses entrees."""
    try:
        return service.get_leaderboard(leaderboard_id)
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/leaderboards/period/{period}", response_model=LeaderboardWithEntries)
async def get_leaderboard_by_period(
    period: LeaderboardPeriod,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere un classement par periode."""
    try:
        return service.get_leaderboard(period=period)
    except GamificationError as e:
        handle_gamification_error(e)


@router.get("/leaderboards/my-rank", response_model=LeaderboardEntryResponse)
async def get_my_rank(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.ALL_TIME),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mon rang dans le classement."""
    try:
        entry = service.get_user_rank(current_user.id, period=period)
        if not entry:
            raise HTTPException(status_code=404, detail="Vous n'etes pas dans le classement")
        return entry
    except GamificationError as e:
        handle_gamification_error(e)


@router.post("/leaderboards/{leaderboard_id}/refresh")
async def refresh_leaderboard(
    leaderboard_id: UUID,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.admin")
):
    """Rafraichit un classement."""
    try:
        service.refresh_leaderboard(leaderboard_id)
        return {"message": "Classement rafraichi"}
    except GamificationError as e:
        handle_gamification_error(e)


# =============================================================================
# NOTIFICATIONS
# =============================================================================

@router.get("/notifications", response_model=list[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mes notifications."""
    notifications = service.get_notifications(
        current_user.id,
        unread_only,
        notification_type,
        limit
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.get("/notifications/count")
async def count_notifications(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Compte les notifications non lues."""
    count = service.count_unread_notifications(current_user.id)
    return {"unread_count": count}


@router.post("/notifications/read")
async def mark_notifications_read(
    data: MarkNotificationsReadRequest,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Marque des notifications comme lues."""
    count = service.mark_notifications_read(
        current_user.id,
        data.notification_ids,
        data.mark_all
    )
    return {"marked_count": count}


# =============================================================================
# STREAKS
# =============================================================================

@router.get("/streaks", response_model=list[StreakResponse])
async def get_my_streaks(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mes series."""
    streaks = service.get_user_streaks(current_user.id)
    return [StreakResponse.model_validate(s) for s in streaks]


@router.post("/streaks/{streak_type}/update", response_model=StreakResponse)
async def update_streak(
    streak_type: str,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Met a jour une serie."""
    try:
        streak = service.update_streak(current_user.id, streak_type)
        return StreakResponse.model_validate(streak)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# ACTIVITE
# =============================================================================

@router.get("/activity", response_model=PaginatedResponse)
async def get_my_activity(
    activity_type: Optional[str] = Query(None),
    source_module: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """Recupere mon historique d'activite."""
    filters = ActivityFilters(
        activity_type=activity_type,
        source_module=source_module,
        date_from=date_from,
        date_to=date_to
    )
    items, total = service.get_user_activity(current_user.id, filters, page, page_size)
    return PaginatedResponse(
        items=[ActivityResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

@router.get("/config", response_model=GamificationConfigResponse)
async def get_config(
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.admin")
):
    """Recupere la configuration de gamification."""
    return service.get_config()


@router.put("/config", response_model=GamificationConfigResponse)
async def update_config(
    data: GamificationConfigUpdate,
    service: GamificationService = Depends(get_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("gamification.admin")
):
    """Met a jour la configuration de gamification."""
    return service.update_config(data.model_dump(exclude_unset=True))
