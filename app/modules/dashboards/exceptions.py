"""
AZALSCORE ERP - Module DASHBOARDS
==================================
Exceptions specifiques au module.
"""

from typing import Optional, Any


class DashboardException(Exception):
    """Exception de base pour le module dashboards."""

    def __init__(
        self,
        message: str,
        code: str = "DASHBOARD_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DashboardNotFoundError(DashboardException):
    """Dashboard non trouve."""

    def __init__(self, dashboard_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Dashboard non trouve: {dashboard_id}",
            code="DASHBOARD_NOT_FOUND",
            details={"dashboard_id": dashboard_id}
        )


class DashboardAccessDeniedError(DashboardException):
    """Acces refuse au dashboard."""

    def __init__(
        self,
        dashboard_id: str,
        user_id: str,
        required_permission: str = "view",
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Acces refuse au dashboard: {dashboard_id}",
            code="DASHBOARD_ACCESS_DENIED",
            details={
                "dashboard_id": dashboard_id,
                "user_id": user_id,
                "required_permission": required_permission
            }
        )


class DashboardCodeExistsError(DashboardException):
    """Code dashboard deja utilise."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Code dashboard deja utilise: {code}",
            code="DASHBOARD_CODE_EXISTS",
            details={"code": code}
        )


class DashboardValidationError(DashboardException):
    """Erreur de validation dashboard."""

    def __init__(self, errors: list[dict[str, Any]], message: Optional[str] = None):
        super().__init__(
            message=message or "Erreur de validation dashboard",
            code="DASHBOARD_VALIDATION_ERROR",
            details={"errors": errors}
        )


class DashboardLimitExceededError(DashboardException):
    """Limite de dashboards atteinte."""

    def __init__(self, limit: int, current: int, message: Optional[str] = None):
        super().__init__(
            message=message or f"Limite de dashboards atteinte: {current}/{limit}",
            code="DASHBOARD_LIMIT_EXCEEDED",
            details={"limit": limit, "current": current}
        )


# ============================================================================
# WIDGET EXCEPTIONS
# ============================================================================

class WidgetNotFoundError(DashboardException):
    """Widget non trouve."""

    def __init__(self, widget_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Widget non trouve: {widget_id}",
            code="WIDGET_NOT_FOUND",
            details={"widget_id": widget_id}
        )


class WidgetValidationError(DashboardException):
    """Erreur de validation widget."""

    def __init__(self, errors: list[dict[str, Any]], message: Optional[str] = None):
        super().__init__(
            message=message or "Erreur de validation widget",
            code="WIDGET_VALIDATION_ERROR",
            details={"errors": errors}
        )


class WidgetDataError(DashboardException):
    """Erreur de recuperation des donnees widget."""

    def __init__(
        self,
        widget_id: str,
        source_error: Optional[str] = None,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur de donnees widget: {widget_id}",
            code="WIDGET_DATA_ERROR",
            details={"widget_id": widget_id, "source_error": source_error}
        )


class WidgetLayoutError(DashboardException):
    """Erreur de layout widget."""

    def __init__(self, errors: list[dict[str, Any]], message: Optional[str] = None):
        super().__init__(
            message=message or "Erreur de layout widget",
            code="WIDGET_LAYOUT_ERROR",
            details={"errors": errors}
        )


# ============================================================================
# DATA SOURCE EXCEPTIONS
# ============================================================================

class DataSourceNotFoundError(DashboardException):
    """Source de donnees non trouvee."""

    def __init__(self, data_source_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Source de donnees non trouvee: {data_source_id}",
            code="DATA_SOURCE_NOT_FOUND",
            details={"data_source_id": data_source_id}
        )


class DataSourceConnectionError(DashboardException):
    """Erreur de connexion a la source de donnees."""

    def __init__(
        self,
        data_source_id: str,
        connection_error: Optional[str] = None,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur de connexion: {data_source_id}",
            code="DATA_SOURCE_CONNECTION_ERROR",
            details={
                "data_source_id": data_source_id,
                "connection_error": connection_error
            }
        )


class DataSourceCodeExistsError(DashboardException):
    """Code source de donnees deja utilise."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Code source deja utilise: {code}",
            code="DATA_SOURCE_CODE_EXISTS",
            details={"code": code}
        )


class DataQueryNotFoundError(DashboardException):
    """Requete non trouvee."""

    def __init__(self, query_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Requete non trouvee: {query_id}",
            code="DATA_QUERY_NOT_FOUND",
            details={"query_id": query_id}
        )


class DataQueryExecutionError(DashboardException):
    """Erreur d'execution de requete."""

    def __init__(
        self,
        query_id: str,
        execution_error: Optional[str] = None,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Erreur d'execution requete: {query_id}",
            code="DATA_QUERY_EXECUTION_ERROR",
            details={
                "query_id": query_id,
                "execution_error": execution_error
            }
        )


