"""
AZALS - Tests workflow de validation RED
Validation stricte des 3 étapes obligatoires pour décisions RED
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.models import User, Decision, DecisionLevel, RedDecisionWorkflow
from app.core.security import get_password_hash, SECRET_KEY, ALGORITHM
from jose import jwt
from datetime import datetime, timedelta


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_red_workflow.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Crée les tables avant les tests."""
    from app.core import models
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Client de test avec override DB."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def create_test_user_and_jwt(tenant_id: str, email: str) -> tuple[int, str]:
    """Crée un utilisateur DIRIGEANT et retourne (user_id, jwt_token)."""
    db = TestingSessionLocal()
    user = User(
        tenant_id=tenant_id,
        email=email,
        password_hash=get_password_hash("password123"),
        role="DIRIGEANT",
        is_active=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": tenant_id,
        "email": user.email,
        "role": user.role.value,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    db.close()
    
    return user.id, token


def create_red_decision(tenant_id: str, entity_type: str, entity_id: str) -> int:
    """Crée une décision RED et retourne son ID."""
    db = TestingSessionLocal()
    decision = Decision(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        level=DecisionLevel.RED,
        reason="Critical violation detected"
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    decision_id = decision.id
    db.close()
    return decision_id


def test_workflow_step_1_acknowledge_success(client):
    """Test 1 : Validation étape 1 ACKNOWLEDGE réussie."""
    tenant_id = "tenant_wf1"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf1@test.com")
    decision_id = create_red_decision(tenant_id, "contract", "CTR-WF1")
    
    response = client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["step"] == "ACKNOWLEDGE"
    assert data["decision_id"] == decision_id
    assert "acknowledged" in data["message"].lower()


def test_workflow_step_2_without_step_1_fails(client):
    """Test 2 : Étape 2 COMPLETENESS sans étape 1 échoue."""
    tenant_id = "tenant_wf2"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf2@test.com")
    decision_id = create_red_decision(tenant_id, "payment", "PAY-WF2")
    
    response = client.post(
        f"/decision/red/confirm-completeness/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 400
    assert "INVALID_ORDER" in response.json()["detail"]
    assert "ACKNOWLEDGE" in response.json()["detail"]


def test_workflow_step_3_without_step_2_fails(client):
    """Test 3 : Étape 3 FINAL sans étape 2 échoue."""
    tenant_id = "tenant_wf3"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf3@test.com")
    decision_id = create_red_decision(tenant_id, "invoice", "INV-WF3")
    
    # Étape 1 OK
    client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Étape 3 sans étape 2 → échec
    response = client.post(
        f"/decision/red/confirm-final/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 400
    assert "INVALID_ORDER" in response.json()["detail"]
    assert "COMPLETENESS" in response.json()["detail"]


def test_workflow_complete_sequence_success(client):
    """Test 4 : Séquence complète des 3 étapes réussit."""
    tenant_id = "tenant_wf4"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf4@test.com")
    decision_id = create_red_decision(tenant_id, "account", "ACC-WF4")
    
    # Étape 1
    r1 = client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    assert r1.status_code == 200
    
    # Étape 2
    r2 = client.post(
        f"/decision/red/confirm-completeness/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    assert r2.status_code == 200
    
    # Étape 3
    r3 = client.post(
        f"/decision/red/confirm-final/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    assert r3.status_code == 200
    assert "complete" in r3.json()["message"].lower()


def test_workflow_duplicate_step_fails(client):
    """Test 5 : Double validation d'une même étape échoue."""
    tenant_id = "tenant_wf5"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf5@test.com")
    decision_id = create_red_decision(tenant_id, "transaction", "TRX-WF5")
    
    # Étape 1 - première fois OK
    r1 = client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    assert r1.status_code == 200
    
    # Étape 1 - deuxième fois KO
    r2 = client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    assert r2.status_code == 409
    assert "DUPLICATE" in r2.json()["detail"]


def test_workflow_status_endpoint(client):
    """Test 6 : Endpoint status retourne l'état du workflow."""
    tenant_id = "tenant_wf6"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf6@test.com")
    decision_id = create_red_decision(tenant_id, "document", "DOC-WF6")
    
    # Avant validation
    r1 = client.get(
        f"/decision/red/status/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    assert r1.status_code == 200
    assert r1.json()["is_fully_validated"] is False
    assert len(r1.json()["pending_steps"]) == 3
    
    # Après étape 1
    client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    r2 = client.get(
        f"/decision/red/status/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    assert r2.status_code == 200
    assert len(r2.json()["completed_steps"]) == 1
    assert "ACKNOWLEDGE" in r2.json()["completed_steps"]
    assert r2.json()["is_fully_validated"] is False


def test_workflow_fully_validated_status(client):
    """Test 7 : Status is_fully_validated à true après les 3 étapes."""
    tenant_id = "tenant_wf7"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf7@test.com")
    decision_id = create_red_decision(tenant_id, "client", "CLI-WF7")
    
    # Compléter les 3 étapes
    client.post(f"/decision/red/acknowledge/{decision_id}",
                headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    client.post(f"/decision/red/confirm-completeness/{decision_id}",
                headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    client.post(f"/decision/red/confirm-final/{decision_id}",
                headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    
    # Vérifier status
    response = client.get(
        f"/decision/red/status/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_fully_validated"] is True
    assert len(data["completed_steps"]) == 3
    assert len(data["pending_steps"]) == 0


def test_workflow_journal_traceability(client):
    """Test 8 : Chaque étape est tracée dans le journal."""
    tenant_id = "tenant_wf8"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf8@test.com")
    decision_id = create_red_decision(tenant_id, "supplier", "SUP-WF8")
    
    # Valider étape 1
    client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Vérifier journal
    db = TestingSessionLocal()
    from app.core.models import JournalEntry
    entries = db.query(JournalEntry).filter(
        JournalEntry.tenant_id == tenant_id,
        JournalEntry.action.like("RED_WORKFLOW_%")
    ).all()
    
    assert len(entries) >= 1
    assert "ACKNOWLEDGE" in entries[0].action
    assert str(decision_id) in entries[0].details
    db.close()


def test_workflow_non_red_decision_fails(client):
    """Test 9 : Workflow sur décision non-RED échoue."""
    tenant_id = "tenant_wf9"
    user_id, token = create_test_user_and_jwt(tenant_id, "wf9@test.com")
    
    # Créer décision GREEN
    db = TestingSessionLocal()
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test",
        entity_id="TEST-WF9",
        level=DecisionLevel.GREEN,
        reason="Normal operation"
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    decision_id = decision.id
    db.close()
    
    # Tenter workflow sur GREEN
    response = client.post(
        f"/decision/red/acknowledge/{decision_id}",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 400
    assert "Only RED decisions" in response.json()["detail"]


def test_workflow_tenant_isolation(client):
    """Test 10 : Isolation stricte entre tenants."""
    tenant_a = "tenant_wf_a"
    tenant_b = "tenant_wf_b"
    
    user_a_id, token_a = create_test_user_and_jwt(tenant_a, "wfa@test.com")
    user_b_id, token_b = create_test_user_and_jwt(tenant_b, "wfb@test.com")
    
    decision_a = create_red_decision(tenant_a, "order", "ORD-A")
    
    # Tenant A valide étape 1
    r1 = client.post(
        f"/decision/red/acknowledge/{decision_a}",
        headers={
            "X-Tenant-ID": tenant_a,
            "Authorization": f"Bearer {token_a}"
        }
    )
    assert r1.status_code == 200
    
    # Tenant B ne peut pas voir la décision de A
    r2 = client.get(
        f"/decision/red/status/{decision_a}",
        headers={
            "X-Tenant-ID": tenant_b,
            "Authorization": f"Bearer {token_b}"
        }
    )
    assert r2.status_code == 404
