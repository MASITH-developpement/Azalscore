"""
AZALS MODULE M7 - Dashboard Service
=====================================

Dashboard et statistiques qualité.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.quality.models import (
    NonConformance,
    NonConformanceStatus,
    NonConformanceSeverity,
    QualityControl,
    ControlStatus,
    ControlResult,
    QualityAudit,
    AuditStatus,
    AuditFinding,
    CAPA,
    CAPAStatus,
    CustomerClaim,
    ClaimStatus,
    Certification,
    CertificationStatus,
    QualityIndicator,
    IndicatorMeasurement,
)
from app.modules.quality.schemas import QualityDashboard

logger = logging.getLogger(__name__)


class DashboardService:
    """Service de dashboard qualité."""

    def __init__(self, db: Session, tenant_id: int, user_id: int = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def get_dashboard(self) -> QualityDashboard:
        """Récupère les statistiques du dashboard qualité."""
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # Non-conformités
        nc_stats = self._get_nc_stats()

        # Contrôles qualité
        control_stats = self._get_control_stats(thirty_days_ago)

        # Audits
        audit_stats = self._get_audit_stats(today)

        # CAPA
        capa_stats = self._get_capa_stats(today)

        # Réclamations
        claim_stats = self._get_claim_stats(today)

        # Certifications
        cert_stats = self._get_certification_stats(today)

        # Indicateurs
        indicator_stats = self._get_indicator_stats()

        return QualityDashboard(
            nc_total=nc_stats["total"],
            nc_open=nc_stats["open"],
            nc_critical=nc_stats["critical"],
            controls_total=control_stats["total"],
            controls_completed=control_stats["completed"],
            controls_pass_rate=control_stats["pass_rate"],
            audits_planned=audit_stats["planned"],
            audits_completed=audit_stats["completed"],
            audit_findings_open=audit_stats["findings_open"],
            capa_total=capa_stats["total"],
            capa_open=capa_stats["open"],
            capa_overdue=capa_stats["overdue"],
            capa_effectiveness_rate=capa_stats["effectiveness_rate"],
            claims_total=claim_stats["total"],
            claims_open=claim_stats["open"],
            certifications_active=cert_stats["active"],
            certifications_expiring_soon=cert_stats["expiring"],
            indicators_on_target=indicator_stats["on_target"],
            indicators_warning=indicator_stats["warning"],
            indicators_critical=indicator_stats["critical"],
        )

    def _get_nc_stats(self) -> dict:
        """Statistiques des non-conformités."""
        base_query = self.db.query(func.count(NonConformance.id)).filter(
            NonConformance.tenant_id == self.tenant_id
        )

        total = base_query.scalar() or 0

        nc_open = self.db.query(func.count(NonConformance.id)).filter(
            NonConformance.tenant_id == self.tenant_id,
            NonConformance.status.notin_([
                NonConformanceStatus.CLOSED,
                NonConformanceStatus.CANCELLED
            ])
        ).scalar() or 0

        nc_critical = self.db.query(func.count(NonConformance.id)).filter(
            NonConformance.tenant_id == self.tenant_id,
            NonConformance.severity == NonConformanceSeverity.CRITICAL,
            NonConformance.status.notin_([
                NonConformanceStatus.CLOSED,
                NonConformanceStatus.CANCELLED
            ])
        ).scalar() or 0

        return {"total": total, "open": nc_open, "critical": nc_critical}

    def _get_control_stats(self, since: date) -> dict:
        """Statistiques des contrôles qualité."""
        total = self.db.query(func.count(QualityControl.id)).filter(
            QualityControl.tenant_id == self.tenant_id,
            QualityControl.control_date >= since
        ).scalar() or 0

        completed = self.db.query(func.count(QualityControl.id)).filter(
            QualityControl.tenant_id == self.tenant_id,
            QualityControl.status == ControlStatus.COMPLETED,
            QualityControl.control_date >= since
        ).scalar() or 0

        passed = self.db.query(func.count(QualityControl.id)).filter(
            QualityControl.tenant_id == self.tenant_id,
            QualityControl.result == ControlResult.PASSED,
            QualityControl.control_date >= since
        ).scalar() or 0

        pass_rate = Decimal(
            passed / completed * 100
        ) if completed > 0 else Decimal("0")

        return {"total": total, "completed": completed, "pass_rate": pass_rate}

    def _get_audit_stats(self, today: date) -> dict:
        """Statistiques des audits."""
        planned = self.db.query(func.count(QualityAudit.id)).filter(
            QualityAudit.tenant_id == self.tenant_id,
            QualityAudit.status.in_([AuditStatus.PLANNED, AuditStatus.SCHEDULED])
        ).scalar() or 0

        completed = self.db.query(func.count(QualityAudit.id)).filter(
            QualityAudit.tenant_id == self.tenant_id,
            QualityAudit.status.in_([AuditStatus.COMPLETED, AuditStatus.CLOSED]),
            func.extract("year", QualityAudit.actual_date) == today.year
        ).scalar() or 0

        findings_open = self.db.query(func.count(AuditFinding.id)).filter(
            AuditFinding.tenant_id == self.tenant_id,
            AuditFinding.status == "OPEN"
        ).scalar() or 0

        return {"planned": planned, "completed": completed, "findings_open": findings_open}

    def _get_capa_stats(self, today: date) -> dict:
        """Statistiques des CAPA."""
        total = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id
        ).scalar() or 0

        capa_open = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.status.notin_([
                CAPAStatus.CLOSED_EFFECTIVE,
                CAPAStatus.CLOSED_INEFFECTIVE,
                CAPAStatus.CANCELLED
            ])
        ).scalar() or 0

        overdue = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.target_close_date < today,
            CAPA.status.notin_([
                CAPAStatus.CLOSED_EFFECTIVE,
                CAPAStatus.CLOSED_INEFFECTIVE,
                CAPAStatus.CANCELLED
            ])
        ).scalar() or 0

        effective = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.status == CAPAStatus.CLOSED_EFFECTIVE
        ).scalar() or 0

        closed = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.status.in_([CAPAStatus.CLOSED_EFFECTIVE, CAPAStatus.CLOSED_INEFFECTIVE])
        ).scalar() or 0

        effectiveness_rate = Decimal(
            effective / closed * 100
        ) if closed > 0 else Decimal("0")

        return {
            "total": total,
            "open": capa_open,
            "overdue": overdue,
            "effectiveness_rate": effectiveness_rate
        }

    def _get_claim_stats(self, today: date) -> dict:
        """Statistiques des réclamations."""
        total = self.db.query(func.count(CustomerClaim.id)).filter(
            CustomerClaim.tenant_id == self.tenant_id,
            func.extract("year", CustomerClaim.received_date) == today.year
        ).scalar() or 0

        claims_open = self.db.query(func.count(CustomerClaim.id)).filter(
            CustomerClaim.tenant_id == self.tenant_id,
            CustomerClaim.status.notin_([ClaimStatus.CLOSED, ClaimStatus.REJECTED])
        ).scalar() or 0

        return {"total": total, "open": claims_open}

    def _get_certification_stats(self, today: date) -> dict:
        """Statistiques des certifications."""
        active = self.db.query(func.count(Certification.id)).filter(
            Certification.tenant_id == self.tenant_id,
            Certification.status == CertificationStatus.ACTIVE
        ).scalar() or 0

        expiring = self.db.query(func.count(Certification.id)).filter(
            Certification.tenant_id == self.tenant_id,
            Certification.status == CertificationStatus.ACTIVE,
            Certification.certificate_expiry_date <= today + timedelta(days=90),
            Certification.certificate_expiry_date >= today
        ).scalar() or 0

        return {"active": active, "expiring": expiring}

    def _get_indicator_stats(self) -> dict:
        """Statistiques des indicateurs."""
        indicators_data = self.db.query(
            IndicatorMeasurement.status,
            func.count(IndicatorMeasurement.id)
        ).join(QualityIndicator).filter(
            QualityIndicator.tenant_id == self.tenant_id,
            QualityIndicator.is_active == True
        ).group_by(IndicatorMeasurement.status).all()

        on_target = 0
        warning = 0
        critical = 0

        for status_val, count in indicators_data:
            if status_val == "ON_TARGET":
                on_target = count
            elif status_val == "WARNING":
                warning = count
            elif status_val == "CRITICAL":
                critical = count

        return {"on_target": on_target, "warning": warning, "critical": critical}

    # ========================================================================
    # RAPPORTS SUPPLÉMENTAIRES
    # ========================================================================

    def get_nc_trend(self, months: int = 12) -> list:
        """Tendance des non-conformités par mois."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        result = []
        now = datetime.now()

        for i in range(months):
            month_start = (now - relativedelta(months=i)).replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

            count = self.db.query(func.count(NonConformance.id)).filter(
                NonConformance.tenant_id == self.tenant_id,
                NonConformance.detected_date >= month_start.date(),
                NonConformance.detected_date <= month_end.date()
            ).scalar() or 0

            result.append({
                "month": month_start.strftime("%Y-%m"),
                "count": count
            })

        return list(reversed(result))

    def get_control_results_summary(self, days: int = 30) -> dict:
        """Résumé des résultats de contrôle."""
        since = date.today() - timedelta(days=days)

        results = self.db.query(
            QualityControl.result,
            func.count(QualityControl.id)
        ).filter(
            QualityControl.tenant_id == self.tenant_id,
            QualityControl.status == ControlStatus.COMPLETED,
            QualityControl.control_date >= since
        ).group_by(QualityControl.result).all()

        return {str(r): c for r, c in results if r is not None}

    def get_top_nc_causes(self, limit: int = 10) -> list:
        """Top causes de non-conformité."""
        from sqlalchemy import desc

        results = self.db.query(
            NonConformance.nc_type,
            func.count(NonConformance.id).label("count")
        ).filter(
            NonConformance.tenant_id == self.tenant_id
        ).group_by(
            NonConformance.nc_type
        ).order_by(
            desc("count")
        ).limit(limit).all()

        return [{"type": str(r[0]), "count": r[1]} for r in results]
