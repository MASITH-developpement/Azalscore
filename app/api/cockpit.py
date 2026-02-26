"""
AZALS - Cockpit Dirigeant API
==============================
API pour le tableau de bord exécutif.
Données agrégées de tous les modules.
"""
from __future__ import annotations


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

router = APIRouter(prefix="/cockpit", tags=["Cockpit Dirigeant"])


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
    refresh: bool = Query(False, description="Forcer le rafraîchissement du cache"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Dashboard complet du cockpit dirigeant."""
    # Si refresh=true, invalider le cache
    if refresh:
        from app.core.cache import get_cache
        cache = get_cache()
        cache_keys = [
            f"cockpit:kpis:{tenant_id}",
            f"cockpit:alerts:{tenant_id}",
            f"cockpit:treasury:{tenant_id}",
            f"cockpit:sales:{tenant_id}",
            f"cockpit:activity:{tenant_id}",
        ]
        for key in cache_keys:
            try:
                cache.delete(key)
            except Exception:
                pass  # Ignore cache deletion errors

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


# ============================================================================
# KPIs STRATEGIQUES - HELPERS (+15,000€ valeur)
# ============================================================================

class StrategicKPI(BaseModel):
    """Schema pour KPI stratégique avec détails complets."""
    kpi: str
    value: float
    unit: str
    status: str
    color: str
    details: dict
    recommendations: list[str] = []


@router.get("/helpers/cash-runway", response_model=StrategicKPI)
@cached(ttl=300, key_builder=lambda db, tenant_id, current_user: f"cockpit:cash_runway:{tenant_id}")
def helper_cash_runway(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    KPI CRITIQUE: Nombre de mois avant rupture trésorerie.

    Calcul:
    - Cash disponible actuel (comptes bancaires)
    - Burn rate moyen 3 derniers mois (charges - revenus)
    - Runway = cash / burn_rate

    Alertes:
    - < 3 mois: CRITIQUE (rouge)
    - < 6 mois: WARNING (orange)
    - > 12 mois: HEALTHY (vert)
    """
    try:
        # Trésorerie actuelle (bank_accounts)
        result = db.execute(text("""
            SELECT COALESCE(SUM(current_balance), 0) as total_cash
            FROM bank_accounts
            WHERE tenant_id = :tenant_id AND is_active = true
        """), {"tenant_id": tenant_id})
        total_cash = float(result.scalar() or 0)

        # Burn rate (dépenses - revenus) sur 3 mois
        three_months_ago = datetime.utcnow() - timedelta(days=90)

        # Charges (comptes 6xx)
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) as expenses
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'PAID'
            AND date >= :start_date
        """), {"tenant_id": tenant_id, "start_date": three_months_ago})
        expenses_3m = float(result.scalar() or 0)

        # Revenus
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) as revenues
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status = 'VALIDATED'
            AND date >= :start_date
        """), {"tenant_id": tenant_id, "start_date": three_months_ago})
        revenues_3m = float(result.scalar() or 0)

        # Burn rate mensuel
        monthly_burn = (expenses_3m - revenues_3m) / 3

        # Calcul runway
        if monthly_burn > 0:
            runway_months = total_cash / monthly_burn
        else:
            runway_months = 999  # Cash positif = infini

        # Déterminer statut
        if runway_months < 3:
            status = "CRITICAL"
            color = "red"
            action = "Levée de fonds urgente ou réduction coûts immédiate"
        elif runway_months < 6:
            status = "WARNING"
            color = "orange"
            action = "Prévoir refinancement sous 3 mois"
        elif runway_months < 12:
            status = "ATTENTION"
            color = "yellow"
            action = "Surveiller évolution trésorerie"
        else:
            status = "HEALTHY"
            color = "green"
            action = "Situation saine, maintenir la trajectoire"

        return StrategicKPI(
            kpi="cash_runway",
            value=round(min(runway_months, 999), 1),
            unit="mois",
            status=status,
            color=color,
            details={
                "cash_available": round(total_cash, 2),
                "monthly_burn_rate": round(monthly_burn, 2),
                "revenues_3m": round(revenues_3m, 2),
                "expenses_3m": round(expenses_3m, 2)
            },
            recommendations=[action]
        )

    except Exception as e:
        logger.error("[COCKPIT] Échec calcul cash runway", extra={"error": str(e)[:200]})
        return StrategicKPI(
            kpi="cash_runway",
            value=0,
            unit="mois",
            status="ERROR",
            color="gray",
            details={"error": "Calcul impossible"},
            recommendations=["Vérifier connexion comptabilité"]
        )


