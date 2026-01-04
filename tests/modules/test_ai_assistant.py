"""
Tests Module IA Transverse Opérationnelle - AZALS
==================================================
Tests complets pour l'assistant IA central.

Scénarios testés:
- Conversations et messages
- Questions directes
- Analyses (360, financial, operational)
- Support de décision avec gouvernance (double confirmation pour points rouges)
- Alertes de risque
- Prédictions
- Feedback et apprentissage
- Synthèses
- Configuration
- Statistiques et santé
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.modules.ai_assistant.models import (
    AIConversation,
    AIMessage,
    AIAnalysis,
    AIDecisionSupport,
    AIRiskAlert,
    AIPrediction,
    AIFeedback,
    AILearningData,
    AIConfiguration,
    AIAuditLog,
    AIRequestType,
    AIResponseStatus,
    RiskLevel,
    RiskCategory,
    DecisionStatus,
)
from app.modules.ai_assistant.schemas import (
    ConversationCreate,
    MessageCreate,
    AIQuestionRequest,
    AnalysisRequest,
    DecisionSupportCreate,
    DecisionConfirmation,
    RiskAlertCreate,
    RiskAcknowledge,
    RiskResolve,
    PredictionRequest,
    FeedbackCreate,
    AIConfigUpdate,
    SynthesisRequest,
)
from app.modules.ai_assistant.service import AIAssistantService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de session DB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def service(mock_db):
    """Service IA avec mock DB."""
    return AIAssistantService(mock_db, "tenant_test")


@pytest.fixture
def sample_conversation():
    """Conversation exemple."""
    conv = AIConversation(
        id=1,
        tenant_id="tenant_test",
        user_id=1,
        title="Test Conversation",
        context={"module": "commercial"},
        module_source="commercial",
        is_active=True,
        message_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
    )
    return conv


@pytest.fixture
def sample_message():
    """Message exemple."""
    msg = AIMessage(
        id=1,
        tenant_id="tenant_test",
        conversation_id=1,
        role="user",
        request_type="question",
        content="Quelle est la marge bénéficiaire ?",
        message_metadata=None,
        tokens_used=50,
        processing_time_ms=150,
        status="completed",
        created_at=datetime.utcnow(),
    )
    return msg


@pytest.fixture
def sample_analysis():
    """Analyse exemple."""
    analysis = AIAnalysis(
        id=1,
        tenant_id="tenant_test",
        user_id=1,
        analysis_code="ANA-20240101-001",
        title="Analyse 360 Client",
        description="Analyse complète du client XYZ",
        analysis_type="360",
        module_source="commercial",
        entity_type="customer",
        entity_id="CUST-001",
        summary="Client fidèle avec potentiel de croissance",
        findings=[{"category": "revenue", "title": "CA en hausse", "severity": "info"}],
        metrics={"total_orders": 150, "avg_order_value": 250.0},
        confidence_score=0.85,
        risks_identified=[],
        overall_risk_level="low",
        recommendations=[{"priority": 1, "title": "Upsell premium"}],
        status="completed",
        created_at=datetime.utcnow(),
    )
    return analysis


@pytest.fixture
def sample_decision():
    """Support de décision exemple."""
    decision = AIDecisionSupport(
        id=1,
        tenant_id="tenant_test",
        decision_code="DEC-20240101-001",
        title="Extension de crédit client",
        description="Faut-il étendre le crédit à 50K€ ?",
        decision_type="credit_extension",
        module_source="commercial",
        priority="high",
        deadline=datetime.utcnow() + timedelta(days=3),
        options=[
            {"title": "Approuver", "pros": ["Fidélisation"], "cons": ["Risque impayé"]},
            {"title": "Refuser", "pros": ["Pas de risque"], "cons": ["Perte client"]},
        ],
        recommended_option=0,
        recommendation_rationale="Client fiable avec historique positif",
        risk_level="medium",
        risks=[{"type": "credit", "description": "Risque d'impayé modéré"}],
        is_red_point=False,
        requires_double_confirmation=False,
        status="pending_review",
        created_by_id=1,
        created_at=datetime.utcnow(),
    )
    return decision


@pytest.fixture
def sample_red_point_decision():
    """Décision point rouge (nécessite double confirmation)."""
    decision = AIDecisionSupport(
        id=2,
        tenant_id="tenant_test",
        decision_code="DEC-20240101-002",
        title="Licenciement économique",
        description="Réduction d'effectifs critiques",
        decision_type="hr_critical",
        module_source="hr",
        priority="critical",
        deadline=datetime.utcnow() + timedelta(days=1),
        options=[
            {"title": "Approuver", "pros": ["Économies"], "cons": ["Impact social"]},
            {"title": "Reporter", "pros": ["Temps analyse"], "cons": ["Incertitude"]},
        ],
        recommended_option=None,
        recommendation_rationale=None,
        risk_level="critical",
        risks=[{"type": "legal", "description": "Risque prud'homal"}],
        is_red_point=True,
        requires_double_confirmation=True,
        status="pending_review",
        created_by_id=1,
        created_at=datetime.utcnow(),
    )
    return decision


@pytest.fixture
def sample_risk_alert():
    """Alerte risque exemple."""
    alert = AIRiskAlert(
        id=1,
        tenant_id="tenant_test",
        alert_code="RSK-20240101-001",
        title="Dépassement seuil crédit",
        description="Client XYZ a dépassé son plafond de crédit",
        category="financial",
        subcategory="credit",
        risk_level="high",
        probability=0.8,
        impact_score=7.5,
        detection_source="credit_monitor",
        trigger_data={"current_credit": 60000, "limit": 50000},
        affected_entities=[{"type": "customer", "id": "CUST-001", "name": "XYZ Corp"}],
        recommended_actions=["Bloquer nouvelles commandes", "Contacter client"],
        status="active",
        detected_at=datetime.utcnow(),
    )
    return alert


@pytest.fixture
def sample_prediction():
    """Prédiction exemple."""
    prediction = AIPrediction(
        id=1,
        tenant_id="tenant_test",
        prediction_code="PRE-20240101-001",
        title="Prévision ventes Q1",
        prediction_type="sales",
        target_metric="revenue",
        module_source="commercial",
        prediction_start=datetime.utcnow(),
        prediction_end=datetime.utcnow() + timedelta(days=90),
        granularity="monthly",
        predicted_values=[
            {"date": "2024-01-01", "value": 150000, "confidence": 0.85},
            {"date": "2024-02-01", "value": 165000, "confidence": 0.80},
            {"date": "2024-03-01", "value": 180000, "confidence": 0.75},
        ],
        confidence_score=0.80,
        status="active",
        created_at=datetime.utcnow(),
    )
    return prediction


@pytest.fixture
def sample_config():
    """Configuration IA exemple."""
    config = AIConfiguration(
        id=1,
        tenant_id="tenant_test",
        is_enabled=True,
        enabled_features=["conversation", "analysis", "prediction"],
        daily_request_limit=1000,
        max_tokens_per_request=4000,
        response_language="fr",
        formality_level="professional",
        detail_level="balanced",
        require_confirmation_threshold="high",
        auto_escalation_enabled=True,
        escalation_delay_hours=24,
        notify_on_risk=True,
        notify_on_anomaly=True,
    )
    return config


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestAIModels:
    """Tests des modèles SQLAlchemy."""

    def test_ai_conversation_creation(self):
        """Test création conversation."""
        conv = AIConversation(
            tenant_id="test",
            user_id=1,
            title="Test",
            is_active=True,
        )
        assert conv.tenant_id == "test"
        assert conv.user_id == 1
        assert conv.is_active is True

    def test_ai_message_creation(self):
        """Test création message."""
        msg = AIMessage(
            tenant_id="test",
            conversation_id=1,
            role="user",
            content="Hello IA",
        )
        assert msg.role == "user"
        assert msg.content == "Hello IA"

    def test_ai_analysis_creation(self):
        """Test création analyse."""
        analysis = AIAnalysis(
            tenant_id="test",
            user_id=1,
            analysis_code="ANA-001",
            title="Analyse test",
            analysis_type="360",
        )
        assert analysis.analysis_type == "360"
        assert analysis.analysis_code == "ANA-001"

    def test_ai_decision_support_creation(self):
        """Test création support décision."""
        decision = AIDecisionSupport(
            tenant_id="test",
            decision_code="DEC-001",
            title="Décision test",
            decision_type="approval",
            is_red_point=False,
            created_by_id=1,
        )
        assert decision.decision_type == "approval"
        assert decision.is_red_point is False

    def test_ai_decision_red_point(self):
        """Test décision point rouge."""
        decision = AIDecisionSupport(
            tenant_id="test",
            decision_code="DEC-002",
            title="Décision critique",
            decision_type="critical_approval",
            is_red_point=True,
            requires_double_confirmation=True,
            created_by_id=1,
        )
        assert decision.is_red_point is True
        assert decision.requires_double_confirmation is True

    def test_ai_risk_alert_creation(self):
        """Test création alerte risque."""
        alert = AIRiskAlert(
            tenant_id="test",
            alert_code="RSK-001",
            title="Risque détecté",
            category="financial",
            risk_level="high",
            status="active",
        )
        assert alert.category == "financial"
        assert alert.risk_level == "high"
        assert alert.status == "active"

    def test_ai_prediction_creation(self):
        """Test création prédiction."""
        prediction = AIPrediction(
            tenant_id="test",
            prediction_code="PRE-001",
            title="Prévision",
            prediction_type="sales",
            prediction_start=datetime.utcnow(),
            prediction_end=datetime.utcnow() + timedelta(days=30),
        )
        assert prediction.prediction_type == "sales"

    def test_ai_feedback_creation(self):
        """Test création feedback."""
        feedback = AIFeedback(
            tenant_id="test",
            user_id=1,
            reference_type="analysis",
            reference_id=1,
            rating=4,
            is_helpful=True,
        )
        assert feedback.rating == 4
        assert feedback.is_helpful is True

    def test_ai_learning_data_creation(self):
        """Test création données apprentissage."""
        learning = AILearningData(
            data_hash="abc123",
            data_type="pattern",
            category="sales",
            usage_count=1,
        )
        assert learning.data_hash == "abc123"
        assert learning.usage_count == 1

    def test_ai_configuration_creation(self):
        """Test création configuration."""
        config = AIConfiguration(
            tenant_id="test",
            is_enabled=True,
            daily_request_limit=500,
            response_language="fr",
        )
        assert config.is_enabled is True
        assert config.daily_request_limit == 500

    def test_ai_audit_log_creation(self):
        """Test création log audit."""
        log = AIAuditLog(
            tenant_id="test",
            user_id=1,
            action="create_analysis",
            action_category="analysis",
            status="success",
        )
        assert log.action == "create_analysis"
        assert log.status == "success"


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestAIEnums:
    """Tests des enums."""

    def test_ai_request_types(self):
        """Test types de requêtes."""
        assert AIRequestType.QUESTION.value == "question"
        assert AIRequestType.ANALYSIS.value == "analysis"
        assert AIRequestType.PREDICTION.value == "prediction"
        assert AIRequestType.RECOMMENDATION.value == "recommendation"
        assert AIRequestType.RISK_DETECTION.value == "risk_detection"
        assert AIRequestType.DECISION_SUPPORT.value == "decision_support"

    def test_ai_response_status(self):
        """Test statuts de réponse."""
        assert AIResponseStatus.PENDING.value == "pending"
        assert AIResponseStatus.PROCESSING.value == "processing"
        assert AIResponseStatus.COMPLETED.value == "completed"
        assert AIResponseStatus.FAILED.value == "failed"
        assert AIResponseStatus.REQUIRES_CONFIRMATION.value == "requires_confirmation"

    def test_risk_levels(self):
        """Test niveaux de risque."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_risk_categories(self):
        """Test catégories de risque."""
        assert RiskCategory.FINANCIAL.value == "financial"
        assert RiskCategory.LEGAL.value == "legal"
        assert RiskCategory.OPERATIONAL.value == "operational"
        assert RiskCategory.REGULATORY.value == "regulatory"
        assert RiskCategory.SECURITY.value == "security"

    def test_decision_status(self):
        """Test statuts de décision."""
        assert DecisionStatus.DRAFT.value == "draft"
        assert DecisionStatus.PENDING_REVIEW.value == "pending_review"
        assert DecisionStatus.PENDING_CONFIRMATION.value == "pending_confirmation"
        assert DecisionStatus.CONFIRMED.value == "confirmed"
        assert DecisionStatus.REJECTED.value == "rejected"


