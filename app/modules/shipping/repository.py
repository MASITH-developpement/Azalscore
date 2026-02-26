"""
Repositories Shipping / Expédition - GAP-078
=============================================
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from .models import (
    Zone, Carrier, ShippingRate, Shipment, Package,
    PickupPoint, Return,
    ShipmentStatus, ReturnStatus
)


class ZoneRepository:
    """Repository pour les zones."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Zone).filter(
            Zone.tenant_id == self.tenant_id,
            Zone.is_deleted == False
        )

    def get_by_id(self, zone_id: UUID) -> Optional[Zone]:
        return self._base_query().filter(Zone.id == zone_id).first()

    def get_by_code(self, code: str) -> Optional[Zone]:
        return self._base_query().filter(Zone.code == code).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Zone], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(Zone.name.ilike(pattern), Zone.code.ilike(pattern))
            )

        if is_active is not None:
            query = query.filter(Zone.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Zone.sort_order, Zone.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, zone: Zone) -> Zone:
        zone.tenant_id = self.tenant_id
        self.db.add(zone)
        self.db.flush()
        return zone

    def update(self, zone: Zone) -> Zone:
        zone.version += 1
        zone.updated_at = datetime.utcnow()
        self.db.flush()
        return zone

    def delete(self, zone: Zone) -> None:
        zone.is_deleted = True
        zone.deleted_at = datetime.utcnow()
        self.db.flush()

    def count_rates_using_zone(self, zone_id: UUID) -> int:
        return self.db.query(ShippingRate).filter(
            ShippingRate.tenant_id == self.tenant_id,
            ShippingRate.zone_id == zone_id,
            ShippingRate.is_deleted == False
        ).count()

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(Zone.code)).filter(
            Zone.tenant_id == self.tenant_id,
            Zone.code.like("ZN-%")
        ).scalar()
        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1
        return f"ZN-{num:04d}"

    def list_zones(
        self,
        *,
        is_active: Optional[bool] = None,
        country_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Zone], int]:
        query = self._base_query()
        if is_active is not None:
            query = query.filter(Zone.is_active == is_active)
        if country_code:
            query = query.filter(Zone.countries.contains([country_code]))
        total = query.count()
        items = query.order_by(Zone.sort_order, Zone.name).offset(skip).limit(limit).all()
        return items, total

    def soft_delete(self, zone_id: str, deleted_by: str) -> Zone:
        zone = self.get_by_id(zone_id)
        if zone:
            zone.is_deleted = True
            zone.deleted_at = datetime.utcnow()
            zone.deleted_by = deleted_by
            self.db.flush()
        return zone

    def restore(self, zone_id: str, restored_by: str) -> Zone:
        zone = self.db.query(Zone).filter(
            Zone.tenant_id == self.tenant_id,
            Zone.id == zone_id,
            Zone.is_deleted == True
        ).first()
        if zone:
            zone.is_deleted = False
            zone.deleted_at = None
            zone.deleted_by = None
            zone.updated_by = restored_by
            zone.updated_at = datetime.utcnow()
            self.db.flush()
        return zone

    def find_zone_for_address(
        self,
        country_code: str,
        postal_code: str
    ) -> Optional[Zone]:
        zones = self._base_query().filter(
            Zone.is_active == True,
            Zone.countries.contains([country_code])
        ).order_by(Zone.sort_order).all()
        for zone in zones:
            if not zone.postal_codes:
                excluded = False
                for pattern in (zone.excluded_postal_codes or []):
                    if self._match_postal_code(postal_code, pattern):
                        excluded = True
                        break
                if not excluded:
                    return zone
            else:
                matched = False
                for pattern in zone.postal_codes:
                    if self._match_postal_code(postal_code, pattern):
                        matched = True
                        break
                if matched:
                    excluded = False
                    for pattern in (zone.excluded_postal_codes or []):
                        if self._match_postal_code(postal_code, pattern):
                            excluded = True
                            break
                    if not excluded:
                        return zone
        return None

    def _match_postal_code(self, postal_code: str, pattern: str) -> bool:
        if "*" in pattern:
            prefix = pattern.replace("*", "")
            return postal_code.startswith(prefix)
        elif "-" in pattern:
            parts = pattern.split("-")
            if len(parts) == 2:
                return parts[0] <= postal_code <= parts[1]
            return False
        else:
            return postal_code == pattern

    def list_by_zone(self, zone_id: str) -> List[ShippingRate]:
        return self.db.query(ShippingRate).filter(
            ShippingRate.tenant_id == self.tenant_id,
            ShippingRate.zone_id == zone_id,
            ShippingRate.is_deleted == False
        ).all()


