"""
Module Signatures Électroniques - GAP-058

Gestion des signatures électroniques:
- Signature simple et avancée (eIDAS)
- Workflows multi-signataires
- Intégration Yousign/DocuSign
- Certificats et horodatage
- Audit trail complet
- Validation des signatures
"""

from .service import (
    # Énumérations
    SignatureLevel,
    SignatureProvider,
    SignatureStatus,
    SignatureRequestStatus,
    SignerRole,
    AuthenticationMethod,
    FieldType,

    # Data classes
    ProviderConfig,
    SignatureField,
    Signer,
    Document,
    SignatureRequest,
    AuditEvent,
    SignatureValidation,
    Certificate,

    # Service
    SignatureService,
    create_signature_service,
)

__all__ = [
    "SignatureLevel",
    "SignatureProvider",
    "SignatureStatus",
    "SignatureRequestStatus",
    "SignerRole",
    "AuthenticationMethod",
    "FieldType",
    "ProviderConfig",
    "SignatureField",
    "Signer",
    "Document",
    "SignatureRequest",
    "AuditEvent",
    "SignatureValidation",
    "Certificate",
    "SignatureService",
    "create_signature_service",
]
