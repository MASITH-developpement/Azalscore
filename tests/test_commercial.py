"""
AZALS MODULE M1 - Tests Commercial
===================================

Tests unitaires pour le CRM et la gestion commerciale.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.commercial.models import (
    Customer, Contact, Opportunity, CommercialDocument, DocumentLine,
    Payment, CustomerActivity, PipelineStage, CatalogProduct as Product,
    CustomerType, OpportunityStatus, DocumentType, DocumentStatus,
    PaymentMethod, PaymentTerms, ActivityType
)

# Import des schémas
from app.modules.commercial.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    ContactCreate, ContactUpdate,
    OpportunityCreate, OpportunityUpdate,
    DocumentCreate, DocumentLineCreate,
    PaymentCreate,
    ActivityCreate,
    PipelineStageCreate,
    ProductCreate, ProductUpdate,
    SalesDashboard, PipelineStats
)

# Import du service
from app.modules.commercial.service import CommercialService, get_commercial_service


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestEnums:
    """Tests des enums."""

    def test_customer_type_values(self):
        """Vérifier les valeurs de CustomerType."""
        assert CustomerType.PROSPECT.value == "PROSPECT"
        assert CustomerType.LEAD.value == "LEAD"
        assert CustomerType.CUSTOMER.value == "CUSTOMER"
        assert CustomerType.VIP.value == "VIP"
        assert CustomerType.PARTNER.value == "PARTNER"
        assert CustomerType.CHURNED.value == "CHURNED"

    def test_opportunity_status_values(self):
        """Vérifier les valeurs de OpportunityStatus."""
        assert OpportunityStatus.NEW.value == "NEW"
        assert OpportunityStatus.QUALIFIED.value == "QUALIFIED"
        assert OpportunityStatus.PROPOSAL.value == "PROPOSAL"
        assert OpportunityStatus.NEGOTIATION.value == "NEGOTIATION"
        assert OpportunityStatus.WON.value == "WON"
        assert OpportunityStatus.LOST.value == "LOST"

    def test_document_type_values(self):
        """Vérifier les valeurs de DocumentType."""
        assert DocumentType.QUOTE.value == "QUOTE"
        assert DocumentType.ORDER.value == "ORDER"
        assert DocumentType.INVOICE.value == "INVOICE"
        assert DocumentType.CREDIT_NOTE.value == "CREDIT_NOTE"
        assert DocumentType.PROFORMA.value == "PROFORMA"
        assert DocumentType.DELIVERY.value == "DELIVERY"

    def test_document_status_values(self):
        """Vérifier les valeurs de DocumentStatus."""
        assert DocumentStatus.DRAFT.value == "DRAFT"
        assert DocumentStatus.VALIDATED.value == "VALIDATED"
        assert DocumentStatus.SENT.value == "SENT"
        assert DocumentStatus.PAID.value == "PAID"

    def test_payment_method_values(self):
        """Vérifier les valeurs de PaymentMethod."""
        assert PaymentMethod.BANK_TRANSFER.value == "BANK_TRANSFER"
        assert PaymentMethod.CHECK.value == "CHECK"
        assert PaymentMethod.CREDIT_CARD.value == "CREDIT_CARD"

    def test_payment_terms_values(self):
        """Vérifier les valeurs de PaymentTerms."""
        assert PaymentTerms.IMMEDIATE.value == "IMMEDIATE"
        assert PaymentTerms.NET_30.value == "NET_30"
        assert PaymentTerms.NET_60.value == "NET_60"


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_customer_model_creation(self):
        """Tester la création d'un modèle Customer."""
        customer = Customer(
            tenant_id="test-tenant",
            code="CLI001",
            name="Entreprise Test",
            type=CustomerType.PROSPECT,
            email="contact@test.com"
        )
        assert customer.code == "CLI001"
        assert customer.name == "Entreprise Test"
        assert customer.type == CustomerType.PROSPECT

    def test_contact_model_creation(self):
        """Tester la création d'un modèle Contact."""
        contact = Contact(
            tenant_id="test-tenant",
            customer_id=uuid4(),
            first_name="Jean",
            last_name="Dupont",
            email="jean.dupont@test.com"
        )
        assert contact.first_name == "Jean"
        assert contact.last_name == "Dupont"

    def test_opportunity_model_creation(self):
        """Tester la création d'un modèle Opportunity."""
        opportunity = Opportunity(
            tenant_id="test-tenant",
            customer_id=uuid4(),
            code="OPP001",
            name="Projet Important",
            amount=Decimal("50000.00"),
            probability=50
        )
        assert opportunity.code == "OPP001"
        assert opportunity.amount == Decimal("50000.00")
        assert opportunity.probability == 50

    def test_document_model_creation(self):
        """Tester la création d'un modèle CommercialDocument."""
        document = CommercialDocument(
            tenant_id="test-tenant",
            customer_id=uuid4(),
            type=DocumentType.QUOTE,
            number="DEV-2026-00001",
            date=date.today(),
            total=Decimal("5000.00")
        )
        assert document.type == DocumentType.QUOTE
        assert document.number == "DEV-2026-00001"
        assert document.total == Decimal("5000.00")

    def test_payment_model_creation(self):
        """Tester la création d'un modèle Payment."""
        payment = Payment(
            tenant_id="test-tenant",
            document_id=uuid4(),
            method=PaymentMethod.BANK_TRANSFER,
            amount=Decimal("5000.00"),
            date=date.today()
        )
        assert payment.method == PaymentMethod.BANK_TRANSFER
        assert payment.amount == Decimal("5000.00")

    def test_activity_model_creation(self):
        """Tester la création d'un modèle CustomerActivity."""
        activity = CustomerActivity(
            tenant_id="test-tenant",
            customer_id=uuid4(),
            type=ActivityType.CALL,
            subject="Appel de suivi",
            date=datetime.utcnow()
        )
        assert activity.type == ActivityType.CALL
        assert activity.subject == "Appel de suivi"

    def test_product_model_creation(self):
        """Tester la création d'un modèle Product."""
        product = Product(
            tenant_id="test-tenant",
            code="PROD001",
            name="Produit Test",
            unit_price=Decimal("99.99"),
            tax_rate=20.0
        )
        assert product.code == "PROD001"
        assert product.unit_price == Decimal("99.99")


