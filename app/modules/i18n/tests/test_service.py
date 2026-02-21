"""
AZALSCORE Module I18N - Tests Service
======================================

Tests unitaires pour le service I18N.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.modules.i18n.models import (
    Language, LanguageStatus,
    TranslationNamespace,
    TranslationKey, TranslationScope,
    Translation, TranslationStatus,
    DateFormatType, NumberFormatType,
)
from app.modules.i18n.schemas import (
    LanguageCreate, LanguageUpdate,
    NamespaceCreate,
    TranslationKeyCreate,
    TranslationBulkUpdate,
    InlineTranslationRequest,
    ExportRequest, ImportRequest,
    ImportExportFormat,
)
from app.modules.i18n.service import I18NService
from app.modules.i18n.exceptions import (
    LanguageNotFoundError,
    LanguageDuplicateError,
    LanguageDeleteError,
    NamespaceNotFoundError,
    TranslationKeyNotFoundError,
    TranslationKeyDuplicateError,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session SQLAlchemy."""
    db = MagicMock()
    db.query.return_value = MagicMock()
    return db


@pytest.fixture
def tenant_id():
    """ID tenant de test."""
    return "test-tenant-001"


@pytest.fixture
def service(mock_db, tenant_id):
    """Instance du service I18N."""
    return I18NService(mock_db, tenant_id)


@pytest.fixture
def sample_language():
    """Langue de test."""
    return Language(
        id=uuid4(),
        tenant_id="test-tenant-001",
        code="fr",
        name="French",
        native_name="Francais",
        locale="fr_FR",
        rtl=False,
        date_format=DateFormatType.DMY,
        date_separator="/",
        number_format=NumberFormatType.SPACE_COMMA,
        decimal_separator=",",
        thousands_separator=" ",
        currency_code="EUR",
        currency_symbol="EUR",
        currency_position="after",
        status=LanguageStatus.ACTIVE,
        is_default=True,
        is_active=True,
        version=1
    )


@pytest.fixture
def sample_namespace():
    """Namespace de test."""
    return TranslationNamespace(
        id=uuid4(),
        tenant_id="test-tenant-001",
        code="common",
        name="Common translations",
        is_system=False,
        is_editable=True,
        is_active=True
    )


@pytest.fixture
def sample_key(sample_namespace):
    """Cle de traduction de test."""
    return TranslationKey(
        id=uuid4(),
        tenant_id="test-tenant-001",
        namespace_id=sample_namespace.id,
        key="button.save",
        scope=TranslationScope.TENANT,
        supports_plural=False,
        is_active=True,
        version=1
    )


# ============================================================================
# TESTS FORMATAGE
# ============================================================================

class TestFormatting:
    """Tests de formatage des dates et nombres."""

    def test_format_date_dmy(self, service, sample_language):
        """Test formatage date DMY."""
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        dt = date(2026, 12, 31)
        result = service.format_date(dt, "fr")

        assert result == "31/12/2026"

    def test_format_date_mdy(self, service, sample_language):
        """Test formatage date MDY."""
        sample_language.date_format = DateFormatType.MDY
        sample_language.date_separator = "/"
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        dt = date(2026, 12, 31)
        result = service.format_date(dt, "en", DateFormatType.MDY)

        assert result == "12/31/2026"

    def test_format_date_ymd(self, service, sample_language):
        """Test formatage date YMD."""
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        dt = date(2026, 12, 31)
        result = service.format_date(dt, "fr", DateFormatType.YMD)

        assert result == "2026-12-31"

    def test_format_date_long(self, service, sample_language):
        """Test formatage date long."""
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        dt = date(2026, 12, 31)
        result = service.format_date(dt, "fr", DateFormatType.LONG)

        assert "31" in result
        assert "2026" in result

    def test_format_number_french(self, service, sample_language):
        """Test formatage nombre francais."""
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        result = service.format_number(Decimal("1234567.89"), "fr", 2)

        assert "1 234 567" in result
        assert ",89" in result

    def test_format_number_no_decimals(self, service, sample_language):
        """Test formatage nombre sans decimales."""
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        result = service.format_number(Decimal("1234.56"), "fr", 0)

        assert result == "1 235"  # Arrondi

    def test_format_currency_after(self, service, sample_language):
        """Test formatage devise apres le montant."""
        sample_language.currency_position = "after"
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        result = service.format_currency(Decimal("1234.56"), "EUR", "fr")

        assert result.endswith("EUR")
        assert "1 234,56" in result

    def test_format_currency_before(self, service, sample_language):
        """Test formatage devise avant le montant."""
        sample_language.currency_position = "before"
        sample_language.decimal_separator = "."
        sample_language.thousands_separator = ","
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        result = service.format_currency(Decimal("1234.56"), "$", "en")

        assert result.startswith("$")

    def test_format_percent(self, service, sample_language):
        """Test formatage pourcentage."""
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)

        result = service.format_percent(Decimal("75.5"), "fr")

        assert "75,50" in result
        assert "%" in result


