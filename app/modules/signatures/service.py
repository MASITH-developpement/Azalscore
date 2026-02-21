"""
Service Signatures Électroniques - GAP-058

Gestion des signatures électroniques:
- Signature simple et avancée (eIDAS)
- Workflows multi-signataires
- Intégration Yousign/DocuSign
- Certificats et horodatage
- Audit trail complet
- Validation des signatures
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import hashlib
import json


# ============================================================
# ÉNUMÉRATIONS
# ============================================================

class SignatureLevel(Enum):
    """Niveaux de signature eIDAS."""
    SIMPLE = "simple"  # Signature électronique simple
    ADVANCED = "advanced"  # Signature avancée (AES)
    QUALIFIED = "qualified"  # Signature qualifiée (QES)


class SignatureProvider(Enum):
    """Fournisseurs de signature."""
    INTERNAL = "internal"
    YOUSIGN = "yousign"
    DOCUSIGN = "docusign"
    UNIVERSIGN = "universign"
    ADOBE_SIGN = "adobe_sign"
    SIGNATURIT = "signaturit"


class SignatureStatus(Enum):
    """Statut d'une signature."""
    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    SIGNED = "signed"
    REFUSED = "refused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SignatureRequestStatus(Enum):
    """Statut d'une demande de signature."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SignerRole(Enum):
    """Rôles des signataires."""
    SIGNER = "signer"
    APPROVER = "approver"
    VALIDATOR = "validator"
    WITNESS = "witness"
    COPY = "copy"


class AuthenticationMethod(Enum):
    """Méthodes d'authentification."""
    EMAIL = "email"
    SMS = "sms"
    FRANCE_CONNECT = "france_connect"
    ID_DOCUMENT = "id_document"
    VIDEO = "video"


class FieldType(Enum):
    """Types de champs de signature."""
    SIGNATURE = "signature"
    INITIALS = "initials"
    DATE = "date"
    TEXT = "text"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ProviderConfig:
    """Configuration d'un fournisseur de signature."""
    id: str
    tenant_id: str
    provider: SignatureProvider

    # Credentials
    api_key: str = ""
    api_secret: str = ""
    webhook_secret: str = ""

    # Configuration
    environment: str = "sandbox"  # sandbox, production
    default_level: SignatureLevel = SignatureLevel.ADVANCED
    default_auth_method: AuthenticationMethod = AuthenticationMethod.EMAIL

    # Options
    auto_archive: bool = True
    send_completion_email: bool = True

    # État
    is_active: bool = True
    is_default: bool = False

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


@dataclass
class SignatureField:
    """Champ à signer dans un document."""
    id: str
    field_type: FieldType

    # Position (en % ou pixels)
    page: int = 1
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 50

    # Signataire assigné
    signer_index: int = 0

    # Options
    required: bool = True
    label: Optional[str] = None
    placeholder: Optional[str] = None

    # Pour dropdown
    options: List[str] = field(default_factory=list)


@dataclass
class Signer:
    """Signataire d'un document."""
    id: str
    email: str
    name: str

    # Rôle
    role: SignerRole = SignerRole.SIGNER
    order: int = 1  # Ordre de signature

    # Authentification
    auth_method: AuthenticationMethod = AuthenticationMethod.EMAIL
    phone: Optional[str] = None

    # État
    status: SignatureStatus = SignatureStatus.PENDING

    # Actions
    invitation_sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    refused_at: Optional[datetime] = None
    refusal_reason: Optional[str] = None

    # Métadonnées signature
    signature_ip: Optional[str] = None
    signature_user_agent: Optional[str] = None
    signature_certificate: Optional[str] = None


@dataclass
class Document:
    """Document à signer."""
    id: str
    name: str
    file_path: str
    file_hash: str
    file_size: int

    # Champs de signature
    fields: List[SignatureField] = field(default_factory=list)

    # Document signé
    signed_file_path: Optional[str] = None
    signed_file_hash: Optional[str] = None

    # Métadonnées
    page_count: int = 1
    mime_type: str = "application/pdf"


