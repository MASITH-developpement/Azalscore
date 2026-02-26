"""
AZALS MODULE ESIGNATURE - Models SQLAlchemy
============================================

Modeles pour la signature electronique conforme eIDAS.
Inspire de DocuSign, Yousign, Odoo Sign, PandaDoc.

Multi-tenant avec tenant_id obligatoire.
Soft delete avec audit complet.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID, JSON, JSONB
from app.db import Base


# =============================================================================
# ENUMS
# =============================================================================

class SignatureProvider(str, enum.Enum):
    """Providers de signature electronique supportes."""
    INTERNAL = "internal"      # Signature interne AZALS
    YOUSIGN = "yousign"        # Leader francais eIDAS
    DOCUSIGN = "docusign"      # Leader mondial
    HELLOSIGN = "hellosign"    # Dropbox Sign
    ADOBE_SIGN = "adobe_sign"  # Adobe Acrobat Sign


class SignatureLevel(str, enum.Enum):
    """Niveau de signature selon eIDAS."""
    SIMPLE = "simple"          # Signature simple (email)
    ADVANCED = "advanced"      # Signature avancee (SMS + piece identite)
    QUALIFIED = "qualified"    # Signature qualifiee (certificat qualifie)


class EnvelopeStatus(str, enum.Enum):
    """Statut d'une enveloppe de signature."""
    DRAFT = "draft"                    # Brouillon
    PENDING_APPROVAL = "pending_approval"  # En attente approbation
    APPROVED = "approved"              # Approuvee, prete a envoyer
    SENT = "sent"                      # Envoyee aux signataires
    IN_PROGRESS = "in_progress"        # Signatures en cours
    COMPLETED = "completed"            # Toutes signatures recues
    DECLINED = "declined"              # Refusee par un signataire
    EXPIRED = "expired"                # Expiree
    CANCELLED = "cancelled"            # Annulee
    VOIDED = "voided"                  # Invalidee


class SignerStatus(str, enum.Enum):
    """Statut d'un signataire."""
    PENDING = "pending"            # En attente
    NOTIFIED = "notified"          # Notifie par email/SMS
    VIEWED = "viewed"              # Document consulte
    SIGNED = "signed"              # Signe
    DECLINED = "declined"          # Refuse
    DELEGATED = "delegated"        # Delegue a un autre
    EXPIRED = "expired"            # Expire


class DocumentType(str, enum.Enum):
    """Type de document a signer."""
    CONTRACT = "contract"          # Contrat
    INVOICE = "invoice"            # Facture
    QUOTE = "quote"                # Devis
    PURCHASE_ORDER = "purchase_order"  # Bon de commande
    NDA = "nda"                    # Accord de confidentialite
    EMPLOYMENT = "employment"      # Contrat de travail
    AMENDMENT = "amendment"        # Avenant
    MANDATE = "mandate"            # Mandat SEPA
    GDPR_CONSENT = "gdpr_consent"  # Consentement RGPD
    LEASE = "lease"                # Bail
    LOAN = "loan"                  # Pret
    POLICY = "policy"              # Politique interne
    OTHER = "other"


class FieldType(str, enum.Enum):
    """Type de champ de signature."""
    SIGNATURE = "signature"        # Signature
    INITIALS = "initials"          # Paraphe
    DATE = "date"                  # Date
    TEXT = "text"                  # Texte libre
    CHECKBOX = "checkbox"          # Case a cocher
    RADIO = "radio"                # Bouton radio
    DROPDOWN = "dropdown"          # Liste deroulante
    ATTACHMENT = "attachment"      # Piece jointe
    COMPANY_STAMP = "company_stamp"  # Cachet societe


class AuthMethod(str, enum.Enum):
    """Methode d'authentification du signataire."""
    EMAIL = "email"                # Email simple
    SMS_OTP = "sms_otp"            # Code SMS
    EMAIL_OTP = "email_otp"        # Code Email
    ID_VERIFICATION = "id_verification"  # Verification piece identite
    KNOWLEDGE_BASED = "knowledge_based"   # Questions de securite
    TWO_FACTOR = "two_factor"      # 2FA


class ReminderType(str, enum.Enum):
    """Type de rappel."""
    SCHEDULED = "scheduled"        # Rappel programme
    MANUAL = "manual"              # Rappel manuel
    AUTOMATIC = "automatic"        # Rappel automatique systeme


