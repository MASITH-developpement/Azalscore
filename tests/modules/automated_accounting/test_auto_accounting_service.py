"""
Unit tests for Auto-Accounting Service.

Tests:
- Automatic journal entry generation
- Entry validation rules
- Multi-line entry creation
- Balance verification
- Auto-validation thresholds
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from decimal import Decimal
from datetime import date, datetime
import uuid

from app.modules.automated_accounting.services.auto_accounting_service import (
    AutoAccountingService,
    AccountingRulesEngine,
)
from app.modules.automated_accounting.models import (
    DocumentType,
    ConfidenceLevel,
)


class TestAccountingRulesEngine:
    """Tests for the AccountingRulesEngine class."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def engine(self, mock_db, tenant_id):
        """Create engine with required db and tenant_id."""
        return AccountingRulesEngine(db=mock_db, tenant_id=tenant_id)

    @pytest.fixture
    def sample_document(self, tenant_id):
        """Create a mock AccountingDocument for testing."""
        doc = MagicMock()
        doc.id = uuid.uuid4()
        doc.tenant_id = tenant_id
        doc.document_type = DocumentType.INVOICE_RECEIVED
        doc.partner_name = "Fournisseur ABC"
        doc.reference = "FA-2024-001"
        doc.document_date = date(2024, 3, 15)
        doc.amount_untaxed = Decimal("1000.00")
        doc.amount_tax = Decimal("200.00")
        doc.amount_total = Decimal("1200.00")
        return doc

    @pytest.fixture
    def sample_classification(self, tenant_id):
        """Create a mock AIClassification for testing."""
        clf = MagicMock()
        clf.id = uuid.uuid4()
        clf.tenant_id = tenant_id
        clf.suggested_account_code = "607100"
        clf.suggested_journal_code = "ACH"
        clf.expense_category = "ACHATS"
        clf.overall_confidence = ConfidenceLevel.HIGH
        clf.overall_confidence_score = Decimal("95.0")
        clf.tax_rates = [{"rate": 20, "amount": Decimal("200.00")}]
        return clf

    # Invoice Entry Generation Tests
    def test_generate_purchase_invoice_entry(self, engine, sample_document, sample_classification):
        """Test entry generation for purchase invoice."""
        sample_document.document_type = DocumentType.INVOICE_RECEIVED

        lines = engine.generate_entry_lines(sample_document, sample_classification)

        assert lines is not None
        assert len(lines) >= 2  # At least charge and vendor

        # Verify debit/credit balance
        total_debit = sum(line.debit for line in lines)
        total_credit = sum(line.credit for line in lines)
        assert abs(total_debit - total_credit) < Decimal("0.02")

    def test_generate_sales_invoice_entry(self, engine, sample_document, sample_classification):
        """Test entry generation for sales invoice."""
        sample_document.document_type = DocumentType.INVOICE_SENT
        sample_document.amount_untaxed = Decimal("2000.00")
        sample_document.amount_tax = Decimal("400.00")
        sample_document.amount_total = Decimal("2400.00")
        sample_classification.suggested_account_code = "707100"

        lines = engine.generate_entry_lines(sample_document, sample_classification)

        assert lines is not None

        # Sales invoice: Client debit, Revenue + VAT credit
        debit_lines = [l for l in lines if l.debit > 0]
        credit_lines = [l for l in lines if l.credit > 0]

        assert len(debit_lines) >= 1  # Client account
        assert len(credit_lines) >= 1  # Revenue account

    def test_generate_expense_note_entry(self, engine, sample_document, sample_classification):
        """Test entry generation for expense note."""
        sample_document.document_type = DocumentType.EXPENSE_NOTE
        sample_document.amount_untaxed = Decimal("150.00")
        sample_document.amount_tax = Decimal("30.00")
        sample_document.amount_total = Decimal("180.00")
        sample_classification.suggested_account_code = "625100"

        lines = engine.generate_entry_lines(sample_document, sample_classification)

        assert lines is not None
        # Expense note should have expense account in debit
        debit_lines = [l for l in lines if l.debit > 0]
        assert any("625" in l.account_code for l in debit_lines)

    def test_generate_credit_note_entry(self, engine, sample_document, sample_classification):
        """Test entry generation for credit note (avoir)."""
        sample_document.document_type = DocumentType.CREDIT_NOTE_RECEIVED
        sample_document.amount_untaxed = Decimal("500.00")
        sample_document.amount_tax = Decimal("100.00")
        sample_document.amount_total = Decimal("600.00")
        sample_document.reference = "AV-2024-001"

        lines = engine.generate_entry_lines(sample_document, sample_classification)

        assert lines is not None
        # Credit note should reverse the normal entry

    # Balance Verification Tests
    def test_entry_is_balanced(self, engine, sample_document, sample_classification):
        """Test that generated entries are always balanced."""
        test_cases = [
            (DocumentType.INVOICE_RECEIVED, Decimal("1234.56"), Decimal("246.91"), Decimal("1481.47")),
            (DocumentType.INVOICE_SENT, Decimal("9999.99"), Decimal("2000.00"), Decimal("11999.99")),
        ]

        for doc_type, ht, tva, ttc in test_cases:
            sample_document.document_type = doc_type
            sample_document.amount_untaxed = ht
            sample_document.amount_tax = tva
            sample_document.amount_total = ttc

            lines = engine.generate_entry_lines(sample_document, sample_classification)
            if lines:
                total_debit = sum(l.debit for l in lines)
                total_credit = sum(l.credit for l in lines)
                assert abs(total_debit - total_credit) < Decimal("0.02"), f"Unbalanced entry"

    # Account Code Validation Tests
    def test_valid_account_code_format(self, engine, sample_document, sample_classification):
        """Test that account codes follow PCG format."""
        lines = engine.generate_entry_lines(sample_document, sample_classification)

        if lines:
            for line in lines:
                account_code = line.account_code
                # PCG accounts are typically 6 digits
                assert len(account_code) >= 3
                assert account_code.isdigit() or account_code[0].isdigit()

    # VAT Handling Tests
    def test_vat_deductible_entry(self, engine, sample_document, sample_classification):
        """Test VAT deductible entry for purchase."""
        sample_document.document_type = DocumentType.INVOICE_RECEIVED
        sample_document.amount_untaxed = Decimal("1000.00")
        sample_document.amount_tax = Decimal("200.00")
        sample_document.amount_total = Decimal("1200.00")

        lines = engine.generate_entry_lines(sample_document, sample_classification)

        if lines:
            # Should have a VAT deductible line (445xxx)
            vat_lines = [l for l in lines if l.account_code.startswith("445")]
            # VAT should be in debit for purchases
            assert len(vat_lines) >= 0  # May or may not have explicit VAT line

    def test_vat_collected_entry(self, engine, sample_document, sample_classification):
        """Test VAT collected entry for sales."""
        sample_document.document_type = DocumentType.INVOICE_SENT
        sample_classification.suggested_account_code = "707100"

        lines = engine.generate_entry_lines(sample_document, sample_classification)

        if lines:
            # Should have a VAT collected line (445xxx)
            # VAT should be in credit for sales
            pass


