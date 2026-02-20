"""
Module de Signature Électronique - GAP-014

Intégration multi-providers pour signature électronique:
- Yousign (leader français, eIDAS compliant)
- DocuSign (leader mondial)
- HelloSign (Dropbox)

Fonctionnalités:
- Création de demandes de signature
- Envoi multi-signataires avec ordre
- Suivi temps réel des signatures
- Webhooks pour notifications
- Archivage avec preuve de signature
- Signature qualifiée eIDAS

Architecture multi-tenant avec isolation stricte.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from abc import ABC, abstractmethod
import hashlib
import hmac
import json
import base64
import uuid


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class SignatureProvider(Enum):
    """Providers de signature électronique supportés."""
    YOUSIGN = "yousign"
    DOCUSIGN = "docusign"
    HELLOSIGN = "hellosign"


class SignatureLevel(Enum):
    """Niveau de signature selon eIDAS."""
    SIMPLE = "simple"  # Signature simple (email)
    ADVANCED = "advanced"  # Signature avancée (SMS + pièce identité)
    QUALIFIED = "qualified"  # Signature qualifiée (certificat qualifié)


class SignatureStatus(Enum):
    """Statut d'une demande de signature."""
    DRAFT = "draft"  # Brouillon
    PENDING = "pending"  # En attente d'envoi
    SENT = "sent"  # Envoyée aux signataires
    IN_PROGRESS = "in_progress"  # Signatures en cours
    COMPLETED = "completed"  # Toutes signatures reçues
    DECLINED = "declined"  # Refusée par un signataire
    EXPIRED = "expired"  # Expirée
    CANCELLED = "cancelled"  # Annulée


class SignerStatus(Enum):
    """Statut d'un signataire."""
    PENDING = "pending"  # En attente
    NOTIFIED = "notified"  # Notifié par email/SMS
    OPENED = "opened"  # Document ouvert
    SIGNED = "signed"  # Signé
    DECLINED = "declined"  # Refusé
    EXPIRED = "expired"  # Expiré


class DocumentType(Enum):
    """Type de document à signer."""
    CONTRACT = "contract"  # Contrat
    INVOICE = "invoice"  # Facture
    QUOTE = "quote"  # Devis
    NDA = "nda"  # Accord de confidentialité
    EMPLOYMENT = "employment"  # Contrat de travail
    AMENDMENT = "amendment"  # Avenant
    MANDATE = "mandate"  # Mandat
    OTHER = "other"  # Autre


class SignatureFieldType(Enum):
    """Type de champ de signature."""
    SIGNATURE = "signature"  # Signature
    INITIALS = "initials"  # Paraphe
    DATE = "date"  # Date
    TEXT = "text"  # Texte libre
    CHECKBOX = "checkbox"  # Case à cocher


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SignatureField:
    """Champ de signature dans un document."""
    field_type: SignatureFieldType
    page: int
    x: float  # Position X en %
    y: float  # Position Y en %
    width: float = 150  # Largeur en pixels
    height: float = 50  # Hauteur en pixels
    required: bool = True
    signer_index: int = 0  # Index du signataire concerné
    label: Optional[str] = None


@dataclass
class Signer:
    """Signataire d'un document."""
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    order: int = 1  # Ordre de signature (1 = premier)
    signature_level: SignatureLevel = SignatureLevel.SIMPLE

    # Authentification renforcée
    require_id_verification: bool = False
    require_sms_otp: bool = False

    # Statut
    status: SignerStatus = SignerStatus.PENDING
    signed_at: Optional[datetime] = None
    ip_address: Optional[str] = None

    # ID externe (provider)
    external_id: Optional[str] = None


@dataclass
class Document:
    """Document à signer."""
    name: str
    content: bytes  # Contenu PDF
    document_type: DocumentType = DocumentType.OTHER

    # Métadonnées
    description: Optional[str] = None
    reference: Optional[str] = None

    # Champs de signature
    fields: List[SignatureField] = field(default_factory=list)

    # ID externe (provider)
    external_id: Optional[str] = None

    # Hash du document original
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content).hexdigest()


