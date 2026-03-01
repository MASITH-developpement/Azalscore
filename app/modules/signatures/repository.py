"""
AZALS MODULE SIGNATURES - Repository
======================================

Repositories SQLAlchemy pour les signatures electroniques (GAP-058).
Conforme aux normes AZALSCORE (isolation tenant, type hints).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload

from .models import (
    ProviderConfig,
    SignatureRequest,
    SignatureDocument,
    SignatureField,
    Signer,
    AuditEvent,
    InternalSignatureCertificate,
    SignatureLevel,
    SignatureProvider,
    SignatureStatus,
    SignatureRequestStatus,
    SignerRole,
    AuthenticationMethod,
    FieldType,
)


class ProviderConfigRepository:
    """Repository pour les configurations de fournisseur."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(ProviderConfig).filter(
            ProviderConfig.tenant_id == self.tenant_id
        )

    def get_by_id(self, config_id: UUID) -> Optional[ProviderConfig]:
        """Recupere une configuration par ID."""
        return self._base_query().filter(ProviderConfig.id == config_id).first()

    def get_by_provider(self, provider: SignatureProvider) -> Optional[ProviderConfig]:
        """Recupere la configuration d'un fournisseur."""
        return self._base_query().filter(
            ProviderConfig.provider == provider,
            ProviderConfig.is_active == True
        ).first()

    def get_default(self) -> Optional[ProviderConfig]:
        """Recupere la configuration par defaut."""
        return self._base_query().filter(
            ProviderConfig.is_default == True,
            ProviderConfig.is_active == True
        ).first()

    def list(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ProviderConfig], int]:
        """Liste les configurations."""
        query = self._base_query()
        if is_active is not None:
            query = query.filter(ProviderConfig.is_active == is_active)
        total = query.count()
        items = query.order_by(ProviderConfig.provider).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> ProviderConfig:
        """Cree une nouvelle configuration."""
        config = ProviderConfig(tenant_id=self.tenant_id, **data)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update(self, config: ProviderConfig, data: Dict[str, Any]) -> ProviderConfig:
        """Met a jour une configuration."""
        for key, value in data.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)
        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        return config

    def set_default(self, config: ProviderConfig) -> ProviderConfig:
        """Definit une configuration comme defaut."""
        self._base_query().filter(ProviderConfig.is_default == True).update(
            {ProviderConfig.is_default: False}
        )
        config.is_default = True
        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete(self, config: ProviderConfig) -> None:
        """Supprime une configuration."""
        self.db.delete(config)
        self.db.commit()


class SignatureRequestRepository:
    """Repository pour les demandes de signature."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(SignatureRequest).filter(
            SignatureRequest.tenant_id == self.tenant_id
        )

    def get_by_id(
        self,
        request_id: UUID,
        with_relations: bool = False
    ) -> Optional[SignatureRequest]:
        """Recupere une demande par ID."""
        query = self._base_query().filter(SignatureRequest.id == request_id)
        if with_relations:
            query = query.options(
                joinedload(SignatureRequest.documents),
                joinedload(SignatureRequest.signers)
            )
        return query.first()

    def get_by_external_id(self, external_id: str) -> Optional[SignatureRequest]:
        """Recupere une demande par ID externe."""
        return self._base_query().filter(
            SignatureRequest.external_id == external_id
        ).first()

    def list(
        self,
        status: Optional[SignatureRequestStatus] = None,
        provider: Optional[SignatureProvider] = None,
        created_by: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[SignatureRequest], int]:
        """Liste les demandes avec filtres."""
        query = self._base_query()

        if status:
            query = query.filter(SignatureRequest.status == status)
        if provider:
            query = query.filter(SignatureRequest.provider == provider)
        if created_by:
            query = query.filter(SignatureRequest.created_by == created_by)
        if date_from:
            query = query.filter(SignatureRequest.created_at >= date_from)
        if date_to:
            query = query.filter(SignatureRequest.created_at <= date_to)
        if search:
            query = query.filter(SignatureRequest.name.ilike(f"%{search}%"))

        total = query.count()
        items = query.order_by(desc(SignatureRequest.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_expiring(self, days: int = 3) -> List[SignatureRequest]:
        """Recupere les demandes qui expirent bientot."""
        cutoff = datetime.utcnow() + timedelta(days=days)
        return self._base_query().filter(
            SignatureRequest.status == SignatureRequestStatus.ACTIVE,
            SignatureRequest.expires_at <= cutoff,
            SignatureRequest.expires_at > datetime.utcnow()
        ).all()

    def get_expired(self) -> List[SignatureRequest]:
        """Recupere les demandes expirees."""
        return self._base_query().filter(
            SignatureRequest.status == SignatureRequestStatus.ACTIVE,
            SignatureRequest.expires_at <= datetime.utcnow()
        ).all()

    def create(self, data: Dict[str, Any]) -> SignatureRequest:
        """Cree une nouvelle demande."""
        request = SignatureRequest(tenant_id=self.tenant_id, **data)
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def update(self, request: SignatureRequest, data: Dict[str, Any]) -> SignatureRequest:
        """Met a jour une demande."""
        for key, value in data.items():
            if hasattr(request, key) and value is not None:
                setattr(request, key, value)
        self.db.commit()
        self.db.refresh(request)
        return request

    def activate(self, request: SignatureRequest) -> SignatureRequest:
        """Active une demande."""
        request.status = SignatureRequestStatus.ACTIVE
        self.db.commit()
        self.db.refresh(request)
        return request

    def complete(self, request: SignatureRequest) -> SignatureRequest:
        """Marque comme complete."""
        request.status = SignatureRequestStatus.COMPLETED
        request.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(request)
        return request

    def cancel(self, request: SignatureRequest) -> SignatureRequest:
        """Annule une demande."""
        request.status = SignatureRequestStatus.CANCELLED
        request.cancelled_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(request)
        return request

    def expire(self, request: SignatureRequest) -> SignatureRequest:
        """Marque comme expiree."""
        request.status = SignatureRequestStatus.EXPIRED
        self.db.commit()
        self.db.refresh(request)
        return request


class SignatureDocumentRepository:
    """Repository pour les documents de signature."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(SignatureDocument).filter(
            SignatureDocument.tenant_id == self.tenant_id
        )

    def get_by_id(self, document_id: UUID) -> Optional[SignatureDocument]:
        """Recupere un document par ID."""
        return self._base_query().filter(SignatureDocument.id == document_id).first()

    def get_by_request(self, request_id: UUID) -> List[SignatureDocument]:
        """Recupere les documents d'une demande."""
        return self._base_query().filter(
            SignatureDocument.request_id == request_id
        ).order_by(SignatureDocument.created_at).all()

    def create(self, data: Dict[str, Any]) -> SignatureDocument:
        """Cree un nouveau document."""
        document = SignatureDocument(tenant_id=self.tenant_id, **data)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: SignatureDocument, data: Dict[str, Any]) -> SignatureDocument:
        """Met a jour un document."""
        for key, value in data.items():
            if hasattr(document, key) and value is not None:
                setattr(document, key, value)
        self.db.commit()
        self.db.refresh(document)
        return document

    def set_signed(self, document: SignatureDocument, signed_path: str, signed_hash: str) -> SignatureDocument:
        """Marque comme signe."""
        document.signed_file_path = signed_path
        document.signed_file_hash = signed_hash
        self.db.commit()
        self.db.refresh(document)
        return document


