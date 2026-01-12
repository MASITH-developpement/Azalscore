"""
AZALSCORE - Tests du Guard Statut Tenant
==========================================
Tests du blocage des tenants impayés/suspendus.

Exécution:
    pytest tests/test_tenant_guard.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.tenant_status_guard import (
    get_tenant_with_status,
    require_active_subscription,
    check_user_limit,
    check_storage_limit,
    suspend_tenant,
    reactivate_tenant,
    convert_trial_to_active,
)


class TestGetTenantWithStatus:
    """Tests de la fonction get_tenant_with_status."""

    def test_active_tenant_allowed(self, db, sample_tenant):
        """Test: tenant ACTIVE → accès autorisé."""
        # Simuler les dépendances
        result = get_tenant_with_status.__wrapped__(
            tenant_id=sample_tenant.tenant_id,
            db=db
        )
        
        assert result is not None
        assert result.tenant_id == sample_tenant.tenant_id

    def test_trial_tenant_allowed(self, db, trial_tenant):
        """Test: tenant TRIAL valide → accès autorisé."""
        result = get_tenant_with_status.__wrapped__(
            tenant_id=trial_tenant.tenant_id,
            db=db
        )
        
        assert result is not None
        assert result.tenant_id == trial_tenant.tenant_id

    def test_expired_trial_blocked(self, db, expired_trial_tenant):
        """Test: tenant TRIAL expiré → HTTP 402."""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_with_status.__wrapped__(
                tenant_id=expired_trial_tenant.tenant_id,
                db=db
            )
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["code"] == "TRIAL_EXPIRED"

    def test_suspended_tenant_blocked(self, db, suspended_tenant):
        """Test: tenant SUSPENDED → HTTP 402."""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_with_status.__wrapped__(
                tenant_id=suspended_tenant.tenant_id,
                db=db
            )
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["code"] == "PAYMENT_REQUIRED"

    def test_cancelled_tenant_blocked(self, db, cancelled_tenant):
        """Test: tenant CANCELLED → HTTP 403."""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_with_status.__wrapped__(
                tenant_id=cancelled_tenant.tenant_id,
                db=db
            )
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TENANT_CANCELLED"

    def test_unknown_tenant_not_found(self, db):
        """Test: tenant inexistant → HTTP 404."""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_with_status.__wrapped__(
                tenant_id="unknown-tenant",
                db=db
            )
        
        assert exc_info.value.status_code == 404

    def test_error_includes_action_url(self, db, suspended_tenant):
        """Test: erreur inclut URL pour action."""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_with_status.__wrapped__(
                tenant_id=suspended_tenant.tenant_id,
                db=db
            )
        
        assert "billing_url" in exc_info.value.detail

    def test_trial_expired_includes_pricing_url(self, db, expired_trial_tenant):
        """Test: trial expiré inclut URL pricing."""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_with_status.__wrapped__(
                tenant_id=expired_trial_tenant.tenant_id,
                db=db
            )
        
        assert "pricing_url" in exc_info.value.detail


class TestRequireActiveSubscription:
    """Tests de la vérification d'abonnement actif."""

    def test_trial_tenant_no_subscription_required(self, db, trial_tenant):
        """Test: tenant TRIAL n'a pas besoin d'abonnement."""
        result = require_active_subscription.__wrapped__(
            tenant=trial_tenant,
            db=db
        )
        
        assert result is not None

    def test_active_tenant_needs_subscription(self, db, sample_tenant):
        """Test: tenant ACTIVE sans abonnement → erreur."""
        # Le sample_tenant est ACTIVE mais n'a pas d'abonnement créé
        with pytest.raises(HTTPException) as exc_info:
            require_active_subscription.__wrapped__(
                tenant=sample_tenant,
                db=db
            )
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["code"] == "NO_SUBSCRIPTION"

    def test_active_tenant_with_valid_subscription(self, db, sample_tenant):
        """Test: tenant ACTIVE avec abonnement valide → OK."""
        from app.modules.tenants.models import TenantSubscription, SubscriptionPlan, BillingCycle
        
        # Créer un abonnement valide
        subscription = TenantSubscription(
            tenant_id=sample_tenant.tenant_id,
            plan=SubscriptionPlan.PROFESSIONAL,
            billing_cycle=BillingCycle.MONTHLY,
            starts_at=datetime.utcnow() - timedelta(days=10),
            ends_at=datetime.utcnow() + timedelta(days=20),
            is_active=True,
            is_trial=False,
        )
        db.add(subscription)
        db.commit()
        
        result = require_active_subscription.__wrapped__(
            tenant=sample_tenant,
            db=db
        )
        
        assert result is not None

    def test_active_tenant_with_expired_subscription(self, db, sample_tenant):
        """Test: tenant ACTIVE avec abonnement expiré → erreur."""
        from app.modules.tenants.models import TenantSubscription, SubscriptionPlan, BillingCycle
        
        # Créer un abonnement expiré
        subscription = TenantSubscription(
            tenant_id=sample_tenant.tenant_id,
            plan=SubscriptionPlan.PROFESSIONAL,
            billing_cycle=BillingCycle.MONTHLY,
            starts_at=datetime.utcnow() - timedelta(days=40),
            ends_at=datetime.utcnow() - timedelta(days=10),  # Expiré
            is_active=True,
            is_trial=False,
        )
        db.add(subscription)
        db.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            require_active_subscription.__wrapped__(
                tenant=sample_tenant,
                db=db
            )
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["code"] == "SUBSCRIPTION_EXPIRED"


