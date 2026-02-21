"""
Schémas Pydantic Shipping / Expédition - GAP-078
================================================
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============== Address Schema ==============

class AddressSchema(BaseModel):
    """Schéma d'adresse."""
    name: str = ""
    company: str = ""
    street1: str = ""
    street2: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country_code: str = "FR"
    phone: str = ""
    email: str = ""
    is_residential: bool = True
    instructions: str = ""


# ============== Zone Schemas ==============

class ZoneCreate(BaseModel):
    """Création zone."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str = ""
    countries: List[str] = Field(default_factory=list)
    postal_codes: List[str] = Field(default_factory=list)
    excluded_postal_codes: List[str] = Field(default_factory=list)
    sort_order: int = 0
    is_active: bool = True


class ZoneUpdate(BaseModel):
    """Mise à jour zone."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    countries: Optional[List[str]] = None
    postal_codes: Optional[List[str]] = None
    excluded_postal_codes: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ZoneResponse(BaseModel):
    """Réponse zone."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    description: str
    countries: List[str]
    postal_codes: List[str]
    excluded_postal_codes: List[str]
    sort_order: int
    is_active: bool
    created_at: datetime
    version: int


class ZoneListResponse(BaseModel):
    """Liste paginée zones."""
    items: List[ZoneResponse]
    total: int
    skip: int
    limit: int


# ============== Carrier Schemas ==============

class CarrierCreate(BaseModel):
    """Création transporteur."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str = ""
    carrier_type: str = "postal"
    api_endpoint: str = ""
    api_key: str = ""
    api_secret: str = ""
    account_number: str = ""
    supports_tracking: bool = True
    supports_labels: bool = True
    supports_returns: bool = True
    supports_pickup: bool = False
    supports_insurance: bool = False
    min_delivery_days: int = Field(default=1, ge=0)
    max_delivery_days: int = Field(default=5, ge=1)
    max_weight_kg: Decimal = Decimal("30")
    max_length_cm: int = 150
    max_girth_cm: int = 300
    logo_url: str = ""
    tracking_url_template: str = ""
    is_active: bool = True


class CarrierUpdate(BaseModel):
    """Mise à jour transporteur."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    carrier_type: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_number: Optional[str] = None
    supports_tracking: Optional[bool] = None
    supports_labels: Optional[bool] = None
    supports_returns: Optional[bool] = None
    supports_pickup: Optional[bool] = None
    supports_insurance: Optional[bool] = None
    min_delivery_days: Optional[int] = Field(None, ge=0)
    max_delivery_days: Optional[int] = Field(None, ge=1)
    max_weight_kg: Optional[Decimal] = None
    max_length_cm: Optional[int] = None
    max_girth_cm: Optional[int] = None
    logo_url: Optional[str] = None
    tracking_url_template: Optional[str] = None
    is_active: Optional[bool] = None


class CarrierResponse(BaseModel):
    """Réponse transporteur."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    description: str
    carrier_type: str
    supports_tracking: bool
    supports_labels: bool
    supports_returns: bool
    supports_pickup: bool
    supports_insurance: bool
    min_delivery_days: int
    max_delivery_days: int
    max_weight_kg: Decimal
    max_length_cm: int
    max_girth_cm: int
    logo_url: str
    tracking_url_template: str
    is_active: bool
    created_at: datetime
    version: int


class CarrierListResponse(BaseModel):
    """Liste paginée transporteurs."""
    items: List[CarrierResponse]
    total: int
    skip: int
    limit: int


# ============== ShippingRate Schemas ==============

class RateCreate(BaseModel):
    """Création tarif."""
    carrier_id: UUID
    zone_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    shipping_method: str = "standard"
    calculation_method: str = "weight"
    base_rate: Decimal = Decimal("0")
    per_kg_rate: Decimal = Decimal("0")
    per_item_rate: Decimal = Decimal("0")
    percent_of_order: Decimal = Decimal("0")
    currency: str = "EUR"
    weight_tiers: List[Dict[str, Any]] = Field(default_factory=list)
    price_tiers: List[Dict[str, Any]] = Field(default_factory=list)
    fuel_surcharge_percent: Decimal = Decimal("0")
    residential_surcharge: Decimal = Decimal("0")
    oversized_surcharge: Decimal = Decimal("0")
    free_shipping_threshold: Optional[Decimal] = None
    min_days: int = Field(default=1, ge=0)
    max_days: int = Field(default=5, ge=1)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: bool = True


