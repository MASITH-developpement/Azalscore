"""
AZALS MODULE CONTRACTS - Models SQLAlchemy
===========================================

Gestion des contrats (CLM) - Contract Lifecycle Management.
Intgre les meilleures pratiques de Sage, Odoo, Microsoft Dynamics 365, Axonaut, Pennylane.

Fonctionnalites:
- Contrats client/fournisseur multi-parties
- Types de contrats configurables
- Lignes de contrat avec facturation recurrente
- Avenants et modifications
- Renouvellements automatiques
- Workflow de validation multi-niveaux
- Alertes et echeances
- Historique et versionning

CRITIQUE: Tous les modeles ont tenant_id pour isolation multi-tenant stricte.
"""
from __future__ import annotations


import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Numeric,
    ForeignKey, Index, Date, Float
)
from app.core.types import UniversalUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import JSON


# ============================================================================
# ENUMS
# ============================================================================

class ContractType(str, Enum):
    """Type de contrat."""
    # Commercial - Ventes
    SALES = "sales"  # Contrat de vente
    PURCHASE = "purchase"  # Contrat d'achat
    SERVICE = "service"  # Prestation de services
    SUBSCRIPTION = "subscription"  # Abonnement
    LICENSE = "license"  # Licence logicielle
    DISTRIBUTION = "distribution"  # Distribution
    FRANCHISE = "franchise"  # Franchise
    AGENCY = "agency"  # Agent commercial
    RESELLER = "reseller"  # Revendeur

    # Partenariats
    PARTNERSHIP = "partnership"  # Partenariat
    JOINT_VENTURE = "joint_venture"  # Coentreprise
    CONSORTIUM = "consortium"  # Consortium
    AFFILIATE = "affiliate"  # Affiliation

    # Confidentialite
    NDA = "nda"  # Accord de confidentialite
    NON_COMPETE = "non_compete"  # Non-concurrence
    NON_SOLICITATION = "non_solicitation"  # Non-sollicitation

    # Immobilier
    LEASE = "lease"  # Bail commercial
    SUBLEASE = "sublease"  # Sous-location
    REAL_ESTATE = "real_estate"  # Immobilier

    # RH
    EMPLOYMENT = "employment"  # Contrat de travail
    CONSULTING = "consulting"  # Consultant
    INTERNSHIP = "internship"  # Stage
    FREELANCE = "freelance"  # Freelance

    # Support/Maintenance
    MAINTENANCE = "maintenance"  # Maintenance
    SLA = "sla"  # Accord de niveau de service
    SUPPORT = "support"  # Support technique
    WARRANTY = "warranty"  # Garantie etendue

    # Location
    RENTAL = "rental"  # Location equipement
    LEASING = "leasing"  # Credit-bail

    # Autres
    FRAMEWORK = "framework"  # Contrat cadre
    MASTER = "master"  # Contrat maitre
    OTHER = "other"  # Autre


class ContractStatus(str, Enum):
    """Statut du contrat."""
    DRAFT = "draft"  # Brouillon
    IN_REVIEW = "in_review"  # En revision interne
    IN_NEGOTIATION = "in_negotiation"  # En negociation avec contrepartie
    PENDING_APPROVAL = "pending_approval"  # En attente approbation
    APPROVED = "approved"  # Approuve, pret pour signature
    PENDING_SIGNATURE = "pending_signature"  # En attente signature
    PARTIALLY_SIGNED = "partially_signed"  # Partiellement signe
    ACTIVE = "active"  # Actif
    SUSPENDED = "suspended"  # Suspendu
    ON_HOLD = "on_hold"  # En pause
    EXPIRED = "expired"  # Expire
    TERMINATED = "terminated"  # Resilie
    RENEWED = "renewed"  # Renouvele
    CANCELLED = "cancelled"  # Annule
    ARCHIVED = "archived"  # Archive

    def allowed_transitions(self) -> List["ContractStatus"]:
        """Transitions d'etat autorisees."""
        transitions = {
            ContractStatus.DRAFT: [
                ContractStatus.IN_REVIEW,
                ContractStatus.IN_NEGOTIATION,
                ContractStatus.PENDING_APPROVAL,
                ContractStatus.CANCELLED
            ],
            ContractStatus.IN_REVIEW: [
                ContractStatus.DRAFT,
                ContractStatus.IN_NEGOTIATION,
                ContractStatus.PENDING_APPROVAL,
                ContractStatus.CANCELLED
            ],
            ContractStatus.IN_NEGOTIATION: [
                ContractStatus.DRAFT,
                ContractStatus.PENDING_APPROVAL,
                ContractStatus.CANCELLED
            ],
            ContractStatus.PENDING_APPROVAL: [
                ContractStatus.DRAFT,
                ContractStatus.APPROVED,
                ContractStatus.CANCELLED
            ],
            ContractStatus.APPROVED: [
                ContractStatus.PENDING_SIGNATURE,
                ContractStatus.CANCELLED
            ],
            ContractStatus.PENDING_SIGNATURE: [
                ContractStatus.PARTIALLY_SIGNED,
                ContractStatus.ACTIVE,
                ContractStatus.CANCELLED
            ],
            ContractStatus.PARTIALLY_SIGNED: [
                ContractStatus.ACTIVE,
                ContractStatus.CANCELLED
            ],
            ContractStatus.ACTIVE: [
                ContractStatus.SUSPENDED,
                ContractStatus.ON_HOLD,
                ContractStatus.TERMINATED,
                ContractStatus.RENEWED,
                ContractStatus.EXPIRED
            ],
            ContractStatus.SUSPENDED: [
                ContractStatus.ACTIVE,
                ContractStatus.TERMINATED
            ],
            ContractStatus.ON_HOLD: [
                ContractStatus.ACTIVE,
                ContractStatus.TERMINATED
            ],
            ContractStatus.EXPIRED: [
                ContractStatus.RENEWED,
                ContractStatus.ARCHIVED
            ],
            ContractStatus.TERMINATED: [
                ContractStatus.ARCHIVED
            ],
            ContractStatus.RENEWED: [
                ContractStatus.ARCHIVED
            ],
            ContractStatus.CANCELLED: [
                ContractStatus.ARCHIVED
            ],
            ContractStatus.ARCHIVED: [],
        }
        return transitions.get(self, [])


