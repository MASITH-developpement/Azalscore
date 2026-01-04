"""
Tests Pack Pays France - AZALS
===============================
Tests complets pour la localisation française.

Scénarios testés:
- PCG 2024 (Plan Comptable Général)
- TVA française
- FEC (Fichier des Écritures Comptables)
- DSN (Déclaration Sociale Nominative)
- Contrats de travail
- RGPD (conformité)
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from app.modules.country_packs.france.models import (
    PCGAccount, PCGClass,
    FRVATRate, FRVATDeclaration, TVARate, TVARegime,
    FECExport, FECEntry, FECStatus,
    DSNDeclaration, DSNEmployee, DSNType, DSNStatus,
    FREmploymentContract, ContractType,
    RGPDConsent, RGPDRequest, RGPDDataProcessing, RGPDDataBreach,
    RGPDConsentStatus, RGPDRequestType,
)
from app.modules.country_packs.france.schemas import (
    PCGAccountCreate,
    FRVATRateCreate, VATDeclarationCreate,
    FECGenerateRequest, FECValidationResult,
    DSNGenerateRequest, DSNEmployeeData,
    FRContractCreate,
    RGPDConsentCreate, RGPDRequestCreate, RGPDProcessingCreate, RGPDBreachCreate,
)
from app.modules.country_packs.france.service import FrancePackService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de session DB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def service(mock_db):
    """Service France Pack avec mock DB."""
    return FrancePackService(mock_db, "tenant_test")


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestFrancePackModels:
    """Tests des modèles SQLAlchemy."""

    def test_pcg_account_creation(self):
        """Test création compte PCG."""
        account = PCGAccount(
            tenant_id="test",
            account_number="411000",
            account_label="Clients",
            pcg_class=PCGClass.CLASSE_4,
            normal_balance="D",
            is_active=True,
        )
        assert account.account_number == "411000"
        assert account.pcg_class == PCGClass.CLASSE_4
        assert account.normal_balance == "D"

    def test_vat_rate_creation(self):
        """Test création taux TVA."""
        vat = FRVATRate(
            tenant_id="test",
            code="TVA_20",
            name="TVA taux normal",
            rate_type=TVARate.NORMAL,
            rate=Decimal("20.00"),
            account_collected="44571",
            account_deductible="44566",
        )
        assert vat.rate == Decimal("20.00")
        assert vat.rate_type == TVARate.NORMAL

    def test_vat_declaration_creation(self):
        """Test création déclaration TVA."""
        decl = FRVATDeclaration(
            tenant_id="test",
            declaration_number="TVA-202401-001",
            declaration_type="CA3",
            regime=TVARegime.REEL_NORMAL,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            status="draft",
        )
        assert decl.declaration_type == "CA3"
        assert decl.regime == TVARegime.REEL_NORMAL

    def test_fec_export_creation(self):
        """Test création export FEC."""
        fec = FECExport(
            tenant_id="test",
            fec_code="FEC-123456789-2024",
            siren="123456789",
            fiscal_year=2024,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            status=FECStatus.DRAFT,
        )
        assert fec.siren == "123456789"
        assert fec.fiscal_year == 2024

    def test_fec_entry_creation(self):
        """Test création entrée FEC."""
        entry = FECEntry(
            tenant_id="test",
            fec_export_id=1,
            journal_code="VT",
            journal_lib="Ventes",
            ecriture_num="VT-001",
            ecriture_date=date(2024, 1, 15),
            compte_num="411000",
            compte_lib="Clients",
            piece_ref="FA-2024-001",
            piece_date=date(2024, 1, 15),
            ecriture_lib="Facture client XYZ",
            debit=Decimal("1200.00"),
            credit=Decimal("0"),
        )
        assert entry.debit == Decimal("1200.00")
        assert entry.compte_num == "411000"

    def test_dsn_declaration_creation(self):
        """Test création déclaration DSN."""
        dsn = DSNDeclaration(
            tenant_id="test",
            dsn_code="DSN-202401-001",
            dsn_type=DSNType.MENSUELLE,
            siret="12345678901234",
            period_month=1,
            period_year=2024,
            status=DSNStatus.DRAFT,
        )
        assert dsn.dsn_type == DSNType.MENSUELLE
        assert dsn.siret == "12345678901234"

    def test_dsn_employee_creation(self):
        """Test création salarié DSN."""
        employee = DSNEmployee(
            tenant_id="test",
            dsn_declaration_id=1,
            employee_id=1,
            nir="1234567890123",
            nom="DUPONT",
            prenoms="Jean",
            date_naissance=date(1985, 5, 15),
            brut_periode=Decimal("3500.00"),
            net_imposable=Decimal("2800.00"),
        )
        assert employee.brut_periode == Decimal("3500.00")
        assert employee.nir == "1234567890123"

    def test_employment_contract_creation(self):
        """Test création contrat de travail."""
        contract = FREmploymentContract(
            tenant_id="test",
            employee_id=1,
            contract_type=ContractType.CDI,
            start_date=date(2024, 1, 1),
            convention_collective="1486",
            is_full_time=True,
            work_hours_weekly=Decimal("35"),
            base_salary=Decimal("3500.00"),
        )
        assert contract.contract_type == ContractType.CDI
        assert contract.is_full_time is True

    def test_rgpd_consent_creation(self):
        """Test création consentement RGPD."""
        consent = RGPDConsent(
            tenant_id="test",
            data_subject_type="customer",
            data_subject_id=1,
            purpose="marketing",
            legal_basis="consent",
            status=RGPDConsentStatus.GRANTED,
            consent_given_at=datetime.utcnow(),
        )
        assert consent.status == RGPDConsentStatus.GRANTED
        assert consent.purpose == "marketing"

    def test_rgpd_request_creation(self):
        """Test création demande RGPD."""
        request = RGPDRequest(
            tenant_id="test",
            request_code="RGPD-2024-001",
            request_type=RGPDRequestType.ACCESS,
            data_subject_type="customer",
            requester_name="Jean Dupont",
            requester_email="jean@example.com",
            status="pending",
            due_date=date.today() + timedelta(days=30),
        )
        assert request.request_type == RGPDRequestType.ACCESS

    def test_rgpd_processing_creation(self):
        """Test création traitement RGPD."""
        processing = RGPDDataProcessing(
            tenant_id="test",
            processing_code="PROC-001",
            processing_name="Gestion clients",
            purposes=["facturation", "relation_client"],
            legal_basis="contract",
            data_categories=["identité", "coordonnées"],
            data_subjects=["clients"],
            retention_period="5 ans",
        )
        assert processing.legal_basis == "contract"

    def test_rgpd_breach_creation(self):
        """Test création violation données."""
        breach = RGPDDataBreach(
            tenant_id="test",
            breach_code="BREACH-2024-001",
            breach_title="Fuite données clients",
            detected_at=datetime.utcnow(),
            breach_description="Accès non autorisé",
            breach_nature="confidentiality",
            severity_level="high",
            cnil_notification_required=True,
            status="detected",
        )
        assert breach.severity_level == "high"
        assert breach.cnil_notification_required is True


# ============================================================================
# TESTS ENUMS
# ============================================================================

class TestFrancePackEnums:
    """Tests des enums."""

    def test_pcg_classes(self):
        """Test classes PCG."""
        assert PCGClass.CLASSE_1.value == "1"
        assert PCGClass.CLASSE_4.value == "4"
        assert PCGClass.CLASSE_6.value == "6"
        assert PCGClass.CLASSE_7.value == "7"

    def test_tva_rates(self):
        """Test taux TVA."""
        assert TVARate.NORMAL.value == "NORMAL"
        assert TVARate.REDUIT.value == "REDUIT"
        assert TVARate.EXONERE.value == "EXONERE"

    def test_tva_regimes(self):
        """Test régimes TVA."""
        assert TVARegime.REEL_NORMAL.value == "REEL_NORMAL"
        assert TVARegime.REEL_SIMPLIFIE.value == "REEL_SIMPLIFIE"
        assert TVARegime.FRANCHISE.value == "FRANCHISE"

    def test_fec_status(self):
        """Test statuts FEC."""
        assert FECStatus.DRAFT.value == "DRAFT"
        assert FECStatus.VALIDATED.value == "VALIDATED"
        assert FECStatus.EXPORTED.value == "EXPORTED"

    def test_dsn_types(self):
        """Test types DSN."""
        assert DSNType.MENSUELLE.value == "MENSUELLE"
        assert DSNType.EVENEMENTIELLE.value == "EVENEMENTIELLE"
        assert DSNType.FIN_CONTRAT.value == "FIN_CONTRAT"

    def test_contract_types(self):
        """Test types de contrats."""
        assert ContractType.CDI.value == "CDI"
        assert ContractType.CDD.value == "CDD"
        assert ContractType.APPRENTISSAGE.value == "APPRENTISSAGE"

    def test_rgpd_request_types(self):
        """Test types demandes RGPD."""
        assert RGPDRequestType.ACCESS.value == "ACCESS"
        assert RGPDRequestType.ERASURE.value == "ERASURE"
        assert RGPDRequestType.PORTABILITY.value == "PORTABILITY"


# ============================================================================
# TESTS SCHEMAS
# ============================================================================

class TestFrancePackSchemas:
    """Tests des schémas Pydantic."""

    def test_pcg_account_create(self):
        """Test schéma création compte PCG."""
        data = PCGAccountCreate(
            account_number="411000",
            account_label="Clients",
            pcg_class="4",
            normal_balance="D",
        )
        assert data.account_number == "411000"
        assert data.pcg_class == "4"

    def test_vat_declaration_create(self):
        """Test schéma création déclaration TVA."""
        data = VATDeclarationCreate(
            declaration_type="CA3",
            regime="REEL_NORMAL",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
        )
        assert data.declaration_type == "CA3"

    def test_fec_generate_request(self):
        """Test schéma demande FEC."""
        data = FECGenerateRequest(
            fiscal_year=2024,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            siren="123456789",
        )
        assert data.fiscal_year == 2024
        assert data.siren == "123456789"

    def test_dsn_generate_request(self):
        """Test schéma demande DSN."""
        data = DSNGenerateRequest(
            dsn_type="MENSUELLE",
            period_month=1,
            period_year=2024,
            siret="12345678901234",
        )
        assert data.period_month == 1
        assert data.siret == "12345678901234"

    def test_dsn_employee_data(self):
        """Test schéma données salarié DSN."""
        data = DSNEmployeeData(
            employee_id=1,
            nir="1234567890123",
            nom="DUPONT",
            prenoms="Jean",
            date_naissance=date(1985, 5, 15),
            brut_periode=Decimal("3500.00"),
            net_imposable=Decimal("2800.00"),
        )
        assert data.brut_periode == Decimal("3500.00")

    def test_contract_create(self):
        """Test schéma création contrat."""
        data = FRContractCreate(
            employee_id=1,
            contract_type="CDI",
            start_date=date(2024, 1, 1),
            is_full_time=True,
            work_hours_weekly=Decimal("35"),
            base_salary=Decimal("3500.00"),
        )
        assert data.contract_type == "CDI"

    def test_rgpd_consent_create(self):
        """Test schéma création consentement."""
        data = RGPDConsentCreate(
            data_subject_type="customer",
            data_subject_id=1,
            purpose="marketing",
            legal_basis="consent",
            consent_method="form",
        )
        assert data.purpose == "marketing"

    def test_rgpd_request_create(self):
        """Test schéma création demande RGPD."""
        data = RGPDRequestCreate(
            request_type="ACCESS",
            data_subject_type="customer",
            requester_name="Jean Dupont",
            requester_email="jean@example.com",
        )
        assert data.request_type == "ACCESS"

    def test_rgpd_breach_create(self):
        """Test schéma signalement violation."""
        data = RGPDBreachCreate(
            breach_title="Fuite données",
            detected_at=datetime.utcnow(),
            breach_description="Description de la fuite",
            breach_nature="confidentiality",
            data_categories_affected=["identité", "email"],
            severity_level="high",
        )
        assert data.severity_level == "high"


# ============================================================================
# TESTS SERVICE - PCG
# ============================================================================

class TestFrancePackServicePCG:
    """Tests service - Plan Comptable Général."""

    def test_initialize_pcg(self, service, mock_db):
        """Test initialisation PCG."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        count = service.initialize_pcg()

        assert count > 0
        mock_db.commit.assert_called()

    def test_initialize_pcg_already_exists(self, service, mock_db):
        """Test initialisation PCG déjà fait."""
        mock_db.query.return_value.filter.return_value.first.return_value = PCGAccount(
            tenant_id="test",
            account_number="10",
            account_label="Capital",
            pcg_class=PCGClass.CLASSE_1,
        )

        count = service.initialize_pcg()

        assert count == 0

    def test_create_custom_account(self, service, mock_db):
        """Test création compte personnalisé."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = PCGAccountCreate(
            account_number="411001",
            account_label="Clients France",
            pcg_class="4",
        )

        result = service.create_pcg_account(data)

        mock_db.add.assert_called()
        mock_db.commit.assert_called()


# ============================================================================
# TESTS SERVICE - TVA
# ============================================================================

class TestFrancePackServiceTVA:
    """Tests service - TVA."""

    def test_initialize_vat_rates(self, service, mock_db):
        """Test initialisation taux TVA."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        count = service.initialize_vat_rates()

        assert count == 5  # 5 taux français
        mock_db.commit.assert_called()

    def test_create_vat_declaration(self, service, mock_db):
        """Test création déclaration TVA."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = VATDeclarationCreate(
            declaration_type="CA3",
            regime="REEL_NORMAL",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
        )

        result = service.create_vat_declaration(data)

        mock_db.add.assert_called()


# ============================================================================
# TESTS SERVICE - FEC
# ============================================================================

class TestFrancePackServiceFEC:
    """Tests service - FEC."""

    def test_generate_fec(self, service, mock_db):
        """Test génération FEC."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        data = FECGenerateRequest(
            fiscal_year=2024,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            siren="123456789",
        )

        result = service.generate_fec(data)

        mock_db.add.assert_called()

    def test_validate_fec(self, service, mock_db):
        """Test validation FEC."""
        fec = FECExport(
            id=1,
            tenant_id="test",
            fec_code="FEC-123456789-2024",
            siren="123456789",
            fiscal_year=2024,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            total_entries=100,
            total_debit=Decimal("50000.00"),
            total_credit=Decimal("50000.00"),  # Équilibré
            status=FECStatus.DRAFT,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = fec
        mock_db.commit = MagicMock()

        result = service.validate_fec(1)

        assert result.is_valid is True
        assert result.is_balanced is True


# ============================================================================
# TESTS SERVICE - DSN
# ============================================================================

class TestFrancePackServiceDSN:
    """Tests service - DSN."""

    def test_create_dsn(self, service, mock_db):
        """Test création DSN."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = DSNGenerateRequest(
            dsn_type="MENSUELLE",
            period_month=1,
            period_year=2024,
            siret="12345678901234",
        )

        result = service.create_dsn(data)

        mock_db.add.assert_called()

    def test_add_dsn_employee(self, service, mock_db):
        """Test ajout salarié DSN."""
        dsn = DSNDeclaration(
            id=1,
            tenant_id="test",
            dsn_code="DSN-202401-001",
            dsn_type=DSNType.MENSUELLE,
            siret="12345678901234",
            period_month=1,
            period_year=2024,
            total_employees=0,
            total_brut=Decimal("0"),
            status=DSNStatus.DRAFT,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = dsn
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = DSNEmployeeData(
            employee_id=1,
            nir="1234567890123",
            nom="DUPONT",
            prenoms="Jean",
            date_naissance=date(1985, 5, 15),
            brut_periode=Decimal("3500.00"),
            net_imposable=Decimal("2800.00"),
        )

        result = service.add_dsn_employee(1, data)

        mock_db.add.assert_called()

    def test_submit_dsn(self, service, mock_db):
        """Test soumission DSN."""
        dsn = DSNDeclaration(
            id=1,
            tenant_id="test",
            dsn_code="DSN-202401-001",
            dsn_type=DSNType.MENSUELLE,
            siret="12345678901234",
            period_month=1,
            period_year=2024,
            status=DSNStatus.DRAFT,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = dsn
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.submit_dsn(1)

        assert dsn.status == DSNStatus.SUBMITTED
        assert dsn.submission_id is not None


# ============================================================================
# TESTS SERVICE - CONTRATS
# ============================================================================

class TestFrancePackServiceContracts:
    """Tests service - Contrats."""

    def test_create_contract(self, service, mock_db):
        """Test création contrat."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = FRContractCreate(
            employee_id=1,
            contract_type="CDI",
            start_date=date(2024, 1, 1),
            is_full_time=True,
            work_hours_weekly=Decimal("35"),
            base_salary=Decimal("3500.00"),
        )

        result = service.create_contract(data)

        mock_db.add.assert_called()


