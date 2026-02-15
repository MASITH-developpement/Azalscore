#!/usr/bin/env python3
"""
AZALS - Enrich Router CRUD Files
=================================

Copie le contenu de router_unified.py vers router_crud.py
en adaptant les imports pour utiliser app.azals.

Usage:
    python scripts/enrich_router_crud.py
"""

import re
from pathlib import Path
from typing import Tuple

MODULES_DIR = Path("app/modules")

# Modules deja enrichis manuellement
ALREADY_ENRICHED = {"commercial", "iam", "accounting"}

# Modules qui n'ont pas de router_unified.py
SKIP_MODULES = {"odoo_import", "enrichment", "contacts"}


def transform_imports(content: str, module_name: str) -> str:
    """
    Transforme les imports pour utiliser app.azals.
    """
    # Remplacer les imports de core.compat/core.database par app.azals
    content = re.sub(
        r'from app\.core\.compat import get_context',
        'from app.azals import SaaSContext, get_context, get_db',
        content
    )
    content = re.sub(
        r'from app\.core\.database import get_db',
        '',
        content
    )
    content = re.sub(
        r'from app\.core\.saas_context import SaaSContext',
        '',
        content
    )

    # Nettoyer les lignes vides en double
    content = re.sub(r'\n\n\n+', '\n\n', content)

    return content


def update_docstring(content: str) -> str:
    """
    Met a jour le docstring pour indiquer v3.
    """
    # Chercher le premier docstring et le modifier
    pattern = r'"""[\s\S]*?Router unifié compatible v1 ET v2\.[\s\S]*?"""'

    def replace_docstring(match):
        return match.group(0).replace(
            "Router unifié compatible v1 ET v2.",
            "Router complet compatible v1, v2 et v3 via app.azals."
        )

    content = re.sub(pattern, replace_docstring, content, count=1)
    return content


def update_router_tag(content: str, module_name: str) -> str:
    """
    S'assure que le router tag est correct.
    """
    # Ajouter le tag v3 au module
    return content


def enrich_module(module_name: str) -> Tuple[bool, str]:
    """
    Enrichit le router_crud.py d'un module depuis router_unified.py.

    Returns:
        Tuple[success, message]
    """
    module_path = MODULES_DIR / module_name

    if not module_path.exists():
        return False, "Module non trouve"

    unified_file = module_path / "router_unified.py"
    crud_file = module_path / "router_crud.py"

    # Verifier que router_unified.py existe
    if not unified_file.exists():
        return False, "Pas de router_unified.py"

    # Lire le contenu
    content = unified_file.read_text()

    # Compter les endpoints
    endpoint_count = len(re.findall(r'@router\.(get|post|put|patch|delete)\(', content))

    if endpoint_count < 5:
        return False, f"Seulement {endpoint_count} endpoints"

    # Transformer les imports
    content = transform_imports(content, module_name)

    # Mettre a jour le docstring
    content = update_docstring(content)

    # Ecrire le fichier
    crud_file.write_text(content)

    return True, f"OK - {endpoint_count} endpoints"


def main():
    """Main function."""
    # Trouver tous les modules
    modules = [d.name for d in MODULES_DIR.iterdir() if d.is_dir() and (d / "__init__.py").exists()]

    success = 0
    skipped = 0
    failed = 0

    print("=" * 60)
    print("ENRICHISSEMENT DES router_crud.py")
    print("=" * 60)
    print()

    for module in sorted(modules):
        if module in ALREADY_ENRICHED:
            print(f"  {module}: Deja enrichi manuellement")
            skipped += 1
            continue

        if module in SKIP_MODULES:
            print(f"  {module}: Module skip")
            skipped += 1
            continue

        ok, msg = enrich_module(module)
        status = "OK" if ok else "SKIP"
        print(f"  {module}: {status} - {msg}")

        if ok:
            success += 1
        elif "Pas de router_unified" in msg or "Seulement" in msg:
            skipped += 1
        else:
            failed += 1

    print()
    print("=" * 60)
    print(f"Total: {success} enrichis, {skipped} skipped, {failed} echecs")
    print("=" * 60)


if __name__ == "__main__":
    main()
