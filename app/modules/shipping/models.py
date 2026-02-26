"""
Modèles SQLAlchemy Shipping / Expédition - GAP-078
==================================================
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ============== Énumérations ==============

class CarrierType(str, Enum):
    """Type de transporteur."""
    POSTAL = "postal"
    EXPRESS = "express"
    FREIGHT = "freight"
    LOCAL = "local"
    PICKUP = "pickup"
    DROPSHIP = "dropship"


class ShippingMethod(str, Enum):
    """Méthode d'expédition."""
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    ECONOMY = "economy"
    PICKUP_POINT = "pickup_point"
    STORE_PICKUP = "store_pickup"
    SAME_DAY = "same_day"


class ShipmentStatus(str, Enum):
    """Statut d'expédition."""
    PENDING = "pending"
    LABEL_CREATED = "label_created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_ATTEMPT = "failed_attempt"
    RETURNED = "returned"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.PENDING: [cls.LABEL_CREATED, cls.CANCELLED],
            cls.LABEL_CREATED: [cls.PICKED_UP, cls.IN_TRANSIT, cls.CANCELLED],
            cls.PICKED_UP: [cls.IN_TRANSIT],
            cls.IN_TRANSIT: [cls.OUT_FOR_DELIVERY, cls.DELIVERED, cls.FAILED_ATTEMPT, cls.EXCEPTION],
            cls.OUT_FOR_DELIVERY: [cls.DELIVERED, cls.FAILED_ATTEMPT],
            cls.FAILED_ATTEMPT: [cls.OUT_FOR_DELIVERY, cls.RETURNED, cls.DELIVERED],
            cls.EXCEPTION: [cls.IN_TRANSIT, cls.RETURNED, cls.CANCELLED],
            cls.DELIVERED: [],
            cls.RETURNED: [],
            cls.CANCELLED: [],
        }


class PackageType(str, Enum):
    """Type de colis."""
    ENVELOPE = "envelope"
    SMALL_BOX = "small_box"
    MEDIUM_BOX = "medium_box"
    LARGE_BOX = "large_box"
    PALLET = "pallet"
    CUSTOM = "custom"


class ReturnStatus(str, Enum):
    """Statut de retour."""
    REQUESTED = "requested"
    APPROVED = "approved"
    LABEL_SENT = "label_sent"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTED = "inspected"
    REFUNDED = "refunded"
    REJECTED = "rejected"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.REQUESTED: [cls.APPROVED, cls.REJECTED],
            cls.APPROVED: [cls.LABEL_SENT],
            cls.LABEL_SENT: [cls.IN_TRANSIT],
            cls.IN_TRANSIT: [cls.RECEIVED],
            cls.RECEIVED: [cls.INSPECTED],
            cls.INSPECTED: [cls.REFUNDED, cls.REJECTED],
            cls.REFUNDED: [],
            cls.REJECTED: [],
        }


class RateCalculation(str, Enum):
    """Mode de calcul des tarifs."""
    FLAT = "flat"
    WEIGHT = "weight"
    VOLUME = "volume"
    DISTANCE = "distance"
    PRICE_BASED = "price_based"
    ITEM_COUNT = "item_count"


# ============== Modèles ==============

class Zone(Base):
    """Zone de livraison."""
    __tablename__ = "shipping_zones"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # Pays et régions
    countries: Mapped[List[str]] = mapped_column(ARRAY(String(3)), default=list)
    postal_codes: Mapped[List[str]] = mapped_column(ARRAY(String(20)), default=list)
    excluded_postal_codes: Mapped[List[str]] = mapped_column(ARRAY(String(20)), default=list)

    # Paramètres
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    rates = relationship("ShippingRate", back_populates="zone")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_zone_tenant_code"),
        Index("ix_zone_tenant_active", "tenant_id", "is_active"),
    )


