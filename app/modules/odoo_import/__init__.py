"""
AZALS MODULE - Odoo Import
==========================

Module d'import de donnees depuis Odoo (versions 8-18).
Supporte:
- Import des produits (product.product)
- Import des contacts/clients (res.partner)
- Import des fournisseurs (res.partner avec supplier_rank)
- Import des commandes d'achat (purchase.order)

Compatible avec Odoo versions 8 a 18 via XML-RPC.
"""

from .connector import OdooConnector
from .mapper import OdooMapper
from .models import OdooConnectionConfig, OdooImportStatus, OdooSyncType
from .router import router as odoo_import_router
from .service import OdooImportService

__all__ = [
    "OdooConnector",
    "OdooConnectionConfig",
    "OdooImportService",
    "OdooImportStatus",
    "OdooMapper",
    "OdooSyncType",
    "odoo_import_router",
]
