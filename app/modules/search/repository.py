"""
AZALS MODULE SEARCH - Repository
=================================

Repositories SQLAlchemy pour le module Search / Indexation.
Conforme aux normes AZALSCORE (isolation tenant, type hints).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from .models import (
    SearchIndex,
    IndexedDocument,
    SearchHistory,
    ReindexJob,
    TermFrequency,
    IndexStatus,
    FieldType,
    AnalyzerType,
    ReindexJobStatus,
)


class SearchIndexRepository:
    """Repository pour les index de recherche."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(SearchIndex).filter(
            SearchIndex.tenant_id == self.tenant_id
        )

    def get_by_id(self, index_id: UUID) -> Optional[SearchIndex]:
        """Recupere un index par ID."""
        return self._base_query().filter(SearchIndex.id == index_id).first()

    def get_by_name(self, name: str) -> Optional[SearchIndex]:
        """Recupere un index par nom."""
        return self._base_query().filter(SearchIndex.name == name).first()

    def get_by_entity_type(self, entity_type: str) -> Optional[SearchIndex]:
        """Recupere un index par type d'entite."""
        return self._base_query().filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.status == IndexStatus.ACTIVE
        ).first()

    def list(
        self,
        status: Optional[IndexStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[SearchIndex], int]:
        """Liste les index avec filtres."""
        query = self._base_query()
        if status:
            query = query.filter(SearchIndex.status == status)
        total = query.count()
        items = query.order_by(SearchIndex.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> SearchIndex:
        """Cree un nouvel index."""
        index = SearchIndex(tenant_id=self.tenant_id, **data)
        self.db.add(index)
        self.db.commit()
        self.db.refresh(index)
        return index

    def update(self, index: SearchIndex, data: Dict[str, Any]) -> SearchIndex:
        """Met a jour un index."""
        for key, value in data.items():
            if hasattr(index, key) and value is not None:
                setattr(index, key, value)
        index.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(index)
        return index

    def update_status(self, index: SearchIndex, status: IndexStatus) -> SearchIndex:
        """Met a jour le statut."""
        index.status = status
        index.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(index)
        return index

    def update_stats(
        self,
        index: SearchIndex,
        document_count: int,
        size_bytes: int
    ) -> SearchIndex:
        """Met a jour les statistiques."""
        index.document_count = document_count
        index.size_bytes = size_bytes
        index.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(index)
        return index

    def mark_reindexed(self, index: SearchIndex) -> SearchIndex:
        """Marque comme reindexe."""
        index.last_reindex_at = datetime.utcnow()
        index.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(index)
        return index

    def delete(self, index: SearchIndex) -> None:
        """Supprime un index."""
        self.db.delete(index)
        self.db.commit()


class IndexedDocumentRepository:
    """Repository pour les documents indexes."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(IndexedDocument).filter(
            IndexedDocument.tenant_id == self.tenant_id
        )

    def get_by_id(self, doc_id: UUID) -> Optional[IndexedDocument]:
        """Recupere un document par ID."""
        return self._base_query().filter(IndexedDocument.id == doc_id).first()

    def get_by_entity(
        self,
        index_id: UUID,
        entity_id: str
    ) -> Optional[IndexedDocument]:
        """Recupere un document par entite."""
        return self._base_query().filter(
            IndexedDocument.index_id == index_id,
            IndexedDocument.entity_id == entity_id
        ).first()

    def list_by_index(
        self,
        index_id: UUID,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[IndexedDocument], int]:
        """Liste les documents d'un index."""
        query = self._base_query().filter(IndexedDocument.index_id == index_id)
        total = query.count()
        items = query.order_by(IndexedDocument.indexed_at).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def search_fulltext(
        self,
        index_id: UUID,
        query_text: str,
        limit: int = 20
    ) -> List[IndexedDocument]:
        """Recherche full-text simple."""
        return self._base_query().filter(
            IndexedDocument.index_id == index_id,
            IndexedDocument.all_text.ilike(f"%{query_text}%")
        ).limit(limit).all()

    def create(self, data: Dict[str, Any]) -> IndexedDocument:
        """Cree un nouveau document."""
        doc = IndexedDocument(tenant_id=self.tenant_id, **data)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update(self, doc: IndexedDocument, data: Dict[str, Any]) -> IndexedDocument:
        """Met a jour un document."""
        for key, value in data.items():
            if hasattr(doc, key) and value is not None:
                setattr(doc, key, value)
        doc.version += 1
        doc.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def upsert(self, index_id: UUID, entity_id: str, data: Dict[str, Any]) -> IndexedDocument:
        """Cree ou met a jour un document."""
        existing = self.get_by_entity(index_id, entity_id)
        if existing:
            return self.update(existing, data)
        else:
            return self.create({
                "index_id": index_id,
                "entity_id": entity_id,
                **data
            })

    def delete(self, doc: IndexedDocument) -> None:
        """Supprime un document."""
        self.db.delete(doc)
        self.db.commit()

    def delete_by_entity(self, index_id: UUID, entity_id: str) -> bool:
        """Supprime un document par entite."""
        doc = self.get_by_entity(index_id, entity_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False

    def delete_all_by_index(self, index_id: UUID) -> int:
        """Supprime tous les documents d'un index."""
        result = self._base_query().filter(
            IndexedDocument.index_id == index_id
        ).delete(synchronize_session=False)
        self.db.commit()
        return result


class SearchHistoryRepository:
    """Repository pour l'historique des recherches."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(SearchHistory).filter(
            SearchHistory.tenant_id == self.tenant_id
        )

    def list(
        self,
        user_id: Optional[UUID] = None,
        index_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[SearchHistory], int]:
        """Liste l'historique avec filtres."""
        query = self._base_query()
        if user_id:
            query = query.filter(SearchHistory.user_id == user_id)
        if index_id:
            query = query.filter(SearchHistory.index_id == index_id)
        if date_from:
            query = query.filter(SearchHistory.searched_at >= date_from)
        if date_to:
            query = query.filter(SearchHistory.searched_at <= date_to)
        total = query.count()
        items = query.order_by(desc(SearchHistory.searched_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_user_recent(self, user_id: UUID, limit: int = 10) -> List[SearchHistory]:
        """Recupere les recherches recentes d'un utilisateur."""
        return self._base_query().filter(
            SearchHistory.user_id == user_id
        ).order_by(desc(SearchHistory.searched_at)).limit(limit).all()

    def get_popular_queries(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Recupere les requetes populaires."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = self.db.query(
            SearchHistory.query_text,
            func.count(SearchHistory.id).label("count")
        ).filter(
            SearchHistory.tenant_id == self.tenant_id,
            SearchHistory.searched_at >= cutoff
        ).group_by(
            SearchHistory.query_text
        ).order_by(
            desc("count")
        ).limit(limit).all()

        return [{"query": r[0], "count": r[1]} for r in results]

    def create(self, data: Dict[str, Any]) -> SearchHistory:
        """Cree une nouvelle entree."""
        history = SearchHistory(tenant_id=self.tenant_id, **data)
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def record_click(self, history_id: UUID, doc_id: str) -> SearchHistory:
        """Enregistre un clic sur un resultat."""
        history = self._base_query().filter(SearchHistory.id == history_id).first()
        if history:
            clicked = history.clicked_results or []
            if doc_id not in clicked:
                clicked.append(doc_id)
                history.clicked_results = clicked
                self.db.commit()
                self.db.refresh(history)
        return history

    def delete_old(self, days: int = 90) -> int:
        """Supprime l'ancien historique."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self._base_query().filter(
            SearchHistory.searched_at < cutoff
        ).delete(synchronize_session=False)
        self.db.commit()
        return result


class ReindexJobRepository:
    """Repository pour les jobs de reindexation."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(ReindexJob).filter(
            ReindexJob.tenant_id == self.tenant_id
        )

    def get_by_id(self, job_id: UUID) -> Optional[ReindexJob]:
        """Recupere un job par ID."""
        return self._base_query().filter(ReindexJob.id == job_id).first()

    def get_pending(self) -> List[ReindexJob]:
        """Recupere les jobs en attente."""
        return self._base_query().filter(
            ReindexJob.status == ReindexJobStatus.PENDING
        ).order_by(ReindexJob.created_at).all()

    def get_running(self) -> List[ReindexJob]:
        """Recupere les jobs en cours."""
        return self._base_query().filter(
            ReindexJob.status == ReindexJobStatus.RUNNING
        ).all()

    def list_by_index(
        self,
        index_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ReindexJob], int]:
        """Liste les jobs d'un index."""
        query = self._base_query().filter(ReindexJob.index_id == index_id)
        total = query.count()
        items = query.order_by(desc(ReindexJob.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> ReindexJob:
        """Cree un nouveau job."""
        job = ReindexJob(tenant_id=self.tenant_id, **data)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def start(self, job: ReindexJob, total_documents: int) -> ReindexJob:
        """Demarre un job."""
        job.status = ReindexJobStatus.RUNNING
        job.total_documents = total_documents
        job.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_progress(
        self,
        job: ReindexJob,
        processed: int,
        failed: int = 0
    ) -> ReindexJob:
        """Met a jour la progression."""
        job.processed_documents = processed
        job.failed_documents = failed
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete(self, job: ReindexJob) -> ReindexJob:
        """Termine un job."""
        job.status = ReindexJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def fail(self, job: ReindexJob, error_message: str) -> ReindexJob:
        """Marque un job comme echoue."""
        job.status = ReindexJobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def cancel(self, job: ReindexJob) -> ReindexJob:
        """Annule un job."""
        job.status = ReindexJobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job


class TermFrequencyRepository:
    """Repository pour les frequences de termes."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(TermFrequency).filter(
            TermFrequency.tenant_id == self.tenant_id
        )

    def get_suggestions(
        self,
        prefix: str,
        index_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[str]:
        """Recupere les suggestions pour un prefixe."""
        query = self._base_query().filter(
            TermFrequency.term.ilike(f"{prefix}%")
        )
        if index_id:
            query = query.filter(TermFrequency.index_id == index_id)
        results = query.order_by(
            desc(TermFrequency.frequency)
        ).limit(limit).all()
        return [r.term for r in results]

    def increment(self, term: str, index_id: Optional[UUID] = None) -> TermFrequency:
        """Incremente la frequence d'un terme."""
        existing = self._base_query().filter(
            TermFrequency.term == term,
            TermFrequency.index_id == index_id
        ).first()

        if existing:
            existing.frequency += 1
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            tf = TermFrequency(
                tenant_id=self.tenant_id,
                term=term,
                index_id=index_id,
                frequency=1
            )
            self.db.add(tf)
            self.db.commit()
            self.db.refresh(tf)
            return tf

    def delete_low_frequency(self, min_frequency: int = 2) -> int:
        """Supprime les termes a faible frequence."""
        result = self._base_query().filter(
            TermFrequency.frequency < min_frequency
        ).delete(synchronize_session=False)
        self.db.commit()
        return result
