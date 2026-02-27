"""
AZALS MODULE COUNTRY_PACKS/FRANCE - Exceptions
===============================================

Exceptions metier specifiques au module France:
- Facturation electronique (e-invoicing)
- PDP (Plateforme de Dematerialisation Partenaire)
- FEC (Fichier des Ecritures Comptables)
- Liasses fiscales
- EDI TVA
- PCG (Plan Comptable General)
"""

from typing import Optional, List, Dict, Any
from uuid import UUID


class FranceModuleError(Exception):
    """Exception de base du module France."""

    def __init__(self, message: str, tenant_id: Optional[UUID] = None):
        self.message = message
        self.tenant_id = tenant_id
        super().__init__(self.message)


# =============================================================================
# E-INVOICING ERRORS
# =============================================================================

class EInvoicingError(FranceModuleError):
    """Exception de base pour la facturation electronique."""
    pass


class EInvoicingValidationError(EInvoicingError):
    """Erreur de validation de facture electronique."""

    def __init__(self, message: str, errors: Optional[List[str]] = None, field: Optional[str] = None):
        self.errors = errors or []
        self.field = field
        super().__init__(message)


class EInvoicingFormatError(EInvoicingError):
    """Format de facture non supporte ou invalide."""

    def __init__(self, format_name: str, reason: Optional[str] = None):
        self.format_name = format_name
        self.reason = reason
        msg = f"Format de facture invalide: {format_name}"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg)


class EInvoicingSubmissionError(EInvoicingError):
    """Erreur lors de la soumission de facture."""

    def __init__(self, invoice_id: str, reason: str, status_code: Optional[int] = None):
        self.invoice_id = invoice_id
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"Erreur de soumission pour {invoice_id}: {reason}")


class EInvoicingStatusError(EInvoicingError):
    """Erreur lors de la recuperation du statut."""

    def __init__(self, invoice_id: str, reason: str):
        self.invoice_id = invoice_id
        self.reason = reason
        super().__init__(f"Erreur de statut pour {invoice_id}: {reason}")


class EInvoicingWebhookError(EInvoicingError):
    """Erreur lors du traitement d'un webhook e-invoicing."""

    def __init__(self, webhook_type: str, reason: str, payload: Optional[Dict] = None):
        self.webhook_type = webhook_type
        self.reason = reason
        self.payload = payload
        super().__init__(f"Erreur webhook {webhook_type}: {reason}")


class EInvoicingPDFError(EInvoicingError):
    """Erreur lors de la generation PDF Factur-X."""

    def __init__(self, reason: str, invoice_id: Optional[str] = None):
        self.invoice_id = invoice_id
        self.reason = reason
        msg = "Erreur de generation PDF"
        if invoice_id:
            msg += f" pour {invoice_id}"
        msg += f": {reason}"
        super().__init__(msg)


class EInvoicingXMLError(EInvoicingError):
    """Erreur lors du parsing/generation XML."""

    def __init__(self, reason: str, xml_type: Optional[str] = None):
        self.xml_type = xml_type
        self.reason = reason
        msg = "Erreur XML"
        if xml_type:
            msg += f" ({xml_type})"
        msg += f": {reason}"
        super().__init__(msg)


# =============================================================================
# PDP CLIENT ERRORS
# =============================================================================

class PDPError(FranceModuleError):
    """Exception de base pour le client PDP."""
    pass


class PDPConnectionError(PDPError):
    """Erreur de connexion au PDP."""

    def __init__(self, provider: str, reason: str, url: Optional[str] = None):
        self.provider = provider
        self.reason = reason
        self.url = url
        super().__init__(f"Connexion {provider} echouee: {reason}")


class PDPAuthenticationError(PDPError):
    """Erreur d'authentification PDP."""

    def __init__(self, provider: str, reason: Optional[str] = None):
        self.provider = provider
        self.reason = reason or "Identifiants invalides"
        super().__init__(f"Authentification {provider} echouee: {self.reason}")


class PDPAPIError(PDPError):
    """Erreur API PDP."""

    def __init__(
        self,
        provider: str,
        status_code: int,
        message: str,
        response_body: Optional[str] = None
    ):
        self.provider = provider
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"Erreur API {provider} ({status_code}): {message}")


class PDPRateLimitError(PDPError):
    """Rate limit atteint sur le PDP."""

    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.provider = provider
        self.retry_after = retry_after
        msg = f"Rate limit atteint sur {provider}"
        if retry_after:
            msg += f", reessayer dans {retry_after}s"
        super().__init__(msg)


class PDPTimeoutError(PDPError):
    """Timeout lors de l'appel PDP."""

    def __init__(self, provider: str, operation: str, timeout: int):
        self.provider = provider
        self.operation = operation
        self.timeout = timeout
        super().__init__(f"Timeout {provider} ({operation}) apres {timeout}s")


