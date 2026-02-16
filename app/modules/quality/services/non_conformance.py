"""
AZALS MODULE M7 - Non-Conformance Service
==========================================

Gestion des non-conformités.
"""

import logging
from datetime import date
from typing import Optional, Tuple, List

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    NonConformance,
    NonConformanceAction,
    NonConformanceStatus,
    NonConformanceType,
    NonConformanceSeverity,
)
from app.modules.quality.schemas import (
    NonConformanceCreate,
    NonConformanceUpdate,
    NonConformanceClose,
    NonConformanceActionCreate,
    NonConformanceActionUpdate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class NonConformanceService(BaseQualityService[NonConformance]):
    """Service de gestion des non-conformités."""

    model = NonConformance

    # ========================================================================
    # CRUD NON-CONFORMITÉS
    # ========================================================================

    def create(self, data: NonConformanceCreate) -> NonConformance:
        """Crée une nouvelle non-conformité."""
        nc_number = self._generate_sequence("NON_CONFORMITE")
        logger.info(
            "Creating non-conformance | tenant=%s user=%s type=%s severity=%s nc_number=%s",
            self.tenant_id, self.user_id, data.nc_type, data.severity, nc_number
        )

        nc = NonConformance(
            tenant_id=self.tenant_id,
            nc_number=nc_number,
            title=data.title,
            description=data.description,
            nc_type=data.nc_type,
            severity=data.severity,
            status=NonConformanceStatus.DRAFT,
            detected_date=data.detected_date,
            detected_by_id=self.user_id,
            detection_location=data.detection_location,
            detection_phase=data.detection_phase,
            source_type=data.source_type,
            source_reference=data.source_reference,
            source_id=data.source_id,
            product_id=data.product_id,
            lot_number=data.lot_number,
            serial_number=data.serial_number,
            quantity_affected=data.quantity_affected,
            unit_id=data.unit_id,
            supplier_id=data.supplier_id,
            customer_id=data.customer_id,
            immediate_action=data.immediate_action,
            responsible_id=data.responsible_id,
            department=data.department,
            notes=data.notes,
            created_by=self.user_id,
        )

        self.db.add(nc)
        self.db.commit()
        self.db.refresh(nc)

        logger.info("Non-conformance created | nc_id=%s nc_number=%s", nc.id, nc.nc_number)
        return nc

    def get(self, nc_id: int) -> Optional[NonConformance]:
        """Récupère une non-conformité par ID."""
        return self._get_by_id(nc_id, options=[joinedload(NonConformance.actions)])

    def get_by_number(self, nc_number: str) -> Optional[NonConformance]:
        """Récupère une non-conformité par numéro."""
        return self._base_query().options(
            joinedload(NonConformance.actions)
        ).filter(NonConformance.nc_number == nc_number).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        nc_type: Optional[NonConformanceType] = None,
        status: Optional[NonConformanceStatus] = None,
        severity: Optional[NonConformanceSeverity] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[NonConformance], int]:
        """Liste les non-conformités avec filtres."""
        query = self._base_query()

        if nc_type:
            query = query.filter(NonConformance.nc_type == nc_type)
        if status:
            query = query.filter(NonConformance.status == status)
        if severity:
            query = query.filter(NonConformance.severity == severity)
        if date_from:
            query = query.filter(NonConformance.detected_date >= date_from)
        if date_to:
            query = query.filter(NonConformance.detected_date <= date_to)

        if search:
            from sqlalchemy import or_
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    NonConformance.nc_number.ilike(search_filter),
                    NonConformance.title.ilike(search_filter),
                    NonConformance.description.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(
            joinedload(NonConformance.actions)
        ).order_by(
            NonConformance.detected_date.desc()
        ).offset(skip).limit(limit).all()

        return items, total

    def update(self, nc_id: int, data: NonConformanceUpdate) -> Optional[NonConformance]:
        """Met à jour une non-conformité."""
        nc = self.get(nc_id)
        if not nc:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(nc, update_data)

    # ========================================================================
    # WORKFLOW NON-CONFORMITÉS
    # ========================================================================

    def open(self, nc_id: int) -> Optional[NonConformance]:
        """Ouvre une non-conformité."""
        nc = self.get(nc_id)
        if not nc or nc.status != NonConformanceStatus.DRAFT:
            return None

        nc.status = NonConformanceStatus.OPEN
        nc.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(nc)
        return nc

    def close(self, nc_id: int, data: NonConformanceClose) -> Optional[NonConformance]:
        """Clôture une non-conformité."""
        nc = self.get(nc_id)
        if not nc:
            return None

        nc.status = NonConformanceStatus.CLOSED
        nc.closed_date = date.today()
        nc.closed_by_id = self.user_id
        nc.closure_justification = data.closure_justification
        nc.effectiveness_verified = data.effectiveness_verified
        if data.effectiveness_verified:
            nc.effectiveness_date = date.today()

        nc.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(nc)
        return nc

    # ========================================================================
    # ACTIONS NON-CONFORMITÉS
    # ========================================================================

    def add_action(self, nc_id: int, data: NonConformanceActionCreate) -> Optional[NonConformanceAction]:
        """Ajoute une action à une non-conformité."""
        nc = self.get(nc_id)
        if not nc:
            return None

        # Numéro d'action
        action_count = self.db.query(func.count(NonConformanceAction.id)).filter(
            NonConformanceAction.nc_id == nc_id
        ).scalar() or 0

        action = NonConformanceAction(
            tenant_id=self.tenant_id,
            nc_id=nc_id,
            action_number=action_count + 1,
            action_type=data.action_type,
            description=data.description,
            responsible_id=data.responsible_id,
            planned_date=data.planned_date,
            due_date=data.due_date,
            status="PLANNED",
            comments=data.comments,
            created_by=self.user_id,
        )
        self.db.add(action)

        # Mettre à jour statut NC si nécessaire
        if nc.status == NonConformanceStatus.OPEN:
            nc.status = NonConformanceStatus.ACTION_REQUIRED
            nc.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(action)
        return action

    def update_action(self, action_id: int, data: NonConformanceActionUpdate) -> Optional[NonConformanceAction]:
        """Met à jour une action de non-conformité."""
        action = self.db.query(NonConformanceAction).filter(
            NonConformanceAction.id == action_id,
            NonConformanceAction.tenant_id == self.tenant_id
        ).first()
        if not action:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(action, field):
                setattr(action, field, value)

        self.db.commit()
        self.db.refresh(action)
        return action

    def complete_action(self, action_id: int) -> Optional[NonConformanceAction]:
        """Marque une action comme terminée."""
        action = self.db.query(NonConformanceAction).filter(
            NonConformanceAction.id == action_id,
            NonConformanceAction.tenant_id == self.tenant_id
        ).first()
        if not action:
            return None

        action.status = "COMPLETED"
        action.completed_date = date.today()
        action.completed_by_id = self.user_id
        self.db.commit()
        self.db.refresh(action)
        return action
