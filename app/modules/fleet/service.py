"""
Service Fleet Management - GAP-062

Logique metier complete pour la gestion de flotte:
- Vehicules et conducteurs
- Contrats (leasing, assurance, entretien)
- Suivi kilometrage et consommation
- Entretiens et reparations
- Controles techniques
- Amendes et sinistres
- Calcul TCO
- Alertes et echeances
- Dashboard et rapports
"""
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from .models import (
    FleetVehicle, FleetDriver, FleetContract, FleetMileageLog,
    FleetFuelEntry, FleetMaintenance, FleetDocument, FleetIncident,
    FleetCost, FleetAlert,
    VehicleStatus, VehicleType, FuelType, ContractType, ContractStatus,
    MaintenanceType, MaintenanceStatus, DocumentType, IncidentType, IncidentStatus,
    AlertType, AlertSeverity
)
from .repository import (
    VehicleRepository, DriverRepository, ContractRepository,
    FuelEntryRepository, MaintenanceRepository, DocumentRepository,
    IncidentRepository, CostRepository, AlertRepository, MileageLogRepository
)
from .schemas import (
    VehicleFilters, DriverFilters, ContractFilters,
    MaintenanceFilters, IncidentFilters, AlertFilters,
    FleetDashboard, TCOReport, ConsumptionStats
)
from .exceptions import (
    VehicleNotFoundError, VehicleDuplicateError, VehicleStateError,
    DriverNotFoundError, DriverDuplicateError, DriverLicenseExpiredError,
    ContractNotFoundError, ContractDuplicateError,
    MaintenanceNotFoundError, MaintenanceDuplicateError, MaintenanceStateError,
    IncidentNotFoundError, IncidentDuplicateError,
    FuelEntryNotFoundError, FuelAnomalyError,
    DocumentNotFoundError, AlertNotFoundError,
    MileageDecrementError, CodeGenerationError
)

logger = logging.getLogger(__name__)


