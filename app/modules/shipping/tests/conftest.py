"""
Fixtures de test pour le module Shipping - GAP-078
===================================================
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.shipping.models import (
    Zone, Carrier, ShippingRate, Shipment, Package, PickupPoint, Return,
    CarrierType, ShippingMethod, ShipmentStatus, PackageType, ReturnStatus,
    RateCalculation
)
from app.modules.shipping.repository import (
    ZoneRepository, CarrierRepository, ShippingRateRepository,
    ShipmentRepository, PackageRepository, PickupPointRepository,
    ReturnRepository
)
from app.modules.shipping.service import ShippingService


# ==================== Tenant IDs ====================

@pytest.fixture
def tenant_id() -> str:
    """Tenant ID principal pour les tests."""
    return str(uuid4())


@pytest.fixture
def other_tenant_id() -> str:
    """Autre tenant ID pour tester l'isolation."""
    return str(uuid4())


@pytest.fixture
def user_id() -> str:
    """User ID pour les tests."""
    return str(uuid4())


# ==================== Services ====================

@pytest.fixture
def shipping_service(db_session: AsyncSession, tenant_id: str) -> ShippingService:
    """Service Shipping pour le tenant principal."""
    return ShippingService(db_session, tenant_id)


@pytest.fixture
def other_shipping_service(db_session: AsyncSession, other_tenant_id: str) -> ShippingService:
    """Service Shipping pour l'autre tenant."""
    return ShippingService(db_session, other_tenant_id)


# ==================== Repositories ====================

@pytest.fixture
def zone_repo(db_session: AsyncSession, tenant_id: str) -> ZoneRepository:
    """Repository Zone."""
    return ZoneRepository(db_session, tenant_id)


@pytest.fixture
def carrier_repo(db_session: AsyncSession, tenant_id: str) -> CarrierRepository:
    """Repository Carrier."""
    return CarrierRepository(db_session, tenant_id)


@pytest.fixture
def rate_repo(db_session: AsyncSession, tenant_id: str) -> ShippingRateRepository:
    """Repository ShippingRate."""
    return ShippingRateRepository(db_session, tenant_id)


@pytest.fixture
def shipment_repo(db_session: AsyncSession, tenant_id: str) -> ShipmentRepository:
    """Repository Shipment."""
    return ShipmentRepository(db_session, tenant_id)


@pytest.fixture
def package_repo(db_session: AsyncSession, tenant_id: str) -> PackageRepository:
    """Repository Package."""
    return PackageRepository(db_session, tenant_id)


@pytest.fixture
def pickup_point_repo(db_session: AsyncSession, tenant_id: str) -> PickupPointRepository:
    """Repository PickupPoint."""
    return PickupPointRepository(db_session, tenant_id)


@pytest.fixture
def return_repo(db_session: AsyncSession, tenant_id: str) -> ReturnRepository:
    """Repository Return."""
    return ReturnRepository(db_session, tenant_id)


# ==================== Zone Fixtures ====================

@pytest.fixture
def zone_france(tenant_id: str, user_id: str) -> Zone:
    """Zone France métropolitaine."""
    return Zone(
        id=uuid4(),
        tenant_id=tenant_id,
        code="ZN-FR",
        name="France Métropolitaine",
        description="Zone de livraison France métropolitaine",
        countries=["FR"],
        postal_codes=["*"],
        excluded_postal_codes=["97*", "98*"],
        is_active=True,
        sort_order=1,
        created_by=user_id
    )


@pytest.fixture
def zone_europe(tenant_id: str, user_id: str) -> Zone:
    """Zone Europe."""
    return Zone(
        id=uuid4(),
        tenant_id=tenant_id,
        code="ZN-EU",
        name="Union Européenne",
        description="Zone de livraison UE",
        countries=["DE", "ES", "IT", "BE", "NL", "PT", "AT", "PL"],
        postal_codes=[],
        excluded_postal_codes=[],
        is_active=True,
        sort_order=2,
        created_by=user_id
    )


@pytest.fixture
def zone_other_tenant(other_tenant_id: str, user_id: str) -> Zone:
    """Zone pour autre tenant."""
    return Zone(
        id=uuid4(),
        tenant_id=other_tenant_id,
        code="ZN-OTHER",
        name="Zone Autre Tenant",
        description="Zone appartenant à un autre tenant",
        countries=["US"],
        postal_codes=["*"],
        is_active=True,
        sort_order=1,
        created_by=user_id
    )


