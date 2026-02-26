"""
Models SQLAlchemy - Module Commissions (GAP-041)

Modeles complets pour la gestion des commissions commerciales.
CRITIQUE: Tous les modeles ont tenant_id pour isolation multi-tenant.
Soft delete, audit complet, versioning.

Inspire de:
- Sage: Plans de commission flexibles
- Axonaut: Simplicity of commission rules
- Pennylane: Integration comptable
- Odoo: Commission multi-niveaux
- Microsoft Dynamics 365: Sales performance management
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Numeric,
    ForeignKey, Index, Date, Float, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.core.types import JSON, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class CommissionBasis(str, Enum):
    """Base de calcul des commissions."""
    REVENUE = "revenue"  # Chiffre d'affaires HT
    REVENUE_TTC = "revenue_ttc"  # Chiffre d'affaires TTC
    MARGIN = "margin"  # Marge brute
    MARGIN_PERCENT = "margin_percent"  # Pourcentage de marge
    GROSS_PROFIT = "gross_profit"  # Benefice brut
    VOLUME = "volume"  # Nombre d'unites vendues
    CONTRACT_VALUE = "contract_value"  # Valeur contrat (recurrent)
    NEW_BUSINESS = "new_business"  # Nouveau client uniquement
    UPSELL = "upsell"  # Ventes additionnelles
    RENEWAL = "renewal"  # Renouvellements
    COLLECTED = "collected"  # Montant encaisse


class TierType(str, Enum):
    """Type de paliers de commission."""
    FLAT = "flat"  # Taux fixe unique
    PROGRESSIVE = "progressive"  # Paliers progressifs (chaque tranche a son taux)
    RETROACTIVE = "retroactive"  # Retroactif (taux du palier atteint sur tout)
    REGRESSIVE = "regressive"  # Degressif (taux baisse avec volume)
    STEPPED = "stepped"  # Par paliers avec bonus


class CommissionStatus(str, Enum):
    """Statut d'une commission calculee."""
    DRAFT = "draft"  # Brouillon
    PENDING = "pending"  # En attente de validation
    CALCULATED = "calculated"  # Calculee automatiquement
    APPROVED = "approved"  # Approuvee
    DISPUTED = "disputed"  # Contestee
    ADJUSTED = "adjusted"  # Ajustee manuellement
    VALIDATED = "validated"  # Validee pour paiement
    PAID = "paid"  # Payee
    CANCELLED = "cancelled"  # Annulee
    CLAWBACK = "clawback"  # Recuperation


class PlanStatus(str, Enum):
    """Statut d'un plan de commissionnement."""
    DRAFT = "draft"  # En cours de creation
    PENDING_APPROVAL = "pending_approval"  # En attente validation
    ACTIVE = "active"  # Actif
    SUSPENDED = "suspended"  # Suspendu
    EXPIRED = "expired"  # Expire
    ARCHIVED = "archived"  # Archive


class PaymentFrequency(str, Enum):
    """Frequence de paiement des commissions."""
    IMMEDIATE = "immediate"  # A la facturation
    WEEKLY = "weekly"  # Hebdomadaire
    BIWEEKLY = "biweekly"  # Bi-mensuel
    MONTHLY = "monthly"  # Mensuel
    QUARTERLY = "quarterly"  # Trimestriel
    SEMI_ANNUAL = "semi_annual"  # Semestriel
    ANNUAL = "annual"  # Annuel
    ON_PAYMENT = "on_payment"  # A l'encaissement
    ON_DELIVERY = "on_delivery"  # A la livraison


class PeriodType(str, Enum):
    """Type de periode de commissionnement."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class AdjustmentType(str, Enum):
    """Type d'ajustement de commission."""
    BONUS = "bonus"  # Bonus additionnel
    PENALTY = "penalty"  # Penalite
    CORRECTION = "correction"  # Correction d'erreur
    CLAWBACK = "clawback"  # Recuperation
    ADVANCE = "advance"  # Avance sur commission
    GUARANTEE = "guarantee"  # Minimum garanti
    OVERRIDE = "override"  # Override manager
    SPIFF = "spiff"  # Incentive ponctuel


