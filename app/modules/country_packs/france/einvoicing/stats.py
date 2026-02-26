"""
AZALSCORE - E-Invoicing Statistics
Statistiques et tableau de bord e-invoicing
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceDirection,
    EInvoiceRecord,
    EInvoiceStats,
    EInvoiceStatusDB,
    EReportingSubmission,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    EInvoiceDashboard,
    EInvoiceResponse,
    EInvoiceStatsResponse,
    EInvoiceStatsSummary,
    EReportingResponse,
    PDPConfigResponse,
)

if TYPE_CHECKING:
    from .pdp_config import PDPConfigManager

logger = logging.getLogger(__name__)


class EInvoiceStatsManager:
    """
    Gestionnaire des statistiques e-invoicing.

    Fournit:
    - Statistiques par période
    - Résumé des statistiques
    - Données du tableau de bord
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        pdp_config_manager: "PDPConfigManager"
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.pdp_config_manager = pdp_config_manager

    def get_stats(self, period: str | None = None) -> EInvoiceStatsResponse | None:
        """
        Récupère les statistiques pour une période.

        Args:
            period: Période au format YYYY-MM (défaut: mois courant)

        Returns:
            EInvoiceStatsResponse ou None
        """
        if not period:
            period = date.today().strftime("%Y-%m")

        stats = self.db.query(EInvoiceStats).filter(
            EInvoiceStats.tenant_id == self.tenant_id,
            EInvoiceStats.period == period
        ).first()

        if not stats:
            return None

        return EInvoiceStatsResponse.model_validate(stats)

    def get_stats_summary(self) -> EInvoiceStatsSummary:
        """
        Récupère le résumé des statistiques.

        Returns:
            EInvoiceStatsSummary avec mois courant, précédent et YTD
        """
        today = date.today()
        current_period = today.strftime("%Y-%m")

        # Mois précédent
        if today.month == 1:
            prev_period = f"{today.year - 1}-12"
        else:
            prev_period = f"{today.year}-{today.month - 1:02d}"

        current_stats = self.get_stats(current_period)
        previous_stats = self.get_stats(prev_period)

        # Calcul YTD
        ytd_stats = self.db.query(
            func.sum(EInvoiceStats.outbound_total).label("outbound_total"),
            func.sum(EInvoiceStats.inbound_total).label("inbound_total"),
            func.sum(EInvoiceStats.outbound_amount_ttc).label("outbound_amount"),
            func.sum(EInvoiceStats.inbound_amount_ttc).label("inbound_amount"),
        ).filter(
            EInvoiceStats.tenant_id == self.tenant_id,
            EInvoiceStats.period.like(f"{today.year}-%")
        ).first()

        return EInvoiceStatsSummary(
            current_month=current_stats,
            previous_month=previous_stats,
            year_to_date={
                "outbound_total": ytd_stats.outbound_total or 0,
                "inbound_total": ytd_stats.inbound_total or 0,
                "outbound_amount": ytd_stats.outbound_amount or Decimal("0"),
                "inbound_amount": ytd_stats.inbound_amount or Decimal("0"),
            }
        )

    def get_dashboard(self) -> EInvoiceDashboard:
        """
        Récupère les données du tableau de bord.

        Returns:
            EInvoiceDashboard avec toutes les métriques
        """
        # Configs
        active_configs = self.pdp_config_manager.list_configs(active_only=True)
        default_config = self.pdp_config_manager.get_default_config()

        # Stats du mois
        today = date.today()
        current_period = today.strftime("%Y-%m")
        first_of_month = today.replace(day=1)

        outbound_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.OUTBOUND,
            EInvoiceRecord.issue_date >= first_of_month
        ).scalar() or 0

        inbound_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.INBOUND,
            EInvoiceRecord.issue_date >= first_of_month
        ).scalar() or 0

        pending_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.status.in_([EInvoiceStatusDB.DRAFT, EInvoiceStatusDB.VALIDATED])
        ).scalar() or 0

        errors_count = self.db.query(func.count(EInvoiceRecord.id)).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.status == EInvoiceStatusDB.ERROR
        ).scalar() or 0

        # Récentes
        recent_outbound = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.OUTBOUND
        ).order_by(EInvoiceRecord.created_at.desc()).limit(5).all()

        recent_inbound = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.direction == EInvoiceDirection.INBOUND
        ).order_by(EInvoiceRecord.created_at.desc()).limit(5).all()

        recent_errors = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id,
            EInvoiceRecord.status == EInvoiceStatusDB.ERROR
        ).order_by(EInvoiceRecord.updated_at.desc()).limit(5).all()

        # E-reporting
        ereporting_pending = self.db.query(func.count(EReportingSubmission.id)).filter(
            EReportingSubmission.tenant_id == self.tenant_id,
            EReportingSubmission.status == "DRAFT"
        ).scalar() or 0

        current_ereporting = self.db.query(EReportingSubmission).filter(
            EReportingSubmission.tenant_id == self.tenant_id,
            EReportingSubmission.period == current_period
        ).first()

        # Alertes
        alerts = []
        if not default_config:
            alerts.append("Aucune configuration PDP par défaut")
        if errors_count > 0:
            alerts.append(f"{errors_count} facture(s) en erreur")
        if pending_count > 10:
            alerts.append(f"{pending_count} factures en attente de soumission")

        return EInvoiceDashboard(
            active_pdp_configs=len(active_configs),
            default_pdp=PDPConfigResponse.model_validate(default_config) if default_config else None,
            outbound_this_month=outbound_count,
            inbound_this_month=inbound_count,
            pending_actions=pending_count,
            errors_count=errors_count,
            recent_outbound=[EInvoiceResponse.model_validate(e) for e in recent_outbound],
            recent_inbound=[EInvoiceResponse.model_validate(e) for e in recent_inbound],
            recent_errors=[EInvoiceResponse.model_validate(e) for e in recent_errors],
            ereporting_pending=ereporting_pending,
            ereporting_current_period=EReportingResponse.model_validate(current_ereporting) if current_ereporting else None,
            alerts=alerts
        )
