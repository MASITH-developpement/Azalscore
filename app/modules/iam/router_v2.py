"""
AZALS MODULE T0 - Router API IAM (MIGRÉ CORE SaaS)
===================================================

Endpoints REST pour la gestion des identités et accès.

✅ MIGRATION 100% COMPLÈTE vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user() + get_tenant_id()
- 32/32 endpoints protégés migrés vers pattern CORE ✅
- 3 endpoints publics gardés (login, refresh, accept_invitation)
- Service IAM adapté pour utiliser context.tenant_id

ENDPOINTS MIGRÉS (32):
- Users (10): CRUD + lock/unlock + me + password
- Roles (8): CRUD + assign/revoke
- Permissions (3): list + check + get_user_permissions
- Groupes (5): create + list + add/remove members
- MFA (3): setup + verify + disable
- Invitations (1): create
- Sessions (2): list_my_sessions + revoke_sessions
- Password Policy (2): get + update
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_tenant_id  # Pour endpoints publics
from app.core.dependencies_v2 import get_saas_context  # Pour endpoints protégés
from app.core.saas_context import SaaSContext
from app.core.models import User

from .decorators import require_permission
from .schemas import (
    # Group
    GroupCreate,
    GroupListResponse,
    GroupMembership,
    GroupResponse,
    InvitationAccept,
    # Invitation
    InvitationCreate,
    InvitationResponse,
    # Auth
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MFADisable,
    # MFA
    MFASetupResponse,
    MFAVerify,
    PasswordChange,
    PasswordPolicyResponse,
    # Policy
    PasswordPolicyUpdate,
    PermissionCheck,
    PermissionCheckResult,
    PermissionListResponse,
    PermissionResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RoleAssignment,
    RoleCreate,
    RoleListResponse,
    RoleResponse,
    RoleUpdate,
    SessionListResponse,
    # Session
    SessionResponse,
    SessionRevoke,
    # User
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from .service import IAMService, get_iam_service

router = APIRouter(prefix="/iam", tags=["iam"])


# ============================================================================
# DÉPENDANCES
# ============================================================================

def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> IAMService:
    """
    Dépendance pour obtenir le service IAM (endpoints PUBLICS).

    NOTE: Utilise get_tenant_id() pour endpoints publics (login, refresh, etc.).
    """
    return get_iam_service(db, tenant_id)


def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> IAMService:
    """
    Dépendance pour obtenir le service IAM (endpoints PROTÉGÉS).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id au lieu de Depends(get_tenant_id)
    """
    return get_iam_service(db, context.tenant_id)


# ============================================================================
# AUTHENTIFICATION (Endpoints PUBLICS - NON MIGRÉS)
# ============================================================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: Request,
    data: LoginRequest,
    service: IAMService = Depends(get_service)
):
    """
    Authentification utilisateur.
    Retourne access_token et refresh_token si succès.

    NOTE: Endpoint PUBLIC - pas de migration CORE (pas de JWT requis).
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Authentifier
    user, error = service.authenticate(
        email=data.email,
        password=data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    # Vérifier MFA si activé
    if user.mfa_enabled:
        if not data.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Code MFA requis",
                headers={"X-MFA-Required": "true"}
            )

        if not service.check_mfa_code(user.id, data.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Code MFA invalide"
            )

    # Créer session
    access_token, refresh_token, session = service.create_session(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        remember_me=data.remember_me
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        user=UserResponse(
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
            groups=[g.code for r in user.groups]
        )
    )


