"""
AZALS MODULE T0 - Décorateurs IAM
=================================

Décorateurs pour la vérification des permissions et rôles.
"""

from functools import wraps

from fastapi import HTTPException, status


def require_permission(permission_code: str):
    """
    Décorateur pour vérifier qu'un utilisateur a une permission.

    Supporte deux patterns:
    1. Legacy: current_user + service dans kwargs
    2. CORE SaaS: context (SaaSContext) dans kwargs

    Usage:
        @router.get("/protected")
        @require_permission("module.resource.action")
        async def protected_route(...):
            ...
    """
    # Roles admin qui bypassent les vérifications de permissions
    ADMIN_ROLES = {'SUPERADMIN', 'SUPER_ADMIN', 'DIRIGEANT', 'ADMIN'}

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # PATTERN 1: CORE SaaS avec SaaSContext
            context = kwargs.get('context')
            if context is not None:
                # Vérifier le rôle dans SaaSContext
                role = getattr(context, 'role', None)
                if role:
                    role_value = role.value if hasattr(role, 'value') else str(role)
                    if role_value in ADMIN_ROLES:
                        return await func(*args, **kwargs)

                # Vérifier les permissions dans SaaSContext
                permissions = getattr(context, 'permissions', set())
                if '*' in permissions or permission_code in permissions:
                    return await func(*args, **kwargs)

                # Vérifier les patterns de permissions (ex: "iam.*")
                module = permission_code.split('.')[0] if '.' in permission_code else permission_code
                if f"{module}.*" in permissions:
                    return await func(*args, **kwargs)

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_code}' requise"
                )

            # PATTERN 2: Legacy avec current_user + service
            service = kwargs.get('service')
            current_user = kwargs.get('current_user')

            if not service or not current_user:
                # Ni SaaSContext ni current_user - configuration invalide
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur configuration: context ou (service + current_user) requis"
                )

            # Bypass pour les rôles admin (vérifier role de la table users)
            user_role = getattr(current_user, 'role', None)
            if user_role:
                role_value = user_role.value if hasattr(user_role, 'value') else str(user_role)
                if role_value in ADMIN_ROLES:
                    return await func(*args, **kwargs)

            # Vérifier la permission via IAM
            granted, source = service.check_permission(current_user.id, permission_code)

            if not granted:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_code}' requise"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_codes: str | list[str]):
    """
    Décorateur pour vérifier qu'un utilisateur a un rôle.

    Usage:
        @router.get("/admin")
        @require_role("ADMIN")
        async def admin_route(...):
            ...

        @router.get("/manager")
        @require_role(["ADMIN", "MANAGER"])
        async def manager_route(...):
            ...
    """
    if isinstance(role_codes, str):
        role_codes = [role_codes]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            service = kwargs.get('service')
            current_user = kwargs.get('current_user')

            if not service or not current_user:
                # SECURITY FIX: Ne PAS bypasser
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur configuration: service et current_user requis pour vérification rôles"
                )

            # Récupérer l'utilisateur IAM
            user = service.get_user(current_user.id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Utilisateur non trouvé"
                )

            # Vérifier les rôles
            user_role_codes = [r.code for r in user.roles]
            if not any(code in user_role_codes for code in role_codes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Rôle requis: {', '.join(role_codes)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permission_codes: list[str]):
    """
    Décorateur pour vérifier qu'un utilisateur a AU MOINS UNE des permissions.

    Usage:
        @router.get("/data")
        @require_any_permission(["data.read", "data.admin"])
        async def data_route(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            service = kwargs.get('service')
            current_user = kwargs.get('current_user')

            if not service or not current_user:
                # SECURITY FIX: Ne PAS bypasser
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur configuration: service et current_user requis"
                )

            # Vérifier au moins une permission
            for code in permission_codes:
                granted, _ = service.check_permission(current_user.id, code)
                if granted:
                    return await func(*args, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"L'une des permissions requises: {', '.join(permission_codes)}"
            )
        return wrapper
    return decorator


def require_all_permissions(permission_codes: list[str]):
    """
    Décorateur pour vérifier qu'un utilisateur a TOUTES les permissions.

    Usage:
        @router.post("/critical")
        @require_all_permissions(["critical.read", "critical.write"])
        async def critical_route(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            service = kwargs.get('service')
            current_user = kwargs.get('current_user')

            if not service or not current_user:
                # SECURITY FIX: Ne PAS bypasser
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur configuration: service et current_user requis"
                )

            # Vérifier toutes les permissions
            missing = []
            for code in permission_codes:
                granted, _ = service.check_permission(current_user.id, code)
                if not granted:
                    missing.append(code)

            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissions manquantes: {', '.join(missing)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_self_or_permission(permission_code: str, user_id_param: str = "user_id"):
    """
    Décorateur pour autoriser l'accès si l'utilisateur est lui-même OU a la permission.
    Utile pour les profils utilisateurs.

    Usage:
        @router.get("/users/{user_id}")
        @require_self_or_permission("iam.user.read")
        async def get_user(user_id: int, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            service = kwargs.get('service')
            current_user = kwargs.get('current_user')
            target_user_id = kwargs.get(user_id_param)

            if not service or not current_user:
                # SECURITY FIX: Ne PAS bypasser
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur configuration: service et current_user requis"
                )

            # Autoriser si c'est l'utilisateur lui-même
            if target_user_id and current_user.id == target_user_id:
                return await func(*args, **kwargs)

            # Sinon vérifier la permission
            granted, _ = service.check_permission(current_user.id, permission_code)
            if not granted:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """
    Classe utilitaire pour vérifier les permissions dans le code.

    Usage:
        checker = PermissionChecker(service, user_id)
        if checker.has("module.action"):
            # faire quelque chose
    """

    def __init__(self, service, user_id: int):
        self.service = service
        self.user_id = user_id
        self._cache = {}

    def has(self, permission_code: str) -> bool:
        """Vérifie si l'utilisateur a une permission."""
        if permission_code not in self._cache:
            granted, _ = self.service.check_permission(self.user_id, permission_code)
            self._cache[permission_code] = granted
        return self._cache[permission_code]

    def has_any(self, permission_codes: list[str]) -> bool:
        """Vérifie si l'utilisateur a au moins une permission."""
        return any(self.has(code) for code in permission_codes)

    def has_all(self, permission_codes: list[str]) -> bool:
        """Vérifie si l'utilisateur a toutes les permissions."""
        return all(self.has(code) for code in permission_codes)

    def require(self, permission_code: str) -> None:
        """Lève une exception si l'utilisateur n'a pas la permission."""
        if not self.has(permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_code}' requise"
            )
