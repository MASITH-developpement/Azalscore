"""
AZALSCORE GUARDIAN - Rapport Journalier
========================================

Génère automatiquement un rapport journalier des incidents par tenant.
"""
from __future__ import annotations


from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.logging_config import get_logger
from .models import (
    Incident,
    GuardianDailyReport,
    ErrorDetection,
    CorrectionRegistry,
    CorrectionStatus,
)

logger = get_logger(__name__)


class DailyReportService:
    """Service de génération de rapports journaliers Guardian."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def generate_daily_report(self, report_date: Optional[datetime] = None) -> GuardianDailyReport:
        """
        Génère le rapport journalier pour une date donnée.
        Par défaut, génère le rapport de la veille.
        """
        if report_date is None:
            report_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

        # Période du rapport (jour complet)
        start_date = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        logger.info("[GUARDIAN] Generating daily report for %s - tenant: %s", start_date.date(), self.tenant_id)

        # Vérifier si un rapport existe déjà
        existing_report = self.db.query(GuardianDailyReport).filter(
            GuardianDailyReport.tenant_id == self.tenant_id,
            func.date(GuardianDailyReport.report_date) == start_date.date()
        ).first()

        if existing_report:
            logger.info("[GUARDIAN] Report already exists: %s", existing_report.report_uid)
            return existing_report

        # Collecter les statistiques des incidents
        incidents_stats = self._get_incidents_stats(start_date, end_date)

        # Collecter les statistiques des corrections
        corrections_stats = self._get_corrections_stats(start_date, end_date)

        # Pages impactées
        affected_pages = self._get_affected_pages(start_date, end_date)

        # Actions Guardian
        guardian_actions_summary = self._get_guardian_actions_summary(start_date, end_date)

        # Générer le contenu du rapport
        report_content = self._generate_report_content(
            report_date=start_date,
            incidents_stats=incidents_stats,
            corrections_stats=corrections_stats,
            affected_pages=affected_pages,
            guardian_actions_summary=guardian_actions_summary,
        )

        # Créer le rapport
        report = GuardianDailyReport(
            tenant_id=self.tenant_id,
            report_date=start_date,
            total_incidents=incidents_stats["total"],
            incidents_by_type=incidents_stats["by_type"],
            incidents_by_severity=incidents_stats["by_severity"],
            total_corrections=corrections_stats["total"],
            successful_corrections=corrections_stats["successful"],
            failed_corrections=corrections_stats["failed"],
            rollbacks=corrections_stats["rollbacks"],
            guardian_actions_count=sum(a.get("count", 0) for a in guardian_actions_summary),
            guardian_actions_summary=guardian_actions_summary,
            affected_pages=affected_pages,
            report_content=report_content,
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.info("[GUARDIAN] Daily report generated: %s", report.report_uid)
        return report

    def _get_incidents_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collecte les statistiques des incidents."""
        incidents = self.db.query(Incident).filter(
            Incident.tenant_id == self.tenant_id,
            Incident.created_at >= start_date,
            Incident.created_at < end_date,
        ).all()

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}

        for incident in incidents:
            by_type[incident.type] = by_type.get(incident.type, 0) + 1
            by_severity[incident.severity] = by_severity.get(incident.severity, 0) + 1

        return {
            "total": len(incidents),
            "by_type": by_type,
            "by_severity": by_severity,
        }

    def _get_corrections_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collecte les statistiques des corrections."""
        corrections = self.db.query(CorrectionRegistry).filter(
            CorrectionRegistry.tenant_id == self.tenant_id,
            CorrectionRegistry.created_at >= start_date,
            CorrectionRegistry.created_at < end_date,
        ).all()

        successful = sum(1 for c in corrections if c.correction_successful)
        failed = sum(1 for c in corrections if c.status == CorrectionStatus.FAILED)
        rollbacks = sum(1 for c in corrections if c.rolled_back)

        return {
            "total": len(corrections),
            "successful": successful,
            "failed": failed,
            "rollbacks": rollbacks,
        }

    def _get_affected_pages(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Collecte les pages impactées."""
        results = self.db.query(
            Incident.page,
            func.count(Incident.id).label("incident_count")
        ).filter(
            Incident.tenant_id == self.tenant_id,
            Incident.created_at >= start_date,
            Incident.created_at < end_date,
        ).group_by(Incident.page).order_by(func.count(Incident.id).desc()).limit(20).all()

        return [{"page": r.page, "incident_count": r.incident_count} for r in results]

    def _get_guardian_actions_summary(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Résumé des actions Guardian."""
        incidents = self.db.query(Incident).filter(
            Incident.tenant_id == self.tenant_id,
            Incident.created_at >= start_date,
            Incident.created_at < end_date,
            Incident.guardian_actions.isnot(None),
        ).all()

        actions_count: Dict[str, Dict[str, int]] = {}

        for incident in incidents:
            if incident.guardian_actions:
                for action in incident.guardian_actions:
                    action_type = action.get("action_type", "UNKNOWN")
                    if action_type not in actions_count:
                        actions_count[action_type] = {"total": 0, "success": 0}
                    actions_count[action_type]["total"] += 1
                    if action.get("success"):
                        actions_count[action_type]["success"] += 1

        return [
            {
                "action_type": action_type,
                "count": data["total"],
                "success_rate": round(data["success"] / data["total"] * 100, 1) if data["total"] > 0 else 0,
            }
            for action_type, data in actions_count.items()
        ]

    def _generate_report_content(
        self,
        report_date: datetime,
        incidents_stats: Dict[str, Any],
        corrections_stats: Dict[str, Any],
        affected_pages: List[Dict[str, Any]],
        guardian_actions_summary: List[Dict[str, Any]],
    ) -> str:
        """Génère le contenu textuel du rapport."""
        content = f"""# RAPPORT GUARDIAN JOURNALIER
## Tenant: {self.tenant_id}
## Date: {report_date.strftime('%Y-%m-%d')}
---

### RÉSUMÉ EXÉCUTIF

- **Incidents totaux**: {incidents_stats['total']}
- **Corrections appliquées**: {corrections_stats['total']}
- **Corrections réussies**: {corrections_stats['successful']}
- **Corrections échouées**: {corrections_stats['failed']}
- **Rollbacks**: {corrections_stats['rollbacks']}

---

### INCIDENTS PAR SÉVÉRITÉ

"""
        for severity, count in incidents_stats.get("by_severity", {}).items():
            emoji = "🔴" if severity == "critical" else "🟠" if severity == "error" else "🟡" if severity == "warning" else "🔵"
            content += f"- {emoji} **{severity.upper()}**: {count}\n"

        content += """
---

### INCIDENTS PAR TYPE

"""
        for itype, count in incidents_stats.get("by_type", {}).items():
            content += f"- **{itype}**: {count}\n"

        content += """
---

### PAGES LES PLUS IMPACTÉES

"""
        for i, page in enumerate(affected_pages[:10], 1):
            content += f"{i}. `{page['page']}` - {page['incident_count']} incident(s)\n"

        content += """
---

### ACTIONS GUARDIAN

"""
        if guardian_actions_summary:
            for action in guardian_actions_summary:
                content += f"- **{action['action_type']}**: {action['count']} exécution(s), {action['success_rate']}% réussite\n"
        else:
            content += "Aucune action Guardian exécutée.\n"

        content += f"""
---

*Rapport généré automatiquement par GUARDIAN - {datetime.utcnow().isoformat()}*
"""
        return content

    def get_report(self, report_date: datetime) -> Optional[GuardianDailyReport]:
        """Récupère un rapport existant."""
        return self.db.query(GuardianDailyReport).filter(
            GuardianDailyReport.tenant_id == self.tenant_id,
            func.date(GuardianDailyReport.report_date) == report_date.date()
        ).first()

    def list_reports(self, limit: int = 30) -> List[GuardianDailyReport]:
        """Liste les derniers rapports."""
        return self.db.query(GuardianDailyReport).filter(
            GuardianDailyReport.tenant_id == self.tenant_id
        ).order_by(GuardianDailyReport.report_date.desc()).limit(limit).all()


def generate_all_daily_reports(db: Session) -> int:
    """
    Génère les rapports journaliers pour tous les tenants.
    À appeler via cron ou tâche planifiée.
    """
    from app.modules.tenants.models import Tenant

    logger.info("[GUARDIAN] Starting daily report generation for all tenants")

    try:
        tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
        reports_generated = 0

        for tenant in tenants:
            try:
                service = DailyReportService(db, tenant.id)
                service.generate_daily_report()
                reports_generated += 1
            except Exception as e:
                logger.error("[GUARDIAN] Failed to generate report for tenant %s: %s", tenant.id, e)

        logger.info("[GUARDIAN] Daily reports generated: %s/%s", reports_generated, len(tenants))
        return reports_generated

    except Exception as e:
        logger.error("[GUARDIAN] Daily report generation failed: %s", e)
        return 0
