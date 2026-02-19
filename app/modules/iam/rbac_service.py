"""
AZALSCORE - Service RBAC Centralisé
====================================

Service centralisé pour la gestion du contrôle d'accès basé sur les rôles.
Implémente les vérifications de permissions avec deny-by-default.

PRINCIPE FONDAMENTAL: Deny by default
- Toute permission non explicitement accordée est refusée
- Chaque accès est vérifié contre la matrice RBAC
- Les refus critiques sont logués
"""

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import IAMAuditLog, IAMUser
from .rbac_matrix import (
    ROLE_HIERARCHY,
    Action,
    Module,
    Restriction,
    SecurityRules,
    StandardRole,
    check_permission,
    get_all_permissions,
    map_legacy_role_to_standard,
)

logger = logging.getLogger("rbac.service")


class RBACService:
    """
    Service centralisé pour le contrôle d'accès RBAC.

    Fonctionnalités:
    - Vérification des permissions avec deny-by-default
    - Gestion des restrictions (FULL, LIMITED, OWN_DATA, TEAM_DATA)
    - Application des règles transversales de sécurité
    - Logging des refus critiques
    - Isolation des données par tenant
    """

    def __init__(self, db: Session, tenant_id: str):
        """
        Initialise le service RBAC.

        Args:
            db: Session de base de données
            tenant_id: Identifiant du tenant (isolation obligatoire)
        """
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # VÉRIFICATION DES PERMISSIONS
    # =========================================================================

    def check_access(
        self,
        user: IAMUser,
        module: Module,
        action: Action,
        target_resource_id: int | None = None,
        target_owner_id: int | None = None,
    ) -> tuple[bool, Restriction, str]:
        """
        Vérifie si un utilisateur a accès à une action sur un module.

        Args:
            user: L'utilisateur effectuant l'action
            module: Le module concerné
            action: L'action à effectuer
            target_resource_id: ID de la ressource cible (optionnel)
            target_owner_id: ID du propriétaire de la ressource (pour OWN_DATA)

        Returns:
            Tuple (allowed: bool, restriction: Restriction, message: str)
        """
        # Obtenir le rôle standard
        user_role = self._get_standard_role(user)

        if not user_role:
            self._log_access_denied(
                user_id=user.id,
                module=module,
                action=action,
                reason="Rôle non défini"
            )
            return False, Restriction.NONE, "Rôle utilisateur non défini"

        # Vérifier dans la matrice RBAC
        permission = check_permission(user_role, module, action)

        if not permission.allowed:
            self._log_access_denied(
                user_id=user.id,
                module=module,
                action=action,
                reason="Permission refusée par matrice RBAC"
            )
            return False, Restriction.NONE, f"Accès refusé à {module.value}.{action.value}"

        # Vérifier les restrictions
        if permission.restriction == Restriction.OWN_DATA and target_owner_id and target_owner_id != user.id:
            self._log_access_denied(
                user_id=user.id,
                module=module,
                action=action,
                reason="Restriction OWN_DATA - Pas propriétaire"
            )
            return False, Restriction.NONE, "Vous ne pouvez accéder qu'à vos propres données"

        return True, permission.restriction, "Accès autorisé"

    def require_access(
        self,
        user: IAMUser,
        module: Module,
        action: Action,
        target_resource_id: int | None = None,
        target_owner_id: int | None = None,
    ) -> Restriction:
        """
        Exige l'accès ou lève une HTTPException 403.

        Returns:
            La restriction applicable si l'accès est autorisé

        Raises:
            HTTPException: 403 si l'accès est refusé
        """
        allowed, restriction, message = self.check_access(
            user, module, action, target_resource_id, target_owner_id
        )

        if not allowed:
            raise HTTPException(status_code=403, detail=message)

        return restriction

    # =========================================================================
    # RÈGLES TRANSVERSALES DE SÉCURITÉ
    # =========================================================================

    def can_modify_user_roles(self, actor: IAMUser) -> bool:
        """Vérifie si l'utilisateur peut modifier les rôles."""
        actor_role = self._get_standard_role(actor)
        return SecurityRules.can_modify_roles(actor_role) if actor_role else False

    def can_modify_security_settings(self, actor: IAMUser) -> bool:
        """Vérifie si l'utilisateur peut modifier les paramètres de sécurité."""
        actor_role = self._get_standard_role(actor)
        return SecurityRules.can_modify_security(actor_role) if actor_role else False

    def can_access_audit_logs(self, actor: IAMUser) -> bool:
        """Vérifie si l'utilisateur peut accéder aux logs d'audit système."""
        actor_role = self._get_standard_role(actor)
        return SecurityRules.can_access_system_logs(actor_role) if actor_role else False

    def can_delete_user(
        self,
        actor: IAMUser,
        target_user: IAMUser
    ) -> tuple[bool, str]:
        """
        Vérifie si un utilisateur peut supprimer un autre utilisateur.

        Returns:
            Tuple (allowed: bool, reason: str)
        """
        actor_role = self._get_standard_role(actor)
        target_role = self._get_standard_role(target_user)

        if not actor_role or not target_role:
            return False, "Rôles non définis"

        # Un utilisateur ne peut pas se supprimer lui-même
        if actor.id == target_user.id:
            return False, "Vous ne pouvez pas supprimer votre propre compte"

        # Vérifier selon les règles de sécurité
        if not SecurityRules.can_delete_user(actor_role, target_role):
            return False, f"Vous ne pouvez pas supprimer un utilisateur {target_role.value}"

        return True, "Suppression autorisée"

    def can_modify_own_rights(self, actor: IAMUser, target_user: IAMUser) -> bool:
        """Vérifie si un admin essaie de modifier ses propres droits."""
        is_self = actor.id == target_user.id
        actor_role = self._get_standard_role(actor)
        return SecurityRules.can_modify_own_rights(actor_role, is_self) if actor_role else False

    # =========================================================================
    # ISOLATION DES DONNÉES
    # =========================================================================

    def validate_tenant_isolation(self, resource_tenant_id: str) -> bool:
        """
        Vérifie que la ressource appartient au tenant actuel.
        CRITIQUE: Empêche tout accès cross-tenant.
        """
        if resource_tenant_id != self.tenant_id:
            logger.critical(
                "SECURITY VIOLATION: Tentative d'accès cross-tenant! "
                f"Current: {self.tenant_id}, Target: {resource_tenant_id}"
            )
            return False
        return True

    def require_tenant_isolation(self, resource_tenant_id: str):
        """
        Exige l'isolation tenant ou lève une HTTPException.

        Raises:
            HTTPException: 403 si violation d'isolation
        """
        if not self.validate_tenant_isolation(resource_tenant_id):
            raise HTTPException(
                status_code=403,
                detail="Accès interdit: ressource hors de votre organisation"
            )

    # =========================================================================
    # FILTRAGE DES DONNÉES PAR RESTRICTION
    # =========================================================================

    def apply_data_restriction(
        self,
        user: IAMUser,
        restriction: Restriction,
        data: list[dict[str, Any]],
        owner_field: str = "owner_id",
        team_field: str = "team_id"
    ) -> list[dict[str, Any]]:
        """
        Filtre les données selon la restriction de permission.

        Args:
            user: L'utilisateur
            restriction: La restriction à appliquer
            data: Les données à filtrer
            owner_field: Le champ identifiant le propriétaire
            team_field: Le champ identifiant l'équipe

        Returns:
            Les données filtrées
        """
        if restriction == Restriction.FULL:
            return data

        if restriction == Restriction.OWN_DATA:
            return [d for d in data if d.get(owner_field) == user.id]

        if restriction == Restriction.TEAM_DATA:
            user_teams = self._get_user_teams(user)
            return [d for d in data if d.get(team_field) in user_teams]

        if restriction == Restriction.LIMITED:
            # Appliquer une logique métier spécifique
            return self._apply_limited_filter(user, data)

        # NONE - aucune donnée
        return []

    def _get_user_teams(self, user: IAMUser) -> list[int]:
        """Récupère les IDs des équipes de l'utilisateur."""
        # NOTE: Phase 2 - Intégration table user_teams
        return []

    def _apply_limited_filter(
        self,
        user: IAMUser,
        data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Applique un filtre limité selon la logique métier."""
        # Par défaut, renvoie les données publiques ou celles de l'utilisateur
        return [
            d for d in data
            if d.get('is_public', False) or d.get('owner_id') == user.id
        ]

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _get_standard_role(self, user: IAMUser) -> StandardRole | None:
        """
        Récupère le rôle standard d'un utilisateur.
        Gère le mapping depuis les rôles legacy.
        """
        # Vérifier si l'utilisateur a un rôle standard directement
        if hasattr(user, 'standard_role') and user.standard_role:
            try:
                return StandardRole(user.standard_role)
            except ValueError as e:
                logger.warning(
                    "[RBAC_SVC] Rôle standard_role invalide, fallback legacy",
                    extra={"standard_role": user.standard_role, "error": str(e)[:200], "consequence": "fallback_legacy_mapping"}
                )

        # Mapper depuis le rôle legacy via les relations
        if user.roles:
            for role in user.roles:
                if role.code and role.code.lower() in [r.value for r in StandardRole]:
                    return StandardRole(role.code.lower())
                # Essayer le mapping
                standard = map_legacy_role_to_standard(role.code)
                if standard:
                    return standard

        return None

    def _log_access_denied(
        self,
        user_id: int,
        module: Module,
        action: Action,
        reason: str
    ):
        """Log un refus d'accès dans les logs d'audit."""
        logger.warning(
            "ACCESS DENIED: user_id=%s "
            "tenant=%s "
            "module=%s "
            "action=%s "
            "reason=%s",
            user_id, self.tenant_id, module.value, action.value, reason
        )

        # Enregistrer dans la base de données
        try:
            audit_log = IAMAuditLog(
                tenant_id=self.tenant_id,
                action=f"ACCESS_DENIED_{module.value}_{action.value}",
                entity_type="PERMISSION",
                entity_id=None,
                actor_id=user_id,
                details=reason,
                success=False,
                error_message=reason,
            )
            self.db.add(audit_log)
            self.db.commit()
        except Exception as e:
            logger.error("Erreur lors du log d'audit: %s", e)

    # =========================================================================
    # API PERMISSIONS
    # =========================================================================

    def get_user_permissions(self, user: IAMUser) -> dict[str, dict[str, bool]]:
        """
        Retourne toutes les permissions de l'utilisateur.
        Format: {module: {action: allowed}}
        """
        user_role = self._get_standard_role(user)
        if not user_role:
            return {}
        return get_all_permissions(user_role)

    def get_user_role_info(self, user: IAMUser) -> dict[str, Any]:
        """
        Retourne les informations sur le rôle de l'utilisateur.
        """
        user_role = self._get_standard_role(user)
        if not user_role:
            return {
                "role": None,
                "level": None,
                "permissions": {}
            }

        return {
            "role": user_role.value,
            "level": ROLE_HIERARCHY.get(user_role, 99),
            "permissions": get_all_permissions(user_role)
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_rbac_service(db: Session, tenant_id: str) -> RBACService:
    """Factory function pour créer un service RBAC."""
    return RBACService(db, tenant_id)


# ============================================================================
# DEPENDENCY INJECTION POUR FASTAPI
# ============================================================================

def get_rbac_dependency():
    """
    Dependency injection pour FastAPI.

    Usage:
        @app.get("/resource")
        async def get_resource(rbac: RBACService = Depends(get_rbac_dependency())):
            rbac.require_access(user, Module.CLIENTS, Action.READ)
    """
    from fastapi import Depends

    from app.core.database import get_db
    from app.core.dependencies import get_tenant_id

    def _get_rbac(
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ) -> RBACService:
        return RBACService(db, tenant_id)

    return _get_rbac
