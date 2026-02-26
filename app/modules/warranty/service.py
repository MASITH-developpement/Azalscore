"""
Module de Gestion des Garanties Produits - GAP-039

Gestion complète du cycle de vie des garanties:
- Garantie légale de conformité (2 ans)
- Garantie commerciale
- Extensions de garantie
- Demandes SAV et réparations
- Remplacements et remboursements
- Provisions comptables

Conformité:
- Code de la consommation (L217-3 à L217-14)
- Garantie légale de conformité (2 ans)
- Garantie des vices cachés
- Directive européenne 2019/771

Architecture multi-tenant avec isolation stricte.
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class WarrantyType(Enum):
    """Type de garantie."""
    LEGAL_CONFORMITY = "legal_conformity"  # Garantie légale de conformité (2 ans)
    LEGAL_HIDDEN_DEFECTS = "legal_hidden_defects"  # Garantie vices cachés
    COMMERCIAL = "commercial"  # Garantie commerciale constructeur
    EXTENDED = "extended"  # Extension de garantie
    ACCIDENTAL_DAMAGE = "accidental_damage"  # Casse/dommage accidentel
    THEFT = "theft"  # Vol


class WarrantyStatus(Enum):
    """Statut de la garantie."""
    ACTIVE = "active"  # Active
    EXPIRED = "expired"  # Expirée
    SUSPENDED = "suspended"  # Suspendue
    VOIDED = "voided"  # Annulée
    CLAIMED = "claimed"  # Réclamée (épuisée)


class ClaimStatus(Enum):
    """Statut d'une demande de garantie."""
    SUBMITTED = "submitted"  # Soumise
    UNDER_REVIEW = "under_review"  # En cours d'examen
    APPROVED = "approved"  # Approuvée
    REJECTED = "rejected"  # Rejetée
    IN_REPAIR = "in_repair"  # En réparation
    PENDING_PARTS = "pending_parts"  # En attente de pièces
    REPAIRED = "repaired"  # Réparé
    REPLACED = "replaced"  # Remplacé
    REFUNDED = "refunded"  # Remboursé
    CLOSED = "closed"  # Clôturée


class ClaimResolution(Enum):
    """Type de résolution."""
    REPAIR = "repair"  # Réparation
    REPLACEMENT_SAME = "replacement_same"  # Remplacement identique
    REPLACEMENT_EQUIVALENT = "replacement_equivalent"  # Remplacement équivalent
    REFUND_FULL = "refund_full"  # Remboursement intégral
    REFUND_PARTIAL = "refund_partial"  # Remboursement partiel
    NO_ACTION = "no_action"  # Pas d'action (hors garantie)


class DefectType(Enum):
    """Type de défaut."""
    MANUFACTURING = "manufacturing"  # Défaut de fabrication
    MATERIAL = "material"  # Défaut de matériau
    DESIGN = "design"  # Défaut de conception
    SOFTWARE = "software"  # Défaut logiciel
    WEAR = "wear"  # Usure normale
    MISUSE = "misuse"  # Mauvaise utilisation
    ACCIDENTAL = "accidental"  # Accident
    UNKNOWN = "unknown"  # Inconnu


# ============================================================================
# CONSTANTES LÉGALES
# ============================================================================

# Durées légales (France)
LEGAL_WARRANTY_DURATION_MONTHS = 24  # Garantie légale de conformité
HIDDEN_DEFECTS_DURATION_YEARS = 2  # Délai pour vices cachés après découverte
REPAIR_MAX_DAYS = 30  # Délai max réparation sous garantie

