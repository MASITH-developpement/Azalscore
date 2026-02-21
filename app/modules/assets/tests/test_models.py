"""
Tests des modeles SQLAlchemy pour le module ASSETS.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.modules.assets.models import (
    AssetCategory,
    AssetInventory,
    AssetMaintenance,
    AssetMovement,
    AssetStatus,
    AssetTransfer,
    AssetType,
    DepreciationMethod,
    DepreciationSchedule,
    FixedAsset,
    MaintenanceStatus,
    MaintenanceType,
    MovementType,
)


@pytest.fixture
def db_session():
    """Creer une session de test en memoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def tenant_id():
    """Tenant ID de test."""
    return str(uuid.uuid4())


class TestAssetCategory:
    """Tests pour le modele AssetCategory."""

    def test_create_category(self, db_session, tenant_id):
        """Test creation d'une categorie."""
        category = AssetCategory(
            tenant_id=tenant_id,
            code="IT-EQUIP",
            name="Materiel Informatique",
            description="Ordinateurs, serveurs, etc.",
            default_asset_type=AssetType.TANGIBLE_IT,
            default_depreciation_method=DepreciationMethod.LINEAR,
            default_useful_life_years=3,
            default_asset_account="218300",
            default_depreciation_account="281830",
            default_expense_account="681120",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        assert category.id is not None
        assert category.code == "IT-EQUIP"
        assert category.default_useful_life_years == 3
        assert category.version == 1

    def test_category_hierarchy(self, db_session, tenant_id):
        """Test hierarchie des categories."""
        parent = AssetCategory(
            tenant_id=tenant_id,
            code="IMMO-CORP",
            name="Immobilisations Corporelles",
        )
        db_session.add(parent)
        db_session.commit()

        child = AssetCategory(
            tenant_id=tenant_id,
            code="IT-EQUIP",
            name="Materiel Informatique",
            parent_id=parent.id,
        )
        db_session.add(child)
        db_session.commit()

        assert child.parent_id == parent.id

    def test_soft_delete_category(self, db_session, tenant_id):
        """Test soft delete d'une categorie."""
        category = AssetCategory(
            tenant_id=tenant_id,
            code="TEST",
            name="Test Category",
        )
        db_session.add(category)
        db_session.commit()

        category.is_deleted = True
        category.deleted_at = datetime.utcnow()
        db_session.commit()

        assert category.is_deleted is True
        assert category.deleted_at is not None


class TestFixedAsset:
    """Tests pour le modele FixedAsset."""

    def test_create_asset(self, db_session, tenant_id):
        """Test creation d'une immobilisation."""
        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-2024-000001",
            name="MacBook Pro 16",
            description="Ordinateur portable pour developpeur",
            asset_type=AssetType.TANGIBLE_IT,
            status=AssetStatus.DRAFT,
            acquisition_date=date(2024, 1, 15),
            purchase_price=Decimal("2500.00"),
            acquisition_cost=Decimal("2500.00"),
            net_book_value=Decimal("2500.00"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=3,
            asset_account="218300",
            depreciation_account="281830",
            expense_account="681120",
        )
        db_session.add(asset)
        db_session.commit()

        assert asset.id is not None
        assert asset.asset_code == "IMM-2024-000001"
        assert asset.acquisition_cost == Decimal("2500.00")
        assert asset.status == AssetStatus.DRAFT

    def test_asset_with_category(self, db_session, tenant_id):
        """Test immobilisation avec categorie."""
        category = AssetCategory(
            tenant_id=tenant_id,
            code="IT",
            name="IT Equipment",
        )
        db_session.add(category)
        db_session.commit()

        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-001",
            name="Server",
            asset_type=AssetType.TANGIBLE_IT,
            category_id=category.id,
            acquisition_date=date.today(),
            purchase_price=Decimal("5000"),
            acquisition_cost=Decimal("5000"),
            net_book_value=Decimal("5000"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=5,
        )
        db_session.add(asset)
        db_session.commit()

        assert asset.category_id == category.id

    def test_asset_put_in_service(self, db_session, tenant_id):
        """Test mise en service d'un actif."""
        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-002",
            name="Printer",
            asset_type=AssetType.TANGIBLE_OFFICE,
            acquisition_date=date(2024, 1, 1),
            purchase_price=Decimal("800"),
            acquisition_cost=Decimal("800"),
            net_book_value=Decimal("800"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=5,
        )
        db_session.add(asset)
        db_session.commit()

        asset.status = AssetStatus.IN_SERVICE
        asset.in_service_date = date(2024, 1, 15)
        asset.depreciation_start_date = date(2024, 1, 15)
        db_session.commit()

        assert asset.status == AssetStatus.IN_SERVICE
        assert asset.in_service_date == date(2024, 1, 15)

    def test_asset_disposal(self, db_session, tenant_id):
        """Test cession d'un actif."""
        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-003",
            name="Old Computer",
            asset_type=AssetType.TANGIBLE_IT,
            acquisition_date=date(2020, 1, 1),
            in_service_date=date(2020, 1, 1),
            purchase_price=Decimal("1500"),
            acquisition_cost=Decimal("1500"),
            accumulated_depreciation=Decimal("1400"),
            net_book_value=Decimal("100"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=3,
            status=AssetStatus.FULLY_DEPRECIATED,
        )
        db_session.add(asset)
        db_session.commit()

        asset.status = AssetStatus.DISPOSED
        asset.disposal_date = date(2024, 6, 1)
        asset.disposal_proceeds = Decimal("50")
        asset.disposal_gain_loss = Decimal("-50")
        db_session.commit()

        assert asset.status == AssetStatus.DISPOSED
        assert asset.disposal_date == date(2024, 6, 1)

    def test_asset_components(self, db_session, tenant_id):
        """Test composants d'un actif."""
        parent = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-MACHINE",
            name="Machine Industrielle",
            asset_type=AssetType.TANGIBLE_INDUSTRIAL,
            acquisition_date=date.today(),
            purchase_price=Decimal("50000"),
            acquisition_cost=Decimal("50000"),
            net_book_value=Decimal("50000"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=10,
        )
        db_session.add(parent)
        db_session.commit()

        component = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-MACHINE-MOTOR",
            name="Moteur",
            asset_type=AssetType.TANGIBLE_INDUSTRIAL,
            parent_asset_id=parent.id,
            is_component=True,
            acquisition_date=date.today(),
            purchase_price=Decimal("5000"),
            acquisition_cost=Decimal("5000"),
            net_book_value=Decimal("5000"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=5,
        )
        db_session.add(component)
        db_session.commit()

        assert component.parent_asset_id == parent.id
        assert component.is_component is True


class TestDepreciationSchedule:
    """Tests pour le tableau d'amortissement."""

    def test_create_schedule_entry(self, db_session, tenant_id):
        """Test creation d'une ligne d'amortissement."""
        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-DEP",
            name="Test Asset",
            asset_type=AssetType.TANGIBLE_IT,
            acquisition_date=date(2024, 1, 1),
            purchase_price=Decimal("3000"),
            acquisition_cost=Decimal("3000"),
            net_book_value=Decimal("3000"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=3,
        )
        db_session.add(asset)
        db_session.commit()

        entry = DepreciationSchedule(
            tenant_id=tenant_id,
            asset_id=asset.id,
            period_number=1,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            fiscal_year=2024,
            opening_gross_value=Decimal("3000"),
            opening_accumulated_depreciation=Decimal("0"),
            opening_net_book_value=Decimal("3000"),
            depreciation_rate=Decimal("33.33"),
            depreciation_base=Decimal("3000"),
            depreciation_amount=Decimal("1000"),
            closing_accumulated_depreciation=Decimal("1000"),
            closing_net_book_value=Decimal("2000"),
        )
        db_session.add(entry)
        db_session.commit()

        assert entry.id is not None
        assert entry.depreciation_amount == Decimal("1000")
        assert entry.closing_net_book_value == Decimal("2000")


class TestAssetMaintenance:
    """Tests pour les maintenances."""

    def test_create_maintenance(self, db_session, tenant_id):
        """Test creation d'une maintenance."""
        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-MAINT",
            name="Test Asset",
            asset_type=AssetType.TANGIBLE_INDUSTRIAL,
            acquisition_date=date.today(),
            purchase_price=Decimal("10000"),
            acquisition_cost=Decimal("10000"),
            net_book_value=Decimal("10000"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=10,
        )
        db_session.add(asset)
        db_session.commit()

        maintenance = AssetMaintenance(
            tenant_id=tenant_id,
            asset_id=asset.id,
            maintenance_number="MAINT-2024-00001",
            maintenance_type=MaintenanceType.PREVENTIVE,
            status=MaintenanceStatus.PLANNED,
            title="Revision annuelle",
            scheduled_date=date(2024, 6, 1),
            labor_cost=Decimal("500"),
            parts_cost=Decimal("200"),
            total_cost=Decimal("700"),
        )
        db_session.add(maintenance)
        db_session.commit()

        assert maintenance.id is not None
        assert maintenance.maintenance_type == MaintenanceType.PREVENTIVE
        assert maintenance.total_cost == Decimal("700")


class TestAssetMovement:
    """Tests pour les mouvements."""

    def test_create_acquisition_movement(self, db_session, tenant_id):
        """Test mouvement d'acquisition."""
        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-MVT",
            name="Test Asset",
            asset_type=AssetType.TANGIBLE_IT,
            acquisition_date=date.today(),
            purchase_price=Decimal("2000"),
            acquisition_cost=Decimal("2000"),
            net_book_value=Decimal("2000"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=3,
        )
        db_session.add(asset)
        db_session.commit()

        movement = AssetMovement(
            tenant_id=tenant_id,
            asset_id=asset.id,
            movement_type=MovementType.ACQUISITION,
            movement_date=date.today(),
            movement_number="MVT-2024-00001",
            amount=Decimal("2000"),
            previous_value=Decimal("0"),
            new_value=Decimal("2000"),
            description="Acquisition initiale",
        )
        db_session.add(movement)
        db_session.commit()

        assert movement.id is not None
        assert movement.movement_type == MovementType.ACQUISITION


class TestAssetInventory:
    """Tests pour les inventaires."""

    def test_create_inventory(self, db_session, tenant_id):
        """Test creation d'un inventaire."""
        inventory = AssetInventory(
            tenant_id=tenant_id,
            inventory_number="INV-2024-0001",
            inventory_date=date.today(),
            description="Inventaire annuel",
            location_name="Siege social",
            assets_expected=50,
        )
        db_session.add(inventory)
        db_session.commit()

        assert inventory.id is not None
        assert inventory.inventory_number == "INV-2024-0001"


class TestAssetTransfer:
    """Tests pour les transferts."""

    def test_create_transfer(self, db_session, tenant_id):
        """Test creation d'un transfert."""
        asset = FixedAsset(
            tenant_id=tenant_id,
            asset_code="IMM-TRF",
            name="Test Asset",
            asset_type=AssetType.TANGIBLE_IT,
            acquisition_date=date.today(),
            site_name="Siege Paris",
            purchase_price=Decimal("1500"),
            acquisition_cost=Decimal("1500"),
            net_book_value=Decimal("1500"),
            depreciation_method=DepreciationMethod.LINEAR,
            useful_life_years=3,
        )
        db_session.add(asset)
        db_session.commit()

        transfer = AssetTransfer(
            tenant_id=tenant_id,
            asset_id=asset.id,
            transfer_number="TRF-2024-00001",
            transfer_date=date.today(),
            from_location_name="Siege Paris",
            to_location_name="Agence Lyon",
            reason="Reorganisation",
            status="PENDING",
        )
        db_session.add(transfer)
        db_session.commit()

        assert transfer.id is not None
        assert transfer.status == "PENDING"