class PartyType(str, Enum):
    """Type de partie contractante."""
    COMPANY = "company"  # Entreprise
    INDIVIDUAL = "individual"  # Personne physique
    GOVERNMENT = "government"  # Administration
    NONPROFIT = "nonprofit"  # Association/ONG


class PartyRole(str, Enum):
    """Role d'une partie dans le contrat."""
    CONTRACTOR = "contractor"  # Prestataire/Vendeur
    CLIENT = "client"  # Client/Acheteur
    SUPPLIER = "supplier"  # Fournisseur
    PARTNER = "partner"  # Partenaire
    EMPLOYER = "employer"  # Employeur
    EMPLOYEE = "employee"  # Employe
    LICENSOR = "licensor"  # Concedant
    LICENSEE = "licensee"  # Licencie
    LANDLORD = "landlord"  # Bailleur
    TENANT = "tenant"  # Locataire
    GUARANTOR = "guarantor"  # Garant
    BENEFICIARY = "beneficiary"  # Beneficiaire
    AGENT = "agent"  # Agent
    PRINCIPAL = "principal"  # Mandant


class RenewalType(str, Enum):
    """Type de renouvellement."""
    MANUAL = "manual"  # Manuel - necessite action explicite
    AUTOMATIC = "automatic"  # Tacite reconduction
    NEGOTIATED = "negotiated"  # Renégocie
    EVERGREEN = "evergreen"  # Perpetuel avec preavis
    NONE = "none"  # Pas de renouvellement


class BillingFrequency(str, Enum):
    """Frequence de facturation."""
    ONE_TIME = "one_time"  # Ponctuel
    DAILY = "daily"  # Journalier
    WEEKLY = "weekly"  # Hebdomadaire
    BIWEEKLY = "biweekly"  # Bi-hebdomadaire
    MONTHLY = "monthly"  # Mensuel
    BIMONTHLY = "bimonthly"  # Bimestriel
    QUARTERLY = "quarterly"  # Trimestriel
    SEMI_ANNUAL = "semi_annual"  # Semestriel
    ANNUAL = "annual"  # Annuel
    CUSTOM = "custom"  # Personnalise


class AmendmentType(str, Enum):
    """Type d'avenant."""
    EXTENSION = "extension"  # Prolongation
    MODIFICATION = "modification"  # Modification generale
    PRICING = "pricing"  # Revision tarifaire
    SCOPE = "scope"  # Modification perimetre
    PARTIES = "parties"  # Changement parties
    TERMINATION = "termination"  # Resiliation anticipee
    RENEWAL = "renewal"  # Renouvellement formel
    ADDENDUM = "addendum"  # Addendum
    ASSIGNMENT = "assignment"  # Cession
    OTHER = "other"  # Autre


class ObligationType(str, Enum):
    """Type d'obligation contractuelle."""
    PAYMENT = "payment"  # Paiement
    DELIVERY = "delivery"  # Livraison
    PERFORMANCE = "performance"  # Execution prestation
    REPORTING = "reporting"  # Reporting/Rapports
    COMPLIANCE = "compliance"  # Conformite reglementaire
    AUDIT = "audit"  # Audit
    RENEWAL_NOTICE = "renewal_notice"  # Preavis renouvellement
    TERMINATION_NOTICE = "termination_notice"  # Preavis resiliation
    CONFIDENTIALITY = "confidentiality"  # Confidentialite
    INSURANCE = "insurance"  # Assurance
    WARRANTY = "warranty"  # Garantie
    MILESTONE = "milestone"  # Jalon projet
    REVIEW = "review"  # Revue periodique
    OTHER = "other"  # Autre


class ObligationStatus(str, Enum):
    """Statut d'une obligation."""
    PENDING = "pending"  # En attente
    IN_PROGRESS = "in_progress"  # En cours
    COMPLETED = "completed"  # Termine
    OVERDUE = "overdue"  # En retard
    WAIVED = "waived"  # Abandonne
    CANCELLED = "cancelled"  # Annule


class AlertType(str, Enum):
    """Type d'alerte contrat."""
    EXPIRY = "expiry"  # Expiration
    RENEWAL_NOTICE = "renewal_notice"  # Preavis renouvellement
    OBLIGATION_DUE = "obligation_due"  # Obligation due
    MILESTONE_DUE = "milestone_due"  # Jalon a venir
    PAYMENT_DUE = "payment_due"  # Paiement du
    REVIEW_REQUIRED = "review_required"  # Revue requise
    PRICE_REVISION = "price_revision"  # Revision tarifaire
    COMPLIANCE_CHECK = "compliance_check"  # Verification conformite
    SIGNATURE_PENDING = "signature_pending"  # Signature en attente
    CUSTOM = "custom"  # Personnalise


class AlertPriority(str, Enum):
    """Priorite d'alerte."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    """Statut d'approbation."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    ESCALATED = "escalated"


class ClauseType(str, Enum):
    """Type de clause."""
    STANDARD = "standard"  # Clause standard
    LEGAL = "legal"  # Clause legale obligatoire
    CUSTOM = "custom"  # Clause personnalisee
    OPTIONAL = "optional"  # Clause optionnelle
    NEGOTIATED = "negotiated"  # Clause negociee


