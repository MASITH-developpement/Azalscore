"""
Service Shipping / Expédition - GAP-078
========================================

Gestion des expéditions:
- Transporteurs multiples
- Calcul de tarifs
- Génération d'étiquettes
- Suivi des colis
- Zones de livraison
- Points relais
- Retours et réclamations
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
import hashlib
import uuid

from .models import (
    Zone, Carrier, ShippingRate, Shipment, Package, PickupPoint, Return,
    CarrierType, ShippingMethod, ShipmentStatus, PackageType, ReturnStatus,
    RateCalculation
)
from .schemas import (
    ZoneCreate, ZoneUpdate,
    CarrierCreate, CarrierUpdate,
    RateCreate, RateUpdate,
    ShipmentCreate, ShipmentUpdate,
    PackageCreate, PackageUpdate,
    PickupPointCreate, PickupPointUpdate,
    ReturnCreate,
    AddressSchema, RateCalculationRequest, RateCalculationResponse,
    TrackingEventCreate, LabelGenerationResponse
)
from .repository import (
    ZoneRepository, CarrierRepository, ShippingRateRepository,
    ShipmentRepository, PackageRepository, PickupPointRepository,
    ReturnRepository
)
from .exceptions import (
    # Zone exceptions
    ZoneNotFoundError, ZoneDuplicateError, ZoneValidationError, ZoneInUseError,
    # Carrier exceptions
    CarrierNotFoundError, CarrierDuplicateError, CarrierValidationError,
    CarrierInactiveError, CarrierInUseError, CarrierApiError,
    # Rate exceptions
    RateNotFoundError, RateDuplicateError, RateValidationError,
    RateExpiredError, NoRateAvailableError,
    # Shipment exceptions
    ShipmentNotFoundError, ShipmentDuplicateError, ShipmentValidationError,
    ShipmentStateError, ShipmentCancelledError, ShipmentDeliveredError,
    ShipmentCannotBeCancelledError, LabelAlreadyGeneratedError,
    LabelNotGeneratedError, TrackingNumberNotFoundError,
    # Package exceptions
    PackageNotFoundError, PackageValidationError,
    PackageWeightExceededError, PackageDimensionsExceededError,
    # PickupPoint exceptions
    PickupPointNotFoundError, PickupPointDuplicateError,
    PickupPointValidationError, PickupPointInactiveError,
    # Return exceptions
    ReturnNotFoundError, ReturnDuplicateError, ReturnValidationError,
    ReturnStateError, ReturnAlreadyApprovedError, ReturnAlreadyRefundedError,
    ReturnNotApprovedError, ReturnNotReceivedError, ReturnRejectedError,
    # Address exceptions
    AddressValidationError, AddressNotServiceableError
)


class ShippingService:
    """Service de gestion des expéditions."""

    def __init__(self, session: Session, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.zone_repo = ZoneRepository(session, tenant_id)
        self.carrier_repo = CarrierRepository(session, tenant_id)
        self.rate_repo = ShippingRateRepository(session, tenant_id)
        self.shipment_repo = ShipmentRepository(session, tenant_id)
        self.package_repo = PackageRepository(session, tenant_id)
        self.pickup_point_repo = PickupPointRepository(session, tenant_id)
        self.return_repo = ReturnRepository(session, tenant_id)

    # ==================== Zone Methods ====================

    def create_zone(
        self,
        data: ZoneCreate,
        created_by: str
    ) -> Zone:
        """Créer une zone de livraison."""
        # Vérifier le code unique
        existing = self.zone_repo.get_by_code(data.code)
        if existing:
            raise ZoneDuplicateError(data.code)

        # Valider les données
        if not data.countries:
            raise ZoneValidationError("Au moins un pays est requis")

        # Générer le code si non fourni
        code = data.code
        if not code:
            code = self.zone_repo.get_next_code()

        zone = Zone(
            tenant_id=self.tenant_id,
            code=code,
            name=data.name,
            description=data.description,
            countries=data.countries,
            postal_codes=data.postal_codes or [],
            excluded_postal_codes=data.excluded_postal_codes or [],
            is_active=data.is_active,
            sort_order=data.sort_order or 0,
            created_by=created_by
        )

        return self.zone_repo.create(zone)

    def get_zone(self, zone_id: str) -> Zone:
        """Récupérer une zone par ID."""
        zone = self.zone_repo.get_by_id(zone_id)
        if not zone:
            raise ZoneNotFoundError(zone_id)
        return zone

    def get_zone_by_code(self, code: str) -> Zone:
        """Récupérer une zone par code."""
        zone = self.zone_repo.get_by_code(code)
        if not zone:
            raise ZoneNotFoundError(code)
        return zone

    def update_zone(
        self,
        zone_id: str,
        data: ZoneUpdate,
        updated_by: str
    ) -> Zone:
        """Mettre à jour une zone."""
        zone = self.get_zone(zone_id)

        # Vérifier unicité du code si modifié
        if data.code and data.code != zone.code:
            existing = self.zone_repo.get_by_code(data.code)
            if existing:
                raise ZoneDuplicateError(data.code)
            zone.code = data.code

        # Mettre à jour les champs
        if data.name is not None:
            zone.name = data.name
        if data.description is not None:
            zone.description = data.description
        if data.countries is not None:
            zone.countries = data.countries
        if data.postal_codes is not None:
            zone.postal_codes = data.postal_codes
        if data.excluded_postal_codes is not None:
            zone.excluded_postal_codes = data.excluded_postal_codes
        if data.is_active is not None:
            zone.is_active = data.is_active
        if data.sort_order is not None:
            zone.sort_order = data.sort_order

        zone.updated_by = updated_by

        return self.zone_repo.update(zone)

    def delete_zone(
        self,
        zone_id: str,
        deleted_by: str
    ) -> Zone:
        """Supprimer une zone (soft delete)."""
        zone = self.get_zone(zone_id)

        # Vérifier qu'aucun tarif n'utilise cette zone
        rates = self.rate_repo.list_by_zone(zone_id)
        if rates:
            raise ZoneInUseError(zone_id, len(rates))

        return self.zone_repo.soft_delete(zone_id, deleted_by)

    def restore_zone(
        self,
        zone_id: str,
        restored_by: str
    ) -> Zone:
        """Restaurer une zone supprimée."""
        return self.zone_repo.restore(zone_id, restored_by)

    def list_zones(
        self,
        *,
        is_active: Optional[bool] = None,
        country_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Zone], int]:
        """Lister les zones."""
        return self.zone_repo.list_zones(
            is_active=is_active,
            country_code=country_code,
            skip=skip,
            limit=limit
        )

    def find_zone_for_address(
        self,
        country_code: str,
        postal_code: str
    ) -> Optional[Zone]:
        """Trouver la zone pour une adresse."""
        return self.zone_repo.find_zone_for_address(country_code, postal_code)

    # ==================== Carrier Methods ====================

    def create_carrier(
        self,
        data: CarrierCreate,
        created_by: str
    ) -> Carrier:
        """Créer un transporteur."""
        # Vérifier le code unique
        existing = self.carrier_repo.get_by_code(data.code)
        if existing:
            raise CarrierDuplicateError(data.code)

        # Générer le code si non fourni
        code = data.code
        if not code:
            code = self.carrier_repo.get_next_code()

        carrier = Carrier(
            tenant_id=self.tenant_id,
            code=code,
            name=data.name,
            description=data.description,
            carrier_type=data.carrier_type,
            api_endpoint=data.api_endpoint,
            api_key=data.api_key,
            api_secret=data.api_secret,
            account_number=data.account_number,
            supports_tracking=data.supports_tracking,
            supports_labels=data.supports_labels,
            supports_returns=data.supports_returns,
            supports_pickup=data.supports_pickup,
            supports_insurance=data.supports_insurance,
            min_delivery_days=data.min_delivery_days,
            max_delivery_days=data.max_delivery_days,
            max_weight_kg=data.max_weight_kg,
            max_length_cm=data.max_length_cm,
            max_girth_cm=data.max_girth_cm,
            logo_url=data.logo_url,
            tracking_url_template=data.tracking_url_template,
            is_active=data.is_active,
            created_by=created_by
        )

        return self.carrier_repo.create(carrier)

    def get_carrier(self, carrier_id: str) -> Carrier:
        """Récupérer un transporteur par ID."""
        carrier = self.carrier_repo.get_by_id(carrier_id)
        if not carrier:
            raise CarrierNotFoundError(carrier_id)
        return carrier

    def get_carrier_by_code(self, code: str) -> Carrier:
        """Récupérer un transporteur par code."""
        carrier = self.carrier_repo.get_by_code(code)
        if not carrier:
            raise CarrierNotFoundError(code)
        return carrier

    def update_carrier(
        self,
        carrier_id: str,
        data: CarrierUpdate,
        updated_by: str
    ) -> Carrier:
        """Mettre à jour un transporteur."""
        carrier = self.get_carrier(carrier_id)

        # Vérifier unicité du code si modifié
        if data.code and data.code != carrier.code:
            existing = self.carrier_repo.get_by_code(data.code)
            if existing:
                raise CarrierDuplicateError(data.code)
            carrier.code = data.code

        # Mettre à jour les champs
        if data.name is not None:
            carrier.name = data.name
        if data.description is not None:
            carrier.description = data.description
        if data.carrier_type is not None:
            carrier.carrier_type = data.carrier_type
        if data.api_endpoint is not None:
            carrier.api_endpoint = data.api_endpoint
        if data.api_key is not None:
            carrier.api_key = data.api_key
        if data.api_secret is not None:
            carrier.api_secret = data.api_secret
        if data.account_number is not None:
            carrier.account_number = data.account_number
        if data.supports_tracking is not None:
            carrier.supports_tracking = data.supports_tracking
        if data.supports_labels is not None:
            carrier.supports_labels = data.supports_labels
        if data.supports_returns is not None:
            carrier.supports_returns = data.supports_returns
        if data.supports_pickup is not None:
            carrier.supports_pickup = data.supports_pickup
        if data.supports_insurance is not None:
            carrier.supports_insurance = data.supports_insurance
        if data.min_delivery_days is not None:
            carrier.min_delivery_days = data.min_delivery_days
        if data.max_delivery_days is not None:
            carrier.max_delivery_days = data.max_delivery_days
        if data.max_weight_kg is not None:
            carrier.max_weight_kg = data.max_weight_kg
        if data.max_length_cm is not None:
            carrier.max_length_cm = data.max_length_cm
        if data.max_girth_cm is not None:
            carrier.max_girth_cm = data.max_girth_cm
        if data.logo_url is not None:
            carrier.logo_url = data.logo_url
        if data.tracking_url_template is not None:
            carrier.tracking_url_template = data.tracking_url_template
        if data.is_active is not None:
            carrier.is_active = data.is_active

        carrier.updated_by = updated_by

        return self.carrier_repo.update(carrier)

    def delete_carrier(
        self,
        carrier_id: str,
        deleted_by: str
    ) -> Carrier:
        """Supprimer un transporteur (soft delete)."""
        carrier = self.get_carrier(carrier_id)

        # Vérifier qu'aucune expédition n'utilise ce transporteur
        shipments, count = self.shipment_repo.list_shipments(
            carrier_id=carrier_id,
            limit=1
        )
        if count > 0:
            raise CarrierInUseError(carrier_id, count)

        return self.carrier_repo.soft_delete(carrier_id, deleted_by)

    def restore_carrier(
        self,
        carrier_id: str,
        restored_by: str
    ) -> Carrier:
        """Restaurer un transporteur supprimé."""
        return self.carrier_repo.restore(carrier_id, restored_by)

    def list_carriers(
        self,
        *,
        carrier_type: Optional[CarrierType] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Carrier], int]:
        """Lister les transporteurs."""
        return self.carrier_repo.list_carriers(
            carrier_type=carrier_type,
            is_active=is_active,
            search=search,
            skip=skip,
            limit=limit
        )

    def activate_carrier(
        self,
        carrier_id: str,
        updated_by: str
    ) -> Carrier:
        """Activer un transporteur."""
        carrier = self.get_carrier(carrier_id)
        carrier.is_active = True
        carrier.updated_by = updated_by
        return self.carrier_repo.update(carrier)

    def deactivate_carrier(
        self,
        carrier_id: str,
        updated_by: str
    ) -> Carrier:
        """Désactiver un transporteur."""
        carrier = self.get_carrier(carrier_id)
        carrier.is_active = False
        carrier.updated_by = updated_by
        return self.carrier_repo.update(carrier)

    # ==================== ShippingRate Methods ====================

    def create_rate(
        self,
        data: RateCreate,
        created_by: str
    ) -> ShippingRate:
        """Créer un tarif d'expédition."""
        # Vérifier le code unique
        existing = self.rate_repo.get_by_code(data.code)
        if existing:
            raise RateDuplicateError(data.code)

        # Vérifier que le transporteur existe
        carrier = self.carrier_repo.get_by_id(data.carrier_id)
        if not carrier:
            raise CarrierNotFoundError(data.carrier_id)

        # Vérifier que la zone existe si fournie
        if data.zone_id:
            zone = self.zone_repo.get_by_id(data.zone_id)
            if not zone:
                raise ZoneNotFoundError(data.zone_id)

        # Générer le code si non fourni
        code = data.code
        if not code:
            code = self.rate_repo.get_next_code()

        # Valider les dates
        if data.valid_from and data.valid_until:
            if data.valid_from > data.valid_until:
                raise RateValidationError("Date de début doit être avant date de fin")

        rate = ShippingRate(
            tenant_id=self.tenant_id,
            code=code,
            name=data.name,
            description=data.description,
            carrier_id=data.carrier_id,
            zone_id=data.zone_id,
            shipping_method=data.shipping_method,
            calculation_method=data.calculation_method,
            base_rate=data.base_rate,
            per_kg_rate=data.per_kg_rate,
            per_item_rate=data.per_item_rate,
            percent_of_order=data.percent_of_order,
            weight_tiers=data.weight_tiers or [],
            price_tiers=data.price_tiers or [],
            fuel_surcharge_percent=data.fuel_surcharge_percent,
            residential_surcharge=data.residential_surcharge,
            oversized_surcharge=data.oversized_surcharge,
            free_shipping_threshold=data.free_shipping_threshold,
            min_days=data.min_days,
            max_days=data.max_days,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            is_active=data.is_active,
            created_by=created_by
        )

        return self.rate_repo.create(rate)

    def get_rate(self, rate_id: str) -> ShippingRate:
        """Récupérer un tarif par ID."""
        rate = self.rate_repo.get_by_id(rate_id)
        if not rate:
            raise RateNotFoundError(rate_id)
        return rate

    def update_rate(
        self,
        rate_id: str,
        data: RateUpdate,
        updated_by: str
    ) -> ShippingRate:
        """Mettre à jour un tarif."""
        rate = self.get_rate(rate_id)

        # Vérifier unicité du code si modifié
        if data.code and data.code != rate.code:
            existing = self.rate_repo.get_by_code(data.code)
            if existing:
                raise RateDuplicateError(data.code)
            rate.code = data.code

        # Mettre à jour les champs
        if data.name is not None:
            rate.name = data.name
        if data.description is not None:
            rate.description = data.description
        if data.zone_id is not None:
            if data.zone_id:
                zone = self.zone_repo.get_by_id(data.zone_id)
                if not zone:
                    raise ZoneNotFoundError(data.zone_id)
            rate.zone_id = data.zone_id
        if data.shipping_method is not None:
            rate.shipping_method = data.shipping_method
        if data.calculation_method is not None:
            rate.calculation_method = data.calculation_method
        if data.base_rate is not None:
            rate.base_rate = data.base_rate
        if data.per_kg_rate is not None:
            rate.per_kg_rate = data.per_kg_rate
        if data.per_item_rate is not None:
            rate.per_item_rate = data.per_item_rate
        if data.percent_of_order is not None:
            rate.percent_of_order = data.percent_of_order
        if data.weight_tiers is not None:
            rate.weight_tiers = data.weight_tiers
        if data.price_tiers is not None:
            rate.price_tiers = data.price_tiers
        if data.fuel_surcharge_percent is not None:
            rate.fuel_surcharge_percent = data.fuel_surcharge_percent
        if data.residential_surcharge is not None:
            rate.residential_surcharge = data.residential_surcharge
        if data.oversized_surcharge is not None:
            rate.oversized_surcharge = data.oversized_surcharge
        if data.free_shipping_threshold is not None:
            rate.free_shipping_threshold = data.free_shipping_threshold
        if data.min_days is not None:
            rate.min_days = data.min_days
        if data.max_days is not None:
            rate.max_days = data.max_days
        if data.valid_from is not None:
            rate.valid_from = data.valid_from
        if data.valid_until is not None:
            rate.valid_until = data.valid_until
        if data.is_active is not None:
            rate.is_active = data.is_active

        rate.updated_by = updated_by

        return self.rate_repo.update(rate)

    def delete_rate(
        self,
        rate_id: str,
        deleted_by: str
    ) -> ShippingRate:
        """Supprimer un tarif (soft delete)."""
        self.get_rate(rate_id)
        return self.rate_repo.soft_delete(rate_id, deleted_by)

    def restore_rate(
        self,
        rate_id: str,
        restored_by: str
    ) -> ShippingRate:
        """Restaurer un tarif supprimé."""
        return self.rate_repo.restore(rate_id, restored_by)

    def list_rates(
        self,
        *,
        carrier_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        shipping_method: Optional[ShippingMethod] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ShippingRate], int]:
        """Lister les tarifs."""
        return self.rate_repo.list_rates(
            carrier_id=carrier_id,
            zone_id=zone_id,
            shipping_method=shipping_method,
            is_active=is_active,
            skip=skip,
            limit=limit
        )

    def calculate_shipping_rates(
        self,
        request: RateCalculationRequest
    ) -> List[RateCalculationResponse]:
        """Calculer les tarifs disponibles pour une expédition."""
        # Trouver la zone pour l'adresse de destination
        zone = self.find_zone_for_address(
            request.destination.country_code,
            request.destination.postal_code
        )

        if not zone:
            raise AddressNotServiceableError(
                f"{request.destination.postal_code}, {request.destination.country_code}"
            )

        # Calculer le poids total
        total_weight = sum(
            Decimal(str(pkg.weight))
            for pkg in request.packages
        )

        # Récupérer les tarifs actifs pour la zone
        rates, _ = self.rate_repo.list_rates(
            zone_id=zone.id,
            is_active=True,
            limit=1000
        )

        available_rates = []
        today = date.today()

        for rate in rates:
            # Vérifier la validité
            if rate.valid_from and rate.valid_from > today:
                continue
            if rate.valid_until and rate.valid_until < today:
                continue

            # Récupérer le transporteur
            carrier = self.carrier_repo.get_by_id(rate.carrier_id)
            if not carrier or not carrier.is_active:
                continue

            # Vérifier le poids max
            if total_weight > carrier.max_weight_kg:
                continue

            # Calculer le tarif
            shipping_cost = self._calculate_rate(
                rate, total_weight, request.order_total, len(request.packages)
            )

            # Appliquer les surcharges
            if request.destination.is_residential and rate.residential_surcharge:
                shipping_cost += rate.residential_surcharge

            if rate.fuel_surcharge_percent:
                shipping_cost += shipping_cost * (rate.fuel_surcharge_percent / Decimal("100"))

            # Vérifier gratuité
            is_free = False
            if rate.free_shipping_threshold and request.order_total >= rate.free_shipping_threshold:
                shipping_cost = Decimal("0")
                is_free = True

            available_rates.append(RateCalculationResponse(
                rate_id=str(rate.id),
                carrier_id=str(carrier.id),
                carrier_name=carrier.name,
                carrier_code=carrier.code,
                method=rate.shipping_method,
                rate_name=rate.name,
                cost=shipping_cost,
                currency=request.currency,
                min_days=rate.min_days,
                max_days=rate.max_days,
                is_free_shipping=is_free,
                zone_id=str(zone.id),
                zone_name=zone.name
            ))

        # Trier par coût
        available_rates.sort(key=lambda x: x.cost)

        if not available_rates:
            raise NoRateAvailableError(
                f"{request.destination.postal_code}, {request.destination.country_code}"
            )

        return available_rates

    def _calculate_rate(
        self,
        rate: ShippingRate,
        weight: Decimal,
        order_total: Decimal,
        item_count: int
    ) -> Decimal:
        """Calculer le montant d'un tarif."""
        if rate.calculation_method == RateCalculation.FLAT:
            return rate.base_rate

        elif rate.calculation_method == RateCalculation.WEIGHT:
            if rate.weight_tiers:
                for tier in sorted(rate.weight_tiers, key=lambda x: x.get("up_to_kg", 0)):
                    if weight <= Decimal(str(tier.get("up_to_kg", 0))):
                        return Decimal(str(tier.get("rate", 0)))
                # Dernier tier
                if rate.weight_tiers:
                    return Decimal(str(rate.weight_tiers[-1].get("rate", 0)))
            return rate.base_rate + (weight * rate.per_kg_rate)

        elif rate.calculation_method == RateCalculation.PRICE_BASED:
            if rate.price_tiers:
                for tier in sorted(rate.price_tiers, key=lambda x: x.get("min_order", 0)):
                    min_order = Decimal(str(tier.get("min_order", 0)))
                    max_order = tier.get("max_order")
                    if order_total >= min_order:
                        if max_order is None or order_total < Decimal(str(max_order)):
                            return Decimal(str(tier.get("rate", 0)))
            return rate.base_rate

        elif rate.calculation_method == RateCalculation.ITEM_COUNT:
            return rate.base_rate + (Decimal(str(item_count)) * rate.per_item_rate)

        elif rate.calculation_method == RateCalculation.VOLUME:
            # Le calcul volumétrique est géré au niveau du colis
            return rate.base_rate + (weight * rate.per_kg_rate)

        return rate.base_rate

    # ==================== Shipment Methods ====================

    def create_shipment(
        self,
        data: ShipmentCreate,
        created_by: str
    ) -> Shipment:
        """Créer une expédition."""
        # Vérifier que le transporteur existe et est actif
        carrier = self.carrier_repo.get_by_id(data.carrier_id)
        if not carrier:
            raise CarrierNotFoundError(data.carrier_id)
        if not carrier.is_active:
            raise CarrierInactiveError(data.carrier_id)

        # Vérifier le tarif si fourni
        if data.rate_id:
            rate = self.rate_repo.get_by_id(data.rate_id)
            if not rate:
                raise RateNotFoundError(data.rate_id)

        # Vérifier le point relais si fourni
        if data.pickup_point_id:
            pickup_point = self.pickup_point_repo.get_by_id(data.pickup_point_id)
            if not pickup_point:
                raise PickupPointNotFoundError(data.pickup_point_id)
            if not pickup_point.is_active:
                raise PickupPointInactiveError(data.pickup_point_id)

        # Générer le numéro d'expédition
        shipment_number = self.shipment_repo.get_next_number()

        # Estimer la date de livraison
        ship_date = data.ship_date or date.today()
        estimated_delivery = ship_date + timedelta(days=carrier.max_delivery_days)

        shipment = Shipment(
            tenant_id=self.tenant_id,
            shipment_number=shipment_number,
            order_id=data.order_id,
            order_number=data.order_number,
            status=ShipmentStatus.PENDING,
            carrier_id=data.carrier_id,
            carrier_name=carrier.name,
            rate_id=data.rate_id,
            shipping_method=data.shipping_method,
            service_code=data.service_code,
            ship_from=data.ship_from.model_dump() if data.ship_from else {},
            ship_to=data.ship_to.model_dump() if data.ship_to else {},
            shipping_cost=data.shipping_cost or Decimal("0"),
            insurance_cost=data.insurance_cost or Decimal("0"),
            surcharges=data.surcharges or Decimal("0"),
            total_cost=(data.shipping_cost or Decimal("0")) +
                       (data.insurance_cost or Decimal("0")) +
                       (data.surcharges or Decimal("0")),
            currency=data.currency,
            is_insured=data.is_insured,
            insured_value=data.insured_value or Decimal("0"),
            signature_required=data.signature_required,
            saturday_delivery=data.saturday_delivery,
            hold_at_location=data.hold_at_location,
            ship_date=ship_date,
            estimated_delivery=estimated_delivery,
            pickup_point_id=data.pickup_point_id,
            notes=data.notes,
            internal_notes=data.internal_notes,
            extra_data=data.extra_data or {},
            created_by=created_by
        )

        shipment = self.shipment_repo.create(shipment)

        # Créer les colis
        total_weight = Decimal("0")
        for pkg_data in data.packages:
            package = self._create_package(shipment.id, pkg_data, created_by)
            total_weight += package.billable_weight

        # Mettre à jour le poids total
        shipment.total_packages = len(data.packages)
        shipment.total_weight = total_weight
        shipment = self.shipment_repo.update(shipment)

        return shipment

    def _create_package(
        self,
        shipment_id: str,
        data: PackageCreate,
        created_by: str
    ) -> Package:
        """Créer un colis pour une expédition."""
        # Calculer le poids volumétrique
        dim_factor = Decimal("5000")  # Facteur standard
        dimensional_weight = Decimal("0")
        if data.length > 0 and data.width > 0 and data.height > 0:
            dimensional_weight = (data.length * data.width * data.height) / dim_factor

        billable_weight = max(data.weight, dimensional_weight)

        package = Package(
            tenant_id=self.tenant_id,
            shipment_id=shipment_id,
            package_type=data.package_type,
            length=data.length,
            width=data.width,
            height=data.height,
            weight=data.weight,
            dimensional_weight=dimensional_weight,
            billable_weight=billable_weight,
            items=data.items or [],
            declared_value=data.declared_value or Decimal("0"),
            currency=data.currency,
            label_format=data.label_format,
            created_by=created_by
        )

        return self.package_repo.create(package)

    def get_shipment(self, shipment_id: str) -> Shipment:
        """Récupérer une expédition par ID."""
        shipment = self.shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise ShipmentNotFoundError(shipment_id)
        return shipment

    def get_shipment_by_number(self, shipment_number: str) -> Shipment:
        """Récupérer une expédition par numéro."""
        shipment = self.shipment_repo.get_by_number(shipment_number)
        if not shipment:
            raise ShipmentNotFoundError(shipment_number)
        return shipment

    def get_shipment_by_tracking(self, tracking_number: str) -> Shipment:
        """Récupérer une expédition par numéro de suivi."""
        shipment = self.shipment_repo.get_by_tracking_number(tracking_number)
        if not shipment:
            raise TrackingNumberNotFoundError(tracking_number)
        return shipment

    def update_shipment(
        self,
        shipment_id: str,
        data: ShipmentUpdate,
        updated_by: str
    ) -> Shipment:
        """Mettre à jour une expédition."""
        shipment = self.get_shipment(shipment_id)

        # Vérifier que l'expédition peut être modifiée
        if shipment.status in [ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED]:
            raise ShipmentStateError(shipment.status.value, "update")

        # Mettre à jour les champs
        if data.ship_to is not None:
            shipment.ship_to = data.ship_to.model_dump()
        if data.ship_from is not None:
            shipment.ship_from = data.ship_from.model_dump()
        if data.shipping_method is not None:
            shipment.shipping_method = data.shipping_method
        if data.service_code is not None:
            shipment.service_code = data.service_code
        if data.signature_required is not None:
            shipment.signature_required = data.signature_required
        if data.saturday_delivery is not None:
            shipment.saturday_delivery = data.saturday_delivery
        if data.hold_at_location is not None:
            shipment.hold_at_location = data.hold_at_location
        if data.ship_date is not None:
            shipment.ship_date = data.ship_date
        if data.notes is not None:
            shipment.notes = data.notes
        if data.internal_notes is not None:
            shipment.internal_notes = data.internal_notes

        shipment.updated_by = updated_by

        return self.shipment_repo.update(shipment)

    def generate_label(
        self,
        shipment_id: str,
        updated_by: str
    ) -> LabelGenerationResponse:
        """Générer l'étiquette d'expédition."""
        shipment = self.get_shipment(shipment_id)

        # Vérifier le statut
        if shipment.status not in [ShipmentStatus.PENDING]:
            if shipment.master_tracking_number:
                raise LabelAlreadyGeneratedError(shipment_id)
            raise ShipmentStateError(shipment.status.value, "generate_label")

        # Récupérer le transporteur
        carrier = self.carrier_repo.get_by_id(shipment.carrier_id)
        if not carrier:
            raise CarrierNotFoundError(shipment.carrier_id)

        if not carrier.supports_labels:
            raise CarrierValidationError(
                f"Le transporteur {carrier.name} ne supporte pas la génération d'étiquettes"
            )

        # Générer le numéro de suivi principal
        tracking_number = self._generate_tracking_number(carrier.code)
        shipment.master_tracking_number = tracking_number
        shipment.status = ShipmentStatus.LABEL_CREATED

        # Construire l'URL de suivi
        if carrier.tracking_url_template:
            shipment.tracking_url = carrier.tracking_url_template.replace(
                "{tracking_number}", tracking_number
            )

        # Générer les étiquettes pour chaque colis
        packages = self.package_repo.list_by_shipment(shipment_id)
        package_labels = []

        for pkg in packages:
            pkg.tracking_number = self._generate_tracking_number(carrier.code)
            pkg.label_url = f"/api/v1/shipping/labels/{pkg.id}.pdf"
            pkg.label_generated_at = datetime.utcnow()
            pkg.updated_by = updated_by
            self.package_repo.update(pkg)

            package_labels.append({
                "package_id": str(pkg.id),
                "tracking_number": pkg.tracking_number,
                "label_url": pkg.label_url
            })

        # Ajouter un événement de suivi
        self._add_tracking_event(
            shipment,
            "label_created",
            "Étiquette créée",
            shipment.ship_from.get("city", "")
        )

        shipment.updated_by = updated_by
        shipment = self.shipment_repo.update(shipment)

        return LabelGenerationResponse(
            shipment_id=str(shipment.id),
            tracking_number=tracking_number,
            tracking_url=shipment.tracking_url,
            label_url=f"/api/v1/shipping/labels/{shipment.id}.pdf",
            packages=package_labels
        )

    def _generate_tracking_number(self, carrier_code: str) -> str:
        """Générer un numéro de suivi unique."""
        prefix = carrier_code[:2].upper() if carrier_code else "XX"
        hash_input = f"{self.tenant_id}{datetime.utcnow().isoformat()}{uuid.uuid4()}"
        hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:12].upper()
        return f"{prefix}{hash_val}"

    def _add_tracking_event(
        self,
        shipment: Shipment,
        status: str,
        description: str,
        location: str,
        event_time: Optional[datetime] = None
    ) -> None:
        """Ajouter un événement de suivi à l'expédition."""
        event = {
            "timestamp": (event_time or datetime.utcnow()).isoformat(),
            "status": status,
            "description": description,
            "location": location
        }

        if not shipment.tracking_events:
            shipment.tracking_events = []

        shipment.tracking_events.append(event)
        shipment.last_event = description
        shipment.last_event_at = event_time or datetime.utcnow()

    def update_tracking(
        self,
        shipment_id: str,
        event: TrackingEventCreate,
        updated_by: str
    ) -> Shipment:
        """Mettre à jour le suivi d'une expédition."""
        shipment = self.get_shipment(shipment_id)

        # Vérifier les transitions de statut
        if event.status:
            if not ShipmentStatus.is_valid_transition(shipment.status, event.status):
                raise ShipmentStateError(shipment.status.value, event.status.value)
            shipment.status = event.status

        # Ajouter l'événement
        self._add_tracking_event(
            shipment,
            event.status.value if event.status else shipment.status.value,
            event.description,
            event.location or "",
            event.event_time
        )

        # Mettre à jour la date de livraison si livré
        if event.status == ShipmentStatus.DELIVERED:
            shipment.actual_delivery = event.event_time or datetime.utcnow()

        shipment.updated_by = updated_by

        return self.shipment_repo.update(shipment)

    def cancel_shipment(
        self,
        shipment_id: str,
        reason: str,
        cancelled_by: str
    ) -> Shipment:
        """Annuler une expédition."""
        shipment = self.get_shipment(shipment_id)

        # Vérifier que l'expédition peut être annulée
        cancellable_statuses = [
            ShipmentStatus.PENDING,
            ShipmentStatus.LABEL_CREATED
        ]
        if shipment.status not in cancellable_statuses:
            raise ShipmentCannotBeCancelledError(shipment_id, shipment.status.value)

        shipment.status = ShipmentStatus.CANCELLED
        shipment.updated_by = cancelled_by

        self._add_tracking_event(
            shipment,
            "cancelled",
            f"Expédition annulée: {reason}",
            ""
        )

        return self.shipment_repo.update(shipment)

    def mark_picked_up(
        self,
        shipment_id: str,
        pickup_confirmation: str,
        updated_by: str
    ) -> Shipment:
        """Marquer une expédition comme enlevée."""
        shipment = self.get_shipment(shipment_id)

        if shipment.status != ShipmentStatus.LABEL_CREATED:
            raise ShipmentStateError(shipment.status.value, ShipmentStatus.PICKED_UP.value)

        shipment.status = ShipmentStatus.PICKED_UP
        shipment.pickup_confirmation = pickup_confirmation
        shipment.updated_by = updated_by

        self._add_tracking_event(
            shipment,
            "picked_up",
            "Colis enlevé",
            shipment.ship_from.get("city", "")
        )

        return self.shipment_repo.update(shipment)

    def mark_delivered(
        self,
        shipment_id: str,
        delivered_at: Optional[datetime],
        signature: Optional[str],
        updated_by: str
    ) -> Shipment:
        """Marquer une expédition comme livrée."""
        shipment = self.get_shipment(shipment_id)

        delivery_statuses = [
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.OUT_FOR_DELIVERY,
            ShipmentStatus.PICKED_UP
        ]
        if shipment.status not in delivery_statuses:
            raise ShipmentStateError(shipment.status.value, ShipmentStatus.DELIVERED.value)

        shipment.status = ShipmentStatus.DELIVERED
        shipment.actual_delivery = delivered_at or datetime.utcnow()
        if signature:
            if not shipment.extra_data:
                shipment.extra_data = {}
            shipment.extra_data["delivery_signature"] = signature
        shipment.updated_by = updated_by

        self._add_tracking_event(
            shipment,
            "delivered",
            "Colis livré",
            shipment.ship_to.get("city", ""),
            shipment.actual_delivery
        )

        return self.shipment_repo.update(shipment)

    def list_shipments(
        self,
        *,
        status: Optional[ShipmentStatus] = None,
        carrier_id: Optional[str] = None,
        order_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Shipment], int]:
        """Lister les expéditions."""
        return self.shipment_repo.list_shipments(
            status=status,
            carrier_id=carrier_id,
            order_id=order_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
            skip=skip,
            limit=limit
        )

    def get_shipment_packages(self, shipment_id: str) -> List[Package]:
        """Récupérer les colis d'une expédition."""
        self.get_shipment(shipment_id)  # Vérifier que l'expédition existe
        return self.package_repo.list_by_shipment(shipment_id)

    # ==================== Package Methods ====================

    def get_package(self, package_id: str) -> Package:
        """Récupérer un colis par ID."""
        package = self.package_repo.get_by_id(package_id)
        if not package:
            raise PackageNotFoundError(package_id)
        return package

    def update_package(
        self,
        package_id: str,
        data: PackageUpdate,
        updated_by: str
    ) -> Package:
        """Mettre à jour un colis."""
        package = self.get_package(package_id)

        # Mettre à jour les champs
        if data.package_type is not None:
            package.package_type = data.package_type
        if data.length is not None:
            package.length = data.length
        if data.width is not None:
            package.width = data.width
        if data.height is not None:
            package.height = data.height
        if data.weight is not None:
            package.weight = data.weight
        if data.items is not None:
            package.items = data.items
        if data.declared_value is not None:
            package.declared_value = data.declared_value

        # Recalculer les poids
        dim_factor = Decimal("5000")
        if package.length > 0 and package.width > 0 and package.height > 0:
            package.dimensional_weight = (
                package.length * package.width * package.height
            ) / dim_factor
        package.billable_weight = max(package.weight, package.dimensional_weight)

        package.updated_by = updated_by

        return self.package_repo.update(package)

    # ==================== PickupPoint Methods ====================

    def create_pickup_point(
        self,
        data: PickupPointCreate,
        created_by: str
    ) -> PickupPoint:
        """Créer un point relais."""
        # Vérifier que le transporteur existe
        carrier = self.carrier_repo.get_by_id(data.carrier_id)
        if not carrier:
            raise CarrierNotFoundError(data.carrier_id)

        # Vérifier l'unicité de l'external_id pour ce transporteur
        existing = self.pickup_point_repo.get_by_external_id(
            data.carrier_id, data.external_id
        )
        if existing:
            raise PickupPointDuplicateError(data.external_id)

        pickup_point = PickupPoint(
            tenant_id=self.tenant_id,
            carrier_id=data.carrier_id,
            external_id=data.external_id,
            name=data.name,
            address=data.address.model_dump() if data.address else {},
            opening_hours=data.opening_hours or {},
            is_locker=data.is_locker,
            has_parking=data.has_parking,
            wheelchair_accessible=data.wheelchair_accessible,
            latitude=data.latitude,
            longitude=data.longitude,
            is_active=data.is_active,
            created_by=created_by
        )

        return self.pickup_point_repo.create(pickup_point)

    def get_pickup_point(self, pickup_point_id: str) -> PickupPoint:
        """Récupérer un point relais par ID."""
        pickup_point = self.pickup_point_repo.get_by_id(pickup_point_id)
        if not pickup_point:
            raise PickupPointNotFoundError(pickup_point_id)
        return pickup_point

    def update_pickup_point(
        self,
        pickup_point_id: str,
        data: PickupPointUpdate,
        updated_by: str
    ) -> PickupPoint:
        """Mettre à jour un point relais."""
        pickup_point = self.get_pickup_point(pickup_point_id)

        # Mettre à jour les champs
        if data.name is not None:
            pickup_point.name = data.name
        if data.address is not None:
            pickup_point.address = data.address.model_dump()
        if data.opening_hours is not None:
            pickup_point.opening_hours = data.opening_hours
        if data.is_locker is not None:
            pickup_point.is_locker = data.is_locker
        if data.has_parking is not None:
            pickup_point.has_parking = data.has_parking
        if data.wheelchair_accessible is not None:
            pickup_point.wheelchair_accessible = data.wheelchair_accessible
        if data.latitude is not None:
            pickup_point.latitude = data.latitude
        if data.longitude is not None:
            pickup_point.longitude = data.longitude
        if data.is_active is not None:
            pickup_point.is_active = data.is_active

        pickup_point.updated_by = updated_by

        return self.pickup_point_repo.update(pickup_point)

    def delete_pickup_point(
        self,
        pickup_point_id: str,
        deleted_by: str
    ) -> PickupPoint:
        """Supprimer un point relais (soft delete)."""
        self.get_pickup_point(pickup_point_id)
        return self.pickup_point_repo.soft_delete(pickup_point_id, deleted_by)

    def search_pickup_points(
        self,
        carrier_id: str,
        country_code: str,
        postal_code: str,
        *,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None,
        max_results: int = 10,
        max_distance_km: Decimal = Decimal("20")
    ) -> List[PickupPoint]:
        """Rechercher des points relais."""
        return self.pickup_point_repo.search_nearby(
            carrier_id=carrier_id,
            country_code=country_code,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            max_results=max_results,
            max_distance_km=max_distance_km
        )

    def list_pickup_points(
        self,
        *,
        carrier_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_locker: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[PickupPoint], int]:
        """Lister les points relais."""
        return self.pickup_point_repo.list_pickup_points(
            carrier_id=carrier_id,
            is_active=is_active,
            is_locker=is_locker,
            skip=skip,
            limit=limit
        )

    # ==================== Return Methods ====================

    def create_return(
        self,
        data: ReturnCreate,
        created_by: str
    ) -> Return:
        """Créer une demande de retour."""
        # Vérifier que l'expédition existe
        shipment = self.shipment_repo.get_by_id(data.shipment_id)
        if not shipment:
            raise ShipmentNotFoundError(data.shipment_id)

        # Vérifier que l'expédition a été livrée
        if shipment.status != ShipmentStatus.DELIVERED:
            raise ShipmentValidationError(
                "L'expédition doit être livrée pour créer un retour"
            )

        # Générer le numéro de retour
        return_number = self.return_repo.get_next_number()

        ret = Return(
            tenant_id=self.tenant_id,
            return_number=return_number,
            order_id=data.order_id,
            shipment_id=data.shipment_id,
            status=ReturnStatus.REQUESTED,
            reason=data.reason,
            reason_code=data.reason_code,
            customer_notes=data.customer_notes,
            items=data.items or [],
            return_address=shipment.ship_from,  # Adresse de retour = origine de l'expédition
            requested_at=datetime.utcnow(),
            created_by=created_by
        )

        return self.return_repo.create(ret)

    def get_return(self, return_id: str) -> Return:
        """Récupérer un retour par ID."""
        ret = self.return_repo.get_by_id(return_id)
        if not ret:
            raise ReturnNotFoundError(return_id)
        return ret

    def get_return_by_number(self, return_number: str) -> Return:
        """Récupérer un retour par numéro."""
        ret = self.return_repo.get_by_number(return_number)
        if not ret:
            raise ReturnNotFoundError(return_number)
        return ret

    def approve_return(
        self,
        return_id: str,
        approved_by: str
    ) -> Return:
        """Approuver une demande de retour."""
        ret = self.get_return(return_id)

        if ret.status != ReturnStatus.REQUESTED:
            if ret.status == ReturnStatus.APPROVED:
                raise ReturnAlreadyApprovedError(return_id)
            raise ReturnStateError(ret.status.value, ReturnStatus.APPROVED.value)

        ret.status = ReturnStatus.APPROVED
        ret.approved_at = datetime.utcnow()
        ret.updated_by = approved_by

        return self.return_repo.update(ret)

    def reject_return(
        self,
        return_id: str,
        rejection_reason: str,
        rejected_by: str
    ) -> Return:
        """Rejeter une demande de retour."""
        ret = self.get_return(return_id)

        if ret.status != ReturnStatus.REQUESTED:
            raise ReturnStateError(ret.status.value, ReturnStatus.REJECTED.value)

        ret.status = ReturnStatus.REJECTED
        ret.inspection_notes = rejection_reason
        ret.updated_by = rejected_by

        return self.return_repo.update(ret)

    def generate_return_label(
        self,
        return_id: str,
        updated_by: str
    ) -> Dict[str, Any]:
        """Générer l'étiquette de retour."""
        ret = self.get_return(return_id)

        if ret.status != ReturnStatus.APPROVED:
            raise ReturnNotApprovedError(return_id)

        # Récupérer l'expédition originale
        shipment = self.shipment_repo.get_by_id(ret.shipment_id)
        if not shipment:
            raise ShipmentNotFoundError(ret.shipment_id)

        # Récupérer le transporteur
        carrier = self.carrier_repo.get_by_id(shipment.carrier_id)
        if not carrier:
            raise CarrierNotFoundError(shipment.carrier_id)

        if not carrier.supports_returns:
            raise CarrierValidationError(
                f"Le transporteur {carrier.name} ne supporte pas les retours"
            )

        # Générer le numéro de suivi
        tracking_number = self._generate_tracking_number(carrier.code)

        ret.return_carrier_id = shipment.carrier_id
        ret.return_tracking_number = tracking_number
        ret.return_label_url = f"/api/v1/shipping/return-labels/{return_id}.pdf"
        ret.status = ReturnStatus.LABEL_SENT
        ret.updated_by = updated_by

        self.return_repo.update(ret)

        return {
            "return_id": str(ret.id),
            "tracking_number": tracking_number,
            "label_url": ret.return_label_url
        }

    def receive_return(
        self,
        return_id: str,
        condition: str,
        inspection_notes: str,
        received_by: str
    ) -> Return:
        """Réceptionner un retour."""
        ret = self.get_return(return_id)

        valid_statuses = [ReturnStatus.LABEL_SENT, ReturnStatus.IN_TRANSIT]
        if ret.status not in valid_statuses:
            raise ReturnStateError(ret.status.value, ReturnStatus.RECEIVED.value)

        ret.status = ReturnStatus.RECEIVED
        ret.received_at = datetime.utcnow()
        ret.condition = condition
        ret.inspection_notes = inspection_notes
        ret.updated_by = received_by

        return self.return_repo.update(ret)

    def inspect_return(
        self,
        return_id: str,
        condition: str,
        inspection_notes: str,
        inspected_by: str
    ) -> Return:
        """Inspecter un retour reçu."""
        ret = self.get_return(return_id)

        if ret.status != ReturnStatus.RECEIVED:
            raise ReturnNotReceivedError(return_id)

        ret.status = ReturnStatus.INSPECTED
        ret.inspected_at = datetime.utcnow()
        ret.condition = condition
        ret.inspection_notes = inspection_notes
        ret.updated_by = inspected_by

        return self.return_repo.update(ret)

    def process_refund(
        self,
        return_id: str,
        refund_amount: Decimal,
        refund_method: str,
        *,
        restocking_fee: Decimal = Decimal("0"),
        refund_reference: Optional[str] = None,
        processed_by: str
    ) -> Return:
        """Traiter le remboursement d'un retour."""
        ret = self.get_return(return_id)

        if ret.status == ReturnStatus.REFUNDED:
            raise ReturnAlreadyRefundedError(return_id)

        if ret.status == ReturnStatus.REJECTED:
            raise ReturnRejectedError(return_id)

        valid_statuses = [ReturnStatus.RECEIVED, ReturnStatus.INSPECTED]
        if ret.status not in valid_statuses:
            raise ReturnNotReceivedError(return_id)

        ret.status = ReturnStatus.REFUNDED
        ret.refund_amount = refund_amount
        ret.refund_method = refund_method
        ret.restocking_fee = restocking_fee
        ret.refund_reference = refund_reference
        ret.completed_at = datetime.utcnow()
        ret.processed_by = processed_by
        ret.updated_by = processed_by

        return self.return_repo.update(ret)

    def list_returns(
        self,
        *,
        status: Optional[ReturnStatus] = None,
        order_id: Optional[str] = None,
        shipment_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Return], int]:
        """Lister les retours."""
        return self.return_repo.list_returns(
            status=status,
            order_id=order_id,
            shipment_id=shipment_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )

    # ==================== Statistics Methods ====================

    def get_shipping_stats(
        self,
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """Calculer les statistiques d'expédition."""
        # Récupérer toutes les expéditions de la période
        shipments, total = self.shipment_repo.list_shipments(
            start_date=period_start,
            end_date=period_end,
            limit=10000
        )

        # Comptages par statut
        status_counts = {}
        for status in ShipmentStatus:
            status_counts[status.value] = len([
                s for s in shipments if s.status == status
            ])

        # Calculs de performance
        delivered = [s for s in shipments if s.status == ShipmentStatus.DELIVERED]
        on_time = 0
        total_delivery_days = Decimal("0")

        for s in delivered:
            if s.actual_delivery and s.ship_date:
                delivery_days = (s.actual_delivery.date() - s.ship_date).days
                total_delivery_days += delivery_days
                if s.estimated_delivery and s.actual_delivery.date() <= s.estimated_delivery:
                    on_time += 1

        on_time_rate = (
            Decimal(on_time) / Decimal(len(delivered)) * 100
        ) if delivered else Decimal("0")

        avg_delivery_days = (
            total_delivery_days / len(delivered)
        ) if delivered else Decimal("0")

        # Coûts
        total_cost = sum(s.total_cost for s in shipments)
        avg_cost = total_cost / len(shipments) if shipments else Decimal("0")

        # Par transporteur
        by_carrier: Dict[str, int] = {}
        cost_by_carrier: Dict[str, Decimal] = {}
        for s in shipments:
            carrier_name = s.carrier_name or "Unknown"
            by_carrier[carrier_name] = by_carrier.get(carrier_name, 0) + 1
            cost_by_carrier[carrier_name] = (
                cost_by_carrier.get(carrier_name, Decimal("0")) + s.total_cost
            )

        # Par méthode
        by_method: Dict[str, int] = {}
        for s in shipments:
            method = s.shipping_method.value
            by_method[method] = by_method.get(method, 0) + 1

        # Retours
        returns, return_count = self.return_repo.list_returns(
            start_date=period_start,
            end_date=period_end,
            limit=10000
        )
        return_rate = (
            Decimal(return_count) / Decimal(total) * 100
        ) if total > 0 else Decimal("0")

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_shipments": total,
            "total_packages": sum(s.total_packages for s in shipments),
            "total_weight_kg": sum(s.total_weight for s in shipments),
            "status_counts": status_counts,
            "on_time_delivery_rate": float(on_time_rate),
            "avg_delivery_days": float(avg_delivery_days),
            "total_shipping_cost": float(total_cost),
            "avg_cost_per_shipment": float(avg_cost),
            "shipments_by_carrier": by_carrier,
            "cost_by_carrier": {k: float(v) for k, v in cost_by_carrier.items()},
            "shipments_by_method": by_method,
            "total_returns": return_count,
            "return_rate": float(return_rate)
        }


# ============== Factory ==============

def create_shipping_service(session: Session, tenant_id: str) -> ShippingService:
    """Factory pour créer une instance du service."""
    return ShippingService(session, tenant_id)
