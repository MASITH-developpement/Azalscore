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
    # Enums
    PCGClass,
    TVARate,
    TVARegime,
    FECStatus,
    DSNType,
    DSNStatus,
    ContractType,
    RGPDConsentStatus,
    RGPDRequestType,
    # Models
    PCGAccount,
    FRVATRate,
    FRVATDeclaration,
    FECExport,
    FECEntry,
    DSNDeclaration,
    DSNEmployee,
    FREmploymentContract,
    RGPDConsent,
    RGPDRequest,
    RGPDDataProcessing,
    RGPDDataBreach,
)

from .schemas import (
    # PCG
    PCGAccountCreate,
    PCGAccountUpdate,
    PCGAccountResponse,
    # TVA
    FRVATRateCreate,
    FRVATRateResponse,
    VATDeclarationCreate,
    VATDeclarationResponse,
    # FEC
    FECGenerateRequest,
    FECEntrySchema,
    FECValidationResult,
    FECExportResponse,
    # DSN
    DSNGenerateRequest,
    DSNEmployeeData,
    DSNDeclarationResponse,
    # Contrats
    FRContractCreate,
    FRContractResponse,
    # RGPD
    RGPDConsentCreate,
    RGPDConsentResponse,
    RGPDRequestCreate,
    RGPDRequestResponse,
    RGPDProcessingCreate,
    RGPDProcessingResponse,
    RGPDBreachCreate,
    RGPDBreachResponse,
    # Stats
    FrancePackStats,
)

from .service import FrancePackService
from .router import router

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
