"""
Repositories Risk Management - GAP-075
=======================================
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from .models import (
    RiskMatrix, Risk, Control, MitigationAction,
    RiskIndicator, RiskAssessment, RiskIncident,
    RiskStatus, ActionStatus, IndicatorStatus, IncidentStatus
)


class RiskMatrixRepository:
    """Repository pour les matrices de risques."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(RiskMatrix).filter(
            RiskMatrix.tenant_id == self.tenant_id,
            RiskMatrix.is_deleted == False
        )

    def get_by_id(self, matrix_id: UUID) -> Optional[RiskMatrix]:
        return self._base_query().filter(RiskMatrix.id == matrix_id).first()

    def get_by_code(self, code: str) -> Optional[RiskMatrix]:
        return self._base_query().filter(RiskMatrix.code == code).first()

    def get_default(self) -> Optional[RiskMatrix]:
        return self._base_query().filter(
            RiskMatrix.is_default == True,
            RiskMatrix.is_active == True
        ).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[RiskMatrix], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    RiskMatrix.name.ilike(pattern),
                    RiskMatrix.code.ilike(pattern)
                )
            )

        if is_active is not None:
            query = query.filter(RiskMatrix.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(RiskMatrix.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, matrix: RiskMatrix) -> RiskMatrix:
        matrix.tenant_id = self.tenant_id
        self.db.add(matrix)
        self.db.flush()
        return matrix

    def update(self, matrix: RiskMatrix) -> RiskMatrix:
        matrix.version += 1
        self.db.flush()
        return matrix

    def delete(self, matrix: RiskMatrix) -> None:
        matrix.is_deleted = True
        matrix.deleted_at = datetime.utcnow()
        self.db.flush()

    def count_risks_using_matrix(self, matrix_id: UUID) -> int:
        return self.db.query(Risk).filter(
            Risk.tenant_id == self.tenant_id,
            Risk.matrix_id == matrix_id,
            Risk.is_deleted == False
        ).count()


class RiskRepository:
    """Repository pour les risques."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Risk).filter(
            Risk.tenant_id == self.tenant_id,
            Risk.is_deleted == False
        )

    def get_by_id(self, risk_id: UUID) -> Optional[Risk]:
        return self._base_query().filter(Risk.id == risk_id).first()

    def get_by_code(self, code: str) -> Optional[Risk]:
        return self._base_query().filter(Risk.code == code).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        level: Optional[str] = None,
        owner_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        include_closed: bool = False
    ) -> Tuple[List[Risk], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Risk.title.ilike(pattern),
                    Risk.code.ilike(pattern),
                    Risk.description.ilike(pattern)
                )
            )

        if category:
            query = query.filter(Risk.category == category)

        if status:
            query = query.filter(Risk.status == status)
        elif not include_closed:
            query = query.filter(Risk.status != RiskStatus.CLOSED)

        if level:
            query = query.filter(Risk.inherent_level == level)

        if owner_id:
            query = query.filter(Risk.owner_id == owner_id)

        if department_id:
            query = query.filter(Risk.department_id == department_id)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(
            Risk.inherent_score.desc(),
            Risk.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total, pages

    def create(self, risk: Risk) -> Risk:
        risk.tenant_id = self.tenant_id
        self.db.add(risk)
        self.db.flush()
        return risk

    def update(self, risk: Risk) -> Risk:
        risk.version += 1
        risk.updated_at = datetime.utcnow()
        self.db.flush()
        return risk

    def delete(self, risk: Risk) -> None:
        risk.is_deleted = True
        risk.deleted_at = datetime.utcnow()
        self.db.flush()

    def restore(self, risk: Risk) -> Risk:
        risk.is_deleted = False
        risk.deleted_at = None
        risk.deleted_by = None
        self.db.flush()
        return risk

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(Risk.code)).filter(
            Risk.tenant_id == self.tenant_id,
            Risk.code.like("RSK-%")
        ).scalar()

        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"RSK-{num:04d}"

    def count_by_level(self) -> dict:
        result = self.db.query(
            Risk.inherent_level,
            func.count(Risk.id)
        ).filter(
            Risk.tenant_id == self.tenant_id,
            Risk.is_deleted == False,
            Risk.status != RiskStatus.CLOSED
        ).group_by(Risk.inherent_level).all()

        return {str(level): count for level, count in result}

    def count_by_category(self) -> dict:
        result = self.db.query(
            Risk.category,
            func.count(Risk.id)
        ).filter(
            Risk.tenant_id == self.tenant_id,
            Risk.is_deleted == False,
            Risk.status != RiskStatus.CLOSED
        ).group_by(Risk.category).all()

        return {str(cat): count for cat, count in result}

    def count_by_status(self) -> dict:
        result = self.db.query(
            Risk.status,
            func.count(Risk.id)
        ).filter(
            Risk.tenant_id == self.tenant_id,
            Risk.is_deleted == False
        ).group_by(Risk.status).all()

        return {str(status): count for status, count in result}

    def get_risks_for_review(self, before_date: date) -> List[Risk]:
        return self._base_query().filter(
            Risk.next_review_date <= before_date,
            Risk.status != RiskStatus.CLOSED
        ).order_by(Risk.next_review_date).all()

    def get_heatmap_data(self) -> List[dict]:
        result = self.db.query(
            Risk.inherent_probability,
            Risk.inherent_impact,
            func.count(Risk.id),
            func.array_agg(Risk.id)
        ).filter(
            Risk.tenant_id == self.tenant_id,
            Risk.is_deleted == False,
            Risk.status != RiskStatus.CLOSED
        ).group_by(
            Risk.inherent_probability,
            Risk.inherent_impact
        ).all()

        return [
            {
                "probability": str(prob),
                "impact": str(imp),
                "count": count,
                "risk_ids": [str(rid) for rid in risk_ids]
            }
            for prob, imp, count, risk_ids in result
        ]


class ControlRepository:
    """Repository pour les contrôles."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Control).filter(
            Control.tenant_id == self.tenant_id,
            Control.is_deleted == False
        )

    def get_by_id(self, control_id: UUID) -> Optional[Control]:
        return self._base_query().filter(Control.id == control_id).first()

    def get_by_code(self, code: str) -> Optional[Control]:
        return self._base_query().filter(Control.code == code).first()

    def list_by_risk(
        self,
        risk_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[Control]:
        query = self._base_query().filter(Control.risk_id == risk_id)

        if is_active is not None:
            query = query.filter(Control.is_active == is_active)

        return query.order_by(Control.name).all()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        control_type: Optional[str] = None,
        effectiveness: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Control], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Control.name.ilike(pattern),
                    Control.code.ilike(pattern)
                )
            )

        if control_type:
            query = query.filter(Control.control_type == control_type)

        if effectiveness:
            query = query.filter(Control.effectiveness == effectiveness)

        if is_active is not None:
            query = query.filter(Control.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Control.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, control: Control) -> Control:
        control.tenant_id = self.tenant_id
        self.db.add(control)
        self.db.flush()
        return control

    def update(self, control: Control) -> Control:
        control.version += 1
        control.updated_at = datetime.utcnow()
        self.db.flush()
        return control

    def delete(self, control: Control) -> None:
        control.is_deleted = True
        control.deleted_at = datetime.utcnow()
        self.db.flush()

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(Control.code)).filter(
            Control.tenant_id == self.tenant_id,
            Control.code.like("CTL-%")
        ).scalar()

        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"CTL-{num:04d}"


