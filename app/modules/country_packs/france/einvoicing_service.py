"""
AZALS - Service E-Invoicing France 2026
========================================

DEPRECATED: Ce fichier est conservé pour compatibilité ascendante.
La nouvelle implémentation modulaire se trouve dans:
    app/modules/country_packs/france/einvoicing/

Le fichier original a été sauvegardé dans einvoicing_service.py.bak

@module einvoicing_service
@deprecated Utiliser app.modules.country_packs.france.einvoicing
"""
from __future__ import annotations

# Re-export depuis le nouveau module pour compatibilité ascendante
from app.modules.country_packs.france.einvoicing import (
    TenantEInvoicingService,
    get_einvoicing_service,
    PDPConfigManager,
    EInvoiceGenerator,
    EInvoiceSubmitter,
    EInvoiceManager,
    EReportingManager,
    EInvoiceStatsManager,
    WebhookHandler,
    InboundInvoiceHandler,
    LifecycleManager,
    EInvoiceXMLParser,
    get_xml_parser,
    XMLParsingError,
    build_seller_from_tenant,
    build_buyer_from_customer,
    build_seller_from_supplier,
    calculate_vat_breakdown,
    calculate_vat_breakdown_purchase,
    build_invoice_data,
)

__all__ = [
    "TenantEInvoicingService",
    "get_einvoicing_service",
    "PDPConfigManager",
    "EInvoiceGenerator",
    "EInvoiceSubmitter",
    "EInvoiceManager",
    "EReportingManager",
    "EInvoiceStatsManager",
    "WebhookHandler",
    "InboundInvoiceHandler",
    "LifecycleManager",
    "EInvoiceXMLParser",
    "get_xml_parser",
    "XMLParsingError",
    "build_seller_from_tenant",
    "build_buyer_from_customer",
    "build_seller_from_supplier",
    "calculate_vat_breakdown",
    "calculate_vat_breakdown_purchase",
    "build_invoice_data",
]
