#!/usr/bin/env python3
"""
Script de vérification de la migration CORE SaaS v2
Vérifie que tous les modules ont bien été migrés.
"""

import os
import sys
from pathlib import Path

# Modules migrés dans cette session
SESSION_MODULES = [
    "website",
    "ai_assistant",
    "autoconfig",
    "country_packs",
    "marketplace",
    "mobile",
    "stripe_integration"
]

# Tous les routers v2 attendus dans main.py
EXPECTED_V2_ROUTERS = [
    "ai_assistant_router_v2",
    "autoconfig_router_v2",
    "country_packs_router_v2",
    "email_router_v2",
    "marketplace_router_v2",
    "mobile_router_v2",
    "stripe_router_v2",
    "triggers_router_v2",
    "web_router_v2",
    "website_router_v2"
]


def check_module_files(module_name):
    """Vérifie que tous les fichiers requis existent pour un module."""
    base_path = Path(f"app/modules/{module_name}")

    checks = {
        "service.py": base_path / "service.py",
        "router_v2.py": base_path / "router_v2.py",
        "tests/__init__.py": base_path / "tests" / "__init__.py",
        "tests/conftest.py": base_path / "tests" / "conftest.py",
        "tests/test_router_v2.py": base_path / "tests" / "test_router_v2.py"
    }

    results = {}
    for name, path in checks.items():
        results[name] = path.exists()

    return results


def check_main_py_registration():
    """Vérifie que tous les routers v2 sont enregistrés dans main.py."""
    main_py = Path("app/main.py")

    if not main_py.exists():
        return None

    content = main_py.read_text()

    found_routers = []
    missing_routers = []

    for router in EXPECTED_V2_ROUTERS:
        if f"app.include_router({router})" in content:
            found_routers.append(router)
        else:
            missing_routers.append(router)

    return {
        "found": found_routers,
        "missing": missing_routers,
        "total": len(EXPECTED_V2_ROUTERS)
    }


def main():
    print("=" * 70)
    print("VÉRIFICATION MIGRATION CORE SaaS v2 - AZALSCORE")
    print("=" * 70)
    print()

    # Vérifier modules de la session
    print("🔍 Vérification modules migrés dans cette session:")
    print("-" * 70)

    all_modules_ok = True

    for module in SESSION_MODULES:
        print(f"\n📦 Module: {module}")
        checks = check_module_files(module)

        for file_name, exists in checks.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {file_name}")
            if not exists:
                all_modules_ok = False

    print()
    print("-" * 70)

    # Vérifier main.py
    print("\n🔍 Vérification routers v2 enregistrés dans main.py:")
    print("-" * 70)

    main_check = check_main_py_registration()

    if main_check:
        print(f"\n✅ Routers trouvés: {len(main_check['found'])}/{main_check['total']}")

        if main_check['found']:
            print("\nRouters enregistrés:")
            for router in sorted(main_check['found']):
                print(f"  ✅ {router}")

        if main_check['missing']:
            print("\n❌ Routers manquants:")
            for router in sorted(main_check['missing']):
                print(f"  ❌ {router}")
    else:
        print("❌ Fichier main.py introuvable")

    print()
    print("=" * 70)

    # Résumé
    if all_modules_ok and main_check and not main_check['missing']:
        print("✅ MIGRATION VALIDÉE - Tous les fichiers sont présents")
        print("=" * 70)
        return 0
    else:
        print("⚠️  MIGRATION INCOMPLÈTE - Certains fichiers sont manquants")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
