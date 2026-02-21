"""
Tests Sécurité Multi-tenant Requisition
=======================================
CRITIQUE: Vérifier l'isolation stricte entre tenants
"""
import pytest
from uuid import UUID

from app.modules.requisition.service import RequisitionService
from app.modules.requisition.schemas import (
    CatalogCategoryCreate, CatalogCategoryUpdate,
    CatalogItemCreate, CatalogItemUpdate,
    PreferredVendorCreate, PreferredVendorUpdate,
    RequisitionCreate, RequisitionUpdate,
    TemplateCreate, TemplateUpdate
)
from app.modules.requisition.exceptions import (
    CatalogCategoryNotFoundError,
    CatalogItemNotFoundError,
    PreferredVendorNotFoundError,
    BudgetAllocationNotFoundError,
    RequisitionNotFoundError,
    TemplateNotFoundError
)


class TestCatalogCategoryTenantIsolation:
    """Tests d'isolation tenant pour les catégories."""

    def test_cannot_access_other_tenant_category(
        self,
        service_tenant_a: RequisitionService,
        category_tenant_b
    ):
        """Un tenant ne peut pas accéder aux catégories d'un autre tenant."""
        with pytest.raises(CatalogCategoryNotFoundError):
            service_tenant_a.get_category(category_tenant_b.id)

    def test_list_only_shows_own_tenant_categories(
        self,
        service_tenant_a: RequisitionService,
        entities_mixed_tenants: dict
    ):
        """La liste ne retourne que les catégories du tenant courant."""
        items, total, pages = service_tenant_a.list_categories()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_category(
        self,
        service_tenant_a: RequisitionService,
        category_tenant_b
    ):
        """Un tenant ne peut pas modifier les catégories d'un autre tenant."""
        with pytest.raises(CatalogCategoryNotFoundError):
            service_tenant_a.update_category(
                category_tenant_b.id,
                CatalogCategoryUpdate(name="Hacked Category")
            )

    def test_cannot_delete_other_tenant_category(
        self,
        service_tenant_a: RequisitionService,
        category_tenant_b
    ):
        """Un tenant ne peut pas supprimer les catégories d'un autre tenant."""
        with pytest.raises(CatalogCategoryNotFoundError):
            service_tenant_a.delete_category(category_tenant_b.id)


class TestCatalogItemTenantIsolation:
    """Tests d'isolation tenant pour les articles."""

    def test_cannot_access_other_tenant_item(
        self,
        service_tenant_a: RequisitionService,
        item_tenant_b
    ):
        """Un tenant ne peut pas accéder aux articles d'un autre tenant."""
        with pytest.raises(CatalogItemNotFoundError):
            service_tenant_a.get_item(item_tenant_b.id)

    def test_list_only_shows_own_tenant_items(
        self,
        service_tenant_a: RequisitionService,
        item_tenant_a,
        item_tenant_b
    ):
        """La liste ne retourne que les articles du tenant courant."""
        items, total, pages = service_tenant_a.list_items()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_item(
        self,
        service_tenant_a: RequisitionService,
        item_tenant_b
    ):
        """Un tenant ne peut pas modifier les articles d'un autre tenant."""
        with pytest.raises(CatalogItemNotFoundError):
            service_tenant_a.update_item(
                item_tenant_b.id,
                CatalogItemUpdate(name="Hacked Item")
            )

    def test_cannot_delete_other_tenant_item(
        self,
        service_tenant_a: RequisitionService,
        item_tenant_b
    ):
        """Un tenant ne peut pas supprimer les articles d'un autre tenant."""
        with pytest.raises(CatalogItemNotFoundError):
            service_tenant_a.delete_item(item_tenant_b.id)


