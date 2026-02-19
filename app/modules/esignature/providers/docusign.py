"""
AZALS - Provider DocuSign pour Signature Électronique
=====================================================
Intégration avec l'API DocuSign pour signatures électroniques internationales.
"""

import logging
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value

from ..models import SignatureRequest

logger = logging.getLogger(__name__)


class DocuSignProvider:
    """
    Provider DocuSign pour signatures électroniques.
    
    DocuSign est un leader international de la signature électronique,
    particulièrement adapté pour les entreprises avec présence mondiale.
    
    Documentation: https://developers.docusign.com/
    """
    
    API_BASE_URL = "https://demo.docusign.net/restapi"  # Demo env
    # Production: https://na3.docusign.net/restapi (dépend de la région)
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._access_token = None
        self._account_id = None
    
    def _get_access_token(self) -> Optional[str]:
        """Récupère le token OAuth2 DocuSign."""
        if self._access_token:
            return self._access_token
        
        # TODO: Implémenter OAuth2 flow DocuSign
        # ou récupérer token JWT depuis tenant settings
        return None
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None
    ) -> dict:
        """Fait une requête HTTP vers l'API DocuSign."""
        access_token = self._get_access_token()
        if not access_token:
            raise ValueError("DocuSign access token not configured")
        
        url = f"{self.API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client() as client:
                response = client.request(method, url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"DocuSign API error: {str(e)}")
            raise
    
    def create_signature_request(
        self,
        request: SignatureRequest,
        notify_signers: bool = True
    ) -> dict:
        """
        Crée une enveloppe de signature sur DocuSign.
        
        Args:
            request: Demande de signature AzalScore
            notify_signers: Envoyer notifications par email
            
        Returns:
            Dict contenant envelope_id et informations signataires
        """
        # Préparer l'enveloppe DocuSign
        envelope_data = {
            "emailSubject": request.title,
            "emailBlurb": request.message or "",
            "status": "sent" if notify_signers else "created",
            "recipients": {
                "signers": []
            },
            "documents": []
        }
        
        # Ajouter les signataires
        for idx, signer in enumerate(request.signers, start=1):
            envelope_data["recipients"]["signers"].append({
                "email": signer.email,
                "name": f"{signer.first_name} {signer.last_name}",
                "recipientId": str(idx),
                "routingOrder": str(signer.signing_order),
                "clientUserId": None  # Pour signature embedded, sinon None
            })
        
        # Ajouter le document
        if request.document_url:
            envelope_data["documents"].append({
                "documentId": "1",
                "name": f"{request.document_type}_{request.document_number}.pdf",
                "fileExtension": "pdf",
                # "documentBase64": base64_document
            })
        
        # Créer l'enveloppe sur DocuSign
        # response = self._make_request(
        #     "POST",
        #     f"/v2.1/accounts/{self._account_id}/envelopes",
        #     envelope_data
        # )
        
        # Pour l'instant, retourner un mock
        logger.warning("DocuSign integration not fully implemented - using mock data")
        return {
            "request_id": f"docusign_mock_{request.id}",
            "signers": {
                signer.email: {
                    "signer_id": f"recipient_{idx}",
                    "signature_url": f"https://demo.docusign.net/signing/mock/{signer.id}"
                }
                for idx, signer in enumerate(request.signers, start=1)
            }
        }
    
    def get_signature_request(self, envelope_id: str) -> dict:
        """Récupère le statut d'une enveloppe."""
        # response = self._make_request(
        #     "GET",
        #     f"/v2.1/accounts/{self._account_id}/envelopes/{envelope_id}"
        # )
        # return response
        
        logger.warning("DocuSign get_signature_request not implemented")
        return {}
    
    def cancel_signature_request(self, envelope_id: str) -> bool:
        """Annule une enveloppe."""
        # self._make_request(
        #     "PUT",
        #     f"/v2.1/accounts/{self._account_id}/envelopes/{envelope_id}",
        #     {"status": "voided", "voidedReason": "Cancelled by user"}
        # )
        # return True
        
        logger.warning("DocuSign cancel_signature_request not implemented")
        return True
    
    def handle_webhook(self, event_data: dict) -> dict:
        """
        Traite un webhook DocuSign Connect.
        
        Args:
            event_data: Données de l'événement webhook
            
        Returns:
            Dict avec informations normalisées pour AzalScore
        """
        event = event_data.get("event")
        envelope_id = event_data.get("envelopeId")
        
        result = {
            "request_id": envelope_id,
            "event_type": self._normalize_event_type(event),
            "description": event
        }
        
        # Mapper les événements DocuSign vers AzalScore
        if event == "envelope-completed":
            result["status"] = "SIGNED"
        elif event == "envelope-declined":
            result["status"] = "DECLINED"
        elif event == "envelope-voided":
            result["status"] = "CANCELLED"
        elif "recipient" in event:
            recipient_data = event_data.get("recipient", {})
            result["signer_email"] = recipient_data.get("email")
            
            if event == "recipient-completed":
                result["event_type"] = "signer_signed"
            elif event == "recipient-delivered":
                result["event_type"] = "signer_viewed"
            elif event == "recipient-declined":
                result["event_type"] = "signer_declined"
                result["reason"] = recipient_data.get("declineReason")
        
        return result
    
    def _normalize_event_type(self, docusign_event: str) -> str:
        """Normalise le nom d'événement DocuSign vers AzalScore."""
        event_map = {
            "envelope-completed": "request_completed",
            "envelope-declined": "request_declined",
            "envelope-voided": "request_cancelled",
            "recipient-completed": "signer_signed",
            "recipient-delivered": "signer_viewed",
            "recipient-declined": "signer_declined",
        }
        return event_map.get(docusign_event, docusign_event)
