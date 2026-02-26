"""
AZALSCORE Module I18N - Modeles SQLAlchemy
===========================================

Internationalisation complete pour AZALSCORE ERP.
Inspire des meilleures pratiques de Odoo, SAP et Microsoft Dynamics 365.

Fonctionnalites:
- Langues supportees par tenant
- Traductions par cle avec namespaces
- Gestion des pluriels (ICU)
- Formats regionaux (dates, nombres, devises)
- Cache des traductions
- Import/Export fichiers de traduction

REGLES AZALSCORE:
- tenant_id obligatoire sur toutes les tables
- Soft delete avec deleted_at
- Audit complet (created_by, updated_by, etc.)
- Versioning des modifications
"""
from __future__ import annotations


import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.types import JSONB, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class LanguageStatus(str, enum.Enum):
    """Statut d'une langue."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BETA = "BETA"


class TranslationScope(str, enum.Enum):
    """Portee des traductions."""
    SYSTEM = "SYSTEM"       # Traductions systeme (UI)
    TENANT = "TENANT"       # Traductions specifiques tenant
    CONTENT = "CONTENT"     # Contenu metier (produits, etc.)
    CUSTOM = "CUSTOM"       # Personnalisations utilisateur


class TranslationStatus(str, enum.Enum):
    """Statut d'une traduction."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    MACHINE_TRANSLATED = "MACHINE_TRANSLATED"
    DEPRECATED = "DEPRECATED"


class DateFormatType(str, enum.Enum):
    """Formats de date."""
    DMY = "DMY"             # 31/12/2026
    MDY = "MDY"             # 12/31/2026
    YMD = "YMD"             # 2026-12-31
    LONG = "LONG"           # 31 decembre 2026


class NumberFormatType(str, enum.Enum):
    """Formats de nombres."""
    COMMA_DOT = "COMMA_DOT"       # 1,234.56 (US/UK)
    DOT_COMMA = "DOT_COMMA"       # 1.234,56 (DE/IT/ES)
    SPACE_COMMA = "SPACE_COMMA"   # 1 234,56 (FR)
    QUOTE_DOT = "QUOTE_DOT"       # 1'234.56 (CH)


class ImportExportFormat(str, enum.Enum):
    """Formats d'import/export."""
    JSON = "JSON"
    PO = "PO"               # GNU gettext
    XLIFF = "XLIFF"         # XML Localization
    CSV = "CSV"