class TestCheckUserLimit:
    """Tests de la vérification de limite d'utilisateurs."""

    def test_under_limit_allowed(self, db, sample_tenant, sample_user):
        """Test: sous la limite → autorisé."""
        # sample_tenant a max_users=25, on a 1 user
        result = check_user_limit.__wrapped__(
            tenant=sample_tenant,
            db=db
        )
        
        assert result is True

    def test_at_limit_blocked(self, db, sample_tenant):
        """Test: à la limite → bloqué."""
        from app.core.models import User
        from app.core.security import hash_password
        import uuid
        
        # Mettre la limite à 2
        sample_tenant.max_users = 2
        db.commit()
        
        # Créer 2 utilisateurs
        for i in range(2):
            user = User(
                id=uuid.uuid4(),
                tenant_id=sample_tenant.tenant_id,
                email=f"user{i}@test.fr",
                password_hash=hash_password("Test123!"),
                first_name="Test",
                last_name=f"User{i}",
                role="operator",
                is_active=True,
            )
            db.add(user)
        db.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            check_user_limit.__wrapped__(
                tenant=sample_tenant,
                db=db
            )
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "USER_LIMIT_REACHED"

    def test_unlimited_users_allowed(self, db):
        """Test: limite -1 (illimité) → toujours autorisé."""
        from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan
        from app.core.models import User
        from app.core.security import hash_password
        import uuid
        
        # Créer tenant Enterprise (illimité)
        tenant = Tenant(
            tenant_id="unlimited-corp",
            name="Unlimited Corp",
            email="contact@unlimited.fr",
            status=TenantStatus.ACTIVE,
            plan=SubscriptionPlan.ENTERPRISE,
            max_users=-1,  # Illimité
        )
        db.add(tenant)
        
        # Créer 100 utilisateurs
        for i in range(100):
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.tenant_id,
                email=f"user{i}@unlimited.fr",
                password_hash=hash_password("Test123!"),
                first_name="Test",
                last_name=f"User{i}",
                role="operator",
                is_active=True,
            )
            db.add(user)
        db.commit()
        
        # Ne doit pas lever d'exception
        result = check_user_limit.__wrapped__(
            tenant=tenant,
            db=db
        )
        
        assert result is True


class TestCheckStorageLimit:
    """Tests de la vérification de limite de stockage."""

    def test_enough_storage_allowed(self, db, sample_tenant):
        """Test: assez de stockage → autorisé."""
        sample_tenant.storage_used_gb = 10
        sample_tenant.max_storage_gb = 50
        db.commit()
        
        result = check_storage_limit.__wrapped__(
            required_gb=5.0,
            tenant=sample_tenant
        )
        
        assert result is True

    def test_not_enough_storage_blocked(self, db, sample_tenant):
        """Test: pas assez de stockage → bloqué."""
        sample_tenant.storage_used_gb = 48
        sample_tenant.max_storage_gb = 50
        db.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            check_storage_limit.__wrapped__(
                required_gb=5.0,  # Besoin de 5, reste 2
                tenant=sample_tenant
            )
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "STORAGE_LIMIT_REACHED"


class TestSuspendTenant:
    """Tests de la suspension de tenant."""

    def test_suspend_tenant_success(self, db, sample_tenant):
        """Test: suspension réussie."""
        from app.modules.tenants.models import TenantStatus
        
        result = suspend_tenant(db, sample_tenant.tenant_id, "payment_failed")
        
        assert result is True
        
        db.refresh(sample_tenant)
        assert sample_tenant.status == TenantStatus.SUSPENDED
        assert sample_tenant.suspended_at is not None

    def test_suspend_unknown_tenant(self, db):
        """Test: suspension tenant inconnu → False."""
        result = suspend_tenant(db, "unknown-tenant", "payment_failed")
        
        assert result is False

    def test_suspend_creates_event(self, db, sample_tenant):
        """Test: suspension crée un événement d'audit."""
        from app.modules.tenants.models import TenantEvent
        
        suspend_tenant(db, sample_tenant.tenant_id, "payment_failed")
        
        event = db.query(TenantEvent).filter(
            TenantEvent.tenant_id == sample_tenant.tenant_id,
            TenantEvent.event_type == "TENANT_SUSPENDED"
        ).first()
        
        assert event is not None
        assert event.event_data["reason"] == "payment_failed"


