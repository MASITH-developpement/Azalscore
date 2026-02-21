"""
AZALS MODULE - BUDGET: Models
==============================

Modeles SQLAlchemy pour la gestion budgetaire complete.

Fonctionnalites inspirees de: Sage, Odoo, Microsoft Dynamics 365, Pennylane, Axonaut
- Budgets par periode (mensuel, trimestriel, annuel)
- Lignes budgetaires hierarchiques
- Suivi realise vs prevu
- Alertes depassements
- Revisions budgetaires avec workflow
- Multi-axes analytiques
- Consolidation multi-entites
- Scenarios et simulations
- Controle budgetaire (hard/soft)

Conformite:
- AZA-SEC-001: Isolation tenant obligatoire
- AZA-BE-003: Soft delete et audit trail

Auteur: AZALSCORE Team
Version: 2.0.0
"""

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMERATIONS
# ============================================================================

class BudgetType(str, enum.Enum):
    """Type de budget."""
    OPERATING = "OPERATING"           # Budget d'exploitation (OPEX)
    INVESTMENT = "INVESTMENT"         # Budget d'investissement (CAPEX)
    CASH = "CASH"                     # Budget de tresorerie
    PROJECT = "PROJECT"               # Budget projet
    DEPARTMENT = "DEPARTMENT"         # Budget departement
    COST_CENTER = "COST_CENTER"       # Budget centre de couts
    SALES = "SALES"                   # Budget commercial
    PRODUCTION = "PRODUCTION"         # Budget production
    HR = "HR"                         # Budget RH
    MARKETING = "MARKETING"           # Budget marketing
    IT = "IT"                         # Budget IT
    RD = "RD"                         # Budget R&D
    CONSOLIDATED = "CONSOLIDATED"     # Budget consolide


class BudgetPeriodType(str, enum.Enum):
    """Type de periode budgetaire."""
    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"
    WEEKLY = "WEEKLY"
    CUSTOM = "CUSTOM"


class BudgetStatus(str, enum.Enum):
    """Statut du budget."""
    DRAFT = "DRAFT"                   # Brouillon
    SUBMITTED = "SUBMITTED"           # Soumis pour approbation
    UNDER_REVIEW = "UNDER_REVIEW"     # En cours de revue
    APPROVED = "APPROVED"             # Approuve
    ACTIVE = "ACTIVE"                 # Actif (en cours d'execution)
    REVISED = "REVISED"               # En cours de revision
    FROZEN = "FROZEN"                 # Gele (pas de modifications)
    CLOSED = "CLOSED"                 # Cloture
    REJECTED = "REJECTED"             # Rejete
    ARCHIVED = "ARCHIVED"             # Archive


class BudgetLineType(str, enum.Enum):
    """Type de ligne budgetaire."""
    REVENUE = "REVENUE"               # Recette/Produit
    EXPENSE = "EXPENSE"               # Depense/Charge
    INVESTMENT = "INVESTMENT"         # Investissement
    TRANSFER = "TRANSFER"             # Transfert interne
    PROVISION = "PROVISION"           # Provision
    CONTINGENCY = "CONTINGENCY"       # Reserve/Contingence


class AllocationMethod(str, enum.Enum):
    """Methode de repartition du budget sur les periodes."""
    EQUAL = "EQUAL"                   # Repartition egale
    SEASONAL = "SEASONAL"             # Saisonniere (profil personnalise)
    HISTORICAL = "HISTORICAL"         # Basee sur l'historique
    MANUAL = "MANUAL"                 # Saisie manuelle
    WEIGHTED = "WEIGHTED"             # Ponderee
    FRONT_LOADED = "FRONT_LOADED"     # Chargee en debut
    BACK_LOADED = "BACK_LOADED"       # Chargee en fin


class VarianceType(str, enum.Enum):
    """Type d'ecart budgetaire."""
    FAVORABLE = "FAVORABLE"           # Favorable (economie)
    UNFAVORABLE = "UNFAVORABLE"       # Defavorable (depassement)
    ON_TARGET = "ON_TARGET"           # Dans les limites


