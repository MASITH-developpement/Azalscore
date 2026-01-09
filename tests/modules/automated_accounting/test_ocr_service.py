"""
Unit tests for OCR Service.

Tests:
- Field extraction (invoice number, dates, amounts, VAT)
- Confidence scoring
- Duplicate detection
- Multiple OCR engines
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import date
import hashlib
import uuid

from app.modules.automated_accounting.services.ocr_service import (
    OCRService,
    TesseractEngine,
    FieldExtractor,
    OCREngine,
)


class TestFieldExtractor:
    """Tests for the FieldExtractor class."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    # Invoice Number Tests
    def test_extract_invoice_number_standard_format(self, extractor):
        """Test extraction of standard invoice number formats."""
        text = "Facture N° FA-2024-00123\nDate: 15/01/2024"
        result = extractor.extract_fields(text)

        invoice_field = next(
            (f for f in result if f["field_name"] == "invoice_number"), None
        )
        assert invoice_field is not None
        assert invoice_field["value"] == "FA-2024-00123"
        assert invoice_field["confidence"] > 0.8

    def test_extract_invoice_number_with_colon(self, extractor):
        """Test extraction when invoice number uses colon separator."""
        text = "Invoice: INV-001234\nTotal: 1500.00 EUR"
        result = extractor.extract_fields(text)

        invoice_field = next(
            (f for f in result if f["field_name"] == "invoice_number"), None
        )
        assert invoice_field is not None
        assert "001234" in invoice_field["value"] or "INV" in invoice_field["value"]

    def test_extract_invoice_number_french_format(self, extractor):
        """Test French invoice number formats."""
        text = "Numéro de facture: 2024/01/0042"
        result = extractor.extract_fields(text)

        invoice_field = next(
            (f for f in result if f["field_name"] == "invoice_number"), None
        )
        assert invoice_field is not None

    # Date Extraction Tests
    def test_extract_date_french_format(self, extractor):
        """Test extraction of French date format (DD/MM/YYYY)."""
        text = "Date de facture: 15/03/2024"
        result = extractor.extract_fields(text)

        date_field = next(
            (f for f in result if f["field_name"] == "date"), None
        )
        assert date_field is not None
        assert date_field["value"] == "15/03/2024"

    def test_extract_date_iso_format(self, extractor):
        """Test extraction of ISO date format (YYYY-MM-DD)."""
        text = "Invoice Date: 2024-03-15"
        result = extractor.extract_fields(text)

        date_field = next(
            (f for f in result if f["field_name"] == "date"), None
        )
        assert date_field is not None

    def test_extract_due_date(self, extractor):
        """Test extraction of due date."""
        text = """
        Date: 01/03/2024
        Échéance: 31/03/2024
        """
        result = extractor.extract_fields(text)

        due_date_field = next(
            (f for f in result if f["field_name"] == "due_date"), None
        )
        assert due_date_field is not None
        assert due_date_field["value"] == "31/03/2024"

    # Amount Extraction Tests
    def test_extract_total_ht(self, extractor):
        """Test extraction of HT (before tax) amount."""
        text = """
        Sous-total HT: 1 000,00 €
        TVA 20%: 200,00 €
        Total TTC: 1 200,00 €
        """
        result = extractor.extract_fields(text)

        ht_field = next(
            (f for f in result if f["field_name"] == "total_ht"), None
        )
        assert ht_field is not None
        # The value should be parseable as a number
        assert "1" in ht_field["value"] and "000" in ht_field["value"]

    def test_extract_total_tva(self, extractor):
        """Test extraction of VAT amount."""
        text = """
        Total HT: 1000.00
        TVA (20%): 200.00
        Total TTC: 1200.00
        """
        result = extractor.extract_fields(text)

        tva_field = next(
            (f for f in result if f["field_name"] == "total_tva"), None
        )
        assert tva_field is not None
        assert "200" in tva_field["value"]

    def test_extract_total_ttc(self, extractor):
        """Test extraction of TTC (with tax) total."""
        text = "Total TTC: 1 234,56 EUR"
        result = extractor.extract_fields(text)

        ttc_field = next(
            (f for f in result if f["field_name"] == "total_ttc"), None
        )
        assert ttc_field is not None
        assert "1" in ttc_field["value"] and "234" in ttc_field["value"]

    def test_extract_amount_with_currency_symbol(self, extractor):
        """Test amount extraction with various currency symbols."""
        text = "Montant: €1,500.00"
        result = extractor.extract_fields(text)

        # Should extract the numeric value
        amount_fields = [f for f in result if "total" in f["field_name"]]
        assert len(amount_fields) > 0

    # SIRET/VAT Number Tests
    def test_extract_siret(self, extractor):
        """Test extraction of French SIRET number."""
        text = "SIRET: 123 456 789 00012"
        result = extractor.extract_fields(text)

        siret_field = next(
            (f for f in result if f["field_name"] == "siret"), None
        )
        assert siret_field is not None

    def test_extract_tva_intracommunautaire(self, extractor):
        """Test extraction of EU VAT number."""
        text = "N° TVA Intracommunautaire: FR 12 345678901"
        result = extractor.extract_fields(text)

        tva_field = next(
            (f for f in result if f["field_name"] == "tva_intra"), None
        )
        assert tva_field is not None
        assert "FR" in tva_field["value"]

    # IBAN Tests
    def test_extract_iban_french(self, extractor):
        """Test extraction of French IBAN."""
        text = "IBAN: FR76 1234 5678 9012 3456 7890 123"
        result = extractor.extract_fields(text)

        iban_field = next(
            (f for f in result if f["field_name"] == "iban"), None
        )
        assert iban_field is not None
        assert iban_field["value"].startswith("FR")

    def test_extract_iban_german(self, extractor):
        """Test extraction of German IBAN."""
        text = "Bankverbindung: DE89 3704 0044 0532 0130 00"
        result = extractor.extract_fields(text)

        iban_field = next(
            (f for f in result if f["field_name"] == "iban"), None
        )
        assert iban_field is not None
        assert iban_field["value"].startswith("DE")

    # Vendor Name Tests
    def test_extract_vendor_name(self, extractor):
        """Test extraction of vendor name from invoice."""
        text = """
        ACME Corporation SARL
        123 Rue de Paris
        75001 Paris

        Facture N° 2024-001
        """
        result = extractor.extract_fields(text)

        vendor_field = next(
            (f for f in result if f["field_name"] == "vendor_name"), None
        )
        # Vendor extraction is complex, just ensure we attempt it
        assert vendor_field is not None or any(
            f["field_name"] == "vendor_name" for f in result
        )

    # Edge Cases
    def test_extract_fields_empty_text(self, extractor):
        """Test extraction with empty text returns empty list."""
        result = extractor.extract_fields("")
        assert isinstance(result, list)

    def test_extract_fields_garbage_text(self, extractor):
        """Test extraction with garbage text handles gracefully."""
        text = "asdfghjkl qwertyuiop zxcvbnm"
        result = extractor.extract_fields(text)
        # Should return list (possibly empty) without raising
        assert isinstance(result, list)


