"""
Models SQLAlchemy - Module Expenses (GAP-084)

CRITIQUE: Tous les modèles ont tenant_id pour isolation multi-tenant.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Numeric,
    ForeignKey, Index, JSON, Date
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# ============== Enums ==============

class ExpenseCategory(str, Enum):
    """Catégorie de dépense."""
    MILEAGE = "mileage"
    PUBLIC_TRANSPORT = "public_transport"
    TAXI_RIDE = "taxi"
    PARKING = "parking"
    TOLL = "toll"
    RENTAL_CAR = "rental_car"
    FUEL = "fuel"
    HOTEL = "hotel"
    AIRBNB = "airbnb"
    RESTAURANT = "restaurant"
    MEAL_SOLO = "meal_solo"
    MEAL_BUSINESS = "meal_business"
    MEAL_TEAM = "meal_team"
    FLIGHT = "flight"
    TRAIN = "train"
    VISA = "visa"
    TRAVEL_INSURANCE = "travel_insurance"
    PHONE = "phone"
    INTERNET = "internet"
    OFFICE_SUPPLIES = "office_supplies"
    IT_EQUIPMENT = "it_equipment"
    BOOKS = "books"
    REPRESENTATION = "representation"
    SUBSCRIPTION = "subscription"
    OTHER = "other"


class ExpenseStatus(str, Enum):
    """Statut d'une note de frais."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"

    def allowed_transitions(self) -> List["ExpenseStatus"]:
        """Transitions autorisées."""
        transitions = {
            ExpenseStatus.DRAFT: [ExpenseStatus.SUBMITTED, ExpenseStatus.CANCELLED],
            ExpenseStatus.SUBMITTED: [ExpenseStatus.PENDING_APPROVAL, ExpenseStatus.REJECTED, ExpenseStatus.CANCELLED],
            ExpenseStatus.PENDING_APPROVAL: [ExpenseStatus.APPROVED, ExpenseStatus.REJECTED],
            ExpenseStatus.APPROVED: [ExpenseStatus.PAID],
            ExpenseStatus.REJECTED: [ExpenseStatus.DRAFT],
            ExpenseStatus.PAID: [],
            ExpenseStatus.CANCELLED: [],
        }
        return transitions.get(self, [])


class PaymentMethod(str, Enum):
    """Mode de paiement."""
    PERSONAL_CARD = "personal_card"
    COMPANY_CARD = "company_card"
    CASH = "cash"
    COMPANY_ACCOUNT = "company_account"
    MILEAGE = "mileage"


class VehicleType(str, Enum):
    """Type de véhicule pour indemnités kilométriques."""
    CAR_3CV = "car_3cv"
    CAR_4CV = "car_4cv"
    CAR_5CV = "car_5cv"
    CAR_6CV = "car_6cv"
    CAR_7CV_PLUS = "car_7cv_plus"
    MOTORCYCLE_50CC = "moto_50cc"
    MOTORCYCLE_125CC = "moto_125cc"
    MOTORCYCLE_3_5CV = "moto_3_5cv"
    MOTORCYCLE_5CV_PLUS = "moto_5cv_plus"
    BICYCLE = "bicycle"
    ELECTRIC_BICYCLE = "electric_bicycle"


# ============== Models ==============

class ExpenseReport(Base):
    """Note de frais."""
    __tablename__ = "expense_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Employé
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_name = Column(String(255))
    department_id = Column(UUID(as_uuid=True))

    # Période
    period_start = Column(Date)
    period_end = Column(Date)
    mission_reference = Column(String(100))

    # Statut
    status = Column(String(20), default=ExpenseStatus.DRAFT.value)

    # Totaux
    total_amount = Column(Numeric(18, 4), default=0)
    total_vat = Column(Numeric(18, 4), default=0)
    total_reimbursable = Column(Numeric(18, 4), default=0)
    currency = Column(String(3), default="EUR")

    # Workflow
    current_approver_id = Column(UUID(as_uuid=True))
    approval_history = Column(JSON, default=list)

    # Dates workflow
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)
    paid_at = Column(DateTime)

    # Export comptable
    exported_to_accounting = Column(Boolean, default=False)
    accounting_entry_id = Column(UUID(as_uuid=True))
    accounting_export_date = Column(DateTime)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True))

    # Relations
    lines = relationship("ExpenseLine", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_expense_reports_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_expense_reports_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_expense_reports_tenant_status", "tenant_id", "status"),
        Index("ix_expense_reports_tenant_period", "tenant_id", "period_start", "period_end"),
    )


