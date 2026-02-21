"""
AZALS MODULE ESIGNATURE - Signature Electronique
================================================

Module complet de signature electronique conforme eIDAS pour AZALSCORE ERP.

Fonctionnalites:
- Creation d'enveloppes de signature
- Signataires multiples avec ordre
- Champs de signature positionnables
- Envoi par email
- Rappels automatiques
- Suivi statut temps reel
- Certificats et horodatage
- Archivage legal
- Integration providers (DocuSign, Yousign, HelloSign)
- Modeles de documents
- Workflow approbation avant signature
- Audit trail complet

Providers supportes:
- INTERNAL: Signature interne AZALS
- YOUSIGN: Leader francais eIDAS compliant
- DOCUSIGN: Leader mondial
- HELLOSIGN: Dropbox Sign

Usage:
    from app.modules.esignature import (
        ESignatureService,
        get_esignature_service,
        SignatureProvider,
        SignatureLevel,
        EnvelopeStatus,
        SignerStatus,
    )

    # Creer le service
    service = get_esignature_service(db, tenant_id, user_id)

    # Creer une enveloppe
    envelope = service.create_envelope(data, documents)

    # Envoyer
    envelope = await service.send_envelope(envelope.id)

    # Suivi
    envelope = service.get_envelope(envelope.id)
"""

# Models
from .models import (
    # Enums
    SignatureProvider,
    SignatureLevel,
    EnvelopeStatus,
    SignerStatus,
    DocumentType,
    FieldType,
    AuthMethod,
    ReminderType,
    AuditEventType,
    TemplateCategory,
    # Models SQLAlchemy
    ESignatureConfig,
    ProviderCredential,
    SignatureTemplate,
    TemplateField,
    SignatureEnvelope,
    EnvelopeDocument,
    DocumentField,
    EnvelopeSigner,
    SignerAction,
    SignatureAuditEvent,
    SignatureCertificate,
    SignatureReminder,
    SignatureStats,
)

# Schemas
from .schemas import (
    # Config
    ESignatureConfigCreate,
    ESignatureConfigUpdate,
    ESignatureConfigResponse,
    # Provider Credentials
    ProviderCredentialCreate,
    ProviderCredentialUpdate,
    ProviderCredentialResponse,
    # Templates
    SignatureTemplateCreate,
    SignatureTemplateUpdate,
    SignatureTemplateResponse,
    SignatureTemplateList,
    SignatureTemplateListItem,
    TemplateFilters,
    TemplateFieldCreate,
    TemplateFieldResponse,
    SignerRoleSchema,
    MergeFieldSchema,
    # Signers
    SignerCreate,
    SignerUpdate,
    SignerResponse,
    # Documents
    DocumentFieldCreate,
    DocumentFieldResponse,
    EnvelopeDocumentCreate,
    EnvelopeDocumentResponse,
    # Envelopes
    EnvelopeCreate,
    EnvelopeCreateFromTemplate,
    EnvelopeUpdate,
    EnvelopeResponse,
    EnvelopeList,
    EnvelopeListItem,
    EnvelopeFilters,
    # Actions
    SendEnvelopeRequest,
    CancelEnvelopeRequest,
    VoidEnvelopeRequest,
    SendReminderRequest,
    DeclineRequest,
    DelegateRequest,
    ApproveEnvelopeRequest,
    RejectEnvelopeRequest,
    BulkActionRequest,
    BulkActionResponse,
    # Audit & Certificates
    AuditEventResponse,
    AuditTrailResponse,
    CertificateResponse,
    # Stats
    DashboardStatsResponse,
    SignatureStatsResponse,
    # Downloads
    DownloadResponse,
    # Webhooks
    WebhookPayload,
    WebhookResponse,
)

# Repository
from .repository import (
    ESignatureConfigRepository,
    ProviderCredentialRepository,
    SignatureTemplateRepository,
    SignatureEnvelopeRepository,
    EnvelopeDocumentRepository,
    EnvelopeSignerRepository,
    SignatureAuditEventRepository,
    SignatureCertificateRepository,
    SignatureReminderRepository,
    SignatureStatsRepository,
)

# Service
from .service import (
    ESignatureService,
    get_esignature_service,
)

