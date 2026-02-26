"""
Tests for Complaints schemas.
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.complaints.models import (
    ComplaintCategory,
    ComplaintChannel,
    ComplaintPriority,
    ComplaintStatus,
    EscalationLevel,
    ResolutionType,
    SatisfactionRating,
)
from app.modules.complaints.schemas import (
    ActionComplete,
    ActionCreate,
    AgentCreate,
    AttachmentCreate,
    CategoryConfigCreate,
    ComplaintAssign,
    ComplaintClose,
    ComplaintCreate,
    ComplaintEscalate,
    ComplaintFilter,
    ComplaintReopen,
    ComplaintResolve,
    ComplaintStatusChange,
    ComplaintUpdate,
    ExchangeCreate,
    SatisfactionSubmit,
    SLAPolicyCreate,
    TeamCreate,
    TemplateCreate,
    TemplateRender,
)


class TestComplaintCreate:
    """Tests for ComplaintCreate schema."""

    def test_valid_complaint_create(self):
        """Test valid complaint creation."""
        data = ComplaintCreate(
            subject="Test complaint",
            description="This is a test complaint description that is long enough",
            category=ComplaintCategory.BILLING,
            customer_email="test@example.com"
        )

        assert data.subject == "Test complaint"
        assert data.category == ComplaintCategory.BILLING
        assert data.customer_email == "test@example.com"

    def test_subject_min_length(self):
        """Test subject minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintCreate(
                subject="Test",  # Too short (min 5)
                description="This is a test complaint description",
                category=ComplaintCategory.BILLING,
                customer_email="test@example.com"
            )

        assert "subject" in str(exc_info.value)

    def test_description_min_length(self):
        """Test description minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintCreate(
                subject="Test complaint",
                description="Short",  # Too short (min 10)
                category=ComplaintCategory.BILLING,
                customer_email="test@example.com"
            )

        assert "description" in str(exc_info.value)

    def test_valid_email_required(self):
        """Test email validation."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintCreate(
                subject="Test complaint",
                description="This is a test complaint description",
                category=ComplaintCategory.BILLING,
                customer_email="invalid-email"
            )

        assert "customer_email" in str(exc_info.value)

    def test_default_values(self):
        """Test default values are set correctly."""
        data = ComplaintCreate(
            subject="Test complaint",
            description="This is a test complaint description",
            category=ComplaintCategory.OTHER,
            customer_email="test@example.com"
        )

        assert data.priority == ComplaintPriority.MEDIUM
        assert data.channel == ComplaintChannel.EMAIL
        assert data.currency == "EUR"

    def test_disputed_amount_positive(self):
        """Test disputed amount must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintCreate(
                subject="Test complaint",
                description="This is a test complaint description",
                category=ComplaintCategory.BILLING,
                customer_email="test@example.com",
                disputed_amount=Decimal("-100.00")
            )

        assert "disputed_amount" in str(exc_info.value)


class TestComplaintUpdate:
    """Tests for ComplaintUpdate schema."""

    def test_partial_update(self):
        """Test partial update with only some fields."""
        data = ComplaintUpdate(
            subject="Updated subject"
        )

        assert data.subject == "Updated subject"
        assert data.description is None
        assert data.priority is None

    def test_full_update(self):
        """Test full update with all fields."""
        data = ComplaintUpdate(
            subject="Updated subject",
            description="Updated description",
            priority=ComplaintPriority.HIGH,
            status=ComplaintStatus.IN_PROGRESS
        )

        assert data.subject == "Updated subject"
        assert data.priority == ComplaintPriority.HIGH
        assert data.status == ComplaintStatus.IN_PROGRESS


class TestComplaintAssign:
    """Tests for ComplaintAssign schema."""

    def test_valid_assignment(self):
        """Test valid assignment."""
        agent_id = uuid4()
        team_id = uuid4()

        data = ComplaintAssign(
            agent_id=agent_id,
            team_id=team_id,
            note="Assigning to billing team"
        )

        assert data.agent_id == agent_id
        assert data.team_id == team_id
        assert data.note == "Assigning to billing team"

    def test_assignment_without_team(self):
        """Test assignment without team is valid."""
        agent_id = uuid4()

        data = ComplaintAssign(agent_id=agent_id)

        assert data.agent_id == agent_id
        assert data.team_id is None


class TestComplaintStatusChange:
    """Tests for ComplaintStatusChange schema."""

    def test_status_change_with_comment(self):
        """Test status change with comment."""
        data = ComplaintStatusChange(
            status=ComplaintStatus.IN_PROGRESS,
            comment="Starting investigation"
        )

        assert data.status == ComplaintStatus.IN_PROGRESS
        assert data.comment == "Starting investigation"

    def test_status_change_without_comment(self):
        """Test status change without comment."""
        data = ComplaintStatusChange(
            status=ComplaintStatus.RESOLVED
        )

        assert data.status == ComplaintStatus.RESOLVED
        assert data.comment is None


class TestComplaintEscalate:
    """Tests for ComplaintEscalate schema."""

    def test_valid_escalation(self):
        """Test valid escalation."""
        data = ComplaintEscalate(
            to_level=EscalationLevel.LEVEL_2,
            reason="Customer is VIP and requires immediate attention"
        )

        assert data.to_level == EscalationLevel.LEVEL_2
        assert "VIP" in data.reason

    def test_escalation_reason_min_length(self):
        """Test escalation reason minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintEscalate(
                to_level=EscalationLevel.LEVEL_2,
                reason="Short"  # Too short (min 10)
            )

        assert "reason" in str(exc_info.value)


