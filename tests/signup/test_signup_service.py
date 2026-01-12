"""
AZALSCORE - Tests du Service Signup
=====================================
Tests unitaires pour l'inscription de nouvelles entreprises.

Exécution:
    pytest tests/test_signup_service.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.signup_service import SignupService, SignupError, PLAN_CONFIG


class TestSignupService:
    """Tests du service d'inscription."""

    # ========================================================================
    # TESTS DE GÉNÉRATION DU TENANT_ID
    # ========================================================================

    def test_generate_tenant_id_simple(self, db):
        """Test: nom simple → slug correct."""
        service = SignupService(db)
        
        result = service._generate_tenant_id("Acme Corporation")
        
        assert result == "acme-corporation"

    def test_generate_tenant_id_with_accents(self, db):
        """Test: accents supprimés correctement."""
        service = SignupService(db)
        
        result = service._generate_tenant_id("L'Épicerie du Côté")
        
        assert result == "lepicerie-du-cote"

    def test_generate_tenant_id_with_special_chars(self, db):
        """Test: caractères spéciaux supprimés."""
        service = SignupService(db)
        
        result = service._generate_tenant_id("DUPONT & Fils - S.A.S.")
        
        assert result == "dupont-fils-sas"

    def test_generate_tenant_id_max_length(self, db):
        """Test: longueur limitée à 40 caractères."""
        service = SignupService(db)
        
        long_name = "A" * 100
        result = service._generate_tenant_id(long_name)
        
        assert len(result) <= 40

    def test_generate_tenant_id_empty_fallback(self, db):
        """Test: nom vide → fallback aléatoire."""
        service = SignupService(db)
        
        result = service._generate_tenant_id("!!!@@@###")
        
        assert result.startswith("tenant-")
        assert len(result) > 7

    def test_generate_tenant_id_unique_suffix(self, db):
        """Test: doublon → suffixe numérique."""
        from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan
        
        # Créer un tenant existant
        existing = Tenant(
            tenant_id="acme-corp",
            name="Acme Corp",
            email="contact@acme.fr",
            status=TenantStatus.ACTIVE,
            plan=SubscriptionPlan.STARTER,
        )
        db.add(existing)
        db.commit()
        
        service = SignupService(db)
        result = service._generate_tenant_id("Acme Corp")
        
        assert result == "acme-corp-2"

    # ========================================================================
    # TESTS D'INSCRIPTION COMPLÈTE
    # ========================================================================

    def test_signup_success(self, db, sample_tenant_data):
        """Test: inscription réussie crée tenant + user + subscription."""
        service = SignupService(db)
        
        result = service.signup(**sample_tenant_data)
        
        # Vérifier les retours
        assert result["success"] is True or "tenant_id" in result
        assert result["tenant_id"] == "test-company-sas"
        assert result["admin_user"] is not None
        assert result["trial_ends_at"] > datetime.utcnow()
        
        # Vérifier le tenant en base
        from app.modules.tenants.models import Tenant, TenantStatus
        tenant = db.query(Tenant).filter(Tenant.tenant_id == result["tenant_id"]).first()
        assert tenant is not None
        assert tenant.status == TenantStatus.TRIAL
        assert tenant.name == sample_tenant_data["company_name"]

    def test_signup_creates_admin_user(self, db, sample_tenant_data):
        """Test: l'utilisateur admin est bien créé."""
        service = SignupService(db)
        
        result = service.signup(**sample_tenant_data)
        
        from app.core.models import User
        user = db.query(User).filter(User.email == sample_tenant_data["admin_email"]).first()
        
        assert user is not None
        assert user.tenant_id == result["tenant_id"]
        assert user.role == "admin"
        assert user.is_active is True
        assert user.first_name == sample_tenant_data["admin_first_name"]

    def test_signup_creates_subscription(self, db, sample_tenant_data):
        """Test: l'abonnement trial est créé."""
        service = SignupService(db)
        
        result = service.signup(**sample_tenant_data)
        
        from app.modules.tenants.models import TenantSubscription
        subscription = db.query(TenantSubscription).filter(
            TenantSubscription.tenant_id == result["tenant_id"]
        ).first()
        
        assert subscription is not None
        assert subscription.is_trial is True
        assert subscription.is_active is True
        assert subscription.ends_at > datetime.utcnow()

    def test_signup_activates_modules(self, db, sample_tenant_data):
        """Test: les modules selon le plan sont activés."""
        service = SignupService(db)
        
        result = service.signup(**sample_tenant_data)
        
        from app.modules.tenants.models import TenantModule, ModuleStatus
        modules = db.query(TenantModule).filter(
            TenantModule.tenant_id == result["tenant_id"],
            TenantModule.status == ModuleStatus.ACTIVE
        ).all()
        
        expected_modules = PLAN_CONFIG["PROFESSIONAL"]["modules"]
        assert len(modules) == len(expected_modules)

    def test_signup_creates_settings(self, db, sample_tenant_data):
        """Test: les settings par défaut sont créés."""
        service = SignupService(db)
        
        result = service.signup(**sample_tenant_data)
        
        from app.modules.tenants.models import TenantSettings
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == result["tenant_id"]
        ).first()
        
        assert settings is not None
        assert settings.auto_backup_enabled is True

    def test_signup_creates_onboarding(self, db, sample_tenant_data):
        """Test: l'onboarding est initialisé."""
        service = SignupService(db)
        
        result = service.signup(**sample_tenant_data)
        
        from app.modules.tenants.models import TenantOnboarding
        onboarding = db.query(TenantOnboarding).filter(
            TenantOnboarding.tenant_id == result["tenant_id"]
        ).first()
        
        assert onboarding is not None
        assert onboarding.company_info_completed is True
        assert onboarding.admin_created is True
        assert onboarding.progress_percent == 28

    # ========================================================================
    # TESTS D'ERREURS
    # ========================================================================

    def test_signup_duplicate_email_fails(self, db, sample_tenant_data, sample_user):
        """Test: email déjà utilisé → erreur."""
        service = SignupService(db)
        
        # Utiliser l'email de l'utilisateur existant
        sample_tenant_data["admin_email"] = sample_user.email
        sample_tenant_data["company_name"] = "Another Company"
        sample_tenant_data["company_email"] = "another@company.fr"
        
        with pytest.raises(SignupError) as exc_info:
            service.signup(**sample_tenant_data)
        
        assert exc_info.value.code == "EMAIL_EXISTS"

    def test_signup_duplicate_company_email_fails(self, db, sample_tenant_data, sample_tenant):
        """Test: email entreprise déjà utilisé → erreur."""
        service = SignupService(db)
        
        sample_tenant_data["company_email"] = sample_tenant.email
        sample_tenant_data["company_name"] = "Different Company"
        sample_tenant_data["admin_email"] = "new_admin@different.fr"
        
        with pytest.raises(SignupError) as exc_info:
            service.signup(**sample_tenant_data)
        
        assert exc_info.value.code == "COMPANY_EXISTS"

    def test_signup_invalid_plan_defaults_to_professional(self, db, sample_tenant_data):
        """Test: plan invalide → défaut PROFESSIONAL."""
        service = SignupService(db)
        
        sample_tenant_data["plan"] = "INVALID_PLAN"
        result = service.signup(**sample_tenant_data)
        
        from app.modules.tenants.models import Tenant
        tenant = db.query(Tenant).filter(Tenant.tenant_id == result["tenant_id"]).first()
        
        assert tenant.plan.value == "PROFESSIONAL"

    # ========================================================================
    # TESTS PLANS
    # ========================================================================

    def test_signup_starter_plan_limits(self, db, sample_tenant_data):
        """Test: plan STARTER applique les bonnes limites."""
        service = SignupService(db)
        
        sample_tenant_data["plan"] = "STARTER"
        result = service.signup(**sample_tenant_data)
        
        from app.modules.tenants.models import Tenant
        tenant = db.query(Tenant).filter(Tenant.tenant_id == result["tenant_id"]).first()
        
        assert tenant.max_users == 5
        assert tenant.max_storage_gb == 10

    def test_signup_enterprise_plan_limits(self, db):
        """Test: plan ENTERPRISE applique utilisateurs illimités."""
        service = SignupService(db)
        
        data = {
            "company_name": "Enterprise Corp",
            "company_email": "contact@enterprise.fr",
            "admin_email": "admin@enterprise.fr",
            "admin_password": "SecurePass123!",
            "admin_first_name": "CEO",
            "admin_last_name": "Boss",
            "plan": "ENTERPRISE",
        }
        
        result = service.signup(**data)
        
        from app.modules.tenants.models import Tenant
        tenant = db.query(Tenant).filter(Tenant.tenant_id == result["tenant_id"]).first()
        
        assert tenant.max_users == -1  # Illimité
        assert tenant.max_storage_gb == 500

    # ========================================================================
    # TESTS VÉRIFICATIONS
    # ========================================================================

    def test_check_email_available_true(self, db):
        """Test: email non utilisé → disponible."""
        service = SignupService(db)
        
        result = service.check_email_available("nouveau@email.fr")
        
        assert result is True

    def test_check_email_available_false(self, db, sample_user):
        """Test: email utilisé → non disponible."""
        service = SignupService(db)
        
        result = service.check_email_available(sample_user.email)
        
        assert result is False

    def test_check_company_available_true(self, db):
        """Test: nom entreprise non utilisé → disponible."""
        service = SignupService(db)
        
        result = service.check_company_available("Nouvelle Entreprise")
        
        assert result is True

    def test_check_company_available_false(self, db, sample_tenant):
        """Test: nom entreprise utilisé → non disponible."""
        service = SignupService(db)
        
        result = service.check_company_available(sample_tenant.name)
        
        assert result is False


