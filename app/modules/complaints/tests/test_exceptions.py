"""
Tests for Complaints exceptions.
"""

import pytest

from app.modules.complaints.exceptions import (
    ActionNotFoundError,
    AgentNotAvailableError,
    AgentNotFoundError,
    AgentOverloadedError,
    ApprovalRequiredError,
    AttachmentNotFoundError,
    AutomationExecutionError,
    CategoryNotFoundError,
    CompensationLimitExceededError,
    ComplaintAlreadyClosedError,
    ComplaintException,
    ComplaintNotFoundError,
    ComplaintNotResolvedError,
    CustomerInfoRequiredError,
    DuplicateCodeError,
    DuplicateReferenceError,
    ExchangeNotFoundError,
    FileTooLargeError,
    FileUploadError,
    InsufficientPermissionError,
    InvalidAutomationActionError,
    InvalidAutomationConditionError,
    InvalidEscalationLevelError,
    InvalidFileTypeError,
    InvalidStatusTransitionError,
    ResolutionRequiredError,
    SLABreachedError,
    SLABreachWarning,
    SLAPolicyNotFoundError,
    TeamNotFoundError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateVariableError,
)


class TestComplaintException:
    """Tests for base ComplaintException."""

    def test_exception_message(self):
        """Test exception message is set."""
        exc = ComplaintException("Test error")
        assert exc.message == "Test error"
        assert str(exc) == "Test error"

    def test_exception_code(self):
        """Test exception code is set."""
        exc = ComplaintException("Test error", code="TEST_ERROR")
        assert exc.code == "TEST_ERROR"

    def test_exception_details(self):
        """Test exception details are set."""
        exc = ComplaintException("Test error", details={"key": "value"})
        assert exc.details == {"key": "value"}

    def test_exception_default_code(self):
        """Test exception default code."""
        exc = ComplaintException("Test error")
        assert exc.code == "COMPLAINT_ERROR"

    def test_exception_default_details(self):
        """Test exception default details."""
        exc = ComplaintException("Test error")
        assert exc.details == {}


class TestNotFoundExceptions:
    """Tests for not found exceptions."""

    def test_complaint_not_found_with_id(self):
        """Test ComplaintNotFoundError with ID."""
        exc = ComplaintNotFoundError(complaint_id="123")
        assert "123" in exc.message
        assert exc.code == "COMPLAINT_NOT_FOUND"
        assert exc.details["complaint_id"] == "123"

    def test_complaint_not_found_with_reference(self):
        """Test ComplaintNotFoundError with reference."""
        exc = ComplaintNotFoundError(reference="REC-2024-000001")
        assert "REC-2024-000001" in exc.message
        assert exc.details["reference"] == "REC-2024-000001"

    def test_team_not_found(self):
        """Test TeamNotFoundError."""
        exc = TeamNotFoundError("team-123")
        assert "team-123" in exc.message
        assert exc.code == "TEAM_NOT_FOUND"

    def test_agent_not_found(self):
        """Test AgentNotFoundError."""
        exc = AgentNotFoundError("agent-123")
        assert "agent-123" in exc.message
        assert exc.code == "AGENT_NOT_FOUND"

    def test_category_not_found(self):
        """Test CategoryNotFoundError."""
        exc = CategoryNotFoundError(code="BILLING")
        assert "BILLING" in exc.message
        assert exc.code == "CATEGORY_NOT_FOUND"

    def test_sla_policy_not_found(self):
        """Test SLAPolicyNotFoundError."""
        exc = SLAPolicyNotFoundError("sla-123")
        assert "sla-123" in exc.message
        assert exc.code == "SLA_POLICY_NOT_FOUND"

    def test_template_not_found(self):
        """Test TemplateNotFoundError."""
        exc = TemplateNotFoundError(code="ACK_TEMPLATE")
        assert "ACK_TEMPLATE" in exc.message
        assert exc.code == "TEMPLATE_NOT_FOUND"

    def test_action_not_found(self):
        """Test ActionNotFoundError."""
        exc = ActionNotFoundError("action-123")
        assert "action-123" in exc.message
        assert exc.code == "ACTION_NOT_FOUND"

    def test_exchange_not_found(self):
        """Test ExchangeNotFoundError."""
        exc = ExchangeNotFoundError("exchange-123")
        assert "exchange-123" in exc.message
        assert exc.code == "EXCHANGE_NOT_FOUND"

    def test_attachment_not_found(self):
        """Test AttachmentNotFoundError."""
        exc = AttachmentNotFoundError("attachment-123")
        assert "attachment-123" in exc.message
        assert exc.code == "ATTACHMENT_NOT_FOUND"


class TestValidationExceptions:
    """Tests for validation exceptions."""

    def test_invalid_status_transition(self):
        """Test InvalidStatusTransitionError."""
        exc = InvalidStatusTransitionError("new", "closed", "complaint-123")
        assert "new" in exc.message
        assert "closed" in exc.message
        assert exc.code == "INVALID_STATUS_TRANSITION"
        assert exc.details["current_status"] == "new"
        assert exc.details["target_status"] == "closed"

    def test_invalid_escalation_level(self):
        """Test InvalidEscalationLevelError."""
        exc = InvalidEscalationLevelError("level_2", "level_1")
        assert "level_2" in exc.message
        assert "level_1" in exc.message
        assert exc.code == "INVALID_ESCALATION_LEVEL"

    def test_complaint_already_closed(self):
        """Test ComplaintAlreadyClosedError."""
        exc = ComplaintAlreadyClosedError("123", "REC-2024-000001")
        assert "REC-2024-000001" in exc.message
        assert exc.code == "COMPLAINT_ALREADY_CLOSED"

    def test_complaint_not_resolved(self):
        """Test ComplaintNotResolvedError."""
        exc = ComplaintNotResolvedError("123")
        assert "123" in exc.message
        assert exc.code == "COMPLAINT_NOT_RESOLVED"

    def test_duplicate_reference(self):
        """Test DuplicateReferenceError."""
        exc = DuplicateReferenceError("REC-2024-000001")
        assert "REC-2024-000001" in exc.message
        assert exc.code == "DUPLICATE_REFERENCE"

    def test_duplicate_code(self):
        """Test DuplicateCodeError."""
        exc = DuplicateCodeError("BILLING", "category")
        assert "BILLING" in exc.message
        assert "category" in exc.message
        assert exc.code == "DUPLICATE_CODE"

    def test_customer_info_required(self):
        """Test CustomerInfoRequiredError."""
        exc = CustomerInfoRequiredError()
        assert exc.code == "CUSTOMER_INFO_REQUIRED"

    def test_resolution_required(self):
        """Test ResolutionRequiredError."""
        exc = ResolutionRequiredError("123")
        assert "123" in exc.message
        assert exc.code == "RESOLUTION_REQUIRED"


