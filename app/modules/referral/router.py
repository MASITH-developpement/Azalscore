"""
Routes API Referral / Parrainage
=================================
- CRUD programmes et paliers
- Gestion des codes de parrainage
- Tracking clics, inscriptions, conversions
- Récompenses et paiements
- Statistiques
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .exceptions import (
    ProgramNotFoundError, ProgramDuplicateError, ProgramValidationError,
    ProgramStateError, ProgramBudgetExceededError,
    RewardTierNotFoundError,
    ReferralCodeNotFoundError, ReferralCodeDuplicateError,
    ReferralCodeExpiredError, ReferralCodeLimitReachedError, ReferralCodeInactiveError,
    ReferralNotFoundError, ReferralValidationError, ReferralStateError,
    ReferralExpiredError, SelfReferralError, DuplicateRefereeError,
    RewardNotFoundError, RewardAlreadyClaimedError, RewardExpiredError,
    PayoutNotFoundError, PayoutValidationError, PayoutStateError,
    FraudDetectedError
)
from .models import ProgramStatus, ReferralStatus, PayoutStatus, FraudReason
from .schemas import (
    # Program
    ReferralProgramCreate, ReferralProgramUpdate, ReferralProgramResponse,
    ReferralProgramListResponse, ProgramFilters,
    # Tier
    RewardTierCreate, RewardTierUpdate, RewardTierResponse,
    # Code
    ReferralCodeCreate, ReferralCodeUpdate, ReferralCodeResponse,
    ReferralCodeListResponse,
    # Referral
    ReferralResponse, ReferralListResponse, ReferralFilters,
    # Reward
    RewardResponse,
    # Payout
    PayoutCreate, PayoutUpdate, PayoutResponse, PayoutListResponse, PayoutFilters,
    # Tracking
    TrackClickRequest, TrackSignupRequest, TrackConversionRequest,
    # Stats
    ReferralStats, ReferrerProfile,
    # Common
    AutocompleteResponse, BulkResult
)
from .service import ReferralService


router = APIRouter(prefix="/referral", tags=["Referral"])


def get_service(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ReferralService:
    """Factory pour le service Referral."""
    return ReferralService(db, user.tenant_id, user.id)


# ============================================================================
# Program Routes
# ============================================================================

@router.get("/programs", response_model=ReferralProgramListResponse)
async def list_programs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[ProgramStatus]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.view")
):
    """Liste paginée des programmes de parrainage."""
    filters = ProgramFilters(search=search, status=status)
    items, total, pages = service.list_programs(filters, page, page_size, sort_by, sort_dir)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get("/programs/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_programs(
    prefix: str = Query(..., min_length=2),
    field: str = Query("name", pattern="^(name|code)$"),
    limit: int = Query(10, ge=1, le=50),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.view")
):
    """Autocomplete pour les programmes."""
    items = service.autocomplete_program(prefix, field, limit)
    return {"items": items}


@router.get("/programs/{id}", response_model=ReferralProgramResponse)
async def get_program(
    id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.view")
):
    """Récupère un programme par ID."""
    try:
        return service.get_program(id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/programs", response_model=ReferralProgramResponse, status_code=201)
async def create_program(
    data: ReferralProgramCreate,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.create")
):
    """Crée un nouveau programme de parrainage."""
    try:
        return service.create_program(data)
    except ProgramDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/programs/{id}", response_model=ReferralProgramResponse)
async def update_program(
    id: UUID,
    data: ReferralProgramUpdate,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.edit")
):
    """Met à jour un programme."""
    try:
        return service.update_program(id, data)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ProgramStateError, ProgramValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/programs/{id}", status_code=204)
async def delete_program(
    id: UUID,
    hard: bool = Query(False),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.delete")
):
    """Supprime un programme."""
    try:
        service.delete_program(id, hard)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProgramValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/programs/{id}/activate", response_model=ReferralProgramResponse)
async def activate_program(
    id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.edit")
):
    """Active un programme."""
    try:
        return service.activate_program(id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProgramStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/programs/{id}/pause", response_model=ReferralProgramResponse)
async def pause_program(
    id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.edit")
):
    """Met en pause un programme."""
    try:
        return service.pause_program(id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProgramStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/programs/{id}/end", response_model=ReferralProgramResponse)
async def end_program(
    id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.edit")
):
    """Termine un programme."""
    try:
        return service.end_program(id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProgramStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Reward Tier Routes
# ============================================================================

@router.post("/programs/{program_id}/tiers", response_model=RewardTierResponse, status_code=201)
async def add_tier(
    program_id: UUID,
    data: RewardTierCreate,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.edit")
):
    """Ajoute un palier de récompense."""
    try:
        return service.add_tier(program_id, data)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProgramValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/programs/{program_id}/tiers/{tier_id}", response_model=RewardTierResponse)
async def update_tier(
    program_id: UUID,
    tier_id: UUID,
    data: RewardTierUpdate,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.edit")
):
    """Met à jour un palier."""
    try:
        return service.update_tier(program_id, tier_id, data)
    except (ProgramNotFoundError, RewardTierNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/programs/{program_id}/tiers/{tier_id}", status_code=204)
async def delete_tier(
    program_id: UUID,
    tier_id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.edit")
):
    """Supprime un palier."""
    try:
        service.delete_tier(program_id, tier_id)
    except (ProgramNotFoundError, RewardTierNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProgramValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Referral Code Routes
# ============================================================================

@router.post("/codes", response_model=ReferralCodeResponse, status_code=201)
async def generate_code(
    program_id: UUID = Query(...),
    referrer_id: UUID = Query(...),
    custom_code: Optional[str] = Query(None, min_length=4, max_length=20),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.code.create")
):
    """Génère un code de parrainage."""
    try:
        return service.generate_referral_code(program_id, referrer_id, custom_code)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProgramValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ReferralCodeDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/codes/{code}", response_model=ReferralCodeResponse)
async def get_code(
    code: str,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.code.view")
):
    """Récupère un code de parrainage."""
    try:
        return service.get_referral_code(code)
    except ReferralCodeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/codes/validate/{code}", response_model=ReferralCodeResponse)
async def validate_code(
    code: str,
    service: ReferralService = Depends(get_service)
):
    """Valide un code de parrainage (endpoint public)."""
    try:
        return service.validate_code(code)
    except ReferralCodeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ReferralCodeExpiredError, ReferralCodeLimitReachedError,
            ReferralCodeInactiveError, ProgramValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/referrers/{referrer_id}/codes", response_model=List[ReferralCodeResponse])
async def list_referrer_codes(
    referrer_id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.code.view")
):
    """Liste les codes d'un parrain."""
    return service.list_codes_for_referrer(referrer_id)


