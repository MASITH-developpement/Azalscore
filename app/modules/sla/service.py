"""
Module SLA Management - GAP-074

Gestion des accords de niveau de service:
- Définition des SLAs
- Objectifs de performance
- Suivi en temps réel
- Escalades automatiques
- Rapports de conformité
- Pénalités et bonus
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid


# ============== Énumérations ==============

class SLAType(str, Enum):
    """Type de SLA."""
    RESPONSE_TIME = "response_time"
    RESOLUTION_TIME = "resolution_time"
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    CUSTOM = "custom"


class SLAPriority(str, Enum):
    """Priorité SLA."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SLAStatus(str, Enum):
    """Statut du SLA."""
    ACTIVE = "active"
    PAUSED = "paused"
    BREACHED = "breached"
    MET = "met"
    EXPIRED = "expired"


class EscalationLevel(str, Enum):
    """Niveau d'escalade."""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    MANAGEMENT = "management"
    EXECUTIVE = "executive"


class MetricUnit(str, Enum):
    """Unité de mesure."""
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    PERCENT = "percent"
    COUNT = "count"


class BusinessHoursType(str, Enum):
    """Type d'heures ouvrées."""
    CALENDAR = "calendar"  # 24/7
    BUSINESS = "business"  # Heures bureau
    CUSTOM = "custom"


# ============== Data Classes ==============

@dataclass
class BusinessHours:
    """Définition des heures ouvrées."""
    id: str
    tenant_id: str
    name: str

    hours_type: BusinessHoursType = BusinessHoursType.BUSINESS

    # Jours ouvrés (0=Lundi, 6=Dimanche)
    working_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    start_time: time = field(default_factory=lambda: time(9, 0))
    end_time: time = field(default_factory=lambda: time(18, 0))

    # Jours fériés
    holidays: List[date] = field(default_factory=list)

    timezone: str = "Europe/Paris"
    is_default: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SLATarget:
    """Objectif SLA."""
    id: str
    sla_id: str
    name: str
    description: str

    # Type et mesure
    sla_type: SLAType = SLAType.RESPONSE_TIME
    metric_unit: MetricUnit = MetricUnit.HOURS

    # Objectifs
    target_value: Decimal = Decimal("0")
    warning_threshold_percent: Decimal = Decimal("80")  # Alerte à 80%
    critical_threshold_percent: Decimal = Decimal("90")  # Critique à 90%

    # Priorité (objectifs différents par priorité)
    priority: Optional[SLAPriority] = None

    # Pondération pour score global
    weight: Decimal = Decimal("1")

    is_active: bool = True


