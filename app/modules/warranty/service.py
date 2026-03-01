"""
Module de Gestion des Garanties Produits - GAP-039

Gestion complete du cycle de vie des garanties avec persistence SQLAlchemy:
- Garantie legale de conformite (2 ans)
- Garantie commerciale
- Extensions de garantie
- Demandes SAV et reparations
- Remplacements et remboursements
- Provisions comptables

Conformite:
- Code de la consommation (L217-3 a L217-14)
- Garantie legale de conformite (2 ans)
- Garantie des vices caches
- Directive europeenne 2019/771

CRITIQUE: Utilise les repositories pour l'isolation multi-tenant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .models import (
    Warranty,
    WarrantyClaim,
    WarrantyExtension,
    WarrantyProvision,
    WarrantyStatus,
    ClaimStatus,
    ClaimResolution,
    DefectType,
    WarrantyType,
)
from .repository import (
    WarrantyRepository,
    WarrantyClaimRepository,
    WarrantyExtensionRepository,
    WarrantyProvisionRepository,
)
from .schemas import WarrantyFilters, ClaimFilters


# ============================================================================
# CONSTANTES LEGALES
# ============================================================================

LEGAL_WARRANTY_DURATION_MONTHS = 24  # Garantie legale de conformite
HIDDEN_DEFECTS_DURATION_YEARS = 2  # Delai pour vices caches apres decouverte
REPAIR_MAX_DAYS = 30  # Delai max reparation sous garantie

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
# DATA CLASSES (pour compatibilite API)
# ============================================================================

@dataclass
class Product:
    """Produit sous garantie."""
    id: str
    name: str
    sku: str
    serial_number: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    purchase_price: Decimal = Decimal("0")
    currency: str = "EUR"
    purchase_date: Optional[date] = None
    delivery_date: Optional[date] = None


@dataclass
class Customer:
    """Client proprietaire."""
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
    max_claims: Optional[int] = None
    max_claim_amount: Optional[Decimal] = None
    deductible: Decimal = Decimal("0")


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class WarrantyService:
    """
    Service de gestion des garanties avec persistence SQLAlchemy.

    Gere:
    - Enregistrement des garanties
    - Demandes SAV
    - Reparations et remplacements
    - Extensions de garantie
    - Provisions comptables
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        default_warranty_months: int = 24
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.default_warranty_months = default_warranty_months

        # Repositories avec isolation tenant
        self.warranty_repo = WarrantyRepository(db, tenant_id)
        self.claim_repo = WarrantyClaimRepository(db, tenant_id)
        self.extension_repo = WarrantyExtensionRepository(db, tenant_id)
        self.provision_repo = WarrantyProvisionRepository(db, tenant_id)

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
        # Duree par defaut selon le type
        if duration_months is None:
            if warranty_type == WarrantyType.LEGAL_CONFORMITY:
                duration_months = LEGAL_WARRANTY_DURATION_MONTHS
            else:
                duration_months = self.default_warranty_months

        # Date de debut
        if start_date is None:
            start_date = product.purchase_date or date.today()

        # Date de fin
        end_date = start_date + timedelta(days=duration_months * 30)

        # Conditions par defaut
        terms_dict = None
        if terms:
            terms_dict = {
                "coverage_description": terms.coverage_description,
                "inclusions": terms.inclusions,
                "exclusions": terms.exclusions,
                "limitations": terms.limitations,
                "max_claims": terms.max_claims,
                "max_claim_amount": float(terms.max_claim_amount) if terms.max_claim_amount else None,
                "deductible": float(terms.deductible)
            }

        data = {
            "warranty_type": warranty_type,
            "product_id": product.id,
            "product_name": product.name,
            "product_sku": product.sku,
            "serial_number": product.serial_number,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "start_date": start_date,
            "end_date": end_date,
            "duration_months": duration_months,
            "terms": terms_dict,
            "proof_of_purchase_id": proof_of_purchase_id,
            "purchase_price": product.purchase_price,
            "purchase_date": product.purchase_date,
        }

        return self.warranty_repo.create(data, created_by=created_by)

    def register_legal_warranty(
        self,
        product: Product,
        customer: Customer,
        purchase_date: date,
        proof_of_purchase_id: Optional[str] = None
    ) -> Warranty:
        """Enregistre la garantie legale de conformite."""
        terms = WarrantyTerms(
            coverage_description=(
                "Garantie legale de conformite - Code de la consommation "
                "articles L217-3 a L217-14"
            ),
            inclusions=[
                "Defauts de conformite existants a la livraison",
                "Defauts apparaissant dans les 24 mois suivant la livraison "
                "(presumes exister au moment de la livraison)"
            ],
            exclusions=[
                "Defauts resultant de materiaux fournis par le consommateur",
                "Defauts dont le consommateur avait connaissance",
                "Defauts resultant de l'utilisation anormale"
            ],
            limitations=[
                "Reparation ou remplacement sans frais",
                "A defaut, reduction du prix ou resolution du contrat"
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

    def get_warranty(self, warranty_id: str) -> Optional[Warranty]:
        """Recupere une garantie par ID."""
        return self.warranty_repo.get_by_id(warranty_id)

    def get_warranty_by_number(self, warranty_number: str) -> Optional[Warranty]:
        """Recupere une garantie par numero."""
        return self.warranty_repo.get_by_number(warranty_number)

    def list_warranties(
        self,
        filters: WarrantyFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Warranty], int]:
        """Liste les garanties avec filtres."""
        return self.warranty_repo.list(filters=filters, page=page, page_size=page_size)

    def check_warranty_status(self, warranty_id: str) -> Dict[str, Any]:
        """Verifie le statut d'une garantie."""
        warranty = self.warranty_repo.get_by_id(warranty_id)
        if not warranty:
            raise ValueError(f"Garantie {warranty_id} non trouvee")

        today = date.today()
        is_active = (
            warranty.status == WarrantyStatus.ACTIVE and
            warranty.start_date <= today <= warranty.end_date
        )
        days_remaining = max(0, (warranty.end_date - today).days) if is_active else 0

        # Compter les claims en cours
        claims = self.claim_repo.get_by_warranty(warranty_id)
        active_claims = len([
            c for c in claims
            if c.status not in [ClaimStatus.CLOSED, ClaimStatus.REJECTED]
        ])

        return {
            "warranty_id": str(warranty.id),
            "warranty_number": warranty.warranty_number,
            "status": warranty.status.value if hasattr(warranty.status, 'value') else warranty.status,
            "is_active": is_active,
            "start_date": warranty.start_date.isoformat(),
            "end_date": warranty.end_date.isoformat(),
            "days_remaining": days_remaining,
            "claims_count": warranty.claims_count or 0,
            "active_claims": active_claims,
            "product": {
                "name": warranty.product_name,
                "serial_number": warranty.serial_number
            },
            "customer": warranty.customer_name
        }

    def extend_warranty(
        self,
        warranty_id: str,
        additional_months: int,
        extension_type: str = "standard",
        price: Decimal = Decimal("0")
    ) -> WarrantyExtension:
        """Etend une garantie existante."""
        warranty = self.warranty_repo.get_by_id(warranty_id)
        if not warranty:
            raise ValueError(f"Garantie {warranty_id} non trouvee")

        if warranty.status != WarrantyStatus.ACTIVE:
            raise ValueError("Seules les garanties actives peuvent etre etendues")

        # Calculer la nouvelle date de fin
        new_end_date = warranty.end_date + timedelta(days=additional_months * 30)

        extension_data = {
            "warranty_id": warranty_id,
            "extension_type": extension_type,
            "additional_months": additional_months,
            "new_end_date": new_end_date,
            "price": price
        }
        extension = self.extension_repo.create(extension_data)

        # Mettre a jour la garantie
        self.warranty_repo.update(warranty, {
            "end_date": new_end_date,
            "duration_months": warranty.duration_months + additional_months
        })

        return extension

    def expire_warranties(self) -> List[Warranty]:
        """Expire les garanties depassees."""
        return self.warranty_repo.expire_warranties()

    def get_expiring_warranties(self, days: int = 30) -> List[Warranty]:
        """Liste les garanties expirant bientot."""
        return self.warranty_repo.get_expiring(days)

    # ========================================================================
    # DEMANDES DE GARANTIE
    # ========================================================================

    def submit_claim(
        self,
        warranty_id: str,
        defect_type: DefectType,
        defect_description: str,
        occurrence_date: Optional[date] = None,
        submitted_by: str = ""
    ) -> WarrantyClaim:
        """Soumet une demande de garantie."""
        warranty = self.warranty_repo.get_by_id(warranty_id)
        if not warranty:
            raise ValueError(f"Garantie {warranty_id} non trouvee")

        # Verifier que la garantie est active
        today = date.today()
        is_active = (
            warranty.status == WarrantyStatus.ACTIVE and
            warranty.start_date <= today <= warranty.end_date
        )
        if not is_active:
            raise ValueError(
                f"Garantie non active (statut: {warranty.status}, "
                f"fin: {warranty.end_date})"
            )

        # Verifier les limites
        if warranty.terms and warranty.terms.get("max_claims"):
            if (warranty.claims_count or 0) >= warranty.terms["max_claims"]:
                raise ValueError("Nombre maximum de reclamations atteint")

        claim_data = {
            "warranty_id": warranty_id,
            "defect_type": defect_type,
            "defect_description": defect_description,
            "occurrence_date": occurrence_date or date.today(),
        }
        claim = self.claim_repo.create(claim_data, created_by=submitted_by)

        # Incrementer le compteur
        self.warranty_repo.update(warranty, {
            "claims_count": (warranty.claims_count or 0) + 1
        })

        return claim

    def get_claim(self, claim_id: str) -> Optional[WarrantyClaim]:
        """Recupere une demande par ID."""
        return self.claim_repo.get_by_id(claim_id)

    def list_claims(
        self,
        filters: ClaimFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[WarrantyClaim], int]:
        """Liste les demandes avec filtres."""
        return self.claim_repo.list(filters=filters, page=page, page_size=page_size)

    def review_claim(
        self,
        claim_id: str,
        reviewed_by: str,
        approved: bool,
        rejection_reason: Optional[str] = None,
        notes: Optional[str] = None
    ) -> WarrantyClaim:
        """Examine une demande de garantie."""
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvee")

        update_data = {
            "reviewed_at": datetime.utcnow(),
            "assigned_to": reviewed_by,
            "status": ClaimStatus.APPROVED if approved else ClaimStatus.REJECTED
        }

        if not approved and rejection_reason:
            update_data["rejection_reason"] = rejection_reason

        return self.claim_repo.update(claim, update_data, updated_by=reviewed_by)

    def start_repair(
        self,
        claim_id: str,
        repair_center: str,
        technician_name: Optional[str] = None,
        diagnosis: Optional[str] = None
    ) -> WarrantyClaim:
        """Demarre la reparation."""
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvee")

        if claim.status != ClaimStatus.APPROVED:
            raise ValueError("La demande doit etre approuvee")

        update_data = {
            "status": ClaimStatus.IN_REPAIR,
            "repair_center": repair_center,
            "technician_name": technician_name,
            "diagnosis": diagnosis,
            "repair_received_date": date.today(),
            "repair_start_date": date.today(),
        }

        return self.claim_repo.update(claim, update_data)

    def complete_repair(
        self,
        claim_id: str,
        work_performed: str,
        parts_replaced: Optional[List[Dict[str, Any]]] = None,
        labor_cost: Decimal = Decimal("0"),
        parts_cost: Decimal = Decimal("0")
    ) -> WarrantyClaim:
        """Termine la reparation."""
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvee")

        total_cost = labor_cost + parts_cost

        update_data = {
            "status": ClaimStatus.REPAIRED,
            "resolution": ClaimResolution.REPAIR,
            "repair_completion_date": date.today(),
            "work_performed": work_performed,
            "parts_replaced": parts_replaced or [],
            "labor_cost": labor_cost,
            "parts_cost": parts_cost,
            "claim_cost": total_cost,
        }

        return self.claim_repo.update(claim, update_data)

    def process_replacement(
        self,
        claim_id: str,
        replacement_product_id: str,
        replacement_serial_number: Optional[str] = None,
        is_equivalent: bool = False,
        replacement_cost: Decimal = Decimal("0")
    ) -> WarrantyClaim:
        """Traite un remplacement."""
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvee")

        update_data = {
            "status": ClaimStatus.REPLACED,
            "resolution": ClaimResolution.REPLACEMENT_EQUIVALENT if is_equivalent else ClaimResolution.REPLACEMENT_SAME,
            "resolution_date": datetime.utcnow(),
            "replacement_product_id": replacement_product_id,
            "replacement_serial_number": replacement_serial_number,
            "claim_cost": replacement_cost,
        }

        return self.claim_repo.update(claim, update_data)

    def process_refund(
        self,
        claim_id: str,
        refund_amount: Decimal,
        is_full_refund: bool = True,
        refund_reason: Optional[str] = None
    ) -> WarrantyClaim:
        """Traite un remboursement."""
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvee")

        warranty = self.warranty_repo.get_by_id(str(claim.warranty_id))
        if not warranty:
            raise ValueError("Garantie non trouvee")

        # Verifier le montant max
        if warranty.terms and warranty.terms.get("max_claim_amount"):
            if refund_amount > Decimal(str(warranty.terms["max_claim_amount"])):
                raise ValueError(
                    f"Montant depasse le maximum autorise: "
                    f"{warranty.terms['max_claim_amount']}"
                )

        update_data = {
            "status": ClaimStatus.REFUNDED,
            "resolution": ClaimResolution.REFUND_FULL if is_full_refund else ClaimResolution.REFUND_PARTIAL,
            "resolution_date": datetime.utcnow(),
            "refund_amount": refund_amount,
            "refund_reason": refund_reason,
            "claim_cost": refund_amount,
        }
        claim = self.claim_repo.update(claim, update_data)

        # Mettre a jour le total reclame
        self.warranty_repo.update(warranty, {
            "total_claimed_amount": (warranty.total_claimed_amount or Decimal("0")) + refund_amount
        })

        return claim

    def close_claim(
        self,
        claim_id: str,
        resolution_description: Optional[str] = None
    ) -> WarrantyClaim:
        """Cloture une demande."""
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            raise ValueError(f"Demande {claim_id} non trouvee")

        update_data = {
            "status": ClaimStatus.CLOSED,
            "closed_at": datetime.utcnow(),
            "resolution_description": resolution_description,
        }

        return self.claim_repo.update(claim, update_data)

    # ========================================================================
    # PROVISIONS COMPTABLES
    # ========================================================================

    def calculate_provisions(self, period: str) -> WarrantyProvision:
        """Calcule les provisions pour garantie."""
        # Obtenir la provision precedente
        previous_period = self._get_previous_period(period)
        previous_provision = self.provision_repo.get_by_period(previous_period)
        opening_balance = (
            previous_provision.closing_balance if previous_provision
            else Decimal("0")
        )

        # Garanties actives
        active_warranties, _ = self.warranty_repo.list(page_size=10000)
        active_count = len([w for w in active_warranties if w.status == WarrantyStatus.ACTIVE])

        # Calculer le taux de sinistralite
        all_warranties, total_warranties = self.warranty_repo.list(page_size=10000)
        all_claims, total_claims = self.claim_repo.list(page_size=10000)

        claim_rate = (
            Decimal(str(total_claims)) / Decimal(str(total_warranties))
            if total_warranties > 0 else Decimal("0.05")
        )

        # Cout moyen des reclamations
        claim_costs = [c.claim_cost for c in all_claims if c.claim_cost and c.claim_cost > 0]
        avg_claim_cost = (
            sum(claim_costs) / len(claim_costs) if claim_costs
            else Decimal("50")
        )

        # Provision = nombre garanties actives * taux sinistralite * cout moyen
        provisions_added = (
            Decimal(str(active_count)) * claim_rate * avg_claim_cost
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Reclamations du mois
        year, month = period.split("-")
        claims_this_month = [
            c for c in all_claims
            if c.closed_at and c.closed_at.year == int(year) and c.closed_at.month == int(month)
        ]
        claims_charged = sum(c.claim_cost or Decimal("0") for c in claims_this_month)

        # Calcul du solde
        closing_balance = opening_balance + provisions_added - claims_charged

        provision_data = {
            "period": period,
            "opening_balance": opening_balance,
            "provisions_added": provisions_added,
            "claims_charged": claims_charged,
            "closing_balance": closing_balance,
            "warranties_active": active_count,
            "claims_count": len(claims_this_month),
            "average_claim_cost": avg_claim_cost,
        }

        # Verifier si existe deja
        existing = self.provision_repo.get_by_period(period)
        if existing:
            return self.provision_repo.update(existing, provision_data)
        return self.provision_repo.create(provision_data)

    def _get_previous_period(self, period: str) -> str:
        """Retourne la periode precedente."""
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
        """Genere les ecritures comptables pour les provisions."""
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
        warranties, total_warranties = self.warranty_repo.list(page_size=10000)
        claims, total_claims = self.claim_repo.list(page_size=10000)

        active = len([w for w in warranties if w.status == WarrantyStatus.ACTIVE])
        expired = len([w for w in warranties if w.status == WarrantyStatus.EXPIRED])

        # Par type
        by_type = {}
        for wtype in WarrantyType:
            by_type[wtype.value] = len([
                w for w in warranties if w.warranty_type == wtype
            ])

        # Claims par statut
        claims_by_status = {}
        for status in ClaimStatus:
            claims_by_status[status.value] = len([
                c for c in claims if c.status == status
            ])

        # Couts
        total_claim_cost = sum(c.claim_cost or Decimal("0") for c in claims)
        avg_claim_cost = (
            total_claim_cost / len(claims) if claims
            else Decimal("0")
        )

        # Taux de resolution
        resolved = len([
            c for c in claims
            if c.status in [
                ClaimStatus.REPAIRED, ClaimStatus.REPLACED,
                ClaimStatus.REFUNDED, ClaimStatus.CLOSED
            ]
        ])
        resolution_rate = (resolved / len(claims) * 100) if claims else 0

        return {
            "total_warranties": total_warranties,
            "active_warranties": active,
            "expired_warranties": expired,
            "by_type": by_type,
            "total_claims": total_claims,
            "claims_by_status": claims_by_status,
            "total_claim_cost": float(total_claim_cost),
            "average_claim_cost": float(avg_claim_cost),
            "resolution_rate": round(resolution_rate, 1),
            "claim_rate": round(
                total_claims / total_warranties * 100 if total_warranties else 0, 1
            )
        }


# ============================================================================
# FACTORY
# ============================================================================

def create_warranty_service(
    db: Session,
    tenant_id: str,
    default_warranty_months: int = 24
) -> WarrantyService:
    """Cree un service de gestion des garanties."""
    return WarrantyService(
        db=db,
        tenant_id=tenant_id,
        default_warranty_months=default_warranty_months
    )