class CarrierRepository:
    """Repository pour les transporteurs."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Carrier).filter(
            Carrier.tenant_id == self.tenant_id,
            Carrier.is_deleted == False
        )

    def get_by_id(self, carrier_id: UUID) -> Optional[Carrier]:
        return self._base_query().filter(Carrier.id == carrier_id).first()

    def get_by_code(self, code: str) -> Optional[Carrier]:
        return self._base_query().filter(Carrier.code == code).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        carrier_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Carrier], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(Carrier.name.ilike(pattern), Carrier.code.ilike(pattern))
            )

        if carrier_type:
            query = query.filter(Carrier.carrier_type == carrier_type)

        if is_active is not None:
            query = query.filter(Carrier.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Carrier.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, carrier: Carrier) -> Carrier:
        carrier.tenant_id = self.tenant_id
        self.db.add(carrier)
        self.db.flush()
        return carrier

    def update(self, carrier: Carrier) -> Carrier:
        carrier.version += 1
        carrier.updated_at = datetime.utcnow()
        self.db.flush()
        return carrier

    def delete(self, carrier: Carrier) -> None:
        carrier.is_deleted = True
        carrier.deleted_at = datetime.utcnow()
        self.db.flush()

    def count_shipments_using_carrier(self, carrier_id: UUID) -> int:
        return self.db.query(Shipment).filter(
            Shipment.tenant_id == self.tenant_id,
            Shipment.carrier_id == carrier_id,
            Shipment.is_deleted == False
        ).count()

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(Carrier.code)).filter(
            Carrier.tenant_id == self.tenant_id,
            Carrier.code.like("CAR-%")
        ).scalar()
        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1
        return f"CAR-{num:04d}"

    def list_carriers(
        self,
        *,
        carrier_type=None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Carrier], int]:
        query = self._base_query()
        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(Carrier.name.ilike(pattern), Carrier.code.ilike(pattern)))
        if carrier_type:
            query = query.filter(Carrier.carrier_type == carrier_type)
        if is_active is not None:
            query = query.filter(Carrier.is_active == is_active)
        total = query.count()
        items = query.order_by(Carrier.name).offset(skip).limit(limit).all()
        return items, total

    def soft_delete(self, carrier_id: str, deleted_by: str) -> Carrier:
        carrier = self.get_by_id(carrier_id)
        if carrier:
            carrier.is_deleted = True
            carrier.deleted_at = datetime.utcnow()
            carrier.deleted_by = deleted_by
            self.db.flush()
        return carrier

    def restore(self, carrier_id: str, restored_by: str) -> Carrier:
        carrier = self.db.query(Carrier).filter(
            Carrier.tenant_id == self.tenant_id,
            Carrier.id == carrier_id,
            Carrier.is_deleted == True
        ).first()
        if carrier:
            carrier.is_deleted = False
            carrier.deleted_at = None
            carrier.deleted_by = None
            carrier.updated_by = restored_by
            carrier.updated_at = datetime.utcnow()
            self.db.flush()
        return carrier


class ShippingRateRepository:
    """Repository pour les tarifs."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(ShippingRate).filter(
            ShippingRate.tenant_id == self.tenant_id,
            ShippingRate.is_deleted == False
        )

    def get_by_id(self, rate_id: UUID) -> Optional[ShippingRate]:
        return self._base_query().filter(ShippingRate.id == rate_id).first()

    def get_by_code(self, code: str) -> Optional[ShippingRate]:
        return self._base_query().filter(ShippingRate.code == code).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        carrier_id: Optional[UUID] = None,
        zone_id: Optional[UUID] = None,
        shipping_method: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[ShippingRate], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(ShippingRate.name.ilike(pattern), ShippingRate.code.ilike(pattern))
            )

        if carrier_id:
            query = query.filter(ShippingRate.carrier_id == carrier_id)

        if zone_id:
            query = query.filter(ShippingRate.zone_id == zone_id)

        if shipping_method:
            query = query.filter(ShippingRate.shipping_method == shipping_method)

        if is_active is not None:
            query = query.filter(ShippingRate.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(ShippingRate.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def list_by_carrier(
        self,
        carrier_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[ShippingRate]:
        query = self._base_query().filter(ShippingRate.carrier_id == carrier_id)

        if is_active is not None:
            query = query.filter(ShippingRate.is_active == is_active)

        return query.order_by(ShippingRate.name).all()

    def get_valid_rates(
        self,
        zone_id: Optional[UUID] = None,
        today: Optional[date] = None
    ) -> List[ShippingRate]:
        today = today or date.today()
        query = self._base_query().filter(
            ShippingRate.is_active == True,
            or_(ShippingRate.valid_from.is_(None), ShippingRate.valid_from <= today),
            or_(ShippingRate.valid_until.is_(None), ShippingRate.valid_until >= today)
        )

        if zone_id:
            query = query.filter(
                or_(ShippingRate.zone_id.is_(None), ShippingRate.zone_id == zone_id)
            )

        return query.all()

    def create(self, rate: ShippingRate) -> ShippingRate:
        rate.tenant_id = self.tenant_id
        self.db.add(rate)
        self.db.flush()
        return rate

    def update(self, rate: ShippingRate) -> ShippingRate:
        rate.version += 1
        rate.updated_at = datetime.utcnow()
        self.db.flush()
        return rate

    def delete(self, rate: ShippingRate) -> None:
        rate.is_deleted = True
        rate.deleted_at = datetime.utcnow()
        self.db.flush()

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(ShippingRate.code)).filter(
            ShippingRate.tenant_id == self.tenant_id,
            ShippingRate.code.like("RAT-%")
        ).scalar()

        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"RAT-{num:04d}"

    def list_rates(
        self,
        *,
        carrier_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        shipping_method=None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ShippingRate], int]:
        query = self._base_query()
        if carrier_id:
            query = query.filter(ShippingRate.carrier_id == carrier_id)
        if zone_id:
            query = query.filter(ShippingRate.zone_id == zone_id)
        if shipping_method:
            query = query.filter(ShippingRate.shipping_method == shipping_method)
        if is_active is not None:
            query = query.filter(ShippingRate.is_active == is_active)
        total = query.count()
        items = query.order_by(ShippingRate.name).offset(skip).limit(limit).all()
        return items, total

    def list_by_zone(self, zone_id: str) -> List[ShippingRate]:
        return self._base_query().filter(ShippingRate.zone_id == zone_id).all()

    def soft_delete(self, rate_id: str, deleted_by: str) -> ShippingRate:
        rate = self.get_by_id(rate_id)
        if rate:
            rate.is_deleted = True
            rate.deleted_at = datetime.utcnow()
            rate.deleted_by = deleted_by
            self.db.flush()
        return rate

    def restore(self, rate_id: str, restored_by: str) -> ShippingRate:
        rate = self.db.query(ShippingRate).filter(
            ShippingRate.tenant_id == self.tenant_id,
            ShippingRate.id == rate_id,
            ShippingRate.is_deleted == True
        ).first()
        if rate:
            rate.is_deleted = False
            rate.deleted_at = None
            rate.deleted_by = None
            rate.updated_by = restored_by
            rate.updated_at = datetime.utcnow()
            self.db.flush()
        return rate


class ShipmentRepository:
    """Repository pour les expéditions."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Shipment).filter(
            Shipment.tenant_id == self.tenant_id,
            Shipment.is_deleted == False
        )

    def get_by_id(self, shipment_id: UUID) -> Optional[Shipment]:
        return self._base_query().filter(Shipment.id == shipment_id).first()

    def get_by_number(self, number: str) -> Optional[Shipment]:
        return self._base_query().filter(Shipment.shipment_number == number).first()

    def get_by_tracking(self, tracking_number: str) -> Optional[Shipment]:
        return self._base_query().filter(
            or_(
                Shipment.master_tracking_number == tracking_number,
                Shipment.packages.any(Package.tracking_number == tracking_number)
            )
        ).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        carrier_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Tuple[List[Shipment], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Shipment.shipment_number.ilike(pattern),
                    Shipment.order_number.ilike(pattern),
                    Shipment.master_tracking_number.ilike(pattern)
                )
            )

        if status:
            query = query.filter(Shipment.status == status)

        if carrier_id:
            query = query.filter(Shipment.carrier_id == carrier_id)

        if order_id:
            query = query.filter(Shipment.order_id == order_id)

        if date_from:
            query = query.filter(Shipment.ship_date >= date_from)

        if date_to:
            query = query.filter(Shipment.ship_date <= date_to)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Shipment.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, shipment: Shipment) -> Shipment:
        shipment.tenant_id = self.tenant_id
        self.db.add(shipment)
        self.db.flush()
        return shipment

    def update(self, shipment: Shipment) -> Shipment:
        shipment.version += 1
        shipment.updated_at = datetime.utcnow()
        self.db.flush()
        return shipment

    def delete(self, shipment: Shipment) -> None:
        shipment.is_deleted = True
        shipment.deleted_at = datetime.utcnow()
        self.db.flush()

    def get_next_number(self) -> str:
        max_num = self.db.query(func.max(Shipment.shipment_number)).filter(
            Shipment.tenant_id == self.tenant_id,
            Shipment.shipment_number.like("SHP-%")
        ).scalar()

        if max_num:
            try:
                num = int(max_num.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"SHP-{num:08d}"

    def count_by_status(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> dict:
        query = self._base_query()

        if date_from:
            query = query.filter(Shipment.ship_date >= date_from)
        if date_to:
            query = query.filter(Shipment.ship_date <= date_to)

        result = query.with_entities(
            Shipment.status,
            func.count(Shipment.id)
        ).group_by(Shipment.status).all()

        return {str(status): count for status, count in result}

    def count_by_carrier(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> dict:
        query = self._base_query()

        if date_from:
            query = query.filter(Shipment.ship_date >= date_from)
        if date_to:
            query = query.filter(Shipment.ship_date <= date_to)

        result = query.with_entities(
            Shipment.carrier_name,
            func.count(Shipment.id)
        ).group_by(Shipment.carrier_name).all()

        return {name: count for name, count in result}

    def get_total_cost(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Decimal:
        query = self._base_query()

        if date_from:
            query = query.filter(Shipment.ship_date >= date_from)
        if date_to:
            query = query.filter(Shipment.ship_date <= date_to)

        result = query.with_entities(func.sum(Shipment.total_cost)).scalar()
        return Decimal(str(result)) if result else Decimal("0")

    def list_shipments(
        self,
        *,
        status=None,
        carrier_id: Optional[str] = None,
        order_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Shipment], int]:
        query = self._base_query()
        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(
                Shipment.shipment_number.ilike(pattern),
                Shipment.order_number.ilike(pattern),
                Shipment.master_tracking_number.ilike(pattern)
            ))
        if status:
            query = query.filter(Shipment.status == status)
        if carrier_id:
            query = query.filter(Shipment.carrier_id == carrier_id)
        if order_id:
            query = query.filter(Shipment.order_id == order_id)
        if start_date:
            query = query.filter(Shipment.ship_date >= start_date)
        if end_date:
            query = query.filter(Shipment.ship_date <= end_date)
        total = query.count()
        items = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_tracking_number(self, tracking_number: str) -> Optional[Shipment]:
        return self.get_by_tracking(tracking_number)


class PackageRepository:
    """Repository pour les colis."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Package).filter(
            Package.tenant_id == self.tenant_id
        )

    def get_by_id(self, package_id: UUID) -> Optional[Package]:
        return self._base_query().filter(Package.id == package_id).first()

    def get_by_tracking(self, tracking_number: str) -> Optional[Package]:
        return self._base_query().filter(
            Package.tracking_number == tracking_number
        ).first()

    def list_by_shipment(self, shipment_id: UUID) -> List[Package]:
        return self._base_query().filter(
            Package.shipment_id == shipment_id
        ).all()

    def create(self, package: Package) -> Package:
        package.tenant_id = self.tenant_id
        self.db.add(package)
        self.db.flush()
        return package

    def update(self, package: Package) -> Package:
        package.updated_at = datetime.utcnow()
        self.db.flush()
        return package


