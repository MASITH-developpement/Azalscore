"""
AZALS - Endpoints Authentification SÉCURISÉS
=============================================
Login et Register pour utilisateurs DIRIGEANT.
Rate limiting strict sur tous les endpoints auth.
"""

import time
from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User, UserRole
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.two_factor import TwoFactorService

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# RATE LIMITING STRICT POUR AUTH
# ============================================================================

class AuthRateLimiter:
    """
    Rate limiter STRICT pour endpoints d'authentification.
    Protection contre brute force et credential stuffing.
    """

    def __init__(self):
        self._login_attempts: dict[str, list[float]] = defaultdict(list)
        self._register_attempts: dict[str, list[float]] = defaultdict(list)
        self._failed_logins: dict[str, int] = defaultdict(int)

    def _cleanup_old_attempts(self, attempts: list[float], window_seconds: int = 60) -> list[float]:
        """Supprime les tentatives hors fenêtre."""
        cutoff = time.time() - window_seconds
        return [t for t in attempts if t > cutoff]

    def check_login_rate(self, ip: str, email: str) -> None:
        """Vérifie le rate limit pour login."""
        settings = get_settings()
        limit = settings.auth_rate_limit_per_minute

        # Nettoyage
        self._login_attempts[ip] = self._cleanup_old_attempts(self._login_attempts[ip])
        self._login_attempts[email] = self._cleanup_old_attempts(self._login_attempts[email])

        # Vérification par IP
        if len(self._login_attempts[ip]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts from this IP. Wait 60 seconds.",
                headers={"Retry-After": "60"}
            )

        # Vérification par email (3x plus permissif)
        if len(self._login_attempts[email]) >= limit * 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts for this account. Wait 60 seconds.",
                headers={"Retry-After": "60"}
            )

        # Blocage si trop d'échecs consécutifs
        if self._failed_logins[email] >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to failed attempts. Wait 15 minutes.",
                headers={"Retry-After": "900"}
            )

    def record_login_attempt(self, ip: str, email: str, success: bool) -> None:
        """Enregistre une tentative de login."""
        now = time.time()
        self._login_attempts[ip].append(now)
        self._login_attempts[email].append(now)

        if success:
            self._failed_logins[email] = 0
        else:
            self._failed_logins[email] += 1

    def check_register_rate(self, ip: str) -> None:
        """Vérifie le rate limit pour registration (plus strict)."""
        self._register_attempts[ip] = self._cleanup_old_attempts(
            self._register_attempts[ip], window_seconds=300  # 5 minutes
        )

        # Max 3 registrations par 5 minutes par IP
        if len(self._register_attempts[ip]) >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts. Wait 5 minutes.",
                headers={"Retry-After": "300"}
            )

    def record_register_attempt(self, ip: str) -> None:
        """Enregistre une tentative d'inscription."""
        self._register_attempts[ip].append(time.time())


# Instance globale du rate limiter
auth_rate_limiter = AuthRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extrait l'IP client de manière sécurisée."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


def get_bootstrap_secret() -> str:
    """
    Récupère le secret de bootstrap depuis la config.
    Erreur FATALE si non configuré en production.
    """
    settings = get_settings()

    if settings.bootstrap_secret:
        return settings.bootstrap_secret

    # En développement/test, autoriser un secret par défaut (avec warning)
    if settings.is_development:
        import warnings
        warnings.warn(
            "BOOTSTRAP_SECRET non configuré - utilisation valeur dev. "
            "CONFIGURER OBLIGATOIREMENT EN PRODUCTION!",
            UserWarning, stacklevel=2
        )
        return "dev-bootstrap-secret-change-in-production-min32chars"

    # En production, erreur fatale
    raise ValueError("BOOTSTRAP_SECRET est OBLIGATOIRE en production")


# ===== SCHÉMAS PYDANTIC =====

class UserRegister(BaseModel):
    """Schéma pour l'inscription d'un nouveau DIRIGEANT."""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schéma pour la connexion."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema de reponse apres login (ancien format)."""
    access_token: str
    token_type: str
    tenant_id: str
    role: str


