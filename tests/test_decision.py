"""
AZALS - Tests du moteur de classification décisionnelle
Validation des règles d'irréversibilité RED
"""

import os
# Configuration test AVANT import app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_decision.db")
os.environ.setdefault("SECRET_KEY", "test-key-minimum-32-characters-long-for-tests")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.models import User, DecisionLevel, JournalEntry, Decision, Item
from app.core.security import get_password_hash, SECRET_KEY, ALGORITHM
from jose import jwt
from datetime import datetime, timedelta

# Base de données de test SQLite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_decision.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Crée les tables avant tous les tests du module, les supprime après.
    IMPORTANT: Import des modèles AVANT create_all pour que SQLAlchemy les connaisse.
    """
    # Force l'import de TOUS les modèles depuis app.core.models
    # Cela garantit que Base.metadata contient tous les schémas
    from app.core import models  # noqa: F401 - Import nécessaire pour enregistrer les modèles
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Fixture : client de test FastAPI avec override DB isolé."""
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
    """
    Crée un utilisateur de test et retourne (user_id, jwt_token).
    """
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
        "tenant_id": tenant_id,
        "role": "DIRIGEANT",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    db.close()
    return user.id, token


def test_classify_green_decision(client):
    """
    Test 1 : Création d'une décision GREEN autorisée.
    """
    tenant_id = "tenant_green"
    user_id, token = create_test_user_and_jwt(tenant_id, "green@test.com")
    
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "contract",
            "entity_id": "CTR-001",
            "level": "GREEN",
            "reason": "All checks passed"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "GREEN"
    assert data["entity_type"] == "contract"
    assert data["entity_id"] == "CTR-001"
    assert data["tenant_id"] == tenant_id


