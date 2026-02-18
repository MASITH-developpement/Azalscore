"""
AZALSCORE Finance Cash Forecast Service
========================================

Service de prévision de trésorerie avec analyse de scénarios.

Fonctionnalités:
- Prévisions basées sur historique
- Scénarios multiples (base, optimiste, pessimiste)
- Alertes automatiques de seuil
- Intégration factures clients/fournisseurs
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================


class ScenarioType(str, Enum):
    """Type de scénario de prévision."""

    BASE = "base"  # Scénario de base (prévision standard)
    OPTIMISTIC = "optimistic"  # Scénario optimiste (+10-20%)
    PESSIMISTIC = "pessimistic"  # Scénario pessimiste (-10-20%)
    STRESS = "stress"  # Scénario de stress (-30-40%)


class ForecastGranularity(str, Enum):
    """Granularité de la prévision."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AlertSeverity(str, Enum):
    """Sévérité d'alerte de trésorerie."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Type d'alerte."""

    LOW_BALANCE = "low_balance"  # Solde sous seuil
    NEGATIVE_BALANCE = "negative_balance"  # Solde négatif prévu
    HIGH_CONCENTRATION = "high_concentration"  # Concentration échéances
    OVERDRAFT_RISK = "overdraft_risk"  # Risque de découvert


@dataclass
class ForecastEntry:
    """Entrée de prévision pour une période."""

    date: date
    opening_balance: Decimal = Decimal("0")
    closing_balance: Decimal = Decimal("0")

    # Encaissements
    inflows_expected: Decimal = Decimal("0")  # Factures clients échues
    inflows_probable: Decimal = Decimal("0")  # Factures clients probables
    inflows_recurring: Decimal = Decimal("0")  # Revenus récurrents
    total_inflows: Decimal = Decimal("0")

    # Décaissements
    outflows_expected: Decimal = Decimal("0")  # Factures fournisseurs échues
    outflows_probable: Decimal = Decimal("0")  # Factures fournisseurs probables
    outflows_recurring: Decimal = Decimal("0")  # Charges récurrentes
    outflows_payroll: Decimal = Decimal("0")  # Salaires
    outflows_taxes: Decimal = Decimal("0")  # Impôts et taxes
    total_outflows: Decimal = Decimal("0")

    # Solde net
    net_change: Decimal = Decimal("0")

    # Confiance
    confidence: float = 0.0


@dataclass
class ForecastPeriod:
    """Période de prévision avec détail."""

    id: str
    start_date: date
    end_date: date
    scenario: ScenarioType = ScenarioType.BASE
    granularity: ForecastGranularity = ForecastGranularity.DAILY

    entries: list[ForecastEntry] = field(default_factory=list)

    # Totaux
    total_inflows: Decimal = Decimal("0")
    total_outflows: Decimal = Decimal("0")
    net_change: Decimal = Decimal("0")

    # Statistiques
    min_balance: Decimal = Decimal("0")
    max_balance: Decimal = Decimal("0")
    avg_balance: Decimal = Decimal("0")
    min_balance_date: Optional[date] = None

    # Confiance globale
    confidence: float = 0.0


@dataclass
class CashAlert:
    """Alerte de trésorerie."""

    id: str
    type: AlertType
    severity: AlertSeverity
    date: date
    message: str
    amount: Optional[Decimal] = None
    threshold: Optional[Decimal] = None
    recommendation: Optional[str] = None


@dataclass
class ForecastResult:
    """Résultat complet de prévision."""

    success: bool
    tenant_id: str
    generated_at: datetime = field(default_factory=datetime.utcnow)

    # Solde actuel
    current_balance: Decimal = Decimal("0")
    current_date: date = field(default_factory=date.today)

    # Prévisions par scénario
    forecasts: list[ForecastPeriod] = field(default_factory=list)

    # Alertes
    alerts: list[CashAlert] = field(default_factory=list)

    # Résumé
    summary: dict = field(default_factory=dict)

    # Erreur
    error: Optional[str] = None


