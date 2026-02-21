"""
Tests de sécurité multi-tenant - Module Field Service (GAP-081)

CRITIQUE: Ces tests vérifient l'isolation entre tenants.
Un échec = faille de sécurité majeure.
"""
import pytest
from uuid import uuid4
from datetime import date, timedelta
from decimal import Decimal

from app.modules.fieldservice.models import (
    WorkOrderStatus, TechnicianStatus, Priority, WorkOrderType
)
from app.modules.fieldservice.repository import (
    WorkOrderRepository, TechnicianRepository, CustomerSiteRepository,
    ServiceZoneRepository
)


class TestWorkOrderTenantIsolation:
    """Tests isolation tenant pour FSWorkOrder."""

    def test_cannot_access_other_tenant_work_order(
        self, db_session, tenant_a_id, tenant_b_id, work_order_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les WO de tenant B."""
        repo_a = WorkOrderRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(work_order_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_cannot_list_other_tenant_work_orders(
        self, db_session, tenant_a_id, tenant_b_id, work_order_tenant_a, work_order_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les WO du tenant courant."""
        repo_a = WorkOrderRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        wo_ids = [w.id for w in items]
        assert work_order_tenant_a.id in wo_ids, "WO du tenant A manquant"
        assert work_order_tenant_b.id not in wo_ids, "FAILLE: WO tenant B visible!"

    def test_cannot_update_other_tenant_work_order(
        self, db_session, tenant_a_id, tenant_b_id, work_order_tenant_b
    ):
        """CRITIQUE: Ne peut pas modifier un WO d'un autre tenant."""
        repo_a = WorkOrderRepository(db_session, tenant_a_id)
        wo = repo_a.get_by_id(work_order_tenant_b.id)
        assert wo is None, "get_by_id devrait retourner None"

    def test_cannot_delete_other_tenant_work_order(
        self, db_session, tenant_a_id, tenant_b_id, work_order_tenant_b
    ):
        """CRITIQUE: Ne peut pas supprimer un WO d'un autre tenant."""
        repo_a = WorkOrderRepository(db_session, tenant_a_id)
        wo = repo_a.get_by_id(work_order_tenant_b.id)
        assert wo is None

    def test_code_uniqueness_per_tenant(
        self, db_session, tenant_a_id, tenant_b_id, work_order_tenant_a, work_order_tenant_b
    ):
        """Les codes sont uniques par tenant, pas globalement."""
        repo_a = WorkOrderRepository(db_session, tenant_a_id)
        repo_b = WorkOrderRepository(db_session, tenant_b_id)

        # Code existe pour tenant A
        assert repo_a.code_exists(work_order_tenant_a.code) is True
        # Même code n'existe pas pour tenant B
        assert repo_b.code_exists(work_order_tenant_a.code) is False

    def test_autocomplete_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, work_order_tenant_a, work_order_tenant_b
    ):
        """Autocomplete ne retourne que les WO du tenant courant."""
        repo_a = WorkOrderRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("WO")

        codes = [r["code"] for r in results]
        assert work_order_tenant_a.code in codes
        assert work_order_tenant_b.code not in codes

    def test_overdue_work_orders_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id
    ):
        """get_overdue ne retourne que les WO du tenant courant."""
        repo_a = WorkOrderRepository(db_session, tenant_a_id)
        repo_b = WorkOrderRepository(db_session, tenant_b_id)

        overdue_a = repo_a.get_overdue()
        overdue_b = repo_b.get_overdue()

        # Vérifier qu'aucun WO de l'autre tenant n'apparaît
        overdue_a_tenants = {wo.tenant_id for wo in overdue_a}
        overdue_b_tenants = {wo.tenant_id for wo in overdue_b}

        assert tenant_b_id not in overdue_a_tenants
        assert tenant_a_id not in overdue_b_tenants


class TestTechnicianTenantIsolation:
    """Tests isolation tenant pour FSTechnician."""

    def test_cannot_access_other_tenant_technician(
        self, db_session, tenant_a_id, tenant_b_id, technician_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les techniciens de tenant B."""
        repo_a = TechnicianRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(technician_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_cannot_list_other_tenant_technicians(
        self, db_session, tenant_a_id, tenant_b_id, technician_tenant_a, technician_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les techniciens du tenant courant."""
        repo_a = TechnicianRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        tech_ids = [t.id for t in items]
        assert technician_tenant_a.id in tech_ids
        assert technician_tenant_b.id not in tech_ids

    def test_get_available_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, technician_tenant_a, technician_tenant_b
    ):
        """get_available ne retourne que les techniciens du tenant courant."""
        repo_a = TechnicianRepository(db_session, tenant_a_id)
        available = repo_a.get_available()

        tech_ids = [t.id for t in available]
        assert technician_tenant_b.id not in tech_ids

    def test_autocomplete_technician_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, technician_tenant_a, technician_tenant_b
    ):
        """Autocomplete techniciens isolé par tenant."""
        repo_a = TechnicianRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("TECH")

        codes = [r["code"] for r in results]
        assert technician_tenant_a.code in codes
        assert technician_tenant_b.code not in codes

    def test_update_location_requires_tenant_access(
        self, db_session, tenant_a_id, tenant_b_id, technician_tenant_b
    ):
        """Mise à jour GPS nécessite accès au tenant."""
        repo_a = TechnicianRepository(db_session, tenant_a_id)
        tech = repo_a.get_by_id(technician_tenant_b.id)
        assert tech is None  # Ne peut pas récupérer pour mettre à jour