@pytest.fixture
async def saved_zone_france(
    zone_repo: ZoneRepository,
    zone_france: Zone
) -> Zone:
    """Zone France sauvegardée."""
    return await zone_repo.create(zone_france)


@pytest.fixture
async def saved_zone_other_tenant(
    db_session: AsyncSession,
    other_tenant_id: str,
    zone_other_tenant: Zone
) -> Zone:
    """Zone autre tenant sauvegardée."""
    other_repo = ZoneRepository(db_session, other_tenant_id)
    return await other_repo.create(zone_other_tenant)


# ==================== Carrier Fixtures ====================

@pytest.fixture
def carrier_colissimo(tenant_id: str, user_id: str) -> Carrier:
    """Transporteur Colissimo."""
    return Carrier(
        id=uuid4(),
        tenant_id=tenant_id,
        code="COLISSIMO",
        name="La Poste - Colissimo",
        description="Service Colissimo La Poste",
        carrier_type=CarrierType.POSTAL,
        api_endpoint="https://api.colissimo.fr/v1",
        api_key="test_api_key",
        api_secret="test_api_secret",
        account_number="123456",
        supports_tracking=True,
        supports_labels=True,
        supports_returns=True,
        supports_pickup=False,
        supports_insurance=True,
        min_delivery_days=2,
        max_delivery_days=5,
        max_weight_kg=Decimal("30"),
        max_length_cm=150,
        max_girth_cm=300,
        logo_url="https://example.com/colissimo.png",
        tracking_url_template="https://www.laposte.fr/outils/suivre-vos-envois?code={tracking_number}",
        is_active=True,
        created_by=user_id
    )


@pytest.fixture
def carrier_chronopost(tenant_id: str, user_id: str) -> Carrier:
    """Transporteur Chronopost."""
    return Carrier(
        id=uuid4(),
        tenant_id=tenant_id,
        code="CHRONOPOST",
        name="Chronopost",
        description="Livraison express Chronopost",
        carrier_type=CarrierType.EXPRESS,
        api_endpoint="https://api.chronopost.fr/v1",
        supports_tracking=True,
        supports_labels=True,
        supports_returns=True,
        supports_pickup=True,
        supports_insurance=True,
        min_delivery_days=1,
        max_delivery_days=2,
        max_weight_kg=Decimal("30"),
        is_active=True,
        created_by=user_id
    )


@pytest.fixture
def carrier_other_tenant(other_tenant_id: str, user_id: str) -> Carrier:
    """Transporteur pour autre tenant."""
    return Carrier(
        id=uuid4(),
        tenant_id=other_tenant_id,
        code="OTHER-CARRIER",
        name="Autre Transporteur",
        description="Transporteur appartenant à un autre tenant",
        carrier_type=CarrierType.LOCAL,
        is_active=True,
        created_by=user_id
    )


@pytest.fixture
async def saved_carrier_colissimo(
    carrier_repo: CarrierRepository,
    carrier_colissimo: Carrier
) -> Carrier:
    """Transporteur Colissimo sauvegardé."""
    return await carrier_repo.create(carrier_colissimo)


@pytest.fixture
async def saved_carrier_other_tenant(
    db_session: AsyncSession,
    other_tenant_id: str,
    carrier_other_tenant: Carrier
) -> Carrier:
    """Transporteur autre tenant sauvegardé."""
    other_repo = CarrierRepository(db_session, other_tenant_id)
    return await other_repo.create(carrier_other_tenant)


# ==================== Rate Fixtures ====================

@pytest.fixture
def rate_standard(
    tenant_id: str,
    user_id: str,
    saved_carrier_colissimo: Carrier,
    saved_zone_france: Zone
) -> ShippingRate:
    """Tarif standard."""
    return ShippingRate(
        id=uuid4(),
        tenant_id=tenant_id,
        code="RATE-STD",
        name="Colissimo Standard",
        description="Livraison standard Colissimo",
        carrier_id=saved_carrier_colissimo.id,
        zone_id=saved_zone_france.id,
        shipping_method=ShippingMethod.STANDARD,
        calculation_method=RateCalculation.WEIGHT,
        base_rate=Decimal("4.95"),
        per_kg_rate=Decimal("0.50"),
        weight_tiers=[
            {"up_to_kg": 1, "rate": 4.95},
            {"up_to_kg": 3, "rate": 6.95},
            {"up_to_kg": 5, "rate": 8.95},
            {"up_to_kg": 10, "rate": 12.95}
        ],
        fuel_surcharge_percent=Decimal("5"),
        residential_surcharge=Decimal("0"),
        free_shipping_threshold=Decimal("50"),
        min_days=2,
        max_days=5,
        valid_from=date.today() - timedelta(days=30),
        valid_until=date.today() + timedelta(days=365),
        is_active=True,
        created_by=user_id
    )


