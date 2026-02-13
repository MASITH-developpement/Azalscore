"""
AZALS MODULE - Modèles Signature Électronique
==============================================

Modèles SQLAlchemy pour la gestion des signatures électroniques.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class SignatureProvider(str, enum.Enum):
    """Fournisseur de signature électronique."""
    YOUSIGN = "YOUSIGN"  # Français, eIDAS
    DOCUSIGN = "DOCUSIGN"  # International
    INTERNAL = "INTERNAL"  # Signature interne (test)


class SignatureStatus(str, enum.Enum):
    """Statut d'une demande de signature."""
    DRAFT = "DRAFT"  # Brouillon
    PENDING = "PENDING"  # En attente de signature
    SIGNED = "SIGNED"  # Signé par tous
    PARTIALLY_SIGNED = "PARTIALLY_SIGNED"  # Partiellement signé
    DECLINED = "DECLINED"  # Refusé
    EXPIRED = "EXPIRED"  # Expiré
    CANCELLED = "CANCELLED"  # Annulé
    ERROR = "ERROR"  # Erreur


class SignerStatus(str, enum.Enum):
    """Statut d'un signataire."""
    PENDING = "PENDING"
    NOTIFIED = "NOTIFIED"
    VIEWED = "VIEWED"
    SIGNED = "SIGNED"
    DECLINED = "DECLINED"
    ERROR = "ERROR"


# ============================================================================
# MODELS
# ============================================================================

class SignatureRequest(Base):
    """
    Demande de signature électronique.
    
    Représente une demande de signature pour un ou plusieurs documents,
    avec un ou plusieurs signataires.
    """
    __tablename__ = "esignature_requests"

    # Identifiants
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UniversalUUID, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Référence document source
    document_type = Column(String(50), nullable=False)  # QUOTE, CONTRACT, INVOICE, etc.
    document_id = Column(UniversalUUID, nullable=False, index=True)
    document_number = Column(String(50))
    
    # Fournisseur et référence externe
    provider = Column(Enum(SignatureProvider), nullable=False, default=SignatureProvider.YOUSIGN)
    provider_request_id = Column(String(255), unique=True, index=True)  # ID chez le provider
    
    # Statut et métadonnées
    status = Column(Enum(SignatureStatus), nullable=False, default=SignatureStatus.DRAFT, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    
    # URLs et fichiers
    document_url = Column(String(512))  # URL du document à signer
    signed_document_url = Column(String(512))  # URL du document signé
    
    # Configuration
    expires_at = Column(DateTime, nullable=True)  # Date d'expiration
    send_reminders = Column(Boolean, default=True)  # Envoyer rappels auto
    webhook_url = Column(String(512))  # URL callback
    
    # Métadonnées JSON
    metadata = Column(JSON, default=dict)  # Données additionnelles
    
    # Traçabilité
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID, ForeignKey("users.id"), nullable=True)
    
    # Dates importantes
    sent_at = Column(DateTime)  # Date d'envoi aux signataires
    completed_at = Column(DateTime)  # Date de complétion (tous signés)
    
    # Relations
    signers = relationship("SignatureRequestSigner", back_populates="request", cascade="all, delete-orphan")
    logs = relationship("SignatureLog", back_populates="request", cascade="all, delete-orphan")
    
    # Index
    __table_args__ = (
        Index("idx_esign_req_tenant_status", "tenant_id", "status"),
        Index("idx_esign_req_document", "tenant_id", "document_type", "document_id"),
    )

    def __repr__(self):
        return f"<SignatureRequest {self.id} - {self.status}>"


class SignatureRequestSigner(Base):
    """
    Signataire d'une demande de signature.
    
    Un ou plusieurs signataires peuvent être associés à une demande.
    """
    __tablename__ = "esignature_signers"

    # Identifiants
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    request_id = Column(UniversalUUID, ForeignKey("esignature_requests.id"), nullable=False, index=True)
    tenant_id = Column(UniversalUUID, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Informations signataire
    email = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    
    # Position dans l'ordre de signature
    signing_order = Column(Integer, default=1)  # Ordre de signature (1, 2, 3...)
    
    # Statut et URLs
    status = Column(Enum(SignerStatus), nullable=False, default=SignerStatus.PENDING, index=True)
    signature_url = Column(String(512))  # URL pour signer
    provider_signer_id = Column(String(255))  # ID signataire chez le provider
    
    # Dates
    notified_at = Column(DateTime)  # Date d'envoi email
    viewed_at = Column(DateTime)  # Date de consultation
    signed_at = Column(DateTime)  # Date de signature
    declined_at = Column(DateTime)  # Date de refus
    
    # Raison refus
    decline_reason = Column(Text)
    
    # Métadonnées
    metadata = Column(JSON, default=dict)
    
    # Traçabilité
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    request = relationship("SignatureRequest", back_populates="signers")
    
    # Index
    __table_args__ = (
        Index("idx_esign_signer_email", "tenant_id", "email"),
    )

    def __repr__(self):
        return f"<SignatureRequestSigner {self.email} - {self.status}>"


class SignatureLog(Base):
    """
    Journal d'audit des événements de signature.
    
    Traçabilité complète de tous les événements liés aux signatures.
    """
    __tablename__ = "esignature_logs"

    # Identifiants
    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    request_id = Column(UniversalUUID, ForeignKey("esignature_requests.id"), nullable=False, index=True)
    tenant_id = Column(UniversalUUID, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Événement
    event_type = Column(String(50), nullable=False, index=True)  # created, sent, viewed, signed, etc.
    event_source = Column(String(50))  # webhook, api, manual
    
    # Détails
    description = Column(Text)
    metadata = Column(JSON, default=dict)
    
    # Utilisateur/Signataire concerné
    user_id = Column(UniversalUUID, ForeignKey("users.id"), nullable=True)
    signer_email = Column(String(255))
    
    # IP et user agent (pour audit)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    
    # Traçabilité
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relations
    request = relationship("SignatureRequest", back_populates="logs")
    
    # Index
    __table_args__ = (
        Index("idx_esign_log_tenant_event", "tenant_id", "event_type"),
    )

    def __repr__(self):
        return f"<SignatureLog {self.event_type} - {self.created_at}>"
