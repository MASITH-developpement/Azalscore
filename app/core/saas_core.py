"""
CORE SaaS - Point d'entrée UNIQUE pour toutes les actions métier
=================================================================

Ce module centralise TOUTE la gouvernance SaaS :
- Authentification (tenant + user)
- Autorisation (permissions)
- Activation modules
- Audit trail
- Exécution métier

PRINCIPE CLÉ:
Tout passe par CORE.execute(action: str, context: SaaSContext) -> Result

Format action: "module.resource.verb"
Exemples:
- "commercial.customer.create"
- "invoicing.invoice.approve"
- "iam.user.delete"
"""
from __future__ import annotations


import json
import logging
import importlib
from datetime import datetime
from typing import Any, Dict, Optional, Set
from uuid import UUID

from fastapi import Depends
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import Result, SaaSContext, TenantScope, UserRole
from app.core.config import get_settings

# Importer les fonctions existantes de sécurité
from app.core.security import (
    ALGORITHM,
    get_password_hash,
    verify_password,
    create_access_token as security_create_access_token,
)

settings = get_settings()

# Importer les modèles existants
from app.core.models import CoreAuditJournal, User
from app.modules.tenants.models import ModuleStatus, Tenant, TenantModule

logger = logging.getLogger(__name__)


# ============================================================================
# PERMISSIONS PAR RÔLE (matrice RBAC simplifiée)
# ============================================================================

ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.SUPERADMIN: {"*"},  # Toutes les permissions (wildcard)

    UserRole.DIRIGEANT: {
        # Accès complet au tenant
        "commercial.*",
        "invoicing.*",
        "treasury.*",
        "accounting.*",
        "hr.*",
        "iam.*",
        "settings.*",
        "reports.*",
        # Modules métier complets
        "inventory.*",
        "production.*",
        "quality.*",
        "purchases.*",
        "projects.*",
    },

    UserRole.ADMIN: {
        # Administration système
        "iam.user.*",
        "iam.role.read",
        "settings.*",
        # Modules métier en lecture/écriture
        "commercial.*",
        "invoicing.*",
        "treasury.read",
        "accounting.read",
        "hr.read",
        "inventory.*",
        "production.*",
        "quality.*",
        "purchases.*",
    },

    UserRole.DAF: {
        # Finance complet
        "accounting.*",
        "treasury.*",
        "invoicing.*",
        "reports.financial.*",
        # Autres en lecture
        "commercial.read",
        "purchases.read",
        "inventory.read",
    },

    UserRole.COMPTABLE: {
        # Comptabilité
        "accounting.*",
        "invoicing.invoice.read",
        "invoicing.invoice.create",
        "invoicing.payment.read",
        "reports.accounting.*",
        # Lecture limitée
        "commercial.customer.read",
        "purchases.supplier.read",
    },

    UserRole.COMMERCIAL: {
        # Commercial complet
        "commercial.*",
        "invoicing.invoice.read",
        "invoicing.invoice.create",
        "invoicing.quote.*",
        "reports.sales.*",
        # Lecture clients/produits
        "inventory.product.read",
    },

    UserRole.EMPLOYE: {
        # Accès minimal
        "commercial.customer.read",
        "inventory.product.read",
        "projects.task.read",
        "hr.leave.create",
        "hr.timesheet.create",
    },
}


# ============================================================================
# CLASSE PRINCIPALE : SaaSCore
# ============================================================================

