"""
AZALS MODULE T5 - Tests Packs Pays
===================================

Tests unitaires pour le module Packs Pays.
"""

import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch
import json

from app.modules.country_packs.models import (
    CountryPack, TaxRate, DocumentTemplate, BankConfig,
    PublicHoliday, LegalRequirement, TenantCountrySettings,
    TaxType, DocumentType, BankFormat, PackStatus,
    DateFormatStyle, NumberFormatStyle
)
from app.modules.country_packs.service import CountryPackService, get_country_pack_service
from app.modules.country_packs.schemas import (
    CountryPackCreate, CountryPackUpdate, CountryPackResponse,
    TaxRateCreate, TaxRateResponse,
    DocumentTemplateCreate, DocumentTemplateResponse,
    BankConfigCreate, BankConfigResponse,
    PublicHolidayCreate, PublicHolidayResponse,
    LegalRequirementCreate, LegalRequirementResponse,
    TaxTypeEnum, DocumentTypeEnum, BankFormatEnum, PackStatusEnum,
    DateFormatStyleEnum, NumberFormatStyleEnum
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session SQLAlchemy."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def service(mock_db):
    """Instance du service Country Packs."""
    return CountryPackService(mock_db, "test-tenant")


@pytest.fixture
def sample_pack():
    """Pack pays exemple."""
    return CountryPack(
        id=1,
        tenant_id="test-tenant",
        country_code="FR",
        country_name="France",
        default_currency="EUR",
        currency_symbol="€",
        default_language="fr",
        date_format=DateFormatStyle.DMY,
        number_format=NumberFormatStyle.EU,
        timezone="Europe/Paris",
        default_vat_rate=20.0,
        company_id_label="SIRET",
        vat_id_label="TVA",
        is_default=True,
        status=PackStatus.ACTIVE,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_tax_rate():
    """Taux de taxe exemple."""
    return TaxRate(
        id=1,
        tenant_id="test-tenant",
        country_pack_id=1,
        tax_type=TaxType.VAT,
        code="TVA_20",
        name="TVA 20%",
        rate=20.0,
        is_percentage=True,
        applies_to="both",
        account_collected="44571",
        is_active=True,
        is_default=True,
        valid_from=date.today()
    )


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des enums."""

    def test_tax_type_values(self):
        """Vérifie les valeurs de TaxType."""
        assert TaxType.VAT.value == "VAT"
        assert TaxType.CORPORATE_TAX.value == "CORPORATE_TAX"
        assert len(TaxType) == 8

    def test_document_type_values(self):
        """Vérifie les valeurs de DocumentType."""
        assert DocumentType.INVOICE.value == "INVOICE"
        assert DocumentType.PAYSLIP.value == "PAYSLIP"
        assert len(DocumentType) == 10

    def test_bank_format_values(self):
        """Vérifie les valeurs de BankFormat."""
        assert BankFormat.SEPA.value == "SEPA"
        assert BankFormat.SWIFT.value == "SWIFT"
        assert len(BankFormat) == 7

    def test_date_format_style_values(self):
        """Vérifie les valeurs de DateFormatStyle."""
        assert DateFormatStyle.DMY.value == "DMY"
        assert DateFormatStyle.YMD.value == "YMD"
        assert len(DateFormatStyle) == 6

    def test_number_format_style_values(self):
        """Vérifie les valeurs de NumberFormatStyle."""
        assert NumberFormatStyle.EU.value == "EU"
        assert NumberFormatStyle.US.value == "US"
        assert NumberFormatStyle.CH.value == "CH"
        assert len(NumberFormatStyle) == 3

    def test_pack_status_values(self):
        """Vérifie les valeurs de PackStatus."""
        assert PackStatus.DRAFT.value == "DRAFT"
        assert PackStatus.ACTIVE.value == "ACTIVE"
        assert PackStatus.DEPRECATED.value == "DEPRECATED"
        assert len(PackStatus) == 3


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_country_pack_creation(self, sample_pack):
        """Test création d'un pack pays."""
        assert sample_pack.id == 1
        assert sample_pack.country_code == "FR"
        assert sample_pack.default_currency == "EUR"
        assert sample_pack.default_vat_rate == 20.0
        assert sample_pack.is_default == True

    def test_tax_rate_creation(self, sample_tax_rate):
        """Test création d'un taux de taxe."""
        assert sample_tax_rate.tax_type == TaxType.VAT
        assert sample_tax_rate.rate == 20.0
        assert sample_tax_rate.code == "TVA_20"

    def test_document_template_creation(self):
        """Test création d'un template de document."""
        template = DocumentTemplate(
            id=1,
            tenant_id="test-tenant",
            country_pack_id=1,
            document_type=DocumentType.INVOICE,
            code="INVOICE_FR",
            name="Facture France",
            template_format="html",
            is_default=True
        )
        assert template.document_type == DocumentType.INVOICE
        assert template.code == "INVOICE_FR"

    def test_bank_config_creation(self):
        """Test création d'une config bancaire."""
        config = BankConfig(
            id=1,
            tenant_id="test-tenant",
            country_pack_id=1,
            bank_format=BankFormat.SEPA,
            code="SEPA_FR",
            name="Virement SEPA France",
            iban_prefix="FR",
            iban_length=27
        )
        assert config.bank_format == BankFormat.SEPA
        assert config.iban_prefix == "FR"

    def test_public_holiday_creation(self):
        """Test création d'un jour férié."""
        holiday = PublicHoliday(
            id=1,
            tenant_id="test-tenant",
            country_pack_id=1,
            name="New Year",
            name_local="Jour de l'An",
            month=1,
            day=1,
            is_fixed=True,
            is_national=True
        )
        assert holiday.month == 1
        assert holiday.day == 1
        assert holiday.is_national == True

    def test_legal_requirement_creation(self):
        """Test création d'une exigence légale."""
        req = LegalRequirement(
            id=1,
            tenant_id="test-tenant",
            country_pack_id=1,
            category="fiscal",
            code="TVA_DECL",
            name="Déclaration TVA",
            frequency="monthly",
            is_mandatory=True
        )
        assert req.category == "fiscal"
        assert req.frequency == "monthly"


# ============================================================================
# TESTS SCHÉMAS
# ============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_country_pack_create_schema(self):
        """Test schéma création pack."""
        data = CountryPackCreate(
            country_code="MA",
            country_name="Morocco",
            default_currency="MAD",
            default_language="fr",
            default_vat_rate=20.0
        )
        assert data.country_code == "MA"
        assert data.default_currency == "MAD"

    def test_country_pack_update_schema(self):
        """Test schéma mise à jour pack."""
        data = CountryPackUpdate(
            country_name="Maroc",
            default_vat_rate=18.0
        )
        assert data.country_name == "Maroc"
        assert data.default_vat_rate == 18.0

    def test_tax_rate_create_schema(self):
        """Test schéma création taxe."""
        data = TaxRateCreate(
            country_pack_id=1,
            tax_type=TaxTypeEnum.VAT,
            code="TVA_10",
            name="TVA 10%",
            rate=10.0
        )
        assert data.rate == 10.0
        assert data.tax_type == TaxTypeEnum.VAT

    def test_document_template_create_schema(self):
        """Test schéma création template."""
        data = DocumentTemplateCreate(
            country_pack_id=1,
            document_type=DocumentTypeEnum.INVOICE,
            code="INV_FR",
            name="Facture France"
        )
        assert data.document_type == DocumentTypeEnum.INVOICE

    def test_bank_config_create_schema(self):
        """Test schéma création config bancaire."""
        data = BankConfigCreate(
            country_pack_id=1,
            bank_format=BankFormatEnum.SEPA,
            code="SEPA_FR",
            name="SEPA France"
        )
        assert data.bank_format == BankFormatEnum.SEPA

    def test_public_holiday_create_schema(self):
        """Test schéma création jour férié."""
        data = PublicHolidayCreate(
            country_pack_id=1,
            name="Fête Nationale",
            month=7,
            day=14
        )
        assert data.month == 7
        assert data.day == 14


# ============================================================================
# TESTS SERVICE - PACKS PAYS
# ============================================================================

class TestServicePacks:
    """Tests du service - gestion des packs."""

    def test_create_country_pack(self, service, mock_db):
        """Test création d'un pack."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        pack = service.create_country_pack(
            country_code="MA",
            country_name="Morocco",
            default_currency="MAD"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_country_pack_not_found(self, service, mock_db):
        """Test récupération pack inexistant."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        pack = service.get_country_pack(999)
        assert pack is None

    def test_get_country_pack_by_code(self, service, mock_db, sample_pack):
        """Test récupération pack par code."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack

        pack = service.get_country_pack_by_code("FR")
        assert pack.country_name == "France"

    def test_get_default_pack(self, service, mock_db, sample_pack):
        """Test récupération pack par défaut."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack

        pack = service.get_default_pack()
        assert pack.is_default == True

    def test_list_country_packs(self, service, mock_db, sample_pack):
        """Test liste des packs."""
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_pack]

        packs, total = service.list_country_packs()
        assert total == 1


# ============================================================================
# TESTS SERVICE - TAXES
# ============================================================================

class TestServiceTaxes:
    """Tests du service - taxes."""

    def test_create_tax_rate(self, service, mock_db):
        """Test création taux de taxe."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        tax = service.create_tax_rate(
            country_pack_id=1,
            tax_type=TaxType.VAT,
            code="TVA_10",
            name="TVA 10%",
            rate=10.0
        )

        mock_db.add.assert_called_once()

    def test_get_vat_rates(self, service, mock_db, sample_pack, sample_tax_rate):
        """Test récupération taux TVA."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_tax_rate]

        rates = service.get_vat_rates("FR")
        # Vérifie que la méthode s'exécute sans erreur


# ============================================================================
# TESTS SERVICE - UTILITAIRES
# ============================================================================

class TestServiceUtils:
    """Tests du service - utilitaires."""

    def test_format_currency_eu(self, service, mock_db, sample_pack):
        """Test formatage devise EU."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack

        formatted = service.format_currency(1234.56, "FR")
        assert "€" in formatted
        assert "1 234,56" in formatted or "1234,56" in formatted

    def test_format_date_dmy(self, service, mock_db, sample_pack):
        """Test formatage date DMY."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack

        formatted = service.format_date(date(2024, 12, 31), "FR")
        assert formatted == "31/12/2024"

    def test_validate_iban(self, service, mock_db, sample_pack):
        """Test validation IBAN."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack

        # Créer une config bancaire mock
        bank_config = BankConfig(
            id=1,
            tenant_id="test-tenant",
            country_pack_id=1,
            bank_format=BankFormat.SEPA,
            code="SEPA_FR",
            name="SEPA",
            iban_prefix="FR",
            iban_length=27,
            is_default=True
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_pack, bank_config]

        result = service.validate_iban("FR7630001007941234567890185", "FR")
        # Le résultat dépend de la logique de validation


# ============================================================================
# TESTS SERVICE - JOURS FÉRIÉS
# ============================================================================

class TestServiceHolidays:
    """Tests du service - jours fériés."""

    def test_create_holiday(self, service, mock_db):
        """Test création jour férié."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        holiday = service.create_holiday(
            country_pack_id=1,
            name="New Year",
            month=1,
            day=1
        )

        mock_db.add.assert_called_once()

    def test_get_holidays_for_year(self, service, mock_db, sample_pack):
        """Test récupération jours fériés par année."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        holidays = service.get_holidays_for_year("FR", 2024)
        assert isinstance(holidays, list)

    def test_is_holiday(self, service, mock_db, sample_pack):
        """Test vérification jour férié."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack

        result = service.is_holiday(date(2024, 1, 1), "FR")
        assert isinstance(result, bool)


