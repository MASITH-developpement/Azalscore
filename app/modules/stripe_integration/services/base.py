"""
AZALS MODULE 15 - Base Stripe Service
=======================================

Classe de base pour tous les sous-services Stripe.
"""

import logging
import uuid
from datetime import datetime
from typing import Generic, Optional, TypeVar

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import StripeConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseStripeService(Generic[T]):
    """
    Service de base pour les services Stripe.

    Fournit:
    - Accès à la configuration Stripe
    - Client Stripe (mocked en développement)
    - Utilitaires communs
    """

    model: type = None

    def __init__(self, db: Session, tenant_id: str, user_id: Optional[str] = None):
        """
        Initialise le service Stripe.

        Args:
            db: Session SQLAlchemy
            tenant_id: Identifiant du tenant
            user_id: Identifiant de l'utilisateur (optionnel, pour audit)
        """
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._config: Optional[StripeConfig] = None
        self._stripe = None

    def _get_config(self) -> Optional[StripeConfig]:
        """
        Récupère la configuration Stripe du tenant.

        Returns:
            Configuration Stripe ou None
        """
        if self._config is None:
            self._config = (
                self.db.query(StripeConfig)
                .filter(StripeConfig.tenant_id == self.tenant_id)
                .first()
            )
        return self._config

    def _get_stripe_client(self):
        """
        Obtient le client Stripe configuré.

        Returns:
            Client Stripe configuré

        Raises:
            ValueError: Si configuration non trouvée
        """
        config = self._get_config()
        if not config:
            raise ValueError("Configuration Stripe non trouvée")

        # En production, importer stripe et configurer
        # import stripe
        # api_key = config.api_key_live if config.is_live_mode else config.api_key_test
        # stripe.api_key = api_key
        # return stripe

        # Pour le développement, retourner None (mocked)
        return None

    def _base_query(self):
        """
        Requête de base avec filtre tenant.

        Returns:
            Query SQLAlchemy filtrée par tenant_id
        """
        if self.model is None:
            raise NotImplementedError("model doit être défini dans la sous-classe")
        return self.db.query(self.model).filter(
            self.model.tenant_id == self.tenant_id
        )

    def _get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Récupère une entité par ID.

        Args:
            entity_id: ID de l'entité

        Returns:
            Entité ou None
        """
        return self._base_query().filter(self.model.id == entity_id).first()

    @staticmethod
    def _generate_stripe_id(prefix: str, length: int = 14) -> str:
        """
        Génère un ID Stripe simulé.

        Args:
            prefix: Préfixe (ex: "cus_", "pi_", "pm_")
            length: Longueur de la partie aléatoire

        Returns:
            ID simulé
        """
        return f"{prefix}{uuid.uuid4().hex[:length]}"

    @staticmethod
    def _now() -> datetime:
        """Retourne datetime UTC actuel."""
        return datetime.utcnow()
