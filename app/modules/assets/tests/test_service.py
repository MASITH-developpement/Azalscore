"""
Tests du service pour le module ASSETS.
"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.modules.assets.exceptions import (
    AssetAlreadyDisposedError,
    AssetAlreadyInServiceError,
    AssetNotFoundError,
    CategoryCodeExistsError,
    CategoryNotFoundError,
    InServiceDateBeforeAcquisitionError,
)
from app.modules.assets.models import (
    AssetStatus,
    AssetType,
    DepreciationMethod,
    DisposalType,
    MaintenanceType,
)
from app.modules.assets.schemas import (
    AssetCategoryCreate,
    AssetMaintenanceCreate,
    DepreciationRunCreate,
    DisposeAssetRequest,
    FixedAssetCreate,
    PutInServiceRequest,
)
from app.modules.assets.service_db import AssetService


@pytest.fixture
def db_session():
    """Creer une session de test en memoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def tenant_id():
    """Tenant ID de test."""
    return uuid.uuid4()


@pytest.fixture
def user_id():
    """User ID de test."""
    return uuid.uuid4()


@pytest.fixture
def service(db_session, tenant_id, user_id):
    """Service Assets de test."""
    return AssetService(db_session, tenant_id, user_id)


class TestCategoryManagement:
    """Tests pour la gestion des categories."""

    def test_create_category(self, service):
        """Test creation d'une categorie."""
        data = AssetCategoryCreate(
            code="IT-EQUIP",
            name="Materiel Informatique",
            description="Ordinateurs et peripheriques",
            default_useful_life_years=3,
            default_asset_account="218300",
            default_depreciation_account="281830",
            default_expense_account="681120",
        )
        category = service.create_category(data)

        assert category.id is not None
        assert category.code == "IT-EQUIP"
        assert category.name == "Materiel Informatique"
        assert category.default_useful_life_years == 3

    def test_create_duplicate_category_code(self, service):
        """Test erreur code categorie duplique."""
        data = AssetCategoryCreate(code="DUP", name="Category 1")
        service.create_category(data)

        with pytest.raises(CategoryCodeExistsError):
            service.create_category(AssetCategoryCreate(code="DUP", name="Category 2"))

    def test_get_category(self, service):
        """Test recuperation d'une categorie."""
        data = AssetCategoryCreate(code="GET-TEST", name="Test Category")
        created = service.create_category(data)

        retrieved = service.get_category(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_categories(self, service):
        """Test liste des categories."""
        service.create_category(AssetCategoryCreate(code="CAT1", name="Category 1"))
        service.create_category(AssetCategoryCreate(code="CAT2", name="Category 2"))

        items, total = service.list_categories()
        assert total >= 2


class TestAssetManagement:
    """Tests pour la gestion des immobilisations."""

    def test_create_asset(self, service):
        """Test creation d'une immobilisation."""
        data = FixedAssetCreate(
            name="MacBook Pro 16",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("2500.00"),
            useful_life_years=3,
        )
        asset = service.create_asset(data)

        assert asset.id is not None
        assert asset.asset_code is not None
        assert asset.name == "MacBook Pro 16"
        assert asset.acquisition_cost == Decimal("2500.00")
        assert asset.status == AssetStatus.DRAFT

    def test_create_asset_with_costs(self, service):
        """Test creation avec couts additionnels."""
        data = FixedAssetCreate(
            name="Server Dell",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("5000.00"),
            transport_cost=Decimal("200.00"),
            installation_cost=Decimal("500.00"),
            useful_life_years=5,
        )
        asset = service.create_asset(data)

        assert asset.acquisition_cost == Decimal("5700.00")  # 5000 + 200 + 500

    def test_put_in_service(self, service):
        """Test mise en service."""
        asset = service.create_asset(FixedAssetCreate(
            name="Printer",
            asset_type="TANGIBLE_OFFICE",
            acquisition_date=date(2024, 1, 1),
            purchase_price=Decimal("800.00"),
            useful_life_years=5,
        ))

        data = PutInServiceRequest(
            in_service_date=date(2024, 1, 15),
            site_name="Siege Paris",
        )
        updated = service.put_in_service(asset.id, data)

        assert updated.status == AssetStatus.IN_SERVICE
        assert updated.in_service_date == date(2024, 1, 15)
        assert updated.depreciation_start_date == date(2024, 1, 15)

    def test_put_in_service_date_validation(self, service):
        """Test validation date mise en service."""
        asset = service.create_asset(FixedAssetCreate(
            name="Test",
            asset_type="TANGIBLE_IT",
            acquisition_date=date(2024, 3, 1),
            purchase_price=Decimal("1000"),
            useful_life_years=3,
        ))

        with pytest.raises(InServiceDateBeforeAcquisitionError):
            service.put_in_service(asset.id, PutInServiceRequest(
                in_service_date=date(2024, 1, 1)  # Avant acquisition
            ))

    def test_put_in_service_already_in_service(self, service):
        """Test erreur deja en service."""
        asset = service.create_asset(FixedAssetCreate(
            name="Test",
            asset_type="TANGIBLE_IT",
            acquisition_date=date(2024, 1, 1),
            purchase_price=Decimal("1000"),
            useful_life_years=3,
        ))
        service.put_in_service(asset.id, PutInServiceRequest(in_service_date=date(2024, 1, 15)))

        with pytest.raises(AssetAlreadyInServiceError):
            service.put_in_service(asset.id, PutInServiceRequest(in_service_date=date(2024, 2, 1)))

    def test_get_asset(self, service):
        """Test recuperation d'un actif."""
        created = service.create_asset(FixedAssetCreate(
            name="Test Asset",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("500"),
            useful_life_years=3,
        ))

        retrieved = service.get_asset(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_asset_not_found(self, service):
        """Test actif non trouve."""
        result = service.get_asset(uuid.uuid4())
        assert result is None

    def test_autocomplete(self, service):
        """Test autocomplete."""
        service.create_asset(FixedAssetCreate(
            name="MacBook Pro",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("2500"),
            useful_life_years=3,
        ))
        service.create_asset(FixedAssetCreate(
            name="Mac Mini",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("1000"),
            useful_life_years=3,
        ))

        results = service.autocomplete_assets("Mac", 10)
        assert len(results) >= 2


class TestDepreciation:
    """Tests pour les amortissements."""

    def test_depreciation_schedule_linear(self, service):
        """Test tableau amortissement lineaire."""
        asset = service.create_asset(FixedAssetCreate(
            name="Equipment",
            asset_type="TANGIBLE_IT",
            acquisition_date=date(2024, 1, 1),
            purchase_price=Decimal("3000"),
            depreciation_method="LINEAR",
            useful_life_years=3,
        ))
        service.put_in_service(asset.id, PutInServiceRequest(in_service_date=date(2024, 1, 1)))

        schedule = service.get_depreciation_schedule(asset.id)

        assert schedule is not None
        assert len(schedule["entries"]) > 0
        assert schedule["depreciation_method"] == DepreciationMethod.LINEAR

    def test_run_depreciation(self, service):
        """Test execution amortissements."""
        asset = service.create_asset(FixedAssetCreate(
            name="Computer",
            asset_type="TANGIBLE_IT",
            acquisition_date=date(2024, 1, 1),
            purchase_price=Decimal("3000"),
            useful_life_years=3,
        ))
        service.put_in_service(asset.id, PutInServiceRequest(in_service_date=date(2024, 1, 1)))

        run = service.run_depreciation(DepreciationRunCreate(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            fiscal_year=2024,
        ))

        assert run.id is not None
        assert run.assets_processed >= 1
        assert run.total_depreciation > 0


class TestDisposal:
    """Tests pour les cessions."""

    def test_dispose_asset(self, service):
        """Test cession d'un actif."""
        asset = service.create_asset(FixedAssetCreate(
            name="Old Computer",
            asset_type="TANGIBLE_IT",
            acquisition_date=date(2020, 1, 1),
            purchase_price=Decimal("1500"),
            useful_life_years=3,
        ))
        service.put_in_service(asset.id, PutInServiceRequest(in_service_date=date(2020, 1, 1)))

        # Simuler amortissement
        updated_asset = service.get_asset(asset.id)
        updated_asset.accumulated_depreciation = Decimal("1400")
        updated_asset.net_book_value = Decimal("100")
        updated_asset.status = AssetStatus.FULLY_DEPRECIATED
        service.db.commit()

        result = service.dispose_asset(asset.id, DisposeAssetRequest(
            disposal_date=date(2024, 6, 1),
            disposal_type=DisposalType.SALE,
            disposal_proceeds=Decimal("150"),
            disposal_costs=Decimal("0"),
            buyer_name="Acheteur Test",
        ))

        assert result["gain_loss"] == Decimal("50")  # 150 - 100

    def test_dispose_already_disposed(self, service):
        """Test erreur actif deja cede."""
        asset = service.create_asset(FixedAssetCreate(
            name="Test",
            asset_type="TANGIBLE_IT",
            acquisition_date=date(2020, 1, 1),
            purchase_price=Decimal("1000"),
            useful_life_years=3,
        ))
        service.put_in_service(asset.id, PutInServiceRequest(in_service_date=date(2020, 1, 1)))

        # Premiere cession
        a = service.get_asset(asset.id)
        a.accumulated_depreciation = Decimal("900")
        a.net_book_value = Decimal("100")
        service.db.commit()

        service.dispose_asset(asset.id, DisposeAssetRequest(
            disposal_date=date(2024, 1, 1),
            disposal_type=DisposalType.SCRAP,
        ))

        with pytest.raises(AssetAlreadyDisposedError):
            service.dispose_asset(asset.id, DisposeAssetRequest(
                disposal_date=date(2024, 2, 1),
                disposal_type=DisposalType.SALE,
            ))


class TestMaintenance:
    """Tests pour les maintenances."""

    def test_create_maintenance(self, service):
        """Test creation maintenance."""
        asset = service.create_asset(FixedAssetCreate(
            name="Machine",
            asset_type="TANGIBLE_INDUSTRIAL",
            acquisition_date=date.today(),
            purchase_price=Decimal("10000"),
            useful_life_years=10,
        ))

        maint = service.create_maintenance(asset.id, AssetMaintenanceCreate(
            maintenance_type=MaintenanceType.PREVENTIVE,
            title="Revision annuelle",
            scheduled_date=date.today() + timedelta(days=30),
            labor_cost=Decimal("500"),
            parts_cost=Decimal("200"),
        ))

        assert maint.id is not None
        assert maint.total_cost == Decimal("700")

    def test_list_maintenances(self, service):
        """Test liste des maintenances."""
        asset = service.create_asset(FixedAssetCreate(
            name="Machine",
            asset_type="TANGIBLE_INDUSTRIAL",
            acquisition_date=date.today(),
            purchase_price=Decimal("10000"),
            useful_life_years=10,
        ))

        service.create_maintenance(asset.id, AssetMaintenanceCreate(
            maintenance_type=MaintenanceType.PREVENTIVE,
            title="Maintenance 1",
            scheduled_date=date.today() + timedelta(days=30),
        ))

        items, total = service.list_maintenances(asset_id=asset.id)
        assert total >= 1


class TestStatistics:
    """Tests pour les statistiques."""

    def test_get_statistics(self, service):
        """Test statistiques."""
        service.create_asset(FixedAssetCreate(
            name="Asset 1",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("1000"),
            useful_life_years=3,
        ))
        service.create_asset(FixedAssetCreate(
            name="Asset 2",
            asset_type="TANGIBLE_OFFICE",
            acquisition_date=date.today(),
            purchase_price=Decimal("500"),
            useful_life_years=5,
        ))

        stats = service.get_statistics()

        assert stats["total_assets"] >= 2
        assert stats["total_gross_value"] >= Decimal("1500")

    def test_get_dashboard(self, service):
        """Test dashboard."""
        service.create_asset(FixedAssetCreate(
            name="Test Asset",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("1000"),
            useful_life_years=3,
        ))

        dashboard = service.get_dashboard()

        assert "statistics" in dashboard
        assert "recent_acquisitions" in dashboard
        assert "upcoming_maintenances" in dashboard

    def test_get_valuation(self, service):
        """Test valorisation."""
        asset = service.create_asset(FixedAssetCreate(
            name="Test Asset",
            asset_type="TANGIBLE_IT",
            acquisition_date=date.today(),
            purchase_price=Decimal("1000"),
            useful_life_years=3,
        ))
        service.put_in_service(asset.id, PutInServiceRequest(in_service_date=date.today()))

        valuation = service.get_valuation()

        assert valuation["total_assets_count"] >= 1
        assert valuation["total_gross_value"] >= Decimal("1000")