# ============================================================================
# TESTS SERVICE - PARAMÈTRES TENANT
# ============================================================================

class TestServiceTenantSettings:
    """Tests du service - paramètres tenant."""

    def test_activate_country_for_tenant(self, service, mock_db):
        """Test activation pays pour tenant."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        settings = service.activate_country_for_tenant(
            country_pack_id=1,
            is_primary=True
        )

        mock_db.add.assert_called()

    def test_get_tenant_countries(self, service, mock_db):
        """Test récupération pays du tenant."""
        # Configurer mock pour chaînes de filtres
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        countries = service.get_tenant_countries()
        assert isinstance(countries, list)

    def test_get_primary_country(self, service, mock_db, sample_pack):
        """Test récupération pays principal."""
        # Mock des settings avec country_pack_id
        mock_settings = MagicMock()
        mock_settings.country_pack_id = sample_pack.id

        # Premier appel retourne settings, deuxième retourne le pack
        mock_query = MagicMock()
        mock_query.filter.return_value.first.side_effect = [mock_settings, sample_pack]
        mock_db.query.return_value = mock_query

        pack = service.get_primary_country()
        # Vérifie que la méthode retourne un résultat


# ============================================================================
# TESTS FACTORY
# ============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_country_pack_service(self, mock_db):
        """Test factory get_country_pack_service."""
        service = get_country_pack_service(mock_db, "my-tenant")

        assert isinstance(service, CountryPackService)
        assert service.tenant_id == "my-tenant"


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration."""

    def test_full_pack_setup(self, service, mock_db):
        """Test configuration complète d'un pack."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 1. Créer le pack
        pack = service.create_country_pack(
            country_code="SN",
            country_name="Senegal",
            default_currency="XOF",
            default_vat_rate=18.0
        )

        # 2. Ajouter des taxes
        # Simulé dans le mock

        # 3. Ajouter des jours fériés
        # Simulé dans le mock

        mock_db.add.assert_called()

    def test_country_summary(self, service, mock_db, sample_pack):
        """Test résumé pays."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_pack
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        summary = service.get_country_summary("FR")
        assert "country_code" in summary
        assert "currency" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
