"""
Repository - Module Fleet Management (GAP-062)

CRITIQUE: Toutes les requetes filtrees par tenant_id via _base_query().
Soft delete, pagination, filtres avances.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, extract
from sqlalchemy.orm import Session

from .models import (
    FleetVehicle, FleetDriver, FleetContract, FleetMileageLog,
    FleetFuelEntry, FleetMaintenance, FleetDocument, FleetIncident,
    FleetCost, FleetAlert,
    VehicleStatus, VehicleType, FuelType, ContractType, ContractStatus,
    MaintenanceType, MaintenanceStatus, DocumentType, IncidentType, IncidentStatus,
    AlertType, AlertSeverity
)
from .schemas import (
    VehicleFilters, DriverFilters, ContractFilters,
    MaintenanceFilters, IncidentFilters, AlertFilters
)


class VehicleRepository:
    """Repository FleetVehicle avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtre tenant et soft delete."""
        query = self.db.query(FleetVehicle).filter(FleetVehicle.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FleetVehicle.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FleetVehicle]:
        return self._base_query().filter(FleetVehicle.id == id).first()

    def get_by_code(self, code: str) -> Optional[FleetVehicle]:
        return self._base_query().filter(FleetVehicle.code == code.upper()).first()

    def get_by_registration(self, registration: str) -> Optional[FleetVehicle]:
        reg = registration.upper().strip().replace(" ", "-")
        return self._base_query().filter(FleetVehicle.registration_number == reg).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(FleetVehicle.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FleetVehicle.code == code.upper())
        if exclude_id:
            query = query.filter(FleetVehicle.id != exclude_id)
        return query.count() > 0

    def registration_exists(self, registration: str, exclude_id: UUID = None) -> bool:
        reg = registration.upper().strip().replace(" ", "-")
        query = self._base_query().filter(FleetVehicle.registration_number == reg)
        if exclude_id:
            query = query.filter(FleetVehicle.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: VehicleFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[FleetVehicle], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FleetVehicle.registration_number.ilike(term),
                    FleetVehicle.code.ilike(term),
                    FleetVehicle.make.ilike(term),
                    FleetVehicle.model.ilike(term)
                ))
            if filters.status:
                query = query.filter(FleetVehicle.status.in_(filters.status))
            if filters.vehicle_type:
                query = query.filter(FleetVehicle.vehicle_type.in_(filters.vehicle_type))
            if filters.fuel_type:
                query = query.filter(FleetVehicle.fuel_type.in_(filters.fuel_type))
            if filters.department:
                query = query.filter(FleetVehicle.department == filters.department)
            if filters.assigned_driver_id:
                query = query.filter(FleetVehicle.assigned_driver_id == filters.assigned_driver_id)
            if filters.is_active is not None:
                query = query.filter(FleetVehicle.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(FleetVehicle, sort_by, FleetVehicle.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            FleetVehicle.is_active == True
        ).filter(or_(
            FleetVehicle.registration_number.ilike(f"{prefix}%"),
            FleetVehicle.code.ilike(f"{prefix}%"),
            FleetVehicle.make.ilike(f"{prefix}%"),
            FleetVehicle.model.ilike(f"{prefix}%")
        ))
        results = query.order_by(FleetVehicle.registration_number).limit(limit).all()
        return [
            {
                "id": str(v.id),
                "code": v.code,
                "name": f"{v.make} {v.model}",
                "label": f"[{v.registration_number}] {v.make} {v.model}"
            }
            for v in results
        ]

    def get_by_driver(self, driver_id: UUID) -> Optional[FleetVehicle]:
        return self._base_query().filter(
            FleetVehicle.assigned_driver_id == driver_id,
            FleetVehicle.is_active == True
        ).first()

    def get_available(self) -> List[FleetVehicle]:
        return self._base_query().filter(
            FleetVehicle.status == VehicleStatus.AVAILABLE,
            FleetVehicle.is_active == True
        ).all()

    def count_by_status(self) -> Dict[str, int]:
        results = self._base_query().with_entities(
            FleetVehicle.status,
            func.count(FleetVehicle.id)
        ).group_by(FleetVehicle.status).all()
        return {status.value: count for status, count in results}

    def count_by_type(self) -> Dict[str, int]:
        results = self._base_query().with_entities(
            FleetVehicle.vehicle_type,
            func.count(FleetVehicle.id)
        ).group_by(FleetVehicle.vehicle_type).all()
        return {vtype.value: count for vtype, count in results}

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetVehicle:
        entity = FleetVehicle(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FleetVehicle, data: Dict[str, Any], updated_by: UUID = None) -> FleetVehicle:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_location(self, entity: FleetVehicle, lat: Decimal, lng: Decimal) -> FleetVehicle:
        entity.location_lat = lat
        entity.location_lng = lng
        entity.last_location_update = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_mileage(self, entity: FleetVehicle, mileage: int, updated_by: UUID = None) -> FleetVehicle:
        if mileage < entity.current_mileage:
            raise ValueError("Mileage cannot decrease")
        entity.current_mileage = mileage
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FleetVehicle, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        entity.is_active = False
        self.db.commit()
        return True

    def restore(self, entity: FleetVehicle) -> FleetVehicle:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        entity.is_active = True
        self.db.commit()
        self.db.refresh(entity)
        return entity


class DriverRepository:
    """Repository FleetDriver avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FleetDriver).filter(FleetDriver.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FleetDriver.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FleetDriver]:
        return self._base_query().filter(FleetDriver.id == id).first()

    def get_by_code(self, code: str) -> Optional[FleetDriver]:
        return self._base_query().filter(FleetDriver.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FleetDriver.code == code.upper())
        if exclude_id:
            query = query.filter(FleetDriver.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: DriverFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "last_name",
        sort_dir: str = "asc"
    ) -> Tuple[List[FleetDriver], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FleetDriver.first_name.ilike(term),
                    FleetDriver.last_name.ilike(term),
                    FleetDriver.code.ilike(term),
                    FleetDriver.email.ilike(term)
                ))
            if filters.department:
                query = query.filter(FleetDriver.department == filters.department)
            if filters.is_active is not None:
                query = query.filter(FleetDriver.is_active == filters.is_active)
            if filters.license_expiring_days:
                cutoff = date.today() + timedelta(days=filters.license_expiring_days)
                query = query.filter(FleetDriver.license_expiry_date <= cutoff)

        total = query.count()
        sort_col = getattr(FleetDriver, sort_by, FleetDriver.last_name)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            FleetDriver.is_active == True
        ).filter(or_(
            FleetDriver.first_name.ilike(f"{prefix}%"),
            FleetDriver.last_name.ilike(f"{prefix}%"),
            FleetDriver.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(FleetDriver.last_name).limit(limit).all()
        return [
            {
                "id": str(d.id),
                "code": d.code,
                "name": f"{d.first_name} {d.last_name}",
                "label": f"[{d.code}] {d.first_name} {d.last_name}"
            }
            for d in results
        ]

    def get_with_expiring_licenses(self, days: int = 30) -> List[FleetDriver]:
        cutoff = date.today() + timedelta(days=days)
        return self._base_query().filter(
            FleetDriver.is_active == True,
            FleetDriver.license_expiry_date <= cutoff,
            FleetDriver.license_expiry_date >= date.today()
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetDriver:
        entity = FleetDriver(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FleetDriver, data: Dict[str, Any], updated_by: UUID = None) -> FleetDriver:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FleetDriver, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        entity.is_active = False
        self.db.commit()
        return True


class ContractRepository:
    """Repository FleetContract avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FleetContract).filter(FleetContract.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FleetContract.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FleetContract]:
        return self._base_query().filter(FleetContract.id == id).first()

    def get_by_code(self, code: str) -> Optional[FleetContract]:
        return self._base_query().filter(FleetContract.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FleetContract.code == code.upper())
        if exclude_id:
            query = query.filter(FleetContract.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: ContractFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "end_date",
        sort_dir: str = "asc"
    ) -> Tuple[List[FleetContract], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FleetContract.code.ilike(term),
                    FleetContract.provider_name.ilike(term),
                    FleetContract.contract_number.ilike(term)
                ))
            if filters.vehicle_id:
                query = query.filter(FleetContract.vehicle_id == filters.vehicle_id)
            if filters.contract_type:
                query = query.filter(FleetContract.contract_type.in_(filters.contract_type))
            if filters.status:
                query = query.filter(FleetContract.status.in_(filters.status))
            if filters.expiring_days:
                cutoff = date.today() + timedelta(days=filters.expiring_days)
                query = query.filter(
                    FleetContract.end_date <= cutoff,
                    FleetContract.end_date >= date.today()
                )

        total = query.count()
        sort_col = getattr(FleetContract, sort_by, FleetContract.end_date)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_vehicle(self, vehicle_id: UUID, active_only: bool = True) -> List[FleetContract]:
        query = self._base_query().filter(FleetContract.vehicle_id == vehicle_id)
        if active_only:
            query = query.filter(FleetContract.status == ContractStatus.ACTIVE)
        return query.all()

    def get_expiring(self, days: int = 30) -> List[FleetContract]:
        cutoff = date.today() + timedelta(days=days)
        return self._base_query().filter(
            FleetContract.status == ContractStatus.ACTIVE,
            FleetContract.end_date <= cutoff,
            FleetContract.end_date >= date.today()
        ).order_by(FleetContract.end_date).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetContract:
        entity = FleetContract(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FleetContract, data: Dict[str, Any], updated_by: UUID = None) -> FleetContract:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FleetContract, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        entity.is_active = False
        self.db.commit()
        return True


class FuelEntryRepository:
    """Repository FleetFuelEntry avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(FleetFuelEntry).filter(FleetFuelEntry.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[FleetFuelEntry]:
        return self._base_query().filter(FleetFuelEntry.id == id).first()

    def list(
        self,
        vehicle_id: UUID = None,
        driver_id: UUID = None,
        date_from: date = None,
        date_to: date = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[FleetFuelEntry], int]:
        query = self._base_query()

        if vehicle_id:
            query = query.filter(FleetFuelEntry.vehicle_id == vehicle_id)
        if driver_id:
            query = query.filter(FleetFuelEntry.driver_id == driver_id)
        if date_from:
            query = query.filter(FleetFuelEntry.fill_date >= date_from)
        if date_to:
            query = query.filter(FleetFuelEntry.fill_date <= date_to)

        total = query.count()
        query = query.order_by(desc(FleetFuelEntry.fill_date))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_vehicle(self, vehicle_id: UUID, limit: int = None) -> List[FleetFuelEntry]:
        query = self._base_query().filter(
            FleetFuelEntry.vehicle_id == vehicle_id
        ).order_by(desc(FleetFuelEntry.fill_date))
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_last_entry(self, vehicle_id: UUID) -> Optional[FleetFuelEntry]:
        return self._base_query().filter(
            FleetFuelEntry.vehicle_id == vehicle_id
        ).order_by(desc(FleetFuelEntry.mileage_at_fill)).first()

    def get_monthly_totals(self, vehicle_id: UUID, year: int) -> List[Dict[str, Any]]:
        results = self._base_query().filter(
            FleetFuelEntry.vehicle_id == vehicle_id,
            extract('year', FleetFuelEntry.fill_date) == year
        ).with_entities(
            extract('month', FleetFuelEntry.fill_date).label('month'),
            func.sum(FleetFuelEntry.quantity_liters).label('liters'),
            func.sum(FleetFuelEntry.total_cost).label('cost'),
            func.count(FleetFuelEntry.id).label('count')
        ).group_by(
            extract('month', FleetFuelEntry.fill_date)
        ).order_by('month').all()

        return [
            {"month": int(r.month), "liters": r.liters, "cost": r.cost, "count": r.count}
            for r in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetFuelEntry:
        entity = FleetFuelEntry(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FleetFuelEntry, data: Dict[str, Any]) -> FleetFuelEntry:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: FleetFuelEntry) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True


class MaintenanceRepository:
    """Repository FleetMaintenance avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FleetMaintenance).filter(FleetMaintenance.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FleetMaintenance.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FleetMaintenance]:
        return self._base_query().filter(FleetMaintenance.id == id).first()

    def get_by_code(self, code: str) -> Optional[FleetMaintenance]:
        return self._base_query().filter(FleetMaintenance.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FleetMaintenance.code == code.upper())
        if exclude_id:
            query = query.filter(FleetMaintenance.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: MaintenanceFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "scheduled_date",
        sort_dir: str = "desc"
    ) -> Tuple[List[FleetMaintenance], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FleetMaintenance.code.ilike(term),
                    FleetMaintenance.title.ilike(term),
                    FleetMaintenance.provider_name.ilike(term)
                ))
            if filters.vehicle_id:
                query = query.filter(FleetMaintenance.vehicle_id == filters.vehicle_id)
            if filters.maintenance_type:
                query = query.filter(FleetMaintenance.maintenance_type.in_(filters.maintenance_type))
            if filters.status:
                query = query.filter(FleetMaintenance.status.in_(filters.status))
            if filters.date_from:
                query = query.filter(FleetMaintenance.scheduled_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(FleetMaintenance.scheduled_date <= filters.date_to)

        total = query.count()
        sort_col = getattr(FleetMaintenance, sort_by, FleetMaintenance.scheduled_date)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_vehicle(self, vehicle_id: UUID) -> List[FleetMaintenance]:
        return self._base_query().filter(
            FleetMaintenance.vehicle_id == vehicle_id
        ).order_by(desc(FleetMaintenance.scheduled_date)).all()

    def get_scheduled(self, days: int = 30) -> List[FleetMaintenance]:
        cutoff = date.today() + timedelta(days=days)
        return self._base_query().filter(
            FleetMaintenance.status == MaintenanceStatus.SCHEDULED,
            FleetMaintenance.scheduled_date <= cutoff
        ).order_by(FleetMaintenance.scheduled_date).all()

    def get_overdue(self) -> List[FleetMaintenance]:
        return self._base_query().filter(
            FleetMaintenance.status == MaintenanceStatus.SCHEDULED,
            FleetMaintenance.scheduled_date < date.today()
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetMaintenance:
        entity = FleetMaintenance(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FleetMaintenance, data: Dict[str, Any], updated_by: UUID = None) -> FleetMaintenance:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FleetMaintenance, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class DocumentRepository:
    """Repository FleetDocument avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FleetDocument).filter(FleetDocument.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FleetDocument.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FleetDocument]:
        return self._base_query().filter(FleetDocument.id == id).first()

    def get_by_vehicle(self, vehicle_id: UUID) -> List[FleetDocument]:
        return self._base_query().filter(
            FleetDocument.vehicle_id == vehicle_id
        ).order_by(FleetDocument.expiry_date).all()

    def get_by_driver(self, driver_id: UUID) -> List[FleetDocument]:
        return self._base_query().filter(
            FleetDocument.driver_id == driver_id
        ).order_by(FleetDocument.expiry_date).all()

    def get_expiring(self, days: int = 30) -> List[FleetDocument]:
        cutoff = date.today() + timedelta(days=days)
        return self._base_query().filter(
            FleetDocument.expiry_date <= cutoff,
            FleetDocument.expiry_date >= date.today()
        ).order_by(FleetDocument.expiry_date).all()

    def get_expired(self) -> List[FleetDocument]:
        return self._base_query().filter(
            FleetDocument.expiry_date < date.today()
        ).order_by(FleetDocument.expiry_date).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetDocument:
        entity = FleetDocument(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FleetDocument, data: Dict[str, Any], updated_by: UUID = None) -> FleetDocument:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FleetDocument, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class IncidentRepository:
    """Repository FleetIncident avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FleetIncident).filter(FleetIncident.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FleetIncident.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FleetIncident]:
        return self._base_query().filter(FleetIncident.id == id).first()

    def get_by_code(self, code: str) -> Optional[FleetIncident]:
        return self._base_query().filter(FleetIncident.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FleetIncident.code == code.upper())
        if exclude_id:
            query = query.filter(FleetIncident.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: IncidentFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "incident_date",
        sort_dir: str = "desc"
    ) -> Tuple[List[FleetIncident], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FleetIncident.code.ilike(term),
                    FleetIncident.description.ilike(term),
                    FleetIncident.incident_location.ilike(term)
                ))
            if filters.vehicle_id:
                query = query.filter(FleetIncident.vehicle_id == filters.vehicle_id)
            if filters.driver_id:
                query = query.filter(FleetIncident.driver_id == filters.driver_id)
            if filters.incident_type:
                query = query.filter(FleetIncident.incident_type.in_(filters.incident_type))
            if filters.status:
                query = query.filter(FleetIncident.status.in_(filters.status))
            if filters.date_from:
                query = query.filter(FleetIncident.incident_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(FleetIncident.incident_date <= filters.date_to)

        total = query.count()
        sort_col = getattr(FleetIncident, sort_by, FleetIncident.incident_date)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_vehicle(self, vehicle_id: UUID) -> List[FleetIncident]:
        return self._base_query().filter(
            FleetIncident.vehicle_id == vehicle_id
        ).order_by(desc(FleetIncident.incident_date)).all()

    def get_unpaid_fines(self) -> List[FleetIncident]:
        return self._base_query().filter(
            FleetIncident.incident_type.in_([
                IncidentType.FINE, IncidentType.PARKING_FINE,
                IncidentType.SPEED_FINE, IncidentType.OTHER_FINE
            ]),
            FleetIncident.fine_paid == False
        ).order_by(FleetIncident.fine_due_date).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetIncident:
        entity = FleetIncident(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FleetIncident, data: Dict[str, Any], updated_by: UUID = None) -> FleetIncident:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FleetIncident, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class CostRepository:
    """Repository FleetCost avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(FleetCost).filter(FleetCost.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[FleetCost]:
        return self._base_query().filter(FleetCost.id == id).first()

    def get_by_vehicle(
        self,
        vehicle_id: UUID,
        date_from: date = None,
        date_to: date = None,
        category: str = None
    ) -> List[FleetCost]:
        query = self._base_query().filter(FleetCost.vehicle_id == vehicle_id)
        if date_from:
            query = query.filter(FleetCost.cost_date >= date_from)
        if date_to:
            query = query.filter(FleetCost.cost_date <= date_to)
        if category:
            query = query.filter(FleetCost.category == category)
        return query.order_by(desc(FleetCost.cost_date)).all()

    def get_totals_by_category(
        self,
        vehicle_id: UUID,
        date_from: date,
        date_to: date
    ) -> Dict[str, Decimal]:
        results = self._base_query().filter(
            FleetCost.vehicle_id == vehicle_id,
            FleetCost.cost_date >= date_from,
            FleetCost.cost_date <= date_to
        ).with_entities(
            FleetCost.category,
            func.sum(FleetCost.amount).label('total')
        ).group_by(FleetCost.category).all()

        return {cat: total or Decimal("0") for cat, total in results}

    def get_monthly_totals(
        self,
        vehicle_id: UUID = None,
        year: int = None
    ) -> List[Dict[str, Any]]:
        query = self._base_query()
        if vehicle_id:
            query = query.filter(FleetCost.vehicle_id == vehicle_id)
        if year:
            query = query.filter(extract('year', FleetCost.cost_date) == year)

        results = query.with_entities(
            extract('month', FleetCost.cost_date).label('month'),
            FleetCost.category,
            func.sum(FleetCost.amount).label('total')
        ).group_by(
            extract('month', FleetCost.cost_date),
            FleetCost.category
        ).order_by('month').all()

        return [
            {"month": int(r.month), "category": r.category, "total": r.total}
            for r in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetCost:
        entity = FleetCost(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity


class AlertRepository:
    """Repository FleetAlert avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(FleetAlert).filter(FleetAlert.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[FleetAlert]:
        return self._base_query().filter(FleetAlert.id == id).first()

    def list(
        self,
        filters: AlertFilters = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[FleetAlert], int]:
        query = self._base_query()

        if filters:
            if filters.vehicle_id:
                query = query.filter(FleetAlert.vehicle_id == filters.vehicle_id)
            if filters.alert_type:
                query = query.filter(FleetAlert.alert_type.in_(filters.alert_type))
            if filters.severity:
                query = query.filter(FleetAlert.severity.in_(filters.severity))
            if filters.is_resolved is not None:
                query = query.filter(FleetAlert.is_resolved == filters.is_resolved)

        total = query.count()
        query = query.order_by(
            desc(FleetAlert.severity == AlertSeverity.CRITICAL),
            desc(FleetAlert.severity == AlertSeverity.WARNING),
            desc(FleetAlert.created_at)
        )
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_unresolved(self, vehicle_id: UUID = None) -> List[FleetAlert]:
        query = self._base_query().filter(FleetAlert.is_resolved == False)
        if vehicle_id:
            query = query.filter(FleetAlert.vehicle_id == vehicle_id)
        return query.order_by(desc(FleetAlert.created_at)).all()

    def count_by_severity(self) -> Dict[str, int]:
        results = self._base_query().filter(
            FleetAlert.is_resolved == False
        ).with_entities(
            FleetAlert.severity,
            func.count(FleetAlert.id)
        ).group_by(FleetAlert.severity).all()

        return {sev.value: count for sev, count in results}

    def create(self, data: Dict[str, Any]) -> FleetAlert:
        entity = FleetAlert(tenant_id=self.tenant_id, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def mark_read(self, entity: FleetAlert, user_id: UUID) -> FleetAlert:
        entity.is_read = True
        entity.read_at = datetime.utcnow()
        entity.read_by = user_id
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def resolve(self, entity: FleetAlert, user_id: UUID, notes: str = None) -> FleetAlert:
        entity.is_resolved = True
        entity.resolved_at = datetime.utcnow()
        entity.resolved_by = user_id
        entity.resolution_notes = notes
        self.db.commit()
        self.db.refresh(entity)
        return entity


class MileageLogRepository:
    """Repository FleetMileageLog avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(FleetMileageLog).filter(FleetMileageLog.tenant_id == self.tenant_id)

    def get_by_vehicle(
        self,
        vehicle_id: UUID,
        date_from: date = None,
        date_to: date = None
    ) -> List[FleetMileageLog]:
        query = self._base_query().filter(FleetMileageLog.vehicle_id == vehicle_id)
        if date_from:
            query = query.filter(FleetMileageLog.log_date >= date_from)
        if date_to:
            query = query.filter(FleetMileageLog.log_date <= date_to)
        return query.order_by(desc(FleetMileageLog.log_date)).all()

    def get_last_entry(self, vehicle_id: UUID) -> Optional[FleetMileageLog]:
        return self._base_query().filter(
            FleetMileageLog.vehicle_id == vehicle_id
        ).order_by(desc(FleetMileageLog.mileage)).first()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FleetMileageLog:
        entity = FleetMileageLog(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
