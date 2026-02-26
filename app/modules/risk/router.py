"""
Routes API Risk Management - GAP-075
=====================================
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

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
    RiskMatrixCreate, RiskMatrixUpdate, RiskMatrixResponse, RiskMatrixListResponse,
    RiskCreate, RiskUpdate, RiskResponse, RiskListResponse,
    ControlCreate, ControlUpdate, ControlResponse, ControlListResponse, ControlExecutionRecord,
    ActionCreate, ActionUpdate, ActionResponse, ActionListResponse, ActionProgressUpdate,
    IndicatorCreate, IndicatorUpdate, IndicatorResponse, IndicatorListResponse, IndicatorValueRecord,
    AssessmentCreate, AssessmentValidation, AssessmentResponse, AssessmentListResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentListResponse, IncidentResolution,
    RiskReportRequest, RiskReportResponse, RiskHeatmapResponse
)
from .service import RiskService


router = APIRouter(prefix="/risk", tags=["Risk Management"])


def get_service(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> RiskService:
    return RiskService(db, user.tenant_id, user.id)


# ============== Risk Matrix Routes ==============

@router.get("/matrices", response_model=RiskMatrixListResponse)
async def list_matrices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    is_active: Optional[bool] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:matrix:read")
):
    items, total, pages = service.list_matrices(page, page_size, search, is_active)
    return RiskMatrixListResponse(
        items=[RiskMatrixResponse.model_validate(m) for m in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/matrices/{matrix_id}", response_model=RiskMatrixResponse)
async def get_matrix(
    matrix_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:matrix:read")
):
    try:
        return RiskMatrixResponse.model_validate(service.get_matrix(matrix_id))
    except RiskMatrixNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/matrices", response_model=RiskMatrixResponse, status_code=201)
async def create_matrix(
    data: RiskMatrixCreate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:matrix:create")
):
    try:
        return RiskMatrixResponse.model_validate(service.create_matrix(data))
    except RiskMatrixDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/matrices/{matrix_id}", response_model=RiskMatrixResponse)
async def update_matrix(
    matrix_id: UUID,
    data: RiskMatrixUpdate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:matrix:update")
):
    try:
        return RiskMatrixResponse.model_validate(service.update_matrix(matrix_id, data))
    except RiskMatrixNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RiskMatrixDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/matrices/{matrix_id}", status_code=204)
async def delete_matrix(
    matrix_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:matrix:delete")
):
    try:
        service.delete_matrix(matrix_id)
    except RiskMatrixNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RiskMatrixInUseError, DefaultMatrixRequiredError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Risk Routes ==============

@router.get("/risks", response_model=RiskListResponse)
async def list_risks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    category: Optional[str] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,
    owner_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    include_closed: bool = False,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:read")
):
    items, total, pages = service.list_risks(
        page, page_size, search, category, status,
        level, owner_id, department_id, include_closed
    )
    return RiskListResponse(
        items=[RiskResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/risks/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:read")
):
    try:
        return RiskResponse.model_validate(service.get_risk(risk_id))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/risks", response_model=RiskResponse, status_code=201)
async def create_risk(
    data: RiskCreate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:create")
):
    try:
        return RiskResponse.model_validate(service.create_risk(data))
    except RiskDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/risks/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:update")
):
    try:
        return RiskResponse.model_validate(service.update_risk(risk_id, data))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RiskClosedError, RiskCircularReferenceError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/risks/{risk_id}/status", response_model=RiskResponse)
async def change_risk_status(
    risk_id: UUID,
    new_status: str,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:update")
):
    try:
        return RiskResponse.model_validate(service.change_risk_status(risk_id, new_status))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (RiskStateError, RiskHasActiveActionsError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/risks/{risk_id}/close", response_model=RiskResponse)
async def close_risk(
    risk_id: UUID,
    reason: str = "",
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:close")
):
    try:
        return RiskResponse.model_validate(service.close_risk(risk_id, reason))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RiskHasActiveActionsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/risks/{risk_id}", status_code=204)
async def delete_risk(
    risk_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:delete")
):
    try:
        service.delete_risk(risk_id)
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/risks/{risk_id}/restore", response_model=RiskResponse)
async def restore_risk(
    risk_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:restore")
):
    try:
        return RiskResponse.model_validate(service.restore_risk(risk_id))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Assessment Routes ==============

@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_id: Optional[UUID] = None,
    assessor_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:assessment:read")
):
    items, total, pages = service.list_assessments(
        page, page_size, risk_id, assessor_id, date_from, date_to
    )
    return AssessmentListResponse(
        items=[AssessmentResponse.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.post("/risks/{risk_id}/assess", response_model=AssessmentResponse, status_code=201)
async def assess_risk(
    risk_id: UUID,
    data: AssessmentCreate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:assessment:create")
):
    try:
        data.risk_id = risk_id
        return AssessmentResponse.model_validate(service.assess_risk(risk_id, data))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RiskClosedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assessments/{assessment_id}/validate", response_model=AssessmentResponse)
async def validate_assessment(
    assessment_id: UUID,
    data: AssessmentValidation,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:assessment:validate")
):
    try:
        return AssessmentResponse.model_validate(
            service.validate_assessment(assessment_id, data)
        )
    except AssessmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AssessmentAlreadyValidatedError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Control Routes ==============

@router.get("/controls", response_model=ControlListResponse)
async def list_controls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    control_type: Optional[str] = None,
    effectiveness: Optional[str] = None,
    is_active: Optional[bool] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:control:read")
):
    items, total, pages = service.list_controls(
        page, page_size, search, control_type, effectiveness, is_active
    )
    return ControlListResponse(
        items=[ControlResponse.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/risks/{risk_id}/controls", response_model=List[ControlResponse])
async def list_controls_by_risk(
    risk_id: UUID,
    is_active: Optional[bool] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:control:read")
):
    try:
        controls = service.list_controls_by_risk(risk_id, is_active)
        return [ControlResponse.model_validate(c) for c in controls]
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/controls/{control_id}", response_model=ControlResponse)
async def get_control(
    control_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:control:read")
):
    try:
        return ControlResponse.model_validate(service.get_control(control_id))
    except ControlNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/controls", response_model=ControlResponse, status_code=201)
async def create_control(
    data: ControlCreate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:control:create")
):
    try:
        return ControlResponse.model_validate(service.create_control(data))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ControlDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/controls/{control_id}", response_model=ControlResponse)
async def update_control(
    control_id: UUID,
    data: ControlUpdate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:control:update")
):
    try:
        return ControlResponse.model_validate(service.update_control(control_id, data))
    except ControlNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/controls/{control_id}/execute", response_model=ControlResponse)
async def record_control_execution(
    control_id: UUID,
    data: ControlExecutionRecord,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:control:execute")
):
    try:
        return ControlResponse.model_validate(
            service.record_control_execution(control_id, data)
        )
    except ControlNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/controls/{control_id}", status_code=204)
async def delete_control(
    control_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:control:delete")
):
    try:
        service.delete_control(control_id)
    except ControlNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Mitigation Action Routes ==============

@router.get("/actions", response_model=ActionListResponse)
async def list_actions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    risk_id: Optional[UUID] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:read")
):
    items, total, pages = service.list_actions(
        page, page_size, search, status, assignee_id, risk_id
    )
    return ActionListResponse(
        items=[ActionResponse.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/risks/{risk_id}/actions", response_model=List[ActionResponse])
async def list_actions_by_risk(
    risk_id: UUID,
    status: Optional[str] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:read")
):
    try:
        actions = service.list_actions_by_risk(risk_id, status)
        return [ActionResponse.model_validate(a) for a in actions]
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/actions/overdue", response_model=List[ActionResponse])
async def get_overdue_actions(
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:read")
):
    actions = service.get_overdue_actions()
    return [ActionResponse.model_validate(a) for a in actions]


@router.get("/actions/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:read")
):
    try:
        return ActionResponse.model_validate(service.get_action(action_id))
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/actions", response_model=ActionResponse, status_code=201)
async def create_action(
    data: ActionCreate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:create")
):
    try:
        return ActionResponse.model_validate(service.create_action(data))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ActionDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/actions/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: UUID,
    data: ActionUpdate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:update")
):
    try:
        return ActionResponse.model_validate(service.update_action(action_id, data))
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ActionCompletedError, ActionCancelledError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/actions/{action_id}/progress", response_model=ActionResponse)
async def update_action_progress(
    action_id: UUID,
    data: ActionProgressUpdate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:update")
):
    try:
        return ActionResponse.model_validate(
            service.update_action_progress(action_id, data)
        )
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ActionCompletedError, ActionCancelledError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/actions/{action_id}/start", response_model=ActionResponse)
async def start_action(
    action_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:update")
):
    try:
        return ActionResponse.model_validate(service.start_action(action_id))
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ActionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/actions/{action_id}/complete", response_model=ActionResponse)
async def complete_action(
    action_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:update")
):
    try:
        return ActionResponse.model_validate(service.complete_action(action_id))
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ActionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/actions/{action_id}/cancel", response_model=ActionResponse)
async def cancel_action(
    action_id: UUID,
    reason: str = "",
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:cancel")
):
    try:
        return ActionResponse.model_validate(service.cancel_action(action_id, reason))
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ActionStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/actions/{action_id}", status_code=204)
async def delete_action(
    action_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:action:delete")
):
    try:
        service.delete_action(action_id)
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Indicator Routes ==============

@router.get("/indicators", response_model=IndicatorListResponse)
async def list_indicators(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:read")
):
    items, total, pages = service.list_indicators(
        page, page_size, search, status, is_active
    )
    return IndicatorListResponse(
        items=[IndicatorResponse.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/risks/{risk_id}/indicators", response_model=List[IndicatorResponse])
async def list_indicators_by_risk(
    risk_id: UUID,
    is_active: Optional[bool] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:read")
):
    try:
        indicators = service.list_indicators_by_risk(risk_id, is_active)
        return [IndicatorResponse.model_validate(i) for i in indicators]
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/indicators/alerts", response_model=List[IndicatorResponse])
async def get_indicator_alerts(
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:read")
):
    indicators = service.get_indicator_alerts()
    return [IndicatorResponse.model_validate(i) for i in indicators]


@router.get("/indicators/{indicator_id}", response_model=IndicatorResponse)
async def get_indicator(
    indicator_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:read")
):
    try:
        return IndicatorResponse.model_validate(service.get_indicator(indicator_id))
    except IndicatorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/indicators", response_model=IndicatorResponse, status_code=201)
async def create_indicator(
    data: IndicatorCreate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:create")
):
    try:
        return IndicatorResponse.model_validate(service.create_indicator(data))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IndicatorDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except IndicatorThresholdError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/indicators/{indicator_id}", response_model=IndicatorResponse)
async def update_indicator(
    indicator_id: UUID,
    data: IndicatorUpdate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:update")
):
    try:
        return IndicatorResponse.model_validate(
            service.update_indicator(indicator_id, data)
        )
    except IndicatorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IndicatorThresholdError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/indicators/{indicator_id}/record", response_model=IndicatorResponse)
async def record_indicator_value(
    indicator_id: UUID,
    data: IndicatorValueRecord,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:update")
):
    try:
        return IndicatorResponse.model_validate(
            service.record_indicator_value(indicator_id, data)
        )
    except IndicatorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/indicators/{indicator_id}", status_code=204)
async def delete_indicator(
    indicator_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:indicator:delete")
):
    try:
        service.delete_indicator(indicator_id)
    except IndicatorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Incident Routes ==============

@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[str] = None,
    risk_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    impact: Optional[str] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:read")
):
    items, total, pages = service.list_incidents(
        page, page_size, search, status, risk_id, date_from, date_to, impact
    )
    return IncidentListResponse(
        items=[IncidentResponse.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/risks/{risk_id}/incidents", response_model=List[IncidentResponse])
async def list_incidents_by_risk(
    risk_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:read")
):
    try:
        incidents = service.list_incidents_by_risk(risk_id)
        return [IncidentResponse.model_validate(i) for i in incidents]
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:read")
):
    try:
        return IncidentResponse.model_validate(service.get_incident(incident_id))
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    data: IncidentCreate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:create")
):
    try:
        return IncidentResponse.model_validate(service.create_incident(data))
    except RiskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IncidentDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:update")
):
    try:
        return IncidentResponse.model_validate(service.update_incident(incident_id, data))
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IncidentClosedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/investigate", response_model=IncidentResponse)
async def start_investigation(
    incident_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:update")
):
    try:
        return IncidentResponse.model_validate(service.start_investigation(incident_id))
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IncidentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: UUID,
    data: IncidentResolution,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:resolve")
):
    try:
        return IncidentResponse.model_validate(service.resolve_incident(incident_id, data))
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IncidentClosedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/close", response_model=IncidentResponse)
async def close_incident(
    incident_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:close")
):
    try:
        return IncidentResponse.model_validate(service.close_incident(incident_id))
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IncidentNotResolvedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/incidents/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: UUID,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:incident:delete")
):
    try:
        service.delete_incident(incident_id)
    except IncidentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Report Routes ==============

@router.get("/report", response_model=RiskReportResponse)
async def get_risk_report(
    report_date: Optional[date] = None,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:report:read")
):
    return service.generate_report(report_date, period_start, period_end)


@router.get("/heatmap")
async def get_risk_heatmap(
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:report:read")
):
    return {"cells": service.get_heatmap()}


@router.get("/review-due", response_model=List[RiskResponse])
async def get_risks_for_review(
    before_date: Optional[date] = None,
    service: RiskService = Depends(get_service),
    _: None = require_permission("risk:read")
):
    risks = service.get_risks_for_review(before_date)
    return [RiskResponse.model_validate(r) for r in risks]
