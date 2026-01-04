"""
AZALS MODULE 17 - Field Service
================================
Gestion des interventions terrain.

Fonctionnalités:
- Zones géographiques de service
- Techniciens et compétences
- Véhicules et GPS tracking
- Interventions et planification
- Suivi temps et déplacements
- Gestion des frais
- Contrats de service

Intégrations AZALS:
- M1 Commercial (clients)
- M3 RH (employés)
- M5 Stock (pièces)
- M8 Maintenance (équipements)
- M16 Helpdesk (tickets)
"""

from .models import (
    ServiceZone,
    Technician,
    Vehicle,
    InterventionTemplate,
    Intervention,
    InterventionHistory,
    TimeEntry,
    PartUsage,
    Route,
    Expense,
    ServiceContract,
    TechnicianStatus,
    InterventionStatus,
    InterventionPriority,
    InterventionType
)

from .service import FieldServiceService
from .router import router

__all__ = [
    # Models
    "ServiceZone",
    "Technician",
    "Vehicle",
    "InterventionTemplate",
    "Intervention",
    "InterventionHistory",
    "TimeEntry",
    "PartUsage",
    "Route",
    "Expense",
    "ServiceContract",
    # Enums
    "TechnicianStatus",
    "InterventionStatus",
    "InterventionPriority",
    "InterventionType",
    # Service & Router
    "FieldServiceService",
    "router"
]
