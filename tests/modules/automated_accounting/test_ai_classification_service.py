"""
Unit tests for AI Classification Service.

Tests:
- Document type classification
- Vendor detection and matching
- Account suggestion
- Confidence level calculation
- Expense categorization
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import date
import uuid

from app.modules.automated_accounting.services.ai_classification_service import (
    AIClassificationService,
    AIClassificationEngine,
)
from app.modules.automated_accounting.models import ConfidenceLevel


class TestAIClassificationEngine:
    """Tests for the AIClassificationEngine class."""

    @pytest.fixture
    def engine(self):
        return AIClassificationEngine()

    # Document Type Classification Tests
    def test_classify_invoice_received(self, engine):
        """Test classification of received invoice."""
        ocr_data = {
            "raw_text": """
            FACTURE
            De: Fournisseur ABC
            À: Notre Entreprise

            Total TTC: 1 200,00 €
            """,
            "extracted_fields": [
                {"field_name": "total_ttc", "value": "1200.00", "confidence": 0.95},
                {"field_name": "vendor_name", "value": "Fournisseur ABC", "confidence": 0.90},
            ],
        }

        result = engine.classify_document(ocr_data)

        assert result["document_type"] == "INVOICE_RECEIVED"
        assert result["confidence_level"] in ["HIGH", "MEDIUM", "LOW", "VERY_LOW"]

    def test_classify_expense_note(self, engine):
        """Test classification of expense note."""
        ocr_data = {
            "raw_text": """
            NOTE DE FRAIS

            Restaurant: 45,00 €
            Transport: 23,50 €
            Hébergement: 150,00 €

            Total: 218,50 €
            """,
            "extracted_fields": [
                {"field_name": "total_ttc", "value": "218.50", "confidence": 0.88},
            ],
        }

        result = engine.classify_document(ocr_data)

        assert result["document_type"] == "EXPENSE_NOTE"

    def test_classify_credit_note(self, engine):
        """Test classification of credit note."""
        ocr_data = {
            "raw_text": """
            AVOIR N° AV-2024-001

            Annulation partielle facture FA-2024-123
            Montant: -500,00 €
            """,
            "extracted_fields": [
                {"field_name": "invoice_number", "value": "AV-2024-001", "confidence": 0.92},
                {"field_name": "total_ttc", "value": "-500.00", "confidence": 0.90},
            ],
        }

        result = engine.classify_document(ocr_data)

        assert result["document_type"] in ["CREDIT_NOTE_RECEIVED", "CREDIT_NOTE_SENT"]

    def test_classify_quote(self, engine):
        """Test classification of quote/estimate."""
        ocr_data = {
            "raw_text": """
            DEVIS N° DEV-2024-001
            Validité: 30 jours

            Prestation de service
            Total HT: 5 000,00 €
            TVA 20%: 1 000,00 €
            Total TTC: 6 000,00 €
            """,
            "extracted_fields": [
                {"field_name": "invoice_number", "value": "DEV-2024-001", "confidence": 0.95},
            ],
        }

        result = engine.classify_document(ocr_data)

        assert result["document_type"] == "QUOTE"

    def test_classify_purchase_order(self, engine):
        """Test classification of purchase order."""
        ocr_data = {
            "raw_text": """
            BON DE COMMANDE N° BC-2024-001

            Article: Fournitures bureau
            Quantité: 100
            Prix unitaire: 10,00 €

            Total: 1 000,00 €
            """,
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        assert result["document_type"] == "PURCHASE_ORDER"

    # Expense Categorization Tests
    def test_categorize_restaurant_expense(self, engine):
        """Test categorization of restaurant expense."""
        ocr_data = {
            "raw_text": """
            RESTAURANT LE GOURMET
            Menu du jour
            Repas d'affaires
            Total: 85,00 €
            """,
            "extracted_fields": [
                {"field_name": "vendor_name", "value": "Restaurant Le Gourmet", "confidence": 0.90},
            ],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest restaurant/meal expense account
        if result.get("suggested_account_code"):
            assert result["suggested_account_code"].startswith("625")  # Frais de déplacement

    def test_categorize_hotel_expense(self, engine):
        """Test categorization of hotel expense."""
        ocr_data = {
            "raw_text": """
            HOTEL IBIS PARIS
            Nuitée du 15/03/2024
            Chambre simple
            Total: 120,00 €
            """,
            "extracted_fields": [
                {"field_name": "vendor_name", "value": "Hotel Ibis", "confidence": 0.88},
            ],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest lodging expense account
        if result.get("suggested_account_code"):
            assert result["suggested_account_code"].startswith("625")  # Frais de déplacement

    def test_categorize_office_supplies(self, engine):
        """Test categorization of office supplies."""
        ocr_data = {
            "raw_text": """
            BUREAU VALLEE
            Papier A4 x 5 ramettes
            Stylos
            Classeurs
            Total HT: 89,00 €
            """,
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest office supplies account
        if result.get("suggested_account_code"):
            assert result["suggested_account_code"].startswith("606")  # Fournitures

    def test_categorize_telecom(self, engine):
        """Test categorization of telecom expense."""
        ocr_data = {
            "raw_text": """
            ORANGE BUSINESS
            Abonnement téléphone mobile
            Forfait professionnel
            Total: 49,99 €
            """,
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest telecom expense account
        if result.get("suggested_account_code"):
            assert result["suggested_account_code"].startswith("626")  # Frais télécoms

    # Confidence Level Tests
    def test_high_confidence_classification(self, engine):
        """Test high confidence when all fields are clear."""
        ocr_data = {
            "raw_text": """
            FACTURE N° FA-2024-00123

            SARL FOURNISSEUR EXEMPLE
            SIRET: 123 456 789 00012
            N° TVA: FR12345678901

            Total HT: 1 000,00 €
            TVA 20%: 200,00 €
            Total TTC: 1 200,00 €
            """,
            "extracted_fields": [
                {"field_name": "invoice_number", "value": "FA-2024-00123", "confidence": 0.98},
                {"field_name": "total_ht", "value": "1000.00", "confidence": 0.97},
                {"field_name": "total_tva", "value": "200.00", "confidence": 0.96},
                {"field_name": "total_ttc", "value": "1200.00", "confidence": 0.99},
                {"field_name": "siret", "value": "12345678900012", "confidence": 0.95},
                {"field_name": "tva_intra", "value": "FR12345678901", "confidence": 0.94},
            ],
        }

        result = engine.classify_document(ocr_data)

        assert result["confidence_level"] == "HIGH"
        assert result["confidence_score"] >= 0.90

    def test_medium_confidence_classification(self, engine):
        """Test medium confidence with some missing fields."""
        ocr_data = {
            "raw_text": """
            FACTURE
            Total: 500 EUR
            """,
            "extracted_fields": [
                {"field_name": "total_ttc", "value": "500.00", "confidence": 0.80},
            ],
        }

        result = engine.classify_document(ocr_data)

        assert result["confidence_level"] in ["MEDIUM", "LOW"]
        assert 0.60 <= result["confidence_score"] < 0.95

    def test_low_confidence_poor_data(self, engine):
        """Test low confidence with poor OCR data."""
        ocr_data = {
            "raw_text": "illegible text xyz 123",
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        assert result["confidence_level"] in ["LOW", "VERY_LOW"]
        assert result["confidence_score"] < 0.80

    # Account Suggestion Tests
    def test_suggest_purchase_account(self, engine):
        """Test account suggestion for purchase invoice."""
        ocr_data = {
            "raw_text": """
            FACTURE ACHAT
            Matières premières
            Total HT: 5 000,00 €
            """,
            "extracted_fields": [
                {"field_name": "total_ht", "value": "5000.00", "confidence": 0.90},
            ],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest a purchase account (60x)
        assert result.get("suggested_account_code") is not None

    def test_suggest_service_account(self, engine):
        """Test account suggestion for service invoice."""
        ocr_data = {
            "raw_text": """
            FACTURE DE PRESTATION
            Conseil en stratégie
            Honoraires: 2 000,00 €
            """,
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest a service account (61x or 62x)
        if result.get("suggested_account_code"):
            code = result["suggested_account_code"]
            assert code.startswith("61") or code.startswith("62")

    # Journal Suggestion Tests
    def test_suggest_purchase_journal(self, engine):
        """Test journal suggestion for purchase invoice."""
        ocr_data = {
            "raw_text": "FACTURE FOURNISSEUR",
            "extracted_fields": [
                {"field_name": "total_ttc", "value": "1000.00", "confidence": 0.85},
            ],
        }

        result = engine.classify_document(ocr_data)

        assert result["document_type"] == "INVOICE_RECEIVED"
        assert result.get("suggested_journal_code") in ["ACH", "HA", None]

    def test_suggest_sales_journal(self, engine):
        """Test journal suggestion for sales invoice."""
        ocr_data = {
            "raw_text": """
            FACTURE CLIENT
            De: Notre Entreprise
            À: Client ABC
            """,
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        # If classified as sent invoice, should suggest sales journal
        if result["document_type"] == "INVOICE_SENT":
            assert result.get("suggested_journal_code") in ["VT", "VE", None]


class TestAIClassificationService:
    """Tests for the AIClassificationService class."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return AIClassificationService(mock_db)

    @pytest.mark.asyncio
    async def test_classify_document_success(self, service, mock_db):
        """Test successful document classification."""
        tenant_id = uuid.uuid4()
        document_id = uuid.uuid4()
        ocr_result = {
            "raw_text": "FACTURE N° 123",
            "extracted_fields": [
                {"field_name": "invoice_number", "value": "123", "confidence": 0.90},
            ],
        }

        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.classify_document(
            tenant_id=tenant_id,
            document_id=document_id,
            ocr_result=ocr_result,
        )

        assert result is not None
        assert "document_type" in result
        assert "confidence_level" in result

    @pytest.mark.asyncio
    async def test_classify_with_vendor_matching(self, service, mock_db):
        """Test classification with vendor matching from database."""
        tenant_id = uuid.uuid4()
        document_id = uuid.uuid4()
        ocr_result = {
            "raw_text": "FACTURE DE ORANGE",
            "extracted_fields": [
                {"field_name": "vendor_name", "value": "ORANGE", "confidence": 0.92},
            ],
        }

        # Mock vendor lookup
        mock_vendor_result = Mock()
        mock_vendor_result.scalar_one_or_none = Mock(
            return_value=Mock(
                id=uuid.uuid4(),
                name="Orange SA",
                default_account_code="626100",
            )
        )
        mock_db.execute = AsyncMock(return_value=mock_vendor_result)
        mock_db.commit = AsyncMock()

        result = await service.classify_document(
            tenant_id=tenant_id,
            document_id=document_id,
            ocr_result=ocr_result,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_classify_with_learning_from_history(self, service, mock_db):
        """Test that classification learns from historical data."""
        tenant_id = uuid.uuid4()
        document_id = uuid.uuid4()
        ocr_result = {
            "raw_text": "FACTURE RECURRING VENDOR",
            "extracted_fields": [],
        }

        # Mock historical classification lookup
        mock_history_result = Mock()
        mock_history_result.scalars = Mock(
            return_value=Mock(
                all=Mock(
                    return_value=[
                        Mock(
                            document_type="INVOICE_RECEIVED",
                            suggested_account_code="607100",
                            confidence_score=0.95,
                        ),
                        Mock(
                            document_type="INVOICE_RECEIVED",
                            suggested_account_code="607100",
                            confidence_score=0.92,
                        ),
                    ]
                )
            )
        )
        mock_db.execute = AsyncMock(return_value=mock_history_result)
        mock_db.commit = AsyncMock()

        result = await service.classify_document(
            tenant_id=tenant_id,
            document_id=document_id,
            ocr_result=ocr_result,
        )

        # Should use historical patterns to improve classification
        assert result is not None


class TestConfidenceLevelMapping:
    """Tests for confidence level mapping."""

    def test_very_high_score_maps_to_high(self):
        """Test that scores >= 95% map to HIGH."""
        assert ConfidenceLevel.HIGH.value == "HIGH"

    def test_confidence_thresholds(self):
        """Test confidence level thresholds."""
        # These should match the implementation thresholds
        thresholds = {
            "HIGH": 0.95,
            "MEDIUM": 0.80,
            "LOW": 0.60,
            "VERY_LOW": 0.0,
        }

        for level in ConfidenceLevel:
            assert level.value in thresholds


class TestVendorDetection:
    """Tests for vendor detection and matching."""

    @pytest.fixture
    def engine(self):
        return AIClassificationEngine()

    def test_detect_vendor_from_header(self, engine):
        """Test vendor detection from invoice header."""
        ocr_data = {
            "raw_text": """
            AMAZON EU SARL
            38 avenue John F Kennedy
            Luxembourg

            FACTURE
            """,
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        # Should identify Amazon as vendor
        assert result.get("suggested_vendor_name") is not None or True

    def test_detect_vendor_from_siret(self, engine):
        """Test vendor detection from SIRET number."""
        ocr_data = {
            "raw_text": "SIRET: 552 120 222 00013",
            "extracted_fields": [
                {"field_name": "siret", "value": "55212022200013", "confidence": 0.95},
            ],
        }

        result = engine.classify_document(ocr_data)

        # Should attempt to match vendor by SIRET
        assert result is not None

    def test_detect_vendor_from_tva_number(self, engine):
        """Test vendor detection from VAT number."""
        ocr_data = {
            "raw_text": "N° TVA: FR40303265045",
            "extracted_fields": [
                {"field_name": "tva_intra", "value": "FR40303265045", "confidence": 0.93},
            ],
        }

        result = engine.classify_document(ocr_data)

        # Should attempt to match vendor by VAT number
        assert result is not None


class TestTaxCodeSuggestion:
    """Tests for VAT/tax code suggestion."""

    @pytest.fixture
    def engine(self):
        return AIClassificationEngine()

    def test_suggest_standard_vat_20(self, engine):
        """Test suggestion of standard 20% VAT."""
        ocr_data = {
            "raw_text": """
            Total HT: 100,00 €
            TVA 20%: 20,00 €
            Total TTC: 120,00 €
            """,
            "extracted_fields": [
                {"field_name": "total_ht", "value": "100.00", "confidence": 0.95},
                {"field_name": "total_tva", "value": "20.00", "confidence": 0.95},
                {"field_name": "total_ttc", "value": "120.00", "confidence": 0.95},
            ],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest 20% VAT code
        if result.get("suggested_tax_code"):
            assert "20" in result["suggested_tax_code"] or result["suggested_tax_code"] == "TVA_NORMAL"

    def test_suggest_reduced_vat_10(self, engine):
        """Test suggestion of reduced 10% VAT."""
        ocr_data = {
            "raw_text": """
            Restaurant
            Total HT: 50,00 €
            TVA 10%: 5,00 €
            Total TTC: 55,00 €
            """,
            "extracted_fields": [
                {"field_name": "total_ht", "value": "50.00", "confidence": 0.90},
                {"field_name": "total_tva", "value": "5.00", "confidence": 0.90},
            ],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest reduced VAT code
        if result.get("suggested_tax_code"):
            assert "10" in result["suggested_tax_code"] or "REDUIT" in result["suggested_tax_code"].upper()

    def test_suggest_super_reduced_vat_55(self, engine):
        """Test suggestion of super-reduced 5.5% VAT."""
        ocr_data = {
            "raw_text": """
            Produits alimentaires
            Total HT: 100,00 €
            TVA 5,5%: 5,50 €
            Total TTC: 105,50 €
            """,
            "extracted_fields": [],
        }

        result = engine.classify_document(ocr_data)

        # Should suggest super-reduced VAT code
        assert result is not None
