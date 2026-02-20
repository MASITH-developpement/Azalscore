"""
Module de Gestion des Réclamations Clients - GAP-038

Gestion complète du cycle de vie des réclamations:
- Enregistrement multi-canal (email, téléphone, web, courrier)
- Classification et priorisation automatique
- Workflow de traitement avec SLA
- Escalade automatique
- Compensation et gestes commerciaux
- Analyse des causes racines
- Reporting et KPIs qualité

Conformité:
- ISO 10002 (Satisfaction client)
- RGPD (données personnelles)
- Médiation de la consommation

Architecture multi-tenant avec isolation stricte.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class ComplaintChannel(Enum):
    """Canal de réception de la réclamation."""
    EMAIL = "email"
    PHONE = "phone"
    WEB_FORM = "web_form"
    CHAT = "chat"
    SOCIAL_MEDIA = "social_media"
    LETTER = "letter"
    IN_PERSON = "in_person"
    MOBILE_APP = "mobile_app"


class ComplaintCategory(Enum):
    """Catégorie de réclamation."""
    PRODUCT_QUALITY = "product_quality"  # Qualité produit
    PRODUCT_DEFECT = "product_defect"  # Produit défectueux
    DELIVERY = "delivery"  # Livraison
    BILLING = "billing"  # Facturation
    PRICING = "pricing"  # Tarification
    SERVICE = "service"  # Service client
    COMMUNICATION = "communication"  # Communication
    WEBSITE = "website"  # Site web/app
    CONTRACT = "contract"  # Contrat
    RETURNS = "returns"  # Retours
    WARRANTY = "warranty"  # Garantie
    GDPR = "gdpr"  # Données personnelles
    OTHER = "other"  # Autre


class ComplaintPriority(Enum):
    """Priorité de la réclamation."""
    LOW = "low"  # Basse
    MEDIUM = "medium"  # Moyenne
    HIGH = "high"  # Haute
    CRITICAL = "critical"  # Critique


class ComplaintStatus(Enum):
    """Statut de la réclamation."""
    NEW = "new"  # Nouvelle
    ACKNOWLEDGED = "acknowledged"  # Accusé réception envoyé
    IN_PROGRESS = "in_progress"  # En cours de traitement
    PENDING_INFO = "pending_info"  # En attente d'informations
    PENDING_CUSTOMER = "pending_customer"  # En attente client
    ESCALATED = "escalated"  # Escaladée
    RESOLVED = "resolved"  # Résolue
    CLOSED = "closed"  # Clôturée
    REOPENED = "reopened"  # Réouverte


class ResolutionType(Enum):
    """Type de résolution."""
    EXPLANATION = "explanation"  # Explication fournie
    REFUND = "refund"  # Remboursement
    REPLACEMENT = "replacement"  # Remplacement
    REPAIR = "repair"  # Réparation
    CREDIT_NOTE = "credit_note"  # Avoir
    COMMERCIAL_GESTURE = "commercial_gesture"  # Geste commercial
    COMPENSATION = "compensation"  # Compensation
    APOLOGY = "apology"  # Excuses
    NO_ACTION = "no_action"  # Pas d'action (réclamation non fondée)
    ESCALATED_EXTERNAL = "escalated_external"  # Escalade externe


class EscalationLevel(Enum):
    """Niveau d'escalade."""
    LEVEL_1 = "level_1"  # Agent
    LEVEL_2 = "level_2"  # Superviseur
    LEVEL_3 = "level_3"  # Manager
    LEVEL_4 = "level_4"  # Direction
    LEGAL = "legal"  # Juridique
    MEDIATOR = "mediator"  # Médiateur


class SatisfactionRating(Enum):
    """Note de satisfaction."""
    VERY_DISSATISFIED = 1
    DISSATISFIED = 2
    NEUTRAL = 3
    SATISFIED = 4
    VERY_SATISFIED = 5


# ============================================================================
# CONFIGURATION SLA
# ============================================================================

