"""
Tests pour Field Service Router v2 - CORE SaaS
===============================================

Tests des 53 endpoints migrés vers CORE SaaS v2.
Couvre toutes les catégories: Zones, Technicians, Vehicles, Templates,
Interventions, Time Entries, Routes, Expenses, Contracts, Stats.
"""

from datetime import date, datetime, time
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.field_service.models import (
    InterventionPriority,
    InterventionStatus,
    InterventionType,
    TechnicianStatus,
)
from app.modules.field_service.router_v2 import (
    approve_expense,
    arrive_on_site,
    assign_intervention,
    cancel_intervention,
    complete_intervention,
    create_contract,
    create_expense,
    create_intervention,
    create_route,
    create_technician,
    create_template,
    create_time_entry,
    create_vehicle,
    create_zone,
    delete_technician,
    delete_template,
    delete_vehicle,
    delete_zone,
    get_contract,
    get_dashboard,
    get_intervention,
    get_intervention_by_reference,
    get_intervention_history,
    get_intervention_stats,
    get_route,
    get_service,
    get_technician,
    get_technician_schedule,
    get_technician_stats,
    get_template,
    get_vehicle,
    get_zone,
    list_contracts,
    list_expenses,
    list_interventions,
    list_technicians,
    list_templates,
    list_time_entries,
    list_vehicles,
    list_zones,
    rate_intervention,
    reject_expense,
    start_intervention,
    start_travel,
    update_contract,
    update_intervention,
    update_route,
    update_technician,
    update_technician_location,
    update_technician_status,
    update_template,
    update_time_entry,
    update_vehicle,
    update_zone,
)


# =============================================================================
# TEST SERVICE FACTORY
# =============================================================================

@pytest.mark.asyncio
async def test_get_service_creates_service_with_context(test_client, mock_saas_context):
    """Test que get_service crée le service avec le contexte SaaS."""
    mock_db = Mock()

    with patch("app.modules.field_service.router_v2.FieldServiceService") as MockService:
        mock_service_instance = Mock()
        MockService.return_value = mock_service_instance

        service = get_service(db=mock_db, context=mock_saas_context)

        MockService.assert_called_once_with(
            mock_db,
            mock_saas_context.tenant_id,
            str(mock_saas_context.user_id),
        )
        assert service == mock_service_instance


# =============================================================================
# TESTS ZONES (5 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_zones_success(test_client, mock_field_service, mock_zone):
    """Test liste des zones avec succès."""
    mock_field_service.list_zones.return_value = [mock_zone]

    result = await list_zones(active_only=True, service=mock_field_service)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == mock_zone.id
    mock_field_service.list_zones.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_get_zone_success(test_client, mock_field_service, mock_zone):
    """Test récupération d'une zone avec succès."""
    mock_field_service.get_zone.return_value = mock_zone

    result = await get_zone(zone_id=1, service=mock_field_service)

    assert result.id == mock_zone.id
    mock_field_service.get_zone.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_zone_not_found(test_client):
    """Test récupération d'une zone inexistante."""
    mock_field_service.get_zone.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_zone(zone_id=999, service=mock_field_service)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_zone_success(test_client, mock_field_service, zone_create_data, mock_zone):
    """Test création d'une zone avec succès."""
    mock_field_service.create_zone.return_value = mock_zone

    from app.modules.field_service.schemas import ZoneCreate

    data = ZoneCreate(**zone_create_data)
    result = await create_zone(data=data, service=mock_field_service)

    assert result.id == mock_zone.id
    mock_field_service.create_zone.assert_called_once()


@pytest.mark.asyncio
async def test_update_zone_success(test_client, mock_field_service, zone_update_data, mock_zone):
    """Test mise à jour d'une zone avec succès."""
    updated_zone = mock_zone
    updated_zone.name = zone_update_data["name"]
    mock_field_service.update_zone.return_value = updated_zone

    from app.modules.field_service.schemas import ZoneUpdate

    data = ZoneUpdate(**zone_update_data)
    result = await update_zone(zone_id=1, data=data, service=mock_field_service)

    assert result.name == zone_update_data["name"]
    mock_field_service.update_zone.assert_called_once()


@pytest.mark.asyncio
async def test_delete_zone_success(test_client):
    """Test suppression d'une zone avec succès."""
    mock_field_service.delete_zone.return_value = True

    result = await delete_zone(zone_id=1, service=mock_field_service)

    assert result == {"status": "deleted"}
    mock_field_service.delete_zone.assert_called_once_with(1)


