"""
AZALS MODULE - Marceau Memory Service
=======================================

Service de memoire contextuelle avec ChromaDB pour RAG.
Chaque tenant a sa propre collection isolee.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from .models import MarceauMemory, MemoryType

logger = logging.getLogger(__name__)


# ============================================================================
# CHROMADB CLIENT (LAZY INITIALIZATION)
# ============================================================================

_chroma_client = None
_embedding_function = None


def get_chroma_client():
    """
    Initialise et retourne le client ChromaDB.
    Lazy loading pour eviter import au demarrage.
    """
    global _chroma_client

    if _chroma_client is None:
        try:
            import chromadb
            from chromadb.config import Settings

            _chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="/data/marceau/chromadb",
                anonymized_telemetry=False
            ))
            logger.info("[MARCEAU] ChromaDB client initialise")
        except ImportError:
            logger.warning("[MARCEAU] ChromaDB non installe - mode degrade sans embeddings")
            _chroma_client = None
        except Exception as e:
            logger.error(f"[MARCEAU] Erreur initialisation ChromaDB: {e}")
            _chroma_client = None

    return _chroma_client


def get_embedding_function():
    """
    Initialise et retourne la fonction d'embedding.
    Utilise sentence-transformers multilingual.
    """
    global _embedding_function

    if _embedding_function is None:
        try:
            from chromadb.utils import embedding_functions

            _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
            logger.info("[MARCEAU] Embedding function initialisee")
        except ImportError:
            logger.warning("[MARCEAU] sentence-transformers non installe")
            _embedding_function = None
        except Exception as e:
            logger.error(f"[MARCEAU] Erreur initialisation embeddings: {e}")
            _embedding_function = None

    return _embedding_function


def get_collection_name(tenant_id: str) -> str:
    """Genere le nom de collection ChromaDB pour un tenant."""
    # Remplacer les caracteres non valides
    safe_tenant = tenant_id.replace("-", "_").replace(".", "_")
    return f"marceau_memory_{safe_tenant}"


# ============================================================================
# SERVICE DE MEMOIRE
# ============================================================================

class MarceauMemoryService:
    """
    Service de gestion de la memoire Marceau.
    Combine stockage SQL (metadonnees) et ChromaDB (embeddings).
    """

    def __init__(self, tenant_id: str, db: Session):
        """
        Initialise le service de memoire.

        Args:
            tenant_id: ID du tenant
            db: Session SQLAlchemy
        """
        self.tenant_id = tenant_id
        self.db = db
        self.collection_name = get_collection_name(tenant_id)
        self._collection = None

    def _get_collection(self):
        """Recupere ou cree la collection ChromaDB."""
        if self._collection is not None:
            return self._collection

        client = get_chroma_client()
        if client is None:
            return None

        embedding_fn = get_embedding_function()

        try:
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
                metadata={"tenant_id": self.tenant_id}
            )
            return self._collection
        except Exception as e:
            logger.error(f"[MARCEAU] Erreur creation collection: {e}")
            return None

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        tags: list[str] | None = None,
        importance_score: float = 0.5,
        summary: str | None = None,
        related_action_id: uuid.UUID | None = None,
        related_customer_id: uuid.UUID | None = None,
        related_conversation_id: uuid.UUID | None = None,
        source: str | None = None,
        source_file_name: str | None = None,
        is_permanent: bool = False,
        expires_at: datetime | None = None,
    ) -> MarceauMemory:
        """
        Stocke une nouvelle memoire.

        Args:
            content: Contenu textuel de la memoire
            memory_type: Type de memoire
            tags: Tags de classification
            importance_score: Score d'importance (0-1)
            summary: Resume optionnel
            related_action_id: ID action liee
            related_customer_id: ID client lie
            related_conversation_id: ID conversation liee
            source: Source de la memoire
            source_file_name: Nom du fichier source
            is_permanent: Si True, ne sera pas supprimee automatiquement
            expires_at: Date d'expiration

        Returns:
            MarceauMemory creee
        """
        memory_id = uuid.uuid4()
        embedding_id = None

        # Stocker dans ChromaDB si disponible
        collection = self._get_collection()
        if collection is not None:
            try:
                embedding_id = str(memory_id)
                collection.add(
                    ids=[embedding_id],
                    documents=[content],
                    metadatas=[{
                        "memory_type": memory_type.value,
                        "importance_score": importance_score,
                        "tags": ",".join(tags or []),
                        "created_at": datetime.utcnow().isoformat(),
                    }]
                )
            except Exception as e:
                logger.error(f"[MARCEAU] Erreur stockage ChromaDB: {e}")
                embedding_id = None

        # Stocker en base SQL
        memory = MarceauMemory(
            id=memory_id,
            tenant_id=self.tenant_id,
            memory_type=memory_type,
            content=content,
            summary=summary,
            embedding_id=embedding_id,
            collection_name=self.collection_name if embedding_id else None,
            related_action_id=related_action_id,
            related_customer_id=related_customer_id,
            related_conversation_id=related_conversation_id,
            tags=tags or [],
            importance_score=importance_score,
            expires_at=expires_at,
            is_permanent=is_permanent,
            source=source,
            source_file_name=source_file_name,
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        logger.info(f"[MARCEAU] Memoire stockee: {memory_id} (type={memory_type.value})")
        return memory

    async def retrieve_relevant_context(
        self,
        query: str,
        limit: int = 10,
        memory_types: list[MemoryType] | None = None,
        tags: list[str] | None = None,
        min_importance: float = 0.0,
    ) -> list[str]:
        """
        Recupere le contexte pertinent pour une requete (RAG).

        Args:
            query: Requete textuelle
            limit: Nombre max de resultats
            memory_types: Types de memoire a inclure
            tags: Tags a filtrer
            min_importance: Score d'importance minimum

        Returns:
            Liste de contenus pertinents
        """
        results = []

        # Recherche semantique via ChromaDB
        collection = self._get_collection()
        if collection is not None and query.strip():
            try:
                where_filter = {}
                if memory_types:
                    where_filter["memory_type"] = {"$in": [mt.value for mt in memory_types]}
                if min_importance > 0:
                    where_filter["importance_score"] = {"$gte": min_importance}

                chroma_results = collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where_filter if where_filter else None,
                )

                if chroma_results and chroma_results.get("documents"):
                    results.extend(chroma_results["documents"][0])
            except Exception as e:
                logger.error(f"[MARCEAU] Erreur recherche ChromaDB: {e}")

        # Fallback: recherche SQL si pas de resultats ChromaDB
        if not results:
            query_filter = [
                MarceauMemory.tenant_id == self.tenant_id,
                MarceauMemory.importance_score >= min_importance,
            ]

            if memory_types:
                query_filter.append(MarceauMemory.memory_type.in_(memory_types))

            memories = self.db.query(MarceauMemory).filter(
                *query_filter
            ).order_by(
                MarceauMemory.importance_score.desc(),
                MarceauMemory.created_at.desc()
            ).limit(limit).all()

            results = [m.content for m in memories]

        return results

    async def search_memories(
        self,
        query: str | None = None,
        memory_types: list[MemoryType] | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MarceauMemory], int]:
        """
        Recherche des memoires avec filtres.

        Args:
            query: Recherche textuelle
            memory_types: Types de memoire
            tags: Tags a filtrer
            limit: Nombre max
            offset: Offset pagination

        Returns:
            Tuple (liste memoires, total)
        """
        filters = [MarceauMemory.tenant_id == self.tenant_id]

        if memory_types:
            filters.append(MarceauMemory.memory_type.in_(memory_types))

        if tags:
            # Recherche dans le JSON des tags
            for tag in tags:
                filters.append(MarceauMemory.tags.contains([tag]))

        if query:
            filters.append(MarceauMemory.content.ilike(f"%{query}%"))

        base_query = self.db.query(MarceauMemory).filter(*filters)

        total = base_query.count()

        memories = base_query.order_by(
            MarceauMemory.importance_score.desc(),
            MarceauMemory.created_at.desc()
        ).offset(offset).limit(limit).all()

        return memories, total

    async def get_memory(self, memory_id: uuid.UUID) -> MarceauMemory | None:
        """Recupere une memoire par ID."""
        return self.db.query(MarceauMemory).filter(
            MarceauMemory.id == memory_id,
            MarceauMemory.tenant_id == self.tenant_id
        ).first()

    async def delete_memory(self, memory_id: uuid.UUID) -> bool:
        """
        Supprime une memoire.

        Args:
            memory_id: ID de la memoire

        Returns:
            True si supprimee
        """
        memory = await self.get_memory(memory_id)
        if not memory:
            return False

        # Supprimer de ChromaDB si present
        if memory.embedding_id:
            collection = self._get_collection()
            if collection is not None:
                try:
                    collection.delete(ids=[memory.embedding_id])
                except Exception as e:
                    logger.error(f"[MARCEAU] Erreur suppression ChromaDB: {e}")

        # Supprimer de la base SQL
        self.db.delete(memory)
        self.db.commit()

        return True

    async def update_importance(
        self,
        memory_id: uuid.UUID,
        new_importance: float
    ) -> MarceauMemory | None:
        """
        Met a jour le score d'importance d'une memoire.

        Args:
            memory_id: ID de la memoire
            new_importance: Nouveau score (0-1)

        Returns:
            Memoire mise a jour ou None
        """
        memory = await self.get_memory(memory_id)
        if not memory:
            return None

        memory.importance_score = max(0.0, min(1.0, new_importance))
        memory.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(memory)

        # Mettre a jour dans ChromaDB
        if memory.embedding_id:
            collection = self._get_collection()
            if collection is not None:
                try:
                    collection.update(
                        ids=[memory.embedding_id],
                        metadatas=[{"importance_score": memory.importance_score}]
                    )
                except Exception as e:
                    logger.error(f"[MARCEAU] Erreur update ChromaDB: {e}")

        return memory

    async def cleanup_expired(self) -> int:
        """
        Supprime les memoires expirees.

        Returns:
            Nombre de memoires supprimees
        """
        now = datetime.utcnow()

        expired_memories = self.db.query(MarceauMemory).filter(
            MarceauMemory.tenant_id == self.tenant_id,
            MarceauMemory.expires_at <= now,
            MarceauMemory.is_permanent == False
        ).all()

        count = 0
        for memory in expired_memories:
            if await self.delete_memory(memory.id):
                count += 1

        logger.info(f"[MARCEAU] {count} memoires expirees supprimees pour tenant {self.tenant_id}")
        return count

    async def get_stats(self) -> dict:
        """
        Retourne les statistiques de memoire.

        Returns:
            Dict avec statistiques
        """
        from sqlalchemy import func

        total = self.db.query(func.count(MarceauMemory.id)).filter(
            MarceauMemory.tenant_id == self.tenant_id
        ).scalar()

        by_type = self.db.query(
            MarceauMemory.memory_type,
            func.count(MarceauMemory.id)
        ).filter(
            MarceauMemory.tenant_id == self.tenant_id
        ).group_by(MarceauMemory.memory_type).all()

        permanent_count = self.db.query(func.count(MarceauMemory.id)).filter(
            MarceauMemory.tenant_id == self.tenant_id,
            MarceauMemory.is_permanent == True
        ).scalar()

        avg_importance = self.db.query(func.avg(MarceauMemory.importance_score)).filter(
            MarceauMemory.tenant_id == self.tenant_id
        ).scalar()

        return {
            "total_memories": total or 0,
            "by_type": {str(mt): count for mt, count in by_type},
            "permanent_count": permanent_count or 0,
            "avg_importance": float(avg_importance) if avg_importance else 0.0,
            "collection_name": self.collection_name,
        }
