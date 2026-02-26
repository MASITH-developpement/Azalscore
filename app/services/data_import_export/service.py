"""
AZALSCORE - Data Import/Export Service
Service principal d'import/export de données
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import zipfile
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Optional

from .types import (
    ImportFormat,
    ExportFormat,
    ImportStatus,
    ValidationSeverity,
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

logger = logging.getLogger(__name__)


class DataImportExportService:
    """Service d'import/export de données"""

    # Limites pour la création d'archives
    MAX_ARCHIVE_FILES = 1000
    MAX_ARCHIVE_SIZE = 500 * 1024 * 1024  # 500 Mo
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 Mo par fichier

    def __init__(self):
        self._parsers: dict[ImportFormat, BaseParser] = {
            ImportFormat.CSV: CSVParser(),
            ImportFormat.EXCEL: ExcelParser(),
            ImportFormat.JSON: JSONParser(),
            ImportFormat.XML: XMLParser(),
            ImportFormat.FEC: FECParser(),
        }

        self._exporters: dict[ExportFormat, BaseExporter] = {
            ExportFormat.CSV: CSVExporter(),
            ExportFormat.EXCEL: ExcelExporter(),
            ExportFormat.JSON: JSONExporter(),
            ExportFormat.XML: XMLExporter(),
            ExportFormat.FEC: FECExporter(),
        }

        self._templates: dict[str, ImportTemplate] = {}
        self._import_results: dict[str, ImportResult] = {}
        self._progress_callbacks: dict[str, Callable] = {}
        self._batch_size: int = 1000

    # ========================================================================
    # Template Management
    # ========================================================================

    def register_template(self, template: ImportTemplate) -> None:
        """Enregistre un template d'import"""
        self._templates[template.id] = template
        logger.info(f"Template d'import enregistré: {template.id}")

    def get_template(self, template_id: str) -> Optional[ImportTemplate]:
        """Récupère un template par son ID"""
        return self._templates.get(template_id)

    def list_templates(self, tenant_id: str = None) -> list[ImportTemplate]:
        """Liste les templates disponibles"""
        templates = list(self._templates.values())
        if tenant_id:
            templates = [t for t in templates if t.tenant_id == tenant_id or not t.tenant_id]
        return [t for t in templates if t.is_active]

    # ========================================================================
    # File Analysis
    # ========================================================================

    def get_file_headers(
        self,
        content: bytes,
        format: ImportFormat,
        options: dict = None
    ) -> list[str]:
        """Analyse un fichier et retourne ses en-têtes"""
        options = options or {}
        parser = self._parsers.get(format)
        if not parser:
            raise ValueError(f"Format non supporté: {format}")
        return parser.get_headers(content, options)

    def preview_import(
        self,
        content: bytes,
        format: ImportFormat,
        options: dict = None,
        max_rows: int = 10
    ) -> list[dict]:
        """Prévisualise les premières lignes d'un fichier"""
        options = options or {}
        parser = self._parsers.get(format)
        if not parser:
            raise ValueError(f"Format non supporté: {format}")

        preview_data = []
        for record in parser.parse(content, options):
            preview_data.append(record)
            if len(preview_data) >= max_rows:
                break

        return preview_data

    # ========================================================================
    # Validation
    # ========================================================================

    def validate_data(
        self,
        content: bytes,
        format: ImportFormat,
        field_mappings: list[FieldMapping],
        options: dict = None
    ) -> tuple[bool, list[ValidationError]]:
        """Valide les données sans les importer"""
        options = options or {}
        parser = self._parsers.get(format)
        if not parser:
            raise ValueError(f"Format non supporté: {format}")

        errors = []
        row_count = 0

        for record in parser.parse(content, options):
            row_number = record.get("__row_number__", row_count + 1)
            row_count += 1

            for mapping in field_mappings:
                value = record.get(mapping.source_field)

                for transformation in mapping.transformations:
                    value = FieldTransformer.transform(value, transformation)

                if mapping.required:
                    error = FieldValidator.validate_required(value, mapping.target_field)
                    if error:
                        error.row_number = row_number
                        errors.append(error)
                        continue

                error = FieldValidator.validate_type(value, mapping.data_type, mapping.target_field)
                if error:
                    error.row_number = row_number
                    errors.append(error)

                for rule in mapping.validation_rules:
                    rule_type = rule.get("type")

                    if rule_type == "length":
                        error = FieldValidator.validate_length(
                            value, rule.get("min", 0), rule.get("max", 999999),
                            mapping.target_field
                        )
                    elif rule_type == "pattern":
                        error = FieldValidator.validate_pattern(
                            value, rule.get("pattern"), mapping.target_field
                        )
                    elif rule_type == "range":
                        error = FieldValidator.validate_range(
                            value, rule.get("min"), rule.get("max"),
                            mapping.target_field
                        )
                    elif rule_type == "enum":
                        error = FieldValidator.validate_enum(
                            value, rule.get("values", []), mapping.target_field
                        )
                    else:
                        error = None

                    if error:
                        error.row_number = row_number
                        errors.append(error)

        has_critical_errors = any(e.severity == ValidationSeverity.ERROR for e in errors)
        return not has_critical_errors, errors

    # ========================================================================
    # Import
    # ========================================================================

    async def import_data(
        self,
        content: bytes,
        format: ImportFormat,
        field_mappings: list[FieldMapping],
        entity_handler: Callable[[dict], str],
        options: dict = None,
        tenant_id: str = "",
        import_id: str = None,
        validate_first: bool = True,
        stop_on_error: bool = False,
        progress_callback: Callable[[BatchProgress], None] = None
    ) -> ImportResult:
        """Importe les données avec transformation et validation"""
        import uuid

        options = options or {}
        import_id = import_id or str(uuid.uuid4())

        started_at = datetime.utcnow()
        file_hash = hashlib.sha256(content).hexdigest()

        result = ImportResult(
            import_id=import_id,
            status=ImportStatus.VALIDATING,
            total_rows=0,
            processed_rows=0,
            successful_rows=0,
            failed_rows=0,
            skipped_rows=0,
            validation_errors=[],
            created_records=[],
            updated_records=[],
            started_at=started_at,
            completed_at=None,
            duration_seconds=0,
            file_hash=file_hash
        )

        self._import_results[import_id] = result

        if progress_callback:
            self._progress_callbacks[import_id] = progress_callback

        parser = self._parsers.get(format)
        if not parser:
            result.status = ImportStatus.FAILED
            result.validation_errors.append(ValidationError(
                row_number=0,
                field="",
                value=format,
                message=f"Format non supporté: {format}",
                severity=ValidationSeverity.ERROR,
                error_code="UNSUPPORTED_FORMAT"
            ))
            return result

        try:
            all_records = list(parser.parse(content, options))
            result.total_rows = len(all_records)
        except Exception as e:
            result.status = ImportStatus.FAILED
            result.validation_errors.append(ValidationError(
                row_number=0,
                field="",
                value="",
                message=f"Erreur de parsing: {str(e)}",
                severity=ValidationSeverity.ERROR,
                error_code="PARSE_ERROR"
            ))
            return result

        if validate_first:
            is_valid, errors = self.validate_data(content, format, field_mappings, options)
            result.validation_errors.extend(errors)

            if not is_valid and stop_on_error:
                result.status = ImportStatus.FAILED
                result.completed_at = datetime.utcnow()
                result.duration_seconds = (result.completed_at - started_at).total_seconds()
                return result

        result.status = ImportStatus.IMPORTING

        total_batches = (len(all_records) + self._batch_size - 1) // self._batch_size

        for batch_num in range(total_batches):
            start_idx = batch_num * self._batch_size
            end_idx = min(start_idx + self._batch_size, len(all_records))
            batch = all_records[start_idx:end_idx]

            for record in batch:
                row_number = record.get("__row_number__", result.processed_rows + 1)
                result.processed_rows += 1

                try:
                    transformed_record = self._transform_record(record, field_mappings)

                    if transformed_record is None:
                        result.skipped_rows += 1
                        continue

                    record_id = await self._execute_handler(entity_handler, transformed_record)

                    if record_id:
                        result.successful_rows += 1
                        result.created_records.append(record_id)
                    else:
                        result.failed_rows += 1

                except Exception as e:
                    result.failed_rows += 1
                    result.validation_errors.append(ValidationError(
                        row_number=row_number,
                        field="",
                        value="",
                        message=str(e),
                        severity=ValidationSeverity.ERROR,
                        error_code="IMPORT_ERROR"
                    ))

                    if stop_on_error:
                        result.status = ImportStatus.FAILED
                        break

            if progress_callback:
                progress = BatchProgress(
                    import_id=import_id,
                    status=result.status,
                    total_rows=result.total_rows,
                    processed_rows=result.processed_rows,
                    current_batch=batch_num + 1,
                    total_batches=total_batches,
                    errors_count=result.failed_rows,
                    progress_percent=(result.processed_rows / result.total_rows) * 100,
                    estimated_remaining_seconds=None
                )
                progress_callback(progress)

            if result.status == ImportStatus.FAILED:
                break

            await asyncio.sleep(0)

        result.completed_at = datetime.utcnow()
        result.duration_seconds = (result.completed_at - started_at).total_seconds()

        if result.status != ImportStatus.FAILED:
            if result.failed_rows == 0:
                result.status = ImportStatus.COMPLETED
            elif result.successful_rows > 0:
                result.status = ImportStatus.PARTIAL
            else:
                result.status = ImportStatus.FAILED

        result.summary = {
            "total_rows": result.total_rows,
            "successful": result.successful_rows,
            "failed": result.failed_rows,
            "skipped": result.skipped_rows,
            "success_rate": (result.successful_rows / result.total_rows * 100) if result.total_rows > 0 else 0,
            "duration_seconds": result.duration_seconds,
            "rows_per_second": result.processed_rows / result.duration_seconds if result.duration_seconds > 0 else 0
        }

        logger.info(
            f"Import terminé: {import_id} - "
            f"Status: {result.status} - "
            f"Succès: {result.successful_rows}/{result.total_rows}"
        )

        return result

    def _transform_record(
        self,
        record: dict,
        field_mappings: list[FieldMapping]
    ) -> Optional[dict]:
        """Transforme un enregistrement selon les mappings"""
        transformed = {}

        for mapping in field_mappings:
            value = record.get(mapping.source_field)

            if value is None and mapping.default_value is not None:
                value = mapping.default_value

            for transformation in mapping.transformations:
                value = FieldTransformer.transform(value, transformation)

            if mapping.data_type == "integer":
                try:
                    value = int(str(value).replace(" ", "")) if value else None
                except (ValueError, TypeError):
                    value = None
            elif mapping.data_type == "decimal":
                try:
                    value = Decimal(str(value).replace(" ", "").replace(",", ".")) if value else None
                except (ValueError, TypeError):
                    value = None
            elif mapping.data_type == "date":
                if value and not isinstance(value, date):
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"]:
                        try:
                            value = datetime.strptime(str(value), fmt).date()
                            break
                        except ValueError:
                            continue
            elif mapping.data_type == "boolean":
                if isinstance(value, bool):
                    pass
                elif value:
                    value = str(value).lower() in ("true", "1", "oui", "yes")
                else:
                    value = False

            transformed[mapping.target_field] = value

        return transformed

    async def _execute_handler(self, handler: Callable, record: dict) -> Optional[str]:
        """Exécute le handler de création/mise à jour"""
        if asyncio.iscoroutinefunction(handler):
            return await handler(record)
        return handler(record)

    def get_import_result(self, import_id: str) -> Optional[ImportResult]:
        """Récupère le résultat d'un import"""
        return self._import_results.get(import_id)

    # ========================================================================
    # Export
    # ========================================================================

    def export_data(
        self,
        data: list[dict],
        format: ExportFormat,
        options: dict = None,
        export_id: str = None
    ) -> ExportResult:
        """Exporte des données vers un format cible"""
        import uuid

        options = options or {}
        export_id = export_id or str(uuid.uuid4())

        started_at = datetime.utcnow()

        exporter = self._exporters.get(format)
        if not exporter:
            raise ValueError(f"Format d'export non supporté: {format}")

        file_content = exporter.export(data, options)

        completed_at = datetime.utcnow()
        checksum = hashlib.sha256(file_content).hexdigest()

        result = ExportResult(
            export_id=export_id,
            format=format,
            total_records=len(data),
            file_path=None,
            file_content=file_content,
            file_size=len(file_content),
            checksum=checksum,
            created_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            metadata=options.get("metadata", {})
        )

        logger.info(
            f"Export terminé: {export_id} - "
            f"Format: {format} - "
            f"Records: {len(data)} - "
            f"Taille: {len(file_content)} octets"
        )

        return result

    def export_to_file(
        self,
        data: list[dict],
        format: ExportFormat,
        file_path: str,
        options: dict = None,
        allowed_base_path: str = None
    ) -> ExportResult:
        """Exporte les données directement vers un fichier"""
        result = self.export_data(data, format, options)

        # Protection path traversal
        target_path = Path(file_path).resolve()

        if allowed_base_path:
            base_path = Path(allowed_base_path).resolve()
            try:
                target_path.relative_to(base_path)
            except ValueError:
                raise ValueError(
                    f"Chemin de fichier non autorisé: {file_path} "
                    f"(doit être sous {allowed_base_path})"
                )

        # Vérification des caractères dangereux
        dangerous_chars = ['..', '\x00', '|', '>', '<', '&', ';', '$', '`']
        file_name = target_path.name
        for char in dangerous_chars:
            if char in file_name:
                raise ValueError(f"Caractère non autorisé dans le nom de fichier: {char}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as f:
            f.write(result.file_content)

        result.file_path = str(target_path)
        result.file_content = None

        return result

    def create_archive(
        self,
        exports: list[tuple[str, bytes]],
        archive_format: str = "zip"
    ) -> bytes:
        """Crée une archive contenant plusieurs exports (avec protections)"""
        if archive_format != "zip":
            raise ValueError(f"Format d'archive non supporté: {archive_format}")

        if len(exports) > self.MAX_ARCHIVE_FILES:
            raise ValueError(f"Trop de fichiers ({len(exports)} > {self.MAX_ARCHIVE_FILES})")

        total_size = sum(len(content) for _, content in exports)
        if total_size > self.MAX_ARCHIVE_SIZE:
            raise ValueError(
                f"Taille totale trop importante "
                f"({total_size // (1024*1024)} Mo > {self.MAX_ARCHIVE_SIZE // (1024*1024)} Mo)"
            )

        output = io.BytesIO()

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in exports:
                if '..' in filename or filename.startswith('/'):
                    raise ValueError(f"Nom de fichier non autorisé: {filename}")

                if len(content) > self.MAX_FILE_SIZE:
                    raise ValueError(
                        f"Fichier trop volumineux: {filename} "
                        f"({len(content) // (1024*1024)} Mo > {self.MAX_FILE_SIZE // (1024*1024)} Mo)"
                    )

                zf.writestr(filename, content)

        return output.getvalue()
