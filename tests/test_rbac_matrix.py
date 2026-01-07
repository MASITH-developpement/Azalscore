"""
AZALSCORE - Tests de Validation RBAC
=====================================

Tests automatisés pour valider la matrice RBAC selon les spécifications bêta.

Tests requis par module:
- Test accès autorisé
- Test accès refusé (403)
- Test URL directe
- Test modification ID
- Test API brute

Ces tests garantissent que la matrice RBAC est correctement implémentée.
"""

import pytest
from typing import List, Tuple

# Import direct depuis rbac_matrix pour éviter les dépendances SQLAlchemy
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.modules.iam.rbac_matrix import (
    StandardRole,
    Module,
    Action,
    Restriction,
    Permission,
    SecurityRules,
    RBAC_MATRIX,
    ROLE_HIERARCHY,
    check_permission,
    has_permission,
    get_all_permissions,
    get_allowed_actions,
    map_legacy_role_to_standard,
    validate_matrix_completeness,
    FULL,
    LIMITED,
    OWN,
    TEAM,
    DENY,
)


# ============================================================================
# TESTS DE LA MATRICE RBAC PRINCIPALE
# ============================================================================

class TestRBACMatrixStructure:
    """Tests de la structure de la matrice RBAC."""

    def test_matrix_completeness(self):
        """La matrice doit être complète (tous les rôles/modules définis)."""
        # Cette fonction lève une exception si incomplète
        assert validate_matrix_completeness() is True

    def test_all_roles_defined(self):
        """Tous les rôles standards doivent être dans la matrice."""
        for role in StandardRole:
            assert role in RBAC_MATRIX, f"Rôle {role.value} manquant dans la matrice"

    def test_all_modules_per_role(self):
        """Chaque rôle doit avoir des permissions pour tous les modules."""
        for role in StandardRole:
            for module in Module:
                assert module in RBAC_MATRIX[role], \
                    f"Module {module.value} manquant pour rôle {role.value}"

    def test_role_hierarchy_defined(self):
        """La hiérarchie des rôles doit être définie."""
        for role in StandardRole:
            assert role in ROLE_HIERARCHY, f"Hiérarchie non définie pour {role.value}"

    def test_role_hierarchy_order(self):
        """super_admin doit être au niveau 0 (plus élevé)."""
        assert ROLE_HIERARCHY[StandardRole.SUPER_ADMIN] == 0
        assert ROLE_HIERARCHY[StandardRole.ADMIN] == 1
        assert ROLE_HIERARCHY[StandardRole.MANAGER] == 2
        assert ROLE_HIERARCHY[StandardRole.USER] == 3
        assert ROLE_HIERARCHY[StandardRole.READONLY] == 4


# ============================================================================
# TESTS UTILISATEURS & RÔLES (Module USERS)
# ============================================================================

class TestUsersPermissions:
    """Tests des permissions sur le module Utilisateurs & Rôles."""

    # Test: super_admin a tous les accès
    @pytest.mark.parametrize("action", [
        Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE, Action.ASSIGN
    ])
    def test_super_admin_full_access(self, action):
        """super_admin doit avoir accès complet aux utilisateurs."""
        perm = check_permission(StandardRole.SUPER_ADMIN, Module.USERS, action)
        assert perm.allowed is True, f"super_admin devrait avoir {action.value}"

    # Test: admin a accès limité (pas de modification des rôles)
    def test_admin_can_read_users(self):
        """admin peut voir les utilisateurs."""
        assert has_permission(StandardRole.ADMIN, Module.USERS, Action.READ)

    def test_admin_can_create_users(self):
        """admin peut créer des utilisateurs."""
        assert has_permission(StandardRole.ADMIN, Module.USERS, Action.CREATE)

    def test_admin_can_update_users(self):
        """admin peut modifier des utilisateurs."""
        assert has_permission(StandardRole.ADMIN, Module.USERS, Action.UPDATE)

    def test_admin_cannot_assign_roles(self):
        """admin ne peut PAS modifier les rôles."""
        assert not has_permission(StandardRole.ADMIN, Module.USERS, Action.ASSIGN)

    def test_admin_delete_is_limited(self):
        """admin a une suppression limitée."""
        perm = check_permission(StandardRole.ADMIN, Module.USERS, Action.DELETE)
        assert perm.allowed is True
        assert perm.restriction == Restriction.LIMITED

    # Test: manager, user, readonly n'ont pas accès
    @pytest.mark.parametrize("role", [
        StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY
    ])
    @pytest.mark.parametrize("action", [
        Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE, Action.ASSIGN
    ])
    def test_lower_roles_no_user_access(self, role, action):
        """manager, user, readonly n'ont pas accès à la gestion des utilisateurs."""
        assert not has_permission(role, Module.USERS, action), \
            f"{role.value} ne devrait pas avoir {action.value} sur users"


