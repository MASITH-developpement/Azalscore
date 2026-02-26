"""
Module Shipping / Expédition - GAP-078

Gestion des expéditions:
- Transporteurs multiples
- Calcul de tarifs
- Génération d'étiquettes
- Suivi des colis
- Zones de livraison
- Points relais
- Retours et réclamations
"""

from .models import (
    # Enums
    CarrierType,
    ShippingMethod,
    ShipmentStatus,
    PackageType,
    ReturnStatus,
    RateCalculation,
    # Models
    Zone,
    Carrier,
    ShippingRate,
    Shipment,
    Package,
    PickupPoint,
    Return,
)

from .schemas import (
    # Address
    AddressSchema,
    # Zone
    ZoneCreate,
    ZoneUpdate,
    ZoneResponse,
    ZoneListResponse,
    # Carrier
    CarrierCreate,
    CarrierUpdate,
    CarrierResponse,
    CarrierListResponse,
    # Rate
    RateCreate,
    RateUpdate,
    RateResponse,
    RateListResponse,
    RateQuoteRequest,
    RateQuoteResponse,
    RateCalculationRequest,
    RateCalculationResponse,
    ShippingRateCreate,
    ShippingRateUpdate,
    ShippingRateResponse,
    ShippingRateListResponse,
    # Shipment
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    ShipmentListResponse,
    TrackingEventCreate,
    TrackingEventSchema,
    TrackingUpdateRequest,
    LabelGenerationResponse,
    # Package
    PackageCreate,
    PackageUpdate,
    PackageResponse,
    # PickupPoint
    PickupPointCreate,
    PickupPointUpdate,
    PickupPointResponse,
    PickupPointListResponse,
    PickupPointSearchRequest,
    # Return
    ReturnCreate,
    ReturnUpdate,
    ReturnResponse,
    ReturnListResponse,
    ReturnRefundRequest,
    RefundRequest,
    ReturnApprovalRequest,
    ReturnReceiptRequest,
    # Stats
    ShippingStatsRequest,
    ShippingStatsResponse,
    # Utils
    AutocompleteResponse,
    BulkResult,
)

from .repository import (
    ZoneRepository,
    CarrierRepository,
    ShippingRateRepository,
    ShipmentRepository,
    PackageRepository,
    PickupPointRepository,
    ReturnRepository,
)

from .service import (
    ShippingService,
    create_shipping_service,
)

from .router import router

from .exceptions import (
    ShippingError,
    # Zone
    ZoneNotFoundError,
    ZoneDuplicateError,
    ZoneValidationError,
    ZoneInUseError,
    # Carrier
    CarrierNotFoundError,
    CarrierDuplicateError,
    CarrierValidationError,
    CarrierInactiveError,
    CarrierInUseError,
    CarrierApiError,
    # Rate
    RateNotFoundError,
    RateDuplicateError,
    RateValidationError,
    RateExpiredError,
    NoRateAvailableError,
    # Shipment
    ShipmentNotFoundError,
    ShipmentDuplicateError,
    ShipmentValidationError,
    ShipmentStateError,
    ShipmentCancelledError,
    ShipmentDeliveredError,
    ShipmentCannotBeCancelledError,
    LabelAlreadyGeneratedError,
    LabelNotGeneratedError,
    TrackingNumberNotFoundError,
    # Package
    PackageNotFoundError,
    PackageValidationError,
    PackageWeightExceededError,
    PackageDimensionsExceededError,
    # PickupPoint
    PickupPointNotFoundError,
    PickupPointDuplicateError,
    PickupPointValidationError,
    PickupPointInactiveError,
    # Return
    ReturnNotFoundError,
    ReturnDuplicateError,
    ReturnValidationError,
    ReturnStateError,
    ReturnAlreadyApprovedError,
    ReturnAlreadyRefundedError,
    ReturnNotApprovedError,
    ReturnNotReceivedError,
    ReturnRejectedError,
    # Address
    AddressValidationError,
    AddressNotServiceableError,
)


