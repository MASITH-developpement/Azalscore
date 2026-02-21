"""
AZALS MODULE T0 - Router API IAM
================================

Endpoints REST pour la gestion des identités et accès.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
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
    """Dépendance pour obtenir le service IAM."""
    return get_iam_service(db, tenant_id)


# ============================================================================
# AUTHENTIFICATION
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
            groups=[g.code for g in user.groups]
        )
    )


@router.post("/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    service: IAMService = Depends(get_service)
):
    """Rafraîchit les tokens avec le refresh_token."""
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
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Déconnexion utilisateur."""
    # NOTE: Phase 2 - Extraire JTI du token pour révocation ciblée
    if data.all_sessions:
        service.revoke_all_sessions(current_user.id, "User logout all")


# ============================================================================
# UTILISATEURS
# ============================================================================

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.user.create")
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Crée un nouvel utilisateur."""
    try:
        user = service.create_user(data, created_by=current_user.id)
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
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
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
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Récupère le profil de l'utilisateur connecté."""
    user = service.get_user(current_user.id)
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
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Récupère un utilisateur par ID."""
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
    user_id: UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Met à jour un utilisateur."""
    try:
        user = service.update_user(user_id, data, updated_by=current_user.id)
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
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
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
    service: IAMService = Depends(get_service)
):
    """Verrouille un utilisateur."""
    try:
        user = service.lock_user(user_id, reason, duration_minutes, locked_by=current_user.id)
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
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Déverrouille un utilisateur."""
    try:
        user = service.unlock_user(user_id, unlocked_by=current_user.id)
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
# MOT DE PASSE
# ============================================================================

@router.post("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Change le mot de passe de l'utilisateur connecté."""
    success, error = service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


# ============================================================================
# RÔLES
# ============================================================================

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.role.create")
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Crée un nouveau rôle."""
    try:
        role = service.create_role(data, created_by=current_user.id)
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


@router.get("/roles", response_model=list[RoleResponse])
@require_permission("iam.role.read")
async def list_roles(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service),
    db: Session = Depends(get_db)
):
    """Liste tous les rôles."""
    from app.modules.iam.models import IAMUser

    roles = service.list_roles(include_inactive=include_inactive)

    # SÉCURITÉ: Récupérer les noms des créateurs (filtrer par tenant_id)
    creator_ids = [r.created_by for r in roles if r.created_by]
    creators = {}
    if creator_ids:
        creator_users = db.query(IAMUser).filter(
            IAMUser.tenant_id == service.tenant_id,
            IAMUser.id.in_(creator_ids)
        ).all()
        creators = {
            u.id: f"{u.first_name or ''} {u.last_name or ''}".strip() or u.email
            for u in creator_users
        }

    return [
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
            created_at=r.created_at,
            created_by_name=creators.get(r.created_by) if r.created_by else None
        )
        for r in roles
    ]


@router.get("/roles/{role_id}", response_model=RoleResponse)
@require_permission("iam.role.read")
async def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service),
    db: Session = Depends(get_db)
):
    """Récupère un rôle par ID."""
    from app.modules.iam.models import IAMUser

    role = service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")

    # SÉCURITÉ: Récupérer le nom du créateur (filtrer par tenant_id)
    created_by_name = None
    if role.created_by:
        creator = db.query(IAMUser).filter(
            IAMUser.tenant_id == service.tenant_id,
            IAMUser.id == role.created_by
        ).first()
        if creator:
            created_by_name = f"{creator.first_name or ''} {creator.last_name or ''}".strip() or creator.email

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


@router.patch("/roles/{role_id}", response_model=RoleResponse)
@require_permission("iam.role.update")
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Met à jour un rôle."""
    try:
        role = service.update_role(role_id, data, updated_by=current_user.id)
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
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Supprime un rôle."""
    try:
        if not service.delete_role(role_id, deleted_by=current_user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/roles/assign", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.assign")
async def assign_role(
    data: RoleAssignment,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Attribue un rôle à un utilisateur."""
    try:
        service.assign_role_to_user(
            user_id=data.user_id,
            role_code=data.role_code,
            granted_by=current_user.id,
            expires_at=data.expires_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/roles/revoke", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.assign")