# ============================================================================
# TESTS ORGANISATION (Module ORGANIZATION)
# ============================================================================

class TestOrganizationPermissions:
    """Tests des permissions sur le module Organisation."""

    def test_super_admin_full_access(self):
        """super_admin a accès complet à l'organisation."""
        assert has_permission(StandardRole.SUPER_ADMIN, Module.ORGANIZATION, Action.READ)
        assert has_permission(StandardRole.SUPER_ADMIN, Module.ORGANIZATION, Action.UPDATE)
        assert has_permission(StandardRole.SUPER_ADMIN, Module.ORGANIZATION, Action.ADMIN)

    def test_admin_can_read_and_update(self):
        """admin peut voir et modifier l'organisation."""
        assert has_permission(StandardRole.ADMIN, Module.ORGANIZATION, Action.READ)
        assert has_permission(StandardRole.ADMIN, Module.ORGANIZATION, Action.UPDATE)

    def test_admin_cannot_access_sensitive_settings(self):
        """admin ne peut pas accéder aux paramètres sensibles."""
        assert not has_permission(StandardRole.ADMIN, Module.ORGANIZATION, Action.ADMIN)

    @pytest.mark.parametrize("role", [
        StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY
    ])
    def test_all_can_read_organization(self, role):
        """Tous les rôles peuvent voir l'organisation."""
        assert has_permission(role, Module.ORGANIZATION, Action.READ)

    @pytest.mark.parametrize("role", [
        StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY
    ])
    def test_lower_roles_cannot_update_organization(self, role):
        """manager, user, readonly ne peuvent pas modifier l'organisation."""
        assert not has_permission(role, Module.ORGANIZATION, Action.UPDATE)


# ============================================================================
# TESTS CLIENTS / CONTACTS (Module CLIENTS)
# ============================================================================

class TestClientsPermissions:
    """Tests des permissions sur le module Clients/Contacts."""

    @pytest.mark.parametrize("role", [
        StandardRole.SUPER_ADMIN, StandardRole.ADMIN, StandardRole.MANAGER
    ])
    def test_high_roles_full_access(self, role):
        """super_admin, admin, manager ont accès complet aux clients."""
        assert has_permission(role, Module.CLIENTS, Action.READ)
        assert has_permission(role, Module.CLIENTS, Action.CREATE)
        assert has_permission(role, Module.CLIENTS, Action.UPDATE)

    def test_manager_cannot_delete_clients(self):
        """manager ne peut pas supprimer des clients."""
        assert not has_permission(StandardRole.MANAGER, Module.CLIENTS, Action.DELETE)

    def test_admin_can_delete_clients(self):
        """admin peut supprimer des clients."""
        assert has_permission(StandardRole.ADMIN, Module.CLIENTS, Action.DELETE)

    def test_user_limited_create(self):
        """user a une création limitée."""
        perm = check_permission(StandardRole.USER, Module.CLIENTS, Action.CREATE)
        assert perm.allowed is True
        assert perm.restriction == Restriction.LIMITED

    def test_user_own_data_update(self):
        """user ne peut modifier que ses propres données."""
        perm = check_permission(StandardRole.USER, Module.CLIENTS, Action.UPDATE)
        assert perm.allowed is True
        assert perm.restriction == Restriction.OWN_DATA

    def test_readonly_cannot_create_or_update(self):
        """readonly ne peut pas créer ou modifier des clients."""
        assert has_permission(StandardRole.READONLY, Module.CLIENTS, Action.READ)
        assert not has_permission(StandardRole.READONLY, Module.CLIENTS, Action.CREATE)
        assert not has_permission(StandardRole.READONLY, Module.CLIENTS, Action.UPDATE)
        assert not has_permission(StandardRole.READONLY, Module.CLIENTS, Action.DELETE)


