"""
Fixtures pour les tests du module Consolidation.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, MagicMock


@pytest.fixture
def tenant_id():
    """Tenant ID pour les tests."""
    return "tenant-test-001"


@pytest.fixture
def user_id():
    """User ID pour les tests."""
    return str(uuid4())


@pytest.fixture
def mock_db():
    """Session de base de donnees mockee."""
    db = Mock()
    db.query = Mock(return_value=MagicMock())
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.flush = Mock()
    return db


@pytest.fixture
def test_client(mock_db, tenant_id, user_id):
    """Client de test avec contexte."""
    mock_context = Mock()
    mock_context.tenant_id = tenant_id
    mock_context.user_id = user_id
    return {"db": mock_db, "context": mock_context}


@pytest.fixture
def sample_perimeter():
    """Perimetre de consolidation exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "code": "GRP-2025",
        "name": "Groupe AZALS 2025",
        "description": "Perimetre de consolidation annuel 2025",
        "fiscal_year": 2025,
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 12, 31),
        "consolidation_currency": "EUR",
        "accounting_standard": "french_gaap",
        "status": "draft",
        "is_active": True,
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_entity():
    """Entite de groupe exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "perimeter_id": str(uuid4()),
        "code": "HOLDING",
        "name": "AZALS Holding SA",
        "legal_name": "AZALS Holding Societe Anonyme",
        "registration_number": "123456789",
        "country": "FR",
        "currency": "EUR",
        "is_parent": True,
        "consolidation_method": "full_integration",
        "control_type": "exclusive",
        "direct_ownership_pct": Decimal("100.000"),
        "indirect_ownership_pct": Decimal("0.000"),
        "total_ownership_pct": Decimal("100.000"),
        "voting_rights_pct": Decimal("100.000"),
        "integration_pct": Decimal("100.000"),
        "fiscal_year_end_month": 12,
        "is_active": True,
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_subsidiary():
    """Filiale exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "perimeter_id": str(uuid4()),
        "code": "SUB-FR-01",
        "name": "AZALS France SAS",
        "legal_name": "AZALS France Societe par Actions Simplifiee",
        "registration_number": "987654321",
        "country": "FR",
        "currency": "EUR",
        "is_parent": False,
        "consolidation_method": "full_integration",
        "control_type": "exclusive",
        "direct_ownership_pct": Decimal("80.000"),
        "indirect_ownership_pct": Decimal("0.000"),
        "total_ownership_pct": Decimal("80.000"),
        "voting_rights_pct": Decimal("80.000"),
        "integration_pct": Decimal("100.000"),
        "fiscal_year_end_month": 12,
        "is_active": True,
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_participation():
    """Participation exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "parent_id": str(uuid4()),
        "subsidiary_id": str(uuid4()),
        "direct_ownership": Decimal("80.000"),
        "indirect_ownership": Decimal("0.000"),
        "total_ownership": Decimal("80.000"),
        "voting_rights": Decimal("80.000"),
        "acquisition_date": date(2020, 1, 1),
        "acquisition_cost": Decimal("1000000.00"),
        "fair_value_at_acquisition": Decimal("1200000.00"),
        "goodwill_amount": Decimal("200000.00"),
        "goodwill_impairment": Decimal("0.00"),
        "goodwill_currency": "EUR",
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_consolidation():
    """Consolidation exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "perimeter_id": str(uuid4()),
        "code": "CONSO-2025-Q4",
        "name": "Consolidation Q4 2025",
        "description": "Consolidation trimestrielle T4 2025",
        "period_start": date(2025, 10, 1),
        "period_end": date(2025, 12, 31),
        "fiscal_year": 2025,
        "period_type": "quarterly",
        "consolidation_currency": "EUR",
        "accounting_standard": "french_gaap",
        "status": "draft",
        "total_assets": Decimal("10000000.00"),
        "total_liabilities": Decimal("4000000.00"),
        "total_equity": Decimal("6000000.00"),
        "group_equity": Decimal("5000000.00"),
        "minority_interests": Decimal("1000000.00"),
        "consolidated_revenue": Decimal("20000000.00"),
        "consolidated_net_income": Decimal("2000000.00"),
        "group_net_income": Decimal("1600000.00"),
        "minority_net_income": Decimal("400000.00"),
        "translation_difference": Decimal("50000.00"),
        "total_goodwill": Decimal("500000.00"),
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_package():
    """Paquet de consolidation exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "consolidation_id": str(uuid4()),
        "entity_id": str(uuid4()),
        "period_start": date(2025, 10, 1),
        "period_end": date(2025, 12, 31),
        "local_currency": "EUR",
        "reporting_currency": "EUR",
        "closing_rate": Decimal("1.00000000"),
        "average_rate": Decimal("1.00000000"),
        "total_assets_local": Decimal("5000000.00"),
        "total_liabilities_local": Decimal("2000000.00"),
        "total_equity_local": Decimal("3000000.00"),
        "net_income_local": Decimal("500000.00"),
        "total_assets_converted": Decimal("5000000.00"),
        "total_liabilities_converted": Decimal("2000000.00"),
        "total_equity_converted": Decimal("3000000.00"),
        "net_income_converted": Decimal("500000.00"),
        "translation_difference": Decimal("0.00"),
        "intercompany_receivables": Decimal("100000.00"),
        "intercompany_payables": Decimal("50000.00"),
        "intercompany_sales": Decimal("200000.00"),
        "intercompany_purchases": Decimal("150000.00"),
        "dividends_to_parent": Decimal("100000.00"),
        "status": "validated",
        "is_audited": False,
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_elimination():
    """Elimination exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "consolidation_id": str(uuid4()),
        "elimination_type": "intercompany_receivables",
        "code": "ELIM-001",
        "description": "Elimination creances/dettes entre Holding et France",
        "entity1_id": str(uuid4()),
        "entity2_id": str(uuid4()),
        "amount": Decimal("100000.00"),
        "currency": "EUR",
        "journal_entries": [
            {"account": "401_ELIM", "debit": 100000, "credit": 0, "label": "Elimination dette"},
            {"account": "411_ELIM", "debit": 0, "credit": 100000, "label": "Elimination creance"}
        ],
        "is_automatic": True,
        "is_validated": False,
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_reconciliation():
    """Reconciliation intercompany exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "consolidation_id": str(uuid4()),
        "entity1_id": str(uuid4()),
        "entity2_id": str(uuid4()),
        "transaction_type": "receivable",
        "amount_entity1": Decimal("100000.00"),
        "amount_entity2": Decimal("100050.00"),
        "currency": "EUR",
        "difference": Decimal("50.00"),
        "difference_pct": Decimal("0.0500"),
        "is_reconciled": False,
        "is_within_tolerance": True,
        "tolerance_amount": Decimal("100.00"),
        "tolerance_pct": Decimal("0.1000"),
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_exchange_rate():
    """Cours de change exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "from_currency": "USD",
        "to_currency": "EUR",
        "rate_date": date(2025, 12, 31),
        "closing_rate": Decimal("0.92500000"),
        "average_rate": Decimal("0.91200000"),
        "historical_rate": Decimal("0.89000000"),
        "source": "BCE",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_report():
    """Rapport consolide exemple."""
    return {
        "id": str(uuid4()),
        "tenant_id": "tenant-test-001",
        "consolidation_id": str(uuid4()),
        "report_type": "balance_sheet",
        "name": "Bilan Consolide T4 2025",
        "description": "Bilan consolide au 31/12/2025",
        "period_start": date(2025, 10, 1),
        "period_end": date(2025, 12, 31),
        "report_data": {
            "assets": {"total": "10000000.00"},
            "liabilities": {"total": "4000000.00"},
            "equity": {"total": "6000000.00"}
        },
        "comparative_data": None,
        "parameters": {},
        "is_final": False,
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def perimeter_data():
    """Donnees pour creer un perimetre."""
    return {
        "code": "GRP-2025",
        "name": "Groupe AZALS 2025",
        "description": "Perimetre annuel",
        "fiscal_year": 2025,
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 12, 31),
        "consolidation_currency": "EUR",
        "accounting_standard": "french_gaap"
    }


