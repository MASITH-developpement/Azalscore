"""
Service Import/Export de Données - GAP-048

Échange de données complet:
- Import CSV, Excel, JSON, XML
- Mapping de colonnes
- Validation et transformation
- Gestion des erreurs
- Export multi-format
- Planification
- Historique et audit
- Intégrations tierces
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4
import csv
import json
import io
import re


class ImportFormat(Enum):
    """Format d'import."""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    XML = "xml"
    FIXED_WIDTH = "fixed_width"


class ExportFormat(Enum):
    """Format d'export."""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    XML = "xml"
    PDF = "pdf"


class ImportStatus(Enum):
    """Statut d'import."""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportStatus(Enum):
    """Statut d'export."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FieldType(Enum):
    """Type de champ."""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    ENUM = "enum"
    REFERENCE = "reference"  # Clé étrangère


class ValidationAction(Enum):
    """Action sur erreur de validation."""
    REJECT = "reject"  # Rejeter la ligne
    SKIP = "skip"  # Ignorer le champ
    DEFAULT = "default"  # Utiliser valeur par défaut
    TRANSFORM = "transform"  # Transformer la valeur


class DuplicateAction(Enum):
    """Action sur doublon."""
    REJECT = "reject"
    SKIP = "skip"
    UPDATE = "update"
    CREATE_NEW = "create_new"


@dataclass
class FieldMapping:
    """Mapping d'un champ."""
    source_field: str  # Nom dans le fichier source
    target_field: str  # Nom dans le système
    field_type: FieldType = FieldType.STRING

    # Validation
    is_required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex
    allowed_values: List[Any] = field(default_factory=list)
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None

    # Transformation
    transformation: Optional[str] = None  # Expression de transformation
    default_value: Any = None
    trim: bool = True
    uppercase: bool = False
    lowercase: bool = False

    # Format
    date_format: str = "%d/%m/%Y"
    decimal_separator: str = ","
    thousands_separator: str = " "

    # Action sur erreur
    on_error: ValidationAction = ValidationAction.REJECT


@dataclass
class ImportProfile:
    """Profil d'import réutilisable."""
    profile_id: str
    tenant_id: str
    name: str
    description: str
    entity_type: str  # "customer", "product", "invoice", etc.
    format: ImportFormat

    # Mapping
    field_mappings: List[FieldMapping] = field(default_factory=list)

    # Options de fichier
    encoding: str = "utf-8"
    delimiter: str = ";"  # Pour CSV
    has_header: bool = True
    skip_rows: int = 0
    sheet_name: Optional[str] = None  # Pour Excel

    # Gestion des doublons
    unique_fields: List[str] = field(default_factory=list)
    duplicate_action: DuplicateAction = DuplicateAction.REJECT

    # Validation
    validate_before_import: bool = True
    stop_on_first_error: bool = False
    max_errors: int = 100

    # Post-traitement
    post_actions: List[Dict[str, Any]] = field(default_factory=list)

    # Métadonnées
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    last_used_at: Optional[datetime] = None


@dataclass
class ValidationError:
    """Erreur de validation."""
    row_number: int
    field_name: str
    field_value: Any
    error_type: str
    error_message: str
    severity: str = "error"  # error, warning


@dataclass
class ImportJob:
    """Job d'import."""
    job_id: str
    tenant_id: str
    profile_id: str
    status: ImportStatus

    # Fichier source
    file_name: str
    file_size: int = 0
    file_path: Optional[str] = None

    # Progression
    total_rows: int = 0
    processed_rows: int = 0
    imported_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    error_rows: int = 0

    # Erreurs
    validation_errors: List[ValidationError] = field(default_factory=list)
    system_error: Optional[str] = None

    # Résultats
    created_ids: List[str] = field(default_factory=list)
    updated_ids: List[str] = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Utilisateur
    created_by: str = ""

    # Options
    dry_run: bool = False  # Test sans import réel
    rollback_on_error: bool = True