class Carrier(Base):
    """Transporteur."""
    __tablename__ = "shipping_carriers"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    carrier_type: Mapped[CarrierType] = mapped_column(
        SQLEnum(CarrierType, name="carrier_type"),
        default=CarrierType.POSTAL
    )

    # Intégration API
    api_endpoint: Mapped[str] = mapped_column(String(500), default="")
    api_key: Mapped[str] = mapped_column(String(500), default="")
    api_secret: Mapped[str] = mapped_column(String(500), default="")
    account_number: Mapped[str] = mapped_column(String(100), default="")

    # Configuration
    supports_tracking: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_labels: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_returns: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_pickup: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_insurance: Mapped[bool] = mapped_column(Boolean, default=False)

    # Délais standard (jours ouvrés)
    min_delivery_days: Mapped[int] = mapped_column(Integer, default=1)
    max_delivery_days: Mapped[int] = mapped_column(Integer, default=5)

    # Limites
    max_weight_kg: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("30"))
    max_length_cm: Mapped[int] = mapped_column(Integer, default=150)
    max_girth_cm: Mapped[int] = mapped_column(Integer, default=300)

    # Logo et tracking
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    tracking_url_template: Mapped[str] = mapped_column(String(500), default="")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    rates = relationship("ShippingRate", back_populates="carrier")
    shipments = relationship("Shipment", back_populates="carrier")
    pickup_points = relationship("PickupPoint", back_populates="carrier")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_carrier_tenant_code"),
        Index("ix_carrier_tenant_type", "tenant_id", "carrier_type"),
        Index("ix_carrier_tenant_active", "tenant_id", "is_active"),
    )


class ShippingRate(Base):
    """Tarif d'expédition."""
    __tablename__ = "shipping_rates"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    carrier_id: Mapped[UUID] = mapped_column(
        UUID(), ForeignKey("shipping_carriers.id"), nullable=False
    )
    zone_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("shipping_zones.id"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)

    shipping_method: Mapped[ShippingMethod] = mapped_column(
        SQLEnum(ShippingMethod, name="shipping_method"),
        default=ShippingMethod.STANDARD
    )
    calculation_method: Mapped[RateCalculation] = mapped_column(
        SQLEnum(RateCalculation, name="rate_calculation"),
        default=RateCalculation.WEIGHT
    )

    # Tarif
    base_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    per_kg_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    per_item_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    percent_of_order: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Paliers (stockés en JSON)
    weight_tiers: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    price_tiers: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # Frais supplémentaires
    fuel_surcharge_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    residential_surcharge: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    oversized_surcharge: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))

    # Seuil de gratuité
    free_shipping_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Délai
    min_days: Mapped[int] = mapped_column(Integer, default=1)
    max_days: Mapped[int] = mapped_column(Integer, default=5)

    # Validité
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    carrier = relationship("Carrier", back_populates="rates")
    zone = relationship("Zone", back_populates="rates")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_rate_tenant_code"),
        Index("ix_rate_carrier", "carrier_id"),
        Index("ix_rate_zone", "zone_id"),
        Index("ix_rate_tenant_method", "tenant_id", "shipping_method"),
    )


class Shipment(Base):
    """Expédition."""
    __tablename__ = "shipping_shipments"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    shipment_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Références
    order_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    order_number: Mapped[str] = mapped_column(String(50), default="")

    status: Mapped[ShipmentStatus] = mapped_column(
        SQLEnum(ShipmentStatus, name="shipment_status"),
        default=ShipmentStatus.PENDING
    )

    # Transporteur
    carrier_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("shipping_carriers.id"), nullable=True
    )
    carrier_name: Mapped[str] = mapped_column(String(100), default="")
    shipping_method: Mapped[ShippingMethod] = mapped_column(
        SQLEnum(ShippingMethod, name="shipping_method", create_type=False),
        default=ShippingMethod.STANDARD
    )
    service_code: Mapped[str] = mapped_column(String(50), default="")

    # Adresses (stockées en JSON)
    ship_from: Mapped[dict] = mapped_column(JSONB, default=dict)
    ship_to: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Totaux
    total_packages: Mapped[int] = mapped_column(Integer, default=0)
    total_weight: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0"))

    # Tracking principal
    master_tracking_number: Mapped[str] = mapped_column(String(100), default="")
    tracking_url: Mapped[str] = mapped_column(String(500), default="")

    # Coûts
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    insurance_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    surcharges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Assurance
    is_insured: Mapped[bool] = mapped_column(Boolean, default=False)
    insured_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))

    # Options
    signature_required: Mapped[bool] = mapped_column(Boolean, default=False)
    saturday_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    hold_at_location: Mapped[bool] = mapped_column(Boolean, default=False)

    # Dates
    ship_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estimated_delivery: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Pickup
    pickup_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    pickup_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    pickup_confirmation: Mapped[str] = mapped_column(String(100), default="")

    # Point relais
    pickup_point_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("shipping_pickup_points.id"), nullable=True
    )
    pickup_point_name: Mapped[str] = mapped_column(String(200), default="")
    pickup_point_address: Mapped[str] = mapped_column(Text, default="")

    # Documents
    commercial_invoice_url: Mapped[str] = mapped_column(String(500), default="")
    customs_docs_url: Mapped[str] = mapped_column(String(500), default="")

    # Événements
    tracking_events: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    last_event: Mapped[str] = mapped_column(String(200), default="")
    last_event_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Notes
    notes: Mapped[str] = mapped_column(Text, default="")
    internal_notes: Mapped[str] = mapped_column(Text, default="")

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    carrier = relationship("Carrier", back_populates="shipments")
    pickup_point = relationship("PickupPoint")
    packages = relationship("Package", back_populates="shipment", cascade="all, delete-orphan")
    returns = relationship("Return", back_populates="shipment")

    __table_args__ = (
        UniqueConstraint("tenant_id", "shipment_number", name="uq_shipment_tenant_number"),
        Index("ix_shipment_tenant_status", "tenant_id", "status"),
        Index("ix_shipment_tenant_date", "tenant_id", "ship_date"),
        Index("ix_shipment_order", "order_id"),
        Index("ix_shipment_tracking", "master_tracking_number"),
    )


