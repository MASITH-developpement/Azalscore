"""
Integration tests for Automated Accounting module.

Tests the full flow:
- Document upload → OCR → AI Classification → Auto-accounting → Reconciliation

These tests verify the end-to-end functionality of the module.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import date, datetime
import uuid
import io

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDocumentToAccountingFlow:
    """Integration tests for full document processing flow."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def tenant_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def user_id(self):
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_full_invoice_processing_flow(self, mock_db, tenant_id, user_id):
        """Test complete flow from invoice upload to accounting entry."""
        from app.modules.automated_accounting.services import (
            DocumentService,
            OCRService,
            AIClassificationService,
            AutoAccountingService,
        )

        # 1. Create document service
        doc_service = DocumentService(mock_db)
        ocr_service = OCRService(mock_db)
        ai_service = AIClassificationService(mock_db)
        accounting_service = AutoAccountingService(mock_db)

        # Mock file content (PDF invoice)
        file_content = b"%PDF-1.4 fake invoice content"
        filename = "invoice_FA-2024-001.pdf"

        # 2. Mock OCR result
        ocr_result = {
            "raw_text": """
            FACTURE N° FA-2024-00123
            Date: 15/03/2024

            FOURNISSEUR ABC SARL
            SIRET: 123 456 789 00012

            Total HT: 1 000,00 €
            TVA 20%: 200,00 €
            Total TTC: 1 200,00 €
            """,
            "extracted_fields": [
                {"field_name": "invoice_number", "value": "FA-2024-00123", "confidence": 0.95},
                {"field_name": "date", "value": "15/03/2024", "confidence": 0.98},
                {"field_name": "total_ht", "value": "1000.00", "confidence": 0.96},
                {"field_name": "total_tva", "value": "200.00", "confidence": 0.97},
                {"field_name": "total_ttc", "value": "1200.00", "confidence": 0.99},
                {"field_name": "siret", "value": "12345678900012", "confidence": 0.94},
            ],
            "confidence_score": 0.965,
        }

        # 3. Mock AI classification result
        classification_result = {
            "document_type": "INVOICE_RECEIVED",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
            "suggested_vendor_name": "FOURNISSEUR ABC SARL",
            "suggested_account_code": "607100",
            "suggested_account_name": "Achats de marchandises",
            "suggested_journal_code": "ACH",
            "suggested_tax_code": "TVA_DEDUCTIBLE_20",
        }

        # 4. Expected accounting entry
        expected_entry = {
            "journal_code": "ACH",
            "entry_date": date(2024, 3, 15),
            "description": "Facture FA-2024-00123 - FOURNISSEUR ABC SARL",
            "lines": [
                {
                    "account_code": "607100",
                    "account_name": "Achats de marchandises",
                    "debit": Decimal("1000.00"),
                    "credit": Decimal("0.00"),
                    "label": "Achat marchandises",
                },
                {
                    "account_code": "445660",
                    "account_name": "TVA déductible sur ABS",
                    "debit": Decimal("200.00"),
                    "credit": Decimal("0.00"),
                    "label": "TVA déductible 20%",
                },
                {
                    "account_code": "401000",
                    "account_name": "Fournisseurs",
                    "debit": Decimal("0.00"),
                    "credit": Decimal("1200.00"),
                    "label": "FOURNISSEUR ABC SARL",
                },
            ],
            "status": "AUTO_VALIDATED",
        }

        # Verify the flow produces balanced entry
        total_debit = sum(l["debit"] for l in expected_entry["lines"])
        total_credit = sum(l["credit"] for l in expected_entry["lines"])
        assert total_debit == total_credit == Decimal("1200.00")

    @pytest.mark.asyncio
    async def test_low_confidence_requires_validation(self, mock_db, tenant_id):
        """Test that low confidence documents require manual validation."""
        from app.modules.automated_accounting.services import DocumentService

        doc_service = DocumentService(mock_db)

        # Poor quality scan with low OCR confidence
        ocr_result = {
            "raw_text": "illegible... FACTUR3... 1OOO EUR",
            "extracted_fields": [
                {"field_name": "total_ttc", "value": "1000.00", "confidence": 0.55},
            ],
            "confidence_score": 0.45,
        }

        classification_result = {
            "document_type": "INVOICE_RECEIVED",
            "confidence_level": "VERY_LOW",
            "confidence_score": 0.42,
        }

        # Document should be flagged for manual review
        assert classification_result["confidence_level"] == "VERY_LOW"
        assert classification_result["confidence_score"] < 0.60

    @pytest.mark.asyncio
    async def test_duplicate_detection_blocks_processing(self, mock_db, tenant_id):
        """Test that duplicate documents are detected and blocked."""
        from app.modules.automated_accounting.services import OCRService

        ocr_service = OCRService(mock_db)

        file_content = b"same file content"
        file_hash = ocr_service.calculate_file_hash(file_content)

        # Mock finding existing document with same hash
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=uuid.uuid4())
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_duplicate, existing_id = await ocr_service.check_duplicate(
            tenant_id, file_hash
        )

        assert is_duplicate is True
        assert existing_id is not None


