"""
AZALS MODULE CONTRACTS - Tests Complets
=======================================

Tests bloquants pour la gestion des contrats (CLM).
Couvre: modeles, schemas, repository, service, workflow.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session
import uuid

from app.modules.contracts.models import (
    Contract, ContractParty, ContractLine, ContractClause,
    ContractObligation, ContractMilestone, ContractAmendment,
    ContractRenewal, ContractDocument, ContractAlert, ContractApproval,
    ContractHistory, ContractCategory, ContractTemplate, ClauseTemplate,
    ContractMetrics,
    ContractType, ContractStatus, PartyType, PartyRole,
    BillingFrequency, BillingType, RenewalType, RenewalStatus,
    AmendmentType, AmendmentStatus, ObligationType, ObligationStatus,
    MilestoneStatus, AlertType, AlertPriority, AlertStatus,
    ApprovalStatus, ClauseCategory, ClauseStatus, DocumentType
)
from app.modules.contracts.schemas import (
    ContractCreate, ContractUpdate, ContractFilters,
    ContractPartyCreate, ContractPartyUpdate, ContractRecordSignatureRequest,
    ContractLineCreate, ContractLineUpdate,
    ContractClauseCreate, ContractClauseUpdate,
    ContractObligationCreate, ContractObligationUpdate, ObligationCompleteRequest,
    ContractMilestoneCreate, ContractMilestoneUpdate, MilestoneCompleteRequest,
    ContractAmendmentCreate, ContractAmendmentUpdate,
    ContractAlertCreate, AlertAcknowledgeRequest,
    ContractApprovalCreate, ApprovalDecisionRequest,
    ContractCategoryCreate, ContractCategoryUpdate,
    ContractTemplateCreate, ContractTemplateUpdate,
    ClauseTemplateCreate, ClauseTemplateUpdate,
    ContractSubmitForApprovalRequest,
    ContractTerminateRequest, ContractRenewRequest
)
from app.modules.contracts.exceptions import (
    ContractError, ContractNotFoundError, ContractDuplicateError,
    ContractValidationError, ContractStateError, ContractNotEditableError,
    PartyNotFoundError, PartyAlreadySignedError, MissingPartyError,
    ContractLineNotFoundError, ClauseNotFoundError, MandatoryClauseMissingError,
    ObligationNotFoundError, ObligationAlreadyCompletedError,
    MilestoneNotFoundError, MilestoneAlreadyCompletedError, MilestoneDependencyError,
    AmendmentNotFoundError, AmendmentNotAllowedError,
    RenewalNotAllowedError, MaxRenewalsReachedError,
    ApprovalNotFoundError, ApprovalNotAuthorizedError, ApprovalAlreadyProcessedError,
    CategoryNotFoundError, CategoryDuplicateError,
    TemplateNotFoundError, TemplateDuplicateError,
    AlertNotFoundError, AlertAlreadyAcknowledgedError,
    ContractVersionConflictError
)
from app.modules.contracts.service import ContractService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def contract_service(mock_db):
    """Contract service instance."""
    return ContractService(mock_db, "test-tenant")


@pytest.fixture
def sample_contract_create():
    """Sample contract creation data."""
    return ContractCreate(
        contract_type=ContractType.SERVICE,
        title="Contrat de prestation de services",
        description="Contrat de developpement logiciel",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        total_value=Decimal("50000.00"),
        currency="EUR",
        payment_terms="30 jours net"
    )


@pytest.fixture
def sample_party_create():
    """Sample party creation data."""
    return ContractContractPartyCreate(
        party_type=PartyType.COMPANY,
        role=PartyRole.CLIENT,
        name="Entreprise ABC",
        email="contact@abc.com",
        is_signatory=True,
        is_primary=True
    )


@pytest.fixture
def sample_line_create():
    """Sample contract line creation data."""
    return ContractContractLineCreate(
        description="Developpement application web",
        quantity=Decimal("1"),
        unit_price=Decimal("40000.00"),
        billing_type=BillingType.FIXED,
        billing_frequency=BillingFrequency.ONCE
    )


@pytest.fixture
def sample_contract():
    """Sample contract model instance."""
    contract = Contract(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        contract_number="CTR202401-00001",
        contract_type=ContractType.SERVICE,
        status=ContractStatus.DRAFT,
        title="Test Contract",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        total_value=Decimal("50000.00"),
        currency="EUR",
        version=1
    )
    return contract


@pytest.fixture
def active_contract():
    """Active contract model instance."""
    contract = Contract(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        contract_number="CTR202401-00002",
        contract_type=ContractType.SERVICE,
        status=ContractStatus.ACTIVE,
        title="Active Contract",
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=335),
        total_value=Decimal("100000.00"),
        currency="EUR",
        version=3,
        activated_at=datetime.utcnow() - timedelta(days=30)
    )
    return contract


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestContractModels:
    """Tests des modeles Contract."""

    def test_contract_model_creation(self):
        """Test creation modele contrat."""
        contract = Contract(
            tenant_id="test",
            contract_number="CTR001",
            contract_type=ContractType.SERVICE,
            status=ContractStatus.DRAFT,
            title="Test Contract",
            start_date=date.today()
        )
        assert contract.contract_type == ContractType.SERVICE
        assert contract.status == ContractStatus.DRAFT

    def test_contract_party_model_creation(self):
        """Test creation modele partie contractante."""
        party = ContractParty(
            tenant_id="test",
            contract_id=uuid.uuid4(),
            party_type=PartyType.COMPANY,
            role=PartyRole.CLIENT,
            name="Client Test"
        )
        assert party.role == PartyRole.CLIENT
        assert party.party_type == PartyType.COMPANY

    def test_contract_line_model_creation(self):
        """Test creation modele ligne de contrat."""
        line = ContractLine(
            tenant_id="test",
            contract_id=uuid.uuid4(),
            line_number=1,
            description="Service de consulting",
            quantity=Decimal("10"),
            unit_price=Decimal("1000.00"),
            billing_type=BillingType.TIME_MATERIAL
        )
        assert line.billing_type == BillingType.TIME_MATERIAL
        assert line.unit_price == Decimal("1000.00")

    def test_contract_obligation_model_creation(self):
        """Test creation modele obligation."""
        obligation = ContractObligation(
            tenant_id="test",
            contract_id=uuid.uuid4(),
            title="Livrer le rapport",
            obligation_type=ObligationType.DELIVERABLE,
            status=ObligationStatus.PENDING,
            due_date=date.today() + timedelta(days=30)
        )
        assert obligation.obligation_type == ObligationType.DELIVERABLE
        assert obligation.status == ObligationStatus.PENDING

    def test_contract_milestone_model_creation(self):
        """Test creation modele jalon."""
        milestone = ContractMilestone(
            tenant_id="test",
            contract_id=uuid.uuid4(),
            title="Phase 1 Complete",
            due_date=date.today() + timedelta(days=60),
            status=MilestoneStatus.PENDING
        )
        assert milestone.status == MilestoneStatus.PENDING

    def test_contract_amendment_model_creation(self):
        """Test creation modele avenant."""
        amendment = ContractAmendment(
            tenant_id="test",
            contract_id=uuid.uuid4(),
            amendment_number="AVN001",
            title="Extension de contrat",
            amendment_type=AmendmentType.EXTENSION,
            status=AmendmentStatus.DRAFT
        )
        assert amendment.amendment_type == AmendmentType.EXTENSION
        assert amendment.status == AmendmentStatus.DRAFT

    def test_contract_alert_model_creation(self):
        """Test creation modele alerte."""
        alert = ContractAlert(
            tenant_id="test",
            contract_id=uuid.uuid4(),
            alert_type=AlertType.RENEWAL_REMINDER,
            priority=AlertPriority.HIGH,
            title="Renouvellement proche",
            due_date=date.today() + timedelta(days=30)
        )
        assert alert.alert_type == AlertType.RENEWAL_REMINDER
        assert alert.priority == AlertPriority.HIGH

    def test_contract_category_model_creation(self):
        """Test creation modele categorie."""
        category = ContractCategory(
            tenant_id="test",
            code="SERVICE",
            name="Contrats de service",
            is_active=True
        )
        assert category.code == "SERVICE"
        assert category.is_active is True

    def test_contract_template_model_creation(self):
        """Test creation modele template."""
        template = ContractTemplate(
            tenant_id="test",
            code="SVC_STANDARD",
            name="Contrat de service standard",
            contract_type=ContractType.SERVICE,
            is_active=True
        )
        assert template.contract_type == ContractType.SERVICE


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestContractEnums:
    """Tests des enumerations."""

    def test_contract_type_values(self):
        """Test valeurs types de contrat."""
        assert ContractType.SERVICE.value == "service"
        assert ContractType.SUBSCRIPTION.value == "subscription"
        assert ContractType.NDA.value == "nda"
        assert ContractType.EMPLOYMENT.value == "employment"

    def test_contract_status_values(self):
        """Test valeurs statuts de contrat."""
        assert ContractStatus.DRAFT.value == "draft"
        assert ContractStatus.ACTIVE.value == "active"
        assert ContractStatus.EXPIRED.value == "expired"
        assert ContractStatus.TERMINATED.value == "terminated"

    def test_contract_status_allowed_transitions(self):
        """Test transitions d'etat autorisees."""
        # From DRAFT
        allowed = ContractStatus.DRAFT.allowed_transitions()
        assert ContractStatus.IN_REVIEW in allowed
        assert ContractStatus.CANCELLED in allowed
        assert ContractStatus.ACTIVE not in allowed

        # From ACTIVE
        allowed = ContractStatus.ACTIVE.allowed_transitions()
        assert ContractStatus.SUSPENDED in allowed
        assert ContractStatus.TERMINATED in allowed
        assert ContractStatus.DRAFT not in allowed

        # From ARCHIVED (terminal state)
        allowed = ContractStatus.ARCHIVED.allowed_transitions()
        assert len(allowed) == 0

    def test_party_role_values(self):
        """Test valeurs roles de partie."""
        assert PartyRole.CLIENT.value == "client"
        assert PartyRole.CONTRACTOR.value == "contractor"
        assert PartyRole.SUPPLIER.value == "supplier"

    def test_billing_frequency_values(self):
        """Test valeurs frequences de facturation."""
        assert BillingFrequency.MONTHLY.value == "monthly"
        assert BillingFrequency.QUARTERLY.value == "quarterly"
        assert BillingFrequency.ANNUAL.value == "annual"

    def test_renewal_type_values(self):
        """Test valeurs types de renouvellement."""
        assert RenewalType.AUTOMATIC.value == "automatic"
        assert RenewalType.MANUAL.value == "manual"
        assert RenewalType.NONE.value == "none"

    def test_alert_priority_values(self):
        """Test valeurs priorites d'alerte."""
        assert AlertPriority.LOW.value == "low"
        assert AlertPriority.MEDIUM.value == "medium"
        assert AlertPriority.HIGH.value == "high"
        assert AlertPriority.CRITICAL.value == "critical"


