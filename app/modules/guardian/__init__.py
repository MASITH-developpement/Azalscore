"""
AZALS MODULE GUARDIAN - Correction Automatique Gouvernée & Auditable
=====================================================================

Module de détection, analyse et correction automatique des erreurs.
Garantit la traçabilité complète et l'auditabilité de toutes les actions.

Principes fondamentaux:
- Aucune correction non explicable
- Aucune correction non traçable
- Aucune correction non justifiable
- Registre append-only obligatoire
- Tests post-correction obligatoires

GUARDIAN agit. GUARDIAN explique. GUARDIAN assume.
"""

from .models import (
    # Enums
    ErrorSeverity,
    ErrorSource,
    ErrorType,
    CorrectionStatus,
    CorrectionAction,
    TestResult,
    Environment,

    # Models
    ErrorDetection,
    CorrectionRegistry,
    CorrectionRule,
    CorrectionTest,
    GuardianAlert,
    GuardianConfig,
)

from .service import GuardianService, get_guardian_service
from .router import router as guardian_router
from .middleware import GuardianMiddleware, setup_guardian_middleware

# Fonctions SAFE de gestion des erreurs HTTP
from .error_response import (
    build_error_response,
    build_safe_error_response,
    get_error_type_for_status,
    get_error_severity_for_status,
    DEFAULT_ERROR_MESSAGES,
)

__all__ = [
    # Enums
    "ErrorSeverity",
    "ErrorSource",
    "ErrorType",
    "CorrectionStatus",
    "CorrectionAction",
    "TestResult",
    "Environment",

    # Models
    "ErrorDetection",
    "CorrectionRegistry",
    "CorrectionRule",
    "CorrectionTest",
    "GuardianAlert",
    "GuardianConfig",

    # Service
    "GuardianService",
    "get_guardian_service",

    # Router
    "guardian_router",

    # Middleware
    "GuardianMiddleware",
    "setup_guardian_middleware",

    # Fonctions SAFE de gestion des erreurs HTTP
    "build_error_response",
    "build_safe_error_response",
    "get_error_type_for_status",
    "get_error_severity_for_status",
    "DEFAULT_ERROR_MESSAGES",
]
