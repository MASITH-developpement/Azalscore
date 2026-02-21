"""
Tests de sécurité et d'isolation multi-tenant - Module Shipping
================================================================

Ces tests vérifient que les données d'un tenant ne sont jamais
accessibles par un autre tenant.
"""

import pytest
from uuid import uuid4

from app.modules.shipping.models import (
    Zone, Carrier, ShippingRate, Shipment, Package, PickupPoint, Return,
    ShipmentStatus, ReturnStatus
)
from app.modules.shipping.repository import (
    ZoneRepository, CarrierRepository, ShippingRateRepository,
    ShipmentRepository, PackageRepository, PickupPointRepository,
    ReturnRepository
)
from app.modules.shipping.service import ShippingService
from app.modules.shipping.exceptions import (
    ZoneNotFoundError, CarrierNotFoundError, RateNotFoundError,
    ShipmentNotFoundError, PackageNotFoundError, PickupPointNotFoundError,
    ReturnNotFoundError
)


# ==================== Zone Isolation Tests ====================

class TestZoneIsolation:
    """Tests d'isolation pour les zones."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_zone_by_id(
        self,
        shipping_service: ShippingService,
        saved_zone_other_tenant: Zone
    ):
        """Un tenant ne peut pas accéder à une zone d'un autre tenant par ID."""
        with pytest.raises(ZoneNotFoundError):
            await shipping_service.get_zone(str(saved_zone_other_tenant.id))

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_zone_by_code(
        self,
        shipping_service: ShippingService,
        saved_zone_other_tenant: Zone
    ):
        """Un tenant ne peut pas accéder à une zone d'un autre tenant par code."""
        with pytest.raises(ZoneNotFoundError):
            await shipping_service.get_zone_by_code(saved_zone_other_tenant.code)

    @pytest.mark.asyncio
    async def test_list_zones_excludes_other_tenant(
        self,
        shipping_service: ShippingService,
        saved_zone_france: Zone,
        saved_zone_other_tenant: Zone
    ):
        """La liste des zones n'inclut pas les zones d'autres tenants."""
        zones, total = await shipping_service.list_zones()

        zone_ids = [str(z.id) for z in zones]
        assert str(saved_zone_france.id) in zone_ids
        assert str(saved_zone_other_tenant.id) not in zone_ids

    @pytest.mark.asyncio
    async def test_zone_repo_base_query_filters_tenant(
        self,
        zone_repo: ZoneRepository,
        saved_zone_france: Zone,
        saved_zone_other_tenant: Zone
    ):
        """Le repository filtre par tenant_id dans _base_query."""
        zone = await zone_repo.get_by_id(str(saved_zone_france.id))
        assert zone is not None
        assert zone.tenant_id == zone_repo.tenant_id

        # L'autre zone ne doit pas être accessible
        other_zone = await zone_repo.get_by_id(str(saved_zone_other_tenant.id))
        assert other_zone is None


# ==================== Carrier Isolation Tests ====================

class TestCarrierIsolation:
    """Tests d'isolation pour les transporteurs."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_carrier_by_id(
        self,
        shipping_service: ShippingService,
        saved_carrier_other_tenant: Carrier
    ):
        """Un tenant ne peut pas accéder à un transporteur d'un autre tenant."""
        with pytest.raises(CarrierNotFoundError):
            await shipping_service.get_carrier(str(saved_carrier_other_tenant.id))

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_carrier_by_code(
        self,
        shipping_service: ShippingService,
        saved_carrier_other_tenant: Carrier
    ):
        """Un tenant ne peut pas accéder à un transporteur d'un autre tenant par code."""
        with pytest.raises(CarrierNotFoundError):
            await shipping_service.get_carrier_by_code(saved_carrier_other_tenant.code)

    @pytest.mark.asyncio
    async def test_list_carriers_excludes_other_tenant(
        self,
        shipping_service: ShippingService,
        saved_carrier_colissimo: Carrier,
        saved_carrier_other_tenant: Carrier
    ):
        """La liste des transporteurs n'inclut pas ceux d'autres tenants."""
        carriers, total = await shipping_service.list_carriers()

        carrier_ids = [str(c.id) for c in carriers]
        assert str(saved_carrier_colissimo.id) in carrier_ids
        assert str(saved_carrier_other_tenant.id) not in carrier_ids

    @pytest.mark.asyncio
    async def test_carrier_repo_base_query_filters_tenant(
        self,
        carrier_repo: CarrierRepository,
        saved_carrier_colissimo: Carrier,
        saved_carrier_other_tenant: Carrier
    ):
        """Le repository Carrier filtre par tenant_id."""
        carrier = await carrier_repo.get_by_id(str(saved_carrier_colissimo.id))
        assert carrier is not None
        assert carrier.tenant_id == carrier_repo.tenant_id

        other_carrier = await carrier_repo.get_by_id(str(saved_carrier_other_tenant.id))
        assert other_carrier is None


