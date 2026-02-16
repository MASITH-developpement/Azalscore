"""
AZALS MODULE - Odoo Import Contacts Service
=============================================

Service d'import des contacts et fournisseurs depuis Odoo.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import UUID

from app.modules.odoo_import.models import OdooImportHistory, OdooSyncType

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class ContactImportService(BaseOdooService[OdooImportHistory]):
    """Service d'import des contacts et fournisseurs Odoo."""

    model = OdooImportHistory

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
        config = self._require_config(config_id)

        sync_type = OdooSyncType.CONTACTS
        if include_suppliers:
            sync_type = OdooSyncType.FULL

        history = self._create_history(
            config_id=config_id,
            sync_type=sync_type,
            is_delta=not full_sync,
        )

        try:
            connector = self._get_connector(config)
            mapper = self._get_mapper(config_id)

            # Déterminer la date de delta
            delta_date = None
            if not full_sync and config.contacts_last_sync_at:
                delta_date = config.contacts_last_sync_at
                history.delta_from_date = delta_date

            # Construire le domaine de recherche
            domain = [("is_company", "=", True)]  # Uniquement les sociétés
            if not include_suppliers:
                domain.append(("customer_rank", ">", 0))

            fields = mapper.get_odoo_fields("res.partner")

            if delta_date:
                domain.extend([
                    "|",
                    ("write_date", ">=", delta_date.strftime("%Y-%m-%d %H:%M:%S")),
                    ("create_date", ">=", delta_date.strftime("%Y-%m-%d %H:%M:%S")),
                ])

            odoo_contacts = connector.search_read("res.partner", domain, fields)
            history.total_records = len(odoo_contacts)

            # Mapper et importer
            mapped_contacts = mapper.map_records(
                "res.partner",
                odoo_contacts,
                self.tenant_id,
            )
            created, updated, errors = self._import_contacts_batch(mapped_contacts)

            # Mettre à jour la configuration
            config.contacts_last_sync_at = datetime.utcnow()
            config.total_contacts_imported += created + updated
            config.total_imports += 1

            history = self._finalize_history(history, created, updated, errors)

            logger.info(
                "Import contacts terminé | tenant=%s created=%d updated=%d errors=%d",
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
        config = self._require_config(config_id)

        history = self._create_history(
            config_id=config_id,
            sync_type=OdooSyncType.SUPPLIERS,
            is_delta=not full_sync,
        )

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
                    ("write_date", ">=", delta_date.strftime("%Y-%m-%d %H:%M:%S")),
                    ("create_date", ">=", delta_date.strftime("%Y-%m-%d %H:%M:%S")),
                ])

            odoo_suppliers = connector.search_read("res.partner", domain, fields)
            history.total_records = len(odoo_suppliers)

            # Utilise le même processus que contacts
            mapped_suppliers = mapper.map_records(
                "res.partner",
                odoo_suppliers,
                self.tenant_id,
            )
            created, updated, errors = self._import_contacts_batch(mapped_suppliers)

            # Mettre à jour la configuration
            config.suppliers_last_sync_at = datetime.utcnow()
            config.total_suppliers_imported += created + updated
            config.total_imports += 1

            history = self._finalize_history(history, created, updated, errors)

            logger.info(
                "Import fournisseurs terminé | tenant=%s created=%d updated=%d errors=%d",
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

    def _import_contacts_batch(
        self,
        mapped_contacts: List[Dict[str, Any]],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Importe un lot de contacts mappés.

        Crée également un Customer dans le module commercial pour
        le matching des documents.

        Args:
            mapped_contacts: Liste des contacts mappés

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
                savepoint = self.db.begin_nested()

                # Rechercher un contact existant par email ou tax_id
                existing = self._find_existing_contact(email, tax_id)

                if existing:
                    # Mise à jour
                    for key, value in mapped.items():
                        if key not in ("tenant_id", "id") and hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    savepoint.commit()
                    updated += 1
                    logger.debug("Contact mis à jour: %s", name)
                else:
                    # Création
                    contact = UnifiedContact(**mapped)
                    self.db.add(contact)

                    # Créer aussi un Customer pour le matching des documents
                    self._create_customer_if_needed(odoo_id, name, email, tax_id)

                    savepoint.commit()
                    created += 1
                    logger.debug("Contact créé: %s", name)

            except Exception as e:
                self.db.rollback()
                errors.append({
                    "odoo_id": odoo_id,
                    "email": email,
                    "name": name,
                    "error": str(e)[:200],
                })
                logger.warning("Erreur contact %s: %s", name, str(e)[:100])

        # Commit final
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        return created, updated, errors

    def _find_existing_contact(
        self,
        email: str | None,
        tax_id: str | None,
    ):
        """
        Recherche un contact existant par email ou tax_id.

        Args:
            email: Email du contact
            tax_id: Numéro fiscal (SIRET, TVA, etc.)

        Returns:
            Contact existant ou None
        """
        from app.modules.contacts.models import UnifiedContact

        existing = None

        if email:
            existing = (
                self.db.query(UnifiedContact)
                .filter(
                    UnifiedContact.tenant_id == self.tenant_id,
                    UnifiedContact.email == email,
                )
                .first()
            )

        if not existing and tax_id:
            existing = (
                self.db.query(UnifiedContact)
                .filter(
                    UnifiedContact.tenant_id == self.tenant_id,
                    UnifiedContact.tax_id == tax_id,
                )
                .first()
            )

        return existing

    def _create_customer_if_needed(
        self,
        odoo_id: int | None,
        name: str,
        email: str | None,
        tax_id: str | None,
    ) -> None:
        """
        Crée un Customer si nécessaire pour le matching des documents.

        Args:
            odoo_id: ID Odoo du partenaire
            name: Nom du client
            email: Email du client
            tax_id: Numéro fiscal
        """
        from app.modules.commercial.models import Customer, CustomerType

        odoo_code = f"ODOO-{odoo_id}" if odoo_id else f"ODOO-{name[:20]}"

        existing_customer = (
            self.db.query(Customer)
            .filter(
                Customer.tenant_id == self.tenant_id,
                Customer.code == odoo_code,
            )
            .first()
        )

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
            logger.debug("Customer créé: %s (%s)", name, odoo_code)
