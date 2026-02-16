"""
AZALS MODULE - Odoo Import Preview Service
============================================

Service de prévisualisation des données Odoo avant import.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from app.modules.odoo_import.models import OdooConnectionConfig

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class PreviewService(BaseOdooService[OdooConnectionConfig]):
    """Service de prévisualisation des données Odoo."""

    model = OdooConnectionConfig

    def preview(
        self,
        config_id: UUID,
        model: str,
        limit: int = 10,
        domain: List[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Prévisualise les données Odoo avant import.

        Args:
            config_id: ID de la configuration
            model: Modèle Odoo (product.product, res.partner, etc.)
            limit: Nombre de records à prévisualiser
            domain: Filtre de domaine Odoo optionnel

        Returns:
            Dictionnaire contenant:
            - model: Nom du modèle
            - total_count: Nombre total d'enregistrements
            - preview_count: Nombre de records prévisualisés
            - fields: Liste des champs récupérés
            - odoo_records: Données brutes Odoo
            - mapped_records: Données après mapping AZALS
        """
        config = self._require_config(config_id)

        connector = self._get_connector(config)
        mapper = self._get_mapper(config_id)

        # Récupérer les champs à mapper
        fields = mapper.get_odoo_fields(model)

        # Récupérer les enregistrements
        records = connector.search_read(
            model,
            domain or [],
            fields,
            limit=limit,
        )

        # Compter le total
        total_count = connector.search_count(model, domain or [])

        # Mapper les enregistrements
        mapped_records = mapper.map_records(model, records, self.tenant_id)

        # Nettoyer les champs internes pour l'affichage
        for rec in mapped_records:
            rec.pop("_odoo_id", None)
            rec.pop("_odoo_model", None)

        return {
            "model": model,
            "total_count": total_count,
            "preview_count": len(records),
            "fields": fields,
            "odoo_records": records,
            "mapped_records": mapped_records,
        }

    def preview_products(
        self,
        config_id: UUID,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Prévisualise les produits.

        Args:
            config_id: ID de la configuration
            limit: Nombre de produits à prévisualiser

        Returns:
            Données de prévisualisation
        """
        return self.preview(
            config_id,
            "product.product",
            limit,
            [("active", "in", [True, False])],
        )

    def preview_contacts(
        self,
        config_id: UUID,
        limit: int = 10,
        customers_only: bool = True,
    ) -> Dict[str, Any]:
        """
        Prévisualise les contacts.

        Args:
            config_id: ID de la configuration
            limit: Nombre de contacts à prévisualiser
            customers_only: Si True, uniquement les clients

        Returns:
            Données de prévisualisation
        """
        domain = [("is_company", "=", True)]
        if customers_only:
            domain.append(("customer_rank", ">", 0))

        return self.preview(config_id, "res.partner", limit, domain)

    def preview_suppliers(
        self,
        config_id: UUID,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Prévisualise les fournisseurs.

        Args:
            config_id: ID de la configuration
            limit: Nombre de fournisseurs à prévisualiser

        Returns:
            Données de prévisualisation
        """
        return self.preview(
            config_id,
            "res.partner",
            limit,
            [("supplier_rank", ">", 0)],
        )

    def preview_invoices(
        self,
        config_id: UUID,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Prévisualise les factures.

        Args:
            config_id: ID de la configuration
            limit: Nombre de factures à prévisualiser

        Returns:
            Données de prévisualisation
        """
        return self.preview(
            config_id,
            "account.move",
            limit,
            [
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
            ],
        )

    def preview_orders(
        self,
        config_id: UUID,
        limit: int = 10,
        include_drafts: bool = False,
    ) -> Dict[str, Any]:
        """
        Prévisualise les commandes de vente.

        Args:
            config_id: ID de la configuration
            limit: Nombre de commandes à prévisualiser
            include_drafts: Si True, inclut les brouillons/devis

        Returns:
            Données de prévisualisation
        """
        domain = []
        if not include_drafts:
            domain = [("state", "not in", ["draft", "sent", "cancel"])]

        return self.preview(config_id, "sale.order", limit, domain)

    def preview_accounting(
        self,
        config_id: UUID,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Prévisualise les écritures comptables.

        Args:
            config_id: ID de la configuration
            limit: Nombre d'écritures à prévisualiser

        Returns:
            Données de prévisualisation
        """
        return self.preview(
            config_id,
            "account.move",
            limit,
            [("state", "=", "posted")],
        )

    def get_available_models(self, config_id: UUID) -> Dict[str, Any]:
        """
        Récupère la liste des modèles disponibles sur le serveur Odoo.

        Args:
            config_id: ID de la configuration

        Returns:
            Dictionnaire avec les modèles supportés et leur disponibilité
        """
        config = self._require_config(config_id)
        connector = self._get_connector(config)

        models = {
            "products": {
                "model": "product.product",
                "available": False,
                "count": 0,
            },
            "contacts": {
                "model": "res.partner",
                "available": False,
                "count": 0,
            },
            "invoices": {
                "model": "account.move",
                "available": False,
                "count": 0,
            },
            "orders": {
                "model": "sale.order",
                "available": False,
                "count": 0,
            },
            "purchase_orders": {
                "model": "purchase.order",
                "available": False,
                "count": 0,
            },
            "accounting": {
                "model": "account.account",
                "available": False,
                "count": 0,
            },
            "interventions": {
                "model": "intervention.intervention",
                "available": False,
                "count": 0,
            },
            "projects": {
                "model": "project.task",
                "available": False,
                "count": 0,
            },
            "helpdesk": {
                "model": "helpdesk.ticket",
                "available": False,
                "count": 0,
            },
        }

        for key, info in models.items():
            try:
                count = connector.search_count(info["model"], [])
                info["available"] = True
                info["count"] = count
            except Exception:
                # Modèle non disponible
                pass

        return {
            "models": models,
            "summary": {
                "total_available": sum(
                    1 for m in models.values() if m["available"]
                ),
                "total_records": sum(m["count"] for m in models.values()),
            },
        }
