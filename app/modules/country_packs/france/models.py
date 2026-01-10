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
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text

from app.db import Base
from app.core.types import UniversalUUID
from sqlalchemy.dialects.postgresql import UUID

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

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    account_number = Column(String(10), nullable=False)  # Ex: 411000
    account_label = Column(String(255), nullable=False)

    # Classification PCG
    pcg_class = Column(Enum(PCGClass), nullable=False)
    parent_account = Column(String(10))  # Compte parent

    # Type
    is_summary = Column(Boolean, default=False)  # Compte de regroupement
    is_active = Column(Boolean, default=True)
    is_custom = Column(Boolean, default=False)  # Créé par le tenant

    # Soldes
    normal_balance = Column(String(1), default="D")  # D=Débit, C=Crédit

    # TVA associée
    default_vat_code = Column(String(20))

    # Notes
    description = Column(Text)
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

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

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False)  # TVA_20, TVA_10, etc.
    name = Column(String(100), nullable=False)
    rate_type = Column(Enum(TVARate), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)  # 20.00, 10.00, etc.

    # Comptes comptables associés
    account_collected = Column(String(10))   # 44571
    account_deductible = Column(String(10))  # 44566
    account_intra_eu = Column(String(10))    # 4452
    account_payable = Column(String(10))     # 44551

    # Applicabilité
    applies_to_goods = Column(Boolean, default=True)
    applies_to_services = Column(Boolean, default=True)
    is_intra_eu = Column(Boolean, default=False)
    is_import = Column(Boolean, default=False)

    # Mentions légales
    legal_mention = Column(Text)  # Mention sur facture si exonéré

    # Validité
    valid_from = Column(Date, default=date.today)
    valid_to = Column(Date)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_fr_vat_tenant', 'tenant_id'),
        Index('idx_fr_vat_code', 'tenant_id', 'code', unique=True),
    )


class FRVATDeclaration(Base):
    """Déclaration de TVA (CA3, CA12)."""
    __tablename__ = "fr_vat_declarations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    declaration_number = Column(String(50), unique=True, nullable=False)
    declaration_type = Column(String(10), nullable=False)  # CA3, CA12
    regime = Column(Enum(TVARegime), nullable=False)

    # Période
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date)

    # Montants
    total_ht = Column(Numeric(15, 2), default=0)
    total_tva_collectee = Column(Numeric(15, 2), default=0)
    total_tva_deductible = Column(Numeric(15, 2), default=0)
    tva_nette = Column(Numeric(15, 2), default=0)  # Collectée - Déductible
    credit_tva = Column(Numeric(15, 2), default=0)

    # Détails par taux
    details = Column(JSON)  # {rate: {base, tva_collectee, tva_deduc}}

    # Statut
    status = Column(String(20), default="draft")  # draft, submitted, paid
    submitted_at = Column(DateTime)
    submission_reference = Column(String(100))

    # Paiement
    payment_date = Column(Date)
    payment_amount = Column(Numeric(15, 2))
    payment_reference = Column(String(100))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())
    validated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)

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

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    fec_code = Column(String(50), unique=True, nullable=False)
    siren = Column(String(9), nullable=False)  # SIREN de l'entreprise

    # Période
    fiscal_year = Column(Integer, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Fichier
    filename = Column(String(255))  # Format: SIRENFECaaaammjj.txt
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_hash = Column(String(64))  # SHA-256 pour intégrité

    # Statistiques
    total_entries = Column(Integer, default=0)
    total_debit = Column(Numeric(15, 2), default=0)
    total_credit = Column(Numeric(15, 2), default=0)
    is_balanced = Column(Boolean, default=False)

    # Validation
    validation_errors = Column(JSON)  # Liste des erreurs
    is_valid = Column(Boolean, default=False)

    # Statut
    status = Column(Enum(FECStatus), default=FECStatus.DRAFT)

    # Audit
    generated_at = Column(DateTime)
    generated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)
    validated_by = Column(UniversalUUID())
    exported_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_fr_fec_tenant', 'tenant_id'),
        Index('idx_fr_fec_year', 'tenant_id', 'fiscal_year'),
    )


