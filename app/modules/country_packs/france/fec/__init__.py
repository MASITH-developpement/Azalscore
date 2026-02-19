"""
AZALS MODULE - FEC (Fichier des Écritures Comptables)
=====================================================

Module de génération et validation du FEC conforme à l'Article A.47 A-1 du LPF.

Conformité:
- Format 18 colonnes obligatoires
- Encodage UTF-8 ou ISO-8859-15
- Séparateur TAB ou pipe
- Nommage: {SIREN}FEC{YYYYMMDD}.txt
"""

from .service import FECService
from .service_sync import FECServiceSync
from .router import router as fec_router
from .models import FECExport, FECValidationResult
from .schemas import (
    FECExportRequest,
    FECExportResponse,
    FECValidationResponse,
    FECColumn,
    FEC_COLUMNS,
)

__all__ = [
    "FECService",
    "FECServiceSync",
    "fec_router",
    "FECExport",
    "FECValidationResult",
    "FECExportRequest",
    "FECExportResponse",
    "FECValidationResponse",
    "FECColumn",
    "FEC_COLUMNS",
]