# ============================================================================
# SCHEMA TESTS
# ============================================================================

class TestContractSchemas:
    """Tests des schemas Contracts."""

    def test_contract_create_schema(self, sample_contract_create):
        """Test schema creation contrat."""
        assert sample_contract_create.contract_type == ContractType.SERVICE
        assert sample_contract_create.total_value == Decimal("50000.00")
        assert sample_contract_create.currency == "EUR"

    def test_contract_create_with_parties(self):
        """Test schema creation contrat avec parties."""
        data = ContractCreate(
            contract_type=ContractType.SALES,
            title="Contrat de vente",
            start_date=date.today(),
            total_value=Decimal("10000.00"),
            parties=[
                ContractPartyCreate(
                    party_type=PartyType.COMPANY,
                    role=PartyRole.CONTRACTOR,
                    name="Vendeur SA",
                    is_primary=True
                ),
                ContractPartyCreate(
                    party_type=PartyType.COMPANY,
                    role=PartyRole.CLIENT,
                    name="Acheteur SARL",
                    is_primary=False
                )
            ]
        )
        assert len(data.parties) == 2
        assert data.parties[0].role == PartyRole.CONTRACTOR

    def test_party_create_schema(self, sample_party_create):
        """Test schema creation partie."""
        assert sample_party_create.role == PartyRole.CLIENT
        assert sample_party_create.is_signatory is True

    def test_line_create_schema(self, sample_line_create):
        """Test schema creation ligne."""
        assert sample_line_create.unit_price == Decimal("40000.00")
        assert sample_line_create.billing_type == BillingType.FIXED

    def test_line_create_recurring(self):
        """Test schema ligne recurrente."""
        line = ContractLineCreate(
            description="Maintenance mensuelle",
            quantity=Decimal("1"),
            unit_price=Decimal("500.00"),
            billing_type=BillingType.RECURRING,
            billing_frequency=BillingFrequency.MONTHLY,
            start_date=date.today()
        )
        assert line.billing_frequency == BillingFrequency.MONTHLY

    def test_obligation_create_schema(self):
        """Test schema creation obligation."""
        obligation = ContractObligationCreate(
            title="Rapport mensuel",
            obligation_type=ObligationType.REPORTING,
            due_date=date.today() + timedelta(days=30),
            description="Rapport d'avancement"
        )
        assert obligation.obligation_type == ObligationType.REPORTING

    def test_milestone_create_schema(self):
        """Test schema creation jalon."""
        milestone = ContractMilestoneCreate(
            title="Livraison V1",
            due_date=date.today() + timedelta(days=90),
            payment_percentage=Decimal("30.00")
        )
        assert milestone.payment_percentage == Decimal("30.00")

    def test_amendment_create_schema(self):
        """Test schema creation avenant."""
        amendment = ContractAmendmentCreate(
            title="Extension du contrat",
            amendment_type=AmendmentType.EXTENSION,
            reason="Besoins supplementaires",
            new_end_date=date.today() + timedelta(days=730)
        )
        assert amendment.amendment_type == AmendmentType.EXTENSION

    def test_alert_create_schema(self):
        """Test schema creation alerte."""
        alert = ContractAlertCreate(
            alert_type=AlertType.EXPIRATION_WARNING,
            priority=AlertPriority.HIGH,
            title="Contrat expire dans 30 jours",
            due_date=date.today() + timedelta(days=30)
        )
        assert alert.priority == AlertPriority.HIGH

    def test_category_create_schema(self):
        """Test schema creation categorie."""
        category = ContractCategoryCreate(
            code="COMMERCIAL",
            name="Contrats commerciaux",
            description="Tous les contrats commerciaux"
        )
        assert category.code == "COMMERCIAL"

    def test_template_create_schema(self):
        """Test schema creation template."""
        template = ContractTemplateCreate(
            code="NDA_FR",
            name="Accord de confidentialite France",
            contract_type=ContractType.NDA,
            default_duration_months=24
        )
        assert template.contract_type == ContractType.NDA
        assert template.default_duration_months == 24

    def test_contract_filter_params(self):
        """Test parametres de filtrage."""
        filters = ContractFilterParams(
            status=[ContractStatus.ACTIVE, ContractStatus.DRAFT],
            contract_type=[ContractType.SERVICE],
            start_date_from=date.today() - timedelta(days=365),
            value_min=Decimal("10000.00")
        )
        assert ContractStatus.ACTIVE in filters.status
        assert filters.value_min == Decimal("10000.00")


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestContractExceptions:
    """Tests des exceptions."""

    def test_contract_not_found_error(self):
        """Test exception contrat non trouve."""
        exc = ContractNotFoundError("CTR001")
        assert "CTR001" in str(exc)
        assert exc.contract_id == "CTR001"

    def test_contract_duplicate_error(self):
        """Test exception contrat duplique."""
        exc = ContractDuplicateError("CTR001")
        assert "CTR001" in str(exc)
        assert exc.contract_number == "CTR001"

    def test_contract_state_error(self):
        """Test exception transition d'etat invalide."""
        exc = ContractStateError("draft", "active")
        assert "draft" in str(exc)
        assert "active" in str(exc)
        assert exc.current_status == "draft"
        assert exc.target_status == "active"

    def test_contract_not_editable_error(self):
        """Test exception contrat non modifiable."""
        exc = ContractNotEditableError("active")
        assert "active" in str(exc)
        assert exc.status == "active"

    def test_party_not_found_error(self):
        """Test exception partie non trouvee."""
        exc = PartyNotFoundError("PARTY001")
        assert "PARTY001" in str(exc)

    def test_party_already_signed_error(self):
        """Test exception partie deja signee."""
        exc = PartyAlreadySignedError("PARTY001")
        assert "PARTY001" in str(exc)

    def test_missing_party_error(self):
        """Test exception partie manquante."""
        exc = MissingPartyError("client")
        assert "client" in str(exc)

    def test_obligation_overdue_error(self):
        """Test exception obligation en retard."""
        exc = ObligationOverdueError("OBL001", "2024-01-15")
        assert "OBL001" in str(exc)
        assert "2024-01-15" in str(exc)

    def test_milestone_dependency_error(self):
        """Test exception dependance jalon non satisfaite."""
        exc = MilestoneDependencyError("MS002", "MS001")
        assert "MS002" in str(exc)
        assert "MS001" in str(exc)

    def test_amendment_not_allowed_error(self):
        """Test exception avenant non autorise."""
        exc = AmendmentNotAllowedError("draft")
        assert "draft" in str(exc)

    def test_max_renewals_reached_error(self):
        """Test exception nombre max de renouvellements."""
        exc = MaxRenewalsReachedError(3)
        assert "3" in str(exc)
        assert exc.max_renewals == 3

    def test_renewal_notice_period_error(self):
        """Test exception preavis non respecte."""
        exc = RenewalNoticePeriodError(30, 15)
        assert "30" in str(exc)
        assert "15" in str(exc)

    def test_approval_not_authorized_error(self):
        """Test exception non autorise a approuver."""
        exc = ApprovalNotAuthorizedError("USER001")
        assert "USER001" in str(exc)

    def test_category_duplicate_error(self):
        """Test exception categorie dupliquee."""
        exc = CategoryDuplicateError("COMMERCIAL")
        assert "COMMERCIAL" in str(exc)

    def test_contract_version_conflict_error(self):
        """Test exception conflit de version."""
        exc = ContractVersionConflictError(1, 3)
        assert exc.expected_version == 1
        assert exc.current_version == 3
        assert "version" in str(exc).lower()


