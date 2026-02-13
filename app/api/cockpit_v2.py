"""
AZALS API - Cockpit Dirigeant v2 (CORE SaaS)
=============================================

Tableau de bord executif - Version CORE SaaS.

MIGRATION CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user() + get_tenant_id()
- SaaSContext fournit tenant_id + user_id directement
- Audit automatique via CoreAuthMiddleware
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/cockpit", tags=["Cockpit Dirigeant v2 - CORE SaaS"])


# ============================================================================
# SCHEMAS
# ============================================================================

class DashboardKPI(BaseModel):
    """KPI du tableau de bord."""
    id: str
    label: str
    value: float
    unit: str | None = None
    trend: float | None = None
    status: str  # green, orange, red


class Alert(BaseModel):
    """Alerte du cockpit."""
    id: str
    severity: str  # RED, ORANGE, GREEN
    message: str
    module: str
    action_url: str | None = None
    created_at: datetime


class TreasurySummary(BaseModel):
    """Resume tresorerie."""
    balance: float
    forecast_30d: float
    pending_payments: float


class SalesSummary(BaseModel):
    """Resume des ventes."""
    month_revenue: float
    prev_month_revenue: float
    pending_invoices: int
    overdue_invoices: int


class ActivitySummary(BaseModel):
    """Resume de l'activite."""
    open_quotes: int
    pending_orders: int
    scheduled_interventions: int


class CockpitDashboard(BaseModel):
    """Dashboard complet du cockpit."""
    kpis: list[DashboardKPI]
    alerts: list[Alert]
    treasury_summary: TreasurySummary
    sales_summary: SalesSummary
    activity_summary: ActivitySummary


class PendingDecision(BaseModel):
    """Decision en attente."""
    id: str
    type: str
    title: str
    severity: str  # RED, ORANGE, GREEN
    module: str
    created_at: datetime
    action_url: str


class PaginatedDecisions(BaseModel):
    """Liste paginee de decisions."""
    items: list[PendingDecision]
    total: int
    page: int
    page_size: int


class AcknowledgeResponse(BaseModel):
    """Reponse d'acquittement d'alerte."""
    acknowledged: bool
    alert_id: str


# ============================================================================
# HELPERS
# ============================================================================

def _get_kpis(db: Session, tenant_id: str) -> list[DashboardKPI]:
    """Calcule les KPIs du tableau de bord."""
    kpis = []
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # CA du mois
    try:
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) as revenue
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
            AND date >= :month_start
        """), {"tenant_id": tenant_id, "month_start": month_start})
        month_revenue = float(result.scalar() or 0)

        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) as revenue
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
            AND date >= :prev_month_start
            AND date < :month_start
        """), {"tenant_id": tenant_id, "prev_month_start": prev_month_start, "month_start": month_start})
        prev_revenue = float(result.scalar() or 0)

        trend = ((month_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        status = "green" if trend >= 0 else "orange" if trend >= -10 else "red"

        kpis.append(DashboardKPI(
            id="revenue",
            label="CA du mois",
            value=month_revenue,
            unit="EUR",
            trend=round(trend, 1),
            status=status
        ))
    except Exception as e:
        logger.error(
            "[COCKPIT_V2] Echec calcul KPI revenue",
            extra={"kpi": "revenue", "error": str(e)[:200], "consequence": "fallback_zero"}
        )
        kpis.append(DashboardKPI(id="revenue", label="CA du mois", value=0, unit="EUR", trend=0, status="green"))

    # Factures en attente
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status IN ('DRAFT', 'SENT')
        """), {"tenant_id": tenant_id})
        pending_count = int(result.scalar() or 0)
        status = "green" if pending_count < 10 else "orange" if pending_count < 25 else "red"
        kpis.append(DashboardKPI(id="invoices", label="Factures en attente", value=pending_count, status=status))
    except Exception as e:
        logger.error(
            "[COCKPIT_V2] Echec calcul KPI invoices",
            extra={"kpi": "invoices", "error": str(e)[:200], "consequence": "fallback_zero"}
        )
        kpis.append(DashboardKPI(id="invoices", label="Factures en attente", value=0, status="green"))

    # Tresorerie
    try:
        result = db.execute(text("""
            SELECT COALESCE(SUM(current_balance), 0) FROM bank_accounts
            WHERE tenant_id = :tenant_id AND is_active = true
        """), {"tenant_id": tenant_id})
        treasury = float(result.scalar() or 0)
        status = "green" if treasury > 10000 else "orange" if treasury > 0 else "red"
        kpis.append(DashboardKPI(id="treasury", label="Tresorerie", value=treasury, unit="EUR", status=status))
    except Exception as e:
        logger.error(
            "[COCKPIT_V2] Echec calcul KPI treasury",
            extra={"kpi": "treasury", "error": str(e)[:200], "consequence": "fallback_zero"}
        )
        kpis.append(DashboardKPI(id="treasury", label="Tresorerie", value=0, unit="EUR", status="green"))

    # Impayes
    try:
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
            AND due_date < :now
        """), {"tenant_id": tenant_id, "now": now})
        overdue = float(result.scalar() or 0)
        status = "green" if overdue == 0 else "orange" if overdue < 5000 else "red"
        kpis.append(DashboardKPI(id="overdue", label="Impayes", value=overdue, unit="EUR", status=status))
    except Exception as e:
        logger.error(
            "[COCKPIT_V2] Echec calcul KPI overdue",
            extra={"kpi": "overdue", "error": str(e)[:200], "consequence": "fallback_zero"}
        )
        kpis.append(DashboardKPI(id="overdue", label="Impayes", value=0, unit="EUR", status="green"))

    return kpis


