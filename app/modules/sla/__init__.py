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

from .service import (
    # Énumérations
    SLAType,
    SLAPriority,
    SLAStatus,
    EscalationLevel,
    MetricUnit,
    BusinessHoursType,

    # Data classes
    BusinessHours,
    SLATarget,
    SLAPolicy,
    EscalationRule,
    SLAInstance,
    SLAEvent,
    SLABreach,
    SLAReport,

    # Service
    SLAService,
    create_sla_service,
)

__all__ = [
    "SLAType",
    "SLAPriority",
    "SLAStatus",
    "EscalationLevel",
    "MetricUnit",
    "BusinessHoursType",
    "BusinessHours",
    "SLATarget",
    "SLAPolicy",
    "EscalationRule",
    "SLAInstance",
    "SLAEvent",
    "SLABreach",
    "SLAReport",
    "SLAService",
    "create_sla_service",
]
