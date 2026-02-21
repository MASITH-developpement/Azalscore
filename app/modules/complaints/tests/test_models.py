"""
Tests for Complaints models.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.modules.complaints.models import (
    ActionType,
    Complaint,
    ComplaintAction,
    ComplaintAgent,
    ComplaintCategory,
    ComplaintCategoryConfig,
    ComplaintChannel,
    ComplaintEscalation,
    ComplaintExchange,
    ComplaintPriority,
    ComplaintSLAPolicy,
    ComplaintStatus,
    ComplaintTeam,
    ComplaintTemplate,
    EscalationLevel,
    ResolutionType,
    RootCauseCategory,
    SatisfactionRating,
)


class TestEnums:
    """Tests for enum values."""

    def test_complaint_channel_values(self):
        """Test all complaint channels are defined."""
        assert ComplaintChannel.EMAIL.value == "email"
        assert ComplaintChannel.PHONE.value == "phone"
        assert ComplaintChannel.WEB_FORM.value == "web_form"
        assert ComplaintChannel.CHAT.value == "chat"
        assert ComplaintChannel.SOCIAL_MEDIA.value == "social_media"
        assert ComplaintChannel.LETTER.value == "letter"
        assert ComplaintChannel.IN_PERSON.value == "in_person"
        assert ComplaintChannel.MOBILE_APP.value == "mobile_app"
        assert ComplaintChannel.API.value == "api"

    def test_complaint_category_values(self):
        """Test all complaint categories are defined."""
        assert ComplaintCategory.PRODUCT_QUALITY.value == "product_quality"
        assert ComplaintCategory.PRODUCT_DEFECT.value == "product_defect"
        assert ComplaintCategory.DELIVERY.value == "delivery"
        assert ComplaintCategory.BILLING.value == "billing"
        assert ComplaintCategory.GDPR.value == "gdpr"
        assert ComplaintCategory.FRAUD.value == "fraud"

    def test_complaint_priority_values(self):
        """Test all complaint priorities are defined."""
        assert ComplaintPriority.LOW.value == "low"
        assert ComplaintPriority.MEDIUM.value == "medium"
        assert ComplaintPriority.HIGH.value == "high"
        assert ComplaintPriority.URGENT.value == "urgent"
        assert ComplaintPriority.CRITICAL.value == "critical"

    def test_complaint_status_values(self):
        """Test all complaint statuses are defined."""
        assert ComplaintStatus.DRAFT.value == "draft"
        assert ComplaintStatus.NEW.value == "new"
        assert ComplaintStatus.ACKNOWLEDGED.value == "acknowledged"
        assert ComplaintStatus.IN_PROGRESS.value == "in_progress"
        assert ComplaintStatus.PENDING_INFO.value == "pending_info"
        assert ComplaintStatus.ESCALATED.value == "escalated"
        assert ComplaintStatus.RESOLVED.value == "resolved"
        assert ComplaintStatus.CLOSED.value == "closed"
        assert ComplaintStatus.REOPENED.value == "reopened"
        assert ComplaintStatus.CANCELLED.value == "cancelled"

    def test_resolution_type_values(self):
        """Test all resolution types are defined."""
        assert ResolutionType.REFUND.value == "refund"
        assert ResolutionType.REPLACEMENT.value == "replacement"
        assert ResolutionType.REPAIR.value == "repair"
        assert ResolutionType.CREDIT_NOTE.value == "credit_note"
        assert ResolutionType.COMMERCIAL_GESTURE.value == "commercial_gesture"
        assert ResolutionType.COMPENSATION.value == "compensation"

    def test_escalation_level_values(self):
        """Test all escalation levels are defined."""
        assert EscalationLevel.LEVEL_1.value == "level_1"
        assert EscalationLevel.LEVEL_2.value == "level_2"
        assert EscalationLevel.LEVEL_3.value == "level_3"
        assert EscalationLevel.LEVEL_4.value == "level_4"
        assert EscalationLevel.LEGAL.value == "legal"
        assert EscalationLevel.MEDIATOR.value == "mediator"
        assert EscalationLevel.EXTERNAL.value == "external"

    def test_satisfaction_rating_values(self):
        """Test all satisfaction ratings are defined."""
        assert SatisfactionRating.VERY_DISSATISFIED.value == "very_dissatisfied"
        assert SatisfactionRating.DISSATISFIED.value == "dissatisfied"
        assert SatisfactionRating.NEUTRAL.value == "neutral"
        assert SatisfactionRating.SATISFIED.value == "satisfied"
        assert SatisfactionRating.VERY_SATISFIED.value == "very_satisfied"


class TestComplaintModel:
    """Tests for Complaint model."""

    def test_complaint_table_name(self):
        """Test table name is correct."""
        assert Complaint.__tablename__ == "complaints"

    def test_complaint_has_required_fields(self):
        """Test complaint model has all required fields."""
        columns = [c.name for c in Complaint.__table__.columns]

        required_fields = [
            "id", "tenant_id", "reference", "subject", "description",
            "category", "priority", "status", "channel",
            "customer_id", "customer_name", "customer_email",
            "created_at", "updated_at", "version"
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

    def test_complaint_has_sla_fields(self):
        """Test complaint has SLA tracking fields."""
        columns = [c.name for c in Complaint.__table__.columns]

        sla_fields = [
            "sla_policy_id", "acknowledgment_due", "acknowledged_at",
            "acknowledgment_breached", "resolution_due", "resolved_at",
            "resolution_breached", "escalation_due"
        ]

        for field in sla_fields:
            assert field in columns, f"Missing SLA field: {field}"

    def test_complaint_has_escalation_fields(self):
        """Test complaint has escalation tracking fields."""
        columns = [c.name for c in Complaint.__table__.columns]

        escalation_fields = [
            "current_escalation_level", "escalated_at", "escalation_count"
        ]

        for field in escalation_fields:
            assert field in columns, f"Missing escalation field: {field}"

    def test_complaint_has_resolution_fields(self):
        """Test complaint has resolution fields."""
        columns = [c.name for c in Complaint.__table__.columns]

        resolution_fields = [
            "resolution_type", "resolution_summary",
            "compensation_amount", "compensation_type"
        ]

        for field in resolution_fields:
            assert field in columns, f"Missing resolution field: {field}"

    def test_complaint_has_satisfaction_fields(self):
        """Test complaint has satisfaction fields."""
        columns = [c.name for c in Complaint.__table__.columns]

        satisfaction_fields = [
            "satisfaction_rating", "satisfaction_comment",
            "satisfaction_submitted_at", "nps_score"
        ]

        for field in satisfaction_fields:
            assert field in columns, f"Missing satisfaction field: {field}"

    def test_complaint_has_audit_fields(self):
        """Test complaint has audit fields."""
        columns = [c.name for c in Complaint.__table__.columns]

        audit_fields = [
            "is_deleted", "deleted_at", "deleted_by",
            "created_at", "updated_at", "created_by", "updated_by", "version"
        ]

        for field in audit_fields:
            assert field in columns, f"Missing audit field: {field}"

    def test_complaint_indexes(self):
        """Test complaint has proper indexes."""
        index_names = [idx.name for idx in Complaint.__table__.indexes]

        expected_indexes = [
            "idx_complaint_tenant",
            "idx_complaint_ref",
            "idx_complaint_status",
            "idx_complaint_priority",
            "idx_complaint_customer",
            "idx_complaint_assigned",
            "idx_complaint_deleted"
        ]

        for idx in expected_indexes:
            assert idx in index_names, f"Missing index: {idx}"


class TestComplaintTeamModel:
    """Tests for ComplaintTeam model."""

    def test_team_table_name(self):
        """Test table name is correct."""
        assert ComplaintTeam.__tablename__ == "complaints_teams"

    def test_team_has_required_fields(self):
        """Test team model has all required fields."""
        columns = [c.name for c in ComplaintTeam.__table__.columns]

        required_fields = [
            "id", "tenant_id", "name", "description", "email",
            "manager_id", "auto_assign_method", "max_complaints_per_agent",
            "working_hours", "timezone", "is_active", "deleted_at",
            "created_at", "updated_at", "version"
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"


class TestComplaintAgentModel:
    """Tests for ComplaintAgent model."""

    def test_agent_table_name(self):
        """Test table name is correct."""
        assert ComplaintAgent.__tablename__ == "complaints_agents"

    def test_agent_has_required_fields(self):
        """Test agent model has all required fields."""
        columns = [c.name for c in ComplaintAgent.__table__.columns]

        required_fields = [
            "id", "tenant_id", "user_id", "team_id",
            "display_name", "email", "phone",
            "skills", "languages", "max_escalation_level",
            "can_assign", "can_escalate", "can_resolve", "can_close",
            "can_approve_compensation", "max_compensation_amount",
            "is_available", "current_load", "last_assigned_at",
            "complaints_assigned", "complaints_resolved",
            "avg_resolution_hours", "satisfaction_score",
            "is_active", "deleted_at", "created_at", "updated_at", "version"
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"


class TestComplaintSLAPolicyModel:
    """Tests for ComplaintSLAPolicy model."""

    def test_sla_policy_table_name(self):
        """Test table name is correct."""
        assert ComplaintSLAPolicy.__tablename__ == "complaints_sla_policies"

    def test_sla_policy_has_acknowledgment_hours(self):
        """Test SLA policy has acknowledgment hours for all priorities."""
        columns = [c.name for c in ComplaintSLAPolicy.__table__.columns]

        ack_fields = [
            "ack_hours_low", "ack_hours_medium", "ack_hours_high",
            "ack_hours_urgent", "ack_hours_critical"
        ]

        for field in ack_fields:
            assert field in columns, f"Missing ack field: {field}"

    def test_sla_policy_has_resolution_hours(self):
        """Test SLA policy has resolution hours for all priorities."""
        columns = [c.name for c in ComplaintSLAPolicy.__table__.columns]

        resolution_fields = [
            "resolution_hours_low", "resolution_hours_medium",
            "resolution_hours_high", "resolution_hours_urgent",
            "resolution_hours_critical"
        ]

        for field in resolution_fields:
            assert field in columns, f"Missing resolution field: {field}"

    def test_sla_policy_has_escalation_hours(self):
        """Test SLA policy has escalation hours for all priorities."""
        columns = [c.name for c in ComplaintSLAPolicy.__table__.columns]

        escalation_fields = [
            "escalation_hours_low", "escalation_hours_medium",
            "escalation_hours_high", "escalation_hours_urgent",
            "escalation_hours_critical"
        ]

        for field in escalation_fields:
            assert field in columns, f"Missing escalation field: {field}"


class TestComplaintExchangeModel:
    """Tests for ComplaintExchange model."""

    def test_exchange_table_name(self):
        """Test table name is correct."""
        assert ComplaintExchange.__tablename__ == "complaints_exchanges"

    def test_exchange_has_required_fields(self):
        """Test exchange model has all required fields."""
        columns = [c.name for c in ComplaintExchange.__table__.columns]

        required_fields = [
            "id", "tenant_id", "complaint_id",
            "author_type", "author_id", "author_name", "author_email",
            "subject", "body", "body_html",
            "exchange_type", "is_internal", "is_first_response",
            "channel", "sentiment", "created_at"
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"


class TestComplaintActionModel:
    """Tests for ComplaintAction model."""

    def test_action_table_name(self):
        """Test table name is correct."""
        assert ComplaintAction.__tablename__ == "complaints_actions"

    def test_action_has_required_fields(self):
        """Test action model has all required fields."""
        columns = [c.name for c in ComplaintAction.__table__.columns]

        required_fields = [
            "id", "tenant_id", "complaint_id",
            "action_type", "title", "description",
            "assigned_to_id", "assigned_to_name",
            "due_date", "reminder_date",
            "status", "completed_at", "completed_by_id",
            "completion_notes", "outcome", "follow_up_required",
            "created_at", "created_by", "updated_at", "version"
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"


class TestComplaintEscalationModel:
    """Tests for ComplaintEscalation model."""

    def test_escalation_table_name(self):
        """Test table name is correct."""
        assert ComplaintEscalation.__tablename__ == "complaints_escalations"

    def test_escalation_has_required_fields(self):
        """Test escalation model has all required fields."""
        columns = [c.name for c in ComplaintEscalation.__table__.columns]

        required_fields = [
            "id", "tenant_id", "complaint_id",
            "from_level", "to_level", "reason", "is_automatic",
            "escalated_by_id", "escalated_by_name",
            "assigned_to_id", "assigned_to_name",
            "accepted_at", "resolved_at", "resolution_notes",
            "created_at"
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"


class TestComplaintTemplateModel:
    """Tests for ComplaintTemplate model."""

    def test_template_table_name(self):
        """Test table name is correct."""
        assert ComplaintTemplate.__tablename__ == "complaints_templates"

    def test_template_has_required_fields(self):
        """Test template model has all required fields."""
        columns = [c.name for c in ComplaintTemplate.__table__.columns]

        required_fields = [
            "id", "tenant_id", "code", "name", "description",
            "category", "template_type",
            "subject", "body", "body_html", "language",
            "variables", "scope", "team_id", "owner_id",
            "usage_count", "last_used_at",
            "is_active", "deleted_at", "created_at", "updated_at",
            "created_by", "version"
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"
