"""
AZALS - Dépendances FastAPI Multi-Tenant + Authentification
Injection sécurisée du tenant_id et vérification JWT
"""

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import User
from app.core.security import decode_access_token

security = HTTPBearer()


def get_tenant_id(request: Request) -> str:
    """
    Dépendance FastAPI : extraction du tenant_id.
    Le tenant_id a été validé et injecté par TenantMiddleware.

    Usage dans un endpoint :
        @app.get("/items")
        def list_items(tenant_id: str = Depends(get_tenant_id)):
            # tenant_id garanti valide ici
    """
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Tenant-ID header"
        )
    return request.state.tenant_id


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> User:
    """
    Dépendance FastAPI : authentification et validation tenant.

    Vérifie :
    1. JWT valide
    2. Utilisateur existe et actif
    3. tenant_id du JWT = X-Tenant-ID du header

    Refuse l'accès si incohérence.

    Usage :
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            # current_user garanti authentifié et cohérent avec tenant
    """
    token = credentials.credentials

    # Décoder le JWT
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Extraire user_id et tenant_id du JWT
    user_id = payload.get("sub")
    jwt_tenant_id = payload.get("tenant_id")

    if not user_id or not jwt_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # SÉCURITÉ CRITIQUE : vérifier cohérence tenant
    if jwt_tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch. Access denied."
        )

    # Charger l'utilisateur depuis la DB
    try:
        # Support UUID (nouveau) et int (legacy)
        if isinstance(user_id, str) and '-' in user_id:
            user_uuid = UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        else:
            user_id_int = int(user_id)
            user = db.query(User).filter(User.id == user_id_int).first()
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Double vérification tenant (paranoia)
    if user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch in database. Access denied."
        )

    return user


def get_current_user_id(
    current_user: User = Depends(get_current_user)
) -> int:
    """
    Dépendance FastAPI : retourne l'ID de l'utilisateur authentifié.

    Usage :
        @app.get("/my-data")
        def get_my_data(user_id: int = Depends(get_current_user_id)):
            # user_id garanti authentifié
    """
    return current_user.id


def get_tenant_db(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Dépendance combinée : DB session + tenant_id.
    Simplifie l'écriture des endpoints.

    Usage :
        @app.get("/items")
        def list_items(tenant_db = Depends(get_tenant_db)):
            db, tenant_id = tenant_db
            items = db.query(Item).filter(Item.tenant_id == tenant_id).all()
    """
    return db, tenant_id


def get_current_user_and_tenant(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
) -> dict:
    """
    Dépendance combinée : utilisateur authentifié + tenant_id + user_id.
    Retourne un dict avec toutes les infos nécessaires.

    Usage :
        @app.post("/action")
        def protected_action(auth_data: dict = Depends(get_current_user_and_tenant)):
            tenant_id = auth_data["tenant_id"]
            user_id = auth_data["user_id"]
            user = auth_data["user"]
    """
    return {
        "user": current_user,
        "user_id": current_user.id,
        "tenant_id": tenant_id
    }
