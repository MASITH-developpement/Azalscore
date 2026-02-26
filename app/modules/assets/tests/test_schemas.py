"""
Tests des schemas Pydantic pour le module ASSETS.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.assets.schemas import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetFilters,
    AssetInventoryCreate,
    AssetMaintenanceCreate,
    DepreciationRunCreate,
    DisposeAssetRequest,
    FixedAssetCreate,
    FixedAssetUpdate,
    PutInServiceRequest,
)


class TestAssetCategorySchemas:
    """Tests pour les schemas de categories."""

    def test_category_create_valid(self):
        """Test creation valide."""
        data = AssetCategoryCreate(
            code="IT-EQUIP",
            name="Materiel Informatique",
            description="Ordinateurs et peripheriques",
            default_useful_life_years=3,
        )
        assert data.code == "IT-EQUIP"
        assert data.default_useful_life_years == 3

    def test_category_create_code_required(self):
        """Test code obligatoire."""
        with pytest.raises(ValidationError):
            AssetCategoryCreate(name="Test")

    def test_category_create_name_min_length(self):
        """Test longueur minimale du nom."""
        with pytest.raises(ValidationError):
            AssetCategoryCreate(code="TEST", name="A")

    def test_category_update_partial(self):
        """Test mise a jour partielle."""
        data = AssetCategoryUpdate(name="New Name")
        assert data.name == "New Name"
        assert data.description is None


class TestFixedAssetSchemas:
    """Tests pour les schemas d'immobilisations."""

    def test_asset_create_valid(self):
        """Test creation valide."""
        data = FixedAssetCreate(
            name="MacBook Pro 16",
            asset_type="TANGIBLE_IT",
            acquisition_date=date(2024, 1, 15),
            purchase_price=Decimal("2500.00"),
            useful_life_years=3,
        )
        assert data.name == "MacBook Pro 16"
        assert data.purchase_price == Decimal("2500.00")
        assert data.useful_life_years == 3

    def test_asset_create_with_costs(self):
        """Test creation avec couts."""
        data = FixedAssetCreate(
            name="Server",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("5000"),
            transport_cost=Decimal("200"),
            installation_cost=Decimal("500"),
            useful_life_years=5,
        )
        assert data.transport_cost == Decimal("200")
        assert data.installation_cost == Decimal("500")

    def test_asset_create_with_location(self):
        """Test creation avec localisation."""
        data = FixedAssetCreate(
            name="Printer",
            asset_type="TANGIBLE_OFFICE",
            acquisition_date=date.today(),
            purchase_price=Decimal("800"),
            useful_life_years=5,
            site_name="Siege Paris",
            building="Batiment A",
            floor="3eme etage",
            room="Bureau 301",
        )
        assert data.site_name == "Siege Paris"
        assert data.room == "Bureau 301"

    def test_asset_create_name_required(self):
        """Test nom obligatoire."""
        with pytest.raises(ValidationError):
            FixedAssetCreate(
                asset_type="TANGIBLE_IT",
                acquisition_date=date.today(),
                purchase_price=Decimal("1000"),
                useful_life_years=3,
            )

    def test_asset_update_partial(self):
        """Test mise a jour partielle."""
        data = FixedAssetUpdate(
            description="Updated description",
            notes="New notes",
        )
        assert data.description == "Updated description"
        assert data.name is None

    def test_asset_update_condition_rating(self):
        """Test notation d'etat."""
        data = FixedAssetUpdate(condition_rating=4)
        assert data.condition_rating == 4

        with pytest.raises(ValidationError):
            FixedAssetUpdate(condition_rating=6)  # > 5

        with pytest.raises(ValidationError):
            FixedAssetUpdate(condition_rating=0)  # < 1


class TestPutInServiceSchema:
    """Tests pour le schema de mise en service."""

    def test_put_in_service_valid(self):
        """Test mise en service valide."""
        data = PutInServiceRequest(
            in_service_date=date(2024, 1, 15),
            site_name="Paris",
            responsible_name="Jean Dupont",
        )
        assert data.in_service_date == date(2024, 1, 15)
        assert data.site_name == "Paris"

    def test_put_in_service_date_required(self):
        """Test date obligatoire."""
        with pytest.raises(ValidationError):
            PutInServiceRequest(site_name="Paris")


class TestDisposeAssetSchema:
    """Tests pour le schema de cession."""

    def test_dispose_valid(self):
        """Test cession valide."""
        data = DisposeAssetRequest(
            disposal_date=date(2024, 6, 1),
            disposal_type="SALE",
            disposal_proceeds=Decimal("500"),
            buyer_name="Acheteur SA",
        )
        assert data.disposal_type == "SALE"
        assert data.disposal_proceeds == Decimal("500")

    def test_dispose_scrap(self):
        """Test mise au rebut."""
        data = DisposeAssetRequest(
            disposal_date=date(2024, 6, 1),
            disposal_type="SCRAP",
        )
        assert data.disposal_type == "SCRAP"
        assert data.disposal_proceeds == Decimal("0")


class TestMaintenanceSchemas:
    """Tests pour les schemas de maintenance."""

    def test_maintenance_create_valid(self):
        """Test creation maintenance valide."""
        data = AssetMaintenanceCreate(
            maintenance_type="PREVENTIVE",
            title="Revision annuelle",
            scheduled_date=date(2024, 6, 1),
            labor_cost=Decimal("500"),
            parts_cost=Decimal("200"),
        )
        assert data.maintenance_type == "PREVENTIVE"
        assert data.labor_cost == Decimal("500")

    def test_maintenance_title_min_length(self):
        """Test longueur minimale du titre."""
        with pytest.raises(ValidationError):
            AssetMaintenanceCreate(
                maintenance_type="PREVENTIVE",
                title="Test",  # < 5 caracteres
                scheduled_date=date.today(),
            )


class TestDepreciationSchemas:
    """Tests pour les schemas d'amortissement."""

    def test_depreciation_run_create(self):
        """Test creation execution amortissement."""
        data = DepreciationRunCreate(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            fiscal_year=2024,
        )
        assert data.period_start == date(2024, 1, 1)
        assert data.fiscal_year == 2024


class TestInventorySchemas:
    """Tests pour les schemas d'inventaire."""

    def test_inventory_create_valid(self):
        """Test creation inventaire valide."""
        data = AssetInventoryCreate(
            inventory_date=date.today(),
            description="Inventaire annuel",
            location_name="Siege Paris",
        )
        assert data.inventory_date == date.today()
        assert data.location_name == "Siege Paris"


class TestAssetFilters:
    """Tests pour les filtres."""

    def test_filters_empty(self):
        """Test filtres vides."""
        data = AssetFilters()
        assert data.search is None
        assert data.status is None

    def test_filters_with_values(self):
        """Test filtres avec valeurs."""
        data = AssetFilters(
            search="MacBook",
            status=["IN_SERVICE", "FULLY_DEPRECIATED"],
            acquisition_date_from=date(2024, 1, 1),
            min_value=Decimal("1000"),
        )
        assert data.search == "MacBook"
        assert len(data.status) == 2
        assert data.min_value == Decimal("1000")

    def test_filters_tags(self):
        """Test filtres par tags."""
        data = AssetFilters(tags=["urgent", "priority"])
        assert len(data.tags) == 2
