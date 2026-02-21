"""
Tests de securite multi-tenant - Module Appointments

CRITIQUE: Ces tests verifient l'isolation entre tenants.
Un echec = faille de securite majeure.

Conformite AZALSCORE:
- Chaque tenant ne doit voir que ses propres donnees
- Soft delete doit etre respecte
- Les recherches et autocomplete doivent etre isolees
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta, date

from app.modules.appointments.repository import (
    AppointmentRepository,
    AppointmentTypeRepository,
    ResourceRepository,
    AttendeeRepository,
    AvailabilityRepository,
    WaitlistRepository,
)
from app.modules.appointments.models import (
    AppointmentStatus,
    AppointmentMode,
    AvailabilityType,
)


class TestAppointmentTenantIsolation:
    """Tests d'isolation tenant pour les rendez-vous."""

    def test_cannot_access_other_tenant_appointment(
        self, db_session, tenant_a_id, tenant_b_id, appointment_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les rendez-vous de tenant B."""
        repo_a = AppointmentRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(appointment_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Acces cross-tenant detecte!"

    def test_cannot_list_other_tenant_appointments(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_tenant_a, appointment_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les rendez-vous du tenant courant."""
        repo_a = AppointmentRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        appointment_ids = [a.id for a in items]
        assert appointment_tenant_a.id in appointment_ids, "RDV du tenant A manquant"
        assert appointment_tenant_b.id not in appointment_ids, "FAILLE: RDV tenant B visible!"

    def test_cannot_get_appointment_by_confirmation_code_cross_tenant(
        self, db_session, tenant_a_id, tenant_b_id, appointment_tenant_b
    ):
        """CRITIQUE: Code de confirmation ne fonctionne que pour le bon tenant."""
        repo_a = AppointmentRepository(db_session, tenant_a_id)
        result = repo_a.get_by_confirmation_code(appointment_tenant_b.confirmation_code)
        assert result is None, "FAILLE: Acces par code de confirmation cross-tenant!"

    def test_code_uniqueness_per_tenant(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_tenant_a, appointment_tenant_b
    ):
        """Les codes sont uniques par tenant, pas globalement."""
        repo_a = AppointmentRepository(db_session, tenant_a_id)
        repo_b = AppointmentRepository(db_session, tenant_b_id)

        # Le code de A existe pour A
        assert repo_a.code_exists(appointment_tenant_a.code) is True
        # Le code de A n'existe pas pour B
        assert repo_b.code_exists(appointment_tenant_a.code) is False

    def test_autocomplete_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_tenant_a, appointment_tenant_b
    ):
        """Autocomplete ne retourne que les rendez-vous du tenant courant."""
        repo_a = AppointmentRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("RDV")

        result_ids = [r["id"] for r in results]
        assert str(appointment_tenant_a.id) in result_ids
        assert str(appointment_tenant_b.id) not in result_ids

    def test_get_day_schedule_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_tenant_a, appointment_tenant_b
    ):
        """Le planning journalier est isole par tenant."""
        repo_a = AppointmentRepository(db_session, tenant_a_id)
        target_date = appointment_tenant_a.start_datetime.date()

        schedule = repo_a.get_day_schedule(target_date)

        appointment_ids = [a.id for a in schedule]
        assert appointment_tenant_b.id not in appointment_ids

    def test_check_conflicts_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_tenant_a, appointment_tenant_b
    ):
        """La detection de conflits est isolee par tenant."""
        repo_a = AppointmentRepository(db_session, tenant_a_id)

        # Verifier les conflits pour le creneau du tenant B
        conflicts = repo_a.check_conflicts(
            start_datetime=appointment_tenant_b.start_datetime,
            end_datetime=appointment_tenant_b.end_datetime
        )

        # Ne devrait pas detecter le RDV du tenant B comme conflit
        conflict_ids = [c.id for c in conflicts]
        assert appointment_tenant_b.id not in conflict_ids


class TestAppointmentTypeTenantIsolation:
    """Tests d'isolation tenant pour les types de rendez-vous."""

    def test_cannot_access_other_tenant_type(
        self, db_session, tenant_a_id, tenant_b_id, appointment_type_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les types de tenant B."""
        repo_a = AppointmentTypeRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(appointment_type_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Acces cross-tenant detecte!"

    def test_cannot_list_other_tenant_types(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_type_tenant_a, appointment_type_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les types du tenant courant."""
        repo_a = AppointmentTypeRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        type_ids = [t.id for t in items]
        assert appointment_type_tenant_a.id in type_ids
        assert appointment_type_tenant_b.id not in type_ids

    def test_list_active_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_type_tenant_a, appointment_type_tenant_b
    ):
        """list_active ne retourne que les types du tenant courant."""
        repo_a = AppointmentTypeRepository(db_session, tenant_a_id)
        types = repo_a.list_active()

        type_ids = [t.id for t in types]
        assert appointment_type_tenant_a.id in type_ids
        assert appointment_type_tenant_b.id not in type_ids

    def test_autocomplete_types_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id,
        appointment_type_tenant_a, appointment_type_tenant_b
    ):
        """Autocomplete types ne retourne que ceux du tenant courant."""
        repo_a = AppointmentTypeRepository(db_session, tenant_a_id)
        results = repo_a.autocomplete("TYPE")

        result_ids = [r["id"] for r in results]
        assert str(appointment_type_tenant_a.id) in result_ids
        assert str(appointment_type_tenant_b.id) not in result_ids