# ============================================================================
# TESTS TRADUCTION
# ============================================================================

class TestTranslation:
    """Tests de traduction."""

    def test_t_simple(self, service):
        """Test traduction simple."""
        service.translation_repo.get_value = MagicMock(return_value="Enregistrer")

        result = service.t("save", "fr", "common")

        assert result == "Enregistrer"

    def test_t_with_params(self, service):
        """Test traduction avec parametres."""
        service.translation_repo.get_value = MagicMock(return_value="Bonjour {name}")

        result = service.t("greeting", "fr", "common", name="Jean")

        assert result == "Bonjour Jean"

    def test_t_fallback_to_key(self, service):
        """Test fallback sur la cle si pas de traduction."""
        service.translation_repo.get_value = MagicMock(return_value=None)

        result = service.t("unknown.key", "fr", "common")

        assert result == "unknown.key"

    def test_tp_zero(self, service):
        """Test pluriel zero."""
        # Le service fallback sur t() si pas de pluriel configure
        service.key_repo.get_by_full_key = MagicMock(return_value=None)
        service.translation_repo.get_value = MagicMock(return_value="{count} elements")

        result = service.tp("item", 0, "fr", "common")

        assert "0" in result

    def test_tp_one(self, service):
        """Test pluriel un."""
        service.key_repo.get_by_full_key = MagicMock(return_value=None)
        service.translation_repo.get_value = MagicMock(return_value="{count} element")

        result = service.tp("item", 1, "fr", "common")

        assert "1" in result

    def test_get_plural_form_french(self, service):
        """Test determination forme plurielle francais."""
        assert service._get_plural_form(0, "fr") == "zero"
        assert service._get_plural_form(1, "fr") == "one"
        assert service._get_plural_form(2, "fr") == "other"


# ============================================================================
# TESTS LANGUES
# ============================================================================

class TestLanguageManagement:
    """Tests gestion des langues."""

    def test_create_language(self, service, sample_language):
        """Test creation langue."""
        service.language_repo.code_exists = MagicMock(return_value=False)
        service.language_repo.create = MagicMock(return_value=sample_language)
        service.cache_repo.invalidate_all = MagicMock()

        data = LanguageCreate(
            code="fr",
            name="French",
            native_name="Francais"
        )
        result = service.create_language(data, uuid4())

        assert result.code == "fr"
        service.language_repo.create.assert_called_once()

    def test_create_language_duplicate(self, service):
        """Test creation langue dupliquee."""
        service.language_repo.code_exists = MagicMock(return_value=True)

        data = LanguageCreate(
            code="fr",
            name="French",
            native_name="Francais"
        )

        with pytest.raises(LanguageDuplicateError):
            service.create_language(data, uuid4())

    def test_delete_default_language(self, service, sample_language):
        """Test suppression langue par defaut interdite."""
        sample_language.is_default = True
        service.language_repo.get_by_id = MagicMock(return_value=sample_language)

        with pytest.raises(LanguageDeleteError):
            service.delete_language(sample_language.id, uuid4())

    def test_set_default_language(self, service, sample_language):
        """Test definition langue par defaut."""
        service.language_repo.set_default = MagicMock(return_value=sample_language)

        result = service.set_default_language(sample_language.id, uuid4())

        assert result.code == "fr"
        service.language_repo.set_default.assert_called_once()


# ============================================================================
# TESTS NAMESPACE
# ============================================================================

