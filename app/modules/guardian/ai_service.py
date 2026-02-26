"""
AZALS GUARDIAN - Service IA Monitoring
======================================
Service principal pour les 3 modes d'exécution IA.

MODE A: Intervention sur bug réel (réactif)
MODE B: Audit mensuel passif (lecture seule)
MODE C: Calcul SLA/Enterprise (métriques)

RÈGLES:
- IA réactive, non permanente
- Déclenchée par événement uniquement
- Arrêt obligatoire après chaque intervention
"""
from __future__ import annotations


import hashlib
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.modules.guardian.ai_models import (
    AIIncident,
    AIModuleScore,
    AIAuditReport,
    AISLAMetric,
    AIConfig,
    IncidentType,
    IncidentStatus,
    IncidentSeverity,
    AuditStatus,
)

logger = get_logger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

# Seuils de scoring
SCORE_WEIGHTS = {
    "errors": 30,      # Aucune erreur critique récente
    "performance": 20,  # Temps de réponse acceptable
    "data": 20,        # Données cohérentes
    "security": 20,    # Sécurité intacte
    "stability": 10,   # Stabilité post-correction
}

# Mapping HTTP status -> Severity
HTTP_SEVERITY_MAP = {
    range(500, 600): IncidentSeverity.CRITICAL,
    range(400, 500): IncidentSeverity.MEDIUM,
}

# Modules critiques (severity automatiquement élevée)
CRITICAL_MODULES = {"auth", "tenants", "billing", "security", "guardian"}


# =============================================================================
# SERVICE PRINCIPAL
# =============================================================================

