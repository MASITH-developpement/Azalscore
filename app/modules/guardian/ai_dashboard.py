"""
AZALS GUARDIAN - Structures Dashboard Mode C
=============================================
Schémas et données pour le dashboard IA Guardian.

Mode C: Calcul d'indicateurs objectifs
- Données horodatées et auditables
- Agrégations pour visualisation
- Pas d'action, pas de décision
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.guardian.ai_models import (
    AIAuditReport,
    AIIncident,
    AIModuleScore,
    AISLAMetric,
    IncidentSeverity,
    IncidentStatus,
)


# =============================================================================
# SCHEMAS DASHBOARD
# =============================================================================

class DashboardKPI(BaseModel):
    """KPI individuel pour le dashboard."""
    id: str
    label: str
    value: float
    unit: Optional[str] = None
    trend: float = 0  # % variation par rapport à période précédente
    status: str = "green"  # green, yellow, red
    target: Optional[float] = None


class IncidentSummary(BaseModel):
    """Résumé des incidents."""
    total_24h: int = 0
    total_7d: int = 0
    total_30d: int = 0
    critical_open: int = 0
    high_open: int = 0
    by_module: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    resolution_rate: float = 0.0


class SLASummary(BaseModel):
    """Résumé SLA."""
    current_uptime: float = 99.9
    target_uptime: float = 99.9
    status: str = "green"
    downtime_today_min: int = 0
    avg_resolution_ms: Optional[int] = None
    rollback_rate: float = 0.0
    tenant_isolation: bool = True
    data_integrity: float = 100.0


class ModuleHealth(BaseModel):
    """Santé d'un module."""
    module: str
    score: int = 100
    status: str = "healthy"  # healthy, warning, critical
    incidents_24h: int = 0
    last_incident: Optional[datetime] = None
    trend: str = "stable"  # improving, stable, degrading


class ChartDataPoint(BaseModel):
    """Point de données pour graphique."""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class AlertItem(BaseModel):
    """Alerte dashboard."""
    id: str
    severity: str
    title: str
    description: str
    module: Optional[str] = None
    timestamp: datetime
    action_required: bool = False


class AIGuardianDashboard(BaseModel):
    """Données complètes du dashboard AI Guardian."""
    # Timestamp de génération
    generated_at: datetime
    tenant_id: Optional[str] = None

    # KPIs principaux
    kpis: List[DashboardKPI] = Field(default_factory=list)

    # Résumés
    incidents: IncidentSummary = Field(default_factory=IncidentSummary)
    sla: SLASummary = Field(default_factory=SLASummary)

    # Santé des modules
    modules: List[ModuleHealth] = Field(default_factory=list)

    # Alertes actives
    alerts: List[AlertItem] = Field(default_factory=list)

    # Données pour graphiques
    uptime_history: List[ChartDataPoint] = Field(default_factory=list)
    incidents_history: List[ChartDataPoint] = Field(default_factory=list)
    resolution_time_history: List[ChartDataPoint] = Field(default_factory=list)

    # Dernier audit
    last_audit: Optional[Dict[str, Any]] = None


# =============================================================================
# GÉNÉRATEUR DASHBOARD
# =============================================================================

