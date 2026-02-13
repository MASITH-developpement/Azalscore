"""
AZALS - Dépendances FastAPI Multi-Tenant + Authentification
Injection sécurisée du tenant_id et vérification JWT

SÉCURITÉ MULTI-TENANT:
- Toute requête DOIT être filtrée par tenant_id
- Le décorateur @enforce_tenant_isolation vérifie ce principe
- Les fonctions get_tenant_db et get_current_user_and_tenant garantissent l'isolation
"""

import functools
import logging
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import User
from app.core.security import decode_access_token

security = HTTPBearer()
logger = logging.getLogger(__name__)


class TenantIsolationError(Exception):
    """Erreur levée quand l'isolation tenant est violée."""
    pass


def enforce_tenant_isolation(func):
    """
    Décorateur de sécurité pour les méthodes de service.

    Vérifie que:
    1. Le service a un tenant_id défini
    2. Le tenant_id n'est pas vide ou None

    Usage:
        class MyService:
            def __init__(self, db: Session, tenant_id: str):
                self.db = db
                self.tenant_id = tenant_id

            @enforce_tenant_isolation
            def get_items(self):
                # tenant_id garanti non-null ici
                return self.db.query(Item).filter(
                    Item.tenant_id == self.tenant_id
                ).all()

    ATTENTION: Ce décorateur ne vérifie pas que la requête SQL
    contient effectivement le filtre tenant_id. Il vérifie seulement
    que le service a un tenant_id valide. La responsabilité de
    filtrer correctement reste au développeur.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Vérifier que self a un tenant_id
        if not hasattr(self, 'tenant_id'):
            logger.critical(
                f"[TENANT_ISOLATION] VIOLATION: {func.__name__} appelé sur un service "
                f"sans attribut tenant_id. Classe: {self.__class__.__name__}"
            )
            raise TenantIsolationError(
                f"Le service {self.__class__.__name__} n'a pas d'attribut tenant_id. "
                "Tous les services doivent être initialisés avec un tenant_id."
            )

        # Vérifier que tenant_id n'est pas vide
        if not self.tenant_id:
            logger.critical(
                f"[TENANT_ISOLATION] VIOLATION: {func.__name__} appelé avec "
                f"tenant_id vide ou None. Classe: {self.__class__.__name__}"
            )
            raise TenantIsolationError(
                f"tenant_id est vide ou None dans {self.__class__.__name__}. "
                "Toutes les opérations doivent avoir un tenant_id valide."
            )

        # Log pour audit (niveau DEBUG en production)
        logger.debug(
            f"[TENANT_ISOLATION] {self.__class__.__name__}.{func.__name__} "
            f"exécuté pour tenant={self.tenant_id}"
        )

        return func(self, *args, **kwargs)

    return wrapper


def enforce_tenant_isolation_async(func):
    """
    Version async du décorateur enforce_tenant_isolation.

    Usage:
        @enforce_tenant_isolation_async
        async def get_items_async(self):
            ...
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'tenant_id'):
            logger.critical(
                f"[TENANT_ISOLATION] VIOLATION: {func.__name__} appelé sur un service "
                f"sans attribut tenant_id. Classe: {self.__class__.__name__}"
            )
            raise TenantIsolationError(
                f"Le service {self.__class__.__name__} n'a pas d'attribut tenant_id."
            )

        if not self.tenant_id:
            logger.critical(
                f"[TENANT_ISOLATION] VIOLATION: {func.__name__} appelé avec "
                f"tenant_id vide ou None. Classe: {self.__class__.__name__}"
            )
            raise TenantIsolationError(
                f"tenant_id est vide ou None dans {self.__class__.__name__}."
            )

        logger.debug(
            f"[TENANT_ISOLATION] {self.__class__.__name__}.{func.__name__} "
            f"exécuté pour tenant={self.tenant_id}"
        )

        return await func(self, *args, **kwargs)

    return wrapper


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
    Dépendance combinée : DB session + tenant_id avec contexte RLS.

    SÉCURITÉ P1: Active le contexte RLS pour le filtrage automatique.

    Usage :
        @app.get("/items")
        def list_items(tenant_db = Depends(get_tenant_db)):
            db, tenant_id = tenant_db
            # RLS filtre automatiquement, mais garder le filtre explicite
            items = db.query(Item).filter(Item.tenant_id == tenant_id).all()
    """
    # SÉCURITÉ P1: Activer RLS pour defense-in-depth
    from app.core.database import set_rls_context
    set_rls_context(db, tenant_id)

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
        "tenant_id": tenant_id,
        "email": current_user.email
    }