class SignatureFieldRepository:
    """Repository pour les champs de signature."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(SignatureField).filter(
            SignatureField.tenant_id == self.tenant_id
        )

    def get_by_id(self, field_id: UUID) -> Optional[SignatureField]:
        """Recupere un champ par ID."""
        return self._base_query().filter(SignatureField.id == field_id).first()

    def get_by_document(self, document_id: UUID) -> List[SignatureField]:
        """Recupere les champs d'un document."""
        return self._base_query().filter(
            SignatureField.document_id == document_id
        ).order_by(SignatureField.page, SignatureField.y).all()

    def create(self, data: Dict[str, Any]) -> SignatureField:
        """Cree un nouveau champ."""
        field = SignatureField(tenant_id=self.tenant_id, **data)
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field

    def create_batch(self, fields_data: List[Dict[str, Any]]) -> List[SignatureField]:
        """Cree plusieurs champs."""
        fields = []
        for data in fields_data:
            field = SignatureField(tenant_id=self.tenant_id, **data)
            self.db.add(field)
            fields.append(field)
        self.db.commit()
        for f in fields:
            self.db.refresh(f)
        return fields

    def delete(self, field: SignatureField) -> None:
        """Supprime un champ."""
        self.db.delete(field)
        self.db.commit()


class SignerRepository:
    """Repository pour les signataires."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(Signer).filter(
            Signer.tenant_id == self.tenant_id
        )

    def get_by_id(self, signer_id: UUID) -> Optional[Signer]:
        """Recupere un signataire par ID."""
        return self._base_query().filter(Signer.id == signer_id).first()

    def get_by_request(self, request_id: UUID) -> List[Signer]:
        """Recupere les signataires d'une demande."""
        return self._base_query().filter(
            Signer.request_id == request_id
        ).order_by(Signer.order_index).all()

    def get_by_email(self, request_id: UUID, email: str) -> Optional[Signer]:
        """Recupere un signataire par email."""
        return self._base_query().filter(
            Signer.request_id == request_id,
            Signer.email == email
        ).first()

    def get_pending(self, request_id: UUID) -> List[Signer]:
        """Recupere les signataires en attente."""
        return self._base_query().filter(
            Signer.request_id == request_id,
            Signer.status.in_([SignatureStatus.PENDING, SignatureStatus.SENT, SignatureStatus.VIEWED])
        ).order_by(Signer.order_index).all()

    def create(self, data: Dict[str, Any]) -> Signer:
        """Cree un nouveau signataire."""
        signer = Signer(tenant_id=self.tenant_id, **data)
        self.db.add(signer)
        self.db.commit()
        self.db.refresh(signer)
        return signer

    def create_batch(self, signers_data: List[Dict[str, Any]]) -> List[Signer]:
        """Cree plusieurs signataires."""
        signers = []
        for data in signers_data:
            signer = Signer(tenant_id=self.tenant_id, **data)
            self.db.add(signer)
            signers.append(signer)
        self.db.commit()
        for s in signers:
            self.db.refresh(s)
        return signers

    def update(self, signer: Signer, data: Dict[str, Any]) -> Signer:
        """Met a jour un signataire."""
        for key, value in data.items():
            if hasattr(signer, key) and value is not None:
                setattr(signer, key, value)
        self.db.commit()
        self.db.refresh(signer)
        return signer

    def mark_sent(self, signer: Signer) -> Signer:
        """Marque l'invitation comme envoyee."""
        signer.status = SignatureStatus.SENT
        signer.invitation_sent_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(signer)
        return signer

    def mark_viewed(self, signer: Signer) -> Signer:
        """Marque comme vu."""
        signer.status = SignatureStatus.VIEWED
        signer.viewed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(signer)
        return signer

    def mark_signed(
        self,
        signer: Signer,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        certificate: Optional[str] = None
    ) -> Signer:
        """Marque comme signe."""
        signer.status = SignatureStatus.SIGNED
        signer.signed_at = datetime.utcnow()
        if ip:
            signer.signature_ip = ip
        if user_agent:
            signer.signature_user_agent = user_agent
        if certificate:
            signer.signature_certificate = certificate
        self.db.commit()
        self.db.refresh(signer)
        return signer

    def mark_refused(self, signer: Signer, reason: Optional[str] = None) -> Signer:
        """Marque comme refuse."""
        signer.status = SignatureStatus.REFUSED
        signer.refused_at = datetime.utcnow()
        if reason:
            signer.refusal_reason = reason
        self.db.commit()
        self.db.refresh(signer)
        return signer


