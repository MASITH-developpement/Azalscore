"""
Repository - Module Forecasting (GAP-076)

CRITIQUE: Toutes les requêtes filtrées par tenant_id.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from .models import (
    Forecast, ForecastModel, Scenario, ForecastBudget, KPI,
    ForecastStatus, BudgetStatus, KPIStatus, ForecastType
)
# Alias pour compatibilité
Budget = ForecastBudget
from .schemas import ForecastFilters, BudgetFilters, KPIFilters


class ForecastRepository:
    """
    Repository Forecast avec isolation tenant obligatoire.

    SÉCURITÉ: _base_query() filtre TOUJOURS par tenant_id.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Point d'entrée unique - TOUJOURS filtrer par tenant_id."""
        query = self.db.query(Forecast).filter(
            Forecast.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Forecast.is_deleted == False)
        return query

    # === READ ===
    def get_by_id(self, id: UUID) -> Optional[Forecast]:
        return self._base_query().filter(Forecast.id == id).first()

    def get_by_code(self, code: str) -> Optional[Forecast]:
        return self._base_query().filter(Forecast.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(Forecast.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Forecast.code == code.upper())
        if exclude_id:
            query = query.filter(Forecast.id != exclude_id)
        return query.count() > 0

    # === LIST ===
    def list(
        self,
        filters: ForecastFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Forecast], int]:
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        sort_col = getattr(Forecast, sort_by, Forecast.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: ForecastFilters):
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(or_(
                Forecast.name.ilike(term),
                Forecast.code.ilike(term),
                Forecast.description.ilike(term)
            ))

        if filters.forecast_type:
            query = query.filter(Forecast.forecast_type.in_(filters.forecast_type))

        if filters.status:
            query = query.filter(Forecast.status.in_(filters.status))

        if filters.method:
            query = query.filter(Forecast.method.in_(filters.method))

        if filters.category:
            query = query.filter(Forecast.category == filters.category)

        if filters.date_from:
            query = query.filter(Forecast.start_date >= filters.date_from)

        if filters.date_to:
            query = query.filter(Forecast.end_date <= filters.date_to)

        return query

    # === AUTOCOMPLETE ===
    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []

        query = self._base_query().filter(
            Forecast.status.in_([ForecastStatus.ACTIVE, ForecastStatus.APPROVED])
        )

        if field == "code":
            query = query.filter(Forecast.code.ilike(f"{prefix}%"))
        else:
            query = query.filter(or_(
                Forecast.name.ilike(f"{prefix}%"),
                Forecast.code.ilike(f"{prefix}%")
            ))

        results = query.order_by(Forecast.name).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": f"[{item.code}] {item.name}"
            }
            for item in results
        ]

    # === CREATE ===
    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Forecast:
        entity = Forecast(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # === UPDATE ===
    def update(
        self,
        entity: Forecast,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> Forecast:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # === DELETE ===
    def soft_delete(self, entity: Forecast, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def hard_delete(self, entity: Forecast) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True

    def restore(self, entity: Forecast) -> Forecast:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # === BULK ===
    def bulk_create(self, items: List[Dict[str, Any]], created_by: UUID = None) -> int:
        now = datetime.utcnow()
        for item in items:
            item["tenant_id"] = self.tenant_id
            item["created_at"] = now
            item["created_by"] = created_by
        self.db.bulk_insert_mappings(Forecast, items)
        self.db.commit()
        return len(items)

    def bulk_update(self, ids: List[UUID], data: Dict[str, Any], updated_by: UUID = None) -> int:
        data["updated_at"] = datetime.utcnow()
        data["updated_by"] = updated_by
        result = self._base_query().filter(Forecast.id.in_(ids)).update(
            data, synchronize_session=False
        )
        self.db.commit()
        return result

    def bulk_delete(self, ids: List[UUID], deleted_by: UUID = None, hard: bool = False) -> int:
        if hard:
            result = self._base_query().filter(Forecast.id.in_(ids)).delete(
                synchronize_session=False
            )
        else:
            result = self._base_query().filter(Forecast.id.in_(ids)).update({
                "is_deleted": True,
                "deleted_at": datetime.utcnow(),
                "deleted_by": deleted_by
            }, synchronize_session=False)
        self.db.commit()
        return result

    # === STATS ===
    def get_stats(self) -> Dict[str, Any]:
        base = self._base_query()
        total = base.count()
        by_status = {}
        for status in ForecastStatus:
            by_status[status.value] = base.filter(Forecast.status == status).count()
        by_type = {}
        for ftype in ForecastType:
            by_type[ftype.value] = base.filter(Forecast.forecast_type == ftype).count()
        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type
        }


class BudgetRepository:
    """Repository Budget avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(Budget).filter(Budget.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Budget.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Budget]:
        return self._base_query().filter(Budget.id == id).first()

    def get_by_code(self, code: str) -> Optional[Budget]:
        return self._base_query().filter(Budget.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(Budget.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Budget.code == code.upper())
        if exclude_id:
            query = query.filter(Budget.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: BudgetFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Budget], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Budget.name.ilike(term),
                    Budget.code.ilike(term)
                ))
            if filters.fiscal_year:
                query = query.filter(Budget.fiscal_year == filters.fiscal_year)
            if filters.status:
                query = query.filter(Budget.status.in_(filters.status))
            if filters.department_id:
                query = query.filter(Budget.department_id == filters.department_id)

        total = query.count()
        sort_col = getattr(Budget, sort_by, Budget.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(or_(
            Budget.name.ilike(f"{prefix}%"),
            Budget.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(Budget.name).limit(limit).all()
        return [
            {"id": str(b.id), "code": b.code, "name": b.name, "label": f"[{b.code}] {b.name}"}
            for b in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Budget:
        entity = Budget(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Budget, data: Dict[str, Any], updated_by: UUID = None) -> Budget:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Budget, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: Budget) -> Budget:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity


class KPIRepository:
    """Repository KPI avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(KPI).filter(KPI.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(KPI.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[KPI]:
        return self._base_query().filter(KPI.id == id).first()

    def get_by_code(self, code: str) -> Optional[KPI]:
        return self._base_query().filter(KPI.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(KPI.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(KPI.code == code.upper())
        if exclude_id:
            query = query.filter(KPI.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: KPIFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[KPI], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    KPI.name.ilike(term),
                    KPI.code.ilike(term)
                ))
            if filters.category:
                query = query.filter(KPI.category == filters.category)
            if filters.status:
                query = query.filter(KPI.status.in_(filters.status))
            if filters.is_active is not None:
                query = query.filter(KPI.is_active == filters.is_active)

        total = query.count()
        sort_col = getattr(KPI, sort_by, KPI.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            KPI.is_active == True
        ).filter(or_(
            KPI.name.ilike(f"{prefix}%"),
            KPI.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(KPI.name).limit(limit).all()
        return [
            {"id": str(k.id), "code": k.code, "name": k.name, "label": f"[{k.code}] {k.name}"}
            for k in results
        ]

    def get_by_category(self, category: str) -> List[KPI]:
        return self._base_query().filter(
            KPI.category == category,
            KPI.is_active == True
        ).all()

    def get_alerts(self) -> List[KPI]:
        """Récupère les KPIs en alerte (rouge)."""
        return self._base_query().filter(
            KPI.status == KPIStatus.RED,
            KPI.is_active == True
        ).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> KPI:
        entity = KPI(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: KPI, data: Dict[str, Any], updated_by: UUID = None) -> KPI:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: KPI, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: KPI) -> KPI:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Données pour le dashboard KPI."""
        kpis = self._base_query().filter(KPI.is_active == True).all()

        by_status = {"green": 0, "amber": 0, "red": 0}
        by_category: Dict[str, List[Dict]] = {}

        for kpi in kpis:
            by_status[kpi.status.value] = by_status.get(kpi.status.value, 0) + 1
            cat = kpi.category or "Other"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "id": str(kpi.id),
                "name": kpi.name,
                "code": kpi.code,
                "current_value": float(kpi.current_value),
                "target_value": float(kpi.target_value),
                "achievement_percent": float(kpi.achievement_percent),
                "status": kpi.status.value,
                "trend": kpi.trend,
                "unit": kpi.unit
            })

        alerts = [
            {"kpi_id": str(k.id), "name": k.name, "status": k.status.value, "value": float(k.current_value)}
            for k in kpis if k.status == KPIStatus.RED
        ]

        return {
            "total_kpis": len(kpis),
            "by_status": by_status,
            "by_category": by_category,
            "alerts": alerts
        }


class ScenarioRepository:
    """Repository Scenario avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(Scenario).filter(Scenario.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Scenario.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Scenario]:
        return self._base_query().filter(Scenario.id == id).first()

    def get_by_forecast(self, forecast_id: UUID) -> List[Scenario]:
        return self._base_query().filter(Scenario.base_forecast_id == forecast_id).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Scenario:
        entity = Scenario(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Scenario, data: Dict[str, Any], updated_by: UUID = None) -> Scenario:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Scenario, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class ForecastModelRepository:
    """Repository ForecastModel avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ForecastModel).filter(ForecastModel.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(ForecastModel.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ForecastModel]:
        return self._base_query().filter(ForecastModel.id == id).first()

    def get_by_code(self, code: str) -> Optional[ForecastModel]:
        return self._base_query().filter(ForecastModel.code == code.upper()).first()

    def list_active(self) -> List[ForecastModel]:
        return self._base_query().filter(ForecastModel.is_active == True).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ForecastModel:
        entity = ForecastModel(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ForecastModel, data: Dict[str, Any], updated_by: UUID = None) -> ForecastModel:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: ForecastModel, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True