def test_classify_green_to_orange(client):
    """
    Test 2 : Passage GREEN → ORANGE autorisé.
    """
    tenant_id = "tenant_transition"
    user_id, token = create_test_user_and_jwt(tenant_id, "transition@test.com")
    
    # Création GREEN
    client.post(
        "/decision/classify",
        json={
            "entity_type": "invoice",
            "entity_id": "INV-001",
            "level": "GREEN",
            "reason": "Initial classification"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Passage à ORANGE
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "invoice",
            "entity_id": "INV-001",
            "level": "ORANGE",
            "reason": "Anomaly detected"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "ORANGE"


def test_classify_orange_to_red(client):
    """
    Test 3 : Passage ORANGE → RED autorisé.
    """
    tenant_id = "tenant_escalation"
    user_id, token = create_test_user_and_jwt(tenant_id, "escalation@test.com")
    
    # Création ORANGE
    client.post(
        "/decision/classify",
        json={
            "entity_type": "payment",
            "entity_id": "PAY-001",
            "level": "ORANGE",
            "reason": "Suspicious pattern"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Escalade vers RED
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "payment",
            "entity_id": "PAY-001",
            "level": "RED",
            "reason": "Fraud confirmed"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "RED"


def test_red_is_irreversible_to_orange(client):
    """
    Test 4 : Passage RED → ORANGE IMPOSSIBLE (403).
    """
    tenant_id = "tenant_red_lock"
    user_id, token = create_test_user_and_jwt(tenant_id, "redlock@test.com")
    
    # Création RED directe
    client.post(
        "/decision/classify",
        json={
            "entity_type": "document",
            "entity_id": "DOC-001",
            "level": "RED",
            "reason": "Critical violation"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Tentative de rétrogradation vers ORANGE
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "document",
            "entity_id": "DOC-001",
            "level": "ORANGE",
            "reason": "Trying to downgrade"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 403
    assert "IRREVERSIBLE" in response.json()["detail"]


def test_red_is_irreversible_to_green(client):
    """
    Test 5 : Passage RED → GREEN IMPOSSIBLE (403).
    """
    tenant_id = "tenant_red_final"
    user_id, token = create_test_user_and_jwt(tenant_id, "redfinal@test.com")
    
    # Création RED
    client.post(
        "/decision/classify",
        json={
            "entity_type": "account",
            "entity_id": "ACC-001",
            "level": "RED",
            "reason": "Blocked permanently"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Tentative de rétrogradation vers GREEN
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "account",
            "entity_id": "ACC-001",
            "level": "GREEN",
            "reason": "Trying to clear"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 403
    assert "IRREVERSIBLE" in response.json()["detail"]


def test_red_decision_is_journalized(client):
    """
    Test 6 : Toute décision RED est journalisée automatiquement.
    """
    tenant_id = "tenant_journal_red"
    user_id, token = create_test_user_and_jwt(tenant_id, "journalred@test.com")
    
    # Création RED
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "transaction",
            "entity_id": "TRX-001",
            "level": "RED",
            "reason": "High risk transaction"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    
    # Vérification dans le journal
    db = TestingSessionLocal()
    journal_entries = db.query(JournalEntry).filter(
        JournalEntry.tenant_id == tenant_id,
        JournalEntry.action == "DECISION_RED"
    ).all()
    
    assert len(journal_entries) == 1
    assert "transaction:TRX-001" in journal_entries[0].details
    assert "High risk transaction" in journal_entries[0].details
    
    db.close()


def test_get_decision_status(client):
    """
    Test 7 : Récupération du statut décisionnel actuel.
    """
    tenant_id = "tenant_status"
    user_id, token = create_test_user_and_jwt(tenant_id, "status@test.com")
    
    # Création ORANGE
    client.post(
        "/decision/classify",
        json={
            "entity_type": "client",
            "entity_id": "CLI-001",
            "level": "ORANGE",
            "reason": "Late payment"
        },
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Récupération du statut
    response = client.get(
        "/decision/status/client/CLI-001",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "ORANGE"
    assert data["is_red"] is False


def test_get_decision_status_for_nonexistent_entity(client):
    """
    Test 8 : Statut d'une entité sans décision.
    """
    tenant_id = "tenant_empty"
    user_id, token = create_test_user_and_jwt(tenant_id, "empty@test.com")
    
    response = client.get(
        "/decision/status/contract/CTR-999",
        headers={
            "X-Tenant-ID": tenant_id,
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] is None
    assert data["is_red"] is False


def test_decision_without_jwt_fails(client):
    """
    Test 9 : Classification sans JWT échoue (403 car pas de Bearer token).
    """
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "test",
            "entity_id": "TST-001",
            "level": "GREEN",
            "reason": "Test"
        },
        headers={
            "X-Tenant-ID": "tenant_test"
        }
    )
    
    assert response.status_code == 403


def test_decision_tenant_isolation(client):
    """
    Test 10 : Isolation stricte entre tenants.
    """
    tenant_a = "tenant_a"
    tenant_b = "tenant_b"
    
    user_a_id, token_a = create_test_user_and_jwt(tenant_a, "usera@test.com")
    user_b_id, token_b = create_test_user_and_jwt(tenant_b, "userb@test.com")
    
    # Tenant A crée une décision RED
    client.post(
        "/decision/classify",
        json={
            "entity_type": "shared",
            "entity_id": "SHARED-001",
            "level": "RED",
            "reason": "Tenant A blocks this"
        },
        headers={
            "X-Tenant-ID": tenant_a,
            "Authorization": f"Bearer {token_a}"
        }
    )
    
    # Tenant B peut créer sa propre décision GREEN sur la même entity_id
    response = client.post(
        "/decision/classify",
        json={
            "entity_type": "shared",
            "entity_id": "SHARED-001",
            "level": "GREEN",
            "reason": "Tenant B has no issue"
        },
        headers={
            "X-Tenant-ID": tenant_b,
            "Authorization": f"Bearer {token_b}"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "GREEN"
    assert data["tenant_id"] == tenant_b
