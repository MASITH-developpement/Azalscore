"""
AZALS - Cockpit Dirigeant API
==============================
API pour le tableau de bord exécutif.
Données agrégées de tous les modules.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.cache import cached
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/cockpit", tags=["Cockpit Dirigeant"])


# ============================================================================
# SCHEMAS
# ============================================================================

class DashboardKPI(BaseModel):
    id: str
    label: str
    value: float
    unit: str | None = None
    trend: float | None = None
    status: str  # green, orange, red


class Alert(BaseModel):
    id: str
    severity: str  # RED, ORANGE, GREEN
    message: str
    module: str
    action_url: str | None = None
    created_at: datetime


class TreasurySummary(BaseModel):
    balance: float
    forecast_30d: float
    pending_payments: float


class SalesSummary(BaseModel):
    month_revenue: float
    prev_month_revenue: float
    pending_invoices: int
    overdue_invoices: int


class ActivitySummary(BaseModel):
    open_quotes: int
    pending_orders: int
    scheduled_interventions: int


class CockpitDashboard(BaseModel):
    kpis: list[DashboardKPI]
    alerts: list[Alert]
    treasury_summary: TreasurySummary
    sales_summary: SalesSummary
    activity_summary: ActivitySummary


class PendingDecision(BaseModel):
    id: str
    type: str
    title: str
    severity: str  # RED, ORANGE, GREEN
    module: str
    created_at: datetime
    action_url: str


class PaginatedDecisions(BaseModel):
    items: list[PendingDecision]
    total: int
    page: int
    page_size: int


# ============================================================================
# HELPERS
# ============================================================================

@cached(ttl=300, key_builder=lambda db, tenant_id: f"cockpit:kpis:{tenant_id}")
def get_kpis(db: Session, tenant_id: str) -> list[DashboardKPI]:
    """Calcule les KPIs du tableau de bord (cache 5min)."""
    kpis = []
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # CA du mois (depuis commercial_documents)
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
        logger.error("[COCKPIT] Échec calcul KPI revenue", extra={"kpi": "revenue", "error": str(e)[:200], "consequence": "fallback_zero"})
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
        logger.error("[COCKPIT] Échec calcul KPI invoices", extra={"kpi": "invoices", "error": str(e)[:200], "consequence": "fallback_zero"})
        kpis.append(DashboardKPI(id="invoices", label="Factures en attente", value=0, status="green"))

    # Trésorerie
    try:
        result = db.execute(text("""
            SELECT COALESCE(SUM(current_balance), 0) FROM bank_accounts
            WHERE tenant_id = :tenant_id AND is_active = true
        """), {"tenant_id": tenant_id})
        treasury = float(result.scalar() or 0)
        status = "green" if treasury > 10000 else "orange" if treasury > 0 else "red"
        kpis.append(DashboardKPI(id="treasury", label="Trésorerie", value=treasury, unit="EUR", status=status))
    except Exception as e:
        logger.error("[COCKPIT] Échec calcul KPI treasury", extra={"kpi": "treasury", "error": str(e)[:200], "consequence": "fallback_zero"})
        kpis.append(DashboardKPI(id="treasury", label="Trésorerie", value=0, unit="EUR", status="green"))

    # Impayés
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
        kpis.append(DashboardKPI(id="overdue", label="Impayés", value=overdue, unit="EUR", status=status))
    except Exception as e:
        logger.error("[COCKPIT] Échec calcul KPI overdue", extra={"kpi": "overdue", "error": str(e)[:200], "consequence": "fallback_zero"})
        kpis.append(DashboardKPI(id="overdue", label="Impayés", value=0, unit="EUR", status="green"))

    return kpis


@cached(ttl=60, key_builder=lambda db, tenant_id: f"cockpit:alerts:{tenant_id}")
def get_alerts(db: Session, tenant_id: str) -> list[Alert]:
    """Récupère les alertes actives (cache 1min)."""
    alerts = []
    now = datetime.utcnow()

    # Alertes factures échues
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
        logger.warning("[COCKPIT] Échec récupération alertes factures échues", extra={"alert": "overdue_invoices", "error": str(e)[:200], "consequence": "alert_skipped"})

    # Alertes factures à échéance proche
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
                message=f"{due_soon} facture(s) arrivent à échéance cette semaine",
                module="invoicing",
                action_url="/invoicing?filter=due_soon",
                created_at=now
            ))
    except Exception as e:
        logger.warning("[COCKPIT] Échec récupération alertes échéances proches", extra={"alert": "invoices_due_soon", "error": str(e)[:200], "consequence": "alert_skipped"})

    # Alertes tickets support non résolus
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
        logger.warning("[COCKPIT] Échec récupération alertes tickets support", extra={"alert": "urgent_tickets", "error": str(e)[:200], "consequence": "alert_skipped"})

    return alerts


@cached(ttl=300, key_builder=lambda db, tenant_id: f"cockpit:treasury:{tenant_id}")
def get_treasury_summary(db: Session, tenant_id: str) -> TreasurySummary:
    """Résumé trésorerie (cache 5min)."""
    try:
        result = db.execute(text("""
            SELECT COALESCE(SUM(current_balance), 0) FROM bank_accounts
            WHERE tenant_id = :tenant_id AND is_active = true
        """), {"tenant_id": tenant_id})
        balance = float(result.scalar() or 0)

        # Prévision 30j (simplifié)
        forecast = balance * 0.95  # Placeholder

        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
        """), {"tenant_id": tenant_id})
        pending = float(result.scalar() or 0)

        return TreasurySummary(balance=balance, forecast_30d=forecast, pending_payments=pending)
    except Exception as e:
        logger.error("[COCKPIT] Échec calcul résumé trésorerie", extra={"section": "treasury_summary", "error": str(e)[:200], "consequence": "fallback_zero"})
        return TreasurySummary(balance=0, forecast_30d=0, pending_payments=0)


