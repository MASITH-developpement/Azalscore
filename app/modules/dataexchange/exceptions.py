"""
AZALS - Module DataExchange - Exceptions
========================================
Exceptions specifiques au module d'import/export de donnees.
"""
from typing import Optional, Dict, Any, List


class DataExchangeError(Exception):
    """Exception de base pour le module DataExchange."""

    def __init__(
        self,
        message: str,
        code: str = "DATAEXCHANGE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ============== Profile Errors ==============

class ProfileNotFoundError(DataExchangeError):
    """Profil d'import/export non trouve."""

    def __init__(self, profile_id: str):
        super().__init__(
            message=f"Profil d'import/export non trouve: {profile_id}",
            code="PROFILE_NOT_FOUND",
            details={"profile_id": str(profile_id)}
        )


class ProfileDuplicateCodeError(DataExchangeError):
    """Code de profil deja existant."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Un profil avec le code '{code}' existe deja",
            code="PROFILE_DUPLICATE_CODE",
            details={"code": code}
        )


class ProfileInUseError(DataExchangeError):
    """Profil utilise par des echanges planifies ou jobs."""

    def __init__(self, profile_id: str, usage_count: int):
        super().__init__(
            message=f"Le profil est utilise par {usage_count} element(s) et ne peut pas etre supprime",
            code="PROFILE_IN_USE",
            details={"profile_id": str(profile_id), "usage_count": usage_count}
        )


class SystemProfileError(DataExchangeError):
    """Operation interdite sur un profil systeme."""

    def __init__(self, profile_id: str, operation: str):
        super().__init__(
            message=f"Operation '{operation}' interdite sur un profil systeme",
            code="SYSTEM_PROFILE_ERROR",
            details={"profile_id": str(profile_id), "operation": operation}
        )


# ============== Connector Errors ==============

class ConnectorNotFoundError(DataExchangeError):
    """Connecteur de fichiers non trouve."""

    def __init__(self, connector_id: str):
        super().__init__(
            message=f"Connecteur non trouve: {connector_id}",
            code="CONNECTOR_NOT_FOUND",
            details={"connector_id": str(connector_id)}
        )


class ConnectorDuplicateCodeError(DataExchangeError):
    """Code de connecteur deja existant."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Un connecteur avec le code '{code}' existe deja",
            code="CONNECTOR_DUPLICATE_CODE",
            details={"code": code}
        )


class ConnectorConnectionError(DataExchangeError):
    """Erreur de connexion au connecteur."""

    def __init__(self, connector_id: str, error: str):
        super().__init__(
            message=f"Erreur de connexion au connecteur: {error}",
            code="CONNECTOR_CONNECTION_ERROR",
            details={"connector_id": str(connector_id), "error": error}
        )


class ConnectorAuthenticationError(DataExchangeError):
    """Erreur d'authentification au connecteur."""

    def __init__(self, connector_id: str):
        super().__init__(
            message="Erreur d'authentification au connecteur",
            code="CONNECTOR_AUTH_ERROR",
            details={"connector_id": str(connector_id)}
        )


class ConnectorInUseError(DataExchangeError):
    """Connecteur utilise par des echanges planifies."""

    def __init__(self, connector_id: str, usage_count: int):
        super().__init__(
            message=f"Le connecteur est utilise par {usage_count} element(s)",
            code="CONNECTOR_IN_USE",
            details={"connector_id": str(connector_id), "usage_count": usage_count}
        )


# ============== Schedule Errors ==============

class ScheduledExchangeNotFoundError(DataExchangeError):
    """Echange planifie non trouve."""

    def __init__(self, schedule_id: str):
        super().__init__(
            message=f"Echange planifie non trouve: {schedule_id}",
            code="SCHEDULED_NOT_FOUND",
            details={"schedule_id": str(schedule_id)}
        )


class ScheduledExchangeDuplicateCodeError(DataExchangeError):
    """Code d'echange planifie deja existant."""

    def __init__(self, code: str):
        super().__init__(
            message=f"Un echange planifie avec le code '{code}' existe deja",
            code="SCHEDULED_DUPLICATE_CODE",
            details={"code": code}
        )


class InvalidCronExpressionError(DataExchangeError):
    """Expression cron invalide."""

    def __init__(self, expression: str):
        super().__init__(
            message=f"Expression cron invalide: {expression}",
            code="INVALID_CRON_EXPRESSION",
            details={"expression": expression}
        )


# ============== Job Errors ==============

class JobNotFoundError(DataExchangeError):
    """Job d'echange non trouve."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job d'echange non trouve: {job_id}",
            code="JOB_NOT_FOUND",
            details={"job_id": str(job_id)}
        )


class JobAlreadyRunningError(DataExchangeError):
    """Un job est deja en cours d'execution."""

    def __init__(self, job_id: str):
        super().__init__(
            message="Un job est deja en cours d'execution",
            code="JOB_ALREADY_RUNNING",
            details={"job_id": str(job_id)}
        )


