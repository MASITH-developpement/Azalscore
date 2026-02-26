"""
Module de Gestion des Appels d'Offres (RFQ/RFP) - GAP-037

Gestion complète des appels d'offres:
- AO entrants (réponse aux marchés)
- AO sortants (consultation fournisseurs)
- Workflow de validation interne
- Gestion documentaire complète
- Scoring et comparaison des offres
- Conformité marchés publics

Conformité:
- Code de la commande publique
- DUME (Document Unique de Marché Européen)
- Signature électronique

Architecture multi-tenant avec isolation stricte.
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class TenderType(Enum):
    """Type d'appel d'offres."""
    # Marchés publics
    OPEN_PROCEDURE = "open_procedure"  # Procédure ouverte
    RESTRICTED_PROCEDURE = "restricted_procedure"  # Procédure restreinte
    COMPETITIVE_DIALOGUE = "competitive_dialogue"  # Dialogue compétitif
    NEGOTIATED_PROCEDURE = "negotiated_procedure"  # Procédure négociée
    DESIGN_CONTEST = "design_contest"  # Concours
    FRAMEWORK_AGREEMENT = "framework_agreement"  # Accord-cadre

    # Marchés privés
    RFQ = "rfq"  # Request for Quotation (devis)
    RFP = "rfp"  # Request for Proposal
    RFI = "rfi"  # Request for Information
    DIRECT_AWARD = "direct_award"  # Gré à gré


class TenderStatus(Enum):
    """Statut de l'appel d'offres."""
    DRAFT = "draft"  # Brouillon
    PUBLISHED = "published"  # Publié
    OPEN = "open"  # Ouvert aux réponses
    CLOSED = "closed"  # Fermé
    EVALUATION = "evaluation"  # En cours d'évaluation
    AWARDED = "awarded"  # Attribué
    CANCELLED = "cancelled"  # Annulé


class BidStatus(Enum):
    """Statut d'une offre."""
    DRAFT = "draft"  # Brouillon
    IN_REVIEW = "in_review"  # En revue interne
    APPROVED = "approved"  # Approuvée
    SUBMITTED = "submitted"  # Soumise
    RECEIVED = "received"  # Reçue (AO sortant)
    SHORTLISTED = "shortlisted"  # Présélectionnée
    AWARDED = "awarded"  # Retenue
    REJECTED = "rejected"  # Rejetée
    WITHDRAWN = "withdrawn"  # Retirée


class CriterionType(Enum):
    """Type de critère d'évaluation."""
    PRICE = "price"  # Prix
    QUALITY = "quality"  # Qualité
    TECHNICAL = "technical"  # Technique
    DELIVERY = "delivery"  # Délai
    ENVIRONMENTAL = "environmental"  # Environnemental
    SOCIAL = "social"  # Social
    INNOVATION = "innovation"  # Innovation
    SERVICE = "service"  # Service
    EXPERIENCE = "experience"  # Expérience
    FINANCIAL = "financial"  # Solidité financière


class DocumentCategory(Enum):
    """Catégorie de document."""
    TENDER_NOTICE = "tender_notice"  # Avis de marché
    SPECIFICATIONS = "specifications"  # Cahier des charges
    TECHNICAL_SPECS = "technical_specs"  # Spécifications techniques
    ADMIN_DOCS = "admin_docs"  # Documents administratifs
    PRICING = "pricing"  # Bordereau de prix
    PROPOSAL = "proposal"  # Offre technique
    FINANCIAL_OFFER = "financial_offer"  # Offre financière
    CERTIFICATE = "certificate"  # Attestation
    DUME = "dume"  # DUME
    CONTRACT = "contract"  # Contrat
    AMENDMENT = "amendment"  # Avenant
    OTHER = "other"  # Autre


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TenderDocument:
    """Document d'appel d'offres."""
    id: str
    name: str
    category: DocumentCategory
    file_path: str
    file_size: int
    mime_type: str

    # Métadonnées
    version: int = 1
    is_mandatory: bool = False
    description: Optional[str] = None

    # Dates
    uploaded_at: datetime = field(default_factory=datetime.now)
    uploaded_by: str = ""

    # Signature
    is_signed: bool = False
    signature_id: Optional[str] = None


