"""
AZALS MODULE T2 - Tests Système de Déclencheurs & Diffusion
============================================================

Tests unitaires et d'intégration pour le module Triggers.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json

from app.modules.triggers.models import (
    Trigger, TriggerSubscription, TriggerEvent, Notification,
    NotificationTemplate, ScheduledReport, ReportHistory,
    WebhookEndpoint, TriggerLog,
    TriggerType, TriggerStatus, ConditionOperator, AlertSeverity,
    NotificationChannel, NotificationStatus, ReportFrequency, EscalationLevel
)
from app.modules.triggers.service import TriggerService, get_trigger_service
from app.modules.triggers.schemas import (
    TriggerCreateSchema, TriggerUpdateSchema, TriggerResponseSchema,
    SubscriptionCreateSchema, TemplateCreateSchema,
    ScheduledReportCreateSchema, RecipientsSchema,
    WebhookCreateSchema
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock de la session DB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    return db


@pytest.fixture
def trigger_service(mock_db):
    """Service de triggers avec mock DB."""
    return TriggerService(mock_db, "tenant_test")


@pytest.fixture
def sample_trigger():
    """Trigger d'exemple."""
    trigger = Trigger(
        id=1,
        tenant_id="tenant_test",
        code="TRESO_BALANCE_NEG",
        name="Solde trésorerie négatif",
        description="Alerte quand le solde devient négatif",
        trigger_type=TriggerType.THRESHOLD,
        status=TriggerStatus.ACTIVE,
        source_module="treasury",
        source_entity="forecast",
        source_field="balance",
        condition='{"field": "balance", "operator": "lt", "value": 0}',
        threshold_value="0",
        threshold_operator=ConditionOperator.LT,
        severity=AlertSeverity.CRITICAL,
        escalation_enabled=True,
        escalation_delay_minutes=30,
        cooldown_minutes=60,
        is_active=True,
        trigger_count=0,
        created_at=datetime.utcnow()
    )
    return trigger


@pytest.fixture
def sample_condition_simple():
    """Condition simple."""
    return {
        "field": "balance",
        "operator": "lt",
        "value": 0
    }


@pytest.fixture
def sample_condition_complex():
    """Condition complexe avec AND/OR."""
    return {
        "and": [
            {"field": "balance", "operator": "lt", "value": 1000},
            {
                "or": [
                    {"field": "status", "operator": "eq", "value": "PENDING"},
                    {"field": "priority", "operator": "eq", "value": "HIGH"}
                ]
            }
        ]
    }


# ============================================================================
# TESTS SCHEMAS
# ============================================================================

class TestTriggerSchemas:
    """Tests des schémas Pydantic."""

    def test_trigger_create_valid(self):
        """Création valide d'un trigger."""
        data = TriggerCreateSchema(
            code="TEST_TRIGGER",
            name="Test Trigger",
            trigger_type=TriggerType.THRESHOLD,
            source_module="treasury",
            condition={"field": "balance", "operator": "lt", "value": 0},
            severity=AlertSeverity.WARNING
        )
        assert data.code == "TEST_TRIGGER"
        assert data.trigger_type == TriggerType.THRESHOLD

    def test_trigger_create_invalid_code(self):
        """Code de trigger invalide."""
        with pytest.raises(ValueError):
            TriggerCreateSchema(
                code="test-invalid",  # Tiret non autorisé
                name="Test",
                trigger_type=TriggerType.THRESHOLD,
                source_module="treasury",
                condition={"field": "balance", "operator": "lt", "value": 0}
            )

    def test_trigger_create_empty_condition(self):
        """Condition vide non autorisée."""
        with pytest.raises(ValueError):
            TriggerCreateSchema(
                code="TEST",
                name="Test",
                trigger_type=TriggerType.THRESHOLD,
                source_module="treasury",
                condition={}
            )

    def test_subscription_create_valid(self):
        """Création valide d'un abonnement."""
        data = SubscriptionCreateSchema(
            trigger_id=1,
            user_id=10,
            channel=NotificationChannel.EMAIL,
            escalation_level=EscalationLevel.L1
        )
        assert data.trigger_id == 1
        assert data.user_id == 10

    def test_template_create_valid(self):
        """Création valide d'un template."""
        data = TemplateCreateSchema(
            code="TEST_TEMPLATE",
            name="Test Template",
            body_template="Alerte: {{trigger_name}}",
            subject_template="[{{severity}}] Alerte",
            available_variables=["trigger_name", "severity"]
        )
        assert data.code == "TEST_TEMPLATE"

    def test_scheduled_report_create_valid(self):
        """Création valide d'un rapport planifié."""
        data = ScheduledReportCreateSchema(
            code="WEEKLY_REPORT",
            name="Rapport Hebdomadaire",
            report_type="cockpit_summary",
            frequency=ReportFrequency.WEEKLY,
            schedule_day=1,  # Lundi
            schedule_time="08:00",
            recipients=RecipientsSchema(
                users=[1, 2],
                roles=["DAF"],
                emails=["external@test.com"]
            ),
            output_format="PDF"
        )
        assert data.frequency == ReportFrequency.WEEKLY

    def test_webhook_create_valid(self):
        """Création valide d'un webhook."""
        data = WebhookCreateSchema(
            code="SLACK_WEBHOOK",
            name="Webhook Slack",
            url="https://hooks.slack.com/test",
            method="POST",
            auth_type="bearer"
        )
        assert data.url == "https://hooks.slack.com/test"


