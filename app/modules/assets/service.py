"""
Module de Gestion des Immobilisations et Actifs - GAP-036

Gestion complète du cycle de vie des actifs:
- Acquisition et mise en service
- Calcul des amortissements (linéaire, dégressif, exceptionnel)
- Inventaire physique et localisation
- Cessions et mises au rebut
- Réévaluations et dépréciations
- Conformité comptable et fiscale

Conformité:
- PCG (Plan Comptable Général)
- Code Général des Impôts (amortissements fiscaux)
- IFRS 16 (contrats de location)
- Règlement ANC 2014-03

Architecture multi-tenant avec isolation stricte.
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid
import calendar


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class AssetCategory(Enum):
    """Catégorie d'immobilisation."""
    # Immobilisations incorporelles (compte 20)
    GOODWILL = "goodwill"  # Fonds commercial
    PATENT = "patent"  # Brevets
    LICENSE = "license"  # Licences
    SOFTWARE = "software"  # Logiciels
    TRADEMARK = "trademark"  # Marques
    DEVELOPMENT_COSTS = "development_costs"  # Frais de développement

    # Immobilisations corporelles (compte 21)
    LAND = "land"  # Terrains
    BUILDING = "building"  # Constructions
    TECHNICAL_INSTALLATION = "technical_installation"  # Installations techniques
    INDUSTRIAL_EQUIPMENT = "industrial_equipment"  # Matériel industriel
    TRANSPORT_EQUIPMENT = "transport_equipment"  # Matériel de transport
    OFFICE_EQUIPMENT = "office_equipment"  # Matériel de bureau
    IT_EQUIPMENT = "it_equipment"  # Matériel informatique
    FURNITURE = "furniture"  # Mobilier
    FIXTURE = "fixture"  # Agencements

    # Immobilisations financières (compte 26-27)
    PARTICIPATION = "participation"  # Participations
    LOAN = "loan"  # Prêts
    DEPOSIT = "deposit"  # Dépôts et cautionnements


class DepreciationMethod(Enum):
    """Méthode d'amortissement."""
    LINEAR = "linear"  # Linéaire
    DECLINING_BALANCE = "declining_balance"  # Dégressif
    UNITS_OF_PRODUCTION = "units_of_production"  # Unités de production
    SUM_OF_YEARS = "sum_of_years"  # Somme des années
    NONE = "none"  # Non amortissable (terrains)


class AssetStatus(Enum):
    """Statut de l'actif."""
    DRAFT = "draft"  # Brouillon
    IN_SERVICE = "in_service"  # En service
    UNDER_MAINTENANCE = "under_maintenance"  # En maintenance
    OUT_OF_SERVICE = "out_of_service"  # Hors service
    DISPOSED = "disposed"  # Cédé
    SCRAPPED = "scrapped"  # Mis au rebut
    FULLY_DEPRECIATED = "fully_depreciated"  # Totalement amorti


class DisposalType(Enum):
    """Type de cession."""
    SALE = "sale"  # Vente
    SCRAP = "scrap"  # Mise au rebut
    DONATION = "donation"  # Don
    THEFT = "theft"  # Vol
    DESTRUCTION = "destruction"  # Destruction
    TRANSFER = "transfer"  # Transfert intra-groupe


class MovementType(Enum):
    """Type de mouvement sur l'actif."""
    ACQUISITION = "acquisition"  # Acquisition
    IMPROVEMENT = "improvement"  # Amélioration
    REVALUATION = "revaluation"  # Réévaluation
    IMPAIRMENT = "impairment"  # Dépréciation
    DISPOSAL = "disposal"  # Cession
    TRANSFER = "transfer"  # Transfert
    DEPRECIATION = "depreciation"  # Amortissement


# ============================================================================
# COEFFICIENTS DÉGRESSIFS (CGI)
# ============================================================================

DECLINING_BALANCE_COEFFICIENTS = {
    3: Decimal("1.25"),   # Durée 3-4 ans
    4: Decimal("1.25"),
    5: Decimal("1.75"),   # Durée 5-6 ans
    6: Decimal("1.75"),
    7: Decimal("2.25"),   # Durée > 6 ans
}