# =============================================================================
# TESTS TECHNICIANS (8 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_technicians_success(test_client, mock_field_service, mock_technician):
    """Test liste des techniciens avec succès."""
    mock_field_service.list_technicians.return_value = [mock_technician]

    result = await list_technicians(
        active_only=True,
        zone_id=None,
        status=None,
        available_only=False,
        service=mock_field_service,
    )

    assert isinstance(result, list)
    assert len(result) == 1
    mock_field_service.list_technicians.assert_called_once()


@pytest.mark.asyncio
async def test_list_technicians_filtered_by_zone(test_client, mock_field_service, mock_technician):
    """Test liste des techniciens filtrés par zone."""
    mock_field_service.list_technicians.return_value = [mock_technician]

    result = await list_technicians(
        active_only=True,
        zone_id=1,
        status=None,
        available_only=False,
        service=mock_field_service,
    )

    assert len(result) == 1
    mock_field_service.list_technicians.assert_called_once_with(True, 1, None, False)


@pytest.mark.asyncio
async def test_list_technicians_available_only(test_client, mock_field_service, mock_technician):
    """Test liste des techniciens disponibles uniquement."""
    mock_technician.status = TechnicianStatus.AVAILABLE
    mock_field_service.list_technicians.return_value = [mock_technician]

    result = await list_technicians(
        active_only=True,
        zone_id=None,
        status=TechnicianStatus.AVAILABLE,
        available_only=True,
        service=mock_field_service,
    )

    assert len(result) == 1
    assert result[0].status == TechnicianStatus.AVAILABLE


@pytest.mark.asyncio
async def test_get_technician_success(test_client, mock_field_service, mock_technician):
    """Test récupération d'un technicien avec succès."""
    mock_field_service.get_technician.return_value = mock_technician

    result = await get_technician(tech_id=1, service=mock_field_service)

    assert result.id == mock_technician.id
    mock_field_service.get_technician.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_create_technician_success(test_client, mock_field_service, technician_create_data, mock_technician):
    """Test création d'un technicien avec succès."""
    mock_field_service.create_technician.return_value = mock_technician

    from app.modules.field_service.schemas import TechnicianCreate

    data = TechnicianCreate(**technician_create_data)
    result = await create_technician(data=data, service=mock_field_service)

    assert result.id == mock_technician.id
    mock_field_service.create_technician.assert_called_once()


@pytest.mark.asyncio
async def test_update_technician_status_success(test_client, mock_field_service, mock_technician):
    """Test mise à jour du statut d'un technicien."""
    mock_technician.status = TechnicianStatus.ON_MISSION
    mock_field_service.update_technician_status.return_value = mock_technician

    from app.modules.field_service.schemas import TechnicianStatusUpdate

    data = TechnicianStatusUpdate(
        status=TechnicianStatus.ON_MISSION,
        latitude=Decimal("48.8566"),
        longitude=Decimal("2.3522"),
    )
    result = await update_technician_status(tech_id=1, data=data, service=mock_field_service)

    assert result.status == TechnicianStatus.ON_MISSION
    mock_field_service.update_technician_status.assert_called_once()


@pytest.mark.asyncio
async def test_update_technician_location_success(test_client, mock_field_service, mock_technician):
    """Test mise à jour de la position GPS d'un technicien."""
    mock_technician.last_location_lat = Decimal("48.8566")
    mock_technician.last_location_lng = Decimal("2.3522")
    mock_field_service.update_technician_location.return_value = mock_technician

    from app.modules.field_service.schemas import TechnicianLocation

    data = TechnicianLocation(latitude=Decimal("48.8566"), longitude=Decimal("2.3522"))
    result = await update_technician_location(tech_id=1, data=data, service=mock_field_service)

    assert result.last_location_lat == Decimal("48.8566")
    mock_field_service.update_technician_location.assert_called_once()


@pytest.mark.asyncio
async def test_delete_technician_success(test_client):
    """Test suppression d'un technicien avec succès."""
    mock_field_service.delete_technician.return_value = True

    result = await delete_technician(tech_id=1, service=mock_field_service)

    assert result == {"status": "deleted"}
    mock_field_service.delete_technician.assert_called_once_with(1)


# =============================================================================
# TESTS SCHEDULES (1 endpoint)
# =============================================================================

@pytest.mark.asyncio
async def test_get_technician_schedule_success(test_client, mock_field_service, mock_intervention):
    """Test récupération du planning d'un technicien."""
    mock_field_service.get_technician_schedule.return_value = [mock_intervention]

    date_from = date.today()
    date_to = date(2026, 2, 1)

    result = await get_technician_schedule(
        tech_id=1, date_from=date_from, date_to=date_to, service=mock_field_service
    )

    assert isinstance(result, list)
    assert len(result) == 1
    mock_field_service.get_technician_schedule.assert_called_once_with(1, date_from, date_to)


