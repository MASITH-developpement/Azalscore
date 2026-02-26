"""
Tests pour le module OCR Factures Fournisseurs.
================================================

Tests unitaires et d'intégration pour InvoiceOCRService et Router.
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
import tempfile
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.finance.invoice_ocr.service import (
    InvoiceOCRService,
    InvoiceExtraction,
    ExtractionResult,
    ExtractedVendor,
    ExtractedLineItem,
    InvoiceType,
    ValidationStatus,
    InvoicePatterns,
)
from app.modules.finance.invoice_ocr.router import (
    router,
    get_invoice_ocr_service,
    ExtractionResponse,
)
from app.core.dependencies_v2 import get_saas_context


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tenant_id() -> str:
    """ID de tenant pour les tests."""
    return "tenant-test-ocr-001"


@pytest.fixture
def mock_db():
    """Session de base de données mockée."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture
def service(mock_db, tenant_id):
    """Service OCR pour les tests."""
    return InvoiceOCRService(db=mock_db, tenant_id=tenant_id)


@pytest.fixture
def mock_service():
    """Service mocké pour les tests de router."""
    service = MagicMock(spec=InvoiceOCRService)
    service.process_invoice = AsyncMock(return_value=ExtractionResult(
        success=True,
        extraction=InvoiceExtraction(
            id="test-extraction-001",
            invoice_type=InvoiceType.SUPPLIER,
            confidence=0.95,
            invoice_number="FAC-2024-001",
            invoice_number_confidence=0.98,
            invoice_date=date(2024, 1, 15),
            invoice_date_confidence=0.95,
            due_date=date(2024, 2, 15),
            due_date_confidence=0.90,
            amount_untaxed=Decimal("1000.00"),
            amount_untaxed_confidence=0.97,
            amount_tax=Decimal("200.00"),
            amount_tax_confidence=0.95,
            amount_total=Decimal("1200.00"),
            amount_total_confidence=0.98,
            currency="EUR",
            vendor=ExtractedVendor(
                name="Fournisseur Test",
                siret="12345678901234",
                tva_number="FR12345678901",
                confidence=0.92,
            ),
            line_items=[
                ExtractedLineItem(
                    description="Produit A",
                    quantity=Decimal("2"),
                    unit_price=Decimal("500.00"),
                    total=Decimal("1000.00"),
                    confidence=0.90,
                ),
            ],
            amounts_consistent=True,
            tva_validated=ValidationStatus.VALID,
        ),
        file_hash="abc123def456",
    ))
    return service


@pytest.fixture
def mock_context():
    """Contexte SaaS mocké."""
    context = MagicMock()
    context.tenant_id = "test-tenant-ocr-123"
    context.user_id = uuid4()
    return context


@pytest.fixture
def app(mock_service, mock_context):
    """Application FastAPI de test."""
    test_app = FastAPI()
    test_app.include_router(router)

    async def override_service():
        return mock_service

    async def override_context():
        return mock_context

    test_app.dependency_overrides[get_invoice_ocr_service] = override_service
    test_app.dependency_overrides[get_saas_context] = override_context
    return test_app


@pytest.fixture
def client(app):
    """Client de test."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_content():
    """Contenu PDF simulé."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


@pytest.fixture
def temp_pdf_file(sample_pdf_content):
    """Fichier PDF temporaire."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(sample_pdf_content)
        tmp_path = tmp.name
    yield tmp_path
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


# =============================================================================
# TESTS SERVICE - INITIALISATION
# =============================================================================


class TestServiceInit:
    """Tests d'initialisation du service."""

    def test_init_with_tenant_id(self, mock_db, tenant_id):
        """Test initialisation avec tenant_id."""
        service = InvoiceOCRService(db=mock_db, tenant_id=tenant_id)
        assert service.tenant_id == tenant_id
        assert service.db == mock_db

    def test_init_requires_tenant_id(self, mock_db):
        """Test que tenant_id est obligatoire."""
        with pytest.raises(ValueError, match="tenant_id est obligatoire"):
            InvoiceOCRService(db=mock_db, tenant_id="")

    def test_init_with_none_tenant_id(self, mock_db):
        """Test que tenant_id None est refusé."""
        with pytest.raises(ValueError, match="tenant_id est obligatoire"):
            InvoiceOCRService(db=mock_db, tenant_id=None)


# =============================================================================
# TESTS SERVICE - PATTERNS
# =============================================================================