class TranslationJobStatus(str, enum.Enum):
    """Statut d'un job de traduction."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ============================================================================
# LANGUE
# ============================================================================

class Language(Base):
    """
    Langue supportee par le tenant.

    Configuration des langues disponibles avec leurs parametres regionaux.
    """
    __tablename__ = "i18n_languages"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(10), nullable=False)           # fr, en, de, fr-CA
    name = Column(String(100), nullable=False)          # French
    native_name = Column(String(100), nullable=False)   # Francais

    # Parametres regionaux
    locale = Column(String(20))                         # fr_FR, en_US

    # Direction du texte
    rtl = Column(Boolean, default=False)                # Right-to-left

    # Formats
    date_format = Column(
        Enum(DateFormatType, name='i18n_date_format_type'),
        default=DateFormatType.DMY
    )
    date_separator = Column(String(5), default="/")
    time_format_24h = Column(Boolean, default=True)

    number_format = Column(
        Enum(NumberFormatType, name='i18n_number_format_type'),
        default=NumberFormatType.SPACE_COMMA
    )
    decimal_separator = Column(String(5), default=",")
    thousands_separator = Column(String(5), default=" ")

    # Devise
    currency_code = Column(String(3), default="EUR")
    currency_symbol = Column(String(10), default="EUR")
    currency_position = Column(String(10), default="after")  # before/after

    # Calendrier
    first_day_of_week = Column(Integer, default=1)  # 0=Dim, 1=Lun

    # Statut
    status = Column(
        Enum(LanguageStatus, name='i18n_language_status'),
        default=LanguageStatus.ACTIVE
    )
    is_default = Column(Boolean, default=False)
    is_fallback = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    # Flag/icone
    flag_emoji = Column(String(10))
    flag_url = Column(String(500))

    # Statistiques
    translation_coverage = Column(Numeric(5, 2), default=Decimal("0.00"))
    total_keys = Column(Integer, default=0)
    translated_keys = Column(Integer, default=0)

    # Audit
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    translations = relationship(
        "Translation",
        back_populates="language",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_i18n_lang_tenant_code'),
        Index('idx_i18n_lang_tenant', 'tenant_id'),
        Index('idx_i18n_lang_tenant_default', 'tenant_id', 'is_default'),
        Index('idx_i18n_lang_tenant_active', 'tenant_id', 'is_active'),
    )

    def can_delete(self) -> tuple[bool, str]:
        """Verifie si la langue peut etre supprimee."""
        if self.is_default:
            return False, "Cannot delete default language"
        if self.is_fallback:
            return False, "Cannot delete fallback language"
        return True, ""


# ============================================================================
# NAMESPACE DE TRADUCTION
# ============================================================================

class TranslationNamespace(Base):
    """
    Namespace pour organiser les traductions.

    Ex: common, invoicing, inventory, errors, etc.
    """
    __tablename__ = "i18n_namespaces"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)           # common, invoicing
    name = Column(String(100), nullable=False)          # Common translations
    description = Column(Text)

    # Hierarchie
    parent_id = Column(UniversalUUID(), ForeignKey("i18n_namespaces.id"))

    # Module associe
    module_code = Column(String(50))                    # accounting, crm

    # Configuration
    is_system = Column(Boolean, default=False)          # Namespace systeme
    is_editable = Column(Boolean, default=True)         # Peut etre modifie

    # Statistiques
    total_keys = Column(Integer, default=0)

    # Audit
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    parent = relationship("TranslationNamespace", remote_side=[id], backref="children")
    keys = relationship(
        "TranslationKey",
        back_populates="namespace",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_i18n_ns_tenant_code'),
        Index('idx_i18n_ns_tenant', 'tenant_id'),
        Index('idx_i18n_ns_tenant_module', 'tenant_id', 'module_code'),
    )


# ============================================================================
# CLE DE TRADUCTION
# ============================================================================

class TranslationKey(Base):
    """
    Cle de traduction.

    Represente un element a traduire (ex: "button.save", "error.required").
    """
    __tablename__ = "i18n_translation_keys"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Namespace
    namespace_id = Column(
        UniversalUUID(),
        ForeignKey("i18n_namespaces.id"),
        nullable=False,
        index=True
    )

    # Identification
    key = Column(String(255), nullable=False)           # button.save

    # Scope
    scope = Column(
        Enum(TranslationScope, name='i18n_translation_scope'),
        default=TranslationScope.TENANT
    )

    # Description/contexte pour les traducteurs
    description = Column(Text)
    context = Column(Text)                              # Contexte d'utilisation
    screenshot_url = Column(String(500))                # Capture d'ecran

    # Pluralisation
    supports_plural = Column(Boolean, default=False)
    plural_forms = Column(JSONB, default=list)          # ["zero", "one", "few", "many", "other"]

    # Variables/parametres
    parameters = Column(JSONB, default=list)            # ["count", "name"]

    # Contraintes
    max_length = Column(Integer)                        # Longueur max

    # Reference (entite source si contenu)
    entity_type = Column(String(50))                    # product, category
    entity_id = Column(UniversalUUID())
    entity_field = Column(String(50))                   # name, description

    # Tags pour filtrage
    tags = Column(JSONB, default=list)

    # Audit
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    namespace = relationship("TranslationNamespace", back_populates="keys")
    translations = relationship(
        "Translation",
        back_populates="translation_key",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    __table_args__ = (
        UniqueConstraint('tenant_id', 'namespace_id', 'key', name='uq_i18n_key_tenant_ns_key'),
        Index('idx_i18n_key_tenant', 'tenant_id'),
        Index('idx_i18n_key_tenant_ns', 'tenant_id', 'namespace_id'),
        Index('idx_i18n_key_tenant_scope', 'tenant_id', 'scope'),
        Index('idx_i18n_key_entity', 'tenant_id', 'entity_type', 'entity_id'),
        Index('idx_i18n_key_tags', 'tags', postgresql_using='gin'),
    )


# ============================================================================
# TRADUCTION
# ============================================================================

class Translation(Base):
    """
    Traduction d'une cle dans une langue.

    Contient la valeur traduite et les formes plurielles si applicable.
    """
    __tablename__ = "i18n_translations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # References
    translation_key_id = Column(
        UniversalUUID(),
        ForeignKey("i18n_translation_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    language_id = Column(
        UniversalUUID(),
        ForeignKey("i18n_languages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    language_code = Column(String(10), nullable=False)  # Denormalise pour perf

    # Valeur traduite
    value = Column(Text, nullable=False)

    # Pluriels (ICU format)
    plural_values = Column(JSONB, default=dict)
    # {"zero": "...", "one": "...", "few": "...", "many": "...", "other": "..."}

    # Statut
    status = Column(
        Enum(TranslationStatus, name='i18n_translation_status'),
        default=TranslationStatus.DRAFT
    )

    # Source
    is_machine_translated = Column(Boolean, default=False)
    machine_translation_provider = Column(String(50))   # google, deepl, azure
    machine_translation_confidence = Column(Numeric(5, 2))

    # Validation
    validated_by = Column(UniversalUUID())
    validated_at = Column(DateTime)

    # Commentaires
    translator_notes = Column(Text)
    reviewer_notes = Column(Text)

    # Audit
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    translation_key = relationship("TranslationKey", back_populates="translations")
    language = relationship("Language", back_populates="translations")

    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'translation_key_id', 'language_id',
            name='uq_i18n_trans_tenant_key_lang'
        ),
        Index('idx_i18n_trans_tenant', 'tenant_id'),
        Index('idx_i18n_trans_tenant_key', 'tenant_id', 'translation_key_id'),
        Index('idx_i18n_trans_tenant_lang', 'tenant_id', 'language_id'),
        Index('idx_i18n_trans_tenant_status', 'tenant_id', 'status'),
        Index('idx_i18n_trans_lang_code', 'tenant_id', 'language_code'),
    )

    def can_delete(self) -> tuple[bool, str]:
        """Verifie si la traduction peut etre supprimee."""
        return True, ""


# ============================================================================
# JOB DE TRADUCTION AUTOMATIQUE
# ============================================================================

class TranslationJob(Base):
    """
    Job de traduction automatique (batch).

    Pour traduction en masse via API externes.
    """
    __tablename__ = "i18n_translation_jobs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Configuration
    source_language_id = Column(UniversalUUID(), ForeignKey("i18n_languages.id"))
    target_language_ids = Column(JSONB, default=list)

    # Filtres
    namespace_ids = Column(JSONB, default=list)
    scope = Column(Enum(TranslationScope, name='i18n_job_scope'))

    # Provider
    provider = Column(String(50), nullable=False)       # google, deepl, azure, openai
    model = Column(String(50))                          # gpt-4, etc.

    # Progression
    status = Column(
        Enum(TranslationJobStatus, name='i18n_job_status'),
        default=TranslationJobStatus.PENDING
    )
    total_keys = Column(Integer, default=0)
    processed_keys = Column(Integer, default=0)
    failed_keys = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Erreurs
    error_message = Column(Text)
    error_details = Column(JSONB)

    # Audit
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_i18n_job_tenant', 'tenant_id'),
        Index('idx_i18n_job_tenant_status', 'tenant_id', 'status'),
    )

    @property
    def progress_percent(self) -> float:
        """Pourcentage de progression."""
        if self.total_keys == 0:
            return 0.0
        return (self.processed_keys / self.total_keys) * 100


# ============================================================================
# IMPORT/EXPORT
# ============================================================================

class TranslationImportExport(Base):
    """
    Historique des imports/exports de traductions.
    """
    __tablename__ = "i18n_import_exports"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type
    operation = Column(String(10), nullable=False)      # import, export

    # Format
    format = Column(
        Enum(ImportExportFormat, name='i18n_import_export_format'),
        nullable=False
    )

    # Fichier
    file_name = Column(String(255))
    file_url = Column(String(500))
    file_size = Column(Integer)

    # Filtres
    language_codes = Column(JSONB, default=list)
    namespace_codes = Column(JSONB, default=list)

    # Resultats
    status = Column(String(20), default="pending")
    total_keys = Column(Integer, default=0)
    processed_keys = Column(Integer, default=0)
    new_keys = Column(Integer, default=0)
    updated_keys = Column(Integer, default=0)
    skipped_keys = Column(Integer, default=0)
    error_keys = Column(Integer, default=0)

    # Erreurs
    errors = Column(JSONB, default=list)

    # Audit
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    __table_args__ = (
        Index('idx_i18n_ie_tenant', 'tenant_id'),
        Index('idx_i18n_ie_tenant_op', 'tenant_id', 'operation'),
    )


# ============================================================================
# CACHE DE TRADUCTION
# ============================================================================

class TranslationCache(Base):
    """
    Cache des traductions pour acces rapide.

    Aggregation des traductions par namespace et langue.
    """
    __tablename__ = "i18n_cache"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Cle de cache
    namespace_code = Column(String(50), nullable=False)
    language_code = Column(String(10), nullable=False)

    # Donnees en cache (JSON complet)
    translations = Column(JSONB, nullable=False, default=dict)
    # {"key1": "value1", "key2": {"zero": "...", "one": "...", "other": "..."}}

    # Validite
    generated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)

    # Stats
    key_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'namespace_code', 'language_code',
            name='uq_i18n_cache_tenant_ns_lang'
        ),
        Index('idx_i18n_cache_tenant', 'tenant_id'),
        Index('idx_i18n_cache_valid', 'tenant_id', 'is_valid'),
    )


# ============================================================================
# GLOSSAIRE
# ============================================================================

class Glossary(Base):
    """
    Glossaire de termes a ne pas traduire ou a traduire de maniere coherente.

    Ex: noms de marque, termes techniques specifiques.
    """
    __tablename__ = "i18n_glossary"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Terme source
    source_term = Column(String(255), nullable=False)
    source_language_code = Column(String(10), nullable=False)

    # Traductions
    translations = Column(JSONB, default=dict)
    # {"fr": "...", "en": "...", "de": "..."}

    # Type
    term_type = Column(String(50))                      # brand, technical, acronym
    do_not_translate = Column(Boolean, default=False)

    # Description
    definition = Column(Text)
    usage_notes = Column(Text)

    # Tags
    tags = Column(JSONB, default=list)

    # Audit
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime)
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(UniversalUUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'source_term', 'source_language_code',
            name='uq_i18n_glossary_tenant_term_lang'
        ),
        Index('idx_i18n_glossary_tenant', 'tenant_id'),
    )