class TestNamespaceManagement:
    """Tests gestion des namespaces."""

    def test_create_namespace(self, service, sample_namespace):
        """Test creation namespace."""
        service.namespace_repo.code_exists = MagicMock(return_value=False)
        service.namespace_repo.create = MagicMock(return_value=sample_namespace)

        data = NamespaceCreate(
            code="common",
            name="Common translations"
        )
        result = service.create_namespace(data, uuid4())

        assert result.code == "common"

    def test_create_namespace_duplicate(self, service):
        """Test creation namespace duplique."""
        service.namespace_repo.code_exists = MagicMock(return_value=True)

        data = NamespaceCreate(
            code="common",
            name="Common"
        )

        with pytest.raises(NamespaceDuplicateError):
            service.create_namespace(data, uuid4())

    def test_ensure_namespace_exists(self, service, sample_namespace):
        """Test ensure_namespace quand existe."""
        service.namespace_repo.get_by_code = MagicMock(return_value=sample_namespace)

        result = service.ensure_namespace("common")

        assert result.code == "common"
        service.namespace_repo.create.assert_not_called()

    def test_ensure_namespace_creates(self, service, sample_namespace):
        """Test ensure_namespace quand n'existe pas."""
        service.namespace_repo.get_by_code = MagicMock(return_value=None)
        service.namespace_repo.create = MagicMock(return_value=sample_namespace)

        result = service.ensure_namespace("common", "Common")

        service.namespace_repo.create.assert_called_once()


# ============================================================================
# TESTS CLES
# ============================================================================

class TestTranslationKeyManagement:
    """Tests gestion des cles de traduction."""

    def test_create_key(self, service, sample_key, sample_namespace):
        """Test creation cle."""
        service.key_repo.key_exists = MagicMock(return_value=False)
        service.key_repo.create = MagicMock(return_value=sample_key)
        service.namespace_repo.get_by_id = MagicMock(return_value=sample_namespace)
        service.cache_repo.invalidate = MagicMock()

        data = TranslationKeyCreate(
            key="button.save",
            namespace_id=sample_namespace.id
        )
        result = service.create_translation_key(data, uuid4())

        assert result.key == "button.save"

    def test_create_key_duplicate(self, service, sample_namespace):
        """Test creation cle dupliquee."""
        service.key_repo.key_exists = MagicMock(return_value=True)
        service.namespace_repo.get_by_id = MagicMock(return_value=sample_namespace)

        data = TranslationKeyCreate(
            key="button.save",
            namespace_id=sample_namespace.id
        )

        with pytest.raises(TranslationKeyDuplicateError):
            service.create_translation_key(data, uuid4())


# ============================================================================
# TESTS BUNDLES
# ============================================================================

class TestBundles:
    """Tests bundles de traductions."""

    def test_get_bundle(self, service, sample_namespace, sample_language):
        """Test recuperation bundle."""
        service.cache_repo.get = MagicMock(return_value=None)
        service.translation_repo.get_bundle = MagicMock(return_value={
            "save": "Enregistrer",
            "cancel": "Annuler"
        })
        service.cache_repo.set = MagicMock()

        result = service.get_bundle("fr", "common")

        assert result.language == "fr"
        assert result.namespace == "common"
        assert result.key_count == 2
        assert "save" in result.translations

    def test_get_bundle_from_cache(self, service):
        """Test bundle depuis cache."""
        from app.modules.i18n.models import TranslationCache

        cached = MagicMock()
        cached.translations = {"save": "Enregistrer"}
        cached.is_valid = True
        cached.generated_at = datetime.utcnow()
        cached.key_count = 1

        service.cache_repo.get = MagicMock(return_value=cached)

        result = service.get_bundle("fr", "common")

        assert "save" in result.translations
        service.translation_repo.get_bundle.assert_not_called()


# ============================================================================
# TESTS IMPORT/EXPORT
# ============================================================================

