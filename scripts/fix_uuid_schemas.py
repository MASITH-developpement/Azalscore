#!/usr/bin/env python3
"""
Script de correction automatique des schémas UUID
=================================================

Corrige les schémas Pydantic qui utilisent `id: str` alors que les modèles
utilisent UUID. Cela évite l'erreur "UUID is not JSON serializable".

Usage:
    python3 scripts/fix_uuid_schemas.py
"""

import re
from pathlib import Path


MODULES_WITH_UUID = ["iam", "backup", "email", "marketplace"]


def fix_schema_file(schema_path: Path) -> tuple[bool, int]:
    """
    Corrige un fichier de schémas.

    Returns:
        (modified, num_fixes): True si modifié, nombre de corrections
    """
    content = schema_path.read_text()
    original_content = content

    num_fixes = 0

    # 1. Ajouter import UUID si manquant
    if "from uuid import UUID" not in content and "import UUID" not in content:
        # Trouver la ligne d'import de pydantic
        import_pattern = r"(from pydantic import [^\n]+)"
        match = re.search(import_pattern, content)

        if match:
            # Ajouter l'import UUID juste avant ou après
            import_line = match.group(1)
            new_imports = f"from uuid import UUID\n{import_line}"
            content = content.replace(import_line, new_imports)
            num_fixes += 1

    # 2. Remplacer id: str par id: UUID dans les classes Response
    # Pattern: cherche "id: str" dans les classes *Response
    response_class_pattern = r"(class \w+Response\([^)]+\):.*?)(id:\s*str)(\s)"

    def replace_id_type(match):
        nonlocal num_fixes
        before = match.group(1)
        old_type = match.group(2)
        after = match.group(3)

        # Vérifier si c'est bien un champ id (pas tenant_id, user_id, etc.)
        if "id: str" in old_type and not any(prefix in before[-50:] for prefix in ["tenant_", "user_", "role_", "group_", "session_"]):
            num_fixes += 1
            return f"{before}id: UUID{after}"
        return match.group(0)

    # Rechercher dans tout le fichier
    lines = content.split('\n')
    new_lines = []
    in_response_class = False

    for line in lines:
        if 'class ' in line and 'Response' in line and 'BaseModel' in line:
            in_response_class = True
            new_lines.append(line)
        elif in_response_class:
            if line.strip().startswith('class ') or (line and not line[0].isspace()):
                in_response_class = False
            elif re.match(r'\s+id:\s*str\s*$', line):
                # C'est un champ id: str dans une classe Response
                new_lines.append(line.replace('id: str', 'id: UUID'))
                num_fixes += 1
                continue
            new_lines.append(line)
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    # Écrire seulement si modifié
    if content != original_content:
        schema_path.write_text(content)
        return True, num_fixes

    return False, 0


def main():
    """Point d'entrée principal."""
    print("🔧 Correction des schémas UUID")
    print("=" * 50)
    print()

    base_path = Path(__file__).parent.parent / "app" / "modules"
    total_fixes = 0
    modified_files = []

    for module_name in MODULES_WITH_UUID:
        schema_path = base_path / module_name / "schemas.py"

        if not schema_path.exists():
            print(f"⏭️  {module_name}: schemas.py non trouvé")
            continue

        print(f"🔍 {module_name}...", end=" ")

        try:
            modified, num_fixes = fix_schema_file(schema_path)

            if modified:
                print(f"✅ {num_fixes} correction(s)")
                modified_files.append(module_name)
                total_fixes += num_fixes
            else:
                print("✓ Déjà correct")

        except Exception as e:
            print(f"❌ Erreur: {e}")

    print()
    print("=" * 50)
    print(f"✅ {total_fixes} correction(s) appliquée(s)")

    if modified_files:
        print(f"\n📝 Fichiers modifiés:")
        for module in modified_files:
            print(f"  - app/modules/{module}/schemas.py")

        print("\n💡 N'oubliez pas de rebuilder l'image Docker:")
        print("   docker compose -f docker-compose.prod.yml build api")
        print("   docker compose -f docker-compose.prod.yml up -d api")

    print()


if __name__ == "__main__":
    main()