class FECEntry(Base):
    """Entrée dans le FEC."""
    __tablename__ = "fr_fec_entries"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    fec_export_id = Column(UniversalUUID(), ForeignKey("fr_fec_exports.id"), nullable=False)

    # Champs FEC obligatoires (norme DGFIP)
    journal_code = Column(String(10), nullable=False)      # JournalCode
    journal_lib = Column(String(255), nullable=False)      # JournalLib
    ecriture_num = Column(String(50), nullable=False)      # EcritureNum
    ecriture_date = Column(Date, nullable=False)           # EcritureDate
    compte_num = Column(String(10), nullable=False)        # CompteNum
    compte_lib = Column(String(255), nullable=False)       # CompteLib
    comp_aux_num = Column(String(17))                      # CompAuxNum (client/fournisseur)
    comp_aux_lib = Column(String(255))                     # CompAuxLib
    piece_ref = Column(String(50), nullable=False)         # PieceRef
    piece_date = Column(Date, nullable=False)              # PieceDate
    ecriture_lib = Column(String(255), nullable=False)     # EcritureLib
    debit = Column(Numeric(15, 2), default=0)              # Debit
    credit = Column(Numeric(15, 2), default=0)             # Credit
    ecriture_let = Column(String(20))                      # EcritureLet (lettrage)
    date_let = Column(Date)                                # DateLet
    valid_date = Column(Date)                              # ValidDate
    montant_devise = Column(Numeric(15, 2))                # Montantdevise
    idevise = Column(String(3))                            # Idevise (code devise)

    # Métadonnées
    line_number = Column(Integer)  # Numéro de ligne dans le FEC

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

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    dsn_code = Column(String(50), unique=True, nullable=False)
    dsn_type = Column(Enum(DSNType), nullable=False)
    siret = Column(String(14), nullable=False)

    # Période
    period_month = Column(Integer, nullable=False)  # 1-12
    period_year = Column(Integer, nullable=False)

    # Fichier
    filename = Column(String(255))
    file_path = Column(String(500))

    # Statistiques
    total_employees = Column(Integer, default=0)
    total_brut = Column(Numeric(15, 2), default=0)
    total_cotisations = Column(Numeric(15, 2), default=0)

    # Statut
    status = Column(Enum(DSNStatus), default=DSNStatus.DRAFT)

    # Transmission
    submitted_at = Column(DateTime)
    submission_id = Column(String(100))  # ID retourné par Net-Entreprises
    ack_received_at = Column(DateTime)
    ack_status = Column(String(50))
    rejection_reason = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())
    validated_by = Column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_dsn_tenant', 'tenant_id'),
        Index('idx_fr_dsn_period', 'tenant_id', 'period_year', 'period_month'),
    )


class DSNEmployee(Base):
    """Données salarié pour la DSN."""
    __tablename__ = "fr_dsn_employees"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    dsn_declaration_id = Column(UniversalUUID(), ForeignKey("fr_dsn_declarations.id"), nullable=False)
    employee_id = Column(UniversalUUID(), nullable=False)  # Référence vers HR

    # Identification salarié
    nir = Column(String(15), nullable=False)  # NIR (sécurité sociale)
    nom = Column(String(100), nullable=False)
    prenoms = Column(String(100), nullable=False)
    date_naissance = Column(Date, nullable=False)
    lieu_naissance = Column(String(100))
    code_pays_naissance = Column(String(2))

    # Contrat
    contract_type = Column(Enum(ContractType))
    date_debut_contrat = Column(Date)
    date_fin_contrat = Column(Date)
    motif_rupture = Column(String(3))  # Code motif

    # Rémunération période
    brut_periode = Column(Numeric(15, 2), default=0)
    net_imposable = Column(Numeric(15, 2), default=0)
    heures_travaillees = Column(Numeric(8, 2))

    # Cotisations
    cotisations_details = Column(JSON)  # Détail par code cotisation

    # Absences/Arrêts
    absences = Column(JSON)  # Liste des absences

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

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(UniversalUUID(), nullable=False)

    # Type de contrat
    contract_type = Column(Enum(ContractType), nullable=False)
    contract_number = Column(String(50))

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # Null pour CDI
    trial_period_end = Column(Date)

    # Classification
    convention_collective = Column(String(20))  # IDCC
    niveau = Column(String(10))
    coefficient = Column(String(10))
    echelon = Column(String(10))
    position = Column(String(10))

    # Temps de travail
    is_full_time = Column(Boolean, default=True)
    work_hours_weekly = Column(Numeric(5, 2), default=35)
    work_hours_monthly = Column(Numeric(6, 2))
    is_forfait_jours = Column(Boolean, default=False)
    forfait_jours_annual = Column(Integer)  # 218 jours max

    # Rémunération
    base_salary = Column(Numeric(10, 2))
    salary_type = Column(String(20))  # mensuel, horaire, annuel
    variable_component = Column(JSON)  # Primes, commissions

    # Avantages
    avantages_nature = Column(JSON)  # Voiture, logement, etc.
    tickets_restaurant = Column(Boolean, default=False)
    mutuelle_obligatoire = Column(Boolean, default=True)

    # Statut
    is_active = Column(Boolean, default=True)
    termination_date = Column(Date)
    termination_reason = Column(String(10))  # Code motif rupture

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())

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

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Personne concernée
    data_subject_type = Column(String(50), nullable=False)  # customer, employee, contact
    data_subject_id = Column(UniversalUUID(), nullable=False)
    data_subject_email = Column(String(255))

    # Consentement
    purpose = Column(String(100), nullable=False)  # marketing, analytics, etc.
    purpose_description = Column(Text)
    legal_basis = Column(String(50))  # consent, contract, legal_obligation, vital_interest, public_interest, legitimate_interest

    # Statut
    status = Column(Enum(RGPDConsentStatus), default=RGPDConsentStatus.PENDING)

    # Historique
    consent_given_at = Column(DateTime)
    consent_method = Column(String(50))  # form, email, verbal
    consent_proof = Column(Text)  # IP, référence, etc.
    withdrawn_at = Column(DateTime)
    withdrawn_reason = Column(Text)

    # Validité
    valid_until = Column(Date)
    requires_renewal = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_fr_rgpd_consent_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_consent_subject', 'tenant_id', 'data_subject_type', 'data_subject_id'),
    )