class DataQueryCodeExistsError(DashboardException):
    """Code requete deja utilise."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Code requete deja utilise: {code}",
            code="DATA_QUERY_CODE_EXISTS",
            details={"code": code}
        )


# ============================================================================
# SHARE EXCEPTIONS
# ============================================================================

class ShareNotFoundError(DashboardException):
    """Partage non trouve."""

    def __init__(self, share_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Partage non trouve: {share_id}",
            code="SHARE_NOT_FOUND",
            details={"share_id": share_id}
        )


class ShareInvalidLinkError(DashboardException):
    """Lien de partage invalide."""

    def __init__(self, link: str, reason: str = "expired", message: Optional[str] = None):
        super().__init__(
            message=message or f"Lien de partage invalide: {reason}",
            code="SHARE_INVALID_LINK",
            details={"link": link, "reason": reason}
        )


class SharePermissionError(DashboardException):
    """Permission de partage insuffisante."""

    def __init__(
        self,
        share_id: str,
        required: str,
        actual: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Permission insuffisante: {actual} < {required}",
            code="SHARE_PERMISSION_ERROR",
            details={"share_id": share_id, "required": required, "actual": actual}
        )


# ============================================================================
# ALERT EXCEPTIONS
# ============================================================================

class AlertRuleNotFoundError(DashboardException):
    """Regle d'alerte non trouvee."""

    def __init__(self, rule_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Regle d'alerte non trouvee: {rule_id}",
            code="ALERT_RULE_NOT_FOUND",
            details={"rule_id": rule_id}
        )


class AlertRuleCodeExistsError(DashboardException):
    """Code regle d'alerte deja utilise."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Code regle deja utilise: {code}",
            code="ALERT_RULE_CODE_EXISTS",
            details={"code": code}
        )


class AlertNotFoundError(DashboardException):
    """Alerte non trouvee."""

    def __init__(self, alert_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Alerte non trouvee: {alert_id}",
            code="ALERT_NOT_FOUND",
            details={"alert_id": alert_id}
        )


class AlertAlreadyResolvedError(DashboardException):
    """Alerte deja resolue."""

    def __init__(self, alert_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Alerte deja resolue: {alert_id}",
            code="ALERT_ALREADY_RESOLVED",
            details={"alert_id": alert_id}
        )


# ============================================================================
# EXPORT EXCEPTIONS
# ============================================================================

class ExportNotFoundError(DashboardException):
    """Export non trouve."""

    def __init__(self, export_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Export non trouve: {export_id}",
            code="EXPORT_NOT_FOUND",
            details={"export_id": export_id}
        )


class ExportFailedError(DashboardException):
    """Echec de l'export."""

    def __init__(
        self,
        export_id: str,
        reason: Optional[str] = None,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Echec de l'export: {export_id}",
            code="EXPORT_FAILED",
            details={"export_id": export_id, "reason": reason}
        )


class ExportExpiredError(DashboardException):
    """Export expire."""

    def __init__(self, export_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Export expire: {export_id}",
            code="EXPORT_EXPIRED",
            details={"export_id": export_id}
        )


class ExportFormatNotSupportedError(DashboardException):
    """Format d'export non supporte."""

    def __init__(
        self,
        format: str,
        supported_formats: list[str],
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Format non supporte: {format}",
            code="EXPORT_FORMAT_NOT_SUPPORTED",
            details={"format": format, "supported_formats": supported_formats}
        )


# ============================================================================
# SCHEDULED REPORT EXCEPTIONS
# ============================================================================

class ScheduledReportNotFoundError(DashboardException):
    """Rapport planifie non trouve."""

    def __init__(self, report_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Rapport planifie non trouve: {report_id}",
            code="SCHEDULED_REPORT_NOT_FOUND",
            details={"report_id": report_id}
        )


class ScheduledReportCodeExistsError(DashboardException):
    """Code rapport planifie deja utilise."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Code rapport deja utilise: {code}",
            code="SCHEDULED_REPORT_CODE_EXISTS",
            details={"code": code}
        )


class InvalidCronExpressionError(DashboardException):
    """Expression cron invalide."""

    def __init__(self, expression: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Expression cron invalide: {expression}",
            code="INVALID_CRON_EXPRESSION",
            details={"expression": expression}
        )


# ============================================================================
# TEMPLATE EXCEPTIONS
# ============================================================================

class TemplateNotFoundError(DashboardException):
    """Template non trouve."""

    def __init__(self, template_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Template non trouve: {template_id}",
            code="TEMPLATE_NOT_FOUND",
            details={"template_id": template_id}
        )


class TemplateCodeExistsError(DashboardException):
    """Code template deja utilise."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Code template deja utilise: {code}",
            code="TEMPLATE_CODE_EXISTS",
            details={"code": code}
        )


# ============================================================================
# FAVORITE EXCEPTIONS
# ============================================================================

class FavoriteNotFoundError(DashboardException):
    """Favori non trouve."""

    def __init__(self, favorite_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Favori non trouve: {favorite_id}",
            code="FAVORITE_NOT_FOUND",
            details={"favorite_id": favorite_id}
        )


class FavoriteAlreadyExistsError(DashboardException):
    """Dashboard deja en favori."""

    def __init__(self, dashboard_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Dashboard deja en favori: {dashboard_id}",
            code="FAVORITE_ALREADY_EXISTS",
            details={"dashboard_id": dashboard_id}
        )