class MitigationActionRepository:
    """Repository pour les actions de mitigation."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(MitigationAction).filter(
            MitigationAction.tenant_id == self.tenant_id,
            MitigationAction.is_deleted == False
        )

    def get_by_id(self, action_id: UUID) -> Optional[MitigationAction]:
        return self._base_query().filter(MitigationAction.id == action_id).first()

    def get_by_code(self, code: str) -> Optional[MitigationAction]:
        return self._base_query().filter(MitigationAction.code == code).first()

    def list_by_risk(
        self,
        risk_id: UUID,
        status: Optional[str] = None
    ) -> List[MitigationAction]:
        query = self._base_query().filter(MitigationAction.risk_id == risk_id)

        if status:
            query = query.filter(MitigationAction.status == status)

        return query.order_by(
            MitigationAction.priority.desc(),
            MitigationAction.planned_end
        ).all()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[UUID] = None,
        risk_id: Optional[UUID] = None
    ) -> Tuple[List[MitigationAction], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    MitigationAction.title.ilike(pattern),
                    MitigationAction.code.ilike(pattern)
                )
            )

        if status:
            query = query.filter(MitigationAction.status == status)

        if assignee_id:
            query = query.filter(MitigationAction.assignee_id == assignee_id)

        if risk_id:
            query = query.filter(MitigationAction.risk_id == risk_id)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(
            MitigationAction.priority.desc(),
            MitigationAction.planned_end
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total, pages

    def create(self, action: MitigationAction) -> MitigationAction:
        action.tenant_id = self.tenant_id
        self.db.add(action)
        self.db.flush()
        return action

    def update(self, action: MitigationAction) -> MitigationAction:
        action.version += 1
        action.updated_at = datetime.utcnow()
        self.db.flush()
        return action

    def delete(self, action: MitigationAction) -> None:
        action.is_deleted = True
        action.deleted_at = datetime.utcnow()
        self.db.flush()

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(MitigationAction.code)).filter(
            MitigationAction.tenant_id == self.tenant_id,
            MitigationAction.code.like("ACT-%")
        ).scalar()

        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"ACT-{num:04d}"

    def get_overdue(self) -> List[MitigationAction]:
        today = date.today()
        return self._base_query().filter(
            MitigationAction.planned_end < today,
            MitigationAction.status.notin_([
                ActionStatus.COMPLETED,
                ActionStatus.CANCELLED
            ])
        ).order_by(MitigationAction.planned_end).all()

    def count_by_status(self) -> dict:
        result = self.db.query(
            MitigationAction.status,
            func.count(MitigationAction.id)
        ).filter(
            MitigationAction.tenant_id == self.tenant_id,
            MitigationAction.is_deleted == False
        ).group_by(MitigationAction.status).all()

        return {str(status): count for status, count in result}

    def count_active_for_risk(self, risk_id: UUID) -> int:
        return self._base_query().filter(
            MitigationAction.risk_id == risk_id,
            MitigationAction.status.notin_([
                ActionStatus.COMPLETED,
                ActionStatus.CANCELLED
            ])
        ).count()


class RiskIndicatorRepository:
    """Repository pour les indicateurs de risque."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(RiskIndicator).filter(
            RiskIndicator.tenant_id == self.tenant_id,
            RiskIndicator.is_deleted == False
        )

    def get_by_id(self, indicator_id: UUID) -> Optional[RiskIndicator]:
        return self._base_query().filter(RiskIndicator.id == indicator_id).first()

    def get_by_code(self, code: str) -> Optional[RiskIndicator]:
        return self._base_query().filter(RiskIndicator.code == code).first()

    def list_by_risk(
        self,
        risk_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[RiskIndicator]:
        query = self._base_query().filter(RiskIndicator.risk_id == risk_id)

        if is_active is not None:
            query = query.filter(RiskIndicator.is_active == is_active)

        return query.order_by(RiskIndicator.name).all()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[RiskIndicator], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    RiskIndicator.name.ilike(pattern),
                    RiskIndicator.code.ilike(pattern)
                )
            )

        if status:
            query = query.filter(RiskIndicator.current_status == status)

        if is_active is not None:
            query = query.filter(RiskIndicator.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(RiskIndicator.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, indicator: RiskIndicator) -> RiskIndicator:
        indicator.tenant_id = self.tenant_id
        self.db.add(indicator)
        self.db.flush()
        return indicator

    def update(self, indicator: RiskIndicator) -> RiskIndicator:
        indicator.version += 1
        indicator.updated_at = datetime.utcnow()
        self.db.flush()
        return indicator

    def delete(self, indicator: RiskIndicator) -> None:
        indicator.is_deleted = True
        indicator.deleted_at = datetime.utcnow()
        self.db.flush()

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(RiskIndicator.code)).filter(
            RiskIndicator.tenant_id == self.tenant_id,
            RiskIndicator.code.like("KRI-%")
        ).scalar()

        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"KRI-{num:04d}"

    def count_by_status(self) -> dict:
        result = self.db.query(
            RiskIndicator.current_status,
            func.count(RiskIndicator.id)
        ).filter(
            RiskIndicator.tenant_id == self.tenant_id,
            RiskIndicator.is_deleted == False,
            RiskIndicator.is_active == True
        ).group_by(RiskIndicator.current_status).all()

        return {str(status): count for status, count in result}

    def get_alerts(self) -> List[RiskIndicator]:
        return self._base_query().filter(
            RiskIndicator.is_active == True,
            RiskIndicator.current_status.in_([
                IndicatorStatus.AMBER,
                IndicatorStatus.RED
            ])
        ).order_by(RiskIndicator.current_status.desc()).all()


