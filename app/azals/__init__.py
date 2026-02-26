"""
AZALSCORE - API Unifiée
========================

Expose tous les patterns et utilitaires essentiels en un seul import.
Simplifie drastiquement les imports dans les modules.

USAGE:
    # Au lieu de 5-7 imports:
    from app.core.compat import get_context
    from app.core.database import get_db
    from app.core.base_service import BaseService
    from app.core.saas_context import SaaSContext, Result
    from app.core.pagination import PaginatedResponse
    from app.core.base_router import CRUDRouter

    # Un seul import:
    from app.azals import (
        BaseService, SaaSContext, Result,
        get_context, get_db,
        CRUDRouter, PaginatedResponse
    )

Conformité: AZA-NF-008
"""

# =============================================================================
# CORE SAAS PATTERNS
# =============================================================================

from app.core.saas_context import (
    SaaSContext,
    Result,
    UserRole,
    TenantScope,
)

from app.core.base_service import (
    BaseService,
    CRUDService,
)

from app.core.base_router import (
    CRUDRouter,
    create_simple_crud,
    create_readonly_crud,
)

from app.core.repository import BaseRepository

# =============================================================================
# DEPENDENCIES
# =============================================================================

from app.core.compat import (
    get_context,
    create_context_from_user,
    unified_endpoint,
)

from app.core.database import get_db

# =============================================================================
# PAGINATION
# =============================================================================

from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    PaginationLimits,
    paginate_query,
    paginate_list,
)

# =============================================================================
# MODELS BASE
# =============================================================================

from app.models.base import TenantMixin

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # SaaS Context
    "SaaSContext",
    "Result",
    "UserRole",
    "TenantScope",

    # Services
    "BaseService",
    "CRUDService",
    "BaseRepository",

    # Routers
    "CRUDRouter",
    "create_simple_crud",
    "create_readonly_crud",

    # Dependencies
    "get_context",
    "get_db",
    "create_context_from_user",
    "unified_endpoint",

    # Pagination
    "PaginatedResponse",
    "PaginationParams",
    "PaginationLimits",
    "paginate_query",
    "paginate_list",

    # Models
    "TenantMixin",
]

__version__ = "2.0.0"
