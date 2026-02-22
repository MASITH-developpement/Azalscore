"""
AZALS MODULE ASSETS - Repository
================================

Acces aux donnees pour le module de gestion des immobilisations.
CRITIQUE: Toutes les requetes sont filtrees par tenant_id.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, List, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, asc, func, or_
from sqlalchemy.orm import Session, joinedload

from .models import (
    AssetCategory,
    AssetDocument,
    AssetInsuranceItem,
    AssetInsurancePolicy,
    AssetInventory,
    AssetInventoryItem,
    AssetMaintenance,
    AssetMovement,
    AssetStatus,
    AssetTransfer,
    AssetValuation,
    DepreciationRun,
    DepreciationSchedule,
    FixedAsset,
    InventoryStatus,
    MaintenanceStatus,
)
from .schemas import AssetFilters


class AssetCategoryRepository:
    """Repository pour les categories d'immobilisations."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(AssetCategory).filter(AssetCategory.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(AssetCategory.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> AssetCategory | None:
        return self._base_query().filter(AssetCategory.id == id).first()

    def get_by_code(self, code: str) -> AssetCategory | None:
        return self._base_query().filter(AssetCategory.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(AssetCategory.code == code.upper())
        if exclude_id:
            query = query.filter(AssetCategory.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        parent_id: UUID | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AssetCategory], int]:
        query = self._base_query()

        if parent_id:
            query = query.filter(AssetCategory.parent_id == parent_id)
        else:
            query = query.filter(AssetCategory.parent_id == None)

        if active_only:
            query = query.filter(AssetCategory.is_active == True)

        total = query.count()
        items = query.order_by(AssetCategory.name).offset(skip).limit(limit).all()
        return items, total

    def list_all(self, active_only: bool = True) -> List[AssetCategory]:
        query = self._base_query()
        if active_only:
            query = query.filter(AssetCategory.is_active == True)
        return query.order_by(AssetCategory.code).all()

    def count_assets(self, category_id: UUID) -> int:
        return self.db.query(FixedAsset).filter(
            FixedAsset.tenant_id == self.tenant_id,
            FixedAsset.category_id == category_id,
            FixedAsset.is_deleted == False
        ).count()

    def count_children(self, category_id: UUID) -> int:
        return self._base_query().filter(AssetCategory.parent_id == category_id).count()

    def create(self, data: dict[str, Any], created_by: UUID = None) -> AssetCategory:
        if "code" in data:
            data["code"] = data["code"].upper()
        entity = AssetCategory(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: AssetCategory, data: dict[str, Any], updated_by: UUID = None) -> AssetCategory:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: AssetCategory, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: AssetCategory) -> AssetCategory:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity


class FixedAssetRepository:
    """Repository pour les immobilisations."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(FixedAsset).filter(FixedAsset.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(FixedAsset.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> FixedAsset | None:
        return self._base_query().options(
            joinedload(FixedAsset.category),
            joinedload(FixedAsset.depreciation_schedule),
        ).filter(FixedAsset.id == id).first()

    def get_by_code(self, code: str) -> FixedAsset | None:
        return self._base_query().filter(FixedAsset.asset_code == code.upper()).first()

    def get_by_barcode(self, barcode: str) -> FixedAsset | None:
        return self._base_query().filter(FixedAsset.barcode == barcode).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FixedAsset.asset_code == code.upper())
        if exclude_id:
            query = query.filter(FixedAsset.id != exclude_id)
        return query.count() > 0

    def barcode_exists(self, barcode: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(FixedAsset.barcode == barcode)
        if exclude_id:
            query = query.filter(FixedAsset.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: AssetFilters | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[FixedAsset], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    FixedAsset.name.ilike(term),
                    FixedAsset.asset_code.ilike(term),
                    FixedAsset.serial_number.ilike(term),
                    FixedAsset.barcode.ilike(term),
                    FixedAsset.description.ilike(term)
                ))
            if filters.status:
                query = query.filter(FixedAsset.status.in_([s.value for s in filters.status]))
            if filters.asset_type:
                query = query.filter(FixedAsset.asset_type.in_([t.value for t in filters.asset_type]))
            if filters.category_id:
                query = query.filter(FixedAsset.category_id == filters.category_id)
            if filters.location_id:
                query = query.filter(FixedAsset.location_id == filters.location_id)
            if filters.responsible_id:
                query = query.filter(FixedAsset.responsible_id == filters.responsible_id)
            if filters.department_id:
                query = query.filter(FixedAsset.department_id == filters.department_id)
            if filters.acquisition_date_from:
                query = query.filter(FixedAsset.acquisition_date >= filters.acquisition_date_from)
            if filters.acquisition_date_to:
                query = query.filter(FixedAsset.acquisition_date <= filters.acquisition_date_to)
            if filters.min_value is not None:
                query = query.filter(FixedAsset.acquisition_cost >= filters.min_value)
            if filters.max_value is not None:
                query = query.filter(FixedAsset.acquisition_cost <= filters.max_value)
            if filters.warranty_expiring_before:
                query = query.filter(FixedAsset.warranty_end_date <= filters.warranty_expiring_before)
            if filters.maintenance_due_before:
                query = query.filter(FixedAsset.next_maintenance_date <= filters.maintenance_due_before)

        total = query.count()
        sort_col = getattr(FixedAsset, sort_by, FixedAsset.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_in_service(self) -> List[FixedAsset]:
        return self._base_query().filter(FixedAsset.status == AssetStatus.IN_SERVICE).all()

    def get_depreciable(self) -> List[FixedAsset]:
        """Retourne les actifs amortissables (en service, non totalement amortis)."""
        from .models import DepreciationMethod
        return self._base_query().filter(
            FixedAsset.status == AssetStatus.IN_SERVICE,
            FixedAsset.depreciation_method != DepreciationMethod.NONE,
            FixedAsset.in_service_date != None
        ).all()

    def get_components(self, parent_id: UUID) -> List[FixedAsset]:
        return self._base_query().filter(FixedAsset.parent_asset_id == parent_id).all()

    def count_components(self, parent_id: UUID) -> int:
        return self._base_query().filter(FixedAsset.parent_asset_id == parent_id).count()

    def get_by_location(self, location_id: UUID) -> List[FixedAsset]:
        return self._base_query().filter(
            FixedAsset.location_id == location_id,
            FixedAsset.status == AssetStatus.IN_SERVICE
        ).all()

    def get_by_responsible(self, responsible_id: UUID) -> List[FixedAsset]:
        return self._base_query().filter(
            FixedAsset.responsible_id == responsible_id,
            FixedAsset.status == AssetStatus.IN_SERVICE
        ).all()

    def get_warranty_expiring(self, before_date: date) -> List[FixedAsset]:
        return self._base_query().filter(
            FixedAsset.status == AssetStatus.IN_SERVICE,
            FixedAsset.warranty_end_date != None,
            FixedAsset.warranty_end_date <= before_date
        ).order_by(FixedAsset.warranty_end_date).all()

    def get_maintenance_due(self, before_date: date) -> List[FixedAsset]:
        return self._base_query().filter(
            FixedAsset.status == AssetStatus.IN_SERVICE,
            FixedAsset.next_maintenance_date != None,
            FixedAsset.next_maintenance_date <= before_date
        ).order_by(FixedAsset.next_maintenance_date).all()

    def get_next_code(self, prefix: str = "IMM") -> str:
        """Generer le prochain code d'immobilisation."""
        year = datetime.utcnow().year
        code_prefix = f"{prefix}-{year}-"

        last = self.db.query(FixedAsset).filter(
            FixedAsset.tenant_id == self.tenant_id,
            FixedAsset.asset_code.like(f"{code_prefix}%")
        ).order_by(desc(FixedAsset.asset_code)).first()

        if last:
            try:
                last_num = int(last.asset_code.split("-")[-1])
                return f"{code_prefix}{last_num + 1:06d}"
            except (ValueError, IndexError):
                pass

        return f"{code_prefix}000001"

    def autocomplete(self, prefix: str, limit: int = 10) -> List[dict[str, Any]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(or_(
            FixedAsset.name.ilike(f"%{prefix}%"),
            FixedAsset.asset_code.ilike(f"%{prefix}%"),
            FixedAsset.barcode.ilike(f"%{prefix}%"),
            FixedAsset.serial_number.ilike(f"%{prefix}%")
        ))
        results = query.order_by(FixedAsset.name).limit(limit).all()
        return [
            {
                "id": str(r.id),
                "asset_code": r.asset_code,
                "name": r.name,
                "asset_type": r.asset_type.value if r.asset_type else None,
                "status": r.status.value if r.status else None,
                "site_name": r.site_name,
                "label": f"[{r.asset_code}] {r.name}" + (f" - {r.site_name}" if r.site_name else "")
            }
            for r in results
        ]

    def create(self, data: dict[str, Any], created_by: UUID = None) -> FixedAsset:
        # Auto-generate code if not provided
        if "asset_code" not in data or not data["asset_code"]:
            data["asset_code"] = self.get_next_code()
        else:
            data["asset_code"] = data["asset_code"].upper()

        # Calculate acquisition cost
        purchase_price = Decimal(str(data.get("purchase_price", 0)))
        vat_amount = Decimal(str(data.get("vat_amount", 0)))
        transport_cost = Decimal(str(data.get("transport_cost", 0)))
        installation_cost = Decimal(str(data.get("installation_cost", 0)))
        customs_cost = Decimal(str(data.get("customs_cost", 0)))
        other_costs = Decimal(str(data.get("other_costs", 0)))

        data["acquisition_cost"] = (
            purchase_price + vat_amount + transport_cost +
            installation_cost + customs_cost + other_costs
        )
        data["net_book_value"] = data["acquisition_cost"]

        entity = FixedAsset(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: FixedAsset, data: dict[str, Any], updated_by: UUID = None) -> FixedAsset:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: FixedAsset, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: FixedAsset) -> FixedAsset:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # Statistics
    def get_statistics(self) -> dict[str, Any]:
        today = date.today()
        month_start = date(today.year, today.month, 1)

        # Counts
        total = self._base_query().count()
        in_service = self._base_query().filter(FixedAsset.status == AssetStatus.IN_SERVICE).count()
        fully_depreciated = self._base_query().filter(FixedAsset.status == AssetStatus.FULLY_DEPRECIATED).count()
        disposed = self._base_query().filter(FixedAsset.status.in_([AssetStatus.DISPOSED, AssetStatus.SCRAPPED])).count()
        under_maintenance = self._base_query().filter(FixedAsset.status == AssetStatus.UNDER_MAINTENANCE).count()

        # Values
        value_result = self.db.query(
            func.sum(FixedAsset.acquisition_cost),
            func.sum(FixedAsset.accumulated_depreciation),
            func.sum(FixedAsset.net_book_value)
        ).filter(
            FixedAsset.tenant_id == self.tenant_id,
            FixedAsset.is_deleted == False,
            FixedAsset.status.in_([AssetStatus.IN_SERVICE, AssetStatus.FULLY_DEPRECIATED])
        ).first()

        # By type
        by_type = {}
        type_result = self.db.query(
            FixedAsset.asset_type,
            func.count(FixedAsset.id)
        ).filter(
            FixedAsset.tenant_id == self.tenant_id,
            FixedAsset.is_deleted == False
        ).group_by(FixedAsset.asset_type).all()
        for t, c in type_result:
            if t:
                by_type[t.value] = c

        # By status
        by_status = {}
        status_result = self.db.query(
            FixedAsset.status,
            func.count(FixedAsset.id)
        ).filter(
            FixedAsset.tenant_id == self.tenant_id,
            FixedAsset.is_deleted == False
        ).group_by(FixedAsset.status).all()
        for s, c in status_result:
            if s:
                by_status[s.value] = c

        # Alerts
        warranty_soon = self._base_query().filter(
            FixedAsset.warranty_end_date != None,
            FixedAsset.warranty_end_date <= today + timedelta(days=30),
            FixedAsset.warranty_end_date >= today,
            FixedAsset.status == AssetStatus.IN_SERVICE
        ).count()

        maintenance_overdue = self._base_query().filter(
            FixedAsset.next_maintenance_date != None,
            FixedAsset.next_maintenance_date < today,
            FixedAsset.status == AssetStatus.IN_SERVICE
        ).count()

        maintenance_soon = self._base_query().filter(
            FixedAsset.next_maintenance_date != None,
            FixedAsset.next_maintenance_date <= today + timedelta(days=30),
            FixedAsset.next_maintenance_date >= today,
            FixedAsset.status == AssetStatus.IN_SERVICE
        ).count()

        # This month
        acq_month = self._base_query().filter(
            FixedAsset.acquisition_date >= month_start
        ).count()
        acq_value = self.db.query(func.sum(FixedAsset.acquisition_cost)).filter(
            FixedAsset.tenant_id == self.tenant_id,
            FixedAsset.is_deleted == False,
            FixedAsset.acquisition_date >= month_start
        ).scalar() or Decimal("0")

        disp_month = self._base_query().filter(
            FixedAsset.disposal_date >= month_start
        ).count()
        disp_value = self.db.query(func.sum(FixedAsset.disposal_proceeds)).filter(
            FixedAsset.tenant_id == self.tenant_id,
            FixedAsset.is_deleted == False,
            FixedAsset.disposal_date >= month_start
        ).scalar() or Decimal("0")

        return {
            "total_assets": total,
            "assets_in_service": in_service,
            "assets_fully_depreciated": fully_depreciated,
            "assets_disposed": disposed,
            "assets_under_maintenance": under_maintenance,
            "total_gross_value": value_result[0] or Decimal("0"),
            "total_accumulated_depreciation": value_result[1] or Decimal("0"),
            "total_net_book_value": value_result[2] or Decimal("0"),
            "by_asset_type": by_type,
            "by_status": by_status,
            "warranty_expiring_soon": warranty_soon,
            "maintenance_overdue": maintenance_overdue,
            "maintenance_due_soon": maintenance_soon,
            "acquisitions_this_month": acq_month,
            "acquisitions_value_this_month": acq_value,
            "disposals_this_month": disp_month,
            "disposals_value_this_month": disp_value,
        }