@dataclass
class SignatureRequest:
    """Demande de signature."""
    id: str
    tenant_id: str
    name: str

    # Documents
    documents: List[Document] = field(default_factory=list)

    # Signataires
    signers: List[Signer] = field(default_factory=list)

    # Configuration
    signature_level: SignatureLevel = SignatureLevel.ADVANCED
    provider: SignatureProvider = SignatureProvider.INTERNAL

    # Expiration
    expires_at: Optional[datetime] = None
    reminder_interval_days: int = 3

    # Messages
    email_subject: Optional[str] = None
    email_message: Optional[str] = None

    # État
    status: SignatureRequestStatus = SignatureRequestStatus.DRAFT

    # Référence externe (Yousign, etc.)
    external_id: Optional[str] = None
    external_url: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_by: Optional[str] = None

    @property
    def all_signed(self) -> bool:
        """Vérifie si tous les signataires ont signé."""
        signers_to_sign = [s for s in self.signers if s.role in (SignerRole.SIGNER, SignerRole.APPROVER)]
        return all(s.status == SignatureStatus.SIGNED for s in signers_to_sign)


@dataclass
class AuditEvent:
    """Événement d'audit."""
    id: str
    request_id: str
    event_type: str  # created, sent, viewed, signed, refused, etc.

    # Acteur
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None

    # Détails
    details: Dict[str, Any] = field(default_factory=dict)

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SignatureValidation:
    """Résultat de validation d'une signature."""
    is_valid: bool
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None

    # Certificat
    certificate_issuer: Optional[str] = None
    certificate_valid_from: Optional[datetime] = None
    certificate_valid_to: Optional[datetime] = None
    certificate_is_trusted: bool = False

    # Horodatage
    timestamp: Optional[datetime] = None
    timestamp_authority: Optional[str] = None

    # Intégrité
    document_modified: bool = False

    # Erreurs
    errors: List[str] = field(default_factory=list)


