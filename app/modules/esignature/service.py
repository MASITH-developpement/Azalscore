"""
AZALS - Module Signature Électronique - Service
================================================
Service de gestion des signatures électroniques avec multi-providers.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.encryption import decrypt_value, encrypt_value

from .models import (
    SignatureLog,
    SignatureProvider,
    SignatureRequest,
    SignatureRequestSigner,
    SignatureStatus,
    SignerStatus,
)
from .schemas import (
    SignatureRequestCreate,
    SignatureRequestListResponse,
    SignatureRequestResponse,
    SignatureRequestUpdate,
    SignatureStats,
    SignerCreate,
    SignerResponse,
)

logger = logging.getLogger(__name__)


class ESignatureService:
    """Service pour la gestion des signatures électroniques."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # =========================================================================
    # CRÉATION DEMANDE SIGNATURE
    # =========================================================================

    def create_request(self, data: SignatureRequestCreate) -> SignatureRequest:
        """
        Crée une nouvelle demande de signature.
        
        Args:
            data: Données de la demande
            
        Returns:
            Demande de signature créée
        """
        # Créer la demande
        request = SignatureRequest(
            tenant_id=self.tenant_id,
            document_type=data.document_type,
            document_id=data.document_id,
            document_number=data.document_number,
            provider=data.provider,
            title=data.title,
            message=data.message,
            document_url=data.document_url,
            expires_at=data.expires_at,
            send_reminders=data.send_reminders,
            webhook_url=data.webhook_url,
            metadata=data.metadata,
            created_by=self.user_id,
            status=SignatureStatus.DRAFT
        )
        
        self.db.add(request)
        self.db.flush()
        
        # Créer les signataires
        for signer_data in data.signers:
            signer = SignatureRequestSigner(
                request_id=request.id,
                tenant_id=self.tenant_id,
                email=signer_data.email,
                first_name=signer_data.first_name,
                last_name=signer_data.last_name,
                phone=signer_data.phone,
                signing_order=signer_data.signing_order,
                status=SignerStatus.PENDING
            )
            self.db.add(signer)
        
        # Log création
        self._log_event(
            request_id=request.id,
            event_type="request_created",
            description=f"Demande de signature créée pour {data.document_type} #{data.document_number}"
        )
        
        self.db.commit()
        self.db.refresh(request)
        
        return request

    def get_request(self, request_id: str) -> Optional[SignatureRequest]:
        """Récupère une demande de signature."""
        return self.db.query(SignatureRequest).filter(
            and_(
                SignatureRequest.id == request_id,
                SignatureRequest.tenant_id == self.tenant_id
            )
        ).options(
            joinedload(SignatureRequest.signers)
        ).first()

    def list_requests(
        self,
        status: Optional[SignatureStatus] = None,
        document_type: Optional[str] = None,
        document_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> SignatureRequestListResponse:
        """Liste les demandes de signature avec filtres."""
        query = self.db.query(SignatureRequest).filter(
            SignatureRequest.tenant_id == self.tenant_id
        )
        
        # Filtres
        if status:
            query = query.filter(SignatureRequest.status == status)
        if document_type:
            query = query.filter(SignatureRequest.document_type == document_type)
        if document_id:
            query = query.filter(SignatureRequest.document_id == document_id)
        
        # Pagination
        total = query.count()
        requests = query.order_by(SignatureRequest.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return SignatureRequestListResponse(
            requests=[SignatureRequestResponse.model_validate(r) for r in requests],
            total=total,
            page=page,
            page_size=page_size
        )

    def update_request(
        self,
        request_id: str,
        data: SignatureRequestUpdate
    ) -> Optional[SignatureRequest]:
        """Met à jour une demande de signature."""
        request = self.get_request(request_id)
        if not request:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(request, field, value)
        
        request.updated_at = datetime.utcnow()
        
        self._log_event(
            request_id=request.id,
            event_type="request_updated",
            description="Demande de signature mise à jour",
            metadata=update_data
        )
        
        self.db.commit()
        self.db.refresh(request)
        
        return request

    # =========================================================================
    # ENVOI ET SIGNATURE
    # =========================================================================

    def send_request(self, request_id: str, notify_signers: bool = True) -> Optional[SignatureRequest]:
        """
        Envoie une demande de signature aux signataires.
        
        Cette méthode délègue au provider configuré (Yousign, DocuSign, etc.)
        pour créer la demande chez le fournisseur et envoyer les emails.
        
        Args:
            request_id: ID de la demande
            notify_signers: Envoyer notification par email
            
        Returns:
            Demande mise à jour ou None
        """
        request = self.get_request(request_id)
        if not request:
            return None
        
        if request.status != SignatureStatus.DRAFT:
            logger.warning(f"Cannot send request {request_id} - not in DRAFT status")
            return None
        
        try:
            # Récupérer le provider
            provider = self._get_provider(request.provider)
            
            # Créer la demande chez le provider
            provider_data = provider.create_signature_request(
                request=request,
                notify_signers=notify_signers
            )
            
            # Mettre à jour avec les données du provider
            request.provider_request_id = provider_data.get("request_id")
            request.status = SignatureStatus.PENDING
            request.sent_at = datetime.utcnow()
            
            # Mettre à jour les signataires
            for signer in request.signers:
                signer_data = provider_data.get("signers", {}).get(signer.email)
                if signer_data:
                    signer.provider_signer_id = signer_data.get("signer_id")
                    signer.signature_url = signer_data.get("signature_url")
                    signer.status = SignerStatus.NOTIFIED if notify_signers else SignerStatus.PENDING
                    if notify_signers:
                        signer.notified_at = datetime.utcnow()
            
            self._log_event(
                request_id=request.id,
                event_type="request_sent",
                description=f"Demande envoyée via {request.provider}",
                metadata={"provider_request_id": request.provider_request_id}
            )
            
            self.db.commit()
            self.db.refresh(request)
            
            return request
            
        except Exception as e:
            logger.error(f"Error sending signature request {request_id}: {str(e)}")
            request.status = SignatureStatus.ERROR
            self._log_event(
                request_id=request.id,
                event_type="request_error",
                description=f"Erreur lors de l'envoi: {str(e)}"
            )
            self.db.commit()
            return None

    def cancel_request(self, request_id: str, reason: str = None) -> Optional[SignatureRequest]:
        """Annule une demande de signature."""
        request = self.get_request(request_id)
        if not request:
            return None
        
        if request.status in [SignatureStatus.SIGNED, SignatureStatus.CANCELLED]:
            return None
        
        try:
            # Annuler chez le provider si envoyé
            if request.provider_request_id:
                provider = self._get_provider(request.provider)
                provider.cancel_signature_request(request.provider_request_id)
            
            request.status = SignatureStatus.CANCELLED
            
            # Mettre à jour les signataires non signés
            for signer in request.signers:
                if signer.status not in [SignerStatus.SIGNED, SignerStatus.DECLINED]:
                    signer.status = SignerStatus.DECLINED
                    signer.decline_reason = reason or "Demande annulée"
            
            self._log_event(
                request_id=request.id,
                event_type="request_cancelled",
                description=f"Demande annulée: {reason or 'Non spécifié'}"
            )
            
            self.db.commit()
            self.db.refresh(request)
            
            return request
            
        except Exception as e:
            logger.error(f"Error cancelling request {request_id}: {str(e)}")
            return None

    # =========================================================================
    # WEBHOOKS ET CALLBACKS
    # =========================================================================

    def handle_webhook(
        self,
        provider: SignatureProvider,
        event_data: dict
    ) -> bool:
        """
        Traite un événement webhook du provider.
        
        Args:
            provider: Provider source
            event_data: Données de l'événement
            
        Returns:
            True si traité avec succès
        """
        try:
            provider_service = self._get_provider(provider)
            result = provider_service.handle_webhook(event_data)
            
            if result:
                # Récupérer la demande mise à jour
                request = self.db.query(SignatureRequest).filter(
                    SignatureRequest.provider_request_id == result.get("request_id")
                ).first()
                
                if request:
                    self._update_request_from_webhook(request, result)
                    
            return True
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return False

    def _update_request_from_webhook(self, request: SignatureRequest, data: dict):
        """Met à jour une demande à partir d'un webhook."""
        event_type = data.get("event_type")
        
        # Mettre à jour le statut de la demande
        if "status" in data:
            request.status = data["status"]
        
        # Mettre à jour les signataires
        if "signer_email" in data:
            signer = self.db.query(SignatureRequestSigner).filter(
                and_(
                    SignatureRequestSigner.request_id == request.id,
                    SignatureRequestSigner.email == data["signer_email"]
                )
            ).first()
            
            if signer:
                if event_type == "signer_viewed":
                    signer.status = SignerStatus.VIEWED
                    signer.viewed_at = datetime.utcnow()
                elif event_type == "signer_signed":
                    signer.status = SignerStatus.SIGNED
                    signer.signed_at = datetime.utcnow()
                elif event_type == "signer_declined":
                    signer.status = SignerStatus.DECLINED
                    signer.declined_at = datetime.utcnow()
                    signer.decline_reason = data.get("reason")
        
        # Si tous signés, marquer comme complet
        if request.status == SignatureStatus.SIGNED:
            request.completed_at = datetime.utcnow()
            if "signed_document_url" in data:
                request.signed_document_url = data["signed_document_url"]
        
        self._log_event(
            request_id=request.id,
            event_type=event_type,
            event_source="webhook",
            description=data.get("description", "Événement webhook"),
            metadata=data,
            signer_email=data.get("signer_email")
        )
        
        self.db.commit()

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_stats(self) -> SignatureStats:
        """Récupère les statistiques de signature."""
        query = self.db.query(SignatureRequest).filter(
            SignatureRequest.tenant_id == self.tenant_id
        )
        
        total = query.count()
        pending = query.filter(SignatureRequest.status == SignatureStatus.PENDING).count()
        signed = query.filter(SignatureRequest.status == SignatureStatus.SIGNED).count()
        declined = query.filter(SignatureRequest.status == SignatureStatus.DECLINED).count()
        expired = query.filter(SignatureRequest.status == SignatureStatus.EXPIRED).count()
        
        # Calculer temps moyen de signature
        avg_time = self.db.query(
            func.avg(
                func.extract('epoch', SignatureRequest.completed_at - SignatureRequest.sent_at) / 3600
            )
        ).filter(
            and_(
                SignatureRequest.tenant_id == self.tenant_id,
                SignatureRequest.status == SignatureStatus.SIGNED,
                SignatureRequest.completed_at.isnot(None),
                SignatureRequest.sent_at.isnot(None)
            )
        ).scalar()
        
        # Stats signataires
        signer_query = self.db.query(SignatureRequestSigner).filter(
            SignatureRequestSigner.tenant_id == self.tenant_id
        )
        total_signers = signer_query.count()
        signed_signers = signer_query.filter(
            SignatureRequestSigner.status == SignerStatus.SIGNED
        ).count()
        
        return SignatureStats(
            total_requests=total,
            pending_requests=pending,
            signed_requests=signed,
            declined_requests=declined,
            expired_requests=expired,
            average_signature_time_hours=float(avg_time) if avg_time else None,
            total_signers=total_signers,
            signed_signers=signed_signers
        )

    # =========================================================================
    # HELPERS PRIVÉS
    # =========================================================================

    def _get_provider(self, provider: SignatureProvider):
        """Récupère une instance du provider configuré."""
        if provider == SignatureProvider.YOUSIGN:
            from .providers.yousign import YousignProvider
            return YousignProvider(self.db, self.tenant_id)
        elif provider == SignatureProvider.DOCUSIGN:
            from .providers.docusign import DocuSignProvider
            return DocuSignProvider(self.db, self.tenant_id)
        else:
            raise ValueError(f"Provider non supporté: {provider}")

    def _log_event(
        self,
        request_id: str,
        event_type: str,
        description: str = None,
        event_source: str = "api",
        metadata: dict = None,
        signer_email: str = None
    ):
        """Enregistre un événement dans le journal d'audit."""
        log = SignatureLog(
            request_id=request_id,
            tenant_id=self.tenant_id,
            event_type=event_type,
            event_source=event_source,
            description=description,
            metadata=metadata or {},
            user_id=self.user_id,
            signer_email=signer_email
        )
        self.db.add(log)