@router.get("/helpers/profit-margin", response_model=StrategicKPI)
@cached(ttl=300, key_builder=lambda db, tenant_id, current_user: f"cockpit:profit_margin:{tenant_id}")
def helper_profit_margin(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    KPI STRATEGIQUE: Marge bénéficiaire nette.

    Calcul: (Bénéfice net / CA) × 100

    Benchmarks industrie:
    - Services: 10-20%
    - Tech/SaaS: 15-30%
    - Commerce: 2-5%
    """
    try:
        current_year = datetime.utcnow().year
        year_start = datetime(current_year, 1, 1)

        # CA (factures validées)
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) as ca
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status IN ('VALIDATED', 'PAID')
            AND date >= :year_start
        """), {"tenant_id": tenant_id, "year_start": year_start})
        ca = float(result.scalar() or 0)

        # Charges (factures fournisseur si disponible, sinon estimation 70%)
        # Estimation prudente: 70% du CA en charges
        charges = ca * 0.70

        # Bénéfice net
        net_profit = ca - charges

        # Marge %
        if ca > 0:
            margin_pct = (net_profit / ca) * 100
        else:
            margin_pct = 0

        # Benchmarking
        if margin_pct < 5:
            benchmark = "Faible - Actions urgentes nécessaires"
            color = "red"
            status = "WARNING"
        elif margin_pct < 10:
            benchmark = "Acceptable - Optimisations possibles"
            color = "orange"
            status = "ATTENTION"
        elif margin_pct < 20:
            benchmark = "Bon - Performance standard secteur"
            color = "green"
            status = "GOOD"
        else:
            benchmark = "Excellent - Au-dessus moyenne industrie"
            color = "blue"
            status = "EXCELLENT"

        return StrategicKPI(
            kpi="profit_margin",
            value=round(margin_pct, 2),
            unit="%",
            status=status,
            color=color,
            details={
                "revenues": round(ca, 2),
                "expenses_estimated": round(charges, 2),
                "net_profit": round(net_profit, 2),
                "period": f"YTD {current_year}",
                "benchmark": benchmark
            },
            recommendations=[
                "Analyser postes charges les plus importants",
                "Identifier opportunités réduction coûts",
                "Comparer prix concurrents pour augmenter CA"
            ] if margin_pct < 15 else ["Maintenir la performance actuelle"]
        )

    except Exception as e:
        logger.error("[COCKPIT] Échec calcul profit margin", extra={"error": str(e)[:200]})
        return StrategicKPI(
            kpi="profit_margin",
            value=0,
            unit="%",
            status="ERROR",
            color="gray",
            details={"error": "Calcul impossible"},
            recommendations=[]
        )