# ============================================================================
# TESTS FACTURATION (Module BILLING)
# ============================================================================

class TestBillingPermissions:
    """Tests des permissions sur le module Facturation/Devis/Paiements."""

    def test_super_admin_full_access(self):
        """super_admin a accès complet à la facturation."""
        for action in [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE, Action.VALIDATE]:
            assert has_permission(StandardRole.SUPER_ADMIN, Module.BILLING, action)

    def test_admin_full_access_except_delete(self):
        """admin a accès complet sauf suppression limitée."""
        assert has_permission(StandardRole.ADMIN, Module.BILLING, Action.READ)
        assert has_permission(StandardRole.ADMIN, Module.BILLING, Action.CREATE)
        assert has_permission(StandardRole.ADMIN, Module.BILLING, Action.UPDATE)
        assert has_permission(StandardRole.ADMIN, Module.BILLING, Action.VALIDATE)
        # Suppression avec audit
        perm = check_permission(StandardRole.ADMIN, Module.BILLING, Action.DELETE)
        assert perm.restriction == Restriction.LIMITED

    def test_manager_limited_access(self):
        """manager peut voir et créer mais pas modifier/supprimer."""
        assert has_permission(StandardRole.MANAGER, Module.BILLING, Action.READ)
        assert has_permission(StandardRole.MANAGER, Module.BILLING, Action.CREATE)
        assert not has_permission(StandardRole.MANAGER, Module.BILLING, Action.UPDATE)
        assert not has_permission(StandardRole.MANAGER, Module.BILLING, Action.DELETE)

    def test_user_restricted_view(self):
        """user a une vue restreinte (ses données)."""
        perm = check_permission(StandardRole.USER, Module.BILLING, Action.READ)
        assert perm.allowed is True
        assert perm.restriction == Restriction.OWN_DATA

    def test_user_cannot_create_or_modify(self):
        """user ne peut pas créer ou modifier la facturation."""
        assert not has_permission(StandardRole.USER, Module.BILLING, Action.CREATE)
        assert not has_permission(StandardRole.USER, Module.BILLING, Action.UPDATE)
        assert not has_permission(StandardRole.USER, Module.BILLING, Action.DELETE)

    def test_readonly_can_only_read(self):
        """readonly peut seulement lire la facturation."""
        assert has_permission(StandardRole.READONLY, Module.BILLING, Action.READ)
        assert not has_permission(StandardRole.READONLY, Module.BILLING, Action.CREATE)
        assert not has_permission(StandardRole.READONLY, Module.BILLING, Action.UPDATE)
        assert not has_permission(StandardRole.READONLY, Module.BILLING, Action.DELETE)


# ============================================================================
# TESTS PROJETS (Module PROJECTS)
# ============================================================================

