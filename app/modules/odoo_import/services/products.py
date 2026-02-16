"""
AZALS MODULE - Odoo Import Products Service
=============================================

Service d'import des produits depuis Odoo.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import UUID

from app.modules.odoo_import.models import OdooImportHistory, OdooSyncType

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class ProductImportService(BaseOdooService[OdooImportHistory]):
    """Service d'import des produits Odoo."""

    model = OdooImportHistory

    def import_products(
        self,
        config_id: UUID,
        full_sync: bool = False,
    ) -> OdooImportHistory:
        """
        Importe les produits depuis Odoo.

        Supporte l'import delta (incrémental) basé sur write_date.

        Args:
            config_id: ID de la configuration
            full_sync: Si True, ignore le delta et importe tout

        Returns:
            Historique de l'import avec statistiques

        Raises:
            ValueError: Si configuration non trouvée
        """
        config = self._require_config(config_id)

        # Créer l'historique
        history = self._create_history(
            config_id=config_id,
            sync_type=OdooSyncType.PRODUCTS,
            is_delta=not full_sync,
        )

        try:
            connector = self._get_connector(config)
            mapper = self._get_mapper(config_id)

            # Déterminer la date de delta
            delta_date = None
            if not full_sync and config.products_last_sync_at:
                delta_date = config.products_last_sync_at
                history.delta_from_date = delta_date

            # Récupérer les produits Odoo
            fields = mapper.get_odoo_fields("product.product")

            if delta_date:
                odoo_products = connector.get_modified_since(
                    "product.product",
                    delta_date,
                    fields,
                )
            else:
                odoo_products = connector.search_read(
                    "product.product",
                    [("active", "in", [True, False])],  # Inclure produits inactifs
                    fields,
                )

            history.total_records = len(odoo_products)

            # Mapper et importer
            mapped_products = mapper.map_records(
                "product.product",
                odoo_products,
                self.tenant_id,
            )
            created, updated, errors = self._import_batch(mapped_products)

            # Mettre à jour la configuration
            config.products_last_sync_at = datetime.utcnow()
            config.total_products_imported += created + updated
            config.total_imports += 1

            # Finaliser l'historique
            history = self._finalize_history(history, created, updated, errors)

            logger.info(
                "Import produits terminé | tenant=%s created=%d updated=%d errors=%d",
                self.tenant_id,
                created,
                updated,
                len(errors),
            )
            return history

        except Exception as e:
            self._fail_history(history, e)
            config.last_error_message = str(e)
            self.db.commit()
            raise

    def _import_batch(
        self,
        mapped_products: List[Dict[str, Any]],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe un lot de produits mappés.

        Utilise des savepoints pour pouvoir rollback chaque produit
        individuellement en cas d'erreur.

        Args:
            mapped_products: Liste des produits mappés

        Returns:
            Tuple (created_count, updated_count, errors)
        """
        from app.modules.inventory.models import Product

        created = 0
        updated = 0
        errors = []

        for mapped in mapped_products:
            # Extraire les métadonnées Odoo
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
                savepoint = self.db.begin_nested()

                # Rechercher un produit existant
                existing = (
                    self.db.query(Product)
                    .filter(
                        Product.tenant_id == self.tenant_id,
                        Product.code == code,
                    )
                    .first()
                )

                if existing:
                    # Mise à jour
                    for key, value in mapped.items():
                        if key not in ("tenant_id", "id") and hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    savepoint.commit()
                    updated += 1
                    logger.debug("Produit mis à jour: %s", code)
                else:
                    # Création
                    product = Product(**mapped)
                    self.db.add(product)
                    savepoint.commit()
                    created += 1
                    logger.debug("Produit créé: %s", code)

            except Exception as e:
                self.db.rollback()
                error_msg = str(e)

                # Gestion des conflits de duplication
                if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                    try:
                        existing = (
                            self.db.query(Product)
                            .filter(
                                Product.tenant_id == self.tenant_id,
                                Product.code == code,
                            )
                            .first()
                        )
                        if existing:
                            for key, value in mapped.items():
                                if key not in ("tenant_id", "id") and hasattr(existing, key):
                                    setattr(existing, key, value)
                            existing.updated_at = datetime.utcnow()
                            self.db.commit()
                            updated += 1
                            logger.debug(
                                "Produit mis à jour après conflit: %s",
                                code,
                            )
                            continue
                    except Exception as e2:
                        error_msg = str(e2)

                errors.append({
                    "odoo_id": odoo_id,
                    "code": code,
                    "error": error_msg[:200],
                })
                logger.warning(
                    "Erreur produit %s: %s",
                    code,
                    error_msg[:100],
                )

        # Commit final
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, updated, errors
