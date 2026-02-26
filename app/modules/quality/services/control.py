"""
AZALS MODULE M7 - Control Service
==================================

Gestion des contrôles qualité.
"""
from __future__ import annotations


import logging
from datetime import date, datetime
from typing import Optional, Tuple, List

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    QualityControl,
    QualityControlLine,
    QualityControlTemplate,
    ControlType,
    ControlStatus,
    ControlResult,
)
from app.modules.quality.schemas import (
    ControlCreate,
    ControlUpdate,
    ControlLineUpdate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class ControlService(BaseQualityService[QualityControl]):
    """Service de gestion des contrôles qualité."""

    model = QualityControl

    def create(self, data: ControlCreate) -> QualityControl:
        """Crée un contrôle qualité."""
        control = QualityControl(
            tenant_id=self.tenant_id,
            control_number=self._generate_sequence("INSPECTION"),
            template_id=data.template_id,
            control_type=data.control_type,
            source_type=data.source_type,
            source_reference=data.source_reference,
            source_id=data.source_id,
            product_id=data.product_id,
            lot_number=data.lot_number,
            serial_number=data.serial_number,
            quantity_to_control=data.quantity_to_control,
            unit_id=data.unit_id,
            supplier_id=data.supplier_id,
            customer_id=data.customer_id,
            control_date=data.control_date,
            start_time=datetime.now(),
            location=data.location,
            controller_id=data.controller_id or self.user_id,
            status=ControlStatus.PLANNED,
            observations=data.observations,
            created_by=self.user_id,
        )
        self.db.add(control)
        self.db.flush()

        # Créer les lignes depuis le template si spécifié
        if data.template_id:
            template = self.db.query(QualityControlTemplate).options(
                joinedload(QualityControlTemplate.items)
            ).filter(
                QualityControlTemplate.id == data.template_id,
                QualityControlTemplate.tenant_id == self.tenant_id
            ).first()

            if template and template.items:
                for item in template.items:
                    line = QualityControlLine(
                        tenant_id=self.tenant_id,
                        control_id=control.id,
                        template_item_id=item.id,
                        sequence=item.sequence,
                        characteristic=item.characteristic,
                        nominal_value=item.nominal_value,
                        tolerance_min=item.tolerance_min,
                        tolerance_max=item.tolerance_max,
                        unit=item.unit,
                        result=ControlResult.PENDING,
                        created_by=self.user_id,
                    )
                    self.db.add(line)

        # Ou créer les lignes passées en paramètre
        elif data.lines:
            for line_data in data.lines:
                line = QualityControlLine(
                    tenant_id=self.tenant_id,
                    control_id=control.id,
                    template_item_id=line_data.template_item_id,
                    sequence=line_data.sequence,
                    characteristic=line_data.characteristic,
                    nominal_value=line_data.nominal_value,
                    tolerance_min=line_data.tolerance_min,
                    tolerance_max=line_data.tolerance_max,
                    unit=line_data.unit,
                    measured_value=line_data.measured_value,
                    measured_text=line_data.measured_text,
                    measured_boolean=line_data.measured_boolean,
                    result=line_data.result or ControlResult.PENDING,
                    equipment_code=line_data.equipment_code,
                    comments=line_data.comments,
                    created_by=self.user_id,
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(control)
        return control

    def get(self, control_id: int) -> Optional[QualityControl]:
        """Récupère un contrôle par ID."""
        return self._get_by_id(control_id, options=[
            joinedload(QualityControl.lines)
        ])

    def get_by_number(self, control_number: str) -> Optional[QualityControl]:
        """Récupère un contrôle par numéro."""
        return self._base_query().options(
            joinedload(QualityControl.lines)
        ).filter(QualityControl.control_number == control_number).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        control_type: Optional[ControlType] = None,
        status: Optional[ControlStatus] = None,
        result: Optional[ControlResult] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[QualityControl], int]:
        """Liste les contrôles qualité."""
        query = self._base_query()

        if control_type:
            query = query.filter(QualityControl.control_type == control_type)
        if status:
            query = query.filter(QualityControl.status == status)
        if result:
            query = query.filter(QualityControl.result == result)
        if date_from:
            query = query.filter(QualityControl.control_date >= date_from)
        if date_to:
            query = query.filter(QualityControl.control_date <= date_to)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityControl.control_number.ilike(search_filter),
                    QualityControl.lot_number.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(
            joinedload(QualityControl.lines)
        ).order_by(
            QualityControl.control_date.desc()
        ).offset(skip).limit(limit).all()

        return items, total

    def update(self, control_id: int, data: ControlUpdate) -> Optional[QualityControl]:
        """Met à jour un contrôle."""
        control = self.get(control_id)
        if not control:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(control, update_data)

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def start(self, control_id: int) -> Optional[QualityControl]:
        """Démarre un contrôle."""
        control = self.get(control_id)
        if not control or control.status != ControlStatus.PLANNED:
            return None

        control.status = ControlStatus.IN_PROGRESS
        control.start_time = datetime.now()
        control.controller_id = self.user_id
        self.db.commit()
        self.db.refresh(control)
        return control

    def complete(self, control_id: int) -> Optional[QualityControl]:
        """Termine un contrôle et calcule le résultat global."""
        control = self.get(control_id)
        if not control:
            return None

        control.status = ControlStatus.COMPLETED
        control.end_time = datetime.now()

        # Calculer le résultat global
        if control.lines:
            has_failed = any(line.result == ControlResult.FAILED for line in control.lines)
            all_passed = all(line.result == ControlResult.PASSED for line in control.lines)

            if has_failed:
                control.result = ControlResult.FAILED
            elif all_passed:
                control.result = ControlResult.PASSED
            else:
                control.result = ControlResult.PASSED  # Default si pas d'échec

        self.db.commit()
        self.db.refresh(control)
        return control

    def cancel(self, control_id: int, reason: str = None) -> Optional[QualityControl]:
        """Annule un contrôle."""
        control = self.get(control_id)
        if not control:
            return None

        control.status = ControlStatus.CANCELLED
        if reason:
            control.observations = f"{control.observations or ''}\n[Annulé] {reason}".strip()
        self.db.commit()
        self.db.refresh(control)
        return control

    # ========================================================================
    # LIGNES DE CONTRÔLE
    # ========================================================================

    def update_line(self, line_id: int, data: ControlLineUpdate) -> Optional[QualityControlLine]:
        """Met à jour une ligne de contrôle."""
        line = self.db.query(QualityControlLine).filter(
            QualityControlLine.id == line_id,
            QualityControlLine.tenant_id == self.tenant_id
        ).first()
        if not line:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(line, field):
                setattr(line, field, value)

        # Auto-calculer le résultat si valeur mesurée
        if line.measured_value is not None and line.nominal_value is not None:
            in_tolerance = True
            if line.tolerance_min is not None and line.measured_value < line.tolerance_min:
                in_tolerance = False
            if line.tolerance_max is not None and line.measured_value > line.tolerance_max:
                in_tolerance = False
            line.result = ControlResult.PASSED if in_tolerance else ControlResult.FAILED

        self.db.commit()
        self.db.refresh(line)
        return line

    def validate_line(self, line_id: int, result: ControlResult) -> Optional[QualityControlLine]:
        """Valide manuellement une ligne de contrôle."""
        line = self.db.query(QualityControlLine).filter(
            QualityControlLine.id == line_id,
            QualityControlLine.tenant_id == self.tenant_id
        ).first()
        if not line:
            return None

        line.result = result
        line.validated_by = self.user_id
        line.validated_at = datetime.now()
        self.db.commit()
        self.db.refresh(line)
        return line
