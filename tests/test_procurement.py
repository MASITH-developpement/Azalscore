"""
AZALS MODULE M4 - Tests Achats (Procurement)
============================================

Tests unitaires pour la gestion des achats.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Import des modèles
from app.modules.procurement.models import (
    Supplier, SupplierContact, PurchaseRequisition, PurchaseRequisitionLine,
    SupplierQuotation, SupplierQuotationLine, PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine, PurchaseInvoice, PurchaseInvoiceLine,
    SupplierPayment, PaymentAllocation, SupplierEvaluation,
    SupplierStatus, SupplierType, RequisitionStatus, PurchaseOrderStatus,
    ReceivingStatus, PurchaseInvoiceStatus, QuotationStatus
)

# Import des schémas
from app.modules.procurement.schemas import (
    SupplierCreate, SupplierUpdate, SupplierContactCreate,
    RequisitionCreate, RequisitionLineCreate,
    QuotationCreate, QuotationLineCreate,
    PurchaseOrderCreate, OrderLineCreate as PurchaseOrderLineCreate,
    GoodsReceiptCreate, ReceiptLineCreate as GoodsReceiptLineCreate,
    PurchaseInvoiceCreate, InvoiceLineCreate as PurchaseInvoiceLineCreate,
    SupplierPaymentCreate, PaymentAllocationCreate,
    SupplierEvaluationCreate, ProcurementDashboard
)

# Import du service
from app.modules.procurement.service import ProcurementService, get_procurement_service


# =============================================================================
# TESTS DES ENUMS
# =============================================================================

class TestEnums:
    """Tests des énumérations."""

    def test_supplier_status_values(self):
        """Tester les statuts fournisseur."""
        assert SupplierStatus.PROSPECT.value == "PROSPECT"
        assert SupplierStatus.PENDING.value == "PENDING"
        assert SupplierStatus.APPROVED.value == "APPROVED"
        assert SupplierStatus.BLOCKED.value == "BLOCKED"
        assert SupplierStatus.INACTIVE.value == "INACTIVE"
        assert len(SupplierStatus) == 5

    def test_supplier_type_values(self):
        """Tester les types de fournisseur."""
        assert SupplierType.MANUFACTURER.value == "MANUFACTURER"
        assert SupplierType.DISTRIBUTOR.value == "DISTRIBUTOR"
        assert SupplierType.SERVICE.value == "SERVICE"
        assert SupplierType.FREELANCE.value == "FREELANCE"
        assert len(SupplierType) == 5

    def test_requisition_status_values(self):
        """Tester les statuts de demande d'achat."""
        assert RequisitionStatus.DRAFT.value == "DRAFT"
        assert RequisitionStatus.SUBMITTED.value == "SUBMITTED"
        assert RequisitionStatus.APPROVED.value == "APPROVED"
        assert RequisitionStatus.REJECTED.value == "REJECTED"
        assert RequisitionStatus.ORDERED.value == "ORDERED"
        assert len(RequisitionStatus) == 6

    def test_purchase_order_status_values(self):
        """Tester les statuts de commande."""
        assert PurchaseOrderStatus.DRAFT.value == "DRAFT"
        assert PurchaseOrderStatus.SENT.value == "SENT"
        assert PurchaseOrderStatus.CONFIRMED.value == "CONFIRMED"
        assert PurchaseOrderStatus.PARTIAL.value == "PARTIAL"
        assert PurchaseOrderStatus.RECEIVED.value == "RECEIVED"
        assert len(PurchaseOrderStatus) == 7

    def test_quotation_status_values(self):
        """Tester les statuts de devis."""
        assert QuotationStatus.REQUESTED.value == "REQUESTED"
        assert QuotationStatus.RECEIVED.value == "RECEIVED"
        assert QuotationStatus.ACCEPTED.value == "ACCEPTED"
        assert QuotationStatus.REJECTED.value == "REJECTED"
        assert len(QuotationStatus) == 5