@dataclass
class ExportProfile:
    """Profil d'export."""
    profile_id: str
    tenant_id: str
    name: str
    description: str
    entity_type: str
    format: ExportFormat

    # Champs à exporter
    fields: List[str] = field(default_factory=list)
    field_labels: Dict[str, str] = field(default_factory=dict)

    # Filtres par défaut
    default_filters: Dict[str, Any] = field(default_factory=dict)

    # Options de format
    encoding: str = "utf-8"
    delimiter: str = ";"
    include_header: bool = True

    # Format de date/nombre
    date_format: str = "%d/%m/%Y"
    datetime_format: str = "%d/%m/%Y %H:%M"
    decimal_separator: str = ","

    # Tri
    order_by: List[str] = field(default_factory=list)

    # Limites
    max_rows: Optional[int] = None

    # Template (pour PDF)
    template_id: Optional[str] = None

    # Métadonnées
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExportJob:
    """Job d'export."""
    job_id: str
    tenant_id: str
    profile_id: Optional[str]
    status: ExportStatus
    format: ExportFormat

    # Requête
    entity_type: str = ""
    filters: Dict[str, Any] = field(default_factory=dict)
    fields: List[str] = field(default_factory=list)

    # Résultat
    total_rows: int = 0
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: int = 0
    download_url: Optional[str] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Utilisateur
    created_by: str = ""

    # Erreur
    error_message: Optional[str] = None


@dataclass
class ScheduledExport:
    """Export planifié."""
    schedule_id: str
    tenant_id: str
    profile_id: str
    name: str

    # Planification
    schedule_cron: str
    timezone: str = "Europe/Paris"

    # Destination
    destination_type: str = "email"  # email, sftp, s3, webhook
    destination_config: Dict[str, Any] = field(default_factory=dict)

    # Filtres dynamiques
    dynamic_filters: Dict[str, str] = field(default_factory=dict)  # Ex: {"date": "last_month"}

    # État
    is_active: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_status: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


