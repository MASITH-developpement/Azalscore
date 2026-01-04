"""
AZALS MODULE T1 - CONFIGURATION AUTOMATIQUE PAR FONCTION
=========================================================

Module pour l'attribution automatique des droits selon le titre/fonction.

Fonctionnalités:
- Profils métier prédéfinis (CEO, CFO, DRH, etc.)
- Mapping automatique titre → rôles → permissions
- Sécurité par défaut (principe moindre privilège)
- Override dirigeant (ajustements stratégiques)
- Override RSI (ajustements techniques)
- Permissions temporaires avec expiration
- Onboarding automatisé
- Offboarding automatisé
- Audit trail complet

Architecture:
- models.py : Modèles SQLAlchemy
- schemas.py : Schémas Pydantic
- service.py : Logique métier
- router.py : Endpoints API
- profiles.py : Profils métier prédéfinis
- rules.py : Règles d'attribution

Version: 1.0.0
Auteur: AZALS Team
Date: 2026-01-03
"""

__version__ = "1.0.0"
__module_code__ = "T1"
__module_name__ = "Configuration Automatique par Fonction"
