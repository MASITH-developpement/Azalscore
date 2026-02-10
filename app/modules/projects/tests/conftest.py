"""
Fixtures pour les tests Projects v2
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole
from app.main import app


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
def tenant_id():
    """Tenant ID de test"""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """User ID de test"""
    return "user-test-001"


@pytest.fixture
def auth_headers():
    """Headers d'authentification"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    """Mock get_saas_context pour tous les tests"""
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"projects.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            correlation_id="test-correlation"
        )

    from app.modules.projects import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)

    return mock_get_context


# ============================================================================
# FIXTURES PROJETS
# ============================================================================

@pytest.fixture
def sample_project_data(tenant_id):
    """Données de projet sample"""
    return {
        "name": "Projet Test",
        "code": "PROJ-001",
        "description": "Description du projet de test",
        "status": "DRAFT",
        "priority": "HIGH",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=90)),
        "budget": 100000.00,
    }


@pytest.fixture
def sample_project(sample_project_data, tenant_id, user_id):
    """Instance projet sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **sample_project_data,
        "progress": 0.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_phase_data():
    """Données de phase sample"""
    return {
        "name": "Phase 1 - Conception",
        "description": "Phase de conception du projet",
        "sequence": 1,
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
    }


@pytest.fixture
def sample_phase(sample_phase_data, sample_project):
    """Instance phase sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_phase_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_task_data():
    """Données de tâche sample"""
    return {
        "name": "Tâche de test",
        "description": "Description de la tâche",
        "status": "TODO",
        "priority": "MEDIUM",
        "estimated_hours": 8.0,
        "start_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=7)),
    }


@pytest.fixture
def sample_task(sample_task_data, sample_project, sample_phase):
    """Instance tâche sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        "phase_id": sample_phase["id"],
        **sample_task_data,
        "progress": 0.0,
        "actual_hours": 0.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_milestone_data():
    """Données de jalon sample"""
    return {
        "name": "Jalon 1 - Livraison MVP",
        "description": "Livraison de la version MVP",
        "target_date": str(date.today() + timedelta(days=45)),
        "is_achieved": False,
    }


@pytest.fixture
def sample_milestone(sample_milestone_data, sample_project):
    """Instance jalon sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_milestone_data,
        "achieved_date": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_team_member_data(user_id):
    """Données de membre d'équipe sample"""
    return {
        "user_id": user_id,
        "role": "DEVELOPER",
        "allocation": 100,
        "hourly_rate": 75.00,
    }


@pytest.fixture
def sample_team_member(sample_team_member_data, sample_project):
    """Instance membre d'équipe sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_team_member_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_risk_data():
    """Données de risque sample"""
    return {
        "title": "Risque technique",
        "description": "Risque lié à la complexité technique",
        "probability": 50,
        "impact": 8,
        "status": "IDENTIFIED",
        "mitigation_plan": "Plan de mitigation du risque",
    }


@pytest.fixture
def sample_risk(sample_risk_data, sample_project):
    """Instance risque sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_risk_data,
        "risk_score": 4.0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_issue_data():
    """Données de problème sample"""
    return {
        "title": "Problème de performance",
        "description": "Application lente au démarrage",
        "status": "OPEN",
        "priority": "HIGH",
        "severity": "MAJOR",
    }


@pytest.fixture
def sample_issue(sample_issue_data, sample_project):
    """Instance problème sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_issue_data,
        "resolution": None,
        "resolved_at": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_time_entry_data(user_id):
    """Données de saisie de temps sample"""
    return {
        "task_id": str(uuid4()),
        "user_id": user_id,
        "date": str(date.today()),
        "hours": 8.0,
        "description": "Travail sur la tâche",
        "billable": True,
    }


@pytest.fixture
def sample_time_entry(sample_time_entry_data, sample_project, sample_task):
    """Instance saisie de temps sample"""
    data = sample_time_entry_data.copy()
    data["task_id"] = sample_task["id"]

    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **data,
        "status": "DRAFT",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_expense_data():
    """Données de dépense sample"""
    return {
        "category": "TRAVEL",
        "amount": 150.50,
        "currency": "EUR",
        "date": str(date.today()),
        "description": "Déplacement client",
        "receipt_url": "https://example.com/receipt.pdf",
    }


@pytest.fixture
def sample_expense(sample_expense_data, sample_project, user_id):
    """Instance dépense sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        "user_id": user_id,
        **sample_expense_data,
        "status": "PENDING",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_document_data(user_id):
    """Données de document sample"""
    return {
        "name": "Cahier des charges.pdf",
        "description": "Cahier des charges du projet",
        "file_url": "https://example.com/documents/cdc.pdf",
        "file_size": 2048576,
        "mime_type": "application/pdf",
        "uploaded_by": user_id,
    }


@pytest.fixture
def sample_document(sample_document_data, sample_project):
    """Instance document sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_document_data,
        "version": 1,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_budget_data():
    """Données de budget sample"""
    return {
        "category": "LABOR",
        "planned_amount": 50000.00,
        "currency": "EUR",
        "period_start": str(date.today()),
        "period_end": str(date.today() + timedelta(days=90)),
    }


@pytest.fixture
def sample_budget(sample_budget_data, sample_project):
    """Instance budget sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_budget_data,
        "actual_amount": 0.00,
        "variance": 0.00,
        "is_approved": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_template_data():
    """Données de template sample"""
    return {
        "name": "Template Projet Standard",
        "description": "Template pour un projet standard",
        "category": "SOFTWARE_DEVELOPMENT",
        "is_active": True,
        "configuration": {
            "default_phases": [
                {"name": "Conception", "duration_days": 30},
                {"name": "Développement", "duration_days": 60},
            ],
        },
    }


@pytest.fixture
def sample_template(sample_template_data, tenant_id):
    """Instance template sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        **sample_template_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_comment_data(user_id):
    """Données de commentaire sample"""
    return {
        "content": "Ceci est un commentaire de test",
        "user_id": user_id,
        "entity_type": "PROJECT",
    }


@pytest.fixture
def sample_comment(sample_comment_data, sample_project):
    """Instance commentaire sample"""
    return {
        "id": str(uuid4()),
        "project_id": sample_project["id"],
        **sample_comment_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
