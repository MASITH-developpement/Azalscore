"""
AZALS MODULE M5 - STOCK (Inventaire + Logistique)
==================================================

Module complet de gestion des stocks et de la logistique.

Fonctionnalités:
- Gestion des entrepôts et emplacements
- Catalogue produits/articles
- Mouvements de stock (entrées, sorties, transferts)
- Inventaires physiques
- Suivi des lots et numéros de série
- Niveaux de stock et réapprovisionnement
- Valorisation des stocks
- Logistique et préparation de commandes

Dépendances:
- T0 (IAM) : Authentification et permissions
- T5 (Packs Pays) : Unités de mesure localisées
- M4 (Achats) : Réceptions de marchandises

Auteur: AZALS Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__module_code__ = "M5"
__module_name__ = "Stock - Inventaire & Logistique"
__dependencies__ = ["T0", "T5", "M4"]

# Constantes du module
DEFAULT_WAREHOUSE_CODE = "MAIN"
DEFAULT_LOCATION_CODE = "DEFAULT"

# Méthodes de valorisation
VALUATION_METHODS = ["FIFO", "LIFO", "AVG", "STANDARD"]

# Types d'unités
UNIT_TYPES = ["UNIT", "KG", "L", "M", "M2", "M3", "BOX", "PALLET", "PACK"]

# Priorités de réapprovisionnement
REPLENISHMENT_PRIORITIES = ["LOW", "NORMAL", "HIGH", "URGENT"]