class AuditEventType(str, enum.Enum):
    """Type d'evenement audit."""
    CREATED = "created"
    SENT = "sent"
    VIEWED = "viewed"
    SIGNED = "signed"
    DECLINED = "declined"
    DELEGATED = "delegated"
    REMINDER_SENT = "reminder_sent"
    DOWNLOADED = "downloaded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    COMPLETED = "completed"
    VOIDED = "voided"
    FIELD_FILLED = "field_filled"
    ATTACHMENT_ADDED = "attachment_added"
    COMMENT_ADDED = "comment_added"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"


class TemplateCategory(str, enum.Enum):
    """Categorie de modele."""
    SALES = "sales"
    HR = "hr"
    LEGAL = "legal"
    FINANCE = "finance"
    PROCUREMENT = "procurement"
    OPERATIONS = "operations"
    CUSTOM = "custom"


# =============================================================================
# MODELS - CONFIGURATION
# =============================================================================

class ESignatureConfig(Base):
    """Configuration globale signature electronique par tenant."""
    __tablename__ = "esignature_configs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Provider par defaut
    default_provider = Column(Enum(SignatureProvider), default=SignatureProvider.INTERNAL)
    default_signature_level = Column(Enum(SignatureLevel), default=SignatureLevel.SIMPLE)

    # Expiration
    default_expiry_days = Column(Integer, default=30)
    max_expiry_days = Column(Integer, default=90)

    # Rappels
    auto_reminders_enabled = Column(Boolean, default=True)
    reminder_interval_days = Column(Integer, default=3)
    max_reminders = Column(Integer, default=5)

    # Branding
    company_logo_url = Column(Text, nullable=True)
    primary_color = Column(String(7), default="#1976D2")
    email_footer = Column(Text, nullable=True)

    # Notifications
    notify_on_view = Column(Boolean, default=True)
    notify_on_sign = Column(Boolean, default=True)
    notify_on_complete = Column(Boolean, default=True)
    notify_on_decline = Column(Boolean, default=True)

    # Archivage
    auto_archive_days = Column(Integer, default=365)  # Archiver apres X jours
    retention_years = Column(Integer, default=10)     # Conserver X annees

    # Securite
    require_auth_before_view = Column(Boolean, default=False)
    allow_decline = Column(Boolean, default=True)
    allow_delegation = Column(Boolean, default=True)

    # Workflow
    require_approval_before_send = Column(Boolean, default=False)
    approval_workflow_id = Column(UniversalUUID(), nullable=True)

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', name='uq_esignature_config_tenant'),
        Index('ix_esig_config_tenant', 'tenant_id'),
    )


class ProviderCredential(Base):
    """Credentials pour un provider externe."""
    __tablename__ = "esignature_provider_credentials"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    provider = Column(Enum(SignatureProvider), nullable=False)
    environment = Column(String(20), default="production")  # production, sandbox

    # Credentials (chiffres en base)
    api_key_encrypted = Column(Text, nullable=True)
    api_secret_encrypted = Column(Text, nullable=True)
    account_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    private_key_encrypted = Column(Text, nullable=True)

    # Webhook
    webhook_secret_encrypted = Column(Text, nullable=True)
    webhook_url = Column(Text, nullable=True)

    # OAuth tokens
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Statut
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'provider', 'environment', name='uq_provider_cred'),
        Index('ix_provider_cred_tenant', 'tenant_id'),
    )


# =============================================================================
# MODELS - TEMPLATES
# =============================================================================

