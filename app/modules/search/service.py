"""
Service Recherche et Indexation - GAP-052

Moteur de recherche full-text:
- Indexation multi-entités
- Recherche full-text avec scoring
- Filtres et facettes
- Suggestions et autocomplétion
- Recherche phonétique
- Synonymes configurables
- Historique de recherche
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4
import re
import unicodedata


# ============================================================
# ÉNUMÉRATIONS
# ============================================================

class IndexStatus(Enum):
    """Statut d'un index."""
    ACTIVE = "active"
    BUILDING = "building"
    REBUILDING = "rebuilding"
    DISABLED = "disabled"
    ERROR = "error"


class FieldType(Enum):
    """Types de champs indexés."""
    TEXT = "text"
    KEYWORD = "keyword"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    BOOLEAN = "boolean"
    GEO_POINT = "geo_point"
    NESTED = "nested"


class AnalyzerType(Enum):
    """Types d'analyseurs de texte."""
    STANDARD = "standard"
    FRENCH = "french"
    SIMPLE = "simple"
    WHITESPACE = "whitespace"
    KEYWORD = "keyword"
    PHONETIC = "phonetic"


class SortOrder(Enum):
    """Ordre de tri."""
    ASC = "asc"
    DESC = "desc"
    RELEVANCE = "relevance"


class SuggestionType(Enum):
    """Types de suggestions."""
    COMPLETION = "completion"
    PHRASE = "phrase"
    TERM = "term"
    DID_YOU_MEAN = "did_you_mean"


class QueryType(Enum):
    """Types de requêtes."""
    MATCH = "match"
    MATCH_PHRASE = "match_phrase"
    MULTI_MATCH = "multi_match"
    TERM = "term"
    RANGE = "range"
    PREFIX = "prefix"
    WILDCARD = "wildcard"
    FUZZY = "fuzzy"
    BOOL = "bool"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class FieldMapping:
    """Mapping d'un champ indexé."""
    name: str
    field_type: FieldType
    analyzer: Optional[AnalyzerType] = None

    # Options
    searchable: bool = True
    filterable: bool = True
    sortable: bool = False
    facetable: bool = False

    # Boost de pertinence
    boost: float = 1.0

    # Copie vers un champ combiné
    copy_to: Optional[str] = None

    # Champs imbriqués
    nested_fields: List["FieldMapping"] = field(default_factory=list)


@dataclass
class IndexDefinition:
    """Définition d'un index de recherche."""
    id: str
    tenant_id: str
    name: str
    entity_type: str  # Ex: "product", "customer", "order"

    # Mapping des champs
    field_mappings: List[FieldMapping] = field(default_factory=list)

    # Analyseur par défaut
    default_analyzer: AnalyzerType = AnalyzerType.FRENCH

    # Configuration
    refresh_interval_seconds: int = 1
    number_of_shards: int = 1
    number_of_replicas: int = 0

    # Synonymes
    synonyms: Dict[str, List[str]] = field(default_factory=dict)

    # État
    status: IndexStatus = IndexStatus.ACTIVE
    document_count: int = 0
    size_bytes: int = 0

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    last_reindex_at: Optional[datetime] = None


@dataclass
class IndexedDocument:
    """Document indexé."""
    id: str
    tenant_id: str
    index_id: str
    entity_id: str
    entity_type: str

    # Contenu
    fields: Dict[str, Any] = field(default_factory=dict)

    # Champ combiné pour recherche full-text
    _all_text: str = ""

    # Vecteur de tokens (simplifié)
    tokens: List[str] = field(default_factory=list)

    # Métadonnées
    indexed_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: int = 1


@dataclass
class SearchQuery:
    """Requête de recherche."""
    query_text: str
    query_type: QueryType = QueryType.MULTI_MATCH

    # Champs à rechercher
    fields: List[str] = field(default_factory=list)

    # Filtres
    filters: Dict[str, Any] = field(default_factory=dict)
    range_filters: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)

    # Pagination
    offset: int = 0
    limit: int = 20

    # Tri
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.RELEVANCE

    # Options
    highlight: bool = True
    highlight_fields: List[str] = field(default_factory=list)
    facets: List[str] = field(default_factory=list)

    # Fuzzy
    fuzziness: int = 0  # 0 = exact, 1-2 = tolérance erreurs