class UserResponse(BaseModel):
    """Schema de reponse utilisateur."""
    id: int
    email: str
    tenant_id: str
    role: str
    full_name: str | None = None

    model_config = {"from_attributes": True}


class TokensSchema(BaseModel):
    """Schema des tokens."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Schema de reponse login compatible frontend."""
    user: UserResponse
    tokens: TokensSchema
    tenant_id: str
    must_change_password: bool = False


# ===== SCHÉMAS 2FA =====

class TwoFactorSetupResponse(BaseModel):
    """Réponse setup 2FA avec QR code."""
    secret: str
    provisioning_uri: str
    qr_code_data: str
    backup_codes: list[str]
    message: str


class TwoFactorVerifyRequest(BaseModel):
    """Requête de vérification 2FA."""
    code: str = Field(..., min_length=6, max_length=10)


class TwoFactorLoginRequest(BaseModel):
    """Requête login avec 2FA."""
    pending_token: str
    code: str = Field(..., min_length=6, max_length=10)


class TwoFactorStatusResponse(BaseModel):
    """Statut 2FA d'un utilisateur."""
    enabled: bool
    verified_at: str | None = None
    has_backup_codes: bool
    required: bool


class LoginResponseWith2FA(BaseModel):
    """Réponse login quand 2FA est requis."""
    requires_2fa: bool = True
    pending_token: str
    message: str = "2FA verification required"


# ===== ENDPOINTS SÉCURISÉS =====

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    user_data: UserRegister,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Création d'un nouveau compte DIRIGEANT.
    RATE LIMITED: Max 3 inscriptions par 5 minutes par IP.
    """
    # SÉCURITÉ: Rate limiting strict
    client_ip = get_client_ip(request)
    auth_rate_limiter.check_register_rate(client_ip)

    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        # Enregistrer la tentative même si échec
        auth_rate_limiter.record_register_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash du mot de passe
    password_hash = get_password_hash(user_data.password)

    # Création de l'utilisateur
    db_user = User(
        email=user_data.email,
        password_hash=password_hash,
        tenant_id=tenant_id,
        role=UserRole.DIRIGEANT,
        is_active=1
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Enregistrer la tentative réussie
    auth_rate_limiter.record_register_attempt(client_ip)

    return db_user


@router.post("/login")
def login(
    request: Request,
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Connexion par email/password.
    RATE LIMITED: Max 5 tentatives par minute par IP.
    BLOCAGE: Apres 5 echecs consecutifs, compte bloque 15 min.
    Retourne LoginResponse ou LoginResponseWith2FA si 2FA requis.
    """
    # SÉCURITÉ: Rate limiting strict
    client_ip = get_client_ip(request)
    auth_rate_limiter.check_login_rate(client_ip, user_data.email)

    # Recherche de l'utilisateur
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        # Enregistrer l'échec (timing constant pour éviter user enumeration)
        auth_rate_limiter.record_login_attempt(client_ip, user_data.email, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Vérification du mot de passe
    if not verify_password(user_data.password, user.password_hash):
        auth_rate_limiter.record_login_attempt(client_ip, user_data.email, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Vérification compte actif
    if not user.is_active:
        auth_rate_limiter.record_login_attempt(client_ip, user_data.email, success=False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Vérifier si 2FA est activé
    if user.totp_enabled == 1:
        # Créer un token temporaire pour la vérification 2FA
        pending_token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": user.tenant_id,
                "role": user.role.value,
                "pending_2fa": True  # Marqueur indiquant que 2FA est requis
            },
            expires_delta=timedelta(minutes=5)  # Token court pour 2FA
        )
        auth_rate_limiter.record_login_attempt(client_ip, user_data.email, success=True)
        return {
            "requires_2fa": True,
            "pending_token": pending_token,
            "message": "2FA verification required. Use /auth/2fa/verify-login endpoint."
        }

    # Creation du JWT final (pas de 2FA)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": user.tenant_id,
            "role": user.role.value
        }
    )

    # Creer un refresh token (meme payload, duree plus longue)
    refresh_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": user.tenant_id,
            "role": user.role.value,
            "type": "refresh"
        },
        expires_delta=timedelta(days=7)
    )

    # Enregistrer le succes (reset du compteur d'echecs)
    auth_rate_limiter.record_login_attempt(client_ip, user_data.email, success=True)

    # Vérifier si changement de mot de passe obligatoire
    must_change = getattr(user, 'must_change_password', 0) == 1

    # Retourner le format attendu par le frontend
    # Note V0: access_token au niveau racine pour compatibilité frontend simple
    return {
        "status": "ok",
        "access_token": access_token,  # V0: accès direct pour frontend simple
        "user": {
            "id": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "role": user.role.value,
            "full_name": getattr(user, 'full_name', None)
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        },
        "tenant_id": user.tenant_id,
        "must_change_password": must_change
    }


