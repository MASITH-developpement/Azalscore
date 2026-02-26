"""
AZALSCORE - E-Invoicing Module
===============================
Service de facturation électronique France 2026.

Structure modulaire refactorisée depuis einvoicing_service.py (2,101 lignes)
vers une architecture avec séparation des responsabilités.

Modules:
- pdp_config: Gestion des configurations PDP
- generation: Génération de factures électroniques
- submission: Soumission aux PDP
- management: CRUD des factures
- ereporting: E-reporting B2C
- stats: Statistiques et dashboard
- webhooks: Traitement des webhooks
- inbound: Factures entrantes
- lifecycle: Gestion du cycle de vie
- xml_parsing: Parsing Factur-X/UBL
- helpers: Fonctions utilitaires

@module einvoicing
"""
from .service import TenantEInvoicingService, get_einvoicing_service
from .pdp_config import PDPConfigManager
from .generation import EInvoiceGenerator
from .submission import EInvoiceSubmitter
from .management import EInvoiceManager
from .ereporting import EReportingManager
from .stats import EInvoiceStatsManager
from .webhooks import WebhookHandler
from .inbound import InboundInvoiceHandler
from .lifecycle import LifecycleManager
from .xml_parsing import EInvoiceXMLParser, get_xml_parser, XMLParsingError
from .helpers import (
    build_seller_from_tenant,
    build_buyer_from_customer,
    build_seller_from_supplier,
    calculate_vat_breakdown,
    calculate_vat_breakdown_purchase,
    build_invoice_data,
)


__all__ = [
    # Service principal
    "TenantEInvoicingService",
    "get_einvoicing_service",
    # Managers
    "PDPConfigManager",
    "EInvoiceGenerator",
    "EInvoiceSubmitter",
    "EInvoiceManager",
    "EReportingManager",
    "EInvoiceStatsManager",
    "WebhookHandler",
    "InboundInvoiceHandler",
    "LifecycleManager",
    # XML Parsing
    "EInvoiceXMLParser",
    "get_xml_parser",
    "XMLParsingError",
    # Helpers
    "build_seller_from_tenant",
    "build_buyer_from_customer",
    "build_seller_from_supplier",
    "calculate_vat_breakdown",
    "calculate_vat_breakdown_purchase",
    "build_invoice_data",
]