class BillingType(str, Enum):
    """Type de facturation."""
    FIXED = "fixed"  # Prix fixe
    TIME_MATERIAL = "time_material"  # Regie (temps et materiaux)
    RECURRING = "recurring"  # Recurrent
    MILESTONE = "milestone"  # Par jalon
    USAGE = "usage"  # A l'usage
    RETAINER = "retainer"  # Abonnement/provision


class RenewalStatus(str, Enum):
    """Statut de renouvellement."""
    PENDING = "pending"  # En attente
    APPROVED = "approved"  # Approuve
    EXECUTED = "executed"  # Execute
    CANCELLED = "cancelled"  # Annule
    REJECTED = "rejected"  # Rejete


class AlertStatus(str, Enum):
    """Statut d'alerte."""
    PENDING = "pending"  # En attente
    ACKNOWLEDGED = "acknowledged"  # Acquittee
    RESOLVED = "resolved"  # Resolue
    DISMISSED = "dismissed"  # Ignoree
    ESCALATED = "escalated"  # Escaladee


class MilestoneStatus(str, Enum):
    """Statut de jalon."""
    PENDING = "pending"  # En attente
    IN_PROGRESS = "in_progress"  # En cours
    COMPLETED = "completed"  # Termine
    DELAYED = "delayed"  # En retard
    CANCELLED = "cancelled"  # Annule
    SKIPPED = "skipped"  # Saute


class ClauseCategory(str, Enum):
    """Categorie de clause."""
    GENERAL = "general"  # Conditions generales
    COMMERCIAL = "commercial"  # Conditions commerciales
    FINANCIAL = "financial"  # Conditions financieres
    LEGAL = "legal"  # Clauses legales
    CONFIDENTIALITY = "confidentiality"  # Confidentialite
    IP = "ip"  # Propriete intellectuelle
    LIABILITY = "liability"  # Responsabilite
    TERMINATION = "termination"  # Resiliation
    DISPUTE = "dispute"  # Litiges
    OTHER = "other"  # Autres


class ClauseStatus(str, Enum):
    """Statut de clause."""
    DRAFT = "draft"  # Brouillon
    PROPOSED = "proposed"  # Proposee
    ACCEPTED = "accepted"  # Acceptee
    REJECTED = "rejected"  # Rejetee
    NEGOTIATING = "negotiating"  # En negociation
    FINAL = "final"  # Finalisee


class DocumentType(str, Enum):
    """Type de document."""
    CONTRACT = "contract"  # Document contractuel
    AMENDMENT = "amendment"  # Avenant
    ANNEX = "annex"  # Annexe
    ATTACHMENT = "attachment"  # Piece jointe
    INVOICE = "invoice"  # Facture
    PROOF_OF_DELIVERY = "proof_of_delivery"  # Bon de livraison
    INSURANCE = "insurance"  # Attestation assurance
    CERTIFICATE = "certificate"  # Certificat
    CORRESPONDENCE = "correspondence"  # Correspondance
    LEGAL = "legal"  # Document legal
    OTHER = "other"  # Autre


class AmendmentStatus(str, Enum):
    """Statut d'avenant."""
    DRAFT = "draft"  # Brouillon
    PROPOSED = "proposed"  # Propose
    IN_REVIEW = "in_review"  # En revision
    APPROVED = "approved"  # Approuve
    PENDING_SIGNATURE = "pending_signature"  # En attente signature
    SIGNED = "signed"  # Signe
    APPLIED = "applied"  # Applique
    REJECTED = "rejected"  # Rejete
    CANCELLED = "cancelled"  # Annule


# ============================================================================
# MODELS - Configuration
# ============================================================================

class ContractCategory(Base):
    """Categorie de contrat configurable par tenant."""
    __tablename__ = "contract_categories"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    parent_id = Column(UUID(), ForeignKey("contract_categories.id"))
    color = Column(String(20), default="#3B82F6")
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)

    # Configuration par defaut pour les contrats de cette categorie
    default_contract_type = Column(String(50))
    default_duration_months = Column(Integer)
    default_renewal_type = Column(String(30))
    default_billing_frequency = Column(String(30))

    # Workflow
    approval_required = Column(Boolean, default=True)
    min_approval_amount = Column(Numeric(18, 4), default=0)

    is_active = Column(Boolean, default=True)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    children = relationship("ContractCategory", backref="parent", remote_side=[id])

    __table_args__ = (
        Index("ix_contract_categories_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_contract_categories_tenant_active", "tenant_id", "is_active"),
    )


class ContractTemplate(Base):
    """Modele de contrat reutilisable."""
    __tablename__ = "contract_templates"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    contract_type = Column(String(50), nullable=False)
    category_id = Column(UUID(), ForeignKey("contract_categories.id"))

    # Contenu template
    content = Column(Text)  # HTML ou Markdown
    header_content = Column(Text)
    footer_content = Column(Text)

    # Structure
    sections = Column(JSON, default=list)  # [{order, title, content}]
    variables = Column(JSON, default=list)  # [{name, type, default, required}]

    # Configuration
    language = Column(String(5), default="fr")
    default_duration_months = Column(Integer)
    default_renewal_type = Column(String(30))
    default_payment_terms_days = Column(Integer, default=30)

    # Clauses par defaut
    default_clauses = Column(JSON, default=list)  # [clause_template_ids]

    # Legal
    requires_signature = Column(Boolean, default=True)
    requires_witness = Column(Boolean, default=False)
    requires_notarization = Column(Boolean, default=False)

    # Metadata
    tags = Column(JSON, default=list)
    version_number = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    category = relationship("ContractCategory")
    clause_templates = relationship("ClauseTemplate", back_populates="contract_template")

    __table_args__ = (
        Index("ix_contract_templates_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_contract_templates_tenant_type", "tenant_id", "contract_type"),
        Index("ix_contract_templates_tenant_active", "tenant_id", "is_active"),
    )