# ============================================================================
# TESTS SERVICE - TRIGGERS
# ============================================================================

class TestTriggerService:
    """Tests du service Triggers."""

    def test_create_trigger(self, trigger_service, mock_db):
        """Création d'un trigger."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        trigger = trigger_service.create_trigger(
            code="NEW_TRIGGER",
            name="Nouveau Trigger",
            trigger_type=TriggerType.THRESHOLD,
            source_module="treasury",
            condition={"field": "balance", "operator": "lt", "value": 0},
            severity=AlertSeverity.WARNING
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_create_trigger_duplicate(self, trigger_service, mock_db, sample_trigger):
        """Création d'un trigger avec code existant."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_trigger

        with pytest.raises(ValueError, match="existe déjà"):
            trigger_service.create_trigger(
                code="TRESO_BALANCE_NEG",
                name="Duplicate",
                trigger_type=TriggerType.THRESHOLD,
                source_module="treasury",
                condition={"field": "balance", "operator": "lt", "value": 0}
            )

    def test_pause_trigger(self, trigger_service, mock_db, sample_trigger):
        """Mise en pause d'un trigger."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_trigger

        result = trigger_service.pause_trigger(1)

        assert result.status == TriggerStatus.PAUSED
        mock_db.commit.assert_called()

    def test_resume_trigger(self, trigger_service, mock_db, sample_trigger):
        """Reprise d'un trigger."""
        sample_trigger.status = TriggerStatus.PAUSED
        mock_db.query.return_value.filter.return_value.first.return_value = sample_trigger

        result = trigger_service.resume_trigger(1)

        assert result.status == TriggerStatus.ACTIVE

    def test_delete_trigger(self, trigger_service, mock_db, sample_trigger):
        """Suppression d'un trigger."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_trigger

        result = trigger_service.delete_trigger(1)

        assert result is True
        mock_db.delete.assert_called_with(sample_trigger)

    def test_delete_trigger_not_found(self, trigger_service, mock_db):
        """Suppression d'un trigger inexistant."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = trigger_service.delete_trigger(999)

        assert result is False


# ============================================================================
# TESTS SERVICE - ÉVALUATION DES CONDITIONS
# ============================================================================

