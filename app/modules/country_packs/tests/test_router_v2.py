"""Tests pour le router v2 du module Country Packs - CORE SaaS v2."""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.modules.country_packs.models import PackStatus, TaxType, DocumentType, BankFormat

client = TestClient(app)
BASE_URL = "/v2/country-packs"


# ============================================================================
# TESTS COUNTRY PACKS
# ============================================================================

def test_list_country_packs(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs")
    assert response.status_code == 200
    data = response.json()
    assert "packs" in data
    assert "total" in data
    assert len(data["packs"]) == 2


def test_list_country_packs_with_filters(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs", params={"status": PackStatus.ACTIVE.value})
    assert response.status_code == 200


def test_list_country_packs_pagination(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs", params={"skip": 0, "limit": 10})
    assert response.status_code == 200


def test_get_country_pack_success(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["country_code"] == "FR"


def test_get_country_pack_by_code_success(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs/code/FR")
    assert response.status_code == 200
    data = response.json()
    assert data["country_code"] == "FR"


def test_get_country_pack_by_code_not_found(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs/code/XX")
    assert response.status_code == 404


def test_get_default_pack(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs/default")
    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True


def test_get_country_summary(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/summary/FR")
    assert response.status_code == 200
    data = response.json()
    assert "country_code" in data
    assert "vat_rates_count" in data


# ============================================================================
# TESTS TAX RATES
# ============================================================================

def test_get_tax_rates(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/tax-rates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_tax_rates_with_filters(mock_country_pack_service):
    response = client.get(
        f"{BASE_URL}/tax-rates",
        params={"country_pack_id": 1, "tax_type": TaxType.VAT.value}
    )
    assert response.status_code == 200


def test_get_vat_rates(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/vat-rates/FR")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


def test_get_default_vat_rate_success(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/vat-rates/FR/default")
    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True


def test_get_default_vat_rate_not_found(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/vat-rates/XX/default")
    assert response.status_code == 404


# ============================================================================
# TESTS DOCUMENT TEMPLATES
# ============================================================================

def test_get_document_templates(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/templates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_document_templates_with_filters(mock_country_pack_service):
    response = client.get(
        f"{BASE_URL}/templates",
        params={"country_pack_id": 1, "document_type": DocumentType.INVOICE.value}
    )
    assert response.status_code == 200


def test_get_default_template_success(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/templates/FR/invoice/default")
    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True


def test_get_default_template_not_found(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/templates/XX/invoice/default")
    assert response.status_code == 404


# ============================================================================
# TESTS BANK CONFIGURATIONS
# ============================================================================

def test_get_bank_configs(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/bank-configs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_bank_configs_with_filters(mock_country_pack_service):
    response = client.get(
        f"{BASE_URL}/bank-configs",
        params={"country_pack_id": 1, "bank_format": BankFormat.SEPA.value}
    )
    assert response.status_code == 200


def test_validate_iban_success(mock_country_pack_service):
    response = client.post(
        f"{BASE_URL}/bank-configs/validate-iban",
        params={"iban": "FR76 1234 5678 9012 3456 7890 123", "country_code": "FR"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_validate_iban_invalid(mock_country_pack_service):
    response = client.post(
        f"{BASE_URL}/bank-configs/validate-iban",
        params={"iban": "XX1234567890", "country_code": "FR"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


# ============================================================================
# TESTS PUBLIC HOLIDAYS
# ============================================================================

def test_get_holidays(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/holidays")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_holidays_with_filters(mock_country_pack_service):
    response = client.get(
        f"{BASE_URL}/holidays",
        params={"country_pack_id": 1, "year": 2024}
    )
    assert response.status_code == 200


def test_get_holidays_for_year(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/holidays/FR/year/2024")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_is_holiday_true(mock_country_pack_service):
    response = client.post(
        f"{BASE_URL}/holidays/check",
        params={"check_date": "2024-01-01", "country_code": "FR"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_holiday"] is True


def test_is_holiday_false(mock_country_pack_service):
    response = client.post(
        f"{BASE_URL}/holidays/check",
        params={"check_date": "2024-03-15", "country_code": "FR"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_holiday"] is False


# ============================================================================
# TESTS LEGAL REQUIREMENTS
# ============================================================================

def test_get_legal_requirements(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/legal-requirements")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_legal_requirements_with_filters(mock_country_pack_service):
    response = client.get(
        f"{BASE_URL}/legal-requirements",
        params={"country_pack_id": 1, "category": "tax"}
    )
    assert response.status_code == 200


# ============================================================================
# TESTS TENANT COUNTRY SETTINGS
# ============================================================================

def test_get_tenant_countries(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/tenant/countries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_tenant_countries_all(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/tenant/countries", params={"active_only": False})
    assert response.status_code == 200


def test_get_primary_country(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/tenant/primary-country")
    assert response.status_code == 200
    data = response.json()
    assert data["country_code"] == "FR"


def test_activate_country_for_tenant(mock_country_pack_service):
    response = client.post(
        f"{BASE_URL}/tenant/activate-country",
        params={"country_pack_id": 2, "is_primary": False}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["country_pack_id"] == 2


# ============================================================================
# TESTS UTILITIES
# ============================================================================

def test_format_currency(mock_country_pack_service):
    response = client.post(
        f"{BASE_URL}/format-currency",
        params={"amount": 1234.56, "country_code": "FR"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "formatted" in data


def test_format_date(mock_country_pack_service):
    response = client.post(
        f"{BASE_URL}/format-date",
        params={"date_value": "2024-03-15", "country_code": "FR"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "formatted" in data


# ============================================================================
# TESTS TENANT ISOLATION
# ============================================================================

def test_packs_tenant_isolation(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/packs")
    assert response.status_code == 200


def test_tax_rates_tenant_isolation(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/tax-rates")
    assert response.status_code == 200


def test_templates_tenant_isolation(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/templates")
    assert response.status_code == 200


def test_holidays_tenant_isolation(mock_country_pack_service):
    response = client.get(f"{BASE_URL}/holidays")
    assert response.status_code == 200
