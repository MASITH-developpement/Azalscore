"""
AZALSCORE Finance Invoice OCR
==============================

Service OCR spécialisé pour les factures fournisseurs.

Fonctionnalités:
- Extraction intelligente des données facture
- Matching automatique fournisseur
- Validation croisée TVA/SIRET
- Intégration comptable automatique
- Batch processing

Usage:
    from app.modules.finance.invoice_ocr import InvoiceOCRService

    service = InvoiceOCRService(db, tenant_id)
    result = await service.process_invoice(file_path)
"""

from .service import InvoiceOCRService, InvoiceExtraction, ExtractionResult
from .router import router as invoice_ocr_router

__all__ = [
    "InvoiceOCRService",
    "InvoiceExtraction",
    "ExtractionResult",
    "invoice_ocr_router",
]
