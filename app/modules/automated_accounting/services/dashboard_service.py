"""
AZALS MODULE M2A - Service Dashboard
=====================================

Service de génération des tableaux de bord par vue utilisateur.

Trois vues distinctes:
- Dirigeant: Piloter & décider (simplifié, aucun jargon comptable)
- Assistante: Centraliser & organiser (documentaire)
- Expert-comptable: Contrôler, valider, certifier (exceptions uniquement)
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models import (
    AccountingAlert,
    AccountingDocument,
    AIClassification,
    AlertSeverity,
    AlertType,
    AutoEntry,
    ConfidenceLevel,
    DashboardMetrics,
    DocumentStatus,
    DocumentType,
    PaymentStatus,
    ReconciliationHistory,
    ReconciliationStatusAuto,
    SyncedTransaction,
)
from ..schemas import (
    AIPerformanceStats,
    AlertResponse,
    AssistanteDashboard,
    CashForecastItem,
    CashForecastResponse,
    CashPositionResponse,
    DirigeantDashboard,
    DocumentCountsByStatus,
    DocumentCountsByType,
    ExpertComptableDashboard,
    InvoicesSummary,
    ReconciliationStats,
    ResultSummary,
    ValidationQueueItem,
    ValidationQueueResponse,
)
from .bank_pull_service import BankPullService

logger = logging.getLogger(__name__)


class DashboardService:
    """Service de génération des tableaux de bord.

    Chaque vue a accès aux mêmes données mais avec une présentation différente:
    - Dirigeant: Vision simplifiée, pas de jargon, décision rapide
    - Assistante: Gestion documentaire, pas d'accès bancaire
    - Expert-comptable: Validation des exceptions, détail technique
    """

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2
        self.bank_service = BankPullService(db, tenant_id, user_id)

    # =========================================================================
    # DASHBOARD DIRIGEANT
    # =========================================================================

    def get_dirigeant_dashboard(
        self,
        sync_bank: bool = True
    ) -> DirigeantDashboard:
        """Génère le dashboard pour la vue Dirigeant.

        Ce dashboard est conçu pour:
        - Piloter l'entreprise en un coup d'œil
        - Prendre des décisions rapidement
        - ZÉRO jargon comptable
        - ZÉRO saisie possible

        Args:
            sync_bank: Si True, synchronise la banque avant (mode PULL)

        Returns:
            DirigeantDashboard avec toutes les données
        """
        # Synchronise la banque si demandé (mode PULL à l'ouverture)
        if sync_bank:
            self.bank_service.sync_all(sync_type="ON_DEMAND")

        # Position de trésorerie
        cash_position = self._get_cash_position()

        # Prévision de trésorerie
        cash_forecast = self._get_cash_forecast()

        # Résumé factures
        invoices_summary = self._get_invoices_summary()

        # Résultat estimé
        result_summary = self._get_result_summary()

        # Alertes critiques uniquement
        alerts = self._get_critical_alerts()

        # Fraîcheur des données
        data_freshness = self._calculate_data_freshness()

        return DirigeantDashboard(
            cash_position=cash_position,
            cash_forecast=cash_forecast,
            invoices_summary=invoices_summary,
            result_summary=result_summary,
            alerts=alerts,
            data_freshness=data_freshness,
            last_updated=datetime.utcnow()
        )

    def _get_cash_position(self) -> CashPositionResponse:
        """Calcule la position de trésorerie actuelle."""
        balance_info = self.bank_service.get_total_balance()

        accounts = self.bank_service.get_synced_accounts()
        accounts_data = []
        for account in accounts:
            accounts_data.append({
                "name": account.account_name,
                "balance": float(account.balance_current or 0),
                "currency": account.balance_currency,
            })

        return CashPositionResponse(
            total_balance=balance_info["total_eur"],
            available_balance=balance_info["total_eur"],  # Simplifié
            currency="EUR",
            accounts=accounts_data,
            last_sync_at=balance_info.get("last_updated"),
            freshness_score=balance_info["freshness_score"]
        )

    def _get_cash_forecast(self, days: int = 30) -> CashForecastResponse:
        """Génère les prévisions de trésorerie."""
        today = date.today()
        current_balance = self.bank_service.get_total_balance()["total_eur"]

        forecast_items = []
        running_balance = current_balance

        # Récupère les échéances à venir
        invoices_to_pay = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type == DocumentType.INVOICE_RECEIVED,
            AccountingDocument.payment_status.in_([
                PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID
            ]),
            AccountingDocument.due_date >= today,
            AccountingDocument.due_date <= today + timedelta(days=days)
        ).all()

        invoices_to_collect = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type == DocumentType.INVOICE_SENT,
            AccountingDocument.payment_status.in_([
                PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID
            ]),
            AccountingDocument.due_date >= today,
            AccountingDocument.due_date <= today + timedelta(days=days)
        ).all()

        # Agrège par semaine
        for week in range(0, days, 7):
            week_start = today + timedelta(days=week)
            week_end = week_start + timedelta(days=6)

            # Décaissements prévus
            payments = sum(
                float(inv.amount_remaining or inv.amount_total or 0)
                for inv in invoices_to_pay
                if inv.due_date and week_start <= inv.due_date <= week_end
            )

            # Encaissements prévus
            receipts = sum(
                float(inv.amount_remaining or inv.amount_total or 0)
                for inv in invoices_to_collect
                if inv.due_date and week_start <= inv.due_date <= week_end
            )

            closing = running_balance + Decimal(str(receipts)) - Decimal(str(payments))

            forecast_items.append(CashForecastItem(
                date=week_start,
                opening_balance=running_balance,
                expected_receipts=Decimal(str(receipts)),
                expected_payments=Decimal(str(payments)),
                expected_closing=closing
            ))

            running_balance = closing

        return CashForecastResponse(
            current_balance=current_balance,
            forecast_items=forecast_items,
            period_start=today,
            period_end=today + timedelta(days=days),
            warning_threshold=Decimal("5000"),  # À paramétrer
            alert_threshold=Decimal("0")
        )

    def _get_invoices_summary(self) -> InvoicesSummary:
        """Calcule le résumé des factures."""
        today = date.today()

        # Factures à payer
        to_pay = self.db.query(
            func.count(AccountingDocument.id),
            func.coalesce(func.sum(AccountingDocument.amount_total), 0)
        ).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type == DocumentType.INVOICE_RECEIVED,
            AccountingDocument.payment_status.in_([
                PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID
            ])
        ).first()

        # Factures à payer en retard
        overdue_to_pay = self.db.query(
            func.count(AccountingDocument.id),
            func.coalesce(func.sum(AccountingDocument.amount_total), 0)
        ).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type == DocumentType.INVOICE_RECEIVED,
            AccountingDocument.payment_status.in_([
                PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID
            ]),
            AccountingDocument.due_date < today
        ).first()

        # Factures à encaisser
        to_collect = self.db.query(
            func.count(AccountingDocument.id),
            func.coalesce(func.sum(AccountingDocument.amount_total), 0)
        ).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type == DocumentType.INVOICE_SENT,
            AccountingDocument.payment_status.in_([
                PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID
            ])
        ).first()

        # Factures à encaisser en retard
        overdue_to_collect = self.db.query(
            func.count(AccountingDocument.id),
            func.coalesce(func.sum(AccountingDocument.amount_total), 0)
        ).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type == DocumentType.INVOICE_SENT,
            AccountingDocument.payment_status.in_([
                PaymentStatus.UNPAID, PaymentStatus.PARTIALLY_PAID
            ]),
            AccountingDocument.due_date < today
        ).first()

        return InvoicesSummary(
            to_pay_count=to_pay[0] or 0,
            to_pay_amount=Decimal(str(to_pay[1] or 0)),
            overdue_to_pay_count=overdue_to_pay[0] or 0,
            overdue_to_pay_amount=Decimal(str(overdue_to_pay[1] or 0)),
            to_collect_count=to_collect[0] or 0,
            to_collect_amount=Decimal(str(to_collect[1] or 0)),
            overdue_to_collect_count=overdue_to_collect[0] or 0,
            overdue_to_collect_amount=Decimal(str(overdue_to_collect[1] or 0))
        )

    def _get_result_summary(self, period: str = "MONTH") -> ResultSummary:
        """Calcule le résultat estimé de la période."""
        today = date.today()

        if period == "MONTH":
            start = today.replace(day=1)
            end = today
        elif period == "QUARTER":
            quarter = (today.month - 1) // 3
            start = date(today.year, quarter * 3 + 1, 1)
            end = today
        else:  # YEAR
            start = date(today.year, 1, 1)
            end = today

        # Revenus (factures clients)
        revenue = self.db.query(
            func.coalesce(func.sum(AccountingDocument.amount_untaxed), 0)
        ).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type == DocumentType.INVOICE_SENT,
            AccountingDocument.document_date >= start,
            AccountingDocument.document_date <= end
        ).scalar() or Decimal("0")

        # Charges (factures fournisseurs + notes de frais)
        expenses = self.db.query(
            func.coalesce(func.sum(AccountingDocument.amount_untaxed), 0)
        ).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.document_type.in_([
                DocumentType.INVOICE_RECEIVED,
                DocumentType.EXPENSE_NOTE
            ]),
            AccountingDocument.document_date >= start,
            AccountingDocument.document_date <= end
        ).scalar() or Decimal("0")

        return ResultSummary(
            revenue=Decimal(str(revenue)),
            expenses=Decimal(str(expenses)),
            result=Decimal(str(revenue)) - Decimal(str(expenses)),
            period=period,
            period_start=start,
            period_end=end
        )

    def _get_critical_alerts(self, limit: int = 5) -> list[AlertResponse]:
        """Récupère les alertes critiques pour le dirigeant."""
        alerts = self.db.query(AccountingAlert).filter(
            AccountingAlert.tenant_id == self.tenant_id,
            not AccountingAlert.is_resolved,
            AccountingAlert.severity.in_([
                AlertSeverity.ERROR, AlertSeverity.CRITICAL
            ]),
            or_(
                AccountingAlert.target_roles.contains(["DIRIGEANT"]),
                AccountingAlert.alert_type.in_([
                    AlertType.CASH_FLOW_WARNING,
                    AlertType.OVERDUE_PAYMENT
                ])
            )
        ).order_by(
            AccountingAlert.severity.desc(),
            AccountingAlert.created_at.desc()
        ).limit(limit).all()

        return [self._alert_to_response(a) for a in alerts]

    def _calculate_data_freshness(self) -> Decimal:
        """Calcule le score de fraîcheur des données."""
        balance_info = self.bank_service.get_total_balance()
        return balance_info.get("freshness_score", Decimal("0"))

    # =========================================================================
    # DASHBOARD ASSISTANTE
    # =========================================================================

    def get_assistante_dashboard(self) -> AssistanteDashboard:
        """Génère le dashboard pour la vue Assistante.

        Ce dashboard est conçu pour:
        - Centraliser & organiser les documents
        - Voir les statuts des pièces
        - Ajouter du contexte (commentaires, projet)
        - JAMAIS comptabiliser
        - AUCUN accès bancaire

        Returns:
            AssistanteDashboard avec les données documentaires
        """
        # Compte total
        total = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id
        ).count()

        # Par statut
        status_counts = self._get_document_counts_by_status()

        # Par type
        type_counts = self._get_document_counts_by_type()

        # Documents récents
        recent = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id
        ).order_by(
            AccountingDocument.received_at.desc()
        ).limit(20).all()

        # Alertes documentaires
        alerts = self._get_documentary_alerts()

        return AssistanteDashboard(
            total_documents=total,
            documents_by_status=status_counts,
            documents_by_type=type_counts,
            recent_documents=[self._doc_to_response(d) for d in recent],
            alerts=alerts,
            last_updated=datetime.utcnow()
        )

    def _get_document_counts_by_status(self) -> DocumentCountsByStatus:
        """Compte les documents par statut."""
        counts = dict(
            self.db.query(
                AccountingDocument.status,
                func.count(AccountingDocument.id)
            ).filter(
                AccountingDocument.tenant_id == self.tenant_id
            ).group_by(AccountingDocument.status).all()
        )

        return DocumentCountsByStatus(
            received=counts.get(DocumentStatus.RECEIVED, 0),
            processing=counts.get(DocumentStatus.PROCESSING, 0),
            analyzed=counts.get(DocumentStatus.ANALYZED, 0),
            pending_validation=counts.get(DocumentStatus.PENDING_VALIDATION, 0),
            validated=counts.get(DocumentStatus.VALIDATED, 0),
            accounted=counts.get(DocumentStatus.ACCOUNTED, 0),
            rejected=counts.get(DocumentStatus.REJECTED, 0),
            error=counts.get(DocumentStatus.ERROR, 0)
        )

    def _get_document_counts_by_type(self) -> DocumentCountsByType:
        """Compte les documents par type."""
        counts = dict(
            self.db.query(
                AccountingDocument.document_type,
                func.count(AccountingDocument.id)
            ).filter(
                AccountingDocument.tenant_id == self.tenant_id
            ).group_by(AccountingDocument.document_type).all()
        )

        return DocumentCountsByType(
            invoice_received=counts.get(DocumentType.INVOICE_RECEIVED, 0),
            invoice_sent=counts.get(DocumentType.INVOICE_SENT, 0),
            expense_note=counts.get(DocumentType.EXPENSE_NOTE, 0),
            credit_note_received=counts.get(DocumentType.CREDIT_NOTE_RECEIVED, 0),
            credit_note_sent=counts.get(DocumentType.CREDIT_NOTE_SENT, 0),
            quote=counts.get(DocumentType.QUOTE, 0),
            purchase_order=counts.get(DocumentType.PURCHASE_ORDER, 0),
            other=counts.get(DocumentType.OTHER, 0)
        )

    def _get_documentary_alerts(self) -> list[AlertResponse]:
        """Récupère les alertes documentaires pour l'assistante."""
        alerts = self.db.query(AccountingAlert).filter(
            AccountingAlert.tenant_id == self.tenant_id,
            not AccountingAlert.is_resolved,
            AccountingAlert.alert_type.in_([
                AlertType.DOCUMENT_UNREADABLE,
                AlertType.MISSING_INFO,
                AlertType.DUPLICATE_SUSPECTED
            ])
        ).order_by(
            AccountingAlert.created_at.desc()
        ).limit(20).all()

        return [self._alert_to_response(a) for a in alerts]

    # =========================================================================
    # DASHBOARD EXPERT-COMPTABLE
    # =========================================================================

    def get_expert_comptable_dashboard(self) -> ExpertComptableDashboard:
        """Génère le dashboard pour la vue Expert-comptable.

        Ce dashboard est conçu pour:
        - Voir UNIQUEMENT les exceptions
        - Valider les écritures en masse
        - Accéder aux justificatifs + OCR
        - Voir le taux de confiance IA
        - Valider/clôturer les périodes
        - JAMAIS ressaisir
        - JAMAIS reconstituer bancaire

        Returns:
            ExpertComptableDashboard avec les données de validation
        """
        # File de validation
        validation_queue = self._get_validation_queue()

        # Performance IA
        ai_performance = self._get_ai_performance()

        # Stats rapprochement
        reconciliation_stats = self._get_reconciliation_stats()

        # Alertes non résolues
        alerts = self._get_expert_alerts()

        # Statut des périodes
        periods_status = self._get_periods_status()

        return ExpertComptableDashboard(
            validation_queue=validation_queue,
            ai_performance=ai_performance,
            reconciliation_stats=reconciliation_stats,
            unresolved_alerts=alerts,
            periods_status=periods_status,
            last_updated=datetime.utcnow()
        )

    def _get_validation_queue(self) -> ValidationQueueResponse:
        """Récupère la file de validation."""
        # Documents en attente de validation
        documents = self.db.query(AccountingDocument).filter(
            AccountingDocument.tenant_id == self.tenant_id,
            AccountingDocument.requires_validation,
            AccountingDocument.status.in_([
                DocumentStatus.PENDING_VALIDATION,
                DocumentStatus.ANALYZED
            ])
        ).order_by(
            AccountingDocument.ai_confidence_score.asc()
        ).limit(100).all()

        items = []
        high_priority = 0
        medium_priority = 0
        low_priority = 0

        for doc in documents:
            # Récupère la classification IA
            # SÉCURITÉ: Toujours filtrer par tenant_id
            classification = self.db.query(AIClassification).filter(
                AIClassification.tenant_id == self.tenant_id,
                AIClassification.document_id == doc.id
            ).order_by(AIClassification.created_at.desc()).first()

            # Récupère l'écriture auto
            # SÉCURITÉ: Toujours filtrer par tenant_id
            auto_entry = self.db.query(AutoEntry).filter(
                AutoEntry.tenant_id == self.tenant_id,
                AutoEntry.document_id == doc.id
            ).order_by(AutoEntry.created_at.desc()).first()

            # Récupère les alertes du document
            # SÉCURITÉ: Toujours filtrer par tenant_id
            doc_alerts = self.db.query(AccountingAlert).filter(
                AccountingAlert.tenant_id == self.tenant_id,
                AccountingAlert.document_id == doc.id,
                not AccountingAlert.is_resolved
            ).all()

            # Priorité basée sur la confiance
            if doc.ai_confidence in [ConfidenceLevel.VERY_LOW]:
                high_priority += 1
            elif doc.ai_confidence in [ConfidenceLevel.LOW]:
                medium_priority += 1
            else:
                low_priority += 1

            items.append(ValidationQueueItem(
                document=self._doc_to_response(doc),
                ai_classification=self._classification_to_response(classification) if classification else None,
                auto_entry=self._auto_entry_to_response(auto_entry) if auto_entry else None,
                alerts=[self._alert_to_response(a) for a in doc_alerts]
            ))

        return ValidationQueueResponse(
            items=items,
            total=len(documents),
            high_priority_count=high_priority,
            medium_priority_count=medium_priority,
            low_priority_count=low_priority
        )

    def _get_ai_performance(self) -> AIPerformanceStats:
        """Calcule les statistiques de performance IA."""
        total = self.db.query(AIClassification).filter(
            AIClassification.tenant_id == self.tenant_id
        ).count()

        if total == 0:
            return AIPerformanceStats(
                total_processed=0,
                auto_validated_count=0,
                auto_validated_rate=Decimal("0"),
                corrections_count=0,
                corrections_rate=Decimal("0"),
                average_confidence=Decimal("0"),
                by_document_type={}
            )

        # Auto-validés (haute confiance)
        auto_validated = self.db.query(AIClassification).filter(
            AIClassification.tenant_id == self.tenant_id,
            AIClassification.overall_confidence == ConfidenceLevel.HIGH
        ).count()

        # Corrections
        corrections = self.db.query(AIClassification).filter(
            AIClassification.tenant_id == self.tenant_id,
            AIClassification.was_corrected
        ).count()

        # Confiance moyenne
        avg = self.db.query(
            func.avg(AIClassification.overall_confidence_score)
        ).filter(
            AIClassification.tenant_id == self.tenant_id
        ).scalar() or 0

        return AIPerformanceStats(
            total_processed=total,
            auto_validated_count=auto_validated,
            auto_validated_rate=Decimal(str(round(auto_validated / total * 100, 2))),
            corrections_count=corrections,
            corrections_rate=Decimal(str(round(corrections / total * 100, 2))),
            average_confidence=Decimal(str(round(float(avg), 2))),
            by_document_type={}
        )

    def _get_reconciliation_stats(self) -> ReconciliationStats:
        """Calcule les statistiques de rapprochement."""
        total = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.tenant_id == self.tenant_id
        ).count()

        matched_auto = self.db.query(ReconciliationHistory).filter(
            ReconciliationHistory.tenant_id == self.tenant_id,
            ReconciliationHistory.reconciliation_type == "auto",
            not ReconciliationHistory.is_cancelled
        ).count()

        matched_manual = self.db.query(ReconciliationHistory).filter(
            ReconciliationHistory.tenant_id == self.tenant_id,
            ReconciliationHistory.reconciliation_type == "manual",
            not ReconciliationHistory.is_cancelled
        ).count()

        unmatched = self.db.query(SyncedTransaction).filter(
            SyncedTransaction.tenant_id == self.tenant_id,
            SyncedTransaction.reconciliation_status.in_([
                ReconciliationStatusAuto.PENDING,
                ReconciliationStatusAuto.UNMATCHED
            ])
        ).count()

        match_rate = Decimal("0")
        if total > 0:
            match_rate = Decimal(str(round((matched_auto + matched_manual) / total * 100, 2)))

        return ReconciliationStats(
            total_transactions=total,
            matched_auto=matched_auto,
            matched_manual=matched_manual,
            unmatched=unmatched,
            match_rate=match_rate
        )

    def _get_expert_alerts(self) -> list[AlertResponse]:
        """Récupère les alertes pour l'expert-comptable."""
        alerts = self.db.query(AccountingAlert).filter(
            AccountingAlert.tenant_id == self.tenant_id,
            not AccountingAlert.is_resolved,
            or_(
                AccountingAlert.target_roles.contains(["EXPERT_COMPTABLE"]),
                AccountingAlert.alert_type.in_([
                    AlertType.LOW_CONFIDENCE,
                    AlertType.TAX_ERROR,
                    AlertType.AMOUNT_MISMATCH,
                    AlertType.RECONCILIATION_ISSUE
                ])
            )
        ).order_by(
            AccountingAlert.severity.desc(),
            AccountingAlert.created_at.desc()
        ).limit(50).all()

        return [self._alert_to_response(a) for a in alerts]

    def _get_periods_status(self) -> list[dict[str, Any]]:
        """Récupère le statut des périodes comptables."""
        # Simplifié - à implémenter avec le module Finance
        today = date.today()
        return [
            {
                "period": today.strftime("%B %Y"),
                "start_date": today.replace(day=1).isoformat(),
                "end_date": today.isoformat(),
                "status": "OPEN",
                "documents_count": self.db.query(AccountingDocument).filter(
                    AccountingDocument.tenant_id == self.tenant_id,
                    AccountingDocument.document_date >= today.replace(day=1)
                ).count()
            }
        ]

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _doc_to_response(self, doc: AccountingDocument) -> dict[str, Any]:
        """Convertit un document en réponse."""
        return {
            "id": str(doc.id),
            "document_type": doc.document_type.value if doc.document_type else None,
            "status": doc.status.value if doc.status else None,
            "reference": doc.reference,
            "partner_name": doc.partner_name,
            "amount_total": float(doc.amount_total) if doc.amount_total else None,
            "document_date": doc.document_date.isoformat() if doc.document_date else None,
            "due_date": doc.due_date.isoformat() if doc.due_date else None,
            "ai_confidence": doc.ai_confidence.value if doc.ai_confidence else None,
            "ai_confidence_score": float(doc.ai_confidence_score) if doc.ai_confidence_score else None,
            "received_at": doc.received_at.isoformat() if doc.received_at else None,
        }

    def _alert_to_response(self, alert: AccountingAlert) -> AlertResponse:
        """Convertit une alerte en réponse."""
        return AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            entity_type=alert.entity_type,
            entity_id=alert.entity_id,
            document_id=alert.document_id,
            is_read=alert.is_read,
            is_resolved=alert.is_resolved,
            resolved_at=alert.resolved_at,
            resolution_notes=alert.resolution_notes,
            created_at=alert.created_at
        )

    def _classification_to_response(self, classification: AIClassification) -> dict[str, Any]:
        """Convertit une classification en réponse."""
        return {
            "id": str(classification.id),
            "model_name": classification.model_name,
            "overall_confidence": classification.overall_confidence.value,
            "overall_confidence_score": float(classification.overall_confidence_score),
            "suggested_account_code": classification.suggested_account_code,
            "expense_category": classification.expense_category,
            "was_corrected": classification.was_corrected,
        }

    def _auto_entry_to_response(self, entry: AutoEntry) -> dict[str, Any]:
        """Convertit une écriture auto en réponse."""
        return {
            "id": str(entry.id),
            "confidence_level": entry.confidence_level.value,
            "confidence_score": float(entry.confidence_score),
            "auto_validated": entry.auto_validated,
            "requires_review": entry.requires_review,
            "is_posted": entry.is_posted,
            "proposed_lines": entry.proposed_lines,
        }

    # =========================================================================
    # MÉTRIQUES STOCKÉES
    # =========================================================================

    def save_daily_metrics(self):
        """Sauvegarde les métriques quotidiennes."""
        today = date.today()

        # Vérifie si déjà calculé
        existing = self.db.query(DashboardMetrics).filter(
            DashboardMetrics.tenant_id == self.tenant_id,
            DashboardMetrics.metric_date == today,
            DashboardMetrics.metric_type == "DAILY"
        ).first()

        if existing:
            return existing

        # Calcule les métriques
        invoices = self._get_invoices_summary()
        result = self._get_result_summary()
        balance_info = self.bank_service.get_total_balance()

        metrics = DashboardMetrics(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            metric_date=today,
            metric_type="DAILY",
            cash_balance=balance_info["total_eur"],
            cash_balance_updated_at=balance_info.get("last_updated"),
            invoices_to_pay_count=invoices.to_pay_count,
            invoices_to_pay_amount=invoices.to_pay_amount,
            invoices_overdue_count=invoices.overdue_to_pay_count,
            invoices_overdue_amount=invoices.overdue_to_pay_amount,
            invoices_to_collect_count=invoices.to_collect_count,
            invoices_to_collect_amount=invoices.to_collect_amount,
            invoices_overdue_collect_count=invoices.overdue_to_collect_count,
            invoices_overdue_collect_amount=invoices.overdue_to_collect_amount,
            revenue_period=result.revenue,
            expenses_period=result.expenses,
            result_period=result.result,
            documents_pending_count=self.db.query(AccountingDocument).filter(
                AccountingDocument.tenant_id == self.tenant_id,
                AccountingDocument.requires_validation
            ).count(),
            documents_error_count=self.db.query(AccountingDocument).filter(
                AccountingDocument.tenant_id == self.tenant_id,
                AccountingDocument.status == DocumentStatus.ERROR
            ).count(),
            transactions_unreconciled=self.db.query(SyncedTransaction).filter(
                SyncedTransaction.tenant_id == self.tenant_id,
                SyncedTransaction.reconciliation_status == ReconciliationStatusAuto.PENDING
            ).count(),
            data_freshness_score=balance_info.get("freshness_score", Decimal("0")),
            last_bank_sync=balance_info.get("last_updated"),
            calculated_at=datetime.utcnow()
        )

        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)

        return metrics