# =============================================================================
# TESTS DES MODÈLES
# =============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_supplier_model(self):
        """Tester le modèle Supplier."""
        supplier = Supplier(
            tenant_id="test-tenant",
            code="FOUR001",
            name="Fournisseur Test",
            type=SupplierType.MANUFACTURER,
            email="contact@fournisseur.com"
        )
        assert supplier.code == "FOUR001"
        assert supplier.type == SupplierType.MANUFACTURER
        assert supplier.status == SupplierStatus.PROSPECT
        assert supplier.is_active == True

    def test_purchase_requisition_model(self):
        """Tester le modèle PurchaseRequisition."""
        requisition = PurchaseRequisition(
            tenant_id="test-tenant",
            number="DA-2026-001",
            title="Fournitures bureau",
            requester_id=uuid4(),
            requested_date=date.today()
        )
        assert requisition.number == "DA-2026-001"
        assert requisition.status == RequisitionStatus.DRAFT
        assert requisition.priority == "NORMAL"

    def test_purchase_order_model(self):
        """Tester le modèle PurchaseOrder."""
        order = PurchaseOrder(
            tenant_id="test-tenant",
            number="PO-2026-001",
            supplier_id=uuid4(),
            order_date=date.today()
        )
        assert order.number == "PO-2026-001"
        assert order.status == PurchaseOrderStatus.DRAFT
        assert order.total == Decimal("0")

    def test_goods_receipt_model(self):
        """Tester le modèle GoodsReceipt."""
        receipt = GoodsReceipt(
            tenant_id="test-tenant",
            number="BR-2026-001",
            order_id=uuid4(),
            supplier_id=uuid4(),
            receipt_date=date.today()
        )
        assert receipt.number == "BR-2026-001"
        assert receipt.status == ReceivingStatus.DRAFT

    def test_purchase_invoice_model(self):
        """Tester le modèle PurchaseInvoice."""
        invoice = PurchaseInvoice(
            tenant_id="test-tenant",
            number="FA-2026-001",
            supplier_id=uuid4(),
            invoice_date=date.today(),
            total=Decimal("5000")
        )
        assert invoice.number == "FA-2026-001"
        assert invoice.status == PurchaseInvoiceStatus.DRAFT
        assert invoice.paid_amount == Decimal("0")

    def test_supplier_evaluation_model(self):
        """Tester le modèle SupplierEvaluation."""
        evaluation = SupplierEvaluation(
            tenant_id="test-tenant",
            supplier_id=uuid4(),
            evaluation_date=date.today(),
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            overall_score=Decimal("4.2")
        )
        assert evaluation.overall_score == Decimal("4.2")


# =============================================================================
# TESTS DES SCHÉMAS
# =============================================================================

class TestSchemas:
    """Tests des schémas Pydantic."""

    def test_supplier_create_schema(self):
        """Tester le schéma SupplierCreate."""
        data = SupplierCreate(
            code="FOUR001",
            name="Fournisseur ABC",
            type=SupplierType.DISTRIBUTOR,
            email="contact@abc.com",
            payment_terms="NET30"
        )
        assert data.code == "FOUR001"
        assert data.type == SupplierType.DISTRIBUTOR

    def test_requisition_create_schema(self):
        """Tester le schéma RequisitionCreate."""
        lines = [
            RequisitionLineCreate(
                description="Papier A4",
                quantity=Decimal("10"),
                estimated_price=Decimal("25")
            )
        ]
        data = RequisitionCreate(
            title="Fournitures",
            required_date=date.today() + timedelta(days=7),
            lines=lines
        )
        assert data.title == "Fournitures"
        assert len(data.lines) == 1

    def test_purchase_order_create_schema(self):
        """Tester le schéma PurchaseOrderCreate."""
        lines = [
            PurchaseOrderLineCreate(
                description="Article A",
                quantity=Decimal("100"),
                unit_price=Decimal("10")
            )
        ]
        data = PurchaseOrderCreate(
            supplier_id=uuid4(),
            order_date=date.today(),
            lines=lines
        )
        assert len(data.lines) == 1


# =============================================================================
# TESTS DU SERVICE - FOURNISSEURS
# =============================================================================

