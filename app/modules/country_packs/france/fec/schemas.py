"""
AZALS MODULE - FEC: Schémas Pydantic
====================================

Schémas de validation pour l'API FEC.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# ENUMS
# ============================================================================

class FECFormatEnum(str, Enum):
    """Format de fichier FEC."""
    TXT = "txt"
    XML = "xml"


class FECEncodingEnum(str, Enum):
    """Encodage du fichier FEC."""
    UTF8 = "UTF-8"
    ISO_8859_15 = "ISO-8859-15"


class FECSeparatorEnum(str, Enum):
    """Séparateur de champs FEC."""
    TAB = "TAB"
    PIPE = "PIPE"


class FECExportStatusEnum(str, Enum):
    """Statut d'export FEC."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class FECValidationLevelEnum(str, Enum):
    """Niveau de validation."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


# ============================================================================
# COLONNES FEC (Article A.47 A-1 LPF)
# ============================================================================

class FECColumn(BaseModel):
    """
    Définition d'une colonne FEC.

    Les 18 colonnes obligatoires selon l'Article A.47 A-1 du LPF.
    """
    position: int = Field(..., ge=1, le=18, description="Position de la colonne (1-18)")
    name: str = Field(..., description="Nom technique de la colonne")
    label: str = Field(..., description="Libellé français")
    type: str = Field(..., description="Type de données (AN, N, D)")
    max_length: Optional[int] = Field(None, description="Longueur maximale")
    required: bool = Field(True, description="Colonne obligatoire")
    description: str = Field("", description="Description détaillée")


# Les 18 colonnes FEC obligatoires
FEC_COLUMNS: list[FECColumn] = [
    FECColumn(position=1, name="JournalCode", label="Code journal", type="AN", max_length=10, required=True,
              description="Code du journal comptable"),
    FECColumn(position=2, name="JournalLib", label="Libellé journal", type="AN", max_length=100, required=True,
              description="Libellé du journal comptable"),
    FECColumn(position=3, name="EcritureNum", label="Numéro écriture", type="AN", max_length=50, required=True,
              description="Numéro de l'écriture comptable"),
    FECColumn(position=4, name="EcritureDate", label="Date écriture", type="D", required=True,
              description="Date de l'écriture (YYYYMMDD)"),
    FECColumn(position=5, name="CompteNum", label="Numéro compte", type="AN", max_length=20, required=True,
              description="Numéro du compte comptable"),
    FECColumn(position=6, name="CompteLib", label="Libellé compte", type="AN", max_length=255, required=True,
              description="Libellé du compte comptable"),
    FECColumn(position=7, name="CompAuxNum", label="Numéro compte auxiliaire", type="AN", max_length=50, required=False,
              description="Numéro du compte auxiliaire (tiers)"),
    FECColumn(position=8, name="CompAuxLib", label="Libellé compte auxiliaire", type="AN", max_length=255, required=False,
              description="Libellé du compte auxiliaire"),
    FECColumn(position=9, name="PieceRef", label="Référence pièce", type="AN", max_length=100, required=True,
              description="Référence de la pièce justificative"),
    FECColumn(position=10, name="PieceDate", label="Date pièce", type="D", required=True,
              description="Date de la pièce justificative (YYYYMMDD)"),
    FECColumn(position=11, name="EcritureLib", label="Libellé écriture", type="AN", max_length=255, required=True,
              description="Libellé de l'écriture"),
    FECColumn(position=12, name="Debit", label="Montant débit", type="N", required=True,
              description="Montant au débit"),
    FECColumn(position=13, name="Credit", label="Montant crédit", type="N", required=True,
              description="Montant au crédit"),
    FECColumn(position=14, name="EcritureLet", label="Lettrage", type="AN", max_length=50, required=False,
              description="Référence de lettrage"),
    FECColumn(position=15, name="DateLet", label="Date lettrage", type="D", required=False,
              description="Date de lettrage (YYYYMMDD)"),
    FECColumn(position=16, name="ValidDate", label="Date validation", type="D", required=True,
              description="Date de validation de l'écriture (YYYYMMDD)"),
    FECColumn(position=17, name="Montantdevise", label="Montant en devise", type="N", required=False,
              description="Montant en devise étrangère"),
    FECColumn(position=18, name="Idevise", label="Code devise", type="AN", max_length=3, required=False,
              description="Code ISO devise (EUR, USD, etc.)"),
]


# ============================================================================
# REQUÊTES
# ============================================================================

class FECExportRequest(BaseModel):
    """Requête d'export FEC."""
    fiscal_year_id: UUID = Field(..., description="ID de l'exercice fiscal")
    siren: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$",
                       description="SIREN de l'entreprise (9 chiffres)")
    company_name: str = Field(..., min_length=1, max_length=255,
                              description="Raison sociale de l'entreprise")

    # Options
    format: FECFormatEnum = Field(FECFormatEnum.TXT, description="Format de fichier")
    encoding: FECEncodingEnum = Field(FECEncodingEnum.UTF8, description="Encodage")
    separator: FECSeparatorEnum = Field(FECSeparatorEnum.TAB, description="Séparateur")

    # Filtres optionnels
    start_date: Optional[date] = Field(None, description="Date de début (surcharge exercice)")
    end_date: Optional[date] = Field(None, description="Date de fin (surcharge exercice)")
    journal_codes: Optional[list[str]] = Field(None, description="Codes journaux à inclure")
    include_draft: bool = Field(False, description="Inclure les brouillons")

    @field_validator('siren')
    @classmethod
    def validate_siren(cls, v: str) -> str:
        """Valide le format SIREN."""
        if not v.isdigit() or len(v) != 9:
            raise ValueError("Le SIREN doit contenir exactement 9 chiffres")
        return v


