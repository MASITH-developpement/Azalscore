"""
AZALSCORE Module I18N - Repository
===================================

Repository avec isolation tenant obligatoire.
_base_query() filtre TOUJOURS par tenant_id.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.orm import Session, joinedload

from .models import (
    Language, LanguageStatus,
    TranslationNamespace,
    TranslationKey, TranslationScope,
    Translation, TranslationStatus,
    TranslationJob, TranslationJobStatus,
    TranslationImportExport, ImportExportFormat,
    TranslationCache,
    Glossary,
)
from .schemas import (
    LanguageFilters,
    TranslationKeyFilters,
    TranslationFilters,
)


# ============================================================================
# LANGUAGE REPOSITORY
# ============================================================================

class LanguageRepository:
    """
    Repository Language avec isolation tenant obligatoire.

    SECURITE: _base_query() filtre TOUJOURS par tenant_id.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        include_deleted: bool = False
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        """Point d'entree unique - TOUJOURS filtrer par tenant_id."""
        query = self.db.query(Language).filter(
            Language.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Language.deleted_at.is_(None))
        return query

    # === READ ===
    def get_by_id(self, id: UUID) -> Optional[Language]:
        return self._base_query().filter(Language.id == id).first()

    def get_by_code(self, code: str) -> Optional[Language]:
        return self._base_query().filter(Language.code == code.lower()).first()

    def get_default(self) -> Optional[Language]:
        return self._base_query().filter(Language.is_default == True).first()

    def get_fallback(self) -> Optional[Language]:
        return self._base_query().filter(Language.is_fallback == True).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(Language.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Language.code == code.lower())
        if exclude_id:
            query = query.filter(Language.id != exclude_id)
        return query.count() > 0

    # === LIST ===
    def list(
        self,
        filters: LanguageFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "sort_order",
        sort_dir: str = "asc"
    ) -> Tuple[List[Language], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Language.code.ilike(term),
                    Language.name.ilike(term),
                    Language.native_name.ilike(term)
                ))
            if filters.status:
                query = query.filter(Language.status.in_(filters.status))
            if filters.is_default is not None:
                query = query.filter(Language.is_default == filters.is_default)
            if filters.rtl is not None:
                query = query.filter(Language.rtl == filters.rtl)

        total = query.count()

        sort_col = getattr(Language, sort_by, Language.sort_order)
        query = query.order_by(asc(sort_col) if sort_dir == "asc" else desc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def list_active(self) -> List[Language]:
        """Liste les langues actives triees."""
        return self._base_query().filter(
            Language.status == LanguageStatus.ACTIVE
        ).order_by(Language.sort_order, Language.name).all()

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 1:
            return []
        query = self._base_query().filter(
            Language.status == LanguageStatus.ACTIVE
        ).filter(or_(
            Language.code.ilike(f"{prefix}%"),
            Language.name.ilike(f"{prefix}%")
        ))
        results = query.order_by(Language.name).limit(limit).all()
        return [
            {
                "id": str(lang.id),
                "code": lang.code,
                "name": lang.name,
                "label": f"{lang.flag_emoji or ''} {lang.name} ({lang.code})".strip()
            }
            for lang in results
        ]

    # === CREATE ===
    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Language:
        # Normaliser le code
        if "code" in data:
            data["code"] = data["code"].lower()

        entity = Language(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    # === UPDATE ===
    def update(
        self,
        entity: Language,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> Language:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def set_default(self, language_id: UUID, updated_by: UUID = None) -> Language:
        """Definit une langue comme langue par defaut."""
        # Retirer le flag des autres
        self._base_query().filter(Language.is_default == True).update(
            {"is_default": False}, synchronize_session=False
        )
        # Definir la nouvelle
        lang = self.get_by_id(language_id)
        if lang:
            lang.is_default = True
            lang.updated_by = updated_by
            self.db.commit()
            self.db.refresh(lang)
        return lang

    # === DELETE ===
    def soft_delete(self, entity: Language, deleted_by: UUID = None) -> bool:
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True

    def hard_delete(self, entity: Language) -> bool:
        self.db.delete(entity)
        self.db.commit()
        return True

    # === STATS ===
    def update_coverage(self, language_id: UUID) -> Optional[Language]:
        """Met a jour les stats de couverture."""
        lang = self.get_by_id(language_id)
        if not lang:
            return None

        # Compter les cles et traductions
        total_keys = self.db.query(TranslationKey).filter(
            TranslationKey.tenant_id == self.tenant_id,
            TranslationKey.deleted_at.is_(None)
        ).count()

        translated = self.db.query(Translation).filter(
            Translation.tenant_id == self.tenant_id,
            Translation.language_id == language_id,
            Translation.deleted_at.is_(None)
        ).count()

        lang.total_keys = total_keys
        lang.translated_keys = translated
        lang.translation_coverage = Decimal(
            (translated / total_keys * 100) if total_keys > 0 else 0
        ).quantize(Decimal("0.01"))

        self.db.commit()
        self.db.refresh(lang)
        return lang


# ============================================================================
# NAMESPACE REPOSITORY
# ============================================================================

class NamespaceRepository:
    """Repository Namespace avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(TranslationNamespace).filter(
            TranslationNamespace.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(TranslationNamespace.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[TranslationNamespace]:
        return self._base_query().filter(TranslationNamespace.id == id).first()

    def get_by_code(self, code: str) -> Optional[TranslationNamespace]:
        return self._base_query().filter(TranslationNamespace.code == code).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(TranslationNamespace.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(TranslationNamespace.code == code)
        if exclude_id:
            query = query.filter(TranslationNamespace.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "code",
        sort_dir: str = "asc",
        search: Optional[str] = None,
        module_code: Optional[str] = None
    ) -> Tuple[List[TranslationNamespace], int]:
        query = self._base_query()

        if search:
            term = f"%{search}%"
            query = query.filter(or_(
                TranslationNamespace.code.ilike(term),
                TranslationNamespace.name.ilike(term)
            ))
        if module_code:
            query = query.filter(TranslationNamespace.module_code == module_code)

        total = query.count()
        sort_col = getattr(TranslationNamespace, sort_by, TranslationNamespace.code)
        query = query.order_by(asc(sort_col) if sort_dir == "asc" else desc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def list_all(self) -> List[TranslationNamespace]:
        return self._base_query().order_by(TranslationNamespace.code).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> TranslationNamespace:
        entity = TranslationNamespace(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: TranslationNamespace,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> TranslationNamespace:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: TranslationNamespace, deleted_by: UUID = None) -> bool:
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True


# ============================================================================
# TRANSLATION KEY REPOSITORY
# ============================================================================

class TranslationKeyRepository:
    """Repository TranslationKey avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(TranslationKey).filter(
            TranslationKey.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(TranslationKey.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[TranslationKey]:
        return self._base_query().filter(TranslationKey.id == id).first()

    def get_by_key(self, namespace_id: UUID, key: str) -> Optional[TranslationKey]:
        return self._base_query().filter(
            TranslationKey.namespace_id == namespace_id,
            TranslationKey.key == key
        ).first()

    def get_by_full_key(self, namespace_code: str, key: str) -> Optional[TranslationKey]:
        """Recupere par namespace.key"""
        return self._base_query().join(TranslationNamespace).filter(
            TranslationNamespace.code == namespace_code,
            TranslationKey.key == key
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(TranslationKey.id == id).count() > 0

    def key_exists(
        self,
        namespace_id: UUID,
        key: str,
        exclude_id: UUID = None
    ) -> bool:
        query = self._base_query().filter(
            TranslationKey.namespace_id == namespace_id,
            TranslationKey.key == key
        )
        if exclude_id:
            query = query.filter(TranslationKey.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: TranslationKeyFilters = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "key",
        sort_dir: str = "asc"
    ) -> Tuple[List[TranslationKey], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    TranslationKey.key.ilike(term),
                    TranslationKey.description.ilike(term)
                ))
            if filters.namespace_id:
                query = query.filter(TranslationKey.namespace_id == filters.namespace_id)
            if filters.namespace_code:
                query = query.join(TranslationNamespace).filter(
                    TranslationNamespace.code == filters.namespace_code
                )
            if filters.scope:
                query = query.filter(TranslationKey.scope == filters.scope)
            if filters.tags:
                query = query.filter(TranslationKey.tags.contains(filters.tags))
            if filters.entity_type:
                query = query.filter(TranslationKey.entity_type == filters.entity_type)

        total = query.count()
        sort_col = getattr(TranslationKey, sort_by, TranslationKey.key)
        query = query.order_by(asc(sort_col) if sort_dir == "asc" else desc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def list_by_namespace(self, namespace_id: UUID) -> List[TranslationKey]:
        return self._base_query().filter(
            TranslationKey.namespace_id == namespace_id
        ).order_by(TranslationKey.key).all()

    def list_by_entity(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> List[TranslationKey]:
        return self._base_query().filter(
            TranslationKey.entity_type == entity_type,
            TranslationKey.entity_id == entity_id
        ).all()

    def get_missing_for_language(
        self,
        language_id: UUID,
        namespace_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[TranslationKey]:
        """Recupere les cles sans traduction pour une langue."""
        subquery = self.db.query(Translation.translation_key_id).filter(
            Translation.tenant_id == self.tenant_id,
            Translation.language_id == language_id,
            Translation.deleted_at.is_(None)
        ).subquery()

        query = self._base_query().filter(
            ~TranslationKey.id.in_(subquery)
        )

        if namespace_id:
            query = query.filter(TranslationKey.namespace_id == namespace_id)

        return query.limit(limit).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> TranslationKey:
        entity = TranslationKey(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: TranslationKey,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> TranslationKey:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: TranslationKey, deleted_by: UUID = None) -> bool:
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True

    def bulk_create(self, items: List[Dict[str, Any]], created_by: UUID = None) -> int:
        now = datetime.utcnow()
        for item in items:
            item["tenant_id"] = self.tenant_id
            item["created_at"] = now
            item["created_by"] = created_by
        self.db.bulk_insert_mappings(TranslationKey, items)
        self.db.commit()
        return len(items)


# ============================================================================
# TRANSLATION REPOSITORY
# ============================================================================

class TranslationRepository:
    """Repository Translation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(Translation).filter(
            Translation.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Translation.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[Translation]:
        return self._base_query().filter(Translation.id == id).first()

    def get_by_key_language(
        self,
        translation_key_id: UUID,
        language_id: UUID
    ) -> Optional[Translation]:
        return self._base_query().filter(
            Translation.translation_key_id == translation_key_id,
            Translation.language_id == language_id
        ).first()

    def get_value(
        self,
        namespace_code: str,
        key: str,
        language_code: str,
        fallback_language_code: str = "en"
    ) -> Optional[str]:
        """Recupere la valeur traduite avec fallback."""
        result = self._base_query().join(TranslationKey).join(TranslationNamespace).filter(
            TranslationNamespace.code == namespace_code,
            TranslationKey.key == key,
            Translation.language_code == language_code
        ).first()

        if result:
            return result.value

        # Fallback
        if language_code != fallback_language_code:
            result = self._base_query().join(TranslationKey).join(TranslationNamespace).filter(
                TranslationNamespace.code == namespace_code,
                TranslationKey.key == key,
                Translation.language_code == fallback_language_code
            ).first()
            if result:
                return result.value

        return None

    def list(
        self,
        filters: TranslationFilters = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Translation], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(Translation.value.ilike(term))
            if filters.language_code:
                query = query.filter(Translation.language_code == filters.language_code)
            if filters.status:
                query = query.filter(Translation.status.in_(filters.status))
            if filters.is_machine_translated is not None:
                query = query.filter(
                    Translation.is_machine_translated == filters.is_machine_translated
                )

        total = query.count()
        sort_col = getattr(Translation, sort_by, Translation.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    def list_by_language(
        self,
        language_code: str,
        namespace_code: Optional[str] = None
    ) -> List[Translation]:
        """Liste toutes les traductions d'une langue."""
        query = self._base_query().filter(
            Translation.language_code == language_code
        )
        if namespace_code:
            query = query.join(TranslationKey).join(TranslationNamespace).filter(
                TranslationNamespace.code == namespace_code
            )
        return query.all()

    def list_needs_review(self, limit: int = 100) -> List[Translation]:
        """Liste les traductions a revoir."""
        return self._base_query().filter(
            Translation.status == TranslationStatus.NEEDS_REVIEW
        ).limit(limit).all()

    def list_machine_translated(
        self,
        language_code: Optional[str] = None,
        limit: int = 100
    ) -> List[Translation]:
        """Liste les traductions automatiques non validees."""
        query = self._base_query().filter(
            Translation.is_machine_translated == True,
            Translation.status != TranslationStatus.VALIDATED
        )
        if language_code:
            query = query.filter(Translation.language_code == language_code)
        return query.limit(limit).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Translation:
        entity = Translation(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: Translation,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> Translation:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def validate(self, entity: Translation, validated_by: UUID) -> Translation:
        """Valide une traduction."""
        entity.status = TranslationStatus.VALIDATED
        entity.validated_by = validated_by
        entity.validated_at = datetime.utcnow()
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Translation, deleted_by: UUID = None) -> bool:
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True

    def bulk_upsert(
        self,
        translations: List[Dict[str, Any]],
        created_by: UUID = None
    ) -> Tuple[int, int]:
        """Insert ou update en masse. Retourne (created, updated)."""
        created = 0
        updated = 0
        now = datetime.utcnow()

        for trans in translations:
            existing = self.get_by_key_language(
                trans["translation_key_id"],
                trans["language_id"]
            )
            if existing:
                existing.value = trans["value"]
                existing.plural_values = trans.get("plural_values", {})
                existing.status = trans.get("status", existing.status)
                existing.updated_by = created_by
                existing.updated_at = now
                existing.version += 1
                updated += 1
            else:
                trans["tenant_id"] = self.tenant_id
                trans["created_at"] = now
                trans["created_by"] = created_by
                entity = Translation(**trans)
                self.db.add(entity)
                created += 1

        self.db.commit()
        return created, updated

    def get_bundle(
        self,
        language_code: str,
        namespace_code: str
    ) -> Dict[str, Any]:
        """Recupere un bundle de traductions pour le frontend."""
        results = self._base_query().join(TranslationKey).join(TranslationNamespace).filter(
            TranslationNamespace.code == namespace_code,
            Translation.language_code == language_code
        ).all()

        bundle = {}
        for trans in results:
            key = trans.translation_key.key
            if trans.translation_key.supports_plural and trans.plural_values:
                bundle[key] = trans.plural_values
            else:
                bundle[key] = trans.value

        return bundle


# ============================================================================
# CACHE REPOSITORY
# ============================================================================

class CacheRepository:
    """Repository pour le cache de traductions."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(TranslationCache).filter(
            TranslationCache.tenant_id == self.tenant_id
        )

    def get(self, namespace_code: str, language_code: str) -> Optional[TranslationCache]:
        return self._base_query().filter(
            TranslationCache.namespace_code == namespace_code,
            TranslationCache.language_code == language_code,
            TranslationCache.is_valid == True
        ).first()

    def set(
        self,
        namespace_code: str,
        language_code: str,
        translations: Dict[str, Any]
    ) -> TranslationCache:
        """Met a jour ou cree une entree de cache."""
        existing = self._base_query().filter(
            TranslationCache.namespace_code == namespace_code,
            TranslationCache.language_code == language_code
        ).first()

        now = datetime.utcnow()

        if existing:
            existing.translations = translations
            existing.generated_at = now
            existing.is_valid = True
            existing.key_count = len(translations)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            cache = TranslationCache(
                tenant_id=self.tenant_id,
                namespace_code=namespace_code,
                language_code=language_code,
                translations=translations,
                generated_at=now,
                is_valid=True,
                key_count=len(translations)
            )
            self.db.add(cache)
            self.db.commit()
            self.db.refresh(cache)
            return cache

    def invalidate(
        self,
        namespace_code: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> int:
        """Invalide le cache."""
        query = self._base_query()
        if namespace_code:
            query = query.filter(TranslationCache.namespace_code == namespace_code)
        if language_code:
            query = query.filter(TranslationCache.language_code == language_code)

        count = query.update({"is_valid": False}, synchronize_session=False)
        self.db.commit()
        return count

    def invalidate_all(self) -> int:
        """Invalide tout le cache du tenant."""
        count = self._base_query().update({"is_valid": False}, synchronize_session=False)
        self.db.commit()
        return count


# ============================================================================
# GLOSSARY REPOSITORY
# ============================================================================

class GlossaryRepository:
    """Repository Glossary avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(Glossary).filter(
            Glossary.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Glossary.deleted_at.is_(None))
        return query

    def get_by_id(self, id: UUID) -> Optional[Glossary]:
        return self._base_query().filter(Glossary.id == id).first()

    def get_by_term(
        self,
        source_term: str,
        source_language_code: str
    ) -> Optional[Glossary]:
        return self._base_query().filter(
            Glossary.source_term == source_term,
            Glossary.source_language_code == source_language_code
        ).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        term_type: Optional[str] = None
    ) -> Tuple[List[Glossary], int]:
        query = self._base_query()

        if search:
            term = f"%{search}%"
            query = query.filter(or_(
                Glossary.source_term.ilike(term),
                Glossary.definition.ilike(term)
            ))
        if term_type:
            query = query.filter(Glossary.term_type == term_type)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Glossary.source_term).offset(offset).limit(page_size).all()
        return items, total

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Glossary:
        entity = Glossary(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: Glossary,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> Glossary:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Glossary, deleted_by: UUID = None) -> bool:
        entity.deleted_at = datetime.utcnow()
        entity.is_active = False
        self.db.commit()
        return True


# ============================================================================
# TRANSLATION JOB REPOSITORY
# ============================================================================

class TranslationJobRepository:
    """Repository TranslationJob avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(TranslationJob).filter(
            TranslationJob.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[TranslationJob]:
        return self._base_query().filter(TranslationJob.id == id).first()

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[TranslationJobStatus] = None
    ) -> Tuple[List[TranslationJob], int]:
        query = self._base_query()
        if status:
            query = query.filter(TranslationJob.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(TranslationJob.created_at)).offset(offset).limit(page_size).all()
        return items, total

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> TranslationJob:
        entity = TranslationJob(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: TranslationJob, data: Dict[str, Any]) -> TranslationJob:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity
