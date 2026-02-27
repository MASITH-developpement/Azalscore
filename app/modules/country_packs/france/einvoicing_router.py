"""
AZALS - Router E-Invoicing France 2026
=======================================

Endpoints REST pour la facturation électronique.
Multi-tenant avec authentification.
"""
from __future__ import annotations


import logging
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User
from app.modules.country_packs.france.einvoicing_schemas import (
    BulkGenerateRequest,
    BulkGenerateResponse,
    BulkSubmitRequest,
    BulkSubmitResponse,
    EInvoiceCreateFromSource,
    EInvoiceCreateManual,
    EInvoiceDashboard,
    EInvoiceDetailResponse,
    EInvoiceDirection,
    EInvoiceFilter,
    EInvoiceFormat,
    EInvoiceListResponse,
    EInvoiceResponse,
    EInvoiceStatus,
    EInvoiceStatusUpdate,
    EInvoiceStatsSummary,
    EInvoiceSubmitResponse,
    EInvoiceValidateRequest,
    EReportingCreate,
    EReportingListResponse,
    EReportingResponse,
    EReportingSubmitResponse,
    InboundBatchRequest,
    InboundBatchResponse,
    InboundInvoiceParsed,
    InboundInvoiceResponse,
    InboundInvoiceXML,
    LifecycleEventResponse,
    PDPConfigCreate,
    PDPConfigListResponse,
    PDPConfigResponse,
    PDPConfigUpdate,
    PDPProviderType,
    PDPWebhookPayload,
    ValidationResult,
    WebhookResponse,
)
from app.modules.country_packs.france.einvoicing_service import get_einvoicing_service
from app.modules.country_packs.france.einvoicing_autogen import (
    EInvoiceAutogenService,
    get_autogen_service,
    AutogenResult,
    AutogenSuggestion,
    AutogenConfidence,
    DocumentContext,
)
from app.modules.country_packs.france.exceptions import (
    EInvoicingError,
    EInvoicingValidationError,
    EInvoicingSubmissionError,
    EInvoicingStatusError,
    PDPError,
    PDPAPIError,
    PDPConnectionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/france/einvoicing",
    tags=["France - Facturation Électronique"]
)


# =============================================================================
# CONFIGURATION PDP
# =============================================================================

@router.get("/pdp-configs", response_model=PDPConfigListResponse)
async def list_pdp_configs(
    active_only: bool = Query(True, description="Filtrer les configs actives"),
    provider: PDPProviderType | None = Query(None, description="Filtrer par provider"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les configurations PDP du tenant.

    Retourne toutes les configurations PDP avec leur statut.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)
    configs = service.list_pdp_configs(active_only=active_only, provider=provider)

    return PDPConfigListResponse(
        items=[_config_to_response(c) for c in configs],
        total=len(configs)
    )


@router.get("/pdp-configs/default", response_model=PDPConfigResponse | None)
async def get_default_pdp_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère la configuration PDP par défaut."""
    service = get_einvoicing_service(db, current_user.tenant_id)
    config = service.get_default_pdp_config()

    if not config:
        return None

    return _config_to_response(config)


@router.get("/pdp-configs/{config_id}", response_model=PDPConfigResponse)
async def get_pdp_config(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère une configuration PDP par son ID."""
    service = get_einvoicing_service(db, current_user.tenant_id)
    config = service.get_pdp_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Configuration PDP non trouvée")

    return _config_to_response(config)


@router.post("/pdp-configs", response_model=PDPConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_pdp_config(
    data: PDPConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une nouvelle configuration PDP.

    Permet de configurer un provider PDP (Chorus Pro, PPF, Yooz, etc.)
    pour la soumission de factures électroniques.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        config = service.create_pdp_config(data, created_by=current_user.id)
        return _config_to_response(config)
    except (PDPError, PDPConnectionError, ValueError) as e:
        logger.error(f"Erreur creation config PDP: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/pdp-configs/{config_id}", response_model=PDPConfigResponse)
async def update_pdp_config(
    config_id: UUID,
    data: PDPConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met à jour une configuration PDP."""
    service = get_einvoicing_service(db, current_user.tenant_id)

    config = service.update_pdp_config(config_id, data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration PDP non trouvée")

    return _config_to_response(config)


@router.delete("/pdp-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdp_config(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime une configuration PDP.

    Si des factures sont liées, la configuration est désactivée au lieu d'être supprimée.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    if not service.delete_pdp_config(config_id):
        raise HTTPException(status_code=404, detail="Configuration PDP non trouvée")


# =============================================================================
# FACTURES ÉLECTRONIQUES
# =============================================================================

@router.get("/einvoices", response_model=EInvoiceListResponse)
async def list_einvoices(
    direction: EInvoiceDirection | None = Query(None),
    status: EInvoiceStatus | None = Query(None),
    format: EInvoiceFormat | None = Query(None),
    pdp_config_id: UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    seller_siret: str | None = Query(None),
    buyer_siret: str | None = Query(None),
    search: str | None = Query(None, description="Recherche par numéro, nom, PPF/PDP ID"),
    source_type: str | None = Query(None),
    has_errors: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les factures électroniques du tenant.

    Supporte de nombreux filtres pour retrouver rapidement les factures.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    filters = EInvoiceFilter(
        direction=direction,
        status=status,
        format=format,
        pdp_config_id=pdp_config_id,
        date_from=date_from,
        date_to=date_to,
        seller_siret=seller_siret,
        buyer_siret=buyer_siret,
        search=search,
        source_type=source_type,
        has_errors=has_errors
    )

    items, total = service.list_einvoices(filters=filters, page=page, page_size=page_size)

    return EInvoiceListResponse(
        items=[EInvoiceResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/einvoices/{einvoice_id}", response_model=EInvoiceDetailResponse)
async def get_einvoice(
    einvoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le détail d'une facture électronique.

    Inclut le contenu XML, les événements du cycle de vie et les métadonnées.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)
    einvoice = service.get_einvoice_detail(einvoice_id)

    if not einvoice:
        raise HTTPException(status_code=404, detail="Facture électronique non trouvée")

    return EInvoiceDetailResponse(
        id=einvoice.id,
        tenant_id=einvoice.tenant_id,
        direction=EInvoiceDirection(einvoice.direction.value),
        invoice_number=einvoice.invoice_number,
        invoice_type=einvoice.invoice_type,
        format=EInvoiceFormat(einvoice.format.value),
        status=EInvoiceStatus(einvoice.status.value),
        lifecycle_status=einvoice.lifecycle_status,
        issue_date=einvoice.issue_date,
        due_date=einvoice.due_date,
        currency=einvoice.currency,
        total_ht=einvoice.total_ht,
        total_tva=einvoice.total_tva,
        total_ttc=einvoice.total_ttc,
        vat_breakdown=einvoice.vat_breakdown,
        seller_name=einvoice.seller_name,
        seller_siret=einvoice.seller_siret,
        buyer_name=einvoice.buyer_name,
        buyer_siret=einvoice.buyer_siret,
        transaction_id=einvoice.transaction_id,
        ppf_id=einvoice.ppf_id,
        pdp_id=einvoice.pdp_id,
        source_type=einvoice.source_type,
        source_invoice_id=einvoice.source_invoice_id,
        is_valid=einvoice.is_valid,
        validation_errors=einvoice.validation_errors or [],
        validation_warnings=einvoice.validation_warnings or [],
        last_error=einvoice.last_error,
        submission_date=einvoice.submission_date,
        pdp_config_id=einvoice.pdp_config_id,
        created_at=einvoice.created_at,
        updated_at=einvoice.updated_at,
        xml_content=einvoice.xml_content,
        xml_hash=einvoice.xml_hash,
        pdf_storage_ref=einvoice.pdf_storage_ref,
        lifecycle_events=[
            LifecycleEventResponse.model_validate(e)
            for e in einvoice.lifecycle_events
        ],
        metadata=einvoice.extra_data or {}
    )


@router.post("/einvoices/from-source", response_model=EInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_einvoice_from_source(
    data: EInvoiceCreateFromSource,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une facture électronique depuis un document source.

    Supporte:
    - INVOICE: Facture client (CommercialDocument)
    - CREDIT_NOTE: Avoir client (CommercialDocument)
    - PURCHASE_INVOICE: Facture fournisseur (LegacyPurchaseInvoice)
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        einvoice = service.create_einvoice_from_source(data, created_by=current_user.id)
        return EInvoiceResponse.model_validate(einvoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (EInvoicingError, EInvoicingValidationError) as e:
        logger.error(f"Erreur creation e-invoice: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la creation")


@router.post("/einvoices/manual", response_model=EInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_einvoice_manual(
    data: EInvoiceCreateManual,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une facture électronique manuellement.

    Permet de créer une facture sans document source existant.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        einvoice = service.create_einvoice_manual(data, created_by=current_user.id)
        return EInvoiceResponse.model_validate(einvoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (EInvoicingError, EInvoicingValidationError) as e:
        logger.error(f"Erreur creation e-invoice manuelle: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la creation")


@router.post("/einvoices/{einvoice_id}/submit", response_model=EInvoiceSubmitResponse)
async def submit_einvoice(
    einvoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soumet une facture électronique au PDP.

    La facture doit être valide (is_valid=true) pour être soumise.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        response = service.submit_einvoice(einvoice_id, submitted_by=current_user.id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (EInvoicingSubmissionError, PDPAPIError, PDPConnectionError) as e:
        logger.error(f"Erreur soumission e-invoice: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la soumission")


@router.post("/einvoices/{einvoice_id}/validate", response_model=ValidationResult)
async def validate_einvoice(
    einvoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Valide une facture électronique.

    Vérifie la conformité du XML Factur-X selon le profil.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        result = service.validate_einvoice(einvoice_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/einvoices/{einvoice_id}/status", response_model=EInvoiceResponse)
async def update_einvoice_status(
    einvoice_id: UUID,
    data: EInvoiceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour le statut d'une facture électronique.

    Utilisé principalement pour les mises à jour manuelles ou via webhook.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    einvoice = service.update_einvoice_status(einvoice_id, data)
    if not einvoice:
        raise HTTPException(status_code=404, detail="Facture électronique non trouvée")

    return EInvoiceResponse.model_validate(einvoice)


@router.get("/einvoices/{einvoice_id}/xml")
async def get_einvoice_xml(
    einvoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le contenu XML d'une facture.

    Retourne le XML Factur-X brut.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)
    einvoice = service.get_einvoice(einvoice_id)

    if not einvoice:
        raise HTTPException(status_code=404, detail="Facture électronique non trouvée")

    if not einvoice.xml_content:
        raise HTTPException(status_code=404, detail="Aucun contenu XML disponible")

    from fastapi.responses import Response
    return Response(
        content=einvoice.xml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="facturx-{einvoice.invoice_number}.xml"'
        }
    )


@router.get("/einvoices/{einvoice_id}/pdf")
async def get_einvoice_pdf(
    einvoice_id: UUID,
    embed_xml: bool = Query(True, description="Embarquer le XML dans le PDF (Factur-X)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère et retourne le PDF Factur-X de la facture.

    Par défaut, génère un PDF/A-3 avec XML embarqué (conforme Factur-X).
    Utiliser embed_xml=false pour obtenir uniquement le PDF visuel.
    """
    from fastapi.responses import Response
    from app.modules.country_packs.france.einvoicing_pdf_generator import (
        FacturXPDFGenerator,
        FacturXProfile,
        convert_einvoice_to_pdf_data,
    )

    service = get_einvoicing_service(db, current_user.tenant_id)
    einvoice = service.get_einvoice(einvoice_id)

    if not einvoice:
        raise HTTPException(status_code=404, detail="Facture électronique non trouvée")

    # Convertir les données pour le générateur PDF
    pdf_data = convert_einvoice_to_pdf_data(einvoice)

    # Déterminer le profil Factur-X depuis le format
    profile_mapping = {
        "FACTURX_MINIMUM": FacturXProfile.MINIMUM,
        "FACTURX_BASIC": FacturXProfile.BASIC,
        "FACTURX_EN16931": FacturXProfile.EN16931,
        "FACTURX_EXTENDED": FacturXProfile.EXTENDED,
    }
    profile = profile_mapping.get(einvoice.format.value, FacturXProfile.EN16931)

    # Générer le PDF
    generator = FacturXPDFGenerator()

    if embed_xml and einvoice.xml_content:
        pdf_content = generator.generate_facturx_pdf(
            invoice_data=pdf_data,
            xml_content=einvoice.xml_content,
            profile=profile
        )
        filename = f"facturx-{einvoice.invoice_number}.pdf"
    else:
        pdf_content = generator.generate_visual_pdf_only(invoice_data=pdf_data)
        filename = f"facture-{einvoice.invoice_number}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/einvoices/{einvoice_id}/generate-pdf")
async def generate_and_store_pdf(
    einvoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère et stocke le PDF Factur-X pour une facture.

    Le PDF est généré avec XML embarqué et la référence de stockage
    est enregistrée dans la facture.
    """
    import base64
    from app.modules.country_packs.france.einvoicing_pdf_generator import (
        FacturXPDFGenerator,
        FacturXProfile,
        convert_einvoice_to_pdf_data,
    )

    service = get_einvoicing_service(db, current_user.tenant_id)
    einvoice = service.get_einvoice(einvoice_id)

    if not einvoice:
        raise HTTPException(status_code=404, detail="Facture électronique non trouvée")

    if not einvoice.xml_content:
        raise HTTPException(status_code=400, detail="Aucun contenu XML disponible pour générer le PDF")

    # Convertir et générer
    pdf_data = convert_einvoice_to_pdf_data(einvoice)

    profile_mapping = {
        "FACTURX_MINIMUM": FacturXProfile.MINIMUM,
        "FACTURX_BASIC": FacturXProfile.BASIC,
        "FACTURX_EN16931": FacturXProfile.EN16931,
        "FACTURX_EXTENDED": FacturXProfile.EXTENDED,
    }
    profile = profile_mapping.get(einvoice.format.value, FacturXProfile.EN16931)

    generator = FacturXPDFGenerator()
    pdf_content = generator.generate_facturx_pdf(
        invoice_data=pdf_data,
        xml_content=einvoice.xml_content,
        profile=profile
    )

    # Stocker la référence (TODO: intégrer avec un service de stockage)
    pdf_storage_ref = f"einvoices/{current_user.tenant_id}/{einvoice.id}.pdf"
    einvoice.pdf_storage_ref = pdf_storage_ref
    db.commit()

    return {
        "einvoice_id": str(einvoice.id),
        "pdf_storage_ref": pdf_storage_ref,
        "pdf_size_bytes": len(pdf_content),
        "pdf_base64": base64.b64encode(pdf_content).decode(),
        "profile": profile.value,
        "message": "PDF Factur-X généré avec succès"
    }


@router.post("/pdf/preview")
async def preview_pdf(
    invoice_number: str = Query(..., description="Numéro de facture"),
    issue_date: date = Query(..., description="Date d'émission"),
    seller_name: str = Query("Entreprise Test", description="Nom vendeur"),
    seller_siret: str | None = Query(None, description="SIRET vendeur"),
    buyer_name: str = Query("Client Test", description="Nom acheteur"),
    buyer_siret: str | None = Query(None, description="SIRET acheteur"),
    total_ht: float = Query(1000.0, description="Total HT"),
    total_tva: float = Query(200.0, description="Total TVA"),
    total_ttc: float = Query(1200.0, description="Total TTC"),
    current_user: User = Depends(get_current_user)
):
    """
    Génère une prévisualisation PDF sans enregistrer.

    Utile pour tester la mise en page avant génération finale.
    Retourne le PDF encodé en base64.
    """
    import base64
    from decimal import Decimal
    from app.modules.country_packs.france.einvoicing_pdf_generator import (
        FacturXPDFGenerator,
        InvoiceData,
        InvoiceParty,
        InvoiceLine,
    )

    # Construire les données de prévisualisation
    seller = InvoiceParty(
        name=seller_name,
        siret=seller_siret,
    )

    buyer = InvoiceParty(
        name=buyer_name,
        siret=buyer_siret,
    )

    # Ligne de démonstration
    lines = [
        InvoiceLine(
            line_number=1,
            description="Prestation de services",
            quantity=Decimal("1"),
            unit="C62",
            unit_price=Decimal(str(total_ht)),
            vat_rate=Decimal("20"),
            net_amount=Decimal(str(total_ht)),
            vat_amount=Decimal(str(total_tva)),
            total_amount=Decimal(str(total_ttc)),
        )
    ]

    invoice_data = InvoiceData(
        invoice_number=invoice_number,
        invoice_type="380",
        issue_date=issue_date,
        seller=seller,
        buyer=buyer,
        lines=lines,
        total_ht=Decimal(str(total_ht)),
        total_tva=Decimal(str(total_tva)),
        total_ttc=Decimal(str(total_ttc)),
        vat_breakdown={"20.0": total_tva},
    )

    generator = FacturXPDFGenerator()
    pdf_content = generator.generate_visual_pdf_only(invoice_data)

    return {
        "pdf_base64": base64.b64encode(pdf_content).decode(),
        "pdf_size_bytes": len(pdf_content),
        "message": "Prévisualisation PDF générée"
    }


# =============================================================================
# OPÉRATIONS EN MASSE
# =============================================================================

@router.post("/einvoices/bulk/generate", response_model=BulkGenerateResponse)
async def bulk_generate_einvoices(
    data: BulkGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère des factures électroniques en masse depuis des documents sources.

    Maximum 100 documents par requête.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        response = service.bulk_generate(data, created_by=current_user.id)
        return response
    except (EInvoicingError, EInvoicingValidationError, ValueError) as e:
        logger.error(f"Erreur generation en masse: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la generation")


@router.post("/einvoices/bulk/submit", response_model=BulkSubmitResponse)
async def bulk_submit_einvoices(
    data: BulkSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soumet des factures électroniques en masse.

    Maximum 100 factures par requête.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        response = service.bulk_submit(data, submitted_by=current_user.id)
        return response
    except (EInvoicingSubmissionError, PDPAPIError, PDPConnectionError, ValueError) as e:
        logger.error(f"Erreur soumission en masse: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la soumission")


# =============================================================================
# RÉCEPTION FACTURES ENTRANTES (INBOUND)
# =============================================================================

@router.post("/einvoices/inbound/xml", response_model=InboundInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def receive_inbound_xml(
    data: InboundInvoiceXML,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reçoit une facture entrante via XML Factur-X ou UBL.

    Le XML est parsé automatiquement pour extraire:
    - Numéro de facture et type
    - Parties (vendeur/acheteur avec SIRET/TVA)
    - Montants et TVA
    - Dates

    La facture est enregistrée avec le statut RECEIVED.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        einvoice, validation = service.receive_inbound_xml(
            xml_content=data.xml_content,
            source_pdp=data.source_pdp,
            ppf_id=data.ppf_id,
            pdp_id=data.pdp_id,
            pdf_base64=data.pdf_base64,
            received_by=current_user.id,
            metadata=data.metadata
        )

        return InboundInvoiceResponse(
            einvoice_id=einvoice.id,
            invoice_number=einvoice.invoice_number,
            seller_name=einvoice.seller_name,
            seller_siret=einvoice.seller_siret,
            total_ttc=einvoice.total_ttc,
            status=EInvoiceStatus(einvoice.status.value),
            validation_result=ValidationResult(
                is_valid=validation.get("valid", True),
                errors=validation.get("errors", []),
                warnings=validation.get("warnings", []),
                profile=validation.get("profile"),
                format=EInvoiceFormat(einvoice.format.value)
            ),
            message="Facture entrante reçue avec succès",
            received_at=einvoice.reception_date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (EInvoicingError, EInvoicingValidationError) as e:
        logger.error(f"Erreur reception facture entrante: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la reception")


@router.post("/einvoices/inbound/parsed", response_model=InboundInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def receive_inbound_parsed(
    data: InboundInvoiceParsed,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reçoit une facture entrante avec données déjà parsées.

    Utilisé quand le parsing XML a déjà été fait en amont
    (par exemple par le PDP ou un système tiers).
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        einvoice, validation = service.receive_inbound_parsed(
            data=data.model_dump(),
            received_by=current_user.id
        )

        return InboundInvoiceResponse(
            einvoice_id=einvoice.id,
            invoice_number=einvoice.invoice_number,
            seller_name=einvoice.seller_name,
            seller_siret=einvoice.seller_siret,
            total_ttc=einvoice.total_ttc,
            status=EInvoiceStatus(einvoice.status.value),
            validation_result=ValidationResult(
                is_valid=validation.get("valid", True),
                errors=validation.get("errors", []),
                warnings=validation.get("warnings", []),
                profile=validation.get("profile"),
                format=EInvoiceFormat(einvoice.format.value)
            ),
            message="Facture entrante enregistrée",
            received_at=einvoice.reception_date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (EInvoicingError, EInvoicingValidationError) as e:
        logger.error(f"Erreur reception facture parsee: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la reception")


@router.post("/einvoices/inbound/batch", response_model=InboundBatchResponse)
async def receive_inbound_batch(
    data: InboundBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reçoit un lot de factures entrantes.

    Maximum 50 factures par requête.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    results = []
    received = 0
    failed = 0

    for invoice_data in data.invoices:
        try:
            einvoice, validation = service.receive_inbound_xml(
                xml_content=invoice_data.xml_content,
                source_pdp=invoice_data.source_pdp,
                ppf_id=invoice_data.ppf_id,
                pdp_id=invoice_data.pdp_id,
                pdf_base64=invoice_data.pdf_base64,
                received_by=current_user.id,
                metadata=invoice_data.metadata
            )
            results.append({
                "einvoice_id": str(einvoice.id),
                "invoice_number": einvoice.invoice_number,
                "status": "received"
            })
            received += 1
        except (EInvoicingError, EInvoicingValidationError, ValueError) as e:
            results.append({
                "ppf_id": invoice_data.ppf_id,
                "pdp_id": invoice_data.pdp_id,
                "status": "failed",
                "error": str(e)
            })
            failed += 1

    return InboundBatchResponse(
        total=len(data.invoices),
        received=received,
        failed=failed,
        results=results
    )


@router.post("/einvoices/{einvoice_id}/accept", response_model=EInvoiceResponse)
async def accept_inbound_invoice(
    einvoice_id: UUID,
    message: str | None = Query(None, description="Message d'acceptation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepte une facture entrante.

    Change le statut de RECEIVED à ACCEPTED.
    Notifie le fournisseur via le PDP/PPF.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        einvoice = service.accept_inbound_invoice(
            einvoice_id=einvoice_id,
            accepted_by=current_user.id,
            message=message
        )
        return EInvoiceResponse.model_validate(einvoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/einvoices/{einvoice_id}/refuse", response_model=EInvoiceResponse)
async def refuse_inbound_invoice(
    einvoice_id: UUID,
    reason: str = Query(..., description="Motif du refus"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Refuse une facture entrante.

    Change le statut de RECEIVED à REFUSED.
    Le motif de refus est obligatoire et sera transmis au fournisseur.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        einvoice = service.refuse_inbound_invoice(
            einvoice_id=einvoice_id,
            refused_by=current_user.id,
            reason=reason
        )
        return EInvoiceResponse.model_validate(einvoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# E-REPORTING
# =============================================================================

@router.get("/ereporting", response_model=EReportingListResponse)
async def list_ereporting(
    period: str | None = Query(None, description="Période YYYY-MM"),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les soumissions e-reporting."""
    service = get_einvoicing_service(db, current_user.tenant_id)

    items, total = service.list_ereporting(
        period=period,
        status=status,
        page=page,
        page_size=page_size
    )

    return EReportingListResponse(
        items=[EReportingResponse.model_validate(item) for item in items],
        total=total
    )


@router.post("/ereporting", response_model=EReportingResponse, status_code=status.HTTP_201_CREATED)
async def create_ereporting(
    data: EReportingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une soumission e-reporting.

    Pour les transactions B2C et internationales.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        submission = service.create_ereporting(data, created_by=current_user.id)
        return EReportingResponse.model_validate(submission)
    except (EInvoicingError, EInvoicingValidationError, ValueError) as e:
        logger.error(f"Erreur creation e-reporting: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ereporting/{ereporting_id}/submit", response_model=EReportingSubmitResponse)
async def submit_ereporting(
    ereporting_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soumet l'e-reporting au PPF."""
    service = get_einvoicing_service(db, current_user.tenant_id)

    try:
        response = service.submit_ereporting(ereporting_id, submitted_by=current_user.id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# STATISTIQUES ET DASHBOARD
# =============================================================================

@router.get("/stats", response_model=EInvoiceStatsSummary)
async def get_stats_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le résumé des statistiques e-invoicing.

    Inclut les stats du mois courant, précédent et YTD.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)
    return service.get_stats_summary()


@router.get("/dashboard", response_model=EInvoiceDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les données du dashboard e-invoicing.

    Vue d'ensemble: configs, stats, factures récentes, alertes.
    """
    service = get_einvoicing_service(db, current_user.tenant_id)
    return service.get_dashboard()


# =============================================================================
# WEBHOOKS
# =============================================================================

class WebhookTestRequest(BaseModel):
    """Requête de test webhook."""
    einvoice_id: UUID | None = None
    event_type: str = "test.ping"
    message: str = "Test webhook from AZALS"


class WebhookTestResponse(BaseModel):
    """Réponse de test webhook."""
    total_webhooks: int
    results: list[dict]


@router.post("/webhooks/test", response_model=WebhookTestResponse)
async def test_webhooks(
    data: WebhookTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Teste les webhooks configurés pour le tenant.

    Envoie un événement de test à toutes les URLs webhook configurées.
    """
    from app.modules.country_packs.france.einvoicing_webhooks import (
        WebhookNotificationService,
        WebhookPayload,
    )

    service = get_einvoicing_service(db, current_user.tenant_id)
    webhook_service = WebhookNotificationService(db)

    # Construire un payload de test
    test_payload = {
        "event_type": data.event_type,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "tenant_id": current_user.tenant_id,
            "test": True,
        },
        "message": data.message
    }

    # Si une facture est spécifiée, utiliser ses données
    if data.einvoice_id:
        einvoice = service.get_einvoice(data.einvoice_id)
        if einvoice:
            test_payload = WebhookPayload.from_einvoice(
                einvoice,
                data.event_type,
                message=data.message
            )

    # Récupérer les webhooks configurés
    webhooks = webhook_service._get_configured_webhooks(current_user.tenant_id)

    results = []
    async with webhook_service:
        for webhook in webhooks:
            result = await webhook_service._send_webhook(
                url=webhook["url"],
                payload=test_payload,
                secret=webhook.get("secret"),
                config_id=webhook.get("config_id"),
                retry_count=1  # Pas de retry pour les tests
            )
            results.append(result)

    return WebhookTestResponse(
        total_webhooks=len(webhooks),
        results=results
    )


@router.get("/webhooks/configs")
async def list_webhook_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste les configurations webhook du tenant.

    Retourne les URLs webhook configurées (sans les secrets).
    """
    from app.modules.country_packs.france.einvoicing_webhooks import WebhookNotificationService

    webhook_service = WebhookNotificationService(db)
    webhooks = webhook_service._get_configured_webhooks(current_user.tenant_id)

    # Masquer les secrets
    return {
        "total": len(webhooks),
        "webhooks": [
            {
                "config_id": str(w.get("config_id")),
                "url": w.get("url"),
                "provider": w.get("provider"),
                "has_secret": bool(w.get("secret"))
            }
            for w in webhooks
        ]
    }


@router.post("/webhook/{config_id}", response_model=WebhookResponse)
async def receive_pdp_webhook(
    config_id: UUID,
    payload: PDPWebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Endpoint pour recevoir les webhooks des PDP.

    Met à jour automatiquement le statut des factures.
    Note: Cet endpoint n'utilise pas l'auth utilisateur standard.
    """
    # NOTE: Phase 2 - Validation signature webhook HMAC

    # Récupérer le tenant depuis la config PDP
    from app.modules.country_packs.france.einvoicing_models import TenantPDPConfig

    config = db.query(TenantPDPConfig).filter(
        TenantPDPConfig.id == config_id
    ).first()

    if not config:
        return WebhookResponse(
            received=True,
            processed=False,
            message="Configuration PDP non trouvée"
        )

    service = get_einvoicing_service(db, config.tenant_id)

    try:
        result = service.process_webhook(config_id, payload.model_dump())
        return WebhookResponse(
            received=True,
            processed=result.get("processed", False),
            message=result.get("message")
        )
    except (EInvoicingError, PDPError, ValueError) as e:
        logger.error(f"Erreur traitement webhook: {e}")
        return WebhookResponse(
            received=True,
            processed=False,
            message=str(e)
        )


# =============================================================================
# AUTO-GENERATION
# =============================================================================

class AutoCompleteRequest(BaseModel):
    """Requête d'auto-complétion."""
    seller_country: str = "FR"
    buyer_country: str = "FR"
    buyer_siret: str | None = None
    buyer_vat: str | None = None
    buyer_name: str | None = None
    is_public_entity: bool = False
    lines: list[dict] = []
    payment_terms: str = "NET_30"

    model_config = {"extra": "allow"}


class AutoCompleteResponse(BaseModel):
    """Réponse d'auto-complétion."""
    suggestions: list[dict]
    auto_filled: dict
    warnings: list[str]
    requires_validation: list[str]
    ready_for_submission: bool
    confidence_score: float
    document_context: str


class SuggestDescriptionRequest(BaseModel):
    """Requête de suggestion de description."""
    service_type: str
    context: str | None = None
    client_code: str | None = None


class SuggestDescriptionResponse(BaseModel):
    """Réponse de suggestion de description."""
    suggested: str
    alternatives: list[str]
    confidence: str


@router.post("/autogen/complete", response_model=AutoCompleteResponse)
async def auto_complete_invoice(
    data: AutoCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Auto-complète une facture avec toutes les valeurs manquantes.

    Analyse le contexte (B2B, B2G, export...) et propose:
    - Le format de facture approprié
    - Les taux de TVA
    - Les mentions légales
    - Le PDP à utiliser
    - Les dates d'échéance

    Retourne un score de confiance et indique si la facture
    est prête pour soumission automatique.
    """
    autogen = get_autogen_service(current_user.tenant_id)

    seller_info = {
        "country_code": data.seller_country,
    }

    buyer_info = {
        "country_code": data.buyer_country,
        "siret": data.buyer_siret,
        "vat_number": data.buyer_vat,
        "name": data.buyer_name,
    }

    result = autogen.auto_complete_invoice(
        partial_data=data.model_dump(exclude={"seller_country", "buyer_country", "buyer_siret", "buyer_vat", "buyer_name", "is_public_entity", "lines"}),
        seller=seller_info,
        buyer=buyer_info,
        lines=data.lines
    )

    return AutoCompleteResponse(
        suggestions=[
            {
                "field": s.field_name,
                "value": str(s.suggested_value) if s.suggested_value else None,
                "confidence": s.confidence.value,
                "reason": s.reason,
                "alternatives": [str(a) for a in s.alternatives]
            }
            for s in result.suggestions
        ],
        auto_filled=result.auto_filled,
        warnings=result.warnings,
        requires_validation=result.requires_validation,
        ready_for_submission=result.ready_for_submission,
        confidence_score=result.confidence_score,
        document_context=result.auto_filled.get("document_context", "B2B_DOMESTIC")
    )


@router.post("/autogen/suggest-description", response_model=SuggestDescriptionResponse)
async def suggest_line_description(
    data: SuggestDescriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Suggère une description pour une ligne de facture.

    Basé sur:
    - Le type de service (consulting, development, etc.)
    - Le contexte optionnel
    - L'historique client (si fourni)
    """
    autogen = get_autogen_service(current_user.tenant_id)

    # NOTE: Phase 2 - Historique via InvoiceService.get_client_history()
    client_history = None

    suggestion = autogen.suggest_line_description(
        service_type=data.service_type,
        context=data.context,
        client_history=client_history
    )

    return SuggestDescriptionResponse(
        suggested=suggestion.suggested_value,
        alternatives=suggestion.alternatives,
        confidence=suggestion.confidence.value
    )


@router.get("/autogen/vat-rates")
async def get_vat_rates(
    context: str = Query("B2B_DOMESTIC", description="Contexte document"),
    product_type: str | None = Query(None, description="Type de produit/service"),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les taux de TVA applicables selon le contexte.

    Détecte automatiquement:
    - Le taux standard (20%)
    - Les taux réduits (10%, 5.5%, 2.1%)
    - Les exonérations (export, intra-UE)
    """
    autogen = get_autogen_service(current_user.tenant_id)

    try:
        doc_context = DocumentContext(context)
    except ValueError:
        doc_context = DocumentContext.B2B_DOMESTIC

    vat_cat, vat_rate, confidence = autogen.detect_vat_category(
        context=doc_context,
        product_type=product_type
    )

    return {
        "category": vat_cat.value,
        "rate": float(vat_rate),
        "confidence": confidence.value,
        "all_rates": {
            "standard": 20.0,
            "intermediate": 10.0,
            "reduced": 5.5,
            "super_reduced": 2.1,
            "zero": 0.0
        },
        "context": context
    }


@router.get("/autogen/legal-mentions")
async def get_legal_mentions(
    context: str = Query("B2B_DOMESTIC"),
    payment_terms: str = Query("NET_30"),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les mentions légales obligatoires.

    Génère automatiquement:
    - Conditions de paiement
    - Pénalités de retard
    - Mentions TVA (exonération si applicable)
    - Escompte
    """
    from app.modules.country_packs.france.einvoicing_autogen import TextTemplates

    mentions = {
        "payment_terms": TextTemplates.get_payment_terms_text(payment_terms),
        "late_payment": TextTemplates.get_late_payment_text(),
        "early_payment": "Aucun escompte pour paiement anticipé",
    }

    try:
        doc_context = DocumentContext(context)
        if doc_context == DocumentContext.B2B_INTRA_EU:
            mentions["vat_exemption"] = TextTemplates.get_vat_exemption_text("INTRA_EU")
        elif doc_context == DocumentContext.B2B_EXPORT:
            mentions["vat_exemption"] = TextTemplates.get_vat_exemption_text("EXPORT")
    except ValueError:
        pass

    return mentions


@router.get("/autogen/payment-terms")
async def get_payment_terms_options(
    current_user: User = Depends(get_current_user)
):
    """
    Retourne toutes les options de conditions de paiement.
    """
    from app.modules.country_packs.france.einvoicing_autogen import TextTemplates

    return {
        "options": [
            {"code": code, "label": text}
            for code, text in TextTemplates.PAYMENT_TERMS.items()
        ]
    }


@router.get("/autogen/service-templates")
async def get_service_templates(
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les templates de descriptions de services.
    """
    from app.modules.country_packs.france.einvoicing_autogen import TextTemplates

    return {
        "templates": [
            {"type": stype, "description": desc}
            for stype, desc in TextTemplates.SERVICE_DESCRIPTIONS.items()
        ]
    }


# =============================================================================
# HELPERS
# =============================================================================

def _config_to_response(config) -> PDPConfigResponse:
    """Convertit un TenantPDPConfig en PDPConfigResponse."""
    from app.modules.country_packs.france.einvoicing_schemas import (
        CompanySizeType as SchemaSizeType,
        EInvoiceFormat,
        PDPProviderType as SchemaProviderType,
    )

    return PDPConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        provider=SchemaProviderType(config.provider.value),
        name=config.name,
        description=config.description,
        api_url=config.api_url,
        token_url=config.token_url,
        scope=config.scope,
        siret=config.siret,
        siren=config.siren,
        tva_number=config.tva_number,
        company_size=SchemaSizeType(config.company_size.value) if config.company_size else SchemaSizeType.PME,
        is_active=config.is_active,
        is_default=config.is_default,
        test_mode=config.test_mode,
        timeout_seconds=config.timeout_seconds,
        retry_count=config.retry_count,
        webhook_url=config.webhook_url,
        preferred_format=EInvoiceFormat(config.preferred_format.value) if config.preferred_format else EInvoiceFormat.FACTURX_EN16931,
        generate_pdf=config.generate_pdf,
        provider_options=config.provider_options or {},
        custom_endpoints=config.custom_endpoints or {},
        has_credentials=bool(config.client_id and config.client_secret),
        has_certificate=bool(config.certificate_ref),
        last_sync_at=config.last_sync_at,
        created_at=config.created_at,
        updated_at=config.updated_at
    )
