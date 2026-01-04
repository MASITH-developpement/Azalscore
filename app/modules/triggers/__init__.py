"""
AZALS MODULE T2 - SYSTÈME DE DÉCLENCHEURS & DIFFUSION
======================================================

Module pour la gestion des alertes, rapports périodiques et monitoring.

Fonctionnalités:
- Déclencheurs conditionnels (triggers)
- Alertes par seuil et condition
- Rapports périodiques automatiques
- Notifications multi-canal (email, webhook, in-app)
- Benchmark monitoring
- Escalade automatique
- Historique des événements
- Templates de messages

Architecture:
- models.py : Modèles SQLAlchemy
- schemas.py : Schémas Pydantic
- service.py : Logique métier
- router.py : Endpoints API
- engine.py : Moteur d'exécution des triggers
- channels.py : Canaux de diffusion

Version: 1.0.0
Auteur: AZALS Team
Date: 2026-01-03
"""

__version__ = "1.0.0"
__module_code__ = "T2"
__module_name__ = "Système de Déclencheurs & Diffusion"
