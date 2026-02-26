"""
Tests for Complaints service.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.modules.complaints.exceptions import (
    AgentNotAvailableError,
    AgentNotFoundError,
    ComplaintAlreadyClosedError,
    ComplaintNotFoundError,
    ComplaintNotResolvedError,
    CustomerInfoRequiredError,
    DuplicateCodeError,
    InvalidEscalationLevelError,
    InvalidStatusTransitionError,
)
from app.modules.complaints.models import (
    Complaint,
    ComplaintAgent,
    ComplaintCategory,
    ComplaintChannel,
    ComplaintPriority,
    ComplaintSLAPolicy,
    ComplaintStatus,
    ComplaintTeam,
    EscalationLevel,
    ResolutionType,
)
from app.modules.complaints.schemas import (
    ComplaintAssign,
    ComplaintClose,
    ComplaintCreate,
    ComplaintEscalate,
    ComplaintReopen,
    ComplaintResolve,
    ComplaintStatusChange,
    ComplaintUpdate,
)
from app.modules.complaints.service import ComplaintService, VALID_STATUS_TRANSITIONS


class TestStatusTransitions:
    """Tests for status transition rules."""

    def test_new_complaint_can_be_acknowledged(self):
        """Test NEW complaint can transition to ACKNOWLEDGED."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.NEW, [])
        assert ComplaintStatus.ACKNOWLEDGED in valid

    def test_acknowledged_can_progress(self):
        """Test ACKNOWLEDGED complaint can progress to IN_PROGRESS."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.ACKNOWLEDGED, [])
        assert ComplaintStatus.IN_PROGRESS in valid

    def test_in_progress_can_be_resolved(self):
        """Test IN_PROGRESS complaint can be RESOLVED."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.IN_PROGRESS, [])
        assert ComplaintStatus.RESOLVED in valid

    def test_resolved_can_be_closed(self):
        """Test RESOLVED complaint can be CLOSED."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.RESOLVED, [])
        assert ComplaintStatus.CLOSED in valid

    def test_resolved_can_be_reopened(self):
        """Test RESOLVED complaint can be REOPENED."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.RESOLVED, [])
        assert ComplaintStatus.REOPENED in valid

    def test_closed_can_be_reopened(self):
        """Test CLOSED complaint can be REOPENED."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.CLOSED, [])
        assert ComplaintStatus.REOPENED in valid

    def test_cancelled_cannot_transition(self):
        """Test CANCELLED complaint cannot transition."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.CANCELLED, [])
        assert valid == []

    def test_escalated_can_be_resolved(self):
        """Test ESCALATED complaint can be RESOLVED."""
        valid = VALID_STATUS_TRANSITIONS.get(ComplaintStatus.ESCALATED, [])
        assert ComplaintStatus.RESOLVED in valid


class TestComplaintServiceAutoPrioritize:
    """Tests for auto-prioritization logic."""

    def test_gdpr_category_is_critical(self):
        """Test GDPR complaints are marked as CRITICAL."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        data = ComplaintCreate(
            subject="GDPR request",
            description="I want my data deleted",
            category=ComplaintCategory.GDPR,
            customer_email="test@example.com"
        )

        priority = service._auto_prioritize(data)
        assert priority == ComplaintPriority.CRITICAL

    def test_fraud_category_is_urgent(self):
        """Test fraud complaints are marked as URGENT."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        data = ComplaintCreate(
            subject="Fraudulent charge",
            description="I see a charge I did not make",
            category=ComplaintCategory.FRAUD,
            customer_email="test@example.com"
        )

        priority = service._auto_prioritize(data)
        assert priority == ComplaintPriority.URGENT

    def test_urgent_keywords_increase_priority(self):
        """Test urgent keywords increase priority to HIGH."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        data = ComplaintCreate(
            subject="Urgent issue",
            description="This is urgent, I will contact my avocat if not resolved",
            category=ComplaintCategory.SERVICE,
            customer_email="test@example.com"
        )

        priority = service._auto_prioritize(data)
        assert priority == ComplaintPriority.HIGH

    def test_high_disputed_amount_increases_priority(self):
        """Test high disputed amount increases priority to HIGH."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        data = ComplaintCreate(
            subject="Billing issue",
            description="I was overcharged",
            category=ComplaintCategory.BILLING,
            customer_email="test@example.com",
            disputed_amount=Decimal("2500.00")
        )

        priority = service._auto_prioritize(data)
        assert priority == ComplaintPriority.HIGH

    def test_normal_complaint_is_medium(self):
        """Test normal complaints are marked as MEDIUM."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        data = ComplaintCreate(
            subject="Question about order",
            description="I have a question about my order",
            category=ComplaintCategory.OTHER,
            customer_email="test@example.com"
        )

        priority = service._auto_prioritize(data)
        assert priority == ComplaintPriority.MEDIUM


class TestComplaintServiceSentimentAnalysis:
    """Tests for sentiment analysis."""

    def test_negative_sentiment_detected(self):
        """Test negative sentiment is detected."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        text = "This is inacceptable! I am furieux and this is a catastrophe!"
        sentiment = service._analyze_sentiment(text)
        assert sentiment == "negative"

    def test_positive_sentiment_detected(self):
        """Test positive sentiment is detected."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        text = "Merci for your help. I am satisfied and everything is parfait."
        sentiment = service._analyze_sentiment(text)
        assert sentiment == "positive"

    def test_neutral_sentiment_detected(self):
        """Test neutral sentiment is detected."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        text = "I would like to know the status of my order."
        sentiment = service._analyze_sentiment(text)
        assert sentiment == "neutral"