class AIGuardianService:
    """
    Service IA Guardian pour monitoring automatisé.

    Usage:
        service = AIGuardianService(db)

        # Mode A - Incident
        incident = service.detect_incident(error_data)

        # Mode B - Audit
        report = service.run_monthly_audit(year=2026, month=1)

        # Mode C - SLA
        metrics = service.calculate_sla_metrics(period="daily")
    """

    def __init__(self, db: Session, tenant_id: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # MODE A - DÉTECTION ET TRAITEMENT INCIDENTS
    # =========================================================================

    def detect_incident(
        self,
        error_type: str,
        error_message: str,
        module: str,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        http_status: Optional[int] = None,
        stack_trace: Optional[str] = None,
        context_data: Optional[Dict] = None,
    ) -> AIIncident:
        """
        MODE A: Détecte et enregistre un incident.

        Args:
            error_type: Type d'erreur (ValueError, TypeError, etc.)
            error_message: Message d'erreur
            module: Module source de l'erreur
            endpoint: Endpoint concerné
            method: Méthode HTTP
            http_status: Code HTTP
            stack_trace: Trace complète
            context_data: Données contextuelles

        Returns:
            AIIncident créé
        """
        logger.info("[AI_GUARDIAN] MODE A - Détection incident: %s dans %s", error_type, module)

        # Générer signature unique pour déduplication
        signature = self._generate_error_signature(error_type, error_message, module)

        # Vérifier si incident similaire récent (< 5 min)
        recent = self._find_recent_similar_incident(signature)
        if recent:
            logger.debug("[AI_GUARDIAN] Incident similaire récent ignoré: %s", recent.incident_uid)
            return recent

        # Déterminer sévérité
        severity = self._determine_severity(http_status, module, error_type)

        # Déterminer type d'incident
        incident_type = self._determine_incident_type(module, error_type)

        # Créer l'incident
        incident = AIIncident(
            incident_uid=f"INC-{uuid.uuid4().hex[:12].upper()}",
            tenant_id=self.tenant_id,
            module=module,
            endpoint=endpoint,
            method=method,
            error_signature=signature,
            error_type=error_type,
            error_message=error_message[:2000] if error_message else None,
            stack_trace=stack_trace[:10000] if stack_trace else None,
            http_status=http_status,
            incident_type=incident_type.value,
            severity=severity.value,
            status=IncidentStatus.DETECTED.value,
            context_data=context_data,
            created_at=datetime.utcnow(),
        )

        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        logger.info(
            "[AI_GUARDIAN] Incident créé: %s "
            "(severity=%s, module=%s)",
            incident.incident_uid, severity.value, module
        )

        # Mettre à jour le score du module
        self._update_module_score_on_incident(module, severity)

        return incident

    def start_analysis(self, incident_id: int) -> AIIncident:
        """Marque le début de l'analyse d'un incident."""
        # SÉCURITÉ: Toujours filtrer par tenant_id
        incident = self.db.query(AIIncident).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.id == incident_id
        ).first()
        if incident:
            incident.status = IncidentStatus.ANALYZING.value
            incident.analysis_started_at = datetime.utcnow()
            self.db.commit()
            logger.info("[AI_GUARDIAN] Analyse démarrée: %s", incident.incident_uid)
        return incident

    def complete_analysis(
        self,
        incident_id: int,
        status: IncidentStatus,
        action_taken: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        git_branch: Optional[str] = None,
        git_commit: Optional[str] = None,
        rollback_performed: bool = False,
        auto_resolved: bool = False,
        requires_human: bool = False,
    ) -> AIIncident:
        """
        Finalise l'analyse d'un incident.

        Args:
            incident_id: ID de l'incident
            status: Statut final (fixed, rollback, failed)
            action_taken: Description de l'action
            resolution_notes: Notes de résolution
            git_branch: Branche git créée
            git_commit: Commit de correction
            rollback_performed: Si rollback effectué
            auto_resolved: Si résolu automatiquement
            requires_human: Si intervention humaine requise

        Returns:
            Incident mis à jour
        """
        # SÉCURITÉ: Toujours filtrer par tenant_id
        incident = self.db.query(AIIncident).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.id == incident_id
        ).first()
        if not incident:
            return None

        now = datetime.utcnow()
        incident.status = status.value
        incident.analysis_completed_at = now
        incident.action_taken = action_taken
        incident.resolution_notes = resolution_notes
        incident.git_branch = git_branch
        incident.git_commit = git_commit
        incident.rollback_performed = rollback_performed
        incident.auto_resolved = auto_resolved
        incident.requires_human = requires_human

        # Calculer durée
        if incident.analysis_started_at:
            duration = (now - incident.analysis_started_at).total_seconds() * 1000
            incident.duration_ms = int(duration)

        self.db.commit()

        logger.info(
            "[AI_GUARDIAN] Analyse terminée: %s "
            "(status=%s, duration=%sms)",
            incident.incident_uid, status.value, incident.duration_ms
        )

        return incident

    def _generate_error_signature(
        self,
        error_type: str,
        error_message: str,
        module: str
    ) -> str:
        """Génère une signature unique pour déduplication."""
        # Nettoyer le message (enlever IDs, timestamps, etc.)
        clean_message = error_message[:100] if error_message else ""
        raw = f"{error_type}:{module}:{clean_message}"
        # NOTE: MD5 utilisé uniquement pour fingerprinting/déduplication, pas pour sécurité
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()[:16]

    def _find_recent_similar_incident(
        self,
        signature: str,
        minutes: int = 5
    ) -> Optional[AIIncident]:
        """Trouve un incident similaire récent."""
        threshold = datetime.utcnow() - timedelta(minutes=minutes)
        # SÉCURITÉ: Toujours filtrer par tenant_id
        return self.db.query(AIIncident).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.error_signature == signature,
            AIIncident.created_at >= threshold,
        ).first()

    def _determine_severity(
        self,
        http_status: Optional[int],
        module: str,
        error_type: str
    ) -> IncidentSeverity:
        """Détermine la sévérité de l'incident."""
        # Modules critiques = toujours HIGH minimum
        if module.lower() in CRITICAL_MODULES:
            if http_status and http_status >= 500:
                return IncidentSeverity.CRITICAL
            return IncidentSeverity.HIGH

        # Basé sur HTTP status
        if http_status:
            if http_status >= 500:
                return IncidentSeverity.CRITICAL
            if http_status >= 400:
                return IncidentSeverity.MEDIUM

        # Erreurs de sécurité
        security_errors = {"PermissionError", "AuthenticationError", "SecurityError"}
        if error_type in security_errors:
            return IncidentSeverity.HIGH

        return IncidentSeverity.MEDIUM

    def _determine_incident_type(
        self,
        module: str,
        error_type: str
    ) -> IncidentType:
        """Détermine le type d'incident."""
        module_lower = module.lower()

        if module_lower in {"auth", "security", "guardian"}:
            return IncidentType.SECURITY
        if "data" in error_type.lower() or "integrity" in error_type.lower():
            return IncidentType.DATA
        if "timeout" in error_type.lower() or "performance" in module_lower:
            return IncidentType.PERFORMANCE
        if module_lower == "frontend":
            return IncidentType.FRONTEND

        return IncidentType.BACKEND

    # =========================================================================
    # MODE A - SCORING MODULE
    # =========================================================================

    def _update_module_score_on_incident(
        self,
        module: str,
        severity: IncidentSeverity
    ) -> None:
        """Met à jour le score du module après un incident."""
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        # Trouver ou créer le score du module
        score = self.db.query(AIModuleScore).filter(
            AIModuleScore.tenant_id == self.tenant_id,
            AIModuleScore.module == module,
            AIModuleScore.period_start == period_start,
        ).first()

        if not score:
            score = AIModuleScore(
                tenant_id=self.tenant_id,
                module=module,
                period_start=period_start,
                period_end=period_end,
            )
            self.db.add(score)

        # Incrémenter compteurs
        score.incidents_total += 1
        if severity == IncidentSeverity.CRITICAL:
            score.incidents_critical += 1

        score.last_incident_at = now

        # Recalculer score
        self._recalculate_module_score(score)

        self.db.commit()

    def _recalculate_module_score(self, score: AIModuleScore) -> None:
        """Recalcule le score total d'un module."""
        # Score erreurs (30 pts)
        if score.incidents_critical >= 3:
            score.score_errors = 0
        elif score.incidents_critical >= 1:
            score.score_errors = 15
        elif score.incidents_total >= 10:
            score.score_errors = 20
        elif score.incidents_total >= 5:
            score.score_errors = 25
        else:
            score.score_errors = 30

        # Score stabilité (10 pts)
        if score.incidents_resolved > 0:
            resolution_rate = score.incidents_resolved / max(score.incidents_total, 1)
            score.score_stability = int(resolution_rate * 10)
        else:
            score.score_stability = 5  # Par défaut

        # Total
        score.score_total = (
            score.score_errors +
            score.score_performance +
            score.score_data +
            score.score_security +
            score.score_stability
        )
        score.calculated_at = datetime.utcnow()

    def calculate_module_score(self, module: str) -> AIModuleScore:
        """
        Calcule le score complet d'un module.

        Returns:
            AIModuleScore avec tous les détails
        """
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        # Récupérer incidents du mois
        # SÉCURITÉ: Toujours filtrer par tenant_id
        incidents = self.db.query(AIIncident).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.module == module,
            AIIncident.created_at >= period_start,
            AIIncident.created_at <= period_end,
        )
        if self.tenant_id:
            incidents = incidents.filter(AIIncident.tenant_id == self.tenant_id)

        incidents = incidents.all()

        # Statistiques
        total = len(incidents)
        critical = len([i for i in incidents if i.severity == IncidentSeverity.CRITICAL.value])
        resolved = len([i for i in incidents if i.status == IncidentStatus.FIXED.value])

        # Créer/Mettre à jour score
        score = self.db.query(AIModuleScore).filter(
            AIModuleScore.tenant_id == self.tenant_id,
            AIModuleScore.module == module,
            AIModuleScore.period_start == period_start,
        ).first()

        if not score:
            score = AIModuleScore(
                tenant_id=self.tenant_id,
                module=module,
                period_start=period_start,
                period_end=period_end,
            )
            self.db.add(score)

        score.incidents_total = total
        score.incidents_critical = critical
        score.incidents_resolved = resolved

        self._recalculate_module_score(score)

        self.db.commit()
        self.db.refresh(score)

        return score

    # =========================================================================
    # MODE B - AUDIT MENSUEL
    # =========================================================================

    def run_monthly_audit(
        self,
        year: int,
        month: int,
        tenant_id: Optional[str] = None
    ) -> AIAuditReport:
        """
        MODE B: Exécute un audit mensuel PASSIF (lecture seule).

        Args:
            year: Année de l'audit
            month: Mois de l'audit (1-12)
            tenant_id: Tenant spécifique ou None pour global

        Returns:
            AIAuditReport avec le rapport complet
        """
        logger.info("[AI_GUARDIAN] MODE B - Audit mensuel %s-%s", year, month)

        # Période
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)

        # Créer le rapport
        report = AIAuditReport(
            report_uid=f"AUD-{year}{month:02d}-{uuid.uuid4().hex[:8].upper()}",
            tenant_id=tenant_id,
            audit_month=month,
            audit_year=year,
            period_start=period_start,
            period_end=period_end,
            status=AuditStatus.RUNNING.value,
            started_at=datetime.utcnow(),
        )
        self.db.add(report)
        self.db.commit()

        try:
            # Collecter données (LECTURE SEULE)
            module_reports = self._audit_all_modules(period_start, period_end, tenant_id)
            risks = self._identify_risks(module_reports)
            debt = self._estimate_technical_debt(module_reports)
            recommendations = self._generate_recommendations(module_reports, risks)

            # Calculer résumé
            report.modules_audited = len(module_reports)
            report.total_incidents = sum(m.get("incidents_total", 0) for m in module_reports.values())
            report.critical_incidents = sum(m.get("incidents_critical", 0) for m in module_reports.values())
            report.avg_score = sum(m.get("score", 100) for m in module_reports.values()) / max(len(module_reports), 1)

            # Stocker détails
            report.module_reports = module_reports
            report.risks_identified = risks
            report.technical_debt = debt
            report.recommendations = recommendations
            report.report_json = {
                "summary": {
                    "modules_audited": report.modules_audited,
                    "total_incidents": report.total_incidents,
                    "critical_incidents": report.critical_incidents,
                    "avg_score": round(report.avg_score, 2),
                },
                "modules": module_reports,
                "risks": risks,
                "technical_debt": debt,
                "recommendations": recommendations,
            }

            report.status = AuditStatus.COMPLETED.value
            report.completed_at = datetime.utcnow()

            logger.info(
                "[AI_GUARDIAN] Audit terminé: %s "
                "(%s modules, score moyen=%s)",
                report.report_uid, report.modules_audited, report.avg_score
            )

        except Exception as e:
            report.status = AuditStatus.FAILED.value
            report.completed_at = datetime.utcnow()
            logger.error("[AI_GUARDIAN] Échec audit: %s", e)

        self.db.commit()
        self.db.refresh(report)

        return report

    def _audit_all_modules(
        self,
        period_start: datetime,
        period_end: datetime,
        tenant_id: Optional[str]
    ) -> Dict[str, Dict]:
        """
        Audite tous les modules (lecture seule).

        SÉCURITÉ: Filtrage par tenant_id OBLIGATOIRE.
        Sans tenant_id, retourne un dictionnaire vide avec avertissement.
        """
        # SÉCURITÉ: Utiliser self.tenant_id par défaut si non spécifié
        effective_tenant_id = tenant_id if tenant_id is not None else self.tenant_id

        # SÉCURITÉ: Sans tenant_id, retourner vide avec avertissement
        if not effective_tenant_id:
            logger.warning(
                "[AI_SERVICE] _audit_all_modules called without tenant_id - returning empty"
            )
            return {}

        # SÉCURITÉ: Récupérer UNIQUEMENT les modules de ce tenant
        query = self.db.query(AIIncident.module).distinct().filter(
            AIIncident.tenant_id == effective_tenant_id
        )

        modules = [m[0] for m in query.all()]

        results = {}
        for module in modules:
            # SÉCURITÉ: TOUJOURS filtrer par tenant_id
            score = self.db.query(AIModuleScore).filter(
                AIModuleScore.tenant_id == effective_tenant_id,
                AIModuleScore.module == module,
                AIModuleScore.period_start >= period_start,
            ).first()

            results[module] = {
                "score": score.score_total if score else 100,
                "incidents_total": score.incidents_total if score else 0,
                "incidents_critical": score.incidents_critical if score else 0,
                "incidents_resolved": score.incidents_resolved if score else 0,
                "score_breakdown": {
                    "errors": score.score_errors if score else 30,
                    "performance": score.score_performance if score else 20,
                    "data": score.score_data if score else 20,
                    "security": score.score_security if score else 20,
                    "stability": score.score_stability if score else 10,
                } if score else None,
            }

        return results

    def _identify_risks(self, module_reports: Dict) -> Dict:
        """Identifie les risques P1/P2/P3."""
        risks = {"P1": [], "P2": [], "P3": []}

        for module, data in module_reports.items():
            score = data.get("score", 100)
            critical = data.get("incidents_critical", 0)

            if score < 50 or critical >= 3:
                risks["P1"].append({
                    "module": module,
                    "score": score,
                    "reason": "Score critique ou incidents multiples",
                })
            elif score < 70 or critical >= 1:
                risks["P2"].append({
                    "module": module,
                    "score": score,
                    "reason": "Score dégradé ou incident critique",
                })
            elif score < 85:
                risks["P3"].append({
                    "module": module,
                    "score": score,
                    "reason": "Score à surveiller",
                })

        return risks

    def _estimate_technical_debt(self, module_reports: Dict) -> Dict:
        """Estime la dette technique."""
        debt = {
            "high_debt_modules": [],
            "total_estimated_hours": 0,
        }

        for module, data in module_reports.items():
            score = data.get("score", 100)
            if score < 70:
                # Estimation grossière: (100 - score) / 10 heures de travail
                hours = (100 - score) / 10
                debt["high_debt_modules"].append({
                    "module": module,
                    "estimated_hours": round(hours, 1),
                    "priority": "high" if score < 50 else "medium",
                })
                debt["total_estimated_hours"] += hours

        debt["total_estimated_hours"] = round(debt["total_estimated_hours"], 1)
        return debt

    def _generate_recommendations(
        self,
        module_reports: Dict,
        risks: Dict
    ) -> List[Dict]:
        """Génère des recommandations (SANS ACTION)."""
        recommendations = []

        for risk in risks.get("P1", []):
            recommendations.append({
                "priority": "critical",
                "module": risk["module"],
                "recommendation": f"Audit approfondi requis pour {risk['module']}",
                "action": "AUCUNE - Décision humaine requise",
            })

        for risk in risks.get("P2", []):
            recommendations.append({
                "priority": "high",
                "module": risk["module"],
                "recommendation": f"Surveillance renforcée pour {risk['module']}",
                "action": "AUCUNE - Information uniquement",
            })

        return recommendations

    # =========================================================================
    # MODE C - MÉTRIQUES SLA
    # =========================================================================

    def calculate_sla_metrics(
        self,
        period_type: str = "daily",
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> AISLAMetric:
        """
        MODE C: Calcule les métriques SLA/Enterprise.

        Args:
            period_type: hourly, daily, weekly, monthly
            period_start: Début de période (défaut: période précédente)
            period_end: Fin de période

        Returns:
            AISLAMetric avec tous les indicateurs
        """
        logger.info("[AI_GUARDIAN] MODE C - Calcul SLA (%s)", period_type)

        now = datetime.utcnow()

        # Déterminer période
        if not period_start or not period_end:
            period_start, period_end = self._get_period_bounds(period_type, now)

        # Créer métrique
        metric = AISLAMetric(
            metric_uid=f"SLA-{period_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}",
            tenant_id=self.tenant_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
        )

        # Calculer métriques
        incidents = self._get_incidents_for_period(period_start, period_end)

        # Total incidents
        metric.total_incidents = len(incidents)

        # Incidents par module
        by_module = {}
        for inc in incidents:
            by_module[inc.module] = by_module.get(inc.module, 0) + 1
        metric.incidents_by_module = by_module

        # Rollbacks
        rollbacks = [i for i in incidents if i.rollback_performed]
        metric.rollback_count = len(rollbacks)
        metric.rollback_rate = (len(rollbacks) / max(len(incidents), 1)) * 100

        # Temps de résolution moyen
        resolved = [i for i in incidents if i.duration_ms]
        if resolved:
            metric.avg_resolution_time_ms = int(sum(i.duration_ms for i in resolved) / len(resolved))
            metric.avg_detection_time_ms = int(metric.avg_resolution_time_ms * 0.2)  # Estimation

        # Disponibilité (estimation basée sur incidents)
        total_minutes = (period_end - period_start).total_seconds() / 60
        downtime_estimate = len([i for i in incidents if i.severity == IncidentSeverity.CRITICAL.value]) * 5
        metric.downtime_minutes = downtime_estimate
        metric.uptime_percent = ((total_minutes - downtime_estimate) / total_minutes) * 100

        # Sécurité
        security_incidents = [i for i in incidents if i.incident_type == IncidentType.SECURITY.value]
        metric.security_incidents = len(security_incidents)
        metric.tenant_isolation_verified = len(security_incidents) == 0

        # Data intégrité (score basé sur incidents data)
        data_incidents = [i for i in incidents if i.incident_type == IncidentType.DATA.value]
        metric.data_integrity_score = 100 - (len(data_incidents) * 10)

        metric.calculated_at = now

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)

        logger.info(
            "[AI_GUARDIAN] SLA calculé: %s "
            "(uptime=%s%%, incidents=%s)",
            metric.metric_uid, metric.uptime_percent, metric.total_incidents
        )

        return metric

    def _get_period_bounds(
        self,
        period_type: str,
        reference: datetime
    ) -> Tuple[datetime, datetime]:
        """Calcule les bornes de période."""
        if period_type == "hourly":
            end = reference.replace(minute=0, second=0, microsecond=0)
            start = end - timedelta(hours=1)
        elif period_type == "daily":
            end = reference.replace(hour=0, minute=0, second=0, microsecond=0)
            start = end - timedelta(days=1)
        elif period_type == "weekly":
            end = reference.replace(hour=0, minute=0, second=0, microsecond=0)
            start = end - timedelta(weeks=1)
        elif period_type == "monthly":
            end = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start = (end - timedelta(days=1)).replace(day=1)
        else:
            end = reference
            start = reference - timedelta(days=1)

        return start, end

    def _get_incidents_for_period(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> List[AIIncident]:
        """
        Récupère les incidents pour une période.

        SÉCURITÉ: Filtre TOUJOURS par tenant_id si défini.
        Sans tenant_id, retourne liste vide (mode sécurisé par défaut).
        """
        if not self.tenant_id:
            import logging
            logging.getLogger(__name__).warning(
                "[AI_SERVICE] _get_incidents_for_period called without tenant_id - returning empty"
            )
            return []

        query = self.db.query(AIIncident).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.created_at >= period_start,
            AIIncident.created_at <= period_end,
        )
        return query.all()

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def get_incident(self, incident_uid: str) -> Optional[AIIncident]:
        """
        Récupère un incident par UID.

        SÉCURITÉ: Filtre TOUJOURS par tenant_id. Sans tenant_id, retourne None.
        """
        if not self.tenant_id:
            import logging
            logging.getLogger(__name__).warning(
                "[AI_SERVICE] get_incident called without tenant_id - returning None"
            )
            return None

        return self.db.query(AIIncident).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.incident_uid == incident_uid
        ).first()

    def get_recent_incidents(
        self,
        limit: int = 50,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[IncidentStatus] = None,
    ) -> List[AIIncident]:
        """
        Récupère les incidents récents.

        SÉCURITÉ: Filtre TOUJOURS par tenant_id. Sans tenant_id, retourne liste vide.
        """
        if not self.tenant_id:
            import logging
            logging.getLogger(__name__).warning(
                "[AI_SERVICE] get_recent_incidents called without tenant_id - returning empty"
            )
            return []

        query = self.db.query(AIIncident).filter(
            AIIncident.tenant_id == self.tenant_id
        )
        if severity:
            query = query.filter(AIIncident.severity == severity.value)
        if status:
            query = query.filter(AIIncident.status == status.value)

        return query.order_by(AIIncident.created_at.desc()).limit(limit).all()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Récupère les données pour le dashboard.

        SÉCURITÉ: Requiert tenant_id. Sans tenant, retourne données vides/défaut.

        Returns:
            Dict avec statistiques globales
        """
        now = datetime.utcnow()

        # SÉCURITÉ: Sans tenant_id, retourner données par défaut sécurisées
        if not self.tenant_id:
            import logging
            logging.getLogger(__name__).warning(
                "[AI_SERVICE] get_dashboard_data called without tenant_id - returning defaults"
            )
            return {
                "incidents_24h": 0,
                "critical_open": 0,
                "avg_module_score": 100.0,
                "uptime_percent": 99.9,
                "last_updated": now.isoformat(),
            }

        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(weeks=1)

        # Incidents 24h - TOUJOURS filtré par tenant
        incidents_24h = self.db.query(func.count(AIIncident.id)).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.created_at >= day_ago,
        ).scalar()

        # Incidents critiques ouverts - TOUJOURS filtré par tenant
        critical_open = self.db.query(func.count(AIIncident.id)).filter(
            AIIncident.tenant_id == self.tenant_id,
            AIIncident.severity == IncidentSeverity.CRITICAL.value,
            AIIncident.status.in_([IncidentStatus.DETECTED.value, IncidentStatus.ANALYZING.value]),
        ).scalar()

        # Score moyen - TOUJOURS filtré par tenant
        avg_score = self.db.query(func.avg(AIModuleScore.score_total)).filter(
            AIModuleScore.tenant_id == self.tenant_id,
            AIModuleScore.calculated_at >= week_ago,
        ).scalar() or 100

        # Dernier SLA - TOUJOURS filtré par tenant
        last_sla = self.db.query(AISLAMetric).filter(
            AISLAMetric.tenant_id == self.tenant_id
        ).order_by(AISLAMetric.calculated_at.desc()).first()

        return {
            "incidents_24h": incidents_24h,
            "critical_open": critical_open,
            "avg_module_score": round(avg_score, 1),
            "uptime_percent": last_sla.uptime_percent if last_sla else 99.9,
            "last_updated": now.isoformat(),
        }


# =============================================================================
# FACTORY
# =============================================================================

def get_ai_guardian_service(
    db: Session,
    tenant_id: Optional[str] = None
) -> AIGuardianService:
    """Factory pour le service AI Guardian."""
    return AIGuardianService(db, tenant_id)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "AIGuardianService",
    "get_ai_guardian_service",
]