@cached(ttl=300, key_builder=lambda db, tenant_id: f"cockpit:sales:{tenant_id}")
def get_sales_summary(db: Session, tenant_id: str) -> SalesSummary:
    """Résumé ventes (cache 5min)."""
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
        logger.error("[COCKPIT] Échec calcul résumé ventes", extra={"section": "sales_summary", "error": str(e)[:200], "consequence": "fallback_zero"})
        return SalesSummary(month_revenue=0, prev_month_revenue=0, pending_invoices=0, overdue_invoices=0)


@cached(ttl=300, key_builder=lambda db, tenant_id: f"cockpit:activity:{tenant_id}")
def get_activity_summary(db: Session, tenant_id: str) -> ActivitySummary:
    """Résumé activité (cache 5min)."""
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
        logger.error("[COCKPIT] Échec calcul résumé activité", extra={"section": "activity_summary", "error": str(e)[:200], "consequence": "fallback_zero"})
        return ActivitySummary(open_quotes=0, pending_orders=0, scheduled_interventions=0)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=CockpitDashboard)
def get_dashboard(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Dashboard complet du cockpit dirigeant."""
    return CockpitDashboard(
        kpis=get_kpis(db, tenant_id),
        alerts=get_alerts(db, tenant_id),
        treasury_summary=get_treasury_summary(db, tenant_id),
        sales_summary=get_sales_summary(db, tenant_id),
        activity_summary=get_activity_summary(db, tenant_id)
    )


@router.get("/decisions", response_model=PaginatedDecisions)
def get_pending_decisions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Liste des décisions en attente pour le dirigeant."""
    decisions = []
    datetime.utcnow()

    # Devis à valider
    try:
        result = db.execute(text("""
            SELECT id, number, customer_name, total, created_at
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'QUOTE'
            AND status = 'DRAFT'
            ORDER BY created_at DESC
            LIMIT 10
        """), {"tenant_id": tenant_id})
        for row in result:
            decisions.append(PendingDecision(
                id=str(row[0]),
                type="QUOTE_VALIDATION",
                title=f"Devis {row[1]} - {row[2]} ({row[3]}€)",
                severity="ORANGE",
                module="commercial",
                created_at=row[4],
                action_url=f"/commercial/quotes/{row[0]}"
            ))
    except Exception as e:
        logger.warning("[COCKPIT] Échec récupération devis en attente", extra={"decision": "quotes", "error": str(e)[:200], "consequence": "decision_skipped"})

    # Factures importantes à valider
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
        """), {"tenant_id": tenant_id})
        for row in result:
            decisions.append(PendingDecision(
                id=str(row[0]),
                type="INVOICE_VALIDATION",
                title=f"Facture {row[1]} - {row[2]} ({row[3]}€)",
                severity="RED" if row[3] > 10000 else "ORANGE",
                module="invoicing",
                created_at=row[4],
                action_url=f"/invoicing/{row[0]}"
            ))
    except Exception as e:
        logger.warning("[COCKPIT] Échec récupération factures à valider", extra={"decision": "invoices", "error": str(e)[:200], "consequence": "decision_skipped"})

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
        """), {"tenant_id": tenant_id})
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
        logger.warning("[COCKPIT] Échec récupération tickets support critiques", extra={"decision": "support", "error": str(e)[:200], "consequence": "decision_skipped"})

    total = len(decisions)
    paginated = decisions[skip:skip + limit]

    return PaginatedDecisions(items=paginated, total=total, page=skip // limit + 1, page_size=limit)


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Acquitter une alerte."""
    # Log l'acquittement
    return {"acknowledged": True, "alert_id": alert_id}
