"""
AZALS MODULE - PCG 2025: Schemas
=================================

Schémas Pydantic pour le Plan Comptable Général 2025.
"""
from __future__ import annotations


from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# REQUESTS
# ============================================================================

class PCGAccountCreate(BaseModel):
    """Création d'un compte PCG personnalisé."""
    account_number: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Numéro du compte (ex: 411001)",
        pattern=r"^[1-8]\d{1,9}$",
    )
    account_label: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Libellé du compte",
    )
    parent_account: Optional[str] = Field(
        None,
        description="Numéro du compte parent (optionnel, déduit automatiquement)",
    )
    is_summary: bool = Field(
        False,
        description="Compte de regroupement (synthétique)",
    )
    normal_balance: Literal["D", "C"] = Field(
        "D",
        description="Solde normal: D=Débit, C=Crédit",
    )
    description: Optional[str] = Field(
        None,
        description="Description du compte",
    )
    default_vat_code: Optional[str] = Field(
        None,
        description="Code TVA par défaut pour ce compte",
    )

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Le numéro de compte doit être numérique")
        if v[0] not in "12345678":
            raise ValueError("Le numéro doit commencer par un chiffre de classe (1-8)")
        return v


class PCGAccountUpdate(BaseModel):
    """Mise à jour d'un compte PCG personnalisé."""
    account_label: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    default_vat_code: Optional[str] = None
    notes: Optional[str] = None


class PCGInitRequest(BaseModel):
    """Paramètres d'initialisation du PCG."""
    force: bool = Field(
        False,
        description="Forcer la réinitialisation (supprime les comptes standard existants)",
    )
    version: Literal["2024", "2025"] = Field(
        "2025",
        description="Version du PCG à initialiser",
    )


class PCGMigrateRequest(BaseModel):
    """Paramètres de migration PCG."""
    source_version: Literal["2024"] = Field(
        "2024",
        description="Version source",
    )
    target_version: Literal["2025"] = Field(
        "2025",
        description="Version cible",
    )


# ============================================================================
# RESPONSES
# ============================================================================

class PCGAccountResponse(BaseModel):
    """Réponse compte PCG."""
    id: UUID
    tenant_id: str
    account_number: str
    account_label: str
    pcg_class: str
    parent_account: Optional[str] = None
    is_summary: bool
    is_active: bool
    is_custom: bool
    normal_balance: str
    description: Optional[str] = None
    default_vat_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PCGAccountListResponse(BaseModel):
    """Liste paginée de comptes PCG."""
    items: list[PCGAccountResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PCGInitResult(BaseModel):
    """Résultat d'initialisation du PCG."""
    success: bool
    message: str
    accounts_created: int
    accounts_existing: int = 0
    version: Optional[str] = "2025"


class PCGValidationIssue(BaseModel):
    """Problème de validation PCG."""
    code: str
    message: str
    severity: Literal["error", "warning", "info"] = "error"
    field: Optional[str] = None
    value: Optional[str] = None


class PCGValidationResult(BaseModel):
    """Résultat de validation d'un compte PCG."""
    is_valid: bool
    account_number: str
    is_standard: bool = False
    standard_label: Optional[str] = None
    pcg_class: Optional[str] = None
    normal_balance: Optional[str] = None
    issues: list[PCGValidationIssue] = []


class PCGMigrationResult(BaseModel):
    """Résultat de migration PCG."""
    success: bool
    source_version: str
    target_version: str
    accounts_updated: int
    accounts_added: int
    accounts_unchanged: int
    details: list[str] = []


class PCGStatisticsResponse(BaseModel):
    """Statistiques du plan comptable."""
    total_accounts: int
    active_accounts: int
    inactive_accounts: int
    custom_accounts: int
    standard_accounts: int
    by_class: dict[str, int]
    pcg_version: str


class PCGStatusResponse(BaseModel):
    """État d'initialisation du PCG."""
    is_initialized: bool
    standard_accounts: int
    custom_accounts: int
    total_accounts: int
    expected_standard: int
    is_complete: bool
    completion_percentage: float


class PCGHierarchyResponse(BaseModel):
    """Hiérarchie d'un compte."""
    account_number: str
    hierarchy: list[PCGAccountResponse]
    children: list[PCGAccountResponse]


# ============================================================================
# RÉFÉRENCE
# ============================================================================

class PCGClassInfo(BaseModel):
    """Information sur une classe PCG."""
    class_number: str
    class_name: str
    description: str
    balance_type: Literal["actif", "passif", "charges", "produits", "special"]


PCG_CLASSES = [
    PCGClassInfo(
        class_number="1",
        class_name="Comptes de capitaux",
        description="Capital, réserves, emprunts, provisions",
        balance_type="passif",
    ),
    PCGClassInfo(
        class_number="2",
        class_name="Comptes d'immobilisations",
        description="Immobilisations incorporelles, corporelles et financières",
        balance_type="actif",
    ),
    PCGClassInfo(
        class_number="3",
        class_name="Comptes de stocks et en-cours",
        description="Matières premières, produits, marchandises",
        balance_type="actif",
    ),
    PCGClassInfo(
        class_number="4",
        class_name="Comptes de tiers",
        description="Fournisseurs, clients, personnel, État",
        balance_type="actif",  # Mixte en réalité
    ),
    PCGClassInfo(
        class_number="5",
        class_name="Comptes financiers",
        description="Banque, caisse, VMP",
        balance_type="actif",
    ),
    PCGClassInfo(
        class_number="6",
        class_name="Comptes de charges",
        description="Achats, services, personnel, impôts",
        balance_type="charges",
    ),
    PCGClassInfo(
        class_number="7",
        class_name="Comptes de produits",
        description="Ventes, prestations, produits financiers",
        balance_type="produits",
    ),
    PCGClassInfo(
        class_number="8",
        class_name="Comptes spéciaux",
        description="Engagements hors bilan, résultat",
        balance_type="special",
    ),
]
