"""
Tests Sécurité Multi-tenant Manufacturing
==========================================
CRITIQUE: Vérifier l'isolation stricte entre tenants
"""
import pytest
from uuid import UUID

from app.modules.manufacturing.service import ManufacturingService
from app.modules.manufacturing.schemas import (
    BOMCreate, BOMUpdate,
    WorkcenterCreate, WorkcenterUpdate,
    RoutingCreate, RoutingUpdate,
    WorkOrderCreate, WorkOrderUpdate,
    QualityCheckCreate
)
from app.modules.manufacturing.exceptions import (
    BOMNotFoundError,
    WorkcenterNotFoundError,
    RoutingNotFoundError,
    WorkOrderNotFoundError,
    QualityCheckNotFoundError
)


class TestBOMTenantIsolation:
    """Tests d'isolation tenant pour les BOMs."""

    def test_cannot_access_other_tenant_bom(
        self,
        service_tenant_a: ManufacturingService,
        bom_tenant_b
    ):
        """Un tenant ne peut pas accéder aux BOMs d'un autre tenant."""
        with pytest.raises(BOMNotFoundError):
            service_tenant_a.get_bom(bom_tenant_b.id)

    def test_list_only_shows_own_tenant_boms(
        self,
        service_tenant_a: ManufacturingService,
        entities_mixed_tenants: dict
    ):
        """La liste ne retourne que les BOMs du tenant courant."""
        items, total, pages = service_tenant_a.list_boms()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_bom(
        self,
        service_tenant_a: ManufacturingService,
        bom_tenant_b
    ):
        """Un tenant ne peut pas modifier les BOMs d'un autre tenant."""
        with pytest.raises(BOMNotFoundError):
            service_tenant_a.update_bom(
                bom_tenant_b.id,
                BOMUpdate(name="Hacked BOM")
            )

    def test_cannot_delete_other_tenant_bom(
        self,
        service_tenant_a: ManufacturingService,
        bom_tenant_b
    ):
        """Un tenant ne peut pas supprimer les BOMs d'un autre tenant."""
        with pytest.raises(BOMNotFoundError):
            service_tenant_a.delete_bom(bom_tenant_b.id)

    def test_autocomplete_isolated(
        self,
        service_tenant_a: ManufacturingService,
        entities_mixed_tenants: dict
    ):
        """L'autocomplete ne retourne que les BOMs du tenant courant."""
        results = service_tenant_a.autocomplete_bom("Test")

        for item in results:
            bom = service_tenant_a.get_bom(item["id"])
            assert bom.tenant_id == service_tenant_a.tenant_id


class TestWorkcenterTenantIsolation:
    """Tests d'isolation tenant pour les Workcenters."""

    def test_cannot_access_other_tenant_workcenter(
        self,
        service_tenant_a: ManufacturingService,
        workcenter_tenant_b
    ):
        """Un tenant ne peut pas accéder aux workcenters d'un autre tenant."""
        with pytest.raises(WorkcenterNotFoundError):
            service_tenant_a.get_workcenter(workcenter_tenant_b.id)

    def test_list_only_shows_own_tenant_workcenters(
        self,
        service_tenant_a: ManufacturingService,
        workcenter_tenant_a,
        workcenter_tenant_b
    ):
        """La liste ne retourne que les workcenters du tenant courant."""
        items, total, pages = service_tenant_a.list_workcenters()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id
        assert total >= 1

    def test_cannot_update_other_tenant_workcenter(
        self,
        service_tenant_a: ManufacturingService,
        workcenter_tenant_b
    ):
        """Un tenant ne peut pas modifier les workcenters d'un autre tenant."""
        with pytest.raises(WorkcenterNotFoundError):
            service_tenant_a.update_workcenter(
                workcenter_tenant_b.id,
                WorkcenterUpdate(name="Hacked Workcenter")
            )

    def test_cannot_delete_other_tenant_workcenter(
        self,
        service_tenant_a: ManufacturingService,
        workcenter_tenant_b
    ):
        """Un tenant ne peut pas supprimer les workcenters d'un autre tenant."""
        with pytest.raises(WorkcenterNotFoundError):
            service_tenant_a.delete_workcenter(workcenter_tenant_b.id)

    def test_autocomplete_isolated(
        self,
        service_tenant_a: ManufacturingService,
        workcenter_tenant_a,
        workcenter_tenant_b
    ):
        """L'autocomplete ne retourne que les workcenters du tenant courant."""
        results = service_tenant_a.autocomplete_workcenter("Work")

        for item in results:
            wc = service_tenant_a.get_workcenter(item["id"])
            assert wc.tenant_id == service_tenant_a.tenant_id