class ClauseTemplate(Base):
    """Modele de clause reutilisable."""
    __tablename__ = "contract_clause_templates"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_template_id = Column(UUID(), ForeignKey("contract_templates.id"))

    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    clause_type = Column(String(30), default=ClauseType.STANDARD.value)
    section = Column(String(100))

    # Configuration
    is_mandatory = Column(Boolean, default=False)
    is_negotiable = Column(Boolean, default=True)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    sort_order = Column(Integer, default=0)

    # Variables dans la clause
    variables = Column(JSON, default=list)

    # Compliance
    compliance_tags = Column(JSON, default=list)  # RGPD, etc.
    jurisdiction = Column(String(100))

    language = Column(String(5), default="fr")
    is_active = Column(Boolean, default=True)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract_template = relationship("ContractTemplate", back_populates="clause_templates")

    __table_args__ = (
        Index("ix_clause_templates_tenant_code", "tenant_id", "code", unique=True),
        Index("ix_clause_templates_tenant_type", "tenant_id", "clause_type"),
    )


# ============================================================================
# MODELS - Contrats
# ============================================================================

class Contract(Base):
    """Contrat principal."""
    __tablename__ = "contracts"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    contract_number = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    reference = Column(String(100))  # Reference externe/client

    # Classification
    contract_type = Column(String(50), nullable=False, default=ContractType.SERVICE.value)
    category_id = Column(UUID(), ForeignKey("contract_categories.id"))
    template_id = Column(UUID(), ForeignKey("contract_templates.id"))

    # Hierarchie contrat
    parent_contract_id = Column(UUID(), ForeignKey("contracts.id"))  # Contrat cadre
    master_contract_id = Column(UUID(), ForeignKey("contracts.id"))  # Contrat maitre

    # Statut
    status = Column(String(30), default=ContractStatus.DRAFT.value, index=True)
    status_reason = Column(Text)
    status_changed_at = Column(DateTime)
    status_changed_by = Column(UUID())

    # Contenu
    content = Column(Text)  # Contenu complet du contrat
    summary = Column(Text)  # Resume executif
    special_conditions = Column(Text)  # Conditions particulieres

    # Dates principales
    created_date = Column(Date, default=date.today)
    effective_date = Column(Date)
    start_date = Column(Date)
    end_date = Column(Date)
    signed_date = Column(DateTime)

    # Duree
    duration_months = Column(Integer)
    duration_days = Column(Integer)
    is_indefinite = Column(Boolean, default=False)  # Duree indeterminee

    # Renouvellement
    renewal_type = Column(String(30), default=RenewalType.MANUAL.value)
    renewal_notice_days = Column(Integer, default=90)
    auto_renewal_term_months = Column(Integer, default=12)
    max_renewals = Column(Integer)  # Nombre max de renouvellements
    renewal_count = Column(Integer, default=0)
    next_renewal_date = Column(Date)
    renewal_price_increase_percent = Column(Numeric(5, 2))  # Augmentation auto

    # Financier
    total_value = Column(Numeric(18, 4), default=0)
    currency = Column(String(3), default="EUR")
    billing_frequency = Column(String(30), default=BillingFrequency.MONTHLY.value)
    payment_terms_days = Column(Integer, default=30)
    payment_method = Column(String(50))

    # Revision tarifaire
    price_revision_enabled = Column(Boolean, default=False)
    price_revision_index = Column(String(50))  # INSEE, SYNTEC, etc.
    price_revision_date = Column(Date)
    price_revision_cap_percent = Column(Numeric(5, 2))
    last_price_revision_date = Column(Date)

    # Penalites
    late_payment_rate = Column(Numeric(5, 2), default=Decimal("0.05"))
    penalty_clause_enabled = Column(Boolean, default=False)
    penalty_percentage = Column(Numeric(5, 2))
    penalty_max_amount = Column(Numeric(18, 4))

    # Garanties
    deposit_amount = Column(Numeric(18, 4))
    deposit_received = Column(Boolean, default=False)
    guarantee_type = Column(String(50))
    guarantee_amount = Column(Numeric(18, 4))

    # Resiliation
    termination_notice_days = Column(Integer, default=90)
    termination_reason = Column(Text)
    termination_date = Column(Date)
    termination_by = Column(UUID())
    early_termination_penalty = Column(Numeric(18, 4))

    # Workflow Approbation
    requires_approval = Column(Boolean, default=True)
    approval_status = Column(String(30))
    current_approver_id = Column(UUID())
    approval_level = Column(Integer, default=0)
    approved_at = Column(DateTime)
    approved_by = Column(UUID())

    # Signature
    requires_signature = Column(Boolean, default=True)
    signature_method = Column(String(50))  # electronic, manual, notarized
    signature_request_id = Column(String(100))  # ID service signature externe
    all_parties_signed = Column(Boolean, default=False)

    # Documents
    main_document_id = Column(UUID())
    signed_document_id = Column(UUID())

    # Attribution
    owner_id = Column(UUID(), index=True)  # Responsable interne
    owner_name = Column(String(255))
    team_id = Column(UUID())
    department_id = Column(UUID())

    # Compliance
    compliance_status = Column(String(30))
    compliance_notes = Column(Text)
    last_compliance_check = Column(DateTime)
    gdpr_compliant = Column(Boolean, default=True)
    data_processing_agreement = Column(Boolean, default=False)

    # Legal
    governing_law = Column(String(100))  # Loi applicable
    jurisdiction = Column(String(100))  # Juridiction competente
    dispute_resolution = Column(String(50))  # mediation, arbitration, litigation
    confidentiality_level = Column(String(30), default="standard")

    # Metadata
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    notes = Column(Text)
    internal_notes = Column(Text)
    external_reference = Column(String(255))

    # Statistiques
    total_invoiced = Column(Numeric(18, 4), default=0)
    total_paid = Column(Numeric(18, 4), default=0)
    amendment_count = Column(Integer, default=0)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    category = relationship("ContractCategory")
    template = relationship("ContractTemplate")
    parent_contract = relationship("Contract", foreign_keys=[parent_contract_id], remote_side=[id])
    master_contract = relationship("Contract", foreign_keys=[master_contract_id], remote_side=[id])
    parties = relationship("ContractParty", back_populates="contract", cascade="all, delete-orphan")
    lines = relationship("ContractLine", back_populates="contract", cascade="all, delete-orphan")
    clauses = relationship("ContractClause", back_populates="contract", cascade="all, delete-orphan")
    obligations = relationship("ContractObligation", back_populates="contract", cascade="all, delete-orphan")
    milestones = relationship("ContractMilestone", back_populates="contract", cascade="all, delete-orphan")
    amendments = relationship("ContractAmendment", back_populates="contract", cascade="all, delete-orphan")
    renewals = relationship("ContractRenewal", back_populates="contract", cascade="all, delete-orphan")
    documents = relationship("ContractDocument", back_populates="contract", cascade="all, delete-orphan")
    alerts = relationship("ContractAlert", back_populates="contract", cascade="all, delete-orphan")
    approvals = relationship("ContractApproval", back_populates="contract", cascade="all, delete-orphan")
    history = relationship("ContractHistory", back_populates="contract", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_contracts_tenant_number", "tenant_id", "contract_number", unique=True),
        Index("ix_contracts_tenant_status", "tenant_id", "status"),
        Index("ix_contracts_tenant_type", "tenant_id", "contract_type"),
        Index("ix_contracts_tenant_owner", "tenant_id", "owner_id"),
        Index("ix_contracts_tenant_dates", "tenant_id", "start_date", "end_date"),
        Index("ix_contracts_tenant_renewal", "tenant_id", "next_renewal_date"),
        Index("ix_contracts_tenant_category", "tenant_id", "category_id"),
        Index("ix_contracts_parent", "parent_contract_id"),
        Index("ix_contracts_master", "master_contract_id"),
    )