class TestConditionEvaluation:
    """Tests de l'évaluation des conditions."""

    def test_evaluate_simple_lt(self, trigger_service, sample_trigger):
        """Évaluation condition LT."""
        data = {"balance": -500}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is True

    def test_evaluate_simple_lt_false(self, trigger_service, sample_trigger):
        """Évaluation condition LT non remplie."""
        data = {"balance": 500}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is False

    def test_evaluate_paused_trigger(self, trigger_service, sample_trigger):
        """Trigger en pause ne se déclenche pas."""
        sample_trigger.status = TriggerStatus.PAUSED
        data = {"balance": -500}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is False

    def test_evaluate_cooldown(self, trigger_service, sample_trigger):
        """Respect du cooldown."""
        sample_trigger.last_triggered_at = datetime.utcnow() - timedelta(minutes=30)
        sample_trigger.cooldown_minutes = 60
        data = {"balance": -500}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is False

    def test_evaluate_cooldown_expired(self, trigger_service, sample_trigger):
        """Cooldown expiré."""
        sample_trigger.last_triggered_at = datetime.utcnow() - timedelta(minutes=90)
        sample_trigger.cooldown_minutes = 60
        data = {"balance": -500}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is True

    def test_compare_eq(self, trigger_service):
        """Opérateur EQ."""
        assert trigger_service._compare("active", "eq", "active") is True
        assert trigger_service._compare("active", "eq", "inactive") is False

    def test_compare_ne(self, trigger_service):
        """Opérateur NE."""
        assert trigger_service._compare("active", "ne", "inactive") is True
        assert trigger_service._compare("active", "ne", "active") is False

    def test_compare_gt(self, trigger_service):
        """Opérateur GT."""
        assert trigger_service._compare(100, "gt", 50) is True
        assert trigger_service._compare(50, "gt", 100) is False

    def test_compare_ge(self, trigger_service):
        """Opérateur GE."""
        assert trigger_service._compare(100, "ge", 100) is True
        assert trigger_service._compare(100, "ge", 50) is True
        assert trigger_service._compare(50, "ge", 100) is False

    def test_compare_lt(self, trigger_service):
        """Opérateur LT."""
        assert trigger_service._compare(50, "lt", 100) is True
        assert trigger_service._compare(100, "lt", 50) is False

    def test_compare_le(self, trigger_service):
        """Opérateur LE."""
        assert trigger_service._compare(100, "le", 100) is True
        assert trigger_service._compare(50, "le", 100) is True
        assert trigger_service._compare(100, "le", 50) is False

    def test_compare_in(self, trigger_service):
        """Opérateur IN."""
        assert trigger_service._compare("PENDING", "in", ["PENDING", "ACTIVE"]) is True
        assert trigger_service._compare("CLOSED", "in", ["PENDING", "ACTIVE"]) is False

    def test_compare_not_in(self, trigger_service):
        """Opérateur NOT_IN."""
        assert trigger_service._compare("CLOSED", "not_in", ["PENDING", "ACTIVE"]) is True
        assert trigger_service._compare("PENDING", "not_in", ["PENDING", "ACTIVE"]) is False

    def test_compare_contains(self, trigger_service):
        """Opérateur CONTAINS."""
        assert trigger_service._compare("Hello World", "contains", "World") is True
        assert trigger_service._compare("Hello World", "contains", "Goodbye") is False

    def test_compare_starts_with(self, trigger_service):
        """Opérateur STARTS_WITH."""
        assert trigger_service._compare("Hello World", "starts_with", "Hello") is True
        assert trigger_service._compare("Hello World", "starts_with", "World") is False

    def test_compare_ends_with(self, trigger_service):
        """Opérateur ENDS_WITH."""
        assert trigger_service._compare("Hello World", "ends_with", "World") is True
        assert trigger_service._compare("Hello World", "ends_with", "Hello") is False

    def test_compare_between(self, trigger_service):
        """Opérateur BETWEEN."""
        assert trigger_service._compare(50, "between", [0, 100]) is True
        assert trigger_service._compare(150, "between", [0, 100]) is False

    def test_compare_is_null(self, trigger_service):
        """Opérateur IS_NULL."""
        assert trigger_service._compare(None, "is_null", None) is True
        assert trigger_service._compare("value", "is_null", None) is False

    def test_compare_is_not_null(self, trigger_service):
        """Opérateur IS_NOT_NULL."""
        assert trigger_service._compare("value", "is_not_null", None) is True
        assert trigger_service._compare(None, "is_not_null", None) is False

    def test_get_nested_field(self, trigger_service):
        """Récupération de champ imbriqué."""
        data = {
            "treasury": {
                "forecast": {
                    "balance": -1000
                }
            }
        }
        value = trigger_service._get_field_value(data, "treasury.forecast.balance")
        assert value == -1000

    def test_evaluate_and_condition(self, trigger_service, sample_trigger):
        """Évaluation condition AND."""
        sample_trigger.condition = json.dumps({
            "and": [
                {"field": "balance", "operator": "lt", "value": 0},
                {"field": "status", "operator": "eq", "value": "CRITICAL"}
            ]
        })
        data = {"balance": -500, "status": "CRITICAL"}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is True

        data2 = {"balance": -500, "status": "NORMAL"}
        result2 = trigger_service.evaluate_trigger(sample_trigger, data2)
        assert result2 is False

    def test_evaluate_or_condition(self, trigger_service, sample_trigger):
        """Évaluation condition OR."""
        sample_trigger.condition = json.dumps({
            "or": [
                {"field": "balance", "operator": "lt", "value": 0},
                {"field": "status", "operator": "eq", "value": "ALERT"}
            ]
        })
        data = {"balance": 500, "status": "ALERT"}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is True

    def test_evaluate_not_condition(self, trigger_service, sample_trigger):
        """Évaluation condition NOT."""
        sample_trigger.condition = json.dumps({
            "not": {"field": "status", "operator": "eq", "value": "INACTIVE"}
        })
        data = {"status": "ACTIVE"}
        result = trigger_service.evaluate_trigger(sample_trigger, data)
        assert result is True

        data2 = {"status": "INACTIVE"}
        result2 = trigger_service.evaluate_trigger(sample_trigger, data2)
        assert result2 is False


