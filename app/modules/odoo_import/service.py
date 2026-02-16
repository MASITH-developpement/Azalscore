"""
AZALS MODULE - Odoo Import Service (Refactorisé)
=================================================

Service façade qui délègue aux sous-services modulaires.
Maintient la compatibilité avec l'API existante.

Architecture:
- OdooImportService (façade) → Délègue aux sous-services
- ConfigService → Gestion des configurations
- ConnectionService → Test de connexion
- ProductImportService → Import produits
- ContactImportService → Import contacts/fournisseurs
- OrderImportService → Import commandes
- InvoiceImportService → Import factures
- AccountingImportService → Import comptabilité
- InterventionImportService → Import interventions
- HistoryService → Historique et statistiques
- PreviewService → Prévisualisation

Migration depuis service.py (2465 lignes) → ~350 lignes
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.odoo_import.models import (
    OdooConnectionConfig,
    OdooImportHistory,
    OdooSyncType,
)

from .services import (
    AccountingImportService,
    ConfigService,
    ConnectionService,
    ContactImportService,
    HistoryService,
    InterventionImportService,
    InvoiceImportService,
    OrderImportService,
    PreviewService,
    ProductImportService,
)

logger = logging.getLogger(__name__)


class OdooImportService:
    """
    Service façade pour les imports Odoo.

    Délègue aux sous-services spécialisés tout en maintenant
    l'interface publique existante pour la compatibilité.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        user_id: Optional[str] = None,
    ):
        """
        Initialise le service avec ses sous-services.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour isolation multi-tenant
            user_id: ID de l'utilisateur pour audit
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Initialiser les sous-services
        self._config = ConfigService(db, tenant_id, user_id)
        self._connection = ConnectionService(db, tenant_id, user_id)
        self._products = ProductImportService(db, tenant_id, user_id)
        self._contacts = ContactImportService(db, tenant_id, user_id)
        self._orders = OrderImportService(db, tenant_id, user_id)
        self._invoices = InvoiceImportService(db, tenant_id, user_id)
        self._accounting = AccountingImportService(db, tenant_id, user_id)
        self._interventions = InterventionImportService(db, tenant_id, user_id)
        self._history = HistoryService(db, tenant_id, user_id)
        self._preview = PreviewService(db, tenant_id, user_id)

    # =========================================================================
    # CONFIGURATION (délégation)
    # =========================================================================

    def create_config(
        self,
        name: str,
        odoo_url: str,
        odoo_database: str,
        username: str,
        credential: str,
        auth_method: str = "api_key",
        **kwargs,
    ) -> OdooConnectionConfig:
        """Crée une nouvelle configuration de connexion Odoo."""
        return self._config.create(
            name=name,
            odoo_url=odoo_url,
            odoo_database=odoo_database,
            username=username,
            credential=credential,
            auth_method=auth_method,
            **kwargs,
        )

    def update_config(
        self,
        config_id: UUID,
        **kwargs,
    ) -> Optional[OdooConnectionConfig]:
        """Met à jour une configuration existante."""
        return self._config.update(config_id, **kwargs)

    def delete_config(self, config_id: UUID) -> bool:
        """Supprime une configuration."""
        return self._config.delete(config_id)

    def get_config(self, config_id: UUID) -> Optional[OdooConnectionConfig]:
        """Récupère une configuration par ID."""
        return self._config.get_config(config_id)

    def list_configs(self, active_only: bool = False) -> List[OdooConnectionConfig]:
        """Liste les configurations du tenant."""
        return self._config.list(active_only)

    # =========================================================================
    # TEST DE CONNEXION (délégation)
    # =========================================================================

    def test_connection(
        self,
        odoo_url: str,
        odoo_database: str,
        username: str,
        credential: str,
        auth_method: str = "api_key",
    ) -> Dict[str, Any]:
        """Teste une connexion Odoo."""
        return self._connection.test(
            odoo_url=odoo_url,
            odoo_database=odoo_database,
            username=username,
            credential=credential,
            auth_method=auth_method,
        )

    def test_config_connection(self, config_id: UUID) -> Dict[str, Any]:
        """Teste la connexion d'une configuration existante."""
        return self._connection.test_config(config_id)

    # =========================================================================
    # IMPORTS (délégation)
    # =========================================================================

    def import_products(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les produits depuis Odoo."""
        return self._products.import_products(config_id, full_sync)

    def import_contacts(
        self,
        config_id: UUID,
        full_sync: bool = False,
        include_suppliers: bool = False,
    ) -> OdooImportHistory:
        """Importe les contacts/clients depuis Odoo."""
        return self._contacts.import_contacts(config_id, full_sync, include_suppliers)

    def import_suppliers(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les fournisseurs depuis Odoo."""
        return self._contacts.import_suppliers(config_id, full_sync)

    def import_purchase_orders(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les commandes d'achat depuis Odoo."""
        return self._orders.import_purchase_orders(config_id, full_sync)

    def import_sale_orders(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les commandes de vente depuis Odoo."""
        return self._orders.import_sale_orders(config_id, full_sync)

    def import_quotes(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les devis depuis Odoo."""
        return self._orders.import_quotes(config_id, full_sync)

    def import_invoices(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les factures depuis Odoo."""
        return self._invoices.import_invoices(config_id, full_sync)

    def import_accounting(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les écritures comptables depuis Odoo."""
        return self._accounting.import_accounting(config_id, full_sync)

    def import_bank_statements(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les relevés bancaires depuis Odoo."""
        return self._accounting.import_bank_statements(config_id, full_sync)

    def import_interventions(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """Importe les interventions depuis Odoo."""
        return self._interventions.import_interventions(config_id, full_sync)

    # =========================================================================
    # FULL SYNC (orchestration)
    # =========================================================================

    def full_sync(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> List[OdooImportHistory]:
        """
        Effectue une synchronisation complète (tous les types activés).

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore les deltas

        Returns:
            Liste des historiques d'import
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvée")

        histories = []

        if config.sync_products:
            histories.append(self.import_products(config_id, full_sync))

        if config.sync_contacts:
            histories.append(self.import_contacts(config_id, full_sync))

        if config.sync_suppliers:
            histories.append(self.import_suppliers(config_id, full_sync))

        if getattr(config, "sync_purchase_orders", False):
            histories.append(self.import_purchase_orders(config_id, full_sync))

        if getattr(config, "sync_sale_orders", False):
            histories.append(self.import_sale_orders(config_id, full_sync))

        if getattr(config, "sync_invoices", False):
            histories.append(self.import_invoices(config_id, full_sync))

        if getattr(config, "sync_quotes", False):
            histories.append(self.import_quotes(config_id, full_sync))

        if getattr(config, "sync_accounting", False):
            histories.append(self.import_accounting(config_id, full_sync))

        if getattr(config, "sync_bank", False):
            histories.append(self.import_bank_statements(config_id, full_sync))

        if getattr(config, "sync_interventions", False):
            histories.append(self.import_interventions(config_id, full_sync))

        return histories

    # =========================================================================
    # HISTORIQUE (délégation)
    # =========================================================================

    def get_import_history(
        self,
        config_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[OdooImportHistory]:
        """Récupère l'historique des imports."""
        return self._history.list(config_id=config_id, limit=limit)

    def get_stats(self, config_id: UUID) -> Dict[str, Any]:
        """Récupère les statistiques d'une configuration."""
        return self._history.get_stats(config_id)

    # =========================================================================
    # PREVIEW (délégation)
    # =========================================================================

    def preview_data(
        self,
        config_id: UUID,
        model: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Prévisualise les données Odoo avant import."""
        return self._preview.preview(config_id, model, limit)


def get_odoo_import_service(
    db: Session,
    tenant_id: str,
    user_id: Optional[str] = None,
) -> OdooImportService:
    """Factory function pour le service Odoo Import."""
    return OdooImportService(db, tenant_id, user_id)
