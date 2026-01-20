"""
AZALS - Middleware d'Authentification
=====================================

Middleware pour parser le JWT et injecter l'utilisateur dans request.state.
S'exécute après TenantMiddleware et avant RBACMiddleware.

Ceci permet au RBACMiddleware de vérifier les permissions basées sur
request.state.user.
"""

from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import SessionLocal
from app.core.logging_config import get_logger
from app.core.models import User
from app.core.security import decode_access_token

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware d'authentification JWT.

    Parse le token JWT de l'header Authorization et charge l'utilisateur
    dans request.state.user pour les middlewares et endpoints suivants.

    Ne bloque PAS les requêtes sans token - laisse les autres middlewares
    et les dépendances FastAPI gérer l'autorisation.
    """

    async def dispatch(self, request: Request, call_next):
        """Traite chaque requête."""
        path = request.url.path

        # Ignorer les OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extraire le token de l'header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Pas de token - continuer sans authentification
            logger.debug(f"[AuthMiddleware] No token for {path}")
            return await call_next(request)

        token = auth_header.split(" ", 1)[1]

        # Décoder le JWT
        payload = decode_access_token(token)
        if payload is None:
            # Token invalide - continuer sans authentification
            return await call_next(request)

        # Extraire user_id et tenant_id du JWT
        user_id = payload.get("sub")
        jwt_tenant_id = payload.get("tenant_id")

        if not user_id or not jwt_tenant_id:
            # Payload incomplet
            return await call_next(request)

        # Vérifier cohérence tenant si disponible
        request_tenant_id = getattr(request.state, "tenant_id", None)
        if request_tenant_id and jwt_tenant_id != request_tenant_id:
            # Incohérence tenant - ne pas authentifier
            logger.warning(
                "Tenant mismatch",
                extra={
                    "jwt_tenant": jwt_tenant_id,
                    "request_tenant": request_tenant_id,
                    "path": str(request.url.path)
                }
            )
            return await call_next(request)

        # Charger l'utilisateur depuis la DB
        db: Session = SessionLocal()
        try:
            user = self._load_user(db, user_id, jwt_tenant_id)
            if user and user.is_active:
                # Injecter l'utilisateur dans request.state
                request.state.user = user
                request.state.user_id = user.id
                # S'assurer que tenant_id est défini
                if not hasattr(request.state, "tenant_id"):
                    request.state.tenant_id = jwt_tenant_id
        except Exception as e:
            logger.error(f"Error loading user: {e}")
        finally:
            db.close()

        return await call_next(request)

    def _load_user(self, db: Session, user_id: str, tenant_id: str) -> User | None:
        """Charge l'utilisateur depuis la base de données."""
        try:
            # Support UUID (nouveau) et int (legacy)
            if isinstance(user_id, str) and '-' in user_id:
                user_uuid = UUID(user_id)
                user = db.query(User).filter(
                    User.id == user_uuid,
                    User.tenant_id == tenant_id
                ).first()
            else:
                user_id_int = int(user_id)
                user = db.query(User).filter(
                    User.id == user_id_int,
                    User.tenant_id == tenant_id
                ).first()
            return user
        except (ValueError, TypeError):
            return None