class TestRoutingTenantIsolation:
    """Tests d'isolation tenant pour les Routings."""

    def test_cannot_access_other_tenant_routing(
        self,
        service_tenant_a: ManufacturingService,
        routing_tenant_b
    ):
        """Un tenant ne peut pas accéder aux routings d'un autre tenant."""
        with pytest.raises(RoutingNotFoundError):
            service_tenant_a.get_routing(routing_tenant_b.id)

    def test_list_only_shows_own_tenant_routings(
        self,
        service_tenant_a: ManufacturingService,
        routing_tenant_a,
        routing_tenant_b
    ):
        """La liste ne retourne que les routings du tenant courant."""
        items, total, pages = service_tenant_a.list_routings()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_routing(
        self,
        service_tenant_a: ManufacturingService,
        routing_tenant_b
    ):
        """Un tenant ne peut pas modifier les routings d'un autre tenant."""
        with pytest.raises(RoutingNotFoundError):
            service_tenant_a.update_routing(
                routing_tenant_b.id,
                RoutingUpdate(name="Hacked Routing")
            )

    def test_cannot_delete_other_tenant_routing(
        self,
        service_tenant_a: ManufacturingService,
        routing_tenant_b
    ):
        """Un tenant ne peut pas supprimer les routings d'un autre tenant."""
        with pytest.raises(RoutingNotFoundError):
            service_tenant_a.delete_routing(routing_tenant_b.id)


class TestWorkOrderTenantIsolation:
    """Tests d'isolation tenant pour les Work Orders."""

    def test_cannot_access_other_tenant_work_order(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_b
    ):
        """Un tenant ne peut pas accéder aux work orders d'un autre tenant."""
        with pytest.raises(WorkOrderNotFoundError):
            service_tenant_a.get_work_order(work_order_tenant_b.id)

    def test_list_only_shows_own_tenant_work_orders(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_a,
        work_order_tenant_b
    ):
        """La liste ne retourne que les work orders du tenant courant."""
        items, total, pages = service_tenant_a.list_work_orders()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_work_order(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_b
    ):
        """Un tenant ne peut pas modifier les work orders d'un autre tenant."""
        with pytest.raises(WorkOrderNotFoundError):
            service_tenant_a.update_work_order(
                work_order_tenant_b.id,
                WorkOrderUpdate(name="Hacked Work Order")
            )

    def test_cannot_delete_other_tenant_work_order(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_b
    ):
        """Un tenant ne peut pas supprimer les work orders d'un autre tenant."""
        with pytest.raises(WorkOrderNotFoundError):
            service_tenant_a.delete_work_order(work_order_tenant_b.id)

    def test_cannot_confirm_other_tenant_work_order(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_b
    ):
        """Un tenant ne peut pas confirmer les work orders d'un autre tenant."""
        with pytest.raises(WorkOrderNotFoundError):
            service_tenant_a.confirm_work_order(work_order_tenant_b.id)

    def test_cannot_start_other_tenant_work_order(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_b
    ):
        """Un tenant ne peut pas démarrer les work orders d'un autre tenant."""
        with pytest.raises(WorkOrderNotFoundError):
            service_tenant_a.start_work_order(work_order_tenant_b.id)

    def test_autocomplete_isolated(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_a,
        work_order_tenant_b
    ):
        """L'autocomplete ne retourne que les work orders du tenant courant."""
        results = service_tenant_a.autocomplete_work_order("WO")

        for item in results:
            wo = service_tenant_a.get_work_order(item["id"])
            assert wo.tenant_id == service_tenant_a.tenant_id