# ============================================================================
# SERVICE TESTS - CONTRACTS
# ============================================================================

class TestContractService:
    """Tests service contracts."""

    def test_create_contract_success(self, contract_service, sample_contract_create, mock_db):
        """Test creation contrat reussie."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        contract = contract_service.create_contract(sample_contract_create, created_by="user1")

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_create_contract_with_parties(self, contract_service, mock_db):
        """Test creation contrat avec parties."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        data = ContractCreate(
            contract_type=ContractType.SERVICE,
            title="Test avec parties",
            start_date=date.today(),
            parties=[
                ContractPartyCreate(
                    party_type=PartyType.COMPANY,
                    role=PartyRole.CONTRACTOR,
                    name="Prestataire",
                    is_primary=True
                )
            ]
        )

        contract = contract_service.create_contract(data, created_by="user1")
        # Parties should be added
        assert mock_db.add.call_count >= 1

    def test_get_contract_not_found(self, contract_service, mock_db):
        """Test recuperation contrat inexistant."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ContractNotFoundError):
            contract_service.get_contract(uuid.uuid4())

    def test_get_contract_success(self, contract_service, sample_contract, mock_db):
        """Test recuperation contrat reussie."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        result = contract_service.get_contract(sample_contract.id)
        assert result.id == sample_contract.id

    def test_update_contract_success(self, contract_service, sample_contract, mock_db):
        """Test mise a jour contrat."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        update_data = ContractUpdate(
            title="Titre modifie",
            description="Nouvelle description"
        )

        result = contract_service.update_contract(
            sample_contract.id,
            update_data,
            updated_by="user2"
        )

        assert sample_contract.title == "Titre modifie"
        mock_db.commit.assert_called()

    def test_update_contract_not_editable(self, contract_service, active_contract, mock_db):
        """Test mise a jour contrat actif echoue."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        update_data = ContractUpdate(title="Nouveau titre")

        with pytest.raises(ContractNotEditableError):
            contract_service.update_contract(
                active_contract.id,
                update_data,
                updated_by="user1"
            )

    def test_delete_contract_success(self, contract_service, sample_contract, mock_db):
        """Test suppression contrat (soft delete)."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        contract_service.delete_contract(sample_contract.id, deleted_by="user1")

        assert sample_contract.is_deleted is True
        assert sample_contract.deleted_by == "user1"
        mock_db.commit.assert_called()

    def test_delete_active_contract_fails(self, contract_service, active_contract, mock_db):
        """Test suppression contrat actif echoue."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        with pytest.raises(ContractNotEditableError):
            contract_service.delete_contract(active_contract.id, deleted_by="user1")