__all__ = [
    # Enums
    "CarrierType",
    "ShippingMethod",
    "ShipmentStatus",
    "PackageType",
    "ReturnStatus",
    "RateCalculation",
    # Models
    "Zone",
    "Carrier",
    "ShippingRate",
    "Shipment",
    "Package",
    "PickupPoint",
    "Return",
    # Schemas - Address
    "AddressSchema",
    # Schemas - Zone
    "ZoneCreate",
    "ZoneUpdate",
    "ZoneResponse",
    "ZoneListResponse",
    # Schemas - Carrier
    "CarrierCreate",
    "CarrierUpdate",
    "CarrierResponse",
    "CarrierListResponse",
    # Schemas - Rate
    "RateCreate",
    "RateUpdate",
    "RateResponse",
    "RateListResponse",
    "RateQuoteRequest",
    "RateQuoteResponse",
    "RateCalculationRequest",
    "RateCalculationResponse",
    "ShippingRateCreate",
    "ShippingRateUpdate",
    "ShippingRateResponse",
    "ShippingRateListResponse",
    # Schemas - Shipment
    "ShipmentCreate",
    "ShipmentUpdate",
    "ShipmentResponse",
    "ShipmentListResponse",
    "TrackingEventCreate",
    "TrackingEventSchema",
    "TrackingUpdateRequest",
    "LabelGenerationResponse",
    # Schemas - Package
    "PackageCreate",
    "PackageUpdate",
    "PackageResponse",
    # Schemas - PickupPoint
    "PickupPointCreate",
    "PickupPointUpdate",
    "PickupPointResponse",
    "PickupPointListResponse",
    "PickupPointSearchRequest",
    # Schemas - Return
    "ReturnCreate",
    "ReturnUpdate",
    "ReturnResponse",
    "ReturnListResponse",
    "ReturnRefundRequest",
    "RefundRequest",
    "ReturnApprovalRequest",
    "ReturnReceiptRequest",
    # Schemas - Stats
    "ShippingStatsRequest",
    "ShippingStatsResponse",
    # Schemas - Utils
    "AutocompleteResponse",
    "BulkResult",
    # Repositories
    "ZoneRepository",
    "CarrierRepository",
    "ShippingRateRepository",
    "ShipmentRepository",
    "PackageRepository",
    "PickupPointRepository",
    "ReturnRepository",
    # Service
    "ShippingService",
    "create_shipping_service",
    # Router
    "router",
    # Exceptions
    "ShippingError",
    "ZoneNotFoundError",
    "ZoneDuplicateError",
    "ZoneValidationError",
    "ZoneInUseError",
    "CarrierNotFoundError",
    "CarrierDuplicateError",
    "CarrierValidationError",
    "CarrierInactiveError",
    "CarrierInUseError",
    "CarrierApiError",
    "RateNotFoundError",
    "RateDuplicateError",
    "RateValidationError",
    "RateExpiredError",
    "NoRateAvailableError",
    "ShipmentNotFoundError",
    "ShipmentDuplicateError",
    "ShipmentValidationError",
    "ShipmentStateError",
    "ShipmentCancelledError",
    "ShipmentDeliveredError",
    "ShipmentCannotBeCancelledError",
    "LabelAlreadyGeneratedError",
    "LabelNotGeneratedError",
    "TrackingNumberNotFoundError",
    "PackageNotFoundError",
    "PackageValidationError",
    "PackageWeightExceededError",
    "PackageDimensionsExceededError",
    "PickupPointNotFoundError",
    "PickupPointDuplicateError",
    "PickupPointValidationError",
    "PickupPointInactiveError",
    "ReturnNotFoundError",
    "ReturnDuplicateError",
    "ReturnValidationError",
    "ReturnStateError",
    "ReturnAlreadyApprovedError",
    "ReturnAlreadyRefundedError",
    "ReturnNotApprovedError",
    "ReturnNotReceivedError",
    "ReturnRejectedError",
    "AddressValidationError",
    "AddressNotServiceableError",
]