class TestPermissionExceptions:
    """Tests for permission exceptions."""

    def test_agent_not_available(self):
        """Test AgentNotAvailableError."""
        exc = AgentNotAvailableError("agent-123", "on vacation")
        assert "agent-123" in exc.message
        assert "on vacation" in exc.message
        assert exc.code == "AGENT_NOT_AVAILABLE"

    def test_agent_overloaded(self):
        """Test AgentOverloadedError."""
        exc = AgentOverloadedError("agent-123", 25, 25)
        assert "agent-123" in exc.message
        assert "25" in exc.message
        assert exc.code == "AGENT_OVERLOADED"

    def test_insufficient_permission(self):
        """Test InsufficientPermissionError."""
        exc = InsufficientPermissionError("approve_compensation", "agent-123")
        assert "approve_compensation" in exc.message
        assert exc.code == "INSUFFICIENT_PERMISSION"

    def test_compensation_limit_exceeded(self):
        """Test CompensationLimitExceededError."""
        exc = CompensationLimitExceededError(500.0, 200.0, "agent-123")
        assert "500" in exc.message
        assert "200" in exc.message
        assert exc.code == "COMPENSATION_LIMIT_EXCEEDED"

    def test_approval_required(self):
        """Test ApprovalRequiredError."""
        exc = ApprovalRequiredError("123", "Compensation exceeds limit")
        assert "Compensation exceeds limit" in exc.message
        assert exc.code == "APPROVAL_REQUIRED"


class TestSLAExceptions:
    """Tests for SLA exceptions."""

    def test_sla_breach_warning(self):
        """Test SLABreachWarning."""
        exc = SLABreachWarning("123", "resolution", "2024-01-01 12:00:00", 2.5)
        assert "resolution" in exc.message
        assert "2.5" in exc.message
        assert exc.code == "SLA_BREACH_WARNING"

    def test_sla_breached(self):
        """Test SLABreachedError."""
        exc = SLABreachedError("123", "resolution", "2024-01-01 12:00:00")
        assert "resolution" in exc.message
        assert "123" in exc.message
        assert exc.code == "SLA_BREACHED"


class TestTemplateExceptions:
    """Tests for template exceptions."""

    def test_template_variable_error(self):
        """Test TemplateVariableError."""
        exc = TemplateVariableError("template-123", ["customer_name", "order_id"])
        assert "customer_name" in exc.message
        assert "order_id" in exc.message
        assert exc.code == "TEMPLATE_VARIABLE_ERROR"

    def test_template_render_error(self):
        """Test TemplateRenderError."""
        exc = TemplateRenderError("template-123", "Invalid syntax")
        assert "template-123" in exc.message
        assert "Invalid syntax" in exc.message
        assert exc.code == "TEMPLATE_RENDER_ERROR"


class TestAutomationExceptions:
    """Tests for automation exceptions."""

    def test_automation_execution_error(self):
        """Test AutomationExecutionError."""
        exc = AutomationExecutionError("rule-123", "Connection timeout")
        assert "rule-123" in exc.message
        assert "Connection timeout" in exc.message
        assert exc.code == "AUTOMATION_EXECUTION_ERROR"

    def test_invalid_automation_condition(self):
        """Test InvalidAutomationConditionError."""
        exc = InvalidAutomationConditionError("rule-123", "unknown_field == value")
        assert "rule-123" in exc.message
        assert "unknown_field == value" in exc.message
        assert exc.code == "INVALID_AUTOMATION_CONDITION"

    def test_invalid_automation_action(self):
        """Test InvalidAutomationActionError."""
        exc = InvalidAutomationActionError("rule-123", "unknown_action")
        assert "rule-123" in exc.message
        assert "unknown_action" in exc.message
        assert exc.code == "INVALID_AUTOMATION_ACTION"


class TestAttachmentExceptions:
    """Tests for attachment exceptions."""

    def test_file_too_large(self):
        """Test FileTooLargeError."""
        exc = FileTooLargeError("document.pdf", 10485760, 5242880)
        assert "document.pdf" in exc.message
        assert exc.code == "FILE_TOO_LARGE"

    def test_invalid_file_type(self):
        """Test InvalidFileTypeError."""
        exc = InvalidFileTypeError("script.exe", "application/x-executable", ["pdf", "jpg"])
        assert "script.exe" in exc.message
        assert "application/x-executable" in exc.message
        assert exc.code == "INVALID_FILE_TYPE"

    def test_file_upload_error(self):
        """Test FileUploadError."""
        exc = FileUploadError("document.pdf", "Storage service unavailable")
        assert "document.pdf" in exc.message
        assert "Storage service unavailable" in exc.message
        assert exc.code == "FILE_UPLOAD_ERROR"