class SignatureTemplate(Base):
    """Modele de document reutilisable."""
    __tablename__ = "esignature_templates"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(TemplateCategory), default=TemplateCategory.CUSTOM)
    document_type = Column(Enum(DocumentType), default=DocumentType.OTHER)

    # Document source
    file_path = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA256
    mime_type = Column(String(100), default="application/pdf")
    page_count = Column(Integer, nullable=True)

    # Configuration signature
    default_signature_level = Column(Enum(SignatureLevel), default=SignatureLevel.SIMPLE)
    default_expiry_days = Column(Integer, default=30)

    # Message par defaut
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    sms_message = Column(String(160), nullable=True)

    # Roles signataires predefinis
    signer_roles = Column(JSON, default=list)  # [{"role": "client", "order": 1, "required": true}]

    # Variables pour merge
    merge_fields = Column(JSON, default=list)  # [{"name": "client_name", "type": "text", "required": true}]

    # Statut
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)  # Empeche modification

    # Versioning
    version = Column(Integer, default=1)
    parent_template_id = Column(UniversalUUID(), nullable=True)

    # Usage stats
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_template_code'),
        Index('ix_template_tenant', 'tenant_id'),
        Index('ix_template_category', 'tenant_id', 'category'),
        Index('ix_template_active', 'tenant_id', 'is_active', 'is_deleted'),
    )


class TemplateField(Base):
    """Champ predefini dans un template."""
    __tablename__ = "esignature_template_fields"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    template_id = Column(UniversalUUID(), ForeignKey("esignature_templates.id", ondelete="CASCADE"), nullable=False)

    # Type et position
    field_type = Column(Enum(FieldType), nullable=False, default=FieldType.SIGNATURE)
    page = Column(Integer, nullable=False, default=1)
    x_position = Column(Float, nullable=False)  # Position en %
    y_position = Column(Float, nullable=False)  # Position en %
    width = Column(Float, default=150)          # Pixels
    height = Column(Float, default=50)          # Pixels

    # Configuration
    signer_role = Column(String(50), nullable=True)  # Role du signataire
    label = Column(String(255), nullable=True)
    placeholder = Column(String(255), nullable=True)
    tooltip = Column(String(500), nullable=True)
    is_required = Column(Boolean, default=True)
    is_read_only = Column(Boolean, default=False)

    # Validation
    validation_regex = Column(String(500), nullable=True)
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    options = Column(JSON, nullable=True)  # Pour dropdown/radio

    # Ordre
    tab_order = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    template = relationship("SignatureTemplate", back_populates="fields")

    __table_args__ = (
        Index('ix_template_field_template', 'template_id'),
    )


# =============================================================================
# MODELS - ENVELOPES
# =============================================================================