# ============================================================================
# Tracking Routes
# ============================================================================

@router.post("/track/click", response_model=ReferralResponse)
async def track_click(
    data: TrackClickRequest,
    service: ReferralService = Depends(get_service)
):
    """Enregistre un clic sur un lien de parrainage (public)."""
    try:
        return service.track_click(data)
    except ReferralCodeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ReferralCodeExpiredError, ReferralCodeLimitReachedError,
            ReferralCodeInactiveError, ProgramValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/track/signup", response_model=ReferralResponse)
async def track_signup(
    data: TrackSignupRequest,
    service: ReferralService = Depends(get_service)
):
    """Enregistre une inscription via parrainage (public)."""
    try:
        return service.track_signup(data)
    except ReferralNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ReferralStateError, ReferralExpiredError,
            SelfReferralError, DuplicateRefereeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/track/conversion", response_model=ReferralResponse)
async def track_conversion(
    data: TrackConversionRequest,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.referral.edit")
):
    """Enregistre une conversion."""
    try:
        return service.track_conversion(data)
    except ReferralNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ReferralStateError, ReferralExpiredError, ReferralValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Referral Management Routes
# ============================================================================

@router.get("/referrals", response_model=ReferralListResponse)
async def list_referrals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    program_id: Optional[UUID] = Query(None),
    referrer_id: Optional[UUID] = Query(None),
    referee_id: Optional[UUID] = Query(None),
    status: Optional[List[ReferralStatus]] = Query(None),
    is_suspicious: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.referral.view")
):
    """Liste paginée des parrainages."""
    filters = ReferralFilters(
        search=search,
        program_id=program_id,
        referrer_id=referrer_id,
        referee_id=referee_id,
        status=status,
        is_suspicious=is_suspicious
    )
    items, total, pages = service.list_referrals(filters, page, page_size, sort_by, sort_dir)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.post("/referrals/{id}/qualify", response_model=ReferralResponse)
