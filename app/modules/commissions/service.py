"""
Service de Gestion des Commissions Commerciales - GAP-041

Service complet pour la gestion des commissions:
- Plans de commissionnement multi-niveaux
- Calcul automatique sur factures payees
- Paliers progressifs et degressifs
- Accelerateurs de performance
- Split commission (multi-vendeurs)
- Override manager sur equipe
- Validation workflow
- Paiement des commissions
- Rapports et dashboard

Architecture multi-tenant avec isolation stricte.

Inspire de:
- Sage: Plans de commission flexibles
- Axonaut: Simplicity of commission rules
- Pennylane: Integration comptable
- Odoo: Commission multi-niveaux
- Microsoft Dynamics 365: Sales performance management
"""
from __future__ import annotations


from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple, Callable
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session

from .models import (
    CommissionPlan, CommissionTier, CommissionAccelerator,
    CommissionAssignment, SalesTeamMember,
    CommissionTransaction, CommissionCalculation,
    CommissionPeriod, CommissionStatement,
    CommissionAdjustment, CommissionClawback,
    CommissionWorkflow, CommissionAuditLog,
    CommissionBasis, TierType, CommissionStatus, PlanStatus,
    PaymentFrequency, PeriodType, AdjustmentType, WorkflowStatus
)
from .repository import (
    CommissionPlanRepository, CommissionAssignmentRepository,
    SalesTeamMemberRepository, CommissionTransactionRepository,
    CommissionCalculationRepository, CommissionPeriodRepository,
    CommissionStatementRepository, CommissionAdjustmentRepository,
    CommissionClawbackRepository, CommissionAuditLogRepository
)
from .schemas import (
    CommissionPlanCreate, CommissionPlanUpdate,
    AssignmentCreate, TeamMemberCreate,
    TransactionCreate, CalculationRequest, BulkCalculationRequest,
    PeriodCreate, AdjustmentCreate, ClawbackCreate,
    SalesRepPerformance, TeamPerformance, CommissionDashboard, Leaderboard
)
from .exceptions import (
    PlanNotFoundError, PlanDuplicateError, PlanInvalidStateError,
    PlanActivationError, TierConfigurationError,
    AssignmentNotFoundError, AssignmentDuplicateError, AssignmentOverlapError,
    TransactionNotFoundError, TransactionDuplicateError, TransactionLockedError,
    CalculationNotFoundError, CalculationError, CalculationAlreadyExistsError,
    NoPlanApplicableError, CalculationLockedError,
    PeriodNotFoundError, PeriodDuplicateError, PeriodLockedError,
    StatementNotFoundError, StatementAlreadyPaidError, StatementGenerationError,
    AdjustmentNotFoundError, AdjustmentNotPendingError,
    ClawbackNotFoundError, ClawbackNotEligibleError, ClawbackPeriodExpiredError,
    TeamMemberNotFoundError
)

logger = logging.getLogger(__name__)


