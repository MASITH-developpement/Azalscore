"""
Module de Signature Électronique - GAP-014

Intégration multi-providers pour signature électronique conforme eIDAS:
- Yousign (leader français)
- DocuSign (leader mondial)
- HelloSign (Dropbox)

Usage:
    from app.modules.esignature import (
        SignatureService,
        SignatureServiceFactory,
        SignatureProvider,
        SignatureLevel,
        Document,
        Signer,
        SignatureField,
        SignatureFieldType,
        create_simple_signature_request
    )

    # Configuration
    service = SignatureServiceFactory.create(
        yousign_config={"api_key": "...", "environment": "sandbox"}
    )

    # Création simple
    request = create_simple_signature_request(
        tenant_id="tenant_123",
        document_name="Contrat.pdf",
        document_content=pdf_bytes,
        signer_email="client@example.com",
        signer_name="Jean Dupont"
    )

    # Envoi
    request = await service.create_and_send_signature_request(
        tenant_id=request.tenant_id,
        name=request.name,
        documents=request.documents,
        signers=request.signers
    )
"""

from .service import (
    # Énumérations
    SignatureProvider,
    SignatureLevel,
    SignatureStatus,
    SignerStatus,
    DocumentType,
    SignatureFieldType,

    # Data classes
    SignatureField,
    Signer,
    Document,
    SignatureRequest,
    SignatureProof,
    WebhookEvent,

    # Providers
    YousignProvider,
    DocuSignProvider,
    HelloSignProvider,

    # Service principal
    SignatureService,
    SignatureServiceFactory,

    # Helpers
    create_simple_signature_request,
)

__all__ = [
    # Énumérations
    "SignatureProvider",
    "SignatureLevel",
    "SignatureStatus",
    "SignerStatus",
    "DocumentType",
    "SignatureFieldType",

    # Data classes
    "SignatureField",
    "Signer",
    "Document",
    "SignatureRequest",
    "SignatureProof",
    "WebhookEvent",

    # Providers
    "YousignProvider",
    "DocuSignProvider",
    "HelloSignProvider",

    # Service principal
    "SignatureService",
    "SignatureServiceFactory",

    # Helpers
    "create_simple_signature_request",
]