class TestComplaintResolve:
    """Tests for ComplaintResolve schema."""

    def test_valid_resolution(self):
        """Test valid resolution."""
        data = ComplaintResolve(
            resolution_type=ResolutionType.REFUND,
            resolution_summary="Full refund provided to customer satisfaction",
            compensation_amount=Decimal("100.00"),
            compensation_type="refund"
        )

        assert data.resolution_type == ResolutionType.REFUND
        assert data.compensation_amount == Decimal("100.00")

    def test_resolution_summary_min_length(self):
        """Test resolution summary minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintResolve(
                resolution_type=ResolutionType.EXPLANATION,
                resolution_summary="Short"  # Too short (min 10)
            )

        assert "resolution_summary" in str(exc_info.value)

    def test_compensation_must_be_positive(self):
        """Test compensation must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintResolve(
                resolution_type=ResolutionType.REFUND,
                resolution_summary="Refund for defective product",
                compensation_amount=Decimal("-50.00")
            )

        assert "compensation_amount" in str(exc_info.value)


class TestComplaintReopen:
    """Tests for ComplaintReopen schema."""

    def test_valid_reopen(self):
        """Test valid reopen request."""
        data = ComplaintReopen(
            reason="Customer reports issue is not resolved"
        )

        assert "not resolved" in data.reason

    def test_reopen_reason_min_length(self):
        """Test reopen reason minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            ComplaintReopen(reason="Short")  # Too short (min 10)

        assert "reason" in str(exc_info.value)


class TestSatisfactionSubmit:
    """Tests for SatisfactionSubmit schema."""

    def test_valid_satisfaction(self):
        """Test valid satisfaction submission."""
        data = SatisfactionSubmit(
            rating=SatisfactionRating.SATISFIED,
            comment="Good service overall",
            nps_score=8
        )

        assert data.rating == SatisfactionRating.SATISFIED
        assert data.nps_score == 8

    def test_nps_score_range(self):
        """Test NPS score must be between 0 and 10."""
        with pytest.raises(ValidationError) as exc_info:
            SatisfactionSubmit(
                rating=SatisfactionRating.SATISFIED,
                nps_score=15  # Out of range
            )

        assert "nps_score" in str(exc_info.value)

    def test_nps_score_negative(self):
        """Test NPS score cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            SatisfactionSubmit(
                rating=SatisfactionRating.SATISFIED,
                nps_score=-1
            )

        assert "nps_score" in str(exc_info.value)


class TestTeamCreate:
    """Tests for TeamCreate schema."""

    def test_valid_team(self):
        """Test valid team creation."""
        data = TeamCreate(
            name="Billing Support",
            description="Team handling billing complaints",
            email="billing@example.com"
        )

        assert data.name == "Billing Support"
        assert data.email == "billing@example.com"

    def test_default_values(self):
        """Test default values."""
        data = TeamCreate(name="Test Team")

        assert data.auto_assign_method == "round_robin"
        assert data.max_complaints_per_agent == 25
        assert data.timezone == "Europe/Paris"


class TestAgentCreate:
    """Tests for AgentCreate schema."""

    def test_valid_agent(self):
        """Test valid agent creation."""
        user_id = uuid4()

        data = AgentCreate(
            user_id=user_id,
            display_name="John Doe",
            email="john.doe@example.com"
        )

        assert data.user_id == user_id
        assert data.display_name == "John Doe"

    def test_default_permissions(self):
        """Test default permissions."""
        data = AgentCreate(
            user_id=uuid4(),
            display_name="Test Agent"
        )

        assert data.can_assign is True
        assert data.can_escalate is True
        assert data.can_resolve is True
        assert data.can_close is False
        assert data.can_approve_compensation is False