# ============================================================================
# TESTS SERVICE - DÉCLENCHEMENT
# ============================================================================

class TestTriggerFiring:
    """Tests du déclenchement des triggers."""

    def test_fire_trigger(self, trigger_service, mock_db, sample_trigger):
        """Déclenchement d'un trigger."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_trigger
        mock_db.query.return_value.filter.return_value.all.return_value = []

        event = trigger_service.fire_trigger(
            trigger=sample_trigger,
            triggered_value="-500",
            condition_details={"balance": -500}
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        assert sample_trigger.trigger_count == 1
        assert sample_trigger.last_triggered_at is not None


# ============================================================================
# TESTS SERVICE - ÉVÉNEMENTS
# ============================================================================

class TestEventManagement:
    """Tests de gestion des événements."""

    def test_resolve_event(self, trigger_service, mock_db):
        """Résolution d'un événement."""
        event = TriggerEvent(
            id=1,
            tenant_id="tenant_test",
            trigger_id=1,
            severity=AlertSeverity.WARNING,
            resolved=False
        )
        mock_db.query.return_value.filter.return_value.first.return_value = event

        result = trigger_service.resolve_event(
            event_id=1,
            resolved_by=10,
            resolution_notes="Problème résolu"
        )

        assert result.resolved is True
        assert result.resolved_by == 10
        assert result.resolved_at is not None

    def test_resolve_already_resolved(self, trigger_service, mock_db):
        """Résolution d'un événement déjà résolu."""
        event = TriggerEvent(
            id=1,
            tenant_id="tenant_test",
            trigger_id=1,
            severity=AlertSeverity.WARNING,
            resolved=True
        )
        mock_db.query.return_value.filter.return_value.first.return_value = event

        with pytest.raises(ValueError, match="déjà résolu"):
            trigger_service.resolve_event(1, 10)

    def test_escalate_event(self, trigger_service, mock_db, sample_trigger):
        """Escalade d'un événement."""
        event = TriggerEvent(
            id=1,
            tenant_id="tenant_test",
            trigger_id=1,
            severity=AlertSeverity.CRITICAL,
            escalation_level=EscalationLevel.L1,
            resolved=False
        )
        event.trigger = sample_trigger
        mock_db.query.return_value.filter.return_value.first.return_value = event
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = trigger_service.escalate_event(1)

        assert result.escalation_level == EscalationLevel.L2
        assert result.escalated_at is not None

    def test_escalate_max_level(self, trigger_service, mock_db):
        """Escalade au niveau maximum."""
        event = TriggerEvent(
            id=1,
            tenant_id="tenant_test",
            trigger_id=1,
            severity=AlertSeverity.EMERGENCY,
            escalation_level=EscalationLevel.L4,
            resolved=False
        )
        mock_db.query.return_value.filter.return_value.first.return_value = event

        with pytest.raises(ValueError, match="maximum atteint"):
            trigger_service.escalate_event(1)


