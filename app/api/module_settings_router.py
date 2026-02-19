"""
AZALSCORE - Router Paramètres Modules
======================================

Endpoints REST pour la gestion des paramètres par module.
Permet à chaque tenant de configurer ses modules activés.

Endpoints:
- GET  /settings/modules                    - Liste des modules configurables
- GET  /settings/modules/{code}/schema      - Schéma des paramètres d'un module
- GET  /settings/modules/{code}             - Paramètres actuels d'un module
- PUT  /settings/modules/{code}             - Mise à jour des paramètres
- POST /settings/modules/{code}/reset       - Réinitialiser aux valeurs par défaut
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.module_settings_registry import (
    get_module_settings_schema,
    get_module_settings_defaults,
    get_all_module_settings,
    get_modules_with_settings,
    validate_module_settings,
    merge_with_defaults,
    SettingType,
    SettingCategory,
)
from app.modules.tenants.models import TenantModule, ModuleStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/settings/modules",
    tags=["Paramètres Modules"]
)


# =============================================================================
# SCHEMAS
# =============================================================================

class SettingOption(BaseModel):
    """Option pour un paramètre de type select."""
    value: str
    label: str


class SettingDefinition(BaseModel):
    """Définition d'un paramètre."""
    key: str
    label: str
    type: str
    default: Any = None
    category: str = "general"
    description: str | None = None
    placeholder: str | None = None
    options: list[SettingOption] | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    max_length: int | None = None
    multiline: bool = False
    depends_on: dict | None = None


class ModuleSettingsSchema(BaseModel):
    """Schéma des paramètres d'un module."""
    module_code: str
    module_name: str
    description: str | None = None
    settings: list[SettingDefinition]
    categories: list[dict]


class ModuleSettingsResponse(BaseModel):
    """Réponse avec les paramètres actuels."""
    module_code: str
    module_name: str
    is_active: bool
    settings: dict[str, Any]
    settings_schema: ModuleSettingsSchema | None = None


class ModuleSettingsUpdate(BaseModel):
    """Requête de mise à jour des paramètres."""
    settings: dict[str, Any] = Field(..., description="Paramètres à mettre à jour")


class ModuleSettingsListItem(BaseModel):
    """Item de la liste des modules configurables."""
    code: str
    name: str
    description: str | None = None
    is_active: bool
    has_custom_settings: bool
    settings_count: int


class ModuleSettingsListResponse(BaseModel):
    """Liste des modules configurables."""
    modules: list[ModuleSettingsListItem]
    total: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=ModuleSettingsListResponse)
async def list_configurable_modules(
    active_only: bool = True,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Liste tous les modules configurables pour le tenant.

    Retourne les modules qui ont des paramètres définis,
    avec indication de leur statut d'activation.
    """
    # Modules avec paramètres définis
    modules_with_settings = get_modules_with_settings()

    # Modules activés pour le tenant
    active_modules = db.query(TenantModule).filter(
        TenantModule.tenant_id == ctx.tenant_id,
        TenantModule.status == ModuleStatus.ACTIVE
    ).all()

    active_codes = {m.module_code for m in active_modules}
    active_configs = {m.module_code: m.config or {} for m in active_modules}

    result = []
    all_settings = get_all_module_settings()

    for code in modules_with_settings:
        schema = all_settings.get(code, {})
        is_active = code in active_codes

        if active_only and not is_active:
            continue

        # Vérifier si le tenant a des paramètres personnalisés
        has_custom = bool(active_configs.get(code))

        result.append(ModuleSettingsListItem(
            code=code,
            name=schema.get("name", code),
            description=schema.get("description"),
            is_active=is_active,
            has_custom_settings=has_custom,
            settings_count=len(schema.get("settings", []))
        ))

    return ModuleSettingsListResponse(
        modules=result,
        total=len(result)
    )


@router.get("/{module_code}/schema", response_model=ModuleSettingsSchema)
async def get_module_schema(
    module_code: str,
    ctx: SaaSContext = Depends(get_saas_context)
):
    """
    Retourne le schéma des paramètres d'un module.

    Inclut les définitions de tous les paramètres configurables
    avec leurs types, valeurs par défaut, et validations.
    """
    schema = get_module_settings_schema(module_code)

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_code}' n'a pas de paramètres configurables"
        )

    # Construire les définitions
    settings_defs = []
    for s in schema.get("settings", []):
        settings_defs.append(SettingDefinition(
            key=s["key"],
            label=s["label"],
            type=s["type"].value if isinstance(s["type"], SettingType) else s["type"],
            default=s.get("default"),
            category=s.get("category", SettingCategory.GENERAL).value if isinstance(s.get("category"), SettingCategory) else s.get("category", "general"),
            description=s.get("description"),
            placeholder=s.get("placeholder"),
            options=[SettingOption(value=o["value"], label=o["label"]) for o in s.get("options", [])] if s.get("options") else None,
            min=s.get("min"),
            max=s.get("max"),
            step=s.get("step"),
            max_length=s.get("max_length"),
            multiline=s.get("multiline", False),
            depends_on=s.get("depends_on"),
        ))

    # Grouper par catégorie
    categories = {}
    for s in settings_defs:
        cat = s.category
        if cat not in categories:
            categories[cat] = {
                "key": cat,
                "label": _get_category_label(cat),
                "count": 0
            }
        categories[cat]["count"] += 1

    return ModuleSettingsSchema(
        module_code=module_code,
        module_name=schema.get("name", module_code),
        description=schema.get("description"),
        settings=settings_defs,
        categories=list(categories.values())
    )


@router.get("/{module_code}", response_model=ModuleSettingsResponse)
async def get_module_settings(
    module_code: str,
    include_schema: bool = False,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Retourne les paramètres actuels d'un module pour le tenant.

    Les paramètres non définis utilisent les valeurs par défaut.
    """
    schema = get_module_settings_schema(module_code)

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_code}' n'a pas de paramètres configurables"
        )

    # Récupérer le module du tenant
    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == ctx.tenant_id,
        TenantModule.module_code == module_code
    ).first()

    is_active = tenant_module and tenant_module.status == ModuleStatus.ACTIVE

    # Fusionner avec les valeurs par défaut
    user_settings = tenant_module.config if tenant_module and tenant_module.config else {}
    merged_settings = merge_with_defaults(module_code, user_settings)

    response = ModuleSettingsResponse(
        module_code=module_code,
        module_name=schema.get("name", module_code),
        is_active=is_active,
        settings=merged_settings
    )

    if include_schema:
        response.settings_schema = await get_module_schema(module_code, ctx)

    return response


