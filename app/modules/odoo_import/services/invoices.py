"""
AZALS MODULE - Odoo Import Invoices Service
=============================================

Service d'import des factures depuis Odoo.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.modules.odoo_import.models import OdooImportHistory, OdooSyncType

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class InvoiceImportService(BaseOdooService[OdooImportHistory]):
    """Service d'import des factures Odoo."""

    model = OdooImportHistory

    def import_invoices(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les factures depuis Odoo (account.move type=out_invoice).

        Importe les factures clients et les avoirs (credit notes).

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta

        Returns:
            Historique de l'import
        """
        from app.modules.commercial.models import (
            CommercialDocument,
            Customer,
            DocumentStatus,
            DocumentType,
        )

        config = self._require_config(config_id)

        history = self._create_history(
            config_id=config_id,
            sync_type=OdooSyncType.INVOICES,
            is_delta=not full_sync,
        )

        created = 0
        updated = 0
        errors = []

        try:
            connector = self._get_connector(config)

            # Factures clients (out_invoice) et avoirs (out_refund) validées
            domain = [
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
            ]
            fields = [
                "name",
                "partner_id",
                "invoice_date",
                "invoice_date_due",
                "state",
                "amount_untaxed",
                "amount_tax",
                "amount_total",
                "amount_residual",
                "currency_id",
                "move_type",
                "invoice_line_ids",
            ]

            invoices = connector.search_read("account.move", domain, fields)
            history.total_records = len(invoices)

            logger.info("Récupéré %d factures depuis Odoo", len(invoices))

            # Mapping des statuts Odoo -> AZALS
            status_map = {
                "draft": DocumentStatus.DRAFT,
                "posted": DocumentStatus.VALIDATED,
                "cancel": DocumentStatus.CANCELLED,
            }

            for inv in invoices:
                try:
                    result = self._import_invoice(
                        inv,
                        status_map,
                        Customer,
                        CommercialDocument,
                        DocumentType,
                        DocumentStatus,
                    )
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
                except Exception as e:
                    errors.append({
                        "number": inv.get("name"),
                        "error": str(e)[:200],
                    })
                    self.db.rollback()

            self.db.commit()

            history = self._finalize_history(history, created, updated, errors)

            logger.info(
                "Import factures terminé | created=%d updated=%d errors=%d",
                created,
                updated,
                len(errors),
            )
            return history

        except Exception as e:
            self._fail_history(history, e)
            self.db.commit()
            raise

    def _import_invoice(
        self,
        inv: Dict[str, Any],
        status_map: Dict[str, Any],
        customer_model: Any,
        document_model: Any,
        document_type_enum: Any,
        document_status_enum: Any,
    ) -> Optional[str]:
        """
        Importe une facture individuelle.

        Args:
            inv: Données de la facture Odoo
            status_map: Mapping des statuts Odoo -> AZALS
            customer_model: Modèle Customer
            document_model: Modèle CommercialDocument
            document_type_enum: Enum DocumentType
            document_status_enum: Enum DocumentStatus

        Returns:
            "created", "updated" ou None si erreur
        """
        from app.modules.commercial.models import CustomerType

        odoo_number = inv.get("name", "")
        partner_id = self._get_odoo_id(inv.get("partner_id"))
        partner_name = self._get_odoo_name(inv.get("partner_id")) or "Client Odoo"

        if not partner_id:
            raise ValueError("Aucun partner_id")

        # Trouver ou créer le client
        customer = self._get_or_create_customer(
            partner_id,
            partner_name,
            customer_model,
            CustomerType,
        )

        # Déterminer le type de document
        move_type = inv.get("move_type")
        doc_type = (
            document_type_enum.CREDIT_NOTE
            if move_type == "out_refund"
            else document_type_enum.INVOICE
        )

        # Vérifier si la facture existe déjà
        existing = (
            self.db.query(document_model)
            .filter(
                document_model.tenant_id == self.tenant_id,
                document_model.type == doc_type,
                document_model.number == odoo_number,
            )
            .first()
        )

        invoice_date = self._parse_date(inv.get("invoice_date"))
        due_date = self._parse_date(inv.get("invoice_date_due"))
        currency = self._get_currency(inv.get("currency_id"))

        amount_total = inv.get("amount_total", 0)
        amount_residual = inv.get("amount_residual", 0)
        paid_amount = amount_total - amount_residual

        if existing:
            existing.subtotal = inv.get("amount_untaxed", 0)
            existing.tax_amount = inv.get("amount_tax", 0)
            existing.total = amount_total
            existing.remaining_amount = amount_residual
            existing.paid_amount = paid_amount
            existing.status = status_map.get(
                inv.get("state"),
                document_status_enum.VALIDATED,
            )
            existing.updated_at = datetime.utcnow()
            self.db.flush()
            return "updated"

        doc = document_model(
            tenant_id=self.tenant_id,
            customer_id=customer.id,
            type=doc_type,
            number=odoo_number,
            status=status_map.get(
                inv.get("state"),
                document_status_enum.VALIDATED,
            ),
            date=invoice_date or datetime.utcnow().date(),
            due_date=due_date,
            subtotal=inv.get("amount_untaxed", 0),
            tax_amount=inv.get("amount_tax", 0),
            total=amount_total,
            paid_amount=paid_amount,
            remaining_amount=amount_residual,
            currency=currency,
        )
        self.db.add(doc)
        self.db.flush()
        return "created"

    def _get_or_create_customer(
        self,
        partner_id: int,
        partner_name: str,
        customer_model: Any,
        customer_type_model: Any,
    ):
        """
        Récupère ou crée un customer à partir d'un partenaire Odoo.

        Args:
            partner_id: ID du partenaire Odoo
            partner_name: Nom du partenaire
            customer_model: Modèle Customer
            customer_type_model: Enum CustomerType

        Returns:
            Customer existant ou créé
        """
        odoo_code = f"ODOO-{partner_id}"

        customer = (
            self.db.query(customer_model)
            .filter(
                customer_model.tenant_id == self.tenant_id,
                customer_model.code == odoo_code,
            )
            .first()
        )

        if not customer:
            customer = customer_model(
                tenant_id=self.tenant_id,
                code=odoo_code,
                name=partner_name,
                type=customer_type_model.CUSTOMER,
            )
            self.db.add(customer)
            self.db.flush()
            logger.info("Customer créé: %s (%s)", partner_name, odoo_code)

        return customer

    @staticmethod
    def _get_currency(currency_value: Any) -> str:
        """
        Extrait le code devise d'une valeur Many2one Odoo.

        Args:
            currency_value: Valeur [id, code] ou None

        Returns:
            Code devise ou "EUR" par défaut
        """
        if not currency_value:
            return "EUR"
        if isinstance(currency_value, (list, tuple)) and len(currency_value) > 1:
            return currency_value[1]
        return "EUR"