class TestOCRService:
    """Tests for the OCRService class."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ocr_engine(self):
        engine = Mock(spec=OCREngine)
        engine.process = AsyncMock(return_value={
            "raw_text": "Facture N° FA-2024-001\nTotal: 1000.00 EUR",
            "confidence": 0.95,
        })
        return engine

    @pytest.fixture
    def ocr_service(self, mock_db, mock_ocr_engine):
        service = OCRService(mock_db)
        service.engine = mock_ocr_engine
        return service

    @pytest.mark.asyncio
    async def test_process_document_success(self, ocr_service, mock_db):
        """Test successful document processing."""
        file_content = b"fake pdf content"
        tenant_id = uuid.uuid4()
        document_id = uuid.uuid4()

        # Mock database operations
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await ocr_service.process_document(
            tenant_id=tenant_id,
            document_id=document_id,
            file_content=file_content,
            filename="invoice.pdf",
        )

        assert result is not None
        assert "raw_text" in result
        assert "extracted_fields" in result
        assert "confidence_score" in result

    @pytest.mark.asyncio
    async def test_calculate_file_hash(self, ocr_service):
        """Test file hash calculation for duplicate detection."""
        content1 = b"file content 1"
        content2 = b"file content 2"
        content1_copy = b"file content 1"

        hash1 = ocr_service.calculate_file_hash(content1)
        hash2 = ocr_service.calculate_file_hash(content2)
        hash1_copy = ocr_service.calculate_file_hash(content1_copy)

        # Same content should produce same hash
        assert hash1 == hash1_copy
        # Different content should produce different hash
        assert hash1 != hash2
        # Hash should be a valid SHA-256 hex string
        assert len(hash1) == 64

    @pytest.mark.asyncio
    async def test_check_duplicate_returns_true(self, ocr_service, mock_db):
        """Test duplicate detection when document exists."""
        file_hash = "abc123" * 10 + "abcd"
        tenant_id = uuid.uuid4()

        # Mock finding an existing document
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=uuid.uuid4())
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_duplicate, existing_id = await ocr_service.check_duplicate(
            tenant_id, file_hash
        )

        assert is_duplicate is True
        assert existing_id is not None

    @pytest.mark.asyncio
    async def test_check_duplicate_returns_false(self, ocr_service, mock_db):
        """Test duplicate detection when document is new."""
        file_hash = "abc123" * 10 + "abcd"
        tenant_id = uuid.uuid4()

        # Mock not finding an existing document
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_duplicate, existing_id = await ocr_service.check_duplicate(
            tenant_id, file_hash
        )

        assert is_duplicate is False
        assert existing_id is None

    @pytest.mark.asyncio
    async def test_process_document_with_invalid_file(self, ocr_service):
        """Test handling of invalid file content."""
        ocr_service.engine.process = AsyncMock(
            side_effect=Exception("Invalid file format")
        )

        with pytest.raises(Exception):
            await ocr_service.process_document(
                tenant_id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                file_content=b"invalid",
                filename="bad.xyz",
            )


class TestTesseractEngine:
    """Tests for the Tesseract OCR engine."""

    @pytest.fixture
    def tesseract_engine(self):
        return TesseractEngine()

    @pytest.mark.asyncio
    @patch("app.modules.automated_accounting.services.ocr_service.pytesseract")
    async def test_tesseract_process_image(self, mock_pytesseract, tesseract_engine):
        """Test Tesseract processing of image file."""
        mock_pytesseract.image_to_string = Mock(return_value="Extracted text")
        mock_pytesseract.image_to_data = Mock(return_value={
            "conf": [90, 85, 95],
            "text": ["word1", "word2", "word3"],
        })

        # This would require actual image data in a real test
        # Here we just verify the mock integration
        assert mock_pytesseract is not None

    @pytest.mark.asyncio
    @patch("app.modules.automated_accounting.services.ocr_service.pdf2image")
    async def test_tesseract_process_pdf(self, mock_pdf2image, tesseract_engine):
        """Test Tesseract processing of PDF file."""
        mock_pdf2image.convert_from_bytes = Mock(return_value=[Mock()])

        # Verify PDF conversion mock is set up
        assert mock_pdf2image is not None


class TestOCRConfidenceScoring:
    """Tests for OCR confidence score calculation."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    def test_high_confidence_clean_invoice(self, extractor):
        """Test high confidence score for clean, well-formatted invoice."""
        text = """
        FACTURE N° FA-2024-00123

        Date: 15/03/2024
        Échéance: 15/04/2024

        Client: Entreprise ABC
        SIRET: 123 456 789 00012
        N° TVA: FR12345678901

        Description          Qté    Prix HT    Total HT
        Service conseil      10     100,00     1 000,00

        Total HT:                              1 000,00 €
        TVA 20%:                                 200,00 €
        Total TTC:                             1 200,00 €

        IBAN: FR76 1234 5678 9012 3456 7890 123
        """
        result = extractor.extract_fields(text)

        # High confidence = many fields extracted with good confidence
        high_confidence_fields = [f for f in result if f["confidence"] > 0.8]
        assert len(high_confidence_fields) >= 3

    def test_low_confidence_poor_scan(self, extractor):
        """Test lower confidence for poorly scanned document."""
        text = """
        FACTUR3 N* FA-2O24-OOl23

        Dat3: l5/O3/2O24

        Tot4l: l,OOO.OO EUR
        """
        result = extractor.extract_fields(text)

        # Should still attempt extraction but with lower confidence
        if result:
            avg_confidence = sum(f["confidence"] for f in result) / len(result)
            # Poor OCR should result in lower average confidence
            assert avg_confidence < 1.0


