"""
AZALSCORE - IAM Users Router
Endpoints pour la gestion des utilisateurs
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_user
from app.core.models import User

from ..decorators import require_permission
from ..schemas import (
    PasswordChange,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from .helpers import get_service, user_to_response

router = APIRouter(tags=["users"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.user.create")
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Crée un nouvel utilisateur."""
    try:
        user = service.create_user(data, created_by=current_user.id)
        return user_to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users", response_model=UserListResponse)
@require_permission("iam.user.read")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    search: str | None = None,
    role_code: str | None = None,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Liste les utilisateurs avec pagination."""
    users, total = service.list_users(
        page=page,
        page_size=page_size,
        is_active=is_active,
        search=search,
        role_code=role_code
    )

    return UserListResponse(
        items=[user_to_response(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Récupère le profil de l'utilisateur connecté."""
    user = service.get_user(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return user_to_response(user)


@router.get("/users/{user_id}", response_model=UserResponse)
@require_permission("iam.user.read")
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Récupère un utilisateur par ID."""
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    return user_to_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
@require_permission("iam.user.update")
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Met à jour un utilisateur."""
    try:
        user = service.update_user(user_id, data, updated_by=current_user.id)
        return user_to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.user.delete")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Supprime un utilisateur (désactivation)."""
    if not service.delete_user(user_id, deleted_by=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/users/{user_id}/lock", response_model=UserResponse)
@require_permission("iam.user.admin")
async def lock_user(
    user_id: UUID,
    reason: str = Query(..., min_length=1),
    duration_minutes: int | None = Query(None, ge=1),
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Verrouille un utilisateur."""
    try:
        user = service.lock_user(user_id, reason, duration_minutes, locked_by=current_user.id)
        return user_to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/{user_id}/unlock", response_model=UserResponse)
@require_permission("iam.user.admin")
async def unlock_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Déverrouille un utilisateur."""
    try:
        user = service.unlock_user(user_id, unlocked_by=current_user.id)
        return user_to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Change le mot de passe de l'utilisateur connecté."""
    success, error = service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
