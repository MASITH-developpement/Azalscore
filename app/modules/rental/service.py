"""
Service Rental / Location - GAP-063

Gestion de la location:
- Catalogue articles locatifs
- Disponibilités et planning
- Contrats de location
- Tarification dynamique
- Dépôts de garantie
- États des lieux
- Facturation récurrente
- Prolongations et retours
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class RentalItemType(str, Enum):
    """Type d'article locatif."""
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    PROPERTY = "property"
    TOOL = "tool"
    FURNITURE = "furniture"
    ELECTRONICS = "electronics"
    OTHER = "other"


class RentalItemStatus(str, Enum):
    """Statut d'un article."""
    AVAILABLE = "available"
    RENTED = "rented"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class ContractStatus(str, Enum):
    """Statut d'un contrat."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    EXTENDED = "extended"
    ENDED = "ended"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class PricingType(str, Enum):
    """Type de tarification."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    FIXED = "fixed"


class InspectionType(str, Enum):
    """Type d'inspection."""
    CHECK_OUT = "check_out"
    CHECK_IN = "check_in"
    INTERIM = "interim"


class InspectionCondition(str, Enum):
    """État lors de l'inspection."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"


class DepositStatus(str, Enum):
    """Statut du dépôt."""
    PENDING = "pending"
    RECEIVED = "received"
    PARTIALLY_REFUNDED = "partially_refunded"
    FULLY_REFUNDED = "fully_refunded"
    RETAINED = "retained"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PricingRule:
    """Règle de tarification."""
    id: str
    name: str
    pricing_type: PricingType
    base_price: Decimal
    currency: str = "EUR"
    min_duration: int = 1
    max_duration: Optional[int] = None
    discount_percent: Decimal = Decimal("0")
    weekend_surcharge_percent: Decimal = Decimal("0")
    holiday_surcharge_percent: Decimal = Decimal("0")
    season_adjustments: Dict[str, Decimal] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class RentalItem:
    """Un article locatif."""
    id: str
    tenant_id: str
    name: str
    description: str
    item_type: RentalItemType
    status: RentalItemStatus = RentalItemStatus.AVAILABLE
    sku: Optional[str] = None
    serial_number: Optional[str] = None
    category_id: Optional[str] = None
    location: Optional[str] = None
    pricing_rule_id: Optional[str] = None
    default_deposit: Decimal = Decimal("0")
    replacement_value: Decimal = Decimal("0")
    condition: InspectionCondition = InspectionCondition.GOOD
    images: List[str] = field(default_factory=list)
    specifications: Dict[str, Any] = field(default_factory=dict)
    maintenance_interval_days: Optional[int] = None
    last_maintenance_date: Optional[date] = None
    total_rentals: int = 0
    total_revenue: Decimal = Decimal("0")
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RentalContract:
    """Un contrat de location."""
    id: str
    tenant_id: str
    reference: str
    customer_id: str
    customer_name: str
    status: ContractStatus = ContractStatus.DRAFT
    items: List[Dict[str, Any]] = field(default_factory=list)
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    pricing_type: PricingType = PricingType.DAILY
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    deposit_amount: Decimal = Decimal("0")
    deposit_status: DepositStatus = DepositStatus.PENDING
    deposit_received_date: Optional[date] = None
    amount_paid: Decimal = Decimal("0")
    balance_due: Decimal = Decimal("0")
    currency: str = "EUR"
    billing_frequency: str = "on_return"  # on_return, weekly, monthly
    next_billing_date: Optional[date] = None
    terms_accepted: bool = False
    terms_accepted_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    signed_by: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_date: Optional[datetime] = None
    pickup_address: Optional[str] = None
    pickup_date: Optional[datetime] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContractLine:
    """Ligne de contrat."""
    id: str
    contract_id: str
    item_id: str
    item_name: str
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    total_price: Decimal = Decimal("0")
    deposit_per_unit: Decimal = Decimal("0")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    condition_at_checkout: InspectionCondition = InspectionCondition.GOOD
    condition_at_checkin: Optional[InspectionCondition] = None
    damage_noted: Optional[str] = None
    damage_charge: Decimal = Decimal("0")


@dataclass
class Inspection:
    """État des lieux."""
    id: str
    tenant_id: str
    contract_id: str
    item_id: str
    inspection_type: InspectionType
    date: datetime = field(default_factory=datetime.now)
    performed_by: Optional[str] = None
    overall_condition: InspectionCondition = InspectionCondition.GOOD
    mileage: Optional[int] = None
    fuel_level: Optional[int] = None  # Pourcentage
    cleanliness: str = "clean"  # clean, acceptable, dirty
    photos: List[str] = field(default_factory=list)
    checklist_items: List[Dict[str, Any]] = field(default_factory=list)
    damages_found: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None
    customer_signature: Optional[str] = None
    customer_signed_at: Optional[datetime] = None


@dataclass
class Reservation:
    """Une réservation."""
    id: str
    tenant_id: str
    customer_id: str
    customer_name: str
    item_id: str
    item_name: str
    start_date: date
    end_date: date
    status: str = "pending"  # pending, confirmed, cancelled, converted
    quoted_amount: Decimal = Decimal("0")
    deposit_required: Decimal = Decimal("0")
    contract_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class Extension:
    """Extension de location."""
    id: str
    contract_id: str
    original_end_date: date
    new_end_date: date
    additional_days: int
    additional_amount: Decimal
    reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AvailabilitySlot:
    """Créneau de disponibilité."""
    date: date
    is_available: bool
    price: Decimal
    reserved_by: Optional[str] = None
    contract_id: Optional[str] = None


@dataclass
class RentalStats:
    """Statistiques de location."""
    tenant_id: str
    period_start: date
    period_end: date
    total_items: int = 0
    items_rented: int = 0
    utilization_rate: Decimal = Decimal("0")
    total_contracts: int = 0
    active_contracts: int = 0
    total_revenue: Decimal = Decimal("0")
    total_deposits: Decimal = Decimal("0")
    avg_rental_duration_days: Decimal = Decimal("0")
    top_rented_items: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class RentalService:
    """Service de gestion de location."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (simulation)
        self._items: Dict[str, RentalItem] = {}
        self._contracts: Dict[str, RentalContract] = {}
        self._lines: Dict[str, List[ContractLine]] = {}
        self._inspections: Dict[str, Inspection] = {}
        self._reservations: Dict[str, Reservation] = {}
        self._extensions: Dict[str, Extension] = {}
        self._pricing_rules: Dict[str, PricingRule] = {}

        self._contract_counter = 0

    # -------------------------------------------------------------------------
    # Articles locatifs
    # -------------------------------------------------------------------------

    def create_item(
        self,
        name: str,
        description: str,
        item_type: RentalItemType,
        **kwargs
    ) -> RentalItem:
        """Crée un article locatif."""
        item_id = str(uuid4())

        item = RentalItem(
            id=item_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            item_type=item_type,
            **kwargs
        )

        self._items[item_id] = item
        return item

    def get_item(self, item_id: str) -> Optional[RentalItem]:
        """Récupère un article."""
        item = self._items.get(item_id)
        if item and item.tenant_id == self.tenant_id:
            return item
        return None

    def update_item(self, item_id: str, **updates) -> Optional[RentalItem]:
        """Met à jour un article."""
        item = self.get_item(item_id)
        if not item:
            return None

        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)

        item.updated_at = datetime.now()
        return item

    def list_items(
        self,
        *,
        item_type: Optional[RentalItemType] = None,
        status: Optional[RentalItemStatus] = None,
        category_id: Optional[str] = None,
        available_only: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[RentalItem], int]:
        """Liste les articles."""
        results = []

        for item in self._items.values():
            if item.tenant_id != self.tenant_id:
                continue
            if not item.is_active:
                continue
            if item_type and item.item_type != item_type:
                continue
            if status and item.status != status:
                continue
            if category_id and item.category_id != category_id:
                continue
            if available_only and item.status != RentalItemStatus.AVAILABLE:
                continue
            results.append(item)

        results.sort(key=lambda x: x.name)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    def check_availability(
        self,
        item_id: str,
        start_date: date,
        end_date: date
    ) -> List[AvailabilitySlot]:
        """Vérifie la disponibilité d'un article."""
        item = self.get_item(item_id)
        if not item:
            return []

        slots = []
        current = start_date

        # Récupérer les contrats existants
        booked_dates = set()
        for contract in self._contracts.values():
            if contract.tenant_id != self.tenant_id:
                continue
            if contract.status not in [ContractStatus.ACTIVE, ContractStatus.EXTENDED]:
                continue

            lines = self._lines.get(contract.id, [])
            for line in lines:
                if line.item_id != item_id:
                    continue
                line_start = line.start_date or contract.start_date
                line_end = line.actual_return_date or line.end_date or contract.end_date

                if line_end:
                    d = line_start
                    while d <= line_end:
                        booked_dates.add(d)
                        d += timedelta(days=1)

        # Vérifier aussi les réservations
        for res in self._reservations.values():
            if res.tenant_id != self.tenant_id:
                continue
            if res.item_id != item_id:
                continue
            if res.status not in ["pending", "confirmed"]:
                continue

            d = res.start_date
            while d <= res.end_date:
                booked_dates.add(d)
                d += timedelta(days=1)

        # Générer les créneaux
        while current <= end_date:
            is_available = current not in booked_dates and item.status != RentalItemStatus.OUT_OF_SERVICE

            # Calculer le prix
            price = self._calculate_daily_price(item, current)

            slot = AvailabilitySlot(
                date=current,
                is_available=is_available,
                price=price
            )
            slots.append(slot)

            current += timedelta(days=1)

        return slots

    # -------------------------------------------------------------------------
    # Contrats
    # -------------------------------------------------------------------------

    def create_contract(
        self,
        customer_id: str,
        customer_name: str,
        items: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        **kwargs
    ) -> RentalContract:
        """Crée un contrat de location."""
        contract_id = str(uuid4())
        self._contract_counter += 1
        reference = f"LOC-{datetime.now().strftime('%Y%m')}-{self._contract_counter:04d}"

        contract = RentalContract(
            id=contract_id,
            tenant_id=self.tenant_id,
            reference=reference,
            customer_id=customer_id,
            customer_name=customer_name,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )

        # Créer les lignes
        lines = []
        total = Decimal("0")
        total_deposit = Decimal("0")

        for item_data in items:
            item = self.get_item(item_data["item_id"])
            if not item:
                continue

            quantity = item_data.get("quantity", 1)
            days = (end_date - start_date).days + 1

            # Calculer le prix
            unit_price = self._calculate_price(item, start_date, end_date)
            line_total = unit_price * quantity

            line = ContractLine(
                id=str(uuid4()),
                contract_id=contract_id,
                item_id=item.id,
                item_name=item.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=line_total,
                deposit_per_unit=item.default_deposit,
                start_date=start_date,
                end_date=end_date
            )

            lines.append(line)
            total += line_total
            total_deposit += item.default_deposit * quantity

        self._lines[contract_id] = lines

        # Calculer les totaux
        contract.subtotal = total
        contract.total_amount = total  # Simplification
        contract.deposit_amount = total_deposit
        contract.balance_due = total + total_deposit
        contract.items = [{"item_id": l.item_id, "item_name": l.item_name, "quantity": l.quantity} for l in lines]

        self._contracts[contract_id] = contract

        return contract

    def get_contract(self, contract_id: str) -> Optional[RentalContract]:
        """Récupère un contrat."""
        contract = self._contracts.get(contract_id)
        if contract and contract.tenant_id == self.tenant_id:
            return contract
        return None

    def activate_contract(
        self,
        contract_id: str,
        deposit_received: bool = True
    ) -> Optional[RentalContract]:
        """Active un contrat."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None

        if contract.status not in [ContractStatus.DRAFT, ContractStatus.PENDING_APPROVAL]:
            return None

        contract.status = ContractStatus.ACTIVE
        contract.signed_at = datetime.now()

        if deposit_received:
            contract.deposit_status = DepositStatus.RECEIVED
            contract.deposit_received_date = date.today()
            contract.amount_paid = contract.deposit_amount
            contract.balance_due = contract.total_amount

        # Marquer les articles comme loués
        lines = self._lines.get(contract_id, [])
        for line in lines:
            item = self.get_item(line.item_id)
            if item:
                item.status = RentalItemStatus.RENTED
                item.total_rentals += 1

        contract.updated_at = datetime.now()

        return contract

    def end_contract(
        self,
        contract_id: str,
        return_date: Optional[date] = None
    ) -> Optional[RentalContract]:
        """Termine un contrat."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None

        if contract.status not in [ContractStatus.ACTIVE, ContractStatus.EXTENDED]:
            return None

        contract.status = ContractStatus.ENDED
        contract.actual_return_date = return_date or date.today()

        # Libérer les articles
        lines = self._lines.get(contract_id, [])
        for line in lines:
            line.actual_return_date = contract.actual_return_date
            item = self.get_item(line.item_id)
            if item:
                item.status = RentalItemStatus.AVAILABLE
                item.total_revenue += line.total_price

        # Calculer les frais supplémentaires (retard, dommages)
        self._calculate_final_charges(contract)

        contract.updated_at = datetime.now()

        return contract

    def extend_contract(
        self,
        contract_id: str,
        new_end_date: date,
        reason: Optional[str] = None
    ) -> Optional[Extension]:
        """Prolonge un contrat."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None

        if contract.status not in [ContractStatus.ACTIVE, ContractStatus.EXTENDED]:
            return None

        if not contract.end_date or new_end_date <= contract.end_date:
            return None

        additional_days = (new_end_date - contract.end_date).days

        # Calculer le coût supplémentaire
        lines = self._lines.get(contract_id, [])
        additional_amount = Decimal("0")

        for line in lines:
            item = self.get_item(line.item_id)
            if item:
                daily_rate = self._calculate_daily_price(item, new_end_date)
                additional_amount += daily_rate * additional_days * line.quantity

        extension_id = str(uuid4())
        extension = Extension(
            id=extension_id,
            contract_id=contract_id,
            original_end_date=contract.end_date,
            new_end_date=new_end_date,
            additional_days=additional_days,
            additional_amount=additional_amount,
            reason=reason
        )

        self._extensions[extension_id] = extension

        # Mettre à jour le contrat
        contract.end_date = new_end_date
        contract.status = ContractStatus.EXTENDED
        contract.total_amount += additional_amount
        contract.balance_due += additional_amount

        # Mettre à jour les lignes
        for line in lines:
            line.end_date = new_end_date

        contract.updated_at = datetime.now()

        return extension

    def list_contracts(
        self,
        *,
        status: Optional[ContractStatus] = None,
        customer_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[RentalContract], int]:
        """Liste les contrats."""
        results = []

        for contract in self._contracts.values():
            if contract.tenant_id != self.tenant_id:
                continue
            if status and contract.status != status:
                continue
            if customer_id and contract.customer_id != customer_id:
                continue
            if from_date and contract.start_date < from_date:
                continue
            if to_date and contract.start_date > to_date:
                continue
            results.append(contract)

        results.sort(key=lambda x: x.created_at, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    def get_contract_lines(self, contract_id: str) -> List[ContractLine]:
        """Récupère les lignes d'un contrat."""
        contract = self.get_contract(contract_id)
        if not contract:
            return []
        return self._lines.get(contract_id, [])

    # -------------------------------------------------------------------------
    # Inspections
    # -------------------------------------------------------------------------

    def create_inspection(
        self,
        contract_id: str,
        item_id: str,
        inspection_type: InspectionType,
        overall_condition: InspectionCondition,
        performed_by: Optional[str] = None,
        **kwargs
    ) -> Optional[Inspection]:
        """Crée une inspection."""
        contract = self.get_contract(contract_id)
        item = self.get_item(item_id)

        if not contract or not item:
            return None

        inspection_id = str(uuid4())

        inspection = Inspection(
            id=inspection_id,
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            item_id=item_id,
            inspection_type=inspection_type,
            overall_condition=overall_condition,
            performed_by=performed_by,
            **kwargs
        )

        self._inspections[inspection_id] = inspection

        # Mettre à jour la condition de l'article
        item.condition = overall_condition

        # Mettre à jour la ligne de contrat
        lines = self._lines.get(contract_id, [])
        for line in lines:
            if line.item_id == item_id:
                if inspection_type == InspectionType.CHECK_OUT:
                    line.condition_at_checkout = overall_condition
                elif inspection_type == InspectionType.CHECK_IN:
                    line.condition_at_checkin = overall_condition

        return inspection

    def get_inspections(
        self,
        contract_id: str,
        item_id: Optional[str] = None
    ) -> List[Inspection]:
        """Liste les inspections d'un contrat."""
        results = []

        for insp in self._inspections.values():
            if insp.tenant_id != self.tenant_id:
                continue
            if insp.contract_id != contract_id:
                continue
            if item_id and insp.item_id != item_id:
                continue
            results.append(insp)

        results.sort(key=lambda x: x.date)
        return results

    # -------------------------------------------------------------------------
    # Réservations
    # -------------------------------------------------------------------------

    def create_reservation(
        self,
        customer_id: str,
        customer_name: str,
        item_id: str,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> Optional[Reservation]:
        """Crée une réservation."""
        item = self.get_item(item_id)
        if not item:
            return None

        # Vérifier disponibilité
        slots = self.check_availability(item_id, start_date, end_date)
        if not all(slot.is_available for slot in slots):
            return None

        res_id = str(uuid4())

        # Calculer le montant
        quoted_amount = self._calculate_price(item, start_date, end_date)

        reservation = Reservation(
            id=res_id,
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            customer_name=customer_name,
            item_id=item_id,
            item_name=item.name,
            start_date=start_date,
            end_date=end_date,
            quoted_amount=quoted_amount,
            deposit_required=item.default_deposit,
            expires_at=datetime.now() + timedelta(hours=24),
            **kwargs
        )

        self._reservations[res_id] = reservation

        # Marquer l'article comme réservé
        item.status = RentalItemStatus.RESERVED

        return reservation

    def confirm_reservation(self, reservation_id: str) -> Optional[Reservation]:
        """Confirme une réservation."""
        reservation = self._reservations.get(reservation_id)
        if not reservation or reservation.tenant_id != self.tenant_id:
            return None

        reservation.status = "confirmed"
        return reservation

    def convert_reservation_to_contract(
        self,
        reservation_id: str
    ) -> Optional[RentalContract]:
        """Convertit une réservation en contrat."""
        reservation = self._reservations.get(reservation_id)
        if not reservation or reservation.tenant_id != self.tenant_id:
            return None

        if reservation.status != "confirmed":
            return None

        # Créer le contrat
        contract = self.create_contract(
            customer_id=reservation.customer_id,
            customer_name=reservation.customer_name,
            items=[{
                "item_id": reservation.item_id,
                "quantity": 1
            }],
            start_date=reservation.start_date,
            end_date=reservation.end_date
        )

        reservation.status = "converted"
        reservation.contract_id = contract.id

        return contract

    def cancel_reservation(self, reservation_id: str) -> bool:
        """Annule une réservation."""
        reservation = self._reservations.get(reservation_id)
        if not reservation or reservation.tenant_id != self.tenant_id:
            return False

        reservation.status = "cancelled"

        # Libérer l'article
        item = self.get_item(reservation.item_id)
        if item and item.status == RentalItemStatus.RESERVED:
            item.status = RentalItemStatus.AVAILABLE

        return True

    def list_reservations(
        self,
        *,
        item_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None
    ) -> List[Reservation]:
        """Liste les réservations."""
        results = []

        for res in self._reservations.values():
            if res.tenant_id != self.tenant_id:
                continue
            if item_id and res.item_id != item_id:
                continue
            if customer_id and res.customer_id != customer_id:
                continue
            if status and res.status != status:
                continue
            if from_date and res.end_date < from_date:
                continue
            results.append(res)

        results.sort(key=lambda x: x.start_date)
        return results

    # -------------------------------------------------------------------------
    # Tarification
    # -------------------------------------------------------------------------

    def create_pricing_rule(
        self,
        name: str,
        pricing_type: PricingType,
        base_price: Decimal,
        **kwargs
    ) -> PricingRule:
        """Crée une règle de tarification."""
        rule_id = str(uuid4())

        rule = PricingRule(
            id=rule_id,
            name=name,
            pricing_type=pricing_type,
            base_price=base_price,
            **kwargs
        )

        self._pricing_rules[rule_id] = rule
        return rule

    def _calculate_price(
        self,
        item: RentalItem,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """Calcule le prix total pour une période."""
        days = (end_date - start_date).days + 1
        total = Decimal("0")

        current = start_date
        while current <= end_date:
            total += self._calculate_daily_price(item, current)
            current += timedelta(days=1)

        return total

    def _calculate_daily_price(self, item: RentalItem, target_date: date) -> Decimal:
        """Calcule le prix journalier."""
        if item.pricing_rule_id:
            rule = self._pricing_rules.get(item.pricing_rule_id)
            if rule:
                price = rule.base_price

                # Supplément week-end
                if target_date.weekday() >= 5:
                    price = price * (1 + rule.weekend_surcharge_percent / 100)

                return price

        # Prix par défaut basé sur la valeur de remplacement
        return item.replacement_value * Decimal("0.01")  # 1% par jour

    def _calculate_final_charges(self, contract: RentalContract):
        """Calcule les frais finaux."""
        if not contract.actual_return_date or not contract.end_date:
            return

        lines = self._lines.get(contract.id, [])

        # Vérifier retard
        if contract.actual_return_date > contract.end_date:
            late_days = (contract.actual_return_date - contract.end_date).days
            late_fee = Decimal("0")

            for line in lines:
                item = self.get_item(line.item_id)
                if item:
                    daily_rate = self._calculate_daily_price(item, contract.actual_return_date)
                    # Pénalité: 150% du tarif normal
                    late_fee += daily_rate * Decimal("1.5") * late_days * line.quantity

            contract.total_amount += late_fee
            contract.balance_due += late_fee

        # Dommages
        for line in lines:
            if line.damage_charge > 0:
                contract.total_amount += line.damage_charge
                contract.balance_due += line.damage_charge

    # -------------------------------------------------------------------------
    # Dépôts
    # -------------------------------------------------------------------------

    def record_deposit_payment(
        self,
        contract_id: str,
        amount: Decimal
    ) -> Optional[RentalContract]:
        """Enregistre un paiement de dépôt."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None

        contract.amount_paid += amount
        contract.deposit_status = DepositStatus.RECEIVED
        contract.deposit_received_date = date.today()

        if contract.amount_paid >= contract.deposit_amount + contract.total_amount:
            contract.balance_due = Decimal("0")
        else:
            contract.balance_due = contract.deposit_amount + contract.total_amount - contract.amount_paid

        contract.updated_at = datetime.now()

        return contract

    def refund_deposit(
        self,
        contract_id: str,
        amount: Decimal,
        deductions: Optional[Dict[str, Decimal]] = None
    ) -> Optional[RentalContract]:
        """Rembourse le dépôt."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None

        if contract.status != ContractStatus.ENDED:
            return None

        total_deductions = Decimal("0")
        if deductions:
            total_deductions = sum(deductions.values())

        refund_amount = contract.deposit_amount - total_deductions

        if refund_amount >= contract.deposit_amount:
            contract.deposit_status = DepositStatus.FULLY_REFUNDED
        elif refund_amount > 0:
            contract.deposit_status = DepositStatus.PARTIALLY_REFUNDED
        else:
            contract.deposit_status = DepositStatus.RETAINED

        contract.updated_at = datetime.now()

        return contract

    # -------------------------------------------------------------------------
    # Statistiques
    # -------------------------------------------------------------------------

    def get_statistics(
        self,
        period_start: date,
        period_end: date
    ) -> RentalStats:
        """Calcule les statistiques de location."""
        stats = RentalStats(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end
        )

        # Compter les articles
        item_rental_counts = {}
        for item in self._items.values():
            if item.tenant_id != self.tenant_id:
                continue
            if not item.is_active:
                continue
            stats.total_items += 1
            if item.status == RentalItemStatus.RENTED:
                stats.items_rented += 1
            item_rental_counts[item.id] = {"name": item.name, "count": 0, "revenue": Decimal("0")}

        if stats.total_items > 0:
            stats.utilization_rate = Decimal(stats.items_rented) / Decimal(stats.total_items) * 100

        # Analyser les contrats
        total_days = 0
        contract_count = 0

        for contract in self._contracts.values():
            if contract.tenant_id != self.tenant_id:
                continue
            if contract.start_date < period_start or contract.start_date > period_end:
                continue

            stats.total_contracts += 1

            if contract.status in [ContractStatus.ACTIVE, ContractStatus.EXTENDED]:
                stats.active_contracts += 1

            if contract.status == ContractStatus.ENDED:
                stats.total_revenue += contract.total_amount
                stats.total_deposits += contract.deposit_amount

                if contract.end_date and contract.start_date:
                    days = (contract.end_date - contract.start_date).days + 1
                    total_days += days
                    contract_count += 1

                # Comptage par article
                lines = self._lines.get(contract.id, [])
                for line in lines:
                    if line.item_id in item_rental_counts:
                        item_rental_counts[line.item_id]["count"] += 1
                        item_rental_counts[line.item_id]["revenue"] += line.total_price

        if contract_count > 0:
            stats.avg_rental_duration_days = Decimal(total_days) / Decimal(contract_count)

        # Top articles
        top_items = sorted(
            [v for v in item_rental_counts.values() if v["count"] > 0],
            key=lambda x: x["revenue"],
            reverse=True
        )[:5]
        stats.top_rented_items = top_items

        return stats


# ============================================================================
# FACTORY
# ============================================================================

def create_rental_service(tenant_id: str) -> RentalService:
    """Factory pour créer un service de location."""
    return RentalService(tenant_id)