class AlertSeverity(str, enum.Enum):
    """Severite des alertes."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EXCEEDED = "EXCEEDED"


class AlertStatus(str, enum.Enum):
    """Statut des alertes."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class ControlMode(str, enum.Enum):
    """Mode de controle budgetaire (inspire Dynamics 365)."""
    NONE = "NONE"                     # Pas de controle
    WARNING_ONLY = "WARNING_ONLY"     # Avertissement seulement
    SOFT = "SOFT"                     # Controle souple (peut depasser)
    HARD = "HARD"                     # Controle strict (bloque)


class RevisionStatus(str, enum.Enum):
    """Statut de revision."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"


class ForecastConfidence(str, enum.Enum):
    """Niveau de confiance des previsions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CERTAIN = "CERTAIN"


class ScenarioType(str, enum.Enum):
    """Type de scenario budgetaire."""
    BASELINE = "BASELINE"             # Scenario de base
    OPTIMISTIC = "OPTIMISTIC"         # Scenario optimiste
    PESSIMISTIC = "PESSIMISTIC"       # Scenario pessimiste
    WHAT_IF = "WHAT_IF"               # Scenario "Et si"
    STRESS_TEST = "STRESS_TEST"       # Test de stress


# ============================================================================
# MODELES PRINCIPAUX
# ============================================================================

class BudgetCategory(Base):
    """
    Categorie/Poste budgetaire.

    Permet de definir une hierarchie de postes budgetaires
    lies aux comptes comptables.
    """
    __tablename__ = "budget_categories"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Type
    line_type = Column(Enum(BudgetLineType), nullable=False, default=BudgetLineType.EXPENSE)

    # Hierarchie
    parent_id = Column(UniversalUUID(), ForeignKey("budget_categories.id"))
    level = Column(Integer, default=0)
    path = Column(String(500))  # Chemin hierarchique ex: "1/2/5"
    sort_order = Column(Integer, default=0)

    # Liaison comptable
    account_codes = Column(JSON, default=list)  # Comptes comptables lies
    default_account_id = Column(UniversalUUID())  # Compte par defaut

    # Parametres
    is_active = Column(Boolean, default=True)
    is_summary = Column(Boolean, default=False)  # Categorie de synthese
    allow_direct_posting = Column(Boolean, default=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1, nullable=False)

    # Relations
    parent = relationship("BudgetCategory", remote_side=[id], backref="children")
    budget_lines = relationship("BudgetLine", back_populates="category")

    __table_args__ = (
        Index("ix_budget_categories_tenant_code", "tenant_id", "code"),
        Index("ix_budget_categories_tenant_parent", "tenant_id", "parent_id"),
        Index("ix_budget_categories_tenant_active", "tenant_id", "is_active"),
        UniqueConstraint("tenant_id", "code", name="uq_budget_categories_tenant_code"),
    )


