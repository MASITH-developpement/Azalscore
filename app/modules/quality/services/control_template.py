"""
AZALS MODULE M7 - Control Template Service
==========================================

Gestion des templates de contrôle qualité.
"""

import logging
from typing import Optional, Tuple, List

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    QualityControlTemplate,
    QualityControlTemplateItem,
    ControlType,
)
from app.modules.quality.schemas import (
    ControlTemplateCreate,
    ControlTemplateUpdate,
    ControlTemplateItemCreate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class ControlTemplateService(BaseQualityService[QualityControlTemplate]):
    """Service de gestion des templates de contrôle."""

    model = QualityControlTemplate

    def create(self, data: ControlTemplateCreate) -> QualityControlTemplate:
        """Crée un template de contrôle qualité."""
        template = QualityControlTemplate(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            version=data.version,
            control_type=data.control_type,
            applies_to=data.applies_to,
            product_category_id=data.product_category_id,
            instructions=data.instructions,
            sampling_plan=data.sampling_plan,
            acceptance_criteria=data.acceptance_criteria,
            estimated_duration_minutes=data.estimated_duration_minutes,
            required_equipment=data.required_equipment,
            is_active=True,
            created_by=self.user_id,
        )
        self.db.add(template)
        self.db.flush()

        # Ajouter les items
        if data.items:
            for item_data in data.items:
                item = QualityControlTemplateItem(
                    tenant_id=self.tenant_id,
                    template_id=template.id,
                    sequence=item_data.sequence,
                    characteristic=item_data.characteristic,
                    description=item_data.description,
                    measurement_type=item_data.measurement_type,
                    unit=item_data.unit,
                    nominal_value=item_data.nominal_value,
                    tolerance_min=item_data.tolerance_min,
                    tolerance_max=item_data.tolerance_max,
                    expected_result=item_data.expected_result,
                    measurement_method=item_data.measurement_method,
                    equipment_code=item_data.equipment_code,
                    is_critical=item_data.is_critical,
                    is_mandatory=item_data.is_mandatory,
                    sampling_frequency=item_data.sampling_frequency,
                )
                self.db.add(item)

        self.db.commit()
        self.db.refresh(template)
        return template

    def get(self, template_id: int) -> Optional[QualityControlTemplate]:
        """Récupère un template par ID."""
        return self._get_by_id(template_id, options=[
            joinedload(QualityControlTemplate.items)
        ])

    def get_by_code(self, code: str) -> Optional[QualityControlTemplate]:
        """Récupère un template par code."""
        return self._base_query().options(
            joinedload(QualityControlTemplate.items)
        ).filter(QualityControlTemplate.code == code).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        control_type: Optional[ControlType] = None,
        active_only: bool = True,
        search: Optional[str] = None,
    ) -> Tuple[List[QualityControlTemplate], int]:
        """Liste les templates de contrôle."""
        query = self._base_query()

        if control_type:
            query = query.filter(QualityControlTemplate.control_type == control_type)
        if active_only:
            query = query.filter(QualityControlTemplate.is_active == True)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityControlTemplate.code.ilike(search_filter),
                    QualityControlTemplate.name.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(
            joinedload(QualityControlTemplate.items)
        ).order_by(QualityControlTemplate.code).offset(skip).limit(limit).all()

        return items, total

    def update(self, template_id: int, data: ControlTemplateUpdate) -> Optional[QualityControlTemplate]:
        """Met à jour un template."""
        template = self.get(template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(template, update_data)

    def add_item(self, template_id: int, data: ControlTemplateItemCreate) -> Optional[QualityControlTemplateItem]:
        """Ajoute un item à un template."""
        template = self.get(template_id)
        if not template:
            return None

        item = QualityControlTemplateItem(
            tenant_id=self.tenant_id,
            template_id=template_id,
            sequence=data.sequence,
            characteristic=data.characteristic,
            description=data.description,
            measurement_type=data.measurement_type,
            unit=data.unit,
            nominal_value=data.nominal_value,
            tolerance_min=data.tolerance_min,
            tolerance_max=data.tolerance_max,
            expected_result=data.expected_result,
            measurement_method=data.measurement_method,
            equipment_code=data.equipment_code,
            is_critical=data.is_critical,
            is_mandatory=data.is_mandatory,
            sampling_frequency=data.sampling_frequency,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_item(self, item_id: int) -> bool:
        """Supprime un item d'un template."""
        item = self.db.query(QualityControlTemplateItem).filter(
            QualityControlTemplateItem.id == item_id,
            QualityControlTemplateItem.tenant_id == self.tenant_id
        ).first()
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()
        return True

    def deactivate(self, template_id: int) -> Optional[QualityControlTemplate]:
        """Désactive un template."""
        template = self.get(template_id)
        if not template:
            return None

        template.is_active = False
        self.db.commit()
        self.db.refresh(template)
        return template
