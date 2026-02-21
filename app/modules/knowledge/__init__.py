"""
Module Knowledge Base - GAP-068

Base de connaissances:
- Articles et documentation
- Catégories et tags
- Recherche full-text
- Versioning des articles
- Feedback et notation
- FAQ dynamique
- Analytics de lecture
"""

from .service import (
    # Énumérations
    ArticleStatus,
    ArticleType,
    Visibility,
    FeedbackType,

    # Data classes
    Category,
    Article,
    ArticleVersion,
    FAQItem,
    Feedback,
    SearchResult,
    ViewLog,
    KnowledgeStats,

    # Service
    KnowledgeService,
    create_knowledge_service,
)

__all__ = [
    "ArticleStatus",
    "ArticleType",
    "Visibility",
    "FeedbackType",
    "Category",
    "Article",
    "ArticleVersion",
    "FAQItem",
    "Feedback",
    "SearchResult",
    "ViewLog",
    "KnowledgeStats",
    "KnowledgeService",
    "create_knowledge_service",
]
