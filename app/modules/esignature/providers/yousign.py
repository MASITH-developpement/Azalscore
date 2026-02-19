"""
AZALS - Provider Yousign pour Signature Électronique
====================================================
Intégration avec l'API Yousign pour signatures électroniques conformes eIDAS.
"""

import logging
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value

from ..models import SignatureRequest

logger = logging.getLogger(__name__)


class YousignProvider:
    """
    Provider Yousign pour signatures électroniques.
    
    Yousign est un service français de signature électronique conforme eIDAS,
    particulièrement adapté pour les entreprises françaises et européennes.
    
    Documentation: https://dev.yousign.com/
    """
    
    API_BASE_URL = "https://api.yousign.com/v3"
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._api_key = None
        
    def _get_api_key(self) -> Optional[str]:
        """Récupère la clé API Yousign depuis la configuration tenant."""
        if self._api_key:
            return self._api_key
            
        # TODO: Récupérer depuis tenant.settings['esignature']['yousign_api_key']
        # from app.modules.tenants.models import Tenant
        # tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        # if tenant and tenant.settings:
        #     encrypted_key = tenant.settings.get('esignature', {}).get('yousign_api_key')
        #     if encrypted_key:
        #         self._api_key = decrypt_value(encrypted_key)
        
        return self._api_key
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None
    ) -> dict:
        """Fait une requête HTTP vers l'API Yousign."""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("Yousign API key not configured for tenant")
        
        url = f"{self.API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client() as client:
                response = client.request(method, url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Yousign API error: {str(e)}")
            raise
    
    def create_signature_request(
        self,
        request: SignatureRequest,
        notify_signers: bool = True
    ) -> dict:
        """
        Crée une demande de signature sur Yousign.
        
        Args:
            request: Demande de signature AzalScore
            notify_signers: Envoyer notifications par email
            
        Returns:
            Dict contenant request_id et informations signataires
        """
        # Préparer les données pour Yousign
        yousign_data = {
            "name": request.title,
            "description": request.message or "",
            "workspace_id": None,  # TODO: Récupérer depuis config
            "timezone": "Europe/Paris",
            "email_notification": {
                "sender": {
                    "email": "noreply@azalscore.com",  # TODO: Config
                    "name": "AzalScore"
                },
                "subject": request.title,
                "message": request.message or ""
            },
            "signers": [],
            "documents": []
        }
        
        # Ajouter les signataires
        for signer in request.signers:
            yousign_data["signers"].append({
                "info": {
                    "first_name": signer.first_name,
                    "last_name": signer.last_name,
                    "email": signer.email,
                    "phone_number": signer.phone
                },
                "signature_level": "electronic_signature",  # ou "advanced_electronic_signature"
                "signature_authentication_mode": "no_otp",  # ou "otp_sms", "otp_email"
            })
        
        # Ajouter le document
        if request.document_url:
            yousign_data["documents"].append({
                "nature": "signable_document",
                "file": request.document_url,  # Base64 ou URL
            })
        
        # Créer la signature request sur Yousign
        # response = self._make_request("POST", "/signature_requests", yousign_data)
        
        # Pour l'instant, retourner un mock
        logger.warning("Yousign integration not fully implemented - using mock data")
        return {
            "request_id": f"yousign_mock_{request.id}",
            "signers": {
                signer.email: {
                    "signer_id": f"signer_mock_{signer.id}",
                    "signature_url": f"https://app.yousign.com/signature/mock/{signer.id}"
                }
                for signer in request.signers
            }
        }
    
    def get_signature_request(self, provider_request_id: str) -> dict:
        """Récupère le statut d'une demande de signature."""
        # response = self._make_request("GET", f"/signature_requests/{provider_request_id}")
        # return response
        
        logger.warning("Yousign get_signature_request not implemented")
        return {}
    
    def cancel_signature_request(self, provider_request_id: str) -> bool:
        """Annule une demande de signature."""
        # self._make_request("POST", f"/signature_requests/{provider_request_id}/cancel")
        # return True
        
        logger.warning("Yousign cancel_signature_request not implemented")
        return True
    
    def handle_webhook(self, event_data: dict) -> dict:
        """
        Traite un webhook Yousign.
        
        Args:
            event_data: Données de l'événement webhook
            
        Returns:
            Dict avec informations normalisées pour AzalScore
        """
        event_name = event_data.get("event_name")
        signature_request_id = event_data.get("signature_request", {}).get("id")
        
        result = {
            "request_id": signature_request_id,
            "event_type": self._normalize_event_type(event_name),
            "description": event_name
        }
        
        # Mapper les événements Yousign vers AzalScore
        if event_name == "signature_request.done":
            result["status"] = "SIGNED"
            result["signed_document_url"] = event_data.get("signature_request", {}).get("signed_document_url")
        elif event_name == "signature_request.declined":
            result["status"] = "DECLINED"
        elif event_name == "signature_request.expired":
            result["status"] = "EXPIRED"
        elif "signer" in event_name:
            signer_data = event_data.get("signer", {})
            result["signer_email"] = signer_data.get("info", {}).get("email")
            
            if event_name == "signer.signed":
                result["event_type"] = "signer_signed"
            elif event_name == "signer.viewed":
                result["event_type"] = "signer_viewed"
            elif event_name == "signer.declined":
                result["event_type"] = "signer_declined"
                result["reason"] = signer_data.get("decline_reason")
        
        return result
    
    def _normalize_event_type(self, yousign_event: str) -> str:
        """Normalise le nom d'événement Yousign vers AzalScore."""
        event_map = {
            "signature_request.done": "request_completed",
            "signature_request.declined": "request_declined",
            "signature_request.expired": "request_expired",
            "signer.signed": "signer_signed",
            "signer.viewed": "signer_viewed",
            "signer.declined": "signer_declined",
        }
        return event_map.get(yousign_event, yousign_event)
