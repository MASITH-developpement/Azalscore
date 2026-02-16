"""
AZALS MODULE 15 - Tenant Provisioning Service
===============================================

Provisioning automatique de tenants après paiement Stripe.

Flux:
1. Client complète Stripe Checkout
2. Webhook checkout.session.completed reçu
3. Tenant créé automatiquement
4. Utilisateur admin créé
5. Email de bienvenue envoyé (optionnel)
"""

import logging
import re
import secrets
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .base import BaseStripeService

logger = logging.getLogger(__name__)


class TenantProvisioningService(BaseStripeService):
    """Service de provisioning automatique de tenants."""

    def handle_checkout_completed(self, data: Dict[str, Any]):
        """
        Gère checkout Stripe complété - création automatique de tenant.

        Metadata attendues:
        - tenant_name: Nom de l'entreprise
        - admin_email: Email de l'admin
        - admin_first_name: Prénom
        - admin_last_name: Nom
        - country: Pays (défaut: FR)

        Args:
            data: Données de l'événement checkout.session.completed
        """
        logger.info("Processing checkout.session.completed: %s", data.get("id"))

        customer_email = data.get("customer_email") or data.get(
            "customer_details", {}
        ).get("email")
        metadata = data.get("metadata", {})

        tenant_name = metadata.get("tenant_name") or metadata.get("company_name")
        admin_email = metadata.get("admin_email") or customer_email
        admin_first_name = metadata.get("admin_first_name", "Admin")
        admin_last_name = metadata.get("admin_last_name", "")
        country = metadata.get("country", "FR")

        plan = self._determine_plan_from_checkout(data)

        if not admin_email:
            logger.error(
                "checkout.session.completed: No email found, cannot create tenant"
            )
            return

        if not tenant_name:
            tenant_name = admin_email.split("@")[0].replace(".", " ").title()

        tenant_id = self._generate_tenant_id(tenant_name)

        existing_tenant = self._get_tenant_by_email(admin_email)
        if existing_tenant:
            logger.info(
                "Tenant already exists for email %s, skipping creation", admin_email
            )
            return

        result = self._provision_new_tenant(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            admin_email=admin_email,
            admin_first_name=admin_first_name,
            admin_last_name=admin_last_name,
            plan=plan,
            country=country,
            stripe_customer_id=data.get("customer"),
            stripe_subscription_id=data.get("subscription"),
        )

        if result:
            logger.info(
                "Tenant %s created successfully for %s", tenant_id, admin_email
            )
        else:
            logger.error("Failed to create tenant for %s", admin_email)

    def handle_subscription_created(self, data: Dict[str, Any]):
        """Gère création abonnement."""
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")

        logger.info(
            "Subscription created | subscription_id=%s customer_id=%s status=%s",
            subscription_id,
            customer_id,
            status,
        )

        metadata = data.get("metadata", {})

        if status in ["active", "trialing"] and metadata.get("tenant_id"):
            tenant_id = metadata.get("tenant_id")
            self._update_tenant_stripe_info(
                tenant_id=tenant_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan=self._determine_plan_from_subscription(data),
            )

    def handle_subscription_updated(self, data: Dict[str, Any]):
        """Gère mise à jour abonnement."""
        subscription_id = data.get("id")
        status = data.get("status")
        metadata = data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        if not tenant_id:
            tenant_id = self._find_tenant_by_subscription(subscription_id)

        if not tenant_id:
            logger.warning("No tenant found for subscription %s", subscription_id)
            return

        if status == "active":
            self._activate_tenant(tenant_id)
            new_plan = self._determine_plan_from_subscription(data)
            self._update_tenant_plan(tenant_id, new_plan)
        elif status == "past_due":
            self._mark_tenant_payment_issue(tenant_id)
        elif status == "unpaid":
            self._suspend_tenant(tenant_id, reason="payment_failed")

    def handle_subscription_deleted(self, data: Dict[str, Any]):
        """Gère suppression abonnement."""
        subscription_id = data.get("id")
        metadata = data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        if not tenant_id:
            tenant_id = self._find_tenant_by_subscription(subscription_id)

        if tenant_id:
            self._suspend_tenant(tenant_id, reason="subscription_cancelled")
            logger.info(
                "Subscription cancelled | subscription_id=%s tenant=%s",
                subscription_id,
                tenant_id,
            )
        else:
            logger.warning(
                "Subscription cancelled but no tenant found | subscription_id=%s",
                subscription_id,
            )

    def handle_invoice_paid(self, data: Dict[str, Any]):
        """Gère facture payée."""
        subscription_id = data.get("subscription")
        if not subscription_id:
            return

        metadata = data.get("subscription_details", {}).get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        if not tenant_id:
            tenant_id = self._find_tenant_by_subscription(subscription_id)

        if tenant_id:
            self._activate_tenant(tenant_id)
            self._clear_payment_issues(tenant_id)

    def handle_invoice_payment_failed(self, data: Dict[str, Any]):
        """Gère échec paiement facture."""
        subscription_id = data.get("subscription")
        attempt_count = data.get("attempt_count", 1)

        logger.warning(
            "Invoice payment failed | subscription_id=%s attempt=%s",
            subscription_id,
            attempt_count,
        )

        if not subscription_id:
            return

        tenant_id = self._find_tenant_by_subscription(subscription_id)

        if tenant_id:
            self._mark_tenant_payment_issue(tenant_id, attempt_count=attempt_count)

            if attempt_count >= 3:
                self._suspend_tenant(tenant_id, reason="payment_failed_multiple")
                logger.warning(
                    "Tenant suspended due to payment failures | tenant=%s",
                    tenant_id,
                )

    # =========================================================================
    # HELPERS INTERNES
    # =========================================================================

    def _generate_tenant_id(self, name: str) -> str:
        """Génère un tenant_id unique."""
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        slug = slug[:20]

        base_slug = slug
        counter = 0

        while self._tenant_exists(slug):
            counter += 1
            slug = f"{base_slug}-{counter}"

        return slug

    def _tenant_exists(self, tenant_id: str) -> bool:
        """Vérifie si un tenant existe."""
        from app.modules.tenants.models import Tenant

        return (
            self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            is not None
        )

    def _get_tenant_by_email(self, email: str):
        """Récupère un tenant par email admin."""
        from app.modules.tenants.models import Tenant

        return self.db.query(Tenant).filter(Tenant.email == email).first()

    def _find_tenant_by_subscription(self, subscription_id: str) -> Optional[str]:
        """Trouve le tenant_id associé à une subscription."""
        from app.modules.tenants.models import Tenant

        tenant = (
            self.db.query(Tenant)
            .filter(
                Tenant.extra_data["stripe_subscription_id"].astext == subscription_id
            )
            .first()
        )
        return tenant.tenant_id if tenant else None

    def _determine_plan_from_checkout(self, data: Dict[str, Any]) -> str:
        """Détermine le plan depuis les données de checkout."""
        amount_total = data.get("amount_total", 0)
        metadata = data.get("metadata", {})

        if metadata.get("plan"):
            return metadata.get("plan").upper()

        if amount_total >= 50000:
            return "ENTERPRISE"
        elif amount_total >= 10000:
            return "PROFESSIONAL"
        elif amount_total >= 3000:
            return "STARTER"
        else:
            return "FREE"

    def _determine_plan_from_subscription(self, data: Dict[str, Any]) -> str:
        """Détermine le plan depuis les données de subscription."""
        items = data.get("items", {}).get("data", [])
        if items:
            price = items[0].get("price", {})
            unit_amount = price.get("unit_amount", 0)

            if unit_amount >= 50000:
                return "ENTERPRISE"
            elif unit_amount >= 10000:
                return "PROFESSIONAL"
            elif unit_amount >= 3000:
                return "STARTER"

        return "STARTER"

    def _provision_new_tenant(
        self,
        tenant_id: str,
        tenant_name: str,
        admin_email: str,
        admin_first_name: str,
        admin_last_name: str,
        plan: str,
        country: str,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Provisionne un nouveau tenant complet avec admin.

        Returns:
            Dict avec tenant et admin info, ou None si échec
        """
        from app.modules.iam.schemas import UserCreate
        from app.modules.iam.service import IAMService
        from app.modules.tenants.models import (
            SubscriptionPlan,
            Tenant,
            TenantEnvironment,
            TenantStatus,
        )

        temp_password = secrets.token_urlsafe(12)

        tenant = Tenant(
            tenant_id=tenant_id,
            name=tenant_name,
            legal_name=tenant_name,
            email=admin_email,
            country=country,
            environment=TenantEnvironment.PRODUCTION,
            status=TenantStatus.ACTIVE,
            plan=(
                SubscriptionPlan[plan]
                if plan in SubscriptionPlan.__members__
                else SubscriptionPlan.STARTER
            ),
            timezone="Europe/Paris",
            language="fr",
            currency="EUR",
            max_users=self._get_max_users_for_plan(plan),
            max_storage_gb=self._get_max_storage_for_plan(plan),
            features={"stripe_provisioned": True},
            extra_data={
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id,
                "provisioned_at": datetime.utcnow().isoformat(),
            },
            activated_at=datetime.utcnow(),
            created_by="system:stripe_webhook",
        )
        self.db.add(tenant)
        self.db.flush()

        iam_service = IAMService(self.db, tenant_id)
        admin_user = iam_service.create_user(
            UserCreate(
                email=admin_email,
                username=admin_email.split("@")[0],
                password=temp_password,
                first_name=admin_first_name,
                last_name=admin_last_name,
                role_codes=["ADMIN"],
                locale="fr",
                timezone="Europe/Paris",
            )
        )

        admin_user.must_change_password = True
        self.db.commit()

        logger.info("Provisioned tenant %s with admin %s", tenant_id, admin_email)

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "admin_email": admin_email,
            "admin_user_id": admin_user.id,
            "temporary_password": temp_password,
            "plan": plan,
        }

    def _get_max_users_for_plan(self, plan: str) -> int:
        """Retourne le nombre max d'utilisateurs selon le plan."""
        limits = {"FREE": 2, "STARTER": 5, "PROFESSIONAL": 25, "ENTERPRISE": 100}
        return limits.get(plan, 5)

    def _get_max_storage_for_plan(self, plan: str) -> int:
        """Retourne le stockage max en GB selon le plan."""
        limits = {"FREE": 1, "STARTER": 10, "PROFESSIONAL": 100, "ENTERPRISE": 500}
        return limits.get(plan, 10)

    def _update_tenant_stripe_info(
        self,
        tenant_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        plan: str,
    ):
        """Met à jour les infos Stripe d'un tenant."""
        from app.modules.tenants.models import SubscriptionPlan, Tenant

        tenant = (
            self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        )
        if tenant:
            if not tenant.extra_data:
                tenant.extra_data = {}
            tenant.extra_data["stripe_customer_id"] = stripe_customer_id
            tenant.extra_data["stripe_subscription_id"] = stripe_subscription_id
            tenant.plan = (
                SubscriptionPlan[plan]
                if plan in SubscriptionPlan.__members__
                else tenant.plan
            )
            tenant.updated_at = datetime.utcnow()
            self.db.commit()

    def _update_tenant_plan(self, tenant_id: str, plan: str):
        """Met à jour le plan d'un tenant."""
        from app.modules.tenants.models import SubscriptionPlan, Tenant

        tenant = (
            self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        )
        if tenant and plan in SubscriptionPlan.__members__:
            tenant.plan = SubscriptionPlan[plan]
            tenant.max_users = self._get_max_users_for_plan(plan)
            tenant.max_storage_gb = self._get_max_storage_for_plan(plan)
            tenant.updated_at = datetime.utcnow()
            self.db.commit()

    def _activate_tenant(self, tenant_id: str):
        """Active un tenant."""
        from app.modules.tenants.models import Tenant, TenantStatus

        tenant = (
            self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        )
        if tenant and tenant.status != TenantStatus.ACTIVE:
            tenant.status = TenantStatus.ACTIVE
            tenant.suspended_at = None
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info("Tenant %s activated", tenant_id)

    def _suspend_tenant(self, tenant_id: str, reason: str):
        """Suspend un tenant."""
        from app.modules.tenants.models import Tenant, TenantStatus

        tenant = (
            self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        )
        if tenant:
            tenant.status = TenantStatus.SUSPENDED
            tenant.suspended_at = datetime.utcnow()
            if not tenant.extra_data:
                tenant.extra_data = {}
            tenant.extra_data["suspension_reason"] = reason
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info("Tenant %s suspended: %s", tenant_id, reason)

    def _mark_tenant_payment_issue(self, tenant_id: str, attempt_count: int = 1):
        """Marque un tenant comme ayant un problème de paiement."""
        from app.modules.tenants.models import Tenant

        tenant = (
            self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        )
        if tenant:
            if not tenant.extra_data:
                tenant.extra_data = {}
            tenant.extra_data["payment_issue"] = True
            tenant.extra_data["payment_failure_count"] = attempt_count
            tenant.extra_data["last_payment_failure"] = datetime.utcnow().isoformat()
            tenant.updated_at = datetime.utcnow()
            self.db.commit()

    def _clear_payment_issues(self, tenant_id: str):
        """Efface les problèmes de paiement d'un tenant."""
        from app.modules.tenants.models import Tenant

        tenant = (
            self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        )
        if tenant and tenant.extra_data:
            tenant.extra_data.pop("payment_issue", None)
            tenant.extra_data.pop("payment_failure_count", None)
            tenant.extra_data.pop("last_payment_failure", None)
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
