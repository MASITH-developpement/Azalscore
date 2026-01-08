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
]
