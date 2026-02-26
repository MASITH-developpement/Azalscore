"""
AZALS - PACK PAYS FRANCE - Schémas Pydantic
=============================================
Schémas pour validation et sérialisation.
"""
from __future__ import annotations


from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# PCG - PLAN COMPTABLE GÉNÉRAL
# ============================================================================

class PCGAccountCreate(BaseModel):
    """Création compte PCG."""
    account_number: str = Field(..., min_length=1, max_length=10)
    account_label: str = Field(..., min_length=1, max_length=255)
    pcg_class: str
    parent_account: str | None = None
    is_summary: bool = False
    normal_balance: str = "D"
    default_vat_code: str | None = None
    description: str | None = None


class PCGAccountUpdate(BaseModel):
    """Mise à jour compte PCG."""
    account_label: str | None = None
    is_active: bool | None = None
    default_vat_code: str | None = None
    description: str | None = None
    notes: str | None = None


class PCGAccountResponse(BaseModel):
    """Réponse compte PCG."""
    id: int
    account_number: str
    account_label: str
    pcg_class: str
    parent_account: str | None
    is_summary: bool
    is_active: bool
    is_custom: bool
    normal_balance: str
    default_vat_code: str | None
    description: str | None
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
    account_collected: str | None = None
    account_deductible: str | None = None
    account_intra_eu: str | None = None
    applies_to_goods: bool = True
    applies_to_services: bool = True
    legal_mention: str | None = None


class FRVATRateResponse(BaseModel):
    """Réponse taux TVA."""
    id: int
    code: str
    name: str
    rate_type: str
    rate: Decimal
    account_collected: str | None
    account_deductible: str | None
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
    due_date: date | None = None


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
    due_date: date | None
    total_ht: Decimal
    total_tva_collectee: Decimal
    total_tva_deductible: Decimal
    tva_nette: Decimal
    credit_tva: Decimal
    status: str
    submitted_at: datetime | None
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
    comp_aux_num: str | None = None
    comp_aux_lib: str | None = None
    piece_ref: str
    piece_date: date
    ecriture_lib: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    ecriture_let: str | None = None
    date_let: date | None = None
    valid_date: date | None = None
    montant_devise: Decimal | None = None
    idevise: str | None = None


class FECValidationResult(BaseModel):
    """Résultat validation FEC."""
    is_valid: bool
    total_entries: int
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []


class FECExportResponse(BaseModel):
    """Réponse export FEC."""
    id: int
    fec_code: str
    siren: str
    fiscal_year: int
    period_start: date
    period_end: date
    filename: str | None
    total_entries: int
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    is_valid: bool
    status: str
    generated_at: datetime | None
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
    heures_travaillees: Decimal | None = None
    cotisations: dict[str, Decimal] | None = None
    absences: list[dict[str, Any]] | None = None


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
    submitted_at: datetime | None
    ack_status: str | None
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
    end_date: date | None = None
    trial_period_end: date | None = None
    convention_collective: str | None = None
    niveau: str | None = None
    coefficient: str | None = None
    is_full_time: bool = True
    work_hours_weekly: Decimal = Decimal("35")
    is_forfait_jours: bool = False
    forfait_jours_annual: int | None = None
    base_salary: Decimal
    salary_type: str = "mensuel"
    tickets_restaurant: bool = False
    mutuelle_obligatoire: bool = True


class FRContractResponse(BaseModel):
    """Réponse contrat français."""
    id: int
    employee_id: int
    contract_type: str
    contract_number: str | None
    start_date: date
    end_date: date | None
    convention_collective: str | None
    niveau: str | None
    coefficient: str | None
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
    data_subject_email: str | None = None
    purpose: str
    purpose_description: str | None = None
    legal_basis: str
    consent_method: str
    consent_proof: str | None = None
    valid_until: date | None = None


class RGPDConsentResponse(BaseModel):
    """Réponse consentement RGPD."""
    id: int
    data_subject_type: str
    data_subject_id: int
    purpose: str
    legal_basis: str | None
    status: str
    consent_given_at: datetime | None
    withdrawn_at: datetime | None
    valid_until: date | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RGPDRequestCreate(BaseModel):
    """Création demande RGPD."""
    request_type: str
    data_subject_type: str
    data_subject_id: int | None = None
    requester_name: str
    requester_email: str
    requester_phone: str | None = None
    request_details: str | None = None


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
    due_date: date | None
    processed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RGPDProcessingCreate(BaseModel):
    """Création traitement RGPD."""
    processing_code: str
    processing_name: str
    processing_description: str | None = None
    purposes: list[str]
    legal_basis: str
    legal_basis_details: str | None = None
    data_categories: list[str]
    special_categories: bool = False
    data_subjects: list[str]
    recipients: list[str] | None = None
    retention_period: str
    security_measures: list[str] | None = None


class RGPDProcessingResponse(BaseModel):
    """Réponse traitement RGPD."""
    id: int
    processing_code: str
    processing_name: str
    purposes: list[str]
    legal_basis: str
    data_categories: list[str]
    special_categories: bool
    retention_period: str
    is_active: bool
    aipd_required: bool
    created_at: datetime
    last_review_date: date | None

    model_config = ConfigDict(from_attributes=True)


class RGPDBreachCreate(BaseModel):
    """Signalement violation données."""
    breach_title: str
    detected_at: datetime
    breach_description: str
    breach_nature: str
    breach_cause: str | None = None
    data_categories_affected: list[str]
    estimated_subjects_affected: int | None = None
    potential_consequences: str | None = None
    severity_level: str = "medium"
    containment_measures: list[str] | None = None


class RGPDBreachResponse(BaseModel):
    """Réponse violation données."""
    id: int
    breach_code: str
    breach_title: str
    detected_at: datetime
    breach_nature: str
    severity_level: str
    estimated_subjects_affected: int | None
    cnil_notification_required: bool
    cnil_notified_at: datetime | None
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
    last_vat_declaration_date: date | None = None
    # FEC
    total_fec_exports: int = 0
    last_fec_export_date: date | None = None
    # DSN
    total_dsn_declarations: int = 0
    pending_dsn: int = 0
    rejected_dsn: int = 0
    # RGPD
    pending_rgpd_requests: int = 0
    open_data_breaches: int = 0
    active_consents: int = 0
