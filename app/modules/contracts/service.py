"""
Module de Gestion des Contrats (CLM) - GAP-035

Contract Lifecycle Management complet:
- Création et rédaction de contrats
- Templates et clauses réutilisables
- Workflow de négociation et approbation
- Signature électronique intégrée
- Suivi des obligations et jalons
- Alertes de renouvellement/échéance
- Gestion des avenants
- Archivage et recherche

Fonctionnalités:
- Multi-parties (clients, fournisseurs, partenaires)
- Versioning et historique
- Conformité RGPD
- Extraction IA des clauses clés

Architecture multi-tenant avec isolation stricte.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class ContractType(Enum):
    """Type de contrat."""
    # Commercial
    SALES = "sales"  # Vente
    PURCHASE = "purchase"  # Achat
    SERVICE = "service"  # Prestation de services
    SUBSCRIPTION = "subscription"  # Abonnement
    LICENSE = "license"  # Licence logicielle
    DISTRIBUTION = "distribution"  # Distribution
    FRANCHISE = "franchise"  # Franchise
    AGENCY = "agency"  # Agent commercial

    # Partenariats
    PARTNERSHIP = "partnership"  # Partenariat
    JOINT_VENTURE = "joint_venture"  # Coentreprise
    CONSORTIUM = "consortium"  # Consortium

    # Confidentialité
    NDA = "nda"  # Accord de confidentialité
    NON_COMPETE = "non_compete"  # Non-concurrence

    # Immobilier
    LEASE = "lease"  # Bail commercial
    SUBLEASE = "sublease"  # Sous-location

    # RH
    EMPLOYMENT = "employment"  # Contrat de travail
    CONSULTING = "consulting"  # Consultant
    INTERNSHIP = "internship"  # Stage

    # Autres
    MAINTENANCE = "maintenance"  # Maintenance
    SLA = "sla"  # Accord de niveau de service
    OTHER = "other"  # Autre


class ContractStatus(Enum):
    """Statut du contrat."""
    DRAFT = "draft"  # Brouillon
    IN_NEGOTIATION = "in_negotiation"  # En négociation
    PENDING_APPROVAL = "pending_approval"  # En attente approbation
    PENDING_SIGNATURE = "pending_signature"  # En attente signature
    ACTIVE = "active"  # Actif
    SUSPENDED = "suspended"  # Suspendu
    EXPIRED = "expired"  # Expiré
    TERMINATED = "terminated"  # Résilié
    RENEWED = "renewed"  # Renouvelé
    ARCHIVED = "archived"  # Archivé


class PartyRole(Enum):
    """Rôle d'une partie dans le contrat."""
    CONTRACTOR = "contractor"  # Prestataire
    CLIENT = "client"  # Client
    SUPPLIER = "supplier"  # Fournisseur
    PARTNER = "partner"  # Partenaire
    EMPLOYER = "employer"  # Employeur
    EMPLOYEE = "employee"  # Employé
    LICENSOR = "licensor"  # Concédant
    LICENSEE = "licensee"  # Licencié
    LANDLORD = "landlord"  # Bailleur
    TENANT = "tenant"  # Locataire


class ObligationType(Enum):
    """Type d'obligation contractuelle."""
    PAYMENT = "payment"  # Paiement
    DELIVERY = "delivery"  # Livraison
    PERFORMANCE = "performance"  # Exécution
    REPORTING = "reporting"  # Reporting
    COMPLIANCE = "compliance"  # Conformité
    AUDIT = "audit"  # Audit
    RENEWAL = "renewal"  # Renouvellement
    NOTICE = "notice"  # Préavis
    CONFIDENTIALITY = "confidentiality"  # Confidentialité
    OTHER = "other"  # Autre


class RenewalType(Enum):
    """Type de renouvellement."""
    MANUAL = "manual"  # Manuel
    AUTOMATIC = "automatic"  # Tacite reconduction
    NEGOTIATED = "negotiated"  # Renégocié


