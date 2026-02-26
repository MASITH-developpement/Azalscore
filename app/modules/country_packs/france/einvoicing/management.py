"""
AZALSCORE - E-Invoicing Management
Gestion CRUD des factures électroniques
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.modules.country_packs.france.e_invoicing import (
    EInvoiceDocument,
    EInvoiceLine as FacturXLine,
    EInvoiceParty as FacturXParty,
    EInvoiceService as FacturXGenerator,
    EInvoiceType,
)
from app.modules.country_packs.france.einvoicing_models import (
    EInvoiceDirection,
    EInvoiceFormatDB,
    EInvoiceRecord,
    EInvoiceStatusDB,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    EInvoiceFilter,
    EInvoiceFormat,
    EInvoiceStatusUpdate,
    ValidationResult,
)

if TYPE_CHECKING:
    from .lifecycle import LifecycleManager
    from .webhooks import WebhookHandler

logger = logging.getLogger(__name__)


class EInvoiceManager:
    """
    Gestionnaire CRUD des factures électroniques.

    Gère:
    - Récupération de factures
    - Liste avec filtres
    - Mise à jour de statut
    - Validation
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
        self._facturx_generator: FacturXGenerator | None = None

    @property
    def facturx_generator(self) -> FacturXGenerator:
        """Lazy-load du générateur Factur-X."""
        if self._facturx_generator is None:
            self._facturx_generator = FacturXGenerator(self.db, self.tenant_id)
        return self._facturx_generator

    def get_einvoice(self, einvoice_id: uuid.UUID) -> EInvoiceRecord | None:
        """Récupère une facture électronique."""
        return self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.id == einvoice_id,
            EInvoiceRecord.tenant_id == self.tenant_id
        ).first()

    def get_einvoice_detail(self, einvoice_id: uuid.UUID) -> EInvoiceRecord | None:
        """Récupère une facture avec ses événements."""
        return self.db.query(EInvoiceRecord).options(
            joinedload(EInvoiceRecord.lifecycle_events),
            joinedload(EInvoiceRecord.pdp_config)
        ).filter(
            EInvoiceRecord.id == einvoice_id,
            EInvoiceRecord.tenant_id == self.tenant_id
        ).first()

    def list_einvoices(
        self,
        filters: EInvoiceFilter | None = None,
        page: int = 1,
        page_size: int = 25
    ) -> tuple[list[EInvoiceRecord], int]:
        """Liste les factures électroniques avec filtres."""
        query = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.tenant_id == self.tenant_id
        )

        if filters:
            query = self._apply_filters(query, filters)

        total = query.count()

        items = query.order_by(
            EInvoiceRecord.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def _apply_filters(self, query, filters: EInvoiceFilter):
        """Applique les filtres à la requête."""
        if filters.direction:
            query = query.filter(
                EInvoiceRecord.direction == EInvoiceDirection(filters.direction.value)
            )
        if filters.status:
            query = query.filter(
                EInvoiceRecord.status == EInvoiceStatusDB(filters.status.value)
            )
        if filters.format:
            query = query.filter(
                EInvoiceRecord.format == EInvoiceFormatDB(filters.format.value)
            )
        if filters.pdp_config_id:
            query = query.filter(
                EInvoiceRecord.pdp_config_id == filters.pdp_config_id
            )
        if filters.date_from:
            query = query.filter(EInvoiceRecord.issue_date >= filters.date_from)
        if filters.date_to:
            query = query.filter(EInvoiceRecord.issue_date <= filters.date_to)
        if filters.seller_siret:
            query = query.filter(EInvoiceRecord.seller_siret == filters.seller_siret)
        if filters.buyer_siret:
            query = query.filter(EInvoiceRecord.buyer_siret == filters.buyer_siret)
        if filters.source_type:
            query = query.filter(EInvoiceRecord.source_type == filters.source_type)
        if filters.has_errors is True:
            query = query.filter(EInvoiceRecord.error_count > 0)
        elif filters.has_errors is False:
            query = query.filter(
                or_(EInvoiceRecord.error_count == 0, EInvoiceRecord.error_count.is_(None))
            )
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    EInvoiceRecord.invoice_number.ilike(search_term),
                    EInvoiceRecord.seller_name.ilike(search_term),
                    EInvoiceRecord.buyer_name.ilike(search_term),
                    EInvoiceRecord.ppf_id.ilike(search_term),
                    EInvoiceRecord.pdp_id.ilike(search_term)
                )
            )
        return query

    def update_einvoice_status(
        self,
        einvoice_id: uuid.UUID,
        data: EInvoiceStatusUpdate
    ) -> EInvoiceRecord | None:
        """Met à jour le statut d'une facture."""
        einvoice = self.get_einvoice(einvoice_id)
        if not einvoice:
            return None

        old_status = einvoice.status
        einvoice.status = EInvoiceStatusDB(data.status.value)

        if data.lifecycle_status:
            einvoice.lifecycle_status = data.lifecycle_status

        einvoice.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(einvoice)

        self.lifecycle_manager.add_event(
            einvoice,
            status=data.status.value,
            actor=data.actor,
            source=data.source or "MANUAL",
            message=data.message or f"Statut mis à jour: {old_status} -> {data.status}"
        )

        # Mettre à jour les stats
        self.lifecycle_manager.update_stats_on_status_change(einvoice, old_status, einvoice.status)

        # Envoyer notification webhook
        self.webhook_handler.trigger_notification(
            einvoice,
            old_status,
            einvoice.status,
            data.message
        )

        return einvoice

    def validate_einvoice(self, einvoice_id: uuid.UUID) -> ValidationResult:
        """Valide une facture électronique."""
        einvoice = self.get_einvoice(einvoice_id)
        if not einvoice:
            raise ValueError(f"Facture non trouvée: {einvoice_id}")

        # Reconstruire le document pour validation
        doc = self._rebuild_document_from_einvoice(einvoice)
        validation = self.facturx_generator.validate_einvoice(doc)

        einvoice.validation_errors = validation.get("errors", [])
        einvoice.validation_warnings = validation.get("warnings", [])
        einvoice.is_valid = validation.get("valid", False)

        if einvoice.is_valid and einvoice.status == EInvoiceStatusDB.DRAFT:
            einvoice.status = EInvoiceStatusDB.VALIDATED

        self.db.commit()
        self.db.refresh(einvoice)

        return ValidationResult(
            is_valid=einvoice.is_valid,
            errors=einvoice.validation_errors,
            warnings=einvoice.validation_warnings,
            profile=validation.get("profile"),
            format=EInvoiceFormat(einvoice.format.value) if einvoice.format else None
        )

    def _rebuild_document_from_einvoice(self, einvoice: EInvoiceRecord) -> EInvoiceDocument:
        """Reconstruit un EInvoiceDocument depuis un enregistrement."""
        # Créer les parties
        seller = FacturXParty(
            name=einvoice.seller_name or "",
            siret=einvoice.seller_siret or "",
            tva_number=einvoice.seller_tva,
        )

        buyer = FacturXParty(
            name=einvoice.buyer_name or "",
            siret=einvoice.buyer_siret or "",
            tva_number=einvoice.buyer_tva,
            routing_id=einvoice.buyer_routing_id,
        )

        # Recréer les lignes depuis vat_breakdown
        lines = []
        vat_breakdown = einvoice.vat_breakdown or {}
        line_num = 1
        for rate_str, amount in vat_breakdown.items():
            rate = Decimal(str(rate_str))
            vat_amount = Decimal(str(amount))
            ht_amount = vat_amount * Decimal("100") / rate if rate > 0 else Decimal("0")

            lines.append(FacturXLine(
                line_number=line_num,
                description=f"Ligne facture (TVA {rate}%)",
                quantity=Decimal("1"),
                unit_price=ht_amount,
                net_amount=ht_amount,
                vat_rate=rate,
                vat_amount=vat_amount,
            ))
            line_num += 1

        # Si pas de lignes, créer une ligne par défaut
        if not lines:
            lines.append(FacturXLine(
                line_number=1,
                description="Ligne facture",
                quantity=Decimal("1"),
                unit_price=einvoice.total_ht or Decimal("0"),
                net_amount=einvoice.total_ht or Decimal("0"),
                vat_rate=Decimal("20"),
                vat_amount=einvoice.total_tva or Decimal("0"),
            ))

        # Déterminer le type de facture
        invoice_type = EInvoiceType.INVOICE
        if einvoice.invoice_type == "381":
            invoice_type = EInvoiceType.CREDIT_NOTE
        elif einvoice.invoice_type:
            try:
                invoice_type = EInvoiceType(einvoice.invoice_type)
            except ValueError:
                pass

        return EInvoiceDocument(
            invoice_number=einvoice.invoice_number,
            invoice_type=invoice_type,
            issue_date=einvoice.issue_date,
            due_date=einvoice.due_date,
            currency_code=einvoice.currency or "EUR",
            seller=seller,
            buyer=buyer,
            lines=lines,
            total_ht=einvoice.total_ht or Decimal("0"),
            total_tva=einvoice.total_tva or Decimal("0"),
            total_ttc=einvoice.total_ttc or Decimal("0"),
        )