@dataclass
class SearchHit:
    """Résultat de recherche."""
    document_id: str
    entity_id: str
    entity_type: str
    score: float

    # Données
    source: Dict[str, Any] = field(default_factory=dict)

    # Highlights
    highlights: Dict[str, List[str]] = field(default_factory=dict)

    # Explication du score (optionnel)
    explanation: Optional[str] = None


@dataclass
class FacetBucket:
    """Bucket pour une facette."""
    value: Any
    count: int
    selected: bool = False


@dataclass
class FacetResult:
    """Résultat de facette."""
    field: str
    buckets: List[FacetBucket] = field(default_factory=list)


@dataclass
class SearchResult:
    """Résultat de recherche complet."""
    query: SearchQuery
    total_hits: int
    hits: List[SearchHit] = field(default_factory=list)
    facets: Dict[str, FacetResult] = field(default_factory=dict)

    # Statistiques
    took_ms: int = 0
    timed_out: bool = False

    # Suggestions
    suggestions: List[str] = field(default_factory=list)


@dataclass
class Suggestion:
    """Suggestion de recherche."""
    text: str
    score: float
    suggestion_type: SuggestionType
    highlighted: Optional[str] = None
    frequency: int = 0


@dataclass
class SearchHistory:
    """Historique de recherche."""
    id: str
    tenant_id: str
    user_id: Optional[str]

    # Requête
    query_text: str
    filters_used: Dict[str, Any] = field(default_factory=dict)

    # Résultat
    result_count: int = 0
    clicked_results: List[str] = field(default_factory=list)

    # Timestamp
    searched_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReindexJob:
    """Job de réindexation."""
    id: str
    tenant_id: str
    index_id: str

    # Progression
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0

    # État
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_documents == 0:
            return 0.0
        return (self.processed_documents / self.total_documents) * 100


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class SearchService:
    """Service de recherche et indexation."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (à remplacer par Elasticsearch/Meilisearch)
        self._indexes: Dict[str, IndexDefinition] = {}
        self._documents: Dict[str, IndexedDocument] = {}
        self._search_history: List[SearchHistory] = []
        self._reindex_jobs: Dict[str, ReindexJob] = {}

        # Index inversé simplifié (token -> doc_ids)
        self._inverted_index: Dict[str, Dict[str, Set[str]]] = {}

        # Suggestions (terme -> fréquence)
        self._term_frequencies: Dict[str, int] = {}

        # Stopwords français
        self._stopwords = {
            "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou",
            "mais", "donc", "car", "ni", "que", "qui", "quoi", "dont",
            "ce", "cette", "ces", "son", "sa", "ses", "mon", "ma", "mes",
            "ton", "ta", "tes", "notre", "nos", "votre", "vos", "leur", "leurs",
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
            "ne", "pas", "plus", "moins", "très", "bien", "mal",
            "sur", "sous", "dans", "avec", "sans", "pour", "par", "en", "à",
            "est", "sont", "était", "été", "être", "avoir", "fait", "faire",
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
    ) -> IndexDefinition:
        """Crée un nouvel index."""
        index = IndexDefinition(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            entity_type=entity_type,
            field_mappings=field_mappings,
            default_analyzer=kwargs.get("default_analyzer", AnalyzerType.FRENCH),
            refresh_interval_seconds=kwargs.get("refresh_interval_seconds", 1),
            synonyms=kwargs.get("synonyms", {}),
        )

        self._indexes[index.id] = index

        # Initialiser l'index inversé
        self._inverted_index[index.id] = {}

        return index

    def get_index(self, index_id: str) -> Optional[IndexDefinition]:
        """Récupère un index."""
        index = self._indexes.get(index_id)
        if index and index.tenant_id == self.tenant_id:
            return index
        return None

    def get_index_by_name(self, name: str) -> Optional[IndexDefinition]:
        """Récupère un index par son nom."""
        for index in self._indexes.values():
            if index.tenant_id == self.tenant_id and index.name == name:
                return index
        return None

    def list_indexes(self) -> List[IndexDefinition]:
        """Liste tous les index."""
        return [
            idx for idx in self._indexes.values()
            if idx.tenant_id == self.tenant_id
        ]

    def delete_index(self, index_id: str) -> bool:
        """Supprime un index et ses documents."""
        index = self.get_index(index_id)
        if not index:
            return False

        # Supprimer les documents
        to_delete = [
            doc_id for doc_id, doc in self._documents.items()
            if doc.index_id == index_id
        ]
        for doc_id in to_delete:
            del self._documents[doc_id]

        # Supprimer l'index inversé
        if index_id in self._inverted_index:
            del self._inverted_index[index_id]

        # Supprimer l'index
        del self._indexes[index_id]

        return True

    def update_synonyms(
        self,
        index_id: str,
        synonyms: Dict[str, List[str]]
    ) -> bool:
        """Met à jour les synonymes d'un index."""
        index = self.get_index(index_id)
        if not index:
            return False

        index.synonyms = synonyms
        index.updated_at = datetime.now()
        return True

    # ========================================
    # INDEXATION
    # ========================================

    def index_document(
        self,
        index_id: str,
        entity_id: str,
        fields: Dict[str, Any]
    ) -> Optional[IndexedDocument]:
        """Indexe un document."""
        index = self.get_index(index_id)
        if not index:
            return None

        # Vérifier si le document existe déjà
        existing = self._find_document(index_id, entity_id)

        doc = IndexedDocument(
            id=existing.id if existing else str(uuid4()),
            tenant_id=self.tenant_id,
            index_id=index_id,
            entity_id=entity_id,
            entity_type=index.entity_type,
            fields=fields,
            version=(existing.version + 1) if existing else 1,
        )

        # Construire le texte combiné
        text_parts = []
        for mapping in index.field_mappings:
            if mapping.field_type == FieldType.TEXT and mapping.name in fields:
                value = str(fields[mapping.name])
                text_parts.append(value)
                if mapping.boost > 1:
                    # Répéter pour booster
                    for _ in range(int(mapping.boost)):
                        text_parts.append(value)

        doc._all_text = " ".join(text_parts)

        # Tokeniser
        doc.tokens = self._tokenize(doc._all_text, index.default_analyzer)

        # Appliquer les synonymes
        doc.tokens = self._expand_synonyms(doc.tokens, index.synonyms)

        # Mettre à jour l'index inversé
        if existing:
            self._remove_from_inverted_index(index_id, existing)
        self._add_to_inverted_index(index_id, doc)

        # Stocker
        self._documents[doc.id] = doc

        # Mettre à jour le compteur de fréquence des termes
        for token in set(doc.tokens):
            self._term_frequencies[token] = self._term_frequencies.get(token, 0) + 1

        # Mettre à jour les stats de l'index
        index.document_count = sum(
            1 for d in self._documents.values() if d.index_id == index_id
        )
        index.updated_at = datetime.now()

        return doc

    def _find_document(self, index_id: str, entity_id: str) -> Optional[IndexedDocument]:
        """Trouve un document par entité."""
        for doc in self._documents.values():
            if doc.index_id == index_id and doc.entity_id == entity_id:
                return doc
        return None

    def _tokenize(self, text: str, analyzer: AnalyzerType) -> List[str]:
        """Tokenise le texte selon l'analyseur."""
        if not text:
            return []

        # Normaliser (accents, casse)
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ASCII', 'ignore').decode('ASCII')
        text = text.lower()

        # Tokeniser
        if analyzer == AnalyzerType.WHITESPACE:
            tokens = text.split()
        elif analyzer == AnalyzerType.KEYWORD:
            tokens = [text.strip()]
        else:
            # Standard/French: split sur non-alphanum
            tokens = re.findall(r'\b[a-z0-9]+\b', text)

        # Filtrer les stopwords (sauf pour keyword)
        if analyzer in (AnalyzerType.STANDARD, AnalyzerType.FRENCH):
            tokens = [t for t in tokens if t not in self._stopwords and len(t) > 1]

        # Stemming simplifié pour le français
        if analyzer == AnalyzerType.FRENCH:
            tokens = [self._stem_french(t) for t in tokens]

        return tokens

    def _stem_french(self, word: str) -> str:
        """Stemming simplifié pour le français."""
        # Suffixes courants à supprimer
        suffixes = [
            'issements', 'issement', 'ations', 'ation', 'ements', 'ement',
            'iques', 'ique', 'ables', 'able', 'ibles', 'ible',
            'eurs', 'eur', 'euses', 'euse', 'ants', 'ant', 'ents', 'ent',
            'ions', 'ion', 'ites', 'ite', 'ives', 'ive',
            'aux', 'al', 'els', 'el', 'eux',
            'es', 's', 'e'
        ]

        for suffix in suffixes:
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                return word[:-len(suffix)]
        return word

    def _expand_synonyms(
        self,
        tokens: List[str],
        synonyms: Dict[str, List[str]]
    ) -> List[str]:
        """Étend les tokens avec les synonymes."""
        expanded = list(tokens)
        for token in tokens:
            if token in synonyms:
                expanded.extend(synonyms[token])
        return expanded

    def _add_to_inverted_index(self, index_id: str, doc: IndexedDocument) -> None:
        """Ajoute un document à l'index inversé."""
        if index_id not in self._inverted_index:
            self._inverted_index[index_id] = {}

        inv_idx = self._inverted_index[index_id]
        for token in set(doc.tokens):
            if token not in inv_idx:
                inv_idx[token] = set()
            inv_idx[token].add(doc.id)

    def _remove_from_inverted_index(self, index_id: str, doc: IndexedDocument) -> None:
        """Supprime un document de l'index inversé."""
        if index_id not in self._inverted_index:
            return

        inv_idx = self._inverted_index[index_id]
        for token in set(doc.tokens):
            if token in inv_idx:
                inv_idx[token].discard(doc.id)
                if not inv_idx[token]:
                    del inv_idx[token]

    def delete_document(self, index_id: str, entity_id: str) -> bool:
        """Supprime un document de l'index."""
        doc = self._find_document(index_id, entity_id)
        if not doc:
            return False

        self._remove_from_inverted_index(index_id, doc)
        del self._documents[doc.id]

        # Mettre à jour les stats
        index = self.get_index(index_id)
        if index:
            index.document_count -= 1
            index.updated_at = datetime.now()

        return True

    def bulk_index(
        self,
        index_id: str,
        documents: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Indexe plusieurs documents.
        Retourne (succès, échecs).
        """
        success = 0
        failures = 0

        for doc_data in documents:
            entity_id = doc_data.pop("_id", str(uuid4()))
            try:
                result = self.index_document(index_id, entity_id, doc_data)
                if result:
                    success += 1
                else:
                    failures += 1
            except Exception:
                failures += 1

        return success, failures

    # ========================================
    # RECHERCHE
    # ========================================

    def search(
        self,
        index_id: str,
        query: SearchQuery,
        user_id: Optional[str] = None
    ) -> SearchResult:
        """Effectue une recherche."""
        import time
        start_time = time.time()

        index = self.get_index(index_id)
        if not index:
            return SearchResult(query=query, total_hits=0)

        # Tokeniser la requête
        query_tokens = self._tokenize(query.query_text, index.default_analyzer)
        query_tokens = self._expand_synonyms(query_tokens, index.synonyms)

        # Appliquer le fuzziness
        if query.fuzziness > 0:
            query_tokens = self._apply_fuzziness(query_tokens, index_id, query.fuzziness)

        # Trouver les documents correspondants
        matching_doc_ids = self._find_matching_documents(index_id, query_tokens, query.query_type)

        # Appliquer les filtres
        if query.filters:
            matching_doc_ids = self._apply_filters(matching_doc_ids, query.filters)

        if query.range_filters:
            matching_doc_ids = self._apply_range_filters(matching_doc_ids, query.range_filters)

        # Scorer et trier
        scored_hits = self._score_documents(
            matching_doc_ids, query_tokens, query.fields, index
        )

        # Trier
        if query.sort_order == SortOrder.RELEVANCE:
            scored_hits.sort(key=lambda x: x[1], reverse=True)
        elif query.sort_by:
            scored_hits.sort(
                key=lambda x: self._get_sort_value(x[0], query.sort_by),
                reverse=(query.sort_order == SortOrder.DESC)
            )

        total_hits = len(scored_hits)

        # Paginer
        paginated = scored_hits[query.offset:query.offset + query.limit]

        # Construire les hits
        hits = []
        for doc_id, score in paginated:
            doc = self._documents.get(doc_id)
            if doc:
                hit = SearchHit(
                    document_id=doc.id,
                    entity_id=doc.entity_id,
                    entity_type=doc.entity_type,
                    score=score,
                    source=doc.fields,
                )

                # Highlights
                if query.highlight:
                    hit.highlights = self._generate_highlights(
                        doc, query_tokens, query.highlight_fields or list(doc.fields.keys())
                    )

                hits.append(hit)

        # Facettes
        facets = {}
        if query.facets:
            all_matching_docs = [self._documents.get(did) for did, _ in scored_hits]
            all_matching_docs = [d for d in all_matching_docs if d]
            facets = self._compute_facets(all_matching_docs, query.facets)

        # Suggestions
        suggestions = self._generate_suggestions(query.query_text, index_id) if not hits else []

        elapsed_ms = int((time.time() - start_time) * 1000)

        result = SearchResult(
            query=query,
            total_hits=total_hits,
            hits=hits,
            facets=facets,
            took_ms=elapsed_ms,
            suggestions=suggestions,
        )

        # Enregistrer dans l'historique
        self._record_search(query, total_hits, user_id)

        return result

    def _find_matching_documents(
        self,
        index_id: str,
        tokens: List[str],
        query_type: QueryType
    ) -> Set[str]:
        """Trouve les documents correspondant aux tokens."""
        if index_id not in self._inverted_index:
            return set()

        inv_idx = self._inverted_index[index_id]

        if not tokens:
            # Retourner tous les documents de l'index
            return set(
                doc.id for doc in self._documents.values()
                if doc.index_id == index_id
            )

        if query_type == QueryType.MATCH:
            # OR: union de tous les tokens
            result = set()
            for token in tokens:
                if token in inv_idx:
                    result.update(inv_idx[token])
            return result

        elif query_type in (QueryType.MATCH_PHRASE, QueryType.MULTI_MATCH):
            # AND: intersection (simplifié)
            if not tokens:
                return set()

            result = None
            for token in tokens:
                if token in inv_idx:
                    if result is None:
                        result = inv_idx[token].copy()
                    else:
                        result &= inv_idx[token]
                else:
                    return set()

            return result or set()

        elif query_type == QueryType.PREFIX:
            # Préfixe: trouve tous les tokens commençant par
            result = set()
            for token in tokens:
                for idx_token in inv_idx:
                    if idx_token.startswith(token):
                        result.update(inv_idx[idx_token])
            return result

        elif query_type == QueryType.WILDCARD:
            # Wildcard simplifié (* = n'importe quoi)
            import fnmatch
            result = set()
            for token in tokens:
                pattern = token.replace('*', '.*')
                for idx_token in inv_idx:
                    if re.match(pattern, idx_token):
                        result.update(inv_idx[idx_token])
            return result

        return set()

    def _apply_fuzziness(
        self,
        tokens: List[str],
        index_id: str,
        fuzziness: int
    ) -> List[str]:
        """Applique la recherche floue aux tokens."""
        if index_id not in self._inverted_index:
            return tokens

        inv_idx = self._inverted_index[index_id]
        expanded = list(tokens)

        for token in tokens:
            # Trouver les tokens similaires
            for idx_token in inv_idx:
                if self._levenshtein_distance(token, idx_token) <= fuzziness:
                    if idx_token not in expanded:
                        expanded.append(idx_token)

        return expanded

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calcule la distance de Levenshtein entre deux chaînes."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _apply_filters(
        self,
        doc_ids: Set[str],
        filters: Dict[str, Any]
    ) -> Set[str]:
        """Applique les filtres exacts."""
        result = set()

        for doc_id in doc_ids:
            doc = self._documents.get(doc_id)
            if not doc:
                continue

            match = True
            for field, value in filters.items():
                doc_value = doc.fields.get(field)
                if isinstance(value, list):
                    if doc_value not in value:
                        match = False
                        break
                else:
                    if doc_value != value:
                        match = False
                        break

            if match:
                result.add(doc_id)

        return result

    def _apply_range_filters(
        self,
        doc_ids: Set[str],
        range_filters: Dict[str, Tuple[Any, Any]]
    ) -> Set[str]:
        """Applique les filtres de plage."""
        result = set()

        for doc_id in doc_ids:
            doc = self._documents.get(doc_id)
            if not doc:
                continue

            match = True
            for field, (min_val, max_val) in range_filters.items():
                doc_value = doc.fields.get(field)
                if doc_value is None:
                    match = False
                    break

                if min_val is not None and doc_value < min_val:
                    match = False
                    break
                if max_val is not None and doc_value > max_val:
                    match = False
                    break

            if match:
                result.add(doc_id)

        return result

    def _score_documents(
        self,
        doc_ids: Set[str],
        query_tokens: List[str],
        query_fields: List[str],
        index: IndexDefinition
    ) -> List[Tuple[str, float]]:
        """Score les documents (TF-IDF simplifié)."""
        total_docs = index.document_count or 1
        scores = []

        for doc_id in doc_ids:
            doc = self._documents.get(doc_id)
            if not doc:
                continue

            score = 0.0
            for token in query_tokens:
                # Term Frequency
                tf = doc.tokens.count(token)

                # Inverse Document Frequency
                if self._inverted_index.get(index.id, {}).get(token):
                    df = len(self._inverted_index[index.id][token])
                    idf = 1 + (total_docs / (1 + df))
                else:
                    idf = 1

                score += tf * idf

                # Boost si présent dans un champ spécifique
                for mapping in index.field_mappings:
                    if mapping.name in doc.fields:
                        field_value = str(doc.fields[mapping.name]).lower()
                        if token in field_value:
                            score += mapping.boost

            scores.append((doc_id, score))

        return scores

    def _get_sort_value(self, doc_id: str, field: str) -> Any:
        """Récupère la valeur de tri d'un document."""
        doc = self._documents.get(doc_id)
        if doc:
            return doc.fields.get(field, "")
        return ""

    def _generate_highlights(
        self,
        doc: IndexedDocument,
        query_tokens: List[str],
        fields: List[str]
    ) -> Dict[str, List[str]]:
        """Génère les highlights pour un document."""
        highlights = {}

        for field in fields:
            if field not in doc.fields:
                continue

            value = str(doc.fields[field])
            highlighted_fragments = []

            # Trouver les occurrences des tokens
            for token in query_tokens:
                pattern = re.compile(re.escape(token), re.IGNORECASE)
                matches = list(pattern.finditer(value))

                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(value), match.end() + 50)
                    fragment = value[start:end]

                    # Ajouter les marqueurs
                    highlighted = pattern.sub(f"<em>{match.group()}</em>", fragment)
                    if start > 0:
                        highlighted = "..." + highlighted
                    if end < len(value):
                        highlighted = highlighted + "..."

                    highlighted_fragments.append(highlighted)

            if highlighted_fragments:
                highlights[field] = highlighted_fragments[:3]  # Max 3 fragments

        return highlights

    def _compute_facets(
        self,
        documents: List[IndexedDocument],
        facet_fields: List[str]
    ) -> Dict[str, FacetResult]:
        """Calcule les facettes."""
        facets = {}

        for field in facet_fields:
            value_counts: Dict[Any, int] = {}

            for doc in documents:
                value = doc.fields.get(field)
                if value is not None:
                    if isinstance(value, list):
                        for v in value:
                            value_counts[v] = value_counts.get(v, 0) + 1
                    else:
                        value_counts[value] = value_counts.get(value, 0) + 1

            buckets = [
                FacetBucket(value=v, count=c)
                for v, c in sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
            ]

            facets[field] = FacetResult(field=field, buckets=buckets[:20])

        return facets

    def _generate_suggestions(self, query_text: str, index_id: str) -> List[str]:
        """Génère des suggestions de recherche."""
        if not query_text:
            return []

        suggestions = []
        query_lower = query_text.lower()

        # Chercher des termes similaires
        for term, freq in sorted(self._term_frequencies.items(), key=lambda x: x[1], reverse=True):
            if term.startswith(query_lower) or self._levenshtein_distance(term, query_lower) <= 2:
                if term != query_lower:
                    suggestions.append(term)
                    if len(suggestions) >= 5:
                        break

        return suggestions

    def _record_search(
        self,
        query: SearchQuery,
        result_count: int,
        user_id: Optional[str]
    ) -> None:
        """Enregistre la recherche dans l'historique."""
        history = SearchHistory(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            user_id=user_id,
            query_text=query.query_text,
            filters_used=query.filters,
            result_count=result_count,
        )
        self._search_history.append(history)

    # ========================================
    # SUGGESTIONS ET AUTOCOMPLÉTION
    # ========================================

    def suggest(
        self,
        prefix: str,
        index_id: str,
        limit: int = 10
    ) -> List[Suggestion]:
        """Autocomplétion basée sur un préfixe."""
        if not prefix or len(prefix) < 2:
            return []

        index = self.get_index(index_id)
        if not index:
            return []

        prefix_lower = prefix.lower()
        suggestions = []

        # Rechercher dans les termes indexés
        for term, freq in self._term_frequencies.items():
            if term.startswith(prefix_lower):
                suggestions.append(Suggestion(
                    text=term,
                    score=freq,
                    suggestion_type=SuggestionType.COMPLETION,
                    frequency=freq,
                ))

        # Trier par fréquence
        suggestions.sort(key=lambda x: x.frequency, reverse=True)

        return suggestions[:limit]

    def did_you_mean(self, query_text: str, index_id: str) -> Optional[str]:
        """Suggestion 'Vouliez-vous dire...'."""
        if not query_text:
            return None

        tokens = self._tokenize(query_text, AnalyzerType.FRENCH)
        corrections = []

        for token in tokens:
            best_match = None
            best_distance = float('inf')

            for term in self._term_frequencies:
                distance = self._levenshtein_distance(token, term)
                if 0 < distance <= 2 and distance < best_distance:
                    best_distance = distance
                    best_match = term

            if best_match:
                corrections.append(best_match)
            else:
                corrections.append(token)

        corrected = " ".join(corrections)
        if corrected != query_text.lower():
            return corrected

        return None

    # ========================================
    # RÉINDEXATION
    # ========================================

    def start_reindex(self, index_id: str) -> Optional[ReindexJob]:
        """Démarre un job de réindexation."""
        index = self.get_index(index_id)
        if not index:
            return None

        job = ReindexJob(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            index_id=index_id,
            total_documents=index.document_count,
            started_at=datetime.now(),
        )

        self._reindex_jobs[job.id] = job
        index.status = IndexStatus.REBUILDING

        # En production, lancer en background
        # Ici, simuler immédiatement
        self._perform_reindex(job)

        return job

    def _perform_reindex(self, job: ReindexJob) -> None:
        """Effectue la réindexation."""
        index = self.get_index(job.index_id)
        if not index:
            return

        # Reconstruire l'index inversé
        self._inverted_index[job.index_id] = {}

        docs_to_reindex = [
            d for d in self._documents.values()
            if d.index_id == job.index_id
        ]

        for doc in docs_to_reindex:
            try:
                # Re-tokeniser
                doc.tokens = self._tokenize(doc._all_text, index.default_analyzer)
                doc.tokens = self._expand_synonyms(doc.tokens, index.synonyms)

                # Reconstruire l'index inversé
                self._add_to_inverted_index(job.index_id, doc)

                job.processed_documents += 1
            except Exception:
                job.failed_documents += 1

        job.completed_at = datetime.now()
        index.status = IndexStatus.ACTIVE
        index.last_reindex_at = datetime.now()

    def get_reindex_job(self, job_id: str) -> Optional[ReindexJob]:
        """Récupère un job de réindexation."""
        return self._reindex_jobs.get(job_id)

    # ========================================
    # HISTORIQUE
    # ========================================

    def get_search_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SearchHistory]:
        """Récupère l'historique de recherche."""
        history = [
            h for h in self._search_history
            if h.tenant_id == self.tenant_id
        ]

        if user_id:
            history = [h for h in history if h.user_id == user_id]

        return sorted(history, key=lambda x: x.searched_at, reverse=True)[:limit]

    def get_popular_searches(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Récupère les recherches populaires."""
        query_counts: Dict[str, int] = {}

        for h in self._search_history:
            if h.tenant_id == self.tenant_id:
                query_counts[h.query_text] = query_counts.get(h.query_text, 0) + 1

        return sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:limit]


# ============================================================
# FACTORY
# ============================================================

def create_search_service(tenant_id: str) -> SearchService:
    """Crée une instance du service Search."""
    return SearchService(tenant_id=tenant_id)
