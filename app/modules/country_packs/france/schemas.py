"""
AZALS - PACK PAYS FRANCE - Schémas Pydantic
=============================================
Schémas pour validation et sérialisation.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# PCG - PLAN COMPTABLE GÉNÉRAL
# ============================================================================

class PCGAccountCreate(BaseModel):
    """Création compte PCG."""
    account_number: str = Field(..., min_length=1, max_length=10)
    account_label: str = Field(..., min_length=1, max_length=255)
    pcg_class: str
    parent_account: Optional[str] = None
    is_summary: bool = False
    normal_balance: str = "D"
    default_vat_code: Optional[str] = None
    description: Optional[str] = None


class PCGAccountUpdate(BaseModel):
    """Mise à jour compte PCG."""
    account_label: Optional[str] = None
    is_active: Optional[bool] = None
    default_vat_code: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class PCGAccountResponse(BaseModel):
    """Réponse compte PCG."""
    id: int
    account_number: str
    account_label: str
    pcg_class: str
    parent_account: Optional[str]
    is_summary: bool
    is_active: bool
    is_custom: bool
    normal_balance: str
    default_vat_code: Optional[str]
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TVA FRANÇAISE
# ============================================================================

class FRVATRateCreate(BaseModel):
    """Création taux TVA."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    rate_type: str
    rate: Decimal
    account_collected: Optional[str] = None
    account_deductible: Optional[str] = None
    account_intra_eu: Optional[str] = None
    applies_to_goods: bool = True
    applies_to_services: bool = True
    legal_mention: Optional[str] = None


class FRVATRateResponse(BaseModel):
    """Réponse taux TVA."""
    id: int
    code: str
    name: str
    rate_type: str
    rate: Decimal
    account_collected: Optional[str]
    account_deductible: Optional[str]
    applies_to_goods: bool
    applies_to_services: bool
    is_active: bool
    valid_from: date

    model_config = ConfigDict(from_attributes=True)


class VATDeclarationCreate(BaseModel):
    """Création déclaration TVA."""
    declaration_type: str = "CA3"
    regime: str
    period_start: date
    period_end: date
    due_date: Optional[date] = None


class VATDeclarationDetails(BaseModel):
    """Détails par taux TVA."""
    rate_code: str
    rate: Decimal
    base_ht: Decimal
    tva_collectee: Decimal
    tva_deductible: Decimal


class VATDeclarationResponse(BaseModel):
    """Réponse déclaration TVA."""
    id: int
    declaration_number: str
    declaration_type: str
    regime: str
    period_start: date
    period_end: date
    due_date: Optional[date]
    total_ht: Decimal
    total_tva_collectee: Decimal
    total_tva_deductible: Decimal
    tva_nette: Decimal
    credit_tva: Decimal
    status: str
    submitted_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# FEC - FICHIER DES ÉCRITURES COMPTABLES
# ============================================================================

class FECGenerateRequest(BaseModel):
    """Demande de génération FEC."""
    fiscal_year: int
    period_start: date
    period_end: date
    siren: str = Field(..., min_length=9, max_length=9)


class FECEntrySchema(BaseModel):
    """Entrée FEC."""
    journal_code: str
    journal_lib: str
    ecriture_num: str
    ecriture_date: date
    compte_num: str
    compte_lib: str
    comp_aux_num: Optional[str] = None
    comp_aux_lib: Optional[str] = None
    piece_ref: str
    piece_date: date
    ecriture_lib: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    ecriture_let: Optional[str] = None
    date_let: Optional[date] = None
    valid_date: Optional[date] = None
    montant_devise: Optional[Decimal] = None
    idevise: Optional[str] = None


class FECValidationResult(BaseModel):
    """Résultat validation FEC."""
    is_valid: bool
    total_entries: int
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []


class FECExportResponse(BaseModel):
    """Réponse export FEC."""
    id: int
    fec_code: str
    siren: str
    fiscal_year: int
    period_start: date
    period_end: date
    filename: Optional[str]
    total_entries: int
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    is_valid: bool
    status: str
    generated_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DSN - DÉCLARATION SOCIALE NOMINATIVE
# ============================================================================

class DSNGenerateRequest(BaseModel):
    """Demande de génération DSN."""
    dsn_type: str = "MENSUELLE"
    period_month: int = Field(..., ge=1, le=12)
    period_year: int = Field(..., ge=2000)
    siret: str = Field(..., min_length=14, max_length=14)


class DSNEmployeeData(BaseModel):
    """Données salarié pour DSN."""
    employee_id: int
    nir: str = Field(..., min_length=13, max_length=15)
    nom: str
    prenoms: str
    date_naissance: date
    brut_periode: Decimal
    net_imposable: Decimal
    heures_travaillees: Optional[Decimal] = None
    cotisations: Optional[Dict[str, Decimal]] = None
    absences: Optional[List[Dict[str, Any]]] = None


