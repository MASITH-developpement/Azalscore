"""
Repository Manufacturing / Fabrication
=======================================
CRITIQUE: Toutes les requêtes filtrées par tenant_id via _base_query()
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from .models import (
    BOM, BOMLine, BOMStatus, BOMType,
    Workcenter, WorkcenterState, WorkcenterType,
    Routing, Operation,
    WorkOrder, WorkOrderStatus, WorkOrderOperation, OperationStatus,
    QualityCheck, QualityCheckType, QualityResult,
    ProductionLog
)
from .schemas import (
    BOMFilters, WorkcenterFilters, WorkOrderFilters
)


T = TypeVar('T')


class BaseTenantRepository:
    """
    Repository de base avec isolation tenant obligatoire.

    SÉCURITÉ: _base_query() filtre TOUJOURS par tenant_id.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        model: Type[T],
        include_deleted: bool = False
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.model = model
        self.include_deleted = include_deleted

    def _base_query(self):
        """
        CRITIQUE: Point d'entrée unique pour toutes les requêtes.
        TOUJOURS filtrer par tenant_id.
        """
        query = self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )
        if not self.include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[T]:
        """Récupère par ID."""
        return self._base_query().filter(self.model.id == id).first()

    def exists(self, id: UUID) -> bool:
        """Vérifie l'existence."""
        return self._base_query().filter(self.model.id == id).count() > 0

    def count(self, filters: Dict[str, Any] = None) -> int:
        """Compte les entités."""
        query = self._base_query()
        return query.count()


