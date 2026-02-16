"""
AZALS MODULE - Odoo Import Base Service
=========================================

Service de base avec fonctionnalités communes pour tous les sous-services.
Gère le chiffrement des credentials, la création de connecteurs et mappers.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.cache import CacheTTL, get_cache
from app.modules.odoo_import.connector import OdooConnector
from app.modules.odoo_import.mapper import OdooMapper
from app.modules.odoo_import.models import (
    OdooConnectionConfig,
    OdooFieldMapping,
    OdooImportHistory,
    OdooImportStatus,
    OdooSyncType,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Clé de chiffrement pour les credentials
_ENV_KEY = os.environ.get("ENCRYPTION_KEY")
if _ENV_KEY:
    ENCRYPTION_KEY = _ENV_KEY.encode() if isinstance(_ENV_KEY, str) else _ENV_KEY
else:
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning(
        "[ODOO_IMPORT] ENCRYPTION_KEY non définie, utilisation clé temporaire"
    )


class BaseOdooService(Generic[T]):
    """
    Service de base pour les imports Odoo.

    Fournit:
    - Gestion du chiffrement des credentials
    - Création de connecteurs Odoo
    - Création de mappers avec mappings personnalisés
    - Création d'historiques d'import
    - Méthodes utilitaires communes
    """

    model: Type[T] = None

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        user_id: Optional[str] = None,
    ):
        """
        Initialise le service de base.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour isolation multi-tenant
            user_id: ID de l'utilisateur pour audit
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._fernet = Fernet(ENCRYPTION_KEY)
        self._cache = get_cache()

    # =========================================================================
    # CHIFFREMENT
    # =========================================================================

    def _encrypt_credential(self, credential: str) -> str:
        """
        Chiffre un credential avec Fernet.

        Args:
            credential: Mot de passe ou API key en clair

        Returns:
            Credential chiffré (base64)
        """
        return self._fernet.encrypt(credential.encode()).decode()

    def _decrypt_credential(self, encrypted: str) -> str:
        """
        Déchiffre un credential.

        Args:
            encrypted: Credential chiffré

        Returns:
            Credential en clair
        """
        return self._fernet.decrypt(encrypted.encode()).decode()

    # =========================================================================
    # CONNECTEUR ET MAPPER
    # =========================================================================

    def _get_connector(self, config: OdooConnectionConfig) -> OdooConnector:
        """
        Crée et connecte un OdooConnector pour une configuration.

        Args:
            config: Configuration de connexion

        Returns:
            Connecteur Odoo connecté
        """
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
        """
        Crée un mapper avec les mappings personnalisés du tenant.

        Args:
            config_id: ID de la configuration

        Returns:
            Mapper configuré
        """
        custom_mappings = {}
        field_mappings = (
            self.db.query(OdooFieldMapping)
            .filter(
                OdooFieldMapping.tenant_id == self.tenant_id,
                OdooFieldMapping.config_id == config_id,
                OdooFieldMapping.is_active == True,
            )
            .all()
        )

        for fm in field_mappings:
            custom_mappings[fm.odoo_model] = fm.field_mapping

        return OdooMapper(custom_mappings=custom_mappings)

    # =========================================================================
    # GESTION DE LA CONFIGURATION
    # =========================================================================

    def get_config(self, config_id: UUID) -> Optional[OdooConnectionConfig]:
        """
        Récupère une configuration par ID avec isolation tenant.

        Args:
            config_id: ID de la configuration

        Returns:
            Configuration ou None si non trouvée
        """
        return (
            self.db.query(OdooConnectionConfig)
            .filter(
                OdooConnectionConfig.tenant_id == self.tenant_id,
                OdooConnectionConfig.id == config_id,
            )
            .first()
        )

    def _require_config(self, config_id: UUID) -> OdooConnectionConfig:
        """
        Récupère une configuration ou lève une exception.

        Args:
            config_id: ID de la configuration

        Returns:
            Configuration

        Raises:
            ValueError: Si configuration non trouvée
        """
        config = self.get_config(config_id)
        if not config:
            raise ValueError(f"Configuration {config_id} non trouvée")
        return config

    # =========================================================================
    # HISTORIQUE D'IMPORT
    # =========================================================================

    def _create_history(
        self,
        config_id: UUID,
        sync_type: OdooSyncType,
        is_delta: bool = True,
        trigger_method: str = "manual",
    ) -> OdooImportHistory:
        """
        Crée un enregistrement d'historique d'import.

        Args:
            config_id: ID de la configuration
            sync_type: Type de synchronisation
            is_delta: True pour import delta (incrémental)
            trigger_method: Méthode de déclenchement (manual, scheduled, api)

        Returns:
            Historique créé avec status RUNNING
        """
        history = OdooImportHistory(
            tenant_id=self.tenant_id,
            config_id=config_id,
            sync_type=sync_type,
            status=OdooImportStatus.RUNNING,
            triggered_by=UUID(self.user_id) if self.user_id else None,
            trigger_method=trigger_method,
            is_delta_sync=is_delta,
        )
        self.db.add(history)
        self.db.commit()
        return history

    def _finalize_history(
        self,
        history: OdooImportHistory,
        created: int,
        updated: int,
        errors: List[Dict[str, Any]],
    ) -> OdooImportHistory:
        """
        Finalise un historique d'import avec les résultats.

        Args:
            history: Historique à finaliser
            created: Nombre d'enregistrements créés
            updated: Nombre d'enregistrements mis à jour
            errors: Liste des erreurs rencontrées

        Returns:
            Historique finalisé
        """
        history.created_count = created
        history.updated_count = updated
        history.error_count = len(errors)
        history.error_details = errors[:100]  # Limiter les erreurs stockées

        if errors and created == 0 and updated == 0:
            history.status = OdooImportStatus.ERROR
        elif errors:
            history.status = OdooImportStatus.PARTIAL
        else:
            history.status = OdooImportStatus.SUCCESS

        history.completed_at = datetime.utcnow()
        history.duration_seconds = int(
            (history.completed_at - history.started_at).total_seconds()
        )

        self.db.commit()
        self.db.refresh(history)
        return history

    def _fail_history(
        self,
        history: OdooImportHistory,
        error: Exception,
    ) -> None:
        """
        Marque un historique comme échoué.

        Args:
            history: Historique à marquer
            error: Exception survenue
        """
        history.status = OdooImportStatus.ERROR
        history.error_details = [{"error": str(error)}]
        history.completed_at = datetime.utcnow()
        self.db.commit()

    # =========================================================================
    # UTILITAIRES DE PARSING
    # =========================================================================

    @staticmethod
    def _parse_date(value: Any, include_time: bool = False) -> Optional[datetime]:
        """
        Parse une date depuis Odoo (peut être string, False, ou None).

        Args:
            value: Valeur à parser
            include_time: True pour parser datetime complet

        Returns:
            datetime ou None
        """
        if not value or value is False:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                if include_time and len(value) > 10:
                    return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
                return datetime.strptime(value[:10], "%Y-%m-%d")
            except ValueError:
                return None

        return None

    @staticmethod
    def _get_odoo_id(value: Any) -> Optional[int]:
        """
        Extrait l'ID Odoo d'une valeur Many2one.

        Args:
            value: Valeur Many2one [id, name] ou id seul

        Returns:
            ID Odoo ou None
        """
        if not value or value is False:
            return None
        if isinstance(value, (list, tuple)):
            return value[0] if value else None
        return int(value) if value else None

    @staticmethod
    def _get_odoo_name(value: Any) -> Optional[str]:
        """
        Extrait le nom d'une valeur Many2one.

        Args:
            value: Valeur Many2one [id, name]

        Returns:
            Nom ou None
        """
        if not value or value is False:
            return None
        if isinstance(value, (list, tuple)) and len(value) > 1:
            return value[1]
        return None