@dataclass
class EvaluationCriterion:
    """Critère d'évaluation."""
    id: str
    name: str
    criterion_type: CriterionType
    weight: Decimal  # Pondération en %
    description: Optional[str] = None

    # Notation
    max_score: int = 10
    is_eliminatory: bool = False
    minimum_score: Optional[int] = None

    # Sous-critères
    sub_criteria: List["EvaluationCriterion"] = field(default_factory=list)


@dataclass
class Lot:
    """Lot d'un appel d'offres."""
    id: str
    number: str
    title: str
    description: Optional[str] = None

    # Montant
    estimated_value: Optional[Decimal] = None
    currency: str = "EUR"

    # Quantités
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None

    # Critères spécifiques
    criteria: List[EvaluationCriterion] = field(default_factory=list)

    # Attribution
    is_awarded: bool = False
    awarded_to: Optional[str] = None
    awarded_amount: Optional[Decimal] = None


@dataclass
class Tender:
    """Appel d'offres."""
    id: str
    tenant_id: str
    reference: str
    title: str
    description: str

    # Type et procédure
    tender_type: TenderType
    is_public_procurement: bool = False

    # Dates clés
    publication_date: Optional[date] = None
    questions_deadline: Optional[datetime] = None
    submission_deadline: datetime = field(default_factory=datetime.now)
    opening_date: Optional[datetime] = None

    # Organisation
    contracting_authority: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    # Lots
    lots: List[Lot] = field(default_factory=list)
    allow_partial_bid: bool = True  # Autoriser offre sur lots partiels

    # Documents
    documents: List[TenderDocument] = field(default_factory=list)

    # Critères d'évaluation
    evaluation_criteria: List[EvaluationCriterion] = field(default_factory=list)

    # Montants
    estimated_value: Optional[Decimal] = None
    currency: str = "EUR"
    budget_min: Optional[Decimal] = None
    budget_max: Optional[Decimal] = None

    # Conditions
    warranty_required: bool = False
    warranty_amount: Optional[Decimal] = None
    bid_validity_days: int = 90

    # Statut
    status: TenderStatus = TenderStatus.DRAFT

    # Métadonnées
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    cpv_codes: List[str] = field(default_factory=list)  # Codes CPV

    # Historique
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class BidDocument:
    """Document d'une offre."""
    id: str
    name: str
    category: DocumentCategory
    file_path: str
    file_size: int

    version: int = 1
    uploaded_at: datetime = field(default_factory=datetime.now)

    # Signature
    is_signed: bool = False


@dataclass
class BidLineItem:
    """Ligne de prix d'une offre."""
    id: str
    lot_id: Optional[str] = None
    description: str = ""

    # Quantités et prix
    quantity: Decimal = Decimal("1")
    unit: str = "unité"
    unit_price: Decimal = Decimal("0")
    total_price: Decimal = Decimal("0")

    # Détails
    discount_percent: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("20")

    # Notes
    notes: Optional[str] = None


@dataclass
class BidScore:
    """Score d'évaluation d'une offre."""
    criterion_id: str
    criterion_name: str
    weight: Decimal
    raw_score: int  # Score brut (0-10)
    weighted_score: Decimal  # Score pondéré
    comments: Optional[str] = None
    evaluator_id: str = ""


@dataclass
class Bid:
    """Offre/Réponse à un appel d'offres."""
    id: str
    tenant_id: str
    tender_id: str
    reference: str

    # Soumissionnaire
    bidder_name: str
    bidder_id: Optional[str] = None  # ID fournisseur/client
    bidder_email: Optional[str] = None
    bidder_phone: Optional[str] = None
    bidder_address: Optional[str] = None
    bidder_siret: Optional[str] = None

    # Lots concernés
    lot_ids: List[str] = field(default_factory=list)
    is_global_bid: bool = True  # Offre globale vs par lot

    # Documents
    documents: List[BidDocument] = field(default_factory=list)

    # Prix
    line_items: List[BidLineItem] = field(default_factory=list)
    total_amount: Decimal = Decimal("0")
    currency: str = "EUR"

    # Délais
    delivery_time_days: Optional[int] = None
    validity_days: int = 90
    valid_until: Optional[date] = None

    # Évaluation
    scores: List[BidScore] = field(default_factory=list)
    total_score: Decimal = Decimal("0")
    rank: Optional[int] = None

    # Statut
    status: BidStatus = BidStatus.DRAFT
    submitted_at: Optional[datetime] = None
    received_at: Optional[datetime] = None

    # Workflow interne
    internal_reviewers: List[str] = field(default_factory=list)
    approval_status: str = "pending"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Notes internes
    internal_notes: Optional[str] = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def calculate_total(self):
        """Calcule le montant total."""
        self.total_amount = sum(
            item.total_price for item in self.line_items
        )