class RateUpdate(BaseModel):
    """Mise à jour tarif."""
    zone_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    shipping_method: Optional[str] = None
    calculation_method: Optional[str] = None
    base_rate: Optional[Decimal] = None
    per_kg_rate: Optional[Decimal] = None
    per_item_rate: Optional[Decimal] = None
    percent_of_order: Optional[Decimal] = None
    currency: Optional[str] = None
    weight_tiers: Optional[List[Dict[str, Any]]] = None
    price_tiers: Optional[List[Dict[str, Any]]] = None
    fuel_surcharge_percent: Optional[Decimal] = None
    residential_surcharge: Optional[Decimal] = None
    oversized_surcharge: Optional[Decimal] = None
    free_shipping_threshold: Optional[Decimal] = None
    min_days: Optional[int] = Field(None, ge=0)
    max_days: Optional[int] = Field(None, ge=1)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: Optional[bool] = None


class RateResponse(BaseModel):
    """Réponse tarif."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    carrier_id: UUID
    zone_id: Optional[UUID]
    name: str
    code: str
    shipping_method: str
    calculation_method: str
    base_rate: Decimal
    per_kg_rate: Decimal
    per_item_rate: Decimal
    percent_of_order: Decimal
    currency: str
    weight_tiers: List[Dict[str, Any]]
    price_tiers: List[Dict[str, Any]]
    fuel_surcharge_percent: Decimal
    residential_surcharge: Decimal
    oversized_surcharge: Decimal
    free_shipping_threshold: Optional[Decimal]
    min_days: int
    max_days: int
    valid_from: Optional[date]
    valid_until: Optional[date]
    is_active: bool
    created_at: datetime
    version: int


class RateListResponse(BaseModel):
    """Liste paginée tarifs."""
    items: List[RateResponse]
    total: int
    skip: int
    limit: int


class RateQuoteRequest(BaseModel):
    """Demande de calcul de tarifs."""
    destination: AddressSchema
    packages: List[Dict[str, Any]]
    order_total: Decimal = Decimal("0")
    currency: str = "EUR"


class RateQuoteResponse(BaseModel):
    """Réponse calcul de tarifs."""
    rate_id: UUID
    carrier_id: UUID
    carrier_name: str
    method: str
    name: str
    cost: Decimal
    currency: str
    min_days: int
    max_days: int
    free_shipping: bool


# ============== Package Schemas ==============

class PackageCreate(BaseModel):
    """Création colis."""
    package_type: str = "medium_box"
    length: Decimal = Decimal("0")
    width: Decimal = Decimal("0")
    height: Decimal = Decimal("0")
    weight: Decimal = Decimal("0")
    items: List[Dict[str, Any]] = Field(default_factory=list)
    declared_value: Decimal = Decimal("0")
    currency: str = "EUR"
    label_format: str = "PDF"


class PackageUpdate(BaseModel):
    """Mise à jour colis."""
    package_type: Optional[str] = None
    length: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    items: Optional[List[Dict[str, Any]]] = None
    declared_value: Optional[Decimal] = None
    currency: Optional[str] = None
    label_format: Optional[str] = None


class PackageResponse(BaseModel):
    """Réponse colis."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID
    package_type: str
    length: Decimal
    width: Decimal
    height: Decimal
    weight: Decimal
    dimensional_weight: Decimal
    billable_weight: Decimal
    items: List[Dict[str, Any]]
    declared_value: Decimal
    currency: str
    tracking_number: str
    label_url: str
    label_format: str


# ============== Rate Calculation Schemas ==============

class RateCalculationRequest(BaseModel):
    """Demande de calcul de tarifs."""
    destination: AddressSchema
    packages: List[PackageCreate]
    order_total: Decimal = Decimal("0")
    currency: str = "EUR"


