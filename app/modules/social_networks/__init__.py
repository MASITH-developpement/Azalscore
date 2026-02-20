"""
AZALS MODULE - Réseaux Sociaux & Marketing Digital
===================================================

Gestion des métriques des plateformes marketing :
- Google Analytics, Ads, Search Console, My Business
- Meta Business (Facebook, Instagram)
- LinkedIn
- Solocal (PagesJaunes)

Accessible via Administration > Réseaux Sociaux
"""

from .router import router
from .service import SocialNetworksService

__all__ = ["router", "SocialNetworksService"]