class DashboardGenerator:
    """
    Génère les données du dashboard Mode C.

    Mode C = Calcul uniquement:
    - Pas d'action
    - Pas de décision
    - Données objectives et auditables
    """

    def __init__(self, db: Session, tenant_id: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.now = datetime.utcnow()

    def generate(self) -> AIGuardianDashboard:
        """Génère le dashboard complet."""
        return AIGuardianDashboard(
            generated_at=self.now,
            tenant_id=self.tenant_id,
            kpis=self._generate_kpis(),
            incidents=self._generate_incident_summary(),
            sla=self._generate_sla_summary(),
            modules=self._generate_module_health(),
            alerts=self._generate_alerts(),
            uptime_history=self._generate_uptime_history(),
            incidents_history=self._generate_incidents_history(),
            resolution_time_history=self._generate_resolution_history(),
            last_audit=self._get_last_audit(),
        )

    def _base_query(self, model):
        """Query de base avec filtre tenant."""
        query = self.db.query(model)
        if self.tenant_id:
            query = query.filter(model.tenant_id == self.tenant_id)
        return query

    def _generate_kpis(self) -> List[DashboardKPI]:
        """Génère les KPIs principaux."""
        kpis = []

        # KPI 1: Uptime
        latest_sla = self._base_query(AISLAMetric).order_by(
            AISLAMetric.calculated_at.desc()
        ).first()

        uptime = latest_sla.uptime_percent if latest_sla else 99.9
        kpis.append(DashboardKPI(
            id="uptime",
            label="Disponibilité",
            value=uptime,
            unit="%",
            target=99.9,
            status="green" if uptime >= 99.9 else ("yellow" if uptime >= 99.0 else "red")
        ))

        # KPI 2: Incidents critiques ouverts
        critical_open = self._base_query(AIIncident).filter(
            AIIncident.severity == IncidentSeverity.CRITICAL.value,
            AIIncident.status.notin_([IncidentStatus.FIXED.value, IncidentStatus.IGNORED.value])
        ).count()

        kpis.append(DashboardKPI(
            id="critical_incidents",
            label="Incidents Critiques",
            value=critical_open,
            status="green" if critical_open == 0 else "red"
        ))

        # KPI 3: Score moyen des modules
        scores = self._base_query(AIModuleScore).filter(
            AIModuleScore.calculated_at >= self.now - timedelta(days=7)
        ).all()

        avg_score = sum(s.score_total for s in scores) / len(scores) if scores else 100
        kpis.append(DashboardKPI(
            id="avg_module_score",
            label="Score Moyen",
            value=round(avg_score, 1),
            unit="/100",
            target=90,
            status="green" if avg_score >= 90 else ("yellow" if avg_score >= 70 else "red")
        ))

        # KPI 4: Temps de résolution moyen
        resolution_ms = latest_sla.avg_resolution_time_ms if latest_sla else None
        if resolution_ms:
            kpis.append(DashboardKPI(
                id="avg_resolution",
                label="Résolution Moyenne",
                value=resolution_ms / 1000,  # Convert to seconds
                unit="s",
                target=30,
                status="green" if resolution_ms <= 30000 else ("yellow" if resolution_ms <= 60000 else "red")
            ))

        return kpis

    def _generate_incident_summary(self) -> IncidentSummary:
        """Génère le résumé des incidents."""
        now = self.now
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        base = self._base_query(AIIncident)

        # Comptages par période
        total_24h = base.filter(AIIncident.created_at >= day_ago).count()
        total_7d = base.filter(AIIncident.created_at >= week_ago).count()
        total_30d = base.filter(AIIncident.created_at >= month_ago).count()

        # Incidents critiques/high ouverts
        open_statuses = [IncidentStatus.DETECTED.value, IncidentStatus.ANALYZING.value]
        critical_open = base.filter(
            AIIncident.severity == IncidentSeverity.CRITICAL.value,
            AIIncident.status.in_(open_statuses)
        ).count()
        high_open = base.filter(
            AIIncident.severity == IncidentSeverity.HIGH.value,
            AIIncident.status.in_(open_statuses)
        ).count()

        # Par module (30 derniers jours)
        by_module = {}
        module_counts = self.db.query(
            AIIncident.module,
            func.count(AIIncident.id)
        ).filter(
            AIIncident.created_at >= month_ago
        )
        if self.tenant_id:
            module_counts = module_counts.filter(AIIncident.tenant_id == self.tenant_id)
        module_counts = module_counts.group_by(AIIncident.module).all()

        for module, count in module_counts:
            by_module[module] = count

        # Par type
        by_type = {}
        type_counts = self.db.query(
            AIIncident.incident_type,
            func.count(AIIncident.id)
        ).filter(
            AIIncident.created_at >= month_ago
        )
        if self.tenant_id:
            type_counts = type_counts.filter(AIIncident.tenant_id == self.tenant_id)
        type_counts = type_counts.group_by(AIIncident.incident_type).all()

        for inc_type, count in type_counts:
            by_type[inc_type] = count

        # Taux de résolution
        total = base.filter(AIIncident.created_at >= month_ago).count()
        resolved = base.filter(
            AIIncident.created_at >= month_ago,
            AIIncident.status.in_([IncidentStatus.FIXED.value, IncidentStatus.ROLLBACK.value])
        ).count()
        resolution_rate = (resolved / total * 100) if total > 0 else 100.0

        return IncidentSummary(
            total_24h=total_24h,
            total_7d=total_7d,
            total_30d=total_30d,
            critical_open=critical_open,
            high_open=high_open,
            by_module=by_module,
            by_type=by_type,
            resolution_rate=round(resolution_rate, 1)
        )

    def _generate_sla_summary(self) -> SLASummary:
        """Génère le résumé SLA."""
        latest_sla = self._base_query(AISLAMetric).order_by(
            AISLAMetric.calculated_at.desc()
        ).first()

        if not latest_sla:
            return SLASummary()

        uptime = latest_sla.uptime_percent or 99.9
        status = "green" if uptime >= 99.9 else ("yellow" if uptime >= 99.0 else "red")

        return SLASummary(
            current_uptime=uptime,
            target_uptime=99.9,
            status=status,
            downtime_today_min=latest_sla.downtime_minutes,
            avg_resolution_ms=latest_sla.avg_resolution_time_ms,
            rollback_rate=latest_sla.rollback_rate or 0.0,
            tenant_isolation=latest_sla.tenant_isolation_verified,
            data_integrity=latest_sla.data_integrity_score or 100.0
        )

    def _generate_module_health(self) -> List[ModuleHealth]:
        """Génère la santé des modules."""
        modules = []
        day_ago = self.now - timedelta(days=1)

        # Récupérer les scores récents (derniers 7 jours)
        scores = self._base_query(AIModuleScore).filter(
            AIModuleScore.calculated_at >= self.now - timedelta(days=7)
        ).order_by(AIModuleScore.calculated_at.desc()).all()

        # Dédupliquer par module
        seen = set()
        for score in scores:
            if score.module in seen:
                continue
            seen.add(score.module)

            # Comptage incidents 24h pour ce module
            incidents_24h = self._base_query(AIIncident).filter(
                AIIncident.module == score.module,
                AIIncident.created_at >= day_ago
            ).count()

            # Déterminer le statut
            if score.score_total >= 90:
                status = "healthy"
            elif score.score_total >= 70:
                status = "warning"
            else:
                status = "critical"

            modules.append(ModuleHealth(
                module=score.module,
                score=score.score_total,
                status=status,
                incidents_24h=incidents_24h,
                last_incident=score.last_incident_at,
                trend="stable"  # TODO: calculer la tendance
            ))

        return modules

    def _generate_alerts(self) -> List[AlertItem]:
        """Génère les alertes actives."""
        alerts = []

        # Alertes pour incidents critiques non résolus
        critical_incidents = self._base_query(AIIncident).filter(
            AIIncident.severity == IncidentSeverity.CRITICAL.value,
            AIIncident.status.in_([IncidentStatus.DETECTED.value, IncidentStatus.ANALYZING.value])
        ).order_by(AIIncident.created_at.desc()).limit(5).all()

        for inc in critical_incidents:
            alerts.append(AlertItem(
                id=inc.incident_uid,
                severity="critical",
                title=f"Incident critique: {inc.error_type}",
                description=inc.error_message[:200] if inc.error_message else "Détails non disponibles",
                module=inc.module,
                timestamp=inc.created_at,
                action_required=True
            ))

        # Alerte si uptime < 99%
        latest_sla = self._base_query(AISLAMetric).order_by(
            AISLAMetric.calculated_at.desc()
        ).first()

        if latest_sla and latest_sla.uptime_percent and latest_sla.uptime_percent < 99.0:
            alerts.append(AlertItem(
                id=f"sla-uptime-{latest_sla.metric_uid}",
                severity="high",
                title="SLA Uptime dégradé",
                description=f"Uptime actuel: {latest_sla.uptime_percent:.2f}% (cible: 99.9%)",
                timestamp=latest_sla.calculated_at,
                action_required=True
            ))

        # Alerte si score module < 70
        low_scores = self._base_query(AIModuleScore).filter(
            AIModuleScore.score_total < 70,
            AIModuleScore.calculated_at >= self.now - timedelta(days=1)
        ).all()

        for score in low_scores:
            alerts.append(AlertItem(
                id=f"score-{score.module}-{score.id}",
                severity="warning",
                title=f"Score module bas: {score.module}",
                description=f"Score: {score.score_total}/100 - Investigation recommandée",
                module=score.module,
                timestamp=score.calculated_at,
                action_required=False
            ))

        return alerts[:10]  # Limiter à 10 alertes

    def _generate_uptime_history(self) -> List[ChartDataPoint]:
        """Génère l'historique uptime pour graphique."""
        history = []
        metrics = self._base_query(AISLAMetric).filter(
            AISLAMetric.period_type == "daily",
            AISLAMetric.period_start >= self.now - timedelta(days=30)
        ).order_by(AISLAMetric.period_start).all()

        for metric in metrics:
            history.append(ChartDataPoint(
                timestamp=metric.period_start,
                value=metric.uptime_percent or 99.9,
                label=metric.period_start.strftime("%d/%m")
            ))

        return history

    def _generate_incidents_history(self) -> List[ChartDataPoint]:
        """Génère l'historique des incidents pour graphique."""
        history = []

        # Grouper par jour sur 30 jours
        for i in range(30, -1, -1):
            day = self.now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            count = self._base_query(AIIncident).filter(
                AIIncident.created_at >= day_start,
                AIIncident.created_at < day_end
            ).count()

            history.append(ChartDataPoint(
                timestamp=day_start,
                value=count,
                label=day_start.strftime("%d/%m")
            ))

        return history

    def _generate_resolution_history(self) -> List[ChartDataPoint]:
        """Génère l'historique temps de résolution."""
        history = []
        metrics = self._base_query(AISLAMetric).filter(
            AISLAMetric.period_type == "daily",
            AISLAMetric.period_start >= self.now - timedelta(days=30),
            AISLAMetric.avg_resolution_time_ms.isnot(None)
        ).order_by(AISLAMetric.period_start).all()

        for metric in metrics:
            if metric.avg_resolution_time_ms:
                history.append(ChartDataPoint(
                    timestamp=metric.period_start,
                    value=metric.avg_resolution_time_ms / 1000,  # En secondes
                    label=metric.period_start.strftime("%d/%m")
                ))

        return history

    def _get_last_audit(self) -> Optional[Dict[str, Any]]:
        """Récupère le dernier rapport d'audit."""
        report = self._base_query(AIAuditReport).filter(
            AIAuditReport.status == "completed"
        ).order_by(AIAuditReport.completed_at.desc()).first()

        if not report:
            return None

        return {
            "report_uid": report.report_uid,
            "period": f"{report.audit_year}-{report.audit_month:02d}",
            "status": report.status,
            "modules_audited": report.modules_audited,
            "total_incidents": report.total_incidents,
            "critical_incidents": report.critical_incidents,
            "avg_score": report.avg_score,
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            "risks_p1": len(report.risks_identified.get("P1", [])) if report.risks_identified else 0,
            "risks_p2": len(report.risks_identified.get("P2", [])) if report.risks_identified else 0,
        }


# =============================================================================
# FONCTION HELPER
# =============================================================================

def get_ai_dashboard(db: Session, tenant_id: Optional[str] = None) -> AIGuardianDashboard:
    """
    Génère le dashboard AI Guardian Mode C.

    Args:
        db: Session SQLAlchemy
        tenant_id: Tenant spécifique ou None pour global

    Returns:
        AIGuardianDashboard: Données complètes du dashboard
    """
    generator = DashboardGenerator(db, tenant_id)
    return generator.generate()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "DashboardKPI",
    "IncidentSummary",
    "SLASummary",
    "ModuleHealth",
    "ChartDataPoint",
    "AlertItem",
    "AIGuardianDashboard",
    "DashboardGenerator",
    "get_ai_dashboard",
]