# ============================================================================
# TESTS SERVICE - RGPD
# ============================================================================

class TestFrancePackServiceRGPD:
    """Tests service - RGPD."""

    def test_create_consent(self, service, mock_db):
        """Test création consentement."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = RGPDConsentCreate(
            data_subject_type="customer",
            data_subject_id=1,
            purpose="marketing",
            legal_basis="consent",
            consent_method="form",
        )

        result = service.create_consent(data)

        mock_db.add.assert_called()

    def test_withdraw_consent(self, service, mock_db):
        """Test retrait consentement."""
        consent = RGPDConsent(
            id=1,
            tenant_id="test",
            data_subject_type="customer",
            data_subject_id=1,
            purpose="marketing",
            status=RGPDConsentStatus.GRANTED,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = consent
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.withdraw_consent(1, "Plus intéressé")

        assert consent.status == RGPDConsentStatus.WITHDRAWN
        assert consent.withdrawn_reason == "Plus intéressé"

    def test_create_rgpd_request(self, service, mock_db):
        """Test création demande RGPD."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = RGPDRequestCreate(
            request_type="ACCESS",
            data_subject_type="customer",
            requester_name="Jean Dupont",
            requester_email="jean@example.com",
        )

        result = service.create_rgpd_request(data)

        mock_db.add.assert_called()

    def test_process_rgpd_request(self, service, mock_db):
        """Test traitement demande RGPD."""
        request = RGPDRequest(
            id=1,
            tenant_id="test",
            request_code="RGPD-2024-001",
            request_type=RGPDRequestType.ACCESS,
            data_subject_type="customer",
            requester_name="Jean Dupont",
            requester_email="jean@example.com",
            status="pending",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = request
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.process_rgpd_request(1, "Données fournies", data_exported=True)

        assert request.status == "completed"
        assert request.data_exported is True

    def test_report_data_breach(self, service, mock_db):
        """Test signalement violation."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = RGPDBreachCreate(
            breach_title="Fuite données",
            detected_at=datetime.utcnow(),
            breach_description="Accès non autorisé",
            breach_nature="confidentiality",
            data_categories_affected=["identité", "email"],
            severity_level="high",
        )

        result = service.report_data_breach(data)

        mock_db.add.assert_called()

    def test_breach_high_severity_requires_cnil_notification(self, service, mock_db):
        """Test violation haute sévérité nécessite notification CNIL."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = RGPDBreachCreate(
            breach_title="Fuite critique",
            detected_at=datetime.utcnow(),
            breach_description="Données sensibles exposées",
            breach_nature="confidentiality",
            data_categories_affected=["données santé"],
            severity_level="critical",
        )

        # Capture l'objet ajouté
        captured_breach = None
        def capture_add(obj):
            nonlocal captured_breach
            captured_breach = obj
        mock_db.add.side_effect = capture_add

        result = service.report_data_breach(data)

        assert captured_breach.cnil_notification_required is True
        assert captured_breach.subjects_notification_required is True


