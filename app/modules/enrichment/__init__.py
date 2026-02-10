"""
AZALS MODULE - Auto-Enrichment
==============================

Module d'auto-enrichissement des formulaires via APIs externes.

APIs gratuites supportees:
- SIRENE/INSEE: Lookup entreprises francaises (SIRET/SIREN)
- API Adresse gouv.fr: Autocomplete adresses francaises
- Open Food Facts: Produits alimentaires par code-barres
- Open Beauty Facts: Produits cosmetiques
- Open Pet Food Facts: Produits animaliers

APIs payantes (documentation future):
- Pappers: Donnees entreprises detaillees
- Google Places API
- Amazon Product Advertising API
"""

from .router import router as enrichment_router

__all__ = ["enrichment_router"]