class JobCannotBeCancelledError(DataExchangeError):
    """Le job ne peut pas etre annule."""

    def __init__(self, job_id: str, status: str):
        super().__init__(
            message=f"Le job ne peut pas etre annule (statut: {status})",
            code="JOB_CANNOT_CANCEL",
            details={"job_id": str(job_id), "status": status}
        )


class JobCannotBeRolledBackError(DataExchangeError):
    """Le job ne peut pas etre rollback."""

    def __init__(self, job_id: str, reason: str):
        super().__init__(
            message=f"Le job ne peut pas etre rollback: {reason}",
            code="JOB_CANNOT_ROLLBACK",
            details={"job_id": str(job_id), "reason": reason}
        )


class JobAlreadyRolledBackError(DataExchangeError):
    """Le job a deja ete rollback."""

    def __init__(self, job_id: str):
        super().__init__(
            message="Le job a deja ete rollback",
            code="JOB_ALREADY_ROLLED_BACK",
            details={"job_id": str(job_id)}
        )


# ============== File Errors ==============

class FileNotFoundError(DataExchangeError):
    """Fichier non trouve."""

    def __init__(self, file_path: str):
        super().__init__(
            message=f"Fichier non trouve: {file_path}",
            code="FILE_NOT_FOUND",
            details={"file_path": file_path}
        )


class FileFormatError(DataExchangeError):
    """Format de fichier non supporte ou invalide."""

    def __init__(self, format: str, reason: Optional[str] = None):
        message = f"Format de fichier non supporte: {format}"
        if reason:
            message += f" ({reason})"
        super().__init__(
            message=message,
            code="FILE_FORMAT_ERROR",
            details={"format": format, "reason": reason}
        )


class FileReadError(DataExchangeError):
    """Erreur de lecture du fichier."""

    def __init__(self, file_path: str, error: str):
        super().__init__(
            message=f"Erreur de lecture du fichier: {error}",
            code="FILE_READ_ERROR",
            details={"file_path": file_path, "error": error}
        )


class FileWriteError(DataExchangeError):
    """Erreur d'ecriture du fichier."""

    def __init__(self, file_path: str, error: str):
        super().__init__(
            message=f"Erreur d'ecriture du fichier: {error}",
            code="FILE_WRITE_ERROR",
            details={"file_path": file_path, "error": error}
        )


class FileTooLargeError(DataExchangeError):
    """Fichier trop volumineux."""

    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"Fichier trop volumineux ({file_size} bytes, max: {max_size} bytes)",
            code="FILE_TOO_LARGE",
            details={"file_size": file_size, "max_size": max_size}
        )


class FileEncodingError(DataExchangeError):
    """Erreur d'encodage du fichier."""

    def __init__(self, expected_encoding: str, error: str):
        super().__init__(
            message=f"Erreur d'encodage du fichier (attendu: {expected_encoding}): {error}",
            code="FILE_ENCODING_ERROR",
            details={"expected_encoding": expected_encoding, "error": error}
        )


# ============== Validation Errors ==============

class ValidationError(DataExchangeError):
    """Erreur de validation des donnees."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"errors": errors or []}
        )
        self.errors = errors or []


class RequiredFieldMissingError(ValidationError):
    """Champ requis manquant."""

    def __init__(self, field: str, row: Optional[int] = None):
        message = f"Champ requis manquant: {field}"
        if row is not None:
            message += f" (ligne {row})"
        super().__init__(
            message=message,
            errors=[{"field": field, "row": row, "type": "required"}]
        )


class InvalidFieldValueError(ValidationError):
    """Valeur de champ invalide."""

    def __init__(
        self,
        field: str,
        value: Any,
        expected: str,
        row: Optional[int] = None
    ):
        message = f"Valeur invalide pour le champ '{field}': '{value}' (attendu: {expected})"
        if row is not None:
            message += f" (ligne {row})"
        super().__init__(
            message=message,
            errors=[{
                "field": field,
                "value": str(value),
                "expected": expected,
                "row": row,
                "type": "invalid"
            }]
        )


class DuplicateKeyError(ValidationError):
    """Cle de deduplication dupliquee."""

    def __init__(self, key_field: str, value: Any, rows: List[int]):
        super().__init__(
            message=f"Valeur dupliquee pour la cle '{key_field}': '{value}' (lignes: {rows})",
            errors=[{
                "field": key_field,
                "value": str(value),
                "rows": rows,
                "type": "duplicate"
            }]
        )


class ReferenceNotFoundError(ValidationError):
    """Reference externe non trouvee."""

    def __init__(self, field: str, value: Any, entity_type: str, row: Optional[int] = None):
        message = f"Reference non trouvee pour '{field}': '{value}' (type: {entity_type})"
        if row is not None:
            message += f" (ligne {row})"
        super().__init__(
            message=message,
            errors=[{
                "field": field,
                "value": str(value),
                "entity_type": entity_type,
                "row": row,
                "type": "reference_not_found"
            }]
        )


# ============== Mapping Errors ==============

class MappingNotFoundError(DataExchangeError):
    """Mapping de champ non trouve."""

    def __init__(self, mapping_id: str):
        super().__init__(
            message=f"Mapping non trouve: {mapping_id}",
            code="MAPPING_NOT_FOUND",
            details={"mapping_id": str(mapping_id)}
        )


class MappingConfigurationError(DataExchangeError):
    """Erreur de configuration du mapping."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=f"Erreur de configuration du mapping: {message}",
            code="MAPPING_CONFIG_ERROR",
            details={"field": field} if field else {}
        )