async def revoke_role(
    data: RoleAssignment,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Retire un rôle à un utilisateur."""
    service.revoke_role_from_user(
        user_id=data.user_id,
        role_code=data.role_code,
        revoked_by=current_user.id
    )


# ============================================================================
# PERMISSIONS - Auto-générées depuis modules_registry
# ============================================================================

def _generate_capabilities_by_module() -> dict:
    """
    Génère automatiquement CAPABILITIES_BY_MODULE depuis modules_registry.
    Les modules avec overrides personnalisés sont préservés.
    """
    from app.core.modules_registry import MODULES

    # Modules avec capabilities personnalisées (ne pas auto-générer)
    CUSTOM_CAPABILITIES = _get_custom_capabilities()

    result = dict(CUSTOM_CAPABILITIES)

    # Générer les capabilities pour les modules non personnalisés
    for module in MODULES:
        code = module["code"].replace("-", "_")

        # Ignorer les imports (IMP1, IMP2, etc.)
        if code.startswith("IMP"):
            continue

        # Ignorer si déjà personnalisé
        if code in result:
            continue

        # Générer capabilities par défaut
        result[code] = {
            "name": module["name"],
            "icon": _get_icon_for_module(module.get("icon", "folder")),
            "capabilities": [
                {"code": f"{code}.view", "name": f"Voir {module['name']}", "description": f"Accès au module {module['name']}"},
                {"code": f"{code}.create", "name": f"Créer", "description": f"Créer dans {module['name']}"},
                {"code": f"{code}.edit", "name": f"Modifier", "description": f"Modifier dans {module['name']}"},
                {"code": f"{code}.delete", "name": f"Supprimer", "description": f"Supprimer dans {module['name']}"},
            ]
        }

    return result


def _get_icon_for_module(icon_code: str) -> str:
    """Convertit le code icône en nom Lucide React."""
    icon_map = {
        "book": "BookOpen", "file-text": "FileText", "dollar-sign": "DollarSign",
        "users": "Users", "credit-card": "CreditCard", "briefcase": "Briefcase",
        "package": "Package", "shopping-cart": "ShoppingCart", "user": "User",
        "settings": "Settings", "tool": "Wrench", "check-circle": "CheckCircle",
        "monitor": "Monitor", "shopping-bag": "ShoppingBag", "headphones": "Headphones",
        "bar-chart-2": "BarChart2", "shield": "Shield", "truck": "Truck",
        "bot": "Bot", "building": "Building", "file-signature": "FileSignature",
        "receipt": "Receipt", "clock": "Clock", "map-pin": "MapPin",
        "alert-circle": "AlertCircle", "shield-check": "ShieldCheck",
        "file-search": "FileSearch", "repeat": "Repeat", "store": "Store",
        "pen-tool": "PenTool", "mail": "Mail", "send": "Send", "globe": "Globe",
        "trending-up": "TrendingUp", "layers": "Layers", "check-square": "CheckSquare",
        "cpu": "Cpu", "share-2": "Share2", "smartphone": "Smartphone", "mic": "Mic",
        "database": "Database", "eye": "Eye", "key": "Key", "building-2": "Building2",
        "zap": "Zap", "download": "Download", "flag": "Flag", "lock": "Lock",
        "folder": "Folder",
    }
    return icon_map.get(icon_code, "Folder")


def _get_custom_capabilities() -> dict:
    """Capabilities personnalisées pour les modules complexes."""
    return {
    "cockpit": {
        "name": "Tableau de bord",
        "icon": "LayoutDashboard",
        "capabilities": [
            {"code": "cockpit.view", "name": "Voir le tableau de bord", "description": "Accès au cockpit principal"},
            {"code": "cockpit.decisions.view", "name": "Voir les décisions", "description": "Accès aux décisions stratégiques"},
        ]
    },
    "partners": {
        "name": "Partenaires",
        "icon": "Users",
        "capabilities": [
            {"code": "partners.view", "name": "Voir les partenaires", "description": "Accès en lecture aux partenaires"},
            {"code": "partners.create", "name": "Créer des partenaires", "description": "Créer de nouveaux partenaires"},
            {"code": "partners.edit", "name": "Modifier les partenaires", "description": "Modifier les partenaires existants"},
            {"code": "partners.delete", "name": "Supprimer les partenaires", "description": "Supprimer des partenaires"},
            {"code": "partners.clients.view", "name": "Voir les clients", "description": "Accès aux fiches clients"},
            {"code": "partners.clients.create", "name": "Créer des clients", "description": "Créer de nouveaux clients"},
            {"code": "partners.clients.edit", "name": "Modifier les clients", "description": "Modifier les clients"},
            {"code": "partners.clients.delete", "name": "Supprimer les clients", "description": "Supprimer des clients"},
            {"code": "partners.suppliers.view", "name": "Voir les fournisseurs", "description": "Accès aux fiches fournisseurs"},
            {"code": "partners.suppliers.create", "name": "Créer des fournisseurs", "description": "Créer de nouveaux fournisseurs"},
            {"code": "partners.suppliers.edit", "name": "Modifier les fournisseurs", "description": "Modifier les fournisseurs"},
            {"code": "partners.suppliers.delete", "name": "Supprimer les fournisseurs", "description": "Supprimer des fournisseurs"},
            {"code": "partners.contacts.view", "name": "Voir les contacts", "description": "Accès aux contacts"},
            {"code": "partners.contacts.create", "name": "Créer des contacts", "description": "Créer de nouveaux contacts"},
            {"code": "partners.contacts.edit", "name": "Modifier les contacts", "description": "Modifier les contacts"},
            {"code": "partners.contacts.delete", "name": "Supprimer les contacts", "description": "Supprimer des contacts"},
        ]
    },
    "contacts": {
        "name": "Contacts Unifiés",
        "icon": "Contact",
        "capabilities": [
            {"code": "contacts.view", "name": "Voir les contacts", "description": "Accès aux contacts unifiés"},
            {"code": "contacts.create", "name": "Créer des contacts", "description": "Créer de nouveaux contacts"},
            {"code": "contacts.edit", "name": "Modifier les contacts", "description": "Modifier les contacts"},
            {"code": "contacts.delete", "name": "Supprimer les contacts", "description": "Supprimer des contacts"},
        ]
    },
    "invoicing": {
        "name": "Facturation",
        "icon": "FileText",
        "capabilities": [
            {"code": "invoicing.view", "name": "Voir la facturation", "description": "Accès en lecture à la facturation"},
            {"code": "invoicing.create", "name": "Créer des documents", "description": "Créer devis/factures/avoirs"},
            {"code": "invoicing.edit", "name": "Modifier des documents", "description": "Modifier les documents"},
            {"code": "invoicing.delete", "name": "Supprimer des documents", "description": "Supprimer des documents"},
            {"code": "invoicing.send", "name": "Envoyer des documents", "description": "Envoyer par email"},
            {"code": "invoicing.quotes.view", "name": "Voir les devis", "description": "Accès aux devis"},
            {"code": "invoicing.quotes.create", "name": "Créer des devis", "description": "Créer de nouveaux devis"},
            {"code": "invoicing.quotes.edit", "name": "Modifier les devis", "description": "Modifier les devis"},
            {"code": "invoicing.quotes.delete", "name": "Supprimer les devis", "description": "Supprimer des devis"},
            {"code": "invoicing.quotes.send", "name": "Envoyer les devis", "description": "Envoyer les devis par email"},
            {"code": "invoicing.invoices.view", "name": "Voir les factures", "description": "Accès aux factures"},
            {"code": "invoicing.invoices.create", "name": "Créer des factures", "description": "Créer de nouvelles factures"},
            {"code": "invoicing.invoices.edit", "name": "Modifier les factures", "description": "Modifier les factures"},
            {"code": "invoicing.invoices.delete", "name": "Supprimer les factures", "description": "Supprimer des factures"},
            {"code": "invoicing.invoices.send", "name": "Envoyer les factures", "description": "Envoyer les factures par email"},
            {"code": "invoicing.credits.view", "name": "Voir les avoirs", "description": "Accès aux avoirs"},
            {"code": "invoicing.credits.create", "name": "Créer des avoirs", "description": "Créer de nouveaux avoirs"},
            {"code": "invoicing.credits.edit", "name": "Modifier les avoirs", "description": "Modifier les avoirs"},
            {"code": "invoicing.credits.delete", "name": "Supprimer les avoirs", "description": "Supprimer des avoirs"},
            {"code": "invoicing.credits.send", "name": "Envoyer les avoirs", "description": "Envoyer les avoirs par email"},
        ]
    },
    "treasury": {
        "name": "Trésorerie",
        "icon": "Wallet",
        "capabilities": [
            {"code": "treasury.view", "name": "Voir la trésorerie", "description": "Accès à la trésorerie"},
            {"code": "treasury.create", "name": "Créer des opérations", "description": "Créer des opérations"},
            {"code": "treasury.transfer.execute", "name": "Exécuter des virements", "description": "Exécuter des virements bancaires"},
            {"code": "treasury.accounts.view", "name": "Voir les comptes", "description": "Accès aux comptes bancaires"},
            {"code": "treasury.accounts.create", "name": "Créer des comptes", "description": "Créer de nouveaux comptes"},
            {"code": "treasury.accounts.edit", "name": "Modifier les comptes", "description": "Modifier les comptes"},
            {"code": "treasury.accounts.delete", "name": "Supprimer les comptes", "description": "Supprimer des comptes"},
        ]
    },
    "accounting": {
        "name": "Comptabilité",
        "icon": "Calculator",
        "capabilities": [
            {"code": "accounting.view", "name": "Voir la comptabilité", "description": "Accès à la comptabilité"},
            {"code": "accounting.journal.view", "name": "Voir les journaux", "description": "Accès aux journaux comptables"},
            {"code": "accounting.journal.delete", "name": "Supprimer des écritures", "description": "Supprimer des écritures comptables"},
        ]
    },
    "purchases": {
        "name": "Achats",
        "icon": "ShoppingCart",
        "capabilities": [
            {"code": "purchases.view", "name": "Voir les achats", "description": "Accès aux achats"},
            {"code": "purchases.create", "name": "Créer des achats", "description": "Créer des commandes d'achat"},
            {"code": "purchases.edit", "name": "Modifier les achats", "description": "Modifier les achats"},
            {"code": "purchases.orders.view", "name": "Voir les commandes", "description": "Accès aux commandes fournisseurs"},
            {"code": "purchases.orders.create", "name": "Créer des commandes", "description": "Créer des commandes"},
            {"code": "purchases.orders.edit", "name": "Modifier les commandes", "description": "Modifier les commandes"},
            {"code": "purchases.orders.delete", "name": "Supprimer les commandes", "description": "Supprimer des commandes"},
        ]
    },
    "projects": {
        "name": "Projets",
        "icon": "FolderKanban",
        "capabilities": [
            {"code": "projects.view", "name": "Voir les projets", "description": "Accès aux projets"},
            {"code": "projects.create", "name": "Créer des projets", "description": "Créer de nouveaux projets"},
            {"code": "projects.edit", "name": "Modifier les projets", "description": "Modifier les projets"},
            {"code": "projects.delete", "name": "Supprimer les projets", "description": "Supprimer des projets"},
        ]
    },
    "hr": {
        "name": "Ressources Humaines",
        "icon": "UserCog",
        "capabilities": [
            {"code": "hr.view", "name": "Voir les RH", "description": "Accès au module RH"},
            {"code": "hr.create", "name": "Créer des données RH", "description": "Créer des données RH"},
            {"code": "hr.edit", "name": "Modifier les données RH", "description": "Modifier les données RH"},
            {"code": "hr.delete", "name": "Supprimer les données RH", "description": "Supprimer des données RH"},
            {"code": "hr.employees.view", "name": "Voir les employés", "description": "Accès aux fiches employés"},
            {"code": "hr.employees.create", "name": "Créer des employés", "description": "Créer de nouveaux employés"},
            {"code": "hr.employees.edit", "name": "Modifier les employés", "description": "Modifier les employés"},
            {"code": "hr.employees.delete", "name": "Supprimer les employés", "description": "Supprimer des employés"},
            {"code": "hr.payroll.view", "name": "Voir la paie", "description": "Accès à la paie"},
            {"code": "hr.payroll.create", "name": "Créer des bulletins", "description": "Créer des bulletins de paie"},
            {"code": "hr.payroll.edit", "name": "Modifier la paie", "description": "Modifier les bulletins"},
            {"code": "hr.leave.view", "name": "Voir les congés", "description": "Accès aux congés"},
            {"code": "hr.leave.create", "name": "Créer des congés", "description": "Créer des demandes de congés"},
            {"code": "hr.leave.approve", "name": "Approuver les congés", "description": "Approuver/refuser les congés"},
        ]
    },
    "interventions": {
        "name": "Interventions",
        "icon": "Wrench",
        "capabilities": [
            {"code": "interventions.view", "name": "Voir les interventions", "description": "Accès aux interventions"},
            {"code": "interventions.create", "name": "Créer des interventions", "description": "Créer de nouvelles interventions"},
            {"code": "interventions.edit", "name": "Modifier les interventions", "description": "Modifier les interventions"},
            {"code": "interventions.tickets.view", "name": "Voir les tickets", "description": "Accès aux tickets"},
            {"code": "interventions.tickets.create", "name": "Créer des tickets", "description": "Créer de nouveaux tickets"},
            {"code": "interventions.tickets.edit", "name": "Modifier les tickets", "description": "Modifier les tickets"},
            {"code": "interventions.tickets.delete", "name": "Supprimer les tickets", "description": "Supprimer des tickets"},
        ]
    },
    "inventory": {
        "name": "Stock / Inventaire",
        "icon": "Package",
        "capabilities": [
            {"code": "inventory.view", "name": "Voir le stock", "description": "Accès au stock"},
            {"code": "inventory.create", "name": "Créer des articles", "description": "Créer des articles de stock"},
            {"code": "inventory.edit", "name": "Modifier le stock", "description": "Modifier le stock"},
            {"code": "inventory.delete", "name": "Supprimer du stock", "description": "Supprimer des articles"},
            {"code": "inventory.warehouses.view", "name": "Voir les entrepôts", "description": "Accès aux entrepôts"},
            {"code": "inventory.warehouses.create", "name": "Créer des entrepôts", "description": "Créer de nouveaux entrepôts"},
            {"code": "inventory.warehouses.edit", "name": "Modifier les entrepôts", "description": "Modifier les entrepôts"},
            {"code": "inventory.products.view", "name": "Voir les produits", "description": "Accès aux produits"},
            {"code": "inventory.products.create", "name": "Créer des produits", "description": "Créer de nouveaux produits"},
            {"code": "inventory.products.edit", "name": "Modifier les produits", "description": "Modifier les produits"},
            {"code": "inventory.movements.view", "name": "Voir les mouvements", "description": "Accès aux mouvements de stock"},
            {"code": "inventory.movements.create", "name": "Créer des mouvements", "description": "Créer des mouvements de stock"},
        ]
    },
    "ecommerce": {
        "name": "E-commerce",
        "icon": "Store",
        "capabilities": [
            {"code": "ecommerce.view", "name": "Voir l'e-commerce", "description": "Accès au module e-commerce"},
            {"code": "ecommerce.create", "name": "Créer des données", "description": "Créer des données e-commerce"},
            {"code": "ecommerce.edit", "name": "Modifier l'e-commerce", "description": "Modifier les données"},
            {"code": "ecommerce.delete", "name": "Supprimer des données", "description": "Supprimer des données"},
            {"code": "ecommerce.products.view", "name": "Voir les produits", "description": "Accès aux produits"},
            {"code": "ecommerce.products.create", "name": "Créer des produits", "description": "Créer de nouveaux produits"},
            {"code": "ecommerce.products.edit", "name": "Modifier les produits", "description": "Modifier les produits"},
            {"code": "ecommerce.products.delete", "name": "Supprimer les produits", "description": "Supprimer des produits"},
            {"code": "ecommerce.orders.view", "name": "Voir les commandes", "description": "Accès aux commandes"},
            {"code": "ecommerce.orders.create", "name": "Créer des commandes", "description": "Créer de nouvelles commandes"},
            {"code": "ecommerce.orders.edit", "name": "Modifier les commandes", "description": "Modifier les commandes"},
            {"code": "ecommerce.orders.delete", "name": "Supprimer les commandes", "description": "Supprimer des commandes"},
        ]
    },
    "crm": {
        "name": "CRM",
        "icon": "Heart",
        "capabilities": [
            {"code": "crm.view", "name": "Voir le CRM", "description": "Accès au CRM"},
            {"code": "crm.create", "name": "Créer des données CRM", "description": "Créer des opportunités/leads"},
            {"code": "crm.edit", "name": "Modifier le CRM", "description": "Modifier les données CRM"},
            {"code": "crm.delete", "name": "Supprimer du CRM", "description": "Supprimer des données CRM"},
        ]
    },
    "production": {
        "name": "Production",
        "icon": "Factory",
        "capabilities": [
            {"code": "production.view", "name": "Voir la production", "description": "Accès à la production"},
            {"code": "production.create", "name": "Créer des ordres", "description": "Créer des ordres de fabrication"},
            {"code": "production.edit", "name": "Modifier la production", "description": "Modifier les ordres"},
            {"code": "production.delete", "name": "Supprimer des ordres", "description": "Supprimer des ordres"},
        ]
    },
    "quality": {
        "name": "Qualité",
        "icon": "CheckCircle",
        "capabilities": [
            {"code": "quality.view", "name": "Voir la qualité", "description": "Accès au module qualité"},
            {"code": "quality.create", "name": "Créer des contrôles", "description": "Créer des contrôles qualité"},
            {"code": "quality.edit", "name": "Modifier la qualité", "description": "Modifier les contrôles"},
        ]
    },
    "maintenance": {
        "name": "Maintenance (GMAO)",
        "icon": "Settings",
        "capabilities": [
            {"code": "maintenance.view", "name": "Voir la maintenance", "description": "Accès à la GMAO"},
            {"code": "maintenance.create", "name": "Créer des interventions", "description": "Créer des interventions"},
            {"code": "maintenance.edit", "name": "Modifier la maintenance", "description": "Modifier les interventions"},
            {"code": "maintenance.delete", "name": "Supprimer des interventions", "description": "Supprimer des interventions"},
        ]
    },
    "pos": {
        "name": "Point de Vente",
        "icon": "CreditCard",
        "capabilities": [
            {"code": "pos.view", "name": "Voir le POS", "description": "Accès au point de vente"},
            {"code": "pos.create", "name": "Créer des ventes", "description": "Créer des ventes"},
            {"code": "pos.edit", "name": "Modifier le POS", "description": "Modifier les ventes"},
        ]
    },
    "subscriptions": {
        "name": "Abonnements",
        "icon": "Repeat",
        "capabilities": [
            {"code": "subscriptions.view", "name": "Voir les abonnements", "description": "Accès aux abonnements"},
            {"code": "subscriptions.create", "name": "Créer des abonnements", "description": "Créer de nouveaux abonnements"},
            {"code": "subscriptions.edit", "name": "Modifier les abonnements", "description": "Modifier les abonnements"},
            {"code": "subscriptions.delete", "name": "Supprimer les abonnements", "description": "Supprimer des abonnements"},
        ]
    },
    "helpdesk": {
        "name": "Helpdesk",
        "icon": "Headphones",
        "capabilities": [
            {"code": "helpdesk.view", "name": "Voir le helpdesk", "description": "Accès au helpdesk"},
            {"code": "helpdesk.create", "name": "Créer des tickets", "description": "Créer des tickets support"},
            {"code": "helpdesk.edit", "name": "Modifier les tickets", "description": "Modifier les tickets"},
        ]
    },
    "bi": {
        "name": "Business Intelligence",
        "icon": "BarChart3",
        "capabilities": [
            {"code": "bi.view", "name": "Voir les rapports", "description": "Accès aux rapports BI"},
            {"code": "bi.create", "name": "Créer des rapports", "description": "Créer de nouveaux rapports"},
            {"code": "bi.edit", "name": "Modifier les rapports", "description": "Modifier les rapports"},
        ]
    },
    "compliance": {
        "name": "Conformité",
        "icon": "Shield",
        "capabilities": [
            {"code": "compliance.view", "name": "Voir la conformité", "description": "Accès à la conformité"},
            {"code": "compliance.edit", "name": "Modifier la conformité", "description": "Gérer la conformité"},
        ]
    },
    "web": {
        "name": "Site Web",
        "icon": "Globe",
        "capabilities": [
            {"code": "web.view", "name": "Voir le site web", "description": "Accès au module web"},
            {"code": "web.edit", "name": "Modifier le site web", "description": "Modifier le contenu web"},
        ]
    },
    "marketplace": {
        "name": "Marketplace",
        "icon": "ShoppingBag",
        "capabilities": [
            {"code": "marketplace.view", "name": "Voir la marketplace", "description": "Accès à la marketplace"},
            {"code": "marketplace.edit", "name": "Modifier la marketplace", "description": "Gérer la marketplace"},
        ]
    },
    "payments": {
        "name": "Paiements",
        "icon": "Banknote",
        "capabilities": [
            {"code": "payments.view", "name": "Voir les paiements", "description": "Accès aux paiements"},
            {"code": "payments.create", "name": "Créer des paiements", "description": "Créer des paiements"},
        ]
    },
    "mobile": {
        "name": "Application Mobile",
        "icon": "Smartphone",
        "capabilities": [
            {"code": "mobile.view", "name": "Accès mobile", "description": "Accès à l'application mobile"},
        ]
    },
    "admin": {
        "name": "Administration",
        "icon": "Lock",
        "capabilities": [
            {"code": "admin.view", "name": "Accès administration", "description": "Accès au module admin"},
            {"code": "admin.users.view", "name": "Voir les utilisateurs", "description": "Voir la liste des utilisateurs"},
            {"code": "admin.users.create", "name": "Créer des utilisateurs", "description": "Créer de nouveaux utilisateurs"},
            {"code": "admin.users.edit", "name": "Modifier les utilisateurs", "description": "Modifier les utilisateurs"},
            {"code": "admin.users.delete", "name": "Supprimer les utilisateurs", "description": "Supprimer des utilisateurs"},
            {"code": "admin.roles.view", "name": "Voir les rôles", "description": "Voir la liste des rôles"},
            {"code": "admin.roles.create", "name": "Créer des rôles", "description": "Créer de nouveaux rôles"},
            {"code": "admin.roles.edit", "name": "Modifier les rôles", "description": "Modifier les rôles"},
            {"code": "admin.roles.delete", "name": "Supprimer les rôles", "description": "Supprimer des rôles"},
            {"code": "admin.tenants.view", "name": "Voir les tenants", "description": "Voir la liste des tenants"},
            {"code": "admin.tenants.create", "name": "Créer des tenants", "description": "Créer de nouveaux tenants"},
            {"code": "admin.tenants.delete", "name": "Supprimer les tenants", "description": "Supprimer des tenants"},
            {"code": "admin.modules.view", "name": "Voir les modules", "description": "Voir les modules activés"},
            {"code": "admin.modules.edit", "name": "Modifier les modules", "description": "Activer/désactiver des modules"},
            {"code": "admin.logs.view", "name": "Voir les logs", "description": "Accès aux journaux système"},
            {"code": "admin.root.break_glass", "name": "Break Glass", "description": "Accès d'urgence super admin"},
        ]
    },
    "iam": {
        "name": "Gestion des Accès (IAM)",
        "icon": "Key",
        "capabilities": [
            {"code": "iam.user.create", "name": "Créer des utilisateurs IAM", "description": "Créer des utilisateurs"},
            {"code": "iam.user.read", "name": "Voir les utilisateurs IAM", "description": "Voir les utilisateurs"},
            {"code": "iam.user.update", "name": "Modifier les utilisateurs IAM", "description": "Modifier les utilisateurs"},
            {"code": "iam.user.delete", "name": "Supprimer les utilisateurs IAM", "description": "Supprimer des utilisateurs"},
            {"code": "iam.user.admin", "name": "Administrer les utilisateurs", "description": "Administration complète"},
            {"code": "iam.role.create", "name": "Créer des rôles", "description": "Créer de nouveaux rôles"},
            {"code": "iam.role.read", "name": "Voir les rôles", "description": "Voir les rôles"},
            {"code": "iam.role.update", "name": "Modifier les rôles", "description": "Modifier les rôles"},
            {"code": "iam.role.delete", "name": "Supprimer les rôles", "description": "Supprimer des rôles"},
            {"code": "iam.role.assign", "name": "Assigner des rôles", "description": "Assigner des rôles aux utilisateurs"},
            {"code": "iam.group.create", "name": "Créer des groupes", "description": "Créer de nouveaux groupes"},
            {"code": "iam.group.read", "name": "Voir les groupes", "description": "Voir les groupes"},
            {"code": "iam.group.update", "name": "Modifier les groupes", "description": "Modifier les groupes"},
            {"code": "iam.group.delete", "name": "Supprimer les groupes", "description": "Supprimer des groupes"},
            {"code": "iam.permission.read", "name": "Voir les permissions", "description": "Voir les permissions"},
            {"code": "iam.permission.admin", "name": "Administrer les permissions", "description": "Gérer toutes les permissions"},
            {"code": "iam.invitation.create", "name": "Créer des invitations", "description": "Inviter des utilisateurs"},
            {"code": "iam.policy.read", "name": "Voir les politiques", "description": "Voir les politiques de sécurité"},
            {"code": "iam.policy.update", "name": "Modifier les politiques", "description": "Modifier les politiques"},
        ]
    },
    "marceau": {
        "name": "Marceau AI Assistant",
        "icon": "Bot",
        "capabilities": [
            {"code": "marceau.view", "name": "Voir Marceau", "description": "Accès au module Marceau AI"},
            {"code": "marceau.config.view", "name": "Voir la configuration", "description": "Voir la configuration Marceau"},
            {"code": "marceau.config.edit", "name": "Modifier la configuration", "description": "Modifier les paramètres Marceau"},
            {"code": "marceau.actions.view", "name": "Voir les actions", "description": "Voir l'historique des actions IA"},
            {"code": "marceau.actions.validate", "name": "Valider les actions", "description": "Valider/rejeter les actions IA"},
            {"code": "marceau.conversations.view", "name": "Voir les conversations", "description": "Accès aux conversations téléphoniques"},
            {"code": "marceau.memory.view", "name": "Voir la mémoire", "description": "Accès à la mémoire Marceau"},
            {"code": "marceau.memory.edit", "name": "Modifier la mémoire", "description": "Ajouter/supprimer des souvenirs"},
            {"code": "marceau.knowledge.view", "name": "Voir la base de connaissances", "description": "Accès aux documents"},
            {"code": "marceau.knowledge.edit", "name": "Modifier la base de connaissances", "description": "Upload/supprimer des documents"},
            {"code": "marceau.chat", "name": "Discuter avec Marceau", "description": "Utiliser le chat Marceau"},
        ]
    },
    "enrichment": {
        "name": "Enrichissement",
        "icon": "Sparkles",
        "capabilities": [
            {"code": "enrichment.view", "name": "Utiliser l'enrichissement", "description": "Accès aux fonctions d'auto-enrichissement"},
            {"code": "enrichment.siret", "name": "Recherche SIRET/SIREN", "description": "Rechercher des entreprises par SIRET/SIREN"},
            {"code": "enrichment.address", "name": "Autocomplete adresse", "description": "Utiliser l'autocomplete d'adresses"},
            {"code": "enrichment.barcode", "name": "Recherche code-barres", "description": "Rechercher des produits par code-barres"},
            {"code": "enrichment.risk_analysis", "name": "Analyse de risque", "description": "Accès a l'analyse de risque entreprise (donnees confidentielles)"},
            {"code": "enrichment.history", "name": "Historique enrichissement", "description": "Voir l'historique des enrichissements"},
            {"code": "enrichment.stats", "name": "Statistiques enrichissement", "description": "Voir les statistiques d'utilisation"},
        ]
    },
    # =========================================================================
    # NOUVEAUX MODULES (ajoutés automatiquement)
    # =========================================================================
    "ai_assistant": {
        "name": "Assistant IA",
        "icon": "Bot",
        "capabilities": [
            {"code": "ai_assistant.view", "name": "Voir l'assistant IA", "description": "Accès à l'assistant IA"},
            {"code": "ai_assistant.chat", "name": "Utiliser le chat IA", "description": "Discuter avec l'assistant"},
            {"code": "ai_assistant.config", "name": "Configurer l'assistant", "description": "Modifier les paramètres"},
        ]
    },
    "assets": {
        "name": "Immobilisations",
        "icon": "Building",
        "capabilities": [
            {"code": "assets.view", "name": "Voir les immobilisations", "description": "Accès aux immobilisations"},
            {"code": "assets.create", "name": "Créer des immobilisations", "description": "Créer de nouvelles immobilisations"},
            {"code": "assets.edit", "name": "Modifier les immobilisations", "description": "Modifier les immobilisations"},
            {"code": "assets.delete", "name": "Supprimer les immobilisations", "description": "Supprimer des immobilisations"},
        ]
    },
    "audit": {
        "name": "Audit",
        "icon": "Eye",
        "capabilities": [
            {"code": "audit.view", "name": "Voir les audits", "description": "Accès aux logs d'audit"},
            {"code": "audit.create", "name": "Créer des audits", "description": "Déclencher des audits"},
            {"code": "audit.export", "name": "Exporter les audits", "description": "Exporter les données d'audit"},
        ]
    },
    "autoconfig": {
        "name": "Configuration Auto",
        "icon": "Settings",
        "capabilities": [
            {"code": "autoconfig.view", "name": "Voir la configuration", "description": "Accès à l'auto-configuration"},
            {"code": "autoconfig.edit", "name": "Modifier la configuration", "description": "Modifier les paramètres"},
        ]
    },
    "automated_accounting": {
        "name": "Comptabilité Auto",
        "icon": "Calculator",
        "capabilities": [
            {"code": "automated_accounting.view", "name": "Voir la comptabilité auto", "description": "Accès à la comptabilisation automatique"},
            {"code": "automated_accounting.config", "name": "Configurer les règles", "description": "Gérer les règles de comptabilisation"},
            {"code": "automated_accounting.execute", "name": "Exécuter la comptabilisation", "description": "Lancer la comptabilisation automatique"},
        ]
    },
    "backup": {
        "name": "Sauvegardes",
        "icon": "Database",
        "capabilities": [
            {"code": "backup.view", "name": "Voir les sauvegardes", "description": "Accès aux sauvegardes"},
            {"code": "backup.create", "name": "Créer des sauvegardes", "description": "Créer de nouvelles sauvegardes"},
            {"code": "backup.restore", "name": "Restaurer", "description": "Restaurer depuis une sauvegarde"},
            {"code": "backup.delete", "name": "Supprimer des sauvegardes", "description": "Supprimer des sauvegardes"},
        ]
    },
    "broadcast": {
        "name": "Diffusion",
        "icon": "Send",
        "capabilities": [
            {"code": "broadcast.view", "name": "Voir les diffusions", "description": "Accès aux diffusions"},
            {"code": "broadcast.create", "name": "Créer des diffusions", "description": "Créer de nouvelles campagnes"},
            {"code": "broadcast.send", "name": "Envoyer des diffusions", "description": "Envoyer des campagnes"},
        ]
    },
    "commercial": {
        "name": "Commercial",
        "icon": "Briefcase",
        "capabilities": [
            {"code": "commercial.view", "name": "Voir le commercial", "description": "Accès au module commercial"},
            {"code": "commercial.create", "name": "Créer des opportunités", "description": "Créer des opportunités commerciales"},
            {"code": "commercial.edit", "name": "Modifier le commercial", "description": "Modifier les données"},
        ]
    },
    "complaints": {
        "name": "Réclamations",
        "icon": "AlertCircle",
        "capabilities": [
            {"code": "complaints.view", "name": "Voir les réclamations", "description": "Accès aux réclamations"},
            {"code": "complaints.create", "name": "Créer des réclamations", "description": "Créer de nouvelles réclamations"},
            {"code": "complaints.resolve", "name": "Résoudre les réclamations", "description": "Traiter et résoudre"},
        ]
    },
    "consolidation": {
        "name": "Consolidation",
        "icon": "Layers",
        "capabilities": [
            {"code": "consolidation.view", "name": "Voir la consolidation", "description": "Accès à la consolidation"},
            {"code": "consolidation.create", "name": "Créer des consolidations", "description": "Créer de nouvelles consolidations"},
            {"code": "consolidation.execute", "name": "Exécuter la consolidation", "description": "Lancer la consolidation"},
        ]
    },
    "contracts": {
        "name": "Contrats",
        "icon": "FileSignature",
        "capabilities": [
            {"code": "contracts.view", "name": "Voir les contrats", "description": "Accès aux contrats"},
            {"code": "contracts.create", "name": "Créer des contrats", "description": "Créer de nouveaux contrats"},
            {"code": "contracts.edit", "name": "Modifier les contrats", "description": "Modifier les contrats"},
            {"code": "contracts.delete", "name": "Supprimer les contrats", "description": "Supprimer des contrats"},
        ]
    },
    "country_packs": {
        "name": "Packs Pays",
        "icon": "Flag",
        "capabilities": [
            {"code": "country_packs.view", "name": "Voir les packs pays", "description": "Accès aux localisations"},
            {"code": "country_packs.install", "name": "Installer des packs", "description": "Installer de nouvelles localisations"},
        ]
    },
    "email": {
        "name": "Email",
        "icon": "Mail",
        "capabilities": [
            {"code": "email.view", "name": "Voir les emails", "description": "Accès aux emails"},
            {"code": "email.send", "name": "Envoyer des emails", "description": "Envoyer des emails"},
            {"code": "email.config", "name": "Configurer les emails", "description": "Paramètres email"},
        ]
    },
    "esignature": {
        "name": "Signature Électronique",
        "icon": "PenTool",
        "capabilities": [
            {"code": "esignature.view", "name": "Voir les signatures", "description": "Accès aux signatures"},
            {"code": "esignature.create", "name": "Créer des demandes", "description": "Créer des demandes de signature"},
            {"code": "esignature.sign", "name": "Signer des documents", "description": "Signer électroniquement"},
        ]
    },
    "expenses": {
        "name": "Notes de Frais",
        "icon": "Receipt",
        "capabilities": [
            {"code": "expenses.view", "name": "Voir les notes de frais", "description": "Accès aux notes de frais"},
            {"code": "expenses.create", "name": "Créer des notes de frais", "description": "Créer de nouvelles notes"},
            {"code": "expenses.approve", "name": "Approuver les notes", "description": "Approuver/rejeter les notes"},
            {"code": "expenses.reject", "name": "Rejeter les notes", "description": "Rejeter des notes de frais"},
        ]
    },
    "field_service": {
        "name": "Service Terrain",
        "icon": "MapPin",
        "capabilities": [
            {"code": "field_service.view", "name": "Voir le service terrain", "description": "Accès aux équipes terrain"},
            {"code": "field_service.create", "name": "Créer des missions", "description": "Créer de nouvelles missions"},
            {"code": "field_service.dispatch", "name": "Dispatcher les équipes", "description": "Assigner les techniciens"},
        ]
    },
    "finance": {
        "name": "Finance",
        "icon": "TrendingUp",
        "capabilities": [
            {"code": "finance.view", "name": "Voir la finance", "description": "Accès au module finance"},
            {"code": "finance.reports", "name": "Voir les rapports", "description": "Accès aux rapports financiers"},
            {"code": "finance.edit", "name": "Modifier les données", "description": "Modifier les données financières"},
        ]
    },
    "guardian": {
        "name": "Guardian",
        "icon": "Shield",
        "capabilities": [
            {"code": "guardian.view", "name": "Voir Guardian", "description": "Accès au module sécurité"},
            {"code": "guardian.config", "name": "Configurer Guardian", "description": "Paramètres de sécurité"},
            {"code": "guardian.alerts", "name": "Voir les alertes", "description": "Accès aux alertes de sécurité"},
        ]
    },
    "hr_vault": {
        "name": "Coffre-fort RH",
        "icon": "Lock",
        "capabilities": [
            {"code": "hr_vault.view", "name": "Voir le coffre RH", "description": "Accès au coffre-fort RH"},
            {"code": "hr_vault.access", "name": "Accéder aux documents", "description": "Consulter les documents RH"},
            {"code": "hr_vault.upload", "name": "Déposer des documents", "description": "Ajouter des documents"},
        ]
    },
    "odoo_import": {
        "name": "Import Odoo",
        "icon": "Download",
        "capabilities": [
            {"code": "odoo_import.view", "name": "Voir les imports", "description": "Accès aux imports Odoo"},
            {"code": "odoo_import.config", "name": "Configurer l'import", "description": "Paramètres d'import"},
            {"code": "odoo_import.execute", "name": "Exécuter l'import", "description": "Lancer l'import des données"},
        ]
    },
    "procurement": {
        "name": "Approvisionnement",
        "icon": "Truck",
        "capabilities": [
            {"code": "procurement.view", "name": "Voir les approvisionnements", "description": "Accès aux approvisionnements"},
            {"code": "procurement.create", "name": "Créer des demandes", "description": "Créer des demandes d'achat"},
            {"code": "procurement.edit", "name": "Modifier les demandes", "description": "Modifier les demandes"},
        ]
    },
    "qc": {
        "name": "Contrôle Qualité",
        "icon": "CheckSquare",
        "capabilities": [
            {"code": "qc.view", "name": "Voir les contrôles", "description": "Accès aux contrôles qualité"},
            {"code": "qc.create", "name": "Créer des contrôles", "description": "Créer de nouveaux contrôles"},
            {"code": "qc.validate", "name": "Valider les contrôles", "description": "Valider/rejeter les contrôles"},
        ]
    },
    "rfq": {
        "name": "Appels d'Offres",
        "icon": "FileSearch",
        "capabilities": [
            {"code": "rfq.view", "name": "Voir les appels d'offres", "description": "Accès aux appels d'offres"},
            {"code": "rfq.create", "name": "Créer des appels", "description": "Créer de nouveaux appels d'offres"},
            {"code": "rfq.respond", "name": "Répondre aux appels", "description": "Soumettre des réponses"},
        ]
    },
    "social_networks": {
        "name": "Réseaux Sociaux",
        "icon": "Share2",
        "capabilities": [
            {"code": "social_networks.view", "name": "Voir les réseaux sociaux", "description": "Accès aux réseaux sociaux"},
            {"code": "social_networks.post", "name": "Publier", "description": "Publier sur les réseaux"},
            {"code": "social_networks.config", "name": "Configurer", "description": "Paramètres des réseaux"},
        ]
    },
    "stripe_integration": {
        "name": "Intégration Stripe",
        "icon": "CreditCard",
        "capabilities": [
            {"code": "stripe_integration.view", "name": "Voir Stripe", "description": "Accès à l'intégration Stripe"},
            {"code": "stripe_integration.config", "name": "Configurer Stripe", "description": "Paramètres Stripe"},
        ]
    },
    "tenants": {
        "name": "Multi-Tenants",
        "icon": "Building2",
        "capabilities": [
            {"code": "tenants.view", "name": "Voir les tenants", "description": "Accès aux tenants"},
            {"code": "tenants.create", "name": "Créer des tenants", "description": "Créer de nouveaux tenants"},
            {"code": "tenants.edit", "name": "Modifier les tenants", "description": "Modifier les tenants"},
            {"code": "tenants.delete", "name": "Supprimer les tenants", "description": "Supprimer des tenants"},
        ]
    },
    "timesheet": {
        "name": "Feuilles de Temps",
        "icon": "Clock",
        "capabilities": [
            {"code": "timesheet.view", "name": "Voir les feuilles de temps", "description": "Accès aux feuilles de temps"},
            {"code": "timesheet.create", "name": "Créer des entrées", "description": "Saisir du temps"},
            {"code": "timesheet.approve", "name": "Approuver les feuilles", "description": "Approuver les feuilles de temps"},
        ]
    },
    "triggers": {
        "name": "Déclencheurs",
        "icon": "Zap",
        "capabilities": [
            {"code": "triggers.view", "name": "Voir les déclencheurs", "description": "Accès aux automatisations"},
            {"code": "triggers.create", "name": "Créer des déclencheurs", "description": "Créer des automatisations"},
            {"code": "triggers.edit", "name": "Modifier les déclencheurs", "description": "Modifier les automatisations"},
        ]
    },
    "warranty": {
        "name": "Garanties",
        "icon": "ShieldCheck",
        "capabilities": [
            {"code": "warranty.view", "name": "Voir les garanties", "description": "Accès aux garanties"},
            {"code": "warranty.create", "name": "Créer des garanties", "description": "Créer de nouvelles garanties"},
            {"code": "warranty.claim", "name": "Déclarer des sinistres", "description": "Faire des réclamations"},
        ]
    },
    "website": {
        "name": "Site Web Builder",
        "icon": "Globe",
        "capabilities": [
            {"code": "website.view", "name": "Voir le site web", "description": "Accès au constructeur de site"},
            {"code": "website.edit", "name": "Modifier le site", "description": "Éditer le contenu"},
            {"code": "website.publish", "name": "Publier", "description": "Publier les modifications"},
        ]
    },
    "workflows": {
        "name": "Workflows",
        "icon": "GitBranch",
        "capabilities": [
            {"code": "workflows.view", "name": "Voir les workflows", "description": "Accès aux workflows"},
            {"code": "workflows.create", "name": "Créer des workflows", "description": "Créer de nouveaux workflows"},
            {"code": "workflows.edit", "name": "Modifier les workflows", "description": "Modifier les workflows"},
        ]
    },
    # =========================================================================
    # MODULES UTILITAIRES ET TECHNIQUES
    # =========================================================================
    "cache": {
        "name": "Cache",
        "icon": "Database",
        "capabilities": [
            {"code": "cache.view", "name": "Voir le cache", "description": "Accès au gestionnaire de cache"},
            {"code": "cache.clear", "name": "Vider le cache", "description": "Purger le cache"},
        ]
    },
    "currency": {
        "name": "Devises",
        "icon": "CircleDollarSign",
        "capabilities": [
            {"code": "currency.view", "name": "Voir les devises", "description": "Accès aux devises"},
            {"code": "currency.edit", "name": "Modifier les taux", "description": "Modifier les taux de change"},
        ]
    },
    "dashboards": {
        "name": "Tableaux de Bord",
        "icon": "LayoutDashboard",
        "capabilities": [
            {"code": "dashboards.view", "name": "Voir les tableaux", "description": "Accès aux tableaux de bord"},
            {"code": "dashboards.create", "name": "Créer des tableaux", "description": "Créer des tableaux de bord"},
            {"code": "dashboards.edit", "name": "Modifier les tableaux", "description": "Modifier les tableaux"},
        ]
    },
    "dataexchange": {
        "name": "Échange de Données",
        "icon": "ArrowLeftRight",
        "capabilities": [
            {"code": "dataexchange.view", "name": "Voir les échanges", "description": "Accès aux échanges de données"},
            {"code": "dataexchange.export", "name": "Exporter", "description": "Exporter des données"},
            {"code": "dataexchange.import", "name": "Importer", "description": "Importer des données"},
        ]
    },
    "gateway": {
        "name": "Passerelle",
        "icon": "Network",
        "capabilities": [
            {"code": "gateway.view", "name": "Voir la passerelle", "description": "Accès à la passerelle"},
            {"code": "gateway.config", "name": "Configurer", "description": "Configurer la passerelle"},
        ]
    },
    "i18n": {
        "name": "Internationalisation",
        "icon": "Languages",
        "capabilities": [
            {"code": "i18n.view", "name": "Voir les traductions", "description": "Accès aux traductions"},
            {"code": "i18n.edit", "name": "Modifier les traductions", "description": "Modifier les traductions"},
        ]
    },
    "integrations": {
        "name": "Intégrations",
        "icon": "Plug",
        "capabilities": [
            {"code": "integrations.view", "name": "Voir les intégrations", "description": "Accès aux intégrations"},
            {"code": "integrations.config", "name": "Configurer", "description": "Configurer les intégrations"},
        ]
    },
    "notifications": {
        "name": "Notifications",
        "icon": "Bell",
        "capabilities": [
            {"code": "notifications.view", "name": "Voir les notifications", "description": "Accès aux notifications"},
            {"code": "notifications.config", "name": "Configurer", "description": "Configurer les notifications"},
            {"code": "notifications.send", "name": "Envoyer", "description": "Envoyer des notifications"},
        ]
    },
    "scheduler": {
        "name": "Planificateur",
        "icon": "Calendar",
        "capabilities": [
            {"code": "scheduler.view", "name": "Voir les tâches", "description": "Accès aux tâches planifiées"},
            {"code": "scheduler.create", "name": "Créer des tâches", "description": "Créer des tâches"},
            {"code": "scheduler.edit", "name": "Modifier les tâches", "description": "Modifier les tâches"},
        ]
    },
    "search": {
        "name": "Recherche",
        "icon": "Search",
        "capabilities": [
            {"code": "search.view", "name": "Rechercher", "description": "Accès à la recherche globale"},
            {"code": "search.advanced", "name": "Recherche avancée", "description": "Recherche avancée"},
        ]
    },
    "webhooks": {
        "name": "Webhooks",
        "icon": "Webhook",
        "capabilities": [
            {"code": "webhooks.view", "name": "Voir les webhooks", "description": "Accès aux webhooks"},
            {"code": "webhooks.create", "name": "Créer des webhooks", "description": "Créer de nouveaux webhooks"},
            {"code": "webhooks.edit", "name": "Modifier les webhooks", "description": "Modifier les webhooks"},
        ]
    },
    "import_data": {
        "name": "Import de Données",
        "icon": "Download",
        "capabilities": [
            {"code": "import_data.view", "name": "Voir les imports", "description": "Accès aux imports"},
            {"code": "import_data.odoo", "name": "Import Odoo", "description": "Importer depuis Odoo"},
            {"code": "import_data.axonaut", "name": "Import Axonaut", "description": "Importer depuis Axonaut"},
            {"code": "import_data.pennylane", "name": "Import Pennylane", "description": "Importer depuis Pennylane"},
            {"code": "import_data.sage", "name": "Import Sage", "description": "Importer depuis Sage"},
            {"code": "import_data.chorus", "name": "Import Chorus", "description": "Importer depuis Chorus Pro"},
        ]
    },
}


# Générer CAPABILITIES_BY_MODULE au chargement du module
# Combine les capabilities personnalisées avec celles auto-générées depuis modules_registry
CAPABILITIES_BY_MODULE = _generate_capabilities_by_module()


@router.get("/capabilities/modules")
@require_permission("iam.permission.read")
async def get_capabilities_by_module(
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Retourne toutes les capabilities groupées par module (auto-générées)."""
    return CAPABILITIES_BY_MODULE


@router.get("/permissions", response_model=PermissionListResponse)
@require_permission("iam.permission.read")
async def list_permissions(
    module: str | None = None,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Liste les permissions."""
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
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Vérifie si l'utilisateur a une permission."""
    user_id = data.user_id or current_user.id
    granted, source = service.check_permission(user_id, data.permission_code)

    return PermissionCheckResult(
        permission_code=data.permission_code,
        granted=granted,
        source=source
    )


@router.get("/users/{user_id}/permissions", response_model=list[str])
@require_permission("iam.permission.read")
async def get_user_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Récupère toutes les permissions d'un utilisateur."""
    return service.get_user_permissions(user_id)


class PermissionsUpdateRequest(BaseModel):
    """Request body pour mise à jour des permissions."""
    capabilities: list[str] = []
    permissions: list[str] = []  # Alias pour compatibilité


@router.put("/users/{user_id}/permissions", response_model=list[str])
@require_permission("iam.permission.admin")
async def update_user_permissions(
    user_id: UUID,
    data: PermissionsUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Met à jour les permissions d'un utilisateur."""
    # Accepte capabilities ou permissions
    perms = data.capabilities if data.capabilities else data.permissions
    return service.update_user_permissions(user_id, perms)


# ============================================================================
# GROUPES
# ============================================================================

@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.group.create")
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Crée un nouveau groupe."""
    try:
        group = service.create_group(data, created_by=current_user.id)
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
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Liste tous les groupes."""
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
    group_id: UUID,
    data: GroupMembership,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Ajoute des utilisateurs à un groupe."""
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for user_id in data.user_ids:
        service.add_user_to_group(user_id, group.code, added_by=current_user.id)


@router.delete("/groups/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.group.update")
async def remove_group_members(
    group_id: UUID,
    data: GroupMembership,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Retire des utilisateurs d'un groupe."""
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for user_id in data.user_ids:
        service.remove_user_from_group(user_id, group.code, removed_by=current_user.id)


# ============================================================================
# MFA
# ============================================================================

@router.post("/users/me/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Configure MFA pour l'utilisateur connecté."""
    secret, qr_uri, backup_codes = service.setup_mfa(current_user.id)

    return MFASetupResponse(
        secret=secret,
        qr_code_uri=qr_uri,
        backup_codes=backup_codes
    )


@router.post("/users/me/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_mfa(
    data: MFAVerify,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Vérifie et active MFA."""
    if not service.verify_mfa(current_user.id, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code MFA invalide"
        )


@router.post("/users/me/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_mfa(
    data: MFADisable,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Désactive MFA."""
    if not service.disable_mfa(current_user.id, data.password, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe ou code MFA invalide"
        )


# ============================================================================
# INVITATIONS
# ============================================================================

@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.invitation.create")
async def create_invitation(
    data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Crée une invitation."""
    try:
        invitation = service.create_invitation(
            email=data.email,
            role_codes=data.role_codes,
            group_codes=data.group_codes,
            expires_in_hours=data.expires_in_hours,
            invited_by=current_user.id
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
    """Accepte une invitation et crée le compte."""
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
# SESSIONS
# ============================================================================

@router.get("/users/me/sessions", response_model=SessionListResponse)
async def list_my_sessions(
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Liste les sessions de l'utilisateur connecté."""
    from .models import IAMSession, SessionStatus

    sessions = service.db.query(IAMSession).filter(
        IAMSession.user_id == current_user.id,
        IAMSession.tenant_id == service.tenant_id,
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
                is_current=False  # NOTE: Phase 2 - comparer avec JTI du token
            )
            for s in sessions
        ],
        total=len(sessions)
    )


@router.post("/users/me/sessions/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_sessions(
    data: SessionRevoke,
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
):
    """Révoque des sessions."""
    if data.session_ids:
        # Révoquer sessions spécifiques
        from .models import IAMSession, SessionStatus

        for session_id in data.session_ids:
            session = service.db.query(IAMSession).filter(
                IAMSession.id == session_id,
                IAMSession.user_id == current_user.id,
                IAMSession.tenant_id == service.tenant_id
            ).first()

            if session:
                session.status = SessionStatus.REVOKED
                session.revoked_at = datetime.utcnow()
                session.revoked_reason = data.reason or "User revoked"

        service.db.commit()
    else:
        # Révoquer toutes sauf courante
        service.revoke_all_sessions(current_user.id, data.reason or "User revoked all")


# ============================================================================
# POLITIQUE MOT DE PASSE
# ============================================================================

@router.get("/password-policy", response_model=PasswordPolicyResponse)
@require_permission("iam.policy.read")
async def get_password_policy(
    current_user: User = Depends(get_current_user),
    service: IAMService = Depends(get_service)
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
    service: IAMService = Depends(get_service)
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
