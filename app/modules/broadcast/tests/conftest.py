"""
Configuration des tests pour le module broadcast v2.

Hérite des fixtures globales de app/conftest.py.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.modules.broadcast.models import (
    BroadcastFrequency,
    BroadcastStatus,
    ContentType,
    DeliveryChannel,
    DeliveryStatus,
    RecipientType,
)


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


# ============================================================================
# FIXTURES DE DONNÉES
# ============================================================================

@pytest.fixture
def template_data():
    """Données d'un template de diffusion."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "code": "TMPL001",
        "name": "Template Test",
        "content_type": ContentType.EMAIL,
        "subject_template": "Sujet: {{title}}",
        "body_template": "Corps: {{message}}",
        "html_template": "<html>{{content}}</html>",
        "default_channel": DeliveryChannel.EMAIL,
        "available_channels": '["EMAIL", "SMS"]',
        "variables": '{"title": "string", "message": "string"}',
        "styling": '{"theme": "modern"}',
        "data_sources": '[{"type": "database", "query": "SELECT * FROM users"}]',
        "language": "fr",
        "is_active": True,
        "is_system": False,
        "created_by": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def recipient_list_data():
    """Données d'une liste de destinataires."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "code": "LIST001",
        "name": "Liste Test",
        "description": "Liste de test",
        "is_dynamic": False,
        "query_config": None,
        "total_recipients": 0,
        "active_recipients": 0,
        "is_active": True,
        "created_by": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def recipient_member_data():
    """Données d'un membre de liste."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "list_id": 1,
        "recipient_type": RecipientType.USER,
        "user_id": 123,
        "group_id": None,
        "role_code": None,
        "external_email": None,
        "external_name": None,
        "preferred_channel": DeliveryChannel.EMAIL,
        "is_active": True,
        "is_unsubscribed": False,
        "added_by": 1,
        "added_at": datetime.utcnow()
    }


@pytest.fixture
def broadcast_data():
    """Données d'une diffusion programmée."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "code": "BROAD001",
        "name": "Diffusion Test",
        "content_type": ContentType.EMAIL,
        "frequency": BroadcastFrequency.DAILY,
        "delivery_channel": DeliveryChannel.EMAIL,
        "template_id": 1,
        "recipient_list_id": 1,
        "subject": "Sujet test",
        "body_content": "Contenu test",
        "html_content": "<p>Contenu HTML</p>",
        "cron_expression": None,
        "timezone": "Europe/Paris",
        "start_date": datetime.utcnow(),
        "end_date": datetime.utcnow() + timedelta(days=30),
        "send_time": "09:00",
        "day_of_week": None,
        "day_of_month": None,
        "data_query": None,
        "data_filters": None,
        "additional_channels": None,
        "status": BroadcastStatus.DRAFT,
        "is_active": True,
        "total_sent": 0,
        "total_delivered": 0,
        "total_failed": 0,
        "last_run_at": None,
        "next_run_at": datetime.utcnow() + timedelta(hours=1),
        "last_error": None,
        "created_by": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def execution_data():
    """Données d'une exécution de diffusion."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "scheduled_broadcast_id": 1,
        "execution_number": 1,
        "started_at": datetime.utcnow(),
        "completed_at": datetime.utcnow() + timedelta(minutes=5),
        "duration_seconds": 300,
        "status": DeliveryStatus.DELIVERED,
        "total_recipients": 10,
        "sent_count": 10,
        "delivered_count": 10,
        "failed_count": 0,
        "bounced_count": 0,
        "opened_count": 5,
        "clicked_count": 2,
        "unsubscribed_count": 0,
        "generated_subject": "Sujet généré",
        "generated_content": "Contenu généré",
        "error_message": None,
        "triggered_by": "scheduler",
        "triggered_user": None
    }