def _get_alerts(db: Session, tenant_id: str) -> list[Alert]:
    """Recupere les alertes actives."""
    alerts = []
    now = datetime.utcnow()

    # Alertes factures echues
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
            AND due_date < :now
        """), {"tenant_id": tenant_id, "now": now})
        overdue_count = int(result.scalar() or 0)
        if overdue_count > 0:
            alerts.append(Alert(
                id="overdue_invoices",
                severity="RED" if overdue_count > 5 else "ORANGE",
                message=f"{overdue_count} facture(s) en retard de paiement",
                module="invoicing",
                action_url="/invoicing?filter=overdue",
                created_at=now
            ))
    except Exception as e:
        logger.warning(
            "[COCKPIT_V2] Echec recuperation alertes factures echues",
            extra={"alert": "overdue_invoices", "error": str(e)[:200], "consequence": "alert_skipped"}
        )

    # Alertes factures a echeance proche
    try:
        week_ahead = now + timedelta(days=7)
        result = db.execute(text("""
            SELECT COUNT(*) FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
            AND due_date >= :now
            AND due_date <= :week_ahead
        """), {"tenant_id": tenant_id, "now": now, "week_ahead": week_ahead})
        due_soon = int(result.scalar() or 0)
        if due_soon > 0:
            alerts.append(Alert(
                id="invoices_due_soon",
                severity="ORANGE",
                message=f"{due_soon} facture(s) arrivent a echeance cette semaine",
                module="invoicing",
                action_url="/invoicing?filter=due_soon",
                created_at=now
            ))
    except Exception as e:
        logger.warning(
            "[COCKPIT_V2] Echec recuperation alertes echeances proches",
            extra={"alert": "invoices_due_soon", "error": str(e)[:200], "consequence": "alert_skipped"}
        )

    # Alertes tickets support non resolus
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM support_tickets
            WHERE tenant_id = :tenant_id
            AND status IN ('open', 'in_progress')
            AND priority IN ('critical', 'high')
        """), {"tenant_id": tenant_id})
        urgent_tickets = int(result.scalar() or 0)
        if urgent_tickets > 0:
            alerts.append(Alert(
                id="urgent_tickets",
                severity="RED" if urgent_tickets > 3 else "ORANGE",
                message=f"{urgent_tickets} ticket(s) support urgents en attente",
                module="support",
                action_url="/support?filter=urgent",
                created_at=now
            ))
    except Exception as e:
        logger.warning(
            "[COCKPIT_V2] Echec recuperation alertes tickets support",
            extra={"alert": "urgent_tickets", "error": str(e)[:200], "consequence": "alert_skipped"}
        )

    return alerts