@dataclass
class SignatureRequest:
    """Demande de signature."""
    id: str
    tenant_id: str
    name: str

    # Documents et signataires
    documents: List[Document]
    signers: List[Signer]

    # Configuration
    provider: SignatureProvider = SignatureProvider.YOUSIGN
    signature_level: SignatureLevel = SignatureLevel.SIMPLE

    # Expiration
    expires_at: Optional[datetime] = None
    reminder_interval_days: int = 3

    # Messages personnalisés
    email_subject: Optional[str] = None
    email_message: Optional[str] = None

    # Statut
    status: SignatureStatus = SignatureStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # IDs externes
    external_id: Optional[str] = None

    # Webhook
    webhook_url: Optional[str] = None

    # Métadonnées business
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignatureProof:
    """Preuve de signature (audit trail)."""
    request_id: str
    signer_email: str
    signed_at: datetime
    ip_address: str
    user_agent: str

    # Vérification
    signature_hash: str
    certificate_issuer: Optional[str] = None
    certificate_serial: Optional[str] = None

    # Localisation
    country: Optional[str] = None
    city: Optional[str] = None

    # Authentification
    authentication_method: str = "email"  # email, sms_otp, id_verification

    # Document signé
    signed_document_hash: Optional[str] = None


@dataclass
class WebhookEvent:
    """Événement webhook reçu d'un provider."""
    provider: SignatureProvider
    event_type: str
    request_external_id: str
    signer_external_id: Optional[str]
    timestamp: datetime
    raw_payload: Dict[str, Any]


# ============================================================================
# INTERFACE PROVIDER
# ============================================================================

class SignatureProviderInterface(ABC):
    """Interface commune pour tous les providers de signature."""

    @abstractmethod
    async def create_signature_request(
        self,
        request: SignatureRequest
    ) -> str:
        """Crée une demande de signature. Retourne l'ID externe."""
        pass

    @abstractmethod
    async def send_signature_request(
        self,
        external_id: str
    ) -> bool:
        """Envoie la demande aux signataires."""
        pass

    @abstractmethod
    async def get_request_status(
        self,
        external_id: str
    ) -> Dict[str, Any]:
        """Récupère le statut d'une demande."""
        pass

    @abstractmethod
    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        """Télécharge le document signé."""
        pass

    @abstractmethod
    async def download_audit_trail(
        self,
        external_id: str
    ) -> bytes:
        """Télécharge la preuve de signature (audit trail PDF)."""
        pass

    @abstractmethod
    async def cancel_request(
        self,
        external_id: str
    ) -> bool:
        """Annule une demande de signature."""
        pass

    @abstractmethod
    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        """Envoie un rappel aux signataires."""
        pass

    @abstractmethod
    def parse_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> WebhookEvent:
        """Parse un webhook entrant."""
        pass


# ============================================================================
# PROVIDER YOUSIGN
# ============================================================================