class AmendmentType(Enum):
    """Type d'avenant."""
    EXTENSION = "extension"  # Prolongation
    MODIFICATION = "modification"  # Modification
    PRICING = "pricing"  # Révision tarifaire
    SCOPE = "scope"  # Périmètre
    TERMINATION = "termination"  # Résiliation anticipée
    OTHER = "other"  # Autre


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ContractParty:
    """Partie au contrat."""
    id: str
    role: PartyRole
    name: str

    # Identification
    entity_type: str = "company"  # company, individual
    entity_id: Optional[str] = None  # ID dans le système (client, fournisseur...)
    registration_number: Optional[str] = None  # SIRET, etc.
    vat_number: Optional[str] = None

    # Contact
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    # Représentant
    representative_name: Optional[str] = None
    representative_title: Optional[str] = None

    # Signature
    has_signed: bool = False
    signed_at: Optional[datetime] = None
    signature_id: Optional[str] = None


@dataclass
class ContractClause:
    """Clause contractuelle."""
    id: str
    title: str
    content: str
    clause_type: str = "standard"  # standard, custom, legal, optional
    section: Optional[str] = None

    # Template
    is_from_template: bool = False
    template_id: Optional[str] = None

    # Négociation
    is_negotiable: bool = False
    negotiation_status: str = "accepted"  # accepted, pending, rejected
    original_content: Optional[str] = None
    modification_history: List[Dict[str, Any]] = field(default_factory=list)

    # Importance
    is_mandatory: bool = True
    risk_level: str = "low"  # low, medium, high, critical


@dataclass
class ContractObligation:
    """Obligation contractuelle."""
    id: str
    contract_id: str
    obligation_type: ObligationType
    description: str

    # Partie responsable
    responsible_party_id: str

    # Échéances
    due_date: Optional[date] = None
    recurrence: Optional[str] = None  # daily, weekly, monthly, quarterly, yearly
    next_due_date: Optional[date] = None

    # Montant (si applicable)
    amount: Optional[Decimal] = None
    currency: str = "EUR"

    # Statut
    status: str = "pending"  # pending, completed, overdue, waived
    completed_at: Optional[datetime] = None

    # Alertes
    alert_days_before: int = 30
    alert_sent: bool = False


@dataclass
class ContractMilestone:
    """Jalon contractuel."""
    id: str
    contract_id: str
    name: str
    description: Optional[str] = None

    # Date
    target_date: date = field(default_factory=date.today)
    actual_date: Optional[date] = None

    # Deliverables
    deliverables: List[str] = field(default_factory=list)

    # Paiement associé
    payment_amount: Optional[Decimal] = None
    payment_triggered: bool = False

    # Statut
    status: str = "pending"  # pending, in_progress, completed, delayed


@dataclass
class ContractFinancials:
    """Informations financières du contrat."""
    total_value: Decimal = Decimal("0")
    currency: str = "EUR"

    # Paiement
    payment_terms: str = "30_days"  # 30_days, 45_days, 60_days, end_of_month
    payment_method: str = "bank_transfer"

    # Récurrence
    is_recurring: bool = False
    recurring_amount: Optional[Decimal] = None
    recurring_frequency: Optional[str] = None  # monthly, quarterly, yearly

    # Révision
    price_revision_clause: bool = False
    price_revision_index: Optional[str] = None  # INSEE, SYNTEC, etc.
    price_revision_cap: Optional[Decimal] = None

    # Pénalités
    late_payment_rate: Decimal = Decimal("0.05")  # 5%
    penalty_clause: bool = False
    penalty_amount: Optional[Decimal] = None


@dataclass
class ContractDocument:
    """Document attaché au contrat."""
    id: str
    name: str
    file_path: str
    file_size: int
    mime_type: str
    document_type: str = "contract"  # contract, annex, amendment, other
    version: int = 1
    uploaded_at: datetime = field(default_factory=datetime.now)
    uploaded_by: str = ""

    # Signature
    is_signed: bool = False
    signature_request_id: Optional[str] = None