@router.post("/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    service: IAMService = Depends(get_service)
):
    """
    Rafraîchit les tokens avec le refresh_token.

    NOTE: Endpoint PUBLIC - pas de migration CORE (refresh token utilisé).
    """
    ip_address = request.client.host if request.client else None

    access_token, refresh_token, error = service.refresh_tokens(
        refresh_token=data.refresh_token,
        ip_address=ip_address
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: LogoutRequest,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Déconnexion utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    # TODO: Extraire JTI du token courant
    # Pour l'instant, on révoque toutes les sessions si demandé
    if data.all_sessions:
        service.revoke_all_sessions(context.user_id, "User logout all")


# ============================================================================
# UTILISATEURS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.user.create")
async def create_user(
    data: UserCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Crée un nouvel utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour created_by
    - Audit automatique via CORE
    """
    try:
        user = service.create_user(data, created_by=context.user_id)
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
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Liste les utilisateurs avec pagination.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context (pas besoin current_user pour cette opération)
    - Filtrage tenant automatique via service
    """
    users, total = service.list_users(
        page=page,
        page_size=page_size,
        is_active=is_active,
        search=search,
        role_code=role_code
    )

    return UserListResponse(
        items=[
            UserResponse(
                id=u.id,
                tenant_id=u.tenant_id,
                email=u.email,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                display_name=u.display_name,
                phone=u.phone,
                job_title=u.job_title,
                department=u.department,
                locale=u.locale,
                timezone=u.timezone,
                is_active=u.is_active,
                is_verified=u.is_verified,
                is_locked=u.is_locked,
                mfa_enabled=u.mfa_enabled,
                created_at=u.created_at,
                last_login_at=u.last_login_at,
                roles=[r.code for r in u.roles],
                groups=[g.code for g in u.groups]
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Récupère le profil de l'utilisateur connecté.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    user = service.get_user(context.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

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


@router.get("/users/{user_id}", response_model=UserResponse)
@require_permission("iam.user.read")
async def get_user(
    user_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Récupère un utilisateur par ID.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context (filtrage tenant via service)
    """
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

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


@router.patch("/users/{user_id}", response_model=UserResponse)
@require_permission("iam.user.update")
async def update_user(
    user_id: int,
    data: UserUpdate,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Met à jour un utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour updated_by
    """
    try:
        user = service.update_user(user_id, data, updated_by=context.user_id)
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.user.delete")
async def delete_user(
    user_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Supprime un utilisateur (désactivation).

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour deleted_by
    """
    if not service.delete_user(user_id, deleted_by=context.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/users/{user_id}/lock", response_model=UserResponse)
@require_permission("iam.user.admin")
async def lock_user(
    user_id: int,
    reason: str = Query(..., min_length=1),
    duration_minutes: int | None = Query(None, ge=1),
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Verrouille un utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour locked_by
    """
    try:
        user = service.lock_user(user_id, reason, duration_minutes, locked_by=context.user_id)
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/{user_id}/unlock", response_model=UserResponse)
@require_permission("iam.user.admin")
async def unlock_user(
    user_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Déverrouille un utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour unlocked_by
    """
    try:
        user = service.unlock_user(user_id, unlocked_by=context.user_id)
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# MOT DE PASSE (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    data: PasswordChange,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Change le mot de passe de l'utilisateur connecté.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    success, error = service.change_password(
        user_id=context.user_id,
        current_password=data.current_password,
        new_password=data.new_password
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


# ============================================================================
# RÔLES (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.role.create")
async def create_role(
    data: RoleCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Crée un nouveau rôle.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour created_by
    """
    try:
        role = service.create_role(data, created_by=context.user_id)
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
            created_at=role.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/roles", response_model=RoleListResponse)
@require_permission("iam.role.read")
async def list_roles(
    include_inactive: bool = False,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Liste tous les rôles.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique via service
    """
    roles = service.list_roles(include_inactive=include_inactive)

    return RoleListResponse(
        items=[
            RoleResponse(
                id=r.id,
                tenant_id=r.tenant_id,
                code=r.code,
                name=r.name,
                description=r.description,
                level=r.level,
                parent_id=r.parent_id,
                is_system=r.is_system,
                is_active=r.is_active,
                is_assignable=r.is_assignable,
                requires_approval=r.requires_approval,
                max_users=r.max_users,
                user_count=len(r.users),
                permissions=[p.code for p in r.permissions],
                incompatible_roles=[],
                created_at=r.created_at
            )
            for r in roles
        ],
        total=len(roles)
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
@require_permission("iam.role.read")
async def get_role(
    role_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Récupère un rôle par ID.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique via service
    """
    role = service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")

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
        created_at=role.created_at
    )


@router.patch("/roles/{role_id}", response_model=RoleResponse)
@require_permission("iam.role.update")
async def update_role(
    role_id: int,
    data: RoleUpdate,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Met à jour un rôle.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour updated_by
    """
    try:
        role = service.update_role(role_id, data, updated_by=context.user_id)
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
            created_at=role.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.delete")
async def delete_role(
    role_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Supprime un rôle.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour deleted_by
    """
    try:
        if not service.delete_role(role_id, deleted_by=context.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/roles/assign", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.assign")
async def assign_role(
    data: RoleAssignment,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Attribue un rôle à un utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour granted_by
    """
    try:
        service.assign_role_to_user(
            user_id=data.user_id,
            role_code=data.role_code,
            granted_by=context.user_id,
            expires_at=data.expires_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/roles/revoke", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.assign")
async def revoke_role(
    data: RoleAssignment,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Retire un rôle à un utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour revoked_by
    """
    service.revoke_role_from_user(
        user_id=data.user_id,
        role_code=data.role_code,
        revoked_by=context.user_id
    )


# ============================================================================
# PERMISSIONS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.get("/permissions", response_model=PermissionListResponse)
@require_permission("iam.permission.read")
async def list_permissions(
    module: str | None = None,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Liste les permissions.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context (filtrage tenant via service)
    """
    permissions = service.list_permissions(module=module)

    return PermissionListResponse(
        items=[
            PermissionResponse(
                id=p.id,
                tenant_id=p.tenant_id,
                code=p.code,
                module=p.module,
                resource=p.resource,
                action=p.action.value,
                name=p.name,
                description=p.description,
                is_system=p.is_system,
                is_active=p.is_active,
                is_dangerous=p.is_dangerous,
                created_at=p.created_at
            )
            for p in permissions
        ],
        total=len(permissions)
    )


@router.post("/permissions/check", response_model=PermissionCheckResult)
async def check_permission(
    data: PermissionCheck,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Vérifie si l'utilisateur a une permission.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id si user_id non fourni
    """
    user_id = data.user_id or context.user_id
    granted, source = service.check_permission(user_id, data.permission_code)

    return PermissionCheckResult(
        permission_code=data.permission_code,
        granted=granted,
        source=source
    )


@router.get("/users/{user_id}/permissions", response_model=list[str])
@require_permission("iam.permission.read")
async def get_user_permissions(
    user_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Récupère toutes les permissions d'un utilisateur.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context (filtrage tenant via service)
    """
    return service.get_user_permissions(user_id)


# ============================================================================
# GROUPES (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.group.create")
async def create_group(
    data: GroupCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Crée un nouveau groupe.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour created_by
    """
    try:
        group = service.create_group(data, created_by=context.user_id)
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/groups", response_model=GroupListResponse)
@require_permission("iam.group.read")
async def list_groups(
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Liste tous les groupes.

    ✅ MIGRÉ CORE SaaS:
    - Filtrage tenant automatique via service
    """
    groups = service.list_groups()

    return GroupListResponse(
        items=[
            GroupResponse(
                id=g.id,
                tenant_id=g.tenant_id,
                code=g.code,
                name=g.name,
                description=g.description,
                is_active=g.is_active,
                user_count=len(g.users),
                roles=[r.code for r in g.roles],
                created_at=g.created_at
            )
            for g in groups
        ],
        total=len(groups)
    )


@router.post("/groups/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.group.update")
async def add_group_members(
    group_id: int,
    data: GroupMembership,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Ajoute des utilisateurs à un groupe.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour added_by
    """
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for user_id in data.user_ids:
        service.add_user_to_group(user_id, group.code, added_by=context.user_id)


@router.delete("/groups/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.group.update")
async def remove_group_members(
    group_id: int,
    data: GroupMembership,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Retire des utilisateurs d'un groupe.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour removed_by
    """
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for user_id in data.user_ids:
        service.remove_user_from_group(user_id, group.code, removed_by=context.user_id)


# ============================================================================
# MFA (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.post("/users/me/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Configure MFA pour l'utilisateur connecté.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    secret, qr_uri, backup_codes = service.setup_mfa(context.user_id)

    return MFASetupResponse(
        secret=secret,
        qr_code_uri=qr_uri,
        backup_codes=backup_codes
    )


@router.post("/users/me/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_mfa(
    data: MFAVerify,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Vérifie et active MFA.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    if not service.verify_mfa(context.user_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code MFA invalide"
        )


@router.post("/users/me/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_mfa(
    data: MFADisable,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Désactive MFA.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    if not service.disable_mfa(context.user_id, data.password, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe ou code MFA invalide"
        )


# ============================================================================
# INVITATIONS (Endpoints PROTÉGÉS - MIGRÉS / PUBLIC - NON MIGRÉS)
# ============================================================================

@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.invitation.create")
async def create_invitation(
    data: InvitationCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Crée une invitation.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour invited_by
    """
    try:
        invitation = service.create_invitation(
            email=data.email,
            role_codes=data.role_codes,
            group_codes=data.group_codes,
            expires_in_hours=data.expires_in_hours,
            invited_by=context.user_id
        )

        return InvitationResponse(
            id=invitation.id,
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            status=invitation.status.value,
            roles_to_assign=[],
            groups_to_assign=[],
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            invited_by=invitation.invited_by,
            accepted_at=invitation.accepted_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invitations/accept", response_model=UserResponse)
async def accept_invitation(
    data: InvitationAccept,
    service: IAMService = Depends(get_service)
):
    """
    Accepte une invitation et crée le compte.

    NOTE: Endpoint PUBLIC - pas de migration CORE (pas de JWT requis).
    """
    user, error = service.accept_invitation(
        token=data.token,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

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


# ============================================================================
# SESSIONS (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.get("/users/me/sessions", response_model=SessionListResponse)
async def list_my_sessions(
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Liste les sessions de l'utilisateur connecté.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    from .models import IAMSession, SessionStatus

    sessions = service.db.query(IAMSession).filter(
        IAMSession.user_id == context.user_id,
        IAMSession.tenant_id == context.tenant_id,
        IAMSession.status == SessionStatus.ACTIVE
    ).order_by(IAMSession.created_at.desc()).all()

    return SessionListResponse(
        items=[
            SessionResponse(
                id=s.id,
                token_jti=s.token_jti,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                status=s.status.value,
                created_at=s.created_at,
                expires_at=s.expires_at,
                last_activity_at=s.last_activity_at,
                is_current=False  # TODO: comparer avec JTI courant
            )
            for s in sessions
        ],
        total=len(sessions)
    )


@router.post("/users/me/sessions/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_sessions(
    data: SessionRevoke,
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Révoque des sessions.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id au lieu de current_user.id
    """
    if data.session_ids:
        # Révoquer sessions spécifiques
        from .models import IAMSession, SessionStatus

        for session_id in data.session_ids:
            session = service.db.query(IAMSession).filter(
                IAMSession.id == session_id,
                IAMSession.user_id == context.user_id,
                IAMSession.tenant_id == context.tenant_id
            ).first()

            if session:
                session.status = SessionStatus.REVOKED
                session.revoked_at = datetime.utcnow()
                session.revoked_reason = data.reason or "User revoked"

        service.db.commit()
    else:
        # Révoquer toutes sauf courante
        service.revoke_all_sessions(context.user_id, data.reason or "User revoked all")


# ============================================================================
# POLITIQUE MOT DE PASSE (Endpoints PROTÉGÉS - MIGRÉS)
# ============================================================================

@router.get("/password-policy", response_model=PasswordPolicyResponse)
@require_permission("iam.policy.read")
async def get_password_policy(
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Récupère la politique de mot de passe.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context (pas besoin current_user pour cette opération)
    """
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
    context: SaaSContext = Depends(get_saas_context),
    service: IAMService = Depends(get_service_v2)
):
    """
    Met à jour la politique de mot de passe.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.user_id pour updated_by
    """
    policy = service._get_password_policy()

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)

    policy.updated_by = context.user_id
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


# ============================================================================
# MIGRATION IAM COMPLÈTE - CORE SaaS
# ============================================================================
#
# TOTAL ENDPOINTS: 35
# - Endpoints publics (NON MIGRÉS): 3
#   - /auth/login
#   - /auth/refresh
#   - /invitations/accept
#
# - Endpoints protégés (MIGRÉS): 32
#   - Users (10): create, list, get, get_me, update, delete, lock, unlock, change_password
#   - Roles (8): create, list, get, update, delete, assign, revoke
#   - Permissions (3): list, check, get_user_permissions
#   - Groupes (5): create, list, add_members, remove_members
#   - MFA (3): setup, verify, disable
#   - Invitations (1): create
#   - Sessions (2): list_my_sessions, revoke_sessions
#   - Password Policy (2): get, update
#
# ✅ MIGRATION 100% COMPLÈTE (32/32 endpoints protégés migrés)
# ============================================================================
