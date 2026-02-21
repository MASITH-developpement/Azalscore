"""
AZALS MODULE - BUDGET: Service
===============================

Service metier pour la gestion budgetaire complete.

Fonctionnalites:
- CRUD budgets, lignes, categories
- Workflow d'approbation
- Suivi des realises
- Calcul des ecarts
- Alertes de depassement
- Revisions budgetaires
- Previsions (rolling forecast)
- Scenarios et simulations
- Consolidation
- Controle budgetaire

Auteur: AZALSCORE Team
Version: 2.0.0
"""

import calendar
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .exceptions import (
    BudgetAlreadyExistsError,
    BudgetApprovalError,
    BudgetCalculationError,
    BudgetCategoryNotFoundError,
    BudgetControlViolationError,
    BudgetControlWarning,
    BudgetLineNotFoundError,
    BudgetNotFoundError,
    BudgetNotModifiableError,
    BudgetPeriodLockedError,
    BudgetRevisionError,
    BudgetRevisionNotFoundError,
    BudgetStatusError,
    BudgetValidationError,
    BudgetWorkflowError,
    InsufficientBudgetError,
    OptimisticLockError,
)
from .models import (
    AlertSeverity,
    AlertStatus,
    AllocationMethod,
    Budget,
    BudgetActual,
    BudgetAlert,
    BudgetCategory,
    BudgetConsolidation,
    BudgetForecast,
    BudgetLine,
    BudgetLineType,
    BudgetPeriod,
    BudgetPeriodAmount,
    BudgetPeriodType,
    BudgetRevision,
    BudgetRevisionDetail,
    BudgetScenario,
    BudgetScenarioLine,
    BudgetStatus,
    BudgetTemplate,
    BudgetType,
    ControlMode,
    ForecastConfidence,
    RevisionStatus,
    ScenarioType,
    SeasonalProfile,
    VarianceType,
)
from .repository import BudgetRepository
from .schemas import (
    BudgetActualCreate,
    BudgetActualResponse,
    BudgetCategoryCreate,
    BudgetCategoryResponse,
    BudgetCategoryUpdate,
    BudgetControlCheck,
    BudgetControlResult,
    BudgetCreate,
    BudgetDashboard,
    BudgetDetailResponse,
    BudgetExecutionRate,
    BudgetForecastCreate,
    BudgetForecastResponse,
    BudgetLineCreate,
    BudgetLineResponse,
    BudgetLineUpdate,
    BudgetResponse,
    BudgetRevisionCreate,
    BudgetRevisionResponse,
    BudgetScenarioCreate,
    BudgetScenarioResponse,
    BudgetSummary,
    BudgetUpdate,
    BudgetVariance,
    SeasonalProfileCreate,
)


# Profils saisonniers par defaut
DEFAULT_SEASONAL_PROFILES = {
    "retail": [8, 6, 7, 8, 9, 8, 7, 6, 9, 10, 11, 11],
    "tourism": [5, 5, 6, 8, 9, 12, 15, 15, 8, 7, 5, 5],
    "b2b": [7, 8, 9, 9, 8, 7, 6, 5, 9, 10, 10, 12],
    "education": [10, 10, 8, 6, 5, 3, 3, 3, 12, 12, 10, 8],
    "flat": [8.33] * 12,
}