class FECValidateRequest(BaseModel):
    """Requête de validation FEC."""
    export_id: Optional[UUID] = Field(None, description="ID de l'export à valider")
    file_content: Optional[str] = Field(None, description="Contenu du fichier FEC (base64)")
    strict_mode: bool = Field(True, description="Mode strict (erreurs sur warnings)")


# ============================================================================
# RÉPONSES
# ============================================================================

class FECValidationIssue(BaseModel):
    """Problème de validation FEC."""
    level: FECValidationLevelEnum
    code: str = Field(..., description="Code erreur (ex: FEC-001)")
    message: str
    line_number: Optional[int] = None
    column_name: Optional[str] = None
    entry_number: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None


class FECStatistics(BaseModel):
    """Statistiques du fichier FEC."""
    total_entries: int = Field(..., description="Nombre d'écritures")
    total_lines: int = Field(..., description="Nombre de lignes")
    total_debit: Decimal = Field(..., description="Total des débits")
    total_credit: Decimal = Field(..., description="Total des crédits")
    balance: Decimal = Field(..., description="Solde (doit être 0)")
    is_balanced: bool = Field(..., description="Équilibre respecté")
    journals_count: int = Field(..., description="Nombre de journaux")
    accounts_count: int = Field(..., description="Nombre de comptes utilisés")
    first_entry_date: Optional[date] = None
    last_entry_date: Optional[date] = None


class FECValidationResponse(BaseModel):
    """Réponse de validation FEC."""
    is_valid: bool = Field(..., description="FEC conforme")
    errors_count: int = Field(0, description="Nombre d'erreurs")
    warnings_count: int = Field(0, description="Nombre d'avertissements")
    issues: list[FECValidationIssue] = Field(default_factory=list)
    statistics: Optional[FECStatistics] = None
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class FECExportResponse(BaseModel):
    """Réponse d'export FEC."""
    id: UUID
    tenant_id: str
    siren: str
    company_name: str
    fiscal_year_code: str
    start_date: date
    end_date: date
    format: FECFormatEnum
    encoding: FECEncodingEnum
    separator: FECSeparatorEnum
    filename: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    status: FECExportStatusEnum
    is_valid: bool = False
    validation_errors: int = 0
    validation_warnings: int = 0
    statistics: Optional[FECStatistics] = None
    error_message: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FECDownloadResponse(BaseModel):
    """Réponse de téléchargement FEC."""
    filename: str
    content_type: str
    content: str = Field(..., description="Contenu base64 du fichier")
    file_size: int
    file_hash: str