@pytest.fixture
def rate_express(
    tenant_id: str,
    user_id: str,
    saved_carrier_colissimo: Carrier,
    saved_zone_france: Zone
) -> ShippingRate:
    """Tarif express."""
    return ShippingRate(
        id=uuid4(),
        tenant_id=tenant_id,
        code="RATE-EXP",
        name="Colissimo Express",
        description="Livraison express Colissimo",
        carrier_id=saved_carrier_colissimo.id,
        zone_id=saved_zone_france.id,
        shipping_method=ShippingMethod.EXPRESS,
        calculation_method=RateCalculation.FLAT,
        base_rate=Decimal("12.95"),
        min_days=1,
        max_days=2,
        is_active=True,
        created_by=user_id
    )


@pytest.fixture
async def saved_rate_standard(
    rate_repo: ShippingRateRepository,
    rate_standard: ShippingRate
) -> ShippingRate:
    """Tarif standard sauvegardé."""
    return await rate_repo.create(rate_standard)


# ==================== Shipment Fixtures ====================

@pytest.fixture
def ship_from_address() -> dict:
    """Adresse d'expédition."""
    return {
        "name": "Mon Entreprise",
        "company": "ACME Corp",
        "street1": "123 Rue du Commerce",
        "street2": "",
        "city": "Paris",
        "state": "IDF",
        "postal_code": "75001",
        "country_code": "FR",
        "phone": "+33123456789",
        "email": "expeditions@acme.fr",
        "is_residential": False,
        "instructions": ""
    }


@pytest.fixture
def ship_to_address() -> dict:
    """Adresse de livraison."""
    return {
        "name": "Jean Dupont",
        "company": "",
        "street1": "45 Avenue de la République",
        "street2": "Apt 12",
        "city": "Lyon",
        "state": "ARA",
        "postal_code": "69001",
        "country_code": "FR",
        "phone": "+33612345678",
        "email": "jean.dupont@email.com",
        "is_residential": True,
        "instructions": "Code: 1234"
    }


@pytest.fixture
def shipment_pending(
    tenant_id: str,
    user_id: str,
    saved_carrier_colissimo: Carrier,
    ship_from_address: dict,
    ship_to_address: dict
) -> Shipment:
    """Expédition en attente."""
    return Shipment(
        id=uuid4(),
        tenant_id=tenant_id,
        shipment_number="SHP-00000001",
        order_id=str(uuid4()),
        order_number="CMD-2024-001",
        status=ShipmentStatus.PENDING,
        carrier_id=saved_carrier_colissimo.id,
        carrier_name=saved_carrier_colissimo.name,
        shipping_method=ShippingMethod.STANDARD,
        ship_from=ship_from_address,
        ship_to=ship_to_address,
        total_packages=1,
        total_weight=Decimal("2.5"),
        shipping_cost=Decimal("6.95"),
        insurance_cost=Decimal("0"),
        surcharges=Decimal("0"),
        total_cost=Decimal("6.95"),
        currency="EUR",
        is_insured=False,
        signature_required=False,
        ship_date=date.today(),
        estimated_delivery=date.today() + timedelta(days=3),
        tracking_events=[],
        created_by=user_id
    )


@pytest.fixture
def shipment_delivered(
    tenant_id: str,
    user_id: str,
    saved_carrier_colissimo: Carrier,
    ship_from_address: dict,
    ship_to_address: dict
) -> Shipment:
    """Expédition livrée."""
    return Shipment(
        id=uuid4(),
        tenant_id=tenant_id,
        shipment_number="SHP-00000002",
        order_id=str(uuid4()),
        order_number="CMD-2024-002",
        status=ShipmentStatus.DELIVERED,
        carrier_id=saved_carrier_colissimo.id,
        carrier_name=saved_carrier_colissimo.name,
        shipping_method=ShippingMethod.STANDARD,
        ship_from=ship_from_address,
        ship_to=ship_to_address,
        master_tracking_number="CO123456789FR",
        total_packages=1,
        total_weight=Decimal("1.5"),
        shipping_cost=Decimal("4.95"),
        total_cost=Decimal("4.95"),
        ship_date=date.today() - timedelta(days=5),
        estimated_delivery=date.today() - timedelta(days=2),
        actual_delivery=datetime.utcnow() - timedelta(days=2),
        tracking_events=[
            {
                "timestamp": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "status": "label_created",
                "description": "Étiquette créée",
                "location": "Paris"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(days=4)).isoformat(),
                "status": "picked_up",
                "description": "Colis enlevé",
                "location": "Paris"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "status": "delivered",
                "description": "Colis livré",
                "location": "Lyon"
            }
        ],
        created_by=user_id
    )


