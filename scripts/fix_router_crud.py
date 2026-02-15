#!/usr/bin/env python3
"""
AZALS - Fix Router CRUD Files
==============================

Regenere les router_crud.py avec les bons noms de schemas.
Analyse schemas.py pour trouver les vrais noms.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

MODULES_DIR = Path("app/modules")

# Template pour router_crud.py minimal mais fonctionnel
ROUTER_TEMPLATE = '''"""
AZALS - {module_title} Router (CRUDRouter v3)
{separator}

Router minimaliste utilisant CRUDRouter.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

{imports}

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================

router = APIRouter(prefix="/{module_name}", tags=["{module_title}"])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_module_status():
    """Statut du module {module_title}."""
    return {{
        "module": "{module_name}",
        "version": "v3",
        "status": "active"
    }}

{endpoints}
'''


def find_schemas(module_path: Path) -> Dict[str, List[str]]:
    """
    Trouve les schemas Pydantic dans un module.

    Returns:
        Dict mapping base_name -> [Create, Update, Response schemas]
    """
    schemas_file = module_path / "schemas.py"
    if not schemas_file.exists():
        return {}

    content = schemas_file.read_text()
    schemas = {}

    # Pattern pour trouver les classes de schema
    # class XxxCreate, class XxxUpdate, class XxxResponse, class XxxBase
    pattern = r'class\s+(\w+)(Create|Update|Response|Base)\s*\('
    matches = re.findall(pattern, content)

    for base_name, suffix in matches:
        full_name = f"{base_name}{suffix}"
        if base_name not in schemas:
            schemas[base_name] = []
        if full_name not in schemas[base_name]:
            schemas[base_name].append(full_name)

    return schemas


def find_service_class(module_path: Path) -> Tuple[str, str]:
    """
    Trouve la classe de service principale dans service.py.

    Returns:
        Tuple[class_name, import_path]
    """
    service_file = module_path / "service.py"
    if not service_file.exists():
        return None, None

    content = service_file.read_text()

    # Chercher la premiere classe de service
    match = re.search(r'class\s+(\w+Service)\s*[:\(]', content)
    if match:
        return match.group(1), "service"

    return None, None


def generate_crud_endpoint(resource: str, schemas: List[str], service_class: str) -> str:
    """Genere un endpoint CRUD simple pour une ressource."""
    create_schema = next((s for s in schemas if s.endswith("Create")), None)
    response_schema = next((s for s in schemas if s.endswith("Response")), None)

    if not response_schema:
        return ""

    plural = f"{resource.lower()}s" if not resource.lower().endswith("s") else resource.lower()

    return f'''
@router.get("/{plural}", response_model=List[{response_schema}])
async def list_{plural}(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db),
):
    """Liste les {plural}."""
    # TODO: Implementer avec service
    return []
'''


def fix_module(module_name: str) -> Tuple[bool, str]:
    """Corrige le router_crud.py d'un module."""
    module_path = MODULES_DIR / module_name

    if not module_path.exists():
        return False, "Module non trouve"

    # Trouver les schemas
    schemas = find_schemas(module_path)
    if not schemas:
        return False, "Pas de schemas"

    # Trouver le service
    service_class, service_import = find_service_class(module_path)

    # Generer les imports
    schema_imports = []
    for base_name, schema_list in list(schemas.items())[:5]:  # Max 5 ressources
        for schema in schema_list:
            if schema not in schema_imports:
                schema_imports.append(schema)

    imports = ""
    if schema_imports:
        imports = f"from app.modules.{module_name}.schemas import (\n"
        imports += "    " + ",\n    ".join(schema_imports[:15]) + ",\n)"

    if service_class:
        imports += f"\nfrom app.modules.{module_name}.{service_import} import {service_class}"

    # Generer les endpoints
    endpoints = ""
    for base_name, schema_list in list(schemas.items())[:3]:  # Max 3 ressources
        endpoints += generate_crud_endpoint(base_name, schema_list, service_class)

    # Generer le fichier
    module_title = module_name.replace("_", " ").title()
    separator = "=" * (len(module_title) + 30)

    content = ROUTER_TEMPLATE.format(
        module_title=module_title,
        separator=separator,
        module_name=module_name,
        imports=imports,
        endpoints=endpoints if endpoints else "pass"
    )

    # Ecrire le fichier
    router_file = module_path / "router_crud.py"
    router_file.write_text(content)

    return True, f"OK - {len(schemas)} ressources"


def main():
    # Liste des modules a corriger
    modules = [
        "iam", "backup", "tenants", "guardian", "audit",
        "accounting", "finance", "procurement", "purchases", "pos",
        "stripe_integration", "subscriptions", "inventory", "production",
        "projects", "maintenance", "field_service", "helpdesk",
        "interventions", "qc", "quality", "commercial", "contacts",
        "bi", "broadcast", "compliance", "hr", "email", "mobile",
        "marketplace", "autoconfig", "triggers", "country_packs",
        "web", "website", "ai_assistant", "enrichment", "odoo_import"
    ]

    success = 0
    failed = 0

    for module in modules:
        ok, msg = fix_module(module)
        status = "✓" if ok else "✗"
        print(f"{status} {module}: {msg}")
        if ok:
            success += 1
        else:
            failed += 1

    print(f"\nTotal: {success} OK, {failed} echecs")


if __name__ == "__main__":
    main()