async def qualify_referral(
    id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.referral.edit")
):
    """Qualifie un parrainage pour récompense."""
    try:
        return service.qualify_referral(id)
    except ReferralNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ReferralStateError, FraudDetectedError, ProgramBudgetExceededError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/referrals/{id}/reject", response_model=ReferralResponse)
async def reject_referral(
    id: UUID,
    reason: str = Query("", max_length=500),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.referral.edit")
):
    """Rejette un parrainage."""
    try:
        return service.reject_referral(id, reason)
    except ReferralNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ReferralStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/referrals/{id}/flag-fraud", response_model=ReferralResponse)
async def flag_fraud(
    id: UUID,
    reason: FraudReason = Query(...),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.referral.edit")
):
    """Marque un parrainage comme frauduleux."""
    try:
        return service.flag_fraudulent(id, reason)
    except ReferralNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Reward Routes
# ============================================================================

@router.get("/users/{user_id}/rewards", response_model=List[RewardResponse])
async def list_user_rewards(
    user_id: UUID,
    is_claimed: Optional[bool] = Query(None),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.reward.view")
):
    """Liste les récompenses d'un utilisateur."""
    return service.list_rewards_for_user(user_id, is_claimed)


@router.post("/rewards/{id}/claim", response_model=RewardResponse)
async def claim_reward(
    id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.reward.edit")
):
    """Réclame une récompense."""
    try:
        return service.claim_reward(id)
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RewardAlreadyClaimedError, RewardExpiredError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Payout Routes
# ============================================================================

@router.get("/payouts", response_model=PayoutListResponse)
async def list_payouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[UUID] = Query(None),
    status: Optional[List[PayoutStatus]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.payout.view")
):
    """Liste paginée des paiements."""
    filters = PayoutFilters(user_id=user_id, status=status)
    items, total, pages = service.list_payouts(filters, page, page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.post("/payouts", response_model=PayoutResponse, status_code=201)
async def create_payout(
    data: PayoutCreate,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.payout.create")
):
    """Crée une demande de paiement."""
    try:
        return service.create_payout(data)
    except RewardNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PayoutValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payouts/{id}/process", response_model=PayoutResponse)
async def process_payout(
    id: UUID,
    transaction_reference: str = Query(..., min_length=1),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.payout.edit")
):
    """Traite un paiement."""
    try:
        return service.process_payout(id, transaction_reference)
    except PayoutNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PayoutStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Stats Routes
# ============================================================================

@router.get("/stats/programs", response_model=dict)
async def get_program_stats(
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.program.view")
):
    """Statistiques des programmes."""
    return service.get_program_stats()


@router.get("/stats/referrals", response_model=ReferralStats)
async def get_referral_stats(
    program_id: Optional[UUID] = Query(None),
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.referral.view")
):
    """Statistiques des parrainages."""
    return service.get_referral_stats(program_id)


@router.get("/referrers/{user_id}/profile", response_model=ReferrerProfile)
async def get_referrer_profile(
    user_id: UUID,
    service: ReferralService = Depends(get_service),
    _: None = require_permission("referral.referral.view")
):
    """Récupère le profil d'un parrain."""
    return service.get_referrer_profile(user_id)
