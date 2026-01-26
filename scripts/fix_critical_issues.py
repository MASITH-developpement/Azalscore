#!/usr/bin/env python3
"""
Fix Critical Issues - Code Review v2
====================================
Corrige automatiquement les 21 issues critiques identifiées.
"""

import re
from pathlib import Path
from typing import List, Tuple


def fix_missing_imports(file_path: Path) -> bool:
    """Ajoute les imports manquants pour CORE SaaS v2."""
    content = file_path.read_text()
    original = content
    modified = False

    # Vérifier si c'est un router_v2.py
    if not file_path.name == "router_v2.py":
        return False

    # Import get_saas_context manquant
    if "from app.core.dependencies_v2 import get_saas_context" not in content:
        # Trouver la section des imports
        import_section_end = content.find("\n\n")
        if import_section_end == -1:
            import_section_end = content.find("\nrouter = ")

        if import_section_end > 0:
            # Ajouter l'import
            new_import = "from app.core.dependencies_v2 import get_saas_context\n"

            # Chercher où insérer (après les imports FastAPI généralement)
            fastapi_import_pos = content.find("from fastapi import")
            if fastapi_import_pos > -1:
                # Trouver la fin de cette ligne
                line_end = content.find("\n", fastapi_import_pos)
                content = content[:line_end+1] + new_import + content[line_end+1:]
                modified = True

    # Import SaaSContext manquant
    if "from app.core.saas_context import SaaSContext" not in content:
        # Ajouter après get_saas_context si présent
        saas_dep_pos = content.find("from app.core.dependencies_v2 import get_saas_context")
        if saas_dep_pos > -1:
            line_end = content.find("\n", saas_dep_pos)
            content = content[:line_end+1] + "from app.core.saas_context import SaaSContext\n" + content[line_end+1:]
            modified = True

    if modified:
        file_path.write_text(content)
        return True

    return False


def fix_missing_prefix(file_path: Path) -> bool:
    """Corrige le prefix /v2/ manquant dans APIRouter."""
    content = file_path.read_text()
    original = content
    modified = False

    # Vérifier si c'est un router_v2.py
    if not file_path.name == "router_v2.py":
        return False

    # Chercher APIRouter sans prefix /v2/
    patterns = [
        # Pattern 1: prefix sans /v2/
        (r'APIRouter\(prefix="(/[^v][^2][^/][^"]*)"', r'APIRouter(prefix="/v2\1"'),
        # Pattern 2: Pas de prefix du tout
        (r'APIRouter\(\s*tags=', r'APIRouter(prefix="/v2/FIXME", tags='),
    ]

    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True

    if modified:
        file_path.write_text(content)
        return True

    return False


def analyze_and_fix_module(module_name: str) -> Tuple[int, List[str]]:
    """Analyse et corrige un module."""
    module_path = Path(f"app/modules/{module_name}")
    router_file = module_path / "router_v2.py"

    fixes_applied = 0
    fixes_list = []

    if router_file.exists():
        # Fix imports
        if fix_missing_imports(router_file):
            fixes_applied += 1
            fixes_list.append(f"Imports CORE SaaS v2 ajoutés")

        # Fix prefix
        if fix_missing_prefix(router_file):
            fixes_applied += 1
            fixes_list.append(f"Prefix /v2/ corrigé")

    return fixes_applied, fixes_list


def main():
    """Main function."""
    print("🔧 Correction Issues Critiques - Code Review v2")
    print("=" * 60)
    print()

    # Modules identifiés avec issues critiques
    modules_with_issues = [
        "audit", "automated_accounting", "bi", "commercial", "ecommerce",
        "finance", "guardian", "helpdesk", "hr", "iam", "inventory",
        "marketplace", "production", "projects", "tenants"
    ]

    total_fixes = 0
    modules_fixed = []

    for module in modules_with_issues:
        print(f"🔍 Analyse: {module}...", end=" ")

        fixes_count, fixes_list = analyze_and_fix_module(module)

        if fixes_count > 0:
            print(f"✅ {fixes_count} fix(es)")
            for fix in fixes_list:
                print(f"   - {fix}")
            total_fixes += fixes_count
            modules_fixed.append(module)
        else:
            print("⏭️  Aucun fix nécessaire")

    print()
    print("=" * 60)
    print(f"✅ Corrections terminées!")
    print(f"📊 {total_fixes} fixes appliqués sur {len(modules_fixed)} modules")
    print()

    if modules_fixed:
        print("Modules corrigés:")
        for module in modules_fixed:
            print(f"  - {module}")
        print()

    return 0


if __name__ == "__main__":
    exit(main())
