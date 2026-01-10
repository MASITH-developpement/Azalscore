"""
AZALS - PACK PAYS FRANCE - Modèles
===================================
Modèles SQLAlchemy pour la localisation française.

Inclut:
- PCG 2024 (Plan Comptable Général)
- TVA française
- FEC (Fichier des Écritures Comptables)
- DSN (Déclaration Sociale Nominative)
- RGPD

MIGRATED: All PKs and FKs use UUID for PostgreSQL compatibility.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text

from app.db import Base
from app.core.types import UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

# ============================================================================
# ENUMS
# ============================================================================

class PCGClass(str, PyEnum):
    """Classes du PCG français."""
    CLASSE_1 = "1"  # Comptes de capitaux
    CLASSE_2 = "2"  # Comptes d'immobilisations
    CLASSE_3 = "3"  # Comptes de stocks et en-cours
    CLASSE_4 = "4"  # Comptes de tiers
    CLASSE_5 = "5"  # Comptes financiers
    CLASSE_6 = "6"  # Comptes de charges
    CLASSE_7 = "7"  # Comptes de produits
    CLASSE_8 = "8"  # Comptes spéciaux


class TVARate(str, PyEnum):
    """Taux de TVA France."""
    NORMAL = "NORMAL"        # 20%
    INTERMEDIAIRE = "INTER"  # 10%
    REDUIT = "REDUIT"        # 5.5%
    SUPER_REDUIT = "SUPER"   # 2.1%
    EXONERE = "EXONERE"      # 0%


class TVARegime(str, PyEnum):
    """Régimes de TVA."""
    REEL_NORMAL = "REEL_NORMAL"
    REEL_SIMPLIFIE = "REEL_SIMPLIFIE"
    FRANCHISE = "FRANCHISE"
    MINI_REEL = "MINI_REEL"
    AGRICOLE = "AGRICOLE"


class FECStatus(str, PyEnum):
    """Statuts de génération FEC."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    EXPORTED = "EXPORTED"
    ARCHIVED = "ARCHIVED"


class DSNType(str, PyEnum):
    """Types de DSN."""
    MENSUELLE = "MENSUELLE"
    EVENEMENTIELLE = "EVENEMENTIELLE"
    FIN_CONTRAT = "FIN_CONTRAT"
    REPRISE_HISTORIQUE = "REPRISE_HISTORIQUE"


