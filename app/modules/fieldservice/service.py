"""
Service Field Service / Service Terrain - GAP-081

Gestion des interventions terrain:
- Ordres de travail
- Techniciens et équipes
- Planification et dispatch
- Suivi GPS et géolocalisation
- Pièces détachées et stock mobile
- Signatures et photos
- Rapports d'intervention
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


# ============== Énumérations ==============

class WorkOrderType(str, Enum):
    """Types d'ordres de travail"""
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    INSPECTION = "inspection"
    EMERGENCY = "emergency"
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    UPGRADE = "upgrade"


class WorkOrderStatus(str, Enum):
    """Statuts d'ordre de travail"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TechnicianStatus(str, Enum):
    """Statuts technicien"""
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"
    UNAVAILABLE = "unavailable"


class Priority(str, Enum):
    """Priorités"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SkillLevel(str, Enum):
    """Niveaux de compétence"""
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    EXPERT = "expert"


class PartUsageType(str, Enum):
    """Types d'utilisation pièce"""
    INSTALLED = "installed"
    REPLACED = "replaced"
    RETURNED = "returned"
    DEFECTIVE = "defective"


# ============== Data Classes ==============

@dataclass
class FSSkill:
    """Compétence technicien"""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str = ""
    category: str = ""
    certification_required: bool = False
    certification_validity_days: int = 365
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TechnicianSkill:
    """Compétence d'un technicien"""
    skill_id: str
    skill_name: str
    level: SkillLevel = SkillLevel.INTERMEDIATE
    certified: bool = False
    certification_date: Optional[date] = None
    certification_expiry: Optional[date] = None


@dataclass
class FSTechnician:
    """Technicien terrain"""
    id: str
    tenant_id: str
    employee_id: str
    code: str
    first_name: str
    last_name: str
    email: str
    phone: str
    skills: List[TechnicianSkill] = field(default_factory=list)
    status: TechnicianStatus = TechnicianStatus.AVAILABLE
    current_location_lat: Optional[Decimal] = None
    current_location_lng: Optional[Decimal] = None
    last_location_update: Optional[datetime] = None
    home_zone_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    max_daily_work_orders: int = 8
    hourly_rate: Decimal = Decimal("0")
    overtime_rate: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class FSServiceZone:
    """Zone de service"""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str = ""
    polygon_coordinates: List[Dict] = field(default_factory=list)
    center_lat: Optional[Decimal] = None
    center_lng: Optional[Decimal] = None
    radius_km: Optional[Decimal] = None
    assigned_technicians: List[str] = field(default_factory=list)
    travel_time_minutes: int = 30
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FSCustomerSite:
    """Site client"""
    id: str
    tenant_id: str
    customer_id: str
    customer_name: str
    name: str
    code: str
    address_line1: str
    address_line2: str = ""
    city: str = ""
    postal_code: str = ""
    country: str = "France"
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    access_instructions: str = ""
    special_requirements: str = ""
    equipment_list: List[Dict] = field(default_factory=list)
    zone_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkOrderLine:
    """Ligne d'ordre de travail"""
    id: str
    description: str
    task_type: str = ""
    estimated_duration_minutes: int = 30
    actual_duration_minutes: int = 0
    completed: bool = False
    notes: str = ""


@dataclass
class PartUsage:
    """Utilisation de pièce"""
    id: str
    part_id: str
    part_code: str
    part_name: str
    serial_number: str = ""
    quantity: int = 1
    usage_type: PartUsageType = PartUsageType.INSTALLED
    unit_cost: Decimal = Decimal("0")
    unit_price: Decimal = Decimal("0")
    notes: str = ""
    added_at: datetime = field(default_factory=datetime.now)


@dataclass
class TimeEntry:
    """Entrée temps"""
    id: str
    technician_id: str
    entry_type: str  # travel, work, break, admin
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 0
    is_billable: bool = True
    notes: str = ""


@dataclass
class Attachment:
    """Pièce jointe"""
    id: str
    filename: str
    file_type: str  # photo, document, signature
    file_url: str
    description: str = ""
    uploaded_at: datetime = field(default_factory=datetime.now)
    uploaded_by: str = ""


