"""
AZALS MODULE HR_VAULT - Coffre-fort RH
========================================

Module de gestion securisee des documents employes.

Fonctionnalites:
- Stockage chiffre AES-256 des documents
- Gestion des acces par role
- Historique complet des acces (audit trail)
- Conformite RGPD (portabilite, droit a l'oubli)
- Integration signature electronique
- Categories personnalisables
- Alertes et notifications
- Export dossier salarie

Conformite:
- RGPD (articles 15, 17, 20)
- Code du travail articles L3243-2, D3243-8
- Decret 2016-1762 (bulletins de paie electroniques)
- NF Z42-020 (archivage electronique)

Inspire de: Sage HR, Lucca, Payfit, Personio, BambooHR
"""

from .models import (
    # Enums
    AlertType,
    EncryptionAlgorithm,
    GDPRRequestStatus,
    GDPRRequestType,
    RetentionPeriod,
    SignatureStatus,
    VaultAccessRole,
    VaultAccessType,
    VaultDocumentStatus,
    VaultDocumentType,
    # Models
    VaultAccessLog,
    VaultAccessPermission,
    VaultAlert,
    VaultConsent,
    VaultDocument,
    VaultDocumentCategory,
    VaultDocumentVersion,
    VaultEncryptionKey,
    VaultGDPRRequest,
    VaultStatistics,
)

from .schemas import (
    VaultCategoryCreate,
    VaultCategoryResponse,
    VaultCategoryUpdate,
    VaultDashboardStats,
    VaultDocumentFilters,
    VaultDocumentListResponse,
    VaultDocumentResponse,
    VaultDocumentSummary,
    VaultDocumentUpdate,
    VaultDocumentUpload,
    VaultEmployeeStats,
    VaultExportRequest,
    VaultExportResponse,
    VaultGDPRRequestCreate,
    VaultGDPRRequestProcess,
    VaultGDPRRequestResponse,
    VaultSignatureRequest,
    VaultSignatureStatus,
)

from .repository import HRVaultRepository
from .service import HRVaultService, create_hr_vault_service
from .router import router

from .exceptions import (
    HRVaultException,
    DocumentNotFoundException,
    DocumentDeletedException,
    DocumentIntegrityException,
    AccessDeniedException,
    VaultNotActivatedException,
    ConsentRequiredException,
    EncryptionException,
    DecryptionException,
    FileSizeLimitException,
    InvalidFileTypeException,
    RetentionPeriodActiveException,
    GDPRRequestNotFoundException,
    CategoryNotFoundException,
)

__all__ = [
    # Enums
    "AlertType",
    "EncryptionAlgorithm",
    "GDPRRequestStatus",
    "GDPRRequestType",
    "RetentionPeriod",
    "SignatureStatus",
    "VaultAccessRole",
    "VaultAccessType",
    "VaultDocumentStatus",
    "VaultDocumentType",
    # Models
    "VaultAccessLog",
    "VaultAccessPermission",
    "VaultAlert",
    "VaultConsent",
    "VaultDocument",
    "VaultDocumentCategory",
    "VaultDocumentVersion",
    "VaultEncryptionKey",
    "VaultGDPRRequest",
    "VaultStatistics",
    # Schemas
    "VaultCategoryCreate",
    "VaultCategoryResponse",
    "VaultCategoryUpdate",
    "VaultDashboardStats",
    "VaultDocumentFilters",
    "VaultDocumentListResponse",
    "VaultDocumentResponse",
    "VaultDocumentSummary",
    "VaultDocumentUpdate",
    "VaultDocumentUpload",
    "VaultEmployeeStats",
    "VaultExportRequest",
    "VaultExportResponse",
    "VaultGDPRRequestCreate",
    "VaultGDPRRequestProcess",
    "VaultGDPRRequestResponse",
    "VaultSignatureRequest",
    "VaultSignatureStatus",
    # Repository & Service
    "HRVaultRepository",
    "HRVaultService",
    "create_hr_vault_service",
    # Router
    "router",
    # Exceptions
    "HRVaultException",
    "DocumentNotFoundException",
    "DocumentDeletedException",
    "DocumentIntegrityException",
    "AccessDeniedException",
    "VaultNotActivatedException",
    "ConsentRequiredException",
    "EncryptionException",
    "DecryptionException",
    "FileSizeLimitException",
    "InvalidFileTypeException",
    "RetentionPeriodActiveException",
    "GDPRRequestNotFoundException",
    "CategoryNotFoundException",
]