class ContractParty(Base):
    """Partie contractante."""
    __tablename__ = "contract_parties"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Identification
    party_type = Column(String(30), default=PartyType.COMPANY.value)
    role = Column(String(30), nullable=False)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))

    # Reference interne
    entity_type = Column(String(50))  # customer, supplier, partner, employee
    entity_id = Column(UUID(), index=True)  # ID dans le systeme CRM

    # Informations legales
    registration_number = Column(String(50))  # SIRET
    vat_number = Column(String(50))
    legal_form = Column(String(100))

    # Contact
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))

    # Adresse
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    state = Column(String(100))
    country_code = Column(String(3), default="FR")

    # Representant legal
    representative_name = Column(String(255))
    representative_title = Column(String(100))
    representative_email = Column(String(255))
    representative_phone = Column(String(50))

    # Signature
    is_signatory = Column(Boolean, default=True)
    signatory_name = Column(String(255))
    signatory_title = Column(String(100))
    signatory_email = Column(String(255))
    has_signed = Column(Boolean, default=False)
    signed_at = Column(DateTime)
    signature_id = Column(String(100))
    signature_ip = Column(String(50))

    # Ordre dans le contrat
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)

    # Metadata
    notes = Column(Text)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="parties")

    __table_args__ = (
        Index("ix_contract_parties_contract", "contract_id"),
        Index("ix_contract_parties_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_contract_parties_role", "tenant_id", "role"),
    )


class ContractLine(Base):
    """Ligne de contrat - produit/service avec facturation."""
    __tablename__ = "contract_lines"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Identification
    line_number = Column(Integer, nullable=False)
    reference = Column(String(50))
    description = Column(Text, nullable=False)

    # Produit/Service
    product_id = Column(UUID())
    product_code = Column(String(50))
    product_name = Column(String(255))
    is_service = Column(Boolean, default=True)

    # Quantites
    quantity = Column(Numeric(18, 4), default=1)
    unit = Column(String(20))  # piece, hour, day, month, etc.
    delivered_quantity = Column(Numeric(18, 4), default=0)

    # Prix
    unit_price = Column(Numeric(18, 4), default=0)
    currency = Column(String(3), default="EUR")
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(18, 4), default=0)
    subtotal = Column(Numeric(18, 4), default=0)

    # TVA
    tax_rate = Column(Numeric(5, 2), default=Decimal("20.00"))
    tax_amount = Column(Numeric(18, 4), default=0)
    total = Column(Numeric(18, 4), default=0)

    # Facturation recurrente
    is_recurring = Column(Boolean, default=False)
    billing_frequency = Column(String(30))
    billing_start_date = Column(Date)
    billing_end_date = Column(Date)
    next_billing_date = Column(Date)
    last_billed_date = Column(Date)
    billing_day = Column(Integer)  # Jour du mois

    # Revision tarifaire
    price_revision_enabled = Column(Boolean, default=False)
    price_revision_index = Column(String(50))
    original_price = Column(Numeric(18, 4))
    last_revision_date = Column(Date)

    # Livraison
    delivery_date = Column(Date)
    delivery_address = Column(Text)
    delivery_status = Column(String(30))

    # SLA
    sla_id = Column(UUID())
    response_time_hours = Column(Integer)
    resolution_time_hours = Column(Integer)

    # Comptabilite
    accounting_code = Column(String(20))
    cost_center = Column(String(50))
    analytic_axis = Column(JSON)

    # Statut
    status = Column(String(30), default="active")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="lines")

    __table_args__ = (
        Index("ix_contract_lines_contract", "contract_id"),
        Index("ix_contract_lines_product", "tenant_id", "product_id"),
        Index("ix_contract_lines_billing", "tenant_id", "next_billing_date"),
        Index("ix_contract_lines_recurring", "tenant_id", "is_recurring", "is_active"),
    )


