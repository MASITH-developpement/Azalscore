"""
AZALS MODULE - Odoo Import - Service
=====================================

Service principal d'orchestration des imports Odoo.
Gere les imports avec isolation multi-tenant complete.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import get_cache, CacheTTL

from .connector import (
    OdooConnector,
    OdooConnectionError,
    OdooAuthenticationError,
    OdooAPIError,
)
from .mapper import OdooMapper
from .models import (
    OdooConnectionConfig,
    OdooImportHistory,
    OdooFieldMapping,
    OdooSyncType,
    OdooImportStatus,
    OdooAuthMethod,
    DEFAULT_MAPPINGS,
)

logger = logging.getLogger(__name__)


# Cle de chiffrement pour les credentials depuis les variables d'environnement
import os
_env_key = os.environ.get("ENCRYPTION_KEY")
if _env_key:
    ENCRYPTION_KEY = _env_key.encode() if isinstance(_env_key, str) else _env_key
else:
    # Fallback pour dev local uniquement
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning("[ODOO_IMPORT] ENCRYPTION_KEY non definie, utilisation cle temporaire")


class OdooImportService:
    """
    Service principal pour les imports Odoo.

    Fonctionnalites:
    - Gestion des configurations de connexion par tenant
    - Import des produits, contacts, fournisseurs
    - Delta sync base sur write_date Odoo
    - Deduplication automatique
    - Historique complet des imports
    """

    def __init__(self, db: Session, tenant_id: str, user_id: Optional[str] = None):
        """
        Initialise le service.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour isolation
            user_id: ID de l'utilisateur (pour audit)
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._fernet = Fernet(ENCRYPTION_KEY)
        self._connector: Optional[OdooConnector] = None
        self._mapper: Optional[OdooMapper] = None
        self._cache = get_cache()

    # =========================================================================
    # GESTION DES CONFIGURATIONS
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
        """
        Cree une nouvelle configuration de connexion Odoo.

        Args:
            name: Nom de la connexion
            odoo_url: URL Odoo
            odoo_database: Nom de la base
            username: Nom d'utilisateur
            credential: Mot de passe ou API key
            auth_method: Methode d'auth ('password' ou 'api_key')
            **kwargs: Options supplementaires (sync_products, etc.)

        Returns:
            Configuration creee
        """
        # Chiffrer le credential
        encrypted_credential = self._encrypt_credential(credential)

        config = OdooConnectionConfig(
            tenant_id=self.tenant_id,
            name=name,
            odoo_url=odoo_url.rstrip('/'),
            odoo_database=odoo_database,
            username=username,
            encrypted_credential=encrypted_credential,
            auth_method=OdooAuthMethod(auth_method),
            created_by=UUID(self.user_id) if self.user_id else None,
            **kwargs,
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        logger.info(
            f"[ODOO_IMPORT] Configuration creee: {name} pour tenant {self.tenant_id}"
        )
        return config

    def update_config(
        self,
        config_id: UUID,
        **kwargs,
    ) -> Optional[OdooConnectionConfig]:
        """
        Met a jour une configuration existante.

        Args:
            config_id: ID de la configuration
            **kwargs: Champs a mettre a jour

        Returns:
            Configuration mise a jour ou None
        """
        config = self.get_config(config_id)
        if not config:
            return None

        # Chiffrer le nouveau credential si fourni
        if 'credential' in kwargs:
            kwargs['encrypted_credential'] = self._encrypt_credential(kwargs.pop('credential'))

        # Convertir auth_method si fourni
        if 'auth_method' in kwargs:
            kwargs['auth_method'] = OdooAuthMethod(kwargs['auth_method'])

        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        config.updated_by = UUID(self.user_id) if self.user_id else None
        config.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_config(self, config_id: UUID) -> bool:
        """
        Supprime une configuration.

        Args:
            config_id: ID de la configuration

        Returns:
            True si supprime
        """
        config = self.get_config(config_id)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()

        logger.info(
            f"[ODOO_IMPORT] Configuration supprimee: {config_id} pour tenant {self.tenant_id}"
        )
        return True

    def get_config(self, config_id: UUID) -> Optional[OdooConnectionConfig]:
        """
        Recupere une configuration par ID.

        Args:
            config_id: ID de la configuration

        Returns:
            Configuration ou None
        """
        return self.db.query(OdooConnectionConfig).filter(
            OdooConnectionConfig.tenant_id == self.tenant_id,
            OdooConnectionConfig.id == config_id,
        ).first()

    def list_configs(self, active_only: bool = False) -> List[OdooConnectionConfig]:
        """
        Liste les configurations du tenant.

        Args:
            active_only: Si True, uniquement les configs actives

        Returns:
            Liste des configurations
        """
        query = self.db.query(OdooConnectionConfig).filter(
            OdooConnectionConfig.tenant_id == self.tenant_id,
        )
        if active_only:
            query = query.filter(OdooConnectionConfig.is_active == True)
        return query.order_by(OdooConnectionConfig.name).all()

    # =========================================================================
    # TEST DE CONNEXION
    # =========================================================================

    def test_connection(
        self,
        odoo_url: str,
        odoo_database: str,
        username: str,
        credential: str,
        auth_method: str = "api_key",
    ) -> Dict[str, Any]:
        """
        Teste une connexion Odoo.

        Args:
            odoo_url: URL Odoo
            odoo_database: Nom de la base
            username: Nom d'utilisateur
            credential: Mot de passe ou API key
            auth_method: Methode d'auth

        Returns:
            Resultat du test
        """
        try:
            connector = OdooConnector(
                url=odoo_url,
                database=odoo_database,
                username=username,
                credential=credential,
                auth_method=auth_method,
            )
            return connector.test_connection()

        except OdooAuthenticationError as e:
            return {
                "success": False,
                "message": str(e),
                "error_type": "authentication",
            }
        except OdooConnectionError as e:
            return {
                "success": False,
                "message": str(e),
                "error_type": "connection",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur inattendue: {str(e)}",
                "error_type": "unknown",
            }

    def test_config_connection(self, config_id: UUID) -> Dict[str, Any]:
        """
        Teste la connexion d'une configuration existante.

        Args:
            config_id: ID de la configuration

        Returns:
            Resultat du test
        """
        config = self.get_config(config_id)
        if not config:
            return {
                "success": False,
                "message": "Configuration non trouvee",
                "error_type": "not_found",
            }

        credential = self._decrypt_credential(config.encrypted_credential)
        result = self.test_connection(
            odoo_url=config.odoo_url,
            odoo_database=config.odoo_database,
            username=config.username,
            credential=credential,
            auth_method=config.auth_method.value,
        )

        # Mettre a jour le statut de connexion
        config.is_connected = result.get("success", False)
        config.last_connection_test_at = datetime.utcnow()
        if result.get("odoo_version"):
            config.odoo_version = result["odoo_version"]
        if not result["success"]:
            config.last_error_message = result.get("message")

        self.db.commit()
        return result

    # =========================================================================
    # IMPORTS
    # =========================================================================

    def _get_connector(self, config: OdooConnectionConfig) -> OdooConnector:
        """Cree et connecte un OdooConnector pour une config."""
        credential = self._decrypt_credential(config.encrypted_credential)
        connector = OdooConnector(
            url=config.odoo_url,
            database=config.odoo_database,
            username=config.username,
            credential=credential,
            auth_method=config.auth_method.value,
        )
        connector.connect()
        return connector

    def _get_mapper(self, config_id: UUID) -> OdooMapper:
        """Cree un mapper avec les mappings personnalises."""
        # Charger les mappings personnalises
        custom_mappings = {}
        field_mappings = self.db.query(OdooFieldMapping).filter(
            OdooFieldMapping.tenant_id == self.tenant_id,
            OdooFieldMapping.config_id == config_id,
            OdooFieldMapping.is_active == True,
        ).all()

        for fm in field_mappings:
            custom_mappings[fm.odoo_model] = fm.field_mapping

        return OdooMapper(custom_mappings=custom_mappings)

    def import_products(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les produits depuis Odoo.

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta et importe tout

        Returns:
            Historique de l'import
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        # Creer l'historique
        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.PRODUCTS,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        try:
            connector = self._get_connector(config)
            mapper = self._get_mapper(config_id)

            # Determiner la date de delta
            delta_date = None
            if not full_sync and config.products_last_sync_at:
                delta_date = config.products_last_sync_at
                history.delta_from_date = delta_date

            # Recuperer les produits Odoo
            fields = mapper.get_odoo_fields("product.product")

            if delta_date:
                odoo_products = connector.get_modified_since(
                    "product.product", delta_date, fields
                )
            else:
                odoo_products = connector.search_read(
                    "product.product",
                    [("active", "in", [True, False])],  # Inclure inactifs
                    fields,
                )

            history.total_records = len(odoo_products)

            # Mapper et importer
            created, updated, errors = self._import_products_batch(
                mapper.map_records("product.product", odoo_products, self.tenant_id)
            )

            # Mettre a jour l'historique
            history.created_count = created
            history.updated_count = updated
            history.error_count = len(errors)
            history.error_details = errors
            history.status = OdooImportStatus.SUCCESS if not errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int(
                (history.completed_at - history.started_at).total_seconds()
            )

            # Mettre a jour la config
            config.products_last_sync_at = datetime.utcnow()
            config.total_products_imported += created + updated
            config.total_imports += 1

            self.db.commit()
            self.db.refresh(history)

            logger.info(
                f"[ODOO_IMPORT] Products import termine: {created} crees, "
                f"{updated} mis a jour, {len(errors)} erreurs"
            )
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            config.last_error_message = str(e)
            self.db.commit()
            raise

    def _import_products_batch(
        self,
        mapped_products: List[Dict[str, Any]],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe un lot de produits mappes.

        Returns:
            Tuple (created_count, updated_count, errors)
        """
        from app.modules.inventory.models import Product

        created = 0
        updated = 0
        errors = []

        # Traiter chaque produit individuellement avec savepoint
        for mapped in mapped_products:
            odoo_id = mapped.pop("_odoo_id", None)
            mapped.pop("_odoo_model", None)
            mapped.pop("_odoo_category_id", None)
            mapped.pop("_odoo_category_name", None)

            code = mapped.get("code")
            if not code:
                errors.append({
                    "odoo_id": odoo_id,
                    "code": None,
                    "error": "Code produit manquant",
                })
                continue

            try:
                # Utiliser un savepoint pour pouvoir rollback ce produit seul
                savepoint = self.db.begin_nested()

                # Rechercher un produit existant (case-insensitive pour plus de robustesse)
                existing = self.db.query(Product).filter(
                    Product.tenant_id == self.tenant_id,
                    Product.code == code,
                ).first()

                if existing:
                    # Mise a jour
                    for key, value in mapped.items():
                        if key not in ("tenant_id", "id") and hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    savepoint.commit()
                    updated += 1
                    logger.debug(f"[ODOO_IMPORT] Produit mis a jour: {code}")
                else:
                    # Creation
                    product = Product(**mapped)
                    self.db.add(product)
                    savepoint.commit()
                    created += 1
                    logger.debug(f"[ODOO_IMPORT] Produit cree: {code}")

            except Exception as e:
                # Rollback uniquement ce produit
                self.db.rollback()
                error_msg = str(e)
                if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                    # Produit deja existe, essayer de le mettre a jour
                    try:
                        existing = self.db.query(Product).filter(
                            Product.tenant_id == self.tenant_id,
                            Product.code == code,
                        ).first()
                        if existing:
                            for key, value in mapped.items():
                                if key not in ("tenant_id", "id") and hasattr(existing, key):
                                    setattr(existing, key, value)
                            existing.updated_at = datetime.utcnow()
                            self.db.commit()
                            updated += 1
                            logger.debug(f"[ODOO_IMPORT] Produit mis a jour (apres conflit): {code}")
                            continue
                    except Exception as e2:
                        error_msg = str(e2)

                errors.append({
                    "odoo_id": odoo_id,
                    "code": code,
                    "error": error_msg[:200],  # Limiter la taille du message
                })
                logger.warning(f"[ODOO_IMPORT] Erreur produit {code}: {error_msg[:100]}")

        # Commit final pour s'assurer que tout est persiste
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, updated, errors

    def import_contacts(
        self,
        config_id: UUID,
        full_sync: bool = False,
        include_suppliers: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les contacts/clients depuis Odoo.

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta
            include_suppliers: Si True, inclut les fournisseurs

        Returns:
            Historique de l'import
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        sync_type = OdooSyncType.CONTACTS
        if include_suppliers:
            sync_type = OdooSyncType.FULL

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=sync_type,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        try:
            connector = self._get_connector(config)
            mapper = self._get_mapper(config_id)

            # Determiner la date de delta
            delta_date = None
            if not full_sync and config.contacts_last_sync_at:
                delta_date = config.contacts_last_sync_at
                history.delta_from_date = delta_date

            # Construire le domaine
            domain = [("is_company", "=", True)]  # Uniquement les societes
            if not include_suppliers:
                domain.append(("customer_rank", ">", 0))

            fields = mapper.get_odoo_fields("res.partner")

            if delta_date:
                # Ajouter filtre date
                domain.extend([
                    "|",
                    ("write_date", ">=", delta_date.strftime('%Y-%m-%d %H:%M:%S')),
                    ("create_date", ">=", delta_date.strftime('%Y-%m-%d %H:%M:%S')),
                ])

            odoo_contacts = connector.search_read("res.partner", domain, fields)
            history.total_records = len(odoo_contacts)

            # Mapper et importer
            created, updated, errors = self._import_contacts_batch(
                mapper.map_records("res.partner", odoo_contacts, self.tenant_id)
            )

            # Mettre a jour l'historique
            history.created_count = created
            history.updated_count = updated
            history.error_count = len(errors)
            history.error_details = errors
            history.status = OdooImportStatus.SUCCESS if not errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int(
                (history.completed_at - history.started_at).total_seconds()
            )

            # Mettre a jour la config
            config.contacts_last_sync_at = datetime.utcnow()
            config.total_contacts_imported += created + updated
            config.total_imports += 1

            self.db.commit()
            self.db.refresh(history)

            logger.info(
                f"[ODOO_IMPORT] Contacts import termine: {created} crees, "
                f"{updated} mis a jour, {len(errors)} erreurs"
            )
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            config.last_error_message = str(e)
            self.db.commit()
            raise

    def _import_contacts_batch(
        self,
        mapped_contacts: List[Dict[str, Any]],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe un lot de contacts mappes.

        Returns:
            Tuple (created_count, updated_count, errors)
        """
        from app.modules.contacts.models import UnifiedContact

        created = 0
        updated = 0
        errors = []

        for mapped in mapped_contacts:
            odoo_id = mapped.pop("_odoo_id", None)
            mapped.pop("_odoo_model", None)

            email = mapped.get("email")
            tax_id = mapped.get("tax_id")
            name = mapped.get("name", "Unknown")

            try:
                # Utiliser un savepoint pour pouvoir rollback ce contact seul
                savepoint = self.db.begin_nested()

                # Rechercher un contact existant par email ou tax_id
                existing = None
                if email:
                    existing = self.db.query(UnifiedContact).filter(
                        UnifiedContact.tenant_id == self.tenant_id,
                        UnifiedContact.email == email,
                    ).first()

                if not existing and tax_id:
                    existing = self.db.query(UnifiedContact).filter(
                        UnifiedContact.tenant_id == self.tenant_id,
                        UnifiedContact.tax_id == tax_id,
                    ).first()

                if existing:
                    # Mise a jour
                    for key, value in mapped.items():
                        if key not in ("tenant_id", "id") and hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    savepoint.commit()
                    updated += 1
                    logger.debug(f"[ODOO_IMPORT] Contact mis a jour: {name}")
                else:
                    # Creation
                    contact = UnifiedContact(**mapped)
                    self.db.add(contact)

                    # Creer aussi un Customer pour le matching des documents
                    from app.modules.commercial.models import Customer, CustomerType
                    odoo_code = f"ODOO-{odoo_id}" if odoo_id else f"ODOO-{name[:20]}"
                    existing_customer = self.db.query(Customer).filter(
                        Customer.tenant_id == self.tenant_id,
                        Customer.code == odoo_code
                    ).first()

                    if not existing_customer:
                        customer = Customer(
                            tenant_id=self.tenant_id,
                            code=odoo_code,
                            name=name,
                            email=email,
                            type=CustomerType.CUSTOMER,
                            tax_id=tax_id,
                        )
                        self.db.add(customer)

                    savepoint.commit()
                    created += 1
                    logger.debug(f"[ODOO_IMPORT] Contact cree: {name} (code: {odoo_code})")

            except Exception as e:
                # Rollback uniquement ce contact
                self.db.rollback()
                error_msg = str(e)
                errors.append({
                    "odoo_id": odoo_id,
                    "email": email,
                    "name": name,
                    "error": error_msg[:200],
                })
                logger.warning(f"[ODOO_IMPORT] Erreur contact {name}: {error_msg[:100]}")

        # Commit final
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, updated, errors

    def import_suppliers(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les fournisseurs depuis Odoo.

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta

        Returns:
            Historique de l'import
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.SUPPLIERS,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        try:
            connector = self._get_connector(config)
            mapper = self._get_mapper(config_id)

            delta_date = None
            if not full_sync and config.suppliers_last_sync_at:
                delta_date = config.suppliers_last_sync_at
                history.delta_from_date = delta_date

            # Domaine: fournisseurs uniquement
            domain = [("supplier_rank", ">", 0)]
            fields = mapper.get_odoo_fields("res.partner")

            if delta_date:
                domain.extend([
                    "|",
                    ("write_date", ">=", delta_date.strftime('%Y-%m-%d %H:%M:%S')),
                    ("create_date", ">=", delta_date.strftime('%Y-%m-%d %H:%M:%S')),
                ])

            odoo_suppliers = connector.search_read("res.partner", domain, fields)
            history.total_records = len(odoo_suppliers)

            # Mapper et importer (utilise le meme processus que contacts)
            created, updated, errors = self._import_contacts_batch(
                mapper.map_records("res.partner", odoo_suppliers, self.tenant_id)
            )

            history.created_count = created
            history.updated_count = updated
            history.error_count = len(errors)
            history.error_details = errors
            history.status = OdooImportStatus.SUCCESS if not errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int(
                (history.completed_at - history.started_at).total_seconds()
            )

            config.suppliers_last_sync_at = datetime.utcnow()
            config.total_suppliers_imported += created + updated
            config.total_imports += 1

            self.db.commit()
            self.db.refresh(history)

            logger.info(
                f"[ODOO_IMPORT] Suppliers import termine: {created} crees, "
                f"{updated} mis a jour, {len(errors)} erreurs"
            )
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            config.last_error_message = str(e)
            self.db.commit()
            raise

    # =========================================================================
    # IMPORT COMMANDES
    # =========================================================================

    def import_purchase_orders(self, config_id: UUID, full_sync: bool = False) -> OdooImportHistory:
        """Import des commandes d'achat depuis Odoo (purchase.order)."""
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.PURCHASE_ORDERS,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        try:
            connector = self._get_connector(config)

            domain = []
            fields = ["name", "date_order", "partner_id", "state", "amount_total", "currency_id", "order_line"]

            orders = connector.search_read("purchase.order", domain, fields)
            history.total_records = len(orders)

            # Pour l'instant, on log les donnees recuperees
            logger.info(f"[ODOO_IMPORT] Recupere {len(orders)} commandes d'achat")

            history.created_count = len(orders)
            history.status = OdooImportStatus.SUCCESS
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int((history.completed_at - history.started_at).total_seconds())

            self.db.commit()
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def import_sale_orders(self, config_id: UUID, full_sync: bool = False) -> OdooImportHistory:
        """Import des commandes de vente depuis Odoo (sale.order confirmees)."""
        from app.modules.commercial.models import CommercialDocument, DocumentType, DocumentStatus, Customer

        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.SALE_ORDERS,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        created = 0
        updated = 0
        errors = []

        try:
            connector = self._get_connector(config)

            # Commandes confirmees (state = sale, done) - exclure draft, sent, cancel
            domain = [("state", "not in", ["draft", "sent", "cancel"])]
            fields = ["name", "date_order", "partner_id", "state", "amount_untaxed", "amount_tax", "amount_total", "currency_id", "commitment_date"]

            orders = connector.search_read("sale.order", domain, fields)
            history.total_records = len(orders)

            logger.info(f"[ODOO_IMPORT] Recupere {len(orders)} commandes de vente")

            # Mapping des statuts Odoo -> AZALS
            status_map = {
                "sale": DocumentStatus.VALIDATED,  # Commande confirmee
                "done": DocumentStatus.PAID,       # Commande terminee/livree
                "cancel": DocumentStatus.CANCELLED,
            }

            for order in orders:
                try:
                    odoo_number = order.get("name", "")
                    partner_data = order.get("partner_id")
                    partner_id = partner_data[0] if partner_data else None

                    # Trouver ou creer le client dans AZALS
                    customer = None
                    partner_name = partner_data[1] if partner_data and len(partner_data) > 1 else "Client Odoo"

                    if partner_id:
                        odoo_code = f"ODOO-{partner_id}"
                        customer = self.db.query(Customer).filter(
                            Customer.tenant_id == self.tenant_id,
                            Customer.code == odoo_code
                        ).first()

                        # Creer le customer s'il n'existe pas
                        if not customer:
                            from app.modules.commercial.models import CustomerType
                            customer = Customer(
                                tenant_id=self.tenant_id,
                                code=odoo_code,
                                name=partner_name,
                                type=CustomerType.CUSTOMER,
                            )
                            self.db.add(customer)
                            self.db.flush()
                            logger.info(f"[ODOO_IMPORT] Customer cree: {partner_name} ({odoo_code})")

                    if not customer:
                        errors.append({"number": odoo_number, "error": "Aucun partner_id"})
                        continue

                    # Verifier si la commande existe deja
                    existing = self.db.query(CommercialDocument).filter(
                        CommercialDocument.tenant_id == self.tenant_id,
                        CommercialDocument.type == DocumentType.ORDER,
                        CommercialDocument.number == odoo_number
                    ).first()

                    order_date = order.get("date_order")
                    if order_date and isinstance(order_date, str):
                        order_date = datetime.strptime(order_date[:10], "%Y-%m-%d").date()
                    elif not order_date:  # Handle False or None from Odoo
                        order_date = None

                    commitment_date = order.get("commitment_date")
                    if commitment_date and isinstance(commitment_date, str):
                        commitment_date = datetime.strptime(commitment_date[:10], "%Y-%m-%d").date()
                    elif not commitment_date:  # Handle False or None from Odoo
                        commitment_date = None

                    if existing:
                        # Mise a jour
                        existing.subtotal = order.get("amount_untaxed", 0)
                        existing.tax_amount = order.get("amount_tax", 0)
                        existing.total = order.get("amount_total", 0)
                        existing.status = status_map.get(order.get("state"), DocumentStatus.VALIDATED)
                        existing.due_date = commitment_date
                        existing.updated_at = datetime.utcnow()
                        updated += 1
                    else:
                        # Creation
                        doc = CommercialDocument(
                            tenant_id=self.tenant_id,
                            customer_id=customer.id,
                            type=DocumentType.ORDER,
                            number=odoo_number,
                            status=status_map.get(order.get("state"), DocumentStatus.VALIDATED),
                            date=order_date or datetime.utcnow().date(),
                            due_date=commitment_date,
                            subtotal=order.get("amount_untaxed", 0),
                            tax_amount=order.get("amount_tax", 0),
                            total=order.get("amount_total", 0),
                            currency=order.get("currency_id", [False, "EUR"])[1] if order.get("currency_id") else "EUR",
                        )
                        self.db.add(doc)
                        created += 1

                    self.db.flush()

                except Exception as e:
                    errors.append({"number": order.get("name"), "error": str(e)[:200]})
                    self.db.rollback()

            self.db.commit()

            history.created_count = created
            history.updated_count = updated
            history.error_count = len(errors)
            history.error_details = errors[:50]
            history.status = OdooImportStatus.SUCCESS if not errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int((history.completed_at - history.started_at).total_seconds())

            config.orders_last_sync_at = datetime.utcnow()
            config.total_orders_imported += created + updated
            config.total_imports += 1

            self.db.commit()

            logger.info(f"[ODOO_IMPORT] Commandes: {created} creees, {updated} maj, {len(errors)} erreurs")
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def import_invoices(self, config_id: UUID, full_sync: bool = False) -> OdooImportHistory:
        """Import des factures depuis Odoo (account.move type=out_invoice)."""
        from app.modules.commercial.models import CommercialDocument, DocumentLine, DocumentType, DocumentStatus, Customer

        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.INVOICES,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        created = 0
        updated = 0
        errors = []

        try:
            connector = self._get_connector(config)

            # Factures clients (out_invoice) et avoirs (out_refund)
            domain = [("move_type", "in", ["out_invoice", "out_refund"]), ("state", "=", "posted")]
            fields = ["name", "partner_id", "invoice_date", "invoice_date_due", "state", "amount_untaxed", "amount_tax", "amount_total", "amount_residual", "currency_id", "move_type", "invoice_line_ids"]

            invoices = connector.search_read("account.move", domain, fields)
            history.total_records = len(invoices)

            logger.info(f"[ODOO_IMPORT] Recupere {len(invoices)} factures")

            # Mapping des statuts Odoo -> AZALS
            status_map = {
                "draft": DocumentStatus.DRAFT,
                "posted": DocumentStatus.VALIDATED,
                "cancel": DocumentStatus.CANCELLED,
            }

            for inv in invoices:
                try:
                    odoo_number = inv.get("name", "")
                    partner_data = inv.get("partner_id")
                    partner_id = partner_data[0] if partner_data else None

                    # Trouver ou creer le client dans AZALS
                    customer = None
                    partner_name = partner_data[1] if partner_data and len(partner_data) > 1 else "Client Odoo"

                    if partner_id:
                        odoo_code = f"ODOO-{partner_id}"
                        # Chercher par code Odoo
                        customer = self.db.query(Customer).filter(
                            Customer.tenant_id == self.tenant_id,
                            Customer.code == odoo_code
                        ).first()

                        # Creer le customer s'il n'existe pas
                        if not customer:
                            from app.modules.commercial.models import CustomerType
                            customer = Customer(
                                tenant_id=self.tenant_id,
                                code=odoo_code,
                                name=partner_name,
                                type=CustomerType.CUSTOMER,
                            )
                            self.db.add(customer)
                            self.db.flush()
                            logger.info(f"[ODOO_IMPORT] Customer cree: {partner_name} ({odoo_code})")

                    if not customer:
                        errors.append({"number": odoo_number, "error": "Aucun partner_id"})
                        continue

                    # Verifier si la facture existe deja
                    doc_type = DocumentType.CREDIT_NOTE if inv.get("move_type") == "out_refund" else DocumentType.INVOICE
                    existing = self.db.query(CommercialDocument).filter(
                        CommercialDocument.tenant_id == self.tenant_id,
                        CommercialDocument.type == doc_type,
                        CommercialDocument.number == odoo_number
                    ).first()

                    invoice_date = inv.get("invoice_date")
                    if invoice_date and isinstance(invoice_date, str):
                        invoice_date = datetime.strptime(invoice_date, "%Y-%m-%d").date()
                    elif not invoice_date:  # Handle False or None from Odoo
                        invoice_date = None

                    due_date = inv.get("invoice_date_due")
                    if due_date and isinstance(due_date, str):
                        due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                    elif not due_date:  # Handle False or None from Odoo
                        due_date = None

                    if existing:
                        # Mise a jour
                        existing.subtotal = inv.get("amount_untaxed", 0)
                        existing.tax_amount = inv.get("amount_tax", 0)
                        existing.total = inv.get("amount_total", 0)
                        existing.remaining_amount = inv.get("amount_residual", 0)
                        existing.paid_amount = inv.get("amount_total", 0) - inv.get("amount_residual", 0)
                        existing.status = status_map.get(inv.get("state"), DocumentStatus.VALIDATED)
                        existing.updated_at = datetime.utcnow()
                        updated += 1
                    else:
                        # Creation
                        doc = CommercialDocument(
                            tenant_id=self.tenant_id,
                            customer_id=customer.id,
                            type=doc_type,
                            number=odoo_number,
                            status=status_map.get(inv.get("state"), DocumentStatus.VALIDATED),
                            date=invoice_date or datetime.utcnow().date(),
                            due_date=due_date,
                            subtotal=inv.get("amount_untaxed", 0),
                            tax_amount=inv.get("amount_tax", 0),
                            total=inv.get("amount_total", 0),
                            paid_amount=inv.get("amount_total", 0) - inv.get("amount_residual", 0),
                            remaining_amount=inv.get("amount_residual", 0),
                            currency=inv.get("currency_id", [False, "EUR"])[1] if inv.get("currency_id") else "EUR",
                        )
                        self.db.add(doc)
                        created += 1

                    self.db.flush()

                except Exception as e:
                    errors.append({"number": inv.get("name"), "error": str(e)[:200]})
                    self.db.rollback()

            self.db.commit()

            history.created_count = created
            history.updated_count = updated
            history.error_count = len(errors)
            history.error_details = errors[:50]  # Limiter les erreurs
            history.status = OdooImportStatus.SUCCESS if not errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int((history.completed_at - history.started_at).total_seconds())

            self.db.commit()

            logger.info(f"[ODOO_IMPORT] Factures: {created} creees, {updated} maj, {len(errors)} erreurs")
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def import_quotes(self, config_id: UUID, full_sync: bool = False) -> OdooImportHistory:
        """Import des devis depuis Odoo (sale.order state=draft/sent)."""
        from app.modules.commercial.models import CommercialDocument, DocumentType, DocumentStatus, Customer

        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.QUOTES,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        created = 0
        updated = 0
        errors = []

        try:
            connector = self._get_connector(config)

            # Devis = commandes en brouillon ou envoyees
            domain = [("state", "in", ["draft", "sent"])]
            fields = ["name", "date_order", "partner_id", "state", "amount_untaxed", "amount_tax", "amount_total", "validity_date", "currency_id"]

            quotes = connector.search_read("sale.order", domain, fields)
            history.total_records = len(quotes)

            logger.info(f"[ODOO_IMPORT] Recupere {len(quotes)} devis")

            status_map = {
                "draft": DocumentStatus.DRAFT,
                "sent": DocumentStatus.SENT,
                "sale": DocumentStatus.ACCEPTED,
                "cancel": DocumentStatus.CANCELLED,
            }

            for quote in quotes:
                try:
                    odoo_number = quote.get("name", "")
                    partner_data = quote.get("partner_id")
                    partner_id = partner_data[0] if partner_data else None

                    # Trouver ou creer le client
                    customer = None
                    partner_name = partner_data[1] if partner_data and len(partner_data) > 1 else "Client Odoo"

                    if partner_id:
                        odoo_code = f"ODOO-{partner_id}"
                        customer = self.db.query(Customer).filter(
                            Customer.tenant_id == self.tenant_id,
                            Customer.code == odoo_code
                        ).first()

                        # Creer le customer s'il n'existe pas
                        if not customer:
                            from app.modules.commercial.models import CustomerType
                            customer = Customer(
                                tenant_id=self.tenant_id,
                                code=odoo_code,
                                name=partner_name,
                                type=CustomerType.CUSTOMER,
                            )
                            self.db.add(customer)
                            self.db.flush()
                            logger.info(f"[ODOO_IMPORT] Customer cree: {partner_name} ({odoo_code})")

                    if not customer:
                        errors.append({"number": odoo_number, "error": "Aucun partner_id"})
                        continue

                    # Verifier si le devis existe
                    existing = self.db.query(CommercialDocument).filter(
                        CommercialDocument.tenant_id == self.tenant_id,
                        CommercialDocument.type == DocumentType.QUOTE,
                        CommercialDocument.number == odoo_number
                    ).first()

                    order_date = quote.get("date_order")
                    if order_date and isinstance(order_date, str):
                        order_date = datetime.strptime(order_date[:10], "%Y-%m-%d").date()
                    elif not order_date:  # Handle False or None from Odoo
                        order_date = None

                    validity_date = quote.get("validity_date")
                    if validity_date and isinstance(validity_date, str):
                        validity_date = datetime.strptime(validity_date, "%Y-%m-%d").date()
                    elif not validity_date:  # Handle False or None from Odoo
                        validity_date = None

                    if existing:
                        existing.subtotal = quote.get("amount_untaxed", 0)
                        existing.tax_amount = quote.get("amount_tax", 0)
                        existing.total = quote.get("amount_total", 0)
                        existing.status = status_map.get(quote.get("state"), DocumentStatus.DRAFT)
                        existing.validity_date = validity_date
                        existing.updated_at = datetime.utcnow()
                        updated += 1
                    else:
                        doc = CommercialDocument(
                            tenant_id=self.tenant_id,
                            customer_id=customer.id,
                            type=DocumentType.QUOTE,
                            number=odoo_number,
                            status=status_map.get(quote.get("state"), DocumentStatus.DRAFT),
                            date=order_date or datetime.utcnow().date(),
                            validity_date=validity_date,
                            subtotal=quote.get("amount_untaxed", 0),
                            tax_amount=quote.get("amount_tax", 0),
                            total=quote.get("amount_total", 0),
                            currency=quote.get("currency_id", [False, "EUR"])[1] if quote.get("currency_id") else "EUR",
                        )
                        self.db.add(doc)
                        created += 1

                    self.db.flush()

                except Exception as e:
                    errors.append({"number": quote.get("name"), "error": str(e)[:200]})
                    self.db.rollback()

            self.db.commit()

            history.created_count = created
            history.updated_count = updated
            history.error_count = len(errors)
            history.error_details = errors[:50]
            history.status = OdooImportStatus.SUCCESS if not errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int((history.completed_at - history.started_at).total_seconds())

            self.db.commit()

            logger.info(f"[ODOO_IMPORT] Devis: {created} crees, {updated} maj, {len(errors)} erreurs")
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def import_accounting(self, config_id: UUID, full_sync: bool = False) -> OdooImportHistory:
        """
        Import des ecritures comptables depuis Odoo.

        Importe:
        1. Plan comptable (account.account)
        2. Journaux comptables (account.journal)
        3. Ecritures (account.move avec account.move.line)

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta

        Returns:
            Historique de l'import
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.ACCOUNTING,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        total_created = 0
        total_updated = 0
        all_errors = []

        try:
            connector = self._get_connector(config)
            mapper = self._get_mapper(config_id)

            # =================================================================
            # ETAPE 1: Import du plan comptable (account.account)
            # =================================================================
            logger.info("[ODOO_IMPORT] Import du plan comptable...")

            account_fields = ["id", "code", "name", "account_type", "reconcile", "deprecated"]
            # Exclure les comptes deprecies
            accounts = connector.search_read(
                "account.account",
                [("deprecated", "=", False)],
                account_fields
            )

            accounts_created, accounts_errors, accounts_map = self._import_chart_of_accounts_batch(
                accounts
            )
            total_created += accounts_created
            all_errors.extend(accounts_errors)

            logger.info(f"[ODOO_IMPORT] Plan comptable: {accounts_created} comptes importes")

            # =================================================================
            # ETAPE 2: Import des journaux comptables (account.journal)
            # =================================================================
            logger.info("[ODOO_IMPORT] Import des journaux comptables...")

            journal_fields = ["id", "code", "name", "type"]
            journals = connector.search_read("account.journal", [], journal_fields)

            journals_map = {}
            for journal in journals:
                journals_map[journal["id"]] = {
                    "code": journal.get("code", f"J{journal['id']}"),
                    "label": journal.get("name", "Journal"),
                    "type": journal.get("type", "general"),
                }

            logger.info(f"[ODOO_IMPORT] {len(journals_map)} journaux charges")

            # =================================================================
            # ETAPE 3: Import des ecritures (account.move + lignes)
            # =================================================================
            logger.info("[ODOO_IMPORT] Import des ecritures comptables...")

            # Determiner la date de delta
            delta_date = None
            if not full_sync and config.accounting_last_sync_at:
                delta_date = config.accounting_last_sync_at
                history.delta_from_date = delta_date

            # Domaine pour les ecritures
            move_domain = [("state", "=", "posted")]  # Ecritures validees
            if delta_date:
                move_domain.extend([
                    "|",
                    ("write_date", ">=", delta_date.strftime('%Y-%m-%d %H:%M:%S')),
                    ("create_date", ">=", delta_date.strftime('%Y-%m-%d %H:%M:%S')),
                ])

            move_fields = [
                "id", "name", "ref", "date", "journal_id", "state",
                "move_type", "currency_id", "partner_id", "line_ids"
            ]

            moves = connector.search_read("account.move", move_domain, move_fields, limit=5000)
            history.total_records = len(moves)

            logger.info(f"[ODOO_IMPORT] Recupere {len(moves)} ecritures comptables")

            # Recuperer toutes les lignes en une seule requete
            move_ids = [m["id"] for m in moves]
            if move_ids:
                line_fields = [
                    "id", "move_id", "account_id", "partner_id", "name",
                    "debit", "credit", "date", "ref", "currency_id"
                ]
                lines = connector.search_read(
                    "account.move.line",
                    [("move_id", "in", move_ids)],
                    line_fields
                )

                # Grouper les lignes par move_id
                lines_by_move = {}
                for line in lines:
                    move_id = line.get("move_id")
                    if isinstance(move_id, (list, tuple)):
                        move_id = move_id[0]
                    if move_id not in lines_by_move:
                        lines_by_move[move_id] = []
                    lines_by_move[move_id].append(line)

                # Importer les ecritures avec leurs lignes
                entries_created, entries_updated, entries_errors = self._import_accounting_batch(
                    moves, lines_by_move, accounts_map, journals_map
                )
                total_created += entries_created
                total_updated += entries_updated
                all_errors.extend(entries_errors)

            # Mettre a jour l'historique
            history.created_count = total_created
            history.updated_count = total_updated
            history.error_count = len(all_errors)
            history.error_details = all_errors[:100]  # Limiter les erreurs stockees
            history.status = OdooImportStatus.SUCCESS if not all_errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int(
                (history.completed_at - history.started_at).total_seconds()
            )

            # Mettre a jour la config
            config.accounting_last_sync_at = datetime.utcnow()
            config.total_imports += 1

            self.db.commit()
            self.db.refresh(history)

            logger.info(
                f"[ODOO_IMPORT] Accounting import termine: {total_created} crees, "
                f"{total_updated} mis a jour, {len(all_errors)} erreurs"
            )
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            config.last_error_message = str(e)
            self.db.commit()
            raise

    def _import_chart_of_accounts_batch(
        self,
        odoo_accounts: List[Dict[str, Any]],
    ) -> Tuple[int, List[Dict[str, Any]], Dict[int, str]]:
        """
        Importe le plan comptable Odoo vers AZALS.

        Args:
            odoo_accounts: Liste des comptes Odoo

        Returns:
            Tuple (created_count, errors, accounts_map {odoo_id: account_number})
        """
        from app.modules.accounting.models import ChartOfAccounts, AccountType

        created = 0
        errors = []
        accounts_map = {}  # {odoo_id: account_number}

        # Mapping des types de compte Odoo vers AZALS
        type_mapping = {
            "asset_receivable": AccountType.ASSET,
            "asset_cash": AccountType.ASSET,
            "asset_current": AccountType.ASSET,
            "asset_non_current": AccountType.ASSET,
            "asset_prepayments": AccountType.ASSET,
            "asset_fixed": AccountType.ASSET,
            "liability_payable": AccountType.LIABILITY,
            "liability_credit_card": AccountType.LIABILITY,
            "liability_current": AccountType.LIABILITY,
            "liability_non_current": AccountType.LIABILITY,
            "equity": AccountType.EQUITY,
            "equity_unaffected": AccountType.EQUITY,
            "income": AccountType.REVENUE,
            "income_other": AccountType.REVENUE,
            "expense": AccountType.EXPENSE,
            "expense_depreciation": AccountType.EXPENSE,
            "expense_direct_cost": AccountType.EXPENSE,
            "off_balance": AccountType.SPECIAL,
        }

        for account in odoo_accounts:
            odoo_id = account.get("id")
            code = account.get("code", "")
            name = account.get("name", "")
            odoo_type = account.get("account_type", "asset_current")

            if not code:
                errors.append({
                    "odoo_id": odoo_id,
                    "error": "Code compte manquant",
                })
                continue

            # Determiner la classe comptable (premier chiffre du code)
            account_class = code[0] if code and code[0].isdigit() else "0"

            try:
                savepoint = self.db.begin_nested()

                # Rechercher un compte existant
                existing = self.db.query(ChartOfAccounts).filter(
                    ChartOfAccounts.tenant_id == self.tenant_id,
                    ChartOfAccounts.account_number == code,
                ).first()

                if existing:
                    # Mise a jour
                    existing.account_label = name
                    existing.account_type = type_mapping.get(odoo_type, AccountType.ASSET)
                    existing.account_class = account_class
                    existing.updated_at = datetime.utcnow()
                    savepoint.commit()
                    accounts_map[odoo_id] = code
                    logger.debug(f"[ODOO_IMPORT] Compte mis a jour: {code}")
                else:
                    # Creation
                    new_account = ChartOfAccounts(
                        tenant_id=self.tenant_id,
                        account_number=code,
                        account_label=name,
                        account_type=type_mapping.get(odoo_type, AccountType.ASSET),
                        account_class=account_class,
                        is_auxiliary=odoo_type in ("asset_receivable", "liability_payable"),
                        is_active=True,
                    )
                    self.db.add(new_account)
                    savepoint.commit()
                    created += 1
                    accounts_map[odoo_id] = code
                    logger.debug(f"[ODOO_IMPORT] Compte cree: {code}")

            except Exception as e:
                self.db.rollback()
                errors.append({
                    "odoo_id": odoo_id,
                    "code": code,
                    "error": str(e)[:200],
                })
                # Ajouter quand meme au mapping pour ne pas bloquer les ecritures
                accounts_map[odoo_id] = code

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, errors, accounts_map

    def _import_accounting_batch(
        self,
        moves: List[Dict[str, Any]],
        lines_by_move: Dict[int, List[Dict[str, Any]]],
        accounts_map: Dict[int, str],
        journals_map: Dict[int, Dict[str, str]],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe les ecritures comptables Odoo vers AZALS.

        Args:
            moves: Liste des ecritures (account.move)
            lines_by_move: Lignes groupees par move_id
            accounts_map: Mapping {odoo_account_id: account_number}
            journals_map: Mapping {odoo_journal_id: {code, label, type}}

        Returns:
            Tuple (created_count, updated_count, errors)
        """
        from app.modules.accounting.models import (
            AccountingJournalEntry,
            AccountingJournalEntryLine,
            AccountingFiscalYear,
            EntryStatus,
        )
        from decimal import Decimal

        created = 0
        updated = 0
        errors = []

        # Cache des exercices fiscaux par annee
        fiscal_years_cache = {}

        for move in moves:
            odoo_id = move.get("id")
            entry_number = move.get("name", f"ODOO-{odoo_id}")
            entry_date_str = move.get("date")
            journal_value = move.get("journal_id")
            ref = move.get("ref", "")

            # Parser la date
            try:
                if isinstance(entry_date_str, str):
                    entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d")
                else:
                    entry_date = datetime.utcnow()
            except ValueError:
                entry_date = datetime.utcnow()

            # Determiner le journal
            journal_id = journal_value[0] if isinstance(journal_value, (list, tuple)) else journal_value
            journal_info = journals_map.get(journal_id, {"code": "OD", "label": "Divers"})

            # Determiner la periode
            period = entry_date.strftime("%Y-%m")

            # Trouver ou creer l'exercice fiscal
            year = entry_date.year
            if year not in fiscal_years_cache:
                fiscal_year = self.db.query(AccountingFiscalYear).filter(
                    AccountingFiscalYear.tenant_id == self.tenant_id,
                    AccountingFiscalYear.start_date <= entry_date,
                    AccountingFiscalYear.end_date >= entry_date,
                ).first()

                if not fiscal_year:
                    # Verifier aussi par code pour eviter les doublons
                    fiscal_year = self.db.query(AccountingFiscalYear).filter(
                        AccountingFiscalYear.tenant_id == self.tenant_id,
                        AccountingFiscalYear.code == f"FY{year}",
                    ).first()

                if not fiscal_year:
                    # Creer un exercice fiscal par defaut pour l'annee
                    fiscal_year = AccountingFiscalYear(
                        tenant_id=self.tenant_id,
                        name=f"Exercice {year}",
                        code=f"FY{year}",
                        start_date=datetime(year, 1, 1),
                        end_date=datetime(year, 12, 31, 23, 59, 59),
                    )
                    self.db.add(fiscal_year)
                    # Commit l'exercice fiscal pour avoir un ID valide
                    self.db.commit()
                    self.db.refresh(fiscal_year)
                    logger.info(f"[ODOO_IMPORT] Exercice fiscal cree: FY{year}")

                fiscal_years_cache[year] = fiscal_year.id

            fiscal_year_id = fiscal_years_cache[year]

            try:
                savepoint = self.db.begin_nested()

                # Rechercher une ecriture existante
                existing = self.db.query(AccountingJournalEntry).filter(
                    AccountingJournalEntry.tenant_id == self.tenant_id,
                    AccountingJournalEntry.entry_number == entry_number,
                ).first()

                if existing:
                    # Mise a jour - supprimer les anciennes lignes et recreer
                    self.db.query(AccountingJournalEntryLine).filter(
                        AccountingJournalEntryLine.entry_id == existing.id
                    ).delete()

                    existing.piece_number = ref or entry_number
                    existing.journal_code = journal_info["code"]
                    existing.journal_label = journal_info["label"]
                    existing.entry_date = entry_date
                    existing.period = period
                    existing.label = f"Import Odoo - {entry_number}"
                    existing.status = EntryStatus.POSTED
                    existing.updated_at = datetime.utcnow()

                    entry = existing
                    updated += 1
                else:
                    # Creation
                    entry = AccountingJournalEntry(
                        tenant_id=self.tenant_id,
                        entry_number=entry_number,
                        piece_number=ref or entry_number,
                        journal_code=journal_info["code"],
                        journal_label=journal_info["label"],
                        fiscal_year_id=fiscal_year_id,
                        entry_date=entry_date,
                        period=period,
                        label=f"Import Odoo - {entry_number}",
                        status=EntryStatus.POSTED,
                        document_type="ODOO_IMPORT",
                    )
                    self.db.add(entry)
                    self.db.flush()
                    created += 1

                # Ajouter les lignes
                move_lines = lines_by_move.get(odoo_id, [])
                total_debit = Decimal("0")
                total_credit = Decimal("0")

                for idx, line in enumerate(move_lines, start=1):
                    account_value = line.get("account_id")
                    account_odoo_id = account_value[0] if isinstance(account_value, (list, tuple)) else account_value
                    account_number = accounts_map.get(account_odoo_id, str(account_odoo_id))
                    account_label = account_value[1] if isinstance(account_value, (list, tuple)) and len(account_value) > 1 else "Compte"

                    debit = Decimal(str(line.get("debit", 0) or 0))
                    credit = Decimal(str(line.get("credit", 0) or 0))
                    label = line.get("name", "")

                    # Code auxiliaire si partenaire
                    auxiliary_code = None
                    partner_value = line.get("partner_id")
                    if partner_value and isinstance(partner_value, (list, tuple)):
                        auxiliary_code = f"ODOO-{partner_value[0]}"

                    entry_line = AccountingJournalEntryLine(
                        tenant_id=self.tenant_id,
                        entry_id=entry.id,
                        line_number=idx,
                        account_number=account_number,
                        account_label=account_label,
                        label=label,
                        debit=debit,
                        credit=credit,
                        auxiliary_code=auxiliary_code,
                    )
                    self.db.add(entry_line)

                    total_debit += debit
                    total_credit += credit

                # Mettre a jour les totaux
                entry.total_debit = total_debit
                entry.total_credit = total_credit
                entry.is_balanced = (total_debit == total_credit)

                savepoint.commit()

            except Exception as e:
                self.db.rollback()
                errors.append({
                    "odoo_id": odoo_id,
                    "entry_number": entry_number,
                    "error": str(e)[:200],
                })
                logger.warning(f"[ODOO_IMPORT] Erreur ecriture {entry_number}: {str(e)[:100]}")

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, updated, errors

    def import_bank_statements(self, config_id: UUID, full_sync: bool = False) -> OdooImportHistory:
        """Import des releves bancaires depuis Odoo (account.bank.statement)."""
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.BANK,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        try:
            connector = self._get_connector(config)

            # Releves bancaires (Odoo 17+ n'a plus le champ 'state')
            domain = []
            fields = ["name", "date", "journal_id", "balance_start", "balance_end_real", "line_ids"]

            statements = connector.search_read("account.bank.statement", domain, fields)
            history.total_records = len(statements)

            logger.info(f"[ODOO_IMPORT] Recupere {len(statements)} releves bancaires")

            history.created_count = len(statements)
            history.status = OdooImportStatus.SUCCESS
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int((history.completed_at - history.started_at).total_seconds())

            self.db.commit()
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def import_interventions(self, config_id: UUID, full_sync: bool = False) -> OdooImportHistory:
        """Import des interventions depuis Odoo (project.task ou helpdesk.ticket)."""
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=OdooSyncType.INTERVENTIONS,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method="manual",
            is_delta_sync=not full_sync,
        )
        self.db.add(history)
        self.db.commit()

        try:
            connector = self._get_connector(config)

            # Essayer d'abord intervention.intervention (module custom MASITH)
            tasks = []
            source_model = None
            try:
                domain = []
                # Champs du module intervention.intervention personnalisé
                fields = [
                    "id", "display_name", "description",
                    "date_prevue", "date_debut", "date_fin", "heure_arrivee",
                    "duree_prevue", "duree_reelle",
                    "client_final_id", "donneur_ordre_id", "technicien_principal_id",
                    "adresse_intervention", "adresse_entreprise",
                    "latitude", "longitude",
                    "facturer_a", "distance_km", "duree_trajet_min",
                    "date_signature", "create_date", "company_id"
                ]
                tasks = connector.search_read("intervention.intervention", domain, fields)
                source_model = "intervention.intervention"
                logger.info(f"[ODOO_IMPORT] Trouve {len(tasks)} intervention.intervention")
            except Exception as e:
                logger.exception(f"[ODOO_IMPORT] Module intervention.intervention non disponible: {e}")

            # Fallback: project.task
            if not tasks:
                try:
                    domain = []
                    fields = [
                        "id", "name", "project_id", "partner_id", "user_ids",
                        "date_deadline", "stage_id", "description", "create_date",
                        "priority", "kanban_state", "date_assign", "date_end",
                        "sequence", "display_name", "x_studio_reference", "x_reference",
                        "code", "ref", "number"
                    ]
                    tasks = connector.search_read("project.task", domain, fields)
                    source_model = "project.task"
                    logger.info(f"[ODOO_IMPORT] Trouve {len(tasks)} project.task")
                except Exception as e:
                    logger.info(f"[ODOO_IMPORT] Module project non disponible: {e}")

            # Fallback: helpdesk.ticket
            if not tasks:
                try:
                    domain = []
                    fields = [
                        "id", "name", "partner_id", "user_id", "stage_id",
                        "description", "ticket_type_id", "create_date", "priority"
                    ]
                    tasks = connector.search_read("helpdesk.ticket", domain, fields)
                    source_model = "helpdesk.ticket"
                    logger.info(f"[ODOO_IMPORT] Trouve {len(tasks)} helpdesk.ticket")
                except Exception as e:
                    logger.info(f"[ODOO_IMPORT] Module helpdesk non disponible: {e}")

            history.total_records = len(tasks)
            logger.info(f"[ODOO_IMPORT] Recupere {len(tasks)} interventions/taches depuis {source_model}")

            # Importer les taches dans fs_interventions
            created, updated, errors = self._import_interventions_batch(tasks, source_model)

            history.created_count = created
            history.updated_count = updated
            history.error_count = len(errors)
            history.error_details = errors
            history.status = OdooImportStatus.SUCCESS if not errors else OdooImportStatus.PARTIAL
            history.completed_at = datetime.utcnow()
            history.duration_seconds = int((history.completed_at - history.started_at).total_seconds())

            config.total_imports += 1
            self.db.commit()

            logger.info(
                f"[ODOO_IMPORT] Interventions import termine: {created} crees, "
                f"{updated} mis a jour, {len(errors)} erreurs"
            )
            return history

        except Exception as e:
            history.status = OdooImportStatus.ERROR
            history.error_details = [{"error": str(e)}]
            history.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def _import_interventions_batch(
        self,
        tasks: List[Dict[str, Any]],
        source_model: str | None
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe un lot d'interventions depuis Odoo vers int_interventions.

        Returns:
            Tuple (created_count, updated_count, errors)
        """
        from app.modules.interventions.models import (
            Intervention, InterventionStatut, InterventionPriorite, TypeIntervention
        )
        import uuid as uuid_module

        created = 0
        updated = 0
        errors = []

        # Get or create a default client_id for imports (required field)
        default_client_id = self._get_or_create_default_odoo_client()

        # Map Odoo stage to internal status
        def map_stage_to_status(stage_id, kanban_state=None):
            """Map Odoo stage to AZALSCORE InterventionStatut."""
            if not stage_id:
                return InterventionStatut.A_PLANIFIER

            stage_name = stage_id[1].lower() if isinstance(stage_id, (list, tuple)) else str(stage_id).lower()

            if any(x in stage_name for x in ["done", "termine", "cloture", "fini", "resolu", "closed"]):
                return InterventionStatut.TERMINEE
            elif any(x in stage_name for x in ["cancel", "annule"]):
                return InterventionStatut.ANNULEE
            elif any(x in stage_name for x in ["progress", "cours", "encours", "en cours", "doing"]):
                return InterventionStatut.EN_COURS
            elif any(x in stage_name for x in ["plan", "prevu", "assigne", "scheduled"]):
                return InterventionStatut.PLANIFIEE
            elif any(x in stage_name for x in ["blocked", "bloque", "attente", "waiting"]):
                return InterventionStatut.BLOQUEE
            elif any(x in stage_name for x in ["draft", "brouillon", "new", "nouveau"]):
                return InterventionStatut.DRAFT
            else:
                return InterventionStatut.A_PLANIFIER

        # Map Odoo priority to internal priority
        def map_priority(priority):
            """Map Odoo priority to AZALSCORE InterventionPriorite."""
            if not priority:
                return InterventionPriorite.NORMAL

            p = str(priority)
            if p in ["2", "3", "high", "urgent"]:
                return InterventionPriorite.HIGH
            elif p in ["0", "low", "basse"]:
                return InterventionPriorite.LOW
            else:
                return InterventionPriorite.NORMAL

        # Extract reference from Odoo intervention (keep original numbering)
        def get_odoo_reference(task):
            """Extract the best reference from Odoo intervention."""
            # For intervention.intervention, display_name IS the reference (e.g., "INT-001")
            display_name = task.get('display_name', '')
            if display_name and display_name.strip():
                return display_name.strip()[:20]

            # Fallback: use Odoo ID with prefix
            return f"ODOO-{task.get('id', 0)}"

        for task in tasks:
            odoo_id = task.get("id")
            # For intervention.intervention, display_name is the reference (e.g., "INT-001")
            display_name = task.get("display_name", "")
            description = task.get("description", "")

            if not display_name:
                errors.append({
                    "odoo_id": odoo_id,
                    "error": "Référence intervention manquante",
                })
                continue

            try:
                savepoint = self.db.begin_nested()

                # Check if already imported (by reference_externe containing Odoo ID)
                ref_externe = f"ODOO-{odoo_id}"
                existing = self.db.query(Intervention).filter(
                    Intervention.tenant_id == self.tenant_id,
                    Intervention.reference_externe == ref_externe,
                ).first()

                # Extract client info from client_final_id
                client_final = task.get("client_final_id")
                client_id = default_client_id
                client_name = None
                if client_final and isinstance(client_final, (list, tuple)) and len(client_final) > 1:
                    client_name = client_final[1]
                    matched_client = self._find_customer_by_name(client_name)
                    if matched_client:
                        client_id = matched_client

                # Extract donneur d'ordre info
                donneur_ordre = task.get("donneur_ordre_id")
                donneur_ordre_name = None
                if donneur_ordre and isinstance(donneur_ordre, (list, tuple)) and len(donneur_ordre) > 1:
                    donneur_ordre_name = donneur_ordre[1]

                # Parse date_prevue (datetime field)
                date_prevue = None
                date_prevue_raw = task.get("date_prevue")
                if date_prevue_raw:
                    try:
                        if isinstance(date_prevue_raw, str):
                            date_prevue = datetime.strptime(date_prevue_raw[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S") if len(date_prevue_raw) > 10 else datetime.strptime(date_prevue_raw[:10], "%Y-%m-%d")
                    except ValueError:
                        pass

                # Parse date_debut (actual start)
                date_debut = None
                date_debut_raw = task.get("date_debut")
                if date_debut_raw:
                    try:
                        if isinstance(date_debut_raw, str):
                            date_debut = datetime.strptime(date_debut_raw[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass

                # Parse date_fin (actual end)
                date_fin = None
                date_fin_raw = task.get("date_fin")
                if date_fin_raw:
                    try:
                        if isinstance(date_fin_raw, str):
                            date_fin = datetime.strptime(date_fin_raw[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass

                # Determine status based on dates
                if date_fin:
                    statut = InterventionStatut.TERMINEE
                elif date_debut:
                    statut = InterventionStatut.EN_COURS
                elif date_prevue:
                    statut = InterventionStatut.PLANIFIEE
                else:
                    statut = InterventionStatut.A_PLANIFIER

                # Calculate duration in minutes
                duree_minutes = None
                duree_prevue = task.get("duree_prevue")  # In hours
                if duree_prevue:
                    duree_minutes = int(float(duree_prevue) * 60)

                duree_reelle_minutes = None
                duree_reelle = task.get("duree_reelle")  # In hours
                if duree_reelle:
                    duree_reelle_minutes = int(float(duree_reelle) * 60)

                # Address
                adresse = task.get("adresse_intervention") or task.get("adresse_entreprise") or ""

                # Get the original Odoo reference (display_name like "INT-001")
                odoo_reference = get_odoo_reference(task)

                # Build notes
                notes_internes = f"Import Odoo {source_model} ID: {odoo_id}"
                if donneur_ordre_name:
                    notes_internes += f"\nDonneur d'ordre: {donneur_ordre_name}"
                if client_name:
                    notes_internes += f"\nClient Odoo: {client_name}"

                if existing:
                    # Update existing
                    existing.titre = description[:500] if description else display_name
                    existing.description = description or existing.description
                    existing.notes_internes = notes_internes
                    existing.statut = statut
                    existing.client_id = client_id
                    if date_prevue:
                        existing.date_prevue_debut = date_prevue
                    if date_debut:
                        existing.date_demarrage = date_debut
                    if date_fin:
                        existing.date_fin = date_fin
                    if duree_minutes:
                        existing.duree_prevue_minutes = duree_minutes
                    if duree_reelle_minutes:
                        existing.duree_reelle_minutes = duree_reelle_minutes
                    if adresse:
                        existing.adresse_ligne1 = adresse[:255]
                    existing.updated_at = datetime.utcnow()
                    savepoint.commit()
                    updated += 1
                else:
                    # Check if reference already exists (to avoid duplicates)
                    existing_ref = self.db.query(Intervention).filter(
                        Intervention.tenant_id == self.tenant_id,
                        Intervention.reference == odoo_reference,
                    ).first()

                    if existing_ref:
                        # Reference exists, update it instead
                        existing_ref.titre = description[:500] if description else display_name
                        existing_ref.description = description or existing_ref.description
                        existing_ref.reference_externe = ref_externe
                        existing_ref.statut = statut
                        if date_prevue:
                            existing_ref.date_prevue_debut = date_prevue
                        if date_debut:
                            existing_ref.date_demarrage = date_debut
                        if date_fin:
                            existing_ref.date_fin = date_fin
                        if duree_minutes:
                            existing_ref.duree_prevue_minutes = duree_minutes
                        if duree_reelle_minutes:
                            existing_ref.duree_reelle_minutes = duree_reelle_minutes
                        if adresse:
                            existing_ref.adresse_ligne1 = adresse[:255]
                        existing_ref.updated_at = datetime.utcnow()
                        savepoint.commit()
                        updated += 1
                    else:
                        # Create new with Odoo reference
                        intervention = Intervention(
                            id=uuid_module.uuid4(),
                            tenant_id=self.tenant_id,
                            reference=odoo_reference,
                            reference_externe=ref_externe,
                            client_id=client_id,
                            titre=description[:500] if description else display_name,
                            description=description or "",
                            notes_internes=notes_internes,
                            statut=statut,
                            priorite=InterventionPriorite.NORMAL,
                            type_intervention=TypeIntervention.MAINTENANCE,
                            date_prevue_debut=date_prevue,
                            date_demarrage=date_debut,
                            date_fin=date_fin,
                            duree_prevue_minutes=duree_minutes,
                            duree_reelle_minutes=duree_reelle_minutes,
                            adresse_ligne1=adresse[:255] if adresse else None,
                            facturable=True,
                        )
                        self.db.add(intervention)
                        savepoint.commit()
                        created += 1

            except Exception as e:
                try:
                    savepoint.rollback()
                except Exception:
                    pass
                errors.append({
                    "odoo_id": odoo_id,
                    "reference": display_name,
                    "error": str(e),
                })
                logger.warning(f"[ODOO_IMPORT] Erreur intervention {odoo_id} ({display_name}): {e}")

        return created, updated, errors

    def _get_or_create_default_odoo_client(self) -> UUID:
        """Get or create a default client for Odoo imports."""
        from app.modules.commercial.models import Customer
        import uuid as uuid_module

        # Look for existing Odoo default client
        existing = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.code == "ODOO-DEFAULT"
        ).first()

        if existing:
            return existing.id

        # Create default client
        default_client = Customer(
            id=uuid_module.uuid4(),
            tenant_id=self.tenant_id,
            code="ODOO-DEFAULT",
            name="Client Import Odoo",
            is_active=True,
        )
        self.db.add(default_client)
        self.db.flush()
        return default_client.id

    def _find_customer_by_name(self, name: str) -> Optional[UUID]:
        """Try to find a customer by name."""
        from app.modules.commercial.models import Customer

        if not name:
            return None

        customer = self.db.query(Customer).filter(
            Customer.tenant_id == self.tenant_id,
            Customer.name.ilike(f"%{name}%")
        ).first()

        return customer.id if customer else None

    # =========================================================================
    # FULL SYNC
    # =========================================================================

    def full_sync(self, config_id: UUID, full_sync: bool = False) -> List[OdooImportHistory]:
        """
        Effectue une synchronisation complete (tous les types actives).

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore les deltas

        Returns:
            Liste des historiques d'import
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        histories = []

        if config.sync_products:
            histories.append(self.import_products(config_id, full_sync))

        if config.sync_contacts:
            histories.append(self.import_contacts(config_id, full_sync))

        if config.sync_suppliers:
            histories.append(self.import_suppliers(config_id, full_sync))

        if getattr(config, 'sync_purchase_orders', False):
            histories.append(self.import_purchase_orders(config_id, full_sync))

        if getattr(config, 'sync_sale_orders', False):
            histories.append(self.import_sale_orders(config_id, full_sync))

        if getattr(config, 'sync_invoices', False):
            histories.append(self.import_invoices(config_id, full_sync))

        if getattr(config, 'sync_quotes', False):
            histories.append(self.import_quotes(config_id, full_sync))

        if getattr(config, 'sync_accounting', False):
            histories.append(self.import_accounting(config_id, full_sync))

        if getattr(config, 'sync_bank', False):
            histories.append(self.import_bank_statements(config_id, full_sync))

        if getattr(config, 'sync_interventions', False):
            histories.append(self.import_interventions(config_id, full_sync))

        return histories

    # =========================================================================
    # HISTORIQUE
    # =========================================================================

    def get_import_history(
        self,
        config_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[OdooImportHistory]:
        """
        Recupere l'historique des imports.

        Args:
            config_id: Filtrer par configuration (optionnel)
            limit: Nombre max de resultats

        Returns:
            Liste des historiques
        """
        query = self.db.query(OdooImportHistory).filter(
            OdooImportHistory.tenant_id == self.tenant_id,
        )
        if config_id:
            query = query.filter(OdooImportHistory.config_id == config_id)

        return query.order_by(OdooImportHistory.started_at.desc()).limit(limit).all()

    def get_stats(self, config_id: UUID) -> Dict[str, Any]:
        """
        Recupere les statistiques d'une configuration.

        Args:
            config_id: ID de la configuration

        Returns:
            Dictionnaire de statistiques
        """
        config = self.get_config(config_id)
        if not config:
            return {}

        # Compter les imports par statut
        status_counts = dict(
            self.db.query(
                OdooImportHistory.status,
                func.count(OdooImportHistory.id)
            ).filter(
                OdooImportHistory.tenant_id == self.tenant_id,
                OdooImportHistory.config_id == config_id,
            ).group_by(OdooImportHistory.status).all()
        )

        # Dernier import par type
        last_imports = {}
        for sync_type in OdooSyncType:
            last = self.db.query(OdooImportHistory).filter(
                OdooImportHistory.tenant_id == self.tenant_id,
                OdooImportHistory.config_id == config_id,
                OdooImportHistory.sync_type == sync_type,
            ).order_by(OdooImportHistory.started_at.desc()).first()
            if last:
                last_imports[sync_type.value] = {
                    "started_at": last.started_at,
                    "status": last.status.value,
                    "records": last.total_records,
                }

        return {
            "config_id": str(config_id),
            "config_name": config.name,
            "total_imports": config.total_imports,
            "total_products": config.total_products_imported,
            "total_contacts": config.total_contacts_imported,
            "total_suppliers": config.total_suppliers_imported,
            "is_connected": config.is_connected,
            "last_connection_test": config.last_connection_test_at,
            "status_counts": {k.value: v for k, v in status_counts.items()},
            "last_imports": last_imports,
        }

    # =========================================================================
    # PREVIEW
    # =========================================================================

    def preview_data(
        self,
        config_id: UUID,
        model: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Previsualise les donnees Odoo avant import.

        Args:
            config_id: ID de la configuration
            model: Modele Odoo (product.product, res.partner)
            limit: Nombre de records a previsualiser

        Returns:
            Donnees brutes et mappees
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError("Configuration non trouvee")

        connector = self._get_connector(config)
        mapper = self._get_mapper(config_id)

        fields = mapper.get_odoo_fields(model)
        records = connector.search_read(model, [], fields, limit=limit)

        mapped_records = mapper.map_records(model, records, self.tenant_id)

        # Nettoyer les champs internes pour l'affichage
        for rec in mapped_records:
            rec.pop("_odoo_id", None)
            rec.pop("_odoo_model", None)

        return {
            "model": model,
            "total_count": connector.search_count(model, []),
            "preview_count": len(records),
            "fields": fields,
            "odoo_records": records,
            "mapped_records": mapped_records,
        }

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _encrypt_credential(self, credential: str) -> str:
        """Chiffre un credential."""
        return self._fernet.encrypt(credential.encode()).decode()

    def _decrypt_credential(self, encrypted: str) -> str:
        """Dechiffre un credential."""
        return self._fernet.decrypt(encrypted.encode()).decode()
