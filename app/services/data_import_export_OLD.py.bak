"""
Service d'Import/Export de Données - AZALSCORE
Import et export de données multi-format avec validation et transformation
"""
from __future__ import annotations


import csv
import json
import io
import hashlib
import zipfile
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Callable, Generator, TypeVar, Generic
from dataclasses import dataclass, field
from pathlib import Path
# XML - Import standard pour types, defusedxml pour parsing sécurisé
import xml.etree.ElementTree as ET_std  # Pour les types (Element, etc.)
import defusedxml.ElementTree as DefusedET  # Pour parsing sécurisé (XXE protection)
import defusedxml.minidom as minidom  # Sécurisé contre XXE attacks

# Alias pour compatibilité - utiliser DefusedET.fromstring() pour parser
ET = type('ET', (), {
    'Element': ET_std.Element,
    'SubElement': ET_std.SubElement,
    'tostring': ET_std.tostring,
    'fromstring': DefusedET.fromstring,  # Parsing sécurisé
    'parse': DefusedET.parse,  # Parsing sécurisé
    'ParseError': ET_std.ParseError,
})()
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Enums et Types
# ============================================================================

class ImportFormat(str, Enum):
    """Formats d'import supportés"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    XML = "xml"
    FEC = "fec"  # Format FEC spécifique
    CFONB = "cfonb"  # Format bancaire français


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


# ============================================================================
# Validators
# ============================================================================

class FieldValidator:
    """Validateur de champs"""

    @staticmethod
    def validate_required(value: Any, field_name: str) -> Optional[ValidationError]:
        """Valide qu'un champ est renseigné"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' est obligatoire",
                severity=ValidationSeverity.ERROR,
                error_code="REQUIRED_FIELD"
            )
        return None

    @staticmethod
    def validate_type(value: Any, expected_type: str, field_name: str) -> Optional[ValidationError]:
        """Valide le type d'un champ"""
        type_validators = {
            "string": lambda v: isinstance(v, str) or v is None,
            "integer": lambda v: FieldValidator._is_valid_integer(v),
            "decimal": lambda v: FieldValidator._is_valid_decimal(v),
            "date": lambda v: FieldValidator._is_valid_date(v),
            "datetime": lambda v: FieldValidator._is_valid_datetime(v),
            "boolean": lambda v: FieldValidator._is_valid_boolean(v),
            "email": lambda v: FieldValidator._is_valid_email(v),
            "siren": lambda v: FieldValidator._is_valid_siren(v),
            "siret": lambda v: FieldValidator._is_valid_siret(v),
            "iban": lambda v: FieldValidator._is_valid_iban(v),
        }

        validator = type_validators.get(expected_type)
        if validator and not validator(value):
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' doit être de type {expected_type}",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_TYPE"
            )
        return None

    @staticmethod
    def validate_length(value: Any, min_len: int, max_len: int, field_name: str) -> Optional[ValidationError]:
        """Valide la longueur d'un champ"""
        if value is None:
            return None
        str_value = str(value)
        if len(str_value) < min_len or len(str_value) > max_len:
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' doit avoir entre {min_len} et {max_len} caractères",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_LENGTH"
            )
        return None

    @staticmethod
    def validate_pattern(value: Any, pattern: str, field_name: str) -> Optional[ValidationError]:
        """Valide un champ contre une expression régulière"""
        import re
        if value is None:
            return None
        if not re.match(pattern, str(value)):
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' ne correspond pas au format attendu",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_PATTERN"
            )
        return None

    @staticmethod
    def validate_range(value: Any, min_val: Any, max_val: Any, field_name: str) -> Optional[ValidationError]:
        """Valide qu'une valeur est dans une plage"""
        if value is None:
            return None
        try:
            num_value = Decimal(str(value))
            if min_val is not None and num_value < Decimal(str(min_val)):
                return ValidationError(
                    row_number=0,
                    field=field_name,
                    value=value,
                    message=f"Le champ '{field_name}' doit être >= {min_val}",
                    severity=ValidationSeverity.ERROR,
                    error_code="VALUE_TOO_LOW"
                )
            if max_val is not None and num_value > Decimal(str(max_val)):
                return ValidationError(
                    row_number=0,
                    field=field_name,
                    value=value,
                    message=f"Le champ '{field_name}' doit être <= {max_val}",
                    severity=ValidationSeverity.ERROR,
                    error_code="VALUE_TOO_HIGH"
                )
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def validate_enum(value: Any, allowed_values: list, field_name: str) -> Optional[ValidationError]:
        """Valide qu'une valeur est dans une liste autorisée"""
        if value is None:
            return None
        if value not in allowed_values:
            return ValidationError(
                row_number=0,
                field=field_name,
                value=value,
                message=f"Le champ '{field_name}' doit être l'une des valeurs: {', '.join(map(str, allowed_values))}",
                severity=ValidationSeverity.ERROR,
                error_code="INVALID_ENUM_VALUE"
            )
        return None

    @staticmethod
    def _is_valid_integer(value: Any) -> bool:
        if value is None or value == "":
            return True
        try:
            int(str(value).replace(" ", ""))
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_valid_decimal(value: Any) -> bool:
        if value is None or value == "":
            return True
        try:
            Decimal(str(value).replace(" ", "").replace(",", "."))
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_valid_date(value: Any) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, (date, datetime)):
            return True
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"]
        for fmt in date_formats:
            try:
                datetime.strptime(str(value), fmt)
                return True
            except ValueError:
                continue
        return False

    @staticmethod
    def _is_valid_datetime(value: Any) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, datetime):
            return True
        datetime_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y %H:%M:%S",
        ]
        for fmt in datetime_formats:
            try:
                datetime.strptime(str(value), fmt)
                return True
            except ValueError:
                continue
        return False

    @staticmethod
    def _is_valid_boolean(value: Any) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, bool):
            return True
        return str(value).lower() in ("true", "false", "1", "0", "oui", "non", "yes", "no")

    @staticmethod
    def _is_valid_email(value: Any) -> bool:
        import re
        if value is None or value == "":
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(value)))

    @staticmethod
    def _is_valid_siren(value: Any) -> bool:
        if value is None or value == "":
            return True
        siren = str(value).replace(" ", "")
        if len(siren) != 9 or not siren.isdigit():
            return False
        return FieldValidator._luhn_check(siren)

    @staticmethod
    def _is_valid_siret(value: Any) -> bool:
        if value is None or value == "":
            return True
        siret = str(value).replace(" ", "")
        if len(siret) != 14 or not siret.isdigit():
            return False
        return FieldValidator._luhn_check(siret)

    @staticmethod
    def _is_valid_iban(value: Any) -> bool:
        if value is None or value == "":
            return True
        iban = str(value).replace(" ", "").upper()
        if len(iban) < 15 or len(iban) > 34:
            return False
        if not iban[:2].isalpha() or not iban[2:4].isdigit():
            return False
        rearranged = iban[4:] + iban[:4]
        numeric = ""
        for char in rearranged:
            if char.isdigit():
                numeric += char
            else:
                numeric += str(ord(char) - 55)
        return int(numeric) % 97 == 1

    @staticmethod
    def _luhn_check(number: str) -> bool:
        """Vérifie la clé de Luhn (SIREN/SIRET)"""
        total = 0
        for i, char in enumerate(reversed(number)):
            digit = int(char)
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        return total % 10 == 0


