"""
AZALSCORE - IAM Router Helpers
Fonctions utilitaires partagées par les routers
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_tenant_id

from ..service import IAMService, get_iam_service
from ..schemas import UserResponse, RoleResponse, GroupResponse


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> IAMService:
    """Dépendance pour obtenir le service IAM."""
    return get_iam_service(db, tenant_id)


def user_to_response(user) -> UserResponse:
    """Convertit un utilisateur IAM en réponse API."""
    return UserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        phone=user.phone,
        job_title=user.job_title,
        department=user.department,
        locale=user.locale,
        timezone=user.timezone,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_locked=user.is_locked,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        roles=[r.code for r in user.roles],
        groups=[g.code for g in user.groups]
    )


def role_to_response(
    role,
    created_by_name: str | None = None
) -> RoleResponse:
    """Convertit un rôle IAM en réponse API."""
    return RoleResponse(
        id=role.id,
        tenant_id=role.tenant_id,
        code=role.code,
        name=role.name,
        description=role.description,
        level=role.level,
        parent_id=role.parent_id,
        is_system=role.is_system,
        is_active=role.is_active,
        is_assignable=role.is_assignable,
        requires_approval=role.requires_approval,
        max_users=role.max_users,
        user_count=len(role.users),
        permissions=[p.code for p in role.permissions],
        incompatible_roles=[],
        created_at=role.created_at,
        created_by_name=created_by_name
    )


def group_to_response(group) -> GroupResponse:
    """Convertit un groupe IAM en réponse API."""
    return GroupResponse(
        id=group.id,
        tenant_id=group.tenant_id,
        code=group.code,
        name=group.name,
        description=group.description,
        is_active=group.is_active,
        user_count=len(group.users),
        roles=[r.code for r in group.roles],
        created_at=group.created_at
    )