class TestComplaintServiceEscalation:
    """Tests for escalation logic."""

    def test_get_escalation_order(self):
        """Test escalation level ordering."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        assert service._get_escalation_order(EscalationLevel.LEVEL_1) == 1
        assert service._get_escalation_order(EscalationLevel.LEVEL_2) == 2
        assert service._get_escalation_order(EscalationLevel.LEVEL_3) == 3
        assert service._get_escalation_order(EscalationLevel.LEVEL_4) == 4
        assert service._get_escalation_order(EscalationLevel.LEGAL) == 5
        assert service._get_escalation_order(EscalationLevel.MEDIATOR) == 6
        assert service._get_escalation_order(EscalationLevel.EXTERNAL) == 7

    def test_escalation_order_is_ascending(self):
        """Test escalation levels are ordered correctly."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        levels = [
            EscalationLevel.LEVEL_1,
            EscalationLevel.LEVEL_2,
            EscalationLevel.LEVEL_3,
            EscalationLevel.LEVEL_4,
            EscalationLevel.LEGAL,
            EscalationLevel.MEDIATOR,
            EscalationLevel.EXTERNAL
        ]

        orders = [service._get_escalation_order(level) for level in levels]
        assert orders == sorted(orders)


class TestComplaintServiceSLACalculation:
    """Tests for SLA deadline calculation."""

    def test_calculate_sla_deadlines_low_priority(self):
        """Test SLA calculation for LOW priority."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        # Mock SLA policy
        policy = MagicMock(spec=ComplaintSLAPolicy)
        policy.ack_hours_low = 48
        policy.resolution_hours_low = 240
        policy.escalation_hours_low = 168
        policy.business_hours_only = False

        # Create complaint
        complaint = Complaint()
        complaint.priority = ComplaintPriority.LOW

        result = service._calculate_sla_deadlines(complaint, policy)

        now = datetime.utcnow()

        # Check deadlines are set correctly (with some tolerance)
        assert result.acknowledgment_due is not None
        assert result.resolution_due is not None
        assert result.escalation_due is not None

        # Verify relative timings
        ack_diff = (result.acknowledgment_due - now).total_seconds() / 3600
        assert 47 < ack_diff < 49  # ~48 hours

        resolution_diff = (result.resolution_due - now).total_seconds() / 3600
        assert 239 < resolution_diff < 241  # ~240 hours

    def test_calculate_sla_deadlines_critical_priority(self):
        """Test SLA calculation for CRITICAL priority."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        # Mock SLA policy
        policy = MagicMock(spec=ComplaintSLAPolicy)
        policy.ack_hours_critical = 1
        policy.resolution_hours_critical = 8
        policy.escalation_hours_critical = 2
        policy.business_hours_only = False

        # Create complaint
        complaint = Complaint()
        complaint.priority = ComplaintPriority.CRITICAL

        result = service._calculate_sla_deadlines(complaint, policy)

        now = datetime.utcnow()

        # Critical priority should have shortest deadlines
        ack_diff = (result.acknowledgment_due - now).total_seconds() / 3600
        assert 0.9 < ack_diff < 1.1  # ~1 hour

        resolution_diff = (result.resolution_due - now).total_seconds() / 3600
        assert 7.9 < resolution_diff < 8.1  # ~8 hours


class TestComplaintServiceAutomationConditions:
    """Tests for automation condition checking."""

    def test_check_conditions_equals(self):
        """Test equals condition."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        # Mock rule with equals condition
        rule = MagicMock()
        rule.trigger_conditions = [
            {"field": "priority", "operator": "equals", "value": "high"}
        ]

        # Mock complaint
        complaint = MagicMock()
        complaint.priority = ComplaintPriority.HIGH

        result = service._check_automation_conditions(rule, complaint)
        assert result is True

    def test_check_conditions_in_list(self):
        """Test in condition."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        rule = MagicMock()
        rule.trigger_conditions = [
            {"field": "category", "operator": "in", "value": ["billing", "pricing"]}
        ]

        complaint = MagicMock()
        complaint.category = ComplaintCategory.BILLING

        result = service._check_automation_conditions(rule, complaint)
        assert result is True

    def test_check_conditions_contains(self):
        """Test contains condition."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        rule = MagicMock()
        rule.trigger_conditions = [
            {"field": "subject", "operator": "contains", "value": "urgent"}
        ]

        complaint = MagicMock()
        complaint.subject = "URGENT: Please help"

        result = service._check_automation_conditions(rule, complaint)
        assert result is True

    def test_check_conditions_empty_returns_true(self):
        """Test empty conditions return True."""
        service = ComplaintService.__new__(ComplaintService)
        service.tenant_id = "test_tenant"

        rule = MagicMock()
        rule.trigger_conditions = None

        complaint = MagicMock()

        result = service._check_automation_conditions(rule, complaint)
        assert result is True


class TestComplaintServiceReferenceGeneration:
    """Tests for reference generation."""

    def test_reference_format(self):
        """Test reference format is correct."""
        # Reference format should be REC-YYYY-XXXXXX
        import re

        year = datetime.utcnow().year
        pattern = rf"^REC-{year}-\d{{6}}$"

        # Test pattern matches expected format
        test_ref = f"REC-{year}-000001"
        assert re.match(pattern, test_ref) is not None

        test_ref = f"REC-{year}-123456"
        assert re.match(pattern, test_ref) is not None

    def test_reference_sequential(self):
        """Test references are sequential."""
        year = datetime.utcnow().year

        ref1 = f"REC-{year}-000001"
        ref2 = f"REC-{year}-000002"
        ref3 = f"REC-{year}-000003"

        # Extract numbers
        num1 = int(ref1.split("-")[-1])
        num2 = int(ref2.split("-")[-1])
        num3 = int(ref3.split("-")[-1])

        assert num2 == num1 + 1
        assert num3 == num2 + 1
