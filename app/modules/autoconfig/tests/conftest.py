"""Configuration pytest et fixtures pour les tests AutoConfig."""

import pytest
from datetime import datetime, timedelta

from app.core.saas_context import SaaSContext, UserRole
from app.modules.autoconfig.models import OverrideType


@pytest.fixture
def tenant_id():
    return "tenant-test-001"


@pytest.fixture
def user_id():
    return "user-test-001"


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"autoconfig.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    from app.modules.autoconfig import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)
    return mock_get_context


@pytest.fixture
def mock_autoconfig_service(monkeypatch, tenant_id, user_id):
    """Mock du service AutoConfig."""

    class MockAutoConfigService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = user_id

        # Profiles
        def initialize_predefined_profiles(self, created_by=None):
            return 10  # 10 profils créés

        def list_profiles(self, include_inactive=False):
            return [
                {
                    "id": 1,
                    "code": "CEO",
                    "name": "CEO",
                    "level": "executive",
                    "is_active": True
                },
                {
                    "id": 2,
                    "code": "ACCOUNTANT",
                    "name": "Comptable",
                    "level": "operational",
                    "is_active": True
                }
            ]

        def get_profile_by_code(self, code):
            if code == "CEO":
                return {
                    "id": 1,
                    "code": "CEO",
                    "name": "CEO",
                    "level": "executive"
                }
            return None

        def get_profile(self, profile_id):
            return {
                "id": profile_id,
                "code": "CEO",
                "name": "CEO",
                "level": "executive"
            }

        def detect_profile(self, job_title, department=None):
            if "CEO" in job_title.upper():
                return {
                    "id": 1,
                    "code": "CEO",
                    "name": "CEO",
                    "level": "executive"
                }
            return None

        # Assignments
        def auto_assign_profile(self, user_id, job_title, department=None, manager_id=None, assigned_by=None):
            if "CEO" not in job_title.upper():
                return None  # No profile found
            return {
                "id": 1,
                "user_id": user_id,
                "profile_id": 1,
                "job_title": job_title,
                "department": department,
                "is_auto": True
            }

        def manual_assign_profile(self, user_id, profile_code, assigned_by, job_title=None, department=None):
            if profile_code not in ["CEO", "ACCOUNTANT"]:
                raise ValueError(f"Profil {profile_code} non trouvé")
            return {
                "id": 2,
                "user_id": user_id,
                "profile_id": 1,
                "profile_code": profile_code,
                "is_auto": False
            }

        def get_user_profile(self, user_id):
            return {
                "id": 1,
                "user_id": user_id,
                "profile_id": 1,
                "profile": {
                    "code": "CEO",
                    "name": "CEO"
                },
                "is_active": True
            }

        def get_user_effective_config(self, user_id):
            return {
                "profile_code": "CEO",
                "profile_name": "CEO",
                "roles": ["admin", "user"],
                "permissions": ["*"],
                "modules": ["all"],
                "requires_mfa": True,
                "data_access_level": 10,
                "overrides_applied": 0
            }

        # Overrides
        def request_override(
            self, user_id, override_type, reason, requested_by,
            added_roles=None, removed_roles=None,
            added_permissions=None, removed_permissions=None,
            added_modules=None, removed_modules=None,
            expires_at=None, business_justification=None
        ):
            return {
                "id": 1,
                "user_id": user_id,
                "override_type": override_type,
                "status": "pending" if override_type == OverrideType.TEMPORARY else "approved",
                "reason": reason
            }

        def list_user_overrides(self, user_id, include_inactive=False):
            return [
                {"id": 1, "user_id": user_id, "status": "approved", "override_type": "temporary"},
                {"id": 2, "user_id": user_id, "status": "pending", "override_type": "temporary"}
            ]

        def approve_override(self, override_id, approved_by):
            if override_id == 999:
                raise ValueError("Override non trouvé")
            return {
                "id": override_id,
                "status": "approved",
                "approved_by": approved_by
            }

        def reject_override(self, override_id, rejected_by, rejection_reason):
            if override_id == 999:
                raise ValueError("Override non trouvé")
            return {
                "id": override_id,
                "status": "rejected",
                "rejected_by": rejected_by,
                "rejection_reason": rejection_reason
            }

        def revoke_override(self, override_id, revoked_by):
            if override_id == 999:
                raise ValueError("Override non trouvé")
            return {
                "id": override_id,
                "status": "revoked",
                "revoked_by": revoked_by
            }

        def expire_overrides(self):
            return 5  # 5 overrides expirés

        # Onboarding
        def create_onboarding(
            self, email, job_title, start_date, created_by=None,
            first_name=None, last_name=None, department=None, manager_id=None
        ):
            return {
                "id": 1,
                "email": email,
                "job_title": job_title,
                "start_date": start_date,
                "status": "pending"
            }

        def list_pending_onboardings(self):
            return [
                {"id": 1, "email": "new1@example.com", "status": "pending"},
                {"id": 2, "email": "new2@example.com", "status": "in_progress"}
            ]

        def execute_onboarding(self, onboarding_id, executed_by=None):
            if onboarding_id == 999:
                raise ValueError("Onboarding non trouvé")
            return {
                "steps": ["account_created", "profile_assigned", "welcome_email"],
                "errors": []
            }

        # Offboarding
        def create_offboarding(
            self, user_id, departure_date, departure_type, created_by,
            transfer_to_user_id=None, transfer_notes=None
        ):
            return {
                "id": 1,
                "user_id": user_id,
                "departure_date": departure_date,
                "departure_type": departure_type,
                "status": "scheduled"
            }

        def list_scheduled_offboardings(self):
            return [
                {"id": 1, "user_id": 100, "status": "scheduled"},
                {"id": 2, "user_id": 101, "status": "in_progress"}
            ]

        def execute_offboarding(self, offboarding_id, executed_by=None):
            if offboarding_id == 999:
                raise ValueError("Offboarding non trouvé")
            return {
                "steps": ["overrides_revoked", "profile_revoked", "account_deactivated"],
                "errors": []
            }

        def execute_due_offboardings(self):
            return 3  # 3 offboardings exécutés

    from app.modules.autoconfig import router_v2

    def mock_get_service(db, tenant_id, user_id):
        return MockAutoConfigService(db, tenant_id, user_id)

    monkeypatch.setattr(router_v2, "get_autoconfig_service", mock_get_service)
    return MockAutoConfigService(None, tenant_id, user_id)
