"""
Fixtures pour les tests Backup v2

Hérite des fixtures globales de app/conftest.py.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.modules.backup.models import BackupFrequency, BackupStatus, BackupType


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


# ============================================================================
# FIXTURES BACKUP SERVICE
# ============================================================================

@pytest.fixture
def mock_backup_service(monkeypatch):
    """Mock BackupService pour les tests"""
    mock_service = MagicMock()

    def mock_get_backup_service(db, tenant_id, user_id=None):
        return mock_service

    from app.modules.backup import router_v2
    monkeypatch.setattr(router_v2, "get_backup_service", mock_get_backup_service)

    return mock_service


# ============================================================================
# FIXTURES DONNÉES BACKUP CONFIG
# ============================================================================

@pytest.fixture
def backup_config_data():
    """Données de configuration backup sample"""
    return {
        "frequency": "DAILY",
        "backup_hour": 2,
        "backup_day": 0,
        "backup_day_of_month": 1,
        "retention_days": 90,
        "max_backups": 12,
        "storage_path": None,
        "storage_type": "local",
        "include_attachments": True,
        "compress": True,
        "verify_after_backup": True,
    }


@pytest.fixture
def backup_config(backup_config_data, tenant_id):
    """Instance configuration backup sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "encryption_key_encrypted": "encrypted_key_base64",
        "encryption_algorithm": "AES-256-GCM",
        "frequency": backup_config_data["frequency"],
        "backup_hour": backup_config_data["backup_hour"],
        "backup_day": backup_config_data["backup_day"],
        "backup_day_of_month": backup_config_data["backup_day_of_month"],
        "retention_days": backup_config_data["retention_days"],
        "max_backups": backup_config_data["max_backups"],
        "storage_path": f"/var/azals/backups/{tenant_id}",
        "storage_type": backup_config_data["storage_type"],
        "include_attachments": backup_config_data["include_attachments"],
        "compress": backup_config_data["compress"],
        "verify_after_backup": backup_config_data["verify_after_backup"],
        "is_active": True,
        "last_backup_at": None,
        "next_backup_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# FIXTURES DONNÉES BACKUP
# ============================================================================

@pytest.fixture
def backup_data():
    """Données de backup sample"""
    return {
        "backup_type": "FULL",
        "include_attachments": True,
        "notes": "Test backup manuel",
    }


@pytest.fixture
def backup(backup_data, tenant_id, user_id):
    """Instance backup sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "config_id": str(uuid4()),
        "reference": f"BKP-{tenant_id[:8].upper()}-20260125120000",
        "backup_type": backup_data["backup_type"],
        "status": "COMPLETED",
        "file_name": f"{tenant_id}_20260125_120000.azals.bak",
        "file_path": f"/var/azals/backups/{tenant_id}/{tenant_id}_20260125_120000.azals.bak",
        "file_size": 1024000,
        "file_checksum": "abc123def456",
        "is_encrypted": True,
        "encryption_algorithm": "AES-256-GCM",
        "encryption_iv": "nonce_base64",
        "tables_included": ["users", "commercial_customers", "invoices"],
        "records_count": 150,
        "include_attachments": backup_data["include_attachments"],
        "is_compressed": True,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_seconds": 45,
        "last_restored_at": None,
        "restore_count": 0,
        "notes": backup_data["notes"],
        "error_message": None,
        "triggered_by": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def backup_list(backup):
    """Liste de backups sample"""
    return [
        backup,
        {
            **backup,
            "id": str(uuid4()),
            "reference": f"BKP-TEST-20260124120000",
            "status": "PENDING",
            "file_name": None,
            "file_size": None,
        },
    ]


# ============================================================================
# FIXTURES DONNÉES RESTORE
# ============================================================================

@pytest.fixture
def restore_request_data(backup):
    """Données de requête de restauration sample"""
    return {
        "backup_id": backup["id"],
        "target_type": "same_tenant",
        "target_tenant_id": None,
        "tables_to_restore": None,
    }


@pytest.fixture
def restore_log(restore_request_data, tenant_id, backup, user_id):
    """Instance log de restauration sample"""
    return {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "backup_id": restore_request_data["backup_id"],
        "status": "COMPLETED",
        "target_type": restore_request_data["target_type"],
        "target_tenant_id": restore_request_data["target_tenant_id"],
        "tables_restored": ["users", "commercial_customers", "invoices"],
        "records_restored": 150,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_seconds": 30,
        "error_message": None,
        "restored_by": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# FIXTURES DASHBOARD
# ============================================================================

@pytest.fixture
def backup_stats():
    """Statistiques backup sample"""
    return {
        "total_backups": 10,
        "total_size_bytes": 10240000,
        "last_backup_at": datetime.utcnow().isoformat(),
        "last_backup_status": "COMPLETED",
        "next_backup_at": datetime.utcnow().isoformat(),
        "success_rate": 95.5,
        "average_duration_seconds": 42.5,
    }


@pytest.fixture
def backup_dashboard(backup_config, backup_stats, backup_list, restore_log):
    """Dashboard backup sample"""
    return {
        "config": backup_config,
        "stats": backup_stats,
        "recent_backups": backup_list,
        "recent_restores": [restore_log],
    }