class SignatureEnvelope(Base):
    """Enveloppe de signature (conteneur principal)."""
    __tablename__ = "esignature_envelopes"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    envelope_number = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Reference business
    reference_type = Column(String(50), nullable=True)  # invoice, quote, contract...
    reference_id = Column(UniversalUUID(), nullable=True)
    reference_number = Column(String(50), nullable=True)

    # Template source
    template_id = Column(UniversalUUID(), ForeignKey("esignature_templates.id"), nullable=True)

    # Configuration
    provider = Column(Enum(SignatureProvider), default=SignatureProvider.INTERNAL)
    signature_level = Column(Enum(SignatureLevel), default=SignatureLevel.SIMPLE)
    document_type = Column(Enum(DocumentType), default=DocumentType.OTHER)

    # Statut
    status = Column(Enum(EnvelopeStatus), default=EnvelopeStatus.DRAFT, index=True)
    status_message = Column(Text, nullable=True)

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)  # Premier view
    completed_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True)
    voided_at = Column(DateTime, nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Message personnalise
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    sms_message = Column(String(160), nullable=True)

    # Rappels
    reminder_enabled = Column(Boolean, default=True)
    reminder_interval_days = Column(Integer, default=3)
    reminder_count = Column(Integer, default=0)
    last_reminder_at = Column(DateTime, nullable=True)
    next_reminder_at = Column(DateTime, nullable=True)

    # Callbacks
    callback_url = Column(Text, nullable=True)  # Webhook custom
    redirect_url = Column(Text, nullable=True)  # Redirect apres signature

    # Provider externe
    external_id = Column(String(255), nullable=True, index=True)
    external_url = Column(Text, nullable=True)  # URL signature chez provider

    # Statistiques
    total_signers = Column(Integer, default=0)
    signed_count = Column(Integer, default=0)
    viewed_count = Column(Integer, default=0)

    # Metadonnees business (extra_data car 'metadata' reserve SQLAlchemy)
    extra_data = Column(JSON, default=dict)
    tags = Column(JSON, default=list)

    # Workflow approbation
    requires_approval = Column(Boolean, default=False)
    approval_status = Column(String(20), nullable=True)  # pending, approved, rejected
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(UniversalUUID(), nullable=True)

    # Archive
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    archive_path = Column(Text, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Versioning
    version = Column(Integer, default=1)

    # Audit
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    template = relationship("SignatureTemplate")
    documents = relationship("EnvelopeDocument", back_populates="envelope", cascade="all, delete-orphan")
    signers = relationship("EnvelopeSigner", back_populates="envelope", cascade="all, delete-orphan", order_by="EnvelopeSigner.signing_order")
    audit_events = relationship("SignatureAuditEvent", back_populates="envelope", cascade="all, delete-orphan")
    reminders = relationship("SignatureReminder", back_populates="envelope", cascade="all, delete-orphan")
    certificates = relationship("SignatureCertificate", back_populates="envelope", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'envelope_number', name='uq_envelope_number'),
        Index('ix_envelope_tenant', 'tenant_id'),
        Index('ix_envelope_status', 'tenant_id', 'status'),
        Index('ix_envelope_reference', 'tenant_id', 'reference_type', 'reference_id'),
        Index('ix_envelope_external', 'external_id'),
        Index('ix_envelope_expires', 'tenant_id', 'status', 'expires_at'),
        Index('ix_envelope_created', 'tenant_id', 'created_at'),
    )


class EnvelopeDocument(Base):
    """Document dans une enveloppe."""
    __tablename__ = "esignature_envelope_documents"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    envelope_id = Column(UniversalUUID(), ForeignKey("esignature_envelopes.id", ondelete="CASCADE"), nullable=False)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_order = Column(Integer, default=1)

    # Fichier original
    original_file_path = Column(Text, nullable=False)
    original_file_name = Column(String(255), nullable=False)
    original_file_size = Column(BigInteger, nullable=False)
    original_file_hash = Column(String(64), nullable=False)  # SHA256
    mime_type = Column(String(100), default="application/pdf")
    page_count = Column(Integer, nullable=True)

    # Fichier signe
    signed_file_path = Column(Text, nullable=True)
    signed_file_hash = Column(String(64), nullable=True)
    signed_at = Column(DateTime, nullable=True)

    # Provider externe
    external_id = Column(String(255), nullable=True)

    # Statut
    is_signed = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    envelope = relationship("SignatureEnvelope", back_populates="documents")
    fields = relationship("DocumentField", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_doc_envelope', 'envelope_id'),
        Index('ix_doc_tenant', 'tenant_id'),
    )


class DocumentField(Base):
    """Champ de signature/saisie dans un document."""
    __tablename__ = "esignature_document_fields"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    document_id = Column(UniversalUUID(), ForeignKey("esignature_envelope_documents.id", ondelete="CASCADE"), nullable=False)
    signer_id = Column(UniversalUUID(), ForeignKey("esignature_envelope_signers.id", ondelete="CASCADE"), nullable=True)

    # Type et position
    field_type = Column(Enum(FieldType), nullable=False, default=FieldType.SIGNATURE)
    page = Column(Integer, nullable=False, default=1)
    x_position = Column(Float, nullable=False)
    y_position = Column(Float, nullable=False)
    width = Column(Float, default=150)
    height = Column(Float, default=50)

    # Configuration
    name = Column(String(100), nullable=True)
    label = Column(String(255), nullable=True)
    placeholder = Column(String(255), nullable=True)
    tooltip = Column(String(500), nullable=True)
    is_required = Column(Boolean, default=True)
    is_read_only = Column(Boolean, default=False)

    # Validation
    validation_regex = Column(String(500), nullable=True)
    options = Column(JSON, nullable=True)

    # Valeur
    value = Column(Text, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    filled_by = Column(UniversalUUID(), nullable=True)

    # Signature specifique
    signature_data = Column(Text, nullable=True)  # Base64 de la signature
    signature_ip = Column(String(45), nullable=True)
    signature_user_agent = Column(String(500), nullable=True)

    # Ordre
    tab_order = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    document = relationship("EnvelopeDocument", back_populates="fields")
    signer = relationship("EnvelopeSigner", back_populates="fields")

    __table_args__ = (
        Index('ix_field_document', 'document_id'),
        Index('ix_field_signer', 'signer_id'),
    )


# =============================================================================
# MODELS - SIGNERS
# =============================================================================

class EnvelopeSigner(Base):
    """Signataire d'une enveloppe."""
    __tablename__ = "esignature_envelope_signers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    envelope_id = Column(UniversalUUID(), ForeignKey("esignature_envelopes.id", ondelete="CASCADE"), nullable=False)

    # Identification signataire
    email = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(100), nullable=True)

    # Role
    role = Column(String(50), default="signer")  # signer, approver, cc, witness
    signing_order = Column(Integer, default=1)
    is_required = Column(Boolean, default=True)

    # Authentification
    auth_method = Column(Enum(AuthMethod), default=AuthMethod.EMAIL)
    auth_code = Column(String(20), nullable=True)  # Code OTP si requis
    require_id_verification = Column(Boolean, default=False)

    # Statut
    status = Column(Enum(SignerStatus), default=SignerStatus.PENDING, index=True)
    status_message = Column(Text, nullable=True)

    # Notifications
    notified_at = Column(DateTime, nullable=True)
    notification_count = Column(Integer, default=0)
    last_notification_at = Column(DateTime, nullable=True)

    # Activite
    viewed_at = Column(DateTime, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    delegated_at = Column(DateTime, nullable=True)

    # Info signature
    signature_ip = Column(String(45), nullable=True)
    signature_user_agent = Column(String(500), nullable=True)
    signature_location = Column(String(255), nullable=True)  # Geoloc approximative

    # Delegation
    delegated_to_id = Column(UniversalUUID(), nullable=True)
    delegated_to_email = Column(String(255), nullable=True)
    delegation_reason = Column(Text, nullable=True)

    # Refus
    decline_reason = Column(Text, nullable=True)

    # Token d'acces unique
    access_token = Column(String(255), nullable=True, unique=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Provider externe
    external_id = Column(String(255), nullable=True)
    external_url = Column(Text, nullable=True)  # Lien direct signature

    # Lien utilisateur systeme
    user_id = Column(UniversalUUID(), nullable=True)  # Si signataire interne
    contact_id = Column(UniversalUUID(), nullable=True)  # Si contact CRM

    # Message personnalise
    personal_message = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    envelope = relationship("SignatureEnvelope", back_populates="signers")
    fields = relationship("DocumentField", back_populates="signer")
    actions = relationship("SignerAction", back_populates="signer", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_signer_envelope', 'envelope_id'),
        Index('ix_signer_email', 'tenant_id', 'email'),
        Index('ix_signer_status', 'tenant_id', 'status'),
        Index('ix_signer_token', 'access_token'),
        Index('ix_signer_order', 'envelope_id', 'signing_order'),
    )


class SignerAction(Base):
    """Action effectuee par un signataire (historique)."""
    __tablename__ = "esignature_signer_actions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    signer_id = Column(UniversalUUID(), ForeignKey("esignature_envelope_signers.id", ondelete="CASCADE"), nullable=False)

    # Action
    action = Column(String(50), nullable=False)  # viewed, signed, declined, delegated...
    details = Column(JSON, nullable=True)

    # Contexte
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)

    # Timestamp
    action_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    signer = relationship("EnvelopeSigner", back_populates="actions")

    __table_args__ = (
        Index('ix_action_signer', 'signer_id'),
        Index('ix_action_tenant', 'tenant_id'),
    )


# =============================================================================
# MODELS - AUDIT & CERTIFICATES
# =============================================================================

class SignatureAuditEvent(Base):
    """Evenement d'audit pour une enveloppe."""
    __tablename__ = "esignature_audit_events"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    envelope_id = Column(UniversalUUID(), ForeignKey("esignature_envelopes.id", ondelete="CASCADE"), nullable=False)

    # Evenement
    event_type = Column(Enum(AuditEventType), nullable=False)
    event_description = Column(Text, nullable=True)
    event_data = Column(JSON, nullable=True)

    # Acteur
    actor_type = Column(String(20), nullable=False)  # user, signer, system
    actor_id = Column(UniversalUUID(), nullable=True)
    actor_email = Column(String(255), nullable=True)
    actor_name = Column(String(255), nullable=True)

    # Contexte technique
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(255), nullable=True)

    # Document/Signer concerne
    document_id = Column(UniversalUUID(), nullable=True)
    signer_id = Column(UniversalUUID(), nullable=True)
    field_id = Column(UniversalUUID(), nullable=True)

    # Hash integrite
    event_hash = Column(String(64), nullable=True)  # SHA256 de l'evenement
    previous_hash = Column(String(64), nullable=True)  # Chaine de hash

    # Timestamp
    event_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relations
    envelope = relationship("SignatureEnvelope", back_populates="audit_events")

    __table_args__ = (
        Index('ix_audit_envelope', 'envelope_id'),
        Index('ix_audit_tenant', 'tenant_id', 'event_at'),
        Index('ix_audit_type', 'tenant_id', 'event_type'),
    )


class SignatureCertificate(Base):
    """Certificat de signature (preuve legale)."""
    __tablename__ = "esignature_certificates"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    envelope_id = Column(UniversalUUID(), ForeignKey("esignature_envelopes.id", ondelete="CASCADE"), nullable=False)

    # Numero certificat
    certificate_number = Column(String(100), nullable=False, unique=True)

    # Type
    certificate_type = Column(String(50), nullable=False)  # completion, audit_trail, legal

    # Contenu
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(BigInteger, nullable=False)

    # Horodatage qualifie
    timestamp_authority = Column(String(255), nullable=True)
    timestamp_token = Column(Text, nullable=True)
    timestamped_at = Column(DateTime, nullable=True)

    # Signature serveur
    server_signature = Column(Text, nullable=True)
    signature_algorithm = Column(String(50), nullable=True)

    # Validite
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=True)

    # Verification
    verification_url = Column(Text, nullable=True)
    verification_code = Column(String(50), nullable=True)

    # Audit
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    envelope = relationship("SignatureEnvelope", back_populates="certificates")

    __table_args__ = (
        Index('ix_cert_envelope', 'envelope_id'),
        Index('ix_cert_number', 'certificate_number'),
    )


