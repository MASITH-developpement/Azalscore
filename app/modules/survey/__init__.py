"""
Module Survey / Enquêtes et Feedback - GAP-082

Gestion des enquêtes et retours:
- Création d'enquêtes
- Types de questions variés
- Distribution et collecte
- Analyse des réponses
- Score NPS et satisfaction
- Rapports et tendances
"""

from .service import (
    # Énumérations
    SurveyType,
    SurveyStatus,
    QuestionType,
    ResponseStatus,
    DistributionChannel,

    # Data classes
    QuestionOption,
    QuestionLogic,
    Question,
    Survey,
    Answer,
    SurveyResponse,
    Distribution,
    SurveyTemplate,
    QuestionStats,
    SurveyAnalytics,

    # Service
    SurveyService,
    create_survey_service,
)

__all__ = [
    "SurveyType",
    "SurveyStatus",
    "QuestionType",
    "ResponseStatus",
    "DistributionChannel",
    "QuestionOption",
    "QuestionLogic",
    "Question",
    "Survey",
    "Answer",
    "SurveyResponse",
    "Distribution",
    "SurveyTemplate",
    "QuestionStats",
    "SurveyAnalytics",
    "SurveyService",
    "create_survey_service",
]
