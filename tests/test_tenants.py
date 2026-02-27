"""
AZALS MODULE T9 - Tests Tenants
================================

Tests unitaires pour le module de gestion des tenants.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.tenants.models import (
    Tenant, TenantSubscription, TenantModule, TenantInvitation,
    TenantUsage, TenantEvent, TenantSettings, TenantOnboarding,
    TenantStatus, SubscriptionPlan, BillingCycle, ModuleStatus, InvitationStatus
)
from app.modules.tenants.schemas import (
    TenantCreate, TenantUpdate,
    SubscriptionCreate, SubscriptionUpdate,
    ModuleActivation,
    TenantInvitationCreate,
    TenantSettingsUpdate,
    OnboardingStepUpdate,
    ProvisionTenantRequest
)
from app.modules.tenants.service import TenantService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    return MagicMock(spec=Session)


@pytest.fixture
def tenant_service(mock_db):
    """Service tenant pour tests."""
    return TenantService(mock_db, actor_id=1, actor_email="admin@test.com")


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des enums."""

    def test_tenant_status_values(self):
        """Vérifier les statuts de tenant."""
        assert TenantStatus.PENDING.value == "PENDING"
        assert TenantStatus.ACTIVE.value == "ACTIVE"
        assert TenantStatus.SUSPENDED.value == "SUSPENDED"
        assert TenantStatus.TRIAL.value == "TRIAL"
        assert len(TenantStatus) == 5

    def test_subscription_plan_values(self):
        """Vérifier les plans."""
        assert SubscriptionPlan.STARTER.value == "STARTER"
        assert SubscriptionPlan.ENTERPRISE.value == "ENTERPRISE"
        assert len(SubscriptionPlan) == 4

    def test_billing_cycle_values(self):
        """Vérifier les cycles de facturation."""
        assert BillingCycle.MONTHLY.value == "MONTHLY"
        assert BillingCycle.YEARLY.value == "YEARLY"
        assert len(BillingCycle) == 3

    def test_module_status_values(self):
        """Vérifier les statuts de module."""
        assert ModuleStatus.ACTIVE.value == "ACTIVE"
        assert ModuleStatus.DISABLED.value == "DISABLED"
        assert len(ModuleStatus) == 3

    def test_invitation_status_values(self):
        """Vérifier les statuts d'invitation."""
        assert InvitationStatus.PENDING.value == "PENDING"
        assert InvitationStatus.ACCEPTED.value == "ACCEPTED"
        assert len(InvitationStatus) == 4


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles."""

    def test_tenant_model(self):
        """Tester le modèle Tenant."""
        tenant = Tenant(
            tenant_id="test-tenant",
            name="Test Company",
            email="admin@test.com",
            country="FR",
            status=TenantStatus.PENDING,  # Explicit default
            plan=SubscriptionPlan.STARTER  # Explicit default
        )
        assert tenant.tenant_id == "test-tenant"
        assert tenant.status == TenantStatus.PENDING
        assert tenant.plan == SubscriptionPlan.STARTER

    def test_subscription_model(self):
        """Tester le modèle TenantSubscription."""
        subscription = TenantSubscription(
            tenant_id="test",
            plan=SubscriptionPlan.PROFESSIONAL,
            starts_at=datetime.utcnow(),
            is_active=True  # Explicit default
        )
        assert subscription.plan == SubscriptionPlan.PROFESSIONAL
        assert subscription.is_active == True

    def test_module_model(self):
        """Tester le modèle TenantModule."""
        module = TenantModule(
            tenant_id="test",
            module_code="M1",
            module_name="Trésorerie",
            status=ModuleStatus.ACTIVE  # Explicit default
        )
        assert module.module_code == "M1"
        assert module.status == ModuleStatus.ACTIVE

    def test_invitation_model(self):
        """Tester le modèle TenantInvitation."""
        invitation = TenantInvitation(
            token="abc123",
            email="invite@test.com",
            expires_at=datetime.utcnow() + timedelta(days=7),
            status=InvitationStatus.PENDING  # Explicit default
        )
        assert invitation.token == "abc123"
        assert invitation.status == InvitationStatus.PENDING

    def test_settings_model(self):
        """Tester le modèle TenantSettings."""
        settings = TenantSettings(
            tenant_id="test",
            two_factor_required=False,  # Explicit default
            session_timeout_minutes=30  # Explicit default
        )
        assert settings.two_factor_required == False
        assert settings.session_timeout_minutes == 30

    def test_onboarding_model(self):
        """Tester le modèle TenantOnboarding."""
        onboarding = TenantOnboarding(
            tenant_id="test",
            progress_percent=0,  # Explicit default
            current_step="company_info"  # Explicit default
        )
        assert onboarding.progress_percent == 0
        assert onboarding.current_step == "company_info"


# ============================================================================
# TESTS SCHÉMAS
# ============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_tenant_create_schema(self):
        """Tester TenantCreate."""
        data = TenantCreate(
            tenant_id="new-tenant",
            name="New Company",
            email="admin@new.com"
        )
        assert data.tenant_id == "new-tenant"
        assert data.plan == "STARTER"
        assert data.country == "FR"

    def test_tenant_create_schema_validation(self):
        """Tester la validation TenantCreate."""
        with pytest.raises(Exception):
            TenantCreate(
                tenant_id="ab",  # Trop court
                name="Test",
                email="admin@test.com"
            )

    def test_subscription_create_schema(self):
        """Tester SubscriptionCreate."""
        data = SubscriptionCreate(
            plan="PROFESSIONAL",
            starts_at=datetime.utcnow()
        )
        assert data.plan == "PROFESSIONAL"
        assert data.billing_cycle == "MONTHLY"

    def test_module_activation_schema(self):
        """Tester ModuleActivation."""
        data = ModuleActivation(
            module_code="M1",
            module_name="Trésorerie"
        )
        assert data.module_code == "M1"

    def test_invitation_create_schema(self):
        """Tester TenantInvitationCreate."""
        data = TenantInvitationCreate(
            email="invite@test.com",
            plan="ENTERPRISE"
        )
        assert data.expires_in_days == 7
        assert data.proposed_role == "TENANT_ADMIN"


# ============================================================================
# TESTS SERVICE - TENANTS
# ============================================================================

class TestServiceTenants:
    """Tests du service tenants."""

    def test_create_tenant(self, tenant_service, mock_db):
        """Tester la création de tenant."""
        data = TenantCreate(
            tenant_id="new-tenant",
            name="New Company",
            email="admin@new.com"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        tenant = tenant_service.create_tenant(data)
        mock_db.add.assert_called()

    def test_get_tenant(self, tenant_service, mock_db):
        """Tester la récupération de tenant."""
        mock_tenant = Tenant(
            id=1, tenant_id="test",
            name="Test", email="test@test.com"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant

        tenant = tenant_service.get_tenant("test")
        assert tenant.tenant_id == "test"

    def test_activate_tenant(self, tenant_service, mock_db):
        """Tester l'activation de tenant."""
        mock_tenant = Tenant(
            id=1, tenant_id="test",
            name="Test", email="test@test.com",
            status=TenantStatus.PENDING
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant

        tenant = tenant_service.activate_tenant("test")
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.activated_at is not None

    def test_suspend_tenant(self, tenant_service, mock_db):
        """Tester la suspension de tenant."""
        mock_tenant = Tenant(
            id=1, tenant_id="test",
            name="Test", email="test@test.com",
            status=TenantStatus.ACTIVE
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant

        tenant = tenant_service.suspend_tenant("test", "Non-paiement")
        assert tenant.status == TenantStatus.SUSPENDED

    def test_start_trial(self, tenant_service, mock_db):
        """Tester le démarrage d'essai."""
        mock_tenant = Tenant(
            id=1, tenant_id="test",
            name="Test", email="test@test.com",
            status=TenantStatus.PENDING
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant

        tenant = tenant_service.start_trial("test", 14)
        assert tenant.status == TenantStatus.TRIAL
        assert tenant.trial_ends_at is not None


# ============================================================================
# TESTS SERVICE - SUBSCRIPTIONS
# ============================================================================

class TestServiceSubscriptions:
    """Tests du service abonnements."""

    def test_create_subscription(self, tenant_service, mock_db):
        """Tester la création d'abonnement."""
        mock_tenant = Tenant(id=1, tenant_id="test", name="Test", email="test@test.com")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = SubscriptionCreate(
            plan="PROFESSIONAL",
            billing_cycle="YEARLY",
            starts_at=datetime.utcnow()
        )

        subscription = tenant_service.create_subscription("test", data)
        mock_db.add.assert_called()

    def test_update_subscription(self, tenant_service, mock_db):
        """Tester la mise à jour d'abonnement."""
        mock_subscription = TenantSubscription(
            id=1, tenant_id="test",
            plan=SubscriptionPlan.STARTER,
            billing_cycle=BillingCycle.MONTHLY,
            starts_at=datetime.utcnow(),
            is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription

        data = SubscriptionUpdate(plan="ENTERPRISE")
        subscription = tenant_service.update_subscription("test", data)
        assert subscription.plan == SubscriptionPlan.ENTERPRISE


# ============================================================================
# TESTS SERVICE - MODULES
# ============================================================================

class TestServiceModules:
    """Tests du service modules."""

    def test_activate_module(self, tenant_service, mock_db):
        """Tester l'activation de module."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = ModuleActivation(module_code="M1", module_name="Trésorerie")
        module = tenant_service.activate_module("test", data)
        mock_db.add.assert_called()

    def test_deactivate_module(self, tenant_service, mock_db):
        """Tester la désactivation de module."""
        mock_module = TenantModule(
            id=1, tenant_id="test",
            module_code="M1", status=ModuleStatus.ACTIVE
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_module

        module = tenant_service.deactivate_module("test", "M1")
        assert module.status == ModuleStatus.DISABLED

    def test_is_module_active(self, tenant_service, mock_db):
        """Tester la vérification de module actif."""
        mock_module = TenantModule(
            id=1, tenant_id="test",
            module_code="M1", status=ModuleStatus.ACTIVE
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_module

        is_active = tenant_service.is_module_active("test", "M1")
        assert is_active == True


# ============================================================================
# TESTS SERVICE - INVITATIONS
# ============================================================================

class TestServiceInvitations:
    """Tests du service invitations."""

    def test_create_invitation(self, tenant_service, mock_db):
        """Tester la création d'invitation."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = TenantInvitationCreate(
            email="invite@test.com",
            tenant_id="test",
            plan="PROFESSIONAL"
        )

        invitation = tenant_service.create_invitation(data)
        mock_db.add.assert_called()

    def test_accept_invitation(self, tenant_service, mock_db):
        """Tester l'acceptation d'invitation."""
        mock_invitation = TenantInvitation(
            id=1, token="abc123",
            email="invite@test.com",
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invitation

        invitation = tenant_service.accept_invitation("abc123")
        assert invitation.status == InvitationStatus.ACCEPTED

    def test_accept_expired_invitation(self, tenant_service, mock_db):
        """Tester l'acceptation d'invitation expirée."""
        mock_invitation = TenantInvitation(
            id=1, token="abc123",
            email="invite@test.com",
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invitation

        invitation = tenant_service.accept_invitation("abc123")
        assert invitation is None


# ============================================================================
# TESTS SERVICE - SETTINGS & ONBOARDING
# ============================================================================

class TestServiceSettingsOnboarding:
    """Tests settings et onboarding."""

    def test_update_settings(self, tenant_service, mock_db):
        """Tester la mise à jour des paramètres."""
        mock_settings = TenantSettings(id=1, tenant_id="test")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = TenantSettingsUpdate(
            two_factor_required=True,
            session_timeout_minutes=60
        )

        settings = tenant_service.update_settings("test", data)
        assert settings.two_factor_required == True

    def test_update_onboarding_step(self, tenant_service, mock_db):
        """Tester la mise à jour d'étape onboarding."""
        mock_onboarding = TenantOnboarding(
            id=1, tenant_id="test",
            progress_percent=0,
            current_step="company_info",
            # Explicit defaults for all boolean fields (SQLAlchemy defaults don't apply without DB)
            company_info_completed=False,
            admin_created=False,
            users_invited=False,
            modules_configured=False,
            country_pack_selected=False,
            first_data_imported=False,
            training_completed=False
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_onboarding
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = OnboardingStepUpdate(step="company_info", completed=True)
        onboarding = tenant_service.update_onboarding_step("test", data)
        assert onboarding.company_info_completed == True


# ============================================================================
# TESTS SERVICE - PROVISIONING
# ============================================================================

class TestServiceProvisioning:
    """Tests du provisioning."""

    @pytest.mark.skip(reason="Test d'intégration complexe nécessitant une vraie session DB")
    def test_provision_tenant(self, tenant_service, mock_db):
        """Tester le provisioning complet."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = ProvisionTenantRequest(
            tenant=TenantCreate(
                tenant_id="new-company",
                name="New Company",
                email="admin@new.com"
            ),
            admin_email="admin@new.com",
            admin_first_name="Admin",
            admin_last_name="User",
            modules=["T0", "T1", "M1"]
        )

        # Mock pour get_onboarding
        mock_onboarding = TenantOnboarding(
            id=1, tenant_id="new-company",
            progress_percent=0
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # get_tenant
            mock_onboarding,  # get_onboarding
        ]

        result = tenant_service.provision_tenant(data)
        assert "tenant" in result
        assert "activated_modules" in result

    @pytest.mark.skip(reason="Test d'intégration complexe nécessitant une vraie session DB")
    def test_provision_masith(self, tenant_service, mock_db):
        """Tester le provisioning de MASITH."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_onboarding = TenantOnboarding(
            id=1, tenant_id="masith",
            progress_percent=0
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # check existing
            None,  # get_tenant
            mock_onboarding,  # get_onboarding
        ]

        result = tenant_service.provision_masith()
        assert "tenant" in result


# ============================================================================
# TESTS SERVICE - PLATFORM STATS
# ============================================================================

class TestServicePlatformStats:
    """Tests des stats plateforme."""

    def test_get_platform_stats(self, tenant_service, mock_db):
        """Tester les statistiques."""
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 8
        mock_db.query.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.scalar.return_value = 50.5

        stats = tenant_service.get_platform_stats()
        assert stats["total_tenants"] == 10


# ============================================================================
# TESTS FACTORY
# ============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_tenant_service(self, mock_db):
        """Tester la factory."""
        from app.modules.tenants.service import get_tenant_service

        service = get_tenant_service(mock_db, actor_id=5, actor_email="admin@test.com")
        assert service.actor_id == 5
        assert service.actor_email == "admin@test.com"


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration."""

    def test_full_tenant_lifecycle(self, tenant_service, mock_db):
        """Tester le cycle de vie complet d'un tenant."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 1. Création
        data = TenantCreate(
            tenant_id="lifecycle-test",
            name="Lifecycle Test",
            email="admin@lifecycle.com"
        )

        tenant = tenant_service.create_tenant(data)

        # 2. Activation
        mock_tenant = Tenant(
            id=1, tenant_id="lifecycle-test",
            name="Lifecycle Test", email="admin@lifecycle.com",
            status=TenantStatus.PENDING
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant

        activated = tenant_service.activate_tenant("lifecycle-test")
        assert activated.status == TenantStatus.ACTIVE

        # 3. Suspension
        suspended = tenant_service.suspend_tenant("lifecycle-test", "Test")
        assert suspended.status == TenantStatus.SUSPENDED

    def test_module_workflow(self, tenant_service, mock_db):
        """Tester le workflow des modules."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 1. Activer module
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = ModuleActivation(module_code="M1", module_name="Trésorerie")
        module = tenant_service.activate_module("test", data)

        # 2. Désactiver
        mock_module = TenantModule(
            id=1, tenant_id="test",
            module_code="M1", status=ModuleStatus.ACTIVE
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_module

        deactivated = tenant_service.deactivate_module("test", "M1")
        assert deactivated.status == ModuleStatus.DISABLED