# ============================================================================
# TESTS SERVICE - NOTIFICATIONS
# ============================================================================

class TestNotificationManagement:
    """Tests de gestion des notifications."""

    def test_mark_notification_read(self, trigger_service, mock_db):
        """Marquage d'une notification comme lue."""
        notification = Notification(
            id=1,
            tenant_id="tenant_test",
            event_id=1,
            channel=NotificationChannel.IN_APP,
            body="Test notification",
            status=NotificationStatus.DELIVERED,
            read_at=None
        )
        mock_db.query.return_value.filter.return_value.first.return_value = notification

        result = trigger_service.mark_notification_read(1)

        assert result.read_at is not None
        assert result.status == NotificationStatus.READ

    def test_send_pending_notifications(self, trigger_service, mock_db):
        """Envoi des notifications en attente."""
        notifications = [
            Notification(
                id=1,
                tenant_id="tenant_test",
                event_id=1,
                channel=NotificationChannel.IN_APP,
                body="Test 1",
                status=NotificationStatus.PENDING
            ),
            Notification(
                id=2,
                tenant_id="tenant_test",
                event_id=1,
                channel=NotificationChannel.IN_APP,
                body="Test 2",
                status=NotificationStatus.PENDING
            )
        ]
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = notifications

        count = trigger_service.send_pending_notifications()

        assert count == 2
        mock_db.commit.assert_called()


# ============================================================================
# TESTS SERVICE - RAPPORTS PLANIFIÉS
# ============================================================================