# ===== BOOTSTRAP (Premier utilisateur) =====

class BootstrapRequest(BaseModel):
    """Schéma pour créer le premier tenant et admin."""
    bootstrap_secret: str
    tenant_id: str = "masith"
    tenant_name: str = "SAS MASITH"
    admin_email: EmailStr
    admin_password: str


class BootstrapResponse(BaseModel):
    """Réponse du bootstrap."""
    success: bool
    tenant_id: str
    admin_email: str
    message: str


@router.post("/bootstrap", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
def bootstrap(
    request: Request,
    data: BootstrapRequest,
    db: Session = Depends(get_db)
):
    """
    Bootstrap initial : crée le premier tenant et l'utilisateur admin.
    RATE LIMITED: Max 3 tentatives par heure par IP.

    ATTENTION : Cet endpoint nécessite un secret configuré via
    la variable d'environnement BOOTSTRAP_SECRET et ne peut être
    utilisé qu'une seule fois (si aucun utilisateur n'existe).
    """
    # SÉCURITÉ: Rate limiting très strict (1 par 20 minutes)
    get_client_ip(request)  # Conservé pour logging futur

    # Vérifier le secret depuis la configuration sécurisée
    expected_secret = get_bootstrap_secret()
    if data.bootstrap_secret != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid bootstrap secret"
        )

    # Vérifier qu'aucun utilisateur n'existe (bootstrap unique)
    existing_users = db.query(User).count()
    if existing_users > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bootstrap already done. Users exist in database."
        )

    # Validation mot de passe fort
    if len(data.admin_password) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin password must be at least 12 characters"
        )

    # Import du modele Tenant
    from app.modules.tenants.models import Tenant, TenantStatus

    # Creer le tenant dans la table tenants
    tenant = Tenant(
        tenant_id=data.tenant_id,
        name=data.tenant_name,
        email=data.admin_email,
        status=TenantStatus.ACTIVE
    )
    db.add(tenant)

    # Créer l'utilisateur admin
    password_hash = get_password_hash(data.admin_password)

    admin_user = User(
        email=data.admin_email,
        password_hash=password_hash,
        tenant_id=data.tenant_id,
        role=UserRole.DIRIGEANT,
        is_active=1
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return {
        "success": True,
        "tenant_id": data.tenant_id,
        "admin_email": data.admin_email,
        "message": f"Bootstrap réussi! Tenant '{data.tenant_id}' créé avec admin '{data.admin_email}'. Vous pouvez maintenant vous connecter via /auth/login"
    }


# ============================================================================
# ENDPOINTS 2FA (Two-Factor Authentication)
# ============================================================================

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Configure le 2FA pour l'utilisateur connecté.
    Retourne le secret TOTP, l'URI de provisionnement (QR code) et les codes de secours.

    ATTENTION: Le 2FA n'est PAS encore activé après cet appel.
    Utilisez /auth/2fa/enable avec un code TOTP pour finaliser l'activation.
    """
    if current_user.totp_enabled == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled for this account"
        )

    two_factor_service = TwoFactorService(db)
    result = two_factor_service.setup_2fa(current_user)

    return TwoFactorSetupResponse(
        secret=result.secret,
        provisioning_uri=result.provisioning_uri,
        qr_code_data=result.qr_code_data,
        backup_codes=result.backup_codes,
        message="Scan the QR code with your authenticator app, then call /auth/2fa/enable with the code to activate."
    )


@router.post("/2fa/enable")
def enable_2fa(
    verify_request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Active le 2FA après vérification du code TOTP.
    À appeler après /auth/2fa/setup avec un code généré par l'application authenticator.
    """
    two_factor_service = TwoFactorService(db)
    result = two_factor_service.verify_and_enable_2fa(current_user, verify_request.code)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return {"success": True, "message": result.message}


@router.post("/2fa/verify-login", response_model=TokenResponse)
def verify_2fa_login(
    request: Request,
    data: TwoFactorLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Vérifie le code 2FA et retourne le token d'accès final.
    Utilisé après un login qui retourne requires_2fa=True.
    """
    from app.core.security import decode_access_token

    # Décoder le pending token
    payload = decode_access_token(data.pending_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired pending token"
        )

    # Vérifier que c'est bien un token 2FA pending
    if not payload.get("pending_2fa"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type. This is not a pending 2FA token."
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Vérifier le code 2FA
    two_factor_service = TwoFactorService(db)
    result = two_factor_service.verify_2fa(user, data.code)

    if not result.success:
        # Rate limiting sur les échecs 2FA
        client_ip = get_client_ip(request)
        auth_rate_limiter.record_login_attempt(client_ip, user.email, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message
        )

    # Créer le token final
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": user.tenant_id,
            "role": user.role.value
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        tenant_id=user.tenant_id,
        role=user.role.value
    )


@router.post("/2fa/disable")
def disable_2fa(
    verify_request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Désactive le 2FA pour l'utilisateur connecté.
    Nécessite la vérification d'un code TOTP valide.
    """
    if current_user.totp_enabled != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this account"
        )

    two_factor_service = TwoFactorService(db)
    result = two_factor_service.disable_2fa(current_user, verify_request.code)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return {"success": True, "message": result.message}


@router.get("/2fa/status", response_model=TwoFactorStatusResponse)
def get_2fa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retourne le statut 2FA de l'utilisateur connecté.
    """
    two_factor_service = TwoFactorService(db)
    status_data = two_factor_service.get_2fa_status(current_user)

    return TwoFactorStatusResponse(
        enabled=status_data["enabled"],
        verified_at=status_data["verified_at"],
        has_backup_codes=status_data["has_backup_codes"],
        required=status_data["required"]
    )


@router.post("/2fa/regenerate-backup-codes")
def regenerate_backup_codes(
    verify_request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Régénère les codes de secours.
    Nécessite la vérification d'un code TOTP valide (pas un code de secours).
    Les anciens codes de secours seront invalidés.
    """
    if current_user.totp_enabled != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this account"
        )

    two_factor_service = TwoFactorService(db)
    success, new_codes = two_factor_service.regenerate_backup_codes(current_user, verify_request.code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Cannot regenerate backup codes."
        )

    return {
        "success": True,
        "backup_codes": new_codes,
        "message": "New backup codes generated. Store them securely. Old codes are now invalid."
    }