class DSNStatus(str, PyEnum):
    """Statuts de la DSN."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"


class ContractType(str, PyEnum):
    """Types de contrats français."""
    CDI = "CDI"
    CDD = "CDD"
    CTT = "CTT"  # Intérim
    APPRENTISSAGE = "APPRENTISSAGE"
    PROFESSIONALISATION = "PROFESSIONALISATION"
    STAGE = "STAGE"
    VIE = "VIE"  # Volontariat International
    MANDATAIRE = "MANDATAIRE"


class RGPDConsentStatus(str, PyEnum):
    """Statuts de consentement RGPD."""
    PENDING = "PENDING"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    WITHDRAWN = "WITHDRAWN"


class RGPDRequestType(str, PyEnum):
    """Types de demandes RGPD."""
    ACCESS = "ACCESS"              # Droit d'accès
    RECTIFICATION = "RECTIFICATION"  # Droit de rectification
    ERASURE = "ERASURE"            # Droit à l'effacement
    PORTABILITY = "PORTABILITY"    # Droit à la portabilité
    OPPOSITION = "OPPOSITION"      # Droit d'opposition
    LIMITATION = "LIMITATION"      # Droit à la limitation


# ============================================================================
# PCG - PLAN COMPTABLE GÉNÉRAL
# ============================================================================

class PCGAccount(Base):
    """Compte du Plan Comptable Général français."""
    __tablename__ = "fr_pcg_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    account_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=False)  # Ex: 411000
    account_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)

    # Classification PCG
    pcg_class: Mapped[Optional[str]] = mapped_column(Enum(PCGClass), nullable=False)
    parent_account: Mapped[Optional[str]] = mapped_column(String(10))  # Compte parent

    # Type
    is_summary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)  # Compte de regroupement
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_custom: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)  # Créé par le tenant

    # Soldes
    normal_balance: Mapped[Optional[str]] = mapped_column(String(1), default="D")  # D=Débit, C=Crédit

    # TVA associée
    default_vat_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Notes
    description: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_pcg_tenant', 'tenant_id'),
        Index('idx_fr_pcg_number', 'tenant_id', 'account_number', unique=True),
        Index('idx_fr_pcg_class', 'tenant_id', 'pcg_class'),
    )


# ============================================================================
# TVA FRANÇAISE
# ============================================================================

class FRVATRate(Base):
    """Taux de TVA français."""
    __tablename__ = "fr_vat_rates"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=False)  # TVA_20, TVA_10, etc.
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    rate_type: Mapped[Optional[str]] = mapped_column(Enum(TVARate), nullable=False)
    rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=False)  # 20.00, 10.00, etc.

    # Comptes comptables associés
    account_collected: Mapped[Optional[str]] = mapped_column(String(10))   # 44571
    account_deductible: Mapped[Optional[str]] = mapped_column(String(10))  # 44566
    account_intra_eu: Mapped[Optional[str]] = mapped_column(String(10))    # 4452
    account_payable: Mapped[Optional[str]] = mapped_column(String(10))     # 44551

    # Applicabilité
    applies_to_goods: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    applies_to_services: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_intra_eu: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_import: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Mentions légales
    legal_mention: Mapped[Optional[str]] = mapped_column(Text)  # Mention sur facture si exonéré

    # Validité
    valid_from: Mapped[Optional[date]] = mapped_column(Date, default=date.today)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_fr_vat_tenant', 'tenant_id'),
        Index('idx_fr_vat_code', 'tenant_id', 'code', unique=True),
    )


class FRVATDeclaration(Base):
    """Déclaration de TVA (CA3, CA12)."""
    __tablename__ = "fr_vat_declarations"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    declaration_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False)
    declaration_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=False)  # CA3, CA12
    regime: Mapped[Optional[str]] = mapped_column(Enum(TVARegime), nullable=False)

    # Période
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    due_date: Mapped[Optional[date]] = mapped_column(Date)

    # Montants
    total_ht: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    total_tva_collectee: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    total_tva_deductible: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    tva_nette: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)  # Collectée - Déductible
    credit_tva: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)

    # Détails par taux
    details: Mapped[Optional[dict]] = mapped_column(JSON)  # {rate: {base, tva_collectee, tva_deduc}}

    # Statut
    status: Mapped[Optional[str]] = mapped_column(String(20), default="draft")  # draft, submitted, paid
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    submission_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Paiement
    payment_date: Mapped[Optional[date]] = mapped_column(Date)
    payment_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    validated_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index('idx_fr_vat_decl_tenant', 'tenant_id'),
        Index('idx_fr_vat_decl_period', 'tenant_id', 'period_start', 'period_end'),
    )


# ============================================================================
# FEC - FICHIER DES ÉCRITURES COMPTABLES
# ============================================================================

class FECExport(Base):
    """Export FEC (Fichier des Écritures Comptables)."""
    __tablename__ = "fr_fec_exports"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    fec_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False)
    siren: Mapped[Optional[str]] = mapped_column(String(9), nullable=False)  # SIREN de l'entreprise

    # Période
    fiscal_year: Mapped[int] = mapped_column(Integer)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)

    # Fichier
    filename: Mapped[Optional[str]] = mapped_column(String(255))  # Format: SIRENFECaaaammjj.txt
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256 pour intégrité

    # Statistiques
    total_entries: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_debit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    total_credit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    is_balanced: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Validation
    validation_errors: Mapped[Optional[dict]] = mapped_column(JSON)  # Liste des erreurs
    is_valid: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(FECStatus), default=FECStatus.DRAFT)

    # Audit
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    generated_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    validated_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    exported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_fr_fec_tenant', 'tenant_id'),
        Index('idx_fr_fec_year', 'tenant_id', 'fiscal_year'),
    )


class FECEntry(Base):
    """Entrée dans le FEC."""
    __tablename__ = "fr_fec_entries"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    fec_export_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fr_fec_exports.id"), nullable=False)

    # Champs FEC obligatoires (norme DGFIP)
    journal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=False)      # JournalCode
    journal_lib: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)      # JournalLib
    ecriture_num: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)      # EcritureNum
    ecriture_date: Mapped[date] = mapped_column(Date)           # EcritureDate
    compte_num: Mapped[Optional[str]] = mapped_column(String(10), nullable=False)        # CompteNum
    compte_lib: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)       # CompteLib
    comp_aux_num: Mapped[Optional[str]] = mapped_column(String(17))                      # CompAuxNum (client/fournisseur)
    comp_aux_lib: Mapped[Optional[str]] = mapped_column(String(255))                     # CompAuxLib
    piece_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)         # PieceRef
    piece_date: Mapped[date] = mapped_column(Date)              # PieceDate
    ecriture_lib: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)     # EcritureLib
    debit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)              # Debit
    credit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)             # Credit
    ecriture_let: Mapped[Optional[str]] = mapped_column(String(20))                      # EcritureLet (lettrage)
    date_let: Mapped[Optional[date]] = mapped_column(Date)                                # DateLet
    valid_date: Mapped[Optional[date]] = mapped_column(Date)                              # ValidDate
    montant_devise: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))                # Montantdevise
    idevise: Mapped[Optional[str]] = mapped_column(String(3))                            # Idevise (code devise)

    # Métadonnées
    line_number: Mapped[Optional[int]] = mapped_column(Integer)  # Numéro de ligne dans le FEC

    __table_args__ = (
        Index('idx_fr_fec_entry_export', 'fec_export_id'),
        Index('idx_fr_fec_entry_compte', 'tenant_id', 'compte_num'),
    )


# ============================================================================
# DSN - DÉCLARATION SOCIALE NOMINATIVE
# ============================================================================

class DSNDeclaration(Base):
    """Déclaration Sociale Nominative."""
    __tablename__ = "fr_dsn_declarations"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    dsn_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False)
    dsn_type: Mapped[Optional[str]] = mapped_column(Enum(DSNType), nullable=False)
    siret: Mapped[Optional[str]] = mapped_column(String(14), nullable=False)

    # Période
    period_month: Mapped[int] = mapped_column(Integer)  # 1-12
    period_year: Mapped[int] = mapped_column(Integer)

    # Fichier
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Statistiques
    total_employees: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_brut: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    total_cotisations: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(DSNStatus), default=DSNStatus.DRAFT)

    # Transmission
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    submission_id: Mapped[Optional[str]] = mapped_column(String(100))  # ID retourné par Net-Entreprises
    ack_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ack_status: Mapped[Optional[str]] = mapped_column(String(50))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    validated_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_dsn_tenant', 'tenant_id'),
        Index('idx_fr_dsn_period', 'tenant_id', 'period_year', 'period_month'),
    )


class DSNEmployee(Base):
    """Données salarié pour la DSN."""
    __tablename__ = "fr_dsn_employees"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    dsn_declaration_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fr_dsn_declarations.id"), nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)  # Référence vers HR

    # Identification salarié
    nir: Mapped[Optional[str]] = mapped_column(String(15), nullable=False)  # NIR (sécurité sociale)
    nom: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    prenoms: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    date_naissance: Mapped[date] = mapped_column(Date)
    lieu_naissance: Mapped[Optional[str]] = mapped_column(String(100))
    code_pays_naissance: Mapped[Optional[str]] = mapped_column(String(2))

    # Contrat
    contract_type: Mapped[Optional[str]] = mapped_column(Enum(ContractType))
    date_debut_contrat: Mapped[Optional[date]] = mapped_column(Date)
    date_fin_contrat: Mapped[Optional[date]] = mapped_column(Date)
    motif_rupture: Mapped[Optional[str]] = mapped_column(String(3))  # Code motif

    # Rémunération période
    brut_periode: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    net_imposable: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=0)
    heures_travaillees: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))

    # Cotisations
    cotisations_details: Mapped[Optional[dict]] = mapped_column(JSON)  # Détail par code cotisation

    # Absences/Arrêts
    absences: Mapped[Optional[dict]] = mapped_column(JSON)  # Liste des absences

    __table_args__ = (
        Index('idx_fr_dsn_emp_dsn', 'dsn_declaration_id'),
        Index('idx_fr_dsn_emp_employee', 'tenant_id', 'employee_id'),
    )


# ============================================================================
# CONTRATS DE TRAVAIL FRANÇAIS
# ============================================================================

class FREmploymentContract(Base):
    """Spécificités contrat de travail français."""
    __tablename__ = "fr_employment_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)

    # Type de contrat
    contract_type: Mapped[Optional[str]] = mapped_column(Enum(ContractType), nullable=False)
    contract_number: Mapped[Optional[str]] = mapped_column(String(50))

    # Dates
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)  # Null pour CDI
    trial_period_end: Mapped[Optional[date]] = mapped_column(Date)

    # Classification
    convention_collective: Mapped[Optional[str]] = mapped_column(String(20))  # IDCC
    niveau: Mapped[Optional[str]] = mapped_column(String(10))
    coefficient: Mapped[Optional[str]] = mapped_column(String(10))
    echelon: Mapped[Optional[str]] = mapped_column(String(10))
    position: Mapped[Optional[str]] = mapped_column(String(10))

    # Temps de travail
    is_full_time: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    work_hours_weekly: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), default=35)
    work_hours_monthly: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    is_forfait_jours: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    forfait_jours_annual: Mapped[Optional[int]] = mapped_column(Integer)  # 218 jours max

    # Rémunération
    base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    salary_type: Mapped[Optional[str]] = mapped_column(String(20))  # mensuel, horaire, annuel
    variable_component: Mapped[Optional[dict]] = mapped_column(JSON)  # Primes, commissions

    # Avantages
    avantages_nature: Mapped[Optional[dict]] = mapped_column(JSON)  # Voiture, logement, etc.
    tickets_restaurant: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    mutuelle_obligatoire: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Statut
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    termination_date: Mapped[Optional[date]] = mapped_column(Date)
    termination_reason: Mapped[Optional[str]] = mapped_column(String(10))  # Code motif rupture

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_contract_tenant', 'tenant_id'),
        Index('idx_fr_contract_employee', 'tenant_id', 'employee_id'),
    )


# ============================================================================
# RGPD - RÈGLEMENT GÉNÉRAL SUR LA PROTECTION DES DONNÉES
# ============================================================================

class RGPDConsent(Base):
    """Consentements RGPD."""
    __tablename__ = "fr_rgpd_consents"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Personne concernée
    data_subject_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # customer, employee, contact
    data_subject_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False)
    data_subject_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Consentement
    purpose: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)  # marketing, analytics, etc.
    purpose_description: Mapped[Optional[str]] = mapped_column(Text)
    legal_basis: Mapped[Optional[str]] = mapped_column(String(50))  # consent, contract, legal_obligation, vital_interest, public_interest, legitimate_interest

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(RGPDConsentStatus), default=RGPDConsentStatus.PENDING)

    # Historique
    consent_given_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    consent_method: Mapped[Optional[str]] = mapped_column(String(50))  # form, email, verbal
    consent_proof: Mapped[Optional[str]] = mapped_column(Text)  # IP, référence, etc.
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    withdrawn_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Validité
    valid_until: Mapped[Optional[date]] = mapped_column(Date)
    requires_renewal: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_fr_rgpd_consent_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_consent_subject', 'tenant_id', 'data_subject_type', 'data_subject_id'),
    )


class RGPDRequest(Base):
    """Demandes RGPD (droits des personnes)."""
    __tablename__ = "fr_rgpd_requests"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    request_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False)
    request_type: Mapped[Optional[str]] = mapped_column(Enum(RGPDRequestType), nullable=False)

    # Demandeur
    data_subject_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    data_subject_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    requester_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    requester_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    requester_phone: Mapped[Optional[str]] = mapped_column(String(50))

    # Demande
    request_details: Mapped[Optional[str]] = mapped_column(Text)
    identity_verified: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    identity_verification_method: Mapped[Optional[str]] = mapped_column(String(100))

    # Traitement
    status: Mapped[Optional[str]] = mapped_column(String(30), default="pending")  # pending, processing, completed, rejected
    assigned_to: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    due_date: Mapped[Optional[date]] = mapped_column(Date)  # 1 mois max légal
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Réponse
    response_details: Mapped[Optional[str]] = mapped_column(Text)
    data_exported: Mapped[Optional[bool]] = mapped_column(Boolean)
    data_deleted: Mapped[Optional[bool]] = mapped_column(Boolean)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Documents
    attachments: Mapped[Optional[dict]] = mapped_column(JSON)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_rgpd_request_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_request_status', 'tenant_id', 'status'),
    )


class RGPDDataProcessing(Base):
    """Registre des traitements RGPD (Article 30)."""
    __tablename__ = "fr_rgpd_data_processing"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification du traitement
    processing_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    processing_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    processing_description: Mapped[Optional[str]] = mapped_column(Text)

    # Finalités
    purposes: Mapped[Optional[dict]] = mapped_column(JSON)  # Liste des finalités
    legal_basis: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    legal_basis_details: Mapped[Optional[str]] = mapped_column(Text)

    # Données traitées
    data_categories: Mapped[Optional[dict]] = mapped_column(JSON)  # Types de données personnelles
    special_categories: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)  # Données sensibles
    special_categories_details: Mapped[Optional[str]] = mapped_column(Text)

    # Personnes concernées
    data_subjects: Mapped[Optional[dict]] = mapped_column(JSON)  # Catégories de personnes

    # Destinataires
    recipients: Mapped[Optional[dict]] = mapped_column(JSON)  # Catégories de destinataires
    third_country_transfers: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    transfer_safeguards: Mapped[Optional[str]] = mapped_column(Text)

    # Durées de conservation
    retention_period: Mapped[Optional[str]] = mapped_column(String(100))
    retention_criteria: Mapped[Optional[str]] = mapped_column(Text)

    # Sécurité
    security_measures: Mapped[Optional[dict]] = mapped_column(JSON)

    # DPO
    dpo_consulted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    dpo_opinion: Mapped[Optional[str]] = mapped_column(Text)

    # AIPD (Analyse d'Impact)
    aipd_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    aipd_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Statut
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    last_review_date: Mapped[Optional[date]] = mapped_column(Date)
    last_review_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_rgpd_processing_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_processing_code', 'tenant_id', 'processing_code', unique=True),
    )


class RGPDDataBreach(Base):
    """Violations de données (Article 33)."""
    __tablename__ = "fr_rgpd_data_breaches"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    breach_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False)
    breach_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)

    # Détection
    detected_at: Mapped[datetime] = mapped_column(DateTime)
    detected_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    detection_method: Mapped[Optional[str]] = mapped_column(String(100))

    # Description
    breach_description: Mapped[str] = mapped_column(Text)
    breach_nature: Mapped[Optional[str]] = mapped_column(String(50))  # confidentiality, integrity, availability
    breach_cause: Mapped[Optional[str]] = mapped_column(Text)

    # Impact
    data_categories_affected: Mapped[Optional[dict]] = mapped_column(JSON)
    estimated_subjects_affected: Mapped[Optional[int]] = mapped_column(Integer)
    potential_consequences: Mapped[Optional[str]] = mapped_column(Text)
    severity_level: Mapped[Optional[str]] = mapped_column(String(20))  # low, medium, high, critical

    # Mesures prises
    containment_measures: Mapped[Optional[dict]] = mapped_column(JSON)
    remediation_measures: Mapped[Optional[dict]] = mapped_column(JSON)
    prevention_measures: Mapped[Optional[dict]] = mapped_column(JSON)

    # Notification CNIL (obligatoire si risque)
    cnil_notification_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    cnil_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cnil_reference: Mapped[Optional[str]] = mapped_column(String(100))
    notification_delay_reason: Mapped[Optional[str]] = mapped_column(Text)  # Si > 72h

    # Notification personnes concernées
    subjects_notification_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    subjects_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notification_content: Mapped[Optional[str]] = mapped_column(Text)

    # Statut
    status: Mapped[Optional[str]] = mapped_column(String(30), default="detected")  # detected, investigating, contained, resolved
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)

    # Audit
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    managed_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_rgpd_breach_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_breach_status', 'tenant_id', 'status'),
    )
