"""
AZALS MODULE 15 - Stripe Config Service
=========================================

Gestion de la configuration Stripe.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import StripeConfig
from app.modules.stripe_integration.schemas import StripeConfigCreate, StripeConfigUpdate

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class ConfigService(BaseStripeService[StripeConfig]):
    """Service de gestion de la configuration Stripe."""

    model = StripeConfig

    def create(self, data: StripeConfigCreate) -> StripeConfig:
        """
        Crée la configuration Stripe du tenant.

        Args:
            data: Données de configuration

        Returns:
            Configuration créée

        Raises:
            ValueError: Si configuration existe déjà
        """
        existing = self._get_config()
        if existing:
            raise ValueError("Configuration déjà existante")

        config = StripeConfig(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        self._config = config
        logger.info(
            "Stripe config created | tenant=%s live_mode=%s",
            self.tenant_id,
            config.is_live_mode,
        )
        return config

    def update(self, data: StripeConfigUpdate) -> StripeConfig:
        """
        Met à jour la configuration Stripe.

        Args:
            data: Données de mise à jour

        Returns:
            Configuration mise à jour

        Raises:
            ValueError: Si configuration non trouvée
        """
        config = self._get_config()
        if not config:
            raise ValueError("Configuration non trouvée")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_at = self._now()
        self.db.commit()
        self.db.refresh(config)

        self._config = config
        logger.info("Stripe config updated | tenant=%s", self.tenant_id)
        return config

    def get(self) -> Optional[StripeConfig]:
        """
        Récupère la configuration Stripe.

        Returns:
            Configuration ou None
        """
        return self._get_config()

    def delete(self) -> bool:
        """
        Supprime la configuration Stripe.

        Returns:
            True si supprimée
        """
        config = self._get_config()
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()
        self._config = None

        logger.info("Stripe config deleted | tenant=%s", self.tenant_id)
        return True
