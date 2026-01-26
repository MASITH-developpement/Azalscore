#!/usr/bin/env python3
"""
Script de Migration Endpoints vers CORE SaaS
=============================================

Ce script aide à migrer les endpoints FastAPI pour utiliser le nouveau
pattern CORE SaaS avec `get_saas_context()`.

Usage:
    python scripts/migrate_endpoint_to_core.py <fichier.py>
    python scripts/migrate_endpoint_to_core.py app/api/myendpoint.py

Le script génère un fichier migré: <fichier>_migrated.py

Transformations:
    AVANT:
        from app.core.dependencies import get_current_user, get_tenant_id
        def my_endpoint(
            current_user: User = Depends(get_current_user),
            tenant_id: str = Depends(get_tenant_id)
        ):
            user_id = current_user.id
            role = current_user.role

    APRÈS:
        from app.core.dependencies_v2 import get_saas_context
        from app.core.saas_context import SaaSContext
        def my_endpoint(
            context: SaaSContext = Depends(get_saas_context)
        ):
            user_id = context.user_id
            role = context.role
"""

import re
import sys
from pathlib import Path


def migrate_imports(content: str) -> str:
    """
    Migre les imports vers le nouveau pattern.
    """
    # Remplacer import get_current_user
    content = re.sub(
        r'from app\.core\.dependencies import.*',
        lambda m: m.group(0).replace('get_current_user', '').replace('get_tenant_id', '').replace(', ,', ',').strip(', '),
        content
    )

    # Ajouter nouveaux imports si pas déjà présents
    if 'from app.core.dependencies_v2 import get_saas_context' not in content:
        # Trouver la section imports
        import_section = content.find('from fastapi import')
        if import_section != -1:
            # Insérer après les imports fastapi
            next_newline = content.find('\n', import_section)
            if next_newline != -1:
                content = (
                    content[:next_newline + 1] +
                    '\nfrom app.core.dependencies_v2 import get_saas_context\n' +
                    'from app.core.saas_context import SaaSContext\n' +
                    content[next_newline + 1:]
                )

    # Supprimer imports inutilisés
    content = content.replace('from app.core.models import User\n', '')

    return content


def migrate_function_signature(content: str) -> str:
    """
    Migre les signatures de fonctions.

    AVANT:
        def my_func(
            current_user: User = Depends(get_current_user),
            tenant_id: str = Depends(get_tenant_id),
            ...
        )

    APRÈS:
        def my_func(
            context: SaaSContext = Depends(get_saas_context),
            ...
        )
    """
    # Pattern 1: current_user + tenant_id ensemble
    pattern1 = r'(\s+)current_user:\s*User\s*=\s*Depends\(get_current_user\),?\s*\n\s*tenant_id:\s*str\s*=\s*Depends\(get_tenant_id\),?'
    replacement1 = r'\1context: SaaSContext = Depends(get_saas_context),'

    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: tenant_id seul
    pattern2 = r'(\s+)tenant_id:\s*str\s*=\s*Depends\(get_tenant_id\),?'
    replacement2 = r'\1context: SaaSContext = Depends(get_saas_context),'

    content = re.sub(pattern2, replacement2, content)

    # Pattern 3: current_user seul
    pattern3 = r'(\s+)current_user:\s*User\s*=\s*Depends\(get_current_user\),?'
    replacement3 = r'\1context: SaaSContext = Depends(get_saas_context),'

    content = re.sub(pattern3, replacement3, content)

    return content