class TestScheduledReports:
    """Tests des rapports planifiés."""

    def test_create_scheduled_report(self, trigger_service, mock_db):
        """Création d'un rapport planifié."""
        report = trigger_service.create_scheduled_report(
            code="WEEKLY_COCKPIT",
            name="Rapport Hebdomadaire Cockpit",
            report_type="cockpit_summary",
            frequency=ReportFrequency.WEEKLY,
            recipients={"users": [1, 2], "roles": ["DAF"]},
            schedule_day=1,
            schedule_time="08:00"
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_calculate_next_generation_daily(self, trigger_service):
        """Calcul prochaine génération - quotidien."""
        report = ScheduledReport(
            frequency=ReportFrequency.DAILY,
            schedule_time="08:00"
        )
        next_gen = trigger_service._calculate_next_generation(report)
        assert next_gen > datetime.utcnow()

    def test_calculate_next_generation_weekly(self, trigger_service):
        """Calcul prochaine génération - hebdomadaire."""
        report = ScheduledReport(
            frequency=ReportFrequency.WEEKLY,
            schedule_day=1,  # Lundi
            schedule_time="09:00"
        )
        next_gen = trigger_service._calculate_next_generation(report)
        assert next_gen > datetime.utcnow()
        assert next_gen.weekday() == 0  # Lundi

    def test_calculate_next_generation_monthly(self, trigger_service):
        """Calcul prochaine génération - mensuel."""
        report = ScheduledReport(
            frequency=ReportFrequency.MONTHLY,
            schedule_day=15,
            schedule_time="10:00"
        )
        next_gen = trigger_service._calculate_next_generation(report)
        assert next_gen > datetime.utcnow()
        assert next_gen.day == 15


# ============================================================================
# TESTS SERVICE - TEMPLATES
# ============================================================================

class TestTemplateManagement:
    """Tests de gestion des templates."""

    def test_create_template(self, trigger_service, mock_db):
        """Création d'un template."""
        template = trigger_service.create_template(
            code="CUSTOM_ALERT",
            name="Alerte Personnalisée",
            body_template="Alerte: {{trigger_name}} - {{severity}}",
            subject_template="[{{severity}}] {{trigger_name}}",
            available_variables=["trigger_name", "severity"]
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_render_template(self, trigger_service):
        """Rendu d'un template."""
        template = "Alerte: {{trigger_name}} - Sévérité: {{severity}}"
        variables = {"trigger_name": "Solde négatif", "severity": "CRITICAL"}
        result = trigger_service._render_template(template, variables)
        assert result == "Alerte: Solde négatif - Sévérité: CRITICAL"


# ============================================================================
# TESTS SERVICE - WEBHOOKS
# ============================================================================

class TestWebhookManagement:
    """Tests de gestion des webhooks."""

    def test_create_webhook(self, trigger_service, mock_db):
        """Création d'un webhook."""
        webhook = trigger_service.create_webhook(
            code="SLACK_ALERTS",
            name="Webhook Slack",
            url="https://hooks.slack.com/services/xxx",
            method="POST",
            auth_type="bearer",
            auth_config={"token": "xxx"}
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()


# ============================================================================
# TESTS MODÈLES
# ============================================================================

class TestModels:
    """Tests des modèles SQLAlchemy."""

    def test_trigger_model(self):
        """Test du modèle Trigger."""
        trigger = Trigger(
            tenant_id="test",
            code="TEST",
            name="Test Trigger",
            trigger_type=TriggerType.THRESHOLD,
            status=TriggerStatus.ACTIVE,
            source_module="treasury",
            condition='{"field": "balance", "operator": "lt", "value": 0}',
            severity=AlertSeverity.WARNING
        )
        assert trigger.code == "TEST"
        assert trigger.trigger_type == TriggerType.THRESHOLD

    def test_trigger_event_model(self):
        """Test du modèle TriggerEvent."""
        event = TriggerEvent(
            tenant_id="test",
            trigger_id=1,
            severity=AlertSeverity.CRITICAL,
            escalation_level=EscalationLevel.L1
        )
        assert event.resolved is False
        assert event.escalation_level == EscalationLevel.L1

    def test_notification_model(self):
        """Test du modèle Notification."""
        notification = Notification(
            tenant_id="test",
            event_id=1,
            channel=NotificationChannel.EMAIL,
            body="Test notification"
        )
        assert notification.status == NotificationStatus.PENDING
        assert notification.retry_count == 0

    def test_scheduled_report_model(self):
        """Test du modèle ScheduledReport."""
        report = ScheduledReport(
            tenant_id="test",
            code="WEEKLY",
            name="Rapport Hebdo",
            report_type="summary",
            frequency=ReportFrequency.WEEKLY,
            recipients='{"users": [1, 2]}'
        )
        assert report.frequency == ReportFrequency.WEEKLY
        assert report.output_format == "PDF"


# ============================================================================
# TESTS INTÉGRATION (API)
# ============================================================================

class TestAPIIntegration:
    """Tests d'intégration API (nécessite FastAPI TestClient)."""

    @pytest.mark.skip(reason="Nécessite configuration TestClient complète")
    def test_create_trigger_api(self):
        """Test création trigger via API."""
        pass

    @pytest.mark.skip(reason="Nécessite configuration TestClient complète")
    def test_list_triggers_api(self):
        """Test liste triggers via API."""
        pass

    @pytest.mark.skip(reason="Nécessite configuration TestClient complète")
    def test_fire_trigger_api(self):
        """Test déclenchement trigger via API."""
        pass


# ============================================================================
# TESTS DE PERFORMANCE
# ============================================================================

class TestPerformance:
    """Tests de performance."""

    def test_evaluate_complex_condition_performance(self, trigger_service, sample_trigger):
        """Performance évaluation condition complexe."""
        complex_condition = {
            "and": [
                {"or": [
                    {"field": f"field_{i}", "operator": "eq", "value": i}
                    for i in range(10)
                ]}
                for _ in range(5)
            ]
        }
        sample_trigger.condition = json.dumps(complex_condition)

        data = {f"field_{i}": i for i in range(10)}

        import time
        start = time.time()
        for _ in range(1000):
            trigger_service.evaluate_trigger(sample_trigger, data)
        elapsed = time.time() - start

        assert elapsed < 1.0  # 1000 évaluations en moins d'1 seconde


# ============================================================================
# TOTAL: 48 TESTS
# ============================================================================