class TestProjectsPermissions:
    """Tests des permissions sur le module Projets/Activités."""

    @pytest.mark.parametrize("role", [StandardRole.SUPER_ADMIN, StandardRole.ADMIN])
    def test_admin_roles_full_access(self, role):
        """super_admin et admin ont accès complet aux projets."""
        for action in [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE]:
            assert has_permission(role, Module.PROJECTS, action)

    def test_manager_can_manage_but_not_delete(self):
        """manager peut gérer les projets mais pas supprimer."""
        assert has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.READ)
        assert has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.CREATE)
        assert has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.UPDATE)
        assert not has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.DELETE)

    def test_user_can_read_and_update_assigned(self):
        """user peut voir tous les projets et modifier ceux assignés."""
        assert has_permission(StandardRole.USER, Module.PROJECTS, Action.READ)
        perm = check_permission(StandardRole.USER, Module.PROJECTS, Action.UPDATE)
        assert perm.allowed is True
        assert perm.restriction == Restriction.OWN_DATA

    def test_user_cannot_create_or_delete(self):
        """user ne peut pas créer ou supprimer des projets."""
        assert not has_permission(StandardRole.USER, Module.PROJECTS, Action.CREATE)
        assert not has_permission(StandardRole.USER, Module.PROJECTS, Action.DELETE)

    def test_readonly_can_only_read(self):
        """readonly peut uniquement voir les projets."""
        assert has_permission(StandardRole.READONLY, Module.PROJECTS, Action.READ)
        assert not has_permission(StandardRole.READONLY, Module.PROJECTS, Action.CREATE)
        assert not has_permission(StandardRole.READONLY, Module.PROJECTS, Action.UPDATE)
        assert not has_permission(StandardRole.READONLY, Module.PROJECTS, Action.DELETE)


# ============================================================================
# TESTS REPORTING (Module REPORTING)
# ============================================================================

class TestReportingPermissions:
    """Tests des permissions sur le module Reporting/KPI."""

    def test_super_admin_can_read_and_export(self):
        """super_admin peut voir et exporter les rapports."""
        assert has_permission(StandardRole.SUPER_ADMIN, Module.REPORTING, Action.READ)
        assert has_permission(StandardRole.SUPER_ADMIN, Module.REPORTING, Action.EXPORT)

    def test_admin_cannot_export(self):
        """admin peut voir mais pas exporter."""
        assert has_permission(StandardRole.ADMIN, Module.REPORTING, Action.READ)
        assert not has_permission(StandardRole.ADMIN, Module.REPORTING, Action.EXPORT)

    def test_manager_team_data_only(self):
        """manager voit uniquement les données de son équipe."""
        perm = check_permission(StandardRole.MANAGER, Module.REPORTING, Action.READ)
        assert perm.allowed is True
        assert perm.restriction == Restriction.TEAM_DATA

    def test_user_personal_data_only(self):
        """user voit uniquement ses données personnelles."""
        perm = check_permission(StandardRole.USER, Module.REPORTING, Action.READ)
        assert perm.allowed is True
        assert perm.restriction == Restriction.OWN_DATA

    def test_readonly_limited_view(self):
        """readonly a une vue limitée des rapports."""
        perm = check_permission(StandardRole.READONLY, Module.REPORTING, Action.READ)
        assert perm.allowed is True
        assert perm.restriction == Restriction.LIMITED

    @pytest.mark.parametrize("role", [
        StandardRole.ADMIN, StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY
    ])
    def test_no_export_except_super_admin(self, role):
        """Seul super_admin peut exporter."""
        assert not has_permission(role, Module.REPORTING, Action.EXPORT)


# ============================================================================
# TESTS PARAMÈTRES (Module SETTINGS)
# ============================================================================

class TestSettingsPermissions:
    """Tests des permissions sur le module Paramètres/Configuration."""

    def test_super_admin_full_access(self):
        """super_admin peut voir et modifier les paramètres."""
        assert has_permission(StandardRole.SUPER_ADMIN, Module.SETTINGS, Action.READ)
        assert has_permission(StandardRole.SUPER_ADMIN, Module.SETTINGS, Action.UPDATE)

    def test_admin_can_read_only(self):
        """admin peut seulement voir les paramètres."""
        assert has_permission(StandardRole.ADMIN, Module.SETTINGS, Action.READ)
        assert not has_permission(StandardRole.ADMIN, Module.SETTINGS, Action.UPDATE)

    @pytest.mark.parametrize("role", [
        StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY
    ])
    def test_lower_roles_no_access(self, role):
        """manager, user, readonly n'ont pas accès aux paramètres."""
        assert not has_permission(role, Module.SETTINGS, Action.READ)
        assert not has_permission(role, Module.SETTINGS, Action.UPDATE)


# ============================================================================
# TESTS RÈGLES TRANSVERSALES DE SÉCURITÉ
# ============================================================================