# Conditions d'application
WARRANTY_EXCLUSIONS = [
    "usure_normale",
    "mauvaise_utilisation",
    "modification_non_autorisee",
    "accident",
    "negligence",
    "dommage_volontaire",
    "catastrophe_naturelle",
    "non_respect_instructions",
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Product:
    """Produit sous garantie."""
    id: str
    name: str
    sku: str
    serial_number: Optional[str] = None

    # Catégorie
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None

    # Prix
    purchase_price: Decimal = Decimal("0")
    currency: str = "EUR"

    # Dates
    purchase_date: Optional[date] = None
    delivery_date: Optional[date] = None


@dataclass
class Customer:
    """Client propriétaire."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    customer_number: Optional[str] = None


@dataclass
class WarrantyTerms:
    """Conditions de garantie."""
    coverage_description: str
    inclusions: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    # Limites
    max_claims: Optional[int] = None
    max_claim_amount: Optional[Decimal] = None
    deductible: Decimal = Decimal("0")


@dataclass
class Warranty:
    """Garantie produit."""
    id: str
    tenant_id: str
    warranty_number: str

    # Type
    warranty_type: WarrantyType

    # Produit et client (champs requis)
    product: Product
    customer: Customer

    # Statut
    status: WarrantyStatus = WarrantyStatus.ACTIVE

    # Durée
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    duration_months: int = 24

    # Conditions
    terms: Optional[WarrantyTerms] = None

    # Prix (extensions)
    price: Decimal = Decimal("0")
    is_paid: bool = True

    # Documents
    proof_of_purchase_id: Optional[str] = None
    warranty_certificate_id: Optional[str] = None

    # Utilisation
    claims_count: int = 0
    total_claimed_amount: Decimal = Decimal("0")

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    notes: Optional[str] = None

    def is_active(self) -> bool:
        """Vérifie si la garantie est active."""
        if self.status != WarrantyStatus.ACTIVE:
            return False
        today = date.today()
        return self.start_date <= today <= self.end_date

    def days_remaining(self) -> int:
        """Jours restants de garantie."""
        if not self.is_active():
            return 0
        delta = self.end_date - date.today()
        return max(0, delta.days)


@dataclass
class ClaimDocument:
    """Document de la demande."""
    id: str
    name: str
    file_path: str
    document_type: str  # photo, video, receipt, report
    uploaded_at: datetime = field(default_factory=datetime.now)


@dataclass
class RepairDetail:
    """Détails de réparation."""
    technician_id: Optional[str] = None
    technician_name: Optional[str] = None
    repair_center: Optional[str] = None

    # Dates
    received_date: Optional[date] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    return_date: Optional[date] = None

    # Travaux
    diagnosis: Optional[str] = None
    work_performed: Optional[str] = None
    parts_replaced: List[Dict[str, Any]] = field(default_factory=list)

    # Coûts (internes)
    labor_cost: Decimal = Decimal("0")
    parts_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")


@dataclass
class WarrantyClaim:
    """Demande de garantie."""
    id: str
    tenant_id: str
    claim_number: str
    warranty_id: str

    # Statut
    status: ClaimStatus = ClaimStatus.SUBMITTED

    # Description du problème
    defect_type: DefectType = DefectType.UNKNOWN
    defect_description: str = ""
    occurrence_date: Optional[date] = None

    # Documents
    documents: List[ClaimDocument] = field(default_factory=list)

    # Réparation
    repair: Optional[RepairDetail] = None

    # Résolution
    resolution: Optional[ClaimResolution] = None
    resolution_description: Optional[str] = None
    resolution_date: Optional[datetime] = None

    # Remplacement
    replacement_product_id: Optional[str] = None
    replacement_serial_number: Optional[str] = None

    # Remboursement
    refund_amount: Decimal = Decimal("0")
    refund_reason: Optional[str] = None

    # Rejet
    rejection_reason: Optional[str] = None

    # Coûts
    claim_cost: Decimal = Decimal("0")

    # Dates
    submitted_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Assignation
    assigned_to: Optional[str] = None

    # Notes
    internal_notes: List[str] = field(default_factory=list)
    customer_communications: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WarrantyExtension:
    """Extension de garantie."""
    id: str
    warranty_id: str
    extension_type: str  # standard, premium, accidental

    # Durée
    additional_months: int
    new_end_date: date

    # Prix
    price: Decimal
    currency: str = "EUR"

    # Dates
    purchased_at: datetime = field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None


@dataclass
class WarrantyProvision:
    """Provision pour garantie (comptabilité)."""
    id: str
    tenant_id: str
    period: str  # YYYY-MM

    # Montants
    opening_balance: Decimal = Decimal("0")
    provisions_added: Decimal = Decimal("0")
    claims_charged: Decimal = Decimal("0")
    reversals: Decimal = Decimal("0")
    closing_balance: Decimal = Decimal("0")

    # Statistiques
    warranties_active: int = 0
    claims_count: int = 0
    average_claim_cost: Decimal = Decimal("0")

    calculated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class WarrantyService:
    """
    Service de gestion des garanties.

    Gère:
    - Enregistrement des garanties
    - Demandes SAV
    - Réparations et remplacements
    - Extensions de garantie
    - Provisions comptables
    """

    def __init__(
        self,
        tenant_id: str,
        default_warranty_months: int = 24
    ):
        self.tenant_id = tenant_id
        self.default_warranty_months = default_warranty_months

        # Stockage (à remplacer par DB)
        self._warranties: Dict[str, Warranty] = {}
        self._claims: Dict[str, WarrantyClaim] = {}
        self._extensions: Dict[str, WarrantyExtension] = {}
        self._provisions: Dict[str, WarrantyProvision] = {}
        self._warranty_counter = 0
        self._claim_counter = 0

    # ========================================================================
    # GESTION DES GARANTIES
    # ========================================================================

    def register_warranty(
        self,
        product: Product,
        customer: Customer,
        warranty_type: WarrantyType = WarrantyType.LEGAL_CONFORMITY,
        duration_months: Optional[int] = None,
        start_date: Optional[date] = None,
        terms: Optional[WarrantyTerms] = None,
        proof_of_purchase_id: Optional[str] = None,
        created_by: str = ""
    ) -> Warranty:
        """Enregistre une nouvelle garantie."""
        self._warranty_counter += 1
        warranty_number = f"GAR-{date.today().year}-{self._warranty_counter:06d}"

        # Durée par défaut selon le type
        if duration_months is None:
            if warranty_type == WarrantyType.LEGAL_CONFORMITY:
                duration_months = LEGAL_WARRANTY_DURATION_MONTHS
            else:
                duration_months = self.default_warranty_months

        # Date de début
        if start_date is None:
            start_date = product.purchase_date or date.today()

        # Date de fin
        end_date = start_date + timedelta(days=duration_months * 30)

        # Conditions par défaut
        if terms is None:
            terms = WarrantyTerms(
                coverage_description="Garantie standard",
                exclusions=WARRANTY_EXCLUSIONS
            )

        warranty = Warranty(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            warranty_number=warranty_number,
            warranty_type=warranty_type,
            product=product,
            customer=customer,
            start_date=start_date,
            end_date=end_date,
            duration_months=duration_months,
            terms=terms,
            proof_of_purchase_id=proof_of_purchase_id,
            created_by=created_by
        )

        self._warranties[warranty.id] = warranty
        return warranty

    def register_legal_warranty(
        self,
        product: Product,
        customer: Customer,
        purchase_date: date,
        proof_of_purchase_id: Optional[str] = None
    ) -> Warranty:
        """Enregistre la garantie légale de conformité."""
        terms = WarrantyTerms(
            coverage_description=(
                "Garantie légale de conformité - Code de la consommation "
                "articles L217-3 à L217-14"
            ),
            inclusions=[
                "Défauts de conformité existants à la livraison",
                "Défauts apparaissant dans les 24 mois suivant la livraison "
                "(présumés exister au moment de la livraison)"
            ],
            exclusions=[
                "Défauts résultant de matériaux fournis par le consommateur",
                "Défauts dont le consommateur avait connaissance",
                "Défauts résultant de l'utilisation anormale"
            ],
            limitations=[
                "Réparation ou remplacement sans frais",
                "À défaut, réduction du prix ou résolution du contrat"
            ]
        )

        product.purchase_date = purchase_date

        return self.register_warranty(
            product=product,
            customer=customer,
            warranty_type=WarrantyType.LEGAL_CONFORMITY,
            duration_months=LEGAL_WARRANTY_DURATION_MONTHS,
            start_date=purchase_date,
            terms=terms,
            proof_of_purchase_id=proof_of_purchase_id
        )

    def check_warranty_status(
        self,
        warranty_id: str
    ) -> Dict[str, Any]:
        """Vérifie le statut d'une garantie."""
        warranty = self._warranties.get(warranty_id)
        if not warranty:
            raise ValueError(f"Garantie {warranty_id} non trouvée")

        today = date.today()
        is_active = warranty.is_active()
        days_remaining = warranty.days_remaining()

        # Vérifier si des claims sont en cours
        active_claims = [
            c for c in self._claims.values()
            if c.warranty_id == warranty_id
            and c.status not in [ClaimStatus.CLOSED, ClaimStatus.REJECTED]
        ]

        return {
            "warranty_id": warranty_id,
            "warranty_number": warranty.warranty_number,
            "status": warranty.status.value,
            "is_active": is_active,
            "start_date": warranty.start_date.isoformat(),
            "end_date": warranty.end_date.isoformat(),
            "days_remaining": days_remaining,
            "claims_count": warranty.claims_count,
            "active_claims": len(active_claims),
            "product": {
                "name": warranty.product.name,
                "serial_number": warranty.product.serial_number
            },
            "customer": warranty.customer.name
        }

    def extend_warranty(
        self,
        warranty_id: str,
        additional_months: int,
        extension_type: str = "standard",
        price: Decimal = Decimal("0")
    ) -> WarrantyExtension:
        """Étend une garantie existante."""
        warranty = self._warranties.get(warranty_id)
        if not warranty:
            raise ValueError(f"Garantie {warranty_id} non trouvée")

        if warranty.status != WarrantyStatus.ACTIVE:
            raise ValueError("Seules les garanties actives peuvent être étendues")

        # Calculer la nouvelle date de fin
        new_end_date = warranty.end_date + timedelta(days=additional_months * 30)

        extension = WarrantyExtension(
            id=str(uuid.uuid4()),
            warranty_id=warranty_id,
            extension_type=extension_type,
            additional_months=additional_months,
            new_end_date=new_end_date,
            price=price
        )

        # Mettre à jour la garantie
        warranty.end_date = new_end_date
        warranty.duration_months += additional_months

        self._extensions[extension.id] = extension
        return extension

    def expire_warranties(self) -> List[Warranty]:
        """Expire les garanties dépassées."""
        expired = []
        today = date.today()

        for warranty in self._warranties.values():
            if warranty.status == WarrantyStatus.ACTIVE:
                if warranty.end_date < today:
                    warranty.status = WarrantyStatus.EXPIRED
                    expired.append(warranty)

        return expired

    # ========================================================================
    # DEMANDES DE GARANTIE
    # ========================================================================

    def submit_claim(
        self,
        warranty_id: str,
        defect_type: DefectType,
        defect_description: str,
        occurrence_date: Optional[date] = None,
        documents: Optional[List[ClaimDocument]] = None,
        submitted_by: str = ""
    ) -> WarrantyClaim:
        """Soumet une demande de garantie."""
        warranty = self._warranties.get(warranty_id)
        if not warranty:
            raise ValueError(f"Garantie {warranty_id} non trouvée")

        # Vérifier que la garantie est active
        if not warranty.is_active():
            raise ValueError(
                f"Garantie non active (statut: {warranty.status.value}, "
                f"fin: {warranty.end_date})"
            )

        # Vérifier les limites
        if warranty.terms and warranty.terms.max_claims:
            if warranty.claims_count >= warranty.terms.max_claims:
                raise ValueError("Nombre maximum de réclamations atteint")

        self._claim_counter += 1
        claim_number = f"SAV-{date.today().year}-{self._claim_counter:06d}"

        claim = WarrantyClaim(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            claim_number=claim_number,
            warranty_id=warranty_id,
            defect_type=defect_type,
            defect_description=defect_description,
            occurrence_date=occurrence_date or date.today(),
            documents=documents or []
        )

        self._claims[claim.id] = claim
        warranty.claims_count += 1

        return claim

    def review_claim(
        self,
        claim_id: str,
        reviewed_by: str,
        approved: bool,
        rejection_reason: Optional[str] = None,
        notes: Optional[str] = None
    ) -> WarrantyClaim:
        """Examine une demande de garantie."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvée")

        claim.reviewed_at = datetime.now()
        claim.assigned_to = reviewed_by

        if approved:
            claim.status = ClaimStatus.APPROVED
        else:
            claim.status = ClaimStatus.REJECTED
            claim.rejection_reason = rejection_reason

        if notes:
            claim.internal_notes.append(f"[{datetime.now()}] {reviewed_by}: {notes}")

        return claim

    def start_repair(
        self,
        claim_id: str,
        repair_center: str,
        technician_name: Optional[str] = None,
        diagnosis: Optional[str] = None
    ) -> WarrantyClaim:
        """Démarre la réparation."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvée")

        if claim.status != ClaimStatus.APPROVED:
            raise ValueError("La demande doit être approuvée")

        claim.status = ClaimStatus.IN_REPAIR
        claim.repair = RepairDetail(
            repair_center=repair_center,
            technician_name=technician_name,
            received_date=date.today(),
            start_date=date.today(),
            diagnosis=diagnosis
        )

        return claim

    def complete_repair(
        self,
        claim_id: str,
        work_performed: str,
        parts_replaced: Optional[List[Dict[str, Any]]] = None,
        labor_cost: Decimal = Decimal("0"),
        parts_cost: Decimal = Decimal("0")
    ) -> WarrantyClaim:
        """Termine la réparation."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvée")

        if not claim.repair:
            raise ValueError("Pas de réparation en cours")

        claim.repair.completion_date = date.today()
        claim.repair.work_performed = work_performed
        claim.repair.parts_replaced = parts_replaced or []
        claim.repair.labor_cost = labor_cost
        claim.repair.parts_cost = parts_cost
        claim.repair.total_cost = labor_cost + parts_cost

        claim.status = ClaimStatus.REPAIRED
        claim.resolution = ClaimResolution.REPAIR
        claim.claim_cost = claim.repair.total_cost

        return claim

    def process_replacement(
        self,
        claim_id: str,
        replacement_product_id: str,
        replacement_serial_number: Optional[str] = None,
        is_equivalent: bool = False,
        replacement_cost: Decimal = Decimal("0")
    ) -> WarrantyClaim:
        """Traite un remplacement."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvée")

        claim.replacement_product_id = replacement_product_id
        claim.replacement_serial_number = replacement_serial_number
        claim.status = ClaimStatus.REPLACED
        claim.resolution = (
            ClaimResolution.REPLACEMENT_EQUIVALENT if is_equivalent
            else ClaimResolution.REPLACEMENT_SAME
        )
        claim.resolution_date = datetime.now()
        claim.claim_cost = replacement_cost

        return claim

    def process_refund(
        self,
        claim_id: str,
        refund_amount: Decimal,
        is_full_refund: bool = True,
        refund_reason: Optional[str] = None
    ) -> WarrantyClaim:
        """Traite un remboursement."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvée")

        warranty = self._warranties.get(claim.warranty_id)
        if not warranty:
            raise ValueError("Garantie non trouvée")

        # Vérifier le montant max
        if warranty.terms and warranty.terms.max_claim_amount:
            if refund_amount > warranty.terms.max_claim_amount:
                raise ValueError(
                    f"Montant dépasse le maximum autorisé: "
                    f"{warranty.terms.max_claim_amount}"
                )

        claim.refund_amount = refund_amount
        claim.refund_reason = refund_reason
        claim.status = ClaimStatus.REFUNDED
        claim.resolution = (
            ClaimResolution.REFUND_FULL if is_full_refund
            else ClaimResolution.REFUND_PARTIAL
        )
        claim.resolution_date = datetime.now()
        claim.claim_cost = refund_amount

        warranty.total_claimed_amount += refund_amount

        return claim

    def close_claim(
        self,
        claim_id: str,
        resolution_description: Optional[str] = None
    ) -> WarrantyClaim:
        """Clôture une demande."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvée")

        claim.status = ClaimStatus.CLOSED
        claim.closed_at = datetime.now()
        claim.resolution_description = resolution_description

        return claim

    # ========================================================================
    # PROVISIONS COMPTABLES
    # ========================================================================

    def calculate_provisions(
        self,
        period: str  # YYYY-MM
    ) -> WarrantyProvision:
        """Calcule les provisions pour garantie."""
        # Obtenir la provision précédente
        previous_period = self._get_previous_period(period)
        previous_provision = self._provisions.get(
            f"{self.tenant_id}_{previous_period}"
        )
        opening_balance = (
            previous_provision.closing_balance if previous_provision
            else Decimal("0")
        )

        # Calculer les nouvelles provisions
        # Méthode: % du CA * taux de sinistralité historique
        active_warranties = [
            w for w in self._warranties.values()
            if w.status == WarrantyStatus.ACTIVE
        ]

        # Calculer le taux de sinistralité
        total_warranties = len(self._warranties)
        total_claims = len(self._claims)
        claim_rate = (
            total_claims / total_warranties if total_warranties > 0
            else Decimal("0.05")  # 5% par défaut
        )

        # Coût moyen des réclamations
        claim_costs = [
            c.claim_cost for c in self._claims.values()
            if c.claim_cost > 0
        ]
        avg_claim_cost = (
            sum(claim_costs) / len(claim_costs) if claim_costs
            else Decimal("50")  # 50€ par défaut
        )

        # Provision = nombre garanties actives * taux sinistralité * coût moyen
        provisions_added = (
            Decimal(str(len(active_warranties))) *
            Decimal(str(claim_rate)) *
            avg_claim_cost
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Réclamations du mois
        year, month = period.split("-")
        claims_this_month = [
            c for c in self._claims.values()
            if c.closed_at and c.closed_at.year == int(year)
            and c.closed_at.month == int(month)
        ]
        claims_charged = sum(c.claim_cost for c in claims_this_month)

        # Calcul du solde
        closing_balance = (
            opening_balance + provisions_added - claims_charged
        )

        provision = WarrantyProvision(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            period=period,
            opening_balance=opening_balance,
            provisions_added=provisions_added,
            claims_charged=claims_charged,
            closing_balance=closing_balance,
            warranties_active=len(active_warranties),
            claims_count=len(claims_this_month),
            average_claim_cost=avg_claim_cost
        )

        self._provisions[f"{self.tenant_id}_{period}"] = provision
        return provision

    def _get_previous_period(self, period: str) -> str:
        """Retourne la période précédente."""
        year, month = period.split("-")
        year = int(year)
        month = int(month)

        if month == 1:
            return f"{year - 1}-12"
        return f"{year}-{month - 1:02d}"

    def generate_accounting_entries(
        self,
        provision: WarrantyProvision
    ) -> List[Dict[str, Any]]:
        """Génère les écritures comptables pour les provisions."""
        entries = []

        # Dotation aux provisions
        if provision.provisions_added > 0:
            entries.append({
                "account": "681500",  # Dotations provisions charges
                "debit": float(provision.provisions_added),
                "credit": 0,
                "label": f"Dotation provision garantie {provision.period}"
            })
            entries.append({
                "account": "158000",  # Provisions pour charges
                "debit": 0,
                "credit": float(provision.provisions_added),
                "label": f"Dotation provision garantie {provision.period}"
            })

        # Reprise de provisions (si claims)
        if provision.claims_charged > 0:
            entries.append({
                "account": "158000",
                "debit": float(provision.claims_charged),
                "credit": 0,
                "label": f"Reprise provision garantie {provision.period}"
            })
            entries.append({
                "account": "781500",  # Reprise provisions charges
                "debit": 0,
                "credit": float(provision.claims_charged),
                "label": f"Reprise provision garantie {provision.period}"
            })

        return entries

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_warranty_statistics(self) -> Dict[str, Any]:
        """Statistiques sur les garanties."""
        warranties = list(self._warranties.values())
        claims = list(self._claims.values())

        active = len([w for w in warranties if w.status == WarrantyStatus.ACTIVE])
        expired = len([w for w in warranties if w.status == WarrantyStatus.EXPIRED])

        # Par type
        by_type = {}
        for wtype in WarrantyType:
            by_type[wtype.value] = len([
                w for w in warranties if w.warranty_type == wtype
            ])

        # Claims
        claims_by_status = {}
        for status in ClaimStatus:
            claims_by_status[status.value] = len([
                c for c in claims if c.status == status
            ])

        # Coûts
        total_claim_cost = sum(c.claim_cost for c in claims)
        avg_claim_cost = (
            total_claim_cost / len(claims) if claims
            else Decimal("0")
        )

        # Taux de résolution
        resolved = len([
            c for c in claims
            if c.status in [
                ClaimStatus.REPAIRED, ClaimStatus.REPLACED,
                ClaimStatus.REFUNDED, ClaimStatus.CLOSED
            ]
        ])
        resolution_rate = (resolved / len(claims) * 100) if claims else 0

        return {
            "total_warranties": len(warranties),
            "active_warranties": active,
            "expired_warranties": expired,
            "by_type": by_type,
            "total_claims": len(claims),
            "claims_by_status": claims_by_status,
            "total_claim_cost": float(total_claim_cost),
            "average_claim_cost": float(avg_claim_cost),
            "resolution_rate": round(resolution_rate, 1),
            "claim_rate": round(
                len(claims) / len(warranties) * 100 if warranties else 0, 1
            )
        }

    def get_expiring_warranties(
        self,
        days: int = 30
    ) -> List[Warranty]:
        """Liste les garanties expirant bientôt."""
        cutoff = date.today() + timedelta(days=days)
        return [
            w for w in self._warranties.values()
            if w.status == WarrantyStatus.ACTIVE
            and w.end_date <= cutoff
        ]


# ============================================================================
# FACTORY
# ============================================================================

def create_warranty_service(
    tenant_id: str,
    default_warranty_months: int = 24
) -> WarrantyService:
    """Crée un service de gestion des garanties."""
    return WarrantyService(
        tenant_id=tenant_id,
        default_warranty_months=default_warranty_months
    )