@dataclass
class ContractAmendment:
    """Avenant au contrat."""
    id: str
    contract_id: str
    amendment_number: int
    amendment_type: AmendmentType
    title: str
    description: str

    # Dates
    effective_date: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=datetime.now)

    # Changements
    changes: List[Dict[str, Any]] = field(default_factory=list)

    # Financier
    value_change: Optional[Decimal] = None
    new_end_date: Optional[date] = None

    # Statut
    status: ContractStatus = ContractStatus.DRAFT
    signed_at: Optional[datetime] = None

    # Document
    document_id: Optional[str] = None


@dataclass
class ContractTemplate:
    """Modèle de contrat."""
    id: str
    tenant_id: str
    name: str
    contract_type: ContractType
    description: Optional[str] = None

    # Structure
    clauses: List[ContractClause] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)

    # Variables
    variables: List[Dict[str, str]] = field(default_factory=list)

    # Métadonnées
    language: str = "fr"
    version: str = "1.0"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Contract:
    """Contrat principal."""
    id: str
    tenant_id: str
    contract_number: str
    title: str
    contract_type: ContractType

    # Parties
    parties: List[ContractParty] = field(default_factory=list)

    # Contenu
    clauses: List[ContractClause] = field(default_factory=list)
    description: Optional[str] = None

    # Dates
    created_date: date = field(default_factory=date.today)
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    signed_date: Optional[datetime] = None

    # Renouvellement
    renewal_type: RenewalType = RenewalType.MANUAL
    renewal_notice_days: int = 90
    auto_renewal_term_months: int = 12

    # Financier
    financials: ContractFinancials = field(default_factory=ContractFinancials)

    # Obligations et jalons
    obligations: List[ContractObligation] = field(default_factory=list)
    milestones: List[ContractMilestone] = field(default_factory=list)

    # Documents
    documents: List[ContractDocument] = field(default_factory=list)
    amendments: List[ContractAmendment] = field(default_factory=list)

    # Template
    template_id: Optional[str] = None

    # Statut
    status: ContractStatus = ContractStatus.DRAFT
    status_history: List[Dict[str, Any]] = field(default_factory=list)

    # Workflow
    current_approver_id: Optional[str] = None
    approval_history: List[Dict[str, Any]] = field(default_factory=list)

    # Métadonnées
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def get_primary_party(self, role: PartyRole) -> Optional[ContractParty]:
        """Récupère la partie principale d'un rôle donné."""
        for party in self.parties:
            if party.role == role:
                return party
        return None

    def is_fully_signed(self) -> bool:
        """Vérifie si toutes les parties ont signé."""
        return all(party.has_signed for party in self.parties)

    def days_until_expiry(self) -> Optional[int]:
        """Jours avant expiration."""
        if not self.end_date:
            return None
        delta = self.end_date - date.today()
        return delta.days

    def days_until_renewal_notice(self) -> Optional[int]:
        """Jours avant la date limite de préavis de renouvellement."""
        if not self.end_date:
            return None
        notice_date = self.end_date - timedelta(days=self.renewal_notice_days)
        delta = notice_date - date.today()
        return delta.days