# ============================================================================
# Transformers
# ============================================================================

class FieldTransformer:
    """Transformateur de champs"""

    @staticmethod
    def transform(value: Any, transformation: dict) -> Any:
        """Applique une transformation à une valeur"""
        transform_type = TransformationType(transformation.get("type", "trim"))

        transformers = {
            TransformationType.UPPERCASE: FieldTransformer._uppercase,
            TransformationType.LOWERCASE: FieldTransformer._lowercase,
            TransformationType.TRIM: FieldTransformer._trim,
            TransformationType.DATE_FORMAT: FieldTransformer._date_format,
            TransformationType.NUMBER_FORMAT: FieldTransformer._number_format,
            TransformationType.LOOKUP: FieldTransformer._lookup,
            TransformationType.CONCATENATE: FieldTransformer._concatenate,
            TransformationType.SPLIT: FieldTransformer._split,
            TransformationType.DEFAULT: FieldTransformer._default,
            TransformationType.CUSTOM: FieldTransformer._custom,
        }

        transformer = transformers.get(transform_type)
        if transformer:
            return transformer(value, transformation)
        return value

    @staticmethod
    def _uppercase(value: Any, params: dict) -> Any:
        return str(value).upper() if value else value

    @staticmethod
    def _lowercase(value: Any, params: dict) -> Any:
        return str(value).lower() if value else value

    @staticmethod
    def _trim(value: Any, params: dict) -> Any:
        return str(value).strip() if value else value

    @staticmethod
    def _date_format(value: Any, params: dict) -> Any:
        """Convertit une date d'un format à un autre"""
        if not value:
            return value

        input_format = params.get("input_format", "%d/%m/%Y")
        output_format = params.get("output_format", "%Y-%m-%d")

        if isinstance(value, (date, datetime)):
            return value.strftime(output_format)

        input_formats = [input_format, "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"]
        for fmt in input_formats:
            try:
                parsed = datetime.strptime(str(value), fmt)
                return parsed.strftime(output_format)
            except ValueError:
                continue
        return value

    @staticmethod
    def _number_format(value: Any, params: dict) -> Any:
        """Formate un nombre"""
        if not value:
            return value

        decimal_separator = params.get("input_decimal", ",")
        thousands_separator = params.get("input_thousands", " ")
        output_decimal = params.get("output_decimal", ".")
        precision = params.get("precision")

        try:
            str_value = str(value)
            str_value = str_value.replace(thousands_separator, "")
            str_value = str_value.replace(decimal_separator, ".")
            num_value = Decimal(str_value)

            if precision is not None:
                num_value = round(num_value, precision)

            result = str(num_value)
            if output_decimal != ".":
                result = result.replace(".", output_decimal)

            return result
        except (ValueError, TypeError):
            return value

    @staticmethod
    def _lookup(value: Any, params: dict) -> Any:
        """Recherche une valeur dans une table de correspondance"""
        lookup_table = params.get("table", {})
        default = params.get("default")
        case_sensitive = params.get("case_sensitive", False)

        if not case_sensitive and value:
            value_lower = str(value).lower()
            for key, mapped_value in lookup_table.items():
                if str(key).lower() == value_lower:
                    return mapped_value
        else:
            if value in lookup_table:
                return lookup_table[value]

        return default if default is not None else value

    @staticmethod
    def _concatenate(value: Any, params: dict) -> Any:
        """Concatène avec d'autres valeurs"""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        return f"{prefix}{value or ''}{suffix}"

    @staticmethod
    def _split(value: Any, params: dict) -> Any:
        """Divise une valeur et retourne une partie"""
        if not value:
            return value

        separator = params.get("separator", ",")
        index = params.get("index", 0)

        parts = str(value).split(separator)
        if 0 <= index < len(parts):
            return parts[index].strip()
        return value

    @staticmethod
    def _default(value: Any, params: dict) -> Any:
        """Retourne une valeur par défaut si vide"""
        default_value = params.get("value")
        if value is None or (isinstance(value, str) and not value.strip()):
            return default_value
        return value

    @staticmethod
    def _custom(value: Any, params: dict) -> Any:
        """Transformation personnalisée via opérations prédéfinies sécurisées

        IMPORTANT: N'utilise PAS eval() pour des raisons de sécurité.
        Supporte uniquement des opérations prédéfinies et sûres.
        """
        operation = params.get("operation")
        if not operation:
            return value

        try:
            # Opérations sécurisées prédéfinies
            if operation == "substring":
                start = params.get("start", 0)
                end = params.get("end")
                if value and isinstance(value, str):
                    return value[start:end] if end else value[start:]

            elif operation == "pad_left":
                width = params.get("width", 0)
                char = params.get("char", " ")[:1] or " "
                return str(value or "").rjust(width, char)

            elif operation == "pad_right":
                width = params.get("width", 0)
                char = params.get("char", " ")[:1] or " "
                return str(value or "").ljust(width, char)

            elif operation == "replace_chars":
                old_char = params.get("old", "")
                new_char = params.get("new", "")
                if value and isinstance(value, str):
                    return value.replace(old_char, new_char)

            elif operation == "extract_digits":
                if value:
                    return "".join(c for c in str(value) if c.isdigit())

            elif operation == "extract_alpha":
                if value:
                    return "".join(c for c in str(value) if c.isalpha())

            elif operation == "format_phone":
                # Format téléphone français
                if value:
                    digits = "".join(c for c in str(value) if c.isdigit())
                    if len(digits) == 10:
                        return " ".join([digits[i:i+2] for i in range(0, 10, 2)])

            elif operation == "normalize_spaces":
                if value and isinstance(value, str):
                    return " ".join(value.split())

            else:
                logger.warning(f"Opération custom non reconnue: {operation}")

            return value
        except Exception as e:
            logger.warning(f"Erreur transformation custom: {e}")
            return value


