"""
Exceptions Shipping / Expédition - GAP-078
==========================================
"""


class ShippingError(Exception):
    """Exception de base pour le module Shipping."""
    pass


# ============== Zone Exceptions ==============

class ZoneNotFoundError(ShippingError):
    """Zone non trouvée."""
    def __init__(self, zone_id: str):
        self.zone_id = zone_id
        super().__init__(f"Zone non trouvée: {zone_id}")


class ZoneDuplicateError(ShippingError):
    """Code zone déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code zone déjà utilisé: {code}")


class ZoneValidationError(ShippingError):
    """Erreur de validation zone."""
    def __init__(self, message: str):
        super().__init__(message)


class ZoneInUseError(ShippingError):
    """Zone utilisée par des tarifs."""
    def __init__(self, zone_id: str, rate_count: int):
        self.zone_id = zone_id
        self.rate_count = rate_count
        super().__init__(f"Zone utilisée par {rate_count} tarif(s)")


# ============== Carrier Exceptions ==============

class CarrierNotFoundError(ShippingError):
    """Transporteur non trouvé."""
    def __init__(self, carrier_id: str):
        self.carrier_id = carrier_id
        super().__init__(f"Transporteur non trouvé: {carrier_id}")


class CarrierDuplicateError(ShippingError):
    """Code transporteur déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code transporteur déjà utilisé: {code}")


class CarrierValidationError(ShippingError):
    """Erreur de validation transporteur."""
    def __init__(self, message: str):
        super().__init__(message)


class CarrierInactiveError(ShippingError):
    """Transporteur désactivé."""
    def __init__(self, carrier_id: str):
        self.carrier_id = carrier_id
        super().__init__(f"Transporteur désactivé: {carrier_id}")


class CarrierInUseError(ShippingError):
    """Transporteur utilisé par des expéditions."""
    def __init__(self, carrier_id: str, shipment_count: int):
        self.carrier_id = carrier_id
        self.shipment_count = shipment_count
        super().__init__(f"Transporteur utilisé par {shipment_count} expédition(s)")


class CarrierApiError(ShippingError):
    """Erreur API transporteur."""
    def __init__(self, carrier_id: str, message: str):
        self.carrier_id = carrier_id
        super().__init__(f"Erreur API transporteur {carrier_id}: {message}")


# ============== ShippingRate Exceptions ==============

class RateNotFoundError(ShippingError):
    """Tarif non trouvé."""
    def __init__(self, rate_id: str):
        self.rate_id = rate_id
        super().__init__(f"Tarif non trouvé: {rate_id}")


class RateDuplicateError(ShippingError):
    """Code tarif déjà utilisé."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Code tarif déjà utilisé: {code}")


class RateValidationError(ShippingError):
    """Erreur de validation tarif."""
    def __init__(self, message: str):
        super().__init__(message)


class RateExpiredError(ShippingError):
    """Tarif expiré."""
    def __init__(self, rate_id: str):
        self.rate_id = rate_id
        super().__init__(f"Tarif expiré: {rate_id}")


class NoRateAvailableError(ShippingError):
    """Aucun tarif disponible."""
    def __init__(self, destination: str):
        self.destination = destination
        super().__init__(f"Aucun tarif disponible pour: {destination}")


# ============== Shipment Exceptions ==============

class ShipmentNotFoundError(ShippingError):
    """Expédition non trouvée."""
    def __init__(self, shipment_id: str):
        self.shipment_id = shipment_id
        super().__init__(f"Expédition non trouvée: {shipment_id}")


class ShipmentDuplicateError(ShippingError):
    """Numéro d'expédition déjà utilisé."""
    def __init__(self, number: str):
        self.number = number
        super().__init__(f"Numéro d'expédition déjà utilisé: {number}")


class ShipmentValidationError(ShippingError):
    """Erreur de validation expédition."""
    def __init__(self, message: str):
        super().__init__(message)


class ShipmentStateError(ShippingError):
    """Erreur de transition d'état expédition."""
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition non autorisée: {current_status} -> {target_status}"
        )


class ShipmentCancelledError(ShippingError):
    """Expédition annulée."""
    def __init__(self, shipment_id: str):
        self.shipment_id = shipment_id
        super().__init__(f"Expédition annulée: {shipment_id}")


class ShipmentDeliveredError(ShippingError):
    """Expédition déjà livrée."""
    def __init__(self, shipment_id: str):
        self.shipment_id = shipment_id
        super().__init__(f"Expédition déjà livrée: {shipment_id}")


class ShipmentCannotBeCancelledError(ShippingError):
    """Expédition ne peut pas être annulée."""
    def __init__(self, shipment_id: str, status: str):
        self.shipment_id = shipment_id
        self.status = status
        super().__init__(f"Impossible d'annuler l'expédition en statut: {status}")


