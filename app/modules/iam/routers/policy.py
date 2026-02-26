"""
AZALSCORE - IAM Password Policy Router
Endpoints pour la politique de mot de passe
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.models import User

from ..decorators import require_permission
from ..schemas import PasswordPolicyResponse, PasswordPolicyUpdate
from .helpers import get_service

router = APIRouter(tags=["policy"])


@router.get("/password-policy", response_model=PasswordPolicyResponse)
@require_permission("iam.policy.read")
async def get_password_policy(
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Récupère la politique de mot de passe."""
    policy = service._get_password_policy()
    return PasswordPolicyResponse(
        tenant_id=policy.tenant_id,
        min_length=policy.min_length,
        require_uppercase=policy.require_uppercase,
        require_lowercase=policy.require_lowercase,
        require_numbers=policy.require_numbers,
        require_special=policy.require_special,
        password_history_count=policy.password_history_count,
        password_expires_days=policy.password_expires_days,
        max_failed_attempts=policy.max_failed_attempts,
        lockout_duration_minutes=policy.lockout_duration_minutes
    )


@router.patch("/password-policy", response_model=PasswordPolicyResponse)
@require_permission("iam.policy.update")
async def update_password_policy(
    data: PasswordPolicyUpdate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Met à jour la politique de mot de passe."""
    policy = service._get_password_policy()

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)

    policy.updated_by = current_user.id
    service.db.commit()

    return PasswordPolicyResponse(
        tenant_id=policy.tenant_id,
        min_length=policy.min_length,
        require_uppercase=policy.require_uppercase,
        require_lowercase=policy.require_lowercase,
        require_numbers=policy.require_numbers,
        require_special=policy.require_special,
        password_history_count=policy.password_history_count,
        password_expires_days=policy.password_expires_days,
        max_failed_attempts=policy.max_failed_attempts,
        lockout_duration_minutes=policy.lockout_duration_minutes
    )
