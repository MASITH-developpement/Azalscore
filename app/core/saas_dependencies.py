"""
CORE SaaS - FastAPI Dependencies
==================================

Dependencies pour injection dans les routes FastAPI.
"""

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.saas_core import SaaSCore, get_saas_core


# Security scheme pour Swagger UI
security = HTTPBearer()


async def get_saas_context(
    authorization: HTTPAuthorizationCredentials = Depends(security),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_correlation_id: str = Header(None, alias="X-Correlation-ID"),
    db: Session = Depends(get_db)
) -> SaaSContext:
    """
    Dépendance FastAPI pour obtenir le SaaSContext.

    Cette fonction:
    1. Extrait le token JWT du header Authorization
    2. Extrait le tenant_id du header X-Tenant-ID
    3. Authentifie via SaaSCore
    4. Retourne le SaaSContext ou lève HTTPException

    Args:
        authorization: Credentials Bearer token
        x_tenant_id: Tenant ID depuis header
        x_correlation_id: ID de corrélation (optionnel)
        db: Session database

    Returns:
        SaaSContext authentifié

    Raises:
        HTTPException 401: Si authentification échoue
        HTTPException 403: Si tenant non actif
    """
    # Extraire token
    token = authorization.credentials

    # Créer instance SaaSCore
    core = SaaSCore(db)

    # Authentifier
    result = core.authenticate(
        token=token,
        tenant_id=x_tenant_id,
        correlation_id=x_correlation_id or ""
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result.data