@dataclass
class SLAPolicy:
    """Politique SLA."""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str

    # Applicabilité
    applies_to_entity_type: str = ""  # ticket, order, project, etc.
    applies_to_categories: List[str] = field(default_factory=list)
    applies_to_customer_segments: List[str] = field(default_factory=list)

    # Heures ouvrées
    business_hours_id: Optional[str] = None
    use_business_hours: bool = True

    # Objectifs
    targets: List[SLATarget] = field(default_factory=list)

    # Escalade
    escalation_enabled: bool = True
    auto_escalate: bool = True

    # Pénalités/Bonus
    penalty_enabled: bool = False
    penalty_percent_per_breach: Decimal = Decimal("0")
    max_penalty_percent: Decimal = Decimal("0")
    bonus_enabled: bool = False
    bonus_percent_for_exceeding: Decimal = Decimal("0")

    # Période
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EscalationRule:
    """Règle d'escalade."""
    id: str
    tenant_id: str
    sla_policy_id: str

    level: EscalationLevel = EscalationLevel.LEVEL_1

    # Conditions
    trigger_percent: Decimal = Decimal("50")  # % du temps SLA écoulé
    trigger_on_breach: bool = False

    # Actions
    notify_user_ids: List[str] = field(default_factory=list)
    notify_roles: List[str] = field(default_factory=list)
    notify_email: str = ""

    # Auto-actions
    auto_reassign: bool = False
    reassign_to_user_id: str = ""
    reassign_to_group_id: str = ""

    priority_boost: bool = False
    new_priority: Optional[SLAPriority] = None

    # Message
    notification_template: str = ""

    is_active: bool = True
    sort_order: int = 0

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SLAInstance:
    """Instance SLA (application à une entité)."""
    id: str
    tenant_id: str
    sla_policy_id: str

    # Entité concernée
    entity_type: str = ""
    entity_id: str = ""

    # Statut
    status: SLAStatus = SLAStatus.ACTIVE
    priority: SLAPriority = SLAPriority.MEDIUM

    # Temps
    started_at: datetime = field(default_factory=datetime.utcnow)
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Pause (hors heures ouvrées, en attente client, etc.)
    paused_at: Optional[datetime] = None
    total_paused_duration_minutes: int = 0
    pause_reason: str = ""

    # Calculs
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None
    business_hours_elapsed_minutes: int = 0

    # Échéances
    response_due_at: Optional[datetime] = None
    resolution_due_at: Optional[datetime] = None

    # Breaches
    response_breached: bool = False
    resolution_breached: bool = False
    breach_count: int = 0
    first_breach_at: Optional[datetime] = None

    # Escalades
    current_escalation_level: Optional[EscalationLevel] = None
    escalation_history: List[Dict[str, Any]] = field(default_factory=list)

    # Scores
    compliance_score: Decimal = Decimal("100")

    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SLAEvent:
    """Événement SLA."""
    id: str
    tenant_id: str
    sla_instance_id: str

    event_type: str = ""  # started, paused, resumed, responded, resolved, breached, escalated
    event_data: Dict[str, Any] = field(default_factory=dict)

    user_id: str = ""
    notes: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SLABreach:
    """Violation SLA."""
    id: str
    tenant_id: str
    sla_instance_id: str
    sla_policy_id: str
    target_id: str

    # Détails
    breach_type: str = ""  # response, resolution
    target_value: Decimal = Decimal("0")
    actual_value: Decimal = Decimal("0")
    exceeded_by: Decimal = Decimal("0")

    # Pénalité
    penalty_applied: bool = False
    penalty_amount: Decimal = Decimal("0")

    # Résolution
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SLAReport:
    """Rapport SLA."""
    tenant_id: str
    period_start: date
    period_end: date
    sla_policy_id: Optional[str] = None

    # Volume
    total_instances: int = 0
    active_instances: int = 0
    completed_instances: int = 0

    # Conformité
    met_instances: int = 0
    breached_instances: int = 0
    compliance_rate: Decimal = Decimal("0")

    # Performance
    avg_response_time_minutes: Decimal = Decimal("0")
    avg_resolution_time_minutes: Decimal = Decimal("0")
    median_response_time_minutes: Decimal = Decimal("0")
    median_resolution_time_minutes: Decimal = Decimal("0")

    # Par priorité
    stats_by_priority: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Par target
    stats_by_target: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Pénalités
    total_penalties: Decimal = Decimal("0")
    total_bonuses: Decimal = Decimal("0")

    # Escalades
    total_escalations: int = 0
    escalations_by_level: Dict[str, int] = field(default_factory=dict)

    # Tendances
    daily_compliance: List[Dict[str, Any]] = field(default_factory=list)


# ============== Service Principal ==============

