"""
AZALSCORE Module I18N - Service Complet
========================================

Service d'internationalisation complet pour AZALSCORE ERP.
Inspire des meilleures pratiques de Odoo, SAP et Microsoft Dynamics 365.

Fonctionnalites:
- Gestion des langues par tenant
- Traductions par cle avec namespaces
- Gestion des pluriels (ICU MessageFormat)
- Formats regionaux (dates, nombres, devises)
- Traduction automatique (OpenAI, Google, DeepL)
- Import/Export (JSON, PO, XLIFF, CSV)
- Cache des traductions
- Dashboard couverture traduction
"""
from __future__ import annotations


import json
import logging
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import uuid as uuid_module

from sqlalchemy.orm import Session

from .models import (
    Language, LanguageStatus,
    TranslationNamespace,
    TranslationKey, TranslationScope,
    Translation, TranslationStatus,
    TranslationJob, TranslationJobStatus,
    TranslationImportExport, ImportExportFormat,
    TranslationCache,
    Glossary,
    DateFormatType, NumberFormatType,
)
from .repository import (
    LanguageRepository,
    NamespaceRepository,
    TranslationKeyRepository,
    TranslationRepository,
    CacheRepository,
    GlossaryRepository,
    TranslationJobRepository,
)
from .schemas import (
    LanguageCreate, LanguageUpdate,
    NamespaceCreate, NamespaceUpdate,
    TranslationKeyCreate, TranslationKeyUpdate,
    TranslationCreate, TranslationUpdate, TranslationBulkUpdate,
    AutoTranslateRequest,
    ImportRequest, ExportRequest,
    GlossaryCreate, GlossaryUpdate,
    TranslationBundle,
    TranslationDashboard, LanguageStats, CoverageReport,
    InlineTranslationRequest, InlineTranslationResponse,
)
from .exceptions import (
    LanguageNotFoundError, LanguageDuplicateError, LanguageDeleteError,
    NamespaceNotFoundError, NamespaceDuplicateError, NamespaceNotEditableError,
    TranslationKeyNotFoundError, TranslationKeyDuplicateError,
    TranslationNotFoundError, TranslationDuplicateError, TranslationLengthError,
    ImportFormatError, ImportParseError, ExportError,
    AutoTranslationError, AutoTranslationProviderError,
    GlossaryTermNotFoundError, GlossaryTermDuplicateError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES DE FORMATAGE
# ============================================================================

MONTH_NAMES = {
    "fr": ["janvier", "fevrier", "mars", "avril", "mai", "juin",
           "juillet", "aout", "septembre", "octobre", "novembre", "decembre"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "de": ["Januar", "Februar", "Marz", "April", "Mai", "Juni",
           "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
}

DAY_NAMES = {
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "es": ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"],
}


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class I18NService:
    """
    Service complet d'internationalisation.

    Usage:
        service = I18NService(db, tenant_id)
        text = service.t("button.save", "fr")
        formatted = service.format_currency(Decimal("1234.56"), "EUR", "fr")
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self.language_repo = LanguageRepository(db, tenant_id)
        self.namespace_repo = NamespaceRepository(db, tenant_id)
        self.key_repo = TranslationKeyRepository(db, tenant_id)
        self.translation_repo = TranslationRepository(db, tenant_id)
        self.cache_repo = CacheRepository(db, tenant_id)
        self.glossary_repo = GlossaryRepository(db, tenant_id)
        self.job_repo = TranslationJobRepository(db, tenant_id)

        # Cache local
        self._bundle_cache: Dict[str, Dict[str, Any]] = {}

    # ========================================================================
    # GESTION DES LANGUES
    # ========================================================================

    def list_languages(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> Tuple[List[Language], int]:
        """Liste les langues avec pagination."""
        from .schemas import LanguageFilters
        return self.language_repo.list(
            LanguageFilters(**filters) if filters else None,
            page, page_size
        )

    def get_language(self, language_id: UUID) -> Language:
        """Recupere une langue par ID."""
        lang = self.language_repo.get_by_id(language_id)
        if not lang:
            raise LanguageNotFoundError(str(language_id))
        return lang

    def get_language_by_code(self, code: str) -> Language:
        """Recupere une langue par code."""
        lang = self.language_repo.get_by_code(code)
        if not lang:
            raise LanguageNotFoundError(code)
        return lang

    def get_default_language(self) -> Optional[Language]:
        """Recupere la langue par defaut."""
        return self.language_repo.get_default()

    def get_active_languages(self) -> List[Language]:
        """Liste les langues actives."""
        return self.language_repo.list_active()

    def create_language(
        self,
        data: LanguageCreate,
        created_by: UUID = None
    ) -> Language:
        """Cree une nouvelle langue."""
        if self.language_repo.code_exists(data.code):
            raise LanguageDuplicateError(data.code)

        lang = self.language_repo.create(
            data.model_dump(exclude_unset=True),
            created_by
        )

        # Invalider le cache
        self.cache_repo.invalidate_all()

        return lang

    def update_language(
        self,
        language_id: UUID,
        data: LanguageUpdate,
        updated_by: UUID = None
    ) -> Language:
        """Met a jour une langue."""
        lang = self.get_language(language_id)
        updated = self.language_repo.update(
            lang,
            data.model_dump(exclude_unset=True),
            updated_by
        )

        # Invalider le cache de cette langue
        self.cache_repo.invalidate(language_code=lang.code)

        return updated

    def delete_language(
        self,
        language_id: UUID,
        deleted_by: UUID = None,
        hard: bool = False
    ) -> bool:
        """Supprime une langue."""
        lang = self.get_language(language_id)

        can_delete, reason = lang.can_delete()
        if not can_delete:
            raise LanguageDeleteError(reason)

        if hard:
            self.language_repo.hard_delete(lang)
        else:
            self.language_repo.soft_delete(lang, deleted_by)

        # Invalider le cache
        self.cache_repo.invalidate(language_code=lang.code)

        return True

    def set_default_language(
        self,
        language_id: UUID,
        updated_by: UUID = None
    ) -> Language:
        """Definit la langue par defaut."""
        return self.language_repo.set_default(language_id, updated_by)

    # ========================================================================
    # GESTION DES NAMESPACES
    # ========================================================================

    def list_namespaces(
        self,
        page: int = 1,
        page_size: int = 50,
        **filters
    ) -> Tuple[List[TranslationNamespace], int]:
        """Liste les namespaces avec pagination."""
        return self.namespace_repo.list(
            page, page_size,
            search=filters.get("search"),
            module_code=filters.get("module_code")
        )

    def get_namespace(self, namespace_id: UUID) -> TranslationNamespace:
        """Recupere un namespace par ID."""
        ns = self.namespace_repo.get_by_id(namespace_id)
        if not ns:
            raise NamespaceNotFoundError(str(namespace_id))
        return ns

    def get_namespace_by_code(self, code: str) -> TranslationNamespace:
        """Recupere un namespace par code."""
        ns = self.namespace_repo.get_by_code(code)
        if not ns:
            raise NamespaceNotFoundError(code)
        return ns

    def create_namespace(
        self,
        data: NamespaceCreate,
        created_by: UUID = None
    ) -> TranslationNamespace:
        """Cree un nouveau namespace."""
        if self.namespace_repo.code_exists(data.code):
            raise NamespaceDuplicateError(data.code)

        return self.namespace_repo.create(
            data.model_dump(exclude_unset=True),
            created_by
        )

    def update_namespace(
        self,
        namespace_id: UUID,
        data: NamespaceUpdate,
        updated_by: UUID = None
    ) -> TranslationNamespace:
        """Met a jour un namespace."""
        ns = self.get_namespace(namespace_id)

        if not ns.is_editable:
            raise NamespaceNotEditableError(ns.code)

        updated = self.namespace_repo.update(
            ns,
            data.model_dump(exclude_unset=True),
            updated_by
        )

        # Invalider le cache du namespace
        self.cache_repo.invalidate(namespace_code=ns.code)

        return updated

    def delete_namespace(
        self,
        namespace_id: UUID,
        deleted_by: UUID = None
    ) -> bool:
        """Supprime un namespace."""
        ns = self.get_namespace(namespace_id)

        if ns.is_system:
            raise NamespaceNotEditableError(ns.code)

        self.namespace_repo.soft_delete(ns, deleted_by)
        self.cache_repo.invalidate(namespace_code=ns.code)

        return True

    def ensure_namespace(
        self,
        code: str,
        name: str = None,
        created_by: UUID = None
    ) -> TranslationNamespace:
        """Cree le namespace s'il n'existe pas."""
        existing = self.namespace_repo.get_by_code(code)
        if existing:
            return existing

        return self.namespace_repo.create({
            "code": code,
            "name": name or code.replace("_", " ").title(),
        }, created_by)

    # ========================================================================
    # GESTION DES CLES DE TRADUCTION
    # ========================================================================

    def list_translation_keys(
        self,
        page: int = 1,
        page_size: int = 50,
        **filters
    ) -> Tuple[List[TranslationKey], int]:
        """Liste les cles de traduction."""
        from .schemas import TranslationKeyFilters
        return self.key_repo.list(
            TranslationKeyFilters(**filters) if filters else None,
            page, page_size
        )

    def get_translation_key(self, key_id: UUID) -> TranslationKey:
        """Recupere une cle par ID."""
        key = self.key_repo.get_by_id(key_id)
        if not key:
            raise TranslationKeyNotFoundError(str(key_id))
        return key

    def get_translation_key_by_full_key(
        self,
        namespace_code: str,
        key: str
    ) -> TranslationKey:
        """Recupere une cle par namespace.key"""
        tk = self.key_repo.get_by_full_key(namespace_code, key)
        if not tk:
            raise TranslationKeyNotFoundError(f"{namespace_code}.{key}")
        return tk

    def create_translation_key(
        self,
        data: TranslationKeyCreate,
        created_by: UUID = None
    ) -> TranslationKey:
        """Cree une nouvelle cle de traduction."""
        # Verifier unicite
        if self.key_repo.key_exists(data.namespace_id, data.key):
            ns = self.get_namespace(data.namespace_id)
            raise TranslationKeyDuplicateError(ns.code, data.key)

        # Extraire les traductions initiales
        initial_translations = data.translations or {}
        key_data = data.model_dump(exclude_unset=True, exclude={"translations"})

        key = self.key_repo.create(key_data, created_by)

        # Creer les traductions initiales
        if initial_translations:
            for lang_code, value in initial_translations.items():
                try:
                    lang = self.get_language_by_code(lang_code)
                    self.translation_repo.create({
                        "translation_key_id": key.id,
                        "language_id": lang.id,
                        "language_code": lang_code,
                        "value": value,
                        "status": TranslationStatus.DRAFT,
                    }, created_by)
                except LanguageNotFoundError:
                    logger.warning(f"Language {lang_code} not found, skipping translation")

        # Invalider le cache du namespace
        ns = self.get_namespace(data.namespace_id)
        self.cache_repo.invalidate(namespace_code=ns.code)

        return key

    def update_translation_key(
        self,
        key_id: UUID,
        data: TranslationKeyUpdate,
        updated_by: UUID = None
    ) -> TranslationKey:
        """Met a jour une cle de traduction."""
        key = self.get_translation_key(key_id)
        ns = self.get_namespace(key.namespace_id)

        updated = self.key_repo.update(
            key,
            data.model_dump(exclude_unset=True),
            updated_by
        )

        self.cache_repo.invalidate(namespace_code=ns.code)

        return updated

    def delete_translation_key(
        self,
        key_id: UUID,
        deleted_by: UUID = None
    ) -> bool:
        """Supprime une cle de traduction."""
        key = self.get_translation_key(key_id)
        ns = self.get_namespace(key.namespace_id)

        self.key_repo.soft_delete(key, deleted_by)
        self.cache_repo.invalidate(namespace_code=ns.code)

        return True

    def get_missing_keys_for_language(
        self,
        language_code: str,
        namespace_code: Optional[str] = None,
        limit: int = 100
    ) -> List[TranslationKey]:
        """Recupere les cles sans traduction pour une langue."""
        lang = self.get_language_by_code(language_code)
        namespace_id = None
        if namespace_code:
            ns = self.get_namespace_by_code(namespace_code)
            namespace_id = ns.id
        return self.key_repo.get_missing_for_language(lang.id, namespace_id, limit)

    # ========================================================================
    # GESTION DES TRADUCTIONS
    # ========================================================================

    def t(
        self,
        key: str,
        language_code: str,
        namespace: str = "common",
        **params
    ) -> str:
        """
        Traduit une cle.

        Usage:
            service.t("button.save", "fr")
            service.t("greeting", "fr", name="John") -> "Bonjour John"
        """
        # Essayer le cache d'abord
        cache_key = f"{namespace}:{language_code}"
        if cache_key in self._bundle_cache:
            bundle = self._bundle_cache[cache_key]
            if key in bundle:
                return self._interpolate(bundle[key], params)

        # Sinon, requete DB
        value = self.translation_repo.get_value(
            namespace, key, language_code,
            fallback_language_code="en"
        )

        if value:
            return self._interpolate(value, params)

        # Retourner la cle si pas de traduction
        return key

    def tp(
        self,
        key: str,
        count: int,
        language_code: str,
        namespace: str = "common",
        **params
    ) -> str:
        """
        Traduit avec pluralisation.

        Usage:
            service.tp("item", 0, "fr") -> "aucun element"
            service.tp("item", 1, "fr") -> "1 element"
            service.tp("item", 5, "fr") -> "5 elements"
        """
        # Determiner la forme plurielle
        plural_form = self._get_plural_form(count, language_code)

        # Recuperer la traduction
        try:
            tk = self.key_repo.get_by_full_key(namespace, key)
            if tk and tk.supports_plural:
                lang = self.language_repo.get_by_code(language_code)
                if lang:
                    trans = self.translation_repo.get_by_key_language(tk.id, lang.id)
                    if trans and trans.plural_values:
                        value = trans.plural_values.get(
                            plural_form,
                            trans.plural_values.get("other", trans.value)
                        )
                        return self._interpolate(value, {**params, "count": count})
        except Exception:
            pass

        # Fallback sur traduction simple
        return self.t(key, language_code, namespace, count=count, **params)

    def _get_plural_form(self, count: int, language_code: str) -> str:
        """Determine la forme plurielle selon la langue."""
        # Regles simplifiees (ICU CLDR)
        if count == 0:
            return "zero"
        elif count == 1:
            return "one"
        elif language_code in ["fr", "pt", "it"] and count <= 1:
            return "one"
        elif language_code == "ar":
            if count == 2:
                return "two"
            elif 3 <= count <= 10:
                return "few"
            elif 11 <= count <= 99:
                return "many"
        elif language_code in ["pl", "ru", "uk"]:
            mod10 = count % 10
            mod100 = count % 100
            if mod10 == 1 and mod100 != 11:
                return "one"
            elif 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
                return "few"
            else:
                return "many"

        return "other"

    def _interpolate(self, template: str, params: Dict[str, Any]) -> str:
        """Interpole les parametres dans le template."""
        result = template
        for key, value in params.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def get_translation(
        self,
        key_id: UUID,
        language_id: UUID
    ) -> Optional[Translation]:
        """Recupere une traduction specifique."""
        return self.translation_repo.get_by_key_language(key_id, language_id)

    def set_translation(
        self,
        key_id: UUID,
        language_id: UUID,
        value: str,
        plural_values: Dict[str, str] = None,
        status: TranslationStatus = TranslationStatus.DRAFT,
        created_by: UUID = None
    ) -> Translation:
        """Definit ou met a jour une traduction."""
        key = self.get_translation_key(key_id)
        lang = self.get_language(language_id)

        # Verifier longueur max
        if key.max_length and len(value) > key.max_length:
            raise TranslationLengthError(key.key, key.max_length, len(value))

        existing = self.translation_repo.get_by_key_language(key_id, language_id)

        if existing:
            updated = self.translation_repo.update(existing, {
                "value": value,
                "plural_values": plural_values or {},
                "status": status,
            }, created_by)
        else:
            updated = self.translation_repo.create({
                "translation_key_id": key_id,
                "language_id": language_id,
                "language_code": lang.code,
                "value": value,
                "plural_values": plural_values or {},
                "status": status,
            }, created_by)

        # Invalider le cache
        ns = self.get_namespace(key.namespace_id)
        self.cache_repo.invalidate(namespace_code=ns.code, language_code=lang.code)
        self._bundle_cache.pop(f"{ns.code}:{lang.code}", None)

        # Mettre a jour la couverture
        self.language_repo.update_coverage(language_id)

        return updated

    def validate_translation(
        self,
        translation_id: UUID,
        validated_by: UUID
    ) -> Translation:
        """Valide une traduction."""
        trans = self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise TranslationNotFoundError("ID", str(translation_id))
        return self.translation_repo.validate(trans, validated_by)

    def bulk_update_translations(
        self,
        data: TranslationBulkUpdate,
        created_by: UUID = None
    ) -> Tuple[int, int]:
        """Mise a jour en masse des traductions."""
        ns = self.get_namespace_by_code(data.namespace_code)
        lang = self.get_language_by_code(data.language_code)

        translations = []
        for key, value in data.translations.items():
            tk = self.key_repo.get_by_key(ns.id, key)
            if not tk:
                # Creer la cle si elle n'existe pas
                tk = self.key_repo.create({
                    "namespace_id": ns.id,
                    "key": key,
                    "scope": TranslationScope.TENANT,
                }, created_by)

            translations.append({
                "translation_key_id": tk.id,
                "language_id": lang.id,
                "language_code": lang.code,
                "value": value,
                "status": data.status,
            })

        created, updated = self.translation_repo.bulk_upsert(translations, created_by)

        # Invalider le cache
        self.cache_repo.invalidate(namespace_code=ns.code, language_code=lang.code)
        self._bundle_cache.pop(f"{ns.code}:{lang.code}", None)

        # Mettre a jour la couverture
        self.language_repo.update_coverage(lang.id)

        return created, updated

    def inline_translate(
        self,
        request: InlineTranslationRequest,
        created_by: UUID = None
    ) -> InlineTranslationResponse:
        """Traduction inline depuis le frontend."""
        ns = self.ensure_namespace(request.namespace, created_by=created_by)
        lang = self.get_language_by_code(request.language)

        # Chercher ou creer la cle
        tk = self.key_repo.get_by_key(ns.id, request.key)
        created_key = False
        if not tk:
            if not request.create_if_missing:
                raise TranslationKeyNotFoundError(f"{request.namespace}.{request.key}")
            tk = self.key_repo.create({
                "namespace_id": ns.id,
                "key": request.key,
                "scope": TranslationScope.TENANT,
            }, created_by)
            created_key = True

        # Chercher ou creer la traduction
        existing = self.translation_repo.get_by_key_language(tk.id, lang.id)
        if existing:
            self.translation_repo.update(existing, {"value": request.value}, created_by)
            return InlineTranslationResponse(
                key=request.key,
                namespace=request.namespace,
                language=request.language,
                value=request.value,
                created=False,
                updated=True
            )
        else:
            self.translation_repo.create({
                "translation_key_id": tk.id,
                "language_id": lang.id,
                "language_code": lang.code,
                "value": request.value,
                "status": TranslationStatus.DRAFT,
            }, created_by)

            # Invalider le cache
            self.cache_repo.invalidate(namespace_code=ns.code, language_code=lang.code)

            return InlineTranslationResponse(
                key=request.key,
                namespace=request.namespace,
                language=request.language,
                value=request.value,
                created=True,
                updated=False
            )

    # ========================================================================
    # BUNDLES & CACHE
    # ========================================================================

    def get_bundle(
        self,
        language_code: str,
        namespace_code: str,
        use_cache: bool = True
    ) -> TranslationBundle:
        """
        Recupere un bundle de traductions pour le frontend.

        Utilise le cache pour de meilleures performances.
        """
        cache_key = f"{namespace_code}:{language_code}"

        # Verifier le cache local
        if use_cache and cache_key in self._bundle_cache:
            return TranslationBundle(
                language=language_code,
                namespace=namespace_code,
                translations=self._bundle_cache[cache_key],
                generated_at=datetime.utcnow(),
                key_count=len(self._bundle_cache[cache_key])
            )

        # Verifier le cache DB
        if use_cache:
            cached = self.cache_repo.get(namespace_code, language_code)
            if cached and cached.is_valid:
                self._bundle_cache[cache_key] = cached.translations
                return TranslationBundle(
                    language=language_code,
                    namespace=namespace_code,
                    translations=cached.translations,
                    generated_at=cached.generated_at,
                    key_count=cached.key_count
                )

        # Generer le bundle
        translations = self.translation_repo.get_bundle(language_code, namespace_code)

        # Mettre en cache
        self.cache_repo.set(namespace_code, language_code, translations)
        self._bundle_cache[cache_key] = translations

        return TranslationBundle(
            language=language_code,
            namespace=namespace_code,
            translations=translations,
            generated_at=datetime.utcnow(),
            key_count=len(translations)
        )

    def get_bundles(
        self,
        language_code: str,
        namespace_codes: List[str]
    ) -> Dict[str, TranslationBundle]:
        """Recupere plusieurs bundles."""
        return {
            ns: self.get_bundle(language_code, ns)
            for ns in namespace_codes
        }

    def invalidate_cache(
        self,
        namespace_code: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> int:
        """Invalide le cache."""
        count = self.cache_repo.invalidate(namespace_code, language_code)

        # Vider le cache local
        if namespace_code and language_code:
            self._bundle_cache.pop(f"{namespace_code}:{language_code}", None)
        elif namespace_code:
            keys_to_remove = [k for k in self._bundle_cache if k.startswith(f"{namespace_code}:")]
            for k in keys_to_remove:
                self._bundle_cache.pop(k, None)
        elif language_code:
            keys_to_remove = [k for k in self._bundle_cache if k.endswith(f":{language_code}")]
            for k in keys_to_remove:
                self._bundle_cache.pop(k, None)
        else:
            self._bundle_cache.clear()

        return count

    # ========================================================================
    # FORMATAGE REGIONAL
    # ========================================================================

    def format_date(
        self,
        dt: date,
        language_code: str,
        format_type: DateFormatType = None
    ) -> str:
        """Formate une date selon la locale."""
        lang = self.language_repo.get_by_code(language_code)
        fmt = format_type or (lang.date_format if lang else DateFormatType.DMY)
        separator = lang.date_separator if lang else "/"

        if fmt == DateFormatType.DMY:
            return f"{dt.day:02d}{separator}{dt.month:02d}{separator}{dt.year}"
        elif fmt == DateFormatType.MDY:
            return f"{dt.month:02d}{separator}{dt.day:02d}{separator}{dt.year}"
        elif fmt == DateFormatType.YMD:
            return f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
        elif fmt == DateFormatType.LONG:
            months = MONTH_NAMES.get(language_code, MONTH_NAMES["en"])
            return f"{dt.day} {months[dt.month - 1]} {dt.year}"

        return str(dt)

    def format_datetime(
        self,
        dt: datetime,
        language_code: str,
        include_time: bool = True
    ) -> str:
        """Formate une date/heure."""
        date_str = self.format_date(dt.date(), language_code)

        if not include_time:
            return date_str

        lang = self.language_repo.get_by_code(language_code)
        if lang and lang.time_format_24h:
            time_str = dt.strftime("%H:%M")
        else:
            time_str = dt.strftime("%I:%M %p")

        return f"{date_str} {time_str}"

    def format_number(
        self,
        number: Decimal,
        language_code: str,
        decimals: int = 2
    ) -> str:
        """Formate un nombre selon la locale."""
        lang = self.language_repo.get_by_code(language_code)

        decimal_sep = lang.decimal_separator if lang else ","
        thousands_sep = lang.thousands_separator if lang else " "

        # Arrondir
        if decimals > 0:
            quantize_str = "0." + "0" * decimals
        else:
            quantize_str = "1"
        rounded = number.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

        # Separer partie entiere et decimale
        parts = str(rounded).split(".")
        integer_part = parts[0].lstrip("-")
        decimal_part = parts[1] if len(parts) > 1 else ""
        is_negative = str(rounded).startswith("-")

        # Ajouter les separateurs de milliers
        integer_with_sep = ""
        for i, digit in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0:
                integer_with_sep = thousands_sep + integer_with_sep
            integer_with_sep = digit + integer_with_sep

        # Assembler
        result = integer_with_sep
        if decimal_part:
            result = f"{result}{decimal_sep}{decimal_part}"
        if is_negative:
            result = f"-{result}"

        return result

    def format_currency(
        self,
        amount: Decimal,
        currency_symbol: str,
        language_code: str,
        decimals: int = 2
    ) -> str:
        """Formate un montant avec devise."""
        lang = self.language_repo.get_by_code(language_code)
        position = lang.currency_position if lang else "after"

        formatted_number = self.format_number(amount, language_code, decimals)

        if position == "before":
            return f"{currency_symbol}{formatted_number}"
        else:
            return f"{formatted_number} {currency_symbol}"

    def format_percent(
        self,
        value: Decimal,
        language_code: str,
        decimals: int = 2
    ) -> str:
        """Formate un pourcentage."""
        formatted = self.format_number(value, language_code, decimals)
        return f"{formatted} %"

    # ========================================================================
    # IMPORT / EXPORT
    # ========================================================================

    def export_translations(
        self,
        request: ExportRequest,
        created_by: UUID = None
    ) -> Dict[str, Any]:
        """Exporte les traductions."""
        result = {}

        # Recuperer les namespaces
        if request.namespace_codes:
            namespaces = [
                self.namespace_repo.get_by_code(code)
                for code in request.namespace_codes
            ]
        else:
            namespaces = self.namespace_repo.list_all()

        for ns in namespaces:
            if not ns:
                continue

            ns_data = {}
            keys = self.key_repo.list_by_namespace(ns.id)

            for key in keys:
                key_data = {}
                for lang_code in request.language_codes:
                    try:
                        lang = self.language_repo.get_by_code(lang_code)
                        if not lang:
                            continue
                        trans = self.translation_repo.get_by_key_language(key.id, lang.id)
                        if trans:
                            if key.supports_plural and trans.plural_values:
                                key_data[lang_code] = trans.plural_values
                            else:
                                key_data[lang_code] = trans.value
                        elif request.include_empty:
                            key_data[lang_code] = ""
                    except LanguageNotFoundError:
                        pass

                if key_data or request.include_empty:
                    if request.include_metadata:
                        ns_data[key.key] = {
                            "translations": key_data,
                            "description": key.description,
                            "context": key.context,
                            "supports_plural": key.supports_plural,
                            "parameters": key.parameters,
                        }
                    else:
                        ns_data[key.key] = key_data

            if ns_data:
                result[ns.code] = ns_data

        return result

    def import_translations(
        self,
        data: Dict[str, Any],
        request: ImportRequest,
        created_by: UUID = None
    ) -> Tuple[int, int, int, List[Dict]]:
        """
        Importe des traductions.

        Retourne: (created, updated, skipped, errors)
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for namespace_code, keys in data.items():
            # Creer le namespace si necessaire
            ns = self.ensure_namespace(namespace_code, created_by=created_by)

            for key_name, translations in keys.items():
                try:
                    # Gerer le format avec metadata
                    if isinstance(translations, dict) and "translations" in translations:
                        trans_data = translations["translations"]
                        metadata = translations
                    else:
                        trans_data = translations
                        metadata = {}

                    # Creer/recuperer la cle
                    tk = self.key_repo.get_by_key(ns.id, key_name)
                    if not tk:
                        tk = self.key_repo.create({
                            "namespace_id": ns.id,
                            "key": key_name,
                            "scope": TranslationScope.TENANT,
                            "description": metadata.get("description"),
                            "context": metadata.get("context"),
                            "supports_plural": metadata.get("supports_plural", False),
                            "parameters": metadata.get("parameters", []),
                        }, created_by)

                    # Traiter les traductions
                    for lang_code, value in trans_data.items():
                        if request.language_codes and lang_code not in request.language_codes:
                            continue

                        try:
                            lang = self.language_repo.get_by_code(lang_code)
                            if not lang:
                                logger.warning(f"Language {lang_code} not found")
                                continue

                            existing = self.translation_repo.get_by_key_language(tk.id, lang.id)

                            if existing:
                                if request.overwrite_existing:
                                    if isinstance(value, dict):
                                        self.translation_repo.update(existing, {
                                            "plural_values": value,
                                            "value": value.get("one", value.get("other", "")),
                                            "status": TranslationStatus.VALIDATED if request.mark_as_validated else TranslationStatus.DRAFT,
                                        }, created_by)
                                    else:
                                        self.translation_repo.update(existing, {
                                            "value": value,
                                            "status": TranslationStatus.VALIDATED if request.mark_as_validated else TranslationStatus.DRAFT,
                                        }, created_by)
                                    updated += 1
                                else:
                                    skipped += 1
                            else:
                                if isinstance(value, dict):
                                    self.translation_repo.create({
                                        "translation_key_id": tk.id,
                                        "language_id": lang.id,
                                        "language_code": lang_code,
                                        "value": value.get("one", value.get("other", "")),
                                        "plural_values": value,
                                        "status": TranslationStatus.VALIDATED if request.mark_as_validated else TranslationStatus.DRAFT,
                                    }, created_by)
                                else:
                                    self.translation_repo.create({
                                        "translation_key_id": tk.id,
                                        "language_id": lang.id,
                                        "language_code": lang_code,
                                        "value": value,
                                        "status": TranslationStatus.VALIDATED if request.mark_as_validated else TranslationStatus.DRAFT,
                                    }, created_by)
                                created += 1

                        except Exception as e:
                            errors.append({
                                "namespace": namespace_code,
                                "key": key_name,
                                "language": lang_code,
                                "error": str(e)
                            })

                except Exception as e:
                    errors.append({
                        "namespace": namespace_code,
                        "key": key_name,
                        "error": str(e)
                    })

        # Invalider tout le cache
        self.invalidate_cache()

        # Mettre a jour les couvertures
        for lang in self.language_repo.list_active():
            self.language_repo.update_coverage(lang.id)

        return created, updated, skipped, errors

    # ========================================================================
    # TRADUCTION AUTOMATIQUE
    # ========================================================================

    async def auto_translate(
        self,
        request: AutoTranslateRequest,
        created_by: UUID = None
    ) -> TranslationJob:
        """
        Lance un job de traduction automatique.

        Supporte: openai, google, deepl, azure
        """
        source_lang = self.get_language_by_code(request.source_language_code)
        target_langs = [
            self.get_language_by_code(code)
            for code in request.target_language_codes
        ]

        # Creer le job
        job = self.job_repo.create({
            "source_language_id": source_lang.id,
            "target_language_ids": [str(lang.id) for lang in target_langs],
            "namespace_ids": [],
            "provider": request.provider,
            "model": request.model,
            "status": TranslationJobStatus.PENDING,
        }, created_by)

        # Lancer le job en arriere-plan (a implementer avec Celery/Redis)
        # Pour l'instant, execution synchrone simplifiee
        try:
            await self._execute_translation_job(job, source_lang, target_langs, request)
        except Exception as e:
            self.job_repo.update(job, {
                "status": TranslationJobStatus.FAILED,
                "error_message": str(e),
                "completed_at": datetime.utcnow()
            })

        return self.job_repo.get_by_id(job.id)

    async def _execute_translation_job(
        self,
        job: TranslationJob,
        source_lang: Language,
        target_langs: List[Language],
        request: AutoTranslateRequest
    ):
        """Execute le job de traduction."""
        self.job_repo.update(job, {
            "status": TranslationJobStatus.IN_PROGRESS,
            "started_at": datetime.utcnow()
        })

        # Recuperer les cles a traduire
        keys_query = self.key_repo._base_query()
        if request.scope:
            keys_query = keys_query.filter(TranslationKey.scope == request.scope)

        keys = keys_query.all()
        total_keys = len(keys) * len(target_langs)

        self.job_repo.update(job, {"total_keys": total_keys})

        processed = 0
        failed = 0

        for key in keys:
            # Recuperer la traduction source
            source_trans = self.translation_repo.get_by_key_language(key.id, source_lang.id)
            if not source_trans:
                continue

            for target_lang in target_langs:
                try:
                    # Verifier si traduction existe deja
                    existing = self.translation_repo.get_by_key_language(key.id, target_lang.id)
                    if existing and not request.overwrite_existing:
                        processed += 1
                        continue

                    # Appeler l'API de traduction
                    translated_value = await self._call_translation_api(
                        source_trans.value,
                        source_lang.code,
                        target_lang.code,
                        request.provider,
                        request.model
                    )

                    # Sauvegarder
                    if existing:
                        self.translation_repo.update(existing, {
                            "value": translated_value,
                            "is_machine_translated": True,
                            "machine_translation_provider": request.provider,
                            "status": TranslationStatus.MACHINE_TRANSLATED,
                        })
                    else:
                        self.translation_repo.create({
                            "translation_key_id": key.id,
                            "language_id": target_lang.id,
                            "language_code": target_lang.code,
                            "value": translated_value,
                            "is_machine_translated": True,
                            "machine_translation_provider": request.provider,
                            "status": TranslationStatus.MACHINE_TRANSLATED,
                        })

                    processed += 1

                except Exception as e:
                    logger.error(f"Translation failed for key {key.key}: {e}")
                    failed += 1

                # Mettre a jour la progression
                self.job_repo.update(job, {
                    "processed_keys": processed,
                    "failed_keys": failed
                })

        # Finaliser
        self.job_repo.update(job, {
            "status": TranslationJobStatus.COMPLETED,
            "completed_at": datetime.utcnow()
        })

        # Invalider le cache
        self.invalidate_cache()

    async def _call_translation_api(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        provider: str,
        model: Optional[str] = None
    ) -> str:
        """Appelle l'API de traduction."""
        if provider == "openai":
            return await self._translate_with_openai(text, source_lang, target_lang, model)
        elif provider == "google":
            return await self._translate_with_google(text, source_lang, target_lang)
        elif provider == "deepl":
            return await self._translate_with_deepl(text, source_lang, target_lang)
        else:
            raise AutoTranslationProviderError(provider)

    async def _translate_with_openai(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None
    ) -> str:
        """Traduction via OpenAI."""
        try:
            import openai
            client = openai.AsyncOpenAI()

            response = await client.chat.completions.create(
                model=model or "gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the following text from {source_lang} to {target_lang}. "
                                   f"Keep the same tone and style. Preserve any placeholders like {{name}} or {{count}}. "
                                   f"Return only the translated text, nothing else."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise AutoTranslationError("openai", str(e))

    async def _translate_with_google(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Traduction via Google Cloud Translation."""
        # A implementer avec google-cloud-translate
        raise AutoTranslationProviderError("google - not implemented")

    async def _translate_with_deepl(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Traduction via DeepL."""
        # A implementer avec deepl-python
        raise AutoTranslationProviderError("deepl - not implemented")

    # ========================================================================
    # DASHBOARD & STATISTIQUES
    # ========================================================================

    def get_dashboard(self) -> TranslationDashboard:
        """Recupere les donnees du dashboard."""
        languages = self.language_repo.list_active()
        all_langs, total_langs = self.language_repo.list(page_size=1000)

        # Compter les cles totales
        total_keys = self.key_repo._base_query().count()

        # Compter les traductions
        total_translations = self.translation_repo._base_query().count()

        # Stats par langue
        language_stats = []
        for lang in languages:
            translated = self.db.query(Translation).filter(
                Translation.tenant_id == self.tenant_id,
                Translation.language_id == lang.id,
                Translation.deleted_at.is_(None)
            ).count()

            needs_review = self.db.query(Translation).filter(
                Translation.tenant_id == self.tenant_id,
                Translation.language_id == lang.id,
                Translation.status == TranslationStatus.NEEDS_REVIEW,
                Translation.deleted_at.is_(None)
            ).count()

            machine_translated = self.db.query(Translation).filter(
                Translation.tenant_id == self.tenant_id,
                Translation.language_id == lang.id,
                Translation.is_machine_translated == True,
                Translation.status != TranslationStatus.VALIDATED,
                Translation.deleted_at.is_(None)
            ).count()

            language_stats.append(LanguageStats(
                language_code=lang.code,
                language_name=lang.name,
                total_keys=total_keys,
                translated_keys=translated,
                missing_keys=total_keys - translated,
                needs_review=needs_review,
                machine_translated=machine_translated,
                coverage_percent=(translated / total_keys * 100) if total_keys > 0 else 0
            ))

        # Couverture globale
        if total_keys > 0 and len(languages) > 0:
            overall_coverage = sum(s.coverage_percent for s in language_stats) / len(languages)
        else:
            overall_coverage = 0

        # Traductions a revoir
        pending_reviews = self.db.query(Translation).filter(
            Translation.tenant_id == self.tenant_id,
            Translation.status == TranslationStatus.NEEDS_REVIEW,
            Translation.deleted_at.is_(None)
        ).count()

        machine_pending = self.db.query(Translation).filter(
            Translation.tenant_id == self.tenant_id,
            Translation.is_machine_translated == True,
            Translation.status != TranslationStatus.VALIDATED,
            Translation.deleted_at.is_(None)
        ).count()

        return TranslationDashboard(
            total_languages=total_langs,
            active_languages=len(languages),
            total_keys=total_keys,
            total_translations=total_translations,
            overall_coverage=overall_coverage,
            languages_stats=language_stats,
            recent_activity=[],  # A implementer
            pending_reviews=pending_reviews,
            machine_translated_pending=machine_pending
        )

    def get_coverage_report(self, language_code: str) -> CoverageReport:
        """Rapport de couverture detaille pour une langue."""
        lang = self.get_language_by_code(language_code)
        namespaces = self.namespace_repo.list_all()

        ns_stats = []
        missing_keys = []
        needs_review = []

        for ns in namespaces:
            keys = self.key_repo.list_by_namespace(ns.id)
            total = len(keys)
            translated = 0

            for key in keys:
                trans = self.translation_repo.get_by_key_language(key.id, lang.id)
                if trans:
                    translated += 1
                    if trans.status == TranslationStatus.NEEDS_REVIEW:
                        needs_review.append(f"{ns.code}.{key.key}")
                else:
                    missing_keys.append(f"{ns.code}.{key.key}")

            ns_stats.append({
                "namespace": ns.code,
                "total": total,
                "translated": translated,
                "coverage": (translated / total * 100) if total > 0 else 100
            })

        return CoverageReport(
            language_code=language_code,
            namespaces=ns_stats,
            missing_keys=missing_keys[:100],  # Limiter
            needs_review=needs_review[:100]
        )

    # ========================================================================
    # GLOSSAIRE
    # ========================================================================

    def list_glossary_terms(
        self,
        page: int = 1,
        page_size: int = 50,
        **filters
    ) -> Tuple[List[Glossary], int]:
        """Liste les termes du glossaire."""
        return self.glossary_repo.list(
            page, page_size,
            search=filters.get("search"),
            term_type=filters.get("term_type")
        )

    def create_glossary_term(
        self,
        data: GlossaryCreate,
        created_by: UUID = None
    ) -> Glossary:
        """Cree un terme de glossaire."""
        existing = self.glossary_repo.get_by_term(
            data.source_term,
            data.source_language_code
        )
        if existing:
            raise GlossaryTermDuplicateError(data.source_term, data.source_language_code)

        return self.glossary_repo.create(
            data.model_dump(exclude_unset=True),
            created_by
        )

    def update_glossary_term(
        self,
        term_id: UUID,
        data: GlossaryUpdate,
        updated_by: UUID = None
    ) -> Glossary:
        """Met a jour un terme de glossaire."""
        term = self.glossary_repo.get_by_id(term_id)
        if not term:
            raise GlossaryTermNotFoundError(str(term_id))

        return self.glossary_repo.update(
            term,
            data.model_dump(exclude_unset=True),
            updated_by
        )

    def delete_glossary_term(
        self,
        term_id: UUID,
        deleted_by: UUID = None
    ) -> bool:
        """Supprime un terme de glossaire."""
        term = self.glossary_repo.get_by_id(term_id)
        if not term:
            raise GlossaryTermNotFoundError(str(term_id))

        return self.glossary_repo.soft_delete(term, deleted_by)


# ============================================================================
# FACTORY
# ============================================================================

def create_i18n_service(db: Session, tenant_id: str) -> I18NService:
    """Factory pour creer une instance du service I18N."""
    return I18NService(db=db, tenant_id=tenant_id)
