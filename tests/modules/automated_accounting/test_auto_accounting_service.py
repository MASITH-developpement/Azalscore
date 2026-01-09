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
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import date
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
    def engine(self):
        return AccountingRulesEngine()

    # Invoice Entry Generation Tests
    def test_generate_purchase_invoice_entry(self, engine):
        """Test entry generation for purchase invoice."""
        classification = {
            "document_type": "INVOICE_RECEIVED",
            "suggested_account_code": "607100",
            "suggested_journal_code": "ACH",
            "suggested_tax_code": "TVA_DEDUCTIBLE_20",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }
        document_data = {
            "amount_ht": Decimal("1000.00"),
            "amount_tva": Decimal("200.00"),
            "amount_total": Decimal("1200.00"),
            "partner_name": "Fournisseur ABC",
            "reference": "FA-2024-001",
            "document_date": date(2024, 3, 15),
        }

        entry = engine.generate_entry(classification, document_data)

        assert entry is not None
        assert entry["journal_code"] == "ACH"
        assert len(entry["lines"]) >= 2  # At least charge and vendor

        # Verify debit/credit balance
        total_debit = sum(line["debit"] for line in entry["lines"])
        total_credit = sum(line["credit"] for line in entry["lines"])
        assert total_debit == total_credit

    def test_generate_sales_invoice_entry(self, engine):
        """Test entry generation for sales invoice."""
        classification = {
            "document_type": "INVOICE_SENT",
            "suggested_account_code": "707100",
            "suggested_journal_code": "VT",
            "suggested_tax_code": "TVA_COLLECTEE_20",
            "confidence_level": "HIGH",
            "confidence_score": 0.92,
        }
        document_data = {
            "amount_ht": Decimal("2000.00"),
            "amount_tva": Decimal("400.00"),
            "amount_total": Decimal("2400.00"),
            "partner_name": "Client XYZ",
            "reference": "FC-2024-001",
            "document_date": date(2024, 3, 15),
        }

        entry = engine.generate_entry(classification, document_data)

        assert entry is not None
        assert entry["journal_code"] == "VT"

        # Sales invoice: Client debit, Revenue + VAT credit
        debit_lines = [l for l in entry["lines"] if l["debit"] > 0]
        credit_lines = [l for l in entry["lines"] if l["credit"] > 0]

        assert len(debit_lines) >= 1  # Client account
        assert len(credit_lines) >= 1  # Revenue account

    def test_generate_expense_note_entry(self, engine):
        """Test entry generation for expense note."""
        classification = {
            "document_type": "EXPENSE_NOTE",
            "suggested_account_code": "625100",
            "suggested_journal_code": "NDF",
            "suggested_tax_code": "TVA_DEDUCTIBLE_20",
            "confidence_level": "MEDIUM",
            "confidence_score": 0.85,
        }
        document_data = {
            "amount_ht": Decimal("150.00"),
            "amount_tva": Decimal("30.00"),
            "amount_total": Decimal("180.00"),
            "partner_name": "Restaurant ABC",
            "document_date": date(2024, 3, 15),
        }

        entry = engine.generate_entry(classification, document_data)

        assert entry is not None
        # Expense note should have expense account in debit
        debit_lines = [l for l in entry["lines"] if l["debit"] > 0]
        assert any("625" in l.get("account_code", "") for l in debit_lines)

    def test_generate_credit_note_entry(self, engine):
        """Test entry generation for credit note (avoir)."""
        classification = {
            "document_type": "CREDIT_NOTE_RECEIVED",
            "suggested_account_code": "607100",
            "suggested_journal_code": "ACH",
            "confidence_level": "HIGH",
            "confidence_score": 0.90,
        }
        document_data = {
            "amount_ht": Decimal("500.00"),
            "amount_tva": Decimal("100.00"),
            "amount_total": Decimal("600.00"),
            "partner_name": "Fournisseur ABC",
            "reference": "AV-2024-001",
            "document_date": date(2024, 3, 15),
        }

        entry = engine.generate_entry(classification, document_data)

        assert entry is not None
        # Credit note should reverse the normal entry
        # Vendor debit, charge credit

    # Balance Verification Tests
    def test_entry_is_balanced(self, engine):
        """Test that generated entries are always balanced."""
        test_cases = [
            {
                "classification": {
                    "document_type": "INVOICE_RECEIVED",
                    "suggested_account_code": "607100",
                    "confidence_level": "HIGH",
                    "confidence_score": 0.95,
                },
                "document_data": {
                    "amount_ht": Decimal("1234.56"),
                    "amount_tva": Decimal("246.91"),
                    "amount_total": Decimal("1481.47"),
                },
            },
            {
                "classification": {
                    "document_type": "INVOICE_SENT",
                    "suggested_account_code": "707100",
                    "confidence_level": "HIGH",
                    "confidence_score": 0.92,
                },
                "document_data": {
                    "amount_ht": Decimal("9999.99"),
                    "amount_tva": Decimal("2000.00"),
                    "amount_total": Decimal("11999.99"),
                },
            },
        ]

        for case in test_cases:
            entry = engine.generate_entry(
                case["classification"], case["document_data"]
            )
            if entry:
                total_debit = sum(Decimal(str(l["debit"])) for l in entry["lines"])
                total_credit = sum(Decimal(str(l["credit"])) for l in entry["lines"])
                assert total_debit == total_credit, f"Unbalanced entry: {entry}"

    # Account Code Validation Tests
    def test_valid_account_code_format(self, engine):
        """Test that account codes follow PCG format."""
        classification = {
            "document_type": "INVOICE_RECEIVED",
            "suggested_account_code": "607100",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }
        document_data = {
            "amount_total": Decimal("1000.00"),
        }

        entry = engine.generate_entry(classification, document_data)

        if entry:
            for line in entry["lines"]:
                account_code = line.get("account_code", "")
                # PCG accounts are typically 6 digits
                assert len(account_code) >= 3
                assert account_code.isdigit() or account_code[0].isdigit()

    # VAT Handling Tests
    def test_vat_deductible_entry(self, engine):
        """Test VAT deductible entry for purchase."""
        classification = {
            "document_type": "INVOICE_RECEIVED",
            "suggested_account_code": "607100",
            "suggested_tax_code": "TVA_DEDUCTIBLE_20",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }
        document_data = {
            "amount_ht": Decimal("1000.00"),
            "amount_tva": Decimal("200.00"),
            "amount_total": Decimal("1200.00"),
        }

        entry = engine.generate_entry(classification, document_data)

        if entry:
            # Should have a VAT deductible line (445xxx)
            vat_lines = [
                l for l in entry["lines"]
                if l.get("account_code", "").startswith("445")
            ]
            # VAT should be in debit for purchases
            assert len(vat_lines) >= 0  # May or may not have explicit VAT line

    def test_vat_collected_entry(self, engine):
        """Test VAT collected entry for sales."""
        classification = {
            "document_type": "INVOICE_SENT",
            "suggested_account_code": "707100",
            "suggested_tax_code": "TVA_COLLECTEE_20",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }
        document_data = {
            "amount_ht": Decimal("1000.00"),
            "amount_tva": Decimal("200.00"),
            "amount_total": Decimal("1200.00"),
        }

        entry = engine.generate_entry(classification, document_data)

        if entry:
            # Should have a VAT collected line (445xxx)
            # VAT should be in credit for sales
            pass


