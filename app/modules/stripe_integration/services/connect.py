"""
AZALS MODULE 15 - Stripe Connect Service
==========================================

Gestion des comptes Stripe Connect.
"""

import logging
from datetime import timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import (
    StripeAccountStatus,
    StripeConnectAccount,
)
from app.modules.stripe_integration.schemas import ConnectAccountCreate

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class ConnectService(BaseStripeService[StripeConnectAccount]):
    """Service de gestion des comptes Stripe Connect."""

    model = StripeConnectAccount

    def create(self, data: ConnectAccountCreate) -> StripeConnectAccount:
        """
        Crée un compte Connect.

        Args:
            data: Données du compte

        Returns:
            Compte créé
        """
        # Simuler appel API Stripe
        stripe_account_id = self._generate_stripe_id("acct_", 16)
        onboarding_id = self._generate_stripe_id("", 20)

        account = StripeConnectAccount(
            tenant_id=self.tenant_id,
            stripe_account_id=stripe_account_id,
            vendor_id=data.vendor_id,
            account_type=data.account_type,
            country=data.country,
            email=data.email,
            business_type=data.business_type,
            status=StripeAccountStatus.PENDING,
            charges_enabled=False,
            payouts_enabled=False,
            details_submitted=False,
            onboarding_url=f"https://connect.stripe.com/setup/{onboarding_id}",
            onboarding_expires_at=self._now() + timedelta(hours=24),
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        logger.info(
            "Connect account created | tenant=%s account_id=%s vendor_id=%s",
            self.tenant_id,
            stripe_account_id,
            data.vendor_id,
        )
        return account

    def get(self, account_id: int) -> Optional[StripeConnectAccount]:
        """
        Récupère un compte Connect.

        Args:
            account_id: ID du compte

        Returns:
            Compte ou None
        """
        return self._get_by_id(account_id)

    def get_by_vendor(self, vendor_id: int) -> Optional[StripeConnectAccount]:
        """
        Récupère un compte par vendor_id.

        Args:
            vendor_id: ID du vendeur

        Returns:
            Compte ou None
        """
        return (
            self._base_query()
            .filter(StripeConnectAccount.vendor_id == vendor_id)
            .first()
        )

    def list(
        self,
        status: Optional[StripeAccountStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[StripeConnectAccount]:
        """
        Liste les comptes Connect.

        Args:
            status: Filtrer par statut
            skip: Offset
            limit: Limite

        Returns:
            Liste des comptes
        """
        query = self._base_query()

        if status:
            query = query.filter(StripeConnectAccount.status == status)

        return (
            query.order_by(StripeConnectAccount.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def refresh_onboarding_link(self, account_id: int) -> Optional[str]:
        """
        Rafraîchit le lien d'onboarding.

        Args:
            account_id: ID du compte

        Returns:
            Nouveau lien ou None
        """
        account = self.get(account_id)
        if not account:
            return None

        # Simuler génération nouveau lien
        onboarding_id = self._generate_stripe_id("", 20)
        account.onboarding_url = f"https://connect.stripe.com/setup/{onboarding_id}"
        account.onboarding_expires_at = self._now() + timedelta(hours=24)

        self.db.commit()
        self.db.refresh(account)

        logger.info(
            "Onboarding link refreshed | tenant=%s account_id=%s",
            self.tenant_id,
            account_id,
        )
        return account.onboarding_url

    def activate(self, account_id: int) -> Optional[StripeConnectAccount]:
        """
        Active un compte Connect.

        Args:
            account_id: ID du compte

        Returns:
            Compte activé ou None
        """
        account = self.get(account_id)
        if not account:
            return None

        account.status = StripeAccountStatus.ACTIVE
        account.charges_enabled = True
        account.payouts_enabled = True
        account.details_submitted = True
        account.updated_at = self._now()

        self.db.commit()
        self.db.refresh(account)

        logger.info(
            "Connect account activated | tenant=%s account_id=%s",
            self.tenant_id,
            account_id,
        )
        return account

    def suspend(self, account_id: int, reason: Optional[str] = None) -> bool:
        """
        Suspend un compte Connect.

        Args:
            account_id: ID du compte
            reason: Raison de la suspension

        Returns:
            True si suspendu
        """
        account = self.get(account_id)
        if not account:
            return False

        account.status = StripeAccountStatus.SUSPENDED
        account.charges_enabled = False
        account.payouts_enabled = False
        account.updated_at = self._now()

        self.db.commit()

        logger.info(
            "Connect account suspended | tenant=%s account_id=%s reason=%s",
            self.tenant_id,
            account_id,
            reason,
        )
        return True