# ============================================================================
# Parsers
# ============================================================================

class BaseParser(ABC):
    """Classe de base pour les parsers"""

    @abstractmethod
    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        """Parse le contenu et génère des enregistrements"""
        pass

    @abstractmethod
    def get_headers(self, content: bytes, options: dict) -> list[str]:
        """Retourne les en-têtes du fichier"""
        pass


class CSVParser(BaseParser):
    """Parser CSV avec protection DoS"""

    # Limite de taille CSV (50 Mo)
    MAX_CSV_SIZE = 50 * 1024 * 1024
    # Limite de colonnes
    MAX_COLUMNS = 500
    # Limite de lignes par défaut
    MAX_ROWS = 1_000_000

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        # Vérification limite de taille
        if len(content) > self.MAX_CSV_SIZE:
            raise ValueError(f"Fichier CSV trop volumineux (max {self.MAX_CSV_SIZE // (1024*1024)} Mo)")
        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ";")
        quotechar = options.get("quotechar", '"')
        skip_rows = options.get("skip_rows", 0)
        has_header = options.get("has_header", True)

        try:
            text_content = content.decode(encoding)
        except UnicodeDecodeError:
            for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    text_content = content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Impossible de décoder le fichier")

        reader = csv.reader(
            io.StringIO(text_content),
            delimiter=delimiter,
            quotechar=quotechar
        )

        for _ in range(skip_rows):
            try:
                next(reader)
            except StopIteration:
                return

        headers = []
        if has_header:
            try:
                headers = [h.strip() for h in next(reader)]
                # Limite de colonnes
                if len(headers) > self.MAX_COLUMNS:
                    raise ValueError(f"Trop de colonnes ({len(headers)} > {self.MAX_COLUMNS})")
            except StopIteration:
                return

        row_count = 0
        for row_num, row in enumerate(reader, start=skip_rows + 2 if has_header else skip_rows + 1):
            row_count += 1
            if row_count > self.MAX_ROWS:
                logger.warning(f"Limite de lignes atteinte ({self.MAX_ROWS})")
                break
            if not any(row):
                continue

            if headers:
                record = {}
                for i, header in enumerate(headers):
                    record[header] = row[i] if i < len(row) else ""
            else:
                record = {f"col_{i}": val for i, val in enumerate(row)}

            record["__row_number__"] = row_num
            yield record

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ";")
        skip_rows = options.get("skip_rows", 0)

        try:
            text_content = content.decode(encoding)
        except UnicodeDecodeError:
            text_content = content.decode("latin-1")

        reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)

        for _ in range(skip_rows):
            try:
                next(reader)
            except StopIteration:
                return []

        try:
            return [h.strip() for h in next(reader)]
        except StopIteration:
            return []


