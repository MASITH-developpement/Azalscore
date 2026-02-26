"""
AZALSCORE Finance Suite Router V3
==================================

Endpoints REST pour l'orchestrateur Finance Suite.

Endpoints:
- GET  /v3/finance/suite/dashboard - Tableau de bord consolidé
- GET  /v3/finance/suite/modules - Liste des modules
- GET  /v3/finance/suite/modules/{name} - Détails d'un module
- GET  /v3/finance/suite/modules/{name}/health - Health check module
- GET  /v3/finance/suite/config - Configuration
- PUT  /v3/finance/suite/config - Modifier config
- GET  /v3/finance/suite/alerts - Liste des alertes
- POST /v3/finance/suite/alerts - Créer une alerte
- POST /v3/finance/suite/alerts/{id}/acknowledge - Acquitter
- GET  /v3/finance/suite/alerts/summary - Résumé alertes
- GET  /v3/finance/suite/workflows - Liste workflows
- POST /v3/finance/suite/workflows - Démarrer workflow
- GET  /v3/finance/suite/workflows/{id} - Détails workflow
- POST /v3/finance/suite/workflows/{id}/advance - Avancer
- POST /v3/finance/suite/workflows/{id}/cancel - Annuler
- GET  /v3/finance/suite/summary - Résumé financier
- GET  /v3/finance/suite/kpis - KPIs
- GET  /v3/finance/suite/health - Health check global
"""
from __future__ import annotations


import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    FinanceSuiteService,
    FinanceDashboard,
    ModuleStatus,
    SuiteConfig,
    AlertSeverity,
    WorkflowType,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/suite", tags=["Finance Suite"])


# =============================================================================
# SCHEMAS
# =============================================================================


class ModuleResponse(BaseModel):
    """Réponse module."""

    name: str
    display_name: str
    description: str
    status: str
    version: str
    endpoint: str
    features: list[str] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    """Réponse tableau de bord."""

    tenant_id: str
    generated_at: str
    current_balance: Decimal
    available_balance: Decimal
    projected_balance_30d: Decimal
    pending_entries: int
    unreconciled_transactions: int
    invoices_pending: int
    invoices_overdue: int
    total_receivable: Decimal
    total_payable: Decimal
    active_cards: int
    cards_near_limit: int
    alerts: list[dict] = Field(default_factory=list)
    modules_status: dict = Field(default_factory=dict)


class ConfigResponse(BaseModel):
    """Réponse configuration."""

    default_currency: str
    fiscal_year_start_month: int
    auto_reconciliation_enabled: bool
    ocr_auto_processing: bool
    approval_workflow_enabled: bool
    alert_thresholds: dict
    notification_settings: dict
    integration_settings: dict


class UpdateConfigRequest(BaseModel):
    """Requête de mise à jour config."""

    default_currency: Optional[str] = None
    fiscal_year_start_month: Optional[int] = Field(None, ge=1, le=12)
    auto_reconciliation_enabled: Optional[bool] = None
    ocr_auto_processing: Optional[bool] = None
    approval_workflow_enabled: Optional[bool] = None
    alert_thresholds: Optional[dict] = None
    notification_settings: Optional[dict] = None
    integration_settings: Optional[dict] = None


class CreateAlertRequest(BaseModel):
    """Requête de création d'alerte."""

    severity: AlertSeverity
    module: str
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    metadata: Optional[dict] = None


class AlertResponse(BaseModel):
    """Réponse alerte."""

    id: str
    severity: str
    module: str
    title: str
    message: str
    created_at: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    """Requête d'acquittement."""

    user_id: str


class StartWorkflowRequest(BaseModel):
    """Requête de démarrage de workflow."""

    workflow_type: WorkflowType
    data: dict = Field(default_factory=dict)
    created_by: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Réponse workflow."""

    id: str
    workflow_type: str
    status: str
    current_step: int
    total_steps: int
    data: dict
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    created_by: Optional[str] = None
    error_message: Optional[str] = None


class AdvanceWorkflowRequest(BaseModel):
    """Requête d'avancement."""

    step_data: Optional[dict] = None


