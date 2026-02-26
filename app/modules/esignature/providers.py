"""
AZALS MODULE ESIGNATURE - Providers externes
=============================================

Integration avec les providers de signature electronique:
- Yousign (leader francais, eIDAS compliant)
- DocuSign (leader mondial)
- HelloSign (Dropbox Sign)
- Adobe Sign

Architecture: Interface commune + implementations specifiques.
"""
from __future__ import annotations


import base64
import hashlib
import hmac
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from .models import SignatureProvider, SignatureLevel, FieldType


# =============================================================================
# DATA CLASSES POUR PROVIDERS
# =============================================================================

@dataclass
class ProviderSignerInfo:
    """Information signataire pour provider."""
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    order: int = 1
    signature_level: SignatureLevel = SignatureLevel.SIMPLE
    require_id_verification: bool = False
    require_sms_otp: bool = False
    external_id: Optional[str] = None


@dataclass
class ProviderFieldInfo:
    """Information champ pour provider."""
    field_type: FieldType
    page: int
    x: float
    y: float
    width: float = 150
    height: float = 50
    required: bool = True
    signer_index: int = 0
    label: Optional[str] = None


@dataclass
class ProviderDocumentInfo:
    """Information document pour provider."""
    name: str
    content: bytes
    fields: List[ProviderFieldInfo] = field(default_factory=list)
    external_id: Optional[str] = None

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass
class ProviderEnvelopeInfo:
    """Information enveloppe pour provider."""
    name: str
    documents: List[ProviderDocumentInfo]
    signers: List[ProviderSignerInfo]
    signature_level: SignatureLevel = SignatureLevel.SIMPLE
    expires_at: Optional[datetime] = None
    email_subject: Optional[str] = None
    email_message: Optional[str] = None
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    external_id: Optional[str] = None


@dataclass
class ProviderStatusInfo:
    """Information statut retournee par provider."""
    external_id: str
    status: str  # Statut specifique provider
    signers_status: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookEventInfo:
    """Evenement webhook parse."""
    provider: SignatureProvider
    event_type: str
    envelope_external_id: str
    signer_external_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_payload: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# INTERFACE PROVIDER
# =============================================================================

class SignatureProviderInterface(ABC):
    """Interface commune pour tous les providers de signature."""

    provider: SignatureProvider

    @abstractmethod
    async def create_envelope(self, envelope: ProviderEnvelopeInfo) -> str:
        """Cree une enveloppe chez le provider. Retourne l'ID externe."""
        pass

    @abstractmethod
    async def send_envelope(self, external_id: str) -> bool:
        """Envoie l'enveloppe aux signataires."""
        pass

    @abstractmethod
    async def get_status(self, external_id: str) -> ProviderStatusInfo:
        """Recupere le statut d'une enveloppe."""
        pass

    @abstractmethod
    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        """Telecharge le document signe."""
        pass

    @abstractmethod
    async def download_audit_trail(self, external_id: str) -> bytes:
        """Telecharge la preuve de signature (audit trail PDF)."""
        pass

    @abstractmethod
    async def cancel_envelope(self, external_id: str, reason: str = None) -> bool:
        """Annule une enveloppe."""
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
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verifie la signature d'un webhook."""
        pass

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookEventInfo:
        """Parse un webhook entrant."""
        pass

    @abstractmethod
    async def verify_credentials(self) -> bool:
        """Verifie que les credentials sont valides."""
        pass


# =============================================================================
# PROVIDER YOUSIGN
# =============================================================================