def migrate_variable_usages(content: str) -> str:
    """
    Migre les usages de variables dans le corps des fonctions.

    current_user.id → context.user_id
    current_user.role → context.role
    tenant_id → context.tenant_id
    """
    # current_user.id → context.user_id
    content = re.sub(r'\bcurrent_user\.id\b', 'context.user_id', content)

    # current_user.role → context.role
    content = re.sub(r'\bcurrent_user\.role\b', 'context.role', content)

    # current_user.tenant_id → context.tenant_id
    content = re.sub(r'\bcurrent_user\.tenant_id\b', 'context.tenant_id', content)

    # current_user.email → context.user_id (NOTE: email n'est plus directement disponible)
    # On laisse un commentaire TODO
    if 'current_user.email' in content:
        content = content.replace('current_user.email', 'context.user_id  # TODO: Get email from user table if needed')

    # tenant_id (variable locale) → context.tenant_id
    # ATTENTION: Ne pas remplacer dans les noms d'attributs/paramètres !
    # Seulement dans les usages comme variables locales

    # Pattern pour remplacer tenant_id quand c'est une variable locale
    # (ex: Item.tenant_id == tenant_id)
    def replace_tenant_id(match):
        """Remplace tenant_id seulement si c'est une utilisation de variable."""
        full_match = match.group(0)
        # Ne pas remplacer si c'est un nom d'attribut (ex: Item.tenant_id)
        if match.group(1):  # Il y a quelque chose avant (ex: Item.)
            return full_match
        # Ne pas remplacer si c'est un paramètre de fonction
        if ':' in match.group(0):
            return full_match
        # Remplacer
        return match.group(1) + 'context.tenant_id' + match.group(2)

    # Remplacer tenant_id quand utilisé comme variable (pas comme attribut)
    content = re.sub(r'(\W|^)(tenant_id)(\W|$)', replace_tenant_id, content)

    return content


def add_migration_comment(content: str) -> str:
    """Ajoute un commentaire indiquant que le fichier a été migré."""
    docstring_end = content.find('"""', 10)  # Trouver la fin du docstring
    if docstring_end != -1:
        migration_note = """

✅ MIGRÉ vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user() / get_tenant_id()
- SaaSContext fournit: tenant_id, user_id, role, permissions
- Prêt pour permissions granulaires
"""
        content = content[:docstring_end] + migration_note + content[docstring_end:]

    return content


def migrate_file(file_path: Path) -> str:
    """
    Migre un fichier complet.

    Returns:
        Le contenu migré
    """
    print(f"📄 Migration de {file_path}...")

    # Lire le contenu
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Vérifier si déjà migré
    if 'get_saas_context' in content:
        print(f"⚠️  Le fichier semble déjà migré (contient get_saas_context)")
        return content

    # Vérifier si contient des endpoints à migrer
    if 'get_current_user' not in content and 'get_tenant_id' not in content:
        print(f"ℹ️  Rien à migrer (pas d'usage de get_current_user/get_tenant_id)")
        return content

    print(f"🔄 Application des transformations...")

    # Étape 1: Migrer les imports
    content = migrate_imports(content)

    # Étape 2: Migrer les signatures de fonctions
    content = migrate_function_signature(content)

    # Étape 3: Migrer les usages de variables
    content = migrate_variable_usages(content)

    # Étape 4: Ajouter commentaire de migration
    content = add_migration_comment(content)

    print(f"✅ Migration complétée!")

    return content


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_endpoint_to_core.py <fichier.py>")
        print("Exemple: python scripts/migrate_endpoint_to_core.py app/api/myendpoint.py")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"❌ Erreur: Le fichier {file_path} n'existe pas")
        sys.exit(1)

    if not file_path.suffix == '.py':
        print(f"❌ Erreur: Le fichier doit être un .py")
        sys.exit(1)

    # Migrer
    migrated_content = migrate_file(file_path)

    # Générer nom de fichier de sortie
    output_path = file_path.parent / f"{file_path.stem}_migrated.py"

    # Écrire le résultat
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(migrated_content)

    print(f"\n✅ Fichier migré sauvegardé: {output_path}")
    print(f"\n📝 Prochaines étapes:")
    print(f"   1. Vérifier le fichier migré: {output_path}")
    print(f"   2. Tester les endpoints")
    print(f"   3. Si OK, remplacer l'original: mv {output_path} {file_path}")
    print(f"   4. Ajouter au commit Git")


if __name__ == '__main__':
    main()
