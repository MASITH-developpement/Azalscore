#!/usr/bin/env python3
"""
AZALS - Fix Service V2 Type Annotations
========================================

Corrige les annotations de type dans les fichiers service_v2.py generes.
Remplace les noms de schemas incorrects par Any pour permettre le chargement.
"""

import os
import re
from pathlib import Path

MODULES_DIR = Path("app/modules")


def fix_service_v2(module_path: Path) -> bool:
    """Corrige le service_v2.py d'un module."""
    service_file = module_path / "service_v2.py"
    if not service_file.exists():
        return False

    content = service_file.read_text()
    original = content

    # Ajouter Any aux imports typing si necessaire
    if "from typing import" in content and "Any" not in content:
        content = content.replace(
            "from typing import",
            "from typing import Any,"
        )

    # Pattern: BaseService[Model, ModelCreate, ModelUpdate]
    # Remplacer par: BaseService[Model, Any, Any]
    pattern = r"BaseService\[(\w+),\s*\w+,\s*\w+\]"
    content = re.sub(pattern, r"BaseService[\1, Any, Any]", content)

    if content != original:
        service_file.write_text(content)
        return True
    return False


def main():
    modules = sorted([
        d for d in MODULES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ])

    fixed = 0
    for module in modules:
        if fix_service_v2(module):
            print(f"Fixed: {module.name}")
            fixed += 1

    print(f"\nTotal fixed: {fixed}")


if __name__ == "__main__":
    main()
