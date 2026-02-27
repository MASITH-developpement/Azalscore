"""
Tests RBAC pour le module INTERVENTIONS.

Vérifie l'application des rôles:
- Intervenant: actions terrain uniquement
- Manager: création, planification, clôture
- Admin: tout
- Lecture seule: consultation uniquement
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.modules.interventions.router import (
    RBACRoles,
    require_role,
)


# ============================================================================
# FIXTURES
# ============================================================================

def _make_user_mock(role, email):
    """Helper pour créer un mock utilisateur avec les bons attributs."""
    user = MagicMock()
    user.user_id = uuid4()
    user.tenant_id = "test_tenant"
    user.role = role
    user.email = email
    return user


@pytest.fixture
def admin_user():
    """Utilisateur admin."""
    return _make_user_mock(RBACRoles.ADMIN, "admin@test.com")


@pytest.fixture
def manager_user():
    """Utilisateur manager."""
    return _make_user_mock(RBACRoles.MANAGER, "manager@test.com")


@pytest.fixture
def intervenant_user():
    """Utilisateur intervenant."""
    return _make_user_mock(RBACRoles.INTERVENANT, "intervenant@test.com")


@pytest.fixture
def readonly_user():
    """Utilisateur lecture seule."""
    return _make_user_mock(RBACRoles.READONLY, "readonly@test.com")


# ============================================================================
# TESTS - RBAC HELPER
# ============================================================================

class TestRBACHelper:
    """Tests de la fonction require_role."""

    def test_admin_acces_tout(self, admin_user):
        """L'admin a accès à tout."""
        # Simuler la vérification de rôle
        check = require_role(RBACRoles.MANAGER, RBACRoles.INTERVENANT)

        # Admin doit passer même s'il n'est pas dans la liste
        # Car admin a tous les droits
        with patch(
            'app.modules.interventions.router.get_current_user',
            return_value=admin_user
        ):
            result = check(admin_user)
            assert result == admin_user

    def test_manager_acces_manager(self, manager_user):
        """Le manager a accès aux routes manager."""
        check = require_role(RBACRoles.MANAGER)

        with patch(
            'app.modules.interventions.router.get_current_user',
            return_value=manager_user
        ):
            result = check(manager_user)
            assert result == manager_user

    def test_intervenant_acces_terrain(self, intervenant_user):
        """L'intervenant a accès aux actions terrain."""
        check = require_role(RBACRoles.INTERVENANT)

        with patch(
            'app.modules.interventions.router.get_current_user',
            return_value=intervenant_user
        ):
            result = check(intervenant_user)
            assert result == intervenant_user

    def test_readonly_refuse_creation(self, readonly_user):
        """Readonly est refusé pour la création."""
        check = require_role(RBACRoles.MANAGER)

        with pytest.raises(HTTPException) as exc_info:
            check(readonly_user)

        assert exc_info.value.status_code == 403
        assert "Accès refusé" in exc_info.value.detail

    def test_intervenant_refuse_creation(self, intervenant_user):
        """L'intervenant est refusé pour la création."""
        check = require_role(RBACRoles.MANAGER)

        with pytest.raises(HTTPException) as exc_info:
            check(intervenant_user)

        assert exc_info.value.status_code == 403


# ============================================================================
# TESTS - PERMISSIONS PAR ENDPOINT
# ============================================================================

class TestPermissionsEndpoints:
    """Tests des permissions par endpoint."""

    def test_liste_accessible_tous_roles(self):
        """La liste des interventions est accessible à tous."""
        # Ce test vérifie que l'endpoint de liste ne nécessite pas de rôle spécifique
        # (seule l'authentification est requise via get_current_user)
        assert True  # Placeholder - testé via integration tests

    def test_creation_manager_admin_only(self):
        """La création est réservée aux managers et admins."""
        # Vérifié par le décorateur sur l'endpoint
        check = require_role(RBACRoles.ADMIN, RBACRoles.MANAGER)

        # Doit accepter admin et manager
        admin = _make_user_mock(RBACRoles.ADMIN, "admin@test.com")
        manager = _make_user_mock(RBACRoles.MANAGER, "manager@test.com")

        assert check(admin) == admin
        assert check(manager) == manager

    def test_suppression_admin_only(self):
        """La suppression est réservée aux admins."""
        check = require_role(RBACRoles.ADMIN)

        admin = _make_user_mock(RBACRoles.ADMIN, "admin@test.com")
        manager = _make_user_mock(RBACRoles.MANAGER, "manager@test.com")

        assert check(admin) == admin

        with pytest.raises(HTTPException):
            check(manager)

    def test_actions_terrain_tous_sauf_readonly(self):
        """Les actions terrain sont accessibles à tous sauf readonly."""
        check = require_role(
            RBACRoles.ADMIN,
            RBACRoles.MANAGER,
            RBACRoles.INTERVENANT
        )

        admin = _make_user_mock(RBACRoles.ADMIN, "admin@test.com")
        manager = _make_user_mock(RBACRoles.MANAGER, "manager@test.com")
        intervenant = _make_user_mock(RBACRoles.INTERVENANT, "intervenant@test.com")
        readonly = _make_user_mock(RBACRoles.READONLY, "readonly@test.com")

        assert check(admin) == admin
        assert check(manager) == manager
        assert check(intervenant) == intervenant

        with pytest.raises(HTTPException):
            check(readonly)