# =============================================================================
# TESTS VEHICLES (5 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_vehicles_success(test_client, mock_field_service, mock_vehicle):
    """Test liste des véhicules avec succès."""
    mock_field_service.list_vehicles.return_value = [mock_vehicle]

    result = await list_vehicles(active_only=True, service=mock_field_service)

    assert isinstance(result, list)
    assert len(result) == 1
    mock_field_service.list_vehicles.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_get_vehicle_success(test_client, mock_field_service, mock_vehicle):
    """Test récupération d'un véhicule avec succès."""
    mock_field_service.get_vehicle.return_value = mock_vehicle

    result = await get_vehicle(vehicle_id=1, service=mock_field_service)

    assert result.id == mock_vehicle.id
    mock_field_service.get_vehicle.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_create_vehicle_success(test_client, mock_field_service, vehicle_create_data, mock_vehicle):
    """Test création d'un véhicule avec succès."""
    mock_field_service.create_vehicle.return_value = mock_vehicle

    from app.modules.field_service.schemas import VehicleCreate

    data = VehicleCreate(**vehicle_create_data)
    result = await create_vehicle(data=data, service=mock_field_service)

    assert result.id == mock_vehicle.id
    mock_field_service.create_vehicle.assert_called_once()


@pytest.mark.asyncio
async def test_update_vehicle_success(test_client, mock_field_service, mock_vehicle):
    """Test mise à jour d'un véhicule avec succès."""
    mock_vehicle.mileage = 20000
    mock_field_service.update_vehicle.return_value = mock_vehicle

    from app.modules.field_service.schemas import VehicleUpdate

    data = VehicleUpdate(mileage=20000)
    result = await update_vehicle(vehicle_id=1, data=data, service=mock_field_service)

    assert result.mileage == 20000
    mock_field_service.update_vehicle.assert_called_once()


@pytest.mark.asyncio
async def test_delete_vehicle_success(test_client):
    """Test suppression d'un véhicule avec succès."""
    mock_field_service.delete_vehicle.return_value = True

    result = await delete_vehicle(vehicle_id=1, service=mock_field_service)

    assert result == {"status": "deleted"}
    mock_field_service.delete_vehicle.assert_called_once_with(1)


# =============================================================================
# TESTS TEMPLATES (5 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_templates_success(test_client, mock_field_service, mock_template):
    """Test liste des templates avec succès."""
    mock_field_service.list_templates.return_value = [mock_template]

    result = await list_templates(active_only=True, service=mock_field_service)

    assert isinstance(result, list)
    assert len(result) == 1
    mock_field_service.list_templates.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_get_template_success(test_client, mock_field_service, mock_template):
    """Test récupération d'un template avec succès."""
    mock_field_service.get_template.return_value = mock_template

    result = await get_template(template_id=1, service=mock_field_service)

    assert result.id == mock_template.id
    mock_field_service.get_template.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_create_template_success(test_client, mock_field_service, template_create_data, mock_template):
    """Test création d'un template avec succès."""
    mock_field_service.create_template.return_value = mock_template

    from app.modules.field_service.schemas import TemplateCreate

    data = TemplateCreate(**template_create_data)
    result = await create_template(data=data, service=mock_field_service)

    assert result.id == mock_template.id
    mock_field_service.create_template.assert_called_once()


@pytest.mark.asyncio
async def test_update_template_success(test_client, mock_field_service, mock_template):
    """Test mise à jour d'un template avec succès."""
    mock_template.estimated_duration = 180
    mock_field_service.update_template.return_value = mock_template

    from app.modules.field_service.schemas import TemplateUpdate

    data = TemplateUpdate(estimated_duration=180)
    result = await update_template(template_id=1, data=data, service=mock_field_service)

    assert result.estimated_duration == 180
    mock_field_service.update_template.assert_called_once()


@pytest.mark.asyncio
async def test_delete_template_success(test_client):
    """Test suppression d'un template avec succès."""
    mock_field_service.delete_template.return_value = True

    result = await delete_template(template_id=1, service=mock_field_service)

    assert result == {"status": "deleted"}
    mock_field_service.delete_template.assert_called_once_with(1)