class TestImportExport:
    """Tests import/export traductions."""

    def test_export_translations(self, service, sample_namespace, sample_key, sample_language):
        """Test export traductions."""
        trans = MagicMock()
        trans.value = "Enregistrer"
        trans.plural_values = {}

        service.namespace_repo.list_all = MagicMock(return_value=[sample_namespace])
        service.key_repo.list_by_namespace = MagicMock(return_value=[sample_key])
        sample_key.supports_plural = False
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)
        service.translation_repo.get_by_key_language = MagicMock(return_value=trans)

        request = ExportRequest(
            format=ImportExportFormat.JSON,
            language_codes=["fr"]
        )
        result = service.export_translations(request)

        assert "common" in result
        assert "button.save" in result["common"]

    def test_import_translations(self, service, sample_namespace, sample_key, sample_language):
        """Test import traductions."""
        service.ensure_namespace = MagicMock(return_value=sample_namespace)
        service.key_repo.get_by_key = MagicMock(return_value=sample_key)
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)
        service.translation_repo.get_by_key_language = MagicMock(return_value=None)
        service.translation_repo.create = MagicMock()
        service.invalidate_cache = MagicMock()
        service.language_repo.update_coverage = MagicMock()
        service.language_repo.list_active = MagicMock(return_value=[sample_language])

        data = {
            "common": {
                "button.save": {"fr": "Enregistrer"}
            }
        }
        request = ImportRequest(format=ImportExportFormat.JSON)

        created, updated, skipped, errors = service.import_translations(data, request)

        assert created == 1
        assert updated == 0
        assert len(errors) == 0


# ============================================================================
# TESTS PLURALISATION
# ============================================================================

class TestPluralization:
    """Tests regles de pluralisation."""

    def test_plural_form_english(self, service):
        """Test formes plurielles anglais."""
        assert service._get_plural_form(0, "en") == "zero"
        assert service._get_plural_form(1, "en") == "one"
        assert service._get_plural_form(2, "en") == "other"
        assert service._get_plural_form(100, "en") == "other"

    def test_plural_form_russian(self, service):
        """Test formes plurielles russe (regles complexes)."""
        assert service._get_plural_form(1, "ru") == "one"
        assert service._get_plural_form(2, "ru") == "few"
        assert service._get_plural_form(5, "ru") == "many"
        assert service._get_plural_form(21, "ru") == "one"
        assert service._get_plural_form(22, "ru") == "few"

    def test_plural_form_arabic(self, service):
        """Test formes plurielles arabe."""
        assert service._get_plural_form(0, "ar") == "zero"
        assert service._get_plural_form(1, "ar") == "one"
        assert service._get_plural_form(2, "ar") == "two"
        assert service._get_plural_form(5, "ar") == "few"
        assert service._get_plural_form(50, "ar") == "many"


# ============================================================================
# TESTS INLINE TRANSLATION
# ============================================================================

class TestInlineTranslation:
    """Tests traduction inline."""

    def test_inline_translate_create(
        self, service, sample_namespace, sample_key, sample_language
    ):
        """Test creation traduction inline."""
        service.ensure_namespace = MagicMock(return_value=sample_namespace)
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)
        service.key_repo.get_by_key = MagicMock(return_value=None)
        service.key_repo.create = MagicMock(return_value=sample_key)
        service.translation_repo.get_by_key_language = MagicMock(return_value=None)
        service.translation_repo.create = MagicMock()
        service.cache_repo.invalidate = MagicMock()

        request = InlineTranslationRequest(
            key="new.key",
            namespace="common",
            language="fr",
            value="Nouvelle valeur"
        )
        result = service.inline_translate(request)

        assert result.created == True
        assert result.updated == False
        assert result.value == "Nouvelle valeur"

    def test_inline_translate_update(
        self, service, sample_namespace, sample_key, sample_language
    ):
        """Test mise a jour traduction inline."""
        existing_trans = MagicMock()

        service.ensure_namespace = MagicMock(return_value=sample_namespace)
        service.language_repo.get_by_code = MagicMock(return_value=sample_language)
        service.key_repo.get_by_key = MagicMock(return_value=sample_key)
        service.translation_repo.get_by_key_language = MagicMock(return_value=existing_trans)
        service.translation_repo.update = MagicMock()

        request = InlineTranslationRequest(
            key="button.save",
            namespace="common",
            language="fr",
            value="Sauvegarder"
        )
        result = service.inline_translate(request)

        assert result.created == False
        assert result.updated == True