class ExcelParser(BaseParser):
    """Parser Excel (xlsx)"""

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl requis pour parser Excel: pip install openpyxl")

        sheet_name = options.get("sheet_name")
        sheet_index = options.get("sheet_index", 0)
        skip_rows = options.get("skip_rows", 0)
        has_header = options.get("has_header", True)

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)

        if sheet_name:
            ws = wb[sheet_name]
        else:
            ws = wb.worksheets[sheet_index]

        rows = ws.iter_rows(values_only=True)

        for _ in range(skip_rows):
            try:
                next(rows)
            except StopIteration:
                wb.close()
                return

        headers = []
        if has_header:
            try:
                header_row = next(rows)
                headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(header_row)]
            except StopIteration:
                wb.close()
                return

        row_num = skip_rows + 2 if has_header else skip_rows + 1
        for row in rows:
            if not any(row):
                row_num += 1
                continue

            if headers:
                record = {}
                for i, header in enumerate(headers):
                    value = row[i] if i < len(row) else None
                    if isinstance(value, datetime):
                        record[header] = value.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(value, date):
                        record[header] = value.strftime("%Y-%m-%d")
                    else:
                        record[header] = value
            else:
                record = {f"col_{i}": val for i, val in enumerate(row)}

            record["__row_number__"] = row_num
            yield record
            row_num += 1

        wb.close()

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        try:
            import openpyxl
        except ImportError:
            return []

        sheet_index = options.get("sheet_index", 0)
        skip_rows = options.get("skip_rows", 0)

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.worksheets[sheet_index]

        rows = ws.iter_rows(values_only=True)
        for _ in range(skip_rows):
            try:
                next(rows)
            except StopIteration:
                wb.close()
                return []

        try:
            header_row = next(rows)
            headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(header_row)]
        except StopIteration:
            headers = []

        wb.close()
        return headers


class JSONParser(BaseParser):
    """Parser JSON avec protection DoS"""

    # Limite de taille JSON (50 Mo)
    MAX_JSON_SIZE = 50 * 1024 * 1024
    # Limite de profondeur de parsing
    MAX_DEPTH = 50

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        # Vérification limite de taille
        if len(content) > self.MAX_JSON_SIZE:
            raise ValueError(f"Fichier JSON trop volumineux (max {self.MAX_JSON_SIZE // (1024*1024)} Mo)")

        encoding = options.get("encoding", "utf-8")
        root_path = options.get("root_path")

        data = json.loads(content.decode(encoding))

        if root_path:
            for key in root_path.split("."):
                if isinstance(data, dict):
                    data = data.get(key, [])
                elif isinstance(data, list) and key.isdigit():
                    data = data[int(key)]

        if not isinstance(data, list):
            data = [data]

        for row_num, record in enumerate(data, start=1):
            if isinstance(record, dict):
                record["__row_number__"] = row_num
                yield record

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        encoding = options.get("encoding", "utf-8")
        root_path = options.get("root_path")

        data = json.loads(content.decode(encoding))

        if root_path:
            for key in root_path.split("."):
                if isinstance(data, dict):
                    data = data.get(key, [])

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return list(data[0].keys())
        elif isinstance(data, dict):
            return list(data.keys())
        return []