class TestInvoicePatterns:
    """Tests des patterns d'extraction."""

    def test_patterns_invoice_number_defined(self):
        """Test que les patterns de numéro de facture sont définis."""
        assert len(InvoicePatterns.INVOICE_NUMBER) > 0
        assert all(isinstance(p, str) for p in InvoicePatterns.INVOICE_NUMBER)

    def test_patterns_date_defined(self):
        """Test que les patterns de date sont définis."""
        assert len(InvoicePatterns.DATE_PATTERNS) > 0

    def test_patterns_amount_defined(self):
        """Test que les patterns de montant sont définis."""
        assert len(InvoicePatterns.AMOUNT_PATTERNS) > 0

    def test_patterns_siret_defined(self):
        """Test que les patterns SIRET sont définis."""
        assert len(InvoicePatterns.SIRET) > 0

    def test_patterns_tva_defined(self):
        """Test que les patterns TVA sont définis."""
        assert len(InvoicePatterns.TVA_INTRA) > 0

    def test_patterns_iban_defined(self):
        """Test que les patterns IBAN sont définis."""
        assert len(InvoicePatterns.IBAN) > 0


# =============================================================================
# TESTS SERVICE - VALIDATION SIRET
# =============================================================================


class TestValidationSiret:
    """Tests de validation SIRET."""

    def test_validate_siret_wrong_length(self, service):
        """Test validation SIRET longueur incorrecte."""
        is_valid = service._validate_siret("123456")
        assert is_valid is False

    def test_validate_siret_non_numeric(self, service):
        """Test validation SIRET non numérique."""
        is_valid = service._validate_siret("1234567890ABCD")
        assert is_valid is False

    def test_validate_siret_returns_boolean(self, service):
        """Test validation retourne booléen."""
        result = service._validate_siret("12345678901234")
        assert isinstance(result, bool)


# =============================================================================
# TESTS SERVICE - UTILITAIRES
# =============================================================================


class TestUtilities:
    """Tests des méthodes utilitaires."""

    def test_parse_amount_comma(self, service):
        """Test parsing montant avec virgule."""
        result = service._parse_amount("1234,56")
        assert result == Decimal("1234.56")

    def test_parse_amount_point(self, service):
        """Test parsing montant avec point."""
        result = service._parse_amount("1234.56")
        assert result == Decimal("1234.56")

    def test_parse_amount_spaces(self, service):
        """Test parsing montant avec espaces."""
        result = service._parse_amount("1 234,56")
        assert result == Decimal("1234.56")

    def test_parse_amount_invalid(self, service):
        """Test parsing montant invalide."""
        result = service._parse_amount("abc")
        assert result is None

    def test_parse_amount_empty(self, service):
        """Test parsing montant vide."""
        result = service._parse_amount("")
        assert result is None

    def test_parse_date_french_format(self, service):
        """Test parsing date format français."""
        result = service._parse_date("15/01/2024")
        assert result == date(2024, 1, 15)

    def test_parse_date_dash_format(self, service):
        """Test parsing date format tirets."""
        result = service._parse_date("15-01-2024")
        assert result == date(2024, 1, 15)

    def test_parse_date_dot_format(self, service):
        """Test parsing date format points."""
        result = service._parse_date("15.01.2024")
        assert result == date(2024, 1, 15)

    def test_parse_date_short_year(self, service):
        """Test parsing date année courte."""
        result = service._parse_date("15/01/24")
        assert result is not None
        assert result.day == 15
        assert result.month == 1

    def test_parse_date_invalid(self, service):
        """Test parsing date invalide."""
        result = service._parse_date("invalid")
        assert result is None

    def test_parse_date_empty(self, service):
        """Test parsing date vide."""
        result = service._parse_date("")
        assert result is None


# =============================================================================
# TESTS SERVICE - PROCESS INVOICE
# =============================================================================


class TestProcessInvoice:
    """Tests du traitement de facture."""

    @pytest.mark.asyncio
    async def test_process_invoice_file_not_found(self, service):
        """Test traitement fichier inexistant."""
        result = await service.process_invoice("/nonexistent/file.pdf")
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_process_invoice_returns_extraction_result(self, service, temp_pdf_file):
        """Test que process_invoice retourne un ExtractionResult."""
        result = await service.process_invoice(temp_pdf_file)
        assert isinstance(result, ExtractionResult)
        assert result.file_hash is not None

    @pytest.mark.asyncio
    async def test_process_invoice_calculates_hash(self, service, temp_pdf_file):
        """Test que le hash est calculé."""
        result = await service.process_invoice(temp_pdf_file)
        assert result.file_hash is not None
        assert len(result.file_hash) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_process_batch_returns_list(self, service, temp_pdf_file):
        """Test que process_batch retourne une liste."""
        results = await service.process_batch([temp_pdf_file])
        assert isinstance(results, list)
        assert len(results) == 1


