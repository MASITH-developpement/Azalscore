"""
AZALS GUARDIAN - Router API IA
==============================
Endpoints pour le système de monitoring IA.

Endpoints:
- POST /guardian/ai/incident - Signaler un incident (Mode A)
- GET /guardian/ai/incidents - Liste des incidents
- GET /guardian/ai/incidents/{uid} - Détail incident
- POST /guardian/ai/audit - Lancer audit mensuel (Mode B)
- GET /guardian/ai/audit/{uid} - Rapport d'audit
- POST /guardian/ai/sla - Calculer métriques SLA (Mode C)
- GET /guardian/ai/sla/latest - Dernières métriques SLA
- GET /guardian/ai/dashboard - Données dashboard
- GET /guardian/ai/scores - Scores des modules
"""
from __future__ import annotations


from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.modules.guardian.ai_service import (
    AIGuardianService,
    get_ai_guardian_service,
)
from app.modules.guardian.ai_models import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/guardian/ai", tags=["AI Guardian"])


# =============================================================================
# SCHEMAS
# =============================================================================

class IncidentCreateSchema(BaseModel):
    """Schema pour créer un incident."""
    error_type: str = Field(..., description="Type d'erreur (ValueError, etc.)")
    error_message: str = Field(..., description="Message d'erreur")
    module: str = Field(..., description="Module source")
    endpoint: Optional[str] = Field(None, description="Endpoint concerné")
    method: Optional[str] = Field(None, description="Méthode HTTP")
    http_status: Optional[int] = Field(None, description="Code HTTP")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    context_data: Optional[dict] = Field(None, description="Données contextuelles")


class IncidentResponseSchema(BaseModel):
    """Schema de réponse incident."""
    id: int
    incident_uid: str
    tenant_id: Optional[str]
    module: str
    endpoint: Optional[str]
    error_type: str
    error_message: Optional[str]
    http_status: Optional[int]
    incident_type: str
    severity: str
    status: str
    duration_ms: Optional[int]
    action_taken: Optional[str]
    auto_resolved: bool
    requires_human: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditRequestSchema(BaseModel):
    """Schema pour demander un audit."""
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)


class AuditResponseSchema(BaseModel):
    """Schema de réponse audit."""
    id: int
    report_uid: str
    tenant_id: Optional[str]
    audit_year: int
    audit_month: int
    status: str
    modules_audited: int
    total_incidents: int
    critical_incidents: int
    avg_score: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    module_reports: Optional[dict]
    risks_identified: Optional[dict]
    recommendations: Optional[list]

    class Config:
        from_attributes = True


class SLARequestSchema(BaseModel):
    """Schema pour calculer SLA."""
    period_type: str = Field("daily", description="hourly, daily, weekly, monthly")


class SLAResponseSchema(BaseModel):
    """Schema de réponse SLA."""
    id: int
    metric_uid: str
    tenant_id: Optional[str]
    period_type: str
    period_start: datetime
    period_end: datetime
    uptime_percent: Optional[float]
    downtime_minutes: int
    avg_resolution_time_ms: Optional[int]
    total_incidents: int
    rollback_count: int
    rollback_rate: Optional[float]
    security_incidents: int
    tenant_isolation_verified: bool
    data_integrity_score: Optional[float]
    calculated_at: datetime

    class Config:
        from_attributes = True


class ModuleScoreSchema(BaseModel):
    """Schema score module."""
    module: str
    score_total: int
    score_errors: int
    score_performance: int
    score_data: int
    score_security: int
    score_stability: int
    incidents_total: int
    incidents_critical: int
    incidents_resolved: int
    last_incident_at: Optional[datetime]

    class Config:
        from_attributes = True


class DashboardSchema(BaseModel):
    """Schema données dashboard."""
    incidents_24h: int
    critical_open: int
    avg_module_score: float
    uptime_percent: float
    last_updated: str


# =============================================================================
# HELPERS
# =============================================================================

def get_service(request: Request, db: Session = Depends(get_db)) -> AIGuardianService:
    """Factory pour le service."""
    tenant_id = getattr(request.state, "tenant_id", None)
    return get_ai_guardian_service(db, tenant_id)


# =============================================================================
# MODE A - INCIDENTS
# =============================================================================

@router.post("/incident", response_model=IncidentResponseSchema)
async def create_incident(
    data: IncidentCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    MODE A: Signale un nouvel incident.

    Endpoint appelé automatiquement par le middleware Guardian
    lors de la détection d'une erreur 4xx/5xx.

    Ne nécessite pas d'authentification (appel interne).
    """
    logger.info("[AI_ROUTER] Incident signalé: %s dans %s", data.error_type, data.module)

    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_ai_guardian_service(db, tenant_id)

    incident = service.detect_incident(
        error_type=data.error_type,
        error_message=data.error_message,
        module=data.module,
        endpoint=data.endpoint,
        method=data.method,
        http_status=data.http_status,
        stack_trace=data.stack_trace,
        context_data=data.context_data,
    )

    return incident


@router.get("/incidents", response_model=List[IncidentResponseSchema])
async def list_incidents(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None, description="critical, high, medium, low"),
    status: Optional[str] = Query(None, description="detected, analyzing, fixed, rollback, failed"),
):
    """
    Liste les incidents récents.

    Filtres disponibles:
    - severity: Filtrer par sévérité
    - status: Filtrer par statut
    """
    service = get_service(request, db)

    sev = IncidentSeverity(severity) if severity else None
    stat = IncidentStatus(status) if status else None

    incidents = service.get_recent_incidents(
        limit=limit,
        severity=sev,
        status=stat,
    )

    return incidents


@router.get("/incidents/{incident_uid}", response_model=IncidentResponseSchema)
async def get_incident(
    incident_uid: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Récupère le détail d'un incident."""
    service = get_service(request, db)
    incident = service.get_incident(incident_uid)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")

    return incident


# =============================================================================
# MODE B - AUDIT
# =============================================================================

@router.post("/audit", response_model=AuditResponseSchema)
async def run_audit(
    data: AuditRequestSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    MODE B: Lance un audit mensuel.

    LECTURE SEULE - Aucune modification système.

    Génère un rapport avec:
    - Score de fiabilité par module
    - Risques identifiés (P1/P2/P3)
    - Dette technique estimée
    - Recommandations (sans action)
    """
    logger.info("[AI_ROUTER] Audit demandé: %s-%s", data.year, data.month)

    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_ai_guardian_service(db, tenant_id)

    report = service.run_monthly_audit(
        year=data.year,
        month=data.month,
        tenant_id=tenant_id,
    )

    return report


@router.get("/audit/{report_uid}", response_model=AuditResponseSchema)
async def get_audit_report(
    report_uid: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Récupère un rapport d'audit."""
    from app.modules.guardian.ai_models import AIAuditReport

    # SÉCURITÉ: tenant_id OBLIGATOIRE pour cette route
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requis")

    report = db.query(AIAuditReport).filter(
        AIAuditReport.tenant_id == tenant_id,
        AIAuditReport.report_uid == report_uid
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")

    return report


@router.get("/audits", response_model=List[AuditResponseSchema])
async def list_audits(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    limit: int = Query(12, ge=1, le=50),
):
    """Liste les rapports d'audit."""
    from app.modules.guardian.ai_models import AIAuditReport

    # SÉCURITÉ: tenant_id OBLIGATOIRE pour cette route
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requis")

    reports = db.query(AIAuditReport).filter(
        AIAuditReport.tenant_id == tenant_id
    ).order_by(AIAuditReport.created_at.desc()).limit(limit).all()

    return reports


# =============================================================================
# MODE C - SLA
# =============================================================================

@router.post("/sla", response_model=SLAResponseSchema)
async def calculate_sla(
    data: SLARequestSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    MODE C: Calcule les métriques SLA.

    Indicateurs objectifs et auditables:
    - Disponibilité réelle (% uptime)
    - Temps moyen de détection/correction
    - Taux de rollback
    - Incidents par module
    - Isolation multi-tenant
    - Intégrité des données
    """
    logger.info("[AI_ROUTER] Calcul SLA: %s", data.period_type)

    service = get_service(request, db)

    metric = service.calculate_sla_metrics(
        period_type=data.period_type,
    )

    return metric


@router.get("/sla/latest", response_model=SLAResponseSchema)
async def get_latest_sla(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    period_type: str = Query("daily", description="hourly, daily, weekly, monthly"),
):
    """Récupère les dernières métriques SLA."""
    from app.modules.guardian.ai_models import AISLAMetric

    # SÉCURITÉ: tenant_id OBLIGATOIRE pour cette route
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requis")

    metric = db.query(AISLAMetric).filter(
        AISLAMetric.tenant_id == tenant_id,
        AISLAMetric.period_type == period_type
    ).order_by(AISLAMetric.calculated_at.desc()).first()

    if not metric:
        raise HTTPException(status_code=404, detail="Aucune métrique SLA disponible")

    return metric


@router.get("/sla/history", response_model=List[SLAResponseSchema])
async def get_sla_history(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    period_type: str = Query("daily", description="hourly, daily, weekly, monthly"),
    limit: int = Query(30, ge=1, le=100),
):
    """Historique des métriques SLA."""
    from app.modules.guardian.ai_models import AISLAMetric

    # SÉCURITÉ: tenant_id OBLIGATOIRE pour cette route
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requis")

    metrics = db.query(AISLAMetric).filter(
        AISLAMetric.tenant_id == tenant_id,
        AISLAMetric.period_type == period_type
    ).order_by(AISLAMetric.period_start.desc()).limit(limit).all()

    return metrics


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=DashboardSchema)
async def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Données pour le dashboard IA Guardian.

    Retourne:
    - Incidents dernières 24h
    - Incidents critiques ouverts
    - Score moyen des modules
    - Uptime
    """
    service = get_service(request, db)
    return service.get_dashboard_data()


@router.get("/scores", response_model=List[ModuleScoreSchema])
async def get_module_scores(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste les scores de tous les modules."""
    from app.modules.guardian.ai_models import AIModuleScore
    from datetime import timedelta

    # SÉCURITÉ: tenant_id OBLIGATOIRE pour cette route
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requis")

    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)

    # TOUJOURS filtrer par tenant_id
    scores = db.query(AIModuleScore).filter(
        AIModuleScore.tenant_id == tenant_id,
        AIModuleScore.calculated_at >= month_ago
    ).order_by(AIModuleScore.calculated_at.desc()).all()

    # Dédupliquer par module
    seen = set()
    unique_scores = []
    for score in scores:
        if score.module not in seen:
            seen.add(score.module)
            unique_scores.append(score)

    return unique_scores


@router.post("/scores/{module}/recalculate", response_model=ModuleScoreSchema)
async def recalculate_module_score(
    module: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Recalcule le score d'un module."""
    service = get_service(request, db)
    score = service.calculate_module_score(module)
    return score


# =============================================================================
# DASHBOARD COMPLET MODE C
# =============================================================================

@router.get("/dashboard/full")
async def get_full_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    MODE C: Dashboard complet AI Guardian.

    Retourne toutes les données nécessaires pour afficher
    un dashboard de monitoring IA complet:
    - KPIs principaux (uptime, incidents, scores)
    - Résumé des incidents
    - Résumé SLA
    - Santé des modules
    - Alertes actives
    - Historiques pour graphiques (30 jours)
    - Dernier rapport d'audit

    Données objectives, horodatées et auditables.
    """
    from app.modules.guardian.ai_dashboard import get_ai_dashboard

    tenant_id = getattr(request.state, "tenant_id", None)
    dashboard = get_ai_dashboard(db, tenant_id)

    return dashboard.model_dump()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["router"]