class Package(Base):
    """Colis."""
    __tablename__ = "shipping_packages"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    shipment_id: Mapped[UUID] = mapped_column(
        UUID(), ForeignKey("shipping_shipments.id"), nullable=False
    )

    package_type: Mapped[PackageType] = mapped_column(
        SQLEnum(PackageType, name="package_type"),
        default=PackageType.MEDIUM_BOX
    )

    # Dimensions (cm)
    length: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    width: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    height: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))

    # Poids (kg)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0"))
    dimensional_weight: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0"))
    billable_weight: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=Decimal("0"))

    # Contenu
    items: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    declared_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Tracking
    tracking_number: Mapped[str] = mapped_column(String(100), default="")

    # Étiquette
    label_url: Mapped[str] = mapped_column(String(500), default="")
    label_format: Mapped[str] = mapped_column(String(10), default="PDF")

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    shipment = relationship("Shipment", back_populates="packages")

    __table_args__ = (
        Index("ix_package_shipment", "shipment_id"),
        Index("ix_package_tracking", "tracking_number"),
    )


class PickupPoint(Base):
    """Point relais."""
    __tablename__ = "shipping_pickup_points"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    carrier_id: Mapped[UUID] = mapped_column(
        UUID(), ForeignKey("shipping_carriers.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Adresse (stockée en JSON)
    address: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Horaires
    opening_hours: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Caractéristiques
    is_locker: Mapped[bool] = mapped_column(Boolean, default=False)
    has_parking: Mapped[bool] = mapped_column(Boolean, default=False)
    wheelchair_accessible: Mapped[bool] = mapped_column(Boolean, default=False)

    # Coordonnées
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    carrier = relationship("Carrier", back_populates="pickup_points")

    __table_args__ = (
        UniqueConstraint("tenant_id", "carrier_id", "external_id", name="uq_pickup_point_tenant_carrier_external"),
        Index("ix_pickup_point_carrier", "carrier_id"),
        Index("ix_pickup_point_tenant_active", "tenant_id", "is_active"),
    )


class Return(Base):
    """Retour."""
    __tablename__ = "shipping_returns"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(), nullable=False, index=True
    )

    return_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Références
    order_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    shipment_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("shipping_shipments.id"), nullable=True
    )

    status: Mapped[ReturnStatus] = mapped_column(
        SQLEnum(ReturnStatus, name="return_status"),
        default=ReturnStatus.REQUESTED
    )

    # Raison
    reason: Mapped[str] = mapped_column(Text, default="")
    reason_code: Mapped[str] = mapped_column(String(50), default="")
    customer_notes: Mapped[str] = mapped_column(Text, default="")

    # Articles
    items: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # Expédition retour
    return_carrier_id: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    return_tracking_number: Mapped[str] = mapped_column(String(100), default="")
    return_label_url: Mapped[str] = mapped_column(String(500), default="")

    # Adresse de retour (JSON)
    return_address: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Dates
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    inspected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Inspection
    inspection_notes: Mapped[str] = mapped_column(Text, default="")
    condition: Mapped[str] = mapped_column(String(50), default="")

    # Remboursement
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    refund_method: Mapped[str] = mapped_column(String(50), default="")
    refund_reference: Mapped[str] = mapped_column(String(100), default="")
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Frais
    return_shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    restocking_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))

    processed_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relations
    shipment = relationship("Shipment", back_populates="returns")

    __table_args__ = (
        UniqueConstraint("tenant_id", "return_number", name="uq_return_tenant_number"),
        Index("ix_return_tenant_status", "tenant_id", "status"),
        Index("ix_return_order", "order_id"),
        Index("ix_return_shipment", "shipment_id"),
    )