class Budget(Base):
    """
    Budget principal.

    Represente un budget complet avec ses parametres,
    son workflow d'approbation et son suivi.
    """
    __tablename__ = "budgets"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Type et statut
    budget_type = Column(Enum(BudgetType), nullable=False, default=BudgetType.OPERATING)
    status = Column(Enum(BudgetStatus), nullable=False, default=BudgetStatus.DRAFT)

    # Periode
    period_type = Column(Enum(BudgetPeriodType), nullable=False, default=BudgetPeriodType.ANNUAL)
    fiscal_year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Version et revision
    version_number = Column(Integer, default=1, nullable=False)
    is_current_version = Column(Boolean, default=True)
    parent_budget_id = Column(UniversalUUID(), ForeignKey("budgets.id"))  # Version precedente

    # Perimetre / Axes analytiques (inspire Sage)
    entity_id = Column(UniversalUUID())           # Entite/Societe
    department_id = Column(UniversalUUID())       # Departement
    cost_center_id = Column(UniversalUUID())      # Centre de couts
    project_id = Column(UniversalUUID())          # Projet
    product_line_id = Column(UniversalUUID())     # Ligne de produits
    region_id = Column(UniversalUUID())           # Region/Zone

    # Devise
    currency = Column(String(3), default="EUR", nullable=False)
    exchange_rate = Column(Numeric(15, 6), default=Decimal("1.0"))

    # Totaux (calcules)
    total_revenue = Column(Numeric(18, 2), default=Decimal("0"))
    total_expense = Column(Numeric(18, 2), default=Decimal("0"))
    total_investment = Column(Numeric(18, 2), default=Decimal("0"))
    net_result = Column(Numeric(18, 2), default=Decimal("0"))

    # Controle budgetaire (inspire Dynamics 365)
    control_mode = Column(Enum(ControlMode), default=ControlMode.WARNING_ONLY)
    warning_threshold = Column(Numeric(5, 2), default=Decimal("80.00"))  # % seuil alerte
    critical_threshold = Column(Numeric(5, 2), default=Decimal("95.00"))  # % seuil critique
    block_threshold = Column(Numeric(5, 2), default=Decimal("100.00"))  # % seuil blocage
    allow_override = Column(Boolean, default=False)  # Autoriser depassement

    # Workflow (inspire Odoo)
    owner_id = Column(UniversalUUID())
    approvers = Column(JSON, default=list)  # Liste des approbateurs
    approval_history = Column(JSON, default=list)
    submitted_at = Column(DateTime)
    submitted_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    approved_by = Column(UniversalUUID())
    activated_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Notes et commentaires
    notes = Column(Text)
    assumptions = Column(Text)  # Hypotheses budgetaires
    objectives = Column(Text)  # Objectifs

    # Parametres
    settings = Column(JSON, default=dict)
    tags = Column(JSON, default=list)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1, nullable=False)

    # Relations
    lines = relationship("BudgetLine", back_populates="budget", cascade="all, delete-orphan")
    periods = relationship("BudgetPeriod", back_populates="budget", cascade="all, delete-orphan")
    revisions = relationship("BudgetRevision", back_populates="budget", cascade="all, delete-orphan")
    alerts = relationship("BudgetAlert", back_populates="budget", cascade="all, delete-orphan")
    actuals = relationship("BudgetActual", back_populates="budget", cascade="all, delete-orphan")
    forecasts = relationship("BudgetForecast", back_populates="budget", cascade="all, delete-orphan")
    scenarios = relationship("BudgetScenario", back_populates="budget", cascade="all, delete-orphan")
    parent_budget = relationship("Budget", remote_side=[id], backref="child_versions")

    __table_args__ = (
        Index("ix_budgets_tenant_code", "tenant_id", "code"),
        Index("ix_budgets_tenant_type", "tenant_id", "budget_type"),
        Index("ix_budgets_tenant_status", "tenant_id", "status"),
        Index("ix_budgets_tenant_year", "tenant_id", "fiscal_year"),
        Index("ix_budgets_tenant_dates", "tenant_id", "start_date", "end_date"),
        Index("ix_budgets_tenant_entity", "tenant_id", "entity_id"),
        Index("ix_budgets_tenant_department", "tenant_id", "department_id"),
        CheckConstraint("end_date > start_date", name="check_budget_dates"),
        CheckConstraint("warning_threshold < critical_threshold", name="check_thresholds"),
    )