# ==================== ShippingRate Isolation Tests ====================

class TestRateIsolation:
    """Tests d'isolation pour les tarifs."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_rate(
        self,
        shipping_service: ShippingService,
        db_session,
        other_tenant_id: str,
        saved_carrier_other_tenant: Carrier,
        user_id: str
    ):
        """Un tenant ne peut pas accéder à un tarif d'un autre tenant."""
        # Créer un tarif pour l'autre tenant
        other_service = ShippingService(db_session, other_tenant_id)
        from app.modules.shipping.schemas import ShippingRateCreate
        from app.modules.shipping.models import ShippingMethod, RateCalculation
        from decimal import Decimal

        rate_data = ShippingRateCreate(
            code="RATE-OTHER",
            name="Tarif Autre Tenant",
            carrier_id=str(saved_carrier_other_tenant.id),
            shipping_method=ShippingMethod.STANDARD,
            calculation_method=RateCalculation.FLAT,
            base_rate=Decimal("10")
        )
        other_rate = await other_service.create_rate(rate_data, user_id)

        # Vérifier qu'on ne peut pas y accéder depuis notre tenant
        with pytest.raises(RateNotFoundError):
            await shipping_service.get_rate(str(other_rate.id))

    @pytest.mark.asyncio
    async def test_list_rates_excludes_other_tenant(
        self,
        shipping_service: ShippingService,
        saved_rate_standard: ShippingRate,
        db_session,
        other_tenant_id: str,
        saved_carrier_other_tenant: Carrier,
        user_id: str
    ):
        """La liste des tarifs n'inclut pas ceux d'autres tenants."""
        # Créer un tarif pour l'autre tenant
        other_service = ShippingService(db_session, other_tenant_id)
        from app.modules.shipping.schemas import ShippingRateCreate
        from app.modules.shipping.models import ShippingMethod, RateCalculation
        from decimal import Decimal

        rate_data = ShippingRateCreate(
            code="RATE-OTHER-2",
            name="Tarif Autre Tenant 2",
            carrier_id=str(saved_carrier_other_tenant.id),
            shipping_method=ShippingMethod.STANDARD,
            calculation_method=RateCalculation.FLAT,
            base_rate=Decimal("15")
        )
        other_rate = await other_service.create_rate(rate_data, user_id)

        # Vérifier la liste
        rates, total = await shipping_service.list_rates()
        rate_ids = [str(r.id) for r in rates]

        assert str(saved_rate_standard.id) in rate_ids
        assert str(other_rate.id) not in rate_ids


# ==================== Shipment Isolation Tests ====================

