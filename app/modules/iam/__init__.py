"""
AZALS MODULE T0 - GESTION DES UTILISATEURS & RÔLES (IAM)
=========================================================

Module enterprise complet pour la gestion des identités et accès.

Fonctionnalités:
- Gestion des utilisateurs (CRUD, profils, activation)
- Gestion des rôles (hiérarchie, permissions)
- Permissions granulaires (module.ressource.action)
- Groupes utilisateurs
- Sessions et tokens
- Séparation des pouvoirs
- Audit trail complet
- Rate limiting
- MFA/2FA (TOTP)

Architecture:
- models.py : Modèles SQLAlchemy
- schemas.py : Schémas Pydantic
- service.py : Logique métier
- router.py : Endpoints API
- permissions.py : Définitions permissions
- decorators.py : Décorateurs sécurité

Version: 1.0.0
Auteur: AZALS Team
Date: 2026-01-03
"""

__version__ = "1.0.0"
__module_code__ = "T0"
__module_name__ = "IAM - Gestion Utilisateurs & Rôles"
