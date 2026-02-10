"""Configuration pytest et fixtures pour les tests AI Assistant."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.core.saas_context import SaaSContext, UserRole


@pytest.fixture
def client(mock_db, mock_saas_context, mock_ai_service):
    """Test client with all mocks applied."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def tenant_id():
    return "tenant-test-001"


@pytest.fixture
def user_id():
    return "user-test-001"


@pytest.fixture(autouse=True)
def mock_db():
    """Mock database session."""
    class MockDB:
        def query(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

        def all(self):
            return []

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    mock_session = MockDB()

    from app.core.database import get_db
    from app.main import app

    def mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db

    yield mock_session

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def mock_saas_context(tenant_id, user_id):
    """Mock SaaSContext using FastAPI dependency_overrides."""
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"ai.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    from app.core.dependencies_v2 import get_saas_context
    from app.main import app

    # Use FastAPI's dependency_overrides instead of monkeypatching
    app.dependency_overrides[get_saas_context] = mock_get_context

    yield mock_get_context

    # Cleanup: remove the override after the test
    app.dependency_overrides.pop(get_saas_context, None)


@pytest.fixture(autouse=True)
def mock_ai_service(tenant_id, user_id):
    """Mock du service AI Assistant using dependency_overrides."""

    class MockAIService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = user_id

        # Configuration
        def get_config(self):
            return {
                "id": 1,
                "tenant_id": self.tenant_id,
                "is_enabled": True,
                "enabled_features": ["question", "analysis", "risk_detection"],
                "daily_request_limit": 1000,
                "response_language": "fr"
            }

        def update_config(self, user_id, data):
            return {**self.get_config(), **data.model_dump(exclude_unset=True)}

        def is_feature_enabled(self, feature):
            return True

        # Conversations
        def create_conversation(self, user_id, data):
            return {
                "id": 1,
                "tenant_id": self.tenant_id,
                "user_id": user_id,
                "title": data.title or "New Conversation",
                "context": data.context,
                "module_source": data.module_source,
                "is_active": True,
                "message_count": 0
            }

        def get_conversation(self, conversation_id):
            return {
                "id": conversation_id,
                "title": "Test Conversation",
                "message_count": 5
            }

        def list_conversations(self, user_id, active_only=True, skip=0, limit=50):
            return [
                {"id": 1, "title": "Conversation 1", "is_active": True},
                {"id": 2, "title": "Conversation 2", "is_active": True}
            ]

        def add_message(self, conversation_id, user_id, data):
            user_message = {
                "id": 1,
                "conversation_id": conversation_id,
                "role": "user",
                "content": data.content,
                "request_type": data.request_type
            }
            assistant_message = {
                "id": 2,
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": "AI response to your question",
                "processing_time_ms": 150
            }
            return user_message, assistant_message

        # Analyses
        def create_analysis(self, user_id, data):
            return {
                "id": 1,
                "analysis_code": "ANA-20240101-ABC123",
                "title": data.title,
                "analysis_type": data.analysis_type,
                "status": "processing",
                "user_id": user_id
            }

        def get_analysis(self, analysis_id):
            return {
                "id": analysis_id,
                "analysis_code": "ANA-20240101-ABC123",
                "status": "completed",
                "findings": [],
                "recommendations": []
            }

        def list_analyses(self, user_id=None, analysis_type=None, skip=0, limit=50):
            return [
                {"id": 1, "title": "Analysis 1", "status": "completed"},
                {"id": 2, "title": "Analysis 2", "status": "processing"}
            ]

        # Decision Support
        def create_decision_support(self, user_id, data):
            return {
                "id": 1,
                "decision_code": "DEC-20240101-XYZ789",
                "title": data.title,
                "decision_type": data.decision_type,
                "is_red_point": False,
                "status": "pending_review",
                "options": []
            }

        def get_decision(self, decision_id):
            return {
                "id": decision_id,
                "decision_code": "DEC-20240101-XYZ789",
                "status": "pending_review"
            }

        def list_pending_decisions(self, skip=0, limit=50):
            return [
                {"id": 1, "title": "Decision 1", "status": "pending_review"},
                {"id": 2, "title": "Decision 2", "status": "pending_confirmation"}
            ]

        def confirm_decision(self, decision_id, user_id, data):
            return {
                "id": decision_id,
                "status": "confirmed",
                "decided_by_id": user_id,
                "decision_made": data.decision_made
            }

        def reject_decision(self, decision_id, user_id, reason):
            return {
                "id": decision_id,
                "status": "rejected",
                "decided_by_id": user_id,
                "decision_notes": f"REJETÉ: {reason}"
            }

        # Risk Detection
        def create_risk_alert(self, data):
            return {
                "id": 1,
                "alert_code": "RISK-20240101-DEF456",
                "title": data.title,
                "category": data.category,
                "risk_level": data.risk_level,
                "status": "active"
            }

        def get_risk_alert(self, alert_id):
            return {
                "id": alert_id,
                "alert_code": "RISK-20240101-DEF456",
                "status": "active"
            }

        def list_active_risks(self, category=None, level=None, skip=0, limit=50):
            return [
                {"id": 1, "title": "Risk 1", "risk_level": "high"},
                {"id": 2, "title": "Risk 2", "risk_level": "medium"}
            ]

        def acknowledge_risk(self, alert_id, user_id, data):
            return {
                "id": alert_id,
                "status": "acknowledged",
                "acknowledged_by": user_id
            }

        def resolve_risk(self, alert_id, user_id, data):
            return {
                "id": alert_id,
                "status": "resolved",
                "resolved_by": user_id,
                "resolution_notes": data.resolution_notes
            }

        # Predictions
        def create_prediction(self, user_id, data):
            return {
                "id": 1,
                "prediction_code": "PRED-20240101-GHI789",
                "title": data.title,
                "prediction_type": data.prediction_type,
                "status": "processing"
            }

        def get_prediction(self, prediction_id):
            return {
                "id": prediction_id,
                "prediction_code": "PRED-20240101-GHI789",
                "status": "active"
            }

        def list_predictions(self, prediction_type=None, skip=0, limit=50):
            return [
                {"id": 1, "title": "Prediction 1", "status": "active"},
                {"id": 2, "title": "Prediction 2", "status": "expired"}
            ]

        # Feedback
        def add_feedback(self, user_id, data):
            return {
                "id": 1,
                "user_id": user_id,
                "reference_type": data.reference_type,
                "reference_id": data.reference_id,
                "rating": data.rating,
                "is_helpful": data.is_helpful
            }

        # Synthesis
        def generate_synthesis(self, user_id, data):
            return {
                "title": data.title,
                "synthesis_type": data.synthesis_type,
                "executive_summary": "Executive summary here",
                "key_metrics": {},
                "highlights": [],
                "concerns": [],
                "action_items": []
            }

        # Statistics & Health
        def get_stats(self):
            return {
                "total_conversations": 150,
                "total_messages": 2500,
                "total_analyses": 45,
                "pending_decisions": 5,
                "active_risks": 12,
                "critical_risks": 2,
                "requests_today": 87,
                "avg_response_time_ms": 250.5,
                "avg_satisfaction_rating": 4.2
            }

        def health_check(self):
            return {
                "status": "healthy",
                "response_time_ms": 50,
                "features_status": {
                    "configuration": "healthy",
                    "database": "healthy",
                    "nlp_engine": "healthy"
                }
            }

        # Audit
        def get_audit_logs(self, action=None, user_id=None, skip=0, limit=100):
            return [
                {"id": 1, "action": "conversation_create", "user_id": user_id},
                {"id": 2, "action": "analysis_create", "user_id": user_id}
            ]

    # Create factory function
    def mock_get_service(db, tenant_id, user_id):
        return MockAIService(db, tenant_id, user_id)

    # Override via module-level assignment (before test runs)
    from app.modules.ai_assistant import router_v2
    original_get_service = router_v2.get_ai_service
    router_v2.get_ai_service = mock_get_service

    yield MockAIService(None, tenant_id, user_id)

    # Restore original after test
    router_v2.get_ai_service = original_get_service


# Fixtures de données
@pytest.fixture
def sample_conversation_data():
    return {
        "title": "Test Conversation",
        "context": {"module": "test"},
        "module_source": "test_module"
    }


@pytest.fixture
def sample_message_data():
    return {
        "content": "What is the current status?",
        "request_type": "question",
        "context": {"urgency": "normal"}
    }


@pytest.fixture
def sample_analysis_data():
    return {
        "title": "Test Analysis",
        "description": "Analyzing test data",
        "analysis_type": "360",
        "module_source": "finance",
        "entity_type": "customer",
        "entity_id": "123"
    }


@pytest.fixture
def sample_decision_data():
    return {
        "title": "Important Decision",
        "description": "Decision description",
        "decision_type": "strategic",
        "module_source": "hr",
        "priority": "high"
    }


@pytest.fixture
def sample_risk_data():
    return {
        "title": "Financial Risk",
        "description": "Risk description",
        "category": "financial",
        "subcategory": "liquidity",
        "risk_level": "high",
        "probability": 0.7,
        "impact_score": 8,
        "detection_source": "automated"
    }


@pytest.fixture
def sample_prediction_data():
    return {
        "title": "Revenue Prediction",
        "prediction_type": "financial",
        "target_metric": "revenue",
        "module_source": "finance",
        "prediction_start": datetime.utcnow().date(),
        "prediction_end": (datetime.utcnow() + timedelta(days=30)).date(),
        "granularity": "daily"
    }


@pytest.fixture
def sample_feedback_data():
    return {
        "reference_type": "message",
        "reference_id": 123,
        "rating": 5,
        "is_helpful": True,
        "is_accurate": True,
        "feedback_text": "Very helpful response"
    }


@pytest.fixture
def sample_synthesis_data():
    return {
        "title": "Monthly Synthesis",
        "synthesis_type": "monthly",
        "modules": ["finance", "commercial"],
        "period_start": datetime.utcnow().date(),
        "period_end": datetime.utcnow().date()
    }
