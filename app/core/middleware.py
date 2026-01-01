"""
AZALS - Middleware Multi-Tenant
Validation stricte du header X-Tenant-ID pour TOUTES les requêtes
Exception : /health (monitoring public)
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware de validation du tenant.
    Refuse toute requête sans X-Tenant-ID valide (hors endpoints publics).
    Injecte le tenant_id dans request.state pour usage par les endpoints.
    """
    
    # Endpoints publics exclus de la validation tenant
    PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/", "/dashboard", "/static"}
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercepte chaque requête HTTP.
        Valide la présence et le format du tenant_id.
        """
        # Endpoints publics : bypass validation
        # Vérifier si le chemin commence par un des chemins publics
        if any(request.url.path == path or request.url.path.startswith(path + "/") 
               for path in self.PUBLIC_PATHS):
            return await call_next(request)
        
        # Extraction du header X-Tenant-ID
        tenant_id: Optional[str] = request.headers.get("X-Tenant-ID")
        
        # Validation : header obligatoire
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Tenant-ID header. Multi-tenant isolation required."
            )
        
        # Validation : format du tenant_id (alphanumerique + tirets)
        if not self._is_valid_tenant_id(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Tenant-ID format. Alphanumeric and hyphens only."
            )
        
        # Injection du tenant_id dans request.state
        request.state.tenant_id = tenant_id
        
        # Poursuite de la requête
        response = await call_next(request)
        return response
    
    @staticmethod
    def _is_valid_tenant_id(tenant_id: str) -> bool:
        """
        Valide le format du tenant_id.
        Accepte : lettres, chiffres, tirets, underscores
        Longueur : 1-255 caractères
        """
        if not tenant_id or len(tenant_id) > 255:
            return False
        
        # Validation alphanumérique + tirets + underscores uniquement
        return all(c.isalnum() or c in ['-', '_'] for c in tenant_id)
