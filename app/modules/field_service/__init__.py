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

Note: Module currently disabled - files have .disabled extension.
"""

__all__ = []

# Module is currently disabled - imports are optional
try:
    from .router_crud import router
    __all__.append("router")
except ImportError:
    router = None

try:
    from .service import FieldServiceService
    __all__.append("FieldServiceService")
except ImportError:
    FieldServiceService = None

try:
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
    __all__.extend([
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
    ])
except ImportError:
    pass