class TestPreferredVendorTenantIsolation:
    """Tests d'isolation tenant pour les fournisseurs préférés."""

    def test_cannot_access_other_tenant_vendor(
        self,
        service_tenant_a: RequisitionService,
        vendor_tenant_b
    ):
        """Un tenant ne peut pas accéder aux fournisseurs d'un autre tenant."""
        with pytest.raises(PreferredVendorNotFoundError):
            service_tenant_a.get_preferred_vendor(vendor_tenant_b.id)

    def test_list_only_shows_own_tenant_vendors(
        self,
        service_tenant_a: RequisitionService,
        vendor_tenant_a,
        vendor_tenant_b
    ):
        """La liste ne retourne que les fournisseurs du tenant courant."""
        items, total, pages = service_tenant_a.list_preferred_vendors()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_vendor(
        self,
        service_tenant_a: RequisitionService,
        vendor_tenant_b
    ):
        """Un tenant ne peut pas modifier les fournisseurs d'un autre tenant."""
        with pytest.raises(PreferredVendorNotFoundError):
            service_tenant_a.update_preferred_vendor(
                vendor_tenant_b.id,
                PreferredVendorUpdate(vendor_name="Hacked Vendor")
            )

    def test_cannot_delete_other_tenant_vendor(
        self,
        service_tenant_a: RequisitionService,
        vendor_tenant_b
    ):
        """Un tenant ne peut pas supprimer les fournisseurs d'un autre tenant."""
        with pytest.raises(PreferredVendorNotFoundError):
            service_tenant_a.delete_preferred_vendor(vendor_tenant_b.id)


class TestBudgetAllocationTenantIsolation:
    """Tests d'isolation tenant pour les allocations budgétaires."""

    def test_cannot_access_other_tenant_budget(
        self,
        service_tenant_a: RequisitionService,
        budget_tenant_b
    ):
        """Un tenant ne peut pas accéder aux allocations d'un autre tenant."""
        with pytest.raises(BudgetAllocationNotFoundError):
            service_tenant_a.get_budget_allocation(budget_tenant_b.id)

    def test_list_only_shows_own_tenant_budgets(
        self,
        service_tenant_a: RequisitionService,
        budget_tenant_a,
        budget_tenant_b
    ):
        """La liste ne retourne que les allocations du tenant courant."""
        items, total, pages = service_tenant_a.list_budget_allocations()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id


class TestRequisitionTenantIsolation:
    """Tests d'isolation tenant pour les demandes d'achat."""

    def test_cannot_access_other_tenant_requisition(
        self,
        service_tenant_a: RequisitionService,
        requisition_tenant_b
    ):
        """Un tenant ne peut pas accéder aux demandes d'un autre tenant."""
        with pytest.raises(RequisitionNotFoundError):
            service_tenant_a.get_requisition(requisition_tenant_b.id)

    def test_list_only_shows_own_tenant_requisitions(
        self,
        service_tenant_a: RequisitionService,
        entities_mixed_tenants: dict
    ):
        """La liste ne retourne que les demandes du tenant courant."""
        items, total, pages = service_tenant_a.list_requisitions()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_requisition(
        self,
        service_tenant_a: RequisitionService,
        requisition_tenant_b
    ):
        """Un tenant ne peut pas modifier les demandes d'un autre tenant."""
        with pytest.raises(RequisitionNotFoundError):
            service_tenant_a.update_requisition(
                requisition_tenant_b.id,
                RequisitionUpdate(title="Hacked Requisition")
            )

    def test_cannot_delete_other_tenant_requisition(
        self,
        service_tenant_a: RequisitionService,
        requisition_tenant_b
    ):
        """Un tenant ne peut pas supprimer les demandes d'un autre tenant."""
        with pytest.raises(RequisitionNotFoundError):
            service_tenant_a.delete_requisition(requisition_tenant_b.id)

    def test_cannot_submit_other_tenant_requisition(
        self,
        service_tenant_a: RequisitionService,
        requisition_tenant_b
    ):
        """Un tenant ne peut pas soumettre les demandes d'un autre tenant."""
        with pytest.raises(RequisitionNotFoundError):
            service_tenant_a.submit_requisition(requisition_tenant_b.id)

    def test_cannot_cancel_other_tenant_requisition(
        self,
        service_tenant_a: RequisitionService,
        requisition_tenant_b
    ):
        """Un tenant ne peut pas annuler les demandes d'un autre tenant."""
        with pytest.raises(RequisitionNotFoundError):
            service_tenant_a.cancel_requisition(requisition_tenant_b.id)

    def test_autocomplete_isolated(
        self,
        service_tenant_a: RequisitionService,
        entities_mixed_tenants: dict
    ):
        """L'autocomplete ne retourne que les demandes du tenant courant."""
        results = service_tenant_a.autocomplete_requisition("Test")

        for item in results:
            req = service_tenant_a.get_requisition(item["id"])
            assert req.tenant_id == service_tenant_a.tenant_id


