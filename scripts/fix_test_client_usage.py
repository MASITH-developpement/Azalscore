#!/usr/bin/env python3
"""
Script pour mettre à jour tous les tests v2 pour utiliser la fixture test_client.
Remplace les imports et usages du client module-level par la fixture.
"""

import re
from pathlib import Path


def fix_test_file(file_path: Path) -> bool:
    """Fixe un fichier de test pour utiliser la fixture test_client."""

    content = file_path.read_text()
    original = content

    # 1. Supprimer les imports FastAPI TestClient et app
    content = re.sub(
        r'from fastapi\.testclient import TestClient\n',
        '',
        content
    )
    content = re.sub(
        r'from app\.main import app\n',
        '',
        content
    )

    # 2. Supprimer la création du client module-level
    content = re.sub(
        r'client = TestClient\(app\)\n',
        '',
        content
    )

    # 3. Remplacer tous les usages de "client." par "test_client."
    # en ajoutant test_client comme paramètre de fonction si nécessaire

    # Trouver toutes les fonctions de test qui utilisent 'client'
    def add_test_client_param(match):
        func_name = match.group(1)
        params = match.group(2).strip()

        # Si la fonction n'a pas de paramètres
        if not params:
            return f"def {func_name}(test_client):"

        # Si elle a déjà test_client, ne rien faire
        if 'test_client' in params:
            return match.group(0)

        # Sinon, ajouter test_client en premier
        return f"def {func_name}(test_client, {params}):"

    # Remplacer les signatures de fonctions de test
    content = re.sub(
        r'def (test_[^(]+)\(([^)]*)\):',
        add_test_client_param,
        content
    )

    # 4. Remplacer "client." par "test_client."
    content = re.sub(
        r'\bclient\.',
        'test_client.',
        content
    )

    # 5. Remplacer f"{BASE_URL}" references si client était utilisé
    # (déjà couvert par l'étape 4)

    # Écrire seulement si modifié
    if content != original:
        file_path.write_text(content)
        return True

    return False


def main():
    """Fixe tous les fichiers test_router_v2.py."""

    modules_dir = Path("app/modules")
    fixed_count = 0

    for test_file in modules_dir.rglob("test_router_v2.py"):
        print(f"Traitement: {test_file}")

        if fix_test_file(test_file):
            print(f"  ✅ Fixé")
            fixed_count += 1
        else:
            print(f"  ⏭️  Pas de changement nécessaire")

    print(f"\n✨ {fixed_count} fichiers modifiés")


if __name__ == "__main__":
    main()