class PickupPointRepository:
    """Repository pour les points relais."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(PickupPoint).filter(
            PickupPoint.tenant_id == self.tenant_id,
            PickupPoint.is_deleted == False
        )

    def get_by_id(self, point_id: UUID) -> Optional[PickupPoint]:
        return self._base_query().filter(PickupPoint.id == point_id).first()

    def get_by_external_id(
        self,
        carrier_id: UUID,
        external_id: str
    ) -> Optional[PickupPoint]:
        return self._base_query().filter(
            PickupPoint.carrier_id == carrier_id,
            PickupPoint.external_id == external_id
        ).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        carrier_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[PickupPoint], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(PickupPoint.name.ilike(pattern))

        if carrier_id:
            query = query.filter(PickupPoint.carrier_id == carrier_id)

        if is_active is not None:
            query = query.filter(PickupPoint.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(PickupPoint.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def search_nearby(
        self,
        carrier_id: UUID,
        country_code: str,
        postal_code: str,
        max_results: int = 10
    ) -> List[PickupPoint]:
        return self._base_query().filter(
            PickupPoint.carrier_id == carrier_id,
            PickupPoint.is_active == True
        ).limit(max_results).all()

    def create(self, point: PickupPoint) -> PickupPoint:
        point.tenant_id = self.tenant_id
        self.db.add(point)
        self.db.flush()
        return point

    def update(self, point: PickupPoint) -> PickupPoint:
        point.version += 1
        point.updated_at = datetime.utcnow()
        self.db.flush()
        return point

    def delete(self, point: PickupPoint) -> None:
        point.is_deleted = True
        point.deleted_at = datetime.utcnow()
        self.db.flush()


class ReturnRepository:
    """Repository pour les retours."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Return).filter(
            Return.tenant_id == self.tenant_id,
            Return.is_deleted == False
        )

    def get_by_id(self, return_id: UUID) -> Optional[Return]:
        return self._base_query().filter(Return.id == return_id).first()

    def get_by_number(self, number: str) -> Optional[Return]:
        return self._base_query().filter(Return.return_number == number).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        order_id: Optional[UUID] = None,
        shipment_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Tuple[List[Return], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Return.return_number.ilike(pattern),
                    Return.reason.ilike(pattern)
                )
            )

        if status:
            query = query.filter(Return.status == status)

        if order_id:
            query = query.filter(Return.order_id == order_id)

        if shipment_id:
            query = query.filter(Return.shipment_id == shipment_id)

        if date_from:
            query = query.filter(func.date(Return.requested_at) >= date_from)

        if date_to:
            query = query.filter(func.date(Return.requested_at) <= date_to)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Return.requested_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, ret: Return) -> Return:
        ret.tenant_id = self.tenant_id
        self.db.add(ret)
        self.db.flush()
        return ret

    def update(self, ret: Return) -> Return:
        ret.version += 1
        ret.updated_at = datetime.utcnow()
        self.db.flush()
        return ret

    def delete(self, ret: Return) -> None:
        ret.is_deleted = True
        ret.deleted_at = datetime.utcnow()
        self.db.flush()

    def get_next_number(self) -> str:
        max_num = self.db.query(func.max(Return.return_number)).filter(
            Return.tenant_id == self.tenant_id,
            Return.return_number.like("RET-%")
        ).scalar()

        if max_num:
            try:
                num = int(max_num.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"RET-{num:08d}"

    def count_by_status(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> dict:
        query = self._base_query()

        if date_from:
            query = query.filter(func.date(Return.requested_at) >= date_from)
        if date_to:
            query = query.filter(func.date(Return.requested_at) <= date_to)

        result = query.with_entities(
            Return.status,
            func.count(Return.id)
        ).group_by(Return.status).all()

        return {str(status): count for status, count in result}