class BudgetService:
    """
    Service de gestion budgetaire.

    Fournit toutes les operations metier pour la gestion des budgets.
    """

    def __init__(self, db: Session, tenant_id: str):
        """
        Initialise le service.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour l'isolation multi-tenant
        """
        self.db = db
        self.tenant_id = tenant_id
        self.repo = BudgetRepository(db, tenant_id)

    # =========================================================================
    # BUDGET CATEGORY METHODS
    # =========================================================================

    def create_category(
        self,
        data: BudgetCategoryCreate,
        created_by: Optional[UUID] = None
    ) -> BudgetCategoryResponse:
        """Cree une nouvelle categorie budgetaire."""
        # Verifier unicite du code
        existing = self.repo.get_category_by_code(data.code)
        if existing:
            raise BudgetAlreadyExistsError(
                data.code,
                f"Une categorie avec le code '{data.code}' existe deja"
            )

        # Verifier le parent si specifie
        parent_level = 0
        parent_path = ""
        if data.parent_id:
            parent = self.repo.get_category(data.parent_id)
            if not parent:
                raise BudgetCategoryNotFoundError(data.parent_id)
            parent_level = parent.level
            parent_path = parent.path or str(parent.id)

        category = BudgetCategory(
            id=uuid.uuid4(),
            code=data.code,
            name=data.name,
            description=data.description,
            line_type=data.line_type,
            parent_id=data.parent_id,
            level=parent_level + 1 if data.parent_id else 0,
            account_codes=data.account_codes,
            sort_order=data.sort_order,
            is_active=data.is_active,
            created_by=created_by
        )

        category = self.repo.create_category(category)
        category.path = f"{parent_path}/{category.id}" if parent_path else str(category.id)
        self.repo.commit()

        return BudgetCategoryResponse.model_validate(category)

    def get_category(self, category_id: UUID) -> BudgetCategoryResponse:
        """Recupere une categorie."""
        category = self.repo.get_category(category_id)
        if not category:
            raise BudgetCategoryNotFoundError(category_id)
        return BudgetCategoryResponse.model_validate(category)

    def list_categories(
        self,
        parent_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Tuple[List[BudgetCategoryResponse], int]:
        """Liste les categories."""
        items, total = self.repo.list_categories(parent_id, is_active, page, per_page)
        return [BudgetCategoryResponse.model_validate(c) for c in items], total

    def update_category(
        self,
        category_id: UUID,
        data: BudgetCategoryUpdate,
        updated_by: Optional[UUID] = None
    ) -> BudgetCategoryResponse:
        """Met a jour une categorie."""
        updates = data.model_dump(exclude_unset=True)
        category = self.repo.update_category(category_id, updates, updated_by)
        if not category:
            raise BudgetCategoryNotFoundError(category_id)
        self.repo.commit()
        return BudgetCategoryResponse.model_validate(category)

    def delete_category(
        self,
        category_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Supprime une categorie (soft delete)."""
        success = self.repo.soft_delete_category(category_id, deleted_by)
        if not success:
            raise BudgetCategoryNotFoundError(category_id)
        self.repo.commit()
        return True

    # =========================================================================
    # BUDGET CRUD METHODS
    # =========================================================================

    def create_budget(
        self,
        data: BudgetCreate,
        created_by: Optional[UUID] = None
    ) -> BudgetResponse:
        """Cree un nouveau budget."""
        # Verifier unicite du code
        existing = self.repo.get_budget_by_code(data.code)
        if existing:
            raise BudgetAlreadyExistsError(data.code)

        # Creer le budget
        budget = Budget(
            id=uuid.uuid4(),
            code=data.code,
            name=data.name,
            description=data.description,
            budget_type=data.budget_type,
            period_type=data.period_type,
            fiscal_year=data.fiscal_year,
            start_date=data.start_date,
            end_date=data.end_date,
            currency=data.currency,
            entity_id=data.entity_id,
            department_id=data.department_id,
            cost_center_id=data.cost_center_id,
            project_id=data.project_id,
            control_mode=data.control_mode,
            warning_threshold=data.warning_threshold,
            critical_threshold=data.critical_threshold,
            notes=data.notes,
            assumptions=data.assumptions,
            objectives=data.objectives,
            tags=data.tags,
            owner_id=data.owner_id,
            approvers=data.approvers or [],
            status=BudgetStatus.DRAFT,
            created_by=created_by
        )

        budget = self.repo.create_budget(budget)

        # Creer les periodes
        periods = self._generate_periods(budget)
        self.repo.create_budget_periods(periods)

        # Si template specifie, copier la structure
        if data.template_id:
            self._apply_template(budget, data.template_id)

        # Si copie depuis un autre budget
        if data.copy_from_id:
            self._copy_budget_structure(budget, data.copy_from_id)

        self.repo.commit()
        return BudgetResponse.model_validate(budget)

    def get_budget(self, budget_id: UUID) -> BudgetResponse:
        """Recupere un budget."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)
        return BudgetResponse.model_validate(budget)

    def get_budget_detail(self, budget_id: UUID) -> BudgetDetailResponse:
        """Recupere un budget avec ses details."""
        budget = self.repo.get_budget_with_lines(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        # Convertir les lignes
        lines = [
            BudgetLineResponse.model_validate(line)
            for line in budget.lines
            if not line.is_deleted
        ]

        # Convertir les periodes
        from .schemas import BudgetPeriodResponse
        periods = [
            BudgetPeriodResponse.model_validate(p)
            for p in budget.periods
        ]

        return BudgetDetailResponse(
            **BudgetResponse.model_validate(budget).model_dump(),
            lines=lines,
            periods=periods,
            approval_history=budget.approval_history or []
        )

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
    ) -> Tuple[List[BudgetResponse], int]:
        """Liste les budgets avec filtres."""
        items, total = self.repo.list_budgets(
            budget_type, status, fiscal_year,
            entity_id, department_id, project_id,
            search, page, per_page
        )
        return [BudgetResponse.model_validate(b) for b in items], total

    def update_budget(
        self,
        budget_id: UUID,
        data: BudgetUpdate,
        updated_by: Optional[UUID] = None
    ) -> BudgetResponse:
        """Met a jour un budget."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        # Verifier que le budget est modifiable
        if budget.status not in [BudgetStatus.DRAFT, BudgetStatus.REJECTED, BudgetStatus.REVISED]:
            raise BudgetNotModifiableError(budget_id, budget.status.value)

        updates = data.model_dump(exclude_unset=True)
        budget = self.repo.update_budget(budget_id, updates, updated_by)
        self.repo.commit()

        return BudgetResponse.model_validate(budget)

    def delete_budget(
        self,
        budget_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Supprime un budget (soft delete)."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        # Ne pas supprimer un budget actif
        if budget.status == BudgetStatus.ACTIVE:
            raise BudgetStatusError(
                budget_id, budget.status.value, "DRAFT,CLOSED",
                "delete"
            )

        success = self.repo.soft_delete_budget(budget_id, deleted_by)
        self.repo.commit()
        return success

    # =========================================================================
    # BUDGET LINE METHODS
    # =========================================================================

    def add_budget_line(
        self,
        budget_id: UUID,
        data: BudgetLineCreate,
        created_by: Optional[UUID] = None
    ) -> BudgetLineResponse:
        """Ajoute une ligne au budget."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status not in [BudgetStatus.DRAFT, BudgetStatus.REJECTED, BudgetStatus.REVISED]:
            raise BudgetNotModifiableError(budget_id, budget.status.value)

        # Verifier la categorie
        category = self.repo.get_category(data.category_id)
        if not category:
            raise BudgetCategoryNotFoundError(data.category_id)

        # Creer la ligne
        line = BudgetLine(
            id=uuid.uuid4(),
            budget_id=budget_id,
            category_id=data.category_id,
            code=data.code,
            name=data.name,
            description=data.description,
            line_type=data.line_type or category.line_type,
            annual_amount=data.annual_amount,
            allocation_method=data.allocation_method,
            seasonal_profile=data.seasonal_profile,
            quantity=data.quantity,
            unit=data.unit,
            unit_price=data.unit_price,
            cost_center_id=data.cost_center_id,
            project_id=data.project_id,
            department_id=data.department_id,
            account_code=data.account_code,
            notes=data.notes,
            assumptions=data.assumptions,
            created_by=created_by
        )

        line = self.repo.create_budget_line(line)

        # Distribuer sur les periodes
        monthly_dist = data.monthly_distribution
        if not monthly_dist:
            monthly_dist = self._distribute_annual_amount(
                data.annual_amount,
                data.allocation_method,
                data.seasonal_profile
            )
        line.monthly_distribution = monthly_dist

        # Creer les montants par periode
        periods = self.repo.get_budget_periods(budget_id)
        period_amounts = []
        for period in periods:
            month = period.period_number
            amount = monthly_dist.get(month, Decimal("0"))
            period_amounts.append(BudgetPeriodAmount(
                budget_line_id=line.id,
                period_id=period.id,
                budget_amount=amount
            ))
        self.repo.create_period_amounts(period_amounts)

        # Recalculer les totaux du budget
        self._recalculate_budget_totals(budget)
        self.repo.commit()

        return BudgetLineResponse.model_validate(line)

    def update_budget_line(
        self,
        line_id: UUID,
        data: BudgetLineUpdate,
        updated_by: Optional[UUID] = None
    ) -> BudgetLineResponse:
        """Met a jour une ligne de budget."""
        line = self.repo.get_budget_line(line_id)
        if not line:
            raise BudgetLineNotFoundError(line_id)

        budget = self.repo.get_budget(line.budget_id)
        if budget.status not in [BudgetStatus.DRAFT, BudgetStatus.REJECTED, BudgetStatus.REVISED]:
            raise BudgetNotModifiableError(line.budget_id, budget.status.value)

        updates = data.model_dump(exclude_unset=True)

        # Si le montant annuel change, redistribuer
        if 'annual_amount' in updates or 'monthly_distribution' in updates:
            annual = updates.get('annual_amount', line.annual_amount)
            monthly = updates.get('monthly_distribution')

            if not monthly:
                method = updates.get('allocation_method', line.allocation_method)
                profile = updates.get('seasonal_profile', line.seasonal_profile)
                monthly = self._distribute_annual_amount(annual, method, profile)

            updates['monthly_distribution'] = monthly

            # Mettre a jour les montants par periode
            periods = self.repo.get_budget_periods(line.budget_id)
            for period in periods:
                amount = monthly.get(period.period_number, Decimal("0"))
                self.repo.update_period_amount(
                    line_id, period.id,
                    {'budget_amount': amount}
                )

        line = self.repo.update_budget_line(line_id, updates, updated_by)
        self._recalculate_budget_totals(budget)
        self.repo.commit()

        return BudgetLineResponse.model_validate(line)

    def delete_budget_line(
        self,
        line_id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Supprime une ligne de budget."""
        line = self.repo.get_budget_line(line_id)
        if not line:
            raise BudgetLineNotFoundError(line_id)

        budget = self.repo.get_budget(line.budget_id)
        if budget.status not in [BudgetStatus.DRAFT, BudgetStatus.REJECTED, BudgetStatus.REVISED]:
            raise BudgetNotModifiableError(line.budget_id, budget.status.value)

        success = self.repo.soft_delete_budget_line(line_id, deleted_by)
        self._recalculate_budget_totals(budget)
        self.repo.commit()
        return success

    def get_budget_lines(
        self,
        budget_id: UUID
    ) -> List[BudgetLineResponse]:
        """Recupere les lignes d'un budget."""
        lines = self.repo.get_budget_lines(budget_id)
        return [BudgetLineResponse.model_validate(l) for l in lines]

    # =========================================================================
    # WORKFLOW METHODS
    # =========================================================================

    def submit_budget(
        self,
        budget_id: UUID,
        submitted_by: UUID,
        comments: Optional[str] = None
    ) -> BudgetResponse:
        """Soumet le budget pour approbation."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status != BudgetStatus.DRAFT:
            raise BudgetStatusError(budget_id, budget.status.value, "DRAFT", "submit")

        # Verifier qu'il y a des lignes
        lines = self.repo.get_budget_lines(budget_id)
        if not lines:
            raise BudgetValidationError("lines", "Le budget doit avoir au moins une ligne")

        # Mettre a jour le statut
        budget.status = BudgetStatus.SUBMITTED
        budget.submitted_at = datetime.utcnow()
        budget.submitted_by = submitted_by

        # Ajouter a l'historique
        history = budget.approval_history or []
        history.append({
            "action": "submitted",
            "by": str(submitted_by),
            "at": datetime.utcnow().isoformat(),
            "comments": comments
        })
        budget.approval_history = history

        self.repo.commit()
        return BudgetResponse.model_validate(budget)

    def approve_budget(
        self,
        budget_id: UUID,
        approved_by: UUID,
        comments: Optional[str] = None
    ) -> BudgetResponse:
        """Approuve le budget."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status not in [BudgetStatus.SUBMITTED, BudgetStatus.UNDER_REVIEW]:
            raise BudgetStatusError(
                budget_id, budget.status.value,
                "SUBMITTED,UNDER_REVIEW", "approve"
            )

        budget.status = BudgetStatus.APPROVED
        budget.approved_at = datetime.utcnow()
        budget.approved_by = approved_by

        history = budget.approval_history or []
        history.append({
            "action": "approved",
            "by": str(approved_by),
            "at": datetime.utcnow().isoformat(),
            "comments": comments
        })
        budget.approval_history = history

        self.repo.commit()
        return BudgetResponse.model_validate(budget)

    def reject_budget(
        self,
        budget_id: UUID,
        rejected_by: UUID,
        reason: str
    ) -> BudgetResponse:
        """Rejette le budget."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status not in [BudgetStatus.SUBMITTED, BudgetStatus.UNDER_REVIEW]:
            raise BudgetStatusError(
                budget_id, budget.status.value,
                "SUBMITTED,UNDER_REVIEW", "reject"
            )

        budget.status = BudgetStatus.REJECTED

        history = budget.approval_history or []
        history.append({
            "action": "rejected",
            "by": str(rejected_by),
            "at": datetime.utcnow().isoformat(),
            "reason": reason
        })
        budget.approval_history = history

        self.repo.commit()
        return BudgetResponse.model_validate(budget)

    def activate_budget(
        self,
        budget_id: UUID,
        activated_by: UUID,
        effective_date: Optional[date] = None
    ) -> BudgetResponse:
        """Active le budget pour execution."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status != BudgetStatus.APPROVED:
            raise BudgetStatusError(budget_id, budget.status.value, "APPROVED", "activate")

        budget.status = BudgetStatus.ACTIVE
        budget.activated_at = datetime.utcnow()

        history = budget.approval_history or []
        history.append({
            "action": "activated",
            "by": str(activated_by),
            "at": datetime.utcnow().isoformat(),
            "effective_date": (effective_date or date.today()).isoformat()
        })
        budget.approval_history = history

        self.repo.commit()
        return BudgetResponse.model_validate(budget)

    def close_budget(
        self,
        budget_id: UUID,
        closed_by: UUID
    ) -> BudgetResponse:
        """Cloture le budget."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status != BudgetStatus.ACTIVE:
            raise BudgetStatusError(budget_id, budget.status.value, "ACTIVE", "close")

        budget.status = BudgetStatus.CLOSED
        budget.closed_at = datetime.utcnow()

        history = budget.approval_history or []
        history.append({
            "action": "closed",
            "by": str(closed_by),
            "at": datetime.utcnow().isoformat()
        })
        budget.approval_history = history

        self.repo.commit()
        return BudgetResponse.model_validate(budget)

    # =========================================================================
    # ACTUALS METHODS
    # =========================================================================

    def record_actual(
        self,
        budget_id: UUID,
        data: BudgetActualCreate,
        created_by: Optional[UUID] = None
    ) -> BudgetActualResponse:
        """Enregistre un montant realise."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status != BudgetStatus.ACTIVE:
            raise BudgetStatusError(budget_id, budget.status.value, "ACTIVE", "record_actual")

        # Parser la periode
        year, month = map(int, data.period.split("-"))
        period_date = date(year, month, 1)

        actual = BudgetActual(
            id=uuid.uuid4(),
            budget_id=budget_id,
            budget_line_id=data.budget_line_id,
            period=data.period,
            period_date=period_date,
            amount=data.amount,
            line_type=data.line_type,
            source=data.source,
            source_document_type=data.source_document_type,
            source_document_id=data.source_document_id,
            reference=data.reference,
            description=data.description,
            account_code=data.account_code,
            cost_center_id=data.cost_center_id,
            project_id=data.project_id,
            created_by=created_by
        )

        actual = self.repo.create_actual(actual)

        # Mettre a jour les indicateurs de la ligne
        if data.budget_line_id:
            self._update_line_indicators(data.budget_line_id)

        # Verifier les seuils d'alerte
        self._check_budget_alerts(budget, data.budget_line_id, data.period)

        self.repo.commit()
        return BudgetActualResponse.model_validate(actual)

    def import_actuals_from_accounting(
        self,
        budget_id: UUID,
        period: str,
        accounting_data: List[Dict[str, Any]],
        created_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Importe les realises depuis la comptabilite."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        # Supprimer les anciens imports pour cette periode
        self.repo.delete_actuals_by_source(budget_id, "ACCOUNTING", period)

        # Parser la periode
        year, month = map(int, period.split("-"))
        period_date = date(year, month, 1)

        # Creer les actuals
        actuals = []
        total_amount = Decimal("0")
        by_category = {}

        for entry in accounting_data:
            account_code = entry.get("account_code", "")
            amount = Decimal(str(entry.get("amount", 0)))

            # Trouver la ligne correspondante par code compte
            lines = self.repo.get_budget_lines(budget_id)
            matching_line = None
            for line in lines:
                if line.account_code and account_code.startswith(line.account_code[:2]):
                    matching_line = line
                    break

            actual = BudgetActual(
                id=uuid.uuid4(),
                budget_id=budget_id,
                budget_line_id=matching_line.id if matching_line else None,
                period=period,
                period_date=period_date,
                amount=amount,
                line_type=entry.get("line_type", BudgetLineType.EXPENSE),
                source="ACCOUNTING",
                source_document_type=entry.get("document_type"),
                source_document_id=entry.get("document_id"),
                reference=entry.get("reference"),
                description=entry.get("description"),
                account_code=account_code,
                created_by=created_by
            )
            actuals.append(actual)
            total_amount += amount

            # Comptabiliser par categorie
            cat_name = matching_line.name if matching_line else "Non affecte"
            by_category[cat_name] = by_category.get(cat_name, Decimal("0")) + amount

        self.repo.create_actuals(actuals)

        # Mettre a jour les indicateurs des lignes
        for line in self.repo.get_budget_lines(budget_id):
            self._update_line_indicators(line.id)

        # Verifier les alertes
        self._check_budget_alerts(budget, None, period)

        self.repo.commit()

        return {
            "success": True,
            "period": period,
            "records_imported": len(actuals),
            "total_amount": total_amount,
            "by_category": {k: float(v) for k, v in by_category.items()},
            "errors": []
        }

    # =========================================================================
    # VARIANCE METHODS
    # =========================================================================

    def calculate_variances(
        self,
        budget_id: UUID,
        period: str
    ) -> List[BudgetVariance]:
        """Calcule les ecarts pour une periode."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        year, month = map(int, period.split("-"))
        lines = self.repo.get_budget_lines(budget_id)
        actuals_by_line = self.repo.get_actuals_sum_by_line(budget_id, period)

        variances = []

        for line in lines:
            # Budget de la periode
            monthly_dist = line.monthly_distribution or {}
            budget_amount = Decimal(str(monthly_dist.get(str(month), 0)))

            # Realise
            actual_amount = actuals_by_line.get(line.id, Decimal("0"))

            # Calcul de l'ecart
            if line.line_type == BudgetLineType.REVENUE:
                variance_amount = actual_amount - budget_amount
            else:
                variance_amount = budget_amount - actual_amount

            # Pourcentage
            if budget_amount != 0:
                variance_percent = (variance_amount / budget_amount * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                variance_percent = Decimal("0")

            # Type d'ecart
            tolerance = Decimal("5")
            if abs(variance_percent) <= tolerance:
                variance_type = VarianceType.ON_TARGET
            elif variance_amount >= 0:
                variance_type = VarianceType.FAVORABLE
            else:
                variance_type = VarianceType.UNFAVORABLE

            # Cumul YTD
            budget_ytd = sum(
                Decimal(str(monthly_dist.get(str(m), 0)))
                for m in range(1, month + 1)
            )
            actual_ytd = Decimal("0")
            for m in range(1, month + 1):
                m_period = f"{year}-{m:02d}"
                m_actuals = self.repo.get_actuals(budget_id, line.id, m_period)
                actual_ytd += sum(a.amount for a in m_actuals)

            if line.line_type == BudgetLineType.REVENUE:
                variance_ytd = actual_ytd - budget_ytd
            else:
                variance_ytd = budget_ytd - actual_ytd

            variance_ytd_percent = (
                (variance_ytd / budget_ytd * 100).quantize(Decimal("0.01"))
                if budget_ytd else Decimal("0")
            )

            variances.append(BudgetVariance(
                category_id=line.category_id,
                category_name=line.category.name if line.category else "",
                budget_line_id=line.id,
                line_name=line.name,
                period=period,
                line_type=line.line_type,
                budget_amount=budget_amount,
                actual_amount=actual_amount,
                committed_amount=Decimal("0"),
                available_amount=budget_amount - actual_amount,
                variance_amount=variance_amount,
                variance_percent=variance_percent,
                variance_type=variance_type,
                budget_ytd=budget_ytd,
                actual_ytd=actual_ytd,
                variance_ytd=variance_ytd,
                variance_ytd_percent=variance_ytd_percent
            ))

        return variances

    def get_execution_rate(
        self,
        budget_id: UUID,
        as_of_period: str
    ) -> BudgetExecutionRate:
        """Calcule le taux d'execution du budget."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        year, month = map(int, as_of_period.split("-"))
        lines = self.repo.get_budget_lines(budget_id)

        # Calculs par type
        budget_ytd_expense = Decimal("0")
        budget_ytd_revenue = Decimal("0")
        budget_ytd_investment = Decimal("0")
        actual_ytd_expense = Decimal("0")
        actual_ytd_revenue = Decimal("0")
        actual_ytd_investment = Decimal("0")

        for line in lines:
            monthly_dist = line.monthly_distribution or {}
            budget_ytd = sum(
                Decimal(str(monthly_dist.get(str(m), 0)))
                for m in range(1, month + 1)
            )

            actual_ytd = Decimal("0")
            for m in range(1, month + 1):
                m_period = f"{year}-{m:02d}"
                m_actuals = self.repo.get_actuals(budget_id, line.id, m_period)
                actual_ytd += sum(a.amount for a in m_actuals)

            if line.line_type == BudgetLineType.REVENUE:
                budget_ytd_revenue += budget_ytd
                actual_ytd_revenue += actual_ytd
            elif line.line_type == BudgetLineType.EXPENSE:
                budget_ytd_expense += budget_ytd
                actual_ytd_expense += actual_ytd
            elif line.line_type == BudgetLineType.INVESTMENT:
                budget_ytd_investment += budget_ytd
                actual_ytd_investment += actual_ytd

        expense_rate = (
            actual_ytd_expense / budget_ytd_expense * 100
            if budget_ytd_expense else Decimal("0")
        ).quantize(Decimal("0.1"))

        revenue_rate = (
            actual_ytd_revenue / budget_ytd_revenue * 100
            if budget_ytd_revenue else Decimal("0")
        ).quantize(Decimal("0.1"))

        total_budget = budget_ytd_expense + budget_ytd_investment
        total_actual = actual_ytd_expense + actual_ytd_investment
        consumption_rate = (
            total_actual / total_budget * 100
            if total_budget else Decimal("0")
        ).quantize(Decimal("0.1"))

        return BudgetExecutionRate(
            budget_id=budget_id,
            as_of_period=as_of_period,
            expense={
                "budget_ytd": float(budget_ytd_expense),
                "actual_ytd": float(actual_ytd_expense),
                "execution_rate": float(expense_rate),
                "remaining": float(budget_ytd_expense - actual_ytd_expense)
            },
            revenue={
                "budget_ytd": float(budget_ytd_revenue),
                "actual_ytd": float(actual_ytd_revenue),
                "execution_rate": float(revenue_rate),
                "variance": float(actual_ytd_revenue - budget_ytd_revenue)
            },
            investment={
                "budget_ytd": float(budget_ytd_investment),
                "actual_ytd": float(actual_ytd_investment),
                "execution_rate": float(
                    (actual_ytd_investment / budget_ytd_investment * 100)
                    if budget_ytd_investment else 0
                ),
                "remaining": float(budget_ytd_investment - actual_ytd_investment)
            },
            net_result={
                "budget": float(budget_ytd_revenue - budget_ytd_expense),
                "actual": float(actual_ytd_revenue - actual_ytd_expense)
            },
            consumption_rate=consumption_rate,
            remaining_budget=total_budget - total_actual
        )

    # =========================================================================
    # BUDGET CONTROL METHODS
    # =========================================================================

    def check_budget_control(
        self,
        data: BudgetControlCheck
    ) -> BudgetControlResult:
        """Verifie le controle budgetaire avant une depense."""
        budget = self.repo.get_budget(data.budget_id)
        if not budget:
            raise BudgetNotFoundError(data.budget_id)

        # Si pas de controle
        if budget.control_mode == ControlMode.NONE:
            return BudgetControlResult(
                allowed=True,
                control_mode=budget.control_mode,
                budget_amount=Decimal("0"),
                consumed_amount=Decimal("0"),
                requested_amount=data.amount,
                available_amount=Decimal("0"),
                consumption_after=Decimal("0"),
                consumption_percent=Decimal("0"),
                message="Controle budgetaire desactive"
            )

        # Calculer les montants
        if data.budget_line_id:
            line = self.repo.get_budget_line(data.budget_line_id)
            if not line:
                raise BudgetLineNotFoundError(data.budget_line_id)

            budget_amount = line.annual_amount
            actuals = self.repo.get_actuals(data.budget_id, data.budget_line_id)
            consumed_amount = sum(a.amount for a in actuals)
        else:
            budget_amount = budget.total_expense
            actuals_by_line = self.repo.get_actuals_sum_by_line(data.budget_id)
            consumed_amount = sum(actuals_by_line.values())

        available = budget_amount - consumed_amount
        after_amount = consumed_amount + data.amount
        consumption_percent = (
            after_amount / budget_amount * 100
            if budget_amount else Decimal("0")
        )

        # Determiner le seuil depasse
        threshold_exceeded = None
        if consumption_percent >= budget.block_threshold:
            threshold_exceeded = "exceeded"
        elif consumption_percent >= budget.critical_threshold:
            threshold_exceeded = "critical"
        elif consumption_percent >= budget.warning_threshold:
            threshold_exceeded = "warning"

        # Determiner si autorise
        allowed = True
        requires_override = False

        if threshold_exceeded == "exceeded":
            if budget.control_mode == ControlMode.HARD:
                allowed = False
            elif budget.control_mode == ControlMode.SOFT:
                requires_override = budget.allow_override
                allowed = budget.allow_override

        message = self._get_control_message(
            allowed, threshold_exceeded, consumption_percent
        )

        return BudgetControlResult(
            allowed=allowed,
            control_mode=budget.control_mode,
            budget_amount=budget_amount,
            consumed_amount=consumed_amount,
            requested_amount=data.amount,
            available_amount=available,
            consumption_after=after_amount,
            consumption_percent=consumption_percent,
            threshold_exceeded=threshold_exceeded,
            message=message,
            requires_override=requires_override
        )

    def _get_control_message(
        self,
        allowed: bool,
        threshold: Optional[str],
        percent: Decimal
    ) -> str:
        """Genere le message de controle."""
        if not threshold:
            return "Operation dans les limites budgetaires"

        if threshold == "warning":
            return f"Attention: {percent:.1f}% du budget consomme"
        elif threshold == "critical":
            return f"Seuil critique atteint: {percent:.1f}% du budget consomme"
        elif threshold == "exceeded":
            if allowed:
                return f"Budget depasse ({percent:.1f}%). Validation requise."
            return f"Operation bloquee: budget depasse ({percent:.1f}%)"

        return ""

    # =========================================================================
    # REVISION METHODS
    # =========================================================================

    def create_revision(
        self,
        budget_id: UUID,
        data: BudgetRevisionCreate,
        created_by: Optional[UUID] = None
    ) -> BudgetRevisionResponse:
        """Cree une revision budgetaire."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        if budget.status != BudgetStatus.ACTIVE:
            raise BudgetStatusError(budget_id, budget.status.value, "ACTIVE", "create_revision")

        # Numero de revision
        revision_number = self.repo.get_next_revision_number(budget_id)

        # Calculer le total des changements
        total_change = Decimal("0")
        for detail in data.details:
            line = self.repo.get_budget_line(detail.budget_line_id)
            if line:
                change = detail.new_amount - line.annual_amount
                total_change += change

        revision = BudgetRevision(
            id=uuid.uuid4(),
            budget_id=budget_id,
            revision_number=revision_number,
            name=data.name,
            description=data.description,
            effective_date=data.effective_date,
            reason=data.reason,
            impact_analysis=data.impact_analysis,
            total_change_amount=total_change,
            status=RevisionStatus.DRAFT,
            created_by=created_by
        )

        revision = self.repo.create_revision(revision)

        # Creer les details
        details = []
        for d in data.details:
            line = self.repo.get_budget_line(d.budget_line_id)
            if line:
                detail = BudgetRevisionDetail(
                    revision_id=revision.id,
                    budget_line_id=d.budget_line_id,
                    previous_amount=line.annual_amount,
                    new_amount=d.new_amount,
                    change_amount=d.new_amount - line.annual_amount,
                    affected_period=d.affected_period,
                    justification=d.justification
                )
                details.append(detail)

        self.repo.create_revision_details(details)
        self.repo.commit()

        return BudgetRevisionResponse.model_validate(revision)

    def submit_revision(
        self,
        revision_id: UUID,
        submitted_by: UUID
    ) -> BudgetRevisionResponse:
        """Soumet une revision pour approbation."""
        revision = self.repo.get_revision(revision_id)
        if not revision:
            raise BudgetRevisionNotFoundError(revision_id)

        if revision.status != RevisionStatus.DRAFT:
            raise BudgetRevisionError(
                revision.budget_id, revision_id,
                "La revision n'est pas en brouillon"
            )

        revision = self.repo.update_revision_status(
            revision_id, RevisionStatus.PENDING, submitted_by
        )
        revision.submitted_at = datetime.utcnow()
        revision.submitted_by = submitted_by
        self.repo.commit()

        return BudgetRevisionResponse.model_validate(revision)

    def approve_revision(
        self,
        revision_id: UUID,
        approved_by: UUID,
        comments: Optional[str] = None
    ) -> BudgetRevisionResponse:
        """Approuve une revision."""
        revision = self.repo.get_revision(revision_id)
        if not revision:
            raise BudgetRevisionNotFoundError(revision_id)

        if revision.status != RevisionStatus.PENDING:
            raise BudgetRevisionError(
                revision.budget_id, revision_id,
                "La revision n'est pas en attente d'approbation"
            )

        revision = self.repo.update_revision_status(
            revision_id, RevisionStatus.APPROVED, approved_by, comments
        )
        self.repo.commit()

        return BudgetRevisionResponse.model_validate(revision)

    def apply_revision(
        self,
        revision_id: UUID,
        applied_by: UUID
    ) -> BudgetRevisionResponse:
        """Applique une revision approuvee."""
        revision = self.repo.get_revision(revision_id)
        if not revision:
            raise BudgetRevisionNotFoundError(revision_id)

        if revision.status != RevisionStatus.APPROVED:
            raise BudgetRevisionError(
                revision.budget_id, revision_id,
                "La revision doit etre approuvee avant application"
            )

        # Appliquer les changements
        for detail in revision.details:
            self.repo.update_budget_line(
                detail.budget_line_id,
                {'annual_amount': detail.new_amount},
                applied_by
            )

        # Marquer comme appliquee
        revision = self.repo.update_revision_status(
            revision_id, RevisionStatus.APPLIED, applied_by
        )

        # Recalculer les totaux du budget
        budget = self.repo.get_budget(revision.budget_id)
        self._recalculate_budget_totals(budget)

        self.repo.commit()
        return BudgetRevisionResponse.model_validate(revision)

    # =========================================================================
    # FORECAST METHODS
    # =========================================================================

    def create_forecast(
        self,
        budget_id: UUID,
        data: BudgetForecastCreate,
        created_by: Optional[UUID] = None
    ) -> BudgetForecastResponse:
        """Cree une prevision revisee."""
        budget = self.repo.get_budget(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        # Recuperer le budget original
        original_budget = Decimal("0")
        if data.budget_line_id:
            line = self.repo.get_budget_line(data.budget_line_id)
            if line:
                year, month = map(int, data.period.split("-"))
                monthly_dist = line.monthly_distribution or {}
                original_budget = Decimal(str(monthly_dist.get(str(month), 0)))

        variance = data.revised_forecast - original_budget
        variance_percent = (
            (variance / original_budget * 100)
            if original_budget else Decimal("0")
        )

        forecast = BudgetForecast(
            id=uuid.uuid4(),
            budget_id=budget_id,
            budget_line_id=data.budget_line_id,
            forecast_date=date.today(),
            period=data.period,
            original_budget=original_budget,
            revised_forecast=data.revised_forecast,
            variance=variance,
            variance_percent=variance_percent,
            confidence=data.confidence,
            probability=data.probability,
            assumptions=data.assumptions,
            methodology=data.methodology,
            created_by=created_by
        )

        forecast = self.repo.create_forecast(forecast)
        self.repo.commit()

        return BudgetForecastResponse.model_validate(forecast)

    # =========================================================================
    # SCENARIO METHODS
    # =========================================================================

    def create_scenario(
        self,
        budget_id: UUID,
        data: BudgetScenarioCreate,
        created_by: Optional[UUID] = None
    ) -> BudgetScenarioResponse:
        """Cree un scenario budgetaire."""
        budget = self.repo.get_budget_with_lines(budget_id)
        if not budget:
            raise BudgetNotFoundError(budget_id)

        scenario = BudgetScenario(
            id=uuid.uuid4(),
            budget_id=budget_id,
            name=data.name,
            description=data.description,
            scenario_type=data.scenario_type,
            revenue_adjustment_percent=data.revenue_adjustment_percent,
            expense_adjustment_percent=data.expense_adjustment_percent,
            assumptions=data.assumptions,
            parameters=data.parameters,
            created_by=created_by
        )

        scenario = self.repo.create_scenario(scenario)

        # Calculer les lignes du scenario
        lines = []
        total_revenue = Decimal("0")
        total_expense = Decimal("0")

        for budget_line in budget.lines:
            if budget_line.is_deleted:
                continue

            original = budget_line.annual_amount

            # Appliquer l'ajustement global
            if budget_line.line_type == BudgetLineType.REVENUE:
                adjustment_pct = data.revenue_adjustment_percent
            else:
                adjustment_pct = data.expense_adjustment_percent

            adjusted = original * (1 + adjustment_pct / 100)

            # Appliquer l'ajustement specifique si fourni
            if data.lines:
                for line_data in data.lines:
                    if line_data.budget_line_id == budget_line.id:
                        if line_data.adjusted_amount is not None:
                            adjusted = line_data.adjusted_amount
                        elif line_data.adjustment_percent is not None:
                            adjusted = original * (1 + line_data.adjustment_percent / 100)
                        break

            scenario_line = BudgetScenarioLine(
                scenario_id=scenario.id,
                budget_line_id=budget_line.id,
                original_amount=original,
                adjusted_amount=adjusted,
                adjustment_percent=(
                    ((adjusted - original) / original * 100)
                    if original else Decimal("0")
                ),
                variance=adjusted - original
            )
            lines.append(scenario_line)

            if budget_line.line_type == BudgetLineType.REVENUE:
                total_revenue += adjusted
            else:
                total_expense += adjusted

        self.repo.create_scenario_lines(lines)

        # Mettre a jour les totaux du scenario
        scenario.total_revenue = total_revenue
        scenario.total_expense = total_expense
        scenario.net_result = total_revenue - total_expense
        scenario.variance_vs_baseline = (
            (total_revenue - total_expense) -
            (budget.total_revenue - budget.total_expense)
        )

        self.repo.commit()
        return BudgetScenarioResponse.model_validate(scenario)

    # =========================================================================
    # DASHBOARD METHODS
    # =========================================================================

    def get_dashboard(
        self,
        fiscal_year: Optional[int] = None,
        as_of_date: Optional[date] = None
    ) -> BudgetDashboard:
        """Genere le dashboard budgetaire."""
        if not fiscal_year:
            fiscal_year = date.today().year
        if not as_of_date:
            as_of_date = date.today()

        as_of_period = f"{as_of_date.year}-{as_of_date.month:02d}"

        # Recuperer les budgets actifs
        active_budgets = self.repo.get_active_budgets(fiscal_year)

        # Calculer les totaux
        total_budgeted_expense = Decimal("0")
        total_budgeted_revenue = Decimal("0")
        total_actual_expense = Decimal("0")
        total_actual_revenue = Decimal("0")

        budgets_summary = []

        for budget in active_budgets:
            total_budgeted_expense += budget.total_expense
            total_budgeted_revenue += budget.total_revenue

            # Calculer les realises
            actuals_by_line = self.repo.get_actuals_sum_by_line(budget.id, as_of_period)
            lines = self.repo.get_budget_lines(budget.id)

            ytd_expense = Decimal("0")
            ytd_revenue = Decimal("0")

            for line in lines:
                actual = actuals_by_line.get(line.id, Decimal("0"))
                if line.line_type == BudgetLineType.REVENUE:
                    ytd_revenue += actual
                else:
                    ytd_expense += actual

            total_actual_expense += ytd_expense
            total_actual_revenue += ytd_revenue

            # Resume du budget
            consumption = (
                ytd_expense / budget.total_expense * 100
                if budget.total_expense else Decimal("0")
            )

            alerts = self.repo.get_active_alerts(budget.id)

            budgets_summary.append(BudgetSummary(
                id=budget.id,
                code=budget.code,
                name=budget.name,
                budget_type=budget.budget_type,
                status=budget.status,
                fiscal_year=budget.fiscal_year,
                version_number=budget.version_number,
                total_revenue=budget.total_revenue,
                total_expense=budget.total_expense,
                total_investment=budget.total_investment,
                net_result=budget.net_result,
                ytd_actual_expense=ytd_expense,
                ytd_actual_revenue=ytd_revenue,
                consumption_rate=consumption,
                alerts_count=len(alerts),
                lines_count=len(lines)
            ))

        # Variance globale
        total_variance = (
            (total_actual_revenue - total_budgeted_revenue) -
            (total_actual_expense - total_budgeted_expense)
        )

        # Taux de consommation global
        overall_consumption = (
            total_actual_expense / total_budgeted_expense * 100
            if total_budgeted_expense else Decimal("0")
        )

        # Alertes actives
        all_alerts = self.repo.get_active_alerts(limit=10)
        critical_alerts = [a for a in all_alerts if a.severity == AlertSeverity.CRITICAL]

        # Top depassements / economies
        all_variances = []
        for budget in active_budgets:
            variances = self.calculate_variances(budget.id, as_of_period)
            all_variances.extend(variances)

        # Trier par ecart
        all_variances.sort(key=lambda v: v.variance_amount)
        top_overruns = [v for v in all_variances if v.variance_type == VarianceType.UNFAVORABLE][:5]
        top_savings = [v for v in reversed(all_variances) if v.variance_type == VarianceType.FAVORABLE][:5]

        from .schemas import BudgetAlertResponse
        return BudgetDashboard(
            tenant_id=self.tenant_id,
            fiscal_year=fiscal_year,
            as_of_date=as_of_date,
            total_budgeted_expense=total_budgeted_expense,
            total_budgeted_revenue=total_budgeted_revenue,
            total_actual_expense=total_actual_expense,
            total_actual_revenue=total_actual_revenue,
            total_variance=total_variance,
            overall_consumption_rate=overall_consumption,
            active_budgets_count=len(active_budgets),
            budgets_summary=budgets_summary,
            active_alerts_count=len(all_alerts),
            critical_alerts_count=len(critical_alerts),
            recent_alerts=[BudgetAlertResponse.model_validate(a) for a in all_alerts[:5]],
            top_overruns=top_overruns,
            top_savings=top_savings,
            monthly_trend=[]  # A implementer
        )

    # =========================================================================
    # ALERT METHODS
    # =========================================================================

    def get_active_alerts(
        self,
        budget_id: Optional[UUID] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50
    ) -> List[BudgetAlert]:
        """Recupere les alertes actives."""
        return self.repo.get_active_alerts(budget_id, severity, limit)

    def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: UUID,
        notes: Optional[str] = None
    ) -> BudgetAlert:
        """Acquitte une alerte."""
        alert = self.repo.update_alert_status(
            alert_id, AlertStatus.ACKNOWLEDGED, acknowledged_by
        )
        if not alert:
            raise BudgetNotFoundError(alert_id)
        self.repo.commit()
        return alert

    def resolve_alert(
        self,
        alert_id: UUID,
        resolved_by: UUID,
        resolution_notes: str
    ) -> BudgetAlert:
        """Resout une alerte."""
        alert = self.repo.update_alert_status(
            alert_id, AlertStatus.RESOLVED, resolved_by, resolution_notes
        )
        if not alert:
            raise BudgetNotFoundError(alert_id)
        self.repo.commit()
        return alert

    def _check_budget_alerts(
        self,
        budget: Budget,
        line_id: Optional[UUID],
        period: str
    ):
        """Verifie et genere les alertes de depassement."""
        if line_id:
            lines = [self.repo.get_budget_line(line_id)]
        else:
            lines = self.repo.get_budget_lines(budget.id)

        for line in lines:
            if not line or line.line_type != BudgetLineType.EXPENSE:
                continue

            # Calcul du cumul YTD
            actuals = self.repo.get_actuals(budget.id, line.id)
            actual_ytd = sum(a.amount for a in actuals)
            budget_ytd = line.annual_amount

            if budget_ytd == 0:
                continue

            consumption_pct = actual_ytd / budget_ytd * 100

            # Verifier les seuils
            alert_type = None
            severity = None

            if consumption_pct >= 100:
                alert_type = "THRESHOLD"
                severity = AlertSeverity.EXCEEDED
            elif consumption_pct >= budget.critical_threshold:
                alert_type = "THRESHOLD"
                severity = AlertSeverity.CRITICAL
            elif consumption_pct >= budget.warning_threshold:
                alert_type = "THRESHOLD"
                severity = AlertSeverity.WARNING

            if alert_type:
                alert = BudgetAlert(
                    id=uuid.uuid4(),
                    budget_id=budget.id,
                    budget_line_id=line.id,
                    alert_type=alert_type,
                    severity=severity,
                    status=AlertStatus.ACTIVE,
                    title=f"Seuil budgetaire atteint: {line.name}",
                    message=f"{consumption_pct:.1f}% du budget consomme pour '{line.name}'",
                    threshold_percent=budget.warning_threshold if severity == AlertSeverity.WARNING
                                      else budget.critical_threshold,
                    current_percent=consumption_pct,
                    budget_amount=budget_ytd,
                    actual_amount=actual_ytd,
                    period=period
                )
                self.repo.create_alert(alert)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _generate_periods(self, budget: Budget) -> List[BudgetPeriod]:
        """Genere les periodes d'un budget."""
        periods = []

        if budget.period_type == BudgetPeriodType.MONTHLY:
            current = budget.start_date.replace(day=1)
            period_num = 1

            while current <= budget.end_date:
                # Fin du mois
                _, last_day = calendar.monthrange(current.year, current.month)
                end = date(current.year, current.month, last_day)
                if end > budget.end_date:
                    end = budget.end_date

                period = BudgetPeriod(
                    id=uuid.uuid4(),
                    budget_id=budget.id,
                    period_number=period_num,
                    name=current.strftime("%B %Y"),
                    start_date=current,
                    end_date=end
                )
                periods.append(period)

                # Mois suivant
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)
                period_num += 1

        elif budget.period_type == BudgetPeriodType.QUARTERLY:
            current = budget.start_date
            period_num = 1
            quarter_months = [3, 6, 9, 12]

            while current <= budget.end_date and period_num <= 4:
                q_end_month = quarter_months[period_num - 1]
                _, last_day = calendar.monthrange(budget.fiscal_year, q_end_month)
                end = date(budget.fiscal_year, q_end_month, last_day)

                period = BudgetPeriod(
                    id=uuid.uuid4(),
                    budget_id=budget.id,
                    period_number=period_num,
                    name=f"T{period_num} {budget.fiscal_year}",
                    start_date=current,
                    end_date=min(end, budget.end_date)
                )
                periods.append(period)

                current = end + timedelta(days=1)
                period_num += 1

        elif budget.period_type == BudgetPeriodType.ANNUAL:
            period = BudgetPeriod(
                id=uuid.uuid4(),
                budget_id=budget.id,
                period_number=1,
                name=f"Exercice {budget.fiscal_year}",
                start_date=budget.start_date,
                end_date=budget.end_date
            )
            periods.append(period)

        return periods

    def _distribute_annual_amount(
        self,
        annual_amount: Decimal,
        method: AllocationMethod,
        seasonal_profile: Optional[str] = None
    ) -> Dict[int, Decimal]:
        """Distribue le montant annuel sur les mois."""
        distribution = {}

        if method == AllocationMethod.EQUAL:
            monthly = (annual_amount / 12).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            for m in range(1, 13):
                distribution[m] = monthly

            # Ajuster le dernier mois
            total = sum(distribution.values())
            diff = annual_amount - total
            distribution[12] += diff

        elif method == AllocationMethod.SEASONAL:
            profile = DEFAULT_SEASONAL_PROFILES.get(
                seasonal_profile or "flat",
                DEFAULT_SEASONAL_PROFILES["flat"]
            )
            total_weight = sum(profile)

            for month in range(1, 13):
                weight = Decimal(str(profile[month - 1]))
                amount = (
                    annual_amount * weight / Decimal(str(total_weight))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                distribution[month] = amount

            # Ajuster pour equilibrer
            total = sum(distribution.values())
            diff = annual_amount - total
            distribution[12] += diff

        else:
            # Par defaut: repartition egale
            return self._distribute_annual_amount(annual_amount, AllocationMethod.EQUAL)

        return distribution

    def _recalculate_budget_totals(self, budget: Budget):
        """Recalcule les totaux du budget."""
        lines = self.repo.get_budget_lines(budget.id)

        total_revenue = Decimal("0")
        total_expense = Decimal("0")
        total_investment = Decimal("0")

        for line in lines:
            if line.line_type == BudgetLineType.REVENUE:
                total_revenue += line.annual_amount
            elif line.line_type == BudgetLineType.EXPENSE:
                total_expense += line.annual_amount
            elif line.line_type == BudgetLineType.INVESTMENT:
                total_investment += line.annual_amount

        budget.total_revenue = total_revenue
        budget.total_expense = total_expense
        budget.total_investment = total_investment
        budget.net_result = total_revenue - total_expense

    def _update_line_indicators(self, line_id: UUID):
        """Met a jour les indicateurs d'une ligne."""
        line = self.repo.get_budget_line(line_id)
        if not line:
            return

        actuals = self.repo.get_actuals(line.budget_id, line_id)
        ytd_actual = sum(a.amount for a in actuals)

        line.ytd_actual = ytd_actual
        line.remaining_budget = line.annual_amount - ytd_actual
        line.consumption_rate = (
            (ytd_actual / line.annual_amount * 100)
            if line.annual_amount else Decimal("0")
        )

    def _apply_template(self, budget: Budget, template_id: UUID):
        """Applique un template au budget."""
        template = self.repo.get_template(template_id)
        if not template:
            return

        # Appliquer la structure du template
        for line_data in template.line_template or []:
            category = self.repo.get_category_by_code(line_data.get("category_code"))
            if category:
                line = BudgetLine(
                    id=uuid.uuid4(),
                    budget_id=budget.id,
                    category_id=category.id,
                    name=line_data.get("name", category.name),
                    line_type=category.line_type,
                    annual_amount=Decimal(str(line_data.get("default_amount", 0))),
                    allocation_method=template.default_allocation_method
                )
                self.repo.create_budget_line(line)

    def _copy_budget_structure(
        self,
        budget: Budget,
        source_budget_id: UUID
    ):
        """Copie la structure d'un budget existant."""
        source = self.repo.get_budget_with_lines(source_budget_id)
        if not source:
            return

        for source_line in source.lines:
            if source_line.is_deleted:
                continue

            line = BudgetLine(
                id=uuid.uuid4(),
                budget_id=budget.id,
                category_id=source_line.category_id,
                code=source_line.code,
                name=source_line.name,
                description=source_line.description,
                line_type=source_line.line_type,
                annual_amount=source_line.annual_amount,
                monthly_distribution=source_line.monthly_distribution,
                allocation_method=source_line.allocation_method,
                seasonal_profile=source_line.seasonal_profile,
                cost_center_id=source_line.cost_center_id,
                project_id=source_line.project_id,
                department_id=source_line.department_id,
                account_code=source_line.account_code,
                notes=source_line.notes
            )
            self.repo.create_budget_line(line)


def create_budget_service(db: Session, tenant_id: str) -> BudgetService:
    """Factory pour creer le service budgetaire."""
    return BudgetService(db, tenant_id)