class YousignProvider(SignatureProviderInterface):
    """
    Provider Yousign - Leader francais de la signature electronique.

    Conforme eIDAS, serveurs en France.
    Documentation: https://developers.yousign.com/
    """

    provider = SignatureProvider.YOUSIGN

    def __init__(
        self,
        api_key: str,
        environment: str = "production",
        webhook_secret: Optional[str] = None
    ):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.environment = environment

        if environment == "sandbox":
            self.base_url = "https://api-sandbox.yousign.app/v3"
        else:
            self.base_url = "https://api.yousign.app/v3"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _http_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        files: Dict = None
    ) -> Dict[str, Any]:
        """Execute une requete HTTP vers Yousign."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                if files:
                    # Multipart pour upload fichiers
                    del headers["Content-Type"]
                    response = await client.post(url, headers=headers, files=files, data=data)
                else:
                    response = await client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Methode HTTP non supportee: {method}")

            response.raise_for_status()
            return response.json() if response.text else {}

    async def create_envelope(self, envelope: ProviderEnvelopeInfo) -> str:
        """Cree une signature request Yousign."""
        # 1. Creer la signature request
        payload = {
            "name": envelope.name,
            "delivery_mode": "email",
            "timezone": "Europe/Paris",
            "signers_allowed_to_decline": True
        }

        if envelope.expires_at:
            payload["expiration_date"] = envelope.expires_at.isoformat()

        if envelope.email_message:
            payload["email_custom_note"] = envelope.email_message

        if envelope.webhook_url:
            payload["webhook_url"] = envelope.webhook_url

        if envelope.extra_data:
            payload["external_id"] = envelope.extra_data.get("envelope_id", "")

        result = await self._http_request("POST", "/signature_requests", payload)
        external_id = result["id"]

        # 2. Upload des documents
        for doc in envelope.documents:
            doc_result = await self._http_request(
                "POST",
                f"/signature_requests/{external_id}/documents",
                data={"nature": "signable_document"},
                files={"file": (doc.name, doc.content, "application/pdf")}
            )
            doc.external_id = doc_result["id"]

        # 3. Ajouter les signataires
        for i, signer in enumerate(envelope.signers):
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

            signer_result = await self._http_request(
                "POST",
                f"/signature_requests/{external_id}/signers",
                signer_payload
            )
            signer.external_id = signer_result["id"]

            # 4. Ajouter les champs pour ce signataire
            for doc in envelope.documents:
                for field in doc.fields:
                    if field.signer_index == i:
                        field_payload = {
                            "document_id": doc.external_id,
                            "type": self._map_field_type(field.field_type),
                            "page": field.page,
                            "x": int(field.x),
                            "y": int(field.y),
                            "width": int(field.width),
                            "height": int(field.height)
                        }
                        await self._http_request(
                            "POST",
                            f"/signature_requests/{external_id}/signers/{signer.external_id}/fields",
                            field_payload
                        )

        return external_id

    def _map_signature_level(self, level: SignatureLevel) -> str:
        mapping = {
            SignatureLevel.SIMPLE: "electronic_signature",
            SignatureLevel.ADVANCED: "advanced_electronic_signature",
            SignatureLevel.QUALIFIED: "qualified_electronic_signature"
        }
        return mapping.get(level, "electronic_signature")

    def _get_auth_mode(self, signer: ProviderSignerInfo) -> str:
        if signer.require_id_verification:
            return "id_document"
        elif signer.require_sms_otp:
            return "otp_sms"
        return "no_otp"

    def _map_field_type(self, field_type: FieldType) -> str:
        mapping = {
            FieldType.SIGNATURE: "signature",
            FieldType.INITIALS: "initials",
            FieldType.DATE: "date",
            FieldType.TEXT: "text",
            FieldType.CHECKBOX: "checkbox"
        }
        return mapping.get(field_type, "signature")

    async def send_envelope(self, external_id: str) -> bool:
        await self._http_request("POST", f"/signature_requests/{external_id}/activate", {})
        return True

    async def get_status(self, external_id: str) -> ProviderStatusInfo:
        result = await self._http_request("GET", f"/signature_requests/{external_id}")

        signers_status = []
        for signer in result.get("signers", []):
            signers_status.append({
                "external_id": signer["id"],
                "status": signer["status"],
                "signed_at": signer.get("signature_date")
            })

        return ProviderStatusInfo(
            external_id=external_id,
            status=result.get("status", "unknown"),
            signers_status=signers_status,
            raw_data=result
        )

    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        url = f"{self.base_url}/signature_requests/{external_id}/documents/{document_external_id}/download"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.content

    async def download_audit_trail(self, external_id: str) -> bytes:
        url = f"{self.base_url}/signature_requests/{external_id}/audit_trails/download"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.content

    async def cancel_envelope(self, external_id: str, reason: str = None) -> bool:
        payload = {"reason": reason or "Cancelled by user"}
        await self._http_request("POST", f"/signature_requests/{external_id}/cancel", payload)
        return True

    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        if signer_external_id:
            await self._http_request(
                "POST",
                f"/signature_requests/{external_id}/signers/{signer_external_id}/send_reminder",
                {}
            )
        else:
            await self._http_request("POST", f"/signature_requests/{external_id}/reminders", {})
        return True

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            return True  # Pas de verification si pas de secret

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookEventInfo:
        event_type = payload.get("event_name", "unknown")
        data = payload.get("data", {})

        return WebhookEventInfo(
            provider=SignatureProvider.YOUSIGN,
            event_type=event_type,
            envelope_external_id=data.get("signature_request", {}).get("id", ""),
            signer_external_id=data.get("signer", {}).get("id"),
            raw_payload=payload
        )

    async def verify_credentials(self) -> bool:
        try:
            await self._http_request("GET", "/signature_requests?limit=1")
            return True
        except Exception:
            return False


# =============================================================================
# PROVIDER DOCUSIGN
# =============================================================================

class DocuSignProvider(SignatureProviderInterface):
    """
    Provider DocuSign - Leader mondial de la signature electronique.

    Documentation: https://developers.docusign.com/
    """

    provider = SignatureProvider.DOCUSIGN

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
        self.environment = environment

        if environment == "demo":
            self.base_url = "https://demo.docusign.net/restapi/v2.1"
            self.auth_url = "https://account-d.docusign.com"
        else:
            self.base_url = "https://eu.docusign.net/restapi/v2.1"
            self.auth_url = "https://account.docusign.com"

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _ensure_token(self):
        """S'assure qu'un token valide est disponible (JWT Grant)."""
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at - timedelta(minutes=5):
                return

        # Implementation JWT Grant simplifiee
        # En production, utiliser une librairie JWT comme PyJWT
        try:
            import jwt
            now = datetime.utcnow()
            claims = {
                "iss": self.integration_key,
                "sub": self.user_id,
                "aud": self.auth_url,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(hours=1)).timestamp()),
                "scope": "signature impersonation"
            }
            jwt_token = jwt.encode(claims, self.private_key, algorithm="RS256")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.auth_url}/oauth/token",
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                        "assertion": jwt_token
                    }
                )
                response.raise_for_status()
                token_data = response.json()
                self._access_token = token_data["access_token"]
                self._token_expires_at = now + timedelta(seconds=token_data.get("expires_in", 3600))
        except ImportError:
            # Fallback si jwt non installe
            self._access_token = "mock_token"
            self._token_expires_at = datetime.utcnow() + timedelta(hours=1)

    async def _http_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None
    ) -> Dict[str, Any]:
        await self._ensure_token()

        url = f"{self.base_url}/accounts/{self.account_id}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Methode non supportee: {method}")

            response.raise_for_status()
            return response.json() if response.text else {}

    async def create_envelope(self, envelope: ProviderEnvelopeInfo) -> str:
        # Construction de l'enveloppe DocuSign
        envelope_definition = {
            "emailSubject": envelope.email_subject or f"Signature required: {envelope.name}",
            "status": "created",
            "documents": [],
            "recipients": {"signers": []}
        }

        # Documents
        for i, doc in enumerate(envelope.documents):
            envelope_definition["documents"].append({
                "documentId": str(i + 1),
                "name": doc.name,
                "documentBase64": base64.b64encode(doc.content).decode(),
                "fileExtension": "pdf"
            })

        # Signataires
        for i, signer in enumerate(envelope.signers):
            signer_def = {
                "recipientId": str(i + 1),
                "routingOrder": str(signer.order),
                "email": signer.email,
                "name": f"{signer.first_name} {signer.last_name}",
                "tabs": self._build_tabs(envelope.documents, i)
            }

            if signer.require_sms_otp and signer.phone:
                signer_def["phoneAuthentication"] = {
                    "recipMayProvideNumber": False,
                    "senderProvidedNumbers": [signer.phone]
                }

            envelope_definition["recipients"]["signers"].append(signer_def)

        if envelope.email_message:
            envelope_definition["emailBlurb"] = envelope.email_message

        result = await self._http_request("POST", "/envelopes", envelope_definition)
        return result["envelopeId"]

    def _build_tabs(
        self,
        documents: List[ProviderDocumentInfo],
        signer_index: int
    ) -> Dict[str, List[Dict]]:
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

                if field.field_type == FieldType.SIGNATURE:
                    tabs["signHereTabs"].append(tab_data)
                elif field.field_type == FieldType.INITIALS:
                    tabs["initialHereTabs"].append(tab_data)
                elif field.field_type == FieldType.DATE:
                    tabs["dateSignedTabs"].append(tab_data)
                elif field.field_type == FieldType.TEXT:
                    tab_data["width"] = int(field.width)
                    tabs["textTabs"].append(tab_data)
                elif field.field_type == FieldType.CHECKBOX:
                    tabs["checkboxTabs"].append(tab_data)

        return tabs

    async def send_envelope(self, external_id: str) -> bool:
        await self._http_request("PUT", f"/envelopes/{external_id}", {"status": "sent"})
        return True

    async def get_status(self, external_id: str) -> ProviderStatusInfo:
        result = await self._http_request("GET", f"/envelopes/{external_id}")

        signers_status = []
        recipients = result.get("recipients", {}).get("signers", [])
        for signer in recipients:
            signers_status.append({
                "external_id": signer.get("recipientId"),
                "status": signer.get("status"),
                "signed_at": signer.get("signedDateTime")
            })

        return ProviderStatusInfo(
            external_id=external_id,
            status=result.get("status", "unknown"),
            signers_status=signers_status,
            completed_at=datetime.fromisoformat(result["completedDateTime"]) if result.get("completedDateTime") else None,
            raw_data=result
        )

    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        await self._ensure_token()
        url = f"{self.base_url}/accounts/{self.account_id}/envelopes/{external_id}/documents/{document_external_id}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {self._access_token}"}
            )
            response.raise_for_status()
            return response.content

    async def download_audit_trail(self, external_id: str) -> bytes:
        await self._ensure_token()
        url = f"{self.base_url}/accounts/{self.account_id}/envelopes/{external_id}/documents/certificate"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {self._access_token}"}
            )
            response.raise_for_status()
            return response.content

    async def cancel_envelope(self, external_id: str, reason: str = None) -> bool:
        await self._http_request(
            "PUT",
            f"/envelopes/{external_id}",
            {"status": "voided", "voidedReason": reason or "Cancelled"}
        )
        return True

    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        await self._http_request(
            "PUT",
            f"/envelopes/{external_id}/recipients",
            {"resend_envelope": True}
        )
        return True

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            return True

        computed = base64.b64encode(
            hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).digest()
        ).decode()
        return hmac.compare_digest(signature, computed)

    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookEventInfo:
        envelope_status = payload.get("envelopeStatus", {})

        return WebhookEventInfo(
            provider=SignatureProvider.DOCUSIGN,
            event_type=envelope_status.get("status", "unknown"),
            envelope_external_id=envelope_status.get("envelopeId", ""),
            raw_payload=payload
        )

    async def verify_credentials(self) -> bool:
        try:
            await self._ensure_token()
            await self._http_request("GET", "/envelopes?count=1")
            return True
        except Exception:
            return False


# =============================================================================
# PROVIDER HELLOSIGN
# =============================================================================

class HelloSignProvider(SignatureProviderInterface):
    """
    Provider HelloSign (Dropbox Sign).

    Documentation: https://developers.hellosign.com/
    """

    provider = SignatureProvider.HELLOSIGN

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

    async def _http_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        files: Dict = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        auth = (self.api_key, "")

        async with httpx.AsyncClient(timeout=30.0, auth=auth) as client:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                if files:
                    response = await client.post(url, data=data, files=files)
                else:
                    response = await client.post(url, json=data)
            else:
                raise ValueError(f"Methode non supportee: {method}")

            response.raise_for_status()
            return response.json() if response.text else {}

    async def create_envelope(self, envelope: ProviderEnvelopeInfo) -> str:
        form_data = {
            "title": envelope.name,
            "subject": envelope.email_subject or f"Signature required: {envelope.name}",
            "message": envelope.email_message or "Please sign this document.",
            "test_mode": 0
        }

        # Signataires
        for i, signer in enumerate(envelope.signers):
            form_data[f"signers[{i}][email_address]"] = signer.email
            form_data[f"signers[{i}][name]"] = f"{signer.first_name} {signer.last_name}"
            form_data[f"signers[{i}][order]"] = signer.order

        # Documents
        files = {}
        for i, doc in enumerate(envelope.documents):
            files[f"file[{i}]"] = (doc.name, doc.content, "application/pdf")

        result = await self._http_request("POST", "/signature_request/send", form_data, files)
        return result.get("signature_request", {}).get("signature_request_id", "")

    async def send_envelope(self, external_id: str) -> bool:
        # HelloSign envoie automatiquement a la creation
        return True

    async def get_status(self, external_id: str) -> ProviderStatusInfo:
        result = await self._http_request("GET", f"/signature_request/{external_id}")
        sr = result.get("signature_request", {})

        signers_status = []
        for sig in sr.get("signatures", []):
            signers_status.append({
                "external_id": sig.get("signature_id"),
                "status": "signed" if sig.get("status_code") == "signed" else "pending",
                "signed_at": sig.get("signed_at")
            })

        status = "completed" if sr.get("is_complete") else "in_progress"
        if sr.get("is_declined"):
            status = "declined"

        return ProviderStatusInfo(
            external_id=external_id,
            status=status,
            signers_status=signers_status,
            raw_data=result
        )

    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        url = f"{self.base_url}/signature_request/files/{external_id}"
        auth = (self.api_key, "")
        async with httpx.AsyncClient(timeout=60.0, auth=auth) as client:
            response = await client.get(url, params={"file_type": "pdf"})
            response.raise_for_status()
            return response.content

    async def download_audit_trail(self, external_id: str) -> bytes:
        # HelloSign inclut l'audit trail dans le document signe
        return await self.download_signed_document(external_id, "1")

    async def cancel_envelope(self, external_id: str, reason: str = None) -> bool:
        await self._http_request("POST", f"/signature_request/cancel/{external_id}", {})
        return True

    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        data = {}
        if signer_external_id:
            data["email_address"] = signer_external_id
        await self._http_request("POST", f"/signature_request/remind/{external_id}", data)
        return True

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            return True

        computed = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, computed)

    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookEventInfo:
        event = payload.get("event", {})
        sr = payload.get("signature_request", {})

        return WebhookEventInfo(
            provider=SignatureProvider.HELLOSIGN,
            event_type=event.get("event_type", "unknown"),
            envelope_external_id=sr.get("signature_request_id", ""),
            raw_payload=payload
        )

    async def verify_credentials(self) -> bool:
        try:
            await self._http_request("GET", "/account")
            return True
        except Exception:
            return False


# =============================================================================
# PROVIDER INTERNAL (Simulation)
# =============================================================================

class InternalProvider(SignatureProviderInterface):
    """
    Provider interne AZALS pour signature simple.

    Utilise pour les tests et les signatures simples sans provider externe.
    """

    provider = SignatureProvider.INTERNAL

    def __init__(self):
        self._envelopes: Dict[str, Dict] = {}

    async def create_envelope(self, envelope: ProviderEnvelopeInfo) -> str:
        external_id = f"internal_{uuid.uuid4().hex[:16]}"
        self._envelopes[external_id] = {
            "envelope": envelope,
            "status": "created",
            "created_at": datetime.utcnow()
        }
        return external_id

    async def send_envelope(self, external_id: str) -> bool:
        if external_id in self._envelopes:
            self._envelopes[external_id]["status"] = "sent"
            return True
        return False

    async def get_status(self, external_id: str) -> ProviderStatusInfo:
        data = self._envelopes.get(external_id, {})
        return ProviderStatusInfo(
            external_id=external_id,
            status=data.get("status", "unknown"),
            raw_data=data
        )

    async def download_signed_document(
        self,
        external_id: str,
        document_external_id: str
    ) -> bytes:
        return b""  # Retourne document vide pour simulation

    async def download_audit_trail(self, external_id: str) -> bytes:
        return b""

    async def cancel_envelope(self, external_id: str, reason: str = None) -> bool:
        if external_id in self._envelopes:
            self._envelopes[external_id]["status"] = "cancelled"
            return True
        return False

    async def send_reminder(
        self,
        external_id: str,
        signer_external_id: Optional[str] = None
    ) -> bool:
        return True

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return True

    def parse_webhook(self, payload: Dict[str, Any]) -> WebhookEventInfo:
        return WebhookEventInfo(
            provider=SignatureProvider.INTERNAL,
            event_type=payload.get("event_type", "unknown"),
            envelope_external_id=payload.get("envelope_id", ""),
            raw_payload=payload
        )

    async def verify_credentials(self) -> bool:
        return True


# =============================================================================
# FACTORY
# =============================================================================

class ProviderFactory:
    """Factory pour creer les providers de signature."""

    @staticmethod
    def create(
        provider: SignatureProvider,
        credentials: Dict[str, Any]
    ) -> SignatureProviderInterface:
        """Cree une instance de provider."""

        if provider == SignatureProvider.YOUSIGN:
            return YousignProvider(
                api_key=credentials.get("api_key", ""),
                environment=credentials.get("environment", "production"),
                webhook_secret=credentials.get("webhook_secret")
            )

        elif provider == SignatureProvider.DOCUSIGN:
            return DocuSignProvider(
                integration_key=credentials.get("integration_key", ""),
                account_id=credentials.get("account_id", ""),
                user_id=credentials.get("user_id", ""),
                private_key=credentials.get("private_key", ""),
                environment=credentials.get("environment", "production"),
                webhook_secret=credentials.get("webhook_secret")
            )

        elif provider == SignatureProvider.HELLOSIGN:
            return HelloSignProvider(
                api_key=credentials.get("api_key", ""),
                client_id=credentials.get("client_id"),
                webhook_secret=credentials.get("webhook_secret")
            )

        elif provider == SignatureProvider.INTERNAL:
            return InternalProvider()

        else:
            raise ValueError(f"Provider non supporte: {provider}")
