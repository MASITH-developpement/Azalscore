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
- Optimisation des tournées (TSP/VRP) - GAP-002

Intégrations AZALS:
- M1 Commercial (clients)
- M3 RH (employés)
- M5 Stock (pièces)
- M8 Maintenance (équipements)
- M16 Helpdesk (tickets)

Note: Les modèles SQLAlchemy doivent être importés directement depuis
app.modules.field_service.models pour éviter les conflits de registry.
"""

from .router_crud import router
from .service import FieldServiceService
from .route_optimization import (
    RouteOptimizationService,
    TSPSolver,
    VRPSolver,
    OptimizationAlgorithm,
    Location,
    VehicleConstraints,
    OptimizedRoute,
    VRPSolution,
    haversine_distance,
    calculate_travel_time,
)

__all__ = [
    "FieldServiceService",
    "router",
    # Route Optimization (GAP-002)
    "RouteOptimizationService",
    "TSPSolver",
    "VRPSolver",
    "OptimizationAlgorithm",
    "Location",
    "VehicleConstraints",
    "OptimizedRoute",
    "VRPSolution",
    "haversine_distance",
    "calculate_travel_time",
]