class CommissionService:
    """
    Service principal de gestion des commissions.

    Responsabilites:
    - Gestion des plans de commissionnement
    - Attribution des plans aux commerciaux/equipes
    - Enregistrement des transactions de vente
    - Calcul automatique des commissions
    - Gestion des periodes et releves
    - Workflow de validation
    - Ajustements et clawbacks
    - Reporting et analytics
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        user_id: UUID = None,
        payroll_callback: Callable = None
    ):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.user_id = user_id
        self.payroll_callback = payroll_callback

        # Repositories
        self.plan_repo = CommissionPlanRepository(db, tenant_id)
        self.assignment_repo = CommissionAssignmentRepository(db, tenant_id)
        self.team_repo = SalesTeamMemberRepository(db, tenant_id)
        self.transaction_repo = CommissionTransactionRepository(db, tenant_id)
        self.calculation_repo = CommissionCalculationRepository(db, tenant_id)
        self.period_repo = CommissionPeriodRepository(db, tenant_id)
        self.statement_repo = CommissionStatementRepository(db, tenant_id)
        self.adjustment_repo = CommissionAdjustmentRepository(db, tenant_id)
        self.clawback_repo = CommissionClawbackRepository(db, tenant_id)
        self.audit_repo = CommissionAuditLogRepository(db, tenant_id)

    # =========================================================================
    # PLANS DE COMMISSION
    # =========================================================================

    def create_plan(
        self,
        data: CommissionPlanCreate
    ) -> CommissionPlan:
        """Cree un nouveau plan de commission."""
        # Verifier unicite du code
        if data.code and self.plan_repo.code_exists(data.code):
            raise PlanDuplicateError(data.code)

        # Valider les paliers
        tiers_data = [t.model_dump() for t in data.tiers]
        self._validate_tiers(tiers_data, data.tier_type)

        # Creer le plan
        plan_data = data.model_dump()
        plan_data["tiers"] = tiers_data
        plan_data["accelerators"] = [a.model_dump() for a in data.accelerators]

        plan = self.plan_repo.create(plan_data, self.user_id)

        # Audit
        self._audit("plan_created", "plan", plan.id, plan.code)

        return plan

    def update_plan(
        self,
        plan_id: UUID,
        data: CommissionPlanUpdate
    ) -> CommissionPlan:
        """Met a jour un plan de commission."""
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))

        # Verifier que le plan peut etre modifie
        if plan.status == PlanStatus.ARCHIVED.value:
            raise PlanInvalidStateError(plan.status, ["draft", "active", "suspended"])

        # Verifier unicite du code si change
        if data.code and data.code != plan.code:
            if self.plan_repo.code_exists(data.code, plan_id):
                raise PlanDuplicateError(data.code)

        update_data = data.model_dump(exclude_unset=True)
        plan = self.plan_repo.update(plan, update_data, self.user_id)

        # Audit
        self._audit("plan_updated", "plan", plan.id, plan.code)

        return plan

    def activate_plan(self, plan_id: UUID) -> CommissionPlan:
        """Active un plan de commission."""
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))

        # Valider les paliers
        if not plan.tiers:
            raise PlanActivationError("Le plan doit avoir au moins un palier")

        # Verifier la coherence des paliers
        tiers_data = [{"min_value": t.min_value, "max_value": t.max_value, "rate": t.rate}
                      for t in plan.tiers]
        self._validate_tiers(tiers_data, TierType(plan.tier_type))

        plan = self.plan_repo.activate(plan, self.user_id)

        # Audit
        self._audit("plan_activated", "plan", plan.id, plan.code)

        return plan

    def suspend_plan(self, plan_id: UUID) -> CommissionPlan:
        """Suspend un plan de commission."""
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))

        plan = self.plan_repo.suspend(plan)

        # Audit
        self._audit("plan_suspended", "plan", plan.id, plan.code)

        return plan

    def archive_plan(self, plan_id: UUID) -> CommissionPlan:
        """Archive un plan de commission."""
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))

        plan = self.plan_repo.archive(plan)

        # Audit
        self._audit("plan_archived", "plan", plan.id, plan.code)

        return plan

    def _validate_tiers(
        self,
        tiers: List[Dict],
        tier_type: TierType
    ) -> None:
        """Valide la configuration des paliers."""
        if not tiers:
            return

        # Trier par min_value
        sorted_tiers = sorted(tiers, key=lambda x: Decimal(str(x.get("min_value", 0))))

        # Verifier la continuite pour les types progressifs
        if tier_type in [TierType.PROGRESSIVE, TierType.RETROACTIVE]:
            for i in range(len(sorted_tiers) - 1):
                current_max = sorted_tiers[i].get("max_value")
                next_min = sorted_tiers[i + 1].get("min_value", 0)

                if current_max is not None:
                    current_max = Decimal(str(current_max))
                    next_min = Decimal(str(next_min))
                    if current_max != next_min:
                        raise TierConfigurationError(
                            f"Discontinuite entre paliers: {current_max} != {next_min}"
                        )

        # Verifier que les taux sont valides
        for tier in sorted_tiers:
            rate = Decimal(str(tier.get("rate", 0)))
            if rate < 0 or rate > 100:
                raise TierConfigurationError(f"Taux invalide: {rate}")

    # =========================================================================
    # ATTRIBUTIONS
    # =========================================================================

    def assign_plan(
        self,
        data: AssignmentCreate
    ) -> CommissionAssignment:
        """Assigne un plan a un commercial/equipe."""
        # Verifier que le plan existe et est actif
        plan = self.plan_repo.get_by_id(data.plan_id)
        if not plan:
            raise PlanNotFoundError(str(data.plan_id))

        if plan.status != PlanStatus.ACTIVE.value:
            raise PlanInvalidStateError(plan.status, ["active"])

        # Verifier qu'il n'y a pas de chevauchement
        if self.assignment_repo.exists_for_period(
            data.assignee_id,
            data.plan_id,
            data.effective_from,
            data.effective_to
        ):
            raise AssignmentOverlapError()

        assignment = self.assignment_repo.create(data.model_dump(), self.user_id)

        # Audit
        self._audit("plan_assigned", "assignment", assignment.id)

        return assignment

    def update_assignment(
        self,
        assignment_id: UUID,
        data: Dict[str, Any]
    ) -> CommissionAssignment:
        """Met a jour une attribution."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise AssignmentNotFoundError(str(assignment_id))

        assignment = self.assignment_repo.update(assignment, data)

        # Audit
        self._audit("assignment_updated", "assignment", assignment.id)

        return assignment

    def deactivate_assignment(self, assignment_id: UUID) -> bool:
        """Desactive une attribution."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise AssignmentNotFoundError(str(assignment_id))

        self.assignment_repo.deactivate(assignment)

        # Audit
        self._audit("assignment_deactivated", "assignment", assignment.id)

        return True

    def get_plans_for_employee(
        self,
        employee_id: UUID,
        effective_date: date = None
    ) -> List[CommissionPlan]:
        """Recupere les plans assignes a un employe."""
        return self.plan_repo.get_plans_for_employee(employee_id, effective_date)

    # =========================================================================
    # TRANSACTIONS
    # =========================================================================

    def record_transaction(
        self,
        data: TransactionCreate
    ) -> CommissionTransaction:
        """Enregistre une transaction de vente."""
        # Verifier qu'il n'y a pas de doublon
        existing = self.transaction_repo.get_by_source(
            data.source_type,
            data.source_id
        )
        if existing:
            raise TransactionDuplicateError(data.source_type, str(data.source_id))

        transaction = self.transaction_repo.create(data.model_dump())

        # Audit
        self._audit(
            "transaction_recorded",
            "transaction",
            transaction.id,
            transaction.source_number
        )

        return transaction

    def update_transaction_payment(
        self,
        transaction_id: UUID,
        payment_status: str,
        payment_date: date = None,
        payment_amount: Decimal = None
    ) -> CommissionTransaction:
        """Met a jour le statut de paiement d'une transaction."""
        transaction = self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise TransactionNotFoundError(str(transaction_id))

        if transaction.commission_locked:
            raise TransactionLockedError(str(transaction_id))

        data = {"payment_status": payment_status}
        if payment_date:
            data["payment_date"] = payment_date
        if payment_amount is not None:
            data["payment_amount"] = payment_amount

        transaction = self.transaction_repo.update(transaction, data)

        # Si paiement complet et trigger on_payment, calculer commission
        if (payment_status == "paid" and
            self._should_trigger_on_payment(transaction)):
            self._calculate_transaction_commission(transaction)

        return transaction

    def _should_trigger_on_payment(
        self,
        transaction: CommissionTransaction
    ) -> bool:
        """Verifie si le calcul doit etre declenche a l'encaissement."""
        plans = self.get_plans_for_employee(
            transaction.sales_rep_id,
            transaction.source_date
        )
        return any(p.trigger_on_payment for p in plans)

    # =========================================================================
    # CALCUL DES COMMISSIONS
    # =========================================================================

    def calculate_commission(
        self,
        request: CalculationRequest
    ) -> CommissionCalculation:
        """Calcule la commission pour un commercial sur une periode."""
        # Recuperer le plan
        plan = self.plan_repo.get_by_id(request.plan_id)
        if not plan:
            raise PlanNotFoundError(str(request.plan_id))

        # Verifier si deja calcule
        existing = self.calculation_repo.get_for_period(
            request.sales_rep_id,
            request.period_start,
            request.period_end,
            [CommissionStatus.CALCULATED.value, CommissionStatus.APPROVED.value]
        )

        if existing and not request.recalculate:
            raise CalculationAlreadyExistsError(
                str(request.sales_rep_id),
                f"{request.period_start} - {request.period_end}"
            )

        # Recuperer les transactions
        transactions = self.transaction_repo.get_for_period(
            request.sales_rep_id,
            request.period_start,
            request.period_end,
            "pending"
        )

        # Filtrer selon le trigger du plan
        if plan.trigger_on_payment:
            transactions = [t for t in transactions if t.payment_status == "paid"]
        elif plan.trigger_on_delivery:
            transactions = [t for t in transactions if t.delivery_status == "delivered"]
        elif plan.trigger_on_invoice:
            # Toutes les factures
            pass

        # Filtrer selon les produits/categories
        transactions = self._filter_transactions_for_plan(transactions, plan)

        if not transactions:
            # Pas de transactions, creer un calcul a zero si minimum garanti
            if plan.minimum_guaranteed > 0:
                return self._create_minimum_calculation(
                    request.sales_rep_id, plan,
                    request.period_start, request.period_end
                )
            raise CalculationError("Aucune transaction pour cette periode")

        # Calculer
        calculation = self._perform_calculation(
            request.sales_rep_id,
            plan,
            transactions,
            request.period_start,
            request.period_end
        )

        # Marquer les transactions comme calculees
        for txn in transactions:
            self.transaction_repo.update_commission_status(txn, "calculated")

        # Audit
        self._audit(
            "commission_calculated",
            "calculation",
            calculation.id,
            extra_info={
                "amount": str(calculation.net_commission),
                "transactions": len(transactions)
            }
        )

        return calculation

    def calculate_all_for_period(
        self,
        request: BulkCalculationRequest
    ) -> Dict[str, Any]:
        """Calcule toutes les commissions pour une periode."""
        results = {
            "success": [],
            "errors": [],
            "total_calculated": Decimal("0")
        }

        # Determiner la periode
        if request.period_id:
            period = self.period_repo.get_by_id(request.period_id)
            if not period:
                raise PeriodNotFoundError(str(request.period_id))
            period_start = period.start_date
            period_end = period.end_date
        else:
            period_start = request.period_start
            period_end = request.period_end

        # Recuperer les plans actifs
        if request.plan_ids:
            plans = [self.plan_repo.get_by_id(pid) for pid in request.plan_ids]
            plans = [p for p in plans if p and p.status == PlanStatus.ACTIVE.value]
        else:
            plans = self.plan_repo.get_active_plans(period_end)

        # Pour chaque plan, recuperer les assignes
        for plan in plans:
            assignments = self.assignment_repo.get_by_plan(plan.id)

            for assignment in assignments:
                # Filtrer si sales_rep_ids specifie
                if (request.sales_rep_ids and
                    assignment.assignee_id not in request.sales_rep_ids):
                    continue

                try:
                    calc_request = CalculationRequest(
                        sales_rep_id=assignment.assignee_id,
                        plan_id=plan.id,
                        period_start=period_start,
                        period_end=period_end,
                        recalculate=request.recalculate
                    )
                    calculation = self.calculate_commission(calc_request)
                    results["success"].append({
                        "sales_rep_id": str(assignment.assignee_id),
                        "plan_id": str(plan.id),
                        "calculation_id": str(calculation.id),
                        "amount": str(calculation.net_commission)
                    })
                    results["total_calculated"] += calculation.net_commission
                except Exception as e:
                    results["errors"].append({
                        "sales_rep_id": str(assignment.assignee_id),
                        "plan_id": str(plan.id),
                        "error": str(e)
                    })

        return results

    def _filter_transactions_for_plan(
        self,
        transactions: List[CommissionTransaction],
        plan: CommissionPlan
    ) -> List[CommissionTransaction]:
        """Filtre les transactions selon les criteres du plan."""
        filtered = transactions

        # Filtrer par produits
        if not plan.apply_to_all_products:
            if plan.included_products:
                filtered = [t for t in filtered
                           if str(t.product_id) in plan.included_products]
            if plan.excluded_products:
                filtered = [t for t in filtered
                           if str(t.product_id) not in plan.excluded_products]

        # Filtrer par categories
        if plan.included_categories:
            filtered = [t for t in filtered
                       if t.product_category in plan.included_categories]
        if plan.excluded_categories:
            filtered = [t for t in filtered
                       if t.product_category not in plan.excluded_categories]

        # Filtrer par clients
        if not plan.apply_to_all_customers:
            if plan.included_customer_segments:
                filtered = [t for t in filtered
                           if t.customer_segment in plan.included_customer_segments]
            if plan.excluded_customer_segments:
                filtered = [t for t in filtered
                           if t.customer_segment not in plan.excluded_customer_segments]

        # Nouveaux clients uniquement
        if plan.new_customers_only:
            filtered = [t for t in filtered if t.is_new_customer]

        return filtered

    def _perform_calculation(
        self,
        sales_rep_id: UUID,
        plan: CommissionPlan,
        transactions: List[CommissionTransaction],
        period_start: date,
        period_end: date
    ) -> CommissionCalculation:
        """Effectue le calcul de commission."""
        # Calculer la base
        base_amount = Decimal("0")
        transaction_ids = []

        for txn in transactions:
            amount = self._get_base_amount(txn, CommissionBasis(plan.basis))
            if amount is not None:
                # Appliquer le split si present
                if txn.has_split and txn.split_config:
                    rep_share = Decimal("100")
                    for split in txn.split_config:
                        if str(split.get("participant_id")) != str(sales_rep_id):
                            rep_share -= Decimal(str(split.get("percent", 0)))
                    amount = amount * rep_share / Decimal("100")

                base_amount += amount
                transaction_ids.append(str(txn.id))

        # Calculer selon les paliers
        commission_amount, tier_breakdown = self._calculate_tiered(
            base_amount, plan
        )

        # Appliquer les accelerateurs
        accelerator_bonus = Decimal("0")
        accelerators_applied = []

        if plan.accelerators:
            accelerator_bonus, accelerators_applied = self._apply_accelerators(
                commission_amount,
                base_amount,
                plan,
                period_end
            )

        # Total brut
        gross_commission = commission_amount + accelerator_bonus

        # Appliquer le plafond
        cap_applied = False
        pre_cap_amount = None

        if plan.cap_enabled and plan.cap_amount:
            if gross_commission > plan.cap_amount:
                pre_cap_amount = gross_commission
                gross_commission = plan.cap_amount
                cap_applied = True

        # Appliquer le minimum garanti
        if gross_commission < plan.minimum_guaranteed:
            gross_commission = plan.minimum_guaranteed

        # Net (avant ajustements)
        net_commission = gross_commission

        # Calculer le taux d'atteinte
        achievement_rate = None
        if plan.quota_amount:
            achievement_rate = (
                base_amount / plan.quota_amount * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Determiner le palier applique
        tier_applied = None
        rate_applied = None
        if tier_breakdown:
            last_tier = tier_breakdown[-1]
            tier_applied = last_tier.get("tier")
            rate_applied = Decimal(str(last_tier.get("rate", 0)))

        # Creer le calcul
        calculation_data = {
            "plan_id": plan.id,
            "sales_rep_id": sales_rep_id,
            "sales_rep_name": self._get_employee_name(sales_rep_id),
            "period_start": period_start,
            "period_end": period_end,
            "basis": plan.basis,
            "base_amount": base_amount,
            "currency": plan.currency,
            "rate_applied": rate_applied,
            "tier_applied": tier_applied,
            "commission_amount": commission_amount,
            "accelerator_bonus": accelerator_bonus,
            "accelerators_applied": accelerators_applied,
            "split_percent": Decimal("100"),
            "gross_commission": gross_commission,
            "adjustments": Decimal("0"),
            "net_commission": net_commission,
            "cap_applied": cap_applied,
            "pre_cap_amount": pre_cap_amount,
            "cap_amount": plan.cap_amount if cap_applied else None,
            "quota_target": plan.quota_amount,
            "quota_achieved": base_amount,
            "achievement_rate": achievement_rate,
            "calculation_details": {
                "tier_breakdown": tier_breakdown,
                "transaction_count": len(transactions),
                "transaction_ids": transaction_ids
            },
            "status": CommissionStatus.CALCULATED.value,
            "calculated_by": "system"
        }

        return self.calculation_repo.create(calculation_data)

    def _get_base_amount(
        self,
        transaction: CommissionTransaction,
        basis: CommissionBasis
    ) -> Optional[Decimal]:
        """Recupere le montant de base selon le type de commission."""
        if basis == CommissionBasis.REVENUE:
            return transaction.revenue
        elif basis == CommissionBasis.REVENUE_TTC:
            return transaction.revenue_ttc or transaction.revenue
        elif basis == CommissionBasis.MARGIN:
            return transaction.margin
        elif basis == CommissionBasis.MARGIN_PERCENT:
            return transaction.margin_percent
        elif basis == CommissionBasis.GROSS_PROFIT:
            return transaction.margin
        elif basis == CommissionBasis.VOLUME:
            return transaction.quantity
        elif basis == CommissionBasis.COLLECTED:
            if transaction.payment_status == "paid":
                return transaction.payment_amount or transaction.revenue
            return None
        elif basis == CommissionBasis.NEW_BUSINESS:
            return transaction.revenue if transaction.is_new_customer else None
        elif basis == CommissionBasis.UPSELL:
            return transaction.revenue if transaction.transaction_type == "upsell" else None
        elif basis == CommissionBasis.RENEWAL:
            return transaction.revenue if transaction.transaction_type == "renewal" else None

        return transaction.revenue

    def _calculate_tiered(
        self,
        base_amount: Decimal,
        plan: CommissionPlan
    ) -> Tuple[Decimal, List[Dict]]:
        """Calcule la commission selon les paliers."""
        total_commission = Decimal("0")
        breakdown = []

        tier_type = TierType(plan.tier_type)
        tiers = sorted(plan.tiers, key=lambda t: t.min_value)

        if tier_type == TierType.FLAT:
            # Taux fixe (premier palier)
            if tiers:
                tier = tiers[0]
                commission = (
                    base_amount * tier.rate / Decimal("100")
                ) + tier.fixed_amount
                total_commission = commission.quantize(Decimal("0.01"), ROUND_HALF_UP)
                breakdown.append({
                    "tier": tier.name or f"Tier {tier.tier_number}",
                    "rate": str(tier.rate),
                    "base": str(base_amount),
                    "commission": str(total_commission)
                })

        elif tier_type == TierType.PROGRESSIVE:
            # Paliers progressifs
            remaining = base_amount
            for tier in tiers:
                if remaining <= 0:
                    break

                tier_min = tier.min_value
                tier_max = tier.max_value or Decimal("999999999999")

                if base_amount <= tier_min:
                    continue

                applicable = min(remaining, tier_max - tier_min)
                if applicable > 0:
                    tier_commission = (
                        applicable * tier.rate / Decimal("100")
                    ).quantize(Decimal("0.01"), ROUND_HALF_UP)
                    total_commission += tier_commission
                    breakdown.append({
                        "tier": tier.name or f"Tier {tier.tier_number}",
                        "range": f"{tier_min}-{tier_max}",
                        "rate": str(tier.rate),
                        "applicable": str(applicable),
                        "commission": str(tier_commission)
                    })
                    remaining -= applicable

        elif tier_type == TierType.RETROACTIVE:
            # Retroactif
            applicable_tier = None
            for tier in tiers:
                if base_amount >= tier.min_value:
                    applicable_tier = tier

            if applicable_tier:
                commission = (
                    base_amount * applicable_tier.rate / Decimal("100")
                ).quantize(Decimal("0.01"), ROUND_HALF_UP)
                total_commission = commission + applicable_tier.fixed_amount
                breakdown.append({
                    "tier": applicable_tier.name or f"Tier {applicable_tier.tier_number}",
                    "rate": str(applicable_tier.rate),
                    "base": str(base_amount),
                    "commission": str(total_commission),
                    "type": "retroactive"
                })

        elif tier_type == TierType.REGRESSIVE:
            # Degressif
            applicable_tier = tiers[0] if tiers else None
            for tier in tiers:
                if base_amount >= tier.min_value:
                    applicable_tier = tier

            if applicable_tier:
                commission = (
                    base_amount * applicable_tier.rate / Decimal("100")
                ).quantize(Decimal("0.01"), ROUND_HALF_UP)
                total_commission = commission
                breakdown.append({
                    "tier": applicable_tier.name or f"Tier {applicable_tier.tier_number}",
                    "rate": str(applicable_tier.rate),
                    "base": str(base_amount),
                    "commission": str(total_commission),
                    "type": "regressive"
                })

        elif tier_type == TierType.STEPPED:
            # Par paliers avec bonus
            applicable_tier = None
            for tier in tiers:
                if base_amount >= tier.min_value:
                    applicable_tier = tier

            if applicable_tier:
                commission = (
                    base_amount * applicable_tier.rate / Decimal("100")
                ).quantize(Decimal("0.01"), ROUND_HALF_UP)
                total_commission = commission + (applicable_tier.tier_bonus or Decimal("0"))
                breakdown.append({
                    "tier": applicable_tier.name or f"Tier {applicable_tier.tier_number}",
                    "rate": str(applicable_tier.rate),
                    "base": str(base_amount),
                    "tier_bonus": str(applicable_tier.tier_bonus or 0),
                    "commission": str(total_commission),
                    "type": "stepped"
                })

        return total_commission, breakdown

    def _apply_accelerators(
        self,
        base_commission: Decimal,
        achieved: Decimal,
        plan: CommissionPlan,
        period_date: date
    ) -> Tuple[Decimal, List[str]]:
        """Applique les accelerateurs de performance."""
        bonus = Decimal("0")
        applied = []

        for acc in plan.accelerators:
            if not acc.is_active:
                continue

            # Verifier les dates
            if acc.valid_from and period_date < acc.valid_from:
                continue
            if acc.valid_to and period_date > acc.valid_to:
                continue

            # Verifier le seuil
            if self._check_accelerator_threshold(acc, achieved, plan.quota_amount):
                # Calculer le bonus
                acc_bonus = Decimal("0")

                if acc.multiplier and acc.multiplier > Decimal("1"):
                    acc_bonus = base_commission * (acc.multiplier - Decimal("1"))

                if acc.bonus_amount:
                    acc_bonus += acc.bonus_amount

                if acc.bonus_percent:
                    acc_bonus += base_commission * acc.bonus_percent / Decimal("100")

                # Appliquer le plafond de bonus
                if acc.max_bonus_amount and acc_bonus > acc.max_bonus_amount:
                    acc_bonus = acc.max_bonus_amount

                bonus += acc_bonus.quantize(Decimal("0.01"), ROUND_HALF_UP)
                applied.append(str(acc.id))

        return bonus, applied

    def _check_accelerator_threshold(
        self,
        accelerator: CommissionAccelerator,
        achieved: Decimal,
        target: Decimal
    ) -> bool:
        """Verifie si le seuil de l'accelerateur est atteint."""
        threshold = accelerator.threshold_value
        operator = accelerator.threshold_operator

        if accelerator.threshold_type == "quota_percent":
            if not target or target == 0:
                return False
            value = achieved / target * Decimal("100")
        elif accelerator.threshold_type == "absolute_amount":
            value = achieved
        else:
            return False

        if operator == ">=":
            return value >= threshold
        elif operator == ">":
            return value > threshold
        elif operator == "=":
            return value == threshold
        elif operator == "<":
            return value < threshold
        elif operator == "<=":
            return value <= threshold

        return False

    def _create_minimum_calculation(
        self,
        sales_rep_id: UUID,
        plan: CommissionPlan,
        period_start: date,
        period_end: date
    ) -> CommissionCalculation:
        """Cree un calcul avec minimum garanti."""
        calculation_data = {
            "plan_id": plan.id,
            "sales_rep_id": sales_rep_id,
            "sales_rep_name": self._get_employee_name(sales_rep_id),
            "period_start": period_start,
            "period_end": period_end,
            "basis": plan.basis,
            "base_amount": Decimal("0"),
            "currency": plan.currency,
            "commission_amount": Decimal("0"),
            "accelerator_bonus": Decimal("0"),
            "accelerators_applied": [],
            "gross_commission": plan.minimum_guaranteed,
            "adjustments": Decimal("0"),
            "net_commission": plan.minimum_guaranteed,
            "quota_target": plan.quota_amount,
            "quota_achieved": Decimal("0"),
            "achievement_rate": Decimal("0"),
            "calculation_details": {
                "minimum_guaranteed_applied": True
            },
            "status": CommissionStatus.CALCULATED.value,
            "calculated_by": "system",
            "notes": "Minimum garanti applique"
        }

        return self.calculation_repo.create(calculation_data)

    def _calculate_transaction_commission(
        self,
        transaction: CommissionTransaction
    ):
        """Calcule la commission pour une seule transaction."""
        plans = self.get_plans_for_employee(
            transaction.sales_rep_id,
            transaction.source_date
        )

        for plan in plans:
            if plan.trigger_on_payment:
                # Creer un calcul pour cette transaction
                filtered = self._filter_transactions_for_plan([transaction], plan)
                if filtered:
                    calculation = self._perform_calculation(
                        transaction.sales_rep_id,
                        plan,
                        filtered,
                        transaction.source_date,
                        transaction.source_date
                    )
                    calculation.transaction_id = transaction.id
                    self.db.commit()

    def _get_employee_name(self, employee_id: UUID) -> str:
        """Recupere le nom d'un employe."""
        member = self.team_repo.get_by_employee_id(employee_id)
        return member.employee_name if member else str(employee_id)

    # =========================================================================
    # CALCUL OVERRIDE MANAGER
    # =========================================================================

    def calculate_manager_override(
        self,
        manager_id: UUID,
        period_start: date,
        period_end: date
    ) -> CommissionCalculation:
        """Calcule l'override du manager sur les ventes de son equipe."""
        manager = self.team_repo.get_by_employee_id(manager_id)
        if not manager:
            raise TeamMemberNotFoundError(employee_id=str(manager_id))

        if not manager.override_enabled:
            raise CalculationError("Override non active pour ce manager")

        # Recuperer tous les subordonnes
        subordinates = self.team_repo.get_all_subordinates_recursive(
            manager.id,
            max_depth=manager.override_levels
        )

        if not subordinates:
            raise CalculationError("Aucun subordonne pour ce manager")

        # Calculer le total des ventes de l'equipe
        total_base = Decimal("0")
        transaction_ids = []

        for sub in subordinates:
            transactions = self.transaction_repo.get_for_period(
                sub.employee_id,
                period_start,
                period_end
            )

            for txn in transactions:
                amount = self._get_base_amount(
                    txn,
                    CommissionBasis(manager.override_basis)
                )
                if amount:
                    total_base += amount
                    transaction_ids.append(str(txn.id))

        # Calculer l'override
        override_commission = (
            total_base * manager.override_rate / Decimal("100")
        ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        calculation_data = {
            "sales_rep_id": manager_id,
            "sales_rep_name": manager.employee_name,
            "period_start": period_start,
            "period_end": period_end,
            "basis": manager.override_basis,
            "base_amount": total_base,
            "rate_applied": manager.override_rate,
            "commission_amount": override_commission,
            "gross_commission": override_commission,
            "net_commission": override_commission,
            "calculation_details": {
                "type": "manager_override",
                "subordinate_count": len(subordinates),
                "transaction_count": len(transaction_ids),
                "transaction_ids": transaction_ids
            },
            "status": CommissionStatus.CALCULATED.value,
            "calculated_by": "system",
            "notes": f"Override manager {manager.override_rate}% sur equipe"
        }

        calculation = self.calculation_repo.create(calculation_data)

        # Audit
        self._audit(
            "override_calculated",
            "calculation",
            calculation.id,
            extra_info={"amount": str(override_commission)}
        )

        return calculation

    # =========================================================================
    # SPLIT COMMISSIONS
    # =========================================================================

    def calculate_split_commissions(
        self,
        transaction_id: UUID,
        plan_id: UUID
    ) -> List[CommissionCalculation]:
        """Calcule les commissions splitees pour tous les participants."""
        transaction = self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise TransactionNotFoundError(str(transaction_id))

        if not transaction.has_split or not transaction.split_config:
            raise CalculationError("Transaction sans configuration de split")

        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))

        calculations = []
        base_amount = self._get_base_amount(
            transaction,
            CommissionBasis(plan.basis)
        )

        if not base_amount:
            return calculations

        # Commission du vendeur principal
        primary_share = Decimal("100")
        for split in transaction.split_config:
            primary_share -= Decimal(str(split.get("percent", 0)))

        if primary_share > 0:
            primary_amount = base_amount * primary_share / Decimal("100")
            primary_commission, _ = self._calculate_tiered(primary_amount, plan)

            primary_calc = self.calculation_repo.create({
                "transaction_id": transaction_id,
                "plan_id": plan.id,
                "sales_rep_id": transaction.sales_rep_id,
                "sales_rep_name": transaction.sales_rep_name,
                "period_start": transaction.source_date,
                "period_end": transaction.source_date,
                "basis": plan.basis,
                "base_amount": primary_amount,
                "split_percent": primary_share,
                "split_role": "primary",
                "original_amount": base_amount,
                "commission_amount": primary_commission,
                "gross_commission": primary_commission,
                "net_commission": primary_commission,
                "status": CommissionStatus.CALCULATED.value,
                "notes": f"Part principale ({primary_share}%)"
            })
            calculations.append(primary_calc)

        # Commissions des participants secondaires
        for split in transaction.split_config:
            participant_id = split.get("participant_id")
            share_percent = Decimal(str(split.get("percent", 0)))
            role = split.get("role", "secondary")

            if share_percent <= 0:
                continue

            split_amount = base_amount * share_percent / Decimal("100")
            split_commission, _ = self._calculate_tiered(split_amount, plan)

            participant_name = self._get_employee_name(UUID(participant_id))

            split_calc = self.calculation_repo.create({
                "transaction_id": transaction_id,
                "plan_id": plan.id,
                "sales_rep_id": UUID(participant_id),
                "sales_rep_name": participant_name,
                "period_start": transaction.source_date,
                "period_end": transaction.source_date,
                "basis": plan.basis,
                "base_amount": split_amount,
                "split_percent": share_percent,
                "split_role": role,
                "original_amount": base_amount,
                "commission_amount": split_commission,
                "gross_commission": split_commission,
                "net_commission": split_commission,
                "status": CommissionStatus.CALCULATED.value,
                "notes": f"Part {role} ({share_percent}%)"
            })
            calculations.append(split_calc)

        # Marquer la transaction comme calculee
        self.transaction_repo.update_commission_status(
            transaction, "calculated", lock=True
        )

        return calculations

    # =========================================================================
    # WORKFLOW DE VALIDATION
    # =========================================================================

    def approve_calculation(
        self,
        calculation_id: UUID,
        comments: str = None
    ) -> CommissionCalculation:
        """Approuve un calcul de commission."""
        calculation = self.calculation_repo.get_by_id(calculation_id)
        if not calculation:
            raise CalculationNotFoundError(str(calculation_id))

        if calculation.status != CommissionStatus.CALCULATED.value:
            raise CalculationLockedError(
                str(calculation_id),
                calculation.status
            )

        calculation = self.calculation_repo.approve(calculation, self.user_id)

        if comments:
            calculation.notes = (calculation.notes or "") + f"\nApprobation: {comments}"
            self.db.commit()

        # Audit
        self._audit("calculation_approved", "calculation", calculation.id)

        return calculation

    def reject_calculation(
        self,
        calculation_id: UUID,
        reason: str
    ) -> CommissionCalculation:
        """Rejette un calcul de commission."""
        calculation = self.calculation_repo.get_by_id(calculation_id)
        if not calculation:
            raise CalculationNotFoundError(str(calculation_id))

        calculation.status = CommissionStatus.DISPUTED.value
        calculation.dispute_reason = reason
        calculation.version += 1
        self.db.commit()

        # Audit
        self._audit(
            "calculation_disputed",
            "calculation",
            calculation.id,
            extra_info={"reason": reason}
        )

        return calculation

    def validate_for_payment(
        self,
        calculation_id: UUID
    ) -> CommissionCalculation:
        """Valide un calcul pour paiement."""
        calculation = self.calculation_repo.get_by_id(calculation_id)
        if not calculation:
            raise CalculationNotFoundError(str(calculation_id))

        if calculation.status != CommissionStatus.APPROVED.value:
            raise CalculationLockedError(
                str(calculation_id),
                calculation.status
            )

        calculation = self.calculation_repo.validate(calculation, self.user_id)

        # Audit
        self._audit("calculation_validated", "calculation", calculation.id)

        return calculation

    def bulk_approve_calculations(
        self,
        calculation_ids: List[UUID]
    ) -> Dict[str, Any]:
        """Approuve plusieurs calculs en masse."""
        results = {"approved": [], "errors": []}

        for calc_id in calculation_ids:
            try:
                self.approve_calculation(calc_id)
                results["approved"].append(str(calc_id))
            except Exception as e:
                results["errors"].append({
                    "calculation_id": str(calc_id),
                    "error": str(e)
                })

        return results

    # =========================================================================
    # PERIODES & RELEVES
    # =========================================================================

    def create_period(
        self,
        data: PeriodCreate
    ) -> CommissionPeriod:
        """Cree une nouvelle periode de commissionnement."""
        # Verifier unicite du code
        if data.code and self.period_repo.code_exists(data.code):
            raise PeriodDuplicateError(data.code)

        # Verifier pas de chevauchement
        if self.period_repo.check_overlap(data.start_date, data.end_date):
            raise PeriodDuplicateError(
                f"Chevauchement avec periode existante"
            )

        period = self.period_repo.create(data.model_dump(), self.user_id)

        # Audit
        self._audit("period_created", "period", period.id, period.code)

        return period

    def close_period(
        self,
        period_id: UUID
    ) -> CommissionPeriod:
        """Cloture une periode de commissionnement."""
        period = self.period_repo.get_by_id(period_id)
        if not period:
            raise PeriodNotFoundError(str(period_id))

        if period.is_locked:
            raise PeriodLockedError(str(period_id))

        # Mettre a jour les totaux
        calcs, _ = self.calculation_repo.list(
            filters=CalculationFilters(period_id=period_id),
            page=1, page_size=10000
        )

        period.total_commissions = sum(c.net_commission for c in calcs)
        period.calculation_count = len(calcs)

        period = self.period_repo.close(period, self.user_id)

        # Audit
        self._audit("period_closed", "period", period.id, period.code)

        return period

    def generate_statement(
        self,
        period_id: UUID,
        sales_rep_id: UUID
    ) -> CommissionStatement:
        """Genere un releve de commission pour un commercial."""
        period = self.period_repo.get_by_id(period_id)
        if not period:
            raise PeriodNotFoundError(str(period_id))

        # Recuperer les calculs approuves/valides
        calculations = self.calculation_repo.get_for_period(
            sales_rep_id,
            period.start_date,
            period.end_date,
            [CommissionStatus.APPROVED.value, CommissionStatus.VALIDATED.value]
        )

        if not calculations:
            raise StatementGenerationError("Aucun calcul approuve pour cette periode")

        # Calculer les totaux
        gross = sum(c.gross_commission for c in calculations)
        acc_bonus = sum(c.accelerator_bonus for c in calculations)
        adjustments = sum(c.adjustments for c in calculations)

        # Recuperer les clawbacks en attente
        clawbacks = self.clawback_repo.get_pending_for_rep(sales_rep_id)
        clawback_total = sum(c.clawback_amount for c in clawbacks)

        # Net
        net = gross + adjustments - clawback_total

        # YTD
        ytd = self.calculation_repo.get_ytd_totals(
            sales_rep_id,
            period.start_date.year
        )

        # Generer le numero
        statement_number = self.statement_repo.get_next_number(period.code)

        statement = self.statement_repo.create({
            "statement_number": statement_number,
            "period_id": period.id,
            "sales_rep_id": sales_rep_id,
            "sales_rep_name": self._get_employee_name(sales_rep_id),
            "period_start": period.start_date,
            "period_end": period.end_date,
            "gross_commissions": gross,
            "accelerator_bonuses": acc_bonus,
            "adjustments": adjustments,
            "clawbacks": clawback_total,
            "net_commission": net,
            "ytd_commissions": ytd["total_commission"] + net,
            "ytd_sales": ytd["total_sales"],
            "transaction_count": sum(
                len(c.calculation_details.get("transaction_ids", []))
                for c in calculations
            ),
            "calculation_ids": [str(c.id) for c in calculations],
            "status": CommissionStatus.PENDING.value
        })

        # Appliquer les clawbacks
        for clawback in clawbacks:
            self.clawback_repo.apply(clawback, statement.id)

        # Audit
        self._audit(
            "statement_generated",
            "statement",
            statement.id,
            statement.statement_number
        )

        return statement

    def approve_statement(
        self,
        statement_id: UUID
    ) -> CommissionStatement:
        """Approuve un releve de commission."""
        statement = self.statement_repo.get_by_id(statement_id)
        if not statement:
            raise StatementNotFoundError(str(statement_id))

        statement = self.statement_repo.approve(statement, self.user_id)

        # Audit
        self._audit(
            "statement_approved",
            "statement",
            statement.id,
            statement.statement_number
        )

        return statement

    def pay_statement(
        self,
        statement_id: UUID,
        payment_reference: str,
        payment_method: str = None
    ) -> CommissionStatement:
        """Marque un releve comme paye."""
        statement = self.statement_repo.get_by_id(statement_id)
        if not statement:
            raise StatementNotFoundError(str(statement_id))

        if statement.status == CommissionStatus.PAID.value:
            raise StatementAlreadyPaidError(str(statement_id))

        statement = self.statement_repo.mark_paid(
            statement,
            payment_reference,
            payment_method
        )

        # Marquer les calculs comme payes
        for calc_id in statement.calculation_ids:
            calc = self.calculation_repo.get_by_id(UUID(calc_id))
            if calc:
                self.calculation_repo.mark_paid(calc, payment_reference)

        # Callback integration paie
        if self.payroll_callback:
            try:
                self.payroll_callback(statement)
            except Exception as e:
                logger.error(f"Erreur integration paie: {e}")

        # Audit
        self._audit(
            "statement_paid",
            "statement",
            statement.id,
            statement.statement_number,
            extra_info={"payment_reference": payment_reference}
        )

        return statement

    # =========================================================================
    # AJUSTEMENTS
    # =========================================================================

    def create_adjustment(
        self,
        data: AdjustmentCreate
    ) -> CommissionAdjustment:
        """Cree un ajustement de commission."""
        adjustment = self.adjustment_repo.create(
            data.model_dump(),
            self.user_id
        )

        # Audit
        self._audit(
            "adjustment_created",
            "adjustment",
            adjustment.id,
            adjustment.code,
            extra_info={
                "type": adjustment.adjustment_type,
                "amount": str(adjustment.amount)
            }
        )

        return adjustment

    def approve_adjustment(
        self,
        adjustment_id: UUID
    ) -> CommissionAdjustment:
        """Approuve un ajustement."""
        adjustment = self.adjustment_repo.get_by_id(adjustment_id)
        if not adjustment:
            raise AdjustmentNotFoundError(str(adjustment_id))

        if adjustment.status != WorkflowStatus.PENDING.value:
            raise AdjustmentNotPendingError(
                str(adjustment_id),
                adjustment.status
            )

        adjustment = self.adjustment_repo.approve(adjustment, self.user_id)

        # Audit
        self._audit(
            "adjustment_approved",
            "adjustment",
            adjustment.id,
            adjustment.code
        )

        return adjustment

    def reject_adjustment(
        self,
        adjustment_id: UUID,
        reason: str
    ) -> CommissionAdjustment:
        """Rejette un ajustement."""
        adjustment = self.adjustment_repo.get_by_id(adjustment_id)
        if not adjustment:
            raise AdjustmentNotFoundError(str(adjustment_id))

        adjustment = self.adjustment_repo.reject(
            adjustment,
            self.user_id,
            reason
        )

        # Audit
        self._audit(
            "adjustment_rejected",
            "adjustment",
            adjustment.id,
            adjustment.code,
            extra_info={"reason": reason}
        )

        return adjustment

    # =========================================================================
    # CLAWBACKS
    # =========================================================================

    def create_clawback(
        self,
        data: ClawbackCreate
    ) -> CommissionClawback:
        """Cree un clawback (recuperation de commission)."""
        # Verifier le calcul original
        calculation = self.calculation_repo.get_by_id(data.original_calculation_id)
        if not calculation:
            raise CalculationNotFoundError(str(data.original_calculation_id))

        # Verifier le plan pour la periode de clawback
        plan = self.plan_repo.get_by_id(calculation.plan_id) if calculation.plan_id else None

        if plan and plan.clawback_enabled:
            # Verifier la periode
            transaction = self.transaction_repo.get_by_id(data.original_transaction_id)
            if transaction:
                days_since = (data.cancellation_date - transaction.source_date).days
                if days_since > plan.clawback_period_days:
                    raise ClawbackPeriodExpiredError(
                        str(transaction.source_date),
                        plan.clawback_period_days
                    )

        clawback_data = data.model_dump()
        clawback_data["original_commission"] = calculation.net_commission

        clawback = self.clawback_repo.create(clawback_data, self.user_id)

        # Audit
        self._audit(
            "clawback_created",
            "clawback",
            clawback.id,
            clawback.code,
            extra_info={"amount": str(clawback.clawback_amount)}
        )

        return clawback

    def check_clawback_eligibility(
        self,
        transaction_id: UUID,
        cancellation_date: date
    ) -> List[Dict[str, Any]]:
        """Verifie l'eligibilite au clawback pour une transaction."""
        calculations = self.calculation_repo.get_by_transaction(transaction_id)

        eligible = []
        for calc in calculations:
            if not calc.plan_id:
                continue

            plan = self.plan_repo.get_by_id(calc.plan_id)
            if not plan or not plan.clawback_enabled:
                continue

            transaction = self.transaction_repo.get_by_id(transaction_id)
            if not transaction:
                continue

            days_since = (cancellation_date - transaction.source_date).days

            if days_since <= plan.clawback_period_days:
                eligible.append({
                    "calculation_id": str(calc.id),
                    "sales_rep_id": str(calc.sales_rep_id),
                    "commission_amount": str(calc.net_commission),
                    "days_since_transaction": days_since,
                    "clawback_period": plan.clawback_period_days,
                    "clawback_percent": plan.clawback_percent
                })

        return eligible

    def waive_clawback(
        self,
        clawback_id: UUID,
        reason: str
    ) -> CommissionClawback:
        """Annule un clawback."""
        clawback = self.clawback_repo.get_by_id(clawback_id)
        if not clawback:
            raise ClawbackNotFoundError(str(clawback_id))

        clawback = self.clawback_repo.waive(clawback, self.user_id, reason)

        # Audit
        self._audit(
            "clawback_waived",
            "clawback",
            clawback.id,
            clawback.code,
            extra_info={"reason": reason}
        )

        return clawback

    # =========================================================================
    # REPORTING & DASHBOARD
    # =========================================================================

    def get_sales_rep_performance(
        self,
        sales_rep_id: UUID,
        period_start: date,
        period_end: date
    ) -> SalesRepPerformance:
        """Recupere les performances d'un commercial."""
        transactions = self.transaction_repo.get_for_period(
            sales_rep_id,
            period_start,
            period_end
        )

        calculations, _ = self.calculation_repo.list(
            filters=CalculationFilters(
                sales_rep_id=sales_rep_id,
                period_start=period_start,
                period_end=period_end
            ),
            page=1, page_size=1000
        )

        total_revenue = sum(t.revenue for t in transactions)
        total_margin = sum(t.margin or Decimal("0") for t in transactions)
        total_commissions = sum(c.net_commission for c in calculations)

        # Quota
        assignments = self.assignment_repo.get_by_assignee(
            sales_rep_id, period_end
        )
        quota_target = None
        for a in assignments:
            if a.quota_override:
                quota_target = (quota_target or Decimal("0")) + a.quota_override
            else:
                plan = self.plan_repo.get_by_id(a.plan_id)
                if plan and plan.quota_amount:
                    quota_target = (quota_target or Decimal("0")) + plan.quota_amount

        achievement_rate = None
        if quota_target:
            achievement_rate = (
                total_revenue / quota_target * Decimal("100")
            ).quantize(Decimal("0.01"))

        commission_rate = None
        if total_revenue > 0:
            commission_rate = (
                total_commissions / total_revenue * Decimal("100")
            ).quantize(Decimal("0.01"))

        return SalesRepPerformance(
            sales_rep_id=sales_rep_id,
            sales_rep_name=self._get_employee_name(sales_rep_id),
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
            total_margin=total_margin,
            transaction_count=len(transactions),
            new_customer_count=sum(1 for t in transactions if t.is_new_customer),
            quota_target=quota_target,
            quota_achieved=total_revenue,
            achievement_rate=achievement_rate,
            total_commissions=total_commissions,
            commission_rate_effective=commission_rate
        )

    def get_leaderboard(
        self,
        period_start: date,
        period_end: date,
        metric: str = "revenue",
        limit: int = 10
    ) -> Leaderboard:
        """Recupere le classement des commerciaux."""
        # Recuperer tous les membres actifs
        members = self.team_repo.list_active()

        performances = []
        for member in members:
            perf = self.get_sales_rep_performance(
                member.employee_id,
                period_start,
                period_end
            )
            performances.append(perf)

        # Trier selon le metric
        metric_map = {
            "revenue": lambda p: p.total_revenue,
            "margin": lambda p: p.total_margin,
            "commissions": lambda p: p.total_commissions,
            "quota_achievement": lambda p: p.achievement_rate or Decimal("0"),
            "transactions": lambda p: p.transaction_count
        }

        sort_key = metric_map.get(metric, metric_map["revenue"])
        performances.sort(key=sort_key, reverse=True)

        # Ajouter les rangs et limiter
        for i, perf in enumerate(performances[:limit], 1):
            perf.rank = i

        return Leaderboard(
            period_start=period_start,
            period_end=period_end,
            metric=metric,
            entries=performances[:limit]
        )

    def get_dashboard(
        self,
        period_start: date,
        period_end: date
    ) -> CommissionDashboard:
        """Recupere le dashboard des commissions."""
        # Transactions
        transactions, txn_count = self.transaction_repo.list(
            filters=TransactionFilters(
                date_from=period_start,
                date_to=period_end
            ),
            page=1, page_size=10000
        )

        # Calculs
        calculations, calc_count = self.calculation_repo.list(
            filters=CalculationFilters(
                period_start=period_start,
                period_end=period_end
            ),
            page=1, page_size=10000
        )

        total_revenue = sum(t.revenue for t in transactions)
        total_commissions = sum(c.net_commission for c in calculations)

        # Par statut
        by_status = {}
        for c in calculations:
            by_status[c.status] = by_status.get(c.status, 0) + 1

        # Top performers
        leaderboard = self.get_leaderboard(period_start, period_end, "revenue", 5)

        # Plans actifs
        active_plans = self.plan_repo.get_active_plans(period_end)

        # Reps actifs
        members = self.team_repo.list_active()

        # Alertes
        pending_approvals = len(self.calculation_repo.get_pending_approval())
        pending_adjustments = len(self.adjustment_repo.get_pending_approval())

        return CommissionDashboard(
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
            total_commissions=total_commissions,
            total_pending=sum(
                c.net_commission for c in calculations
                if c.status in [
                    CommissionStatus.CALCULATED.value,
                    CommissionStatus.PENDING.value
                ]
            ),
            total_approved=sum(
                c.net_commission for c in calculations
                if c.status == CommissionStatus.APPROVED.value
            ),
            total_paid=sum(
                c.net_commission for c in calculations
                if c.status == CommissionStatus.PAID.value
            ),
            transaction_count=txn_count,
            calculation_count=calc_count,
            active_plans_count=len(active_plans),
            active_reps_count=len(members),
            top_performers=leaderboard.entries,
            by_status=by_status,
            pending_approvals=pending_approvals + pending_adjustments,
            disputed_calculations=by_status.get(
                CommissionStatus.DISPUTED.value, 0
            )
        )

    # =========================================================================
    # AUDIT
    # =========================================================================

    def _audit(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID,
        entity_code: str = None,
        old_values: Dict = None,
        new_values: Dict = None,
        metadata: Dict = None
    ):
        """Enregistre une entree d'audit."""
        try:
            self.audit_repo.create(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_code=entity_code,
                user_id=self.user_id or UUID("00000000-0000-0000-0000-000000000000"),
                old_values=old_values,
                new_values=new_values,
                extra_info=metadata
            )
        except Exception as e:
            logger.warning(f"Erreur audit: {e}")


# ============================================================================
# FACTORY
# ============================================================================

def create_commission_service(
    db: Session,
    tenant_id: str,
    user_id: UUID = None,
    payroll_callback: Callable = None
) -> CommissionService:
    """Factory pour creer un service de commissions."""
    return CommissionService(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        payroll_callback=payroll_callback
    )
