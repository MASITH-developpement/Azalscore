"""Configuration pytest et fixtures pour les tests Country Packs."""

import pytest
from datetime import datetime, timedelta, date

from app.core.saas_context import SaaSContext, UserRole
from app.modules.country_packs.models import TaxType, DocumentType, BankFormat


@pytest.fixture
def tenant_id():
    return "tenant-test-001"


@pytest.fixture
def user_id():
    return "user-test-001"


@pytest.fixture(autouse=True)
def mock_saas_context(monkeypatch, tenant_id, user_id):
    def mock_get_context():
        return SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole.ADMIN,
            permissions={"country_packs.*"},
            scope="tenant",
            session_id="session-test",
            ip_address="127.0.0.1",
            user_agent="pytest",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    from app.modules.country_packs import router_v2
    monkeypatch.setattr(router_v2, "get_saas_context", mock_get_context)
    return mock_get_context


@pytest.fixture
def mock_country_pack_service(monkeypatch, tenant_id, user_id):
    """Mock du service Country Packs."""

    class MockCountryPackService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = user_id

        # Country Packs
        def list_country_packs(self, status=None, skip=0, limit=50):
            packs = [
                {"id": 1, "country_code": "FR", "country_name": "France"},
                {"id": 2, "country_code": "US", "country_name": "United States"}
            ]
            return packs, len(packs)

        def get_country_pack(self, pack_id):
            return {
                "id": pack_id,
                "country_code": "FR",
                "country_name": "France",
                "default_currency": "EUR"
            }

        def get_country_pack_by_code(self, country_code):
            if country_code.upper() == "FR":
                return {
                    "id": 1,
                    "country_code": "FR",
                    "country_name": "France",
                    "default_currency": "EUR"
                }
            return None

        def get_default_pack(self):
            return {
                "id": 1,
                "country_code": "FR",
                "country_name": "France",
                "is_default": True
            }

        def get_country_summary(self, country_code):
            return {
                "country_code": country_code,
                "country_name": "France",
                "currency": "EUR",
                "vat_rates_count": 3,
                "templates_count": 5
            }

        # Tax Rates
        def get_tax_rates(self, country_pack_id=None, tax_type=None, is_active=True):
            return [
                {"id": 1, "code": "VAT20", "rate": 20.0, "tax_type": "vat"},
                {"id": 2, "code": "VAT10", "rate": 10.0, "tax_type": "vat"}
            ]

        def get_vat_rates(self, country_code):
            return [
                {"id": 1, "code": "VAT20", "rate": 20.0},
                {"id": 2, "code": "VAT10", "rate": 10.0},
                {"id": 3, "code": "VAT5.5", "rate": 5.5}
            ]

        def get_default_vat_rate(self, country_code):
            if country_code.upper() != "FR":
                return None
            return {"id": 1, "code": "VAT20", "rate": 20.0, "is_default": True}

        # Document Templates
        def get_document_templates(self, country_pack_id=None, document_type=None, is_active=True):
            return [
                {"id": 1, "code": "INV_FR", "document_type": "invoice"},
                {"id": 2, "code": "QUOTE_FR", "document_type": "quote"}
            ]

        def get_default_template(self, country_code, document_type):
            if country_code.upper() != "FR":
                return None
            return {
                "id": 1,
                "code": "INV_FR",
                "document_type": document_type,
                "is_default": True
            }

        # Bank Configs
        def get_bank_configs(self, country_pack_id=None, bank_format=None):
            return [
                {"id": 1, "code": "SEPA", "bank_format": "sepa"},
                {"id": 2, "code": "SWIFT", "bank_format": "swift"}
            ]

        def validate_iban(self, iban, country_code):
            if iban.upper().startswith("FR"):
                return {"valid": True, "formatted_iban": iban.replace(" ", "").upper()}
            return {"valid": False, "error": "Invalid IBAN"}

        # Holidays
        def get_holidays(self, country_pack_id=None, year=None, region=None):
            return [
                {"id": 1, "name": "New Year", "month": 1, "day": 1},
                {"id": 2, "name": "Christmas", "month": 12, "day": 25}
            ]

        def get_holidays_for_year(self, country_code, year):
            return [
                {"id": 1, "name": "New Year", "date": f"{year}-01-01"},
                {"id": 2, "name": "Christmas", "date": f"{year}-12-25"}
            ]

        def is_holiday(self, check_date, country_code):
            # New Year and Christmas
            return check_date.month == 1 and check_date.day == 1 or \
                   check_date.month == 12 and check_date.day == 25

        # Legal Requirements
        def get_legal_requirements(self, country_pack_id=None, category=None):
            return [
                {"id": 1, "category": "tax", "code": "VAT_FILING"},
                {"id": 2, "category": "compliance", "code": "AML_CHECK"}
            ]

        # Tenant Settings
        def get_tenant_countries(self, active_only=True):
            return [
                {"country_pack_id": 1, "is_primary": True, "is_active": True},
                {"country_pack_id": 2, "is_primary": False, "is_active": True}
            ]

        def get_primary_country(self):
            return {
                "id": 1,
                "country_code": "FR",
                "country_name": "France",
                "is_default": True
            }

        def activate_country_for_tenant(self, country_pack_id, is_primary=False, custom_config=None, activated_by=None):
            return {
                "id": 1,
                "country_pack_id": country_pack_id,
                "is_primary": is_primary,
                "is_active": True
            }

        # Utilities
        def format_currency(self, amount, country_code):
            return f"{amount:,.2f}".replace(",", " ").replace(".", ",") + " €"

        def format_date(self, d, country_code):
            return d.strftime("%d/%m/%Y")

    from app.modules.country_packs import router_v2

    def mock_get_service(db, tenant_id, user_id):
        return MockCountryPackService(db, tenant_id, user_id)

    monkeypatch.setattr(router_v2, "get_country_pack_service", mock_get_service)
    return MockCountryPackService(None, tenant_id, user_id)