class TestResourceTenantIsolation:
    """Tests d'isolation tenant pour les ressources."""

    def test_cannot_access_other_tenant_resource(
        self, db_session, tenant_a_id, tenant_b_id, resource_tenant_b
    ):
        """CRITIQUE: Tenant A ne peut pas voir les ressources de tenant B."""
        repo_a = ResourceRepository(db_session, tenant_a_id)
        result = repo_a.get_by_id(resource_tenant_b.id)
        assert result is None, "FAILLE SECURITE: Acces cross-tenant detecte!"

    def test_cannot_list_other_tenant_resources(
        self, db_session, tenant_a_id, tenant_b_id,
        resource_tenant_a, resource_tenant_b
    ):
        """CRITIQUE: Liste ne retourne que les ressources du tenant courant."""
        repo_a = ResourceRepository(db_session, tenant_a_id)
        items, total = repo_a.list()

        resource_ids = [r.id for r in items]
        assert resource_tenant_a.id in resource_ids
        assert resource_tenant_b.id not in resource_ids

    def test_list_available_tenant_isolated(
        self, db_session, tenant_a_id, tenant_b_id,
        resource_tenant_a, resource_tenant_b
    ):
        """list_available ne retourne que les ressources du tenant courant."""
        repo_a = ResourceRepository(db_session, tenant_a_id)
        resources = repo_a.list_available()

        resource_ids = [r.id for r in resources]
        assert resource_tenant_a.id in resource_ids
        assert resource_tenant_b.id not in resource_ids