class DepreciationScheduleRepository:
    """Repository pour les tableaux d'amortissement."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(DepreciationSchedule).filter(DepreciationSchedule.tenant_id == self.tenant_id)

    def get_by_asset(self, asset_id: UUID) -> List[DepreciationSchedule]:
        return self._base_query().filter(
            DepreciationSchedule.asset_id == asset_id
        ).order_by(DepreciationSchedule.period_number).all()

    def get_for_period(self, period_start: date, period_end: date) -> List[DepreciationSchedule]:
        return self._base_query().filter(
            DepreciationSchedule.period_start <= period_end,
            DepreciationSchedule.period_end >= period_start,
            DepreciationSchedule.is_posted == False
        ).all()

    def delete_by_asset(self, asset_id: UUID):
        self._base_query().filter(DepreciationSchedule.asset_id == asset_id).delete()
        self.db.commit()

    def create_bulk(self, entries: List[dict[str, Any]]) -> List[DepreciationSchedule]:
        objects = [
            DepreciationSchedule(tenant_id=self.tenant_id, **entry)
            for entry in entries
        ]
        self.db.add_all(objects)
        self.db.commit()
        return objects

    def mark_as_posted(self, ids: List[UUID], journal_entry_id: UUID = None):
        self.db.query(DepreciationSchedule).filter(
            DepreciationSchedule.id.in_(ids)
        ).update({
            "is_posted": True,
            "posted_date": datetime.utcnow(),
            "journal_entry_id": journal_entry_id
        }, synchronize_session=False)
        self.db.commit()


class AssetMovementRepository:
    """Repository pour les mouvements d'immobilisations."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(AssetMovement).filter(AssetMovement.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(AssetMovement.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> AssetMovement | None:
        return self._base_query().filter(AssetMovement.id == id).first()

    def get_by_asset(self, asset_id: UUID) -> List[AssetMovement]:
        return self._base_query().filter(
            AssetMovement.asset_id == asset_id
        ).order_by(desc(AssetMovement.movement_date)).all()

    def list(
        self,
        asset_id: UUID | None = None,
        movement_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AssetMovement], int]:
        query = self._base_query()

        if asset_id:
            query = query.filter(AssetMovement.asset_id == asset_id)
        if movement_type:
            query = query.filter(AssetMovement.movement_type == movement_type)
        if date_from:
            query = query.filter(AssetMovement.movement_date >= date_from)
        if date_to:
            query = query.filter(AssetMovement.movement_date <= date_to)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(AssetMovement.movement_date)).offset(offset).limit(page_size).all()
        return items, total

    def get_next_number(self) -> str:
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        prefix = f"MVT-{year}{month:02d}-"

        last = self.db.query(AssetMovement).filter(
            AssetMovement.tenant_id == self.tenant_id,
            AssetMovement.movement_number.like(f"{prefix}%")
        ).order_by(desc(AssetMovement.movement_number)).first()

        if last and last.movement_number:
            try:
                last_num = int(last.movement_number.split("-")[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}0001"

    def create(self, data: dict[str, Any], created_by: UUID = None) -> AssetMovement:
        if "movement_number" not in data or not data["movement_number"]:
            data["movement_number"] = self.get_next_number()

        entity = AssetMovement(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: AssetMovement, data: dict[str, Any], updated_by: UUID = None) -> AssetMovement:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: AssetMovement, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class AssetMaintenanceRepository:
    """Repository pour les maintenances."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(AssetMaintenance).filter(AssetMaintenance.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(AssetMaintenance.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> AssetMaintenance | None:
        return self._base_query().filter(AssetMaintenance.id == id).first()

    def get_by_asset(self, asset_id: UUID) -> List[AssetMaintenance]:
        return self._base_query().filter(
            AssetMaintenance.asset_id == asset_id
        ).order_by(desc(AssetMaintenance.scheduled_date)).all()

    def list(
        self,
        asset_id: UUID | None = None,
        status: MaintenanceStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AssetMaintenance], int]:
        query = self._base_query()

        if asset_id:
            query = query.filter(AssetMaintenance.asset_id == asset_id)
        if status:
            query = query.filter(AssetMaintenance.status == status)
        if date_from:
            query = query.filter(AssetMaintenance.scheduled_date >= date_from)
        if date_to:
            query = query.filter(AssetMaintenance.scheduled_date <= date_to)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(AssetMaintenance.scheduled_date).offset(offset).limit(page_size).all()
        return items, total

    def get_upcoming(self, days: int = 30) -> List[AssetMaintenance]:
        today = date.today()
        return self._base_query().filter(
            AssetMaintenance.status.in_([MaintenanceStatus.PLANNED, MaintenanceStatus.OVERDUE]),
            AssetMaintenance.scheduled_date <= today + timedelta(days=days)
        ).order_by(AssetMaintenance.scheduled_date).all()

    def get_overdue(self) -> List[AssetMaintenance]:
        today = date.today()
        return self._base_query().filter(
            AssetMaintenance.status == MaintenanceStatus.PLANNED,
            AssetMaintenance.scheduled_date < today
        ).all()

    def get_next_number(self) -> str:
        year = datetime.utcnow().year
        prefix = f"MAINT-{year}-"

        last = self.db.query(AssetMaintenance).filter(
            AssetMaintenance.tenant_id == self.tenant_id,
            AssetMaintenance.maintenance_number.like(f"{prefix}%")
        ).order_by(desc(AssetMaintenance.maintenance_number)).first()

        if last and last.maintenance_number:
            try:
                last_num = int(last.maintenance_number.split("-")[-1])
                return f"{prefix}{last_num + 1:05d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}00001"

    def create(self, data: dict[str, Any], created_by: UUID = None) -> AssetMaintenance:
        if "maintenance_number" not in data or not data["maintenance_number"]:
            data["maintenance_number"] = self.get_next_number()

        # Calculate total cost
        labor = Decimal(str(data.get("labor_cost", 0)))
        parts = Decimal(str(data.get("parts_cost", 0)))
        external = Decimal(str(data.get("external_cost", 0)))
        other = Decimal(str(data.get("other_cost", 0)))
        data["total_cost"] = labor + parts + external + other

        entity = AssetMaintenance(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: AssetMaintenance, data: dict[str, Any], updated_by: UUID = None) -> AssetMaintenance:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        # Recalculate total cost
        entity.total_cost = (
            (entity.labor_cost or Decimal("0")) +
            (entity.parts_cost or Decimal("0")) +
            (entity.external_cost or Decimal("0")) +
            (entity.other_cost or Decimal("0"))
        )

        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: AssetMaintenance, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class AssetInventoryRepository:
    """Repository pour les inventaires physiques."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(AssetInventory).filter(AssetInventory.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(AssetInventory.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> AssetInventory | None:
        return self._base_query().options(
            joinedload(AssetInventory.items)
        ).filter(AssetInventory.id == id).first()

    def list(
        self,
        status: InventoryStatus | None = None,
        location_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AssetInventory], int]:
        query = self._base_query()

        if status:
            query = query.filter(AssetInventory.status == status)
        if location_id:
            query = query.filter(AssetInventory.location_id == location_id)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(AssetInventory.inventory_date)).offset(offset).limit(page_size).all()
        return items, total

    def has_in_progress(self, location_id: UUID = None) -> bool:
        query = self._base_query().filter(
            AssetInventory.status == InventoryStatus.IN_PROGRESS
        )
        if location_id:
            query = query.filter(AssetInventory.location_id == location_id)
        return query.count() > 0

    def get_next_number(self) -> str:
        year = datetime.utcnow().year
        prefix = f"INV-{year}-"

        last = self.db.query(AssetInventory).filter(
            AssetInventory.tenant_id == self.tenant_id,
            AssetInventory.inventory_number.like(f"{prefix}%")
        ).order_by(desc(AssetInventory.inventory_number)).first()

        if last:
            try:
                last_num = int(last.inventory_number.split("-")[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}0001"

    def create(self, data: dict[str, Any], created_by: UUID = None) -> AssetInventory:
        if "inventory_number" not in data or not data["inventory_number"]:
            data["inventory_number"] = self.get_next_number()

        entity = AssetInventory(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: AssetInventory, data: dict[str, Any], updated_by: UUID = None) -> AssetInventory:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def add_items(self, inventory_id: UUID, items: List[dict[str, Any]]) -> List[AssetInventoryItem]:
        objects = [
            AssetInventoryItem(tenant_id=self.tenant_id, inventory_id=inventory_id, **item)
            for item in items
        ]
        self.db.add_all(objects)
        self.db.commit()
        return objects

    def get_item(self, item_id: UUID) -> AssetInventoryItem | None:
        return self.db.query(AssetInventoryItem).filter(
            AssetInventoryItem.tenant_id == self.tenant_id,
            AssetInventoryItem.id == item_id
        ).first()

    def update_item(self, item: AssetInventoryItem, data: dict[str, Any]) -> AssetInventoryItem:
        for key, value in data.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def recalculate_counts(self, inventory: AssetInventory):
        items = self.db.query(AssetInventoryItem).filter(
            AssetInventoryItem.inventory_id == inventory.id
        ).all()

        inventory.assets_found = sum(1 for i in items if i.found)
        inventory.assets_missing = sum(1 for i in items if not i.found and not i.is_unexpected)
        inventory.assets_unexpected = sum(1 for i in items if i.is_unexpected)
        inventory.assets_condition_issues = sum(1 for i in items if i.condition_rating and i.condition_rating <= 2)

        self.db.commit()


class DepreciationRunRepository:
    """Repository pour les executions d'amortissement."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(DepreciationRun).filter(DepreciationRun.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(DepreciationRun.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> DepreciationRun | None:
        return self._base_query().filter(DepreciationRun.id == id).first()

    def list(
        self,
        fiscal_year: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DepreciationRun], int]:
        query = self._base_query()

        if fiscal_year:
            query = query.filter(DepreciationRun.fiscal_year == fiscal_year)
        if status:
            query = query.filter(DepreciationRun.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(DepreciationRun.run_date)).offset(offset).limit(page_size).all()
        return items, total

    def period_exists(self, period_start: date, period_end: date) -> bool:
        return self._base_query().filter(
            DepreciationRun.period_start == period_start,
            DepreciationRun.period_end == period_end,
            DepreciationRun.status.in_(["VALIDATED", "POSTED"])
        ).count() > 0

    def get_next_number(self) -> str:
        year = datetime.utcnow().year
        prefix = f"DEP-{year}-"

        last = self.db.query(DepreciationRun).filter(
            DepreciationRun.tenant_id == self.tenant_id,
            DepreciationRun.run_number.like(f"{prefix}%")
        ).order_by(desc(DepreciationRun.run_number)).first()

        if last:
            try:
                last_num = int(last.run_number.split("-")[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}0001"

    def create(self, data: dict[str, Any], created_by: UUID = None) -> DepreciationRun:
        if "run_number" not in data or not data["run_number"]:
            data["run_number"] = self.get_next_number()

        entity = DepreciationRun(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: DepreciationRun, data: dict[str, Any], updated_by: UUID = None) -> DepreciationRun:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity


class AssetInsurancePolicyRepository:
    """Repository pour les polices d'assurance."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(AssetInsurancePolicy).filter(AssetInsurancePolicy.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(AssetInsurancePolicy.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> AssetInsurancePolicy | None:
        return self._base_query().options(
            joinedload(AssetInsurancePolicy.items)
        ).filter(AssetInsurancePolicy.id == id).first()

    def list(
        self,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AssetInsurancePolicy], int]:
        query = self._base_query()

        if status:
            query = query.filter(AssetInsurancePolicy.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(AssetInsurancePolicy.start_date)).offset(offset).limit(page_size).all()
        return items, total

    def create(self, data: dict[str, Any], created_by: UUID = None) -> AssetInsurancePolicy:
        entity = AssetInsurancePolicy(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def add_item(self, policy_id: UUID, data: dict[str, Any], created_by: UUID = None) -> AssetInsuranceItem:
        item = AssetInsuranceItem(
            tenant_id=self.tenant_id,
            policy_id=policy_id,
            created_by=created_by,
            **data
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def asset_in_policy(self, policy_id: UUID, asset_id: UUID) -> bool:
        return self.db.query(AssetInsuranceItem).filter(
            AssetInsuranceItem.policy_id == policy_id,
            AssetInsuranceItem.asset_id == asset_id
        ).count() > 0


class AssetTransferRepository:
    """Repository pour les transferts d'actifs."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(AssetTransfer).filter(AssetTransfer.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(AssetTransfer.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> AssetTransfer | None:
        return self._base_query().filter(AssetTransfer.id == id).first()

    def get_by_asset(self, asset_id: UUID) -> List[AssetTransfer]:
        return self._base_query().filter(
            AssetTransfer.asset_id == asset_id
        ).order_by(desc(AssetTransfer.transfer_date)).all()

    def list(
        self,
        asset_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AssetTransfer], int]:
        query = self._base_query()

        if asset_id:
            query = query.filter(AssetTransfer.asset_id == asset_id)
        if status:
            query = query.filter(AssetTransfer.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(AssetTransfer.transfer_date)).offset(offset).limit(page_size).all()
        return items, total

    def get_next_number(self) -> str:
        year = datetime.utcnow().year
        prefix = f"TRF-{year}-"

        last = self.db.query(AssetTransfer).filter(
            AssetTransfer.tenant_id == self.tenant_id,
            AssetTransfer.transfer_number.like(f"{prefix}%")
        ).order_by(desc(AssetTransfer.transfer_number)).first()

        if last:
            try:
                last_num = int(last.transfer_number.split("-")[-1])
                return f"{prefix}{last_num + 1:05d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}00001"

    def create(self, data: dict[str, Any], created_by: UUID = None) -> AssetTransfer:
        if "transfer_number" not in data or not data["transfer_number"]:
            data["transfer_number"] = self.get_next_number()

        entity = AssetTransfer(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: AssetTransfer, data: dict[str, Any], updated_by: UUID = None) -> AssetTransfer:
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity
