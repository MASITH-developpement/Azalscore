"""
AZALSCORE - E-Invoicing Generation
Génération de factures électroniques depuis documents sources
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session, joinedload

from app.modules.commercial.models import CommercialDocument, DocumentType
from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceDirection,
    EInvoiceFormatDB,
    EInvoiceRecord,
    EInvoiceStatusDB,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    EInvoiceCreateFromSource,
    EInvoiceCreateManual,
    EInvoiceFormat,
)
from app.modules.country_packs.france.e_invoicing import (
    EInvoiceService as FacturXGenerator,
)
from app.modules.purchases.models import LegacyPurchaseInvoice

from .helpers import (
    build_buyer_from_customer,
    build_invoice_data,
    build_seller_from_supplier,
    build_seller_from_tenant,
    calculate_vat_breakdown,
    calculate_vat_breakdown_purchase,
)

if TYPE_CHECKING:
    from .lifecycle import LifecycleManager

logger = logging.getLogger(__name__)


class EInvoiceGenerator:
    """
    Générateur de factures électroniques.

    Crée des e-invoices depuis:
    - Documents commerciaux (factures client)
    - Factures d'achat
    - Saisie manuelle
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        lifecycle_manager: "LifecycleManager"
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.lifecycle_manager = lifecycle_manager
        self._facturx_generator: FacturXGenerator | None = None

    @property
    def facturx_generator(self) -> FacturXGenerator:
        """Lazy-load du générateur Factur-X."""
        if self._facturx_generator is None:
            self._facturx_generator = FacturXGenerator(self.db, self.tenant_id)
        return self._facturx_generator

    def create_from_source(
        self,
        data: EInvoiceCreateFromSource,
        pdp_config: TenantPDPConfig | None,
        created_by: uuid.UUID | None = None
    ) -> EInvoiceRecord:
        """
        Crée une facture électronique depuis un document existant.

        Args:
            data: Données de création
            pdp_config: Configuration PDP
            created_by: UUID de l'utilisateur créateur

        Returns:
            EInvoiceRecord créé

        Raises:
            ValueError: Si le source_type n'est pas supporté
        """
        if data.source_type in ("INVOICE", "CREDIT_NOTE"):
            return self._create_from_commercial_document(
                data, pdp_config, created_by
            )
        elif data.source_type == "PURCHASE_INVOICE":
            return self._create_from_purchase_invoice(
                data, pdp_config, created_by
            )
        else:
            raise ValueError(f"Source type non supporté: {data.source_type}")

    def _create_from_commercial_document(
        self,
        data: EInvoiceCreateFromSource,
        pdp_config: TenantPDPConfig | None,
        created_by: uuid.UUID | None
    ) -> EInvoiceRecord:
        """Crée e-invoice depuis CommercialDocument."""
        doc = self.db.query(CommercialDocument).options(
            joinedload(CommercialDocument.customer),
            joinedload(CommercialDocument.lines)
        ).filter(
            CommercialDocument.id == data.source_id,
            CommercialDocument.tenant_id == self.tenant_id
        ).first()

        if not doc:
            raise ValueError(f"Document non trouvé: {data.source_id}")

        # Vérifier le type
        expected_type = DocumentType.INVOICE if data.source_type == "INVOICE" else DocumentType.CREDIT_NOTE
        if doc.type != expected_type:
            raise ValueError(f"Type de document incompatible: {doc.type}")

        # Construire les parties
        seller = build_seller_from_tenant(pdp_config)
        buyer = build_buyer_from_customer(doc.customer)

        # Calculer les totaux TVA
        vat_breakdown = calculate_vat_breakdown(doc.lines)

        # Générer le XML Factur-X
        invoice_data = build_invoice_data(
            doc, seller, buyer, vat_breakdown, data.format.value
        )
        xml_content = self.facturx_generator.generate_xml(invoice_data)
        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()

        # Valider
        validation = self.facturx_generator.validate_xml(xml_content)

        # Créer l'enregistrement
        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.OUTBOUND,
            invoice_number=doc.number,
            invoice_type="380" if data.source_type == "INVOICE" else "381",
            format=EInvoiceFormatDB(data.format.value),
            source_invoice_id=doc.id,
            source_type=data.source_type,
            issue_date=doc.date,
            due_date=doc.due_date,
            seller_siret=seller.siret,
            seller_name=seller.name,
            seller_tva=seller.vat_number,
            buyer_siret=buyer.siret,
            buyer_name=buyer.name,
            buyer_tva=buyer.vat_number,
            buyer_routing_id=buyer.routing_id,
            currency=doc.currency,
            total_ht=doc.subtotal,
            total_tva=doc.tax_amount,
            total_ttc=doc.total,
            vat_breakdown=vat_breakdown,
            status=EInvoiceStatusDB.DRAFT,
            xml_content=xml_content,
            xml_hash=xml_hash,
            validation_errors=validation.get("errors", []),
            validation_warnings=validation.get("warnings", []),
            is_valid=validation.get("is_valid", False),
            extra_data=data.metadata,
            created_by=created_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        # Ajouter événement lifecycle
        self.lifecycle_manager.add_event(
            einvoice,
            status="CREATED",
            actor=str(created_by) if created_by else "SYSTEM",
            source="SYSTEM",
            message=f"Facture électronique créée depuis {data.source_type}"
        )

        return einvoice

    def _create_from_purchase_invoice(
        self,
        data: EInvoiceCreateFromSource,
        pdp_config: TenantPDPConfig | None,
        created_by: uuid.UUID | None
    ) -> EInvoiceRecord:
        """Crée e-invoice depuis facture d'achat (INBOUND)."""
        invoice = self.db.query(LegacyPurchaseInvoice).options(
            joinedload(LegacyPurchaseInvoice.supplier),
            joinedload(LegacyPurchaseInvoice.lines)
        ).filter(
            LegacyPurchaseInvoice.id == data.source_id,
            LegacyPurchaseInvoice.tenant_id == self.tenant_id
        ).first()

        if not invoice:
            raise ValueError(f"Facture d'achat non trouvée: {data.source_id}")

        # Construire les parties (nous sommes l'acheteur)
        buyer = build_seller_from_tenant(pdp_config)
        seller = build_seller_from_supplier(invoice.supplier)

        # Calculer TVA
        vat_breakdown = calculate_vat_breakdown_purchase(invoice.lines)

        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.INBOUND,
            invoice_number=invoice.number,
            invoice_type="380",
            format=EInvoiceFormatDB(data.format.value),
            source_invoice_id=invoice.id,
            source_type="PURCHASE_INVOICE",
            issue_date=invoice.invoice_date.date() if invoice.invoice_date else date.today(),
            due_date=invoice.due_date.date() if invoice.due_date else None,
            seller_siret=seller.siret,
            seller_name=seller.name,
            seller_tva=seller.vat_number,
            buyer_siret=buyer.siret,
            buyer_name=buyer.name,
            buyer_tva=buyer.vat_number,
            currency=invoice.currency,
            total_ht=invoice.total_ht,
            total_tva=invoice.total_tax,
            total_ttc=invoice.total_ttc,
            vat_breakdown=vat_breakdown,
            status=EInvoiceStatusDB.RECEIVED,
            is_valid=True,
            reception_date=None,
            extra_data=data.metadata,
            created_by=created_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        self.lifecycle_manager.add_event(
            einvoice,
            status="RECEIVED",
            actor=str(created_by) if created_by else "SYSTEM",
            source="SYSTEM",
            message="Facture fournisseur enregistrée"
        )

        return einvoice

    def create_manual(
        self,
        data: EInvoiceCreateManual,
        pdp_config: TenantPDPConfig | None,
        created_by: uuid.UUID | None = None
    ) -> EInvoiceRecord:
        """Crée une facture électronique manuellement."""
        # Calculer les totaux
        total_ht = Decimal("0")
        total_tva = Decimal("0")
        vat_breakdown: dict[str, Decimal] = {}

        for line in data.lines:
            line_ht = line.quantity * line.unit_price * (1 - line.discount_percent / 100)
            line_tva = line_ht * line.vat_rate / 100
            total_ht += line_ht
            total_tva += line_tva

            rate_key = str(line.vat_rate)
            vat_breakdown[rate_key] = vat_breakdown.get(rate_key, Decimal("0")) + line_tva

        total_ttc = total_ht + total_tva

        # Préparer les données pour le générateur Factur-X
        invoice_data = {
            "invoice_number": data.invoice_number,
            "type": data.invoice_type,
            "issue_date": data.issue_date,
            "due_date": data.due_date,
            "seller_name": data.seller.name,
            "seller_siret": data.seller.siret,
            "seller_tva": data.seller.vat_number,
            "seller_address": data.seller.address_line1,
            "seller_postal_code": data.seller.postal_code,
            "seller_city": data.seller.city,
            "buyer_name": data.buyer.name,
            "buyer_siret": data.buyer.siret,
            "buyer_tva": data.buyer.vat_number,
            "buyer_address": data.buyer.address_line1,
            "buyer_postal_code": data.buyer.postal_code,
            "buyer_city": data.buyer.city,
            "lines": [
                {
                    "description": line.description,
                    "quantity": float(line.quantity),
                    "unit_price": float(line.unit_price),
                    "vat_rate": float(line.vat_rate),
                    "net_amount": float(line.quantity * line.unit_price * (1 - line.discount_percent / 100)),
                    "vat_amount": float(line.quantity * line.unit_price * (1 - line.discount_percent / 100) * line.vat_rate / 100)
                }
                for line in data.lines
            ],
            "total_ht": float(total_ht),
            "total_tva": float(total_tva),
            "total_ttc": float(total_ttc),
            "payment_means": data.payment_means_code or "30",
            "note": data.notes
        }

        # Créer le document et générer le XML
        doc = self.facturx_generator.create_einvoice(invoice_data)
        xml_content = self.facturx_generator.generate_facturx_xml(doc)
        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()
        validation = self.facturx_generator.validate_einvoice(doc)

        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection(data.direction.value),
            invoice_number=data.invoice_number,
            invoice_type=data.invoice_type,
            format=EInvoiceFormatDB(data.format.value),
            issue_date=data.issue_date,
            due_date=data.due_date,
            seller_siret=data.seller.siret,
            seller_name=data.seller.name,
            seller_tva=data.seller.vat_number,
            buyer_siret=data.buyer.siret,
            buyer_name=data.buyer.name,
            buyer_tva=data.buyer.vat_number,
            buyer_routing_id=data.buyer.routing_id,
            currency=data.currency,
            total_ht=total_ht,
            total_tva=total_tva,
            total_ttc=total_ttc,
            vat_breakdown={str(k): float(v) for k, v in vat_breakdown.items()},
            status=EInvoiceStatusDB.DRAFT,
            xml_content=xml_content,
            xml_hash=xml_hash,
            validation_errors=validation.get("errors", []),
            validation_warnings=validation.get("warnings", []),
            is_valid=validation.get("is_valid", False),
            extra_data=data.metadata,
            created_by=created_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        self.lifecycle_manager.add_event(
            einvoice,
            status="CREATED",
            actor=str(created_by) if created_by else "SYSTEM",
            source="MANUAL",
            message="Facture électronique créée manuellement"
        )

        return einvoice