class BudgetLine(Base):
    """
    Ligne de budget.

    Detail d'un poste budgetaire avec repartition sur les periodes.
    """
    __tablename__ = "budget_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UniversalUUID(), ForeignKey("budget_categories.id"), nullable=False)

    # Identification
    code = Column(String(50))
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Type
    line_type = Column(Enum(BudgetLineType), nullable=False, default=BudgetLineType.EXPENSE)

    # Montant annuel
    annual_amount = Column(Numeric(18, 2), default=Decimal("0"), nullable=False)

    # Repartition mensuelle (JSON pour flexibilite)
    monthly_distribution = Column(JSON, default=dict)  # {1: amount, 2: amount, ...}

    # Methode de repartition
    allocation_method = Column(Enum(AllocationMethod), default=AllocationMethod.EQUAL)
    seasonal_profile = Column(String(50))  # Profil saisonnier
    allocation_weights = Column(JSON)  # Poids personnalises

    # Quantites (optionnel)
    quantity = Column(Numeric(15, 4))
    unit = Column(String(20))
    unit_price = Column(Numeric(15, 4))

    # Hierarchie
    parent_line_id = Column(UniversalUUID(), ForeignKey("budget_lines.id"))
    sort_order = Column(Integer, default=0)
    is_summary = Column(Boolean, default=False)

    # Axes analytiques (niveau ligne)
    cost_center_id = Column(UniversalUUID())
    project_id = Column(UniversalUUID())
    department_id = Column(UniversalUUID())

    # Compte comptable
    account_code = Column(String(20))
    account_id = Column(UniversalUUID())

    # Controle individuel
    has_custom_control = Column(Boolean, default=False)
    custom_warning_threshold = Column(Numeric(5, 2))
    custom_critical_threshold = Column(Numeric(5, 2))
    custom_block_threshold = Column(Numeric(5, 2))

    # Notes
    notes = Column(Text)
    assumptions = Column(Text)

    # Indicateurs calcules (mis a jour automatiquement)
    ytd_actual = Column(Numeric(18, 2), default=Decimal("0"))
    ytd_committed = Column(Numeric(18, 2), default=Decimal("0"))
    remaining_budget = Column(Numeric(18, 2), default=Decimal("0"))
    consumption_rate = Column(Numeric(8, 2), default=Decimal("0"))

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1, nullable=False)

    # Relations
    budget = relationship("Budget", back_populates="lines")
    category = relationship("BudgetCategory", back_populates="budget_lines")
    parent_line = relationship("BudgetLine", remote_side=[id], backref="child_lines")
    period_amounts = relationship("BudgetPeriodAmount", back_populates="budget_line", cascade="all, delete-orphan")
    actuals = relationship("BudgetActual", back_populates="budget_line")

    __table_args__ = (
        Index("ix_budget_lines_budget", "budget_id"),
        Index("ix_budget_lines_category", "category_id"),
        Index("ix_budget_lines_tenant_account", "tenant_id", "account_code"),
        Index("ix_budget_lines_cost_center", "tenant_id", "cost_center_id"),
    )


class BudgetPeriod(Base):
    """
    Periode budgetaire.

    Decoupage temporel du budget (mois, trimestre, etc.)
    avec totaux agreges.
    """
    __tablename__ = "budget_periods"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)

    # Identification
    period_number = Column(Integer, nullable=False)  # 1-12 pour mensuel
    name = Column(String(100), nullable=False)  # "Janvier 2026"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Statut
    is_open = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime)
    locked_by = Column(UniversalUUID())

    # Totaux periode (calcules)
    total_budget = Column(Numeric(18, 2), default=Decimal("0"))
    total_actual = Column(Numeric(18, 2), default=Decimal("0"))
    total_committed = Column(Numeric(18, 2), default=Decimal("0"))
    total_available = Column(Numeric(18, 2), default=Decimal("0"))
    variance = Column(Numeric(18, 2), default=Decimal("0"))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Relations
    budget = relationship("Budget", back_populates="periods")
    amounts = relationship("BudgetPeriodAmount", back_populates="period", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_budget_periods_budget", "budget_id"),
        Index("ix_budget_periods_dates", "tenant_id", "start_date", "end_date"),
        UniqueConstraint("budget_id", "period_number", name="uq_budget_period_number"),
    )


class BudgetPeriodAmount(Base):
    """
    Montant budgete par ligne et par periode.

    Permet un suivi detaille periode par periode.
    """
    __tablename__ = "budget_period_amounts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_line_id = Column(UniversalUUID(), ForeignKey("budget_lines.id", ondelete="CASCADE"), nullable=False)
    period_id = Column(UniversalUUID(), ForeignKey("budget_periods.id", ondelete="CASCADE"), nullable=False)

    # Montants
    budget_amount = Column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    actual_amount = Column(Numeric(18, 2), default=Decimal("0"))
    committed_amount = Column(Numeric(18, 2), default=Decimal("0"))
    forecast_amount = Column(Numeric(18, 2))  # Prevision revisee

    # Ecarts calcules
    variance_amount = Column(Numeric(18, 2), default=Decimal("0"))
    variance_percent = Column(Numeric(8, 2), default=Decimal("0"))
    variance_type = Column(Enum(VarianceType))

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    budget_line = relationship("BudgetLine", back_populates="period_amounts")
    period = relationship("BudgetPeriod", back_populates="amounts")

    __table_args__ = (
        Index("ix_budget_period_amounts_line", "budget_line_id"),
        Index("ix_budget_period_amounts_period", "period_id"),
        UniqueConstraint("budget_line_id", "period_id", name="uq_budget_line_period"),
    )