@dataclass
class FSWorkOrder:
    """Ordre de travail terrain"""
    id: str
    tenant_id: str
    number: str
    work_order_type: WorkOrderType
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    priority: Priority = Priority.MEDIUM

    # Client et site
    customer_id: str = ""
    customer_name: str = ""
    site_id: str = ""
    site_name: str = ""
    site_address: str = ""

    # Description
    title: str = ""
    description: str = ""
    problem_description: str = ""
    resolution_notes: str = ""

    # Planification
    scheduled_date: Optional[date] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    estimated_duration_minutes: int = 60

    # Exécution
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_duration_minutes: int = 0

    # Technicien
    assigned_technician_id: Optional[str] = None
    assigned_technician_name: str = ""
    required_skills: List[str] = field(default_factory=list)

    # Lignes et pièces
    lines: List[WorkOrderLine] = field(default_factory=list)
    parts_used: List[PartUsage] = field(default_factory=list)
    time_entries: List[TimeEntry] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)

    # Signature
    customer_signature_url: str = ""
    customer_signed_by: str = ""
    customer_signed_at: Optional[datetime] = None

    # Financier
    labor_cost: Decimal = Decimal("0")
    parts_cost: Decimal = Decimal("0")
    travel_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    labor_price: Decimal = Decimal("0")
    parts_price: Decimal = Decimal("0")
    travel_price: Decimal = Decimal("0")
    total_price: Decimal = Decimal("0")
    is_billable: bool = True
    invoice_id: Optional[str] = None

    # Références
    contract_id: Optional[str] = None
    asset_id: Optional[str] = None
    parent_wo_id: Optional[str] = None

    # SLA
    sla_response_due: Optional[datetime] = None
    sla_resolution_due: Optional[datetime] = None
    sla_breached: bool = False

    # Métadonnées
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Route:
    """Route planifiée"""
    id: str
    tenant_id: str
    technician_id: str
    technician_name: str
    route_date: date
    work_orders: List[str] = field(default_factory=list)
    optimized: bool = False
    total_distance_km: Decimal = Decimal("0")
    estimated_duration_minutes: int = 0
    start_location_lat: Optional[Decimal] = None
    start_location_lng: Optional[Decimal] = None
    end_location_lat: Optional[Decimal] = None
    end_location_lng: Optional[Decimal] = None
    status: str = "planned"  # planned, in_progress, completed
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MobileInventory:
    """Stock mobile technicien"""
    id: str
    tenant_id: str
    technician_id: str
    part_id: str
    part_code: str
    part_name: str
    quantity_on_hand: int = 0
    min_quantity: int = 1
    max_quantity: int = 10
    vehicle_location: str = ""
    last_replenished: Optional[date] = None
    last_counted: Optional[date] = None


@dataclass
class ServiceReport:
    """Rapport d'intervention"""
    id: str
    tenant_id: str
    work_order_id: str
    work_order_number: str
    customer_id: str
    customer_name: str
    site_name: str
    technician_id: str
    technician_name: str
    report_date: date

    # Contenu
    work_performed: str = ""
    findings: str = ""
    recommendations: str = ""
    follow_up_required: bool = False
    follow_up_notes: str = ""

    # Statut équipement
    equipment_status: str = "operational"  # operational, degraded, failed
    equipment_notes: str = ""

    # Photos et signatures
    photos: List[str] = field(default_factory=list)
    customer_signature_url: str = ""
    technician_signature_url: str = ""

    # Email
    emailed_to_customer: bool = False
    email_sent_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DispatchStats:
    """Statistiques dispatch"""
    tenant_id: str
    period_start: date
    period_end: date
    total_work_orders: int = 0
    completed_work_orders: int = 0
    cancelled_work_orders: int = 0
    average_completion_time_minutes: Decimal = Decimal("0")
    first_time_fix_rate: Decimal = Decimal("0")
    sla_compliance_rate: Decimal = Decimal("0")
    technician_utilization: Decimal = Decimal("0")
    customer_satisfaction_score: Decimal = Decimal("0")
    total_revenue: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    by_technician: Dict[str, Dict] = field(default_factory=dict)
    by_zone: Dict[str, Dict] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)


# ============== Service ==============