DEFAULT_SLA_CONFIG = {
    ComplaintPriority.LOW: {
        "acknowledgment_hours": 48,
        "resolution_hours": 240,  # 10 jours
        "escalation_hours": 168,  # 7 jours
    },
    ComplaintPriority.MEDIUM: {
        "acknowledgment_hours": 24,
        "resolution_hours": 120,  # 5 jours
        "escalation_hours": 72,  # 3 jours
    },
    ComplaintPriority.HIGH: {
        "acknowledgment_hours": 4,
        "resolution_hours": 48,  # 2 jours
        "escalation_hours": 24,
    },
    ComplaintPriority.CRITICAL: {
        "acknowledgment_hours": 1,
        "resolution_hours": 24,
        "escalation_hours": 4,
    },
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Customer:
    """Client à l'origine de la réclamation."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    # Identifiants
    customer_number: Optional[str] = None
    account_id: Optional[str] = None

    # Historique
    total_complaints: int = 0
    is_vip: bool = False
    customer_since: Optional[date] = None

    # RGPD
    gdpr_consent: bool = True
    anonymize_requested: bool = False


@dataclass
class ComplaintAttachment:
    """Pièce jointe à la réclamation."""
    id: str
    name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = field(default_factory=datetime.now)
    uploaded_by: str = ""
    description: Optional[str] = None


@dataclass
class ComplaintNote:
    """Note/commentaire sur la réclamation."""
    id: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    is_internal: bool = True  # Non visible par le client
    note_type: str = "note"  # note, action, decision


@dataclass
class ComplaintAction:
    """Action entreprise sur la réclamation."""
    id: str
    action_type: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    # Planification
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_completed: bool = False

    # Assignation
    assigned_to: Optional[str] = None


@dataclass
class Resolution:
    """Résolution de la réclamation."""
    id: str
    resolution_type: ResolutionType
    description: str
    resolved_at: datetime = field(default_factory=datetime.now)
    resolved_by: str = ""

    # Compensation
    compensation_amount: Decimal = Decimal("0")
    compensation_type: Optional[str] = None  # refund, credit, voucher
    credit_note_id: Optional[str] = None
    voucher_code: Optional[str] = None

    # Validation
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Communication
    response_sent: bool = False
    response_sent_at: Optional[datetime] = None


@dataclass
class Escalation:
    """Escalade de la réclamation."""
    id: str
    level: EscalationLevel
    escalated_at: datetime = field(default_factory=datetime.now)
    escalated_by: str = ""
    reason: str = ""

    # Assignation
    assigned_to: Optional[str] = None
    accepted_at: Optional[datetime] = None

    # Résolution
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


@dataclass
class SLAStatus:
    """Statut SLA de la réclamation."""
    acknowledgment_due: datetime
    resolution_due: datetime
    escalation_due: datetime

    acknowledgment_met: Optional[bool] = None
    resolution_met: Optional[bool] = None
    is_breached: bool = False

    acknowledgment_at: Optional[datetime] = None
    resolution_at: Optional[datetime] = None


@dataclass
class CustomerFeedback:
    """Feedback client après résolution."""
    id: str
    complaint_id: str
    rating: SatisfactionRating
    comments: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.now)

    # Détails
    would_recommend: Optional[bool] = None
    resolution_fair: Optional[bool] = None
    response_time_ok: Optional[bool] = None


@dataclass
class Complaint:
    """Réclamation client."""
    id: str
    tenant_id: str
    reference: str

    # Client
    customer: Customer

    # Détails (champs requis)
    subject: str
    description: str
    category: ComplaintCategory

    # Références optionnelles
    order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    product_id: Optional[str] = None

    # Priorité
    priority: ComplaintPriority = ComplaintPriority.MEDIUM

    # Canal
    channel: ComplaintChannel = ComplaintChannel.EMAIL
    original_message: Optional[str] = None

    # Statut
    status: ComplaintStatus = ComplaintStatus.NEW
    current_owner_id: Optional[str] = None
    team_id: Optional[str] = None

    # SLA
    sla_status: Optional[SLAStatus] = None

    # Dates
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Contenu
    attachments: List[ComplaintAttachment] = field(default_factory=list)
    notes: List[ComplaintNote] = field(default_factory=list)
    actions: List[ComplaintAction] = field(default_factory=list)

    # Escalade
    escalations: List[Escalation] = field(default_factory=list)
    current_escalation_level: EscalationLevel = EscalationLevel.LEVEL_1

    # Résolution
    resolution: Optional[Resolution] = None

    # Feedback
    feedback: Optional[CustomerFeedback] = None

    # Analyse
    root_cause: Optional[str] = None
    root_cause_category: Optional[str] = None
    corrective_actions: List[str] = field(default_factory=list)

    # Tags et classification
    tags: List[str] = field(default_factory=list)
    sentiment: Optional[str] = None  # positive, neutral, negative

    # Métadonnées
    created_by: str = ""
    source_system: Optional[str] = None

    def is_sla_breached(self) -> bool:
        """Vérifie si le SLA est en dépassement."""
        if not self.sla_status:
            return False
        now = datetime.now()
        if self.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            if now > self.sla_status.resolution_due:
                return True
        return self.sla_status.is_breached


@dataclass
class ComplaintTemplate:
    """Modèle de réponse."""
    id: str
    tenant_id: str
    name: str
    category: ComplaintCategory
    subject: str
    body: str
    language: str = "fr"
    is_active: bool = True
    variables: List[str] = field(default_factory=list)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class ComplaintService:
    """
    Service de gestion des réclamations.

    Gère:
    - Enregistrement et classification
    - Workflow de traitement
    - SLA et escalade
    - Résolution et compensation
    - Analyse et reporting
    """

    def __init__(
        self,
        tenant_id: str,
        sla_config: Optional[Dict] = None
    ):
        self.tenant_id = tenant_id
        self.sla_config = sla_config or DEFAULT_SLA_CONFIG

        # Stockage (à remplacer par DB)
        self._complaints: Dict[str, Complaint] = {}
        self._templates: Dict[str, ComplaintTemplate] = {}
        self._complaint_counter = 0

    # ========================================================================
    # CRÉATION DE RÉCLAMATIONS
    # ========================================================================

    def create_complaint(
        self,
        customer: Customer,
        subject: str,
        description: str,
        category: ComplaintCategory,
        channel: ComplaintChannel = ComplaintChannel.EMAIL,
        priority: Optional[ComplaintPriority] = None,
        order_id: Optional[str] = None,
        product_id: Optional[str] = None,
        attachments: Optional[List[ComplaintAttachment]] = None,
        created_by: str = ""
    ) -> Complaint:
        """Crée une nouvelle réclamation."""
        self._complaint_counter += 1
        reference = f"REC-{date.today().year}-{self._complaint_counter:06d}"

        # Auto-déterminer la priorité si non fournie
        if not priority:
            priority = self._auto_prioritize(customer, category, description)

        complaint = Complaint(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            reference=reference,
            customer=customer,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            channel=channel,
            order_id=order_id,
            product_id=product_id,
            attachments=attachments or [],
            created_by=created_by
        )

        # Calculer les SLA
        complaint.sla_status = self._calculate_sla(priority)

        # Analyser le sentiment
        complaint.sentiment = self._analyze_sentiment(description)

        # Incrémenter le compteur client
        customer.total_complaints += 1

        self._complaints[complaint.id] = complaint
        return complaint

    def _auto_prioritize(
        self,
        customer: Customer,
        category: ComplaintCategory,
        description: str
    ) -> ComplaintPriority:
        """Détermine automatiquement la priorité."""
        # Client VIP = haute priorité
        if customer.is_vip:
            return ComplaintPriority.HIGH

        # Réclamations RGPD = critique
        if category == ComplaintCategory.GDPR:
            return ComplaintPriority.CRITICAL

        # Mots-clés urgents
        urgent_keywords = [
            "urgent", "immédiat", "avocat", "juridique", "plainte",
            "médiation", "litige", "scandale", "réseaux sociaux"
        ]
        description_lower = description.lower()
        if any(kw in description_lower for kw in urgent_keywords):
            return ComplaintPriority.HIGH

        # Client récurrent = priorité élevée
        if customer.total_complaints >= 3:
            return ComplaintPriority.HIGH

        # Catégories sensibles
        if category in [ComplaintCategory.PRODUCT_DEFECT, ComplaintCategory.BILLING]:
            return ComplaintPriority.MEDIUM

        return ComplaintPriority.MEDIUM

    def _calculate_sla(self, priority: ComplaintPriority) -> SLAStatus:
        """Calcule les délais SLA."""
        config = self.sla_config.get(priority, self.sla_config[ComplaintPriority.MEDIUM])
        now = datetime.now()

        return SLAStatus(
            acknowledgment_due=now + timedelta(hours=config["acknowledgment_hours"]),
            resolution_due=now + timedelta(hours=config["resolution_hours"]),
            escalation_due=now + timedelta(hours=config["escalation_hours"])
        )

    def _analyze_sentiment(self, text: str) -> str:
        """Analyse le sentiment du texte."""
        text_lower = text.lower()

        negative_words = [
            "inacceptable", "scandaleux", "honteux", "inadmissible",
            "furieux", "déçu", "mécontent", "catastrophe", "nul",
            "arnaque", "vol", "menteur", "incompétent"
        ]

        positive_words = [
            "merci", "satisfait", "content", "bien", "correct"
        ]

        negative_count = sum(1 for w in negative_words if w in text_lower)
        positive_count = sum(1 for w in positive_words if w in text_lower)

        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        return "neutral"

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def acknowledge_complaint(
        self,
        complaint_id: str,
        acknowledged_by: str,
        send_notification: bool = True
    ) -> Complaint:
        """Accuse réception de la réclamation."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        complaint.status = ComplaintStatus.ACKNOWLEDGED
        complaint.acknowledged_at = datetime.now()
        complaint.updated_at = datetime.now()

        # Vérifier le SLA
        if complaint.sla_status:
            complaint.sla_status.acknowledgment_at = datetime.now()
            complaint.sla_status.acknowledgment_met = (
                datetime.now() <= complaint.sla_status.acknowledgment_due
            )

        # Ajouter une note
        note = ComplaintNote(
            id=str(uuid.uuid4()),
            content="Accusé de réception envoyé",
            created_by=acknowledged_by,
            note_type="action"
        )
        complaint.notes.append(note)

        return complaint

    def assign_complaint(
        self,
        complaint_id: str,
        owner_id: str,
        team_id: Optional[str] = None,
        assigned_by: str = ""
    ) -> Complaint:
        """Assigne la réclamation à un agent."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        previous_owner = complaint.current_owner_id
        complaint.current_owner_id = owner_id
        complaint.team_id = team_id
        complaint.status = ComplaintStatus.IN_PROGRESS
        complaint.updated_at = datetime.now()

        # Ajouter une note
        note = ComplaintNote(
            id=str(uuid.uuid4()),
            content=f"Assignée à {owner_id}" +
                    (f" (précédent: {previous_owner})" if previous_owner else ""),
            created_by=assigned_by,
            note_type="action"
        )
        complaint.notes.append(note)

        return complaint

    def add_note(
        self,
        complaint_id: str,
        content: str,
        created_by: str,
        is_internal: bool = True,
        note_type: str = "note"
    ) -> ComplaintNote:
        """Ajoute une note à la réclamation."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        note = ComplaintNote(
            id=str(uuid.uuid4()),
            content=content,
            created_by=created_by,
            is_internal=is_internal,
            note_type=note_type
        )

        complaint.notes.append(note)
        complaint.updated_at = datetime.now()

        return note

    def request_information(
        self,
        complaint_id: str,
        requested_by: str,
        information_needed: str
    ) -> Complaint:
        """Met la réclamation en attente d'informations."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        complaint.status = ComplaintStatus.PENDING_INFO
        complaint.updated_at = datetime.now()

        note = ComplaintNote(
            id=str(uuid.uuid4()),
            content=f"Information demandée: {information_needed}",
            created_by=requested_by,
            note_type="action"
        )
        complaint.notes.append(note)

        return complaint

    # ========================================================================
    # ESCALADE
    # ========================================================================

    def escalate_complaint(
        self,
        complaint_id: str,
        level: EscalationLevel,
        reason: str,
        escalated_by: str,
        assign_to: Optional[str] = None
    ) -> Escalation:
        """Escalade la réclamation."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        escalation = Escalation(
            id=str(uuid.uuid4()),
            level=level,
            escalated_by=escalated_by,
            reason=reason,
            assigned_to=assign_to
        )

        complaint.escalations.append(escalation)
        complaint.current_escalation_level = level
        complaint.status = ComplaintStatus.ESCALATED
        complaint.updated_at = datetime.now()

        # Augmenter la priorité si escalade niveau 3+
        if level in [EscalationLevel.LEVEL_3, EscalationLevel.LEVEL_4, EscalationLevel.LEGAL]:
            if complaint.priority != ComplaintPriority.CRITICAL:
                complaint.priority = ComplaintPriority.HIGH

        return escalation

    def check_auto_escalation(self) -> List[Complaint]:
        """Vérifie et effectue les escalades automatiques."""
        escalated = []
        now = datetime.now()

        for complaint in self._complaints.values():
            if complaint.status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
                continue

            if not complaint.sla_status:
                continue

            # Escalade si délai dépassé
            if now > complaint.sla_status.escalation_due:
                if complaint.current_escalation_level == EscalationLevel.LEVEL_1:
                    self.escalate_complaint(
                        complaint.id,
                        EscalationLevel.LEVEL_2,
                        "Escalade automatique - SLA dépassé",
                        "system"
                    )
                    escalated.append(complaint)

        return escalated

    # ========================================================================
    # RÉSOLUTION
    # ========================================================================

    def resolve_complaint(
        self,
        complaint_id: str,
        resolution_type: ResolutionType,
        description: str,
        resolved_by: str,
        compensation_amount: Decimal = Decimal("0"),
        compensation_type: Optional[str] = None,
        requires_approval: bool = False
    ) -> Resolution:
        """Résout la réclamation."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        resolution = Resolution(
            id=str(uuid.uuid4()),
            resolution_type=resolution_type,
            description=description,
            resolved_by=resolved_by,
            compensation_amount=compensation_amount,
            compensation_type=compensation_type,
            requires_approval=requires_approval
        )

        complaint.resolution = resolution
        complaint.resolved_at = datetime.now()
        complaint.updated_at = datetime.now()

        # Si pas d'approbation requise, passer en résolu
        if not requires_approval:
            complaint.status = ComplaintStatus.RESOLVED

            # Vérifier le SLA
            if complaint.sla_status:
                complaint.sla_status.resolution_at = datetime.now()
                complaint.sla_status.resolution_met = (
                    datetime.now() <= complaint.sla_status.resolution_due
                )

        return resolution

    def approve_resolution(
        self,
        complaint_id: str,
        approved_by: str
    ) -> Complaint:
        """Approuve une résolution en attente."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        if not complaint.resolution:
            raise ValueError("Pas de résolution à approuver")

        complaint.resolution.approved_by = approved_by
        complaint.resolution.approved_at = datetime.now()
        complaint.status = ComplaintStatus.RESOLVED
        complaint.updated_at = datetime.now()

        return complaint

    def close_complaint(
        self,
        complaint_id: str,
        closed_by: str,
        root_cause: Optional[str] = None,
        corrective_actions: Optional[List[str]] = None
    ) -> Complaint:
        """Clôture définitivement la réclamation."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        if complaint.status != ComplaintStatus.RESOLVED:
            raise ValueError("Réclamation doit être résolue avant clôture")

        complaint.status = ComplaintStatus.CLOSED
        complaint.closed_at = datetime.now()
        complaint.root_cause = root_cause
        complaint.corrective_actions = corrective_actions or []
        complaint.updated_at = datetime.now()

        return complaint

    def reopen_complaint(
        self,
        complaint_id: str,
        reason: str,
        reopened_by: str
    ) -> Complaint:
        """Réouvre une réclamation clôturée."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        complaint.status = ComplaintStatus.REOPENED
        complaint.resolved_at = None
        complaint.closed_at = None
        complaint.resolution = None
        complaint.updated_at = datetime.now()

        note = ComplaintNote(
            id=str(uuid.uuid4()),
            content=f"Réouverture: {reason}",
            created_by=reopened_by,
            note_type="action"
        )
        complaint.notes.append(note)

        return complaint

    # ========================================================================
    # FEEDBACK CLIENT
    # ========================================================================

    def record_feedback(
        self,
        complaint_id: str,
        rating: SatisfactionRating,
        comments: Optional[str] = None,
        would_recommend: Optional[bool] = None,
        resolution_fair: Optional[bool] = None
    ) -> CustomerFeedback:
        """Enregistre le feedback client."""
        complaint = self._complaints.get(complaint_id)
        if not complaint:
            raise ValueError(f"Réclamation {complaint_id} non trouvée")

        feedback = CustomerFeedback(
            id=str(uuid.uuid4()),
            complaint_id=complaint_id,
            rating=rating,
            comments=comments,
            would_recommend=would_recommend,
            resolution_fair=resolution_fair
        )

        complaint.feedback = feedback
        complaint.updated_at = datetime.now()

        return feedback

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(
        self,
        name: str,
        category: ComplaintCategory,
        subject: str,
        body: str,
        language: str = "fr"
    ) -> ComplaintTemplate:
        """Crée un modèle de réponse."""
        # Extraire les variables {{variable}}
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', body)

        template = ComplaintTemplate(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            category=category,
            subject=subject,
            body=body,
            language=language,
            variables=list(set(variables))
        )

        self._templates[template.id] = template
        return template

    def render_template(
        self,
        template_id: str,
        variables: Dict[str, str]
    ) -> Dict[str, str]:
        """Rend un template avec les variables."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        subject = template.subject
        body = template.body

        for var_name, var_value in variables.items():
            subject = subject.replace(f"{{{{{var_name}}}}}", var_value)
            body = body.replace(f"{{{{{var_name}}}}}", var_value)

        return {"subject": subject, "body": body}

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Statistiques des réclamations."""
        complaints = list(self._complaints.values())

        if start_date:
            complaints = [
                c for c in complaints
                if c.created_at.date() >= start_date
            ]
        if end_date:
            complaints = [
                c for c in complaints
                if c.created_at.date() <= end_date
            ]

        total = len(complaints)
        if total == 0:
            return {"total": 0}

        # Par statut
        by_status = {}
        for status in ComplaintStatus:
            by_status[status.value] = len([
                c for c in complaints if c.status == status
            ])

        # Par catégorie
        by_category = {}
        for cat in ComplaintCategory:
            count = len([c for c in complaints if c.category == cat])
            if count > 0:
                by_category[cat.value] = count

        # Par priorité
        by_priority = {}
        for priority in ComplaintPriority:
            by_priority[priority.value] = len([
                c for c in complaints if c.priority == priority
            ])

        # Par canal
        by_channel = {}
        for channel in ComplaintChannel:
            count = len([c for c in complaints if c.channel == channel])
            if count > 0:
                by_channel[channel.value] = count

        # SLA
        resolved = [c for c in complaints if c.status in [
            ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED
        ]]
        sla_met = len([
            c for c in resolved
            if c.sla_status and c.sla_status.resolution_met
        ])
        sla_rate = (sla_met / len(resolved) * 100) if resolved else 0

        # Temps moyen de résolution
        resolution_times = []
        for c in resolved:
            if c.resolved_at and c.created_at:
                delta = c.resolved_at - c.created_at
                resolution_times.append(delta.total_seconds() / 3600)

        avg_resolution_hours = (
            sum(resolution_times) / len(resolution_times)
            if resolution_times else 0
        )

        # Satisfaction
        ratings = [
            c.feedback.rating.value
            for c in complaints
            if c.feedback
        ]
        avg_satisfaction = sum(ratings) / len(ratings) if ratings else 0

        return {
            "total": total,
            "by_status": by_status,
            "by_category": by_category,
            "by_priority": by_priority,
            "by_channel": by_channel,
            "resolved_count": len(resolved),
            "sla_compliance_rate": round(sla_rate, 1),
            "average_resolution_hours": round(avg_resolution_hours, 1),
            "average_satisfaction": round(avg_satisfaction, 2),
            "escalation_rate": round(
                len([c for c in complaints if c.escalations]) / total * 100, 1
            ),
            "reopening_rate": round(
                len([c for c in complaints if c.status == ComplaintStatus.REOPENED]) / total * 100, 1
            )
        }

    def get_root_cause_analysis(self) -> Dict[str, int]:
        """Analyse des causes racines."""
        causes = {}

        for complaint in self._complaints.values():
            if complaint.root_cause:
                cause = complaint.root_cause
                if cause not in causes:
                    causes[cause] = 0
                causes[cause] += 1

        return dict(sorted(causes.items(), key=lambda x: x[1], reverse=True))

    def search_complaints(
        self,
        query: Optional[str] = None,
        status: Optional[ComplaintStatus] = None,
        category: Optional[ComplaintCategory] = None,
        priority: Optional[ComplaintPriority] = None,
        customer_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        sla_breached: Optional[bool] = None
    ) -> List[Complaint]:
        """Recherche des réclamations."""
        results = list(self._complaints.values())

        if query:
            query_lower = query.lower()
            results = [
                c for c in results
                if query_lower in c.subject.lower()
                or query_lower in c.description.lower()
                or query_lower in c.reference.lower()
            ]

        if status:
            results = [c for c in results if c.status == status]

        if category:
            results = [c for c in results if c.category == category]

        if priority:
            results = [c for c in results if c.priority == priority]

        if customer_id:
            results = [c for c in results if c.customer.id == customer_id]

        if owner_id:
            results = [c for c in results if c.current_owner_id == owner_id]

        if sla_breached is not None:
            results = [c for c in results if c.is_sla_breached() == sla_breached]

        return sorted(results, key=lambda c: c.created_at, reverse=True)


# ============================================================================
# FACTORY
# ============================================================================

def create_complaint_service(
    tenant_id: str,
    sla_config: Optional[Dict] = None
) -> ComplaintService:
    """Crée un service de gestion des réclamations."""
    return ComplaintService(
        tenant_id=tenant_id,
        sla_config=sla_config
    )