# ===== LOGOUT =====

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Déconnexion de l'utilisateur.
    Avec JWT, le logout est géré côté client (suppression du token).
    Cet endpoint permet au frontend d'avoir un point de terminaison cohérent.
    """
    return {"success": True, "message": "Logged out successfully"}


# ===== REFRESH TOKEN =====

class RefreshTokenRequest(BaseModel):
    """Schema pour refresh token."""
    refresh_token: str


@router.post("/refresh")
def refresh_access_token(
    request: Request,
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Rafraichit le token d'acces avec un refresh token valide.

    GUARDIAN: Cet endpoint ne doit JAMAIS retourner 500.
    Toute erreur doit être traitée comme 401 (auth invalide).
    """
    from app.core.security import decode_access_token
    from app.core.logging_config import get_logger

    logger = get_logger(__name__)
    client_ip = get_client_ip(request)

    try:
        # Decoder le refresh token
        try:
            payload = decode_access_token(data.refresh_token)
        except Exception as decode_error:
            logger.warning(
                f"[GUARDIAN] Refresh token decode failed: {decode_error}",
                extra={
                    "client_ip": client_ip,
                    "error_type": "token_decode_error",
                    "path": "/auth/refresh"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or malformed refresh token"
            )

        if payload is None:
            logger.warning(
                "[GUARDIAN] Refresh token invalid or expired",
                extra={"client_ip": client_ip, "path": "/auth/refresh"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Verifier que c'est bien un refresh token
        if payload.get("type") != "refresh":
            logger.warning(
                "[GUARDIAN] Token type mismatch - expected refresh",
                extra={
                    "client_ip": client_ip,
                    "token_type": payload.get("type"),
                    "path": "/auth/refresh"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type - refresh token required"
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.warning(
                "[GUARDIAN] Refresh token missing user ID",
                extra={"client_ip": client_ip, "path": "/auth/refresh"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - missing user identifier"
            )

        # Recherche utilisateur avec gestion d'erreur DB
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
        except Exception as db_error:
            logger.error(
                f"[GUARDIAN] Database error during refresh: {db_error}",
                extra={
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "error_type": "database_error",
                    "path": "/auth/refresh"
                }
            )
            # GUARDIAN: Erreur DB = traiter comme auth invalide, pas 500
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication service temporarily unavailable - please login again"
            )

        if not user:
            logger.warning(
                f"[GUARDIAN] Refresh token for non-existent user: {user_id}",
                extra={"client_ip": client_ip, "user_id": user_id, "path": "/auth/refresh"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.is_active:
            logger.warning(
                f"[GUARDIAN] Refresh token for inactive user: {user_id}",
                extra={"client_ip": client_ip, "user_id": user_id, "path": "/auth/refresh"}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive - contact administrator"
            )

        # Creer les nouveaux tokens avec gestion d'erreur
        try:
            access_token = create_access_token(
                data={
                    "sub": str(user.id),
                    "tenant_id": user.tenant_id,
                    "role": user.role.value
                }
            )

            refresh_token = create_access_token(
                data={
                    "sub": str(user.id),
                    "tenant_id": user.tenant_id,
                    "role": user.role.value,
                    "type": "refresh"
                },
                expires_delta=timedelta(days=7)
            )
        except Exception as token_error:
            logger.error(
                f"[GUARDIAN] Token creation failed: {token_error}",
                extra={
                    "client_ip": client_ip,
                    "user_id": str(user.id),
                    "error_type": "token_creation_error",
                    "path": "/auth/refresh"
                }
            )
            # GUARDIAN: Erreur création token = traiter comme auth invalide
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed - please login again"
            )

        logger.info(
            f"[GUARDIAN] Token refreshed successfully for user: {user.id}",
            extra={"client_ip": client_ip, "user_id": str(user.id)}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except HTTPException:
        # Re-raise HTTPException as-is (already proper status code)
        raise
    except Exception as unexpected_error:
        # GUARDIAN: Catch-all - JAMAIS de 500 sur /auth/refresh
        logger.error(
            f"[GUARDIAN] UNEXPECTED error in refresh endpoint: {unexpected_error}",
            extra={
                "client_ip": client_ip,
                "error_type": "unexpected_error",
                "exception_type": type(unexpected_error).__name__,
                "path": "/auth/refresh"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed - please login again"
        )


# ===== ENDPOINTS UTILISATEUR COURANT =====

@router.get("/me")
def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les informations de l'utilisateur connecte.
    Utilise pour recuperer le profil apres login.

    GUARDIAN: Endpoint sécurisé - retourne 401/403 proprement, jamais 500.
    """
    from app.core.logging_config import get_logger

    logger = get_logger(__name__)
    client_ip = get_client_ip(request)

    try:
        # Si current_user est None (ne devrait pas arriver grâce au Depends)
        if current_user is None:
            logger.warning(
                "[GUARDIAN] /auth/me called with null user",
                extra={"client_ip": client_ip, "path": "/auth/me"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        return {
            "id": current_user.id,
            "email": current_user.email,
            "tenant_id": current_user.tenant_id,
            "role": current_user.role.value,
            "full_name": getattr(current_user, 'full_name', None),
            "is_active": current_user.is_active == 1,
            "totp_enabled": current_user.totp_enabled == 1
        }

    except HTTPException:
        raise
    except Exception as e:
        # GUARDIAN: Log l'erreur mais retourne 401, pas 500
        logger.error(
            f"[GUARDIAN] Unexpected error in /auth/me: {e}",
            extra={
                "client_ip": client_ip,
                "error_type": "unexpected_error",
                "path": "/auth/me"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error - please login again"
        )


@router.get("/capabilities")
def get_user_capabilities(
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les capacites/permissions de l'utilisateur connecte.
    Utilise pour le controle d'acces cote frontend.
    """
    # Toutes les capacites disponibles
    ALL_CAPABILITIES = [
        "cockpit.view", "cockpit.decisions.view",
        # Partners - permissions generiques ET specifiques (frontend utilise les deux)
        "partners.view", "partners.create", "partners.edit", "partners.delete",
        "partners.clients.view", "partners.clients.create", "partners.clients.edit", "partners.clients.delete",
        "partners.suppliers.view", "partners.suppliers.create", "partners.suppliers.edit", "partners.suppliers.delete",
        "partners.contacts.view", "partners.contacts.create", "partners.contacts.edit", "partners.contacts.delete",
        # Invoicing - generiques ET specifiques par type (quotes, invoices, credits)
        "invoicing.view", "invoicing.create", "invoicing.edit", "invoicing.delete", "invoicing.send",
        "invoicing.quotes.view", "invoicing.quotes.create", "invoicing.quotes.edit", "invoicing.quotes.delete", "invoicing.quotes.send",
        "invoicing.invoices.view", "invoicing.invoices.create", "invoicing.invoices.edit", "invoicing.invoices.delete", "invoicing.invoices.send",
        "invoicing.credits.view", "invoicing.credits.create", "invoicing.credits.edit", "invoicing.credits.delete", "invoicing.credits.send",
        # Treasury - generiques ET specifiques (accounts)
        "treasury.view", "treasury.create", "treasury.transfer.execute",
        "treasury.accounts.view", "treasury.accounts.create", "treasury.accounts.edit", "treasury.accounts.delete",
        # Accounting
        "accounting.view", "accounting.journal.view", "accounting.journal.delete",
        # Purchases - generiques ET specifiques (orders)
        "purchases.view", "purchases.create", "purchases.edit",
        "purchases.orders.view", "purchases.orders.create", "purchases.orders.edit", "purchases.orders.delete",
        # Projects
        "projects.view", "projects.create", "projects.edit", "projects.delete",
        # Interventions - generiques ET specifiques (tickets)
        "interventions.view", "interventions.create", "interventions.edit",
        "interventions.tickets.view", "interventions.tickets.create", "interventions.tickets.edit", "interventions.tickets.delete",
        # Web
        "web.view", "web.edit",
        # Ecommerce - generiques ET specifiques (products, orders)
        "ecommerce.view", "ecommerce.edit", "ecommerce.create", "ecommerce.delete",
        "ecommerce.products.view", "ecommerce.products.create", "ecommerce.products.edit", "ecommerce.products.delete",
        "ecommerce.orders.view", "ecommerce.orders.create", "ecommerce.orders.edit", "ecommerce.orders.delete",
        # Marketplace
        "marketplace.view", "marketplace.edit",
        # Payments
        "payments.view", "payments.create",
        # Mobile
        "mobile.view",
        # Admin - avec create pour roles
        "admin.view", "admin.users.view", "admin.users.create", "admin.users.edit", "admin.users.delete",
        "admin.roles.view", "admin.roles.create", "admin.roles.edit", "admin.roles.delete",
        "admin.tenants.view", "admin.tenants.create", "admin.tenants.delete",
        "admin.modules.view", "admin.modules.edit",
        "admin.logs.view",
        "admin.root.break_glass",
        # IAM permissions (required by IAM module)
        "iam.user.create", "iam.user.read", "iam.user.update", "iam.user.delete", "iam.user.admin",
        "iam.role.create", "iam.role.read", "iam.role.update", "iam.role.delete", "iam.role.assign",
        "iam.group.create", "iam.group.read", "iam.group.update", "iam.group.delete",
        "iam.permission.read",
        "iam.invitation.create",
        "iam.policy.read", "iam.policy.update",
    ]

    # Capacites basees sur le role
    role_capabilities = {
        "DIRIGEANT": ALL_CAPABILITIES,  # Acces complet
        "DAF": [
            "cockpit.view", "treasury.view", "treasury.create", "treasury.transfer.execute",
            "accounting.view", "accounting.journal.view", "invoicing.view", "invoicing.create",
            "payments.view", "payments.create",
        ],
        "COMPTABLE": [
            "cockpit.view", "accounting.view", "accounting.journal.view",
            "invoicing.view", "invoicing.create", "treasury.view",
        ],
        "COMMERCIAL": [
            "cockpit.view", "partners.view", "partners.create", "partners.edit",
            "invoicing.view", "invoicing.create",
        ],
        "EMPLOYE": ["cockpit.view"],
        "ADMIN": ALL_CAPABILITIES,
    }

    role_name = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    capabilities = role_capabilities.get(role_name, ["cockpit.view"])

    return {"data": {
        "capabilities": capabilities,
        "role": role_name,
    }}


# ===== CHANGEMENT DE MOT DE PASSE =====

class ChangePasswordRequest(BaseModel):
    """Schema pour changement de mot de passe."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordResponse(BaseModel):
    """Schema de réponse changement de mot de passe."""
    success: bool
    message: str


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change le mot de passe de l'utilisateur connecté.

    SÉCURITÉ:
    - Requiert le mot de passe actuel pour validation
    - Le nouveau mot de passe est hashé avec bcrypt
    - Met à jour password_changed_at
    - Désactive must_change_password

    AUDIT:
    - Log l'événement sans exposer les mots de passe
    """
    from datetime import datetime

    # Vérifier le mot de passe actuel
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Vérifier que le nouveau mot de passe est différent
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Hash du nouveau mot de passe
    new_password_hash = get_password_hash(data.new_password)

    # Mise à jour en base
    current_user.password_hash = new_password_hash
    current_user.must_change_password = 0
    current_user.password_changed_at = datetime.utcnow()
    current_user.updated_at = datetime.utcnow()

    db.commit()

    # Log d'audit (sans mot de passe)
    get_client_ip(request)

    return ChangePasswordResponse(
        success=True,
        message="Password changed successfully"
    )


@router.post("/force-change-password", response_model=ChangePasswordResponse)
def force_change_password(
    request: Request,
    data: ChangePasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint spécial pour le changement de mot de passe obligatoire.
    Utilisé quand must_change_password=true après le login initial.

    SÉCURITÉ:
    - L'utilisateur doit fournir son mot de passe actuel
    - Ne nécessite pas d'être "vraiment" connecté (juste authentifié)
    - Met à jour must_change_password à false après succès
    """
    from datetime import datetime

    from app.core.security import decode_access_token

    # Récupérer le token depuis le header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Vérifier le mot de passe actuel
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Vérifier que le nouveau mot de passe est différent
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Hash du nouveau mot de passe
    new_password_hash = get_password_hash(data.new_password)

    # Mise à jour en base
    user.password_hash = new_password_hash
    user.must_change_password = 0
    user.password_changed_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()

    db.commit()

    return ChangePasswordResponse(
        success=True,
        message="Password changed successfully. You can now login with your new password."
    )