class SaaSCore:
    """
    Point d'entrée UNIQUE pour toute la gouvernance SaaS.

    Responsabilités:
    1. Authentification (authenticate)
    2. Autorisation (authorize)
    3. Vérification activation modules (is_module_active)
    4. Exécution métier centralisée (execute)
    5. Audit trail (audit)
    6. Gestion modules (activate_module, deactivate_module)
    """

    def __init__(self, db: Session):
        """
        Initialise le CORE SaaS.

        Args:
            db: Session SQLAlchemy pour accéder à la base
        """
        self.db = db

    # ========================================================================
    # AUTHENTIFICATION
    # ========================================================================

    def authenticate(
        self,
        token: str,
        tenant_id: str,
        ip_address: str = "",
        user_agent: str = "",
        correlation_id: str = "",
    ) -> Result:
        """
        Authentifie un utilisateur et crée un SaaSContext.

        Vérifie:
        1. Token JWT valide
        2. Utilisateur existe et actif
        3. Utilisateur appartient au tenant
        4. Tenant existe et actif

        Args:
            token: JWT token
            tenant_id: Tenant ID depuis header X-Tenant-ID
            ip_address: Adresse IP du client
            user_agent: User agent du client
            correlation_id: ID de corrélation pour traçabilité

        Returns:
            Result contenant SaaSContext si succès, erreur sinon
        """
        try:
            # Décoder JWT
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[ALGORITHM]
            )

            user_id_str: str = payload.get("sub")
            if not user_id_str:
                return Result.fail("Invalid token: missing user ID", "AUTH_INVALID_TOKEN")

            user_id = UUID(user_id_str)

        except JWTError as e:
            logger.warning("JWT decode error: %s", e)
            return Result.fail("Invalid or expired token", "AUTH_INVALID_TOKEN")

        # Récupérer utilisateur
        stmt = select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == 1
        )
        user = self.db.execute(stmt).scalar_one_or_none()

        if not user:
            return Result.fail(
                "User not found or not active",
                "AUTH_USER_NOT_FOUND"
            )

        # Vérifier tenant
        stmt = select(Tenant).where(Tenant.tenant_id == tenant_id)
        tenant = self.db.execute(stmt).scalar_one_or_none()

        if not tenant:
            return Result.fail("Tenant not found", "AUTH_TENANT_NOT_FOUND")

        if tenant.status != "ACTIVE":
            return Result.fail(
                f"Tenant is not active (status: {tenant.status})",
                "AUTH_TENANT_NOT_ACTIVE"
            )

        # Déterminer les permissions basées sur le rôle
        permissions = self._get_permissions_for_role(user.role)

        # Déterminer le scope
        scope = TenantScope.GLOBAL if user.role == UserRole.SUPERADMIN else TenantScope.TENANT

        # Créer SaaSContext
        context = SaaSContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=user.role,
            permissions=permissions,
            scope=scope,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
        )

        return Result.ok(context)

    def _get_permissions_for_role(self, role: UserRole) -> Set[str]:
        """
        Récupère les permissions pour un rôle donné.

        Args:
            role: Rôle utilisateur

        Returns:
            Set de permissions (format "module.resource.action")
        """
        return ROLE_PERMISSIONS.get(role, set())

    # ========================================================================
    # AUTORISATION
    # ========================================================================

    def authorize(self, context: SaaSContext, permission: str) -> bool:
        """
        Vérifie si le contexte a la permission demandée.

        Utilise la matrice RBAC + permissions dynamiques du contexte.

        Args:
            context: Contexte SaaS
            permission: Permission à vérifier (format "module.resource.action")

        Returns:
            True si autorisé, False sinon
        """
        # SUPERADMIN a toutes les permissions
        if context.is_creator:
            return True

        # Vérifier via la méthode has_permission du contexte
        return context.has_permission(permission)

    # ========================================================================
    # MODULES
    # ========================================================================

    def is_module_active(self, context: SaaSContext, module_code: str) -> bool:
        """
        Vérifie si un module est actif pour le tenant du contexte.

        Args:
            context: Contexte SaaS
            module_code: Code du module (ex: "commercial", "invoicing")

        Returns:
            True si module actif, False sinon
        """
        # SUPERADMIN peut accéder à tous les modules
        if context.is_creator and context.is_global_scope:
            return True

        # Vérifier activation du module pour le tenant
        stmt = select(TenantModule).where(
            TenantModule.tenant_id == context.tenant_id,
            TenantModule.module_code == module_code,
            TenantModule.status == ModuleStatus.ACTIVE
        )
        module = self.db.execute(stmt).scalar_one_or_none()

        return module is not None

    def activate_module(
        self,
        context: SaaSContext,
        module_code: str,
        module_name: str = "",
        module_version: str = "1.0.0",
        config: Optional[Dict] = None,
    ) -> Result:
        """
        Active un module pour le tenant.

        Nécessite permission "iam.module.activate" (typiquement DIRIGEANT ou ADMIN).

        Args:
            context: Contexte SaaS
            module_code: Code du module
            module_name: Nom du module (optionnel)
            module_version: Version du module
            config: Configuration du module (dict JSON)

        Returns:
            Result contenant le TenantModule créé si succès
        """
        # Vérifier permission
        if not self.authorize(context, "iam.module.activate"):
            return Result.fail(
                "Permission denied: iam.module.activate",
                "AUTH_PERMISSION_DENIED"
            )

        # Vérifier si module déjà actif
        if self.is_module_active(context, module_code):
            return Result.fail(
                f"Module {module_code} already active",
                "MODULE_ALREADY_ACTIVE"
            )

        # Créer entrée TenantModule
        tenant_module = TenantModule(
            tenant_id=context.tenant_id,
            module_code=module_code,
            module_name=module_name or module_code,
            module_version=module_version,
            status=ModuleStatus.ACTIVE,
            config=config or {},
            activated_at=datetime.utcnow(),
        )

        self.db.add(tenant_module)
        self.db.commit()
        self.db.refresh(tenant_module)

        # Audit
        self._audit(
            context,
            action=f"module.{module_code}.activate",
            details={"module_code": module_code}
        )

        logger.info(
            "Module %s activated for tenant %s "
            "by user %s",
            module_code, context.tenant_id, context.user_id
        )

        return Result.ok(tenant_module)

    def deactivate_module(self, context: SaaSContext, module_code: str) -> Result:
        """
        Désactive un module pour le tenant.

        Args:
            context: Contexte SaaS
            module_code: Code du module

        Returns:
            Result indiquant succès ou échec
        """
        # Vérifier permission
        if not self.authorize(context, "iam.module.deactivate"):
            return Result.fail(
                "Permission denied: iam.module.deactivate",
                "AUTH_PERMISSION_DENIED"
            )

        # Récupérer module
        stmt = select(TenantModule).where(
            TenantModule.tenant_id == context.tenant_id,
            TenantModule.module_code == module_code,
        )
        module = self.db.execute(stmt).scalar_one_or_none()

        if not module:
            return Result.fail(
                f"Module {module_code} not found",
                "MODULE_NOT_FOUND"
            )

        # Désactiver
        module.status = ModuleStatus.DISABLED
        module.deactivated_at = datetime.utcnow()

        self.db.commit()

        # Audit
        self._audit(
            context,
            action=f"module.{module_code}.deactivate",
            details={"module_code": module_code}
        )

        logger.info(
            "Module %s deactivated for tenant %s "
            "by user %s",
            module_code, context.tenant_id, context.user_id
        )

        return Result.ok({"module_code": module_code, "status": "DISABLED"})

    # ========================================================================
    # EXÉCUTION CENTRALISÉE
    # ========================================================================

    async def execute(
        self,
        action: str,
        context: SaaSContext,
        data: Any = None
    ) -> Result:
        """
        Point d'entrée UNIQUE pour toute action métier.

        Format action: "module.resource.verb"
        Exemples:
        - "commercial.customer.create"
        - "invoicing.invoice.approve"
        - "iam.user.delete"

        Workflow:
        1. Parser l'action (module.resource.verb)
        2. Vérifier module actif
        3. Vérifier permission
        4. Auditer l'action
        5. Charger et exécuter l'executor du module

        Args:
            action: Action à exécuter (format "module.resource.verb")
            context: Contexte SaaS
            data: Données de l'action (payload)

        Returns:
            Result contenant le résultat de l'exécution
        """
        # Parser action
        parts = action.split(".")
        if len(parts) != 3:
            return Result.fail(
                f"Invalid action format: {action}. Expected 'module.resource.verb'",
                "CORE_INVALID_ACTION_FORMAT"
            )

        module_code, resource, verb = parts

        # Vérifier module actif
        if not self.is_module_active(context, module_code):
            return Result.fail(
                f"Module {module_code} is not active for tenant {context.tenant_id}",
                "CORE_MODULE_NOT_ACTIVE"
            )

        # Construire permission requise
        permission = f"{module_code}.{resource}.{verb}"

        # Vérifier autorisation
        if not self.authorize(context, permission):
            return Result.fail(
                f"Permission denied: {permission}",
                "AUTH_PERMISSION_DENIED"
            )

        # Auditer AVANT exécution
        self._audit(context, action, details={"data": data})

        # Charger et exécuter l'executor du module
        try:
            executor = self._load_module_executor(module_code)
            result = await executor.execute(action, context, data)
            return result
        except Exception as e:
            logger.error(
                "Error executing action %s: %s", action, e,
                exc_info=True
            )
            return Result.fail(
                f"Execution error: {str(e)}",
                "CORE_EXECUTION_ERROR"
            )

    def _load_module_executor(self, module_code: str):
        """
        Charge dynamiquement l'executor d'un module.

        Convention: app.modules.{module_code}.executor.ModuleExecutor

        Args:
            module_code: Code du module

        Returns:
            Instance de l'executor du module

        Raises:
            ImportError: Si l'executor n'existe pas
        """
        try:
            # Import dynamique
            module_path = f"app.modules.{module_code}.executor"
            module = importlib.import_module(module_path)

            # Récupérer la classe ModuleExecutor
            executor_class = getattr(module, "ModuleExecutor")

            # Instancier avec db
            return executor_class(self.db)

        except (ImportError, AttributeError) as e:
            logger.error("Failed to load executor for module %s: %s", module_code, e)
            raise ImportError(
                f"Module executor not found: app.modules.{module_code}.executor.ModuleExecutor"
            )

    # ========================================================================
    # AUDIT
    # ========================================================================

    def _audit(
        self,
        context: SaaSContext,
        action: str,
        details: Optional[Dict] = None
    ) -> None:
        """
        Écrit une entrée dans le journal d'audit.

        Le journal est APPEND-ONLY (pas de UPDATE/DELETE).

        Args:
            context: Contexte SaaS
            action: Action auditée
            details: Détails supplémentaires (JSON)
        """
        try:
            audit_entry = CoreAuditJournal(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                action=action,
                details=json.dumps(details or {}),
            )

            self.db.add(audit_entry)
            self.db.commit()

        except Exception as e:
            logger.error("Failed to write audit entry: %s", e, exc_info=True)
            # Ne pas bloquer l'exécution si l'audit échoue
            # (mais logger l'erreur pour investigation)

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe avec bcrypt."""
        return get_password_hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe contre son hash."""
        return verify_password(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: UUID, expires_delta: Optional[int] = None) -> str:
        """
        Crée un JWT access token.

        Args:
            user_id: ID utilisateur
            expires_delta: Durée de validité en minutes (défaut: settings)

        Returns:
            JWT token encodé
        """
        from datetime import timedelta

        data = {"sub": str(user_id)}

        expires = None
        if expires_delta is not None:
            expires = timedelta(minutes=expires_delta)

        return security_create_access_token(data=data, expires_delta=expires)


# ============================================================================
# INSTANCE GLOBALE (pour usage simple)
# ============================================================================

def get_saas_core(db: Session = Depends(get_db)) -> SaaSCore:
    """
    Factory function pour obtenir une instance de SaaSCore.

    À utiliser avec FastAPI Depends.

    Args:
        db: Session SQLAlchemy (injectée via Depends)

    Returns:
        Instance de SaaSCore
    """
    return SaaSCore(db)