@router.put("/{module_code}", response_model=ModuleSettingsResponse)
async def update_module_settings(
    module_code: str,
    data: ModuleSettingsUpdate,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Met à jour les paramètres d'un module pour le tenant.

    Seuls les paramètres fournis sont mis à jour.
    Les paramètres non fournis conservent leur valeur actuelle.
    """
    schema = get_module_settings_schema(module_code)

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_code}' n'a pas de paramètres configurables"
        )

    # Valider les paramètres
    is_valid, errors = validate_module_settings(module_code, data.settings)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Paramètres invalides", "errors": errors}
        )

    # Récupérer ou créer le module du tenant
    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == ctx.tenant_id,
        TenantModule.module_code == module_code
    ).first()

    if not tenant_module:
        # Le module n'est pas activé pour ce tenant
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le module '{module_code}' n'est pas activé pour ce tenant"
        )

    # Fusionner les paramètres existants avec les nouveaux
    current_config = tenant_module.config or {}
    updated_config = {**current_config, **data.settings}

    tenant_module.config = updated_config
    db.commit()
    db.refresh(tenant_module)

    logger.info(
        f"Paramètres module '{module_code}' mis à jour pour tenant '{ctx.tenant_id}'"
    )

    # Retourner les paramètres mis à jour
    return ModuleSettingsResponse(
        module_code=module_code,
        module_name=schema.get("name", module_code),
        is_active=tenant_module.status == ModuleStatus.ACTIVE,
        settings=merge_with_defaults(module_code, updated_config)
    )


@router.post("/{module_code}/reset", response_model=ModuleSettingsResponse)
async def reset_module_settings(
    module_code: str,
    ctx: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Réinitialise les paramètres d'un module aux valeurs par défaut.

    Supprime tous les paramètres personnalisés du tenant.
    """
    schema = get_module_settings_schema(module_code)

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_code}' n'a pas de paramètres configurables"
        )

    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == ctx.tenant_id,
        TenantModule.module_code == module_code
    ).first()

    if not tenant_module:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le module '{module_code}' n'est pas activé pour ce tenant"
        )

    # Réinitialiser la config
    tenant_module.config = {}
    db.commit()

    logger.info(
        f"Paramètres module '{module_code}' réinitialisés pour tenant '{ctx.tenant_id}'"
    )

    return ModuleSettingsResponse(
        module_code=module_code,
        module_name=schema.get("name", module_code),
        is_active=tenant_module.status == ModuleStatus.ACTIVE,
        settings=get_module_settings_defaults(module_code)
    )


@router.get("/{module_code}/defaults")
async def get_module_defaults(
    module_code: str,
    ctx: SaaSContext = Depends(get_saas_context)
):
    """
    Retourne les valeurs par défaut d'un module.

    Utile pour comparer avec les valeurs actuelles.
    """
    schema = get_module_settings_schema(module_code)

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_code}' n'a pas de paramètres configurables"
        )

    return {
        "module_code": module_code,
        "module_name": schema.get("name", module_code),
        "defaults": get_module_settings_defaults(module_code)
    }


# =============================================================================
# HELPERS
# =============================================================================

def _get_category_label(category: str) -> str:
    """Retourne le label français d'une catégorie."""
    labels = {
        "general": "Général",
        "display": "Affichage",
        "notifications": "Notifications",
        "integration": "Intégrations",
        "security": "Sécurité",
        "advanced": "Avancé",
    }
    return labels.get(category, category.capitalize())
