"""
Tests de sécurité multi-tenant - Module Integrations (GAP-086)

CRITIQUE: Ces tests vérifient l'isolation entre tenants.
Un échec = faille de sécurité majeure.
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.modules.integrations.models import (
    ConnectionStatus, SyncStatus, ConnectorType, SyncDirection
)
from app.modules.integrations.repository import (
    ConnectionRepository, EntityMappingRepository, SyncJobRepository,
    ConflictRepository
)


class TestConnectionTenantIsolation:
    """Tests isolation tenant pour Connection."""

    def test_cannot_access_other_tenant_connection(
        self, db_session, tenant_a_id, tenant_b_id, connection_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les connexions de tenant B."""
        repo_a = ConnectionRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(connection_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_cannot_list_other_tenant_connections(
        self, db_session, tenant_a_id, tenant_b_id, connection_tenant_a, connection_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les connexions du tenant courant."""
        repo_a = ConnectionRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        conn_ids = [c.id for c in items]
        assert connection_tenant_a.id in conn_ids, "Connexion du tenant A manquante"
        assert connection_tenant_b.id not in conn_ids, "FAILLE: Connexion tenant B visible!"

    def test_code_uniqueness_per_tenant(
        self, db_session, tenant_a_id, tenant_b_id, connection_tenant_a, connection_tenant_b
    ):
        """Les codes sont uniques par tenant, pas globalement."""
        repo_a = ConnectionRepository(db_session, tenant_a_id)
        repo_b = ConnectionRepository(db_session, tenant_b_id)

        assert repo_a.code_exists(connection_tenant_a.code) is True
        assert repo_b.code_exists(connection_tenant_a.code) is False

    def test_get_by_type_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, connection_tenant_a, connection_tenant_b
    ):
        """get_by_type respecte l'isolation tenant."""
        repo_b = ConnectionRepository(db_session, tenant_b_id)
        connections = repo_b.get_by_type(ConnectorType.STRIPE)

        # Tenant B n'a pas de connexion Stripe
        conn_ids = [c.id for c in connections]
        assert connection_tenant_a.id not in conn_ids

    def test_autocomplete_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, connection_tenant_a, connection_tenant_b
    ):
        """Autocomplete ne retourne que les connexions du tenant courant."""
        repo_a = ConnectionRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("CONN")

        codes = [r["code"] for r in results]
        assert connection_tenant_a.code in codes
        assert connection_tenant_b.code not in codes


class TestEntityMappingTenantIsolation:
    """Tests isolation tenant pour EntityMapping."""

    def test_cannot_access_other_tenant_mapping(
        self, db_session, tenant_a_id, tenant_b_id, mapping_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les mappings de tenant B."""
        repo_a = EntityMappingRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(mapping_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_get_by_connection_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, mapping_tenant_a, mapping_tenant_b, connection_tenant_a
    ):
        """get_by_connection respecte l'isolation tenant."""
        repo_b = EntityMappingRepository(db_session, tenant_b_id)
        mappings = repo_b.get_by_connection(connection_tenant_a.id)

        # Connexion A n'appartient pas à tenant B
        mapping_ids = [m.id for m in mappings]
        assert mapping_tenant_a.id not in mapping_ids


class TestSyncJobTenantIsolation:
    """Tests isolation tenant pour SyncJob."""

    def test_cannot_access_other_tenant_job(
        self, db_session, tenant_a_id, tenant_b_id, sync_job_tenant_a
    ):
        """CRITIQUE: Tenant B ne peut pas voir les jobs de tenant A."""
        repo_b = SyncJobRepository(db_session, tenant_b_id)
        result = repo_b.get_by_id(sync_job_tenant_a.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_cannot_list_other_tenant_jobs(
        self, db_session, tenant_a_id, tenant_b_id, sync_job_tenant_a
    ):
        """Liste ne retourne que les jobs du tenant courant."""
        repo_b = SyncJobRepository(db_session, tenant_b_id)
        items, total = repo_b.list()

        job_ids = [j.id for j in items]
        assert sync_job_tenant_a.id not in job_ids

    def test_get_running_for_connection_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, connection_tenant_a
    ):
        """get_running_for_connection respecte l'isolation tenant."""
        repo_b = SyncJobRepository(db_session, tenant_b_id)
        running = repo_b.get_running_for_connection(connection_tenant_a.id)
        assert running is None


class TestConflictTenantIsolation:
    """Tests isolation tenant pour Conflict."""

    def test_cannot_access_other_tenant_conflict(
        self, db_session, tenant_a_id, tenant_b_id, conflict_tenant_a
    ):
        """CRITIQUE: Tenant B ne peut pas voir les conflits de tenant A."""
        repo_b = ConflictRepository(db_session, tenant_b_id)
        result = repo_b.get_by_id(conflict_tenant_a.id)
        assert result is None, "FAILLE SECURITE: Accès cross-tenant détecté!"

    def test_get_pending_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id, conflict_tenant_a
    ):
        """get_pending ne retourne que les conflits du tenant courant."""
        repo_b = ConflictRepository(db_session, tenant_b_id)
        conflicts = repo_b.get_pending()

        conflict_ids = [c.id for c in conflicts]
        assert conflict_tenant_a.id not in conflict_ids


class TestSoftDeleteIsolation:
    """Tests soft delete avec isolation tenant."""

    def test_soft_deleted_connection_hidden_by_default(
        self, db_session, tenant_a_id, user_id, connection_tenant_a
    ):
        """Connexion soft-deleted n'apparaît pas par défaut."""
        repo = ConnectionRepository(db_session, tenant_a_id)
        repo.soft_delete(connection_tenant_a, user_id)

        result = repo.get_by_id(connection_tenant_a.id)
        assert result is None

    def test_soft_deleted_visible_with_include_deleted(
        self, db_session, tenant_a_id, user_id, connection_tenant_a
    ):
        """Connexion soft-deleted visible avec include_deleted=True."""
        repo = ConnectionRepository(db_session, tenant_a_id)
        repo.soft_delete(connection_tenant_a, user_id)

        repo_with_deleted = ConnectionRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_with_deleted.get_by_id(connection_tenant_a.id)
        assert result is not None
        assert result.is_deleted is True

    def test_soft_deleted_other_tenant_still_hidden(
        self, db_session, tenant_a_id, tenant_b_id, user_id, connection_tenant_b
    ):
        """Connexion soft-deleted d'un autre tenant reste invisible."""
        repo_b = ConnectionRepository(db_session, tenant_b_id)
        repo_b.soft_delete(connection_tenant_b, user_id)

        repo_a_with_deleted = ConnectionRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_a_with_deleted.get_by_id(connection_tenant_b.id)
        assert result is None


class TestConnectionStatus:
    """Tests de gestion du statut de connexion."""

    def test_update_status_connected(
        self, db_session, tenant_a_id, connection_tenant_a
    ):
        """Mise à jour statut CONNECTED réinitialise les erreurs."""
        repo = ConnectionRepository(db_session, tenant_a_id)

        # Simuler des erreurs
        connection_tenant_a.consecutive_errors = 5
        connection_tenant_a.last_error = "Previous error"
        db_session.commit()

        repo.update_status(connection_tenant_a, ConnectionStatus.CONNECTED)

        assert connection_tenant_a.status == ConnectionStatus.CONNECTED.value
        assert connection_tenant_a.consecutive_errors == 0
        assert connection_tenant_a.last_error is None
        assert connection_tenant_a.last_connected_at is not None

    def test_update_status_error_increments_counter(
        self, db_session, tenant_a_id, connection_tenant_a
    ):
        """Mise à jour statut ERROR incrémente le compteur."""
        repo = ConnectionRepository(db_session, tenant_a_id)
        initial_errors = connection_tenant_a.consecutive_errors or 0

        repo.update_status(connection_tenant_a, ConnectionStatus.ERROR, "Test error")

        assert connection_tenant_a.status == ConnectionStatus.ERROR.value
        assert connection_tenant_a.consecutive_errors == initial_errors + 1
        assert connection_tenant_a.last_error == "Test error"


class TestSyncJobWorkflow:
    """Tests du workflow de job de synchronisation."""

    def test_start_job(
        self, db_session, tenant_a_id, user_id, connection_tenant_a, mapping_tenant_a
    ):
        """Démarrer un job change son statut."""
        repo = SyncJobRepository(db_session, tenant_a_id)

        job = repo.create({
            "connection_id": connection_tenant_a.id,
            "entity_mapping_id": mapping_tenant_a.id,
            "direction": SyncDirection.IMPORT.value
        }, user_id)

        assert job.status == SyncStatus.PENDING.value

        repo.start(job)

        assert job.status == SyncStatus.RUNNING.value
        assert job.started_at is not None

    def test_complete_job(
        self, db_session, tenant_a_id, user_id, connection_tenant_a, mapping_tenant_a
    ):
        """Compléter un job enregistre les statistiques."""
        repo = SyncJobRepository(db_session, tenant_a_id)

        job = repo.create({
            "connection_id": connection_tenant_a.id,
            "entity_mapping_id": mapping_tenant_a.id,
            "direction": SyncDirection.IMPORT.value
        }, user_id)
        repo.start(job)

        repo.complete(job, SyncStatus.COMPLETED, 100, 80, 15, 5, 0)

        assert job.status == SyncStatus.COMPLETED.value
        assert job.completed_at is not None
        assert job.total_records == 100
        assert job.created_records == 80
        assert job.updated_records == 15
        assert job.skipped_records == 5
        assert job.failed_records == 0

    def test_cancel_running_job(
        self, db_session, tenant_a_id, user_id, connection_tenant_a, mapping_tenant_a
    ):
        """Annuler un job en cours."""
        repo = SyncJobRepository(db_session, tenant_a_id)

        job = repo.create({
            "connection_id": connection_tenant_a.id,
            "entity_mapping_id": mapping_tenant_a.id,
            "direction": SyncDirection.IMPORT.value
        }, user_id)
        repo.start(job)

        repo.cancel(job)

        assert job.status == SyncStatus.CANCELLED.value
        assert job.completed_at is not None


class TestConflictResolution:
    """Tests de résolution de conflits."""

    def test_resolve_conflict(
        self, db_session, tenant_a_id, user_id, conflict_tenant_a
    ):
        """Résoudre un conflit."""
        repo = ConflictRepository(db_session, tenant_a_id)

        resolved_data = {"email": "merged@example.com", "name": "Merged Name"}
        repo.resolve(conflict_tenant_a, "merge", resolved_data, user_id)

        assert conflict_tenant_a.resolution == "merge"
        assert conflict_tenant_a.resolved_data == resolved_data
        assert conflict_tenant_a.resolved_at is not None
        assert conflict_tenant_a.resolved_by == user_id

    def test_resolved_conflict_not_in_pending(
        self, db_session, tenant_a_id, user_id, conflict_tenant_a
    ):
        """Un conflit résolu n'apparaît plus dans les pending."""
        repo = ConflictRepository(db_session, tenant_a_id)

        # Avant résolution
        pending = repo.get_pending()
        assert conflict_tenant_a.id in [c.id for c in pending]

        # Résoudre
        repo.resolve(conflict_tenant_a, "source_wins", {}, user_id)

        # Après résolution
        pending = repo.get_pending()
        assert conflict_tenant_a.id not in [c.id for c in pending]
