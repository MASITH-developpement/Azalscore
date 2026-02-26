#!/usr/bin/env python3
"""
AZALS - Script de Migration vers CRUDRouter
=============================================

Génère automatiquement les services v2 et routers CRUD pour chaque module.

Usage:
    python scripts/migrate_to_crudrouter.py --module commercial
    python scripts/migrate_to_crudrouter.py --all
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

MODULES_DIR = Path("app/modules")

# Template pour service v2 (BaseService compatible)
SERVICE_V2_TEMPLATE = '''"""
AZALS - {module_title} Service (v2 - CRUDRouter Compatible)
{separator}

Service compatible avec BaseService et CRUDRouter.
Migration automatique depuis service.py.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.core.saas_context import Result, SaaSContext

{model_imports}
{schema_imports}

logger = logging.getLogger(__name__)


{service_classes}
'''

# Template pour router CRUD
ROUTER_CRUD_TEMPLATE = '''"""
AZALS - {module_title} Router (CRUDRouter)
{separator}

Router minimaliste utilisant CRUDRouter.
Génération automatique des endpoints CRUD.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import CRUDRouter, SaaSContext, get_context, get_db, PaginatedResponse

{imports}

# =============================================================================
# ROUTERS CRUD AUTO-GÉNÉRÉS
# =============================================================================

{crud_routers}

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/{module_name}", tags=["{module_title}"])

{include_routers}

# =============================================================================
# ENDPOINTS MÉTIER PERSONNALISÉS
# =============================================================================

{custom_endpoints}
'''


def find_models_in_module(module_path: Path) -> List[str]:
    """Trouve les modèles SQLAlchemy dans un module."""
    models_file = module_path / "models.py"
    if not models_file.exists():
        return []

    content = models_file.read_text()
    # Pattern: class ModelName(Base) ou class ModelName(TenantModel)
    pattern = r'class\s+(\w+)\s*\([^)]*(?:Base|TenantModel|Model)[^)]*\)'
    return re.findall(pattern, content)


def find_schemas_in_module(module_path: Path) -> Dict[str, List[str]]:
    """Trouve les schémas Pydantic dans un module."""
    schemas_file = module_path / "schemas.py"
    if not schemas_file.exists():
        return {}

    content = schemas_file.read_text()
    schemas = {}

    # Pattern: class SchemaName(BaseModel/Schema)
    pattern = r'class\s+(\w+)(Create|Update|Response|Base)\s*\('
    matches = re.findall(pattern, content)

    for base_name, suffix in matches:
        full_name = f"{base_name}{suffix}"
        resource = base_name
        if resource not in schemas:
            schemas[resource] = []
        schemas[resource].append(full_name)

    return schemas


def analyze_service(module_path: Path) -> Dict[str, any]:
    """Analyse le service.py existant pour extraire les ressources."""
    service_file = module_path / "service.py"
    if not service_file.exists():
        return {"resources": [], "methods": {}}

    content = service_file.read_text()

    # Trouver les méthodes CRUD par ressource
    resources = {}

    # Patterns: create_xxx, get_xxx, list_xxx, update_xxx, delete_xxx
    crud_pattern = r'def\s+(create|get|list|update|delete)_(\w+)\s*\('
    matches = re.findall(crud_pattern, content)

    for action, resource in matches:
        if resource not in resources:
            resources[resource] = set()
        resources[resource].add(action)

    return {"resources": resources}


def generate_service_class(resource: str, model: str, schemas: List[str]) -> str:
    """Génère une classe de service pour une ressource."""
    create_schema = next((s for s in schemas if s.endswith("Create")), f"{model}Create")
    update_schema = next((s for s in schemas if s.endswith("Update")), f"{model}Update")

    class_name = f"{model}Service"

    return f'''
class {class_name}(BaseService[{model}, {create_schema}, {update_schema}]):
    """Service CRUD pour {resource}."""

    model = {model}

    # Les méthodes CRUD sont héritées de BaseService:
    # - get(id) -> Optional[{model}]
    # - get_or_fail(id) -> Result[{model}]
    # - list(page, page_size, filters) -> PaginatedResponse
    # - create(data) -> Result[{model}]
    # - update(id, data) -> Result[{model}]
    # - delete(id, soft) -> Result[bool]

    # Ajouter ici les méthodes métier spécifiques
'''


def generate_crud_router(resource: str, model: str, schemas: List[str], module_name: str) -> str:
    """Génère un router CRUD pour une ressource."""
    create_schema = next((s for s in schemas if s.endswith("Create")), f"{model}Create")
    update_schema = next((s for s in schemas if s.endswith("Update")), f"{model}Update")
    response_schema = next((s for s in schemas if s.endswith("Response")), f"{model}Response")

    service_class = f"{model}Service"
    plural = f"{resource}s" if not resource.endswith("s") else resource

    return f'''
{plural}_router = CRUDRouter.create_crud_router(
    service_class={service_class},
    resource_name="{resource}",
    plural_name="{plural}",
    create_schema={create_schema},
    update_schema={update_schema},
    response_schema={response_schema},
    tags=["{module_name.replace('_', ' ').title()}"],
)
'''


def migrate_module(module_name: str, dry_run: bool = False) -> Tuple[bool, str]:
    """Migre un module vers CRUDRouter."""
    module_path = MODULES_DIR / module_name

    if not module_path.exists():
        return False, f"Module {module_name} non trouvé"

    # Analyser le module
    models = find_models_in_module(module_path)
    schemas = find_schemas_in_module(module_path)
    service_info = analyze_service(module_path)

    if not models:
        return False, f"Pas de modèles trouvés dans {module_name}"

    print(f"\n{'='*60}")
    print(f"Module: {module_name}")
    print(f"{'='*60}")
    print(f"Modèles trouvés: {', '.join(models)}")
    print(f"Schémas trouvés: {schemas}")
    print(f"Ressources CRUD: {list(service_info['resources'].keys())}")

    if dry_run:
        return True, "Dry run - pas de fichiers créés"

    # Générer service_v2.py
    module_title = module_name.replace("_", " ").title()

    model_imports = f"from app.modules.{module_name}.models import (\n"
    model_imports += "    " + ",\n    ".join(models) + ",\n)"

    schema_list = []
    for resource_schemas in schemas.values():
        schema_list.extend(resource_schemas)

    if schema_list:
        schema_imports = f"from app.modules.{module_name}.schemas import (\n"
        schema_imports += "    " + ",\n    ".join(sorted(set(schema_list))) + ",\n)"
    else:
        schema_imports = "# Pas de schémas trouvés - à ajouter manuellement"

    # Générer les classes de service
    service_classes = []
    for model in models:
        resource = model.lower()
        model_schemas = schemas.get(model, [])
        service_classes.append(generate_service_class(resource, model, model_schemas))

    service_content = SERVICE_V2_TEMPLATE.format(
        module_title=module_title,
        separator="=" * (len(module_title) + 50),
        model_imports=model_imports,
        schema_imports=schema_imports,
        service_classes="\n".join(service_classes)
    )

    # Écrire service_v2.py
    service_v2_path = module_path / "service_v2.py"
    service_v2_path.write_text(service_content)
    print(f"✓ Créé: {service_v2_path}")

    # Générer router_crud.py
    crud_routers = []
    include_routers = []

    for model in models[:5]:  # Limiter à 5 ressources principales
        resource = model.lower()
        model_schemas = schemas.get(model, [])
        crud_routers.append(generate_crud_router(resource, model, model_schemas, module_name))
        plural = f"{resource}s" if not resource.endswith("s") else resource
        include_routers.append(f"router.include_router({plural}_router)")

    # Imports pour le router
    imports = [f"from app.modules.{module_name}.service_v2 import ("]
    for model in models[:5]:
        imports.append(f"    {model}Service,")
    imports.append(")")

    if schema_list:
        imports.append(f"\nfrom app.modules.{module_name}.schemas import (")
        for schema in sorted(set(schema_list))[:15]:
            imports.append(f"    {schema},")
        imports.append(")")

    router_content = ROUTER_CRUD_TEMPLATE.format(
        module_title=module_title,
        separator="=" * (len(module_title) + 35),
        module_name=module_name,
        imports="\n".join(imports),
        crud_routers="\n".join(crud_routers),
        include_routers="\n".join(include_routers),
        custom_endpoints="# Ajouter ici les endpoints métier personnalisés\npass"
    )

    router_crud_path = module_path / "router_crud.py"
    router_crud_path.write_text(router_content)
    print(f"✓ Créé: {router_crud_path}")

    return True, f"Module {module_name} migré avec succès"


def main():
    parser = argparse.ArgumentParser(description="Migration vers CRUDRouter")
    parser.add_argument("--module", help="Nom du module à migrer")
    parser.add_argument("--all", action="store_true", help="Migrer tous les modules")
    parser.add_argument("--dry-run", action="store_true", help="Analyse sans créer de fichiers")
    parser.add_argument("--list", action="store_true", help="Lister les modules disponibles")

    args = parser.parse_args()

    if args.list:
        modules = sorted([d.name for d in MODULES_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")])
        print("Modules disponibles:")
        for m in modules:
            print(f"  - {m}")
        return

    if args.module:
        success, message = migrate_module(args.module, args.dry_run)
        print(f"\n{message}")
    elif args.all:
        modules = sorted([d.name for d in MODULES_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")])
        results = []
        for module in modules:
            try:
                success, message = migrate_module(module, args.dry_run)
                results.append((module, success, message))
            except Exception as e:
                results.append((module, False, str(e)))

        print("\n" + "="*60)
        print("RÉSUMÉ")
        print("="*60)
        for module, success, message in results:
            status = "✓" if success else "✗"
            print(f"{status} {module}: {message}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