class BOMRepository(BaseTenantRepository):
    """Repository BOM avec isolation tenant."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        super().__init__(db, tenant_id, BOM, include_deleted)

    def get_by_code(self, code: str) -> Optional[BOM]:
        """Récupère par code."""
        return self._base_query().filter(
            BOM.code == code.upper()
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        """Vérifie si le code existe."""
        query = self._base_query().filter(BOM.code == code.upper())
        if exclude_id:
            query = query.filter(BOM.id != exclude_id)
        return query.count() > 0

    def get_current_for_product(self, product_id: UUID) -> Optional[BOM]:
        """Récupère la BOM active et courante pour un produit."""
        return self._base_query().filter(
            BOM.product_id == product_id,
            BOM.status == BOMStatus.ACTIVE,
            BOM.is_current == True
        ).first()

    def list(
        self,
        filters: BOMFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[BOM], int]:
        """Liste paginée avec filtres."""
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        # Tri
        sort_col = getattr(BOM, sort_by, BOM.created_at)
        query = query.order_by(
            desc(sort_col) if sort_dir == "desc" else asc(sort_col)
        )

        # Pagination
        offset = (page - 1) * page_size
        items = query.options(
            joinedload(BOM.lines)
        ).offset(offset).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: BOMFilters):
        """Applique les filtres."""
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(or_(
                BOM.name.ilike(term),
                BOM.code.ilike(term),
                BOM.product_code.ilike(term),
                BOM.product_name.ilike(term)
            ))

        if filters.status:
            query = query.filter(BOM.status.in_(filters.status))

        if filters.bom_type:
            query = query.filter(BOM.bom_type.in_(filters.bom_type))

        if filters.product_id:
            query = query.filter(BOM.product_id == filters.product_id)

        if filters.tags:
            query = query.filter(BOM.tags.overlap(filters.tags))

        if filters.date_from:
            query = query.filter(BOM.created_at >= filters.date_from)

        if filters.date_to:
            query = query.filter(BOM.created_at <= filters.date_to)

        return query

    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete."""
        if len(prefix) < 2:
            return []

        query = self._base_query().filter(
            BOM.status == BOMStatus.ACTIVE
        )

        if field == "code":
            query = query.filter(BOM.code.ilike(f"{prefix}%"))
        else:
            query = query.filter(or_(
                BOM.name.ilike(f"{prefix}%"),
                BOM.code.ilike(f"{prefix}%")
            ))

        results = query.order_by(BOM.name).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": f"[{item.code}] {item.name}"
            }
            for item in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> BOM:
        """Crée une BOM."""
        lines_data = data.pop('lines', [])

        bom = BOM(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(bom)
        self.db.flush()

        # Ajouter les lignes
        for i, line_data in enumerate(lines_data):
            line = BOMLine(
                tenant_id=self.tenant_id,
                bom_id=bom.id,
                sequence=line_data.get('sequence', (i + 1) * 10),
                **{k: v for k, v in line_data.items() if k != 'sequence'}
            )
            line.calculate_total_cost()
            self.db.add(line)

        self.db.commit()
        self.db.refresh(bom)
        bom.recalculate_costs()
        self.db.commit()

        return bom

    def update(
        self,
        bom: BOM,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> BOM:
        """Met à jour une BOM."""
        for key, value in data.items():
            if hasattr(bom, key):
                setattr(bom, key, value)
        bom.updated_by = updated_by
        self.db.commit()
        self.db.refresh(bom)
        return bom

    def soft_delete(self, bom: BOM, deleted_by: UUID = None) -> bool:
        """Soft delete."""
        bom.is_deleted = True
        bom.deleted_at = datetime.utcnow()
        bom.deleted_by = deleted_by
        self.db.commit()
        return True

    def hard_delete(self, bom: BOM) -> bool:
        """Hard delete."""
        self.db.delete(bom)
        self.db.commit()
        return True

    def restore(self, bom: BOM) -> BOM:
        """Restaure une BOM supprimée."""
        bom.is_deleted = False
        bom.deleted_at = None
        bom.deleted_by = None
        self.db.commit()
        self.db.refresh(bom)
        return bom

    def add_line(
        self,
        bom: BOM,
        line_data: Dict[str, Any]
    ) -> BOMLine:
        """Ajoute une ligne à la BOM."""
        sequence = line_data.get('sequence')
        if sequence is None:
            max_seq = max([l.sequence for l in bom.lines], default=0)
            sequence = max_seq + 10

        line = BOMLine(
            tenant_id=self.tenant_id,
            bom_id=bom.id,
            sequence=sequence,
            **{k: v for k, v in line_data.items() if k != 'sequence'}
        )
        line.calculate_total_cost()
        self.db.add(line)
        self.db.commit()

        bom.recalculate_costs()
        self.db.commit()

        self.db.refresh(line)
        return line

    def update_line(
        self,
        line: BOMLine,
        data: Dict[str, Any]
    ) -> BOMLine:
        """Met à jour une ligne."""
        for key, value in data.items():
            if hasattr(line, key):
                setattr(line, key, value)
        line.calculate_total_cost()
        self.db.commit()

        # Recalculer les coûts de la BOM
        bom = line.bom
        bom.recalculate_costs()
        self.db.commit()

        self.db.refresh(line)
        return line

    def delete_line(self, line: BOMLine) -> bool:
        """Supprime une ligne."""
        bom = line.bom
        self.db.delete(line)
        self.db.commit()

        bom.recalculate_costs()
        self.db.commit()

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques."""
        base = self._base_query()
        total = base.count()
        by_status = {}
        for status in BOMStatus:
            by_status[status.value] = base.filter(
                BOM.status == status
            ).count()
        return {
            "total": total,
            "by_status": by_status
        }


class WorkcenterRepository(BaseTenantRepository):
    """Repository Workcenter avec isolation tenant."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        super().__init__(db, tenant_id, Workcenter, include_deleted)

    def get_by_code(self, code: str) -> Optional[Workcenter]:
        """Récupère par code."""
        return self._base_query().filter(
            Workcenter.code == code.upper()
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        """Vérifie si le code existe."""
        query = self._base_query().filter(Workcenter.code == code.upper())
        if exclude_id:
            query = query.filter(Workcenter.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: WorkcenterFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "code",
        sort_dir: str = "asc"
    ) -> Tuple[List[Workcenter], int]:
        """Liste paginée avec filtres."""
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        sort_col = getattr(Workcenter, sort_by, Workcenter.code)
        query = query.order_by(
            desc(sort_col) if sort_dir == "desc" else asc(sort_col)
        )

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: WorkcenterFilters):
        """Applique les filtres."""
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(or_(
                Workcenter.name.ilike(term),
                Workcenter.code.ilike(term),
                Workcenter.description.ilike(term)
            ))

        if filters.workcenter_type:
            query = query.filter(Workcenter.workcenter_type.in_(filters.workcenter_type))

        if filters.state:
            query = query.filter(Workcenter.state.in_(filters.state))

        if filters.is_active is not None:
            query = query.filter(Workcenter.is_active == filters.is_active)

        if filters.department:
            query = query.filter(Workcenter.department == filters.department)

        if filters.tags:
            query = query.filter(Workcenter.tags.overlap(filters.tags))

        return query

    def autocomplete(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete."""
        if len(prefix) < 2:
            return []

        query = self._base_query().filter(
            Workcenter.is_active == True,
            Workcenter.state != WorkcenterState.OFFLINE
        )

        if field == "code":
            query = query.filter(Workcenter.code.ilike(f"{prefix}%"))
        else:
            query = query.filter(or_(
                Workcenter.name.ilike(f"{prefix}%"),
                Workcenter.code.ilike(f"{prefix}%")
            ))

        results = query.order_by(Workcenter.name).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": f"[{item.code}] {item.name}"
            }
            for item in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Workcenter:
        """Crée un Workcenter."""
        wc = Workcenter(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(wc)
        self.db.commit()
        self.db.refresh(wc)
        return wc

    def update(
        self,
        wc: Workcenter,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> Workcenter:
        """Met à jour un Workcenter."""
        for key, value in data.items():
            if hasattr(wc, key):
                setattr(wc, key, value)
        wc.updated_by = updated_by
        self.db.commit()
        self.db.refresh(wc)
        return wc

    def soft_delete(self, wc: Workcenter, deleted_by: UUID = None) -> bool:
        """Soft delete."""
        wc.is_deleted = True
        wc.deleted_at = datetime.utcnow()
        wc.deleted_by = deleted_by
        self.db.commit()
        return True

    def hard_delete(self, wc: Workcenter) -> bool:
        """Hard delete."""
        self.db.delete(wc)
        self.db.commit()
        return True

    def restore(self, wc: Workcenter) -> Workcenter:
        """Restaure."""
        wc.is_deleted = False
        wc.deleted_at = None
        wc.deleted_by = None
        self.db.commit()
        self.db.refresh(wc)
        return wc

    def get_available(self) -> List[Workcenter]:
        """Liste les workcenters disponibles."""
        return self._base_query().filter(
            Workcenter.is_active == True,
            Workcenter.state == WorkcenterState.AVAILABLE
        ).order_by(Workcenter.code).all()


class RoutingRepository(BaseTenantRepository):
    """Repository Routing avec isolation tenant."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        super().__init__(db, tenant_id, Routing, include_deleted)

    def get_by_code(self, code: str) -> Optional[Routing]:
        """Récupère par code."""
        return self._base_query().options(
            joinedload(Routing.operations)
        ).filter(Routing.code == code.upper()).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        """Vérifie si le code existe."""
        query = self._base_query().filter(Routing.code == code.upper())
        if exclude_id:
            query = query.filter(Routing.id != exclude_id)
        return query.count() > 0

    def get_current_for_product(self, product_id: UUID) -> Optional[Routing]:
        """Récupère la gamme active et courante pour un produit."""
        return self._base_query().options(
            joinedload(Routing.operations)
        ).filter(
            Routing.product_id == product_id,
            Routing.is_active == True,
            Routing.is_current == True
        ).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "code",
        sort_dir: str = "asc",
        product_id: UUID = None,
        is_active: bool = None
    ) -> Tuple[List[Routing], int]:
        """Liste paginée."""
        query = self._base_query()

        if product_id:
            query = query.filter(Routing.product_id == product_id)

        if is_active is not None:
            query = query.filter(Routing.is_active == is_active)

        total = query.count()

        sort_col = getattr(Routing, sort_by, Routing.code)
        query = query.order_by(
            desc(sort_col) if sort_dir == "desc" else asc(sort_col)
        )

        offset = (page - 1) * page_size
        items = query.options(
            joinedload(Routing.operations)
        ).offset(offset).limit(page_size).all()

        return items, total

    def autocomplete(
        self,
        prefix: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete."""
        if len(prefix) < 2:
            return []

        query = self._base_query().filter(
            Routing.is_active == True,
            or_(
                Routing.name.ilike(f"{prefix}%"),
                Routing.code.ilike(f"{prefix}%")
            )
        )

        results = query.order_by(Routing.name).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "label": f"[{item.code}] {item.name}"
            }
            for item in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Routing:
        """Crée une Routing."""
        operations_data = data.pop('operations', [])

        routing = Routing(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(routing)
        self.db.flush()

        # Ajouter les opérations
        for i, op_data in enumerate(operations_data):
            operation = Operation(
                tenant_id=self.tenant_id,
                routing_id=routing.id,
                sequence=op_data.get('sequence', (i + 1) * 10),
                **{k: v for k, v in op_data.items() if k != 'sequence'}
            )
            self.db.add(operation)

        self.db.commit()
        self.db.refresh(routing)
        routing.recalculate_totals()
        self.db.commit()

        return routing

    def update(
        self,
        routing: Routing,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> Routing:
        """Met à jour une Routing."""
        for key, value in data.items():
            if hasattr(routing, key):
                setattr(routing, key, value)
        routing.updated_by = updated_by
        self.db.commit()
        self.db.refresh(routing)
        return routing

    def soft_delete(self, routing: Routing, deleted_by: UUID = None) -> bool:
        """Soft delete."""
        routing.is_deleted = True
        routing.deleted_at = datetime.utcnow()
        routing.deleted_by = deleted_by
        self.db.commit()
        return True

    def add_operation(
        self,
        routing: Routing,
        op_data: Dict[str, Any]
    ) -> Operation:
        """Ajoute une opération."""
        sequence = op_data.get('sequence')
        if sequence is None:
            max_seq = max([op.sequence for op in routing.operations], default=0)
            sequence = max_seq + 10

        operation = Operation(
            tenant_id=self.tenant_id,
            routing_id=routing.id,
            sequence=sequence,
            **{k: v for k, v in op_data.items() if k != 'sequence'}
        )
        self.db.add(operation)
        self.db.commit()

        routing.recalculate_totals()
        self.db.commit()

        self.db.refresh(operation)
        return operation


class WorkOrderRepository(BaseTenantRepository):
    """Repository Work Order avec isolation tenant."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        super().__init__(db, tenant_id, WorkOrder, include_deleted)
        self._wo_counter = 0

    def get_by_number(self, number: str) -> Optional[WorkOrder]:
        """Récupère par numéro."""
        return self._base_query().options(
            joinedload(WorkOrder.operations),
            joinedload(WorkOrder.quality_checks)
        ).filter(WorkOrder.number == number).first()

    def number_exists(self, number: str, exclude_id: UUID = None) -> bool:
        """Vérifie si le numéro existe."""
        query = self._base_query().filter(WorkOrder.number == number)
        if exclude_id:
            query = query.filter(WorkOrder.id != exclude_id)
        return query.count() > 0

    def generate_number(self) -> str:
        """Génère un numéro d'OF unique."""
        # Trouver le max actuel
        result = self.db.query(func.max(WorkOrder.number)).filter(
            WorkOrder.tenant_id == self.tenant_id
        ).scalar()

        if result:
            # Extraire le numéro
            try:
                current = int(result.split('-')[-1])
            except (ValueError, IndexError):
                current = 0
        else:
            current = 0

        return f"MO-{current + 1:06d}"

    def list(
        self,
        filters: WorkOrderFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[WorkOrder], int]:
        """Liste paginée avec filtres."""
        query = self._base_query()

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        sort_col = getattr(WorkOrder, sort_by, WorkOrder.created_at)
        query = query.order_by(
            desc(sort_col) if sort_dir == "desc" else asc(sort_col)
        )

        offset = (page - 1) * page_size
        items = query.options(
            joinedload(WorkOrder.operations)
        ).offset(offset).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: WorkOrderFilters):
        """Applique les filtres."""
        if filters.search:
            term = f"%{filters.search}%"
            query = query.filter(or_(
                WorkOrder.name.ilike(term),
                WorkOrder.number.ilike(term),
                WorkOrder.product_code.ilike(term),
                WorkOrder.product_name.ilike(term)
            ))

        if filters.status:
            query = query.filter(WorkOrder.status.in_(filters.status))

        if filters.product_id:
            query = query.filter(WorkOrder.product_id == filters.product_id)

        if filters.priority_min is not None:
            query = query.filter(WorkOrder.priority >= filters.priority_min)

        if filters.planned_start_from:
            query = query.filter(WorkOrder.planned_start >= filters.planned_start_from)

        if filters.planned_start_to:
            query = query.filter(WorkOrder.planned_start <= filters.planned_start_to)

        if filters.tags:
            query = query.filter(WorkOrder.tags.overlap(filters.tags))

        return query

    def autocomplete(
        self,
        prefix: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete."""
        if len(prefix) < 2:
            return []

        query = self._base_query().filter(
            WorkOrder.status.notin_([WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]),
            or_(
                WorkOrder.number.ilike(f"{prefix}%"),
                WorkOrder.product_code.ilike(f"{prefix}%")
            )
        )

        results = query.order_by(WorkOrder.number).limit(limit).all()

        return [
            {
                "id": str(item.id),
                "code": item.number,
                "name": item.product_name,
                "label": f"[{item.number}] {item.product_name}"
            }
            for item in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> WorkOrder:
        """Crée un Work Order."""
        # Générer le numéro
        number = self.generate_number()

        wo = WorkOrder(
            tenant_id=self.tenant_id,
            number=number,
            created_by=created_by,
            **data
        )
        self.db.add(wo)
        self.db.commit()
        self.db.refresh(wo)
        return wo

    def update(
        self,
        wo: WorkOrder,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> WorkOrder:
        """Met à jour un Work Order."""
        for key, value in data.items():
            if hasattr(wo, key):
                setattr(wo, key, value)
        wo.updated_by = updated_by
        self.db.commit()
        self.db.refresh(wo)
        return wo

    def soft_delete(self, wo: WorkOrder, deleted_by: UUID = None) -> bool:
        """Soft delete."""
        wo.is_deleted = True
        wo.deleted_at = datetime.utcnow()
        wo.deleted_by = deleted_by
        self.db.commit()
        return True

    def add_operation(
        self,
        wo: WorkOrder,
        op_data: Dict[str, Any]
    ) -> WorkOrderOperation:
        """Ajoute une opération."""
        sequence = op_data.get('sequence')
        if sequence is None:
            max_seq = max([op.sequence for op in wo.operations], default=0)
            sequence = max_seq + 10

        operation = WorkOrderOperation(
            tenant_id=self.tenant_id,
            work_order_id=wo.id,
            sequence=sequence,
            **{k: v for k, v in op_data.items() if k != 'sequence'}
        )
        self.db.add(operation)
        self.db.commit()
        self.db.refresh(operation)
        return operation

    def get_by_status(
        self,
        status: WorkOrderStatus
    ) -> List[WorkOrder]:
        """Liste les OF par statut."""
        return self._base_query().filter(
            WorkOrder.status == status
        ).order_by(desc(WorkOrder.priority), WorkOrder.planned_start).all()

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques."""
        base = self._base_query()
        total = base.count()

        by_status = {}
        for status in WorkOrderStatus:
            by_status[status.value] = base.filter(
                WorkOrder.status == status
            ).count()

        total_produced = self.db.query(
            func.sum(WorkOrder.quantity_produced)
        ).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.is_deleted == False
        ).scalar() or Decimal("0")

        total_scrapped = self.db.query(
            func.sum(WorkOrder.quantity_scrapped)
        ).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.is_deleted == False
        ).scalar() or Decimal("0")

        return {
            "total": total,
            "by_status": by_status,
            "total_produced": total_produced,
            "total_scrapped": total_scrapped
        }


class QualityCheckRepository(BaseTenantRepository):
    """Repository Quality Check avec isolation tenant."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        include_deleted: bool = False
    ):
        super().__init__(db, tenant_id, QualityCheck, include_deleted)

    def list_for_work_order(
        self,
        work_order_id: UUID
    ) -> List[QualityCheck]:
        """Liste les contrôles d'un OF."""
        return self._base_query().filter(
            QualityCheck.work_order_id == work_order_id
        ).order_by(QualityCheck.created_at).all()

    def create(self, data: Dict[str, Any]) -> QualityCheck:
        """Crée un Quality Check."""
        qc = QualityCheck(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(qc)
        self.db.commit()
        self.db.refresh(qc)
        return qc

    def update(
        self,
        qc: QualityCheck,
        data: Dict[str, Any]
    ) -> QualityCheck:
        """Met à jour un Quality Check."""
        for key, value in data.items():
            if hasattr(qc, key):
                setattr(qc, key, value)
        self.db.commit()
        self.db.refresh(qc)
        return qc


class ProductionLogRepository(BaseTenantRepository):
    """Repository Production Log avec isolation tenant."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID
    ):
        super().__init__(db, tenant_id, ProductionLog, include_deleted=False)

    def list_for_work_order(
        self,
        work_order_id: UUID
    ) -> List[ProductionLog]:
        """Liste les logs d'un OF."""
        return self._base_query().filter(
            ProductionLog.work_order_id == work_order_id
        ).order_by(ProductionLog.timestamp).all()

    def create(self, data: Dict[str, Any]) -> ProductionLog:
        """Crée un log."""
        log = ProductionLog(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
