"""
AZALS MODULE - Odoo Import Connection Service
===============================================

Service de test de connexion Odoo.
"""

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from app.modules.odoo_import.connector import (
    OdooAuthenticationError,
    OdooConnectionError,
    OdooConnector,
)
from app.modules.odoo_import.models import OdooConnectionConfig

from .base import BaseOdooService

logger = logging.getLogger(__name__)


class ConnectionService(BaseOdooService[OdooConnectionConfig]):
    """Service de test de connexion Odoo."""

    model = OdooConnectionConfig

    def test(
        self,
        odoo_url: str,
        odoo_database: str,
        username: str,
        credential: str,
        auth_method: str = "api_key",
    ) -> Dict[str, Any]:
        """
        Teste une connexion Odoo avec les paramètres fournis.

        Args:
            odoo_url: URL du serveur Odoo
            odoo_database: Nom de la base de données
            username: Nom d'utilisateur
            credential: Mot de passe ou API key
            auth_method: Méthode d'authentification

        Returns:
            Dictionnaire avec résultat du test:
            - success: bool
            - message: str (message d'erreur si échec)
            - error_type: str (type d'erreur si échec)
            - odoo_version: str (version Odoo si succès)
            - uid: int (ID utilisateur si succès)
        """
        try:
            connector = OdooConnector(
                url=odoo_url,
                database=odoo_database,
                username=username,
                credential=credential,
                auth_method=auth_method,
            )
            result = connector.test_connection()

            logger.info(
                "Test connexion Odoo réussi | url=%s database=%s",
                odoo_url,
                odoo_database,
            )
            return result

        except OdooAuthenticationError as e:
            logger.warning(
                "Test connexion Odoo échec auth | url=%s error=%s",
                odoo_url,
                str(e),
            )
            return {
                "success": False,
                "message": str(e),
                "error_type": "authentication",
            }

        except OdooConnectionError as e:
            logger.warning(
                "Test connexion Odoo échec connexion | url=%s error=%s",
                odoo_url,
                str(e),
            )
            return {
                "success": False,
                "message": str(e),
                "error_type": "connection",
            }

        except Exception as e:
            logger.exception(
                "Test connexion Odoo erreur inattendue | url=%s",
                odoo_url,
            )
            return {
                "success": False,
                "message": f"Erreur inattendue: {str(e)}",
                "error_type": "unknown",
            }

    def test_config(self, config_id: UUID) -> Dict[str, Any]:
        """
        Teste la connexion d'une configuration existante.

        Met à jour les informations de connexion dans la configuration:
        - is_connected
        - last_connection_test_at
        - odoo_version
        - last_error_message

        Args:
            config_id: ID de la configuration à tester

        Returns:
            Dictionnaire avec résultat du test
        """
        config = self.get_config(config_id)
        if not config:
            return {
                "success": False,
                "message": "Configuration non trouvée",
                "error_type": "not_found",
            }

        # Déchiffrer le credential et tester
        credential = self._decrypt_credential(config.encrypted_credential)
        result = self.test(
            odoo_url=config.odoo_url,
            odoo_database=config.odoo_database,
            username=config.username,
            credential=credential,
            auth_method=config.auth_method.value,
        )

        # Mettre à jour la configuration avec le résultat
        config.is_connected = result.get("success", False)
        config.last_connection_test_at = datetime.utcnow()

        if result.get("odoo_version"):
            config.odoo_version = result["odoo_version"]

        if result["success"]:
            config.last_error_message = None
        else:
            config.last_error_message = result.get("message")

        self.db.commit()

        logger.info(
            "Test connexion config | tenant=%s config_id=%s success=%s",
            self.tenant_id,
            config_id,
            result["success"],
        )
        return result

    def get_available_databases(
        self,
        odoo_url: str,
    ) -> Dict[str, Any]:
        """
        Récupère la liste des bases de données disponibles sur un serveur Odoo.

        Args:
            odoo_url: URL du serveur Odoo

        Returns:
            Dictionnaire avec:
            - success: bool
            - databases: list[str] (liste des bases si succès)
            - message: str (message d'erreur si échec)
        """
        try:
            connector = OdooConnector(
                url=odoo_url,
                database="",  # Non requis pour lister les bases
                username="",
                credential="",
                auth_method="api_key",
            )
            databases = connector.list_databases()

            return {
                "success": True,
                "databases": databases,
            }

        except Exception as e:
            return {
                "success": False,
                "databases": [],
                "message": str(e),
            }

    def get_server_version(
        self,
        odoo_url: str,
    ) -> Dict[str, Any]:
        """
        Récupère la version du serveur Odoo.

        Args:
            odoo_url: URL du serveur Odoo

        Returns:
            Dictionnaire avec:
            - success: bool
            - version: str (version Odoo si succès)
            - message: str (message d'erreur si échec)
        """
        try:
            connector = OdooConnector(
                url=odoo_url,
                database="",
                username="",
                credential="",
                auth_method="api_key",
            )
            version = connector.get_server_version()

            return {
                "success": True,
                "version": version,
            }

        except Exception as e:
            return {
                "success": False,
                "version": None,
                "message": str(e),
            }