class BudgetRevision(Base):
    """
    Revision budgetaire.

    Permet de tracer les modifications du budget
    avec workflow d'approbation.
    """
    __tablename__ = "budget_revisions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)

    # Identification
    revision_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Statut
    status = Column(Enum(RevisionStatus), default=RevisionStatus.DRAFT, nullable=False)

    # Dates
    effective_date = Column(Date, nullable=False)
    submitted_at = Column(DateTime)
    submitted_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    approved_by = Column(UniversalUUID())
    applied_at = Column(DateTime)
    applied_by = Column(UniversalUUID())

    # Changements
    changes = Column(JSON, default=list)  # Liste des modifications
    total_change_amount = Column(Numeric(18, 2), default=Decimal("0"))

    # Justification
    reason = Column(Text, nullable=False)
    impact_analysis = Column(Text)
    supporting_documents = Column(JSON, default=list)

    # Approbation
    approvers = Column(JSON, default=list)
    approval_comments = Column(Text)
    rejection_reason = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1, nullable=False)

    # Relations
    budget = relationship("Budget", back_populates="revisions")
    details = relationship("BudgetRevisionDetail", back_populates="revision", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_budget_revisions_budget", "budget_id"),
        Index("ix_budget_revisions_status", "tenant_id", "status"),
        UniqueConstraint("budget_id", "revision_number", name="uq_budget_revision_number"),
    )


class BudgetRevisionDetail(Base):
    """Detail d'une revision budgetaire."""
    __tablename__ = "budget_revision_details"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    revision_id = Column(UniversalUUID(), ForeignKey("budget_revisions.id", ondelete="CASCADE"), nullable=False)
    budget_line_id = Column(UniversalUUID(), ForeignKey("budget_lines.id"))

    # Montants
    previous_amount = Column(Numeric(18, 2), nullable=False)
    new_amount = Column(Numeric(18, 2), nullable=False)
    change_amount = Column(Numeric(18, 2), nullable=False)

    # Periode affectee (optionnel)
    affected_period = Column(Integer)  # Numero de periode ou null pour annuel

    # Notes
    justification = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    revision = relationship("BudgetRevision", back_populates="details")

    __table_args__ = (
        Index("ix_revision_details_revision", "revision_id"),
    )


class BudgetActual(Base):
    """
    Montant realise (actuals).

    Enregistre les depenses/recettes reelles
    pour comparaison avec le budget.
    """
    __tablename__ = "budget_actuals"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    budget_line_id = Column(UniversalUUID(), ForeignKey("budget_lines.id"))

    # Periode
    period = Column(String(7), nullable=False)  # Format YYYY-MM
    period_date = Column(Date, nullable=False)

    # Montant
    amount = Column(Numeric(18, 2), nullable=False)
    line_type = Column(Enum(BudgetLineType), nullable=False)

    # Source
    source = Column(String(50), default="MANUAL")  # MANUAL, ACCOUNTING, IMPORT
    source_document_type = Column(String(50))  # invoice, payment, etc.
    source_document_id = Column(UniversalUUID())
    journal_entry_id = Column(UniversalUUID())

    # Reference
    reference = Column(String(100))
    description = Column(Text)

    # Analytique
    account_code = Column(String(20))
    cost_center_id = Column(UniversalUUID())
    project_id = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    budget = relationship("Budget", back_populates="actuals")
    budget_line = relationship("BudgetLine", back_populates="actuals")

    __table_args__ = (
        Index("ix_budget_actuals_budget", "budget_id"),
        Index("ix_budget_actuals_line", "budget_line_id"),
        Index("ix_budget_actuals_period", "tenant_id", "period"),
        Index("ix_budget_actuals_source", "tenant_id", "source_document_type", "source_document_id"),
    )