class WorkflowStatus(str, Enum):
    """Statut du workflow de validation."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


# ============================================================================
# MODELES PLANS DE COMMISSION
# ============================================================================

class CommissionPlan(Base):
    """Plan de commissionnement."""
    __tablename__ = "commission_plans"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Configuration de base
    basis = Column(String(30), default=CommissionBasis.REVENUE.value)
    tier_type = Column(String(30), default=TierType.FLAT.value)
    payment_frequency = Column(String(30), default=PaymentFrequency.MONTHLY.value)

    # Statut
    status = Column(String(30), default=PlanStatus.DRAFT.value)

    # Periode de quota
    quota_period = Column(String(30), default=PeriodType.MONTHLY.value)
    quota_amount = Column(Numeric(18, 4))  # Objectif

    # Plafonnement
    cap_enabled = Column(Boolean, default=False)
    cap_amount = Column(Numeric(18, 4))  # Plafond montant
    cap_percent = Column(Float)  # Plafond % salaire base

    # Minimum garanti
    minimum_guaranteed = Column(Numeric(18, 4), default=0)
    minimum_guaranteed_period = Column(String(30))

    # Clawback (recuperation si annulation)
    clawback_enabled = Column(Boolean, default=True)
    clawback_period_days = Column(Integer, default=90)
    clawback_percent = Column(Float, default=100.0)  # % a recuperer

    # Conditions declenchement
    trigger_on_invoice = Column(Boolean, default=True)  # Declenchement facture
    trigger_on_payment = Column(Boolean, default=False)  # Declenchement encaissement
    trigger_on_delivery = Column(Boolean, default=False)  # Declenchement livraison

    # Eligibilite
    eligibility_rules = Column(JSON, default=dict)
    # {"min_tenure_days": 90, "min_performance_score": 70, "required_certifications": []}

    # Produits/Services concernes
    apply_to_all_products = Column(Boolean, default=True)
    included_products = Column(JSON, default=list)  # IDs produits inclus
    excluded_products = Column(JSON, default=list)  # IDs produits exclus
    included_categories = Column(JSON, default=list)
    excluded_categories = Column(JSON, default=list)

    # Clients concernes
    apply_to_all_customers = Column(Boolean, default=True)
    included_customer_segments = Column(JSON, default=list)
    excluded_customer_segments = Column(JSON, default=list)
    new_customers_only = Column(Boolean, default=False)

    # Dates de validite
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)

    # Devise
    currency = Column(String(3), default="EUR")

    # Priorite (si plusieurs plans applicables)
    priority = Column(Integer, default=100)

    # Configuration avancee
    settings = Column(JSON, default=dict)
    # {"prorate_partial_period": true, "round_to": 2, "include_returns": false}

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    approved_by = Column(UniversalUUID())

    # Relations
    tiers = relationship("CommissionTier", back_populates="plan", cascade="all, delete-orphan")
    accelerators = relationship("CommissionAccelerator", back_populates="plan", cascade="all, delete-orphan")
    assignments = relationship("CommissionAssignment", back_populates="plan")
    calculations = relationship("CommissionCalculation", back_populates="plan")

    __table_args__ = (
        Index("ix_commission_plans_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_commission_plans_tenant_status", "tenant_id", "status"),
        Index("ix_commission_plans_tenant_dates", "tenant_id", "effective_from", "effective_to"),
        Index("ix_commission_plans_tenant_deleted", "tenant_id", "is_deleted"),
    )


class CommissionTier(Base):
    """Palier de commission."""
    __tablename__ = "commission_tiers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    plan_id = Column(UniversalUUID(), ForeignKey("commission_plans.id", ondelete="CASCADE"), nullable=False)

    # Identification
    tier_number = Column(Integer, nullable=False)  # Ordre du palier
    name = Column(String(100))

    # Seuils
    min_value = Column(Numeric(18, 4), nullable=False, default=0)
    max_value = Column(Numeric(18, 4))  # NULL = illimite

    # Taux et montants
    rate = Column(Numeric(8, 4), nullable=False)  # Pourcentage (ex: 5.00 = 5%)
    fixed_amount = Column(Numeric(18, 4), default=0)  # Montant fixe additionnel

    # Bonus de palier (pour tier_type STEPPED)
    tier_bonus = Column(Numeric(18, 4), default=0)

    # Metadonnees
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relation
    plan = relationship("CommissionPlan", back_populates="tiers")

    __table_args__ = (
        Index("ix_commission_tiers_plan", "plan_id", "tier_number"),
        CheckConstraint("rate >= 0 AND rate <= 100", name="ck_tier_rate_range"),
    )


class CommissionAccelerator(Base):
    """Accelerateur de performance."""
    __tablename__ = "commission_accelerators"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    plan_id = Column(UniversalUUID(), ForeignKey("commission_plans.id", ondelete="CASCADE"), nullable=False)

    # Identification
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Condition de declenchement
    threshold_type = Column(String(30), nullable=False)
    # "quota_percent", "absolute_amount", "growth_percent", "rank", "streak"
    threshold_value = Column(Numeric(18, 4), nullable=False)
    threshold_operator = Column(String(10), default=">=")  # >=, >, =, <, <=

    # Multiplicateur ou bonus
    multiplier = Column(Numeric(6, 4), default=1)  # Ex: 1.5 = +50%
    bonus_amount = Column(Numeric(18, 4), default=0)  # Bonus fixe
    bonus_percent = Column(Numeric(6, 4), default=0)  # Bonus en %

    # Cumul
    is_cumulative = Column(Boolean, default=False)  # Se cumule avec autres accelerateurs

    # Dates de validite
    valid_from = Column(Date)
    valid_to = Column(Date)

    # Limites
    max_applications = Column(Integer)  # Nombre max d'applications
    max_bonus_amount = Column(Numeric(18, 4))

    # Metadonnees
    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relation
    plan = relationship("CommissionPlan", back_populates="accelerators")

    __table_args__ = (
        Index("ix_commission_accelerators_plan", "plan_id", "is_active"),
    )


# ============================================================================
# MODELES ATTRIBUTION
# ============================================================================

class CommissionAssignment(Base):
    """Attribution d'un plan a un commercial/equipe."""
    __tablename__ = "commission_assignments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Plan
    plan_id = Column(UniversalUUID(), ForeignKey("commission_plans.id"), nullable=False)

    # Beneficiaire
    assignee_type = Column(String(30), nullable=False)  # "employee", "team", "territory", "role"
    assignee_id = Column(UniversalUUID(), nullable=False)
    assignee_name = Column(String(255))  # Cache pour affichage

    # Quota specifique (override du plan)
    quota_override = Column(Numeric(18, 4))
    quota_currency = Column(String(3), default="EUR")

    # Dates
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)

    # Statut
    is_active = Column(Boolean, default=True)

    # Override personnel
    personal_rate_override = Column(Numeric(8, 4))  # Override du taux
    personal_cap_override = Column(Numeric(18, 4))  # Override du plafond

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    plan = relationship("CommissionPlan", back_populates="assignments")

    __table_args__ = (
        Index("ix_commission_assignments_tenant_assignee", "tenant_id", "assignee_type", "assignee_id"),
        Index("ix_commission_assignments_plan_active", "plan_id", "is_active"),
        Index("ix_commission_assignments_dates", "effective_from", "effective_to"),
    )