class PDPInvoiceNotFoundError(PDPError):
    """Facture non trouvee sur le PDP."""

    def __init__(self, provider: str, invoice_id: str):
        self.provider = provider
        self.invoice_id = invoice_id
        super().__init__(f"Facture {invoice_id} non trouvee sur {provider}")


class PDPInvoiceRejectedError(PDPError):
    """Facture rejetee par le PDP."""

    def __init__(self, provider: str, invoice_id: str, rejection_reason: str):
        self.provider = provider
        self.invoice_id = invoice_id
        self.rejection_reason = rejection_reason
        super().__init__(f"Facture {invoice_id} rejetee par {provider}: {rejection_reason}")


# =============================================================================
# FEC ERRORS
# =============================================================================

class FECError(FranceModuleError):
    """Exception de base pour le FEC."""
    pass


class FECGenerationError(FECError):
    """Erreur lors de la generation du FEC."""

    def __init__(self, reason: str, fiscal_year: Optional[str] = None):
        self.fiscal_year = fiscal_year
        self.reason = reason
        msg = "Erreur de generation FEC"
        if fiscal_year:
            msg += f" ({fiscal_year})"
        msg += f": {reason}"
        super().__init__(msg)


class FECValidationError(FECError):
    """Erreur de validation du FEC."""

    def __init__(self, message: str, errors: Optional[List[Dict]] = None, line: Optional[int] = None):
        self.errors = errors or []
        self.line = line
        super().__init__(message)


class FECExportError(FECError):
    """Erreur lors de l'export du FEC."""

    def __init__(self, reason: str, format_type: Optional[str] = None):
        self.format_type = format_type
        self.reason = reason
        super().__init__(f"Erreur d'export FEC: {reason}")


class FECDataMissingError(FECError):
    """Donnees manquantes pour la generation FEC."""

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Donnees FEC manquantes: {', '.join(missing_fields)}")


# =============================================================================
# LIASSES FISCALES ERRORS
# =============================================================================

class LiasseFiscaleError(FranceModuleError):
    """Exception de base pour les liasses fiscales."""
    pass


class LiasseGenerationError(LiasseFiscaleError):
    """Erreur lors de la generation de liasse."""

    def __init__(self, reason: str, form_type: Optional[str] = None):
        self.form_type = form_type
        self.reason = reason
        msg = "Erreur de generation de liasse"
        if form_type:
            msg += f" ({form_type})"
        msg += f": {reason}"
        super().__init__(msg)


class LiasseValidationError(LiasseFiscaleError):
    """Erreur de validation de liasse."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


class LiasseSubmissionError(LiasseFiscaleError):
    """Erreur lors de la soumission EDI-TDFC."""

    def __init__(self, reason: str, submission_id: Optional[str] = None):
        self.submission_id = submission_id
        self.reason = reason
        super().__init__(f"Erreur de soumission liasse: {reason}")


# =============================================================================
# EDI TVA ERRORS
# =============================================================================

class EDITVAError(FranceModuleError):
    """Exception de base pour l'EDI TVA."""
    pass


class EDITVAGenerationError(EDITVAError):
    """Erreur lors de la generation EDI TVA."""

    def __init__(self, reason: str, period: Optional[str] = None):
        self.period = period
        self.reason = reason
        msg = "Erreur de generation EDI TVA"
        if period:
            msg += f" ({period})"
        msg += f": {reason}"
        super().__init__(msg)


class EDITVAValidationError(EDITVAError):
    """Erreur de validation EDI TVA."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


# =============================================================================
# PCG ERRORS
# =============================================================================

class PCGError(FranceModuleError):
    """Exception de base pour le PCG."""
    pass


class PCGImportError(PCGError):
    """Erreur lors de l'import du PCG."""

    def __init__(self, reason: str, line: Optional[int] = None):
        self.line = line
        self.reason = reason
        msg = "Erreur d'import PCG"
        if line:
            msg += f" (ligne {line})"
        msg += f": {reason}"
        super().__init__(msg)


class PCGAccountNotFoundError(PCGError):
    """Compte PCG non trouve."""

    def __init__(self, account_code: str):
        self.account_code = account_code
        super().__init__(f"Compte PCG {account_code} non trouve")


# =============================================================================
# NETWORK/HTTP ERRORS (for external API calls)
# =============================================================================

class FranceAPIError(FranceModuleError):
    """Erreur generique API pour les services France."""

    def __init__(
        self,
        service: str,
        status_code: Optional[int] = None,
        message: str = "Erreur API",
        response: Optional[Any] = None
    ):
        self.service = service
        self.status_code = status_code
        self.response = response
        msg = f"Erreur API {service}"
        if status_code:
            msg += f" ({status_code})"
        msg += f": {message}"
        super().__init__(msg)
