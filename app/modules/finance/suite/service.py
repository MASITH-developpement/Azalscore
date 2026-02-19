"""
AZALSCORE Finance Suite Service
================================

Service orchestrateur central pour la suite Finance.

Fonctionnalités:
- Coordination des modules finance
- Tableau de bord unifié
- Health check global
- Configuration centralisée
- Workflows cross-modules
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class ModuleStatus(str, Enum):
    """Statut d'un module."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AlertSeverity(str, Enum):
    """Sévérité d'une alerte."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class WorkflowType(str, Enum):
    """Type de workflow."""
    INVOICE_PROCESSING = "invoice_processing"
    PAYMENT_APPROVAL = "payment_approval"
    RECONCILIATION = "reconciliation"
    MONTH_END_CLOSE = "month_end_close"
    EXPENSE_REPORT = "expense_report"


class WorkflowStatus(str, Enum):
    """Statut d'un workflow."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class ModuleInfo:
    """Information sur un module."""
    name: str
    display_name: str
    description: str
    status: ModuleStatus
    version: str
    endpoint: str
    features: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    last_health_check: Optional[datetime] = None


@dataclass
class FinanceDashboard:
    """Tableau de bord finance consolidé."""
    tenant_id: str
    generated_at: datetime
    # Trésorerie
    current_balance: Decimal
    available_balance: Decimal
    projected_balance_30d: Decimal
    # Comptabilité
    pending_entries: int
    unreconciled_transactions: int
    # Factures
    invoices_pending: int
    invoices_overdue: int
    total_receivable: Decimal
    total_payable: Decimal
    # Cartes
    active_cards: int
    cards_near_limit: int
    # Alertes
    alerts: list[dict] = field(default_factory=list)
    # Modules
    modules_status: dict = field(default_factory=dict)


@dataclass
class SuiteConfig:
    """Configuration de la suite Finance."""
    tenant_id: str
    default_currency: str = "EUR"
    fiscal_year_start_month: int = 1
    auto_reconciliation_enabled: bool = True
    ocr_auto_processing: bool = True
    approval_workflow_enabled: bool = True
    alert_thresholds: dict = field(default_factory=dict)
    notification_settings: dict = field(default_factory=dict)
    integration_settings: dict = field(default_factory=dict)


@dataclass
class FinanceAlert:
    """Alerte finance."""
    id: str
    tenant_id: str
    severity: AlertSeverity
    module: str
    title: str
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class WorkflowInstance:
    """Instance de workflow."""
    id: str
    tenant_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    current_step: int
    total_steps: int
    data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    error_message: Optional[str] = None


# =============================================================================
# MODULE DEFINITIONS
# =============================================================================


FINANCE_MODULES = {
    "reconciliation": ModuleInfo(
        name="reconciliation",
        display_name="Rapprochement Bancaire IA",
        description="Rapprochement automatique intelligent des transactions bancaires",
        status=ModuleStatus.ACTIVE,
        version="1.0.0",
        endpoint="/v3/finance/reconciliation",
        features=["ai_matching", "multi_account", "suggestions", "batch_processing"],
    ),
    "invoice_ocr": ModuleInfo(
        name="invoice_ocr",
        display_name="OCR Factures",
        description="Extraction automatique des données de factures par OCR/IA",
        status=ModuleStatus.ACTIVE,
        version="1.0.0",
        endpoint="/v3/finance/invoice-ocr",
        features=["text_extraction", "data_validation", "vendor_recognition"],
    ),
    "cash_forecast": ModuleInfo(
        name="cash_forecast",
        display_name="Prévisionnel Trésorerie",
        description="Prévisions de trésorerie multi-scénarios",
        status=ModuleStatus.ACTIVE,
        version="1.0.0",
        endpoint="/v3/finance/cash-forecast",
        features=["multi_scenario", "ai_predictions", "alerts"],
    ),
    "auto_categorization": ModuleInfo(
        name="auto_categorization",
        display_name="Catégorisation Automatique",
        description="Catégorisation intelligente des transactions",
        status=ModuleStatus.ACTIVE,
        version="1.0.0",
        endpoint="/v3/finance/auto-categorization",
        features=["rule_engine", "ml_suggestions", "bulk_categorization"],
    ),
    "currency": ModuleInfo(
        name="currency",
        display_name="Devises & Taux de Change",
        description="Gestion des devises et conversions",
        status=ModuleStatus.ACTIVE,
        version="1.0.0",
        endpoint="/v3/finance/currency",
        features=["ecb_rates", "manual_rates", "batch_conversion"],
    ),
    "virtual_cards": ModuleInfo(
        name="virtual_cards",
        display_name="Cartes Virtuelles",
        description="Gestion des cartes bancaires virtuelles",
        status=ModuleStatus.ACTIVE,
        version="1.0.0",
        endpoint="/v3/finance/virtual-cards",
        features=["card_creation", "limits", "single_use", "merchant_blocking"],
    ),
    "integration": ModuleInfo(
        name="integration",
        display_name="Intégration Comptable",
        description="Synchronisation avec la comptabilité et la facturation",
        status=ModuleStatus.ACTIVE,
        version="1.0.0",
        endpoint="/v3/finance/integration",
        features=["accounting_sync", "invoice_sync", "mapping", "validation"],
    ),
}