class ContractClause(Base):
    """Clause specifique d'un contrat."""
    __tablename__ = "contract_clauses"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)
    template_id = Column(UUID(), ForeignKey("contract_clause_templates.id"))

    # Contenu
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    clause_type = Column(String(30), default=ClauseType.STANDARD.value)
    section = Column(String(100))
    sort_order = Column(Integer, default=0)

    # Source
    is_from_template = Column(Boolean, default=False)
    original_content = Column(Text)  # Contenu original avant modification

    # Negociation
    is_negotiable = Column(Boolean, default=True)
    negotiation_status = Column(String(30), default="accepted")  # accepted, pending, rejected
    negotiation_notes = Column(Text)
    modified_by_party_id = Column(UUID())

    # Historique modifications
    modification_history = Column(JSON, default=list)

    # Importance
    is_mandatory = Column(Boolean, default=False)
    risk_level = Column(String(20), default="low")

    # Compliance
    compliance_tags = Column(JSON, default=list)

    # Approbation clause
    requires_legal_review = Column(Boolean, default=False)
    legal_reviewed = Column(Boolean, default=False)
    legal_reviewer_id = Column(UUID())
    legal_review_date = Column(DateTime)
    legal_review_notes = Column(Text)

    is_active = Column(Boolean, default=True)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="clauses")
    template = relationship("ClauseTemplate")

    __table_args__ = (
        Index("ix_contract_clauses_contract", "contract_id"),
        Index("ix_contract_clauses_type", "tenant_id", "clause_type"),
    )


class ContractObligation(Base):
    """Obligation contractuelle a suivre."""
    __tablename__ = "contract_obligations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Identification
    code = Column(String(50))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    obligation_type = Column(String(30), nullable=False)

    # Partie responsable
    responsible_party_id = Column(UUID(), ForeignKey("contract_parties.id"))
    responsible_user_id = Column(UUID())
    responsible_name = Column(String(255))

    # Echeances
    due_date = Column(Date)
    reminder_date = Column(Date)
    grace_period_days = Column(Integer, default=0)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(30))  # daily, weekly, monthly, quarterly, yearly
    recurrence_interval = Column(Integer, default=1)
    recurrence_end_date = Column(Date)
    next_due_date = Column(Date)
    last_completed_date = Column(Date)
    occurrences_completed = Column(Integer, default=0)

    # Montant associe
    amount = Column(Numeric(18, 4))
    currency = Column(String(3), default="EUR")

    # Statut
    status = Column(String(30), default=ObligationStatus.PENDING.value)
    completed_at = Column(DateTime)
    completed_by = Column(UUID())
    completion_notes = Column(Text)

    # Alertes
    alert_days_before = Column(Integer, default=30)
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime)

    # Evidence
    evidence_required = Column(Boolean, default=False)
    evidence_document_id = Column(UUID())

    # Penalite
    penalty_on_breach = Column(Numeric(18, 4))

    # Importance
    priority = Column(String(20), default="medium")
    is_critical = Column(Boolean, default=False)

    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="obligations")
    responsible_party = relationship("ContractParty")

    __table_args__ = (
        Index("ix_contract_obligations_contract", "contract_id"),
        Index("ix_contract_obligations_due", "tenant_id", "due_date", "status"),
        Index("ix_contract_obligations_type", "tenant_id", "obligation_type"),
        Index("ix_contract_obligations_recurring", "tenant_id", "is_recurring", "next_due_date"),
    )


class ContractMilestone(Base):
    """Jalon contractuel."""
    __tablename__ = "contract_milestones"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Identification
    code = Column(String(50))
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Dates
    target_date = Column(Date, nullable=False)
    actual_date = Column(Date)
    due_date_tolerance_days = Column(Integer, default=0)

    # Livrables
    deliverables = Column(JSON, default=list)  # [{name, description, status}]
    acceptance_criteria = Column(Text)

    # Paiement associe
    payment_amount = Column(Numeric(18, 4))
    payment_percentage = Column(Numeric(5, 2))  # % du contrat
    payment_currency = Column(String(3), default="EUR")
    payment_triggered = Column(Boolean, default=False)
    invoice_id = Column(UUID())

    # Validation
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(UUID())
    approved_at = Column(DateTime)
    approval_notes = Column(Text)

    # Statut
    status = Column(String(30), default="pending")  # pending, in_progress, completed, delayed, cancelled
    progress_percentage = Column(Integer, default=0)
    completed_at = Column(DateTime)
    completed_by = Column(UUID())

    # Responsable
    responsible_user_id = Column(UUID())
    responsible_name = Column(String(255))

    # Dependances
    depends_on_milestone_id = Column(UUID(), ForeignKey("contract_milestones.id"))

    # Alertes
    alert_days_before = Column(Integer, default=14)

    sort_order = Column(Integer, default=0)
    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="milestones")
    depends_on = relationship("ContractMilestone", remote_side=[id])

    __table_args__ = (
        Index("ix_contract_milestones_contract", "contract_id"),
        Index("ix_contract_milestones_date", "tenant_id", "target_date"),
        Index("ix_contract_milestones_status", "tenant_id", "status"),
    )


