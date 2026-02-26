"""
AZALS MODULE T0 - Router API IAM
================================

Endpoints REST pour la gestion des identités et accès.

Architecture modulaire refactorisée depuis un fichier monolithique (2,029 lignes)
vers une structure avec séparation des responsabilités.

Structure:
- routers/auth.py: Authentification (login, refresh, logout)
- routers/users.py: Gestion des utilisateurs (CRUD, lock/unlock, password)
- routers/roles.py: Gestion des rôles (CRUD, assign, revoke)
- routers/permissions.py: Permissions et capabilities
- routers/groups.py: Gestion des groupes
- routers/mfa.py: Authentification multi-facteurs
- routers/invitations.py: Invitations utilisateurs
- routers/sessions.py: Gestion des sessions
- routers/policy.py: Politique de mot de passe
- capabilities.py: Définitions des capabilities par module

@module iam
"""
from .routers import create_iam_router

# Créer le router IAM avec tous les sous-routers
router = create_iam_router()

# Re-exports pour compatibilité
__all__ = ["router"]