# =============================================================================
# TESTS INTERVENTIONS (15 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_interventions_success(test_client, mock_field_service, mock_intervention):
    """Test liste des interventions avec succès."""
    mock_field_service.list_interventions.return_value = ([mock_intervention], 1)

    result = await list_interventions(
        status=None,
        priority=None,
        intervention_type=None,
        technician_id=None,
        zone_id=None,
        customer_id=None,
        scheduled_date=None,
        date_from=None,
        date_to=None,
        search=None,
        skip=0,
        limit=50,
        service=mock_field_service,
    )

    assert "items" in result
    assert "total" in result
    assert result["total"] == 1
    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_list_interventions_with_filters(test_client, mock_field_service, mock_intervention):
    """Test liste des interventions avec filtres."""
    mock_field_service.list_interventions.return_value = ([mock_intervention], 1)

    result = await list_interventions(
        status=InterventionStatus.SCHEDULED,
        priority=InterventionPriority.HIGH,
        intervention_type=InterventionType.CORRECTIVE,
        technician_id=None,
        zone_id=1,
        customer_id=501,
        scheduled_date=date.today(),
        date_from=None,
        date_to=None,
        search="fuite",
        skip=0,
        limit=50,
        service=mock_field_service,
    )

    assert result["total"] == 1
    mock_field_service.list_interventions.assert_called_once()


@pytest.mark.asyncio
async def test_get_intervention_success(test_client, mock_field_service, mock_intervention):
    """Test récupération d'une intervention avec succès."""
    mock_field_service.get_intervention.return_value = mock_intervention

    result = await get_intervention(intervention_id=1, service=mock_field_service)

    assert result.id == mock_intervention.id
    mock_field_service.get_intervention.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_intervention_by_reference_success(test_client, mock_field_service, mock_intervention):
    """Test récupération d'une intervention par référence."""
    mock_field_service.get_intervention_by_reference.return_value = mock_intervention

    result = await get_intervention_by_reference(
        reference="INT-202601-ABC123", service=mock_field_service
    )

    assert result.reference == mock_intervention.reference
    mock_field_service.get_intervention_by_reference.assert_called_once()


@pytest.mark.asyncio
async def test_create_intervention_success(test_client, mock_field_service, intervention_create_data, mock_intervention):
    """Test création d'une intervention avec succès."""
    mock_field_service.create_intervention.return_value = mock_intervention

    from app.modules.field_service.schemas import InterventionCreate

    data = InterventionCreate(**intervention_create_data)
    result = await create_intervention(data=data, service=mock_field_service)

    assert result.id == mock_intervention.id
    mock_field_service.create_intervention.assert_called_once()


@pytest.mark.asyncio
async def test_update_intervention_success(test_client, mock_field_service, intervention_update_data, mock_intervention):
    """Test mise à jour d'une intervention avec succès."""
    mock_intervention.priority = InterventionPriority.URGENT
    mock_field_service.update_intervention.return_value = mock_intervention

    from app.modules.field_service.schemas import InterventionUpdate

    data = InterventionUpdate(**intervention_update_data)
    result = await update_intervention(intervention_id=1, data=data, service=mock_field_service)

    assert result.priority == InterventionPriority.URGENT
    mock_field_service.update_intervention.assert_called_once()


@pytest.mark.asyncio
async def test_assign_intervention_success(test_client, mock_field_service, mock_assigned_intervention):
    """Test assignation d'une intervention à un technicien."""
    mock_field_service.assign_intervention.return_value = mock_assigned_intervention

    from app.modules.field_service.schemas import InterventionAssign

    data = InterventionAssign(
        technician_id=1,
        scheduled_date=date.today(),
        scheduled_time_start=time(9, 0),
        scheduled_time_end=time(11, 0),
    )
    result = await assign_intervention(intervention_id=1, data=data, service=mock_field_service)

    assert result.status == InterventionStatus.ASSIGNED
    assert result.technician_id == 1
    mock_field_service.assign_intervention.assert_called_once()


@pytest.mark.asyncio
async def test_start_travel_success(test_client, mock_field_service, mock_assigned_intervention):
    """Test démarrage du trajet vers l'intervention."""
    mock_assigned_intervention.status = InterventionStatus.EN_ROUTE
    mock_field_service.start_travel.return_value = mock_assigned_intervention

    from app.modules.field_service.schemas import InterventionStart

    data = InterventionStart(latitude=Decimal("48.8566"), longitude=Decimal("2.3522"))
    result = await start_travel(
        intervention_id=1, tech_id=1, data=data, service=mock_field_service
    )

    assert result.status == InterventionStatus.EN_ROUTE
    mock_field_service.start_travel.assert_called_once()


