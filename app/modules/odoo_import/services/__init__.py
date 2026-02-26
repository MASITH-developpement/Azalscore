"""
AZALS MODULE - Odoo Import Services
====================================

Sous-services modulaires pour l'import Odoo.
Architecture façade avec délégation vers services spécialisés.
"""

from .base import BaseOdooService
from .config import ConfigService
from .connection import ConnectionService
from .products import ProductImportService
from .contacts import ContactImportService
from .orders import OrderImportService
from .invoices import InvoiceImportService
from .accounting import AccountingImportService
from .interventions import InterventionImportService
from .history import HistoryService
from .preview import PreviewService

__all__ = [
    "BaseOdooService",
    "ConfigService",
    "ConnectionService",
    "ProductImportService",
    "ContactImportService",
    "OrderImportService",
    "InvoiceImportService",
    "AccountingImportService",
    "InterventionImportService",
    "HistoryService",
    "PreviewService",
]