class CancelWorkflowRequest(BaseModel):
    """Requête d'annulation."""

    reason: Optional[str] = None


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_suite_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> FinanceSuiteService:
    """Dépendance pour obtenir le service Finance Suite."""
    return FinanceSuiteService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# ENDPOINTS - DASHBOARD
# =============================================================================


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Tableau de bord finance",
    description="Retourne le tableau de bord consolidé de tous les modules finance.",
)
async def get_dashboard(
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """
    Tableau de bord finance consolidé.

    Agrège les données de:
    - Trésorerie
    - Comptabilité
    - Facturation
    - Cartes virtuelles
    - Alertes
    """
    dashboard = await service.get_dashboard()

    return DashboardResponse(
        tenant_id=dashboard.tenant_id,
        generated_at=dashboard.generated_at.isoformat(),
        current_balance=dashboard.current_balance,
        available_balance=dashboard.available_balance,
        projected_balance_30d=dashboard.projected_balance_30d,
        pending_entries=dashboard.pending_entries,
        unreconciled_transactions=dashboard.unreconciled_transactions,
        invoices_pending=dashboard.invoices_pending,
        invoices_overdue=dashboard.invoices_overdue,
        total_receivable=dashboard.total_receivable,
        total_payable=dashboard.total_payable,
        active_cards=dashboard.active_cards,
        cards_near_limit=dashboard.cards_near_limit,
        alerts=dashboard.alerts,
        modules_status=dashboard.modules_status,
    )


# =============================================================================
# ENDPOINTS - MODULES
# =============================================================================


@router.get(
    "/modules",
    response_model=list[ModuleResponse],
    summary="Liste des modules",
    description="Retourne la liste de tous les modules de la suite Finance.",
)
async def list_modules(
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Liste les modules de la suite Finance."""
    modules = await service.list_modules()

    return [
        ModuleResponse(
            name=m.name,
            display_name=m.display_name,
            description=m.description,
            status=m.status.value,
            version=m.version,
            endpoint=m.endpoint,
            features=m.features,
        )
        for m in modules
    ]


@router.get(
    "/modules/{module_name}",
    response_model=ModuleResponse,
    summary="Détails d'un module",
    description="Retourne les détails d'un module spécifique.",
)
async def get_module(
    module_name: str,
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Détails d'un module."""
    module = await service.get_module(module_name)

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module non trouvé",
        )

    return ModuleResponse(
        name=module.name,
        display_name=module.display_name,
        description=module.description,
        status=module.status.value,
        version=module.version,
        endpoint=module.endpoint,
        features=module.features,
    )


@router.get(
    "/modules/{module_name}/health",
    summary="Health check module",
    description="Retourne le health check d'un module spécifique.",
)
async def get_module_health(
    module_name: str,
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Health check d'un module."""
    health = await service.get_module_health(module_name)

    if "error" in health:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=health["error"],
        )

    return health


# =============================================================================
# ENDPOINTS - CONFIGURATION
# =============================================================================


@router.get(
    "/config",
    response_model=ConfigResponse,
    summary="Configuration",
    description="Retourne la configuration de la suite Finance.",
)
async def get_config(
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Configuration de la suite Finance."""
    config = await service.get_config()

    return ConfigResponse(
        default_currency=config.default_currency,
        fiscal_year_start_month=config.fiscal_year_start_month,
        auto_reconciliation_enabled=config.auto_reconciliation_enabled,
        ocr_auto_processing=config.ocr_auto_processing,
        approval_workflow_enabled=config.approval_workflow_enabled,
        alert_thresholds=config.alert_thresholds,
        notification_settings=config.notification_settings,
        integration_settings=config.integration_settings,
    )


@router.put(
    "/config",
    response_model=ConfigResponse,
    summary="Modifier la configuration",
    description="Met à jour la configuration de la suite Finance.",
)
async def update_config(
    request: UpdateConfigRequest,
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Met à jour la configuration."""
    config = await service.update_config(
        default_currency=request.default_currency,
        fiscal_year_start_month=request.fiscal_year_start_month,
        auto_reconciliation_enabled=request.auto_reconciliation_enabled,
        ocr_auto_processing=request.ocr_auto_processing,
        approval_workflow_enabled=request.approval_workflow_enabled,
        alert_thresholds=request.alert_thresholds,
        notification_settings=request.notification_settings,
        integration_settings=request.integration_settings,
    )

    return ConfigResponse(
        default_currency=config.default_currency,
        fiscal_year_start_month=config.fiscal_year_start_month,
        auto_reconciliation_enabled=config.auto_reconciliation_enabled,
        ocr_auto_processing=config.ocr_auto_processing,
        approval_workflow_enabled=config.approval_workflow_enabled,
        alert_thresholds=config.alert_thresholds,
        notification_settings=config.notification_settings,
        integration_settings=config.integration_settings,
    )


# =============================================================================
# ENDPOINTS - ALERTS
# =============================================================================


@router.get(
    "/alerts",
    response_model=list[AlertResponse],
    summary="Liste des alertes",
    description="Retourne la liste des alertes finance.",
)
async def list_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filtrer par sévérité"),
    module: Optional[str] = Query(None, description="Filtrer par module"),
    acknowledged: Optional[bool] = Query(None, description="Filtrer par statut"),
    limit: int = Query(50, ge=1, le=500),
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Liste les alertes."""
    alerts = await service.list_alerts(
        severity=severity,
        module=module,
        acknowledged=acknowledged,
        limit=limit,
    )

    return [
        AlertResponse(
            id=a.id,
            severity=a.severity.value,
            module=a.module,
            title=a.title,
            message=a.message,
            created_at=a.created_at.isoformat(),
            acknowledged=a.acknowledged,
            acknowledged_by=a.acknowledged_by,
            acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        )
        for a in alerts
    ]


@router.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une alerte",
    description="Crée une nouvelle alerte finance.",
)
async def create_alert(
    request: CreateAlertRequest,
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Crée une alerte."""
    alert = await service.create_alert(
        severity=request.severity,
        module=request.module,
        title=request.title,
        message=request.message,
        metadata=request.metadata,
    )

    return AlertResponse(
        id=alert.id,
        severity=alert.severity.value,
        module=alert.module,
        title=alert.title,
        message=alert.message,
        created_at=alert.created_at.isoformat(),
        acknowledged=alert.acknowledged,
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=dict,
    summary="Acquitter une alerte",
    description="Marque une alerte comme acquittée.",
)
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeRequest,
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Acquitte une alerte."""
    success = await service.acknowledge_alert(alert_id, request.user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte non trouvée",
        )

    return {"success": True, "message": "Alerte acquittée"}


@router.get(
    "/alerts/summary",
    summary="Résumé des alertes",
    description="Retourne un résumé des alertes.",
)
async def get_alert_summary(
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Résumé des alertes."""
    return await service.get_alert_summary()


# =============================================================================
# ENDPOINTS - WORKFLOWS
# =============================================================================


@router.get(
    "/workflows",
    response_model=list[WorkflowResponse],
    summary="Liste des workflows",
    description="Retourne la liste des workflows.",
)
async def list_workflows(
    workflow_type: Optional[WorkflowType] = Query(None, description="Filtrer par type"),
    workflow_status: Optional[WorkflowStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Liste les workflows."""
    workflows = await service.list_workflows(
        workflow_type=workflow_type,
        status=workflow_status,
        limit=limit,
    )

    return [
        WorkflowResponse(
            id=w.id,
            workflow_type=w.workflow_type.value,
            status=w.status.value,
            current_step=w.current_step,
            total_steps=w.total_steps,
            data=w.data,
            created_at=w.created_at.isoformat(),
            updated_at=w.updated_at.isoformat(),
            completed_at=w.completed_at.isoformat() if w.completed_at else None,
            created_by=w.created_by,
            error_message=w.error_message,
        )
        for w in workflows
    ]


@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Démarrer un workflow",
    description="Démarre un nouveau workflow.",
)
async def start_workflow(
    request: StartWorkflowRequest,
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """
    Démarre un workflow.

    Types disponibles:
    - **invoice_processing**: Traitement de facture
    - **payment_approval**: Approbation de paiement
    - **reconciliation**: Rapprochement
    - **month_end_close**: Clôture mensuelle
    - **expense_report**: Note de frais
    """
    workflow = await service.start_workflow(
        workflow_type=request.workflow_type,
        data=request.data,
        created_by=request.created_by,
    )

    return WorkflowResponse(
        id=workflow.id,
        workflow_type=workflow.workflow_type.value,
        status=workflow.status.value,
        current_step=workflow.current_step,
        total_steps=workflow.total_steps,
        data=workflow.data,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat(),
        created_by=workflow.created_by,
    )


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Détails d'un workflow",
    description="Retourne les détails d'un workflow.",
)
async def get_workflow(
    workflow_id: str,
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Détails d'un workflow."""
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow non trouvé",
        )

    return WorkflowResponse(
        id=workflow.id,
        workflow_type=workflow.workflow_type.value,
        status=workflow.status.value,
        current_step=workflow.current_step,
        total_steps=workflow.total_steps,
        data=workflow.data,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        created_by=workflow.created_by,
        error_message=workflow.error_message,
    )


@router.post(
    "/workflows/{workflow_id}/advance",
    response_model=WorkflowResponse,
    summary="Avancer un workflow",
    description="Avance un workflow à l'étape suivante.",
)
async def advance_workflow(
    workflow_id: str,
    request: AdvanceWorkflowRequest = AdvanceWorkflowRequest(),
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Avance un workflow."""
    workflow = await service.advance_workflow(workflow_id, request.step_data)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow non trouvé",
        )

    return WorkflowResponse(
        id=workflow.id,
        workflow_type=workflow.workflow_type.value,
        status=workflow.status.value,
        current_step=workflow.current_step,
        total_steps=workflow.total_steps,
        data=workflow.data,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        created_by=workflow.created_by,
    )


@router.post(
    "/workflows/{workflow_id}/cancel",
    response_model=dict,
    summary="Annuler un workflow",
    description="Annule un workflow en cours.",
)
async def cancel_workflow(
    workflow_id: str,
    request: CancelWorkflowRequest = CancelWorkflowRequest(),
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Annule un workflow."""
    success = await service.cancel_workflow(workflow_id, request.reason)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow non trouvé",
        )

    return {"success": True, "message": "Workflow annulé"}


# =============================================================================
# ENDPOINTS - REPORTING
# =============================================================================


@router.get(
    "/summary",
    summary="Résumé financier",
    description="Retourne le résumé financier pour une période.",
)
async def get_finance_summary(
    start_date: date = Query(..., description="Date de début"),
    end_date: date = Query(..., description="Date de fin"),
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Résumé financier pour une période."""
    return await service.get_finance_summary(start_date, end_date)


@router.get(
    "/kpis",
    summary="KPIs finance",
    description="Retourne les indicateurs clés de performance finance.",
)
async def get_kpis(
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """KPIs finance."""
    return await service.get_kpis()


# =============================================================================
# ENDPOINTS - HEALTH
# =============================================================================


@router.get(
    "/health",
    summary="Health check global",
    description="Retourne le health check de la suite Finance complète.",
)
async def health_check(
    service: FinanceSuiteService = Depends(get_suite_service),
):
    """Health check global de la suite Finance."""
    return await service.get_suite_health()