class TestSoftDeleteIsolation:
    """Tests soft delete avec isolation tenant."""

    def test_soft_deleted_appointment_hidden_by_default(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """Rendez-vous soft-deleted n'apparait pas par defaut."""
        repo = AppointmentRepository(db_session, tenant_a_id)
        repo.soft_delete(appointment_tenant_a, user_id)

        result = repo.get_by_id(appointment_tenant_a.id)
        assert result is None

    def test_soft_deleted_visible_with_include_deleted(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """Rendez-vous soft-deleted visible avec include_deleted=True."""
        repo = AppointmentRepository(db_session, tenant_a_id)
        repo.soft_delete(appointment_tenant_a, user_id)

        repo_with_deleted = AppointmentRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_with_deleted.get_by_id(appointment_tenant_a.id)
        assert result is not None
        assert result.is_deleted is True

    def test_soft_deleted_other_tenant_still_hidden(
        self, db_session, tenant_a_id, tenant_b_id, user_id, appointment_tenant_b
    ):
        """Rendez-vous soft-deleted d'un autre tenant reste invisible."""
        repo_b = AppointmentRepository(db_session, tenant_b_id)
        repo_b.soft_delete(appointment_tenant_b, user_id)

        repo_a_with_deleted = AppointmentRepository(db_session, tenant_a_id, include_deleted=True)
        result = repo_a_with_deleted.get_by_id(appointment_tenant_b.id)
        assert result is None

    def test_soft_deleted_type_hidden_by_default(
        self, db_session, tenant_a_id, user_id, appointment_type_tenant_a
    ):
        """Type soft-deleted n'apparait pas par defaut."""
        repo = AppointmentTypeRepository(db_session, tenant_a_id)
        repo.soft_delete(appointment_type_tenant_a, user_id)

        result = repo.get_by_id(appointment_type_tenant_a.id)
        assert result is None

    def test_soft_deleted_resource_hidden_by_default(
        self, db_session, tenant_a_id, user_id, resource_tenant_a
    ):
        """Ressource soft-deleted n'apparait pas par defaut."""
        repo = ResourceRepository(db_session, tenant_a_id)
        repo.soft_delete(resource_tenant_a, user_id)

        result = repo.get_by_id(resource_tenant_a.id)
        assert result is None


class TestAppointmentWorkflow:
    """Tests du workflow de rendez-vous."""

    def test_confirm_changes_status(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """La confirmation change le statut."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        # Mettre en statut PENDING d'abord
        appointment_tenant_a.status = AppointmentStatus.PENDING
        db_session.commit()

        repo.confirm(appointment_tenant_a, user_id)

        assert appointment_tenant_a.status == AppointmentStatus.CONFIRMED
        assert appointment_tenant_a.confirmed_at is not None
        assert appointment_tenant_a.confirmed_by == user_id

    def test_cancel_changes_status(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """L'annulation change le statut."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        repo.cancel(appointment_tenant_a, user_id, "Raison du test")

        assert appointment_tenant_a.status == AppointmentStatus.CANCELLED
        assert appointment_tenant_a.cancelled_at is not None
        assert appointment_tenant_a.cancelled_by == user_id
        assert appointment_tenant_a.cancellation_reason == "Raison du test"

    def test_complete_changes_status(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """La completion change le statut."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        repo.complete(appointment_tenant_a, user_id, "Bien passe")

        assert appointment_tenant_a.status == AppointmentStatus.COMPLETED
        assert appointment_tenant_a.completed_at is not None
        assert appointment_tenant_a.completed_by == user_id
        assert appointment_tenant_a.outcome == "Bien passe"

    def test_reschedule_updates_dates(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """La replanification met a jour les dates."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        old_start = appointment_tenant_a.start_datetime
        new_start = old_start + timedelta(days=1)
        new_end = new_start + timedelta(hours=1)

        repo.reschedule(appointment_tenant_a, new_start, new_end, user_id)

        assert appointment_tenant_a.start_datetime == new_start
        assert appointment_tenant_a.end_datetime == new_end
        assert appointment_tenant_a.status == AppointmentStatus.RESCHEDULED
        assert appointment_tenant_a.reschedule_count == 1

    def test_check_in_changes_status(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """Le check-in change le statut."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        repo.check_in(appointment_tenant_a, user_id)

        assert appointment_tenant_a.status == AppointmentStatus.CHECKED_IN
        assert appointment_tenant_a.checked_in_at is not None

    def test_mark_no_show_changes_status(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """Le marquage absent change le statut."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        repo.mark_no_show(appointment_tenant_a, user_id)

        assert appointment_tenant_a.status == AppointmentStatus.NO_SHOW


class TestVersionOptimisticLocking:
    """Tests du verrouillage optimiste par version."""

    def test_version_increments_on_update(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """La version s'incremente a chaque mise a jour."""
        repo = AppointmentRepository(db_session, tenant_a_id)
        initial_version = appointment_tenant_a.version

        repo.update(appointment_tenant_a, {"title": "Nouveau titre"}, user_id)

        assert appointment_tenant_a.version == initial_version + 1

    def test_version_increments_on_confirm(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """La version s'incremente a la confirmation."""
        repo = AppointmentRepository(db_session, tenant_a_id)
        appointment_tenant_a.status = AppointmentStatus.PENDING
        db_session.commit()

        initial_version = appointment_tenant_a.version

        repo.confirm(appointment_tenant_a, user_id)

        assert appointment_tenant_a.version == initial_version + 1

    def test_version_increments_on_cancel(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """La version s'incremente a l'annulation."""
        repo = AppointmentRepository(db_session, tenant_a_id)
        initial_version = appointment_tenant_a.version

        repo.cancel(appointment_tenant_a, user_id)

        assert appointment_tenant_a.version == initial_version + 1


class TestAuditFields:
    """Tests des champs d'audit."""

    def test_created_fields_set_on_create(
        self, db_session, tenant_a_id, user_id, appointment_data
    ):
        """Les champs created_* sont definis a la creation."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        appointment = repo.create(appointment_data, user_id)

        assert appointment.created_at is not None
        assert appointment.created_by == user_id
        assert appointment.updated_at is not None

    def test_updated_fields_set_on_update(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """Les champs updated_* sont mis a jour a la modification."""
        repo = AppointmentRepository(db_session, tenant_a_id)
        old_updated_at = appointment_tenant_a.updated_at

        # Attendre un peu pour que le timestamp change
        import time
        time.sleep(0.1)

        repo.update(appointment_tenant_a, {"title": "Nouveau"}, user_id)

        assert appointment_tenant_a.updated_at > old_updated_at
        assert appointment_tenant_a.updated_by == user_id

    def test_deleted_fields_set_on_soft_delete(
        self, db_session, tenant_a_id, user_id, appointment_tenant_a
    ):
        """Les champs deleted_* sont definis au soft delete."""
        repo = AppointmentRepository(db_session, tenant_a_id)

        repo.soft_delete(appointment_tenant_a, user_id)

        assert appointment_tenant_a.is_deleted is True
        assert appointment_tenant_a.deleted_at is not None
        assert appointment_tenant_a.deleted_by == user_id
