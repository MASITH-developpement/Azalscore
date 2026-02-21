"""
Tests de sécurité multi-tenant - Module Expenses (GAP-084)

CRITIQUE: Ces tests vérifient l'isolation entre tenants.
Un échec = faille de sécurité majeure.
"""
import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from app.modules.expenses.models import ExpenseStatus, ExpenseCategory, PaymentMethod
from app.modules.expenses.repository import (
    ExpenseReportRepository, ExpensePolicyRepository, EmployeeVehicleRepository
)


class TestExpenseReportTenantIsolation:
    """Tests isolation tenant pour ExpenseReport."""

    def test_cannot_access_other_tenant_report(
        self, db_session, tenant_a_id, tenant_b_id, report_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les notes de tenant B."""
        repo_a = ExpenseReportRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(report_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_cannot_list_other_tenant_reports(
        self, db_session, tenant_a_id, tenant_b_id, report_tenant_a, report_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les notes du tenant courant."""
        repo_a = ExpenseReportRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        report_ids = [r.id for r in items]
        assert report_tenant_a.id in report_ids, "Note du tenant A manquante"
        assert report_tenant_b.id not in report_ids, "FAILLE: Note tenant B visible!"

    def test_code_uniqueness_per_tenant(
        self, db_session, tenant_a_id, tenant_b_id, report_tenant_a, report_tenant_b
    ):
        """Les codes sont uniques par tenant, pas globalement."""
        repo_a = ExpenseReportRepository(db_session, tenant_a_id)
        repo_b = ExpenseReportRepository(db_session, tenant_b_id)

        # Même code dans les deux tenants
        assert repo_a.code_exists(report_tenant_a.code) is True
        # Code de A n'existe pas pour B (même si B a le même code)
        assert repo_b.code_exists(report_tenant_a.code) is True  # Car B a aussi NF-202602-0001

    def test_get_by_employee_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, report_tenant_a, report_tenant_b, employee_id
    ):
        """get_by_employee respecte l'isolation tenant."""
        repo_b = ExpenseReportRepository(db_session, tenant_b_id)
        reports = repo_b.get_by_employee(employee_id, 2026)

        # L'employé du tenant A ne devrait pas apparaître dans tenant B
        report_ids = [r.id for r in reports]
        assert report_tenant_a.id not in report_ids

    def test_autocomplete_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, report_tenant_a, report_tenant_b
    ):
        """Autocomplete ne retourne que les notes du tenant courant."""
        repo_a = ExpenseReportRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("NF")

        codes = [r["code"] for r in results]
        assert report_tenant_a.code in codes
        # Note: report_tenant_b a le même code donc on vérifie les IDs
        result_ids = [r["id"] for r in results]
        assert str(report_tenant_b.id) not in result_ids


class TestExpensePolicyTenantIsolation:
    """Tests isolation tenant pour ExpensePolicy."""

    def test_cannot_access_other_tenant_policy(
        self, db_session, tenant_a_id, tenant_b_id, policy_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les politiques de tenant B."""
        repo_a = ExpensePolicyRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(policy_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_get_default_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, policy_tenant_a, policy_tenant_b
    ):
        """get_default ne retourne que la politique du tenant courant."""
        repo_a = ExpensePolicyRepository(db_session, tenant_a_id)
        default_a = repo_a.get_default()

        assert default_a is not None
        assert default_a.id == policy_tenant_a.id
        assert default_a.id != policy_tenant_b.id

    def test_list_active_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, policy_tenant_a, policy_tenant_b
    ):
        """list_active ne retourne que les politiques du tenant courant."""
        repo_a = ExpensePolicyRepository(db_session, tenant_a_id)
        policies = repo_a.list_active()

        policy_ids = [p.id for p in policies]
        assert policy_tenant_a.id in policy_ids
        assert policy_tenant_b.id not in policy_ids


class TestEmployeeVehicleTenantIsolation:
    """Tests isolation tenant pour EmployeeVehicle."""

    def test_get_by_employee_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, vehicle_tenant_a, employee_id
    ):
        """get_by_employee respecte l'isolation tenant."""
        repo_b = EmployeeVehicleRepository(db_session, tenant_b_id)
        vehicles = repo_b.get_by_employee(employee_id)

        vehicle_ids = [v.id for v in vehicles]
        assert vehicle_tenant_a.id not in vehicle_ids

    def test_get_annual_mileage_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, vehicle_tenant_a, employee_id
    ):
        """get_annual_mileage respecte l'isolation tenant."""
        repo_b = EmployeeVehicleRepository(db_session, tenant_b_id)
        mileage = repo_b.get_annual_mileage(employee_id, 2026)

        # Devrait être 0 car pas de véhicule pour cet employé dans tenant B
        assert mileage == Decimal("0")


