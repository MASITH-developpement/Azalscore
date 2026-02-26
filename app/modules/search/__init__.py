"""
Module Recherche et Indexation - GAP-052

Moteur de recherche full-text:
- Indexation multi-entités
- Recherche full-text avec scoring
- Filtres et facettes
- Suggestions et autocomplétion
- Recherche phonétique
- Synonymes configurables
- Historique de recherche
"""

from .service import (
    # Énumérations
    IndexStatus,
    FieldType,
    AnalyzerType,
    SortOrder,
    SuggestionType,
    QueryType,

    # Data classes
    FieldMapping,
    IndexDefinition,
    IndexedDocument,
    SearchQuery,
    SearchHit,
    FacetBucket,
    FacetResult,
    SearchResult,
    Suggestion,
    SearchHistory,
    ReindexJob,

    # Service
    SearchService,
    create_search_service,
)

__all__ = [
    "IndexStatus",
    "FieldType",
    "AnalyzerType",
    "SortOrder",
    "SuggestionType",
    "QueryType",
    "FieldMapping",
    "IndexDefinition",
    "IndexedDocument",
    "SearchQuery",
    "SearchHit",
    "FacetBucket",
    "FacetResult",
    "SearchResult",
    "Suggestion",
    "SearchHistory",
    "ReindexJob",
    "SearchService",
    "create_search_service",
]