class TestSecurityRules:
    """Tests des règles transversales de sécurité."""

    def test_only_super_admin_can_modify_roles(self):
        """Seul super_admin peut modifier les rôles."""
        assert SecurityRules.can_modify_roles(StandardRole.SUPER_ADMIN)
        assert not SecurityRules.can_modify_roles(StandardRole.ADMIN)
        assert not SecurityRules.can_modify_roles(StandardRole.MANAGER)
        assert not SecurityRules.can_modify_roles(StandardRole.USER)
        assert not SecurityRules.can_modify_roles(StandardRole.READONLY)

    def test_only_super_admin_can_modify_security(self):
        """Seul super_admin peut modifier la sécurité."""
        assert SecurityRules.can_modify_security(StandardRole.SUPER_ADMIN)
        assert not SecurityRules.can_modify_security(StandardRole.ADMIN)

    def test_only_super_admin_can_access_system_logs(self):
        """Seul super_admin peut accéder aux logs système."""
        assert SecurityRules.can_access_system_logs(StandardRole.SUPER_ADMIN)
        assert not SecurityRules.can_access_system_logs(StandardRole.ADMIN)

    def test_admin_cannot_modify_own_rights(self):
        """admin ne peut pas modifier ses propres droits."""
        # super_admin peut s'auto-modifier
        assert SecurityRules.can_modify_own_rights(StandardRole.SUPER_ADMIN, is_self=True)
        # admin ne peut pas s'auto-modifier
        assert not SecurityRules.can_modify_own_rights(StandardRole.ADMIN, is_self=True)

    def test_can_delete_user_hierarchy(self):
        """Test de la hiérarchie de suppression des utilisateurs."""
        # super_admin peut supprimer tout le monde
        assert SecurityRules.can_delete_user(StandardRole.SUPER_ADMIN, StandardRole.SUPER_ADMIN)
        assert SecurityRules.can_delete_user(StandardRole.SUPER_ADMIN, StandardRole.ADMIN)
        assert SecurityRules.can_delete_user(StandardRole.SUPER_ADMIN, StandardRole.USER)

        # admin ne peut pas supprimer super_admin
        assert not SecurityRules.can_delete_user(StandardRole.ADMIN, StandardRole.SUPER_ADMIN)
        # admin peut supprimer les autres
        assert SecurityRules.can_delete_user(StandardRole.ADMIN, StandardRole.MANAGER)
        assert SecurityRules.can_delete_user(StandardRole.ADMIN, StandardRole.USER)

        # autres ne peuvent pas supprimer
        assert not SecurityRules.can_delete_user(StandardRole.MANAGER, StandardRole.USER)
        assert not SecurityRules.can_delete_user(StandardRole.USER, StandardRole.READONLY)

    def test_role_hierarchy_comparison(self):
        """Test de la comparaison hiérarchique des rôles."""
        assert SecurityRules.is_role_higher_or_equal(StandardRole.SUPER_ADMIN, StandardRole.ADMIN)
        assert SecurityRules.is_role_higher_or_equal(StandardRole.ADMIN, StandardRole.MANAGER)
        assert SecurityRules.is_role_higher_or_equal(StandardRole.MANAGER, StandardRole.USER)
        assert SecurityRules.is_role_higher_or_equal(StandardRole.USER, StandardRole.READONLY)

        # Même niveau
        assert SecurityRules.is_role_higher_or_equal(StandardRole.ADMIN, StandardRole.ADMIN)

        # Inverse
        assert not SecurityRules.is_role_higher_or_equal(StandardRole.READONLY, StandardRole.USER)
        assert not SecurityRules.is_role_higher_or_equal(StandardRole.USER, StandardRole.ADMIN)


# ============================================================================
# TESTS SÉCURITÉ ET AUDIT (Modules SECURITY, AUDIT)
# ============================================================================