class ContractAmendment(Base):
    """Avenant au contrat."""
    __tablename__ = "contract_amendments"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Identification
    amendment_number = Column(Integer, nullable=False)
    amendment_code = Column(String(50))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    amendment_type = Column(String(30), nullable=False)

    # Raison
    reason = Column(Text)
    justification = Column(Text)

    # Dates
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date)

    # Changements
    changes = Column(JSON, default=list)  # [{field, old_value, new_value}]
    content = Column(Text)  # Texte complet de l'avenant

    # Impact financier
    value_change = Column(Numeric(18, 4))  # Positif = augmentation
    new_total_value = Column(Numeric(18, 4))
    currency = Column(String(3), default="EUR")

    # Changement dates
    new_end_date = Column(Date)
    new_duration_months = Column(Integer)

    # Statut
    status = Column(String(30), default=ContractStatus.DRAFT.value)

    # Approbation
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(UUID())
    approved_at = Column(DateTime)

    # Signature
    requires_signature = Column(Boolean, default=True)
    all_parties_signed = Column(Boolean, default=False)
    signed_at = Column(DateTime)

    # Document
    document_id = Column(UUID())
    signed_document_id = Column(UUID())

    # Parties
    signing_parties = Column(JSON, default=list)  # [{party_id, signed, signed_at}]

    notes = Column(Text)

    # Audit
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="amendments")

    __table_args__ = (
        Index("ix_contract_amendments_contract", "contract_id"),
        Index("ix_contract_amendments_tenant_number", "tenant_id", "contract_id", "amendment_number", unique=True),
        Index("ix_contract_amendments_type", "tenant_id", "amendment_type"),
        Index("ix_contract_amendments_status", "tenant_id", "status"),
    )


class ContractRenewal(Base):
    """Historique et suivi des renouvellements."""
    __tablename__ = "contract_renewals"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Identification
    renewal_number = Column(Integer, nullable=False)

    # Dates
    original_end_date = Column(Date, nullable=False)
    new_end_date = Column(Date, nullable=False)
    renewal_date = Column(Date, nullable=False)
    effective_date = Column(Date)

    # Type
    renewal_type = Column(String(30), nullable=False)  # automatic, manual, negotiated
    is_automatic = Column(Boolean, default=False)

    # Financier
    previous_value = Column(Numeric(18, 4))
    new_value = Column(Numeric(18, 4))
    value_change_percent = Column(Numeric(5, 2))
    currency = Column(String(3), default="EUR")

    # Conditions
    new_terms = Column(JSON)  # Nouvelles conditions
    price_index_applied = Column(String(50))
    price_increase_percent = Column(Numeric(5, 2))

    # Notification
    notice_sent = Column(Boolean, default=False)
    notice_sent_at = Column(DateTime)
    notice_response = Column(String(30))  # accepted, rejected, negotiated
    notice_response_at = Column(DateTime)

    # Statut
    status = Column(String(30), default="pending")  # pending, confirmed, cancelled, declined

    # Document
    amendment_id = Column(UUID(), ForeignKey("contract_amendments.id"))

    # Approbation
    approved_by = Column(UUID())
    approved_at = Column(DateTime)

    notes = Column(Text)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="renewals")
    amendment = relationship("ContractAmendment")

    __table_args__ = (
        Index("ix_contract_renewals_contract", "contract_id"),
        Index("ix_contract_renewals_tenant_number", "tenant_id", "contract_id", "renewal_number", unique=True),
        Index("ix_contract_renewals_date", "tenant_id", "renewal_date"),
    )


class ContractDocument(Base):
    """Document attache au contrat."""
    __tablename__ = "contract_documents"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)
    amendment_id = Column(UUID(), ForeignKey("contract_amendments.id"))

    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    document_type = Column(String(50), default="contract")  # contract, annex, amendment, supporting, signed

    # Fichier
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(64))  # SHA256

    # Version
    version_number = Column(Integer, default=1)
    is_latest_version = Column(Boolean, default=True)
    previous_version_id = Column(UUID(), ForeignKey("contract_documents.id"))

    # Signature
    is_signed = Column(Boolean, default=False)
    signature_request_id = Column(String(100))
    signed_at = Column(DateTime)
    signed_document_path = Column(String(500))

    # Statut
    status = Column(String(30), default="draft")  # draft, final, signed, archived
    is_confidential = Column(Boolean, default=False)

    # Metadata
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)

    # Acces
    is_public = Column(Boolean, default=False)
    access_token = Column(String(100))
    expires_at = Column(DateTime)

    notes = Column(Text)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="documents")
    amendment = relationship("ContractAmendment")
    previous_version = relationship("ContractDocument", remote_side=[id])

    __table_args__ = (
        Index("ix_contract_documents_contract", "contract_id"),
        Index("ix_contract_documents_type", "tenant_id", "document_type"),
        Index("ix_contract_documents_signed", "tenant_id", "is_signed"),
    )


class ContractAlert(Base):
    """Alerte contrat."""
    __tablename__ = "contract_alerts"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Type et priorite
    alert_type = Column(String(30), nullable=False)
    priority = Column(String(20), default=AlertPriority.MEDIUM.value)

    # Contenu
    title = Column(String(255), nullable=False)
    message = Column(Text)

    # Reference
    reference_type = Column(String(50))  # obligation, milestone, renewal, etc.
    reference_id = Column(UUID())

    # Date
    due_date = Column(Date, nullable=False)
    trigger_date = Column(Date)  # Date a laquelle l'alerte doit etre envoyee

    # Destinataires
    recipients = Column(JSON, default=list)  # [{user_id, email, notified}]
    notify_owner = Column(Boolean, default=True)
    notify_parties = Column(Boolean, default=False)

    # Notifications
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    send_channels = Column(JSON, default=list)  # email, sms, push, in_app
    notification_count = Column(Integer, default=0)
    last_notification_at = Column(DateTime)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(30))
    next_alert_date = Column(Date)

    # Acquittement
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(UUID())
    acknowledgement_notes = Column(Text)

    # Action
    action_required = Column(Boolean, default=True)
    action_taken = Column(Text)
    action_date = Column(DateTime)

    # Statut
    status = Column(String(30), default="pending")  # pending, sent, acknowledged, dismissed, resolved
    is_active = Column(Boolean, default=True)
    auto_dismiss_days = Column(Integer)

    notes = Column(Text)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="alerts")

    __table_args__ = (
        Index("ix_contract_alerts_contract", "contract_id"),
        Index("ix_contract_alerts_due", "tenant_id", "due_date", "status"),
        Index("ix_contract_alerts_type", "tenant_id", "alert_type"),
        Index("ix_contract_alerts_active", "tenant_id", "is_active", "is_sent"),
    )


