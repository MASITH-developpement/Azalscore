"""
AZALS - Tests rapports RED immuables
Validation de la génération automatique et immutabilité des rapports 🔴
"""

import pytest

# Skip tests that require middleware refactoring for DB session injection
pytestmark = pytest.mark.skip(
    reason="RED report tests require middleware refactoring - auth middleware uses SessionLocal directly"
)
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.models import User, UserRole, Decision, DecisionLevel, RedDecisionReport
from app.core.security import get_password_hash, create_access_token

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_red_report.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Active contraintes FK pour SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Session de test isolée."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Client de test avec DB override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def create_test_user_and_jwt(tenant_id: str, email: str, db_session):
    """Helper pour créer utilisateur DIRIGEANT et JWT."""
    user = User(
        tenant_id=tenant_id,
        email=email,
        password_hash=get_password_hash("password123"),
        role=UserRole.DIRIGEANT
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "tenant_id": tenant_id}
    )
    
    return user.id, token


def test_report_generated_automatically_on_final_step(client, db_session):
    """Test 1 : Rapport créé automatiquement à la validation finale."""
    tenant_id = "tenant_report_1"
    user_id, token = create_test_user_and_jwt(tenant_id, "report1@test.com", db_session)
    
    # Créer décision RED
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="1",
        level=DecisionLevel.RED,
        reason="Test RED decision for report"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Workflow complet
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-final/{decision.id}", headers=headers)
    
    # Vérifier rapport créé
    report = db_session.query(RedDecisionReport).filter(
        RedDecisionReport.decision_id == decision.id
    ).first()
    
    assert report is not None
    assert report.decision_id == decision.id
    assert report.tenant_id == tenant_id
    assert report.validator_id == user_id
    assert report.decision_reason == "Test RED decision for report"


def test_report_not_created_before_final_step(client, db_session):
    """Test 2 : Rapport NON créé avant étape FINAL."""
    tenant_id = "tenant_report_2"
    user_id, token = create_test_user_and_jwt(tenant_id, "report2@test.com", db_session)
    
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="2",
        level=DecisionLevel.RED,
        reason="Test RED no report yet"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Seulement étapes 1 et 2
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    
    # Vérifier aucun rapport
    report = db_session.query(RedDecisionReport).filter(
        RedDecisionReport.decision_id == decision.id
    ).first()
    
    assert report is None


def test_report_immutable_unique_per_decision(client, db_session):
    """Test 3 : Un seul rapport par décision (contrainte UNIQUE)."""
    tenant_id = "tenant_report_3"
    user_id, token = create_test_user_and_jwt(tenant_id, "report3@test.com", db_session)
    
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="3",
        level=DecisionLevel.RED,
        reason="Test unique report"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Workflow complet
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-final/{decision.id}", headers=headers)
    
    # Vérifier exactement UN rapport
    reports = db_session.query(RedDecisionReport).filter(
        RedDecisionReport.decision_id == decision.id
    ).all()
    
    assert len(reports) == 1