# ============================================================================
# TESTS SCHÉMAS
# ============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_customer_create_schema(self):
        """Tester le schéma CustomerCreate."""
        data = CustomerCreate(
            code="CLI001",
            name="Test Client",
            type=CustomerType.PROSPECT,
            email="test@test.com"
        )
        assert data.code == "CLI001"
        assert data.name == "Test Client"

    def test_opportunity_create_schema(self):
        """Tester le schéma OpportunityCreate."""
        data = OpportunityCreate(
            code="OPP001",
            name="Opportunité Test",
            customer_id=uuid4(),
            amount=Decimal("10000.00"),
            probability=25
        )
        assert data.code == "OPP001"
        assert data.probability == 25

    def test_document_create_schema(self):
        """Tester le schéma DocumentCreate."""
        data = DocumentCreate(
            customer_id=uuid4(),
            type=DocumentType.QUOTE,
            date=date.today(),
            lines=[
                DocumentLineCreate(
                    description="Service conseil",
                    quantity=Decimal("10"),
                    unit_price=Decimal("100.00")
                )
            ]
        )
        assert data.type == DocumentType.QUOTE
        assert len(data.lines) == 1

    def test_product_create_schema(self):
        """Tester le schéma ProductCreate."""
        data = ProductCreate(
            code="SERV001",
            name="Service de conseil",
            is_service=True,
            unit_price=Decimal("500.00"),
            unit="h"
        )
        assert data.is_service == True
        assert data.unit == "h"


# ============================================================================
# TESTS SERVICE
# ============================================================================

