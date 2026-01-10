#!/usr/bin/env python3
"""
AZALS - Fix Imports Safe - Correcteur d'imports intelligent
============================================================
Corrige les imports de Base sans casser les imports multilignes.
"""

import os
import sys
import re
from pathlib import Path


def fix_file_imports(file_path: Path) -> bool:
    """Corrige les imports d'un fichier de manière sécurisée."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[ERREUR] {file_path}: {e}")
        return False

    original = content
    modified = False

    # 1. Remplacer l'import de Base depuis app.core.database
    # Pattern: from app.core.database import ... Base ...
    if 'from app.core.database import' in content and 'Base' in content:
        # Trouver la ligne d'import
        lines = content.split('\n')
        new_lines = []
        base_import_added = False

        for i, line in enumerate(lines):
            if 'from app.core.database import' in line:
                # Vérifier si c'est une import multiligne
                if line.rstrip().endswith('('):
                    # Import multiligne - trouver la fin
                    import_lines = [line]
                    j = i + 1
                    while j < len(lines) and ')' not in lines[j]:
                        import_lines.append(lines[j])
                        j += 1
                    if j < len(lines):
                        import_lines.append(lines[j])

                    # Reconstruire sans Base
                    full_import = '\n'.join(import_lines)
                    if 'Base' in full_import:
                        # Retirer Base de l'import
                        full_import = re.sub(r',?\s*\bBase\b\s*,?', '', full_import)
                        full_import = re.sub(r'\(\s*,', '(', full_import)
                        full_import = re.sub(r',\s*\)', ')', full_import)
                        full_import = re.sub(r',\s*,', ',', full_import)

                        # Vérifier s'il reste quelque chose à importer
                        match = re.search(r'import\s*\(([^)]*)\)', full_import, re.DOTALL)
                        if match:
                            remaining = match.group(1).strip(' ,\n')
                            if remaining:
                                new_lines.append(full_import)
                        # Sinon ne pas ajouter l'import vide

                        # Ajouter le nouvel import de Base
                        if not base_import_added:
                            new_lines.append('from app.db import Base')
                            base_import_added = True
                            modified = True

                        # Sauter les lignes déjà traitées
                        for _ in range(len(import_lines) - 1):
                            if i + 1 < len(lines):
                                i += 1
                        continue
                else:
                    # Import simple sur une ligne
                    if 'Base' in line:
                        # Retirer Base
                        new_line = re.sub(r',?\s*\bBase\b\s*,?', '', line)
                        new_line = re.sub(r'import\s*,', 'import ', new_line)
                        new_line = re.sub(r',\s*$', '', new_line)
                        new_line = re.sub(r',\s*,', ',', new_line)

                        # Vérifier s'il reste des imports
                        if 'import' in new_line and new_line.split('import')[1].strip():
                            new_lines.append(new_line)

                        # Ajouter le nouvel import
                        if not base_import_added:
                            new_lines.append('from app.db import Base')
                            base_import_added = True
                            modified = True
                        continue

            new_lines.append(line)

        content = '\n'.join(new_lines)

    # 2. Ajouter from app.db import Base si manquant et que Base est utilisé
    if 'Base)' in content or '(Base,' in content or 'Base):' in content:
        if 'from app.db import Base' not in content and 'from app.db.base import Base' not in content:
            # Trouver l'endroit pour insérer
            lines = content.split('\n')
            insert_idx = 0

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    insert_idx = i + 1
                elif stripped and not stripped.startswith('#') and insert_idx > 0:
                    break

            lines.insert(insert_idx, 'from app.db import Base')
            content = '\n'.join(lines)
            modified = True

    # Sauvegarder si modifié
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False


def main():
    base_path = Path('/home/user/Azalscore/app')

    print("[FIX] Correction sécurisée des imports...")

    fixed_count = 0
    for file_path in base_path.rglob('*.py'):
        if '__pycache__' in str(file_path):
            continue
        if 'test' in str(file_path).lower():
            continue

        if fix_file_imports(file_path):
            rel_path = file_path.relative_to(base_path)
            print(f"  ✓ {rel_path}")
            fixed_count += 1

    print(f"\n[FIX] {fixed_count} fichier(s) corrigé(s)")


if __name__ == '__main__':
    main()
