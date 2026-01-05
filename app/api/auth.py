"""
AZALS - Endpoints Authentification SÉCURISÉS
=============================================
Login et Register pour utilisateurs DIRIGEANT.
Rate limiting strict sur tous les endpoints auth.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from datetime import datetime
import time
from collections import defaultdict
from typing import Dict, List

from app.core.database import get_db
from app.core.models import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_tenant_id
from app.core.config import get_settings


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
        self._login_attempts: Dict[str, List[float]] = defaultdict(list)
        self._register_attempts: Dict[str, List[float]] = defaultdict(list)
        self._failed_logins: Dict[str, int] = defaultdict(int)

    def _cleanup_old_attempts(self, attempts: List[float], window_seconds: int = 60) -> List[float]:
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
                detail=f"Too many login attempts from this IP. Wait 60 seconds.",
                headers={"Retry-After": "60"}
            )

        # Vérification par email (3x plus permissif)
        if len(self._login_attempts[email]) >= limit * 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts for this account. Wait 60 seconds.",
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
            UserWarning
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
    """Schéma de réponse après login."""
    access_token: str
    token_type: str
    tenant_id: str
    role: str


class UserResponse(BaseModel):
    """Schéma de réponse utilisateur."""
    id: int
    email: str
    tenant_id: str
    role: str
    
    model_config = {"from_attributes": True}


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


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Connexion par email/password.
    RATE LIMITED: Max 5 tentatives par minute par IP.
    BLOCAGE: Après 5 échecs consécutifs, compte bloqué 15 min.
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

    # Création du JWT
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": user.tenant_id,
            "role": user.role.value
        }
    )

    # Enregistrer le succès (reset du compteur d'échecs)
    auth_rate_limiter.record_login_attempt(client_ip, user_data.email, success=True)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": user.tenant_id,
        "role": user.role.value
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
    client_ip = get_client_ip(request)

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