class RateCalculationResponse(BaseModel):
    """Réponse calcul de tarifs."""
    rate_id: str
    carrier_id: str
    carrier_name: str
    carrier_code: str
    method: str
    rate_name: str
    cost: Decimal
    currency: str
    min_days: int
    max_days: int
    is_free_shipping: bool
    zone_id: str
    zone_name: str


# ============== Shipment Schemas ==============

class ShipmentCreate(BaseModel):
    """Création expédition."""
    order_id: Optional[UUID] = None
    order_number: str = ""
    carrier_id: UUID
    shipping_method: str = "standard"
    service_code: str = ""
    ship_from: AddressSchema
    ship_to: AddressSchema
    packages: List[PackageCreate]
    shipping_cost: Decimal = Decimal("0")
    is_insured: bool = False
    insured_value: Decimal = Decimal("0")
    signature_required: bool = False
    saturday_delivery: bool = False
    hold_at_location: bool = False
    pickup_point_id: Optional[UUID] = None
    notes: str = ""


class ShipmentUpdate(BaseModel):
    """Mise à jour expédition."""
    ship_to: Optional[AddressSchema] = None
    is_insured: Optional[bool] = None
    insured_value: Optional[Decimal] = None
    signature_required: Optional[bool] = None
    saturday_delivery: Optional[bool] = None
    hold_at_location: Optional[bool] = None
    pickup_point_id: Optional[UUID] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class ShipmentResponse(BaseModel):
    """Réponse expédition."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    shipment_number: str
    order_id: Optional[UUID]
    order_number: str
    status: str
    carrier_id: Optional[UUID]
    carrier_name: str
    shipping_method: str
    service_code: str
    ship_from: Dict[str, Any]
    ship_to: Dict[str, Any]
    total_packages: int
    total_weight: Decimal
    master_tracking_number: str
    tracking_url: str
    shipping_cost: Decimal
    insurance_cost: Decimal
    surcharges: Decimal
    total_cost: Decimal
    currency: str
    is_insured: bool
    insured_value: Decimal
    signature_required: bool
    saturday_delivery: bool
    hold_at_location: bool
    ship_date: Optional[date]
    estimated_delivery: Optional[date]
    actual_delivery: Optional[datetime]
    pickup_scheduled: bool
    pickup_date: Optional[date]
    pickup_confirmation: str
    pickup_point_id: Optional[UUID]
    pickup_point_name: str
    pickup_point_address: str
    last_event: str
    last_event_at: Optional[datetime]
    notes: str
    created_at: datetime
    version: int
    packages: List[PackageResponse] = Field(default_factory=list)


class ShipmentListResponse(BaseModel):
    """Liste paginée expéditions."""
    items: List[ShipmentResponse]
    total: int
    skip: int
    limit: int


class LabelGenerationResponse(BaseModel):
    """Réponse génération étiquette."""
    shipment_id: UUID
    tracking_number: str
    tracking_url: Optional[str] = None
    label_url: str
    packages: List[Dict[str, Any]]


class TrackingEventSchema(BaseModel):
    """Événement de suivi."""
    timestamp: datetime
    status: str
    description: str
    location: str


class TrackingEventCreate(BaseModel):
    """Création événement de suivi."""
    status: Optional[str] = None
    description: str
    location: Optional[str] = None
    event_time: Optional[datetime] = None


class TrackingUpdateRequest(BaseModel):
    """Mise à jour suivi."""
    status: str
    event_description: str
    location: str = ""
    event_time: Optional[datetime] = None


# ============== PickupPoint Schemas ==============

class PickupPointCreate(BaseModel):
    """Création point relais."""
    carrier_id: UUID
    external_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    address: AddressSchema
    opening_hours: Dict[str, str] = Field(default_factory=dict)
    is_locker: bool = False
    has_parking: bool = False
    wheelchair_accessible: bool = False
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_active: bool = True


class PickupPointUpdate(BaseModel):
    """Mise à jour point relais."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[AddressSchema] = None
    opening_hours: Optional[Dict[str, str]] = None
    is_locker: Optional[bool] = None
    has_parking: Optional[bool] = None
    wheelchair_accessible: Optional[bool] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_active: Optional[bool] = None


