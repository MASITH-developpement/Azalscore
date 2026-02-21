"""
AZALS MODULE ESIGNATURE - Exceptions metier
============================================

Exceptions specifiques au module de signature electronique.
"""


class ESignatureError(Exception):
    """Exception de base pour le module ESignature."""
    def __init__(self, message: str = "Erreur de signature electronique", code: str = "ESIGN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# =============================================================================
# CONFIG EXCEPTIONS
# =============================================================================

class ConfigNotFoundError(ESignatureError):
    """Configuration non trouvee."""
    def __init__(self, message: str = "Configuration signature non trouvee"):
        super().__init__(message, "CONFIG_NOT_FOUND")


class ConfigAlreadyExistsError(ESignatureError):
    """Configuration deja existante."""
    def __init__(self, message: str = "Configuration signature deja existante"):
        super().__init__(message, "CONFIG_EXISTS")


# =============================================================================
# PROVIDER EXCEPTIONS
# =============================================================================

class ProviderNotConfiguredError(ESignatureError):
    """Provider non configure."""
    def __init__(self, provider: str):
        super().__init__(f"Provider {provider} non configure", "PROVIDER_NOT_CONFIGURED")
        self.provider = provider


class ProviderCredentialNotFoundError(ESignatureError):
    """Credentials provider non trouves."""
    def __init__(self, provider: str):
        super().__init__(f"Credentials pour {provider} non trouves", "CREDENTIALS_NOT_FOUND")
        self.provider = provider


class ProviderAuthenticationError(ESignatureError):
    """Erreur d'authentification provider."""
    def __init__(self, provider: str, message: str = ""):
        super().__init__(f"Erreur authentification {provider}: {message}", "PROVIDER_AUTH_ERROR")
        self.provider = provider


class ProviderAPIError(ESignatureError):
    """Erreur API provider."""
    def __init__(self, provider: str, message: str, status_code: int = None):
        super().__init__(f"Erreur API {provider}: {message}", "PROVIDER_API_ERROR")
        self.provider = provider
        self.status_code = status_code


class ProviderWebhookError(ESignatureError):
    """Erreur webhook provider."""
    def __init__(self, provider: str, message: str = ""):
        super().__init__(f"Erreur webhook {provider}: {message}", "WEBHOOK_ERROR")
        self.provider = provider


class InvalidWebhookSignatureError(ESignatureError):
    """Signature webhook invalide."""
    def __init__(self, provider: str):
        super().__init__(f"Signature webhook invalide pour {provider}", "INVALID_WEBHOOK_SIGNATURE")
        self.provider = provider


# =============================================================================
# TEMPLATE EXCEPTIONS
# =============================================================================

class TemplateNotFoundError(ESignatureError):
    """Template non trouve."""
    def __init__(self, template_id: str = None, code: str = None):
        identifier = template_id or code or "inconnu"
        super().__init__(f"Template {identifier} non trouve", "TEMPLATE_NOT_FOUND")


class TemplateDuplicateCodeError(ESignatureError):
    """Code template deja utilise."""
    def __init__(self, code: str):
        super().__init__(f"Code template '{code}' deja utilise", "TEMPLATE_DUPLICATE_CODE")
        self.template_code = code


class TemplateLockedError(ESignatureError):
    """Template verrouille."""
    def __init__(self, template_id: str):
        super().__init__(f"Template {template_id} est verrouille", "TEMPLATE_LOCKED")


class TemplateValidationError(ESignatureError):
    """Erreur de validation template."""
    def __init__(self, message: str):
        super().__init__(f"Validation template: {message}", "TEMPLATE_VALIDATION_ERROR")


class TemplateFileRequiredError(ESignatureError):
    """Fichier template requis."""
    def __init__(self):
        super().__init__("Un fichier PDF est requis pour le template", "TEMPLATE_FILE_REQUIRED")


# =============================================================================
# ENVELOPE EXCEPTIONS
# =============================================================================

class EnvelopeNotFoundError(ESignatureError):
    """Enveloppe non trouvee."""
    def __init__(self, envelope_id: str = None, envelope_number: str = None):
        identifier = envelope_id or envelope_number or "inconnue"
        super().__init__(f"Enveloppe {identifier} non trouvee", "ENVELOPE_NOT_FOUND")


class EnvelopeDuplicateNumberError(ESignatureError):
    """Numero enveloppe deja utilise."""
    def __init__(self, number: str):
        super().__init__(f"Numero enveloppe '{number}' deja utilise", "ENVELOPE_DUPLICATE_NUMBER")


class EnvelopeStateError(ESignatureError):
    """Transition d'etat enveloppe invalide."""
    def __init__(self, current_status: str, attempted_action: str):
        super().__init__(
            f"Action '{attempted_action}' impossible depuis le statut '{current_status}'",
            "ENVELOPE_STATE_ERROR"
        )
        self.current_status = current_status
        self.attempted_action = attempted_action


class EnvelopeNotDraftError(ESignatureError):
    """Enveloppe n'est pas en brouillon."""
    def __init__(self, envelope_id: str):
        super().__init__(
            f"Enveloppe {envelope_id} n'est pas en brouillon, modification impossible",
            "ENVELOPE_NOT_DRAFT"
        )


class EnvelopeAlreadySentError(ESignatureError):
    """Enveloppe deja envoyee."""
    def __init__(self, envelope_id: str):
        super().__init__(f"Enveloppe {envelope_id} deja envoyee", "ENVELOPE_ALREADY_SENT")


class EnvelopeExpiredError(ESignatureError):
    """Enveloppe expiree."""
    def __init__(self, envelope_id: str):
        super().__init__(f"Enveloppe {envelope_id} expiree", "ENVELOPE_EXPIRED")


class EnvelopeCancelledError(ESignatureError):
    """Enveloppe annulee."""
    def __init__(self, envelope_id: str):
        super().__init__(f"Enveloppe {envelope_id} annulee", "ENVELOPE_CANCELLED")


class EnvelopeCompletedError(ESignatureError):
    """Enveloppe deja completee."""
    def __init__(self, envelope_id: str):
        super().__init__(f"Enveloppe {envelope_id} deja completee", "ENVELOPE_COMPLETED")


class EnvelopeNoDocumentsError(ESignatureError):
    """Enveloppe sans documents."""
    def __init__(self, envelope_id: str):
        super().__init__(f"Enveloppe {envelope_id} ne contient aucun document", "ENVELOPE_NO_DOCUMENTS")


class EnvelopeNoSignersError(ESignatureError):
    """Enveloppe sans signataires."""
    def __init__(self, envelope_id: str):
        super().__init__(f"Enveloppe {envelope_id} ne contient aucun signataire", "ENVELOPE_NO_SIGNERS")


class EnvelopePendingApprovalError(ESignatureError):
    """Enveloppe en attente d'approbation."""
    def __init__(self, envelope_id: str):
        super().__init__(
            f"Enveloppe {envelope_id} en attente d'approbation",
            "ENVELOPE_PENDING_APPROVAL"
        )


# =============================================================================
# DOCUMENT EXCEPTIONS
# =============================================================================

class DocumentNotFoundError(ESignatureError):
    """Document non trouve."""
    def __init__(self, document_id: str):
        super().__init__(f"Document {document_id} non trouve", "DOCUMENT_NOT_FOUND")


class DocumentUploadError(ESignatureError):
    """Erreur upload document."""
    def __init__(self, message: str):
        super().__init__(f"Erreur upload: {message}", "DOCUMENT_UPLOAD_ERROR")


class InvalidDocumentTypeError(ESignatureError):
    """Type de document invalide."""
    def __init__(self, mime_type: str):
        super().__init__(
            f"Type de fichier {mime_type} non supporte. Utilisez PDF.",
            "INVALID_DOCUMENT_TYPE"
        )


class DocumentTooLargeError(ESignatureError):
    """Document trop volumineux."""
    def __init__(self, size: int, max_size: int):
        super().__init__(
            f"Document trop volumineux ({size} octets). Maximum: {max_size} octets",
            "DOCUMENT_TOO_LARGE"
        )


class DocumentCorruptedError(ESignatureError):
    """Document corrompu."""
    def __init__(self, filename: str):
        super().__init__(f"Document {filename} semble corrompu", "DOCUMENT_CORRUPTED")


# =============================================================================
# SIGNER EXCEPTIONS
# =============================================================================

class SignerNotFoundError(ESignatureError):
    """Signataire non trouve."""
    def __init__(self, signer_id: str = None, email: str = None):
        identifier = signer_id or email or "inconnu"
        super().__init__(f"Signataire {identifier} non trouve", "SIGNER_NOT_FOUND")


class SignerAlreadySignedError(ESignatureError):
    """Signataire a deja signe."""
    def __init__(self, signer_id: str):
        super().__init__(f"Signataire {signer_id} a deja signe", "SIGNER_ALREADY_SIGNED")


class SignerDeclinedError(ESignatureError):
    """Signataire a refuse."""
    def __init__(self, signer_id: str):
        super().__init__(f"Signataire {signer_id} a refuse de signer", "SIGNER_DECLINED")


class SignerExpiredError(ESignatureError):
    """Acces signataire expire."""
    def __init__(self, signer_id: str):
        super().__init__(f"Acces signataire {signer_id} expire", "SIGNER_EXPIRED")


class SignerNotAuthorizedError(ESignatureError):
    """Signataire non autorise."""
    def __init__(self, signer_id: str = None):
        super().__init__(
            f"Signataire non autorise a effectuer cette action",
            "SIGNER_NOT_AUTHORIZED"
        )


class SignerDelegationNotAllowedError(ESignatureError):
    """Delegation non autorisee."""
    def __init__(self):
        super().__init__(
            "La delegation n'est pas autorisee pour cette enveloppe",
            "DELEGATION_NOT_ALLOWED"
        )


class SignerAlreadyDelegatedError(ESignatureError):
    """Signataire a deja delegue."""
    def __init__(self, signer_id: str):
        super().__init__(f"Signataire {signer_id} a deja delegue", "SIGNER_ALREADY_DELEGATED")


class InvalidAccessTokenError(ESignatureError):
    """Token d'acces invalide."""
    def __init__(self):
        super().__init__("Token d'acces invalide ou expire", "INVALID_ACCESS_TOKEN")


class SignerOrderError(ESignatureError):
    """Ordre de signature non respecte."""
    def __init__(self, signer_id: str, expected_order: int):
        super().__init__(
            f"Ce n'est pas le tour du signataire. Ordre attendu: {expected_order}",
            "SIGNER_ORDER_ERROR"
        )


# =============================================================================
# FIELD EXCEPTIONS
# =============================================================================

class FieldNotFoundError(ESignatureError):
    """Champ non trouve."""
    def __init__(self, field_id: str):
        super().__init__(f"Champ {field_id} non trouve", "FIELD_NOT_FOUND")


class FieldRequiredError(ESignatureError):
    """Champ obligatoire non rempli."""
    def __init__(self, field_name: str):
        super().__init__(f"Champ obligatoire '{field_name}' non rempli", "FIELD_REQUIRED")


class FieldValidationError(ESignatureError):
    """Erreur validation champ."""
    def __init__(self, field_name: str, message: str):
        super().__init__(f"Validation champ '{field_name}': {message}", "FIELD_VALIDATION_ERROR")


class FieldAlreadyFilledError(ESignatureError):
    """Champ deja rempli."""
    def __init__(self, field_id: str):
        super().__init__(f"Champ {field_id} deja rempli", "FIELD_ALREADY_FILLED")


# =============================================================================
# SIGNATURE EXCEPTIONS
# =============================================================================

class SignatureRequiredError(ESignatureError):
    """Signature requise."""
    def __init__(self, field_count: int):
        super().__init__(
            f"{field_count} signature(s) requise(s) non fournie(s)",
            "SIGNATURE_REQUIRED"
        )


class InvalidSignatureDataError(ESignatureError):
    """Donnees de signature invalides."""
    def __init__(self, message: str = ""):
        super().__init__(f"Donnees de signature invalides: {message}", "INVALID_SIGNATURE_DATA")


class SignatureVerificationError(ESignatureError):
    """Erreur verification signature."""
    def __init__(self, message: str = ""):
        super().__init__(f"Verification signature echouee: {message}", "SIGNATURE_VERIFICATION_ERROR")


# =============================================================================
# CERTIFICATE EXCEPTIONS
# =============================================================================

class CertificateNotFoundError(ESignatureError):
    """Certificat non trouve."""
    def __init__(self, certificate_id: str = None, envelope_id: str = None):
        identifier = certificate_id or f"enveloppe {envelope_id}" or "inconnu"
        super().__init__(f"Certificat {identifier} non trouve", "CERTIFICATE_NOT_FOUND")


class CertificateGenerationError(ESignatureError):
    """Erreur generation certificat."""
    def __init__(self, message: str):
        super().__init__(f"Erreur generation certificat: {message}", "CERTIFICATE_GENERATION_ERROR")


class CertificateExpiredError(ESignatureError):
    """Certificat expire."""
    def __init__(self, certificate_number: str):
        super().__init__(f"Certificat {certificate_number} expire", "CERTIFICATE_EXPIRED")


class CertificateInvalidError(ESignatureError):
    """Certificat invalide."""
    def __init__(self, certificate_number: str, reason: str = ""):
        super().__init__(
            f"Certificat {certificate_number} invalide: {reason}",
            "CERTIFICATE_INVALID"
        )


# =============================================================================
# REMINDER EXCEPTIONS
# =============================================================================

class ReminderNotFoundError(ESignatureError):
    """Rappel non trouve."""
    def __init__(self, reminder_id: str):
        super().__init__(f"Rappel {reminder_id} non trouve", "REMINDER_NOT_FOUND")


class MaxRemindersReachedError(ESignatureError):
    """Nombre maximum de rappels atteint."""
    def __init__(self, max_reminders: int):
        super().__init__(
            f"Nombre maximum de rappels atteint ({max_reminders})",
            "MAX_REMINDERS_REACHED"
        )


class ReminderTooSoonError(ESignatureError):
    """Rappel envoye trop tot."""
    def __init__(self, hours_remaining: int):
        super().__init__(
            f"Prochain rappel possible dans {hours_remaining} heures",
            "REMINDER_TOO_SOON"
        )


# =============================================================================
# APPROVAL EXCEPTIONS
# =============================================================================

class ApprovalRequiredError(ESignatureError):
    """Approbation requise avant envoi."""
    def __init__(self, envelope_id: str):
        super().__init__(
            f"Enveloppe {envelope_id} requiert une approbation avant envoi",
            "APPROVAL_REQUIRED"
        )


class ApprovalNotAuthorizedError(ESignatureError):
    """Non autorise a approuver."""
    def __init__(self, user_id: str):
        super().__init__(
            f"Utilisateur {user_id} non autorise a approuver",
            "APPROVAL_NOT_AUTHORIZED"
        )


class ApprovalAlreadyProcessedError(ESignatureError):
    """Approbation deja traitee."""
    def __init__(self, envelope_id: str):
        super().__init__(
            f"Approbation enveloppe {envelope_id} deja traitee",
            "APPROVAL_ALREADY_PROCESSED"
        )


# =============================================================================
# ARCHIVE EXCEPTIONS
# =============================================================================

class ArchiveError(ESignatureError):
    """Erreur archivage."""
    def __init__(self, message: str):
        super().__init__(f"Erreur archivage: {message}", "ARCHIVE_ERROR")


class EnvelopeNotCompletedForArchiveError(ESignatureError):
    """Enveloppe non completee pour archivage."""
    def __init__(self, envelope_id: str):
        super().__init__(
            f"Enveloppe {envelope_id} doit etre completee pour etre archivee",
            "ENVELOPE_NOT_COMPLETED_FOR_ARCHIVE"
        )


# =============================================================================
# QUOTA EXCEPTIONS
# =============================================================================

class QuotaExceededError(ESignatureError):
    """Quota depasse."""
    def __init__(self, quota_type: str, current: int, maximum: int):
        super().__init__(
            f"Quota {quota_type} depasse: {current}/{maximum}",
            "QUOTA_EXCEEDED"
        )
        self.quota_type = quota_type
        self.current = current
        self.maximum = maximum


class MonthlyEnvelopeLimitError(ESignatureError):
    """Limite mensuelle enveloppes atteinte."""
    def __init__(self, limit: int):
        super().__init__(
            f"Limite mensuelle de {limit} enveloppes atteinte",
            "MONTHLY_ENVELOPE_LIMIT"
        )