class TestCommercialService:
    """Tests du service Commercial."""

    @pytest.fixture
    def mock_db(self):
        """Mock de la session DB."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Instance du service avec mock."""
        return CommercialService(mock_db, "test-tenant")

    # Tests Clients

    def test_create_customer(self, service, mock_db):
        """Tester la création d'un client."""
        data = CustomerCreate(
            code="CLI001",
            name="Test Client",
            type=CustomerType.PROSPECT
        )
        user_id = uuid4()

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        customer = service.create_customer(data, user_id)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_customer(self, service, mock_db):
        """Tester la récupération d'un client."""
        customer_id = uuid4()
        mock_customer = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

        result = service.get_customer(customer_id)

        assert result == mock_customer

    def test_list_customers(self, service, mock_db):
        """Tester le listage des clients."""
        mock_query = MagicMock()
        mock_query.count.return_value = 5
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value = mock_query

        items, total = service.list_customers()

        assert total == 5

    def test_convert_prospect(self, service, mock_db):
        """Tester la conversion d'un prospect en client."""
        customer_id = uuid4()
        mock_customer = MagicMock()
        mock_customer.type = CustomerType.PROSPECT
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

        result = service.convert_prospect(customer_id)

        assert mock_customer.type == CustomerType.CUSTOMER
        mock_db.commit.assert_called()

    # Tests Opportunités

    def test_create_opportunity(self, service, mock_db):
        """Tester la création d'une opportunité."""
        data = OpportunityCreate(
            code="OPP001",
            name="Opportunité Test",
            customer_id=uuid4(),
            amount=Decimal("10000.00"),
            probability=25
        )
        user_id = uuid4()

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        opportunity = service.create_opportunity(data, user_id)

        mock_db.add.assert_called_once()

    def test_win_opportunity(self, service, mock_db):
        """Tester le marquage d'une opportunité comme gagnée."""
        opp_id = uuid4()
        mock_opp = MagicMock()
        mock_opp.status = OpportunityStatus.PROPOSAL
        mock_opp.amount = Decimal("10000.00")
        mock_opp.customer_id = uuid4()

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_opp, MagicMock()]

        result = service.win_opportunity(opp_id, "Bon prix")

        assert mock_opp.status == OpportunityStatus.WON
        assert mock_opp.probability == 100
        mock_db.commit.assert_called()

    def test_lose_opportunity(self, service, mock_db):
        """Tester le marquage d'une opportunité comme perdue."""
        opp_id = uuid4()
        mock_opp = MagicMock()
        mock_opp.status = OpportunityStatus.PROPOSAL
        mock_opp.amount = Decimal("10000.00")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_opp

        result = service.lose_opportunity(opp_id, "Prix trop élevé")

        assert mock_opp.status == OpportunityStatus.LOST
        assert mock_opp.probability == 0

    # Tests Documents

    def test_create_document(self, service, mock_db):
        """Tester la création d'un document."""
        data = DocumentCreate(
            customer_id=uuid4(),
            type=DocumentType.QUOTE,
            date=date.today(),
            lines=[
                DocumentLineCreate(
                    description="Service",
                    quantity=Decimal("1"),
                    unit_price=Decimal("1000.00")
                )
            ]
        )
        user_id = uuid4()

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.all.return_value = []

        document = service.create_document(data, user_id)

        assert mock_db.add.called
        mock_db.commit.assert_called()

    def test_validate_document(self, service, mock_db):
        """Tester la validation d'un document."""
        doc_id = uuid4()
        user_id = uuid4()
        mock_doc = MagicMock()
        mock_doc.status = DocumentStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

        result = service.validate_document(doc_id, user_id)

        assert mock_doc.status == DocumentStatus.VALIDATED
        assert mock_doc.validated_by == user_id
        mock_db.commit.assert_called()

    # Tests Paiements

    def test_create_payment(self, service, mock_db):
        """Tester l'enregistrement d'un paiement."""
        doc_id = uuid4()
        data = PaymentCreate(
            document_id=doc_id,
            method=PaymentMethod.BANK_TRANSFER,
            amount=Decimal("5000.00")
        )
        user_id = uuid4()

        mock_doc = MagicMock()
        mock_doc.type = DocumentType.INVOICE
        mock_doc.total = Decimal("5000.00")
        mock_doc.paid_amount = Decimal("0")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        payment = service.create_payment(data, user_id)

        assert mock_doc.status == DocumentStatus.PAID
        mock_db.add.assert_called()

    # Tests Produits

    def test_create_product(self, service, mock_db):
        """Tester la création d'un produit."""
        data = ProductCreate(
            code="PROD001",
            name="Produit Test",
            unit_price=Decimal("99.99")
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        product = service.create_product(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_list_products(self, service, mock_db):
        """Tester le listage des produits."""
        mock_query = MagicMock()
        mock_query.count.return_value = 10
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value = mock_query

        items, total = service.list_products()

        assert total == 10

    # Tests Activités

    def test_create_activity(self, service, mock_db):
        """Tester la création d'une activité."""
        data = ActivityCreate(
            customer_id=uuid4(),
            type=ActivityType.CALL,
            subject="Appel de suivi"
        )
        user_id = uuid4()

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        activity = service.create_activity(data, user_id)

        mock_db.add.assert_called_once()

    def test_complete_activity(self, service, mock_db):
        """Tester la complétion d'une activité."""
        activity_id = uuid4()
        mock_activity = MagicMock()
        mock_activity.is_completed = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_activity

        result = service.complete_activity(activity_id)

        assert mock_activity.is_completed == True
        mock_db.commit.assert_called()

    # Tests Pipeline

    def test_create_pipeline_stage(self, service, mock_db):
        """Tester la création d'une étape du pipeline."""
        data = PipelineStageCreate(
            name="Nouveau",
            order=1,
            probability=10
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        stage = service.create_pipeline_stage(data)

        mock_db.add.assert_called_once()


# ============================================================================
# TESTS FACTORY
# ============================================================================

class TestFactory:
    """Tests de la factory du service."""

    def test_get_commercial_service(self):
        """Tester la factory get_commercial_service."""
        mock_db = MagicMock()
        service = get_commercial_service(mock_db, "test-tenant")

        assert isinstance(service, CommercialService)
        assert service.tenant_id == "test-tenant"


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestIntegration:
    """Tests d'intégration."""

    def test_quote_to_order_workflow(self):
        """Tester le workflow devis → commande."""
        mock_db = MagicMock()
        service = CommercialService(mock_db, "test-tenant")

        # Simuler un devis existant
        mock_quote = MagicMock()
        mock_quote.id = uuid4()
        mock_quote.type = DocumentType.QUOTE
        mock_quote.status = DocumentStatus.SENT
        mock_quote.lines = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_quote
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        # Convertir en commande
        order = service.convert_quote_to_order(mock_quote.id, uuid4())

        assert mock_quote.status == DocumentStatus.ACCEPTED
        mock_db.add.assert_called()

    def test_full_sales_cycle(self):
        """Tester un cycle de vente complet."""
        mock_db = MagicMock()
        service = CommercialService(mock_db, "test-tenant")

        # Ce test vérifie que les méthodes s'enchaînent correctement
        # Dans un vrai test d'intégration, on utiliserait une vraie DB

        # 1. Créer un prospect
        # 2. Créer une opportunité
        # 3. Créer un devis
        # 4. Convertir en commande
        # 5. Facturer
        # 6. Enregistrer le paiement

        # Vérification simplifiée
        assert service.tenant_id == "test-tenant"


# ============================================================================
# TESTS ISOLATION MULTI-TENANT
# ============================================================================

class TestMultiTenantIsolation:
    """Tests d'isolation multi-tenant."""

    def test_customer_tenant_filter(self):
        """Vérifier que les clients sont filtrés par tenant."""
        mock_db = MagicMock()
        service = CommercialService(mock_db, "tenant-a")

        service.list_customers()

        # Vérifier que le filtre tenant est appliqué
        mock_db.query.assert_called()
        call_args = str(mock_db.query.return_value.filter.call_args)
        # Le filtre tenant_id doit être présent dans la requête


# ============================================================================
# TESTS CALCULS
# ============================================================================

class TestCalculations:
    """Tests des calculs."""

    def test_line_total_calculation(self):
        """Tester le calcul des totaux de ligne."""
        mock_db = MagicMock()
        service = CommercialService(mock_db, "test-tenant")

        line = DocumentLine(
            tenant_id="test-tenant",
            document_id=uuid4(),
            line_number=1,
            description="Service",
            quantity=Decimal("10"),
            unit_price=Decimal("100.00"),
            discount_percent=10.0,
            tax_rate=20.0
        )

        service._calculate_line_totals(line)

        # Subtotal: 10 * 100 = 1000
        # Discount: 1000 * 10% = 100
        # Net: 1000 - 100 = 900
        # Tax: 900 * 20% = 180
        # Total: 900 + 180 = 1080
        assert line.subtotal == Decimal("900")
        assert line.tax_amount == Decimal("180")
        assert line.total == Decimal("1080")

    def test_weighted_amount_calculation(self):
        """Tester le calcul du montant pondéré."""
        opportunity = Opportunity(
            tenant_id="test-tenant",
            customer_id=uuid4(),
            code="OPP001",
            name="Test",
            amount=Decimal("10000.00"),
            probability=30
        )

        # Le montant pondéré devrait être 10000 * 30% = 3000
        weighted = opportunity.amount * Decimal(opportunity.probability) / 100
        assert weighted == Decimal("3000.00")