class DSNDeclarationResponse(BaseModel):
    """Réponse déclaration DSN."""
    id: int
    dsn_code: str
    dsn_type: str
    siret: str
    period_month: int
    period_year: int
    total_employees: int
    total_brut: Decimal
    total_cotisations: Decimal
    status: str
    submitted_at: Optional[datetime]
    ack_status: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONTRATS FRANÇAIS
# ============================================================================

class FRContractCreate(BaseModel):
    """Création contrat français."""
    employee_id: int
    contract_type: str
    start_date: date
    end_date: Optional[date] = None
    trial_period_end: Optional[date] = None
    convention_collective: Optional[str] = None
    niveau: Optional[str] = None
    coefficient: Optional[str] = None
    is_full_time: bool = True
    work_hours_weekly: Decimal = Decimal("35")
    is_forfait_jours: bool = False
    forfait_jours_annual: Optional[int] = None
    base_salary: Decimal
    salary_type: str = "mensuel"
    tickets_restaurant: bool = False
    mutuelle_obligatoire: bool = True


class FRContractResponse(BaseModel):
    """Réponse contrat français."""
    id: int
    employee_id: int
    contract_type: str
    contract_number: Optional[str]
    start_date: date
    end_date: Optional[date]
    convention_collective: Optional[str]
    niveau: Optional[str]
    coefficient: Optional[str]
    is_full_time: bool
    work_hours_weekly: Decimal
    is_forfait_jours: bool
    base_salary: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RGPD
# ============================================================================

class RGPDConsentCreate(BaseModel):
    """Création consentement RGPD."""
    data_subject_type: str
    data_subject_id: int
    data_subject_email: Optional[str] = None
    purpose: str
    purpose_description: Optional[str] = None
    legal_basis: str
    consent_method: str
    consent_proof: Optional[str] = None
    valid_until: Optional[date] = None


class RGPDConsentResponse(BaseModel):
    """Réponse consentement RGPD."""
    id: int
    data_subject_type: str
    data_subject_id: int
    purpose: str
    legal_basis: Optional[str]
    status: str
    consent_given_at: Optional[datetime]
    withdrawn_at: Optional[datetime]
    valid_until: Optional[date]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RGPDRequestCreate(BaseModel):
    """Création demande RGPD."""
    request_type: str
    data_subject_type: str
    data_subject_id: Optional[int] = None
    requester_name: str
    requester_email: str
    requester_phone: Optional[str] = None
    request_details: Optional[str] = None


class RGPDRequestResponse(BaseModel):
    """Réponse demande RGPD."""
    id: int
    request_code: str
    request_type: str
    data_subject_type: str
    requester_name: str
    requester_email: str
    status: str
    received_at: datetime
    due_date: Optional[date]
    processed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RGPDProcessingCreate(BaseModel):
    """Création traitement RGPD."""
    processing_code: str
    processing_name: str
    processing_description: Optional[str] = None
    purposes: List[str]
    legal_basis: str
    legal_basis_details: Optional[str] = None
    data_categories: List[str]
    special_categories: bool = False
    data_subjects: List[str]
    recipients: Optional[List[str]] = None
    retention_period: str
    security_measures: Optional[List[str]] = None


class RGPDProcessingResponse(BaseModel):
    """Réponse traitement RGPD."""
    id: int
    processing_code: str
    processing_name: str
    purposes: List[str]
    legal_basis: str
    data_categories: List[str]
    special_categories: bool
    retention_period: str
    is_active: bool
    aipd_required: bool
    created_at: datetime
    last_review_date: Optional[date]

    model_config = ConfigDict(from_attributes=True)


class RGPDBreachCreate(BaseModel):
    """Signalement violation données."""
    breach_title: str
    detected_at: datetime
    breach_description: str
    breach_nature: str
    breach_cause: Optional[str] = None
    data_categories_affected: List[str]
    estimated_subjects_affected: Optional[int] = None
    potential_consequences: Optional[str] = None
    severity_level: str = "medium"
    containment_measures: Optional[List[str]] = None


class RGPDBreachResponse(BaseModel):
    """Réponse violation données."""
    id: int
    breach_code: str
    breach_title: str
    detected_at: datetime
    breach_nature: str
    severity_level: str
    estimated_subjects_affected: Optional[int]
    cnil_notification_required: bool
    cnil_notified_at: Optional[datetime]
    subjects_notification_required: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# STATISTIQUES FRANCE
# ============================================================================

class FrancePackStats(BaseModel):
    """Statistiques Pack France."""
    # PCG
    total_pcg_accounts: int = 0
    custom_accounts: int = 0
    # TVA
    total_vat_declarations: int = 0
    pending_vat_declarations: int = 0
    last_vat_declaration_date: Optional[date] = None
    # FEC
    total_fec_exports: int = 0
    last_fec_export_date: Optional[date] = None
    # DSN
    total_dsn_declarations: int = 0
    pending_dsn: int = 0
    rejected_dsn: int = 0
    # RGPD
    pending_rgpd_requests: int = 0
    open_data_breaches: int = 0
    active_consents: int = 0
