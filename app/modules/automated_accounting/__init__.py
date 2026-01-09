"""
AZALS MODULE M2A - Comptabilité Automatisée
============================================

Module de comptabilité automatisée piloté par IA.

Objectif principal: Une facture reçue = la comptabilité se fait toute seule.

Principes clés:
- ZÉRO saisie comptable manuelle
- ZÉRO export par défaut
- ZÉRO dépendance aux emails pour travailler
- Automatisation maximale par IA
- L'humain valide par exception uniquement
- Banque en mode PULL (jamais PUSH)

Vues disponibles:
- Dirigeant: Piloter & décider (tableau de bord simplifié)
- Assistante: Centraliser & organiser documents (jamais comptabiliser)
- Expert-comptable: Contrôler, valider, certifier (exceptions uniquement)
"""

__version__ = "1.0.0"
__module_code__ = "M2A"
__module_name__ = "Comptabilité Automatisée"
__dependencies__ = ["T0", "T3", "T5", "M2"]  # IAM, Audit, Country Packs, Finance