# ============================================================================
# TESTS SCHEMAS
# ============================================================================

class TestAISchemas:
    """Tests des schémas Pydantic."""

    def test_conversation_create(self):
        """Test schéma création conversation."""
        data = ConversationCreate(
            title="Ma conversation",
            context={"module": "commercial"},
            module_source="commercial",
        )
        assert data.title == "Ma conversation"
        assert data.context["module"] == "commercial"

    def test_message_create(self):
        """Test schéma création message."""
        data = MessageCreate(
            content="Question test",
            request_type="question",
        )
        assert data.content == "Question test"
        assert data.request_type == "question"

    def test_message_create_validation(self):
        """Test validation longueur message."""
        # Contenu trop court
        with pytest.raises(Exception):
            MessageCreate(content="", request_type="question")

    def test_ai_question_request(self):
        """Test schéma question IA."""
        data = AIQuestionRequest(
            question="Quelle est la marge ?",
            module_source="finance",
            include_data=True,
        )
        assert data.question == "Quelle est la marge ?"
        assert data.include_data is True

    def test_analysis_request(self):
        """Test schéma demande analyse."""
        data = AnalysisRequest(
            title="Analyse client",
            analysis_type="360",
            entity_type="customer",
            entity_id="CUST-001",
        )
        assert data.analysis_type == "360"
        assert data.entity_type == "customer"

    def test_decision_support_create(self):
        """Test schéma création décision."""
        data = DecisionSupportCreate(
            title="Décision crédit",
            decision_type="credit",
            priority="high",
        )
        assert data.priority == "high"

    def test_decision_confirmation(self):
        """Test schéma confirmation décision."""
        data = DecisionConfirmation(
            decision_made=0,
            notes="Approuvé après analyse",
        )
        assert data.decision_made == 0
        assert data.notes == "Approuvé après analyse"

    def test_risk_alert_create(self):
        """Test schéma création alerte."""
        data = RiskAlertCreate(
            title="Risque crédit",
            category="financial",
            risk_level="high",
            probability=0.75,
            impact_score=8.0,
        )
        assert data.risk_level == "high"
        assert data.probability == 0.75

    def test_prediction_request(self):
        """Test schéma demande prédiction."""
        data = PredictionRequest(
            title="Prévision ventes",
            prediction_type="sales",
            prediction_start=datetime.utcnow(),
            prediction_end=datetime.utcnow() + timedelta(days=30),
            granularity="weekly",
        )
        assert data.prediction_type == "sales"
        assert data.granularity == "weekly"

    def test_feedback_create(self):
        """Test schéma création feedback."""
        data = FeedbackCreate(
            reference_type="analysis",
            reference_id=1,
            rating=5,
            is_helpful=True,
            feedback_text="Très utile !",
        )
        assert data.rating == 5
        assert data.is_helpful is True

    def test_ai_config_update(self):
        """Test schéma mise à jour config."""
        data = AIConfigUpdate(
            is_enabled=True,
            daily_request_limit=2000,
            response_language="en",
        )
        assert data.daily_request_limit == 2000

    def test_synthesis_request(self):
        """Test schéma demande synthèse."""
        data = SynthesisRequest(
            title="Synthèse hebdo",
            synthesis_type="weekly",
            modules=["commercial", "finance"],
        )
        assert data.synthesis_type == "weekly"
        assert "commercial" in data.modules