class SalesTeamMember(Base):
    """Membre d'equipe commerciale avec hierarchie."""
    __tablename__ = "commission_team_members"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Employe
    employee_id = Column(UniversalUUID(), nullable=False)
    employee_name = Column(String(255))
    employee_email = Column(String(255))

    # Role
    role = Column(String(50), nullable=False)
    # "sales_rep", "senior_rep", "account_executive", "team_lead", "sales_manager", "director", "vp"

    # Hierarchie
    parent_id = Column(UniversalUUID(), ForeignKey("commission_team_members.id"))
    team_id = Column(UniversalUUID())
    team_name = Column(String(100))
    territory = Column(String(100))

    # Override manager (touche % sur ventes equipe)
    override_enabled = Column(Boolean, default=False)
    override_rate = Column(Numeric(6, 4), default=0)
    override_basis = Column(String(30), default=CommissionBasis.REVENUE.value)
    override_levels = Column(Integer, default=1)  # Niveaux de profondeur

    # Split par defaut
    default_split_percent = Column(Numeric(6, 4), default=100)

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    parent = relationship("SalesTeamMember", remote_side=[id], backref="subordinates")

    __table_args__ = (
        Index("ix_team_members_tenant_employee", "tenant_id", "employee_id"),
        Index("ix_team_members_tenant_team", "tenant_id", "team_id"),
        Index("ix_team_members_tenant_parent", "tenant_id", "parent_id"),
        Index("ix_team_members_tenant_active", "tenant_id", "is_active"),
    )