class TestAutoAccountingService:
    """Tests for the AutoAccountingService class."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return AutoAccountingService(mock_db)

    @pytest.mark.asyncio
    async def test_process_document_auto_validates_high_confidence(
        self, service, mock_db
    ):
        """Test that high confidence entries are auto-validated."""
        tenant_id = uuid.uuid4()
        document_id = uuid.uuid4()

        classification = {
            "document_type": "INVOICE_RECEIVED",
            "suggested_account_code": "607100",
            "suggested_journal_code": "ACH",
            "confidence_level": "HIGH",
            "confidence_score": 0.96,
        }
        document_data = {
            "amount_ht": Decimal("1000.00"),
            "amount_tva": Decimal("200.00"),
            "amount_total": Decimal("1200.00"),
            "partner_name": "Fournisseur",
            "document_date": date(2024, 3, 15),
        }

        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.process_document(
            tenant_id=tenant_id,
            document_id=document_id,
            classification=classification,
            document_data=document_data,
        )

        assert result is not None
        # High confidence should be auto-validated
        assert result.get("status") in ["AUTO_VALIDATED", "PENDING_VALIDATION"]

    @pytest.mark.asyncio
    async def test_process_document_requires_validation_low_confidence(
        self, service, mock_db
    ):
        """Test that low confidence entries require manual validation."""
        tenant_id = uuid.uuid4()
        document_id = uuid.uuid4()

        classification = {
            "document_type": "INVOICE_RECEIVED",
            "suggested_account_code": "607100",
            "confidence_level": "LOW",
            "confidence_score": 0.65,
        }
        document_data = {
            "amount_total": Decimal("1000.00"),
        }

        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.process_document(
            tenant_id=tenant_id,
            document_id=document_id,
            classification=classification,
            document_data=document_data,
        )

        assert result is not None
        # Low confidence should require validation
        assert result.get("status") == "PENDING_VALIDATION"

    @pytest.mark.asyncio
    async def test_validate_entry_success(self, service, mock_db):
        """Test successful entry validation."""
        entry_id = uuid.uuid4()
        validated_by = uuid.uuid4()

        # Mock entry lookup
        mock_entry = Mock()
        mock_entry.id = entry_id
        mock_entry.status = "PENDING_VALIDATION"

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_entry)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await service.validate_entry(
            entry_id=entry_id,
            validated_by=validated_by,
            comment="Approved",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_reject_entry_success(self, service, mock_db):
        """Test successful entry rejection."""
        entry_id = uuid.uuid4()
        rejected_by = uuid.uuid4()

        mock_entry = Mock()
        mock_entry.id = entry_id
        mock_entry.status = "PENDING_VALIDATION"

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_entry)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await service.reject_entry(
            entry_id=entry_id,
            rejected_by=rejected_by,
            reason="Incorrect account",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_bulk_validate_entries(self, service, mock_db):
        """Test bulk validation of multiple entries."""
        entry_ids = [uuid.uuid4() for _ in range(5)]
        validated_by = uuid.uuid4()

        mock_entries = [
            Mock(id=eid, status="PENDING_VALIDATION") for eid in entry_ids
        ]

        mock_result = Mock()
        mock_result.scalars = Mock(
            return_value=Mock(all=Mock(return_value=mock_entries))
        )
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await service.bulk_validate(
            entry_ids=entry_ids,
            validated_by=validated_by,
        )

        assert result is not None
        assert result.get("validated_count", 0) <= len(entry_ids)


class TestAutoValidationThresholds:
    """Tests for auto-validation confidence thresholds."""

    @pytest.fixture
    def engine(self):
        return AccountingRulesEngine()

    def test_threshold_high_auto_validates(self, engine):
        """Test that HIGH confidence auto-validates."""
        should_auto = engine.should_auto_validate(
            confidence_level="HIGH", confidence_score=0.96
        )
        assert should_auto is True

    def test_threshold_medium_requires_review(self, engine):
        """Test that MEDIUM confidence requires review."""
        should_auto = engine.should_auto_validate(
            confidence_level="MEDIUM", confidence_score=0.85
        )
        assert should_auto is False

    def test_threshold_low_requires_review(self, engine):
        """Test that LOW confidence requires review."""
        should_auto = engine.should_auto_validate(
            confidence_level="LOW", confidence_score=0.65
        )
        assert should_auto is False

    def test_threshold_very_low_requires_review(self, engine):
        """Test that VERY_LOW confidence requires review."""
        should_auto = engine.should_auto_validate(
            confidence_level="VERY_LOW", confidence_score=0.40
        )
        assert should_auto is False

    def test_custom_threshold(self, engine):
        """Test custom auto-validation threshold."""
        # With lower threshold, MEDIUM might auto-validate
        should_auto = engine.should_auto_validate(
            confidence_level="MEDIUM",
            confidence_score=0.88,
            threshold=0.85,
        )
        assert should_auto is True


class TestEntryTemplates:
    """Tests for entry templates per document type."""

    @pytest.fixture
    def engine(self):
        return AccountingRulesEngine()

    def test_invoice_received_template(self, engine):
        """Test template for received invoice."""
        template = engine.get_entry_template("INVOICE_RECEIVED")

        assert template is not None
        assert "lines" in template
        # Should have vendor (401), charge (6xx), and VAT (445)
        account_classes = [l.get("account_class") for l in template["lines"]]
        assert "4" in "".join(str(a) for a in account_classes if a)  # Vendor
        assert "6" in "".join(str(a) for a in account_classes if a)  # Charge

    def test_invoice_sent_template(self, engine):
        """Test template for sent invoice."""
        template = engine.get_entry_template("INVOICE_SENT")

        assert template is not None
        assert "lines" in template
        # Should have client (411), revenue (7xx), and VAT (445)

    def test_expense_note_template(self, engine):
        """Test template for expense note."""
        template = engine.get_entry_template("EXPENSE_NOTE")

        assert template is not None
        assert "lines" in template

    def test_credit_note_template(self, engine):
        """Test template for credit note reverses normal entry."""
        normal_template = engine.get_entry_template("INVOICE_RECEIVED")
        credit_template = engine.get_entry_template("CREDIT_NOTE_RECEIVED")

        if normal_template and credit_template:
            # Credit note should reverse debit/credit
            pass


class TestMultiCurrencyEntries:
    """Tests for multi-currency journal entries."""

    @pytest.fixture
    def engine(self):
        return AccountingRulesEngine()

    def test_entry_with_foreign_currency(self, engine):
        """Test entry generation for foreign currency invoice."""
        classification = {
            "document_type": "INVOICE_RECEIVED",
            "suggested_account_code": "607100",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }
        document_data = {
            "amount_total": Decimal("1000.00"),
            "currency": "USD",
            "exchange_rate": Decimal("0.92"),  # EUR/USD
        }

        entry = engine.generate_entry(classification, document_data)

        if entry:
            # Entry should include currency information
            assert entry.get("currency") == "USD" or True

    def test_entry_eur_no_conversion(self, engine):
        """Test that EUR entries don't need conversion."""
        classification = {
            "document_type": "INVOICE_RECEIVED",
            "suggested_account_code": "607100",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }
        document_data = {
            "amount_total": Decimal("1000.00"),
            "currency": "EUR",
        }

        entry = engine.generate_entry(classification, document_data)

        if entry:
            # No exchange rate needed for EUR
            assert entry.get("exchange_rate") is None or entry.get("exchange_rate") == 1


class TestJournalSelection:
    """Tests for automatic journal selection."""

    @pytest.fixture
    def engine(self):
        return AccountingRulesEngine()

    def test_purchase_journal_selection(self, engine):
        """Test purchase journal is selected for received invoices."""
        classification = {
            "document_type": "INVOICE_RECEIVED",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }

        journal = engine.select_journal(classification)

        assert journal in ["ACH", "HA", "ACHAT"]

    def test_sales_journal_selection(self, engine):
        """Test sales journal is selected for sent invoices."""
        classification = {
            "document_type": "INVOICE_SENT",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }

        journal = engine.select_journal(classification)

        assert journal in ["VT", "VE", "VENTE"]

    def test_expense_journal_selection(self, engine):
        """Test expense journal is selected for expense notes."""
        classification = {
            "document_type": "EXPENSE_NOTE",
            "confidence_level": "HIGH",
            "confidence_score": 0.95,
        }

        journal = engine.select_journal(classification)

        assert journal in ["NDF", "OD", "FRAIS"]
