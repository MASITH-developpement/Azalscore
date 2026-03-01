"""
Service Recherche et Indexation - GAP-052

Moteur de recherche full-text avec persistence SQLAlchemy:
- Indexation multi-entites
- Recherche full-text avec scoring
- Filtres et facettes
- Suggestions et autocompletion
- Recherche phonetique
- Synonymes configurables
- Historique de recherche

CRITIQUE: Utilise les repositories pour l'isolation multi-tenant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import re
import unicodedata

from sqlalchemy.orm import Session

from .models import (
    IndexStatus,
    FieldType,
    AnalyzerType,
    SearchIndex,
    IndexedDocument,
    SearchHistory,
    ReindexJob,
    TermFrequency,
    ReindexJobStatus,
)
from .repository import (
    SearchIndexRepository,
    IndexedDocumentRepository,
    SearchHistoryRepository,
    ReindexJobRepository,
    TermFrequencyRepository,
)


# ============================================================
# ENUMERATIONS LOCALES
# ============================================================

class SortOrder:
    """Ordre de tri."""
    ASC = "asc"
    DESC = "desc"
    RELEVANCE = "relevance"


class SuggestionType:
    """Types de suggestions."""
    COMPLETION = "completion"
    PHRASE = "phrase"
    TERM = "term"
    DID_YOU_MEAN = "did_you_mean"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class FieldMapping:
    """Mapping d'un champ indexe."""
    name: str
    field_type: FieldType
    analyzer: Optional[AnalyzerType] = None
    searchable: bool = True
    filterable: bool = True
    sortable: bool = False
    facetable: bool = False
    boost: float = 1.0
    copy_to: Optional[str] = None
    nested_fields: List["FieldMapping"] = field(default_factory=list)


