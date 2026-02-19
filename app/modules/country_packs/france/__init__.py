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
- E-Invoicing 2026 (Factur-X, PDP, PPF) - NOUVEAU
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

# E-Invoicing France 2026
from .einvoicing_models import (
    CompanySizeType,
    EInvoiceDirection,
    EInvoiceFormatDB,
    EInvoiceLifecycleEvent,
    EInvoiceRecord,
    EInvoiceStats,
    EInvoiceStatusDB,
    EReportingSubmission,
    PDPProviderType,
    TenantPDPConfig,
)
from .einvoicing_router import router as einvoicing_router
from .einvoicing_schemas import (
    BulkGenerateRequest,
    BulkGenerateResponse,
    BulkSubmitRequest,
    BulkSubmitResponse,
    EInvoiceCreateFromSource,
    EInvoiceCreateManual,
    EInvoiceDashboard,
    EInvoiceDetailResponse,
    EInvoiceDirection as EInvoiceDirectionSchema,
    EInvoiceFilter,
    EInvoiceFormat,
    EInvoiceListResponse,
    EInvoiceResponse,
    EInvoiceStatus,
    EInvoiceStatusUpdate,
    EInvoiceStatsSummary,
    EInvoiceSubmitResponse,
    EReportingCreate,
    EReportingListResponse,
    EReportingResponse,
    EReportingSubmitResponse,
    PDPConfigCreate,
    PDPConfigListResponse,
    PDPConfigResponse,
    PDPConfigUpdate,
    PDPProviderType as PDPProviderTypeSchema,
    ValidationResult,
)
from .einvoicing_service import TenantEInvoicingService, get_einvoicing_service
from .pdp_client import (
    BasePDPClient,
    ChorusProClient,
    FacturXPDFGenerator,
    GenericPDPClient,
    PDPClientFactory,
    PDPInvoiceResponse,
    PPFClient,
    UnifiedEInvoicingService,
)
from .einvoicing_autogen import (
    AutogenConfidence,
    AutogenResult,
    AutogenSuggestion,
    DocumentContext,
    EInvoiceAutogenService,
    TextTemplates,
    VATCategory,
    get_autogen_service,
)

# PDF Generator Factur-X (PDF/A-3 avec XML embarqué)
from .einvoicing_pdf_generator import (
    FacturXPDFGenerator as FacturXPDFGeneratorNew,
    FacturXProfile,
    InvoiceData,
    InvoiceLine,
    InvoiceParty,
    convert_einvoice_to_pdf_data,
    get_pdf_generator,
)

# Webhooks
from .einvoicing_webhooks import (
    WebhookNotificationService,
    WebhookVerificationService,
    WebhookPayload,
    WebhookEventType,
    get_webhook_service,
)

# FEC - Fichier des Écritures Comptables (Module complet)
from .fec import (
    FECService,
    FECServiceSync,
    fec_router,
    FECExport as FECExportNew,
    FECValidationResult as FECValidationResultModel,
    FECExportRequest,
    FECExportResponse as FECExportResponseNew,
    FECValidationResponse,
    FECColumn,
    FEC_COLUMNS,
)

# PCG 2025 - Plan Comptable Général (Module complet)
from .pcg import (
    PCG2025Service,
    pcg_router,
    PCGAccountCreate as PCGAccountCreate2025,
    PCGAccountResponse as PCGAccountResponse2025,
    PCGInitResult,
    PCGValidationResult as PCGValidationResult2025,
    PCGMigrationResult,
    PCG_CLASSES,
    PCG2025_ALL_ACCOUNTS,
    PCG2025Account,
    get_pcg2025_account,
    get_pcg2025_class,
    validate_pcg_account_number,
)

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
    # E-Invoicing 2026 - Models
    "TenantPDPConfig",
    "EInvoiceRecord",
    "EInvoiceLifecycleEvent",
    "EReportingSubmission",
    "EInvoiceStats",
    "PDPProviderType",
    "EInvoiceStatusDB",
    "EInvoiceDirection",
    "EInvoiceFormatDB",
    "CompanySizeType",
    # E-Invoicing 2026 - Schemas
    "PDPConfigCreate",
    "PDPConfigUpdate",
    "PDPConfigResponse",
    "PDPConfigListResponse",
    "PDPProviderTypeSchema",
    "EInvoiceFormat",
    "EInvoiceStatus",
    "EInvoiceDirectionSchema",
    "EInvoiceCreateFromSource",
    "EInvoiceCreateManual",
    "EInvoiceResponse",
    "EInvoiceDetailResponse",
    "EInvoiceListResponse",
    "EInvoiceFilter",
    "EInvoiceStatusUpdate",
    "EInvoiceSubmitResponse",
    "EInvoiceStatsSummary",
    "EInvoiceDashboard",
    "ValidationResult",
    "EReportingCreate",
    "EReportingResponse",
    "EReportingListResponse",
    "EReportingSubmitResponse",
    "BulkGenerateRequest",
    "BulkGenerateResponse",
    "BulkSubmitRequest",
    "BulkSubmitResponse",
    # E-Invoicing 2026 - Service & Router
    "TenantEInvoicingService",
    "get_einvoicing_service",
    "einvoicing_router",
    # E-Invoicing 2026 - PDP Clients
    "BasePDPClient",
    "ChorusProClient",
    "PPFClient",
    "GenericPDPClient",
    "PDPClientFactory",
    "PDPInvoiceResponse",
    "UnifiedEInvoicingService",
    "FacturXPDFGenerator",
    # E-Invoicing 2026 - Auto-generation
    "EInvoiceAutogenService",
    "get_autogen_service",
    "AutogenResult",
    "AutogenSuggestion",
    "AutogenConfidence",
    "DocumentContext",
    "VATCategory",
    "TextTemplates",
    # E-Invoicing 2026 - PDF Generator
    "FacturXPDFGeneratorNew",
    "FacturXProfile",
    "InvoiceData",
    "InvoiceLine",
    "InvoiceParty",
    "convert_einvoice_to_pdf_data",
    "get_pdf_generator",
    # E-Invoicing 2026 - Webhooks
    "WebhookNotificationService",
    "WebhookVerificationService",
    "WebhookPayload",
    "WebhookEventType",
    "get_webhook_service",
    # FEC - Fichier des Écritures Comptables (Module complet)
    "FECService",
    "FECServiceSync",
    "fec_router",
    "FECExportNew",
    "FECValidationResultModel",
    "FECExportRequest",
    "FECExportResponseNew",
    "FECValidationResponse",
    "FECColumn",
    "FEC_COLUMNS",
    # PCG 2025 - Plan Comptable Général (Module complet)
    "PCG2025Service",
    "pcg_router",
    "PCGAccountCreate2025",
    "PCGAccountResponse2025",
    "PCGInitResult",
    "PCGValidationResult2025",
    "PCGMigrationResult",
    "PCG_CLASSES",
    "PCG2025_ALL_ACCOUNTS",
    "PCG2025Account",
    "get_pcg2025_account",
    "get_pcg2025_class",
    "validate_pcg_account_number",
]