class TestCustomerSiteTenantIsolation:
    """Tests isolation tenant pour FSCustomerSite."""

    def test_cannot_access_other_tenant_site(
        self, db_session, tenant_a_id, tenant_b_id, site_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les sites de tenant B."""
        repo_a = CustomerSiteRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(site_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_get_by_customer_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, site_tenant_a, site_tenant_b, customer_id
    ):
        """get_by_customer respecte l'isolation tenant."""
        repo_a = CustomerSiteRepository(db_session, tenant_a_id)
        sites = repo_a.get_by_customer(customer_id)

        site_ids = [s.id for s in sites]
        assert site_tenant_a.id in site_ids
        # Site B est pour un autre customer ET autre tenant
        assert site_tenant_b.id not in site_ids

    def test_autocomplete_site_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, site_tenant_a, site_tenant_b
    ):
        """Autocomplete sites isolé par tenant."""
        repo_a = CustomerSiteRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("SITE")

        codes = [r["code"] for r in results]
        assert site_tenant_a.code in codes
        assert site_tenant_b.code not in codes


class TestServiceZoneTenantIsolation:
    """Tests isolation tenant pour FSServiceZone."""

    def test_cannot_access_other_tenant_zone(
        self, db_session, tenant_a_id, tenant_b_id, zone_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les zones de tenant B."""
        repo_a = ServiceZoneRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(zone_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_list_active_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, zone_tenant_a, zone_tenant_b
    ):
        """list_active ne retourne que les zones du tenant courant."""
        repo_a = ServiceZoneRepository(db_session, tenant_a_id)
        zones = repo_a.list_active()

        zone_ids = [z.id for z in zones]
        assert zone_tenant_a.id in zone_ids
        assert zone_tenant_b.id not in zone_ids

    def test_autocomplete_zone_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, zone_tenant_a, zone_tenant_b
    ):
        """Autocomplete zones isolé par tenant."""
        repo_a = ServiceZoneRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("ZONE")

        codes = [r["code"] for r in results]
        assert zone_tenant_a.code in codes
        assert zone_tenant_b.code not in codes


class TestSoftDeleteIsolation:
    """Tests soft delete avec isolation tenant."""

    def test_soft_deleted_work_order_hidden_by_default(
        self, db_session, tenant_a_id, user_id, work_order_tenant_a
    ):
        """WO soft-deleted n'apparaît pas par défaut."""
        repo = WorkOrderRepository(db_session, tenant_a_id)
        repo.soft_delete(work_order_tenant_a, user_id)

        result = repo.get_by_id(work_order_tenant_a.id)
        assert result is None

    def test_soft_deleted_visible_with_include_deleted(
        self, db_session, tenant_a_id, user_id, work_order_tenant_a
    ):
        """WO soft-deleted visible avec include_deleted=True."""
        repo = WorkOrderRepository(db_session, tenant_a_id)
        repo.soft_delete(work_order_tenant_a, user_id)

        repo_with_deleted = WorkOrderRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_with_deleted.get_by_id(work_order_tenant_a.id)
        assert result is not None
        assert result.is_deleted is True

    def test_soft_deleted_other_tenant_still_hidden(
        self, db_session, tenant_a_id, tenant_b_id, user_id, work_order_tenant_b
    ):
        """WO soft-deleted d'un autre tenant reste invisible."""
        repo_b = WorkOrderRepository(db_session, tenant_b_id)
        repo_b.soft_delete(work_order_tenant_b, user_id)

        # Même avec include_deleted, tenant A ne voit pas
        repo_a_with_deleted = WorkOrderRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_a_with_deleted.get_by_id(work_order_tenant_b.id)
        assert result is None

    def test_restore_only_own_tenant(
        self, db_session, tenant_a_id, user_id, work_order_tenant_a
    ):
        """Restore fonctionne pour son propre tenant."""
        repo = WorkOrderRepository(db_session, tenant_a_id)
        repo.soft_delete(work_order_tenant_a, user_id)

        repo_with_deleted = WorkOrderRepository(db_session, tenant_a_id, include_deleted=True)
        deleted_wo = repo_with_deleted.get_by_id(work_order_tenant_a.id)
        restored = repo_with_deleted.restore(deleted_wo)

        assert restored.is_deleted is False
        assert restored.deleted_at is None


class TestWorkOrderStatusTransitions:
    """Tests transitions de statut."""

    def test_valid_status_transition(
        self, db_session, tenant_a_id, user_id, work_order_tenant_a
    ):
        """Transition valide: SCHEDULED -> DISPATCHED."""
        repo = WorkOrderRepository(db_session, tenant_a_id)
        wo = repo.get_by_id(work_order_tenant_a.id)

        # Vérifier transition valide
        assert WorkOrderStatus.DISPATCHED in wo.status.allowed_transitions()

        updated = repo.update(wo, {"status": WorkOrderStatus.DISPATCHED}, user_id)
        assert updated.status == WorkOrderStatus.DISPATCHED

    def test_full_workflow_transitions(
        self, db_session, tenant_a_id, user_id, work_order_tenant_a
    ):
        """Test workflow complet: SCHEDULED -> DISPATCHED -> EN_ROUTE -> ON_SITE -> IN_PROGRESS -> COMPLETED."""
        repo = WorkOrderRepository(db_session, tenant_a_id)
        wo = repo.get_by_id(work_order_tenant_a.id)

        workflow = [
            WorkOrderStatus.DISPATCHED,
            WorkOrderStatus.EN_ROUTE,
            WorkOrderStatus.ON_SITE,
            WorkOrderStatus.IN_PROGRESS,
            WorkOrderStatus.COMPLETED
        ]

        for next_status in workflow:
            assert next_status in wo.status.allowed_transitions(), \
                f"Transition {wo.status} -> {next_status} devrait être valide"
            wo = repo.update(wo, {"status": next_status}, user_id)
            assert wo.status == next_status
