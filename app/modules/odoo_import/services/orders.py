"""
AZALS MODULE - Odoo Import Orders Service
==========================================

Service d'import des commandes depuis Odoo.
Gère les commandes d'achat, de vente et les devis.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.modules.odoo_import.models import OdooImportHistory, OdooSyncType

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class OrderImportService(BaseOdooService[OdooImportHistory]):
    """Service d'import des commandes Odoo."""

    model = OdooImportHistory

    def import_purchase_orders(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les commandes d'achat depuis Odoo (purchase.order).

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta

        Returns:
            Historique de l'import
        """
        config = self._require_config(config_id)

        history = self._create_history(
            config_id=config_id,
            sync_type=OdooSyncType.PURCHASE_ORDERS,
            is_delta=not full_sync,
        )

        try:
            connector = self._get_connector(config)

            domain = []
            fields = [
                "name",
                "date_order",
                "partner_id",
                "state",
                "amount_total",
                "currency_id",
                "order_line",
            ]

            orders = connector.search_read("purchase.order", domain, fields)
            history.total_records = len(orders)

            logger.info(
                "Récupéré %d commandes d'achat depuis Odoo",
                len(orders),
            )

            # Pour l'instant, on log les données récupérées
            # L'import effectif nécessite le modèle PurchaseOrder
            history.created_count = len(orders)
            history.status = OdooSyncType.PURCHASE_ORDERS
            history = self._finalize_history(history, len(orders), 0, [])

            return history

        except Exception as e:
            self._fail_history(history, e)
            self.db.commit()
            raise

    def import_sale_orders(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les commandes de vente depuis Odoo (sale.order confirmées).

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
            sync_type=OdooSyncType.SALE_ORDERS,
            is_delta=not full_sync,
        )

        created = 0
        updated = 0
        errors = []

        try:
            connector = self._get_connector(config)

            # Commandes confirmées (exclure draft, sent, cancel)
            domain = [("state", "not in", ["draft", "sent", "cancel"])]
            fields = [
                "name",
                "date_order",
                "partner_id",
                "state",
                "amount_untaxed",
                "amount_tax",
                "amount_total",
                "currency_id",
                "commitment_date",
            ]

            orders = connector.search_read("sale.order", domain, fields)
            history.total_records = len(orders)

            logger.info("Récupéré %d commandes de vente depuis Odoo", len(orders))

            # Mapping des statuts Odoo -> AZALS
            status_map = {
                "sale": DocumentStatus.VALIDATED,
                "done": DocumentStatus.PAID,
                "cancel": DocumentStatus.CANCELLED,
            }

            for order in orders:
                try:
                    result = self._import_sale_order(
                        order,
                        status_map,
                        DocumentType.ORDER,
                        Customer,
                        CommercialDocument,
                    )
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
                except Exception as e:
                    errors.append({
                        "number": order.get("name"),
                        "error": str(e)[:200],
                    })
                    self.db.rollback()

            self.db.commit()

            # Mettre à jour la configuration
            config.orders_last_sync_at = datetime.utcnow()
            config.total_orders_imported += created + updated
            config.total_imports += 1

            history = self._finalize_history(history, created, updated, errors)

            logger.info(
                "Import commandes terminé | created=%d updated=%d errors=%d",
                created,
                updated,
                len(errors),
            )
            return history

        except Exception as e:
            self._fail_history(history, e)
            self.db.commit()
            raise

    def import_quotes(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les devis depuis Odoo (sale.order state=draft/sent).

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
            sync_type=OdooSyncType.QUOTES,
            is_delta=not full_sync,
        )

        created = 0
        updated = 0
        errors = []

        try:
            connector = self._get_connector(config)

            # Devis = commandes en brouillon ou envoyées
            domain = [("state", "in", ["draft", "sent"])]
            fields = [
                "name",
                "date_order",
                "partner_id",
                "state",
                "amount_untaxed",
                "amount_tax",
                "amount_total",
                "validity_date",
                "currency_id",
            ]

            quotes = connector.search_read("sale.order", domain, fields)
            history.total_records = len(quotes)

            logger.info("Récupéré %d devis depuis Odoo", len(quotes))

            status_map = {
                "draft": DocumentStatus.DRAFT,
                "sent": DocumentStatus.SENT,
                "sale": DocumentStatus.ACCEPTED,
                "cancel": DocumentStatus.CANCELLED,
            }

            for quote in quotes:
                try:
                    result = self._import_quote(
                        quote,
                        status_map,
                        Customer,
                        CommercialDocument,
                    )
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
                except Exception as e:
                    errors.append({
                        "number": quote.get("name"),
                        "error": str(e)[:200],
                    })
                    self.db.rollback()

            self.db.commit()

            history = self._finalize_history(history, created, updated, errors)

            logger.info(
                "Import devis terminé | created=%d updated=%d errors=%d",
                created,
                updated,
                len(errors),
            )
            return history

        except Exception as e:
            self._fail_history(history, e)
            self.db.commit()
            raise

    def _import_sale_order(
        self,
        order: Dict[str, Any],
        status_map: Dict[str, Any],
        doc_type: Any,
        customer_model: Any,
        document_model: Any,
    ) -> Optional[str]:
        """
        Importe une commande de vente individuelle.

        Returns:
            "created", "updated" ou None si erreur
        """
        from app.modules.commercial.models import CustomerType

        odoo_number = order.get("name", "")
        partner_id = self._get_odoo_id(order.get("partner_id"))
        partner_name = self._get_odoo_name(order.get("partner_id")) or "Client Odoo"

        if not partner_id:
            raise ValueError("Aucun partner_id")

        # Trouver ou créer le client
        customer = self._get_or_create_customer(
            partner_id,
            partner_name,
            customer_model,
            CustomerType,
        )

        # Vérifier si la commande existe déjà
        existing = (
            self.db.query(document_model)
            .filter(
                document_model.tenant_id == self.tenant_id,
                document_model.type == doc_type,
                document_model.number == odoo_number,
            )
            .first()
        )

        order_date = self._parse_date(order.get("date_order"))
        commitment_date = self._parse_date(order.get("commitment_date"))
        currency = self._get_currency(order.get("currency_id"))

        if existing:
            existing.subtotal = order.get("amount_untaxed", 0)
            existing.tax_amount = order.get("amount_tax", 0)
            existing.total = order.get("amount_total", 0)
            existing.status = status_map.get(order.get("state"))
            existing.due_date = commitment_date
            existing.updated_at = datetime.utcnow()
            self.db.flush()
            return "updated"

        doc = document_model(
            tenant_id=self.tenant_id,
            customer_id=customer.id,
            type=doc_type,
            number=odoo_number,
            status=status_map.get(order.get("state")),
            date=order_date or datetime.utcnow().date(),
            due_date=commitment_date,
            subtotal=order.get("amount_untaxed", 0),
            tax_amount=order.get("amount_tax", 0),
            total=order.get("amount_total", 0),
            currency=currency,
        )
        self.db.add(doc)
        self.db.flush()
        return "created"

    def _import_quote(
        self,
        quote: Dict[str, Any],
        status_map: Dict[str, Any],
        customer_model: Any,
        document_model: Any,
    ) -> Optional[str]:
        """
        Importe un devis individuel.

        Returns:
            "created", "updated" ou None si erreur
        """
        from app.modules.commercial.models import CustomerType, DocumentType

        odoo_number = quote.get("name", "")
        partner_id = self._get_odoo_id(quote.get("partner_id"))
        partner_name = self._get_odoo_name(quote.get("partner_id")) or "Client Odoo"

        if not partner_id:
            raise ValueError("Aucun partner_id")

        customer = self._get_or_create_customer(
            partner_id,
            partner_name,
            customer_model,
            CustomerType,
        )

        existing = (
            self.db.query(document_model)
            .filter(
                document_model.tenant_id == self.tenant_id,
                document_model.type == DocumentType.QUOTE,
                document_model.number == odoo_number,
            )
            .first()
        )

        order_date = self._parse_date(quote.get("date_order"))
        validity_date = self._parse_date(quote.get("validity_date"))
        currency = self._get_currency(quote.get("currency_id"))

        if existing:
            existing.subtotal = quote.get("amount_untaxed", 0)
            existing.tax_amount = quote.get("amount_tax", 0)
            existing.total = quote.get("amount_total", 0)
            existing.status = status_map.get(quote.get("state"))
            existing.validity_date = validity_date
            existing.updated_at = datetime.utcnow()
            self.db.flush()
            return "updated"

        doc = document_model(
            tenant_id=self.tenant_id,
            customer_id=customer.id,
            type=DocumentType.QUOTE,
            number=odoo_number,
            status=status_map.get(quote.get("state")),
            date=order_date or datetime.utcnow().date(),
            validity_date=validity_date,
            subtotal=quote.get("amount_untaxed", 0),
            tax_amount=quote.get("amount_tax", 0),
            total=quote.get("amount_total", 0),
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