class PickupPointResponse(BaseModel):
    """Réponse point relais."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    carrier_id: UUID
    external_id: str
    name: str
    address: Dict[str, Any]
    opening_hours: Dict[str, str]
    is_locker: bool
    has_parking: bool
    wheelchair_accessible: bool
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    is_active: bool
    created_at: datetime
    version: int


class PickupPointListResponse(BaseModel):
    """Liste paginée points relais."""
    items: List[PickupPointResponse]
    total: int
    skip: int
    limit: int


class PickupPointSearchRequest(BaseModel):
    """Recherche points relais."""
    carrier_id: str
    country_code: str = Field(..., min_length=2, max_length=2)
    postal_code: str = Field(..., min_length=1)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    max_results: int = Field(default=10, ge=1, le=50)
    max_distance_km: Decimal = Decimal("20")


# ============== Return Schemas ==============

class ReturnCreate(BaseModel):
    """Création retour."""
    order_id: Optional[UUID] = None
    shipment_id: Optional[UUID] = None
    reason: str = Field(..., min_length=1)
    reason_code: str = ""
    customer_notes: str = ""
    items: List[Dict[str, Any]] = Field(default_factory=list)
    return_address: Optional[AddressSchema] = None


class ReturnUpdate(BaseModel):
    """Mise à jour retour."""
    reason: Optional[str] = None
    reason_code: Optional[str] = None
    customer_notes: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    return_address: Optional[AddressSchema] = None


class ReturnResponse(BaseModel):
    """Réponse retour."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    return_number: str
    order_id: Optional[UUID]
    shipment_id: Optional[UUID]
    status: str
    reason: str
    reason_code: str
    customer_notes: str
    items: List[Dict[str, Any]]
    return_carrier_id: Optional[UUID]
    return_tracking_number: str
    return_label_url: str
    return_address: Dict[str, Any]
    requested_at: datetime
    approved_at: Optional[datetime]
    received_at: Optional[datetime]
    inspected_at: Optional[datetime]
    completed_at: Optional[datetime]
    inspection_notes: str
    condition: str
    refund_amount: Decimal
    refund_method: str
    refund_reference: str
    currency: str
    return_shipping_cost: Decimal
    restocking_fee: Decimal
    processed_by: Optional[UUID]
    created_at: datetime
    version: int


class ReturnListResponse(BaseModel):
    """Liste paginée retours."""
    items: List[ReturnResponse]
    total: int
    skip: int
    limit: int


class ReturnApprovalRequest(BaseModel):
    """Approbation retour."""
    notes: str = ""


class ReturnReceiptRequest(BaseModel):
    """Réception retour."""
    condition: str = Field(..., min_length=1)
    inspection_notes: str = ""


class ReturnRefundRequest(BaseModel):
    """Remboursement retour."""
    refund_amount: Decimal
    refund_method: str
    restocking_fee: Optional[Decimal] = Decimal("0")
    refund_reference: Optional[str] = None


# Alias pour compatibilité
RefundRequest = ReturnRefundRequest


# ============== Stats Schemas ==============

class ShippingStatsRequest(BaseModel):
    """Demande statistiques."""
    period_start: date
    period_end: date


class ShippingStatsResponse(BaseModel):
    """Statistiques d'expédition."""
    period_start: str
    period_end: str
    total_shipments: int
    total_packages: int
    total_weight_kg: float
    status_counts: Dict[str, int]
    on_time_delivery_rate: float
    avg_delivery_days: float
    total_shipping_cost: float
    avg_cost_per_shipment: float
    shipments_by_carrier: Dict[str, int]
    cost_by_carrier: Dict[str, float]
    shipments_by_method: Dict[str, int]
    total_returns: int
    return_rate: float


# ============== Common Schemas ==============

class AutocompleteResponse(BaseModel):
    """Réponse autocomplete."""
    items: List[Dict[str, Any]]


class BulkResult(BaseModel):
    """Résultat opération en masse."""
    success_count: int
    failure_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ============== Aliases ==============

# ShippingRate aliases
ShippingRateCreate = RateCreate
ShippingRateUpdate = RateUpdate
ShippingRateResponse = RateResponse
ShippingRateListResponse = RateListResponse