# ============================================================================
# TESTS STATISTIQUES
# ============================================================================

class TestFrancePackStats:
    """Tests statistiques Pack France."""

    def test_get_stats(self, service, mock_db):
        """Test récupération statistiques."""
        mock_db.query.return_value.filter.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 5

        result = service.get_stats()

        assert result is not None
        assert hasattr(result, "total_pcg_accounts")
        assert hasattr(result, "pending_rgpd_requests")


# ============================================================================
# TESTS CONFORMITÉ LÉGALE
# ============================================================================

class TestFrancePackLegalCompliance:
    """Tests conformité légale française."""

    def test_fec_format_compliance(self):
        """Test conformité format FEC."""
        # Le FEC doit contenir les 18 champs obligatoires
        entry = FECEntry(
            tenant_id="test",
            fec_export_id=1,
            journal_code="VT",
            journal_lib="Ventes",
            ecriture_num="VT-001",
            ecriture_date=date(2024, 1, 15),
            compte_num="411000",
            compte_lib="Clients",
            piece_ref="FA-2024-001",
            piece_date=date(2024, 1, 15),
            ecriture_lib="Facture client",
            debit=Decimal("1200.00"),
            credit=Decimal("0"),
        )

        # Vérifier que tous les champs obligatoires sont présents
        assert entry.journal_code is not None
        assert entry.journal_lib is not None
        assert entry.ecriture_num is not None
        assert entry.ecriture_date is not None
        assert entry.compte_num is not None
        assert entry.compte_lib is not None
        assert entry.piece_ref is not None
        assert entry.piece_date is not None
        assert entry.ecriture_lib is not None
        assert entry.debit is not None
        assert entry.credit is not None

    def test_dsn_nir_format(self):
        """Test format NIR pour DSN."""
        # NIR doit avoir 13 ou 15 caractères
        employee = DSNEmployee(
            tenant_id="test",
            dsn_declaration_id=1,
            employee_id=1,
            nir="1234567890123",  # 13 caractères
            nom="DUPONT",
            prenoms="Jean",
            date_naissance=date(1985, 5, 15),
            brut_periode=Decimal("3500.00"),
            net_imposable=Decimal("2800.00"),
        )
        assert len(employee.nir) == 13

    def test_rgpd_request_delay(self, service, mock_db):
        """Test délai légal demande RGPD (1 mois)."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        data = RGPDRequestCreate(
            request_type="ACCESS",
            data_subject_type="customer",
            requester_name="Jean Dupont",
            requester_email="jean@example.com",
        )

        # Capture l'objet ajouté
        captured_request = None
        def capture_add(obj):
            nonlocal captured_request
            captured_request = obj
        mock_db.add.side_effect = capture_add

        result = service.create_rgpd_request(data)

        # Le délai légal est de 30 jours max
        expected_due = date.today() + timedelta(days=30)
        assert captured_request.due_date == expected_due

    def test_vat_rates_french_standards(self, service, mock_db):
        """Test taux TVA conformes aux standards français."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        # Capturer les taux ajoutés
        added_rates = []
        def capture_add(obj):
            if isinstance(obj, FRVATRate):
                added_rates.append(obj)
        mock_db.add.side_effect = capture_add

        service.initialize_vat_rates()

        # Vérifier les taux français officiels
        rates_by_code = {r.code: r for r in added_rates}
        assert rates_by_code["TVA_20"].rate == Decimal("20.00")
        assert rates_by_code["TVA_10"].rate == Decimal("10.00")
        assert rates_by_code["TVA_5_5"].rate == Decimal("5.50")
        assert rates_by_code["TVA_2_1"].rate == Decimal("2.10")
        assert rates_by_code["TVA_0"].rate == Decimal("0.00")