class BudgetAlert(Base):
    """
    Alerte budgetaire.

    Notifications de depassement ou d'approche des seuils.
    """
    __tablename__ = "budget_alerts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    budget_line_id = Column(UniversalUUID(), ForeignKey("budget_lines.id"))

    # Alert info
    alert_type = Column(String(50), nullable=False)  # THRESHOLD, TREND, ANOMALY
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False)

    # Contenu
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Metriques
    threshold_percent = Column(Numeric(8, 2))
    current_percent = Column(Numeric(8, 2))
    budget_amount = Column(Numeric(18, 2))
    actual_amount = Column(Numeric(18, 2))

    # Periode concernee
    period = Column(String(7))

    # Gestion
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(UniversalUUID())
    resolved_at = Column(DateTime)
    resolved_by = Column(UniversalUUID())
    resolution_notes = Column(Text)

    # Notifications envoyees
    notifications_sent = Column(JSON, default=list)

    # Relations
    budget = relationship("Budget", back_populates="alerts")

    __table_args__ = (
        Index("ix_budget_alerts_budget", "budget_id"),
        Index("ix_budget_alerts_status", "tenant_id", "status"),
        Index("ix_budget_alerts_severity", "tenant_id", "severity"),
    )


class BudgetForecast(Base):
    """
    Prevision budgetaire (Rolling Forecast).

    Permet de mettre a jour les previsions en cours d'annee
    sans modifier le budget initial.
    """
    __tablename__ = "budget_forecasts"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    budget_line_id = Column(UniversalUUID(), ForeignKey("budget_lines.id"))

    # Date de la prevision
    forecast_date = Column(Date, nullable=False)
    period = Column(String(7), nullable=False)  # YYYY-MM

    # Montants
    original_budget = Column(Numeric(18, 2), nullable=False)
    revised_forecast = Column(Numeric(18, 2), nullable=False)
    variance = Column(Numeric(18, 2), nullable=False)
    variance_percent = Column(Numeric(8, 2))

    # Confiance
    confidence = Column(Enum(ForecastConfidence), default=ForecastConfidence.MEDIUM)
    probability = Column(Numeric(5, 2))  # Probabilite 0-100

    # Justification
    assumptions = Column(Text)
    methodology = Column(String(100))  # linear, seasonal, ml, manual

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    budget = relationship("Budget", back_populates="forecasts")

    __table_args__ = (
        Index("ix_budget_forecasts_budget", "budget_id"),
        Index("ix_budget_forecasts_period", "tenant_id", "period"),
    )


class BudgetScenario(Base):
    """
    Scenario budgetaire.

    Permet de creer des simulations et analyses "what-if".
    """
    __tablename__ = "budget_scenarios"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    budget_id = Column(UniversalUUID(), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    scenario_type = Column(Enum(ScenarioType), default=ScenarioType.WHAT_IF, nullable=False)

    # Parametres
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Scenario par defaut

    # Ajustements globaux
    revenue_adjustment_percent = Column(Numeric(8, 2), default=Decimal("0"))
    expense_adjustment_percent = Column(Numeric(8, 2), default=Decimal("0"))

    # Hypotheses
    assumptions = Column(JSON, default=dict)
    parameters = Column(JSON, default=dict)

    # Resultats calcules
    total_revenue = Column(Numeric(18, 2), default=Decimal("0"))
    total_expense = Column(Numeric(18, 2), default=Decimal("0"))
    net_result = Column(Numeric(18, 2), default=Decimal("0"))
    variance_vs_baseline = Column(Numeric(18, 2))

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1, nullable=False)

    # Relations
    budget = relationship("Budget", back_populates="scenarios")
    lines = relationship("BudgetScenarioLine", back_populates="scenario", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_budget_scenarios_budget", "budget_id"),
        Index("ix_budget_scenarios_type", "tenant_id", "scenario_type"),
    )


class BudgetScenarioLine(Base):
    """Ligne de scenario avec ajustements."""
    __tablename__ = "budget_scenario_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    scenario_id = Column(UniversalUUID(), ForeignKey("budget_scenarios.id", ondelete="CASCADE"), nullable=False)
    budget_line_id = Column(UniversalUUID(), ForeignKey("budget_lines.id"), nullable=False)

    # Montants
    original_amount = Column(Numeric(18, 2), nullable=False)
    adjusted_amount = Column(Numeric(18, 2), nullable=False)
    adjustment_percent = Column(Numeric(8, 2))
    variance = Column(Numeric(18, 2))

    # Notes
    justification = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    scenario = relationship("BudgetScenario", back_populates="lines")

    __table_args__ = (
        Index("ix_scenario_lines_scenario", "scenario_id"),
    )