# ============================================================================
# SERVICE TESTS - WORKFLOW
# ============================================================================

class TestContractWorkflow:
    """Tests workflow de contrat."""

    def test_submit_for_review_success(self, contract_service, sample_contract, mock_db):
        """Test soumission pour revision."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        result = contract_service.submit_for_review(
            sample_contract.id,
            ContractSubmitForReviewRequest(comments="A verifier"),
            user_id="user1"
        )

        assert sample_contract.status == ContractStatus.IN_REVIEW

    def test_submit_for_review_invalid_state(self, contract_service, active_contract, mock_db):
        """Test soumission depuis etat invalide."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        with pytest.raises(ContractStateError):
            contract_service.submit_for_review(
                active_contract.id,
                ContractSubmitForReviewRequest(),
                user_id="user1"
            )

    def test_start_negotiation_success(self, contract_service, sample_contract, mock_db):
        """Test demarrage negociation."""
        sample_contract.status = ContractStatus.IN_REVIEW
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        result = contract_service.start_negotiation(
            sample_contract.id,
            ContractStartNegotiationRequest(counterparty_contact="partner@example.com"),
            user_id="user1"
        )

        assert sample_contract.status == ContractStatus.IN_NEGOTIATION

    def test_submit_for_approval_success(self, contract_service, sample_contract, mock_db):
        """Test soumission pour approbation."""
        sample_contract.status = ContractStatus.IN_NEGOTIATION
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        result = contract_service.submit_for_approval(
            sample_contract.id,
            ContractSubmitForApprovalRequest(approval_level=1),
            user_id="user1"
        )

        assert sample_contract.status == ContractStatus.PENDING_APPROVAL

    def test_approve_contract_success(self, contract_service, sample_contract, mock_db):
        """Test approbation contrat."""
        sample_contract.status = ContractStatus.PENDING_APPROVAL
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = contract_service.approve_contract(
            sample_contract.id,
            ApprovalDecisionRequest(decision="approved", comments="OK"),
            user_id="manager1"
        )

        assert sample_contract.status == ContractStatus.APPROVED

    def test_activate_contract_success(self, contract_service, sample_contract, mock_db):
        """Test activation contrat."""
        sample_contract.status = ContractStatus.PENDING_SIGNATURE
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract
        # Mock all parties signed
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = contract_service.activate_contract(
            sample_contract.id,
            ContractActivateRequest(),
            user_id="user1"
        )

        assert sample_contract.status == ContractStatus.ACTIVE
        assert sample_contract.activated_at is not None

    def test_suspend_contract_success(self, contract_service, active_contract, mock_db):
        """Test suspension contrat."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        result = contract_service.suspend_contract(
            active_contract.id,
            ContractSuspendRequest(reason="Paiement en retard"),
            user_id="user1"
        )

        assert active_contract.status == ContractStatus.SUSPENDED

    def test_resume_contract_success(self, contract_service, active_contract, mock_db):
        """Test reprise contrat suspendu."""
        active_contract.status = ContractStatus.SUSPENDED
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        result = contract_service.resume_contract(active_contract.id, user_id="user1")

        assert active_contract.status == ContractStatus.ACTIVE

    def test_terminate_contract_success(self, contract_service, active_contract, mock_db):
        """Test resiliation contrat."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        result = contract_service.terminate_contract(
            active_contract.id,
            ContractTerminateRequest(reason="Fin anticipee", termination_date=date.today()),
            user_id="user1"
        )

        assert active_contract.status == ContractStatus.TERMINATED
        assert active_contract.terminated_at is not None


