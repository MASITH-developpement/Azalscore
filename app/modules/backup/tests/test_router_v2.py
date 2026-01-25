"""
Tests pour Backup Router v2 (CORE SaaS)
"""

import pytest
from unittest.mock import MagicMock


# ============================================================================
# TESTS CONFIGURATION
# ============================================================================

def test_create_config_success(client, backup_config_data, backup_config, mock_backup_service):
    """Test création configuration backup avec succès"""
    mock_backup_service.get_config.return_value = None
    mock_backup_service.create_config.return_value = MagicMock(**backup_config)

    response = client.post("/v2/backup/config", json=backup_config_data)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == backup_config["id"]
    assert data["frequency"] == backup_config_data["frequency"]
    assert data["encryption_algorithm"] == "AES-256-GCM"
    assert data["is_active"] is True


def test_create_config_already_exists(client, backup_config_data, backup_config, mock_backup_service):
    """Test création configuration backup - config déjà existante"""
    mock_backup_service.get_config.return_value = MagicMock(**backup_config)

    response = client.post("/v2/backup/config", json=backup_config_data)

    assert response.status_code == 409
    assert "Configuration déjà existante" in response.json()["detail"]


def test_get_config_success(client, backup_config, mock_backup_service):
    """Test récupération configuration backup avec succès"""
    mock_backup_service.get_config.return_value = MagicMock(**backup_config)

    response = client.get("/v2/backup/config")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == backup_config["id"]
    assert data["tenant_id"] == backup_config["tenant_id"]
    assert data["encryption_algorithm"] == "AES-256-GCM"


def test_get_config_not_found(client, mock_backup_service):
    """Test récupération configuration backup - non trouvée"""
    mock_backup_service.get_config.return_value = None

    response = client.get("/v2/backup/config")

    assert response.status_code == 404
    assert "Configuration non trouvée" in response.json()["detail"]