@pytest.fixture
def shipment_other_tenant(
    other_tenant_id: str,
    user_id: str,
    saved_carrier_other_tenant: Carrier
) -> Shipment:
    """Expédition pour autre tenant."""
    return Shipment(
        id=uuid4(),
        tenant_id=other_tenant_id,
        shipment_number="SHP-OTHER-001",
        order_id=str(uuid4()),
        order_number="CMD-OTHER-001",
        status=ShipmentStatus.PENDING,
        carrier_id=saved_carrier_other_tenant.id,
        carrier_name=saved_carrier_other_tenant.name,
        shipping_method=ShippingMethod.STANDARD,
        ship_from={"name": "Other", "country_code": "US"},
        ship_to={"name": "Customer", "country_code": "US"},
        total_packages=1,
        total_weight=Decimal("1"),
        shipping_cost=Decimal("10"),
        total_cost=Decimal("10"),
        created_by=user_id
    )


@pytest.fixture
async def saved_shipment_pending(
    shipment_repo: ShipmentRepository,
    shipment_pending: Shipment
) -> Shipment:
    """Expédition en attente sauvegardée."""
    return await shipment_repo.create(shipment_pending)


@pytest.fixture
async def saved_shipment_delivered(
    shipment_repo: ShipmentRepository,
    shipment_delivered: Shipment
) -> Shipment:
    """Expédition livrée sauvegardée."""
    return await shipment_repo.create(shipment_delivered)


@pytest.fixture
async def saved_shipment_other_tenant(
    db_session: AsyncSession,
    other_tenant_id: str,
    shipment_other_tenant: Shipment
) -> Shipment:
    """Expédition autre tenant sauvegardée."""
    other_repo = ShipmentRepository(db_session, other_tenant_id)
    return await other_repo.create(shipment_other_tenant)


# ==================== Package Fixtures ====================

@pytest.fixture
def package_small(
    tenant_id: str,
    user_id: str,
    saved_shipment_pending: Shipment
) -> Package:
    """Petit colis."""
    return Package(
        id=uuid4(),
        tenant_id=tenant_id,
        shipment_id=saved_shipment_pending.id,
        package_type=PackageType.SMALL_BOX,
        length=Decimal("20"),
        width=Decimal("15"),
        height=Decimal("10"),
        weight=Decimal("1.5"),
        dimensional_weight=Decimal("0.6"),
        billable_weight=Decimal("1.5"),
        items=[
            {"product_id": str(uuid4()), "name": "Article 1", "quantity": 2}
        ],
        declared_value=Decimal("45.00"),
        currency="EUR",
        label_format="PDF",
        created_by=user_id
    )


@pytest.fixture
async def saved_package_small(
    package_repo: PackageRepository,
    package_small: Package
) -> Package:
    """Petit colis sauvegardé."""
    return await package_repo.create(package_small)


# ==================== PickupPoint Fixtures ====================

@pytest.fixture
def pickup_point_relay(
    tenant_id: str,
    user_id: str,
    saved_carrier_colissimo: Carrier
) -> PickupPoint:
    """Point relais."""
    return PickupPoint(
        id=uuid4(),
        tenant_id=tenant_id,
        carrier_id=saved_carrier_colissimo.id,
        external_id="RELAY-001",
        name="Tabac Presse Le Central",
        address={
            "street1": "12 Place de la Mairie",
            "city": "Lyon",
            "postal_code": "69001",
            "country_code": "FR"
        },
        opening_hours={
            "monday": "08:00-19:00",
            "tuesday": "08:00-19:00",
            "wednesday": "08:00-19:00",
            "thursday": "08:00-19:00",
            "friday": "08:00-19:00",
            "saturday": "09:00-12:00",
            "sunday": "closed"
        },
        is_locker=False,
        has_parking=True,
        wheelchair_accessible=True,
        latitude=Decimal("45.7676"),
        longitude=Decimal("4.8344"),
        is_active=True,
        created_by=user_id
    )