# =============================================================================
# MODELS - REMINDERS
# =============================================================================

class SignatureReminder(Base):
    """Rappel programme ou envoye."""
    __tablename__ = "esignature_reminders"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    envelope_id = Column(UniversalUUID(), ForeignKey("esignature_envelopes.id", ondelete="CASCADE"), nullable=False)
    signer_id = Column(UniversalUUID(), ForeignKey("esignature_envelope_signers.id", ondelete="SET NULL"), nullable=True)

    # Type
    reminder_type = Column(Enum(ReminderType), default=ReminderType.AUTOMATIC)

    # Planification
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    # Canal
    channel = Column(String(20), default="email")  # email, sms
    recipient_email = Column(String(255), nullable=True)
    recipient_phone = Column(String(20), nullable=True)

    # Message
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=True)

    # Statut
    status = Column(String(20), default="pending")  # pending, sent, failed, cancelled
    error_message = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    envelope = relationship("SignatureEnvelope", back_populates="reminders")

    __table_args__ = (
        Index('ix_reminder_envelope', 'envelope_id'),
        Index('ix_reminder_scheduled', 'tenant_id', 'status', 'scheduled_at'),
    )


# =============================================================================
# MODELS - STATISTICS
# =============================================================================

class SignatureStats(Base):
    """Statistiques agregees par periode."""
    __tablename__ = "esignature_stats"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Periode
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Volumes
    envelopes_created = Column(Integer, default=0)
    envelopes_sent = Column(Integer, default=0)
    envelopes_completed = Column(Integer, default=0)
    envelopes_declined = Column(Integer, default=0)
    envelopes_expired = Column(Integer, default=0)
    envelopes_cancelled = Column(Integer, default=0)

    # Signataires
    total_signers = Column(Integer, default=0)
    signers_signed = Column(Integer, default=0)
    signers_declined = Column(Integer, default=0)

    # Performance
    avg_completion_hours = Column(Float, nullable=True)
    avg_view_to_sign_minutes = Column(Float, nullable=True)

    # Par provider
    by_provider = Column(JSON, default=dict)

    # Par type document
    by_document_type = Column(JSON, default=dict)

    # Par niveau signature
    by_signature_level = Column(JSON, default=dict)

    # Calcule a
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'period_type', 'period_start', name='uq_stats_period'),
        Index('ix_stats_tenant_period', 'tenant_id', 'period_type', 'period_start'),
    )
