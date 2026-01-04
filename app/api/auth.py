"""
AZALS - Endpoints Authentification
Login et Register pour utilisateurs DIRIGEANT
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_tenant_id


router = APIRouter(prefix="/auth", tags=["auth"])

# Clé secrète pour le bootstrap (définie en variable d'environnement)
BOOTSTRAP_SECRET = os.getenv("BOOTSTRAP_SECRET", "azals-bootstrap-2024")


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


# ===== ENDPOINTS =====

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Création d'un nouveau compte DIRIGEANT.
    Le tenant_id est extrait du header X-Tenant-ID.
    Un utilisateur est lié à UN SEUL tenant à vie.
    """
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
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
        tenant_id=tenant_id,  # Lié au tenant via X-Tenant-ID
        role=UserRole.DIRIGEANT,
        is_active=1
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=TokenResponse)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Connexion par email/password.
    Retourne un JWT contenant : user_id, tenant_id, role.
    Le client DOIT ensuite utiliser X-Tenant-ID = tenant_id du JWT.
    """
    # Recherche de l'utilisateur
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Vérification du mot de passe
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Vérification compte actif
    if not user.is_active:
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
    data: BootstrapRequest,
    db: Session = Depends(get_db)
):
    """
    Bootstrap initial : crée le premier tenant et l'utilisateur admin.
    ATTENTION : Cet endpoint nécessite un secret et ne peut être utilisé
    qu'une seule fois (si aucun utilisateur n'existe).

    Pour l'utiliser :
    POST /auth/bootstrap
    {
        "bootstrap_secret": "azals-bootstrap-2024",
        "tenant_id": "masith",
        "tenant_name": "SAS MASITH",
        "admin_email": "admin@masith.fr",
        "admin_password": "VotreMotDePasse123!"
    }
    """
    # Vérifier le secret
    if data.bootstrap_secret != BOOTSTRAP_SECRET:
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