@dataclass
class Certificate:
    """Certificat de signature."""
    id: str
    tenant_id: str
    name: str

    # Certificat
    certificate_pem: str
    private_key_ref: str  # Référence au secret manager

    # Validité
    valid_from: datetime
    valid_to: datetime

    # Émetteur
    issuer: str
    issuer_organization: str

    # Sujet
    subject: str
    subject_organization: str

    # État
    is_active: bool = True
    is_revoked: bool = False

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class SignatureService:
    """Service de gestion des signatures électroniques."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (à remplacer par DB)
        self._provider_configs: Dict[str, ProviderConfig] = {}
        self._requests: Dict[str, SignatureRequest] = {}
        self._audit_events: List[AuditEvent] = []
        self._certificates: Dict[str, Certificate] = {}

    # ========================================
    # CONFIGURATION PROVIDER
    # ========================================

    def configure_provider(
        self,
        provider: SignatureProvider,
        api_key: str,
        **kwargs
    ) -> ProviderConfig:
        """Configure un fournisseur de signature."""
        config = ProviderConfig(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            provider=provider,
            api_key=api_key,
            api_secret=kwargs.get("api_secret", ""),
            webhook_secret=kwargs.get("webhook_secret", ""),
            environment=kwargs.get("environment", "sandbox"),
            default_level=kwargs.get("default_level", SignatureLevel.ADVANCED),
            default_auth_method=kwargs.get("default_auth_method", AuthenticationMethod.EMAIL),
        )

        self._provider_configs[config.id] = config
        return config

    def get_provider_config(
        self,
        provider: Optional[SignatureProvider] = None
    ) -> Optional[ProviderConfig]:
        """Récupère la configuration d'un provider."""
        for config in self._provider_configs.values():
            if config.tenant_id == self.tenant_id:
                if provider is None or config.provider == provider:
                    if config.is_active:
                        return config
        return None

    def list_provider_configs(self) -> List[ProviderConfig]:
        """Liste les configurations de providers."""
        return [
            c for c in self._provider_configs.values()
            if c.tenant_id == self.tenant_id
        ]

    # ========================================
    # DEMANDES DE SIGNATURE
    # ========================================

    def create_request(
        self,
        name: str,
        documents: List[Dict[str, Any]],
        signers: List[Dict[str, Any]],
        **kwargs
    ) -> SignatureRequest:
        """Crée une demande de signature."""
        # Créer les documents
        doc_objects = []
        for doc in documents:
            doc_obj = Document(
                id=str(uuid4()),
                name=doc["name"],
                file_path=doc["file_path"],
                file_hash=self._compute_hash(doc.get("content", b"")),
                file_size=doc.get("file_size", 0),
                fields=[
                    SignatureField(
                        id=str(uuid4()),
                        field_type=FieldType(f.get("type", "signature")),
                        page=f.get("page", 1),
                        x=f.get("x", 0),
                        y=f.get("y", 0),
                        width=f.get("width", 200),
                        height=f.get("height", 50),
                        signer_index=f.get("signer_index", 0),
                    )
                    for f in doc.get("fields", [])
                ],
            )
            doc_objects.append(doc_obj)

        # Créer les signataires
        signer_objects = []
        for i, signer in enumerate(signers):
            signer_obj = Signer(
                id=str(uuid4()),
                email=signer["email"],
                name=signer["name"],
                role=SignerRole(signer.get("role", "signer")),
                order=signer.get("order", i + 1),
                auth_method=AuthenticationMethod(signer.get("auth_method", "email")),
                phone=signer.get("phone"),
            )
            signer_objects.append(signer_obj)

        # Créer la demande
        request = SignatureRequest(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            documents=doc_objects,
            signers=signer_objects,
            signature_level=SignatureLevel(kwargs.get("signature_level", "advanced")),
            provider=SignatureProvider(kwargs.get("provider", "internal")),
            expires_at=kwargs.get("expires_at"),
            email_subject=kwargs.get("email_subject"),
            email_message=kwargs.get("email_message"),
            created_by=kwargs.get("created_by"),
        )

        self._requests[request.id] = request

        # Audit
        self._log_event(request.id, "created", created_by=kwargs.get("created_by"))

        return request

    def _compute_hash(self, content: bytes) -> str:
        """Calcule le hash SHA-256 d'un contenu."""
        return hashlib.sha256(content).hexdigest()

    def get_request(self, request_id: str) -> Optional[SignatureRequest]:
        """Récupère une demande de signature."""
        request = self._requests.get(request_id)
        if request and request.tenant_id == self.tenant_id:
            return request
        return None

    def list_requests(
        self,
        status: Optional[SignatureRequestStatus] = None,
        created_by: Optional[str] = None,
        limit: int = 50
    ) -> List[SignatureRequest]:
        """Liste les demandes de signature."""
        requests = [
            r for r in self._requests.values()
            if r.tenant_id == self.tenant_id
        ]

        if status:
            requests = [r for r in requests if r.status == status]
        if created_by:
            requests = [r for r in requests if r.created_by == created_by]

        return sorted(requests, key=lambda x: x.created_at, reverse=True)[:limit]

    def send_request(self, request_id: str) -> SignatureRequest:
        """Envoie une demande de signature."""
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Demande {request_id} non trouvée")

        if request.status != SignatureRequestStatus.DRAFT:
            raise ValueError("Seules les demandes en brouillon peuvent être envoyées")

        # Envoyer via le provider
        config = self.get_provider_config(request.provider)

        if request.provider == SignatureProvider.INTERNAL:
            # Envoyer les invitations par email (simulé)
            for signer in request.signers:
                signer.status = SignatureStatus.SENT
                signer.invitation_sent_at = datetime.now()
        else:
            # Appeler l'API externe (simulé)
            request.external_id = f"ext_{request_id}"
            request.external_url = f"https://sign.example.com/{request.external_id}"

            for signer in request.signers:
                signer.status = SignatureStatus.SENT
                signer.invitation_sent_at = datetime.now()

        request.status = SignatureRequestStatus.ACTIVE

        # Audit
        self._log_event(request_id, "sent")

        return request

    def cancel_request(
        self,
        request_id: str,
        reason: Optional[str] = None
    ) -> SignatureRequest:
        """Annule une demande de signature."""
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Demande {request_id} non trouvée")

        if request.status in (SignatureRequestStatus.COMPLETED, SignatureRequestStatus.CANCELLED):
            raise ValueError("Cette demande ne peut pas être annulée")

        request.status = SignatureRequestStatus.CANCELLED
        request.cancelled_at = datetime.now()

        for signer in request.signers:
            if signer.status not in (SignatureStatus.SIGNED, SignatureStatus.REFUSED):
                signer.status = SignatureStatus.CANCELLED

        # Audit
        self._log_event(request_id, "cancelled", details={"reason": reason})

        return request

    # ========================================
    # SIGNATURE
    # ========================================

    def record_view(
        self,
        request_id: str,
        signer_id: str,
        **kwargs
    ) -> Signer:
        """Enregistre la consultation d'un document."""
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Demande {request_id} non trouvée")

        signer = next((s for s in request.signers if s.id == signer_id), None)
        if not signer:
            raise ValueError(f"Signataire {signer_id} non trouvé")

        if signer.viewed_at is None:
            signer.viewed_at = datetime.now()
            signer.status = SignatureStatus.VIEWED

            # Audit
            self._log_event(
                request_id, "viewed",
                actor_email=signer.email,
                actor_name=signer.name,
                actor_ip=kwargs.get("ip"),
                actor_user_agent=kwargs.get("user_agent"),
            )

        return signer

    def sign(
        self,
        request_id: str,
        signer_id: str,
        signature_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Signer:
        """Enregistre la signature d'un document."""
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Demande {request_id} non trouvée")

        signer = next((s for s in request.signers if s.id == signer_id), None)
        if not signer:
            raise ValueError(f"Signataire {signer_id} non trouvé")

        if signer.status == SignatureStatus.SIGNED:
            raise ValueError("Ce signataire a déjà signé")

        if signer.status in (SignatureStatus.REFUSED, SignatureStatus.CANCELLED):
            raise ValueError("Ce signataire ne peut plus signer")

        # Vérifier l'ordre
        for other in request.signers:
            if other.order < signer.order and other.status != SignatureStatus.SIGNED:
                if other.role in (SignerRole.SIGNER, SignerRole.APPROVER):
                    raise ValueError("Des signatures précédentes sont requises")

        signer.signed_at = datetime.now()
        signer.status = SignatureStatus.SIGNED
        signer.signature_ip = kwargs.get("ip")
        signer.signature_user_agent = kwargs.get("user_agent")

        # Audit
        self._log_event(
            request_id, "signed",
            actor_email=signer.email,
            actor_name=signer.name,
            actor_ip=kwargs.get("ip"),
            actor_user_agent=kwargs.get("user_agent"),
        )

        # Vérifier si tous ont signé
        if request.all_signed:
            request.status = SignatureRequestStatus.COMPLETED
            request.completed_at = datetime.now()

            # Générer le document signé
            self._finalize_documents(request)

            # Audit
            self._log_event(request_id, "completed")

        return signer

    def refuse(
        self,
        request_id: str,
        signer_id: str,
        reason: str,
        **kwargs
    ) -> Signer:
        """Enregistre le refus de signature."""
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Demande {request_id} non trouvée")

        signer = next((s for s in request.signers if s.id == signer_id), None)
        if not signer:
            raise ValueError(f"Signataire {signer_id} non trouvé")

        signer.refused_at = datetime.now()
        signer.status = SignatureStatus.REFUSED
        signer.refusal_reason = reason

        # Audit
        self._log_event(
            request_id, "refused",
            actor_email=signer.email,
            actor_name=signer.name,
            details={"reason": reason},
        )

        return signer

    def _finalize_documents(self, request: SignatureRequest) -> None:
        """Finalise les documents signés."""
        for doc in request.documents:
            # En production: appliquer les signatures au PDF
            doc.signed_file_path = f"{doc.file_path}.signed.pdf"
            doc.signed_file_hash = hashlib.sha256(
                f"signed_{doc.file_hash}".encode()
            ).hexdigest()

    # ========================================
    # VALIDATION
    # ========================================

    def validate_signature(
        self,
        file_path: str,
        file_content: Optional[bytes] = None
    ) -> SignatureValidation:
        """Valide les signatures d'un document."""
        # En production: utiliser une librairie de validation PDF/signature

        # Simulation
        validation = SignatureValidation(
            is_valid=True,
            signer_name="Jean Dupont",
            signer_email="jean.dupont@example.com",
            certificate_issuer="AZALSCORE CA",
            certificate_valid_from=datetime.now() - timedelta(days=365),
            certificate_valid_to=datetime.now() + timedelta(days=365),
            certificate_is_trusted=True,
            timestamp=datetime.now(),
            timestamp_authority="AZALSCORE TSA",
            document_modified=False,
        )

        return validation

    # ========================================
    # AUDIT
    # ========================================

    def _log_event(
        self,
        request_id: str,
        event_type: str,
        **kwargs
    ) -> AuditEvent:
        """Enregistre un événement d'audit."""
        event = AuditEvent(
            id=str(uuid4()),
            request_id=request_id,
            event_type=event_type,
            actor_email=kwargs.get("actor_email"),
            actor_name=kwargs.get("actor_name"),
            actor_ip=kwargs.get("actor_ip"),
            actor_user_agent=kwargs.get("actor_user_agent"),
            details=kwargs.get("details", {}),
        )

        self._audit_events.append(event)
        return event

    def get_audit_trail(self, request_id: str) -> List[AuditEvent]:
        """Récupère l'historique d'audit d'une demande."""
        events = [e for e in self._audit_events if e.request_id == request_id]
        return sorted(events, key=lambda x: x.timestamp)

    def export_audit_trail(
        self,
        request_id: str,
        format: str = "json"
    ) -> str:
        """Exporte l'historique d'audit."""
        events = self.get_audit_trail(request_id)

        if format == "json":
            return json.dumps([
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "actor_email": e.actor_email,
                    "actor_name": e.actor_name,
                    "actor_ip": e.actor_ip,
                    "details": e.details,
                }
                for e in events
            ], indent=2, ensure_ascii=False)

        # Format texte
        lines = []
        for e in events:
            lines.append(
                f"{e.timestamp.isoformat()} | {e.event_type} | "
                f"{e.actor_name or 'Système'} ({e.actor_email or '-'})"
            )
        return "\n".join(lines)

    # ========================================
    # STATISTIQUES
    # ========================================

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calcule les statistiques de signature."""
        requests = [
            r for r in self._requests.values()
            if r.tenant_id == self.tenant_id
        ]

        if start_date:
            requests = [r for r in requests if r.created_at >= start_date]
        if end_date:
            requests = [r for r in requests if r.created_at <= end_date]

        completed = [r for r in requests if r.status == SignatureRequestStatus.COMPLETED]
        cancelled = [r for r in requests if r.status == SignatureRequestStatus.CANCELLED]

        # Temps moyen de signature
        signature_times = []
        for r in completed:
            if r.completed_at and r.created_at:
                delta = (r.completed_at - r.created_at).total_seconds() / 3600  # heures
                signature_times.append(delta)

        avg_time = sum(signature_times) / len(signature_times) if signature_times else 0

        return {
            "total_requests": len(requests),
            "completed": len(completed),
            "cancelled": len(cancelled),
            "pending": len(requests) - len(completed) - len(cancelled),
            "completion_rate": (len(completed) / len(requests) * 100) if requests else 0,
            "average_completion_hours": round(avg_time, 1),
            "total_signers": sum(len(r.signers) for r in requests),
            "total_documents": sum(len(r.documents) for r in requests),
        }


# ============================================================
# FACTORY
# ============================================================

def create_signature_service(tenant_id: str) -> SignatureService:
    """Crée une instance du service Signature."""
    return SignatureService(tenant_id=tenant_id)