def _get_treasury_summary(db: Session, tenant_id: str) -> TreasurySummary:
    """Resume tresorerie."""
    try:
        result = db.execute(text("""
            SELECT COALESCE(SUM(current_balance), 0) FROM bank_accounts
            WHERE tenant_id = :tenant_id AND is_active = true
        """), {"tenant_id": tenant_id})
        balance = float(result.scalar() or 0)

        # Prevision 30j (simplifie)
        forecast = balance * 0.95

        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
        """), {"tenant_id": tenant_id})
        pending = float(result.scalar() or 0)

        return TreasurySummary(balance=balance, forecast_30d=forecast, pending_payments=pending)
    except Exception as e:
        logger.error(
            "[COCKPIT_V2] Echec calcul resume tresorerie",
            extra={"section": "treasury_summary", "error": str(e)[:200], "consequence": "fallback_zero"}
        )
        return TreasurySummary(balance=0, forecast_30d=0, pending_payments=0)


def _get_sales_summary(db: Session, tenant_id: str) -> SalesSummary:
    """Resume ventes."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    try:
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) FROM commercial_documents
            WHERE tenant_id = :tenant_id AND type = 'INVOICE' AND status = 'VALIDATED' AND date >= :month_start
        """), {"tenant_id": tenant_id, "month_start": month_start})
        month_revenue = float(result.scalar() or 0)

        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) FROM commercial_documents
            WHERE tenant_id = :tenant_id AND type = 'INVOICE' AND status = 'VALIDATED'
            AND date >= :prev_month_start AND date < :month_start
        """), {"tenant_id": tenant_id, "prev_month_start": prev_month_start, "month_start": month_start})
        prev_revenue = float(result.scalar() or 0)

        result = db.execute(text("""
            SELECT COUNT(*) FROM commercial_documents
            WHERE tenant_id = :tenant_id AND type = 'INVOICE' AND status IN ('DRAFT', 'SENT')
        """), {"tenant_id": tenant_id})
        pending = int(result.scalar() or 0)

        result = db.execute(text("""
            SELECT COUNT(*) FROM commercial_documents
            WHERE tenant_id = :tenant_id AND type = 'INVOICE' AND status = 'VALIDATED' AND due_date < :now
        """), {"tenant_id": tenant_id, "now": now})
        overdue = int(result.scalar() or 0)

        return SalesSummary(
            month_revenue=month_revenue,
            prev_month_revenue=prev_revenue,
            pending_invoices=pending,
            overdue_invoices=overdue
        )
    except Exception as e:
        logger.error(
            "[COCKPIT_V2] Echec calcul resume ventes",
            extra={"section": "sales_summary", "error": str(e)[:200], "consequence": "fallback_zero"}
        )
        return SalesSummary(month_revenue=0, prev_month_revenue=0, pending_invoices=0, overdue_invoices=0)


