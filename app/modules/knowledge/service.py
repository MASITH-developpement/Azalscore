"""
Service Knowledge Base - GAP-068

Base de connaissances:
- Articles et documentation
- Catégories et tags
- Recherche full-text
- Versioning des articles
- Feedback et notation
- FAQ dynamique
- Analytics de lecture
- Multi-langue
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from uuid import uuid4
import re


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class ArticleStatus(str, Enum):
    """Statut d'un article."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ArticleType(str, Enum):
    """Type d'article."""
    ARTICLE = "article"
    FAQ = "faq"
    TUTORIAL = "tutorial"
    GUIDE = "guide"
    TROUBLESHOOTING = "troubleshooting"
    GLOSSARY = "glossary"
    RELEASE_NOTE = "release_note"


class Visibility(str, Enum):
    """Visibilité."""
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


class FeedbackType(str, Enum):
    """Type de feedback."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    COMMENT = "comment"
    SUGGESTION = "suggestion"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Category:
    """Catégorie d'articles."""
    id: str
    tenant_id: str
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    order: int = 0
    article_count: int = 0
    is_visible: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Article:
    """Un article."""
    id: str
    tenant_id: str
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    article_type: ArticleType = ArticleType.ARTICLE
    status: ArticleStatus = ArticleStatus.DRAFT
    visibility: Visibility = Visibility.PUBLIC
    category_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    language: str = "fr"
    translations: Dict[str, str] = field(default_factory=dict)  # lang -> article_id
    featured_image: Optional[str] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    reviewer_id: Optional[str] = None
    version: int = 1
    reading_time_minutes: int = 0
    view_count: int = 0
    unique_views: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    comment_count: int = 0
    search_keywords: List[str] = field(default_factory=list)
    related_articles: List[str] = field(default_factory=list)
    attachments: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ArticleVersion:
    """Version d'un article."""
    id: str
    article_id: str
    version: int
    title: str
    content: str
    change_summary: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FAQItem:
    """Item FAQ."""
    id: str
    tenant_id: str
    question: str
    answer: str
    category_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    order: int = 0
    is_featured: bool = False
    view_count: int = 0
    helpful_count: int = 0
    language: str = "fr"
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)
    status: ArticleStatus = ArticleStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Feedback:
    """Feedback sur un article."""
    id: str
    article_id: str
    user_id: Optional[str] = None
    feedback_type: FeedbackType = FeedbackType.HELPFUL
    comment: Optional[str] = None
    rating: Optional[int] = None  # 1-5
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Résultat de recherche."""
    article_id: str
    title: str
    excerpt: str
    category: Optional[str] = None
    score: float = 0.0
    highlights: List[str] = field(default_factory=list)


@dataclass
class ViewLog:
    """Log de consultation."""
    id: str
    article_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    time_spent_seconds: int = 0
    scroll_depth_percent: int = 0
    viewed_at: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeStats:
    """Statistiques de la base."""
    tenant_id: str
    total_articles: int = 0
    published_articles: int = 0
    draft_articles: int = 0
    total_views: int = 0
    total_unique_views: int = 0
    avg_time_on_page_seconds: int = 0
    helpful_rate: Decimal = Decimal("0")
    top_articles: List[Dict[str, Any]] = field(default_factory=list)
    top_searches: List[Dict[str, Any]] = field(default_factory=list)
    articles_by_category: Dict[str, int] = field(default_factory=dict)
    views_by_day: Dict[str, int] = field(default_factory=dict)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class KnowledgeService:
    """Service de base de connaissances."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (simulation)
        self._categories: Dict[str, Category] = {}
        self._articles: Dict[str, Article] = {}
        self._versions: Dict[str, List[ArticleVersion]] = {}
        self._faqs: Dict[str, FAQItem] = {}
        self._feedback: Dict[str, Feedback] = {}
        self._view_logs: Dict[str, ViewLog] = {}
        self._search_logs: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Catégories
    # -------------------------------------------------------------------------

    def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
        **kwargs
    ) -> Category:
        """Crée une catégorie."""
        category_id = str(uuid4())
        slug = self._generate_slug(name)

        category = Category(
            id=category_id,
            tenant_id=self.tenant_id,
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            **kwargs
        )

        self._categories[category_id] = category
        return category

    def get_category(self, category_id: str) -> Optional[Category]:
        """Récupère une catégorie."""
        cat = self._categories.get(category_id)
        if cat and cat.tenant_id == self.tenant_id:
            return cat
        return None

    def list_categories(
        self,
        parent_id: Optional[str] = None,
        include_hidden: bool = False
    ) -> List[Category]:
        """Liste les catégories."""
        results = []

        for cat in self._categories.values():
            if cat.tenant_id != self.tenant_id:
                continue
            if not include_hidden and not cat.is_visible:
                continue
            if parent_id is not None and cat.parent_id != parent_id:
                continue
            results.append(cat)

        results.sort(key=lambda x: (x.order, x.name))
        return results

    def get_category_tree(self) -> List[Dict[str, Any]]:
        """Récupère l'arborescence des catégories."""
        def build_tree(parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
            children = []
            for cat in self._categories.values():
                if cat.tenant_id != self.tenant_id:
                    continue
                if cat.parent_id != parent_id:
                    continue
                if not cat.is_visible:
                    continue

                node = {
                    "id": cat.id,
                    "name": cat.name,
                    "slug": cat.slug,
                    "article_count": cat.article_count,
                    "children": build_tree(cat.id)
                }
                children.append(node)

            children.sort(key=lambda x: x["name"])
            return children

        return build_tree(None)

    # -------------------------------------------------------------------------
    # Articles
    # -------------------------------------------------------------------------

    def create_article(
        self,
        title: str,
        content: str,
        article_type: ArticleType = ArticleType.ARTICLE,
        author_id: Optional[str] = None,
        author_name: Optional[str] = None,
        **kwargs
    ) -> Article:
        """Crée un article."""
        article_id = str(uuid4())
        slug = self._generate_slug(title)

        # Calculer temps de lecture (environ 200 mots/minute)
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)

        # Générer extrait
        excerpt = kwargs.pop('excerpt', None)
        if not excerpt:
            excerpt = self._generate_excerpt(content)

        article = Article(
            id=article_id,
            tenant_id=self.tenant_id,
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            article_type=article_type,
            author_id=author_id,
            author_name=author_name,
            reading_time_minutes=reading_time,
            **kwargs
        )

        self._articles[article_id] = article

        # Créer première version
        self._create_version(article, "Initial version")

        # Mettre à jour compteur catégorie
        if article.category_id:
            cat = self.get_category(article.category_id)
            if cat:
                cat.article_count += 1

        return article

    def get_article(self, article_id: str) -> Optional[Article]:
        """Récupère un article."""
        article = self._articles.get(article_id)
        if article and article.tenant_id == self.tenant_id:
            return article
        return None

    def get_article_by_slug(self, slug: str) -> Optional[Article]:
        """Récupère un article par son slug."""
        for article in self._articles.values():
            if article.tenant_id == self.tenant_id and article.slug == slug:
                return article
        return None

    def update_article(
        self,
        article_id: str,
        change_summary: Optional[str] = None,
        **updates
    ) -> Optional[Article]:
        """Met à jour un article."""
        article = self.get_article(article_id)
        if not article:
            return None

        # Sauvegarder ancienne version si contenu change
        if 'content' in updates or 'title' in updates:
            self._create_version(article, change_summary or "Content update")
            article.version += 1

        for key, value in updates.items():
            if hasattr(article, key):
                setattr(article, key, value)

        # Recalculer temps de lecture si contenu change
        if 'content' in updates:
            word_count = len(article.content.split())
            article.reading_time_minutes = max(1, word_count // 200)

        article.updated_at = datetime.now()

        return article

    def publish_article(self, article_id: str) -> Optional[Article]:
        """Publie un article."""
        article = self.get_article(article_id)
        if not article:
            return None

        article.status = ArticleStatus.PUBLISHED
        article.published_at = datetime.now()
        article.updated_at = datetime.now()

        return article

    def archive_article(self, article_id: str) -> Optional[Article]:
        """Archive un article."""
        article = self.get_article(article_id)
        if not article:
            return None

        article.status = ArticleStatus.ARCHIVED
        article.updated_at = datetime.now()

        # Mettre à jour compteur catégorie
        if article.category_id:
            cat = self.get_category(article.category_id)
            if cat:
                cat.article_count = max(0, cat.article_count - 1)

        return article

    def list_articles(
        self,
        *,
        category_id: Optional[str] = None,
        article_type: Optional[ArticleType] = None,
        status: Optional[ArticleStatus] = None,
        visibility: Optional[Visibility] = None,
        tags: Optional[List[str]] = None,
        author_id: Optional[str] = None,
        language: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Article], int]:
        """Liste les articles."""
        results = []

        for article in self._articles.values():
            if article.tenant_id != self.tenant_id:
                continue
            if category_id and article.category_id != category_id:
                continue
            if article_type and article.article_type != article_type:
                continue
            if status and article.status != status:
                continue
            if visibility and article.visibility != visibility:
                continue
            if author_id and article.author_id != author_id:
                continue
            if language and article.language != language:
                continue
            if tags:
                if not any(tag in article.tags for tag in tags):
                    continue
            if search:
                search_lower = search.lower()
                if (search_lower not in article.title.lower() and
                    search_lower not in article.content.lower()):
                    continue

            results.append(article)

        # Trier par date de publication (plus récent d'abord)
        results.sort(key=lambda x: x.published_at or x.created_at, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    def get_related_articles(
        self,
        article_id: str,
        limit: int = 5
    ) -> List[Article]:
        """Récupère les articles liés."""
        article = self.get_article(article_id)
        if not article:
            return []

        # Articles explicitement liés
        related = []
        for related_id in article.related_articles[:limit]:
            rel_article = self.get_article(related_id)
            if rel_article and rel_article.status == ArticleStatus.PUBLISHED:
                related.append(rel_article)

        # Compléter avec des articles de même catégorie/tags
        if len(related) < limit:
            for other in self._articles.values():
                if other.id == article_id:
                    continue
                if other.tenant_id != self.tenant_id:
                    continue
                if other.status != ArticleStatus.PUBLISHED:
                    continue
                if other.id in [r.id for r in related]:
                    continue

                # Même catégorie ou tags communs
                if (other.category_id == article.category_id or
                    any(tag in article.tags for tag in other.tags)):
                    related.append(other)
                    if len(related) >= limit:
                        break

        return related

    def _create_version(self, article: Article, change_summary: str):
        """Crée une version."""
        version_id = str(uuid4())

        version = ArticleVersion(
            id=version_id,
            article_id=article.id,
            version=article.version,
            title=article.title,
            content=article.content,
            change_summary=change_summary,
            created_by=article.author_id
        )

        if article.id not in self._versions:
            self._versions[article.id] = []
        self._versions[article.id].append(version)

    def get_article_versions(self, article_id: str) -> List[ArticleVersion]:
        """Liste les versions d'un article."""
        return self._versions.get(article_id, [])

    def restore_version(
        self,
        article_id: str,
        version_number: int
    ) -> Optional[Article]:
        """Restaure une version."""
        article = self.get_article(article_id)
        if not article:
            return None

        versions = self._versions.get(article_id, [])
        target = None
        for v in versions:
            if v.version == version_number:
                target = v
                break

        if not target:
            return None

        article.title = target.title
        article.content = target.content
        article.version += 1
        article.updated_at = datetime.now()

        self._create_version(article, f"Restored from version {version_number}")

        return article

    # -------------------------------------------------------------------------
    # Recherche
    # -------------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        category_id: Optional[str] = None,
        article_type: Optional[ArticleType] = None,
        language: Optional[str] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """Recherche dans la base."""
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()

        # Logger la recherche
        self._search_logs.append({
            "query": query,
            "timestamp": datetime.now(),
            "results_count": 0
        })

        for article in self._articles.values():
            if article.tenant_id != self.tenant_id:
                continue
            if article.status != ArticleStatus.PUBLISHED:
                continue
            if category_id and article.category_id != category_id:
                continue
            if article_type and article.article_type != article_type:
                continue
            if language and article.language != language:
                continue

            # Calculer score
            score = 0.0
            highlights = []

            title_lower = article.title.lower()
            content_lower = article.content.lower()

            # Match exact dans le titre (score élevé)
            if query_lower in title_lower:
                score += 10.0
                highlights.append(article.title)

            # Match mots dans le titre
            for word in query_words:
                if word in title_lower:
                    score += 3.0

            # Match dans le contenu
            for word in query_words:
                count = content_lower.count(word)
                score += count * 0.5

                # Extraire highlights
                if count > 0 and len(highlights) < 3:
                    idx = content_lower.find(word)
                    start = max(0, idx - 50)
                    end = min(len(article.content), idx + len(word) + 50)
                    highlight = "..." + article.content[start:end] + "..."
                    highlights.append(highlight)

            # Match tags
            for tag in article.tags:
                if query_lower in tag.lower():
                    score += 2.0

            # Match keywords
            for keyword in article.search_keywords:
                if query_lower in keyword.lower():
                    score += 2.0

            if score > 0:
                # Récupérer nom catégorie
                category_name = None
                if article.category_id:
                    cat = self.get_category(article.category_id)
                    if cat:
                        category_name = cat.name

                results.append(SearchResult(
                    article_id=article.id,
                    title=article.title,
                    excerpt=article.excerpt or "",
                    category=category_name,
                    score=score,
                    highlights=highlights[:3]
                ))

        # Trier par score
        results.sort(key=lambda x: x.score, reverse=True)

        # Mettre à jour log
        if self._search_logs:
            self._search_logs[-1]["results_count"] = len(results)

        return results[:limit]

    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les recherches populaires."""
        search_counts = {}
        for log in self._search_logs:
            query = log["query"].lower()
            search_counts[query] = search_counts.get(query, 0) + 1

        sorted_searches = sorted(
            search_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"query": q, "count": c}
            for q, c in sorted_searches[:limit]
        ]

    # -------------------------------------------------------------------------
    # FAQ
    # -------------------------------------------------------------------------

    def create_faq(
        self,
        question: str,
        answer: str,
        category_id: Optional[str] = None,
        **kwargs
    ) -> FAQItem:
        """Crée une FAQ."""
        faq_id = str(uuid4())

        faq = FAQItem(
            id=faq_id,
            tenant_id=self.tenant_id,
            question=question,
            answer=answer,
            category_id=category_id,
            **kwargs
        )

        self._faqs[faq_id] = faq
        return faq

    def list_faqs(
        self,
        category_id: Optional[str] = None,
        featured_only: bool = False,
        language: Optional[str] = None
    ) -> List[FAQItem]:
        """Liste les FAQs."""
        results = []

        for faq in self._faqs.values():
            if faq.tenant_id != self.tenant_id:
                continue
            if faq.status != ArticleStatus.PUBLISHED:
                continue
            if category_id and faq.category_id != category_id:
                continue
            if featured_only and not faq.is_featured:
                continue
            if language and faq.language != language:
                continue
            results.append(faq)

        results.sort(key=lambda x: (not x.is_featured, x.order, -x.view_count))
        return results

    # -------------------------------------------------------------------------
    # Feedback
    # -------------------------------------------------------------------------

    def submit_feedback(
        self,
        article_id: str,
        feedback_type: FeedbackType,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
        rating: Optional[int] = None
    ) -> Optional[Feedback]:
        """Soumet un feedback."""
        article = self.get_article(article_id)
        if not article:
            return None

        feedback_id = str(uuid4())

        feedback = Feedback(
            id=feedback_id,
            article_id=article_id,
            user_id=user_id,
            feedback_type=feedback_type,
            comment=comment,
            rating=rating
        )

        self._feedback[feedback_id] = feedback

        # Mettre à jour compteurs
        if feedback_type == FeedbackType.HELPFUL:
            article.helpful_count += 1
        elif feedback_type == FeedbackType.NOT_HELPFUL:
            article.not_helpful_count += 1
        elif feedback_type == FeedbackType.COMMENT:
            article.comment_count += 1

        return feedback

    def list_feedback(
        self,
        article_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        unresolved_only: bool = False
    ) -> List[Feedback]:
        """Liste les feedbacks."""
        results = []

        for fb in self._feedback.values():
            article = self.get_article(fb.article_id)
            if not article:
                continue
            if article_id and fb.article_id != article_id:
                continue
            if feedback_type and fb.feedback_type != feedback_type:
                continue
            if unresolved_only and fb.is_resolved:
                continue
            results.append(fb)

        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def resolve_feedback(
        self,
        feedback_id: str,
        resolved_by: str
    ) -> Optional[Feedback]:
        """Résout un feedback."""
        fb = self._feedback.get(feedback_id)
        if not fb:
            return None

        fb.is_resolved = True
        fb.resolved_by = resolved_by
        fb.resolved_at = datetime.now()

        return fb

    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------

    def record_view(
        self,
        article_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[ViewLog]:
        """Enregistre une vue."""
        article = self.get_article(article_id)
        if not article:
            return None

        log_id = str(uuid4())

        log = ViewLog(
            id=log_id,
            article_id=article_id,
            user_id=user_id,
            session_id=session_id,
            **kwargs
        )

        self._view_logs[log_id] = log

        # Mettre à jour compteurs
        article.view_count += 1

        # Compter unique views (par session)
        if session_id:
            existing = [
                v for v in self._view_logs.values()
                if v.article_id == article_id and
                   v.session_id == session_id and
                   v.id != log_id
            ]
            if not existing:
                article.unique_views += 1
        else:
            article.unique_views += 1

        return log

    def update_view_metrics(
        self,
        log_id: str,
        time_spent_seconds: int,
        scroll_depth_percent: int
    ) -> Optional[ViewLog]:
        """Met à jour les métriques de vue."""
        log = self._view_logs.get(log_id)
        if not log:
            return None

        log.time_spent_seconds = time_spent_seconds
        log.scroll_depth_percent = scroll_depth_percent

        return log

    def get_statistics(self) -> KnowledgeStats:
        """Calcule les statistiques."""
        stats = KnowledgeStats(tenant_id=self.tenant_id)

        helpful_total = 0
        not_helpful_total = 0
        total_time = 0
        view_count = 0
        article_views = {}

        for article in self._articles.values():
            if article.tenant_id != self.tenant_id:
                continue

            stats.total_articles += 1

            if article.status == ArticleStatus.PUBLISHED:
                stats.published_articles += 1
            elif article.status == ArticleStatus.DRAFT:
                stats.draft_articles += 1

            stats.total_views += article.view_count
            stats.total_unique_views += article.unique_views

            helpful_total += article.helpful_count
            not_helpful_total += article.not_helpful_count

            # Par catégorie
            if article.category_id:
                cat = self.get_category(article.category_id)
                if cat:
                    stats.articles_by_category[cat.name] = (
                        stats.articles_by_category.get(cat.name, 0) + 1
                    )

            article_views[article.id] = {
                "id": article.id,
                "title": article.title,
                "views": article.view_count
            }

        # Temps moyen
        for log in self._view_logs.values():
            article = self.get_article(log.article_id)
            if not article:
                continue
            total_time += log.time_spent_seconds
            view_count += 1

            # Par jour
            day = log.viewed_at.strftime("%Y-%m-%d")
            stats.views_by_day[day] = stats.views_by_day.get(day, 0) + 1

        if view_count > 0:
            stats.avg_time_on_page_seconds = total_time // view_count

        # Taux d'utilité
        total_feedback = helpful_total + not_helpful_total
        if total_feedback > 0:
            stats.helpful_rate = Decimal(helpful_total) / Decimal(total_feedback) * 100

        # Top articles
        top = sorted(article_views.values(), key=lambda x: x["views"], reverse=True)[:10]
        stats.top_articles = top

        # Top recherches
        stats.top_searches = self.get_popular_searches(10)

        return stats

    def get_article_analytics(
        self,
        article_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Récupère les analytics d'un article."""
        article = self.get_article(article_id)
        if not article:
            return {}

        cutoff = datetime.now() - timedelta(days=period_days)

        views_by_day = {}
        total_time = 0
        total_scroll = 0
        view_count = 0

        for log in self._view_logs.values():
            if log.article_id != article_id:
                continue
            if log.viewed_at < cutoff:
                continue

            day = log.viewed_at.strftime("%Y-%m-%d")
            views_by_day[day] = views_by_day.get(day, 0) + 1

            total_time += log.time_spent_seconds
            total_scroll += log.scroll_depth_percent
            view_count += 1

        return {
            "article_id": article_id,
            "title": article.title,
            "total_views": article.view_count,
            "unique_views": article.unique_views,
            "helpful_count": article.helpful_count,
            "not_helpful_count": article.not_helpful_count,
            "helpful_rate": (
                article.helpful_count / (article.helpful_count + article.not_helpful_count) * 100
                if (article.helpful_count + article.not_helpful_count) > 0 else 0
            ),
            "views_in_period": view_count,
            "views_by_day": views_by_day,
            "avg_time_seconds": total_time // view_count if view_count > 0 else 0,
            "avg_scroll_depth": total_scroll // view_count if view_count > 0 else 0
        }

    # -------------------------------------------------------------------------
    # Utilitaires
    # -------------------------------------------------------------------------

    def _generate_slug(self, title: str) -> str:
        """Génère un slug."""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')

        # Vérifier unicité
        base_slug = slug
        counter = 1
        while any(
            a.slug == slug
            for a in self._articles.values()
            if a.tenant_id == self.tenant_id
        ):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def _generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Génère un extrait."""
        # Nettoyer HTML basique
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= max_length:
            return text

        return text[:max_length].rsplit(' ', 1)[0] + "..."


# ============================================================================
# FACTORY
# ============================================================================

def create_knowledge_service(tenant_id: str) -> KnowledgeService:
    """Factory pour créer un service de base de connaissances."""
    return KnowledgeService(tenant_id)