class XMLParser(BaseParser):
    """Parser XML avec protection XXE"""

    # Limite de taille XML (10 Mo)
    MAX_XML_SIZE = 10 * 1024 * 1024

    def _safe_parse_xml(self, xml_content: bytes) -> ET.Element:
        """Parse XML de manière sécurisée (protection XXE)"""
        import defusedxml.ElementTree as DefusedET

        # Limite de taille
        if len(xml_content) > self.MAX_XML_SIZE:
            raise ValueError(f"Fichier XML trop volumineux (max {self.MAX_XML_SIZE // (1024*1024)} Mo)")

        try:
            return DefusedET.fromstring(xml_content)
        except ImportError:
            # Fallback si defusedxml non installé: désactiver les entités
            logger.warning("defusedxml non installé - utilisation du parser sécurisé manuel")

            # Vérification basique anti-XXE
            xml_str = xml_content.decode("utf-8", errors="replace")
            dangerous_patterns = [
                "<!ENTITY", "<!DOCTYPE", "SYSTEM", "PUBLIC",
                "file://", "http://", "https://", "ftp://"
            ]
            xml_upper = xml_str.upper()
            for pattern in dangerous_patterns:
                if pattern.upper() in xml_upper:
                    raise ValueError(f"Contenu XML potentiellement dangereux détecté: {pattern}")

            return ET.fromstring(xml_content)

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        root_element = options.get("root_element", "record")
        encoding = options.get("encoding", "utf-8")

        try:
            xml_content = content if isinstance(content, bytes) else content.encode(encoding)
            root = self._safe_parse_xml(xml_content)
        except UnicodeDecodeError:
            root = self._safe_parse_xml(content)

        records = root.findall(f".//{root_element}")

        for row_num, elem in enumerate(records, start=1):
            record = self._element_to_dict(elem)
            record["__row_number__"] = row_num
            yield record

    def _element_to_dict(self, elem: ET.Element) -> dict:
        """Convertit un élément XML en dictionnaire"""
        result = {}

        result.update(elem.attrib)

        for child in elem:
            if len(child) > 0:
                result[child.tag] = self._element_to_dict(child)
            else:
                result[child.tag] = child.text

        if elem.text and elem.text.strip():
            if not result:
                return {"__text__": elem.text.strip()}
            result["__text__"] = elem.text.strip()

        return result

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        root_element = options.get("root_element", "record")

        try:
            root = self._safe_parse_xml(content)
        except (ET.ParseError, ValueError) as e:
            logger.warning(f"Erreur parsing XML headers: {e}")
            return []

        records = root.findall(f".//{root_element}")
        if records:
            first_record = self._element_to_dict(records[0])
            return list(first_record.keys())
        return []


class FECParser(BaseParser):
    """Parser FEC (Fichier des Écritures Comptables)"""

    FEC_COLUMNS = [
        "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
        "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
        "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit",
        "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
    ]

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        delimiter = options.get("delimiter", "\t")

        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                text_content = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Impossible de décoder le fichier FEC")

        reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)

        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            return

        for row_num, row in enumerate(reader, start=2):
            if not any(row):
                continue

            record = {}
            for i, header in enumerate(headers):
                record[header] = row[i] if i < len(row) else ""

            record["__row_number__"] = row_num
            yield record

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        return self.FEC_COLUMNS


# ============================================================================
# Exporters
# ============================================================================

class BaseExporter(ABC):
    """Classe de base pour les exporters"""

    @abstractmethod
    def export(self, data: list[dict], options: dict) -> bytes:
        """Exporte les données vers le format cible"""
        pass


class CSVExporter(BaseExporter):
    """Exporter CSV"""

    def export(self, data: list[dict], options: dict) -> bytes:
        if not data:
            return b""

        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ";")
        quotechar = options.get("quotechar", '"')
        include_bom = options.get("include_bom", False)
        columns = options.get("columns")

        output = io.StringIO()

        if columns:
            headers = columns
        else:
            headers = [k for k in data[0].keys() if not k.startswith("__")]

        writer = csv.DictWriter(
            output,
            fieldnames=headers,
            delimiter=delimiter,
            quotechar=quotechar,
            extrasaction="ignore"
        )

        writer.writeheader()

        for record in data:
            filtered_record = {k: v for k, v in record.items() if not k.startswith("__")}
            writer.writerow(filtered_record)

        content = output.getvalue()

        if include_bom and encoding.lower() in ("utf-8", "utf8"):
            return b'\xef\xbb\xbf' + content.encode(encoding)
        return content.encode(encoding)


