"""
Module Surveys / Sondages - GAP-065

Gestion des enquêtes et sondages:
- Création de questionnaires
- Types de questions variés
- Logique conditionnelle
- Distribution multi-canal
- Collecte de réponses
- Analyses et rapports
- NPS et satisfaction
"""

from .service import (
    # Énumérations
    SurveyType,
    SurveyStatus,
    QuestionType,
    ResponseStatus,
    DistributionChannel,
    TriggerType,

    # Data classes
    QuestionOption,
    QuestionLogic,
    Question,
    SurveyPage,
    Survey,
    SurveyDistribution,
    Response,
    Answer,
    QuestionAnalytics,
    SurveyAnalytics,
    SurveyTemplate,

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
    "TriggerType",
    "QuestionOption",
    "QuestionLogic",
    "Question",
    "SurveyPage",
    "Survey",
    "SurveyDistribution",
    "Response",
    "Answer",
    "QuestionAnalytics",
    "SurveyAnalytics",
    "SurveyTemplate",
    "SurveyService",
    "create_survey_service",
]