@pytest.fixture
def delivery_detail_data():
    """Données d'un détail de livraison."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "execution_id": 1,
        "recipient_type": RecipientType.USER,
        "user_id": 123,
        "email": "test@example.com",
        "phone": None,
        "channel": DeliveryChannel.EMAIL,
        "status": DeliveryStatus.DELIVERED,
        "tracking_id": "track-123",
        "sent_at": datetime.utcnow(),
        "delivered_at": datetime.utcnow() + timedelta(seconds=30),
        "opened_at": None,
        "clicked_at": None,
        "bounced_at": None,
        "bounce_reason": None,
        "error_message": None
    }


@pytest.fixture
def preference_data():
    """Données de préférences utilisateur."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "user_id": 123,
        "preferred_channel": DeliveryChannel.EMAIL,
        "is_unsubscribed_all": False,
        "excluded_content_types": None,
        "excluded_broadcasts": None,
        "receive_digest": True,
        "digest_frequency": BroadcastFrequency.WEEKLY,
        "receive_reports": True,
        "report_frequency": BroadcastFrequency.MONTHLY,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
        "unsubscribed_at": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def metric_data():
    """Données de métriques."""
    return {
        "id": 1,
        "tenant_id": "test-tenant",
        "metric_date": datetime.utcnow().date(),
        "period_type": "DAILY",
        "total_broadcasts": 5,
        "active_broadcasts": 3,
        "total_executions": 10,
        "total_messages": 100,
        "delivered_count": 95,
        "failed_count": 5,
        "opened_count": 60,
        "clicked_count": 20,
        "bounced_count": 2,
        "unsubscribed_count": 1,
        "delivery_rate": 95.0,
        "open_rate": 63.16,
        "click_rate": 33.33,
        "bounce_rate": 2.0,
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def dashboard_stats():
    """Statistiques du dashboard."""
    return {
        "total_broadcasts": 10,
        "active_broadcasts": 5,
        "executions_this_week": 25,
        "messages_sent_this_week": 500,
        "delivery_rate": 95.5,
        "open_rate": 62.3,
        "upcoming_broadcasts": [
            {
                "id": 1,
                "name": "Diffusion 1",
                "next_run_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            },
            {
                "id": 2,
                "name": "Diffusion 2",
                "next_run_at": (datetime.utcnow() + timedelta(hours=5)).isoformat()
            }
        ]
    }


# ============================================================================
# MOCKS
# ============================================================================

@pytest.fixture
def mock_broadcast_service():
    """Mock du BroadcastService."""
    service = MagicMock()

    # Configuration des méthodes par défaut
    service.create_template.return_value = None
    service.get_template.return_value = None
    service.get_template_by_code.return_value = None
    service.list_templates.return_value = ([], 0)
    service.update_template.return_value = None
    service.delete_template.return_value = True

    service.create_recipient_list.return_value = None
    service.get_recipient_list.return_value = None
    service.list_recipient_lists.return_value = ([], 0)
    service.add_member_to_list.return_value = None
    service.get_list_members.return_value = ([], 0)
    service.remove_member_from_list.return_value = True

    service.create_scheduled_broadcast.return_value = None
    service.get_scheduled_broadcast.return_value = None
    service.list_scheduled_broadcasts.return_value = ([], 0)
    service.update_scheduled_broadcast.return_value = None
    service.activate_broadcast.return_value = None
    service.pause_broadcast.return_value = None
    service.cancel_broadcast.return_value = None
    service.execute_broadcast.return_value = None

    service.list_executions.return_value = ([], 0)
    service.get_execution.return_value = None
    service.get_delivery_details.return_value = ([], 0)

    service.get_user_preferences.return_value = None
    service.set_user_preferences.return_value = None
    service.unsubscribe_user.return_value = True

    service.get_metrics.return_value = []
    service.record_metrics.return_value = None
    service.get_dashboard_stats.return_value = {}
    service.get_broadcasts_due.return_value = []

    return service


@pytest.fixture
def auth_headers(tenant_id):
    """Headers d'authentification avec tenant ID."""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": tenant_id
    }