# =============================================================================
# TESTS SERVICE - EXTRACTION DATA
# =============================================================================


class TestExtractionData:
    """Tests de l'extraction de données."""

    def test_extract_invoice_data_returns_extraction(self, service):
        """Test que _extract_invoice_data retourne une InvoiceExtraction."""
        text = "FACTURE FAC-2024-001\nTotal: 1200 EUR"
        result = service._extract_invoice_data(text)
        assert isinstance(result, InvoiceExtraction)

    def test_detect_invoice_type_supplier(self, service):
        """Test détection type facture fournisseur."""
        result = service._detect_invoice_type("FACTURE N° 12345")
        assert result == InvoiceType.SUPPLIER

    def test_detect_invoice_type_credit_note(self, service):
        """Test détection type avoir."""
        result = service._detect_invoice_type("AVOIR N° 12345")
        assert result == InvoiceType.CREDIT_NOTE

    def test_detect_invoice_type_unknown(self, service):
        """Test détection type inconnu."""
        result = service._detect_invoice_type("Document quelconque")
        assert result == InvoiceType.UNKNOWN


# =============================================================================
# TESTS ROUTER - EXTRACT
# =============================================================================


class TestRouterExtract:
    """Tests endpoint extraction."""

    def test_extract_invoice_success(self, client, mock_service, sample_pdf_content):
        """Test extraction facture succès."""
        response = client.post(
            "/v3/finance/invoice-ocr/extract",
            files={"file": ("facture.pdf", sample_pdf_content, "application/pdf")},
            data={"check_duplicate": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["invoice_number"] == "FAC-2024-001"
        assert data["amount_total"] == "1200.00"

    def test_extract_invoice_png(self, client, mock_service):
        """Test extraction image PNG."""
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'

        response = client.post(
            "/v3/finance/invoice-ocr/extract",
            files={"file": ("facture.png", png_content, "image/png")},
        )

        assert response.status_code == 200

    def test_extract_invoice_invalid_type(self, client, mock_service):
        """Test extraction type de fichier invalide."""
        response = client.post(
            "/v3/finance/invoice-ocr/extract",
            files={"file": ("document.txt", b"Hello", "text/plain")},
        )

        assert response.status_code == 400
        assert "non supporté" in response.json()["detail"]


# =============================================================================
# TESTS ROUTER - VALIDATE AMOUNTS
# =============================================================================


class TestRouterValidateAmounts:
    """Tests endpoint validation montants."""

    def test_validate_amounts_valid(self, client):
        """Test validation montants valides."""
        response = client.post(
            "/v3/finance/invoice-ocr/validate-amounts",
            data={
                "amount_ht": "1000.00",
                "amount_tva": "200.00",
                "amount_ttc": "1200.00",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["tva_rate_detected"] == 20.0

    def test_validate_amounts_invalid(self, client):
        """Test validation montants invalides."""
        response = client.post(
            "/v3/finance/invoice-ocr/validate-amounts",
            data={
                "amount_ht": "1000.00",
                "amount_tva": "200.00",
                "amount_ttc": "1500.00",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert float(data["difference"]) > 0

    def test_validate_amounts_with_tolerance(self, client):
        """Test validation montants avec tolérance."""
        response = client.post(
            "/v3/finance/invoice-ocr/validate-amounts",
            data={
                "amount_ht": "100.00",
                "amount_tva": "20.00",
                "amount_ttc": "120.01",
                "tolerance": "0.02",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


# =============================================================================
# TESTS ROUTER - VALIDATE SIRET
# =============================================================================


class TestRouterValidateSiret:
    """Tests endpoint validation SIRET."""

    def test_validate_siret_format(self, client):
        """Test validation SIRET format et structure réponse."""
        response = client.post(
            "/v3/finance/invoice-ocr/validate-siret",
            data={"siret": "35600000000048"},
        )

        assert response.status_code == 200
        data = response.json()
        # Vérifie structure de la réponse
        assert "valid" in data
        assert "siret" in data
        assert data["siret"] == "35600000000048"
        assert isinstance(data["valid"], bool)

    def test_validate_siret_with_spaces(self, client):
        """Test validation SIRET avec espaces."""
        response = client.post(
            "/v3/finance/invoice-ocr/validate-siret",
            data={"siret": "356 000 000 00048"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["siret"] == "35600000000048"

    def test_validate_siret_wrong_length(self, client):
        """Test validation SIRET longueur incorrecte."""
        response = client.post(
            "/v3/finance/invoice-ocr/validate-siret",
            data={"siret": "123456"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "14 chiffres" in data["error"]

    def test_validate_siret_non_numeric(self, client):
        """Test validation SIRET non numérique."""
        response = client.post(
            "/v3/finance/invoice-ocr/validate-siret",
            data={"siret": "1234567890ABCD"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "chiffres" in data["error"]


# =============================================================================
# TESTS ROUTER - SUPPORTED FORMATS
# =============================================================================


class TestRouterSupportedFormats:
    """Tests endpoint formats supportés."""

    def test_get_supported_formats(self, client):
        """Test récupération formats supportés."""
        response = client.get("/v3/finance/invoice-ocr/supported-formats")

        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) >= 4

        extensions = [f["extension"] for f in data["formats"]]
        assert ".pdf" in extensions
        assert ".png" in extensions
        assert ".jpg" in extensions

        assert data["max_file_size_mb"] == 20
        assert data["max_pages"] == 50


# =============================================================================
# TESTS ROUTER - HEALTH
# =============================================================================


class TestRouterHealth:
    """Tests endpoint health."""

    def test_health_check(self, client):
        """Test health check."""
        response = client.get("/v3/finance/invoice-ocr/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "finance-invoice-ocr"
        assert "engines" in data
        assert "features" in data
        assert "invoice_extraction" in data["features"]


# =============================================================================
# TESTS ENUMS
# =============================================================================


class TestEnums:
    """Tests des enums."""

    def test_invoice_types(self):
        """Test types de facture."""
        assert InvoiceType.SUPPLIER.value == "supplier"
        assert InvoiceType.CREDIT_NOTE.value == "credit_note"
        assert InvoiceType.UNKNOWN.value == "unknown"

    def test_validation_status(self):
        """Test statuts de validation."""
        assert ValidationStatus.VALID.value == "valid"
        assert ValidationStatus.INVALID.value == "invalid"
        assert ValidationStatus.UNVERIFIED.value == "unverified"


# =============================================================================
# TESTS DATA CLASSES
# =============================================================================


class TestDataClasses:
    """Tests des classes de données."""

    def test_vendor_info_creation(self):
        """Test création ExtractedVendor."""
        vendor = ExtractedVendor(
            name="Test Vendor",
            siret="12345678901234",
            tva_number="FR12345678901",
            iban="FR7612345678901234567890123",
            address="123 Rue Test",
            confidence=0.95,
        )
        assert vendor.name == "Test Vendor"
        assert vendor.confidence == 0.95

    def test_line_item_creation(self):
        """Test création ExtractedLineItem."""
        item = ExtractedLineItem(
            description="Test Product",
            quantity=Decimal("2"),
            unit_price=Decimal("50.00"),
            total=Decimal("100.00"),
            tva_rate=Decimal("20.0"),
            confidence=0.90,
        )
        assert item.description == "Test Product"
        assert item.total == Decimal("100.00")

    def test_invoice_extraction_creation(self):
        """Test création InvoiceExtraction."""
        extraction = InvoiceExtraction(
            id="test-001",
            invoice_type=InvoiceType.SUPPLIER,
            confidence=0.95,
            invoice_number="FAC-001",
            invoice_date=date.today(),
            amount_total=Decimal("1200.00"),
            currency="EUR",
        )
        assert extraction.id == "test-001"
        assert extraction.invoice_type == InvoiceType.SUPPLIER

    def test_extraction_result_success(self):
        """Test ExtractionResult succès."""
        result = ExtractionResult(
            success=True,
            extraction=InvoiceExtraction(
                id="test-001",
                invoice_type=InvoiceType.SUPPLIER,
                confidence=0.95,
            ),
            file_hash="abc123",
        )
        assert result.success is True
        assert result.extraction is not None

    def test_extraction_result_failure(self):
        """Test ExtractionResult échec."""
        result = ExtractionResult(
            success=False,
            error="Fichier corrompu",
        )
        assert result.success is False
        assert result.error == "Fichier corrompu"
        assert result.extraction is None