class FleetService:
    """
    Service de gestion de flotte vehicules.

    Fonctionnalites:
    - CRUD vehicules et conducteurs
    - Gestion des contrats
    - Suivi kilometrage
    - Consommation carburant avec detection anomalies
    - Planification et suivi entretiens
    - Gestion documents et echeances
    - Incidents, sinistres et amendes
    - Calcul TCO (Total Cost of Ownership)
    - Alertes automatiques
    - Dashboard et rapports
    """

    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Repositories
        self.vehicle_repo = VehicleRepository(db, tenant_id)
        self.driver_repo = DriverRepository(db, tenant_id)
        self.contract_repo = ContractRepository(db, tenant_id)
        self.fuel_repo = FuelEntryRepository(db, tenant_id)
        self.maintenance_repo = MaintenanceRepository(db, tenant_id)
        self.document_repo = DocumentRepository(db, tenant_id)
        self.incident_repo = IncidentRepository(db, tenant_id)
        self.cost_repo = CostRepository(db, tenant_id)
        self.alert_repo = AlertRepository(db, tenant_id)
        self.mileage_repo = MileageLogRepository(db, tenant_id)

    # =========================================================================
    # VEHICLES
    # =========================================================================

    def create_vehicle(self, data: Dict[str, Any]) -> FleetVehicle:
        """Cree un nouveau vehicule."""
        # Generer code si non fourni
        if not data.get('code'):
            data['code'] = self._generate_code('VEH')

        # Verifier unicite
        if self.vehicle_repo.code_exists(data['code']):
            raise VehicleDuplicateError('code', data['code'])

        if self.vehicle_repo.registration_exists(data['registration_number']):
            raise VehicleDuplicateError('registration_number', data['registration_number'])

        vehicle = self.vehicle_repo.create(data, self.user_id)

        logger.info(f"Vehicle created: {vehicle.code} - {vehicle.registration_number}")
        return vehicle

    def update_vehicle(self, vehicle_id: UUID, data: Dict[str, Any]) -> FleetVehicle:
        """Met a jour un vehicule."""
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(vehicle_id=str(vehicle_id))

        # Verifier unicite si changement
        if data.get('code') and data['code'] != vehicle.code:
            if self.vehicle_repo.code_exists(data['code'], exclude_id=vehicle_id):
                raise VehicleDuplicateError('code', data['code'])

        if data.get('registration_number') and data['registration_number'] != vehicle.registration_number:
            if self.vehicle_repo.registration_exists(data['registration_number'], exclude_id=vehicle_id):
                raise VehicleDuplicateError('registration_number', data['registration_number'])

        return self.vehicle_repo.update(vehicle, data, self.user_id)

    def get_vehicle(self, vehicle_id: UUID) -> FleetVehicle:
        """Recupere un vehicule."""
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(vehicle_id=str(vehicle_id))
        return vehicle

    def list_vehicles(
        self,
        filters: VehicleFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[FleetVehicle], int]:
        """Liste les vehicules avec filtres et pagination."""
        return self.vehicle_repo.list(filters, page, page_size, sort_by, sort_dir)

    def delete_vehicle(self, vehicle_id: UUID) -> bool:
        """Supprime (soft delete) un vehicule."""
        vehicle = self.get_vehicle(vehicle_id)

        can_delete, reason = vehicle.can_delete()
        if not can_delete:
            raise VehicleStateError(vehicle.status.value, "delete")

        return self.vehicle_repo.soft_delete(vehicle, self.user_id)

    def assign_driver(self, vehicle_id: UUID, driver_id: UUID) -> FleetVehicle:
        """Affecte un conducteur a un vehicule."""
        vehicle = self.get_vehicle(vehicle_id)
        driver = self.driver_repo.get_by_id(driver_id)

        if not driver:
            raise DriverNotFoundError(driver_id=str(driver_id))

        # Verifier permis valide
        if driver.license_expiry_date and driver.license_expiry_date < date.today():
            raise DriverLicenseExpiredError(
                str(driver_id),
                driver.license_expiry_date.isoformat()
            )

        # Desaffecter ancien vehicule du conducteur
        old_vehicle = self.vehicle_repo.get_by_driver(driver_id)
        if old_vehicle and old_vehicle.id != vehicle_id:
            self.vehicle_repo.update(old_vehicle, {
                'assigned_driver_id': None,
                'status': VehicleStatus.AVAILABLE
            }, self.user_id)

        # Affecter
        return self.vehicle_repo.update(vehicle, {
            'assigned_driver_id': driver_id,
            'status': VehicleStatus.ASSIGNED
        }, self.user_id)

    def unassign_driver(self, vehicle_id: UUID) -> FleetVehicle:
        """Retire l'affectation du conducteur."""
        vehicle = self.get_vehicle(vehicle_id)

        return self.vehicle_repo.update(vehicle, {
            'assigned_driver_id': None,
            'status': VehicleStatus.AVAILABLE
        }, self.user_id)

    def update_vehicle_location(
        self,
        vehicle_id: UUID,
        lat: Decimal,
        lng: Decimal
    ) -> FleetVehicle:
        """Met a jour la position GPS du vehicule."""
        vehicle = self.get_vehicle(vehicle_id)
        return self.vehicle_repo.update_location(vehicle, lat, lng)

    def update_vehicle_mileage(
        self,
        vehicle_id: UUID,
        mileage: int,
        log_date: date = None,
        source: str = "manual",
        notes: str = None
    ) -> FleetVehicle:
        """Met a jour le kilometrage et cree un log."""
        vehicle = self.get_vehicle(vehicle_id)

        if mileage < vehicle.current_mileage:
            raise MileageDecrementError(vehicle.current_mileage, mileage)

        # Creer log
        previous = vehicle.current_mileage
        self.mileage_repo.create({
            'vehicle_id': vehicle_id,
            'log_date': log_date or date.today(),
            'mileage': mileage,
            'previous_mileage': previous,
            'distance_since_last': mileage - previous,
            'source': source,
            'notes': notes
        }, self.user_id)

        # Mettre a jour vehicule
        vehicle = self.vehicle_repo.update_mileage(vehicle, mileage, self.user_id)

        # Verifier alertes maintenance basees sur kilometrage
        self._check_mileage_alerts(vehicle)

        return vehicle

    # =========================================================================
    # DRIVERS
    # =========================================================================

    def create_driver(self, data: Dict[str, Any]) -> FleetDriver:
        """Cree un nouveau conducteur."""
        if not data.get('code'):
            data['code'] = self._generate_code('DRV')

        if self.driver_repo.code_exists(data['code']):
            raise DriverDuplicateError(data['code'])

        driver = self.driver_repo.create(data, self.user_id)

        # Verifier echeance permis
        if driver.license_expiry_date:
            self._check_license_expiry(driver)

        logger.info(f"Driver created: {driver.code}")
        return driver

    def update_driver(self, driver_id: UUID, data: Dict[str, Any]) -> FleetDriver:
        """Met a jour un conducteur."""
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError(driver_id=str(driver_id))

        if data.get('code') and data['code'] != driver.code:
            if self.driver_repo.code_exists(data['code'], exclude_id=driver_id):
                raise DriverDuplicateError(data['code'])

        driver = self.driver_repo.update(driver, data, self.user_id)

        # Reverifier permis si date changee
        if 'license_expiry_date' in data and driver.license_expiry_date:
            self._check_license_expiry(driver)

        return driver

    def get_driver(self, driver_id: UUID) -> FleetDriver:
        """Recupere un conducteur."""
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundError(driver_id=str(driver_id))
        return driver

    def list_drivers(
        self,
        filters: DriverFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "last_name",
        sort_dir: str = "asc"
    ) -> Tuple[List[FleetDriver], int]:
        """Liste les conducteurs."""
        return self.driver_repo.list(filters, page, page_size, sort_by, sort_dir)

    def delete_driver(self, driver_id: UUID) -> bool:
        """Supprime un conducteur."""
        driver = self.get_driver(driver_id)

        can_delete, reason = driver.can_delete()
        if not can_delete:
            raise DriverNotFoundError(driver_id=str(driver_id))

        return self.driver_repo.soft_delete(driver, self.user_id)

    # =========================================================================
    # CONTRACTS
    # =========================================================================

    def create_contract(self, data: Dict[str, Any]) -> FleetContract:
        """Cree un nouveau contrat."""
        # Verifier vehicule existe
        vehicle = self.get_vehicle(data['vehicle_id'])

        if not data.get('code'):
            data['code'] = self._generate_code('CTR')

        if self.contract_repo.code_exists(data['code']):
            raise ContractDuplicateError(data['code'])

        contract = self.contract_repo.create(data, self.user_id)

        # Creer alerte echeance
        if contract.end_date:
            self._create_contract_expiry_alert(contract)

        logger.info(f"Contract created: {contract.code} for vehicle {vehicle.code}")
        return contract

    def update_contract(self, contract_id: UUID, data: Dict[str, Any]) -> FleetContract:
        """Met a jour un contrat."""
        contract = self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise ContractNotFoundError(contract_id=str(contract_id))

        if data.get('code') and data['code'] != contract.code:
            if self.contract_repo.code_exists(data['code'], exclude_id=contract_id):
                raise ContractDuplicateError(data['code'])

        return self.contract_repo.update(contract, data, self.user_id)

    def get_contract(self, contract_id: UUID) -> FleetContract:
        """Recupere un contrat."""
        contract = self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise ContractNotFoundError(contract_id=str(contract_id))
        return contract

    def list_contracts(
        self,
        filters: ContractFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "end_date",
        sort_dir: str = "asc"
    ) -> Tuple[List[FleetContract], int]:
        """Liste les contrats."""
        return self.contract_repo.list(filters, page, page_size, sort_by, sort_dir)

    def get_vehicle_contracts(self, vehicle_id: UUID) -> List[FleetContract]:
        """Liste les contrats d'un vehicule."""
        return self.contract_repo.get_by_vehicle(vehicle_id)

    def get_expiring_contracts(self, days: int = 30) -> List[FleetContract]:
        """Liste les contrats expirant dans N jours."""
        return self.contract_repo.get_expiring(days)

    # =========================================================================
    # FUEL ENTRIES
    # =========================================================================

    def add_fuel_entry(self, data: Dict[str, Any]) -> FleetFuelEntry:
        """Ajoute une entree de carburant."""
        vehicle = self.get_vehicle(data['vehicle_id'])

        # Calculer total si non fourni
        if not data.get('total_cost'):
            data['total_cost'] = data['quantity_liters'] * data['price_per_liter']

        # Recuperer derniere entree pour calculs
        last_entry = self.fuel_repo.get_last_entry(data['vehicle_id'])

        if last_entry:
            data['previous_mileage'] = last_entry.mileage_at_fill
            data['distance_since_last'] = data['mileage_at_fill'] - last_entry.mileage_at_fill

            # Calculer consommation si plein
            if last_entry.full_tank and data.get('full_tank', True):
                if data['distance_since_last'] > 0:
                    consumption = (data['quantity_liters'] / Decimal(data['distance_since_last'])) * 100
                    data['consumption_per_100km'] = consumption.quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

                    # Detecter anomalie
                    if vehicle.average_consumption:
                        if consumption > vehicle.average_consumption * Decimal("1.5"):
                            data['anomaly_detected'] = True
                            data['anomaly_reason'] = "Consumption 50% above average"

        entry = self.fuel_repo.create(data, self.user_id)

        # Mettre a jour kilometrage vehicule
        if data['mileage_at_fill'] > vehicle.current_mileage:
            self.update_vehicle_mileage(
                vehicle.id,
                data['mileage_at_fill'],
                data['fill_date'],
                "fuel"
            )

        # Mettre a jour consommation moyenne vehicule
        self._update_average_consumption(vehicle)

        # Enregistrer cout
        self.cost_repo.create({
            'vehicle_id': vehicle.id,
            'category': 'fuel',
            'description': f"Fuel {data['quantity_liters']}L",
            'cost_date': data['fill_date'],
            'amount': data['total_cost'],
            'mileage_at_cost': data['mileage_at_fill'],
            'reference_type': 'fuel_entry',
            'reference_id': entry.id
        }, self.user_id)

        # Mettre a jour stats conducteur
        if data.get('driver_id'):
            driver = self.driver_repo.get_by_id(data['driver_id'])
            if driver:
                driver.total_fuel_cost += data['total_cost']
                self.db.commit()

        return entry

    def get_fuel_entries(
        self,
        vehicle_id: UUID = None,
        driver_id: UUID = None,
        date_from: date = None,
        date_to: date = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[FleetFuelEntry], int]:
        """Liste les entrees carburant."""
        return self.fuel_repo.list(vehicle_id, driver_id, date_from, date_to, page, page_size)

    def get_consumption_stats(
        self,
        vehicle_id: UUID,
        date_from: date = None,
        date_to: date = None
    ) -> ConsumptionStats:
        """Calcule les statistiques de consommation."""
        if not date_from:
            date_from = date.today() - timedelta(days=365)
        if not date_to:
            date_to = date.today()

        entries, _ = self.fuel_repo.list(vehicle_id, date_from=date_from, date_to=date_to, page_size=1000)

        stats = ConsumptionStats(
            vehicle_id=vehicle_id,
            period_start=date_from,
            period_end=date_to
        )

        if not entries:
            return stats

        stats.fill_count = len(entries)
        stats.total_liters = sum(e.quantity_liters for e in entries)
        stats.total_cost = sum(e.total_cost for e in entries)

        if stats.total_liters > 0:
            stats.avg_price_per_liter = stats.total_cost / stats.total_liters

        # Calculer distance et consommation
        entries_sorted = sorted(entries, key=lambda x: x.mileage_at_fill)
        if len(entries_sorted) >= 2:
            stats.total_distance_km = entries_sorted[-1].mileage_at_fill - entries_sorted[0].mileage_at_fill
            if stats.total_distance_km > 0:
                # Exclure le premier plein du calcul
                liters_after_first = sum(e.quantity_liters for e in entries_sorted[1:])
                stats.avg_consumption_per_100km = (liters_after_first / Decimal(stats.total_distance_km)) * 100

        return stats

    # =========================================================================
    # MAINTENANCE
    # =========================================================================

    def create_maintenance(self, data: Dict[str, Any]) -> FleetMaintenance:
        """Cree une maintenance."""
        vehicle = self.get_vehicle(data['vehicle_id'])

        if not data.get('code'):
            data['code'] = self._generate_code('MNT')

        if self.maintenance_repo.code_exists(data['code']):
            raise MaintenanceDuplicateError(data['code'])

        maintenance = self.maintenance_repo.create(data, self.user_id)

        # Si planifiee, mettre vehicule en maintenance si date aujourd'hui
        if maintenance.scheduled_date == date.today():
            self.vehicle_repo.update(vehicle, {'status': VehicleStatus.MAINTENANCE}, self.user_id)

        logger.info(f"Maintenance created: {maintenance.code}")
        return maintenance

    def complete_maintenance(
        self,
        maintenance_id: UUID,
        data: Dict[str, Any]
    ) -> FleetMaintenance:
        """Complete une maintenance."""
        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance:
            raise MaintenanceNotFoundError(maintenance_id=str(maintenance_id))

        if maintenance.status == MaintenanceStatus.COMPLETED:
            raise MaintenanceStateError(maintenance.status.value, "completed")

        # Calculer total
        cost_parts = data.get('cost_parts', maintenance.cost_parts)
        cost_labor = data.get('cost_labor', maintenance.cost_labor)
        cost_other = data.get('cost_other', maintenance.cost_other or Decimal("0"))
        cost_total = cost_parts + cost_labor + cost_other

        # Calculer TVA
        vat_rate = data.get('vat_rate', maintenance.vat_rate or Decimal("20"))
        vat_amount = (cost_total * vat_rate / 100).quantize(Decimal("0.01"))

        update_data = {
            **data,
            'status': MaintenanceStatus.COMPLETED,
            'completed_date': data.get('completed_date', date.today()),
            'cost_parts': cost_parts,
            'cost_labor': cost_labor,
            'cost_other': cost_other,
            'cost_total': cost_total,
            'vat_amount': vat_amount
        }

        maintenance = self.maintenance_repo.update(maintenance, update_data, self.user_id)

        # Enregistrer cout
        self.cost_repo.create({
            'vehicle_id': maintenance.vehicle_id,
            'category': 'maintenance',
            'subcategory': maintenance.maintenance_type.value,
            'description': maintenance.title,
            'cost_date': maintenance.completed_date,
            'amount': cost_total,
            'vat_amount': vat_amount,
            'mileage_at_cost': maintenance.mileage_at_maintenance,
            'reference_type': 'maintenance',
            'reference_id': maintenance.id
        }, self.user_id)

        # Remettre vehicule disponible
        vehicle = self.get_vehicle(maintenance.vehicle_id)
        if vehicle.status == VehicleStatus.MAINTENANCE:
            new_status = VehicleStatus.ASSIGNED if vehicle.assigned_driver_id else VehicleStatus.AVAILABLE
            self.vehicle_repo.update(vehicle, {'status': new_status}, self.user_id)

        # Mettre a jour prochaine maintenance vehicule
        if maintenance.next_maintenance_date:
            self.vehicle_repo.update(vehicle, {
                'next_service_date': maintenance.next_maintenance_date,
                'next_service_mileage': maintenance.next_maintenance_mileage,
                'last_service_date': maintenance.completed_date
            }, self.user_id)

        return maintenance

    def get_maintenance(self, maintenance_id: UUID) -> FleetMaintenance:
        """Recupere une maintenance."""
        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance:
            raise MaintenanceNotFoundError(maintenance_id=str(maintenance_id))
        return maintenance

    def list_maintenances(
        self,
        filters: MaintenanceFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "scheduled_date",
        sort_dir: str = "desc"
    ) -> Tuple[List[FleetMaintenance], int]:
        """Liste les maintenances."""
        return self.maintenance_repo.list(filters, page, page_size, sort_by, sort_dir)

    def get_vehicle_maintenances(self, vehicle_id: UUID) -> List[FleetMaintenance]:
        """Liste les maintenances d'un vehicule."""
        return self.maintenance_repo.get_by_vehicle(vehicle_id)

    def get_scheduled_maintenances(self, days: int = 30) -> List[FleetMaintenance]:
        """Liste les maintenances planifiees."""
        return self.maintenance_repo.get_scheduled(days)

    def get_overdue_maintenances(self) -> List[FleetMaintenance]:
        """Liste les maintenances en retard."""
        return self.maintenance_repo.get_overdue()

    # =========================================================================
    # DOCUMENTS
    # =========================================================================

    def add_document(self, data: Dict[str, Any]) -> FleetDocument:
        """Ajoute un document."""
        # Verifier entite existe
        if data.get('vehicle_id'):
            self.get_vehicle(data['vehicle_id'])
        if data.get('driver_id'):
            self.get_driver(data['driver_id'])

        document = self.document_repo.create(data, self.user_id)

        # Creer alerte si expiration
        if document.expiry_date:
            self._create_document_expiry_alert(document)

        return document

    def get_document(self, document_id: UUID) -> FleetDocument:
        """Recupere un document."""
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))
        return document

    def update_document(self, document_id: UUID, data: Dict[str, Any]) -> FleetDocument:
        """Met a jour un document."""
        document = self.get_document(document_id)
        return self.document_repo.update(document, data, self.user_id)

    def get_vehicle_documents(self, vehicle_id: UUID) -> List[FleetDocument]:
        """Liste les documents d'un vehicule."""
        return self.document_repo.get_by_vehicle(vehicle_id)

    def get_driver_documents(self, driver_id: UUID) -> List[FleetDocument]:
        """Liste les documents d'un conducteur."""
        return self.document_repo.get_by_driver(driver_id)

    def get_expiring_documents(self, days: int = 30) -> List[FleetDocument]:
        """Liste les documents expirant."""
        return self.document_repo.get_expiring(days)

    # =========================================================================
    # INCIDENTS
    # =========================================================================

    def create_incident(self, data: Dict[str, Any]) -> FleetIncident:
        """Cree un incident/sinistre/amende."""
        vehicle = self.get_vehicle(data['vehicle_id'])

        if not data.get('code'):
            prefix = 'FIN' if 'fine' in data.get('incident_type', '').lower() else 'INC'
            data['code'] = self._generate_code(prefix)

        if self.incident_repo.code_exists(data['code']):
            raise IncidentDuplicateError(data['code'])

        # Calculer total
        repair_cost = data.get('repair_cost') or Decimal("0")
        other_costs = data.get('other_costs') or Decimal("0")
        fine_amount = data.get('fine_amount') or Decimal("0")
        data['total_cost'] = repair_cost + other_costs + fine_amount

        incident = self.incident_repo.create(data, self.user_id)

        # Enregistrer cout si montant
        if incident.total_cost > 0:
            category = 'fine' if incident.incident_type.value.endswith('fine') else 'incident'
            self.cost_repo.create({
                'vehicle_id': vehicle.id,
                'category': category,
                'subcategory': incident.incident_type.value,
                'description': incident.description[:200],
                'cost_date': incident.incident_date.date(),
                'amount': incident.total_cost,
                'reference_type': 'incident',
                'reference_id': incident.id
            }, self.user_id)

        logger.info(f"Incident created: {incident.code}")
        return incident

    def update_incident(self, incident_id: UUID, data: Dict[str, Any]) -> FleetIncident:
        """Met a jour un incident."""
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise IncidentNotFoundError(incident_id=str(incident_id))

        if data.get('code') and data['code'] != incident.code:
            if self.incident_repo.code_exists(data['code'], exclude_id=incident_id):
                raise IncidentDuplicateError(data['code'])

        return self.incident_repo.update(incident, data, self.user_id)

    def get_incident(self, incident_id: UUID) -> FleetIncident:
        """Recupere un incident."""
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise IncidentNotFoundError(incident_id=str(incident_id))
        return incident

    def list_incidents(
        self,
        filters: IncidentFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "incident_date",
        sort_dir: str = "desc"
    ) -> Tuple[List[FleetIncident], int]:
        """Liste les incidents."""
        return self.incident_repo.list(filters, page, page_size, sort_by, sort_dir)

    def get_vehicle_incidents(self, vehicle_id: UUID) -> List[FleetIncident]:
        """Liste les incidents d'un vehicule."""
        return self.incident_repo.get_by_vehicle(vehicle_id)

    def get_unpaid_fines(self) -> List[FleetIncident]:
        """Liste les amendes non payees."""
        return self.incident_repo.get_unpaid_fines()

    def pay_fine(self, incident_id: UUID, paid_date: date = None) -> FleetIncident:
        """Marque une amende comme payee."""
        incident = self.get_incident(incident_id)

        if not incident.incident_type.value.endswith('fine'):
            raise IncidentNotFoundError(incident_id=str(incident_id))

        return self.incident_repo.update(incident, {
            'fine_paid': True,
            'fine_paid_date': paid_date or date.today()
        }, self.user_id)

    # =========================================================================
    # ALERTS
    # =========================================================================

    def get_alerts(
        self,
        filters: AlertFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[FleetAlert], int]:
        """Liste les alertes."""
        return self.alert_repo.list(filters, page, page_size)

    def get_unresolved_alerts(self, vehicle_id: UUID = None) -> List[FleetAlert]:
        """Liste les alertes non resolues."""
        return self.alert_repo.get_unresolved(vehicle_id)

    def mark_alert_read(self, alert_id: UUID) -> FleetAlert:
        """Marque une alerte comme lue."""
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise AlertNotFoundError(str(alert_id))
        return self.alert_repo.mark_read(alert, self.user_id)

    def resolve_alert(self, alert_id: UUID, notes: str = None) -> FleetAlert:
        """Resout une alerte."""
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise AlertNotFoundError(str(alert_id))
        return self.alert_repo.resolve(alert, self.user_id, notes)

    def _create_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
        vehicle_id: UUID = None,
        driver_id: UUID = None,
        due_date: date = None,
        **kwargs
    ) -> FleetAlert:
        """Cree une alerte interne."""
        return self.alert_repo.create({
            'alert_type': alert_type,
            'title': title,
            'message': message,
            'severity': severity,
            'vehicle_id': vehicle_id,
            'driver_id': driver_id,
            'due_date': due_date,
            **kwargs
        })

    def _check_mileage_alerts(self, vehicle: FleetVehicle):
        """Verifie les alertes liees au kilometrage."""
        # Verifier prochain entretien
        if vehicle.next_service_mileage:
            diff = vehicle.next_service_mileage - vehicle.current_mileage
            if diff <= 0:
                self._create_alert(
                    AlertType.MAINTENANCE_DUE,
                    f"Service overdue for {vehicle.registration_number}",
                    f"Service was due at {vehicle.next_service_mileage}km, current: {vehicle.current_mileage}km",
                    AlertSeverity.CRITICAL,
                    vehicle_id=vehicle.id
                )
            elif diff <= 500:
                self._create_alert(
                    AlertType.MAINTENANCE_DUE,
                    f"Service due soon for {vehicle.registration_number}",
                    f"Service due in {diff}km",
                    AlertSeverity.WARNING,
                    vehicle_id=vehicle.id
                )

        # Verifier limite kilometrage contrat
        if vehicle.annual_mileage_limit:
            # Calculer kilometrage annuel
            year_start = date.today().replace(month=1, day=1)
            mileage_logs = self.mileage_repo.get_by_vehicle(
                vehicle.id,
                date_from=year_start
            )
            if mileage_logs:
                first = min(mileage_logs, key=lambda x: x.log_date)
                annual_km = vehicle.current_mileage - first.previous_mileage
                if annual_km > vehicle.annual_mileage_limit:
                    self._create_alert(
                        AlertType.MILEAGE_EXCEEDED,
                        f"Annual mileage limit exceeded for {vehicle.registration_number}",
                        f"Limit: {vehicle.annual_mileage_limit}km, Current: {annual_km}km",
                        AlertSeverity.WARNING,
                        vehicle_id=vehicle.id
                    )

    def _check_license_expiry(self, driver: FleetDriver):
        """Cree alerte si permis expire bientot."""
        if not driver.license_expiry_date:
            return

        days_until = (driver.license_expiry_date - date.today()).days

        if days_until <= 0:
            self._create_alert(
                AlertType.LICENSE_EXPIRY,
                f"Driver license expired: {driver.first_name} {driver.last_name}",
                f"License expired on {driver.license_expiry_date}",
                AlertSeverity.CRITICAL,
                driver_id=driver.id,
                due_date=driver.license_expiry_date
            )
        elif days_until <= 30:
            self._create_alert(
                AlertType.LICENSE_EXPIRY,
                f"Driver license expiring: {driver.first_name} {driver.last_name}",
                f"License expires on {driver.license_expiry_date} ({days_until} days)",
                AlertSeverity.WARNING,
                driver_id=driver.id,
                due_date=driver.license_expiry_date
            )

    def _create_contract_expiry_alert(self, contract: FleetContract):
        """Cree alerte expiration contrat."""
        if not contract.end_date:
            return

        days = contract.reminder_days or 60
        self._create_alert(
            AlertType.CONTRACT_EXPIRY,
            f"Contract expiring: {contract.code}",
            f"{contract.contract_type.value} contract expires on {contract.end_date}",
            AlertSeverity.WARNING if days > 30 else AlertSeverity.INFO,
            vehicle_id=contract.vehicle_id,
            due_date=contract.end_date,
            contract_id=contract.id,
            days_before_due=days
        )

    def _create_document_expiry_alert(self, document: FleetDocument):
        """Cree alerte expiration document."""
        if not document.expiry_date:
            return

        alert_type = AlertType.INSURANCE_EXPIRY if document.document_type == DocumentType.INSURANCE \
            else AlertType.INSPECTION_DUE if document.document_type == DocumentType.TECHNICAL_INSPECTION \
            else AlertType.DOCUMENT_EXPIRY

        self._create_alert(
            alert_type,
            f"Document expiring: {document.name}",
            f"Expires on {document.expiry_date}",
            AlertSeverity.WARNING,
            vehicle_id=document.vehicle_id,
            driver_id=document.driver_id,
            due_date=document.expiry_date,
            document_id=document.id,
            days_before_due=document.reminder_days
        )

    def _update_average_consumption(self, vehicle: FleetVehicle):
        """Met a jour la consommation moyenne du vehicule."""
        entries = self.fuel_repo.get_by_vehicle(vehicle.id, limit=20)

        consumptions = [e.consumption_per_100km for e in entries if e.consumption_per_100km]
        if consumptions:
            avg = sum(consumptions) / len(consumptions)
            self.vehicle_repo.update(vehicle, {
                'average_consumption': avg.quantize(Decimal("0.01"))
            }, self.user_id)

    # =========================================================================
    # TCO & REPORTS
    # =========================================================================

    def get_tco_report(
        self,
        vehicle_id: UUID,
        date_from: date,
        date_to: date
    ) -> TCOReport:
        """Genere un rapport TCO (Total Cost of Ownership)."""
        vehicle = self.get_vehicle(vehicle_id)

        report = TCOReport(
            vehicle_id=vehicle_id,
            vehicle_info=f"{vehicle.make} {vehicle.model} ({vehicle.registration_number})",
            period_start=date_from,
            period_end=date_to
        )

        # Recuperer tous les couts
        costs = self.cost_repo.get_by_vehicle(vehicle_id, date_from, date_to)

        for cost in costs:
            amount = cost.amount
            if cost.category == 'fuel':
                report.fuel_cost += amount
            elif cost.category == 'maintenance':
                report.maintenance_cost += amount
            elif cost.category == 'insurance':
                report.insurance_cost += amount
            elif cost.category == 'tax':
                report.tax_cost += amount
            elif cost.category == 'fine':
                report.fines_cost += amount
            else:
                report.other_costs += amount

        # Couts contrats (leasing)
        contracts = self.contract_repo.get_by_vehicle(vehicle_id)
        for contract in contracts:
            if contract.contract_type in [ContractType.LEASING, ContractType.LLD, ContractType.LOA]:
                if contract.monthly_payment:
                    # Calculer nombre de mois dans la periode
                    months = (date_to.year - date_from.year) * 12 + date_to.month - date_from.month
                    report.leasing_cost = contract.monthly_payment * months

        # Depreciation
        if vehicle.purchase_price and vehicle.current_value:
            days_in_period = (date_to - date_from).days
            if vehicle.purchase_date:
                total_days = (date_to - vehicle.purchase_date).days
                if total_days > 0:
                    total_depreciation = vehicle.purchase_price - vehicle.current_value
                    report.depreciation = (total_depreciation * days_in_period / total_days).quantize(
                        Decimal("0.01")
                    )

        # Total
        report.total_cost = (
            report.fuel_cost + report.maintenance_cost + report.insurance_cost +
            report.tax_cost + report.leasing_cost + report.depreciation +
            report.fines_cost + report.other_costs
        )

        # Distance
        mileage_logs = self.mileage_repo.get_by_vehicle(vehicle_id, date_from, date_to)
        if len(mileage_logs) >= 2:
            sorted_logs = sorted(mileage_logs, key=lambda x: x.log_date)
            report.total_distance_km = sorted_logs[-1].mileage - sorted_logs[0].previous_mileage

        # Cout par km
        if report.total_distance_km > 0:
            report.cost_per_km = (report.total_cost / Decimal(report.total_distance_km)).quantize(
                Decimal("0.01")
            )

        # Carburant
        fuel_stats = self.get_consumption_stats(vehicle_id, date_from, date_to)
        report.total_fuel_liters = fuel_stats.total_liters
        report.avg_consumption_per_100km = fuel_stats.avg_consumption_per_100km

        # Breakdown
        report.cost_breakdown = {
            'fuel': report.fuel_cost,
            'maintenance': report.maintenance_cost,
            'insurance': report.insurance_cost,
            'tax': report.tax_cost,
            'leasing': report.leasing_cost,
            'depreciation': report.depreciation,
            'fines': report.fines_cost,
            'other': report.other_costs
        }

        return report

    def get_dashboard(self) -> FleetDashboard:
        """Genere le dashboard de la flotte."""
        dashboard = FleetDashboard()

        # Vehicules
        vehicles, dashboard.total_vehicles = self.vehicle_repo.list(page_size=1000)
        dashboard.vehicles_by_status = self.vehicle_repo.count_by_status()
        dashboard.vehicles_by_type = self.vehicle_repo.count_by_type()

        # Conducteurs
        drivers, dashboard.total_drivers = self.driver_repo.list(page_size=1000)
        dashboard.active_drivers = len([d for d in drivers if d.is_active])

        # Stats mensuelles
        month_start = date.today().replace(day=1)
        month_end = date.today()

        # Kilometrage
        for vehicle in vehicles:
            logs = self.mileage_repo.get_by_vehicle(vehicle.id, month_start, month_end)
            if logs:
                sorted_logs = sorted(logs, key=lambda x: x.log_date)
                if len(sorted_logs) >= 2:
                    dashboard.total_mileage_month += sorted_logs[-1].mileage - sorted_logs[0].previous_mileage

        # Couts carburant et maintenance
        fuel_entries, _ = self.fuel_repo.list(date_from=month_start, date_to=month_end, page_size=1000)
        dashboard.total_fuel_cost_month = sum(e.total_cost for e in fuel_entries)

        maintenances = self.maintenance_repo.get_by_vehicle(None)
        dashboard.total_maintenance_cost_month = sum(
            m.cost_total for m in maintenances
            if m.status == MaintenanceStatus.COMPLETED
            and m.completed_date and m.completed_date >= month_start
        )

        # Incidents et amendes
        incidents, _ = self.incident_repo.list(
            IncidentFilters(date_from=datetime.combine(month_start, datetime.min.time())),
            page_size=1000
        )
        dashboard.total_incidents_month = len(incidents)
        fines = [i for i in incidents if i.incident_type.value.endswith('fine')]
        dashboard.total_fines_month = len(fines)
        dashboard.total_fines_amount_month = sum(f.fine_amount or Decimal("0") for f in fines)

        # Consommation moyenne
        if dashboard.total_mileage_month > 0:
            total_liters = sum(e.quantity_liters for e in fuel_entries)
            dashboard.avg_consumption = (total_liters / Decimal(dashboard.total_mileage_month)) * 100

            total_cost = dashboard.total_fuel_cost_month + dashboard.total_maintenance_cost_month
            dashboard.avg_cost_per_km = total_cost / Decimal(dashboard.total_mileage_month)

        # Alertes
        alert_counts = self.alert_repo.count_by_severity()
        dashboard.alerts_critical = alert_counts.get('critical', 0)
        dashboard.alerts_warning = alert_counts.get('warning', 0)
        dashboard.alerts_total = sum(alert_counts.values())

        # Echeances
        dashboard.contracts_expiring_30d = len(self.contract_repo.get_expiring(30))
        dashboard.documents_expiring_30d = len(self.document_repo.get_expiring(30))
        dashboard.inspections_due_30d = len([
            d for d in self.document_repo.get_expiring(30)
            if d.document_type == DocumentType.TECHNICAL_INSPECTION
        ])
        dashboard.maintenances_due_30d = len(self.maintenance_repo.get_scheduled(30))

        # Alertes recentes
        recent_alerts, _ = self.alert_repo.list(
            AlertFilters(is_resolved=False),
            page_size=10
        )
        dashboard.recent_alerts = [
            {
                'id': str(a.id),
                'vehicle_id': str(a.vehicle_id) if a.vehicle_id else None,
                'alert_type': a.alert_type.value,
                'severity': a.severity.value,
                'title': a.title,
                'due_date': a.due_date,
                'is_read': a.is_read,
                'is_resolved': a.is_resolved,
                'created_at': a.created_at
            }
            for a in recent_alerts
        ]

        return dashboard

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _generate_code(self, prefix: str) -> str:
        """Genere un code unique."""
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        return f"{prefix}-{timestamp}"

    def run_scheduled_checks(self):
        """Execute les verifications planifiees (cron job)."""
        logger.info("Running scheduled fleet checks...")

        # Verifier contrats expirant
        expiring_contracts = self.contract_repo.get_expiring(60)
        for contract in expiring_contracts:
            if not contract.reminder_sent:
                self._create_contract_expiry_alert(contract)
                self.contract_repo.update(contract, {'reminder_sent': True}, None)

        # Verifier documents expirant
        expiring_docs = self.document_repo.get_expiring(30)
        for doc in expiring_docs:
            if not doc.reminder_sent:
                self._create_document_expiry_alert(doc)
                self.document_repo.update(doc, {'reminder_sent': True}, None)

        # Verifier permis expirant
        expiring_licenses = self.driver_repo.get_with_expiring_licenses(30)
        for driver in expiring_licenses:
            self._check_license_expiry(driver)

        # Verifier maintenances en retard
        overdue = self.maintenance_repo.get_overdue()
        for m in overdue:
            self.maintenance_repo.update(m, {'status': MaintenanceStatus.OVERDUE}, None)
            self._create_alert(
                AlertType.MAINTENANCE_DUE,
                f"Maintenance overdue: {m.code}",
                f"{m.title} was scheduled for {m.scheduled_date}",
                AlertSeverity.CRITICAL,
                vehicle_id=m.vehicle_id,
                maintenance_id=m.id
            )

        logger.info("Scheduled fleet checks completed")


# ============================================================================
# FACTORY
# ============================================================================

def create_fleet_service(db: Session, tenant_id: UUID, user_id: UUID = None) -> FleetService:
    """Factory pour creer le service Fleet."""
    return FleetService(db, tenant_id, user_id)