class SLAService:
    """Service de gestion des SLAs."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._business_hours: Dict[str, BusinessHours] = {}
        self._policies: Dict[str, SLAPolicy] = {}
        self._targets: Dict[str, SLATarget] = {}
        self._escalation_rules: Dict[str, EscalationRule] = {}
        self._instances: Dict[str, SLAInstance] = {}
        self._events: Dict[str, SLAEvent] = {}
        self._breaches: Dict[str, SLABreach] = {}

    # ===== Heures ouvrées =====

    def create_business_hours(
        self,
        name: str,
        *,
        hours_type: BusinessHoursType = BusinessHoursType.BUSINESS,
        working_days: Optional[List[int]] = None,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        timezone: str = "Europe/Paris",
        is_default: bool = False
    ) -> BusinessHours:
        """Créer une définition d'heures ouvrées."""
        hours_id = str(uuid.uuid4())

        # Si 24/7
        if hours_type == BusinessHoursType.CALENDAR:
            working_days = [0, 1, 2, 3, 4, 5, 6]
            start_time = time(0, 0)
            end_time = time(23, 59)

        hours = BusinessHours(
            id=hours_id,
            tenant_id=self.tenant_id,
            name=name,
            hours_type=hours_type,
            working_days=working_days if working_days is not None else [0, 1, 2, 3, 4],
            start_time=start_time or time(9, 0),
            end_time=end_time or time(18, 0),
            timezone=timezone,
            is_default=is_default
        )

        # Désactiver l'ancien défaut si nouveau défaut
        if is_default:
            for bh in self._business_hours.values():
                if bh.tenant_id == self.tenant_id and bh.is_default:
                    bh.is_default = False

        self._business_hours[hours_id] = hours
        return hours

    def add_holiday(
        self,
        business_hours_id: str,
        holiday_date: date
    ) -> Optional[BusinessHours]:
        """Ajouter un jour férié."""
        hours = self._business_hours.get(business_hours_id)
        if not hours or hours.tenant_id != self.tenant_id:
            return None

        if holiday_date not in hours.holidays:
            hours.holidays.append(holiday_date)

        return hours

    # ===== Politiques SLA =====

    def create_policy(
        self,
        name: str,
        code: str,
        description: str = "",
        *,
        applies_to_entity_type: str = "ticket",
        business_hours_id: Optional[str] = None,
        use_business_hours: bool = True,
        escalation_enabled: bool = True,
        penalty_enabled: bool = False,
        penalty_percent_per_breach: Decimal = Decimal("0")
    ) -> SLAPolicy:
        """Créer une politique SLA."""
        policy_id = str(uuid.uuid4())

        policy = SLAPolicy(
            id=policy_id,
            tenant_id=self.tenant_id,
            name=name,
            code=code,
            description=description,
            applies_to_entity_type=applies_to_entity_type,
            business_hours_id=business_hours_id,
            use_business_hours=use_business_hours,
            escalation_enabled=escalation_enabled,
            penalty_enabled=penalty_enabled,
            penalty_percent_per_breach=penalty_percent_per_breach
        )

        self._policies[policy_id] = policy
        return policy

    def add_target(
        self,
        policy_id: str,
        name: str,
        sla_type: SLAType,
        target_value: Decimal,
        metric_unit: MetricUnit,
        *,
        description: str = "",
        priority: Optional[SLAPriority] = None,
        warning_threshold_percent: Decimal = Decimal("80"),
        weight: Decimal = Decimal("1")
    ) -> Optional[SLATarget]:
        """Ajouter un objectif à une politique."""
        policy = self._policies.get(policy_id)
        if not policy or policy.tenant_id != self.tenant_id:
            return None

        target_id = str(uuid.uuid4())

        target = SLATarget(
            id=target_id,
            sla_id=policy_id,
            name=name,
            description=description,
            sla_type=sla_type,
            metric_unit=metric_unit,
            target_value=target_value,
            priority=priority,
            warning_threshold_percent=warning_threshold_percent,
            weight=weight
        )

        policy.targets.append(target)
        self._targets[target_id] = target
        return target

    def add_escalation_rule(
        self,
        policy_id: str,
        level: EscalationLevel,
        trigger_percent: Decimal,
        *,
        notify_user_ids: Optional[List[str]] = None,
        notify_roles: Optional[List[str]] = None,
        auto_reassign: bool = False,
        reassign_to_user_id: str = "",
        priority_boost: bool = False,
        new_priority: Optional[SLAPriority] = None
    ) -> Optional[EscalationRule]:
        """Ajouter une règle d'escalade."""
        policy = self._policies.get(policy_id)
        if not policy or policy.tenant_id != self.tenant_id:
            return None

        rule_id = str(uuid.uuid4())

        rule = EscalationRule(
            id=rule_id,
            tenant_id=self.tenant_id,
            sla_policy_id=policy_id,
            level=level,
            trigger_percent=trigger_percent,
            notify_user_ids=notify_user_ids or [],
            notify_roles=notify_roles or [],
            auto_reassign=auto_reassign,
            reassign_to_user_id=reassign_to_user_id,
            priority_boost=priority_boost,
            new_priority=new_priority
        )

        self._escalation_rules[rule_id] = rule
        return rule

    def get_policy(self, policy_id: str) -> Optional[SLAPolicy]:
        """Récupérer une politique."""
        policy = self._policies.get(policy_id)
        if policy and policy.tenant_id == self.tenant_id:
            return policy
        return None

    def list_policies(self, entity_type: Optional[str] = None) -> List[SLAPolicy]:
        """Lister les politiques."""
        policies = [
            p for p in self._policies.values()
            if p.tenant_id == self.tenant_id and p.is_active
        ]

        if entity_type:
            policies = [p for p in policies if p.applies_to_entity_type == entity_type]

        return sorted(policies, key=lambda x: x.name)

    # ===== Instances SLA =====

    def start_sla(
        self,
        policy_id: str,
        entity_type: str,
        entity_id: str,
        priority: SLAPriority = SLAPriority.MEDIUM
    ) -> Optional[SLAInstance]:
        """Démarrer un SLA pour une entité."""
        policy = self._policies.get(policy_id)
        if not policy or policy.tenant_id != self.tenant_id:
            return None

        instance_id = str(uuid.uuid4())
        now = datetime.utcnow()

        instance = SLAInstance(
            id=instance_id,
            tenant_id=self.tenant_id,
            sla_policy_id=policy_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=SLAStatus.ACTIVE,
            priority=priority,
            started_at=now
        )

        # Calculer les échéances
        response_target = self._get_target_for_priority(policy, SLAType.RESPONSE_TIME, priority)
        resolution_target = self._get_target_for_priority(policy, SLAType.RESOLUTION_TIME, priority)

        if response_target:
            instance.response_due_at = self._calculate_due_date(
                now, response_target.target_value, response_target.metric_unit,
                policy.business_hours_id if policy.use_business_hours else None
            )

        if resolution_target:
            instance.resolution_due_at = self._calculate_due_date(
                now, resolution_target.target_value, resolution_target.metric_unit,
                policy.business_hours_id if policy.use_business_hours else None
            )

        self._instances[instance_id] = instance

        # Enregistrer événement
        self._log_event(instance_id, "started", {"priority": priority.value})

        return instance

    def record_first_response(
        self,
        instance_id: str,
        user_id: str = ""
    ) -> Optional[SLAInstance]:
        """Enregistrer la première réponse."""
        instance = self._instances.get(instance_id)
        if not instance or instance.tenant_id != self.tenant_id:
            return None

        if instance.first_response_at:
            return instance  # Déjà enregistré

        now = datetime.utcnow()
        instance.first_response_at = now

        # Calculer temps de réponse
        elapsed = self._calculate_elapsed_minutes(
            instance.started_at,
            now,
            instance.sla_policy_id,
            instance.total_paused_duration_minutes
        )
        instance.response_time_minutes = elapsed

        # Vérifier breach
        if instance.response_due_at and now > instance.response_due_at:
            instance.response_breached = True
            instance.breach_count += 1
            if not instance.first_breach_at:
                instance.first_breach_at = now
            self._record_breach(instance, "response")

        instance.updated_at = now
        self._log_event(instance_id, "responded", {
            "response_time_minutes": elapsed,
            "breached": instance.response_breached,
            "user_id": user_id
        })

        return instance

    def record_resolution(
        self,
        instance_id: str,
        user_id: str = "",
        notes: str = ""
    ) -> Optional[SLAInstance]:
        """Enregistrer la résolution."""
        instance = self._instances.get(instance_id)
        if not instance or instance.tenant_id != self.tenant_id:
            return None

        now = datetime.utcnow()
        instance.resolved_at = now

        # Calculer temps de résolution
        elapsed = self._calculate_elapsed_minutes(
            instance.started_at,
            now,
            instance.sla_policy_id,
            instance.total_paused_duration_minutes
        )
        instance.resolution_time_minutes = elapsed

        # Vérifier breach
        if instance.resolution_due_at and now > instance.resolution_due_at:
            instance.resolution_breached = True
            instance.breach_count += 1
            if not instance.first_breach_at:
                instance.first_breach_at = now
            self._record_breach(instance, "resolution")

        # Statut final
        if instance.response_breached or instance.resolution_breached:
            instance.status = SLAStatus.BREACHED
        else:
            instance.status = SLAStatus.MET

        # Calculer score de conformité
        instance.compliance_score = self._calculate_compliance_score(instance)

        instance.updated_at = now
        self._log_event(instance_id, "resolved", {
            "resolution_time_minutes": elapsed,
            "breached": instance.resolution_breached,
            "user_id": user_id,
            "notes": notes
        })

        return instance

    def pause_sla(
        self,
        instance_id: str,
        reason: str = ""
    ) -> Optional[SLAInstance]:
        """Mettre en pause le SLA."""
        instance = self._instances.get(instance_id)
        if not instance or instance.tenant_id != self.tenant_id:
            return None

        if instance.status != SLAStatus.ACTIVE:
            return None

        if instance.paused_at:
            return instance  # Déjà en pause

        now = datetime.utcnow()
        instance.paused_at = now
        instance.pause_reason = reason
        instance.status = SLAStatus.PAUSED
        instance.updated_at = now

        self._log_event(instance_id, "paused", {"reason": reason})

        return instance

    def resume_sla(
        self,
        instance_id: str
    ) -> Optional[SLAInstance]:
        """Reprendre le SLA."""
        instance = self._instances.get(instance_id)
        if not instance or instance.tenant_id != self.tenant_id:
            return None

        if not instance.paused_at:
            return instance  # Pas en pause

        now = datetime.utcnow()

        # Calculer durée de pause
        pause_duration = int((now - instance.paused_at).total_seconds() / 60)
        instance.total_paused_duration_minutes += pause_duration

        # Ajuster les échéances
        if instance.response_due_at and not instance.first_response_at:
            instance.response_due_at += timedelta(minutes=pause_duration)

        if instance.resolution_due_at and not instance.resolved_at:
            instance.resolution_due_at += timedelta(minutes=pause_duration)

        instance.paused_at = None
        instance.pause_reason = ""
        instance.status = SLAStatus.ACTIVE
        instance.updated_at = now

        self._log_event(instance_id, "resumed", {"paused_duration_minutes": pause_duration})

        return instance

    def escalate(
        self,
        instance_id: str,
        level: EscalationLevel,
        reason: str = ""
    ) -> Optional[SLAInstance]:
        """Escalader manuellement."""
        instance = self._instances.get(instance_id)
        if not instance or instance.tenant_id != self.tenant_id:
            return None

        now = datetime.utcnow()

        escalation_entry = {
            "level": level.value,
            "timestamp": now.isoformat(),
            "reason": reason,
            "manual": True
        }

        instance.escalation_history.append(escalation_entry)
        instance.current_escalation_level = level
        instance.updated_at = now

        self._log_event(instance_id, "escalated", escalation_entry)

        # Exécuter les actions d'escalade
        self._execute_escalation_actions(instance, level)

        return instance

    def check_escalations(self) -> List[SLAInstance]:
        """Vérifier et appliquer les escalades automatiques."""
        escalated = []
        now = datetime.utcnow()

        for instance in self._instances.values():
            if instance.tenant_id != self.tenant_id:
                continue

            if instance.status != SLAStatus.ACTIVE:
                continue

            policy = self._policies.get(instance.sla_policy_id)
            if not policy or not policy.escalation_enabled or not policy.auto_escalate:
                continue

            # Récupérer les règles d'escalade
            rules = sorted(
                [r for r in self._escalation_rules.values()
                 if r.sla_policy_id == policy.id and r.is_active],
                key=lambda x: x.sort_order
            )

            for rule in rules:
                # Vérifier si déjà à ce niveau ou supérieur
                if instance.current_escalation_level:
                    current_level_order = list(EscalationLevel).index(instance.current_escalation_level)
                    rule_level_order = list(EscalationLevel).index(rule.level)
                    if current_level_order >= rule_level_order:
                        continue

                # Calculer pourcentage écoulé
                due_at = instance.resolution_due_at or instance.response_due_at
                if not due_at:
                    continue

                total_time = (due_at - instance.started_at).total_seconds()
                elapsed_time = (now - instance.started_at).total_seconds() - (instance.total_paused_duration_minutes * 60)

                if total_time > 0:
                    percent_elapsed = (elapsed_time / total_time) * 100

                    if percent_elapsed >= float(rule.trigger_percent):
                        self.escalate(instance.id, rule.level, f"Auto-escalade à {rule.trigger_percent}%")
                        escalated.append(instance)
                        break

        return escalated

    def get_instance(self, instance_id: str) -> Optional[SLAInstance]:
        """Récupérer une instance SLA."""
        instance = self._instances.get(instance_id)
        if instance and instance.tenant_id == self.tenant_id:
            return instance
        return None

    def get_instance_by_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[SLAInstance]:
        """Récupérer l'instance SLA active d'une entité."""
        for instance in self._instances.values():
            if (instance.entity_type == entity_type and
                instance.entity_id == entity_id and
                instance.tenant_id == self.tenant_id and
                instance.status == SLAStatus.ACTIVE):
                return instance
        return None

    def list_active_instances(
        self,
        policy_id: Optional[str] = None,
        priority: Optional[SLAPriority] = None,
        at_risk: bool = False
    ) -> List[SLAInstance]:
        """Lister les instances actives."""
        instances = [
            i for i in self._instances.values()
            if i.tenant_id == self.tenant_id and i.status == SLAStatus.ACTIVE
        ]

        if policy_id:
            instances = [i for i in instances if i.sla_policy_id == policy_id]

        if priority:
            instances = [i for i in instances if i.priority == priority]

        if at_risk:
            now = datetime.utcnow()
            at_risk_instances = []
            for instance in instances:
                due_at = instance.resolution_due_at or instance.response_due_at
                if due_at:
                    remaining = (due_at - now).total_seconds()
                    total = (due_at - instance.started_at).total_seconds()
                    if total > 0 and remaining / total < 0.2:  # Moins de 20% restant
                        at_risk_instances.append(instance)
            instances = at_risk_instances

        return sorted(instances, key=lambda x: x.started_at)

    # ===== Helpers =====

    def _get_target_for_priority(
        self,
        policy: SLAPolicy,
        sla_type: SLAType,
        priority: SLAPriority
    ) -> Optional[SLATarget]:
        """Récupérer l'objectif pour une priorité."""
        # Chercher un objectif spécifique à la priorité
        for target in policy.targets:
            if target.sla_type == sla_type and target.priority == priority:
                return target

        # Sinon prendre l'objectif général
        for target in policy.targets:
            if target.sla_type == sla_type and target.priority is None:
                return target

        return None

    def _calculate_due_date(
        self,
        start: datetime,
        target_value: Decimal,
        unit: MetricUnit,
        business_hours_id: Optional[str]
    ) -> datetime:
        """Calculer la date d'échéance."""
        # Conversion en minutes
        if unit == MetricUnit.MINUTES:
            minutes = int(target_value)
        elif unit == MetricUnit.HOURS:
            minutes = int(target_value * 60)
        elif unit == MetricUnit.DAYS:
            minutes = int(target_value * 24 * 60)
        else:
            minutes = int(target_value * 60)

        # Si pas d'heures ouvrées, calcul simple
        if not business_hours_id:
            return start + timedelta(minutes=minutes)

        # Avec heures ouvrées
        hours = self._business_hours.get(business_hours_id)
        if not hours or hours.hours_type == BusinessHoursType.CALENDAR:
            return start + timedelta(minutes=minutes)

        # Calcul avec heures ouvrées
        return self._add_business_minutes(start, minutes, hours)

    def _add_business_minutes(
        self,
        start: datetime,
        minutes: int,
        hours: BusinessHours
    ) -> datetime:
        """Ajouter des minutes en heures ouvrées."""
        current = start
        remaining = minutes

        daily_minutes = (
            datetime.combine(date.today(), hours.end_time) -
            datetime.combine(date.today(), hours.start_time)
        ).total_seconds() / 60

        while remaining > 0:
            # Vérifier si jour ouvré
            if current.weekday() not in hours.working_days:
                current = datetime.combine(
                    current.date() + timedelta(days=1),
                    hours.start_time
                )
                continue

            if current.date() in hours.holidays:
                current = datetime.combine(
                    current.date() + timedelta(days=1),
                    hours.start_time
                )
                continue

            # Ajuster si avant début de journée
            if current.time() < hours.start_time:
                current = datetime.combine(current.date(), hours.start_time)

            # Ajuster si après fin de journée
            if current.time() >= hours.end_time:
                current = datetime.combine(
                    current.date() + timedelta(days=1),
                    hours.start_time
                )
                continue

            # Calculer minutes restantes dans la journée
            end_of_day = datetime.combine(current.date(), hours.end_time)
            minutes_left_today = int((end_of_day - current).total_seconds() / 60)

            if remaining <= minutes_left_today:
                return current + timedelta(minutes=remaining)
            else:
                remaining -= minutes_left_today
                current = datetime.combine(
                    current.date() + timedelta(days=1),
                    hours.start_time
                )

        return current

    def _calculate_elapsed_minutes(
        self,
        start: datetime,
        end: datetime,
        policy_id: str,
        paused_minutes: int
    ) -> int:
        """Calculer les minutes écoulées (avec heures ouvrées)."""
        policy = self._policies.get(policy_id)

        if not policy or not policy.use_business_hours or not policy.business_hours_id:
            return int((end - start).total_seconds() / 60) - paused_minutes

        hours = self._business_hours.get(policy.business_hours_id)
        if not hours or hours.hours_type == BusinessHoursType.CALENDAR:
            return int((end - start).total_seconds() / 60) - paused_minutes

        # Calcul en heures ouvrées
        total_minutes = 0
        current = start

        while current < end:
            if current.weekday() not in hours.working_days:
                current = datetime.combine(
                    current.date() + timedelta(days=1),
                    hours.start_time
                )
                continue

            if current.date() in hours.holidays:
                current = datetime.combine(
                    current.date() + timedelta(days=1),
                    hours.start_time
                )
                continue

            day_start = datetime.combine(current.date(), hours.start_time)
            day_end = datetime.combine(current.date(), hours.end_time)

            period_start = max(current, day_start)
            period_end = min(end, day_end)

            if period_start < period_end:
                total_minutes += int((period_end - period_start).total_seconds() / 60)

            current = datetime.combine(
                current.date() + timedelta(days=1),
                hours.start_time
            )

        return total_minutes - paused_minutes

    def _record_breach(self, instance: SLAInstance, breach_type: str) -> SLABreach:
        """Enregistrer une violation."""
        breach_id = str(uuid.uuid4())

        policy = self._policies.get(instance.sla_policy_id)
        target = self._get_target_for_priority(
            policy,
            SLAType.RESPONSE_TIME if breach_type == "response" else SLAType.RESOLUTION_TIME,
            instance.priority
        ) if policy else None

        actual_value = Decimal(str(
            instance.response_time_minutes if breach_type == "response"
            else instance.resolution_time_minutes or 0
        ))
        target_value = target.target_value if target else Decimal("0")

        breach = SLABreach(
            id=breach_id,
            tenant_id=self.tenant_id,
            sla_instance_id=instance.id,
            sla_policy_id=instance.sla_policy_id,
            target_id=target.id if target else "",
            breach_type=breach_type,
            target_value=target_value,
            actual_value=actual_value,
            exceeded_by=actual_value - target_value if target else actual_value
        )

        # Calculer pénalité si applicable
        if policy and policy.penalty_enabled:
            penalty = actual_value * policy.penalty_percent_per_breach / 100
            breach.penalty_amount = min(penalty, policy.max_penalty_percent)
            breach.penalty_applied = True

        self._breaches[breach_id] = breach
        return breach

    def _calculate_compliance_score(self, instance: SLAInstance) -> Decimal:
        """Calculer le score de conformité."""
        if not instance.response_breached and not instance.resolution_breached:
            return Decimal("100")

        policy = self._policies.get(instance.sla_policy_id)
        if not policy:
            return Decimal("0")

        total_weight = Decimal("0")
        weighted_score = Decimal("0")

        for target in policy.targets:
            if target.priority and target.priority != instance.priority:
                continue

            total_weight += target.weight

            if target.sla_type == SLAType.RESPONSE_TIME:
                if not instance.response_breached:
                    weighted_score += target.weight * 100
                else:
                    # Score partiel basé sur le dépassement
                    if instance.response_time_minutes:
                        ratio = float(target.target_value) / instance.response_time_minutes
                        weighted_score += target.weight * min(100, Decimal(str(ratio * 100)))

            elif target.sla_type == SLAType.RESOLUTION_TIME:
                if not instance.resolution_breached:
                    weighted_score += target.weight * 100
                else:
                    if instance.resolution_time_minutes:
                        ratio = float(target.target_value) / instance.resolution_time_minutes
                        weighted_score += target.weight * min(100, Decimal(str(ratio * 100)))

        if total_weight > 0:
            return (weighted_score / total_weight).quantize(Decimal("0.01"))

        return Decimal("0")

    def _execute_escalation_actions(
        self,
        instance: SLAInstance,
        level: EscalationLevel
    ) -> None:
        """Exécuter les actions d'escalade."""
        rules = [
            r for r in self._escalation_rules.values()
            if r.sla_policy_id == instance.sla_policy_id and r.level == level
        ]

        for rule in rules:
            # Actions de notification simulées
            if rule.notify_user_ids:
                pass  # Envoyer notifications

            # Réassignation simulée
            if rule.auto_reassign and rule.reassign_to_user_id:
                pass  # Réassigner

            # Boost de priorité
            if rule.priority_boost and rule.new_priority:
                instance.priority = rule.new_priority

    def _log_event(
        self,
        instance_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> SLAEvent:
        """Enregistrer un événement."""
        event_id = str(uuid.uuid4())

        event = SLAEvent(
            id=event_id,
            tenant_id=self.tenant_id,
            sla_instance_id=instance_id,
            event_type=event_type,
            event_data=event_data
        )

        self._events[event_id] = event
        return event

    # ===== Rapports =====

    def generate_report(
        self,
        period_start: date,
        period_end: date,
        policy_id: Optional[str] = None
    ) -> SLAReport:
        """Générer un rapport SLA."""
        instances = [
            i for i in self._instances.values()
            if i.tenant_id == self.tenant_id and
               i.started_at.date() >= period_start and
               i.started_at.date() <= period_end
        ]

        if policy_id:
            instances = [i for i in instances if i.sla_policy_id == policy_id]

        # Métriques de base
        total = len(instances)
        active = len([i for i in instances if i.status == SLAStatus.ACTIVE])
        completed = len([i for i in instances if i.status in [SLAStatus.MET, SLAStatus.BREACHED]])
        met = len([i for i in instances if i.status == SLAStatus.MET])
        breached = len([i for i in instances if i.status == SLAStatus.BREACHED])

        compliance = (Decimal(met) / Decimal(completed) * 100) if completed > 0 else Decimal("0")

        # Temps moyens
        response_times = [i.response_time_minutes for i in instances if i.response_time_minutes]
        resolution_times = [i.resolution_time_minutes for i in instances if i.resolution_time_minutes]

        avg_response = Decimal(str(sum(response_times) / len(response_times))) if response_times else Decimal("0")
        avg_resolution = Decimal(str(sum(resolution_times) / len(resolution_times))) if resolution_times else Decimal("0")

        # Médiane
        def median(lst):
            if not lst:
                return 0
            sorted_lst = sorted(lst)
            n = len(sorted_lst)
            mid = n // 2
            return sorted_lst[mid] if n % 2 else (sorted_lst[mid - 1] + sorted_lst[mid]) / 2

        med_response = Decimal(str(median(response_times)))
        med_resolution = Decimal(str(median(resolution_times)))

        # Par priorité
        by_priority: Dict[str, Dict[str, Any]] = {}
        for priority in SLAPriority:
            priority_instances = [i for i in instances if i.priority == priority]
            if priority_instances:
                p_met = len([i for i in priority_instances if i.status == SLAStatus.MET])
                p_total = len([i for i in priority_instances if i.status in [SLAStatus.MET, SLAStatus.BREACHED]])
                by_priority[priority.value] = {
                    "total": len(priority_instances),
                    "compliance": (p_met / p_total * 100) if p_total > 0 else 0
                }

        # Pénalités
        breaches = [
            b for b in self._breaches.values()
            if b.tenant_id == self.tenant_id and
               any(i.id == b.sla_instance_id for i in instances)
        ]
        total_penalties = sum(b.penalty_amount for b in breaches)

        # Escalades
        total_escalations = sum(len(i.escalation_history) for i in instances)
        by_level: Dict[str, int] = {}
        for instance in instances:
            for esc in instance.escalation_history:
                level = esc.get("level", "")
                by_level[level] = by_level.get(level, 0) + 1

        return SLAReport(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end,
            sla_policy_id=policy_id,
            total_instances=total,
            active_instances=active,
            completed_instances=completed,
            met_instances=met,
            breached_instances=breached,
            compliance_rate=compliance,
            avg_response_time_minutes=avg_response,
            avg_resolution_time_minutes=avg_resolution,
            median_response_time_minutes=med_response,
            median_resolution_time_minutes=med_resolution,
            stats_by_priority=by_priority,
            total_penalties=total_penalties,
            total_escalations=total_escalations,
            escalations_by_level=by_level
        )


# ============== Factory ==============

def create_sla_service(tenant_id: str) -> SLAService:
    """Factory pour créer une instance du service."""
    return SLAService(tenant_id)