# Providers
from .providers import (
    SignatureProviderInterface,
    YousignProvider,
    DocuSignProvider,
    HelloSignProvider,
    InternalProvider,
    ProviderFactory,
    ProviderEnvelopeInfo,
    ProviderDocumentInfo,
    ProviderSignerInfo,
    ProviderFieldInfo,
    WebhookEventInfo,
)

# Exceptions
from .exceptions import (
    ESignatureError,
    ConfigNotFoundError,
    ConfigAlreadyExistsError,
    ProviderNotConfiguredError,
    ProviderCredentialNotFoundError,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderWebhookError,
    InvalidWebhookSignatureError,
    TemplateNotFoundError,
    TemplateDuplicateCodeError,
    TemplateLockedError,
    TemplateValidationError,
    TemplateFileRequiredError,
    EnvelopeNotFoundError,
    EnvelopeDuplicateNumberError,
    EnvelopeStateError,
    EnvelopeNotDraftError,
    EnvelopeAlreadySentError,
    EnvelopeExpiredError,
    EnvelopeCancelledError,
    EnvelopeCompletedError,
    EnvelopeNoDocumentsError,
    EnvelopeNoSignersError,
    EnvelopePendingApprovalError,
    DocumentNotFoundError,
    DocumentUploadError,
    InvalidDocumentTypeError,
    DocumentTooLargeError,
    DocumentCorruptedError,
    SignerNotFoundError,
    SignerAlreadySignedError,
    SignerDeclinedError,
    SignerExpiredError,
    SignerNotAuthorizedError,
    SignerDelegationNotAllowedError,
    SignerAlreadyDelegatedError,
    InvalidAccessTokenError,
    SignerOrderError,
    FieldNotFoundError,
    FieldRequiredError,
    FieldValidationError,
    FieldAlreadyFilledError,
    SignatureRequiredError,
    InvalidSignatureDataError,
    SignatureVerificationError,
    CertificateNotFoundError,
    CertificateGenerationError,
    CertificateExpiredError,
    CertificateInvalidError,
    ReminderNotFoundError,
    MaxRemindersReachedError,
    ReminderTooSoonError,
    ApprovalRequiredError,
    ApprovalNotAuthorizedError,
    ApprovalAlreadyProcessedError,
    ArchiveError,
    EnvelopeNotCompletedForArchiveError,
    QuotaExceededError,
    MonthlyEnvelopeLimitError,
)

# Router
from .router import router

__all__ = [
    # Router
    "router",

    # Service
    "ESignatureService",
    "get_esignature_service",

    # Enums
    "SignatureProvider",
    "SignatureLevel",
    "EnvelopeStatus",
    "SignerStatus",
    "DocumentType",
    "FieldType",
    "AuthMethod",
    "ReminderType",
    "AuditEventType",
    "TemplateCategory",

    # Models
    "ESignatureConfig",
    "ProviderCredential",
    "SignatureTemplate",
    "TemplateField",
    "SignatureEnvelope",
    "EnvelopeDocument",
    "DocumentField",
    "EnvelopeSigner",
    "SignerAction",
    "SignatureAuditEvent",
    "SignatureCertificate",
    "SignatureReminder",
    "SignatureStats",

    # Schemas
    "ESignatureConfigCreate",
    "ESignatureConfigUpdate",
    "ESignatureConfigResponse",
    "ProviderCredentialCreate",
    "ProviderCredentialUpdate",
    "ProviderCredentialResponse",
    "SignatureTemplateCreate",
    "SignatureTemplateUpdate",
    "SignatureTemplateResponse",
    "SignatureTemplateList",
    "EnvelopeCreate",
    "EnvelopeCreateFromTemplate",
    "EnvelopeUpdate",
    "EnvelopeResponse",
    "EnvelopeList",
    "SignerCreate",
    "SignerUpdate",
    "SignerResponse",

    # Providers
    "SignatureProviderInterface",
    "YousignProvider",
    "DocuSignProvider",
    "HelloSignProvider",
    "InternalProvider",
    "ProviderFactory",

    # Exceptions
    "ESignatureError",
    "EnvelopeNotFoundError",
    "SignerNotFoundError",
    "TemplateNotFoundError",
    "InvalidAccessTokenError",
]