class TestSignupServiceIntegration:
    """Tests d'intégration du service signup."""

    def test_full_signup_flow(self, db, mock_email_service):
        """Test: flux complet d'inscription."""
        service = SignupService(db)
        
        # 1. Vérifier disponibilité
        assert service.check_email_available("new@company.fr") is True
        assert service.check_company_available("New Company") is True
        
        # 2. Inscription
        result = service.signup(
            company_name="New Company",
            company_email="contact@newcompany.fr",
            admin_email="admin@newcompany.fr",
            admin_password="SecurePass123!",
            admin_first_name="Admin",
            admin_last_name="User",
            plan="PROFESSIONAL",
        )
        
        # 3. Vérifications
        assert result["tenant_id"] == "new-company"
        
        # 4. Vérifier que l'email n'est plus disponible
        assert service.check_email_available("admin@newcompany.fr") is False

    def test_password_is_hashed(self, db, sample_tenant_data):
        """Test: le mot de passe est bien hashé, pas stocké en clair."""
        service = SignupService(db)
        
        result = service.signup(**sample_tenant_data)
        
        from app.core.models import User
        user = db.query(User).filter(User.email == sample_tenant_data["admin_email"]).first()
        
        # Le hash ne doit pas être égal au mot de passe
        assert user.password_hash != sample_tenant_data["admin_password"]
        # Le hash doit commencer par $2b$ (bcrypt)
        assert user.password_hash.startswith("$2b$")

    def test_trial_duration_is_14_days(self, db, sample_tenant_data):
        """Test: la période d'essai est de 14 jours."""
        service = SignupService(db)
        
        before = datetime.utcnow()
        result = service.signup(**sample_tenant_data)
        after = datetime.utcnow()
        
        trial_ends = result["trial_ends_at"]
        
        # Doit être entre 13 et 15 jours (marge pour l'exécution)
        assert trial_ends > before + timedelta(days=13)
        assert trial_ends < after + timedelta(days=15)