class ExcelExporter(BaseExporter):
    """Exporter Excel (xlsx)"""

    def export(self, data: list[dict], options: dict) -> bytes:
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            raise ImportError("openpyxl requis pour export Excel")

        if not data:
            return b""

        sheet_name = options.get("sheet_name", "Export")
        columns = options.get("columns")
        style_header = options.get("style_header", True)
        auto_width = options.get("auto_width", True)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name

        if columns:
            headers = columns
        else:
            headers = [k for k in data[0].keys() if not k.startswith("__")]

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        for col_num, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_num, value=header)
            if style_header:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border

        for row_num, record in enumerate(data, start=2):
            for col_num, header in enumerate(headers, start=1):
                value = record.get(header)

                if isinstance(value, datetime):
                    cell = ws.cell(row=row_num, column=col_num, value=value)
                    cell.number_format = "DD/MM/YYYY HH:MM:SS"
                elif isinstance(value, date):
                    cell = ws.cell(row=row_num, column=col_num, value=value)
                    cell.number_format = "DD/MM/YYYY"
                elif isinstance(value, Decimal):
                    cell = ws.cell(row=row_num, column=col_num, value=float(value))
                    cell.number_format = "#,##0.00"
                else:
                    cell = ws.cell(row=row_num, column=col_num, value=value)

                cell.border = thin_border

        if auto_width:
            for col_num, header in enumerate(headers, start=1):
                max_length = len(str(header))
                for row in range(2, len(data) + 2):
                    cell_value = ws.cell(row=row, column=col_num).value
                    if cell_value:
                        max_length = max(max_length, len(str(cell_value)))
                ws.column_dimensions[get_column_letter(col_num)].width = min(max_length + 2, 50)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()


class JSONExporter(BaseExporter):
    """Exporter JSON"""

    def export(self, data: list[dict], options: dict) -> bytes:
        encoding = options.get("encoding", "utf-8")
        indent = options.get("indent", 2)
        root_key = options.get("root_key")
        date_format = options.get("date_format", "%Y-%m-%d")
        datetime_format = options.get("datetime_format", "%Y-%m-%dT%H:%M:%S")

        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.strftime(datetime_format)
            elif isinstance(obj, date):
                return obj.strftime(date_format)
            elif isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        filtered_data = []
        for record in data:
            filtered_record = {k: v for k, v in record.items() if not k.startswith("__")}
            filtered_data.append(filtered_record)

        if root_key:
            output_data = {root_key: filtered_data}
        else:
            output_data = filtered_data

        return json.dumps(
            output_data,
            ensure_ascii=False,
            indent=indent,
            default=json_serializer
        ).encode(encoding)


class XMLExporter(BaseExporter):
    """Exporter XML"""

    def export(self, data: list[dict], options: dict) -> bytes:
        encoding = options.get("encoding", "utf-8")
        root_element = options.get("root_element", "data")
        record_element = options.get("record_element", "record")
        pretty_print = options.get("pretty_print", True)

        root = ET.Element(root_element)

        for record in data:
            record_elem = ET.SubElement(root, record_element)

            for key, value in record.items():
                if key.startswith("__"):
                    continue

                field_elem = ET.SubElement(record_elem, self._sanitize_xml_tag(key))

                if isinstance(value, datetime):
                    field_elem.text = value.strftime("%Y-%m-%dT%H:%M:%S")
                elif isinstance(value, date):
                    field_elem.text = value.strftime("%Y-%m-%d")
                elif isinstance(value, Decimal):
                    field_elem.text = str(value)
                elif isinstance(value, dict):
                    self._dict_to_xml(value, field_elem)
                elif value is not None:
                    field_elem.text = str(value)

        if pretty_print:
            xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            xml_lines = xml_string.split("\n")[1:]
            return "\n".join(xml_lines).encode(encoding)

        return ET.tostring(root, encoding=encoding)

    def _sanitize_xml_tag(self, tag: str) -> str:
        """Nettoie un nom de tag XML"""
        import re
        tag = re.sub(r'[^a-zA-Z0-9_\-.]', '_', str(tag))
        if tag and tag[0].isdigit():
            tag = f"_{tag}"
        return tag or "field"

    def _dict_to_xml(self, d: dict, parent: ET.Element) -> None:
        """Convertit un dictionnaire en éléments XML"""
        for key, value in d.items():
            child = ET.SubElement(parent, self._sanitize_xml_tag(key))
            if isinstance(value, dict):
                self._dict_to_xml(value, child)
            elif value is not None:
                child.text = str(value)


