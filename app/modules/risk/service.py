"""
Service Risk Management - GAP-075
==================================
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    RiskMatrix, Risk, Control, MitigationAction,
    RiskIndicator, RiskAssessment, RiskIncident,
    RiskCategory, RiskStatus, Probability, Impact, RiskLevel,
    MitigationStrategy, ActionStatus, ControlType, ControlEffectiveness,
    IndicatorStatus, IncidentStatus
)
from .repository import (
    RiskMatrixRepository, RiskRepository, ControlRepository,
    MitigationActionRepository, RiskIndicatorRepository,
    RiskAssessmentRepository, RiskIncidentRepository
)
from .exceptions import (
    RiskMatrixNotFoundError, RiskMatrixDuplicateError, RiskMatrixInUseError,
    DefaultMatrixRequiredError,
    RiskNotFoundError, RiskDuplicateError, RiskStateError, RiskClosedError,
    RiskHasActiveActionsError, RiskCircularReferenceError,
    ControlNotFoundError, ControlDuplicateError,
    ActionNotFoundError, ActionDuplicateError, ActionStateError,
    ActionCompletedError, ActionCancelledError,
    IndicatorNotFoundError, IndicatorDuplicateError, IndicatorThresholdError,
    AssessmentNotFoundError, AssessmentAlreadyValidatedError,
    IncidentNotFoundError, IncidentDuplicateError, IncidentStateError,
    IncidentClosedError, IncidentNotResolvedError
)
from .schemas import (
    RiskMatrixCreate, RiskMatrixUpdate,
    RiskCreate, RiskUpdate,
    ControlCreate, ControlUpdate, ControlExecutionRecord,
    ActionCreate, ActionUpdate, ActionProgressUpdate,
    IndicatorCreate, IndicatorUpdate, IndicatorValueRecord,
    AssessmentCreate, AssessmentValidation,
    IncidentCreate, IncidentUpdate, IncidentResolution,
    RiskReportResponse
)


class RiskService:
    """Service de gestion des risques."""

    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        self.matrix_repo = RiskMatrixRepository(db, tenant_id)
        self.risk_repo = RiskRepository(db, tenant_id)
        self.control_repo = ControlRepository(db, tenant_id)
        self.action_repo = MitigationActionRepository(db, tenant_id)
        self.indicator_repo = RiskIndicatorRepository(db, tenant_id)
        self.assessment_repo = RiskAssessmentRepository(db, tenant_id)
        self.incident_repo = RiskIncidentRepository(db, tenant_id)

    # ============== Risk Matrix ==============

    def list_matrices(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[RiskMatrix], int, int]:
        return self.matrix_repo.list(page, page_size, search, is_active)

    def get_matrix(self, matrix_id: UUID) -> RiskMatrix:
        matrix = self.matrix_repo.get_by_id(matrix_id)
        if not matrix:
            raise RiskMatrixNotFoundError(str(matrix_id))
        return matrix

    def create_matrix(self, data: RiskMatrixCreate) -> RiskMatrix:
        if self.matrix_repo.get_by_code(data.code):
            raise RiskMatrixDuplicateError(data.code)

        matrix = RiskMatrix(
            name=data.name,
            code=data.code,
            description=data.description,
            probability_scale=data.probability_scale,
            impact_scale=data.impact_scale,
            low_threshold=data.low_threshold,
            medium_threshold=data.medium_threshold,
            high_threshold=data.high_threshold,
            probability_labels=data.probability_labels,
            impact_labels=data.impact_labels,
            color_low=data.color_low,
            color_medium=data.color_medium,
            color_high=data.color_high,
            color_critical=data.color_critical,
            is_default=data.is_default,
            is_active=data.is_active,
            created_by=self.user_id
        )

        if data.is_default:
            self._clear_default_matrix()

        return self.matrix_repo.create(matrix)

    def update_matrix(self, matrix_id: UUID, data: RiskMatrixUpdate) -> RiskMatrix:
        matrix = self.get_matrix(matrix_id)

        if data.code and data.code != matrix.code:
            if self.matrix_repo.get_by_code(data.code):
                raise RiskMatrixDuplicateError(data.code)

        if data.is_default and not matrix.is_default:
            self._clear_default_matrix()

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(matrix, field, value)

        matrix.updated_by = self.user_id
        return self.matrix_repo.update(matrix)

    def delete_matrix(self, matrix_id: UUID) -> None:
        matrix = self.get_matrix(matrix_id)

        risk_count = self.matrix_repo.count_risks_using_matrix(matrix_id)
        if risk_count > 0:
            raise RiskMatrixInUseError(str(matrix_id), risk_count)

        if matrix.is_default:
            raise DefaultMatrixRequiredError()

        matrix.deleted_by = self.user_id
        self.matrix_repo.delete(matrix)

    def _clear_default_matrix(self) -> None:
        current_default = self.matrix_repo.get_default()
        if current_default:
            current_default.is_default = False
            self.matrix_repo.update(current_default)

    # ============== Risk ==============

    def list_risks(
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
        return self.risk_repo.list(
            page, page_size, search, category, status,
            level, owner_id, department_id, include_closed
        )

    def get_risk(self, risk_id: UUID) -> Risk:
        risk = self.risk_repo.get_by_id(risk_id)
        if not risk:
            raise RiskNotFoundError(str(risk_id))
        return risk

    def create_risk(self, data: RiskCreate) -> Risk:
        code = data.code or self.risk_repo.get_next_code()

        if self.risk_repo.get_by_code(code):
            raise RiskDuplicateError(code)

        if data.parent_risk_id:
            parent = self.risk_repo.get_by_id(data.parent_risk_id)
            if not parent:
                raise RiskNotFoundError(str(data.parent_risk_id))

        probability = Probability(data.inherent_probability)
        impact = Impact(data.inherent_impact)
        score = self._calculate_score(probability, impact)
        level = self._determine_level(score, data.matrix_id)

        risk = Risk(
            code=code,
            title=data.title,
            description=data.description,
            category=RiskCategory(data.category),
            matrix_id=data.matrix_id,
            inherent_probability=probability,
            inherent_impact=impact,
            inherent_score=score,
            inherent_level=level,
            financial_impact_min=data.financial_impact_min,
            financial_impact_max=data.financial_impact_max,
            financial_impact_expected=data.financial_impact_expected,
            owner_id=data.owner_id,
            reviewer_id=data.reviewer_id,
            department_id=data.department_id,
            next_review_date=data.next_review_date,
            causes=data.causes,
            consequences=data.consequences,
            affected_objectives=data.affected_objectives,
            affected_processes=data.affected_processes,
            related_risk_ids=data.related_risk_ids,
            parent_risk_id=data.parent_risk_id,
            mitigation_strategy=MitigationStrategy(data.mitigation_strategy),
            tags=data.tags,
            created_by=self.user_id
        )

        if data.target_probability and data.target_impact:
            risk.target_probability = Probability(data.target_probability)
            risk.target_impact = Impact(data.target_impact)
            target_score = self._calculate_score(
                risk.target_probability, risk.target_impact
            )
            risk.target_level = self._determine_level(target_score, data.matrix_id)

        risk = self.risk_repo.create(risk)

        self._create_initial_assessment(risk)

        return risk

    def update_risk(self, risk_id: UUID, data: RiskUpdate) -> Risk:
        risk = self.get_risk(risk_id)

        if risk.status == RiskStatus.CLOSED:
            raise RiskClosedError(str(risk_id))

        if data.parent_risk_id:
            if data.parent_risk_id == risk_id:
                raise RiskCircularReferenceError(str(risk_id), str(data.parent_risk_id))
            parent = self.risk_repo.get_by_id(data.parent_risk_id)
            if not parent:
                raise RiskNotFoundError(str(data.parent_risk_id))

        for field, value in data.model_dump(exclude_unset=True).items():
            if field in ("inherent_probability", "inherent_impact"):
                continue
            if field == "category" and value:
                value = RiskCategory(value)
            elif field == "mitigation_strategy" and value:
                value = MitigationStrategy(value)
            elif field in ("target_probability", "residual_probability") and value:
                value = Probability(value)
            elif field in ("target_impact", "residual_impact") and value:
                value = Impact(value)
            setattr(risk, field, value)

        if data.inherent_probability or data.inherent_impact:
            prob = Probability(data.inherent_probability) if data.inherent_probability else risk.inherent_probability
            imp = Impact(data.inherent_impact) if data.inherent_impact else risk.inherent_impact
            risk.inherent_probability = prob
            risk.inherent_impact = imp
            risk.inherent_score = self._calculate_score(prob, imp)
            risk.inherent_level = self._determine_level(risk.inherent_score, risk.matrix_id)

        if data.target_probability and data.target_impact:
            risk.target_probability = Probability(data.target_probability)
            risk.target_impact = Impact(data.target_impact)
            target_score = self._calculate_score(
                risk.target_probability, risk.target_impact
            )
            risk.target_level = self._determine_level(target_score, risk.matrix_id)

        risk.updated_by = self.user_id
        return self.risk_repo.update(risk)

    def change_risk_status(self, risk_id: UUID, new_status: str) -> Risk:
        risk = self.get_risk(risk_id)
        target_status = RiskStatus(new_status)

        allowed = RiskStatus.allowed_transitions().get(risk.status, [])
        if target_status not in allowed:
            raise RiskStateError(risk.status.value, target_status.value)

        if target_status == RiskStatus.CLOSED:
            active_actions = self.action_repo.count_active_for_risk(risk_id)
            if active_actions > 0:
                raise RiskHasActiveActionsError(str(risk_id), active_actions)
            risk.closed_at = datetime.utcnow()

        risk.status = target_status
        risk.updated_by = self.user_id
        return self.risk_repo.update(risk)

    def close_risk(self, risk_id: UUID, reason: str) -> Risk:
        risk = self.get_risk(risk_id)

        active_actions = self.action_repo.count_active_for_risk(risk_id)
        if active_actions > 0:
            raise RiskHasActiveActionsError(str(risk_id), active_actions)

        risk.status = RiskStatus.CLOSED
        risk.closed_at = datetime.utcnow()
        risk.extra_data["close_reason"] = reason
        risk.updated_by = self.user_id
        return self.risk_repo.update(risk)

    def delete_risk(self, risk_id: UUID) -> None:
        risk = self.get_risk(risk_id)
        risk.deleted_by = self.user_id
        self.risk_repo.delete(risk)

    def restore_risk(self, risk_id: UUID) -> Risk:
        risk = self.db.query(Risk).filter(
            Risk.id == risk_id,
            Risk.tenant_id == self.tenant_id,
            Risk.is_deleted == True
        ).first()

        if not risk:
            raise RiskNotFoundError(str(risk_id))

        return self.risk_repo.restore(risk)

    # ============== Assessment ==============

    def assess_risk(
        self,
        risk_id: UUID,
        data: AssessmentCreate
    ) -> RiskAssessment:
        risk = self.get_risk(risk_id)

        if risk.status == RiskStatus.CLOSED:
            raise RiskClosedError(str(risk_id))

        probability = Probability(data.probability)
        impact = Impact(data.impact)
        score = self._calculate_score(probability, impact)
        level = self._determine_level(score, risk.matrix_id)

        assessment = RiskAssessment(
            risk_id=risk_id,
            assessor_id=self.user_id,
            probability=probability,
            impact=impact,
            score=score,
            level=level,
            assessment_type=data.assessment_type,
            is_residual=data.is_residual,
            trigger_event=data.trigger_event,
            rationale=data.rationale,
            supporting_evidence=data.supporting_evidence,
            controls_evaluated=data.controls_evaluated,
            control_effectiveness_summary=data.control_effectiveness_summary,
            created_by=self.user_id
        )

        assessment = self.assessment_repo.create(assessment)

        if data.is_residual:
            risk.residual_probability = probability
            risk.residual_impact = impact
            risk.residual_score = score
            risk.residual_level = level
        else:
            risk.inherent_probability = probability
            risk.inherent_impact = impact
            risk.inherent_score = score
            risk.inherent_level = level

        risk.status = RiskStatus.ASSESSED
        risk.last_assessed_at = datetime.utcnow()
        risk.updated_by = self.user_id
        self.risk_repo.update(risk)

        return assessment

    def validate_assessment(
        self,
        assessment_id: UUID,
        data: AssessmentValidation
    ) -> RiskAssessment:
        assessment = self.assessment_repo.get_by_id(assessment_id)
        if not assessment:
            raise AssessmentNotFoundError(str(assessment_id))

        if assessment.is_validated:
            raise AssessmentAlreadyValidatedError(str(assessment_id))

        assessment.is_validated = True
        assessment.validated_by = self.user_id
        assessment.validated_at = datetime.utcnow()

        self.db.flush()
        return assessment

    def list_assessments(
        self,
        page: int = 1,
        page_size: int = 20,
        risk_id: Optional[UUID] = None,
        assessor_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Tuple[List[RiskAssessment], int, int]:
        return self.assessment_repo.list(
            page, page_size, risk_id, assessor_id, date_from, date_to
        )

    def _create_initial_assessment(self, risk: Risk) -> RiskAssessment:
        assessment = RiskAssessment(
            risk_id=risk.id,
            assessor_id=self.user_id,
            probability=risk.inherent_probability,
            impact=risk.inherent_impact,
            score=risk.inherent_score,
            level=risk.inherent_level,
            assessment_type="initial",
            rationale="Évaluation initiale à la création du risque",
            created_by=self.user_id
        )
        return self.assessment_repo.create(assessment)

    # ============== Control ==============

    def list_controls(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        control_type: Optional[str] = None,
        effectiveness: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Control], int, int]:
        return self.control_repo.list(
            page, page_size, search, control_type, effectiveness, is_active
        )

    def list_controls_by_risk(
        self,
        risk_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[Control]:
        self.get_risk(risk_id)
        return self.control_repo.list_by_risk(risk_id, is_active)

    def get_control(self, control_id: UUID) -> Control:
        control = self.control_repo.get_by_id(control_id)
        if not control:
            raise ControlNotFoundError(str(control_id))
        return control

    def create_control(self, data: ControlCreate) -> Control:
        self.get_risk(data.risk_id)

        code = data.code or self.control_repo.get_next_code()

        if self.control_repo.get_by_code(code):
            raise ControlDuplicateError(code)

        control = Control(
            risk_id=data.risk_id,
            code=code,
            name=data.name,
            description=data.description,
            control_type=ControlType(data.control_type),
            effectiveness=ControlEffectiveness(data.effectiveness),
            cost=data.cost,
            owner_id=data.owner_id,
            operator_id=data.operator_id,
            frequency=data.frequency,
            procedure=data.procedure,
            evidence_required=data.evidence_required,
            evidence_links=data.evidence_links,
            is_automated=data.is_automated,
            is_active=data.is_active,
            created_by=self.user_id
        )

        control = self.control_repo.create(control)

        risk = self.get_risk(data.risk_id)
        if risk.status == RiskStatus.IDENTIFIED:
            risk.status = RiskStatus.MITIGATING
            self.risk_repo.update(risk)

        return control

    def update_control(self, control_id: UUID, data: ControlUpdate) -> Control:
        control = self.get_control(control_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "control_type" and value:
                value = ControlType(value)
            elif field == "effectiveness" and value:
                value = ControlEffectiveness(value)
            setattr(control, field, value)

        control.updated_by = self.user_id
        return self.control_repo.update(control)

    def record_control_execution(
        self,
        control_id: UUID,
        data: ControlExecutionRecord
    ) -> Control:
        control = self.get_control(control_id)

        control.effectiveness = ControlEffectiveness(data.effectiveness)
        control.last_executed_at = datetime.utcnow()

        if data.evidence_links:
            control.evidence_links.extend(data.evidence_links)

        control.updated_by = self.user_id
        return self.control_repo.update(control)

    def delete_control(self, control_id: UUID) -> None:
        control = self.get_control(control_id)
        control.deleted_by = self.user_id
        self.control_repo.delete(control)

    # ============== Mitigation Action ==============

    def list_actions(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[UUID] = None,
        risk_id: Optional[UUID] = None
    ) -> Tuple[List[MitigationAction], int, int]:
        return self.action_repo.list(
            page, page_size, search, status, assignee_id, risk_id
        )

    def list_actions_by_risk(
        self,
        risk_id: UUID,
        status: Optional[str] = None
    ) -> List[MitigationAction]:
        self.get_risk(risk_id)
        return self.action_repo.list_by_risk(risk_id, status)

    def get_action(self, action_id: UUID) -> MitigationAction:
        action = self.action_repo.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(str(action_id))
        return action

    def create_action(self, data: ActionCreate) -> MitigationAction:
        self.get_risk(data.risk_id)

        code = data.code or self.action_repo.get_next_code()

        if self.action_repo.get_by_code(code):
            raise ActionDuplicateError(code)

        action = MitigationAction(
            risk_id=data.risk_id,
            code=code,
            title=data.title,
            description=data.description,
            assignee_id=data.assignee_id,
            planned_start=data.planned_start,
            planned_end=data.planned_end,
            estimated_cost=data.estimated_cost,
            currency=data.currency,
            expected_probability_reduction=data.expected_probability_reduction,
            expected_impact_reduction=data.expected_impact_reduction,
            priority=data.priority,
            notes=data.notes,
            created_by=self.user_id
        )

        return self.action_repo.create(action)

    def update_action(self, action_id: UUID, data: ActionUpdate) -> MitigationAction:
        action = self.get_action(action_id)

        if action.status == ActionStatus.COMPLETED:
            raise ActionCompletedError(str(action_id))

        if action.status == ActionStatus.CANCELLED:
            raise ActionCancelledError(str(action_id))

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(action, field, value)

        action.updated_by = self.user_id
        return self.action_repo.update(action)

    def update_action_progress(
        self,
        action_id: UUID,
        data: ActionProgressUpdate
    ) -> MitigationAction:
        action = self.get_action(action_id)

        if action.status == ActionStatus.COMPLETED:
            raise ActionCompletedError(str(action_id))

        if action.status == ActionStatus.CANCELLED:
            raise ActionCancelledError(str(action_id))

        action.progress_percent = data.progress_percent

        if data.progress_percent > 0 and not action.actual_start:
            action.actual_start = date.today()
            action.status = ActionStatus.IN_PROGRESS

        if data.progress_percent == 100:
            action.actual_end = date.today()
            action.status = ActionStatus.COMPLETED

        if data.actual_cost is not None:
            action.actual_cost = data.actual_cost

        if data.notes:
            action.notes = data.notes

        action.updated_by = self.user_id
        return self.action_repo.update(action)

    def start_action(self, action_id: UUID) -> MitigationAction:
        action = self.get_action(action_id)

        allowed = ActionStatus.allowed_transitions().get(action.status, [])
        if ActionStatus.IN_PROGRESS not in allowed:
            raise ActionStateError(action.status.value, ActionStatus.IN_PROGRESS.value)

        action.status = ActionStatus.IN_PROGRESS
        action.actual_start = date.today()
        action.updated_by = self.user_id
        return self.action_repo.update(action)

    def complete_action(self, action_id: UUID) -> MitigationAction:
        action = self.get_action(action_id)

        allowed = ActionStatus.allowed_transitions().get(action.status, [])
        if ActionStatus.COMPLETED not in allowed:
            raise ActionStateError(action.status.value, ActionStatus.COMPLETED.value)

        action.status = ActionStatus.COMPLETED
        action.progress_percent = 100
        action.actual_end = date.today()
        action.updated_by = self.user_id
        return self.action_repo.update(action)

    def cancel_action(self, action_id: UUID, reason: str = "") -> MitigationAction:
        action = self.get_action(action_id)

        allowed = ActionStatus.allowed_transitions().get(action.status, [])
        if ActionStatus.CANCELLED not in allowed:
            raise ActionStateError(action.status.value, ActionStatus.CANCELLED.value)

        action.status = ActionStatus.CANCELLED
        if reason:
            action.notes = f"{action.notes}\nAnnulé: {reason}".strip()
        action.updated_by = self.user_id
        return self.action_repo.update(action)

    def delete_action(self, action_id: UUID) -> None:
        action = self.get_action(action_id)
        action.deleted_by = self.user_id
        self.action_repo.delete(action)

    def get_overdue_actions(self) -> List[MitigationAction]:
        return self.action_repo.get_overdue()

    # ============== Risk Indicator ==============

    def list_indicators(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[RiskIndicator], int, int]:
        return self.indicator_repo.list(
            page, page_size, search, status, is_active
        )

    def list_indicators_by_risk(
        self,
        risk_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[RiskIndicator]:
        self.get_risk(risk_id)
        return self.indicator_repo.list_by_risk(risk_id, is_active)

    def get_indicator(self, indicator_id: UUID) -> RiskIndicator:
        indicator = self.indicator_repo.get_by_id(indicator_id)
        if not indicator:
            raise IndicatorNotFoundError(str(indicator_id))
        return indicator

    def create_indicator(self, data: IndicatorCreate) -> RiskIndicator:
        self.get_risk(data.risk_id)

        code = data.code or self.indicator_repo.get_next_code()

        if self.indicator_repo.get_by_code(code):
            raise IndicatorDuplicateError(code)

        self._validate_thresholds(
            data.green_threshold,
            data.amber_threshold,
            data.red_threshold,
            data.higher_is_worse
        )

        indicator = RiskIndicator(
            risk_id=data.risk_id,
            code=code,
            name=data.name,
            description=data.description,
            metric_type=data.metric_type,
            unit=data.unit,
            green_threshold=data.green_threshold,
            amber_threshold=data.amber_threshold,
            red_threshold=data.red_threshold,
            higher_is_worse=data.higher_is_worse,
            measurement_frequency=data.measurement_frequency,
            data_source=data.data_source,
            is_automated=data.is_automated,
            is_active=data.is_active,
            created_by=self.user_id
        )

        return self.indicator_repo.create(indicator)

    def update_indicator(
        self,
        indicator_id: UUID,
        data: IndicatorUpdate
    ) -> RiskIndicator:
        indicator = self.get_indicator(indicator_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(indicator, field, value)

        self._validate_thresholds(
            indicator.green_threshold,
            indicator.amber_threshold,
            indicator.red_threshold,
            indicator.higher_is_worse
        )

        indicator.updated_by = self.user_id
        return self.indicator_repo.update(indicator)

    def record_indicator_value(
        self,
        indicator_id: UUID,
        data: IndicatorValueRecord
    ) -> RiskIndicator:
        indicator = self.get_indicator(indicator_id)

        status = self._determine_indicator_status(indicator, data.value)

        now = data.measurement_date or datetime.utcnow()

        indicator.historical_values.append({
            "date": now.isoformat(),
            "value": float(data.value),
            "status": status.value,
            "notes": data.notes
        })

        indicator.current_value = data.value
        indicator.current_status = status
        indicator.last_measured_at = now
        indicator.updated_by = self.user_id

        return self.indicator_repo.update(indicator)

    def delete_indicator(self, indicator_id: UUID) -> None:
        indicator = self.get_indicator(indicator_id)
        indicator.deleted_by = self.user_id
        self.indicator_repo.delete(indicator)

    def get_indicator_alerts(self) -> List[RiskIndicator]:
        return self.indicator_repo.get_alerts()

    def _validate_thresholds(
        self,
        green: Decimal,
        amber: Decimal,
        red: Decimal,
        higher_is_worse: bool
    ) -> None:
        if higher_is_worse:
            if not (green <= amber <= red):
                raise IndicatorThresholdError(
                    "Pour higher_is_worse=true: green <= amber <= red"
                )
        else:
            if not (green >= amber >= red):
                raise IndicatorThresholdError(
                    "Pour higher_is_worse=false: green >= amber >= red"
                )

    def _determine_indicator_status(
        self,
        indicator: RiskIndicator,
        value: Decimal
    ) -> IndicatorStatus:
        if indicator.higher_is_worse:
            if value >= indicator.red_threshold:
                return IndicatorStatus.RED
            elif value >= indicator.amber_threshold:
                return IndicatorStatus.AMBER
            else:
                return IndicatorStatus.GREEN
        else:
            if value <= indicator.red_threshold:
                return IndicatorStatus.RED
            elif value <= indicator.amber_threshold:
                return IndicatorStatus.AMBER
            else:
                return IndicatorStatus.GREEN

    # ============== Risk Incident ==============

    def list_incidents(
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
        return self.incident_repo.list(
            page, page_size, search, status, risk_id,
            date_from, date_to, impact
        )

    def list_incidents_by_risk(self, risk_id: UUID) -> List[RiskIncident]:
        self.get_risk(risk_id)
        return self.incident_repo.list_by_risk(risk_id)

    def get_incident(self, incident_id: UUID) -> RiskIncident:
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise IncidentNotFoundError(str(incident_id))
        return incident

    def create_incident(self, data: IncidentCreate) -> RiskIncident:
        if data.risk_id:
            self.get_risk(data.risk_id)

        code = data.code or self.incident_repo.get_next_code()

        if self.incident_repo.get_by_code(code):
            raise IncidentDuplicateError(code)

        incident = RiskIncident(
            risk_id=data.risk_id,
            code=code,
            title=data.title,
            description=data.description,
            occurred_at=data.occurred_at or datetime.utcnow(),
            detected_at=data.detected_at,
            actual_impact=Impact(data.actual_impact),
            financial_loss=data.financial_loss,
            currency=data.currency,
            affected_parties=data.affected_parties,
            root_cause=data.root_cause,
            contributing_factors=data.contributing_factors,
            owner_id=data.owner_id,
            reporter_id=self.user_id,
            created_by=self.user_id
        )

        incident = self.incident_repo.create(incident)

        if data.risk_id:
            risk = self.get_risk(data.risk_id)
            risk.extra_data["last_incident_id"] = str(incident.id)
            risk.extra_data["incident_count"] = risk.extra_data.get("incident_count", 0) + 1
            self.risk_repo.update(risk)

        return incident

    def update_incident(
        self,
        incident_id: UUID,
        data: IncidentUpdate
    ) -> RiskIncident:
        incident = self.get_incident(incident_id)

        if incident.status == IncidentStatus.CLOSED:
            raise IncidentClosedError(str(incident_id))

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "actual_impact" and value:
                value = Impact(value)
            setattr(incident, field, value)

        incident.updated_by = self.user_id
        return self.incident_repo.update(incident)

    def start_investigation(self, incident_id: UUID) -> RiskIncident:
        incident = self.get_incident(incident_id)

        if incident.status != IncidentStatus.OPEN:
            raise IncidentStateError(
                incident.status.value, IncidentStatus.INVESTIGATING.value
            )

        incident.status = IncidentStatus.INVESTIGATING
        incident.updated_by = self.user_id
        return self.incident_repo.update(incident)

    def resolve_incident(
        self,
        incident_id: UUID,
        data: IncidentResolution
    ) -> RiskIncident:
        incident = self.get_incident(incident_id)

        if incident.status == IncidentStatus.CLOSED:
            raise IncidentClosedError(str(incident_id))

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
        incident.lessons_learned = data.lessons_learned
        incident.corrective_action_ids = data.corrective_action_ids
        incident.updated_by = self.user_id

        return self.incident_repo.update(incident)

    def close_incident(self, incident_id: UUID) -> RiskIncident:
        incident = self.get_incident(incident_id)

        if incident.status != IncidentStatus.RESOLVED:
            raise IncidentNotResolvedError(str(incident_id))

        incident.status = IncidentStatus.CLOSED
        incident.closed_at = datetime.utcnow()
        incident.updated_by = self.user_id

        return self.incident_repo.update(incident)

    def delete_incident(self, incident_id: UUID) -> None:
        incident = self.get_incident(incident_id)
        incident.deleted_by = self.user_id
        self.incident_repo.delete(incident)

    # ============== Helpers ==============

    def _calculate_score(self, probability: Probability, impact: Impact) -> int:
        prob_values = {
            Probability.RARE: 1,
            Probability.UNLIKELY: 2,
            Probability.POSSIBLE: 3,
            Probability.LIKELY: 4,
            Probability.ALMOST_CERTAIN: 5
        }
        impact_values = {
            Impact.NEGLIGIBLE: 1,
            Impact.MINOR: 2,
            Impact.MODERATE: 3,
            Impact.MAJOR: 4,
            Impact.CATASTROPHIC: 5
        }
        return prob_values.get(probability, 3) * impact_values.get(impact, 3)

    def _determine_level(
        self,
        score: int,
        matrix_id: Optional[UUID] = None
    ) -> RiskLevel:
        matrix = None
        if matrix_id:
            matrix = self.matrix_repo.get_by_id(matrix_id)
        if not matrix:
            matrix = self.matrix_repo.get_default()

        if matrix:
            if score <= matrix.low_threshold:
                return RiskLevel.LOW
            elif score <= matrix.medium_threshold:
                return RiskLevel.MEDIUM
            elif score <= matrix.high_threshold:
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL
        else:
            if score <= 4:
                return RiskLevel.LOW
            elif score <= 9:
                return RiskLevel.MEDIUM
            elif score <= 15:
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL

    # ============== Reports ==============

    def generate_report(
        self,
        report_date: Optional[date] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> RiskReportResponse:
        today = report_date or date.today()

        risks_by_level = self.risk_repo.count_by_level()
        risks_by_category = self.risk_repo.count_by_category()
        risks_by_status = self.risk_repo.count_by_status()

        actions_by_status = self.action_repo.count_by_status()
        indicators_by_status = self.indicator_repo.count_by_status()

        total_risks = sum(risks_by_status.values())
        active_risks = total_risks - risks_by_status.get("closed", 0)

        total_actions = sum(actions_by_status.values())
        completed_actions = actions_by_status.get("completed", 0)
        overdue_actions = actions_by_status.get("overdue", 0)
        completion_rate = (
            Decimal(completed_actions) / Decimal(total_actions) * 100
            if total_actions > 0 else Decimal("0")
        )

        total_kris = sum(indicators_by_status.values())
        kris_in_red = indicators_by_status.get("red", 0)
        kris_in_amber = indicators_by_status.get("amber", 0)

        incidents_by_status = self.incident_repo.count_by_status()
        total_incidents = sum(incidents_by_status.values())
        total_financial_loss = self.incident_repo.get_total_financial_loss(
            period_start, period_end
        )

        heatmap_data = self.risk_repo.get_heatmap_data()

        top_risks, _, _ = self.risk_repo.list(page=1, page_size=5)
        top_risks_data = [
            {
                "id": str(r.id),
                "code": r.code,
                "title": r.title,
                "level": r.inherent_level.value,
                "score": r.inherent_score,
                "category": r.category.value
            }
            for r in top_risks
        ]

        return RiskReportResponse(
            tenant_id=self.tenant_id,
            report_date=today,
            period_start=period_start,
            period_end=period_end,
            total_risks=total_risks,
            active_risks=active_risks,
            new_risks=0,
            closed_risks=risks_by_status.get("closed", 0),
            critical_risks=risks_by_level.get("critical", 0),
            high_risks=risks_by_level.get("high", 0),
            medium_risks=risks_by_level.get("medium", 0),
            low_risks=risks_by_level.get("low", 0),
            risks_by_category=risks_by_category,
            risks_by_status=risks_by_status,
            total_actions=total_actions,
            completed_actions=completed_actions,
            overdue_actions=overdue_actions,
            action_completion_rate=completion_rate,
            total_kris=total_kris,
            kris_in_red=kris_in_red,
            kris_in_amber=kris_in_amber,
            total_incidents=total_incidents,
            total_financial_loss=total_financial_loss,
            risk_trend="stable",
            top_risks=top_risks_data,
            heatmap_data=heatmap_data
        )

    def get_heatmap(self) -> List[dict]:
        return self.risk_repo.get_heatmap_data()

    def get_risks_for_review(self, before_date: Optional[date] = None) -> List[Risk]:
        check_date = before_date or date.today()
        return self.risk_repo.get_risks_for_review(check_date)