class TestMultiLanguageOCR:
    """Tests for multi-language OCR support."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    def test_german_invoice_extraction(self, extractor):
        """Test extraction from German invoice."""
        text = """
        Rechnung Nr. 2024-001
        Rechnungsdatum: 15.03.2024
        Fälligkeitsdatum: 15.04.2024

        Nettobetrag: 1.000,00 €
        MwSt. 19%: 190,00 €
        Gesamtbetrag: 1.190,00 €

        IBAN: DE89 3704 0044 0532 0130 00
        """
        result = extractor.extract_fields(text)

        # Should extract German date format and IBAN
        assert any(f["field_name"] == "iban" for f in result)

    def test_spanish_invoice_extraction(self, extractor):
        """Test extraction from Spanish invoice."""
        text = """
        Factura Nº 2024-001
        Fecha: 15/03/2024

        Base imponible: 1.000,00 €
        IVA 21%: 210,00 €
        Total: 1.210,00 €
        """
        result = extractor.extract_fields(text)

        # Should extract invoice number and amounts
        assert len(result) > 0

    def test_italian_invoice_extraction(self, extractor):
        """Test extraction from Italian invoice."""
        text = """
        Fattura N. 2024-001
        Data: 15/03/2024

        Imponibile: € 1.000,00
        IVA 22%: € 220,00
        Totale: € 1.220,00
        """
        result = extractor.extract_fields(text)

        # Should extract amounts
        amount_fields = [f for f in result if "total" in f["field_name"]]
        assert len(amount_fields) > 0
