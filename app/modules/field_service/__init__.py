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

Note: Les modèles SQLAlchemy doivent être importés directement depuis
app.modules.field_service.models pour éviter les conflits de registry.
"""

from .router import router
from .service import FieldServiceService

__all__ = [
    "FieldServiceService",
    "router"
]