# ============================================================================
# MODELES TRANSACTIONS & CALCULS
# ============================================================================

class CommissionTransaction(Base):
    """Transaction de vente declenchant une commission."""
    __tablename__ = "commission_transactions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Reference source
    source_type = Column(String(30), nullable=False)
    # "invoice", "order", "contract", "subscription", "payment"
    source_id = Column(UniversalUUID(), nullable=False)
    source_number = Column(String(100))  # Numero facture/commande
    source_date = Column(Date, nullable=False)

    # Commercial principal
    sales_rep_id = Column(UniversalUUID(), nullable=False, index=True)
    sales_rep_name = Column(String(255))

    # Client
    customer_id = Column(UniversalUUID(), nullable=False)
    customer_name = Column(String(255))
    customer_segment = Column(String(50))
    is_new_customer = Column(Boolean, default=False)

    # Produit/Service
    product_id = Column(UniversalUUID())
    product_code = Column(String(50))
    product_name = Column(String(255))
    product_category = Column(String(100))

    # Montants
    revenue = Column(Numeric(18, 4), nullable=False)  # CA HT
    revenue_ttc = Column(Numeric(18, 4))  # CA TTC
    cost = Column(Numeric(18, 4), default=0)  # Cout
    margin = Column(Numeric(18, 4))  # Marge
    margin_percent = Column(Numeric(6, 4))  # % marge
    quantity = Column(Numeric(12, 4), default=1)
    currency = Column(String(3), default="EUR")

    # Classification
    transaction_type = Column(String(30), default="standard")
    # "standard", "new_business", "upsell", "cross_sell", "renewal", "expansion"
    is_recurring = Column(Boolean, default=False)
    contract_months = Column(Integer)  # Duree contrat si recurrent

    # Paiement
    payment_status = Column(String(30), default="pending")
    # "pending", "partial", "paid", "overdue", "written_off"
    payment_date = Column(Date)
    payment_amount = Column(Numeric(18, 4))

    # Livraison
    delivery_status = Column(String(30))
    delivery_date = Column(Date)

    # Split (partage de commission)
    has_split = Column(Boolean, default=False)
    split_config = Column(JSON, default=list)
    # [{"participant_id": "uuid", "role": "primary", "percent": 60}, ...]

    # Statut commission
    commission_status = Column(String(30), default="pending")
    # "pending", "calculated", "approved", "paid", "cancelled"
    commission_locked = Column(Boolean, default=False)

    # Liens
    opportunity_id = Column(UniversalUUID())
    campaign_id = Column(UniversalUUID())

    # Metadonnees
    extra_data = Column(JSON, default=dict)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    calculations = relationship("CommissionCalculation", back_populates="transaction")

    __table_args__ = (
        Index("ix_comm_transactions_tenant_source", "tenant_id", "source_type", "source_id"),
        Index("ix_comm_transactions_tenant_rep", "tenant_id", "sales_rep_id"),
        Index("ix_comm_transactions_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_comm_transactions_tenant_date", "tenant_id", "source_date"),
        Index("ix_comm_transactions_tenant_status", "tenant_id", "commission_status"),
        Index("ix_comm_transactions_tenant_deleted", "tenant_id", "is_deleted"),
    )