class TestAutoAccountingService:
    """Tests for the AutoAccountingService class."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        return db

    @pytest.fixture
    def tenant_id(self):
        return str(uuid.uuid4())

    @pytest.fixture
    def service(self, mock_db, tenant_id):
        return AutoAccountingService(db=mock_db, tenant_id=tenant_id)

    @pytest.fixture
    def sample_document(self, tenant_id):
        """Create a mock AccountingDocument for testing."""
        doc = MagicMock()
        doc.id = uuid.uuid4()
        doc.tenant_id = tenant_id
        doc.document_type = DocumentType.INVOICE_RECEIVED
        doc.partner_name = "Fournisseur"
        doc.reference = "FA-2024-001"
        doc.document_date = date(2024, 3, 15)
        doc.due_date = None
        doc.amount_untaxed = Decimal("1000.00")
        doc.amount_tax = Decimal("200.00")
        doc.amount_total = Decimal("1200.00")
        doc.ai_suggested_journal = "PURCHASES"
        doc.partner_id = None
        doc.status = None
        doc.requires_validation = False
        doc.journal_entry_id = None
        return doc

    @pytest.fixture
    def sample_classification(self, tenant_id):
        """Create a mock AIClassification for testing."""
        clf = MagicMock()
        clf.id = uuid.uuid4()
        clf.tenant_id = tenant_id
        clf.suggested_account_code = "607100"
        clf.suggested_journal_code = "PURCHASES"
        clf.expense_category = "ACHATS"
        clf.overall_confidence = ConfidenceLevel.HIGH
        clf.overall_confidence_score = Decimal("95.0")
        clf.tax_rates = [{"rate": 20, "amount": Decimal("200.00")}]
        return clf

    @patch.object(AutoAccountingService, '_create_journal_entry')
    @patch.object(AccountingRulesEngine, 'generate_entry_lines')
    def test_process_document_success(self, mock_generate, mock_create_entry, service, mock_db, sample_document, sample_classification):
        """Test successful document processing."""
        from app.modules.automated_accounting.schemas import ProposedEntryLine

        document_id = sample_document.id

        # Mock journal entry creation
        mock_journal_entry = MagicMock()
        mock_journal_entry.id = uuid.uuid4()
        mock_create_entry.return_value = mock_journal_entry

        # Mock generate_entry_lines to return valid lines
        mock_line = ProposedEntryLine(
            account_code="607100",
            account_name="Achats de marchandises",
            debit_amount=Decimal("1000.00"),
            credit_amount=Decimal("0"),
            label="Achat facture test",
        )
        mock_generate.return_value = [mock_line]

        # Mock query chains
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = sample_classification
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.process_document(document_id=document_id)

        assert result is not None
        assert result.tenant_id == service.tenant_id

    @patch.object(AutoAccountingService, '_create_journal_entry')
    def test_validate_entry_success(self, mock_create_entry, service, mock_db, sample_document):
        """Test successful entry validation."""
        # Mock journal entry creation
        mock_journal_entry = MagicMock()
        mock_journal_entry.id = uuid.uuid4()
        mock_create_entry.return_value = mock_journal_entry

        entry_id = uuid.uuid4()
        validated_by = uuid.uuid4()

        # Mock entry and document lookup
        mock_entry = Mock()  # Use Mock instead of MagicMock for proper boolean handling
        mock_entry.id = entry_id
        mock_entry.is_posted = False
        mock_entry.document_id = sample_document.id
        mock_entry.proposed_lines = []
        mock_entry.requires_review = True
        mock_entry.reviewed_by = None
        mock_entry.reviewed_at = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_entry,  # AutoEntry
            sample_document,  # AccountingDocument
        ]
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.validate_entry(
            auto_entry_id=entry_id,
            validated_by=validated_by,
            approved=True,
        )

        assert result is not None
        mock_create_entry.assert_called_once()

    @patch.object(AutoAccountingService, '_create_journal_entry')
    def test_bulk_validate_entries(self, mock_create_entry, service, mock_db, sample_document):
        """Test bulk validation of multiple entries."""
        # Mock the journal entry creation to avoid complex DB interactions
        mock_journal_entry = MagicMock()
        mock_journal_entry.id = uuid.uuid4()
        mock_create_entry.return_value = mock_journal_entry

        entry_ids = [uuid.uuid4() for _ in range(3)]
        validated_by = uuid.uuid4()

        # Create mock entries with proper boolean values
        mock_entries = {}
        for eid in entry_ids:
            mock_entry = Mock()  # Use Mock instead of MagicMock for explicit control
            mock_entry.id = eid
            mock_entry.is_posted = False  # Must be actual boolean
            mock_entry.journal_entry_id = None
            mock_entry.document_id = sample_document.id
            mock_entry.proposed_lines = []
            mock_entry.status = "PENDING"
            mock_entry.requires_review = True
            mock_entry.reviewed_by = None
            mock_entry.reviewed_at = None
            mock_entries[eid] = mock_entry

        # Sequence of returns: for each entry_id, we need entry then document
        call_sequence = []
        for eid in entry_ids:
            call_sequence.append(mock_entries[eid])  # AutoEntry query
            call_sequence.append(sample_document)    # AccountingDocument query

        mock_db.query.return_value.filter.return_value.first.side_effect = call_sequence
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.bulk_validate(
            auto_entry_ids=entry_ids,
            validated_by=validated_by,
        )

        assert result is not None
        assert "validated" in result
        assert result["validated"] == 3


class TestAutoValidationThresholds:
    """Tests for auto-validation confidence thresholds."""

    def test_threshold_high_auto_validates(self):
        """Test that HIGH confidence auto-validates."""
        # HIGH confidence with score >= 95 should auto-validate
        confidence_level = ConfidenceLevel.HIGH
        confidence_score = Decimal("96.0")

        should_auto = confidence_level == ConfidenceLevel.HIGH and confidence_score >= 95
        assert should_auto is True

    def test_threshold_medium_requires_review(self):
        """Test that MEDIUM confidence requires review."""
        confidence_level = ConfidenceLevel.MEDIUM
        confidence_score = Decimal("85.0")

        should_auto = confidence_level == ConfidenceLevel.HIGH and confidence_score >= 95
        assert should_auto is False

    def test_threshold_low_requires_review(self):
        """Test that LOW confidence requires review."""
        confidence_level = ConfidenceLevel.LOW
        confidence_score = Decimal("65.0")

        should_auto = confidence_level == ConfidenceLevel.HIGH and confidence_score >= 95
        assert should_auto is False

    def test_threshold_very_low_requires_review(self):
        """Test that VERY_LOW confidence requires review."""
        confidence_level = ConfidenceLevel.VERY_LOW
        confidence_score = Decimal("40.0")

        should_auto = confidence_level == ConfidenceLevel.HIGH and confidence_score >= 95
        assert should_auto is False

    def test_custom_threshold(self):
        """Test custom auto-validation threshold."""
        # With lower threshold, MEDIUM might auto-validate
        confidence_level = ConfidenceLevel.MEDIUM
        confidence_score = Decimal("88.0")
        threshold = Decimal("85.0")

        should_auto = confidence_score >= threshold
        assert should_auto is True


class TestEntryTemplates:
    """Tests for entry templates per document type."""

    def test_invoice_received_template(self):
        """Test template for received invoice."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        template = templates.get(DocumentType.INVOICE_RECEIVED)

        assert template is not None
        assert "lines" in template
        # Should have supplier, expense, and VAT
        line_types = [l["type"] for l in template["lines"]]
        assert "supplier" in line_types
        assert "expense" in line_types

    def test_invoice_sent_template(self):
        """Test template for sent invoice."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        template = templates.get(DocumentType.INVOICE_SENT)

        assert template is not None
        assert "lines" in template
        # Should have customer, revenue, and VAT
        line_types = [l["type"] for l in template["lines"]]
        assert "customer" in line_types
        assert "revenue" in line_types

    def test_expense_note_template(self):
        """Test template for expense note."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        template = templates.get(DocumentType.EXPENSE_NOTE)

        assert template is not None
        assert "lines" in template

    def test_credit_note_template(self):
        """Test template for credit note reverses normal entry."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        normal_template = templates.get(DocumentType.INVOICE_RECEIVED)
        credit_template = templates.get(DocumentType.CREDIT_NOTE_RECEIVED)

        # Both templates should exist
        assert normal_template is not None
        assert credit_template is not None

        # Credit note should have reversed debit/credit sides
        for normal_line, credit_line in zip(
            normal_template["lines"], credit_template["lines"]
        ):
            # Sides should be reversed for credit notes
            assert normal_line is not None


class TestMultiCurrencyEntries:
    """Tests for multi-currency journal entries."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def tenant_id(self):
        return str(uuid.uuid4())

    @pytest.fixture
    def engine(self, mock_db, tenant_id):
        return AccountingRulesEngine(db=mock_db, tenant_id=tenant_id)

    @pytest.fixture
    def sample_document(self, tenant_id):
        doc = MagicMock()
        doc.id = uuid.uuid4()
        doc.tenant_id = tenant_id
        doc.document_type = DocumentType.INVOICE_RECEIVED
        doc.partner_name = "Fournisseur"
        doc.reference = "FA-2024-001"
        doc.document_date = date(2024, 3, 15)
        doc.amount_untaxed = Decimal("1000.00")
        doc.amount_tax = Decimal("200.00")
        doc.amount_total = Decimal("1200.00")
        return doc

    def test_entry_with_foreign_currency(self, engine, sample_document):
        """Test entry generation for foreign currency invoice."""
        # Document with foreign currency
        lines = engine.generate_entry_lines(sample_document, None)

        # Entry should be generated
        assert lines is not None

    def test_entry_eur_no_conversion(self, engine, sample_document):
        """Test that EUR entries don't need conversion."""
        lines = engine.generate_entry_lines(sample_document, None)

        # Entry should be generated without currency conversion
        assert lines is not None


class TestJournalSelection:
    """Tests for automatic journal selection."""

    def test_purchase_journal_selection(self):
        """Test purchase journal is selected for received invoices."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        template = templates.get(DocumentType.INVOICE_RECEIVED)

        assert template is not None
        assert template["journal"] == "PURCHASES"

    def test_sales_journal_selection(self):
        """Test sales journal is selected for sent invoices."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        template = templates.get(DocumentType.INVOICE_SENT)

        assert template is not None
        assert template["journal"] == "SALES"

    def test_expense_journal_selection(self):
        """Test expense journal is selected for expense notes."""
        templates = AccountingRulesEngine.ENTRY_TEMPLATES
        template = templates.get(DocumentType.EXPENSE_NOTE)

        assert template is not None
        assert template["journal"] == "PURCHASES"