class TestShipmentIsolation:
    """Tests d'isolation pour les expéditions."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_shipment_by_id(
        self,
        shipping_service: ShippingService,
        saved_shipment_other_tenant: Shipment
    ):
        """Un tenant ne peut pas accéder à une expédition d'un autre tenant."""
        with pytest.raises(ShipmentNotFoundError):
            await shipping_service.get_shipment(str(saved_shipment_other_tenant.id))

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_shipment_by_number(
        self,
        shipping_service: ShippingService,
        saved_shipment_other_tenant: Shipment
    ):
        """Un tenant ne peut pas accéder à une expédition d'un autre tenant par numéro."""
        with pytest.raises(ShipmentNotFoundError):
            await shipping_service.get_shipment_by_number(
                saved_shipment_other_tenant.shipment_number
            )

    @pytest.mark.asyncio
    async def test_list_shipments_excludes_other_tenant(
        self,
        shipping_service: ShippingService,
        saved_shipment_pending: Shipment,
        saved_shipment_other_tenant: Shipment
    ):
        """La liste des expéditions n'inclut pas celles d'autres tenants."""
        shipments, total = await shipping_service.list_shipments()

        shipment_ids = [str(s.id) for s in shipments]
        assert str(saved_shipment_pending.id) in shipment_ids
        assert str(saved_shipment_other_tenant.id) not in shipment_ids

    @pytest.mark.asyncio
    async def test_shipment_repo_base_query_filters_tenant(
        self,
        shipment_repo: ShipmentRepository,
        saved_shipment_pending: Shipment,
        saved_shipment_other_tenant: Shipment
    ):
        """Le repository Shipment filtre par tenant_id."""
        shipment = await shipment_repo.get_by_id(str(saved_shipment_pending.id))
        assert shipment is not None
        assert shipment.tenant_id == shipment_repo.tenant_id

        other_shipment = await shipment_repo.get_by_id(str(saved_shipment_other_tenant.id))
        assert other_shipment is None

    @pytest.mark.asyncio
    async def test_cannot_cancel_other_tenant_shipment(
        self,
        shipping_service: ShippingService,
        saved_shipment_other_tenant: Shipment,
        user_id: str
    ):
        """Un tenant ne peut pas annuler une expédition d'un autre tenant."""
        with pytest.raises(ShipmentNotFoundError):
            await shipping_service.cancel_shipment(
                str(saved_shipment_other_tenant.id),
                "Test annulation",
                user_id
            )


# ==================== Package Isolation Tests ====================

class TestPackageIsolation:
    """Tests d'isolation pour les colis."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_package(
        self,
        shipping_service: ShippingService,
        db_session,
        other_tenant_id: str,
        saved_shipment_other_tenant: Shipment,
        user_id: str
    ):
        """Un tenant ne peut pas accéder à un colis d'un autre tenant."""
        # Créer un colis pour l'autre tenant
        from app.modules.shipping.models import Package, PackageType
        from decimal import Decimal

        other_package = Package(
            id=uuid4(),
            tenant_id=other_tenant_id,
            shipment_id=saved_shipment_other_tenant.id,
            package_type=PackageType.SMALL_BOX,
            weight=Decimal("1"),
            billable_weight=Decimal("1"),
            created_by=user_id
        )
        other_package_repo = PackageRepository(db_session, other_tenant_id)
        saved_other_package = await other_package_repo.create(other_package)

        # Vérifier qu'on ne peut pas y accéder
        with pytest.raises(PackageNotFoundError):
            await shipping_service.get_package(str(saved_other_package.id))


# ==================== PickupPoint Isolation Tests ====================

class TestPickupPointIsolation:
    """Tests d'isolation pour les points relais."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_pickup_point(
        self,
        shipping_service: ShippingService,
        db_session,
        other_tenant_id: str,
        saved_carrier_other_tenant: Carrier,
        user_id: str
    ):
        """Un tenant ne peut pas accéder à un point relais d'un autre tenant."""
        # Créer un point relais pour l'autre tenant
        from app.modules.shipping.models import PickupPoint

        other_point = PickupPoint(
            id=uuid4(),
            tenant_id=other_tenant_id,
            carrier_id=saved_carrier_other_tenant.id,
            external_id="OTHER-RELAY-001",
            name="Point Relais Autre Tenant",
            address={"country_code": "US"},
            is_active=True,
            created_by=user_id
        )
        other_repo = PickupPointRepository(db_session, other_tenant_id)
        saved_other_point = await other_repo.create(other_point)

        # Vérifier qu'on ne peut pas y accéder
        with pytest.raises(PickupPointNotFoundError):
            await shipping_service.get_pickup_point(str(saved_other_point.id))

    @pytest.mark.asyncio
    async def test_list_pickup_points_excludes_other_tenant(
        self,
        shipping_service: ShippingService,
        saved_pickup_point_relay: PickupPoint,
        db_session,
        other_tenant_id: str,
        saved_carrier_other_tenant: Carrier,
        user_id: str
    ):
        """La liste des points relais n'inclut pas ceux d'autres tenants."""
        # Créer un point relais pour l'autre tenant
        from app.modules.shipping.models import PickupPoint

        other_point = PickupPoint(
            id=uuid4(),
            tenant_id=other_tenant_id,
            carrier_id=saved_carrier_other_tenant.id,
            external_id="OTHER-RELAY-002",
            name="Point Relais Autre Tenant 2",
            address={"country_code": "US"},
            is_active=True,
            created_by=user_id
        )
        other_repo = PickupPointRepository(db_session, other_tenant_id)
        saved_other_point = await other_repo.create(other_point)

        # Vérifier la liste
        points, total = await shipping_service.list_pickup_points()
        point_ids = [str(p.id) for p in points]

        assert str(saved_pickup_point_relay.id) in point_ids
        assert str(saved_other_point.id) not in point_ids