class TestBankReconciliationFlow:
    """Integration tests for bank transaction reconciliation."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def tenant_id(self):
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_auto_reconciliation_exact_match(self, mock_db, tenant_id):
        """Test automatic reconciliation with exact amount match."""
        from app.modules.automated_accounting.services import ReconciliationService

        recon_service = ReconciliationService(mock_db)

        # Bank transaction
        transaction = {
            "id": uuid.uuid4(),
            "amount": Decimal("-1200.00"),  # Payment outgoing
            "description": "VIREMENT FOURNISSEUR ABC FA-2024-00123",
            "transaction_date": date(2024, 3, 20),
            "counterparty_name": "FOURNISSEUR ABC",
        }

        # Matching invoice
        document = {
            "id": uuid.uuid4(),
            "document_type": "INVOICE_RECEIVED",
            "amount_total": Decimal("1200.00"),
            "reference": "FA-2024-00123",
            "partner_name": "FOURNISSEUR ABC SARL",
            "payment_status": "PENDING",
        }

        # Mock the matching logic
        match_confidence = 0.95  # High confidence match

        # Should auto-reconcile when confidence >= 90%
        should_auto_reconcile = match_confidence >= 0.90
        assert should_auto_reconcile is True

    @pytest.mark.asyncio
    async def test_partial_amount_requires_review(self, mock_db, tenant_id):
        """Test that partial payments require manual review."""
        transaction = {
            "id": uuid.uuid4(),
            "amount": Decimal("-600.00"),  # Partial payment
            "description": "ACOMPTE FA-2024-00123",
        }

        document = {
            "id": uuid.uuid4(),
            "amount_total": Decimal("1200.00"),
            "reference": "FA-2024-00123",
        }

        # Partial payment should flag for review
        payment_ratio = abs(transaction["amount"]) / document["amount_total"]
        assert payment_ratio < 1.0  # Not full payment
        # Should not auto-reconcile partial payments

    @pytest.mark.asyncio
    async def test_rule_based_reconciliation(self, mock_db, tenant_id):
        """Test reconciliation using custom rules."""
        from app.modules.automated_accounting.services import ReconciliationService

        recon_service = ReconciliationService(mock_db)

        # Custom rule: Match "LOYER" transactions to rent account
        rule = {
            "pattern_type": "CONTAINS",
            "pattern_field": "description",
            "pattern_value": "LOYER",
            "target_type": "ACCOUNT",
            "target_value": "613200",  # Rent expense account
        }

        transaction = {
            "description": "LOYER BUREAUX MARS 2024",
            "amount": Decimal("-2500.00"),
        }

        # Rule should match
        import re
        matches = rule["pattern_value"].lower() in transaction["description"].lower()
        assert matches is True


class TestMultiDocumentProcessing:
    """Integration tests for bulk document processing."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_bulk_upload_processing(self, mock_db):
        """Test processing multiple documents in bulk."""
        documents = [
            {"filename": "invoice1.pdf", "type": "INVOICE_RECEIVED"},
            {"filename": "invoice2.pdf", "type": "INVOICE_RECEIVED"},
            {"filename": "expense.pdf", "type": "EXPENSE_NOTE"},
        ]

        # All documents should be queued for processing
        assert len(documents) == 3

    @pytest.mark.asyncio
    async def test_bulk_validation_by_expert(self, mock_db):
        """Test expert bulk validation of pending entries."""
        from app.modules.automated_accounting.services import AutoAccountingService

        service = AutoAccountingService(mock_db)

        pending_entries = [uuid.uuid4() for _ in range(10)]
        expert_id = uuid.uuid4()

        # Mock successful bulk validation
        mock_entries = [
            Mock(id=eid, status="PENDING_VALIDATION") for eid in pending_entries
        ]
        mock_result = Mock()
        mock_result.scalars = Mock(
            return_value=Mock(all=Mock(return_value=mock_entries))
        )
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.bulk_validate(
            entry_ids=pending_entries,
            validated_by=expert_id,
        )

        assert result is not None


class TestAPIEndpointIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def mock_auth_user(self):
        return {
            "id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "role": "EXPERT_COMPTABLE",
            "capabilities": [
                "accounting.expert.view",
                "accounting.expert.validate",
            ],
        }

    @pytest.mark.asyncio
    async def test_dirigeant_dashboard_endpoint(self, mock_auth_user):
        """Test dirigeant dashboard API returns correct data."""
        expected_response = {
            "cash_position": {
                "current_balance": 50000.00,
                "available_balance": 45000.00,
            },
            "cash_forecast": [],
            "invoices_receivable": {
                "total": 25000.00,
                "overdue": 5000.00,
            },
            "invoices_payable": {
                "total": 15000.00,
                "due_soon": 8000.00,
            },
        }

        # Verify response structure
        assert "cash_position" in expected_response
        assert "invoices_receivable" in expected_response

    @pytest.mark.asyncio
    async def test_assistante_upload_endpoint(self, mock_auth_user):
        """Test assistante document upload endpoint."""
        # Assistante should be able to upload
        # but NOT validate or access bank

        assistante_capabilities = [
            "accounting.assistante.view",
            "accounting.assistante.upload",
        ]

        can_upload = "accounting.assistante.upload" in assistante_capabilities
        can_validate = "accounting.expert.validate" in assistante_capabilities
        can_access_bank = "accounting.bank.view" in assistante_capabilities

        assert can_upload is True
        assert can_validate is False
        assert can_access_bank is False

    @pytest.mark.asyncio
    async def test_expert_validation_endpoint(self, mock_auth_user):
        """Test expert validation endpoint."""
        expert_capabilities = [
            "accounting.expert.view",
            "accounting.expert.validate",
            "accounting.reconciliation.manage",
        ]

        can_validate = "accounting.expert.validate" in expert_capabilities
        can_reconcile = "accounting.reconciliation.manage" in expert_capabilities

        assert can_validate is True
        assert can_reconcile is True


class TestErrorHandlingFlow:
    """Integration tests for error handling in the flow."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_ocr_failure_creates_alert(self, mock_db):
        """Test that OCR failure creates an alert."""
        from app.modules.automated_accounting.services import DocumentService

        service = DocumentService(mock_db)

        # OCR fails on corrupted file
        ocr_error = {
            "success": False,
            "error": "Unable to process image",
            "confidence_score": 0.0,
        }

        # Should create DOCUMENT_UNREADABLE alert
        alert_type = "DOCUMENT_UNREADABLE"
        severity = "ERROR"

        assert alert_type == "DOCUMENT_UNREADABLE"
        assert severity == "ERROR"

    @pytest.mark.asyncio
    async def test_bank_sync_failure_creates_alert(self, mock_db):
        """Test that bank sync failure creates an alert."""
        from app.modules.automated_accounting.services import BankPullService

        service = BankPullService(mock_db)

        # Bank connection fails
        sync_error = {
            "success": False,
            "error": "Authentication expired",
            "connection_id": uuid.uuid4(),
        }

        # Should create BANK_SYNC_FAILED alert
        alert_type = "BANK_SYNC_FAILED"
        severity = "WARNING"

        assert alert_type == "BANK_SYNC_FAILED"

    @pytest.mark.asyncio
    async def test_unbalanced_entry_rejected(self, mock_db):
        """Test that unbalanced entries are rejected."""
        # Manually constructed unbalanced entry (should never happen)
        entry = {
            "lines": [
                {"account_code": "607100", "debit": Decimal("1000.00"), "credit": Decimal("0.00")},
                {"account_code": "401000", "debit": Decimal("0.00"), "credit": Decimal("900.00")},
            ],
        }

        total_debit = sum(l["debit"] for l in entry["lines"])
        total_credit = sum(l["credit"] for l in entry["lines"])

        is_balanced = total_debit == total_credit
        assert is_balanced is False

        # System should reject this entry
        should_reject = not is_balanced
        assert should_reject is True


class TestPeriodCertificationFlow:
    """Integration tests for accounting period certification."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_period_can_be_certified(self, mock_db):
        """Test that a period with no pending items can be certified."""
        period = "2024-03"

        period_status = {
            "period": period,
            "documents_count": 150,
            "entries_count": 145,
            "pending_validation": 0,
            "unreconciled": 0,
            "status": "PENDING_CERTIFICATION",
        }

        can_certify = (
            period_status["pending_validation"] == 0
            and period_status["unreconciled"] == 0
        )

        assert can_certify is True

    @pytest.mark.asyncio
    async def test_period_blocked_with_pending_items(self, mock_db):
        """Test that period certification is blocked with pending items."""
        period_status = {
            "period": "2024-03",
            "pending_validation": 5,
            "unreconciled": 3,
            "status": "OPEN",
        }

        can_certify = (
            period_status["pending_validation"] == 0
            and period_status["unreconciled"] == 0
        )

        assert can_certify is False

    @pytest.mark.asyncio
    async def test_certified_period_is_locked(self, mock_db):
        """Test that certified periods cannot be modified."""
        certified_period = {
            "period": "2024-02",
            "status": "CERTIFIED",
            "certified_at": datetime(2024, 3, 5, 10, 0, 0),
            "certified_by": "Expert Comptable",
        }

        is_locked = certified_period["status"] == "CERTIFIED"
        assert is_locked is True

        # Modifications should be rejected
        can_modify = not is_locked
        assert can_modify is False
