"""
AZALS MODULE - CONSOLIDATION: Modeles SQLAlchemy
==================================================

Module de Consolidation Comptable Multi-Entites pour AZALSCORE ERP.

Fonctionnalites:
- Perimetre de consolidation (filiales)
- Methodes (integration globale, proportionnelle, equivalence)
- Eliminations intra-groupe
- Conversions devises
- Retraitements
- Etats consolides (bilan, compte de resultat)
- Liasse de consolidation
- Reconciliation inter-societes
- Ecarts d'acquisition
- Rapports reglementaires

Normes supportees:
- Reglement ANC 2020-01 (France)
- IFRS 10, 11, 12 (international)
- US GAAP ASC 810 (Etats-Unis)

REGLES CRITIQUES:
- tenant_id obligatoire sur toutes les tables
- Soft delete (is_deleted, deleted_at, deleted_by)
- Audit complet (created_by, updated_by, created_at, updated_at)
- Versioning (version)
- _base_query() filtre par tenant_id

Auteur: AZALSCORE Team
Version: 1.0.0
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
# ENUMS
# ============================================================================

class ConsolidationMethod(str, enum.Enum):
    """Methode de consolidation."""
    FULL_INTEGRATION = "full_integration"      # Integration globale (>50% controle)
    PROPORTIONAL = "proportional"              # Integration proportionnelle (co-entreprises)
    EQUITY_METHOD = "equity_method"            # Mise en equivalence (20-50% influence notable)
    NOT_CONSOLIDATED = "not_consolidated"      # Non consolide (<20%)


class ControlType(str, enum.Enum):
    """Type de controle."""
    EXCLUSIVE = "exclusive"                    # Controle exclusif
    JOINT = "joint"                            # Controle conjoint
    SIGNIFICANT_INFLUENCE = "significant_influence"  # Influence notable
    NONE = "none"                              # Pas de controle


class AccountingStandard(str, enum.Enum):
    """Referentiel comptable."""
    FRENCH_GAAP = "french_gaap"               # PCG / Reglement ANC 2020-01
    IFRS = "ifrs"                             # Normes internationales IFRS 10/11/12
    US_GAAP = "us_gaap"                       # Normes americaines ASC 810


class EliminationType(str, enum.Enum):
    """Type d'elimination intra-groupe."""
    INTERCOMPANY_SALES = "intercompany_sales"            # Ventes intra-groupe
    INTERCOMPANY_RECEIVABLES = "intercompany_receivables"  # Creances/dettes
    INTERCOMPANY_DIVIDENDS = "intercompany_dividends"    # Dividendes
    INTERCOMPANY_PROVISIONS = "intercompany_provisions"  # Provisions
    INTERNAL_MARGIN = "internal_margin"                  # Marges sur stocks
    INTERNAL_FIXED_ASSETS = "internal_fixed_assets"      # Plus-values immos
    CAPITAL_ELIMINATION = "capital_elimination"          # Titres vs capitaux propres


class ConsolidationStatus(str, enum.Enum):
    """Statut d'une consolidation."""
    DRAFT = "draft"                           # Brouillon
    IN_PROGRESS = "in_progress"               # En cours
    PENDING_REVIEW = "pending_review"         # En attente de revue
    VALIDATED = "validated"                   # Validee
    PUBLISHED = "published"                   # Publiee
    ARCHIVED = "archived"                     # Archivee


class PackageStatus(str, enum.Enum):
    """Statut d'un paquet de consolidation."""
    NOT_STARTED = "not_started"               # Non demarre
    IN_PROGRESS = "in_progress"               # En cours de saisie
    SUBMITTED = "submitted"                   # Soumis
    VALIDATED = "validated"                   # Valide
    REJECTED = "rejected"                     # Rejete


class RestatementType(str, enum.Enum):
    """Type de retraitement."""
    LEASE_IFRS16 = "lease_ifrs16"             # Retraitement bail IFRS 16
    PENSION_IAS19 = "pension_ias19"           # Engagements retraite IAS 19
    REVENUE_IFRS15 = "revenue_ifrs15"         # Reconnaissance revenu IFRS 15
    DEPRECIATION = "depreciation"             # Harmonisation amortissements
    PROVISION = "provision"                   # Provisions groupe
    TAX_DEFERRED = "tax_deferred"             # Impots differes
    CUSTOM = "custom"                         # Retraitement personnalise


