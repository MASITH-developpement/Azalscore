"""
AZALS MODULE - PCG 2025 (Plan Comptable Général)
=================================================

Module de gestion du Plan Comptable Général 2025 conforme à l'ANC
(Autorité des Normes Comptables).

Fonctionnalités:
- PCG 2025 complet (classes 1-8, ~400 comptes standards)
- Gestion des comptes personnalisés
- Validation de conformité PCG
- Migration PCG 2024 -> 2025
- Hiérarchie des comptes

Référence: Règlement ANC n°2014-03 modifié
"""

from .service import PCG2025Service
from .router import router as pcg_router
from .schemas import (
    PCGAccountCreate,
    PCGAccountResponse,
    PCGInitResult,
    PCGValidationResult,
    PCGMigrationResult,
    PCG_CLASSES,
)
from .pcg2025_accounts import (
    PCG2025_ALL_ACCOUNTS,
    PCG2025Account,
    get_pcg2025_account,
    get_pcg2025_class,
    validate_pcg_account_number,
)

__all__ = [
    # Service
    "PCG2025Service",
    # Router
    "pcg_router",
    # Schemas
    "PCGAccountCreate",
    "PCGAccountResponse",
    "PCGInitResult",
    "PCGValidationResult",
    "PCGMigrationResult",
    "PCG_CLASSES",
    # Comptes
    "PCG2025_ALL_ACCOUNTS",
    "PCG2025Account",
    "get_pcg2025_account",
    "get_pcg2025_class",
    "validate_pcg_account_number",
]
