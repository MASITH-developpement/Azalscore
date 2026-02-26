"""
AZALS MODULE M7 - Indicator Service
====================================

Gestion des indicateurs qualité.
"""
from __future__ import annotations


import logging
from datetime import date
from typing import Optional, Tuple, List

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.modules.quality.models import (
    QualityIndicator,
    IndicatorMeasurement,
)
from app.modules.quality.schemas import (
    IndicatorCreate,
    IndicatorUpdate,
    IndicatorMeasurementCreate,
)
from .base import BaseQualityService

logger = logging.getLogger(__name__)


class IndicatorService(BaseQualityService[QualityIndicator]):
    """Service de gestion des indicateurs qualité."""

    model = QualityIndicator

    def create(self, data: IndicatorCreate) -> QualityIndicator:
        """Crée un indicateur qualité."""
        indicator = QualityIndicator(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            category=data.category,
            formula=data.formula,
            unit=data.unit,
            target_value=data.target_value,
            target_min=data.target_min,
            target_max=data.target_max,
            warning_threshold=data.warning_threshold,
            critical_threshold=data.critical_threshold,
            direction=data.direction,
            measurement_frequency=data.measurement_frequency,
            data_source=data.data_source,
            owner_id=data.owner_id,
            is_active=True,
            created_by=self.user_id,
        )
        self.db.add(indicator)
        self.db.commit()
        self.db.refresh(indicator)
        return indicator

    def get(self, indicator_id: int) -> Optional[QualityIndicator]:
        """Récupère un indicateur par ID."""
        return self._get_by_id(indicator_id, options=[
            joinedload(QualityIndicator.measurements)
        ])

    def get_by_code(self, code: str) -> Optional[QualityIndicator]:
        """Récupère un indicateur par code."""
        return self._base_query().options(
            joinedload(QualityIndicator.measurements)
        ).filter(QualityIndicator.code == code).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        active_only: bool = True,
        search: Optional[str] = None,
    ) -> Tuple[List[QualityIndicator], int]:
        """Liste les indicateurs."""
        query = self._base_query()

        if category:
            query = query.filter(QualityIndicator.category == category)
        if active_only:
            query = query.filter(QualityIndicator.is_active == True)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityIndicator.code.ilike(search_filter),
                    QualityIndicator.name.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.order_by(QualityIndicator.code).offset(skip).limit(limit).all()

        return items, total

    def update(self, indicator_id: int, data: IndicatorUpdate) -> Optional[QualityIndicator]:
        """Met à jour un indicateur."""
        indicator = self.get(indicator_id)
        if not indicator:
            return None

        update_data = data.model_dump(exclude_unset=True)
        return self._update(indicator, update_data)

    def deactivate(self, indicator_id: int) -> Optional[QualityIndicator]:
        """Désactive un indicateur."""
        indicator = self.get(indicator_id)
        if not indicator:
            return None

        indicator.is_active = False
        self.db.commit()
        self.db.refresh(indicator)
        return indicator

    # ========================================================================
    # MESURES
    # ========================================================================

    def add_measurement(self, indicator_id: int, data: IndicatorMeasurementCreate) -> Optional[IndicatorMeasurement]:
        """Ajoute une mesure à un indicateur."""
        indicator = self.get(indicator_id)
        if not indicator:
            return None

        # Calculer les métriques
        target_value = indicator.target_value
        deviation = None
        achievement_rate = None
        status = None

        if target_value:
            deviation = data.value - target_value
            if indicator.direction == "HIGHER_BETTER":
                achievement_rate = (data.value / target_value * 100) if target_value != 0 else None
            elif indicator.direction == "LOWER_BETTER":
                achievement_rate = (target_value / data.value * 100) if data.value != 0 else None
            else:
                achievement_rate = 100 - abs(deviation / target_value * 100) if target_value != 0 else None

        # Déterminer le statut
        if indicator.critical_threshold is not None:
            if indicator.direction == "HIGHER_BETTER":
                if data.value <= indicator.critical_threshold:
                    status = "CRITICAL"
                elif indicator.warning_threshold and data.value <= indicator.warning_threshold:
                    status = "WARNING"
                else:
                    status = "ON_TARGET"
            else:
                if data.value >= indicator.critical_threshold:
                    status = "CRITICAL"
                elif indicator.warning_threshold and data.value >= indicator.warning_threshold:
                    status = "WARNING"
                else:
                    status = "ON_TARGET"

        measurement = IndicatorMeasurement(
            tenant_id=self.tenant_id,
            indicator_id=indicator_id,
            measurement_date=data.measurement_date,
            period_start=data.period_start,
            period_end=data.period_end,
            value=data.value,
            numerator=data.numerator,
            denominator=data.denominator,
            target_value=target_value,
            deviation=deviation,
            achievement_rate=achievement_rate,
            status=status,
            comments=data.comments,
            action_required=status in ["WARNING", "CRITICAL"],
            source=data.source,
            created_by=self.user_id,
        )
        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    def get_measurements(
        self,
        indicator_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100,
    ) -> List[IndicatorMeasurement]:
        """Récupère les mesures d'un indicateur."""
        query = self.db.query(IndicatorMeasurement).filter(
            IndicatorMeasurement.indicator_id == indicator_id,
            IndicatorMeasurement.tenant_id == self.tenant_id
        )

        if date_from:
            query = query.filter(IndicatorMeasurement.measurement_date >= date_from)
        if date_to:
            query = query.filter(IndicatorMeasurement.measurement_date <= date_to)

        return query.order_by(
            IndicatorMeasurement.measurement_date.desc()
        ).limit(limit).all()

    def get_latest_measurement(self, indicator_id: int) -> Optional[IndicatorMeasurement]:
        """Récupère la dernière mesure d'un indicateur."""
        return self.db.query(IndicatorMeasurement).filter(
            IndicatorMeasurement.indicator_id == indicator_id,
            IndicatorMeasurement.tenant_id == self.tenant_id
        ).order_by(
            IndicatorMeasurement.measurement_date.desc()
        ).first()

    def get_indicators_needing_measurement(self) -> List[QualityIndicator]:
        """Récupère les indicateurs qui nécessitent une nouvelle mesure."""
        from datetime import timedelta

        indicators = self._base_query().filter(
            QualityIndicator.is_active == True
        ).all()

        result = []
        for indicator in indicators:
            last = self.get_latest_measurement(indicator.id)
            if not last:
                result.append(indicator)
                continue

            # Calculer si mesure nécessaire selon fréquence
            freq = indicator.measurement_frequency or "MONTHLY"
            days_map = {
                "DAILY": 1,
                "WEEKLY": 7,
                "MONTHLY": 30,
                "QUARTERLY": 90,
                "YEARLY": 365,
            }
            days = days_map.get(freq, 30)

            if (date.today() - last.measurement_date).days >= days:
                result.append(indicator)

        return result