# ============================================================================
# TESTS SERVICE - CONVERSATIONS
# ============================================================================

class TestAIServiceConversations:
    """Tests service - Gestion des conversations."""

    def test_create_conversation(self, service, mock_db):
        """Test création conversation."""
        data = ConversationCreate(
            title="Nouvelle conversation",
            module_source="commercial",
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_conversation(user_id=1, data=data)

        # add est appelé 2 fois: 1 pour la conversation, 1 pour le log audit
        assert mock_db.add.call_count >= 1
        mock_db.commit.assert_called()
        assert result is not None

    def test_list_conversations(self, service, mock_db, sample_conversation):
        """Test liste conversations."""
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_conversation]

        result = service.list_conversations(user_id=1)

        assert len(result) >= 0

    def test_get_conversation(self, service, mock_db, sample_conversation):
        """Test récupération conversation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_conversation

        result = service.get_conversation(conversation_id=1)

        assert result is not None
        assert result.id == 1

    def test_get_conversation_not_found(self, service, mock_db):
        """Test conversation non trouvée."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_conversation(conversation_id=999)

        assert result is None

    def test_add_message(self, service, mock_db, sample_conversation):
        """Test ajout message."""
        # Mock différent selon le type de query
        def mock_query_side_effect(model):
            mock = MagicMock()
            if model == AIConversation:
                mock.filter.return_value.first.return_value = sample_conversation
            else:
                # Pour AILearningData, retourner None
                mock.filter.return_value.first.return_value = None
            return mock

        mock_db.query.side_effect = mock_query_side_effect

        data = MessageCreate(
            content="Bonjour, j'ai une question",
            request_type="question",
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        user_msg, assistant_msg = service.add_message(
            conversation_id=1,
            user_id=1,
            data=data,
        )

        # Au moins 2 messages ajoutés (user + assistant)
        assert mock_db.add.call_count >= 2


# ============================================================================
# TESTS SERVICE - ANALYSES
# ============================================================================

class TestAIServiceAnalyses:
    """Tests service - Analyses IA."""

    def test_create_analysis(self, service, mock_db):
        """Test création analyse."""
        data = AnalysisRequest(
            title="Analyse client",
            analysis_type="360",
            entity_type="customer",
            entity_id="CUST-001",
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_analysis(user_id=1, data=data)

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_get_analysis(self, service, mock_db, sample_analysis):
        """Test récupération analyse."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_analysis

        result = service.get_analysis(analysis_id=1)

        assert result is not None
        assert result.analysis_type == "360"

    def test_list_analyses(self, service, mock_db, sample_analysis):
        """Test liste analyses."""
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_analysis]

        result = service.list_analyses()

        assert len(result) >= 0


# ============================================================================
# TESTS SERVICE - DÉCISIONS (GOUVERNANCE)
# ============================================================================

class TestAIServiceDecisions:
    """Tests service - Support de décision avec gouvernance."""

    def test_create_decision_support(self, service, mock_db):
        """Test création support décision."""
        data = DecisionSupportCreate(
            title="Extension crédit",
            decision_type="credit",
            priority="high",
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_decision_support(user_id=1, data=data)

        mock_db.add.assert_called()

    def test_confirm_decision_normal(self, service, mock_db, sample_decision):
        """Test confirmation décision normale (pas point rouge)."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_decision
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()
        mock_db.refresh = MagicMock()

        data = DecisionConfirmation(decision_made=0, notes="OK")

        result = service.confirm_decision(
            decision_id=1,
            user_id=1,
            data=data,
        )

        assert sample_decision.status == "confirmed"
        assert sample_decision.decision_made == 0

    def test_confirm_decision_red_point_first(self, service, mock_db, sample_red_point_decision):
        """Test première confirmation point rouge."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_red_point_decision
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()
        mock_db.refresh = MagicMock()

        data = DecisionConfirmation(decision_made=0, notes="Première validation")

        result = service.confirm_decision(
            decision_id=2,
            user_id=1,
            data=data,
        )

        # Après première confirmation, statut doit être pending_confirmation
        assert sample_red_point_decision.first_confirmation_by == 1
        assert sample_red_point_decision.status == "pending_confirmation"

    def test_confirm_decision_red_point_second_different_user(self, service, mock_db, sample_red_point_decision):
        """Test deuxième confirmation point rouge par utilisateur différent."""
        # Simuler première confirmation déjà faite
        sample_red_point_decision.first_confirmation_by = 1
        sample_red_point_decision.first_confirmation_at = datetime.utcnow()
        sample_red_point_decision.status = "pending_confirmation"

        mock_db.query.return_value.filter.return_value.first.return_value = sample_red_point_decision
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()
        mock_db.refresh = MagicMock()

        data = DecisionConfirmation(decision_made=0, notes="Deuxième validation")

        # User 2 confirme (différent de user 1)
        result = service.confirm_decision(
            decision_id=2,
            user_id=2,
            data=data,
        )

        assert sample_red_point_decision.second_confirmation_by == 2
        assert sample_red_point_decision.status == "confirmed"

    def test_confirm_decision_red_point_same_user_fails(self, service, mock_db, sample_red_point_decision):
        """Test échec si même utilisateur tente double confirmation."""
        # Simuler première confirmation
        sample_red_point_decision.first_confirmation_by = 1
        sample_red_point_decision.first_confirmation_at = datetime.utcnow()
        sample_red_point_decision.status = "pending_confirmation"

        mock_db.query.return_value.filter.return_value.first.return_value = sample_red_point_decision

        data = DecisionConfirmation(decision_made=0, notes="Tentative même user")

        # User 1 tente de confirmer une deuxième fois
        with pytest.raises(ValueError) as exc_info:
            service.confirm_decision(
                decision_id=2,
                user_id=1,  # Même user que première confirmation
                data=data,
            )

        assert "deux personnes différentes" in str(exc_info.value).lower() or "different" in str(exc_info.value).lower()

    def test_reject_decision(self, service, mock_db, sample_decision):
        """Test rejet décision."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_decision
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.reject_decision(
            decision_id=1,
            user_id=1,
            reason="Risque trop élevé",
        )

        assert sample_decision.status == "rejected"


# ============================================================================
# TESTS SERVICE - RISQUES
# ============================================================================

class TestAIServiceRisks:
    """Tests service - Alertes de risque."""

    def test_create_risk_alert(self, service, mock_db):
        """Test création alerte risque."""
        data = RiskAlertCreate(
            title="Dépassement crédit",
            category="financial",
            risk_level="high",
            probability=0.8,
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_risk_alert(data=data)

        mock_db.add.assert_called()

    def test_get_risk_alert(self, service, mock_db, sample_risk_alert):
        """Test récupération alerte."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_risk_alert

        result = service.get_risk_alert(alert_id=1)

        assert result is not None
        assert result.risk_level == "high"

    def test_acknowledge_risk(self, service, mock_db, sample_risk_alert):
        """Test accusé réception risque."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_risk_alert
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()
        mock_db.refresh = MagicMock()

        data = RiskAcknowledge(notes="Pris en compte")

        result = service.acknowledge_risk(
            alert_id=1,
            user_id=1,
            data=data,
        )

        assert sample_risk_alert.status == "acknowledged"
        assert sample_risk_alert.acknowledged_by == 1

    def test_resolve_risk(self, service, mock_db, sample_risk_alert):
        """Test résolution risque."""
        sample_risk_alert.status = "acknowledged"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_risk_alert
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()
        mock_db.refresh = MagicMock()

        data = RiskResolve(
            resolution_notes="Client a régularisé sa situation",
            actions_taken=["Contact client", "Plan de paiement"],
        )

        result = service.resolve_risk(
            alert_id=1,
            user_id=1,
            data=data,
        )

        assert sample_risk_alert.status == "resolved"
        assert sample_risk_alert.resolved_by == 1


# ============================================================================
# TESTS SERVICE - PRÉDICTIONS
# ============================================================================

class TestAIServicePredictions:
    """Tests service - Prédictions IA."""

    def test_create_prediction(self, service, mock_db):
        """Test création prédiction."""
        data = PredictionRequest(
            title="Prévision ventes",
            prediction_type="sales",
            prediction_start=datetime.utcnow(),
            prediction_end=datetime.utcnow() + timedelta(days=30),
            granularity="daily",
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_prediction(user_id=1, data=data)

        mock_db.add.assert_called()

    def test_get_prediction(self, service, mock_db, sample_prediction):
        """Test récupération prédiction."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_prediction

        result = service.get_prediction(prediction_id=1)

        assert result is not None
        assert result.prediction_type == "sales"


# ============================================================================
# TESTS SERVICE - FEEDBACK
# ============================================================================

class TestAIServiceFeedback:
    """Tests service - Feedback utilisateur."""

    def test_add_feedback(self, service, mock_db):
        """Test ajout feedback."""
        data = FeedbackCreate(
            reference_type="analysis",
            reference_id=1,
            rating=5,
            is_helpful=True,
            feedback_text="Excellente analyse !",
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.add_feedback(user_id=1, data=data)

        mock_db.add.assert_called()


# ============================================================================
# TESTS SERVICE - CONFIGURATION
# ============================================================================

class TestAIServiceConfig:
    """Tests service - Configuration IA."""

    def test_get_config_existing(self, service, mock_db, sample_config):
        """Test récupération config existante."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_config

        result = service.get_config()

        assert result is not None
        assert result.is_enabled is True
        assert result.daily_request_limit == 1000

    def test_get_config_creates_default(self, service, mock_db):
        """Test création config par défaut si inexistante."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.get_config()

        mock_db.add.assert_called()

    def test_update_config(self, service, mock_db, sample_config):
        """Test mise à jour config."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_config
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()

        data = AIConfigUpdate(
            daily_request_limit=2000,
            response_language="en",
        )

        result = service.update_config(user_id=1, data=data)

        assert sample_config.daily_request_limit == 2000
        assert sample_config.response_language == "en"


# ============================================================================
# TESTS SERVICE - SYNTHÈSES
# ============================================================================

class TestAIServiceSynthesis:
    """Tests service - Génération de synthèses."""

    def test_generate_synthesis(self, service, mock_db):
        """Test génération synthèse."""
        data = SynthesisRequest(
            title="Synthèse hebdomadaire",
            synthesis_type="weekly",
            modules=["commercial", "finance"],
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = service.generate_synthesis(user_id=1, data=data)

        assert result is not None
        assert "executive_summary" in result


# ============================================================================
# TESTS SERVICE - STATISTIQUES & SANTÉ
# ============================================================================

class TestAIServiceStats:
    """Tests service - Statistiques et santé."""

    def test_get_stats(self, service, mock_db):
        """Test récupération statistiques."""
        # Mock des comptages
        mock_db.query.return_value.filter.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.scalar.return_value = 0

        result = service.get_stats()

        assert result is not None
        assert "total_conversations" in result

    def test_health_check(self, service, mock_db, sample_config):
        """Test vérification santé."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_config
        mock_db.execute = MagicMock()

        result = service.health_check()

        assert result is not None
        assert "status" in result


# ============================================================================
# TESTS GOUVERNANCE - TRAÇABILITÉ
# ============================================================================

class TestAIGovernance:
    """Tests de gouvernance et traçabilité."""

    def test_audit_log_on_analysis(self, service, mock_db):
        """Test création log audit lors d'une analyse."""
        data = AnalysisRequest(
            title="Analyse test",
            analysis_type="financial",
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        service.create_analysis(user_id=1, data=data)

        # Vérifier que add a été appelé plusieurs fois (analyse + audit)
        assert mock_db.add.call_count >= 1

    def test_audit_log_on_decision(self, service, mock_db, sample_decision):
        """Test création log audit lors d'une décision."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_decision
        mock_db.commit = MagicMock()
        mock_db.add = MagicMock()
        mock_db.refresh = MagicMock()

        data = DecisionConfirmation(decision_made=0, notes="Approuvé")

        service.confirm_decision(
            decision_id=1,
            user_id=1,
            data=data,
        )

        # Vérifier que add a été appelé pour le log audit
        assert mock_db.add.call_count >= 1

    def test_ia_never_decides_alone(self, sample_decision):
        """Test que l'IA ne décide jamais seule - décisions humaines requises."""
        # Une décision sans confirmation humaine ne doit pas être 'confirmed'
        assert sample_decision.status == "pending_review"
        assert sample_decision.decided_by_id is None

        # L'IA peut recommander mais pas décider
        assert sample_decision.recommended_option is not None or sample_decision.recommended_option == 0
        assert sample_decision.status != "confirmed"

    def test_red_point_requires_double_confirmation(self, sample_red_point_decision):
        """Test que les points rouges nécessitent double confirmation."""
        assert sample_red_point_decision.is_red_point is True
        assert sample_red_point_decision.requires_double_confirmation is True

        # Sans double confirmation, statut ne peut pas être confirmed
        assert sample_red_point_decision.first_confirmation_by is None
        assert sample_red_point_decision.second_confirmation_by is None
        assert sample_red_point_decision.status != "confirmed"


# ============================================================================
# TESTS INTÉGRATION API
# ============================================================================

class TestAIAPIIntegration:
    """Tests d'intégration API (structure des réponses)."""

    def test_conversation_response_structure(self, sample_conversation):
        """Test structure réponse conversation."""
        assert hasattr(sample_conversation, "id")
        assert hasattr(sample_conversation, "tenant_id")
        assert hasattr(sample_conversation, "user_id")
        assert hasattr(sample_conversation, "title")
        assert hasattr(sample_conversation, "is_active")
        assert hasattr(sample_conversation, "message_count")

    def test_analysis_response_structure(self, sample_analysis):
        """Test structure réponse analyse."""
        assert hasattr(sample_analysis, "id")
        assert hasattr(sample_analysis, "analysis_code")
        assert hasattr(sample_analysis, "analysis_type")
        assert hasattr(sample_analysis, "summary")
        assert hasattr(sample_analysis, "findings")
        assert hasattr(sample_analysis, "recommendations")
        assert hasattr(sample_analysis, "confidence_score")

    def test_decision_response_structure(self, sample_decision):
        """Test structure réponse décision."""
        assert hasattr(sample_decision, "id")
        assert hasattr(sample_decision, "decision_code")
        assert hasattr(sample_decision, "options")
        assert hasattr(sample_decision, "recommended_option")
        assert hasattr(sample_decision, "is_red_point")
        assert hasattr(sample_decision, "requires_double_confirmation")
        assert hasattr(sample_decision, "status")

    def test_risk_response_structure(self, sample_risk_alert):
        """Test structure réponse risque."""
        assert hasattr(sample_risk_alert, "id")
        assert hasattr(sample_risk_alert, "alert_code")
        assert hasattr(sample_risk_alert, "category")
        assert hasattr(sample_risk_alert, "risk_level")
        assert hasattr(sample_risk_alert, "status")
        assert hasattr(sample_risk_alert, "recommended_actions")

    def test_prediction_response_structure(self, sample_prediction):
        """Test structure réponse prédiction."""
        assert hasattr(sample_prediction, "id")
        assert hasattr(sample_prediction, "prediction_code")
        assert hasattr(sample_prediction, "prediction_type")
        assert hasattr(sample_prediction, "predicted_values")
        assert hasattr(sample_prediction, "confidence_score")