class ExpenseLine(Base):
    """Ligne de dépense."""
    __tablename__ = "expense_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("expense_reports.id"), nullable=False)

    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    expense_date = Column(Date, nullable=False)

    # Montants
    amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(3), default="EUR")
    vat_rate = Column(Numeric(5, 2))
    vat_amount = Column(Numeric(18, 4))
    amount_excl_vat = Column(Numeric(18, 4))
    vat_recoverable = Column(Boolean, default=True)

    # Paiement
    payment_method = Column(String(30), default=PaymentMethod.PERSONAL_CARD.value)

    # Justificatif
    receipt_id = Column(UUID(as_uuid=True))
    receipt_file_path = Column(String(500))
    receipt_required = Column(Boolean, default=True)

    # Kilométrique
    mileage_departure = Column(String(255))
    mileage_arrival = Column(String(255))
    mileage_distance_km = Column(Numeric(10, 2))
    mileage_is_round_trip = Column(Boolean, default=False)
    vehicle_type = Column(String(30))
    mileage_rate = Column(Numeric(6, 4))
    mileage_purpose = Column(Text)

    # Repas d'affaires
    guests = Column(JSON, default=list)
    guest_count = Column(Integer, default=0)

    # Projet/Client
    project_id = Column(UUID(as_uuid=True))
    client_id = Column(UUID(as_uuid=True))
    billable = Column(Boolean, default=False)

    # Conformité
    is_policy_compliant = Column(Boolean, default=True)
    policy_violation_reason = Column(Text)

    # Comptabilité
    accounting_code = Column(String(20))
    cost_center = Column(String(50))
    analytic_axis = Column(JSON)

    # OCR
    ocr_processed = Column(Boolean, default=False)
    ocr_data = Column(JSON)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relation
    report = relationship("ExpenseReport", back_populates="lines")

    __table_args__ = (
        Index("ix_expense_lines_report", "report_id", "expense_date"),
        Index("ix_expense_lines_category", "tenant_id", "category"),
    )


class ExpensePolicy(Base):
    """Politique de dépenses."""
    __tablename__ = "expense_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Limites par catégorie (JSON)
    category_limits = Column(JSON, default=dict)

    # Limites générales
    single_expense_limit = Column(Numeric(18, 4), default=500)
    daily_limit = Column(Numeric(18, 4), default=200)
    monthly_limit = Column(Numeric(18, 4), default=2000)

    # Règles justificatifs
    receipt_required_above = Column(Numeric(18, 4), default=10)
    receipt_required_categories = Column(JSON, default=list)

    # Règles repas
    meal_solo_limit = Column(Numeric(18, 4), default=Decimal("20.20"))
    meal_business_limit = Column(Numeric(18, 4), default=50)
    meal_require_guests = Column(Boolean, default=True)

    # Règles transport
    mileage_max_daily_km = Column(Numeric(10, 2), default=500)
    require_train_over_km = Column(Numeric(10, 2), default=300)

    # Seuils d'approbation (JSON)
    approval_thresholds = Column(JSON, default=dict)

    # Catégories interdites (JSON)
    blocked_categories = Column(JSON, default=list)

    # Règles avancées (JSON)
    rules = Column(JSON, default=list)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True))

    __table_args__ = (
        Index("ix_expense_policies_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_expense_policies_tenant_default", "tenant_id", "is_default"),
    )


class MileageRate(Base):
    """Barème kilométrique."""
    __tablename__ = "expense_mileage_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    year = Column(Integer, nullable=False)
    vehicle_type = Column(String(30), nullable=False)

    # Tranches
    rate_up_to_5000 = Column(Numeric(6, 4))
    rate_5001_to_20000 = Column(Numeric(6, 4))
    fixed_5001_to_20000 = Column(Numeric(10, 2))
    rate_above_20000 = Column(Numeric(6, 4))

    # Pour vélo
    flat_rate = Column(Numeric(6, 4))

    is_active = Column(Boolean, default=True)
    source = Column(String(100))  # URSSAF, custom, etc.

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))

    __table_args__ = (
        Index("ix_mileage_rates_tenant_year", "tenant_id", "year", "vehicle_type", unique=True),
    )


class EmployeeVehicle(Base):
    """Véhicule employé pour kilométrique."""
    __tablename__ = "expense_employee_vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False)

    vehicle_type = Column(String(30), nullable=False)
    registration_number = Column(String(20))
    fiscal_power = Column(Integer)
    make = Column(String(100))
    model = Column(String(100))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Kilométrage annuel cumulé
    annual_mileage = Column(JSON, default=dict)  # {year: total_km}

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_employee_vehicles_tenant_employee", "tenant_id", "employee_id"),
    )