@dataclass
class Question:
    """Question sur un appel d'offres."""
    id: str
    tender_id: str
    question_text: str
    asked_by: str
    asked_at: datetime = field(default_factory=datetime.now)

    # Réponse
    answer_text: Optional[str] = None
    answered_by: Optional[str] = None
    answered_at: Optional[datetime] = None

    # Visibilité
    is_public: bool = True  # Visible par tous les candidats
    is_published: bool = False


@dataclass
class TenderAlert:
    """Alerte sur un appel d'offres."""
    id: str
    alert_type: str  # deadline, evaluation, award
    message: str
    due_date: date

    # Références optionnelles
    tender_id: Optional[str] = None
    bid_id: Optional[str] = None

    is_sent: bool = False
    sent_at: Optional[datetime] = None


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class TenderService:
    """
    Service de gestion des appels d'offres.

    Gère:
    - Création et publication d'AO
    - Réception et évaluation des offres
    - Workflow de validation
    - Scoring et attribution
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage (à remplacer par DB)
        self._tenders: Dict[str, Tender] = {}
        self._bids: Dict[str, Bid] = {}
        self._questions: Dict[str, Question] = {}
        self._alerts: Dict[str, TenderAlert] = {}
        self._tender_counter = 0
        self._bid_counter = 0

    # ========================================================================
    # GESTION DES APPELS D'OFFRES
    # ========================================================================

    def create_tender(
        self,
        title: str,
        description: str,
        tender_type: TenderType,
        submission_deadline: datetime,
        estimated_value: Optional[Decimal] = None,
        is_public_procurement: bool = False,
        contracting_authority: Optional[str] = None,
        created_by: str = ""
    ) -> Tender:
        """Crée un nouvel appel d'offres."""
        self._tender_counter += 1
        reference = f"AO-{date.today().year}-{self._tender_counter:05d}"

        tender = Tender(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            reference=reference,
            title=title,
            description=description,
            tender_type=tender_type,
            submission_deadline=submission_deadline,
            estimated_value=estimated_value,
            is_public_procurement=is_public_procurement,
            contracting_authority=contracting_authority,
            created_by=created_by
        )

        self._tenders[tender.id] = tender
        return tender

    def add_lot(
        self,
        tender_id: str,
        number: str,
        title: str,
        description: Optional[str] = None,
        estimated_value: Optional[Decimal] = None,
        quantity: Optional[Decimal] = None,
        unit: Optional[str] = None
    ) -> Lot:
        """Ajoute un lot à l'appel d'offres."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        lot = Lot(
            id=str(uuid.uuid4()),
            number=number,
            title=title,
            description=description,
            estimated_value=estimated_value,
            quantity=quantity,
            unit=unit
        )

        tender.lots.append(lot)
        tender.updated_at = datetime.now()

        return lot

    def add_evaluation_criterion(
        self,
        tender_id: str,
        name: str,
        criterion_type: CriterionType,
        weight: Decimal,
        description: Optional[str] = None,
        is_eliminatory: bool = False,
        minimum_score: Optional[int] = None,
        lot_id: Optional[str] = None
    ) -> EvaluationCriterion:
        """Ajoute un critère d'évaluation."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        criterion = EvaluationCriterion(
            id=str(uuid.uuid4()),
            name=name,
            criterion_type=criterion_type,
            weight=weight,
            description=description,
            is_eliminatory=is_eliminatory,
            minimum_score=minimum_score
        )

        if lot_id:
            # Ajouter au lot spécifique
            for lot in tender.lots:
                if lot.id == lot_id:
                    lot.criteria.append(criterion)
                    break
        else:
            # Ajouter au niveau AO
            tender.evaluation_criteria.append(criterion)

        tender.updated_at = datetime.now()
        return criterion

    def publish_tender(
        self,
        tender_id: str,
        publication_date: Optional[date] = None
    ) -> Tender:
        """Publie un appel d'offres."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        if tender.status != TenderStatus.DRAFT:
            raise ValueError("AO déjà publié")

        # Vérifier les critères obligatoires
        if not tender.evaluation_criteria:
            raise ValueError("Au moins un critère d'évaluation requis")

        total_weight = sum(c.weight for c in tender.evaluation_criteria)
        if total_weight != Decimal("100"):
            raise ValueError(
                f"Total des pondérations doit être 100% (actuel: {total_weight}%)"
            )

        tender.publication_date = publication_date or date.today()
        tender.status = TenderStatus.PUBLISHED
        tender.updated_at = datetime.now()

        return tender

    def open_tender(self, tender_id: str) -> Tender:
        """Ouvre l'AO aux réponses."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        tender.status = TenderStatus.OPEN
        tender.updated_at = datetime.now()

        return tender

    def close_tender(self, tender_id: str) -> Tender:
        """Ferme l'AO aux réponses."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        tender.status = TenderStatus.CLOSED
        tender.updated_at = datetime.now()

        return tender

    # ========================================================================
    # GESTION DES OFFRES
    # ========================================================================

    def create_bid(
        self,
        tender_id: str,
        bidder_name: str,
        bidder_email: Optional[str] = None,
        bidder_id: Optional[str] = None,
        lot_ids: Optional[List[str]] = None,
        created_by: str = ""
    ) -> Bid:
        """Crée une offre pour un appel d'offres."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        self._bid_counter += 1
        reference = f"OFF-{date.today().year}-{self._bid_counter:05d}"

        bid = Bid(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            tender_id=tender_id,
            reference=reference,
            bidder_name=bidder_name,
            bidder_email=bidder_email,
            bidder_id=bidder_id,
            lot_ids=lot_ids or [lot.id for lot in tender.lots],
            is_global_bid=not lot_ids or len(lot_ids) == len(tender.lots),
            valid_until=date.today() + timedelta(days=90),
            created_by=created_by
        )

        self._bids[bid.id] = bid
        return bid

    def add_bid_line_item(
        self,
        bid_id: str,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        unit: str = "unité",
        lot_id: Optional[str] = None,
        discount_percent: Decimal = Decimal("0"),
        vat_rate: Decimal = Decimal("20")
    ) -> BidLineItem:
        """Ajoute une ligne de prix à l'offre."""
        bid = self._bids.get(bid_id)
        if not bid:
            raise ValueError(f"Offre {bid_id} non trouvée")

        # Calculer le total
        subtotal = quantity * unit_price
        discount = subtotal * discount_percent / 100
        total = subtotal - discount

        item = BidLineItem(
            id=str(uuid.uuid4()),
            lot_id=lot_id,
            description=description,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            total_price=total,
            discount_percent=discount_percent,
            vat_rate=vat_rate
        )

        bid.line_items.append(item)
        bid.calculate_total()
        bid.updated_at = datetime.now()

        return item

    def submit_bid(
        self,
        bid_id: str,
        submitted_by: str
    ) -> Bid:
        """Soumet une offre (AO entrant: notre réponse)."""
        bid = self._bids.get(bid_id)
        if not bid:
            raise ValueError(f"Offre {bid_id} non trouvée")

        tender = self._tenders.get(bid.tender_id)
        if not tender:
            raise ValueError("AO non trouvé")

        # Vérifier la date limite
        if datetime.now() > tender.submission_deadline:
            raise ValueError("Date limite de soumission dépassée")

        # Vérifier l'approbation interne
        if bid.approval_status != "approved":
            raise ValueError("Offre non approuvée en interne")

        bid.status = BidStatus.SUBMITTED
        bid.submitted_at = datetime.now()
        bid.updated_at = datetime.now()

        return bid

    def receive_bid(
        self,
        bid_id: str,
        received_by: str
    ) -> Bid:
        """Enregistre la réception d'une offre (AO sortant)."""
        bid = self._bids.get(bid_id)
        if not bid:
            raise ValueError(f"Offre {bid_id} non trouvée")

        bid.status = BidStatus.RECEIVED
        bid.received_at = datetime.now()
        bid.updated_at = datetime.now()

        return bid

    # ========================================================================
    # WORKFLOW INTERNE
    # ========================================================================

    def request_internal_review(
        self,
        bid_id: str,
        reviewer_ids: List[str]
    ) -> Bid:
        """Demande une revue interne de l'offre."""
        bid = self._bids.get(bid_id)
        if not bid:
            raise ValueError(f"Offre {bid_id} non trouvée")

        bid.status = BidStatus.IN_REVIEW
        bid.internal_reviewers = reviewer_ids
        bid.updated_at = datetime.now()

        return bid

    def approve_bid(
        self,
        bid_id: str,
        approver_id: str,
        comments: Optional[str] = None
    ) -> Bid:
        """Approuve une offre en interne."""
        bid = self._bids.get(bid_id)
        if not bid:
            raise ValueError(f"Offre {bid_id} non trouvée")

        bid.status = BidStatus.APPROVED
        bid.approval_status = "approved"
        bid.approved_by = approver_id
        bid.approved_at = datetime.now()
        bid.updated_at = datetime.now()

        if comments:
            bid.internal_notes = (bid.internal_notes or "") + f"\nApprobation: {comments}"

        return bid

    # ========================================================================
    # ÉVALUATION
    # ========================================================================

    def start_evaluation(self, tender_id: str) -> Tender:
        """Démarre l'évaluation des offres."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        tender.status = TenderStatus.EVALUATION
        tender.updated_at = datetime.now()

        return tender

    def score_bid(
        self,
        bid_id: str,
        criterion_id: str,
        score: int,
        evaluator_id: str,
        comments: Optional[str] = None
    ) -> BidScore:
        """Note une offre sur un critère."""
        bid = self._bids.get(bid_id)
        if not bid:
            raise ValueError(f"Offre {bid_id} non trouvée")

        tender = self._tenders.get(bid.tender_id)
        if not tender:
            raise ValueError("AO non trouvé")

        # Trouver le critère
        criterion = None
        for c in tender.evaluation_criteria:
            if c.id == criterion_id:
                criterion = c
                break

        if not criterion:
            raise ValueError(f"Critère {criterion_id} non trouvé")

        # Vérifier le score
        if score < 0 or score > criterion.max_score:
            raise ValueError(
                f"Score doit être entre 0 et {criterion.max_score}"
            )

        # Vérifier le minimum éliminatoire
        if criterion.is_eliminatory and criterion.minimum_score:
            if score < criterion.minimum_score:
                bid.status = BidStatus.REJECTED
                bid.internal_notes = (bid.internal_notes or "") + \
                    f"\nÉliminé: critère {criterion.name} < minimum"

        # Calculer le score pondéré
        weighted_score = (
            Decimal(str(score)) * criterion.weight / criterion.max_score
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        bid_score = BidScore(
            criterion_id=criterion_id,
            criterion_name=criterion.name,
            weight=criterion.weight,
            raw_score=score,
            weighted_score=weighted_score,
            comments=comments,
            evaluator_id=evaluator_id
        )

        # Remplacer si déjà noté par ce critère
        bid.scores = [s for s in bid.scores if s.criterion_id != criterion_id]
        bid.scores.append(bid_score)

        # Recalculer le total
        bid.total_score = sum(s.weighted_score for s in bid.scores)
        bid.updated_at = datetime.now()

        return bid_score

    def rank_bids(self, tender_id: str) -> List[Bid]:
        """Classe les offres par score."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        # Récupérer les offres valides
        bids = [
            b for b in self._bids.values()
            if b.tender_id == tender_id
            and b.status not in [BidStatus.DRAFT, BidStatus.REJECTED, BidStatus.WITHDRAWN]
        ]

        # Trier par score décroissant
        bids.sort(key=lambda b: b.total_score, reverse=True)

        # Attribuer les rangs
        for i, bid in enumerate(bids):
            bid.rank = i + 1

        return bids

    def award_tender(
        self,
        tender_id: str,
        winning_bid_ids: Dict[str, str],  # lot_id -> bid_id
        awarded_by: str
    ) -> Tender:
        """Attribue l'appel d'offres."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        for lot_id, bid_id in winning_bid_ids.items():
            bid = self._bids.get(bid_id)
            if bid:
                bid.status = BidStatus.AWARDED
                bid.updated_at = datetime.now()

                # Marquer le lot comme attribué
                for lot in tender.lots:
                    if lot.id == lot_id:
                        lot.is_awarded = True
                        lot.awarded_to = bid.bidder_name
                        lot.awarded_amount = bid.total_amount
                        break

            # Rejeter les autres offres pour ce lot
            for other_bid in self._bids.values():
                if (other_bid.tender_id == tender_id and
                    other_bid.id != bid_id and
                    lot_id in other_bid.lot_ids and
                    other_bid.status not in [BidStatus.REJECTED, BidStatus.WITHDRAWN]):
                    other_bid.status = BidStatus.REJECTED

        tender.status = TenderStatus.AWARDED
        tender.updated_at = datetime.now()

        return tender

    # ========================================================================
    # QUESTIONS-RÉPONSES
    # ========================================================================

    def ask_question(
        self,
        tender_id: str,
        question_text: str,
        asked_by: str
    ) -> Question:
        """Pose une question sur l'AO."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        # Vérifier la date limite des questions
        if tender.questions_deadline and datetime.now() > tender.questions_deadline:
            raise ValueError("Date limite des questions dépassée")

        question = Question(
            id=str(uuid.uuid4()),
            tender_id=tender_id,
            question_text=question_text,
            asked_by=asked_by
        )

        self._questions[question.id] = question
        return question

    def answer_question(
        self,
        question_id: str,
        answer_text: str,
        answered_by: str,
        publish: bool = True
    ) -> Question:
        """Répond à une question."""
        question = self._questions.get(question_id)
        if not question:
            raise ValueError(f"Question {question_id} non trouvée")

        question.answer_text = answer_text
        question.answered_by = answered_by
        question.answered_at = datetime.now()
        question.is_published = publish

        return question

    # ========================================================================
    # ALERTES
    # ========================================================================

    def check_deadlines(self) -> List[TenderAlert]:
        """Vérifie les échéances et génère les alertes."""
        alerts = []
        today = date.today()

        for tender in self._tenders.values():
            if tender.status not in [TenderStatus.OPEN, TenderStatus.PUBLISHED]:
                continue

            # Alerte de clôture imminente
            days_to_close = (tender.submission_deadline.date() - today).days
            if 0 < days_to_close <= 7:
                alert = TenderAlert(
                    id=str(uuid.uuid4()),
                    tender_id=tender.id,
                    alert_type="deadline",
                    message=f"AO {tender.reference} clôture dans {days_to_close} jours",
                    due_date=tender.submission_deadline.date()
                )
                alerts.append(alert)
                self._alerts[alert.id] = alert

        return alerts

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_tender_summary(self, tender_id: str) -> Dict[str, Any]:
        """Résumé d'un appel d'offres."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        bids = [b for b in self._bids.values() if b.tender_id == tender_id]

        return {
            "reference": tender.reference,
            "title": tender.title,
            "status": tender.status.value,
            "type": tender.tender_type.value,
            "estimated_value": float(tender.estimated_value) if tender.estimated_value else None,
            "lot_count": len(tender.lots),
            "submission_deadline": tender.submission_deadline.isoformat(),
            "bid_count": len(bids),
            "bids_by_status": {
                status.value: len([b for b in bids if b.status == status])
                for status in BidStatus
            },
            "average_bid_amount": float(
                sum(b.total_amount for b in bids) / len(bids)
            ) if bids else 0,
            "lowest_bid": float(min(b.total_amount for b in bids)) if bids else None,
            "highest_bid": float(max(b.total_amount for b in bids)) if bids else None,
        }

    def get_bid_comparison(self, tender_id: str) -> List[Dict[str, Any]]:
        """Comparaison des offres pour un AO."""
        tender = self._tenders.get(tender_id)
        if not tender:
            raise ValueError(f"AO {tender_id} non trouvé")

        bids = self.rank_bids(tender_id)

        comparison = []
        for bid in bids:
            scores_by_criterion = {
                s.criterion_name: {
                    "raw_score": s.raw_score,
                    "weighted_score": float(s.weighted_score)
                }
                for s in bid.scores
            }

            comparison.append({
                "rank": bid.rank,
                "reference": bid.reference,
                "bidder_name": bid.bidder_name,
                "total_amount": float(bid.total_amount),
                "total_score": float(bid.total_score),
                "status": bid.status.value,
                "scores": scores_by_criterion,
                "strengths": bid.strengths,
                "weaknesses": bid.weaknesses,
            })

        return comparison


# ============================================================================
# FACTORY
# ============================================================================

def create_tender_service(tenant_id: str) -> TenderService:
    """Crée un service de gestion des appels d'offres."""
    return TenderService(tenant_id=tenant_id)