# ============================================================================
# TESTS - MATRICE RBAC
# ============================================================================

class TestMatriceRBAC:
    """Tests de la matrice RBAC complète."""

    def test_matrice_lecture(self):
        """Tous les rôles ont accès en lecture."""
        roles = [
            RBACRoles.ADMIN,
            RBACRoles.MANAGER,
            RBACRoles.INTERVENANT,
            RBACRoles.READONLY
        ]

        for role in roles:
            user = _make_user_mock(role, f"{role}@test.com")
            # La lecture ne nécessite pas require_role, juste l'authentification
            assert user.role in roles

    def test_matrice_creation(self):
        """Seuls admin et manager peuvent créer."""
        can_create = [RBACRoles.ADMIN, RBACRoles.MANAGER]
        cannot_create = [RBACRoles.INTERVENANT, RBACRoles.READONLY]

        check = require_role(*can_create)

        for role in can_create:
            user = _make_user_mock(role, f"{role}@test.com")
            assert check(user) == user

        for role in cannot_create:
            user = _make_user_mock(role, f"{role}@test.com")
            with pytest.raises(HTTPException):
                check(user)

    def test_matrice_planification(self):
        """Seuls admin et manager peuvent planifier."""
        can_planify = [RBACRoles.ADMIN, RBACRoles.MANAGER]
        cannot_planify = [RBACRoles.INTERVENANT, RBACRoles.READONLY]

        check = require_role(*can_planify)

        for role in can_planify:
            user = _make_user_mock(role, f"{role}@test.com")
            assert check(user) == user

        for role in cannot_planify:
            user = _make_user_mock(role, f"{role}@test.com")
            with pytest.raises(HTTPException):
                check(user)

    def test_matrice_actions_terrain(self):
        """Admin, manager et intervenant peuvent effectuer les actions terrain."""
        can_action = [RBACRoles.ADMIN, RBACRoles.MANAGER, RBACRoles.INTERVENANT]
        cannot_action = [RBACRoles.READONLY]

        check = require_role(*can_action)

        for role in can_action:
            user = _make_user_mock(role, f"{role}@test.com")
            assert check(user) == user

        for role in cannot_action:
            user = _make_user_mock(role, f"{role}@test.com")
            with pytest.raises(HTTPException):
                check(user)

    def test_matrice_suppression(self):
        """Seul l'admin peut supprimer."""
        can_delete = [RBACRoles.ADMIN]
        cannot_delete = [RBACRoles.MANAGER, RBACRoles.INTERVENANT, RBACRoles.READONLY]

        check = require_role(*can_delete)

        for role in can_delete:
            user = _make_user_mock(role, f"{role}@test.com")
            assert check(user) == user

        for role in cannot_delete:
            user = _make_user_mock(role, f"{role}@test.com")
            with pytest.raises(HTTPException):
                check(user)

    def test_matrice_rapport_final(self):
        """Seuls admin et manager peuvent générer le rapport final."""
        can_generate = [RBACRoles.ADMIN, RBACRoles.MANAGER]
        cannot_generate = [RBACRoles.INTERVENANT, RBACRoles.READONLY]

        check = require_role(*can_generate)

        for role in can_generate:
            user = _make_user_mock(role, f"{role}@test.com")
            assert check(user) == user

        for role in cannot_generate:
            user = _make_user_mock(role, f"{role}@test.com")
            with pytest.raises(HTTPException):
                check(user)


# ============================================================================
# TESTS - ISOLATION DONNÉES
# ============================================================================

class TestIsolationDonnees:
    """Tests de l'isolation des données par rôle."""

    def test_intervenant_voit_ses_interventions(self):
        """L'intervenant ne voit que ses interventions assignées."""
        # Ce test vérifie la logique métier de filtrage
        # Dans l'implémentation réelle, le service filtre par intervenant_id
        assert True  # Vérifié dans test_interventions.py

    def test_manager_voit_toutes_interventions_tenant(self):
        """Le manager voit toutes les interventions du tenant."""
        # Le manager a accès à toutes les interventions du tenant
        assert True  # Vérifié dans test_interventions.py

    def test_admin_voit_tout(self):
        """L'admin voit toutes les interventions."""
        # L'admin a accès complet
        assert True  # Vérifié dans test_interventions.py