class ContractApproval(Base):
    """Approbation de contrat - workflow multi-niveaux."""
    __tablename__ = "contract_approvals"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)
    amendment_id = Column(UUID(), ForeignKey("contract_amendments.id"))

    # Niveau approbation
    level = Column(Integer, nullable=False)
    level_name = Column(String(100))

    # Approbateur
    approver_id = Column(UUID(), nullable=False)
    approver_name = Column(String(255))
    approver_email = Column(String(255))
    approver_role = Column(String(100))

    # Delegation
    delegated_from_id = Column(UUID())
    delegation_reason = Column(Text)

    # Statut
    status = Column(String(30), default=ApprovalStatus.PENDING.value)

    # Decision
    decision = Column(String(30))  # approved, rejected
    decision_date = Column(DateTime)
    comments = Column(Text)
    rejection_reason = Column(Text)

    # Conditions
    approved_with_conditions = Column(Boolean, default=False)
    conditions = Column(JSON, default=list)

    # Echeance
    due_date = Column(DateTime)
    reminder_sent = Column(Boolean, default=False)
    reminder_count = Column(Integer, default=0)

    # Escalade
    escalated = Column(Boolean, default=False)
    escalated_to_id = Column(UUID())
    escalation_reason = Column(Text)
    escalation_date = Column(DateTime)

    # Notifications
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime)

    sort_order = Column(Integer, default=0)

    # Audit
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID())
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    updated_by = Column(UUID())

    # Relations
    contract = relationship("Contract", back_populates="approvals")
    amendment = relationship("ContractAmendment")

    __table_args__ = (
        Index("ix_contract_approvals_contract", "contract_id"),
        Index("ix_contract_approvals_approver", "tenant_id", "approver_id", "status"),
        Index("ix_contract_approvals_pending", "tenant_id", "status", "due_date"),
    )


class ContractHistory(Base):
    """Historique des modifications du contrat."""
    __tablename__ = "contract_history"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contract_id = Column(UUID(), ForeignKey("contracts.id"), nullable=False)

    # Version
    version_number = Column(Integer, nullable=False)

    # Action
    action = Column(String(50), nullable=False)  # created, updated, status_changed, signed, amended, etc.
    action_detail = Column(String(255))

    # Changements
    changes = Column(JSON)  # {field: {old: x, new: y}}
    previous_status = Column(String(30))
    new_status = Column(String(30))

    # Snapshot
    contract_snapshot = Column(JSON)  # Snapshot complet du contrat a ce moment

    # Utilisateur
    user_id = Column(UUID(), nullable=False)
    user_name = Column(String(255))
    user_email = Column(String(255))
    user_ip = Column(String(50))

    # Context
    reason = Column(Text)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    contract = relationship("Contract", back_populates="history")

    __table_args__ = (
        Index("ix_contract_history_contract", "contract_id"),
        Index("ix_contract_history_tenant_date", "tenant_id", "created_at"),
        Index("ix_contract_history_action", "tenant_id", "action"),
        Index("ix_contract_history_version", "contract_id", "version_number"),
    )


# ============================================================================
# MODELS - Reporting
# ============================================================================

class ContractMetrics(Base):
    """Metriques agregees des contrats - snapshot periodique."""
    __tablename__ = "contract_metrics"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Periode
    metric_date = Column(Date, nullable=False)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Compteurs
    total_contracts = Column(Integer, default=0)
    active_contracts = Column(Integer, default=0)
    draft_contracts = Column(Integer, default=0)
    pending_signature = Column(Integer, default=0)
    expired_contracts = Column(Integer, default=0)
    terminated_contracts = Column(Integer, default=0)

    # Nouveaux
    new_contracts = Column(Integer, default=0)
    new_value = Column(Numeric(18, 4), default=0)

    # Renouveles
    renewed_contracts = Column(Integer, default=0)
    renewal_rate = Column(Numeric(5, 2))

    # Resilies
    terminated_this_period = Column(Integer, default=0)
    churn_rate = Column(Numeric(5, 2))

    # Valeur
    total_active_value = Column(Numeric(18, 4), default=0)
    average_contract_value = Column(Numeric(18, 4), default=0)
    mrr = Column(Numeric(18, 4), default=0)  # Monthly Recurring Revenue
    arr = Column(Numeric(18, 4), default=0)  # Annual Recurring Revenue

    # Echeances
    expiring_30_days = Column(Integer, default=0)
    expiring_60_days = Column(Integer, default=0)
    expiring_90_days = Column(Integer, default=0)

    # Par type
    by_type = Column(JSON, default=dict)  # {type: count}
    by_status = Column(JSON, default=dict)  # {status: count}
    by_category = Column(JSON, default=dict)  # {category_id: count}

    # Workflow
    avg_approval_days = Column(Numeric(10, 2))
    avg_signature_days = Column(Numeric(10, 2))
    pending_approvals = Column(Integer, default=0)

    # Obligations
    overdue_obligations = Column(Integer, default=0)
    upcoming_obligations_30d = Column(Integer, default=0)

    currency = Column(String(3), default="EUR")

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_contract_metrics_tenant_date", "tenant_id", "metric_date", unique=True),
        Index("ix_contract_metrics_period", "tenant_id", "period_type", "metric_date"),
    )
