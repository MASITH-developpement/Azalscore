"""
AZALS MODULE COMMERCIAL - Exceptions
=====================================

Exceptions metier specifiques au module commercial.
"""

from typing import Optional, List
from uuid import UUID
from decimal import Decimal


class CommercialError(Exception):
    """Exception de base du module Commercial."""

    def __init__(self, message: str, tenant_id: Optional[UUID] = None):
        self.message = message
        self.tenant_id = tenant_id
        super().__init__(self.message)


# ============================================================================
# DOCUMENT ERRORS (Factures, Devis, Commandes)
# ============================================================================

class DocumentNotFoundError(CommercialError):
    """Document commercial non trouve."""

    def __init__(
        self,
        document_id: Optional[str] = None,
        document_number: Optional[str] = None,
        document_type: Optional[str] = None
    ):
        self.document_id = document_id
        self.document_number = document_number
        self.document_type = document_type
        identifier = document_number or document_id
        type_str = f" ({document_type})" if document_type else ""
        super().__init__(f"Document{type_str} {identifier} non trouve")


class DocumentDuplicateError(CommercialError):
    """Numero de document deja existant."""

    def __init__(self, document_number: str, document_type: str):
        self.document_number = document_number
        self.document_type = document_type
        super().__init__(
            f"Le numero de {document_type} {document_number} existe deja"
        )


class DocumentValidationError(CommercialError):
    """Erreur de validation du document."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


class DocumentNotEditableError(CommercialError):
    """Document non modifiable dans son etat actuel."""

    def __init__(self, document_number: str, status: str, document_type: str = "document"):
        self.document_number = document_number
        self.status = status
        self.document_type = document_type
        super().__init__(
            f"Le {document_type} {document_number} n'est pas modifiable "
            f"(statut: {status})"
        )


class DocumentStateError(CommercialError):
    """Transition d'etat invalide pour le document."""

    def __init__(self, current_status: str, target_status: str, document_type: str = "document"):
        self.current_status = current_status
        self.target_status = target_status
        self.document_type = document_type
        super().__init__(
            f"Transition impossible de {current_status} vers {target_status} "
            f"pour ce {document_type}"
        )


# ============================================================================
# INVOICE SPECIFIC ERRORS
# ============================================================================

class InvoiceNotFoundError(DocumentNotFoundError):
    """Facture non trouvee."""

    def __init__(self, invoice_id: Optional[str] = None, invoice_number: Optional[str] = None):
        super().__init__(invoice_id, invoice_number, "facture")


class InvoiceAlreadyPaidError(CommercialError):
    """Facture deja payee."""

    def __init__(self, invoice_number: str):
        self.invoice_number = invoice_number
        super().__init__(f"La facture {invoice_number} est deja payee")


class InvoicePartialPaymentError(CommercialError):
    """Paiement partiel insuffisant."""

    def __init__(self, invoice_number: str, amount_due: Decimal, amount_paid: Decimal):
        self.invoice_number = invoice_number
        self.amount_due = amount_due
        self.amount_paid = amount_paid
        super().__init__(
            f"Paiement insuffisant pour {invoice_number}: "
            f"du={amount_due}, paye={amount_paid}"
        )


class InvoiceCancelledError(CommercialError):
    """Operation sur une facture annulee."""

    def __init__(self, invoice_number: str):
        self.invoice_number = invoice_number
        super().__init__(f"La facture {invoice_number} est annulee")


# ============================================================================
# QUOTE SPECIFIC ERRORS
# ============================================================================

class QuoteNotFoundError(DocumentNotFoundError):
    """Devis non trouve."""

    def __init__(self, quote_id: Optional[str] = None, quote_number: Optional[str] = None):
        super().__init__(quote_id, quote_number, "devis")


class QuoteExpiredError(CommercialError):
    """Devis expire."""

    def __init__(self, quote_number: str, expired_at: str):
        self.quote_number = quote_number
        self.expired_at = expired_at
        super().__init__(f"Le devis {quote_number} a expire le {expired_at}")


class QuoteAlreadyConvertedError(CommercialError):
    """Devis deja converti en commande/facture."""

    def __init__(self, quote_number: str, converted_to: str):
        self.quote_number = quote_number
        self.converted_to = converted_to
        super().__init__(
            f"Le devis {quote_number} a deja ete converti en {converted_to}"
        )


# ============================================================================
# ORDER SPECIFIC ERRORS
# ============================================================================

class OrderNotFoundError(DocumentNotFoundError):
    """Commande non trouvee."""

    def __init__(self, order_id: Optional[str] = None, order_number: Optional[str] = None):
        super().__init__(order_id, order_number, "commande")


class OrderCancelledError(CommercialError):
    """Operation sur une commande annulee."""

    def __init__(self, order_number: str):
        self.order_number = order_number
        super().__init__(f"La commande {order_number} est annulee")


class OrderAlreadyDeliveredError(CommercialError):
    """Commande deja livree."""

    def __init__(self, order_number: str):
        self.order_number = order_number
        super().__init__(f"La commande {order_number} est deja livree")


# ============================================================================
# CLIENT ERRORS
# ============================================================================

class ClientNotFoundError(CommercialError):
    """Client non trouve."""

    def __init__(self, client_id: Optional[str] = None, client_code: Optional[str] = None):
        self.client_id = client_id
        self.client_code = client_code
        identifier = client_code or client_id
        super().__init__(f"Client {identifier} non trouve")


class ClientInactiveError(CommercialError):
    """Client inactif."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        super().__init__(f"Le client {client_id} est inactif")


class ClientCreditLimitExceededError(CommercialError):
    """Limite de credit client depassee."""

    def __init__(self, client_id: str, limit: Decimal, current: Decimal, requested: Decimal):
        self.client_id = client_id
        self.limit = limit
        self.current = current
        self.requested = requested
        super().__init__(
            f"Limite de credit depassee pour le client {client_id}: "
            f"limite={limit}, encours={current}, demande={requested}"
        )


# ============================================================================
# PRODUCT/LINE ERRORS
# ============================================================================

class ProductNotFoundError(CommercialError):
    """Produit non trouve."""

    def __init__(self, product_id: Optional[str] = None, sku: Optional[str] = None):
        self.product_id = product_id
        self.sku = sku
        identifier = sku or product_id
        super().__init__(f"Produit {identifier} non trouve")


class LineNotFoundError(CommercialError):
    """Ligne de document non trouvee."""

    def __init__(self, line_id: str, document_number: Optional[str] = None):
        self.line_id = line_id
        self.document_number = document_number
        super().__init__(f"Ligne {line_id} non trouvee")


# ============================================================================
# PAYMENT ERRORS
# ============================================================================

class PaymentNotFoundError(CommercialError):
    """Paiement non trouve."""

    def __init__(self, payment_id: Optional[str] = None):
        self.payment_id = payment_id
        super().__init__(f"Paiement {payment_id} non trouve")


class PaymentAmountError(CommercialError):
    """Montant de paiement invalide."""

    def __init__(self, amount: Decimal, reason: str):
        self.amount = amount
        self.reason = reason
        super().__init__(f"Montant de paiement invalide ({amount}): {reason}")


# ============================================================================
# CACHE ERRORS
# ============================================================================

class CommercialCacheError(CommercialError):
    """Erreur de cache non critique."""
    pass