@pytest.mark.asyncio
async def test_arrive_on_site_success(test_client, mock_field_service, mock_assigned_intervention):
    """Test arrivée sur site d'intervention."""
    mock_assigned_intervention.status = InterventionStatus.ON_SITE
    mock_field_service.arrive_on_site.return_value = mock_assigned_intervention

    from app.modules.field_service.schemas import InterventionStart

    data = InterventionStart(latitude=Decimal("48.8566"), longitude=Decimal("2.3522"))
    result = await arrive_on_site(
        intervention_id=1, tech_id=1, data=data, service=mock_field_service
    )

    assert result.status == InterventionStatus.ON_SITE
    mock_field_service.arrive_on_site.assert_called_once()


@pytest.mark.asyncio
async def test_start_intervention_success(test_client, mock_field_service, mock_assigned_intervention):
    """Test démarrage de l'intervention."""
    mock_assigned_intervention.status = InterventionStatus.IN_PROGRESS
    mock_field_service.start_intervention.return_value = mock_assigned_intervention

    from app.modules.field_service.schemas import InterventionStart

    data = InterventionStart(latitude=Decimal("48.8566"), longitude=Decimal("2.3522"))
    result = await start_intervention(
        intervention_id=1, tech_id=1, data=data, service=mock_field_service
    )

    assert result.status == InterventionStatus.IN_PROGRESS
    mock_field_service.start_intervention.assert_called_once()


@pytest.mark.asyncio
async def test_complete_intervention_success(test_client, mock_field_service, mock_completed_intervention):
    """Test complétion d'une intervention."""
    mock_field_service.complete_intervention.return_value = mock_completed_intervention

    from app.modules.field_service.schemas import InterventionComplete

    data = InterventionComplete(
        completion_notes="Intervention réussie",
        labor_hours=Decimal("2.0"),
        parts_used=[{"name": "Robinet", "quantity": 1, "unit_price": 50.0, "total_price": 50.0}],
        signature_name="Client Martin",
        signature_data="base64_signature_data",
    )
    result = await complete_intervention(
        intervention_id=1, tech_id=1, data=data, service=mock_field_service
    )

    assert result.status == InterventionStatus.COMPLETED
    assert result.total_cost == Decimal("160.00")
    mock_field_service.complete_intervention.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_intervention_success(test_client, mock_field_service, mock_intervention):
    """Test annulation d'une intervention."""
    mock_intervention.status = InterventionStatus.CANCELLED
    mock_field_service.cancel_intervention.return_value = mock_intervention

    result = await cancel_intervention(
        intervention_id=1, reason="Client annulation", service=mock_field_service
    )

    assert result.status == InterventionStatus.CANCELLED
    mock_field_service.cancel_intervention.assert_called_once_with(1, "Client annulation")


@pytest.mark.asyncio
async def test_rate_intervention_success(test_client, mock_field_service, mock_completed_intervention):
    """Test notation d'une intervention."""
    mock_completed_intervention.customer_rating = 5
    mock_field_service.rate_intervention.return_value = mock_completed_intervention

    result = await rate_intervention(
        intervention_id=1,
        rating=5,
        feedback="Excellent service",
        service=mock_field_service,
    )

    assert result.customer_rating == 5
    mock_field_service.rate_intervention.assert_called_once_with(1, 5, "Excellent service")


@pytest.mark.asyncio
async def test_get_intervention_history_success(test_client):
    """Test récupération de l'historique d'une intervention."""
    mock_history = [
        Mock(action="created", created_at=datetime.utcnow()),
        Mock(action="assigned", created_at=datetime.utcnow()),
        Mock(action="completed", created_at=datetime.utcnow()),
    ]
    mock_field_service.get_intervention_history.return_value = mock_history

    result = await get_intervention_history(intervention_id=1, service=mock_field_service)

    assert isinstance(result, list)
    assert len(result) == 3
    mock_field_service.get_intervention_history.assert_called_once_with(1)


# =============================================================================
# TESTS TIME ENTRIES (3 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_time_entries_success(test_client, mock_field_service, mock_time_entry):
    """Test liste des entrées de temps avec succès."""
    mock_field_service.list_time_entries.return_value = [mock_time_entry]

    result = await list_time_entries(
        technician_id=None,
        intervention_id=None,
        date_from=None,
        date_to=None,
        entry_type=None,
        service=mock_field_service,
    )

    assert isinstance(result, list)
    assert len(result) == 1
    mock_field_service.list_time_entries.assert_called_once()


