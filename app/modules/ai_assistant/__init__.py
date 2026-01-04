"""
AZALS - MODULE IA TRANSVERSE OPÉRATIONNELLE
=============================================
Assistant IA central pour aide à la décision.

Principes fondamentaux:
- IA assistante, JAMAIS décisionnaire finale
- Double confirmation pour points rouges
- Traçabilité complète
- Apprentissage transversal anonymisé

Fonctionnalités:
- Conversations interactives
- Analyses 360° (financial, operational, risk)
- Support de décision avec gouvernance
- Détection et alertes de risques
- Prédictions (ventes, trésorerie, demande)
- Synthèses automatisées
- Feedback et apprentissage continu
"""

from .models import (
    # Enums
    AIRequestType,
    AIResponseStatus,
    RiskLevel,
    RiskCategory,
    DecisionStatus,
    # Models
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
)

from .schemas import (
    # Conversation
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    AIQuestionRequest,
    AIQuestionResponse,
    # Analysis
    AnalysisRequest,
    AnalysisFinding,
    AnalysisRecommendation,
    AnalysisResponse,
    # Decision Support
    DecisionOption,
    DecisionSupportCreate,
    DecisionSupportResponse,
    DecisionConfirmation,
    # Risk
    RiskAlertCreate,
    RiskAlertResponse,
    RiskAcknowledge,
    RiskResolve,
    # Prediction
    PredictionRequest,
    PredictionValue,
    PredictionResponse,
    # Feedback
    FeedbackCreate,
    # Config
    AIConfigUpdate,
    AIConfigResponse,
    # Dashboard
    AIStats,
    AIHealthCheck,
    # Synthesis
    SynthesisRequest,
    SynthesisResponse,
)

from .service import AIAssistantService
from .router import router

__all__ = [
    # Enums
    "AIRequestType",
    "AIResponseStatus",
    "RiskLevel",
    "RiskCategory",
    "DecisionStatus",
    # Models
    "AIConversation",
    "AIMessage",
    "AIAnalysis",
    "AIDecisionSupport",
    "AIRiskAlert",
    "AIPrediction",
    "AIFeedback",
    "AILearningData",
    "AIConfiguration",
    "AIAuditLog",
    # Schemas - Conversation
    "ConversationCreate",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse",
    "AIQuestionRequest",
    "AIQuestionResponse",
    # Schemas - Analysis
    "AnalysisRequest",
    "AnalysisFinding",
    "AnalysisRecommendation",
    "AnalysisResponse",
    # Schemas - Decision
    "DecisionOption",
    "DecisionSupportCreate",
    "DecisionSupportResponse",
    "DecisionConfirmation",
    # Schemas - Risk
    "RiskAlertCreate",
    "RiskAlertResponse",
    "RiskAcknowledge",
    "RiskResolve",
    # Schemas - Prediction
    "PredictionRequest",
    "PredictionValue",
    "PredictionResponse",
    # Schemas - Feedback
    "FeedbackCreate",
    # Schemas - Config
    "AIConfigUpdate",
    "AIConfigResponse",
    # Schemas - Dashboard
    "AIStats",
    "AIHealthCheck",
    # Schemas - Synthesis
    "SynthesisRequest",
    "SynthesisResponse",
    # Service
    "AIAssistantService",
    # Router
    "router",
]
