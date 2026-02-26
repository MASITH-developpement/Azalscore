"""
AZALS MODULE ESIGNATURE - Service Principal
============================================

Service metier pour la signature electronique.
Orchestre les repositories, providers et logique metier.

Architecture multi-tenant avec audit complet.
"""
from __future__ import annotations


import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value

from .models import (
    ESignatureConfig,
    ProviderCredential,
    SignatureTemplate,
    SignatureEnvelope,
    EnvelopeDocument,
    EnvelopeSigner,
    SignatureCertificate,
    EnvelopeStatus,
    SignerStatus,
    AuditEventType,
    SignatureProvider,
    SignatureLevel,
    FieldType,
)
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
from .schemas import (
    ESignatureConfigCreate,
    ESignatureConfigUpdate,
    ProviderCredentialCreate,
    ProviderCredentialUpdate,
    SignatureTemplateCreate,
    SignatureTemplateUpdate,
    EnvelopeCreate,
    EnvelopeCreateFromTemplate,
    EnvelopeUpdate,
    SignerCreate,
    EnvelopeFilters,
    TemplateFilters,
    SendReminderRequest,
    DashboardStatsResponse,
    SignatureStatsResponse,
)
from .providers import (
    ProviderFactory,
    SignatureProviderInterface,
    ProviderEnvelopeInfo,
    ProviderDocumentInfo,
    ProviderSignerInfo,
    ProviderFieldInfo,
    WebhookEventInfo,
)
from .exceptions import (
    ConfigNotFoundError,
    ConfigAlreadyExistsError,
    ProviderNotConfiguredError,
    ProviderCredentialNotFoundError,
    ProviderAPIError,
    TemplateNotFoundError,
    TemplateDuplicateCodeError,
    TemplateLockedError,
    EnvelopeNotFoundError,
    EnvelopeStateError,
    EnvelopeNotDraftError,
    EnvelopeAlreadySentError,
    EnvelopeNoDocumentsError,
    EnvelopeNoSignersError,
    EnvelopePendingApprovalError,
    SignerNotFoundError,
    SignerAlreadySignedError,
    SignerNotAuthorizedError,
    InvalidAccessTokenError,
    MaxRemindersReachedError,
    CertificateGenerationError,
)

logger = logging.getLogger(__name__)