class LabelAlreadyGeneratedError(ShippingError):
    """Étiquette déjà générée."""
    def __init__(self, shipment_id: str):
        self.shipment_id = shipment_id
        super().__init__(f"Étiquette déjà générée pour l'expédition: {shipment_id}")


class LabelNotGeneratedError(ShippingError):
    """Étiquette non générée."""
    def __init__(self, shipment_id: str):
        self.shipment_id = shipment_id
        super().__init__(f"Étiquette non générée pour l'expédition: {shipment_id}")


class TrackingNumberNotFoundError(ShippingError):
    """Numéro de suivi non trouvé."""
    def __init__(self, tracking_number: str):
        self.tracking_number = tracking_number
        super().__init__(f"Numéro de suivi non trouvé: {tracking_number}")


# ============== Package Exceptions ==============

class PackageNotFoundError(ShippingError):
    """Colis non trouvé."""
    def __init__(self, package_id: str):
        self.package_id = package_id
        super().__init__(f"Colis non trouvé: {package_id}")


class PackageValidationError(ShippingError):
    """Erreur de validation colis."""
    def __init__(self, message: str):
        super().__init__(message)


class PackageWeightExceededError(ShippingError):
    """Poids du colis dépassé."""
    def __init__(self, weight: str, max_weight: str):
        self.weight = weight
        self.max_weight = max_weight
        super().__init__(f"Poids dépassé: {weight} kg (max: {max_weight} kg)")


class PackageDimensionsExceededError(ShippingError):
    """Dimensions du colis dépassées."""
    def __init__(self, dimension: str, value: str, max_value: str):
        self.dimension = dimension
        self.value = value
        self.max_value = max_value
        super().__init__(f"Dimension {dimension} dépassée: {value} cm (max: {max_value} cm)")


# ============== PickupPoint Exceptions ==============

class PickupPointNotFoundError(ShippingError):
    """Point relais non trouvé."""
    def __init__(self, point_id: str):
        self.point_id = point_id
        super().__init__(f"Point relais non trouvé: {point_id}")


class PickupPointDuplicateError(ShippingError):
    """Point relais déjà existant."""
    def __init__(self, external_id: str):
        self.external_id = external_id
        super().__init__(f"Point relais déjà existant: {external_id}")


class PickupPointValidationError(ShippingError):
    """Erreur de validation point relais."""
    def __init__(self, message: str):
        super().__init__(message)


class PickupPointInactiveError(ShippingError):
    """Point relais désactivé."""
    def __init__(self, point_id: str):
        self.point_id = point_id
        super().__init__(f"Point relais désactivé: {point_id}")


# ============== Return Exceptions ==============

class ReturnNotFoundError(ShippingError):
    """Retour non trouvé."""
    def __init__(self, return_id: str):
        self.return_id = return_id
        super().__init__(f"Retour non trouvé: {return_id}")


class ReturnDuplicateError(ShippingError):
    """Numéro de retour déjà utilisé."""
    def __init__(self, number: str):
        self.number = number
        super().__init__(f"Numéro de retour déjà utilisé: {number}")


class ReturnValidationError(ShippingError):
    """Erreur de validation retour."""
    def __init__(self, message: str):
        super().__init__(message)


class ReturnStateError(ShippingError):
    """Erreur de transition d'état retour."""
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transition non autorisée: {current_status} -> {target_status}"
        )


class ReturnAlreadyApprovedError(ShippingError):
    """Retour déjà approuvé."""
    def __init__(self, return_id: str):
        self.return_id = return_id
        super().__init__(f"Retour déjà approuvé: {return_id}")


class ReturnAlreadyRefundedError(ShippingError):
    """Retour déjà remboursé."""
    def __init__(self, return_id: str):
        self.return_id = return_id
        super().__init__(f"Retour déjà remboursé: {return_id}")


class ReturnNotApprovedError(ShippingError):
    """Retour non approuvé."""
    def __init__(self, return_id: str):
        self.return_id = return_id
        super().__init__(f"Retour non approuvé: {return_id}")


class ReturnNotReceivedError(ShippingError):
    """Retour non reçu."""
    def __init__(self, return_id: str):
        self.return_id = return_id
        super().__init__(f"Retour non reçu: {return_id}")


class ReturnRejectedError(ShippingError):
    """Retour rejeté."""
    def __init__(self, return_id: str):
        self.return_id = return_id
        super().__init__(f"Retour rejeté: {return_id}")


# ============== Address Exceptions ==============

class AddressValidationError(ShippingError):
    """Erreur de validation adresse."""
    def __init__(self, message: str):
        super().__init__(message)


class AddressNotServiceableError(ShippingError):
    """Adresse non desservie."""
    def __init__(self, address: str):
        self.address = address
        super().__init__(f"Adresse non desservie: {address}")
