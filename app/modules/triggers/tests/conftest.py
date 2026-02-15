"""
Configuration pytest et fixtures pour les tests Triggers.

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4


# ============================================================================
# FIXTURES HÉRITÉES DU CONFTEST GLOBAL
# ============================================================================
# Les fixtures suivantes sont héritées de app/conftest.py:
# - tenant_id, user_id, user_uuid
# - db_session, test_db_session
# - test_client (avec headers auto-injectés)
# - mock_auth_global (autouse=True)
# - saas_context


@pytest.fixture
def client(test_client):
    """
    Alias pour test_client (compatibilité avec anciens tests).

    Le test_client du conftest global ajoute déjà les headers requis.
    """
    return test_client


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }


@pytest.fixture
def mock_db(monkeypatch):
    """Mock de la session DB."""
    class MockQuery:
        def __init__(self, model=None):
            self.model = model
            self._filters = []
            self._order_by_clause = None
            self._limit_value = None

        def filter(self, *args):
            self._filters.extend(args)
            return self

        def order_by(self, *args):
            self._order_by_clause = args
            return self

        def limit(self, value):
            self._limit_value = value
            return self

        def first(self):
            return None

        def all(self):
            return []

        def count(self):
            return 0

    class MockDB:
        def __init__(self):
            self.added = []
            self.deleted = []

        def query(self, model):
            return MockQuery(model)

        def add(self, obj):
            self.added.append(obj)

        def delete(self, obj):
            self.deleted.append(obj)

        def commit(self):
            pass

        def rollback(self):
            pass

        def refresh(self, obj):
            pass

        def flush(self):
            pass

    db = MockDB()

    from app.modules.triggers import router_v2
    monkeypatch.setattr(router_v2, "get_db", lambda: db)

    return db


# ============================================================================
# FIXTURES MOCK SERVICE
# ============================================================================

@pytest.fixture
def mock_trigger_service(monkeypatch, tenant_id, user_id):
    """Mock du service Triggers."""
    from app.modules.triggers.models import (
        AlertSeverity,
        EscalationLevel,
        NotificationChannel,
        NotificationStatus,
        ReportFrequency,
        TriggerStatus,
        TriggerType,
    )

    class MockTriggerService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = user_id

        # Triggers
        def create_trigger(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "trigger_type": kwargs.get("trigger_type", TriggerType.THRESHOLD),
                "source_module": kwargs.get("source_module"),
                "condition": kwargs.get("condition"),
                "status": TriggerStatus.ACTIVE,
                "severity": kwargs.get("severity", AlertSeverity.WARNING),
                "trigger_count": 0,
                "created_by": kwargs.get("created_by"),
                "created_at": datetime.utcnow()
            }

        def get_trigger(self, trigger_id):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": "TRIG-001",
                "name": "Trigger Test",
                "trigger_type": TriggerType.THRESHOLD,
                "source_module": "treasury",
                "condition": '{"operator": "lt", "value": 0}',
                "status": TriggerStatus.ACTIVE,
                "severity": AlertSeverity.WARNING
            }

        def get_trigger_by_code(self, code):
            return None  # Permet création sans conflit

        def list_triggers(self, **kwargs):
            return [
                {
                    "id": str(uuid4()),
                    "code": f"TRIG-{i}",
                    "name": f"Trigger {i}",
                    "status": TriggerStatus.ACTIVE
                }
                for i in range(1, 4)
            ]

        def update_trigger(self, trigger_id, **kwargs):
            trigger = self.get_trigger(trigger_id)
            trigger.update(kwargs)
            return trigger

        def delete_trigger(self, trigger_id, **kwargs):
            return True

        def pause_trigger(self, trigger_id):
            trigger = self.get_trigger(trigger_id)
            trigger["status"] = TriggerStatus.PAUSED
            return trigger

        def resume_trigger(self, trigger_id):
            trigger = self.get_trigger(trigger_id)
            trigger["status"] = TriggerStatus.ACTIVE
            return trigger

        def evaluate_trigger(self, trigger, data):
            return True

        def fire_trigger(self, trigger, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "trigger_id": trigger.get("id") if isinstance(trigger, dict) else str(trigger.id),
                "triggered_at": datetime.utcnow(),
                "triggered_value": kwargs.get("triggered_value"),
                "severity": AlertSeverity.WARNING,
                "escalation_level": EscalationLevel.L1,
                "resolved": False
            }

        # Subscriptions
        def subscribe_user(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "trigger_id": kwargs.get("trigger_id"),
                "user_id": kwargs.get("user_id"),
                "channel": kwargs.get("channel", NotificationChannel.IN_APP),
                "escalation_level": kwargs.get("escalation_level", EscalationLevel.L1),
                "is_active": True
            }

        def subscribe_role(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "trigger_id": kwargs.get("trigger_id"),
                "role_code": kwargs.get("role_code"),
                "channel": kwargs.get("channel", NotificationChannel.IN_APP),
                "is_active": True
            }

        def get_trigger_subscriptions(self, trigger_id):
            return [
                {
                    "id": str(uuid4()),
                    "trigger_id": trigger_id,
                    "user_id": str(uuid4()),
                    "channel": NotificationChannel.EMAIL
                }
            ]

        def unsubscribe(self, subscription_id):
            return True

        # Events
        def list_events(self, **kwargs):
            return [
                {
                    "id": str(uuid4()),
                    "trigger_id": str(uuid4()),
                    "triggered_at": datetime.utcnow() - timedelta(hours=i),
                    "severity": AlertSeverity.WARNING,
                    "resolved": False
                }
                for i in range(1, 4)
            ]

        def get_event(self, event_id):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "trigger_id": str(uuid4()),
                "triggered_at": datetime.utcnow(),
                "severity": AlertSeverity.WARNING,
                "resolved": False
            }

        def resolve_event(self, event_id, **kwargs):
            event = self.get_event(event_id)
            event["resolved"] = True
            event["resolved_at"] = datetime.utcnow()
            event["resolved_by"] = kwargs.get("resolved_by")
            return event

        def escalate_event(self, event_id):
            event = self.get_event(event_id)
            event["escalation_level"] = EscalationLevel.L2
            event["escalated_at"] = datetime.utcnow()
            return event

        # Notifications
        def get_user_notifications(self, **kwargs):
            return [
                {
                    "id": str(uuid4()),
                    "event_id": str(uuid4()),
                    "user_id": kwargs.get("user_id"),
                    "channel": NotificationChannel.IN_APP,
                    "subject": f"Notification {i}",
                    "body": "Test notification",
                    "status": NotificationStatus.SENT,
                    "read_at": None if i == 1 else datetime.utcnow()
                }
                for i in range(1, 4)
            ]

        def mark_notification_read(self, notification_id):
            return {
                "id": notification_id,
                "read_at": datetime.utcnow(),
                "status": NotificationStatus.READ
            }

        def send_pending_notifications(self):
            return 5

        # Templates
        def create_template(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "body_template": kwargs.get("body_template"),
                "is_active": True
            }

        def list_templates(self):
            return [
                {
                    "id": str(uuid4()),
                    "code": f"TPL-{i}",
                    "name": f"Template {i}"
                }
                for i in range(1, 3)
            ]

        # Reports
        def create_scheduled_report(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "report_type": kwargs.get("report_type"),
                "frequency": kwargs.get("frequency"),
                "is_active": True,
                "next_generation_at": datetime.utcnow() + timedelta(days=1)
            }

        def list_scheduled_reports(self, **kwargs):
            return [
                {
                    "id": str(uuid4()),
                    "code": f"RPT-{i}",
                    "name": f"Report {i}",
                    "frequency": ReportFrequency.MONTHLY
                }
                for i in range(1, 3)
            ]

        def generate_report(self, report_id, **kwargs):
            return {
                "id": str(uuid4()),
                "report_id": report_id,
                "generated_at": datetime.utcnow(),
                "file_name": f"report_{datetime.utcnow().strftime('%Y%m%d')}.pdf",
                "success": True
            }

        # Webhooks
        def create_webhook(self, **kwargs):
            return {
                "id": str(uuid4()),
                "tenant_id": self.tenant_id,
                "code": kwargs.get("code"),
                "name": kwargs.get("name"),
                "url": kwargs.get("url"),
                "is_active": True
            }

        def list_webhooks(self):
            return [
                {
                    "id": str(uuid4()),
                    "code": f"WHK-{i}",
                    "name": f"Webhook {i}",
                    "url": f"https://example.com/webhook{i}"
                }
                for i in range(1, 3)
            ]

        def get_webhook_decrypted_config(self, webhook_id):
            return {"api_key": "test-key"}

    from app.modules.triggers import router_v2

    def mock_get_service(db, tenant_id, user_id):
        return MockTriggerService(db, tenant_id, user_id)

    monkeypatch.setattr(router_v2, "get_trigger_service", mock_get_service)

    return MockTriggerService(None, tenant_id, user_id)


# ============================================================================
# FIXTURES DONNÉES DE TEST
# ============================================================================

@pytest.fixture
def sample_trigger_data():
    """Données de test pour créer un trigger."""
    return {
        "code": "TRIG-TREASURY-LOW",
        "name": "Alerte Trésorerie Faible",
        "trigger_type": "THRESHOLD",
        "source_module": "treasury",
        "source_entity": "forecast",
        "source_field": "balance",
        "condition": {"operator": "lt", "value": 0},
        "threshold_value": "0",
        "threshold_operator": "lt",
        "severity": "WARNING",
        "escalation_enabled": False,
        "cooldown_minutes": 60
    }


@pytest.fixture
def sample_subscription_data():
    """Données de test pour créer un abonnement."""
    return {
        "trigger_id": str(uuid4()),
        "user_id": str(uuid4()),
        "channel": "EMAIL",
        "escalation_level": "L1"
    }


@pytest.fixture
def sample_template_data():
    """Données de test pour créer un template."""
    return {
        "code": "TPL-ALERT",
        "name": "Template Alerte Standard",
        "subject_template": "[{{severity}}] Alerte: {{trigger_name}}",
        "body_template": "Alerte déclenchée: {{trigger_name}}\nModule: {{source_module}}\nValeur: {{triggered_value}}"
    }


@pytest.fixture
def sample_report_data():
    """Données de test pour créer un rapport planifié."""
    return {
        "code": "RPT-MONTHLY",
        "name": "Rapport Mensuel",
        "report_type": "cockpit_summary",
        "frequency": "MONTHLY",
        "schedule_day": 1,
        "schedule_time": "09:00",
        "recipients": {"users": [str(uuid4())], "roles": ["DAF"]},
        "output_format": "PDF"
    }


@pytest.fixture
def sample_webhook_data():
    """Données de test pour créer un webhook."""
    return {
        "code": "WHK-SLACK",
        "name": "Webhook Slack",
        "url": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
        "method": "POST",
        "auth_type": "none"
    }
