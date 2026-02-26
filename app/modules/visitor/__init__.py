"""
Module Visitor Management - GAP-079

Gestion des visiteurs:
- Pré-enregistrement
- Check-in / Check-out
- Badges visiteurs
- Hôtes et notifications
- Accords de confidentialité
- Rapports de visite
- Intégration contrôle d'accès
"""

from .service import (
    # Énumérations
    VisitorType,
    VisitStatus,
    BadgeType,
    DocumentType,
    AccessLevel,

    # Data classes
    Location,
    Host,
    VisitorProfile,
    Visit,
    VisitorBadge,
    VisitGroup,
    WatchlistEntry,
    VisitorStats,

    # Service
    VisitorService,
    create_visitor_service,
)

__all__ = [
    "VisitorType",
    "VisitStatus",
    "BadgeType",
    "DocumentType",
    "AccessLevel",
    "Location",
    "Host",
    "VisitorProfile",
    "Visit",
    "VisitorBadge",
    "VisitGroup",
    "WatchlistEntry",
    "VisitorStats",
    "VisitorService",
    "create_visitor_service",
]