class TestSLAPolicyCreate:
    """Tests for SLAPolicyCreate schema."""

    def test_valid_sla_policy(self):
        """Test valid SLA policy creation."""
        data = SLAPolicyCreate(
            name="Standard SLA",
            ack_hours_medium=24,
            resolution_hours_medium=120
        )

        assert data.name == "Standard SLA"

    def test_default_values(self):
        """Test default SLA values."""
        data = SLAPolicyCreate(name="Test SLA")

        assert data.ack_hours_low == 48
        assert data.ack_hours_medium == 24
        assert data.ack_hours_high == 4
        assert data.ack_hours_urgent == 2
        assert data.ack_hours_critical == 1

        assert data.resolution_hours_low == 240
        assert data.resolution_hours_medium == 120
        assert data.resolution_hours_high == 48
        assert data.resolution_hours_urgent == 24
        assert data.resolution_hours_critical == 8

    def test_hours_must_be_positive(self):
        """Test hours must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            SLAPolicyCreate(
                name="Invalid SLA",
                ack_hours_low=0  # Must be >= 1
            )

        assert "ack_hours_low" in str(exc_info.value)


class TestExchangeCreate:
    """Tests for ExchangeCreate schema."""

    def test_valid_exchange(self):
        """Test valid exchange creation."""
        data = ExchangeCreate(
            body="Thank you for contacting us. We are looking into your issue.",
            is_internal=False
        )

        assert data.body is not None
        assert data.is_internal is False

    def test_body_required(self):
        """Test body is required."""
        with pytest.raises(ValidationError) as exc_info:
            ExchangeCreate(body="")

        assert "body" in str(exc_info.value)


class TestTemplateCreate:
    """Tests for TemplateCreate schema."""

    def test_valid_template(self):
        """Test valid template creation."""
        data = TemplateCreate(
            code="ACK_BILLING",
            name="Billing Acknowledgment",
            body="Dear {{customer_name}}, we have received your complaint regarding billing."
        )

        assert data.code == "ACK_BILLING"
        assert "{{customer_name}}" in data.body

    def test_body_min_length(self):
        """Test body minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateCreate(
                code="TEST",
                name="Test Template",
                body="Short"  # Too short (min 10)
            )

        assert "body" in str(exc_info.value)


class TestComplaintFilter:
    """Tests for ComplaintFilter schema."""

    def test_empty_filter(self):
        """Test empty filter."""
        data = ComplaintFilter()

        assert data.query is None
        assert data.status is None
        assert data.priority is None

    def test_filter_with_values(self):
        """Test filter with values."""
        data = ComplaintFilter(
            query="billing",
            status=[ComplaintStatus.NEW, ComplaintStatus.IN_PROGRESS],
            priority=[ComplaintPriority.HIGH, ComplaintPriority.CRITICAL],
            sla_breached=True
        )

        assert data.query == "billing"
        assert len(data.status) == 2
        assert len(data.priority) == 2
        assert data.sla_breached is True


class TestActionCreate:
    """Tests for ActionCreate schema."""

    def test_valid_action(self):
        """Test valid action creation."""
        data = ActionCreate(
            title="Call customer",
            description="Call customer to discuss resolution options",
            due_date=datetime.utcnow()
        )

        assert data.title == "Call customer"
        assert data.due_date is not None


class TestActionComplete:
    """Tests for ActionComplete schema."""

    def test_valid_completion(self):
        """Test valid action completion."""
        data = ActionComplete(
            completion_notes="Called customer, agreed on refund",
            outcome="success",
            follow_up_required=False
        )

        assert data.outcome == "success"
        assert data.follow_up_required is False

    def test_outcome_validation(self):
        """Test outcome must be valid value."""
        with pytest.raises(ValidationError) as exc_info:
            ActionComplete(outcome="invalid")

        assert "outcome" in str(exc_info.value)


class TestTemplateRender:
    """Tests for TemplateRender schema."""

    def test_valid_render_request(self):
        """Test valid render request."""
        data = TemplateRender(
            variables={
                "customer_name": "John Doe",
                "complaint_reference": "REC-2024-000001"
            }
        )

        assert data.variables["customer_name"] == "John Doe"
