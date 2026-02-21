"""
AZALS MODULE - BUDGET: Repository
==================================

Couche d'acces aux donnees pour le module budgetaire.

Applique l'isolation multi-tenant et les regles de soft delete.

Auteur: AZALSCORE Team
Version: 2.0.0
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from .models import (
    Budget,
    BudgetActual,
    BudgetAlert,
    BudgetApprovalRule,
    BudgetCategory,
    BudgetConsolidation,
    BudgetForecast,
    BudgetLine,
    BudgetPeriod,
    BudgetPeriodAmount,
    BudgetRevision,
    BudgetRevisionDetail,
    BudgetScenario,
    BudgetScenarioLine,
    BudgetStatus,
    BudgetTemplate,
    BudgetType,
    SeasonalProfile,
    AlertSeverity,
    AlertStatus,
    RevisionStatus,
)


class BudgetRepository:
    """
    Repository pour l'acces aux donnees budgetaires.

    Applique automatiquement:
    - Filtrage par tenant_id
    - Exclusion des enregistrements soft-deleted
    """

    def __init__(self, db: Session, tenant_id: str):
        """
        Initialise le repository.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour l'isolation
        """
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # BASE QUERY METHODS
    # =========================================================================

    def _base_query(self, model):
        """Query de base filtree par tenant_id."""
        return self.db.query(model).filter(model.tenant_id == self.tenant_id)

    def _base_query_active(self, model):
        """Query de base excluant les soft-deleted."""
        return self._base_query(model).filter(model.is_deleted == False)

    # =========================================================================
    # BUDGET CATEGORY METHODS
    # =========================================================================

    def get_category(self, category_id: UUID) -> Optional[BudgetCategory]:
        """Recupere une categorie par son ID."""
        return self._base_query_active(BudgetCategory).filter(
            BudgetCategory.id == category_id
        ).first()

    def get_category_by_code(self, code: str) -> Optional[BudgetCategory]:
        """Recupere une categorie par son code."""
        return self._base_query_active(BudgetCategory).filter(
            BudgetCategory.code == code
        ).first()

    def list_categories(
        self,
        parent_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Tuple[List[BudgetCategory], int]:
        """Liste les categories avec pagination."""
        query = self._base_query_active(BudgetCategory)

        if parent_id is not None:
            query = query.filter(BudgetCategory.parent_id == parent_id)
        elif parent_id is None:
            # Categories racines par defaut
            pass

        if is_active is not None:
            query = query.filter(BudgetCategory.is_active == is_active)

        total = query.count()
        offset = (page - 1) * per_page
        items = query.order_by(
            BudgetCategory.sort_order,
            BudgetCategory.code
        ).offset(offset).limit(per_page).all()

        return items, total

    def get_category_tree(self) -> List[BudgetCategory]:
        """Recupere l'arbre complet des categories."""
        return self._base_query_active(BudgetCategory).order_by(
            BudgetCategory.path,
            BudgetCategory.sort_order
        ).all()

    def create_category(self, category: BudgetCategory) -> BudgetCategory:
        """Cree une categorie."""
        category.tenant_id = self.tenant_id
        self.db.add(category)
        self.db.flush()
        return category

    def update_category(
        self,
        category_id: UUID,
        updates: Dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> Optional[BudgetCategory]:
        """Met a jour une categorie."""
        category = self.get_category(category_id)
        if not category:
            return None

        for key, value in updates.items():
            if hasattr(category, key):
                setattr(category, key, value)

        category.updated_at = datetime.utcnow()
        category.updated_by = updated_by
        category.version += 1

        self.db.flush()
        return category

    def soft_delete_category(
        self,
        category_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Soft delete une categorie."""
        category = self.get_category(category_id)
        if not category:
            return False

        category.is_deleted = True
        category.deleted_at = datetime.utcnow()
        category.deleted_by = deleted_by
        self.db.flush()
        return True

    # =========================================================================
    # BUDGET METHODS
    # =========================================================================

    def get_budget(self, budget_id: UUID) -> Optional[Budget]:
        """Recupere un budget par son ID."""
        return self._base_query_active(Budget).filter(
            Budget.id == budget_id
        ).first()

    def get_budget_with_lines(self, budget_id: UUID) -> Optional[Budget]:
        """Recupere un budget avec ses lignes."""
        return self._base_query_active(Budget).options(
            joinedload(Budget.lines).joinedload(BudgetLine.category),
            joinedload(Budget.periods)
        ).filter(Budget.id == budget_id).first()

    def get_budget_by_code(self, code: str) -> Optional[Budget]:
        """Recupere un budget par son code."""
        return self._base_query_active(Budget).filter(
            Budget.code == code
        ).first()

    def list_budgets(
        self,
        budget_type: Optional[BudgetType] = None,
        status: Optional[BudgetStatus] = None,
        fiscal_year: Optional[int] = None,
        entity_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Budget], int]:
        """Liste les budgets avec filtres et pagination."""
        query = self._base_query_active(Budget)

        if budget_type:
            query = query.filter(Budget.budget_type == budget_type)

        if status:
            query = query.filter(Budget.status == status)

        if fiscal_year:
            query = query.filter(Budget.fiscal_year == fiscal_year)

        if entity_id:
            query = query.filter(Budget.entity_id == entity_id)

        if department_id:
            query = query.filter(Budget.department_id == department_id)

        if project_id:
            query = query.filter(Budget.project_id == project_id)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Budget.code.ilike(search_filter),
                    Budget.name.ilike(search_filter)
                )
            )

        # Only current versions by default
        query = query.filter(Budget.is_current_version == True)

        total = query.count()
        offset = (page - 1) * per_page

        items = query.order_by(
            desc(Budget.fiscal_year),
            Budget.code
        ).offset(offset).limit(per_page).all()

        return items, total

    def get_active_budgets(
        self,
        fiscal_year: Optional[int] = None
    ) -> List[Budget]:
        """Recupere les budgets actifs."""
        query = self._base_query_active(Budget).filter(
            Budget.status == BudgetStatus.ACTIVE,
            Budget.is_current_version == True
        )

        if fiscal_year:
            query = query.filter(Budget.fiscal_year == fiscal_year)

        return query.all()

    def create_budget(self, budget: Budget) -> Budget:
        """Cree un budget."""
        budget.tenant_id = self.tenant_id
        self.db.add(budget)
        self.db.flush()
        return budget

    def update_budget(
        self,
        budget_id: UUID,
        updates: Dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> Optional[Budget]:
        """Met a jour un budget."""
        budget = self.get_budget(budget_id)
        if not budget:
            return None

        for key, value in updates.items():
            if hasattr(budget, key) and key not in ('id', 'tenant_id'):
                setattr(budget, key, value)

        budget.updated_at = datetime.utcnow()
        budget.updated_by = updated_by
        budget.version += 1

        self.db.flush()
        return budget

    def soft_delete_budget(
        self,
        budget_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Soft delete un budget et ses lignes."""
        budget = self.get_budget(budget_id)
        if not budget:
            return False

        budget.is_deleted = True
        budget.deleted_at = datetime.utcnow()
        budget.deleted_by = deleted_by

        # Soft delete des lignes
        for line in budget.lines:
            line.is_deleted = True
            line.deleted_at = datetime.utcnow()
            line.deleted_by = deleted_by

        self.db.flush()
        return True

    # =========================================================================
    # BUDGET LINE METHODS
    # =========================================================================

    def get_budget_line(self, line_id: UUID) -> Optional[BudgetLine]:
        """Recupere une ligne de budget."""
        return self._base_query_active(BudgetLine).filter(
            BudgetLine.id == line_id
        ).first()

    def get_budget_lines(self, budget_id: UUID) -> List[BudgetLine]:
        """Recupere toutes les lignes d'un budget."""
        return self._base_query_active(BudgetLine).filter(
            BudgetLine.budget_id == budget_id
        ).order_by(BudgetLine.sort_order).all()

    def get_budget_lines_by_category(
        self,
        budget_id: UUID,
        category_id: UUID
    ) -> List[BudgetLine]:
        """Recupere les lignes d'une categorie."""
        return self._base_query_active(BudgetLine).filter(
            BudgetLine.budget_id == budget_id,
            BudgetLine.category_id == category_id
        ).all()

    def create_budget_line(self, line: BudgetLine) -> BudgetLine:
        """Cree une ligne de budget."""
        line.tenant_id = self.tenant_id
        self.db.add(line)
        self.db.flush()
        return line

    def create_budget_lines(self, lines: List[BudgetLine]) -> List[BudgetLine]:
        """Cree plusieurs lignes de budget."""
        for line in lines:
            line.tenant_id = self.tenant_id
        self.db.add_all(lines)
        self.db.flush()
        return lines

    def update_budget_line(
        self,
        line_id: UUID,
        updates: Dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> Optional[BudgetLine]:
        """Met a jour une ligne de budget."""
        line = self.get_budget_line(line_id)
        if not line:
            return None

        for key, value in updates.items():
            if hasattr(line, key) and key not in ('id', 'tenant_id', 'budget_id'):
                setattr(line, key, value)

        line.updated_at = datetime.utcnow()
        line.updated_by = updated_by
        line.version += 1

        self.db.flush()
        return line

    def soft_delete_budget_line(
        self,
        line_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Soft delete une ligne de budget."""
        line = self.get_budget_line(line_id)
        if not line:
            return False

        line.is_deleted = True
        line.deleted_at = datetime.utcnow()
        line.deleted_by = deleted_by
        self.db.flush()
        return True

    # =========================================================================
    # BUDGET PERIOD METHODS
    # =========================================================================

    def get_budget_periods(self, budget_id: UUID) -> List[BudgetPeriod]:
        """Recupere les periodes d'un budget."""
        return self._base_query(BudgetPeriod).filter(
            BudgetPeriod.budget_id == budget_id
        ).order_by(BudgetPeriod.period_number).all()

    def get_budget_period(
        self,
        budget_id: UUID,
        period_number: int
    ) -> Optional[BudgetPeriod]:
        """Recupere une periode specifique."""
        return self._base_query(BudgetPeriod).filter(
            BudgetPeriod.budget_id == budget_id,
            BudgetPeriod.period_number == period_number
        ).first()

    def create_budget_periods(
        self,
        periods: List[BudgetPeriod]
    ) -> List[BudgetPeriod]:
        """Cree les periodes d'un budget."""
        for period in periods:
            period.tenant_id = self.tenant_id
        self.db.add_all(periods)
        self.db.flush()
        return periods

    def lock_period(
        self,
        period_id: UUID,
        locked_by: UUID
    ) -> Optional[BudgetPeriod]:
        """Verrouille une periode."""
        period = self.db.query(BudgetPeriod).filter(
            BudgetPeriod.id == period_id,
            BudgetPeriod.tenant_id == self.tenant_id
        ).first()

        if not period:
            return None

        period.is_locked = True
        period.locked_at = datetime.utcnow()
        period.locked_by = locked_by
        self.db.flush()
        return period

    # =========================================================================
    # BUDGET PERIOD AMOUNT METHODS
    # =========================================================================

    def get_period_amounts(
        self,
        budget_line_id: UUID
    ) -> List[BudgetPeriodAmount]:
        """Recupere les montants par periode pour une ligne."""
        return self._base_query(BudgetPeriodAmount).filter(
            BudgetPeriodAmount.budget_line_id == budget_line_id
        ).all()

    def create_period_amounts(
        self,
        amounts: List[BudgetPeriodAmount]
    ) -> List[BudgetPeriodAmount]:
        """Cree les montants par periode."""
        for amount in amounts:
            amount.tenant_id = self.tenant_id
        self.db.add_all(amounts)
        self.db.flush()
        return amounts

    def update_period_amount(
        self,
        line_id: UUID,
        period_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[BudgetPeriodAmount]:
        """Met a jour un montant de periode."""
        amount = self._base_query(BudgetPeriodAmount).filter(
            BudgetPeriodAmount.budget_line_id == line_id,
            BudgetPeriodAmount.period_id == period_id
        ).first()

        if not amount:
            return None

        for key, value in updates.items():
            if hasattr(amount, key):
                setattr(amount, key, value)

        amount.updated_at = datetime.utcnow()
        self.db.flush()
        return amount

    # =========================================================================
    # BUDGET REVISION METHODS
    # =========================================================================

    def get_revision(self, revision_id: UUID) -> Optional[BudgetRevision]:
        """Recupere une revision."""
        return self._base_query(BudgetRevision).options(
            joinedload(BudgetRevision.details)
        ).filter(BudgetRevision.id == revision_id).first()

    def list_revisions(
        self,
        budget_id: UUID,
        status: Optional[RevisionStatus] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[BudgetRevision], int]:
        """Liste les revisions d'un budget."""
        query = self._base_query(BudgetRevision).filter(
            BudgetRevision.budget_id == budget_id
        )

        if status:
            query = query.filter(BudgetRevision.status == status)

        total = query.count()
        offset = (page - 1) * per_page

        items = query.order_by(
            desc(BudgetRevision.revision_number)
        ).offset(offset).limit(per_page).all()

        return items, total

    def get_next_revision_number(self, budget_id: UUID) -> int:
        """Obtient le prochain numero de revision."""
        result = self.db.query(
            func.coalesce(func.max(BudgetRevision.revision_number), 0)
        ).filter(
            BudgetRevision.budget_id == budget_id,
            BudgetRevision.tenant_id == self.tenant_id
        ).scalar()
        return result + 1

    def create_revision(self, revision: BudgetRevision) -> BudgetRevision:
        """Cree une revision."""
        revision.tenant_id = self.tenant_id
        self.db.add(revision)
        self.db.flush()
        return revision

    def create_revision_details(
        self,
        details: List[BudgetRevisionDetail]
    ) -> List[BudgetRevisionDetail]:
        """Cree les details d'une revision."""
        for detail in details:
            detail.tenant_id = self.tenant_id
        self.db.add_all(details)
        self.db.flush()
        return details

    def update_revision_status(
        self,
        revision_id: UUID,
        status: RevisionStatus,
        updated_by: UUID,
        comments: Optional[str] = None
    ) -> Optional[BudgetRevision]:
        """Met a jour le statut d'une revision."""
        revision = self.get_revision(revision_id)
        if not revision:
            return None

        revision.status = status
        revision.updated_at = datetime.utcnow()
        revision.updated_by = updated_by

        if status == RevisionStatus.APPROVED:
            revision.approved_at = datetime.utcnow()
            revision.approved_by = updated_by
            revision.approval_comments = comments
        elif status == RevisionStatus.REJECTED:
            revision.rejection_reason = comments
        elif status == RevisionStatus.APPLIED:
            revision.applied_at = datetime.utcnow()
            revision.applied_by = updated_by

        self.db.flush()
        return revision

    # =========================================================================
    # BUDGET ACTUAL METHODS
    # =========================================================================

    def get_actual(self, actual_id: UUID) -> Optional[BudgetActual]:
        """Recupere un realise."""
        return self._base_query(BudgetActual).filter(
            BudgetActual.id == actual_id
        ).first()

    def get_actuals(
        self,
        budget_id: UUID,
        budget_line_id: Optional[UUID] = None,
        period: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[BudgetActual]:
        """Recupere les realises avec filtres."""
        query = self._base_query(BudgetActual).filter(
            BudgetActual.budget_id == budget_id
        )

        if budget_line_id:
            query = query.filter(BudgetActual.budget_line_id == budget_line_id)

        if period:
            query = query.filter(BudgetActual.period == period)

        if from_date:
            query = query.filter(BudgetActual.period_date >= from_date)

        if to_date:
            query = query.filter(BudgetActual.period_date <= to_date)

        return query.order_by(BudgetActual.period_date).all()

    def get_actuals_sum_by_line(
        self,
        budget_id: UUID,
        as_of_period: Optional[str] = None
    ) -> Dict[UUID, Decimal]:
        """Calcule la somme des realises par ligne."""
        query = self.db.query(
            BudgetActual.budget_line_id,
            func.sum(BudgetActual.amount).label('total')
        ).filter(
            BudgetActual.budget_id == budget_id,
            BudgetActual.tenant_id == self.tenant_id
        )

        if as_of_period:
            query = query.filter(BudgetActual.period <= as_of_period)

        query = query.group_by(BudgetActual.budget_line_id)

        return {row.budget_line_id: row.total for row in query.all()}

    def get_actuals_by_period(
        self,
        budget_id: UUID
    ) -> Dict[str, Decimal]:
        """Calcule la somme des realises par periode."""
        query = self.db.query(
            BudgetActual.period,
            func.sum(BudgetActual.amount).label('total')
        ).filter(
            BudgetActual.budget_id == budget_id,
            BudgetActual.tenant_id == self.tenant_id
        ).group_by(BudgetActual.period)

        return {row.period: row.total for row in query.all()}

    def create_actual(self, actual: BudgetActual) -> BudgetActual:
        """Cree un realise."""
        actual.tenant_id = self.tenant_id
        self.db.add(actual)
        self.db.flush()
        return actual

    def create_actuals(self, actuals: List[BudgetActual]) -> List[BudgetActual]:
        """Cree plusieurs realises."""
        for actual in actuals:
            actual.tenant_id = self.tenant_id
        self.db.add_all(actuals)
        self.db.flush()
        return actuals

    def delete_actuals_by_source(
        self,
        budget_id: UUID,
        source: str,
        period: Optional[str] = None
    ) -> int:
        """Supprime les realises par source (pour reimport)."""
        query = self.db.query(BudgetActual).filter(
            BudgetActual.budget_id == budget_id,
            BudgetActual.tenant_id == self.tenant_id,
            BudgetActual.source == source
        )

        if period:
            query = query.filter(BudgetActual.period == period)

        count = query.delete()
        self.db.flush()
        return count

    # =========================================================================
    # BUDGET ALERT METHODS
    # =========================================================================

    def get_alert(self, alert_id: UUID) -> Optional[BudgetAlert]:
        """Recupere une alerte."""
        return self._base_query(BudgetAlert).filter(
            BudgetAlert.id == alert_id
        ).first()

    def get_active_alerts(
        self,
        budget_id: Optional[UUID] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50
    ) -> List[BudgetAlert]:
        """Recupere les alertes actives."""
        query = self._base_query(BudgetAlert).filter(
            BudgetAlert.status == AlertStatus.ACTIVE
        )

        if budget_id:
            query = query.filter(BudgetAlert.budget_id == budget_id)

        if severity:
            query = query.filter(BudgetAlert.severity == severity)

        return query.order_by(
            desc(BudgetAlert.severity),
            desc(BudgetAlert.triggered_at)
        ).limit(limit).all()

    def list_alerts(
        self,
        budget_id: Optional[UUID] = None,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[BudgetAlert], int]:
        """Liste les alertes avec filtres."""
        query = self._base_query(BudgetAlert)

        if budget_id:
            query = query.filter(BudgetAlert.budget_id == budget_id)

        if status:
            query = query.filter(BudgetAlert.status == status)

        if severity:
            query = query.filter(BudgetAlert.severity == severity)

        total = query.count()
        offset = (page - 1) * per_page

        items = query.order_by(
            desc(BudgetAlert.triggered_at)
        ).offset(offset).limit(per_page).all()

        return items, total

    def create_alert(self, alert: BudgetAlert) -> BudgetAlert:
        """Cree une alerte."""
        alert.tenant_id = self.tenant_id
        self.db.add(alert)
        self.db.flush()
        return alert

    def update_alert_status(
        self,
        alert_id: UUID,
        status: AlertStatus,
        updated_by: UUID,
        notes: Optional[str] = None
    ) -> Optional[BudgetAlert]:
        """Met a jour le statut d'une alerte."""
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        alert.status = status

        if status == AlertStatus.ACKNOWLEDGED:
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = updated_by
        elif status == AlertStatus.RESOLVED:
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = updated_by
            alert.resolution_notes = notes

        self.db.flush()
        return alert

    # =========================================================================
    # BUDGET FORECAST METHODS
    # =========================================================================

    def get_forecasts(
        self,
        budget_id: UUID,
        budget_line_id: Optional[UUID] = None,
        period: Optional[str] = None
    ) -> List[BudgetForecast]:
        """Recupere les previsions."""
        query = self._base_query(BudgetForecast).filter(
            BudgetForecast.budget_id == budget_id
        )

        if budget_line_id:
            query = query.filter(BudgetForecast.budget_line_id == budget_line_id)

        if period:
            query = query.filter(BudgetForecast.period == period)

        return query.order_by(
            desc(BudgetForecast.forecast_date),
            BudgetForecast.period
        ).all()

    def get_latest_forecasts(
        self,
        budget_id: UUID
    ) -> List[BudgetForecast]:
        """Recupere les dernieres previsions par periode."""
        subquery = self.db.query(
            BudgetForecast.period,
            func.max(BudgetForecast.forecast_date).label('max_date')
        ).filter(
            BudgetForecast.budget_id == budget_id,
            BudgetForecast.tenant_id == self.tenant_id
        ).group_by(BudgetForecast.period).subquery()

        return self.db.query(BudgetForecast).join(
            subquery,
            and_(
                BudgetForecast.period == subquery.c.period,
                BudgetForecast.forecast_date == subquery.c.max_date
            )
        ).filter(
            BudgetForecast.budget_id == budget_id,
            BudgetForecast.tenant_id == self.tenant_id
        ).all()

    def create_forecast(self, forecast: BudgetForecast) -> BudgetForecast:
        """Cree une prevision."""
        forecast.tenant_id = self.tenant_id
        self.db.add(forecast)
        self.db.flush()
        return forecast

    # =========================================================================
    # BUDGET SCENARIO METHODS
    # =========================================================================

    def get_scenario(self, scenario_id: UUID) -> Optional[BudgetScenario]:
        """Recupere un scenario."""
        return self._base_query_active(BudgetScenario).options(
            joinedload(BudgetScenario.lines)
        ).filter(BudgetScenario.id == scenario_id).first()

    def list_scenarios(
        self,
        budget_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[BudgetScenario]:
        """Liste les scenarios d'un budget."""
        query = self._base_query_active(BudgetScenario).filter(
            BudgetScenario.budget_id == budget_id
        )

        if is_active is not None:
            query = query.filter(BudgetScenario.is_active == is_active)

        return query.order_by(BudgetScenario.name).all()

    def create_scenario(self, scenario: BudgetScenario) -> BudgetScenario:
        """Cree un scenario."""
        scenario.tenant_id = self.tenant_id
        self.db.add(scenario)
        self.db.flush()
        return scenario

    def create_scenario_lines(
        self,
        lines: List[BudgetScenarioLine]
    ) -> List[BudgetScenarioLine]:
        """Cree les lignes d'un scenario."""
        for line in lines:
            line.tenant_id = self.tenant_id
        self.db.add_all(lines)
        self.db.flush()
        return lines

    def soft_delete_scenario(
        self,
        scenario_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Soft delete un scenario."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return False

        scenario.is_deleted = True
        scenario.deleted_at = datetime.utcnow()
        scenario.deleted_by = deleted_by
        self.db.flush()
        return True

    # =========================================================================
    # BUDGET CONSOLIDATION METHODS
    # =========================================================================

    def get_consolidation(
        self,
        consolidation_id: UUID
    ) -> Optional[BudgetConsolidation]:
        """Recupere une consolidation."""
        return self._base_query_active(BudgetConsolidation).filter(
            BudgetConsolidation.id == consolidation_id
        ).first()

    def list_consolidations(
        self,
        fiscal_year: Optional[int] = None
    ) -> List[BudgetConsolidation]:
        """Liste les consolidations."""
        query = self._base_query_active(BudgetConsolidation)

        if fiscal_year:
            query = query.filter(BudgetConsolidation.fiscal_year == fiscal_year)

        return query.order_by(BudgetConsolidation.name).all()

    def create_consolidation(
        self,
        consolidation: BudgetConsolidation
    ) -> BudgetConsolidation:
        """Cree une consolidation."""
        consolidation.tenant_id = self.tenant_id
        self.db.add(consolidation)
        self.db.flush()
        return consolidation

    # =========================================================================
    # BUDGET TEMPLATE METHODS
    # =========================================================================

    def get_template(self, template_id: UUID) -> Optional[BudgetTemplate]:
        """Recupere un template."""
        return self._base_query_active(BudgetTemplate).filter(
            BudgetTemplate.id == template_id
        ).first()

    def list_templates(
        self,
        budget_type: Optional[BudgetType] = None,
        is_active: Optional[bool] = None
    ) -> List[BudgetTemplate]:
        """Liste les templates."""
        query = self._base_query_active(BudgetTemplate)

        if budget_type:
            query = query.filter(BudgetTemplate.budget_type == budget_type)

        if is_active is not None:
            query = query.filter(BudgetTemplate.is_active == is_active)

        return query.order_by(BudgetTemplate.name).all()

    def create_template(self, template: BudgetTemplate) -> BudgetTemplate:
        """Cree un template."""
        template.tenant_id = self.tenant_id
        self.db.add(template)
        self.db.flush()
        return template

    # =========================================================================
    # SEASONAL PROFILE METHODS
    # =========================================================================

    def get_seasonal_profile(
        self,
        profile_id: UUID
    ) -> Optional[SeasonalProfile]:
        """Recupere un profil saisonnier."""
        return self._base_query(SeasonalProfile).filter(
            SeasonalProfile.id == profile_id
        ).first()

    def get_seasonal_profile_by_code(
        self,
        code: str
    ) -> Optional[SeasonalProfile]:
        """Recupere un profil par code."""
        return self._base_query(SeasonalProfile).filter(
            SeasonalProfile.code == code
        ).first()

    def list_seasonal_profiles(self) -> List[SeasonalProfile]:
        """Liste les profils saisonniers."""
        return self._base_query(SeasonalProfile).filter(
            SeasonalProfile.is_active == True
        ).order_by(SeasonalProfile.name).all()

    def create_seasonal_profile(
        self,
        profile: SeasonalProfile
    ) -> SeasonalProfile:
        """Cree un profil saisonnier."""
        profile.tenant_id = self.tenant_id
        self.db.add(profile)
        self.db.flush()
        return profile

    # =========================================================================
    # APPROVAL RULES METHODS
    # =========================================================================

    def get_approval_rules(
        self,
        budget_type: Optional[BudgetType] = None,
        amount: Optional[Decimal] = None
    ) -> List[BudgetApprovalRule]:
        """Recupere les regles d'approbation applicables."""
        query = self._base_query(BudgetApprovalRule).filter(
            BudgetApprovalRule.is_active == True
        )

        if budget_type:
            query = query.filter(
                or_(
                    BudgetApprovalRule.budget_type == budget_type,
                    BudgetApprovalRule.budget_type == None
                )
            )

        if amount is not None:
            query = query.filter(
                BudgetApprovalRule.min_amount <= amount,
                or_(
                    BudgetApprovalRule.max_amount >= amount,
                    BudgetApprovalRule.max_amount == None
                )
            )

        return query.order_by(BudgetApprovalRule.priority).all()

    # =========================================================================
    # COMMIT / ROLLBACK
    # =========================================================================

    def commit(self):
        """Commit la transaction."""
        self.db.commit()

    def rollback(self):
        """Rollback la transaction."""
        self.db.rollback()

    def flush(self):
        """Flush les changements."""
        self.db.flush()