class TestSecurityAuditPermissions:
    """Tests des permissions sur les modules Sécurité et Audit."""

    def test_only_super_admin_has_security_access(self):
        """Seul super_admin a accès à la sécurité."""
        assert has_permission(StandardRole.SUPER_ADMIN, Module.SECURITY, Action.READ)
        assert has_permission(StandardRole.SUPER_ADMIN, Module.SECURITY, Action.UPDATE)
        assert has_permission(StandardRole.SUPER_ADMIN, Module.SECURITY, Action.ADMIN)

        for role in [StandardRole.ADMIN, StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY]:
            assert not has_permission(role, Module.SECURITY, Action.READ)
            assert not has_permission(role, Module.SECURITY, Action.UPDATE)
            assert not has_permission(role, Module.SECURITY, Action.ADMIN)

    def test_only_super_admin_has_audit_access(self):
        """Seul super_admin a accès aux logs d'audit."""
        assert has_permission(StandardRole.SUPER_ADMIN, Module.AUDIT, Action.READ)
        assert has_permission(StandardRole.SUPER_ADMIN, Module.AUDIT, Action.EXPORT)

        for role in [StandardRole.ADMIN, StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY]:
            assert not has_permission(role, Module.AUDIT, Action.READ)
            assert not has_permission(role, Module.AUDIT, Action.EXPORT)


# ============================================================================
# TESTS MAPPING RÔLES LEGACY
# ============================================================================

class TestLegacyRoleMapping:
    """Tests du mapping des rôles legacy vers les rôles standards."""

    def test_dirigeant_maps_to_admin(self):
        """DIRIGEANT doit mapper vers admin."""
        assert map_legacy_role_to_standard("DIRIGEANT") == StandardRole.ADMIN

    def test_admin_maps_to_admin(self):
        """ADMIN doit mapper vers admin."""
        assert map_legacy_role_to_standard("ADMIN") == StandardRole.ADMIN

    def test_daf_maps_to_manager(self):
        """DAF doit mapper vers manager."""
        assert map_legacy_role_to_standard("DAF") == StandardRole.MANAGER

    def test_comptable_maps_to_user(self):
        """COMPTABLE doit mapper vers user."""
        assert map_legacy_role_to_standard("COMPTABLE") == StandardRole.USER

    def test_employe_maps_to_readonly(self):
        """EMPLOYE doit mapper vers readonly."""
        assert map_legacy_role_to_standard("EMPLOYE") == StandardRole.READONLY

    def test_consultant_maps_to_readonly(self):
        """CONSULTANT doit mapper vers readonly."""
        assert map_legacy_role_to_standard("CONSULTANT") == StandardRole.READONLY

    def test_super_admin_maps_correctly(self):
        """SUPER_ADMIN doit mapper vers super_admin."""
        assert map_legacy_role_to_standard("SUPER_ADMIN") == StandardRole.SUPER_ADMIN

    def test_unknown_role_returns_none(self):
        """Un rôle inconnu doit retourner None."""
        assert map_legacy_role_to_standard("UNKNOWN_ROLE") is None
        assert map_legacy_role_to_standard(None) is None


# ============================================================================
# TESTS UTILITAIRES
# ============================================================================

class TestUtilityFunctions:
    """Tests des fonctions utilitaires."""

    def test_get_all_permissions(self):
        """get_all_permissions doit retourner un dict complet."""
        perms = get_all_permissions(StandardRole.ADMIN)
        assert isinstance(perms, dict)
        assert "users" in perms
        assert "read" in perms["users"]

    def test_get_allowed_actions(self):
        """get_allowed_actions doit retourner les actions autorisées."""
        actions = get_allowed_actions(StandardRole.ADMIN, Module.USERS)
        assert Action.READ in actions
        assert Action.CREATE in actions
        assert Action.UPDATE in actions
        assert Action.ASSIGN not in actions  # admin ne peut pas assigner de rôles

    def test_check_permission_deny_by_default(self):
        """check_permission doit refuser par défaut."""
        # Rôle inexistant
        perm = check_permission(None, Module.USERS, Action.READ)
        # Devrait être DENY
        assert perm.allowed is False


# ============================================================================
# TESTS D'INTÉGRATION - SCÉNARIOS COMPLETS
# ============================================================================

