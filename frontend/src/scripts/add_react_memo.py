#!/usr/bin/env python3
"""
Script pour ajouter React.memo aux composants Tab.
Transformation:
  export const XxxTab: React.FC<Type> = ({ data: var }) => {
    ...
  };
->
  export const XxxTab = React.memo<Type>(function XxxTab({ data: var }) {
    ...
  });
"""

import os
import re
import sys


def transform_tab_component(content: str) -> str:
    """Transforme un composant Tab pour utiliser React.memo."""

    # Pattern pour matcher l'export du composant
    # export const XxxTab: React.FC<TabContentProps<Type>> = ({ data: varname }) => {
    pattern = r'export const (\w+Tab): React\.FC<([^>]+(?:<[^>]+>)?)> = \(\{ data: (\w+) \}\) => \{'

    def replacer(match):
        tab_name = match.group(1)
        type_param = match.group(2)
        var_name = match.group(3)
        return f'export const {tab_name} = React.memo<{type_param}>(function {tab_name}({{ data: {var_name} }}) {{'

    # Appliquer la transformation de l'export
    new_content = re.sub(pattern, replacer, content)

    # Si la transformation a eu lieu, on doit aussi fermer le React.memo
    if new_content != content:
        # Trouver le }; de fermeture du composant et le remplacer par });
        # Approche: compter les { et } pour trouver la fermeture correspondante

        # Pattern pour trouver le debut de la fonction React.memo
        match = re.search(
            r'export const (\w+Tab) = React\.memo<[^>]+(?:<[^>]+>)?>\(function \1\([^)]*\) \{',
            new_content
        )
        if match:
            start = match.end()
            brace_count = 1
            pos = start

            # Compter les accolades pour trouver la fermeture
            while pos < len(new_content) and brace_count > 0:
                char = new_content[pos]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                pos += 1

            # pos pointe maintenant apres le } de fermeture de la fonction
            closing_brace_pos = pos - 1  # Position du }

            # Chercher le ; en sautant les espaces/newlines
            semicolon_pos = pos
            while semicolon_pos < len(new_content) and new_content[semicolon_pos] in ' \t\n\r':
                semicolon_pos += 1

            if semicolon_pos < len(new_content) and new_content[semicolon_pos] == ';':
                # Remplacer }....; par });
                # On garde l'indentation avant le }
                new_content = new_content[:closing_brace_pos] + '});' + new_content[semicolon_pos + 1:]

    return new_content


def process_file(filepath: str) -> bool:
    """Traite un fichier et retourne True si modifie."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verifier si deja transforme
        if 'React.memo<' in content:
            return False

        # Verifier si c'est un Tab component avec le bon pattern
        if not re.search(r'export const \w+Tab: React\.FC<', content):
            return False

        new_content = transform_tab_component(content)

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True

        return False
    except Exception as e:
        print(f"Erreur sur {filepath}: {e}", file=sys.stderr)
        return False


def main():
    """Point d'entree principal."""
    base_path = '/home/ubuntu/azalscore/frontend/src/modules'
    modified = 0
    total = 0
    errors = []

    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith('Tab.tsx'):
                filepath = os.path.join(root, filename)
                total += 1
                if process_file(filepath):
                    modified += 1
                    print(f"OK {filepath}")
                else:
                    # Verifier si le fichier n'a pas le bon pattern
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'React.memo<' not in content and 'export const' in content:
                        if not re.search(r'export const \w+Tab: React\.FC<[^>]+>\s*=\s*\(\{\s*data:', content):
                            errors.append(filepath)

    print(f"\nTotal: {modified}/{total} fichiers modifies")
    if errors:
        print(f"\n{len(errors)} fichiers avec pattern non reconnu:")
        for e in errors:
            print(f"  - {e}")


if __name__ == '__main__':
    main()
