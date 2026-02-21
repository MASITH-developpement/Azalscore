"""
AZALS MODULE - Réseaux Sociaux & Marketing Digital
===================================================

Gestion des métriques des plateformes marketing :
- Google Analytics, Ads, Search Console, My Business
- Meta Business (Facebook, Instagram)
- LinkedIn
- Solocal (PagesJaunes)

Accessible via Administration > Réseaux Sociaux

Fonctionnalités:
- Saisie manuelle des métriques via formulaires
- Configuration des connexions OAuth/API
- Synchronisation automatique depuis les APIs
- Export vers Prometheus/Grafana
"""

from .router import router
from .service import SocialNetworksService
from .config_service import ConfigService
from .scheduler import scheduler, start_scheduler, stop_scheduler

__all__ = [
    "router",
    "SocialNetworksService",
    "ConfigService",
    "scheduler",
    "start_scheduler",
    "stop_scheduler",
]