class NoKeyFieldDefinedError(MappingConfigurationError):
    """Aucun champ cle defini pour la deduplication."""

    def __init__(self):
        super().__init__(
            message="Aucun champ cle defini pour la deduplication (mode 'update' requis)"
        )


# ============== Transformation Errors ==============

class TransformationError(DataExchangeError):
    """Erreur lors de la transformation des donnees."""

    def __init__(
        self,
        message: str,
        transformation_code: Optional[str] = None,
        row: Optional[int] = None
    ):
        details = {}
        if transformation_code:
            details["transformation_code"] = transformation_code
        if row is not None:
            details["row"] = row
        super().__init__(
            message=f"Erreur de transformation: {message}",
            code="TRANSFORMATION_ERROR",
            details=details
        )


class TransformationScriptError(TransformationError):
    """Erreur dans le script de transformation."""

    def __init__(self, script_error: str, transformation_code: Optional[str] = None):
        super().__init__(
            message=f"Erreur dans le script de transformation: {script_error}",
            transformation_code=transformation_code
        )


class LookupTableNotFoundError(DataExchangeError):
    """Table de correspondance non trouvee."""

    def __init__(self, lookup_code: str):
        super().__init__(
            message=f"Table de correspondance non trouvee: {lookup_code}",
            code="LOOKUP_TABLE_NOT_FOUND",
            details={"lookup_code": lookup_code}
        )


class LookupValueNotFoundError(DataExchangeError):
    """Valeur non trouvee dans la table de correspondance."""

    def __init__(self, lookup_code: str, value: Any):
        super().__init__(
            message=f"Valeur '{value}' non trouvee dans la table '{lookup_code}'",
            code="LOOKUP_VALUE_NOT_FOUND",
            details={"lookup_code": lookup_code, "value": str(value)}
        )


# ============== Notification Errors ==============

class NotificationConfigNotFoundError(DataExchangeError):
    """Configuration de notification non trouvee."""

    def __init__(self, config_id: str):
        super().__init__(
            message=f"Configuration de notification non trouvee: {config_id}",
            code="NOTIFICATION_CONFIG_NOT_FOUND",
            details={"config_id": str(config_id)}
        )


class NotificationSendError(DataExchangeError):
    """Erreur lors de l'envoi de notification."""

    def __init__(self, notification_type: str, error: str):
        super().__init__(
            message=f"Erreur lors de l'envoi de notification ({notification_type}): {error}",
            code="NOTIFICATION_SEND_ERROR",
            details={"notification_type": notification_type, "error": error}
        )


# ============== Processing Errors ==============

class ProcessingError(DataExchangeError):
    """Erreur lors du traitement des donnees."""

    def __init__(
        self,
        message: str,
        row: Optional[int] = None,
        entity_type: Optional[str] = None
    ):
        details = {}
        if row is not None:
            details["row"] = row
        if entity_type:
            details["entity_type"] = entity_type
        super().__init__(
            message=f"Erreur de traitement: {message}",
            code="PROCESSING_ERROR",
            details=details
        )


class EntityCreationError(ProcessingError):
    """Erreur lors de la creation d'une entite."""

    def __init__(self, entity_type: str, error: str, row: Optional[int] = None):
        super().__init__(
            message=f"Erreur lors de la creation de {entity_type}: {error}",
            row=row,
            entity_type=entity_type
        )


class EntityUpdateError(ProcessingError):
    """Erreur lors de la mise a jour d'une entite."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        error: str,
        row: Optional[int] = None
    ):
        super().__init__(
            message=f"Erreur lors de la mise a jour de {entity_type} ({entity_id}): {error}",
            row=row,
            entity_type=entity_type
        )


class RollbackError(DataExchangeError):
    """Erreur lors du rollback."""

    def __init__(self, job_id: str, error: str):
        super().__init__(
            message=f"Erreur lors du rollback: {error}",
            code="ROLLBACK_ERROR",
            details={"job_id": str(job_id), "error": error}
        )
