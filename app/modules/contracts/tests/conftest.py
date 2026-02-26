"""
AZALS MODULE CONTRACTS - Test Configuration
============================================

Fixtures partagees pour les tests du module Contracts.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
import uuid

from app.modules.contracts.models import (
    Contract, ContractParty, ContractLine, ContractClause,
    ContractObligation, ContractMilestone, ContractAmendment,
    ContractCategory, ContractTemplate, ClauseTemplate,
    ContractType, ContractStatus, PartyType, PartyRole,
    BillingFrequency, BillingType, RenewalType,
    ObligationType, ObligationStatus, MilestoneStatus,
    AmendmentType, AmendmentStatus, AlertType, AlertPriority
)
from app.modules.contracts.service import ContractService


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def tenant_id():
    """Tenant ID for tests."""
    return "test-tenant-001"


# ============================================================================
# SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def contract_service(mock_db, tenant_id):
    """Contract service instance."""
    return ContractService(mock_db, tenant_id)


# ============================================================================
# MODEL FIXTURES - CONTRACTS
# ============================================================================

@pytest.fixture
def draft_contract(tenant_id):
    """Draft contract instance."""
    return Contract(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_number="CTR202401-00001",
        contract_type=ContractType.SERVICE,
        status=ContractStatus.DRAFT,
        title="Contrat de service - Brouillon",
        description="Description du contrat",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        total_value=Decimal("50000.00"),
        currency="EUR",
        payment_terms="30 jours net",
        version=1,
        is_deleted=False,
        created_at=datetime.utcnow(),
        created_by="user1"
    )


@pytest.fixture
def active_contract(tenant_id):
    """Active contract instance."""
    return Contract(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_number="CTR202401-00002",
        contract_type=ContractType.SERVICE,
        status=ContractStatus.ACTIVE,
        title="Contrat de service - Actif",
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=335),
        total_value=Decimal("100000.00"),
        currency="EUR",
        renewal_type=RenewalType.MANUAL,
        renewal_count=0,
        max_renewals=3,
        version=3,
        is_deleted=False,
        activated_at=datetime.utcnow() - timedelta(days=30),
        created_at=datetime.utcnow() - timedelta(days=60),
        created_by="user1"
    )


@pytest.fixture
def subscription_contract(tenant_id):
    """Subscription contract instance."""
    return Contract(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_number="CTR202401-00003",
        contract_type=ContractType.SUBSCRIPTION,
        status=ContractStatus.ACTIVE,
        title="Abonnement SaaS",
        start_date=date.today() - timedelta(days=180),
        end_date=date.today() + timedelta(days=185),
        total_value=Decimal("12000.00"),
        currency="EUR",
        renewal_type=RenewalType.AUTOMATIC,
        auto_renew=True,
        renewal_notice_days=30,
        version=5,
        is_deleted=False
    )


@pytest.fixture
def expired_contract(tenant_id):
    """Expired contract instance."""
    return Contract(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_number="CTR202301-00001",
        contract_type=ContractType.SERVICE,
        status=ContractStatus.EXPIRED,
        title="Contrat expire",
        start_date=date.today() - timedelta(days=400),
        end_date=date.today() - timedelta(days=35),
        total_value=Decimal("25000.00"),
        currency="EUR",
        version=2,
        is_deleted=False,
        expired_at=datetime.utcnow() - timedelta(days=35)
    )


# ============================================================================
# MODEL FIXTURES - PARTIES
# ============================================================================

@pytest.fixture
def client_party(tenant_id, draft_contract):
    """Client party instance."""
    return ContractParty(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=draft_contract.id,
        party_type=PartyType.COMPANY,
        role=PartyRole.CLIENT,
        name="Entreprise Cliente SA",
        legal_name="Entreprise Cliente SA",
        registration_number="123456789",
        vat_number="FR12345678901",
        email="contact@client.com",
        phone="+33 1 23 45 67 89",
        address="1 rue du Client, 75001 Paris",
        is_primary=True,
        is_signatory=True,
        has_signed=False,
        version=1,
        is_deleted=False
    )


@pytest.fixture
def contractor_party(tenant_id, draft_contract):
    """Contractor party instance."""
    return ContractParty(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=draft_contract.id,
        party_type=PartyType.COMPANY,
        role=PartyRole.CONTRACTOR,
        name="Prestataire SARL",
        email="contact@prestataire.com",
        is_primary=False,
        is_signatory=True,
        has_signed=False,
        version=1,
        is_deleted=False
    )


# ============================================================================
# MODEL FIXTURES - LINES
# ============================================================================

@pytest.fixture
def fixed_line(tenant_id, draft_contract):
    """Fixed price line instance."""
    return ContractLine(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=draft_contract.id,
        line_number=1,
        description="Developpement application web",
        quantity=Decimal("1"),
        unit_price=Decimal("40000.00"),
        discount_percent=Decimal("0"),
        tax_rate=Decimal("20.00"),
        total_ht=Decimal("40000.00"),
        total_ttc=Decimal("48000.00"),
        billing_type=BillingType.FIXED,
        billing_frequency=BillingFrequency.ONCE,
        version=1,
        is_deleted=False
    )


@pytest.fixture
def recurring_line(tenant_id, subscription_contract):
    """Recurring billing line instance."""
    return ContractLine(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=subscription_contract.id,
        line_number=1,
        description="Abonnement mensuel",
        quantity=Decimal("1"),
        unit_price=Decimal("1000.00"),
        tax_rate=Decimal("20.00"),
        total_ht=Decimal("1000.00"),
        total_ttc=Decimal("1200.00"),
        billing_type=BillingType.RECURRING,
        billing_frequency=BillingFrequency.MONTHLY,
        start_date=date.today() - timedelta(days=180),
        version=1,
        is_deleted=False
    )


# ============================================================================
# MODEL FIXTURES - OBLIGATIONS & MILESTONES
# ============================================================================

@pytest.fixture
def pending_obligation(tenant_id, active_contract):
    """Pending obligation instance."""
    return ContractObligation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=active_contract.id,
        title="Livraison rapport mensuel",
        description="Rapport d'avancement projet",
        obligation_type=ObligationType.REPORTING,
        status=ObligationStatus.PENDING,
        due_date=date.today() + timedelta(days=15),
        responsible_party_id=None,
        version=1,
        is_deleted=False
    )


@pytest.fixture
def pending_milestone(tenant_id, active_contract):
    """Pending milestone instance."""
    return ContractMilestone(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=active_contract.id,
        title="Phase 1 - Specifications",
        description="Livraison specifications techniques",
        due_date=date.today() + timedelta(days=30),
        status=MilestoneStatus.PENDING,
        payment_percentage=Decimal("20.00"),
        payment_amount=Decimal("20000.00"),
        version=1,
        is_deleted=False
    )


@pytest.fixture
def completed_milestone(tenant_id, active_contract):
    """Completed milestone instance."""
    return ContractMilestone(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=active_contract.id,
        title="Phase 0 - Kick-off",
        description="Reunion de lancement",
        due_date=date.today() - timedelta(days=25),
        status=MilestoneStatus.COMPLETED,
        completed_at=datetime.utcnow() - timedelta(days=27),
        payment_percentage=Decimal("10.00"),
        payment_amount=Decimal("10000.00"),
        version=2,
        is_deleted=False
    )


# ============================================================================
# MODEL FIXTURES - AMENDMENTS
# ============================================================================

@pytest.fixture
def draft_amendment(tenant_id, active_contract):
    """Draft amendment instance."""
    return ContractAmendment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=active_contract.id,
        amendment_number="AVN202401-00001",
        title="Extension du contrat",
        description="Extension de 6 mois",
        amendment_type=AmendmentType.EXTENSION,
        status=AmendmentStatus.DRAFT,
        new_end_date=active_contract.end_date + timedelta(days=180),
        version=1,
        is_deleted=False
    )


# ============================================================================
# MODEL FIXTURES - CATEGORIES & TEMPLATES
# ============================================================================

@pytest.fixture
def service_category(tenant_id):
    """Service category instance."""
    return ContractCategory(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="SERVICE",
        name="Contrats de service",
        description="Prestations de services",
        is_active=True,
        version=1,
        is_deleted=False
    )


@pytest.fixture
def nda_template(tenant_id):
    """NDA template instance."""
    return ContractTemplate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="NDA_FR",
        name="Accord de confidentialite France",
        description="Template NDA standard pour la France",
        contract_type=ContractType.NDA,
        default_duration_months=24,
        is_active=True,
        version=1,
        is_deleted=False
    )


@pytest.fixture
def confidentiality_clause_template(tenant_id):
    """Confidentiality clause template instance."""
    return ClauseTemplate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="CONFIDENTIALITY_FR",
        title="Clause de confidentialite",
        content="Les parties s'engagent a maintenir la confidentialite...",
        is_mandatory=True,
        is_active=True,
        version=1,
        is_deleted=False
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_contract_with_parties(tenant_id, num_parties=2):
    """Create a contract with parties."""
    contract = Contract(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_number="CTR-TEST-001",
        contract_type=ContractType.SERVICE,
        status=ContractStatus.DRAFT,
        title="Test Contract with Parties",
        version=1
    )

    parties = []
    roles = [PartyRole.CONTRACTOR, PartyRole.CLIENT, PartyRole.PARTNER]
    for i in range(num_parties):
        party = ContractParty(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            contract_id=contract.id,
            role=roles[i % len(roles)],
            name=f"Party {i+1}",
            is_primary=(i == 0),
            is_signatory=True,
            has_signed=False,
            version=1
        )
        parties.append(party)

    return contract, parties


def create_contract_with_lines(tenant_id, num_lines=3):
    """Create a contract with lines."""
    contract = Contract(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_number="CTR-TEST-002",
        contract_type=ContractType.SERVICE,
        status=ContractStatus.DRAFT,
        title="Test Contract with Lines",
        total_value=Decimal("0"),
        version=1
    )

    lines = []
    total = Decimal("0")
    for i in range(num_lines):
        unit_price = Decimal(f"{(i+1) * 1000}.00")
        quantity = Decimal("1")
        line_total = unit_price * quantity
        total += line_total

        line = ContractLine(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            contract_id=contract.id,
            line_number=i + 1,
            description=f"Service {i+1}",
            quantity=quantity,
            unit_price=unit_price,
            total_ht=line_total,
            version=1
        )
        lines.append(line)

    contract.total_value = total
    return contract, lines


def create_milestone_chain(tenant_id, contract_id, num_milestones=3):
    """Create a chain of dependent milestones."""
    milestones = []
    prev_id = None

    for i in range(num_milestones):
        milestone = ContractMilestone(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            contract_id=contract_id,
            title=f"Phase {i+1}",
            due_date=date.today() + timedelta(days=30 * (i+1)),
            status=MilestoneStatus.PENDING,
            depends_on_milestone_id=prev_id,
            payment_percentage=Decimal(f"{100 // num_milestones}"),
            version=1
        )
        milestones.append(milestone)
        prev_id = milestone.id

    return milestones
