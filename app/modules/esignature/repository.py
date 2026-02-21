"""
AZALS MODULE ESIGNATURE - Repository
====================================

Repositories pour l'acces aux donnees avec isolation tenant.
Pattern _base_query() filtre obligatoire par tenant_id.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from .models import (
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
    EnvelopeStatus,
    SignerStatus,
    AuditEventType,
    SignatureProvider,
)
from .schemas import EnvelopeFilters, TemplateFilters


class ESignatureConfigRepository:
    """Repository pour la configuration signature."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base filtree par tenant."""
        return self.db.query(ESignatureConfig).filter(
            ESignatureConfig.tenant_id == self.tenant_id
        )

    def get(self) -> Optional[ESignatureConfig]:
        """Recupere la configuration du tenant."""
        return self._base_query().first()

    def exists(self) -> bool:
        """Verifie si la configuration existe."""
        return self._base_query().count() > 0

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ESignatureConfig:
        """Cree la configuration."""
        config = ESignatureConfig(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update(self, config: ESignatureConfig, data: Dict[str, Any], updated_by: UUID = None) -> ESignatureConfig:
        """Met a jour la configuration."""
        for key, value in data.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)
        config.updated_by = updated_by
        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        return config


class ProviderCredentialRepository:
    """Repository pour les credentials provider."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ProviderCredential).filter(
            ProviderCredential.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[ProviderCredential]:
        return self._base_query().filter(ProviderCredential.id == id).first()

    def get_by_provider(self, provider: SignatureProvider, environment: str = "production") -> Optional[ProviderCredential]:
        return self._base_query().filter(
            ProviderCredential.provider == provider,
            ProviderCredential.environment == environment
        ).first()

    def list_all(self) -> List[ProviderCredential]:
        return self._base_query().order_by(ProviderCredential.provider).all()

    def create(self, data: Dict[str, Any]) -> ProviderCredential:
        credential = ProviderCredential(tenant_id=self.tenant_id, **data)
        self.db.add(credential)
        self.db.commit()
        self.db.refresh(credential)
        return credential

    def update(self, credential: ProviderCredential, data: Dict[str, Any]) -> ProviderCredential:
        for key, value in data.items():
            if hasattr(credential, key) and value is not None:
                setattr(credential, key, value)
        credential.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(credential)
        return credential

    def delete(self, credential: ProviderCredential) -> bool:
        self.db.delete(credential)
        self.db.commit()
        return True


class SignatureTemplateRepository:
    """Repository pour les templates de signature."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(SignatureTemplate).filter(
            SignatureTemplate.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(SignatureTemplate.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[SignatureTemplate]:
        return self._base_query().options(
            joinedload(SignatureTemplate.fields)
        ).filter(SignatureTemplate.id == id).first()

    def get_by_code(self, code: str) -> Optional[SignatureTemplate]:
        return self._base_query().filter(
            SignatureTemplate.code == code.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(SignatureTemplate.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(SignatureTemplate.code == code.upper())
        if exclude_id:
            query = query.filter(SignatureTemplate.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: TemplateFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[SignatureTemplate], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    SignatureTemplate.name.ilike(term),
                    SignatureTemplate.code.ilike(term),
                    SignatureTemplate.description.ilike(term)
                ))
            if filters.category:
                query = query.filter(SignatureTemplate.category == filters.category)
            if filters.document_type:
                query = query.filter(SignatureTemplate.document_type == filters.document_type)
            if filters.is_active is not None:
                query = query.filter(SignatureTemplate.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(SignatureTemplate, sort_by, SignatureTemplate.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> SignatureTemplate:
        fields_data = data.pop("fields", [])
        template = SignatureTemplate(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(template)
        self.db.flush()

        for field_data in fields_data:
            field = TemplateField(
                tenant_id=self.tenant_id,
                template_id=template.id,
                **field_data
            )
            self.db.add(field)

        self.db.commit()
        self.db.refresh(template)
        return template

    def update(self, template: SignatureTemplate, data: Dict[str, Any], updated_by: UUID = None) -> SignatureTemplate:
        for key, value in data.items():
            if hasattr(template, key) and key != "fields" and value is not None:
                setattr(template, key, value)
        template.updated_by = updated_by
        template.updated_at = datetime.utcnow()
        template.version += 1
        self.db.commit()
        self.db.refresh(template)
        return template

    def increment_usage(self, template: SignatureTemplate) -> None:
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        self.db.commit()

    def soft_delete(self, template: SignatureTemplate, deleted_by: UUID = None) -> bool:
        template.is_deleted = True
        template.deleted_at = datetime.utcnow()
        template.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, template: SignatureTemplate) -> SignatureTemplate:
        template.is_deleted = False
        template.deleted_at = None
        template.deleted_by = None
        self.db.commit()
        self.db.refresh(template)
        return template


class SignatureEnvelopeRepository:
    """Repository pour les enveloppes de signature."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(SignatureEnvelope).filter(
            SignatureEnvelope.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(SignatureEnvelope.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[SignatureEnvelope]:
        return self._base_query().options(
            joinedload(SignatureEnvelope.documents).joinedload(EnvelopeDocument.fields),
            joinedload(SignatureEnvelope.signers)
        ).filter(SignatureEnvelope.id == id).first()

    def get_by_number(self, number: str) -> Optional[SignatureEnvelope]:
        return self._base_query().filter(
            SignatureEnvelope.envelope_number == number
        ).first()

    def get_by_external_id(self, external_id: str) -> Optional[SignatureEnvelope]:
        return self._base_query().filter(
            SignatureEnvelope.external_id == external_id
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(SignatureEnvelope.id == id).count() > 0

    def number_exists(self, number: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(SignatureEnvelope.envelope_number == number)
        if exclude_id:
            query = query.filter(SignatureEnvelope.id != exclude_id)
        return query.count() > 0

    def get_next_number(self) -> str:
        """Genere le prochain numero d'enveloppe."""
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        prefix = f"ESIG-{year}{month:02d}-"

        last = self.db.query(SignatureEnvelope).filter(
            SignatureEnvelope.tenant_id == self.tenant_id,
            SignatureEnvelope.envelope_number.like(f"{prefix}%")
        ).order_by(desc(SignatureEnvelope.envelope_number)).first()

        if last:
            try:
                last_num = int(last.envelope_number.split("-")[-1])
                return f"{prefix}{last_num + 1:06d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}000001"

    def list(
        self,
        filters: EnvelopeFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[SignatureEnvelope], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    SignatureEnvelope.name.ilike(term),
                    SignatureEnvelope.envelope_number.ilike(term),
                    SignatureEnvelope.reference_number.ilike(term)
                ))
            if filters.status:
                query = query.filter(SignatureEnvelope.status.in_(filters.status))
            if filters.provider:
                query = query.filter(SignatureEnvelope.provider == filters.provider)
            if filters.document_type:
                query = query.filter(SignatureEnvelope.document_type == filters.document_type)
            if filters.reference_type:
                query = query.filter(SignatureEnvelope.reference_type == filters.reference_type)
            if filters.reference_id:
                query = query.filter(SignatureEnvelope.reference_id == filters.reference_id)
            if filters.created_by:
                query = query.filter(SignatureEnvelope.created_by == filters.created_by)
            if filters.date_from:
                query = query.filter(SignatureEnvelope.created_at >= datetime.combine(
                    filters.date_from, datetime.min.time()
                ))
            if filters.date_to:
                query = query.filter(SignatureEnvelope.created_at <= datetime.combine(
                    filters.date_to, datetime.max.time()
                ))
            if filters.expires_before:
                query = query.filter(SignatureEnvelope.expires_at <= datetime.combine(
                    filters.expires_before, datetime.max.time()
                ))
            if not filters.include_archived:
                query = query.filter(SignatureEnvelope.is_archived == False)
            if filters.tags:
                # Filtre sur tags JSON
                for tag in filters.tags:
                    query = query.filter(SignatureEnvelope.tags.contains([tag]))

        total = query.count()
        sort_col = getattr(SignatureEnvelope, sort_by, SignatureEnvelope.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_reference(self, reference_type: str, reference_id: UUID) -> List[SignatureEnvelope]:
        return self._base_query().filter(
            SignatureEnvelope.reference_type == reference_type,
            SignatureEnvelope.reference_id == reference_id
        ).order_by(desc(SignatureEnvelope.created_at)).all()

    def get_pending_reminders(self, before: datetime) -> List[SignatureEnvelope]:
        """Recupere les enveloppes necessitant un rappel."""
        return self._base_query().filter(
            SignatureEnvelope.status.in_([EnvelopeStatus.SENT, EnvelopeStatus.IN_PROGRESS]),
            SignatureEnvelope.reminder_enabled == True,
            SignatureEnvelope.next_reminder_at <= before
        ).all()

    def get_expiring_soon(self, days: int = 3) -> List[SignatureEnvelope]:
        """Recupere les enveloppes qui expirent bientot."""
        threshold = datetime.utcnow() + timedelta(days=days)
        return self._base_query().filter(
            SignatureEnvelope.status.in_([EnvelopeStatus.SENT, EnvelopeStatus.IN_PROGRESS]),
            SignatureEnvelope.expires_at <= threshold,
            SignatureEnvelope.expires_at > datetime.utcnow()
        ).all()

    def get_expired(self) -> List[SignatureEnvelope]:
        """Recupere les enveloppes expirees non traitees."""
        return self._base_query().filter(
            SignatureEnvelope.status.in_([EnvelopeStatus.SENT, EnvelopeStatus.IN_PROGRESS]),
            SignatureEnvelope.expires_at <= datetime.utcnow()
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> SignatureEnvelope:
        signers_data = data.pop("signers", [])
        documents_data = data.pop("documents", [])

        if "envelope_number" not in data:
            data["envelope_number"] = self.get_next_number()

        envelope = SignatureEnvelope(
            tenant_id=self.tenant_id,
            created_by=created_by,
            total_signers=len(signers_data),
            **data
        )
        self.db.add(envelope)
        self.db.flush()

        # Ajouter les signataires
        for i, signer_data in enumerate(signers_data):
            signer = EnvelopeSigner(
                tenant_id=self.tenant_id,
                envelope_id=envelope.id,
                signing_order=signer_data.get("signing_order", i + 1),
                access_token=secrets.token_urlsafe(32),
                token_expires_at=envelope.expires_at,
                **{k: v for k, v in signer_data.items() if k != "signing_order"}
            )
            self.db.add(signer)

        self.db.commit()
        self.db.refresh(envelope)
        return envelope

    def update(self, envelope: SignatureEnvelope, data: Dict[str, Any], updated_by: UUID = None) -> SignatureEnvelope:
        for key, value in data.items():
            if hasattr(envelope, key) and key not in ["signers", "documents"] and value is not None:
                setattr(envelope, key, value)
        envelope.updated_by = updated_by
        envelope.updated_at = datetime.utcnow()
        envelope.version += 1
        self.db.commit()
        self.db.refresh(envelope)
        return envelope

    def update_status(
        self,
        envelope: SignatureEnvelope,
        status: EnvelopeStatus,
        message: str = None
    ) -> SignatureEnvelope:
        """Met a jour le statut avec timestamp."""
        envelope.status = status
        envelope.status_message = message

        now = datetime.utcnow()
        if status == EnvelopeStatus.SENT:
            envelope.sent_at = now
        elif status == EnvelopeStatus.COMPLETED:
            envelope.completed_at = now
        elif status == EnvelopeStatus.DECLINED:
            envelope.declined_at = now
        elif status == EnvelopeStatus.EXPIRED:
            envelope.expired_at = now
        elif status == EnvelopeStatus.VOIDED:
            envelope.voided_at = now

        self.db.commit()
        self.db.refresh(envelope)
        return envelope

    def soft_delete(self, envelope: SignatureEnvelope, deleted_by: UUID = None) -> bool:
        envelope.is_deleted = True
        envelope.deleted_at = datetime.utcnow()
        envelope.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, envelope: SignatureEnvelope) -> SignatureEnvelope:
        envelope.is_deleted = False
        envelope.deleted_at = None
        envelope.deleted_by = None
        self.db.commit()
        self.db.refresh(envelope)
        return envelope

    def archive(self, envelope: SignatureEnvelope, archive_path: str = None) -> SignatureEnvelope:
        envelope.is_archived = True
        envelope.archived_at = datetime.utcnow()
        envelope.archive_path = archive_path
        self.db.commit()
        self.db.refresh(envelope)
        return envelope

    def count_by_status(self) -> Dict[str, int]:
        """Compte les enveloppes par statut."""
        result = self.db.query(
            SignatureEnvelope.status,
            func.count(SignatureEnvelope.id)
        ).filter(
            SignatureEnvelope.tenant_id == self.tenant_id,
            SignatureEnvelope.is_deleted == False
        ).group_by(SignatureEnvelope.status).all()

        return {status.value: count for status, count in result}


class EnvelopeDocumentRepository:
    """Repository pour les documents d'enveloppe."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(EnvelopeDocument).filter(
            EnvelopeDocument.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[EnvelopeDocument]:
        return self._base_query().options(
            joinedload(EnvelopeDocument.fields)
        ).filter(EnvelopeDocument.id == id).first()

    def get_by_envelope(self, envelope_id: UUID) -> List[EnvelopeDocument]:
        return self._base_query().filter(
            EnvelopeDocument.envelope_id == envelope_id
        ).order_by(EnvelopeDocument.document_order).all()

    def create(self, data: Dict[str, Any]) -> EnvelopeDocument:
        document = EnvelopeDocument(tenant_id=self.tenant_id, **data)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: EnvelopeDocument, data: Dict[str, Any]) -> EnvelopeDocument:
        for key, value in data.items():
            if hasattr(document, key):
                setattr(document, key, value)
        document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(document)
        return document

    def add_field(self, document_id: UUID, signer_id: UUID, field_data: Dict[str, Any]) -> DocumentField:
        field = DocumentField(
            tenant_id=self.tenant_id,
            document_id=document_id,
            signer_id=signer_id,
            **field_data
        )
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field


class EnvelopeSignerRepository:
    """Repository pour les signataires."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(EnvelopeSigner).filter(
            EnvelopeSigner.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[EnvelopeSigner]:
        return self._base_query().filter(EnvelopeSigner.id == id).first()

    def get_by_token(self, token: str) -> Optional[EnvelopeSigner]:
        return self._base_query().filter(
            EnvelopeSigner.access_token == token,
            EnvelopeSigner.token_expires_at > datetime.utcnow()
        ).first()

    def get_by_envelope(self, envelope_id: UUID) -> List[EnvelopeSigner]:
        return self._base_query().filter(
            EnvelopeSigner.envelope_id == envelope_id
        ).order_by(EnvelopeSigner.signing_order).all()

    def get_pending_by_envelope(self, envelope_id: UUID) -> List[EnvelopeSigner]:
        return self._base_query().filter(
            EnvelopeSigner.envelope_id == envelope_id,
            EnvelopeSigner.status.in_([SignerStatus.PENDING, SignerStatus.NOTIFIED, SignerStatus.VIEWED])
        ).order_by(EnvelopeSigner.signing_order).all()

    def get_next_signer(self, envelope_id: UUID) -> Optional[EnvelopeSigner]:
        """Recupere le prochain signataire dans l'ordre."""
        return self._base_query().filter(
            EnvelopeSigner.envelope_id == envelope_id,
            EnvelopeSigner.status.in_([SignerStatus.PENDING, SignerStatus.NOTIFIED, SignerStatus.VIEWED])
        ).order_by(EnvelopeSigner.signing_order).first()

    def create(self, data: Dict[str, Any]) -> EnvelopeSigner:
        signer = EnvelopeSigner(
            tenant_id=self.tenant_id,
            access_token=secrets.token_urlsafe(32),
            **data
        )
        self.db.add(signer)
        self.db.commit()
        self.db.refresh(signer)
        return signer

    def update(self, signer: EnvelopeSigner, data: Dict[str, Any]) -> EnvelopeSigner:
        for key, value in data.items():
            if hasattr(signer, key):
                setattr(signer, key, value)
        signer.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(signer)
        return signer

    def update_status(
        self,
        signer: EnvelopeSigner,
        status: SignerStatus,
        message: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> EnvelopeSigner:
        """Met a jour le statut avec timestamp et info technique."""
        signer.status = status
        signer.status_message = message

        now = datetime.utcnow()
        if status == SignerStatus.NOTIFIED:
            signer.notified_at = now
            signer.notification_count += 1
            signer.last_notification_at = now
        elif status == SignerStatus.VIEWED:
            signer.viewed_at = now
        elif status == SignerStatus.SIGNED:
            signer.signed_at = now
            signer.signature_ip = ip_address
            signer.signature_user_agent = user_agent
        elif status == SignerStatus.DECLINED:
            signer.declined_at = now
        elif status == SignerStatus.DELEGATED:
            signer.delegated_at = now

        self.db.commit()
        self.db.refresh(signer)
        return signer

    def add_action(
        self,
        signer: EnvelopeSigner,
        action: str,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> SignerAction:
        """Ajoute une action a l'historique du signataire."""
        action_record = SignerAction(
            tenant_id=self.tenant_id,
            signer_id=signer.id,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(action_record)
        self.db.commit()
        self.db.refresh(action_record)
        return action_record

    def regenerate_token(self, signer: EnvelopeSigner, expires_in_days: int = 30) -> EnvelopeSigner:
        """Regenere le token d'acces."""
        signer.access_token = secrets.token_urlsafe(32)
        signer.token_expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        self.db.commit()
        self.db.refresh(signer)
        return signer


class SignatureAuditEventRepository:
    """Repository pour les evenements d'audit."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._last_hash: Optional[str] = None

    def _base_query(self):
        return self.db.query(SignatureAuditEvent).filter(
            SignatureAuditEvent.tenant_id == self.tenant_id
        )

    def get_by_envelope(self, envelope_id: UUID) -> List[SignatureAuditEvent]:
        return self._base_query().filter(
            SignatureAuditEvent.envelope_id == envelope_id
        ).order_by(SignatureAuditEvent.event_at).all()

    def get_last_event(self, envelope_id: UUID) -> Optional[SignatureAuditEvent]:
        return self._base_query().filter(
            SignatureAuditEvent.envelope_id == envelope_id
        ).order_by(desc(SignatureAuditEvent.event_at)).first()

    def create(
        self,
        envelope_id: UUID,
        event_type: AuditEventType,
        actor_type: str,
        actor_id: UUID = None,
        actor_email: str = None,
        actor_name: str = None,
        event_description: str = None,
        event_data: Dict[str, Any] = None,
        document_id: UUID = None,
        signer_id: UUID = None,
        field_id: UUID = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None
    ) -> SignatureAuditEvent:
        """Cree un evenement d'audit avec chaine de hash."""
        # Recuperer le dernier hash
        last_event = self.get_last_event(envelope_id)
        previous_hash = last_event.event_hash if last_event else None

        # Calculer le hash de cet evenement
        hash_data = {
            "envelope_id": str(envelope_id),
            "event_type": event_type.value,
            "actor_type": actor_type,
            "actor_id": str(actor_id) if actor_id else None,
            "timestamp": datetime.utcnow().isoformat(),
            "previous_hash": previous_hash
        }
        event_hash = hashlib.sha256(
            str(hash_data).encode()
        ).hexdigest()

        event = SignatureAuditEvent(
            tenant_id=self.tenant_id,
            envelope_id=envelope_id,
            event_type=event_type,
            event_description=event_description,
            event_data=event_data,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_name=actor_name,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            document_id=document_id,
            signer_id=signer_id,
            field_id=field_id,
            event_hash=event_hash,
            previous_hash=previous_hash
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event


class SignatureCertificateRepository:
    """Repository pour les certificats."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(SignatureCertificate).filter(
            SignatureCertificate.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[SignatureCertificate]:
        return self._base_query().filter(SignatureCertificate.id == id).first()

    def get_by_number(self, number: str) -> Optional[SignatureCertificate]:
        return self._base_query().filter(
            SignatureCertificate.certificate_number == number
        ).first()

    def get_by_envelope(self, envelope_id: UUID) -> List[SignatureCertificate]:
        return self._base_query().filter(
            SignatureCertificate.envelope_id == envelope_id
        ).order_by(SignatureCertificate.generated_at).all()

    def create(self, data: Dict[str, Any], generated_by: UUID = None) -> SignatureCertificate:
        certificate = SignatureCertificate(
            tenant_id=self.tenant_id,
            generated_by=generated_by,
            **data
        )
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        return certificate


class SignatureReminderRepository:
    """Repository pour les rappels."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(SignatureReminder).filter(
            SignatureReminder.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[SignatureReminder]:
        return self._base_query().filter(SignatureReminder.id == id).first()

    def get_pending(self, before: datetime) -> List[SignatureReminder]:
        return self._base_query().filter(
            SignatureReminder.status == "pending",
            SignatureReminder.scheduled_at <= before
        ).order_by(SignatureReminder.scheduled_at).all()

    def get_by_envelope(self, envelope_id: UUID) -> List[SignatureReminder]:
        return self._base_query().filter(
            SignatureReminder.envelope_id == envelope_id
        ).order_by(desc(SignatureReminder.scheduled_at)).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> SignatureReminder:
        reminder = SignatureReminder(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def update_status(self, reminder: SignatureReminder, status: str, error: str = None) -> SignatureReminder:
        reminder.status = status
        if status == "sent":
            reminder.sent_at = datetime.utcnow()
        if error:
            reminder.error_message = error
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def cancel_pending(self, envelope_id: UUID) -> int:
        """Annule tous les rappels en attente pour une enveloppe."""
        count = self._base_query().filter(
            SignatureReminder.envelope_id == envelope_id,
            SignatureReminder.status == "pending"
        ).update({"status": "cancelled"})
        self.db.commit()
        return count


class SignatureStatsRepository:
    """Repository pour les statistiques."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(SignatureStats).filter(
            SignatureStats.tenant_id == self.tenant_id
        )

    def get_by_period(self, period_type: str, period_start) -> Optional[SignatureStats]:
        return self._base_query().filter(
            SignatureStats.period_type == period_type,
            SignatureStats.period_start == period_start
        ).first()

    def create_or_update(self, data: Dict[str, Any]) -> SignatureStats:
        existing = self.get_by_period(data["period_type"], data["period_start"])

        if existing:
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.calculated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        stats = SignatureStats(tenant_id=self.tenant_id, **data)
        self.db.add(stats)
        self.db.commit()
        self.db.refresh(stats)
        return stats