def test_update_config_success(client, backup_config, mock_backup_service):
    """Test mise à jour configuration backup avec succès"""
    update_data = {"frequency": "WEEKLY", "retention_days": 120}
    updated_config = {**backup_config, **update_data}
    mock_backup_service.update_config.return_value = MagicMock(**updated_config)

    response = client.patch("/v2/backup/config", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["frequency"] == "WEEKLY"
    assert data["retention_days"] == 120


def test_update_config_not_found(client, mock_backup_service):
    """Test mise à jour configuration backup - non trouvée"""
    mock_backup_service.update_config.return_value = None

    response = client.patch("/v2/backup/config", json={"frequency": "WEEKLY"})

    assert response.status_code == 404
    assert "Configuration non trouvée" in response.json()["detail"]


# ============================================================================
# TESTS BACKUPS
# ============================================================================

def test_create_backup_success(client, backup_data, backup, mock_backup_service):
    """Test création backup manuel avec succès"""
    mock_backup_service.create_backup.return_value = MagicMock(**backup)

    response = client.post("/v2/backup", json=backup_data)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == backup["id"]
    assert data["reference"].startswith("BKP-")
    assert data["backup_type"] == backup_data["backup_type"]
    assert data["status"] == "COMPLETED"
    assert data["is_encrypted"] is True


def test_create_backup_no_config(client, backup_data, mock_backup_service):
    """Test création backup - configuration non trouvée"""
    mock_backup_service.create_backup.side_effect = ValueError("Configuration backup requise")

    response = client.post("/v2/backup", json=backup_data)

    assert response.status_code == 400
    assert "Configuration backup requise" in response.json()["detail"]


def test_list_backups_success(client, backup_list, mock_backup_service):
    """Test liste des backups avec succès"""
    mock_backup_service.list_backups.return_value = ([MagicMock(**b) for b in backup_list], len(backup_list))

    response = client.get("/v2/backup")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(backup_list)
    assert data[0]["id"] == backup_list[0]["id"]
    assert data[0]["status"] == "COMPLETED"


def test_list_backups_with_status_filter(client, backup_list, mock_backup_service):
    """Test liste des backups avec filtre status"""
    completed_backups = [b for b in backup_list if b["status"] == "COMPLETED"]
    mock_backup_service.list_backups.return_value = ([MagicMock(**b) for b in completed_backups], len(completed_backups))

    response = client.get("/v2/backup?status=COMPLETED")

    assert response.status_code == 200
    data = response.json()
    assert all(b["status"] == "COMPLETED" for b in data)


def test_list_backups_with_pagination(client, backup_list, mock_backup_service):
    """Test liste des backups avec pagination"""
    mock_backup_service.list_backups.return_value = ([MagicMock(**backup_list[0])], 1)

    response = client.get("/v2/backup?skip=0&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_backup_success(client, backup, mock_backup_service):
    """Test récupération d'un backup avec succès"""
    mock_backup_service.get_backup.return_value = MagicMock(**backup)

    response = client.get(f"/v2/backup/{backup['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == backup["id"]
    assert data["reference"] == backup["reference"]
    assert "tables_included" in data
    assert "encryption_iv" in data


def test_get_backup_not_found(client, mock_backup_service):
    """Test récupération d'un backup - non trouvé"""
    mock_backup_service.get_backup.return_value = None

    response = client.get("/v2/backup/fake-backup-id")

    assert response.status_code == 404
    assert "Sauvegarde non trouvée" in response.json()["detail"]


def test_delete_backup_success(client, backup, mock_backup_service):
    """Test suppression d'un backup avec succès"""
    mock_backup = MagicMock(**backup)
    mock_backup_service.get_backup.return_value = mock_backup

    response = client.delete(f"/v2/backup/{backup['id']}")

    assert response.status_code == 204
    # Vérifier que le status a été changé à DELETED
    assert mock_backup.status == "DELETED"


def test_delete_backup_not_found(client, mock_backup_service):
    """Test suppression d'un backup - non trouvé"""
    mock_backup_service.get_backup.return_value = None

    response = client.delete("/v2/backup/fake-backup-id")

    assert response.status_code == 404
    assert "Sauvegarde non trouvée" in response.json()["detail"]


def test_run_backup_success(client, backup, mock_backup_service):
    """Test exécution d'un backup depuis une référence existante"""
    existing_backup = MagicMock(**backup)
    new_backup = {**backup, "id": "new-backup-id", "reference": "BKP-NEW-20260125140000"}
    mock_backup_service.get_backup.return_value = existing_backup
    mock_backup_service.create_backup.return_value = MagicMock(**new_backup)

    response = client.post(f"/v2/backup/{backup['id']}/run")

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == new_backup["id"]
    assert "Re-exécution" in data["notes"]


def test_run_backup_reference_not_found(client, mock_backup_service):
    """Test exécution d'un backup - référence non trouvée"""
    mock_backup_service.get_backup.return_value = None

    response = client.post("/v2/backup/fake-backup-id/run")

    assert response.status_code == 404
    assert "Sauvegarde de référence non trouvée" in response.json()["detail"]


# ============================================================================
# TESTS RESTAURATION
# ============================================================================

def test_restore_backup_success(client, restore_request_data, restore_log, mock_backup_service):
    """Test restauration d'un backup avec succès"""
    mock_backup_service.restore_backup.return_value = MagicMock(**restore_log)

    response = client.post("/v2/backup/restore", json=restore_request_data)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == restore_log["id"]
    assert data["backup_id"] == restore_request_data["backup_id"]
    assert data["status"] == "COMPLETED"
    assert data["records_restored"] == 150


def test_restore_backup_not_found(client, restore_request_data, mock_backup_service):
    """Test restauration d'un backup - backup non trouvé"""
    mock_backup_service.restore_backup.side_effect = ValueError("Sauvegarde non trouvée")

    response = client.post("/v2/backup/restore", json=restore_request_data)

    assert response.status_code == 400
    assert "Sauvegarde non trouvée" in response.json()["detail"]


def test_restore_backup_invalid_status(client, restore_request_data, mock_backup_service):
    """Test restauration d'un backup - status invalide"""
    mock_backup_service.restore_backup.side_effect = ValueError("Sauvegarde non valide pour restauration")

    response = client.post("/v2/backup/restore", json=restore_request_data)

    assert response.status_code == 400
    assert "Sauvegarde non valide" in response.json()["detail"]


# ============================================================================
# TESTS DASHBOARD
# ============================================================================

def test_get_dashboard_success(client, backup_dashboard, mock_backup_service):
    """Test récupération du dashboard backup avec succès"""
    mock_backup_service.get_dashboard.return_value = MagicMock(**backup_dashboard)

    response = client.get("/v2/backup/dashboard/stats")

    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert "stats" in data
    assert "recent_backups" in data
    assert "recent_restores" in data
    assert data["stats"]["total_backups"] == 10
    assert data["stats"]["success_rate"] == 95.5


def test_get_dashboard_no_config(client, backup_dashboard, mock_backup_service):
    """Test récupération du dashboard backup sans configuration"""
    dashboard_no_config = {**backup_dashboard, "config": None}
    mock_backup_service.get_dashboard.return_value = MagicMock(**dashboard_no_config)

    response = client.get("/v2/backup/dashboard/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["config"] is None
    assert "stats" in data