@dataclass
class SearchQuery:
    """Requete de recherche."""
    query_text: str
    fields: Optional[List[str]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    sort_by: Optional[str] = None
    sort_order: str = "relevance"
    page: int = 1
    page_size: int = 20
    highlight: bool = True
    fuzzy: bool = True
    fuzzy_distance: int = 2


@dataclass
class SearchResult:
    """Resultat de recherche."""
    document_id: str
    entity_id: str
    entity_type: str
    score: float
    data: Dict[str, Any]
    highlights: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Reponse complete de recherche."""
    query: str
    total: int
    page: int
    page_size: int
    results: List[SearchResult]
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    execution_time_ms: int = 0


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class SearchService:
    """Service de recherche et indexation avec persistence SQLAlchemy."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories avec isolation tenant
        self.index_repo = SearchIndexRepository(db, tenant_id)
        self.document_repo = IndexedDocumentRepository(db, tenant_id)
        self.history_repo = SearchHistoryRepository(db, tenant_id)
        self.reindex_repo = ReindexJobRepository(db, tenant_id)
        self.term_repo = TermFrequencyRepository(db, tenant_id)

        # Stopwords francais
        self._stopwords = {
            "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou",
            "mais", "donc", "car", "ni", "que", "qui", "quoi", "dont",
            "ce", "cette", "ces", "son", "sa", "ses", "mon", "ma", "mes",
            "ton", "ta", "tes", "notre", "nos", "votre", "vos", "leur", "leurs",
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
            "ne", "pas", "plus", "moins", "tres", "bien", "mal",
            "sur", "sous", "dans", "avec", "sans", "pour", "par", "en", "a",
            "est", "sont", "etait", "ete", "etre", "avoir", "fait", "faire",
        }

    # ========================================
    # GESTION DES INDEX
    # ========================================

    def create_index(
        self,
        name: str,
        entity_type: str,
        field_mappings: List[FieldMapping],
        **kwargs
    ) -> SearchIndex:
        """Cree un nouvel index."""
        # Verifier unicite du nom
        existing = self.index_repo.get_by_name(name)
        if existing:
            raise ValueError(f"Index {name} existe deja")

        # Convertir les field_mappings en dict
        mappings = [
            {
                "name": fm.name,
                "field_type": fm.field_type.value if hasattr(fm.field_type, 'value') else fm.field_type,
                "analyzer": fm.analyzer.value if fm.analyzer and hasattr(fm.analyzer, 'value') else fm.analyzer,
                "searchable": fm.searchable,
                "filterable": fm.filterable,
                "sortable": fm.sortable,
                "facetable": fm.facetable,
                "boost": fm.boost,
            }
            for fm in field_mappings
        ]

        data = {
            "name": name,
            "entity_type": entity_type,
            "field_mappings": mappings,
            "default_analyzer": kwargs.get("default_analyzer", AnalyzerType.FRENCH),
            "refresh_interval_seconds": kwargs.get("refresh_interval_seconds", 1),
            "synonyms": kwargs.get("synonyms", {}),
            "status": IndexStatus.ACTIVE,
        }

        return self.index_repo.create(data)

    def get_index(self, index_id: str) -> Optional[SearchIndex]:
        """Recupere un index par ID."""
        return self.index_repo.get_by_id(index_id)

    def get_index_by_name(self, name: str) -> Optional[SearchIndex]:
        """Recupere un index par nom."""
        return self.index_repo.get_by_name(name)

    def get_index_for_entity(self, entity_type: str) -> Optional[SearchIndex]:
        """Recupere l'index pour un type d'entite."""
        return self.index_repo.get_by_entity_type(entity_type)

    def list_indexes(
        self,
        status: Optional[IndexStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[SearchIndex], int]:
        """Liste les index."""
        return self.index_repo.list(status=status, page=page, page_size=page_size)

    def update_index(self, index_id: str, **updates) -> Optional[SearchIndex]:
        """Met a jour un index."""
        index = self.index_repo.get_by_id(index_id)
        if not index:
            return None
        return self.index_repo.update(index, updates)

    def delete_index(self, index_id: str) -> bool:
        """Supprime un index et ses documents."""
        index = self.index_repo.get_by_id(index_id)
        if not index:
            return False

        # Supprimer tous les documents
        self.document_repo.delete_all_by_index(index_id)

        # Supprimer l'index
        self.index_repo.delete(index)
        return True

    # ========================================
    # INDEXATION DE DOCUMENTS
    # ========================================

    def index_document(
        self,
        index_id: str,
        entity_id: str,
        data: Dict[str, Any],
        **kwargs
    ) -> IndexedDocument:
        """Indexe un document."""
        index = self.index_repo.get_by_id(index_id)
        if not index:
            raise ValueError(f"Index {index_id} non trouve")

        if index.status != IndexStatus.ACTIVE:
            raise ValueError(f"Index {index.name} n'est pas actif")

        # Creer le texte recherchable
        all_text = self._extract_searchable_text(data, index.field_mappings)

        # Upsert le document
        doc_data = {
            "data": data,
            "all_text": all_text,
            "indexed_at": datetime.utcnow(),
        }

        doc = self.document_repo.upsert(index_id, entity_id, doc_data)

        # Mettre a jour les frequences de termes
        tokens = self._tokenize(all_text)
        for token in set(tokens):
            self.term_repo.increment(token, index_id)

        # Mettre a jour les stats de l'index
        docs, total = self.document_repo.list_by_index(index_id, page_size=1)
        self.index_repo.update_stats(index, total, 0)

        return doc

    def bulk_index(
        self,
        index_id: str,
        documents: List[Dict[str, Any]],
        id_field: str = "id"
    ) -> Dict[str, Any]:
        """Indexe plusieurs documents en masse."""
        index = self.index_repo.get_by_id(index_id)
        if not index:
            raise ValueError(f"Index {index_id} non trouve")

        success = 0
        errors = []

        for doc in documents:
            entity_id = str(doc.get(id_field))
            if not entity_id:
                errors.append({"error": "Missing ID", "document": doc})
                continue

            try:
                self.index_document(index_id, entity_id, doc)
                success += 1
            except Exception as e:
                errors.append({"error": str(e), "entity_id": entity_id})

        return {
            "success": success,
            "errors": len(errors),
            "error_details": errors[:10]  # Limiter les details
        }

    def delete_document(self, index_id: str, entity_id: str) -> bool:
        """Supprime un document de l'index."""
        return self.document_repo.delete_by_entity(index_id, entity_id)

    def get_document(self, index_id: str, entity_id: str) -> Optional[IndexedDocument]:
        """Recupere un document indexe."""
        return self.document_repo.get_by_entity(index_id, entity_id)

    # ========================================
    # RECHERCHE
    # ========================================

    def search(
        self,
        index_id: str,
        query: SearchQuery,
        user_id: Optional[str] = None
    ) -> SearchResponse:
        """Execute une recherche."""
        import time
        start = time.time()

        index = self.index_repo.get_by_id(index_id)
        if not index:
            raise ValueError(f"Index {index_id} non trouve")

        # Tokenizer la requete
        tokens = self._tokenize(query.query_text)

        # Recherche simple par texte
        documents = self.document_repo.search_fulltext(
            index_id,
            query.query_text,
            limit=query.page_size * 2
        )

        # Scorer les resultats
        results = []
        for doc in documents:
            score = self._calculate_score(doc, tokens)
            highlights = self._generate_highlights(doc.all_text, tokens) if query.highlight else {}

            results.append(SearchResult(
                document_id=str(doc.id),
                entity_id=doc.entity_id,
                entity_type=index.entity_type,
                score=score,
                data=doc.data or {},
                highlights={"content": highlights} if highlights else {}
            ))

        # Trier par score
        results.sort(key=lambda r: r.score, reverse=True)

        # Pagination
        total = len(results)
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        paginated = results[start_idx:end_idx]

        execution_time = int((time.time() - start) * 1000)

        # Enregistrer l'historique
        if user_id:
            self.history_repo.create({
                "query_text": query.query_text,
                "index_id": index_id,
                "user_id": user_id,
                "results_count": total,
                "execution_time_ms": execution_time,
                "filters_used": query.filters,
            })

        # Obtenir les suggestions
        suggestions = self.get_suggestions(query.query_text[:3], index_id, limit=5)

        return SearchResponse(
            query=query.query_text,
            total=total,
            page=query.page,
            page_size=query.page_size,
            results=paginated,
            suggestions=suggestions,
            execution_time_ms=execution_time
        )

    def search_all_indexes(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, List[SearchResult]]:
        """Recherche dans tous les index."""
        indexes, _ = self.index_repo.list(status=IndexStatus.ACTIVE)
        results_by_type = {}

        query = SearchQuery(
            query_text=query_text,
            page_size=limit
        )

        for index in indexes:
            try:
                response = self.search(str(index.id), query)
                if response.results:
                    results_by_type[index.entity_type] = response.results
            except Exception:
                continue

        return results_by_type

    # ========================================
    # SUGGESTIONS
    # ========================================

    def get_suggestions(
        self,
        prefix: str,
        index_id: Optional[str] = None,
        limit: int = 10
    ) -> List[str]:
        """Recupere les suggestions pour un prefixe."""
        if len(prefix) < 2:
            return []

        return self.term_repo.get_suggestions(prefix, index_id, limit)

    # ========================================
    # HISTORIQUE
    # ========================================

    def get_search_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchHistory]:
        """Recupere l'historique de recherche."""
        if user_id:
            return self.history_repo.get_user_recent(user_id, limit)
        items, _ = self.history_repo.list(page_size=limit)
        return items

    def get_popular_searches(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Recupere les recherches populaires."""
        return self.history_repo.get_popular_queries(days, limit)

    def record_click(self, search_id: str, document_id: str) -> Optional[SearchHistory]:
        """Enregistre un clic sur un resultat."""
        return self.history_repo.record_click(search_id, document_id)

    # ========================================
    # REINDEXATION
    # ========================================

    def start_reindex(
        self,
        index_id: str,
        full: bool = True,
        started_by: Optional[str] = None
    ) -> ReindexJob:
        """Demarre un job de reindexation."""
        index = self.index_repo.get_by_id(index_id)
        if not index:
            raise ValueError(f"Index {index_id} non trouve")

        # Verifier qu'il n'y a pas de job en cours
        running = self.reindex_repo.get_running()
        for job in running:
            if str(job.index_id) == index_id:
                raise ValueError("Reindexation deja en cours")

        job_data = {
            "index_id": index_id,
            "job_type": "full" if full else "partial",
            "started_by": started_by,
        }
        return self.reindex_repo.create(job_data)

    def get_reindex_job(self, job_id: str) -> Optional[ReindexJob]:
        """Recupere un job de reindexation."""
        return self.reindex_repo.get_by_id(job_id)

    def list_reindex_jobs(
        self,
        index_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ReindexJob], int]:
        """Liste les jobs de reindexation."""
        return self.reindex_repo.list_by_index(index_id, page, page_size)

    # ========================================
    # UTILITAIRES
    # ========================================

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize et normalise le texte."""
        if not text:
            return []

        # Normaliser (accents)
        text = unicodedata.normalize("NFD", text.lower())
        text = "".join(c for c in text if not unicodedata.combining(c))

        # Extraire les mots
        tokens = re.findall(r'\b\w+\b', text)

        # Filtrer stopwords et trop courts
        return [t for t in tokens if len(t) > 2 and t not in self._stopwords]

    def _extract_searchable_text(
        self,
        data: Dict[str, Any],
        field_mappings: List[Dict[str, Any]]
    ) -> str:
        """Extrait le texte recherchable d'un document."""
        texts = []

        for mapping in field_mappings:
            if not mapping.get("searchable", True):
                continue

            field_name = mapping["name"]
            value = data.get(field_name)

            if value is None:
                continue

            if isinstance(value, str):
                texts.append(value)
            elif isinstance(value, (list, tuple)):
                texts.extend(str(v) for v in value if v)
            else:
                texts.append(str(value))

        return " ".join(texts)

    def _calculate_score(
        self,
        document: IndexedDocument,
        query_tokens: List[str]
    ) -> float:
        """Calcule le score de pertinence."""
        if not query_tokens or not document.all_text:
            return 0.0

        doc_text = document.all_text.lower()
        doc_tokens = set(self._tokenize(doc_text))

        # TF-IDF simplifie
        matches = len(set(query_tokens) & doc_tokens)
        if matches == 0:
            return 0.0

        # Score = matches / tokens dans la requete
        score = matches / len(query_tokens)

        # Bonus pour correspondance exacte de phrase
        query_phrase = " ".join(query_tokens)
        if query_phrase in doc_text:
            score *= 1.5

        return min(score, 1.0)

    def _generate_highlights(
        self,
        text: str,
        query_tokens: List[str],
        max_fragments: int = 3
    ) -> List[str]:
        """Genere les extraits surlignés."""
        if not text or not query_tokens:
            return []

        highlights = []
        text_lower = text.lower()

        for token in query_tokens:
            # Trouver les positions
            start = text_lower.find(token)
            if start == -1:
                continue

            # Extraire le contexte
            context_start = max(0, start - 50)
            context_end = min(len(text), start + len(token) + 50)

            fragment = text[context_start:context_end]
            if context_start > 0:
                fragment = "..." + fragment
            if context_end < len(text):
                fragment = fragment + "..."

            highlights.append(fragment)

            if len(highlights) >= max_fragments:
                break

        return highlights


# ============================================================
# FACTORY
# ============================================================

def create_search_service(db: Session, tenant_id: str) -> SearchService:
    """Cree un service de recherche."""
    return SearchService(db, tenant_id)