# Durées d'amortissement recommandées (en années)
RECOMMENDED_USEFUL_LIFE = {
    AssetCategory.SOFTWARE: 3,
    AssetCategory.IT_EQUIPMENT: 3,
    AssetCategory.OFFICE_EQUIPMENT: 5,
    AssetCategory.FURNITURE: 10,
    AssetCategory.TRANSPORT_EQUIPMENT: 5,
    AssetCategory.INDUSTRIAL_EQUIPMENT: 10,
    AssetCategory.TECHNICAL_INSTALLATION: 10,
    AssetCategory.BUILDING: 25,
    AssetCategory.FIXTURE: 10,
    AssetCategory.PATENT: 5,
    AssetCategory.LICENSE: 5,
    AssetCategory.TRADEMARK: 10,
    AssetCategory.GOODWILL: 10,
    AssetCategory.DEVELOPMENT_COSTS: 5,
}

# Comptes comptables par catégorie
ACCOUNTING_ACCOUNTS = {
    AssetCategory.GOODWILL: {"asset": "207000", "depreciation": "280700", "expense": "681100"},
    AssetCategory.PATENT: {"asset": "205000", "depreciation": "280500", "expense": "681100"},
    AssetCategory.LICENSE: {"asset": "205000", "depreciation": "280500", "expense": "681100"},
    AssetCategory.SOFTWARE: {"asset": "205000", "depreciation": "280500", "expense": "681100"},
    AssetCategory.TRADEMARK: {"asset": "206000", "depreciation": "280600", "expense": "681100"},
    AssetCategory.DEVELOPMENT_COSTS: {"asset": "203000", "depreciation": "280300", "expense": "681100"},
    AssetCategory.LAND: {"asset": "211000", "depreciation": None, "expense": None},
    AssetCategory.BUILDING: {"asset": "213000", "depreciation": "281300", "expense": "681120"},
    AssetCategory.TECHNICAL_INSTALLATION: {"asset": "215100", "depreciation": "281510", "expense": "681120"},
    AssetCategory.INDUSTRIAL_EQUIPMENT: {"asset": "215400", "depreciation": "281540", "expense": "681120"},
    AssetCategory.TRANSPORT_EQUIPMENT: {"asset": "218200", "depreciation": "281820", "expense": "681120"},
    AssetCategory.OFFICE_EQUIPMENT: {"asset": "218300", "depreciation": "281830", "expense": "681120"},
    AssetCategory.IT_EQUIPMENT: {"asset": "218300", "depreciation": "281830", "expense": "681120"},
    AssetCategory.FURNITURE: {"asset": "218400", "depreciation": "281840", "expense": "681120"},
    AssetCategory.FIXTURE: {"asset": "218100", "depreciation": "281810", "expense": "681120"},
    AssetCategory.PARTICIPATION: {"asset": "261000", "depreciation": "296100", "expense": "686100"},
    AssetCategory.LOAN: {"asset": "274000", "depreciation": "297400", "expense": "686600"},
    AssetCategory.DEPOSIT: {"asset": "275000", "depreciation": None, "expense": None},
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AssetLocation:
    """Localisation d'un actif."""
    site: str
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    position: Optional[str] = None
    gps_coordinates: Optional[Tuple[float, float]] = None


@dataclass
class DepreciationScheduleEntry:
    """Ligne du tableau d'amortissement."""
    period_start: date
    period_end: date
    year: int

    # Valeurs
    opening_gross_value: Decimal
    opening_accumulated_depreciation: Decimal
    opening_net_book_value: Decimal

    # Amortissement de la période
    depreciation_amount: Decimal
    depreciation_rate: Decimal

    # Valeurs de clôture
    closing_accumulated_depreciation: Decimal
    closing_net_book_value: Decimal

    # Fiscal (si différent)
    fiscal_depreciation_amount: Optional[Decimal] = None
    deferred_tax_impact: Optional[Decimal] = None


@dataclass
class AssetMovement:
    """Mouvement sur un actif."""
    id: str
    asset_id: str
    movement_type: MovementType
    movement_date: date

    # Montants
    amount: Decimal
    previous_value: Decimal
    new_value: Decimal

    # Description
    description: Optional[str] = None
    reference: Optional[str] = None

    # Journal comptable
    accounting_entry_id: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class AssetDisposal:
    """Cession d'un actif."""
    id: str
    asset_id: str
    disposal_type: DisposalType
    disposal_date: date

    # Valeurs
    gross_value: Decimal
    accumulated_depreciation: Decimal
    net_book_value: Decimal

    # Cession
    disposal_proceeds: Decimal = Decimal("0")  # Prix de cession
    disposal_costs: Decimal = Decimal("0")  # Frais de cession

    # Résultat
    gain_or_loss: Decimal = Decimal("0")  # Plus ou moins-value

    # Acheteur (si vente)
    buyer_name: Optional[str] = None
    buyer_id: Optional[str] = None
    invoice_id: Optional[str] = None

    # Comptabilisation
    accounting_entry_id: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AssetImpairment:
    """Dépréciation d'un actif."""
    id: str
    asset_id: str
    impairment_date: date

    # Montants
    net_book_value_before: Decimal
    recoverable_amount: Decimal
    impairment_loss: Decimal

    # Justification
    reason: str
    is_reversible: bool = True

    # Comptabilisation
    accounting_entry_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Asset:
    """Immobilisation."""
    id: str
    tenant_id: str
    asset_number: str
    name: str
    description: Optional[str] = None

    # Classification
    category: AssetCategory = AssetCategory.IT_EQUIPMENT
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Acquisition
    acquisition_date: date = field(default_factory=date.today)
    in_service_date: Optional[date] = None
    acquisition_cost: Decimal = Decimal("0")
    residual_value: Decimal = Decimal("0")

    # Composants du coût
    purchase_price: Decimal = Decimal("0")
    installation_cost: Decimal = Decimal("0")
    transport_cost: Decimal = Decimal("0")
    other_costs: Decimal = Decimal("0")

    # Fournisseur
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_reference: Optional[str] = None
    purchase_order_reference: Optional[str] = None

    # Amortissement
    depreciation_method: DepreciationMethod = DepreciationMethod.LINEAR
    useful_life_years: int = 5
    useful_life_months: int = 0
    fiscal_useful_life_years: Optional[int] = None  # Si différent comptable

    # Valeurs calculées
    accumulated_depreciation: Decimal = Decimal("0")
    net_book_value: Decimal = Decimal("0")
    fiscal_accumulated_depreciation: Decimal = Decimal("0")

    # Localisation
    location: Optional[AssetLocation] = None
    responsible_employee_id: Optional[str] = None
    department_id: Optional[str] = None

    # Identification
    serial_number: Optional[str] = None
    barcode: Optional[str] = None
    rfid_tag: Optional[str] = None

    # Garantie et maintenance
    warranty_end_date: Optional[date] = None
    maintenance_contract_id: Optional[str] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: Optional[date] = None

    # Statut
    status: AssetStatus = AssetStatus.DRAFT

    # Historique
    movements: List[AssetMovement] = field(default_factory=list)
    depreciation_schedule: List[DepreciationScheduleEntry] = field(default_factory=list)

    # Cession
    disposal: Optional[AssetDisposal] = None
    disposal_date: Optional[date] = None

    # Comptabilité
    cost_center: Optional[str] = None
    analytic_axis: Optional[Dict[str, str]] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def __post_init__(self):
        """Calcule les valeurs initiales."""
        if self.acquisition_cost == 0:
            self.acquisition_cost = (
                self.purchase_price +
                self.installation_cost +
                self.transport_cost +
                self.other_costs
            )
        self.net_book_value = self.acquisition_cost - self.accumulated_depreciation

    def get_useful_life_months(self) -> int:
        """Retourne la durée d'utilisation totale en mois."""
        return self.useful_life_years * 12 + self.useful_life_months

    def get_monthly_depreciation_rate(self) -> Decimal:
        """Calcule le taux d'amortissement mensuel linéaire."""
        months = self.get_useful_life_months()
        if months == 0:
            return Decimal("0")
        depreciable_amount = self.acquisition_cost - self.residual_value
        return (depreciable_amount / months).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def get_annual_depreciation_rate(self) -> Decimal:
        """Calcule le taux d'amortissement annuel."""
        if self.useful_life_years == 0:
            return Decimal("0")
        return (Decimal("100") / self.useful_life_years).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


@dataclass
class DepreciationRun:
    """Exécution d'amortissement."""
    id: str
    tenant_id: str
    run_date: date
    period_start: date
    period_end: date

    # Résultats
    assets_processed: int = 0
    total_depreciation: Decimal = Decimal("0")
    entries_generated: List[Dict[str, Any]] = field(default_factory=list)

    # Statut
    status: str = "draft"  # draft, validated, posted
    validated_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PhysicalInventory:
    """Inventaire physique des actifs."""
    id: str
    tenant_id: str
    inventory_date: date
    location: Optional[str] = None

    # Résultats
    assets_expected: int = 0
    assets_found: int = 0
    assets_missing: int = 0
    assets_unexpected: int = 0

    # Détails
    items: List[Dict[str, Any]] = field(default_factory=list)

    # Statut
    status: str = "in_progress"  # in_progress, completed, reconciled
    completed_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class AssetService:
    """
    Service de gestion des immobilisations.

    Gère:
    - Création et suivi des actifs
    - Calcul des amortissements
    - Cessions et mises au rebut
    - Inventaire physique
    - Reporting comptable et fiscal
    """

    def __init__(
        self,
        tenant_id: str,
        fiscal_year_end_month: int = 12
    ):
        self.tenant_id = tenant_id
        self.fiscal_year_end_month = fiscal_year_end_month

        # Stockage (à remplacer par DB)
        self._assets: Dict[str, Asset] = {}
        self._depreciation_runs: Dict[str, DepreciationRun] = {}
        self._inventories: Dict[str, PhysicalInventory] = {}
        self._asset_counter = 0

    # ========================================================================
    # CRÉATION D'ACTIFS
    # ========================================================================

    def create_asset(
        self,
        name: str,
        category: AssetCategory,
        acquisition_date: date,
        purchase_price: Decimal,
        useful_life_years: int,
        depreciation_method: DepreciationMethod = DepreciationMethod.LINEAR,
        residual_value: Decimal = Decimal("0"),
        installation_cost: Decimal = Decimal("0"),
        transport_cost: Decimal = Decimal("0"),
        supplier_id: Optional[str] = None,
        supplier_name: Optional[str] = None,
        serial_number: Optional[str] = None,
        location: Optional[AssetLocation] = None,
        created_by: str = ""
    ) -> Asset:
        """Crée une nouvelle immobilisation."""
        # Générer le numéro d'actif
        self._asset_counter += 1
        asset_number = f"IMM-{date.today().year}-{self._asset_counter:06d}"

        # Déterminer la durée si non fournie
        if useful_life_years == 0:
            useful_life_years = RECOMMENDED_USEFUL_LIFE.get(category, 5)

        asset = Asset(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            asset_number=asset_number,
            name=name,
            category=category,
            acquisition_date=acquisition_date,
            purchase_price=purchase_price,
            installation_cost=installation_cost,
            transport_cost=transport_cost,
            residual_value=residual_value,
            depreciation_method=depreciation_method,
            useful_life_years=useful_life_years,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            serial_number=serial_number,
            location=location,
            created_by=created_by
        )

        # Calculer le coût d'acquisition
        asset.acquisition_cost = (
            purchase_price + installation_cost + transport_cost
        )
        asset.net_book_value = asset.acquisition_cost

        # Enregistrer le mouvement d'acquisition
        movement = AssetMovement(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            movement_type=MovementType.ACQUISITION,
            movement_date=acquisition_date,
            amount=asset.acquisition_cost,
            previous_value=Decimal("0"),
            new_value=asset.acquisition_cost,
            description=f"Acquisition de {name}",
            created_by=created_by
        )
        asset.movements.append(movement)

        self._assets[asset.id] = asset
        return asset

    def put_in_service(
        self,
        asset_id: str,
        in_service_date: date
    ) -> Asset:
        """Met en service une immobilisation."""
        asset = self._assets.get(asset_id)
        if not asset:
            raise ValueError(f"Actif {asset_id} non trouvé")

        if asset.status != AssetStatus.DRAFT:
            raise ValueError("Actif déjà en service")

        asset.in_service_date = in_service_date
        asset.status = AssetStatus.IN_SERVICE
        asset.updated_at = datetime.now()

        # Générer le tableau d'amortissement
        self._generate_depreciation_schedule(asset)

        return asset

    # ========================================================================
    # CALCUL DES AMORTISSEMENTS
    # ========================================================================

    def _generate_depreciation_schedule(self, asset: Asset):
        """Génère le tableau d'amortissement prévisionnel."""
        if asset.depreciation_method == DepreciationMethod.NONE:
            return

        if not asset.in_service_date:
            return

        schedule = []
        start_date = asset.in_service_date
        depreciable_amount = asset.acquisition_cost - asset.residual_value
        remaining_value = depreciable_amount
        accumulated = Decimal("0")

        if asset.depreciation_method == DepreciationMethod.LINEAR:
            schedule = self._calculate_linear_depreciation(
                asset, start_date, depreciable_amount
            )
        elif asset.depreciation_method == DepreciationMethod.DECLINING_BALANCE:
            schedule = self._calculate_declining_balance(
                asset, start_date, depreciable_amount
            )

        asset.depreciation_schedule = schedule

    def _calculate_linear_depreciation(
        self,
        asset: Asset,
        start_date: date,
        depreciable_amount: Decimal
    ) -> List[DepreciationScheduleEntry]:
        """Calcule l'amortissement linéaire."""
        schedule = []
        annual_rate = asset.get_annual_depreciation_rate()
        annual_amount = (depreciable_amount * annual_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        remaining = depreciable_amount
        accumulated = Decimal("0")
        current_date = start_date

        for year in range(asset.useful_life_years + 1):
            # Calcul au prorata pour première et dernière année
            if year == 0:
                # Première année : prorata temporis
                days_in_year = 366 if calendar.isleap(start_date.year) else 365
                remaining_days = (
                    date(start_date.year, 12, 31) - start_date
                ).days + 1
                prorata = Decimal(str(remaining_days)) / Decimal(str(days_in_year))
                period_depreciation = (annual_amount * prorata).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                period_start = start_date
                period_end = date(start_date.year, 12, 31)
            else:
                period_start = date(start_date.year + year, 1, 1)
                period_end = date(start_date.year + year, 12, 31)

                if remaining <= annual_amount:
                    period_depreciation = remaining
                else:
                    period_depreciation = annual_amount

            if remaining <= 0:
                break

            opening_accumulated = accumulated
            accumulated += period_depreciation
            remaining -= period_depreciation

            entry = DepreciationScheduleEntry(
                period_start=period_start,
                period_end=period_end,
                year=year + 1,
                opening_gross_value=asset.acquisition_cost,
                opening_accumulated_depreciation=opening_accumulated,
                opening_net_book_value=asset.acquisition_cost - opening_accumulated,
                depreciation_amount=period_depreciation,
                depreciation_rate=annual_rate,
                closing_accumulated_depreciation=accumulated,
                closing_net_book_value=asset.acquisition_cost - accumulated
            )
            schedule.append(entry)

        return schedule

    def _calculate_declining_balance(
        self,
        asset: Asset,
        start_date: date,
        depreciable_amount: Decimal
    ) -> List[DepreciationScheduleEntry]:
        """Calcule l'amortissement dégressif."""
        schedule = []

        # Coefficient dégressif
        coef = DECLINING_BALANCE_COEFFICIENTS.get(
            asset.useful_life_years,
            Decimal("2.25")
        )

        linear_rate = Decimal("100") / asset.useful_life_years
        declining_rate = linear_rate * coef

        remaining = depreciable_amount
        accumulated = Decimal("0")

        for year in range(asset.useful_life_years + 1):
            if remaining <= 0:
                break

            if year == 0:
                # Première année : prorata temporis
                days_in_year = 366 if calendar.isleap(start_date.year) else 365
                remaining_days = (
                    date(start_date.year, 12, 31) - start_date
                ).days + 1
                prorata = Decimal(str(remaining_days)) / Decimal(str(days_in_year))
                period_depreciation = (
                    remaining * declining_rate / 100 * prorata
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                period_start = start_date
                period_end = date(start_date.year, 12, 31)
            else:
                period_start = date(start_date.year + year, 1, 1)
                period_end = date(start_date.year + year, 12, 31)

                # Comparer dégressif vs linéaire sur le reste
                declining_amount = (remaining * declining_rate / 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                remaining_years = asset.useful_life_years - year
                if remaining_years > 0:
                    linear_amount = (remaining / remaining_years).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                else:
                    linear_amount = remaining

                # Prendre le plus élevé
                period_depreciation = max(declining_amount, linear_amount)

            if period_depreciation > remaining:
                period_depreciation = remaining

            opening_accumulated = accumulated
            accumulated += period_depreciation
            remaining -= period_depreciation

            entry = DepreciationScheduleEntry(
                period_start=period_start,
                period_end=period_end,
                year=year + 1,
                opening_gross_value=asset.acquisition_cost,
                opening_accumulated_depreciation=opening_accumulated,
                opening_net_book_value=asset.acquisition_cost - opening_accumulated,
                depreciation_amount=period_depreciation,
                depreciation_rate=declining_rate,
                closing_accumulated_depreciation=accumulated,
                closing_net_book_value=asset.acquisition_cost - accumulated
            )
            schedule.append(entry)

        return schedule

    def run_depreciation(
        self,
        period_end: date,
        post_to_accounting: bool = False
    ) -> DepreciationRun:
        """Exécute le calcul des amortissements pour une période."""
        # Déterminer la période
        period_start = date(period_end.year, period_end.month, 1)

        run = DepreciationRun(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            run_date=date.today(),
            period_start=period_start,
            period_end=period_end
        )

        entries = []
        total_depreciation = Decimal("0")

        for asset in self._assets.values():
            if asset.status != AssetStatus.IN_SERVICE:
                continue
            if asset.depreciation_method == DepreciationMethod.NONE:
                continue
            if not asset.in_service_date:
                continue

            # Calculer l'amortissement de la période
            depreciation = self._calculate_period_depreciation(
                asset, period_start, period_end
            )

            if depreciation > 0:
                # Mettre à jour l'actif
                asset.accumulated_depreciation += depreciation
                asset.net_book_value = (
                    asset.acquisition_cost - asset.accumulated_depreciation
                )

                # Enregistrer le mouvement
                movement = AssetMovement(
                    id=str(uuid.uuid4()),
                    asset_id=asset.id,
                    movement_type=MovementType.DEPRECIATION,
                    movement_date=period_end,
                    amount=depreciation,
                    previous_value=asset.net_book_value + depreciation,
                    new_value=asset.net_book_value,
                    description=f"Amortissement période {period_start} - {period_end}"
                )
                asset.movements.append(movement)

                # Préparer l'écriture comptable
                accounts = ACCOUNTING_ACCOUNTS.get(asset.category, {})
                if accounts.get("depreciation") and accounts.get("expense"):
                    entry = {
                        "asset_id": asset.id,
                        "asset_number": asset.asset_number,
                        "asset_name": asset.name,
                        "depreciation_amount": float(depreciation),
                        "debit_account": accounts["expense"],
                        "credit_account": accounts["depreciation"],
                        "period": f"{period_start} - {period_end}"
                    }
                    entries.append(entry)

                total_depreciation += depreciation
                run.assets_processed += 1

                # Vérifier si totalement amorti
                if asset.net_book_value <= asset.residual_value:
                    asset.status = AssetStatus.FULLY_DEPRECIATED

        run.total_depreciation = total_depreciation
        run.entries_generated = entries

        if post_to_accounting:
            run.status = "posted"
            run.posted_at = datetime.now()
        else:
            run.status = "validated"
            run.validated_at = datetime.now()

        self._depreciation_runs[run.id] = run
        return run

    def _calculate_period_depreciation(
        self,
        asset: Asset,
        period_start: date,
        period_end: date
    ) -> Decimal:
        """Calcule l'amortissement pour une période donnée."""
        # Trouver l'entrée correspondante dans le tableau
        for entry in asset.depreciation_schedule:
            if entry.period_start <= period_end and entry.period_end >= period_start:
                # Calculer le prorata si période partielle
                entry_days = (entry.period_end - entry.period_start).days + 1
                overlap_start = max(period_start, entry.period_start)
                overlap_end = min(period_end, entry.period_end)
                overlap_days = (overlap_end - overlap_start).days + 1

                if overlap_days >= entry_days:
                    return entry.depreciation_amount
                else:
                    prorata = Decimal(str(overlap_days)) / Decimal(str(entry_days))
                    return (entry.depreciation_amount * prorata).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

        return Decimal("0")

    # ========================================================================
    # CESSIONS
    # ========================================================================

    def dispose_asset(
        self,
        asset_id: str,
        disposal_type: DisposalType,
        disposal_date: date,
        disposal_proceeds: Decimal = Decimal("0"),
        disposal_costs: Decimal = Decimal("0"),
        buyer_name: Optional[str] = None,
        buyer_id: Optional[str] = None
    ) -> AssetDisposal:
        """Cède ou met au rebut un actif."""
        asset = self._assets.get(asset_id)
        if not asset:
            raise ValueError(f"Actif {asset_id} non trouvé")

        if asset.status in [AssetStatus.DISPOSED, AssetStatus.SCRAPPED]:
            raise ValueError("Actif déjà cédé")

        # Calculer l'amortissement jusqu'à la date de cession
        if asset.in_service_date and asset.status == AssetStatus.IN_SERVICE:
            # Calculer les amortissements manquants
            last_depreciation_date = None
            for entry in asset.depreciation_schedule:
                if entry.closing_accumulated_depreciation <= asset.accumulated_depreciation:
                    last_depreciation_date = entry.period_end

            if last_depreciation_date and last_depreciation_date < disposal_date:
                additional_depreciation = self._calculate_period_depreciation(
                    asset,
                    last_depreciation_date + timedelta(days=1),
                    disposal_date
                )
                asset.accumulated_depreciation += additional_depreciation
                asset.net_book_value = (
                    asset.acquisition_cost - asset.accumulated_depreciation
                )

        # Calculer la plus ou moins-value
        net_proceeds = disposal_proceeds - disposal_costs
        gain_or_loss = net_proceeds - asset.net_book_value

        disposal = AssetDisposal(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            disposal_type=disposal_type,
            disposal_date=disposal_date,
            gross_value=asset.acquisition_cost,
            accumulated_depreciation=asset.accumulated_depreciation,
            net_book_value=asset.net_book_value,
            disposal_proceeds=disposal_proceeds,
            disposal_costs=disposal_costs,
            gain_or_loss=gain_or_loss,
            buyer_name=buyer_name,
            buyer_id=buyer_id
        )

        # Mettre à jour l'actif
        asset.disposal = disposal
        asset.disposal_date = disposal_date
        asset.status = (
            AssetStatus.DISPOSED if disposal_type == DisposalType.SALE
            else AssetStatus.SCRAPPED
        )
        asset.updated_at = datetime.now()

        # Enregistrer le mouvement
        movement = AssetMovement(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            movement_type=MovementType.DISPOSAL,
            movement_date=disposal_date,
            amount=asset.net_book_value,
            previous_value=asset.net_book_value,
            new_value=Decimal("0"),
            description=f"Cession: {disposal_type.value}"
        )
        asset.movements.append(movement)

        return disposal

    # ========================================================================
    # INVENTAIRE PHYSIQUE
    # ========================================================================

    def create_physical_inventory(
        self,
        inventory_date: date,
        location: Optional[str] = None
    ) -> PhysicalInventory:
        """Crée un inventaire physique."""
        # Compter les actifs attendus
        expected_assets = [
            a for a in self._assets.values()
            if a.status == AssetStatus.IN_SERVICE
            and (not location or (a.location and a.location.site == location))
        ]

        inventory = PhysicalInventory(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            inventory_date=inventory_date,
            location=location,
            assets_expected=len(expected_assets),
            items=[{
                "asset_id": a.id,
                "asset_number": a.asset_number,
                "name": a.name,
                "barcode": a.barcode,
                "expected_location": a.location.site if a.location else None,
                "found": False,
                "actual_location": None,
                "condition": None,
                "notes": None
            } for a in expected_assets]
        )

        self._inventories[inventory.id] = inventory
        return inventory

    def record_inventory_item(
        self,
        inventory_id: str,
        asset_id: str,
        found: bool,
        actual_location: Optional[str] = None,
        condition: Optional[str] = None,
        notes: Optional[str] = None
    ) -> PhysicalInventory:
        """Enregistre un élément d'inventaire."""
        inventory = self._inventories.get(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire {inventory_id} non trouvé")

        # Trouver l'élément
        for item in inventory.items:
            if item["asset_id"] == asset_id:
                item["found"] = found
                item["actual_location"] = actual_location
                item["condition"] = condition
                item["notes"] = notes
                break
        else:
            # Actif inattendu
            inventory.items.append({
                "asset_id": asset_id,
                "found": True,
                "actual_location": actual_location,
                "condition": condition,
                "notes": notes,
                "unexpected": True
            })
            inventory.assets_unexpected += 1

        # Mettre à jour les compteurs
        inventory.assets_found = sum(1 for i in inventory.items if i.get("found"))
        inventory.assets_missing = inventory.assets_expected - inventory.assets_found

        return inventory

    def complete_inventory(
        self,
        inventory_id: str
    ) -> PhysicalInventory:
        """Termine un inventaire physique."""
        inventory = self._inventories.get(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire {inventory_id} non trouvé")

        inventory.status = "completed"
        inventory.completed_at = datetime.now()

        return inventory

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_asset_register(
        self,
        as_of_date: Optional[date] = None,
        category: Optional[AssetCategory] = None,
        status: Optional[AssetStatus] = None
    ) -> List[Dict[str, Any]]:
        """Génère le registre des immobilisations."""
        as_of = as_of_date or date.today()
        register = []

        for asset in self._assets.values():
            if category and asset.category != category:
                continue
            if status and asset.status != status:
                continue

            accounts = ACCOUNTING_ACCOUNTS.get(asset.category, {})

            register.append({
                "asset_number": asset.asset_number,
                "name": asset.name,
                "category": asset.category.value,
                "acquisition_date": asset.acquisition_date.isoformat(),
                "in_service_date": asset.in_service_date.isoformat() if asset.in_service_date else None,
                "acquisition_cost": float(asset.acquisition_cost),
                "accumulated_depreciation": float(asset.accumulated_depreciation),
                "net_book_value": float(asset.net_book_value),
                "depreciation_method": asset.depreciation_method.value,
                "useful_life_years": asset.useful_life_years,
                "status": asset.status.value,
                "location": asset.location.site if asset.location else None,
                "asset_account": accounts.get("asset"),
                "depreciation_account": accounts.get("depreciation"),
            })

        return sorted(register, key=lambda x: x["asset_number"])

    def get_depreciation_summary(
        self,
        year: int
    ) -> Dict[str, Any]:
        """Résumé des amortissements pour une année."""
        summary = {
            "year": year,
            "by_category": {},
            "total_depreciation": Decimal("0"),
            "total_gross_value": Decimal("0"),
            "total_net_book_value": Decimal("0"),
        }

        for asset in self._assets.values():
            if asset.status in [AssetStatus.DRAFT]:
                continue

            cat = asset.category.value
            if cat not in summary["by_category"]:
                summary["by_category"][cat] = {
                    "count": 0,
                    "gross_value": Decimal("0"),
                    "depreciation": Decimal("0"),
                    "net_book_value": Decimal("0")
                }

            # Amortissement de l'année
            year_depreciation = Decimal("0")
            for entry in asset.depreciation_schedule:
                if entry.period_start.year == year or entry.period_end.year == year:
                    year_depreciation += entry.depreciation_amount

            summary["by_category"][cat]["count"] += 1
            summary["by_category"][cat]["gross_value"] += asset.acquisition_cost
            summary["by_category"][cat]["depreciation"] += year_depreciation
            summary["by_category"][cat]["net_book_value"] += asset.net_book_value

            summary["total_depreciation"] += year_depreciation
            summary["total_gross_value"] += asset.acquisition_cost
            summary["total_net_book_value"] += asset.net_book_value

        # Convertir en float pour JSON
        summary["total_depreciation"] = float(summary["total_depreciation"])
        summary["total_gross_value"] = float(summary["total_gross_value"])
        summary["total_net_book_value"] = float(summary["total_net_book_value"])

        for cat in summary["by_category"]:
            for key in ["gross_value", "depreciation", "net_book_value"]:
                summary["by_category"][cat][key] = float(
                    summary["by_category"][cat][key]
                )

        return summary

    def generate_accounting_entries(
        self,
        asset_id: str,
        entry_type: str = "acquisition"
    ) -> List[Dict[str, Any]]:
        """Génère les écritures comptables pour un actif."""
        asset = self._assets.get(asset_id)
        if not asset:
            raise ValueError(f"Actif {asset_id} non trouvé")

        accounts = ACCOUNTING_ACCOUNTS.get(asset.category, {})
        entries = []

        if entry_type == "acquisition":
            # Débit: Compte d'immobilisation
            entries.append({
                "account": accounts.get("asset", "218000"),
                "debit": float(asset.acquisition_cost),
                "credit": 0,
                "label": f"Acquisition {asset.name}",
                "reference": asset.asset_number
            })
            # Crédit: Fournisseur
            entries.append({
                "account": "404000",  # Fournisseurs d'immobilisations
                "debit": 0,
                "credit": float(asset.acquisition_cost),
                "label": f"Acquisition {asset.name}",
                "reference": asset.asset_number
            })

        elif entry_type == "disposal" and asset.disposal:
            disposal = asset.disposal

            # Sortie de l'immobilisation
            entries.append({
                "account": accounts.get("depreciation", "281000"),
                "debit": float(disposal.accumulated_depreciation),
                "credit": 0,
                "label": f"Sortie amortissement {asset.name}"
            })

            if disposal.gain_or_loss >= 0:
                # Plus-value
                entries.append({
                    "account": "775000",  # Produits des cessions
                    "debit": 0,
                    "credit": float(disposal.disposal_proceeds),
                    "label": f"Cession {asset.name}"
                })
            else:
                # Moins-value
                entries.append({
                    "account": "675000",  # Valeurs comptables des cessions
                    "debit": float(disposal.net_book_value),
                    "credit": 0,
                    "label": f"VNC sortie {asset.name}"
                })

            entries.append({
                "account": accounts.get("asset", "218000"),
                "debit": 0,
                "credit": float(disposal.gross_value),
                "label": f"Sortie immobilisation {asset.name}"
            })

        return entries


# ============================================================================
# FACTORY
# ============================================================================

def create_asset_service(
    tenant_id: str,
    fiscal_year_end_month: int = 12
) -> AssetService:
    """Crée un service de gestion des immobilisations."""
    return AssetService(
        tenant_id=tenant_id,
        fiscal_year_end_month=fiscal_year_end_month
    )