class FieldService:
    """
    Service de gestion des interventions terrain.

    Fonctionnalités:
    - Ordres de travail et planification
    - Gestion des techniciens
    - Dispatch et optimisation routes
    - Stock mobile
    - Rapports d'intervention
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._skills: Dict[str, FSSkill] = {}
        self._technicians: Dict[str, FSTechnician] = {}
        self._zones: Dict[str, FSServiceZone] = {}
        self._sites: Dict[str, FSCustomerSite] = {}
        self._work_orders: Dict[str, FSWorkOrder] = {}
        self._routes: Dict[str, Route] = {}
        self._mobile_inventory: Dict[str, MobileInventory] = {}
        self._reports: Dict[str, ServiceReport] = {}
        self._wo_counter = 0

    # ========== Compétences ==========

    def create_skill(
        self,
        name: str,
        code: str,
        description: str = "",
        category: str = "",
        certification_required: bool = False,
        certification_validity_days: int = 365
    ) -> FSSkill:
        """Créer une compétence"""
        skill = FSSkill(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            code=code.upper(),
            description=description,
            category=category,
            certification_required=certification_required,
            certification_validity_days=certification_validity_days
        )
        self._skills[skill.id] = skill
        return skill

    def get_skills(
        self,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[FSSkill]:
        """Lister les compétences"""
        skills = list(self._skills.values())

        if active_only:
            skills = [s for s in skills if s.is_active]
        if category:
            skills = [s for s in skills if s.category == category]

        return sorted(skills, key=lambda x: x.name)

    # ========== Techniciens ==========

    def create_technician(
        self,
        employee_id: str,
        code: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        skills: List[Dict] = None,
        home_zone_id: Optional[str] = None,
        max_daily_work_orders: int = 8,
        hourly_rate: Decimal = Decimal("0"),
        overtime_rate: Decimal = Decimal("0")
    ) -> FSTechnician:
        """Créer un technicien"""
        tech_skills = []
        if skills:
            for s in skills:
                tech_skills.append(TechnicianSkill(
                    skill_id=s.get("skill_id", ""),
                    skill_name=s.get("skill_name", ""),
                    level=SkillLevel(s.get("level", "intermediate")),
                    certified=s.get("certified", False),
                    certification_date=s.get("certification_date"),
                    certification_expiry=s.get("certification_expiry")
                ))

        technician = FSTechnician(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            code=code.upper(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            skills=tech_skills,
            home_zone_id=home_zone_id,
            max_daily_work_orders=max_daily_work_orders,
            hourly_rate=hourly_rate,
            overtime_rate=overtime_rate
        )
        self._technicians[technician.id] = technician
        return technician

    def update_technician_location(
        self,
        technician_id: str,
        latitude: Decimal,
        longitude: Decimal
    ) -> Optional[FSTechnician]:
        """Mettre à jour position GPS technicien"""
        tech = self._technicians.get(technician_id)
        if not tech:
            return None

        tech.current_location_lat = latitude
        tech.current_location_lng = longitude
        tech.last_location_update = datetime.now()
        return tech

    def update_technician_status(
        self,
        technician_id: str,
        status: TechnicianStatus
    ) -> Optional[FSTechnician]:
        """Mettre à jour statut technicien"""
        tech = self._technicians.get(technician_id)
        if not tech:
            return None

        tech.status = status
        return tech

    def get_available_technicians(
        self,
        date: date,
        skills_required: List[str] = None,
        zone_id: Optional[str] = None
    ) -> List[FSTechnician]:
        """Obtenir techniciens disponibles"""
        available = []

        for tech in self._technicians.values():
            if not tech.is_active:
                continue
            if tech.status in [TechnicianStatus.OFF_DUTY, TechnicianStatus.UNAVAILABLE]:
                continue

            # Vérifier compétences
            if skills_required:
                tech_skill_ids = [s.skill_id for s in tech.skills]
                if not all(s in tech_skill_ids for s in skills_required):
                    continue

            # Vérifier zone
            if zone_id and tech.home_zone_id != zone_id:
                zone = self._zones.get(zone_id)
                if zone and tech.id not in zone.assigned_technicians:
                    continue

            # Vérifier charge de travail
            wo_count = sum(
                1 for wo in self._work_orders.values()
                if wo.assigned_technician_id == tech.id
                and wo.scheduled_date == date
                and wo.status not in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]
            )
            if wo_count >= tech.max_daily_work_orders:
                continue

            available.append(tech)

        return available

    def get_technician(self, technician_id: str) -> Optional[FSTechnician]:
        """Obtenir un technicien"""
        return self._technicians.get(technician_id)

    def list_technicians(
        self,
        status: Optional[TechnicianStatus] = None,
        zone_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[FSTechnician]:
        """Lister les techniciens"""
        technicians = list(self._technicians.values())

        if active_only:
            technicians = [t for t in technicians if t.is_active]
        if status:
            technicians = [t for t in technicians if t.status == status]
        if zone_id:
            technicians = [t for t in technicians if t.home_zone_id == zone_id]

        return sorted(technicians, key=lambda x: x.full_name)

    # ========== Zones ==========

    def create_zone(
        self,
        name: str,
        code: str,
        description: str = "",
        center_lat: Optional[Decimal] = None,
        center_lng: Optional[Decimal] = None,
        radius_km: Optional[Decimal] = None,
        travel_time_minutes: int = 30
    ) -> FSServiceZone:
        """Créer une zone de service"""
        zone = FSServiceZone(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            code=code.upper(),
            description=description,
            center_lat=center_lat,
            center_lng=center_lng,
            radius_km=radius_km,
            travel_time_minutes=travel_time_minutes
        )
        self._zones[zone.id] = zone
        return zone

    def assign_technician_to_zone(
        self,
        zone_id: str,
        technician_id: str
    ) -> Optional[FSServiceZone]:
        """Assigner technicien à zone"""
        zone = self._zones.get(zone_id)
        tech = self._technicians.get(technician_id)

        if not zone or not tech:
            return None

        if technician_id not in zone.assigned_technicians:
            zone.assigned_technicians.append(technician_id)

        return zone

    # ========== Sites clients ==========

    def create_customer_site(
        self,
        customer_id: str,
        customer_name: str,
        name: str,
        code: str,
        address_line1: str,
        city: str = "",
        postal_code: str = "",
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None,
        contact_name: str = "",
        contact_phone: str = "",
        zone_id: Optional[str] = None
    ) -> FSCustomerSite:
        """Créer un site client"""
        site = FSCustomerSite(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            customer_name=customer_name,
            name=name,
            code=code.upper(),
            address_line1=address_line1,
            city=city,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            contact_name=contact_name,
            contact_phone=contact_phone,
            zone_id=zone_id
        )
        self._sites[site.id] = site
        return site

    def get_customer_sites(self, customer_id: str) -> List[FSCustomerSite]:
        """Obtenir sites d'un client"""
        return [
            s for s in self._sites.values()
            if s.customer_id == customer_id and s.is_active
        ]

    # ========== Ordres de travail ==========

    def create_work_order(
        self,
        work_order_type: WorkOrderType,
        customer_id: str,
        customer_name: str,
        site_id: str,
        site_name: str,
        site_address: str,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        scheduled_date: Optional[date] = None,
        estimated_duration_minutes: int = 60,
        required_skills: List[str] = None,
        contract_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        is_billable: bool = True,
        created_by: str = ""
    ) -> FSWorkOrder:
        """Créer un ordre de travail"""
        self._wo_counter += 1
        number = f"WO-{datetime.now().year}-{self._wo_counter:06d}"

        wo = FSWorkOrder(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            number=number,
            work_order_type=work_order_type,
            customer_id=customer_id,
            customer_name=customer_name,
            site_id=site_id,
            site_name=site_name,
            site_address=site_address,
            title=title,
            description=description,
            priority=priority,
            scheduled_date=scheduled_date,
            estimated_duration_minutes=estimated_duration_minutes,
            required_skills=required_skills or [],
            contract_id=contract_id,
            asset_id=asset_id,
            is_billable=is_billable,
            created_by=created_by
        )

        # Calculer SLA si priorité haute
        if priority in [Priority.HIGH, Priority.CRITICAL, Priority.EMERGENCY]:
            now = datetime.now()
            if priority == Priority.EMERGENCY:
                wo.sla_response_due = now + timedelta(hours=2)
                wo.sla_resolution_due = now + timedelta(hours=4)
            elif priority == Priority.CRITICAL:
                wo.sla_response_due = now + timedelta(hours=4)
                wo.sla_resolution_due = now + timedelta(hours=8)
            else:
                wo.sla_response_due = now + timedelta(hours=8)
                wo.sla_resolution_due = now + timedelta(hours=24)

        self._work_orders[wo.id] = wo
        return wo

    def assign_work_order(
        self,
        work_order_id: str,
        technician_id: str,
        scheduled_start_time: Optional[datetime] = None,
        scheduled_end_time: Optional[datetime] = None
    ) -> Optional[FSWorkOrder]:
        """Assigner ordre de travail à technicien"""
        wo = self._work_orders.get(work_order_id)
        tech = self._technicians.get(technician_id)

        if not wo or not tech:
            return None

        wo.assigned_technician_id = technician_id
        wo.assigned_technician_name = tech.full_name
        wo.scheduled_start_time = scheduled_start_time
        wo.scheduled_end_time = scheduled_end_time

        if scheduled_start_time:
            wo.scheduled_date = scheduled_start_time.date()

        wo.status = WorkOrderStatus.SCHEDULED
        wo.updated_at = datetime.now()

        return wo

    def dispatch_work_order(self, work_order_id: str) -> Optional[FSWorkOrder]:
        """Dispatcher ordre de travail"""
        wo = self._work_orders.get(work_order_id)
        if not wo or wo.status != WorkOrderStatus.SCHEDULED:
            return None

        wo.status = WorkOrderStatus.DISPATCHED
        wo.updated_at = datetime.now()

        # Mettre à jour statut technicien
        if wo.assigned_technician_id:
            tech = self._technicians.get(wo.assigned_technician_id)
            if tech:
                tech.status = TechnicianStatus.EN_ROUTE

        return wo

    def start_work_order(
        self,
        work_order_id: str,
        start_time: Optional[datetime] = None
    ) -> Optional[FSWorkOrder]:
        """Démarrer intervention"""
        wo = self._work_orders.get(work_order_id)
        if not wo or wo.status not in [
            WorkOrderStatus.DISPATCHED,
            WorkOrderStatus.EN_ROUTE,
            WorkOrderStatus.ON_SITE
        ]:
            return None

        wo.actual_start_time = start_time or datetime.now()
        wo.status = WorkOrderStatus.IN_PROGRESS
        wo.updated_at = datetime.now()

        # Ajouter entrée temps
        time_entry = TimeEntry(
            id=str(uuid4()),
            technician_id=wo.assigned_technician_id or "",
            entry_type="work",
            start_time=wo.actual_start_time,
            is_billable=wo.is_billable
        )
        wo.time_entries.append(time_entry)

        # Mettre à jour technicien
        if wo.assigned_technician_id:
            tech = self._technicians.get(wo.assigned_technician_id)
            if tech:
                tech.status = TechnicianStatus.ON_SITE

        return wo

    def add_work_order_line(
        self,
        work_order_id: str,
        description: str,
        task_type: str = "",
        estimated_duration_minutes: int = 30
    ) -> Optional[FSWorkOrder]:
        """Ajouter ligne à l'ordre de travail"""
        wo = self._work_orders.get(work_order_id)
        if not wo:
            return None

        line = WorkOrderLine(
            id=str(uuid4()),
            description=description,
            task_type=task_type,
            estimated_duration_minutes=estimated_duration_minutes
        )
        wo.lines.append(line)
        wo.updated_at = datetime.now()

        return wo

    def complete_work_order_line(
        self,
        work_order_id: str,
        line_id: str,
        actual_duration_minutes: int,
        notes: str = ""
    ) -> Optional[FSWorkOrder]:
        """Compléter une ligne d'ordre de travail"""
        wo = self._work_orders.get(work_order_id)
        if not wo:
            return None

        for line in wo.lines:
            if line.id == line_id:
                line.completed = True
                line.actual_duration_minutes = actual_duration_minutes
                line.notes = notes
                break

        wo.updated_at = datetime.now()
        return wo

    def add_part_usage(
        self,
        work_order_id: str,
        part_id: str,
        part_code: str,
        part_name: str,
        quantity: int,
        usage_type: PartUsageType,
        unit_cost: Decimal,
        unit_price: Decimal,
        serial_number: str = ""
    ) -> Optional[FSWorkOrder]:
        """Ajouter pièce utilisée"""
        wo = self._work_orders.get(work_order_id)
        if not wo:
            return None

        part = PartUsage(
            id=str(uuid4()),
            part_id=part_id,
            part_code=part_code,
            part_name=part_name,
            serial_number=serial_number,
            quantity=quantity,
            usage_type=usage_type,
            unit_cost=unit_cost,
            unit_price=unit_price
        )
        wo.parts_used.append(part)

        # Mettre à jour coûts
        wo.parts_cost += unit_cost * quantity
        wo.parts_price += unit_price * quantity
        wo.total_cost = wo.labor_cost + wo.parts_cost + wo.travel_cost
        wo.total_price = wo.labor_price + wo.parts_price + wo.travel_price
        wo.updated_at = datetime.now()

        # Déduire du stock mobile
        if wo.assigned_technician_id:
            for inv in self._mobile_inventory.values():
                if (inv.technician_id == wo.assigned_technician_id
                    and inv.part_id == part_id):
                    inv.quantity_on_hand = max(0, inv.quantity_on_hand - quantity)

        return wo

    def add_attachment(
        self,
        work_order_id: str,
        filename: str,
        file_type: str,
        file_url: str,
        description: str = "",
        uploaded_by: str = ""
    ) -> Optional[FSWorkOrder]:
        """Ajouter pièce jointe"""
        wo = self._work_orders.get(work_order_id)
        if not wo:
            return None

        attachment = Attachment(
            id=str(uuid4()),
            filename=filename,
            file_type=file_type,
            file_url=file_url,
            description=description,
            uploaded_by=uploaded_by
        )
        wo.attachments.append(attachment)
        wo.updated_at = datetime.now()

        return wo

    def capture_signature(
        self,
        work_order_id: str,
        signature_url: str,
        signed_by: str
    ) -> Optional[FSWorkOrder]:
        """Capturer signature client"""
        wo = self._work_orders.get(work_order_id)
        if not wo:
            return None

        wo.customer_signature_url = signature_url
        wo.customer_signed_by = signed_by
        wo.customer_signed_at = datetime.now()
        wo.updated_at = datetime.now()

        return wo

    def complete_work_order(
        self,
        work_order_id: str,
        resolution_notes: str = "",
        end_time: Optional[datetime] = None
    ) -> Optional[FSWorkOrder]:
        """Compléter ordre de travail"""
        wo = self._work_orders.get(work_order_id)
        if not wo or wo.status != WorkOrderStatus.IN_PROGRESS:
            return None

        wo.actual_end_time = end_time or datetime.now()
        wo.resolution_notes = resolution_notes
        wo.status = WorkOrderStatus.COMPLETED

        # Calculer durée
        if wo.actual_start_time:
            delta = wo.actual_end_time - wo.actual_start_time
            wo.actual_duration_minutes = int(delta.total_seconds() / 60)

        # Fermer entrée temps
        for entry in wo.time_entries:
            if entry.entry_type == "work" and not entry.end_time:
                entry.end_time = wo.actual_end_time
                entry.duration_minutes = wo.actual_duration_minutes

        # Calculer coût main d'oeuvre
        if wo.assigned_technician_id:
            tech = self._technicians.get(wo.assigned_technician_id)
            if tech:
                hours = Decimal(wo.actual_duration_minutes) / Decimal("60")
                wo.labor_cost = hours * tech.hourly_rate
                wo.labor_price = hours * tech.hourly_rate * Decimal("1.5")  # Marge 50%

        wo.total_cost = wo.labor_cost + wo.parts_cost + wo.travel_cost
        wo.total_price = wo.labor_price + wo.parts_price + wo.travel_price
        wo.updated_at = datetime.now()

        # Vérifier SLA
        if wo.sla_resolution_due and wo.actual_end_time > wo.sla_resolution_due:
            wo.sla_breached = True

        # Mettre à jour technicien
        if wo.assigned_technician_id:
            tech = self._technicians.get(wo.assigned_technician_id)
            if tech:
                tech.status = TechnicianStatus.AVAILABLE

        return wo

    def cancel_work_order(
        self,
        work_order_id: str,
        reason: str
    ) -> Optional[FSWorkOrder]:
        """Annuler ordre de travail"""
        wo = self._work_orders.get(work_order_id)
        if not wo or wo.status == WorkOrderStatus.COMPLETED:
            return None

        wo.status = WorkOrderStatus.CANCELLED
        wo.resolution_notes = f"Annulé: {reason}"
        wo.updated_at = datetime.now()

        return wo

    def get_work_order(self, work_order_id: str) -> Optional[FSWorkOrder]:
        """Obtenir ordre de travail"""
        return self._work_orders.get(work_order_id)

    def list_work_orders(
        self,
        status: Optional[WorkOrderStatus] = None,
        technician_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        priority: Optional[Priority] = None
    ) -> List[FSWorkOrder]:
        """Lister ordres de travail"""
        work_orders = list(self._work_orders.values())

        if status:
            work_orders = [w for w in work_orders if w.status == status]
        if technician_id:
            work_orders = [w for w in work_orders if w.assigned_technician_id == technician_id]
        if customer_id:
            work_orders = [w for w in work_orders if w.customer_id == customer_id]
        if date_from:
            work_orders = [w for w in work_orders
                          if w.scheduled_date and w.scheduled_date >= date_from]
        if date_to:
            work_orders = [w for w in work_orders
                          if w.scheduled_date and w.scheduled_date <= date_to]
        if priority:
            work_orders = [w for w in work_orders if w.priority == priority]

        return sorted(work_orders, key=lambda x: (x.scheduled_date or date.max, x.priority.value))

    def get_technician_schedule(
        self,
        technician_id: str,
        schedule_date: date
    ) -> List[FSWorkOrder]:
        """Obtenir planning technicien"""
        return [
            wo for wo in self._work_orders.values()
            if wo.assigned_technician_id == technician_id
            and wo.scheduled_date == schedule_date
            and wo.status not in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]
        ]

    # ========== Routes ==========

    def create_route(
        self,
        technician_id: str,
        route_date: date,
        work_order_ids: List[str]
    ) -> Optional[Route]:
        """Créer une route"""
        tech = self._technicians.get(technician_id)
        if not tech:
            return None

        # Vérifier que tous les WO existent
        for wo_id in work_order_ids:
            if wo_id not in self._work_orders:
                return None

        route = Route(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            technician_id=technician_id,
            technician_name=tech.full_name,
            route_date=route_date,
            work_orders=work_order_ids
        )
        self._routes[route.id] = route
        return route

    def optimize_route(self, route_id: str) -> Optional[Route]:
        """Optimiser route (simulation)"""
        route = self._routes.get(route_id)
        if not route:
            return None

        # Simulation d'optimisation (en réel: algo TSP)
        route.optimized = True
        route.total_distance_km = Decimal(str(len(route.work_orders) * 15))
        route.estimated_duration_minutes = len(route.work_orders) * 60 + 30

        return route

    # ========== Stock mobile ==========

    def add_to_mobile_inventory(
        self,
        technician_id: str,
        part_id: str,
        part_code: str,
        part_name: str,
        quantity: int,
        min_quantity: int = 1,
        max_quantity: int = 10
    ) -> Optional[MobileInventory]:
        """Ajouter au stock mobile"""
        tech = self._technicians.get(technician_id)
        if not tech:
            return None

        # Vérifier si existe déjà
        for inv in self._mobile_inventory.values():
            if inv.technician_id == technician_id and inv.part_id == part_id:
                inv.quantity_on_hand += quantity
                inv.last_replenished = date.today()
                return inv

        inventory = MobileInventory(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            technician_id=technician_id,
            part_id=part_id,
            part_code=part_code,
            part_name=part_name,
            quantity_on_hand=quantity,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            last_replenished=date.today()
        )
        self._mobile_inventory[inventory.id] = inventory
        return inventory

    def get_mobile_inventory(self, technician_id: str) -> List[MobileInventory]:
        """Obtenir stock mobile technicien"""
        return [
            inv for inv in self._mobile_inventory.values()
            if inv.technician_id == technician_id
        ]

    def get_low_stock_alerts(self) -> List[MobileInventory]:
        """Obtenir alertes stock bas"""
        return [
            inv for inv in self._mobile_inventory.values()
            if inv.quantity_on_hand < inv.min_quantity
        ]

    # ========== Rapports ==========

    def generate_service_report(
        self,
        work_order_id: str,
        work_performed: str,
        findings: str = "",
        recommendations: str = "",
        equipment_status: str = "operational",
        follow_up_required: bool = False,
        follow_up_notes: str = ""
    ) -> Optional[ServiceReport]:
        """Générer rapport d'intervention"""
        wo = self._work_orders.get(work_order_id)
        if not wo or wo.status != WorkOrderStatus.COMPLETED:
            return None

        report = ServiceReport(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            work_order_id=work_order_id,
            work_order_number=wo.number,
            customer_id=wo.customer_id,
            customer_name=wo.customer_name,
            site_name=wo.site_name,
            technician_id=wo.assigned_technician_id or "",
            technician_name=wo.assigned_technician_name,
            report_date=date.today(),
            work_performed=work_performed,
            findings=findings,
            recommendations=recommendations,
            follow_up_required=follow_up_required,
            follow_up_notes=follow_up_notes,
            equipment_status=equipment_status,
            photos=[a.file_url for a in wo.attachments if a.file_type == "photo"],
            customer_signature_url=wo.customer_signature_url
        )
        self._reports[report.id] = report
        return report

    def get_service_report(self, report_id: str) -> Optional[ServiceReport]:
        """Obtenir rapport"""
        return self._reports.get(report_id)

    # ========== Statistiques ==========

    def get_dispatch_stats(
        self,
        period_start: date,
        period_end: date
    ) -> DispatchStats:
        """Calculer statistiques dispatch"""
        stats = DispatchStats(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end
        )

        work_orders = [
            wo for wo in self._work_orders.values()
            if wo.scheduled_date and period_start <= wo.scheduled_date <= period_end
        ]

        stats.total_work_orders = len(work_orders)
        completed = [wo for wo in work_orders if wo.status == WorkOrderStatus.COMPLETED]
        stats.completed_work_orders = len(completed)
        stats.cancelled_work_orders = len([
            wo for wo in work_orders if wo.status == WorkOrderStatus.CANCELLED
        ])

        if completed:
            total_duration = sum(wo.actual_duration_minutes for wo in completed)
            stats.average_completion_time_minutes = Decimal(total_duration) / len(completed)

            # Premier passage réussi (simulation)
            stats.first_time_fix_rate = Decimal("0.85")

            # SLA compliance
            sla_met = len([wo for wo in completed if not wo.sla_breached])
            stats.sla_compliance_rate = Decimal(sla_met) / len(completed) * 100

            # Revenus
            stats.total_revenue = sum(wo.total_price for wo in completed)
            stats.total_cost = sum(wo.total_cost for wo in completed)

        # Par technicien
        for tech in self._technicians.values():
            tech_wos = [wo for wo in completed if wo.assigned_technician_id == tech.id]
            if tech_wos:
                stats.by_technician[tech.id] = {
                    "name": tech.full_name,
                    "completed": len(tech_wos),
                    "revenue": sum(wo.total_price for wo in tech_wos)
                }

        # Par type
        for wo in work_orders:
            wo_type = wo.work_order_type.value
            stats.by_type[wo_type] = stats.by_type.get(wo_type, 0) + 1

        return stats

    def get_sla_alerts(self) -> List[FSWorkOrder]:
        """Obtenir alertes SLA"""
        now = datetime.now()
        alerts = []

        for wo in self._work_orders.values():
            if wo.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]:
                continue

            # Vérifier SLA réponse
            if wo.sla_response_due and wo.sla_response_due < now:
                if not wo.actual_start_time:
                    alerts.append(wo)
                    continue

            # Vérifier SLA résolution
            if wo.sla_resolution_due and wo.sla_resolution_due < now:
                alerts.append(wo)

        return sorted(alerts, key=lambda x: x.sla_resolution_due or datetime.max)


def create_field_service(tenant_id: str) -> FieldService:
    """Factory function pour créer le service terrain"""
    return FieldService(tenant_id)