@pytest.mark.asyncio
async def test_create_time_entry_success(test_client, mock_field_service, time_entry_create_data, mock_time_entry):
    """Test création d'une entrée de temps avec succès."""
    mock_field_service.create_time_entry.return_value = mock_time_entry

    from app.modules.field_service.schemas import TimeEntryCreate

    data = TimeEntryCreate(**time_entry_create_data)
    result = await create_time_entry(data=data, service=mock_field_service)

    assert result.id == mock_time_entry.id
    mock_field_service.create_time_entry.assert_called_once()


@pytest.mark.asyncio
async def test_update_time_entry_success(test_client, mock_field_service, mock_time_entry):
    """Test mise à jour d'une entrée de temps avec succès."""
    mock_time_entry.end_time = datetime.utcnow()
    mock_time_entry.duration_minutes = 120
    mock_field_service.update_time_entry.return_value = mock_time_entry

    from app.modules.field_service.schemas import TimeEntryUpdate

    data = TimeEntryUpdate(end_time=datetime.utcnow())
    result = await update_time_entry(entry_id=1, data=data, service=mock_field_service)

    assert result.end_time is not None
    mock_field_service.update_time_entry.assert_called_once()


# =============================================================================
# TESTS ROUTES (3 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_get_route_success(test_client, mock_field_service, mock_route):
    """Test récupération d'une tournée avec succès."""
    mock_field_service.get_route.return_value = mock_route

    result = await get_route(tech_id=1, route_date=date.today(), service=mock_field_service)

    assert result.id == mock_route.id
    mock_field_service.get_route.assert_called_once_with(1, date.today())


@pytest.mark.asyncio
async def test_create_route_success(test_client, mock_field_service, route_create_data, mock_route):
    """Test création d'une tournée avec succès."""
    mock_field_service.create_route.return_value = mock_route

    from app.modules.field_service.schemas import RouteCreate

    data = RouteCreate(**route_create_data)
    result = await create_route(data=data, service=mock_field_service)

    assert result.id == mock_route.id
    mock_field_service.create_route.assert_called_once()


@pytest.mark.asyncio
async def test_update_route_success(test_client, mock_field_service, mock_route):
    """Test mise à jour d'une tournée avec succès."""
    mock_route.actual_distance_km = Decimal("50.0")
    mock_field_service.update_route.return_value = mock_route

    from app.modules.field_service.schemas import RouteUpdate

    data = RouteUpdate(actual_distance_km=Decimal("50.0"))
    result = await update_route(route_id=1, data=data, service=mock_field_service)

    assert result.actual_distance_km == Decimal("50.0")
    mock_field_service.update_route.assert_called_once()


# =============================================================================
# TESTS EXPENSES (4 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_expenses_success(test_client, mock_field_service, mock_expense):
    """Test liste des frais avec succès."""
    mock_field_service.list_expenses.return_value = [mock_expense]

    result = await list_expenses(
        technician_id=None,
        status=None,
        date_from=None,
        date_to=None,
        service=mock_field_service,
    )

    assert isinstance(result, list)
    assert len(result) == 1
    mock_field_service.list_expenses.assert_called_once()


@pytest.mark.asyncio
async def test_create_expense_success(test_client, mock_field_service, expense_create_data, mock_expense):
    """Test création d'un frais avec succès."""
    mock_field_service.create_expense.return_value = mock_expense

    from app.modules.field_service.schemas import ExpenseCreate

    data = ExpenseCreate(**expense_create_data)
    result = await create_expense(data=data, service=mock_field_service)

    assert result.id == mock_expense.id
    mock_field_service.create_expense.assert_called_once()


@pytest.mark.asyncio
async def test_approve_expense_success(test_client, mock_field_service, mock_expense):
    """Test approbation d'un frais avec succès."""
    mock_expense.status = "approved"
    mock_field_service.approve_expense.return_value = mock_expense

    result = await approve_expense(expense_id=1, approved_by=100, service=mock_field_service)

    assert result.status == "approved"
    mock_field_service.approve_expense.assert_called_once_with(1, 100)


@pytest.mark.asyncio
async def test_reject_expense_success(test_client, mock_field_service, mock_expense):
    """Test rejet d'un frais avec succès."""
    mock_expense.status = "rejected"
    mock_field_service.reject_expense.return_value = mock_expense

    result = await reject_expense(
        expense_id=1, reason="Justificatif manquant", service=mock_field_service
    )

    assert result.status == "rejected"
    mock_field_service.reject_expense.assert_called_once_with(1, "Justificatif manquant")