class AuditEventRepository:
    """Repository pour les evenements d'audit."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(AuditEvent).filter(
            AuditEvent.tenant_id == self.tenant_id
        )

    def get_by_request(
        self,
        request_id: UUID,
        event_type: Optional[str] = None
    ) -> List[AuditEvent]:
        """Recupere les evenements d'une demande."""
        query = self._base_query().filter(AuditEvent.request_id == request_id)
        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        return query.order_by(AuditEvent.timestamp).all()

    def create(self, data: Dict[str, Any]) -> AuditEvent:
        """Cree un nouvel evenement."""
        event = AuditEvent(tenant_id=self.tenant_id, **data)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def log_event(
        self,
        request_id: UUID,
        event_type: str,
        actor_email: Optional[str] = None,
        actor_name: Optional[str] = None,
        actor_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Enregistre un evenement d'audit."""
        return self.create({
            "request_id": request_id,
            "event_type": event_type,
            "actor_email": actor_email,
            "actor_name": actor_name,
            "actor_ip": actor_ip,
            "details": details or {}
        })


class CertificateRepository:
    """Repository pour les certificats de signature."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(InternalSignatureCertificate).filter(
            InternalSignatureCertificate.tenant_id == self.tenant_id
        )

    def get_by_id(self, cert_id: UUID) -> Optional[InternalSignatureCertificate]:
        """Recupere un certificat par ID."""
        return self._base_query().filter(InternalSignatureCertificate.id == cert_id).first()

    def get_active(self) -> Optional[InternalSignatureCertificate]:
        """Recupere le certificat actif."""
        now = datetime.utcnow()
        return self._base_query().filter(
            InternalSignatureCertificate.is_active == True,
            InternalSignatureCertificate.is_revoked == False,
            InternalSignatureCertificate.valid_from <= now,
            InternalSignatureCertificate.valid_to >= now
        ).first()

    def list(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[InternalSignatureCertificate], int]:
        """Liste les certificats."""
        query = self._base_query()
        if is_active is not None:
            query = query.filter(InternalSignatureCertificate.is_active == is_active)
        total = query.count()
        items = query.order_by(desc(InternalSignatureCertificate.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_expiring(self, days: int = 30) -> List[InternalSignatureCertificate]:
        """Recupere les certificats qui expirent bientot."""
        cutoff = datetime.utcnow() + timedelta(days=days)
        return self._base_query().filter(
            InternalSignatureCertificate.is_active == True,
            InternalSignatureCertificate.is_revoked == False,
            InternalSignatureCertificate.valid_to <= cutoff
        ).all()

    def create(self, data: Dict[str, Any]) -> InternalSignatureCertificate:
        """Cree un nouveau certificat."""
        cert = InternalSignatureCertificate(tenant_id=self.tenant_id, **data)
        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def revoke(self, cert: InternalSignatureCertificate, reason: str) -> InternalSignatureCertificate:
        """Revoque un certificat."""
        cert.is_revoked = True
        cert.revoked_at = datetime.utcnow()
        cert.revocation_reason = reason
        cert.is_active = False
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def deactivate(self, cert: InternalSignatureCertificate) -> InternalSignatureCertificate:
        """Desactive un certificat."""
        cert.is_active = False
        self.db.commit()
        self.db.refresh(cert)
        return cert
