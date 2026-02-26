"""
AZALSCORE - E-Invoicing Inbound
Gestion des factures entrantes
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceDirection,
    EInvoiceFormatDB,
    EInvoiceRecord,
    EInvoiceStatusDB,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_schemas import EInvoiceFormat

from .xml_parsing import get_xml_parser

if TYPE_CHECKING:
    from .lifecycle import LifecycleManager
    from .webhooks import WebhookHandler

logger = logging.getLogger(__name__)


class InboundInvoiceHandler:
    """
    Gestionnaire des factures entrantes.

    Gère:
    - Réception de factures via XML
    - Réception de factures pré-parsées
    - Acceptation / Refus de factures
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        lifecycle_manager: "LifecycleManager",
        webhook_handler: "WebhookHandler"
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.lifecycle_manager = lifecycle_manager
        self.webhook_handler = webhook_handler
        self.xml_parser = get_xml_parser()

    def receive_inbound_xml(
        self,
        xml_content: str,
        pdp_config: TenantPDPConfig | None,
        source_pdp: str | None = None,
        ppf_id: str | None = None,
        pdp_id: str | None = None,
        pdf_base64: str | None = None,
        received_by: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None
    ) -> tuple[EInvoiceRecord, dict[str, Any]]:
        """
        Reçoit et enregistre une facture entrante depuis XML.

        Args:
            xml_content: Contenu XML de la facture
            pdp_config: Configuration PDP
            source_pdp: Identifiant du PDP source
            ppf_id: Identifiant PPF
            pdp_id: Identifiant PDP
            pdf_base64: PDF en base64 (optionnel)
            received_by: UUID de l'utilisateur
            metadata: Métadonnées additionnelles

        Returns:
            Tuple (EInvoiceRecord, validation_result)

        Raises:
            ValueError: Si le parsing XML échoue
        """
        # Parser le XML
        try:
            parsed_data = self.xml_parser.parse(xml_content)
        except Exception as e:
            raise ValueError(f"Erreur parsing XML: {str(e)}")

        # Déterminer le format depuis le XML
        format_detected = self.xml_parser.detect_format(xml_content)

        # Calculer le hash
        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()

        # Créer l'enregistrement
        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.INBOUND,
            invoice_number=parsed_data.get("invoice_number", f"INB-{uuid.uuid4().hex[:8]}"),
            invoice_type=parsed_data.get("invoice_type", "380"),
            format=format_detected,
            ppf_id=ppf_id,
            pdp_id=pdp_id,
            issue_date=parsed_data.get("issue_date", date.today()),
            due_date=parsed_data.get("due_date"),
            reception_date=datetime.utcnow(),
            seller_siret=parsed_data.get("seller_siret"),
            seller_name=parsed_data.get("seller_name"),
            seller_tva=parsed_data.get("seller_tva"),
            buyer_siret=parsed_data.get("buyer_siret"),
            buyer_name=parsed_data.get("buyer_name"),
            buyer_tva=parsed_data.get("buyer_tva"),
            currency=parsed_data.get("currency", "EUR"),
            total_ht=Decimal(str(parsed_data.get("total_ht", 0))),
            total_tva=Decimal(str(parsed_data.get("total_tva", 0))),
            total_ttc=Decimal(str(parsed_data.get("total_ttc", 0))),
            vat_breakdown=parsed_data.get("vat_breakdown", {}),
            status=EInvoiceStatusDB.RECEIVED,
            xml_content=xml_content,
            xml_hash=xml_hash,
            is_valid=True,
            extra_data=metadata or {},
            created_by=received_by
        )

        # Stocker le PDF si fourni
        if pdf_base64:
            einvoice.pdf_storage_ref = f"inbound/{self.tenant_id}/{einvoice.id}.pdf"
            # NOTE: Phase 2 - Sauvegarder PDF via storage_service

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        # Ajouter événement lifecycle
        self.lifecycle_manager.add_event(
            einvoice,
            status="RECEIVED",
            actor=source_pdp or "EXTERNAL",
            source="PDP" if source_pdp else "MANUAL",
            message=f"Facture reçue depuis {source_pdp or 'source externe'}",
            details={"ppf_id": ppf_id, "pdp_id": pdp_id}
        )

        # Valider la facture
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "profile": format_detected.value
        }

        # Mettre à jour les stats
        self.lifecycle_manager.update_stats(einvoice, "inbound_total")

        return einvoice, validation_result

    def receive_inbound_parsed(
        self,
        data: dict[str, Any],
        pdp_config: TenantPDPConfig | None,
        received_by: uuid.UUID | None = None
    ) -> tuple[EInvoiceRecord, dict[str, Any]]:
        """
        Reçoit une facture entrante avec données déjà parsées.

        Args:
            data: Données de la facture
            pdp_config: Configuration PDP
            received_by: UUID de l'utilisateur

        Returns:
            Tuple (EInvoiceRecord, validation_result)
        """
        # Calculer hash si XML fourni
        xml_hash = None
        if data.get("xml_content"):
            xml_hash = hashlib.sha256(data["xml_content"].encode()).hexdigest()

        # Calculer les totaux si pas fournis
        total_ht = Decimal(str(data.get("total_ht", 0)))
        total_tva = Decimal(str(data.get("total_tva", 0)))
        total_ttc = Decimal(str(data.get("total_ttc", total_ht + total_tva)))

        einvoice = EInvoiceRecord(
            tenant_id=self.tenant_id,
            pdp_config_id=pdp_config.id if pdp_config else None,
            direction=EInvoiceDirection.INBOUND,
            invoice_number=data.get("invoice_number", f"INB-{uuid.uuid4().hex[:8]}"),
            invoice_type=data.get("invoice_type", "380"),
            format=EInvoiceFormatDB(data.get("format", EInvoiceFormat.FACTURX_EN16931).value),
            ppf_id=data.get("ppf_id"),
            pdp_id=data.get("pdp_id"),
            issue_date=data.get("issue_date", date.today()),
            due_date=data.get("due_date"),
            reception_date=data.get("received_at") or datetime.utcnow(),
            seller_siret=data.get("seller", {}).get("siret"),
            seller_name=data.get("seller", {}).get("name"),
            seller_tva=data.get("seller", {}).get("vat_number"),
            buyer_siret=data.get("buyer", {}).get("siret"),
            buyer_name=data.get("buyer", {}).get("name"),
            buyer_tva=data.get("buyer", {}).get("vat_number"),
            currency=data.get("currency", "EUR"),
            total_ht=total_ht,
            total_tva=total_tva,
            total_ttc=total_ttc,
            vat_breakdown=data.get("vat_breakdown", {}),
            status=EInvoiceStatusDB.RECEIVED,
            xml_content=data.get("xml_content"),
            xml_hash=xml_hash,
            is_valid=True,
            extra_data=data.get("metadata", {}),
            created_by=received_by
        )

        self.db.add(einvoice)
        self.db.commit()
        self.db.refresh(einvoice)

        self.lifecycle_manager.add_event(
            einvoice,
            status="RECEIVED",
            actor=data.get("source_pdp", "EXTERNAL"),
            source="PDP" if data.get("source_pdp") else "MANUAL",
            message="Facture entrante enregistrée"
        )

        self.lifecycle_manager.update_stats(einvoice, "inbound_total")

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "profile": einvoice.format.value
        }

        return einvoice, validation_result

    def accept_inbound_invoice(
        self,
        einvoice: EInvoiceRecord,
        accepted_by: uuid.UUID | None = None,
        message: str | None = None
    ) -> EInvoiceRecord:
        """
        Accepte une facture entrante.

        Args:
            einvoice: Facture à accepter
            accepted_by: UUID de l'utilisateur
            message: Message optionnel

        Returns:
            EInvoiceRecord mis à jour

        Raises:
            ValueError: Si la facture n'est pas entrante ou statut incompatible
        """
        if einvoice.direction != EInvoiceDirection.INBOUND:
            raise ValueError("Cette méthode est réservée aux factures entrantes")

        if einvoice.status not in (EInvoiceStatusDB.RECEIVED, EInvoiceStatusDB.VALIDATED):
            raise ValueError(f"Statut incompatible: {einvoice.status}")

        old_status = einvoice.status
        einvoice.status = EInvoiceStatusDB.ACCEPTED
        einvoice.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(einvoice)

        self.lifecycle_manager.add_event(
            einvoice,
            status="ACCEPTED",
            actor=str(accepted_by) if accepted_by else "SYSTEM",
            source="MANUAL",
            message=message or "Facture acceptée"
        )

        self.lifecycle_manager.update_stats_on_status_change(
            einvoice, old_status, EInvoiceStatusDB.ACCEPTED
        )

        # Notification webhook
        self.webhook_handler.trigger_notification(
            einvoice, old_status, EInvoiceStatusDB.ACCEPTED, message
        )

        return einvoice

    def refuse_inbound_invoice(
        self,
        einvoice: EInvoiceRecord,
        refused_by: uuid.UUID | None = None,
        reason: str | None = None
    ) -> EInvoiceRecord:
        """
        Refuse une facture entrante.

        Args:
            einvoice: Facture à refuser
            refused_by: UUID de l'utilisateur
            reason: Raison du refus

        Returns:
            EInvoiceRecord mis à jour

        Raises:
            ValueError: Si la facture n'est pas entrante ou statut incompatible
        """
        if einvoice.direction != EInvoiceDirection.INBOUND:
            raise ValueError("Cette méthode est réservée aux factures entrantes")

        if einvoice.status not in (EInvoiceStatusDB.RECEIVED, EInvoiceStatusDB.VALIDATED):
            raise ValueError(f"Statut incompatible: {einvoice.status}")

        old_status = einvoice.status
        einvoice.status = EInvoiceStatusDB.REFUSED
        einvoice.last_error = reason
        einvoice.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(einvoice)

        self.lifecycle_manager.add_event(
            einvoice,
            status="REFUSED",
            actor=str(refused_by) if refused_by else "SYSTEM",
            source="MANUAL",
            message=reason or "Facture refusée"
        )

        self.lifecycle_manager.update_stats_on_status_change(
            einvoice, old_status, EInvoiceStatusDB.REFUSED
        )

        # Notification webhook
        self.webhook_handler.trigger_notification(
            einvoice, old_status, EInvoiceStatusDB.REFUSED, reason
        )

        return einvoice