@pytest.fixture
def pickup_point_locker(
    tenant_id: str,
    user_id: str,
    saved_carrier_colissimo: Carrier
) -> PickupPoint:
    """Casier automatique."""
    return PickupPoint(
        id=uuid4(),
        tenant_id=tenant_id,
        carrier_id=saved_carrier_colissimo.id,
        external_id="LOCKER-001",
        name="Locker Gare Part-Dieu",
        address={
            "street1": "Gare de Lyon Part-Dieu",
            "city": "Lyon",
            "postal_code": "69003",
            "country_code": "FR"
        },
        opening_hours={
            "monday": "06:00-23:00",
            "tuesday": "06:00-23:00",
            "wednesday": "06:00-23:00",
            "thursday": "06:00-23:00",
            "friday": "06:00-23:00",
            "saturday": "06:00-23:00",
            "sunday": "06:00-23:00"
        },
        is_locker=True,
        has_parking=False,
        wheelchair_accessible=True,
        latitude=Decimal("45.7606"),
        longitude=Decimal("4.8600"),
        is_active=True,
        created_by=user_id
    )


@pytest.fixture
async def saved_pickup_point_relay(
    pickup_point_repo: PickupPointRepository,
    pickup_point_relay: PickupPoint
) -> PickupPoint:
    """Point relais sauvegardé."""
    return await pickup_point_repo.create(pickup_point_relay)


# ==================== Return Fixtures ====================

@pytest.fixture
def return_requested(
    tenant_id: str,
    user_id: str,
    saved_shipment_delivered: Shipment
) -> Return:
    """Retour demandé."""
    return Return(
        id=uuid4(),
        tenant_id=tenant_id,
        return_number="RET-00000001",
        order_id=saved_shipment_delivered.order_id,
        shipment_id=saved_shipment_delivered.id,
        status=ReturnStatus.REQUESTED,
        reason="Produit défectueux",
        reason_code="DEFECTIVE",
        customer_notes="L'écran ne s'allume plus",
        items=[
            {
                "product_id": str(uuid4()),
                "name": "Smartphone XYZ",
                "quantity": 1,
                "reason": "defective"
            }
        ],
        return_address=saved_shipment_delivered.ship_from,
        requested_at=datetime.utcnow(),
        created_by=user_id
    )


@pytest.fixture
def return_approved(
    tenant_id: str,
    user_id: str,
    saved_shipment_delivered: Shipment
) -> Return:
    """Retour approuvé."""
    return Return(
        id=uuid4(),
        tenant_id=tenant_id,
        return_number="RET-00000002",
        order_id=saved_shipment_delivered.order_id,
        shipment_id=saved_shipment_delivered.id,
        status=ReturnStatus.APPROVED,
        reason="Ne correspond pas",
        reason_code="NOT_AS_DESCRIBED",
        items=[
            {
                "product_id": str(uuid4()),
                "name": "T-shirt",
                "quantity": 1,
                "reason": "wrong_size"
            }
        ],
        return_address=saved_shipment_delivered.ship_from,
        requested_at=datetime.utcnow() - timedelta(days=1),
        approved_at=datetime.utcnow(),
        created_by=user_id
    )


@pytest.fixture
def return_other_tenant(
    other_tenant_id: str,
    user_id: str,
    saved_shipment_other_tenant: Shipment
) -> Return:
    """Retour pour autre tenant."""
    return Return(
        id=uuid4(),
        tenant_id=other_tenant_id,
        return_number="RET-OTHER-001",
        order_id=saved_shipment_other_tenant.order_id,
        shipment_id=saved_shipment_other_tenant.id,
        status=ReturnStatus.REQUESTED,
        reason="Changed mind",
        items=[],
        created_by=user_id
    )


@pytest.fixture
async def saved_return_requested(
    return_repo: ReturnRepository,
    return_requested: Return
) -> Return:
    """Retour demandé sauvegardé."""
    return await return_repo.create(return_requested)


@pytest.fixture
async def saved_return_approved(
    return_repo: ReturnRepository,
    return_approved: Return
) -> Return:
    """Retour approuvé sauvegardé."""
    return await return_repo.create(return_approved)


@pytest.fixture
async def saved_return_other_tenant(
    db_session: AsyncSession,
    other_tenant_id: str,
    return_other_tenant: Return
) -> Return:
    """Retour autre tenant sauvegardé."""
    other_repo = ReturnRepository(db_session, other_tenant_id)
    return await other_repo.create(return_other_tenant)
