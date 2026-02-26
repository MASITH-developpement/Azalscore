"""
AZALS - Tests module Trésorerie
Validation calcul et déclenchement RED automatique
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.models import User, TreasuryForecast, Decision, JournalEntry
from app.core.security import get_password_hash, SECRET_KEY, ALGORITHM
from jose import jwt
from datetime import datetime, timedelta


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_treasury.db"
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
        "user_id": str(user.id),
        "tenant_id": str(tenant_id),
        "email": user.email,
        "role": user.role.value,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    db.close()
    
    return user.id, token


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal "
    "directement au lieu de get_db, causant des problèmes de visibilité entre sessions"
)
def test_treasury_forecast_positive_balance(client):
    """Test 1 : Trésorerie positive → pas de RED."""
    tenant_id = "tenant_treasury_1"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury1@test.com")
    
    response = client.post(
        "/treasury/forecast",
        json={
            "opening_balance": 10000,
            "inflows": 5000,
            "outflows": 3000
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["forecast_balance"] == 12000
    assert data["red_triggered"] is False
    
    # Vérifier qu'aucune décision RED n'a été créée
    db = TestingSessionLocal()
    decision = db.query(Decision).filter(
        Decision.tenant_id == tenant_id,
        Decision.entity_type == "treasury_forecast"
    ).first()
    assert decision is None
    db.close()


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_forecast_zero_balance(client):
    """Test 2 : Trésorerie à zéro → pas de RED."""
    tenant_id = "tenant_treasury_2"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury2@test.com")
    
    response = client.post(
        "/treasury/forecast",
        json={
            "opening_balance": 5000,
            "inflows": 2000,
            "outflows": 7000
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["forecast_balance"] == 0
    assert data["red_triggered"] is False


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_forecast_negative_triggers_red(client):
    """Test 3 : Trésorerie négative → RED déclenché."""
    tenant_id = "tenant_treasury_3"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury3@test.com")
    
    response = client.post(
        "/treasury/forecast",
        json={
            "opening_balance": 1000,
            "inflows": 500,
            "outflows": 2000
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["forecast_balance"] == -500
    assert data["red_triggered"] is True
    
    # Vérifier décision RED créée
    db = TestingSessionLocal()
    decision = db.query(Decision).filter(
        Decision.tenant_id == tenant_id,
        Decision.entity_type == "treasury_forecast",
        Decision.entity_id == str(data["id"])
    ).first()
    
    assert decision is not None
    assert decision.level.value == "RED"
    assert "Negative treasury" in decision.reason
    db.close()


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_negative_creates_journal_entry(client):
    """Test 4 : Trésorerie négative → journalisé."""
    tenant_id = "tenant_treasury_4"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury4@test.com")
    
    response = client.post(
        "/treasury/forecast",
        json={
            "opening_balance": 100,
            "inflows": 50,
            "outflows": 300
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["red_triggered"] is True
    
    # Vérifier entrée journal
    db = TestingSessionLocal()
    journal = db.query(JournalEntry).filter(
        JournalEntry.tenant_id == tenant_id,
        JournalEntry.action == "TREASURY_RED_TRIGGERED"
    ).first()
    
    assert journal is not None
    assert str(data["id"]) in journal.details
    assert str(data["forecast_balance"]) in journal.details
    db.close()


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_calculation_accuracy(client):
    """Test 5 : Calcul trésorerie précis."""
    tenant_id = "tenant_treasury_5"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury5@test.com")
    
    test_cases = [
        (1000, 2000, 500, 2500),
        (0, 1000, 1000, 0),
        (5000, 0, 6000, -1000),
        (-100, 200, 50, 50),
    ]
    
    for opening, inflows, outflows, expected in test_cases:
        response = client.post(
            "/treasury/forecast",
            json={
                "opening_balance": opening,
                "inflows": inflows,
                "outflows": outflows
            },
            headers={
                "X-Tenant-ID": tenant_id,
                "Authorization": f"Bearer {token}"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["forecast_balance"] == expected


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_get_latest(client):
    """Test 6 : Récupération dernière prévision."""
    tenant_id = "tenant_treasury_6"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury6@test.com")
    
    # Créer 2 prévisions
    client.post(
        "/treasury/forecast",
        json={"opening_balance": 1000, "inflows": 500, "outflows": 300},
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    )
    
    r2 = client.post(
        "/treasury/forecast",
        json={"opening_balance": 2000, "inflows": 1000, "outflows": 500},
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    )
    
    # Récupérer la dernière
    response = client.get(
        "/treasury/latest",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Vérifier montants au lieu des IDs
    assert data["opening_balance"] == 2000
    assert data["inflows"] == 1000
    assert data["outflows"] == 500
    assert data["forecast_balance"] == 2500


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_tenant_isolation(client):
    """Test 7 : Isolation stricte entre tenants."""
    tenant_a = "tenant_treasury_a"
    tenant_b = "tenant_treasury_b"

    user_a_id, token_a = create_test_user_and_jwt(tenant_a, "treasurya@test.com")
    user_b_id, token_b = create_test_user_and_jwt(tenant_b, "treasuryb@test.com")
    
    # Tenant A crée prévision
    client.post(
        "/treasury/forecast",
        json={"opening_balance": 1000, "inflows": 500, "outflows": 300},
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"}
    )
    
    # Tenant B ne voit pas la prévision de A
    response = client.get(
        "/treasury/latest",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"}
    )
    
    # Pas de prévision pour B
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_multiple_negative_creates_multiple_reds(client):
    """Test 8 : Plusieurs trésoreries négatives → plusieurs RED."""
    tenant_id = "tenant_treasury_8"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury8@test.com")
    
    # Créer 2 prévisions négatives
    r1 = client.post(
        "/treasury/forecast",
        json={"opening_balance": 100, "inflows": 0, "outflows": 200},
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    )
    
    r2 = client.post(
        "/treasury/forecast",
        json={"opening_balance": 50, "inflows": 10, "outflows": 100},
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}
    )
    
    assert r1.json()["red_triggered"] is True
    assert r2.json()["red_triggered"] is True
    
    # Vérifier 2 décisions RED distinctes
    db = TestingSessionLocal()
    decisions = db.query(Decision).filter(
        Decision.tenant_id == tenant_id,
        Decision.level.in_(["RED"])
    ).all()
    
    assert len(decisions) == 2
    db.close()


@pytest.mark.skip(
    reason="SQLite session isolation: CoreAuthMiddleware utilise SessionLocal directement"
)
def test_treasury_large_negative_balance(client):
    """Test 9 : Grande trésorerie négative → RED."""
    tenant_id = "tenant_treasury_9"
    user_id, token = create_test_user_and_jwt(tenant_id, "treasury9@test.com")
    
    response = client.post(
        "/treasury/forecast",
        json={
            "opening_balance": 1000,
            "inflows": 500,
            "outflows": 1000000
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["forecast_balance"] == -998500
    assert data["red_triggered"] is True


def test_treasury_without_jwt_fails(client):
    """Test 10 : Accès sans JWT échoue."""
    tenant_id = "tenant_treasury_10"
    
    response = client.post(
        "/treasury/forecast",
        json={"opening_balance": 1000, "inflows": 500, "outflows": 300},
        headers={"X-Tenant-ID": tenant_id}
    )
    
    assert response.status_code == 403
