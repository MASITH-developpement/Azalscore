"""
AZALS MODULE - Réseaux Sociaux & Marketing Digital
===================================================

Gestion complète du marketing digital :

1. MÉTRIQUES (Administration > Réseaux Sociaux)
   - Google Analytics, Ads, Search Console, My Business
   - Meta Business (Facebook, Instagram)
   - LinkedIn, Solocal (PagesJaunes)
   - Saisie manuelle et synchronisation API
   - Export vers Prometheus/Grafana

2. PUBLICATIONS & LEADS (Marketing > Publications)
   - Création de publications multi-plateformes
   - Programmation et calendrier éditorial
   - Templates réutilisables
   - Tracking UTM automatique
   - Génération et qualification de leads
   - Conversion en contacts/opportunités CRM
"""

# === Métriques (existant) ===
from .router import router as metrics_router
from .service import SocialNetworksService
from .config_service import ConfigService
from .scheduler import scheduler, start_scheduler, stop_scheduler

# === Publications & Leads (nouveau) ===
from .publication_router import router as publication_router
from .publication_service import PublicationService
from .publication_models import (
    SocialCampaign, SocialPost, SocialLead, PostTemplate, PublishingSlot,
    PostStatus, PostType, CampaignStatus, LeadStatus, LeadSource
)

# Alias pour compatibilité
router = metrics_router

__all__ = [
    # Métriques
    "router",
    "metrics_router",
    "SocialNetworksService",
    "ConfigService",
    "scheduler",
    "start_scheduler",
    "stop_scheduler",
    # Publications
    "publication_router",
    "PublicationService",
    "SocialCampaign",
    "SocialPost",
    "SocialLead",
    "PostTemplate",
    "PublishingSlot",
    "PostStatus",
    "PostType",
    "CampaignStatus",
    "LeadStatus",
    "LeadSource",
]