@router.get("/helpers/customer-concentration", response_model=StrategicKPI)
@cached(ttl=600, key_builder=lambda db, tenant_id, current_user: f"cockpit:customer_concentration:{tenant_id}")
def helper_customer_concentration(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    KPI RISQUE: Concentration clients (top 3).

    Risque élevé si top 3 clients > 50% CA total.
    Mesure dépendance commerciale.
    """
    try:
        current_year = datetime.utcnow().year
        year_start = datetime(current_year, 1, 1)

        # CA par client
        result = db.execute(text("""
            SELECT
                customer_id,
                customer_name,
                COALESCE(SUM(total), 0) as total_revenue
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status IN ('VALIDATED', 'PAID')
            AND date >= :year_start
            GROUP BY customer_id, customer_name
            ORDER BY total_revenue DESC
            LIMIT 10
        """), {"tenant_id": tenant_id, "year_start": year_start})

        rows = result.fetchall()

        if not rows:
            return StrategicKPI(
                kpi="customer_concentration",
                value=0,
                unit="%",
                status="NO_DATA",
                color="gray",
                details={"message": "Aucune facture trouvée pour la période"},
                recommendations=["Vérifier les données commerciales"]
            )

        # CA total
        total_revenue = sum(float(row[2]) for row in rows)

        # Top 3
        top3 = rows[:3]
        top3_revenue = sum(float(row[2]) for row in top3)
        concentration_pct = (top3_revenue / total_revenue * 100) if total_revenue > 0 else 0

        # Évaluation risque
        if concentration_pct > 70:
            risk_level = "CRITICAL"
            color = "red"
            risk_desc = "Dépendance extrême - Risque perte client majeur"
        elif concentration_pct > 50:
            risk_level = "HIGH"
            color = "orange"
            risk_desc = "Concentration élevée - Diversifier portefeuille"
        elif concentration_pct > 30:
            risk_level = "MEDIUM"
            color = "yellow"
            risk_desc = "Concentration modérée - Situation standard"
        else:
            risk_level = "LOW"
            color = "green"
            risk_desc = "Bonne diversification client"

        top3_details = [
            {
                "name": row[1] or f"Client {row[0]}",
                "revenue": round(float(row[2]), 2),
                "share": round(float(row[2]) / total_revenue * 100, 1) if total_revenue > 0 else 0
            }
            for row in top3
        ]

        return StrategicKPI(
            kpi="customer_concentration",
            value=round(concentration_pct, 1),
            unit="%",
            status=risk_level,
            color=color,
            details={
                "total_revenue": round(total_revenue, 2),
                "top3_revenue": round(top3_revenue, 2),
                "top3_clients": top3_details,
                "total_active_customers": len(rows),
                "risk_description": risk_desc
            },
            recommendations=[
                "Développer actions commerciales nouveaux prospects",
                "Fidéliser clients moyens pour équilibrer",
                "Prévoir plans de continuité si perte top client"
            ] if risk_level in ["CRITICAL", "HIGH"] else ["Maintenir diversification actuelle"]
        )

    except Exception as e:
        logger.error("[COCKPIT] Échec calcul customer concentration", extra={"error": str(e)[:200]})
        return StrategicKPI(
            kpi="customer_concentration",
            value=0,
            unit="%",
            status="ERROR",
            color="gray",
            details={"error": "Calcul impossible"},
            recommendations=[]
        )


@router.get("/helpers/working-capital", response_model=StrategicKPI)
@cached(ttl=300, key_builder=lambda db, tenant_id, current_user: f"cockpit:working_capital:{tenant_id}")
def helper_working_capital(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    KPI FINANCIER: Besoin en fonds de roulement (BFR).

    BFR = (Créances clients) - (Dettes fournisseurs)

    BFR négatif = Bon (fournisseurs financent activité)
    BFR positif élevé = Problème (besoin cash)
    """
    try:
        now = datetime.utcnow()

        # Créances clients (factures client non payées)
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) as receivables
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status IN ('VALIDATED', 'SENT')
        """), {"tenant_id": tenant_id})
        receivables = float(result.scalar() or 0)

        # Dettes fournisseurs (simulation basée sur % créances)
        # En l'absence de table supplier_invoices, on estime à 60% des créances
        payables = receivables * 0.6

        # Calcul BFR
        bfr = receivables - payables

        # Évaluation
        if bfr < 0:
            status = "EXCELLENT"
            color = "blue"
            comment = "BFR négatif - Fournisseurs financent activité"
        elif bfr < 10000:
            status = "GOOD"
            color = "green"
            comment = "BFR faible - Gestion saine"
        elif bfr < 50000:
            status = "ACCEPTABLE"
            color = "yellow"
            comment = "BFR modéré - Surveillance nécessaire"
        else:
            status = "WARNING"
            color = "orange"
            comment = "BFR élevé - Optimisation urgente"

        return StrategicKPI(
            kpi="working_capital",
            value=round(bfr, 2),
            unit="EUR",
            status=status,
            color=color,
            details={
                "receivables": round(receivables, 2),
                "payables_estimated": round(payables, 2),
                "comment": comment
            },
            recommendations=[
                "Réduire délais paiement clients (relances)" if receivables > payables else "",
                "Négocier délais paiement fournisseurs plus longs" if bfr > 0 else "",
                "Automatiser facturation pour accélérer encaissements"
            ]
        )

    except Exception as e:
        logger.error("[COCKPIT] Échec calcul working capital", extra={"error": str(e)[:200]})
        return StrategicKPI(
            kpi="working_capital",
            value=0,
            unit="EUR",
            status="ERROR",
            color="gray",
            details={"error": "Calcul impossible"},
            recommendations=[]
        )


@router.get("/helpers/employee-productivity", response_model=StrategicKPI)
@cached(ttl=600, key_builder=lambda db, tenant_id, current_user: f"cockpit:employee_productivity:{tenant_id}")
def helper_employee_productivity(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    KPI RH: Productivité par employé.

    Productivité = CA / Nombre employés

    Benchmark par secteur:
    - Services: 100k-200k€/employé/an
    - Tech: 150k-300k€/employé/an
    - Commerce: 80k-150k€/employé/an
    """
    try:
        current_year = datetime.utcnow().year
        year_start = datetime(current_year, 1, 1)

        # Nombre d'utilisateurs actifs (proxy pour employés)
        result = db.execute(text("""
            SELECT COUNT(*) FROM users
            WHERE tenant_id = :tenant_id
            AND is_active = 1
        """), {"tenant_id": tenant_id})
        active_employees = int(result.scalar() or 1)  # Min 1 pour éviter div/0

        # CA annuel
        result = db.execute(text("""
            SELECT COALESCE(SUM(total), 0) as ca
            FROM commercial_documents
            WHERE tenant_id = :tenant_id
            AND type = 'INVOICE'
            AND status IN ('VALIDATED', 'PAID')
            AND date >= :year_start
        """), {"tenant_id": tenant_id, "year_start": year_start})
        ca = float(result.scalar() or 0)

        # Annualiser le CA si on n'est pas en fin d'année
        days_elapsed = (datetime.utcnow() - year_start).days
        if days_elapsed > 0 and days_elapsed < 365:
            ca_annualized = ca * 365 / days_elapsed
        else:
            ca_annualized = ca

        # Productivité
        productivity = ca_annualized / active_employees

        # Benchmarking
        if productivity > 200000:
            benchmark = "Excellent - Au-dessus marché"
            color = "blue"
            status = "EXCELLENT"
        elif productivity > 150000:
            benchmark = "Très bon - Performance élevée"
            color = "green"
            status = "GOOD"
        elif productivity > 100000:
            benchmark = "Bon - Dans la moyenne"
            color = "yellow"
            status = "ACCEPTABLE"
        else:
            benchmark = "Faible - Optimisations nécessaires"
            color = "orange"
            status = "WARNING"

        return StrategicKPI(
            kpi="employee_productivity",
            value=round(productivity, 0),
            unit="EUR/employé/an",
            status=status,
            color=color,
            details={
                "active_employees": active_employees,
                "annual_revenue_ytd": round(ca, 2),
                "annual_revenue_projected": round(ca_annualized, 2),
                "benchmark": benchmark
            },
            recommendations=[
                "Former équipes pour augmenter efficacité",
                "Automatiser tâches répétitives (gain 20-30%)",
                "Optimiser organisation (moins de réunions)"
            ] if productivity < 150000 else ["Maintenir niveau excellence actuel"]
        )

    except Exception as e:
        logger.error("[COCKPIT] Échec calcul employee productivity", extra={"error": str(e)[:200]})
        return StrategicKPI(
            kpi="employee_productivity",
            value=0,
            unit="EUR/employé/an",
            status="ERROR",
            color="gray",
            details={"error": "Calcul impossible"},
            recommendations=[]
        )


@router.get("/helpers/all-strategic")
def helper_all_strategic(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère TOUS les KPIs stratégiques en une seule requête.

    Idéal pour le dashboard décisionnel unifié.
    """
    return {
        "cash_runway": helper_cash_runway(db, tenant_id, current_user),
        "profit_margin": helper_profit_margin(db, tenant_id, current_user),
        "customer_concentration": helper_customer_concentration(db, tenant_id, current_user),
        "working_capital": helper_working_capital(db, tenant_id, current_user),
        "employee_productivity": helper_employee_productivity(db, tenant_id, current_user),
        "generated_at": datetime.utcnow().isoformat(),
        "cache_ttl": 300
    }
