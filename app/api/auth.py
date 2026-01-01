"""
AZALS - Endpoints Authentification
Login et Register pour utilisateurs DIRIGEANT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_tenant_id


router = APIRouter(prefix="/auth", tags=["auth"])


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