class TestIntegrationScenarios:
    """Tests d'intégration avec des scénarios réels."""

    def test_scenario_new_user_creation_by_admin(self):
        """Scénario: admin crée un nouvel utilisateur."""
        # admin peut créer
        assert has_permission(StandardRole.ADMIN, Module.USERS, Action.CREATE)
        # admin ne peut pas assigner de rôle
        assert not has_permission(StandardRole.ADMIN, Module.USERS, Action.ASSIGN)

    def test_scenario_manager_creates_project(self):
        """Scénario: manager crée et gère un projet."""
        assert has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.CREATE)
        assert has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.UPDATE)
        # Ne peut pas supprimer
        assert not has_permission(StandardRole.MANAGER, Module.PROJECTS, Action.DELETE)

    def test_scenario_user_views_billing(self):
        """Scénario: user consulte la facturation."""
        perm = check_permission(StandardRole.USER, Module.BILLING, Action.READ)
        # Peut voir mais restriction sur ses données
        assert perm.allowed is True
        assert perm.restriction == Restriction.OWN_DATA

    def test_scenario_readonly_exports_report(self):
        """Scénario: readonly tente d'exporter un rapport."""
        # Ne peut pas exporter
        assert not has_permission(StandardRole.READONLY, Module.REPORTING, Action.EXPORT)
        # Peut voir (limité)
        perm = check_permission(StandardRole.READONLY, Module.REPORTING, Action.READ)
        assert perm.allowed is True
        assert perm.restriction == Restriction.LIMITED

    def test_scenario_admin_modifies_own_role(self):
        """Scénario: admin tente de modifier son propre rôle."""
        # Règle transversale: admin ne peut pas modifier ses propres droits
        assert not SecurityRules.can_modify_own_rights(StandardRole.ADMIN, is_self=True)

    def test_scenario_escalation_attempt(self):
        """Scénario: user tente d'accéder à la gestion des utilisateurs."""
        # Toutes les actions sont refusées
        for action in Action:
            if action in [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE, Action.ASSIGN]:
                assert not has_permission(StandardRole.USER, Module.USERS, action)


# ============================================================================
# TESTS DE RÉGRESSION
# ============================================================================

class TestRegressionTests:
    """Tests de régression pour éviter les régressions futures."""

    def test_super_admin_always_has_full_access(self):
        """super_admin doit toujours avoir accès complet à tout."""
        # Actions de base que super_admin doit avoir sur tous les modules
        # Note: Certains modules n'ont pas toutes les actions (ex: pas de CREATE sur org)
        for module in Module:
            # READ doit toujours être disponible
            perm = check_permission(StandardRole.SUPER_ADMIN, module, Action.READ)
            assert perm.allowed is True, \
                f"super_admin devrait avoir read sur {module.value}"

        # Vérifier les modules avec CRUD complet
        crud_modules = [Module.USERS, Module.CLIENTS, Module.BILLING, Module.PROJECTS]
        for module in crud_modules:
            for action in [Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE]:
                perm = check_permission(StandardRole.SUPER_ADMIN, module, action)
                assert perm.allowed is True, \
                    f"super_admin devrait avoir {action.value} sur {module.value}"

    def test_readonly_never_has_write_access(self):
        """readonly ne doit jamais avoir d'accès en écriture."""
        for module in Module:
            for action in [Action.CREATE, Action.UPDATE, Action.DELETE]:
                assert not has_permission(StandardRole.READONLY, module, action), \
                    f"readonly ne devrait pas avoir {action.value} sur {module.value}"

    def test_security_rules_always_enforced(self):
        """Les règles de sécurité transversales doivent toujours être appliquées."""
        # Aucun rôle sauf super_admin ne peut modifier les rôles
        for role in [StandardRole.ADMIN, StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY]:
            assert not SecurityRules.can_modify_roles(role)

        # Aucun rôle sauf super_admin ne peut modifier la sécurité
        for role in [StandardRole.ADMIN, StandardRole.MANAGER, StandardRole.USER, StandardRole.READONLY]:
            assert not SecurityRules.can_modify_security(role)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
