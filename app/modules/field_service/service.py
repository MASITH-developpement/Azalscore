"""
AZALS MODULE 17 - Field Service Service
========================================
Logique métier pour la gestion des interventions terrain.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import uuid

from .models import (
    ServiceZone, Technician, Vehicle, InterventionTemplate,
    Intervention, InterventionHistory, TimeEntry, Route, Expense, ServiceContract,
    TechnicianStatus, InterventionStatus, InterventionPriority, InterventionType
)
from .schemas import (
    ZoneCreate, ZoneUpdate,
    TechnicianCreate, TechnicianUpdate, VehicleCreate, VehicleUpdate,
    TemplateCreate, TemplateUpdate,
    InterventionCreate, InterventionUpdate, InterventionAssign,
    InterventionComplete,
    TimeEntryCreate, TimeEntryUpdate,
    RouteCreate, RouteUpdate,
    ExpenseCreate, ContractCreate, ContractUpdate,
    TechnicianStats, InterventionStats, FieldServiceDashboard
)


class FieldServiceService:
    """Service Field Service."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # ZONES
    # ========================================================================

    def list_zones(self, active_only: bool = True) -> List[ServiceZone]:
        """Liste des zones."""
        query = self.db.query(ServiceZone).filter(
            ServiceZone.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(ServiceZone.is_active == True)
        return query.all()

    def get_zone(self, zone_id: int) -> Optional[ServiceZone]:
        """Récupère une zone."""
        return self.db.query(ServiceZone).filter(
            ServiceZone.id == zone_id,
            ServiceZone.tenant_id == self.tenant_id
        ).first()

    def create_zone(self, data: ZoneCreate) -> ServiceZone:
        """Crée une zone."""
        zone = ServiceZone(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)
        return zone

    def update_zone(self, zone_id: int, data: ZoneUpdate) -> Optional[ServiceZone]:
        """Met à jour une zone."""
        zone = self.get_zone(zone_id)
        if not zone:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(zone, key, value)
        self.db.commit()
        self.db.refresh(zone)
        return zone

    def delete_zone(self, zone_id: int) -> bool:
        """Supprime une zone."""
        zone = self.get_zone(zone_id)
        if not zone:
            return False
        zone.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # TECHNICIANS
    # ========================================================================

    def list_technicians(
        self,
        active_only: bool = True,
        zone_id: Optional[int] = None,
        status: Optional[TechnicianStatus] = None,
        available_only: bool = False
    ) -> List[Technician]:
        """Liste des techniciens."""
        query = self.db.query(Technician).filter(
            Technician.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(Technician.is_active == True)
        if zone_id:
            query = query.filter(Technician.zone_id == zone_id)
        if status:
            query = query.filter(Technician.status == status)
        if available_only:
            query = query.filter(Technician.status == TechnicianStatus.AVAILABLE)
        return query.all()

    def get_technician(self, tech_id: int) -> Optional[Technician]:
        """Récupère un technicien."""
        return self.db.query(Technician).filter(
            Technician.id == tech_id,
            Technician.tenant_id == self.tenant_id
        ).first()

    def get_technician_by_user(self, user_id: int) -> Optional[Technician]:
        """Récupère technicien par user_id."""
        return self.db.query(Technician).filter(
            Technician.user_id == user_id,
            Technician.tenant_id == self.tenant_id
        ).first()

    def create_technician(self, data: TechnicianCreate) -> Technician:
        """Crée un technicien."""
        technician = Technician(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(technician)
        self.db.commit()
        self.db.refresh(technician)
        return technician

    def update_technician(self, tech_id: int, data: TechnicianUpdate) -> Optional[Technician]:
        """Met à jour un technicien."""
        tech = self.get_technician(tech_id)
        if not tech:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(tech, key, value)
        self.db.commit()
        self.db.refresh(tech)
        return tech

    def update_technician_status(
        self,
        tech_id: int,
        status: TechnicianStatus,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None
    ) -> Optional[Technician]:
        """Met à jour le statut d'un technicien."""
        tech = self.get_technician(tech_id)
        if not tech:
            return None
        tech.status = status
        if latitude and longitude:
            tech.last_location_lat = latitude
            tech.last_location_lng = longitude
            tech.last_location_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(tech)
        return tech

    def update_technician_location(
        self,
        tech_id: int,
        latitude: Decimal,
        longitude: Decimal
    ) -> Optional[Technician]:
        """Met à jour la position d'un technicien."""
        tech = self.get_technician(tech_id)
        if not tech:
            return None
        tech.last_location_lat = latitude
        tech.last_location_lng = longitude
        tech.last_location_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(tech)
        return tech

    def delete_technician(self, tech_id: int) -> bool:
        """Supprime un technicien."""
        tech = self.get_technician(tech_id)
        if not tech:
            return False
        tech.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # VEHICLES
    # ========================================================================

    def list_vehicles(self, active_only: bool = True) -> List[Vehicle]:
        """Liste des véhicules."""
        query = self.db.query(Vehicle).filter(
            Vehicle.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(Vehicle.is_active == True)
        return query.all()

    def get_vehicle(self, vehicle_id: int) -> Optional[Vehicle]:
        """Récupère un véhicule."""
        return self.db.query(Vehicle).filter(
            Vehicle.id == vehicle_id,
            Vehicle.tenant_id == self.tenant_id
        ).first()

    def create_vehicle(self, data: VehicleCreate) -> Vehicle:
        """Crée un véhicule."""
        vehicle = Vehicle(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def update_vehicle(self, vehicle_id: int, data: VehicleUpdate) -> Optional[Vehicle]:
        """Met à jour un véhicule."""
        vehicle = self.get_vehicle(vehicle_id)
        if not vehicle:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(vehicle, key, value)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def delete_vehicle(self, vehicle_id: int) -> bool:
        """Supprime un véhicule."""
        vehicle = self.get_vehicle(vehicle_id)
        if not vehicle:
            return False
        vehicle.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def list_templates(self, active_only: bool = True) -> List[InterventionTemplate]:
        """Liste des templates."""
        query = self.db.query(InterventionTemplate).filter(
            InterventionTemplate.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(InterventionTemplate.is_active == True)
        return query.all()

    def get_template(self, template_id: int) -> Optional[InterventionTemplate]:
        """Récupère un template."""
        return self.db.query(InterventionTemplate).filter(
            InterventionTemplate.id == template_id,
            InterventionTemplate.tenant_id == self.tenant_id
        ).first()

    def create_template(self, data: TemplateCreate) -> InterventionTemplate:
        """Crée un template."""
        template = InterventionTemplate(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update_template(self, template_id: int, data: TemplateUpdate) -> Optional[InterventionTemplate]:
        """Met à jour un template."""
        template = self.get_template(template_id)
        if not template:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(template, key, value)
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template_id: int) -> bool:
        """Supprime un template."""
        template = self.get_template(template_id)
        if not template:
            return False
        template.is_active = False
        self.db.commit()
        return True

    # ========================================================================
    # INTERVENTIONS
    # ========================================================================

    def _generate_reference(self) -> str:
        """Génère une référence d'intervention unique."""
        prefix = datetime.utcnow().strftime("%Y%m")
        suffix = str(uuid.uuid4().hex[:6]).upper()
        return f"INT-{prefix}-{suffix}"

    def list_interventions(
        self,
        status: Optional[InterventionStatus] = None,
        priority: Optional[InterventionPriority] = None,
        intervention_type: Optional[InterventionType] = None,
        technician_id: Optional[int] = None,
        zone_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        scheduled_date: Optional[date] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Intervention], int]:
        """Liste des interventions avec filtres."""
        query = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(Intervention.status == status)
        if priority:
            query = query.filter(Intervention.priority == priority)
        if intervention_type:
            query = query.filter(Intervention.intervention_type == intervention_type)
        if technician_id:
            query = query.filter(Intervention.technician_id == technician_id)
        if zone_id:
            query = query.filter(Intervention.zone_id == zone_id)
        if customer_id:
            query = query.filter(Intervention.customer_id == customer_id)
        if scheduled_date:
            query = query.filter(Intervention.scheduled_date == scheduled_date)
        if date_from:
            query = query.filter(Intervention.scheduled_date >= date_from)
        if date_to:
            query = query.filter(Intervention.scheduled_date <= date_to)
        if search:
            query = query.filter(
                or_(
                    Intervention.title.ilike(f"%{search}%"),
                    Intervention.reference.ilike(f"%{search}%"),
                    Intervention.customer_name.ilike(f"%{search}%")
                )
            )

        total = query.count()
        interventions = query.order_by(
            Intervention.scheduled_date.desc(),
            Intervention.scheduled_time_start.asc()
        ).offset(skip).limit(limit).all()

        return interventions, total

    def get_intervention(self, intervention_id: int) -> Optional[Intervention]:
        """Récupère une intervention."""
        return self.db.query(Intervention).filter(
            Intervention.id == intervention_id,
            Intervention.tenant_id == self.tenant_id
        ).first()

    def get_intervention_by_reference(self, reference: str) -> Optional[Intervention]:
        """Récupère une intervention par référence."""
        return self.db.query(Intervention).filter(
            Intervention.reference == reference,
            Intervention.tenant_id == self.tenant_id
        ).first()

    def create_intervention(
        self,
        data: InterventionCreate,
        actor_id: Optional[int] = None,
        actor_name: Optional[str] = None
    ) -> Intervention:
        """Crée une intervention."""
        # Appliquer le template si fourni
        template_data = {}
        if data.template_id:
            template = self.get_template(data.template_id)
            if template:
                template_data = {
                    "intervention_type": template.intervention_type,
                    "estimated_duration": template.estimated_duration,
                    "priority": template.default_priority,
                    "checklist": template.checklist_template
                }

        intervention = Intervention(
            tenant_id=self.tenant_id,
            reference=self._generate_reference(),
            **template_data,
            **data.model_dump(exclude_unset=True)
        )

        # Déterminer le statut initial
        if intervention.technician_id and intervention.scheduled_date:
            intervention.status = InterventionStatus.ASSIGNED
        elif intervention.scheduled_date:
            intervention.status = InterventionStatus.SCHEDULED
        else:
            intervention.status = InterventionStatus.DRAFT

        self.db.add(intervention)
        self.db.flush()

        # Historique
        history = InterventionHistory(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            action="created",
            actor_type="dispatcher",
            actor_id=actor_id,
            actor_name=actor_name
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def update_intervention(
        self,
        intervention_id: int,
        data: InterventionUpdate,
        actor_id: Optional[int] = None,
        actor_name: Optional[str] = None
    ) -> Optional[Intervention]:
        """Met à jour une intervention."""
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            old_value = getattr(intervention, key)
            if old_value != value:
                setattr(intervention, key, value)

                # Historique
                history = InterventionHistory(
                    tenant_id=self.tenant_id,
                    intervention_id=intervention.id,
                    action="updated",
                    field_name=key,
                    old_value=str(old_value) if old_value else None,
                    new_value=str(value) if value else None,
                    actor_type="dispatcher",
                    actor_id=actor_id,
                    actor_name=actor_name
                )
                self.db.add(history)

        intervention.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def assign_intervention(
        self,
        intervention_id: int,
        data: InterventionAssign,
        actor_id: Optional[int] = None,
        actor_name: Optional[str] = None
    ) -> Optional[Intervention]:
        """Assigne une intervention à un technicien."""
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            return None

        tech = self.get_technician(data.technician_id)
        if not tech:
            return None

        old_tech_id = intervention.technician_id
        intervention.technician_id = data.technician_id

        if data.scheduled_date:
            intervention.scheduled_date = data.scheduled_date
        if data.scheduled_time_start:
            intervention.scheduled_time_start = data.scheduled_time_start
        if data.scheduled_time_end:
            intervention.scheduled_time_end = data.scheduled_time_end

        intervention.status = InterventionStatus.ASSIGNED
        intervention.updated_at = datetime.utcnow()

        # Historique
        history = InterventionHistory(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            action="assigned",
            field_name="technician_id",
            old_value=str(old_tech_id) if old_tech_id else None,
            new_value=str(data.technician_id),
            actor_type="dispatcher",
            actor_id=actor_id,
            actor_name=actor_name
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def start_travel(
        self,
        intervention_id: int,
        tech_id: int,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None
    ) -> Optional[Intervention]:
        """Démarre le trajet vers l'intervention."""
        intervention = self.get_intervention(intervention_id)
        if not intervention or intervention.technician_id != tech_id:
            return None

        intervention.status = InterventionStatus.EN_ROUTE
        intervention.updated_at = datetime.utcnow()

        # Mettre à jour le statut du technicien
        tech = self.get_technician(tech_id)
        if tech:
            tech.status = TechnicianStatus.TRAVELING

        # Créer une entrée de temps pour le trajet
        time_entry = TimeEntry(
            tenant_id=self.tenant_id,
            technician_id=tech_id,
            intervention_id=intervention_id,
            entry_type="travel",
            start_time=datetime.utcnow(),
            start_lat=latitude,
            start_lng=longitude
        )
        self.db.add(time_entry)

        # Historique
        history = InterventionHistory(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            action="started_travel",
            actor_type="technician",
            actor_id=tech_id,
            latitude=latitude,
            longitude=longitude
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def arrive_on_site(
        self,
        intervention_id: int,
        tech_id: int,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None
    ) -> Optional[Intervention]:
        """Arrive sur site."""
        intervention = self.get_intervention(intervention_id)
        if not intervention or intervention.technician_id != tech_id:
            return None

        intervention.status = InterventionStatus.ON_SITE
        intervention.arrival_time = datetime.utcnow()
        intervention.updated_at = datetime.utcnow()

        # Clôturer le trajet
        travel_entry = self.db.query(TimeEntry).filter(
            TimeEntry.intervention_id == intervention_id,
            TimeEntry.entry_type == "travel",
            TimeEntry.end_time == None
        ).first()
        if travel_entry:
            travel_entry.end_time = datetime.utcnow()
            travel_entry.end_lat = latitude
            travel_entry.end_lng = longitude
            travel_entry.duration_minutes = int(
                (travel_entry.end_time - travel_entry.start_time).total_seconds() / 60
            )

        # Historique
        history = InterventionHistory(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            action="arrived_on_site",
            actor_type="technician",
            actor_id=tech_id,
            latitude=latitude,
            longitude=longitude
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def start_intervention(
        self,
        intervention_id: int,
        tech_id: int,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None
    ) -> Optional[Intervention]:
        """Démarre l'intervention."""
        intervention = self.get_intervention(intervention_id)
        if not intervention or intervention.technician_id != tech_id:
            return None

        intervention.status = InterventionStatus.IN_PROGRESS
        intervention.actual_start = datetime.utcnow()
        intervention.updated_at = datetime.utcnow()

        # Mettre à jour le technicien
        tech = self.get_technician(tech_id)
        if tech:
            tech.status = TechnicianStatus.ON_MISSION

        # Créer une entrée de temps pour le travail
        time_entry = TimeEntry(
            tenant_id=self.tenant_id,
            technician_id=tech_id,
            intervention_id=intervention_id,
            entry_type="work",
            start_time=datetime.utcnow(),
            start_lat=latitude,
            start_lng=longitude
        )
        self.db.add(time_entry)

        # Historique
        history = InterventionHistory(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            action="started_work",
            actor_type="technician",
            actor_id=tech_id,
            latitude=latitude,
            longitude=longitude
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def complete_intervention(
        self,
        intervention_id: int,
        tech_id: int,
        data: InterventionComplete,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None
    ) -> Optional[Intervention]:
        """Complète l'intervention."""
        intervention = self.get_intervention(intervention_id)
        if not intervention or intervention.technician_id != tech_id:
            return None

        now = datetime.utcnow()

        intervention.status = InterventionStatus.COMPLETED
        intervention.actual_end = now
        intervention.departure_time = now
        intervention.updated_at = now

        if data.completion_notes:
            intervention.completion_notes = data.completion_notes
        if data.checklist:
            intervention.checklist = data.checklist
        if data.parts_used:
            intervention.parts_used = data.parts_used
        if data.labor_hours:
            intervention.labor_hours = data.labor_hours
        if data.signature_data:
            intervention.signature_data = data.signature_data
            intervention.signature_name = data.signature_name
            intervention.signed_at = now
        if data.photos:
            intervention.photos = data.photos

        # Calculer les coûts
        self._calculate_costs(intervention)

        # Clôturer l'entrée de temps travail
        work_entry = self.db.query(TimeEntry).filter(
            TimeEntry.intervention_id == intervention_id,
            TimeEntry.entry_type == "work",
            TimeEntry.end_time == None
        ).first()
        if work_entry:
            work_entry.end_time = now
            work_entry.end_lat = latitude
            work_entry.end_lng = longitude
            work_entry.duration_minutes = int(
                (work_entry.end_time - work_entry.start_time).total_seconds() / 60
            )

        # Mettre à jour le technicien
        tech = self.get_technician(tech_id)
        if tech:
            tech.status = TechnicianStatus.AVAILABLE
            tech.total_interventions += 1
            tech.completed_interventions += 1

        # Historique
        history = InterventionHistory(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            action="completed",
            actor_type="technician",
            actor_id=tech_id,
            latitude=latitude,
            longitude=longitude
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def cancel_intervention(
        self,
        intervention_id: int,
        reason: str,
        actor_id: Optional[int] = None,
        actor_name: Optional[str] = None
    ) -> Optional[Intervention]:
        """Annule une intervention."""
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            return None

        intervention.status = InterventionStatus.CANCELLED
        intervention.failure_reason = reason
        intervention.updated_at = datetime.utcnow()

        # Historique
        history = InterventionHistory(
            tenant_id=self.tenant_id,
            intervention_id=intervention.id,
            action="cancelled",
            new_value=reason,
            actor_type="dispatcher",
            actor_id=actor_id,
            actor_name=actor_name
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def _calculate_costs(self, intervention: Intervention):
        """Calcule les coûts de l'intervention."""
        # Coût main d'œuvre
        if intervention.labor_hours:
            hourly_rate = Decimal("50")  # Taux horaire par défaut
            intervention.labor_cost = intervention.labor_hours * hourly_rate
        else:
            # Calculer depuis les time entries
            work_entries = self.db.query(TimeEntry).filter(
                TimeEntry.intervention_id == intervention.id,
                TimeEntry.entry_type == "work"
            ).all()
            total_minutes = sum(e.duration_minutes or 0 for e in work_entries)
            intervention.labor_hours = Decimal(str(total_minutes / 60))
            intervention.labor_cost = intervention.labor_hours * Decimal("50")

        # Coût pièces
        if intervention.parts_used:
            intervention.parts_cost = sum(
                Decimal(str(p.get("total_price", 0))) for p in intervention.parts_used
            )
        else:
            intervention.parts_cost = Decimal("0")

        # Coût déplacement
        travel_entries = self.db.query(TimeEntry).filter(
            TimeEntry.intervention_id == intervention.id,
            TimeEntry.entry_type == "travel"
        ).all()
        total_km = sum(float(e.distance_km or 0) for e in travel_entries)
        intervention.travel_cost = Decimal(str(total_km * 0.5))  # 0.50€/km

        # Total
        intervention.total_cost = (
            intervention.labor_cost +
            intervention.parts_cost +
            intervention.travel_cost
        )

    def rate_intervention(
        self,
        intervention_id: int,
        rating: int,
        feedback: Optional[str] = None
    ) -> Optional[Intervention]:
        """Note une intervention (satisfaction client)."""
        intervention = self.get_intervention(intervention_id)
        if not intervention:
            return None

        intervention.customer_rating = rating
        intervention.customer_feedback = feedback

        # Mettre à jour la note moyenne du technicien
        if intervention.technician_id:
            tech = self.get_technician(intervention.technician_id)
            if tech:
                # Recalculer la moyenne
                rated = self.db.query(Intervention).filter(
                    Intervention.technician_id == tech.id,
                    Intervention.customer_rating != None
                ).all()
                if rated:
                    avg = sum(i.customer_rating for i in rated) / len(rated)
                    tech.avg_rating = Decimal(str(round(avg, 2)))

        self.db.commit()
        self.db.refresh(intervention)

        return intervention

    def get_intervention_history(self, intervention_id: int) -> List[InterventionHistory]:
        """Récupère l'historique d'une intervention."""
        return self.db.query(InterventionHistory).filter(
            InterventionHistory.intervention_id == intervention_id,
            InterventionHistory.tenant_id == self.tenant_id
        ).order_by(InterventionHistory.created_at.desc()).all()

    # ========================================================================
    # TIME ENTRIES
    # ========================================================================

    def list_time_entries(
        self,
        technician_id: Optional[int] = None,
        intervention_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        entry_type: Optional[str] = None
    ) -> List[TimeEntry]:
        """Liste les entrées de temps."""
        query = self.db.query(TimeEntry).filter(
            TimeEntry.tenant_id == self.tenant_id
        )
        if technician_id:
            query = query.filter(TimeEntry.technician_id == technician_id)
        if intervention_id:
            query = query.filter(TimeEntry.intervention_id == intervention_id)
        if date_from:
            query = query.filter(TimeEntry.start_time >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.filter(TimeEntry.start_time <= datetime.combine(date_to, datetime.max.time()))
        if entry_type:
            query = query.filter(TimeEntry.entry_type == entry_type)
        return query.order_by(TimeEntry.start_time.desc()).all()

    def create_time_entry(self, data: TimeEntryCreate) -> TimeEntry:
        """Crée une entrée de temps."""
        entry = TimeEntry(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update_time_entry(self, entry_id: int, data: TimeEntryUpdate) -> Optional[TimeEntry]:
        """Met à jour une entrée de temps."""
        entry = self.db.query(TimeEntry).filter(
            TimeEntry.id == entry_id,
            TimeEntry.tenant_id == self.tenant_id
        ).first()
        if not entry:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entry, key, value)

        # Recalculer la durée si end_time est défini
        if entry.end_time and entry.start_time:
            entry.duration_minutes = int(
                (entry.end_time - entry.start_time).total_seconds() / 60
            )

        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ========================================================================
    # ROUTES
    # ========================================================================

    def get_route(
        self,
        technician_id: int,
        route_date: date
    ) -> Optional[Route]:
        """Récupère la tournée d'un technicien pour une date."""
        return self.db.query(Route).filter(
            Route.technician_id == technician_id,
            Route.route_date == route_date,
            Route.tenant_id == self.tenant_id
        ).first()

    def create_route(self, data: RouteCreate) -> Route:
        """Crée une tournée."""
        route = Route(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(route)
        self.db.commit()
        self.db.refresh(route)
        return route

    def update_route(self, route_id: int, data: RouteUpdate) -> Optional[Route]:
        """Met à jour une tournée."""
        route = self.db.query(Route).filter(
            Route.id == route_id,
            Route.tenant_id == self.tenant_id
        ).first()
        if not route:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(route, key, value)
        self.db.commit()
        self.db.refresh(route)
        return route

    def get_technician_schedule(
        self,
        technician_id: int,
        date_from: date,
        date_to: date
    ) -> List[Intervention]:
        """Récupère le planning d'un technicien."""
        return self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.technician_id == technician_id,
            Intervention.scheduled_date >= date_from,
            Intervention.scheduled_date <= date_to,
            Intervention.status.notin_([
                InterventionStatus.CANCELLED,
                InterventionStatus.FAILED
            ])
        ).order_by(
            Intervention.scheduled_date,
            Intervention.scheduled_time_start
        ).all()

    # ========================================================================
    # EXPENSES
    # ========================================================================

    def list_expenses(
        self,
        technician_id: Optional[int] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[Expense]:
        """Liste les frais."""
        query = self.db.query(Expense).filter(
            Expense.tenant_id == self.tenant_id
        )
        if technician_id:
            query = query.filter(Expense.technician_id == technician_id)
        if status:
            query = query.filter(Expense.status == status)
        if date_from:
            query = query.filter(Expense.expense_date >= date_from)
        if date_to:
            query = query.filter(Expense.expense_date <= date_to)
        return query.order_by(Expense.expense_date.desc()).all()

    def create_expense(self, data: ExpenseCreate) -> Expense:
        """Crée un frais."""
        expense = Expense(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def approve_expense(
        self,
        expense_id: int,
        approved_by: int
    ) -> Optional[Expense]:
        """Approuve un frais."""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.tenant_id == self.tenant_id
        ).first()
        if not expense:
            return None
        expense.status = "approved"
        expense.approved_by = approved_by
        expense.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def reject_expense(self, expense_id: int, reason: str) -> Optional[Expense]:
        """Rejette un frais."""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.tenant_id == self.tenant_id
        ).first()
        if not expense:
            return None
        expense.status = "rejected"
        expense.notes = reason
        self.db.commit()
        self.db.refresh(expense)
        return expense

    # ========================================================================
    # CONTRACTS
    # ========================================================================

    def list_contracts(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[ServiceContract]:
        """Liste les contrats."""
        query = self.db.query(ServiceContract).filter(
            ServiceContract.tenant_id == self.tenant_id
        )
        if customer_id:
            query = query.filter(ServiceContract.customer_id == customer_id)
        if status:
            query = query.filter(ServiceContract.status == status)
        return query.all()

    def get_contract(self, contract_id: int) -> Optional[ServiceContract]:
        """Récupère un contrat."""
        return self.db.query(ServiceContract).filter(
            ServiceContract.id == contract_id,
            ServiceContract.tenant_id == self.tenant_id
        ).first()

    def create_contract(self, data: ContractCreate) -> ServiceContract:
        """Crée un contrat."""
        contract = ServiceContract(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update_contract(self, contract_id: int, data: ContractUpdate) -> Optional[ServiceContract]:
        """Met à jour un contrat."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(contract, key, value)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    # ========================================================================
    # DASHBOARD & STATS
    # ========================================================================

    def get_intervention_stats(self, days: int = 30) -> InterventionStats:
        """Statistiques des interventions."""
        since = datetime.utcnow() - timedelta(days=days)

        base_query = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.created_at >= since
        )

        total = base_query.count()

        # Par statut
        status_counts = {}
        for status in [InterventionStatus.SCHEDULED, InterventionStatus.IN_PROGRESS,
                       InterventionStatus.COMPLETED, InterventionStatus.CANCELLED]:
            count = base_query.filter(Intervention.status == status).count()
            status_counts[status.value] = count

        # Par type
        type_counts = {}
        for itype in InterventionType:
            count = base_query.filter(Intervention.intervention_type == itype).count()
            type_counts[itype.value] = count

        # Par priorité
        priority_counts = {}
        for priority in InterventionPriority:
            count = base_query.filter(Intervention.priority == priority).count()
            priority_counts[priority.value] = count

        # Temps moyen de complétion
        completed = base_query.filter(
            Intervention.status == InterventionStatus.COMPLETED,
            Intervention.actual_start != None,
            Intervention.actual_end != None
        ).all()

        avg_time = 0
        if completed:
            total_minutes = sum(
                (i.actual_end - i.actual_start).total_seconds() / 60
                for i in completed
            )
            avg_time = total_minutes / len(completed)

        return InterventionStats(
            total=total,
            scheduled=status_counts.get("scheduled", 0),
            in_progress=status_counts.get("in_progress", 0),
            completed=status_counts.get("completed", 0),
            cancelled=status_counts.get("cancelled", 0),
            by_type=type_counts,
            by_priority=priority_counts,
            avg_completion_time=round(avg_time, 2)
        )

    def get_technician_stats(self, days: int = 30) -> List[TechnicianStats]:
        """Statistiques par technicien."""
        technicians = self.list_technicians(active_only=True)
        since = datetime.utcnow() - timedelta(days=days)

        stats = []
        for tech in technicians:
            base_query = self.db.query(Intervention).filter(
                Intervention.tenant_id == self.tenant_id,
                Intervention.technician_id == tech.id,
                Intervention.created_at >= since
            )

            total = base_query.count()
            completed = base_query.filter(
                Intervention.status == InterventionStatus.COMPLETED
            ).count()
            cancelled = base_query.filter(
                Intervention.status == InterventionStatus.CANCELLED
            ).count()

            # Revenu
            revenue = self.db.query(func.sum(Intervention.total_cost)).filter(
                Intervention.tenant_id == self.tenant_id,
                Intervention.technician_id == tech.id,
                Intervention.status == InterventionStatus.COMPLETED,
                Intervention.created_at >= since
            ).scalar() or 0

            stats.append(TechnicianStats(
                technician_id=tech.id,
                technician_name=f"{tech.first_name} {tech.last_name}",
                total_interventions=total,
                completed=completed,
                cancelled=cancelled,
                avg_rating=float(tech.avg_rating),
                total_km=float(tech.total_km_traveled),
                total_revenue=float(revenue)
            ))

        return stats

    def get_dashboard(self, days: int = 30) -> FieldServiceDashboard:
        """Dashboard complet."""
        intervention_stats = self.get_intervention_stats(days)
        technician_stats = self.get_technician_stats(days)

        today = date.today()

        # Interventions aujourd'hui
        today_count = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.scheduled_date == today
        ).count()

        # Techniciens actifs
        active_techs = self.db.query(Technician).filter(
            Technician.tenant_id == self.tenant_id,
            Technician.is_active == True,
            Technician.status.in_([
                TechnicianStatus.AVAILABLE,
                TechnicianStatus.ON_MISSION,
                TechnicianStatus.TRAVELING
            ])
        ).count()

        # En attente d'assignation
        pending = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.technician_id == None,
            Intervention.status == InterventionStatus.SCHEDULED
        ).count()

        # En retard
        overdue = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.scheduled_date < today,
            Intervention.status.notin_([
                InterventionStatus.COMPLETED,
                InterventionStatus.CANCELLED,
                InterventionStatus.FAILED
            ])
        ).count()

        # Revenu total
        since = datetime.utcnow() - timedelta(days=days)
        revenue = self.db.query(func.sum(Intervention.total_cost)).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.status == InterventionStatus.COMPLETED,
            Intervention.created_at >= since
        ).scalar() or Decimal("0")

        # Satisfaction moyenne
        avg_sat = self.db.query(func.avg(Intervention.customer_rating)).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.customer_rating != None,
            Intervention.created_at >= since
        ).scalar() or 0

        return FieldServiceDashboard(
            intervention_stats=intervention_stats,
            technician_stats=technician_stats,
            today_interventions=today_count,
            active_technicians=active_techs,
            pending_assignments=pending,
            overdue_interventions=overdue,
            total_revenue=revenue,
            avg_satisfaction=round(float(avg_sat), 2)
        )