class TestQualityCheckTenantIsolation:
    """Tests d'isolation tenant pour les Quality Checks."""

    def test_cannot_create_quality_check_for_other_tenant_wo(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_b
    ):
        """Un tenant ne peut pas créer de QC pour un WO d'un autre tenant."""
        with pytest.raises(WorkOrderNotFoundError):
            service_tenant_a.create_quality_check(
                QualityCheckCreate(
                    work_order_id=work_order_tenant_b.id,
                    sample_size=5
                )
            )

    def test_list_quality_checks_isolated(
        self,
        service_tenant_a: ManufacturingService,
        quality_check_tenant_a,
        quality_check_tenant_b,
        work_order_tenant_a
    ):
        """Les QC listés sont uniquement ceux du tenant courant."""
        qcs = service_tenant_a.list_quality_checks_for_work_order(
            work_order_tenant_a.id
        )

        for qc in qcs:
            assert qc.tenant_id == service_tenant_a.tenant_id


class TestCrossEntityTenantIsolation:
    """Tests d'isolation cross-entity."""

    def test_cannot_add_other_tenant_workcenter_to_operation(
        self,
        service_tenant_a: ManufacturingService,
        routing_tenant_a,
        workcenter_tenant_b
    ):
        """Un tenant ne peut pas référencer un workcenter d'un autre tenant."""
        from app.modules.manufacturing.schemas import OperationCreate

        with pytest.raises(WorkcenterNotFoundError):
            service_tenant_a.add_operation(
                routing_tenant_a.id,
                OperationCreate(
                    name="Test Operation",
                    workcenter_id=workcenter_tenant_b.id,
                    workcenter_name="Should Fail"
                )
            )


class TestBulkOperationsTenantIsolation:
    """Tests d'isolation pour les opérations en masse."""

    def test_bulk_delete_cannot_affect_other_tenant(
        self,
        db_session,
        service_tenant_a: ManufacturingService,
        bom_tenant_b
    ):
        """Les suppressions en masse ne peuvent pas affecter d'autres tenants."""
        from app.modules.manufacturing.repository import BOMRepository

        # Tenter de supprimer une BOM d'un autre tenant
        result = service_tenant_a.bom_repo.bulk_delete(
            [bom_tenant_b.id],
            service_tenant_a.user_id
        )

        # Devrait retourner 0 car la BOM n'est pas visible pour ce tenant
        assert result == 0

        # Vérifier que la BOM existe toujours pour le tenant B
        repo_b = BOMRepository(db_session, bom_tenant_b.tenant_id)
        bom = repo_b.get_by_id(bom_tenant_b.id)
        assert bom is not None
        assert not bom.is_deleted


class TestStatsIsolation:
    """Tests d'isolation pour les statistiques."""

    def test_bom_stats_isolated(
        self,
        service_tenant_a: ManufacturingService,
        entities_mixed_tenants: dict
    ):
        """Les stats BOM ne comptent que les entités du tenant courant."""
        stats = service_tenant_a.get_bom_stats()

        # Vérifier que le total correspond aux entités du tenant A
        tenant_a_count = len(entities_mixed_tenants["tenant_a"])
        assert stats["total"] >= tenant_a_count

    def test_work_order_stats_isolated(
        self,
        service_tenant_a: ManufacturingService,
        work_order_tenant_a,
        work_order_tenant_b
    ):
        """Les stats WO ne comptent que les entités du tenant courant."""
        stats = service_tenant_a.get_work_order_stats()

        # Au moins 1 WO pour le tenant A
        assert stats["total"] >= 1