# =============================================================================
# TESTS CONTRACTS (4 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_list_contracts_success(test_client, mock_field_service, mock_contract):
    """Test liste des contrats avec succès."""
    mock_field_service.list_contracts.return_value = [mock_contract]

    result = await list_contracts(
        customer_id=None, status=None, service=mock_field_service
    )

    assert isinstance(result, list)
    assert len(result) == 1
    mock_field_service.list_contracts.assert_called_once()


@pytest.mark.asyncio
async def test_get_contract_success(test_client, mock_field_service, mock_contract):
    """Test récupération d'un contrat avec succès."""
    mock_field_service.get_contract.return_value = mock_contract

    result = await get_contract(contract_id=1, service=mock_field_service)

    assert result.id == mock_contract.id
    mock_field_service.get_contract.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_create_contract_success(test_client, mock_field_service, contract_create_data, mock_contract):
    """Test création d'un contrat avec succès."""
    mock_field_service.create_contract.return_value = mock_contract

    from app.modules.field_service.schemas import ContractCreate

    data = ContractCreate(**contract_create_data)
    result = await create_contract(data=data, service=mock_field_service)

    assert result.id == mock_contract.id
    mock_field_service.create_contract.assert_called_once()


@pytest.mark.asyncio
async def test_update_contract_success(test_client, mock_field_service, mock_contract):
    """Test mise à jour d'un contrat avec succès."""
    mock_contract.status = "suspended"
    mock_field_service.update_contract.return_value = mock_contract

    from app.modules.field_service.schemas import ContractUpdate

    data = ContractUpdate(status="suspended")
    result = await update_contract(contract_id=1, data=data, service=mock_field_service)

    assert result.status == "suspended"
    mock_field_service.update_contract.assert_called_once()


# =============================================================================
# TESTS STATS & DASHBOARD (3 endpoints)
# =============================================================================

@pytest.mark.asyncio
async def test_get_intervention_stats_success(test_client, mock_field_service, mock_intervention_stats):
    """Test récupération des statistiques d'interventions."""
    mock_field_service.get_intervention_stats.return_value = mock_intervention_stats

    result = await get_intervention_stats(days=30, service=mock_field_service)

    assert result["total"] == 150
    assert result["completed"] == 100
    mock_field_service.get_intervention_stats.assert_called_once_with(30)


@pytest.mark.asyncio
async def test_get_technician_stats_success(test_client, mock_field_service, mock_technician_stats):
    """Test récupération des statistiques par technicien."""
    mock_field_service.get_technician_stats.return_value = mock_technician_stats

    result = await get_technician_stats(days=30, service=mock_field_service)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["technician_name"] == "Jean Dupont"
    mock_field_service.get_technician_stats.assert_called_once_with(30)


@pytest.mark.asyncio
async def test_get_dashboard_success(test_client, mock_field_service, mock_dashboard):
    """Test récupération du dashboard complet."""
    mock_field_service.get_dashboard.return_value = mock_dashboard

    result = await get_dashboard(days=30, service=mock_field_service)

    assert "intervention_stats" in result
    assert "technician_stats" in result
    assert result["today_interventions"] == 8
    assert result["active_technicians"] == 5
    mock_field_service.get_dashboard.assert_called_once_with(30)


# =============================================================================
# TESTS WORKFLOW COMPLETS (2 tests)
# =============================================================================

@pytest.mark.asyncio
async def test_complete_work_order_lifecycle(test_client, mock_field_service,
    intervention_create_data,
    mock_intervention,
    mock_assigned_intervention,
    mock_completed_intervention,):
    """Test du cycle de vie complet d'une intervention."""
    # 1. Création
    mock_field_service.create_intervention.return_value = mock_intervention
    from app.modules.field_service.schemas import InterventionCreate

    create_data = InterventionCreate(**intervention_create_data)
    intervention = await create_intervention(data=create_data, service=mock_field_service)
    assert intervention.status == InterventionStatus.SCHEDULED

    # 2. Assignation
    mock_field_service.assign_intervention.return_value = mock_assigned_intervention
    from app.modules.field_service.schemas import InterventionAssign

    assign_data = InterventionAssign(
        technician_id=1,
        scheduled_date=date.today(),
        scheduled_time_start=time(9, 0),
    )
    intervention = await assign_intervention(
        intervention_id=1, data=assign_data, service=mock_field_service
    )
    assert intervention.status == InterventionStatus.ASSIGNED

    # 3. Démarrage trajet
    mock_assigned_intervention.status = InterventionStatus.EN_ROUTE
    mock_field_service.start_travel.return_value = mock_assigned_intervention
    intervention = await start_travel(intervention_id=1, tech_id=1, data=None, service=mock_field_service)
    assert intervention.status == InterventionStatus.EN_ROUTE

    # 4. Arrivée sur site
    mock_assigned_intervention.status = InterventionStatus.ON_SITE
    mock_field_service.arrive_on_site.return_value = mock_assigned_intervention
    intervention = await arrive_on_site(intervention_id=1, tech_id=1, data=None, service=mock_field_service)
    assert intervention.status == InterventionStatus.ON_SITE

    # 5. Démarrage intervention
    mock_assigned_intervention.status = InterventionStatus.IN_PROGRESS
    mock_field_service.start_intervention.return_value = mock_assigned_intervention
    intervention = await start_intervention(intervention_id=1, tech_id=1, data=None, service=mock_field_service)
    assert intervention.status == InterventionStatus.IN_PROGRESS

    # 6. Complétion
    mock_field_service.complete_intervention.return_value = mock_completed_intervention
    from app.modules.field_service.schemas import InterventionComplete

    complete_data = InterventionComplete(
        completion_notes="Terminé",
        labor_hours=Decimal("2.0"),
        signature_name="Client",
    )
    intervention = await complete_intervention(
        intervention_id=1, tech_id=1, data=complete_data, service=mock_field_service
    )
    assert intervention.status == InterventionStatus.COMPLETED
    assert intervention.total_cost == Decimal("160.00")