class FECExporter(BaseExporter):
    """Exporter FEC (Fichier des Écritures Comptables)"""

    FEC_COLUMNS = [
        "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
        "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
        "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit",
        "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
    ]

    def export(self, data: list[dict], options: dict) -> bytes:
        encoding = options.get("encoding", "iso-8859-1")
        delimiter = "\t"
        siren = options.get("siren", "")
        fiscal_year_end = options.get("fiscal_year_end", "")

        if siren and fiscal_year_end:
            filename = f"{siren}FEC{fiscal_year_end}"
        else:
            filename = "FEC"

        output = io.StringIO()

        output.write(delimiter.join(self.FEC_COLUMNS) + "\n")

        for record in data:
            row = []
            for col in self.FEC_COLUMNS:
                value = record.get(col, "")

                if col in ("EcritureDate", "PieceDate", "DateLet", "ValidDate"):
                    if isinstance(value, (date, datetime)):
                        value = value.strftime("%Y%m%d")
                    elif value and isinstance(value, str):
                        for fmt in ["%Y-%m-%d", "%d/%m/%Y"]:
                            try:
                                value = datetime.strptime(value, fmt).strftime("%Y%m%d")
                                break
                            except ValueError:
                                continue

                if col in ("Debit", "Credit", "Montantdevise"):
                    if isinstance(value, (int, float, Decimal)):
                        value = f"{Decimal(str(value)):.2f}".replace(".", ",")
                    elif not value:
                        value = "0,00"

                row.append(str(value) if value is not None else "")

            output.write(delimiter.join(row) + "\n")

        return output.getvalue().encode(encoding)


# ============================================================================
# Service Principal
# ============================================================================

class DataImportExportService:
    """Service d'import/export de données"""

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
        """Exporte les données directement vers un fichier

        Args:
            data: Données à exporter
            format: Format d'export
            file_path: Chemin du fichier de sortie
            options: Options d'export
            allowed_base_path: Répertoire de base autorisé (protection path traversal)
        """
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

        # Vérification des caractères dangereux dans le nom de fichier
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

    # Limites pour la création d'archives
    MAX_ARCHIVE_FILES = 1000
    MAX_ARCHIVE_SIZE = 500 * 1024 * 1024  # 500 Mo
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 Mo par fichier

    def create_archive(
        self,
        exports: list[tuple[str, bytes]],
        archive_format: str = "zip"
    ) -> bytes:
        """Crée une archive contenant plusieurs exports (avec protections)"""
        if archive_format != "zip":
            raise ValueError(f"Format d'archive non supporté: {archive_format}")

        # Protection contre trop de fichiers
        if len(exports) > self.MAX_ARCHIVE_FILES:
            raise ValueError(f"Trop de fichiers ({len(exports)} > {self.MAX_ARCHIVE_FILES})")

        # Calcul de la taille totale
        total_size = sum(len(content) for _, content in exports)
        if total_size > self.MAX_ARCHIVE_SIZE:
            raise ValueError(
                f"Taille totale trop importante "
                f"({total_size // (1024*1024)} Mo > {self.MAX_ARCHIVE_SIZE // (1024*1024)} Mo)"
            )

        output = io.BytesIO()

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in exports:
                # Validation du nom de fichier
                if '..' in filename or filename.startswith('/'):
                    raise ValueError(f"Nom de fichier non autorisé: {filename}")

                # Limite par fichier
                if len(content) > self.MAX_FILE_SIZE:
                    raise ValueError(
                        f"Fichier trop volumineux: {filename} "
                        f"({len(content) // (1024*1024)} Mo > {self.MAX_FILE_SIZE // (1024*1024)} Mo)"
                    )

                zf.writestr(filename, content)

        return output.getvalue()


# ============================================================================
# Templates Prédéfinis
# ============================================================================

def get_fec_import_template() -> ImportTemplate:
    """Template d'import FEC"""
    return ImportTemplate(
        id="fec_import",
        name="Import FEC",
        description="Import du Fichier des Écritures Comptables (format légal)",
        format=ImportFormat.FEC,
        target_entity="accounting_entry",
        field_mappings=[
            FieldMapping(
                source_field="JournalCode",
                target_field="journal_code",
                data_type="string",
                required=True,
                validation_rules=[{"type": "length", "min": 1, "max": 10}]
            ),
            FieldMapping(
                source_field="JournalLib",
                target_field="journal_label",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="EcritureNum",
                target_field="entry_number",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="EcritureDate",
                target_field="entry_date",
                data_type="date",
                required=True,
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="CompteNum",
                target_field="account_number",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="CompteLib",
                target_field="account_label",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="CompAuxNum",
                target_field="auxiliary_account",
                data_type="string"
            ),
            FieldMapping(
                source_field="CompAuxLib",
                target_field="auxiliary_label",
                data_type="string"
            ),
            FieldMapping(
                source_field="PieceRef",
                target_field="document_reference",
                data_type="string"
            ),
            FieldMapping(
                source_field="PieceDate",
                target_field="document_date",
                data_type="date",
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="EcritureLib",
                target_field="entry_label",
                data_type="string"
            ),
            FieldMapping(
                source_field="Debit",
                target_field="debit",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ",",
                    "output_decimal": "."
                }]
            ),
            FieldMapping(
                source_field="Credit",
                target_field="credit",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ",",
                    "output_decimal": "."
                }]
            ),
            FieldMapping(
                source_field="EcritureLet",
                target_field="lettering",
                data_type="string"
            ),
            FieldMapping(
                source_field="DateLet",
                target_field="lettering_date",
                data_type="date",
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="ValidDate",
                target_field="validation_date",
                data_type="date",
                transformations=[{
                    "type": "date_format",
                    "input_format": "%Y%m%d",
                    "output_format": "%Y-%m-%d"
                }]
            ),
            FieldMapping(
                source_field="Montantdevise",
                target_field="currency_amount",
                data_type="decimal",
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ",",
                    "output_decimal": "."
                }]
            ),
            FieldMapping(
                source_field="Idevise",
                target_field="currency_code",
                data_type="string"
            ),
        ],
        options={
            "delimiter": "\t",
            "encoding": "utf-8"
        }
    )