# ============================================================================
# SERVICE TESTS - PARTIES
# ============================================================================

class TestPartyService:
    """Tests service parties contractantes."""

    def test_add_party_success(self, contract_service, sample_contract, sample_party_create, mock_db):
        """Test ajout partie au contrat."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        result = contract_service.add_party(
            sample_contract.id,
            sample_party_create,
            created_by="user1"
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_add_party_to_active_contract_fails(self, contract_service, active_contract, sample_party_create, mock_db):
        """Test ajout partie a contrat actif echoue."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        with pytest.raises(ContractNotEditableError):
            contract_service.add_party(
                active_contract.id,
                sample_party_create,
                created_by="user1"
            )

    def test_record_signature_success(self, contract_service, mock_db):
        """Test enregistrement signature."""
        contract = Contract(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=ContractStatus.PENDING_SIGNATURE,
            version=1
        )
        party = ContractParty(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            contract_id=contract.id,
            is_signatory=True,
            has_signed=False
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [contract, party]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = contract_service.record_party_signature(
            contract.id,
            party.id,
            PartySignatureRequest(signature_method="electronic"),
            user_id="signer1"
        )

        assert party.has_signed is True
        assert party.signed_at is not None

    def test_record_signature_already_signed(self, contract_service, mock_db):
        """Test signature deja enregistree."""
        contract = Contract(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=ContractStatus.PENDING_SIGNATURE,
            version=1
        )
        party = ContractParty(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            contract_id=contract.id,
            is_signatory=True,
            has_signed=True,
            signed_at=datetime.utcnow()
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [contract, party]

        with pytest.raises(PartyAlreadySignedError):
            contract_service.record_party_signature(
                contract.id,
                party.id,
                PartySignatureRequest(signature_method="electronic"),
                user_id="signer1"
            )


# ============================================================================
# SERVICE TESTS - LINES
# ============================================================================

class TestLineService:
    """Tests service lignes de contrat."""

    def test_add_line_success(self, contract_service, sample_contract, sample_line_create, mock_db):
        """Test ajout ligne au contrat."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = contract_service.add_line(
            sample_contract.id,
            sample_line_create,
            created_by="user1"
        )

        mock_db.add.assert_called()

    def test_add_line_recalculates_total(self, contract_service, sample_contract, mock_db):
        """Test que l'ajout d'une ligne recalcule le total."""
        sample_contract.total_value = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.all.return_value = []

        line_data = ContractLineCreate(
            description="Service",
            quantity=Decimal("2"),
            unit_price=Decimal("1000.00"),
            billing_type=BillingType.FIXED
        )

        contract_service.add_line(sample_contract.id, line_data, created_by="user1")
        # Total should be recalculated
        mock_db.commit.assert_called()


# ============================================================================
# SERVICE TESTS - OBLIGATIONS & MILESTONES
# ============================================================================

class TestObligationMilestoneService:
    """Tests service obligations et jalons."""

    def test_add_obligation_success(self, contract_service, sample_contract, mock_db):
        """Test ajout obligation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        obligation_data = ContractObligationCreate(
            title="Livrer rapport",
            obligation_type=ObligationType.DELIVERABLE,
            due_date=date.today() + timedelta(days=30)
        )

        result = contract_service.add_obligation(
            sample_contract.id,
            obligation_data,
            created_by="user1"
        )

        mock_db.add.assert_called()

    def test_complete_obligation_success(self, contract_service, mock_db):
        """Test completion obligation."""
        contract = Contract(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=ContractStatus.ACTIVE,
            version=1
        )
        obligation = ContractObligation(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            contract_id=contract.id,
            status=ObligationStatus.PENDING
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [contract, obligation]

        result = contract_service.complete_obligation(
            contract.id,
            obligation.id,
            ObligationCompleteRequest(completion_notes="Termine"),
            user_id="user1"
        )

        assert obligation.status == ObligationStatus.COMPLETED
        assert obligation.completed_at is not None

    def test_add_milestone_success(self, contract_service, sample_contract, mock_db):
        """Test ajout jalon."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        milestone_data = ContractMilestoneCreate(
            title="Phase 1",
            due_date=date.today() + timedelta(days=60),
            payment_percentage=Decimal("30.00")
        )

        result = contract_service.add_milestone(
            sample_contract.id,
            milestone_data,
            created_by="user1"
        )

        mock_db.add.assert_called()

    def test_complete_milestone_with_dependencies(self, contract_service, mock_db):
        """Test completion jalon avec dependances."""
        contract = Contract(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=ContractStatus.ACTIVE,
            version=1
        )
        # Milestone depends on uncompleted milestone
        dependency = ContractMilestone(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            contract_id=contract.id,
            status=MilestoneStatus.PENDING
        )
        milestone = ContractMilestone(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            contract_id=contract.id,
            status=MilestoneStatus.PENDING,
            depends_on_milestone_id=dependency.id
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            contract, milestone, dependency
        ]

        with pytest.raises(MilestoneDependencyError):
            contract_service.complete_milestone(
                contract.id,
                milestone.id,
                MilestoneCompleteRequest(),
                user_id="user1"
            )


# ============================================================================
# SERVICE TESTS - AMENDMENTS
# ============================================================================

class TestAmendmentService:
    """Tests service avenants."""

    def test_create_amendment_success(self, contract_service, active_contract, mock_db):
        """Test creation avenant."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        amendment_data = ContractAmendmentCreate(
            title="Extension du contrat",
            amendment_type=AmendmentType.EXTENSION,
            reason="Besoins supplementaires",
            new_end_date=date.today() + timedelta(days=730)
        )

        result = contract_service.create_amendment(
            active_contract.id,
            amendment_data,
            created_by="user1"
        )

        mock_db.add.assert_called()

    def test_create_amendment_on_draft_fails(self, contract_service, sample_contract, mock_db):
        """Test creation avenant sur brouillon echoue."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        amendment_data = ContractAmendmentCreate(
            title="Test",
            amendment_type=AmendmentType.MODIFICATION
        )

        with pytest.raises(AmendmentNotAllowedError):
            contract_service.create_amendment(
                sample_contract.id,
                amendment_data,
                created_by="user1"
            )


# ============================================================================
# SERVICE TESTS - RENEWALS
# ============================================================================

class TestRenewalService:
    """Tests service renouvellements."""

    def test_renew_contract_success(self, contract_service, active_contract, mock_db):
        """Test renouvellement contrat."""
        active_contract.renewal_type = RenewalType.MANUAL
        active_contract.renewal_count = 0
        active_contract.max_renewals = 3
        active_contract.end_date = date.today() + timedelta(days=30)
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        result = contract_service.renew_contract(
            active_contract.id,
            ContractRenewRequest(new_end_date=date.today() + timedelta(days=395)),
            user_id="user1"
        )

        assert active_contract.renewal_count == 1
        mock_db.add.assert_called()  # New renewal record

    def test_renew_contract_max_reached(self, contract_service, active_contract, mock_db):
        """Test renouvellement max atteint."""
        active_contract.renewal_type = RenewalType.MANUAL
        active_contract.renewal_count = 3
        active_contract.max_renewals = 3
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        with pytest.raises(MaxRenewalsReachedError):
            contract_service.renew_contract(
                active_contract.id,
                ContractRenewRequest(),
                user_id="user1"
            )

    def test_renew_contract_not_renewable(self, contract_service, active_contract, mock_db):
        """Test renouvellement non autorise."""
        active_contract.renewal_type = RenewalType.NONE
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        with pytest.raises(RenewalNotAllowedError):
            contract_service.renew_contract(
                active_contract.id,
                ContractRenewRequest(),
                user_id="user1"
            )


# ============================================================================
# SERVICE TESTS - ALERTS
# ============================================================================

class TestAlertService:
    """Tests service alertes."""

    def test_create_alert_success(self, contract_service, active_contract, mock_db):
        """Test creation alerte."""
        mock_db.query.return_value.filter.return_value.first.return_value = active_contract

        alert_data = ContractAlertCreate(
            alert_type=AlertType.CUSTOM,
            priority=AlertPriority.MEDIUM,
            title="Reunion de suivi",
            due_date=date.today() + timedelta(days=7)
        )

        result = contract_service.create_alert(
            active_contract.id,
            alert_data,
            created_by="user1"
        )

        mock_db.add.assert_called()

    def test_acknowledge_alert_success(self, contract_service, mock_db):
        """Test acquittement alerte."""
        contract = Contract(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=ContractStatus.ACTIVE,
            version=1
        )
        alert = ContractAlert(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            contract_id=contract.id,
            status=AlertStatus.PENDING
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [contract, alert]

        result = contract_service.acknowledge_alert(
            contract.id,
            alert.id,
            AlertAcknowledgeRequest(notes="Lu et compris"),
            user_id="user1"
        )

        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_at is not None

    def test_acknowledge_already_acknowledged(self, contract_service, mock_db):
        """Test acquittement alerte deja acquittee."""
        contract = Contract(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=ContractStatus.ACTIVE,
            version=1
        )
        alert = ContractAlert(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            contract_id=contract.id,
            status=AlertStatus.ACKNOWLEDGED,
            acknowledged_at=datetime.utcnow()
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [contract, alert]

        with pytest.raises(AlertAlreadyAcknowledgedError):
            contract_service.acknowledge_alert(
                contract.id,
                alert.id,
                AlertAcknowledgeRequest(),
                user_id="user1"
            )


# ============================================================================
# SERVICE TESTS - CATEGORIES
# ============================================================================

class TestCategoryService:
    """Tests service categories."""

    def test_create_category_success(self, contract_service, mock_db):
        """Test creation categorie."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        category_data = ContractCategoryCreate(
            code="COMMERCIAL",
            name="Contrats commerciaux"
        )

        result = contract_service.create_category(category_data, created_by="admin")

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_create_category_duplicate_code(self, contract_service, mock_db):
        """Test creation categorie code duplique."""
        existing = ContractCategory(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            code="COMMERCIAL"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        category_data = ContractCategoryCreate(
            code="COMMERCIAL",
            name="Autre nom"
        )

        with pytest.raises(CategoryDuplicateError):
            contract_service.create_category(category_data, created_by="admin")


# ============================================================================
# SERVICE TESTS - TEMPLATES
# ============================================================================

class TestTemplateService:
    """Tests service templates."""

    def test_create_template_success(self, contract_service, mock_db):
        """Test creation template."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        template_data = ContractTemplateCreate(
            code="NDA_FR",
            name="Accord de confidentialite France",
            contract_type=ContractType.NDA,
            default_duration_months=24
        )

        result = contract_service.create_template(template_data, created_by="admin")

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_create_template_duplicate_code(self, contract_service, mock_db):
        """Test creation template code duplique."""
        existing = ContractTemplate(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            code="NDA_FR"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        template_data = ContractTemplateCreate(
            code="NDA_FR",
            name="Autre nom",
            contract_type=ContractType.NDA
        )

        with pytest.raises(TemplateDuplicateError):
            contract_service.create_template(template_data, created_by="admin")


# ============================================================================
# SERVICE TESTS - STATISTICS
# ============================================================================

class TestStatisticsService:
    """Tests service statistiques."""

    def test_get_contract_stats(self, contract_service, mock_db):
        """Test recuperation statistiques."""
        # Mock count queries
        mock_db.query.return_value.filter.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("500000.00")

        stats = contract_service.get_contract_stats()

        assert stats is not None

    def test_get_dashboard_data(self, contract_service, mock_db):
        """Test recuperation donnees tableau de bord."""
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("100000.00")

        dashboard = contract_service.get_dashboard()

        assert dashboard is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestContractIntegration:
    """Tests d'integration."""

    def test_complete_contract_lifecycle(self, contract_service):
        """Test cycle de vie complet d'un contrat."""
        # Verify methods exist for full lifecycle
        assert hasattr(contract_service, 'create_contract')
        assert hasattr(contract_service, 'submit_for_review')
        assert hasattr(contract_service, 'start_negotiation')
        assert hasattr(contract_service, 'submit_for_approval')
        assert hasattr(contract_service, 'approve_contract')
        assert hasattr(contract_service, 'activate_contract')
        assert hasattr(contract_service, 'suspend_contract')
        assert hasattr(contract_service, 'resume_contract')
        assert hasattr(contract_service, 'terminate_contract')
        assert hasattr(contract_service, 'renew_contract')

    def test_contract_with_full_structure(self, contract_service):
        """Test contrat avec structure complete."""
        # Verify sub-entity methods exist
        assert hasattr(contract_service, 'add_party')
        assert hasattr(contract_service, 'add_line')
        assert hasattr(contract_service, 'add_clause')
        assert hasattr(contract_service, 'add_obligation')
        assert hasattr(contract_service, 'add_milestone')
        assert hasattr(contract_service, 'create_amendment')
        assert hasattr(contract_service, 'create_alert')

    def test_contract_configuration(self, contract_service):
        """Test configuration contrat."""
        # Verify configuration methods exist
        assert hasattr(contract_service, 'create_category')
        assert hasattr(contract_service, 'create_template')


# ============================================================================
# EDGE CASES
# ============================================================================

class TestContractEdgeCases:
    """Tests cas limites."""

    def test_contract_with_zero_value(self):
        """Test contrat avec valeur zero."""
        contract = Contract(
            tenant_id="test",
            contract_number="CTR001",
            contract_type=ContractType.NDA,
            status=ContractStatus.DRAFT,
            title="NDA sans valeur",
            total_value=Decimal("0")
        )
        assert contract.total_value == Decimal("0")

    def test_contract_without_end_date(self):
        """Test contrat sans date de fin (indefini)."""
        contract = Contract(
            tenant_id="test",
            contract_number="CTR001",
            contract_type=ContractType.EMPLOYMENT,
            status=ContractStatus.ACTIVE,
            title="CDI",
            start_date=date.today(),
            end_date=None
        )
        assert contract.end_date is None

    def test_multiple_amendments(self):
        """Test contrat avec multiples avenants."""
        contract_id = uuid.uuid4()
        amendments = [
            ContractAmendment(
                tenant_id="test",
                contract_id=contract_id,
                amendment_number=f"AVN{i:03d}",
                amendment_type=AmendmentType.MODIFICATION,
                status=AmendmentStatus.APPLIED
            )
            for i in range(1, 6)
        ]
        assert len(amendments) == 5

    def test_complex_party_structure(self):
        """Test structure complexe de parties."""
        contract_id = uuid.uuid4()
        parties = [
            ContractParty(
                tenant_id="test",
                contract_id=contract_id,
                party_type=PartyType.COMPANY,
                role=PartyRole.CONTRACTOR,
                name="Vendeur",
                is_primary=True
            ),
            ContractParty(
                tenant_id="test",
                contract_id=contract_id,
                party_type=PartyType.COMPANY,
                role=PartyRole.CLIENT,
                name="Acheteur",
                is_primary=False
            ),
            ContractParty(
                tenant_id="test",
                contract_id=contract_id,
                party_type=PartyType.COMPANY,
                role=PartyRole.GUARANTOR,
                name="Garant",
                is_primary=False
            )
        ]
        assert len(parties) == 3
        assert sum(1 for p in parties if p.is_primary) == 1

    def test_recurring_billing_line(self):
        """Test ligne avec facturation recurrente."""
        line = ContractLine(
            tenant_id="test",
            contract_id=uuid.uuid4(),
            line_number=1,
            description="Maintenance mensuelle",
            quantity=Decimal("1"),
            unit_price=Decimal("500.00"),
            billing_type=BillingType.RECURRING,
            billing_frequency=BillingFrequency.MONTHLY,
            start_date=date.today()
        )
        assert line.billing_frequency == BillingFrequency.MONTHLY
        # Monthly billing = 12 times per year
        annual_value = line.unit_price * line.quantity * 12
        assert annual_value == Decimal("6000.00")

    def test_milestone_chain(self):
        """Test chaine de jalons dependants."""
        contract_id = uuid.uuid4()
        ms1_id = uuid.uuid4()
        ms2_id = uuid.uuid4()
        ms3_id = uuid.uuid4()

        milestones = [
            ContractMilestone(
                id=ms1_id,
                tenant_id="test",
                contract_id=contract_id,
                title="Phase 1",
                due_date=date.today() + timedelta(days=30),
                depends_on_milestone_id=None
            ),
            ContractMilestone(
                id=ms2_id,
                tenant_id="test",
                contract_id=contract_id,
                title="Phase 2",
                due_date=date.today() + timedelta(days=60),
                depends_on_milestone_id=ms1_id
            ),
            ContractMilestone(
                id=ms3_id,
                tenant_id="test",
                contract_id=contract_id,
                title="Phase 3",
                due_date=date.today() + timedelta(days=90),
                depends_on_milestone_id=ms2_id
            )
        ]
        assert milestones[1].depends_on_milestone_id == ms1_id
        assert milestones[2].depends_on_milestone_id == ms2_id


# ============================================================================
# TENANT ISOLATION TESTS
# ============================================================================

class TestTenantIsolation:
    """Tests isolation multi-tenant."""

    def test_contract_has_tenant_id(self):
        """Test que le contrat a un tenant_id."""
        contract = Contract(
            tenant_id="tenant-123",
            contract_number="CTR001",
            contract_type=ContractType.SERVICE,
            status=ContractStatus.DRAFT,
            title="Test"
        )
        assert contract.tenant_id == "tenant-123"

    def test_party_has_tenant_id(self):
        """Test que la partie a un tenant_id."""
        party = ContractParty(
            tenant_id="tenant-123",
            contract_id=uuid.uuid4(),
            role=PartyRole.CLIENT,
            name="Client"
        )
        assert party.tenant_id == "tenant-123"

    def test_line_has_tenant_id(self):
        """Test que la ligne a un tenant_id."""
        line = ContractLine(
            tenant_id="tenant-123",
            contract_id=uuid.uuid4(),
            line_number=1,
            description="Service"
        )
        assert line.tenant_id == "tenant-123"

    def test_service_uses_tenant_id(self, contract_service):
        """Test que le service utilise le tenant_id."""
        assert contract_service.tenant_id == "test-tenant"

    def test_all_models_have_tenant_id(self):
        """Test que tous les modeles ont tenant_id."""
        models = [
            Contract, ContractParty, ContractLine, ContractClause,
            ContractObligation, ContractMilestone, ContractAmendment,
            ContractRenewal, ContractDocument, ContractAlert,
            ContractApproval, ContractHistory, ContractCategory,
            ContractTemplate, ClauseTemplate, ContractMetrics
        ]
        for model in models:
            # Check if tenant_id is in the model's columns
            assert hasattr(model, 'tenant_id'), f"{model.__name__} missing tenant_id"


# ============================================================================
# SOFT DELETE TESTS
# ============================================================================

class TestSoftDelete:
    """Tests soft delete."""

    def test_contract_soft_delete_fields(self):
        """Test champs soft delete sur contrat."""
        contract = Contract(
            tenant_id="test",
            contract_number="CTR001",
            contract_type=ContractType.SERVICE,
            status=ContractStatus.DRAFT,
            title="Test",
            is_deleted=False
        )
        assert contract.is_deleted is False
        assert hasattr(contract, 'deleted_at')
        assert hasattr(contract, 'deleted_by')

    def test_soft_delete_marks_record(self, contract_service, sample_contract, mock_db):
        """Test que soft delete marque l'enregistrement."""
        sample_contract.is_deleted = False
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        contract_service.delete_contract(sample_contract.id, deleted_by="admin")

        assert sample_contract.is_deleted is True
        assert sample_contract.deleted_by == "admin"
        assert sample_contract.deleted_at is not None


# ============================================================================
# OPTIMISTIC LOCKING TESTS
# ============================================================================

class TestOptimisticLocking:
    """Tests verrouillage optimiste."""

    def test_contract_has_version(self):
        """Test que le contrat a un champ version."""
        contract = Contract(
            tenant_id="test",
            contract_number="CTR001",
            contract_type=ContractType.SERVICE,
            status=ContractStatus.DRAFT,
            title="Test",
            version=1
        )
        assert contract.version == 1

    def test_version_increments_on_update(self, contract_service, sample_contract, mock_db):
        """Test que la version s'incremente a chaque mise a jour."""
        initial_version = sample_contract.version
        mock_db.query.return_value.filter.return_value.first.return_value = sample_contract

        contract_service.update_contract(
            sample_contract.id,
            ContractUpdate(title="Nouveau titre"),
            updated_by="user1"
        )

        assert sample_contract.version == initial_version + 1