class TestReactivateTenant:
    """Tests de la réactivation de tenant."""

    def test_reactivate_tenant_success(self, db, suspended_tenant):
        """Test: réactivation réussie."""
        from app.modules.tenants.models import TenantStatus
        
        result = reactivate_tenant(db, suspended_tenant.tenant_id)
        
        assert result is True
        
        db.refresh(suspended_tenant)
        assert suspended_tenant.status == TenantStatus.ACTIVE
        assert suspended_tenant.suspended_at is None

    def test_reactivate_unknown_tenant(self, db):
        """Test: réactivation tenant inconnu → False."""
        result = reactivate_tenant(db, "unknown-tenant")
        
        assert result is False

    def test_reactivate_creates_event(self, db, suspended_tenant):
        """Test: réactivation crée un événement d'audit."""
        from app.modules.tenants.models import TenantEvent
        
        reactivate_tenant(db, suspended_tenant.tenant_id)
        
        event = db.query(TenantEvent).filter(
            TenantEvent.tenant_id == suspended_tenant.tenant_id,
            TenantEvent.event_type == "TENANT_REACTIVATED"
        ).first()
        
        assert event is not None


class TestConvertTrialToActive:
    """Tests de la conversion trial → active."""

    def test_convert_trial_success(self, db, trial_tenant):
        """Test: conversion réussie."""
        from app.modules.tenants.models import TenantStatus, SubscriptionPlan
        
        result = convert_trial_to_active(db, trial_tenant.tenant_id, "PROFESSIONAL")
        
        assert result is True
        
        db.refresh(trial_tenant)
        assert trial_tenant.status == TenantStatus.ACTIVE
        assert trial_tenant.plan == SubscriptionPlan.PROFESSIONAL
        assert trial_tenant.activated_at is not None

    def test_convert_updates_limits_starter(self, db, trial_tenant):
        """Test: conversion STARTER met les bonnes limites."""
        convert_trial_to_active(db, trial_tenant.tenant_id, "STARTER")
        
        db.refresh(trial_tenant)
        assert trial_tenant.max_users == 5
        assert trial_tenant.max_storage_gb == 10

    def test_convert_updates_limits_enterprise(self, db, trial_tenant):
        """Test: conversion ENTERPRISE met utilisateurs illimités."""
        convert_trial_to_active(db, trial_tenant.tenant_id, "ENTERPRISE")
        
        db.refresh(trial_tenant)
        assert trial_tenant.max_users == -1
        assert trial_tenant.max_storage_gb == 500

    def test_convert_creates_event(self, db, trial_tenant):
        """Test: conversion crée un événement d'audit."""
        from app.modules.tenants.models import TenantEvent
        
        convert_trial_to_active(db, trial_tenant.tenant_id, "PROFESSIONAL")
        
        event = db.query(TenantEvent).filter(
            TenantEvent.tenant_id == trial_tenant.tenant_id,
            TenantEvent.event_type == "TRIAL_CONVERTED"
        ).first()
        
        assert event is not None
        assert event.event_data["plan"] == "PROFESSIONAL"

    def test_convert_unknown_tenant(self, db):
        """Test: conversion tenant inconnu → False."""
        result = convert_trial_to_active(db, "unknown-tenant", "PROFESSIONAL")
        
        assert result is False


class TestTenantGuardIntegration:
    """Tests d'intégration du guard tenant."""

    def test_full_lifecycle(self, db, trial_tenant):
        """Test: cycle complet trial → active → suspended → reactivated."""
        from app.modules.tenants.models import TenantStatus
        
        # 1. Conversion trial → active
        convert_trial_to_active(db, trial_tenant.tenant_id, "PROFESSIONAL")
        db.refresh(trial_tenant)
        assert trial_tenant.status == TenantStatus.ACTIVE
        
        # 2. Accès autorisé
        result = get_tenant_with_status.__wrapped__(
            tenant_id=trial_tenant.tenant_id,
            db=db
        )
        assert result is not None
        
        # 3. Suspension (impayé)
        suspend_tenant(db, trial_tenant.tenant_id, "payment_failed")
        db.refresh(trial_tenant)
        assert trial_tenant.status == TenantStatus.SUSPENDED
        
        # 4. Accès bloqué
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_with_status.__wrapped__(
                tenant_id=trial_tenant.tenant_id,
                db=db
            )
        assert exc_info.value.status_code == 402
        
        # 5. Réactivation
        reactivate_tenant(db, trial_tenant.tenant_id)
        db.refresh(trial_tenant)
        assert trial_tenant.status == TenantStatus.ACTIVE
        
        # 6. Accès autorisé à nouveau
        result = get_tenant_with_status.__wrapped__(
            tenant_id=trial_tenant.tenant_id,
            db=db
        )
        assert result is not None