class FECListResponse(BaseModel):
    """Liste des exports FEC."""
    items: list[FECExportResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# LIGNE FEC
# ============================================================================

class FECLine(BaseModel):
    """
    Ligne FEC (18 colonnes).

    Représente une ligne du fichier FEC conforme à l'Article A.47 A-1 du LPF.
    """
    # Colonnes obligatoires
    JournalCode: str = Field(..., max_length=10, description="Code journal")
    JournalLib: str = Field(..., max_length=100, description="Libellé journal")
    EcritureNum: str = Field(..., max_length=50, description="Numéro écriture")
    EcritureDate: str = Field(..., pattern=r"^\d{8}$", description="Date écriture YYYYMMDD")
    CompteNum: str = Field(..., max_length=20, description="Numéro compte")
    CompteLib: str = Field(..., max_length=255, description="Libellé compte")
    PieceRef: str = Field(..., max_length=100, description="Référence pièce")
    PieceDate: str = Field(..., pattern=r"^\d{8}$", description="Date pièce YYYYMMDD")
    EcritureLib: str = Field(..., max_length=255, description="Libellé écriture")
    Debit: Decimal = Field(..., ge=0, description="Montant débit")
    Credit: Decimal = Field(..., ge=0, description="Montant crédit")
    ValidDate: str = Field(..., pattern=r"^\d{8}$", description="Date validation YYYYMMDD")

    # Colonnes optionnelles
    CompAuxNum: Optional[str] = Field(None, max_length=50, description="Numéro compte auxiliaire")
    CompAuxLib: Optional[str] = Field(None, max_length=255, description="Libellé compte auxiliaire")
    EcritureLet: Optional[str] = Field(None, max_length=50, description="Lettrage")
    DateLet: Optional[str] = Field(None, pattern=r"^\d{8}$", description="Date lettrage YYYYMMDD")
    Montantdevise: Optional[Decimal] = Field(None, description="Montant en devise")
    Idevise: Optional[str] = Field(None, max_length=3, description="Code devise ISO")

    @model_validator(mode='after')
    def validate_debit_credit(self) -> 'FECLine':
        """Vérifie que débit et crédit ne sont pas tous deux non nuls."""
        if self.Debit > 0 and self.Credit > 0:
            raise ValueError("Débit et Crédit ne peuvent pas être tous deux positifs")
        if self.Debit == 0 and self.Credit == 0:
            raise ValueError("Débit ou Crédit doit être positif")
        return self

    def to_fec_row(self, separator: str = "\t") -> str:
        """Convertit en ligne FEC formatée."""
        def format_decimal(value: Optional[Decimal]) -> str:
            if value is None:
                return ""
            # Format français: virgule décimale, pas de séparateur milliers
            return str(value).replace(".", ",")

        values = [
            self.JournalCode,
            self.JournalLib,
            self.EcritureNum,
            self.EcritureDate,
            self.CompteNum,
            self.CompteLib,
            self.CompAuxNum or "",
            self.CompAuxLib or "",
            self.PieceRef,
            self.PieceDate,
            self.EcritureLib,
            format_decimal(self.Debit),
            format_decimal(self.Credit),
            self.EcritureLet or "",
            self.DateLet or "",
            self.ValidDate,
            format_decimal(self.Montantdevise) if self.Montantdevise else "",
            self.Idevise or "",
        ]
        return separator.join(values)