class CommissionCalculation(Base):
    """Calcul de commission."""
    __tablename__ = "commission_calculations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # References
    transaction_id = Column(UniversalUUID(), ForeignKey("commission_transactions.id"))
    plan_id = Column(UniversalUUID(), ForeignKey("commission_plans.id"), nullable=False)
    period_id = Column(UniversalUUID(), ForeignKey("commission_periods.id"))

    # Beneficiaire
    sales_rep_id = Column(UniversalUUID(), nullable=False, index=True)
    sales_rep_name = Column(String(255))

    # Periode
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Base de calcul
    basis = Column(String(30), nullable=False)
    base_amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(3), default="EUR")

    # Calcul
    rate_applied = Column(Numeric(8, 4))  # Taux applique
    tier_applied = Column(String(100))  # Palier applique
    commission_amount = Column(Numeric(18, 4), nullable=False)

    # Accelerateurs
    accelerator_bonus = Column(Numeric(18, 4), default=0)
    accelerators_applied = Column(JSON, default=list)  # IDs des accelerateurs

    # Split
    split_percent = Column(Numeric(6, 4), default=100)
    split_role = Column(String(30))  # "primary", "secondary", "overlay", "partner"
    original_amount = Column(Numeric(18, 4))  # Avant split

    # Total
    gross_commission = Column(Numeric(18, 4), nullable=False)
    adjustments = Column(Numeric(18, 4), default=0)
    net_commission = Column(Numeric(18, 4), nullable=False)

    # Plafonnement
    cap_applied = Column(Boolean, default=False)
    cap_amount = Column(Numeric(18, 4))
    pre_cap_amount = Column(Numeric(18, 4))

    # Quota
    quota_target = Column(Numeric(18, 4))
    quota_achieved = Column(Numeric(18, 4))
    achievement_rate = Column(Numeric(8, 4))  # En %

    # Details du calcul
    calculation_details = Column(JSON, default=dict)
    # {"tier_breakdown": [...], "accelerator_details": [...], "split_details": {...}}

    # Statut
    status = Column(String(30), default=CommissionStatus.CALCULATED.value)

    # Dates workflow
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculated_by = Column(String(50))  # "system" ou user_id
    approved_at = Column(DateTime)
    approved_by = Column(UniversalUUID())
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())
    paid_at = Column(DateTime)

    # Paiement
    payment_reference = Column(String(100))
    statement_id = Column(UniversalUUID())

    # Notes
    notes = Column(Text)
    dispute_reason = Column(Text)
    adjustment_reason = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    transaction = relationship("CommissionTransaction", back_populates="calculations")
    plan = relationship("CommissionPlan", back_populates="calculations")
    period = relationship("CommissionPeriod", back_populates="calculations")

    __table_args__ = (
        Index("ix_comm_calculations_tenant_rep", "tenant_id", "sales_rep_id"),
        Index("ix_comm_calculations_tenant_period", "tenant_id", "period_start", "period_end"),
        Index("ix_comm_calculations_tenant_status", "tenant_id", "status"),
        Index("ix_comm_calculations_tenant_plan", "tenant_id", "plan_id"),
        Index("ix_comm_calculations_period_id", "period_id"),
        Index("ix_comm_calculations_tenant_deleted", "tenant_id", "is_deleted"),
    )


# ============================================================================
# MODELES PERIODES & RELEVES
# ============================================================================

class CommissionPeriod(Base):
    """Periode de commissionnement."""
    __tablename__ = "commission_periods"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)  # "2024-M01", "2024-Q1"
    name = Column(String(100), nullable=False)  # "Janvier 2024", "Q1 2024"
    period_type = Column(String(30), nullable=False)

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    close_date = Column(Date)  # Date limite de cloture
    payment_date = Column(Date)  # Date de paiement prevue

    # Statut
    status = Column(String(30), default="open")
    # "open", "calculating", "review", "approved", "closed", "paid"
    is_locked = Column(Boolean, default=False)

    # Totaux
    total_commissions = Column(Numeric(18, 4), default=0)
    total_adjustments = Column(Numeric(18, 4), default=0)
    total_clawbacks = Column(Numeric(18, 4), default=0)
    total_paid = Column(Numeric(18, 4), default=0)
    transaction_count = Column(Integer, default=0)
    calculation_count = Column(Integer, default=0)

    # Workflow
    calculated_at = Column(DateTime)
    calculated_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    approved_by = Column(UniversalUUID())
    closed_at = Column(DateTime)
    closed_by = Column(UniversalUUID())

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    calculations = relationship("CommissionCalculation", back_populates="period")
    statements = relationship("CommissionStatement", back_populates="period")

    __table_args__ = (
        Index("ix_commission_periods_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_commission_periods_tenant_dates", "tenant_id", "start_date", "end_date"),
        Index("ix_commission_periods_tenant_status", "tenant_id", "status"),
    )