def get_client_import_template() -> ImportTemplate:
    """Template d'import clients"""
    return ImportTemplate(
        id="client_import",
        name="Import Clients",
        description="Import de la base clients (CSV/Excel)",
        format=ImportFormat.CSV,
        target_entity="client",
        field_mappings=[
            FieldMapping(
                source_field="code_client",
                target_field="client_code",
                data_type="string",
                required=True,
                transformations=[{"type": "uppercase"}, {"type": "trim"}]
            ),
            FieldMapping(
                source_field="raison_sociale",
                target_field="company_name",
                data_type="string",
                required=True,
                transformations=[{"type": "trim"}]
            ),
            FieldMapping(
                source_field="siren",
                target_field="siren",
                data_type="siren",
                validation_rules=[{"type": "length", "min": 9, "max": 9}]
            ),
            FieldMapping(
                source_field="siret",
                target_field="siret",
                data_type="siret",
                validation_rules=[{"type": "length", "min": 14, "max": 14}]
            ),
            FieldMapping(
                source_field="tva_intra",
                target_field="vat_number",
                data_type="string",
                transformations=[{"type": "uppercase"}]
            ),
            FieldMapping(
                source_field="adresse",
                target_field="address_line1",
                data_type="string"
            ),
            FieldMapping(
                source_field="code_postal",
                target_field="postal_code",
                data_type="string"
            ),
            FieldMapping(
                source_field="ville",
                target_field="city",
                data_type="string",
                transformations=[{"type": "uppercase"}]
            ),
            FieldMapping(
                source_field="pays",
                target_field="country",
                data_type="string",
                default_value="FR"
            ),
            FieldMapping(
                source_field="telephone",
                target_field="phone",
                data_type="string"
            ),
            FieldMapping(
                source_field="email",
                target_field="email",
                data_type="email"
            ),
            FieldMapping(
                source_field="iban",
                target_field="iban",
                data_type="iban"
            ),
            FieldMapping(
                source_field="conditions_paiement",
                target_field="payment_terms_days",
                data_type="integer",
                default_value=30
            ),
        ],
        options={
            "delimiter": ";",
            "encoding": "utf-8",
            "has_header": True
        }
    )


def get_invoice_import_template() -> ImportTemplate:
    """Template d'import factures"""
    return ImportTemplate(
        id="invoice_import",
        name="Import Factures",
        description="Import des factures fournisseurs/clients",
        format=ImportFormat.CSV,
        target_entity="invoice",
        field_mappings=[
            FieldMapping(
                source_field="numero_facture",
                target_field="invoice_number",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="date_facture",
                target_field="invoice_date",
                data_type="date",
                required=True
            ),
            FieldMapping(
                source_field="date_echeance",
                target_field="due_date",
                data_type="date"
            ),
            FieldMapping(
                source_field="code_tiers",
                target_field="partner_code",
                data_type="string",
                required=True
            ),
            FieldMapping(
                source_field="type",
                target_field="invoice_type",
                data_type="string",
                required=True,
                validation_rules=[{
                    "type": "enum",
                    "values": ["FA", "AV", "FC", "AC"]
                }],
                transformations=[{
                    "type": "lookup",
                    "table": {"FA": "invoice", "AV": "credit_note", "FC": "supplier_invoice", "AC": "supplier_credit"}
                }]
            ),
            FieldMapping(
                source_field="montant_ht",
                target_field="amount_untaxed",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ","
                }]
            ),
            FieldMapping(
                source_field="montant_tva",
                target_field="tax_amount",
                data_type="decimal",
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ","
                }]
            ),
            FieldMapping(
                source_field="montant_ttc",
                target_field="amount_total",
                data_type="decimal",
                required=True,
                transformations=[{
                    "type": "number_format",
                    "input_decimal": ","
                }]
            ),
            FieldMapping(
                source_field="devise",
                target_field="currency",
                data_type="string",
                default_value="EUR"
            ),
            FieldMapping(
                source_field="reference",
                target_field="reference",
                data_type="string"
            ),
        ],
        options={
            "delimiter": ";",
            "encoding": "utf-8",
            "has_header": True
        }
    )


# ============================================================================
# Instance Globale
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
