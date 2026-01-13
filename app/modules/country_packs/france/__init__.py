"""
AZALS - PACK PAYS FRANCE
========================
Localisation française complète.

Inclut:
- PCG 2024 (Plan Comptable Général)
- TVA française (taux, déclarations CA3/CA12)
- FEC (Fichier des Écritures Comptables)
- DSN (Déclaration Sociale Nominative)
- Contrats de travail français
- RGPD (conformité, consentements, violations)
"""

from .models import (
    ContractType,
    DSNDeclaration,
    DSNEmployee,
    DSNStatus,
    DSNType,
    FECEntry,
    FECExport,
    FECStatus,
    FREmploymentContract,
    FRVATDeclaration,
    FRVATRate,
    # Models
    PCGAccount,
    # Enums
    PCGClass,
    RGPDConsent,
    RGPDConsentStatus,
    RGPDDataBreach,
    RGPDDataProcessing,
    RGPDRequest,
    RGPDRequestType,
    TVARate,
    TVARegime,
)
from .router import router
from .schemas import (
    DSNDeclarationResponse,
    DSNEmployeeData,
    # DSN
    DSNGenerateRequest,
    FECEntrySchema,
    FECExportResponse,
    # FEC
    FECGenerateRequest,
    FECValidationResult,
    # Stats
    FrancePackStats,
    # Contrats
    FRContractCreate,
    FRContractResponse,
    # TVA
    FRVATRateCreate,
    FRVATRateResponse,
    # PCG
    PCGAccountCreate,
    PCGAccountResponse,
    PCGAccountUpdate,
    RGPDBreachCreate,
    RGPDBreachResponse,
    # RGPD
    RGPDConsentCreate,
    RGPDConsentResponse,
    RGPDProcessingCreate,
    RGPDProcessingResponse,
    RGPDRequestCreate,
    RGPDRequestResponse,
    VATDeclarationCreate,
    VATDeclarationResponse,
)
from .service import FrancePackService

__all__ = [
    # Enums
    "PCGClass",
    "TVARate",
    "TVARegime",
    "FECStatus",
    "DSNType",
    "DSNStatus",
    "ContractType",
    "RGPDConsentStatus",
    "RGPDRequestType",
    # Models
    "PCGAccount",
    "FRVATRate",
    "FRVATDeclaration",
    "FECExport",
    "FECEntry",
    "DSNDeclaration",
    "DSNEmployee",
    "FREmploymentContract",
    "RGPDConsent",
    "RGPDRequest",
    "RGPDDataProcessing",
    "RGPDDataBreach",
    # Schemas
    "PCGAccountCreate",
    "PCGAccountUpdate",
    "PCGAccountResponse",
    "FRVATRateCreate",
    "FRVATRateResponse",
    "VATDeclarationCreate",
    "VATDeclarationResponse",
    "FECGenerateRequest",
    "FECEntrySchema",
    "FECValidationResult",
    "FECExportResponse",
    "DSNGenerateRequest",
    "DSNEmployeeData",
    "DSNDeclarationResponse",
    "FRContractCreate",
    "FRContractResponse",
    "RGPDConsentCreate",
    "RGPDConsentResponse",
    "RGPDRequestCreate",
    "RGPDRequestResponse",
    "RGPDProcessingCreate",
    "RGPDProcessingResponse",
    "RGPDBreachCreate",
    "RGPDBreachResponse",
    "FrancePackStats",
    # Service & Router
    "FrancePackService",
    "router",
]