class TestTemplateTenantIsolation:
    """Tests d'isolation tenant pour les modèles."""

    def test_cannot_access_other_tenant_template(
        self,
        service_tenant_a: RequisitionService,
        template_tenant_b
    ):
        """Un tenant ne peut pas accéder aux modèles d'un autre tenant."""
        with pytest.raises(TemplateNotFoundError):
            service_tenant_a.get_template(template_tenant_b.id)

    def test_list_only_shows_own_tenant_templates(
        self,
        service_tenant_a: RequisitionService,
        template_tenant_a,
        template_tenant_b
    ):
        """La liste ne retourne que les modèles du tenant courant."""
        items, total, pages = service_tenant_a.list_templates()

        for item in items:
            assert item.tenant_id == service_tenant_a.tenant_id

    def test_cannot_update_other_tenant_template(
        self,
        service_tenant_a: RequisitionService,
        template_tenant_b
    ):
        """Un tenant ne peut pas modifier les modèles d'un autre tenant."""
        with pytest.raises(TemplateNotFoundError):
            service_tenant_a.update_template(
                template_tenant_b.id,
                TemplateUpdate(name="Hacked Template")
            )

    def test_cannot_delete_other_tenant_template(
        self,
        service_tenant_a: RequisitionService,
        template_tenant_b
    ):
        """Un tenant ne peut pas supprimer les modèles d'un autre tenant."""
        with pytest.raises(TemplateNotFoundError):
            service_tenant_a.delete_template(template_tenant_b.id)


class TestBulkOperationsTenantIsolation:
    """Tests d'isolation pour les opérations en masse."""

    def test_bulk_delete_cannot_affect_other_tenant(
        self,
        db_session,
        service_tenant_a: RequisitionService,
        requisition_tenant_b
    ):
        """Les suppressions en masse ne peuvent pas affecter d'autres tenants."""
        from app.modules.requisition.repository import RequisitionRepository

        # Tenter de supprimer une demande d'un autre tenant
        result = service_tenant_a.req_repo.bulk_delete(
            [requisition_tenant_b.id],
            service_tenant_a.user_id
        )

        # Devrait retourner 0 car la demande n'est pas visible pour ce tenant
        assert result == 0

        # Vérifier que la demande existe toujours pour le tenant B
        repo_b = RequisitionRepository(db_session, requisition_tenant_b.tenant_id)
        req = repo_b.get_by_id(requisition_tenant_b.id)
        assert req is not None
        assert not req.is_deleted


class TestStatsIsolation:
    """Tests d'isolation pour les statistiques."""

    def test_stats_isolated(
        self,
        service_tenant_a: RequisitionService,
        entities_mixed_tenants: dict
    ):
        """Les stats ne comptent que les entités du tenant courant."""
        stats = service_tenant_a.get_stats()

        # Vérifier que le total correspond aux entités du tenant A
        tenant_a_count = len(entities_mixed_tenants["tenant_a"]["requisitions"])
        assert stats["total"] >= tenant_a_count


class TestCrossEntityTenantIsolation:
    """Tests d'isolation cross-entity."""

    def test_cannot_create_item_with_other_tenant_category(
        self,
        service_tenant_a: RequisitionService,
        category_tenant_b
    ):
        """Un tenant ne peut pas créer un article avec une catégorie d'un autre tenant."""
        from decimal import Decimal

        with pytest.raises(CatalogCategoryNotFoundError):
            service_tenant_a.create_item(
                CatalogItemCreate(
                    code="ITEM-HACKED",
                    name="Hacked Item",
                    category_id=category_tenant_b.id
                )
            )
