"""
AZALSCORE - Data Import/Export Types
Types, Enums et DataClasses pour l'import/export de données
"""
from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ============================================================================
# Enums
# ============================================================================

class ImportFormat(str, Enum):
    """Formats d'import supportés"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    XML = "xml"
    FEC = "fec"
    CFONB = "cfonb"


class ExportFormat(str, Enum):
    """Formats d'export supportés"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    XML = "xml"
    FEC = "fec"
    PDF = "pdf"


class ValidationSeverity(str, Enum):
    """Sévérité des erreurs de validation"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ImportStatus(str, Enum):
    """Statut d'import"""
    PENDING = "pending"
    VALIDATING = "validating"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class TransformationType(str, Enum):
    """Types de transformation"""
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    TRIM = "trim"
    DATE_FORMAT = "date_format"
    NUMBER_FORMAT = "number_format"
    LOOKUP = "lookup"
    CONCATENATE = "concatenate"
    SPLIT = "split"
    DEFAULT = "default"
    CUSTOM = "custom"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class FieldMapping:
    """Mapping d'un champ source vers destination"""
    source_field: str
    target_field: str
    data_type: str = "string"
    required: bool = False
    default_value: Any = None
    transformations: list[dict] = field(default_factory=list)
    validation_rules: list[dict] = field(default_factory=list)


@dataclass
class ImportTemplate:
    """Template d'import réutilisable"""
    id: str
    name: str
    description: str
    format: ImportFormat
    target_entity: str
    field_mappings: list[FieldMapping]
    options: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    tenant_id: str = ""
    is_active: bool = True


@dataclass
class ValidationError:
    """Erreur de validation"""
    row_number: int
    field: str
    value: Any
    message: str
    severity: ValidationSeverity
    error_code: str


@dataclass
class ImportResult:
    """Résultat d'import"""
    import_id: str
    status: ImportStatus
    total_rows: int
    processed_rows: int
    successful_rows: int
    failed_rows: int
    skipped_rows: int
    validation_errors: list[ValidationError]
    created_records: list[str]
    updated_records: list[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float
    file_hash: str
    summary: dict = field(default_factory=dict)


@dataclass
class ExportResult:
    """Résultat d'export"""
    export_id: str
    format: ExportFormat
    total_records: int
    file_path: Optional[str]
    file_content: Optional[bytes]
    file_size: int
    checksum: str
    created_at: datetime
    duration_seconds: float
    metadata: dict = field(default_factory=dict)


@dataclass
class BatchProgress:
    """Progression d'un traitement batch"""
    import_id: str
    status: ImportStatus
    total_rows: int
    processed_rows: int
    current_batch: int
    total_batches: int
    errors_count: int
    progress_percent: float
    estimated_remaining_seconds: Optional[float]
