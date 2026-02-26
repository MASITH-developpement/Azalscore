"""
AZALS MODULE - Odoo Import Config Service
==========================================

Service de gestion des configurations de connexion Odoo.
"""
from __future__ import annotations


import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.modules.odoo_import.models import OdooAuthMethod, OdooConnectionConfig

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class ConfigService(BaseOdooService[OdooConnectionConfig]):
    """Service de gestion des configurations de connexion Odoo."""

    model = OdooConnectionConfig

    def create(
        self,
        name: str,
        odoo_url: str,
        odoo_database: str,
        username: str,
        credential: str,
        auth_method: str = "api_key",
        **options,
    ) -> OdooConnectionConfig:
        """
        Crée une nouvelle configuration de connexion.

        Args:
            name: Nom de la connexion
            odoo_url: URL du serveur Odoo
            odoo_database: Nom de la base de données Odoo
            username: Nom d'utilisateur Odoo
            credential: Mot de passe ou API key
            auth_method: Méthode d'authentification ('password' ou 'api_key')
            **options: Options supplémentaires (sync_products, sync_contacts, etc.)

        Returns:
            Configuration créée

        Raises:
            ValueError: Si une configuration avec ce nom existe déjà
        """
        # Vérifier unicité du nom
        existing = (
            self.db.query(OdooConnectionConfig)
            .filter(
                OdooConnectionConfig.tenant_id == self.tenant_id,
                OdooConnectionConfig.name == name,
            )
            .first()
        )
        if existing:
            raise ValueError(f"Une configuration nommée '{name}' existe déjà")

        # Chiffrer le credential
        encrypted_credential = self._encrypt_credential(credential)

        config = OdooConnectionConfig(
            tenant_id=self.tenant_id,
            name=name,
            odoo_url=odoo_url.rstrip("/"),
            odoo_database=odoo_database,
            username=username,
            encrypted_credential=encrypted_credential,
            auth_method=OdooAuthMethod(auth_method),
            created_by=UUID(self.user_id) if self.user_id else None,
            **options,
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        logger.info(
            "Configuration Odoo créée | tenant=%s name=%s url=%s",
            self.tenant_id,
            name,
            odoo_url,
        )
        return config

    def update(
        self,
        config_id: UUID,
        **updates,
    ) -> Optional[OdooConnectionConfig]:
        """
        Met à jour une configuration existante.

        Args:
            config_id: ID de la configuration
            **updates: Champs à mettre à jour

        Returns:
            Configuration mise à jour ou None si non trouvée
        """
        config = self.get_config(config_id)
        if not config:
            return None

        # Chiffrer le nouveau credential si fourni
        if "credential" in updates:
            updates["encrypted_credential"] = self._encrypt_credential(
                updates.pop("credential")
            )

        # Convertir auth_method si fourni
        if "auth_method" in updates:
            updates["auth_method"] = OdooAuthMethod(updates["auth_method"])

        # Nettoyer l'URL si fournie
        if "odoo_url" in updates:
            updates["odoo_url"] = updates["odoo_url"].rstrip("/")

        # Appliquer les mises à jour
        for key, value in updates.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        config.updated_by = UUID(self.user_id) if self.user_id else None
        config.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(config)

        logger.info(
            "Configuration Odoo mise à jour | tenant=%s config_id=%s",
            self.tenant_id,
            config_id,
        )
        return config

    def delete(self, config_id: UUID) -> bool:
        """
        Supprime une configuration.

        Args:
            config_id: ID de la configuration

        Returns:
            True si supprimée, False si non trouvée
        """
        config = self.get_config(config_id)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()

        logger.info(
            "Configuration Odoo supprimée | tenant=%s config_id=%s",
            self.tenant_id,
            config_id,
        )
        return True

    def list(self, active_only: bool = False) -> List[OdooConnectionConfig]:
        """
        Liste les configurations du tenant.

        Args:
            active_only: Si True, retourne uniquement les configurations actives

        Returns:
            Liste des configurations
        """
        query = self.db.query(OdooConnectionConfig).filter(
            OdooConnectionConfig.tenant_id == self.tenant_id,
        )

        if active_only:
            query = query.filter(OdooConnectionConfig.is_active == True)

        return query.order_by(OdooConnectionConfig.name).all()

    def activate(self, config_id: UUID) -> Optional[OdooConnectionConfig]:
        """
        Active une configuration.

        Args:
            config_id: ID de la configuration

        Returns:
            Configuration activée ou None
        """
        config = self.get_config(config_id)
        if not config:
            return None

        config.is_active = True
        config.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(
            "Configuration Odoo activée | tenant=%s config_id=%s",
            self.tenant_id,
            config_id,
        )
        return config

    def deactivate(self, config_id: UUID) -> Optional[OdooConnectionConfig]:
        """
        Désactive une configuration.

        Args:
            config_id: ID de la configuration

        Returns:
            Configuration désactivée ou None
        """
        config = self.get_config(config_id)
        if not config:
            return None

        config.is_active = False
        config.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(
            "Configuration Odoo désactivée | tenant=%s config_id=%s",
            self.tenant_id,
            config_id,
        )
        return config
