"""
Exceptions metier - Module Fleet Management (GAP-062)

Gestion des erreurs specifiques au module de gestion de flotte.
"""


class FleetError(Exception):
    """Exception de base du module Fleet."""
    pass


# ============== Vehicle Exceptions ==============

class VehicleNotFoundError(FleetError):
    """Vehicule non trouve."""
    def __init__(self, vehicle_id: str = None, code: str = None):
        if vehicle_id:
            message = f"Vehicle with ID {vehicle_id} not found"
        elif code:
            message = f"Vehicle with code {code} not found"
        else:
            message = "Vehicle not found"
        super().__init__(message)


class VehicleDuplicateError(FleetError):
    """Code ou immatriculation vehicule deja existant."""
    def __init__(self, field: str, value: str):
        super().__init__(f"Vehicle with {field} '{value}' already exists")


class VehicleValidationError(FleetError):
    """Erreur de validation vehicule."""
    pass


class VehicleStateError(FleetError):
    """Etat du vehicule incompatible avec l'operation."""
    def __init__(self, current_status: str, operation: str):
        super().__init__(f"Cannot {operation} vehicle in status '{current_status}'")


class VehicleInUseError(FleetError):
    """Vehicule en cours d'utilisation."""
    def __init__(self, vehicle_id: str):
        super().__init__(f"Vehicle {vehicle_id} is currently in use")


class VehicleAssignedError(FleetError):
    """Vehicule deja assigne."""
    def __init__(self, vehicle_id: str, driver_id: str):
        super().__init__(f"Vehicle {vehicle_id} is already assigned to driver {driver_id}")


# ============== Driver Exceptions ==============

class DriverNotFoundError(FleetError):
    """Conducteur non trouve."""
    def __init__(self, driver_id: str = None, code: str = None):
        if driver_id:
            message = f"Driver with ID {driver_id} not found"
        elif code:
            message = f"Driver with code {code} not found"
        else:
            message = "Driver not found"
        super().__init__(message)


class DriverDuplicateError(FleetError):
    """Code conducteur deja existant."""
    def __init__(self, code: str):
        super().__init__(f"Driver with code '{code}' already exists")


class DriverValidationError(FleetError):
    """Erreur de validation conducteur."""
    pass


class DriverLicenseExpiredError(FleetError):
    """Permis de conduire expire."""
    def __init__(self, driver_id: str, expiry_date: str):
        super().__init__(f"Driver {driver_id} license expired on {expiry_date}")


class DriverAlreadyAssignedError(FleetError):
    """Conducteur deja assigne a un vehicule."""
    def __init__(self, driver_id: str, vehicle_id: str):
        super().__init__(f"Driver {driver_id} is already assigned to vehicle {vehicle_id}")


# ============== Contract Exceptions ==============

class ContractNotFoundError(FleetError):
    """Contrat non trouve."""
    def __init__(self, contract_id: str = None, code: str = None):
        if contract_id:
            message = f"Contract with ID {contract_id} not found"
        elif code:
            message = f"Contract with code {code} not found"
        else:
            message = "Contract not found"
        super().__init__(message)


class ContractDuplicateError(FleetError):
    """Code contrat deja existant."""
    def __init__(self, code: str):
        super().__init__(f"Contract with code '{code}' already exists")


class ContractValidationError(FleetError):
    """Erreur de validation contrat."""
    pass


class ContractExpiredError(FleetError):
    """Contrat expire."""
    def __init__(self, contract_id: str):
        super().__init__(f"Contract {contract_id} has expired")


class ContractOverlapError(FleetError):
    """Chevauchement de contrats."""
    def __init__(self, vehicle_id: str, contract_type: str):
        super().__init__(f"Vehicle {vehicle_id} already has an active {contract_type} contract")


# ============== Maintenance Exceptions ==============

class MaintenanceNotFoundError(FleetError):
    """Maintenance non trouvee."""
    def __init__(self, maintenance_id: str = None, code: str = None):
        if maintenance_id:
            message = f"Maintenance with ID {maintenance_id} not found"
        elif code:
            message = f"Maintenance with code {code} not found"
        else:
            message = "Maintenance not found"
        super().__init__(message)


class MaintenanceDuplicateError(FleetError):
    """Code maintenance deja existant."""
    def __init__(self, code: str):
        super().__init__(f"Maintenance with code '{code}' already exists")


class MaintenanceValidationError(FleetError):
    """Erreur de validation maintenance."""
    pass


class MaintenanceStateError(FleetError):
    """Transition d'etat invalide."""
    def __init__(self, current_status: str, new_status: str):
        super().__init__(f"Invalid transition from {current_status} to {new_status}")


# ============== Fuel Entry Exceptions ==============

class FuelEntryNotFoundError(FleetError):
    """Entree carburant non trouvee."""
    def __init__(self, entry_id: str):
        super().__init__(f"Fuel entry with ID {entry_id} not found")


class FuelEntryValidationError(FleetError):
    """Erreur de validation entree carburant."""
    pass


class FuelAnomalyError(FleetError):
    """Anomalie de consommation detectee."""
    def __init__(self, reason: str):
        super().__init__(f"Fuel anomaly detected: {reason}")


# ============== Document Exceptions ==============

class DocumentNotFoundError(FleetError):
    """Document non trouve."""
    def __init__(self, document_id: str):
        super().__init__(f"Document with ID {document_id} not found")


class DocumentValidationError(FleetError):
    """Erreur de validation document."""
    pass


class DocumentExpiredError(FleetError):
    """Document expire."""
    def __init__(self, document_id: str, document_type: str, expiry_date: str):
        super().__init__(f"{document_type} document {document_id} expired on {expiry_date}")


# ============== Incident Exceptions ==============

class IncidentNotFoundError(FleetError):
    """Incident non trouve."""
    def __init__(self, incident_id: str = None, code: str = None):
        if incident_id:
            message = f"Incident with ID {incident_id} not found"
        elif code:
            message = f"Incident with code {code} not found"
        else:
            message = "Incident not found"
        super().__init__(message)


class IncidentDuplicateError(FleetError):
    """Code incident deja existant."""
    def __init__(self, code: str):
        super().__init__(f"Incident with code '{code}' already exists")


class IncidentValidationError(FleetError):
    """Erreur de validation incident."""
    pass


class IncidentStateError(FleetError):
    """Transition d'etat invalide."""
    def __init__(self, current_status: str, new_status: str):
        super().__init__(f"Invalid incident transition from {current_status} to {new_status}")


# ============== Alert Exceptions ==============

class AlertNotFoundError(FleetError):
    """Alerte non trouvee."""
    def __init__(self, alert_id: str):
        super().__init__(f"Alert with ID {alert_id} not found")


# ============== Mileage Exceptions ==============

class MileageValidationError(FleetError):
    """Erreur de validation kilometrage."""
    pass


class MileageDecrementError(FleetError):
    """Tentative de diminution du kilometrage."""
    def __init__(self, current: int, new: int):
        super().__init__(f"Mileage cannot decrease from {current} to {new}")


# ============== Generic Exceptions ==============

class CodeGenerationError(FleetError):
    """Erreur de generation de code."""
    def __init__(self, entity_type: str):
        super().__init__(f"Failed to generate code for {entity_type}")


class PermissionDeniedError(FleetError):
    """Permission refusee."""
    def __init__(self, operation: str):
        super().__init__(f"Permission denied for operation: {operation}")


class ConcurrencyError(FleetError):
    """Erreur de concurrence (version conflict)."""
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(f"Concurrency conflict on {entity_type} {entity_id}. Please refresh and try again.")