def _get_activity_summary(db: Session, tenant_id: str) -> ActivitySummary:
    """Resume activite."""
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM commercial_documents
            WHERE tenant_id = :tenant_id AND type = 'QUOTE' AND status IN ('DRAFT', 'SENT')
        """), {"tenant_id": tenant_id})
        quotes = int(result.scalar() or 0)

        result = db.execute(text("""
            SELECT COUNT(*) FROM commercial_documents
            WHERE tenant_id = :tenant_id AND type = 'ORDER' AND status IN ('DRAFT', 'VALIDATED')
        """), {"tenant_id": tenant_id})
        orders = int(result.scalar() or 0)

        result = db.execute(text("""
            SELECT COUNT(*) FROM interventions
            WHERE tenant_id = :tenant_id AND status = 'scheduled'
        """), {"tenant_id": tenant_id})
        interventions = int(result.scalar() or 0)

        return ActivitySummary(open_quotes=quotes, pending_orders=orders, scheduled_interventions=interventions)
    except Exception as e:
        logger.error(
            "[COCKPIT_V2] Echec calcul resume activite",
            extra={"section": "activity_summary", "error": str(e)[:200], "consequence": "fallback_zero"}
        )
        return ActivitySummary(open_quotes=0, pending_orders=0, scheduled_interventions=0)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=CockpitDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Dashboard complet du cockpit dirigeant.

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    return CockpitDashboard(
        kpis=_get_kpis(db, context.tenant_id),
        alerts=_get_alerts(db, context.tenant_id),
        treasury_summary=_get_treasury_summary(db, context.tenant_id),
        sales_summary=_get_sales_summary(db, context.tenant_id),
        activity_summary=_get_activity_summary(db, context.tenant_id)
    )


@router.get("/decisions", response_model=PaginatedDecisions)
async def get_pending_decisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Liste des decisions en attente pour le dirigeant.

    CORE SaaS: Utilise context.tenant_id pour l'isolation.
    """
    decisions = []
    skip = (page - 1) * page_size

    # Devis a valider
    try:
        result = db.execute(text("""
            SELECT id, number, customer_name, total, created_at
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'QUOTE'
            AND status = 'DRAFT'
            ORDER BY created_at DESC
            LIMIT 10
        """), {"tenant_id": context.tenant_id})
        for row in result:
            decisions.append(PendingDecision(
                id=str(row[0]),
                type="QUOTE_VALIDATION",
                title=f"Devis {row[1]} - {row[2]} ({row[3]}EUR)",
                severity="ORANGE",
                module="commercial",
                created_at=row[4],
                action_url=f"/commercial/quotes/{row[0]}"
            ))
    except Exception as e:
        logger.warning(
            "[COCKPIT_V2] Echec recuperation devis en attente",
            extra={"decision": "quotes", "error": str(e)[:200], "consequence": "decision_skipped"}
        )

    # Factures importantes a valider
    try:
        result = db.execute(text("""
            SELECT id, number, customer_name, total, created_at
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'DRAFT'
            AND total > 5000
            ORDER BY total DESC
            LIMIT 5
        """), {"tenant_id": context.tenant_id})
        for row in result:
            decisions.append(PendingDecision(
                id=str(row[0]),
                type="INVOICE_VALIDATION",
                title=f"Facture {row[1]} - {row[2]} ({row[3]}EUR)",
                severity="RED" if row[3] > 10000 else "ORANGE",
                module="invoicing",
                created_at=row[4],
                action_url=f"/invoicing/{row[0]}"
            ))
    except Exception as e:
        logger.warning(
            "[COCKPIT_V2] Echec recuperation factures a valider",
            extra={"decision": "invoices", "error": str(e)[:200], "consequence": "decision_skipped"}
        )

    # Tickets support critiques
    try:
        result = db.execute(text("""
            SELECT id, reference, subject, priority, created_at
            FROM support_tickets
            WHERE tenant_id = :tenant_id
            AND status IN ('open', 'in_progress')
            AND priority = 'critical'
            ORDER BY created_at ASC
            LIMIT 5
        """), {"tenant_id": context.tenant_id})
        for row in result:
            decisions.append(PendingDecision(
                id=str(row[0]),
                type="SUPPORT_ESCALATION",
                title=f"Ticket {row[1]} - {row[2]}",
                severity="RED",
                module="support",
                created_at=row[4],
                action_url=f"/support/tickets/{row[0]}"
            ))
    except Exception as e:
        logger.warning(
            "[COCKPIT_V2] Echec recuperation tickets support critiques",
            extra={"decision": "support", "error": str(e)[:200], "consequence": "decision_skipped"}
        )

    total = len(decisions)
    paginated = decisions[skip:skip + page_size]

    return PaginatedDecisions(items=paginated, total=total, page=page, page_size=page_size)


@router.post("/alerts/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Acquitter une alerte.

    CORE SaaS: Utilise context.user_id pour l'audit.
    """
    logger.info(
        "[COCKPIT_V2] Alerte acquittee",
        extra={
            "alert_id": alert_id,
            "user_id": str(context.user_id),
            "tenant_id": context.tenant_id
        }
    )
    return AcknowledgeResponse(acknowledged=True, alert_id=alert_id)