class DataExchangeService:
    """Service d'import/export de données."""

    def __init__(
        self,
        tenant_id: str,
        entity_repository: Optional[Any] = None,
        storage_service: Optional[Any] = None,
        notification_service: Optional[Any] = None,
        excel_handler: Optional[Callable] = None,
        xml_handler: Optional[Callable] = None,
        pdf_generator: Optional[Callable] = None
    ):
        self.tenant_id = tenant_id
        self.entity_repo = entity_repository or {}
        self.storage = storage_service
        self.notification = notification_service
        self.excel_handler = excel_handler
        self.xml_handler = xml_handler
        self.pdf_generator = pdf_generator

        # Caches
        self._import_profiles: Dict[str, ImportProfile] = {}
        self._export_profiles: Dict[str, ExportProfile] = {}
        self._import_jobs: Dict[str, ImportJob] = {}
        self._export_jobs: Dict[str, ExportJob] = {}
        self._scheduled_exports: Dict[str, ScheduledExport] = {}

        # Validateurs personnalisés
        self._validators: Dict[str, Callable] = {}

        # Transformateurs
        self._transformers: Dict[str, Callable] = {}

        # Handlers d'entités
        self._entity_handlers: Dict[str, Dict[str, Callable]] = {}

    # =========================================================================
    # Profils d'Import
    # =========================================================================

    def create_import_profile(
        self,
        name: str,
        description: str,
        entity_type: str,
        format: ImportFormat,
        field_mappings: List[Dict[str, Any]],
        **kwargs
    ) -> ImportProfile:
        """Crée un profil d'import."""
        profile_id = f"imp_{uuid4().hex[:12]}"

        # Construire les mappings
        mappings = []
        for mapping_data in field_mappings:
            mapping = FieldMapping(
                source_field=mapping_data["source"],
                target_field=mapping_data["target"],
                field_type=FieldType(mapping_data.get("type", "string")),
                is_required=mapping_data.get("required", False),
                min_length=mapping_data.get("min_length"),
                max_length=mapping_data.get("max_length"),
                pattern=mapping_data.get("pattern"),
                allowed_values=mapping_data.get("allowed_values", []),
                min_value=Decimal(str(mapping_data["min_value"])) if mapping_data.get("min_value") else None,
                max_value=Decimal(str(mapping_data["max_value"])) if mapping_data.get("max_value") else None,
                transformation=mapping_data.get("transformation"),
                default_value=mapping_data.get("default"),
                trim=mapping_data.get("trim", True),
                uppercase=mapping_data.get("uppercase", False),
                lowercase=mapping_data.get("lowercase", False),
                date_format=mapping_data.get("date_format", "%d/%m/%Y"),
                decimal_separator=mapping_data.get("decimal_separator", ","),
                on_error=ValidationAction(mapping_data.get("on_error", "reject"))
            )
            mappings.append(mapping)

        profile = ImportProfile(
            profile_id=profile_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            entity_type=entity_type,
            format=format,
            field_mappings=mappings,
            encoding=kwargs.get("encoding", "utf-8"),
            delimiter=kwargs.get("delimiter", ";"),
            has_header=kwargs.get("has_header", True),
            skip_rows=kwargs.get("skip_rows", 0),
            sheet_name=kwargs.get("sheet_name"),
            unique_fields=kwargs.get("unique_fields", []),
            duplicate_action=DuplicateAction(kwargs.get("duplicate_action", "reject")),
            validate_before_import=kwargs.get("validate_before_import", True),
            stop_on_first_error=kwargs.get("stop_on_first_error", False),
            max_errors=kwargs.get("max_errors", 100),
            post_actions=kwargs.get("post_actions", []),
            created_by=kwargs.get("created_by", "system")
        )

        self._import_profiles[profile_id] = profile
        return profile

    # =========================================================================
    # Import de Données
    # =========================================================================

    def import_data(
        self,
        profile_id: str,
        file_content: bytes,
        file_name: str,
        **kwargs
    ) -> ImportJob:
        """Lance un import de données."""
        profile = self._import_profiles.get(profile_id)
        if not profile:
            raise ValueError(f"Profil {profile_id} non trouvé")

        job_id = f"job_{uuid4().hex[:12]}"

        job = ImportJob(
            job_id=job_id,
            tenant_id=self.tenant_id,
            profile_id=profile_id,
            status=ImportStatus.PENDING,
            file_name=file_name,
            file_size=len(file_content),
            created_by=kwargs.get("created_by", "system"),
            dry_run=kwargs.get("dry_run", False),
            rollback_on_error=kwargs.get("rollback_on_error", True)
        )

        self._import_jobs[job_id] = job

        # Parser le fichier
        try:
            rows = self._parse_file(file_content, profile)
            job.total_rows = len(rows)
        except Exception as e:
            job.status = ImportStatus.FAILED
            job.system_error = str(e)
            return job

        # Phase de validation
        job.status = ImportStatus.VALIDATING
        job.started_at = datetime.now()

        if profile.validate_before_import:
            job.validation_errors = self._validate_rows(rows, profile, job)

            if job.validation_errors and profile.stop_on_first_error:
                job.status = ImportStatus.FAILED
                return job

        # Phase d'import
        job.status = ImportStatus.PROCESSING

        try:
            self._process_import(rows, profile, job)
        except Exception as e:
            job.status = ImportStatus.FAILED
            job.system_error = str(e)
            return job

        # Finalisation
        job.completed_at = datetime.now()
        if job.error_rows > 0:
            job.status = ImportStatus.COMPLETED_WITH_ERRORS
        else:
            job.status = ImportStatus.COMPLETED

        # Mettre à jour le profil
        profile.last_used_at = datetime.now()

        return job

    def _parse_file(
        self,
        content: bytes,
        profile: ImportProfile
    ) -> List[Dict[str, Any]]:
        """Parse un fichier selon son format."""
        if profile.format == ImportFormat.CSV:
            return self._parse_csv(content, profile)
        elif profile.format == ImportFormat.EXCEL:
            return self._parse_excel(content, profile)
        elif profile.format == ImportFormat.JSON:
            return self._parse_json(content, profile)
        elif profile.format == ImportFormat.XML:
            return self._parse_xml(content, profile)
        else:
            raise ValueError(f"Format non supporté: {profile.format}")

    def _parse_csv(
        self,
        content: bytes,
        profile: ImportProfile
    ) -> List[Dict[str, Any]]:
        """Parse un fichier CSV."""
        text = content.decode(profile.encoding)
        reader = csv.DictReader(
            io.StringIO(text),
            delimiter=profile.delimiter
        )

        rows = []
        for i, row in enumerate(reader):
            if i < profile.skip_rows:
                continue
            rows.append(dict(row))

        return rows

    def _parse_excel(
        self,
        content: bytes,
        profile: ImportProfile
    ) -> List[Dict[str, Any]]:
        """Parse un fichier Excel."""
        if not self.excel_handler:
            raise ValueError("Handler Excel non configuré")

        return self.excel_handler(
            content,
            sheet_name=profile.sheet_name,
            skip_rows=profile.skip_rows,
            has_header=profile.has_header
        )

    def _parse_json(
        self,
        content: bytes,
        profile: ImportProfile
    ) -> List[Dict[str, Any]]:
        """Parse un fichier JSON."""
        text = content.decode(profile.encoding)
        data = json.loads(text)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Chercher un tableau dans les clés communes
            for key in ["data", "items", "records", "rows"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]

        return []

    def _parse_xml(
        self,
        content: bytes,
        profile: ImportProfile
    ) -> List[Dict[str, Any]]:
        """Parse un fichier XML."""
        if not self.xml_handler:
            raise ValueError("Handler XML non configuré")

        return self.xml_handler(content)

    def _validate_rows(
        self,
        rows: List[Dict[str, Any]],
        profile: ImportProfile,
        job: ImportJob
    ) -> List[ValidationError]:
        """Valide toutes les lignes."""
        errors = []

        for i, row in enumerate(rows):
            row_number = i + 1 + profile.skip_rows + (1 if profile.has_header else 0)

            for mapping in profile.field_mappings:
                value = row.get(mapping.source_field)

                # Valider le champ
                field_errors = self._validate_field(value, mapping, row_number)
                errors.extend(field_errors)

                if len(errors) >= profile.max_errors:
                    return errors

        return errors

    def _validate_field(
        self,
        value: Any,
        mapping: FieldMapping,
        row_number: int
    ) -> List[ValidationError]:
        """Valide un champ."""
        errors = []
        field_name = mapping.source_field

        # Nettoyage
        if mapping.trim and isinstance(value, str):
            value = value.strip()

        # Requis
        if mapping.is_required and (value is None or value == ""):
            errors.append(ValidationError(
                row_number=row_number,
                field_name=field_name,
                field_value=value,
                error_type="required",
                error_message=f"Le champ '{field_name}' est requis"
            ))
            return errors

        if value is None or value == "":
            return errors

        # Longueur
        if mapping.min_length and len(str(value)) < mapping.min_length:
            errors.append(ValidationError(
                row_number=row_number,
                field_name=field_name,
                field_value=value,
                error_type="min_length",
                error_message=f"Longueur minimale: {mapping.min_length}"
            ))

        if mapping.max_length and len(str(value)) > mapping.max_length:
            errors.append(ValidationError(
                row_number=row_number,
                field_name=field_name,
                field_value=value,
                error_type="max_length",
                error_message=f"Longueur maximale: {mapping.max_length}"
            ))

        # Pattern
        if mapping.pattern:
            if not re.match(mapping.pattern, str(value)):
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=field_name,
                    field_value=value,
                    error_type="pattern",
                    error_message=f"Format invalide"
                ))

        # Valeurs autorisées
        if mapping.allowed_values and value not in mapping.allowed_values:
            errors.append(ValidationError(
                row_number=row_number,
                field_name=field_name,
                field_value=value,
                error_type="allowed_values",
                error_message=f"Valeur non autorisée. Valeurs acceptées: {mapping.allowed_values}"
            ))

        # Type spécifique
        type_error = self._validate_type(value, mapping)
        if type_error:
            errors.append(ValidationError(
                row_number=row_number,
                field_name=field_name,
                field_value=value,
                error_type="type",
                error_message=type_error
            ))

        # Plage de valeurs
        if mapping.field_type in (FieldType.INTEGER, FieldType.DECIMAL):
            try:
                num_value = Decimal(str(value).replace(mapping.decimal_separator, "."))
                if mapping.min_value and num_value < mapping.min_value:
                    errors.append(ValidationError(
                        row_number=row_number,
                        field_name=field_name,
                        field_value=value,
                        error_type="min_value",
                        error_message=f"Valeur minimale: {mapping.min_value}"
                    ))
                if mapping.max_value and num_value > mapping.max_value:
                    errors.append(ValidationError(
                        row_number=row_number,
                        field_name=field_name,
                        field_value=value,
                        error_type="max_value",
                        error_message=f"Valeur maximale: {mapping.max_value}"
                    ))
            except (InvalidOperation, ValueError):
                pass

        return errors

    def _validate_type(self, value: Any, mapping: FieldMapping) -> Optional[str]:
        """Valide le type d'une valeur."""
        if mapping.field_type == FieldType.INTEGER:
            try:
                int(str(value).replace(mapping.thousands_separator, ""))
            except ValueError:
                return "Entier attendu"

        elif mapping.field_type == FieldType.DECIMAL:
            try:
                Decimal(str(value).replace(mapping.decimal_separator, ".").replace(mapping.thousands_separator, ""))
            except InvalidOperation:
                return "Nombre décimal attendu"

        elif mapping.field_type == FieldType.DATE:
            try:
                datetime.strptime(str(value), mapping.date_format)
            except ValueError:
                return f"Date attendue au format {mapping.date_format}"

        elif mapping.field_type == FieldType.EMAIL:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                return "Email invalide"

        elif mapping.field_type == FieldType.PHONE:
            # Format français simplifié
            phone_pattern = r'^(\+33|0)[1-9][0-9]{8}$'
            cleaned = re.sub(r'[\s.-]', '', str(value))
            if not re.match(phone_pattern, cleaned):
                return "Numéro de téléphone invalide"

        elif mapping.field_type == FieldType.BOOLEAN:
            valid_true = ['true', '1', 'yes', 'oui', 'o', 'y']
            valid_false = ['false', '0', 'no', 'non', 'n']
            if str(value).lower() not in valid_true + valid_false:
                return "Booléen attendu"

        return None

    def _process_import(
        self,
        rows: List[Dict[str, Any]],
        profile: ImportProfile,
        job: ImportJob
    ):
        """Traite l'import des données."""
        handler = self._entity_handlers.get(profile.entity_type)

        for i, row in enumerate(rows):
            job.processed_rows += 1

            try:
                # Transformer les données
                transformed = self._transform_row(row, profile)

                # Vérifier les doublons
                duplicate_id = self._check_duplicate(transformed, profile)

                if duplicate_id:
                    if profile.duplicate_action == DuplicateAction.REJECT:
                        job.validation_errors.append(ValidationError(
                            row_number=i + 1,
                            field_name="_duplicate",
                            field_value=str(transformed),
                            error_type="duplicate",
                            error_message="Enregistrement en doublon"
                        ))
                        job.error_rows += 1
                        continue

                    elif profile.duplicate_action == DuplicateAction.SKIP:
                        job.skipped_rows += 1
                        continue

                    elif profile.duplicate_action == DuplicateAction.UPDATE:
                        if not job.dry_run and handler:
                            handler["update"](duplicate_id, transformed)
                        job.updated_rows += 1
                        job.updated_ids.append(duplicate_id)
                        continue

                # Créer l'enregistrement
                if not job.dry_run:
                    if handler:
                        new_id = handler["create"](transformed)
                    else:
                        new_id = f"new_{uuid4().hex[:8]}"

                    job.created_ids.append(new_id)

                job.imported_rows += 1

            except Exception as e:
                job.error_rows += 1
                job.validation_errors.append(ValidationError(
                    row_number=i + 1,
                    field_name="_system",
                    field_value=str(row),
                    error_type="system_error",
                    error_message=str(e)
                ))

    def _transform_row(
        self,
        row: Dict[str, Any],
        profile: ImportProfile
    ) -> Dict[str, Any]:
        """Transforme une ligne selon les mappings."""
        result = {}

        for mapping in profile.field_mappings:
            source_value = row.get(mapping.source_field)

            # Valeur par défaut
            if source_value is None or source_value == "":
                if mapping.default_value is not None:
                    result[mapping.target_field] = mapping.default_value
                continue

            # Nettoyage
            if mapping.trim and isinstance(source_value, str):
                source_value = source_value.strip()

            if mapping.uppercase and isinstance(source_value, str):
                source_value = source_value.upper()

            if mapping.lowercase and isinstance(source_value, str):
                source_value = source_value.lower()

            # Conversion de type
            if mapping.field_type == FieldType.INTEGER:
                source_value = int(str(source_value).replace(mapping.thousands_separator, ""))

            elif mapping.field_type == FieldType.DECIMAL:
                source_value = Decimal(
                    str(source_value)
                    .replace(mapping.thousands_separator, "")
                    .replace(mapping.decimal_separator, ".")
                )

            elif mapping.field_type == FieldType.DATE:
                source_value = datetime.strptime(str(source_value), mapping.date_format).date()

            elif mapping.field_type == FieldType.DATETIME:
                source_value = datetime.strptime(str(source_value), mapping.date_format)

            elif mapping.field_type == FieldType.BOOLEAN:
                source_value = str(source_value).lower() in ['true', '1', 'yes', 'oui', 'o', 'y']

            # Transformation personnalisée
            if mapping.transformation:
                transformer = self._transformers.get(mapping.transformation)
                if transformer:
                    source_value = transformer(source_value, row)

            result[mapping.target_field] = source_value

        return result

    def _check_duplicate(
        self,
        data: Dict[str, Any],
        profile: ImportProfile
    ) -> Optional[str]:
        """Vérifie si un enregistrement existe déjà."""
        if not profile.unique_fields:
            return None

        handler = self._entity_handlers.get(profile.entity_type)
        if not handler or "find" not in handler:
            return None

        # Construire les critères de recherche
        criteria = {
            field: data.get(field)
            for field in profile.unique_fields
            if data.get(field) is not None
        }

        if not criteria:
            return None

        return handler["find"](criteria)

    def register_entity_handler(
        self,
        entity_type: str,
        create_fn: Callable,
        update_fn: Callable,
        find_fn: Callable
    ):
        """Enregistre les handlers pour un type d'entité."""
        self._entity_handlers[entity_type] = {
            "create": create_fn,
            "update": update_fn,
            "find": find_fn
        }

    def register_transformer(self, name: str, fn: Callable):
        """Enregistre un transformateur personnalisé."""
        self._transformers[name] = fn

    # =========================================================================
    # Export de Données
    # =========================================================================

    def create_export_profile(
        self,
        name: str,
        description: str,
        entity_type: str,
        format: ExportFormat,
        fields: List[str],
        **kwargs
    ) -> ExportProfile:
        """Crée un profil d'export."""
        profile_id = f"exp_{uuid4().hex[:12]}"

        profile = ExportProfile(
            profile_id=profile_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            entity_type=entity_type,
            format=format,
            fields=fields,
            field_labels=kwargs.get("field_labels", {}),
            default_filters=kwargs.get("default_filters", {}),
            encoding=kwargs.get("encoding", "utf-8"),
            delimiter=kwargs.get("delimiter", ";"),
            include_header=kwargs.get("include_header", True),
            date_format=kwargs.get("date_format", "%d/%m/%Y"),
            datetime_format=kwargs.get("datetime_format", "%d/%m/%Y %H:%M"),
            decimal_separator=kwargs.get("decimal_separator", ","),
            order_by=kwargs.get("order_by", []),
            max_rows=kwargs.get("max_rows"),
            template_id=kwargs.get("template_id")
        )

        self._export_profiles[profile_id] = profile
        return profile

    def export_data(
        self,
        profile_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        format: Optional[ExportFormat] = None,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        **kwargs
    ) -> ExportJob:
        """Exporte des données."""
        # Utiliser un profil ou des paramètres ad-hoc
        if profile_id:
            profile = self._export_profiles.get(profile_id)
            if not profile:
                raise ValueError(f"Profil {profile_id} non trouvé")
            entity_type = profile.entity_type
            format = profile.format
            fields = fields or profile.fields
            filters = {**profile.default_filters, **(filters or {})}
        else:
            if not entity_type or not format:
                raise ValueError("entity_type et format requis")
            profile = None

        job_id = f"export_{uuid4().hex[:12]}"

        job = ExportJob(
            job_id=job_id,
            tenant_id=self.tenant_id,
            profile_id=profile_id,
            status=ExportStatus.PROCESSING,
            format=format,
            entity_type=entity_type,
            filters=filters or {},
            fields=fields or [],
            created_by=kwargs.get("created_by", "system")
        )

        self._export_jobs[job_id] = job

        try:
            # Récupérer les données
            data = self._fetch_export_data(entity_type, filters, fields, profile)
            job.total_rows = len(data)

            # Générer le fichier
            content, file_name = self._generate_export_file(data, format, profile, fields)

            # Stocker
            if self.storage:
                file_path = f"/exports/{self.tenant_id}/{file_name}"
                self.storage.write(file_path, content)
                job.file_path = file_path
                job.download_url = f"/api/exports/{job_id}/download"

            job.file_name = file_name
            job.file_size = len(content)
            job.status = ExportStatus.COMPLETED
            job.completed_at = datetime.now()
            job.expires_at = datetime.now() + timedelta(days=7)

        except Exception as e:
            job.status = ExportStatus.FAILED
            job.error_message = str(e)

        return job

    def _fetch_export_data(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]],
        fields: Optional[List[str]],
        profile: Optional[ExportProfile]
    ) -> List[Dict[str, Any]]:
        """Récupère les données à exporter."""
        handler = self._entity_handlers.get(entity_type)
        if handler and "list" in handler:
            return handler["list"](filters=filters, fields=fields)

        # Fallback: chercher dans le repo générique
        if self.entity_repo:
            return list(self.entity_repo.get(entity_type, []))

        return []

    def _generate_export_file(
        self,
        data: List[Dict[str, Any]],
        format: ExportFormat,
        profile: Optional[ExportProfile],
        fields: Optional[List[str]]
    ) -> Tuple[bytes, str]:
        """Génère le fichier d'export."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == ExportFormat.CSV:
            content = self._generate_csv(data, profile, fields)
            return content.encode(profile.encoding if profile else "utf-8"), f"export_{timestamp}.csv"

        elif format == ExportFormat.JSON:
            content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            return content.encode("utf-8"), f"export_{timestamp}.json"

        elif format == ExportFormat.EXCEL:
            if self.excel_handler:
                content = self.excel_handler(data, fields, profile)
                return content, f"export_{timestamp}.xlsx"
            raise ValueError("Handler Excel non configuré")

        elif format == ExportFormat.PDF:
            if self.pdf_generator:
                content = self.pdf_generator(data, profile)
                return content, f"export_{timestamp}.pdf"
            raise ValueError("Générateur PDF non configuré")

        raise ValueError(f"Format non supporté: {format}")

    def _generate_csv(
        self,
        data: List[Dict[str, Any]],
        profile: Optional[ExportProfile],
        fields: Optional[List[str]]
    ) -> str:
        """Génère un CSV."""
        if not data:
            return ""

        output = io.StringIO()
        delimiter = profile.delimiter if profile else ";"

        # Déterminer les colonnes
        if fields:
            columns = fields
        elif profile and profile.fields:
            columns = profile.fields
        else:
            columns = list(data[0].keys())

        # Labels
        labels = {}
        if profile:
            labels = profile.field_labels

        writer = csv.writer(output, delimiter=delimiter)

        # En-tête
        if not profile or profile.include_header:
            header = [labels.get(col, col) for col in columns]
            writer.writerow(header)

        # Données
        for row in data:
            values = []
            for col in columns:
                value = row.get(col, "")

                # Formater selon le type
                if isinstance(value, datetime):
                    fmt = profile.datetime_format if profile else "%d/%m/%Y %H:%M"
                    value = value.strftime(fmt)
                elif isinstance(value, date):
                    fmt = profile.date_format if profile else "%d/%m/%Y"
                    value = value.strftime(fmt)
                elif isinstance(value, Decimal):
                    sep = profile.decimal_separator if profile else ","
                    value = str(value).replace(".", sep)
                elif value is None:
                    value = ""

                values.append(value)

            writer.writerow(values)

        return output.getvalue()

    # =========================================================================
    # Exports Planifiés
    # =========================================================================

    def schedule_export(
        self,
        profile_id: str,
        name: str,
        schedule_cron: str,
        destination_type: str,
        destination_config: Dict[str, Any],
        **kwargs
    ) -> ScheduledExport:
        """Planifie un export."""
        profile = self._export_profiles.get(profile_id)
        if not profile:
            raise ValueError(f"Profil {profile_id} non trouvé")

        schedule_id = f"sched_{uuid4().hex[:12]}"

        scheduled = ScheduledExport(
            schedule_id=schedule_id,
            tenant_id=self.tenant_id,
            profile_id=profile_id,
            name=name,
            schedule_cron=schedule_cron,
            timezone=kwargs.get("timezone", "Europe/Paris"),
            destination_type=destination_type,
            destination_config=destination_config,
            dynamic_filters=kwargs.get("dynamic_filters", {}),
            created_by=kwargs.get("created_by", "system")
        )

        # Calculer la prochaine exécution
        scheduled.next_run_at = self._calculate_next_run(schedule_cron)

        self._scheduled_exports[schedule_id] = scheduled
        return scheduled

    def _calculate_next_run(self, cron: str) -> datetime:
        """Calcule la prochaine exécution."""
        # Simplification - à implémenter avec croniter
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=6, minute=0, second=0, microsecond=0)

    def execute_scheduled_export(self, schedule_id: str) -> ExportJob:
        """Exécute un export planifié."""
        scheduled = self._scheduled_exports.get(schedule_id)
        if not scheduled:
            raise ValueError(f"Export planifié {schedule_id} non trouvé")

        # Résoudre les filtres dynamiques
        filters = self._resolve_dynamic_filters(scheduled.dynamic_filters)

        # Exécuter l'export
        job = self.export_data(
            profile_id=scheduled.profile_id,
            filters=filters
        )

        # Envoyer à la destination
        if job.status == ExportStatus.COMPLETED:
            self._send_to_destination(job, scheduled)

        # Mettre à jour le planning
        scheduled.last_run_at = datetime.now()
        scheduled.last_status = job.status.value
        scheduled.next_run_at = self._calculate_next_run(scheduled.schedule_cron)

        return job

    def _resolve_dynamic_filters(
        self,
        dynamic_filters: Dict[str, str]
    ) -> Dict[str, Any]:
        """Résout les filtres dynamiques."""
        resolved = {}
        now = datetime.now()

        for field, expression in dynamic_filters.items():
            if expression == "today":
                resolved[field] = now.date()
            elif expression == "yesterday":
                resolved[field] = (now - timedelta(days=1)).date()
            elif expression == "last_week":
                resolved[f"{field}_start"] = (now - timedelta(weeks=1)).date()
                resolved[f"{field}_end"] = now.date()
            elif expression == "last_month":
                first_of_month = now.replace(day=1)
                last_month_end = first_of_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                resolved[f"{field}_start"] = last_month_start.date()
                resolved[f"{field}_end"] = last_month_end.date()
            elif expression == "this_month":
                resolved[f"{field}_start"] = now.replace(day=1).date()
                resolved[f"{field}_end"] = now.date()
            else:
                resolved[field] = expression

        return resolved

    def _send_to_destination(
        self,
        job: ExportJob,
        scheduled: ScheduledExport
    ):
        """Envoie le fichier à la destination."""
        if scheduled.destination_type == "email":
            if self.notification:
                self.notification.send(
                    "export_ready",
                    email=scheduled.destination_config.get("email"),
                    variables={
                        "export_name": scheduled.name,
                        "download_url": job.download_url
                    }
                )

        # Autres destinations (SFTP, S3, webhook) à implémenter

    # =========================================================================
    # Récupération
    # =========================================================================

    def get_import_job(self, job_id: str) -> Optional[ImportJob]:
        """Récupère un job d'import."""
        return self._import_jobs.get(job_id)

    def get_export_job(self, job_id: str) -> Optional[ExportJob]:
        """Récupère un job d'export."""
        return self._export_jobs.get(job_id)

    def list_import_profiles(self) -> List[ImportProfile]:
        """Liste les profils d'import."""
        return [
            p for p in self._import_profiles.values()
            if p.tenant_id == self.tenant_id and p.is_active
        ]

    def list_export_profiles(self) -> List[ExportProfile]:
        """Liste les profils d'export."""
        return [
            p for p in self._export_profiles.values()
            if p.tenant_id == self.tenant_id and p.is_active
        ]

    def list_import_jobs(
        self,
        status: Optional[ImportStatus] = None,
        limit: int = 50
    ) -> List[ImportJob]:
        """Liste les jobs d'import."""
        jobs = [
            j for j in self._import_jobs.values()
            if j.tenant_id == self.tenant_id
        ]

        if status:
            jobs = [j for j in jobs if j.status == status]

        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def download_export(self, job_id: str) -> bytes:
        """Télécharge un fichier d'export."""
        job = self._export_jobs.get(job_id)
        if not job:
            raise ValueError(f"Export {job_id} non trouvé")

        if job.status != ExportStatus.COMPLETED:
            raise ValueError(f"Export non terminé: {job.status}")

        if job.expires_at and datetime.now() > job.expires_at:
            raise ValueError("Export expiré")

        if self.storage and job.file_path:
            return self.storage.read(job.file_path)

        raise ValueError("Fichier non disponible")


def create_dataexchange_service(
    tenant_id: str,
    **kwargs
) -> DataExchangeService:
    """Factory pour créer un service d'échange de données."""
    return DataExchangeService(tenant_id=tenant_id, **kwargs)