class CommissionStatement(Base):
    """Releve de commission (pour paiement)."""
    __tablename__ = "commission_statements"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    statement_number = Column(String(50), nullable=False)
    period_id = Column(UniversalUUID(), ForeignKey("commission_periods.id"), nullable=False)

    # Beneficiaire
    sales_rep_id = Column(UniversalUUID(), nullable=False, index=True)
    sales_rep_name = Column(String(255))
    sales_rep_email = Column(String(255))

    # Periode
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Montants
    gross_commissions = Column(Numeric(18, 4), default=0)
    accelerator_bonuses = Column(Numeric(18, 4), default=0)
    adjustments = Column(Numeric(18, 4), default=0)
    clawbacks = Column(Numeric(18, 4), default=0)
    advances = Column(Numeric(18, 4), default=0)  # Avances deja versees
    net_commission = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(3), default="EUR")

    # Cumuls
    ytd_commissions = Column(Numeric(18, 4), default=0)
    ytd_sales = Column(Numeric(18, 4), default=0)
    ytd_quota_achievement = Column(Numeric(8, 4))

    # Nombre de transactions
    transaction_count = Column(Integer, default=0)

    # Details
    calculation_ids = Column(JSON, default=list)  # IDs des calculs inclus
    details = Column(JSON, default=dict)  # Details par plan, produit, etc.

    # Statut
    status = Column(String(30), default=CommissionStatus.PENDING.value)

    # Workflow
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(String(50))
    reviewed_at = Column(DateTime)
    reviewed_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    approved_by = Column(UniversalUUID())
    paid_at = Column(DateTime)
    payment_reference = Column(String(100))
    payment_method = Column(String(50))

    # Integration paie
    payroll_exported = Column(Boolean, default=False)
    payroll_export_date = Column(DateTime)
    payroll_reference = Column(String(100))

    # Notes
    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    period = relationship("CommissionPeriod", back_populates="statements")

    __table_args__ = (
        Index("ix_comm_statements_tenant_number", "tenant_id", "statement_number", unique=True),
        Index("ix_comm_statements_tenant_rep", "tenant_id", "sales_rep_id"),
        Index("ix_comm_statements_tenant_period", "tenant_id", "period_id"),
        Index("ix_comm_statements_tenant_status", "tenant_id", "status"),
    )


# ============================================================================
# MODELES AJUSTEMENTS & CLAWBACKS
# ============================================================================

class CommissionAdjustment(Base):
    """Ajustement manuel de commission."""
    __tablename__ = "commission_adjustments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Reference
    code = Column(String(50), nullable=False)
    adjustment_type = Column(String(30), nullable=False)

    # Beneficiaire
    sales_rep_id = Column(UniversalUUID(), nullable=False, index=True)
    sales_rep_name = Column(String(255))

    # Periode
    period_id = Column(UniversalUUID(), ForeignKey("commission_periods.id"))
    effective_date = Column(Date, nullable=False)

    # Montant
    amount = Column(Numeric(18, 4), nullable=False)  # Positif ou negatif
    currency = Column(String(3), default="EUR")

    # Calcul lie (si correction)
    related_calculation_id = Column(UniversalUUID(), ForeignKey("commission_calculations.id"))
    related_transaction_id = Column(UniversalUUID())

    # Justification
    reason = Column(Text, nullable=False)
    supporting_documents = Column(JSON, default=list)

    # Statut
    status = Column(String(30), default=WorkflowStatus.PENDING.value)

    # Workflow
    requested_by = Column(UniversalUUID(), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    rejected_by = Column(UniversalUUID())
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Paiement
    statement_id = Column(UniversalUUID())
    paid_at = Column(DateTime)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_comm_adjustments_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_comm_adjustments_tenant_rep", "tenant_id", "sales_rep_id"),
        Index("ix_comm_adjustments_tenant_type", "tenant_id", "adjustment_type"),
        Index("ix_comm_adjustments_tenant_status", "tenant_id", "status"),
        Index("ix_comm_adjustments_tenant_deleted", "tenant_id", "is_deleted"),
    )