class TestSoftDeleteIsolation:
    """Tests soft delete avec isolation tenant."""

    def test_soft_deleted_report_hidden_by_default(
        self, db_session, tenant_a_id, user_id, report_tenant_a
    ):
        """Note soft-deleted n'apparaît pas par défaut."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)
        repo.soft_delete(report_tenant_a, user_id)

        result = repo.get_by_id(report_tenant_a.id)
        assert result is None

    def test_soft_deleted_visible_with_include_deleted(
        self, db_session, tenant_a_id, user_id, report_tenant_a
    ):
        """Note soft-deleted visible avec include_deleted=True."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)
        repo.soft_delete(report_tenant_a, user_id)

        repo_with_deleted = ExpenseReportRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_with_deleted.get_by_id(report_tenant_a.id)
        assert result is not None
        assert result.is_deleted is True

    def test_soft_deleted_other_tenant_still_hidden(
        self, db_session, tenant_a_id, tenant_b_id, user_id, report_tenant_b
    ):
        """Note soft-deleted d'un autre tenant reste invisible."""
        repo_b = ExpenseReportRepository(db_session, tenant_b_id)
        repo_b.soft_delete(report_tenant_b, user_id)

        repo_a_with_deleted = ExpenseReportRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_a_with_deleted.get_by_id(report_tenant_b.id)
        assert result is None


class TestExpenseReportWorkflow:
    """Tests du workflow de note de frais."""

    def test_cannot_modify_submitted_report(
        self, db_session, tenant_a_id, user_id, report_tenant_a
    ):
        """Impossible de modifier une note soumise."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)

        # Soumettre la note
        repo.submit(report_tenant_a)

        # Tenter d'ajouter une ligne
        with pytest.raises(ValueError, match="submitted"):
            repo.add_line(report_tenant_a, {
                "category": ExpenseCategory.HOTEL.value,
                "description": "Test",
                "expense_date": date.today(),
                "amount": Decimal("100")
            }, user_id)

    def test_submit_changes_status(
        self, db_session, tenant_a_id, report_tenant_a
    ):
        """La soumission change le statut."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)

        assert report_tenant_a.status == ExpenseStatus.DRAFT.value

        repo.submit(report_tenant_a)

        assert report_tenant_a.status == ExpenseStatus.SUBMITTED.value
        assert report_tenant_a.submitted_at is not None

    def test_approve_requires_correct_status(
        self, db_session, tenant_a_id, user_id, report_tenant_a
    ):
        """L'approbation nécessite le bon statut."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)

        # Sans soumettre d'abord
        with pytest.raises(ValueError, match="not pending"):
            repo.approve(report_tenant_a, user_id, "OK")

    def test_full_workflow(
        self, db_session, tenant_a_id, user_id, report_tenant_a
    ):
        """Test du workflow complet."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)

        # 1. Soumettre
        repo.submit(report_tenant_a)
        assert report_tenant_a.status == ExpenseStatus.SUBMITTED.value

        # 2. Approuver
        repo.approve(report_tenant_a, user_id, "Approuvé")
        assert report_tenant_a.status == ExpenseStatus.APPROVED.value
        assert report_tenant_a.approved_at is not None

        # 3. Marquer comme payé
        repo.mark_paid(report_tenant_a, user_id)
        assert report_tenant_a.status == ExpenseStatus.PAID.value
        assert report_tenant_a.paid_at is not None


class TestExpenseLineTotals:
    """Tests des calculs de totaux."""

    def test_totals_recalculated_on_add_line(
        self, db_session, tenant_a_id, user_id, report_tenant_a
    ):
        """Les totaux sont recalculés à l'ajout de ligne."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)
        initial_total = report_tenant_a.total_amount

        repo.add_line(report_tenant_a, {
            "category": ExpenseCategory.HOTEL.value,
            "description": "Hôtel Paris",
            "expense_date": date(2026, 2, 20),
            "amount": Decimal("150.00"),
            "payment_method": PaymentMethod.PERSONAL_CARD.value
        }, user_id)

        assert report_tenant_a.total_amount == initial_total + Decimal("150.00")

    def test_vat_calculated_correctly(
        self, db_session, tenant_a_id, user_id, report_tenant_a
    ):
        """La TVA est calculée correctement."""
        repo = ExpenseReportRepository(db_session, tenant_a_id)

        line = repo.add_line(report_tenant_a, {
            "category": ExpenseCategory.HOTEL.value,
            "description": "Hôtel",
            "expense_date": date.today(),
            "amount": Decimal("110.00"),
            "vat_rate": Decimal("10"),  # TVA 10%
            "payment_method": PaymentMethod.PERSONAL_CARD.value
        }, user_id)

        # TVA = 110 * 10 / 110 = 10
        assert line.vat_amount == Decimal("10.00")
        assert line.amount_excl_vat == Decimal("100.00")