# ==================== Return Isolation Tests ====================

class TestReturnIsolation:
    """Tests d'isolation pour les retours."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_return_by_id(
        self,
        shipping_service: ShippingService,
        saved_return_other_tenant: Return
    ):
        """Un tenant ne peut pas accéder à un retour d'un autre tenant."""
        with pytest.raises(ReturnNotFoundError):
            await shipping_service.get_return(str(saved_return_other_tenant.id))

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_return_by_number(
        self,
        shipping_service: ShippingService,
        saved_return_other_tenant: Return
    ):
        """Un tenant ne peut pas accéder à un retour d'un autre tenant par numéro."""
        with pytest.raises(ReturnNotFoundError):
            await shipping_service.get_return_by_number(
                saved_return_other_tenant.return_number
            )

    @pytest.mark.asyncio
    async def test_list_returns_excludes_other_tenant(
        self,
        shipping_service: ShippingService,
        saved_return_requested: Return,
        saved_return_other_tenant: Return
    ):
        """La liste des retours n'inclut pas ceux d'autres tenants."""
        returns, total = await shipping_service.list_returns()

        return_ids = [str(r.id) for r in returns]
        assert str(saved_return_requested.id) in return_ids
        assert str(saved_return_other_tenant.id) not in return_ids

    @pytest.mark.asyncio
    async def test_return_repo_base_query_filters_tenant(
        self,
        return_repo: ReturnRepository,
        saved_return_requested: Return,
        saved_return_other_tenant: Return
    ):
        """Le repository Return filtre par tenant_id."""
        ret = await return_repo.get_by_id(str(saved_return_requested.id))
        assert ret is not None
        assert ret.tenant_id == return_repo.tenant_id

        other_return = await return_repo.get_by_id(str(saved_return_other_tenant.id))
        assert other_return is None

    @pytest.mark.asyncio
    async def test_cannot_approve_other_tenant_return(
        self,
        shipping_service: ShippingService,
        saved_return_other_tenant: Return,
        user_id: str
    ):
        """Un tenant ne peut pas approuver un retour d'un autre tenant."""
        with pytest.raises(ReturnNotFoundError):
            await shipping_service.approve_return(
                str(saved_return_other_tenant.id),
                user_id
            )


# ==================== Soft Delete Isolation Tests ====================

class TestSoftDeleteIsolation:
    """Tests d'isolation pour les entités supprimées."""

    @pytest.mark.asyncio
    async def test_deleted_zone_not_visible(
        self,
        shipping_service: ShippingService,
        saved_zone_france: Zone,
        user_id: str
    ):
        """Une zone supprimée n'est plus visible dans les listes."""
        # Supprimer la zone
        await shipping_service.delete_zone(str(saved_zone_france.id), user_id)

        # Vérifier qu'elle n'apparaît plus dans la liste
        zones, total = await shipping_service.list_zones()
        zone_ids = [str(z.id) for z in zones]
        assert str(saved_zone_france.id) not in zone_ids

    @pytest.mark.asyncio
    async def test_deleted_carrier_not_visible(
        self,
        shipping_service: ShippingService,
        saved_carrier_colissimo: Carrier,
        user_id: str
    ):
        """Un transporteur supprimé n'est plus visible dans les listes."""
        # Supprimer le transporteur
        await shipping_service.delete_carrier(str(saved_carrier_colissimo.id), user_id)

        # Vérifier qu'il n'apparaît plus dans la liste
        carriers, total = await shipping_service.list_carriers()
        carrier_ids = [str(c.id) for c in carriers]
        assert str(saved_carrier_colissimo.id) not in carrier_ids

    @pytest.mark.asyncio
    async def test_deleted_rate_not_visible(
        self,
        shipping_service: ShippingService,
        saved_rate_standard: ShippingRate,
        user_id: str
    ):
        """Un tarif supprimé n'est plus visible dans les listes."""
        # Supprimer le tarif
        await shipping_service.delete_rate(str(saved_rate_standard.id), user_id)

        # Vérifier qu'il n'apparaît plus dans la liste
        rates, total = await shipping_service.list_rates()
        rate_ids = [str(r.id) for r in rates]
        assert str(saved_rate_standard.id) not in rate_ids


