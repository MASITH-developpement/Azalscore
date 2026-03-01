"""
Service Knowledge Base - GAP-068

Base de connaissances avec persistence SQLAlchemy:
- Articles et documentation
- Categories et tags
- Recherche full-text
- Versioning des articles
- Feedback et notation
- FAQ dynamique
- Analytics de lecture
- Multi-langue

CRITIQUE: Utilise les repositories pour l'isolation multi-tenant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .models import (
    ArticleStatus,
    ArticleType,
    Visibility,
    FeedbackType,
)
from .repository import (
    CategoryRepository,
    ArticleRepository,
    FAQRepository,
    FeedbackRepository,
    ViewLogRepository,
    KnowledgeStatsRepository,
)


# ============================================================================
# DATA CLASSES (pour compatibilite API)
# ============================================================================

@dataclass
class SearchResult:
    """Resultat de recherche."""
    article_id: str
    title: str
    excerpt: str
    category: Optional[str] = None
    score: float = 0.0
    highlights: List[str] = field(default_factory=list)


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
    """Service de base de connaissances avec persistence SQLAlchemy."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories avec isolation tenant
        self.category_repo = CategoryRepository(db, tenant_id)
        self.article_repo = ArticleRepository(db, tenant_id)
        self.faq_repo = FAQRepository(db, tenant_id)
        self.feedback_repo = FeedbackRepository(db, tenant_id)
        self.view_log_repo = ViewLogRepository(db, tenant_id)
        self.stats_repo = KnowledgeStatsRepository(db, tenant_id)

    # -------------------------------------------------------------------------
    # Categories
    # -------------------------------------------------------------------------

    def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
        **kwargs
    ):
        """Cree une categorie."""
        data = {
            "name": name,
            "description": description,
            "parent_id": parent_id,
            **kwargs
        }
        return self.category_repo.create(data)

    def get_category(self, category_id: str):
        """Recupere une categorie."""
        return self.category_repo.get_by_id(category_id)

    def list_categories(
        self,
        parent_id: Optional[str] = None,
        include_hidden: bool = False
    ):
        """Liste les categories."""
        if parent_id is not None:
            return self.category_repo.list(parent_id=parent_id, include_hidden=include_hidden)
        return self.category_repo.list_all(include_hidden=include_hidden)

    def get_category_tree(self) -> List[Dict[str, Any]]:
        """Recupere l'arborescence des categories."""
        return self.category_repo.get_tree()

    def update_category(self, category_id: str, **updates):
        """Met a jour une categorie."""
        entity = self.category_repo.get_by_id(category_id)
        if not entity:
            return None
        return self.category_repo.update(entity, updates)

    def delete_category(self, category_id: str) -> bool:
        """Supprime une categorie."""
        entity = self.category_repo.get_by_id(category_id)
        if not entity:
            return False
        return self.category_repo.delete(entity)

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
    ):
        """Cree un article."""
        # Generer extrait si non fourni
        excerpt = kwargs.pop('excerpt', None)
        if not excerpt:
            excerpt = self._generate_excerpt(content)

        data = {
            "title": title,
            "content": content,
            "article_type": article_type,
            "author_id": author_id,
            "author_name": author_name,
            "excerpt": excerpt,
            **kwargs
        }
        article = self.article_repo.create(data, created_by=author_id)

        # Mettre a jour compteur categorie
        if article.category_id:
            self.category_repo.increment_article_count(str(article.category_id), 1)

        return article

    def get_article(self, article_id: str):
        """Recupere un article."""
        return self.article_repo.get_by_id(article_id)

    def get_article_by_slug(self, slug: str):
        """Recupere un article par son slug."""
        return self.article_repo.get_by_slug(slug)

    def update_article(
        self,
        article_id: str,
        change_summary: Optional[str] = None,
        updated_by: Optional[str] = None,
        **updates
    ):
        """Met a jour un article."""
        article = self.article_repo.get_by_id(article_id)
        if not article:
            return None
        return self.article_repo.update(
            article,
            updates,
            change_summary=change_summary,
            updated_by=updated_by
        )

    def publish_article(self, article_id: str):
        """Publie un article."""
        article = self.article_repo.get_by_id(article_id)
        if not article:
            return None
        return self.article_repo.publish(article)

    def archive_article(self, article_id: str):
        """Archive un article."""
        article = self.article_repo.get_by_id(article_id)
        if not article:
            return None

        # Mettre a jour compteur categorie
        if article.category_id:
            self.category_repo.increment_article_count(str(article.category_id), -1)

        return self.article_repo.archive(article)

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
    ) -> Tuple[List, int]:
        """Liste les articles."""
        return self.article_repo.list(
            category_id=category_id,
            article_type=article_type,
            status=status,
            visibility=visibility,
            tags=tags,
            author_id=author_id,
            language=language,
            search=search,
            page=page,
            page_size=page_size
        )

    def get_related_articles(self, article_id: str, limit: int = 5):
        """Recupere les articles lies."""
        return self.article_repo.get_related(article_id, limit=limit)

    def get_article_versions(self, article_id: str):
        """Liste les versions d'un article."""
        return self.article_repo.get_versions(article_id)

    def restore_version(self, article_id: str, version_number: int):
        """Restaure une version."""
        return self.article_repo.restore_version(article_id, version_number)

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
        results = self.article_repo.search(
            query,
            category_id=category_id,
            article_type=article_type,
            language=language,
            limit=limit
        )

        return [
            SearchResult(
                article_id=r["article_id"],
                title=r["title"],
                excerpt=r["excerpt"],
                category=r.get("category"),
                score=r.get("score", 0.0),
                highlights=r.get("highlights", [])
            )
            for r in results
        ]

    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupere les recherches populaires."""
        # TODO: Implementer tracking des recherches
        return []

    # -------------------------------------------------------------------------
    # FAQ
    # -------------------------------------------------------------------------

    def create_faq(
        self,
        question: str,
        answer: str,
        category_id: Optional[str] = None,
        **kwargs
    ):
        """Cree une FAQ."""
        data = {
            "question": question,
            "answer": answer,
            "category_id": category_id,
            **kwargs
        }
        return self.faq_repo.create(data)

    def get_faq(self, faq_id: str):
        """Recupere une FAQ."""
        return self.faq_repo.get_by_id(faq_id)

    def update_faq(self, faq_id: str, **updates):
        """Met a jour une FAQ."""
        entity = self.faq_repo.get_by_id(faq_id)
        if not entity:
            return None
        return self.faq_repo.update(entity, updates)

    def publish_faq(self, faq_id: str):
        """Publie une FAQ."""
        entity = self.faq_repo.get_by_id(faq_id)
        if not entity:
            return None
        return self.faq_repo.publish(entity)

    def list_faqs(
        self,
        category_id: Optional[str] = None,
        featured_only: bool = False,
        language: Optional[str] = None
    ):
        """Liste les FAQs."""
        return self.faq_repo.list(
            category_id=category_id,
            featured_only=featured_only,
            language=language
        )

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
    ):
        """Soumet un feedback."""
        article = self.article_repo.get_by_id(article_id)
        if not article:
            return None

        data = {
            "article_id": article_id,
            "feedback_type": feedback_type,
            "user_id": user_id,
            "comment": comment,
            "rating": rating
        }
        return self.feedback_repo.create(data)

    def list_feedback(
        self,
        article_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        unresolved_only: bool = False
    ):
        """Liste les feedbacks."""
        return self.feedback_repo.list(
            article_id=article_id,
            feedback_type=feedback_type,
            unresolved_only=unresolved_only
        )

    def resolve_feedback(self, feedback_id: str, resolved_by: str):
        """Resout un feedback."""
        entity = self.feedback_repo.get_by_id(feedback_id)
        if not entity:
            return None
        return self.feedback_repo.resolve(entity, resolved_by)

    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------

    def record_view(
        self,
        article_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """Enregistre une vue."""
        article = self.article_repo.get_by_id(article_id)
        if not article:
            return None

        # Verifier si c'est une vue unique (nouvelle session)
        is_unique = True
        if session_id:
            # Simplification: on considere unique si session_id est fourni
            # Le repository gere le compteur
            pass

        # Creer le log de vue
        data = {
            "article_id": article_id,
            "user_id": user_id,
            "session_id": session_id,
            **kwargs
        }
        log = self.view_log_repo.create(data)

        # Incrementer les compteurs de l'article
        self.article_repo.increment_view_count(article_id, unique=is_unique)

        return log

    def update_view_metrics(
        self,
        log_id: str,
        time_spent_seconds: int,
        scroll_depth_percent: int
    ):
        """Met a jour les metriques de vue."""
        return self.view_log_repo.update_metrics(log_id, time_spent_seconds, scroll_depth_percent)

    def get_statistics(self) -> KnowledgeStats:
        """Calcule les statistiques."""
        stats_dict = self.stats_repo.get_stats()

        return KnowledgeStats(
            tenant_id=self.tenant_id,
            total_articles=stats_dict.get("total_articles", 0),
            published_articles=stats_dict.get("published_articles", 0),
            draft_articles=stats_dict.get("draft_articles", 0),
            total_views=stats_dict.get("total_views", 0),
            total_unique_views=stats_dict.get("total_unique_views", 0),
            avg_time_on_page_seconds=stats_dict.get("avg_time_on_page_seconds", 0),
            helpful_rate=Decimal(str(stats_dict.get("helpful_rate", 0))),
            top_articles=stats_dict.get("top_articles", []),
            top_searches=stats_dict.get("top_searches", []),
            articles_by_category=stats_dict.get("articles_by_category", {}),
            views_by_day=stats_dict.get("views_by_day", {})
        )

    def get_article_analytics(
        self,
        article_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Recupere les analytics d'un article."""
        result = self.stats_repo.get_article_analytics(article_id, period_days)
        return result or {}

    # -------------------------------------------------------------------------
    # Utilitaires
    # -------------------------------------------------------------------------

    def _generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Genere un extrait."""
        import re
        # Nettoyer HTML basique
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= max_length:
            return text

        return text[:max_length].rsplit(' ', 1)[0] + "..."


# ============================================================================
# FACTORY
# ============================================================================

def create_knowledge_service(db: Session, tenant_id: str) -> KnowledgeService:
    """Factory pour creer un service de base de connaissances."""
    return KnowledgeService(db, tenant_id)