@dataclass
class RecurringItem:
    """Élément récurrent (charge ou revenu)."""

    id: str
    name: str
    amount: Decimal
    frequency: str  # daily, weekly, monthly, quarterly, yearly
    next_date: date
    is_inflow: bool  # True = revenu, False = charge
    end_date: Optional[date] = None
    confidence: float = 95.0


# =============================================================================
# SERVICE PRINCIPAL
# =============================================================================


class CashForecastService:
    """
    Service de prévision de trésorerie.

    Fournit des prévisions court/moyen/long terme basées sur:
    - Factures clients en attente de paiement
    - Factures fournisseurs à payer
    - Charges et revenus récurrents
    - Historique des flux

    Usage:
        service = CashForecastService(db, tenant_id)

        # Prévision 90 jours
        result = await service.generate_forecast(days=90)

        # Avec scénarios
        result = await service.generate_forecast(
            days=90,
            scenarios=[ScenarioType.BASE, ScenarioType.PESSIMISTIC]
        )
    """

    # Paramètres de prévision
    DEFAULT_DAYS = 90
    MAX_DAYS = 365

    # Seuils d'alerte par défaut
    LOW_BALANCE_THRESHOLD = Decimal("5000")
    CRITICAL_BALANCE_THRESHOLD = Decimal("1000")

    # Facteurs de scénario
    SCENARIO_FACTORS = {
        ScenarioType.BASE: {"inflows": Decimal("1.0"), "outflows": Decimal("1.0")},
        ScenarioType.OPTIMISTIC: {"inflows": Decimal("1.15"), "outflows": Decimal("0.90")},
        ScenarioType.PESSIMISTIC: {"inflows": Decimal("0.85"), "outflows": Decimal("1.10")},
        ScenarioType.STRESS: {"inflows": Decimal("0.60"), "outflows": Decimal("1.30")},
    }

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        low_balance_threshold: Optional[Decimal] = None,
        critical_balance_threshold: Optional[Decimal] = None,
    ):
        """
        Initialise le service de prévision.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant (obligatoire)
            low_balance_threshold: Seuil d'alerte solde bas
            critical_balance_threshold: Seuil d'alerte critique
        """
        if not tenant_id:
            raise ValueError("tenant_id est obligatoire")

        self.db = db
        self.tenant_id = tenant_id
        self.low_balance_threshold = low_balance_threshold or self.LOW_BALANCE_THRESHOLD
        self.critical_balance_threshold = critical_balance_threshold or self.CRITICAL_BALANCE_THRESHOLD

        self._logger = logging.LoggerAdapter(
            logger,
            extra={"tenant_id": tenant_id, "service": "CashForecastService"},
        )

    # =========================================================================
    # GÉNÉRATION DE PRÉVISION
    # =========================================================================

    async def generate_forecast(
        self,
        days: int = DEFAULT_DAYS,
        scenarios: Optional[list[ScenarioType]] = None,
        granularity: ForecastGranularity = ForecastGranularity.DAILY,
        include_recurring: bool = True,
        include_invoices: bool = True,
    ) -> ForecastResult:
        """
        Génère une prévision de trésorerie.

        Args:
            days: Nombre de jours de prévision (max 365)
            scenarios: Scénarios à calculer (défaut: BASE uniquement)
            granularity: Granularité (daily, weekly, monthly)
            include_recurring: Inclure charges/revenus récurrents
            include_invoices: Inclure factures en attente

        Returns:
            ForecastResult avec prévisions et alertes
        """
        self._logger.info(
            f"Génération prévision: {days} jours, scénarios={scenarios}",
            extra={"days": days, "granularity": granularity.value},
        )

        if days > self.MAX_DAYS:
            days = self.MAX_DAYS

        if scenarios is None:
            scenarios = [ScenarioType.BASE]

        try:
            # 1. Récupérer le solde actuel
            current_balance = await self._get_current_balance()

            # 2. Récupérer les données de base
            pending_receivables = await self._get_pending_receivables(days)
            pending_payables = await self._get_pending_payables(days)
            recurring_items = await self._get_recurring_items() if include_recurring else []

            # 3. Générer les prévisions par scénario
            forecasts = []
            for scenario in scenarios:
                forecast = await self._generate_scenario_forecast(
                    scenario=scenario,
                    days=days,
                    granularity=granularity,
                    current_balance=current_balance,
                    receivables=pending_receivables,
                    payables=pending_payables,
                    recurring=recurring_items,
                )
                forecasts.append(forecast)

            # 4. Générer les alertes
            alerts = self._generate_alerts(forecasts)

            # 5. Construire le résumé
            summary = self._build_summary(forecasts, alerts)

            return ForecastResult(
                success=True,
                tenant_id=self.tenant_id,
                current_balance=current_balance,
                current_date=date.today(),
                forecasts=forecasts,
                alerts=alerts,
                summary=summary,
            )

        except Exception as e:
            self._logger.error(f"Erreur génération prévision: {e}", exc_info=True)
            return ForecastResult(
                success=False,
                tenant_id=self.tenant_id,
                error=str(e),
            )

    async def _generate_scenario_forecast(
        self,
        scenario: ScenarioType,
        days: int,
        granularity: ForecastGranularity,
        current_balance: Decimal,
        receivables: list[dict],
        payables: list[dict],
        recurring: list[RecurringItem],
    ) -> ForecastPeriod:
        """Génère la prévision pour un scénario donné."""
        start_date = date.today()
        end_date = start_date + timedelta(days=days)

        factors = self.SCENARIO_FACTORS[scenario]
        entries = []

        running_balance = current_balance
        min_balance = current_balance
        max_balance = current_balance
        min_balance_date = start_date

        total_inflows = Decimal("0")
        total_outflows = Decimal("0")

        # Générer les entrées selon la granularité
        current_date = start_date
        while current_date <= end_date:
            # Calculer la fin de la période selon la granularité
            if granularity == ForecastGranularity.DAILY:
                period_end = current_date
            elif granularity == ForecastGranularity.WEEKLY:
                period_end = min(current_date + timedelta(days=6), end_date)
            else:  # MONTHLY
                next_month = current_date.replace(day=28) + timedelta(days=4)
                period_end = min(next_month.replace(day=1) - timedelta(days=1), end_date)

            # Calculer les flux pour cette période
            entry = self._calculate_period_entry(
                start=current_date,
                end=period_end,
                opening_balance=running_balance,
                receivables=receivables,
                payables=payables,
                recurring=recurring,
                factors=factors,
            )

            entries.append(entry)

            # Mettre à jour le solde courant
            running_balance = entry.closing_balance
            total_inflows += entry.total_inflows
            total_outflows += entry.total_outflows

            # Tracker min/max
            if entry.closing_balance < min_balance:
                min_balance = entry.closing_balance
                min_balance_date = entry.date

            if entry.closing_balance > max_balance:
                max_balance = entry.closing_balance

            # Passer à la période suivante
            if granularity == ForecastGranularity.DAILY:
                current_date += timedelta(days=1)
            elif granularity == ForecastGranularity.WEEKLY:
                current_date += timedelta(days=7)
            else:
                current_date = period_end + timedelta(days=1)

        # Calculer la confiance globale
        confidence = self._calculate_forecast_confidence(entries, days, scenario)

        # Calculer la moyenne
        if entries:
            avg_balance = sum(e.closing_balance for e in entries) / len(entries)
        else:
            avg_balance = current_balance

        return ForecastPeriod(
            id=str(uuid4()),
            start_date=start_date,
            end_date=end_date,
            scenario=scenario,
            granularity=granularity,
            entries=entries,
            total_inflows=total_inflows,
            total_outflows=total_outflows,
            net_change=total_inflows - total_outflows,
            min_balance=min_balance,
            max_balance=max_balance,
            avg_balance=avg_balance,
            min_balance_date=min_balance_date,
            confidence=confidence,
        )

    def _calculate_period_entry(
        self,
        start: date,
        end: date,
        opening_balance: Decimal,
        receivables: list[dict],
        payables: list[dict],
        recurring: list[RecurringItem],
        factors: dict,
    ) -> ForecastEntry:
        """Calcule les flux pour une période donnée."""
        inflows_expected = Decimal("0")
        inflows_probable = Decimal("0")
        inflows_recurring = Decimal("0")

        outflows_expected = Decimal("0")
        outflows_probable = Decimal("0")
        outflows_recurring = Decimal("0")
        outflows_payroll = Decimal("0")
        outflows_taxes = Decimal("0")

        # Factures clients (créances)
        for recv in receivables:
            due_date = recv.get("due_date")
            if due_date and start <= due_date <= end:
                amount = Decimal(str(recv.get("amount", 0))) * factors["inflows"]
                if recv.get("probability", 100) >= 80:
                    inflows_expected += amount
                else:
                    inflows_probable += amount

        # Factures fournisseurs (dettes)
        for pay in payables:
            due_date = pay.get("due_date")
            if due_date and start <= due_date <= end:
                amount = Decimal(str(pay.get("amount", 0))) * factors["outflows"]
                if pay.get("probability", 100) >= 80:
                    outflows_expected += amount
                else:
                    outflows_probable += amount

        # Éléments récurrents
        for item in recurring:
            if self._is_recurring_in_period(item, start, end):
                amount = item.amount
                if item.is_inflow:
                    inflows_recurring += amount * factors["inflows"]
                else:
                    # Catégoriser les charges
                    if "salaire" in item.name.lower() or "payroll" in item.name.lower():
                        outflows_payroll += amount * factors["outflows"]
                    elif "taxe" in item.name.lower() or "impôt" in item.name.lower():
                        outflows_taxes += amount * factors["outflows"]
                    else:
                        outflows_recurring += amount * factors["outflows"]

        # Totaux
        total_inflows = inflows_expected + inflows_probable + inflows_recurring
        total_outflows = (
            outflows_expected + outflows_probable + outflows_recurring +
            outflows_payroll + outflows_taxes
        )
        net_change = total_inflows - total_outflows
        closing_balance = opening_balance + net_change

        # Confiance de l'entrée
        if total_inflows + total_outflows > 0:
            expected_ratio = (inflows_expected + outflows_expected) / (total_inflows + total_outflows + Decimal("0.01"))
            confidence = float(expected_ratio * 100)
        else:
            confidence = 90.0  # Haute confiance si pas de flux

        return ForecastEntry(
            date=end,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            inflows_expected=inflows_expected,
            inflows_probable=inflows_probable,
            inflows_recurring=inflows_recurring,
            total_inflows=total_inflows,
            outflows_expected=outflows_expected,
            outflows_probable=outflows_probable,
            outflows_recurring=outflows_recurring,
            outflows_payroll=outflows_payroll,
            outflows_taxes=outflows_taxes,
            total_outflows=total_outflows,
            net_change=net_change,
            confidence=confidence,
        )

    def _is_recurring_in_period(
        self,
        item: RecurringItem,
        start: date,
        end: date,
    ) -> bool:
        """Vérifie si un élément récurrent tombe dans la période."""
        if item.end_date and item.end_date < start:
            return False

        next_occurrence = item.next_date
        while next_occurrence <= end:
            if next_occurrence >= start:
                return True
            # Calculer la prochaine occurrence
            if item.frequency == "daily":
                next_occurrence += timedelta(days=1)
            elif item.frequency == "weekly":
                next_occurrence += timedelta(weeks=1)
            elif item.frequency == "monthly":
                # Approximation: +30 jours
                next_occurrence += timedelta(days=30)
            elif item.frequency == "quarterly":
                next_occurrence += timedelta(days=90)
            elif item.frequency == "yearly":
                next_occurrence += timedelta(days=365)
            else:
                break

        return False

    # =========================================================================
    # RÉCUPÉRATION DES DONNÉES
    # =========================================================================

    async def _get_current_balance(self) -> Decimal:
        """Récupère le solde actuel de trésorerie."""
        # NOTE: Phase 2 - Intégration bank_service.get_total_balance()
        return Decimal("50000.00")

    async def _get_pending_receivables(self, days: int) -> list[dict]:
        """Récupère les créances en attente."""
        # NOTE: Phase 2 - Intégration invoice_service.get_pending_receivables()
        today = date.today()
        return [
            {
                "id": "inv-001",
                "customer": "Client A",
                "amount": "5000.00",
                "due_date": today + timedelta(days=15),
                "probability": 95,
            },
            {
                "id": "inv-002",
                "customer": "Client B",
                "amount": "3500.00",
                "due_date": today + timedelta(days=30),
                "probability": 85,
            },
            {
                "id": "inv-003",
                "customer": "Client C",
                "amount": "8000.00",
                "due_date": today + timedelta(days=45),
                "probability": 70,
            },
        ]

    async def _get_pending_payables(self, days: int) -> list[dict]:
        """Récupère les dettes en attente."""
        # NOTE: Phase 2 - Intégration invoice_service.get_pending_payables()
        today = date.today()
        return [
            {
                "id": "bill-001",
                "vendor": "Fournisseur X",
                "amount": "2500.00",
                "due_date": today + timedelta(days=10),
                "probability": 100,
            },
            {
                "id": "bill-002",
                "vendor": "Fournisseur Y",
                "amount": "4000.00",
                "due_date": today + timedelta(days=25),
                "probability": 100,
            },
        ]

    async def _get_recurring_items(self) -> list[RecurringItem]:
        """Récupère les éléments récurrents."""
        # NOTE: Phase 2 - Intégration recurring_service.list_items()
        today = date.today()
        return [
            RecurringItem(
                id="rec-001",
                name="Loyer",
                amount=Decimal("3000.00"),
                frequency="monthly",
                next_date=today.replace(day=1) + timedelta(days=30),
                is_inflow=False,
            ),
            RecurringItem(
                id="rec-002",
                name="Salaires",
                amount=Decimal("15000.00"),
                frequency="monthly",
                next_date=today.replace(day=25) if today.day < 25 else today.replace(day=25) + timedelta(days=30),
                is_inflow=False,
            ),
            RecurringItem(
                id="rec-003",
                name="Abonnement SaaS",
                amount=Decimal("500.00"),
                frequency="monthly",
                next_date=today + timedelta(days=15),
                is_inflow=True,
            ),
        ]

    # =========================================================================
    # ALERTES
    # =========================================================================

    def _generate_alerts(self, forecasts: list[ForecastPeriod]) -> list[CashAlert]:
        """Génère les alertes basées sur les prévisions."""
        alerts = []

        for forecast in forecasts:
            # Alerte solde minimum bas
            if forecast.min_balance < self.critical_balance_threshold:
                alerts.append(CashAlert(
                    id=str(uuid4()),
                    type=AlertType.NEGATIVE_BALANCE if forecast.min_balance < 0 else AlertType.LOW_BALANCE,
                    severity=AlertSeverity.CRITICAL,
                    date=forecast.min_balance_date or forecast.start_date,
                    message=f"Solde critique prévu: {forecast.min_balance:.2f}€ (scénario {forecast.scenario.value})",
                    amount=forecast.min_balance,
                    threshold=self.critical_balance_threshold,
                    recommendation="Envisager un financement court terme ou accélérer les encaissements",
                ))
            elif forecast.min_balance < self.low_balance_threshold:
                alerts.append(CashAlert(
                    id=str(uuid4()),
                    type=AlertType.LOW_BALANCE,
                    severity=AlertSeverity.WARNING,
                    date=forecast.min_balance_date or forecast.start_date,
                    message=f"Solde bas prévu: {forecast.min_balance:.2f}€ (scénario {forecast.scenario.value})",
                    amount=forecast.min_balance,
                    threshold=self.low_balance_threshold,
                    recommendation="Surveiller les encaissements et décaissements",
                ))

            # Alerte solde négatif
            for entry in forecast.entries:
                if entry.closing_balance < 0:
                    alerts.append(CashAlert(
                        id=str(uuid4()),
                        type=AlertType.NEGATIVE_BALANCE,
                        severity=AlertSeverity.CRITICAL,
                        date=entry.date,
                        message=f"Solde négatif prévu: {entry.closing_balance:.2f}€",
                        amount=entry.closing_balance,
                        recommendation="Action immédiate requise pour éviter le découvert",
                    ))
                    break  # Une seule alerte par forecast

        # Dédoublonner et trier par sévérité
        unique_alerts = {a.date: a for a in sorted(alerts, key=lambda x: x.severity.value)}
        return list(unique_alerts.values())[:10]  # Max 10 alertes

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _calculate_forecast_confidence(
        self,
        entries: list[ForecastEntry],
        days: int,
        scenario: ScenarioType,
    ) -> float:
        """Calcule la confiance globale de la prévision."""
        if not entries:
            return 0.0

        # Base: moyenne des confiances des entrées
        avg_confidence = sum(e.confidence for e in entries) / len(entries)

        # Pénalité pour les prévisions longues
        if days > 30:
            penalty = min(20, (days - 30) * 0.3)
            avg_confidence -= penalty

        # Pénalité pour scénarios extrêmes
        if scenario == ScenarioType.STRESS:
            avg_confidence -= 10
        elif scenario == ScenarioType.OPTIMISTIC:
            avg_confidence -= 5

        return max(0, min(100, avg_confidence))

    def _build_summary(
        self,
        forecasts: list[ForecastPeriod],
        alerts: list[CashAlert],
    ) -> dict:
        """Construit le résumé de la prévision."""
        base_forecast = next(
            (f for f in forecasts if f.scenario == ScenarioType.BASE),
            forecasts[0] if forecasts else None,
        )

        if not base_forecast:
            return {}

        critical_alerts = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        warning_alerts = len([a for a in alerts if a.severity == AlertSeverity.WARNING])

        return {
            "period_days": (base_forecast.end_date - base_forecast.start_date).days,
            "total_inflows": str(base_forecast.total_inflows),
            "total_outflows": str(base_forecast.total_outflows),
            "net_change": str(base_forecast.net_change),
            "min_balance": str(base_forecast.min_balance),
            "max_balance": str(base_forecast.max_balance),
            "avg_balance": str(base_forecast.avg_balance),
            "confidence": base_forecast.confidence,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "health_status": "critical" if critical_alerts > 0 else "warning" if warning_alerts > 0 else "good",
        }

    # =========================================================================
    # MÉTHODES PUBLIQUES ADDITIONNELLES
    # =========================================================================

    async def get_cash_position(self) -> dict:
        """
        Retourne la position de trésorerie actuelle.

        Returns:
            Dict avec solde actuel et détails par compte
        """
        current = await self._get_current_balance()
        return {
            "total_balance": str(current),
            "date": date.today().isoformat(),
            "accounts": [],  # TODO: Détail par compte
        }

    async def simulate_transaction(
        self,
        amount: Decimal,
        transaction_date: date,
        is_inflow: bool,
    ) -> ForecastResult:
        """
        Simule l'impact d'une transaction sur les prévisions.

        Args:
            amount: Montant de la transaction
            transaction_date: Date de la transaction
            is_inflow: True si encaissement, False si décaissement

        Returns:
            ForecastResult avec impact de la transaction
        """
        # Générer la prévision de base
        base_result = await self.generate_forecast(days=90)

        # Modifier les prévisions avec la transaction
        for forecast in base_result.forecasts:
            for entry in forecast.entries:
                if entry.date >= transaction_date:
                    if is_inflow:
                        entry.closing_balance += amount
                    else:
                        entry.closing_balance -= amount

            # Recalculer min/max
            if forecast.entries:
                balances = [e.closing_balance for e in forecast.entries]
                forecast.min_balance = min(balances)
                forecast.max_balance = max(balances)

        # Régénérer les alertes
        base_result.alerts = self._generate_alerts(base_result.forecasts)
        base_result.summary = self._build_summary(base_result.forecasts, base_result.alerts)

        return base_result

    async def get_alert_summary(self) -> dict:
        """
        Retourne un résumé des alertes de trésorerie.

        Returns:
            Dict avec nombre d'alertes par sévérité
        """
        result = await self.generate_forecast(days=30)

        return {
            "total_alerts": len(result.alerts),
            "critical": len([a for a in result.alerts if a.severity == AlertSeverity.CRITICAL]),
            "warning": len([a for a in result.alerts if a.severity == AlertSeverity.WARNING]),
            "info": len([a for a in result.alerts if a.severity == AlertSeverity.INFO]),
            "alerts": [
                {
                    "type": a.type.value,
                    "severity": a.severity.value,
                    "date": a.date.isoformat(),
                    "message": a.message,
                }
                for a in result.alerts[:5]
            ],
        }