@pytest.mark.asyncio
async def test_route_optimization_workflow(test_client, mock_field_service, route_create_data, mock_route, mock_intervention):
    """Test du workflow d'optimisation de tournée."""
    # 1. Créer des interventions
    mock_field_service.create_intervention.return_value = mock_intervention

    # 2. Créer une tournée optimisée
    mock_field_service.create_route.return_value = mock_route
    from app.modules.field_service.schemas import RouteCreate

    data = RouteCreate(**route_create_data)
    route = await create_route(data=data, service=mock_field_service)

    assert route.technician_id == 1
    assert route.total_distance_km == Decimal("45.5")
    assert len(route.intervention_ids) == 3
    assert route.optimized_order == [1, 3, 2]

    # 3. Mettre à jour avec les données réelles
    mock_route.actual_distance_km = Decimal("48.0")
    mock_route.actual_duration = 380
    mock_field_service.update_route.return_value = mock_route

    from app.modules.field_service.schemas import RouteUpdate

    update_data = RouteUpdate(actual_distance_km=Decimal("48.0"), actual_duration=380)
    updated_route = await update_route(route_id=1, data=update_data, service=mock_field_service)

    assert updated_route.actual_distance_km == Decimal("48.0")
    assert updated_route.actual_duration == 380


# =============================================================================
# TESTS EDGE CASES & ERROR HANDLING
# =============================================================================

@pytest.mark.asyncio
async def test_intervention_not_found_error(test_client):
    """Test erreur intervention non trouvée."""
    mock_field_service.get_intervention.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_intervention(intervention_id=999, service=mock_field_service)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_technician_not_found_error(test_client):
    """Test erreur technicien non trouvé."""
    mock_field_service.get_technician.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_technician(tech_id=999, service=mock_field_service)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_assign_intervention_technician_not_found(test_client):
    """Test erreur assignation avec technicien inexistant."""
    mock_field_service.assign_intervention.return_value = None

    from app.modules.field_service.schemas import InterventionAssign

    data = InterventionAssign(technician_id=999, scheduled_date=date.today())

    with pytest.raises(HTTPException) as exc_info:
        await assign_intervention(intervention_id=1, data=data, service=mock_field_service)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_time_entry_not_found(test_client):
    """Test erreur mise à jour entrée de temps inexistante."""
    mock_field_service.update_time_entry.return_value = None

    from app.modules.field_service.schemas import TimeEntryUpdate

    data = TimeEntryUpdate(notes="Updated")

    with pytest.raises(HTTPException) as exc_info:
        await update_time_entry(entry_id=999, data=data, service=mock_field_service)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_interventions_pagination(test_client, mock_field_service, mock_intervention):
    """Test pagination de la liste des interventions."""
    interventions = [mock_intervention] * 100
    mock_field_service.list_interventions.return_value = (interventions[:50], 100)

    result = await list_interventions(
        status=None,
        priority=None,
        intervention_type=None,
        technician_id=None,
        zone_id=None,
        customer_id=None,
        scheduled_date=None,
        date_from=None,
        date_to=None,
        search=None,
        skip=0,
        limit=50,
        service=mock_field_service,
    )

    assert result["total"] == 100
    assert len(result["items"]) == 50
    assert result["skip"] == 0
    assert result["limit"] == 50