class CurrencyConversionMethod(str, enum.Enum):
    """Methode de conversion des devises."""
    CLOSING_RATE = "closing_rate"             # Cours de cloture (actifs/passifs)
    AVERAGE_RATE = "average_rate"             # Cours moyen (compte de resultat)
    HISTORICAL_RATE = "historical_rate"       # Cours historique (capitaux propres)


class ReportType(str, enum.Enum):
    """Type de rapport consolide."""
    BALANCE_SHEET = "balance_sheet"           # Bilan consolide
    INCOME_STATEMENT = "income_statement"     # Compte de resultat consolide
    CASH_FLOW = "cash_flow"                   # Tableau des flux de tresorerie
    EQUITY_VARIATION = "equity_variation"     # Tableau de variation des capitaux propres
    SEGMENT_REPORT = "segment_report"         # Information sectorielle
    CONSOLIDATION_PACKAGE = "consolidation_package"  # Liasse de consolidation


# ============================================================================
# MODELE: PERIMETRE DE CONSOLIDATION
# ============================================================================

class ConsolidationPerimeter(Base):
    """
    Perimetre de consolidation.

    Definit l'ensemble des entites juridiques incluses dans
    le perimetre de consolidation pour une periode donnee.
    """
    __tablename__ = "consolidation_perimeters"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Periode
    fiscal_year = Column(Integer, nullable=False)  # Annee fiscale
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Configuration
    consolidation_currency = Column(String(3), default="EUR", nullable=False)
    accounting_standard = Column(
        Enum(AccountingStandard, name='conso_accounting_standard'),
        default=AccountingStandard.FRENCH_GAAP,
        nullable=False
    )

    # Statut
    status = Column(
        Enum(ConsolidationStatus, name='conso_perimeter_status'),
        default=ConsolidationStatus.DRAFT,
        nullable=False
    )
    is_active = Column(Boolean, default=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    entities = relationship("ConsolidationEntity", back_populates="perimeter", lazy="dynamic")
    consolidations = relationship("Consolidation", back_populates="perimeter", lazy="dynamic")

    __table_args__ = (
        Index("ix_conso_perimeter_tenant", "tenant_id"),
        Index("ix_conso_perimeter_code", "tenant_id", "code"),
        Index("ix_conso_perimeter_fiscal_year", "tenant_id", "fiscal_year"),
        Index("ix_conso_perimeter_status", "tenant_id", "status"),
        UniqueConstraint("tenant_id", "code", "fiscal_year", name="uq_conso_perimeter_code_year"),
        CheckConstraint("end_date > start_date", name="check_perimeter_dates"),
    )


class ConsolidationEntity(Base):
    """
    Entite juridique du groupe.

    Represente une societe ou filiale incluse dans le perimetre
    de consolidation avec ses caracteristiques de participation.
    """
    __tablename__ = "consolidation_entities"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien perimetre
    perimeter_id = Column(UniversalUUID(), ForeignKey("consolidation_perimeters.id"), nullable=False)

    # Identification
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    registration_number = Column(String(50))  # SIREN, numero d'identification
    country = Column(String(3), nullable=False)  # Code ISO pays
    currency = Column(String(3), nullable=False)  # Devise locale

    # Classification
    is_parent = Column(Boolean, default=False)  # Societe mere
    parent_entity_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"))

    # Methode de consolidation
    consolidation_method = Column(
        Enum(ConsolidationMethod, name='conso_method'),
        default=ConsolidationMethod.NOT_CONSOLIDATED,
        nullable=False
    )
    control_type = Column(
        Enum(ControlType, name='conso_control_type'),
        default=ControlType.NONE,
        nullable=False
    )

    # Participation
    direct_ownership_pct = Column(Numeric(6, 3), default=Decimal("0.000"))  # % detention directe
    indirect_ownership_pct = Column(Numeric(6, 3), default=Decimal("0.000"))  # % detention indirecte
    total_ownership_pct = Column(Numeric(6, 3), default=Decimal("0.000"))  # % detention totale
    voting_rights_pct = Column(Numeric(6, 3), default=Decimal("0.000"))  # % droits de vote
    integration_pct = Column(Numeric(6, 3), default=Decimal("100.000"))  # % integration (pour proportionnelle)

    # Dates cles
    acquisition_date = Column(Date)
    disposal_date = Column(Date)
    fiscal_year_end_month = Column(Integer, default=12)  # Mois de cloture (1-12)

    # Secteur/Segment (pour reporting sectoriel)
    sector = Column(String(100))
    segment = Column(String(100))

    # Configuration specifique
    config = Column(JSON, default=dict)

    # Statut
    is_active = Column(Boolean, default=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    perimeter = relationship("ConsolidationPerimeter", back_populates="entities")
    parent = relationship("ConsolidationEntity", remote_side=[id], backref="subsidiaries")
    participations = relationship("Participation", back_populates="subsidiary", foreign_keys="Participation.subsidiary_id")
    packages = relationship("ConsolidationPackage", back_populates="entity", lazy="dynamic")

    __table_args__ = (
        Index("ix_conso_entity_tenant", "tenant_id"),
        Index("ix_conso_entity_perimeter", "perimeter_id"),
        Index("ix_conso_entity_code", "tenant_id", "perimeter_id", "code"),
        Index("ix_conso_entity_method", "consolidation_method"),
        Index("ix_conso_entity_parent", "parent_entity_id"),
        UniqueConstraint("tenant_id", "perimeter_id", "code", name="uq_conso_entity_code"),
        CheckConstraint("direct_ownership_pct >= 0 AND direct_ownership_pct <= 100", name="check_direct_ownership"),
        CheckConstraint("total_ownership_pct >= 0 AND total_ownership_pct <= 100", name="check_total_ownership"),
        CheckConstraint("fiscal_year_end_month >= 1 AND fiscal_year_end_month <= 12", name="check_fiscal_month"),
    )


class Participation(Base):
    """
    Lien de participation entre entites.

    Represente la relation capitalistique entre une societe
    mere et une filiale avec les details d'acquisition.
    """
    __tablename__ = "consolidation_participations"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Entites liees
    parent_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"), nullable=False)
    subsidiary_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"), nullable=False)

    # Pourcentages
    direct_ownership = Column(Numeric(6, 3), nullable=False)  # Detention directe
    indirect_ownership = Column(Numeric(6, 3), default=Decimal("0.000"))  # Via autres filiales
    total_ownership = Column(Numeric(6, 3), default=Decimal("0.000"))  # Total
    voting_rights = Column(Numeric(6, 3), default=Decimal("0.000"))

    # Acquisition
    acquisition_date = Column(Date, nullable=False)
    acquisition_cost = Column(Numeric(18, 2), default=Decimal("0.00"))  # Cout d'acquisition
    fair_value_at_acquisition = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Goodwill (Ecart d'acquisition)
    goodwill_amount = Column(Numeric(18, 2), default=Decimal("0.00"))
    goodwill_impairment = Column(Numeric(18, 2), default=Decimal("0.00"))
    goodwill_currency = Column(String(3), default="EUR")

    # Notes
    notes = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    parent = relationship("ConsolidationEntity", foreign_keys=[parent_id])
    subsidiary = relationship("ConsolidationEntity", back_populates="participations", foreign_keys=[subsidiary_id])

    __table_args__ = (
        Index("ix_participation_tenant", "tenant_id"),
        Index("ix_participation_parent", "parent_id"),
        Index("ix_participation_subsidiary", "subsidiary_id"),
        UniqueConstraint("tenant_id", "parent_id", "subsidiary_id", name="uq_participation_link"),
        CheckConstraint("direct_ownership >= 0 AND direct_ownership <= 100", name="check_part_direct_ownership"),
        CheckConstraint("goodwill_amount >= 0", name="check_goodwill_positive"),
    )


# ============================================================================
# MODELE: COURS DE CHANGE
# ============================================================================

class ExchangeRate(Base):
    """
    Cours de change pour la consolidation.

    Stocke les differents cours (cloture, moyen, historique)
    necessaires pour la conversion des devises.
    """
    __tablename__ = "consolidation_exchange_rates"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Devises
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)

    # Date
    rate_date = Column(Date, nullable=False)

    # Cours
    closing_rate = Column(Numeric(18, 8), nullable=False)  # Cours de cloture
    average_rate = Column(Numeric(18, 8), nullable=False)  # Cours moyen periode
    historical_rate = Column(Numeric(18, 8))  # Cours historique si pertinent

    # Source
    source = Column(String(100))  # BCE, Reuters, etc.

    # Audit
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_exchange_rate_tenant", "tenant_id"),
        Index("ix_exchange_rate_currencies", "tenant_id", "from_currency", "to_currency"),
        Index("ix_exchange_rate_date", "tenant_id", "rate_date"),
        UniqueConstraint("tenant_id", "from_currency", "to_currency", "rate_date", name="uq_exchange_rate"),
        CheckConstraint("closing_rate > 0", name="check_closing_rate_positive"),
        CheckConstraint("average_rate > 0", name="check_average_rate_positive"),
    )


# ============================================================================
# MODELE: CONSOLIDATION
# ============================================================================

class Consolidation(Base):
    """
    Consolidation comptable.

    Represente un processus de consolidation complet pour
    une periode et un perimetre donnes.
    """
    __tablename__ = "consolidations"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien perimetre
    perimeter_id = Column(UniversalUUID(), ForeignKey("consolidation_perimeters.id"), nullable=False)

    # Identification
    code = Column(String(30), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Periode
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    period_type = Column(String(20), default="annual")  # annual, quarterly, monthly

    # Configuration
    consolidation_currency = Column(String(3), default="EUR", nullable=False)
    accounting_standard = Column(
        Enum(AccountingStandard, name='conso_standard'),
        default=AccountingStandard.FRENCH_GAAP,
        nullable=False
    )

    # Statut
    status = Column(
        Enum(ConsolidationStatus, name='conso_status'),
        default=ConsolidationStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Resultats agreges
    total_assets = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_liabilities = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_equity = Column(Numeric(18, 2), default=Decimal("0.00"))
    group_equity = Column(Numeric(18, 2), default=Decimal("0.00"))
    minority_interests = Column(Numeric(18, 2), default=Decimal("0.00"))
    consolidated_revenue = Column(Numeric(18, 2), default=Decimal("0.00"))
    consolidated_net_income = Column(Numeric(18, 2), default=Decimal("0.00"))
    group_net_income = Column(Numeric(18, 2), default=Decimal("0.00"))
    minority_net_income = Column(Numeric(18, 2), default=Decimal("0.00"))
    translation_difference = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_goodwill = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Workflow
    submitted_at = Column(DateTime)
    submitted_by = Column(UniversalUUID())
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())
    published_at = Column(DateTime)
    published_by = Column(UniversalUUID())

    # Metadonnees
    metadata = Column(JSON, default=dict)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    perimeter = relationship("ConsolidationPerimeter", back_populates="consolidations")
    packages = relationship("ConsolidationPackage", back_populates="consolidation", lazy="dynamic")
    eliminations = relationship("EliminationEntry", back_populates="consolidation", lazy="dynamic")
    restatements = relationship("Restatement", back_populates="consolidation", lazy="dynamic")
    reconciliations = relationship("IntercompanyReconciliation", back_populates="consolidation", lazy="dynamic")
    reports = relationship("ConsolidatedReport", back_populates="consolidation", lazy="dynamic")

    __table_args__ = (
        Index("ix_consolidation_tenant", "tenant_id"),
        Index("ix_consolidation_perimeter", "perimeter_id"),
        Index("ix_consolidation_code", "tenant_id", "code"),
        Index("ix_consolidation_period", "tenant_id", "period_start", "period_end"),
        Index("ix_consolidation_status", "tenant_id", "status"),
        Index("ix_consolidation_fiscal_year", "tenant_id", "fiscal_year"),
        UniqueConstraint("tenant_id", "code", name="uq_consolidation_code"),
        CheckConstraint("period_end >= period_start", name="check_conso_period"),
    )


# ============================================================================
# MODELE: PAQUET DE CONSOLIDATION
# ============================================================================

class ConsolidationPackage(Base):
    """
    Paquet de consolidation (liasse).

    Contient les donnees comptables d'une entite pour
    la consolidation (balance, interco, etc.).
    """
    __tablename__ = "consolidation_packages"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"), nullable=False)
    entity_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"), nullable=False)

    # Periode
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Devise
    local_currency = Column(String(3), nullable=False)
    reporting_currency = Column(String(3), nullable=False)  # Devise de consolidation

    # Cours de change utilises
    closing_rate = Column(Numeric(18, 8))
    average_rate = Column(Numeric(18, 8))

    # Totaux en devise locale
    total_assets_local = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_liabilities_local = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_equity_local = Column(Numeric(18, 2), default=Decimal("0.00"))
    net_income_local = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Totaux convertis
    total_assets_converted = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_liabilities_converted = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_equity_converted = Column(Numeric(18, 2), default=Decimal("0.00"))
    net_income_converted = Column(Numeric(18, 2), default=Decimal("0.00"))
    translation_difference = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Intercompany totals
    intercompany_receivables = Column(Numeric(18, 2), default=Decimal("0.00"))
    intercompany_payables = Column(Numeric(18, 2), default=Decimal("0.00"))
    intercompany_sales = Column(Numeric(18, 2), default=Decimal("0.00"))
    intercompany_purchases = Column(Numeric(18, 2), default=Decimal("0.00"))
    dividends_to_parent = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Balance detaillee (JSON pour flexibilite)
    trial_balance = Column(JSON, default=list)
    intercompany_details = Column(JSON, default=list)

    # Statut
    status = Column(
        Enum(PackageStatus, name='conso_package_status'),
        default=PackageStatus.NOT_STARTED,
        nullable=False
    )
    is_audited = Column(Boolean, default=False)
    auditor_notes = Column(Text)

    # Workflow
    submitted_at = Column(DateTime)
    submitted_by = Column(UniversalUUID())
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())
    rejected_at = Column(DateTime)
    rejected_by = Column(UniversalUUID())
    rejection_reason = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    consolidation = relationship("Consolidation", back_populates="packages")
    entity = relationship("ConsolidationEntity", back_populates="packages")

    __table_args__ = (
        Index("ix_conso_package_tenant", "tenant_id"),
        Index("ix_conso_package_consolidation", "consolidation_id"),
        Index("ix_conso_package_entity", "entity_id"),
        Index("ix_conso_package_status", "status"),
        UniqueConstraint("tenant_id", "consolidation_id", "entity_id", name="uq_conso_package"),
    )


# ============================================================================
# MODELE: ELIMINATIONS
# ============================================================================

class EliminationEntry(Base):
    """
    Ecriture d'elimination intra-groupe.

    Represente une ecriture d'elimination generee
    automatiquement ou manuellement.
    """
    __tablename__ = "consolidation_eliminations"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien consolidation
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"), nullable=False)

    # Type d'elimination
    elimination_type = Column(
        Enum(EliminationType, name='conso_elimination_type'),
        nullable=False
    )

    # Identification
    code = Column(String(30))
    description = Column(Text, nullable=False)

    # Entites concernees
    entity1_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"))
    entity2_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"))

    # Montants
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Lignes d'ecriture (JSON pour flexibilite)
    journal_entries = Column(JSON, default=list)
    # Format: [{"account": "xxx", "debit": 0, "credit": 0, "label": "", "entity_id": ""}]

    # Source
    source_document_type = Column(String(50))  # intercompany_transaction, manual, etc.
    source_document_id = Column(UniversalUUID())
    is_automatic = Column(Boolean, default=True)

    # Validation
    is_validated = Column(Boolean, default=False)
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    consolidation = relationship("Consolidation", back_populates="eliminations")
    entity1 = relationship("ConsolidationEntity", foreign_keys=[entity1_id])
    entity2 = relationship("ConsolidationEntity", foreign_keys=[entity2_id])

    __table_args__ = (
        Index("ix_elimination_tenant", "tenant_id"),
        Index("ix_elimination_consolidation", "consolidation_id"),
        Index("ix_elimination_type", "elimination_type"),
        Index("ix_elimination_entities", "entity1_id", "entity2_id"),
    )


# ============================================================================
# MODELE: RETRAITEMENTS
# ============================================================================

class Restatement(Base):
    """
    Retraitement de consolidation.

    Ajustements necessaires pour harmoniser les normes
    comptables au sein du groupe (IFRS 16, IAS 19, etc.).
    """
    __tablename__ = "consolidation_restatements"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien consolidation et entite
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"), nullable=False)
    entity_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"), nullable=False)

    # Type de retraitement
    restatement_type = Column(
        Enum(RestatementType, name='conso_restatement_type'),
        nullable=False
    )

    # Identification
    code = Column(String(30))
    description = Column(Text, nullable=False)

    # Norme applicable
    standard_reference = Column(String(50))  # Ex: "IFRS 16", "IAS 19"

    # Montants
    impact_assets = Column(Numeric(18, 2), default=Decimal("0.00"))
    impact_liabilities = Column(Numeric(18, 2), default=Decimal("0.00"))
    impact_equity = Column(Numeric(18, 2), default=Decimal("0.00"))
    impact_income = Column(Numeric(18, 2), default=Decimal("0.00"))
    impact_expense = Column(Numeric(18, 2), default=Decimal("0.00"))
    tax_impact = Column(Numeric(18, 2), default=Decimal("0.00"))  # Impact fiscal

    # Lignes d'ecriture detaillees
    journal_entries = Column(JSON, default=list)

    # Documentation
    calculation_details = Column(JSON, default=dict)  # Details du calcul
    supporting_documents = Column(JSON, default=list)  # Pieces justificatives

    # Recurrence
    is_recurring = Column(Boolean, default=False)  # Retraitement recurrent
    recurrence_pattern = Column(String(50))  # monthly, quarterly, annual

    # Validation
    is_validated = Column(Boolean, default=False)
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    consolidation = relationship("Consolidation", back_populates="restatements")
    entity = relationship("ConsolidationEntity")

    __table_args__ = (
        Index("ix_restatement_tenant", "tenant_id"),
        Index("ix_restatement_consolidation", "consolidation_id"),
        Index("ix_restatement_entity", "entity_id"),
        Index("ix_restatement_type", "restatement_type"),
    )


# ============================================================================
# MODELE: RECONCILIATION INTER-SOCIETES
# ============================================================================

class IntercompanyReconciliation(Base):
    """
    Reconciliation inter-societes.

    Rapprochement des soldes et transactions entre
    entites du groupe pour identifier les ecarts.
    """
    __tablename__ = "consolidation_interco_reconciliations"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien consolidation
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"), nullable=False)

    # Entites concernees
    entity1_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"), nullable=False)
    entity2_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"), nullable=False)

    # Type de flux
    transaction_type = Column(String(50), nullable=False)  # receivable, payable, sale, purchase, loan, etc.

    # Montants declares
    amount_entity1 = Column(Numeric(18, 2), nullable=False)  # Montant declare par entite 1
    amount_entity2 = Column(Numeric(18, 2), nullable=False)  # Montant declare par entite 2
    currency = Column(String(3), default="EUR")

    # Ecart
    difference = Column(Numeric(18, 2), default=Decimal("0.00"))
    difference_pct = Column(Numeric(8, 4), default=Decimal("0.0000"))  # En pourcentage
    difference_reason = Column(Text)  # Explication de l'ecart

    # Statut de reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    reconciled_by = Column(UniversalUUID())

    # Tolerance
    tolerance_amount = Column(Numeric(18, 2), default=Decimal("0.00"))
    tolerance_pct = Column(Numeric(8, 4), default=Decimal("0.0000"))
    is_within_tolerance = Column(Boolean, default=True)

    # Actions requises
    action_required = Column(Text)
    action_taken = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    consolidation = relationship("Consolidation", back_populates="reconciliations")
    entity1 = relationship("ConsolidationEntity", foreign_keys=[entity1_id])
    entity2 = relationship("ConsolidationEntity", foreign_keys=[entity2_id])

    __table_args__ = (
        Index("ix_interco_recon_tenant", "tenant_id"),
        Index("ix_interco_recon_consolidation", "consolidation_id"),
        Index("ix_interco_recon_entities", "entity1_id", "entity2_id"),
        Index("ix_interco_recon_status", "is_reconciled"),
    )


# ============================================================================
# MODELE: ECART D'ACQUISITION (GOODWILL)
# ============================================================================

class GoodwillCalculation(Base):
    """
    Calcul et suivi des ecarts d'acquisition.

    Goodwill = Cout d'acquisition - Quote-part actif net a la juste valeur.
    """
    __tablename__ = "consolidation_goodwill"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"), nullable=False)
    participation_id = Column(UniversalUUID(), ForeignKey("consolidation_participations.id"), nullable=False)

    # Date de calcul
    calculation_date = Column(Date, nullable=False)

    # Cout d'acquisition
    acquisition_cost = Column(Numeric(18, 2), nullable=False)
    acquisition_currency = Column(String(3), default="EUR")

    # Actif net a la juste valeur
    assets_fair_value = Column(Numeric(18, 2), default=Decimal("0.00"))
    liabilities_fair_value = Column(Numeric(18, 2), default=Decimal("0.00"))
    net_assets_fair_value = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Quote-part groupe
    ownership_percentage = Column(Numeric(6, 3), nullable=False)
    group_share_net_assets = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Goodwill
    goodwill_amount = Column(Numeric(18, 2), default=Decimal("0.00"))
    badwill_amount = Column(Numeric(18, 2), default=Decimal("0.00"))  # Si negatif

    # Depreciation
    cumulative_impairment = Column(Numeric(18, 2), default=Decimal("0.00"))
    current_period_impairment = Column(Numeric(18, 2), default=Decimal("0.00"))
    carrying_value = Column(Numeric(18, 2), default=Decimal("0.00"))  # Valeur nette comptable

    # Details des ajustements de juste valeur
    revaluation_adjustments = Column(JSON, default=list)

    # Documentation
    impairment_test_date = Column(Date)
    impairment_test_result = Column(JSON, default=dict)
    notes = Column(Text)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    consolidation = relationship("Consolidation")
    participation = relationship("Participation")

    __table_args__ = (
        Index("ix_goodwill_tenant", "tenant_id"),
        Index("ix_goodwill_consolidation", "consolidation_id"),
        Index("ix_goodwill_participation", "participation_id"),
        Index("ix_goodwill_date", "calculation_date"),
    )


# ============================================================================
# MODELE: INTERETS MINORITAIRES
# ============================================================================

class MinorityInterest(Base):
    """
    Interets minoritaires (participations ne donnant pas le controle).

    Calcul de la part des minoritaires dans les capitaux propres
    et le resultat des filiales non detenues a 100%.
    """
    __tablename__ = "consolidation_minority_interests"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Liens
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"), nullable=False)
    entity_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"), nullable=False)

    # Periode
    period_end = Column(Date, nullable=False)

    # Pourcentages
    group_ownership_pct = Column(Numeric(6, 3), nullable=False)
    minority_pct = Column(Numeric(6, 3), nullable=False)

    # Capitaux propres
    total_equity = Column(Numeric(18, 2), default=Decimal("0.00"))
    group_share_equity = Column(Numeric(18, 2), default=Decimal("0.00"))
    minority_share_equity = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Resultat
    net_income = Column(Numeric(18, 2), default=Decimal("0.00"))
    group_share_income = Column(Numeric(18, 2), default=Decimal("0.00"))
    minority_share_income = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Autres elements du resultat global (OCI)
    other_comprehensive_income = Column(Numeric(18, 2), default=Decimal("0.00"))
    minority_share_oci = Column(Numeric(18, 2), default=Decimal("0.00"))

    # Devise
    currency = Column(String(3), default="EUR")

    # Notes
    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    consolidation = relationship("Consolidation")
    entity = relationship("ConsolidationEntity")

    __table_args__ = (
        Index("ix_minority_tenant", "tenant_id"),
        Index("ix_minority_consolidation", "consolidation_id"),
        Index("ix_minority_entity", "entity_id"),
        UniqueConstraint("tenant_id", "consolidation_id", "entity_id", name="uq_minority_interest"),
    )


# ============================================================================
# MODELE: RAPPORTS CONSOLIDES
# ============================================================================

class ConsolidatedReport(Base):
    """
    Rapport financier consolide.

    Stocke les etats financiers consolides generes
    (bilan, compte de resultat, flux de tresorerie, etc.).
    """
    __tablename__ = "consolidation_reports"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien consolidation
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"), nullable=False)

    # Type de rapport
    report_type = Column(
        Enum(ReportType, name='conso_report_type'),
        nullable=False
    )

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Periode
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Contenu du rapport (JSON structure)
    report_data = Column(JSON, nullable=False, default=dict)
    # Structure selon le type:
    # - balance_sheet: {assets: [...], liabilities: [...], equity: [...]}
    # - income_statement: {revenues: [...], expenses: [...], result: ...}
    # etc.

    # Donnees comparatives
    comparative_data = Column(JSON, default=dict)  # Periode precedente

    # Parametres de generation
    parameters = Column(JSON, default=dict)

    # Export
    pdf_url = Column(String(500))
    excel_url = Column(String(500))
    generated_at = Column(DateTime)

    # Validation
    is_final = Column(Boolean, default=False)
    finalized_at = Column(DateTime)
    finalized_by = Column(UniversalUUID())

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(UniversalUUID())

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    updated_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    consolidation = relationship("Consolidation", back_populates="reports")

    __table_args__ = (
        Index("ix_conso_report_tenant", "tenant_id"),
        Index("ix_conso_report_consolidation", "consolidation_id"),
        Index("ix_conso_report_type", "report_type"),
        Index("ix_conso_report_period", "period_start", "period_end"),
    )


# ============================================================================
# MODELE: MAPPING COMPTES
# ============================================================================

class AccountMapping(Base):
    """
    Mapping des comptes entre plan local et plan consolide.

    Permet d'harmoniser les plans comptables des differentes
    entites vers le plan comptable groupe.
    """
    __tablename__ = "consolidation_account_mappings"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien perimetre
    perimeter_id = Column(UniversalUUID(), ForeignKey("consolidation_perimeters.id"), nullable=False)

    # Entite (optionnel si mapping global)
    entity_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"))

    # Compte local
    local_account_code = Column(String(20), nullable=False)
    local_account_label = Column(String(255))

    # Compte consolide
    group_account_code = Column(String(20), nullable=False)
    group_account_label = Column(String(255))

    # Categorie de reporting
    reporting_category = Column(String(100))  # assets, liabilities, equity, revenue, expense
    reporting_subcategory = Column(String(100))

    # Comportement de conversion
    currency_method = Column(
        Enum(CurrencyConversionMethod, name='conso_currency_method'),
        default=CurrencyConversionMethod.CLOSING_RATE
    )

    # Statut
    is_active = Column(Boolean, default=True)

    # Audit
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_account_mapping_tenant", "tenant_id"),
        Index("ix_account_mapping_perimeter", "perimeter_id"),
        Index("ix_account_mapping_entity", "entity_id"),
        Index("ix_account_mapping_local", "local_account_code"),
        Index("ix_account_mapping_group", "group_account_code"),
        UniqueConstraint("tenant_id", "perimeter_id", "entity_id", "local_account_code",
                        name="uq_account_mapping"),
    )