class RGPDRequest(Base):
    """Demandes RGPD (droits des personnes)."""
    __tablename__ = "fr_rgpd_requests"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    request_code = Column(String(50), unique=True, nullable=False)
    request_type = Column(Enum(RGPDRequestType), nullable=False)

    # Demandeur
    data_subject_type = Column(String(50), nullable=False)
    data_subject_id = Column(UniversalUUID())
    requester_name = Column(String(255), nullable=False)
    requester_email = Column(String(255), nullable=False)
    requester_phone = Column(String(50))

    # Demande
    request_details = Column(Text)
    identity_verified = Column(Boolean, default=False)
    identity_verification_method = Column(String(100))

    # Traitement
    status = Column(String(30), default="pending")  # pending, processing, completed, rejected
    assigned_to = Column(UniversalUUID())
    received_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(Date)  # 1 mois max légal
    processed_at = Column(DateTime)

    # Réponse
    response_details = Column(Text)
    data_exported = Column(Boolean)
    data_deleted = Column(Boolean)
    rejection_reason = Column(Text)

    # Documents
    attachments = Column(JSON)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = Column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_rgpd_request_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_request_status', 'tenant_id', 'status'),
    )


class RGPDDataProcessing(Base):
    """Registre des traitements RGPD (Article 30)."""
    __tablename__ = "fr_rgpd_data_processing"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification du traitement
    processing_code = Column(String(50), nullable=False)
    processing_name = Column(String(255), nullable=False)
    processing_description = Column(Text)

    # Finalités
    purposes = Column(JSON)  # Liste des finalités
    legal_basis = Column(String(50), nullable=False)
    legal_basis_details = Column(Text)

    # Données traitées
    data_categories = Column(JSON)  # Types de données personnelles
    special_categories = Column(Boolean, default=False)  # Données sensibles
    special_categories_details = Column(Text)

    # Personnes concernées
    data_subjects = Column(JSON)  # Catégories de personnes

    # Destinataires
    recipients = Column(JSON)  # Catégories de destinataires
    third_country_transfers = Column(Boolean, default=False)
    transfer_safeguards = Column(Text)

    # Durées de conservation
    retention_period = Column(String(100))
    retention_criteria = Column(Text)

    # Sécurité
    security_measures = Column(JSON)

    # DPO
    dpo_consulted = Column(Boolean, default=False)
    dpo_opinion = Column(Text)

    # AIPD (Analyse d'Impact)
    aipd_required = Column(Boolean, default=False)
    aipd_reference = Column(String(100))

    # Statut
    is_active = Column(Boolean, default=True)
    start_date = Column(Date)
    end_date = Column(Date)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID())
    last_review_date = Column(Date)
    last_review_by = Column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_rgpd_processing_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_processing_code', 'tenant_id', 'processing_code', unique=True),
    )


class RGPDDataBreach(Base):
    """Violations de données (Article 33)."""
    __tablename__ = "fr_rgpd_data_breaches"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    breach_code = Column(String(50), unique=True, nullable=False)
    breach_title = Column(String(255), nullable=False)

    # Détection
    detected_at = Column(DateTime, nullable=False)
    detected_by = Column(UniversalUUID())
    detection_method = Column(String(100))

    # Description
    breach_description = Column(Text, nullable=False)
    breach_nature = Column(String(50))  # confidentiality, integrity, availability
    breach_cause = Column(Text)

    # Impact
    data_categories_affected = Column(JSON)
    estimated_subjects_affected = Column(Integer)
    potential_consequences = Column(Text)
    severity_level = Column(String(20))  # low, medium, high, critical

    # Mesures prises
    containment_measures = Column(JSON)
    remediation_measures = Column(JSON)
    prevention_measures = Column(JSON)

    # Notification CNIL (obligatoire si risque)
    cnil_notification_required = Column(Boolean, default=False)
    cnil_notified_at = Column(DateTime)
    cnil_reference = Column(String(100))
    notification_delay_reason = Column(Text)  # Si > 72h

    # Notification personnes concernées
    subjects_notification_required = Column(Boolean, default=False)
    subjects_notified_at = Column(DateTime)
    notification_content = Column(Text)

    # Statut
    status = Column(String(30), default="detected")  # detected, investigating, contained, resolved
    resolved_at = Column(DateTime)
    lessons_learned = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    managed_by = Column(UniversalUUID())

    __table_args__ = (
        Index('idx_fr_rgpd_breach_tenant', 'tenant_id'),
        Index('idx_fr_rgpd_breach_status', 'tenant_id', 'status'),
    )