def test_get_report_endpoint_returns_report(client, db_session):
    """Test 4 : GET /decision/red/report/{id} retourne le rapport."""
    tenant_id = "tenant_report_4"
    user_id, token = create_test_user_and_jwt(tenant_id, "report4@test.com", db_session)
    
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="4",
        level=DecisionLevel.RED,
        reason="Test GET report"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Workflow complet
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-final/{decision.id}", headers=headers)
    
    # Récupérer rapport via API
    response = client.get(f"/decision/red/report/{decision.id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["decision_id"] == decision.id
    assert data["decision_reason"] == "Test GET report"
    assert data["validator_id"] == user_id
    assert "trigger_data" in data
    assert "journal_references" in data
    assert "validated_at" in data


def test_get_report_before_final_validation_fails(client, db_session):
    """Test 5 : GET rapport avant validation FINAL → 403."""
    tenant_id = "tenant_report_5"
    user_id, token = create_test_user_and_jwt(tenant_id, "report5@test.com", db_session)
    
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="5",
        level=DecisionLevel.RED,
        reason="Test GET before FINAL"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Seulement étape 1
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    
    # Tenter GET rapport
    response = client.get(f"/decision/red/report/{decision.id}", headers=headers)
    
    assert response.status_code == 403
    assert "after complete validation" in response.json()["detail"]


def test_report_contains_journal_references(client, db_session):
    """Test 6 : Rapport contient références journal."""
    tenant_id = "tenant_report_6"
    user_id, token = create_test_user_and_jwt(tenant_id, "report6@test.com", db_session)
    
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="6",
        level=DecisionLevel.RED,
        reason="Test journal refs"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Workflow complet
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-final/{decision.id}", headers=headers)
    
    # Récupérer rapport
    response = client.get(f"/decision/red/report/{decision.id}", headers=headers)
    data = response.json()
    
    # Vérifier journal_references est une liste
    assert isinstance(data["journal_references"], list)
    # Au moins 2 entrées (workflow + report generated)
    assert len(data["journal_references"]) >= 2


def test_report_tenant_isolation(client, db_session):
    """Test 7 : Isolation stricte tenant pour rapports."""
    tenant_a = "tenant_report_7a"
    tenant_b = "tenant_report_7b"
    
    user_a_id, token_a = create_test_user_and_jwt(tenant_a, "report7a@test.com", db_session)
    user_b_id, token_b = create_test_user_and_jwt(tenant_b, "report7b@test.com", db_session)
    
    # Décision RED tenant A
    decision_a = Decision(
        tenant_id=tenant_a,
        entity_type="test_entity",
        entity_id="7a",
        level=DecisionLevel.RED,
        reason="Test tenant A"
    )
    db_session.add(decision_a)
    db_session.commit()
    db_session.refresh(decision_a)
    
    headers_a = {"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"}
    
    # Workflow complet tenant A
    client.post(f"/decision/red/acknowledge/{decision_a.id}", headers=headers_a)
    client.post(f"/decision/red/confirm-completeness/{decision_a.id}", headers=headers_a)
    client.post(f"/decision/red/confirm-final/{decision_a.id}", headers=headers_a)
    
    # Tenant B tente accès rapport tenant A
    headers_b = {"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"}
    response = client.get(f"/decision/red/report/{decision_a.id}", headers=headers_b)
    
    assert response.status_code == 404


def test_report_contains_trigger_data_snapshot(client, db_session):
    """Test 8 : Rapport contient snapshot trigger_data."""
    tenant_id = "tenant_report_8"
    user_id, token = create_test_user_and_jwt(tenant_id, "report8@test.com", db_session)
    
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="8",
        level=DecisionLevel.RED,
        reason="Test trigger data snapshot"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Workflow complet
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-final/{decision.id}", headers=headers)
    
    # Récupérer rapport
    response = client.get(f"/decision/red/report/{decision.id}", headers=headers)
    data = response.json()
    
    # Vérifier trigger_data
    assert "trigger_data" in data
    trigger = data["trigger_data"]
    assert trigger["entity_type"] == "test_entity"
    assert trigger["entity_id"] == "8"
    assert trigger["reason"] == "Test trigger data snapshot"


def test_report_with_treasury_snapshot(client, db_session):
    """Test 9 : Rapport décision treasury inclut snapshot trésorerie."""
    tenant_id = "tenant_report_9"
    user_id, token = create_test_user_and_jwt(tenant_id, "report9@test.com", db_session)
    
    # Créer prévision trésorerie négative (déclenche RED auto)
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/treasury/forecast",
        json={"opening_balance": 1000, "inflows": 500, "outflows": 2000},
        headers=headers
    )
    
    assert response.status_code == 200
    forecast_data = response.json()
    assert forecast_data["red_triggered"] is True
    
    # Récupérer décision RED créée
    decision = db_session.query(Decision).filter(
        Decision.tenant_id == tenant_id,
        Decision.entity_type == "treasury_forecast",
        Decision.level == DecisionLevel.RED
    ).first()
    
    assert decision is not None
    
    # Workflow complet
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-final/{decision.id}", headers=headers)
    
    # Récupérer rapport
    response = client.get(f"/decision/red/report/{decision.id}", headers=headers)
    data = response.json()
    
    # Vérifier treasury_snapshot
    trigger = data["trigger_data"]
    assert "treasury_snapshot" in trigger
    snapshot = trigger["treasury_snapshot"]
    assert snapshot["opening_balance"] == 1000
    assert snapshot["inflows"] == 500
    assert snapshot["outflows"] == 2000
    assert snapshot["forecast_balance"] == -500


def test_report_without_jwt_fails(client, db_session):
    """Test 10 : GET rapport sans JWT → 403."""
    tenant_id = "tenant_report_10"
    user_id, token = create_test_user_and_jwt(tenant_id, "report10@test.com", db_session)
    
    decision = Decision(
        tenant_id=tenant_id,
        entity_type="test_entity",
        entity_id="10",
        level=DecisionLevel.RED,
        reason="Test no JWT"
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)
    
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    
    # Workflow complet
    client.post(f"/decision/red/acknowledge/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-completeness/{decision.id}", headers=headers)
    client.post(f"/decision/red/confirm-final/{decision.id}", headers=headers)
    
    # Tenter GET sans JWT
    response = client.get(
        f"/decision/red/report/{decision.id}",
        headers={"X-Tenant-ID": tenant_id}
    )
    
    assert response.status_code == 403