# ============================================================================
# MODELE: JOURNAL D'AUDIT CONSOLIDATION
# ============================================================================

class ConsolidationAuditLog(Base):
    """
    Journal d'audit pour les operations de consolidation.

    Trace toutes les actions effectuees sur le processus
    de consolidation pour conformite et audit.
    """
    __tablename__ = "consolidation_audit_logs"

    # Cle primaire + tenant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Reference
    consolidation_id = Column(UniversalUUID(), ForeignKey("consolidations.id"))
    entity_id = Column(UniversalUUID(), ForeignKey("consolidation_entities.id"))

    # Action
    action = Column(String(100), nullable=False)  # create, update, delete, validate, publish, etc.
    action_category = Column(String(50))  # perimeter, package, elimination, report, etc.

    # Entite cible
    target_type = Column(String(100))  # Nom du modele
    target_id = Column(UniversalUUID())

    # Details
    old_values = Column(JSON, default=dict)
    new_values = Column(JSON, default=dict)
    description = Column(Text)

    # Utilisateur
    user_id = Column(UniversalUUID(), nullable=False)
    user_name = Column(String(255))
    user_ip = Column(String(50))

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_conso_audit_tenant", "tenant_id"),
        Index("ix_conso_audit_consolidation", "consolidation_id"),
        Index("ix_conso_audit_action", "action"),
        Index("ix_conso_audit_timestamp", "timestamp"),
        Index("ix_conso_audit_user", "user_id"),
        Index("ix_conso_audit_target", "target_type", "target_id"),
    )