class BudgetConsolidation(Base):
    """
    Consolidation budgetaire.

    Permet de consolider plusieurs budgets
    (ex: par entite, par departement).
    """
    __tablename__ = "budget_consolidations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Configuration
    consolidation_type = Column(String(50), nullable=False)  # BY_ENTITY, BY_DEPARTMENT, CUSTOM
    fiscal_year = Column(Integer, nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)

    # Budgets inclus
    budget_ids = Column(JSON, default=list)
    exclude_intercompany = Column(Boolean, default=True)

    # Totaux consolides
    total_revenue = Column(Numeric(18, 2), default=Decimal("0"))
    total_expense = Column(Numeric(18, 2), default=Decimal("0"))
    total_investment = Column(Numeric(18, 2), default=Decimal("0"))
    net_result = Column(Numeric(18, 2), default=Decimal("0"))

    # Resultats
    consolidated_data = Column(JSON, default=dict)
    last_consolidated_at = Column(DateTime)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_budget_consolidations_tenant", "tenant_id"),
        Index("ix_budget_consolidations_year", "tenant_id", "fiscal_year"),
        UniqueConstraint("tenant_id", "code", name="uq_budget_consolidations_code"),
    )


class BudgetTemplate(Base):
    """
    Template de budget.

    Permet de creer des modeles reutilisables.
    """
    __tablename__ = "budget_templates"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Type
    budget_type = Column(Enum(BudgetType), nullable=False)
    period_type = Column(Enum(BudgetPeriodType), default=BudgetPeriodType.ANNUAL)

    # Structure du template
    line_template = Column(JSON, default=list)  # Structure des lignes
    category_ids = Column(JSON, default=list)  # Categories incluses
    default_allocation_method = Column(Enum(AllocationMethod), default=AllocationMethod.EQUAL)

    # Parametres par defaut
    default_settings = Column(JSON, default=dict)
    default_thresholds = Column(JSON, default=dict)

    # Statut
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # Template systeme

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(UniversalUUID())
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_budget_templates_tenant", "tenant_id"),
        Index("ix_budget_templates_type", "tenant_id", "budget_type"),
        UniqueConstraint("tenant_id", "code", name="uq_budget_templates_code"),
    )


class BudgetApprovalRule(Base):
    """
    Regle d'approbation budgetaire.

    Definit le workflow d'approbation selon les montants.
    """
    __tablename__ = "budget_approval_rules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Criteres
    budget_type = Column(Enum(BudgetType))  # Null = tous les types
    min_amount = Column(Numeric(18, 2), default=Decimal("0"))
    max_amount = Column(Numeric(18, 2))  # Null = pas de limite

    # Approbateurs
    approvers = Column(JSON, nullable=False)  # Liste des approbateurs
    approval_sequence = Column(String(20), default="sequential")  # sequential, parallel
    require_all = Column(Boolean, default=False)  # Tous doivent approuver

    # Parametres
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Plus petit = prioritaire

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_budget_approval_rules_tenant", "tenant_id"),
        Index("ix_budget_approval_rules_active", "tenant_id", "is_active"),
    )


class SeasonalProfile(Base):
    """
    Profil saisonnier pour la repartition budgetaire.

    Permet de definir des patterns de saisonnalite.
    """
    __tablename__ = "budget_seasonal_profiles"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Repartition mensuelle (pourcentages ou poids)
    # Format: [jan, fev, mar, avr, mai, jun, jul, aou, sep, oct, nov, dec]
    monthly_weights = Column(JSON, nullable=False)  # Liste de 12 valeurs

    # Parametres
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # Profil systeme (retail, tourisme, etc.)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_seasonal_profiles_tenant", "tenant_id"),
        UniqueConstraint("tenant_id", "code", name="uq_seasonal_profiles_code"),
    )