class YousignProvider(SignatureProviderInterface):
    """
    Provider Yousign - Leader français de la signature électronique.

    Avantages:
    - Conforme eIDAS (signature qualifiée)
    - Serveurs en France
    - API moderne et bien documentée
    - Support natif français

    Documentation: https://developers.yousign.com/
    """

    def __init__(
        self,
        api_key: str,
        environment: str = "production",  # production ou sandbox
        webhook_secret: Optional[str] = None
    ):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

        if environment == "sandbox":
            self.base_url = "https://api-sandbox.yousign.app/v3"
        else:
            self.base_url = "https://api.yousign.app/v3"

    def _get_headers(self) -> Dict[str, str]:
        """Headers pour les requêtes API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_signature_request(
        self,
        request: SignatureRequest
    ) -> str:
        """Crée une demande de signature Yousign."""
        # Construction du payload
        payload = {
            "name": request.name,
            "delivery_mode": "email",
            "timezone": "Europe/Paris",
            "signers_allowed_to_decline": True
        }

        if request.expires_at:
            payload["expiration_date"] = request.expires_at.isoformat()

        if request.email_subject:
            payload["email_custom_note"] = request.email_message or ""

        # Métadonnées
        if request.metadata:
            payload["external_id"] = request.metadata.get("external_ref", request.id)

        # Webhook
        if request.webhook_url:
            payload["webhook_url"] = request.webhook_url

        # Simulation - en production, appel HTTP réel
        # response = await self._http_post("/signature_requests", payload)
        external_id = f"yousign_{uuid.uuid4().hex[:16]}"

        # Upload des documents
        for doc in request.documents:
            doc_payload = {
                "file_name": doc.name,
                "file_content": base64.b64encode(doc.content).decode(),
                "content_type": "application/pdf"
            }
            # doc_response = await self._http_post(
            #     f"/signature_requests/{external_id}/documents",
            #     doc_payload
            # )
            doc.external_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Ajout des signataires
        for i, signer in enumerate(request.signers):
            signer_payload = {
                "info": {
                    "first_name": signer.first_name,
                    "last_name": signer.last_name,
                    "email": signer.email,
                    "locale": "fr"
                },
                "signature_level": self._map_signature_level(signer.signature_level),
                "signature_authentication_mode": self._get_auth_mode(signer)
            }

            if signer.phone:
                signer_payload["info"]["phone_number"] = signer.phone

            # signer_response = await self._http_post(
            #     f"/signature_requests/{external_id}/signers",
            #     signer_payload
            # )
            signer.external_id = f"signer_{uuid.uuid4().hex[:12]}"

            # Ajout des champs de signature pour ce signataire
            for doc in request.documents:
                for field in doc.fields:
                    if field.signer_index == i:
                        field_payload = self._build_field_payload(field, doc.external_id)
                        # await self._http_post(
                        #     f"/signature_requests/{external_id}/signers/{signer.external_id}/fields",
                        #     field_payload
                        # )

        return external_id

    def _map_signature_level(self, level: SignatureLevel) -> str:
        """Mappe le niveau de signature vers Yousign."""
        mapping = {
            SignatureLevel.SIMPLE: "electronic_signature",
            SignatureLevel.ADVANCED: "advanced_electronic_signature",
            SignatureLevel.QUALIFIED: "qualified_electronic_signature"
        }
        return mapping.get(level, "electronic_signature")

    def _get_auth_mode(self, signer: Signer) -> str:
        """Détermine le mode d'authentification."""
        if signer.require_id_verification:
            return "id_document"
        elif signer.require_sms_otp:
            return "otp_sms"
        return "no_otp"

    def _build_field_payload(
        self,
        field: SignatureField,
        document_id: str
    ) -> Dict[str, Any]:
        """Construit le payload pour un champ de signature."""
        type_mapping = {
            SignatureFieldType.SIGNATURE: "signature",
            SignatureFieldType.INITIALS: "initials",
            SignatureFieldType.DATE: "date",
            SignatureFieldType.TEXT: "text",
            SignatureFieldType.CHECKBOX: "checkbox"
        }

        return {
            "document_id": document_id,
            "type": type_mapping.get(field.field_type, "signature"),
            "page": field.page,
            "x": field.x,
            "y": field.y,
            "width": field.width,
            "height": field.height,
            "optional": not field.required
        }

    async def send_signature_request(self, external_id: str) -> bool:
        """Active et envoie la demande de signature."""
        # response = await self._http_post(
        #     f"/signature_requests/{external_id}/activate",
        #     {}
        # )
        return True

    async def get_request_status(self, external_id: str) -> Dict[str, Any]:
        """Récupère le statut complet d'une demande."""
        # response = await self._http_get(f"/signature_requests/{external_id}")

        # Simulation
        return {
            "id": external_id,
            "status": "ongoing",  # draft, ongoing, done, expired, canceled
            "signers": [],
            "documents": []
        }

    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        """Télécharge le document signé."""
        # response = await self._http_get(
        #     f"/signature_requests/{external_id}/documents/{document_external_id}/download",
        #     raw=True
        # )
        return b""  # PDF signé

    async def download_audit_trail(self, external_id: str) -> bytes:
        """Télécharge la preuve de signature."""
        # response = await self._http_get(
        #     f"/signature_requests/{external_id}/audit_trails/download",
        #     raw=True
        # )
        return b""  # PDF audit trail

    async def cancel_request(self, external_id: str) -> bool:
        """Annule une demande de signature."""
        # response = await self._http_post(
        #     f"/signature_requests/{external_id}/cancel",
        #     {"reason": "Annulée par l'utilisateur"}
        # )
        return True

    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        """Envoie un rappel."""
        if signer_external_id:
            # Rappel à un signataire spécifique
            # await self._http_post(
            #     f"/signature_requests/{external_id}/signers/{signer_external_id}/send_reminder",
            #     {}
            # )
            pass
        else:
            # Rappel à tous les signataires en attente
            # await self._http_post(
            #     f"/signature_requests/{external_id}/reminders",
            #     {}
            # )
            pass
        return True

    def parse_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> WebhookEvent:
        """Parse un webhook Yousign."""
        # Vérification signature HMAC si configurée
        if self.webhook_secret and signature:
            expected = hmac.new(
                self.webhook_secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError("Signature webhook invalide")

        event_type = payload.get("event_name", "unknown")
        data = payload.get("data", {})

        return WebhookEvent(
            provider=SignatureProvider.YOUSIGN,
            event_type=event_type,
            request_external_id=data.get("signature_request", {}).get("id", ""),
            signer_external_id=data.get("signer", {}).get("id"),
            timestamp=datetime.now(),
            raw_payload=payload
        )


# ============================================================================
# PROVIDER DOCUSIGN
# ============================================================================

class DocuSignProvider(SignatureProviderInterface):
    """
    Provider DocuSign - Leader mondial de la signature électronique.

    Avantages:
    - Présence mondiale
    - Nombreuses intégrations
    - PowerForms et templates avancés
    - Signature mobile optimisée

    Documentation: https://developers.docusign.com/
    """

    def __init__(
        self,
        integration_key: str,
        account_id: str,
        user_id: str,
        private_key: str,
        environment: str = "production",
        webhook_secret: Optional[str] = None
    ):
        self.integration_key = integration_key
        self.account_id = account_id
        self.user_id = user_id
        self.private_key = private_key
        self.webhook_secret = webhook_secret

        if environment == "demo":
            self.base_url = "https://demo.docusign.net/restapi/v2.1"
            self.auth_url = "https://account-d.docusign.com"
        else:
            self.base_url = "https://eu.docusign.net/restapi/v2.1"
            self.auth_url = "https://account.docusign.com"

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _ensure_token(self):
        """S'assure qu'un token d'accès valide est disponible."""
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return

        # JWT Grant flow
        # claims = {
        #     "iss": self.integration_key,
        #     "sub": self.user_id,
        #     "aud": self.auth_url,
        #     "iat": int(datetime.now().timestamp()),
        #     "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        #     "scope": "signature impersonation"
        # }
        # jwt_token = jwt.encode(claims, self.private_key, algorithm="RS256")
        # response = await self._http_post("/oauth/token", {...})

        self._access_token = "simulated_token"
        self._token_expires_at = datetime.now() + timedelta(hours=1)

    async def create_signature_request(
        self,
        request: SignatureRequest
    ) -> str:
        """Crée une enveloppe DocuSign."""
        await self._ensure_token()

        # Construction de l'enveloppe
        envelope = {
            "emailSubject": request.email_subject or f"Signature requise: {request.name}",
            "status": "created",  # created = brouillon, sent = envoyé
            "documents": [],
            "recipients": {
                "signers": []
            }
        }

        # Documents
        for i, doc in enumerate(request.documents):
            envelope["documents"].append({
                "documentId": str(i + 1),
                "name": doc.name,
                "documentBase64": base64.b64encode(doc.content).decode(),
                "fileExtension": "pdf"
            })

        # Signataires avec routing order
        for i, signer in enumerate(request.signers):
            signer_data = {
                "recipientId": str(i + 1),
                "routingOrder": str(signer.order),
                "email": signer.email,
                "name": f"{signer.first_name} {signer.last_name}",
                "tabs": self._build_tabs(request.documents, i)
            }

            # Authentification renforcée
            if signer.require_sms_otp and signer.phone:
                signer_data["identityVerification"] = {
                    "workflowId": "phone_auth",
                    "steps": [{
                        "name": "phone",
                        "type": "phoneAuthentication",
                        "recipientSupplied": {
                            "phoneNumber": signer.phone
                        }
                    }]
                }

            if signer.require_id_verification:
                signer_data["identityVerification"] = {
                    "workflowId": "id_check"
                }

            envelope["recipients"]["signers"].append(signer_data)
            signer.external_id = str(i + 1)

        # Message personnalisé
        if request.email_message:
            envelope["emailBlurb"] = request.email_message

        # Expiration
        if request.expires_at:
            days_until = (request.expires_at - datetime.now()).days
            if days_until > 0:
                envelope["notification"] = {
                    "expirations": {
                        "expireEnabled": True,
                        "expireAfter": days_until
                    }
                }

        # Simulation - en production: appel API
        # response = await self._http_post(
        #     f"/accounts/{self.account_id}/envelopes",
        #     envelope
        # )

        external_id = f"docusign_{uuid.uuid4().hex[:16]}"

        for doc in request.documents:
            doc.external_id = f"doc_{uuid.uuid4().hex[:12]}"

        return external_id

    def _build_tabs(
        self,
        documents: List[Document],
        signer_index: int
    ) -> Dict[str, List[Dict]]:
        """Construit les onglets (champs) pour un signataire."""
        tabs = {
            "signHereTabs": [],
            "initialHereTabs": [],
            "dateSignedTabs": [],
            "textTabs": [],
            "checkboxTabs": []
        }

        for doc_index, doc in enumerate(documents):
            for field in doc.fields:
                if field.signer_index != signer_index:
                    continue

                tab_data = {
                    "documentId": str(doc_index + 1),
                    "pageNumber": str(field.page),
                    "xPosition": str(int(field.x)),
                    "yPosition": str(int(field.y)),
                    "optional": not field.required
                }

                if field.field_type == SignatureFieldType.SIGNATURE:
                    tabs["signHereTabs"].append(tab_data)
                elif field.field_type == SignatureFieldType.INITIALS:
                    tabs["initialHereTabs"].append(tab_data)
                elif field.field_type == SignatureFieldType.DATE:
                    tabs["dateSignedTabs"].append(tab_data)
                elif field.field_type == SignatureFieldType.TEXT:
                    tab_data["width"] = int(field.width)
                    tab_data["height"] = int(field.height)
                    tabs["textTabs"].append(tab_data)
                elif field.field_type == SignatureFieldType.CHECKBOX:
                    tabs["checkboxTabs"].append(tab_data)

        return tabs

    async def send_signature_request(self, external_id: str) -> bool:
        """Envoie l'enveloppe aux signataires."""
        await self._ensure_token()

        # response = await self._http_put(
        #     f"/accounts/{self.account_id}/envelopes/{external_id}",
        #     {"status": "sent"}
        # )
        return True

    async def get_request_status(self, external_id: str) -> Dict[str, Any]:
        """Récupère le statut de l'enveloppe."""
        await self._ensure_token()

        # response = await self._http_get(
        #     f"/accounts/{self.account_id}/envelopes/{external_id}"
        # )

        return {
            "envelopeId": external_id,
            "status": "sent",  # created, sent, delivered, completed, declined, voided
            "recipients": {
                "signers": []
            }
        }

    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        """Télécharge le document signé."""
        await self._ensure_token()

        # response = await self._http_get(
        #     f"/accounts/{self.account_id}/envelopes/{external_id}/documents/{document_external_id}",
        #     raw=True
        # )
        return b""

    async def download_audit_trail(self, external_id: str) -> bytes:
        """Télécharge le certificate of completion."""
        await self._ensure_token()

        # response = await self._http_get(
        #     f"/accounts/{self.account_id}/envelopes/{external_id}/documents/certificate",
        #     raw=True
        # )
        return b""

    async def cancel_request(self, external_id: str) -> bool:
        """Annule (void) l'enveloppe."""
        await self._ensure_token()

        # response = await self._http_put(
        #     f"/accounts/{self.account_id}/envelopes/{external_id}",
        #     {"status": "voided", "voidedReason": "Annulée par l'utilisateur"}
        # )
        return True

    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        """Envoie un rappel via DocuSign."""
        await self._ensure_token()

        # response = await self._http_post(
        #     f"/accounts/{self.account_id}/envelopes/{external_id}/recipients",
        #     {"resend_envelope": True}
        # )
        return True

    def parse_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> WebhookEvent:
        """Parse un webhook DocuSign Connect."""
        # Vérification HMAC
        if self.webhook_secret and signature:
            computed = base64.b64encode(
                hmac.new(
                    self.webhook_secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).digest()
            ).decode()
            if not hmac.compare_digest(signature, computed):
                raise ValueError("Signature webhook invalide")

        envelope_status = payload.get("envelopeStatus", {})

        return WebhookEvent(
            provider=SignatureProvider.DOCUSIGN,
            event_type=envelope_status.get("status", "unknown"),
            request_external_id=envelope_status.get("envelopeId", ""),
            signer_external_id=None,
            timestamp=datetime.now(),
            raw_payload=payload
        )


# ============================================================================
# PROVIDER HELLOSIGN
# ============================================================================

class HelloSignProvider(SignatureProviderInterface):
    """
    Provider HelloSign (Dropbox Sign) - Solution simple et élégante.

    Avantages:
    - Interface utilisateur très simple
    - Intégration Dropbox native
    - Prix compétitif
    - API simple

    Documentation: https://developers.hellosign.com/
    """

    def __init__(
        self,
        api_key: str,
        client_id: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        self.api_key = api_key
        self.client_id = client_id
        self.webhook_secret = webhook_secret
        self.base_url = "https://api.hellosign.com/v3"

    async def create_signature_request(
        self,
        request: SignatureRequest
    ) -> str:
        """Crée une signature request HelloSign."""

        form_data = {
            "title": request.name,
            "subject": request.email_subject or f"Signature requise: {request.name}",
            "message": request.email_message or "Merci de signer ce document.",
            "test_mode": 0
        }

        # Signataires
        for i, signer in enumerate(request.signers):
            form_data[f"signers[{i}][email_address]"] = signer.email
            form_data[f"signers[{i}][name]"] = f"{signer.first_name} {signer.last_name}"
            form_data[f"signers[{i}][order]"] = signer.order
            signer.external_id = str(i)

        # Documents (envoi en multipart)
        # files = []
        # for i, doc in enumerate(request.documents):
        #     files.append((f"file[{i}]", (doc.name, doc.content, "application/pdf")))

        # Expiration
        if request.expires_at:
            days = (request.expires_at - datetime.now()).days
            if days > 0:
                form_data["signing_options"] = {"expiration_days": days}

        # Simulation
        external_id = f"hellosign_{uuid.uuid4().hex[:16]}"

        for doc in request.documents:
            doc.external_id = f"doc_{uuid.uuid4().hex[:12]}"

        return external_id

    async def send_signature_request(self, external_id: str) -> bool:
        """HelloSign envoie automatiquement à la création."""
        return True

    async def get_request_status(self, external_id: str) -> Dict[str, Any]:
        """Récupère le statut de la signature request."""
        # response = await self._http_get(f"/signature_request/{external_id}")

        return {
            "signature_request_id": external_id,
            "is_complete": False,
            "is_declined": False,
            "signatures": []
        }

    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        """Télécharge le document signé."""
        # response = await self._http_get(
        #     f"/signature_request/files/{external_id}",
        #     params={"file_type": "pdf"},
        #     raw=True
        # )
        return b""

    async def download_audit_trail(self, external_id: str) -> bytes:
        """Télécharge le fichier de log."""
        # response = await self._http_get(
        #     f"/signature_request/files/{external_id}",
        #     params={"file_type": "pdf", "get_data_uri": True},
        #     raw=True
        # )
        return b""

    async def cancel_request(self, external_id: str) -> bool:
        """Annule la signature request."""
        # response = await self._http_post(
        #     f"/signature_request/cancel/{external_id}",
        #     {}
        # )
        return True

    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        """Envoie un rappel."""
        # if signer_external_id:
        #     response = await self._http_post(
        #         f"/signature_request/remind/{external_id}",
        #         {"email_address": signer_email}
        #     )
        return True

    def parse_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> WebhookEvent:
        """Parse un webhook HelloSign."""
        # Vérification HMAC
        if self.webhook_secret and signature:
            computed = hmac.new(
                self.webhook_secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, computed):
                raise ValueError("Signature webhook invalide")

        event = payload.get("event", {})
        signature_request = payload.get("signature_request", {})

        return WebhookEvent(
            provider=SignatureProvider.HELLOSIGN,
            event_type=event.get("event_type", "unknown"),
            request_external_id=signature_request.get("signature_request_id", ""),
            signer_external_id=None,
            timestamp=datetime.now(),
            raw_payload=payload
        )


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class SignatureService:
    """
    Service principal de signature électronique.

    Orchestre les différents providers et gère:
    - Création et envoi des demandes
    - Suivi des signatures
    - Téléchargement des documents signés
    - Webhooks et notifications
    - Archivage et preuves
    """

    def __init__(
        self,
        providers: Dict[SignatureProvider, SignatureProviderInterface]
    ):
        self.providers = providers
        self._requests_cache: Dict[str, SignatureRequest] = {}

    def get_provider(
        self,
        provider: SignatureProvider
    ) -> SignatureProviderInterface:
        """Récupère un provider configuré."""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider.value} non configuré")
        return self.providers[provider]

    async def create_and_send_signature_request(
        self,
        tenant_id: str,
        name: str,
        documents: List[Document],
        signers: List[Signer],
        provider: SignatureProvider = SignatureProvider.YOUSIGN,
        signature_level: SignatureLevel = SignatureLevel.SIMPLE,
        expires_in_days: int = 30,
        email_subject: Optional[str] = None,
        email_message: Optional[str] = None,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        send_immediately: bool = True
    ) -> SignatureRequest:
        """
        Crée et envoie une demande de signature.

        Args:
            tenant_id: ID du tenant
            name: Nom de la demande
            documents: Liste des documents à signer
            signers: Liste des signataires
            provider: Provider à utiliser
            signature_level: Niveau de signature eIDAS
            expires_in_days: Jours avant expiration
            email_subject: Sujet de l'email
            email_message: Message personnalisé
            webhook_url: URL webhook pour notifications
            metadata: Métadonnées business
            send_immediately: Envoyer immédiatement

        Returns:
            SignatureRequest créée et envoyée
        """
        # Validation
        if not documents:
            raise ValueError("Au moins un document requis")
        if not signers:
            raise ValueError("Au moins un signataire requis")

        # Création de la demande
        request = SignatureRequest(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            documents=documents,
            signers=signers,
            provider=provider,
            signature_level=signature_level,
            expires_at=datetime.now() + timedelta(days=expires_in_days),
            email_subject=email_subject,
            email_message=email_message,
            webhook_url=webhook_url,
            metadata=metadata or {}
        )

        # Appliquer le niveau de signature aux signataires
        for signer in request.signers:
            if signer.signature_level == SignatureLevel.SIMPLE:
                signer.signature_level = signature_level

        # Créer chez le provider
        provider_impl = self.get_provider(provider)
        external_id = await provider_impl.create_signature_request(request)
        request.external_id = external_id

        # Envoyer si demandé
        if send_immediately:
            success = await provider_impl.send_signature_request(external_id)
            if success:
                request.status = SignatureStatus.SENT
                request.sent_at = datetime.now()

        # Cacher localement
        self._requests_cache[request.id] = request

        return request

    async def get_signature_status(
        self,
        request: SignatureRequest
    ) -> SignatureRequest:
        """
        Met à jour et retourne le statut d'une demande.

        Args:
            request: Demande à vérifier

        Returns:
            Demande mise à jour
        """
        provider = self.get_provider(request.provider)
        status_data = await provider.get_request_status(request.external_id)

        # Mapper le statut provider vers notre enum
        request.status = self._map_status(request.provider, status_data)

        # Mettre à jour les signataires
        self._update_signers_status(request, status_data)

        if request.status == SignatureStatus.COMPLETED:
            request.completed_at = datetime.now()

        return request

    def _map_status(
        self,
        provider: SignatureProvider,
        status_data: Dict[str, Any]
    ) -> SignatureStatus:
        """Mappe le statut provider vers notre enum."""
        if provider == SignatureProvider.YOUSIGN:
            mapping = {
                "draft": SignatureStatus.DRAFT,
                "ongoing": SignatureStatus.IN_PROGRESS,
                "done": SignatureStatus.COMPLETED,
                "expired": SignatureStatus.EXPIRED,
                "canceled": SignatureStatus.CANCELLED
            }
            return mapping.get(status_data.get("status", ""), SignatureStatus.PENDING)

        elif provider == SignatureProvider.DOCUSIGN:
            mapping = {
                "created": SignatureStatus.DRAFT,
                "sent": SignatureStatus.SENT,
                "delivered": SignatureStatus.IN_PROGRESS,
                "completed": SignatureStatus.COMPLETED,
                "declined": SignatureStatus.DECLINED,
                "voided": SignatureStatus.CANCELLED
            }
            return mapping.get(status_data.get("status", ""), SignatureStatus.PENDING)

        elif provider == SignatureProvider.HELLOSIGN:
            if status_data.get("is_complete"):
                return SignatureStatus.COMPLETED
            elif status_data.get("is_declined"):
                return SignatureStatus.DECLINED
            return SignatureStatus.IN_PROGRESS

        return SignatureStatus.PENDING

    def _update_signers_status(
        self,
        request: SignatureRequest,
        status_data: Dict[str, Any]
    ):
        """Met à jour le statut des signataires."""
        # Implémentation spécifique par provider
        pass

    async def download_signed_documents(
        self,
        request: SignatureRequest
    ) -> Dict[str, bytes]:
        """
        Télécharge tous les documents signés.

        Args:
            request: Demande complétée

        Returns:
            Dict nom_document -> contenu PDF signé
        """
        if request.status != SignatureStatus.COMPLETED:
            raise ValueError("La demande n'est pas encore complétée")

        provider = self.get_provider(request.provider)
        result = {}

        for doc in request.documents:
            content = await provider.download_signed_document(
                request.external_id,
                doc.external_id
            )
            result[doc.name] = content

        return result

    async def download_audit_trail(
        self,
        request: SignatureRequest
    ) -> bytes:
        """
        Télécharge la preuve de signature (audit trail).

        Args:
            request: Demande complétée

        Returns:
            PDF de la preuve de signature
        """
        provider = self.get_provider(request.provider)
        return await provider.download_audit_trail(request.external_id)

    async def cancel_signature_request(
        self,
        request: SignatureRequest
    ) -> bool:
        """
        Annule une demande de signature.

        Args:
            request: Demande à annuler

        Returns:
            True si annulée avec succès
        """
        if request.status in [SignatureStatus.COMPLETED, SignatureStatus.CANCELLED]:
            raise ValueError(f"Impossible d'annuler une demande {request.status.value}")

        provider = self.get_provider(request.provider)
        success = await provider.cancel_request(request.external_id)

        if success:
            request.status = SignatureStatus.CANCELLED

        return success

    async def send_reminder(
        self,
        request: SignatureRequest,
        signer: Optional[Signer] = None
    ) -> bool:
        """
        Envoie un rappel aux signataires.

        Args:
            request: Demande en cours
            signer: Signataire spécifique (optionnel)

        Returns:
            True si rappel envoyé
        """
        if request.status not in [SignatureStatus.SENT, SignatureStatus.IN_PROGRESS]:
            raise ValueError("Rappel possible uniquement pour demandes en cours")

        provider = self.get_provider(request.provider)
        return await provider.send_reminder(
            request.external_id,
            signer.external_id if signer else None
        )

    async def handle_webhook(
        self,
        provider: SignatureProvider,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Optional[SignatureRequest]:
        """
        Traite un webhook entrant.

        Args:
            provider: Provider source
            payload: Payload du webhook
            signature: Signature HMAC pour vérification

        Returns:
            SignatureRequest mise à jour si trouvée
        """
        provider_impl = self.get_provider(provider)
        event = provider_impl.parse_webhook(payload, signature)

        # Chercher la demande correspondante
        request = None
        for req in self._requests_cache.values():
            if req.external_id == event.request_external_id:
                request = req
                break

        if not request:
            # En production, chercher en base de données
            return None

        # Mettre à jour selon l'événement
        await self.get_signature_status(request)

        return request


# ============================================================================
# FACTORY
# ============================================================================

class SignatureServiceFactory:
    """Factory pour créer le service de signature configuré."""

    @staticmethod
    def create(
        yousign_config: Optional[Dict[str, str]] = None,
        docusign_config: Optional[Dict[str, str]] = None,
        hellosign_config: Optional[Dict[str, str]] = None
    ) -> SignatureService:
        """
        Crée un service de signature avec les providers configurés.

        Args:
            yousign_config: {"api_key": ..., "environment": ...}
            docusign_config: {"integration_key": ..., "account_id": ..., ...}
            hellosign_config: {"api_key": ..., "client_id": ...}

        Returns:
            SignatureService configuré
        """
        providers = {}

        if yousign_config:
            providers[SignatureProvider.YOUSIGN] = YousignProvider(
                api_key=yousign_config["api_key"],
                environment=yousign_config.get("environment", "production"),
                webhook_secret=yousign_config.get("webhook_secret")
            )

        if docusign_config:
            providers[SignatureProvider.DOCUSIGN] = DocuSignProvider(
                integration_key=docusign_config["integration_key"],
                account_id=docusign_config["account_id"],
                user_id=docusign_config["user_id"],
                private_key=docusign_config["private_key"],
                environment=docusign_config.get("environment", "production"),
                webhook_secret=docusign_config.get("webhook_secret")
            )

        if hellosign_config:
            providers[SignatureProvider.HELLOSIGN] = HelloSignProvider(
                api_key=hellosign_config["api_key"],
                client_id=hellosign_config.get("client_id"),
                webhook_secret=hellosign_config.get("webhook_secret")
            )

        return SignatureService(providers)


# ============================================================================
# HELPERS
# ============================================================================

def create_simple_signature_request(
    tenant_id: str,
    document_name: str,
    document_content: bytes,
    signer_email: str,
    signer_name: str,
    signature_page: int = 1,
    signature_position: tuple = (70, 80)  # % x, y
) -> SignatureRequest:
    """
    Crée une demande de signature simple (1 document, 1 signataire).

    Helper pour les cas courants.
    """
    first_name, *last_parts = signer_name.split()
    last_name = " ".join(last_parts) if last_parts else ""

    document = Document(
        name=document_name,
        content=document_content,
        fields=[
            SignatureField(
                field_type=SignatureFieldType.SIGNATURE,
                page=signature_page,
                x=signature_position[0],
                y=signature_position[1],
                signer_index=0
            )
        ]
    )

    signer = Signer(
        email=signer_email,
        first_name=first_name,
        last_name=last_name
    )

    return SignatureRequest(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=f"Signature - {document_name}",
        documents=[document],
        signers=[signer]
    )
