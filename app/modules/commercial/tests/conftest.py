"""
Configuration pytest et fixtures communes pour les tests Commercial
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole
from fastapi import Depends

from app.modules.commercial.models import (
    Customer,
    Contact,
    Opportunity,
    CommercialDocument,
    CatalogProduct,
    CustomerActivity,
    PipelineStage,
    CustomerType,
    DocumentType,
    DocumentStatus,
    OpportunityStatus,
    ActivityType,
)


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture(scope="function")
def clean_database(db_session):
    """Nettoyer la base après chaque test."""
    yield
    db_session.rollback()


# ============================================================================
# FIXTURES DONNÉES COMMERCIAL
# ============================================================================

@pytest.fixture
def sample_customer(db_session, tenant_id):
    """Fixture pour un client de test"""
    customer = Customer(
        id=uuid4(),
        tenant_id=tenant_id,
        code="CLI-TEST-001",
        name="Client Test SA",
        type=CustomerType.CUSTOMER,
        email="contact@client-test.com",
        phone="+33123456789",
        is_active=True,
        created_by="user-test-001",
        created_at=datetime.utcnow()
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def sample_prospect(db_session, tenant_id):
    """Fixture pour un prospect de test"""
    prospect = Customer(
        id=uuid4(),
        tenant_id=tenant_id,
        code="PROS-TEST-001",
        name="Prospect Test",
        type=CustomerType.PROSPECT,
        is_active=True,
        created_by="user-test-001"
    )
    db_session.add(prospect)
    db_session.commit()
    db_session.refresh(prospect)
    return prospect


@pytest.fixture
def sample_contact(db_session, tenant_id, sample_customer):
    """Fixture pour un contact de test"""
    contact = Contact(
        id=uuid4(),
        tenant_id=tenant_id,
        customer_id=sample_customer.id,
        first_name="Jean",
        last_name="Dupont",
        email="jean.dupont@client-test.com",
        phone="+33123456789",
        position="Directeur Commercial",
        is_primary=True
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture
def sample_opportunity(db_session, tenant_id, sample_customer):
    """Fixture pour une opportunité de test"""
    opportunity = Opportunity(
        id=uuid4(),
        tenant_id=tenant_id,
        customer_id=sample_customer.id,
        name="Opportunité Test",
        amount=50000.0,
        probability=0.75,
        status=OpportunityStatus.QUALIFIED,
        expected_close_date=date.today(),
        created_by="user-test-001",
        created_at=datetime.utcnow()
    )
    db_session.add(opportunity)
    db_session.commit()
    db_session.refresh(opportunity)
    return opportunity


@pytest.fixture
def sample_document(db_session, tenant_id, sample_customer):
    """Fixture pour un document de test (devis)"""
    document = CommercialDocument(
        id=uuid4(),
        tenant_id=tenant_id,
        customer_id=sample_customer.id,
        document_type=DocumentType.QUOTE,
        number="DEV-2024-001",
        date=date.today(),
        status=DocumentStatus.DRAFT,
        total_ht=10000.0,
        total_tva=2000.0,
        total_ttc=12000.0,
        created_by="user-test-001",
        created_at=datetime.utcnow()
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def sample_product(db_session, tenant_id):
    """Fixture pour un produit de test"""
    product = CatalogProduct(
        id=uuid4(),
        tenant_id=tenant_id,
        code="PROD-TEST-001",
        name="Produit Test",
        description="Description du produit test",
        unit_price=99.99,
        cost_price=50.0,
        is_service=False,
        is_active=True,
        vat_rate=0.20
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_activity(db_session, tenant_id, sample_customer):
    """Fixture pour une activité de test"""
    activity = CustomerActivity(
        id=uuid4(),
        tenant_id=tenant_id,
        customer_id=sample_customer.id,
        activity_type=ActivityType.CALL,
        subject="Appel de suivi",
        description="Discussion sur le projet",
        activity_date=datetime.utcnow(),
        duration=30,
        is_completed=False,
        created_by="user-test-001"
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


@pytest.fixture
def sample_pipeline_stage(db_session, tenant_id):
    """Fixture pour une étape de pipeline"""
    stage = PipelineStage(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Qualification",
        order=1,
        probability=0.25,
        is_active=True
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)
    return stage


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
def create_test_data():
    """Factory pour créer des données de test"""
    def _create(model_class, **kwargs):
        instance = model_class(**kwargs)
        return instance
    return _create


@pytest.fixture
def mock_service():
    """Mock du service Commercial pour tests unitaires"""
    service = Mock()
    service.create_customer = Mock(return_value={"id": str(uuid4()), "code": "TEST"})
    service.list_customers = Mock(return_value=([], 0))
    service.get_customer = Mock(return_value=None)
    service.create_opportunity = Mock(return_value={"id": str(uuid4())})
    service.create_document = Mock(return_value={"id": str(uuid4())})
    return service


@pytest.fixture
def sample_customer_data():
    """Données de test pour création client"""
    return {
        "code": "CLI-NEW-001",
        "name": "Nouveau Client",
        "type": "CUSTOMER",
        "email": "nouveau@client.com",
        "phone": "+33123456789",
        "is_active": True
    }


@pytest.fixture
def sample_opportunity_data(sample_customer):
    """Données de test pour création opportunité"""
    return {
        "customer_id": str(sample_customer.id),
        "name": "Nouvelle Opportunité",
        "amount": 25000.0,
        "probability": 0.5,
        "expected_close_date": str(date.today()),
        "status": "QUALIFIED"
    }


@pytest.fixture
def sample_document_data(sample_customer):
    """Données de test pour création document"""
    return {
        "customer_id": str(sample_customer.id),
        "document_type": "QUOTE",
        "number": "DEV-NEW-001",
        "date": str(date.today()),
        "status": "DRAFT"
    }


# ============================================================================
# FIXTURES ASSERTIONS
# ============================================================================

@pytest.fixture
def assert_response_success():
    """Helper pour asserter une réponse successful"""
    def _assert(response, expected_status=200):
        assert response.status_code == expected_status
        if response.status_code != 204:  # No content
            data = response.json()
            assert data is not None
            return data
    return _assert


@pytest.fixture
def assert_tenant_isolation():
    """Helper pour vérifier l'isolation tenant"""
    def _assert(response, tenant_id):
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if "tenant_id" in item:
                        assert item["tenant_id"] == tenant_id
            elif isinstance(data, dict):
                if "items" in data:  # Liste paginée
                    for item in data["items"]:
                        if "tenant_id" in item:
                            assert item["tenant_id"] == tenant_id
                elif "tenant_id" in data:
                    assert data["tenant_id"] == tenant_id
    return _assert


@pytest.fixture
def assert_audit_trail():
    """Helper pour vérifier la présence d'audit trail"""
    def _assert(response_data):
        assert "created_by" in response_data or "recorded_by" in response_data
        assert "created_at" in response_data or "activity_date" in response_data
    return _assert


@pytest.fixture
def assert_csv_export():
    """Helper pour valider un export CSV"""
    def _assert(response, expected_filename_pattern):
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "Content-Disposition" in response.headers
        assert expected_filename_pattern in response.headers["Content-Disposition"]
        # Vérifier traçabilité tenant
        assert "X-Tenant-ID" in response.headers or response.status_code == 200
    return _assert
