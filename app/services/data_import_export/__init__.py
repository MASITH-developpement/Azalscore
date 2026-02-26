"""
AZALSCORE - Data Import/Export Service
======================================
Service d'import/export de données multi-format avec validation et transformation.

Structure modulaire refactorisée depuis le fichier monolithique (2,186 lignes)
vers une architecture avec séparation des responsabilités.

@module data_import_export
"""
from typing import Optional

from .types import (
    ImportFormat,
    ExportFormat,
    ValidationSeverity,
    ImportStatus,
    TransformationType,
    FieldMapping,
    ImportTemplate,
    ValidationError,
    ImportResult,
    ExportResult,
    BatchProgress,
)
from .validators import FieldValidator
from .transformers import FieldTransformer
from .parsers import (
    BaseParser,
    CSVParser,
    ExcelParser,
    JSONParser,
    XMLParser,
    FECParser,
)
from .exporters import (
    BaseExporter,
    CSVExporter,
    ExcelExporter,
    JSONExporter,
    XMLExporter,
    FECExporter,
)
from .templates import (
    get_fec_import_template,
    get_client_import_template,
    get_invoice_import_template,
)
from .service import DataImportExportService

# ============================================================================
# Global Instance
# ============================================================================

_import_export_service: Optional[DataImportExportService] = None


def get_import_export_service() -> DataImportExportService:
    """Retourne l'instance du service d'import/export"""
    global _import_export_service
    if _import_export_service is None:
        _import_export_service = DataImportExportService()

        _import_export_service.register_template(get_fec_import_template())
        _import_export_service.register_template(get_client_import_template())
        _import_export_service.register_template(get_invoice_import_template())

    return _import_export_service


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Types
    "ImportFormat",
    "ExportFormat",
    "ValidationSeverity",
    "ImportStatus",
    "TransformationType",
    "FieldMapping",
    "ImportTemplate",
    "ValidationError",
    "ImportResult",
    "ExportResult",
    "BatchProgress",
    # Validators & Transformers
    "FieldValidator",
    "FieldTransformer",
    # Parsers
    "BaseParser",
    "CSVParser",
    "ExcelParser",
    "JSONParser",
    "XMLParser",
    "FECParser",
    # Exporters
    "BaseExporter",
    "CSVExporter",
    "ExcelExporter",
    "JSONExporter",
    "XMLExporter",
    "FECExporter",
    # Templates
    "get_fec_import_template",
    "get_client_import_template",
    "get_invoice_import_template",
    # Service
    "DataImportExportService",
    "get_import_export_service",
]
