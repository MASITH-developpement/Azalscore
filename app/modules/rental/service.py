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
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .repository import (
    PricingRuleRepository,
    RentalItemRepository,
    ContractRepository,
    ContractLineRepository,
    InspectionRepository,
    ReservationRepository,
    ExtensionRepository,
    RentalStatsRepository,
)
from .models import (
    RentalItemType,
    RentalItemStatus,
    ContractStatus,
    PricingType,
    InspectionType,
    InspectionCondition,
    DepositStatus,
    RentalItem,
    RentalContract,
    RentalContractLine,
    Inspection,
    Reservation,
    Extension,
    PricingRule,
)


# ============================================================================
# DATA CLASSES (pour compatibilité API)
# ============================================================================

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
    """Service de gestion de location avec persistance SQLAlchemy."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self.pricing_repo = PricingRuleRepository(db, tenant_id)
        self.item_repo = RentalItemRepository(db, tenant_id)
        self.contract_repo = ContractRepository(db, tenant_id)
        self.line_repo = ContractLineRepository(db, tenant_id)
        self.inspection_repo = InspectionRepository(db, tenant_id)
        self.reservation_repo = ReservationRepository(db, tenant_id)
        self.extension_repo = ExtensionRepository(db, tenant_id)
        self.stats_repo = RentalStatsRepository(db, tenant_id)

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
        return self.item_repo.create(
            name=name,
            description=description,
            item_type=item_type,
            sku=kwargs.get("sku"),
            serial_number=kwargs.get("serial_number"),
            category_id=kwargs.get("category_id"),
            location=kwargs.get("location"),
            pricing_rule_id=kwargs.get("pricing_rule_id"),
            default_deposit=kwargs.get("default_deposit", Decimal("0")),
            replacement_value=kwargs.get("replacement_value", Decimal("0")),
            images=kwargs.get("images"),
            specifications=kwargs.get("specifications"),
            maintenance_interval_days=kwargs.get("maintenance_interval_days"),
            notes=kwargs.get("notes"),
        )

    def get_item(self, item_id: str) -> Optional[RentalItem]:
        """Récupère un article."""
        return self.item_repo.get_by_id(item_id)

    def update_item(self, item_id: str, **updates) -> Optional[RentalItem]:
        """Met à jour un article."""
        return self.item_repo.update(item_id, **updates)

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
        return self.item_repo.list_all(
            item_type=item_type,
            status=status,
            category_id=category_id,
            available_only=available_only,
            page=page,
            page_size=page_size,
        )

    def check_availability(
        self,
        item_id: str,
        start_date: date,
        end_date: date
    ) -> List[AvailabilitySlot]:
        """Vérifie la disponibilité d'un article."""
        raw_slots = self.item_repo.check_availability(item_id, start_date, end_date)
        return [
            AvailabilitySlot(
                date=slot["date"],
                is_available=slot["is_available"],
                price=slot["price"],
                reserved_by=slot.get("reserved_by"),
                contract_id=slot.get("contract_id"),
            )
            for slot in raw_slots
        ]

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
        # Créer le contrat
        contract = self.contract_repo.create(
            customer_id=customer_id,
            customer_name=customer_name,
            start_date=start_date,
            end_date=end_date,
            pricing_type=kwargs.get("pricing_type", PricingType.DAILY),
            billing_frequency=kwargs.get("billing_frequency", "on_return"),
            delivery_address=kwargs.get("delivery_address"),
            delivery_date=kwargs.get("delivery_date"),
            pickup_address=kwargs.get("pickup_address"),
            pickup_date=kwargs.get("pickup_date"),
            notes=kwargs.get("notes"),
            created_by=kwargs.get("created_by"),
        )

        # Créer les lignes
        for item_data in items:
            item = self.item_repo.get_by_id(item_data["item_id"])
            if not item:
                continue

            quantity = item_data.get("quantity", 1)

            # Calculer le prix
            unit_price = self._calculate_price(item, start_date, end_date)

            self.line_repo.create(
                contract_id=str(contract.id),
                item_id=str(item.id),
                item_name=item.name,
                quantity=quantity,
                unit_price=unit_price,
                deposit_per_unit=item.default_deposit,
                start_date=start_date,
                end_date=end_date,
            )

        # Recalculer les totaux
        self.contract_repo.recalculate_totals(str(contract.id))

        # Rafraîchir le contrat
        return self.contract_repo.get_by_id(str(contract.id))

    def get_contract(self, contract_id: str) -> Optional[RentalContract]:
        """Récupère un contrat."""
        return self.contract_repo.get_by_id(contract_id)

    def activate_contract(
        self,
        contract_id: str,
        deposit_received: bool = True
    ) -> Optional[RentalContract]:
        """Active un contrat."""
        return self.contract_repo.activate(contract_id, deposit_received)

    def end_contract(
        self,
        contract_id: str,
        return_date: Optional[date] = None
    ) -> Optional[RentalContract]:
        """Termine un contrat."""
        contract = self.contract_repo.end_contract(contract_id, return_date)
        if contract:
            # Calculer les frais supplémentaires
            self._calculate_final_charges(contract)
        return contract

    def extend_contract(
        self,
        contract_id: str,
        new_end_date: date,
        reason: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> Optional[Extension]:
        """Prolonge un contrat."""
        contract = self.contract_repo.get_by_id(contract_id)
        if not contract:
            return None

        if contract.status not in [ContractStatus.ACTIVE, ContractStatus.EXTENDED]:
            return None

        if not contract.end_date or new_end_date <= contract.end_date:
            return None

        # Calculer le coût supplémentaire
        lines = self.line_repo.list_by_contract(contract_id)
        additional_amount = Decimal("0")
        additional_days = (new_end_date - contract.end_date).days

        for line in lines:
            item = self.item_repo.get_by_id(str(line.item_id))
            if item:
                daily_rate = self._calculate_daily_price(item, new_end_date)
                additional_amount += daily_rate * additional_days * line.quantity

        # Créer l'extension
        extension = self.extension_repo.create(
            contract_id=contract_id,
            original_end_date=contract.end_date,
            new_end_date=new_end_date,
            additional_amount=additional_amount,
            reason=reason,
            approved_by=approved_by,
        )

        # Mettre à jour le contrat
        self.contract_repo.update(
            contract_id,
            end_date=new_end_date,
            status=ContractStatus.EXTENDED,
            total_amount=contract.total_amount + additional_amount,
            balance_due=contract.balance_due + additional_amount,
        )

        # Mettre à jour les lignes
        for line in lines:
            self.line_repo.update(str(line.id), end_date=new_end_date)

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
        return self.contract_repo.list_all(
            status=status,
            customer_id=customer_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

    def get_contract_lines(self, contract_id: str) -> List[RentalContractLine]:
        """Récupère les lignes d'un contrat."""
        contract = self.get_contract(contract_id)
        if not contract:
            return []
        return self.line_repo.list_by_contract(contract_id)

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

        inspection = self.inspection_repo.create(
            contract_id=contract_id,
            item_id=item_id,
            inspection_type=inspection_type,
            overall_condition=overall_condition,
            performed_by=performed_by,
            mileage=kwargs.get("mileage"),
            fuel_level=kwargs.get("fuel_level"),
            cleanliness=kwargs.get("cleanliness", "clean"),
            photos=kwargs.get("photos"),
            checklist_items=kwargs.get("checklist_items"),
            damages_found=kwargs.get("damages_found"),
            notes=kwargs.get("notes"),
        )

        # Mettre à jour la condition de l'article
        self.item_repo.update(item_id, condition=overall_condition)

        # Mettre à jour la ligne de contrat
        lines = self.line_repo.list_by_contract(contract_id)
        for line in lines:
            if str(line.item_id) == item_id:
                if inspection_type == InspectionType.CHECK_OUT:
                    self.line_repo.update(str(line.id), condition_at_checkout=overall_condition)
                elif inspection_type == InspectionType.CHECK_IN:
                    self.line_repo.update(str(line.id), condition_at_checkin=overall_condition)

        return inspection

    def get_inspections(
        self,
        contract_id: str,
        item_id: Optional[str] = None
    ) -> List[Inspection]:
        """Liste les inspections d'un contrat."""
        return self.inspection_repo.list_by_contract(contract_id, item_id)

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
        if not self.reservation_repo.check_availability(item_id, start_date, end_date):
            return None

        # Calculer le montant
        quoted_amount = self._calculate_price(item, start_date, end_date)

        return self.reservation_repo.create(
            customer_id=customer_id,
            customer_name=customer_name,
            item_id=item_id,
            item_name=item.name,
            start_date=start_date,
            end_date=end_date,
            quoted_amount=quoted_amount,
            deposit_required=item.default_deposit,
            notes=kwargs.get("notes"),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

    def confirm_reservation(self, reservation_id: str) -> Optional[Reservation]:
        """Confirme une réservation."""
        return self.reservation_repo.confirm(reservation_id)

    def convert_reservation_to_contract(
        self,
        reservation_id: str
    ) -> Optional[RentalContract]:
        """Convertit une réservation en contrat."""
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            return None

        # Créer le contrat
        contract = self.create_contract(
            customer_id=reservation.customer_id,
            customer_name=reservation.customer_name,
            items=[{
                "item_id": str(reservation.item_id),
                "quantity": 1
            }],
            start_date=reservation.start_date,
            end_date=reservation.end_date
        )

        if contract:
            # Marquer la réservation comme convertie
            self.reservation_repo.convert_to_contract(reservation_id, str(contract.id))

        return contract

    def cancel_reservation(self, reservation_id: str) -> bool:
        """Annule une réservation."""
        return self.reservation_repo.cancel(reservation_id)

    def list_reservations(
        self,
        *,
        item_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None
    ) -> List[Reservation]:
        """Liste les réservations."""
        from .models import ReservationStatus

        status_enum = None
        if status:
            try:
                status_enum = ReservationStatus(status)
            except ValueError:
                pass

        return self.reservation_repo.list_all(
            item_id=item_id,
            customer_id=customer_id,
            status=status_enum,
            from_date=from_date,
        )

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
        return self.pricing_repo.create(
            name=name,
            pricing_type=pricing_type,
            base_price=base_price,
            currency=kwargs.get("currency", "EUR"),
            min_duration=kwargs.get("min_duration", 1),
            max_duration=kwargs.get("max_duration"),
            discount_percent=kwargs.get("discount_percent", Decimal("0")),
            weekend_surcharge_percent=kwargs.get("weekend_surcharge_percent", Decimal("0")),
            holiday_surcharge_percent=kwargs.get("holiday_surcharge_percent", Decimal("0")),
            season_adjustments=kwargs.get("season_adjustments"),
        )

    def _calculate_price(
        self,
        item: RentalItem,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """Calcule le prix total pour une période."""
        total = Decimal("0")
        current = start_date

        while current <= end_date:
            total += self._calculate_daily_price(item, current)
            current += timedelta(days=1)

        return total

    def _calculate_daily_price(self, item: RentalItem, target_date: date) -> Decimal:
        """Calcule le prix journalier."""
        if item.pricing_rule_id:
            rule = self.pricing_repo.get_by_id(str(item.pricing_rule_id))
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

        lines = self.line_repo.list_by_contract(str(contract.id))

        # Vérifier retard
        if contract.actual_return_date > contract.end_date:
            late_days = (contract.actual_return_date - contract.end_date).days
            late_fee = Decimal("0")

            for line in lines:
                item = self.item_repo.get_by_id(str(line.item_id))
                if item:
                    daily_rate = self._calculate_daily_price(item, contract.actual_return_date)
                    # Pénalité: 150% du tarif normal
                    late_fee += daily_rate * Decimal("1.5") * late_days * line.quantity

            if late_fee > 0:
                self.contract_repo.update(
                    str(contract.id),
                    total_amount=contract.total_amount + late_fee,
                    balance_due=contract.balance_due + late_fee,
                )

        # Dommages
        total_damage = sum(line.damage_charge or Decimal("0") for line in lines)
        if total_damage > 0:
            self.contract_repo.update(
                str(contract.id),
                total_amount=contract.total_amount + total_damage,
                balance_due=contract.balance_due + total_damage,
            )

    # -------------------------------------------------------------------------
    # Dépôts
    # -------------------------------------------------------------------------

    def record_deposit_payment(
        self,
        contract_id: str,
        amount: Decimal
    ) -> Optional[RentalContract]:
        """Enregistre un paiement de dépôt."""
        contract = self.contract_repo.get_by_id(contract_id)
        if not contract:
            return None

        new_amount_paid = contract.amount_paid + amount
        new_balance = contract.deposit_amount + contract.total_amount - new_amount_paid

        return self.contract_repo.update(
            contract_id,
            amount_paid=new_amount_paid,
            deposit_status=DepositStatus.RECEIVED,
            deposit_received_date=date.today(),
            balance_due=max(Decimal("0"), new_balance),
        )

    def refund_deposit(
        self,
        contract_id: str,
        amount: Decimal,
        deductions: Optional[Dict[str, Decimal]] = None
    ) -> Optional[RentalContract]:
        """Rembourse le dépôt."""
        return self.contract_repo.refund_deposit(contract_id, amount, deductions)

    # -------------------------------------------------------------------------
    # Statistiques
    # -------------------------------------------------------------------------

    def get_statistics(
        self,
        period_start: date,
        period_end: date
    ) -> RentalStats:
        """Calcule les statistiques de location."""
        raw_stats = self.stats_repo.get_statistics(period_start, period_end)

        return RentalStats(
            tenant_id=raw_stats["tenant_id"],
            period_start=raw_stats["period_start"],
            period_end=raw_stats["period_end"],
            total_items=raw_stats["total_items"],
            items_rented=raw_stats["items_rented"],
            utilization_rate=raw_stats["utilization_rate"],
            total_contracts=raw_stats["total_contracts"],
            active_contracts=raw_stats["active_contracts"],
            total_revenue=raw_stats["total_revenue"],
            total_deposits=raw_stats["total_deposits"],
            avg_rental_duration_days=raw_stats["avg_rental_duration_days"],
            top_rented_items=raw_stats["top_rented_items"],
        )


# ============================================================================
# FACTORY
# ============================================================================

def create_rental_service(db: Session, tenant_id: str) -> RentalService:
    """Factory pour créer un service de location."""
    return RentalService(db, tenant_id)
