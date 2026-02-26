"""
Repository - Module Field Service (GAP-081)

CRITIQUE: Toutes les requêtes filtrées par tenant_id.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from .models import (
    FSWorkOrder, FSTechnician, FSCustomerSite, FSServiceZone, FSSkill,
    WorkOrderStatus, TechnicianStatus, Priority
)
from .schemas import WorkOrderFilters, TechnicianFilters


class WorkOrderRepository:
    """Repository FSWorkOrder avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FSWorkOrder).filter(FSWorkOrder.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FSWorkOrder.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FSWorkOrder]:
        return self._base_query().filter(FSWorkOrder.id == id).first()

    def get_by_code(self, code: str) -> Optional[FSWorkOrder]:
        return self._base_query().filter(FSWorkOrder.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(FSWorkOrder.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FSWorkOrder.code == code.upper())
        if exclude_id:
            query = query.filter(FSWorkOrder.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: WorkOrderFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[FSWorkOrder], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FSWorkOrder.title.ilike(term),
                    FSWorkOrder.code.ilike(term),
                    FSWorkOrder.description.ilike(term)
                ))
            if filters.work_order_type:
                query = query.filter(FSWorkOrder.work_order_type.in_(filters.work_order_type))
            if filters.status:
                query = query.filter(FSWorkOrder.status.in_(filters.status))
            if filters.priority:
                query = query.filter(FSWorkOrder.priority.in_(filters.priority))
            if filters.customer_id:
                query = query.filter(FSWorkOrder.customer_id == filters.customer_id)
            if filters.technician_id:
                query = query.filter(FSWorkOrder.technician_id == filters.technician_id)
            if filters.date_from:
                query = query.filter(FSWorkOrder.scheduled_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(FSWorkOrder.scheduled_date <= filters.date_to)

        total = query.count()
        sort_col = getattr(FSWorkOrder, sort_by, FSWorkOrder.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(or_(
            FSWorkOrder.title.ilike(f"{prefix}%"),
            FSWorkOrder.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(FSWorkOrder.title).limit(limit).all()
        return [
            {"id": str(w.id), "code": w.code, "name": w.title, "label": f"[{w.code}] {w.title}"}
            for w in results
        ]

    def get_by_technician(self, technician_id: UUID, date_filter: date = None) -> List[FSWorkOrder]:
        query = self._base_query().filter(FSWorkOrder.technician_id == technician_id)
        if date_filter:
            query = query.filter(FSWorkOrder.scheduled_date == date_filter)
        return query.order_by(FSWorkOrder.scheduled_start_time).all()

    def get_overdue(self) -> List[FSWorkOrder]:
        return self._base_query().filter(
            FSWorkOrder.sla_due_date < datetime.utcnow(),
            FSWorkOrder.status.notin_([WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED])
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FSWorkOrder:
        entity = FSWorkOrder(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FSWorkOrder, data: Dict[str, Any], updated_by: UUID = None) -> FSWorkOrder:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FSWorkOrder, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: FSWorkOrder) -> FSWorkOrder:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity


class TechnicianRepository:
    """Repository FSTechnician avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FSTechnician).filter(FSTechnician.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FSTechnician.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FSTechnician]:
        return self._base_query().filter(FSTechnician.id == id).first()

    def get_by_code(self, code: str) -> Optional[FSTechnician]:
        return self._base_query().filter(FSTechnician.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FSTechnician.code == code.upper())
        if exclude_id:
            query = query.filter(FSTechnician.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: TechnicianFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[FSTechnician], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FSTechnician.first_name.ilike(term),
                    FSTechnician.last_name.ilike(term),
                    FSTechnician.code.ilike(term),
                    FSTechnician.email.ilike(term)
                ))
            if filters.status:
                query = query.filter(FSTechnician.status.in_(filters.status))
            if filters.zone_id:
                query = query.filter(FSTechnician.home_zone_id == filters.zone_id)
            if filters.is_active is not None:
                query = query.filter(FSTechnician.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(FSTechnician, sort_by, FSTechnician.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            FSTechnician.is_active == True
        ).filter(or_(
            FSTechnician.first_name.ilike(f"{prefix}%"),
            FSTechnician.last_name.ilike(f"{prefix}%"),
            FSTechnician.code.ilike(f"{prefix}%")
        ))
        results = query.limit(limit).all()
        return [
            {"id": str(t.id), "code": t.code, "name": f"{t.first_name} {t.last_name}",
             "label": f"[{t.code}] {t.first_name} {t.last_name}"}
            for t in results
        ]

    def get_available(self, date_filter: date = None) -> List[FSTechnician]:
        query = self._base_query().filter(
            FSTechnician.is_active == True,
            FSTechnician.status == TechnicianStatus.AVAILABLE
        )
        return query.all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FSTechnician:
        entity = FSTechnician(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FSTechnician, data: Dict[str, Any], updated_by: UUID = None) -> FSTechnician:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_location(self, entity: FSTechnician, lat: Decimal, lng: Decimal) -> FSTechnician:
        entity.current_location_lat = lat
        entity.current_location_lng = lng
        entity.last_location_update = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FSTechnician, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class CustomerSiteRepository:
    """Repository FSCustomerSite avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FSCustomerSite).filter(FSCustomerSite.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FSCustomerSite.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FSCustomerSite]:
        return self._base_query().filter(FSCustomerSite.id == id).first()

    def get_by_code(self, code: str) -> Optional[FSCustomerSite]:
        return self._base_query().filter(FSCustomerSite.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FSCustomerSite.code == code.upper())
        if exclude_id:
            query = query.filter(FSCustomerSite.id != exclude_id)
        return query.count() > 0

    def get_by_customer(self, customer_id: UUID) -> List[FSCustomerSite]:
        return self._base_query().filter(
            FSCustomerSite.customer_id == customer_id,
            FSCustomerSite.is_active == True
        ).all()

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            FSCustomerSite.is_active == True
        ).filter(or_(
            FSCustomerSite.name.ilike(f"{prefix}%"),
            FSCustomerSite.code.ilike(f"{prefix}%")
        ))
        results = query.limit(limit).all()
        return [
            {"id": str(s.id), "code": s.code, "name": s.name, "label": f"[{s.code}] {s.name}"}
            for s in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FSCustomerSite:
        entity = FSCustomerSite(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FSCustomerSite, data: Dict[str, Any], updated_by: UUID = None) -> FSCustomerSite:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FSCustomerSite, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class ServiceZoneRepository:
    """Repository FSServiceZone avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FSServiceZone).filter(FSServiceZone.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FSServiceZone.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[FSServiceZone]:
        return self._base_query().filter(FSServiceZone.id == id).first()

    def get_by_code(self, code: str) -> Optional[FSServiceZone]:
        return self._base_query().filter(FSServiceZone.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FSServiceZone.code == code.upper())
        if exclude_id:
            query = query.filter(FSServiceZone.id != exclude_id)
        return query.count() > 0

    def list_active(self) -> List[FSServiceZone]:
        return self._base_query().filter(FSServiceZone.is_active == True).all()

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            FSServiceZone.is_active == True
        ).filter(or_(
            FSServiceZone.name.ilike(f"{prefix}%"),
            FSServiceZone.code.ilike(f"{prefix}%")
        ))
        results = query.limit(limit).all()
        return [
            {"id": str(z.id), "code": z.code, "name": z.name, "label": f"[{z.code}] {z.name}"}
            for z in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> FSServiceZone:
        entity = FSServiceZone(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FSServiceZone, data: Dict[str, Any], updated_by: UUID = None) -> FSServiceZone:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FSServiceZone, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True