class RiskAssessmentRepository:
    """Repository pour les évaluations de risque."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.tenant_id == self.tenant_id
        )

    def get_by_id(self, assessment_id: UUID) -> Optional[RiskAssessment]:
        return self._base_query().filter(RiskAssessment.id == assessment_id).first()

    def list_by_risk(
        self,
        risk_id: UUID,
        assessment_type: Optional[str] = None,
        is_residual: Optional[bool] = None
    ) -> List[RiskAssessment]:
        query = self._base_query().filter(RiskAssessment.risk_id == risk_id)

        if assessment_type:
            query = query.filter(RiskAssessment.assessment_type == assessment_type)

        if is_residual is not None:
            query = query.filter(RiskAssessment.is_residual == is_residual)

        return query.order_by(RiskAssessment.assessment_date.desc()).all()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        risk_id: Optional[UUID] = None,
        assessor_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Tuple[List[RiskAssessment], int, int]:
        query = self._base_query()

        if risk_id:
            query = query.filter(RiskAssessment.risk_id == risk_id)

        if assessor_id:
            query = query.filter(RiskAssessment.assessor_id == assessor_id)

        if date_from:
            query = query.filter(
                func.date(RiskAssessment.assessment_date) >= date_from
            )

        if date_to:
            query = query.filter(
                func.date(RiskAssessment.assessment_date) <= date_to
            )

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(
            RiskAssessment.assessment_date.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total, pages

    def create(self, assessment: RiskAssessment) -> RiskAssessment:
        assessment.tenant_id = self.tenant_id
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def get_latest_for_risk(
        self,
        risk_id: UUID,
        is_residual: bool = False
    ) -> Optional[RiskAssessment]:
        return self._base_query().filter(
            RiskAssessment.risk_id == risk_id,
            RiskAssessment.is_residual == is_residual
        ).order_by(RiskAssessment.assessment_date.desc()).first()


class RiskIncidentRepository:
    """Repository pour les incidents de risque."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(RiskIncident).filter(
            RiskIncident.tenant_id == self.tenant_id,
            RiskIncident.is_deleted == False
        )

    def get_by_id(self, incident_id: UUID) -> Optional[RiskIncident]:
        return self._base_query().filter(RiskIncident.id == incident_id).first()

    def get_by_code(self, code: str) -> Optional[RiskIncident]:
        return self._base_query().filter(RiskIncident.code == code).first()

    def list_by_risk(self, risk_id: UUID) -> List[RiskIncident]:
        return self._base_query().filter(
            RiskIncident.risk_id == risk_id
        ).order_by(RiskIncident.occurred_at.desc()).all()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        risk_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        impact: Optional[str] = None
    ) -> Tuple[List[RiskIncident], int, int]:
        query = self._base_query()

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    RiskIncident.title.ilike(pattern),
                    RiskIncident.code.ilike(pattern),
                    RiskIncident.description.ilike(pattern)
                )
            )

        if status:
            query = query.filter(RiskIncident.status == status)

        if risk_id:
            query = query.filter(RiskIncident.risk_id == risk_id)

        if date_from:
            query = query.filter(
                func.date(RiskIncident.occurred_at) >= date_from
            )

        if date_to:
            query = query.filter(
                func.date(RiskIncident.occurred_at) <= date_to
            )

        if impact:
            query = query.filter(RiskIncident.actual_impact == impact)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(
            RiskIncident.occurred_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total, pages

    def create(self, incident: RiskIncident) -> RiskIncident:
        incident.tenant_id = self.tenant_id
        self.db.add(incident)
        self.db.flush()
        return incident

    def update(self, incident: RiskIncident) -> RiskIncident:
        incident.version += 1
        incident.updated_at = datetime.utcnow()
        self.db.flush()
        return incident

    def delete(self, incident: RiskIncident) -> None:
        incident.is_deleted = True
        incident.deleted_at = datetime.utcnow()
        self.db.flush()

    def get_next_code(self) -> str:
        max_code = self.db.query(func.max(RiskIncident.code)).filter(
            RiskIncident.tenant_id == self.tenant_id,
            RiskIncident.code.like("INC-%")
        ).scalar()

        if max_code:
            try:
                num = int(max_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f"INC-{num:04d}"

    def count_by_status(self) -> dict:
        result = self.db.query(
            RiskIncident.status,
            func.count(RiskIncident.id)
        ).filter(
            RiskIncident.tenant_id == self.tenant_id,
            RiskIncident.is_deleted == False
        ).group_by(RiskIncident.status).all()

        return {str(status): count for status, count in result}

    def get_total_financial_loss(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Decimal:
        query = self._base_query()

        if date_from:
            query = query.filter(
                func.date(RiskIncident.occurred_at) >= date_from
            )

        if date_to:
            query = query.filter(
                func.date(RiskIncident.occurred_at) <= date_to
            )

        result = query.with_entities(
            func.sum(RiskIncident.financial_loss)
        ).scalar()

        return Decimal(str(result)) if result else Decimal("0")

    def count_for_risk(self, risk_id: UUID) -> int:
        return self._base_query().filter(
            RiskIncident.risk_id == risk_id
        ).count()
