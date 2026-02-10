"""
AZALS MODULE - Auto-Enrichment - Providers
===========================================

Fournisseurs d'enrichissement pour APIs externes.
"""

from .base import BaseProvider, EnrichmentResult
from .insee import INSEEProvider
from .adresse import AdresseGouvProvider
from .openfoodfacts import OpenFoodFactsProvider, OpenBeautyFactsProvider, OpenPetFoodFactsProvider
from .pappers import PappersProvider
from .internal_scoring import InternalScoringProvider

__all__ = [
    "BaseProvider",
    "EnrichmentResult",
    "INSEEProvider",
    "AdresseGouvProvider",
    "OpenFoodFactsProvider",
    "OpenBeautyFactsProvider",
    "OpenPetFoodFactsProvider",
    "PappersProvider",
    "InternalScoringProvider",
]
