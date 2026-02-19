"""
AZALSCORE Finance Invoice OCR Router V3
========================================

Endpoints REST pour l'OCR des factures fournisseurs.

Endpoints:
- POST /v3/finance/invoice-ocr/extract - Extraire données d'une facture
- POST /v3/finance/invoice-ocr/batch - Traitement par lot
- GET  /v3/finance/invoice-ocr/status/{job_id} - Statut d'un job
- GET  /v3/finance/invoice-ocr/health - Health check
"""

import logging
import os
import tempfile
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    InvoiceOCRService,
    InvoiceExtraction,
    ExtractionResult,
    InvoiceType,
    ValidationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/invoice-ocr", tags=["Finance Invoice OCR"])


# =============================================================================
# SCHEMAS
# =============================================================================


class VendorResponse(BaseModel):
    """Fournisseur extrait."""

    name: str
    siret: Optional[str] = None
    tva_number: Optional[str] = None
    iban: Optional[str] = None
    address: Optional[str] = None
    confidence: float = 0.0
    matched_partner_id: Optional[str] = None


class LineItemResponse(BaseModel):
    """Ligne de facture extraite."""

    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    tva_rate: Optional[Decimal] = None
    confidence: float = 0.0


class ExtractionResponse(BaseModel):
    """Résultat d'extraction de facture."""

    id: str
    success: bool
    error: Optional[str] = None

    # Type et confiance
    invoice_type: str = "unknown"
    confidence: float = 0.0

    # Références
    invoice_number: Optional[str] = None
    invoice_number_confidence: float = 0.0
    order_reference: Optional[str] = None

    # Dates
    invoice_date: Optional[str] = None
    invoice_date_confidence: float = 0.0
    due_date: Optional[str] = None
    due_date_confidence: float = 0.0

    # Fournisseur
    vendor: Optional[VendorResponse] = None

    # Montants
    amount_untaxed: Optional[Decimal] = None
    amount_untaxed_confidence: float = 0.0
    amount_tax: Optional[Decimal] = None
    amount_tax_confidence: float = 0.0
    amount_total: Optional[Decimal] = None
    amount_total_confidence: float = 0.0
    currency: str = "EUR"

    # Lignes
    line_items: list[LineItemResponse] = Field(default_factory=list)

    # Métadonnées
    page_count: int = 1
    processing_time_ms: int = 0
    file_hash: Optional[str] = None

    # Validation
    tva_validated: str = "unverified"
    amounts_consistent: bool = False
    warnings: list[str] = Field(default_factory=list)


class BatchRequest(BaseModel):
    """Requête de traitement par lot."""

    file_ids: list[str] = Field(..., min_length=1, max_length=50)
    check_duplicates: bool = True


class BatchResponse(BaseModel):
    """Réponse de traitement par lot."""

    job_id: str
    total: int
    processed: int
    successful: int
    failed: int
    results: list[ExtractionResponse] = Field(default_factory=list)


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_invoice_ocr_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> InvoiceOCRService:
    """Dépendance pour obtenir le service OCR factures."""
    return InvoiceOCRService(db=db, tenant_id=context.tenant_id)


def extraction_to_response(result: ExtractionResult) -> ExtractionResponse:
    """Convertit un résultat d'extraction en réponse API."""
    if not result.success or not result.extraction:
        return ExtractionResponse(
            id=str(UUID(int=0)),
            success=False,
            error=result.error,
            file_hash=result.file_hash,
        )

    ext = result.extraction

    # Convertir le vendor
    vendor_response = None
    if ext.vendor:
        vendor_response = VendorResponse(
            name=ext.vendor.name,
            siret=ext.vendor.siret,
            tva_number=ext.vendor.tva_number,
            iban=ext.vendor.iban,
            address=ext.vendor.address,
            confidence=ext.vendor.confidence,
            matched_partner_id=str(ext.vendor.matched_partner_id) if ext.vendor.matched_partner_id else None,
        )

    # Convertir les lignes
    line_items = [
        LineItemResponse(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total,
            tva_rate=item.tva_rate,
            confidence=item.confidence,
        )
        for item in ext.line_items
    ]

    return ExtractionResponse(
        id=ext.id,
        success=True,
        invoice_type=ext.invoice_type.value,
        confidence=ext.confidence,
        invoice_number=ext.invoice_number,
        invoice_number_confidence=ext.invoice_number_confidence,
        order_reference=ext.order_reference,
        invoice_date=ext.invoice_date.isoformat() if ext.invoice_date else None,
        invoice_date_confidence=ext.invoice_date_confidence,
        due_date=ext.due_date.isoformat() if ext.due_date else None,
        due_date_confidence=ext.due_date_confidence,
        vendor=vendor_response,
        amount_untaxed=ext.amount_untaxed,
        amount_untaxed_confidence=ext.amount_untaxed_confidence,
        amount_tax=ext.amount_tax,
        amount_tax_confidence=ext.amount_tax_confidence,
        amount_total=ext.amount_total,
        amount_total_confidence=ext.amount_total_confidence,
        currency=ext.currency,
        line_items=line_items,
        page_count=ext.page_count,
        processing_time_ms=ext.processing_time_ms,
        file_hash=result.file_hash,
        tva_validated=ext.tva_validated.value,
        amounts_consistent=ext.amounts_consistent,
        warnings=ext.warnings,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="Extraire les données d'une facture",
    description="Upload et extraction OCR d'une facture fournisseur.",
)
async def extract_invoice(
    file: UploadFile = File(..., description="Fichier facture (PDF, PNG, JPG)"),
    check_duplicate: bool = Form(True, description="Vérifier les doublons"),
    service: InvoiceOCRService = Depends(get_invoice_ocr_service),
):
    """
    Extrait les données d'une facture fournisseur.

    Champs extraits:
    - Numéro de facture
    - Date de facture et d'échéance
    - Montants HT, TVA, TTC
    - Informations fournisseur (nom, SIRET, TVA, IBAN)
    - Lignes de facture

    Formats supportés: PDF, PNG, JPG, JPEG, TIFF
    """
    # Vérifier le type de fichier
    allowed_types = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/tiff",
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non supporté: {file.content_type}. "
            f"Formats acceptés: PDF, PNG, JPG, TIFF",
        )

    # Sauvegarder temporairement le fichier
    suffix = os.path.splitext(file.filename or "")[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Traiter la facture
        result = await service.process_invoice(
            file_path=tmp_path,
            check_duplicate=check_duplicate,
        )

        return extraction_to_response(result)

    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post(
    "/extract-url",
    response_model=ExtractionResponse,
    summary="Extraire depuis une URL",
    description="Extraction OCR depuis un fichier accessible par URL.",
)
async def extract_invoice_from_url(
    url: str = Form(..., description="URL du fichier facture"),
    check_duplicate: bool = Form(True, description="Vérifier les doublons"),
    service: InvoiceOCRService = Depends(get_invoice_ocr_service),
):
    """
    Extrait les données d'une facture depuis une URL.

    L'URL doit pointer vers un fichier accessible (PDF, image).
    """
    import httpx

    # Télécharger le fichier
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de télécharger le fichier: {e}",
        )

    # Déterminer l'extension
    content_type = response.headers.get("content-type", "")
    if "pdf" in content_type:
        suffix = ".pdf"
    elif "png" in content_type:
        suffix = ".png"
    elif "jpeg" in content_type or "jpg" in content_type:
        suffix = ".jpg"
    else:
        suffix = ".pdf"

    # Sauvegarder temporairement
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await service.process_invoice(
            file_path=tmp_path,
            check_duplicate=check_duplicate,
        )
        return extraction_to_response(result)

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post(
    "/validate-amounts",
    summary="Valider la cohérence des montants",
    description="Vérifie que HT + TVA = TTC.",
)
async def validate_amounts(
    amount_ht: Decimal = Form(..., description="Montant HT"),
    amount_tva: Decimal = Form(..., description="Montant TVA"),
    amount_ttc: Decimal = Form(..., description="Montant TTC"),
    tolerance: Decimal = Form(Decimal("0.02"), description="Tolérance en euros"),
):
    """
    Valide la cohérence des montants d'une facture.

    Vérifie que: HT + TVA = TTC (avec tolérance pour arrondis)
    """
    expected = amount_ht + amount_tva
    diff = abs(expected - amount_ttc)

    return {
        "valid": diff <= tolerance,
        "expected_ttc": expected,
        "actual_ttc": amount_ttc,
        "difference": diff,
        "tolerance": tolerance,
        "tva_rate_detected": (
            round(float(amount_tva / amount_ht * 100), 1)
            if amount_ht > 0
            else None
        ),
    }


@router.post(
    "/validate-siret",
    summary="Valider un numéro SIRET",
    description="Vérifie la validité d'un numéro SIRET (algorithme de Luhn).",
)
async def validate_siret(
    siret: str = Form(..., description="Numéro SIRET (14 chiffres)"),
):
    """
    Valide un numéro SIRET avec l'algorithme de Luhn.
    """
    siret_clean = siret.replace(" ", "")

    if len(siret_clean) != 14:
        return {
            "valid": False,
            "error": "Le SIRET doit contenir 14 chiffres",
            "siret": siret_clean,
        }

    if not siret_clean.isdigit():
        return {
            "valid": False,
            "error": "Le SIRET ne doit contenir que des chiffres",
            "siret": siret_clean,
        }

    # Algorithme de Luhn
    total = 0
    for i, digit in enumerate(siret_clean):
        d = int(digit)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    is_valid = total % 10 == 0

    return {
        "valid": is_valid,
        "siret": siret_clean,
        "siren": siret_clean[:9] if is_valid else None,
        "nic": siret_clean[9:] if is_valid else None,
    }


@router.get(
    "/supported-formats",
    summary="Formats de fichiers supportés",
    description="Liste les formats de fichiers acceptés pour l'OCR.",
)
async def get_supported_formats():
    """Retourne les formats de fichiers supportés."""
    return {
        "formats": [
            {"extension": ".pdf", "mime_type": "application/pdf", "description": "Document PDF"},
            {"extension": ".png", "mime_type": "image/png", "description": "Image PNG"},
            {"extension": ".jpg", "mime_type": "image/jpeg", "description": "Image JPEG"},
            {"extension": ".jpeg", "mime_type": "image/jpeg", "description": "Image JPEG"},
            {"extension": ".tiff", "mime_type": "image/tiff", "description": "Image TIFF"},
        ],
        "max_file_size_mb": 20,
        "max_pages": 50,
    }


@router.get(
    "/health",
    summary="Health check OCR factures",
    description="Vérifie que le service OCR est fonctionnel.",
)
async def health_check():
    """Health check pour le service OCR factures."""
    # Vérifier si Tesseract est disponible
    tesseract_available = False
    try:
        from app.modules.automated_accounting.services.ocr_service import TesseractEngine
        engine = TesseractEngine()
        tesseract_available = engine._tesseract_available
    except Exception:
        pass

    return {
        "status": "healthy",
        "service": "finance-invoice-ocr",
        "engines": {
            "tesseract": "available" if tesseract_available else "not_available",
            "mock": "available",
        },
        "features": [
            "invoice_extraction",
            "amount_validation",
            "siret_validation",
            "vendor_matching",
            "duplicate_detection",
        ],
    }