@pytest.fixture
def entity_data():
    """Donnees pour creer une entite."""
    return {
        "perimeter_id": str(uuid4()),
        "code": "HOLDING",
        "name": "AZALS Holding SA",
        "country": "FR",
        "currency": "EUR",
        "is_parent": True,
        "consolidation_method": "full_integration",
        "control_type": "exclusive",
        "direct_ownership_pct": Decimal("100.000")
    }


@pytest.fixture
def consolidation_data():
    """Donnees pour creer une consolidation."""
    return {
        "perimeter_id": str(uuid4()),
        "code": "CONSO-2025-Q4",
        "name": "Consolidation Q4 2025",
        "period_start": date(2025, 10, 1),
        "period_end": date(2025, 12, 31),
        "fiscal_year": 2025,
        "period_type": "quarterly",
        "consolidation_currency": "EUR",
        "accounting_standard": "french_gaap"
    }


@pytest.fixture
def package_data():
    """Donnees pour creer un paquet."""
    return {
        "consolidation_id": str(uuid4()),
        "entity_id": str(uuid4()),
        "period_start": date(2025, 10, 1),
        "period_end": date(2025, 12, 31),
        "local_currency": "EUR",
        "total_assets_local": Decimal("5000000.00"),
        "total_liabilities_local": Decimal("2000000.00"),
        "total_equity_local": Decimal("3000000.00"),
        "net_income_local": Decimal("500000.00"),
        "intercompany_receivables": Decimal("100000.00"),
        "intercompany_payables": Decimal("50000.00"),
        "intercompany_sales": Decimal("200000.00"),
        "intercompany_purchases": Decimal("150000.00")
    }
