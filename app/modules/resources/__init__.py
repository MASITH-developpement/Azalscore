"""
Module Resources / Réservation - GAP-071
========================================

Gestion des réservations de ressources:
- Salles de réunion
- Équipements
- Véhicules de service
- Espaces de travail
- Calendrier de disponibilité
- Récurrence
- Conflits et approbations
"""

# Models
from .models import (
    ResourceType,
    ResourceStatus,
    BookingStatus,
    RecurrenceType,
    ApprovalStatus,
    WaitlistStatus,
    ResourceLocation,
    Amenity,
    Resource,
    Booking,
    BlockedSlot,
    WaitlistEntry,
)

# Alias for compatibility
Location = ResourceLocation

# Schemas
from .schemas import (
    LocationCreate, LocationUpdate, LocationResponse, LocationListResponse,
    AmenityCreate, AmenityUpdate, AmenityResponse, AmenityListResponse,
    ResourceCreate, ResourceUpdate, ResourceResponse, ResourceListResponse, ResourceFilters,
    RecurrenceRule,
    BookingCreate, BookingUpdate, BookingResponse, BookingListResponse, BookingFilters,
    BlockedSlotCreate, BlockedSlotUpdate, BlockedSlotResponse, BlockedSlotListResponse,
    WaitlistCreate, WaitlistResponse, WaitlistListResponse,
    AvailabilitySlot, AvailabilityRequest, AvailabilityResponse,
    ResourceUtilization,
    AutocompleteResponse, BulkResult,
)

# Exceptions
from .exceptions import (
    ResourceError,
    LocationNotFoundError, LocationDuplicateError, LocationValidationError,
    AmenityNotFoundError, AmenityDuplicateError,
    ResourceNotFoundError, ResourceDuplicateError, ResourceValidationError,
    ResourceUnavailableError, ResourceInMaintenanceError,
    BookingNotFoundError, BookingValidationError, BookingStateError,
    BookingConflictError, BookingCapacityExceededError,
    BookingDurationError, BookingAdvanceError, BookingAccessDeniedError,
    BookingApprovalRequiredError, BookingAlreadyCheckedInError, BookingNotCheckedInError,
    BlockedSlotNotFoundError, BlockedSlotValidationError,
    WaitlistEntryNotFoundError, WaitlistValidationError, WaitlistExpiredError,
    RecurrenceValidationError, RecurrenceConflictError,
)

# Repository
from .repository import (
    LocationRepository,
    AmenityRepository,
    ResourceRepository,
    BookingRepository,
    BlockedSlotRepository,
    WaitlistRepository,
)

# Service
from .service import ResourceService

# Router
from .router import router


__all__ = [
    # Enums
    "ResourceType", "ResourceStatus", "BookingStatus",
    "RecurrenceType", "ApprovalStatus", "WaitlistStatus",
    # Models
    "Location", "Amenity", "Resource", "Booking", "BlockedSlot", "WaitlistEntry",
    # Schemas
    "LocationCreate", "LocationUpdate", "LocationResponse", "LocationListResponse",
    "AmenityCreate", "AmenityUpdate", "AmenityResponse", "AmenityListResponse",
    "ResourceCreate", "ResourceUpdate", "ResourceResponse", "ResourceListResponse", "ResourceFilters",
    "RecurrenceRule",
    "BookingCreate", "BookingUpdate", "BookingResponse", "BookingListResponse", "BookingFilters",
    "BlockedSlotCreate", "BlockedSlotUpdate", "BlockedSlotResponse", "BlockedSlotListResponse",
    "WaitlistCreate", "WaitlistResponse", "WaitlistListResponse",
    "AvailabilitySlot", "AvailabilityRequest", "AvailabilityResponse",
    "ResourceUtilization", "AutocompleteResponse", "BulkResult",
    # Exceptions
    "ResourceError",
    "LocationNotFoundError", "LocationDuplicateError", "LocationValidationError",
    "AmenityNotFoundError", "AmenityDuplicateError",
    "ResourceNotFoundError", "ResourceDuplicateError", "ResourceValidationError",
    "ResourceUnavailableError", "ResourceInMaintenanceError",
    "BookingNotFoundError", "BookingValidationError", "BookingStateError",
    "BookingConflictError", "BookingCapacityExceededError",
    "BookingDurationError", "BookingAdvanceError", "BookingAccessDeniedError",
    "BookingApprovalRequiredError", "BookingAlreadyCheckedInError", "BookingNotCheckedInError",
    "BlockedSlotNotFoundError", "BlockedSlotValidationError",
    "WaitlistEntryNotFoundError", "WaitlistValidationError", "WaitlistExpiredError",
    "RecurrenceValidationError", "RecurrenceConflictError",
    # Repository
    "LocationRepository", "AmenityRepository", "ResourceRepository",
    "BookingRepository", "BlockedSlotRepository", "WaitlistRepository",
    # Service
    "ResourceService",
    # Router
    "router",
]