class ESignatureService:
    """
    Service principal de signature electronique.

    Gere tout le cycle de vie des signatures:
    - Configuration et providers
    - Templates de documents
    - Creation et envoi d'enveloppes
    - Suivi des signatures
    - Rappels automatiques
    - Certificats et archivage
    """

    def __init__(self, db: Session, tenant_id: str, user_id: UUID = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Repositories
        self.config_repo = ESignatureConfigRepository(db, tenant_id)
        self.credential_repo = ProviderCredentialRepository(db, tenant_id)
        self.template_repo = SignatureTemplateRepository(db, tenant_id)
        self.envelope_repo = SignatureEnvelopeRepository(db, tenant_id)
        self.document_repo = EnvelopeDocumentRepository(db, tenant_id)
        self.signer_repo = EnvelopeSignerRepository(db, tenant_id)
        self.audit_repo = SignatureAuditEventRepository(db, tenant_id)
        self.certificate_repo = SignatureCertificateRepository(db, tenant_id)
        self.reminder_repo = SignatureReminderRepository(db, tenant_id)
        self.stats_repo = SignatureStatsRepository(db, tenant_id)

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    def get_config(self) -> Optional[ESignatureConfig]:
        """Recupere la configuration signature du tenant."""
        return self.config_repo.get()

    def create_config(self, data: ESignatureConfigCreate) -> ESignatureConfig:
        """Cree la configuration signature."""
        if self.config_repo.exists():
            raise ConfigAlreadyExistsError()

        return self.config_repo.create(data.model_dump(), self.user_id)

    def update_config(self, data: ESignatureConfigUpdate) -> ESignatureConfig:
        """Met a jour la configuration."""
        config = self.config_repo.get()
        if not config:
            raise ConfigNotFoundError()

        update_data = data.model_dump(exclude_unset=True)
        return self.config_repo.update(config, update_data, self.user_id)

    # =========================================================================
    # PROVIDER CREDENTIALS
    # =========================================================================

    def get_provider_credentials(self, provider: SignatureProvider) -> Optional[ProviderCredential]:
        """Recupere les credentials d'un provider."""
        return self.credential_repo.get_by_provider(provider)

    def list_provider_credentials(self) -> List[ProviderCredential]:
        """Liste tous les credentials configures."""
        return self.credential_repo.list_all()

    def create_provider_credential(self, data: ProviderCredentialCreate) -> ProviderCredential:
        """Configure un provider."""
        # Chiffrer les secrets
        encrypted_data = data.model_dump()
        if data.api_key:
            encrypted_data["api_key_encrypted"] = encrypt_value(data.api_key)
            del encrypted_data["api_key"]
        if data.api_secret:
            encrypted_data["api_secret_encrypted"] = encrypt_value(data.api_secret)
            del encrypted_data["api_secret"]
        if data.private_key:
            encrypted_data["private_key_encrypted"] = encrypt_value(data.private_key)
            del encrypted_data["private_key"]
        if data.webhook_secret:
            encrypted_data["webhook_secret_encrypted"] = encrypt_value(data.webhook_secret)
            del encrypted_data["webhook_secret"]

        return self.credential_repo.create(encrypted_data)

    def update_provider_credential(
        self,
        credential_id: UUID,
        data: ProviderCredentialUpdate
    ) -> ProviderCredential:
        """Met a jour les credentials d'un provider."""
        credential = self.credential_repo.get_by_id(credential_id)
        if not credential:
            raise ProviderCredentialNotFoundError(str(credential_id))

        update_data = data.model_dump(exclude_unset=True)

        # Chiffrer les secrets
        if "api_key" in update_data and update_data["api_key"]:
            update_data["api_key_encrypted"] = encrypt_value(update_data.pop("api_key"))
        if "api_secret" in update_data and update_data["api_secret"]:
            update_data["api_secret_encrypted"] = encrypt_value(update_data.pop("api_secret"))
        if "private_key" in update_data and update_data["private_key"]:
            update_data["private_key_encrypted"] = encrypt_value(update_data.pop("private_key"))
        if "webhook_secret" in update_data and update_data["webhook_secret"]:
            update_data["webhook_secret_encrypted"] = encrypt_value(update_data.pop("webhook_secret"))

        return self.credential_repo.update(credential, update_data)

    async def verify_provider_credentials(self, provider: SignatureProvider) -> Tuple[bool, str]:
        """Verifie les credentials d'un provider."""
        try:
            provider_impl = self._get_provider(provider)
            is_valid = await provider_impl.verify_credentials()

            credential = self.credential_repo.get_by_provider(provider)
            if credential:
                credential.is_verified = is_valid
                credential.last_verified_at = datetime.utcnow()
                credential.last_error = None if is_valid else "Verification failed"
                self.db.commit()

            return is_valid, "Credentials valides" if is_valid else "Credentials invalides"

        except Exception as e:
            logger.exception(f"Erreur verification provider {provider}")
            return False, str(e)

    def _get_provider(self, provider: SignatureProvider) -> SignatureProviderInterface:
        """Recupere une instance de provider avec credentials."""
        credential = self.credential_repo.get_by_provider(provider)
        if not credential and provider != SignatureProvider.INTERNAL:
            raise ProviderNotConfiguredError(provider.value)

        credentials = {}
        if credential:
            if credential.api_key_encrypted:
                credentials["api_key"] = decrypt_value(credential.api_key_encrypted)
            if credential.api_secret_encrypted:
                credentials["api_secret"] = decrypt_value(credential.api_secret_encrypted)
            if credential.account_id:
                credentials["account_id"] = credential.account_id
            if credential.user_id:
                credentials["user_id"] = credential.user_id
            if credential.private_key_encrypted:
                credentials["private_key"] = decrypt_value(credential.private_key_encrypted)
            if credential.webhook_secret_encrypted:
                credentials["webhook_secret"] = decrypt_value(credential.webhook_secret_encrypted)
            credentials["environment"] = credential.environment

        return ProviderFactory.create(provider, credentials)

    # =========================================================================
    # TEMPLATES
    # =========================================================================

    def get_template(self, template_id: UUID) -> Optional[SignatureTemplate]:
        """Recupere un template par ID."""
        return self.template_repo.get_by_id(template_id)

    def get_template_by_code(self, code: str) -> Optional[SignatureTemplate]:
        """Recupere un template par code."""
        return self.template_repo.get_by_code(code)

    def list_templates(
        self,
        filters: TemplateFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[SignatureTemplate], int]:
        """Liste les templates avec filtres et pagination."""
        return self.template_repo.list(filters, page, page_size, sort_by, sort_dir)

    def create_template(
        self,
        data: SignatureTemplateCreate,
        file_content: bytes = None,
        file_name: str = None
    ) -> SignatureTemplate:
        """Cree un nouveau template."""
        if self.template_repo.code_exists(data.code):
            raise TemplateDuplicateCodeError(data.code)

        template_data = data.model_dump()

        # Gerer le fichier
        if file_content:
            template_data["file_path"] = self._store_template_file(
                data.code, file_content, file_name
            )
            template_data["file_name"] = file_name
            template_data["file_size"] = len(file_content)
            template_data["file_hash"] = hashlib.sha256(file_content).hexdigest()
            template_data["page_count"] = self._count_pdf_pages(file_content)

        return self.template_repo.create(template_data, self.user_id)

    def update_template(
        self,
        template_id: UUID,
        data: SignatureTemplateUpdate
    ) -> SignatureTemplate:
        """Met a jour un template."""
        template = self.template_repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(str(template_id))

        if template.is_locked:
            raise TemplateLockedError(str(template_id))

        return self.template_repo.update(template, data.model_dump(exclude_unset=True), self.user_id)

    def delete_template(self, template_id: UUID) -> bool:
        """Supprime un template (soft delete)."""
        template = self.template_repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(str(template_id))

        return self.template_repo.soft_delete(template, self.user_id)

    def _store_template_file(self, code: str, content: bytes, filename: str) -> str:
        """Stocke le fichier template et retourne le path."""
        # Implementation stockage (filesystem, S3, etc.)
        # Pour l'exemple, retourne un path fictif
        return f"/storage/esignature/templates/{self.tenant_id}/{code}/{filename}"

    def _count_pdf_pages(self, content: bytes) -> int:
        """Compte le nombre de pages d'un PDF."""
        try:
            # Utiliser PyPDF2 ou pdfplumber si disponible
            import PyPDF2
            from io import BytesIO
            reader = PyPDF2.PdfReader(BytesIO(content))
            return len(reader.pages)
        except Exception:
            return 1  # Fallback

    # =========================================================================
    # ENVELOPES - CREATION
    # =========================================================================

    def get_envelope(self, envelope_id: UUID) -> Optional[SignatureEnvelope]:
        """Recupere une enveloppe par ID."""
        return self.envelope_repo.get_by_id(envelope_id)

    def get_envelope_by_number(self, number: str) -> Optional[SignatureEnvelope]:
        """Recupere une enveloppe par numero."""
        return self.envelope_repo.get_by_number(number)

    def list_envelopes(
        self,
        filters: EnvelopeFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[SignatureEnvelope], int]:
        """Liste les enveloppes avec filtres et pagination."""
        return self.envelope_repo.list(filters, page, page_size, sort_by, sort_dir)

    def create_envelope(
        self,
        data: EnvelopeCreate,
        documents: List[Tuple[bytes, str]] = None  # [(content, filename), ...]
    ) -> SignatureEnvelope:
        """
        Cree une nouvelle enveloppe de signature.

        Args:
            data: Donnees de l'enveloppe
            documents: Liste de tuples (contenu, nom_fichier)
        """
        config = self.get_config()

        # Preparer les donnees
        envelope_data = data.model_dump()
        envelope_data["signers"] = [s.model_dump() for s in data.signers]

        # Appliquer config par defaut
        if not envelope_data.get("expires_at") and config:
            envelope_data["expires_at"] = datetime.utcnow() + timedelta(
                days=config.default_expiry_days
            )

        # Verifier approbation requise
        if config and config.require_approval_before_send:
            envelope_data["requires_approval"] = True
            envelope_data["approval_status"] = "pending"

        # Creer l'enveloppe
        envelope = self.envelope_repo.create(envelope_data, self.user_id)

        # Ajouter les documents
        if documents:
            for i, (content, filename) in enumerate(documents):
                self._add_document_to_envelope(
                    envelope, content, filename, i + 1
                )

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.CREATED,
            "user",
            description=f"Enveloppe {envelope.envelope_number} creee"
        )

        return envelope

    def create_envelope_from_template(
        self,
        data: EnvelopeCreateFromTemplate,
        document_content: bytes = None
    ) -> SignatureEnvelope:
        """Cree une enveloppe depuis un template."""
        template = self.template_repo.get_by_id(data.template_id)
        if not template:
            raise TemplateNotFoundError(str(data.template_id))

        # Incrementer usage
        self.template_repo.increment_usage(template)

        # Construire les donnees depuis template
        envelope_data = {
            "name": data.name or template.name,
            "template_id": template.id,
            "document_type": template.document_type,
            "signature_level": template.default_signature_level,
            "email_subject": template.email_subject,
            "email_body": template.email_body,
            "reference_type": data.reference_type,
            "reference_id": data.reference_id,
            "reference_number": data.reference_number,
            "expires_at": data.expires_at or (
                datetime.utcnow() + timedelta(days=template.default_expiry_days)
            ),
            "metadata": data.metadata,
            "signers": [s.model_dump() for s in data.signers],
        }

        envelope = self.envelope_repo.create(envelope_data, self.user_id)

        # Ajouter le document du template
        if document_content:
            self._add_document_to_envelope(
                envelope,
                document_content,
                template.file_name or "document.pdf",
                1
            )

            # Ajouter les champs du template aux signataires
            for field in template.fields:
                signer = envelope.signers[field.tab_order] if field.tab_order < len(envelope.signers) else envelope.signers[0]
                self.document_repo.add_field(
                    envelope.documents[0].id,
                    signer.id,
                    {
                        "field_type": field.field_type,
                        "page": field.page,
                        "x_position": field.x_position,
                        "y_position": field.y_position,
                        "width": field.width,
                        "height": field.height,
                        "label": field.label,
                        "is_required": field.is_required,
                    }
                )

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.CREATED,
            "user",
            description=f"Enveloppe creee depuis template {template.code}",
            event_data={"template_id": str(template.id)}
        )

        return envelope

    def _add_document_to_envelope(
        self,
        envelope: SignatureEnvelope,
        content: bytes,
        filename: str,
        order: int
    ) -> EnvelopeDocument:
        """Ajoute un document a une enveloppe."""
        file_hash = hashlib.sha256(content).hexdigest()
        file_path = self._store_document_file(envelope.envelope_number, content, filename)
        page_count = self._count_pdf_pages(content)

        document = self.document_repo.create({
            "envelope_id": envelope.id,
            "name": filename.rsplit(".", 1)[0],
            "document_order": order,
            "original_file_path": file_path,
            "original_file_name": filename,
            "original_file_size": len(content),
            "original_file_hash": file_hash,
            "page_count": page_count,
        })

        return document

    def _store_document_file(self, envelope_number: str, content: bytes, filename: str) -> str:
        """Stocke un fichier document."""
        return f"/storage/esignature/documents/{self.tenant_id}/{envelope_number}/{filename}"

    def update_envelope(self, envelope_id: UUID, data: EnvelopeUpdate) -> SignatureEnvelope:
        """Met a jour une enveloppe (brouillon uniquement)."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        if envelope.status != EnvelopeStatus.DRAFT:
            raise EnvelopeNotDraftError(str(envelope_id))

        return self.envelope_repo.update(
            envelope,
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    # =========================================================================
    # ENVELOPES - ENVOI
    # =========================================================================

    async def send_envelope(
        self,
        envelope_id: UUID,
        custom_message: str = None
    ) -> SignatureEnvelope:
        """Envoie une enveloppe aux signataires."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        # Validations
        if envelope.status not in [EnvelopeStatus.DRAFT, EnvelopeStatus.APPROVED]:
            raise EnvelopeStateError(envelope.status.value, "send")

        if not envelope.documents:
            raise EnvelopeNoDocumentsError(str(envelope_id))

        if not envelope.signers:
            raise EnvelopeNoSignersError(str(envelope_id))

        if envelope.requires_approval and envelope.approval_status != "approved":
            raise EnvelopePendingApprovalError(str(envelope_id))

        # Preparer pour le provider
        provider = self._get_provider(envelope.provider)

        provider_envelope = ProviderEnvelopeInfo(
            name=envelope.name,
            documents=[
                ProviderDocumentInfo(
                    name=doc.original_file_name,
                    content=self._load_document_content(doc.original_file_path),
                    fields=[
                        ProviderFieldInfo(
                            field_type=f.field_type,
                            page=f.page,
                            x=f.x_position,
                            y=f.y_position,
                            width=f.width,
                            height=f.height,
                            required=f.is_required,
                            signer_index=self._get_signer_index(envelope.signers, f.signer_id),
                            label=f.label
                        )
                        for f in doc.fields
                    ]
                )
                for doc in envelope.documents
            ],
            signers=[
                ProviderSignerInfo(
                    email=s.email,
                    first_name=s.first_name,
                    last_name=s.last_name,
                    phone=s.phone,
                    order=s.signing_order,
                    signature_level=envelope.signature_level,
                    require_id_verification=s.require_id_verification,
                    require_sms_otp=s.auth_method.value == "sms_otp" if s.auth_method else False
                )
                for s in envelope.signers
            ],
            signature_level=envelope.signature_level,
            expires_at=envelope.expires_at,
            email_subject=envelope.email_subject or custom_message,
            email_message=envelope.email_body,
            webhook_url=envelope.callback_url,
            metadata={"envelope_id": str(envelope.id), "tenant_id": self.tenant_id}
        )

        try:
            # Creer chez le provider
            external_id = await provider.create_envelope(provider_envelope)
            envelope.external_id = external_id

            # Envoyer
            await provider.send_envelope(external_id)

            # Mettre a jour les IDs externes des signataires
            for i, signer in enumerate(envelope.signers):
                if i < len(provider_envelope.signers):
                    signer.external_id = provider_envelope.signers[i].external_id
                self.signer_repo.update_status(signer, SignerStatus.NOTIFIED)

            # Mettre a jour statut
            envelope = self.envelope_repo.update_status(envelope, EnvelopeStatus.SENT)

            # Planifier les rappels
            if envelope.reminder_enabled:
                self._schedule_reminder(envelope)

            # Audit
            self._log_audit(
                envelope.id,
                AuditEventType.SENT,
                "user",
                description=f"Enveloppe envoyee aux {len(envelope.signers)} signataire(s)",
                event_data={"external_id": external_id}
            )

        except Exception as e:
            logger.exception(f"Erreur envoi enveloppe {envelope_id}")
            raise ProviderAPIError(envelope.provider.value, str(e))

        return envelope

    def _load_document_content(self, file_path: str) -> bytes:
        """Charge le contenu d'un document."""
        # Implementation lecture fichier
        # Pour l'exemple, retourne un contenu vide
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return b""

    def _get_signer_index(self, signers: List[EnvelopeSigner], signer_id: UUID) -> int:
        """Trouve l'index d'un signataire."""
        for i, signer in enumerate(signers):
            if signer.id == signer_id:
                return i
        return 0

    # =========================================================================
    # ENVELOPES - ACTIONS
    # =========================================================================

    async def cancel_envelope(
        self,
        envelope_id: UUID,
        reason: str,
        notify_signers: bool = True
    ) -> SignatureEnvelope:
        """Annule une enveloppe."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        if envelope.status in [EnvelopeStatus.COMPLETED, EnvelopeStatus.CANCELLED, EnvelopeStatus.VOIDED]:
            raise EnvelopeStateError(envelope.status.value, "cancel")

        # Annuler chez le provider si envoyee
        if envelope.external_id:
            try:
                provider = self._get_provider(envelope.provider)
                await provider.cancel_envelope(envelope.external_id, reason)
            except Exception as e:
                logger.warning(f"Erreur annulation provider: {e}")

        # Annuler les rappels
        self.reminder_repo.cancel_pending(envelope.id)

        # Mettre a jour statut
        envelope = self.envelope_repo.update_status(
            envelope,
            EnvelopeStatus.CANCELLED,
            reason
        )

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.CANCELLED,
            "user",
            description=f"Enveloppe annulee: {reason}"
        )

        return envelope

    async def void_envelope(self, envelope_id: UUID, reason: str) -> SignatureEnvelope:
        """Invalide une enveloppe completee."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        if envelope.status != EnvelopeStatus.COMPLETED:
            raise EnvelopeStateError(envelope.status.value, "void")

        envelope = self.envelope_repo.update_status(
            envelope,
            EnvelopeStatus.VOIDED,
            reason
        )

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.VOIDED,
            "user",
            description=f"Enveloppe invalidee: {reason}"
        )

        return envelope

    async def send_reminder(
        self,
        envelope_id: UUID,
        signer_ids: List[UUID] = None,
        custom_message: str = None
    ) -> bool:
        """Envoie un rappel aux signataires."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        if envelope.status not in [EnvelopeStatus.SENT, EnvelopeStatus.IN_PROGRESS]:
            raise EnvelopeStateError(envelope.status.value, "remind")

        config = self.get_config()
        if config and envelope.reminder_count >= config.max_reminders:
            raise MaxRemindersReachedError(config.max_reminders)

        provider = self._get_provider(envelope.provider)

        # Determiner les signataires a rappeler
        signers_to_remind = []
        if signer_ids:
            signers_to_remind = [s for s in envelope.signers if s.id in signer_ids]
        else:
            signers_to_remind = self.signer_repo.get_pending_by_envelope(envelope.id)

        # Envoyer rappels
        for signer in signers_to_remind:
            try:
                await provider.send_reminder(envelope.external_id, signer.external_id)

                # Log rappel
                self.reminder_repo.create({
                    "envelope_id": envelope.id,
                    "signer_id": signer.id,
                    "reminder_type": "manual",
                    "scheduled_at": datetime.utcnow(),
                    "sent_at": datetime.utcnow(),
                    "status": "sent",
                    "recipient_email": signer.email,
                    "message": custom_message
                }, self.user_id)

                # Mettre a jour signataire
                signer.notification_count += 1
                signer.last_notification_at = datetime.utcnow()
                self.db.commit()

            except Exception as e:
                logger.warning(f"Erreur rappel signataire {signer.id}: {e}")

        # Mettre a jour enveloppe
        envelope.reminder_count += 1
        envelope.last_reminder_at = datetime.utcnow()
        self.db.commit()

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.REMINDER_SENT,
            "user",
            description=f"Rappel envoye a {len(signers_to_remind)} signataire(s)"
        )

        return True

    def _schedule_reminder(self, envelope: SignatureEnvelope) -> None:
        """Planifie le prochain rappel automatique."""
        config = self.get_config()
        interval_days = envelope.reminder_interval_days or (
            config.reminder_interval_days if config else 3
        )

        next_reminder = datetime.utcnow() + timedelta(days=interval_days)

        # Ne pas depasser l'expiration
        if envelope.expires_at and next_reminder > envelope.expires_at:
            return

        envelope.next_reminder_at = next_reminder

        # Creer le rappel planifie
        for signer in envelope.signers:
            if signer.status in [SignerStatus.PENDING, SignerStatus.NOTIFIED, SignerStatus.VIEWED]:
                self.reminder_repo.create({
                    "envelope_id": envelope.id,
                    "signer_id": signer.id,
                    "reminder_type": "automatic",
                    "scheduled_at": next_reminder,
                    "status": "pending",
                    "recipient_email": signer.email
                })

        self.db.commit()

    # =========================================================================
    # ENVELOPES - APPROBATION
    # =========================================================================

    def approve_envelope(self, envelope_id: UUID, comments: str = None) -> SignatureEnvelope:
        """Approuve une enveloppe avant envoi."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        if envelope.status != EnvelopeStatus.PENDING_APPROVAL:
            raise EnvelopeStateError(envelope.status.value, "approve")

        envelope.approval_status = "approved"
        envelope.approved_at = datetime.utcnow()
        envelope.approved_by = self.user_id
        envelope = self.envelope_repo.update_status(envelope, EnvelopeStatus.APPROVED)

        self._log_audit(
            envelope.id,
            AuditEventType.APPROVAL_GRANTED,
            "user",
            description=f"Enveloppe approuvee{': ' + comments if comments else ''}"
        )

        return envelope

    def reject_envelope(self, envelope_id: UUID, reason: str) -> SignatureEnvelope:
        """Rejette une enveloppe avant envoi."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        if envelope.status != EnvelopeStatus.PENDING_APPROVAL:
            raise EnvelopeStateError(envelope.status.value, "reject")

        envelope.approval_status = "rejected"
        envelope = self.envelope_repo.update_status(
            envelope,
            EnvelopeStatus.DRAFT,
            f"Rejetee: {reason}"
        )

        self._log_audit(
            envelope.id,
            AuditEventType.APPROVAL_REJECTED,
            "user",
            description=f"Enveloppe rejetee: {reason}"
        )

        return envelope

    # =========================================================================
    # SIGNATAIRES - SIGNATURE
    # =========================================================================

    def get_signer_by_token(self, token: str) -> Optional[EnvelopeSigner]:
        """Recupere un signataire par son token d'acces."""
        return self.signer_repo.get_by_token(token)

    def view_envelope_as_signer(
        self,
        token: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[SignatureEnvelope, EnvelopeSigner]:
        """Marque l'enveloppe comme vue par le signataire."""
        signer = self.signer_repo.get_by_token(token)
        if not signer:
            raise InvalidAccessTokenError()

        envelope = self.envelope_repo.get_by_id(signer.envelope_id)

        if signer.status == SignerStatus.PENDING or signer.status == SignerStatus.NOTIFIED:
            self.signer_repo.update_status(
                signer,
                SignerStatus.VIEWED,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.signer_repo.add_action(signer, "viewed", ip_address=ip_address, user_agent=user_agent)

            # Premier view de l'enveloppe
            if not envelope.viewed_at:
                envelope.viewed_at = datetime.utcnow()
                envelope.viewed_count = 1
            else:
                envelope.viewed_count += 1
            self.db.commit()

            # Audit
            self._log_audit(
                envelope.id,
                AuditEventType.VIEWED,
                "signer",
                actor_id=signer.id,
                actor_email=signer.email,
                signer_id=signer.id,
                ip_address=ip_address,
                description=f"Document consulte par {signer.email}"
            )

            # Passer en in_progress si premiere vue
            if envelope.status == EnvelopeStatus.SENT:
                envelope = self.envelope_repo.update_status(envelope, EnvelopeStatus.IN_PROGRESS)

        return envelope, signer

    async def sign_envelope(
        self,
        token: str,
        signatures: Dict[str, str],  # field_id -> signature_data (base64)
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[SignatureEnvelope, EnvelopeSigner]:
        """Signe une enveloppe."""
        signer = self.signer_repo.get_by_token(token)
        if not signer:
            raise InvalidAccessTokenError()

        if signer.status == SignerStatus.SIGNED:
            raise SignerAlreadySignedError(str(signer.id))

        if signer.status in [SignerStatus.DECLINED, SignerStatus.DELEGATED, SignerStatus.EXPIRED]:
            raise SignerNotAuthorizedError(str(signer.id))

        envelope = self.envelope_repo.get_by_id(signer.envelope_id)

        # Verifier l'ordre de signature
        next_signer = self.signer_repo.get_next_signer(envelope.id)
        if next_signer and next_signer.id != signer.id:
            # Un autre signataire doit signer avant
            from .exceptions import SignerOrderError
            raise SignerOrderError(str(signer.id), next_signer.signing_order)

        # Remplir les champs de signature
        for field_id, signature_data in signatures.items():
            field = self.db.query(EnvelopeDocument).get(field_id)
            if field and field.signer_id == signer.id:
                field.value = signature_data
                field.signature_data = signature_data
                field.filled_at = datetime.utcnow()
                field.filled_by = signer.id
                field.signature_ip = ip_address
                field.signature_user_agent = user_agent

        self.db.commit()

        # Marquer comme signe
        self.signer_repo.update_status(
            signer,
            SignerStatus.SIGNED,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.signer_repo.add_action(
            signer, "signed",
            details={"fields_count": len(signatures)},
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Mettre a jour compteur
        envelope.signed_count += 1
        self.db.commit()

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.SIGNED,
            "signer",
            actor_id=signer.id,
            actor_email=signer.email,
            signer_id=signer.id,
            ip_address=ip_address,
            description=f"Document signe par {signer.email}"
        )

        # Verifier si tous ont signe
        pending = self.signer_repo.get_pending_by_envelope(envelope.id)
        if not pending:
            await self._complete_envelope(envelope)
        else:
            # Notifier le prochain signataire
            next_signer = pending[0]
            # TODO: Envoyer notification

        return envelope, signer

    def decline_envelope(
        self,
        token: str,
        reason: str,
        ip_address: str = None
    ) -> Tuple[SignatureEnvelope, EnvelopeSigner]:
        """Refuse de signer une enveloppe."""
        signer = self.signer_repo.get_by_token(token)
        if not signer:
            raise InvalidAccessTokenError()

        envelope = self.envelope_repo.get_by_id(signer.envelope_id)
        config = self.get_config()

        if config and not config.allow_decline:
            raise SignerNotAuthorizedError("Refus non autorise")

        signer.decline_reason = reason
        self.signer_repo.update_status(signer, SignerStatus.DECLINED, ip_address=ip_address)
        self.signer_repo.add_action(
            signer, "declined",
            details={"reason": reason},
            ip_address=ip_address
        )

        # Marquer l'enveloppe comme refusee
        envelope = self.envelope_repo.update_status(
            envelope,
            EnvelopeStatus.DECLINED,
            f"Refuse par {signer.email}: {reason}"
        )

        # Annuler les rappels
        self.reminder_repo.cancel_pending(envelope.id)

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.DECLINED,
            "signer",
            actor_id=signer.id,
            actor_email=signer.email,
            signer_id=signer.id,
            ip_address=ip_address,
            description=f"Signature refusee par {signer.email}: {reason}"
        )

        return envelope, signer

    def delegate_signature(
        self,
        token: str,
        delegate_email: str,
        delegate_first_name: str,
        delegate_last_name: str,
        reason: str = None,
        ip_address: str = None
    ) -> EnvelopeSigner:
        """Delegue la signature a une autre personne."""
        signer = self.signer_repo.get_by_token(token)
        if not signer:
            raise InvalidAccessTokenError()

        config = self.get_config()
        if config and not config.allow_delegation:
            from .exceptions import SignerDelegationNotAllowedError
            raise SignerDelegationNotAllowedError()

        # Creer le nouveau signataire
        new_signer = self.signer_repo.create({
            "envelope_id": signer.envelope_id,
            "email": delegate_email,
            "first_name": delegate_first_name,
            "last_name": delegate_last_name,
            "signing_order": signer.signing_order,
            "auth_method": signer.auth_method,
            "is_required": signer.is_required,
            "token_expires_at": signer.token_expires_at,
        })

        # Marquer l'original comme delegue
        signer.delegated_to_id = new_signer.id
        signer.delegated_to_email = delegate_email
        signer.delegation_reason = reason
        self.signer_repo.update_status(signer, SignerStatus.DELEGATED, ip_address=ip_address)
        self.signer_repo.add_action(
            signer, "delegated",
            details={"delegate_email": delegate_email, "reason": reason},
            ip_address=ip_address
        )

        # Audit
        envelope = self.envelope_repo.get_by_id(signer.envelope_id)
        self._log_audit(
            envelope.id,
            AuditEventType.DELEGATED,
            "signer",
            actor_id=signer.id,
            actor_email=signer.email,
            signer_id=new_signer.id,
            ip_address=ip_address,
            description=f"Signature deleguee de {signer.email} a {delegate_email}"
        )

        # Notifier le delegue
        # TODO: Envoyer email

        return new_signer

    # =========================================================================
    # COMPLETION & CERTIFICATES
    # =========================================================================

    async def _complete_envelope(self, envelope: SignatureEnvelope) -> SignatureEnvelope:
        """Complete une enveloppe quand tous ont signe."""
        # Mettre a jour statut
        envelope = self.envelope_repo.update_status(envelope, EnvelopeStatus.COMPLETED)

        # Annuler les rappels
        self.reminder_repo.cancel_pending(envelope.id)

        # Telecharger les documents signes du provider
        if envelope.external_id:
            try:
                provider = self._get_provider(envelope.provider)

                for doc in envelope.documents:
                    signed_content = await provider.download_signed_document(
                        envelope.external_id,
                        doc.external_id or "1"
                    )
                    if signed_content:
                        signed_path = self._store_document_file(
                            envelope.envelope_number,
                            signed_content,
                            f"signed_{doc.original_file_name}"
                        )
                        doc.signed_file_path = signed_path
                        doc.signed_file_hash = hashlib.sha256(signed_content).hexdigest()
                        doc.signed_at = datetime.utcnow()
                        doc.is_signed = True

                self.db.commit()

            except Exception as e:
                logger.warning(f"Erreur telechargement documents signes: {e}")

        # Generer le certificat
        await self._generate_certificate(envelope)

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.COMPLETED,
            "system",
            description=f"Enveloppe completee - {envelope.signed_count} signature(s)"
        )

        return envelope

    async def _generate_certificate(self, envelope: SignatureEnvelope) -> SignatureCertificate:
        """Genere le certificat de completion."""
        try:
            # Telecharger l'audit trail du provider
            audit_content = b""
            if envelope.external_id:
                try:
                    provider = self._get_provider(envelope.provider)
                    audit_content = await provider.download_audit_trail(envelope.external_id)
                except Exception:
                    pass

            # Generer le numero de certificat
            cert_number = f"CERT-{envelope.envelope_number}-{secrets.token_hex(4).upper()}"

            # Calculer le hash
            cert_hash = hashlib.sha256(
                f"{envelope.id}{envelope.completed_at}{cert_number}".encode()
            ).hexdigest()

            # Stocker le fichier
            cert_path = self._store_document_file(
                envelope.envelope_number,
                audit_content or self._generate_audit_pdf(envelope),
                f"certificate_{cert_number}.pdf"
            )

            certificate = self.certificate_repo.create({
                "envelope_id": envelope.id,
                "certificate_number": cert_number,
                "certificate_type": "completion",
                "file_path": cert_path,
                "file_hash": cert_hash,
                "file_size": len(audit_content) if audit_content else 0,
                "valid_from": datetime.utcnow(),
                "is_valid": True,
            }, self.user_id)

            return certificate

        except Exception as e:
            logger.exception(f"Erreur generation certificat: {e}")
            raise CertificateGenerationError(str(e))

    def _generate_audit_pdf(self, envelope: SignatureEnvelope) -> bytes:
        """Genere un PDF d'audit trail basique."""
        # Implementation basique - en production utiliser une lib PDF
        return b""  # Placeholder

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    async def handle_webhook(
        self,
        provider: SignatureProvider,
        payload: bytes,
        signature: str = None
    ) -> Optional[SignatureEnvelope]:
        """Traite un webhook entrant d'un provider."""
        provider_impl = self._get_provider(provider)

        # Verifier la signature
        if signature and not provider_impl.verify_webhook(payload, signature):
            logger.warning(f"Signature webhook invalide pour {provider}")
            from .exceptions import InvalidWebhookSignatureError
            raise InvalidWebhookSignatureError(provider.value)

        # Parser l'evenement
        import json
        event = provider_impl.parse_webhook(json.loads(payload))

        # Trouver l'enveloppe
        envelope = self.envelope_repo.get_by_external_id(event.envelope_external_id)
        if not envelope:
            logger.warning(f"Enveloppe non trouvee pour webhook: {event.envelope_external_id}")
            return None

        # Traiter selon le type d'evenement
        await self._process_webhook_event(envelope, event)

        return envelope

    async def _process_webhook_event(
        self,
        envelope: SignatureEnvelope,
        event: WebhookEventInfo
    ) -> None:
        """Traite un evenement webhook."""
        event_type = event.event_type.lower()

        if "sign" in event_type or "complete" in event_type:
            # Rafraichir le statut depuis le provider
            provider = self._get_provider(envelope.provider)
            status = await provider.get_status(envelope.external_id)

            # Mettre a jour les signataires
            for signer_status in status.signers_status:
                signer = None
                for s in envelope.signers:
                    if s.external_id == signer_status.get("external_id"):
                        signer = s
                        break

                if signer and signer_status.get("status") == "signed":
                    if signer.status != SignerStatus.SIGNED:
                        self.signer_repo.update_status(signer, SignerStatus.SIGNED)
                        envelope.signed_count += 1

            # Verifier si complete
            if status.status in ["done", "completed"]:
                if envelope.status != EnvelopeStatus.COMPLETED:
                    await self._complete_envelope(envelope)

        elif "decline" in event_type or "reject" in event_type:
            if envelope.status not in [EnvelopeStatus.DECLINED, EnvelopeStatus.COMPLETED]:
                self.envelope_repo.update_status(envelope, EnvelopeStatus.DECLINED)

        elif "expire" in event_type:
            if envelope.status not in [EnvelopeStatus.EXPIRED, EnvelopeStatus.COMPLETED]:
                self.envelope_repo.update_status(envelope, EnvelopeStatus.EXPIRED)

        elif "view" in event_type:
            if event.signer_external_id:
                for signer in envelope.signers:
                    if signer.external_id == event.signer_external_id:
                        if signer.status in [SignerStatus.PENDING, SignerStatus.NOTIFIED]:
                            self.signer_repo.update_status(signer, SignerStatus.VIEWED)
                        break

        self.db.commit()

    # =========================================================================
    # DOWNLOADS
    # =========================================================================

    def get_signed_document(self, envelope_id: UUID, document_id: UUID) -> Tuple[bytes, str]:
        """Recupere un document signe."""
        envelope = self.envelope_repo.get_by_id(envelope_id)
        if not envelope:
            raise EnvelopeNotFoundError(str(envelope_id))

        document = self.document_repo.get_by_id(document_id)
        if not document or document.envelope_id != envelope.id:
            from .exceptions import DocumentNotFoundError
            raise DocumentNotFoundError(str(document_id))

        file_path = document.signed_file_path or document.original_file_path
        content = self._load_document_content(file_path)

        # Audit
        self._log_audit(
            envelope.id,
            AuditEventType.DOWNLOADED,
            "user",
            document_id=document.id,
            description=f"Document telecharge: {document.name}"
        )

        return content, document.original_file_name

    def get_certificate(self, envelope_id: UUID) -> Tuple[bytes, str]:
        """Recupere le certificat d'une enveloppe."""
        certificates = self.certificate_repo.get_by_envelope(envelope_id)
        if not certificates:
            from .exceptions import CertificateNotFoundError
            raise CertificateNotFoundError(envelope_id=str(envelope_id))

        cert = certificates[-1]  # Le plus recent
        content = self._load_document_content(cert.file_path)

        return content, f"certificate_{cert.certificate_number}.pdf"

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_dashboard_stats(self) -> DashboardStatsResponse:
        """Recupere les stats pour le tableau de bord."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Stats aujourd'hui
        today_stats = self._calculate_stats(today_start, now, "daily")

        # Stats ce mois
        month_stats = self._calculate_stats(month_start, now, "monthly")

        # Comptages
        status_counts = self.envelope_repo.count_by_status()
        pending = status_counts.get("sent", 0) + status_counts.get("in_progress", 0)

        # Signatures en attente
        pending_signatures = 0
        pending_envelopes, _ = self.envelope_repo.list(
            EnvelopeFilters(status=[EnvelopeStatus.SENT, EnvelopeStatus.IN_PROGRESS]),
            page_size=1000
        )
        for env in pending_envelopes:
            pending_signatures += env.total_signers - env.signed_count

        # Expirant bientot
        expiring = len(self.envelope_repo.get_expiring_soon(3))

        # Completions recentes
        recent, _ = self.envelope_repo.list(
            EnvelopeFilters(status=[EnvelopeStatus.COMPLETED]),
            page_size=5,
            sort_by="completed_at",
            sort_dir="desc"
        )

        return DashboardStatsResponse(
            tenant_id=self.tenant_id,
            today=today_stats,
            this_month=month_stats,
            pending_envelopes=pending,
            pending_signatures=pending_signatures,
            expiring_soon=expiring,
            recent_completions=[
                {
                    "id": e.id,
                    "envelope_number": e.envelope_number,
                    "name": e.name,
                    "status": e.status,
                    "completed_at": e.completed_at
                }
                for e in recent
            ]
        )

    def _calculate_stats(
        self,
        start: datetime,
        end: datetime,
        period_type: str
    ) -> SignatureStatsResponse:
        """Calcule les statistiques pour une periode."""
        filters = EnvelopeFilters(
            date_from=start.date(),
            date_to=end.date(),
            include_archived=True
        )
        envelopes, total = self.envelope_repo.list(filters, page_size=10000)

        stats = {
            "tenant_id": self.tenant_id,
            "period_type": period_type,
            "period_start": start.date(),
            "period_end": end.date(),
            "envelopes_created": total,
            "envelopes_sent": 0,
            "envelopes_completed": 0,
            "envelopes_declined": 0,
            "envelopes_expired": 0,
            "envelopes_cancelled": 0,
            "total_signers": 0,
            "signers_signed": 0,
            "signers_declined": 0,
            "by_provider": {},
            "by_document_type": {},
            "by_signature_level": {},
        }

        for env in envelopes:
            if env.sent_at:
                stats["envelopes_sent"] += 1
            if env.status == EnvelopeStatus.COMPLETED:
                stats["envelopes_completed"] += 1
            elif env.status == EnvelopeStatus.DECLINED:
                stats["envelopes_declined"] += 1
            elif env.status == EnvelopeStatus.EXPIRED:
                stats["envelopes_expired"] += 1
            elif env.status == EnvelopeStatus.CANCELLED:
                stats["envelopes_cancelled"] += 1

            stats["total_signers"] += env.total_signers
            stats["signers_signed"] += env.signed_count

            # Par provider
            provider_key = env.provider.value
            stats["by_provider"][provider_key] = stats["by_provider"].get(provider_key, 0) + 1

            # Par type document
            doc_key = env.document_type.value
            stats["by_document_type"][doc_key] = stats["by_document_type"].get(doc_key, 0) + 1

            # Par niveau signature
            level_key = env.signature_level.value
            stats["by_signature_level"][level_key] = stats["by_signature_level"].get(level_key, 0) + 1

        # Taux de completion
        if stats["envelopes_sent"] > 0:
            stats["completion_rate"] = round(
                stats["envelopes_completed"] / stats["envelopes_sent"] * 100, 2
            )
        else:
            stats["completion_rate"] = 0.0

        return SignatureStatsResponse(**stats)

    # =========================================================================
    # AUDIT
    # =========================================================================

    def _log_audit(
        self,
        envelope_id: UUID,
        event_type: AuditEventType,
        actor_type: str,
        actor_id: UUID = None,
        actor_email: str = None,
        description: str = None,
        event_data: Dict[str, Any] = None,
        document_id: UUID = None,
        signer_id: UUID = None,
        field_id: UUID = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> None:
        """Enregistre un evenement d'audit."""
        self.audit_repo.create(
            envelope_id=envelope_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id or self.user_id,
            actor_email=actor_email,
            event_description=description,
            event_data=event_data,
            document_id=document_id,
            signer_id=signer_id,
            field_id=field_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def get_audit_trail(self, envelope_id: UUID) -> List[Dict[str, Any]]:
        """Recupere l'historique d'audit d'une enveloppe."""
        events = self.audit_repo.get_by_envelope(envelope_id)
        return [
            {
                "id": str(e.id),
                "event_type": e.event_type.value,
                "event_description": e.event_description,
                "actor_type": e.actor_type,
                "actor_email": e.actor_email,
                "ip_address": e.ip_address,
                "event_at": e.event_at.isoformat()
            }
            for e in events
        ]


# =============================================================================
# FACTORY
# =============================================================================

def get_esignature_service(
    db: Session,
    tenant_id: str,
    user_id: UUID = None
) -> ESignatureService:
    """Factory pour le service signature."""
    return ESignatureService(db, tenant_id, user_id)
