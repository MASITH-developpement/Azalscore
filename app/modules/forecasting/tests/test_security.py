"""
Tests Sécurité Multi-tenant - Module Forecasting

CRITIQUE: Vérifier l'isolation entre tenants.
"""
import pytest
from uuid import uuid4, UUID

from ..repository import ForecastRepository, BudgetRepository, KPIRepository
from ..exceptions import ForecastNotFoundError


class TestForecastTenantIsolation:
    """Tests d'isolation tenant pour Forecast - CRITIQUES."""

    def test_cannot_access_other_tenant_forecast(
        self,
        db_session,
        tenant_a_id,
        tenant_b_id,
        forecast_tenant_b
    ):
        """Un tenant ne peut pas voir les prévisions d'un autre tenant."""
        repo_a = ForecastRepository(db_session, tenant_a_id)

        # Tenter d'accéder à la prévision du tenant B
        result = repo_a.get_by_id(forecast_tenant_b.id)

        assert result is None

    def test_list_only_shows_own_tenant_forecasts(
        self,
        db_session,
        tenant_a_id,
        forecasts_mixed_tenants
    ):
        """List ne retourne que les prévisions du tenant courant."""
        repo = ForecastRepository(db_session, tenant_a_id)
        items, total = repo.list()

        # Vérifier que tous appartiennent au tenant A
        for item in items:
            assert item.tenant_id == tenant_a_id

        # Le tenant A a 3 prévisions (pas les 2 du tenant B)
        assert total == 3

    def test_cannot_update_other_tenant_forecast(
        self,
        db_session,
        tenant_a_id,
        forecast_tenant_b
    ):
        """Un tenant ne peut pas modifier les prévisions d'un autre tenant."""
        repo_a = ForecastRepository(db_session, tenant_a_id)

        # La prévision n'est pas trouvée car filtrée par tenant
        entity = repo_a.get_by_id(forecast_tenant_b.id)
        assert entity is None

    def test_cannot_delete_other_tenant_forecast(
        self,
        db_session,
        tenant_a_id,
        forecast_tenant_b
    ):
        """Un tenant ne peut pas supprimer les prévisions d'un autre tenant."""
        repo_a = ForecastRepository(db_session, tenant_a_id)

        # La prévision n'est pas trouvée
        entity = repo_a.get_by_id(forecast_tenant_b.id)
        assert entity is None

    def test_autocomplete_isolated(
        self,
        db_session,
        tenant_a_id,
        forecasts_mixed_tenants
    ):
        """Autocomplete ne retourne que les prévisions du tenant courant."""
        repo_a = ForecastRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("Forecast")

        # Vérifier que seuls les forecasts A sont retournés
        for item in results:
            entity = repo_a.get_by_id(UUID(item["id"]))
            assert entity is not None
            assert entity.tenant_id == tenant_a_id

    def test_code_uniqueness_per_tenant(
        self,
        db_session,
        tenant_a_id,
        tenant_b_id,
        forecast_tenant_a
    ):
        """Le code est unique par tenant, pas globalement."""
        repo_b = ForecastRepository(db_session, tenant_b_id)

        # Le même code peut exister pour un autre tenant
        assert not repo_b.code_exists(forecast_tenant_a.code)

    def test_bulk_operations_isolated(
        self,
        db_session,
        tenant_a_id,
        forecast_tenant_b,
        user_id
    ):
        """Les opérations bulk ne peuvent pas affecter d'autres tenants."""
        repo_a = ForecastRepository(db_session, tenant_a_id)

        # Tenter de supprimer une prévision d'un autre tenant
        result = repo_a.bulk_delete([forecast_tenant_b.id], user_id)

        # Aucune suppression car le forecast n'appartient pas au tenant A
        assert result == 0

        # Vérifier que le forecast B existe toujours
        repo_b = ForecastRepository(db_session, forecast_tenant_b.tenant_id)
        entity = repo_b.get_by_id(forecast_tenant_b.id)
        assert entity is not None


class TestBudgetTenantIsolation:
    """Tests d'isolation tenant pour Budget."""

    def test_cannot_access_other_tenant_budget(
        self,
        db_session,
        tenant_a_id,
        budget_tenant_b
    ):
        """Un tenant ne peut pas voir les budgets d'un autre tenant."""
        repo_a = BudgetRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(budget_tenant_b.id)
        assert result is None

    def test_list_only_shows_own_tenant_budgets(
        self,
        db_session,
        tenant_a_id,
        budget_tenant_a,
        budget_tenant_b
    ):
        """List ne retourne que les budgets du tenant courant."""
        repo_a = BudgetRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        for item in items:
            assert item.tenant_id == tenant_a_id

        assert total == 1  # Seulement le budget A


class TestKPITenantIsolation:
    """Tests d'isolation tenant pour KPI."""

    def test_cannot_access_other_tenant_kpi(
        self,
        db_session,
        tenant_a_id,
        kpi_tenant_b
    ):
        """Un tenant ne peut pas voir les KPIs d'un autre tenant."""
        repo_a = KPIRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(kpi_tenant_b.id)
        assert result is None

    def test_dashboard_only_shows_own_tenant_kpis(
        self,
        db_session,
        tenant_a_id,
        kpi_tenant_a,
        kpi_tenant_b
    ):
        """Le dashboard KPI ne montre que les KPIs du tenant courant."""
        repo_a = KPIRepository(db_session, tenant_a_id)
        dashboard = repo_a.get_dashboard_data()

        assert dashboard["total_kpis"] == 1
        # Vérifier que le KPI B n'est pas inclus
        for cat_kpis in dashboard["by_category"].values():
            for kpi in cat_kpis:
                assert kpi["code"] != kpi_tenant_b.code


class TestSoftDeleteIsolation:
    """Tests d'isolation avec soft delete."""

    def test_soft_deleted_not_visible(
        self,
        db_session,
        tenant_a_id,
        forecast_tenant_a,
        user_id
    ):
        """Les prévisions soft deleted ne sont pas visibles."""
        repo = ForecastRepository(db_session, tenant_a_id)

        # Soft delete
        repo.soft_delete(forecast_tenant_a, user_id)

        # Plus visible
        result = repo.get_by_id(forecast_tenant_a.id)
        assert result is None

    def test_soft_deleted_visible_with_flag(
        self,
        db_session,
        tenant_a_id,
        forecast_tenant_a,
        user_id
    ):
        """Les prévisions soft deleted sont visibles avec include_deleted."""
        repo = ForecastRepository(db_session, tenant_a_id)
        repo.soft_delete(forecast_tenant_a, user_id)

        # Visible avec include_deleted
        repo_all = ForecastRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_all.get_by_id(forecast_tenant_a.id)

        assert result is not None
        assert result.is_deleted is True

    def test_restore_forecast(
        self,
        db_session,
        tenant_a_id,
        forecast_tenant_a,
        user_id
    ):
        """Restauration d'une prévision supprimée."""
        repo = ForecastRepository(db_session, tenant_a_id, include_deleted=True)

        # Soft delete puis restore
        repo.soft_delete(forecast_tenant_a, user_id)
        restored = repo.restore(forecast_tenant_a)

        assert restored.is_deleted is False
        assert restored.deleted_at is None
        assert restored.deleted_by is None