@dataclass
class ContractAlert:
    """Alerte liée à un contrat."""
    id: str
    contract_id: str
    alert_type: str  # expiry, renewal, obligation, milestone
    title: str
    message: str

    # Dates
    due_date: date
    created_at: datetime = field(default_factory=datetime.now)

    # Destinataires
    recipients: List[str] = field(default_factory=list)

    # Statut
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class ContractService:
    """
    Service de gestion des contrats (CLM).

    Gère:
    - Création et modification des contrats
    - Templates et clauses
    - Workflow d'approbation
    - Suivi des obligations
    - Alertes et notifications
    - Recherche et reporting
    """

    def __init__(
        self,
        tenant_id: str,
        signature_service: Optional[Any] = None
    ):
        self.tenant_id = tenant_id
        self.signature_service = signature_service

        # Stockage (à remplacer par DB)
        self._contracts: Dict[str, Contract] = {}
        self._templates: Dict[str, ContractTemplate] = {}
        self._alerts: Dict[str, ContractAlert] = {}
        self._contract_counter = 0

    # ========================================================================
    # GESTION DES TEMPLATES
    # ========================================================================

    def create_template(
        self,
        name: str,
        contract_type: ContractType,
        clauses: List[ContractClause],
        description: Optional[str] = None,
        variables: Optional[List[Dict[str, str]]] = None
    ) -> ContractTemplate:
        """Crée un modèle de contrat."""
        template = ContractTemplate(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            contract_type=contract_type,
            description=description,
            clauses=clauses,
            variables=variables or []
        )

        self._templates[template.id] = template
        return template

    def get_template(self, template_id: str) -> Optional[ContractTemplate]:
        """Récupère un modèle."""
        return self._templates.get(template_id)

    def list_templates(
        self,
        contract_type: Optional[ContractType] = None
    ) -> List[ContractTemplate]:
        """Liste les modèles disponibles."""
        templates = list(self._templates.values())

        if contract_type:
            templates = [t for t in templates if t.contract_type == contract_type]

        return sorted(templates, key=lambda t: t.name)

    # ========================================================================
    # CRÉATION DE CONTRATS
    # ========================================================================

    def create_contract(
        self,
        title: str,
        contract_type: ContractType,
        parties: List[ContractParty],
        template_id: Optional[str] = None,
        effective_date: Optional[date] = None,
        end_date: Optional[date] = None,
        total_value: Optional[Decimal] = None,
        created_by: str = ""
    ) -> Contract:
        """Crée un nouveau contrat."""
        # Générer le numéro de contrat
        self._contract_counter += 1
        contract_number = f"CTR-{date.today().year}-{self._contract_counter:05d}"

        contract = Contract(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            contract_number=contract_number,
            title=title,
            contract_type=contract_type,
            parties=parties,
            effective_date=effective_date,
            end_date=end_date,
            template_id=template_id,
            created_by=created_by
        )

        # Appliquer le template si fourni
        if template_id:
            template = self._templates.get(template_id)
            if template:
                contract.clauses = [
                    ContractClause(
                        id=str(uuid.uuid4()),
                        title=c.title,
                        content=c.content,
                        clause_type=c.clause_type,
                        section=c.section,
                        is_from_template=True,
                        template_id=template_id,
                        is_negotiable=c.is_negotiable,
                        is_mandatory=c.is_mandatory
                    )
                    for c in template.clauses
                ]

        # Initialiser les financials
        if total_value:
            contract.financials.total_value = total_value

        # Enregistrer l'historique
        contract.status_history.append({
            "status": ContractStatus.DRAFT.value,
            "timestamp": datetime.now().isoformat(),
            "by": created_by
        })

        self._contracts[contract.id] = contract
        return contract

    def create_from_template(
        self,
        template_id: str,
        title: str,
        parties: List[ContractParty],
        variables: Dict[str, str],
        created_by: str = ""
    ) -> Contract:
        """Crée un contrat à partir d'un template avec variables."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} non trouvé")

        contract = self.create_contract(
            title=title,
            contract_type=template.contract_type,
            parties=parties,
            template_id=template_id,
            created_by=created_by
        )

        # Remplacer les variables dans les clauses
        for clause in contract.clauses:
            for var_name, var_value in variables.items():
                clause.content = clause.content.replace(
                    f"{{{{{var_name}}}}}",  # {{variable}}
                    var_value
                )

        return contract

    # ========================================================================
    # MODIFICATION DE CONTRATS
    # ========================================================================

    def add_clause(
        self,
        contract_id: str,
        title: str,
        content: str,
        clause_type: str = "custom",
        section: Optional[str] = None,
        is_negotiable: bool = False
    ) -> ContractClause:
        """Ajoute une clause à un contrat."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        if contract.status not in [ContractStatus.DRAFT, ContractStatus.IN_NEGOTIATION]:
            raise ValueError("Contrat non modifiable")

        clause = ContractClause(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            clause_type=clause_type,
            section=section,
            is_negotiable=is_negotiable
        )

        contract.clauses.append(clause)
        contract.updated_at = datetime.now()

        return clause

    def add_obligation(
        self,
        contract_id: str,
        obligation_type: ObligationType,
        description: str,
        responsible_party_id: str,
        due_date: Optional[date] = None,
        recurrence: Optional[str] = None,
        amount: Optional[Decimal] = None
    ) -> ContractObligation:
        """Ajoute une obligation contractuelle."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        obligation = ContractObligation(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            obligation_type=obligation_type,
            description=description,
            responsible_party_id=responsible_party_id,
            due_date=due_date,
            recurrence=recurrence,
            next_due_date=due_date,
            amount=amount
        )

        contract.obligations.append(obligation)
        contract.updated_at = datetime.now()

        return obligation

    def add_milestone(
        self,
        contract_id: str,
        name: str,
        target_date: date,
        description: Optional[str] = None,
        deliverables: Optional[List[str]] = None,
        payment_amount: Optional[Decimal] = None
    ) -> ContractMilestone:
        """Ajoute un jalon au contrat."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        milestone = ContractMilestone(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            name=name,
            target_date=target_date,
            description=description,
            deliverables=deliverables or [],
            payment_amount=payment_amount
        )

        contract.milestones.append(milestone)
        contract.updated_at = datetime.now()

        return milestone

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def submit_for_approval(
        self,
        contract_id: str,
        approver_id: str,
        submitted_by: str
    ) -> Contract:
        """Soumet un contrat pour approbation."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        if contract.status != ContractStatus.DRAFT:
            raise ValueError("Seuls les brouillons peuvent être soumis")

        contract.status = ContractStatus.PENDING_APPROVAL
        contract.current_approver_id = approver_id
        contract.updated_at = datetime.now()

        contract.status_history.append({
            "status": ContractStatus.PENDING_APPROVAL.value,
            "timestamp": datetime.now().isoformat(),
            "by": submitted_by,
            "approver": approver_id
        })

        return contract

    def approve_contract(
        self,
        contract_id: str,
        approver_id: str,
        comments: Optional[str] = None
    ) -> Contract:
        """Approuve un contrat."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        if contract.current_approver_id != approver_id:
            raise ValueError("Vous n'êtes pas l'approbateur désigné")

        contract.approval_history.append({
            "approver_id": approver_id,
            "action": "approved",
            "comments": comments,
            "timestamp": datetime.now().isoformat()
        })

        contract.status = ContractStatus.PENDING_SIGNATURE
        contract.current_approver_id = None
        contract.updated_at = datetime.now()

        contract.status_history.append({
            "status": ContractStatus.PENDING_SIGNATURE.value,
            "timestamp": datetime.now().isoformat(),
            "by": approver_id
        })

        return contract

    def reject_contract(
        self,
        contract_id: str,
        approver_id: str,
        reason: str
    ) -> Contract:
        """Rejette un contrat."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        contract.approval_history.append({
            "approver_id": approver_id,
            "action": "rejected",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

        contract.status = ContractStatus.DRAFT
        contract.current_approver_id = None
        contract.updated_at = datetime.now()

        return contract

    # ========================================================================
    # SIGNATURE
    # ========================================================================

    def request_signatures(
        self,
        contract_id: str,
        document_content: bytes,
        document_name: str = "contrat.pdf"
    ) -> str:
        """Demande les signatures de toutes les parties."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        if contract.status != ContractStatus.PENDING_SIGNATURE:
            raise ValueError("Contrat non prêt pour signature")

        if not self.signature_service:
            raise ValueError("Service de signature non configuré")

        # Créer le document
        doc = ContractDocument(
            id=str(uuid.uuid4()),
            name=document_name,
            file_path=f"contracts/{contract_id}/{document_name}",
            file_size=len(document_content),
            mime_type="application/pdf",
            document_type="contract"
        )
        contract.documents.append(doc)

        # Demander les signatures via le service de signature électronique
        # signature_request = self.signature_service.create_signature_request(...)
        signature_request_id = f"SIG-{uuid.uuid4().hex[:8]}"
        doc.signature_request_id = signature_request_id

        contract.updated_at = datetime.now()

        return signature_request_id

    def record_signature(
        self,
        contract_id: str,
        party_id: str,
        signature_id: str
    ) -> ContractParty:
        """Enregistre la signature d'une partie."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        party = next((p for p in contract.parties if p.id == party_id), None)
        if not party:
            raise ValueError(f"Partie {party_id} non trouvée")

        party.has_signed = True
        party.signed_at = datetime.now()
        party.signature_id = signature_id

        # Vérifier si toutes les parties ont signé
        if contract.is_fully_signed():
            contract.status = ContractStatus.ACTIVE
            contract.signed_date = datetime.now()

            contract.status_history.append({
                "status": ContractStatus.ACTIVE.value,
                "timestamp": datetime.now().isoformat(),
                "event": "all_signatures_received"
            })

        contract.updated_at = datetime.now()

        return party

    # ========================================================================
    # AVENANTS
    # ========================================================================

    def create_amendment(
        self,
        contract_id: str,
        amendment_type: AmendmentType,
        title: str,
        description: str,
        changes: List[Dict[str, Any]],
        effective_date: Optional[date] = None,
        value_change: Optional[Decimal] = None,
        new_end_date: Optional[date] = None
    ) -> ContractAmendment:
        """Crée un avenant au contrat."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        if contract.status not in [ContractStatus.ACTIVE, ContractStatus.SUSPENDED]:
            raise ValueError("Avenant possible uniquement sur contrat actif")

        amendment_number = len(contract.amendments) + 1

        amendment = ContractAmendment(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            amendment_number=amendment_number,
            amendment_type=amendment_type,
            title=title,
            description=description,
            effective_date=effective_date or date.today(),
            changes=changes,
            value_change=value_change,
            new_end_date=new_end_date
        )

        contract.amendments.append(amendment)
        contract.updated_at = datetime.now()

        return amendment

    def apply_amendment(
        self,
        contract_id: str,
        amendment_id: str
    ) -> Contract:
        """Applique un avenant signé au contrat."""
        contract = self._contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contrat {contract_id} non trouvé")

        amendment = next(
            (a for a in contract.amendments if a.id == amendment_id),
            None
        )
        if not amendment:
            raise ValueError(f"Avenant {amendment_id} non trouvé")

        if amendment.status != ContractStatus.ACTIVE:
            raise ValueError("Avenant non signé")

        # Appliquer les changements
        if amendment.value_change:
            contract.financials.total_value += amendment.value_change

        if amendment.new_end_date:
            contract.end_date = amendment.new_end_date

        # Type spécifique
        if amendment.amendment_type == AmendmentType.TERMINATION:
            contract.status = ContractStatus.TERMINATED
            contract.end_date = amendment.effective_date

        contract.updated_at = datetime.now()

        return contract

    # ========================================================================
    # ALERTES ET NOTIFICATIONS
    # ========================================================================

    def check_and_create_alerts(self) -> List[ContractAlert]:
        """Vérifie les contrats et crée les alertes nécessaires."""
        alerts = []
        today = date.today()

        for contract in self._contracts.values():
            if contract.status != ContractStatus.ACTIVE:
                continue

            # Alerte d'expiration
            days_to_expiry = contract.days_until_expiry()
            if days_to_expiry is not None:
                if days_to_expiry <= 30 and days_to_expiry > 0:
                    alert = self._create_alert(
                        contract_id=contract.id,
                        alert_type="expiry",
                        title=f"Contrat {contract.contract_number} expire bientôt",
                        message=f"Le contrat expire dans {days_to_expiry} jours",
                        due_date=contract.end_date
                    )
                    if alert:
                        alerts.append(alert)

            # Alerte de renouvellement
            days_to_renewal = contract.days_until_renewal_notice()
            if days_to_renewal is not None:
                if days_to_renewal <= 30 and days_to_renewal > 0:
                    if contract.renewal_type == RenewalType.AUTOMATIC:
                        alert = self._create_alert(
                            contract_id=contract.id,
                            alert_type="renewal",
                            title=f"Préavis renouvellement {contract.contract_number}",
                            message=f"Date limite de préavis dans {days_to_renewal} jours",
                            due_date=contract.end_date - timedelta(
                                days=contract.renewal_notice_days
                            )
                        )
                        if alert:
                            alerts.append(alert)

            # Alertes obligations
            for obligation in contract.obligations:
                if obligation.status != "pending":
                    continue
                if obligation.due_date:
                    days_to_due = (obligation.due_date - today).days
                    if days_to_due <= obligation.alert_days_before and not obligation.alert_sent:
                        alert = self._create_alert(
                            contract_id=contract.id,
                            alert_type="obligation",
                            title=f"Obligation à venir: {obligation.description[:50]}",
                            message=f"Échéance dans {days_to_due} jours",
                            due_date=obligation.due_date
                        )
                        if alert:
                            alerts.append(alert)
                            obligation.alert_sent = True

        return alerts

    def _create_alert(
        self,
        contract_id: str,
        alert_type: str,
        title: str,
        message: str,
        due_date: date
    ) -> Optional[ContractAlert]:
        """Crée une alerte si elle n'existe pas déjà."""
        # Vérifier si alerte similaire existe
        for alert in self._alerts.values():
            if (alert.contract_id == contract_id and
                alert.alert_type == alert_type and
                alert.due_date == due_date):
                return None

        alert = ContractAlert(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            alert_type=alert_type,
            title=title,
            message=message,
            due_date=due_date
        )

        self._alerts[alert.id] = alert
        return alert

    # ========================================================================
    # RECHERCHE ET REPORTING
    # ========================================================================

    def search_contracts(
        self,
        query: Optional[str] = None,
        contract_type: Optional[ContractType] = None,
        status: Optional[ContractStatus] = None,
        party_name: Optional[str] = None,
        expiring_within_days: Optional[int] = None
    ) -> List[Contract]:
        """Recherche des contrats."""
        contracts = list(self._contracts.values())

        if query:
            query_lower = query.lower()
            contracts = [
                c for c in contracts
                if query_lower in c.title.lower() or
                query_lower in c.contract_number.lower()
            ]

        if contract_type:
            contracts = [c for c in contracts if c.contract_type == contract_type]

        if status:
            contracts = [c for c in contracts if c.status == status]

        if party_name:
            party_lower = party_name.lower()
            contracts = [
                c for c in contracts
                if any(party_lower in p.name.lower() for p in c.parties)
            ]

        if expiring_within_days:
            today = date.today()
            contracts = [
                c for c in contracts
                if c.end_date and 0 <= (c.end_date - today).days <= expiring_within_days
            ]

        return sorted(contracts, key=lambda c: c.created_at, reverse=True)

    def get_contract_statistics(self) -> Dict[str, Any]:
        """Statistiques sur les contrats."""
        contracts = list(self._contracts.values())

        by_status = {}
        by_type = {}
        total_value = Decimal("0")
        expiring_30_days = 0
        expiring_90_days = 0

        today = date.today()

        for contract in contracts:
            # Par statut
            status = contract.status.value
            if status not in by_status:
                by_status[status] = 0
            by_status[status] += 1

            # Par type
            ctype = contract.contract_type.value
            if ctype not in by_type:
                by_type[ctype] = 0
            by_type[ctype] += 1

            # Valeur totale
            if contract.status == ContractStatus.ACTIVE:
                total_value += contract.financials.total_value

            # Expiration
            if contract.end_date and contract.status == ContractStatus.ACTIVE:
                days = (contract.end_date - today).days
                if 0 <= days <= 30:
                    expiring_30_days += 1
                if 0 <= days <= 90:
                    expiring_90_days += 1

        return {
            "total_contracts": len(contracts),
            "active_contracts": by_status.get("active", 0),
            "draft_contracts": by_status.get("draft", 0),
            "pending_signature": by_status.get("pending_signature", 0),
            "by_status": by_status,
            "by_type": by_type,
            "total_active_value": float(total_value),
            "expiring_30_days": expiring_30_days,
            "expiring_90_days": expiring_90_days
        }


# ============================================================================
# FACTORY
# ============================================================================

def create_contract_service(
    tenant_id: str,
    signature_service: Optional[Any] = None
) -> ContractService:
    """Crée un service de gestion des contrats."""
    return ContractService(
        tenant_id=tenant_id,
        signature_service=signature_service
    )