class TestProcurementServiceSuppliers:
    """Tests du service Procurement - Fournisseurs."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProcurementService(mock_db, "test-tenant")

    def test_create_supplier(self, service, mock_db):
        """Tester la création d'un fournisseur."""
        data = SupplierCreate(
            code="FOUR001",
            name="Fournisseur Test",
            type=SupplierType.MANUFACTURER
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_supplier(data, uuid4())

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.code == "FOUR001"
        assert result.tenant_id == "test-tenant"

    def test_approve_supplier(self, service, mock_db):
        """Tester l'approbation d'un fournisseur."""
        supplier_id = uuid4()
        approver_id = uuid4()
        mock_supplier = MagicMock()
        mock_supplier.status = SupplierStatus.PENDING

        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        result = service.approve_supplier(supplier_id, approver_id)

        assert mock_supplier.status == SupplierStatus.APPROVED
        mock_db.commit.assert_called()

    def test_block_supplier(self, service, mock_db):
        """Tester le blocage d'un fournisseur."""
        supplier_id = uuid4()
        mock_supplier = MagicMock()
        mock_supplier.status = SupplierStatus.APPROVED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_supplier

        result = service.block_supplier(supplier_id, "Problèmes de qualité")

        assert mock_supplier.status == SupplierStatus.BLOCKED


# =============================================================================
# TESTS DU SERVICE - DEMANDES D'ACHAT
# =============================================================================

class TestProcurementServiceRequisitions:
    """Tests du service Procurement - Demandes d'achat."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProcurementService(mock_db, "test-tenant")

    def test_create_requisition(self, service, mock_db):
        """Tester la création d'une demande d'achat."""
        lines = [
            RequisitionLineCreate(
                description="Fourniture",
                quantity=Decimal("5"),
                estimated_price=Decimal("100")
            )
        ]
        data = RequisitionCreate(
            title="Demande test",
            required_date=date.today() + timedelta(days=14),
            lines=lines
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_requisition(data, uuid4())

        assert mock_db.add.called

    def test_submit_requisition(self, service, mock_db):
        """Tester la soumission d'une demande."""
        req_id = uuid4()
        mock_req = MagicMock()
        mock_req.status = RequisitionStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_req

        result = service.submit_requisition(req_id)

        assert mock_req.status == RequisitionStatus.SUBMITTED

    def test_approve_requisition(self, service, mock_db):
        """Tester l'approbation d'une demande."""
        req_id = uuid4()
        mock_req = MagicMock()
        mock_req.status = RequisitionStatus.SUBMITTED

        mock_db.query.return_value.filter.return_value.first.return_value = mock_req

        result = service.approve_requisition(req_id, uuid4())

        assert mock_req.status == RequisitionStatus.APPROVED


# =============================================================================
# TESTS DU SERVICE - COMMANDES
# =============================================================================

class TestProcurementServiceOrders:
    """Tests du service Procurement - Commandes."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProcurementService(mock_db, "test-tenant")

    def test_create_purchase_order(self, service, mock_db):
        """Tester la création d'une commande."""
        lines = [
            PurchaseOrderLineCreate(
                description="Produit A",
                quantity=Decimal("50"),
                unit_price=Decimal("20")
            )
        ]
        data = PurchaseOrderCreate(
            supplier_id=uuid4(),
            order_date=date.today(),
            lines=lines
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_purchase_order(data, uuid4())

        assert mock_db.add.called

    def test_send_purchase_order(self, service, mock_db):
        """Tester l'envoi d'une commande."""
        order_id = uuid4()
        mock_order = MagicMock()
        mock_order.status = PurchaseOrderStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_order

        result = service.send_purchase_order(order_id)

        assert mock_order.status == PurchaseOrderStatus.SENT

    def test_confirm_purchase_order(self, service, mock_db):
        """Tester la confirmation d'une commande."""
        order_id = uuid4()
        mock_order = MagicMock()
        mock_order.status = PurchaseOrderStatus.SENT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_order

        result = service.confirm_purchase_order(order_id, "REF-FOUR-123")

        assert mock_order.status == PurchaseOrderStatus.CONFIRMED


# =============================================================================
# TESTS DU SERVICE - RÉCEPTIONS
# =============================================================================

class TestProcurementServiceReceipts:
    """Tests du service Procurement - Réceptions."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProcurementService(mock_db, "test-tenant")

    def test_create_goods_receipt(self, service, mock_db):
        """Tester la création d'une réception."""
        lines = [
            GoodsReceiptLineCreate(
                order_line_id=uuid4(),
                description="Produit A",
                ordered_quantity=Decimal("50"),
                received_quantity=Decimal("48")
            )
        ]
        data = GoodsReceiptCreate(
            order_id=uuid4(),
            supplier_id=uuid4(),
            receipt_date=date.today(),
            lines=lines
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        result = service.create_goods_receipt(data, uuid4())

        assert mock_db.add.called

    def test_validate_receipt(self, service, mock_db):
        """Tester la validation d'une réception."""
        receipt_id = uuid4()
        mock_receipt = MagicMock()
        mock_receipt.status = ReceivingStatus.DRAFT
        mock_receipt.lines = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_receipt

        result = service.validate_receipt(receipt_id, uuid4())

        assert mock_receipt.status == ReceivingStatus.VALIDATED


# =============================================================================
# TESTS DU SERVICE - FACTURES
# =============================================================================

class TestProcurementServiceInvoices:
    """Tests du service Procurement - Factures."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProcurementService(mock_db, "test-tenant")

    def test_create_purchase_invoice(self, service, mock_db):
        """Tester la création d'une facture."""
        lines = [
            PurchaseInvoiceLineCreate(
                description="Service",
                quantity=Decimal("1"),
                unit_price=Decimal("5000")
            )
        ]
        data = PurchaseInvoiceCreate(
            supplier_id=uuid4(),
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            lines=lines
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_purchase_invoice(data, uuid4())

        assert mock_db.add.called

    def test_validate_invoice(self, service, mock_db):
        """Tester la validation d'une facture."""
        invoice_id = uuid4()
        mock_invoice = MagicMock()
        mock_invoice.status = PurchaseInvoiceStatus.DRAFT

        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice

        result = service.validate_invoice(invoice_id, uuid4())

        assert mock_invoice.status == PurchaseInvoiceStatus.VALIDATED


# =============================================================================
# TESTS DU SERVICE - PAIEMENTS
# =============================================================================

class TestProcurementServicePayments:
    """Tests du service Procurement - Paiements."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return ProcurementService(mock_db, "test-tenant")

    def test_create_payment(self, service, mock_db):
        """Tester la création d'un paiement."""
        data = SupplierPaymentCreate(
            supplier_id=uuid4(),
            payment_date=date.today(),
            amount=Decimal("5000"),
            payment_method="BANK_TRANSFER"
        )

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.create_payment(data, uuid4())

        mock_db.add.assert_called()

    def test_allocate_payment(self, service, mock_db):
        """Tester l'affectation d'un paiement."""
        payment_id = uuid4()
        invoice_id = uuid4()

        mock_payment = MagicMock()
        mock_payment.amount = Decimal("5000")

        mock_invoice = MagicMock()
        mock_invoice.remaining_amount = Decimal("5000")
        mock_invoice.status = PurchaseInvoiceStatus.VALIDATED

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_payment, mock_invoice]
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        data = PaymentAllocationCreate(
            payment_id=payment_id,
            invoice_id=invoice_id,
            amount=Decimal("5000")
        )

        result = service.allocate_payment(data)

        mock_db.add.assert_called()


# =============================================================================
# TESTS FACTORY
# =============================================================================

class TestFactory:
    """Tests de la factory."""

    def test_get_procurement_service(self):
        """Tester la factory."""
        mock_db = MagicMock()
        service = get_procurement_service(mock_db, "test-tenant")

        assert isinstance(service, ProcurementService)
        assert service.tenant_id == "test-tenant"


# =============================================================================
# TESTS MULTI-TENANT
# =============================================================================

class TestMultiTenant:
    """Tests d'isolation multi-tenant."""

    def test_tenant_isolation(self):
        """Tester l'isolation des tenants."""
        mock_db = MagicMock()

        service_a = ProcurementService(mock_db, "tenant-A")
        service_b = ProcurementService(mock_db, "tenant-B")

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Vérifier que les services ont des tenant_id différents
        assert service_a.tenant_id == "tenant-A"
        assert service_b.tenant_id == "tenant-B"


# =============================================================================
# TESTS CALCULS ACHATS
# =============================================================================

class TestProcurementCalculations:
    """Tests des calculs achats."""

    def test_order_line_total(self):
        """Tester le calcul du total d'une ligne."""
        quantity = Decimal("100")
        unit_price = Decimal("25.50")
        discount = Decimal("10")  # 10%
        tax_rate = Decimal("20")  # 20%

        subtotal = quantity * unit_price
        discount_amount = subtotal * discount / 100
        net = subtotal - discount_amount
        tax = net * tax_rate / 100
        total = net + tax

        assert subtotal == Decimal("2550")
        assert discount_amount == Decimal("255")
        assert net == Decimal("2295")
        assert tax == Decimal("459")
        assert total == Decimal("2754")

    def test_supplier_score_average(self):
        """Tester le calcul de la note moyenne fournisseur."""
        quality = Decimal("4.5")
        price = Decimal("4.0")
        delivery = Decimal("3.5")
        service = Decimal("4.0")

        average = (quality + price + delivery + service) / 4

        assert average == Decimal("4.0")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