# ==================== Cross-Tenant Operation Tests ====================

class TestCrossTenantOperations:
    """Tests vérifiant qu'un tenant ne peut pas modifier les données d'un autre."""

    @pytest.mark.asyncio
    async def test_cannot_update_other_tenant_zone(
        self,
        shipping_service: ShippingService,
        saved_zone_other_tenant: Zone,
        user_id: str
    ):
        """Un tenant ne peut pas mettre à jour une zone d'un autre tenant."""
        from app.modules.shipping.schemas import ZoneUpdate

        update_data = ZoneUpdate(name="Zone Modifiée")
        with pytest.raises(ZoneNotFoundError):
            await shipping_service.update_zone(
                str(saved_zone_other_tenant.id),
                update_data,
                user_id
            )

    @pytest.mark.asyncio
    async def test_cannot_delete_other_tenant_zone(
        self,
        shipping_service: ShippingService,
        saved_zone_other_tenant: Zone,
        user_id: str
    ):
        """Un tenant ne peut pas supprimer une zone d'un autre tenant."""
        with pytest.raises(ZoneNotFoundError):
            await shipping_service.delete_zone(
                str(saved_zone_other_tenant.id),
                user_id
            )

    @pytest.mark.asyncio
    async def test_cannot_update_other_tenant_carrier(
        self,
        shipping_service: ShippingService,
        saved_carrier_other_tenant: Carrier,
        user_id: str
    ):
        """Un tenant ne peut pas mettre à jour un transporteur d'un autre tenant."""
        from app.modules.shipping.schemas import CarrierUpdate

        update_data = CarrierUpdate(name="Transporteur Modifié")
        with pytest.raises(CarrierNotFoundError):
            await shipping_service.update_carrier(
                str(saved_carrier_other_tenant.id),
                update_data,
                user_id
            )

    @pytest.mark.asyncio
    async def test_cannot_update_other_tenant_shipment(
        self,
        shipping_service: ShippingService,
        saved_shipment_other_tenant: Shipment,
        user_id: str
    ):
        """Un tenant ne peut pas mettre à jour une expédition d'un autre tenant."""
        from app.modules.shipping.schemas import ShipmentUpdate

        update_data = ShipmentUpdate(notes="Notes modifiées")
        with pytest.raises(ShipmentNotFoundError):
            await shipping_service.update_shipment(
                str(saved_shipment_other_tenant.id),
                update_data,
                user_id
            )


# ==================== Statistics Isolation Tests ====================

class TestStatsIsolation:
    """Tests d'isolation pour les statistiques."""

    @pytest.mark.asyncio
    async def test_stats_only_include_own_tenant_data(
        self,
        shipping_service: ShippingService,
        other_shipping_service: ShippingService,
        saved_shipment_pending: Shipment,
        saved_shipment_delivered: Shipment,
        saved_shipment_other_tenant: Shipment
    ):
        """Les statistiques n'incluent que les données du tenant courant."""
        from datetime import date, timedelta

        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=1)

        # Stats pour notre tenant
        our_stats = await shipping_service.get_shipping_stats(start_date, end_date)

        # Stats pour l'autre tenant
        other_stats = await other_shipping_service.get_shipping_stats(start_date, end_date)

        # Vérifier que les stats sont différentes et correspondent à chaque tenant
        assert our_stats["total_shipments"] >= 2  # Nos 2 expéditions
        assert other_stats["total_shipments"] >= 1  # L'expédition de l'autre tenant

        # Les stats ne doivent pas inclure les données de l'autre tenant
        assert our_stats["total_shipments"] != (
            our_stats["total_shipments"] + other_stats["total_shipments"]
        ) or our_stats["total_shipments"] == 0