# =============================================================================
# SERVICE
# =============================================================================


class FinanceSuiteService:
    """
    Service orchestrateur de la suite Finance.

    Multi-tenant: OUI - Toutes les données isolées par tenant
    Rôle: Coordination, monitoring, configuration
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        if not tenant_id:
            raise ValueError("tenant_id est requis")

        self.db = db
        self.tenant_id = tenant_id
        self._config: Optional[SuiteConfig] = None
        self._alerts: list[FinanceAlert] = []
        self._workflows: list[WorkflowInstance] = []

        logger.info(f"FinanceSuiteService initialisé pour tenant {tenant_id}")

    # =========================================================================
    # DASHBOARD
    # =========================================================================

    async def get_dashboard(self) -> FinanceDashboard:
        """
        Génère le tableau de bord finance consolidé.

        Agrège les données de tous les modules.
        """
        # Simuler les métriques (en production, requête les vrais services)
        dashboard = FinanceDashboard(
            tenant_id=self.tenant_id,
            generated_at=datetime.now(),
            # Trésorerie
            current_balance=Decimal("125000.00"),
            available_balance=Decimal("120000.00"),
            projected_balance_30d=Decimal("135000.00"),
            # Comptabilité
            pending_entries=12,
            unreconciled_transactions=8,
            # Factures
            invoices_pending=15,
            invoices_overdue=3,
            total_receivable=Decimal("45000.00"),
            total_payable=Decimal("28000.00"),
            # Cartes
            active_cards=5,
            cards_near_limit=1,
            # Alertes actives
            alerts=await self._get_active_alerts_summary(),
            # Statut modules
            modules_status=await self._get_modules_status(),
        )

        return dashboard

    async def _get_active_alerts_summary(self) -> list[dict]:
        """Résumé des alertes actives."""
        active = [a for a in self._alerts if not a.acknowledged]
        return [
            {
                "id": a.id,
                "severity": a.severity.value,
                "module": a.module,
                "title": a.title,
                "created_at": a.created_at.isoformat(),
            }
            for a in active[:10]  # Top 10
        ]

    async def _get_modules_status(self) -> dict:
        """Statut de tous les modules."""
        return {
            name: {
                "status": module.status.value,
                "display_name": module.display_name,
                "endpoint": module.endpoint,
            }
            for name, module in FINANCE_MODULES.items()
        }

    # =========================================================================
    # MODULES
    # =========================================================================

    async def list_modules(self) -> list[ModuleInfo]:
        """Liste tous les modules de la suite."""
        return list(FINANCE_MODULES.values())

    async def get_module(self, module_name: str) -> Optional[ModuleInfo]:
        """Récupère les informations d'un module."""
        return FINANCE_MODULES.get(module_name)

    async def get_module_health(self, module_name: str) -> dict:
        """Health check d'un module spécifique."""
        module = FINANCE_MODULES.get(module_name)
        if not module:
            return {"error": "Module non trouvé"}

        return {
            "module": module_name,
            "status": module.status.value,
            "version": module.version,
            "endpoint": module.endpoint,
            "features": module.features,
            "last_check": datetime.now().isoformat(),
        }

    async def get_suite_health(self) -> dict:
        """Health check global de la suite."""
        modules_health = {}
        healthy_count = 0
        degraded_count = 0
        error_count = 0

        for name, module in FINANCE_MODULES.items():
            modules_health[name] = module.status.value
            if module.status == ModuleStatus.ACTIVE:
                healthy_count += 1
            elif module.status == ModuleStatus.DEGRADED:
                degraded_count += 1
            else:
                error_count += 1

        total = len(FINANCE_MODULES)
        overall_status = (
            "healthy" if healthy_count == total
            else "degraded" if error_count == 0
            else "unhealthy"
        )

        return {
            "suite": "finance",
            "status": overall_status,
            "version": "1.0.0",
            "modules_total": total,
            "modules_healthy": healthy_count,
            "modules_degraded": degraded_count,
            "modules_error": error_count,
            "modules": modules_health,
            "checked_at": datetime.now().isoformat(),
        }

    # =========================================================================
    # CONFIGURATION
    # =========================================================================

    async def get_config(self) -> SuiteConfig:
        """Récupère la configuration de la suite."""
        if not self._config:
            self._config = SuiteConfig(
                tenant_id=self.tenant_id,
                alert_thresholds={
                    "low_balance": Decimal("10000"),
                    "card_limit_warning": 80,  # %
                    "overdue_invoice_days": 30,
                },
                notification_settings={
                    "email_enabled": True,
                    "slack_enabled": False,
                    "webhook_enabled": False,
                },
                integration_settings={
                    "accounting_auto_sync": True,
                    "invoice_auto_sync": True,
                },
            )
        return self._config

    async def update_config(
        self,
        default_currency: Optional[str] = None,
        fiscal_year_start_month: Optional[int] = None,
        auto_reconciliation_enabled: Optional[bool] = None,
        ocr_auto_processing: Optional[bool] = None,
        approval_workflow_enabled: Optional[bool] = None,
        alert_thresholds: Optional[dict] = None,
        notification_settings: Optional[dict] = None,
        integration_settings: Optional[dict] = None,
    ) -> SuiteConfig:
        """Met à jour la configuration."""
        config = await self.get_config()

        if default_currency is not None:
            config.default_currency = default_currency
        if fiscal_year_start_month is not None:
            config.fiscal_year_start_month = fiscal_year_start_month
        if auto_reconciliation_enabled is not None:
            config.auto_reconciliation_enabled = auto_reconciliation_enabled
        if ocr_auto_processing is not None:
            config.ocr_auto_processing = ocr_auto_processing
        if approval_workflow_enabled is not None:
            config.approval_workflow_enabled = approval_workflow_enabled
        if alert_thresholds is not None:
            config.alert_thresholds.update(alert_thresholds)
        if notification_settings is not None:
            config.notification_settings.update(notification_settings)
        if integration_settings is not None:
            config.integration_settings.update(integration_settings)

        logger.info(f"Configuration mise à jour pour tenant {self.tenant_id}")
        return config

    # =========================================================================
    # ALERTS
    # =========================================================================

    async def create_alert(
        self,
        severity: AlertSeverity,
        module: str,
        title: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> FinanceAlert:
        """Crée une alerte."""
        alert = FinanceAlert(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            severity=severity,
            module=module,
            title=title,
            message=message,
            metadata=metadata or {},
        )

        self._alerts.append(alert)

        logger.info(f"Alerte créée: [{severity.value}] {title}")
        return alert

    async def list_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        module: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
    ) -> list[FinanceAlert]:
        """Liste les alertes."""
        alerts = [a for a in self._alerts if a.tenant_id == self.tenant_id]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if module:
            alerts = [a for a in alerts if a.module == module]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        return sorted(
            alerts,
            key=lambda a: a.created_at,
            reverse=True
        )[:limit]

    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str,
    ) -> bool:
        """Acquitte une alerte."""
        alert = next(
            (a for a in self._alerts if a.id == alert_id and a.tenant_id == self.tenant_id),
            None
        )

        if not alert:
            return False

        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now()

        logger.info(f"Alerte {alert_id} acquittée par {user_id}")
        return True

    async def get_alert_summary(self) -> dict:
        """Résumé des alertes."""
        alerts = [a for a in self._alerts if a.tenant_id == self.tenant_id]
        active = [a for a in alerts if not a.acknowledged]

        by_severity = {}
        for severity in AlertSeverity:
            by_severity[severity.value] = len([
                a for a in active if a.severity == severity
            ])

        by_module = {}
        for a in active:
            by_module[a.module] = by_module.get(a.module, 0) + 1

        return {
            "total_alerts": len(alerts),
            "active_alerts": len(active),
            "acknowledged_alerts": len(alerts) - len(active),
            "by_severity": by_severity,
            "by_module": by_module,
        }

    # =========================================================================
    # WORKFLOWS
    # =========================================================================

    async def start_workflow(
        self,
        workflow_type: WorkflowType,
        data: dict,
        created_by: Optional[str] = None,
    ) -> WorkflowInstance:
        """Démarre un workflow."""
        # Définir le nombre d'étapes selon le type
        steps = {
            WorkflowType.INVOICE_PROCESSING: 4,
            WorkflowType.PAYMENT_APPROVAL: 3,
            WorkflowType.RECONCILIATION: 2,
            WorkflowType.MONTH_END_CLOSE: 5,
            WorkflowType.EXPENSE_REPORT: 3,
        }

        workflow = WorkflowInstance(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            workflow_type=workflow_type,
            status=WorkflowStatus.IN_PROGRESS,
            current_step=1,
            total_steps=steps.get(workflow_type, 3),
            data=data,
            created_by=created_by,
        )

        self._workflows.append(workflow)

        logger.info(f"Workflow {workflow_type.value} démarré: {workflow.id}")
        return workflow

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """Récupère un workflow."""
        return next(
            (w for w in self._workflows
             if w.id == workflow_id and w.tenant_id == self.tenant_id),
            None
        )

    async def list_workflows(
        self,
        workflow_type: Optional[WorkflowType] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 50,
    ) -> list[WorkflowInstance]:
        """Liste les workflows."""
        workflows = [w for w in self._workflows if w.tenant_id == self.tenant_id]

        if workflow_type:
            workflows = [w for w in workflows if w.workflow_type == workflow_type]

        if status:
            workflows = [w for w in workflows if w.status == status]

        return sorted(
            workflows,
            key=lambda w: w.created_at,
            reverse=True
        )[:limit]

    async def advance_workflow(
        self,
        workflow_id: str,
        step_data: Optional[dict] = None,
    ) -> Optional[WorkflowInstance]:
        """Avance un workflow à l'étape suivante."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        if workflow.status not in [WorkflowStatus.IN_PROGRESS, WorkflowStatus.AWAITING_APPROVAL]:
            return workflow

        if step_data:
            workflow.data.update(step_data)

        workflow.current_step += 1
        workflow.updated_at = datetime.now()

        if workflow.current_step > workflow.total_steps:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()

        logger.info(f"Workflow {workflow_id} avancé à étape {workflow.current_step}")
        return workflow

    async def cancel_workflow(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Annule un workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False

        workflow.status = WorkflowStatus.CANCELLED
        workflow.error_message = reason
        workflow.updated_at = datetime.now()

        logger.info(f"Workflow {workflow_id} annulé: {reason}")
        return True

    # =========================================================================
    # REPORTING
    # =========================================================================

    async def get_finance_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Résumé financier pour une période."""
        # Simuler les données (en production, agréger les vraies données)
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "cash_flow": {
                "opening_balance": "100000.00",
                "closing_balance": "125000.00",
                "total_inflows": "75000.00",
                "total_outflows": "50000.00",
                "net_change": "25000.00",
            },
            "invoices": {
                "issued": 45,
                "paid": 38,
                "overdue": 5,
                "total_issued": "120000.00",
                "total_collected": "95000.00",
            },
            "expenses": {
                "total": "50000.00",
                "by_category": {
                    "salaries": "30000.00",
                    "rent": "5000.00",
                    "utilities": "2000.00",
                    "other": "13000.00",
                },
            },
            "cards": {
                "transactions": 125,
                "total_spent": "8500.00",
            },
            "reconciliation": {
                "transactions_reconciled": 180,
                "auto_match_rate": "92%",
            },
        }

    async def get_kpis(self) -> dict:
        """KPIs finance."""
        return {
            "cash_runway_days": 180,
            "dso": 35,  # Days Sales Outstanding
            "dpo": 28,  # Days Payable Outstanding
            "quick_ratio": 1.5,
            "working_capital": "45000.00",
            "auto_reconciliation_rate": "92%",
            "ocr_accuracy": "97%",
            "invoice_processing_time_hours": 2.5,
        }