class CommissionClawback(Base):
    """Recuperation de commission (annulation/remboursement client)."""
    __tablename__ = "commission_clawbacks"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Reference
    code = Column(String(50), nullable=False)

    # Calcul original
    original_calculation_id = Column(UniversalUUID(), ForeignKey("commission_calculations.id"), nullable=False)
    original_transaction_id = Column(UniversalUUID(), nullable=False)
    original_commission = Column(Numeric(18, 4), nullable=False)

    # Beneficiaire
    sales_rep_id = Column(UniversalUUID(), nullable=False, index=True)
    sales_rep_name = Column(String(255))

    # Montant a recuperer
    clawback_amount = Column(Numeric(18, 4), nullable=False)
    clawback_percent = Column(Numeric(6, 4), default=100)
    currency = Column(String(3), default="EUR")

    # Raison
    reason = Column(String(50), nullable=False)
    # "cancellation", "refund", "chargeback", "return", "credit_note", "error"
    reason_details = Column(Text)
    cancellation_date = Column(Date, nullable=False)

    # Document source (avoir, remboursement, etc.)
    source_document_type = Column(String(30))
    source_document_id = Column(UniversalUUID())
    source_document_number = Column(String(100))

    # Statut
    status = Column(String(30), default="pending")
    # "pending", "approved", "applied", "waived", "partial"

    # Application
    applied_to_statement_id = Column(UniversalUUID())
    applied_at = Column(DateTime)
    applied_amount = Column(Numeric(18, 4))
    remaining_amount = Column(Numeric(18, 4))

    # Workflow
    created_by = Column(UniversalUUID())
    approved_by = Column(UniversalUUID())
    approved_at = Column(DateTime)
    waived_by = Column(UniversalUUID())
    waived_at = Column(DateTime)
    waiver_reason = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_comm_clawbacks_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_comm_clawbacks_tenant_rep", "tenant_id", "sales_rep_id"),
        Index("ix_comm_clawbacks_tenant_status", "tenant_id", "status"),
        Index("ix_comm_clawbacks_original_calc", "original_calculation_id"),
    )


# ============================================================================
# MODELES WORKFLOW VALIDATION
# ============================================================================

class CommissionWorkflow(Base):
    """Workflow de validation des commissions."""
    __tablename__ = "commission_workflows"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type de workflow
    workflow_type = Column(String(30), nullable=False)
    # "period_approval", "adjustment_approval", "plan_approval", "clawback_waiver"

    # Entite concernee
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(UniversalUUID(), nullable=False)

    # Etape actuelle
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=1)
    current_approver_role = Column(String(50))
    current_approver_id = Column(UniversalUUID())

    # Statut
    status = Column(String(30), default=WorkflowStatus.PENDING.value)

    # Montant concerne
    amount = Column(Numeric(18, 4))
    currency = Column(String(3), default="EUR")

    # Historique
    history = Column(JSON, default=list)
    # [{"step": 1, "action": "approved", "by": "uuid", "at": "datetime", "comments": "..."}]

    # Dates
    initiated_at = Column(DateTime, default=datetime.utcnow)
    initiated_by = Column(UniversalUUID())
    due_date = Column(DateTime)
    completed_at = Column(DateTime)

    # Notes
    comments = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_comm_workflows_tenant_type", "tenant_id", "workflow_type"),
        Index("ix_comm_workflows_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_comm_workflows_tenant_status", "tenant_id", "status"),
        Index("ix_comm_workflows_approver", "current_approver_id"),
    )


# ============================================================================
# MODELE AUDIT TRAIL
# ============================================================================

class CommissionAuditLog(Base):
    """Journal d'audit des commissions."""
    __tablename__ = "commission_audit_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Action
    action = Column(String(50), nullable=False)
    # "plan_created", "plan_updated", "calculation_created", "calculation_adjusted",
    # "statement_generated", "statement_approved", "clawback_created", etc.

    # Entite concernee
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(UniversalUUID(), nullable=False)
    entity_code = Column(String(100))

    # Acteur
    user_id = Column(UniversalUUID(), nullable=False)
    user_name = Column(String(255))
    user_role = Column(String(50))

    # Details
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes = Column(JSON)
    extra_info = Column(JSON, default=dict)

    # Context
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    session_id = Column(String(100))

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_comm_audit_tenant_action", "tenant_id", "action"),
        Index("ix_comm_audit_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_comm_audit_tenant_user", "tenant_id", "user_id"),
        Index("ix_comm_audit_tenant_created", "tenant_id", "created_at"),
    )
